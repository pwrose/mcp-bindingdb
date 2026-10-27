"""Structure-activity relationships: R-group decomposition, matched molecular pairs, activity cliffs.

The server's SAR tools (decompose_r_groups, matched_molecular_pairs, activity_cliffs) pair these
algorithms with a target's measurements. Everything here works on SMILES and affinity values alone, so
it can be tested without a database. RDKit is optional (the `substructure` extra).
"""

from __future__ import annotations

import functools
import itertools
import re
from dataclasses import dataclass
from typing import Any

try:
    import numpy as np
    from rdkit import Chem, rdBase
    from rdkit.Chem import rdMMPA
    from rdkit.Chem import rdRGroupDecomposition as rgd
    from rdkit.Chem.MolStandardize import rdMolStandardize
except ImportError:  # the `substructure` extra is not installed
    Chem = None

MAX_CUT_BONDS = 300  # FragmentMol gives nothing for a molecule with more cuttable bonds than this
MAX_VARIABLE_ATOMS = 13  # a transformation is a change of a group, not of most of the molecule
MAX_PAIRS = 200_000  # pairs to consider before giving up; a note says the result is partial
SIMILARITY_BLOCK = 64  # rows per block of the pairwise Tanimoto comparison
HYDROGEN_GROUP = re.compile(r"\[H\]\[\*:\d+\]")  # how RDKit writes hydrogen at an R-group position


def available() -> bool:
    return Chem is not None


@functools.lru_cache(maxsize=200_000)  # fragments repeat heavily; the cache is capped for a long-lived server
def heavy_atoms(smiles: str) -> int:
    """Heavy atoms of a fragment SMILES; the attachment point ('[*:1]') does not count."""
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    return mol.GetNumHeavyAtoms() if mol is not None else 0


@functools.cache
def _largest_fragment() -> Any:
    return rdMolStandardize.LargestFragmentChooser()


def molecules(smiles_list: list[str]) -> list[Any]:
    """The parent (largest fragment) of each SMILES, None where RDKit cannot parse it.

    Taking the parent makes salts and solvates behave as the compound itself, as they already do for
    fingerprints and computed properties; it also keeps a counter-ion from looking like a substituent
    that a matched pair could swap.
    """
    _quiet = rdBase.BlockLogs()  # LargestFragmentChooser logs every call
    parents = []
    for smiles in smiles_list:
        mol = Chem.MolFromSmiles(smiles) if smiles else None
        parents.append(_largest_fragment().choose(mol) if mol is not None and mol.GetNumAtoms() else None)
    return parents


def has_attachment_points(core: Any) -> bool:
    """True if the core marks its R-group positions, e.g. '[*:1]c1ccccc1Nc1ncnc2ccccc12'."""
    return any(a.GetAtomicNum() == 0 and a.GetAtomMapNum() for a in core.GetAtoms())


@dataclass
class Decomposition:
    labels: list[str]  # the R-group positions that vary, 'R1', 'R2', ...
    rows: list[dict[str, str | None] | None]  # per molecule in the order given; None when the core missed
    core: str | None  # the core as RDKit labelled it, with its attachment points

    @property
    def n_matched(self) -> int:
        return sum(row is not None for row in self.rows)


def decompose(core: Any, mols: list[Any]) -> Decomposition:
    """R-group decomposition of `mols` against one core.

    A core that marks its attachment points is taken literally: molecules substituted anywhere else do
    not match. A position where every molecule carries hydrogen is dropped by RDKit, so the labels are
    the positions that actually vary.
    """
    params = rgd.RGroupDecompositionParameters()
    params.onlyMatchAtRGroups = has_attachment_points(core)
    params.removeHydrogensPostMatch = True
    _quiet = rdBase.BlockLogs()  # a core that matches nothing logs per molecule
    decomposition = rgd.RGroupDecomposition(core, params)
    matched = [mol is not None and decomposition.Add(mol) >= 0 for mol in mols]
    if not any(matched) or not decomposition.Process():
        return Decomposition([], [None] * len(mols), None)
    rows = iter(decomposition.GetRGroupsAsRows(asSmiles=True))
    labels = [label for label in decomposition.GetRGroupLabels() if label != "Core"]
    out: list[dict[str, str | None] | None] = []
    core_match = None
    for ok in matched:
        row = next(rows, None) if ok else None
        core_match = core_match or (row or {}).get("Core")
        out.append({label: substituent(row.get(label)) for label in labels} if row else None)
    used = [label for label in labels if any(row[label] is not None for row in out if row is not None)]
    if used != labels:  # a position no matching molecule substitutes would be a column of nulls
        out = [None if row is None else {label: row[label] for label in used} for row in out]
    return Decomposition(used, out, core_match)


def substituent(smiles: str | None) -> str | None:
    """A substituent for one cell of an SAR table: 'H' for hydrogen, None where the position is absent."""
    if not smiles:
        return None
    return "H" if HYDROGEN_GROUP.fullmatch(smiles) else smiles


@functools.lru_cache(maxsize=200_000)
def tidy_fragment(smiles: str) -> str:
    """A fragment SMILES to show: explicit hydrogens dropped, except a lone hydrogen substituent.

    Cutting hydrogen bonds is what makes an H -> F pair findable, but it writes every hydrogen out, so
    the fragments that come back are unreadable and would not group with the same group written plainly.
    '[H][*:1]' itself is kept: that is how a hydrogen substituent is written.
    """
    if HYDROGEN_GROUP.fullmatch(smiles):
        return smiles
    mol = Chem.MolFromSmiles(smiles, sanitize=False)
    if mol is None:
        return smiles
    return Chem.MolToSmiles(Chem.RemoveHs(mol, sanitize=False))


