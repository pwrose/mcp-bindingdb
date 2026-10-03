import numpy as np, pandas as pd
from style import *
df=pd.read_csv('compounds_emb.csv')
P=np.load('iris_polar.npy'); r,th=P[:,0],P[:,1]
df['r'],df['theta']=r,th
o=np.argsort(df.pKi.values)
pk_s, r_s = df.pKi.values[o], r[o]
ticks=[5.0,5.5,6.0,6.5,7.0,7.5,8.0,8.5]
tick_r=np.interp(ticks, pk_s, r_s)
order=list(df.chemotype.value_counts().index); st=ct_style(order)
fig=plt.figure(figsize=(9.2,8.2))
ax=fig.add_subplot(111,projection='polar')
ax.set_facecolor(SURF)
for c in order:
    g=df[df.chemotype==c]; col,mk=st[c]
    ax.scatter(g.theta,g.r,c=col,marker=mk,s=58,linewidths=0.7,edgecolors=SURF,
               label=f"{c} (n={len(g)})",zorder=3)
ax.set_rlim(0,1.06); ax.set_rticks(tick_r)
ax.set_yticklabels([f"{t:.1f}" for t in ticks],fontsize=7.5,color=MUTED)
ax.set_rlabel_position(97)
ax.set_xticks(np.linspace(0,2*np.pi,12,endpoint=False))
ax.set_xticklabels([]); ax.grid(color=GRID,linewidth=0.6)
ax.spines['polar'].set_color(AXIS)
ax.set_title('IRIS projection — radius = pK$_i$ (potency increases outward),\n'
             'angle = Morgan-fingerprint neighbourhood structure',
             fontsize=11.5,fontweight='bold',pad=24,loc='left')
ax.text(np.deg2rad(97),1.045,'pK$_i$',fontsize=8,color=INK2,ha='center')
ax.legend(loc='upper left',bbox_to_anchor=(-0.13,-0.02),ncol=2,fontsize=7,
          handletextpad=0.3,columnspacing=0.8,labelspacing=0.35)
fig.tight_layout(); fig.savefig('fig3_iris.png',bbox_inches='tight')
df[['monomerid','r','theta']].to_csv('iris_coords.csv',index=False)
print('ok')
