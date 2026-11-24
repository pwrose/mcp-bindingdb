"""create_jupyter_notebook: the notebook it writes, and rerunning its cells (without Jupyter)."""

import ast
import base64
import json

import pytest
from mcp import Client

from mcp_bindingdb import notebook
from mcp_bindingdb.db import Database, find_database
from conftest import built_database
from mcp_bindingdb.server import build_server

IMATINIB = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"


def test_digest_ignores_volatile_keys_and_float_noise():
    a = {"overlay_id": "abc", "rows": [{"x": 0.1 + 0.2, "n": 3}], "folder": "/tmp/a"}
    b = {"overlay_id": "def", "rows": [{"n": 3, "x": 0.3}], "folder": "/tmp/b"}
    assert notebook.digest(a) == notebook.digest(b)
    assert notebook.digest(a) != notebook.digest({"rows": [{"x": 0.31, "n": 3}]})
    assert notebook.digest({"rows": [1, 2]}) != notebook.digest({"rows": [2, 1]})  # order matters


def test_bibtex_names_the_rdkit_version_when_known():
    assert "  author={Landrum, G. and others},\n  version={2026.03.6},\n  url=" in notebook.bibtex("2026.03.6")
    assert "version=" not in notebook.bibtex(None) and "{rdkit_version}" not in notebook.bibtex(None)


def test_run_commands_run_in_the_notebook_folder(tmp_path):
    path = tmp_path / "my results" / "a.ipynb"
    commands = notebook.run_commands(path, tmp_path / "bindingdb_202610.duckdb")
    assert commands["jupyter"] == (f"cd '{tmp_path}/my results'\nuv run --no-project --with-requirements "
                                   "requirements.txt --with jupyterlab jupyter lab a.ipynb")
    assert commands["rerun"].startswith(f"cd '{tmp_path}/my results'\nBINDINGDB_RERUN=1 "
                                        f"BINDINGDB_DUCKDB={tmp_path}/bindingdb_202610.duckdb uv run --no-project")
    assert commands["rerun"].endswith("--execute --output a-rerun.ipynb a.ipynb")


def test_requirements_pin_a_published_clean_commit_only():
    commit = "ab" * 20
    line = notebook.server_requirement({"commit": commit, "uncommitted_changes": False, "published": True})
    assert line == f"mcp-bindingdb[substructure,structures,opsin,notebook] @ git+{notebook.REPO_URL}.git@{commit}"
    assert notebook.server_requirement({"commit": commit, "uncommitted_changes": True, "published": True}) is None
    assert notebook.server_requirement({"commit": commit, "uncommitted_changes": False, "published": False}) is None
    assert notebook.server_requirement({}) is None


def test_package_copy_leaves_out_compiled_files_and_build_record():
    files = notebook.package_files()
    assert "mcp_bindingdb/notebook.py" in files and "mcp_bindingdb/builder/__init__.py" in files
    assert not any("__pycache__" in f or f.endswith((".pyc", notebook.BUILD_FILE)) for f in files)


def test_call_source_writes_sql_as_text():
    source = notebook.call_source(2, "run_sql", {"sql": "SELECT 1\nFROM t", "limit": 5}, "ab" * 32, "Call 2")
    assert 'sql = """\nSELECT 1\nFROM t\n"""' in source
    assert "await replay.call(2, 'run_sql', {'sql': sql, 'limit': 5}" in source
    tricky = notebook.call_source(3, "run_sql", {"sql": r"SELECT '\d' AS x"}, None, "Call 3")
    assert "sql = " not in tricky and r"'\\d'" in tricky  # backslashes: kept as a literal


def test_editor_results_become_their_searches_and_panels_are_skipped():
    entry = {"tool": "get_editor_results", "timestamp": "t", "arguments": {"editor_id": "x"},
             "result": {"editor_id": "x", "searches": [
                 {"tool": "substructure_search", "arguments": {"query": "c1ccccc1"}, "ran_at": "t1",
                  "result": {"rows": []}}]}}
    [call] = notebook.expand_call(entry)
    assert call["tool"] == "substructure_search" and call["arguments"] == {"query": "c1ccccc1"} and call["from_editor"]
    assert notebook.expand_call({"tool": "open_structure_editor", "arguments": {}, "result": {}}) == []


