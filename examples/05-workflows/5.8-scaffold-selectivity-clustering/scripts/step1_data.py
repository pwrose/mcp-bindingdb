"""Matches of the imatinib core, their kinase measurements, and a scan for a dense compound x target block."""
import sys, json
from pathlib import Path
import duckdb, pandas as pd
from mcp_bindingdb import substructure as ss

DB = Path("data/bindingdb_202610.duckdb")
OUT = Path(sys.argv[1])
CORE = "c1ccc(Nc2nccc(-c3cccnc3)n2)cc1"

idx = ss.SubstructureIndex(ss.index_path(DB))
q, _ = ss.parse_query(CORE)
m = idx.search(q, max_results=10000, time_limit_s=300)
ids = m.monomerids if hasattr(m, "monomerids") else m[0]
print("matches", len(ids), "complete", m.complete)

con = duckdb.connect(str(DB), read_only=True)
con.execute("CREATE TEMP TABLE hits(monomerid INTEGER)")
con.executemany("INSERT INTO hits VALUES (?)", [(i,) for i in ids])
act = con.execute("""
  SELECT a.monomerid, coalesce('p'||a.polymerid, 'c'||a.complexid) AS tkey, a.target_name, a.uniprot_raw,
         a.organism, a.affinity_type, a.relation, a.value, a.p_affinity, a.source_id
  FROM activity a JOIN hits USING (monomerid)
  WHERE a.affinity_type IN ('Ki','Kd','IC50','EC50') AND a.unit='nM' AND a.value > 0
""").df()
smiles = con.execute("SELECT c.monomerid, c.smiles, c.name FROM compound c JOIN hits USING (monomerid)").df()
names = con.execute("""SELECT monomerid, list(DISTINCT name) AS names FROM mono_name JOIN hits USING (monomerid)
                       GROUP BY monomerid""").df()
print("measurements", len(act), "compounds", act.monomerid.nunique(), "targets", act.tkey.nunique())
kin = act.target_name.str.contains(r"kinase|growth factor receptor|Mast/stem cell", case=False, regex=True)
act["is_kinase"] = kin
print("kinase measurements", kin.sum(), "kinase targets", act[kin].tkey.nunique(),
      "compounds", act[kin].monomerid.nunique())
act.to_parquet(OUT / "act.parquet"); smiles.to_parquet(OUT / "smiles.parquet"); names.to_parquet(OUT / "names.parquet")

k = act[kin]
pairs = k[["monomerid", "tkey"]].drop_duplicates()
print("full kinase matrix", pairs.monomerid.nunique(), "x", pairs.tkey.nunique(), "filled", len(pairs),
      f"{len(pairs)/(pairs.monomerid.nunique()*pairs.tkey.nunique()):.1%}")

def bicluster(pairs, min_c, min_t):
    p = pairs
    while True:
        tc = p.groupby("tkey").monomerid.nunique(); p2 = p[p.tkey.isin(tc[tc >= min_c].index)]
        ct = p2.groupby("monomerid").tkey.nunique(); p2 = p2[p2.monomerid.isin(ct[ct >= min_t].index)]
        if len(p2) == len(p): return p2
        p = p2

for mc, mt in [(8,3),(10,3),(20,3),(8,4),(10,4),(8,5),(8,6)]:
    b = bicluster(pairs, mc, mt)
    nc, nt = b.monomerid.nunique(), b.tkey.nunique()
    tn = k[k.tkey.isin(b.tkey.unique())].groupby("tkey").target_name.first()
    print(mc, mt, f"{nc} x {nt}", f"{len(b)/(nc*nt):.0%}" if nc else "-", "|", "; ".join(tn.values) if nt <= 10 else "")
