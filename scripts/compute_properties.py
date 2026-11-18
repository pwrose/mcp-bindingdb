"""Add a compound_property table to a BindingDB DuckDB file: RDKit properties, scaffolds and structural alerts
of each compound's parent; see mcp_bindingdb.builder.compound_properties.

    uv run --extra substructure python scripts/compute_properties.py data/bindingdb_202610.duckdb

By default the file is updated on a copy that then replaces it, so a running MCP server (which holds a
read lock) keeps working and picks up the table on restart; --in-place updates the file directly.
"""

import argparse
import shutil
import sys
import time
from pathlib import Path

from mcp_bindingdb.builder.compound_properties import update


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    p.add_argument("--in-place", action="store_true", help="Update the file directly instead of via a copy")
    p.add_argument("--workers", type=int, default=None, help="Worker processes (default: all CPUs)")
    args = p.parse_args()

    t0 = time.time()
    target = args.database
    if not args.in_place:
        target = args.database.with_name(args.database.name + ".properties")
        shutil.copyfile(args.database, target)
    last = [0.0]

    def progress(done: int, total: int) -> None:
        if time.time() - last[0] >= 30 and done < total:
            last[0] = time.time()
            elapsed = time.time() - t0
            print(f"  {done:,} of {total:,} compounds ({done / total:.0%}) in {elapsed / 60:.1f} min, "
                  f"about {elapsed * (total / done - 1) / 60:.0f} min left", flush=True)

    stats = update(target, args.workers, progress)
    if not args.in_place:
        target.replace(args.database)
    print(f"  {stats['computed']:,} of {stats['compounds']:,} compounds have properties; "
          f"{stats['with_scaffold']:,} have a scaffold ({stats['scaffolds']:,} distinct)")
    print(f"  structural alerts: PAINS {stats['pains']:,}, Brenk {stats['brenk']:,}, NIH {stats['nih']:,} compounds")
    print(f"Properties computed in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
