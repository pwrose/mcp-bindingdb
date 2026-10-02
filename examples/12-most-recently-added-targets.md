# Most recently added targets

> **Question:** List the 5 most recently added targets.

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `run_sql`

```json
{}
```

```sql
SELECT year(entrydate) AS entry_year,
       count(*) AS entries,
       count(*) FILTER (WHERE entrydate IS NULL) AS missing_date,
       max(entrydate) AS latest
FROM entry
GROUP BY entry_year
ORDER BY entry_year DESC NULLS FIRST
LIMIT 8
```

**Result:**

_8 row(s)._

| entry_year | entries | missing_date | latest |
|---|---|---|---|
| 2026 | 1692 | 0 | 2026-09-23T00:00:00 |
| 2025 | 2375 | 0 | 2025-12-31T00:00:00 |
| 2024 | 2774 | 0 | 2024-12-23T00:00:00 |
| 2023 | 2568 | 0 | 2023-12-29T00:00:00 |
| 2022 | 3021 | 0 | 2022-12-30T00:00:00 |
| 2021 | 3839 | 0 | 2021-12-28T00:00:00 |
| 2020 | 5718 | 0 | 2020-12-21T00:00:00 |
| 2019 | 2163 | 0 | 2019-12-30T00:00:00 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 8,
  "truncated": false,
  "rows": [
    {
      "entry_year": 2026,
      "entries": 1692,
      "missing_date": 0,
      "latest": "2026-09-23T00:00:00"
    },
    {
      "entry_year": 2025,
      "entries": 2375,
      "missing_date": 0,
      "latest": "2025-12-31T00:00:00"
    },
    {
      "entry_year": 2024,
      "entries": 2774,
      "missing_date": 0,
      "latest": "2024-12-23T00:00:00"
    },
    {
      "entry_year": 2023,
      "entries": 2568,
      "missing_date": 0,
      "latest": "2023-12-29T00:00:00"
    },
    {
      "entry_year": 2022,
      "entries": 3021,
      "missing_date": 0,
      "latest": "2022-12-30T00:00:00"
    },
    {
      "entry_year": 2021,
      "entries": 3839,
      "missing_date": 0,
      "latest": "2021-12-28T00:00:00"
    },
    {
      "entry_year": 2020,
      "entries": 5718,
      "missing_date": 0,
      "latest": "2020-12-21T00:00:00"
    },
    {
      "entry_year": 2019,
      "entries": 2163,
      "missing_date": 0,
      "latest": "2019-12-30T00:00:00"
    }
  ]
}
```

</details>

### 2. `run_sql`

```json
{}
```

```sql
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
ORDER BY r.first_added DESC, r.target_id DESC
```

**Result:**

_5 row(s)._

| target_kind | target_id | name | uniprot_raw | taxid | first_added | n_activities | n_compounds | earlier_targets_same_uniprot | entrytitle | source_id |
|---|---|---|---|---|---|---|---|---|---|---|
| polymer | 2170 | Thyrotropin-releasing hormone-degrading ectoenzyme | Q9UKU6 | 9606 | 2026-09-23 | 442 | 442 | 0 | NOVEL SPIRO COMPOUND | US20260132127A1 |
| complex | 508 | Alpha-1-antitrypsin/Neutrophil elastase |  |  | 2026-09-21 | 152 | 152 | 0 | 1H-pyrazolo[4,3-G]isoquinoline and 1H-pyrazolo[4,3-g]quinoline deri... | US12624028B2 |
| polymer | 2171 | E3 ubiquitin-protein ligase CBL-C [46-435] | Q9ULV8[46-435] | 9606 | 2026-09-17 | 295 | 295 | 2 | SUBSTITUTED 1H-PYRAZOLO-PYRIDINE AND -PYRIMIDINE COMPOUNDS | US20260125375A1 |
| polymer | 2165 | Replicase polyprotein 1a | P0C6U2 | 11137 | 2026-09-16 | 12 | 12 | 0 | COMPOUNDS, COMPOSITIONS, AND METHODS OF TREATING RNA VIRAL INFECTIONS | US20260124192A1 |
| complex | 505 | Dynamin-1-like protein [1-699] and Mitochondrial dynamics protein M... |  |  | 2026-09-16 | 54 | 54 | 0 | DYNAMIN-1-LIKE PROTEIN INHIBITORS AND USES THEREOF | US20260125372A1 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 5,
  "truncated": false,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 2170,
      "name": "Thyrotropin-releasing hormone-degrading ectoenzyme",
      "uniprot_raw": "Q9UKU6",
      "taxid": "9606",
      "first_added": "2026-09-23",
      "n_activities": 442,
      "n_compounds": 442,
      "earlier_targets_same_uniprot": 0,
      "entrytitle": "NOVEL SPIRO COMPOUND",
      "source_id": "US20260132127A1"
    },
    {
      "target_kind": "complex",
      "target_id": 508,
      "name": "Alpha-1-antitrypsin/Neutrophil elastase",
      "uniprot_raw": null,
      "taxid": null,
      "first_added": "2026-09-21",
      "n_activities": 152,
      "n_compounds": 152,
      "earlier_targets_same_uniprot": 0,
      "entrytitle": "1H-pyrazolo[4,3-G]isoquinoline and 1H-pyrazolo[4,3-g]quinoline derivatives as alpha-1-antitrypsin modulators for treating alpha-1-antitrypsin deficiency (AATD)",
      "source_id": "US12624028B2"
    },
    {
      "target_kind": "polymer",
      "target_id": 2171,
      "name": "E3 ubiquitin-protein ligase CBL-C [46-435]",
      "uniprot_raw": "Q9ULV8[46-435]",
      "taxid": "9606",
      "first_added": "2026-09-17",
      "n_activities": 295,
      "n_compounds": 295,
      "earlier_targets_same_uniprot": 2,
      "entrytitle": "SUBSTITUTED 1H-PYRAZOLO-PYRIDINE AND -PYRIMIDINE COMPOUNDS",
      "source_id": "US20260125375A1"
    },
    {
      "target_kind": "polymer",
      "target_id": 2165,
      "name": "Replicase polyprotein 1a",
      "uniprot_raw": "P0C6U2",
      "taxid": "11137",
      "first_added": "2026-09-16",
      "n_activities": 12,
      "n_compounds": 12,
      "earlier_targets_same_uniprot": 0,
      "entrytitle": "COMPOUNDS, COMPOSITIONS, AND METHODS OF TREATING RNA VIRAL INFECTIONS",
      "source_id": "US20260124192A1"
    },
    {
      "target_kind": "complex",
      "target_id": 505,
      "name": "Dynamin-1-like protein [1-699] and Mitochondrial dynamics protein MID49 [126-454]",
      "uniprot_raw": null,
      "taxid": null,
      "first_added": "2026-09-16",
      "n_activities": 54,
      "n_compounds": 54,
      "earlier_targets_same_uniprot": 0,
      "entrytitle": "DYNAMIN-1-LIKE PROTEIN INHIBITORS AND USES THEREOF",
      "source_id": "US20260125372A1"
    }
  ]
}
```

