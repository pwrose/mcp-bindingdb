"""Read-only, sandboxed access to the BindingDB DuckDB file."""

from __future__ import annotations

import datetime as dt
import decimal
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb

DEFAULT_TIMEOUT_S = 30.0
MAX_CELL_CHARS = 2000  # long text cells (sequences, abstracts, raw ITC data) are truncated


class QueryError(Exception):
    """A query failed in a way the caller (the model) should see and can fix."""


def find_database() -> Path:
    """Resolve the DuckDB file: $BINDINGDB_DUCKDB, else the newest data/bindingdb_*.duckdb."""
    env = os.environ.get("BINDINGDB_DUCKDB")
    if env:
        path = Path(env).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"BINDINGDB_DUCKDB points to a missing file: {path}")
        return path
    data_dir = Path(__file__).resolve().parents[2] / "data"
    candidates = sorted(data_dir.glob("bindingdb_*.duckdb"))
    if not candidates:
        raise FileNotFoundError(
            f"No bindingdb_*.duckdb in {data_dir}; run scripts/build_duckdb.sh or set BINDINGDB_DUCKDB"
        )
    return candidates[-1]


def _jsonable(v: Any) -> Any:
    if isinstance(v, str):
        return v if len(v) <= MAX_CELL_CHARS else v[:MAX_CELL_CHARS] + f"... [{len(v)} chars]"
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (dt.date, dt.datetime, dt.time)):
        return v.isoformat()
    if isinstance(v, (bytes, bytearray)):
        return f"<{len(v)} bytes>"
    if isinstance(v, list):
        return [_jsonable(x) for x in v]
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    return v


@dataclass
class Result:
    columns: list[str]
    rows: list[dict[str, Any]]
    truncated: bool

    def as_dict(self) -> dict[str, Any]:
        return {"row_count": len(self.rows), "truncated": self.truncated, "rows": self.rows}


class Database:
    """One read-only DuckDB connection; each query runs on its own cursor (thread-safe)."""

    def __init__(self, path: Path, timeout_s: float = DEFAULT_TIMEOUT_S, memory_limit: str = "4GB"):
        self.path = path
        self.timeout_s = timeout_s
        self._con = duckdb.connect(
            str(path),
            read_only=True,
            config={
                # No file, network, or extension access from SQL; settings cannot be changed back.
                "enable_external_access": False,
                "autoinstall_known_extensions": False,
                "autoload_known_extensions": False,
                "memory_limit": memory_limit,
                "lock_configuration": True,
            },
        )

    def query(self, sql: str, params: list[Any] | None = None, limit: int = 100) -> Result:
        cur = self._con.cursor()
        timer = threading.Timer(self.timeout_s, cur.interrupt)
        timer.start()
        try:
            cur.execute(sql, params or [])
            if cur.description is None:
                return Result([], [], False)
            columns = [d[0] for d in cur.description]
            raw = cur.fetchmany(limit + 1)
        except duckdb.InterruptException:
            raise QueryError(f"Query exceeded the {self.timeout_s:.0f}s time limit; narrow it down") from None
        except duckdb.Error as e:
            raise QueryError(f"{type(e).__name__}: {e}") from None
        finally:
            timer.cancel()
            cur.close()
        rows = [dict(zip(columns, (_jsonable(v) for v in r))) for r in raw[:limit]]
        return Result(columns, rows, truncated=len(raw) > limit)

    def rows(self, sql: str, params: list[Any] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        return self.query(sql, params, limit).rows

    def one(self, sql: str, params: list[Any] | None = None) -> dict[str, Any] | None:
        rows = self.query(sql, params, limit=1).rows
        return rows[0] if rows else None

    def build_info(self) -> dict[str, str]:
        try:
            return {r["key"]: r["value"] for r in self.rows("SELECT key, value FROM _build_info", limit=100)}
        except QueryError:
            return {}
