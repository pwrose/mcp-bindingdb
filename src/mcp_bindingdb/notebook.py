"""Jupyter notebooks that rerun a session's BindingDB tool calls (create_jupyter_notebook).

`build_notebook` writes the notebook: the prompts and answers, a code cell per tool call with the result as
it was recorded, the figures, and the provenance (BindingDB release and source checksum, server version and
commit, model). `Replay` is what those cells run: it builds this server in-process on a local copy of the
database, calls each tool again, shows the result and reports whether it matches the recorded one (by a
SHA-256 digest of the result, see `digest`).
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import math
import platform
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import transcript

REPO_URL = "https://github.com/pwrose/mcp-bindingdb"
BINDINGDB_CITATION = ("Liu T, Hwang L, Burley SK, Nitsche CI, Southan C, Walters WP, Gilson MK. BindingDB in 2024: "
                      "a FAIR knowledgebase of protein-small molecule binding data. Nucleic Acids Research 53(D1), 2025.")

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
    """The git commit of this package's checkout, if it is one, and whether it has uncommitted changes."""
    folder = Path(__file__).resolve().parent
    try:
        commit = subprocess.run(["git", "-C", str(folder), "rev-parse", "HEAD"], capture_output=True,
                                text=True, timeout=5, check=True).stdout.strip()
        status = subprocess.run(["git", "-C", str(folder), "status", "--porcelain", "--", "."],
                                capture_output=True, text=True, timeout=5, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    return {"commit": commit, "uncommitted_changes": bool(status.strip())} if commit else {}


def environment() -> dict[str, str]:
    """Versions of the software that computes the results."""
    versions = {"python": platform.python_version()}
    for module, name in (("duckdb", "duckdb"), ("rdkit", "rdkit"), ("mcp", "mcp"), ("gemmi", "gemmi")):
        try:
            versions[name] = getattr(__import__(module), "__version__", None) or _dist_version(name)
        except ImportError:
            continue
    return {k: v for k, v in versions.items() if v}


def _dist_version(name: str) -> str:
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version(name)
    except PackageNotFoundError:
        return ""


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
                   max_rows: int | None, file_name: str = "notebook.ipynb") -> tuple[dict[str, Any], dict[str, int]]:
    """The notebook (nbformat 4.5, as a dict) and counts of what it holds.

    `exchanges` are dicts with prompt, answer, `calls` (logged entries, see ToolLog) and `figures`
    (figures.Figure); `leftover_calls` go in a section after the conversation (when no exchange lists its
    calls), as do `unplaced_figures`."""
    nb = _Notebook(max_rows)
    release = build_info.get("release", "unknown")
    source = source_version()
    env = environment()
    numbers = transcript.figure_numbers([{"figures": [f.id for f in e["figures"]]} for e in exchanges],
                                        unplaced_figures)

    body_start = len(nb.cells)
    for k, exchange in enumerate(exchanges, start=1):
        nb.markdown(f"## Exchange {k}\n\n**👤 User**\n\n{(exchange.get('prompt') or '(no prompt)').strip()}")
        for entry in exchange["calls"]:
            nb.calls(entry)
        for figure in exchange["figures"]:  # before the answer, as the chat showed them
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
              "redrawn_figures": nb.n_redrawn, "skipped_calls": nb.n_skipped}
    meta = {"title": title, "date": when, "model": model, "bindingdb_release": release,
            "bindingdb_build": {k: v for k, v in build_info.items() if k != "table_row_counts"},
            "generated_by": generated_by, "generated_at": _utc_now(), **({"source": source} if source else {}),
            "environment": env, **({"skills": skills} if skills else {}),
            **({"external_mcp_servers": mcp_servers} if mcp_servers else {}), "contents": counts}
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
    return notebook, counts


class _Notebook:
    def __init__(self, max_rows: int | None) -> None:
        self.cells: list[dict[str, Any]] = []
        self.max_rows = max_rows
        self.n_calls = self.n_redrawn = self.n_skipped = 0

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

    def figure(self, figure: Any, number: int) -> None:
        caption = f"**Figure {number}: {figure.title.strip().rstrip('.')}.**" + \
                  (f" {figure.caption}" if figure.caption else "")
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
    return "\n".join([
        "# Reruns this session's BindingDB tool calls on a local copy of the same BindingDB release (see",
        "# 'How to rerun' above). The database is the one in BINDINGDB_DUCKDB, else in mcp-bindingdb's data/",
        "# folder; or pass db_path='/path/to/bindingdb_<release>.duckdb' here.",
        "from mcp_bindingdb.notebook import Replay",
        "",
        f"replay = Replay({', '.join(args)})",
    ])


