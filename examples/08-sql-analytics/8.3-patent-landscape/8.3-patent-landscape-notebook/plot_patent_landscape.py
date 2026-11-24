"""Code 1: Draw the four patent-landscape figures from the run_sql results, from the notebook 8.3-patent-landscape-notebook.ipynb.

Written by claude-opus-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""Figures for Example 8.3 (patent landscape), drawn from the run_sql results.

Each function takes the structured result of one run_sql call ({"rows": [...]}) and writes a PNG.
Run as a script, it reads the results saved with --save from a folder:
    python plot_patent_landscape.py <results_dir> <out_dir>
"""
import json
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, GRAY = "#2a78d6", "#eb6834", "#8a8984"
TXT, TXT2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c9c8c3",
    "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.titleweight": "bold", "axes.titlesize": 11})

CLASSES = [("Kinase", "Kinases"), ("GPCR", "GPCRs"), ("Epigenetic", "Epigenetic"), ("Protease", "Proteases"),
           ("Ion", "Ion channels"), ("PDE", "Phosphodiesterases"), ("NR", "Nuclear receptors"),
           ("Viral", "Viral targets"), ("E3", "E3 ligase / degrader"), ("IO", "Immuno-onc. / innate imm."),
           ("Phosphatase", "Phosphatases (SHP2…)"), ("Other", "Other enzymes & proteins")]

SHORT = {  # short labels for long UniProt target names
    "Q92918": "HPK1 (MAP4K1)", "P01116": "KRAS", "P0DTC1": "SARS-CoV-2 pp1a (Mpro)",
    "P0DTD1": "SARS-CoV-2 pp1ab", "Q13546": "RIPK1", "Q06124": "SHP2 (PTPN11)", "Q96SW2": "Cereblon (CRBN)",
    "P28223": "5-HT2A receptor", "Q86WV6": "STING", "P07949": "RET", "Q9NWZ3": "IRAK4", "P23743": "DGKα",
    "P29274": "Adenosine A2a receptor", "P56817": "BACE1", "Q9Y233": "PDE10A", "Q15858": "Nav1.7 (SCN9A)",
    "P43405": "SYK", "P51449": "RORγt", "O43613": "Orexin OX1R", "O43614": "Orexin OX2R",
    "O00329": "PI3Kδ", "P21453": "S1P1 receptor", "Q06187": "BTK", "P11309": "PIM1", "P35968": "VEGFR2 (KDR)",
    "P08581": "c-MET", "Q9Y5Y4": "CRTH2 (DP2)", "P27487": "DPP-4", "Q99572": "P2X7", "Q8NER1": "TRPV1",
    "P29597": "TYK2", "P23458": "JAK1", "O60674": "JAK2", "P00533": "EGFR", "Q99685": "MAGL",
    "P05177": "CYP1A2", "Q12809": "hERG",
}


def _label(row):
    name = SHORT.get(row["tkey"], row["target"])
    if name.startswith("Programmed cell death 1"):
        return "PD-1 / PD-L1"
    if name.startswith("Cyclin-dependent kinase 2/"):
        return "CDK2 / cyclin E1"
    if name.startswith("DNA damage-binding protein 1/Protein cereblon"):
        return "DDB1–cereblon"
    return name if len(name) <= 28 else name[:27] + "…"


def fig1_growth(result, out):
    """Source documents and distinct compounds per year, patents vs other sources."""
    docs, cpds = defaultdict(dict), defaultdict(dict)
    for r in result["rows"]:
        docs[r["source"]][r["year"]] = r["documents"]
        cpds[r["source"]][r["year"]] = r["compounds"]
    years = list(range(2005, 2027))
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
    for ax, d, ttl, yl, sc in [(axs[0], docs, "Source documents curated per year", "documents", 1),
                               (axs[1], cpds, "Distinct compounds per year", "compounds (thousands)", 1000)]:
        ax.plot(years, [d["other"].get(y, 0) / sc for y in years], color=GRAY, lw=2, marker="o", ms=4)
        ax.plot(years, [d["patent"].get(y, 0) / sc for y in years], color=BLUE, lw=2, marker="o", ms=4)
        ax.axvspan(2023.5, 2026.5, color="#f3f2ee", zorder=0)
        ax.set_title(ttl, loc="left", color=TXT)
        ax.set_ylabel(yl)
        ax.set_xticks(range(2005, 2027, 3))
        ax.text(2013.2, d["patent"][2017] / sc * 1.04, "patents", color=BLUE, fontsize=9, weight="bold")
        gy = d["other"][2005] * 0.82 if sc == 1 else d["other"][2010] * 1.06  # below / above the gray line
        ax.text(2005.3, gy / sc, "journal articles & other", color=GRAY, fontsize=9, weight="bold")
    axs[0].text(2023.7, max(docs["other"].values()) * 0.93, "curation lag\n(articles; 2026 partial)",
                fontsize=8, color=TXT2)
    fig.tight_layout()
    fig.savefig(f"{out}/fig1_growth.png", dpi=170)
    plt.close(fig)


