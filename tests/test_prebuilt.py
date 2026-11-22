"""Prebuilt databases from a mirror folder: listing it, the download and its checks, and the fallback to building."""

import json

import duckdb
import pytest

from mcp_bindingdb import local_build
from mcp_bindingdb.builder import DB_FORMAT, pipeline, prebuilt

RELEASE = "209901"  # newer than any DEFAULT_RELEASE, so a mirror with it is preferred


def _mirror(tmp_path, release=RELEASE, db_release=None, db_format=DB_FORMAT, corrupt=None):
    """A mirror folder (tmp_path/mirror) with one release: a small database and a stand-in index, compressed as
    package_prebuilt.py does, and their .json. Returns (folder, raw files)."""
    src, out = tmp_path / "src", tmp_path / "mirror"
    src.mkdir(exist_ok=True)
    out.mkdir(exist_ok=True)
    db = src / f"bindingdb_{release}.duckdb"
    db.unlink(missing_ok=True)
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE _build_info (key VARCHAR, value VARCHAR)")
    con.executemany("INSERT INTO _build_info VALUES (?, ?)",
                    [["release", db_release or release], ["db_format", str(db_format)], ["built_at", "now"]])
    con.execute("CREATE TABLE t AS SELECT range AS n FROM range(100000)")
    con.close()
    index = src / f"bindingdb_{release}.sslib"
    index.write_bytes(b"index " * 50000)
    names, files = prebuilt.file_names(release), {}
    for kind, path in (("duckdb", db), ("sslib", index)):
        dest = out / names[kind]
        prebuilt.compress(path, dest, level=3)
        files[kind] = {"size": dest.stat().st_size, "sha256": prebuilt.sha256(dest), "raw_size": path.stat().st_size}
    if corrupt:
        files[corrupt]["sha256"] = "0" * 64
    info = prebuilt.release_info(release, {"db_format": str(db_format), "built_at": "now"}, files, "test")
    (out / names["info"]).write_text(json.dumps(info))
    return out, {"duckdb": db, "sslib": index}


DRIVE_PAGE = """<html><body><div class="flip-entries">
<div class="flip-entry" id="entry-1aaa" tabindex="0" role="link"><div class="flip-entry-info">
<a href="https://drive.google.com/file/d/1aaa/view?usp=drive_web" target="_blank"><div class="flip-entry-visual">
</div><div class="flip-entry-title">202611.duckdb.zst</div></a></div></div>
<div class="flip-entry" id="entry-1bbb" tabindex="0" role="link"><div class="flip-entry-info">
<a href="https://drive.google.com/file/d/1bbb/view?usp=drive_web"><div class="flip-entry-title">202611.sslib.zst</div>
</a></div></div>
<div class="flip-entry" id="entry-1ccc"><div class="flip-entry-title">202611.json</div></div>
<div class="flip-entry" id="entry-1ddd"><div class="flip-entry-title">202612.duckdb.zst</div></div>
<div class="flip-entry" id="entry-1eee"><div class="flip-entry-title">notes &amp; such.txt</div></div>
</div></body></html>"""


def test_a_google_drive_folder_is_listed_from_its_embedded_view(monkeypatch):
    opened = []

    class Page:
        def __init__(self, text):
            self.text = text.encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self, _n):
            return self.text

    def fake_open(url, timeout, headers=None):
        opened.append(url)
        return Page(DRIVE_PAGE)

    monkeypatch.setattr(prebuilt, "open_url", fake_open)
    mirror = prebuilt.Mirror("https://drive.google.com/drive/folders/FOLDER_id-1?usp=sharing")
    assert mirror.host == "Google Drive"
    assert mirror.releases() == ["202611"]  # 202612 lacks two of its files
    assert opened == ["https://drive.google.com/embeddedfolderview?id=FOLDER_id-1"]
    assert mirror.url("202611.sslib.zst", 5) == prebuilt.drive_download("1bbb")
    assert mirror.url("202612.sslib.zst", 5) is None
    monkeypatch.setattr(prebuilt, "open_url", lambda *a, **k: Page("<html>Sign in</html>"))
    with pytest.raises(ValueError, match="shared with 'Anyone with the link'"):
        prebuilt.Mirror("https://drive.google.com/drive/u/0/folders/x").releases()


