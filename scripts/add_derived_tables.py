"""Add query-friendly derived tables to a BindingDB DuckDB file.

Runs on the DuckDB file only (no MySQL needed) and is idempotent. Creates:

  activity       one row per measured value (Ki/Kd/IC50/EC50/kon/koff) with the
                 qualifier split off, the value parsed to DOUBLE, its unit, pAffinity,
                 and denormalized target / compound / assay / citation columns
  compound       one row per monomer with a preferred name and activity counts
  compound_name  distinct compound synonyms (names, CHEMBL ids, PubChem cid_N, patent labels)
  target         one row per polymer/complex target with UniProt accession and counts
  target_name    distinct target synonyms
"""

import argparse
import sys
import time
from pathlib import Path

import duckdb

# BindingDB reports Ki/Kd/IC50/EC50 in nM, kon in M^-1 s^-1, koff in s^-1.
AFFINITY_COLUMNS = [
    ("ki", "Ki", "nM"),
    ("kd", "Kd", "nM"),
    ("ic50", "IC50", "nM"),
    ("ec50", "EC50", "nM"),
    ("kon", "kon", "M-1 s-1"),
    ("koff", "koff", "s-1"),
]

SQL = """
-- Target per reactant set. Polymer/complex id 0 are placeholders ("A protein", "A Complex");
-- when a complex is present the polymer is a placeholder, so the complex is the target.
CREATE OR REPLACE TEMP TABLE rs AS
SELECT r.reactant_set_id,
       r.inhibitor_monomerid AS monomerid,
       CASE WHEN r.enzyme_complexid > 0 THEN NULL ELSE NULLIF(r.enzyme_polymerid, 0) END AS polymerid,
       NULLIF(r.enzyme_complexid, 0) AS complexid
FROM enzyme_reactant_set r;

-- One citation per entry (21 of ~57k entries cite two articles; keep the lowest articleid).
CREATE OR REPLACE TEMP TABLE entry_article AS
SELECT entryid, min(articleid) AS articleid FROM entry_citation GROUP BY entryid;

CREATE OR REPLACE TABLE target_name AS
SELECT DISTINCT 'polymer' AS target_kind, polymerid AS target_id, trim(name) AS name
FROM (
  SELECT polymerid, display_name AS name FROM polymer
  UNION ALL SELECT polymerid, short_name FROM polymer
  UNION ALL SELECT polymerid, name FROM poly_name
)
WHERE polymerid > 0 AND name IS NOT NULL AND trim(name) <> ''
UNION
SELECT DISTINCT 'complex', complexid, trim(name)
FROM (SELECT complexid, display_name AS name FROM complex
      UNION ALL SELECT complexid, name FROM complex_name)
WHERE complexid > 0 AND name IS NOT NULL AND trim(name) <> '';

CREATE OR REPLACE TABLE compound_name AS
SELECT DISTINCT monomerid, trim(name) AS name
FROM mono_name WHERE monomerid IS NOT NULL AND name IS NOT NULL AND trim(name) <> '';

-- Preferred name: rank real names (no database ids, patent or compound-number labels)
-- ahead of labels, names without digits (trade/INN names) ahead of others, then shortest.
-- Compounds known only by labels such as "US12466803, Example 2" fall back to the shortest label.
CREATE OR REPLACE TEMP TABLE preferred_name AS
SELECT monomerid,
       arg_min(name, (is_label, regexp_matches(name, '[0-9]'), length(name))) AS name
FROM (
  SELECT monomerid, name,
         regexp_matches(name, '^(CHEMBL[0-9]+|cid_[0-9]+|BDBM[0-9]+)$')
         OR regexp_matches(name, '^(US|WO|EP)[0-9]')
         OR regexp_matches(name, ',\\s*(Example|Compound|Cpd|Cmpd|Ex\\.?|Table|Reference)\\b', 'i')
         OR regexp_matches(name, '^med\\.')
         OR length(name) < 3 AS is_label
  FROM compound_name
)
GROUP BY monomerid;

CREATE OR REPLACE TABLE activity AS
WITH vals AS (
  {unpivot}
),
parsed AS (
  SELECT *,
         regexp_extract(trim(raw_value), '^([<>~=]*)\\s*(.*)$', ['rel', 'num']) AS p
  FROM vals
)
SELECT k.ki_result_id,
       k.reactant_set_id,
       k.entryid,
       v.affinity_type,
       CASE WHEN v.p.rel = '' THEN '=' ELSE v.p.rel END AS relation,
       TRY_CAST(v.p.num AS DOUBLE) AS value,
       v.unit,
       CASE WHEN v.unit = 'nM' AND TRY_CAST(v.p.num AS DOUBLE) > 0
            THEN round(9 - log10(TRY_CAST(v.p.num AS DOUBLE)), 2) END AS p_affinity,
       trim(v.raw_value) AS raw_value,
       nullif(trim(v.raw_uncert), '') AS uncertainty,
       rs.monomerid,
       pn.name AS compound_name,
       m.inchi_key,
       rs.polymerid,
       rs.complexid,
       coalesce(c.display_name, p.display_name) AS target_name,
       regexp_extract(p.unpid1, '^[A-Za-z0-9]+') AS uniprot,
       p.unpid1 AS uniprot_raw,
       p.scientific_name AS organism,
       p.taxid,
       k.ph,
       k.temp AS temp_k,
       a.assay_name,
       ea.articleid,
       ar.pmid AS source_id,
       ar.doi,
       NULLIF(ar.year, 0) AS year  -- 0 is used for "unknown" in article.year
FROM ki_result k
JOIN parsed v USING (ki_result_id)
JOIN rs USING (reactant_set_id)
LEFT JOIN monomer m ON m.monomerid = rs.monomerid
LEFT JOIN preferred_name pn ON pn.monomerid = rs.monomerid
LEFT JOIN polymer p ON p.polymerid = rs.polymerid
LEFT JOIN complex c ON c.complexid = rs.complexid
LEFT JOIN assay a ON a.entryid = k.entryid AND a.assayid = k.assayid
LEFT JOIN entry_article ea ON ea.entryid = k.entryid
LEFT JOIN article ar ON ar.articleid = ea.articleid
ORDER BY affinity_type, polymerid, complexid, value;

CREATE OR REPLACE TABLE compound AS
SELECT m.monomerid,
       'BDBM' || m.monomerid AS bdbm_id,
       pn.name,
       m.inchi_key,
       m.smiles_string AS smiles,
       m.emp_form AS formula,
       TRY_CAST(m.weight AS DOUBLE) AS mol_weight,
       m.type,
       m.het_pdb,
       m.n_pdb_ids_exact,
       coalesce(s.n_activities, 0) AS n_activities,
       coalesce(s.n_targets, 0) AS n_targets
FROM monomer m
LEFT JOIN preferred_name pn USING (monomerid)
LEFT JOIN (
  SELECT monomerid, count(*) AS n_activities,
         count(DISTINCT coalesce(polymerid, -complexid)) AS n_targets
  FROM activity GROUP BY monomerid
) s USING (monomerid);

CREATE OR REPLACE TABLE target AS
WITH s AS (
  SELECT polymerid, complexid, count(*) AS n_activities, count(DISTINCT monomerid) AS n_compounds
  FROM activity GROUP BY polymerid, complexid
)
SELECT 'polymer' AS target_kind, p.polymerid AS target_id, p.display_name AS name,
       regexp_extract(p.unpid1, '^[A-Za-z0-9]+') AS uniprot, p.unpid1 AS uniprot_raw,
       p.scientific_name AS organism, p.taxid, p.type, p.res_count, p.n_pdb_ids,
       p.chembl_id, coalesce(s.n_activities, 0) AS n_activities,
       coalesce(s.n_compounds, 0) AS n_compounds
FROM polymer p LEFT JOIN s ON s.polymerid = p.polymerid
WHERE p.polymerid > 0
UNION ALL
SELECT 'complex', c.complexid, c.display_name, NULL, NULL, NULL, NULL, c.type, NULL,
       c.n_pdb_ids, c.chembl_id, coalesce(s.n_activities, 0), coalesce(s.n_compounds, 0)
FROM complex c LEFT JOIN s ON s.complexid = c.complexid AND s.polymerid IS NULL
WHERE c.complexid > 0;
"""


def build_sql() -> str:
    unpivot = "\n  UNION ALL\n  ".join(
        f"SELECT ki_result_id, '{label}' AS affinity_type, '{unit}' AS unit, "
        f"{col} AS raw_value, {col}_uncert AS raw_uncert FROM ki_result WHERE {col} IS NOT NULL"
        for col, label, unit in AFFINITY_COLUMNS
    )
    return SQL.replace("{unpivot}", unpivot)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("database", type=Path)
    args = p.parse_args()

    t0 = time.time()
    con = duckdb.connect(str(args.database))
    con.execute(build_sql())
    for t in ["activity", "compound", "compound_name", "target", "target_name"]:
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"  {t:<14} {n:>12,}")
    unparsed = con.execute("SELECT count(*) FROM activity WHERE value IS NULL").fetchone()[0]
    print(f"  activity rows with unparseable value: {unparsed}")
    con.execute("CHECKPOINT")
    con.close()
    print(f"Derived tables built in {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
