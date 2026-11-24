"""Code 1: Find the fragment-swap triples and check them, from the notebook 4.5-fragment-swaps-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""Find fragment-swap triples among one BindingDB target's ligands.

A triple is three compounds measured on the same target where

    parent 1 = X-B        (split by cutting one acyclic single bond)
    parent 2 = Y-D
    hybrid   = X-Y        (one fragment of each parent, joined)

so the hybrid is the A-C / A-D / B-C / B-D recombination of the two parents' halves.
Every fragment must hold at least 1/3 of its own molecule's heavy atoms, X, B, Y, D must all be
different, and the three compounds must be distinct constitutions (stereochemistry removed).

Fragmentation is the mcp-bindingdb server's own (sar.py: parent = largest fragment, single acyclic
cuts via rdMMPA), so the fragments are the ones matched_molecular_pairs works with. A triple is in
effect two matched pairs sharing the hybrid; this code finds the pairs that share one.

One compound pair yields several near-identical cuts, and a handful of fragments recur across hundreds
of papers, so the raw triples are heavily redundant. The ranked output keeps one representative per
*swap axis* (the hybrid plus the two fragments it is cut into), then one per compound triple.

The ligands come from run_sql pages (compound, SMILES, the median p_affinity per affinity type, the
articles that report it):

    ranked, counts = find_swaps(pages)
    ranked.to_csv("fragment_swap_axes_polymerid223.csv", index=False)
"""
import collections
import itertools

import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMMPA

from mcp_bindingdb import sar

MIN_FRACTION = 3  # each fragment must be at least 1/MIN_FRACTION of the molecule's heavy atoms


def flat(smiles):
    """Canonical SMILES of the parent with stereochemistry removed (an epimer pair is not a swap)."""
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    Chem.RemoveStereochemistry(mol)
    return Chem.MolToSmiles(mol)


def canon(frag):
    """Canonical SMILES of a cut fragment, attachment point numbered [*:1]."""
    mol = Chem.MolFromSmiles(frag)
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetAtomMapNum(1)
    return Chem.MolToSmiles(mol)