def test_a_web_address_is_looked_up_by_release_name(tmp_path, monkeypatch):
    mirror = prebuilt.Mirror("https://www.bindingdb.org/prebuilt/")
    assert mirror.host == "www.bindingdb.org" and mirror.releases() is None
    assert mirror.url("202611.json", 5) == "https://www.bindingdb.org/prebuilt/202611.json"
    tried = []
    monkeypatch.setattr(prebuilt.Mirror, "release", lambda self, r, f, t=5: tried.append(r) or (
        {"release": r} if r == "202610" else None))
    assert mirror.newest(DB_FORMAT, today=__import__("datetime").date(2026, 12, 3)) == "202610"
    assert tried == ["202612", "202611", "202610"]


def test_without_a_mirror_setting_the_default_folder_is_used(monkeypatch):
    monkeypatch.delenv(prebuilt.MIRROR_ENV)
    assert prebuilt.mirror_url() == prebuilt.DEFAULT_MIRROR
    for unset in ("${user_config.mirror_url}", " "):  # left unfilled by the host, or empty
        monkeypatch.setenv(prebuilt.MIRROR_ENV, unset)
        assert prebuilt.mirror_url() == prebuilt.DEFAULT_MIRROR
    for off in ("none", "OFF", "0"):
        monkeypatch.setenv(prebuilt.MIRROR_ENV, off)
        assert prebuilt.mirror_url() is None
    monkeypatch.setenv(prebuilt.MIRROR_ENV, "https://www.bindingdb.org/prebuilt/")
    assert prebuilt.mirror_url() == "https://www.bindingdb.org/prebuilt/"
    assert prebuilt.mirror_host(prebuilt.DEFAULT_MIRROR) == "Google Drive"


def test_build_downloads_a_prebuilt_release(tmp_path):
    mirror, raw = _mirror(tmp_path)
    folder = tmp_path / "data"
    logged = []
    target = pipeline.build(RELEASE, folder, log=logged.append, mirror=str(mirror))
    assert target == folder / f"bindingdb_{RELEASE}.duckdb"
    assert target.read_bytes() == raw["duckdb"].read_bytes()
    assert (folder / f"bindingdb_{RELEASE}.sslib").read_bytes() == raw["sslib"].read_bytes()
    assert sorted(p.name for p in folder.iterdir()) == [f".build-{RELEASE}.lock", f"bindingdb_{RELEASE}.duckdb",
                                                        f"bindingdb_{RELEASE}.sslib", f"build-{RELEASE}.json"]
    status = pipeline.read_status(folder, RELEASE)
    assert status["state"] == "done" and status["source"] == "prebuilt" and not status["build_seconds"]
    assert local_build.last_build_seconds(folder) is None  # says nothing about how long a build takes
    assert any("downloading the prebuilt release" in line for line in logged)
    assert local_build.current_releases(folder) == [RELEASE]


@pytest.mark.parametrize("problem", ["checksum", "release", "layout", "missing"])
def test_a_bad_download_falls_back_to_building(tmp_path, problem):
    kwargs = {"checksum": {"corrupt": "sslib"}, "release": {"db_release": "200001"},
              "layout": {"db_format": DB_FORMAT + 1}, "missing": {"release": "200001"}}[problem]
    mirror, _ = _mirror(tmp_path, **kwargs)
    folder = tmp_path / "data"
    folder.mkdir()
    target = pipeline.database_path(folder, RELEASE)
    status = pipeline.Status(folder, RELEASE)
    logged = []
    assert not pipeline._fetch_prebuilt(str(mirror), RELEASE, folder, target, target.with_suffix(".sslib"),
                                        status, logged.append)
    assert not target.exists() and not target.with_suffix(".sslib").exists()
    assert not list(folder.glob("*.download"))  # nothing half-written left behind
    assert "source" not in status.data and ("building it here" in logged[-1] or "here instead" in logged[-1])
    if problem == "checksum":
        assert f"does not match the SHA-256 in {RELEASE}.json" in logged[-1]
        assert not (folder / f"bindingdb_{RELEASE}.sslib.zst").exists()  # downloaded again next time
    if problem == "release":
        assert "is release 200001" in logged[-1]


