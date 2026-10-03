import pandas as pd, numpy as np
from style import *
from declutter import place_labels
df=pd.read_csv('compounds_emb.csv')
order=order_chemotypes(df); st=ct_style(order)
fig,axes=plt.subplots(1,2,figsize=(13.5,6.2))
ax=axes[0]
for c in order:
    g=df[df.chemotype==c]; col,mk=st[c]
    ax.scatter(g.tsne1,g.tsne2,c=col,marker=mk,s=46,linewidths=0.7,
               edgecolors=SURF,label=f"{c} (n={len(g)})",zorder=3)
pts=[(df[df.chemotype==c].tsne1.median(), df[df.chemotype==c].tsne2.median()) for c in order]
ax.set_xlim(df.tsne1.min()-7,df.tsne1.max()+7); ax.set_ylim(df.tsne2.min()-7,df.tsne2.max()+9)
place_labels(ax, pts, order)
ax.set_title('A  Chemical space by chemotype')
ax.set_xlabel('t-SNE 1'); ax.set_ylabel('t-SNE 2')
ax.legend(loc='upper left',bbox_to_anchor=(0,-0.09),ncol=2,fontsize=6.6,
          handletextpad=0.3,columnspacing=0.8,labelspacing=0.35)
ax=axes[1]
ex=df[~df.censored]; ce=df[df.censored]
sc=ax.scatter(ex.tsne1,ex.tsne2,c=ex.pKi,cmap=SEQ,s=52,vmin=df.pKi.min(),
              vmax=df.pKi.max(),linewidths=0.7,edgecolors=SURF,zorder=3)
ax.scatter(ce.tsne1,ce.tsne2,facecolors='none',edgecolors=MUTED,s=52,
           linewidths=1.0,zorder=4,label=f'censored Ki bound (n={len(ce)})')
cb=fig.colorbar(sc,ax=ax,pad=0.02,fraction=0.045)
cb.set_label('pK$_i$  =  9 − log$_{10}$(K$_i$ / nM)',color=INK2,fontsize=8.5)
cb.outline.set_visible(False); cb.ax.tick_params(color=MUTED,labelsize=8)
ax.set_title('B  Same coordinates, coloured by affinity')
ax.set_xlabel('t-SNE 1'); ax.set_ylabel('t-SNE 2')
ax.legend(loc='upper left',bbox_to_anchor=(0,-0.09),fontsize=7)
for a in axes: a.set_xlim(df.tsne1.min()-7,df.tsne1.max()+7); a.set_ylim(df.tsne2.min()-7,df.tsne2.max()+9)
fig.suptitle('CDK2/cyclin A2 K$_i$ ligands — Morgan/Tanimoto t-SNE (n=163)',
             x=0.005,ha='left',fontsize=11.5,fontweight='bold')
fig.tight_layout(rect=[0,0,1,0.96]); fig.savefig('fig1_tsne.png',bbox_inches='tight')
print('ok')
