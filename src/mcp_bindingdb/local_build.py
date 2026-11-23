"""First-use build of the database on the user's computer, so the server needs no setup.

When the server finds no database (no --db, $BINDINGDB_DUCKDB or data/bindingdb_*.duckdb in a clone), it builds
release builder.DEFAULT_RELEASE in the user data folder (data_dir()): it downloads BindingDB's MySQL dump from
bindingdb.org and runs mcp_bindingdb.builder in a separate, low-priority process, so the server starts at once.
Until the database is there, the tools that need it fail with a message that says how far the build has got
(from the status file the builder writes). The builder keeps running if the server exits, a second server
process waits for it instead of starting another, and a build that stopped resumes where it ended.

BindingDB publishes a release every month. The server uses the newest complete release in the folder (at least
DEFAULT_RELEASE), and builds a newer one in the background when the user asks (the update_database tool, with
latest_release), answering from the release it has meanwhile. A newer DEFAULT_RELEASE in a new version of the
server is built the same way (locate(use_previous=True)). Once a newer release is complete, the next server start
uses it and deletes the older releases' files (remove_old_releases). A database of an older layout (db_format
below builder.DB_FORMAT, after an update of the server) is rebuilt, same release, before it is used.

With a folder of prebuilt releases ($MCP_BINDINGDB_MIRROR, builder.prebuilt), the builder downloads a release
already built instead of building it, and builds it if that fails; a first use then takes the mirror's newest
release.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

import duckdb

from .builder import DB_FORMAT, DEFAULT_RELEASE, prebuilt
from .builder.pipeline import (RELEASE_FILE, SOURCE_URL, STEPS, database_path, is_locked, lock_path,
                               read_status, remove_old_releases, status_path)
from .db import QueryError, find_database
from .substructure import index_path, rdkit_available

# What the finished build's _build_info says about its contents, so the server can offer every tool before
# the database is there (the release and the source checksum are filled in once it is).
EXPECTED_INFO = {"inchi_keys": "standard InChIKeys computed from SMILES by RDKit",
                 "properties": "compound_property computed from SMILES (largest fragment) by RDKit"}


class NotReady(QueryError, ToolError):
    """A tool needs the database or index, which is still being built; the message says how far it has got.
    A ToolError, so the model sees the message also when a tool does not catch it."""


def data_dir() -> Path:
    """Where the database is built: $MCP_BINDINGDB_DATA_DIR, else the platform's per-user data folder."""
    env = os.environ.get("MCP_BINDINGDB_DATA_DIR", "").strip()
    if env and "${" not in env:  # a bundle setting the host left unsubstituted
        return Path(env).expanduser()
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "mcp-bindingdb"
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local") / "mcp-bindingdb"
    return Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share") / "mcp-bindingdb"


def complete_releases(folder: Path) -> list[str]:
    """The releases in `folder` with both the database and its index, oldest first."""
    return sorted(p.name[len("bindingdb_"):-len(".duckdb")] for p in folder.glob("bindingdb_*.duckdb")
                  if index_path(p).is_file())


def db_format(path: Path) -> int:
    """The layout version a database was built with (_build_info db_format; 1 if not recorded), or 0 if it
    cannot be read."""
    try:
        con = duckdb.connect(str(path), read_only=True)
        try:
            row = con.execute("SELECT value FROM _build_info WHERE key = 'db_format'").fetchone()
        finally:
            con.close()
        return int(row[0]) if row else 1
    except (duckdb.Error, ValueError):
        return 0


def current_releases(folder: Path) -> list[str]:
    """The complete releases in `folder` built with this version's DB_FORMAT, oldest first."""
    return [r for r in complete_releases(folder) if db_format(database_path(folder, r)) == DB_FORMAT]


def previous_release(folder: Path, release: str = DEFAULT_RELEASE) -> str | None:
    """The newest usable (complete, current-format) release in `folder` older than `release`, if any."""
    older = [r for r in current_releases(folder) if r < release]
    return older[-1] if older else None


def unfinished_release(folder: Path, after: str) -> str | None:
    """The newest release newer than `after` whose build in `folder` was started but is not complete, if any."""
    started = sorted(p.name[len("build-"):-len(".json")] for p in folder.glob("build-*.json"))
    pending = [r for r in started if r > after and not LocalBuild(folder, r).complete()]
    return pending[-1] if pending else None


