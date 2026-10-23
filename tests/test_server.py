"""End-to-end tests against the real DuckDB build, through an in-process MCP client."""

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
        "create_transcript", "transcript_to_html", "reset_tool_log", "get_tool_log",
    }
    writes = {"reset_tool_log", "transcript_to_html", "create_transcript"}  # the last two write HTML files
    assert all(t.annotations.read_only_hint for name, t in tools.items() if name not in writes)


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
        assert (await client.call_tool("reset_tool_log", {})).structured_content == {"cleared": 2}
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


@pytest.mark.network
def test_pubchem_lookup_live():
    found = names.pubchem_lookup("Ibrance")
    assert found.inchi_key == "AHJRHEGDXFFMBM-UHFFFAOYSA-N" and found.cid == 5330286
    assert names.pubchem_lookup("not a compound xyzzy") is None
