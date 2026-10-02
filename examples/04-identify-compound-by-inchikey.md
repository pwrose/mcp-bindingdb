# Identify a compound from its InChIKey

> **Question:** I have the InChIKey BNRNXUUZRGQAQC-UHFFFAOYSA-N. What compound is it, and what does it bind?

BindingDB release 202610 · server `mcp-bindingdb` 0.1.0 · generated 2026-10-02

## Tool calls

### 1. `search_compounds`

```json
{"query": "BNRNXUUZRGQAQC-UHFFFAOYSA-N"}
```

**Result:**

_2 row(s) — table shows selected columns._

| monomerid | bdbm_id | name | smiles | mol_weight | n_activities | n_targets |
|---|---|---|---|---|---|---|
| 14390 | BDBM14390 | Viagra | CCCc1c2c(n(n1)C)C(=O)NC(=N2)c3cc(ccc3OCC)S(=O)(=O)N4CCN(CC4)C | 474.2 | 201 | 58 |
| 50238854 | BDBM50238854 | Viagra | CCCc1nn(C)c2c(=O)[nH]c(-c3cc(S(=O)(=O)N4CCN(C)CC4)ccc3OCC)nc12 | 474.2 | 8 | 5 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "row_count": 2,
  "truncated": false,
  "rows": [
    {
      "monomerid": 14390,
      "bdbm_id": "BDBM14390",
      "name": "Viagra",
      "inchi_key": "BNRNXUUZRGQAQC-UHFFFAOYSA-N",
      "smiles": "CCCc1c2c(n(n1)C)C(=O)NC(=N2)c3cc(ccc3OCC)S(=O)(=O)N4CCN(CC4)C",
      "mol_weight": 474.2,
      "n_activities": 201,
      "n_targets": 58
    },
    {
      "monomerid": 50238854,
      "bdbm_id": "BDBM50238854",
      "name": "Viagra",
      "inchi_key": "BNRNXUUZRGQAQC-UHFFFAOYSA-N",
      "smiles": "CCCc1nn(C)c2c(=O)[nH]c(-c3cc(S(=O)(=O)N4CCN(C)CC4)ccc3OCC)nc12",
      "mol_weight": 474.2,
      "n_activities": 8,
      "n_targets": 5
    }
  ]
}
```

</details>

### 2. `get_compound`

```json
{"monomerid": 14390, "max_synonyms": 15}
```

**Result:**

**compound**

| field | value |
|---|---|
| monomerid | 14390 |
| bdbm_id | BDBM14390 |
| name | Viagra |
| inchi_key | BNRNXUUZRGQAQC-UHFFFAOYSA-N |
| smiles | CCCc1c2c(n(n1)C)C(=O)NC(=N2)c3cc(ccc3OCC)S(=O)(=O)N4CCN(CC4)C |
| formula | C22H30N6O4S |
| mol_weight | 474.2 |
| type | Small organic molecule |
| het_pdb | VIA |
| n_pdb_ids_exact | 6 |
| n_activities | 201 |
| n_targets | 58 |
| inchi | InChI=1S/C22H30N6O4S/c1-5-7-17-19-20(27(4)25-17)22(29)24-21(23-19)1... |
| pdb_ids_exact | 10OZ,1TBF,1UDT,1XOS,2H42,3JWQ |
| pdb_ids_sub |  |

**synonyms:** Viagra, CHEMBL192, Sildenafil, Sildenafil#, SILDENAFIL CITRATE, US11155558, Compound sildenafil, US11242347, Compound sildenafil, US11897890, Compound sildenafil, US12139461, Compound sildenafil, 5-{2-ethoxy-5-[(4-methylpiperazine-1-)sulfonyl]phenyl}-1-methyl-3-propyl-1H,6H,7H-pyrazolo[4,3-d]pyrimidin-7-one, 5-[2-ethoxy-5-(4-methyl-1-piperazinylsulfonyl)phenyl]-1-methyl-3-n-propyl-1,6-dihydro-7H-pyrazolo[4,3-d]pyrimidin-7-one

**top_targets**

| polymerid | complexid | target_name | uniprot_raw | organism | n_measurements | best_p_affinity | affinity_types |
|---|---|---|---|---|---|---|---|
| 50002272 |  | cGMP-specific 3',5'-cyclic phosphodiesterase | O54735 | Rattus norvegicus | 3 | 9.52 | IC50, Ki |
| 5066 |  | cGMP-specific 3',5'-cyclic phosphodiesterase | O76074 | Homo sapiens | 72 | 9 | EC50, IC50, Ki |
| 50006512 |  | cGMP-specific 3',5'-cyclic phosphodiesterase | O77746 | Canis lupus familiaris | 2 | 9 | IC50 |
| 1577 |  | cGMP-specific 3',5'-cyclic phosphodiesterase [531-875] | O76074[531-875] | Homo sapiens | 1 | 8.66 | IC50 |
| 1635 |  | cGMP-specific 3',5'-cyclic phosphodiesterase [535-860] | O76074[535-860] | Homo sapiens | 1 | 8.62 | IC50 |
| 1636 |  | cGMP-specific 3',5'-cyclic phosphodiesterase [1-662,679-875] | O76074[1-662,679-875] | Homo sapiens | 1 | 8.23 | IC50 |
| 50000786 |  | cGMP-specific 3',5'-cyclic phosphodiesterase | Q28156 | Bos taurus | 6 | 8.22 | IC50 |
|  | 50000813 | O43924/P16499/P18545/P35913/P51160/Q13956 |  |  | 3 | 8.02 | IC50, Ki |
|  | 50000741 | P04972/P11541/P16586/P22571/P23439/Q95142 |  |  | 5 | 7.7 | IC50 |
| 7940 |  | Cone cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha' | P51160 | Homo sapiens | 4 | 7.62 | IC50 |
|  | 50005049 | Cone cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha'/cG... |  |  | 2 | 7.6 | Ki |
| 1540 |  | Retinal rod rhodopsin-sensitive cGMP 3',5'-cyclic phosphodiesterase... | P54827 | Canis lupus familiaris | 1 | 7.48 | IC50 |
| 10157 |  | Rod cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha | P11541 | Bos taurus | 1 | 6.85 | IC50 |
| 1639 |  | cGMP-specific 3',5'-cyclic phosphodiesterase [1-660,682-875] | O76074[1-660,682-875] | Homo sapiens | 1 | 6.73 | IC50 |
| 2130 |  | Adenosine receptor A2a | P29274 | Homo sapiens | 1 | 6.7 | Ki |
|  | 50000902 | Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleoti... |  |  | 2 | 6.59 | IC50 |
|  | 50000731 | Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleoti... |  |  | 4 | 6.57 | IC50 |
|  | 50000743 | Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleoti... |  |  | 5 | 6.4 | IC50 |
|  | 50000730 | cGMP-inhibited 3',5'-cyclic phosphodiesterase 3A/3B |  |  | 8 | 6.3 | IC50 |
|  | 50000012 | cAMP-specific 3',5'-cyclic phosphodiesterase 4A/4B/4C/4D |  |  | 5 | 6.3 | IC50 |
| 7465 |  | Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleoti... | P54750 | Homo sapiens | 1 | 6.22 | IC50 |
| 5115 |  | Phosphodiesterase |  | Trypanosoma cruzi | 1 | 6 | IC50 |
| 50006081 |  | ATP-binding cassette sub-family C member 5 | O15440 | Homo sapiens | 2 | 5.92 | IC50, Ki |
| 1572 |  | Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleoti... | Q01064 | Homo sapiens | 1 | 5.82 | IC50 |
| 7417 |  | Dual 3',5'-cyclic-AMP and -GMP phosphodiesterase 11A | Q9HCR9 | Homo sapiens | 5 | 5.64 | IC50 |

<details><summary>Raw tool result (JSON)</summary>

```json
{
  "compound": {
    "monomerid": 14390,
    "bdbm_id": "BDBM14390",
    "name": "Viagra",
    "inchi_key": "BNRNXUUZRGQAQC-UHFFFAOYSA-N",
    "smiles": "CCCc1c2c(n(n1)C)C(=O)NC(=N2)c3cc(ccc3OCC)S(=O)(=O)N4CCN(CC4)C",
    "formula": "C22H30N6O4S",
    "mol_weight": 474.2,
    "type": "Small organic molecule",
    "het_pdb": "VIA",
    "n_pdb_ids_exact": 6,
    "n_activities": 201,
    "n_targets": 58,
    "inchi": "InChI=1S/C22H30N6O4S/c1-5-7-17-19-20(27(4)25-17)22(29)24-21(23-19)16-14-15(8-9-18(16)32-6-2)33(30,31)28-12-10-26(3)11-13-28/h8-9,14H,5-7,10-13H2,1-4H3,(H,23,24,29)",
    "pdb_ids_exact": "10OZ,1TBF,1UDT,1XOS,2H42,3JWQ",
    "pdb_ids_sub": null
  },
  "synonyms": [
    "Viagra",
    "CHEMBL192",
    "Sildenafil",
    "Sildenafil#",
    "SILDENAFIL CITRATE",
    "US11155558, Compound sildenafil",
    "US11242347, Compound sildenafil",
    "US11897890, Compound sildenafil",
    "US12139461, Compound sildenafil",
    "5-{2-ethoxy-5-[(4-methylpiperazine-1-)sulfonyl]phenyl}-1-methyl-3-propyl-1H,6H,7H-pyrazolo[4,3-d]pyrimidin-7-one",
    "5-[2-ethoxy-5-(4-methyl-1-piperazinylsulfonyl)phenyl]-1-methyl-3-n-propyl-1,6-dihydro-7H-pyrazolo[4,3-d]pyrimidin-7-one"
  ],
  "top_targets": [
    {
      "polymerid": 50002272,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase",
      "uniprot_raw": "O54735",
      "organism": "Rattus norvegicus",
      "n_measurements": 3,
      "best_p_affinity": 9.52,
      "affinity_types": [
        "IC50",
        "Ki"
      ]
    },
    {
      "polymerid": 5066,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase",
      "uniprot_raw": "O76074",
      "organism": "Homo sapiens",
      "n_measurements": 72,
      "best_p_affinity": 9.0,
      "affinity_types": [
        "EC50",
        "IC50",
        "Ki"
      ]
    },
    {
      "polymerid": 50006512,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase",
      "uniprot_raw": "O77746",
      "organism": "Canis lupus familiaris",
      "n_measurements": 2,
      "best_p_affinity": 9.0,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 1577,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase [531-875]",
      "uniprot_raw": "O76074[531-875]",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 8.66,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 1635,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase [535-860]",
      "uniprot_raw": "O76074[535-860]",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 8.62,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 1636,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase [1-662,679-875]",
      "uniprot_raw": "O76074[1-662,679-875]",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 8.23,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 50000786,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase",
      "uniprot_raw": "Q28156",
      "organism": "Bos taurus",
      "n_measurements": 6,
      "best_p_affinity": 8.22,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000813,
      "target_name": "O43924/P16499/P18545/P35913/P51160/Q13956",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 3,
      "best_p_affinity": 8.02,
      "affinity_types": [
        "IC50",
        "Ki"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000741,
      "target_name": "P04972/P11541/P16586/P22571/P23439/Q95142",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 5,
      "best_p_affinity": 7.7,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 7940,
      "complexid": null,
      "target_name": "Cone cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha'",
      "uniprot_raw": "P51160",
      "organism": "Homo sapiens",
      "n_measurements": 4,
      "best_p_affinity": 7.62,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50005049,
      "target_name": "Cone cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha'/cGMP-specific 3',5'-cyclic phosphodiesterase",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 2,
      "best_p_affinity": 7.6,
      "affinity_types": [
        "Ki"
      ]
    },
    {
      "polymerid": 1540,
      "complexid": null,
      "target_name": "Retinal rod rhodopsin-sensitive cGMP 3',5'-cyclic phosphodiesterase subunit gamma",
      "uniprot_raw": "P54827",
      "organism": "Canis lupus familiaris",
      "n_measurements": 1,
      "best_p_affinity": 7.48,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 10157,
      "complexid": null,
      "target_name": "Rod cGMP-specific 3',5'-cyclic phosphodiesterase subunit alpha",
      "uniprot_raw": "P11541",
      "organism": "Bos taurus",
      "n_measurements": 1,
      "best_p_affinity": 6.85,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 1639,
      "complexid": null,
      "target_name": "cGMP-specific 3',5'-cyclic phosphodiesterase [1-660,682-875]",
      "uniprot_raw": "O76074[1-660,682-875]",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 6.73,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 2130,
      "complexid": null,
      "target_name": "Adenosine receptor A2a",
      "uniprot_raw": "P29274",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 6.7,
      "affinity_types": [
        "Ki"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000902,
      "target_name": "Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1B/Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1C/Phosphodiesterase",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 2,
      "best_p_affinity": 6.59,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000731,
      "target_name": "Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1A/1B/1C",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 4,
      "best_p_affinity": 6.57,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000743,
      "target_name": "Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1A/1B",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 5,
      "best_p_affinity": 6.4,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000730,
      "target_name": "cGMP-inhibited 3',5'-cyclic phosphodiesterase 3A/3B",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 8,
      "best_p_affinity": 6.3,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": null,
      "complexid": 50000012,
      "target_name": "cAMP-specific 3',5'-cyclic phosphodiesterase 4A/4B/4C/4D",
      "uniprot_raw": null,
      "organism": null,
      "n_measurements": 5,
      "best_p_affinity": 6.3,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 7465,
      "complexid": null,
      "target_name": "Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1A",
      "uniprot_raw": "P54750",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 6.22,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 5115,
      "complexid": null,
      "target_name": "Phosphodiesterase",
      "uniprot_raw": null,
      "organism": "Trypanosoma cruzi",
      "n_measurements": 1,
      "best_p_affinity": 6.0,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 50006081,
      "complexid": null,
      "target_name": "ATP-binding cassette sub-family C member 5",
      "uniprot_raw": "O15440",
      "organism": "Homo sapiens",
      "n_measurements": 2,
      "best_p_affinity": 5.92,
      "affinity_types": [
        "IC50",
        "Ki"
      ]
    },
    {
      "polymerid": 1572,
      "complexid": null,
      "target_name": "Dual specificity calcium/calmodulin-dependent 3',5'-cyclic nucleotide phosphodiesterase 1B",
      "uniprot_raw": "Q01064",
      "organism": "Homo sapiens",
      "n_measurements": 1,
      "best_p_affinity": 5.82,
      "affinity_types": [
        "IC50"
      ]
    },
    {
      "polymerid": 7417,
      "complexid": null,
      "target_name": "Dual 3',5'-cyclic-AMP and -GMP phosphodiesterase 11A",
      "uniprot_raw": "Q9HCR9",
      "organism": "Homo sapiens",
      "n_measurements": 5,
      "best_p_affinity": 5.64,
      "affinity_types": [
        "IC50"
      ]
    }
  ]
}
```

</details>

<!-- results-sha256: 3a3c458ceb8ebe571de237abd34cd90e82366af7905c37202420eaab77800830 -->

## Answer

The InChIKey belongs to **sildenafil (Viagra), BDBM14390**: 201 measurements against 58 targets, and the
PDB ligand **VIA** appears in 6 structures. A second record, BDBM50238854 (sildenafil citrate,
ChEMBL-derived), has the same InChIKey.

Its binding profile is what you'd expect for a PDE5 inhibitor:

- **PDE5** (cGMP-specific 3',5'-cyclic phosphodiesterase) is the main target. The human enzyme has a best pAffinity of 9.0 (about 1 nM) over 72 measurements, and the rat, dog and cow orthologs are similar (pAffinity 8.2–9.5).
- **PDE6** (rod and cone photoreceptor phosphodiesterases) comes next, at pAffinity about 7.5–8.0. This off-target activity is linked to sildenafil's visual side effects.
- **Weaker activity** (pAffinity 5.6–6.6) appears against PDE1, PDE3, PDE4 and PDE11A, and the adenosine A2a receptor (pAffinity 6.7).

Some complex targets are labelled only by a list of UniProt accessions, e.g. `O43924/P16499/...`, which is
the PDE6 holoenzyme. `get_target` with `target_kind="complex"` shows their components.
