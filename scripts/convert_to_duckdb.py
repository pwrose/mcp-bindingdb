"""Copy a BindingDB MySQL database into a DuckDB file and validate row counts.

Expects a running MySQL with the BindingDB dump loaded (see build_duckdb.sh).
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import duckdb

# Tables holding passwords or personal contact details; excluded unless --include-pii.
PII_TABLES = {"regusers", "person"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release", required=True, help="BindingDB release, e.g. 202610")
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--zip", type=Path, help="source zip, recorded in _build_info")
    p.add_argument("--source-url", default="")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=3307)
    p.add_argument("--user", default="root")
    p.add_argument("--database", default="bindingdb")
    p.add_argument("--include-pii", action="store_true")
    args = p.parse_args()

    tmp = args.output.with_name(args.output.name + ".tmp")
    tmp.unlink(missing_ok=True)
    started = time.time()

    con = duckdb.connect(str(tmp))
    con.execute("INSTALL mysql; LOAD mysql;")
    con.execute(
        f"ATTACH 'host={args.host} port={args.port} user={args.user} database={args.database}' "
        "AS m (TYPE mysql, READ_ONLY)"
    )

    tables = [
        r[0]
        for r in con.execute(
            "SELECT table_name FROM duckdb_tables() "
            "WHERE database_name = 'm' AND schema_name = ? ORDER BY table_name",
            [args.database],
        ).fetchall()
    ]
    excluded = [] if args.include_pii else sorted(PII_TABLES & set(tables))
    tables = [t for t in tables if t not in excluded]
    print(f"Copying {len(tables)} tables (excluded: {excluded or 'none'})", flush=True)

    counts: dict[str, int] = {}
    mismatches = []
    for t in tables:
        t0 = time.time()
        con.execute(f'CREATE TABLE main."{t}" AS SELECT * FROM m.{args.database}."{t}"')
        n_duck = con.execute(f'SELECT COUNT(*) FROM main."{t}"').fetchone()[0]
        n_mysql = con.execute(
            f"SELECT * FROM mysql_query('m', 'SELECT COUNT(*) FROM `{t}`')"
        ).fetchone()[0]
        counts[t] = n_duck
        status = "ok" if n_duck == n_mysql else "MISMATCH"
        if n_duck != n_mysql:
            mismatches.append((t, n_mysql, n_duck))
        print(f"  {t:<22} {n_duck:>12,}  ({time.time() - t0:5.1f}s) {status}", flush=True)

    con.execute("DETACH m")

    info = {
        "release": args.release,
        "source_url": args.source_url,
        "source_zip": args.zip.name if args.zip else None,
        "source_zip_bytes": args.zip.stat().st_size if args.zip else None,
        "source_zip_sha256": sha256(args.zip) if args.zip else None,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duckdb_version": duckdb.__version__,
        "excluded_tables": json.dumps(excluded),
        "table_row_counts": json.dumps(counts),
    }
    con.execute(
        "CREATE TABLE _build_info AS SELECT * FROM (VALUES "
        + ", ".join("(?, ?)" for _ in info)
        + ") AS t(key, value)",
        [x for kv in info.items() for x in (kv[0], None if kv[1] is None else str(kv[1]))],
    )
    con.execute("CHECKPOINT")
    con.close()

    if mismatches:
        for t, a, b in mismatches:
            print(f"ERROR: {t}: mysql={a} duckdb={b}", file=sys.stderr)
        print(f"Left unvalidated output at {tmp}", file=sys.stderr)
        return 1

    tmp.replace(args.output)
    size_gb = args.output.stat().st_size / 1e9
    print(f"Wrote {args.output} ({size_gb:.2f} GB) in {time.time() - started:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
