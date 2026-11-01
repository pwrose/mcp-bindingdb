import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

OUT = "./"
BLUE, ORANGE, GRAY, RED = "#2a78d6", "#eb6834", "#8a8984", "#e34948"
TXT, TXT2 = "#0b0b0b", "#52514e"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#c9c8c3",
    "axes.labelcolor": TXT2, "xtick.color": TXT2, "ytick.color": TXT2, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.color": "#ecebe7", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.titleweight": "bold", "axes.titlesize": 11})

# ---------- Fig 1: documents & compounds per year ----------
years = list(range(2005, 2027))
lit_docs = {2005:1218,2006:1282,2007:1634,2008:2228,2009:2009,2010:2313,2011:2047,2012:2158,2013:2060,2014:1855,2015:1726,2016:1906,2017:1883,2018:1741,2019:1727,2020:1810,2021:1799,2022:1604,2023:1283,2024:165,2025:1,2026:0}
pat_docs = {2005:1,2006:1,2012:1,2013:234,2014:395,2015:665,2016:663,2017:798,2018:606,2019:774,2020:725,2021:732,2022:644,2023:682,2024:855,2025:940,2026:282}
lit_cpd = {2005:22666,2006:23525,2007:34152,2008:45193,2009:44496,2010:51782,2011:43623,2012:44049,2013:35941,2014:32371,2015:29379,2016:32962,2017:31685,2018:30198,2019:30402,2020:32676,2021:36145,2022:30209,2023:24404,2024:2279,2025:1,2026:0}
pat_cpd = {2005:61,2006:12,2012:267,2013:13196,2014:28114,2015:47590,2016:51907,2017:82399,2018:57818,2019:83836,2020:74380,2021:74404,2022:67477,2023:68629,2024:70616,2025:91525,2026:29640}
fig, axs = plt.subplots(1, 2, figsize=(11, 3.8))
for ax, L, P, ttl, yl in [(axs[0], lit_docs, pat_docs, "Source documents curated per year", "documents"),
                          (axs[1], lit_cpd, pat_cpd, "Distinct compounds per year", "compounds (thousands)")]:
    sc = 1 if yl == "documents" else 1000
    ax.plot(years, [L.get(y, 0)/sc for y in years], color=GRAY, lw=2, marker="o", ms=4)
    ax.plot(years, [P.get(y, 0)/sc for y in years], color=BLUE, lw=2, marker="o", ms=4)
    ax.axvspan(2023.5, 2026.5, color="#f3f2ee", zorder=0)
    ax.set_title(ttl, loc="left", color=TXT); ax.set_ylabel(yl)
    ax.set_xticks(range(2005, 2027, 3))
    ax.text(2013.2, P[2017]/sc*1.02 if sc > 1 else 820, "patents", color=BLUE, fontsize=9, weight="bold")
    ax.text(2005.3, (1050 if sc==1 else L[2010]/sc*1.06), "journal articles & other", color=GRAY, fontsize=9, weight="bold")
axs[0].text(2023.7, 2150, "curation lag\n(articles; 2026 partial)", fontsize=8, color=TXT2)
fig.tight_layout(); fig.savefig(OUT + "fig1_growth.png", dpi=170)

