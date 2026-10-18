# Tools

| Tool | Purpose |
|---|---|
| `search_compounds` | By name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey (full or first block) |
| `chemical_name_to_smiles` | SMILES for a compound name (trade name, IUPAC name, CAS number) from BindingDB synonyms, OPSIN or PubChem, with the BindingDB compounds that have that structure |
| `search_targets` | By name, gene name, UniProt entry name or accession; optional organism filter |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target (by id or UniProt accession, optional variants) |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `describe_tables` | Table list with descriptions, or columns and sample rows of one table |
| `run_sql` | Arbitrary read-only DuckDB SQL |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those measured against a target with potency filters; every target the matching compounds hit, with compounds per target; or a count of matches (needs the structure-search index) |
| `similarity_search` | Compounds similar to a molecule (Tanimoto on Morgan fingerprints) above a threshold, with the same target filter and per-target summary (needs the structure-search index) |

## Safety

All tools are read-only. The connection is opened read-only with file, network and extension access
disabled and settings locked, so `run_sql` cannot write data or read anything outside the database.
Queries time out after 30 s (`--timeout`). The only tool that uses the network is
`chemical_name_to_smiles`, for PubChem; `--no-network` turns that off.

## chemical_name_to_smiles

It tries three sources in order and stops at the first that knows the name: an exact (case-insensitive)
BindingDB synonym, OPSIN (systematic names, offline; the JVM starts on the first lookup, about 1 s), and
the PubChem name service. A BindingDB name can belong to several compounds (stereoisomers, or patent
labels such as `compound 5`); all are returned, most measured first, flagged `ambiguous` when their
InChIKey first blocks differ. A structure from OPSIN or PubChem is matched back to BindingDB by InChIKey:
the same compound first, then compounds sharing the first block (other stereoisomers). PubChem's
staurosporine, for example, has different stereo descriptors from all BindingDB entries named
staurosporine, so it is found only by its first block. The `sources` argument picks which sources to try
and in what order.

## substructure_search

It reads a SMILES query by default, so Kekulé and aromatic forms of a ring match the same compounds. It
uses SMARTS when the query contains `*`, is not valid SMILES, is written aromatic but is not a valid
aromatic molecule (such as a ring nitrogen missing its H), or has a bracket atom without H such as
`[#7]` (which SMILES would make a radical). A SMILES query ignores H counts written in brackets; pass
`query_type="smarts"` to enforce them. The result echoes how the query was read. Without a target,
results are capped at `limit` and favour the compounds with the most measurements. With a target, every
compound measured against it is searched and the matches are ranked by potency. A search stops at 80%
of the query time limit and reports partial results; counting a very generic query (a benzene ring
matches 1.28M compounds) takes about 5 s.

## similarity_search

It takes a whole molecule as SMILES and returns compounds with Tanimoto similarity at or above
`threshold` (default 0.7), most similar first. Fingerprints are Morgan, radius 2, 2048 bits, computed on
the largest fragment, so a salt scores the same as its parent. Stereochemistry is ignored, so
stereoisomers score 1.0. Scoring all 1.46M compounds takes about 50 ms.

## Data notes

- Ki/Kd/IC50/EC50 are in nM, kon in M⁻¹s⁻¹, koff in s⁻¹; `p_affinity = 9 − log10(nM)`.
- `>` values (e.g. `>10000`) usually mean inactive at the highest concentration tested; potency filters exclude them.
- `monomer.display_name` holds only the BDBM id; names are in `compound_name` / `compound.name`.
- `monomer.chembl_id` is empty in this release; ChEMBL ids appear as synonyms instead.
- Mutant and construct targets are separate rows sharing a UniProt accession (`uniprot_raw` like `P00533[L858R]`).
- Text comparisons in DuckDB are case-sensitive (MySQL's were not): use `ILIKE` or `lower()`.