def find_swaps(pages):
    """pages: the run_sql results listing the target's ligands. Returns (ranked table, counts)."""
    cpd = pd.DataFrame([row for page in pages for row in page["rows"]])
    arts = {int(m): set(a or []) for m, a in zip(cpd.monomerid, cpd.articles)}
    counts = {"compounds": len(cpd)}
    flat_smiles = {int(m): flat(s) for m, s in zip(cpd.monomerid, cpd.smiles)}

    # 1. fragment every compound: each single cut whose two halves are both >= 1/3 of the molecule
    cuts = collections.defaultdict(set)
    for mid, mol in zip(cpd.monomerid, sar.molecules(cpd.smiles.tolist())):
        if mol is None:
            continue
        n_heavy = mol.GetNumHeavyAtoms()
        for _, chains in rdMMPA.FragmentMol(mol, maxCuts=1, maxCutBonds=sar.MAX_CUT_BONDS, resultsAsMols=False):
            parts = chains.split(".")
            if len(parts) != 2:
                continue
            if MIN_FRACTION * min(sar.heavy_atoms(p) for p in parts) < n_heavy:
                continue
            cuts[int(mid)].add(tuple(sorted(canon(p) for p in parts)))
    counts["split"] = len(cuts)

    # 2. index fragments: which compounds contain one, and what it is paired with there
    containing = collections.defaultdict(list)
    by_fragment_pair = collections.defaultdict(set)
    for mid, compound_cuts in cuts.items():
        for frag_a, frag_b in compound_cuts:
            containing[frag_a].append((mid, frag_b))
            containing[frag_b].append((mid, frag_a))
            by_fragment_pair[(frag_a, frag_b)].add(mid)

    # 3. for each compound taken as the hybrid X-Y, every parent pair that supplies X and Y
    rows = set()
    for hybrid, compound_cuts in cuts.items():
        for x, y in compound_cuts:
            for (p1, b), (p2, d) in itertools.product(containing[x], containing[y]):
                if len({hybrid, p1, p2}) < 3 or len({x, y, b, d}) < 4:
                    continue
                if len({flat_smiles[hybrid], flat_smiles[p1], flat_smiles[p2]}) < 3:
                    continue  # an epimer pair is not a fragment swap
                first, second = sorted([(p1, x, b), (p2, y, d)])
                rows.add((hybrid, x, y, *first, *second))
    tr = pd.DataFrame(sorted(rows), columns=["hybrid", "axis_x", "axis_y", "parent1", "p1_kept", "p1_other",
                                             "parent2", "p2_kept", "p2_other"])
    counts["raw_triples"] = len(tr)
    counts["hybrids"] = int(tr.hybrid.nunique())
    counts["axes"] = tr.groupby(["hybrid", "axis_x", "axis_y"]).ngroups

    # 4. annotate: affinities, the fourth corner of the square, shared publication
    info = cpd.set_index("monomerid")
    for role in ("hybrid", "parent1", "parent2"):
        for c in ("name", "smiles", "p_ki", "p_ic50", "n_measurements"):
            tr[f"{role}_{c}"] = tr[role].map(info[c])
    tr["fourth_corner"] = [",".join(str(m) for m in sorted(by_fragment_pair.get(tuple(sorted((b, d))), ())))
                           for b, d in zip(tr.p1_other, tr.p2_other)]
    tr["complete_square"] = tr.fourth_corner != ""
    tr["fourth"] = [int(f.split(",")[0]) if f else None for f in tr.fourth_corner]
    tr["shared_article"] = [bool(arts.get(h, set()) & arts.get(p1, set()) & arts.get(p2, set()))
                            for h, p1, p2 in zip(tr.hybrid, tr.parent1, tr.parent2)]
    for t in ("ki", "ic50"):
        best = tr[[f"parent1_p_{t}", f"parent2_p_{t}"]].max(axis=1)
        tr[f"hybrid_minus_best_parent_{t}"] = (tr[f"hybrid_p_{t}"] - best).round(2)
        tr[f"all_three_{t}"] = tr[[f"hybrid_p_{t}", f"parent1_p_{t}", f"parent2_p_{t}"]].notna().all(axis=1)
        # the square closes: with the fourth corner measured too, the two halves' effects can be added up.
        # interaction = what the hybrid does beyond that sum (0 = the halves act independently)
        tr[f"fourth_p_{t}"] = tr.fourth.map(info[f"p_{t}"])
        tr[f"interaction_{t}"] = (tr[f"hybrid_p_{t}"] - (tr[f"parent1_p_{t}"] + tr[f"parent2_p_{t}"]
                                                         - tr[f"fourth_p_{t}"])).round(2)
    tr["comparable"] = tr.all_three_ki | tr.all_three_ic50
    tr["gain"] = tr.hybrid_minus_best_parent_ki.where(tr.all_three_ki, tr.hybrid_minus_best_parent_ic50)

    # 5. one representative per swap axis: the best-evidenced parent pair for that hybrid cut
    tr["evidence"] = (tr.shared_article.astype(int) * 8 + tr.comparable.astype(int) * 4
                      + tr.all_three_ki.astype(int) * 2 + tr.complete_square.astype(int))
    tr["abs_gain"] = tr.gain.abs()
    axis = ["hybrid", "axis_x", "axis_y"]
    tr["n_parent_pairs_for_axis"] = tr.groupby(axis).hybrid.transform("size")
    n_x = tr.axis_x.map(sar.heavy_atoms)
    n_y = tr.axis_y.map(sar.heavy_atoms)
    tr["hybrid_split"] = [f"{a}+{b}" for a, b in zip(n_x, n_y)]
    tr["smaller_fragment_fraction"] = (n_x.combine(n_y, min) / (n_x + n_y)).round(2)
    ranked = (tr.sort_values(["evidence", "abs_gain", "hybrid", "parent1", "parent2", "axis_x", "axis_y"],
                             ascending=[False, False, True, True, True, True, True], na_position="last")
                .drop_duplicates(axis)
                .drop_duplicates(["hybrid", "parent1", "parent2"])
                .drop(columns=["evidence", "abs_gain", "axis_x", "axis_y"]))
    order = ["hybrid", "hybrid_name", "parent1", "parent1_name", "parent2", "parent2_name",
             "p1_kept", "p1_other", "p2_kept", "p2_other",
             "hybrid_p_ki", "parent1_p_ki", "parent2_p_ki", "hybrid_minus_best_parent_ki", "all_three_ki",
             "hybrid_p_ic50", "parent1_p_ic50", "parent2_p_ic50", "hybrid_minus_best_parent_ic50",
             "all_three_ic50", "comparable", "shared_article", "complete_square", "fourth_corner",
             "fourth_p_ki", "interaction_ki", "fourth_p_ic50", "interaction_ic50",
             "hybrid_split", "smaller_fragment_fraction", "n_parent_pairs_for_axis",
             "hybrid_smiles", "parent1_smiles", "parent2_smiles",
             "hybrid_n_measurements", "parent1_n_measurements", "parent2_n_measurements"]
    ranked = (ranked[order].sort_values(["comparable", "shared_article", "complete_square", "hybrid", "parent1",
                                         "parent2"], ascending=[False, False, False, True, True, True])
              .reset_index(drop=True))
    counts["triples"] = len(ranked)
    counts["comparable"] = int(ranked.comparable.sum())
    counts["one_publication"] = int(ranked.shared_article.sum())
    counts["complete_squares"] = int(ranked.complete_square.sum())
    counts["all_four"] = int(ranked[["interaction_ki", "interaction_ic50"]].notna().any(axis=1).sum())
    print(counts)
    return ranked, counts


def rejoin(frag_x, frag_y):
    """Join two fragments at their [*:1] attachment points; canonical SMILES."""
    combo = Chem.CombineMols(Chem.MolFromSmiles(frag_x), Chem.MolFromSmiles(frag_y))
    dummies = [a.GetIdx() for a in combo.GetAtoms() if a.GetAtomicNum() == 0]
    ends = [combo.GetAtomWithIdx(i).GetNeighbors()[0].GetIdx() for i in dummies]
    rw = Chem.RWMol(combo)
    rw.AddBond(ends[0], ends[1], Chem.BondType.SINGLE)
    for i in sorted(dummies, reverse=True):
        rw.RemoveAtom(i)
    mol = rw.GetMol()
    Chem.SanitizeMol(mol)
    return Chem.MolToSmiles(mol)


def rejoin_check(ranked):
    """How many triples' hybrids are exactly the two kept fragments joined (same constitution)."""
    good = 0
    for x, y, smiles in zip(ranked.p1_kept, ranked.p2_kept, ranked.hybrid_smiles):
        try:
            good += flat(rejoin(x, y)) == flat(Chem.MolToSmiles(sar.molecules([smiles])[0]))
        except Exception:
            pass
    print(f"rejoining the two kept fragments reproduces the hybrid in {good} of {len(ranked)} triples")
    return good
