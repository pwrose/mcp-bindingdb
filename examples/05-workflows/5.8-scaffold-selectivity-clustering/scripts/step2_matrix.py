"""Median matrix of the 38 x 8 block, clustering, and the R-group decomposition in heat-map order."""
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list, optimal_leaf_ordering
from scipy.spatial.distance import squareform
from rdkit import Chem
from mcp_bindingdb import sar

S = Path(sys.argv[1])
act = pd.read_parquet(S / "act.parquet"); smi = pd.read_parquet(S / "smiles.parquet")
names = pd.read_parquet(S / "names.parquet")
k = act[act.is_kinase]
pairs = k[["monomerid", "tkey"]].drop_duplicates()
p = pairs
while True:
    tc = p.groupby("tkey").monomerid.nunique(); p2 = p[p.tkey.isin(tc[tc >= 8].index)]
    ct = p2.groupby("monomerid").tkey.nunique(); p2 = p2[p2.monomerid.isin(ct[ct >= 4].index)]
    if len(p2) == len(p): break
    p = p2
blk = k.merge(p, on=["monomerid", "tkey"])

RANK = {"Kd": 0, "Ki": 1, "IC50": 2, "EC50": 3}
cells = []
for (mid, t), g in blk.groupby(["monomerid", "tkey"]):
    typ = min(g.affinity_type, key=RANK.get)
    g = g[g.affinity_type == typ]
    exact = g[g.relation == "="]
    use = exact if len(exact) else g
    nm = float(np.median(use.value))
    cells.append(dict(monomerid=mid, tkey=t, affinity_type=typ, median_nm=nm, p_affinity=round(9 - np.log10(nm), 2),
                      censored=(len(exact) == 0 and (g.relation == ">").any()),
                      censored_lt=(len(exact) == 0 and (g.relation == "<").any()),
                      n_measurements=len(g), n_used=len(use)))
cells = pd.DataFrame(cells)
print("cells", len(cells), cells.affinity_type.value_counts().to_dict(), "censored >", int(cells.censored.sum()),
      "censored <", int(cells.censored_lt.sum()), "cells with >=2 values", int((cells.n_used >= 2).sum()),
      "measurements", int(cells.n_measurements.sum()))

SHORT = {"Tyrosine-protein kinase ABL1": "ABL1", "Breakpoint cluster region protein/Tyrosine-protein kinase ABL1": "BCR-ABL",
         "Platelet-derived growth factor receptor alpha/beta": "PDGFR-α/β", "Proto-oncogene tyrosine-protein kinase Src": "SRC",
         "Epidermal growth factor receptor": "EGFR", "Protein kinase C alpha type": "PKC-α", "Protein kinase C delta type": "PKC-δ",
         "cAMP-dependent protein kinase catalytic subunit alpha/beta/gamma": "PKA"}
tinfo = blk.groupby("tkey").agg(target_name=("target_name", "first"), organism=("organism", "first"),
                                uniprot=("uniprot_raw", "first")).reset_index()
tinfo["short"] = tinfo.target_name.map(SHORT)
print(tinfo.to_string())
M = cells.pivot(index="monomerid", columns="tkey", values="p_affinity")

def nan_euclid(A):
    n = len(A); D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            ok = ~np.isnan(A[i]) & ~np.isnan(A[j])
            d = np.sqrt(np.mean((A[i, ok] - A[j, ok]) ** 2) * A.shape[1]) if ok.any() else 10.0
            D[i, j] = D[j, i] = d
    return D
Dr = nan_euclid(M.values)
Zr = optimal_leaf_ordering(linkage(squareform(Dr), "average"), squareform(Dr))
C = M.corr(min_periods=3).fillna(0).values
Dc = np.clip(1 - C, 0, 2); np.fill_diagonal(Dc, 0)
Zc = optimal_leaf_ordering(linkage(squareform(Dc, checks=False), "average"), squareform(Dc, checks=False))
rows = M.index[leaves_list(Zr)].tolist(); cols = M.columns[leaves_list(Zc)].tolist()
# imatinib/nilotinib at the top reads better: flip the row order if they ended up at the bottom
nm = {r.monomerid: list(r.names) for r in names.itertuples()}
def label(mid):
    low = [x.lower() for x in nm.get(mid, [])]
    for drug in ("imatinib", "nilotinib"):
        if drug in low: return drug.capitalize()
    return f"BDBM{mid}"
labels = [label(m) for m in rows]
print("drugs at", [i for i, l in enumerate(labels) if not l.startswith("BDBM")])
if labels.index("Imatinib") > len(rows) / 2:
    rows = rows[::-1]
json.dump(dict(rows=[int(r) for r in rows], cols=cols, Zr=Zr.tolist(), Zc=Zc.tolist(), row_ids=[int(x) for x in M.index],
               col_ids=list(M.columns)), open(S / "cluster.json", "w"))
cells.to_parquet(S / "cells.parquet"); tinfo.to_parquet(S / "tinfo.parquet")

# R-group decomposition of the 38, unmarked core: every substituted position becomes a column
core = Chem.MolFromSmiles("c1ccc(Nc2nccc(-c3cccnc3)n2)cc1")
s = smi.set_index("monomerid")
mols = sar.molecules([s.smiles[m] for m in rows])
d = sar.decompose(core, mols)
print("labels", d.labels, "matched", d.n_matched, "core", d.core)
for m, r in zip(rows, d.rows):
    print(label(m), r)
json.dump(dict(core=d.core, labels=d.labels, rows=d.rows), open(S / "rgroups.json", "w"))
