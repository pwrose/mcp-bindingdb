# mcp-bindingdb

> **Under construction:** this project is in early development. Tools, table layouts and examples may
> change without notice.

An MCP server that lets Claude query [BindingDB](https://www.bindingdb.org): about 3.2M measured
protein–ligand binding affinities for 1.5M compounds and 13k targets, from a local, read-only copy.

## Examples

[Worked examples](https://htmlpreview.github.io/?https://github.com/sbl-sdsc/mcp-bindingdb/blob/main/examples/index.html), grouped in levels from single lookups to multi-step analyses,
show real questions answered with these tools: looking up compounds and targets, exact, similarity and
substructure search, selectivity profiles, R-group tables and matched pairs, multi-step workflows such as
a clustered selectivity heat map, 3D binding-site views, property filters and structural alerts, SQL
analytics, and saving the work as a transcript or a reproducible, rerunnable Jupyter notebook.

## Quick install: Claude Desktop bundle

1. **Download** [mcp-bindingdb.mcpb](https://github.com/sbl-sdsc/mcp-bindingdb/releases/latest/download/mcp-bindingdb.mcpb)
   (about 4 MB).
2. **Install it:** double-click the file. The first start takes about 2 minutes: Claude Desktop installs the
   Python packages the server needs, and the server then downloads the BindingDB database (see **First Chat**
   below).
3. **Allow the mcp-bindingdb tools:** select **Plugins** in the left sidebar. Click **mcp-bindingdb**, then
   **Settings**. Select **Always allow** for all tools (there are several sections).
4. **Enable mcp-bindingdb in a chat:** in a new chat, click the **+** button and enable **mcp-bindingdb**.
5. **Ask a question** in that chat, e.g. "Look up imatinib in BindingDB."

> **First Chat**
>
> **The server sets up its database on your computer.** It downloads it already built, about 440 MB, from
> mcp-bindingdb's shared folder, which takes about 2 minutes. If that fails, it downloads BindingDB's data
> from bindingdb.org and builds the database in the background instead, which takes
> about half an hour (longer on a computer with few cores). Until it is done, Claude tells you how far it has
> got: ask **"Check the BindingDB build status with mcp-bindingdb"** in the chat at any time. This happens only
> once; to get newer data later, see [Updating](#updating).
>
> The database needs about 3 GB of free disk space while it is set up and 1.8 GB afterwards, in
> `~/Library/Application Support/mcp-bindingdb` on macOS, `%LOCALAPPDATA%\mcp-bindingdb` on Windows and
> `~/.local/share/mcp-bindingdb` on Linux.

If some tools are missing in a chat, check that they are switched on: in Claude Desktop, under **Plugins** in
the left sidebar → **mcp-bindingdb**, or in the chat's tools menu.

## Updating

**BindingDB data.** BindingDB publishes a new release every month. Ask
**"Which BindingDB release does mcp-bindingdb have?"** to see which release you have and whether a newer one is
out. To update, ask Claude **"Update the BindingDB database with mcp-bindingdb"**: it checks bindingdb.org and,
if you agree, downloads the new release already built (about 440 MB, a minute or two) when mcp-bindingdb's
shared folder has it, and otherwise downloads it from bindingdb.org (about 260 MB) and builds it in the
background, in about half an hour, with about 3 GB of free disk space. Claude keeps answering from the current release meanwhile; ask
**"Check the BindingDB build status with mcp-bindingdb"** to see how far the build has got. When it is done,
quit and reopen Claude Desktop to switch to the new release; the old release's files are then deleted.

Naming mcp-bindingdb in these questions makes Claude ask the server, which alone knows; without it, Claude may
look for build files on your computer instead.

**mcp-bindingdb.** To install a new version, download
[mcp-bindingdb.mcpb](https://github.com/sbl-sdsc/mcp-bindingdb/releases/latest/download/mcp-bindingdb.mcpb)
again and double-click it; it replaces the installed one and keeps your database. To hear about new
versions, choose **Watch → Custom → Releases** on the [GitHub page](https://github.com/sbl-sdsc/mcp-bindingdb).

## Interactive structure editor

Ask **"Open the BindingDB structure editor"** in an MCP Apps-compatible chat client. Draw or edit a
molecule, paste SMILES/SMARTS, or resolve a chemical name with the existing name tool. Review an exact,
substructure or similarity search (default threshold 0.7), optionally restrict affinity in nM, and
choose **Run query** to see the results in the editor. The assistant fetches them (`get_editor_results`) when you ask about them. The sketcher and chemistry engines are bundled
with the server. See [setup and testing](docs/structure-editor.md).

## Binding-site overlays

Ask e.g. **"Overlay the crystal structures of the top 4 most potent (Ki or Kd) HIV-1 protease inhibitors"**. The server
finds the target's ligands that have PDB complexes (`find_pdb_complexes`), downloads the entries from PDBe,
superposes their binding sites on the pocket's Cα atoms, and shows them in a 3D viewer in the chat:
protein chains as lines and ligands as sticks, each switched on or off per entry, with hydrogen bonds on
request and a table of the residues each ligand touches. It also writes the superposed complexes as mmCIF
files. See [Tools](docs/tools.md#find_pdb_complexes-and-overlay_binding_site).

## Save your work

Ask e.g. **"Save this chat as a transcript"** or **"Create a Jupyter notebook that reruns this
analysis"**. A transcript is an HTML page with your prompts, Claude's answers, figures and structure
drawings; a [notebook](#jupyter-notebooks) reruns each lookup and checks that it gives the same results, so
others can reproduce your work. With the Claude Desktop bundle, both go to `Documents/BindingDB`
(changeable in the plugin's settings), along with any figures. To save them somewhere else, name the folder
in your request, e.g. "… in ~/results", or, if you attached a folder to the chat, "… in the attached
folder".

## Jupyter notebooks

A notebook turns a chat into a record that anyone can rerun, check and cite. It holds your prompts and
Claude's answers, the BindingDB tool calls behind each answer with their recorded results, any code Claude
wrote (e.g. for a plot), the figures, and where the results came from: BindingDB release and download
checksum, mcp-bindingdb version and commit, model and software versions.

**Create.** Ask at the end of an analysis, or in the same prompt:

```text
Create a Jupyter notebook named imatinib-analogues that reruns this analysis, in ~/results
```

The server writes the folder `~/results/imatinib-analogues/`, with everything the notebook needs to run on
any computer: the notebook `imatinib-analogues.ipynb` and an HTML copy to read in a browser,
`requirements.txt` (mcp-bindingdb at the commit that made it, and the exact versions of the packages it
needs), the recorded results (`data/`), the figures (`figures/`), any longer code Claude wrote as `.py`
files, and a `README.md`. Keep the folder together.

**Run.** You need only [uv](https://docs.astral.sh/uv/), not mcp-bindingdb. Claude's reply gives the command
with your paths filled in:

```bash
cd ~/results/imatinib-analogues
uv run --no-project --with-requirements requirements.txt --with jupyterlab jupyter lab imatinib-analogues.ipynb
```

Choose **Run → Run All Cells**. The cells show the recorded results, and Claude's code runs on them, so
no database is needed. **To rerun every call** on your own copy of BindingDB, set `RERUN = True` in the
first code cell (or start the command with `BINDINGDB_RERUN=1`): each call runs again and is marked
✅ (same result), ⚠️ (different) or ❌ (failed), and a table at the end sums up the checks. A rerun uses
the database in `BINDINGDB_DUCKDB=/path/to/bindingdb_<release>.duckdb`, else the one mcp-bindingdb built on
the computer, else it builds one first (about half an hour).

**Share and cite.** Send the folder: the notebook's **How to run** section tells others how to run and rerun
it; its first cell warns if their database's release differs. Its **How to cite** section lists what to
cite, e.g. when you deposit the folder with a DOI.

**Not recomputed:** Claude's answers, images made with other tools (e.g. a plot added with `add_figure`),
and results from PubChem, RCSB or PDBe, which can change. See
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
| `selectivity_matrix` | Compares 2-10 targets (a family, paralogs, a wild type and its mutants): one row per compound with its potency at each and its selectivity for the first, from one affinity type; each column's protein and gene name in the legend |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `exact_structure_search` | BindingDB entries of the same molecule (salts and stereo included), optionally only those with a measurement in an affinity range |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those with a measurement in an affinity range or with given properties, or the targets they were measured against |
| `similarity_search` | Compounds similar to a molecule, optionally only those with a measurement in an affinity range or with given properties, or the targets they were measured against |
| `decompose_r_groups` | SAR table of a series: a target's ligands containing a core, each R-group position in its own column |
| `matched_molecular_pairs` | Pairs of a target's ligands differing by one group, and what the change did to potency |
| `activity_cliffs` | Near-identical ligands of a target with very different potency |
| `cluster_ligands` | A target's ligands grouped into chemotypes, largest series first |
| `find_pdb_complexes` | A target's ligands with structures in the PDB: ligand code, entries and potency |
| `overlay_binding_site` | PDB complexes of a target's ligands superposed on the binding site, in a 3D viewer in the chat, with each ligand's contacts and hydrogen bonds |
| `open_overlay_viewer` | Opens an overlay's 3D viewer in the browser on the computer running the server, for chats that cannot show the panel (e.g. the first reply of a new Claude Desktop chat) |
| `describe_tables` | Table list with descriptions, or the columns of one table |
| `update_database` | Checks bindingdb.org for a newer monthly release and, if you agree, builds it in the background |
| `run_sql` | Any read-only SQL query |
| `create_transcript` | A record of the session as Markdown, or as an HTML page with structure drawings: your prompts and Claude's answers, and, if you ask, every BindingDB tool call with its result |
| `create_jupyter_notebook` | A Jupyter notebook that reruns the analysis: prompts, answers, each BindingDB tool call with its recorded result, figures, the BindingDB release and software versions, in a folder that runs anywhere with uv; rerun, it checks every result against the recorded one |
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

All tools are read-only, apart from the transcripts, notebooks and figures, which are written to files, and
`update_database`, which builds a newer release next to the database. Only `chemical_name_to_smiles` (PubChem),
`overlay_binding_site` (PDBe, RCSB) and `update_database` (bindingdb.org) use the network.
See [Tools](docs/tools.md) for how the searches work and notes on the data.

## More

- [Install from source](docs/install-from-source.md): Claude Desktop without the bundle, Claude Code
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
  url={https://github.com/sbl-sdsc/mcp-bindingdb}
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
