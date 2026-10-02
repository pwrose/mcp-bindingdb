# Selectivity for EGFR T790M/L858R over wild type

> **Question:** Which compounds are most selective for the drug-resistant EGFR T790M/L858R double mutant over wild-type EGFR, based on IC50?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "P00533", "limit": 5}
```

**Result:**

_5 row(s), more available (truncated by limit) — table shows selected columns._

| target_id | name | uniprot_raw | n_activities | n_compounds |
|---|---|---|---|---|
| 520 | Epidermal growth factor receptor | P00533 | 23266 | 14126 |
| 60 | Epidermal growth factor receptor [T790M,L858R] | P00533[T790M,L858R] | 1536 | 1276 |
| 1058 | Epidermal growth factor receptor [L858R,T790M,C797S] | P00533[L858R,T790M,C797S] | 690 | 666 |
| 1214 | Epidermal growth factor receptor [L858R,C797S] | P00533[L858R,C797S] | 684 | 683 |
| 51 | Epidermal growth factor receptor [L858R] | P00533[L858R] | 678 | 646 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 5,
  "truncated": true,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 520,
      "name": "Epidermal growth factor receptor",
      "uniprot": "P00533",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "type": "Receptor Kinase Domain",
      "n_activities": 23266,
      "n_compounds": 14126
    },
    {
      "target_kind": "polymer",
      "target_id": 60,
      "name": "Epidermal growth factor receptor [T790M,L858R]",
      "uniprot": "P00533",
      "uniprot_raw": "P00533[T790M,L858R]",
      "organism": "Homo sapiens",
      "type": "",
      "n_activities": 1536,
      "n_compounds": 1276
    },
    {
      "target_kind": "polymer",
      "target_id": 1058,
      "name": "Epidermal growth factor receptor [L858R,T790M,C797S]",
      "uniprot": "P00533",
      "uniprot_raw": "P00533[L858R,T790M,C797S]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 690,
      "n_compounds": 666
    },
    {
      "target_kind": "polymer",
      "target_id": 1214,
      "name": "Epidermal growth factor receptor [L858R,C797S]",
      "uniprot": "P00533",
      "uniprot_raw": "P00533[L858R,C797S]",
      "organism": "Homo sapiens",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 684,
      "n_compounds": 683
    },
    {
      "target_kind": "polymer",
      "target_id": 51,
      "name": "Epidermal growth factor receptor [L858R]",
      "uniprot": "P00533",
      "uniprot_raw": "P00533[L858R]",
      "organism": "Homo sapiens",
      "type": "",
      "n_activities": 678,
      "n_compounds": 646
    }
  ]
}
```

</details>

### 2. `run_sql`

```json
{"limit": 15}
```

```sql
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
LIMIT 15
```

**Result:**

_15 row(s)._