try:
    DB_PATH = built_database()
except FileNotFoundError:
    DB_PATH = None
needs_db = pytest.mark.skipif(DB_PATH is None, reason="BindingDB DuckDB file not built")


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def run_cells(nb, namespace):
    """Run a notebook's code cells as Jupyter would (top-level await); returns each cell's value."""
    values = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        tree = ast.parse(source)
        last = tree.body.pop() if tree.body and isinstance(tree.body[-1], ast.Expr) else None
        flags = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        if tree.body:
            result = eval(compile(tree, "<cell>", "exec", flags=flags), namespace)
            if result is not None:
                await result
        value = None
        if last is not None:
            value = eval(compile(ast.Expression(last.value), "<cell>", "eval", flags=flags), namespace)
            if hasattr(value, "__await__"):
                value = await value
        values.append(value)
    return values


PUBLISHED = {"commit": "c0ffee" * 6 + "c0ff", "uncommitted_changes": False, "published": True}


@needs_db
@pytest.mark.anyio
async def test_notebook_records_and_reruns_the_session(tmp_path, monkeypatch):
    monkeypatch.setattr(notebook, "source_version", lambda: PUBLISHED)
    monkeypatch.delenv("BINDINGDB_RERUN", raising=False)
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path / "t")
    plot = tmp_path / "plot.png"
    plot.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="))
    async with Client(srv) as client:
        await client.call_tool("search_compounds", {"query": "imatinib", "limit": 3})
        await client.call_tool("run_sql", {"sql": "SELECT affinity_type, count(*) AS n\nFROM activity\n"
                                                  "GROUP BY 1 ORDER BY n DESC", "limit": 10})
        await client.call_tool("draw_structure_grid", {"title": "Imatinib", "compounds": [
            {"smiles": IMATINIB, "title": "Imatinib"}]})
        await client.call_tool("add_figure", {"title": "A plot", "path": str(plot), "caption": "One pixel."})
        bad_call = await client.call_tool("create_jupyter_notebook", {
            "model": "m", "exchanges": [{"prompt": "p", "calls": [9]}]})
        bad_figure = await client.call_tool("create_jupyter_notebook", {
            "model": "m", "exchanges": [{"prompt": "p", "figures": [9]}]})
        made = await client.call_tool("create_jupyter_notebook", {
            "model": "test-model", "title": "Imatinib check", "output_dir": str(tmp_path), "file_name": "check.ipynb",
            "exchanges": [{"prompt": "Find imatinib.", "answer": "It is **BDBM13530**.", "calls": [1], "figures": [1]},
                          {"prompt": "Counts per type?", "answer": "IC50 leads.", "calls": [2], "figures": [2]}]})
        # A chat that made no figures: the two in the log came from another chat and stay out.
        no_figures = await client.call_tool("create_jupyter_notebook", {
            "model": "m", "output_dir": str(tmp_path), "file_name": "plain.ipynb",
            "exchanges": [{"prompt": "Counts per type?", "answer": "IC50 leads.", "calls": [2]}]})
    assert not no_figures.is_error, no_figures.content
    assert "1 exchange, 1 tool call)" in no_figures.content[0].text
    assert "Left out 2 logged figures no exchange lists (ids 1, 2)" in no_figures.content[0].text
    plain = (tmp_path / "plain" / "plain.ipynb").read_text()
    assert "Figures" not in plain and "image/png" not in plain
    assert bad_call.is_error and "calls [9] are not in the log" in bad_call.content[0].text
    assert bad_figure.is_error and "figures [9] are not in the log" in bad_figure.content[0].text
    assert not made.is_error, made.content
    reply = made.content[0].text
    assert "2 exchanges, 2 tool calls, 2 figures (1 redrawn on rerun)" in reply
    # Its own folder, with what it needs to run: requirements, recorded results, figures, a README, an HTML copy.
    folder = tmp_path / "check"
    assert f"- Folder: {folder} (" in reply and f"- Notebook: {folder / 'check.ipynb'}" in reply
    assert f"HTML copy: {folder / 'check.html'} (" in reply
    page = (folder / "check.html").read_text()
    assert "BDBM13530" in page and "Find imatinib." in page and "data:image/png;base64," in page
    assert "attachment:figure-2.png" not in page  # the add_figure image is embedded too
    assert not (folder / "check-html.log").exists()
    assert (f"cd {folder}\nuv run --no-project --with-requirements requirements.txt --with jupyterlab jupyter lab "
            "check.ipynb\n```") in reply and "nbconvert --to notebook" not in reply
    requirements = (folder / "requirements.txt").read_text().splitlines()
    assert f"mcp-bindingdb[substructure,structures,opsin,notebook] @ git+{notebook.REPO_URL}.git@{PUBLISHED['commit']}" \
        in requirements and any(r.startswith("duckdb==") for r in requirements)
    assert not (folder / "mcp_bindingdb").exists() and "copy of mcp-bindingdb" not in reply
    assert sorted(p.name for p in (folder / "data").iterdir()) == ["call-01.json", "call-02.json"]
    assert sorted(p.name for p in (folder / "figures").iterdir()) == ["figure-1.png", "figure-2.png"]
    readme = (folder / "README.md").read_text()
    assert readme.startswith("# Imatinib check") and "- `data/`: the result each call returned" in readme
    assert "- `figures/figure-2.png`" in readme and "BINDINGDB_RERUN=1 uv run" in readme

    nb = json.loads((folder / "check.ipynb").read_text())
    assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5
    assert len({c["id"] for c in nb["cells"]}) == len(nb["cells"])
    meta = nb["metadata"]["bindingdb"]
    assert meta["model"] == "test-model" and meta["bindingdb_release"] == Database(DB_PATH).build_info()["release"]
    text = ["".join(c["source"]) for c in nb["cells"]]
    header = text[0]
    assert header.startswith("# Imatinib check") and "### How to rerun" in header and "BindingDB release" in header
    assert any("**👤 User**\n\nFind imatinib." in t for t in text)
    assert any("**🧠 Assistant**\n\nIt is **BDBM13530**." in t for t in text)
    assert any(t.startswith("# Figure 1 · draw_structure_grid") for t in text)
    assert "cd /path/to/check\nuv run --no-project --with-requirements requirements.txt --with jupyterlab " \
        "jupyter lab check.ipynb" in header and "--output check-rerun.ipynb check.ipynb" in header
    assert "scripts/build_duckdb.sh --release" in header and "### How to rerun the calls" in header
    cite = text[-1]
    assert cite.startswith("## How to cite") and "@software{rose2026mcp-bindingdb," in cite
    assert "doi={10.1093/nar/gkae1075}" in cite and "doi={10.5281/zenodo.591637}" in cite
    figure_at = next(i for i, t in enumerate(text) if t.startswith("# Figure 1"))
    answer_at = next(i for i, t in enumerate(text) if "It is **BDBM13530**." in t)
    assert figure_at < answer_at  # figures come before the answer, as the chat showed them
    [attached] = [c for c in nb["cells"] if c.get("attachments")]
    assert "attachment:figure-2.png" in "".join(attached["source"]) and "not redrawn" in "".join(attached["source"])
    calls = [c for c in nb["cells"] if c["cell_type"] == "code" and "call" in c["metadata"].get("bindingdb", {})]
    assert [c["metadata"]["bindingdb"]["tool"] for c in calls] == ["search_compounds", "run_sql"]
    assert "BDBM13530" in "".join(calls[0]["outputs"][0]["data"]["text/markdown"])  # the recorded result
    # Call and figure cells open with their source folded (the SQL too), their outputs naming the tool; the
    # setup cell, with its RERUN switch, stays open.
    hidden = lambda c: c["metadata"].get("jupyter", {}).get("source_hidden", False)  # noqa: E731
    redraw = next(c for c in nb["cells"] if "figure" in c["metadata"].get("bindingdb", {}))
    assert all(hidden(c) for c in [*calls, redraw])
    assert "**Call 1** · `search_compounds` · recorded result" in "".join(calls[0]["outputs"][0]["data"]["text/markdown"])
    setup = next(c for c in nb["cells"] if c["cell_type"] == "code")
    assert "RERUN = False" in "".join(setup["source"]) and not hidden(setup)
    # The HTML copy folds them under their first comment line, as JupyterLab does.
    assert page.count('<details class="bdb-fold">') == 3 and "<summary>Call 2 · run_sql" in page

    # Run as it is (in its folder, as Jupyter does): the recorded results and figure, no database needed.
    monkeypatch.chdir(folder)
    monkeypatch.setenv("BINDINGDB_DUCKDB", str(tmp_path / "missing.duckdb"))  # never opened
    values = await run_cells(nb, {})
    assert [v.status for v in values if isinstance(v, notebook.Rerun)] == ["recorded", "figure", "recorded"]
    assert values[-1].counts() == {"recorded": 2, "shown": 1} and "set `RERUN = True`" in values[-1].markdown
    recorded = next(v for v in values if isinstance(v, notebook.Rerun) and v.status == "recorded")
    assert "BDBM13530" in recorded.markdown and "recorded result (`data/call-01.json`)" in recorded.markdown
    shown = next(v for v in values if isinstance(v, notebook.Rerun) and v.status == "figure")
    assert shown.images[0] == ((folder / "figures" / "figure-1.png").read_bytes(), "image/png")

    # Rerun: every call matches its recorded digest; then a tampered digest is reported as different.
    monkeypatch.setenv("BINDINGDB_DUCKDB", str(DB_PATH))
    monkeypatch.setenv("BINDINGDB_RERUN", "1")
    values = await run_cells(nb, {})
    statuses = [v.status for v in values if isinstance(v, notebook.Rerun)]
    assert statuses == ["same", "figure", "same"]
    summary = values[-1]
    assert isinstance(summary, notebook.Summary) and summary.counts() == {"same": 2, "redrawn": 1}
    figure = next(v for v in values if isinstance(v, notebook.Rerun) and v.status == "figure")
    assert figure.images and figure.images[0][1] == "image/png"

    replay = notebook.Replay(release="000000")  # warns, still runs
    rerun = await replay.call(1, "search_compounds", {"query": "imatinib", "limit": 3}, sha256="0" * 64)
    assert rerun.status == "differs" and "differs from the recorded result" in rerun.markdown
    failed = await replay.call(2, "no_such_tool", {})
    assert failed.status == "error"


