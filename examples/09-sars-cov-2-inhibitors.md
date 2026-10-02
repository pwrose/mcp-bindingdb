# Potent SARS-CoV-2 inhibitors

> **Question:** Find the most potent SARS-CoV-2 inhibitors in BindingDB.

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "main protease", "organism": "SARS"}
```

**Result:**

_0 row(s) — table shows selected columns._

_No rows._

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 0,
  "truncated": false,
  "rows": []
}
```

</details>

### 2. `run_sql`

```json
{}
```

```sql
SELECT target_kind, target_id, name, uniprot_raw, n_activities, n_compounds
FROM target
WHERE organism = 'Severe acute respiratory syndrome coronavirus 2'
ORDER BY n_activities DESC
```

**Result:**

_5 row(s)._

| target_kind | target_id | name | uniprot_raw | n_activities | n_compounds |
|---|---|---|---|---|---|
| polymer | 770 | Replicase polyprotein 1ab | P0DTD1 | 13750 | 9142 |
| polymer | 1225 | Replicase polyprotein 1a | P0DTC1 | 5492 | 5153 |
| polymer | 824 | Spike glycoprotein | P0DTC2 | 113 | 87 |
| polymer | 1333 | Replicase polyprotein 1ab-His6 | P0DTD1,SSSSSS | 4 | 4 |
| polymer | 777 | Replicase polyprotein 1ab [3264-3569] | P0DTD1[3264-3569] | 3 | 3 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 5,
  "truncated": false,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 770,
      "name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "n_activities": 13750,
      "n_compounds": 9142
    },
    {
      "target_kind": "polymer",
      "target_id": 1225,
      "name": "Replicase polyprotein 1a",
      "uniprot_raw": "P0DTC1",
      "n_activities": 5492,
      "n_compounds": 5153
    },
    {
      "target_kind": "polymer",
      "target_id": 824,
      "name": "Spike glycoprotein",
      "uniprot_raw": "P0DTC2",
      "n_activities": 113,
      "n_compounds": 87
    },
    {
      "target_kind": "polymer",
      "target_id": 1333,
      "name": "Replicase polyprotein 1ab-His6",
      "uniprot_raw": "P0DTD1,SSSSSS",
      "n_activities": 4,
      "n_compounds": 4
    },
    {
      "target_kind": "polymer",
      "target_id": 777,
      "name": "Replicase polyprotein 1ab [3264-3569]",
      "uniprot_raw": "P0DTD1[3264-3569]",
      "n_activities": 3,
      "n_compounds": 3
    }
  ]
}
```

</details>

### 3. `find_ligands_for_target`

```json
{"target_id": 770, "affinity_types": ["IC50", "Ki"], "max_value_nm": 10, "limit": 10}
```

**Result:**

_10 row(s), more available (truncated by limit) — table shows selected columns._

| monomerid | compound_name | affinity_type | relation | value | p_affinity | assay_name | source_id | year |
|---|---|---|---|---|---|---|---|---|
| 50642734 | CHEMBL5575722 | IC50 | < | 0.01 | 11 | ChEMBL_2458408 | 38179950 |  |
| 513874 | bioRxiv20220126.477782, S-217622 | IC50 | = | 0.013 | 10.89 | ChEMBL_2194251 (CHEMBL5106611) | 36107752 | 2022 |
| 50643614 | CHEMBL5563071 | Ki | = | 0.025 | 10.6 | ChEMBL_2461957 | 38335815 |  |
| 510018 | (3S)-3-({N-[(4-methoxy-1H-indol-2-yl)carbonyl]-L-leucyl}amino)-2-ox... | IC50 | = | 0.03 | 10.52 | SARS-CoV-2 Coronavirus 3C Protease FRET Assay | WO2021205290 | 2021 |
| 617076 | US11753373, Compound D-3-a | Ki | = | 0.04 | 10.4 | ChEMBL_2461957 | 38335815 |  |
| 50643616 | CHEMBL5569828 | Ki | = | 0.09 | 10.05 | ChEMBL_2461957 | 38335815 |  |
| 50643619 | CHEMBL5569267 | Ki | = | 0.094 | 10.03 | ChEMBL_2461957 | 38335815 |  |
| 420298 | PF-0835231 | Ki | = | 0.1 | 10 | ChEMBL_2319961 | 37859715 | 2023 |
| 50645474 | CHEMBL5592467 | Ki | = | 0.17 | 9.77 | ChEMBL_2472180 | 38687966 |  |
| 50662448 | CHEMBL5093164 | IC50 | = | 0.17 | 9.77 | ChEMBL_2641261 | 39121741 |  |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 10,
  "truncated": true,
  "rows": [
    {
      "ki_result_id": 51596048,
      "affinity_type": "IC50",
      "relation": "<",
      "value": 0.01,
      "unit": "nM",
      "p_affinity": 11.0,
      "monomerid": 50642734,
      "compound_name": "CHEMBL5575722",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2458408",
      "source_id": "38179950",
      "doi": "10.1021/acs.jmedchem.3c01971",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51461491,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.013,
      "unit": "nM",
      "p_affinity": 10.89,
      "monomerid": 513874,
      "compound_name": "bioRxiv20220126.477782, S-217622",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2194251 (CHEMBL5106611)",
      "source_id": "36107752",
      "doi": "10.1021/acs.jmedchem.2c01146",
      "year": 2022,
      "n_measurements": 2
    },
    {
      "ki_result_id": 51598152,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.025,
      "unit": "nM",
      "p_affinity": 10.6,
      "monomerid": 50643614,
      "compound_name": "CHEMBL5563071",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2461957",
      "source_id": "38335815",
      "doi": "10.1016/j.ejmech.2024.116132",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 1070309,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.03,
      "unit": "nM",
      "p_affinity": 10.52,
      "monomerid": 510018,
      "compound_name": "(3S)-3-({N-[(4-methoxy-1H-indol-2-yl)carbonyl]-L-leucyl}amino)-2-oxo-4-[(3S)-2-oxopyrrolidin-3-yl]butyl 1-methyl-D-prolinate",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "SARS-CoV-2 Coronavirus 3C Protease FRET Assay",
      "source_id": "WO2021205290",
      "doi": null,
      "year": 2021,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51598148,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.04,
      "unit": "nM",
      "p_affinity": 10.4,
      "monomerid": 617076,
      "compound_name": "US11753373, Compound D-3-a",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2461957",
      "source_id": "38335815",
      "doi": "10.1016/j.ejmech.2024.116132",
      "year": null,
      "n_measurements": 2
    },
    {
      "ki_result_id": 51598154,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.09,
      "unit": "nM",
      "p_affinity": 10.05,
      "monomerid": 50643616,
      "compound_name": "CHEMBL5569828",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2461957",
      "source_id": "38335815",
      "doi": "10.1016/j.ejmech.2024.116132",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51598157,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.094,
      "unit": "nM",
      "p_affinity": 10.03,
      "monomerid": 50643619,
      "compound_name": "CHEMBL5569267",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2461957",
      "source_id": "38335815",
      "doi": "10.1016/j.ejmech.2024.116132",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51539987,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.1,
      "unit": "nM",
      "p_affinity": 10.0,
      "monomerid": 420298,
      "compound_name": "PF-0835231",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2319961",
      "source_id": "37859715",
      "doi": "10.1039/d3md00306j",
      "year": 2023,
      "n_measurements": 13
    },
    {
      "ki_result_id": 51601856,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.17,
      "unit": "nM",
      "p_affinity": 9.77,
      "monomerid": 50645474,
      "compound_name": "CHEMBL5592467",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2472180",
      "source_id": "38687966",
      "doi": "10.1021/acs.jmedchem.3c02469",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51644761,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.17,
      "unit": "nM",
      "p_affinity": 9.77,
      "monomerid": 50662448,
      "compound_name": "CHEMBL5093164",
      "polymerid": 770,
      "complexid": null,
      "target_name": "Replicase polyprotein 1ab",
      "uniprot_raw": "P0DTD1",
      "organism": "Severe acute respiratory syndrome coronavirus 2",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2641261",
      "source_id": "39121741",
      "doi": "10.1016/j.ejmech.2024.116704",
      "year": null,
      "n_measurements": 1
    }
  ]
}
```