| monomerid | name | ic50_mutant_nm | ic50_wildtype_nm | fold_selectivity |
|---|---|---|---|---|
| 391742 | N-(3-((2-((2-methoxy-4-(1-(methylsulfonyl)piperidin-4-yl)phenyl)ami... | 9.8 | 871000 | 88877.6 |
| 391743 | N-(3-((2-((2-methoxy-4-(4-morpholinopiperidin-1-yl)phenyl)amino)-5-... | 1.5 | 73000 | 48666.7 |
| 536968 | US11896597, Compound 84 | 0.4 | 604 | 1510 |
| 789986 | (10S,17E)-8,10,12,16-tetramethyl-15-[2- (pyrrolidin-1-yl)ethyl]-2,1... | 0.06 | 64 | 1066.7 |
| 717530 | US20250034165, Example 79 | 0.007 | 6.2 | 885.7 |
| 790084 | 2-{(11S,17E)-12-cyclopropyl-8,11- dimethyl-16-[(propan-2-yl)oxy]- 2... | 0.42 | 296 | 704.8 |
| 717537 | US20250034165, Example 88 | 0.01 | 6 | 600 |
| 536977 | US11896597, Compound 92 | 1.7 | 765 | 450 |
| 790021 | (2R)-1-[(10S,17E)-8,10,12,16- tetramethyl-2,8,10,11,12,13-hexahydro... | 0.77 | 264 | 342.9 |
| 536959 | US11896597, Compound 87 | 1.4 | 479 | 342.1 |
| 536957 | US11896597, Compound 74 | 0.4 | 133 | 332.5 |
| 536970 | US11896597, Compound 86 | 0.6 | 195 | 325 |
| 717536 | US20250034165, Example 87 | 0.042 | 13 | 309.5 |
| 790066 | (10S,17E)-16-ethoxy-8,10,12-trimethyl- 2,8,10,11,12,13-hexahydro-3,... | 0.65 | 195 | 300 |
| 790097 | (2S)-1-{(10R,17E)-12-ethyl-8,10- dimethyl-16-[(propan-2-yl)oxy]- 2,... | 0.84 | 251 | 298.8 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 15,
  "truncated": false,
  "rows": [
    {
      "monomerid": 391742,
      "name": "N-(3-((2-((2-methoxy-4-(1-(methylsulfonyl)piperidin-4-yl)phenyl)amino)-5-(trifluoromethyl)pyrimidin-4-yl)amino)phenyl)acrylamide",
      "ic50_mutant_nm": 9.8,
      "ic50_wildtype_nm": 871000.0,
      "fold_selectivity": 88877.6
    },
    {
      "monomerid": 391743,
      "name": "N-(3-((2-((2-methoxy-4-(4-morpholinopiperidin-1-yl)phenyl)amino)-5-(trifluoromethyl)pyrimidin-4-yl)amino)phenyl)acrylamide",
      "ic50_mutant_nm": 1.5,
      "ic50_wildtype_nm": 73000.0,
      "fold_selectivity": 48666.7
    },
    {
      "monomerid": 536968,
      "name": "US11896597, Compound 84",
      "ic50_mutant_nm": 0.4,
      "ic50_wildtype_nm": 604.0,
      "fold_selectivity": 1510.0
    },
    {
      "monomerid": 789986,
      "name": "(10S,17E)-8,10,12,16-tetramethyl-15-[2- (pyrrolidin-1-yl)ethyl]-2,10,11,12,13,15- hexahydro-8H-3,5-ethenotripyrazolo[3,4- f:3',4'-j:4$#8243;,3$#8243;- n][1,4]oxazacyclopentadecine",
      "ic50_mutant_nm": 0.06,
      "ic50_wildtype_nm": 64.0,
      "fold_selectivity": 1066.7
    },
    {
      "monomerid": 717530,
      "name": "US20250034165, Example 79",
      "ic50_mutant_nm": 0.007,
      "ic50_wildtype_nm": 6.2,
      "fold_selectivity": 885.7
    },
    {
      "monomerid": 790084,
      "name": "2-{(11S,17E)-12-cyclopropyl-8,11- dimethyl-16-[(propan-2-yl)oxy]- 2,8,10,11,12,13-hexahydro-14H-3,5- ethenotripyrazolo[3,4-f:3',4'-j:4$#8243;,3$#8243;- n][1,4]oxazacyclopentadecin-14- yl}ethan-1-ol",
      "ic50_mutant_nm": 0.42,
      "ic50_wildtype_nm": 296.0,
      "fold_selectivity": 704.8
    },
    {
      "monomerid": 717537,
      "name": "US20250034165, Example 88",
      "ic50_mutant_nm": 0.01,
      "ic50_wildtype_nm": 6.0,
      "fold_selectivity": 600.0
    },
    {
      "monomerid": 536977,
      "name": "US11896597, Compound 92",
      "ic50_mutant_nm": 1.7,
      "ic50_wildtype_nm": 765.0,
      "fold_selectivity": 450.0
    },
    {
      "monomerid": 790021,
      "name": "(2R)-1-[(10S,17E)-8,10,12,16- tetramethyl-2,8,10,11,12,13-hexahydro- 15H-3,5-ethenotripyrazolo[3,4-f:3',4'- j:4$#8243;,3$#8243;-n][1,4]oxazacyclopentadecin-15- yl]propan-2-ol",
      "ic50_mutant_nm": 0.77,
      "ic50_wildtype_nm": 264.0,
      "fold_selectivity": 342.9
    },
    {
      "monomerid": 536959,
      "name": "US11896597, Compound 87",
      "ic50_mutant_nm": 1.4,
      "ic50_wildtype_nm": 479.0,
      "fold_selectivity": 342.1
    },
    {
      "monomerid": 536957,
      "name": "US11896597, Compound 74",
      "ic50_mutant_nm": 0.4,
      "ic50_wildtype_nm": 133.0,
      "fold_selectivity": 332.5
    },
    {
      "monomerid": 536970,
      "name": "US11896597, Compound 86",
      "ic50_mutant_nm": 0.6,
      "ic50_wildtype_nm": 195.0,
      "fold_selectivity": 325.0
    },
    {
      "monomerid": 717536,
      "name": "US20250034165, Example 87",
      "ic50_mutant_nm": 0.042,
      "ic50_wildtype_nm": 13.0,
      "fold_selectivity": 309.5
    },
    {
      "monomerid": 790066,
      "name": "(10S,17E)-16-ethoxy-8,10,12-trimethyl- 2,8,10,11,12,13-hexahydro-3,5- etheno[1,2]oxazolo[5,4-f]dipyrazolo[3,4- j:4',3'-n][1,4]oxazacyclopentadecine",
      "ic50_mutant_nm": 0.65,
      "ic50_wildtype_nm": 195.0,
      "fold_selectivity": 300.0
    },
    {
      "monomerid": 790097,
      "name": "(2S)-1-{(10R,17E)-12-ethyl-8,10- dimethyl-16-[(propan-2-yl)oxy]- 2,8,10,11,12,13-hexahydro-14H-3,5- ethenotripyrazolo[3,4-f:3',4'-j:4$#8243;,3$#8243;- n][1,4]oxazacyclopentadecin-14- yl}propan-2-ol",
      "ic50_mutant_nm": 0.84,
      "ic50_wildtype_nm": 251.0,
      "fold_selectivity": 298.8
    }
  ]
}
```

</details>

<!-- results-sha256: 94964422072ea269740a534f988da5393de70427970f1aa633aeb7593e88c303 -->

## Answer

This compares wild-type EGFR (target 520) with the T790M/L858R double mutant (target 60). It uses the
median IC50 for each compound on each target, and keeps compounds with a mutant IC50 of 10 nM or less.

- **The top two rows look unreliable.** They claim 48,000–89,000-fold selectivity (BDBM391742, BDBM391743), but their wild-type IC50s of 73 µM and 871 µM are far outside a normal assay range. They are most likely extrapolated or mis-recorded values.
- **The most credible selective compounds are 300 to 1,500-fold selective:**
  - US11896597 Compound 84: 0.4 nM on the mutant vs 604 nM on wild type, about 1,500-fold.
  - The macrocycle BDBM789986: 0.06 nM vs 64 nM, about 1,070-fold.
  - US20250034165 Example 79: 0.007 nM vs 6.2 nM, about 890-fold.
  - Further members of the same series, from US11896597, US20250034165 and the macrocycle set.

**Caveat:** the medians can come from different assays and sources. For a stricter matched comparison,
add `AND wt.entryid = mut.entryid` (same paper or patent) to the query. That needs `entryid` carried
through the `ic50` CTE.
