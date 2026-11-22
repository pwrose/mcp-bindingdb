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

On 10 cores it takes about 25 minutes, nearly all of it RDKit (steps 4 to 6). Measured on an Apple M1 Max
(10 cores, all used, foreground) for release 202611 on 2026-11-20:

| Step | Time |
|---|---|
| 1. Download (261 MB) | 70 s (depends on the connection) |
| 2. Load into DuckDB | 17 s |
| 3. Query tables | 3 s |
| 4. InChIKeys | 3.7 min |
| 5. Compound properties | 19.7 min |
| 6. Structure-search index | 1.5 min |
| Total | 26.4 min |

The server's own build runs at low priority with one core left free, so it takes a little longer (24.8 min
wall time for release 202610 on the same machine, with other work running). Time grows with fewer cores,
roughly in proportion for steps 4 to 6. Each build records its step times and the machine it ran on
(cores, workers, background or not) in `build-<release>.json` (`step_seconds`, `build_seconds`, `machine`),
and `update_database` quotes the last build's time as the estimate for the next. Progress goes to
`data/build-<release>.json` and the log to the terminal. A build that stops resumes where it ended: the
download continues and finished steps are skipped. The file is built as `bindingdb_<release>.duckdb.building`
and renamed when complete, so a running server keeps using the old file until it is restarted.

Options:

| Option | Effect |
|---|---|
| `--release YYYYMM` | BindingDB release to build (default 202610, `builder.DEFAULT_RELEASE`) |
| `--workers N` | Worker processes for the RDKit steps (default: all CPUs) |

For release 202611, a build holds about 2.1 GB afterwards: the downloaded dump (0.26 GB, kept in `data/`
for rebuilds, deleted by the server's own build), the database (0.96 GB) and the structure-search index
(0.86 GB). A database changed in place by the scripts below grows (1.4 GB for the 202610 copy in `data/`).

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

## Prebuilt databases from a mirror (test)

Instead of building a release, the builder can download it already built: the database and index of a
finished build, compressed with zstd (about 440 MB for release 202611, against 1.7 GB uncompressed and half an
hour of building). For now the server uses a shared Google Drive folder by default (`DEFAULT_MIRROR` in
`src/mcp_bindingdb/builder/prebuilt.py`), until the prebuilt databases have a permanent home; the local build
is the fallback, and `$MCP_BINDINGDB_MIRROR=none` (or `none` in the Claude Desktop setting) turns the download
off. `scripts/build_duckdb.sh` always builds from the dump.

**The mirror** is a folder with three files per release, named after it:

| File | What it is |
|---|---|
| `202611.duckdb.zst` | the database, compressed with zstd |
| `202611.sslib.zst` | the structure-search index, compressed with zstd |
| `202611.json` | `release`, `db_format`, `built_at`, `source_zip_sha256`, `packaged_by`, and for `duckdb` and `sslib` the compressed `size` and `sha256` and the `raw_size` |

Adding a release is adding its three files, so the folder's link stays the same, and older releases stay
downloadable (for notebook reruns of the release they were made with).

**Using another mirror.** Set `$MCP_BINDINGDB_MIRROR` to the folder: a shared Google Drive folder's link
(`https://drive.google.com/drive/folders/<id>`), a web address the files are under (`<address>/202611.json`,
...), or a local path. In Claude Desktop, it is the extension setting **Prebuilt database folder** (empty: the
default folder); the builder also takes `--mirror`. A Google Drive folder is listed through its embedded view
(`drive.google.com/embeddedfolderview?id=<id>`, which needs no API key, only that the folder is shared with
"Anyone with the link"), and its files are downloaded from `drive.usercontent.google.com` with `confirm=t`,
which skips Drive's virus-scan page for large files. A local folder is listed too; under a web address, which
cannot be listed, a release is looked for by name (for the newest: this month's and the three before).

With a mirror, a first use takes the newest release on it that is newer than `DEFAULT_RELEASE` and in this
version's `DB_FORMAT` (read with a 5 s timeout; no mirror or no answer leaves `DEFAULT_RELEASE`). For whatever
release the builder is asked for (first use, `update_database`, a rebuild after a layout change), it first tries
the mirror: it downloads the two `.zst` files into the data folder (resuming a partial download), checks each
against the SHA-256 in the release's `.json`, decompresses them (zstd checks its own checksum; the size is
checked against `raw_size`), checks that the database is the release and layout expected, and renames the
index, then the database, into place, so a release is never complete half-written. The `.zst` files are then
deleted. If the mirror does not have the release, or anything fails, the builder logs why and builds the release
itself as usual, so a mirror only saves time. Meanwhile the tools say the database is being downloaded, with the
MB so far, and `update_database` says when an update comes from the mirror. The database is the uploaded build
itself, so its `_build_info` (release, source checksum, build date) is the build's, and notebooks check it as
usual.

**Publishing a release** (monthly, after building it):

```bash
uv run python scripts/package_prebuilt.py compress --out ~/bindingdb-mirror   # about 2 minutes
# upload 202611.duckdb.zst, 202611.sslib.zst and 202611.json to the shared folder
uv run python scripts/package_prebuilt.py check <link of the shared folder>    # lists it as the server does
```

Upload each file once: Google Drive allows two files of the same name, and the server takes the first one it
lists. Google Drive also limits how often a shared file can be downloaded in a day, which is fine for a test,
not for many users; the same files under a web address next to BindingDB's dump on bindingdb.org would work
without changes.

## Updating to a newer release

BindingDB publishes a release every month, named by year and month (`202611`), with the dump at
`https://www.bindingdb.org/rwd/bind/BDB-mySQL_All_<release>_dmp.zip`. `DEFAULT_RELEASE` in
`src/mcp_bindingdb/builder/__init__.py` is the release a new installation builds first; after that the
server uses the newest complete release in its folder (a database with its `.sslib` index).

**From a chat.** `update_database` finds the newest release on bindingdb.org (it tries this month's dump
and the three before, newest first, with HEAD requests), reports it with its download size, and with
`start=true`, which the model sends only after the user agrees, starts the same background build as on
first use, in the folder of the loaded database. The loaded database stays open and answers meanwhile;
calling the tool again reports the build's progress, or that it is done. The new release is used from the
next server start (quitting and reopening Claude Desktop), which then deletes the older releases' files
(database, index, status, log, lock and dump) from the user data folder, skipping a release whose build is
still running. A build that stopped (the computer slept, the app quit) resumes at the next server start.
This works in the user data folder and in a clone's `data/` (which the server reads the newest complete
database from, and where nothing is deleted); a database named with `--db` or `$BINDINGDB_DUCKDB` is
updated by hand.

