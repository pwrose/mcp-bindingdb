# hERG potency distribution

> **Question:** How are hERG IC50 values distributed across compounds in BindingDB, and what fraction of tested compounds are potent blockers (IC50 below 1 µM)?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "hERG", "limit": 3}
```

**Result:**

_3 row(s) — table shows selected columns._

| target_id | name | uniprot_raw | organism | n_activities | n_compounds |
|---|---|---|---|---|---|
| 2132 | Potassium voltage-gated channel subfamily H member 2 | Q12809 | Homo sapiens | 18767 | 14872 |
| 49000648 | Potassium voltage-gated channel subfamily H member 2 |  | Bos taurus | 1 | 1 |
| 50001229 | Potassium voltage-gated channel subfamily H member 6 | Q9H252 | Homo sapiens | 1 | 1 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 3,
  "truncated": false,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 2132,
      "name": "Potassium voltage-gated channel subfamily H member 2",
      "uniprot": "Q12809",
      "uniprot_raw": "Q12809",
      "organism": "Homo sapiens",
      "type": "Multi-pass membrane protein",
      "n_activities": 18767,
      "n_compounds": 14872,
      "matched_name": "HERG"
    },
    {
      "target_kind": "polymer",
      "target_id": 49000648,
      "name": "Potassium voltage-gated channel subfamily H member 2",
      "uniprot": null,
      "uniprot_raw": null,
      "organism": "Bos taurus",
      "type": "Enzyme Catalytic Domain",
      "n_activities": 1,
      "n_compounds": 1,
      "matched_name": "HERG"
    },
    {
      "target_kind": "polymer",
      "target_id": 50001229,
      "name": "Potassium voltage-gated channel subfamily H member 6",
      "uniprot": "Q9H252",
      "uniprot_raw": "Q9H252",
      "organism": "Homo sapiens",
      "type": "PROTEIN",
      "n_activities": 1,
      "n_compounds": 1,
      "matched_name": "hERG2"
    }
  ]
}
```

</details>

### 2. `get_target`

```json
{"target_id": 2132}
```

**Result:**

**target**

| field | value |
|---|---|
| target_kind | polymer |
| target_id | 2132 |
| name | Potassium voltage-gated channel subfamily H member 2 |
| uniprot | Q12809 |
| uniprot_raw | Q12809 |
| organism | Homo sapiens |
| taxid | 9606 |
| type | Multi-pass membrane protein |
| res_count | 1159 |
| n_pdb_ids | 24 |
| chembl_id | CHEMBL240 |
| n_activities | 18767 |
| n_compounds | 14872 |
| unpid2 | A0A090N8Q0 |
| common_name | HUMAN |
| topology | null |
| weight | 126672.65 |
| pdb_ids | 8IOB,8IO5,8IO4,5VA2,8ZYQ,8ZYP,8ZYO,8ZYN,7CN1,7CN0,5VA1,9CHS,9CHR,9C... |

**synonyms:** ERG, ERG1, HERG, H-ERG, KCNH2, KCNH2_HUMAN, eag homolog, Cytochrome P450 3A4, Eag-related protein 1, hERG Potassium Channel 1, Transcriptional regulator ERG, Ether-a-go-go-related protein 1, Ether-a-go-go-related gene (HERG), putative potassium channel subunit, Ether-a-go-go-related protein (hERG), Ether-a-go-go-related protein 1 (HERG), 1,3-beta-glucan synthase component GLS2, Ether-a-go-go-related gene potassium channel 1, Voltage-gated potassium channel subunit Kv11.1, Ether a-go-go related gene potassium channel (hERG), Ether-a-go-go-related gene potassium channel (hERG), Potassium voltage-gated channel subfamily H member 2, Ether-a-go-go-related gene potassium channel 1 (HERG), Ether-a-go-go-related gene potassium channel 1 (hERG1), Potassium voltage-gated channel subfamily H member 2 (hERG)

**measurements_by_type**

