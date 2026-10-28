"""Imatinib's targets (Ki/Kd/IC50 <= 1 uM) linked by shared <= 1 uM BindingDB ligands.

Data from mcp-bindingdb (BindingDB 202610): imatinib's best value per human target from
find_targets_for_compound, and the number of other compounds that hit both targets of a pair at
<= 1 uM from run_sql. Writes imatinib_target_network.png next to this script.
"""
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imatinib_target_network.png")
MIN_SHARED = 10

# uniprot: (gene, class, imatinib best nM, affinity type, other <= 1 uM ligands)
T = {
    "P04626": ("ERBB2", "rtk", 0.06, "IC50", 3508), "P00533": ("EGFR", "rtk", 0.11, "IC50", 10921),
    "Q08345": ("DDR1", "rtk", 0.7, "Kd", 1763), "P00519": ("ABL1", "ntk", 1.0, "Kd", 2555),
    "P16234": ("PDGFRA", "rtk", 2, "Ki", 932), "P10721": ("KIT", "rtk", 3, "Kd", 3818),
    "P09619": ("PDGFRB", "rtk", 3, "Ki", 2237), "P42684": ("ABL2", "ntk", 10, "Kd", 118),
    "P07333": ("CSF1R", "rtk", 10, "Kd", 2645), "Q16832": ("DDR2", "rtk", 15, "Kd", 526),
    "P00918": ("CA2", "ca", 30.2, "Ki", 7760), "P00915": ("CA1", "ca", 31.9, "Ki", 5195),
    "P16083": ("NQO2", "ox", 39, "Ki", 190), "P06239": ("LCK", "ntk", 40, "Kd", 1593),
    "Q96FL8": ("SLC47A1", "tr", 40, "IC50", 8), "Q16790": ("CA9", "ca", 75.7, "Ki", 5273),
    "P43166": ("CA7", "ca", 109, "Ki", 1441), "P36888": ("FLT3", "rtk", 131, "IC50", 3480),
    "P07948": ("LYN", "ntk", 220, "IC50", 364), "Q86VL8": ("SLC47A2", "tr", 350, "IC50", 4),
    "Q8TBX8": ("PIP4K2C", "kin", 380, "Kd", 294), "P23280": ("CA6", "ca", 392, "Ki", 273),
    "Q9ULX7": ("CA14", "ca", 468, "Ki", 636), "Q9UNQ0": ("ABCG2", "tr", 500, "IC50", 503),
    "P51451": ("BLK", "ntk", 520, "Kd", 237), "P07451": ("CA3", "ca", 528, "Ki", 115),
    "P08183": ("ABCB1", "tr", 580, "IC50", 564), "Q8NE63": ("HIPK4", "kin", 960, "Kd", 37),
    "O43570": ("CA12", "ca", 980, "Ki", 4524), "O14976": ("GAK", "kin", 1000, "Kd", 237),
}
SUSPECT = {"ERBB2", "EGFR"}  # single 2022 report, at odds with imatinib's known profile

