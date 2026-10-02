# Provenance of a single measurement

> **Question:** What is the most potent BTK inhibitor by IC50, and where does that number come from?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `find_ligands_for_target`

```json
{"target_id": 1846, "affinity_types": ["IC50"], "limit": 3}
```

**Result:**

_3 row(s), more available (truncated by limit) — table shows selected columns._

| ki_result_id | monomerid | compound_name | relation | value | unit | assay_name | source_id | year |
|---|---|---|---|---|---|---|---|---|
| 536982 | 281761 | 4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-6-chloro-3-fluo... | = | 0.00026 | nM | Human Recombinant Btk Enzyme Assay | US10023534B2 | 2018 |
| 536983 | 281762 | 4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-3-fluoro-9H- ca... | = | 0.0003 | nM | Human Recombinant Btk Enzyme Assay | US10023534B2 | 2018 |
| 536984 | 281763 | 9-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-8-fluoro-5H- py... | = | 0.0003 | nM | Human Recombinant Btk Enzyme Assay | US10023534B2 | 2018 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 3,
  "truncated": true,
  "rows": [
    {
      "ki_result_id": 536982,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.00026,
      "unit": "nM",
      "p_affinity": 12.59,
      "monomerid": 281761,
      "compound_name": "4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-6-chloro-3-fluoro- 9H-carbazole-1- carboxamide",
      "polymerid": 1846,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase BTK",
      "uniprot_raw": "Q06187",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Human Recombinant Btk Enzyme Assay",
      "source_id": "US10023534B2",
      "doi": null,
      "year": 2018,
      "n_measurements": 1
    },
    {
      "ki_result_id": 536983,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.0003,
      "unit": "nM",
      "p_affinity": 12.52,
      "monomerid": 281762,
      "compound_name": "4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-3-fluoro-9H- carbazole-1- carboxamide",
      "polymerid": 1846,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase BTK",
      "uniprot_raw": "Q06187",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Human Recombinant Btk Enzyme Assay",
      "source_id": "US10023534B2",
      "doi": null,
      "year": 2018,
      "n_measurements": 1
    },
    {
      "ki_result_id": 536984,
      "affinity_type": "IC50",
      "relation": "=",
      "value": 0.0003,
      "unit": "nM",
      "p_affinity": 12.52,
      "monomerid": 281763,
      "compound_name": "9-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-8-fluoro-5H- pyrido[4,3-b]indole-6- carboxamide",
      "polymerid": 1846,
      "complexid": null,
      "target_name": "Tyrosine-protein kinase BTK",
      "uniprot_raw": "Q06187",
      "organism": "Homo sapiens",
      "ph": 7.4,
      "temp_k": 298.15,
      "assay_name": "Human Recombinant Btk Enzyme Assay",
      "source_id": "US10023534B2",
      "doi": null,
      "year": 2018,
      "n_measurements": 1
    }
  ]
}
```

</details>

### 2. `get_activity`

```json
{"ki_result_id": 536982}
```

**Result:**

**measurement**

| field | value |
|---|---|
| ic50 |  0.00026 |
| ki_result_id | 536982 |
| reactant_set_id | 536984 |
| temp | 298.15 |
| comments | extracted |
| assayid | 1 |
| entryid | 610 |
| ph | 7.4 |

**reactants**

| field | value |
|---|---|
| target_label | Tyrosine-protein kinase BTK |
| ligand_label | BDBM281761 |
| substrate | to-be-curated |
| e_prep |  |
| i_prep |  |
| s_prep |  |
| monomerid | 281761 |
| compound_name | 4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-6-chloro-3-fluo... |
| inchi_key | PRKMJLHNBXYDTM-UHFFFAOYSA-N |
| polymerid | 1846 |
| complexid |  |
| target_name | Tyrosine-protein kinase BTK |
| uniprot_raw | Q06187 |
| organism | Homo sapiens |

**assay**

| field | value |
|---|---|
| assay_name | Human Recombinant Btk Enzyme Assay |
| description | To V-bottom 384-well plates were added test compounds, human recomb... |

**entry**

| field | value |
|---|---|
| entryid | 610 |
| entrytitle | Carbazole and tetrahydrocarbazole compounds useful as inhibitors of... |
| meas_tech | Enzyme Inhibition |
| entrydate | 2018-12-31T00:00:00 |
| ezid | 10.7270/Q2WW7KQR |

**citations**

| articleid | art_purp | title | journal | year | volume | firstpage | source_id | doi | authors |
|---|---|---|---|---|---|---|---|---|---|
| 7043 | header5body5-20180717 | Carbazole and tetrahydrocarbazole compounds useful as inhibitors of... | US Patent | 2018 | 2018 |  | US10023534B2 |  | SH Watterson, AJ Tebben, S Ahmad |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "measurement": {
    "ic50": " 0.00026",
    "ki_result_id": 536982,
    "reactant_set_id": 536984,
    "temp": 298.15,
    "comments": "extracted",
    "assayid": 1,
    "entryid": 610,
    "ph": 7.4
  },
  "reactants": {
    "target_label": "Tyrosine-protein kinase BTK",
    "ligand_label": "BDBM281761",
    "substrate": "to-be-curated",
    "e_prep": null,
    "i_prep": null,
    "s_prep": null,
    "monomerid": 281761,
    "compound_name": "4-(2-acryloyl-1,2,3,4- tetrahydroisoquinolin- 5-yl)-6-chloro-3-fluoro- 9H-carbazole-1- carboxamide",
    "inchi_key": "PRKMJLHNBXYDTM-UHFFFAOYSA-N",
    "polymerid": 1846,
    "complexid": null,
    "target_name": "Tyrosine-protein kinase BTK",
    "uniprot_raw": "Q06187",
    "organism": "Homo sapiens"
  },
  "assay": {
    "assay_name": "Human Recombinant Btk Enzyme Assay",
    "description": "To V-bottom 384-well plates were added test compounds, human recombinant Btk (1 nM, Invitrogen Corporation), fluoresceinated peptide (1.5 &#956;M), ATP (20 &#956;M), and assay buffer (20 mM HEPES pH 7.4, 10 mM MgCl2, 0.015% Brij 35 surfactant and 4 mM DTT in 1.6% DMSO), with a final volume of 30 &#956;L. After incubating at room temperature for 60 min, the reaction was terminated by adding 45 &#956;L of 35 mM EDTA to each sample. The reaction mixture was analyzed on the Caliper LABCHIP 3000 (Caliper, Hopkinton, Mass.) by electrophoretic separation of the fluorescent substrate and phosphorylated product. Inhibition data were calculated by comparison to no enzyme control reactions for 100% inhibition and no inhibitor controls for 0% inhibition. Dose response curves were generated to determine the concentration required for inhibiting 50% of kinase activity (IC50). Compounds were dissolved at 10 mM in DMSO and evaluated at eleven concentrations."
  },
  "entry": {
    "entryid": 610,
    "entrytitle": "Carbazole and tetrahydrocarbazole compounds useful as inhibitors of BTK",
    "meas_tech": "Enzyme Inhibition",
    "entrydate": "2018-12-31T00:00:00",
    "ezid": "10.7270/Q2WW7KQR"
  },
  "citations": [
    {
      "articleid": 7043,
      "art_purp": "header5body5-20180717",
      "title": "Carbazole and tetrahydrocarbazole compounds useful as inhibitors of BTK",
      "journal": "US Patent",
      "year": 2018,
      "volume": 2018,
      "firstpage": null,
      "source_id": "US10023534B2",
      "doi": null,
      "authors": "SH Watterson, AJ Tebben, S Ahmad"
    }
  ]
}
```

