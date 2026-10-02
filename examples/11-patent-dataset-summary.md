# Summary of the patent data

> **Question:** Summarize the data for the patent dataset.

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `run_sql`

```json
{}
```

```sql
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
ORDER BY measurements DESC
```

**Result:**

_4 row(s)._

| source_type | measurements | pct_measurements | sources | compounds | targets | first_year | last_year | median_p_affinity |
|---|---|---|---|---|---|---|---|---|
| article (PubMed) | 1747578 | 53.8 | 45554 | 711462 | 10453 | 1965 | 2024 | 6.63 |
| patent | 1360073 | 41.9 | 8998 | 697536 | 3213 | 2005 | 2026 | 7.26 |
| PubChem assay | 102310 | 3.1 | 690 | 47193 | 575 | 2006 | 2016 | 4.96 |
| other / none | 38419 | 1.2 | 24 | 22541 | 811 | 1989 | 2025 | 6.48 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 4,
  "truncated": false,
  "rows": [
    {
      "source_type": "article (PubMed)",
      "measurements": 1747578,
      "pct_measurements": 53.8,
      "sources": 45554,
      "compounds": 711462,
      "targets": 10453,
      "first_year": 1965,
      "last_year": 2024,
      "median_p_affinity": 6.63
    },
    {
      "source_type": "patent",
      "measurements": 1360073,
      "pct_measurements": 41.9,
      "sources": 8998,
      "compounds": 697536,
      "targets": 3213,
      "first_year": 2005,
      "last_year": 2026,
      "median_p_affinity": 7.26
    },
    {
      "source_type": "PubChem assay",
      "measurements": 102310,
      "pct_measurements": 3.1,
      "sources": 690,
      "compounds": 47193,
      "targets": 575,
      "first_year": 2006,
      "last_year": 2016,
      "median_p_affinity": 4.96
    },
    {
      "source_type": "other / none",
      "measurements": 38419,
      "pct_measurements": 1.2,
      "sources": 24,
      "compounds": 22541,
      "targets": 811,
      "first_year": 1989,
      "last_year": 2025,
      "median_p_affinity": 6.48
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
FROM c
```

**Result:**

_1 row(s)._

| patent_compounds | only_in_patents | pct_only_in_patents |
|---|---|---|
| 697536 | 672363 | 96.4 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 1,
  "truncated": false,
  "rows": [
    {
      "patent_compounds": 697536,
      "only_in_patents": 672363,
      "pct_only_in_patents": 96.4
    }
  ]
}
```

</details>

### 3. `run_sql`

```json
{"limit": 50}
```

```sql
SELECT year,
       count(DISTINCT source_id) AS patents,
       count(*) AS measurements,
       count(DISTINCT monomerid) AS compounds,
       count(DISTINCT coalesce(polymerid, -complexid)) AS targets,
       round(count(*) / count(DISTINCT source_id)) AS measurements_per_patent
FROM activity
WHERE regexp_matches(source_id, '^(US|WO|EP)')
GROUP BY year
ORDER BY year
```

**Result:**

_17 row(s)._

| year | patents | measurements | compounds | targets | measurements_per_patent |
|---|---|---|---|---|---|
| 2005 | 1 | 101 | 61 | 1 | 101 |
| 2006 | 1 | 17 | 12 | 1 | 17 |
| 2012 | 1 | 380 | 267 | 2 | 380 |
| 2013 | 234 | 19599 | 13196 | 239 | 84 |
| 2014 | 395 | 39379 | 28114 | 356 | 100 |
| 2015 | 665 | 69068 | 47590 | 614 | 104 |
| 2016 | 663 | 83830 | 51907 | 742 | 126 |
| 2017 | 798 | 140194 | 82399 | 581 | 176 |
| 2018 | 606 | 101234 | 57818 | 499 | 167 |
| 2019 | 774 | 140867 | 83836 | 666 | 182 |
| 2020 | 725 | 125132 | 74380 | 694 | 173 |
| 2021 | 732 | 124089 | 74404 | 694 | 170 |
| 2022 | 644 | 102739 | 67477 | 580 | 160 |
| 2023 | 682 | 116473 | 68629 | 632 | 171 |
| 2024 | 855 | 107578 | 70616 | 775 | 126 |
| 2025 | 940 | 148465 | 91525 | 859 | 158 |
| 2026 | 282 | 40928 | 29640 | 347 | 145 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 17,
  "truncated": false,
  "rows": [
    {
      "year": 2005,
      "patents": 1,
      "measurements": 101,
      "compounds": 61,
      "targets": 1,
      "measurements_per_patent": 101.0
    },
    {
      "year": 2006,
      "patents": 1,
      "measurements": 17,
      "compounds": 12,
      "targets": 1,
      "measurements_per_patent": 17.0
    },
    {
      "year": 2012,
      "patents": 1,
      "measurements": 380,
      "compounds": 267,
      "targets": 2,
      "measurements_per_patent": 380.0
    },
    {
      "year": 2013,
      "patents": 234,
      "measurements": 19599,
      "compounds": 13196,
      "targets": 239,
      "measurements_per_patent": 84.0
    },
    {
      "year": 2014,
      "patents": 395,
      "measurements": 39379,
      "compounds": 28114,
      "targets": 356,
      "measurements_per_patent": 100.0
    },
    {
      "year": 2015,
      "patents": 665,
      "measurements": 69068,
      "compounds": 47590,
      "targets": 614,
      "measurements_per_patent": 104.0
    },
    {
      "year": 2016,
      "patents": 663,
      "measurements": 83830,
      "compounds": 51907,
      "targets": 742,
      "measurements_per_patent": 126.0
    },
    {
      "year": 2017,
      "patents": 798,
      "measurements": 140194,
      "compounds": 82399,
      "targets": 581,
      "measurements_per_patent": 176.0
    },
    {
      "year": 2018,
      "patents": 606,
      "measurements": 101234,
      "compounds": 57818,
      "targets": 499,
      "measurements_per_patent": 167.0
    },
    {
      "year": 2019,
      "patents": 774,
      "measurements": 140867,
      "compounds": 83836,
      "targets": 666,
      "measurements_per_patent": 182.0
    },
    {
      "year": 2020,
      "patents": 725,
      "measurements": 125132,
      "compounds": 74380,
      "targets": 694,
      "measurements_per_patent": 173.0
    },
    {
      "year": 2021,
      "patents": 732,
      "measurements": 124089,
      "compounds": 74404,
      "targets": 694,
      "measurements_per_patent": 170.0
    },
    {
      "year": 2022,
      "patents": 644,
      "measurements": 102739,
      "compounds": 67477,
      "targets": 580,
      "measurements_per_patent": 160.0
    },
    {
      "year": 2023,
      "patents": 682,
      "measurements": 116473,
      "compounds": 68629,
      "targets": 632,
      "measurements_per_patent": 171.0
    },
    {
      "year": 2024,
      "patents": 855,
      "measurements": 107578,
      "compounds": 70616,
      "targets": 775,
      "measurements_per_patent": 126.0
    },
    {
      "year": 2025,
      "patents": 940,
      "measurements": 148465,
      "compounds": 91525,
      "targets": 859,
      "measurements_per_patent": 158.0
    },
    {
      "year": 2026,
      "patents": 282,
      "measurements": 40928,
      "compounds": 29640,
      "targets": 347,
      "measurements_per_patent": 145.0
    }
  ]
}
```

</details>

### 4. `run_sql`

```json
{}
```

```sql
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
ORDER BY measurements DESC
```

**Result:**

_6 row(s)._

| affinity_type | measurements | pct | pct_exact | pct_less_than | pct_greater_than | median_exact_value |
|---|---|---|---|---|---|---|
| IC50 | 1078416 | 79.3 | 74.8 | 16.6 | 8.6 | 65 |
| Ki | 157850 | 11.6 | 84.1 | 9.7 | 6.2 | 25 |
| EC50 | 88873 | 6.5 | 77.5 | 10.4 | 12.1 | 69 |
| Kd | 34454 | 2.5 | 63.7 | 24.1 | 12.2 | 18.5 |
| kon | 240 | 0 | 100 | 0 | 0 | 1.8e+06 |
| koff | 240 | 0 | 100 | 0 | 0 | 0.0001 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 6,
  "truncated": false,
  "rows": [
    {
      "affinity_type": "IC50",
      "measurements": 1078416,
      "pct": 79.3,
      "pct_exact": 74.8,
      "pct_less_than": 16.6,
      "pct_greater_than": 8.6,
      "median_exact_value": 65.0
    },
    {
      "affinity_type": "Ki",
      "measurements": 157850,
      "pct": 11.6,
      "pct_exact": 84.1,
      "pct_less_than": 9.7,
      "pct_greater_than": 6.2,
      "median_exact_value": 25.0
    },
    {
      "affinity_type": "EC50",
      "measurements": 88873,
      "pct": 6.5,
      "pct_exact": 77.5,
      "pct_less_than": 10.4,
      "pct_greater_than": 12.1,
      "median_exact_value": 69.0
    },
    {
      "affinity_type": "Kd",
      "measurements": 34454,
      "pct": 2.5,
      "pct_exact": 63.7,
      "pct_less_than": 24.1,
      "pct_greater_than": 12.2,
      "median_exact_value": 18.5
    },
    {
      "affinity_type": "kon",
      "measurements": 240,
      "pct": 0.0,
      "pct_exact": 100.0,
      "pct_less_than": 0.0,
      "pct_greater_than": 0.0,
      "median_exact_value": 1800000.0
    },
    {
      "affinity_type": "koff",
      "measurements": 240,
      "pct": 0.0,
      "pct_exact": 100.0,
      "pct_less_than": 0.0,
      "pct_greater_than": 0.0,
      "median_exact_value": 0.0001
    }
  ]
}
```

</details>

### 5. `run_sql`

```json
{}
```

```sql
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
LIMIT 15
```

**Result:**

_15 row(s)._

| polymerid | complexid | target_name | patents | patent_measurements | patent_compounds | pct_of_target_data_from_patents |
|---|---|---|---|---|---|---|
| 1846 |  | Tyrosine-protein kinase BTK | 216 | 19112 | 11849 | 82.7 |
| 4918 |  | Tyrosine-protein kinase JAK2 | 196 | 16016 | 12844 | 76.6 |
| 4917 |  | Tyrosine-protein kinase JAK1 | 183 | 13299 | 11412 | 80.7 |
| 50004052 |  | Mitogen-activated protein kinase kinase kinase kinase 1 | 65 | 13023 | 8940 | 91.2 |
| 5405 |  | Interleukin-1 receptor-associated kinase 4 | 93 | 12978 | 10856 | 87.3 |
| 2109 |  | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit de... | 123 | 12485 | 8398 | 74.4 |
| 5447 |  | Orexin receptor type 2 | 80 | 11252 | 7023 | 87 |
| 6987 |  | P2X purinoceptor 7 | 34 | 10223 | 3826 | 83.7 |
| 738 |  | Nuclear receptor ROR-gamma | 74 | 10116 | 7061 | 68.7 |
| 6835 |  | Sodium channel protein type 9 subunit alpha | 77 | 10012 | 7511 | 73.8 |
| 4919 |  | Tyrosine-protein kinase JAK3 | 161 | 9897 | 7079 | 74.3 |
| 336 |  | Plasma kallikrein | 70 | 9736 | 5044 | 90.9 |
| 5448 |  | Orexin/Hypocretin receptor type 1 | 66 | 9001 | 5804 | 84.5 |
| 1622 |  | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit al... | 73 | 8995 | 8062 | 56.7 |
| 5309 |  | Lysine-specific histone demethylase 1A | 90 | 8756 | 4452 | 75.6 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 15,
  "truncated": false,
  "rows": [
    {
      "polymerid": 1846,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase BTK",
      "patents": 216,
      "patent_measurements": 19112,
      "patent_compounds": 11849,
      "pct_of_target_data_from_patents": 82.7
    },
    {
      "polymerid": 4918,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase JAK2",
      "patents": 196,
      "patent_measurements": 16016,
      "patent_compounds": 12844,
      "pct_of_target_data_from_patents": 76.6
    },
    {
      "polymerid": 4917,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase JAK1",
      "patents": 183,
      "patent_measurements": 13299,
      "patent_compounds": 11412,
      "pct_of_target_data_from_patents": 80.7
    },
    {
      "polymerid": 50004052,
      "complexid": null,
      "target_name": "Mitogen-activated protein kinase kinase kinase kinase 1",
      "patents": 65,
      "patent_measurements": 13023,
      "patent_compounds": 8940,
      "pct_of_target_data_from_patents": 91.2
    },
    {
      "polymerid": 5405,
      "complexid": null,
      "target_name": "Interleukin-1 receptor-associated kinase 4",
      "patents": 93,
      "patent_measurements": 12978,
      "patent_compounds": 10856,
      "pct_of_target_data_from_patents": 87.3
    },
    {
      "polymerid": 2109,
      "complexid": null,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit delta isoform",
      "patents": 123,
      "patent_measurements": 12485,
      "patent_compounds": 8398,
      "pct_of_target_data_from_patents": 74.4
    },
    {
      "polymerid": 5447,
      "complexid": null,
      "target_name": "Orexin receptor type 2",
      "patents": 80,
      "patent_measurements": 11252,
      "patent_compounds": 7023,
      "pct_of_target_data_from_patents": 87.0
    },
    {
      "polymerid": 6987,
      "complexid": null,
      "target_name": "P2X purinoceptor 7",
      "patents": 34,
      "patent_measurements": 10223,
      "patent_compounds": 3826,
      "pct_of_target_data_from_patents": 83.7
    },
    {
      "polymerid": 738,
      "complexid": null,
      "target_name": "Nuclear receptor ROR-gamma",
      "patents": 74,
      "patent_measurements": 10116,
      "patent_compounds": 7061,
      "pct_of_target_data_from_patents": 68.7
    },
    {
      "polymerid": 6835,
      "complexid": null,
      "target_name": "Sodium channel protein type 9 subunit alpha",
      "patents": 77,
      "patent_measurements": 10012,
      "patent_compounds": 7511,
      "pct_of_target_data_from_patents": 73.8
    },
    {
      "polymerid": 4919,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase JAK3",
      "patents": 161,
      "patent_measurements": 9897,
      "patent_compounds": 7079,
      "pct_of_target_data_from_patents": 74.3
    },
    {
      "polymerid": 336,
      "complexid": null,
      "target_name": "Plasma kallikrein",
      "patents": 70,
      "patent_measurements": 9736,
      "patent_compounds": 5044,
      "pct_of_target_data_from_patents": 90.9
    },
    {
      "polymerid": 5448,
      "complexid": null,
      "target_name": "Orexin/Hypocretin receptor type 1",
      "patents": 66,
      "patent_measurements": 9001,
      "patent_compounds": 5804,
      "pct_of_target_data_from_patents": 84.5
    },
    {
      "polymerid": 1622,
      "complexid": null,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit alpha isoform",
      "patents": 73,
      "patent_measurements": 8995,
      "patent_compounds": 8062,
      "pct_of_target_data_from_patents": 56.7
    },
    {
      "polymerid": 5309,
      "complexid": null,
      "target_name": "Lysine-specific histone demethylase 1A",
      "patents": 90,
      "patent_measurements": 8756,
      "patent_compounds": 4452,
      "pct_of_target_data_from_patents": 75.6
    }
  ]
}
```

</details>

<!-- results-sha256: 02fd00feb667ced2031dac5ff45c078fc3476e26332e21a9fda55a460f07f9b0 -->

## Answer

"Patent data" here means measurements whose `source_id` is a patent number (starting `US`, `WO` or `EP`).

**Size.** Patents supply **1.36 million measurements (41.9% of BindingDB)** from 8,998 patents, covering
697,536 compounds and 3,213 targets. Articles are larger by measurements (1.75 M, 53.8%) but have about
the same number of compounds (711k) spread over three times as many targets (10,453). PubChem assays and
other sources add the remaining 4%.

**Patent compounds are almost all unique to patents.** 672,363 of the 697,536 patent compounds (96.4%)
have no measurement from any other source. If you leave patents out, you lose nearly half the compounds
in BindingDB.

**Timeline.** Before 2013 there are only 3 patents (2005, 2006, 2012). Curation starts in earnest in
2013 (234 patents) and settles at 600–950 patents and 100k–150k measurements a year from 2017 on; 2025
is the largest year (940 patents, 148k measurements). 2026 (282 patents) covers only part of the year.
A typical patent contributes 150–180 measurements.

**Measurement types.** IC50 dominates (79.3%), then Ki (11.6%), EC50 (6.5%) and Kd (2.5%). There are
only 240 kon/koff pairs. Censored values are common: 16.6% of IC50s are reported as `<` and 8.6% as `>`
(for Kd, 24.1% are `<`), because patents often report potency as a threshold or bin rather than an
exact number. Medians of the exact values are 65 nM (IC50), 25 nM (Ki), 69 nM (EC50) and 18.5 nM (Kd).

**Potency.** The median exact p_affinity is 7.26 for patents vs 6.63 for articles, about 4× more
potent. This is likely because patents mostly report optimized compounds in a lead series, while articles also include weaker
analogues and screening hits. PubChem assays (median 4.96) are mostly screening data.

**Targets.** The top patent targets are drug-discovery kinases and receptors: BTK (216 patents, 19,112
measurements), JAK2, JAK1, HPK1 (MAP4K1), IRAK4, PI3Kδ, orexin OX2, P2X7, RORγ and Nav1.7. For these
targets **57–91% of all data comes from patents** (HPK1 91.2%, plasma kallikrein 90.9%). Any analysis
of them that leaves out patents misses most of the data.

Caveats:
- `year` for a patent is its publication year, not the year the compounds were made, so patent data lags articles.
- The medians above use only exact (`=`) values, so they leave out about a quarter of the patent IC50s.
