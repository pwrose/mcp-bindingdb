"""Compound properties, Bemis-Murcko scaffolds and structural alerts, computed by RDKit.

scripts/compute_properties.py stores them per compound in the compound_property table; the server uses
murcko_scaffold to match a query molecule's scaffold against that table. Everything is computed for the
largest fragment (the parent, without salts and solvents). RDKit is optional (the `substructure` extra).
"""

from __future__ import annotations

import functools
from typing import Any

try:
    from rdkit import Chem, rdBase
    from rdkit.Chem import QED, Crippen, Descriptors
    from rdkit.Chem import rdMolDescriptors as D
    from rdkit.Chem.FilterCatalog import FilterCatalog, FilterCatalogParams
    from rdkit.Chem.MolStandardize import rdMolStandardize
    from rdkit.Chem.Scaffolds import MurckoScaffold
except ImportError:  # the `substructure` extra is not installed
    Chem = None

COLUMNS = [  # compound_property columns: name, DuckDB type
    ("monomerid", "INTEGER"), ("heavy_atoms", "INTEGER"), ("mw", "DOUBLE"), ("clogp", "DOUBLE"),
    ("tpsa", "DOUBLE"), ("hbd", "INTEGER"), ("hba", "INTEGER"), ("rotatable_bonds", "INTEGER"),
    ("rings", "INTEGER"), ("aromatic_rings", "INTEGER"), ("fsp3", "DOUBLE"), ("qed", "DOUBLE"),
    ("ro5_violations", "INTEGER"), ("scaffold", "VARCHAR"), ("generic_scaffold", "VARCHAR"),
    ("pains", "VARCHAR[]"), ("brenk", "VARCHAR[]"), ("nih", "VARCHAR[]"),
]
ALERT_CATALOGS = ["pains", "brenk", "nih"]  # RDKit FilterCatalogs, in COLUMNS order

# Ligand efficiency in kcal/mol per heavy atom (2.303 RT at 298 K = 1.37 kcal/mol per log unit) and
# lipophilic efficiency, as SQL over activity joined with compound_property AS cp.
LIGAND_EFFICIENCY_SQL = "1.37 * p_affinity / nullif(cp.heavy_atoms, 0)"
LIPE_SQL = "p_affinity - cp.clogp"


@functools.cache
def _tools() -> tuple[Any, list[Any]]:
    catalogs = []
    for name in ALERT_CATALOGS:
        params = FilterCatalogParams()
        params.AddCatalog(getattr(FilterCatalogParams.FilterCatalogs, name.upper()))
        catalogs.append(FilterCatalog(params))
    return rdMolStandardize.LargestFragmentChooser(), catalogs


def parent(smiles: str) -> Any:
    """The largest fragment of a SMILES as an RDKit molecule, or None if RDKit cannot parse it."""
    _quiet = rdBase.BlockLogs()  # LargestFragmentChooser logs every call
    mol = Chem.MolFromSmiles(smiles)
    return _tools()[0].choose(mol) if mol is not None and mol.GetNumAtoms() else None


def _scaffold(mol: Any) -> Any:
    """The Bemis-Murcko scaffold (ring systems and the linkers between them) of a parent; None without rings."""
    return MurckoScaffold.GetScaffoldForMol(mol) if D.CalcNumRings(mol) else None


def murcko_scaffold(smiles: str) -> str | None:
    """Canonical SMILES of a molecule's Bemis-Murcko scaffold, as stored in compound_property.scaffold;
    None if RDKit cannot parse the SMILES or the molecule has no ring. A scaffold is its own scaffold."""
    mol = parent(smiles)
    core = _scaffold(mol) if mol is not None else None
    return Chem.MolToSmiles(core) if core is not None else None


def compute(smiles: str) -> tuple[Any, ...] | None:
    """The COLUMNS after monomerid for one SMILES, or None if RDKit cannot parse it."""
    _quiet = rdBase.BlockLogs()  # e.g. the valence errors of generic scaffolds that cannot be made
    mol = parent(smiles)
    if mol is None:
        return None
    mw, clogp = Descriptors.MolWt(mol), Crippen.MolLogP(mol)
    hbd, hba = D.CalcNumLipinskiHBD(mol), D.CalcNumLipinskiHBA(mol)
    try:
        qed = round(QED.qed(mol), 3)
    except (ValueError, RuntimeError):
        qed = None
    scaffold = generic = None
    if (core := _scaffold(mol)) is not None:
        scaffold = Chem.MolToSmiles(core)
        try:
            generic = Chem.MolToSmiles(MurckoScaffold.MakeScaffoldGeneric(core))
        except (ValueError, RuntimeError):  # e.g. a sulfone S becomes a carbon with valence 6
            pass
    alerts = [sorted({m.GetDescription() for m in c.GetMatches(mol)}) for c in _tools()[1]]
    return (mol.GetNumHeavyAtoms(), round(mw, 2), round(clogp, 2) + 0.0, round(D.CalcTPSA(mol), 2), hbd, hba,
            D.CalcNumRotatableBonds(mol), D.CalcNumRings(mol), D.CalcNumAromaticRings(mol),
            round(D.CalcFractionCSP3(mol), 3), qed, (mw > 500) + (clogp > 5) + (hbd > 5) + (hba > 10),
            scaffold, generic, *alerts)
