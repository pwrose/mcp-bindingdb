# Target profile of a chemotype

> **Question:** Which proteins bind compounds containing the 4-(thiazol-5-yl)-2-aminopyrimidine chemotype (the largest chemotype in example 13), and how many compounds bind each protein?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-03

## Tool calls

### 1. `substructure_search`

```json
{"query": "s1cncc1-c1ccnc([#7])n1", "limit": 5}
```

**Result:**

**query:** input: `s1cncc1-c1ccnc([#7])n1`, interpreted_as: smarts, canonical: `s1cncc1-c1ccnc([#7])n1`

**compounds_searched:** 100000

**search_set_size:** 1464874

_5 row(s), more available (truncated by limit) — table shows selected columns._

| monomerid | name | smiles | n_activities | n_targets |
|---|---|---|---|---|
| 50277583 | CYC-116 | Cc1nc(N)sc1-c1ccnc(Nc2ccc(cc2)N2CCOCC2)n1 | 41 | 31 |
| 50428286 | DABRAFENIB | CC(C)(C)c1nc(c(s1)c2ccnc(n2)N)c3cccc(c3F)NS(=O)(=O)c4c(cccc4F)F | 39 | 11 |
| 50530637 | CHEMBL4591417 | Cc1cc(Nc2nccc(n2)-c2sc(nc2-c2ccc(F)cc2)C2CCNCC2)ccn1 | 34 | 14 |
| 50229973 | 4-methyl-5-(2-(3-nitrophenylamino)pyrimidin-4-yl)thiazol-2-amine | Cc1nc(N)sc1-c1ccnc(Nc2cccc(c2)[N+]([O-])=O)n1 | 22 | 17 |
| 50425008 | CHEMBL2312185 | CNc1nc(C)c(s1)-c1nc(Nc2cccc(c2)N2CCCNCC2)ncc1C#N | 17 | 15 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "query": {
    "input": "s1cncc1-c1ccnc([#7])n1",
    "interpreted_as": "smarts",
    "canonical": "s1cncc1-c1ccnc([#7])n1"
  },
  "row_count": 5,
  "truncated": true,
  "rows": [
    {
      "monomerid": 50277583,
      "bdbm_id": "BDBM50277583",
      "name": "CYC-116",
      "smiles": "Cc1nc(N)sc1-c1ccnc(Nc2ccc(cc2)N2CCOCC2)n1",
      "mol_weight": 368.456,
      "n_activities": 41,
      "n_targets": 31
    },
    {
      "monomerid": 50428286,
      "bdbm_id": "BDBM50428286",
      "name": "DABRAFENIB",
      "smiles": "CC(C)(C)c1nc(c(s1)c2ccnc(n2)N)c3cccc(c3F)NS(=O)(=O)c4c(cccc4F)F",
      "mol_weight": 519.56,
      "n_activities": 39,
      "n_targets": 11
    },
    {
      "monomerid": 50530637,
      "bdbm_id": "BDBM50530637",
      "name": "CHEMBL4591417",
      "smiles": "Cc1cc(Nc2nccc(n2)-c2sc(nc2-c2ccc(F)cc2)C2CCNCC2)ccn1",
      "mol_weight": 446.56,
      "n_activities": 34,
      "n_targets": 14
    },
    {
      "monomerid": 50229973,
      "bdbm_id": "BDBM50229973",
      "name": "4-methyl-5-(2-(3-nitrophenylamino)pyrimidin-4-yl)thiazol-2-amine",
      "smiles": "Cc1nc(N)sc1-c1ccnc(Nc2cccc(c2)[N+]([O-])=O)n1",
      "mol_weight": 328.07,
      "n_activities": 22,
      "n_targets": 17
    },
    {
      "monomerid": 50425008,
      "bdbm_id": "BDBM50425008",
      "name": "CHEMBL2312185",
      "smiles": "CNc1nc(C)c(s1)-c1nc(Nc2cccc(c2)N2CCCNCC2)ncc1C#N",
      "mol_weight": 420.53,
      "n_activities": 17,
      "n_targets": 15
    }
  ],
  "compounds_searched": 100000,
  "search_set_size": 1464874
}
```

</details>

### 2. `substructure_search`

```json
{"query": "s1cncc1-c1ccnc([#7])n1", "summarize_by_target": true, "max_value_nm": 10000, "limit": 500}
```

**Result:**

**query:** input: `s1cncc1-c1ccnc([#7])n1`, interpreted_as: smarts, canonical: `s1cncc1-c1ccnc([#7])n1`

**n_matching_compounds:** 549

**n_targets:** 86

**n_compounds_measured:** 529

**compounds_searched:** 1464874

**search_set_size:** 1464874

_86 row(s) — table shows selected columns._

| target_kind | target_id | target_name | uniprot_raw | organism | n_compounds | n_measurements | affinity_types | best_p_affinity |
|---|---|---|---|---|---|---|---|---|
| polymer | 2869 | Tyrosine-protein kinase CSK | P41240 | Homo sapiens | 149 | 149 | IC50 | 8.57 |
| complex | 113 | Cyclin-T1/Cyclin-dependent kinase 9 |  |  | 131 | 139 | IC50, Ki | 9.4 |
| complex | 97 | Cyclin-A2/Cyclin-dependent kinase 2 |  |  | 93 | 93 | IC50, Kd, Ki | 8.52 |
| complex | 112 | Cyclin-H/Cyclin-dependent kinase 7 |  |  | 92 | 93 | IC50, Ki | 7.62 |
| complex | 95 | Cyclin-dependent kinase/G2/mitotic-specific cyclin- 1 |  |  | 88 | 88 | IC50, Ki | 9.3 |
| complex | 93 | Cyclin-dependent kinase 4/G1/S-specific cyclin-D1 |  |  | 56 | 56 | IC50, Ki | 9 |
| polymer | 50006193 | cGMP-dependent protein kinase |  | Plasmodium falciparum | 43 | 76 | IC50 | 9.52 |
| polymer | 796 | Cyclin-dependent kinase 2 | P24941 | Homo sapiens | 38 | 67 | IC50, Kd, Ki | 9.96 |
| complex | 50000025 | Cyclin-A1/Cyclin-A2/Cyclin-dependent kinase 2 |  |  | 38 | 41 | IC50, Ki | 9.7 |
| polymer | 520 | Epidermal growth factor receptor | P00533 | Homo sapiens | 38 | 58 | IC50 | 9.05 |
| complex | 311 | Cyclin-dependent kinase 6/G1/S-specific cyclin-D3 |  |  | 36 | 36 | Ki | 8.7 |
| polymer | 507 | Tyrosine-protein kinase Lck | P06239 | Homo sapiens | 35 | 35 | IC50, Ki | 8 |
| polymer | 997 | Cyclin-dependent kinase 9 | P50750 | Homo sapiens | 30 | 30 | IC50, Ki | 9.54 |
| complex | 81 | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1 |  |  | 29 | 31 | IC50, Ki | 8.7 |
| polymer | 995 | Cyclin-dependent kinase 7 | P50613 | Homo sapiens | 26 | 27 | IC50, Ki | 9.25 |
| polymer | 799 | Cyclin-dependent kinase 4 | P11802 | Homo sapiens | 26 | 27 | Ki | 8.7 |
| polymer | 804 | Cyclin-dependent kinase 1 | P06493 | Homo sapiens | 23 | 24 | IC50, Ki | 8.52 |
| polymer | 1325 | Aurora kinase A | O14965 | Homo sapiens | 16 | 18 | IC50, Ki | 9.4 |
| polymer | 2857 | Serine/threonine-protein kinase B-raf | P15056 | Homo sapiens | 15 | 40 | EC50, IC50 | 9.4 |
| polymer | 4981 | Aurora kinase B | Q96GD4 | Homo sapiens | 15 | 17 | IC50, Ki | 8.7 |
| polymer | 5506 | MAP kinase-interacting serine/threonine-protein kinase 2 | Q9HBH9 | Homo sapiens | 14 | 15 | IC50, Ki | 6.96 |
| polymer | 3881 | Mitogen-activated protein kinase 14 | Q16539 | Homo sapiens | 12 | 12 | IC50, Kd | 8.7 |
| polymer | 5923 | Serine/threonine-protein kinase/endoribonuclease IRE1 | O75460 | Homo sapiens | 12 | 12 | IC50 | 8 |
| polymer | 50003140 | Wee1-like protein kinase | P30291 | Homo sapiens | 11 | 11 | IC50 | 8.74 |
| polymer | 1358 | Receptor-type tyrosine-protein kinase FLT3 | P36888 | Homo sapiens | 10 | 12 | IC50, Ki | 8.3 |
| polymer | 800 | G1/S-specific cyclin-D1 | P24385 | Homo sapiens | 10 | 10 | IC50 | 8.15 |
| polymer | 802 | G1/S-specific cyclin-E1 | P24864 | Homo sapiens | 10 | 10 | IC50 | 6.66 |
| polymer | 2132 | Potassium voltage-gated channel subfamily H member 2 | Q12809 | Homo sapiens | 9 | 18 | IC50 | 6.22 |
| polymer | 1622 | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit al... | P42336 | Homo sapiens | 7 | 8 | IC50 | 8.12 |
| polymer | 916 | Ketohexokinase | P50053 | Homo sapiens | 6 | 6 | IC50 | 8.62 |
| polymer | 808 | Angiopoietin-1 receptor | Q02763 | Homo sapiens | 6 | 6 | Kd | 8.47 |
| polymer | 932 | Isoform A of Ketohexokinase (Peripheral) | P50053-2 | Homo sapiens | 6 | 6 | IC50 | 7.87 |
| polymer | 9683 | Nuclear receptor subfamily 1 group I member 2 | O75469 | Homo sapiens | 6 | 8 | EC50 | 7.09 |
| polymer | 692 | Vascular endothelial growth factor receptor 2 | P35968 | Homo sapiens | 4 | 5 | IC50, Kd, Ki | 7.36 |
| polymer | 3672 | MAP kinase-interacting serine/threonine-protein kinase 1 | Q9BUB5 | Homo sapiens | 4 | 4 | Ki | 6.07 |
| polymer | 1003 | Glycogen synthase kinase-3 beta | P49841 | Homo sapiens | 3 | 3 | IC50, Ki | 7.7 |
| polymer | 50000409 | Serine/threonine-protein kinase/endoribonuclease IRE2 | Q76MJ5 | Homo sapiens | 3 | 3 | IC50 | 7.49 |
| polymer | 50004126 | LIM domain kinase 2 | P53671 | Homo sapiens | 2 | 2 | IC50 | 8.52 |
| polymer | 4516 | LIM domain kinase 1 | P53667 | Homo sapiens | 2 | 2 | IC50 | 8.4 |
| polymer | 8039 | Receptor-interacting serine/threonine-protein kinase 2 | O43353 | Homo sapiens | 2 | 3 | IC50 | 8.2 |
| polymer | 750 | TGF-beta receptor type-1 | P36897 | Homo sapiens | 2 | 2 | IC50 | 8 |
| polymer | 1967 | Histone deacetylase 1 | Q13547 | Homo sapiens | 2 | 3 | IC50 | 7.8 |
| polymer | 2556 | Histone deacetylase 6 | Q9UBN7 | Homo sapiens | 2 | 3 | IC50 | 7.8 |
| polymer | 5221 | Tyrosine-protein kinase ABL1 | P00519 | Homo sapiens | 2 | 7 | Kd, Ki | 7.31 |
| polymer | 4366 | Calcium-dependent protein kinase 1 | P62343 | Plasmodium falciparum (isolate K1 / Thailand) | 2 | 8 | Kd | 7.3 |
| polymer | 50006194 | Calcium-dependent protein kinase 4 | Q8IBS5 | Plasmodium falciparum (isolate 3D7) | 2 | 8 | Kd | 7.3 |
| polymer | 50000733 | Casein kinase I | Q8IHZ9 | Plasmodium falciparum (isolate 3D7) | 2 | 4 | Kd | 6.82 |
| polymer | 4918 | Tyrosine-protein kinase JAK2 | O60674 | Homo sapiens | 2 | 2 | Kd | 6.7 |
| polymer | 2113 | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit ga... | P48736 | Homo sapiens | 2 | 2 | IC50 | 6.68 |
| polymer | 2107 | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit be... | P42338 | Homo sapiens | 2 | 3 | IC50 | 5.92 |
| polymer | 2700 | Serine/threonine-protein kinase PLK1 | P53350 | Homo sapiens | 2 | 4 | IC50 | 5.3 |
| polymer | 50006237 | Receptor-interacting serine/threonine-protein kinase 3 | Q9Y572 | Homo sapiens | 1 | 2 | IC50 | 8.7 |
| complex | 50000034 | Cyclin-dependent kinase 2/G1/S-specific cyclin-E1/G1/S-specific cyc... |  |  | 1 | 2 | Ki | 8.52 |
| complex | 50000024 | Cyclin-dependent kinase 1/G2/mitotic-specific cyclin-B1/G2/mitotic-... |  |  | 1 | 2 | Ki | 8.4 |
| polymer | 2939 | RAF proto-oncogene serine/threonine-protein kinase | P04049 | Homo sapiens | 1 | 3 | IC50 | 8.3 |
| polymer | 9736 | Eukaryotic translation initiation factor 2-alpha kinase 3 | Q9NZJ5 | Homo sapiens | 1 | 1 | IC50 | 8.15 |
| polymer | 1846 | Tyrosine-protein kinase BTK | Q06187 | Homo sapiens | 1 | 1 | IC50 | 8 |
| polymer | 4514 | Activin receptor type-2B | Q13705 | Homo sapiens | 1 | 1 | IC50 | 8 |
| polymer | 5143 | Receptor tyrosine-protein kinase erbB-4 | Q15303 | Homo sapiens | 1 | 1 | IC50 | 8 |
| polymer | 5481 | Tyrosine-protein kinase Lyn | P07948 | Homo sapiens | 1 | 1 | IC50 | 8 |
| polymer | 50004793 | Nuclear receptor coactivator 1 | Q15788 | Homo sapiens | 1 | 1 | IC50 | 8 |
| polymer | 8117 | Serine/threonine-protein kinase A-Raf | P10398 | Homo sapiens | 1 | 1 | IC50 | 7.59 |
| polymer | 2130 | Adenosine receptor A2a | P29274 | Homo sapiens | 1 | 1 | Ki | 7.25 |
| polymer | 1402 | Aurora kinase C | Q9UQB9 | Homo sapiens | 1 | 1 | IC50 | 7.19 |
| polymer | 4578 | Nuclear receptor subfamily 4 group A member 1 | P22736 | Homo sapiens | 1 | 2 | Kd | 7.04 |
| polymer | 50005111 | Serine/threonine protein kinase YCK2 | A0A1D8PKB4 |  | 1 | 1 | IC50 | 6.85 |
| complex | 329 | CDK-activating kinase assembly factor MAT1/Cyclin-H/Cyclin-dependen... |  |  | 1 | 1 | IC50 | 6.77 |
| complex | 108 | Cyclin-dependent kinase 5 activator 1 |  |  | 1 | 1 | IC50 | 6.73 |
| polymer | 909 | Cyclin-dependent kinase 6 | Q00534 | Homo sapiens | 1 | 1 | Ki | 6.55 |
| polymer | 2750 | Casein kinase I isoform alpha | P48729 | Homo sapiens | 1 | 1 | IC50 | 6.55 |
| polymer | 7547 | Casein kinase I isoform delta | P48730 | Homo sapiens | 1 | 1 | IC50 | 6.51 |
| polymer | 2109 | Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit de... | O00329 | Homo sapiens | 1 | 2 | IC50 | 6.47 |
| polymer | 3619 | Acetylcholinesterase | P22303 | Homo sapiens | 1 | 2 | IC50 | 6.4 |
| polymer | 8047 | Lysine-specific demethylase 5B | Q9UGL1 | Homo sapiens | 1 | 1 | IC50 | 6.35 |
| polymer | 2111 | Ribosomal protein S6 kinase beta-1 | P23443 | Homo sapiens | 1 | 1 | Ki | 6.27 |
| complex | 50016126 | Cyclin-K/Cyclin-dependent kinase 12 |  |  | 1 | 1 | IC50 | 6.26 |
| polymer | 50007656 | Cyclin-dependent kinase 12 | Q9NYV4 | Homo sapiens | 1 | 1 | IC50 | 6.26 |
| polymer | 7795 | Ferrochelatase, mitochondrial [R115L] | P22830[R115L] | Homo sapiens | 1 | 1 | Kd | 6.15 |
| polymer | 2482 | Histone deacetylase 2 | Q92769 | Homo sapiens | 1 | 1 | IC50 | 6.13 |
| polymer | 13 | Proto-oncogene tyrosine-protein kinase Src | P12931 | Homo sapiens | 1 | 1 | Ki | 6.09 |
| polymer | 2129 | Adenosine receptor A1 | P30542 | Homo sapiens | 1 | 1 | Ki | 6.08 |
| polymer | 1995 | Histone deacetylase 3 | O15379 | Homo sapiens | 1 | 1 | IC50 | 6.03 |
| polymer | 2645 | Histone deacetylase 7 | Q8WUI4 | Homo sapiens | 1 | 1 | IC50 | 5.52 |
| polymer | 1216 | Dual specificity tyrosine-phosphorylation-regulated kinase 1A | Q13627 | Homo sapiens | 1 | 1 | IC50 | 5.4 |
| polymer | 357 | Isocitrate dehydrogenase [NADP] cytoplasmic [R132H] | O75874[R132H] | Homo sapiens | 1 | 2 | IC50 | 5.26 |
| polymer | 50004331 | Heat shock factor protein 1 | Q00613 | Homo sapiens | 1 | 1 | IC50 | 5 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "query": {
    "input": "s1cncc1-c1ccnc([#7])n1",
    "interpreted_as": "smarts",
    "canonical": "s1cncc1-c1ccnc([#7])n1"
  },
  "n_matching_compounds": 549,
  "n_targets": 86,
  "n_compounds_measured": 529,
  "row_count": 86,
  "truncated": false,
  "rows": [
    {
      "target_kind": "polymer",
      "target_id": 2869,
      "target_name": "Tyrosine-protein kinase CSK",
      "uniprot_raw": "P41240",
      "organism": "Homo sapiens",
      "n_compounds": 149,
      "n_measurements": 149,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.57
    },
    {
      "target_kind": "complex",
      "target_id": 113,
      "target_name": "Cyclin-T1/Cyclin-dependent kinase 9",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 131,
      "n_measurements": 139,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.4
    },
    {
      "target_kind": "complex",
      "target_id": 97,
      "target_name": "Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 93,
      "n_measurements": 93,
      "affinity_types": [
        "IC50",
        "Kd",
        "Ki"
      ],
      "best_p_affinity": 8.52
    },
    {
      "target_kind": "complex",
      "target_id": 112,
      "target_name": "Cyclin-H/Cyclin-dependent kinase 7",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 92,
      "n_measurements": 93,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 7.62
    },
    {
      "target_kind": "complex",
      "target_id": 95,
      "target_name": "Cyclin-dependent kinase/G2/mitotic-specific cyclin- 1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 88,
      "n_measurements": 88,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.3
    },
    {
      "target_kind": "complex",
      "target_id": 93,
      "target_name": "Cyclin-dependent kinase 4/G1/S-specific cyclin-D1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 56,
      "n_measurements": 56,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.0
    },
    {
      "target_kind": "polymer",
      "target_id": 50006193,
      "target_name": "cGMP-dependent protein kinase",
      "uniprot_raw": null,
      "organism": "Plasmodium falciparum",
      "n_compounds": 43,
      "n_measurements": 76,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 9.52
    },
    {
      "target_kind": "polymer",
      "target_id": 796,
      "target_name": "Cyclin-dependent kinase 2",
      "uniprot_raw": "P24941",
      "organism": "Homo sapiens",
      "n_compounds": 38,
      "n_measurements": 67,
      "affinity_types": [
        "IC50",
        "Kd",
        "Ki"
      ],
      "best_p_affinity": 9.96
    },
    {
      "target_kind": "complex",
      "target_id": 50000025,
      "target_name": "Cyclin-A1/Cyclin-A2/Cyclin-dependent kinase 2",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 38,
      "n_measurements": 41,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.7
    },
    {
      "target_kind": "polymer",
      "target_id": 520,
      "target_name": "Epidermal growth factor receptor",
      "uniprot_raw": "P00533",
      "organism": "Homo sapiens",
      "n_compounds": 38,
      "n_measurements": 58,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 9.05
    },
    {
      "target_kind": "complex",
      "target_id": 311,
      "target_name": "Cyclin-dependent kinase 6/G1/S-specific cyclin-D3",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 36,
      "n_measurements": 36,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 507,
      "target_name": "Tyrosine-protein kinase Lck",
      "uniprot_raw": "P06239",
      "organism": "Homo sapiens",
      "n_compounds": 35,
      "n_measurements": 35,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 997,
      "target_name": "Cyclin-dependent kinase 9",
      "uniprot_raw": "P50750",
      "organism": "Homo sapiens",
      "n_compounds": 30,
      "n_measurements": 30,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.54
    },
    {
      "target_kind": "complex",
      "target_id": 81,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 29,
      "n_measurements": 31,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 995,
      "target_name": "Cyclin-dependent kinase 7",
      "uniprot_raw": "P50613",
      "organism": "Homo sapiens",
      "n_compounds": 26,
      "n_measurements": 27,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.25
    },
    {
      "target_kind": "polymer",
      "target_id": 799,
      "target_name": "Cyclin-dependent kinase 4",
      "uniprot_raw": "P11802",
      "organism": "Homo sapiens",
      "n_compounds": 26,
      "n_measurements": 27,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 804,
      "target_name": "Cyclin-dependent kinase 1",
      "uniprot_raw": "P06493",
      "organism": "Homo sapiens",
      "n_compounds": 23,
      "n_measurements": 24,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.52
    },
    {
      "target_kind": "polymer",
      "target_id": 1325,
      "target_name": "Aurora kinase A",
      "uniprot_raw": "O14965",
      "organism": "Homo sapiens",
      "n_compounds": 16,
      "n_measurements": 18,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 9.4
    },
    {
      "target_kind": "polymer",
      "target_id": 2857,
      "target_name": "Serine/threonine-protein kinase B-raf",
      "uniprot_raw": "P15056",
      "organism": "Homo sapiens",
      "n_compounds": 15,
      "n_measurements": 40,
      "affinity_types": [
        "EC50",
        "IC50"
      ],
      "best_p_affinity": 9.4
    },
    {
      "target_kind": "polymer",
      "target_id": 4981,
      "target_name": "Aurora kinase B",
      "uniprot_raw": "Q96GD4",
      "organism": "Homo sapiens",
      "n_compounds": 15,
      "n_measurements": 17,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 5506,
      "target_name": "MAP kinase-interacting serine/threonine-protein kinase 2",
      "uniprot_raw": "Q9HBH9",
      "organism": "Homo sapiens",
      "n_compounds": 14,
      "n_measurements": 15,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 6.96
    },
    {
      "target_kind": "polymer",
      "target_id": 3881,
      "target_name": "Mitogen-activated protein kinase 14",
      "uniprot_raw": "Q16539",
      "organism": "Homo sapiens",
      "n_compounds": 12,
      "n_measurements": 12,
      "affinity_types": [
        "IC50",
        "Kd"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "polymer",
      "target_id": 5923,
      "target_name": "Serine/threonine-protein kinase/endoribonuclease IRE1",
      "uniprot_raw": "O75460",
      "organism": "Homo sapiens",
      "n_compounds": 12,
      "n_measurements": 12,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 50003140,
      "target_name": "Wee1-like protein kinase",
      "uniprot_raw": "P30291",
      "organism": "Homo sapiens",
      "n_compounds": 11,
      "n_measurements": 11,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.74
    },
    {
      "target_kind": "polymer",
      "target_id": 1358,
      "target_name": "Receptor-type tyrosine-protein kinase FLT3",
      "uniprot_raw": "P36888",
      "organism": "Homo sapiens",
      "n_compounds": 10,
      "n_measurements": 12,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 8.3
    },
    {
      "target_kind": "polymer",
      "target_id": 800,
      "target_name": "G1/S-specific cyclin-D1",
      "uniprot_raw": "P24385",
      "organism": "Homo sapiens",
      "n_compounds": 10,
      "n_measurements": 10,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.15
    },
    {
      "target_kind": "polymer",
      "target_id": 802,
      "target_name": "G1/S-specific cyclin-E1",
      "uniprot_raw": "P24864",
      "organism": "Homo sapiens",
      "n_compounds": 10,
      "n_measurements": 10,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.66
    },
    {
      "target_kind": "polymer",
      "target_id": 2132,
      "target_name": "Potassium voltage-gated channel subfamily H member 2",
      "uniprot_raw": "Q12809",
      "organism": "Homo sapiens",
      "n_compounds": 9,
      "n_measurements": 18,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.22
    },
    {
      "target_kind": "polymer",
      "target_id": 1622,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit alpha isoform",
      "uniprot_raw": "P42336",
      "organism": "Homo sapiens",
      "n_compounds": 7,
      "n_measurements": 8,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.12
    },
    {
      "target_kind": "polymer",
      "target_id": 916,
      "target_name": "Ketohexokinase",
      "uniprot_raw": "P50053",
      "organism": "Homo sapiens",
      "n_compounds": 6,
      "n_measurements": 6,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.62
    },
    {
      "target_kind": "polymer",
      "target_id": 808,
      "target_name": "Angiopoietin-1 receptor",
      "uniprot_raw": "Q02763",
      "organism": "Homo sapiens",
      "n_compounds": 6,
      "n_measurements": 6,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 8.47
    },
    {
      "target_kind": "polymer",
      "target_id": 932,
      "target_name": "Isoform A of Ketohexokinase (Peripheral)",
      "uniprot_raw": "P50053-2",
      "organism": "Homo sapiens",
      "n_compounds": 6,
      "n_measurements": 6,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.87
    },
    {
      "target_kind": "polymer",
      "target_id": 9683,
      "target_name": "Nuclear receptor subfamily 1 group I member 2",
      "uniprot_raw": "O75469",
      "organism": "Homo sapiens",
      "n_compounds": 6,
      "n_measurements": 8,
      "affinity_types": [
        "EC50"
      ],
      "best_p_affinity": 7.09
    },
    {
      "target_kind": "polymer",
      "target_id": 692,
      "target_name": "Vascular endothelial growth factor receptor 2",
      "uniprot_raw": "P35968",
      "organism": "Homo sapiens",
      "n_compounds": 4,
      "n_measurements": 5,
      "affinity_types": [
        "IC50",
        "Kd",
        "Ki"
      ],
      "best_p_affinity": 7.36
    },
    {
      "target_kind": "polymer",
      "target_id": 3672,
      "target_name": "MAP kinase-interacting serine/threonine-protein kinase 1",
      "uniprot_raw": "Q9BUB5",
      "organism": "Homo sapiens",
      "n_compounds": 4,
      "n_measurements": 4,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 6.07
    },
    {
      "target_kind": "polymer",
      "target_id": 1003,
      "target_name": "Glycogen synthase kinase-3 beta",
      "uniprot_raw": "P49841",
      "organism": "Homo sapiens",
      "n_compounds": 3,
      "n_measurements": 3,
      "affinity_types": [
        "IC50",
        "Ki"
      ],
      "best_p_affinity": 7.7
    },
    {
      "target_kind": "polymer",
      "target_id": 50000409,
      "target_name": "Serine/threonine-protein kinase/endoribonuclease IRE2",
      "uniprot_raw": "Q76MJ5",
      "organism": "Homo sapiens",
      "n_compounds": 3,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.49
    },
    {
      "target_kind": "polymer",
      "target_id": 50004126,
      "target_name": "LIM domain kinase 2",
      "uniprot_raw": "P53671",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.52
    },
    {
      "target_kind": "polymer",
      "target_id": 4516,
      "target_name": "LIM domain kinase 1",
      "uniprot_raw": "P53667",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.4
    },
    {
      "target_kind": "polymer",
      "target_id": 8039,
      "target_name": "Receptor-interacting serine/threonine-protein kinase 2",
      "uniprot_raw": "O43353",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.2
    },
    {
      "target_kind": "polymer",
      "target_id": 750,
      "target_name": "TGF-beta receptor type-1",
      "uniprot_raw": "P36897",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 2,
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
      "n_compounds": 2,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.8
    },
    {
      "target_kind": "polymer",
      "target_id": 2556,
      "target_name": "Histone deacetylase 6",
      "uniprot_raw": "Q9UBN7",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.8
    },
    {
      "target_kind": "polymer",
      "target_id": 5221,
      "target_name": "Tyrosine-protein kinase ABL1",
      "uniprot_raw": "P00519",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 7,
      "affinity_types": [
        "Kd",
        "Ki"
      ],
      "best_p_affinity": 7.31
    },
    {
      "target_kind": "polymer",
      "target_id": 4366,
      "target_name": "Calcium-dependent protein kinase 1",
      "uniprot_raw": "P62343",
      "organism": "Plasmodium falciparum (isolate K1 / Thailand)",
      "n_compounds": 2,
      "n_measurements": 8,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 7.3
    },
    {
      "target_kind": "polymer",
      "target_id": 50006194,
      "target_name": "Calcium-dependent protein kinase 4",
      "uniprot_raw": "Q8IBS5",
      "organism": "Plasmodium falciparum (isolate 3D7)",
      "n_compounds": 2,
      "n_measurements": 8,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 7.3
    },
    {
      "target_kind": "polymer",
      "target_id": 50000733,
      "target_name": "Casein kinase I",
      "uniprot_raw": "Q8IHZ9",
      "organism": "Plasmodium falciparum (isolate 3D7)",
      "n_compounds": 2,
      "n_measurements": 4,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 6.82
    },
    {
      "target_kind": "polymer",
      "target_id": 4918,
      "target_name": "Tyrosine-protein kinase JAK2",
      "uniprot_raw": "O60674",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 2,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 6.7
    },
    {
      "target_kind": "polymer",
      "target_id": 2113,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit gamma isoform",
      "uniprot_raw": "P48736",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.68
    },
    {
      "target_kind": "polymer",
      "target_id": 2107,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit beta isoform",
      "uniprot_raw": "P42338",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.92
    },
    {
      "target_kind": "polymer",
      "target_id": 2700,
      "target_name": "Serine/threonine-protein kinase PLK1",
      "uniprot_raw": "P53350",
      "organism": "Homo sapiens",
      "n_compounds": 2,
      "n_measurements": 4,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.3
    },
    {
      "target_kind": "polymer",
      "target_id": 50006237,
      "target_name": "Receptor-interacting serine/threonine-protein kinase 3",
      "uniprot_raw": "Q9Y572",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.7
    },
    {
      "target_kind": "complex",
      "target_id": 50000034,
      "target_name": "Cyclin-dependent kinase 2/G1/S-specific cyclin-E1/G1/S-specific cyclin-E2",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 8.52
    },
    {
      "target_kind": "complex",
      "target_id": 50000024,
      "target_name": "Cyclin-dependent kinase 1/G2/mitotic-specific cyclin-B1/G2/mitotic-specific cyclin-B2/G2/mitotic-specific cyclin-B3",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 8.4
    },
    {
      "target_kind": "polymer",
      "target_id": 2939,
      "target_name": "RAF proto-oncogene serine/threonine-protein kinase",
      "uniprot_raw": "P04049",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 3,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.3
    },
    {
      "target_kind": "polymer",
      "target_id": 9736,
      "target_name": "Eukaryotic translation initiation factor 2-alpha kinase 3",
      "uniprot_raw": "Q9NZJ5",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.15
    },
    {
      "target_kind": "polymer",
      "target_id": 1846,
      "target_name": "Tyrosine-protein kinase BTK",
      "uniprot_raw": "Q06187",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 4514,
      "target_name": "Activin receptor type-2B",
      "uniprot_raw": "Q13705",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 5143,
      "target_name": "Receptor tyrosine-protein kinase erbB-4",
      "uniprot_raw": "Q15303",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 5481,
      "target_name": "Tyrosine-protein kinase Lyn",
      "uniprot_raw": "P07948",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 50004793,
      "target_name": "Nuclear receptor coactivator 1",
      "uniprot_raw": "Q15788",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 8.0
    },
    {
      "target_kind": "polymer",
      "target_id": 8117,
      "target_name": "Serine/threonine-protein kinase A-Raf",
      "uniprot_raw": "P10398",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.59
    },
    {
      "target_kind": "polymer",
      "target_id": 2130,
      "target_name": "Adenosine receptor A2a",
      "uniprot_raw": "P29274",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 7.25
    },
    {
      "target_kind": "polymer",
      "target_id": 1402,
      "target_name": "Aurora kinase C",
      "uniprot_raw": "Q9UQB9",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 7.19
    },
    {
      "target_kind": "polymer",
      "target_id": 4578,
      "target_name": "Nuclear receptor subfamily 4 group A member 1",
      "uniprot_raw": "P22736",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 7.04
    },
    {
      "target_kind": "polymer",
      "target_id": 50005111,
      "target_name": "Serine/threonine protein kinase YCK2",
      "uniprot_raw": "A0A1D8PKB4",
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.85
    },
    {
      "target_kind": "complex",
      "target_id": 329,
      "target_name": "CDK-activating kinase assembly factor MAT1/Cyclin-H/Cyclin-dependent kinase 7",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.77
    },
    {
      "target_kind": "complex",
      "target_id": 108,
      "target_name": "Cyclin-dependent kinase 5 activator 1",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.73
    },
    {
      "target_kind": "polymer",
      "target_id": 909,
      "target_name": "Cyclin-dependent kinase 6",
      "uniprot_raw": "Q00534",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 6.55
    },
    {
      "target_kind": "polymer",
      "target_id": 2750,
      "target_name": "Casein kinase I isoform alpha",
      "uniprot_raw": "P48729",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.55
    },
    {
      "target_kind": "polymer",
      "target_id": 7547,
      "target_name": "Casein kinase I isoform delta",
      "uniprot_raw": "P48730",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.51
    },
    {
      "target_kind": "polymer",
      "target_id": 2109,
      "target_name": "Phosphatidylinositol 4,5-bisphosphate 3-kinase catalytic subunit delta isoform",
      "uniprot_raw": "O00329",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.47
    },
    {
      "target_kind": "polymer",
      "target_id": 3619,
      "target_name": "Acetylcholinesterase",
      "uniprot_raw": "P22303",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.4
    },
    {
      "target_kind": "polymer",
      "target_id": 8047,
      "target_name": "Lysine-specific demethylase 5B",
      "uniprot_raw": "Q9UGL1",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.35
    },
    {
      "target_kind": "polymer",
      "target_id": 2111,
      "target_name": "Ribosomal protein S6 kinase beta-1",
      "uniprot_raw": "P23443",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 6.27
    },
    {
      "target_kind": "complex",
      "target_id": 50016126,
      "target_name": "Cyclin-K/Cyclin-dependent kinase 12",
      "uniprot_raw": null,
      "organism": null,
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.26
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
      "best_p_affinity": 6.26
    },
    {
      "target_kind": "polymer",
      "target_id": 7795,
      "target_name": "Ferrochelatase, mitochondrial [R115L]",
      "uniprot_raw": "P22830[R115L]",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Kd"
      ],
      "best_p_affinity": 6.15
    },
    {
      "target_kind": "polymer",
      "target_id": 2482,
      "target_name": "Histone deacetylase 2",
      "uniprot_raw": "Q92769",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.13
    },
    {
      "target_kind": "polymer",
      "target_id": 13,
      "target_name": "Proto-oncogene tyrosine-protein kinase Src",
      "uniprot_raw": "P12931",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 6.09
    },
    {
      "target_kind": "polymer",
      "target_id": 2129,
      "target_name": "Adenosine receptor A1",
      "uniprot_raw": "P30542",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "Ki"
      ],
      "best_p_affinity": 6.08
    },
    {
      "target_kind": "polymer",
      "target_id": 1995,
      "target_name": "Histone deacetylase 3",
      "uniprot_raw": "O15379",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 6.03
    },
    {
      "target_kind": "polymer",
      "target_id": 2645,
      "target_name": "Histone deacetylase 7",
      "uniprot_raw": "Q8WUI4",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.52
    },
    {
      "target_kind": "polymer",
      "target_id": 1216,
      "target_name": "Dual specificity tyrosine-phosphorylation-regulated kinase 1A",
      "uniprot_raw": "Q13627",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.4
    },
    {
      "target_kind": "polymer",
      "target_id": 357,
      "target_name": "Isocitrate dehydrogenase [NADP] cytoplasmic [R132H]",
      "uniprot_raw": "O75874[R132H]",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 2,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.26
    },
    {
      "target_kind": "polymer",
      "target_id": 50004331,
      "target_name": "Heat shock factor protein 1",
      "uniprot_raw": "Q00613",
      "organism": "Homo sapiens",
      "n_compounds": 1,
      "n_measurements": 1,
      "affinity_types": [
        "IC50"
      ],
      "best_p_affinity": 5.0
    }
  ],
  "compounds_searched": 1464874,
  "search_set_size": 1464874
}
```

</details>

<!-- results-sha256: 582a2bff399ca98e339234fd0b3ae35fe83ba03b849b6ba8d7057509b8011f4f -->

## Answer

**The query.** The chemotype is written as the SMARTS rule from example 13, `s1cncc1-c1ccnc([#7])n1`:
a thiazole joined at C5 to C4 of a pyrimidine that carries a nitrogen at C2. The `[#7]` is SMARTS
syntax (SMILES would read it as a radical nitrogen and match nothing), so the tool read the query as
SMARTS. **549 compounds** contain this substructure. "Binds" here means at least one Ki, Kd, IC50 or
EC50 of 10 µM or better (`max_value_nm=10000`, which excludes `>` values). By that measure, **529 of
the 549 bind at least one target, and 86 targets are bound.** The full list is the step 2 table.
Note that it mixes affinity types, so `best_p_affinity` compares IC50 and Ki values loosely.

**What the profile shows:**
- **Mostly kinases.** 70 of the 86 targets are kinases, and 20 rows are CDKs or cyclins. The most
  compounds bind CDK9/cyclin T1 (131), CDK2/cyclin A2 (93), CDK7/cyclin H (92), CDK1/cyclin B (88)
  and CDK4/cyclin D1 (56). This matches the chemotype's origin as a CDK hinge-binder series.
- **The top row comes from one patent.** All 149 CSK compounds come from US12427146B2 (2025). A count
  of compounds per target says how much a target was tested, which is not the same as how selective
  the chemotype is.
- **Beyond human CDKs.** *Plasmodium falciparum* cGMP-dependent kinase (PKG) has 43 compounds, from
  two antimalarial papers (2018–2019). EGFR has 38, all from one 2023 paper. B-raf has 15, because the
  BRAF inhibitor dabrafenib and its analogues also contain this substructure. The SMARTS rule is
  broader than the CDK series in example 13.
- **The long tail.** 35 targets have a single compound. The 16 non-kinase targets include hERG (9
  compounds, best pIC50 6.2, measured as a safety screen in one of the PKG papers), four HDACs, the
  adenosine A1/A2a receptors and PXR (`NR1I2`, EC50 for activation rather than inhibition).

**Rows to merge or check before counting proteins:**
- **The same protein appears under several targets.** BindingDB keeps a polymer and each complex as
  separate targets, so CDK2 appears as the bare protein (796) and in four complexes (97, 81, 50000025,
  50000034). To count per protein, merge these rows by gene. Summing their `n_compounds` would count
  a compound twice if it was measured on more than one of them.
- **Cyclin-only rows.** G1/S-specific cyclin-D1 (800) and cyclin-E1 (802), with 10 compounds each, are
  almost certainly CDK4/cyclin D1 and CDK2/cyclin E assays recorded against the cyclin alone.
- **Mutant targets.** Two rows are mutants: ferrochelatase R115L and IDH1 R132H.

**Compared with example 13:** that report found 85 of these compounds among the Ki-only ligands of
CDK2/cyclin A2. Here complex 97 has 93, because IC50 and Kd measurements also count.
