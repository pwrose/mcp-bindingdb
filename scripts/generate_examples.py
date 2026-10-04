"""Regenerate the example transcripts in examples/ by running each query through the MCP server.

    uv run python scripts/generate_examples.py                 # all examples
    uv run python scripts/generate_examples.py --only 05 09    # examples whose slug starts with 05 or 09
    uv run python scripts/generate_examples.py --db data/bindingdb_202611.duckdb

The "## Answer" section of each file is written by hand from the results. An existing answer is kept
when a file is regenerated. If the tool results changed since the answer was written, the script prints
a warning so the answer can be reviewed. New examples get a placeholder answer to fill in.
"""

import argparse
import asyncio
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from mcp import Client

from mcp_bindingdb.db import Database, find_database
from mcp_bindingdb.server import build_server, load_substructure_index

ROOT = Path(__file__).resolve().parents[1]
ANSWER_PLACEHOLDER = "<!-- ANSWER: write from the results above -->\n"
RESULTS_HASH = re.compile(r"<!-- results-sha256: ([0-9a-f]{64}) -->")

PALBOCICLIB = "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C"  # BDBM6309, as stored

# Each step is (tool, arguments, columns to show in the table or None for all).
# An argument value "$prev.rows[0].ki_result_id" is taken from the previous step's result.
EXAMPLES = [
    {
        "slug": "01-egfr-most-potent-ki",
        "title": "Most potent Ki ligands for human EGFR",
        "question": "What are the most potent known Ki ligands for wild-type human EGFR?",
        "steps": [
            ("search_targets", {"query": "EGFR", "organism": "Homo sapiens", "limit": 5},
             ["target_id", "name", "uniprot_raw", "organism", "n_activities", "n_compounds", "matched_name"]),
            ("find_ligands_for_target", {"target_id": 520, "affinity_types": ["Ki"], "limit": 10},
             ["ki_result_id", "monomerid", "compound_name", "relation", "value", "unit", "p_affinity",
              "n_measurements", "source_id", "year"]),
        ],
    },
    {
        "slug": "02-imatinib-target-profile",
        "title": "Imatinib target profile",
        "question": "Which targets does imatinib bind with an affinity better than 100 nM?",
        "steps": [
            ("search_compounds", {"query": "imatinib", "limit": 3},
             ["monomerid", "bdbm_id", "name", "inchi_key", "n_activities", "n_targets", "matched_name"]),
            ("find_targets_for_compound", {"monomerid": 13530, "max_value_nm": 100, "limit": 25},
             ["target_name", "uniprot_raw", "organism", "affinity_type", "relation", "value", "p_affinity",
              "n_measurements"]),
        ],
    },
    {
        "slug": "03-egfr-mutant-selectivity",
        "title": "Selectivity for EGFR T790M/L858R over wild type",
        "question": "Which compounds are most selective for the drug-resistant EGFR T790M/L858R double mutant "
                    "over wild-type EGFR, based on IC50?",
        "steps": [
            ("search_targets", {"query": "P00533", "limit": 5},
             ["target_id", "name", "uniprot_raw", "n_activities", "n_compounds"]),
            ("run_sql", {"sql": """
WITH ic50 AS (
  SELECT monomerid, polymerid, median(value) AS ic50_nm
  FROM activity
  WHERE affinity_type = 'IC50' AND relation = '=' AND polymerid IN (520, 60)
  GROUP BY monomerid, polymerid
)
SELECT c.monomerid, c.name,
       mut.ic50_nm AS ic50_mutant_nm,
       wt.ic50_nm  AS ic50_wildtype_nm,
       round(wt.ic50_nm / mut.ic50_nm, 1) AS fold_selectivity
FROM ic50 mut
JOIN ic50 wt ON wt.monomerid = mut.monomerid AND wt.polymerid = 520
JOIN compound c ON c.monomerid = mut.monomerid
WHERE mut.polymerid = 60 AND mut.ic50_nm <= 10
ORDER BY fold_selectivity DESC
LIMIT 15""".strip(), "limit": 15}, None),
        ],
    },
    {
        "slug": "04-identify-compound-by-inchikey",
        "title": "Identify a compound from its InChIKey",
        "question": "I have the InChIKey BNRNXUUZRGQAQC-UHFFFAOYSA-N. What compound is it, and what does it bind?",
        "steps": [
            ("search_compounds", {"query": "BNRNXUUZRGQAQC-UHFFFAOYSA-N"},
             ["monomerid", "bdbm_id", "name", "smiles", "mol_weight", "n_activities", "n_targets"]),
            ("get_compound", {"monomerid": 14390, "max_synonyms": 15}, None),
        ],
    },
    {
        "slug": "05-herg-liability",
        "title": "hERG potency distribution",
        "question": "How are hERG IC50 values distributed across compounds in BindingDB, and what fraction "
                    "of tested compounds are potent blockers (IC50 below 1 µM)?",
        "steps": [
            ("search_targets", {"query": "hERG", "limit": 3},
             ["target_id", "name", "uniprot_raw", "organism", "n_activities", "n_compounds"]),
            ("get_target", {"target_id": 2132}, None),
            ("run_sql", {"sql": """
WITH per_compound AS (
  SELECT monomerid,
         bool_or(relation <> '>' AND value < 1000) AS potent,
         median(p_affinity) FILTER (WHERE relation = '=') AS median_pic50
  FROM activity
  WHERE polymerid = 2132 AND affinity_type = 'IC50' AND value IS NOT NULL
  GROUP BY monomerid
)
SELECT CASE WHEN median_pic50 IS NULL THEN 'only censored values (<, >)'
            WHEN median_pic50 < 5 THEN 'pIC50 < 5   (> 10 µM)'
            WHEN median_pic50 < 6 THEN 'pIC50 5-6   (1-10 µM)'
            WHEN median_pic50 < 7 THEN 'pIC50 6-7   (100 nM-1 µM)'
            WHEN median_pic50 < 8 THEN 'pIC50 7-8   (10-100 nM)'
            ELSE 'pIC50 >= 8  (< 10 nM)' END AS potency_bin,
       count(*) AS n_compounds,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_compounds,
       count(*) FILTER (WHERE potent) AS n_potent_below_1uM
FROM per_compound
GROUP BY potency_bin
ORDER BY potency_bin""".strip()}, None),
        ],
    },
    {
        "slug": "06-measurement-provenance",
        "title": "Provenance of a single measurement",
        "question": "What is the most potent BTK inhibitor by IC50, and where does that number come from?",
        "steps": [
            ("find_ligands_for_target", {"target_id": 1846, "affinity_types": ["IC50"], "limit": 3},
             ["ki_result_id", "monomerid", "compound_name", "relation", "value", "unit", "assay_name",
              "source_id", "year"]),
            ("get_activity", {"ki_result_id": "$prev.rows[0].ki_result_id"}, None),
        ],
    },
    {
        "slug": "07-binding-kinetics-residence-time",
        "title": "Longest drug-target residence times",
        "question": "Which compound-target pairs have the longest residence time (1/koff) in BindingDB?",
        "steps": [
            ("describe_tables", {"table": "activity"}, None),
            ("run_sql", {"sql": """
SELECT off.compound_name, off.target_name, off.organism,
       off.value AS koff_per_s,
       round(1 / off.value / 60, 1) AS residence_time_min,
       ton.value AS kon_per_M_s,
       kd.value AS kd_nm,
       off.source_id, off.year
FROM activity off
LEFT JOIN activity ton ON ton.ki_result_id = off.ki_result_id AND ton.affinity_type = 'kon'
LEFT JOIN activity kd  ON kd.ki_result_id = off.ki_result_id AND kd.affinity_type = 'Kd'
WHERE off.affinity_type = 'koff' AND off.relation = '=' AND off.value > 0
ORDER BY off.value
LIMIT 15""".strip()}, None),
        ],
    },
    {
        "slug": "08-cdk2-cyclin-e-complex",
        "title": "Inhibitors of the CDK2/cyclin E complex",
        "question": "What is the CDK2/cyclin E complex made of in BindingDB, and what are its most potent "
                    "inhibitors (sub-nanomolar)?",
        "steps": [
            ("search_targets", {"query": "CDK2/Cyclin E", "limit": 3},
             ["target_kind", "target_id", "name", "n_activities", "n_compounds", "matched_name"]),
            ("get_target", {"target_id": 81, "target_kind": "complex"}, None),
            ("find_ligands_for_target", {"target_id": 81, "target_kind": "complex", "max_value_nm": 1,
                                         "limit": 10},
             ["monomerid", "compound_name", "affinity_type", "relation", "value", "p_affinity",
              "n_measurements", "source_id", "year"]),
        ],
    },
    {
        "slug": "09-sars-cov-2-inhibitors",
        "title": "Potent SARS-CoV-2 inhibitors",
        "question": "Find the most potent SARS-CoV-2 inhibitors in BindingDB.",
        "steps": [
            ("search_targets", {"query": "main protease", "organism": "SARS"},
             ["target_id", "name", "organism"]),
            ("run_sql", {"sql": """
SELECT target_kind, target_id, name, uniprot_raw, n_activities, n_compounds
FROM target
WHERE organism = 'Severe acute respiratory syndrome coronavirus 2'
ORDER BY n_activities DESC""".strip()}, None),
            ("find_ligands_for_target", {"target_id": 770, "affinity_types": ["IC50", "Ki"], "max_value_nm": 10,
                                         "limit": 10},
             ["monomerid", "compound_name", "affinity_type", "relation", "value", "p_affinity",
              "assay_name", "source_id", "year"]),
        ],
    },
    {
        "slug": "10-kras-g12c-data-growth",
        "title": "Growth of KRAS G12C inhibitor data",
        "question": "How has the amount of KRAS G12C inhibitor data in BindingDB grown over time, and does "
                    "it come mainly from papers or patents?",
        "steps": [
            ("search_targets", {"query": "KRAS", "limit": 8},
             ["target_id", "name", "uniprot_raw", "n_activities", "n_compounds"]),
            ("run_sql", {"sql": """
SELECT year,
       count(*) AS measurements,
       count(DISTINCT monomerid) AS compounds,
       count(DISTINCT source_id) AS sources,
       count(*) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS from_patents,
       count(*) FILTER (WHERE regexp_matches(source_id, '^[0-9]+$')) AS from_pubmed_articles,
       count(*) FILTER (WHERE source_id ILIKE 'aid%') AS from_pubchem_assays
FROM activity
WHERE uniprot_raw LIKE 'P01116[%G12C%'
GROUP BY year
ORDER BY year""".strip()}, None),
            ("run_sql", {"sql": """
SELECT polymerid, target_name,
       count(*) AS measurements,
       count(*) FILTER (WHERE regexp_matches(source_id, '^[0-9]+$')) AS from_pubmed_articles,
       count(*) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS from_patents,
       min(year) AS first_year,
       max(year) AS last_year
FROM activity
WHERE uniprot = 'P01116' AND uniprot_raw NOT LIKE '%[%'
GROUP BY ALL""".strip()}, None),
        ],
    },
    {
        "slug": "11-patent-dataset-summary",
        "title": "Summary of the patent data",
        "question": "Summarize the data for the patent dataset.",
        "steps": [
            ("run_sql", {"sql": """
WITH a AS (
  SELECT *, CASE WHEN regexp_matches(source_id, '^(US|WO|EP)') THEN 'patent'
                 WHEN regexp_matches(source_id, '^[0-9]+$') THEN 'article (PubMed)'
                 WHEN source_id ILIKE 'aid%' THEN 'PubChem assay'
                 ELSE 'other / none' END AS source_type
  FROM activity
)
SELECT source_type,
       count(*) AS measurements,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct_measurements,
       count(DISTINCT source_id) AS sources,
       count(DISTINCT monomerid) AS compounds,
       count(DISTINCT coalesce(polymerid, -complexid)) AS targets,
       min(year) AS first_year,
       max(year) AS last_year,
       round(median(p_affinity) FILTER (WHERE relation = '='), 2) AS median_p_affinity
FROM a
GROUP BY source_type
ORDER BY measurements DESC""".strip()}, None),
            ("run_sql", {"sql": """
WITH c AS (
  SELECT monomerid,
         bool_or(regexp_matches(source_id, '^(US|WO|EP)')) AS in_patent,
         bool_or(NOT regexp_matches(coalesce(source_id, ''), '^(US|WO|EP)')) AS elsewhere
  FROM activity
  GROUP BY monomerid
)
SELECT count(*) FILTER (WHERE in_patent) AS patent_compounds,
       count(*) FILTER (WHERE in_patent AND NOT elsewhere) AS only_in_patents,
       round(100.0 * count(*) FILTER (WHERE in_patent AND NOT elsewhere)
             / count(*) FILTER (WHERE in_patent), 1) AS pct_only_in_patents
FROM c""".strip()}, None),
            ("run_sql", {"sql": """
SELECT year,
       count(DISTINCT source_id) AS patents,
       count(*) AS measurements,
       count(DISTINCT monomerid) AS compounds,
       count(DISTINCT coalesce(polymerid, -complexid)) AS targets,
       round(count(*) / count(DISTINCT source_id)) AS measurements_per_patent
FROM activity
WHERE regexp_matches(source_id, '^(US|WO|EP)')
GROUP BY year
ORDER BY year""".strip(), "limit": 50}, None),
            ("run_sql", {"sql": """
SELECT affinity_type,
       count(*) AS measurements,
       round(100.0 * count(*) / sum(count(*)) OVER (), 1) AS pct,
       round(100.0 * count(*) FILTER (WHERE relation = '=') / count(*), 1) AS pct_exact,
       round(100.0 * count(*) FILTER (WHERE relation = '<') / count(*), 1) AS pct_less_than,
       round(100.0 * count(*) FILTER (WHERE relation = '>') / count(*), 1) AS pct_greater_than,
       median(value) FILTER (WHERE relation = '=') AS median_exact_value
FROM activity
WHERE regexp_matches(source_id, '^(US|WO|EP)')
GROUP BY affinity_type
ORDER BY measurements DESC""".strip()}, None),
            ("run_sql", {"sql": """
WITH t AS (
  SELECT polymerid, complexid,
         any_value(target_name) AS target_name,
         count(*) AS all_measurements,
         count(*) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS patent_measurements,
         count(DISTINCT source_id) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS patents,
         count(DISTINCT monomerid) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS patent_compounds
  FROM activity
  GROUP BY polymerid, complexid
)
SELECT polymerid, complexid, target_name, patents, patent_measurements, patent_compounds,
       round(100.0 * patent_measurements / all_measurements, 1) AS pct_of_target_data_from_patents
FROM t
ORDER BY patent_measurements DESC
LIMIT 15""".strip()}, None),
        ],
    },
    {
        "slug": "12-most-recently-added-targets",
        "title": "Most recently added targets",
        "question": "List the 5 most recently added targets.",
        "steps": [
            ("run_sql", {"sql": """
SELECT year(entrydate) AS entry_year,
       count(*) AS entries,
       count(*) FILTER (WHERE entrydate IS NULL) AS missing_date,
       max(entrydate) AS latest
FROM entry
GROUP BY entry_year
ORDER BY entry_year DESC NULLS FIRST
LIMIT 8""".strip()}, None),
            ("run_sql", {"sql": """
WITH first AS (
  SELECT a.polymerid, a.complexid,
         arg_min(a.entryid, e.entrydate) AS first_entryid,
         min(e.entrydate) AS first_added
  FROM activity a JOIN entry e USING (entryid)
  GROUP BY a.polymerid, a.complexid
),
ranked AS (
  SELECT f.*, t.target_kind, t.target_id, t.name, t.uniprot, t.uniprot_raw, t.taxid,
         t.n_activities, t.n_compounds
  FROM first f
  JOIN target t ON t.target_id = coalesce(f.polymerid, f.complexid)
   AND t.target_kind = CASE WHEN f.polymerid IS NOT NULL THEN 'polymer' ELSE 'complex' END
  ORDER BY first_added DESC, target_id DESC
  LIMIT 5
)
SELECT r.target_kind, r.target_id, r.name, r.uniprot_raw, r.taxid,
       CAST(r.first_added AS DATE) AS first_added,
       r.n_activities, r.n_compounds,
       (SELECT count(*) FROM first f2
        JOIN target t2 ON t2.target_kind = 'polymer' AND t2.target_id = f2.polymerid
        WHERE t2.uniprot = r.uniprot AND f2.first_added < r.first_added) AS earlier_targets_same_uniprot,
       e.entrytitle,
       (SELECT any_value(source_id) FROM activity a WHERE a.entryid = r.first_entryid) AS source_id
FROM ranked r
JOIN entry e ON e.entryid = r.first_entryid
ORDER BY r.first_added DESC, r.target_id DESC""".strip()}, None),
            ("search_targets", {"query": "Q9ULV8"},
             ["target_kind", "target_id", "name", "uniprot_raw", "organism", "n_activities", "n_compounds"]),
            ("get_target", {"target_id": 2170}, None),
        ],
    },
    {
        "slug": "14-chemotype-target-profile",
        "title": "Target profile of a chemotype",
        "question": "Which proteins bind compounds containing the 4-(thiazol-5-yl)-2-aminopyrimidine chemotype "
                    "(the largest chemotype in example 13), and how many compounds bind each protein?",
        "steps": [
            ("substructure_search", {"query": "s1cncc1-c1ccnc([#7])n1", "limit": 5},
             ["monomerid", "name", "smiles", "n_activities", "n_targets"]),
            ("substructure_search", {"query": "s1cncc1-c1ccnc([#7])n1", "summarize_by_target": True,
                                     "max_value_nm": 10000, "limit": 500},
             ["target_kind", "target_id", "target_name", "uniprot_raw", "organism", "n_compounds",
              "n_measurements", "affinity_types", "best_p_affinity"]),
        ],
    },
    {
        "slug": "15-palbociclib-analogues",
        "title": "Analogues of palbociclib",
        "question": "Which compounds are similar to palbociclib (one of the CDK2/cyclin A2 ligands in example 13), "
                    "which targets do they bind, and how do they fare against CDK2/cyclin A2?",
        "steps": [
            ("search_compounds", {"query": "palbociclib", "limit": 3},
             ["monomerid", "name", "smiles", "n_activities", "n_targets", "matched_name"]),
            ("similarity_search", {"smiles": PALBOCICLIB, "threshold": 0.6, "limit": 15},
             ["monomerid", "name", "similarity", "n_activities", "n_targets"]),
            ("similarity_search", {"smiles": PALBOCICLIB, "threshold": 0.6, "summarize_by_target": True,
                                   "max_value_nm": 1000, "limit": 100},
             ["target_kind", "target_id", "target_name", "uniprot_raw", "n_compounds", "n_measurements",
              "affinity_types", "best_p_affinity"]),
            ("similarity_search", {"smiles": PALBOCICLIB, "threshold": 0.6, "target_id": 97,
                                   "target_kind": "complex", "limit": 50},
             ["monomerid", "compound_name", "similarity", "affinity_type", "relation", "value", "p_affinity",
              "n_measurements", "source_id", "year"]),
        ],
    },
]


