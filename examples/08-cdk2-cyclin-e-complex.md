# Inhibitors of the CDK2/cyclin E complex

> **Question:** What is the CDK2/cyclin E complex made of in BindingDB, and what are its most potent inhibitors (sub-nanomolar)?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "CDK2/Cyclin E", "limit": 3}
```

**Result:**

_2 row(s) — table shows selected columns._

| target_kind | target_id | name | n_activities | n_compounds | matched_name |
|---|---|---|---|---|---|
| complex | 81 | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1 | 8087 | 6210 | CDK2/Cyclin E |
| complex | 50000034 | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1/G1/S-specific cyc... | 272 | 261 | CDK2/Cyclin E/G1/S-specific cyclin E2 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 2,
  "truncated": false,
  "rows": [
    {
      "target_kind": "complex",
      "target_id": 81,
      "name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot": null,
      "uniprot_raw": null,
      "organism": null,
      "type": "Protein",
      "n_activities": 8087,
      "n_compounds": 6210,
      "matched_name": "CDK2/Cyclin E"
    },
    {
      "target_kind": "complex",
      "target_id": 50000034,
      "name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1/G1/S-specific cyclin-E2",
      "uniprot": null,
      "uniprot_raw": null,
      "organism": null,
      "type": null,
      "n_activities": 272,
      "n_compounds": 261,
      "matched_name": "CDK2/Cyclin E/G1/S-specific cyclin E2"
    }
  ]
}
```

</details>

### 2. `get_target`

```json
{"target_id": 81, "target_kind": "complex"}
```

**Result:**

**target**

| field | value |
|---|---|
| target_kind | complex |
| target_id | 81 |
| name | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1 |
| uniprot |  |
| uniprot_raw |  |
| organism |  |
| taxid |  |
| type | Protein |
| res_count |  |
| n_pdb_ids | 457 |
| chembl_id |  |
| n_activities | 8087 |
| n_compounds | 6210 |
| pdb_ids | 9NYQ,5L2W,8H4R,7XQK,7KJS,9OB6,9OB5,9OB4,9OB3,9OB2,9NYR,9GP3,9GOP,9D... |
| comments |  |

**synonyms:** CDK2/E, CDK2/E1, CDK2/CycE, CDK2/Cyclin E, Cyclin-Dependent Kinase 2 (CDK2), Cyclin-dependent kinase 2/cyclin E1, Cyclin-dependent kinase 2/G1/S-specific cyclin E1, Cyclin-dependent kinase 2/G1/S-specific cyclin-E1

**measurements_by_type**

| affinity_type | n_measurements | n_compounds | best_p_affinity |
|---|---|---|---|
| IC50 | 5866 | 5211 | 9.67 |
| Ki | 2201 | 990 | 10.4 |
| EC50 | 20 | 20 | 7 |

**components**

