# Building the database

The server reads a local, read-only DuckDB build of BindingDB's monthly MySQL dump.

## Build

Requires [uv](https://docs.astral.sh/uv/); no Docker or MySQL.

```bash
scripts/build_duckdb.sh                    # release 202610 -> data/bindingdb_202610.duckdb
scripts/build_duckdb.sh --release 202611   # a later release
```

The script runs `python -m mcp_bindingdb.builder` (`src/mcp_bindingdb/builder/`), which:

1. downloads the dump from bindingdb.org (`BDB-mySQL_All_<release>_dmp.zip`, 258 MB for release 202610,
   resumed if interrupted);
2. loads it into DuckDB without MySQL (`builder/mysqldump.py`): it reads the dump straight from the zip,
   creates each table with the column types DuckDB's MySQL extension would give it, and turns each
   extended INSERT into CSV lines that DuckDB's CSV reader loads. The tables come out identical, row for
   row, to a copy through MySQL. The `regusers` and `person` tables (passwords and contact details) are
   never copied;
3. adds the derived query tables (`builder/derived.py`, below);
4. computes standard InChIKeys (`builder/inchikeys.py`, below);
5. computes compound properties (`builder/compound_properties.py`, below);
6. builds the structure-search index (`builder/structure_index.py`, below).

On 10 cores it takes about 25 minutes, nearly all of it RDKit (steps 4 to 6). Progress goes to
`data/build-<release>.json` and the log to the terminal. A build that stops resumes where it ended: the
download continues and finished steps are skipped. The file is built as `bindingdb_<release>.duckdb.building`
and renamed when complete, so a running server keeps using the old file until it is restarted.

Options:

| Option | Effect |
|---|---|
| `--release YYYYMM` | BindingDB release to build (default 202610, `builder.DEFAULT_RELEASE`) |
| `--workers N` | Worker processes for the RDKit steps (default: all CPUs) |

For release 202610, `data/` holds about 2.4 GB afterwards: the downloaded dump (0.26 GB, kept for
rebuilds), the database (1.3 GB) and the structure-search index (0.85 GB).

The server uses the file given with `--db PATH` or `$BINDINGDB_DUCKDB`, else the newest
`data/bindingdb_*.duckdb`, else the database it builds on first use (below).

## Build on first use

When the server finds no database, it builds release `builder.DEFAULT_RELEASE` itself, in
`$MCP_BINDINGDB_DATA_DIR`, else the per-user data folder: `~/Library/Application Support/mcp-bindingdb` on
macOS, `%LOCALAPPDATA%\mcp-bindingdb` on Windows, `$XDG_DATA_HOME` or `~/.local/share/mcp-bindingdb` on
Linux (`src/mcp_bindingdb/local_build.py`). Nothing is downloaded but BindingDB's own dump, and the files stay
on that computer. The server starts at once and runs the builder as a separate process at low priority,
leaving one CPU free. Until the database is there, the tools that need it return how far the build has got
(step, percentage, time left), and Claude passes that on; the tools that do not need it (transcripts, the tool
log) work meanwhile. The database becomes usable before the index, so only substructure and similarity search
wait for the last step. The builder keeps running if the server exits; a server started meanwhile waits for it
instead of starting another, and a build that stopped resumes the next time a tool needs the database. Its
log is `build-<release>.log` in the data folder. The dump is deleted after a successful build. Notebook
reruns (`Replay`) build the database the same way when they find none, and wait for it.

Each version of the server builds one release, so its results and notebooks stay reproducible. A new
release is built under a new file name; delete old `bindingdb_*` files from the data folder by hand.

## Claude Desktop bundle

`scripts/build_bundle.sh` builds `dist/mcp-bindingdb.mcpb`, an
[MCP bundle](https://github.com/modelcontextprotocol/mcpb) of about 4 MB (needs Node.js). It holds the
source, `pyproject.toml`, `uv.lock` and `bundle/manifest.json`, and no database or Python environment.
Claude Desktop runs it with uv (manifest server type `uv`), which installs the `substructure` and
`structures` extras from the lock file, and the server builds the database on first use as above.

Claude Desktop installs only from wheels in practice (no compilers on users' computers), so every locked
package needs a wheel for each platform. `[tool.uv]` in `pyproject.toml` lists the platforms
(`required-environments`) and holds Intel Macs (macOS x86_64) back to the last RDKit and cryptography
releases with wheels for them (RDKit 2025.9, cryptography 48); newer releases dropped those wheels.
`uv lock` enforces `required-environments` only for packages without a source distribution, so the
script also checks that the lock installs from wheels alone on each platform. Re-lock with a recent uv
(older ones, such as 0.7, mis-resolve `required-environments`; `uvx uv@latest lock` works); the lock it
writes still installs with older uv. Keep the
version in `bundle/manifest.json` equal to `pyproject.toml`'s; the script checks. The README links
`releases/latest/download/mcp-bindingdb.mcpb`, so attach the file, under that name, to each GitHub release
(`gh release create v<version> dist/mcp-bindingdb.mcpb`).

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
`substructure` extra) and an index file, `data/bindingdb_<release>.sslib`. The build script always creates
it; to rebuild it for an existing database:

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