| affinity_type | n_measurements | n_compounds | best_p_affinity |
|---|---|---|---|
| IC50 | 15761 | 12892 | 10.68 |
| Ki | 2847 | 2102 | 9.55 |
| EC50 | 110 | 108 | 8.72 |
| Kd | 49 | 49 | 9.36 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "target": {
    "target_kind": "polymer",
    "target_id": 2132,
    "name": "Potassium voltage-gated channel subfamily H member 2",
    "uniprot": "Q12809",
    "uniprot_raw": "Q12809",
    "organism": "Homo sapiens",
    "taxid": "9606",
    "type": "Multi-pass membrane protein",
    "res_count": 1159,
    "n_pdb_ids": 24,
    "chembl_id": "CHEMBL240",
    "n_activities": 18767,
    "n_compounds": 14872,
    "unpid2": "A0A090N8Q0",
    "common_name": "HUMAN",
    "topology": "null",
    "weight": "126672.65",
    "pdb_ids": "8IOB,8IO5,8IO4,5VA2,8ZYQ,8ZYP,8ZYO,8ZYN,7CN1,7CN0,5VA1,9CHS,9CHR,9CHQ,9CHP,5VA3,2L1M,2L4R,4HQA,2L0W,4HP9,6SYG,2N7G,1BYW"
  },
  "synonyms": [
    "ERG",
    "ERG1",
    "HERG",
    "H-ERG",
    "KCNH2",
    "KCNH2_HUMAN",
    "eag homolog",
    "Cytochrome P450 3A4",
    "Eag-related protein 1",
    "hERG Potassium Channel 1",
    "Transcriptional regulator ERG",
    "Ether-a-go-go-related protein 1",
    "Ether-a-go-go-related gene (HERG)",
    "putative potassium channel subunit",
    "Ether-a-go-go-related protein (hERG)",
    "Ether-a-go-go-related protein 1 (HERG)",
    "1,3-beta-glucan synthase component GLS2",
    "Ether-a-go-go-related gene potassium channel 1",
    "Voltage-gated potassium channel subunit Kv11.1",
    "Ether a-go-go related gene potassium channel (hERG)",
    "Ether-a-go-go-related gene potassium channel (hERG)",
    "Potassium voltage-gated channel subfamily H member 2",
    "Ether-a-go-go-related gene potassium channel 1 (HERG)",
    "Ether-a-go-go-related gene potassium channel 1 (hERG1)",
    "Potassium voltage-gated channel subfamily H member 2 (hERG)"
  ],
  "measurements_by_type": [
    {
      "affinity_type": "IC50",
      "n_measurements": 15761,
      "n_compounds": 12892,
      "best_p_affinity": 10.68
    },
    {
      "affinity_type": "Ki",
      "n_measurements": 2847,
      "n_compounds": 2102,
      "best_p_affinity": 9.55
    },
    {
      "affinity_type": "EC50",
      "n_measurements": 110,
      "n_compounds": 108,
      "best_p_affinity": 8.72
    },
    {
      "affinity_type": "Kd",
      "n_measurements": 49,
      "n_compounds": 49,
      "best_p_affinity": 9.36
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
ORDER BY potency_bin
```

**Result:**

_6 row(s)._

| potency_bin | n_compounds | pct_compounds | n_potent_below_1uM |
|---|---|---|---|
| only censored values (<, >) | 3813 | 29.6 | 20 |
| pIC50 5-6   (1-10 µM) | 4293 | 33.3 | 80 |
| pIC50 6-7   (100 nM-1 µM) | 1304 | 10.1 | 1213 |
| pIC50 7-8   (10-100 nM) | 356 | 2.8 | 356 |
| pIC50 < 5   (> 10 µM) | 2906 | 22.5 | 9 |
| pIC50 >= 8  (< 10 nM) | 220 | 1.7 | 220 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 6,
  "truncated": false,
  "rows": [
    {
      "potency_bin": "only censored values (<, >)",
      "n_compounds": 3813,
      "pct_compounds": 29.6,
      "n_potent_below_1uM": 20
    },
    {
      "potency_bin": "pIC50 5-6   (1-10 µM)",
      "n_compounds": 4293,
      "pct_compounds": 33.3,
      "n_potent_below_1uM": 80
    },
    {
      "potency_bin": "pIC50 6-7   (100 nM-1 µM)",
      "n_compounds": 1304,
      "pct_compounds": 10.1,
      "n_potent_below_1uM": 1213
    },
    {
      "potency_bin": "pIC50 7-8   (10-100 nM)",
      "n_compounds": 356,
      "pct_compounds": 2.8,
      "n_potent_below_1uM": 356
    },
    {
      "potency_bin": "pIC50 < 5   (> 10 µM)",
      "n_compounds": 2906,
      "pct_compounds": 22.5,
      "n_potent_below_1uM": 9
    },
    {
      "potency_bin": "pIC50 >= 8  (< 10 nM)",
      "n_compounds": 220,
      "pct_compounds": 1.7,
      "n_potent_below_1uM": 220
    }
  ]
}
```

</details>

<!-- results-sha256: 995ac51e59e7665a6d01b5aa29d1a9e888f6609cc227c5a75793737cd418ac8d -->

## Answer

hERG (KCNH2) is target **2132** (UniProt Q12809), with 18,767 measurements. 12,892 compounds have at
least one hERG IC50.

The table below groups compounds by their median pIC50, using only exact (`=`) values. The SQL result
sorts the bins alphabetically; they are reordered here.

| Median IC50 | Compounds | Share |
|---|---:|---:|
| > 10 µM (pIC50 < 5) | 2,906 | 22.5% |
| 1–10 µM | 4,293 | 33.3% |
| 100 nM–1 µM | 1,304 | 10.1% |
| 10–100 nM | 356 | 2.8% |
| < 10 nM | 220 | 1.7% |
| Only censored values (e.g. `>30 µM`) | 3,813 | 29.6% |

**About 15% of tested compounds are potent hERG blockers:**
- 1,898 of 12,892 compounds (14.7%) have at least one IC50 below 1 µM.
- 1,880 (14.6%) have a median IC50 below 1 µM.

Most of the censored-only compounds were inactive at the top concentration tested. The real fraction of
potent blockers is probably lower than 15%, because published data favours interesting (active) compounds.

**Data-quality note:** BindingDB's synonym list for this target includes wrong names such as
"Cytochrome P450 3A4", "Transcriptional regulator ERG" and "1,3-beta-glucan synthase component GLS2". A
search by name can therefore hit hERG by mistake; UniProt accessions are more reliable.