def test_an_interrupted_download_resumes(tmp_path):
    mirror, raw = _mirror(tmp_path)
    folder = tmp_path / "data"
    folder.mkdir()
    item = prebuilt.Mirror(str(mirror)).release(RELEASE, DB_FORMAT)
    whole = (mirror / f"{RELEASE}.duckdb.zst").read_bytes()
    (folder / f"bindingdb_{RELEASE}.duckdb.zst.part").write_bytes(whole[:1000])  # a local file ignores Range
    targets = {"duckdb": folder / "a.duckdb", "sslib": folder / "a.sslib"}
    prebuilt.fetch(item, RELEASE, folder, targets, DB_FORMAT, lambda d, t: None, lambda _s: None)
    assert targets["duckdb"].read_bytes() == raw["duckdb"].read_bytes()


def test_first_use_takes_the_newest_release_on_the_mirror(tmp_path, monkeypatch):
    mirror, _ = _mirror(tmp_path)
    folder = tmp_path / "data"
    monkeypatch.setenv("MCP_BINDINGDB_DATA_DIR", str(folder))
    monkeypatch.delenv("BINDINGDB_DUCKDB", raising=False)
    monkeypatch.setattr(local_build, "find_database", lambda: (_ for _ in ()).throw(FileNotFoundError()))
    monkeypatch.setattr(local_build, "rdkit_available", lambda: True)
    monkeypatch.setenv(prebuilt.MIRROR_ENV, str(mirror))
    path, build = local_build.locate()  # starts the builder, which downloads it
    assert path == folder / f"bindingdb_{RELEASE}.duckdb" and build is not None
    build.wait(report_every=3600)
    assert build.complete() and local_build.locate() == (path, None)

    monkeypatch.setenv(prebuilt.MIRROR_ENV, str(tmp_path / "nowhere"))  # an unreachable mirror
    assert prebuilt.newest_release(DB_FORMAT) is None


def test_the_progress_message_says_it_is_downloading(tmp_path, monkeypatch):
    monkeypatch.setenv(prebuilt.MIRROR_ENV, "https://drive.google.com/drive/folders/abc")
    folder = tmp_path / "data"
    folder.mkdir()
    pipeline.status_path(folder, RELEASE).write_text(json.dumps(
        {"state": "running", "step": "prebuilt", "done": 120e6, "total": 442e6, "source": "prebuilt"}))
    message = local_build.LocalBuild(folder, RELEASE).message()
    assert message.startswith(f"The BindingDB database (release {RELEASE}) is being downloaded, already built, "
                              "from Google Drive") and "120 of 442 MB" in message


def test_old_releases_downloads_are_removed_too(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    names = ["bindingdb_202501.duckdb.zst", "bindingdb_202501.sslib.zst.part", "bindingdb_202501.duckdb.download",
             "bindingdb_202501.sslib.download"]
    for name in names:
        (folder / name).write_bytes(b"x")
    assert sorted(p.name for p in local_build.remove_old_releases(folder, "202611")) == sorted(names)


def test_a_background_build_stops_once_a_newer_release_is_complete(tmp_path):
    folder = tmp_path / "data"
    folder.mkdir()
    (folder / "bindingdb_202610.duckdb.building").write_bytes(b"partial")
    (folder / "BDB-mySQL_All_202610_dmp.zip").write_bytes(b"dump")
    for name in (f"bindingdb_{RELEASE}.duckdb", f"bindingdb_{RELEASE}.sslib"):  # downloaded meanwhile
        (folder / name).write_bytes(b"x")
    with pytest.raises(pipeline.Superseded, match=f"release {RELEASE} is complete"):
        pipeline.build("202610", folder, background=True, mirror="", log=lambda _s: None)
    assert pipeline.read_status(folder, "202610")["state"] == "superseded"
    assert not (folder / "bindingdb_202610.duckdb.building").exists()
    assert not (folder / "BDB-mySQL_All_202610_dmp.zip").exists()
    assert pipeline.newer_complete(folder, RELEASE) is None
    # A build run by hand (not in the background) of an older release is left to run: it may be wanted.
    status = pipeline.Status(folder, "202609")
    assert status.check is None
