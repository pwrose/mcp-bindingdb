"""End-to-end tests against the real DuckDB build, through an in-process MCP client."""

import base64
import json
import re

import pytest
from mcp import Client

from mcp_bindingdb import names
from mcp_bindingdb.db import Database, find_database
from mcp_bindingdb.server import build_server

try:
    DB_PATH = find_database()
except FileNotFoundError:
    pytest.skip("BindingDB DuckDB file not built", allow_module_level=True)

IMATINIB = 13530  # BDBM13530
PALBOCICLIB = 6309
ASPIRIN = 22360
EGFR = 520  # wild-type human EGFR polymer
pytestmark = pytest.mark.anyio


@pytest.fixture(scope="module")
def server():
    return build_server(Database(DB_PATH))


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def call(server, tool, **args):
    async with Client(server) as client:
        result = await client.call_tool(tool, args)
    return result


async def ok(server, tool, **args):
    result = await call(server, tool, **args)
    assert not result.is_error, result.content
    return result.structured_content


async def test_lists_all_tools(server):
    async with Client(server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == {
        "search_compounds", "search_targets", "get_compound", "get_target", "find_ligands_for_target",
        "find_targets_for_compound", "get_activity", "describe_tables", "run_sql", "chemical_name_to_smiles",
        "create_transcript", "transcript_to_html", "reset_tool_log", "get_tool_log", "draw_structure_grid",
        "add_figure", "open_structure_editor", "editor_pubchem_candidates", "editor_search", "get_editor_results",
        "figure_image",
        "exact_structure_search",
    }
    writes = {"reset_tool_log", "transcript_to_html", "create_transcript", "draw_structure_grid",
              "add_figure"}  # write files
    assert all(t.annotations.read_only_hint for name, t in tools.items() if name not in writes)


@pytest.mark.skipif("inchi_keys" not in Database(DB_PATH).build_info(),
                    reason="InChIKeys not computed (scripts/compute_inchikeys.py)")
async def test_exact_structure_search_finds_every_entry(server):
    imatinib = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"
    out = await ok(server, "exact_structure_search", smiles=imatinib)
    # BindingDB stores no InChIKey for 31341 and a non-matching one for 86734.
    assert {r["monomerid"] for r in out["rows"]} == {IMATINIB, 31341, 86734} and "note" not in out
    salt = await ok(server, "exact_structure_search", smiles=imatinib + ".CS(=O)(=O)O")
    assert IMATINIB not in {r["monomerid"] for r in salt["rows"]}  # the mesylate is a different molecule
    potent = await ok(server, "exact_structure_search", smiles=imatinib, affinity_types=["Kd"], min_value_nm=10,
                      max_value_nm=100)
    assert potent["rows"] and all(r["affinity_type"] == "Kd" and 10 <= r["value"] <= 100 for r in potent["rows"])


async def test_search_compounds_by_name_ranks_exact_first(server):
    out = await ok(server, "search_compounds", query="imatinib", limit=5)
    assert out["rows"][0]["monomerid"] == IMATINIB


@pytest.mark.parametrize("query", ["BDBM13530", "13530", "CHEMBL941", "cid_5291",
                                   "KTUFNOKKBVMGRW-UHFFFAOYSA-N", "KTUFNOKKBVMGRW"])
async def test_search_compounds_by_identifier(server, query):
    out = await ok(server, "search_compounds", query=query)
    assert IMATINIB in [r["monomerid"] for r in out["rows"]]


async def test_search_targets_by_gene_and_uniprot(server):
    by_name = await ok(server, "search_targets", query="EGFR", organism="Homo sapiens", limit=5)
    assert by_name["rows"][0]["target_id"] == EGFR
    by_acc = await ok(server, "search_targets", query="P00533")
    assert by_acc["rows"][0]["target_id"] == EGFR  # wild type ranks before mutants
    assert len(by_acc["rows"]) > 1


async def test_get_compound_and_target(server):
    c = await ok(server, "get_compound", monomerid=IMATINIB)
    assert c["compound"]["inchi_key"] == "KTUFNOKKBVMGRW-UHFFFAOYSA-N"
    assert "Imatinib" in c["synonyms"]
    assert any(t["uniprot_raw"] == "P00519" for t in c["top_targets"])  # ABL1
    t = await ok(server, "get_target", target_id=EGFR)
    assert t["target"]["uniprot"] == "P00533" and "sequence" not in t["target"]
    assert {r["affinity_type"] for r in t["measurements_by_type"]} >= {"IC50", "Ki", "Kd"}


async def test_find_ligands_potency_filter(server):
    out = await ok(server, "find_ligands_for_target", uniprot="P00533", affinity_types=["Ki"],
                   max_value_nm=1.0, limit=100)
    rows = out["rows"]
    assert rows and all(r["affinity_type"] == "Ki" and r["value"] <= 1.0 and r["relation"] != ">" for r in rows)
    assert len({r["monomerid"] for r in rows}) == len(rows)  # best per compound
    assert all(r["uniprot_raw"] == "P00533" for r in rows)  # wild type only by default


async def test_find_targets_for_compound(server):
    out = await ok(server, "find_targets_for_compound", inchi_key="KTUFNOKKBVMGRW", max_value_nm=100)
    uniprots = {r["uniprot_raw"] for r in out["rows"]}
    assert "P00519" in uniprots
    ps = [r["p_affinity"] for r in out["rows"]]
    assert ps == sorted(ps, reverse=True)


async def test_get_activity(server):
    rows = (await ok(server, "find_ligands_for_target", target_id=EGFR, limit=1))["rows"]
    out = await ok(server, "get_activity", ki_result_id=rows[0]["ki_result_id"])
    assert out["measurement"]["ki_result_id"] == rows[0]["ki_result_id"]
    assert out["reactants"]["polymerid"] == EGFR


async def test_describe_tables(server):
    out = await ok(server, "describe_tables")
    names = {t["table_name"] for t in out["tables"]}
    assert {"activity", "compound", "ki_result"} <= names and not names & {"regusers", "person"}
    cols = await ok(server, "describe_tables", table="activity")
    assert "p_affinity" in [c["column_name"] for c in cols["columns"]]


async def test_run_sql_limit_and_truncation(server):
    out = await ok(server, "run_sql", sql="SELECT * FROM range(10)", limit=3)
    assert out["row_count"] == 3 and out["truncated"]


@pytest.mark.parametrize("sql", [
    "CREATE TABLE x AS SELECT 1",
    "DROP TABLE activity",
    "SELECT * FROM read_csv('/etc/hosts')",
    "COPY (SELECT 1) TO '/tmp/mcp_bindingdb_test.csv'",
    "SET enable_external_access = true",
    "INSTALL httpfs",
    "SELECT * FROM nonexistent_table",
])
async def test_run_sql_rejects_writes_and_external_access(server, sql):
    result = await call(server, "run_sql", sql=sql)
    assert result.is_error


async def test_query_timeout():
    srv = build_server(Database(DB_PATH, timeout_s=0.5))
    result = await call(srv, "run_sql", sql="SELECT count(*) FROM range(1000000000) a, range(1000) b "
                                            "WHERE (a.range * b.range) % 7 = 3")
    assert result.is_error and "time limit" in result.content[0].text


async def test_name_to_smiles_from_bindingdb(server):
    out = await ok(server, "chemical_name_to_smiles", name="Palbociclib")
    assert out["resolved"] and out["source"] == "bindingdb" and out["monomerid"] == PALBOCICLIB
    assert out["inchi_key"] == "AHJRHEGDXFFMBM-UHFFFAOYSA-N" and not out["ambiguous"]
    assert [t["source"] for t in out["sources_tried"]] == ["bindingdb"]


async def test_name_to_smiles_flags_ambiguous_bindingdb_names(server):
    out = await ok(server, "chemical_name_to_smiles", name="compound 5", sources=["bindingdb"])
    assert out["ambiguous"] and len(out["candidates"]) > 1


requires_opsin = pytest.mark.skipif(names.opsin_unavailable_reason() is not None,
                                    reason=str(names.opsin_unavailable_reason()))


@requires_opsin
async def test_name_to_smiles_from_opsin_maps_to_bindingdb(server):
    out = await ok(server, "chemical_name_to_smiles", name="2-acetyloxybenzoic acid")
    assert out["resolved"] and out["source"] == "opsin"
    assert out["inchi_key"] == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
    assert out["bindingdb_matches"][0]["monomerid"] == ASPIRIN and out["bindingdb_matches"][0]["exact_match"]


async def test_name_to_smiles_from_pubchem(server, monkeypatch):
    def fake_pubchem(name):
        assert name == "Ibrance-like"
        return names.Structure("CC(=O)Oc1ccccc1C(=O)O", "BSYNRYMUTXBXSQ-UHFFFAOYSA-N", title="Aspirin", cid=2244)
    monkeypatch.setattr(names, "pubchem_lookup", fake_pubchem)
    out = await ok(server, "chemical_name_to_smiles", name="Ibrance-like", sources=["bindingdb", "pubchem"])
    assert out["source"] == "pubchem" and out["pubchem_cid"] == 2244
    assert out["bindingdb_matches"][0]["monomerid"] == ASPIRIN
    assert [t["status"] for t in out["sources_tried"]] == ["not found", "found"]


async def test_name_to_smiles_reports_failures(server, monkeypatch):
    def broken_pubchem(name):
        raise names.NameLookupError("PubChem: HTTP 503 Service Unavailable")
    monkeypatch.setattr(names, "pubchem_lookup", broken_pubchem)
    out = await ok(server, "chemical_name_to_smiles", name="not a compound xyzzy", sources=["bindingdb", "pubchem"])
    assert not out["resolved"]
    assert out["sources_tried"][1] == {"source": "pubchem", "status": "error",
                                       "detail": "PubChem: HTTP 503 Service Unavailable"}


async def test_name_to_smiles_without_network():
    out = await ok(build_server(Database(DB_PATH), network=False), "chemical_name_to_smiles",
                   name="not a compound xyzzy", sources=["pubchem"])
    assert not out["resolved"] and out["sources_tried"][0]["status"] == "unavailable"


async def test_transcript_shows_prompts_and_logged_calls():
    srv = build_server(Database(DB_PATH))
    async with Client(srv) as client:
        await client.call_tool("search_compounds", {"query": "imatinib", "limit": 3})
        await client.call_tool("run_sql", {"sql": "SELECT 42 AS answer"})
        await client.call_tool("describe_tables", {})  # schema lookups are not logged
        await client.call_tool("get_compound", {"monomerid": -1})  # nor are failed calls
        plain = (await client.call_tool("create_transcript", {"model": "test-model"})).content[0].text
        result = await client.call_tool("create_transcript", {
            "model": "test-model", "date": "2026-10-23", "include_tool_calls": True,
            "exchanges": [{"prompt": "What is imatinib?", "answer": "A kinase inhibitor."}]})
        md = result.content[0].text
        cleared = (await client.call_tool("reset_tool_log", {})).structured_content
        assert cleared == {"cleared": 2, "figures_cleared": 0}
    assert "#### Call" not in plain and "- **Contents:** 0 exchanges\n" in plain  # tool calls are opt-in
    assert md.startswith("# BindingDB Chat Transcript\n")
    assert "- **Model:** test-model" in md and "- **Contents:** 1 exchange · 2 tool calls" in md
    assert "👤 **User**\n\nWhat is imatinib?" in md and "🧠 **Assistant**\n\nA kinase inhibitor." in md
    assert "search_compounds(query='imatinib', limit=3)" in md
    assert "```sql\nSELECT 42 AS answer\n```" in md and "| 42 |" in md
    assert md.count("#### Call ") == 2


async def test_transcript_of_selected_calls():
    srv = build_server(Database(DB_PATH))
    async with Client(srv) as client:
        await client.call_tool("search_compounds", {"query": "aspirin", "limit": 1})  # an earlier chat
        await client.call_tool("search_compounds", {"query": "imatinib", "limit": 1})
        await client.call_tool("run_sql", {"sql": "SELECT 42 AS answer"})
        log = (await client.call_tool("get_tool_log", {})).structured_content["calls"]
        result = await client.call_tool("create_transcript", {"model": "m", "calls": [3, 2]})
        bad = await client.call_tool("create_transcript", {"model": "m", "calls": [4]})
    assert [c["index"] for c in log] == [1, 2, 3]
    assert log[1]["call"] == "search_compounds(query='imatinib', limit=1)"
    md = result.content[0].text
    assert "1 exchange" not in md and "- **Contents:** 0 exchanges · 2 tool calls" in md
    assert "aspirin" not in md and md.index("imatinib") < md.index("SELECT 42")
    assert bad.is_error and "not in the log" in bad.content[0].text


async def test_markdown_transcript_converts_to_html_with_structures(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    answer = ("**Gleevec** <script>alert(1)</script>\n\n| compound | SMILES |\n|---|---|\n"
              "| aspirin | `CC(=O)Oc1ccccc1C(=O)O` |\n| not a molecule | xyz |")
    async with Client(srv) as client:
        missing = await client.call_tool("transcript_to_html", {})
        await client.call_tool("search_compounds", {"query": "imatinib", "limit": 2})
        md = await client.call_tool("create_transcript", {
            "model": "test-model", "include_tool_calls": True,
            "exchanges": [{"prompt": "What is imatinib?", "answer": answer}]})
        assert "base64" not in md.content[0].text  # the Markdown itself has no drawings
        result = await client.call_tool("transcript_to_html", {})
        assert not result.is_error, result.content
        link = result.content[1]
        assert link.uri == "transcript://session/latest.html"
        resource = (await client.read_resource(link.uri)).contents[0].text
        given = await client.call_tool("transcript_to_html", {"markdown": "# Mine\n\n| smiles |\n|---|\n| CCO |"})
    assert missing.is_error and "create_transcript first" in missing.content[0].text
    [path, _] = sorted(tmp_path.glob("*.html"))
    page = path.read_text()
    assert path.name.startswith("bindingdb-chat-transcript-")
    assert page == resource and str(path) in result.content[0].text and "3 structures drawn" in result.content[0].text
    assert "<strong>Gleevec</strong> &lt;script&gt;" in page and "<script" not in page
    assert page.count("<th>structure</th>") == 2  # the answer's table and the search result
    assert page.count('<img class="structure"') == 3  # aspirin and 2 imatinib rows; not "xyz"
    assert "<footer>3 structures drawn with RDKit.</footer>" in page
    assert "'Mine'" in given.content[0].text and "1 structure drawn" in given.content[0].text


async def test_html_transcript_in_one_call(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    answer = "| compound | SMILES |\n|---|---|\n| aspirin | CC(=O)Oc1ccccc1C(=O)O |"
    async with Client(srv) as client:
        result = await client.call_tool("create_transcript", {
            "model": "test-model", "format": "html", "exchanges": [{"prompt": "Aspirin?", "answer": answer}]})
    assert not result.is_error, result.content
    assert "1 structure drawn" in result.content[0].text and "- **Contents:** 1 exchange" in result.content[0].text
    [path] = tmp_path.glob("*.html")
    assert str(path) in result.content[0].text and path.read_text().count('<img class="structure"') == 1


SORAFENIB = "CNC(=O)c1cc(ccn1)Oc2ccc(cc2)NC(=O)Nc3ccc(c(c3)C(F)(F)F)Cl"
BOSUTINIB = "CN1CCN(CC1)CCCOc2cc3c(cc2OC)c(c(cn3)C#N)Nc4cc(c(cc4Cl)Cl)OC"
CLOZAPINE = "CN1CCN(CC1)C2=Nc3cc(ccc3Nc4c2cccc4)Cl"


async def test_structure_grid_figure_in_transcripts(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    compounds = [
        {"smiles": SORAFENIB, "title": "Sorafenib", "subtitle": "FDA 2005",
         "bars": [{"label": "RAF1", "value_nm": 6, "type": "IC50", "note": "n = 32"}]},
        {"smiles": BOSUTINIB, "title": "Bosutinib", "bars": [{"label": "ABL1", "value_nm": 0.06, "type": "Kd"}]},
        {"smiles": CLOZAPINE, "title": "Clozapine <b>", "caption": "8-chloro ring"},
    ]
    async with Client(srv) as client:
        bad_core = await client.call_tool("draw_structure_grid", {"title": "x", "compounds": compounds,
                                                                  "align_to": "not a smiles ("})
        grid = await client.call_tool("draw_structure_grid", {
            "title": "Chloroanilines", "compounds": compounds, "align_to": "Nc1ccc(Cl)cc1"})
        unknown = await client.call_tool("create_transcript", {"model": "m", "exchanges": [
            {"prompt": "Grid?", "figures": [7]}]})
        md = await client.call_tool("create_transcript", {"model": "m", "exchanges": [
            {"prompt": "Grid?", "answer": "Here.", "figures": [1]}]})
        page = await client.call_tool("create_transcript", {"model": "m", "format": "html", "exchanges": [
            {"prompt": "Grid?", "answer": "Here.", "figures": [1]}]})
        log = (await client.call_tool("get_tool_log", {})).structured_content
    assert bad_core.is_error and "not valid SMILES or SMARTS" in bad_core.content[0].text
    image, text = grid.content
    assert image.type == "image" and image.mime_type == "image/png"
    assert text.text.startswith("Figure id 1: 'Chloroanilines', 3 compounds, aligned on Nc1ccc(Cl)cc1.")
    [png] = (tmp_path / "figures").glob("chloroanilines-*-1.png")
    assert png.read_bytes()[:4] == b"\x89PNG"
    assert log["figures"][0]["id"] == 1 and log["figures"][0]["title"] == "Chloroanilines"
    assert unknown.is_error and "figures [7] are not in the log" in unknown.content[0].text
    markdown, note = md.content
    assert f"Here.\n\n![Figure 1: Chloroanilines](figures/{png.name})" in markdown.text
    assert "- **Contents:** 1 exchange · 1 figure" in markdown.text
    [saved_md] = tmp_path.glob("*.md")
    assert saved_md.read_text() == markdown.text and str(saved_md) in note.text
    [html_path] = tmp_path.glob("*.html")
    html_page = html_path.read_text()
    assert "1 figure" in page.content[0].text and f"figures/{png.name}" not in html_page
    assert html_page.count('<article class="sg-card">') == 3 and "Clozapine &lt;b&gt;" in html_page


async def test_figure_compounds_not_drawn_again_in_tables(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    compounds = [{"smiles": s, "title": t} for s, t in [(SORAFENIB, "a"), (BOSUTINIB, "b")]]
    rewritten = "FC(F)(F)c1cc(NC(=O)Nc2ccc(Oc3ccnc(C(=O)NC)c3)cc2)ccc1Cl"  # sorafenib, other SMILES
    same = f"| drug | SMILES |\n|---|---|\n| a | {rewritten} |\n| b | {BOSUTINIB} |"
    more = f"| drug | SMILES |\n|---|---|\n| a | {SORAFENIB} |\n| c | {CLOZAPINE} |"
    async with Client(srv) as client:
        untyped = await client.call_tool("draw_structure_grid", {"title": "x", "compounds": [
            {"smiles": SORAFENIB, "title": "a", "bars": [{"label": "RAF1", "value_nm": 6}]}]})
        await client.call_tool("draw_structure_grid", {"title": "Grid", "compounds": compounds})
        exchanges = [{"prompt": "1", "answer": f"See Figure 1.\n\n{same}\n\n{more}", "figures": [1]},
                     {"prompt": "2", "answer": same}]
        await client.call_tool("create_transcript", {"model": "m", "format": "html", "exchanges": exchanges})
        markdown = (await client.call_tool("create_transcript", {"model": "m", "title": "Saved",
                                                                 "exchanges": exchanges})).content[0].text
    async with Client(build_server(Database(DB_PATH), transcript_dir=tmp_path)) as client:  # a later process
        await client.call_tool("transcript_to_html", {"markdown": markdown})
    assert untyped.is_error and "type" in untyped.content[0].text
    pages = [p.read_text() for p in sorted(tmp_path.glob("*.html"))]  # the figure from the log, then its PNG
    # Exchange 1: the first table is all in its figure, the second is not; exchange 2 has no figure.
    assert len(pages) == 2 and all(p.count('<img class="structure"') == 4 for p in pages)
    assert all(p.count("<th>structure</th>") == 2 for p in pages)


PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==")
SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>'


async def test_add_figure_images_in_transcripts(tmp_path):
    plot = tmp_path / "plots" / "heatmap.png"
    plot.parent.mkdir()
    plot.write_bytes(PNG_1X1)
    (tmp_path / "notes.txt").write_text("not an image")
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path / "out")
    async with Client(srv) as client:
        added = await client.call_tool("add_figure", {"title": "Heat map", "path": str(plot),
                                                      "caption": "Clustered pKi."})
        svg = await client.call_tool("add_figure", {"title": "Bars",
                                                    "data": base64.b64encode(SVG.encode()).decode()})
        both = await client.call_tool("add_figure", {"title": "x", "path": str(plot), "data": "AA=="})
        missing = await client.call_tool("add_figure", {"title": "x", "path": str(tmp_path / "nope.png")})
        not_image = await client.call_tool("add_figure", {"title": "x", "path": str(tmp_path / "notes.txt")})
        md = await client.call_tool("create_transcript", {"model": "m", "exchanges": [
            {"prompt": "Plot?", "answer": "Here.", "figures": [1, 2]}]})
        await client.call_tool("create_transcript", {"model": "m", "format": "html", "exchanges": [
            {"prompt": "Plot?", "answer": "Here.", "figures": [1, 2]}]})
        log = (await client.call_tool("get_tool_log", {})).structured_content
    assert added.content[0].text.startswith("Figure id 1: 'Heat map' (PNG, ")
    assert svg.content[0].text.startswith("Figure id 2: 'Bars' (SVG, ")
    assert both.is_error and missing.is_error and "Cannot read" in missing.content[0].text
    assert not_image.is_error and "not a PNG" in not_image.content[0].text
    [png] = (tmp_path / "out" / "figures").glob("heat-map-*-1.png")
    assert png.read_bytes() == PNG_1X1 and len(list((tmp_path / "out" / "figures").glob("bars-*-2.svg"))) == 1
    assert [f["title"] for f in log["figures"]] == ["Heat map", "Bars"] and log["calls"] == []
    markdown = md.content[0].text
    assert f"![Figure 1: Heat map](figures/{png.name})\n\n**Figure 1: Heat map.** Clustered pKi." in markdown
    assert "**Figure 2: Bars.**" in markdown and "- **Contents:** 1 exchange · 2 figures" in markdown
    page = next((tmp_path / "out").glob("*.html")).read_text()
    assert f"data:image/png;base64,{base64.b64encode(PNG_1X1).decode()}" in page
    assert "data:image/svg+xml;base64," in page and f"figures/{png.name}" not in page


async def test_figures_numbered_in_transcript_order(tmp_path):
    plot = tmp_path / "plot.png"
    plot.write_bytes(PNG_1X1)
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    async with Client(srv) as client:
        for title in ["Old", "Older"]:
            await client.call_tool("add_figure", {"title": title, "path": str(plot)})
        await client.call_tool("reset_tool_log", {})
        for title in ["A", "B", "C"]:  # ids 3, 4, 5
            await client.call_tool("add_figure", {"title": title, "path": str(plot)})
        md = await client.call_tool("create_transcript", {"model": "m", "exchanges": [
            {"prompt": "1", "figures": [5]}, {"prompt": "2", "figures": [3, 5]}]})
        unplaced = await client.call_tool("create_transcript", {"model": "m", "exchanges": [{"prompt": "1"}]})
        record = await client.call_tool("create_transcript", {"model": "m", "format": "json", "exchanges": [
            {"prompt": "1", "figures": [4]}]})
    markdown = md.content[0].text
    assert "![Figure 1: C]" in markdown and "![Figure 2: A]" in markdown and "**Figure 2: A.**" in markdown
    assert "Figure 3" not in markdown and "- **Contents:** 2 exchanges · 2 figures" in markdown
    assert [line[:13] for line in unplaced.content[0].text.splitlines() if line.startswith("![")] == [
        "![Figure 1: A", "![Figure 2: B", "![Figure 3: C"]
    assert [(f["number"], f["id"]) for f in json.loads(record.content[0].text)["figures"]] == [(1, 4)]


async def test_transcripts_written_to_output_dir(tmp_path):
    plot, svg = tmp_path / "plot.png", tmp_path / "bars.svg"
    plot.write_bytes(PNG_1X1)
    svg.write_text(SVG)
    results = tmp_path / "my results"
    (results / "figures").mkdir(parents=True)
    (results / "report.md").write_text("old")
    (results / "figures" / "mine.png").write_bytes(PNG_1X1)  # not the server's: kept
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path / "server")
    report = {"model": "m", "output_dir": str(results), "file_name": "report.md"}
    async with Client(srv) as client:
        for path in [plot, svg, plot]:
            await client.call_tool("add_figure", {"title": "Plot", "path": str(path)})
        await client.call_tool("create_transcript", {**report, "exchanges": [
            {"prompt": "1", "figures": [1]}, {"prompt": "2", "figures": [2]}]})
        first = sorted(p.name for p in (results / "figures").iterdir())
        md = await client.call_tool("create_transcript", {**report, "exchanges": [  # regenerated with figure 3
            {"prompt": "1", "answer": "Here.", "figures": [3]}]})
        page = await client.call_tool("create_transcript", {"model": "m", "format": "html", "title": "My plot",
                                                            "output_dir": str(results), "exchanges": [
                                                                {"prompt": "1", "figures": [3]}]})
        relative = await client.call_tool("create_transcript", {"model": "m", "output_dir": "results"})
    markdown, note = md.content
    async with Client(build_server(Database(DB_PATH), transcript_dir=tmp_path / "other")) as client:
        await client.call_tool("transcript_to_html", {"markdown": markdown.text, "output_dir": str(results),
                                                      "file_name": "report"})
    assert first == ["mine.png", "report-figure-1.png", "report-figure-2.svg"]
    assert sorted(p.name for p in (results / "figures").iterdir()) == ["mine.png", "report-figure-1.png"]
    assert (results / "report.md").read_text() == markdown.text
    assert "![Figure 1: Plot](figures/report-figure-1.png)" in markdown.text
    assert "report.md (replaced an existing file), with its 1 figure in" in note.text
    assert (results / "my-plot.html").is_file() and f"{results / 'my-plot.html'} (on the" in page.content[0].text
    assert "data:image/png;base64," in (results / "report.html").read_text()  # found in results/figures
    assert relative.is_error and "absolute path" in relative.content[0].text
    assert not list((tmp_path / "server").glob("*.md")) and not list((tmp_path / "server").glob("*.html"))


async def test_html_table_structures_share_a_frame(tmp_path):
    srv = build_server(Database(DB_PATH), transcript_dir=tmp_path)
    answer = f"| drug | SMILES |\n|---|---|\n| a | {SORAFENIB} |\n| b | {BOSUTINIB} |\n| c | {CLOZAPINE} |"
    async with Client(srv) as client:
        await client.call_tool("create_transcript", {"model": "m", "format": "html", "exchanges": [
            {"prompt": "?", "answer": answer}]})
    page = next(tmp_path.glob("*.html")).read_text()
    svgs = [base64.b64decode(b).decode() for b in re.findall(r'class="structure"[^>]*base64,([^"]+)', page)]
    sizes = {re.search(r"width='(\d+)px' height='(\d+)px'", svg).groups() for svg in svgs}
    assert len(svgs) == 3 and len(sizes) == 1  # aligned on their common core: one frame, one scale


@pytest.mark.network
def test_pubchem_lookup_live():
    found = names.pubchem_lookup("Ibrance")
    assert found.inchi_key == "AHJRHEGDXFFMBM-UHFFFAOYSA-N" and found.cid == 5330286
    assert names.pubchem_lookup("not a compound xyzzy") is None
