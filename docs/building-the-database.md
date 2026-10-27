# Building the database

The server reads a local, read-only DuckDB build of BindingDB's monthly MySQL dump.

## Build

Requires Docker (daemon running) and [uv](https://docs.astral.sh/uv/).

```bash
scripts/build_duckdb.sh                    # release 202610 -> data/bindingdb_202610.duckdb
scripts/build_duckdb.sh --release 202611   # a later release
```

The script downloads the dump, loads it into a temporary MySQL 8.4 container, copies it to DuckDB
(`scripts/convert_to_duckdb.py`, checking row counts), adds derived query tables
(`scripts/add_derived_tables.py`), computes standard InChIKeys (below), builds the structure-search
index (below), and removes the container.

Options:

| Option | Effect |
|---|---|
| `--release YYYYMM` | BindingDB release to build (default 202610) |
| `--no-substructure` | Skip the structure-search index |
| `--include-pii` | Keep the `regusers` and `person` tables (passwords and contact details), which are left out by default |
| `--keep-mysql` | Keep the MySQL container after the build |

For release 202610, `data/` holds about 4.5 GB afterwards: the downloaded dump (2.3 GB), the database
(1.2 GB) and the structure-search index (0.8 GB).

The server uses the newest `data/bindingdb_*.duckdb`, or the file given with `--db PATH` or
`$BINDINGDB_DUCKDB`.

## InChIKeys

BindingDB stores no InChIKey for about 31% of its compounds (453k in release 202610), and many stored
keys are non-standard (ending `-NA-N` instead of `-SA-N`) or encode stereo differently (427k), so they do
not match the standard keys that PubChem, OPSIN and RDKit produce. `scripts/compute_inchikeys.py`
computes the standard InChIKey from each compound's SMILES with RDKit and writes it to
`compound.inchi_key` and `activity.inchi_key`; where RDKit cannot make one (about 3k compounds) the
BindingDB key is kept, and `monomer.inchi_key` keeps BindingDB's keys unchanged. Lookups by InChIKey
(`search_compounds`, `find_targets_for_compound`, `chemical_name_to_smiles`, `exact_structure_search`)
depend on these keys. The build script runs it; for an existing database (about 4 minutes, needs the
`substructure` extra):

```bash
uv run --extra substructure python scripts/compute_inchikeys.py data/bindingdb_202610.duckdb
```

It updates a copy that then replaces the file, so a running server keeps working; restart it to use the
new keys. Rerun it after `add_derived_tables.py`, which rebuilds the tables from BindingDB's keys.

## Compound properties

`scripts/compute_properties.py` adds the `compound_property` table: RDKit properties of each compound's
parent (largest fragment, so salts and solvents do not count), its Bemis-Murcko scaffold and the
structural alerts it matches. The `properties` filters, ligand efficiency and LipE, and scaffold
grouping in the tools depend on it ([tools.md](tools.md#compound-properties)). The build script runs it; for an existing
database (about 18 minutes on 10 cores, with progress lines; needs the `substructure` extra):

```bash
uv run --extra substructure python scripts/compute_properties.py data/bindingdb_202610.duckdb
```

Like `compute_inchikeys.py` it updates a copy that then replaces the file; restart the server to use it.
The table only references `compound` by `monomerid`, so it survives a rerun of `add_derived_tables.py`.

## Derived tables

| Table | Contents |
|---|---|
| `activity` | One row per measured value: `affinity_type`, `relation` (`=`, `<`, `>`), numeric `value`, `unit`, `p_affinity`, plus compound, target, assay and citation columns |
| `compound` | One row per small molecule: preferred name, InChIKey, SMILES, formula, weight, counts |
| `compound_name` | Compound synonyms, including ChEMBL ids, PubChem `cid_N` and patent labels |
| `compound_property` | RDKit properties of each compound's parent: heavy atoms, MW, cLogP, TPSA, HBD/HBA, rotatable bonds, rings, Fsp3, QED, Ro5 violations, Bemis-Murcko and generic scaffold, PAINS/Brenk/NIH alerts (from `compute_properties.py`) |
| `target` | One row per polymer/complex target: bare UniProt accession, organism, counts |
| `target_name` | Target synonyms (gene names, UniProt entry names) |

The raw tables mirror the BindingDB MySQL schema; see `schema/`.

## Structure-search index

`substructure_search` and `similarity_search` need [RDKit](https://www.rdkit.org) (the optional
`substructure` extra) and an index file, `data/bindingdb_<release>.sslib`. The build script creates it
unless you pass `--no-substructure`; to build it for an existing database:

```bash
uv run --extra substructure python scripts/build_substructure_index.py data/bindingdb_202610.duckdb
```

For each compound the index holds its canonical SMILES, an RDKit pattern fingerprint (for substructure
screening) and a Morgan fingerprint of its largest fragment (radius 2, 2048 bits, for similarity). For
release 202610 it is about 850 MB and builds in under 1.5 minutes on 10 cores; 1,668 SMILES that RDKit
cannot parse are left out. The server loads it at startup, which takes about 8 s and 1.6 GB of memory.
Without RDKit or the index, or if the index is for a different release or was built by an older
version, the server runs without the two structure-search tools.

## Name-to-structure lookup

`chemical_name_to_smiles` parses systematic (IUPAC) names with [OPSIN](https://github.com/dan2097/opsin),
through the optional `name` extra ([pyopsin](https://pypi.org/project/pyopsin/), which bundles the OPSIN
jar and needs a Java runtime). Without it the tool still uses BindingDB synonyms and PubChem. It needs
no build step.
