import pandas as pd, numpy as np, io
from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D
from PIL import Image
from style import *
import matplotlib.gridspec as gs
rdDepictor.SetPreferCoordGen(True)
R=pd.read_csv('rgroups.csv')
POS=['R1','R2','R3']
TITLES={'R1':'R1 — C8 amine','R2':'R2 — C2 arylamine','R3':'R3 — C6 substituent'}

def draw(smi,w=330,h=190):
    m=Chem.MolFromSmiles(smi)
    if m is None or m.GetNumAtoms()==0: return None
    for a in m.GetAtoms():
        if a.GetAtomicNum()==0: a.SetProp('atomLabel','R')
    rdDepictor.Compute2DCoords(m)
    d=rdMolDraw2D.MolDraw2DCairo(w,h); d.drawOptions().clearBackground=False
    rdMolDraw2D.PrepareAndDrawMolecule(d,m); d.FinishDrawing()
    return Image.open(io.BytesIO(d.GetDrawingText()))

blocks={}
for p in POS:
    t=(R.groupby(p).pKi.agg(['median','size','min','max'])
         .sort_values('median',ascending=False).reset_index())
    blocks[p]=t
nrow=max(len(t) for t in blocks.values())
lo,hi=4.7,R.pKi.max()+0.25
fig=plt.figure(figsize=(14,1.05*nrow+1.9))
G=gs.GridSpec(nrow+1,6,figure=fig,height_ratios=[0.42]+[1]*nrow,
              width_ratios=[1.25,1,1.25,1,1.25,1],hspace=0.12,wspace=0.08)
for ci,p in enumerate(POS):
    t=blocks[p]
    hd=fig.add_subplot(G[0,2*ci:2*ci+2]); hd.set_axis_off()
    hd.text(0,0.25,TITLES[p],fontsize=10,fontweight='bold',color=INK)
    hd.text(0,-0.55,f"{len(t)} unique · median & min–max",fontsize=7.4,color=MUTED)
    for ri in range(nrow):
        am=fig.add_subplot(G[ri+1,2*ci]); ab=fig.add_subplot(G[ri+1,2*ci+1])
        am.set_axis_off()
        for s in ('top','right','left'): ab.spines[s].set_visible(False)
        ab.set_yticks([]); ab.set_xlim(lo,hi); ab.grid(axis='x',color=GRID,lw=0.6)
        if ri==nrow-1 or ri==len(t)-1:
            ab.set_xticks([5,6,7]); ab.tick_params(labelsize=7.5,length=2)
            ab.set_xlabel('median pK$_i$',fontsize=7.5,color=MUTED,labelpad=1)
        else:
            ab.set_xticks([5,6,7]); ab.set_xticklabels([])
        if ri>=len(t):
            am.set_visible(False); ab.set_visible(False); continue
        r=t.iloc[ri]
        lab={'[H][*:3]':'–H  (unsubstituted)','C[*:3]':'–CH$_3$'}.get(r[p])
        im=None if lab else draw(r[p])
        if im is not None: am.imshow(im)
        else: am.text(0.5,0.5,lab or r[p],ha='center',va='center',
                      fontsize=11,color=INK,transform=am.transAxes)
        ab.barh([0],[r['median']-lo],left=lo,height=0.42,color=CAT[0],zorder=3)
        if r['size']>1:
            ab.plot([r['min'],r['max']],[0,0],color=MUTED,lw=1.4,zorder=4,
                    solid_capstyle='butt',alpha=0.9)
        xlab=max(r['median'],r['max'] if r['size']>1 else r['median'])+0.07
        ab.text(xlab,0,f"{r['median']:.2f}",va='center',fontsize=7.8,color=INK,zorder=5)
        ab.text(lo+0.06,0.33,f"n={int(r['size'])}",va='center',fontsize=7,color=MUTED)
        ab.set_ylim(-0.55,0.62); ab.spines['bottom'].set_color(AXIS)
fig.suptitle('Pyrido[3,4-d]pyrimidine series (n=24) — R-group decomposition, '
             'ranked within each position by median pK$_i$',
             x=0.008,y=0.995,ha='left',va='top',fontsize=11.5,fontweight='bold')
fig.subplots_adjust(top=0.955)
fig.savefig('fig4_rgroups.png',bbox_inches='tight',dpi=190)
print('ok',nrow)
