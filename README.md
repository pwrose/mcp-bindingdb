# mcp-bindingdb

> **Under construction:** this project is in early development. Tools, table layouts and examples may
> change without notice.

An MCP server that lets Claude query [BindingDB](https://www.bindingdb.org): about 3.2M measured
protein–ligand binding affinities for 1.5M compounds and 13k targets, from a local, read-only copy.

## Examples

[Worked examples](https://htmlpreview.github.io/?https://github.com/pwrose/mcp-bindingdb/blob/main/examples/index.html), grouped in levels from single lookups to multi-step analyses,
show real questions answered with these tools: looking up compounds and targets, exact, similarity and
substructure search, selectivity profiles, R-group tables and matched pairs, multi-step workflows such as
a clustered selectivity heat map, 3D binding-site views, property filters and structural alerts, SQL
analytics, and saving the work as a transcript or a reproducible, rerunnable Jupyter notebook.

## Quick install: Claude Desktop bundle

1. **Download** [mcp-bindingdb.mcpb](https://github.com/pwrose/mcp-bindingdb/releases/latest/download/mcp-bindingdb.mcpb)
   (about 4 MB).
2. **Install it:** double-click the file. The first start takes a minute or two while Claude Desktop
   installs the Python packages the server needs.
3. **Allow the mcp-bindingdb tools:** select **Plugins** in the left sidebar. Click **mcp-bindingdb**, then
   **Settings**. Select **Always allow** for all tools (there are several sections).
4. **Enable mcp-bindingdb in a chat:** in a new chat, click the **+** button and enable **mcp-bindingdb**.
5. **Ask a question** in that chat, e.g. "Look up imatinib in BindingDB."

> **First Chat**
>
> **The server builds its database on your computer.** It downloads BindingDB's data from
> bindingdb.org and converts it in the background, which takes about half an hour (longer on
> a computer with few cores). Until it is done, Claude tells you how far it has got; ask again when it is
> finished. This happens only once; to get newer data later, see [Updating](#updating).
>
> The database needs about 3 GB of free disk space while it is built and 1.8 GB afterwards, in
> `~/Library/Application Support/mcp-bindingdb` on macOS, `%LOCALAPPDATA%\mcp-bindingdb` on Windows and
> `~/.local/share/mcp-bindingdb` on Linux.

If some tools are missing in a chat, check that they are switched on: in Claude Desktop, under **Plugins** in
the left sidebar → **mcp-bindingdb**, or in the chat's tools menu.

## Updating

**BindingDB data.** BindingDB publishes a new release every month. Ask Claude **"Update the BindingDB
database"**: it checks bindingdb.org and, if you agree, downloads the new release (about 260 MB) and builds
it in the background, in about half an hour, with about 3 GB of free disk space. Claude keeps answering from
the current release meanwhile; ask again to see how far the build has got. When it is done, quit and reopen
Claude Desktop to switch to the new release; the old release's files are then deleted.

**mcp-bindingdb.** To install a new version, download
[mcp-bindingdb.mcpb](https://github.com/pwrose/mcp-bindingdb/releases/latest/download/mcp-bindingdb.mcpb)
again and double-click it; it replaces the installed one and keeps your database. To hear about new
versions, choose **Watch → Custom → Releases** on the [GitHub page](https://github.com/pwrose/mcp-bindingdb).

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

The server writes `imatinib-analogues.ipynb` and an HTML copy to read in a browser. Longer code goes into
`.py` files next to them, so keep the folder together. The notebook opens with the recorded results, so it
can be read without running it.

**Run.** Claude's reply gives the command to open the notebook in JupyterLab, with your paths filled in.
For a [source install](docs/install-from-source.md#run-a-notebook) it is:

```bash
cd /path/to/mcp-bindingdb
uv run --all-extras --with jupyterlab jupyter lab ~/results/imatinib-analogues.ipynb
```

Choose **Run → Run All Cells**. Each tool call runs again on your database and is marked ✅ (same result),
⚠️ (different) or ❌ (failed); a table at the end sums up the checks. If the database is not in the
folder's `data/`, start the command with `BINDINGDB_DUCKDB=/path/to/bindingdb_<release>.duckdb`.

**Share and cite.** The notebook's **How to rerun** section tells others how to rerun it (clone this
repository at the commit it names and build the same BindingDB release); its first cell warns if the
release differs. Its **How to cite** section lists what to cite, e.g. when you deposit it with a DOI.

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
| `update_database` | Checks bindingdb.org for a newer monthly release and, if you agree, builds it in the background |
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
