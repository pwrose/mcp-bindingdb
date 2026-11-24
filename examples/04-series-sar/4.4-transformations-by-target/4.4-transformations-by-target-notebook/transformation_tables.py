"""Code 2: The medians and tenfold counts quoted, from the notebook 4.4-transformations-by-target-notebook.ipynb.

Written by claude-sonnet-5-5 during the analysis. The notebook imports this file, so keep
it in the same folder as the notebook."""

import collections
import statistics

from plot_transformation_effects import CHANGES, TARGETS


def _checked(r):
    return bool(r["shared_source"])


def median_table(rows):
    """Median change per target and group, over the pairs readable inside one document (count in brackets)."""
    for target_id, label, _ in TARGETS:
        cells = []
        for name, _, _ in CHANGES:
            ok = [r["delta_in_assay"] for r in rows if r["target_id"] == target_id and r["change"] == name
                  and _checked(r)]
            cells.append(f"{statistics.median(ok):+.2f} ({len(ok)})")
        print(label, *cells)


def tenfold_table(rows):
    """Pairs that move potency tenfold or more: as reported, and read inside one document."""
    for name, _, _ in CHANGES:
        here = [r for r in rows if r["change"] == name]
        ok = [r for r in here if _checked(r)]
        print(name, len(here), "->", len(ok), "checked;",
              "tenfold+ as reported", sum(abs(r["delta_p_affinity"]) >= 1 for r in here),
              "inside one document", sum(abs(r["delta_in_assay"]) >= 1 for r in ok))


def cost_table(rows):
    """What the one-document rule cost per target, and what sits behind the surviving pairs."""
    for target_id, label, _ in TARGETS:
        here = [r for r in rows if r["target_id"] == target_id]
        ok = [r for r in here if _checked(r)]
        docs = {}
        for r in ok:
            docs.setdefault(r["shared_source"], r["source_kind"])
        counts = collections.Counter(r["shared_source"] for r in ok)
        top = counts.most_common(1)[0]
        kinds = collections.Counter(docs.values())
        print(label, len(here), len(ok), f"{100 * len(ok) / len(here):.0f}%", len(docs), dict(kinds), top)
    ok = [r for r in rows if _checked(r)]
    print("documents", len({r["shared_source"] for r in ok}), "document+assay",
          len({(r["shared_source"], r["assay_name"]) for r in ok}))