def release_size(release: str, timeout: float = 15) -> int | None:
    """The size in bytes of the release's dump on bindingdb.org, or None if there is none."""
    request = urllib.request.Request(SOURCE_URL.format(release=release), method="HEAD",
                                     headers={"User-Agent": "mcp-bindingdb"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.headers.get("Content-Length") or 0) or None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def latest_release(today: date | None = None, months: int = 4) -> tuple[str, int] | None:
    """The newest release on bindingdb.org and its download size: releases are named by year and month
    (YYYYMM) and published around the start of the month, so this month's and the few before are tried, newest
    first. None if there is none of them. Raises OSError if bindingdb.org cannot be reached."""
    today = today or date.today()
    year, month = today.year, today.month
    for _ in range(months):
        release = f"{year}{month:02d}"
        if (size := release_size(release)) is not None:
            return release, size
        year, month = (year, month - 1) if month > 1 else (year - 1, 12)
    return None


def _minutes(seconds: float) -> str:
    return f"{seconds / 60:.0f} minutes" if seconds >= 90 else "about a minute"


def last_build_seconds(folder: Path) -> float | None:
    """How long the newest finished build in `folder` took (the sum of its steps), to estimate the next one."""
    times = sorted((p.name, s["build_seconds"]) for p in folder.glob("build-*.json")
                   if (s := _read_json(p)).get("state") == "done" and s.get("build_seconds"))
    return times[-1][1] if times else None


def build_time(folder: Path) -> str:
    """The expected build time, for messages: from the last build on this computer if there was one."""
    seconds = last_build_seconds(folder)
    return (f"about {_minutes(seconds)} (as long as the last build on this computer took)" if seconds
            else "about half an hour")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


class LocalBuild:
    """Runs and reports on the build of one release in `folder` (python -m mcp_bindingdb.builder)."""

    def __init__(self, folder: Path, release: str = DEFAULT_RELEASE, rebuild: bool = False) -> None:
        """`rebuild`: the release was there in an older layout (db_format) and is built again."""
        self.folder = folder
        self.release = release
        self.rebuild = rebuild
        self.database = database_path(folder, release)
        self.index = index_path(self.database)
        self.build_info: dict[str, str] = {"release": release, "db_format": str(DB_FORMAT), **EXPECTED_INFO}
        self._process: subprocess.Popen[bytes] | None = None

    def complete(self) -> bool:
        return self.database.is_file() and self.index.is_file()

    def running(self) -> bool:
        return is_locked(lock_path(self.folder, self.release))

    def start(self) -> None:
        """Start the builder unless it is running (here or in another process) or the build is complete."""
        if self.complete() or (self._process is not None and self._process.poll() is None) or self.running():
            return
        self.folder.mkdir(parents=True, exist_ok=True)
        log = open(self.folder / f"build-{self.release}.log", "ab")  # noqa: SIM115 - handed to the child
        command = [sys.executable, "-m", "mcp_bindingdb.builder", "--release", self.release,
                   "--dir", str(self.folder), "--background"]
        options: dict[str, Any] = {"stdin": subprocess.DEVNULL, "stdout": log, "stderr": subprocess.STDOUT}
        if os.name == "nt":  # no console window, and not ended with the server
            options["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            options["start_new_session"] = True
        self._process = subprocess.Popen(command, **options)
        log.close()
        print(f"mcp-bindingdb: building BindingDB {self.release} in {self.folder} (pid {self._process.pid}); "
              f"log: {log.name}", file=sys.stderr)
        deadline = time.monotonic() + 5  # wait for the builder to take its lock, so start() is not repeated
        while time.monotonic() < deadline and self._process.poll() is None and not self.running():
            time.sleep(0.05)

    def require(self, path: Path) -> None:
        """Return if `path` is there; else (re)start the build and raise NotReady with its progress."""
        if path.is_file():
            return
        if not rdkit_available():
            raise NotReady(f"The BindingDB database is not on this computer yet, and it cannot be built here: the "
                           "build needs RDKit. Run the server with uv's `--extra substructure` (or point "
                           "BINDINGDB_DUCKDB at a database you built). Tell the user.")
        self.start()
        raise NotReady(self.message(path))

    def message(self, path: Path | None = None) -> str:
        """Where the build stands, for the model to pass on to the user."""
        status = read_status(self.folder, self.release)
        what = ("The structure-search index" if path is not None and path == self.index
                else f"The BindingDB database (release {self.release})")
        if status.get("step") == "prebuilt" and status.get("state") == "running":
            mirror = prebuilt.mirror_url()
            line = (f"{what} is being downloaded, already built, from "
                    f"{prebuilt.mirror_host(mirror) if mirror else 'a mirror'} (it takes a minute or two)")
            if status.get("total"):
                line += f": {status['done'] / 1e6:.0f} of {status['total'] / 1e6:.0f} MB"
            return line + ". Tell the user, and that the BindingDB tools work once it is done."
        if status.get("state") == "failed" and not self.running():
            return (f"{what} could not be built: {status.get('error')}. The build starts again with this call "
                    "and resumes where it stopped; try again in a few minutes. If this keeps happening, tell the "
                    f"user: it needs an internet connection and about 4 GB of free disk space in {self.folder} "
                    f"(the log is {status_path(self.folder, self.release).with_suffix('.log')}).")
        weights = {key: w for key, _, w in STEPS}
        labels = {key: label for key, label, _ in STEPS}
        done_steps = status.get("done_steps", [])
        step = status.get("step")
        fraction = status["done"] / status["total"] if step and status.get("total") else 0.0
        total = sum(weights.values())
        overall = (sum(weights[s] for s in done_steps if s in weights)
                   + (weights.get(step, 0) * fraction if step not in done_steps else 0)) / total
        previous = previous_release(self.folder, self.release)
        if self.rebuild and not previous:
            line = (f"{what} is being rebuilt on this computer for this version of mcp-bindingdb, which needs a newer "
                    "database layout (once only; it takes about half an hour and runs in the background)")
        elif previous:
            line = (f"{what} is being built on this computer to replace release {previous} (it takes about half an "
                    "hour and runs in the background)")
        else:
            line = (f"{what} is being built on this computer for first use (once only; it takes about half an hour "
                    "and runs in the background)")
        if step in labels:
            n = [s[0] for s in STEPS].index(step) + 1
            line += f": step {n} of {len(STEPS)}, {labels[step]}"
            if fraction >= 0.01:
                line += f" ({fraction:.0%})"
            elapsed = time.time() - status.get("started_at", time.time())
            if overall > 0.1 and elapsed > 60:
                line += f"; about {_minutes(elapsed * (1 - overall) / overall)} left in all"
        else:
            line += ": starting"
        if previous and path is None:
            return (line + f". Meanwhile the tools answer from release {previous}; once it is done, quit and reopen "
                    "Claude to switch to the new release. Tell the user.")
        return line + ". Tell the user, and that the BindingDB tools work once it is done."

    def wait(self, report_every: float = 60.0) -> None:
        """Block until the build is complete or has stopped (for notebooks), printing progress now and then."""
        self.start()
        last = 0.0
        while not self.complete():
            if not self.running() and (self._process is None or self._process.poll() is not None):
                if not self.complete():
                    raise RuntimeError(self.message())
                break
            if time.monotonic() - last >= report_every:
                print(self.message().split(". Tell the user")[0] + ".", flush=True)
                last = time.monotonic()
            time.sleep(2)


def locate(explicit: str | None = None, use_previous: bool = False) -> tuple[Path, LocalBuild | None]:
    """The database to open, and the LocalBuild still making it (or its index), if any.

    Order: `explicit` (--db), $BINDINGDB_DUCKDB, the newest data/bindingdb_*.duckdb of a clone, then the newest
    complete release in data_dir() built with this DB_FORMAT, if it is at least DEFAULT_RELEASE. Else a release
    is built there in the background: DEFAULT_RELEASE, or the newest release on the computer again if it is in an
    older layout (its old files are deleted first; an old layout may not work with this version's tools).
    Meanwhile, with `use_previous` (the server, not a notebook rerun, which waits for it), the newest older usable
    release is returned if there is one, with the LocalBuild (whose `database` is then not the path returned). A
    newer release whose build was started (update_database) but stopped is resumed. Releases older than the one
    returned are deleted, from a clone's data/ as from data_dir(); a database named with --db or
    $BINDINGDB_DUCKDB is hand-managed, so nothing beside it is touched."""
    if explicit:
        return Path(explicit).expanduser(), None
    if os.environ.get("BINDINGDB_DUCKDB"):
        return find_database(), None  # raises if the file is missing, and is hand-managed: nothing is deleted
    try:
        clone = find_database()
    except FileNotFoundError:
        pass
    else:  # a clone's data/ is swept like data_dir(), so a rebuilt clone keeps no trace of the release before
        remove_old_releases(clone.parent, clone.name[len("bindingdb_"):-len(".duckdb")])
        return clone, None
    folder = data_dir()
    complete = complete_releases(folder) if folder.is_dir() else []
    current = [r for r in complete if db_format(database_path(folder, r)) == DB_FORMAT]
    outdated = [r for r in complete if r not in current]
    if current and current[-1] >= DEFAULT_RELEASE and (not outdated or current[-1] > outdated[-1]):
        newest = current[-1]
        remove_old_releases(folder, newest)
        if (update := unfinished_release(folder, newest)) is not None and rdkit_available():
            LocalBuild(folder, update).start()  # resumes an update that stopped (e.g. the computer slept)
        return database_path(folder, newest), None
    # Build DEFAULT_RELEASE, or rebuild the newest release on the computer if it is newer and in an older layout;
    # or, with a mirror of prebuilt releases, its newest if that is newer (downloaded rather than built).
    release = outdated[-1] if outdated and outdated[-1] > DEFAULT_RELEASE else DEFAULT_RELEASE
    if (mirrored := prebuilt.newest_release(DB_FORMAT)) is not None and mirrored > release:
        release = mirrored
    rebuild = release in outdated
    if rebuild and not _discard(folder, release):
        print(f"mcp-bindingdb: release {release} needs rebuilding for this version (database layout "
              f"{DB_FORMAT}), but its files are in use; using it as it is", file=sys.stderr)
        return database_path(folder, release), None
    build = LocalBuild(folder, release, rebuild=rebuild)
    if rdkit_available():
        build.start()
    if use_previous and (previous := previous_release(folder, release)) is not None:
        return database_path(folder, previous), build
    return build.database, build


def _discard(folder: Path, release: str) -> bool:
    """Delete a release's database, index and build status, so it is built again from the start; False if a file
    is in use (on Windows) or the release is being built."""
    if lock_path(folder, release).is_file() and is_locked(lock_path(folder, release)):
        return False
    try:
        for path in (database_path(folder, release), index_path(database_path(folder, release)),
                     status_path(folder, release)):
            path.unlink(missing_ok=True)
    except OSError:
        return False
    return True
