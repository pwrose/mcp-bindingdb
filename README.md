# mcp-bindingdb

> **Under construction:** this project is in early development. Tools, table layouts and examples may
> change without notice.

An MCP server for querying [BindingDB](https://www.bindingdb.org) (about 3.2M measured protein–ligand
binding affinities) from a local, read-only DuckDB build of the monthly MySQL dump.

## Build the database

Requires Docker (daemon running) and [uv](https://docs.astral.sh/uv/).

```bash
scripts/build_duckdb.sh                    # release 202610 -> data/bindingdb_202610.duckdb
scripts/build_duckdb.sh --release 202611   # a later release
```

The script downloads the dump, loads it into a temporary MySQL 8.4 container, copies it to DuckDB
(`scripts/convert_to_duckdb.py`, checking row counts), adds derived query tables
(`scripts/add_derived_tables.py`), builds the substructure index (below), and removes the container.
The `regusers` and `person` tables (passwords and contact details) are left out unless you pass
`--include-pii`.

Derived tables:

| Table | Contents |
|---|---|
| `activity` | One row per measured value: `affinity_type`, `relation` (`=`, `<`, `>`), numeric `value`, `unit`, `p_affinity`, plus compound, target, assay and citation columns |
| `compound` | One row per small molecule: preferred name, InChIKey, SMILES, formula, weight, counts |
| `compound_name` | Compound synonyms, including ChEMBL ids, PubChem `cid_N` and patent labels |
| `target` | One row per polymer/complex target: bare UniProt accession, organism, counts |
| `target_name` | Target synonyms (gene names, UniProt entry names) |

### Substructure index

`substructure_search` needs [RDKit](https://www.rdkit.org) (the optional `substructure` extra) and an
index file, `data/bindingdb_<release>.sslib`. The build script creates it unless you pass
`--no-substructure`; to build it for an existing database:

```bash
uv run --extra substructure python scripts/build_substructure_index.py data/bindingdb_202610.duckdb
```

The index holds the canonical SMILES and an RDKit pattern fingerprint of each compound (about 480 MB
for release 202610, built in about a minute on 10 cores; 1,668 SMILES that RDKit cannot parse are
left out). The server loads it into an RDKit `SubstructLibrary` at startup, which takes about 8 s and
1.2 GB of memory. Without RDKit or the index, or if the index is for a different release, the server
runs without `substructure_search`.

## Run the server

```bash
uv run --extra substructure mcp-bindingdb             # stdio
uv run --extra substructure mcp-bindingdb --transport streamable-http --port 8000
uv run mcp-bindingdb                                  # without RDKit (no substructure_search)
```

The database is the newest `data/bindingdb_*.duckdb`, or `--db PATH` / `$BINDINGDB_DUCKDB`.

**Claude Code:** `.mcp.json` in this repo registers the server for the project.
**Claude Desktop:** add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-bindingdb": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-bindingdb", "run", "--extra", "substructure", "mcp-bindingdb"]
    }
  }
}
```

## Tools

| Tool | Purpose |
|---|---|
| `search_compounds` | By name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey (full or first block) |
| `search_targets` | By name, gene name, UniProt entry name or accession; optional organism filter |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target (by id or UniProt accession, optional variants) |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `describe_tables` | Table list with descriptions, or columns and sample rows of one table |
| `run_sql` | Arbitrary read-only DuckDB SQL |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those measured against a target with potency filters; every target the matching compounds hit, with compounds per target; or a count of matches (needs the substructure index) |

All tools are read-only. The connection is opened read-only with file, network and extension access
disabled and settings locked, so `run_sql` cannot write data or read anything outside the database.
Queries time out after 30 s (`--timeout`).

`substructure_search` reads a SMILES query by default, so Kekulé and aromatic forms of a ring match
the same compounds. It uses SMARTS when the query contains `*`, is not valid SMILES, is written
aromatic but is not a valid aromatic molecule (such as a ring nitrogen missing its H), or has a bracket
atom without H such as `[#7]` (which SMILES would make a radical). A SMILES query
ignores H counts written in brackets; pass `query_type="smarts"` to enforce them. The result echoes
how the query was read. Without a target, results are capped at `limit` and favour the compounds with
the most measurements. With a target, every compound measured against it is searched and the matches
are ranked by potency. A search stops at 80% of the query time limit and reports partial results;
counting a very generic query (a benzene ring matches 1.28M compounds) takes about 5 s.

## Data notes

- Ki/Kd/IC50/EC50 are in nM, kon in M⁻¹s⁻¹, koff in s⁻¹; `p_affinity = 9 − log10(nM)`.
- `>` values (e.g. `>10000`) usually mean inactive at the highest concentration tested; potency filters exclude them.
- `monomer.display_name` holds only the BDBM id; names are in `compound_name` / `compound.name`.
- `monomer.chembl_id` is empty in this release; ChEMBL ids appear as synonyms instead.
- Mutant and construct targets are separate rows sharing a UniProt accession (`uniprot_raw` like `P00533[L858R]`).
- Text comparisons in DuckDB are case-sensitive (MySQL's were not): use `ILIKE` or `lower()`.

## Examples

`examples/` has thirteen transcripts of real questions answered with these tools: each one shows the tool
calls, the results, and an answer. Regenerate them after a new release with
`uv run python scripts/generate_examples.py`. Hand-written answers are kept, and the script lists any
example whose results have changed so its answer can be reviewed. There is also an HTML report, a
chemotype map of CDK2/cyclin A2 inhibitors (example 13), which is not regenerated by the script.

## Tests

```bash
uv run pytest
```

## License

BSD 3-Clause; see [LICENSE](LICENSE). BindingDB data are subject to
[BindingDB's own terms](https://www.bindingdb.org).
