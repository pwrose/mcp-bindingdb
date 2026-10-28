"""Potency against size for BACE1 inhibitors, one panel per period of first publication.

Each compound is plotted once, at its best exact ('=') Ki, Kd or IC50 against human BACE1 (target 5093)
and its heavy-atom count (compound_property, RDKit, largest fragment). Dashed lines are constant ligand
efficiency, LE = 1.37 * pAffinity / heavy atoms (kcal/mol per heavy atom).

    python plot_bace1_efficiency.py [path/to/bindingdb_202610.duckdb]

The query result is cached in bace1_best_affinity.csv, so the plot can be redrawn without the database.
Needs matplotlib (and duckdb for the first run).
"""
import csv
import os
import statistics
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "bace1_best_affinity.csv"
SQL = """
WITH best AS (
  SELECT monomerid, max(p_affinity) AS p_affinity, min(year) AS first_year
  FROM activity
  WHERE polymerid = 5093 AND unit = 'nM' AND relation = '=' AND affinity_type IN ('Ki', 'IC50', 'Kd')
  GROUP BY monomerid
)
SELECT monomerid, p_affinity, first_year, heavy_atoms
FROM best JOIN compound_property USING (monomerid)
WHERE first_year IS NOT NULL
ORDER BY monomerid
"""
PERIODS = [(2001, 2004), (2005, 2009), (2010, 2014), (2015, 2019), (2020, 2026)]
CLINICAL = {50580216: "verubecestat", 50510823: "elenbecestat"}
SURF, INK, INK2, GRID, CLOUD = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1", "#d9d8d3"
BLUE, ORANGE = "#2a78d6", "#eb6834"

if not os.path.exists(CSV):
    import duckdb
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/GitRepositories/mcp-bindingdb/data/bindingdb_202610.duckdb")
    rows = duckdb.connect(db, read_only=True).execute(SQL).fetchall()
    with open(CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["monomerid", "p_affinity", "first_year", "heavy_atoms"])
        w.writerows(rows)
data = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(open(CSV))]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2})
fig, axs = plt.subplots(1, len(PERIODS), figsize=(17, 4.6), sharex=True, sharey=True, facecolor=SURF)
xs = [10, 85]
for ax, (start, end) in zip(axs, PERIODS):
    mine = [d for d in data if start <= d["first_year"] <= end]
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
        if int(d["monomerid"]) in CLINICAL:
            ax.scatter([d["heavy_atoms"]], [d["p_affinity"]], s=46, color=ORANGE, edgecolor=SURF, lw=1.5, zorder=5)
            ax.annotate(CLINICAL[int(d["monomerid"])], (d["heavy_atoms"], d["p_affinity"]), xytext=(8, 10),
                        textcoords="offset points", color=INK, fontsize=9,
                        arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.8})
    le_median = statistics.median(1.37 * d["p_affinity"] / d["heavy_atoms"] for d in mine)
    ax.set_title(f"{start}–{end}", loc="left", color=INK, fontsize=12, fontweight="bold", pad=20)
    ax.text(0, 1.015, f"{len(mine):,} compounds · median LE {le_median:.2f}", transform=ax.transAxes,
            color=INK2, fontsize=9, va="bottom")
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
fig.text(0.01, 0.015, "Blue: compounds first published in the period; gray: all periods. Dashed lines: constant "
         "ligand efficiency (kcal/mol per heavy atom). Orange: clinical candidates.", color=INK2, fontsize=9)
fig.subplots_adjust(left=0.045, right=0.99, top=0.78, bottom=0.17, wspace=0.08)
fig.savefig("bace1_efficiency_by_period.png", dpi=170, facecolor=SURF)
print("ok", len(data))