def _header(meta: dict[str, Any], counts: dict[str, int], file_name: str) -> str:
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
    contents = [transcript.plural(counts["exchanges"], "exchange"), transcript.plural(counts["calls"], "tool call")]
    if counts["figures"]:
        contents.append(transcript.plural(counts["figures"], "figure"))
    lines = [
        f"# {meta['title']}", "",
        "A reproducible record of an AI-assisted BindingDB analysis: each prompt, the BindingDB tool calls that "
        "answered it with their recorded results, the answer, and its figures. Run all cells to rerun every "
        "call on your own copy of the database and check each result against the recorded one.", "",
        f"- **Date:** {meta['date']}",
        f"- **Model:** {meta['model']}",
        *([f"- **Skills:** {' · '.join(meta['skills'])}"] if meta.get("skills") else []),
        *([f"- **External MCP servers:** {' · '.join(meta['external_mcp_servers'])}"]
          if meta.get("external_mcp_servers") else []),
        f"- **Data:** {data}",
        *([f"- **Database build:** {build['built_at']}" + (f", DuckDB {build['duckdb_version']}"
                                                            if build.get("duckdb_version") else "")]
          if build.get("built_at") else []),
        *([f"- **Derived data:** {'; '.join(derived)}"] if (derived := [build[k] for k in ("inchi_keys", "properties")
                                                                         if build.get(k)]) else []),
        f"- **Server:** {server}",
        f"- **Software:** {', '.join(f'{k} {v}' for k, v in meta['environment'].items())}",
        f"- **Notebook generated:** {meta['generated_at']}",
        f"- **Contents:** {' · '.join(contents)}",
        "",
        *_rerun_steps(meta, file_name),
        "Each call cell shows its result as recorded until it is run; running it shows the new result with ✅ "
        "when it matches the recorded one (SHA-256 of the result, floats to "
        f"{SIGNIFICANT_DIGITS} significant digits, ids of viewers and files left out). Calls to PubChem, RCSB "
        "or PDBe depend on those services and may differ. The prose answers are the model's and are not "
        "recomputed.",
    ]
    return "\n".join(lines)


def _rerun_steps(meta: dict[str, Any], file_name: str) -> list[str]:
    """'How to rerun': the commands for a computer that runs mcp-bindingdb, then the setup from scratch."""
    release = meta["bindingdb_release"]
    commit = (meta.get("source") or {}).get("commit")
    stem = file_name[:-len(".ipynb")] if file_name.endswith(".ipynb") else file_name
    checks = "release" + (" and source checksum" if meta["bindingdb_build"].get("source_zip_sha256") else "")
    return [
        "### How to rerun", "",
        "Jupyter must run in mcp-bindingdb's Python environment, so start it from the mcp-bindingdb folder "
        "with `uv run` (replace the paths with yours):", "",
        "```bash",
        "cd /path/to/mcp-bindingdb",
        f"uv run --all-extras --with jupyterlab jupyter lab /path/to/{file_name}",
        "```", "",
        "and choose Run → Run All Cells. To rerun it without opening Jupyter, writing a copy with the new "
        "results:", "",
        "```bash",
        "cd /path/to/mcp-bindingdb",
        f"uv run --all-extras --with nbconvert jupyter nbconvert --to notebook --execute --output "
        f"{stem}-rerun.ipynb /path/to/{file_name}",
        "```", "",
        "The database is found in the folder's `data/`; if it is elsewhere, put "
        f"`BINDINGDB_DUCKDB=/path/to/bindingdb_{release}.duckdb` before `uv run`. VS Code works too, with the "
        "folder's `.venv` as the kernel.", "",
        f"**Without mcp-bindingdb** (needs [uv](https://docs.astral.sh/uv/) and Docker), first get the code "
        f"and build the database of release {release} (about 4.5 GB in `data/`; see "
        "`docs/building-the-database.md`):", "",
        "```bash",
        f"git clone {REPO_URL}.git",
        "cd mcp-bindingdb",
        *([f"git checkout {commit}"] if commit else []),
        f"scripts/build_duckdb.sh --release {release}",
        "```", "",
        f"then run the commands above. The setup cell checks the database's {checks} against the recorded "
        "ones.", "",
    ]


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
    ])


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


class Replay:
    """Reruns tool calls in a notebook made by create_jupyter_notebook, on a server built in this process.

    `release` and `source_zip_sha256` are the recorded database's; a database that differs is used anyway,
    with a warning, since its results may then differ."""

    def __init__(self, release: str, source_zip_sha256: str | None = None, db_path: str | Path | None = None,
                 network: bool = True, max_rows: int | None = None) -> None:
        from .db import Database, find_database
        from .server import VERSION, build_server, load_substructure_index

        path = Path(db_path).expanduser() if db_path else find_database()
        self.db = Database(path)
        info = self.db.build_info()
        self.max_rows = max_rows
        self.checks: list[tuple[str, str, str]] = []  # (label, tool, status)
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

    async def call(self, number: int, tool: str, arguments: dict[str, Any], sha256: str | None = None) -> Rerun:
        """Rerun recorded call `number` and compare its result with the recorded digest."""
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
        return Rerun(label, tool, result, status, message, images, self.max_rows)

    async def figure(self, number: int, tool: str, arguments: dict[str, Any]) -> Rerun:
        """Draw recorded figure `number` again with the tool that drew it (images are not compared)."""
        label = f"Figure {number}"
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
             "redrawn": "redrawn"}

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
        return "\n".join([f"**{head}**", "", *rows])

    def __repr__(self) -> str:
        return self.markdown

    def _ipython_display_(self) -> None:
        from IPython.display import Markdown, display
        display(Markdown(self.markdown))