# Pairs sharing >= MIN_SHARED other <= 1 uM ligands (gene, gene, shared compounds)
E = """CA1 CA2 4986;CA2 CA9 4245;CA12 CA9 3912;CA12 CA2 3564;CA1 CA9 3041;CA12 CA1 2649;EGFR ERBB2 1547;
CA2 CA7 1317;CA1 CA7 1040;CA12 CA7 858;CA7 CA9 804;CA2 CA14 564;CA9 CA14 560;KIT FLT3 543;CA12 CA14 533;
DDR1 DDR2 411;CA7 CA14 401;CA1 CA14 395;KIT PDGFRA 347;CSF1R KIT 345;PDGFRB PDGFRA 338;PDGFRB KIT 315;
CA2 CA6 246;CA6 CA7 245;CA6 CA9 240;CA12 CA6 229;CSF1R PDGFRB 221;CA1 CA6 209;CA6 CA14 197;CSF1R FLT3 176;
PDGFRB FLT3 173;CSF1R PDGFRA 165;LCK LYN 165;ABL1 KIT 161;PDGFRA FLT3 140;EGFR LCK 136;EGFR PDGFRB 136;
CA3 CA6 113;ABL1 LCK 113;CA3 CA7 111;CA3 CA9 111;CA12 CA3 110;EGFR CSF1R 109;ABL1 ABL2 109;CA3 CA14 108;
CA2 CA3 106;LCK BLK 101;ABL1 LYN 98;LCK KIT 96;CA1 CA3 95;LCK FLT3 88;LYN BLK 88;ABL1 DDR1 87;KIT ABL2 86;
ABL1 PDGFRB 85;ABL1 DDR2 82;ABL1 EGFR 82;EGFR BLK 81;ABL1 FLT3 78;KIT DDR1 76;ABL1 CSF1R 70;LCK PDGFRB 68;
EGFR FLT3 66;ABL1 PDGFRA 66;LCK CSF1R 63;EGFR KIT 59;ABL1 BLK 55;FLT3 BLK 54;CSF1R LYN 53;LCK PDGFRA 51;
KIT DDR2 50;EGFR PDGFRA 49;LYN FLT3 49;LYN KIT 49;EGFR LYN 47;PDGFRB DDR1 46;FLT3 DDR1 45;CSF1R DDR1 44;
LYN PDGFRB 44;PDGFRB BLK 43;GAK EGFR 42;LCK DDR1 41;KIT BLK 39;CSF1R BLK 39;PDGFRA DDR1 37;CSF1R DDR2 35;
LYN PDGFRA 35;LYN DDR1 34;PDGFRB DDR2 34;LCK DDR2 33;FLT3 DDR2 33;BLK DDR1 33;PDGFRA BLK 33;PDGFRA DDR2 31;
LYN ABL2 30;LCK ABL2 29;ERBB2 BLK 28;GAK LCK 27;GAK FLT3 27;ABL2 DDR1 27;BLK DDR2 26;ABL2 BLK 26;
FLT3 HIPK4 26;EGFR DDR1 26;ERBB2 LCK 26;GAK ABL1 26;LYN DDR2 26;PDGFRB ABL2 25;ABCB1 ABCG2 25;GAK KIT 25;
GAK BLK 25;GAK PDGFRB 24;EGFR ABL2 23;EGFR DDR2 23;CSF1R ABL2 23;KIT HIPK4 23;CSF1R HIPK4 22;
PDGFRB HIPK4 22;ABL1 ERBB2 22;FLT3 ABL2 21;GAK LYN 21;GAK CSF1R 21;ABL1 HIPK4 21;GAK PDGFRA 20;
ABL2 DDR2 19;LCK HIPK4 19;PDGFRA HIPK4 18;ERBB2 LYN 17;BLK HIPK4 17;GAK DDR1 17;LYN HIPK4 17;
DDR1 HIPK4 16;PDGFRA ABL2 16;EGFR HIPK4 16;GAK ABL2 15;GAK HIPK4 14;ERBB2 PDGFRB 14;ERBB2 FLT3 13;
DDR2 HIPK4 13;GAK DDR2 12;ABL2 HIPK4 11;ABL1 PIP4K2C 11;GAK ERBB2 11;ERBB2 KIT 10;EGFR PIP4K2C 10"""
EDGES = [(a, b, int(n)) for a, b, n in (s.split() for s in E.replace("\n", "").split(";"))]
EDGES = [e for e in EDGES if e[2] >= MIN_SHARED]

GENE = {g: (cls, nm, typ, nlig) for g, cls, nm, typ, nlig in T.values()}
COLOR = {"rtk": "#2a78d6", "ntk": "#eb6834", "kin": "#8a5cc7", "ca": "#1f9a72", "tr": "#b98a12", "ox": "#7a8494"}
CLASS_NAME = {"rtk": "Receptor tyrosine kinase", "ntk": "Non-receptor tyrosine kinase", "kin": "Other kinase",
              "ca": "Carbonic anhydrase", "tr": "Transporter", "ox": "Oxidoreductase (NQO2)"}
