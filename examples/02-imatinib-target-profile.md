# Imatinib target profile

> **Question:** Which targets does imatinib bind with an affinity better than 100 nM?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_compounds`

```json
{"query": "imatinib", "limit": 3}
```

**Result:**

_3 row(s) — table shows selected columns._

| monomerid | bdbm_id | name | inchi_key | n_activities | n_targets | matched_name |
|---|---|---|---|---|---|---|
| 13530 | BDBM13530 | Gleevec | KTUFNOKKBVMGRW-UHFFFAOYSA-N | 1156 | 459 | Imatinib |
| 31341 | BDBM31341 | IMATINIB |  | 0 | 0 | IMATINIB |
| 50434581 | BDBM50434581 | imatinib-CD3 | KTUFNOKKBVMGRW-BMSJAHLVSA-N | 2 | 2 | imatinib-CD3 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 3,
  "truncated": false,
  "rows": [
    {
      "monomerid": 13530,
      "bdbm_id": "BDBM13530",
      "name": "Gleevec",
      "inchi_key": "KTUFNOKKBVMGRW-UHFFFAOYSA-N",
      "smiles": "CN1CCN(Cc2ccc(cc2)C(=O)Nc2ccc(C)c(Nc3nccc(n3)-c3cccnc3)c2)CC1",
      "mol_weight": 493.26,
      "n_activities": 1156,
      "n_targets": 459,
      "matched_name": "Imatinib"
    },
    {
      "monomerid": 31341,
      "bdbm_id": "BDBM31341",
      "name": "IMATINIB",
      "inchi_key": null,
      "smiles": "Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C",
      "mol_weight": null,
      "n_activities": 0,
      "n_targets": 0,
      "matched_name": "IMATINIB"
    },
    {
      "monomerid": 50434581,
      "bdbm_id": "BDBM50434581",
      "name": "imatinib-CD3",
      "inchi_key": "KTUFNOKKBVMGRW-BMSJAHLVSA-N",
      "smiles": "[2H]C([2H])([2H])N5CCN(Cc4ccc(C(=O)Nc3ccc(C)c(Nc2nccc(c1cccnc1)n2)c3)cc4)CC5",
      "mol_weight": 496.58,
      "n_activities": 2,
      "n_targets": 2,
      "matched_name": "imatinib-CD3"
    }
  ]
}
```

</details>

### 2. `find_targets_for_compound`

```json
{"monomerid": 13530, "max_value_nm": 100, "limit": 25}
```

**Result:**

_25 row(s), more available (truncated by limit) — table shows selected columns._

