import numpy as np, pandas as pd, pickle, sys
from IRIS import fit_transform, get_rho
d=pickle.load(open('fp.pkl','rb')); Xb=d['Xb']
df=pd.read_csv('compounds_emb.csv')
t=df.pKi.values.astype(np.float64)
rho=get_rho(t); print('rho',rho,file=sys.stderr)
np.random.seed(0)
poptr=fit_transform(Xb, t, return_polar=True, n_neighbors=15, n_iterations=5, rho=0)
np.save('iris_polar.npy', poptr)
print('shape',poptr.shape, 'r range',poptr[:,0].min(),poptr[:,0].max(),file=sys.stderr)
