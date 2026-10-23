# mcp-bindingdb

> **Under construction:** this project is in early development. Tools, table layouts and examples may
> change without notice.

An MCP server that lets Claude query [BindingDB](https://www.bindingdb.org): about 3.2M measured
protein–ligand binding affinities for 1.5M compounds and 13k targets, from a local, read-only copy.

## Examples

[Seventeen worked examples](examples/README.md) show real questions answered with these tools, such as
the most potent EGFR ligands, imatinib's selectivity profile, analogues of palbociclib, the targets of a
chemotype, and turning a chemical name into a structure. Each shows the tool calls, the results and the
answer.

## Claude setup

1. **Install** [uv](https://docs.astral.sh/uv/) and [Docker](https://www.docker.com) (needed only to build
   the database), and optionally a Java runtime (for IUPAC-name parsing). Then clone the repository:

   ```bash
   git clone https://github.com/pwrose/mcp-bindingdb.git
   cd mcp-bindingdb
   ```

2. **Build the database** (downloads the BindingDB dump; needs about 5 GB of disk space):

   ```bash
   scripts/build_duckdb.sh
   ```

   See [Building the database](docs/building-the-database.md) for releases and options.

3. **Add the server to Claude.**

   **Claude Desktop:** add this to `claude_desktop_config.json` (Settings → Developer → Edit Config) and
   restart Claude:

   ```json
   {
     "mcpServers": {
       "mcp-bindingdb": {
         "command": "uv",
         "args": ["--directory", "/path/to/mcp-bindingdb", "run", "--extra", "substructure", "--extra", "name",
                  "mcp-bindingdb"]
       }
     }
   }
   ```

   **Claude Code:** the repository's `.mcp.json` registers the server when you run `claude` in this
   folder. To use it from any folder:

   ```bash
   claude mcp add --scope user mcp-bindingdb -- uv --directory /path/to/mcp-bindingdb run --extra substructure --extra name mcp-bindingdb
   ```

If some tools are missing in a chat, check that they are switched on in the chat's tools menu.

## Tools

| Tool | Purpose |
|---|---|
| `search_compounds` | Find compounds by name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey |
| `chemical_name_to_smiles` | SMILES for a compound name (trade name, IUPAC name, CAS number), with the BindingDB compounds that have that structure |
| `search_targets` | Find targets by name, gene name, UniProt entry name or accession |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, or the targets they were measured against |
| `similarity_search` | Compounds similar to a molecule, or the targets they were measured against |
| `describe_tables` | Table list with descriptions, or the columns of one table |
| `run_sql` | Any read-only SQL query |
| `create_transcript` | A record of the session as Markdown, or as an HTML page with structure drawings: your prompts and Claude's answers, then every BindingDB tool call with its result |
| `reset_tool_log` | Start a new transcript log |

Ask for a transcript at the end of a chat, e.g. "create a transcript of this session and save it as a .md file",
or "create an HTML transcript with structures" (written to `data/transcripts/`).

All tools are read-only. Only `chemical_name_to_smiles` uses the network, to look names up in PubChem.
See [Tools](docs/tools.md) for how the searches work and notes on the data.

## More

- [Building the database](docs/building-the-database.md): releases, derived tables, structure-search index
- [Tools](docs/tools.md): tool details, safety, data notes
- [Development](docs/development.md): running the server by hand, server options, tests, regenerating examples

## License

BSD 3-Clause; see [LICENSE](LICENSE). BindingDB data are subject to
[BindingDB's own terms](https://www.bindingdb.org).