| target_name | uniprot_raw | organism | affinity_type | relation | value | p_affinity | n_measurements |
|---|---|---|---|---|---|---|---|
| Receptor tyrosine-protein kinase erbB-2 | P04626 | Homo sapiens | IC50 | = | 0.06 | 10.22 | 1 |
| Epidermal growth factor receptor | P00533 | Homo sapiens | IC50 | = | 0.11 | 9.96 | 1 |
| Epithelial discoidin domain-containing receptor 1 | Q08345 | Homo sapiens | Kd | = | 0.7 | 9.15 | 6 |
| Tyrosine-protein kinase ABL1 | P00519 | Homo sapiens | Kd | = | 1 | 9 | 38 |
| Breakpoint cluster region protein/Tyrosine-protein kinase ABL1 |  |  | IC50 | = | 1.1 | 8.96 | 19 |
| Tyrosine-protein kinase ABL1 [229-512] | P00519[229-512] | Homo sapiens | Kd | = | 1.5 | 8.82 | 2 |
| Tyrosine-protein kinase ABL1 [201-500] | P00519[201-500] | Homo sapiens | Kd | = | 2 | 8.7 | 1 |
| Platelet-derived growth factor receptor alpha | P16234 | Homo sapiens | Ki | = | 2 | 8.7 | 13 |
| Mast/stem cell growth factor receptor Kit [N822K] | P10721[N822K] | Homo sapiens | Kd | = | 3 | 8.52 | 1 |
| Platelet-derived growth factor receptor beta | P09619 | Homo sapiens | Ki | = | 3 | 8.52 | 6 |
| Tyrosine-protein kinase ABL1 [201-500,M351T] | P00519[201-500,M351T] | Homo sapiens | Kd | = | 10 | 8 | 1 |
| Tyrosine-protein kinase ABL2 | P42684 | Homo sapiens | Kd | = | 10 | 8 | 6 |
| Macrophage colony-stimulating factor 1 receptor | P07333 | Homo sapiens | Kd | = | 10 | 8 | 4 |
| Tyrosine-protein kinase ABL1 | P00520 | Mus musculus | IC50 | = | 10.8 | 7.97 | 1 |
| Mast/stem cell growth factor receptor Kit | P10721 | Homo sapiens | Kd | = | 13 | 7.89 | 27 |
| Discoidin domain-containing receptor 2 [A642S] | Q16832[A642S] | Homo sapiens | Kd | = | 15 | 7.82 | 1 |
| Discoidin domain-containing receptor 2 | Q16832 | Homo sapiens | Kd | = | 15 | 7.82 | 2 |
| Tyrosine-protein kinase ABL1 [201-500,Q252H] | P00519[201-500,Q252H] | Homo sapiens | Kd | = | 20 | 7.7 | 1 |
| Tyrosine-protein kinase ABL1 [201-500,F359V] | P00519[201-500,F359V] | Homo sapiens | Kd | = | 20 | 7.7 | 1 |
| Mast/stem cell growth factor receptor Kit [V559D] | P10721[V559D] | Homo sapiens | Kd | = | 20 | 7.7 | 1 |
| Tyrosine-protein kinase ABL1 [1-999,Q252H] | P00519[1-999,Q252H] | Homo sapiens | IC50 | = | 27 | 7.57 | 1 |
| Carbonic anhydrase 2 | P00918 | Homo sapiens | Ki | = | 30.2 | 7.52 | 1 |
| Carbonic anhydrase 1 | P00915 | Homo sapiens | Ki | = | 31.9 | 7.5 | 1 |
| Breakpoint cluster region protein | Q6PAJ1 | Mus musculus | IC50 | = | 38 | 7.42 | 1 |
| Ribosyldihydronicotinamide dehydrogenase [quinone] | P16083 | Homo sapiens | Ki | = | 39 | 7.41 | 3 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 25,
  "truncated": true,
  "rows": [
    {
      "ki_result_id": 51506159,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.06,
      "unit": "nM",
      "p_affinity": 10.22,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 188,
      "complexid": null,
      "target_name": "Receptor tyrosine-protein kinase erbB-2",
      "uniprot_raw": "P04626",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2261296 (CHEMBL5216307)",
      "source_id": "35696863",
      "doi": "10.1016/j.ejmech.2022.114502",
      "year": 2022,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51506157,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.11,
      "unit": "nM",
      "p_affinity": 9.96,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 520,
      "complexid": null,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2261295 (CHEMBL5216306)",
      "source_id": "35696863",
      "doi": "10.1016/j.ejmech.2022.114502",
      "year": 2022,
      "n_measurements": 1
    },
    {
      "ki_result_id": 58107,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 0.7,
      "unit": "nM",
      "p_affinity": 9.15,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 3993,
      "complexid": null,
      "target_name": "Epithelial discoidin domain-containing receptor 1",
      "uniprot_raw": "Q08345",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Inhibitor Selectivity Profiling Assay",
      "source_id": "aid1433",
      "doi": null,
      "year": 2008,
      "n_measurements": 6
    },
    {
      "ki_result_id": 51232598,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 1.0,
      "unit": "nM",
      "p_affinity": 9.0,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 5221,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1",
      "uniprot_raw": "P00519",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1821228 (CHEMBL4320888)",
      "source_id": "30807144",
      "doi": "10.1021/acs.jmedchem.8b01925",
      "year": 2019,
      "n_measurements": 38
    },
    {
      "ki_result_id": 50160997,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 1.1,
      "unit": "nM",
      "p_affinity": 8.96,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": null,
      "complexid": 261,
      "target_name": "Breakpoint cluster region protein/Tyrosine-protein kinase ABL1",
      "uniprot_raw": null,
      "organism": null,
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_614493 (CHEMBL1110561)",
      "source_id": "20166671",
      "doi": "10.1021/jm901132v",
      "year": 2010,
      "n_measurements": 19
    },
    {
      "ki_result_id": 334877,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 1.5,
      "unit": "nM",
      "p_affinity": 8.82,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 7838,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [229-512]",
      "uniprot_raw": "P00519[229-512]",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "Kinome-Wide Inhibitor Profiling",
      "source_id": "26895387",
      "doi": "10.1021/acschembio.5b01018",
      "year": 2016,
      "n_measurements": 2
    },
    {
      "ki_result_id": 24176,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 2.0,
      "unit": "nM",
      "p_affinity": 8.7,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1385,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [201-500]",
      "uniprot_raw": "P00519[201-500]",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 189434,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 2.0,
      "unit": "nM",
      "p_affinity": 8.7,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 5778,
      "complexid": null,
      "target_name": "Platelet-derived growth factor receptor alpha",
      "uniprot_raw": "P16234",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": null,
      "source_id": "16492761",
      "doi": "10.1073/pnas.0511292103",
      "year": 2006,
      "n_measurements": 13
    },
    {
      "ki_result_id": 24191,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 3.0,
      "unit": "nM",
      "p_affinity": 8.52,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1394,
      "complexid": null,
      "target_name": "Mast/stem cell growth factor receptor Kit [N822K]",
      "uniprot_raw": "P10721[N822K]",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 189436,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 3.0,
      "unit": "nM",
      "p_affinity": 8.52,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 575,
      "complexid": null,
      "target_name": "Platelet-derived growth factor receptor beta",
      "uniprot_raw": "P09619",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": null,
      "source_id": "16492761",
      "doi": "10.1073/pnas.0511292103",
      "year": 2006,
      "n_measurements": 6
    },
    {
      "ki_result_id": 24180,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 10.0,
      "unit": "nM",
      "p_affinity": 8.0,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1389,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [201-500,M351T]",
      "uniprot_raw": "P00519[201-500,M351T]",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 65729,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 10.0,
      "unit": "nM",
      "p_affinity": 8.0,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 50001306,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL2",
      "uniprot_raw": "P42684",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "Kinase Inhibitor Selectivity Profiling Assay",
      "source_id": "aid1433",
      "doi": null,
      "year": 2008,
      "n_measurements": 6
    },
    {
      "ki_result_id": 51232593,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 10.0,
      "unit": "nM",
      "p_affinity": 8.0,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 879,
      "complexid": null,
      "target_name": "Macrophage colony-stimulating factor 1 receptor",
      "uniprot_raw": "P07333",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1821226 (CHEMBL4320886)",
      "source_id": "30807144",
      "doi": "10.1021/acs.jmedchem.8b01925",
      "year": 2019,
      "n_measurements": 4
    },
    {
      "ki_result_id": 50589673,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 10.8,
      "unit": "nM",
      "p_affinity": 7.97,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 50001750,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1",
      "uniprot_raw": "P00520",
      "organism": "Mus musculus",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_647651 (CHEMBL1220002)",
      "source_id": "20621496",
      "doi": "10.1016/j.bmc.2010.05.063",
      "year": 2010,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50195818,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 13.0,
      "unit": "nM",
      "p_affinity": 7.89,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 359,
      "complexid": null,
      "target_name": "Mast/stem cell growth factor receptor Kit",
      "uniprot_raw": "P10721",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_774266 (CHEMBL1908483)",
      "source_id": "22037378",
      "doi": "10.1038/nbt.1990",
      "year": 2011,
      "n_measurements": 27
    },
    {
      "ki_result_id": 58126,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 15.0,
      "unit": "nM",
      "p_affinity": 7.82,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 3995,
      "complexid": null,
      "target_name": "Discoidin domain-containing receptor 2 [A642S]",
      "uniprot_raw": "Q16832[A642S]",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Inhibitor Selectivity Profiling Assay",
      "source_id": "aid1433",
      "doi": null,
      "year": 2008,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50673776,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 15.0,
      "unit": "nM",
      "p_affinity": 7.82,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 5709,
      "complexid": null,
      "target_name": "Discoidin domain-containing receptor 2",
      "uniprot_raw": "Q16832",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_774257 (CHEMBL1908474)",
      "source_id": "22037378",
      "doi": "10.1038/nbt.1990",
      "year": 2011,
      "n_measurements": 2
    },
    {
      "ki_result_id": 24177,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 20.0,
      "unit": "nM",
      "p_affinity": 7.7,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1386,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [201-500,Q252H]",
      "uniprot_raw": "P00519[201-500,Q252H]",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 24181,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 20.0,
      "unit": "nM",
      "p_affinity": 7.7,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1390,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [201-500,F359V]",
      "uniprot_raw": "P00519[201-500,F359V]",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 24192,
      "affinity_type": "Kd",
      "relation": "=",
      "value": 20.0,
      "unit": "nM",
      "p_affinity": 7.7,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1395,
      "complexid": null,
      "target_name": "Mast/stem cell growth factor receptor Kit [V559D]",
      "uniprot_raw": "P10721[V559D]",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "Kinase Assay and Binding Constant Measurement",
      "source_id": "16046538",
      "doi": "10.1073/pnas.0504952102",
      "year": 2005,
      "n_measurements": 1
    },
    {
      "ki_result_id": 126580,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 27.0,
      "unit": "nM",
      "p_affinity": 7.57,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 4453,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase ABL1 [1-999,Q252H]",
      "uniprot_raw": "P00519[1-999,Q252H]",
      "organism": "Homo sapiens",
      "ph": 7.5,
      "temp_k": null,
      "assay_name": "Biochemcial Assay ",
      "source_id": "16873026",
      "doi": "10.1016/j.chembiol.2006.05.015",
      "year": 2006,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50513152,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 30.2,
      "unit": "nM",
      "p_affinity": 7.52,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1193,
      "complexid": null,
      "target_name": "Carbonic anhydrase 2",
      "uniprot_raw": "P00918",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_579711 (CHEMBL1053952)",
      "source_id": "19527930",
      "doi": "10.1016/j.bmcl.2009.06.002",
      "year": 2009,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50513151,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 31.9,
      "unit": "nM",
      "p_affinity": 7.5,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 1192,
      "complexid": null,
      "target_name": "Carbonic anhydrase 1",
      "uniprot_raw": "P00915",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_579710 (CHEMBL1053951)",
      "source_id": "19527930",
      "doi": "10.1016/j.bmcl.2009.06.002",
      "year": 2009,
      "n_measurements": 1
    },
    {
      "ki_result_id": 51519669,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 38.0,
      "unit": "nM",
      "p_affinity": 7.42,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 50001198,
      "complexid": null,
      "target_name": "Breakpoint cluster region protein",
      "uniprot_raw": "Q6PAJ1",
      "organism": "Mus musculus",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_2284540",
      "source_id": "30243589",
      "doi": "10.1016/j.bmcl.2018.09.016",
      "year": 2018,
      "n_measurements": 1
    },
    {
      "ki_result_id": 50552519,
      "affinity_type": "Ki",
      "relation": "=",
      "value": 39.0,
      "unit": "nM",
      "p_affinity": 7.41,
      "monomerid": 13530,
      "compound_name": "Gleevec",
      "polymerid": 5286,
      "complexid": null,
      "target_name": "Ribosyldihydronicotinamide dehydrogenase [quinone]",
      "uniprot_raw": "P16083",
      "organism": "Homo sapiens",
      "ph": null,
      "temp_k": null,
      "assay_name": "ChEMBL_1634419 (CHEMBL3877211)",
      "source_id": "28280261",
      "doi": "10.1038/nrd.2016.266",
      "year": 2017,
      "n_measurements": 3
    }
  ]
}
```

</details>

<!-- results-sha256: 700d7b5896c744702a879aa2c1bbe5f13bd8b9e09f18afd0f02ec78f7ebbef78 -->

## Answer

Imatinib is **BDBM13530** (preferred name "Gleevec"), with 1,156 measurements against 459 targets.

Most of the results match imatinib's known pharmacology:
- **ABL1:** Kd 1 nM, best of 38 measurements. Several ABL1 kinase-domain constructs and resistance mutants (M351T, Q252H, F359V) fall between 1.5 and 27 nM.
- **BCR-ABL:** IC50 1.1 nM, from 19 measurements.
- **PDGFRα/β:** Ki 2–3 nM.
- **KIT:** Kd 13 nM over 27 measurements; the N822K and V559D mutants are 3–20 nM.
- **DDR1** (Kd 0.7 nM), **DDR2**, **CSF1R** and **ABL2**.
- Outside the kinases: **NQO2** (ribosyldihydronicotinamide dehydrogenase, Ki 39 nM) and **carbonic anhydrases I/II** (Ki about 30 nM).

**Caution:** the two top rows, **ERBB2 (IC50 0.06 nM)** and **EGFR (IC50 0.11 nM)**, are each a single
measurement. Imatinib is not known as an EGFR or HER2 inhibitor, so these are probably errors in the
source or the curation. Check `n_measurements` before trusting a value, and inspect suspicious rows with
`get_activity`.
