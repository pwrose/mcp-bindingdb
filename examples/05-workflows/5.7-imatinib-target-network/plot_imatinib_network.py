"""Imatinib's targets (Ki/Kd/IC50 <= 1 uM) linked by shared <= 1 uM BindingDB ligands.

Data from mcp-bindingdb (BindingDB 202611): imatinib's best value per target from
find_targets_for_compound, and the number of other compounds that hit both targets of a pair at
<= 1 uM from run_sql. Writes imatinib_target_network.png next to this script.
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

MIN_SHARED = 10
# uniprot -> (gene, class)
GENES = {
    "P04626": ("ERBB2", "rtk"), "P00533": ("EGFR", "rtk"), "Q08345": ("DDR1", "rtk"), "Q16832": ("DDR2", "rtk"),
    "P16234": ("PDGFRA", "rtk"), "P09619": ("PDGFRB", "rtk"), "P10721": ("KIT", "rtk"),
    "P07333": ("CSF1R", "rtk"), "P36888": ("FLT3", "rtk"),
    "P00519": ("ABL1", "ntk"), "P42684": ("ABL2", "ntk"), "P06239": ("LCK", "ntk"), "P07948": ("LYN", "ntk"),
    "P51451": ("BLK", "ntk"),
    "Q8TBX8": ("PIP4K2C", "kin"), "Q8NE63": ("HIPK4", "kin"), "O14976": ("GAK", "kin"),
    "P00918": ("CA2", "ca"), "P00915": ("CA1", "ca"), "Q16790": ("CA9", "ca"), "P43166": ("CA7", "ca"),
    "P23280": ("CA6", "ca"), "Q9ULX7": ("CA14", "ca"), "P07451": ("CA3", "ca"), "O43570": ("CA12", "ca"),
    "Q96FL8": ("SLC47A1", "tr"), "Q86VL8": ("SLC47A2", "tr"), "Q9UNQ0": ("ABCG2", "tr"), "P08183": ("ABCB1", "tr"),
    "P16083": ("NQO2", "ox"),
}
SUSPECT = {"ERBB2", "EGFR"}  # single 2022 report, at odds with imatinib's known profile
COLOR = {"rtk": "#2a78d6", "ntk": "#eb6834", "kin": "#8a5cc7", "ca": "#1f9a72", "tr": "#b98a12", "ox": "#7a8494"}
CLASS_NAME = {"rtk": "Receptor tyrosine kinase", "ntk": "Non-receptor tyrosine kinase", "kin": "Other kinase",
              "ca": "Carbonic anhydrase", "tr": "Transporter", "ox": "Oxidoreductase (NQO2)"}
TXT, TXT2, EDGE = "#0b0b0b", "#52514e", "#5d6676"


def imatinib_best(targets):
    """gene -> (best nM, affinity type) over the human entries of each UniProt accession (mutants and
    constructs folded into the accession), from find_targets_for_compound's result."""
    best = {}
    for r in targets["rows"]:
        if r["organism"] != "Homo sapiens" or r["polymerid"] is None:
            continue
        acc = r["uniprot_raw"].split("[")[0]
        if acc in GENES and (GENES[acc][0] not in best or r["value"] < best[GENES[acc][0]][0]):
            best[GENES[acc][0]] = (r["value"], r["affinity_type"])
    return best


def network(sql):
    """(other potent ligands per gene, edges (gene, gene, shared) with at least MIN_SHARED), from the SQL rows."""
    nlig = {GENES[r["a"]][0]: r["n"] for r in sql["rows"] if r["kind"] == "ligands"}
    pairs = [(GENES[r["a"]][0], GENES[r["b"]][0], r["n"]) for r in sql["rows"] if r["kind"] == "pair"]
    return nlig, [e for e in pairs if e[2] >= MIN_SHARED], pairs


def ring(genes, cx, cy, r, start=90):
    """Place genes clockwise on a circle, starting at `start` degrees."""
    pos = {}
    for i, g in enumerate(genes):
        a = math.radians(start - 360 * i / len(genes))
        pos[g] = (cx + r * math.cos(a), cy + r * math.sin(a), a)
    return pos


