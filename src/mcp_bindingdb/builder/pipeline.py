"""The build, step by step: download BindingDB's dump, load it into DuckDB, add the derived tables, compute
standard InChIKeys and compound properties, and build the structure-search index.

Progress goes to build-<release>.json in the output folder (Status), which the server reads to tell the user
how far the build has got. A lock file keeps two builds of a release from running at once. A build that
stopped resumes: the download continues where it ended, and the finished steps are not redone.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import IO, Any, Callable

import duckdb

SOURCE_URL = "https://www.bindingdb.org/rwd/bind/BDB-mySQL_All_{release}_dmp.zip"
CHUNK = 1 << 20

# (key, what the step does, relative duration: minutes on 10 cores for release 202610)
STEPS = [
    ("download", "downloading the BindingDB dump", 1.0),
    ("load", "loading the dump into a database", 0.3),
    ("derived", "adding query tables", 0.1),
    ("inchikeys", "computing standard InChIKeys", 3.6),
    ("properties", "computing compound properties and structural alerts", 18.0),
    ("index", "building the structure-search index", 1.5),
]


class AlreadyRunning(RuntimeError):
    pass


class Superseded(RuntimeError):
    """A newer release became complete in the folder (e.g. downloaded prebuilt) while this one was built."""


def newer_complete(folder: Path, release: str) -> str | None:
    """The newest release in `folder` newer than `release` with both its database and index, if any."""
    newer = sorted(p.name[len("bindingdb_"):-len(".duckdb")] for p in folder.glob("bindingdb_*.duckdb")
                   if p.with_suffix(".sslib").is_file())
    newer = [r for r in newer if r > release]
    return newer[-1] if newer else None


def database_path(folder: Path, release: str) -> Path:
    return folder / f"bindingdb_{release}.duckdb"


def status_path(folder: Path, release: str) -> Path:
    return folder / f"build-{release}.json"


def lock_path(folder: Path, release: str) -> Path:
    return folder / f".build-{release}.lock"


def read_status(folder: Path, release: str) -> dict[str, Any]:
    try:
        return json.loads(status_path(folder, release).read_text())
    except (FileNotFoundError, ValueError):
        return {}


def lock(path: Path) -> IO[bytes] | None:
    """An exclusive lock on `path` (held while the returned file is open), or None if another process has it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    f = open(path, "a+b")  # noqa: SIM115 - returned open, as the lock
    try:
        if os.name == "nt":
            import msvcrt
            f.seek(0)
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        f.close()
        return None
    return f


def is_locked(path: Path) -> bool:
    held = lock(path)
    if held is None:
        return True
    held.close()
    return False


class Status:
    """build-<release>.json: the current step, its progress, the finished steps and any error; and, to estimate
    build times, how long each step took (step_seconds, kept across resumed runs) on what machine."""

    def __init__(self, folder: Path, release: str, machine: dict[str, Any] | None = None) -> None:
        self.path = status_path(folder, release)
        previous = read_status(folder, release)
        self.data: dict[str, Any] = {"release": release, "state": "running", "pid": os.getpid(),
                                     "started_at": time.time(), "steps": [s[0] for s in STEPS],
                                     "done_steps": previous.get("done_steps", []), "step": None,
                                     "done": 0, "total": 0, "error": None,
                                     "step_seconds": previous.get("step_seconds", {}), "machine": machine or {}}
        self._written = 0.0
        self.check: Callable[[], None] | None = None  # raises to stop the build (see build); called now and then
        self._checked = time.monotonic()
        self._write()

    def _write(self) -> None:
        self.data["updated_at"] = time.time()
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data))
        tmp.replace(self.path)
        self._written = time.monotonic()

    def step(self, key: str) -> None:
        if self.check:
            self.check()
        self.data.update(step=key, done=0, total=0, step_started_at=time.time())
        self._write()

    def progress(self, done: int, total: int) -> None:
        self.data.update(done=done, total=total)
        if time.monotonic() - self._written >= 1.0 or done >= total:
            self._write()
        if self.check and time.monotonic() - self._checked >= 30:
            self._checked = time.monotonic()
            self.check()

    def finish_step(self, key: str, seconds: float | None = None) -> None:
        if key not in self.data["done_steps"]:
            self.data["done_steps"].append(key)
        if seconds is not None:
            self.data["step_seconds"][key] = round(seconds, 1)
        self._write()

    def end(self, state: str, error: str | None = None) -> None:
        self.data.update(state=state, error=error, step=None if state == "done" else self.data["step"])
        if state == "done":  # the build's own steps: a prebuilt download says nothing about build times
            self.data["build_seconds"] = round(sum(v for k, v in self.data["step_seconds"].items()
                                                   if k != "prebuilt"), 1)
        self._write()


