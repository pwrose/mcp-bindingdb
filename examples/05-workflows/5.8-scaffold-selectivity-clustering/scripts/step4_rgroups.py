"""Arguments for draw_r_group_table (heat-map order), the CSVs, and numbers for the answer."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd

S, OUT = Path(sys.argv[1]), Path(sys.argv[2])
cells = pd.read_parquet(S / "cells.parquet"); tinfo = pd.read_parquet(S / "tinfo.parquet").set_index("tkey")
names = pd.read_parquet(S / "names.parquet"); act = pd.read_parquet(S / "act.parquet")
smi = pd.read_parquet(S / "smiles.parquet").set_index("monomerid")
cl = json.load(open(S / "cluster.json")); rg = json.load(open(S / "rgroups.json"))
rows, cols = cl["rows"], cl["cols"]
nm = {r.monomerid: [x.lower() for x in r.names] for r in names.itertuples()}
def label(m):
    for d in ("imatinib", "nilotinib"):
        if d in nm.get(m, []): return d.capitalize()
    return f"BDBM{m}"
C = cells.set_index(["monomerid", "tkey"])
blk = act[act.is_kinase].merge(cells[["monomerid", "tkey"]], on=["monomerid", "tkey"])
src = blk.groupby("monomerid").source_id.agg(lambda s: sorted(set(s.dropna().astype(str))))

def fmt_nm(v):
    return f"{v/1000:.3g} µM" if v >= 1000 else f"{v:.3g} nM"
BARS = [("p5221", "ABL1"), ("c50000008", "PDGFR-α/β"), ("c599" if False else "p599", "PKC-α")]
def ren(x):  # R3 (meta) becomes R2; the pyridine N-oxide position (R2) is dropped
    return x if x in (None, "H") else x.replace("[*:3]", "[*:2]")
table_rows = []
for i, (m, r) in enumerate(zip(rows, rg["rows"]), 1):
    bars = []
    for t, lab in BARS:
        if (m, t) not in C.index: continue
        c = C.loc[(m, t)]
        note = (f"{c.affinity_type} > {fmt_nm(c.median_nm)}" if c.censored else f"{c.affinity_type} {fmt_nm(c.median_nm)}") \
               + (f" ({int(c.n_used)})" if c.n_used > 1 else "")
        bars.append(dict(label=lab, value_nm=round(float(c.median_nm), 3), type=c.affinity_type, faint=bool(c.censored), note=note))
    sub = f"BDBM{m}" if not label(m).startswith("BDBM") else ""
    if r.get("R2"): sub = (sub + " · " if sub else "") + "pyridine N-oxide"
    table_rows.append(dict(title=f"{i}. {label(m)}", subtitle=sub, r_groups={"R1": ren(r["R1"]), "R2": ren(r["R3"])}, bars=bars))
core = "c1cncc(-c2ccnc(Nc3cc([*:2])ccc3[*:1])n2)c1"
json.dump(dict(core=core, part1=table_rows[:15], part2=table_rows[15:]), open(S / "rgroup_args.json", "w"), ensure_ascii=False)
print(json.dumps(table_rows[:15], ensure_ascii=False))
print("-----")
print(json.dumps(table_rows[15:], ensure_ascii=False))

# files for the example folder
tl = {t: tinfo.short[t] for t in cols}
mat = cells.assign(val=np.where(cells.censored, "<" + cells.p_affinity.map("{:.2f}".format), cells.p_affinity.map("{:.2f}".format)))
mat = mat.pivot(index="monomerid", columns="tkey", values="val").reindex(index=rows, columns=cols).rename(columns=tl)
mat.insert(0, "compound", [label(m) for m in rows]); mat.insert(0, "row", range(1, len(rows) + 1))
mat.to_csv(OUT / "heatmap_matrix.csv", index_label="monomerid")
long = cells.assign(target=cells.tkey.map(tinfo.short), target_name=cells.tkey.map(tinfo.target_name),
                    row=cells.monomerid.map({m: i for i, m in enumerate(rows, 1)}))
long.sort_values(["row", "target"])[["row", "monomerid", "target", "target_name", "affinity_type", "median_nm", "p_affinity",
                                     "censored", "n_measurements", "n_used"]].to_csv(OUT / "heatmap_data_long.csv", index=False)
rgt = pd.DataFrame([dict(row=i, compound=label(m), monomerid=m, R1_ortho=ren(r["R1"]), R2_meta=ren(r["R3"]),
                         pyridine_N_oxide=bool(r.get("R2")), smiles=smi.smiles[m], sources=";".join(src[m]))
                    for i, (m, r) in enumerate(zip(rows, rg["rows"]), 1)])
rgt.to_csv(OUT / "rgroup_table.csv", index=False)
print(rgt[["row", "compound", "sources"]].to_string())
print(cells.groupby("tkey").agg(n=("monomerid", "size"), cens=("censored", "sum")).rename(index=tl))
print("sources in block", blk.source_id.nunique(), blk.source_id.value_counts().head(8).to_dict())
