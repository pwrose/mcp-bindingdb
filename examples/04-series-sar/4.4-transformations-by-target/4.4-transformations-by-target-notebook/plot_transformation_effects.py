"""Code 1: Pair table with the document check, and the figure, from the notebook 4.4-transformations-by-target-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

"""What one fluorine, one methyl and one chlorine do to potency, for seven targets from seven classes.

Each dot is one matched molecular pair: two compounds among the 1,500 most potent ligands of a target
that differ only by the marked group, placed at the change in potency (in log units) that adding the
group brought.

A pair is only trustworthy if both of its values were measured in the same place, so each pair is
checked against the documents it comes from. Blue pairs have at least one patent or paper that reports
*both* compounds under one assay name, and are plotted from that document's own two values. Grey pairs
have no such document: they compare one laboratory's number with another's (or two assays inside one
document), and are plotted where the database-wide best values put them. Medians, and the percentages,
are of the blue pairs only.

The pairs are the ones `matched_molecular_pairs` returns for `transformation: "[H][*:1] >> F[*:1]"`,
`"[H][*:1] >> C[*:1]"` and `"[H][*:1] >> Cl[*:1]"` with `max_compounds: 1500`, one call per target and
change (21 calls). For each target one `run_sql` call lists, for every pair, each document and assay
name that reports both compounds, with the change in potency read from that document's own two values.

    rows = build_rows(pair_results, shared_results)   # lists of the tool results, target by target
    write_csv(rows)                                    # transformation_deltas.csv
    plot(rows)                                         # transformation_effects.png
