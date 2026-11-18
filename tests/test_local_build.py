"""The Docker-free build: the MySQL-dump reader, and the server while the database is still being built."""

import json
import time

import duckdb
import pytest
from mcp import Client

from mcp_bindingdb import local_build
from mcp_bindingdb.builder import mysqldump, pipeline
from mcp_bindingdb.db import Database
from mcp_bindingdb.server import build_server

pytestmark = pytest.mark.anyio

DUMP = r"""-- MySQL dump 10.13
/*!40101 SET NAMES utf8mb4 */;
DROP TABLE IF EXISTS `thing`;
CREATE TABLE `thing` (
  `id` int NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `score` decimal(10,4) DEFAULT NULL,
  `flag` tinyint DEFAULT NULL,
  `big` bigint unsigned DEFAULT NULL,
  `added` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  CONSTRAINT `thing_ibfk_1` FOREIGN KEY (`id`) REFERENCES `other` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
LOCK TABLES `thing` WRITE;
INSERT INTO `thing` VALUES (1,'it\'s',1.5000,1,18446744073709551615,'2024-01-02 03:04:05'),(2,'f(x),(y)',NULL,0,NULL,NULL);
INSERT INTO `thing` VALUES (3,'NULL',-0.0001,NULL,0,NULL),(4,'',2.0000,NULL,NULL,NULL),(5,'back\\slash \"q\" line\nbreak',NULL,NULL,NULL,NULL);
UNLOCK TABLES;
CREATE TABLE `person` (
  `id` int NOT NULL,
  `email` varchar(100) DEFAULT NULL
) ENGINE=InnoDB;
INSERT INTO `person` VALUES (1,'someone@example.org');
CREATE TABLE `empty` (
  `id` int NOT NULL
) ENGINE=InnoDB;
"""


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_dump_reader_keeps_values_exactly(tmp_path):
    dump = tmp_path / "x.dmp"
    dump.write_text(DUMP)
    con = duckdb.connect()
    seen = []
    counts = mysqldump.load(dump, con, lambda done, total, table: seen.append((done <= total, table)))
    assert counts == {"thing": 5, "empty": 0}  # person (PII) is skipped
    assert seen and all(ok for ok, _ in seen) and {t for _, t in seen} == {"thing"}
    types = dict(con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE table_name = 'thing'")
                 .fetchall())
    assert types == {"id": "INTEGER", "name": "VARCHAR", "score": "DECIMAL(10,4)", "flag": "TINYINT",
                     "big": "UBIGINT", "added": "TIMESTAMP"}
    rows = con.execute("SELECT id, name, score::VARCHAR, flag, big, added::VARCHAR FROM thing ORDER BY id").fetchall()
    assert rows == [
        (1, "it's", "1.5000", 1, 18446744073709551615, "2024-01-02 03:04:05"),
        (2, "f(x),(y)", None, 0, None, None),
        (3, "NULL", "-0.0001", None, 0, None),  # the string 'NULL' is not NULL
        (4, "", "2.0000", None, None, None),
        (5, 'back\\slash "q" line\nbreak', None, None, None, None),
    ]


def test_dump_reader_reads_the_zip(tmp_path):
    import zipfile

    with zipfile.ZipFile(tmp_path / "x_dmp.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("BDB-mySQL_All_209901.dmp", DUMP)
    con = duckdb.connect()
    assert mysqldump.load(tmp_path / "x_dmp.zip", con)["thing"] == 5


def _status(folder, **fields):
    data = {"release": "202610", "state": "running", "started_at": time.time() - 600, "done_steps": [],
            "step": None, "done": 0, "total": 0, **fields}
    folder.mkdir(parents=True, exist_ok=True)
    pipeline.status_path(folder, "202610").write_text(json.dumps(data))


def test_progress_message(tmp_path):
    folder = tmp_path / "data"
    build = local_build.LocalBuild(folder, "202610")
    _status(folder, step="properties", done=500, total=1000,
            done_steps=["download", "load", "derived", "inchikeys"])
    with pipeline.lock(pipeline.lock_path(folder, "202610")):  # as if a builder were running
        message = build.message()
    assert "being built on this computer for first use" in message
    assert "step 5 of 6, computing compound properties and structural alerts (50%)" in message
    assert "left in all" in message and message.endswith("the BindingDB tools work once it is done.")

    _status(folder, state="failed", error="ConnectionError: offline", step="download")
    message = build.message()
    assert "could not be built: ConnectionError: offline" in message and "starts again" in message


async def test_tools_say_the_database_is_being_built(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    monkeypatch.setenv("MCP_BINDINGDB_DATA_DIR", str(folder))
    monkeypatch.delenv("BINDINGDB_DUCKDB", raising=False)
    monkeypatch.setattr(local_build, "find_database", lambda: (_ for _ in ()).throw(FileNotFoundError()))
    _status(folder, step="inchikeys", done=10, total=100, done_steps=["download", "load", "derived"])
    started = []
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: started.append(self.release))

    path, pending = local_build.locate()
    assert path == folder / "bindingdb_202610.duckdb" and pending is not None
    db = Database(path, ready=lambda: pending.require(path), build_info=pending.build_info)
    info = db.build_info()
    mcp = build_server(db, transcript_dir=tmp_path / "transcripts")  # does not open the database
    async with Client(mcp) as client:
        result = await client.call_tool("run_sql", {"sql": "SELECT 42 AS n"})
        assert result.is_error
        assert "step 4 of 6, computing standard InChIKeys (10%)" in result.content[0].text
        assert started  # a call (re)starts a build that is not running

        con = duckdb.connect(str(path))  # the build finishes
        con.execute("CREATE TABLE _build_info AS SELECT * FROM (VALUES ('release', '202610'), "
                    "('source_zip_sha256', 'abc')) t(key, value)")
        con.close()
        result = await client.call_tool("run_sql", {"sql": "SELECT 42 AS n"})
        assert result.structured_content["rows"] == [{"n": 42}]
    assert info["source_zip_sha256"] == "abc"  # the dict the server holds now has the file's own build info


def test_locate_prefers_a_local_database(tmp_path, monkeypatch):
    local = tmp_path / "bindingdb_202610.duckdb"
    monkeypatch.delenv("BINDINGDB_DUCKDB", raising=False)
    monkeypatch.setattr(local_build, "find_database", lambda: local)
    assert local_build.locate() == (local, None)
    assert local_build.locate("~/x.duckdb")[0].name == "x.duckdb"


async def test_structure_search_says_the_index_is_being_built(tmp_path):
    from mcp_bindingdb import substructure
    from mcp_bindingdb.server import PendingIndex

    if not substructure.rdkit_available():
        pytest.skip("needs RDKit")
    path = tmp_path / "bindingdb_202610.duckdb"
    duckdb.connect(str(path)).close()

    def ready():
        raise local_build.NotReady("The structure-search index is being built (step 6 of 6)")

    mcp = build_server(Database(path, build_info={"release": "202610"}),
                       PendingIndex(path.with_suffix(".sslib"), ready, "202610"), transcript_dir=tmp_path / "t")
    async with Client(mcp) as client:
        result = await client.call_tool("substructure_search", {"query": "c1ccccc1", "count_only": True})
    assert result.is_error and "index is being built (step 6 of 6)" in result.content[0].text
