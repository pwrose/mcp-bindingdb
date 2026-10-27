"""Add a compound_property table to a BindingDB DuckDB file: properties, scaffolds and structural alerts
computed by RDKit from each compound's SMILES (mcp_bindingdb.properties).

    uv run --extra substructure python scripts/compute_properties.py data/bindingdb_202610.duckdb

Everything is computed for the largest fragment (the parent, without salts and solvents), so mw can differ
from compound.mol_weight, which is BindingDB's weight of the whole record:

  heavy_atoms, mw, clogp (Crippen), tpsa, hbd / hba (Lipinski: NH+OH and N+O counts), rotatable_bonds,
  rings, aromatic_rings, fsp3, qed, ro5_violations (MW > 500, cLogP > 5, HBD > 5, HBA > 10)
  scaffold          Bemis-Murcko scaffold (ring systems and their linkers) as canonical SMILES; NULL for
                    compounds without a ring
  generic_scaffold  the scaffold with every atom a carbon and every bond single (its graph framework)
  pains, brenk, nih names of the structural alerts that match, per RDKit filter catalog (empty if none)

Compounds whose SMILES RDKit cannot parse have no row. The table only references compound by monomerid,
so it survives a rerun of add_derived_tables.py. By default the file is updated on a copy that then
replaces it, so a running MCP server (which holds a read lock) keeps working and picks up the table on
restart; --in-place updates the file directly (the build script uses it on the file it is building).
"""

import argparse
import json
import shutil
import sys
import tempfile
import time
from multiprocessing import Pool
from pathlib import Path

import duckdb
import rdkit

from mcp_bindingdb.properties import COLUMNS, compute

BATCH = 5000
PROGRESS_EVERY = 10  # batches between progress lines


def _batch(rows: list[tuple[int, str]]) -> str:
    """The batch's properties as JSON lines, one object per compound RDKit can parse. Workers serialize
    them so the parent only streams text to a file that DuckDB loads in parallel; passing the values as
    query parameters converts them one by one in the parent, which takes longer than computing them."""
    names = [name for name, _ in COLUMNS]
    return "".join(json.dumps(dict(zip(names, (monomerid, *p)))) + "\n"
                   for monomerid, smiles in rows if (p := compute(smiles)) is not None)


def update(path: Path, workers: int | None = None) -> dict[str, int]:
    """Compute the properties and write them to the file's compound_property table."""
    con = duckdb.connect(str(path))
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' ORDER BY monomerid"
    ).fetchall()
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    t0 = time.time()
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        lines = Path(tmp) / "compound_property.jsonl"
        with open(lines, "w", encoding="utf-8") as f, Pool(workers) as pool:
            for k, out in enumerate(pool.imap(_batch, batches), start=1):  # imap keeps batch order
                f.write(out)
                if k % PROGRESS_EVERY == 0 and k < len(batches):
                    done, elapsed = k * BATCH, time.time() - t0
                    print(f"  {done:,} of {len(rows):,} compounds ({done / len(rows):.0%}) in "
                          f"{elapsed / 60:.1f} min, about {elapsed * (len(rows) / done - 1) / 60:.0f} min left",
                          flush=True)
        types = ", ".join(f"'{name}': '{t}'" for name, t in COLUMNS)
        con.execute(f"""CREATE OR REPLACE TABLE compound_property AS
                        SELECT * FROM read_json(?, format = 'newline_delimited', columns = {{{types}}})
                        ORDER BY monomerid""", [str(lines)])
    stats = con.execute(
        """SELECT count(*), count(scaffold), count(DISTINCT scaffold),
                  count(*) FILTER (WHERE len(pains) > 0), count(*) FILTER (WHERE len(brenk) > 0),
                  count(*) FILTER (WHERE len(nih) > 0)
           FROM compound_property"""
    ).fetchone()
    con.execute("DELETE FROM _build_info WHERE key = 'properties'")
    con.execute("INSERT INTO _build_info VALUES ('properties', ?)",
                [f"compound_property computed from SMILES (largest fragment) by RDKit {rdkit.__version__}"])
    con.execute("CHECKPOINT")
    con.close()
    return {"compounds": len(rows), **dict(zip(["computed", "with_scaffold", "scaffolds", "pains", "brenk", "nih"],
                                                 stats))}


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
    stats = update(target, args.workers)
    if not args.in_place:
        target.replace(args.database)
    print(f"  {stats['computed']:,} of {stats['compounds']:,} compounds have properties; "
          f"{stats['with_scaffold']:,} have a scaffold ({stats['scaffolds']:,} distinct)")
    print(f"  structural alerts: PAINS {stats['pains']:,}, Brenk {stats['brenk']:,}, NIH {stats['nih']:,} compounds")
    print(f"Properties computed in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