# ---------- Fig 2: target-class share over time (small multiples) ----------
raw = """2013 CYP450 1;2013 E3 1;2013 Epigenetic 5;2013 GPCR 42;2013 Ion 2;2013 Kinase 61;2013 NR 2;2013 Other 76;2013 PDE 6;2013 Protease 23;2013 Transporter 6;2013 Viral 9;
2014 CYP450 3;2014 E3 5;2014 Epigenetic 14;2014 GPCR 73;2014 Ion 6;2014 Kinase 88;2014 NR 6;2014 Other 118;2014 PDE 27;2014 Phosphatase 1;2014 Protease 39;2014 Transporter 7;2014 Viral 8;
2015 CYP450 13;2015 E3 9;2015 Epigenetic 19;2015 GPCR 97;2015 Ion 48;2015 Kinase 140;2015 NR 15;2015 Other 207;2015 PDE 25;2015 Phosphatase 3;2015 Protease 60;2015 Transporter 17;2015 Viral 12;
2016 CYP450 18;2016 E3 13;2016 Epigenetic 26;2016 GPCR 90;2016 IO 5;2016 Ion 30;2016 Kinase 155;2016 NR 13;2016 Other 186;2016 PDE 21;2016 Phosphatase 3;2016 Protease 72;2016 Transporter 11;2016 Viral 20;
2017 CYP450 15;2017 E3 11;2017 Epigenetic 54;2017 GPCR 121;2017 IO 11;2017 Ion 51;2017 Kinase 195;2017 NR 39;2017 Other 194;2017 PDE 28;2017 Phosphatase 2;2017 Protease 63;2017 Transporter 8;2017 Viral 6;
2018 CYP450 9;2018 E3 1;2018 Epigenetic 51;2018 GPCR 71;2018 IO 13;2018 Ion 24;2018 Kinase 159;2018 NR 20;2018 Other 158;2018 PDE 12;2018 Phosphatase 3;2018 Protease 47;2018 Transporter 12;2018 Viral 26;
2019 CYP450 3;2019 E3 9;2019 Epigenetic 58;2019 GPCR 96;2019 IO 17;2019 Ion 26;2019 Kinase 182;2019 NR 41;2019 Other 238;2019 PDE 16;2019 Phosphatase 10;2019 Protease 45;2019 Transporter 12;2019 Viral 21;
2020 CYP450 1;2020 E3 14;2020 Epigenetic 58;2020 GPCR 84;2020 IO 23;2020 Ion 41;2020 Kinase 190;2020 NR 28;2020 Other 202;2020 PDE 19;2020 Phosphatase 5;2020 Protease 39;2020 Transporter 9;2020 Viral 12;
2021 CYP450 3;2021 E3 21;2021 Epigenetic 53;2021 GPCR 62;2021 IO 38;2021 Ion 21;2021 Kinase 204;2021 NR 31;2021 Other 211;2021 PDE 15;2021 Phosphatase 11;2021 Protease 41;2021 Transporter 7;2021 Viral 14;
2022 CYP450 6;2022 E3 24;2022 Epigenetic 57;2022 GPCR 51;2022 IO 33;2022 Ion 14;2022 Kinase 175;2022 NR 13;2022 Other 184;2022 PDE 17;2022 Phosphatase 9;2022 Protease 19;2022 Transporter 2;2022 Viral 40;
2023 CYP450 8;2023 E3 25;2023 Epigenetic 40;2023 GPCR 61;2023 IO 33;2023 Ion 21;2023 Kinase 196;2023 NR 12;2023 Other 201;2023 PDE 6;2023 Phosphatase 22;2023 Protease 37;2023 Transporter 7;2023 Viral 13;
2024 CYP450 15;2024 E3 21;2024 Epigenetic 47;2024 GPCR 70;2024 IO 33;2024 Ion 29;2024 Kinase 214;2024 NR 10;2024 Other 312;2024 PDE 12;2024 Phosphatase 19;2024 Protease 28;2024 Transporter 11;2024 Viral 34;
2025 CYP450 17;2025 E3 33;2025 Epigenetic 74;2025 GPCR 67;2025 IO 19;2025 Ion 31;2025 Kinase 263;2025 NR 14;2025 Other 315;2025 PDE 15;2025 Phosphatase 19;2025 Protease 42;2025 Transporter 7;2025 Viral 24"""
d = defaultdict(dict)
for item in raw.replace("\n", "").split(";"):
    y, c, n = item.split(); d[c][int(y)] = int(n)
yrs = list(range(2013, 2026))
tot = {y: sum(d[c].get(y, 0) for c in d) for y in yrs}
show = [("Kinase", "Kinases"), ("GPCR", "GPCRs"), ("Epigenetic", "Epigenetic"), ("Protease", "Proteases"),
        ("Ion", "Ion channels"), ("PDE", "Phosphodiesterases"), ("NR", "Nuclear receptors"), ("Viral", "Viral targets"),
        ("E3", "E3 ligase / degrader"), ("IO", "Immuno-onc. / innate imm."), ("Phosphatase", "Phosphatases (SHP2…)"), ("Other", "Other enzymes & proteins")]
fig, axs = plt.subplots(3, 4, figsize=(12, 7.2), sharex=True)
for ax, (k, lab) in zip(axs.flat, show):
    s = [100*d[k].get(y, 0)/tot[y] for y in yrs]
    ax.plot(yrs, s, color=BLUE, lw=2); ax.fill_between(yrs, s, color=BLUE, alpha=0.08)
    ax.set_title(lab, loc="left", fontsize=10, color=TXT); ax.set_ylim(0, max(s)*1.25)
    ax.set_xticks([2013, 2017, 2021, 2025]); ax.tick_params(labelsize=8)
    ax.text(2025, s[-1], f" {s[-1]:.1f}%", fontsize=8, color=TXT2, va="center")
fig.supylabel("% of patents (by lead target)", color=TXT2, fontsize=10)
fig.suptitle("Target-class mix of BindingDB patents, 2013–2025 (each panel has its own y-scale)", x=0.01, ha="left", fontsize=12, weight="bold")
fig.tight_layout(); fig.savefig(OUT + "fig2_class_share.png", dpi=170)

