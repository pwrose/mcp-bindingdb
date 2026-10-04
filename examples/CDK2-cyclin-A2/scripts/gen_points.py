import pandas as pd, numpy as np, json, re
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from style import CAT, MARKERS
rdDepictor.SetPreferCoordGen(True)
df=pd.read_csv('compounds_emb.csv')
P=np.load('iris_polar.npy'); df['r'],df['theta']=P[:,0],P[:,1]
order=list(df.chemotype.value_counts().index)
cidx={c:i for i,c in enumerate(order)}


STYLE_RE=re.compile(r"\s*style='([^']*)'")
def _attrs(style):
    d=dict(p.split(':',1) for p in style.split(';') if ':' in p)
    out=[]
    fill=d.get('fill','none').strip()
    if fill!='none': out.append(f'fill="{fill}"')
    stroke=d.get('stroke','').strip()
    if stroke and stroke!='none': out.append(f'stroke="{stroke}"')
    sw=d.get('stroke-width','').replace('px','').strip()
    if sw and abs(float(sw)-2.0)>0.05: out.append(f'stroke-width="{float(sw):.1f}"')
    return (' '+' '.join(out)) if out else ''
def compress(s):
    s=re.sub(r"<\?xml[^>]*\?>","",s)
    s=re.sub(r"<!DOCTYPE[^>]*>","",s)
    s=re.sub(r"<rect[^>]*?fill:#FFFFFF[^>]*?>","",s)
    s=re.sub(r"\s*class='[^']*'","",s)
    s=re.sub(r"<!--.*?-->","",s,flags=re.S)
    s=STYLE_RE.sub(lambda m:_attrs(m.group(1)),s)
    s=re.sub(r"\d+\.\d{2,}",lambda m:f"{float(m.group()):.1f}",s)
    s=re.sub(r"<svg[^>]*viewBox='([^']*)'[^>]*>",
      lambda m:("<svg xmlns='http://www.w3.org/2000/svg' viewBox='%s' width='100%%' "
                "fill='none' stroke-width='2' stroke-linecap='butt' "
                "stroke-linejoin='miter'>"%m.group(1)), s, count=1)
    s=re.sub(r">\s+<","><",s); s=re.sub(r"\s{2,}"," ",s)
    return s.strip()

def svg(smi):
    m=Chem.MolFromSmiles(smi); rdDepictor.Compute2DCoords(m)
    d=rdMolDraw2D.MolDraw2DSVG(300,210)
    o=d.drawOptions(); o.clearBackground=False; o.bondLineWidth=1.6
    rdMolDraw2D.PrepareAndDrawMolecule(d,m); d.FinishDrawing()
    return compress(d.GetDrawingText())

pts=[]
for r in df.itertuples():
    pts.append({"i":int(r.monomerid),"n":str(r.compound_name),"c":cidx[r.chemotype],
     "x":round(r.tsne1,2),"y":round(r.tsne2,2),"rr":round(r.r,4),"th":round(r.theta,4),
     "p":round(r.pKi,2),"k":float(r.value),"rel":r.relation,"m":int(r.n_measurements),
     "d":(None if pd.isna(r.doi) else r.doi),"yr":(None if pd.isna(r.year) else int(r.year)),
     "s":r.smiles_std,"g":svg(r.smiles_std)})
out={"chemotypes":order,"colors":CAT,"markers":MARKERS[:len(order)],"points":pts}
json.dump(out,open('points.json','w'),separators=(',',':'))
import os; print('kB', round(os.path.getsize('points.json')/1024))
