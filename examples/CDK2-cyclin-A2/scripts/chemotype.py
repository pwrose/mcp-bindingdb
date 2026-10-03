import pandas as pd
from rdkit import Chem

# Ordered SMARTS rules on the ring system; first match wins. Fused polycyclic
# cores first, then the hinge-binding heterocycle that defines each series.
RULES = [
 ("Indolocarbazole",                   "c1ccc2c(c1)nc1c2ccc2c3ccccc3nc21"),
 ("Pyrazolo[3,4-c]pyridazine",         "c1cc2cn[nX3]c2nn1"),
 ("Pyrazolo[3,4-b]pyridine",           "n1cccc2c1[nX3]nc2"),
 ("Purine",                            "c1nc2[nX3]cnc2c(n1)"),
 ("Pyrido[2,3-d]pyrimidin-7(8H)-one",  "O=c1ccc2cncnc2[nX3]1"),
 ("Pyrido[3,4-d]pyrimidine",           "c1cc2cncnc2cn1"),
 ("5,6,7,8-Tetrahydroquinazoline",     "C1CCc2cncnc2C1"),
 ("4-(Thiazol-5-yl)-2-aminopyrimidine","s1cncc1-c1ccnc([#7])n1"),
 ("7-Azaindol-3-yl-aminothiazole",     "n1cccc2c1[nX3]cc2-c1cscn1"),
 ("Pyrrole-2-carboxamide-pyrimidine",  "O=C([#7])c1cc(c[nX3]1)-c1ccncn1"),
 ("3-Aminopyrazole",                   "[NX3]c1n[nX3]cc1"),
 ("3-Aminopyrazole",                   "[NX3;!$(N=*)]c1ccn[nX3]1"),
 ("Pyrazole-3-carboxamide",            "[#7]c1c[nX3]nc1C(=O)[#7]"),
]
PAT=[(n,Chem.MolFromSmarts(s)) for n,s in RULES]
bad=[n for n,p in PAT if p is None]; assert not bad, bad
def assign(smi):
    m=Chem.MolFromSmiles(smi)
    for name,p in PAT:
        if m.HasSubstructMatch(p): return name
    return "Other"
if __name__=="__main__":
    df=pd.read_csv('compounds.csv')
    df['chemotype']=df.smiles_std.map(assign)
    print(df.chemotype.value_counts().to_string())
    o=df[df.chemotype=="Other"]
    print("\nOTHER",len(o))
    for s,n in o.scaffold.value_counts().items(): print(f"{n:3d} {s}")
    print()
    print(df.groupby('chemotype').pKi.agg(['size','median','max']).round(2).to_string())
    df.to_csv('compounds_ct.csv',index=False)
