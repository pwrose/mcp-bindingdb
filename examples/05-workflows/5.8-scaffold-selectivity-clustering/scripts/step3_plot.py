"""Clustered heat map of the 38 x 8 block."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from scipy.cluster.hierarchy import dendrogram

S, OUT = Path(sys.argv[1]), Path(sys.argv[2])
cells = pd.read_parquet(S / "cells.parquet"); tinfo = pd.read_parquet(S / "tinfo.parquet").set_index("tkey")
names = pd.read_parquet(S / "names.parquet"); cl = json.load(open(S / "cluster.json"))
rows, cols = cl["rows"], cl["cols"]
nm = {r.monomerid: [x.lower() for x in r.names] for r in names.itertuples()}
def label(m):
    for d in ("imatinib", "nilotinib"):
        if d in nm.get(m, []): return d.capitalize()
    return f"BDBM{m}"
C = cells.set_index(["monomerid", "tkey"])

SURF, INK, INK2, MUTED, ND = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#f0efec"
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf",
        "#1c5cab", "#184f95", "#104281", "#0d366b"]
cmap = LinearSegmentedColormap.from_list("blue", RAMP)
lo, hi = 3.0, 8.5
norm = Normalize(lo, hi)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2})

nr, nc = len(rows), len(cols)
fig = plt.figure(figsize=(9.6, 15.2), facecolor=SURF)
L, B, W, H = 0.17, 0.105, 0.47, 0.78
ax = fig.add_axes([L, B, W, H]); axr = fig.add_axes([0.015, B, L - 0.02, H]); axc = fig.add_axes([L, B + H + 0.004, W, 0.06])
for a in (ax, axr, axc): a.set_facecolor(SURF)

for i, m in enumerate(rows):
    for j, t in enumerate(cols):
        y = i
        if (m, t) not in C.index:
            ax.add_patch(Rectangle((j, y), 1, 1, fc=ND, ec=SURF, lw=2))
            ax.text(j + .5, y + .5, "n.d.", ha="center", va="center", fontsize=7, color=MUTED)
            continue
        c = C.loc[(m, t)]
        # a censored cell is "no better than" its bound: drawn at the bottom of the scale, not at the bound
        fc = RAMP[0] if c.censored else cmap(norm(np.clip(c.p_affinity, lo, hi)))
        ax.add_patch(Rectangle((j, y), 1, 1, fc=fc, ec=SURF, lw=2))
        dark = not c.censored and norm(c.p_affinity) > 0.55
        txtc = "#ffffff" if dark else INK
        if c.censored:
            ax.add_patch(Rectangle((j + .04, y + .06), .92, .88, fc="none", ec=INK2 if not dark else "#ffffff",
                                   lw=0, hatch="////", alpha=0.3))
        ax.text(j + .5, y + .5, ("<" if c.censored else "") + f"{c.p_affinity:.1f}", ha="center", va="center",
                fontsize=8, color=txtc, fontweight="bold" if not c.censored else "normal")
        if c.affinity_type in ("Kd", "Ki"):
            mk = "o" if c.affinity_type == "Kd" else "s"
            ax.plot(j + .12, y + .2, marker=mk, ms=4.5, mfc=txtc, mec=txtc, lw=0)
ax.set_xlim(0, nc); ax.set_ylim(nr, 0)
ax.set_xticks(np.arange(nc) + .5); ax.set_xticklabels([tinfo.short[t].replace("PDGFR-", "PDGFR\n").replace("BCR-", "BCR-\n") for t in cols],
                   rotation=0, fontsize=9, color=INK)
ax.xaxis.tick_bottom()
ax.yaxis.tick_right(); ax.set_yticks(np.arange(nr) + .5)
ax.set_yticklabels([f"{i+1:>2}  {label(m)}" for i, m in enumerate(rows)], fontsize=8.5, color=INK, family="DejaVu Sans Mono")
for lab in ax.get_yticklabels():
    if not lab.get_text().split()[-1].startswith("BDBM"): lab.set_fontweight("bold")
ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)

# dendrograms (row order may have been flipped so imatinib/nilotinib sit at the top)
Zr = np.array(cl["Zr"]); Zc = np.array(cl["Zc"])
dr = dendrogram(Zr, orientation="left", no_plot=True)
flip = [cl["row_ids"][k] for k in dr["leaves"]] != rows
for xs, ys in zip(dr["dcoord"], dr["icoord"]):
    ys = np.array(ys) / 10.0
    if flip: ys = nr - ys
    axr.plot(-np.array(xs), ys, color=INK2, lw=1)
axr.set_ylim(nr, 0); axr.axis("off")
dc = dendrogram(Zc, no_plot=True)
for xs, ys in zip(dc["icoord"], dc["dcoord"]):
    axc.plot(np.array(xs) / 10.0, ys, color=INK2, lw=1)
axc.set_xlim(0, nc); axc.axis("off")

fig.text(0.015, 0.975, "Kinase selectivity of 2-anilino-4-(3-pyridyl)pyrimidines", fontsize=14, fontweight="bold")
fig.text(0.015, 0.960, "38 BindingDB compounds × the 8 kinases with the densest shared coverage · median pAffinity per cell",
         fontsize=9.5, color=INK2)
# colour bar and key
cax = fig.add_axes([L, 0.062, W * 0.62, 0.010])
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
cb.outline.set_visible(False); cb.ax.tick_params(length=0, labelsize=8, colors=INK2)
cb.set_label("pAffinity = −log10(median affinity / M)   (darker = more potent)", fontsize=8.5, color=INK2)
key = [Line2D([], [], marker="o", ls="", ms=5, mfc=INK, mec=INK, label="Kd"),
       Line2D([], [], marker="s", ls="", ms=5, mfc=INK, mec=INK, label="Ki"),
       Rectangle((0, 0), 1, 1, fc=RAMP[4], ec="none", label="no glyph: IC50"),
       Rectangle((0, 0), 1, 1, fc=RAMP[0], ec=INK2, lw=0, hatch="////", label="< censored: no activity up to the\n   highest concentration tested"),
       Rectangle((0, 0), 1, 1, fc=ND, ec="none", label="n.d. not measured")]
fig.legend(handles=key, loc="lower left", bbox_to_anchor=(L + W + 0.02, 0.03), frameon=False, fontsize=8, ncol=1,
           labelcolor=INK2, handlelength=1.4)
fig.text(0.015, 0.012, "Source: BindingDB 202610 via mcp-bindingdb. Rows: average linkage on RMS pAffinity difference over shared "
         "kinases;\ncolumns: average linkage on 1 − Pearson r. One affinity type per cell (Kd > Ki > IC50); censored cells cluster at their bound.",
         fontsize=7.2, color=MUTED, va="bottom")
fig.savefig(OUT / "kinase_selectivity_heatmap.png", dpi=200, facecolor=SURF)
print("saved", flip)
