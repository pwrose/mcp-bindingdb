"""Build the RDKit substructure index for a BindingDB DuckDB file.

    uv run --extra substructure python scripts/build_substructure_index.py data/bindingdb_202610.duckdb

Writes data/bindingdb_<release>.sslib next to the DuckDB file (or --output). Every compound with a
SMILES that RDKit can parse is indexed: its canonical SMILES (searched with a trusted-SMILES holder)
and a pattern fingerprint for screening. Compounds are ordered by number of measurements, most
first, so a search that stops at its result limit returns the best-characterized compounds.
"""

import argparse
import sys
import time
from multiprocessing import Pool
from pathlib import Path

import duckdb
import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdSubstructLibrary

from mcp_bindingdb.substructure import index_path, write_index

BATCH = 5000


def _prepare(rows: list[tuple[int, str]]) -> list[tuple[int, str, bytes] | None]:
    """Canonical SMILES and pattern fingerprint per compound; None where the SMILES does not parse."""
    RDLogger.DisableLog("rdApp.*")
    fps = rdSubstructLibrary.PatternHolder()
    out = []
    for monomerid, smiles in rows:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            out.append(None)
        else:
            fp = DataStructs.BitVectToBinaryText(fps.MakeFingerprint(mol))  # raw bits, 256 bytes
            out.append((monomerid, Chem.MolToSmiles(mol), fp))
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    p.add_argument("--output", type=Path, help="Index file (default: the database path with .sslib)")
    p.add_argument("--workers", type=int, default=None, help="Worker processes (default: all CPUs)")
    args = p.parse_args()
    out = args.output or index_path(args.database)

    t0 = time.time()
    con = duckdb.connect(str(args.database), read_only=True)
    release = con.execute("SELECT value FROM _build_info WHERE key = 'release'").fetchone()
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' "
        "ORDER BY n_activities DESC, monomerid"
    ).fetchall()
    con.close()
    print(f"  {len(rows):,} compounds with SMILES")

    ids: list[int] = []
    smiles_out: list[str] = []
    fps: list[bytes] = []
    failed: list[int] = []
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    with Pool(args.workers) as pool:
        for batch, prepared in zip(batches, pool.imap(_prepare, batches)):  # imap keeps batch order
            for (monomerid, _), item in zip(batch, prepared):
                if item is None:
                    failed.append(monomerid)
                    continue
                _, smiles, fp = item
                ids.append(monomerid)
                smiles_out.append(smiles)
                fps.append(fp)
    fp_array = np.frombuffer(b"".join(fps), dtype=np.uint8).reshape(len(fps), -1)

    building = out.with_name(out.name + ".building")
    meta = {"release": release[0] if release else None, "database": args.database.name,
            "n_compounds": len(ids), "n_unparseable": len(failed)}
    write_index(building, meta, np.asarray(ids, dtype=np.int64), smiles_out, fp_array)
    building.replace(out)
    print(f"  {len(ids):,} indexed, {len(failed):,} SMILES RDKit could not parse"
          + (f" (e.g. BDBM{failed[0]})" if failed else ""))
    print(f"Substructure index {out} ({out.stat().st_size / 1e6:.0f} MB) built in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
