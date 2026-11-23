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
        status = await client.call_tool("update_database", {})  # "Build status?" before the database is there
        assert not status.is_error and status.structured_content["building_release"] == "202610"
        assert "step 4 of 6, computing standard InChIKeys" in status.structured_content["message"]

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


def test_transcripts_of_a_first_use_build_go_to_documents(tmp_path, monkeypatch):
    from pathlib import Path

    from mcp_bindingdb.server import _transcript_dir

    monkeypatch.setenv("MCP_BINDINGDB_DATA_DIR", str(tmp_path / "data"))
    built = tmp_path / "data" / "bindingdb_202610.duckdb"
    built.parent.mkdir()
    documents = Path.home() / "Documents" / "BindingDB"
    assert _transcript_dir(None, built) == documents
    assert _transcript_dir("${user_config.results_dir}", built) == documents  # left unfilled by the host
    assert _transcript_dir("  ", built) == documents
    assert _transcript_dir("~/results", built) == Path.home() / "results"
    assert _transcript_dir(None, tmp_path / "repo" / "data" / "bindingdb_202610.duckdb") is None  # a clone's data/


def _release_files(folder, release, complete=True, db_format=None):
    """Stand-ins for a release's files: database (with its _build_info) and index when complete, else a status file
    and a partial dump. `db_format` None: not recorded, as in databases built before it was."""
    folder.mkdir(parents=True, exist_ok=True)
    names = ([f"bindingdb_{release}.duckdb", f"bindingdb_{release}.sslib", f"build-{release}.json",
              f"build-{release}.log", f".build-{release}.lock"] if complete
             else [f"build-{release}.json", f"BDB-mySQL_All_{release}_dmp.zip.part"])
    for name in names:
        if name.endswith(".duckdb"):
            con = duckdb.connect(str(folder / name))
            con.execute("CREATE TABLE _build_info (key VARCHAR, value VARCHAR)")
            con.execute("INSERT INTO _build_info VALUES ('release', ?)", [release])
            if db_format is not None:
                con.execute("INSERT INTO _build_info VALUES ('db_format', ?)", [str(db_format)])
            con.close()
        else:
            (folder / name).write_bytes(b"x")
    return [folder / name for name in names]


def _no_clone_database(monkeypatch, folder):
    monkeypatch.setenv("MCP_BINDINGDB_DATA_DIR", str(folder))
    monkeypatch.delenv("BINDINGDB_DUCKDB", raising=False)
    monkeypatch.setattr(local_build, "find_database", lambda: (_ for _ in ()).throw(FileNotFoundError()))


def test_server_answers_from_the_previous_release_while_the_new_one_builds(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    _no_clone_database(monkeypatch, folder)
    _release_files(folder, "202512")
    _release_files(folder, "202601")
    _release_files(folder, "202610", complete=False)
    started = []
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: started.append(self.release))

    path, build = local_build.locate(use_previous=True)
    assert path == folder / "bindingdb_202601.duckdb"  # the newest complete older release
    assert build is not None and build.database == folder / "bindingdb_202610.duckdb"
    if local_build.rdkit_available():
        assert started == ["202610"]
    assert (folder / "bindingdb_202512.duckdb").is_file()  # nothing is deleted until the new release is done

    path, build = local_build.locate()  # a notebook rerun waits for the release this version builds
    assert path == folder / "bindingdb_202610.duckdb" and build.database == path
    assert "to replace release 202601" in build.message()


def test_older_releases_are_removed_once_the_new_one_is_complete(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    _no_clone_database(monkeypatch, folder)
    old = _release_files(folder, "202512") + _release_files(folder, "202601", complete=False)
    current = _release_files(folder, "202610")
    newer = _release_files(folder, "202701", complete=False)  # an update that stopped (e.g. the computer slept)
    (folder / "transcripts").mkdir()
    (folder / "notes.txt").write_text("mine")
    started = []
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: started.append(self.release))

    assert local_build.locate(use_previous=True) == (folder / "bindingdb_202610.duckdb", None)
    assert not any(p.exists() for p in old)
    assert all(p.exists() for p in current + newer)
    if local_build.rdkit_available():
        assert started == ["202701"]  # the stopped update is resumed
    assert (folder / "transcripts").is_dir() and (folder / "notes.txt").is_file()


