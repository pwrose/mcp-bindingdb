# mcp-bindingdb

> **Under construction:** this project is in early development. Tools, table layouts and examples may
> change without notice.

An MCP server that lets Claude query [BindingDB](https://www.bindingdb.org): about 3.2M measured
protein–ligand binding affinities for 1.5M compounds and 13k targets, from a local, read-only copy.

## Examples

[Worked examples](examples/README.md), grouped in levels from single lookups to multi-step analyses,
show real questions answered with these tools: looking up compounds and targets, exact, similarity and
substructure search, selectivity profiles, R-group tables and matched pairs, multi-step workflows such as
a clustered selectivity heat map, 3D binding-site views, property filters and structural alerts, SQL
analytics, and saving the work as a transcript. Each is an HTML transcript with the prompt, the answer,
its figures and structure drawings
([index](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/index.html)).

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

   **Claude Desktop:** let Claude do it. Paste this prompt into a new Claude Desktop chat, and allow
   Claude to change the file when it asks:

   ```text
   Add the mcp-bindingdb MCP server to my Claude Desktop configuration.

   1. Find the mcp-bindingdb folder I cloned from GitHub: it contains a pyproject.toml with
      name = "mcp-bindingdb". If you find none, or more than one, ask me which folder to use.
   2. Find the full path of the uv program (`which uv` on macOS, `where uv` on Windows). Claude
      Desktop may not find "uv" by name, so use the full path.
   3. Open Claude Desktop's config file: ~/Library/Application Support/Claude/claude_desktop_config.json
      on macOS, %APPDATA%\Claude\claude_desktop_config.json on Windows. If it exists, save a backup copy
      next to it first; if it does not exist, create it.
   4. Inside "mcpServers" (create it if missing), add or replace only this entry, keeping every other
      server and setting exactly as it is:
        "mcp-bindingdb": {
          "command": "<full path of uv>",
          "args": ["--directory", "<the mcp-bindingdb folder>", "run", "--extra", "substructure",
                   "--extra", "name", "--extra", "structures", "mcp-bindingdb"]
        }
   5. Check that the file is still valid JSON, then show me the mcp-bindingdb entry and where the
      backup is. Do not restart Claude yourself.
   ```

   Then:

   1. **Restart Claude Desktop:** quit it completely (⌘Q on macOS; on Windows, quit it from the system
      tray) and open it again. Closing the window is not enough.
   2. **Allow the BindingDB tools:** open Claude → Settings → Plugins → mcp-bindingdb and set its tools
      to **Always allow**, so Claude can look things up without asking you before every search. If you
      skip this, choose **Always allow** the first time Claude asks to use a BindingDB tool.
   3. **Check it works:** in a new chat, ask "Look up imatinib in BindingDB."

   **Claude Code:** the repository's `.mcp.json` registers the server when you run `claude` in this
   folder. To use it from any folder:

   ```bash
   claude mcp add --scope user mcp-bindingdb -- uv --directory /path/to/mcp-bindingdb run --extra substructure --extra name --extra structures mcp-bindingdb
   ```

If some tools are missing in a chat, check that they are switched on: in Claude Desktop, under Claude →
Settings → Plugins → mcp-bindingdb, or in the chat's tools menu.

## Interactive structure editor

Ask **"Open the BindingDB structure editor"** in an MCP Apps-compatible chat client. Draw or edit a
molecule, paste SMILES/SMARTS, or resolve a chemical name with the existing name tool. Review an exact,
substructure or similarity search (default threshold 0.7), optionally restrict affinity in nM, and
choose **Run query** to see the results in the editor. The assistant fetches them (`get_editor_results`) when you ask about them. The sketcher and chemistry engines are bundled
with the server. See [setup and testing](docs/structure-editor.md).

## Binding-site overlays

Ask e.g. **"Overlay the crystal structures of the most potent HIV-1 protease inhibitors"**. The server
finds the target's ligands that have PDB complexes (`find_pdb_complexes`), downloads the entries from PDBe,
superposes their binding sites on the pocket's Cα atoms, and shows them in a 3D viewer in the chat:
protein chains as lines and ligands as sticks, each switched on or off per entry, with hydrogen bonds on
request and a table of the residues each ligand touches. It also writes the superposed complexes as mmCIF
files. See [Tools](docs/tools.md#find_pdb_complexes-and-overlay_binding_site).

## Tools

| Tool | Purpose |
|---|---|
| `open_structure_editor` | Interactive in-chat sketcher that runs exact, substructure and similarity searches |
| `get_editor_results` | Results of the searches the user ran in the structure editor, for follow-up questions |
| `search_compounds` | Find compounds by name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey |
| `chemical_name_to_smiles` | SMILES for a compound name (trade name, IUPAC name, CAS number), with the BindingDB compounds that have that structure |
| `search_targets` | Find targets by name, gene name, UniProt entry name or accession |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets, properties (MW, cLogP, QED, ...), scaffold and structural alerts (PAINS, Brenk, NIH) |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target, with ligand efficiency and LipE; filtered by properties (e.g. MW, Ro5, no PAINS, a scaffold), ranked by efficiency, or grouped by scaffold |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `exact_structure_search` | BindingDB entries of the same molecule (salts and stereo included), optionally only those with a measurement in an affinity range |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those with a measurement in an affinity range or with given properties, or the targets they were measured against |
| `similarity_search` | Compounds similar to a molecule, optionally only those with a measurement in an affinity range or with given properties, or the targets they were measured against |
| `decompose_r_groups` | SAR table of a series: a target's ligands containing a core, each R-group position in its own column |
| `matched_molecular_pairs` | Pairs of a target's ligands differing by one group, and what the change did to potency |
| `activity_cliffs` | Near-identical ligands of a target with very different potency |
| `find_pdb_complexes` | A target's ligands with structures in the PDB: ligand code, entries and potency |
| `overlay_binding_site` | PDB complexes of a target's ligands superposed on the binding site, in a 3D viewer in the chat, with each ligand's contacts and hydrogen bonds |
| `open_overlay_viewer` | Opens an overlay's 3D viewer in the browser on the computer running the server, for chats that cannot show the panel (e.g. the first reply of a new Claude Desktop chat) |
| `describe_tables` | Table list with descriptions, or the columns of one table |
| `run_sql` | Any read-only SQL query |
| `create_transcript` | A record of the session as Markdown, or as an HTML page with structure drawings: your prompts and Claude's answers, and, if you ask, every BindingDB tool call with its result |
| `create_jupyter_notebook` | A Jupyter notebook that reruns the analysis: prompts, answers, each BindingDB tool call with its recorded result, figures, the BindingDB release and software versions; run, it checks every result against the recorded one |
| `draw_structure_grid` | Compounds side by side, aligned on a shared substructure, with binding bars for their main targets |
| `draw_r_group_table` | An R-group table of one series: the core drawn with R1, R2, … named, then a row per compound with its substituents drawn and its potency |
| `add_figure` | Adds an image made with other tools (e.g. a matplotlib plot) as a figure for transcripts |
| `transcript_to_html` | Turns an existing Markdown transcript into an HTML page with structure drawings |
| `get_tool_log` | List the logged tool calls, so a transcript includes only this chat's |
| `reset_tool_log` | Start a new transcript log |

Ask for a transcript at the end of a chat, e.g. "create a transcript of this session as a .md file", or
"create an HTML transcript" for a page with the structures drawn. Name a folder ("... in
~/results/heatmap") and the server writes the files there; otherwise they go to `data/transcripts/`
(change this with `--transcript-dir` or `MCP_BINDINGDB_TRANSCRIPT_DIR`).
Add "with the tool calls" to include every BindingDB lookup and its result.

To let others rerun and check the work, ask for a notebook: "create a Jupyter notebook that reruns this
analysis". It records each prompt, the tool calls behind each answer with their results, the figures, the
BindingDB release (with the checksum of the download it was built from) and the server's commit; run in
Jupyter, it calls the same tools on your copy of the database and marks each result ✅ when it matches the
recorded one (install the `notebook` extra for the Jupyter kernel). See
[Reproducible notebooks](docs/tools.md#create_jupyter_notebook).

All tools are read-only, apart from the transcripts, notebooks and figures, which are written to files. Only `chemical_name_to_smiles` (PubChem) and `overlay_binding_site` (PDBe, RCSB) use the network.
See [Tools](docs/tools.md) for how the searches work and notes on the data.

## More

- [Building the database](docs/building-the-database.md): releases, derived tables, structure-search index
- [Tools](docs/tools.md): tool details, safety, data notes
- [Development](docs/development.md): running the server by hand, server options, tests, examples

## License

BSD 3-Clause; see [LICENSE](LICENSE). BindingDB data are subject to
[BindingDB's own terms](https://www.bindingdb.org).
