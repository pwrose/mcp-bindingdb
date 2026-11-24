"""Code 1: t-SNE map of the potent PDE2A ligands, coloured by chemotype family, from the notebook 7.3-scaffold-landscape-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""t-SNE map of the chemical space of potent PDE2A ligands, coloured by chemotype family.

Compounds: every compound with a Ki, Kd, IC50 or EC50 of 10 nM or better against human PDE2A
(BindingDB target 788, UniProt O00408), the set find_ligands_for_target(group_by_scaffold=True,
max_value_nm=10) groups into Bemis-Murcko scaffolds. The input is the run_sql result that lists them
(monomerid, smiles, scaffold, generic_scaffold, p_affinity), also saved as pde2a_potent_ligands.csv.
Each compound is described by its Morgan fingerprint (radius 2, 2048 bits, largest fragment, as in
similarity_search) and placed by t-SNE on Jaccard (= 1 - Tanimoto) distances, so compounds that are similar
by fingerprint end up close together.

A chemotype family is the set of Murcko scaffolds that share one core: the tool returns them as separate
scaffolds because a ring substituent on the core counts as part of a Murcko scaffold. The families below
are matched by that core, and the legend gives how many scaffolds each one covers.

Needs matplotlib, scikit-learn, numpy and RDKit.
"""
import csv

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rdkit import Chem, DataStructs, RDLogger
from rdkit.Chem import rdFingerprintGenerator
from rdkit.Chem.MolStandardize import rdMolStandardize
from sklearn.manifold import TSNE

# family: (label for the legend, short label on the map, test on the Murcko scaffold)
FAMILIES = [
    ("Pyrimidinone carboxamides", "Pyrimidinone\ncarboxamides",
     lambda s: s.startswith("O=C(NCc1ccccc1)c1cc(=O)[nH]")),
    ("Pyrazolo[3,4-d]pyrimidinones", "Pyrazolo[3,4-d]-\npyrimidinones",
     lambda s: s.startswith("O=c1[nH]cnc2c1cnn2")),
    ("Triazoloquinoxalines", "Triazolo-\nquinoxalines", lambda s: "nnc3cnc4" in s),
    ("Azetidinyl pyrimidines", "Azetidinyl\npyrimidines", lambda s: "N4CCC4" in s or "N3CCC3" in s),
]
SURF, INK, INK2, CLOUD = "#fcfcfb", "#0b0b0b", "#52514e", "#c9c8c2"
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#8d53c4"]


def plot_tsne(result, png="pde2a_chemical_space_tsne.png", csv_path="pde2a_potent_ligands.csv"):
    """result: the run_sql result of the potent-compound query (its 'rows')."""
    rows = result["rows"]
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["monomerid", "smiles", "scaffold", "generic_scaffold", "p_affinity"])
        w.writerows([[r["monomerid"], r["smiles"], r["scaffold"], r["generic_scaffold"], r["p_affinity"]]
                     for r in rows])
    RDLogger.DisableLog("rdApp.*")
    generator = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
    largest = rdMolStandardize.LargestFragmentChooser()
    kept, bits = [], []
    for r in rows:
        mol = Chem.MolFromSmiles(r["smiles"])
        if mol is None:
            continue
        arr = np.zeros(2048, dtype=bool)
        DataStructs.ConvertToNumpyArray(generator.GetFingerprint(largest.choose(mol)), arr)
        kept.append(r)
        bits.append(arr)
    xy = TSNE(n_components=2, metric="jaccard", perplexity=30, init="random", random_state=7,
              max_iter=2000).fit_transform(np.array(bits))
    members = [[i for i, r in enumerate(kept) if r["scaffold"] and test(r["scaffold"])]
               for _, _, test in FAMILIES]
    in_family = {i for idx in members for i in idx}
    other = [i for i in range(len(kept)) if i not in in_family]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, ax = plt.subplots(figsize=(9.5, 8.0), facecolor=SURF)
    ax.set_facecolor(SURF)
    ax.scatter(xy[other, 0], xy[other, 1], s=11, color=CLOUD, lw=0,
               label=f"Other scaffolds ({len(other)} compounds)")
    for (label, short, _), idx, color in zip(FAMILIES, members, COLORS):
        n_scaffolds = len({kept[i]["scaffold"] for i in idx})
        ax.scatter(xy[idx, 0], xy[idx, 1], s=30, color=color, edgecolor=SURF, lw=1.0, zorder=3,
                   label=f"{label} ({len(idx)} compounds, {n_scaffolds} scaffolds)")
        # Label the family where its points are densest, so the text sits on the main island.
        pts = xy[idx]
        k = min(12, len(pts))
        spread = [np.sort(np.hypot(*(pts - p).T))[:k].sum() for p in pts]
        anchor = pts[int(np.argmin(spread))]
        ax.annotate(short, anchor, xytext=(0, 22), textcoords="offset points", ha="center", va="bottom",
                    color=INK, fontsize=9.5, fontweight="bold", zorder=5)
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, -0.01), ncol=1, labelcolor=INK, fontsize=9.5)
    ax.set_title(f"Four chemotypes fill the potent chemical space of PDE2A ({len(kept):,} compounds ≤ 10 nM)",
                 loc="left", color=INK, fontsize=13.5, fontweight="bold", pad=24)
    ax.text(0, 1.015, "Morgan fingerprints (radius 2), Tanimoto distance; nearby points are similar compounds. "
            "Axes have no units.", transform=ax.transAxes, color=INK2, fontsize=9)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.19)
    fig.savefig(png, dpi=170, facecolor=SURF)
    plt.close(fig)
    print("ok", len(kept), [len(i) for i in members], "other", len(other),
          "scaffolds", [len({kept[i]['scaffold'] for i in idx}) for idx in members])
