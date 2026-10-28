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
`"[H][*:1] >> C[*:1]"` and `"[H][*:1] >> Cl[*:1]"` with `max_compounds: 1500`. The ligand set per target
is one row per compound at its most potent exact ('=') measurement in nM of the single affinity type the
target has most of, as every SAR tool in the server uses.

    python plot_transformation_effects.py [path/to/bindingdb_202610.duckdb]

The pairs are cached in transformation_deltas.csv, so the plot can be redrawn without the database. The
first run reproduces that file from the database with mcp_bindingdb's own `sar` module, which is what the
tool calls (needs duckdb and RDKit; it takes about three minutes for the seven targets).
"""
import csv
import math
import os
import statistics
import sys

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
MAX_COMPOUNDS = 1500
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
CHECKED, UNCHECKED = "#2a78d6", "#a9a8a2"  # one document / no document in common


def source_kind(source_id):
    return ("patent" if source_id[:2] in ("US", "WO", "EP")
            else "PubChem assay" if source_id.startswith("aid") else "article")


def collect(database):
    """Rebuild the CSV: each target's matched pairs for each change, with the document check."""
    from mcp_bindingdb import sar
    from mcp_bindingdb.db import Database

    db = Database(database)
    wanted = {name: {sar.tidy_fragment(part.strip()) for part in change.split(">>")}
              for name, change, _ in CHANGES}
    rows = []
    for target_id, label, kind in TARGETS:
        affinity_type = db.one(
            """SELECT affinity_type FROM activity
               WHERE polymerid = ? AND relation = '=' AND unit = 'nM' AND p_affinity IS NOT NULL
                 AND affinity_type IN ('Ki', 'Kd', 'IC50', 'EC50')
               GROUP BY affinity_type ORDER BY count(*) DESC, affinity_type""", [target_id])["affinity_type"]
        ligands = db.rows(
            """SELECT monomerid, any_value(smiles) AS smiles, round(max(p_affinity), 2) AS p_affinity
               FROM activity JOIN compound USING (monomerid)
               WHERE polymerid = ? AND affinity_type = ? AND relation = '=' AND unit = 'nM'
                 AND p_affinity IS NOT NULL AND smiles IS NOT NULL
               GROUP BY monomerid ORDER BY p_affinity DESC, monomerid""",
            [target_id, affinity_type], limit=MAX_COMPOUNDS)
        mols = sar.molecules([row["smiles"] for row in ligands])
        variants = [[] if mol is None else sar.single_cut_variants(mol, include_hydrogens=True) for mol in mols]
        pairs, _ = sar.matched_pairs(variants)
        found = []
        for (i, j), (_, variable_i, variable_j) in pairs.items():
            a, b = ligands[i], ligands[j]
            from_group, to_group = sar.tidy_fragment(variable_i), sar.tidy_fragment(variable_j)
            if sar.heavy_atoms(from_group) > sar.heavy_atoms(to_group) or (
                    sar.heavy_atoms(from_group) == sar.heavy_atoms(to_group) and from_group > to_group):
                a, b, from_group, to_group = b, a, to_group, from_group
            for name, groups in wanted.items():
                if {from_group, to_group} == groups:
                    found.append((name, a, b))
        # Which documents report each of these compounds, and at what value there.
        ids = sorted({compound["monomerid"] for _, a, b in found for compound in (a, b)})
        values = db.rows(
            f"""SELECT monomerid, source_id, assay_name, min(value) AS nm FROM activity
                WHERE polymerid = ? AND affinity_type = ? AND relation = '=' AND unit = 'nM'
                  AND source_id IS NOT NULL AND value > 0
                  AND monomerid IN ({','.join('?' * len(ids))})
                GROUP BY monomerid, source_id, assay_name""",
            [target_id, affinity_type, *ids], limit=200000)
        by_id = {}
        for row in values:
            by_id.setdefault(row["monomerid"], {})[(row["source_id"], row["assay_name"])] = row["nm"]
        for name, a, b in found:
            here, there = by_id.get(a["monomerid"], {}), by_id.get(b["monomerid"], {})
            shared = set(here) & set(there)
            # Where several documents report both compounds, take the middle one rather than the most
            # dramatic: this is an effect size, not a search for the largest claim.
            order = sorted(shared,  # the key breaks ties, so the same data gives the same answer
                           key=lambda k: (math.log10(here[k]) - math.log10(there[k]), k))
            key = order[len(order) // 2] if order else None
            rows.append({
                "target": label, "kind": kind, "target_id": target_id, "change": name,
                "affinity_type": affinity_type, "monomerid_from": a["monomerid"],
                "monomerid_to": b["monomerid"],
                "delta_p_affinity": round(b["p_affinity"] - a["p_affinity"], 2),
                "shared_source": key[0] if key else "", "assay_name": key[1] if key else "",
                "source_kind": source_kind(key[0]) if key else "",
                "delta_in_assay": "" if key is None else
                                  round(math.log10(here[key]) - math.log10(there[key]), 2)})
        print(f"{label}: {affinity_type}, {len(ligands)} compounds, {len(pairs)} pairs, "
              f"{len(found)} of the three changes", flush=True)
    order = [name for name, _, _ in CHANGES]
    rows.sort(key=lambda row: (row["target_id"], order.index(row["change"]),  # a stable file order
                               row["monomerid_from"], row["monomerid_to"]))
    with open(CSV, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


if os.path.exists(CSV):
    data = list(csv.DictReader(open(CSV)))
else:
    data = collect(sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
        "~/GitRepositories/mcp-bindingdb/data/bindingdb_202610.duckdb"))
for row in data:  # a pair is plotted where its own document puts it, when one reports both
    row["delta_p_affinity"] = float(row["delta_p_affinity"])
    row["checked"] = bool(row["shared_source"])
    row["delta"] = float(row["delta_in_assay"]) if row["checked"] else row["delta_p_affinity"]

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
        for rows_, colour, alpha, z in ((([r for r in here if not r["checked"]]), UNCHECKED, 0.65, 2),
                                        (([r for r in here if r["checked"]]), CHECKED, 0.5, 3)):
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
fig.savefig(PNG, dpi=200, facecolor=SURF)
checked_n = sum(row["checked"] for row in data)
print(f"wrote {PNG} from {len(data)} pairs, {checked_n} of them readable inside one document and assay")
