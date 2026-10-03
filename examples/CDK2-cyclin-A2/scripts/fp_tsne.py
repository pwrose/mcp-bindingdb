import numpy as np, pandas as pd, pickle
from rdkit import Chem, DataStructs
from rdkit.Chem import rdFingerprintGenerator
df=pd.read_csv('compounds_ct.csv')
mols=[Chem.MolFromSmiles(s) for s in df.smiles_std]
gen=rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
fps=[gen.GetFingerprint(m) for m in mols]
n=len(fps)
D=np.zeros((n,n))
for i in range(n):
    sims=DataStructs.BulkTanimotoSimilarity(fps[i], fps)
    D[i]=1.0-np.array(sims)
D=(D+D.T)/2; np.fill_diagonal(D,0)
X=np.array([np.frombuffer(bytes(DataStructs.BitVectToBinaryText(f)),dtype=np.uint8) for f in fps])
Xb=np.unpackbits(X,axis=1).astype(np.float32)
from sklearn.manifold import TSNE
ts=TSNE(n_components=2, metric='precomputed', init='random', perplexity=20,
        random_state=42, learning_rate='auto', max_iter=2000)
emb=ts.fit_transform(D)
df['tsne1'],df['tsne2']=emb[:,0],emb[:,1]
df.to_csv('compounds_emb.csv',index=False)
pickle.dump({'D':D,'Xb':Xb},open('fp.pkl','wb'))
print(n, Xb.shape, 'mean Tanimoto dist %.3f'%D[np.triu_indices(n,1)].mean())
