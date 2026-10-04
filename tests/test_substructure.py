"""Substructure search: query parsing (needs RDKit) and the tool (also needs the built index)."""

import pytest
from mcp import Client

from mcp_bindingdb import substructure

if not substructure.rdkit_available():
    pytest.skip("RDKit not installed (substructure extra)", allow_module_level=True)

from mcp_bindingdb.db import Database, find_database  # noqa: E402
from mcp_bindingdb.server import build_server, load_substructure_index  # noqa: E402

IMATINIB = 13530
IMATINIB_SMILES = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"
EGFR = 520
QUINAZOLINE = "c1ncnc2ccccc12"


@pytest.mark.parametrize("query, kind", [
    ("c1ccccc1", "smiles"),
    ("C1=CC=CC=C1", "smiles"),  # Kekulé input is aromatized
    ("c1ccc2[nH]ccc2c1", "smiles"),
    ("[NX3;H2]c1ccccc1", "smarts"),  # not valid SMILES
    ("*c1ccccc1", "smarts"),  # '*' matches nothing in a SMILES query
    ("c1ccc2c(c1)nc1c2ccc2c3ccccc3nc21", "smarts"),  # aromatic as written, not as a molecule
    ("s1cncc1-c1ccnc([#7])n1", "smarts"),  # [#7] is valid SMILES but a radical N
])
def test_parse_query_auto(query, kind):
    assert substructure.parse_query(query)[1] == kind


def test_parse_query_errors():
    for query, query_type in [("", "auto"), ("C1CC", "auto"), ("[NX3;H2]c1ccccc1", "smiles")]:
        with pytest.raises(substructure.QueryParseError):
            substructure.parse_query(query, query_type)


try:
    DB = Database(find_database())
    INDEX = load_substructure_index(DB)
except FileNotFoundError:
    INDEX = None
needs_index = pytest.mark.skipif(INDEX is None, reason="database or substructure index not built")


@pytest.fixture(scope="module")
def server():
    return build_server(DB, INDEX)


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def ok(server, **args):
    async with Client(server) as client:
        result = await client.call_tool("substructure_search", args)
    assert not result.is_error, result.content
    return result.structured_content


@needs_index
@pytest.mark.anyio
async def test_whole_compound_finds_itself_first(server):
    out = await ok(server, query=IMATINIB_SMILES, limit=10)
    assert out["query"]["interpreted_as"] == "smiles"
    assert out["rows"][0]["monomerid"] == IMATINIB  # most-measured match first
    assert out["truncated"]


@needs_index
@pytest.mark.anyio
async def test_count_only(server):
    out = await ok(server, query=QUINAZOLINE, count_only=True)
    assert out["n_matching_compounds"] > 10_000
    assert out["compounds_searched"] == out["compounds_indexed"] == INDEX.n_compounds


@needs_index
@pytest.mark.anyio
async def test_target_filter_returns_potent_matches_only(server):
    out = await ok(server, query=QUINAZOLINE, target_id=EGFR, max_value_nm=10, limit=500)
    rows = out["rows"]
    assert rows and out["n_matching_compounds"] >= len(rows)
    assert out["compounds_searched"] == out["search_set_size"]  # complete
    assert all(r["polymerid"] == EGFR and r["value"] <= 10 and r["relation"] != ">" for r in rows)
    ps = [r["p_affinity"] for r in rows]
    assert ps == sorted(ps, reverse=True)
    assert len({r["monomerid"] for r in rows}) == len(rows)
    for r in rows[:20]:  # every row really contains the quinazoline
        smiles = DB.one("SELECT smiles FROM compound WHERE monomerid = ?", [r["monomerid"]])["smiles"]
        mol = substructure.Chem.MolFromSmiles(smiles)
        assert mol.HasSubstructMatch(substructure.parse_query(QUINAZOLINE)[0])


@needs_index
@pytest.mark.anyio
async def test_no_matches_and_bad_query(server):
    out = await ok(server, query="[Xe]", target_id=EGFR)
    assert out["rows"] == [] and out["n_matching_compounds"] == 0
    async with Client(server) as client:
        result = await client.call_tool("substructure_search", {"query": "C1CC("})
    assert result.is_error and "Not valid" in result.content[0].text


@needs_index
@pytest.mark.anyio
async def test_summarize_by_target(server):
    out = await ok(server, query=QUINAZOLINE, summarize_by_target=True, max_value_nm=1000, limit=500)
    rows = out["rows"]
    assert out["n_matching_compounds"] > 10_000 and out["n_targets"] >= len(rows)
    egfr = next(r for r in rows if r["target_kind"] == "polymer" and r["target_id"] == EGFR)
    expected = DB.one(
        """SELECT count(DISTINCT a.monomerid) AS n FROM activity a JOIN compound c USING (monomerid)
           WHERE a.polymerid = ? AND a.affinity_type IN ('Ki', 'Kd', 'IC50', 'EC50') AND a.unit = 'nM'
             AND a.relation <> '>' AND a.value <= 1000 AND a.monomerid IN (SELECT unnest(?))""",
        [EGFR, INDEX.search(substructure.parse_query(QUINAZOLINE)[0], INDEX.n_compounds, 25).monomerids])
    assert egfr["n_compounds"] == expected["n"]
    ns = [r["n_compounds"] for r in rows]
    assert ns == sorted(ns, reverse=True)
