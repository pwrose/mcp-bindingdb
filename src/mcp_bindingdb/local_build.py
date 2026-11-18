"""First-use build of the database on the user's computer, so the server needs no setup.

When the server finds no database (no --db, $BINDINGDB_DUCKDB or data/bindingdb_*.duckdb in a clone), it builds
release builder.DEFAULT_RELEASE in the user data folder (data_dir()): it downloads BindingDB's MySQL dump from
bindingdb.org and runs mcp_bindingdb.builder in a separate, low-priority process, so the server starts at once.
Until the database is there, the tools that need it fail with a message that says how far the build has got
(from the status file the builder writes). The builder keeps running if the server exits, a second server
process waits for it instead of starting another, and a build that stopped resumes where it ended.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from mcp.server.mcpserver.exceptions import ToolError

from .builder import DEFAULT_RELEASE
from .builder.pipeline import STEPS, database_path, is_locked, lock_path, read_status, status_path
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


def _minutes(seconds: float) -> str:
    return f"{seconds / 60:.0f} minutes" if seconds >= 90 else "about a minute"


class LocalBuild:
    """Runs and reports on the build of one release in `folder` (python -m mcp_bindingdb.builder)."""

    def __init__(self, folder: Path, release: str = DEFAULT_RELEASE) -> None:
        self.folder = folder
        self.release = release
        self.database = database_path(folder, release)
        self.index = index_path(self.database)
        self.build_info: dict[str, str] = {"release": release, **EXPECTED_INFO}
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


def locate(explicit: str | None = None) -> tuple[Path, LocalBuild | None]:
    """The database to open, and the LocalBuild still making it (or its index), if any.

    Order: `explicit` (--db), $BINDINGDB_DUCKDB, the newest data/bindingdb_*.duckdb of a clone, then release
    DEFAULT_RELEASE in data_dir(), built there (in the background) if it is not there yet."""
    if explicit:
        return Path(explicit).expanduser(), None
    if os.environ.get("BINDINGDB_DUCKDB"):
        return find_database(), None  # raises if the file is missing
    try:
        return find_database(), None
    except FileNotFoundError:
        pass
    build = LocalBuild(data_dir())
    if build.complete():
        return build.database, None
    if rdkit_available():
        build.start()
    return build.database, build