</details>

<!-- results-sha256: a916c77014f54657478c80863ed2bd3f2d3c57004fee9ff660c39ad1b81dfd06 -->

## Answer

**Step 1 found nothing.** Searching for "main protease" with organism "SARS" returned no rows. BindingDB
names viral proteases after their UniProt polyproteins, and the organism is stored under its full name.
Listing all targets for "Severe acute respiratory syndrome coronavirus 2" with `run_sql` found them:

- **Replicase polyprotein 1ab** (pp1ab, P0DTD1): 13,750 measurements.
- **Replicase polyprotein 1a** (P0DTC1): 5,492 measurements.
- **Spike glycoprotein** (P0DTC2): 113 measurements.

The most potent compounds on pp1ab (IC50 or Ki of 10 nM or less) have values of 0.01–0.17 nM. Two of them
are named:
- **S-217622 (ensitrelvir):** IC50 0.013 nM. Published reports give ensitrelvir's Mpro IC50 as about 0.013 **µM** (13 nM), so this record is probably a µM/nM unit error. Check it with `get_activity`.
- **PF-00835231** (the active form of lufotrelvir): Ki 0.1 nM.
- The others are ChEMBL compounds from recent papers (PMIDs 38179950–39121741) and patent compounds, e.g. a peptidomimetic from WO2021205290 with an IC50 of 0.03 nM in a 3C-protease FRET assay.

**Caveats:**
- pp1ab contains both the main protease (Mpro/nsp5) and the papain-like protease (PLpro/nsp3). The target record doesn't say which one was assayed; `assay_name`, or the assay description from `get_activity`, does. ChEMBL-derived rows often give only a ChEMBL assay id.
- Several recent ChEMBL-derived citations have no publication year.
