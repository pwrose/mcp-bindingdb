from pathlib import Path
import duckdb
import pytest
from rdkit import Chem
from mcp import Client
from mcp.client import advertise
from mcp.server.apps import APP_MIME_TYPE, EXTENSION_ID
from mcp.server.mcpserver import MCPServer

from mcp_bindingdb import structure_editor as module


@pytest.fixture
def anyio_backend():
    return "asyncio"


class DB:
    def __init__(self):
        self.con = duckdb.connect()
        self.con.execute(
            "CREATE TABLE compound(monomerid INT,bdbm_id VARCHAR,name VARCHAR,smiles VARCHAR,inchi_key VARCHAR,n_activities INT)"
        )
        for i, s in enumerate(
            [
                "N[C@@H](C)C(=O)O",
                "N[C@H](C)C(=O)O",
                "NC(C)C(=O)O",
                "CC(=O)[O-].[Na+]",
                "CC(=O)O",
                "CCO",
            ]
        ):
            self.con.execute(
                "INSERT INTO compound VALUES(?,?,?,?,?,?)",
                [
                    i,
                    "BDBM" + str(i),
                    "test " + str(i),
                    s,
                    Chem.MolToInchiKey(Chem.MolFromSmiles(s)),
                    10,
                ],
            )
        self.con.execute(
            "CREATE TABLE activity(ki_result_id INT,monomerid INT,affinity_type VARCHAR,relation VARCHAR,value DOUBLE,unit VARCHAR)"
        )
        self.con.executemany(
            "INSERT INTO activity VALUES(?,?,?,?,?,?)",
            [
                (0, 0, "Ki", "=", 5, "nM"),
                (1, 0, "IC50", "=", 1500, "nM"),
                (2, 1, "Ki", "=", 1000, "nM"),
                (3, 2, "Kd", "=", 0.5, "nM"),
                (4, 3, "IC50", "=", 50, "nM"),
                (5, 4, "Ki", ">", 5, "nM"),
                (6, 5, "EC50", "<", 100, "nM"),
                (7, 5, "Ki", "=", 5000, "nM"),
                (8, 4, "Kd", "=", None, "nM"),
                (9, 4, "IC50", "=", -5, "nM"),
                (10, 4, "EC50", "=", 0.01, "uM"),
                (11, 4, "Ki", "=", float("nan"), "nM"),
            ],
        )

    timeout_s = 30
    path = Path("fixture.duckdb")

    def build_info(self):
        return {"release": "fixture"}

    def rows(self, sql, params=None, limit=100):
        cursor = self.con.execute(sql, params or [])
        cols = [r[0] for r in cursor.description]
        return [dict(zip(cols, r)) for r in cursor.fetchmany(limit)]


@pytest.mark.anyio
async def test_mcp_apps_discovery_resource_and_initial_input():
    server = MCPServer("BindingDB test", extensions=[module.create_editor_extension()])
    async with Client(
        server, extensions=[advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})]
    ) as client:
        tools = (await client.list_tools()).tools
        tool = next(t for t in tools if t.name == "open_structure_editor")
        assert tool.meta["ui"]["resourceUri"] == module.URI
        result = await client.call_tool(
            "open_structure_editor", {"initial_query": "CCO", "input_type": "smiles"}
        )
        assert not result.is_error
        assert result.structured_content["initial_query"] == "CCO"
        assert result.structured_content["executed"] is False
        resources = await client.read_resource(module.URI)
        resource = resources.contents[0]
        assert resource.mime_type == APP_MIME_TYPE
        assert "BindingDB Structure Studio" in resource.text
        assert "DecompressionStream" in resource.text


@pytest.mark.anyio
async def test_exact_is_stereo_and_salt_sensitive_and_rejects_queries():
    server = MCPServer("Exact test")
    module.register_exact_structure_search(server, DB())
    async with Client(server) as client:
        for smiles, expected in [
            ("N[C@@H](C)C(=O)O", 0),
            ("N[C@H](C)C(=O)O", 1),
            ("NC(C)C(=O)O", 2),
            ("CC(=O)[O-].[Na+]", 3),
            ("CC(=O)O", 4),
        ]:
            r = await client.call_tool("exact_structure_search", {"smiles": smiles})
            assert not r.is_error, r.content
            assert [row["monomerid"] for row in r.structured_content["rows"]] == [
                expected
            ]
        for value in ["*CC", "[NX3][CX3](=[OX1])", "C1CCC", ""]:
            r = await client.call_tool("exact_structure_search", {"smiles": value})
            assert r.is_error


@pytest.mark.anyio
async def test_affinity_exact_range_types_and_censored_measurements():
    db = DB()
    server = MCPServer("Filtered exact test")
    module.register_filtered_structure_search(server, db)
    async with Client(server) as client:

        async def search(query, **args):
            r = await client.call_tool(
                "filtered_structure_search", {"query": query, **args}
            )
            assert not r.is_error, r.content
            return r.structured_content

        r = await search(
            "N[C@@H](C)C(=O)O", affinity_type="Ki", min_value_nm=5, max_value_nm=5
        )
        assert [row["monomerid"] for row in r["rows"]] == [0]
        assert r["rows"][0]["affinity_value_nm"] == 5
        assert (await search("N[C@@H](C)C(=O)O", min_value_nm=10))["rows"] == []
        assert (await search("N[C@@H](C)C(=O)O", affinity_type="IC50"))["rows"] == []
        assert (await search("N[C@H](C)C(=O)O"))["rows"][0]["affinity_value_nm"] == 1000
        assert (await search("CCO"))["rows"][0]["affinity_relation"] == "<"
        assert (await search("CCO", min_value_nm=1))["rows"] == []
        assert (await search("CCO", affinity_type="Ki"))["rows"] == []
        assert (await search("CC(=O)O"))[
            "rows"
        ] == []  # >, missing, negative, wrong-unit and NaN excluded
        for args in [
            {"min_value_nm": -1},
            {"min_value_nm": 1001},
            {"affinity_type": "kon"},
            {"max_value_nm": None},
            {"mode": "similarity"},
            {"mode": "exact", "query_type": "smarts"},
        ]:
            r = await client.call_tool(
                "filtered_structure_search", {"query": "CCO", **args}
            )
            assert r.is_error


