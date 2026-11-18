"""Add query-friendly derived tables (activity, compound, compound_name, target, target_name) to a BindingDB
DuckDB file; see mcp_bindingdb.builder.derived.

    uv run python scripts/add_derived_tables.py data/bindingdb_202610.duckdb
"""

import argparse
import sys
import time
from pathlib import Path

import duckdb

from mcp_bindingdb.builder.derived import TABLES, add


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    args = p.parse_args()

    t0 = time.time()
    con = duckdb.connect(str(args.database))
    counts = add(con)
    for t in TABLES:
        print(f"  {t:<14} {counts[t]:>12,}")
    print(f"  activity rows with unparseable value: {counts['unparsed']}")
    con.execute("CHECKPOINT")
    con.close()
    print(f"Derived tables built in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