def machine_info(workers: int | None, background: bool) -> dict[str, Any]:
    """What a build ran on, recorded with its step times."""
    return {"system": platform.system(), "release": platform.release(), "machine": platform.machine(),
            "processor": platform.processor(), "cpu_count": os.cpu_count(),
            "workers": workers or os.cpu_count(), "background": background,
            "python": platform.python_version(), "duckdb": duckdb.__version__}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(8 * CHUNK):
            h.update(block)
    return h.hexdigest()


def download(url: str, dest: Path, progress: Callable[[int, int], None]) -> None:
    """Fetch `url` to `dest`, resuming a partial file with a Range request; checks the size the server gives."""
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "mcp-bindingdb"})
    with urllib.request.urlopen(request, timeout=60) as response:
        size = int(response.headers["Content-Length"])
    part = dest.with_name(dest.name + ".part")
    if dest.is_file() and dest.stat().st_size == size:
        progress(size, size)
        return
    have = part.stat().st_size if part.is_file() else 0
    if have > size:
        have = 0
    if have < size:
        headers = {"User-Agent": "mcp-bindingdb", **({"Range": f"bytes={have}-"} if have else {})}
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as response:
            if have and response.status != 206:  # the server ignored the Range: start over
                have = 0
            with open(part, "ab" if have else "wb") as out:
                done = have
                while block := response.read(CHUNK):
                    out.write(block)
                    done += len(block)
                    progress(done, size)
    if part.stat().st_size != size:
        raise ConnectionError(f"the download stopped at {part.stat().st_size:,} of {size:,} bytes; it resumes "
                              "on the next try")
    part.replace(dest)


def build(release: str, folder: Path, workers: int | None = None, keep_zip: bool = False,
          log: Callable[[str], None] = print, background: bool = False, mirror: str | None = None) -> Path:
    """Build bindingdb_<release>.duckdb and its .sslib index in `folder`; returns the database path. With a
    `mirror` (a folder of prebuilt releases: see prebuilt; default $MCP_BINDINGDB_MIRROR, "" for none) that has
    the release, they
    are downloaded prebuilt instead, and built here if that fails. Raises AlreadyRunning if another process is
    building the release."""
    from . import DB_FORMAT, compound_properties, derived, inchikeys, mysqldump, prebuilt, structure_index

    folder.mkdir(parents=True, exist_ok=True)
    held = lock(lock_path(folder, release))
    if held is None:
        raise AlreadyRunning(f"release {release} is already being built in {folder}")
    target = database_path(folder, release)
    building = target.with_name(target.name + ".building")
    index = structure_index.index_path(target)
    zip_path = folder / f"BDB-mySQL_All_{release}_dmp.zip"
    url = SOURCE_URL.format(release=release)
    with held:
        status = Status(folder, release, machine_info(workers, background))
        if background:  # the server's build: pointless once a newer release is complete (one it downloaded)

            def check() -> None:
                if (newer := newer_complete(folder, release)) is not None:
                    raise Superseded(f"release {newer} is complete in {folder}, so release {release} is not "
                                     "needed; stopped building it")

            status.check = check
        mirror = prebuilt.mirror_url() if mirror is None else (None if mirror.lower() in prebuilt.NO_MIRROR
                                                                  else mirror)
        if mirror and not target.is_file() and _fetch_prebuilt(mirror, release, folder, target, index, status, log):
            return target
        done = status.data["done_steps"]
        if not building.is_file() and not target.is_file():
            done[:] = [s for s in done if s == "download"]  # nothing built yet: redo the database steps
        try:
            for key, label, _ in STEPS:
                if key in done and (key != "download" or zip_path.is_file() or "load" in done):
                    continue
                status.step(key)
                log(f"{label}")
                t0 = time.time()
                if key == "download":
                    download(url, zip_path, status.progress)
                elif key == "load":
                    building.unlink(missing_ok=True)
                    con = duckdb.connect(str(building))
                    counts = mysqldump.load(zip_path, con, lambda d, t, _table: status.progress(d, t))
                    info = {"release": release, "db_format": DB_FORMAT, "source_url": url, "source_zip": zip_path.name,
                            "source_zip_bytes": zip_path.stat().st_size, "source_zip_sha256": sha256(zip_path),
                            "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "duckdb_version": duckdb.__version__,
                            "excluded_tables": json.dumps(sorted(mysqldump.PII_TABLES)),
                            "table_row_counts": json.dumps(counts)}
                    con.execute("CREATE TABLE _build_info (key VARCHAR, value VARCHAR)")
                    con.executemany("INSERT INTO _build_info VALUES (?, ?)", [[k, str(v)] for k, v in info.items()])
                    con.execute("CHECKPOINT")
                    con.close()
                elif key == "derived":
                    con = duckdb.connect(str(building))
                    derived.add(con)
                    con.execute("CHECKPOINT")
                    con.close()
                elif key == "inchikeys":
                    inchikeys.update(building, workers, status.progress)
                elif key == "properties":
                    compound_properties.update(building, workers, status.progress)
                    building.replace(target)  # usable from here on; the index follows
                elif key == "index":
                    structure_index.build(target, index, workers, status.progress)
                status.finish_step(key, time.time() - t0)
                log(f"  done in {time.time() - t0:.0f}s")
            if not keep_zip:
                zip_path.unlink(missing_ok=True)
            status.end("done")
            log(f"Build time {status.data['build_seconds'] / 60:.1f} min: "
                + ", ".join(f"{k} {v:.0f}s" for k, v in status.data["step_seconds"].items()))
        except Superseded as e:
            building.unlink(missing_ok=True)
            zip_path.unlink(missing_ok=True)
            Path(str(zip_path) + ".part").unlink(missing_ok=True)
            status.end("superseded", str(e))
            raise
        except BaseException as e:
            status.end("failed", f"{type(e).__name__}: {e}" if str(e) else type(e).__name__)
            raise
    log(f"Built {target} and {index.name}")
    return target


