"""Jupyter notebooks that rerun a session's BindingDB tool calls (create_jupyter_notebook).

`build_notebook` writes the notebook: the prompts and answers, a code cell per tool call with the result as
it was recorded, the figures, and the provenance (BindingDB release and source checksum, server version and
commit, model). It goes in a folder of its own with everything it needs (`study_files`): requirements.txt,
which pins this server's GitHub commit and the versions of its dependencies in uv.lock (or, when the commit is
not on GitHub, a copy of the package), the recorded results (data/) and figures (figures/), and a README.

`Replay` is what the cells run. By default it shows the recorded results from data/, so the notebook runs
anywhere in seconds; with `rerun` (or BINDINGDB_RERUN=1) it builds this server in-process on a local copy of
the database, calls each tool again, shows the result and reports whether it matches the recorded one (by a
SHA-256 digest of the result, see `digest`).
"""

from __future__ import annotations

import ast
import base64
import contextlib
import hashlib
import io
import json
import math
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import transcript

REPO_URL = "https://github.com/pwrose/mcp-bindingdb"
BINDINGDB_CITATION = ("Liu T, Hwang L, Burley SK, Nitsche CI, Southan C, Walters WP, Gilson MK. BindingDB in 2024: "
                      "a FAIR knowledgebase of protein-small molecule binding data. Nucleic Acids Research 53(D1):D1633-D1644, "
                      "2025. https://doi.org/10.1093/nar/gkae1075")
#: BibTeX for the server, BindingDB and RDKit, as in the README's Citation section; {rdkit_version} is filled in.
BIBTEX = """@software{rose2026mcp-bindingdb,
  title={MCP BindingDB Server},
  author={Rose, P.W.},
  year={2026},
  url={https://github.com/pwrose/mcp-bindingdb}
}

@article{liu2025bindingdb,
  title={BindingDB in 2024: a FAIR knowledgebase of protein-small molecule binding data},
  author={Liu, T. and Hwang, L. and Burley, S.K. and Nitsche, C.I. and Southan, C. and Walters, W.P. and Gilson, M.K.},
  journal={Nucleic Acids Research},
  volume={53},
  number={D1},
  pages={D1633--D1644},
  year={2025},
  doi={10.1093/nar/gkae1075}
}

@software{rdkit,
  title={RDKit: Open-source cheminformatics},
  author={Landrum, G. and others},{rdkit_version}
  url={https://www.rdkit.org},
  doi={10.5281/zenodo.591637}
}"""

#: Parts of results that differ from run to run by design: ids of viewers, editors and figures, file locations.
VOLATILE_KEYS = {"overlay_id", "editor_id", "figure_id", "figure_file", "contact_figure_id", "folder",
                 "client_shows_viewer"}
#: Tools that read an external service, whose answers can change over time.
NETWORK_TOOLS = {"chemical_name_to_smiles": "PubChem", "find_pdb_complexes": "RCSB",
                 "overlay_binding_site": "PDBe and RCSB"}
#: Tools that only open a panel in the chat: nothing to rerun.
UI_TOOLS = {"open_structure_editor"}
FIGURE_TOOLS = {"draw_structure_grid", "draw_r_group_table"}
SIGNIFICANT_DIGITS = 10  # floats are compared to this precision: parallel sums differ in the last bits
#: Analysis code longer than this many lines goes to a .py file next to the notebook, which a cell imports.
INLINE_CODE_LINES = 40
#: The extras a notebook's environment installs: structure search and drawing, PDB complexes, OPSIN, the kernel.
EXTRAS = ("substructure", "structures", "opsin", "notebook")
#: Written into the package by scripts/build_bundle.sh, and into a copy of it in a notebook folder: the commit
#: the code is from, which a bundle or a copy cannot ask git for.
BUILD_FILE = "_build.json"
#: Turns reruns on in Replay when set to 1 (or true/yes), as RERUN = True in the setup cell does.
RERUN_ENV = "BINDINGDB_RERUN"
_RESULT_REF = re.compile(r"\breplay\.result\(\s*(\d+)\s*\)")


# --------------------------------------------------------------------------------------------------- digests

def canonical(value: Any) -> Any:
    """A result in the form its digest is taken of: JSON types only, volatile keys dropped, floats rounded."""
    value = json.loads(json.dumps(value, default=str))
    return _canonical(value)


def _canonical(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items() if k not in VOLATILE_KEYS}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    if isinstance(value, float):
        return float(f"{value:.{SIGNIFICANT_DIGITS}g}") if math.isfinite(value) else str(value)
    return value