def test_a_release_still_being_built_is_not_removed(tmp_path):
    folder = tmp_path / "data"
    building = _release_files(folder, "202601", complete=False)
    _release_files(folder, "202610")
    with pipeline.lock(pipeline.lock_path(folder, "202601")):
        assert local_build.remove_old_releases(folder, "202610") == []
    assert all(p.exists() for p in building)
    assert len(local_build.remove_old_releases(folder, "202610")) == 3  # status, partial dump and lock file


def test_instructions_say_a_newer_release_is_being_built(tmp_path):
    path = tmp_path / "bindingdb_202601.duckdb"
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE _build_info AS SELECT 'release' AS key, '202601' AS value")
    con.close()
    db = Database(path)
    assert "being built" not in build_server(db, transcript_dir=tmp_path / "t").instructions
    instructions = build_server(db, transcript_dir=tmp_path / "t", building_release="202610").instructions
    assert "release 202610 is being built" in instructions and "answer from release 202601" in instructions


def test_the_newest_complete_release_is_used(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    _no_clone_database(monkeypatch, folder)
    old = _release_files(folder, "202610")
    _release_files(folder, "202611")  # built by update_database
    assert local_build.locate() == (folder / "bindingdb_202611.duckdb", None)
    assert not any(p.exists() for p in old)


def test_latest_release_tries_this_month_and_the_ones_before(monkeypatch):
    from datetime import date

    asked = []

    def size(release):
        asked.append(release)
        return {"202610": 257_801_530, "202609": 251_842_538}.get(release)

    monkeypatch.setattr(local_build, "release_size", size)
    assert local_build.latest_release(date(2026, 11, 20)) == ("202610", 257_801_530)
    assert asked == ["202611", "202610"]
    asked.clear()
    assert local_build.latest_release(date(2027, 1, 2), months=2) is None and asked == ["202701", "202612"]


def _database(path, release):
    path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path))
    con.execute(f"CREATE TABLE _build_info AS SELECT 'release' AS key, '{release}' AS value")
    con.close()
    path.with_suffix(".sslib").write_bytes(b"x")
    return Database(path)


async def test_update_database(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    db = _database(folder / "bindingdb_202610.duckdb", "202610")
    monkeypatch.setattr(local_build, "latest_release", lambda: ("202611", 260_827_759))
    from mcp_bindingdb import substructure

    monkeypatch.setattr(substructure, "rdkit_available", lambda: True)  # as in the bundle
    monkeypatch.setattr(local_build, "rdkit_available", lambda: True)
    started = []
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: started.append(self.release))

    async def update(server, **args):
        async with Client(server) as client:
            result = await client.call_tool("update_database", args)
        assert not result.is_error, result.content
        return result.structured_content

    fixed = await update(build_server(db, transcript_dir=tmp_path / "t"))  # a database named in the configuration
    assert "cannot update it itself" in fixed["message"]

    server = build_server(db, transcript_dir=tmp_path / "t", update_folder=folder)
    found = await update(server)
    assert found["latest_release"] == "202611" and found["download_mb"] == 261 and "Ask the user" in found["message"]
    assert not started
    building = await update(server, start=True)
    assert started == ["202611"] and building["building_release"] == "202611"

    _release_files(folder, "202611")  # the build finishes
    ready = await update(server)
    assert ready["ready_release"] == "202611" and "quit and reopen" in ready["message"].lower()

    monkeypatch.setattr(local_build, "latest_release", lambda: ("202610", 257_801_530))
    current = await update(build_server(db, transcript_dir=tmp_path / "t", update_folder=tmp_path / "other"))
    assert "up to date" in current["message"]


def test_db_format(tmp_path):
    folder = tmp_path / "data"
    _release_files(folder, "202610")
    _release_files(folder, "202611", db_format=2)
    (folder / "bindingdb_202612.duckdb").write_bytes(b"not a database")
    assert local_build.db_format(folder / "bindingdb_202610.duckdb") == 1  # not recorded: the first layout
    assert local_build.db_format(folder / "bindingdb_202611.duckdb") == 2
    assert local_build.db_format(folder / "bindingdb_202612.duckdb") == 0


def test_a_database_of_an_older_layout_is_rebuilt(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    _no_clone_database(monkeypatch, folder)
    monkeypatch.setattr(local_build, "DB_FORMAT", 2)  # as if this version changed the layout
    _release_files(folder, "202611")  # format 1, updated to after DEFAULT_RELEASE
    started = []
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: started.append(self.release))

    path, build = local_build.locate(use_previous=True)
    assert path == folder / "bindingdb_202611.duckdb" and build is not None and build.rebuild
    assert build.database == path and not path.exists()  # the same release, built again from the start
    assert not (folder / "bindingdb_202611.sslib").exists() and not (folder / "build-202611.json").exists()
    if local_build.rdkit_available():
        assert started == ["202611"]
    assert "rebuilt on this computer for this version" in build.message()

    _release_files(folder, "202611", db_format=2)  # the rebuild finishes
    assert local_build.locate(use_previous=True) == (path, None)