def plot_network(targets, sql, out="imatinib_target_network.png"):
    best = imatinib_best(targets)
    _, edges, pairs = network(sql)
    cls = {g: c for g, c in GENES.values()}
    # Kinases on one ring, grouped by family; carbonic anhydrases on a second ring; the rest below.
    kinases = ["EGFR", "ERBB2", "DDR1", "DDR2", "PDGFRA", "PDGFRB", "KIT", "CSF1R", "FLT3",
               "ABL1", "ABL2", "LCK", "LYN", "BLK", "GAK", "HIPK4", "PIP4K2C"]
    cas = ["CA2", "CA1", "CA3", "CA6", "CA14", "CA7", "CA12", "CA9"]
    pos = ring(kinases, 0.0, 0.0, 1.0)
    pos.update(ring(cas, 2.75, 0.5, 0.6))
    pos.update({"ABCB1": (2.5, -0.95, math.pi), "ABCG2": (3.0, -0.95, 0.0),
                "SLC47A1": (2.5, -1.3, math.pi), "SLC47A2": (3.0, -1.3, 0.0),
                "NQO2": (2.5, -1.65, math.pi)})
    fig, ax = plt.subplots(figsize=(13, 8.6))
    ax.set_aspect("equal")
    ax.axis("off")
    # Edges: width and darkness grow with log10(shared ligands); weakest drawn first.
    for a, b, n in sorted(edges, key=lambda e: e[2]):
        x1, y1, _ = pos[a]
        x2, y2, _ = pos[b]
        t = min(1.0, math.log10(n / MIN_SHARED) / math.log10(5000 / MIN_SHARED))
        ax.plot([x1, x2], [y1, y2], color=EDGE, lw=0.4 + 4.2 * t, alpha=0.3 + 0.45 * t,
                solid_capstyle="round", zorder=1)
    # Nodes: area grows with imatinib's pAffinity at the target; label with gene and imatinib value.
    for g, (x, y, a) in pos.items():
        nm, typ = best[g]
        p = 9 - math.log10(nm)
        s = 60 + (p - 6) ** 2 * 55
        ax.scatter(x, y, s=s, color=COLOR[cls[g]], edgecolor="white", linewidth=1.5, zorder=3)
        if g in SUSPECT:
            ax.scatter(x, y, s=s + 260, facecolor="none", edgecolor="#e34948", linewidth=1.2,
                       linestyle=(0, (2, 2)), zorder=2)
        d = 0.16 + math.sqrt(s) / 700
        lx, ly = x + d * math.cos(a), y + d * math.sin(a)
        ha = "left" if math.cos(a) > 0.3 else "right" if math.cos(a) < -0.3 else "center"
        va = "bottom" if math.sin(a) > 0.3 else "top" if math.sin(a) < -0.3 else "center"
        ax.text(lx, ly, f"{g}{'*' if g in SUSPECT else ''}\n{typ} {nm:g} nM", ha=ha, va=va, fontsize=9,
                color=TXT, linespacing=1.15, zorder=4, fontweight="bold")
    for x, y, t in [(0.0, 1.62, "Kinases"), (2.75, 1.48, "Carbonic anhydrases"),
                    (2.75, -0.72, "Transporters and NQO2")]:
        ax.text(x, y, t, ha="center", va="bottom", fontsize=11, color=TXT2, fontweight="bold")
    handles = [Line2D([], [], marker="o", ls="", ms=9, mfc=COLOR[k], mec="white", label=CLASS_NAME[k])
               for k in COLOR]
    handles += [Line2D([], [], color=EDGE, lw=0.4 + 4.2 * min(1, math.log10(n / MIN_SHARED) / math.log10(500)),
                       alpha=0.3 + 0.45 * min(1, math.log10(n / MIN_SHARED) / math.log10(500)),
                       label=f"{n:,} shared ligands") for n in (10, 100, 1000)]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, 1.0), frameon=False, fontsize=9)
    ax.set_title(f"Imatinib targets (Ki, Kd or IC50 ≤ 1 µM), linked when ≥ {MIN_SHARED} other BindingDB "
                 "compounds bind both at ≤ 1 µM", fontsize=12, color=TXT, loc="left", fontweight="bold")
    shared = {frozenset((a, b)): n for a, b, n in pairs}
    mate, nqo = shared.get(frozenset(("SLC47A1", "SLC47A2")), 0), max(
        [n for k, n in shared.items() if "NQO2" in k] or [0])
    fig.text(0.01, 0.012, "Labels give imatinib's best value per target; node size grows with that affinity. "
             "* ERBB2 and EGFR values come from a single 2022 report and are suspect.\n"
             f"MATE1/MATE2 (SLC47A1/2) share {mate} ligands, NQO2 at most {nqo}: below the threshold.",
             fontsize=8.5, color=TXT2)
    ax.set_xlim(-1.75, 4.05)
    ax.set_ylim(-1.85, 1.75)
    fig.tight_layout()
    fig.savefig(out, dpi=160, facecolor="white")
    plt.close(fig)
    return out


def summarize(targets, sql):
    """Print group statistics used in the answer."""
    best = imatinib_best(targets)
    nlig, edges, pairs = network(sql)
    cls = {g: c for g, c in GENES.values()}
    kin = {g for g in best if cls[g] in ("rtk", "ntk", "kin")}
    ca = {g for g in best if cls[g] == "ca"}
    sh = {frozenset((a, b)): n for a, b, n in pairs}
    for name, grp in (("kinases", kin), ("CAs", ca)):
        ps = [(k, n) for k, n in sh.items() if k <= grp]
        print(name, len(grp), "pairs>=10:", sum(1 for _, n in ps if n >= MIN_SHARED), "of", len(grp) * (len(grp) - 1) // 2)
    cross = sorted(((n, tuple(sorted(k))) for k, n in sh.items() if len(k & kin) == 1 and len(k & ca) == 1), reverse=True)
    print("kinase-CA max", cross[:3])
    print("top", sorted(((n, tuple(sorted(k))) for k, n in sh.items()), reverse=True)[:12])
    print("ABL1", sorted(((n, tuple(sorted(k - {'ABL1'}))[0]) for k, n in sh.items() if 'ABL1' in k), reverse=True)[:5],
          sum(1 for k, n in sh.items() if 'ABL1' in k and k <= kin and n >= MIN_SHARED))
    print("PIP4K2C", [(tuple(sorted(k)), n) for k, n in sh.items() if 'PIP4K2C' in k and n >= 5])
    print("ABCB1-ABCG2", sh.get(frozenset(("ABCB1", "ABCG2"))))
    print("ABC others", sorted([(n, tuple(sorted(k))) for k, n in sh.items() if (('ABCB1' in k) or ('ABCG2' in k)) and not {'ABCB1','ABCG2'} <= k], reverse=True)[:4])
    print("MATE", sh.get(frozenset(("SLC47A1", "SLC47A2"))), [nlig.get(g) for g in ("SLC47A1", "SLC47A2")])
    print("NQO2 max", sorted(((n, tuple(sorted(k))) for k, n in sh.items() if 'NQO2' in k), reverse=True)[:2])
    print("nlig EGFR HIPK4", nlig.get("EGFR"), nlig.get("HIPK4"))
    print("edges", len(edges))