def digest(value: Any) -> str:
    """SHA-256 of a tool result's canonical JSON (sorted keys, no whitespace)."""
    text = json.dumps(canonical(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(text.encode()).hexdigest()


# ------------------------------------------------------------------------------------------- environment

def source_version() -> dict[str, Any]:
    """The commit this package's code is from: `commit`, `uncommitted_changes` (in the package), and
    `published` (the commit is on a branch of the GitHub repository, so pip can install it from there).

    Read from the _build.json a bundle or a copied package carries, else from the package's own git checkout,
    else from the record pip keeps of a package it installed from git; {} if none says."""
    folder = Path(__file__).resolve().parent
    with contextlib.suppress(OSError, ValueError):
        recorded = json.loads((folder / BUILD_FILE).read_text())
        if isinstance(recorded, dict):
            return {k: recorded[k] for k in ("commit", "uncommitted_changes", "published") if recorded.get(k) is not None}

    def git(*args: str) -> str:
        return subprocess.run(["git", "-C", str(folder), *args], capture_output=True, text=True, timeout=5,
                              check=True).stdout.strip()
    try:  # only mcp-bindingdb's own checkout: not a repository the package happens to sit in
        if Path(git("rev-parse", "--show-toplevel")).resolve() == folder.parents[1]:
            commit = git("rev-parse", "HEAD")
            return {"commit": commit, "uncommitted_changes": bool(git("status", "--porcelain", "--", ".")),
                    "published": bool(git("branch", "-r", "--contains", commit))}
    except (OSError, subprocess.SubprocessError):
        pass
    from importlib.metadata import PackageNotFoundError, distribution
    with contextlib.suppress(PackageNotFoundError, OSError, ValueError, TypeError, AttributeError):
        direct = json.loads(distribution("mcp-bindingdb").read_text("direct_url.json") or "{}")
        if commit := (direct.get("vcs_info") or {}).get("commit_id"):
            return {"commit": commit, "uncommitted_changes": False, "published": True}
    return {}


def server_requirement(source: dict[str, Any]) -> str | None:
    """requirements.txt's line for this server at its commit on GitHub; None when pip could not install that
    commit from there (it has uncommitted changes, is not pushed, or is unknown): then the folder gets a copy."""
    if source.get("commit") and source.get("published") and not source.get("uncommitted_changes"):
        return f"mcp-bindingdb[{','.join(EXTRAS)}] @ git+{REPO_URL}.git@{source['commit']}"
    return None


def locked_requirements(project: Path | None) -> list[str]:
    """Pinned requirements for this server's dependencies and EXTRAS, as its uv.lock has them (uv export); if
    that fails, the versions installed here of the packages it needs directly."""
    uv = os.environ.get("UV") or shutil.which("uv")
    if project is not None and uv and (project / "uv.lock").is_file():
        command = [uv, "export", "--frozen", "--no-hashes", "--no-header", "--no-annotate", "--no-emit-project",
                   "--no-dev", *(a for e in EXTRAS for a in ("--extra", e))]
        with contextlib.suppress(OSError, subprocess.SubprocessError):
            done = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=60, check=True)
            if lines := [line for line in done.stdout.splitlines() if line.strip() and not line.startswith("#")]:
                return lines
    names = ("duckdb", "markdown-it-py", "mcp", "rdkit", "gemmi", "pyopsin", "jdk4py", "ipykernel")
    return [f"{name}=={v}" for name in names if (v := _dist_version(name))]


def package_files() -> dict[str, bytes]:
    """This package's files, by path relative to the folder holding it (mcp_bindingdb/...), for a notebook
    folder whose commit pip cannot install from GitHub. Compiled files and the build record are left out."""
    folder = Path(__file__).resolve().parent
    return {f"{folder.name}/{p.relative_to(folder).as_posix()}": p.read_bytes() for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc" and p.name != BUILD_FILE}


def environment() -> dict[str, str]:
    """Versions of the software that computes the results."""
    versions = {"python": platform.python_version()}
    for module, name in (("duckdb", "duckdb"), ("rdkit", "rdkit"), ("mcp", "mcp"), ("gemmi", "gemmi")):
        try:
            versions[name] = getattr(__import__(module), "__version__", None) or _dist_version(name)
        except ImportError:
            continue
    return {k: v for k, v in versions.items() if v}


def package_version() -> str:
    """This package's version: from its installed metadata, else from the build record a copy carries."""
    if version := _dist_version("mcp-bindingdb"):
        return version
    with contextlib.suppress(OSError, ValueError, AttributeError):
        return str(json.loads((Path(__file__).resolve().parent / BUILD_FILE).read_text()).get("version") or "unknown")
    return "unknown"


def _dist_version(name: str) -> str:
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version(name)
    except PackageNotFoundError:
        return ""


# ------------------------------------------------------------------------------------- running notebooks

def project_dir() -> Path | None:
    """The mcp-bindingdb folder this package runs from, where `uv run` finds its environment."""
    folder = Path(__file__).resolve().parents[2]
    return folder if (folder / "pyproject.toml").is_file() else None


def rerun_path(path: Path) -> Path:
    """Where nbconvert writes the executed copy of a notebook: <name>-rerun.ipynb next to it."""
    return path.with_name(f"{path.stem}-rerun.ipynb")


def run_commands(path: Path, db_path: Path | None = None) -> dict[str, str]:
    """Shell commands, run in the notebook's folder, that open it in JupyterLab (showing the recorded results),
    and that rerun every call with nbconvert, writing <name>-rerun.ipynb; `db_path` is the database to rerun on.
    `--no-project` keeps uv from using a project the folder happens to sit in."""
    q = lambda p: shlex.quote(str(p))  # noqa: E731
    cd, uv = f"cd {q(path.parent)}", "uv run --no-project --with-requirements requirements.txt"
    db = f"BINDINGDB_DUCKDB={q(db_path)} " if db_path else ""
    return {"jupyter": f"{cd}\n{uv} --with jupyterlab jupyter lab {q(path.name)}",
            "rerun": f"{cd}\n{RERUN_ENV}=1 {db}{uv} --with nbconvert jupyter nbconvert --to notebook --execute "
                     f"--output {q(rerun_path(path).name)} {q(path.name)}"}


def to_html(path: Path, timeout: float = 120) -> Path:
    """Convert the notebook, as written (not run), to <name>.html next to it with nbconvert; returns its
    path. On failure, nbconvert's output goes to <name>-html.log and RuntimeError says so."""
    uv = os.environ.get("UV") or shutil.which("uv")  # `uv run` sets UV to its own path
    if not uv:
        raise RuntimeError("uv was not found")
    out, log = path.with_suffix(".html"), path.with_name(f"{path.stem}-html.log")
    out.unlink(missing_ok=True)
    command = [uv, "run", "--no-project", "--with", "nbconvert", "jupyter", "nbconvert", "--to", "html", path.name]
    try:
        done = subprocess.run(command, cwd=path.parent, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"nbconvert took over {timeout:.0f} s and was stopped") from None
    if done.returncode or not out.is_file():
        log.write_text(f"$ {shlex.join(command)}\n\n{done.stdout}{done.stderr}")
        raise RuntimeError(f"nbconvert failed (exit code {done.returncode}); its output is in {log}")
    log.unlink(missing_ok=True)
    return out


# ------------------------------------------------------------------------------------------------- calls

def expand_call(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """The tool calls a logged call stands for in a notebook: itself; for get_editor_results, the searches
    the user ran in the editor (its arguments name an editor that exists only in that chat); none for a
    tool that only opens a panel."""
    tool = entry["tool"]
    if tool in UI_TOOLS:
        return []
    result = entry.get("result")
    if tool == "get_editor_results" and isinstance(result, dict):
        return [{"tool": s["tool"], "arguments": s.get("arguments") or {}, "result": s.get("result"),
                 "timestamp": s.get("ran_at") or entry.get("timestamp", ""), "from_editor": True}
                for s in result.get("searches") or [] if isinstance(s, dict) and s.get("tool")]
    return [{**entry, "arguments": entry.get("arguments") or {}}]


def call_source(number: int, tool: str, arguments: dict[str, Any], sha256: str | None, comment: str) -> str:
    """The code cell of one call: `await replay.call(...)`, with run_sql's SQL as a block of text."""
    args = dict(arguments)
    lines = [f"# {comment}"]
    sql = args.get("sql") if tool == "run_sql" else None
    if isinstance(sql, str) and '"""' not in sql and "\\" not in sql and not sql.endswith('"'):
        lines += ['sql = """', sql.strip("\n"), '"""']
        args["sql"] = _Raw("sql")
    literal = _literal(args)
    if "\n" in literal:  # long arguments: named first, so the call stays on one line
        lines.append(f"arguments = {literal}")
        literal = "arguments"
    call = f"await replay.call({number}, {tool!r}, {literal}"
    call += f",\n                  sha256={sha256!r})" if sha256 else ")"
    return "\n".join([*lines, call])


class _Raw:
    """A name written as is in generated code (the `sql` variable)."""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name


def _literal(value: Any, indent: int = 0) -> str:
    """A Python literal for JSON-like arguments, one key per line when long."""
    text = repr(value)
    if len(text) <= 90 or not isinstance(value, (dict, list)) or not value:
        return text
    pad = " " * (indent + 4)
    if isinstance(value, dict):
        items = [f"{pad}{k!r}: {_literal(v, indent + 4)}," for k, v in value.items()]
        return "{\n" + "\n".join(items) + "\n" + " " * indent + "}"
    items = [f"{pad}{_literal(v, indent + 4)}," for v in value]
    return "[\n" + "\n".join(items) + "\n" + " " * indent + "]"


# ---------------------------------------------------------------------------------------------- notebook

def build_notebook(*, title: str, when: str, model: str, build_info: dict[str, str], generated_by: str,
                   exchanges: list[dict[str, Any]], leftover_calls: list[dict[str, Any]],
                   unplaced_figures: list[Any], skills: list[str], mcp_servers: list[str],
                   max_rows: int | None, file_name: str = "notebook.ipynb", model_name: str | None = None,
                   log_entries: list[dict[str, Any]] = (), project: Path | None = None,
                   ) -> tuple[dict[str, Any], dict[str, int], dict[str, str | bytes]]:
    """The notebook (nbformat 4.5, as a dict), counts of what it holds, and the other files of its folder,
    by path relative to it: requirements.txt, README.md, the recorded results (data/call-NN.json), the figures
    (figures/figure-N.<ext>), the .py files of its longer analysis code, and, when this server's commit
    cannot be installed from GitHub, a copy of the package (mcp_bindingdb/). `project` is the mcp-bindingdb
    folder whose uv.lock pins the requirements.

    `exchanges` are dicts with prompt, answer, `calls` (logged entries, see ToolLog), `figures`
    (figures.Figure) and `code` (analysis code the model wrote: dicts with code, run, description,
    module_name, packages, output, language and the `figures` it made); `leftover_calls` go in a section
    after the conversation (when no exchange lists its calls), as do `unplaced_figures`. `log_entries` is
    the whole tool log, whose 1-based indices `replay.result(i)` in the code refers to; they become the
    notebook's call numbers. Raises ValueError for code that reads a call not in the notebook."""
    nb = _Notebook(max_rows)
    release = build_info.get("release", "unknown")
    source = source_version()
    env = environment()
    for exchange in exchanges:
        exchange.setdefault("code", [])
    code_figures = [{f.id for b in e["code"] for f in b.get("figures") or []} for e in exchanges]
    numbers = transcript.figure_numbers(
        [{"figures": [*(f.id for b in e["code"] for f in b.get("figures") or []),
                      *(f.id for f in e["figures"] if f.id not in made)]}
         for e, made in zip(exchanges, code_figures)], unplaced_figures)
    call_numbers = _call_numbers([c for e in exchanges for c in e["calls"]] + list(leftover_calls), log_entries)
    stem = _module_stem(file_name)
    files: dict[str, str] = {}  # the analysis code's modules

    body_start = len(nb.cells)
    for k, (exchange, made) in enumerate(zip(exchanges, code_figures), start=1):
        nb.markdown(f"## Exchange {k}\n\n**👤 User**\n\n{(exchange.get('prompt') or '(no prompt)').strip()}")
        for entry in exchange["calls"]:
            nb.calls(entry)
        for block in exchange["code"]:
            nb.analysis(block, call_numbers, numbers, stem, files, file_name, model_name)
        for figure in exchange["figures"]:  # before the answer, as the chat showed them
            if figure.id not in made:
                nb.figure(figure, numbers[figure.id])
        nb.markdown("**🧠 Assistant**\n\n" + ((exchange.get("answer") or "").strip() or "_(no answer recorded)_"))
    if leftover_calls:
        nb.markdown("## BindingDB tool calls\n\nThe calls of this session, in the order they ran.")
        for entry in leftover_calls:
            nb.calls(entry)
    if unplaced_figures:
        nb.markdown("## Figures")
        for figure in unplaced_figures:
            nb.figure(figure, numbers[figure.id])
    body = nb.cells[body_start:]
    nb.cells[body_start:] = []

    counts = {"exchanges": len(exchanges), "calls": nb.n_calls, "figures": len(numbers),
              "redrawn_figures": nb.n_redrawn, "skipped_calls": nb.n_skipped, "code_cells": nb.n_code,
              "code_files": len(files)}
    packages = sorted({p for e in exchanges for b in e["code"] for p in b.get("packages") or []})
    server = server_requirement(source)
    figure_files = {}
    for figure in [*(f for e in exchanges for f in e["figures"]),
                   *(f for e in exchanges for b in e["code"] for f in b.get("figures") or []), *unplaced_figures]:
        figure_files[f"figures/figure-{numbers[figure.id]}{Path(figure.file).suffix.lower()}"] = figure.data
    meta = {"title": title, "date": when, "model": model, "bindingdb_release": release,
            "bindingdb_build": {k: v for k, v in build_info.items() if k != "table_row_counts"},
            "generated_by": generated_by, "generated_at": _utc_now(), **({"source": source} if source else {}),
            "environment": env, **({"skills": skills} if skills else {}),
            **({"external_mcp_servers": mcp_servers} if mcp_servers else {}),
            **({"python_packages": packages} if packages else {}),
            **({"code_files": sorted(files)} if files else {}),
            "server_install": "github" if server else "copy", "contents": counts}
    nb.markdown(_header(meta, counts, file_name))
    nb.code(_setup_source(build_info), [_stream(_recorded_environment(meta))])
    nb.cells += body
    nb.markdown("## Verification\n\nHow each rerun call compared with its recorded result.")
    nb.code("replay.summary()", [_markdown_output(f"_Recorded: {transcript.plural(nb.n_calls, 'tool call')}"
                                                  f"{', ' + transcript.plural(nb.n_redrawn, 'figure') + ' to redraw' if nb.n_redrawn else ''}. "
                                                  "Run all cells to compare._")])
    nb.markdown(_citation(meta))
    for k, cell in enumerate(nb.cells, start=1):
        cell["id"] = f"cell-{k}"
    notebook = {"cells": nb.cells, "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}, "bindingdb": meta}, "nbformat": 4, "nbformat_minor": 5}
    folder: dict[str, str | bytes] = {"requirements.txt": _requirements(server, source, project, packages),
                                      "README.md": _readme(meta, counts, file_name, figure_files),
                                      **nb.data, **figure_files, **files}
    if server is None:
        folder.update(package_files())
        folder[f"mcp_bindingdb/{BUILD_FILE}"] = json.dumps(
            {"commit": source.get("commit"), "uncommitted_changes": source.get("uncommitted_changes", False),
             "published": False, "version": package_version(), "copied_by": generated_by, "copied_at": meta["generated_at"]}, indent=1) + "\n"
    return notebook, counts, folder


def _requirements(server: str | None, source: dict[str, Any], project: Path | None, packages: list[str]) -> str:
    """requirements.txt: this server from GitHub (or a note that the folder holds a copy), the pinned
    versions of its dependencies, and the packages the analysis code imports."""
    commit = (source.get("commit") or "")[:12]
    if server:
        head = [f"# mcp-bindingdb at commit {commit}, with the versions of its dependencies its uv.lock pins.",
                server]
    else:
        why = ("its commit has uncommitted changes" if source.get("uncommitted_changes") else
               f"commit {commit} is not on GitHub" if commit else "its commit is not known")
        head = ["# The dependencies of mcp-bindingdb, at the versions its uv.lock pins. mcp-bindingdb itself is the",
                f"# copy in mcp_bindingdb/ next to the notebook, since {why}."]
    lines = [*head, *locked_requirements(project)]
    if packages:
        lines += ["# Imported by the analysis code:", *packages]
    return "\n".join(lines) + "\n"


def data_file(number: int) -> str:
    """Where a notebook folder keeps the recorded result of call `number`."""
    return f"data/call-{number:02d}.json"


def _call_numbers(entries: list[dict[str, Any]], log_entries: list[dict[str, Any]]) -> dict[int, int]:
    """Tool-log index -> the notebook's number of that call (its first, for editor searches), numbered as
    _Notebook.calls numbers them."""
    index_of = {id(e): i for i, e in enumerate(log_entries, start=1)}
    numbers: dict[int, int] = {}
    n = 0
    for entry in entries:
        if expanded := expand_call(entry):
            if id(entry) in index_of:
                numbers.setdefault(index_of[id(entry)], n + 1)
            n += len(expanded)
    return numbers


def _module_stem(file_name: str) -> str:
    """A Python identifier from the notebook's file name, for its code files: 'imatinib_analogues'."""
    stem = re.sub(r"\W+", "_", Path(file_name).stem).strip("_").lower() or "analysis"
    return stem if stem[0].isalpha() else f"nb_{stem}"


def _module_name(name: str | None, default: str, taken: dict[str, str]) -> str:
    """A module name for a code file: the model's, made an identifier, or `default`; unique in `taken`."""
    base = re.sub(r"\W+", "_", (name or "").removesuffix(".py")).strip("_").lower() or default
    base = base if base[0].isalpha() else f"code_{base}"
    module, k = base, 2
    while f"{module}.py" in taken:
        module, k = f"{base}_{k}", k + 1
    return module


def resolve_results(code: str, call_numbers: dict[int, int]) -> str:
    """replay.result(i) with a tool-log index i -> replay.result(n), the notebook's number of that call."""
    def number(match: re.Match[str]) -> str:
        index = int(match.group(1))
        if index not in call_numbers:
            raise ValueError(f"the code reads replay.result({index}), but call {index} is not in the notebook "
                             "(list it in an exchange's calls)")
        return f"replay.result({call_numbers[index]})"
    return _RESULT_REF.sub(number, code)


def _is_python(code: str) -> bool:
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def _caption(figure: Any, number: int) -> str:
    return f"**Figure {number}: {figure.title.strip().rstrip('.')}.**" + (f" {figure.caption}" if figure.caption else "")


class _Notebook:
    def __init__(self, max_rows: int | None) -> None:
        self.cells: list[dict[str, Any]] = []
        self.data: dict[str, str] = {}  # data/call-NN.json: each call's recorded result
        self.max_rows = max_rows
        self.n_calls = self.n_redrawn = self.n_skipped = self.n_code = 0

    def markdown(self, source: str, attachments: dict[str, Any] | None = None) -> None:
        cell = {"cell_type": "markdown", "metadata": {}, "source": _lines(source)}
        if attachments:
            cell["attachments"] = attachments
        self.cells.append(cell)

    def code(self, source: str, outputs: list[dict[str, Any]], metadata: dict[str, Any] | None = None) -> None:
        self.cells.append({"cell_type": "code", "metadata": metadata or {},
                           "execution_count": None, "source": _lines(source), "outputs": outputs})

    def calls(self, entry: dict[str, Any]) -> None:
        """The cells of one logged call (or of the editor searches it stands for)."""
        expanded = expand_call(entry)
        if not expanded:
            self.n_skipped += 1
            self.markdown(f"_`{transcript.signature(entry, 200)}` opened a panel in the chat; nothing to rerun._")
            return
        if entry["tool"] == "get_editor_results":
            self.markdown(f"_The user ran {transcript.plural(len(expanded), 'search')} in the structure editor; "
                          "get_editor_results passed "
                          f"{'it' if len(expanded) == 1 else 'them'} on, and {'it is' if len(expanded) == 1 else 'they are'} rerun here._")
        for call in expanded:
            self.n_calls += 1
            n = self.n_calls
            sha = digest(call.get("result"))
            self.data[data_file(n)] = json.dumps(call.get("result"), indent=1, ensure_ascii=False, default=str) + "\n"
            stamp = _stamp(call.get("timestamp", ""))
            comment = f"Call {n} · {call['tool']}" + (f" · ran {stamp}" if stamp else "") + \
                      (" · from the structure editor" if call.get("from_editor") else "")
            status = f"**Call {n}** · recorded result · sha256 `{sha[:12]}…`"
            if service := NETWORK_TOOLS.get(call["tool"]):
                status += f" · uses {service}, whose answers can change"
            text = "\n".join([status, "", *transcript.render_result(call.get("result"), self.max_rows)])
            self.code(call_source(n, call["tool"], call["arguments"], sha, comment), [_markdown_output(text)],
                      {"bindingdb": {"call": n, "tool": call["tool"], "recorded_at": call.get("timestamp", ""),
                                     "sha256": sha}})

    def analysis(self, block: dict[str, Any], call_numbers: dict[int, int], figure_numbers: dict[int, int],
                 stem: str, files: dict[str, str], file_name: str, model: str | None) -> None:
        """A cell of the model's analysis code: inline when short, else a .py file (added to `files`) that the
        cell imports; the figures the code made are the cell's recorded output."""
        self.n_code += 1
        n = self.n_code
        code = block["code"].strip("\n")
        run = (block.get("run") or "").strip("\n")
        description = " ".join((block.get("description") or "").split())
        title = f"Code {n}" + (f": {description}" if description else "")
        language = (block.get("language") or "python").strip().lower()
        made = [(f, figure_numbers[f.id]) for f in block.get("figures") or []]
        if language != "python" or not _is_python(code) or (run and not _is_python(run)):
            self.markdown(f"**{title}** _({language}, shown as written and not run: only Python code runs in "
                          f"this notebook)_\n\n```{language}\n{code}\n```")
            for figure, number in made:
                self.figure(figure, number)
            return
        code, run = resolve_results(code, call_numbers), resolve_results(run, call_numbers)
        outputs = [_stream(block["output"].rstrip("\n") + "\n")] if block.get("output") else []
        for figure, number in made:
            outputs += [_markdown_output(_caption(figure, number) + " _(as recorded; running this cell draws it "
                                         "again)_"), _image_output(figure.data, _mime(figure.file))]
        meta: dict[str, Any] = {"code": n}
        lines = len(code.splitlines())
        if lines > INLINE_CODE_LINES:
            module = _module_name(block.get("module_name"), f"{stem}_code_{n}", files)
            files[f"{module}.py"] = "\n".join([
                f'"""{title}, from the notebook {file_name}.',
                "",
                f"Written by {model or 'the model'} during the analysis. The notebook imports this file, so keep",
                'it in the same folder as the notebook."""',
                "", code, ""])
            source = (f"# {title}\n# The code is in {module}.py, next to this notebook ({lines} lines).\n"
                      f"from {module} import *")
            meta["module"] = f"{module}.py"
        else:
            source = f"# {title}\n{code}"
        if run:
            source += f"\n\n{run}"
        self.code(source, outputs, {"bindingdb": meta})

    def figure(self, figure: Any, number: int) -> None:
        caption = _caption(figure, number)
        mime = _mime(figure.file)
        if figure.call and figure.call.get("tool") in FIGURE_TOOLS:
            self.n_redrawn += 1
            args = {k: v for k, v in figure.call["arguments"].items() if v not in (None, "", [], {})}
            literal = _literal(args)
            source = f"# Figure {number} · {figure.call['tool']} draws it again\n"
            if "\n" in literal:
                source += f"arguments = {literal}\n"
                literal = "arguments"
            source += f"await replay.figure({number}, {figure.call['tool']!r}, {literal})"
            self.code(source, [_markdown_output(caption + " _(as recorded)_"), _image_output(figure.data, mime)],
                      {"bindingdb": {"figure": number, "tool": figure.call["tool"]}})
            return
        how = ("Drawn by overlay_binding_site, whose call reruns above and draws it again."
               if "overlay_id" in figure.spec else
               "Made with other tools and added with add_figure, so it is recorded here as an image and not redrawn.")
        name = f"figure-{number}{Path(figure.file).suffix}"
        data = figure.data.decode() if mime == "image/svg+xml" else base64.b64encode(figure.data).decode()
        self.markdown(f"![Figure {number}: {figure.title}](attachment:{name})\n\n{caption}\n\n_{how}_",
                      {name: {mime: data}})


def _setup_source(build_info: dict[str, str]) -> str:
    args = [f"release={build_info.get('release', 'unknown')!r}"]
    if sha := build_info.get("source_zip_sha256"):
        args.append(f"source_zip_sha256={sha!r}")
    args.append("rerun=RERUN")
    return "\n".join([
        "# Shows the results recorded during the session (data/), so the notebook runs without a database. Set",
        "# RERUN = True (or start Jupyter with BINDINGDB_RERUN=1) to rerun every BindingDB call on a local copy of",
        "# the database instead and check it against its recorded result: see 'How to rerun the calls' above.",
        "from mcp_bindingdb.notebook import Replay",
        "",
        "RERUN = False",
        f"replay = Replay({', '.join(args)})",
    ])


def _header(meta: dict[str, Any], counts: dict[str, int], file_name: str) -> str:
    contents = [transcript.plural(counts["exchanges"], "exchange"), transcript.plural(counts["calls"], "tool call")]
    if counts["figures"]:
        contents.append(transcript.plural(counts["figures"], "figure"))
    if counts.get("code_cells"):
        contents.append(transcript.plural(counts["code_cells"], "code cell"))
    lines = [
        f"# {meta['title']}", "",
        "A reproducible record of an AI-assisted BindingDB analysis: each prompt, the BindingDB tool calls that "
        "answered it with their recorded results, the answer, and its figures. Run all cells to show the recorded "
        "results, or rerun every call on your own copy of the database and check each result against the "
        "recorded one.", "",
        *_provenance(meta),
        f"- **Contents:** {' · '.join(contents)}",
        "",
        *_run_steps(meta, file_name, "###"),
        "Run as it is, each call cell shows its recorded result, read from `data/` and checked against the "
        "SHA-256 digest recorded in the cell. Rerun, it shows the new result with ✅ when it matches the recorded "
        f"one (floats to {SIGNIFICANT_DIGITS} significant digits, ids of viewers and files left out). Calls to "
        "PubChem, RCSB or PDBe depend on those services and may differ. The prose answers are the model's and are "
        "not recomputed."
        + (" Code cells hold the analysis code the model wrote; they run as written (reading the results with "
           "`replay.result(n)`, the result of Call n) and draw their figures again, which are not compared."
           if counts.get("code_cells") else ""),
    ]
    return "\n".join(lines)


def _provenance(meta: dict[str, Any]) -> list[str]:
    """The header's list of what the analysis ran on and when."""
    build = meta["bindingdb_build"]
    source = meta.get("source") or {}
    commit = source.get("commit")
    server = meta["generated_by"] + (f", commit [`{commit[:12]}`]({REPO_URL}/commit/{commit})" if commit else "")
    if source.get("uncommitted_changes"):
        server += " with uncommitted changes (a rerun with that commit may differ)"
    data = f"BindingDB release **{meta['bindingdb_release']}**"
    if build.get("source_zip"):
        data += f" (`{build['source_zip']}`"
        data += f", SHA-256 `{build['source_zip_sha256']}`)" if build.get("source_zip_sha256") else ")"
    derived = [build[k] for k in ("inchi_keys", "properties") if build.get(k)]
    return [
        f"- **Date:** {meta['date']}",
        f"- **Model:** {meta['model']}",
        *([f"- **Skills:** {' · '.join(meta['skills'])}"] if meta.get("skills") else []),
        *([f"- **External MCP servers:** {' · '.join(meta['external_mcp_servers'])}"]
          if meta.get("external_mcp_servers") else []),
        f"- **Data:** {data}",
        *([f"- **Database build:** {build['built_at']}" + (f", DuckDB {build['duckdb_version']}"
                                                            if build.get("duckdb_version") else "")]
          if build.get("built_at") else []),
        *([f"- **Derived data:** {'; '.join(derived)}"] if derived else []),
        f"- **Server:** {server}",
        f"- **Software:** {', '.join(f'{k} {v}' for k, v in meta['environment'].items())}",
        f"- **Notebook generated:** {meta['generated_at']}",
    ]


def _run_steps(meta: dict[str, Any], file_name: str, heading: str) -> list[str]:
    """'How to run' and 'How to rerun the calls', with commands run in the notebook's folder."""
    release = meta["bindingdb_release"]
    commit = (meta.get("source") or {}).get("commit")
    stem = file_name[:-len(".ipynb")] if file_name.endswith(".ipynb") else file_name
    checks = "release" + (" and source checksum" if meta["bindingdb_build"].get("source_zip_sha256") else "")
    held = ["`requirements.txt` (" + ("mcp-bindingdb at its commit and " if meta.get("server_install") == "github"
                                      else "") + "the versions of the packages it needs)",
            "the recorded results in `data/`"]
    if meta["contents"].get("figures"):
        held.append("the figures in `figures/`")
    if files := meta.get("code_files"):
        held.append("the analysis code the notebook imports (" + ", ".join(f"`{f}`" for f in files) + ")")
    if meta.get("server_install") == "copy":
        held.append("a copy of the mcp-bindingdb code it ran with in `mcp_bindingdb/`, which cannot be "
                    "installed from GitHub")
    uv = "uv run --no-project --with-requirements requirements.txt"
    return [
        f"{heading} How to run", "",
        f"Keep the notebook in its folder, which holds everything it needs: {', '.join(held[:-1])} and {held[-1]}. "
        "With [uv](https://docs.astral.sh/uv/), from that folder (replace the path with yours):", "",
        "```bash",
        f"cd /path/to/{stem}",
        f"{uv} --with jupyterlab jupyter lab {file_name}",
        "```", "",
        "then choose Run → Run All Cells. The first start installs the packages, which takes a minute or two; "
        "the cells show the recorded results, so no database is needed. Without uv: "
        f"`pip install -r requirements.txt jupyterlab`, then `jupyter lab {file_name}` in the folder.", "",
        f"{heading} How to rerun the calls", "",
        f"To rerun every BindingDB call on your own copy of release {release} and check each result against the "
        "recorded one, set `RERUN = True` in the setup cell and run all cells, or rerun the notebook without "
        "opening Jupyter, writing a copy with the new results:", "",
        "```bash",
        f"cd /path/to/{stem}",
        f"{RERUN_ENV}=1 {uv} --with nbconvert jupyter nbconvert --to notebook --execute "
        f"--output {stem}-rerun.ipynb {file_name}",
        "```", "",
        f"A rerun needs the database: the one `BINDINGDB_DUCKDB=/path/to/bindingdb_{release}.duckdb` names (put it "
        "before `uv run`), else the newest one mcp-bindingdb built on this computer, for example for Claude Desktop. "
        "With neither, the first rerun builds one, which takes about half an hour and 2.4 GB. To build exactly "
        f"release {release}, with a clone of mcp-bindingdb:", "",
        "```bash",
        f"git clone {REPO_URL}.git",
        "cd mcp-bindingdb",
        *([f"git checkout {commit}"] if commit else []),
        f"scripts/build_duckdb.sh --release {release}",
        "```", "",
        f"The setup cell checks the database's {checks} against the recorded ones.", "",
    ]


def _readme(meta: dict[str, Any], counts: dict[str, int], file_name: str, figure_files: dict[str, bytes]) -> str:
    """README.md of the notebook's folder: what it is, how to run and rerun it, and what each file holds."""
    stem = file_name[:-len(".ipynb")] if file_name.endswith(".ipynb") else file_name
    contents = [
        f"- `{file_name}`: the notebook: each prompt, a cell per BindingDB tool call with its recorded result, "
        "the answer and its figures, with the provenance and how to cite it",
        f"- `{stem}.html`: the notebook as a web page, with the results as recorded (when it was written)",
        "- `requirements.txt`: the Python packages it runs with, at pinned versions",
        f"- `data/`: the result each call returned during the session (`call-NN.json`, for Call NN)",
        *(f"- `{name}`" for name in figure_files),
        *(f"- `{name}`: analysis code the notebook imports" for name in meta.get("code_files") or []),
        *(["- `mcp_bindingdb/`: the mcp-bindingdb code the notebook ran with, which cannot be installed from GitHub "
           "(see requirements.txt for why)"]
          if meta.get("server_install") == "copy" else []),
    ]
    return "\n".join([
        f"# {meta['title']}", "",
        f"A reproducible record of an AI-assisted BindingDB analysis with {transcript.plural(counts['calls'], 'tool call')}, "
        f"made by {meta['generated_by']}.", "",
        *_provenance(meta), "",
        *_run_steps(meta, file_name, "##"),
        "## Contents", "",
        *contents, "",
        "## Caveats", "",
        "- The recorded results are what this BindingDB release returned during the session. A rerun on another "
        "release, or of a call that reads PubChem, RCSB or PDBe, can differ; the notebook marks each such result ⚠️.",
        "- Figures drawn by mcp-bindingdb are drawn again on a rerun; other images are kept as recorded.",
        "",
    ])


def _recorded_environment(meta: dict[str, Any]) -> str:
    source = meta.get("source") or {}
    parts = [f"Recorded with BindingDB release {meta['bindingdb_release']}, {meta['generated_by']}"
             + (f" (commit {source['commit'][:12]})" if source.get("commit") else "")]
    parts.append(", ".join(f"{k} {v}" for k, v in meta["environment"].items()))
    return "\n".join(parts) + "\n"


def _citation(meta: dict[str, Any]) -> str:
    build = meta["bindingdb_build"]
    source = meta.get("source") or {}
    data = f"BindingDB release {meta['bindingdb_release']}"
    if build.get("source_url"):
        data += f", {build['source_url']}"
    if build.get("source_zip_sha256"):
        data += f" (SHA-256 {build['source_zip_sha256']})"
    server = meta["generated_by"] + (f", commit {source['commit']}" if source.get("commit") else "") + f", {REPO_URL}"
    return "\n".join([
        "## How to cite", "",
        "Cite this notebook (for example deposited with a DOI) together with the data and software it ran on:", "",
        f"- Data: {data}",
        f"- Software: {server}",
        f"- Analysis: {meta['title']}, {meta['date']}, with {meta['model']}",
        f"- BindingDB: {BINDINGDB_CITATION}",
        "",
        "As BibTeX, for this server, BindingDB and RDKit (used for structure search, properties and drawings):",
        "",
        "```bibtex",
        bibtex(meta["environment"].get("rdkit")),
        "```",
    ])


def bibtex(rdkit_version: str | None = None) -> str:
    """The BibTeX entries to cite, with the RDKit version when known."""
    return BIBTEX.replace("{rdkit_version}", f"\n  version={{{rdkit_version}}}," if rdkit_version else "")


def _first_line(text: str, limit: int = 80) -> str:
    line = " ".join(text.strip().split("\n", 1)[0].split()).lstrip("#").strip() or "Prompt"
    return line if len(line) <= limit else line[:limit - 1].rstrip() + "…"


def _stamp(timestamp: str) -> str:
    """'2026-11-17T10:22:03+00:00' -> '2026-11-17 10:22:03 UTC'."""
    try:
        t = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError):
        return timestamp or ""
    return f"{t:%Y-%m-%d %H:%M:%S} UTC" if t.tzinfo else f"{t:%Y-%m-%d %H:%M:%S}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _lines(text: str) -> list[str]:
    """Notebook source: a list of lines that keep their line ends."""
    return text.splitlines(keepends=True)


def _mime(file: str) -> str:
    return {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
            ".webp": "image/webp", ".svg": "image/svg+xml"}.get(Path(file).suffix.lower(), "image/png")


def _markdown_output(text: str) -> dict[str, Any]:
    return {"output_type": "display_data", "metadata": {}, "data": {"text/markdown": _lines(text),
                                                                  "text/plain": _lines(text)}}


def _image_output(data: bytes, mime: str) -> dict[str, Any]:
    content = data.decode() if mime == "image/svg+xml" else base64.b64encode(data).decode()
    return {"output_type": "display_data", "metadata": {}, "data": {mime: content, "text/plain": ["<image>"]}}


def _stream(text: str) -> dict[str, Any]:
    return {"output_type": "stream", "name": "stdout", "text": _lines(text)}


# ------------------------------------------------------------------------------------------------ replay

class Rerun:
    """One rerun call or figure: its result, how it compares with the recording, and how it displays."""

    def __init__(self, label: str, tool: str, result: Any, status: str, message: str,
                 images: list[tuple[bytes, str]], max_rows: int | None) -> None:
        self.label, self.tool, self.result, self.status, self.message = label, tool, result, status, message
        self.images = images
        self.max_rows = max_rows

    @property
    def markdown(self) -> str:
        lines = [f"**{self.label}** · {self.message}", ""]
        if self.status != "figure":
            lines += transcript.render_result(self.result, self.max_rows)
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.markdown

    def _ipython_display_(self) -> None:
        from IPython.display import Image, Markdown, SVG, display
        display(Markdown(self.markdown))
        for data, mime in self.images:
            display(SVG(data=data) if mime == "image/svg+xml" else Image(data=data))


def _rerun_from_env() -> bool:
    return os.environ.get(RERUN_ENV, "").strip().lower() in ("1", "true", "yes")


class Replay:
    """Runs the tool calls of a notebook made by create_jupyter_notebook.

    By default it shows each call's recorded result, from data/ in `folder` (the notebook's folder, where
    Jupyter runs it). With `rerun` (or BINDINGDB_RERUN=1) it reruns the calls on a server built in this process
    on a local database: `release` and `source_zip_sha256` are the recorded database's, and a database that
    differs is used anyway, with a warning, since its results may then differ."""

    def __init__(self, release: str, source_zip_sha256: str | None = None, db_path: str | Path | None = None,
                 network: bool = True, max_rows: int | None = None, rerun: bool = False,
                 folder: str | Path | None = None) -> None:
        self.max_rows = max_rows
        self.checks: list[tuple[str, str, str]] = []  # (label, tool, status)
        self.results: dict[int, Any] = {}  # call number -> its result, rerun or recorded
        self.folder = Path(folder) if folder else Path.cwd()
        self.rerun = bool(rerun) or _rerun_from_env()
        if not self.rerun:
            if not (self.folder / "data").is_dir():
                print(f"WARNING: no data/ folder in {self.folder}: run the notebook in its own folder, where its "
                      "recorded results are", file=sys.stderr)
            print(f"Showing the results recorded with BindingDB release {release} (data/). To rerun the calls on a "
                  f"local database, set RERUN = True above or start Jupyter with {RERUN_ENV}=1.")
            return
        from .db import Database
        from .local_build import locate
        from .server import VERSION, build_server, load_substructure_index

        path, pending = locate(str(db_path) if db_path else None)
        if pending is not None:  # no database on this computer yet: build it (once), as the server does
            print(f"No BindingDB database found: building one in {pending.folder} (about half an hour)...")
            pending.wait()
        self.db = Database(path)
        info = self.db.build_info()
        self._figure_dir = Path(tempfile.mkdtemp(prefix="bindingdb-replay-"))
        self.server = build_server(self.db, load_substructure_index(self.db), network=network,
                                   transcript_dir=self._figure_dir)
        warnings = []
        if info.get("release") != release:
            warnings.append(f"this database is release {info.get('release', 'unknown')}, the notebook was "
                            f"recorded with {release}: results may differ")
        if source_zip_sha256 and info.get("source_zip_sha256") not in (None, source_zip_sha256):
            warnings.append("this database was built from a different download of BindingDB (source SHA-256 "
                            f"{info.get('source_zip_sha256')}): results may differ")
        source = source_version()
        print(f"Database: {path}\nRelease {info.get('release', 'unknown')}"
              + (" (as recorded)" if info.get("release") == release else ""))
        print(f"mcp-bindingdb {VERSION}" + (f", commit {source['commit'][:12]}" if source.get("commit") else "")
              + (" with uncommitted changes" if source.get("uncommitted_changes") else ""))
        print(", ".join(f"{k} {v}" for k, v in environment().items()))
        for w in warnings:
            print(f"WARNING: {w}", file=sys.stderr)

    async def _run(self, tool: str, arguments: dict[str, Any]) -> tuple[Any, bool, list[tuple[bytes, str]]]:
        """Call a tool through an MCP client, as a chat does; returns its result, whether it failed, and the
        images of the figures it drew."""
        from mcp import Client

        log = self.server.tool_log
        before = len(log.figures)
        with contextlib.redirect_stderr(io.StringIO()):  # the server's per-call diagnostics, not results
            async with Client(self.server) as client:
                result = await client.call_tool(tool, arguments)
        content = result.structured_content
        if content is None:
            content = "\n".join(c.text for c in result.content if c.type == "text")
        images = [(f.data, _mime(f.file)) for f in log.figures[before:]]
        return content, bool(result.is_error), images

    def _recorded(self, number: int, tool: str, sha256: str | None) -> Rerun:
        """Call `number` as recorded: its result from data/, checked against the digest in its cell."""
        label, name = f"Call {number}", data_file(number)
        try:
            result = json.loads((self.folder / name).read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            self.checks.append((label, tool, "error"))
            return Rerun(label, tool, f"{type(e).__name__}: {e}", "error",
                         f"❌ no recorded result in `{name}`: run the notebook in its folder", [], self.max_rows)
        if sha256 is None or digest(result) == sha256:
            status, message = "recorded", f"recorded result (`{name}`)"
        else:
            status, message = "differs", f"⚠️ `{name}` differs from the recorded result (sha256 `{sha256[:12]}…`)"
        self.checks.append((label, tool, status))
        self.results[number] = result
        return Rerun(label, tool, result, status, message, [], self.max_rows)

    async def call(self, number: int, tool: str, arguments: dict[str, Any], sha256: str | None = None) -> Rerun:
        """Recorded call `number`: rerun and compared with the recorded digest, or as recorded (see Replay)."""
        if not self.rerun:
            return self._recorded(number, tool, sha256)
        label = f"Call {number}"
        try:
            result, failed, images = await self._run(tool, arguments)
        except Exception as e:  # noqa: BLE001 - shown in the notebook, not raised
            result, failed, images = f"{type(e).__name__}: {e}", True, []
        if failed:
            status, message = "error", f"❌ failed: {_first_line(str(result), 300)}"
        elif sha256 is None:
            status, message = "unchecked", "rerun (no recorded digest to compare with)"
        elif (now := digest(result)) == sha256:
            status, message = "same", f"✅ same result as recorded (sha256 `{now[:12]}…`)"
        else:
            status = "differs"
            message = f"⚠️ differs from the recorded result (recorded `{sha256[:12]}…`, now `{now[:12]}…`)"
            if service := NETWORK_TOOLS.get(tool):
                message += f"; {tool} uses {service}, whose answers change over time"
        self.checks.append((label, tool, status))
        self.results[number] = result
        return Rerun(label, tool, result, status, message, images, self.max_rows)

    def result(self, number: int) -> Any:
        """The rerun result of call `number` (e.g. a dict with 'rows'), for the notebook's analysis code."""
        if number not in self.results:
            raise KeyError(f"Call {number} has not been rerun: run its cell first")
        return self.results[number]

    async def figure(self, number: int, tool: str, arguments: dict[str, Any]) -> Rerun:
        """Draw recorded figure `number` again with the tool that drew it (images are not compared); without
        reruns, show the image recorded in figures/."""
        label = f"Figure {number}"
        if not self.rerun:
            found = sorted((self.folder / "figures").glob(f"figure-{number}.*"))
            if not found:
                self.checks.append((label, tool, "error"))
                return Rerun(label, tool, "", "error", f"❌ no recorded image `figures/figure-{number}.*`", [],
                             self.max_rows)
            self.checks.append((label, tool, "shown"))
            return Rerun(label, tool, None, "figure", f"as recorded (`figures/{found[0].name}`)",
                         [(found[0].read_bytes(), _mime(found[0].name))], self.max_rows)
        try:
            result, failed, images = await self._run(tool, arguments)
        except Exception as e:  # noqa: BLE001
            result, failed, images = f"{type(e).__name__}: {e}", True, []
        status = "error" if failed else "figure"
        message = f"❌ failed: {_first_line(str(result), 300)}" if failed else f"redrawn by {tool}"
        self.checks.append((label, tool, "redrawn" if not failed else "error"))
        return Rerun(label, tool, result, status, message, images, self.max_rows)

    def summary(self) -> Summary:
        """How the calls run so far compared with their recorded results."""
        return Summary(self.checks)


class Summary:
    ICONS = {"same": "✅ same", "differs": "⚠️ differs", "error": "❌ failed", "unchecked": "not checked",
             "redrawn": "redrawn", "recorded": "recorded (not rerun)", "shown": "shown as recorded"}

    def __init__(self, checks: list[tuple[str, str, str]]) -> None:
        self.checks = list(checks)

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for _, _, status in self.checks:
            out[status] = out.get(status, 0) + 1
        return out

    @property
    def markdown(self) -> str:
        if not self.checks:
            return "_Nothing has been rerun yet: run the cells above._"
        counts = self.counts()
        head = ", ".join(f"{n} {self.ICONS.get(s, s)}" for s, n in counts.items())
        rows = ["| | tool | result |", "|---|---|---|",
                *(f"| {label} | `{tool}` | {self.ICONS.get(status, status)} |" for label, tool, status in self.checks)]
        note = ([f"_These are the recorded results. To rerun the calls and compare, set `RERUN = True` in the setup "
                 f"cell (or start Jupyter with {RERUN_ENV}=1)._", ""] if "recorded" in counts else [])
        return "\n".join([f"**{head}**", "", *note, *rows])

    def __repr__(self) -> str:
        return self.markdown

    def _ipython_display_(self) -> None:
        from IPython.display import Markdown, display
        display(Markdown(self.markdown))
