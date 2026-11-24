import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SHORT = {
    "Tyrosine-protein kinase ABL1": "ABL1",
    "Mast/stem cell growth factor receptor Kit": "KIT",
    "Breakpoint cluster region protein/Tyrosine-protein kinase ABL1": "BCR-ABL (complex)",
    "Tyrosine-protein kinase ABL2": "ABL2",
    "Epidermal growth factor receptor": "EGFR",
    "Epidermal growth factor receptor [T790M,L858R]": "EGFR [T790M, L858R]",
    "Platelet-derived growth factor receptor alpha": "PDGFR-alpha",
    "Vascular endothelial growth factor receptor 2": "VEGFR2",
    "Breakpoint cluster region protein [1-693]": "BCR [1-693]",
    "Platelet-derived growth factor receptor beta": "PDGFR-beta",
    "Serine/threonine-protein kinase TBK1": "TBK1",
    "Inhibitor of nuclear factor kappa-B kinase subunit epsilon": "IKK-epsilon",
    "Platelet-derived growth factor receptor alpha/beta": "PDGFR-alpha/beta (complex)",
    "Tyrosine-protein kinase ZAP-70": "ZAP-70",
    "Mitogen-activated protein kinase 10": "JNK3 (MAPK10)",
}
CLINICAL = {"ABL1", "KIT", "BCR-ABL (complex)", "ABL2", "PDGFR-alpha", "PDGFR-beta", "PDGFR-alpha/beta (complex)"}


def plot_top_targets(result, path="scaffold_targets_top15.png", n=15):
    rows = result["rows"][:n]
    labels = [SHORT.get(r["target_name"], r["target_name"]) for r in rows][::-1]
    counts = [r["n_compounds"] for r in rows][::-1]
    colors = ["#e07b00" if l in CLINICAL else "#4c6a92" for l in labels]
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    ax.barh(labels, counts, color=colors)
    for y, c in enumerate(counts):
        ax.text(c + 1.5, y, str(c), va="center", fontsize=9)
    ax.set_xlabel("Compounds containing the core that bind at 10 µM or better")
    ax.set_title("Top 15 targets of compounds with the imatinib core", loc="left")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, max(counts) * 1.12)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return path