def single_cut_variants(mol: Any, max_variable_atoms: int = MAX_VARIABLE_ATOMS,
                        include_hydrogens: bool = False) -> list[tuple[str, str]]:
    """(constant, variable) fragment SMILES for each way of cutting one acyclic single bond.

    Both halves of a cut take a turn as the variable part, so a fragment can serve either as the context
    or as the group that changed. A cut is kept only when the variable half is no larger than
    max_variable_atoms and no larger than the constant half: a matched pair is a change of a substituent,
    not a swap of most of the molecule.

    include_hydrogens also cuts carbon-hydrogen bonds, which is the only way a pair that *adds* a group
    (H -> F) can be found. The fragments then carry explicit hydrogens, so every molecule compared must
    be fragmented the same way; tidy_fragment makes them readable again.
    """
    if include_hydrogens:
        mol = Chem.AddHs(mol)
    variants = []
    for _, chains in rdMMPA.FragmentMol(mol, maxCuts=1, maxCutBonds=MAX_CUT_BONDS, resultsAsMols=False):
        parts = chains.split(".")
        if len(parts) != 2:
            continue
        sizes = [heavy_atoms(p) for p in parts]
        for (constant, variable), (n_constant, n_variable) in ((parts, sizes), (parts[::-1], sizes[::-1])):
            if n_variable <= max_variable_atoms and n_variable <= n_constant:
                variants.append((constant, variable))
    return variants


def matched_pairs(variants: list[list[tuple[str, str]]],
                  max_pairs: int = MAX_PAIRS) -> tuple[dict[tuple[int, int], tuple[str, str, str]], bool]:
    """Molecules that differ by a single fragment, from their single_cut_variants.

    Returns {(i, j): (constant, variable of i, variable of j)} with i < j, and whether max_pairs was
    reached. A pair that shares several constant parts keeps the largest one: that is the most specific
    context, and it leaves the smallest change as the transformation.
    """
    by_constant: dict[str, list[tuple[int, str]]] = {}
    for i, molecule in enumerate(variants):
        for constant, variable in molecule:
            by_constant.setdefault(constant, []).append((i, variable))
    pairs: dict[tuple[int, int], tuple[int, str, str, str]] = {}
    for constant, members in by_constant.items():
        if len(members) < 2:
            continue
        size = heavy_atoms(constant)
        for (i, var_i), (j, var_j) in itertools.combinations(sorted(members), 2):
            if i == j or var_i == var_j:
                continue
            key = (i, j)
            known = pairs.get(key)
            if known is None and len(pairs) >= max_pairs:
                return {k: v[1:] for k, v in pairs.items()}, True
            if known is None or size > known[0]:
                pairs[key] = (size, constant, var_i, var_j)
    return {k: v[1:] for k, v in pairs.items()}, False


def similar_pairs(fingerprints: list[bytes], min_similarity: float,
                  max_pairs: int = MAX_PAIRS) -> tuple[list[tuple[int, int, float]], bool]:
    """(i, j, Tanimoto) for every pair of fingerprints at or above min_similarity, with i < j.

    Returns the pairs and whether max_pairs was reached. Compared in blocks of rows against all rows, so
    memory stays flat in the number of compounds.
    """
    if len(fingerprints) < 2:
        return [], False
    fps = np.frombuffer(b"".join(fingerprints), dtype=np.uint64).reshape(len(fingerprints), -1)
    bits = np.bitwise_count(fps).sum(axis=1, dtype=np.int32)
    found: list[tuple[int, int, float]] = []
    for start in range(0, len(fps), SIMILARITY_BLOCK):
        block = fps[start:start + SIMILARITY_BLOCK]
        common = np.bitwise_count(block[:, None, :] & fps[None, :, :]).sum(axis=2, dtype=np.int32)
        union = bits[start:start + len(block), None] + bits[None, :] - common
        similarity = np.divide(common, union, out=np.zeros(common.shape), where=union > 0)
        rows, cols = np.nonzero(similarity >= min_similarity)
        keep = (rows + start) < cols
        rows, cols = rows[keep], cols[keep]
        found += list(zip((rows + start).tolist(), cols.tolist(), similarity[rows, cols].round(3).tolist()))
        if len(found) >= max_pairs:
            return found[:max_pairs], True
    return found, False


def same_molecule(a: Any, b: Any) -> bool:
    """True if two molecules are the same structure, so a 'cliff' between them is two records of one
    compound with different reported values rather than a steep SAR."""
    return Chem.MolToSmiles(a) == Chem.MolToSmiles(b)


def fold_change(delta_p_affinity: float) -> float:
    """How many times the potency changed, from a difference in log units; below 1 it got weaker."""
    factor = 10 ** delta_p_affinity
    if factor >= 100:
        return round(factor)
    return round(factor, 1) if factor >= 1 else float(f"{factor:.2g}")


def sali(delta_p_affinity: float, similarity: float) -> float | None:
    """Structure-activity landscape index: potency difference per unit of structural distance.

    None for a pair whose fingerprints are identical (distance 0), where the index is undefined; such a
    pair is still a cliff, and the strongest kind.
    """
    distance = 1.0 - similarity
    return round(abs(delta_p_affinity) / distance, 2) if distance > 0 else None