@needs_db
@pytest.mark.anyio
async def test_notebook_without_listed_calls_takes_the_whole_log(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    async with Client(srv) as client:
        await client.call_tool("search_targets", {"query": "CDK2", "limit": 2})
        made = await client.call_tool("create_jupyter_notebook", {"model": "m",
                                                                  "exchanges": [{"prompt": "CDK2?"}]})
    assert not made.is_error and "every logged call is in a section after the conversation" in made.content[0].text
    assert "- HTML copy: " in made.content[0].text and "jupyter lab" in made.content[0].text
    [path] = tmp_path.glob("bindingdb-analysis-*/bindingdb-analysis-*.ipynb")
    assert path.parent.name == path.stem
    nb = json.loads(path.read_text())
    assert any("".join(c["source"]).startswith("## BindingDB tool calls") for c in nb["cells"])
    assert any("'search_targets'" in "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")


@needs_db
@pytest.mark.anyio
async def test_notebook_includes_the_models_code_inline_or_as_a_module(tmp_path, monkeypatch):
    # An unpushed commit: the folder gets a copy of the package, which the notebook imports from its folder.
    monkeypatch.setattr(notebook, "source_version", lambda: {**PUBLISHED, "published": False})
    monkeypatch.delenv("BINDINGDB_RERUN", raising=False)
    stale = tmp_path / "with-code" / "data" / "call-07.json"  # left by an earlier notebook of the same name
    stale.parent.mkdir(parents=True)
    stale.write_text("{}")
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path / "t")
    plot = tmp_path / "plot.png"
    plot.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="))
    long_code = "\n".join(["def count_rows(result):", '    """How many rows a result has."""',
                           *(f"    x{k} = {k}" for k in range(45)), "    return len(result['rows'])"])
    async with Client(srv) as client:
        await client.call_tool("search_targets", {"query": "CDK2", "limit": 2})  # log 1: not in the notebook
        await client.call_tool("search_compounds", {"query": "imatinib", "limit": 3})  # log 2: notebook Call 1
        await client.call_tool("add_figure", {"title": "Row count", "path": str(plot)})  # figure 1
        args = {"model": "m", "output_dir": str(tmp_path), "file_name": "with-code"}
        unknown = await client.call_tool("create_jupyter_notebook", {**args, "exchanges": [
            {"prompt": "p", "calls": [2], "code": [{"code": "replay.result(1)"}]}]})
        made = await client.call_tool("create_jupyter_notebook", {**args, "exchanges": [{
            "prompt": "How many hits?", "answer": "Three.", "calls": [2], "code": [
                {"code": "rows = replay.result(2)['rows']\nprint(len(rows), 'rows')", "description": "Count hits",
                 "output": "3 rows"},
                {"code": long_code, "run": "n = count_rows(replay.result(2))\nn", "module_name": "Row Count.py",
                 "packages": ["matplotlib"], "figures": [1]},
                {"code": "console.log(1)", "language": "javascript"}]}]})
    assert unknown.is_error and "replay.result(1), but call 1 is not in the notebook" in unknown.content[0].text
    assert not made.is_error, made.content
    reply = made.content[0].text
    folder = tmp_path / "with-code"
    assert "1 figure, 3 code cells" in reply and "the analysis code it imports" in reply
    assert "it is not pushed to GitHub" in reply and "holds a copy of mcp-bindingdb (mcp_bindingdb/)" in reply
    assert json.loads((folder / "mcp_bindingdb" / "_build.json").read_text())["commit"] == PUBLISHED["commit"]
    assert (folder / "mcp_bindingdb" / "notebook.py").is_file() and not stale.exists()
    requirements = (folder / "requirements.txt").read_text()
    assert "mcp-bindingdb[" not in requirements and "copy in mcp_bindingdb/" in requirements
    assert requirements.endswith("# Imported by the analysis code:\nmatplotlib\n")

    nb = json.loads((folder / "with-code.ipynb").read_text())
    text = ["".join(c["source"]) for c in nb["cells"]]
    inline = next(c for c in nb["cells"] if c["metadata"].get("bindingdb", {}).get("code") == 1)
    assert "".join(inline["source"]) == "# Code 1: Count hits\nrows = replay.result(1)['rows']\nprint(len(rows), 'rows')"
    assert "jupyter" not in inline["metadata"]  # short analysis code stays open
    assert inline["outputs"][0]["text"] == ["3 rows\n"]
    module = next(c for c in nb["cells"] if c["metadata"].get("bindingdb", {}).get("module") == "row_count.py")
    assert "from row_count import *\n\nn = count_rows(replay.result(1))\nn" in "".join(module["source"])
    assert "image/png" in module["outputs"][1]["data"]  # the figure the code made, as recorded
    assert not any("attachment:" in t for t in text)  # ... and not also as a figure cell
    assert any("**Code 3** _(javascript, shown as written and not run" in t for t in text)
    assert "the analysis code the notebook imports (`row_count.py`)" in text[0]
    assert "a copy of the mcp-bindingdb code it ran with in `mcp_bindingdb/`" in text[0]
    assert (folder / "row_count.py").read_text().startswith('"""Code 2, from the notebook with-code.ipynb.')

    monkeypatch.chdir(folder)  # Jupyter runs a notebook in its folder, where the module is
    monkeypatch.syspath_prepend(str(folder))
    for rerun, status in ((None, "recorded"), ("1", "same")):  # the code reads recorded and rerun results alike
        if rerun:
            monkeypatch.setenv("BINDINGDB_RERUN", rerun)
            monkeypatch.setenv("BINDINGDB_DUCKDB", str(DB_PATH))
        namespace: dict = {}
        values = await run_cells(nb, namespace)
        assert [v.status for v in values if isinstance(v, notebook.Rerun)] == [status]
        assert namespace["n"] == 3 and len(namespace["rows"]) == 3


