"""Find fragment-swap triples among one BindingDB target's ligands.

A triple is three compounds measured on the same target where

    parent 1 = X-B        (split by cutting one acyclic single bond)
    parent 2 = Y-D
    hybrid   = X-Y        (one fragment of each parent, joined)

so the hybrid is the A-C / A-D / B-C / B-D recombination of the two parents' halves.
Every fragment must hold at least 1/3 of its own molecule's heavy atoms, X, B, Y, D must all be
different, and the three compounds must be distinct.

Fragmentation is the mcp-bindingdb server's own (sar.py: parent = largest fragment, single acyclic
cuts via rdMMPA), so the fragments are the ones matched_molecular_pairs works with. A triple is in
effect two matched pairs sharing the hybrid; this script finds the pairs that share one.

One compound pair yields several near-identical cuts, and a handful of fragments (the Boc-Phe and
darunavir-style sulfonamide halves) recur across hundreds of papers, so the raw triples are heavily
redundant. The ranked output keeps one representative per *swap axis* - the hybrid plus the two
fragments it is cut into - which is one row per distinct piece of chemistry.

usage: python find_fragment_swaps.py DB_PATH --polymer 223 [--complex N] [--raw-out DIR] [--out DIR]
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import itertools
import os
import sys

import duckdb
import pandas as pd
from rdkit import Chem
from rdkit.Chem import rdMMPA

MIN_FRACTION = 3  # each fragment must be at least 1/MIN_FRACTION of the molecule's heavy atoms

ap = argparse.ArgumentParser()
ap.add_argument("db", help="path to bindingdb_*.duckdb")
ap.add_argument("--polymer", type=int)
ap.add_argument("--complex", type=int)
ap.add_argument("--sar", default=os.path.expanduser("~/GitRepositories/mcp-bindingdb/src/mcp_bindingdb/sar.py"))
ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
ap.add_argument("--raw-out", help="also write every triple here (large); default: ranked table only")
args = ap.parse_args()
if not (args.polymer or args.complex):
    sys.exit("give --polymer or --complex")

spec = importlib.util.spec_from_file_location("sar", args.sar)
sar = importlib.util.module_from_spec(spec)
sys.modules["sar"] = sar
spec.loader.exec_module(sar)

col, tid = ("polymerid", args.polymer) if args.polymer else ("complexid", args.complex)
con = duckdb.connect(args.db, read_only=True)
cpd = con.execute(f"""
  select a.monomerid,
         any_value(c.smiles) as smiles,
         any_value(a.compound_name) as "name",
         median(a.p_affinity) filter (where a.affinity_type = 'Ki')   as p_ki,
         median(a.p_affinity) filter (where a.affinity_type = 'IC50') as p_ic50,
         count(*) as n_measurements
  from activity a join compound c using (monomerid)
  where a.{col} = ? and a.p_affinity is not null
  group by 1""", [tid]).df()
articles = con.execute(f"""
  select monomerid, list(distinct articleid) as arts
  from activity where {col} = ? and articleid is not null group by 1""", [tid]).df()
target_name = con.execute(f"select any_value(target_name) from activity where {col} = ?", [tid]).fetchone()[0]
arts = {int(m): set(a) for m, a in zip(articles.monomerid, articles.arts)}
print(f"{target_name} ({col} {tid}): {len(cpd)} compounds with a measured affinity", file=sys.stderr)


def flat(smiles: str) -> str | None:
    """Canonical SMILES of the parent with stereochemistry removed.

    Two epimers fragment into fragments that differ only in stereochemistry, so without this an
    epimer pair looks like a swap of two different fragments. A triple is required to be three
    different constitutions.
    """
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return None
    mol = Chem.MolFromSmiles(Chem.MolToSmiles(mol))
    Chem.RemoveStereochemistry(mol)
    return Chem.MolToSmiles(mol)


def canon(frag: str) -> str:
    """Canonical SMILES of a cut fragment, attachment point numbered [*:1]."""
    mol = Chem.MolFromSmiles(frag)
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0:
            atom.SetAtomMapNum(1)
    return Chem.MolToSmiles(mol)


flat_smiles = {int(m): flat(s) for m, s in zip(cpd.monomerid, cpd.smiles)}

# 1. fragment every compound: each single cut whose two halves are both >= 1/3 of the molecule
cuts: dict[int, set[tuple[str, str]]] = collections.defaultdict(set)
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
print(f"{len(cuts)} of them split into two fragments that are each >= 1/{MIN_FRACTION} of the molecule",
      file=sys.stderr)

# 2. index fragments: which compounds contain one, and what it is paired with there
containing: dict[str, list[tuple[int, str]]] = collections.defaultdict(list)
by_fragment_pair: dict[tuple[str, str], set[int]] = collections.defaultdict(set)
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
tr = pd.DataFrame(sorted(rows), columns=["hybrid", "axis_x", "axis_y",
                                         "parent1", "p1_kept", "p1_other",
                                         "parent2", "p2_kept", "p2_other"])
print(f"{len(tr)} triples over {tr.hybrid.nunique()} hybrids "
      f"and {tr.groupby(['hybrid', 'axis_x', 'axis_y']).ngroups} swap axes", file=sys.stderr)

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
    tr[f"interaction_{t}"] = (tr[f"hybrid_p_{t}"]
                              - (tr[f"parent1_p_{t}"] + tr[f"parent2_p_{t}"] - tr[f"fourth_p_{t}"])).round(2)
tr["comparable"] = tr.all_three_ki | tr.all_three_ic50
tr["gain"] = tr.hybrid_minus_best_parent_ki.where(tr.all_three_ki, tr.hybrid_minus_best_parent_ic50)

slug = f"{col}{tid}"
if args.raw_out:
    tr.to_csv(os.path.join(args.raw_out, f"fragment_swap_triples_{slug}_all.csv"), index=False)

# 5. one representative per swap axis: the best-evidenced parent pair for that hybrid cut
tr["evidence"] = (tr.shared_article.astype(int) * 8 + tr.comparable.astype(int) * 4
                  + tr.all_three_ki.astype(int) * 2 + tr.complete_square.astype(int))
tr["abs_gain"] = tr.gain.abs()
axis = ["hybrid", "axis_x", "axis_y"]
tr["n_parent_pairs_for_axis"] = tr.groupby(axis).hybrid.transform("size")
# how the hybrid divides, as heavy atoms: the 1/3 rule means neither side drops below a third
n_x = tr.axis_x.map(sar.heavy_atoms)
n_y = tr.axis_y.map(sar.heavy_atoms)
tr["hybrid_split"] = [f"{a}+{b}" for a, b in zip(n_x, n_y)]
tr["smaller_fragment_fraction"] = (n_x.combine(n_y, min) / (n_x + n_y)).round(2)
# one row per swap axis, then one per compound triple: near-identical cuts of the same bond region
# are different axes but the same piece of chemistry
ranked = (tr.sort_values(["evidence", "abs_gain"], ascending=False, na_position="last")
            .drop_duplicates(axis)
            .drop_duplicates(["hybrid", "parent1", "parent2"])
            .drop(columns=["evidence", "abs_gain", "axis_x", "axis_y"]))

order = ["hybrid", "hybrid_name", "parent1", "parent1_name", "parent2", "parent2_name",
         "p1_kept", "p1_other", "p2_kept", "p2_other",
         "hybrid_p_ki", "parent1_p_ki", "parent2_p_ki", "hybrid_minus_best_parent_ki", "all_three_ki",
         "hybrid_p_ic50", "parent1_p_ic50", "parent2_p_ic50", "hybrid_minus_best_parent_ic50", "all_three_ic50",
         "comparable", "shared_article", "complete_square", "fourth_corner",
         "fourth_p_ki", "interaction_ki", "fourth_p_ic50", "interaction_ic50",
         "hybrid_split", "smaller_fragment_fraction", "n_parent_pairs_for_axis",
         "hybrid_smiles", "parent1_smiles", "parent2_smiles",
         "hybrid_n_measurements", "parent1_n_measurements", "parent2_n_measurements"]
ranked = ranked[order].sort_values(["comparable", "shared_article", "complete_square"], ascending=False)
out = os.path.join(args.out, f"fragment_swap_axes_{slug}.csv")
ranked.to_csv(out, index=False)
print(f"{len(ranked)} distinct triples -> {out}", file=sys.stderr)
print(f"  comparable (all three same affinity type): {int(ranked.comparable.sum())}", file=sys.stderr)
print(f"  from one publication: {int(ranked.shared_article.sum())}", file=sys.stderr)
print(f"  complete squares: {int(ranked.complete_square.sum())} "
      f"({int(ranked[['interaction_ki', 'interaction_ic50']].notna().any(axis=1).sum())} with all four values)",
      file=sys.stderr)
