# Longest drug-target residence times

> **Question:** Which compound-target pairs have the longest residence time (1/koff) in BindingDB?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `describe_tables`

```json
{"table": "activity"}
```

**Result:**

**table:** activity

**description:** Derived. One row per measured value with parsed numeric value, unit...

**columns**

| column_name | data_type | is_nullable |
|---|---|---|
| ki_result_id | INTEGER | YES |
| reactant_set_id | INTEGER | YES |
| entryid | INTEGER | YES |
| affinity_type | VARCHAR | YES |
| relation | VARCHAR | YES |
| value | DOUBLE | YES |
| unit | VARCHAR | YES |
| p_affinity | DOUBLE | YES |
| raw_value | VARCHAR | YES |
| uncertainty | VARCHAR | YES |
| monomerid | INTEGER | YES |
| compound_name | VARCHAR | YES |
| inchi_key | VARCHAR | YES |
| polymerid | INTEGER | YES |
| complexid | INTEGER | YES |
| target_name | VARCHAR | YES |
| uniprot | VARCHAR | YES |
| uniprot_raw | VARCHAR | YES |
| organism | VARCHAR | YES |
| taxid | VARCHAR | YES |
| ph | DECIMAL(10,4) | YES |
| temp_k | DECIMAL(10,4) | YES |
| assay_name | VARCHAR | YES |
| articleid | INTEGER | YES |
| source_id | VARCHAR | YES |
| doi | VARCHAR | YES |
| year | SMALLINT | YES |

**sample_rows**

