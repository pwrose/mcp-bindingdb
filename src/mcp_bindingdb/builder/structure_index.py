"""Build the RDKit substructure index for a BindingDB DuckDB file (scripts/build_substructure_index.py runs
build()).

Writes bindingdb_<release>.sslib next to the DuckDB file (or to `out`). Every compound with a
SMILES that RDKit can parse is indexed: its canonical SMILES (searched with a trusted-SMILES holder),
a pattern fingerprint for substructure screening, and a Morgan fingerprint of its largest fragment for
similarity search. Compounds are ordered by number of measurements, most
first, so a search that stops at its result limit returns the best-characterized compounds.
"""

from multiprocessing import Pool
from pathlib import Path
from typing import Callable

import duckdb
import numpy as np
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdSubstructLibrary

from mcp_bindingdb.substructure import index_path, morgan_fingerprint, write_index

BATCH = 5000


def _prepare(rows: list[tuple[int, str]]) -> list[tuple[int, str, bytes, bytes] | None]:
    """Canonical SMILES, pattern and Morgan fingerprints per compound; None where the SMILES does not parse."""
    RDLogger.DisableLog("rdApp.*")
    fps = rdSubstructLibrary.PatternHolder()
    out = []
    for monomerid, smiles in rows:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            out.append(None)
        else:
            fp = DataStructs.BitVectToBinaryText(fps.MakeFingerprint(mol))  # raw bits, 256 bytes
            out.append((monomerid, Chem.MolToSmiles(mol), fp, morgan_fingerprint(mol)))
    return out


def build(database: Path, out: Path | None = None, workers: int | None = None,
          progress: Callable[[int, int], None] | None = None) -> dict[str, object]:
    """Write the index of `database` to `out` (default: next to it, .sslib); `progress(done, total)` is called
    after each batch of compounds. Returns the path, counts and an example unparseable compound."""
    out = out or index_path(database)
    con = duckdb.connect(str(database), read_only=True)
    release = con.execute("SELECT value FROM _build_info WHERE key = 'release'").fetchone()
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' "
        "ORDER BY n_activities DESC, monomerid"
    ).fetchall()
    con.close()

    ids: list[int] = []
    smiles_out: list[str] = []
    fps: list[bytes] = []
    morgan: list[bytes] = []
    failed: list[int] = []
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    with Pool(workers) as pool:
        for k, (batch, prepared) in enumerate(zip(batches, pool.imap(_prepare, batches)), start=1):  # in order
            for (monomerid, _), item in zip(batch, prepared):
                if item is None:
                    failed.append(monomerid)
                    continue
                _, smiles, fp, mfp = item
                ids.append(monomerid)
                smiles_out.append(smiles)
                fps.append(fp)
                morgan.append(mfp)
            if progress:
                progress(min(k * BATCH, len(rows)), len(rows))
    fp_array = np.frombuffer(b"".join(fps), dtype=np.uint8).reshape(len(fps), -1)
    morgan_array = np.frombuffer(b"".join(morgan), dtype=np.uint8).reshape(len(morgan), -1)

    building = out.with_name(out.name + ".building")
    meta = {"release": release[0] if release else None, "database": database.name,
            "n_compounds": len(ids), "n_unparseable": len(failed)}
    write_index(building, meta, np.asarray(ids, dtype=np.int64), smiles_out, fp_array, morgan_array)
    building.replace(out)
    return {"path": out, "compounds": len(rows), "indexed": len(ids), "unparseable": len(failed),
            "example_unparseable": failed[0] if failed else None}