TXT, TXT2, EDGE = "#0b0b0b", "#52514e", "#5d6676"


def ring(genes, cx, cy, r, start=90):
    """Place genes clockwise on a circle, starting at `start` degrees."""
    pos = {}
    for i, g in enumerate(genes):
        a = math.radians(start - 360 * i / len(genes))
        pos[g] = (cx + r * math.cos(a), cy + r * math.sin(a), a)
    return pos


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
for a, b, n in sorted(EDGES, key=lambda e: e[2]):
    x1, y1, _ = pos[a]
    x2, y2, _ = pos[b]
    t = min(1.0, math.log10(n / MIN_SHARED) / math.log10(5000 / MIN_SHARED))
    ax.plot([x1, x2], [y1, y2], color=EDGE, lw=0.4 + 4.2 * t, alpha=0.3 + 0.45 * t,
            solid_capstyle="round", zorder=1)

# Nodes: area grows with imatinib's pAffinity at the target; label with gene and imatinib value.
for g, (x, y, a) in pos.items():
    cls, nm, typ, nlig = GENE[g]
    p = 9 - math.log10(nm)
    s = 60 + (p - 6) ** 2 * 55
    ax.scatter(x, y, s=s, color=COLOR[cls], edgecolor="white", linewidth=1.5, zorder=3)
    if g in SUSPECT:
        ax.scatter(x, y, s=s + 260, facecolor="none", edgecolor="#e34948", linewidth=1.2,
                   linestyle=(0, (2, 2)), zorder=2)
    nm_txt = f"{nm:g} nM"
    d = 0.16 + math.sqrt(s) / 700
    lx, ly = x + d * math.cos(a), y + d * math.sin(a)
    ha = "left" if math.cos(a) > 0.3 else "right" if math.cos(a) < -0.3 else "center"
    va = "bottom" if math.sin(a) > 0.3 else "top" if math.sin(a) < -0.3 else "center"
    label = g + ("*" if g in SUSPECT else "")
    ax.text(lx, ly, f"{label}\n{typ} {nm_txt}", ha=ha, va=va, fontsize=9, color=TXT,
            linespacing=1.15, zorder=4, fontweight="bold")

for x, y, t in [(0.0, 1.62, "Kinases"), (2.75, 1.48, "Carbonic anhydrases"),
                (2.75, -0.72, "Transporters and NQO2")]:
    ax.text(x, y, t, ha="center", va="bottom", fontsize=11, color=TXT2, fontweight="bold")

handles = [Line2D([], [], marker="o", ls="", ms=9, mfc=COLOR[k], mec="white", label=CLASS_NAME[k])
           for k in COLOR]
handles += [Line2D([], [], color=EDGE, lw=0.4 + 4.2 * min(1, math.log10(n / MIN_SHARED) / math.log10(500)),
                   alpha=0.3 + 0.45 * min(1, math.log10(n / MIN_SHARED) / math.log10(500)),
                   label=f"{n:,} shared ligands") for n in (10, 100, 1000)]
ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(-0.02, 1.0), frameon=False, fontsize=9)

ax.set_title(f"Imatinib targets (Ki, Kd or IC50 ≤ 1 µM), linked when ≥ {MIN_SHARED} other BindingDB compounds "
             "bind both at ≤ 1 µM", fontsize=12, color=TXT, loc="left", fontweight="bold")
fig.text(0.01, 0.012, "Labels give imatinib's best value per target; node size grows with that affinity. "
         "* ERBB2 and EGFR values come from a single 2022 report and are suspect.\n"
         "MATE1/MATE2 (SLC47A1/2) share 3 ligands, NQO2 at most 4: below the threshold.",
         fontsize=8.5, color=TXT2)
ax.set_xlim(-1.75, 4.05)
ax.set_ylim(-1.85, 1.75)
fig.tight_layout()
fig.savefig(OUT, dpi=160, facecolor="white")
print(OUT, len(EDGES), "edges")