</details>

### 3. `search_targets`

```json
{"query": "Q9ULV8"}
```

**Result:**

_3 row(s) — table shows selected columns._

| target_kind | target_id | name | uniprot_raw | organism | n_activities | n_compounds |
|---|---|---|---|---|---|---|
| polymer | 1721 | E3 ubiquitin-protein ligase CBL-C | Q9ULV8 |  | 839 | 834 |
| polymer | 2171 | E3 ubiquitin-protein ligase CBL-C [46-435] | Q9ULV8[46-435] |  | 295 | 295 |
| polymer | 1973 | E3 ubiquitin-protein ligase CBL-C [47-435] | Q9ULV8[47-435] |  | 197 | 197 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 3,
  "truncated": false,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 1721,
      "name": "E3 ubiquitin-protein ligase CBL-C",
      "uniprot": "Q9ULV8",
      "uniprot_raw": "Q9ULV8",
      "organism": "",
      "type": "Protein",
      "n_activities": 839,
      "n_compounds": 834
    },
    {
      "target_kind": "polymer",
      "target_id": 2171,
      "name": "E3 ubiquitin-protein ligase CBL-C [46-435]",
      "uniprot": "Q9ULV8",
      "uniprot_raw": "Q9ULV8[46-435]",
      "organism": null,
      "type": "Protein",
      "n_activities": 295,
      "n_compounds": 295
    },
    {
      "target_kind": "polymer",
      "target_id": 1973,
      "name": "E3 ubiquitin-protein ligase CBL-C [47-435]",
      "uniprot": "Q9ULV8",
      "uniprot_raw": "Q9ULV8[47-435]",
      "organism": null,
      "type": "Protein",
      "n_activities": 197,
      "n_compounds": 197
    }
  ]
}
```

</details>

### 4. `get_target`

```json
{"target_id": 2170}
```

**Result:**

**target**

| field | value |
|---|---|
| target_kind | polymer |
| target_id | 2170 |
| name | Thyrotropin-releasing hormone-degrading ectoenzyme |
| uniprot | Q9UKU6 |
| uniprot_raw | Q9UKU6 |
| organism |  |
| taxid | 9606 |
| type | Protein |
| res_count | 1069 |
| n_pdb_ids | 0 |
| chembl_id |  |
| n_activities | 442 |
| n_compounds | 442 |
| unpid2 |  |
| common_name |  |
| topology |  |
| weight | 122140.45 |
| pdb_ids |  |

**synonyms:** PAP-II, TRH-DE, Thyroliberinase, TRH-degrading ectoenzyme, Pyroglutamyl-peptidase II, TRH-specific aminopeptidase, Thyrotropin-releasing hormone-degrading ectoenzyme

**measurements_by_type**

| affinity_type | n_measurements | n_compounds | best_p_affinity |
|---|---|---|---|
| IC50 | 442 | 442 | 9 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "target": {
    "target_kind": "polymer",
    "target_id": 2170,
    "name": "Thyrotropin-releasing hormone-degrading ectoenzyme",
    "uniprot": "Q9UKU6",
    "uniprot_raw": "Q9UKU6",
    "organism": null,
    "taxid": "9606",
    "type": "Protein",
    "res_count": 1069,
    "n_pdb_ids": 0,
    "chembl_id": null,
    "n_activities": 442,
    "n_compounds": 442,
    "unpid2": null,
    "common_name": null,
    "topology": null,
    "weight": "122140.45",
    "pdb_ids": ""
  },
  "synonyms": [
    "PAP-II",
    "TRH-DE",
    "Thyroliberinase",
    "TRH-degrading ectoenzyme",
    "Pyroglutamyl-peptidase II",
    "TRH-specific aminopeptidase",
    "Thyrotropin-releasing hormone-degrading ectoenzyme"
  ],
  "measurements_by_type": [
    {
      "affinity_type": "IC50",
      "n_measurements": 442,
      "n_compounds": 442,
      "best_p_affinity": 9.0
    }
  ]
}
```

