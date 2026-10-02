"""End-to-end tests against the real DuckDB build, through an in-process MCP client."""

import pytest
from mcp import Client

from mcp_bindingdb.db import Database, find_database
from mcp_bindingdb.server import build_server

try:
    DB_PATH = find_database()
except FileNotFoundError:
    pytest.skip("BindingDB DuckDB file not built", allow_module_level=True)

IMATINIB = 13530  # BDBM13530
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
        "find_targets_for_compound", "get_activity", "describe_tables", "run_sql",
    }
    assert all(t.annotations.read_only_hint for t in tools.values())


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
