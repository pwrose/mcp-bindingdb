# Most potent Ki ligands for human EGFR

> **Question:** What are the most potent known Ki ligands for wild-type human EGFR?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_targets`

```json
{"query": "EGFR", "organism": "Homo sapiens", "limit": 5}
```

**Result:**

_5 row(s), more available (truncated by limit) — table shows selected columns._

| target_id | name | uniprot_raw | organism | n_activities | n_compounds | matched_name |
|---|---|---|---|---|---|---|
| 520 | Epidermal growth factor receptor | P00533 | Homo sapiens | 23266 | 14126 | EGFR |
| 60 | Epidermal growth factor receptor [T790M,L858R] | P00533[T790M,L858R] | Homo sapiens | 1536 | 1276 | EGFR |
| 1058 | Epidermal growth factor receptor [L858R,T790M,C797S] | P00533[L858R,T790M,C797S] | Homo sapiens | 690 | 666 | EGFR |
| 1214 | Epidermal growth factor receptor [L858R,C797S] | P00533[L858R,C797S] | Homo sapiens | 684 | 683 | EGFR |
| 51 | Epidermal growth factor receptor [L858R] | P00533[L858R] | Homo sapiens | 678 | 646 | EGFR |

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
      "n_compounds": 14126,
      "matched_name": "EGFR"
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
      "n_compounds": 1276,
      "matched_name": "EGFR"
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
      "n_compounds": 666,
      "matched_name": "EGFR"
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
      "n_compounds": 683,
      "matched_name": "EGFR"
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
      "n_compounds": 646,
      "matched_name": "EGFR"
    }
  ]
}
```

</details>

### 2. `find_ligands_for_target`

```json
{"target_id": 520, "affinity_types": ["Ki"], "limit": 10}
```

**Result:**

_10 row(s), more available (truncated by limit) — table shows selected columns._

