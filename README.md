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

## Quick install: Claude Desktop bundle

The easiest way to try it: no terminal, Docker or clone needed.

1. **Download** [mcp-bindingdb.mcpb](https://github.com/pwrose/mcp-bindingdb/releases/latest/download/mcp-bindingdb.mcpb)
   (about 4 MB).
2. **Install it:** double-click the file, or drag it onto Claude Desktop's Settings → Extensions page, then
   click **Install**. The first start takes a minute or two while Claude Desktop installs the Python
   packages the server needs.
3. **Allow the BindingDB tools:** set them to **Always allow** in the extension's settings, or choose
   **Always allow** the first time Claude asks to use one.
4. **Ask a question** in a new chat, e.g. "Look up imatinib in BindingDB." The first time, the server builds
   its database on your computer: it downloads BindingDB's data (258 MB) from bindingdb.org and converts it in
   the background, which takes about half an hour (longer on a computer with few cores). Until it is done,
   Claude tells you how far it has got; ask again when it is finished. This happens only once.

The database needs about 3 GB of free disk space while it is built and 2.2 GB afterwards, in
`~/Library/Application Support/mcp-bindingdb` on macOS, `%LOCALAPPDATA%\mcp-bindingdb` on Windows and
`~/.local/share/mcp-bindingdb` on Linux. Transcripts, figures and notebooks go to `Documents/BindingDB`
(changeable in the extension's settings). The bundle leaves out OPSIN's offline IUPAC-name parsing, which
needs Java; names are still looked up in PubChem. To build the bundle yourself, run
`scripts/build_bundle.sh` (see [Building the database](docs/building-the-database.md#claude-desktop-bundle)).

## Claude setup

1. **Install** [uv](https://docs.astral.sh/uv/), and optionally a Java runtime (for IUPAC-name parsing).
   Then clone the repository:

   ```bash
   git clone https://github.com/pwrose/mcp-bindingdb.git
   cd mcp-bindingdb
   ```

2. **Build the database** (downloads BindingDB's dump; about half an hour, and 2.4 GB of disk space):

   ```bash
   scripts/build_duckdb.sh
   ```

   You can also skip this step: without a database, the server builds the same one on first use, in the
   per-user folder above. See [Building the database](docs/building-the-database.md) for releases and options.

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

## Jupyter notebooks

A notebook turns a chat into a record that anyone can rerun, check and cite. It holds each of your
prompts, the BindingDB tool calls behind each answer with their results as recorded, any code Claude wrote
for the analysis (e.g. for a plot), Claude's answers, the figures, and where the results came from: the BindingDB release (with the checksum of the download
the database was built from), the mcp-bindingdb version and commit, the model, and the software versions.

### Create a notebook in a chat

At the end of an analysis, or in the same prompt, ask for one and name the folder to put it in:

```text
Create a Jupyter notebook named imatinib-analogues that reruns this analysis, in ~/results
```

Claude picks this chat's tool calls, places each under the answer it was made for, and the server writes
the notebook, here `~/results/imatinib-analogues.ipynb`. Without a folder it goes to `data/transcripts/`
in the mcp-bindingdb folder. The notebook opens with the results as they were recorded, so it can be read
without running anything.

Next to it the server saves an HTML copy, here `~/results/imatinib-analogues.html`, to read or share in any
web browser. Code Claude wrote is in the notebook if it is short; longer code is saved as `.py` files in the
same folder, which the notebook imports, so keep them together. Claude's reply gives the command to open the notebook in JupyterLab, with your paths filled in.

### Run a notebook

Jupyter has to run in mcp-bindingdb's Python environment, so start it from the mcp-bindingdb folder:

```bash
cd /path/to/mcp-bindingdb
uv run --all-extras --with jupyterlab jupyter lab ~/results/imatinib-analogues.ipynb
```

Then choose **Run → Run All Cells**. Each tool call runs again on your copy of the database and is
marked ✅ when its result matches the recorded one, ⚠️ when it differs, or ❌ when it fails; structure
grids and R-group tables are drawn again, and a table at the end sums up the checks. To rerun a
notebook without opening Jupyter, writing a copy with the new results:

```bash
cd /path/to/mcp-bindingdb
uv run --all-extras --with nbconvert jupyter nbconvert --to notebook --execute \
  --output imatinib-analogues-rerun.ipynb ~/results/imatinib-analogues.ipynb
```

The database is found in the folder's `data/`; if it is elsewhere, start the commands with
`BINDINGDB_DUCKDB=/path/to/bindingdb_<release>.duckdb`. VS Code works too, with the folder's `.venv`
as the kernel.

### Share and cite a notebook

Someone without mcp-bindingdb can rerun a notebook after cloning this repository at the commit the
notebook names and building the same BindingDB release; the notebook's **How to rerun** section has the
exact commands, and its first cell warns if the database is a different release or build. Its **How to
cite** section lists the data, software and analysis to cite with it, for example when it is deposited
with a DOI.

Some things are not recomputed: Claude's answers are text and are kept as written, images made with other
tools (e.g. a matplotlib plot added with `add_figure`) are kept as recorded, and results from PubChem,
RCSB or PDBe can change as those services change. See
[create_jupyter_notebook](docs/tools.md#create_jupyter_notebook) for how results are compared.

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
~/results/heatmap") and the server writes the files there; otherwise they go to `data/transcripts/`, or to
`Documents/BindingDB` with the Claude Desktop bundle (change this with `--transcript-dir`,
`MCP_BINDINGDB_TRANSCRIPT_DIR` or the bundle's Results folder setting).
Add "with the tool calls" to include every BindingDB lookup and its result.

To let others rerun and check the work, ask for a [Jupyter notebook](#jupyter-notebooks) instead.

All tools are read-only, apart from the transcripts, notebooks and figures, which are written to files. Only `chemical_name_to_smiles` (PubChem) and `overlay_binding_site` (PDBe, RCSB) use the network.
See [Tools](docs/tools.md) for how the searches work and notes on the data.

## More

- [Building the database](docs/building-the-database.md): releases, derived tables, structure-search index
- [Tools](docs/tools.md): tool details, safety, data notes
- [Development](docs/development.md): running the server by hand, server options, tests, examples

## License

BSD 3-Clause; see [LICENSE](LICENSE). BindingDB data are subject to
[BindingDB's own terms](https://www.bindingdb.org).

## Citation

If you use this server in your work, please cite it:

```bibtex
@software{rose2026mcp-bindingdb,
  title={MCP BindingDB Server},
  author={Rose, P.W.},
  year={2026},
  url={https://github.com/pwrose/mcp-bindingdb}
}
```

Please also cite BindingDB, the source of the data; RDKit, which the server uses for structure search,
properties and drawings (add the RDKit version you used, e.g. `version={2026.03}`); 3Dmol.js, the 3D
viewer of binding-site overlays; and JSME, the structure editor's drawing widget:

```bibtex
@article{liu2025bindingdb,
  title={BindingDB in 2024: a FAIR knowledgebase of protein-small molecule binding data},
  author={Liu, T. and Hwang, L. and Burley, S.K. and Nitsche, C.I. and Southan, C. and Walters, W.P. and Gilson, M.K.},
  journal={Nucleic Acids Research},
  volume={53},
  number={D1},
  pages={D1633--D1644},
  year={2025},
  doi={10.1093/nar/gkae1075}
}

@software{rdkit,
  title={RDKit: Open-source cheminformatics},
  author={Landrum, G. and others},
  url={https://www.rdkit.org},
  doi={10.5281/zenodo.591637}
}

@article{rego2015_3dmol,
  title={3Dmol.js: molecular visualization with WebGL},
  author={Rego, N. and Koes, D.},
  journal={Bioinformatics},
  volume={31},
  number={8},
  pages={1322--1324},
  year={2015},
  doi={10.1093/bioinformatics/btu829}
}

@article{bienfait2013jsme,
  title={JSME: a free molecule editor in JavaScript},
  author={Bienfait, B. and Ertl, P.},
  journal={Journal of Cheminformatics},
  volume={5},
  pages={24},
  year={2013},
  doi={10.1186/1758-2946-5-24}
}
```
