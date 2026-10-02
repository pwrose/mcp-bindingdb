# Growth of KRAS G12C inhibitor data

> **Question:** How has the amount of KRAS G12C inhibitor data in BindingDB grown over time, and does it come mainly from papers or patents?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "KRAS", "limit": 8}
```

**Result:**

_8 row(s), more available (truncated by limit) — table shows selected columns._

| target_id | name | uniprot_raw | n_activities | n_compounds |
|---|---|---|---|---|
| 1006 | GTPase KRas [G12D] | P01116[G12D] | 4824 | 3250 |
| 50006227 | GTPase KRas | P01116 | 3166 | 2657 |
| 1398 | GTPase KRas [G12V] | P01116[G12V] | 2912 | 2103 |
| 864 | GTPase KRas [G12C] | P01116[G12C] | 2610 | 2077 |
| 1396 | GTPase KRas [G13C] | P01116[G13C] | 1404 | 1329 |
| 1403 | GTPase KRas [G13D] | P01116[G13D] | 1278 | 1236 |
| 1090 | GTPase KRas [1-169,G12C,C118A] | P01116[1-169,G12C,C118A] | 1269 | 844 |
| 1374 | GTPase KRas [G12S] | P01116[G12S] | 791 | 724 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 8,
  "truncated": true,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 1006,
      "name": "GTPase KRas [G12D]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G12D]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 4824,
      "n_compounds": 3250,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 50006227,
      "name": "GTPase KRas",
      "uniprot": "P01116",
      "uniprot_raw": "P01116",
      "organism": "Homo sapiens",
      "type": "PROTEIN",
      "n_activities": 3166,
      "n_compounds": 2657,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 1398,
      "name": "GTPase KRas [G12V]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G12V]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 2912,
      "n_compounds": 2103,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 864,
      "name": "GTPase KRas [G12C]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G12C]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 2610,
      "n_compounds": 2077,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 1396,
      "name": "GTPase KRas [G13C]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G13C]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 1404,
      "n_compounds": 1329,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 1403,
      "name": "GTPase KRas [G13D]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G13D]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 1278,
      "n_compounds": 1236,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 1090,
      "name": "GTPase KRas [1-169,G12C,C118A]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[1-169,G12C,C118A]",
      "organism": "Homo sapiens",
      "type": "PROTEIN",
      "n_activities": 1269,
      "n_compounds": 844,
      "matched_name": "KRAS"
    },
    {
      "target_kind": "polymer",
      "target_id": 1374,
      "name": "GTPase KRas [G12S]",
      "uniprot": "P01116",
      "uniprot_raw": "P01116[G12S]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 791,
      "n_compounds": 724,
      "matched_name": "KRAS"
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
ORDER BY year
```

**Result:**

_6 row(s)._

| year | measurements | compounds | sources | from_patents | from_pubmed_articles | from_pubchem_assays |
|---|---|---|---|---|---|---|
| 2021 | 703 | 379 | 1 | 703 | 0 | 0 |
| 2022 | 621 | 538 | 4 | 621 | 0 | 0 |
| 2023 | 1018 | 841 | 3 | 1018 | 0 | 0 |
| 2024 | 1015 | 639 | 7 | 1015 | 0 | 0 |
| 2025 | 786 | 773 | 5 | 786 | 0 | 0 |
| 2026 | 41 | 41 | 1 | 41 | 0 | 0 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 6,
  "truncated": false,
  "rows": [
    {
      "year": 2021,
      "measurements": 703,
      "compounds": 379,
      "sources": 1,
      "from_patents": 703,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    },
    {
      "year": 2022,
      "measurements": 621,
      "compounds": 538,
      "sources": 4,
      "from_patents": 621,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    },
    {
      "year": 2023,
      "measurements": 1018,
      "compounds": 841,
      "sources": 3,
      "from_patents": 1018,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    },
    {
      "year": 2024,
      "measurements": 1015,
      "compounds": 639,
      "sources": 7,
      "from_patents": 1015,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    },
    {
      "year": 2025,
      "measurements": 786,
      "compounds": 773,
      "sources": 5,
      "from_patents": 786,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    },
    {
      "year": 2026,
      "measurements": 41,
      "compounds": 41,
      "sources": 1,
      "from_patents": 41,
      "from_pubmed_articles": 0,
      "from_pubchem_assays": 0
    }
  ]
}
```

</details>

### 3. `run_sql`

```json
{}
```

```sql
SELECT polymerid, target_name,
       count(*) AS measurements,
       count(*) FILTER (WHERE regexp_matches(source_id, '^[0-9]+$')) AS from_pubmed_articles,
       count(*) FILTER (WHERE regexp_matches(source_id, '^(US|WO|EP)')) AS from_patents,
       min(year) AS first_year,
       max(year) AS last_year
FROM activity
WHERE uniprot = 'P01116' AND uniprot_raw NOT LIKE '%[%'
GROUP BY ALL
```

**Result:**

_1 row(s)._

| polymerid | target_name | measurements | from_pubmed_articles | from_patents | first_year | last_year |
|---|---|---|---|---|---|---|
| 50006227 | GTPase KRas | 3166 | 1304 | 1860 | 2011 | 2025 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 1,
  "truncated": false,
  "rows": [
    {
      "polymerid": 50006227,
      "target_name": "GTPase KRas",
      "measurements": 3166,
      "from_pubmed_articles": 1304,
      "from_patents": 1860,
      "first_year": 2011,
      "last_year": 2025
    }
  ]
}
```

</details>

<!-- results-sha256: d65ed6852b1e7c3e1e0313b3a30367a83d471d41203909321a37156955ad9a8f -->

## Answer

**Records annotated as G12C come only from patents.** Targets whose UniProt annotation contains G12C hold
about 4,180 measurements, all from patents filed 2021–2026: 703 (2021), 621 (2022), 1,018 (2023),
1,015 (2024), 786 (2025), 41 (2026 so far). Each year has 1–7 patents and 380–840 compounds.

**The article data lives elsewhere.** The generic "GTPase KRas" target (50006227, no mutation annotation)
holds 3,166 measurements from 2011–2025: **1,304 from PubMed articles** and 1,860 from patents. Records
derived from ChEMBL don't separate KRAS mutants at the target level, so which mutant was assayed (often
G12C) is recorded only in the assay description.

So the answer to "papers or patents?" depends on curation:
- Records explicitly annotated as G12C are 100% patents. Their volume rose from 2021, peaked in 2023–2024 at about 1,000 measurements a year, and dipped slightly in 2025.
- Published-article data on G12C inhibitors exists, but it sits under the generic KRAS target.
- To count it, filter the assay descriptions, e.g. join `assay` and require `description ILIKE '%G12C%'`.
