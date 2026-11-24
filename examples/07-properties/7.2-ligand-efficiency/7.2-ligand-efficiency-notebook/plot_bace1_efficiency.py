"""Code 1: Potency against size per period, from the per-period statistics and per-compound values, from the notebook 7.2-ligand-efficiency-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""Potency against size for BACE1 inhibitors, one panel per period of first publication.

Each compound is plotted once, at its best exact ('=') Ki, Kd or IC50 against human BACE1 (target 5093)
and its heavy-atom count (compound_property, RDKit, largest fragment). Dashed lines are constant ligand
efficiency, LE = 1.37 * pAffinity / heavy atoms (kcal/mol per heavy atom).

    python plot_bace1_efficiency.py stats.json points.json

stats.json and points.json are the structured results of the two run_sql queries in the session (per-period
statistics; per period and heavy-atom count the best pAffinity values and monomer ids). The per-compound
values are also written to bace1_best_affinity.csv.
Needs matplotlib.
"""
import csv
import json
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PERIODS = ["2001-2004", "2005-2009", "2010-2014", "2015-2019", "2020-2026"]
CLINICAL = {50580216: "verubecestat", 50510823: "elenbecestat"}
SURF, INK, INK2, GRID, CLOUD = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1", "#d9d8d3"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def compounds(points):
    """One dict per compound from the per-(period, heavy atoms) rows of the points query."""
    return [{"monomerid": int(m), "p_affinity": float(p), "period": r["period"], "heavy_atoms": int(r["ha"])}
            for r in points["rows"] for m, p in zip(r["ids"], r["p_values"])]


def write_csv(data, path="bace1_best_affinity.csv"):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["monomerid", "p_affinity", "period", "heavy_atoms"])
        w.writeheader()
        w.writerows(data)


def plot(stats, points, out="bace1_efficiency_by_period.png"):
    data = compounds(points)
    st = {r["period"]: r for r in stats["rows"]}
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2})
    fig, axs = plt.subplots(1, len(PERIODS), figsize=(17, 4.6), sharex=True, sharey=True, facecolor=SURF)
    xs = [10, 85]
    for ax, period in zip(axs, PERIODS):
        mine = [d for d in data if d["period"] == period]
        ax.set_facecolor(SURF)
        ax.scatter([d["heavy_atoms"] for d in data], [d["p_affinity"] for d in data], s=4, color=CLOUD,
                   lw=0, zorder=1, rasterized=True)
        ax.scatter([d["heavy_atoms"] for d in mine], [d["p_affinity"] for d in mine], s=7, color=BLUE,
                   alpha=0.45, lw=0, zorder=3, rasterized=True)
        for le in (0.2, 0.3, 0.4):
            ax.plot(xs, [le * x / 1.37 for x in xs], color=INK2, lw=0.9, ls=(0, (3, 3)), zorder=2)
            x_label = min(74, 12.4 * 1.37 / le)  # near where the line leaves the panel
            ax.text(x_label + 1, le * x_label / 1.37 - 0.2, f"LE {le}", color=INK2, fontsize=8.5, ha="left",
                    va="top")
        for d in mine:
            if d["monomerid"] in CLINICAL:
                ax.scatter([d["heavy_atoms"]], [d["p_affinity"]], s=46, color=ORANGE, edgecolor=SURF, lw=1.5,
                           zorder=5)
                ax.annotate(CLINICAL[d["monomerid"]], (d["heavy_atoms"], d["p_affinity"]), xytext=(8, 10),
                            textcoords="offset points", color=INK, fontsize=9,
                            arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})
        ax.set_title(period.replace("-", "–"), loc="left", color=INK, fontsize=12, fontweight="bold", pad=20)
        ax.text(0, 1.015, f"{st[period]['n']:,} compounds · median LE {st[period]['med_le']:.2f}",
                transform=ax.transAxes, color=INK2, fontsize=9, va="bottom")
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.set_xlim(*xs)
        ax.set_ylim(3.5, 13)
        ax.set_xlabel("Heavy atoms")
    axs[0].set_ylabel("Best pAffinity (Ki, Kd or IC50)")
    fig.suptitle("BACE1 inhibitors grew smaller and more efficient", x=0.01, ha="left", color=INK,
                 fontsize=14, fontweight="bold")
    fig.text(0.01, 0.015, "Blue: compounds first published in the period; gray: all periods. Dashed lines: "
             "constant ligand efficiency (kcal/mol per heavy atom). Orange: clinical candidates.", color=INK2,
             fontsize=9)
    fig.subplots_adjust(left=0.045, right=0.99, top=0.78, bottom=0.17, wspace=0.08)
    fig.savefig(out, dpi=170, facecolor=SURF)
    plt.close(fig)
    return len(data)


if __name__ == "__main__":
    stats, points = (json.load(open(p)) for p in sys.argv[1:3])
    write_csv(compounds(points))
    print("ok", plot(stats, points))
