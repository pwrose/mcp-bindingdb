"""Add a compound_property table to a BindingDB DuckDB file: properties, scaffolds and structural alerts
computed by RDKit from each compound's SMILES (mcp_bindingdb.properties); scripts/compute_properties.py runs
update().

Everything is computed for the largest fragment (the parent, without salts and solvents), so mw can differ
from compound.mol_weight, which is BindingDB's weight of the whole record:

  heavy_atoms, mw, clogp (Crippen), tpsa, hbd / hba (Lipinski: NH+OH and N+O counts), rotatable_bonds,
  rings, aromatic_rings, fsp3, qed, ro5_violations (MW > 500, cLogP > 5, HBD > 5, HBA > 10)
  scaffold          Bemis-Murcko scaffold (ring systems and their linkers) as canonical SMILES; NULL for
                    compounds without a ring
  generic_scaffold  the scaffold with every atom a carbon and every bond single (its graph framework)
  pains, brenk, nih names of the structural alerts that match, per RDKit filter catalog (empty if none)

Compounds whose SMILES RDKit cannot parse have no row. The table only references compound by monomerid,
so it survives a rerun of derived.add().
"""

import json
import tempfile
from multiprocessing import Pool
from pathlib import Path
from typing import Callable

import duckdb
import rdkit

from mcp_bindingdb.properties import COLUMNS, compute

BATCH = 5000


def _batch(rows: list[tuple[int, str]]) -> str:
    """The batch's properties as JSON lines, one object per compound RDKit can parse. Workers serialize
    them so the parent only streams text to a file that DuckDB loads in parallel; passing the values as
    query parameters converts them one by one in the parent, which takes longer than computing them."""
    names = [name for name, _ in COLUMNS]
    return "".join(json.dumps(dict(zip(names, (monomerid, *p)))) + "\n"
                   for monomerid, smiles in rows if (p := compute(smiles)) is not None)


def update(path: Path, workers: int | None = None,
           progress: Callable[[int, int], None] | None = None) -> dict[str, int]:
    """Compute the properties and write them to the file's compound_property table; `progress(done, total)` is
    called after each batch of compounds."""
    con = duckdb.connect(str(path))
    rows = con.execute(
        "SELECT monomerid, smiles FROM compound WHERE smiles IS NOT NULL AND trim(smiles) <> '' ORDER BY monomerid"
    ).fetchall()
    batches = [rows[i:i + BATCH] for i in range(0, len(rows), BATCH)]
    with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
        lines = Path(tmp) / "compound_property.jsonl"
        with open(lines, "w", encoding="utf-8") as f, Pool(workers) as pool:
            for k, out in enumerate(pool.imap(_batch, batches), start=1):  # imap keeps batch order
                f.write(out)
                if progress:
                    progress(min(k * BATCH, len(rows)), len(rows))
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
