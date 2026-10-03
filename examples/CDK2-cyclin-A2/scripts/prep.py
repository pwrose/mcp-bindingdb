import json,pandas as pd,numpy as np
from rdkit import Chem
from rdkit.Chem.Scaffolds import MurckoScaffold
from rdkit.Chem.MolStandardize import rdMolStandardize
d=pd.DataFrame(json.load(open('ki_raw.json'))['rows'])
d['censored']=d.relation.ne('=')
# strongest Ki per compound: lowest Ki; prefer exact '=' over '>' at equal value
d['rank_rel']=d.relation.map({'<':0,'=':1,'>':2})
d=d.sort_values(['monomerid','value','rank_rel'])
n_meas=d.groupby('monomerid').size()
best=d.groupby('monomerid').head(1).copy()
best['n_measurements']=best.monomerid.map(n_meas)
lfc=rdMolStandardize.LargestFragmentChooser()
def clean(s):
    m=Chem.MolFromSmiles(s); m=lfc.choose(m); return Chem.MolToSmiles(m)
best['smiles_std']=best.smiles.map(clean)
best['pKi']=9-np.log10(best.value)
best['scaffold']=best.smiles_std.map(lambda s: MurckoScaffold.MurckoScaffoldSmiles(s))
best.to_csv('compounds.csv',index=False)
print(len(best), best.censored.sum())
print(best[['monomerid','value','relation']].head())
print(best.groupby('doi').size())
for doi,g in best.groupby('doi'):
    print('\n##',doi, len(g))
    for s in g.scaffold.value_counts().head(4).index: print('  ',s)
