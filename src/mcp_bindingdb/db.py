"""Read-only, sandboxed access to the BindingDB DuckDB file."""

from __future__ import annotations

import datetime as dt
import decimal
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import duckdb

DEFAULT_TIMEOUT_S = 30.0
MAX_CELL_CHARS = 2000  # long text cells (sequences, abstracts, raw ITC data) are truncated


class QueryError(Exception):
    """A query failed in a way the caller (the model) should see and can fix."""


def find_database() -> Path:
    """Resolve the DuckDB file: $BINDINGDB_DUCKDB, else the newest data/bindingdb_*.duckdb that has its structure
    index (a newer one may still be being built), else the newest data/bindingdb_*.duckdb."""
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
    indexed = [c for c in candidates if c.with_suffix(".sslib").is_file()]
    return (indexed or candidates)[-1]


def order_warning(keys: list[str] | None, rows: list[dict[str, Any]]) -> str | None:
    """Why the rows' order may change from run to run: no ORDER BY, or two rows that tie on every ORDER BY
    column (e.g. a GROUP BY's groups come out in whatever order its threads finish). None if it holds."""
    if keys is None or len(rows) < 2:
        return None
    fix = ("with a unique column (e.g. monomerid; ki_result_id, affinity_type for measurements) so the result "
           "is the same on every run and a notebook's rerun check passes.")
    if not keys:
        return (f"The query has no ORDER BY, so its {len(rows)} rows can come back in a different order. Add an "
                f"ORDER BY that ends {fix}")
    if any(k not in rows[0] for k in keys):
        return None
    for k, (a, b) in enumerate(zip(rows, rows[1:]), start=1):
        if all(a[c] == b[c] for c in keys) and a != b:
            return (f"Rows {k} and {k + 1} tie on every ORDER BY column ({', '.join(keys)}), so rows like them "
                    f"can swap places from run to run. End the ORDER BY {fix}")
    return None


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

    def __init__(self, path: Path, timeout_s: float = DEFAULT_TIMEOUT_S, memory_limit: str = "4GB",
                 ready: Callable[[], None] | None = None, build_info: dict[str, str] | None = None):
        """`ready`, for a file that is still being built (local_build.LocalBuild.require), is called before the
        connection is opened, on first use, and raises until the file is there; without it the connection is
        opened now. `build_info` stands in for the file's _build_info table until then."""
        self.path = path
        self.timeout_s = timeout_s
        self._ready = ready
        self._build_info = build_info
        self._config = {
            # No file, network, or extension access from SQL; settings cannot be changed back.
            "enable_external_access": False,
            "autoinstall_known_extensions": False,
            "autoload_known_extensions": False,
            "memory_limit": memory_limit,
            "lock_configuration": True,
        }
        self._connection: duckdb.DuckDBPyConnection | None = None
        self._connect_lock = threading.Lock()
        if ready is None:
            self._connect()

    def _connect(self) -> duckdb.DuckDBPyConnection:
        if self._connection is None:
            if self._ready is not None:
                self._ready()
            with self._connect_lock:
                if self._connection is None:
                    self._connection = duckdb.connect(str(self.path), read_only=True, config=self._config)
                    if self._build_info is not None:  # now the file's own, in the dict callers already hold
                        actual = self._read_build_info()
                        self._build_info.clear()
                        self._build_info.update(actual)
        return self._connection

    @property
    def _con(self) -> duckdb.DuckDBPyConnection:
        return self._connect()

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

    def order_keys(self, sql: str) -> list[str] | None:
        """The output columns a query's outer ORDER BY sorts on, from DuckDB's parse of it: [] when it has no
        ORDER BY; None when that cannot be told (not one SELECT, ORDER BY ALL, or a sort on an expression)."""
        try:
            parsed = json.loads(self._con.execute("SELECT json_serialize_sql(?)", [sql]).fetchone()[0])
        except (duckdb.Error, TypeError, ValueError):
            return None
        statements = parsed.get("statements") or []
        if parsed.get("error") or len(statements) != 1:
            return None
        node = statements[0].get("node") or {}
        if (node.get("from_table") or {}).get("type") == "SHOW_REF":  # DESCRIBE, SHOW, SUMMARIZE: fixed order
            return None
        orders = [o for m in node.get("modifiers") or [] if m.get("type") == "ORDER_MODIFIER" for o in m["orders"]]
        names = {tuple(e["column_names"]): e.get("alias") or e["column_names"][-1]
                 for e in node.get("select_list") or [] if e.get("class") == "COLUMN_REF"}
        aliases = [e.get("alias") or (e["column_names"][-1] if e.get("class") == "COLUMN_REF" else None)
                   for e in node.get("select_list") or []]
        keys = []
        for order in orders:
            expr = order.get("expression") or {}
            if expr.get("class") == "COLUMN_REF":
                keys.append(names.get(tuple(expr["column_names"]), expr["column_names"][-1]))
            elif expr.get("class") == "CONSTANT" and isinstance(v := (expr.get("value") or {}).get("value"), int) \
                    and 1 <= v <= len(aliases) and aliases[v - 1]:
                keys.append(aliases[v - 1])
            else:
                return None
        return keys

    def build_info(self) -> dict[str, str]:
        """The file's _build_info table; before a pending file is opened, the `build_info` given (the same dict,
        filled in from the file once it is opened)."""
        if self._build_info is not None:
            return self._build_info
        return self._read_build_info()

    def _read_build_info(self) -> dict[str, str]:
        try:
            return {r["key"]: r["value"] for r in self.rows("SELECT key, value FROM _build_info", limit=100)}
        except QueryError:
            return {}
