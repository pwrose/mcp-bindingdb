import numpy as np
def place_labels(ax, pts, texts, fontsize=6.8, iters=1500, k=1.0):
    """Greedy force-directed label placement in display coords with leader lines."""
    fig=ax.figure; fig.canvas.draw()
    P=np.array([ax.transData.transform(p) for p in pts],dtype=float)
    C=P.mean(axis=0)
    V=P-C; n=np.linalg.norm(V,axis=1,keepdims=True); n[n==0]=1
    L=P+V/n*46.0+np.array([0,10.0])
    # estimate box sizes
    r=fig.canvas.get_renderer()
    sz=[]
    for t in texts:
        tt=ax.text(0,0,t,fontsize=fontsize); bb=tt.get_window_extent(renderer=r)
        sz.append([bb.width+12,bb.height+12]); tt.remove()
    sz=np.array(sz)
    for _ in range(iters):
        moved=False
        for i in range(len(L)):
            for j in range(i+1,len(L)):
                d=L[i]-L[j]; ov=(sz[i]+sz[j])/2-np.abs(d)
                if ov[0]>0 and ov[1]>0:
                    moved=True
                    ax_=0 if ov[0]<ov[1] else 1
                    s=np.sign(d[ax_]) or 1.0
                    L[i][ax_]+=s*ov[ax_]/2*0.55; L[j][ax_]-=s*ov[ax_]/2*0.55
            # spring back toward anchor
            L[i]+= (P[i]+V[i]/n[i]*46.0-L[i])*0.010
        if not moved: break
    inv=ax.transData.inverted()
    out=[]
    for i,t in enumerate(texts):
        xy=inv.transform(L[i])
        out.append(ax.annotate(t, xy=pts[i], xytext=xy, fontsize=fontsize,
            ha='center', va='center', color='#52514e', zorder=6,
            bbox=dict(boxstyle='round,pad=0.2',fc='#fcfcfb',ec='#c3c2b7',lw=0.4,alpha=0.92),
            arrowprops=dict(arrowstyle='-',color='#898781',lw=0.5,
                            shrinkA=1,shrinkB=3,alpha=0.8)))
    return out