@pytest.mark.anyio
async def test_overlay_calls_carry_their_3d_viewer(tmp_path, monkeypatch):
    """An overlay_binding_site call's standalone viewer goes in the notebook's folder (overlays/) and in the
    call's output, and Replay shows it: the recorded one, or the rerun's own."""
    monkeypatch.setattr(notebook, "source_version", lambda: PUBLISHED)
    overlay = tmp_path / "server" / "overlays" / "abc123"
    overlay.mkdir(parents=True)
    page = '<!doctype html><html><body><p class="x">3D "viewer" & co</p><script>render()</script></body></html>'
    (overlay / "overlay.html").write_text(page)
    result = {"overlay_id": "abc123", "title": "ABL1", "entries": [], "folder": str(overlay)}
    entry = {"tool": "overlay_binding_site", "arguments": {"uniprot": "P00519", "pdb_ids": ["1IEP"]},
             "result": result, "timestamp": "2026-11-23T23:52:47Z"}
    gone = {**entry, "result": {**result, "folder": str(tmp_path / "pruned")}}  # an overlay the server dropped
    nb, counts, files = notebook.build_notebook(
        title="Overlay", when="2026-11-23", model="m", build_info={"release": "202611"}, generated_by="t",
        exchanges=[{"prompt": "Overlay it.", "answer": "Done.", "calls": [entry, gone], "figures": []}],
        leftover_calls=[], unplaced_figures=[], skills=[], mcp_servers=[], max_rows=None, file_name="o.ipynb")
    assert files["overlays/call-01.html"] == page and "overlays/call-02.html" not in files
    assert nb["metadata"]["bindingdb"]["overlay_files"] == ["overlays/call-01.html"]
    first, second = [c for c in nb["cells"] if "call" in c["metadata"].get("bindingdb", {})]
    viewer = "".join(first["outputs"][1]["data"]["text/html"])
    assert viewer.startswith("<iframe srcdoc=\"") and "&quot;viewer&quot; &amp; co" in viewer and 'sandbox="' in viewer
    assert len(second["outputs"]) == 1
    assert "the 3D viewers of the binding-site overlays in `overlays/`" in "".join(nb["cells"][0]["source"])
    assert "- `overlays/call-01.html`: the 3D viewer of Call 1's binding-site overlay" in files["README.md"]

    # Replayed as recorded, from the notebook's folder; a call without a viewer file shows none.
    for name, content in files.items():
        path = tmp_path / "nb" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content) if isinstance(content, str) else path.write_bytes(content)
    replay = notebook.Replay(release="202611", folder=tmp_path / "nb")
    shown = await replay.call(1, "overlay_binding_site", entry["arguments"])
    assert shown.status == "recorded" and shown.viewer == page
    assert (await replay.call(2, "overlay_binding_site", gone["arguments"])).viewer is None
    # A rerun's result names the new overlay's folder, whose viewer it shows.
    assert notebook.overlay_page("overlay_binding_site", result) == page
    assert notebook.overlay_page("overlay_binding_site", gone["result"]) is None
    assert notebook.overlay_page("search_compounds", result) is None