def fixture_index(db, path):
    """Build the actual BindingDB index format over the tiny fixture, without a data download."""
    import numpy as np
    from rdkit import DataStructs
    from mcp_bindingdb import substructure

    rows = db.rows(
        "SELECT monomerid,smiles FROM compound ORDER BY monomerid", limit=100
    )
    mols = [Chem.MolFromSmiles(r["smiles"]) for r in rows]
    patterns = np.array(
        [
            np.frombuffer(
                DataStructs.BitVectToBinaryText(
                    Chem.PatternFingerprint(m, fpSize=2048)
                ),
                dtype=np.uint8,
            )
            for m in mols
        ]
    )
    morgan = np.array(
        [
            np.frombuffer(substructure.morgan_fingerprint(m), dtype=np.uint8)
            for m in mols
        ]
    )
    substructure.write_index(
        path,
        {"n_compounds": len(rows), "release": "fixture"},
        [r["monomerid"] for r in rows],
        [r["smiles"] for r in rows],
        patterns,
        morgan,
    )
    return substructure.SubstructureIndex(path)


@pytest.mark.anyio
async def test_affinity_precedes_result_limit_and_similarity_preserves_scores(tmp_path):
    db = DB()
    server = MCPServer("Filtered indexed test")
    module.register_filtered_structure_search(
        server, db, fixture_index(db, tmp_path / "fixture.sslib")
    )
    async with Client(server) as client:
        # Compound 0 is the first structural match, but fails Kd. Limiting first would lose compound 2.
        r = await client.call_tool(
            "filtered_structure_search",
            {
                "query": "[NX3]",
                "query_type": "smarts",
                "mode": "substructure",
                "affinity_type": "Kd",
                "limit": 1,
            },
        )
        assert not r.is_error, r.content
        assert [row["monomerid"] for row in r.structured_content["rows"]] == [2]
        assert r.structured_content["rows"][0]["affinity_type"] == "Kd"
        r = await client.call_tool(
            "filtered_structure_search",
            {
                "query": "N[C@@H](C)C(=O)O",
                "mode": "similarity",
                "threshold": 1,
                "affinity_type": "Ki",
                "max_value_nm": 10,
            },
        )
        assert not r.is_error, r.content
        assert [row["monomerid"] for row in r.structured_content["rows"]] == [0]
        assert r.structured_content["rows"][0]["similarity"] == 1
        r = await client.call_tool(
            "filtered_structure_search",
            {
                "query": "[NX3]",
                "query_type": "smarts",
                "mode": "substructure",
                "limit": 1,
            },
        )
        assert not r.is_error, r.content
        assert (
            r.structured_content["truncated"]
            and not r.structured_content["search_complete"]
        )
        assert r.structured_content["n_matches"] is None


@pytest.mark.anyio
async def test_editor_is_registered_in_real_server_and_uses_tool_log(tmp_path):
    from mcp_bindingdb.server import build_server

    db = DB()
    server = build_server(
        db,
        fixture_index(db, tmp_path / "fixture.sslib"),
        network=False,
        transcript_dir=tmp_path / "transcripts",
    )
    async with Client(
        server, extensions=[advertise(EXTENSION_ID, {"mimeTypes": [APP_MIME_TYPE]})]
    ) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
        assert {
            "open_structure_editor",
            "exact_structure_search",
            "filtered_structure_search",
        } <= tools.keys()
        assert (
            tools["filtered_structure_search"].input_schema["properties"]["threshold"][
                "default"
            ]
            == 0.85
        )
        result = await client.call_tool(
            "open_structure_editor", {"initial_query": "CCO", "mode": "similarity"}
        )
        assert not result.is_error and result.structured_content["mode"] == "similarity"
        resource = (await client.read_resource(module.URI)).contents[0]
        assert resource.mime_type == APP_MIME_TYPE
        assert "bindingdb-editor-integration.zip" not in resource.text
        result = await client.call_tool(
            "filtered_structure_search",
            {
                "query": "[NX3]",
                "query_type": "smarts",
                "mode": "substructure",
                "affinity_type": "Kd",
                "limit": 1,
            },
        )
        assert not result.is_error, result.content
        assert [r["monomerid"] for r in result.structured_content["rows"]] == [2]
        log = await client.call_tool("get_tool_log", {})
        assert any(
            c["call"].startswith("filtered_structure_search(")
            for c in log.structured_content["calls"]
        )
        blocked = await client.call_tool("editor_pubchem_candidates", {"cids": [2244]})
        assert blocked.is_error and "disabled" in blocked.content[0].text.lower()