"""
import csv
import math
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "transformation_deltas.csv"
PNG = "transformation_effects.png"
TARGETS = [  # target_id, label, protein class
    (520, "EGFR", "receptor tyrosine kinase"),
    (5093, "BACE1", "aspartyl protease"),
    (3619, "AChE", "serine hydrolase"),
    (1193, "CA II", "zinc metalloenzyme"),
    (2130, "Adenosine A2A", "GPCR"),
    (2132, "hERG", "ion channel"),
    (738, "ROR-gamma", "nuclear receptor"),
]
CHANGES = [("fluorine", "[H][*:1] >> F[*:1]", "A  Hydrogen → fluorine"),
           ("methyl", "[H][*:1] >> C[*:1]", "B  Hydrogen → methyl"),
           ("chlorine", "[H][*:1] >> Cl[*:1]", "C  Hydrogen → chlorine")]
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
CHECKED, UNCHECKED = "#2a78d6", "#a9a8a2"  # one document / no document in common


def source_kind(source_id):
    return ("patent" if source_id[:2] in ("US", "WO", "EP")
            else "PubChem assay" if source_id.startswith("aid") else "article")


def build_rows(pair_results, shared_results):
    """pair_results: the 21 matched_molecular_pairs results, in the order of TARGETS x CHANGES;
    shared_results: the 7 run_sql results (monomerid_from, monomerid_to, source_id, assay_name, delta),
    in the order of TARGETS."""
    rows = []
    for t, (target_id, label, kind) in enumerate(TARGETS):
        shared = {}
        for r in shared_results[t]["rows"]:
            shared.setdefault((r["monomerid_from"], r["monomerid_to"]), []).append(
                (r["delta"], r["source_id"], r["assay_name"] or ""))
        for c, (name, _, _) in enumerate(CHANGES):
            result = pair_results[t * len(CHANGES) + c]
            for p in result["rows"]:
                key = (p["monomerid_from"], p["monomerid_to"])
                # Where several documents report both compounds, take the middle one rather than the most
                # dramatic: this is an effect size, not a search for the largest claim.
                order = sorted(shared.get(key, []))
                pick = order[len(order) // 2] if order else None
                rows.append({
                    "target": label, "kind": kind, "target_id": target_id, "change": name,
                    "affinity_type": result["affinity_type"], "monomerid_from": key[0],
                    "monomerid_to": key[1], "delta_p_affinity": round(p["delta_p_affinity"], 2),
                    "shared_source": pick[1] if pick else "", "assay_name": pick[2] if pick else "",
                    "source_kind": source_kind(pick[1]) if pick else "",
                    "delta_in_assay": "" if pick is None else round(pick[0], 2)})
    order = [name for name, _, _ in CHANGES]
    rows.sort(key=lambda row: (row["target_id"], order.index(row["change"]),  # a stable file order
                               row["monomerid_from"], row["monomerid_to"]))
    return rows


def write_csv(rows, path=CSV):
    with open(path, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summary(rows):
    """Pairs, pairs readable inside one document, and medians, per target and change."""
    print("target / change: pairs, checked, median as reported, median in document")
    for target_id, label, _ in TARGETS:
        for name, _, _ in CHANGES:
            here = [r for r in rows if r["target_id"] == target_id and r["change"] == name]
            ok = [r for r in here if r["shared_source"]]
            if here:
                print(label, name, len(here), len(ok),
                      round(statistics.median(r["delta_p_affinity"] for r in here), 2),
                      round(statistics.median(r["delta_in_assay"] for r in ok), 2) if ok else None)


def plot(rows, png=PNG):
    data = []
    for row in rows:  # a pair is plotted where its own document puts it, when one reports both
        row = dict(row)
        row["checked"] = bool(row["shared_source"])
        row["delta"] = float(row["delta_in_assay"]) if row["checked"] else float(row["delta_p_affinity"])
        data.append(row)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "axes.labelcolor": INK2})
    fig, axs = plt.subplots(1, 3, figsize=(17.5, 5.8), sharex=True, sharey=True, facecolor=SURF)
    rng = __import__("random").Random(0)  # jitter only, so overlapping dots stay countable
    for ax, (change, _, heading) in zip(axs, CHANGES):
        ax.set_facecolor(SURF)
        ax.axvline(0, color=INK2, lw=0.9, ls=(0, (3, 3)), zorder=1)
        for y, (target_id, label, kind) in enumerate(TARGETS):
            here = [row for row in data if row["change"] == change and int(row["target_id"]) == target_id]
            if not here:
                continue
            ax.axhline(y, color=GRID, lw=0.8, zorder=0)
            for rows_, colour, alpha, z in (([r for r in here if not r["checked"]], UNCHECKED, 0.65, 2),
                                            ([r for r in here if r["checked"]], CHECKED, 0.5, 3)):
                ax.scatter([r["delta"] for r in rows_], [y + rng.uniform(-0.17, 0.17) for _ in rows_],
                           s=22, color=colour, alpha=alpha, lw=0, zorder=z)
            checked = [r["delta"] for r in here if r["checked"]]
            if checked:
                median = statistics.median(checked)
                ax.plot([median, median], [y - 0.28, y + 0.28], color=INK, lw=2.4, solid_capstyle="butt",
                        zorder=4)
                ax.text(median, y - 0.34, f"{median:+.2f}", color=INK, fontsize=8.5, ha="center",
                        va="bottom", bbox=dict(facecolor=SURF, edgecolor="none", pad=1.2))
                better = round(100 * sum(d > 0 for d in checked) / len(checked))
                ax.text(6.3, y, f"{len(checked)} of {len(here)} · {better}% better",
                        color=INK2, fontsize=8.5, ha="right", va="center")
        ax.set_title(heading, color=INK, fontsize=11.5, loc="left", pad=10)
        ax.set_xlabel("change in potency, log units (right = the group helps)")
        ax.set_xlim(-3.6, 6.4)
        ax.set_xticks([-3, -2, -1, 0, 1, 2, 3])
        ax.set_ylim(len(TARGETS) - 0.5, -0.6)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_bounds(-3.5, 3.5)  # the axis stops where the data does
        ax.tick_params(axis="y", length=0)
    axs[0].set_yticks(range(len(TARGETS)))
    types = {row["target"]: row["affinity_type"] for row in data}
    axs[0].set_yticklabels([f"{label}\n{kind} · {types.get(label, '')}" for _, label, kind in TARGETS],
                           fontsize=9.5, linespacing=1.4)
    handles = [plt.Line2D([], [], marker="o", ls="", ms=7, color=CHECKED, alpha=0.75,
                          label="both values in one document and one assay (median, % better)"),
               plt.Line2D([], [], marker="o", ls="", ms=7, color=UNCHECKED, alpha=0.8,
                          label="no single document and assay reports both — not counted")]
    fig.legend(handles=handles, loc="upper right", frameon=False, fontsize=9.5, ncol=2,
               bbox_to_anchor=(0.995, 1.0))
    fig.suptitle("One fluorine, one methyl, one chlorine: matched pairs read inside a single document",
                 color=INK, fontsize=13.5, x=0.012, ha="left", y=0.98)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(png, dpi=200, facecolor=SURF)
    plt.close(fig)
    print(f"wrote {png} from {len(data)} pairs, {sum(r['checked'] for r in data)} of them readable inside "
          "one document and assay")
