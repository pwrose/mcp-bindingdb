"""create_jupyter_notebook: the notebook it writes, and rerunning its cells (without Jupyter)."""

import ast
import base64
import json

import pytest
from mcp import Client

from mcp_bindingdb import notebook
from mcp_bindingdb.db import Database, find_database
from mcp_bindingdb.server import build_server

IMATINIB = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"


def test_digest_ignores_volatile_keys_and_float_noise():
    a = {"overlay_id": "abc", "rows": [{"x": 0.1 + 0.2, "n": 3}], "folder": "/tmp/a"}
    b = {"overlay_id": "def", "rows": [{"n": 3, "x": 0.3}], "folder": "/tmp/b"}
    assert notebook.digest(a) == notebook.digest(b)
    assert notebook.digest(a) != notebook.digest({"rows": [{"x": 0.31, "n": 3}]})
    assert notebook.digest({"rows": [1, 2]}) != notebook.digest({"rows": [2, 1]})  # order matters


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
    DB_PATH = find_database()
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


@needs_db
@pytest.mark.anyio
async def test_notebook_records_and_reruns_the_session(tmp_path, monkeypatch):
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
    assert bad_call.is_error and "calls [9] are not in the log" in bad_call.content[0].text
    assert bad_figure.is_error and "figures [9] are not in the log" in bad_figure.content[0].text
    assert not made.is_error, made.content
    assert "2 exchanges, 2 tool calls, 2 figures (1 redrawn on rerun)" in made.content[0].text

    nb = json.loads((tmp_path / "check.ipynb").read_text())
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
    assert "jupyter lab /path/to/check.ipynb" in header and "--output check-rerun.ipynb" in header
    assert "scripts/build_duckdb.sh --release" in header
    figure_at = next(i for i, t in enumerate(text) if t.startswith("# Figure 1"))
    answer_at = next(i for i, t in enumerate(text) if "It is **BDBM13530**." in t)
    assert figure_at < answer_at  # figures come before the answer, as the chat showed them
    [attached] = [c for c in nb["cells"] if c.get("attachments")]
    assert "attachment:figure-2.png" in "".join(attached["source"]) and "not redrawn" in "".join(attached["source"])
    calls = [c for c in nb["cells"] if c["cell_type"] == "code" and "call" in c["metadata"].get("bindingdb", {})]
    assert [c["metadata"]["bindingdb"]["tool"] for c in calls] == ["search_compounds", "run_sql"]
    assert "BDBM13530" in "".join(calls[0]["outputs"][0]["data"]["text/markdown"])  # the recorded result

    # Rerun: every call matches its recorded digest; then a tampered digest is reported as different.
    monkeypatch.setenv("BINDINGDB_DUCKDB", str(DB_PATH))
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
        made = await client.call_tool("create_jupyter_notebook", {"model": "m", "exchanges": [{"prompt": "CDK2?"}]})
    assert not made.is_error and "every logged call is in a section after the conversation" in made.content[0].text
    [path] = tmp_path.glob("bindingdb-analysis-*.ipynb")
    nb = json.loads(path.read_text())
    assert any("".join(c["source"]).startswith("## BindingDB tool calls") for c in nb["cells"])
    assert any("'search_targets'" in "".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
