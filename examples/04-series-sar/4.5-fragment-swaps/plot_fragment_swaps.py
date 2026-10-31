"""Does joining two ligands' halves give a better ligand? HIV-1 protease, 1,666 fragment-swap triples.

Panel A places each triple at what the hybrid gained over its better parent. Panel B takes the triples
whose square closes - the fourth recombination was measured too - and places each at the hybrid's
*interaction*: how far it lands from the sum of the two halves' separate effects. Zero means the two
halves act independently, so the hybrid is exactly what adding up the parts predicts.

A comparison is only trustworthy if the values were measured in the same place, so each triple is
checked against the documents its compounds come from. Blue triples have a paper or patent that reports
all three (panel A) or all four (panel B) compounds; grey triples compare one laboratory's number with
another's. Medians and percentages are of the blue triples only.

    python plot_fragment_swaps.py [fragment_swap_axes_polymerid223.csv]

The triples come from find_fragment_swaps.py, which writes that CSV.
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV = sys.argv[1] if len(sys.argv) > 1 else "fragment_swap_axes_polymerid223.csv"
PNG = "fragment_swap_effects.png"
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
CHECKED, UNCHECKED = "#2a78d6", "#a9a8a2"  # one document in common / none
BINS = [x / 2 for x in range(-10, 11)]     # -5 to +5 log units, half-log bins
XLIM = 5

d = pd.read_csv(CSV)
# one value per triple: Ki where all three (or four) have it, otherwise IC50
panels = []
gain = d.hybrid_minus_best_parent_ki.where(d.all_three_ki, d.hybrid_minus_best_parent_ic50)
panels.append(("A  What the hybrid gained over its better parent",
               "hybrid − better parent (log units)", gain[d.comparable], d.shared_article[d.comparable]))
inter = d.interaction_ki.fillna(d.interaction_ic50)
ok = inter.notna()
panels.append(("B  How far the hybrid lands from the two halves added up",
               "observed − additive (log units)", inter[ok], d.shared_article[ok]))

fig, axes = plt.subplots(1, 2, figsize=(12.6, 5.2), facecolor=SURF)
for ax, (title, xlabel, values, checked) in zip(axes, panels):
    ax.set_facecolor(SURF)
    blue, grey = values[checked], values[~checked]
    ax.hist([grey.clip(-XLIM, XLIM), blue.clip(-XLIM, XLIM)], bins=BINS, stacked=True,
            color=[UNCHECKED, CHECKED], edgecolor=SURF, linewidth=0.6)
    ax.set_xlim(-XLIM, XLIM)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.28)          # headroom for the notes
    ax.axvline(0, color=INK, linewidth=1, zorder=3)
    median = blue.median()
    ax.axvline(median, color=CHECKED, linewidth=1.6, linestyle=(0, (4, 2)), zorder=4)
    share = (blue > 0).mean() if title.startswith("A") else (blue.abs() > 1).mean()
    note = (f"{share:.0%} of checked triples beat both parents"
            if title.startswith("A") else
            f"{share:.0%} of checked squares miss additivity by more than 10x")
    box = dict(facecolor=SURF, edgecolor="none", pad=1.5)
    ax.text(0.985, 0.97, note, transform=ax.transAxes, color=INK2, fontsize=9.5,
            ha="right", va="top", bbox=box, zorder=5)
    ax.text(0.985, 0.89, f"median {median:+.2f} · n = {len(blue):,} checked, {len(grey):,} unchecked",
            transform=ax.transAxes, color=INK2, fontsize=9.5, ha="right", va="top", bbox=box, zorder=5)
    ax.set_title(title, color=INK, fontsize=11.5, loc="left", pad=8)
    ax.set_xlabel(xlabel, color=INK2, fontsize=10)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9.5, length=0)
axes[0].set_ylabel("triples", color=INK2, fontsize=10)
fig.tight_layout(rect=(0, 0.07, 1, 0.92))
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in (CHECKED, UNCHECKED)],
           labels=["all values from one document", "values from different documents"],
           loc="lower center", ncol=2, frameon=False, fontsize=9.5, labelcolor=INK2,
           bbox_to_anchor=(0.5, 0.005))
fig.suptitle("Recombining two HIV-1 protease ligands' halves", color=INK, fontsize=13.5,
             x=0.012, ha="left", y=0.975)
fig.savefig(PNG, dpi=200, facecolor=SURF)
print(f"wrote {os.path.abspath(PNG)}")
