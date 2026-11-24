"""Code 1: Median pKd heat map of the 48 kinases, columns clustered, censored cells hatched, from the notebook 5.2-kinase-selectivity-panel-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, leaves_list

DRUGS = ["imatinib", "nilotinib", "bosutinib", "dasatinib"]
GENES = {"O14976": "GAK", "O15197": "EPHB6", "O94804": "STK10", "O95819": "MAP4K4", "P00519": "ABL1",
         "P06239": "LCK", "P06241": "FYN", "P07333": "CSF1R", "P07947": "YES1", "P07948": "LYN",
         "P08631": "HCK", "P09619": "PDGFRB", "P09769": "FGR", "P10721": "KIT", "P12931": "SRC",
         "P16234": "PDGFRA", "P21709": "EPHA1", "P21860": "ERBB3", "P29317": "EPHA2", "P29320": "EPHA3",
         "P29322": "EPHA8", "P29323": "EPHB2", "P36507": "MAP2K2", "P41240": "CSK", "P42681": "TXK",
         "P42684": "ABL2", "P42685": "FRK", "P51451": "BLK", "P51813": "BMX", "P54753": "EPHB3",
         "P54756": "EPHA5", "P54760": "EPHB4", "P54762": "EPHB1", "P54764": "EPHA4", "P57059": "SIK1",
         "Q06187": "BTK", "Q07912": "TNK2", "Q08345": "DDR1", "Q12851": "MAP4K2", "Q13163": "MAP2K5",
         "Q13882": "PTK6", "Q16832": "DDR2", "Q8IVH8": "MAP4K3", "Q8N4C8": "MINK1", "Q8TDR2": "STK35",
         "Q9H0K1": "SIK2", "Q9H2G2": "SLK", "Q9Y4K4": "MAP4K5"}

def matrix(rows):
    """Median pKd (drug x kinase), censored mask (every value was '> 10 uM') and measurement counts."""
    df = pd.DataFrame(rows)
    df["gene"] = df["uniprot"].map(GENES).fillna(df["uniprot"])
    df = df.set_index("gene")
    pkd = df[DRUGS].T.astype(float)
    cens = pd.DataFrame({d: df["neq_" + d] == 0 for d in DRUGS}).T
    n = pd.DataFrame({d: df["n_" + d] for d in DRUGS}).T
    return pkd, cens, n

def order_columns(pkd):
    return list(pkd.columns[leaves_list(linkage(pkd.T.values, "average"))])

def summary(pkd, cens, n):
    out = pd.DataFrame({"kinases >= 8": (pkd >= 8).sum(axis=1), "kinases >= 9": (pkd >= 9).sum(axis=1),
                        "single-measurement cells": (n == 1).sum(axis=1),
                        "censored cells": cens.sum(axis=1)})
    return out

def plot_heatmap(rows, png, csv):
    pkd, cens, n = matrix(rows)
    cols = order_columns(pkd)
    pkd, cens, n = pkd[cols], cens[cols], n[cols]
    pkd.round(2).rename_axis("drug").to_csv(csv)
    fig, ax = plt.subplots(figsize=(15, 3.6), dpi=130)
    im = ax.imshow(pkd.values, aspect="auto", cmap="viridis", vmin=5, vmax=10.5)
    for i in range(cens.shape[0]):
        for j in range(cens.shape[1]):
            if cens.iloc[i, j]:
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, fill=False, hatch="////", edgecolor="#ffffff", lw=0))
            else:
                v = pkd.iloc[i, j]
                ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=6.2,
                        color="white" if v < 8.6 else "black")
    ax.set_xticks(range(len(cols)), cols, rotation=90, fontsize=8)
    ax.set_yticks(range(len(pkd.index)), pkd.index, fontsize=10)
    ax.set_title("Kd selectivity: median pKd across 48 human kinases (hatched: all values Kd > 10 µM)", fontsize=11, loc="left")
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.025); cb.set_label("median pKd")
    fig.tight_layout(); fig.savefig(png); plt.close(fig)
    return summary(pkd, cens, n)
