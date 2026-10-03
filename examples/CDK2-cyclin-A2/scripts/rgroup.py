import pandas as pd, numpy as np
from rdkit import Chem
from rdkit.Chem import rdRGroupDecomposition as rgd
df=pd.read_csv('compounds_ct.csv')
sub=df[df.chemotype=='Pyrido[3,4-d]pyrimidine'].copy()
mols=[Chem.MolFromSmiles(s) for s in sub.smiles_std]
core=Chem.MolFromSmarts('c1cc2cncnc2cn1')
ps=rgd.RGroupDecompositionParameters()
ps.onlyMatchAtRGroups=False; ps.removeHydrogensPostMatch=True
ps.matchingStrategy=rgd.RGroupMatching.GreedyChunks
res,unmatched=rgd.RGroupDecompose([core],mols,asSmiles=True,options=ps)
print('n',len(sub),'matched',len(res),'unmatched',unmatched)
R=pd.DataFrame(res); R['pKi']=sub.pKi.values; R['name']=sub.compound_name.values
cols=[c for c in R.columns if c.startswith('R')]
print(cols)
for c in cols:
    u=R[c].value_counts()
    print(f"\n{c}: {len(u)} unique")
    for s,n in u.items(): print(f"   {n:2d}  med pKi {R[R[c]==s].pKi.median():.2f}  {s}")
R.to_csv('rgroups.csv',index=False)