def _fetch_prebuilt(mirror: str, release: str, folder: Path, target: Path, index: Path, status: Status,
                    log: Callable[[str], None]) -> bool:
    """Download the release prebuilt from `mirror` (see build); False, after logging why, if the mirror does not
    have it or the download fails, so the caller builds it."""
    from . import DB_FORMAT, prebuilt

    where = prebuilt.mirror_host(mirror)
    try:
        item = prebuilt.Mirror(mirror).release(release, DB_FORMAT)
        if item is None:
            log(f"the mirror ({where}) has no prebuilt release {release} for this version; building it here")
            return False
        status.data["source"] = "prebuilt"
        status.step("prebuilt")
        log(f"downloading the prebuilt release {release} from {where} "
            f"({prebuilt.download_size(item) / 1e6:.0f} MB)")
        t0 = time.time()
        prebuilt.fetch(item, release, folder, {"duckdb": target, "sslib": index}, DB_FORMAT, status.progress, log)
    except Exception as e:  # noqa: BLE001 - any failure: build it here instead
        status.data.pop("source", None)
        log(f"the prebuilt download failed ({type(e).__name__}: {e}); building release {release} here instead")
        return False
    status.data["done_steps"] = [key for key, _, _ in STEPS]
    status.finish_step("prebuilt", time.time() - t0)
    status.end("done")
    log(f"  done in {time.time() - t0:.0f}s")
    log(f"Downloaded {target} and {index.name} from {where}")
    return True


def main(argv: list[str] | None = None) -> int:
    import argparse

    from . import DEFAULT_RELEASE

    p = argparse.ArgumentParser(prog="python -m mcp_bindingdb.builder",
                                description="Build a BindingDB DuckDB database from BindingDB's MySQL dump.")
    p.add_argument("--release", default=DEFAULT_RELEASE, help=f"BindingDB release (default {DEFAULT_RELEASE})")
    p.add_argument("--dir", type=Path, required=True, help="Output folder")
    p.add_argument("--workers", type=int, default=None, help="Worker processes (default: all CPUs)")
    p.add_argument("--keep-zip", action="store_true", help="Keep the downloaded dump")
    p.add_argument("--mirror", default=None,
                   help="Folder of prebuilt releases to download instead of building (default "
                        "$MCP_BINDINGDB_MIRROR, else the project's folder; '' or none to build): a shared "
                        "Google Drive folder's link, a web address or a path")
    p.add_argument("--background", action="store_true",
                   help="Run at low priority, leaving one CPU free (as the server does on first use)")
    args = p.parse_args(argv)
    workers = args.workers
    if args.background:
        workers = workers or max(1, (os.cpu_count() or 2) - 1)
        if hasattr(os, "nice"):
            os.nice(10)

    def log(line: str) -> None:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {line}", flush=True)

    try:
        build(args.release, args.dir, workers, args.keep_zip, log, background=args.background, mirror=args.mirror)
    except AlreadyRunning as e:
        print(e, file=sys.stderr)
        return 3
    except Superseded as e:
        log(str(e))
        return 0
    except Exception as e:  # noqa: BLE001 - recorded in the status file too
        print(f"Build failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    return 0