</details>

<!-- results-sha256: c21d941ec68856c01dddc2d0ae7b2e0e8c91aeb4e0ef5f760f5cbb0df7783d3b -->

## Answer

The most potent BTK IC50 in BindingDB is **0.00026 nM (0.26 pM)** for **BDBM281761**, an
acrylamide-bearing tetrahydroisoquinolinyl-carbazole carboxamide.

**Where the number comes from:**
- **Source:** patent **US10023534B2** (2018), *"Carbazole and tetrahydrocarbazole compounds useful as inhibitors of..."* by Watterson, Tebben, Ahmad *et al.* BindingDB entry 610 (DOI-style id 10.7270/Q2WW7KQR).
- **Assay:** "Human Recombinant Btk Enzyme Assay". Recombinant human BTK at **1 nM**, a fluoresceinated peptide (1.5 µM) and ATP (20 µM) at pH 7.4 and room temperature (298 K) for 60 min. The phosphorylated product was read on a Caliper LabChip 3000, and dose responses used 11 concentrations.

**Sanity check:** a measured IC50 normally can't go much below half the enzyme concentration (0.5 nM
here), because of the tight-binding limit. A value of 0.26 pM is about 2,000 times lower. The compound is
also an acrylamide, so it probably binds covalently, and IC50 then depends on incubation time. Treat this
number as "more potent than the assay can resolve", not as a real equilibrium constant. The two runners-up
from the same patent (0.0003 nM) have the same problem.
