# Development

## Run the server

```bash
uv run --extra substructure --extra name mcp-bindingdb   # stdio
uv run --extra substructure --extra name mcp-bindingdb --transport streamable-http --port 8000
uv run mcp-bindingdb                                     # without RDKit and OPSIN
```

| Option | Effect |
|---|---|
| `--db PATH` | DuckDB file (default: `$BINDINGDB_DUCKDB` or the newest `data/bindingdb_*.duckdb`) |
| `--transport stdio\|streamable-http` | Transport (default stdio) |
| `--host`, `--port` | Address for streamable-http (default 127.0.0.1:8000) |
| `--timeout SECONDS` | Per-query time limit (default 30) |
| `--no-network` | Do not look names up in PubChem (`chemical_name_to_smiles`) |

The `substructure` extra (RDKit) enables `substructure_search` and `similarity_search`, which also
need the index, and `exact_structure_search`, `draw_structure_grid`, `draw_r_group_table` and the SAR tools
(`decompose_r_groups`, `matched_molecular_pairs`, `activity_cliffs`), which do not; the `name`
extra (pyopsin, needs Java) enables OPSIN in `chemical_name_to_smiles`. See
[Building the database](building-the-database.md).

## Tests

```bash
uv run pytest
uv run pytest -m "not network"   # without the live PubChem test
```

The tests run against the built database and are skipped if it is missing.

## Examples

`examples/` holds HTML transcripts written by `create_transcript` in Claude sessions, grouped in eight
levels (see [examples/README.md](../examples/README.md)). They are not regenerated when the data release
changes. They are written in a working folder (default `~/mcp-bindingdb-examples`, one folder per level)
and copied here with

```bash
python3 scripts/sync_examples.py --dry-run   # list what would change
python3 scripts/sync_examples.py             # copy, then write examples/index.html and examples/README.md
```

The sync replaces each `examples/<level>/` folder with the working copy, rebuilds the index and README, and
warns about files that contain absolute local paths; it does not commit. Level headings live in `LEVELS`
in the script. `--index-only <folder>` writes the working folder's own index, with relative links.
