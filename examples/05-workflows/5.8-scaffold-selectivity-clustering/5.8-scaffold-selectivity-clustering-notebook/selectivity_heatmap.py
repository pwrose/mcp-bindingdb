"""Code 1: Scan for the densest block, build and cluster the matrix, draw the heat map, write the CSVs, from the notebook 5.8-scaffold-selectivity-clustering-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""Clustered selectivity heat map of the 2-anilino-4-(3-pyridyl)pyrimidines, and the R-group tables in its row order.

Functions take the results of mcp-bindingdb calls (as dicts with a "rows" list): the compounds from
substructure_search, the (compound, kinase) pairs and the block's measurements from run_sql.
"""
import json
import re

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from scipy.cluster.hierarchy import dendrogram, leaves_list, linkage, optimal_leaf_ordering
from scipy.spatial.distance import squareform
from rdkit import Chem, rdBase
from rdkit.Chem import rdRGroupDecomposition as rgd

CORE = "c1ccc(Nc2nccc(-c3cccnc3)n2)cc1"
RANK = {"Kd": 0, "Ki": 1, "IC50": 2, "EC50": 3}
SHORT = {"Tyrosine-protein kinase ABL1": "ABL1",
         "Breakpoint cluster region protein/Tyrosine-protein kinase ABL1": "BCR-ABL",
         "Platelet-derived growth factor receptor alpha/beta": "PDGFR-α/β",
         "Proto-oncogene tyrosine-protein kinase Src": "SRC", "Epidermal growth factor receptor": "EGFR",
         "Protein kinase C alpha type": "PKC-α", "Protein kinase C delta type": "PKC-δ",
         "cAMP-dependent protein kinase catalytic subunit alpha/beta/gamma": "PKA"}


def bicluster(pairs, min_c, min_t):
    """Drop kinases measured on fewer than min_c compounds and compounds measured on fewer than min_t kinases,
    until nothing more drops."""
    p = pairs
    while True:
        tc = p.groupby("tkey").monomerid.nunique()
        p2 = p[p.tkey.isin(tc[tc >= min_c].index)]
        ct = p2.groupby("monomerid").tkey.nunique()
        p2 = p2[p2.monomerid.isin(ct[ct >= min_t].index)]
        if len(p2) == len(p):
            return p2
        p = p2


def scan(*pair_results, settings=((8, 3), (10, 3), (20, 3), (8, 4), (10, 4), (8, 5), (8, 6))):
    """The densest-block scan: for each (min compounds per kinase, min kinases per compound), the block's size."""
    pairs = pd.DataFrame([r for res in pair_results for r in res["rows"]])
    print("full kinase matrix", pairs.monomerid.nunique(), "x", pairs.tkey.nunique(), "filled", len(pairs),
          f"{len(pairs) / (pairs.monomerid.nunique() * pairs.tkey.nunique()):.1%}")
    out = []
    for mc, mt in settings:
        b = bicluster(pairs, mc, mt)
        nc, nt = b.monomerid.nunique(), b.tkey.nunique()
        out.append(dict(min_compounds_per_kinase=mc, min_kinases_per_compound=mt, compounds=nc, kinases=nt,
                        filled=len(b), filled_share=round(len(b) / (nc * nt), 3)))
    df = pd.DataFrame(out)
    print(df.to_string(index=False))
    b = bicluster(pairs, 8, 4)
    print("block ids", sorted(b.monomerid.unique().tolist()))
    print("block targets", sorted(b.tkey.unique().tolist()))
    return df


def make_cells(meas):
    """One cell per (compound, kinase): one affinity type (Kd, then Ki, IC50, EC50), the median of its exact
    values, or of its censored ones when there is no exact value."""
    blk = pd.DataFrame(meas["rows"])
    cells = []
    for (mid, t), g in blk.groupby(["monomerid", "tkey"]):
        typ = min(g.affinity_type, key=RANK.get)
        g = g[g.affinity_type == typ]
        exact = g[g.relation == "="]
        use = exact if len(exact) else g
        nm = float(np.median(use.value))
        cells.append(dict(monomerid=int(mid), tkey=t, affinity_type=typ, median_nm=nm,
                          p_affinity=round(9 - np.log10(nm), 2),
                          censored=bool(len(exact) == 0 and (g.relation == ">").any()),
                          censored_lt=bool(len(exact) == 0 and (g.relation == "<").any()),
                          n_measurements=len(g), n_used=len(use)))
    cells = pd.DataFrame(cells)
    tinfo = blk.groupby("tkey").agg(target_name=("target_name", "first"), organism=("organism", "first"),
                                    uniprot=("uniprot_raw", "first")).reset_index()
    tinfo["short"] = tinfo.target_name.map(SHORT)
    return blk, cells, tinfo