| ki_result_id | reactant_set_id | entryid | affinity_type | relation | value | unit | p_affinity | raw_value | uncertainty | monomerid | compound_name | inchi_key | polymerid | complexid | target_name | uniprot | uniprot_raw | organism | taxid | ph | temp_k | assay_name | articleid | source_id | doi | year |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 856816 | 854546 | 8856 | EC50 | = | 2.5 | nM | 8.6 | 2.50 |  | 423528 | US10508115, Compound If-04 | LVYHWHWKFVCUMH-UHFFFAOYSA-N | 12 |  | Interleukin-6 | P05231 | P05231 | Homo sapiens | 9606 |  |  | Interleukin 6 Induction Assay | 8837 | US10508115B2 |  | 2019 |
| 856746 | 854476 | 8856 | EC50 | = | 3.77 | nM | 8.42 | 3.77 |  | 423493 | US10508115, Compound Ib-12 | RFJDLSDFKISQEE-UHFFFAOYSA-N | 12 |  | Interleukin-6 | P05231 | P05231 | Homo sapiens | 9606 |  |  | Interleukin 6 Induction Assay | 8837 | US10508115B2 |  | 2019 |
| 856820 | 854550 | 8856 | EC50 | = | 3.8 | nM | 8.42 | 3.80 |  | 423530 | US10508115, Compound If-06 | ZLEXSMIIQCQXKU-UHFFFAOYSA-N | 12 |  | Interleukin-6 | P05231 | P05231 | Homo sapiens | 9606 |  |  | Interleukin 6 Induction Assay | 8837 | US10508115B2 |  | 2019 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "table": "activity",
  "description": "Derived. One row per measured value with parsed numeric value, unit, relation, p_affinity, and denormalized compound, target, assay and citation columns. Start here.",
  "columns": [
    {
      "column_name": "ki_result_id",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "reactant_set_id",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "entryid",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "affinity_type",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "relation",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "value",
      "data_type": "DOUBLE",
      "is_nullable": "YES"
    },
    {
      "column_name": "unit",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "p_affinity",
      "data_type": "DOUBLE",
      "is_nullable": "YES"
    },
    {
      "column_name": "raw_value",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "uncertainty",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "monomerid",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "compound_name",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "inchi_key",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "polymerid",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "complexid",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "target_name",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "uniprot",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "uniprot_raw",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "organism",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "taxid",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "ph",
      "data_type": "DECIMAL(10,4)",
      "is_nullable": "YES"
    },
    {
      "column_name": "temp_k",
      "data_type": "DECIMAL(10,4)",
      "is_nullable": "YES"
    },
    {
      "column_name": "assay_name",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "articleid",
      "data_type": "INTEGER",
      "is_nullable": "YES"
    },
    {
      "column_name": "source_id",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "doi",
      "data_type": "VARCHAR",
      "is_nullable": "YES"
    },
    {
      "column_name": "year",
      "data_type": "SMALLINT",
      "is_nullable": "YES"
    }
  ],
  "sample_rows": [
    {
      "ki_result_id": 856816,
      "reactant_set_id": 854546,
      "entryid": 8856,
      "affinity_type": "EC50",
      "relation": "=",
      "value": 2.5,
      "unit": "nM",
      "p_affinity": 8.6,
      "raw_value": "2.50",
      "uncertainty": null,
      "monomerid": 423528,
      "compound_name": "US10508115, Compound If-04",
      "inchi_key": "LVYHWHWKFVCUMH-UHFFFAOYSA-N",
      "polymerid": 12,
      "complexid": null,
      "target_name": "Interleukin-6",
      "uniprot": "P05231",
      "uniprot_raw": "P05231",
      "organism": "Homo sapiens",
      "taxid": "9606",
      "ph": null,
      "temp_k": null,
      "assay_name": "Interleukin 6 Induction Assay",
      "articleid": 8837,
      "source_id": "US10508115B2",
      "doi": null,
      "year": 2019
    },
    {
      "ki_result_id": 856746,
      "reactant_set_id": 854476,
      "entryid": 8856,
      "affinity_type": "EC50",
      "relation": "=",
      "value": 3.77,
      "unit": "nM",
      "p_affinity": 8.42,
      "raw_value": "3.77",
      "uncertainty": null,
      "monomerid": 423493,
      "compound_name": "US10508115, Compound Ib-12",
      "inchi_key": "RFJDLSDFKISQEE-UHFFFAOYSA-N",
      "polymerid": 12,
      "complexid": null,
      "target_name": "Interleukin-6",
      "uniprot": "P05231",
      "uniprot_raw": "P05231",
      "organism": "Homo sapiens",
      "taxid": "9606",
      "ph": null,
      "temp_k": null,
      "assay_name": "Interleukin 6 Induction Assay",
      "articleid": 8837,
      "source_id": "US10508115B2",
      "doi": null,
      "year": 2019
    },
    {
      "ki_result_id": 856820,
      "reactant_set_id": 854550,
      "entryid": 8856,
      "affinity_type": "EC50",
      "relation": "=",
      "value": 3.8,
      "unit": "nM",
      "p_affinity": 8.42,
      "raw_value": "3.80",
      "uncertainty": null,
      "monomerid": 423530,
      "compound_name": "US10508115, Compound If-06",
      "inchi_key": "ZLEXSMIIQCQXKU-UHFFFAOYSA-N",
      "polymerid": 12,
      "complexid": null,
      "target_name": "Interleukin-6",
      "uniprot": "P05231",
      "uniprot_raw": "P05231",
      "organism": "Homo sapiens",
      "taxid": "9606",
      "ph": null,
      "temp_k": null,
      "assay_name": "Interleukin 6 Induction Assay",
      "articleid": 8837,
      "source_id": "US10508115B2",
      "doi": null,
      "year": 2019
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
LIMIT 15
```

**Result:**

_15 row(s)._

| compound_name | target_name | organism | koff_per_s | residence_time_min | kon_per_M_s | kd_nm | source_id | year |
|---|---|---|---|---|---|---|---|---|
| carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 8 | Carbonic anhydrase 13 | Homo sapiens | 1e-08 | 1.66667e+06 |  |  | 29466001 | 2018 |
| carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 10 | Carbonic anhydrase 13 | Homo sapiens | 1e-08 | 1.66667e+06 |  |  | 29466001 | 2018 |
| carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 7 | Carbonic anhydrase 13 | Homo sapiens | 1e-08 | 1.66667e+06 |  |  | 29466001 | 2018 |
| carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 14 | Carbonic anhydrase 13 | Homo sapiens | 1e-08 | 1.66667e+06 |  |  | 29466001 | 2018 |
| CHEMBL4206099 | Chymase | Homo sapiens | 2.1e-08 | 793651 |  |  | 29191554 | 2018 |
| 4-((R)-1-((R)-6-(5-chloro-2-methoxybenzyl)-2,5-dioxo-1,4-diazepane-... | Chymase | Homo sapiens | 1.25e-07 | 133333 |  |  | 29191554 | 2018 |
| 3-Isopropyl-1-methanesulfonyl-4-(4-piperidin-1-yl-but-2-enoyl)-hexa... | Neutrophil elastase | Homo sapiens | 2.07e-06 | 8051.5 | 6630 |  | 12190311 | 2002 |
| CHEMBL145002 | Neutrophil elastase | Homo sapiens | 6.166e-06 | 2703 | 64570 |  | 2299617 | 1990 |
| Doramapimod | Mitogen-activated protein kinase 14 | Homo sapiens | 8e-06 | 2083.3 |  |  | 12941343 | 2003 |
| CHEMBL146003 | Neutrophil elastase | Homo sapiens | 8.71e-06 | 1913.5 | 1318 |  | 2299617 | 1990 |
| CHEMBL2079714 | Beta-lactamase | Pseudomonas aeruginosa (strain ATCC 15692 / DSM 22644 / CIP 104116 ... | 9e-06 | 1851.9 |  |  | 9767633 | 1998 |
| CHEMBL2079714 | Beta-lactamase | Pseudomonas aeruginosa (strain ATCC 15692 / DSM 22644 / CIP 104116 ... | 9e-06 | 1851.9 | 0.9 |  | 9767633 | 1998 |
| 4-[1-(2,2-Dimethyl-propyl)-azetidine-3-carbonyl]-3-isopropyl-1-meth... | Neutrophil elastase | Homo sapiens | 1.09e-05 | 1529.1 | 6306 |  | 12190311 | 2002 |
| CHEMBL145729 | Neutrophil elastase | Homo sapiens | 1.122e-05 | 1485.4 | 7079 |  | 2299617 | 1990 |
| 2-Ethoxy-5-methyl-benzo[d][1,3]oxazin-4-one | Neutrophil elastase | Homo sapiens | 1.175e-05 | 1418.4 | 102300 |  | 2299617 | 1990 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 15,
  "truncated": false,
  "rows": [
    {
      "compound_name": "carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 8",
      "target_name": "Carbonic anhydrase 13",
      "organism": "Homo sapiens",
      "koff_per_s": 1e-08,
      "residence_time_min": 1666666.7,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29466001",
      "year": 2018
    },
    {
      "compound_name": "carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 10",
      "target_name": "Carbonic anhydrase 13",
      "organism": "Homo sapiens",
      "koff_per_s": 1e-08,
      "residence_time_min": 1666666.7,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29466001",
      "year": 2018
    },
    {
      "compound_name": "carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 7",
      "target_name": "Carbonic anhydrase 13",
      "organism": "Homo sapiens",
      "koff_per_s": 1e-08,
      "residence_time_min": 1666666.7,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29466001",
      "year": 2018
    },
    {
      "compound_name": "carbonic anhydrase (CA) inhibitors, benzenesulphonamide ligand, 14",
      "target_name": "Carbonic anhydrase 13",
      "organism": "Homo sapiens",
      "koff_per_s": 1e-08,
      "residence_time_min": 1666666.7,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29466001",
      "year": 2018
    },
    {
      "compound_name": "CHEMBL4206099",
      "target_name": "Chymase",
      "organism": "Homo sapiens",
      "koff_per_s": 2.1e-08,
      "residence_time_min": 793650.8,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29191554",
      "year": 2018
    },
    {
      "compound_name": "4-((R)-1-((R)-6-(5-chloro-2-methoxybenzyl)-2,5-dioxo-1,4-diazepane-4-carboxamido)propyl)-2-aminobenzoic acid",
      "target_name": "Chymase",
      "organism": "Homo sapiens",
      "koff_per_s": 1.25e-07,
      "residence_time_min": 133333.3,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "29191554",
      "year": 2018
    },
    {
      "compound_name": "3-Isopropyl-1-methanesulfonyl-4-(4-piperidin-1-yl-but-2-enoyl)-hexahydro-pyrrolo[3,2-b]pyrrol-2-one; hydrochloride",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 2.07e-06,
      "residence_time_min": 8051.5,
      "kon_per_M_s": 6630.0,
      "kd_nm": null,
      "source_id": "12190311",
      "year": 2002
    },
    {
      "compound_name": "CHEMBL145002",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 6.166e-06,
      "residence_time_min": 2703.0,
      "kon_per_M_s": 64570.0,
      "kd_nm": null,
      "source_id": "2299617",
      "year": 1990
    },
    {
      "compound_name": "Doramapimod",
      "target_name": "Mitogen-activated protein kinase 14",
      "organism": "Homo sapiens",
      "koff_per_s": 8e-06,
      "residence_time_min": 2083.3,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "12941343",
      "year": 2003
    },
    {
      "compound_name": "CHEMBL146003",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 8.71e-06,
      "residence_time_min": 1913.5,
      "kon_per_M_s": 1318.0,
      "kd_nm": null,
      "source_id": "2299617",
      "year": 1990
    },
    {
      "compound_name": "CHEMBL2079714",
      "target_name": "Beta-lactamase",
      "organism": "Pseudomonas aeruginosa (strain ATCC 15692 / DSM 22644 / CIP 104116 / JCM 14847 / LMG 12228 / 1C / PRS 101 / PAO1)",
      "koff_per_s": 9e-06,
      "residence_time_min": 1851.9,
      "kon_per_M_s": null,
      "kd_nm": null,
      "source_id": "9767633",
      "year": 1998
    },
    {
      "compound_name": "CHEMBL2079714",
      "target_name": "Beta-lactamase",
      "organism": "Pseudomonas aeruginosa (strain ATCC 15692 / DSM 22644 / CIP 104116 / JCM 14847 / LMG 12228 / 1C / PRS 101 / PAO1)",
      "koff_per_s": 9e-06,
      "residence_time_min": 1851.9,
      "kon_per_M_s": 0.9,
      "kd_nm": null,
      "source_id": "9767633",
      "year": 1998
    },
    {
      "compound_name": "4-[1-(2,2-Dimethyl-propyl)-azetidine-3-carbonyl]-3-isopropyl-1-methanesulfonyl-hexahydro-pyrrolo[3,2-b]pyrrol-2-one; hydrochloride",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 1.09e-05,
      "residence_time_min": 1529.1,
      "kon_per_M_s": 6306.0,
      "kd_nm": null,
      "source_id": "12190311",
      "year": 2002
    },
    {
      "compound_name": "CHEMBL145729",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 1.122e-05,
      "residence_time_min": 1485.4,
      "kon_per_M_s": 7079.0,
      "kd_nm": null,
      "source_id": "2299617",
      "year": 1990
    },
    {
      "compound_name": "2-Ethoxy-5-methyl-benzo[d][1,3]oxazin-4-one",
      "target_name": "Neutrophil elastase",
      "organism": "Homo sapiens",
      "koff_per_s": 1.175e-05,
      "residence_time_min": 1418.4,
      "kon_per_M_s": 102300.0,
      "kd_nm": null,
      "source_id": "2299617",
      "year": 1990
    }
  ]
}
```

</details>

<!-- results-sha256: 221ed582473e208a6e8ee6f977a0a5f6e57535828de1578748c2ab8b0b99e166 -->

## Answer

BindingDB holds only about 1,000 koff measurements (about 250 records have both kon and koff), so kinetic
data is sparse. The longest residence times (1/koff) are:

- **Carbonic anhydrase XIII with four benzenesulfonamides:** koff = 1×10⁻⁸ s⁻¹ (PMID 29466001). That would be a residence time of about 3 years. Because all four values are identical, they are almost certainly the method's detection limit recorded as exact values.
- **Chymase inhibitors:** koff 2.1×10⁻⁸ and 1.25×10⁻⁷ s⁻¹ (PMID 29191554).
- **Neutrophil elastase acylating inhibitors** (benzoxazinones and related compounds; PMIDs 2299617, 12190311): koff about 2×10⁻⁶ to 1.2×10⁻⁵ s⁻¹, so residence times of about 1–5.6 days. These form a covalent acyl-enzyme, which explains the slow off-rates.
- **Doramapimod (BIRB-796) on p38α (MAPK14):** koff 8×10⁻⁶ s⁻¹, about 35 hours (PMID 12941343). This is a textbook slow-dissociating, DFG-out kinase inhibitor.

**Data-quality notes:**
- CHEMBL2079714 on *P. aeruginosa* β-lactamase appears twice. One copy has a kon of 0.9 M⁻¹s⁻¹, which is implausibly low.
- None of the top rows has a Kd in the same record.
