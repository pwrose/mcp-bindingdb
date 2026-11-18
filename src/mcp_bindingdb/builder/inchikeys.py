"""Replace the InChIKeys in a BindingDB DuckDB file's derived tables with standard InChIKeys computed by RDKit
(scripts/compute_inchikeys.py runs update()).

BindingDB stores no InChIKey for about 31% of its compounds, and many stored keys are non-standard
(ending -NA-N instead of -SA-N) or encode stereo differently, so they do not match the standard keys
PubChem, OPSIN and RDKit produce. This computes the standard key from each compound's SMILES and writes
it to compound.inchi_key and activity.inchi_key. Where RDKit cannot make a key, the BindingDB key (if
any) is kept; monomer.inchi_key keeps BindingDB's keys unchanged.

Rerun it after derived.add(), which rebuilds these tables from BindingDB's keys.
"""

from multiprocessing import Pool
from pathlib import Path
from typing import Callable

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


def update(path: Path, workers: int | None = None,
           progress: Callable[[int, int], None] | None = None) -> dict[str, int]:
    """Compute the keys and write them into the file's compound and activity tables; `progress(done, total)`
    is called after each batch of compounds."""
    con = duckdb.connect(str(path))
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' ORDER BY monomerid"
    ).fetchall()
    ids: list[int] = []
    keys: list[str] = []
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    with Pool(workers) as pool:
        for k, (batch, computed) in enumerate(zip(batches, pool.imap(_keys, batches)), start=1):  # in order
            for (monomerid, _), key in zip(batch, computed):
                if key:
                    ids.append(monomerid)
                    keys.append(key)
            if progress:
                progress(min(k * BATCH, len(rows)), len(rows))
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