def nan_euclid(A):
    n = len(A)
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            ok = ~np.isnan(A[i]) & ~np.isnan(A[j])
            d = np.sqrt(np.mean((A[i, ok] - A[j, ok]) ** 2) * A.shape[1]) if ok.any() else 10.0
            D[i, j] = D[j, i] = d
    return D


def cluster(cells, drugs):
    """Row and column order: average linkage on the RMS pAffinity difference over shared kinases (rows) and on
    1 - Pearson r (columns); the drugs' rows are put at the top."""
    M = cells.pivot(index="monomerid", columns="tkey", values="p_affinity")
    Dr = nan_euclid(M.values)
    Zr = optimal_leaf_ordering(linkage(squareform(Dr), "average"), squareform(Dr))
    C = M.corr(min_periods=3).fillna(0).values
    Dc = np.clip(1 - C, 0, 2)
    np.fill_diagonal(Dc, 0)
    Zc = optimal_leaf_ordering(linkage(squareform(Dc, checks=False), "average"), squareform(Dc, checks=False))
    rows = [int(x) for x in M.index[leaves_list(Zr)]]
    cols = M.columns[leaves_list(Zc)].tolist()
    if rows.index(next(m for m, n in drugs.items() if n == "Imatinib")) > len(rows) / 2:
        rows = rows[::-1]
    return dict(rows=rows, cols=cols, Zr=Zr, Zc=Zc, row_ids=[int(x) for x in M.index])


def label(m, drugs):
    return drugs.get(m, f"BDBM{m}")


SURF, INK, INK2, MUTED, ND = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8984", "#f0efec"
RAMP = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf",
        "#1c5cab", "#184f95", "#104281", "#0d366b"]


def plot_heatmap(cells, tinfo, cl, drugs, out="kinase_selectivity_heatmap.png", release="202611"):
    cmap = LinearSegmentedColormap.from_list("blue", RAMP)
    lo, hi = 3.0, 8.5
    norm = Normalize(lo, hi)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2})
    short = tinfo.set_index("tkey").short
    rows, cols = cl["rows"], cl["cols"]
    C = cells.set_index(["monomerid", "tkey"])
    nr, nc = len(rows), len(cols)
    fig = plt.figure(figsize=(9.6, 15.2), facecolor=SURF)
    L, B, W, H = 0.17, 0.105, 0.47, 0.78
    ax = fig.add_axes([L, B, W, H])
    axr = fig.add_axes([0.015, B, L - 0.02, H])
    axc = fig.add_axes([L, B + H + 0.004, W, 0.06])
    for a in (ax, axr, axc):
        a.set_facecolor(SURF)
    for i, m in enumerate(rows):
        for j, t in enumerate(cols):
            if (m, t) not in C.index:
                ax.add_patch(Rectangle((j, i), 1, 1, fc=ND, ec=SURF, lw=2))
                ax.text(j + .5, i + .5, "n.d.", ha="center", va="center", fontsize=7, color=MUTED)
                continue
            c = C.loc[(m, t)]
            # a censored cell is "no better than" its bound: drawn at the bottom of the scale, not at the bound
            fc = RAMP[0] if c.censored else cmap(norm(np.clip(c.p_affinity, lo, hi)))
            ax.add_patch(Rectangle((j, i), 1, 1, fc=fc, ec=SURF, lw=2))
            dark = not c.censored and norm(c.p_affinity) > 0.55
            txtc = "#ffffff" if dark else INK
            if c.censored:
                ax.add_patch(Rectangle((j + .04, i + .06), .92, .88, fc="none", ec=INK2 if not dark else "#ffffff",
                                       lw=0, hatch="////", alpha=0.3))
            ax.text(j + .5, i + .5, ("<" if c.censored else "") + f"{c.p_affinity:.1f}", ha="center", va="center",
                    fontsize=8, color=txtc, fontweight="bold" if not c.censored else "normal")
            if c.affinity_type in ("Kd", "Ki"):
                ax.plot(j + .12, i + .2, marker="o" if c.affinity_type == "Kd" else "s", ms=4.5, mfc=txtc,
                        mec=txtc, lw=0)
    ax.set_xlim(0, nc)
    ax.set_ylim(nr, 0)
    ax.set_xticks(np.arange(nc) + .5)
    ax.set_xticklabels([short[t].replace("PDGFR-", "PDGFR\n").replace("BCR-", "BCR-\n") for t in cols],
                       rotation=0, fontsize=9, color=INK)
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_right()
    ax.set_yticks(np.arange(nr) + .5)
    ax.set_yticklabels([f"{i + 1:>2}  {label(m, drugs)}" for i, m in enumerate(rows)], fontsize=8.5, color=INK,
                       family="DejaVu Sans Mono")
    for lab in ax.get_yticklabels():
        if not lab.get_text().split()[-1].startswith("BDBM"):
            lab.set_fontweight("bold")
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    # dendrograms (row order may have been flipped so imatinib/nilotinib sit at the top)
    dr = dendrogram(cl["Zr"], orientation="left", no_plot=True)
    flip = [cl["row_ids"][k] for k in dr["leaves"]] != rows
    for xs, ys in zip(dr["dcoord"], dr["icoord"]):
        ys = np.array(ys) / 10.0
        if flip:
            ys = nr - ys
        axr.plot(-np.array(xs), ys, color=INK2, lw=1)
    axr.set_ylim(nr, 0)
    axr.axis("off")
    dc = dendrogram(cl["Zc"], no_plot=True)
    for xs, ys in zip(dc["icoord"], dc["dcoord"]):
        axc.plot(np.array(xs) / 10.0, ys, color=INK2, lw=1)
    axc.set_xlim(0, nc)
    axc.axis("off")
    fig.text(0.015, 0.975, "Kinase selectivity of 2-anilino-4-(3-pyridyl)pyrimidines", fontsize=14, fontweight="bold")
    fig.text(0.015, 0.960, f"{nr} BindingDB compounds × the {nc} kinases with the densest shared coverage · "
             "median pAffinity per cell", fontsize=9.5, color=INK2)
    cax = fig.add_axes([L, 0.062, W * 0.62, 0.010])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.outline.set_visible(False)
    cb.ax.tick_params(length=0, labelsize=8, colors=INK2)
    cb.set_label("pAffinity = −log10(median affinity / M)   (darker = more potent)", fontsize=8.5, color=INK2)
    key = [Line2D([], [], marker="o", ls="", ms=5, mfc=INK, mec=INK, label="Kd"),
           Line2D([], [], marker="s", ls="", ms=5, mfc=INK, mec=INK, label="Ki"),
           Rectangle((0, 0), 1, 1, fc=RAMP[4], ec="none", label="no glyph: IC50"),
           Rectangle((0, 0), 1, 1, fc=RAMP[0], ec=INK2, lw=0, hatch="////",
                     label="< censored: no activity up to the\n   highest concentration tested"),
           Rectangle((0, 0), 1, 1, fc=ND, ec="none", label="n.d. not measured")]
    fig.legend(handles=key, loc="lower left", bbox_to_anchor=(L + W + 0.02, 0.03), frameon=False, fontsize=8,
               ncol=1, labelcolor=INK2, handlelength=1.4)
    fig.text(0.015, 0.012, f"Source: BindingDB {release} via mcp-bindingdb. Rows: average linkage on RMS pAffinity "
             "difference over shared kinases;\ncolumns: average linkage on 1 − Pearson r. One affinity type per cell "
             "(Kd > Ki > IC50); censored cells cluster at their bound.", fontsize=7.2, color=MUTED, va="bottom")
    fig.savefig(out, dpi=200, facecolor=SURF)
    plt.close(fig)
    return out


