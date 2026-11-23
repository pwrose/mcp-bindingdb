# Development

## Run the server

```bash
uv run --extra substructure --extra opsin --extra structures mcp-bindingdb   # stdio
uv run --extra substructure --extra opsin --extra structures mcp-bindingdb --transport streamable-http --port 8000
uv run mcp-bindingdb                                     # without RDKit, OPSIN and gemmi
```

| Option | Effect |
|---|---|
| `--db PATH` | DuckDB file (default: `$BINDINGDB_DUCKDB`, else the newest `data/bindingdb_*.duckdb`, else the database it [builds on first use](building-the-database.md#build-on-first-use) in the user data folder) |
| `--transport stdio\|streamable-http` | Transport (default stdio) |
| `--host`, `--port` | Address for streamable-http (default 127.0.0.1:8000) |
| `--timeout SECONDS` | Per-query time limit (default 30) |

The `substructure` extra (RDKit) enables `substructure_search` and `similarity_search`, which also
need the index, and `exact_structure_search`, `draw_structure_grid`, `draw_r_group_table` and the SAR tools
(`decompose_r_groups`, `matched_molecular_pairs`, `activity_cliffs`), which do not; the `name`
extra (pyopsin, and jdk4py for a Java runtime) enables OPSIN in `chemical_name_to_smiles`; the `structures` extra (gemmi)
enables `find_pdb_complexes` and `overlay_binding_site`; the `notebook` extra (ipykernel) is installed with
the other extras in the environment of a notebook `create_jupyter_notebook` writes. See
[Building the database](building-the-database.md).

## Tests

```bash
uv run pytest
uv run pytest -m "not network"   # without the live PubChem and PDBe tests
```

The tests run against the built database and are skipped if it is missing.

## Changing the database layout

When a change to the builder adds, removes or changes tables or columns the server reads, bump `DB_FORMAT` in
`src/mcp_bindingdb/builder/__init__.py`. Users' databases are then rebuilt at the server's next start
([Database format](building-the-database.md#database-format)); rebuild your own `data/` database with
`scripts/build_duckdb.sh` after deleting it. Changes that only add data the server checks for (as it does
for `compound_property`, through `_build_info`) need no bump.

## Examples

`examples/` holds HTML transcripts written by `create_transcript` in Claude sessions, grouped in
levels (see the [index](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/index.html)). They are not regenerated when the data release
changes. They are written in a working folder (default `~/mcp-bindingdb-examples`, one folder per level)
and copied here with

```bash
python3 scripts/sync_examples.py --dry-run   # list what would change
python3 scripts/sync_examples.py             # copy, then write examples/index.html
```

The sync replaces each `examples/<level>/` folder with the working copy, rebuilds the index, and
warns about files that contain absolute local paths; it does not commit. Level headings live in `LEVELS`
in the script. `--index-only <folder>` writes the working folder's own index, with relative links.
