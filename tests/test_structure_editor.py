import math
import subprocess
import sys
from pathlib import Path

import duckdb
import pytest
from mcp import Client
from mcp.client import advertise
from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID
from mcp.server.mcpserver import MCPServer

from mcp_bindingdb import structure_editor as module

Chem = pytest.importorskip("rdkit.Chem")

SMILES = [
    "N[C@@H](C)C(=O)O",
    "N[C@H](C)C(=O)O",
    "NC(C)C(=O)O",
    "CC(=O)[O-].[Na+]",
    "CC(=O)O",  # stored without an InChIKey, as ~30% of BindingDB compounds are
    "CCO",
]
# (ki_result_id, monomerid, affinity_type, relation, value, unit)
MEASUREMENTS = [
    (0, 0, "Ki", "=", 5, "nM"),
    (1, 0, "IC50", "=", 1500, "nM"),
    (2, 1, "Ki", "=", 1000, "nM"),
    (3, 2, "Kd", "=", 0.5, "nM"),
    (4, 3, "IC50", "=", 50, "nM"),
    (5, 4, "Ki", ">", 5, "nM"),
    (6, 5, "EC50", "<", 100, "nM"),
    (7, 5, "Ki", "=", 5000, "nM"),
    (8, 4, "Kd", "=", None, "nM"),
    (9, 4, "EC50", "=", 0.01, "uM"),
]


@pytest.fixture
def anyio_backend():
    return "asyncio"


def fixture_database(path, compute_keys=True):
    """A tiny DuckDB file with the compound and activity columns the structure tools use; compute_keys runs
    scripts/compute_inchikeys.py on it, as the database build does."""
    from mcp_bindingdb.db import Database

    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE _build_info AS SELECT 'release' AS key, 'fixture' AS value")
    con.execute("""CREATE TABLE compound(monomerid INT, bdbm_id VARCHAR, name VARCHAR, smiles VARCHAR,
                   inchi_key VARCHAR, mol_weight DOUBLE, n_activities INT, n_targets INT)""")
    for i, s in enumerate(SMILES):
        key = None if s == "CC(=O)O" else Chem.MolToInchiKey(Chem.MolFromSmiles(s))
        con.execute("INSERT INTO compound VALUES (?, ?, ?, ?, ?, 0, 10, 1)", [i, f"BDBM{i}", f"test {i}", s, key])
    con.execute("""CREATE TABLE activity(ki_result_id INT, affinity_type VARCHAR, relation VARCHAR, value DOUBLE,
                   unit VARCHAR, p_affinity DOUBLE, monomerid INT, compound_name VARCHAR, inchi_key VARCHAR, polymerid INT,
                   complexid INT, target_name VARCHAR, uniprot_raw VARCHAR, organism VARCHAR, ph DOUBLE,
                   temp_k DOUBLE, assay_name VARCHAR, source_id VARCHAR, doi VARCHAR, year INT)""")
    for rid, mid, kind, rel, value, unit in MEASUREMENTS:
        p = 9 - math.log10(value) if value and unit == "nM" else None
        con.execute("INSERT INTO activity (ki_result_id, affinity_type, relation, value, unit, p_affinity, "
                    "monomerid, compound_name, polymerid) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)",
                    [rid, kind, rel, value, unit, p, mid, f"test {mid}"])
    con.close()
    if compute_keys:
        script = Path(__file__).parents[1] / "scripts" / "compute_inchikeys.py"
        subprocess.run([sys.executable, str(script), "--workers", "1", str(path)], check=True, capture_output=True)
    return Database(path)


def fixture_index(db, path):
    """Build the actual BindingDB index format over the tiny fixture, without a data download."""
    import numpy as np
    from rdkit import DataStructs

    from mcp_bindingdb import substructure

    rows = db.rows("SELECT monomerid, smiles FROM compound ORDER BY monomerid")
    mols = [Chem.MolFromSmiles(r["smiles"]) for r in rows]
    patterns = np.array([np.frombuffer(DataStructs.BitVectToBinaryText(Chem.PatternFingerprint(m, fpSize=2048)),
                                       dtype=np.uint8) for m in mols])
    morgan = np.array([np.frombuffer(substructure.morgan_fingerprint(m), dtype=np.uint8) for m in mols])
    substructure.write_index(path, {"n_compounds": len(rows), "release": "fixture"},
                             [r["monomerid"] for r in rows], [r["smiles"] for r in rows], patterns, morgan)
    return substructure.SubstructureIndex(path)


@pytest.fixture
def server(tmp_path):
    from mcp_bindingdb.server import build_server

    db = fixture_database(tmp_path / "fixture.duckdb")
    return build_server(db, fixture_index(db, tmp_path / "fixture.sslib"), network=False,
                        transcript_dir=tmp_path / "transcripts")


async def call(server, tool, **args):
    async with Client(server) as client:
        result = await client.call_tool(tool, args)
    assert not result.is_error, result.content
    return result.structured_content


async def ids(server, tool, **args):
    return [row["monomerid"] for row in (await call(server, tool, **args))["rows"]]