def decompose(ss, rows):
    """R-group decomposition of the compounds (SMILES from substructure_search) in `rows` order, on the unmarked
    core: R1 ortho and R3 meta to the anilino NH, R2 the pyridine nitrogen."""
    smi = {r["monomerid"]: r["smiles"] for r in ss["rows"]}
    params = rgd.RGroupDecompositionParameters()
    params.removeHydrogensPostMatch = True
    _quiet = rdBase.BlockLogs()
    d = rgd.RGroupDecomposition(Chem.MolFromSmiles(CORE), params)
    for m in rows:
        assert d.Add(Chem.MolFromSmiles(smi[m])) >= 0, m
    d.Process()
    out = d.GetRGroupsAsRows(asSmiles=True)
    labels = [k for k in out[0] if k != "Core"]
    return labels, out


def fmt_nm(v):
    return f"{v / 1000:.3g} µM" if v >= 1000 else f"{v:.3g} nM"


def _tidy(group):
    """'H' for a hydrogen substituent, as draw_r_group_table writes it."""
    return "H" if group is None or re.fullmatch(r"\[H\]\[\*:\d\]", group) else group


def table_args(cells, tinfo, cl, drugs, ss, bars_for=("ABL1", "PDGFR-α/β", "PKC-α")):
    """Rows for draw_r_group_table, in heat-map order, with the median affinity of the key kinases."""
    rows = cl["rows"]
    labels, dec = decompose(ss, rows)
    C = cells.set_index(["monomerid", "tkey"])
    tk = {s: t for t, s in zip(tinfo.tkey, tinfo.short)}
    table = []
    for i, (m, r) in enumerate(zip(rows, dec), 1):
        bars = []
        for lab in bars_for:
            if (m, tk[lab]) not in C.index:
                continue
            c = C.loc[(m, tk[lab])]
            note = (f"{c.affinity_type} > {fmt_nm(c.median_nm)}" if c.censored
                    else f"{c.affinity_type} {fmt_nm(c.median_nm)}") + (f" ({int(c.n_used)})" if c.n_used > 1 else "")
            bars.append(dict(label=lab, value_nm=round(float(c.median_nm), 3), type=c.affinity_type,
                             faint=bool(c.censored), note=note))
        sub = f"BDBM{m}" if label(m, drugs).startswith("BDBM") is False else ""
        # R3 (meta) becomes R2 in the table; the pyridine N-oxide position (R2) is noted on its row, not a column
        r2 = r.get("R2")
        if r2 not in (None, "H"):
            sub = (sub + " · " if sub else "") + "pyridine N-oxide"
        rg = {"R1": _tidy(r.get("R1")), "R2": _tidy((r.get("R3") or "H").replace("[*:3]", "[*:2]"))}
        table.append(dict(title=f"{i}. {label(m, drugs)}", subtitle=sub, r_groups=rg, bars=bars))
    return dict(labels=labels, core="c1cncc(-c2ccnc(Nc3cc([*:2])ccc3[*:1])n2)c1", rows=table, dec=dec)