**By hand.** In a clone, `scripts/build_duckdb.sh --release 202611` builds a release into `data/`, and the
server uses the newest complete one at its next start. Delete older `data/bindingdb_*` files when you no
longer need them.

**A new version of the server with a newer `DEFAULT_RELEASE`** builds it the same way, in the background,
answering from the newest older complete release meanwhile; its instructions tell the model so. A notebook
rerun does not fall back to an older release: it waits for the build.

## Database format

The builder records `db_format` in `_build_info`: `DB_FORMAT` in `src/mcp_bindingdb/builder/__init__.py`,
the layout of the tables and columns the server reads (databases built before it was recorded count as 1).
A version of the server that changes the layout bumps it. At its first start, the server then rebuilds the
newest release in the user data folder, the same release so that results stay comparable: it deletes that
release's old database, index and build status, and builds it again in the background (about half an hour,
downloading the dump again), with the usual progress messages, worded as a one-time rebuild. A usable release
of the current layout, if there is one, answers meanwhile; an old layout is not used, since this version's
tools may fail on it. A database in a clone's `data/` or named with `--db` or `$BINDINGDB_DUCKDB` is not
rebuilt: the server's instructions then say it is of an older layout, and `scripts/build_duckdb.sh` rebuilds
it (delete the old file first, or build another release).

## Claude Desktop bundle

`scripts/build_bundle.sh` builds `dist/mcp-bindingdb.mcpb`, an
[MCP bundle](https://github.com/modelcontextprotocol/mcpb) of about 4 MB (needs Node.js). It holds the
source, `pyproject.toml`, `uv.lock` and `bundle/manifest.json`, and no database or Python environment.
Claude Desktop runs it with uv (manifest server type `uv`), which installs the `substructure`,
`structures` and `opsin` extras from the lock file, and the server builds the database on first use as above.

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
through the optional `opsin` extra ([pyopsin](https://pypi.org/project/pyopsin/), which bundles the OPSIN
jar, and [jdk4py](https://pypi.org/project/jdk4py/), a Java runtime packaged as a Python wheel of about
30 MB, so no installed Java is needed; without jdk4py, an installed Java is used). Without the extra the
tool still uses BindingDB synonyms and PubChem. It needs no build step.