@pytest.mark.anyio
async def test_mcp_apps_discovery_resource_and_initial_input():
    server = MCPServer("BindingDB test", extensions=[module.create_editor_extension()])
    async with Client(server, extensions=[advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})]) as client:
        tools = (await client.list_tools()).tools
        tool = next(t for t in tools if t.name == "open_structure_editor")
        assert tool.meta["ui"]["resourceUri"] == module.URI
        result = await client.call_tool("open_structure_editor", {"initial_query": "CCO", "input_type": "smiles"})
        assert not result.is_error
        assert result.structured_content["initial_query"] == "CCO"
        assert result.structured_content["executed"] is False
        resource = (await client.read_resource(module.URI)).contents[0]
        assert resource.mime_type == APP_MIME_TYPE
        assert "BindingDB Structure Studio" in resource.text
        assert "DecompressionStream" in resource.text


@pytest.mark.anyio
async def test_exact_is_stereo_and_salt_sensitive(server):
    for expected, smiles in enumerate(SMILES):
        result = await call(server, "exact_structure_search", smiles=smiles)
        assert [r["monomerid"] for r in result["rows"]] == [expected] and result["n_exact_matches"] == 1
        assert "note" not in result
    async with Client(server) as client:
        for value in ["*CC", "C1CCC", ""]:
            assert (await client.call_tool("exact_structure_search", {"smiles": value})).is_error


@pytest.mark.anyio
async def test_exact_needs_computed_inchikeys_but_not_the_index(tmp_path):
    from mcp_bindingdb.server import build_server

    # Without computed keys, the compound stored without one cannot be found, and the result says why.
    server = build_server(fixture_database(tmp_path / "raw.duckdb", compute_keys=False), None, network=False)
    result = await call(server, "exact_structure_search", smiles="CC(=O)O")
    assert result["rows"] == [] and "compute_inchikeys" in result["note"]
    server = build_server(fixture_database(tmp_path / "computed.duckdb"), None, network=False)
    assert await ids(server, "exact_structure_search", smiles="CC(=O)O") == [4]


@pytest.mark.anyio
async def test_affinity_range_types_and_censored_measurements(server):
    async def exact(smiles, **filters):
        return (await call(server, "exact_structure_search", smiles=smiles, **filters))["rows"]

    rows = await exact(SMILES[0], affinity_types=["Ki"], min_value_nm=5, max_value_nm=5)  # inclusive
    assert [(r["monomerid"], r["value"]) for r in rows] == [(0, 5)]
    assert await exact(SMILES[0], min_value_nm=10, max_value_nm=1000) == []  # Ki 5 below, IC50 1500 above
    assert await exact(SMILES[0], affinity_types=["IC50"], max_value_nm=1000) == []
    assert (await exact(SMILES[1], max_value_nm=1000))[0]["value"] == 1000
    assert (await exact("CCO", max_value_nm=1000))[0]["relation"] == "<"  # < 100 lies in 0-1000
    assert await exact("CCO", min_value_nm=1, max_value_nm=1000) == []  # but maybe not in 1-1000
    assert await exact("CCO", affinity_types=["Ki"], max_value_nm=1000) == []
    assert await exact("CC(=O)O", max_value_nm=1000) == []  # '>', missing and non-nM values never qualify
    async with Client(server) as client:
        for args in [{"min_value_nm": 100, "max_value_nm": 10}, {"min_value_nm": -1}, {"affinity_types": ["pIC50"]}]:
            for tool, query in [("exact_structure_search", {"smiles": "CCO"}), ("similarity_search", {"smiles": "CCO"}),
                                ("substructure_search", {"query": "CCO"})]:
                assert (await client.call_tool(tool, {**query, **args})).is_error


@pytest.mark.anyio
async def test_affinity_filters_apply_before_the_result_limit(server):
    # Compound 0 is the first structural match but has no Kd; limiting first would lose compound 2.
    rows = (await call(server, "substructure_search", query="[NX3]", query_type="smarts",
                       affinity_types=["Kd"], limit=1))["rows"]
    assert [(r["monomerid"], r["affinity_type"]) for r in rows] == [(2, "Kd")]
    assert (await call(server, "substructure_search", query="[NX3]", query_type="smarts", limit=1))["truncated"]
    # Compounds 0-2 share a fingerprint (chirality is ignored); only 0 has a Ki <= 10 nM.
    rows = (await call(server, "similarity_search", smiles=SMILES[0], threshold=1, affinity_types=["Ki"],
                       max_value_nm=10))["rows"]
    assert [(r["monomerid"], r["similarity"]) for r in rows] == [(0, 1)]


@pytest.mark.anyio
async def test_editor_is_registered_in_real_server_and_uses_tool_log(server):
    async with Client(server, extensions=[advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})]) as client:
        tools = {t.name for t in (await client.list_tools()).tools}
        assert {"open_structure_editor", "exact_structure_search"} <= tools
        assert "filtered_structure_search" not in tools
        result = await client.call_tool("open_structure_editor", {"initial_query": "CCO", "mode": "similarity"})
        assert not result.is_error and result.structured_content["mode"] == "similarity"
        resource = (await client.read_resource(module.URI)).contents[0]
        assert resource.mime_type == APP_MIME_TYPE
        assert "bindingdb-editor-integration.zip" not in resource.text
        result = await client.call_tool("exact_structure_search", {"smiles": "CCO", "max_value_nm": 1000})
        assert not result.is_error, result.content
        log = await client.call_tool("get_tool_log", {})
        assert any(c["call"].startswith("exact_structure_search(") for c in log.structured_content["calls"])
        blocked = await client.call_tool("editor_pubchem_candidates", {"cids": [2244]})
        assert blocked.is_error and "disabled" in blocked.content[0].text.lower()