def write_files(cells, tinfo, cl, drugs, ss, meas, out_prefix=""):
    """heatmap_matrix.csv, heatmap_data_long.csv and rgroup_table.csv, in heat-map order."""
    rows, cols = cl["rows"], cl["cols"]
    short = tinfo.set_index("tkey").short
    nm = tinfo.set_index("tkey").target_name
    mat = cells.assign(val=np.where(cells.censored, "<" + cells.p_affinity.map("{:.2f}".format),
                                    cells.p_affinity.map("{:.2f}".format)))
    mat = mat.pivot(index="monomerid", columns="tkey", values="val").reindex(index=rows, columns=cols).rename(
        columns=short)
    mat.insert(0, "compound", [label(m, drugs) for m in rows])
    mat.insert(0, "row", range(1, len(rows) + 1))
    mat.to_csv(out_prefix + "heatmap_matrix.csv", index_label="monomerid")
    order = {m: i for i, m in enumerate(rows, 1)}
    long = cells.assign(target=cells.tkey.map(short), target_name=cells.tkey.map(nm), row=cells.monomerid.map(order))
    long.sort_values(["row", "target"])[["row", "monomerid", "target", "target_name", "affinity_type", "median_nm",
                                         "p_affinity", "censored", "n_measurements", "n_used"]].to_csv(
        out_prefix + "heatmap_data_long.csv", index=False)
    blk = pd.DataFrame(meas["rows"]).merge(cells[["monomerid", "tkey"]], on=["monomerid", "tkey"])
    src = blk.groupby("monomerid").apply(
        lambda g: sorted(set(g.source_id.dropna().astype(str)) | set("doi:" + g.doi[g.source_id.isna()].dropna())),
        include_groups=False)
    smi = {r["monomerid"]: r["smiles"] for r in ss["rows"]}
    ta = table_args(cells, tinfo, cl, drugs, ss)
    rgt = pd.DataFrame([dict(row=i, compound=label(m, drugs), monomerid=m, R1_ortho=t["r_groups"]["R1"],
                             R2_meta=t["r_groups"]["R2"], pyridine_N_oxide="N-oxide" in t["subtitle"],
                             smiles=smi[m], sources=";".join(src[m]))
                        for i, (m, t) in enumerate(zip(rows, ta["rows"]), 1)])
    rgt.to_csv(out_prefix + "rgroup_table.csv", index=False)
    return rgt


def summary(cells, tinfo, cl, drugs, meas):
    """Numbers quoted in the answer."""
    print("cells", len(cells), cells.affinity_type.value_counts().to_dict(), "censored >", int(cells.censored.sum()),
          "censored <", int(cells.censored_lt.sum()), "cells with >=2 values", int((cells.n_used >= 2).sum()),
          "measurements", int(cells.n_measurements.sum()))
    short = tinfo.set_index("tkey").short
    print(cells.groupby("tkey").agg(n=("monomerid", "size"), cens=("censored", "sum")).rename(index=short))
    print("row order", [(i + 1, label(m, drugs)) for i, m in enumerate(cl["rows"])])
    print("col order", [short[t] for t in cl["cols"]])
    blk = pd.DataFrame(meas["rows"]).merge(cells[["monomerid", "tkey"]], on=["monomerid", "tkey"])
    print(blk.groupby([blk.source_id.fillna("none"), blk.doi.fillna("none")]).agg(
        n=("value", "size"), c=("monomerid", "nunique")).sort_values("n", ascending=False).head(8))