def resolve(args, prev):
    out = {}
    for k, v in args.items():
        if isinstance(v, str) and v.startswith("$prev."):
            expr = v[len("$prev."):]  # e.g. rows[0].ki_result_id
            obj = prev
            for part in expr.replace("[", ".[").split("."):
                obj = obj[int(part[1:-1])] if part.startswith("[") else obj[part]
            out[k] = obj
        else:
            out[k] = v
    return out


def cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        s = f"{v:g}"
    elif isinstance(v, list):
        s = ", ".join(map(str, v))
    else:
        s = str(v)
    s = s.replace("|", "\\|").replace("\n", " ")
    return s if len(s) <= 70 else s[:67] + "..."


def table(rows, cols):
    if not rows:
        return "_No rows._\n"
    cols = cols or list(rows[0])
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(cell(r.get(c)) for c in cols) + " |" for r in rows]
    return "\n".join(lines) + "\n"


def render_result(result, cols):
    if not isinstance(result, dict):
        return f"```\n{result}\n```\n"
    parts = []
    if "rows" in result:
        for key, val in result.items():  # fields reported alongside the rows (e.g. substructure_search)
            if key in ("row_count", "truncated", "rows"):
                continue
            if isinstance(val, dict):
                val = ", ".join(f"{k}: `{v}`" if k in ("input", "canonical") else f"{k}: {v}" for k, v in val.items())
            parts.append(f"**{key}:** {val}\n")
        note =f"{result['row_count']} row(s)" + (", more available (truncated by limit)" if result["truncated"] else "")
        shown = f" — table shows selected columns" if cols else ""
        parts.append(f"_{note}{shown}._\n\n" + table(result["rows"], cols))
    else:
        for key, val in result.items():
            if isinstance(val, list) and val and isinstance(val[0], dict):
                parts.append(f"**{key}**\n\n" + table(val, None))
            elif isinstance(val, list):
                parts.append(f"**{key}:** " + (", ".join(map(str, val)) or "_none_") + "\n")
            elif isinstance(val, dict):
                kv = [{"field": k, "value": v} for k, v in val.items()]
                parts.append(f"**{key}**\n\n" + table(kv, ["field", "value"]))
            else:
                parts.append(f"**{key}:** {cell(val)}\n")
    raw = json.dumps(result, indent=2, ensure_ascii=False, default=str)
    parts.append(f"<details><summary>Raw tool result (JSON)</summary>\n\n```json\n{raw}\n```\n\n</details>\n")
    return "\n".join(parts)