| ki_result_id | monomerid | compound_name | relation | value | unit | p_affinity | n_measurements | source_id | year |
|---|---|---|---|---|---|---|---|---|---|
| 50029862 | 3032 | PD153035 | = | 0.006 | nM | 11.22 | 1 | 18077363 | 2007 |
| 50743804 | 50238182 | CHEMBL4100860 | = | 0.07 | nM | 10.15 | 1 | 28603991 | 2017 |
| 50247882 | 5446 | Tarceva | = | 0.1 | nM | 10 | 6 | 25383627 | 2014 |
| 50552347 | 50210162 | CHEMBL3883534 | = | 0.14 | nM | 9.85 | 1 | 28280261 | 2017 |
| 50743818 | 50238177 | CHEMBL4098072 | = | 0.35 | nM | 9.46 | 6 | 28603991 | 2017 |
| 51525437 | 50613695 | CHEMBL5274166 | = | 0.35 | nM | 9.46 | 5 | 27564586 | 2016 |
| 50917515 | 5447 | Iressa | = | 0.4 | nM | 9.4 | 8 | 15975507 | 2005 |
| 51604168 | 50338602 | Iressa | = | 0.4 | nM | 9.4 | 1 | 38852338 |  |
| 50459689 | 50141636 | CHEMBL3758502 | = | 0.6 | nM | 9.22 | 1 | 26639762 | 2016 |
| 51525430 | 50613687 | CHEMBL5285503 | < | 0.6 | nM | 9.22 | 2 | 27564586 | 2016 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 10,
  "truncated": true,
  "rows": [
    {
      "ki_result_id": 50029862,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.006,
      "unit": "nM",
      "p_affinity": 11.22,
      "monomerid": 3032,
      "compound_name": "PD153035",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_473565 (CHEMBL940057)",
      "source_id": "18077363",
      "doi": "10.1073/pnas.0708800104",
      "year": 2007,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50743804,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.07,
      "unit": "nM",
      "p_affinity": 10.15,
      "monomerid": 50238182,
      "compound_name": "CHEMBL4100860",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1663485 (CHEMBL4013166)",
      "source_id": "28603991",
      "doi": "10.1021/acs.jmedchem.7b00316",
      "year": 2017,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50247882,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.1,
      "unit": "nM",
      "p_affinity": 10.0,
      "monomerid": 5446,
      "compound_name": "Tarceva",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1440951 (CHEMBL3375801)",
      "source_id": "25383627",
      "doi": "10.1021/jm501578n",
      "year": 2014,
      "n_measurements": 6
    },
    {
      "ki_result_id": 50552347,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.14,
      "unit": "nM",
      "p_affinity": 9.85,
      "monomerid": 50210162,
      "compound_name": "CHEMBL3883534",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1634421 (CHEMBL3877213)",
      "source_id": "28280261",
      "doi": "10.1038/nrd.2016.266",
      "year": 2017,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50743818,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.35,
      "unit": "nM",
      "p_affinity": 9.46,
      "monomerid": 50238177,
      "compound_name": "CHEMBL4098072",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1663485 (CHEMBL4013166)",
      "source_id": "28603991",
      "doi": "10.1021/acs.jmedchem.7b00316",
      "year": 2017,
      "n_measurements": 6
    },
    {
      "ki_result_id": 51525437,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.35,
      "unit": "nM",
      "p_affinity": 9.46,
      "monomerid": 50613695,
      "compound_name": "CHEMBL5274166",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2293073",
      "source_id": "27564586",
      "doi": "10.1021/acs.jmedchem.6b00995",
      "year": 2016,
      "n_measurements": 5
    },
    {
      "ki_result_id": 50917515,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.4,
      "unit": "nM",
      "p_affinity": 9.4,
      "monomerid": 5447,
      "compound_name": "Iressa",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_660429 (CHEMBL1250019)",
      "source_id": "15975507",
      "doi": "10.1016/j.chembiol.2005.04.011",
      "year": 2005,
      "n_measurements": 8
    },
    {
      "ki_result_id": 51604168,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.4,
      "unit": "nM",
      "p_affinity": 9.4,
      "monomerid": 50338602,
      "compound_name": "Iressa",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2476250",
      "source_id": "38852338",
      "doi": "10.1016/j.ejmech.2024.116540",
      "year": null,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50459689,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 0.6,
      "unit": "nM",
      "p_affinity": 9.22,
      "monomerid": 50141636,
      "compound_name": "CHEMBL3758502",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1551285 (CHEMBL3762136)",
      "source_id": "26639762",
      "doi": "10.1016/j.bmcl.2015.11.078",
      "year": 2016,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51525430,
      "affinity_type": "Ki",
      "relation": "<",
      "value": 0.6,
      "unit": "nM",
      "p_affinity": 9.22,
      "monomerid": 50613687,
      "compound_name": "CHEMBL5285503",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2293072",
      "source_id": "27564586",
      "doi": "10.1021/acs.jmedchem.6b00995",
      "year": 2016,
      "n_measurements": 2
    }
  ]
}
```

</details>

<!-- results-sha256: 09f1eca55ff8f9772db1064149af726cb5c9ef56deee14bb5024848f081b068f -->

## Answer

Wild-type human EGFR is target **520** (UniProt P00533, 23,266 measurements). Mutant forms such as
T790M/L858R are separate targets, so they are not mixed in here.

The most potent Ki values for wild-type EGFR:

- **PD153035** (BDBM3032): Ki 0.006 nM. This is a single measurement (PMID 18077363).
- **Erlotinib** (Tarceva, BDBM5446): best Ki 0.1 nM, out of 6 Ki measurements.
- **Gefitinib** (Iressa): Ki 0.4 nM, out of 8 measurements.
- The remaining hits are research compounds known only by ChEMBL ids, with Ki 0.07–0.6 nM.

**Things to check:**
- Several top values come from a single measurement (`n_measurements = 1`).
- Gefitinib appears under two compound ids (BDBM5447 and BDBM50338602), so BindingDB holds duplicate records.
- One citation has no publication year.
