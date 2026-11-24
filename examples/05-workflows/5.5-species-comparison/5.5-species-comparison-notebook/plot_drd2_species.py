"""Code 1: Scatter plot of human vs rat pKi; tautomer check of the two clozapine records, from the notebook 5.5-species-comparison-notebook.ipynb.

Written by claude-opus-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from rdkit import Chem
from rdkit.Chem.MolStandardize import rdMolStandardize


def plot_human_vs_rat(rows, out="drd2_human_vs_rat.png",
                      labels=(21397, 21398, 84637, 55121, 50001884, 50116766)):
    """Scatter of the per-species median pKi of every compound measured on both human and rat D2."""
    h = np.array([r["p_human"] for r in rows])
    r_ = np.array([r["p_rat"] for r in rows])
    d = h - r_
    within = np.abs(d) <= 1
    lo, hi = np.floor(min(h.min(), r_.min())) - 0.3, np.ceil(max(h.max(), r_.max())) + 0.3
    fig, ax = plt.subplots(figsize=(6.4, 6))
    xs = np.array([lo, hi])
    ax.fill_between(xs, xs - 1, xs + 1, color="0.9", zorder=0, label="within 10-fold")
    ax.plot(xs, xs, color="0.5", lw=1, zorder=1)
    ax.scatter(h[within], r_[within], s=18, color="#4C72B0", alpha=0.7, edgecolor="none",
               label=f"within 10-fold (n={within.sum()})")
    ax.scatter(h[~within], r_[~within], s=22, color="#DD8452", alpha=0.85, edgecolor="none",
               label=f"differ > 10-fold (n={(~within).sum()})")
    for row in rows:
        if row["monomerid"] in labels:
            ax.annotate(row["name"].capitalize(), (row["p_human"], row["p_rat"]), xytext=(5, -10),
                        textcoords="offset points", fontsize=8)
    r = np.corrcoef(h, r_)[0, 1]
    ax.set_xlim(lo, hi); ax.set_ylim(lo, hi); ax.set_aspect("equal")
    ax.set_xlabel("Human D2 (P14416) median pKi")
    ax.set_ylabel("Rat D2 (P61169) median pKi")
    ax.set_title(f"D2 receptor: human vs rat Ki, {len(rows)} compounds (r = {r:.2f})", fontsize=11)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    print(f"{len(rows)} compounds, {within.sum()} within 10-fold, {(~within).sum()} differ by more; r = {r:.2f}")
    return out


def same_tautomer(rows):
    """Check whether duplicate compound records (different InChIKeys) are tautomers of one structure."""
    enum = rdMolStandardize.TautomerEnumerator()
    for row in rows:
        mol = Chem.MolFromSmiles(row["smiles"])
        print(row["monomerid"], row["inchi_key"], "canonical tautomer:", Chem.MolToSmiles(enum.Canonicalize(mol)))