def existing_answer(path: Path) -> tuple[str | None, str | None]:
    """Return (answer text, results hash recorded with it) from an existing transcript."""
    if not path.exists():
        return None, None
    text = path.read_text()
    m = RESULTS_HASH.search(text)
    _, sep, answer = text.partition("## Answer\n")
    if not sep or answer.strip() == ANSWER_PLACEHOLDER.strip():
        return None, m.group(1) if m else None
    return answer.lstrip("\n"), m.group(1) if m else None


async def run_example(client: Client, ex: dict, release: str) -> tuple[str, str]:
    """Run one example's tool calls; return (markdown up to the answer, hash of the results)."""
    md = [f"# {ex['title']}\n",
          f"> **Question:** {ex['question']}\n",
          f"BindingDB release {release} · server `mcp-bindingdb` 0.1.0 · generated {date.today()}\n",
          "## Tool calls\n"]
    prev = None
    results = []
    for i, (tool, args, cols) in enumerate(ex["steps"], 1):
        args = resolve(args, prev)
        res = await client.call_tool(tool, args)
        if res.is_error:
            result = res.content[0].text
        else:
            result = res.structured_content
            prev = result
        results.append(result)
        shown_args = dict(args)
        sql = shown_args.pop("sql", None)
        md.append(f"### {i}. `{tool}`\n")
        md.append("```json\n" + json.dumps(shown_args, ensure_ascii=False) + "\n```\n")
        if sql:
            md.append("```sql\n" + sql + "\n```\n")
        md.append(("**Error:**\n\n" if res.is_error else "**Result:**\n\n") + render_result(result, cols))
    digest = hashlib.sha256(json.dumps(results, sort_keys=True, default=str).encode()).hexdigest()
    return "\n".join(md), digest