# ---------- Fig 3: rising vs falling lead targets ----------
rise = [("HPK1 (MAP4K1)", 0, 44), ("SARS-CoV-2 pp1a (Mpro)", 0, 44), ("SARS-CoV-2 pp1ab", 0, 34), ("Cereblon (CRBN)", 0, 32),
        ("RIPK1", 1, 33), ("PD-1 / PD-L1", 0, 31), ("SHP2 (PTPN11)", 3, 34), ("5-HT2A receptor", 14, 45),
        ("IRAK4", 11, 36), ("TYK2", 9, 33), ("DGKα", 0, 21), ("CDK2 / cyclin E1", 2, 22)]
fall = [("BACE1", 76, 2), ("PDE10A", 51, 2), ("Nav1.7 (SCN9A)", 40, 6), ("Orexin OX2R", 38, 10), ("BTK", 60, 41),
        ("SYK", 24, 6), ("HCV polyprotein", 22, 5), ("S1P1 receptor", 19, 2), ("c-MET", 22, 6), ("PIM1", 19, 3),
        ("κ-opioid receptor", 17, 2), ("11β-HSD1", 16, 1)]
TE, TL = 2755, 3403
rows = [(n, 100*l/TL - 100*e/TE, e, l) for n, e, l in rise] + [(n, 100*l/TL - 100*e/TE, e, l) for n, e, l in fall]
rows.sort(key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(9, 7.4))
yy = np.arange(len(rows))
ax.barh(yy, [r[1] for r in rows], color=[BLUE if r[1] > 0 else ORANGE for r in rows], height=0.7)
ax.set_yticks(yy, [r[0] for r in rows], fontsize=9); ax.axvline(0, color="#9a9994", lw=1)
for i, r in enumerate(rows):
    ax.text(r[1] + (0.04 if r[1] > 0 else -0.04), i, f"{r[2]} → {r[3]}", va="center",
            ha="left" if r[1] > 0 else "right", fontsize=8, color=TXT2)
ax.set_xlabel("change in share of patents (percentage points), 2013–17 → 2022–26")
ax.set_xlim(-3.3, 1.9); ax.grid(axis="y", visible=False)
ax.set_title("Lead targets gaining and losing patent share\n(labels: number of patents in each window)", loc="left", color=TXT)
fig.tight_layout(); fig.savefig(OUT + "fig3_rise_fall.png", dpi=170)

# ---------- Fig 4: potency + MW ----------
bins = [2,2.5,3,3.5,4,4.5,5,5.5,6,6.5,7,7.5,8,8.5,9,9.5,10,10.5,11,11.5,12,12.5,13]
oth = [4384,4990,22305,40837,162992,146078,298612,176099,217750,179912,190694,148127,130088,75273,50265,19688,8834,3253,1757,448,229,35,49]
pat = [725,772,4028,6251,32777,43538,112723,79698,190329,136196,254843,142259,164093,80526,64315,26575,13072,3431,1834,344,198,26,195]
fig, axs = plt.subplots(1, 2, figsize=(11, 3.9))
ax = axs[0]; x = np.array(bins) + 0.25
ax.plot(x, 100*np.array(oth)/sum(oth), color=GRAY, lw=2, drawstyle="steps-mid")
ax.plot(x, 100*np.array(pat)/sum(pat), color=BLUE, lw=2, drawstyle="steps-mid")
ax.set_xlim(3, 11.5); ax.set_xlabel("pAffinity (−log10 M; Ki, Kd, IC50, EC50)"); ax.set_ylabel("% of measurements")
ax.set_title("Patent data are ~1 log unit more potent", loc="left", color=TXT)
ax.text(8.7, 13.5, "patents\nmedian pIC50 7.0", color=BLUE, fontsize=9, weight="bold")
ax.text(8.7, 9.6, "articles & other\nmedian pIC50 6.0", color=GRAY, fontsize=9, weight="bold")
ax = axs[1]
my = list(range(2013, 2027)); med = [446.2,438.2,447.3,448.3,464.1,455.1,461.2,464.2,466.3,472.2,472.2,473.2,481.2,477.1]
g500 = [27.6,23.5,29.0,28.0,34.1,31.6,32.8,35.6,37.2,39.2,38.3,38.9,42.8,42.0]
ax.plot(my, g500, color=BLUE, lw=2, marker="o", ms=4)
for y, v, m in zip(my, g500, med):
    if y in (2014, 2025): ax.text(y, v + (-5.5 if y==2014 else 1.2), f"{v:.0f}%\n(median MW {m:.0f})", ha="center", fontsize=8, color=TXT2)
ax.set_ylim(15, 50); ax.set_ylabel("% of patent compounds with MW > 500")
ax.set_title("Patented molecules keep getting bigger", loc="left", color=TXT); ax.set_xticks(range(2013, 2027, 2))
fig.tight_layout(); fig.savefig(OUT + "fig4_potency_mw.png", dpi=170)
print("ok")
