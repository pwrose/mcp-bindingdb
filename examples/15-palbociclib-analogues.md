# Analogues of palbociclib

> **Question:** Which compounds are similar to palbociclib (one of the CDK2/cyclin A2 ligands in example 13), which targets do they bind, and how do they fare against CDK2/cyclin A2?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-03

## Tool calls

### 1. `search_compounds`

```json
{"query": "palbociclib", "limit": 3}
```

**Result:**

_1 row(s) — table shows selected columns._

| monomerid | name | smiles | n_activities | n_targets | matched_name |
|---|---|---|---|---|---|
| 6309 | Ibrance | CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C | 154 | 39 | Palbociclib |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 1,
  "truncated": false,
  "rows": [
    {
      "monomerid": 6309,
      "bdbm_id": "BDBM6309",
      "name": "Ibrance",
      "inchi_key": "AHJRHEGDXFFMBM-UHFFFAOYSA-N",
      "smiles": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C",
      "mol_weight": 447.24,
      "n_activities": 154,
      "n_targets": 39,
      "matched_name": "Palbociclib"
    }
  ]
}
```

</details>

### 2. `similarity_search`

```json
{"smiles": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C", "threshold": 0.6, "limit": 15}
```

**Result:**

**query:** input: `CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C`, canonical: `CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O`, threshold: 0.6, fingerprint: Morgan radius 2, 2048 bits, largest fragment

**n_similar_compounds:** 137

**compounds_searched:** 1464874

**search_set_size:** 1464874

_15 row(s), more available (truncated by limit) — table shows selected columns._

| monomerid | name | similarity | n_activities | n_targets |
|---|---|---|---|---|
| 6309 | Ibrance | 1 | 154 | 39 |
| 6323 | Pyrido-[2,3-d]-pyrimidin-7-one 57 | 0.954 | 2 | 2 |
| 533737 | 2-(5-(3,9-diazaspiro[5.5]undecan-3-yl)pyridin-2-ylamino)-6-acetyl-8... | 0.87 | 3 | 3 |
| 6324 | Pyrido-[2,3-d]-pyrimidin-7-one 58 | 0.862 | 2 | 2 |
| 6321 | Pyrido-[2,3-d]-pyrimidin-7-one 55 | 0.836 | 2 | 2 |
| 6325 | Pyrido-[2,3-d]-pyrimidin-7-one 59 | 0.836 | 2 | 2 |
| 533726 | 2-(5-(2,7-Diazaspiro[3.5]nonan-7-yl)pyridin-2-ylamino)-6-acetyl-8-c... | 0.829 | 3 | 3 |
| 6326 | Pyrido-[2,3-d]-pyrimidin-7-one 60 | 0.824 | 2 | 2 |
| 6302 | pyrido[2,3-d]pyrimidin-7-one 31 | 0.821 | 7 | 4 |
| 6310 | Pyrido-[2,3-d]-pyrimidin-7-one 44 | 0.817 | 3 | 3 |
| 6319 | Pyrido-[2,3-d]-pyrimidin-7-one 53 | 0.817 | 2 | 2 |
| 533738 | US11225492, Compound 6 | 0.808 | 3 | 3 |
| 50202483 | CHEMBL3954429 | 0.8 | 2 | 2 |
| 6320 | Pyrido-[2,3-d]-pyrimidin-7-one 54 | 0.797 | 2 | 2 |
| 757722 | pyridin-3-yl)-N-hydroxypiperidine-4-carboxamide | 0.789 | 3 | 3 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "query": {
    "input": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C",
    "canonical": "CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O",
    "threshold": 0.6,
    "fingerprint": "Morgan radius 2, 2048 bits, largest fragment"
  },
  "row_count": 15,
  "truncated": true,
  "rows": [
    {
      "monomerid": 6309,
      "bdbm_id": "BDBM6309",
      "name": "Ibrance",
      "smiles": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C",
      "mol_weight": 447.24,
      "n_activities": 154,
      "n_targets": 39,
      "similarity": 1.0
    },
    {
      "monomerid": 6323,
      "bdbm_id": "BDBM6323",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 57",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCCNCC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 461.25,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.954
    },
    {
      "monomerid": 533737,
      "bdbm_id": "BDBM533737",
      "name": "2-(5-(3,9-diazaspiro[5.5]undecan-3-yl)pyridin-2-ylamino)-6-acetyl-8-cyclopentyl-5-methylpyrido[2,3-d]pyrimidin-7(8H)-one",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCC4(CCNCC4)CC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 515.3,
      "n_activities": 3,
      "n_targets": 3,
      "similarity": 0.87
    },
    {
      "monomerid": 6324,
      "bdbm_id": "BDBM6324",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 58",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCCCC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 446.24,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.862
    },
    {
      "monomerid": 6321,
      "bdbm_id": "BDBM6321",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 55",
      "smiles": "CN1CCN(CC1)c1ccc(Nc2ncc3c(C)c(C(C)=O)c(=O)n(C4CCCC4)c3n2)nc1",
      "mol_weight": 461.25,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.836
    },
    {
      "monomerid": 6325,
      "bdbm_id": "BDBM6325",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 59",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCC(O)CC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 462.24,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.836
    },
    {
      "monomerid": 533726,
      "bdbm_id": "BDBM533726",
      "name": "2-(5-(2,7-Diazaspiro[3.5]nonan-7-yl)pyridin-2-ylamino)-6-acetyl-8-cyclopentyl-5-methylpyrido[2,3-d]pyrimidin-7(8H)-one",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCC4(CNC4)CC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 487.27,
      "n_activities": 3,
      "n_targets": 3,
      "similarity": 0.829
    },
    {
      "monomerid": 6326,
      "bdbm_id": "BDBM6326",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 60",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCOCC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 448.22,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.824
    },
    {
      "monomerid": 6302,
      "bdbm_id": "BDBM6302",
      "name": "pyrido[2,3-d]pyrimidin-7-one 31",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cc3)N3CCNCC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 446.24,
      "n_activities": 7,
      "n_targets": 4,
      "similarity": 0.821
    },
    {
      "monomerid": 6310,
      "bdbm_id": "BDBM6310",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 44",
      "smiles": "CCOC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCNCC3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 477.25,
      "n_activities": 3,
      "n_targets": 3,
      "similarity": 0.817
    },
    {
      "monomerid": 6319,
      "bdbm_id": "BDBM6319",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 53",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCNC(C)(C)C3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 475.27,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.817
    },
    {
      "monomerid": 533738,
      "bdbm_id": "BDBM533738",
      "name": "US11225492, Compound 6",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(cn3)N3CCCC4(CCNCC4)C3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 515.3,
      "n_activities": 3,
      "n_targets": 3,
      "similarity": 0.808
    },
    {
      "monomerid": 50202483,
      "bdbm_id": "BDBM50202483",
      "name": "CHEMBL3954429",
      "smiles": "CCN1CCN(CC1)c1ccc(Nc2ncc3c(C)c(C(C)=O)c(=O)n(C4CCCC4)c3n2)nc1",
      "mol_weight": 475.27,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.8
    },
    {
      "monomerid": 6320,
      "bdbm_id": "BDBM6320",
      "name": "Pyrido-[2,3-d]-pyrimidin-7-one 54",
      "smiles": "CC1CN(CC(C)N1)c1ccc(Nc2ncc3c(C)c(C(C)=O)c(=O)n(C4CCCC4)c3n2)nc1",
      "mol_weight": 475.27,
      "n_activities": 2,
      "n_targets": 2,
      "similarity": 0.797
    },
    {
      "monomerid": 757722,
      "bdbm_id": "BDBM757722",
      "name": "pyridin-3-yl)-N-hydroxypiperidine-4-carboxamide",
      "smiles": "CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCC(C(=O)NO)CC4)cn3)nc2n(C2CCCC2)c1=O",
      "mol_weight": 505.24,
      "n_activities": 3,
      "n_targets": 3,
      "similarity": 0.789
    }
  ],
  "n_similar_compounds": 137,
  "compounds_searched": 1464874,
  "search_set_size": 1464874
}
```

</details>

### 3. `similarity_search`

```json
{"smiles": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C", "threshold": 0.6, "summarize_by_target": true, "max_value_nm": 1000, "limit": 100}
```

**Result:**

**query:** input: `CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C`, canonical: `CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O`, threshold: 0.6, fingerprint: Morgan radius 2, 2048 bits, largest fragment

**n_similar_compounds:** 137

**n_targets:** 26

**n_compounds_measured:** 132

**compounds_searched:** 1464874

**search_set_size:** 1464874

_26 row(s) — table shows selected columns._

| target_kind | target_id | target_name | uniprot_raw | n_compounds | n_measurements | affinity_types | best_p_affinity |
|---|---|---|---|---|---|---|---|
| complex | 93 | Cyclin-dependent kinase 4/G1/S-specific cyclin-D1 |  | 57 | 89 | IC50, Ki | 9.1 |
| complex | 50000065 | CDK6/cyclin D1 |  | 50 | 62 | IC50, Ki | 9.7 |
| complex | 98 | Cyclin-dependent kinase 4/G1/S-specific cyclin-D1 [L188C] |  | 39 | 42 | IC50 | 8.7 |
| polymer | 799 | Cyclin-dependent kinase 4 | P11802 | 30 | 54 | IC50 | 8.89 |
| polymer | 909 | Cyclin-dependent kinase 6 | Q00534 | 27 | 45 | IC50 | 8.92 |
| complex | 50000016 | Cyclin-dependent kinase 4/G1/S-specific cyclin-D3 |  | 18 | 26 | IC50 | 8.66 |
| complex | 304 | Cyclin-A2 [177-432]/Cyclin-dependent kinase 2 |  | 13 | 13 | IC50 | 8 |
| polymer | 1358 | Receptor-type tyrosine-protein kinase FLT3 | P36888 | 7 | 8 | IC50 | 8.7 |
| complex | 311 | Cyclin-dependent kinase 6/G1/S-specific cyclin-D3 |  | 5 | 17 | IC50, Ki | 8.44 |
| polymer | 2556 | Histone deacetylase 6 | Q9UBN7 | 5 | 5 | IC50 | 8 |
| polymer | 1967 | Histone deacetylase 1 | Q13547 | 5 | 5 | IC50 | 7.3 |
| complex | 97 | Cyclin-A2/Cyclin-dependent kinase 2 |  | 5 | 8 | IC50 | 6.64 |
| polymer | 796 | Cyclin-dependent kinase 2 | P24941 | 4 | 5 | IC50 | 8 |
| complex | 113 | Cyclin-T1/Cyclin-dependent kinase 9 |  | 3 | 6 | IC50, Ki | 8.22 |
| complex | 81 | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1 |  | 3 | 3 | IC50 | 8 |
| complex | 50000118 | Cyclin-dependent kinase 6/G1/S-specific cyclin-D1/D2/D3 |  | 2 | 2 | IC50 | 7.82 |
| polymer | 232 | Poly [ADP-ribose] polymerase 1 | P09874 | 1 | 1 | IC50 | 8.46 |
| polymer | 905 | Stimulator of interferon genes protein | Q86WV6 | 1 | 1 | Kd | 8.22 |
| polymer | 50007111 | G1/S-specific cyclin-D2 | P30279 | 1 | 4 | IC50 | 7.82 |
| polymer | 4919 | Tyrosine-protein kinase JAK3 | P52333 | 1 | 1 | IC50 | 7.2 |
| polymer | 50007394 | Phosphatidylinositol 5-phosphate 4-kinase type-2 alpha | P48426 | 1 | 1 | IC50 | 6.68 |
| polymer | 2127 | Cytochrome P450 3A4 | P08684 | 1 | 1 | IC50 | 6.26 |
| polymer | 919 | Calcium/calmodulin-dependent protein kinase type II subunit delta | Q13557 | 1 | 1 | IC50 | 6.21 |
| polymer | 2132 | Potassium voltage-gated channel subfamily H member 2 | Q12809 | 1 | 1 | IC50 | 6.14 |
| polymer | 997 | Cyclin-dependent kinase 9 | P50750 | 1 | 2 | IC50 | 6.1 |
| polymer | 50007656 | Cyclin-dependent kinase 12 | Q9NYV4 | 1 | 1 | IC50 | 6.05 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "query": {
    "input": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C",
    "canonical": "CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O",
    "threshold": 0.6,
    "fingerprint": "Morgan radius 2, 2048 bits, largest fragment"
  },
  "n_similar_compounds": 137,
  "n_targets": 26,
  "n_compounds_measured": 132,
  "row_count": 26,
  "truncated": false,
  "rows": [
    {
      "target_kind": "complex",
      "target_id": 93,
      "target_name": "Cyclin-dependent kinase 4/G1/S-specific cyclin-D1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 57,
      "n_measurements": 89,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.1
    },
    {
      "target_kind": "complex",
      "target_id": 50000065,
      "target_name": "CDK6/cyclin D1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 50,
      "n_measurements": 62,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.7
    },
    {
      "target_kind": "complex",
      "target_id": 98,
      "target_name": "Cyclin-dependent kinase 4/G1/S-specific cyclin-D1 [L188C]",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 39,
      "n_measurements": 42,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 799,
      "target_name": "Cyclin-dependent kinase 4",
      "uniprot_raw": "P11802",
      "organism": "Homo sapiens",
      "n_compounds": 30,
      "n_measurements": 54,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.89
    },
    {
      "target_kind": "polymer",
      "target_id": 909,
      "target_name": "Cyclin-dependent kinase 6",
      "uniprot_raw": "Q00534",
      "organism": "Homo sapiens",
      "n_compounds": 27,
      "n_measurements": 45,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.92
    },
    {
      "target_kind": "complex",
      "target_id": 50000016,
      "target_name": "Cyclin-dependent kinase 4/G1/S-specific cyclin-D3",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 18,
      "n_measurements": 26,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.66
    },
    {
      "target_kind": "complex",
      "target_id": 304,
      "target_name": "Cyclin-A2 [177-432]/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 13,
      "n_measurements": 13,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 1358,
      "target_name": "Receptor-type tyrosine-protein kinase FLT3",
      "uniprot_raw": "P36888",
      "organism": "Homo sapiens",
      "n_compounds": 7,
      "n_measurements": 8,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "complex",
      "target_id": 311,
      "target_name": "Cyclin-dependent kinase 6/G1/S-specific cyclin-D3",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 5,
      "n_measurements": 17,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.44
    },
    {
      "target_kind": "polymer",
      "target_id": 2556,
      "target_name": "Histone deacetylase 6",
      "uniprot_raw": "Q9UBN7",
      "organism": "Homo sapiens",
      "n_compounds": 5,
      "n_measurements": 5,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 1967,
      "target_name": "Histone deacetylase 1",
      "uniprot_raw": "Q13547",
      "organism": "Homo sapiens",
      "n_compounds": 5,
      "n_measurements": 5,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.3
    },
    {
      "target_kind": "complex",
      "target_id": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 5,
      "n_measurements": 8,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.64
    },
    {
      "target_kind": "polymer",
      "target_id": 796,
      "target_name": "Cyclin-dependent kinase 2",
      "uniprot_raw": "P24941",
      "organism": "Homo sapiens",
      "n_compounds": 4,
      "n_measurements": 5,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "complex",
      "target_id": 113,
      "target_name": "Cyclin-T1/Cyclin-dependent kinase 9",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 3,
      "n_measurements": 6,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.22
    },
    {
      "target_kind": "complex",
      "target_id": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 3,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "complex",
      "target_id": 50000118,
      "target_name": "Cyclin-dependent kinase 6/G1/S-specific cyclin-D1/D2/D3",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 2,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.82
    },
    {
      "target_kind": "polymer",
      "target_id": 232,
      "target_name": "Poly [ADP-ribose] polymerase 1",
      "uniprot_raw": "P09874",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.46
    },
    {
      "target_kind": "polymer",
      "target_id": 905,
      "target_name": "Stimulator of interferon genes protein",
      "uniprot_raw": "Q86WV6",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 8.22
    },
    {
      "target_kind": "polymer",
      "target_id": 50007111,
      "target_name": "G1/S-specific cyclin-D2",
      "uniprot_raw": "P30279",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 4,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.82
    },
    {
      "target_kind": "polymer",
      "target_id": 4919,
      "target_name": "Tyrosine-protein kinase JAK3",
      "uniprot_raw": "P52333",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.2
    },
    {
      "target_kind": "polymer",
      "target_id": 50007394,
      "target_name": "Phosphatidylinositol 5-phosphate 4-kinase type-2 alpha",
      "uniprot_raw": "P48426",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.68
    },
    {
      "target_kind": "polymer",
      "target_id": 2127,
      "target_name": "Cytochrome P450 3A4",
      "uniprot_raw": "P08684",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.26
    },
    {
      "target_kind": "polymer",
      "target_id": 919,
      "target_name": "Calcium/calmodulin-dependent protein kinase type II subunit delta",
      "uniprot_raw": "Q13557",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.21
    },
    {
      "target_kind": "polymer",
      "target_id": 2132,
      "target_name": "Potassium voltage-gated channel subfamily H member 2",
      "uniprot_raw": "Q12809",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.14
    },
    {
      "target_kind": "polymer",
      "target_id": 997,
      "target_name": "Cyclin-dependent kinase 9",
      "uniprot_raw": "P50750",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.1
    },
    {
      "target_kind": "polymer",
      "target_id": 50007656,
      "target_name": "Cyclin-dependent kinase 12",
      "uniprot_raw": "Q9NYV4",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.05
    }
  ],
  "compounds_searched": 1464874,
  "search_set_size": 1464874
}
```

</details>

### 4. `similarity_search`

```json
{"smiles": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C", "threshold": 0.6, "target_id": 97, "target_kind": "complex", "limit": 50}
```

**Result:**

**query:** input: `CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C`, canonical: `CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O`, threshold: 0.6, fingerprint: Morgan radius 2, 2048 bits, largest fragment

**n_similar_compounds:** 44

**compounds_searched:** 3069

**search_set_size:** 3069

_44 row(s) — table shows selected columns._

| monomerid | compound_name | similarity | affinity_type | relation | value | p_affinity | n_measurements | source_id | year |
|---|---|---|---|---|---|---|---|---|---|
| 6309 | Ibrance | 1 | IC50 | = | 230 | 6.64 | 11 | 24417566 | 2014 |
| 6323 | Pyrido-[2,3-d]-pyrimidin-7-one 57 | 0.954 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6324 | Pyrido-[2,3-d]-pyrimidin-7-one 58 | 0.862 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6321 | Pyrido-[2,3-d]-pyrimidin-7-one 55 | 0.836 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6325 | Pyrido-[2,3-d]-pyrimidin-7-one 59 | 0.836 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6326 | Pyrido-[2,3-d]-pyrimidin-7-one 60 | 0.824 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6302 | pyrido[2,3-d]pyrimidin-7-one 31 | 0.821 | IC50 | = | 230 | 6.64 | 2 | 15801831 | 2005 |
| 6310 | Pyrido-[2,3-d]-pyrimidin-7-one 44 | 0.817 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6319 | Pyrido-[2,3-d]-pyrimidin-7-one 53 | 0.817 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6320 | Pyrido-[2,3-d]-pyrimidin-7-one 54 | 0.797 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 757722 | pyridin-3-yl)-N-hydroxypiperidine-4-carboxamide | 0.789 | IC50 | > | 2000 | 5.7 | 1 | US12358911B2 | 2025 |
| 6322 | Pyrido-[2,3-d]-pyrimidin-7-one 56 | 0.786 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6327 | Pyrido-[2,3-d]-pyrimidin-7-one 61 | 0.783 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6307 | Pyrido-[2,3-d]-pyrimidin-7-one 41 | 0.779 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 50570698 | CHEMBL4850687 | 0.767 | IC50 | = | 7601 | 5.12 | 1 | 33857728 | 2021 |
| 6314 | Pyrido-[2,3-d]-pyrimidin-7-one 48 | 0.746 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6299 | Pyrido-[2,3-d]-pyrimidin-7-one 33 | 0.729 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6385 | pyrido[2,3-d]pyrimidin-7-one 32 | 0.729 | IC50 | > | 5000 | 5.3 | 1 | 15801830 | 2005 |
| 6304 | Pyrido-[2,3-d]-pyrimidin-7-one 38 | 0.7 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6386 | pyrido[2,3-d]pyrimidin-7-one 33 | 0.699 | IC50 | = | 2819 | 5.55 | 1 | 15801830 | 2005 |
| 6290 | Pyrido-[2,3-d]-pyrimidin-7-one 24 | 0.686 | IC50 | = | 4050 | 5.39 | 1 | 15801831 | 2005 |
| 6308 | Pyrido-[2,3-d]-pyrimidin-7-one 42 | 0.681 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6303 | pyrido[2,3-d]pyrimidin-7-one 34 | 0.671 | IC50 | > | 5000 | 5.3 | 2 | 15801831 | 2005 |
| 6315 | Pyrido-[2,3-d]-pyrimidin-7-one 49 | 0.662 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6316 | Pyrido-[2,3-d]-pyrimidin-7-one 50 | 0.658 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6300 | Pyrido-[2,3-d]-pyrimidin-7-one 34 | 0.649 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6291 | Pyrido-[2,3-d]-pyrimidin-7-one 25 | 0.644 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6313 | Pyrido-[2,3-d]-pyrimidin-7-one 47 | 0.644 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6288 | Pyrido-[2,3-d]-pyrimidin-7-one 22 | 0.639 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6289 | Pyrido-[2,3-d]-pyrimidin-7-one 23 | 0.639 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6287 | Pyrido-[2,3-d]-pyrimidin-7-one 17 | 0.639 | IC50 | = | 6050 | 5.22 | 1 | 15801831 | 2005 |
| 6318 | Pyrido-[2,3-d]-pyrimidin-7-one 52 | 0.636 | IC50 | = | 2050 | 5.69 | 1 | 15801831 | 2005 |
| 6379 | pyrido[2,3-d]pyrimidin-7-one 26 | 0.635 | IC50 | = | 1538 | 5.81 | 1 | 15801830 | 2005 |
| 6292 | Pyrido-[2,3-d]-pyrimidin-7-one 26 | 0.635 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6317 | Pyrido-[2,3-d]-pyrimidin-7-one 51 | 0.635 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6301 | pyrido[2,3-d]pyrimidin-7-one 29 | 0.63 | IC50 | = | 439 | 6.36 | 2 | 15801831 | 2005 |
| 6383 | pyrido[2,3-d]pyrimidin-7-one 30 | 0.63 | IC50 | = | 443 | 6.35 | 1 | 15801830 | 2005 |
| 6381 | pyrido[2,3-d]pyrimidin-7-one 28 | 0.63 | IC50 | = | 1625 | 5.79 | 1 | 15801830 | 2005 |
| 6380 | pyrido[2,3-d]pyrimidin-7-one 27 | 0.63 | IC50 | > | 5000 | 5.3 | 1 | 15801830 | 2005 |
| 6285 | Pyrido-[2,3-d]-pyrimidin-7-one 20 | 0.629 | IC50 | = | 2500 | 5.6 | 1 | 15801831 | 2005 |
| 6286 | Pyrido-[2,3-d]-pyrimidin-7-one 21 | 0.62 | IC50 | = | 835 | 6.08 | 1 | 15801831 | 2005 |
| 6312 | Pyrido-[2,3-d]-pyrimidin-7-one 46 | 0.613 | IC50 | > | 5000 | 5.3 | 1 | 15801831 | 2005 |
| 6293 | Pyrido-[2,3-d]-pyrimidin-7-one 27 | 0.61 | IC50 | = | 3800 | 5.42 | 1 | 15801831 | 2005 |
| 148264 | Kisqali | 0.605 | IC50 | = | 76000 | 4.12 | 2 | 30978559 | 2019 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "query": {
    "input": "CC1=C(C(=O)N(c2c1cnc(n2)Nc3ccc(cn3)N4CCNCC4)C5CCCC5)C(=O)C",
    "canonical": "CC(=O)c1c(C)c2cnc(Nc3ccc(N4CCNCC4)cn3)nc2n(C2CCCC2)c1=O",
    "threshold": 0.6,
    "fingerprint": "Morgan radius 2, 2048 bits, largest fragment"
  },
  "row_count": 44,
  "truncated": false,
  "rows": [
    {
      "ki_result_id": 51092107,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 230.0,
      "unit": "nM",
      "p_affinity": 6.64,
      "monomerid": 6309,
      "compound_name": "Ibrance",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1289040 (CHEMBL3118104)",
      "source_id": "24417566",
      "doi": "10.1021/jm401073p",
      "year": 2014,
      "n_measurements": 11,
      "similarity": 1.0
    },
    {
      "ki_result_id": 10271,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6323,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 57",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.954
    },
    {
      "ki_result_id": 10272,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6324,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 58",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.862
    },
    {
      "ki_result_id": 10269,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6321,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 55",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.836
    },
    {
      "ki_result_id": 10273,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6325,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 59",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.836
    },
    {
      "ki_result_id": 10274,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6326,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 60",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.824
    },
    {
      "ki_result_id": 10250,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 230.0,
      "unit": "nM",
      "p_affinity": 6.64,
      "monomerid": 6302,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 31",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 2,
      "similarity": 0.821
    },
    {
      "ki_result_id": 10258,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6310,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 44",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.817
    },
    {
      "ki_result_id": 10267,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6319,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 53",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.817
    },
    {
      "ki_result_id": 10268,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6320,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 54",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.797
    },
    {
      "ki_result_id": 397618,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 2000.0,
      "unit": "nM",
      "p_affinity": 5.7,
      "monomerid": 757722,
      "compound_name": "pyridin-3-yl)-N-hydroxypiperidine-4-carboxamide",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDK2, CDK4 and CDK6 Kinase Assays",
      "source_id": "US12358911B2",
      "doi": null,
      "year": 2025,
      "n_measurements": 1,
      "similarity": 0.789
    },
    {
      "ki_result_id": 10270,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6322,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 56",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.786
    },
    {
      "ki_result_id": 10275,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6327,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 61",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.783
    },
    {
      "ki_result_id": 10255,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6307,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 41",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.779
    },
    {
      "ki_result_id": 51412831,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 7601.0,
      "unit": "nM",
      "p_affinity": 5.12,
      "monomerid": 50570698,
      "compound_name": "CHEMBL4850687",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2112888 (CHEMBL4821738)",
      "source_id": "33857728",
      "doi": "10.1016/j.ejmech.2021.113432",
      "year": 2021,
      "n_measurements": 1,
      "similarity": 0.767
    },
    {
      "ki_result_id": 10262,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6314,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 48",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.746
    },
    {
      "ki_result_id": 10247,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6299,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 33",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.729
    },
    {
      "ki_result_id": 10469,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6385,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 32",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.729
    },
    {
      "ki_result_id": 10252,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6304,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 38",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.7
    },
    {
      "ki_result_id": 10470,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 2819.0,
      "unit": "nM",
      "p_affinity": 5.55,
      "monomerid": 6386,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 33",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.699
    },
    {
      "ki_result_id": 10238,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 4050.0,
      "unit": "nM",
      "p_affinity": 5.39,
      "monomerid": 6290,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 24",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.686
    },
    {
      "ki_result_id": 10256,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6308,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 42",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.681
    },
    {
      "ki_result_id": 10251,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6303,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 34",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 2,
      "similarity": 0.671
    },
    {
      "ki_result_id": 10263,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6315,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 49",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.662
    },
    {
      "ki_result_id": 10264,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6316,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 50",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.658
    },
    {
      "ki_result_id": 10248,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6300,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 34",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.649
    },
    {
      "ki_result_id": 10239,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6291,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 25",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.644
    },
    {
      "ki_result_id": 10261,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6313,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 47",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.644
    },
    {
      "ki_result_id": 10236,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6288,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 22",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.639
    },
    {
      "ki_result_id": 10237,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6289,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 23",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.639
    },
    {
      "ki_result_id": 10235,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 6050.0,
      "unit": "nM",
      "p_affinity": 5.22,
      "monomerid": 6287,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 17",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.639
    },
    {
      "ki_result_id": 10266,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 2050.0,
      "unit": "nM",
      "p_affinity": 5.69,
      "monomerid": 6318,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 52",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.636
    },
    {
      "ki_result_id": 10463,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 1538.0,
      "unit": "nM",
      "p_affinity": 5.81,
      "monomerid": 6379,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 26",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.635
    },
    {
      "ki_result_id": 10240,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6292,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 26",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.635
    },
    {
      "ki_result_id": 10265,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6317,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 51",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.635
    },
    {
      "ki_result_id": 10249,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 439.0,
      "unit": "nM",
      "p_affinity": 6.36,
      "monomerid": 6301,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 29",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 2,
      "similarity": 0.63
    },
    {
      "ki_result_id": 10467,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 443.0,
      "unit": "nM",
      "p_affinity": 6.35,
      "monomerid": 6383,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 30",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.63
    },
    {
      "ki_result_id": 10465,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 1625.0,
      "unit": "nM",
      "p_affinity": 5.79,
      "monomerid": 6381,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 28",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.63
    },
    {
      "ki_result_id": 10464,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6380,
      "compound_name": "pyrido[2,3-d]pyrimidin-7-one 27",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801830",
      "doi": "10.1021/jm049355+",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.63
    },
    {
      "ki_result_id": 10233,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 2500.0,
      "unit": "nM",
      "p_affinity": 5.6,
      "monomerid": 6285,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 20",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.629
    },
    {
      "ki_result_id": 10234,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 835.0,
      "unit": "nM",
      "p_affinity": 6.08,
      "monomerid": 6286,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 21",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.62
    },
    {
      "ki_result_id": 10260,
      "affinity_type": "IC50",
      "relation": ">",
      "value": 5000.0,
      "unit": "nM",
      "p_affinity": 5.3,
      "monomerid": 6312,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 46",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.613
    },
    {
      "ki_result_id": 10241,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 3800.0,
      "unit": "nM",
      "p_affinity": 5.42,
      "monomerid": 6293,
      "compound_name": "Pyrido-[2,3-d]-pyrimidin-7-one 27",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "CDKs Assay",
      "source_id": "15801831",
      "doi": "10.1021/jm049354h",
      "year": 2005,
      "n_measurements": 1,
      "similarity": 0.61
    },
    {
      "ki_result_id": 51252798,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 76000.0,
      "unit": "nM",
      "p_affinity": 4.12,
      "monomerid": 148264,
      "compound_name": "Kisqali",
      "polymerid": null,
      "complexid": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1848186 (CHEMBL4348727)",
      "source_id": "30978559",
      "doi": "10.1016/j.ejmech.2019.03.064",
      "year": 2019,
      "n_measurements": 2,
      "similarity": 0.605
    }
  ],
  "n_similar_compounds": 44,
  "compounds_searched": 3069,
  "search_set_size": 3069
}
```

</details>

<!-- results-sha256: 5e30c700830fc83ab920228419907c5355c2e6940b3296d37e1b2edf833fe0b0 -->

## Answer

**The query.** Palbociclib is BDBM6309 (listed as "Ibrance"). Its stored SMILES is the query, and
similarity is Tanimoto on Morgan fingerprints (radius 2, 2048 bits). At a threshold of 0.6, **137
compounds** are similar to it. Above 0.8 they are almost all from the series in which palbociclib was
discovered: "Pyrido-[2,3-d]-pyrimidin-7-one" compounds from the 2005 discovery paper (PMID 15801831)
and diazaspiro amines from patent US11225492. They keep the 6-acetyl-8-cyclopentyl-5-methyl core and
change the amine on the pyridine.

**The analogues bind CDK4 and CDK6.** 132 of the 137 analogues have at least one IC50 or Ki of 1 µM or
better, spread over 26 targets (step 3).
- **The top six rows are all CDK4 or CDK6:** CDK4/cyclin D1 (57 compounds, best pIC50 9.1), CDK6/cyclin
  D1 (50), the CDK4 L188C mutant complex (39), CDK4 alone (30), CDK6 alone (27) and CDK4/cyclin D3 (18).
- **CDK2 is weak.** The intact CDK2/cyclin A2 complex (target 97, the target of example 13) has only 5
  analogues at 1 µM or better, with a best pIC50 of 6.64. That matches palbociclib's design as a
  CDK4/6-selective inhibitor.

**Against CDK2/cyclin A2, most analogues are inactive (step 4).**
- **Inactive at the top concentration:** 44 analogues were measured on target 97. 29 of them are only
  `>` values (above 2–10 µM), meaning inactive at the highest concentration tested.
- **Measurable potency:** only five reach 1 µM or better: palbociclib (230 nM) and four
  pyridopyrimidinones from the 2005 papers. Those four include BDBM6302, palbociclib with a phenyl ring
  in place of the pyridine (230 nM).
- **One series:** 40 of the 44 come from the two 2005 papers (PMIDs 15801831 and 15801830). In effect,
  this is one selectivity screen.

**Why palbociclib shows 230 nM here but Ki > 5 µM in example 13:**
- **One row hides the spread.** The tool shows each compound's most potent measurement, while
  palbociclib has 11 on this complex (`n_measurements`). They range from IC50 230 nM to > 10 µM. The
  2005 discovery paper reports > 5 µM, and example 13 used the only Ki, > 5 µM (2017).
- **The 230 nM may belong to another compound.** It comes from two later papers (2014 and 2021). It is
  also exactly the value the 2005 paper gives for the phenyl analogue BDBM6302. That coincidence is
  worth checking before quoting 230 nM for palbociclib.

**Rows to treat with caution:**
- **Cyclin-A2 [177–432]/CDK2 (target 304).** It shows 13 analogues with best pIC50 8.0. All come from
  patent US11225492B2, reported as upper bounds ("< 10 nM", "< 25 nM") against a truncated cyclin A2
  construct. That contradicts the papers' > 5 µM for the same chemotype on the intact complex, so it is
  more likely a patent binning or assignment issue than real CDK2 potency.
- **HDAC1 and HDAC6.** These come from the same patent's hydroxamic acids, which have an
  N-hydroxyamide tail on the piperazine. Those are dual CDK4/6–HDAC designs, not off-target activity of
  palbociclib itself.
- **Mixed affinity types.** The table mixes IC50 and Ki values, and several rows are mutants (CDK4 L188C)
  or single proteins rather than complexes. The note in example 14 about counting one protein under
  several targets applies here too.