async def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--db", type=Path, help="DuckDB file (default: newest data/bindingdb_*.duckdb)")
    p.add_argument("--out", type=Path, default=ROOT / "examples")
    p.add_argument("--only", nargs="+", metavar="PREFIX", help="Only examples whose slug starts with these")
    p.add_argument("--reset-answers", action="store_true", help="Replace existing answers with placeholders")
    args = p.parse_args()

    db = Database(args.db or find_database())
    release = db.build_info().get("release", "?")
    args.out.mkdir(parents=True, exist_ok=True)
    selected = [ex for ex in EXAMPLES if not args.only or ex["slug"].startswith(tuple(args.only))]
    needs_review = []
    async with Client(build_server(db, load_substructure_index(db))) as client:
        for ex in selected:
            path = args.out / f"{ex['slug']}.md"
            answer, old_digest = (None, None) if args.reset_answers else existing_answer(path)
            body, digest = await run_example(client, ex, release)
            if answer is None:
                answer = ANSWER_PLACEHOLDER
                needs_review.append(f"{path.name}: needs an answer")
            elif old_digest != digest:
                needs_review.append(f"{path.name}: results changed since the answer was written")
            path.write_text(f"{body}\n<!-- results-sha256: {digest} -->\n\n## Answer\n\n{answer}")
            print(f"wrote {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")
    for msg in needs_review:
        print(f"REVIEW {msg}")


if __name__ == "__main__":
    asyncio.run(main())
