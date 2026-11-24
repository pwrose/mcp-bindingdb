"""Drug-likeness radar plots of the five DPP-4 inhibitors (gliptins), one panel per drug.

Input: the get_compound results of the five gliptins (their compound_property values: RDKit,
largest fragment). Each axis is the property divided by its drug-likeness limit (Lipinski: MW 500,
cLogP 5, HBD 5, HBA 10; Veber: TPSA 140, rotatable bonds 10), so the dashed ring at 1 is the limit
and a shape inside it passes every rule. Needs matplotlib.
"""
import csv
import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

AXES = [("mw", "MW", 500), ("clogp", "cLogP", 5), ("tpsa", "TPSA", 140), ("hba", "HBA", 10),
        ("hbd", "HBD", 5), ("rotatable_bonds", "Rot. bonds", 10)]
FIELDS = ["name", "bdbm", "heavy_atoms", "mw", "clogp", "tpsa", "hbd", "hba", "rotatable_bonds", "fsp3", "qed",
          "ro5_violations"]
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BLUE = "#2a78d6"
R_MAX = 1.2


def property_rows(results, names):
    """One row per get_compound result: the compound's id and its compound_property values."""
    return [{"name": name, "bdbm": r["compound"]["bdbm_id"], **{k: r["properties"][k] for k in FIELDS[2:]}}
            for name, r in zip(names, results)]


def plot_radar(results, names, png="gliptin_drug_likeness_radar.png", csv_path="gliptin_properties.csv"):
    rows = property_rows(results, names)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    angles = [2 * math.pi * k / len(AXES) for k in range(len(AXES))]  # clockwise from the top
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
    fig, axs = plt.subplots(1, len(rows), figsize=(3.3 * len(rows), 4.6), subplot_kw={"polar": True},
                            facecolor=SURF)
    for ax, row in zip(axs, rows):
        r = [min(max(float(row[key]), 0) / limit, R_MAX) for key, _, limit in AXES]
        ax.set_facecolor(SURF)
        ax.set_theta_offset(math.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xlim(0, 2 * math.pi)
        ax.set_ylim(0, R_MAX)
        ax.set_yticks([0.5, 1.0])
        ax.set_yticklabels([])
        ax.yaxis.grid(color=GRID, lw=0.8)
        ax.xaxis.grid(color=GRID, lw=0.8)
        ax.spines["polar"].set_visible(False)
        ax.set_xticks(angles)
        ax.set_xticklabels([f"{label}\n≤ {limit}" for _, label, limit in AXES], color=INK2, fontsize=8.5)
        ax.tick_params(axis="x", pad=2)
        ring = angles + [angles[0]]
        ax.plot(ring, [1.0] * len(ring), color=INK2, lw=1, ls=(0, (3, 3)), zorder=2)
        closed_a, closed_r = angles + angles[:1], r + r[:1]
        ax.fill(closed_a, closed_r, color=BLUE, alpha=0.18, zorder=3)
        ax.plot(closed_a, closed_r, color=BLUE, lw=2, zorder=4)
        ax.scatter(angles, r, s=22, color=BLUE, edgecolor=SURF, linewidth=1.2, zorder=5)
        ax.set_title(row["name"], color=INK, fontsize=12, fontweight="bold", pad=30)
        ax.text(0.5, -0.27, f"QED {float(row['qed']):.2f} · {row['heavy_atoms']} heavy atoms",
                transform=ax.transAxes, ha="center", color=INK2, fontsize=9.5)
    fig.suptitle("Drug-likeness of the DPP-4 inhibitors: each property as a fraction of its limit",
                 x=0.012, ha="left", color=INK, fontsize=13.5, fontweight="bold")
    fig.text(0.012, 0.015, "Dashed ring = Lipinski (MW, cLogP, HBD, HBA) and Veber (TPSA, rotatable bonds) "
             "limits; inner ring = half the limit. Properties computed by RDKit for the parent molecule.",
             color=INK2, fontsize=9)
    fig.subplots_adjust(left=0.035, right=0.985, top=0.72, bottom=0.2, wspace=0.6)
    fig.savefig(png, dpi=180, facecolor=SURF)
    plt.close(fig)
    return rows