def test_a_usable_release_answers_while_an_older_layout_is_rebuilt(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    _no_clone_database(monkeypatch, folder)
    monkeypatch.setattr(local_build, "DB_FORMAT", 2)
    _release_files(folder, "202610", db_format=2)
    _release_files(folder, "202611")  # format 1
    monkeypatch.setattr(local_build.LocalBuild, "start", lambda self: None)
    path, build = local_build.locate(use_previous=True)
    assert path == folder / "bindingdb_202610.duckdb" and build.release == "202611" and build.rebuild


def test_instructions_warn_about_an_older_layout(tmp_path, monkeypatch):
    from mcp_bindingdb import server

    db = _database(tmp_path / "bindingdb_202610.duckdb", "202610")
    assert "older version of mcp-bindingdb" not in build_server(db, transcript_dir=tmp_path / "t").instructions
    monkeypatch.setattr(server, "DB_FORMAT", 2)
    assert "older version of mcp-bindingdb" in build_server(db, transcript_dir=tmp_path / "t").instructions


def test_build_times_are_recorded_and_used_for_estimates(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    assert local_build.build_time(folder) == "about half an hour"
    status = pipeline.Status(folder, "202610", pipeline.machine_info(9, True))
    for key, seconds in [("download", 70), ("load", 17), ("derived", 3), ("inchikeys", 220),
                         ("properties", 1100), ("index", 90)]:
        status.step(key)
        status.finish_step(key, seconds)
    status.end("done")
    recorded = pipeline.read_status(folder, "202610")
    assert recorded["build_seconds"] == 1500 and recorded["step_seconds"]["inchikeys"] == 220
    assert recorded["machine"]["workers"] == 9 and recorded["machine"]["background"] is True
    assert local_build.build_time(folder).startswith("about 25 minutes (as long as the last build")

    resumed = pipeline.Status(folder, "202610")  # a resumed run keeps the steps already timed
    assert resumed.data["step_seconds"]["properties"] == 1100


def test_an_unpacked_dump_of_an_old_release_is_removed_too(tmp_path):
    # An older version of this package unpacked the dump beside the zip; the pattern missed the .dmp, so
    # 2.2 GB of a superseded release stayed behind.
    folder = tmp_path / "data"
    _release_files(folder, "202610")
    _release_files(folder, "202611")
    for name in ("BDB-mySQL_All_202610.dmp", "BDB-mySQL_All_202610_dmp.zip"):
        (folder / name).write_bytes(b"dump")
    removed = {p.name for p in local_build.remove_old_releases(folder, "202611")}
    assert "BDB-mySQL_All_202610.dmp" in removed and "BDB-mySQL_All_202610_dmp.zip" in removed
    assert not list(folder.glob("*202610*"))
    assert (folder / "bindingdb_202611.duckdb").is_file()  # the release in use is untouched


def test_locate_sweeps_a_clones_data_folder(tmp_path, monkeypatch):
    # The clone's data/ outranks data_dir() but used never to be cleaned, so a clone stayed on an old release
    # while the user data folder moved on, with nothing saying so.
    folder = tmp_path / "clone" / "data"
    _release_files(folder, "202610", db_format=local_build.DB_FORMAT)
    _release_files(folder, "202611", db_format=local_build.DB_FORMAT)
    monkeypatch.delenv("BINDINGDB_DUCKDB", raising=False)
    monkeypatch.setattr(local_build, "find_database", lambda: folder / "bindingdb_202611.duckdb")
    path, build = local_build.locate()
    assert path == folder / "bindingdb_202611.duckdb" and build is None
    assert not list(folder.glob("*202610*"))


def test_locate_leaves_a_hand_named_database_alone(tmp_path, monkeypatch):
    folder = tmp_path / "elsewhere"
    _release_files(folder, "202610", db_format=local_build.DB_FORMAT)
    _release_files(folder, "202611", db_format=local_build.DB_FORMAT)
    monkeypatch.setenv("BINDINGDB_DUCKDB", str(folder / "bindingdb_202611.duckdb"))
    local_build.locate()
    assert (folder / "bindingdb_202610.duckdb").is_file()  # --db / $BINDINGDB_DUCKDB is hand-managed