| type | polymerid | polymer_name | uniprot_raw | monomerid |
|---|---|---|---|---|
| Protein | 796 | Cyclin-dependent kinase 2 | P24941 |  |
| Protein | 802 | G1/S-specific cyclin-E1 | P24864 |  |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "target": {
    "target_kind": "complex",
    "target_id": 81,
    "name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
    "uniprot": null,
    "uniprot_raw": null,
    "organism": null,
    "taxid": null,
    "type": "Protein",
    "res_count": null,
    "n_pdb_ids": 457,
    "chembl_id": null,
    "n_activities": 8087,
    "n_compounds": 6210,
    "pdb_ids": "9NYQ,5L2W,8H4R,7XQK,7KJS,9OB6,9OB5,9OB4,9OB3,9OB2,9NYR,9GP3,9GOP,9D0X,9D0W,9D0V,8VQ4,8VQ3,1W98,9BJC,8H6T,8H6P,23SR,9FR2,8B54,7QHL,7B7S,7ACK,6RIJ,6JGM,6INL,6GVA,5LMK,3DOG,3DDQ,3DDP,2G9X,2CCI,2CCH,1QMZ,1P5E,1GY3,9QJJ,9QCX,9QCV,9I9K,9I9J,9D0U,8ROZ,8OY2,8OR4,8OR0,8FP5,8FP0,8FOW,8CUR,7VDU,7UXK,7UXI,7SA0,7S9X,7S85,7S84,7S7A,7S4T,7RXO,7RWE,7RA5,7NVQ,7M2F,7B5R,7B5L,6P3W,6ATH,5K4J,5JQ8,5JQ5,5IF1,5IEY,5IEX,5IEV,5FP6,5FP5,5D1J,5ANO,5ANK,5ANJ,5ANI,5ANG,5ANE,5AND,5A14,4RJ3,4NJ3,4LYN,4KD1,4II5,4FX3,4FKW,4FKV,4FKU,4FKT,4FKS,4FKR,4FKQ,4FKP,4FKO,4FKL,4FKJ,4FKI,4FKG,4EK8,4EK6,4EK5,4EK4,4EK3,4D1Z,4D1X,4BZD,4BGH,4BCP,4BCO,4BCN,4BCK,4ACM,3WBL,3UNK,3UNJ,3ULI,3TNW,3TIZ,3TIY,3TI1,3SW7,3SW4,3S2P,3PJ8,3NS9,3MY5,3LFS,3LFQ,3LFN,3LE6,3IGG,3IG7,3FZ1,3F5X,3EZV,3EZR,3EOC,3EJ1,3EID,3BHV,3BHU,3BHT,2XNB,2XMY,2X1N,2WHB,2WFY,2WEV,2W1H,2W17,2W06,2W05,2VV9,2VU3,2VTT,2VTS,2VTR,2VTQ,2VTP,2VTO,2VTN,2VTM,2VTL,2VTJ,2VTI,2VTH,2VTA,2V22,2V0D,2UZO,2UZN,2UZL,2UZE,2UZD,2UZB,2UUE,2R64,2R3R,2R3Q,2R3P,2R3O,2R3N,2R3M,2R3L,2R3K,2R3J,2R3I,2R3H,2R3G,2R3F,2J9M,2I40,2FVD,2EXM,2DUV,2CLX,2CJM,2C6T,2C6O,2C6M,2C6L,2C6K,2C6I,2C69,2C68,2C5Y,2C5X,2C5V,2C5O,2C5N,2BTS,2BTR,2BHH,2BHE,2B55,2B54,2B53,2B52,2A4L,2A0C,1YKR,1Y91,1Y8Y,1WCC,1W8C,1W0X,1VYZ,1V1K,1URW,1URC,1R78,1PYE,1PXP,1PXO,1PXN,1PXM,1PXL,1PXK,1PXJ,1PXI,1PW2,1PF8,1P2A,1OL2,1OL1,1OKW,1OKV,1OIR,1OIQ,1KE9,1KE8,1KE7,1KE6,1KE5,1JVP,1JSV,1JSU,1JST,1HCL,1HCK,1H0W,1H0V,1H08,1H07,1H01,1H00,1GZ8,1GIH,1G5S,1FVV,1FVT,1FQ1,1FIN,1F5Q,1E1X,1E1V,1DM2,1DI8,1CKP,1BUH,1B39,1B38,1AQ1,11GV,8ERN,8ERD,7RWF,6OQI,5UQ3,5UQ2,5UQ1,4BCQ,4BCM,9UGF,9UAW,9UAU,9JJ5,9GNO,8YQE,8YPW,7ZPC,7UG1,7MKX,6Q4K,6Q4J,6Q4H,6Q4F,6Q4E,6Q4D,6Q4C,6Q4B,6Q4A,6Q49,6Q48,6Q3F,6Q3C,6Q3B,6GUK,6GUH,5OSJ,5OO0,5NEV,5MHQ,5CYI,4GCJ,4EZ7,4EZ3,4ERW,4CFX,4CFW,4CFM,3SQQ,3S1H,3S0O,3S00,3RZB,3RPY,3RPV,3RPR,3RPO,3ROY,3RNI,3RMF,3RM7,3RM6,3RKB,3RK9,3RK7,3RK5,3RJC,3RAL,3RAK,3RAI,3RAH,3R9O,3R9N,3R9H,3R9D,3R8Z,3R8V,3R8U,3R8P,3R8M,3R8L,3R83,3R7Y,3R7V,3R7U,3R7I,3R7E,3R73,3R71,3R6X,3R28,3R1Y,3R1S,3R1Q,3QZI,3QZH,3QZG,3QZF,3QXP,3QXO,3QX4,3QX2,3QWK,3QWJ,... [2284 chars]",
    "comments": null
  },
  "synonyms": [
    "CDK2/E",
    "CDK2/E1",
    "CDK2/CycE",
    "CDK2/Cyclin E",
    "Cyclin-Dependent Kinase 2 (CDK2)",
    "Cyclin-dependent kinase 2/cyclin E1",
    "Cyclin-dependent kinase 2/G1/S-specific cyclin E1",
    "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1"
  ],
  "measurements_by_type": [
    {
      "affinity_type": "IC50",
      "n_measurements": 5866,
      "n_compounds": 5211,
      "best_p_affinity": 9.67
    },
    {
      "affinity_type": "Ki",
      "n_measurements": 2201,
      "n_compounds": 990,
      "best_p_affinity": 10.4
    },
    {
      "affinity_type": "EC50",
      "n_measurements": 20,
      "n_compounds": 20,
      "best_p_affinity": 7.0
    }
  ],
  "components": [
    {
      "type": "Protein",
      "polymerid": 796,
      "polymer_name": "Cyclin-dependent kinase 2",
      "uniprot_raw": "P24941",
      "monomerid": null
    },
    {
      "type": "Protein",
      "polymerid": 802,
      "polymer_name": "G1/S-specific cyclin-E1",
      "uniprot_raw": "P24864",
      "monomerid": null
    }
  ]
}
```

</details>

### 3. `find_ligands_for_target`

```json
{"target_id": 81, "target_kind": "complex", "max_value_nm": 1, "limit": 10}
```

**Result:**

_10 row(s), more available (truncated by limit) — table shows selected columns._

| monomerid | compound_name | affinity_type | relation | value | p_affinity | n_measurements | source_id | year |
|---|---|---|---|---|---|---|---|---|
| 498218 | US11718603, Example 43 | Ki | = | 0.04 | 10.4 | 2 | US11014911B2 | 2021 |
| 498217 | US11718603, Example 42 | Ki | = | 0.05 | 10.3 | 2 | US11014911B2 | 2021 |
| 370115 | 4-({6-(2-hydroxyethyl)-8-[(1R,2S)-2-methylcyclopentyl]-7-oxo-7,8-di... | Ki | = | 0.06 | 10.22 | 3 | US10233188B2 | 2019 |
| 370149 | US11396512, Example 37 | Ki | = | 0.06 | 10.22 | 3 | US10233188B2 | 2019 |
| 498324 | US11014911, Example 149 | Ki | = | 0.06 | 10.22 | 2 | US11014911B2 | 2021 |
| 498321 | US11718603, Example 146 | Ki | = | 0.07 | 10.15 | 2 | US11014911B2 | 2021 |
| 498778 | (1R,3S)-3-(3-{[(3-methyl-1,2-  oxazol-5-yl)acetyl]amino}-1H-  pyraz... | Ki | = | 0.07 | 10.15 | 4 | US11014911B2 | 2021 |
| 370152 | US11396512, Example 40 | Ki | = | 0.08 | 10.1 | 3 | US10233188B2 | 2019 |
| 370197 | US10233188, Example 84 | Ki | = | 0.08 | 10.1 | 3 | US10233188B2 | 2019 |
| 370205 | US10800783, Example 92 | Ki | = | 0.08 | 10.1 | 4 | US10233188B2 | 2019 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 10,
  "truncated": true,
  "rows": [
    {
      "ki_result_id": 1040429,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.04,
      "unit": "nM",
      "p_affinity": 10.4,
      "monomerid": 498218,
      "compound_name": "US11718603, Example 43",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "Biochemical Assay",
      "source_id": "US11014911B2",
      "doi": null,
      "year": 2021,
      "n_measurements": 2
    },
    {
      "ki_result_id": 1040427,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.05,
      "unit": "nM",
      "p_affinity": 10.3,
      "monomerid": 498217,
      "compound_name": "US11718603, Example 42",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "Biochemical Assay",
      "source_id": "US11014911B2",
      "doi": null,
      "year": 2021,
      "n_measurements": 2
    },
    {
      "ki_result_id": 731737,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.06,
      "unit": "nM",
      "p_affinity": 10.22,
      "monomerid": 370115,
      "compound_name": "4-({6-(2-hydroxyethyl)-8-[(1R,2S)-2-methylcyclopentyl]-7-oxo-7,8-dihydropyrido[2,3-d]pyrimidin-2-yl}amino)-N-methylpiperidine-1-sulfonamide",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2/Cyclin E1 Mobility Shift Assay",
      "source_id": "US10233188B2",
      "doi": null,
      "year": 2019,
      "n_measurements": 3
    },
    {
      "ki_result_id": 731802,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.06,
      "unit": "nM",
      "p_affinity": 10.22,
      "monomerid": 370149,
      "compound_name": "US11396512, Example 37",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2/Cyclin E1 Mobility Shift Assay",
      "source_id": "US10233188B2",
      "doi": null,
      "year": 2019,
      "n_measurements": 3
    },
    {
      "ki_result_id": 1040620,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.06,
      "unit": "nM",
      "p_affinity": 10.22,
      "monomerid": 498324,
      "compound_name": "US11014911, Example 149",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "Biochemical Assay",
      "source_id": "US11014911B2",
      "doi": null,
      "year": 2021,
      "n_measurements": 2
    },
    {
      "ki_result_id": 1040614,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.07,
      "unit": "nM",
      "p_affinity": 10.15,
      "monomerid": 498321,
      "compound_name": "US11718603, Example 146",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "Biochemical Assay",
      "source_id": "US11014911B2",
      "doi": null,
      "year": 2021,
      "n_measurements": 2
    },
    {
      "ki_result_id": 1041294,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.07,
      "unit": "nM",
      "p_affinity": 10.15,
      "monomerid": 498778,
      "compound_name": "(1R,3S)-3-(3-{[(3-methyl-1,2-  oxazol-5-yl)acetyl]amino}-1H-  pyrazol-5-yl)cyclopentyl (2$#958;)-2-  ethyl-2-methylazetidine-1-  carboxylate - Isomer A",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "Biochemical Assay",
      "source_id": "US11014911B2",
      "doi": null,
      "year": 2021,
      "n_measurements": 4
    },
    {
      "ki_result_id": 731807,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.08,
      "unit": "nM",
      "p_affinity": 10.1,
      "monomerid": 370152,
      "compound_name": "US11396512, Example 40",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2/Cyclin E1 Mobility Shift Assay",
      "source_id": "US10233188B2",
      "doi": null,
      "year": 2019,
      "n_measurements": 3
    },
    {
      "ki_result_id": 731889,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.08,
      "unit": "nM",
      "p_affinity": 10.1,
      "monomerid": 370197,
      "compound_name": "US10233188, Example 84",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2/Cyclin E1 Mobility Shift Assay",
      "source_id": "US10233188B2",
      "doi": null,
      "year": 2019,
      "n_measurements": 3
    },
    {
      "ki_result_id": 731905,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.08,
      "unit": "nM",
      "p_affinity": 10.1,
      "monomerid": 370205,
      "compound_name": "US10800783, Example 92",
      "polymerid": null,
      "complexid": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2/Cyclin E1 Mobility Shift Assay",
      "source_id": "US10233188B2",
      "doi": null,
      "year": 2019,
      "n_measurements": 4
    }
  ]
}
```

</details>

<!-- results-sha256: fa140915235c979b9ed374c3427d364dcfcd63906bd200d3142e5306bf7176c2 -->

## Answer

**CDK2/cyclin E** is complex target **81**. It is made of two proteins, CDK2 (P24941) and G1/S-specific
cyclin E1 (P24864). It has 8,087 measurements (5,866 IC50, 2,201 Ki) on 6,210 compounds, and 457 PDB
structures. Complex targets have no single UniProt id, so search for them by name ("CDK2/Cyclin E").

**The most potent inhibitors are all from patents:**
- They are Ki values of **0.04–0.08 nM**, from US11014911, US11718603, US10233188 and US11396512 (2019–2023). These are recent CDK2-selective programs.
- Most compounds are known only by patent labels ("US11014911, Example 43"). `get_compound` returns their SMILES and InChIKeys.
- Several compounds have 2–4 measurements each.

There is also a CDK2/cyclin E1/E2 complex (target 50000034) with 272 more measurements. Include it for a
complete picture.
