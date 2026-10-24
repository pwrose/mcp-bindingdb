"""Replace the InChIKeys in a BindingDB DuckDB file's derived tables with standard InChIKeys computed by RDKit.

    uv run --extra substructure python scripts/compute_inchikeys.py data/bindingdb_202610.duckdb

BindingDB stores no InChIKey for about 31% of its compounds, and many stored keys are non-standard
(ending -NA-N instead of -SA-N) or encode stereo differently, so they do not match the standard keys
PubChem, OPSIN and RDKit produce. This computes the standard key from each compound's SMILES and writes
it to compound.inchi_key and activity.inchi_key. Where RDKit cannot make a key, the BindingDB key (if
any) is kept; monomer.inchi_key keeps BindingDB's keys unchanged.

By default the file is updated on a copy that then replaces it, so a running MCP server (which holds a
read lock) keeps working and picks up the new keys on restart. --in-place updates the file directly (the
build script uses it on the file it is building). Rerun it after add_derived_tables.py, which rebuilds
these tables from BindingDB's keys.
"""

import argparse
import shutil
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import duckdb
import rdkit
from rdkit import Chem, RDLogger

BATCH = 5000


def _keys(rows: list[tuple[int, str]]) -> list[str | None]:
    """Standard InChIKey per compound; None where RDKit cannot parse the SMILES or InChI fails."""
    RDLogger.DisableLog("rdApp.*")
    out = []
    for _, smiles in rows:
        mol = Chem.MolFromSmiles(smiles)
        out.append((Chem.MolToInchiKey(mol) or None) if mol is not None else None)
    return out


def update(path: Path, workers: int | None = None) -> dict[str, int]:
    """Compute the keys and write them into the file's compound and activity tables."""
    con = duckdb.connect(str(path))
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' ORDER BY monomerid"
    ).fetchall()
    ids: list[int] = []
    keys: list[str] = []
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    with Pool(workers) as pool:
        for batch, computed in zip(batches, pool.imap(_keys, batches)):  # imap keeps batch order
            for (monomerid, _), key in zip(batch, computed):
                if key:
                    ids.append(monomerid)
                    keys.append(key)
    con.execute("CREATE OR REPLACE TEMP TABLE computed AS SELECT unnest(?) AS monomerid, unnest(?) AS inchi_key",
                [ids, keys])
    stats = con.execute(
        """SELECT count(*) AS compounds,
                  count(k.inchi_key) AS computed,
                  count(*) FILTER (WHERE k.inchi_key IS NOT NULL AND (c.inchi_key IS NULL OR c.inchi_key = '')) AS added,
                  count(*) FILTER (WHERE k.inchi_key <> c.inchi_key) AS changed,
                  count(*) FILTER (WHERE k.inchi_key IS NULL AND c.inchi_key IS NOT NULL AND c.inchi_key <> '') AS kept,
                  count(*) FILTER (WHERE k.inchi_key IS NULL AND (c.inchi_key IS NULL OR c.inchi_key = '')) AS without_key
           FROM compound c LEFT JOIN computed k USING (monomerid)"""
    ).fetchone()
    con.execute("UPDATE compound SET inchi_key = k.inchi_key FROM computed k WHERE compound.monomerid = k.monomerid")
    con.execute("UPDATE activity SET inchi_key = k.inchi_key FROM computed k WHERE activity.monomerid = k.monomerid")
    con.execute("DELETE FROM _build_info WHERE key = 'inchi_keys'")
    con.execute("INSERT INTO _build_info VALUES ('inchi_keys', ?)",
                [f"standard InChIKeys computed from SMILES by RDKit {rdkit.__version__}"])
    con.execute("CHECKPOINT")
    con.close()
    return dict(zip(["compounds", "computed", "added", "changed", "kept", "without_key"], stats))


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
