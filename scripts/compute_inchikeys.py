"""Replace the InChIKeys in a BindingDB DuckDB file's derived tables with standard InChIKeys computed by RDKit;
see mcp_bindingdb.builder.inchikeys.

    uv run --extra substructure python scripts/compute_inchikeys.py data/bindingdb_202610.duckdb

By default the file is updated on a copy that then replaces it, so a running MCP server (which holds a
read lock) keeps working and picks up the new keys on restart. --in-place updates the file directly.
Rerun it after add_derived_tables.py, which rebuilds these tables from BindingDB's keys.
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

from mcp_bindingdb.builder.inchikeys import update


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    p.add_argument("--in-place", action="store_true", help="Update the file directly instead of via a copy")
    p.add_argument("--workers", type=int, default=None, help="Worker processes (default: all CPUs)")
    args = p.parse_args()

    t0 = time.time()
    target = args.database
    if not args.in_place:
        target = args.database.with_name(args.database.name + ".inchikeys")
        shutil.copyfile(args.database, target)
    stats = update(target, args.workers)
    if not args.in_place:
        target.replace(args.database)
    print(f"  {stats['computed']:,} of {stats['compounds']:,} compounds have a computed key: "
          f"{stats['added']:,} added, {stats['changed']:,} changed")
    print(f"  {stats['kept']:,} BindingDB keys kept where RDKit could not make one; "
          f"{stats['without_key']:,} compounds without a key")
    print(f"InChIKeys computed in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