</details>

<!-- results-sha256: 42745f9e21ed4385d470e7d0c64ab8a415ab49c1fea97761f5dadb8d2d773861 -->

## Answer

BindingDB doesn't record when a target was created, so "added" here means **the deposition date
(`entry.entrydate`) of the earliest entry that has a measurement for the target**. Step 1 checks that
this date is filled in for every recent entry; the newest is 2026-09-23.

| # | First added | Target | Kind | Measurements | Source |
|---|---|---|---|---|---|
| 1 | 2026-09-23 | Thyrotropin-releasing hormone-degrading ectoenzyme (TRH-DE, Q9UKU6), human | protein | 442 IC50s | US20260132127A1 |
| 2 | 2026-09-21 | Alpha-1-antitrypsin/Neutrophil elastase | complex | 152 | US12624028B2 |
| 3 | 2026-09-17 | E3 ubiquitin-protein ligase CBL-C [46-435], human | protein construct | 295 | US20260125375A1 |
| 4 | 2026-09-16 | Replicase polyprotein 1a (P0C6U2), taxid 11137 (human coronavirus 229E) | protein | 12 | US20260124192A1 |
| 5 | 2026-09-16 | Dynamin-1-like protein [1-699] + MID49 [126-454] | complex | 54 | US20260125372A1 |

All five came from patents, and each was added with a single deposition. Every one of them has as
many compounds as measurements, so each compound was measured once.

**Not all of them are new proteins.**
- CBL-C [46-435] is a new *construct*: two CBL-C targets already existed (step 3), the full-length protein (1721, 839 measurements) and a one-residue-shorter [47-435] construct (1973). For a CBL-C question, combine all three.
- The two complexes are new *target definitions*. The alpha-1-antitrypsin/elastase complex reflects the patent's assay design: it describes compounds as AAT modulators for AAT deficiency, and they are measured against the AAT–elastase pair rather than one protein.
- TRH-DE and the 229E replicase have no earlier target with the same UniProt accession, so they are the genuinely new proteins in this list.

**Organism is missing for new targets.** `get_target` for TRH-DE (step 4) returns `organism: null`
even though `taxid` is 9606 (human), and the three CBL-C targets in step 3 have no organism either.
Complexes have no taxid at all. To filter recent targets by species, use `taxid` rather than `organism`.

The order is only as precise as the dates: targets 4 and 5 share a date (2026-09-16), so they are
ordered by target id.
