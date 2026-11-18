"""Build the RDKit substructure and similarity index for a BindingDB DuckDB file; see
mcp_bindingdb.builder.structure_index.

    uv run --extra substructure python scripts/build_substructure_index.py data/bindingdb_202610.duckdb

Writes data/bindingdb_<release>.sslib next to the DuckDB file (or --output).
"""

import argparse
import sys
import time
from pathlib import Path

from mcp_bindingdb.builder.structure_index import build


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    p.add_argument("--output", type=Path, help="Index file (default: the database path with .sslib)")
    p.add_argument("--workers", type=int, default=None, help="Worker processes (default: all CPUs)")
    args = p.parse_args()

    t0 = time.time()
    r = build(args.database, args.output, args.workers)
    print(f"  {r['indexed']:,} of {r['compounds']:,} compounds with SMILES indexed, {r['unparseable']:,} SMILES "
          "RDKit could not parse" + (f" (e.g. BDBM{r['example_unparseable']})" if r["example_unparseable"] else ""))
    print(f"Substructure index {r['path']} ({r['path'].stat().st_size / 1e6:.0f} MB) built in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
