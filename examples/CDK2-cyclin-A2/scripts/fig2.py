import pandas as pd, numpy as np, io
import matplotlib.gridspec as gridspec
from matplotlib.colors import to_rgb
from rdkit import Chem
from rdkit.Chem import rdDepictor, AllChem
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image
from style import *
from chemotype import PAT
rdDepictor.SetPreferCoordGen(True)
df=pd.read_csv('compounds_ct.csv')
order=list(df.chemotype.value_counts().index)
st=ct_style(order)          # same colour+marker map as the t-SNE legend

def core_for(ct, mol):
    for name,p in PAT:
        if name==ct and mol.HasSubstructMatch(p): return p
    return None

rows=[]
for ct in order:
    sub=df[df.chemotype==ct].copy()
    g=pd.concat([sub[~sub.censored].sort_values('pKi',ascending=False),
                 sub[sub.censored].sort_values('pKi',ascending=False)]).head(3)
    mols=[Chem.MolFromSmiles(s) for s in g.smiles_std]
    ref=mols[0]; rdDepictor.Compute2DCoords(ref)
    core=core_for(ct,ref)
    hl=to_rgb(st[ct][0])+(0.30,)      # chemotype colour, translucent
    imgs=[]
    for m,(_,r) in zip(mols,g.iterrows()):
        try: AllChem.GenerateDepictionMatching2DStructure(m,ref,refPatt=core)
        except Exception: rdDepictor.Compute2DCoords(m)
        hit=m.GetSubstructMatch(core) if core is not None else ()
        hb=[b.GetIdx() for b in m.GetBonds()
            if b.GetBeginAtomIdx() in hit and b.GetEndAtomIdx() in hit]
        d=rdMolDraw2D.MolDraw2DCairo(520,400)
        o=d.drawOptions(); o.addStereoAnnotation=False; o.clearBackground=False
        o.highlightColour=hl; o.highlightBondWidthMultiplier=14
        rdMolDraw2D.PrepareAndDrawMolecule(d,m,highlightAtoms=list(hit),highlightBonds=hb)
        d.FinishDrawing()
        imgs.append((Image.open(io.BytesIO(d.GetDrawingText())), r))
    rows.append((ct,imgs))

nr=len(rows)
fig=plt.figure(figsize=(10.5,2.45*nr))
G=gridspec.GridSpec(2*nr,3,figure=fig,
                    height_ratios=[0.40,1]*nr, hspace=0.0, wspace=0.03)
for i,(ct,imgs) in enumerate(rows):
    col,mk=st[ct]
    hd=fig.add_subplot(G[2*i,:]); hd.set_axis_off()
    hd.set_xlim(0,1); hd.set_ylim(0,1)
    hd.plot([0.010],[0.30],marker=mk,color=col,markersize=7.5,
            markeredgecolor=SURF,markeredgewidth=0.7,clip_on=False)
    hd.text(0.028,0.30,ct,fontsize=10.5,fontweight='bold',color=INK,va='center')
    hd.text(0.998,0.30,f"n = {int((df.chemotype==ct).sum())}",fontsize=8.6,
            color=MUTED,va='center',ha='right')
    if i: hd.axhline(0.97,color=GRID,lw=0.8,xmin=0,xmax=1)
    for j in range(3):
        ax=fig.add_subplot(G[2*i+1,j]); ax.set_axis_off()
        if j>=len(imgs): continue
        im,r=imgs[j]; ax.imshow(im)
        rel={'>':'<','<':'>','=':''}[r.relation]
        kir=r.relation if r.relation!='=' else ''
        ax.set_title(f"pK$_i$ {rel}{r.pKi:.2f}   (K$_i$ {kir}{r.value:g} nM)",
                     fontsize=8.2,color=INK,pad=3)
        nm=str(r.compound_name); nm=(nm[:40]+'…') if len(nm)>41 else nm
        ax.text(0.5,-0.02,nm,transform=ax.transAxes,ha='center',va='top',
                fontsize=6.3,color=MUTED)
fig.suptitle('Top 3 compounds per chemotype, aligned and highlighted on the defining core',
             x=0.008,y=0.997,ha='left',va='top',fontsize=11.5,fontweight='bold')
fig.subplots_adjust(top=0.972,bottom=0.004,left=0.008,right=0.995)
fig.savefig('fig2_chemotype_grid.png',bbox_inches='tight')
print('rows',nr)