def fig2_class_share(result, out, last_year=2025):
    """Share of patents per year by the class of their lead target (small multiples)."""
    d = defaultdict(dict)
    for r in result["rows"]:
        d[r["class"]][r["year"]] = r["patents"]
    yrs = list(range(2013, last_year + 1))
    tot = {y: sum(d[c].get(y, 0) for c in d) for y in yrs}
    fig, axs = plt.subplots(3, 4, figsize=(12, 7.2), sharex=True)
    for ax, (k, lab) in zip(axs.flat, CLASSES):
        s = [100 * d[k].get(y, 0) / tot[y] for y in yrs]
        ax.plot(yrs, s, color=BLUE, lw=2)
        ax.fill_between(yrs, s, color=BLUE, alpha=0.08)
        ax.set_title(lab, loc="left", fontsize=10, color=TXT)
        ax.set_ylim(0, max(s) * 1.25)
        ax.set_xticks([2013, 2017, 2021, 2025])
        ax.tick_params(labelsize=8)
        ax.text(yrs[-1], s[-1], f" {s[-1]:.1f}%", fontsize=8, color=TXT2, va="center")
    fig.supylabel("% of patents (by lead target)", color=TXT2, fontsize=10)
    fig.suptitle(f"Target-class mix of BindingDB patents, 2013–{last_year} (each panel has its own y-scale)",
                 x=0.01, ha="left", fontsize=12, weight="bold")
    fig.tight_layout()
    fig.savefig(f"{out}/fig2_class_share.png", dpi=170)
    plt.close(fig)


def fig3_rise_fall(result, out, n=12):
    """The n lead targets that gained and the n that lost the most patent share between the windows."""
    rows = sorted(result["rows"], key=lambda r: r["delta_pp"])
    picked = rows[:n] + rows[-n:]
    te, tl = picked[0]["early_total"], picked[0]["late_total"]
    fig, ax = plt.subplots(figsize=(9, 7.6))
    yy = np.arange(len(picked))
    ax.barh(yy, [r["delta_pp"] for r in picked], color=[BLUE if r["delta_pp"] > 0 else ORANGE for r in picked],
            height=0.7)
    ax.set_yticks(yy, [_label(r) for r in picked], fontsize=9)
    ax.axvline(0, color="#9a9994", lw=1)
    for i, r in enumerate(picked):
        pos = r["delta_pp"] > 0
        ax.text(r["delta_pp"] + (0.04 if pos else -0.04), i, f"{r['early']} → {r['late']}", va="center",
                ha="left" if pos else "right", fontsize=8, color=TXT2)
    lo, hi = picked[0]["delta_pp"], picked[-1]["delta_pp"]
    ax.set_xlim(lo - 0.45, hi + 0.45)
    ax.set_xlabel("change in share of patents (percentage points), 2013–17 → 2022–26")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Lead targets gaining and losing patent share\n(labels: patents in each window; "
                 f"{te:,} and {tl:,} patents in all)", loc="left", color=TXT)
    fig.tight_layout()
    fig.savefig(f"{out}/fig3_rise_fall.png", dpi=170)
    plt.close(fig)


def fig4_potency_mw(hist, mw, potency, out):
    """Left: p_affinity distributions, patent vs other. Right: share of patent compounds above 500 Da."""
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.9))
    ax = axs[0]
    x = np.array([r["bin"] for r in hist["rows"]]) + 0.25
    pat = np.array([r["patent"] for r in hist["rows"]], float)
    oth = np.array([r["other"] for r in hist["rows"]], float)
    ax.plot(x, 100 * oth / oth.sum(), color=GRAY, lw=2, drawstyle="steps-mid")
    ax.plot(x, 100 * pat / pat.sum(), color=BLUE, lw=2, drawstyle="steps-mid")
    ax.set_xlim(3, 11.5)
    ax.set_xlabel("pAffinity (−log10 M; Ki, Kd, IC50, EC50; exact values)")
    ax.set_ylabel("% of measurements")
    med = {(r["affinity_type"], r["source"]): r["median_p_affinity"] for r in potency["rows"]}
    gap = med[("IC50", "patent")] - med[("IC50", "other")]
    ax.set_title(f"Patent data are ~{gap:.1f} log units more potent", loc="left", color=TXT)
    top = max(100 * pat / pat.sum())
    ax.text(8.9, top * 0.85, f"patents\nmedian pIC50 {med[('IC50', 'patent')]:.1f}", color=BLUE, fontsize=9,
            weight="bold")
    ax.text(8.9, top * 0.55, f"articles & other\nmedian pIC50 {med[('IC50', 'other')]:.1f}", color=GRAY,
            fontsize=9, weight="bold")
    ax = axs[1]
    rows = sorted((r for r in mw["rows"] if r["source"] == "patent"), key=lambda r: r["year"])
    my = [r["year"] for r in rows]
    g500 = [r["pct_mw_over_500"] for r in rows]
    ax.plot(my, g500, color=BLUE, lw=2, marker="o", ms=4)
    for r in rows:
        if r["year"] in (2014, 2025):
            ax.text(r["year"], r["pct_mw_over_500"] + (-6.5 if r["year"] == 2014 else 1.2),
                    f"{r['pct_mw_over_500']:.0f}%\n(median MW {r['median_mw']:.0f})", ha="center", fontsize=8,
                    color=TXT2)
    ax.set_ylim(15, 50)
    ax.set_ylabel("% of patent compounds with MW > 500")
    ax.set_title("Patented molecules keep getting bigger", loc="left", color=TXT)
    ax.set_xticks(range(2013, 2027, 2))
    fig.tight_layout()
    fig.savefig(f"{out}/fig4_potency_mw.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    load = lambda name: json.load(open(f"{src}/{name}.json"))
    fig1_growth(load("r3"), out)
    fig2_class_share(load("r6"), out)
    fig3_rise_fall(load("r7"), out)
    fig4_potency_mw(load("r11"), load("r12"), load("r10"), out)
    print("ok")
