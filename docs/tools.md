# Tools

| Tool | Purpose |
|---|---|
| `search_compounds` | By name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey (full or first block) |
| `chemical_name_to_smiles` | SMILES for a compound name (trade name, IUPAC name, CAS number) from BindingDB synonyms, OPSIN or PubChem, with the BindingDB compounds that have that structure |
| `search_targets` | By name, gene name, UniProt entry name or accession; optional organism filter |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets; properties, scaffold and structural alerts |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target (by id or UniProt accession, optional variants), with ligand efficiency and LipE; filtered by properties, ranked by efficiency, or grouped by scaffold |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `describe_tables` | Table list with descriptions, or columns and sample rows of one table |
| `run_sql` | Arbitrary read-only DuckDB SQL |
| `exact_structure_search` | BindingDB entries of the same molecule (all fragments, stereo, charges, isotopes), optionally only those with a measurement in an affinity range (needs RDKit, not the index) |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those with a measurement in an affinity range, with given properties, or measured against a target; every target the matching compounds hit, with compounds per target; or a count of matches (needs the structure-search index) |
| `similarity_search` | Compounds similar to a molecule (Tanimoto on Morgan fingerprints) above a threshold, with the same affinity, property and target filters and per-target summary (needs the structure-search index) |
| `decompose_r_groups` | SAR table of one series: a target's ligands containing a core, with each R-group position in its own column and the compound's potency (needs RDKit) |
| `matched_molecular_pairs` | Pairs of a target's ligands differing by one group, with the effect on potency; or one row per transformation (needs RDKit) |
| `activity_cliffs` | Pairs of a target's ligands that are structurally close but far apart in potency, by SALI (needs RDKit) |
| `get_editor_results` | Results of the searches the user ran in the structure editor ([structure-editor.md](structure-editor.md)): the tool, its arguments and its result, by `editor_id` |
| `create_transcript` | Markdown, HTML (with structure drawings) or JSON transcript of the session: prompts and answers, optionally followed by the logged tool calls with their results |
| `draw_structure_grid` | Compounds side by side, aligned on a shared core that is highlighted, with binding bars per target; shown in the chat and included in transcripts (needs RDKit) |
| `draw_r_group_table` | An R-group table of one series: the core with its positions named R1, R2, …, then a row per compound whose cells are its substituents, drawn, with binding bars (needs RDKit) |
| `add_figure` | Adds an image made with other tools (e.g. a matplotlib plot) as a figure for transcripts |
| `transcript_to_html` | Converts an existing Markdown transcript to an HTML page, drawing the structures in every SMILES column |
| `get_tool_log` | The logged tool calls (index, time, arguments), to pick this chat's calls for `create_transcript` |
| `reset_tool_log` | Clear the tool-call log that `create_transcript` reports |

## Safety

All tools are read-only, except that `create_transcript`, `transcript_to_html`, `draw_structure_grid`,
`draw_r_group_table` and `add_figure` write transcript and figure files (`add_figure` reads the image file it is given, and accepts only
images). The database connection is opened read-only with file, network and extension access
disabled and settings locked, so `run_sql` cannot write data or read anything outside the database.
Queries time out after 30 s (`--timeout`). The only tool that uses the network is
`chemical_name_to_smiles`, for PubChem; `--no-network` turns that off.

## chemical_name_to_smiles

It tries three sources in order and stops at the first that knows the name: an exact (case-insensitive)
BindingDB synonym, OPSIN (systematic names, offline; the JVM starts on the first lookup, about 1 s), and
the PubChem name service. A BindingDB name can belong to several compounds (stereoisomers, or patent
labels such as `compound 5`); all are returned, most measured first, flagged `ambiguous` when their
InChIKey first blocks differ. A structure from OPSIN or PubChem is matched back to BindingDB by InChIKey:
the same compound first, then compounds sharing the first block (other stereoisomers). PubChem's
staurosporine, for example, has different stereo descriptors from all BindingDB entries named
staurosporine, so it is found only by its first block. The `sources` argument picks which sources to try
and in what order.

## substructure_search

It reads a SMILES query by default, so Kekulé and aromatic forms of a ring match the same compounds. It
uses SMARTS when the query contains `*`, is not valid SMILES, is written aromatic but is not a valid
aromatic molecule (such as a ring nitrogen missing its H), or has a bracket atom without H such as
`[#7]` (which SMILES would make a radical). A SMILES query ignores H counts written in brackets; pass
`query_type="smarts"` to enforce them. The result echoes how the query was read. Without a target,
results are capped at `limit` and favour the compounds with the most measurements. With a target, every
compound measured against it is searched and the matches are ranked by potency. A search stops at 80%
of the query time limit and reports partial results; counting a very generic query (a benzene ring
matches 1.28M compounds) takes about 5 s.

Affinity filters (`affinity_types`, `min_value_nm`, `max_value_nm`) keep only compounds with at least one
measurement that passes them, before `limit` applies, and return each with its most potent such
measurement and its SMILES. Types are not interconverted; the default types are Ki, Kd, IC50 and EC50. Values reported
as `>` never pass `max_value_nm`, and values reported as `<` never pass a nonzero `min_value_nm`. Both
structure tools take these filters.

## similarity_search

It takes a whole molecule as SMILES and returns compounds with Tanimoto similarity at or above
`threshold` (default 0.7), most similar first. Fingerprints are Morgan, radius 2, 2048 bits, computed on
the largest fragment, so a salt scores the same as its parent. Stereochemistry is ignored, so
stereoisomers score 1.0. Scoring all 1.46M compounds takes about 50 ms.

## exact_structure_search

It finds the BindingDB entries of the query molecule: compounds whose canonical isomeric SMILES equals
the query's, so salts, stereo, charges and isotopes must match, and tautomers or protonation states
count as different (`similarity_search` with threshold 1.0 ignores stereo and salts). Candidates are the
compounds sharing the query's InChIKey first block, so it needs the standard InChIKeys that the build
computes ([InChIKeys](building-the-database.md#inchikeys)); on a database without them it says so, since
BindingDB's own keys miss many entries (imatinib has three, and BindingDB's keys find only one). It takes
the same affinity filters as the structure-search tools and needs RDKit but not the index.

## Compound properties

With the `compound_property` table ([building-the-database.md](building-the-database.md#compound-properties)),
computed by RDKit for each compound's parent (largest fragment):

- `get_compound` adds the compound's `properties`: heavy atoms, MW, cLogP (Crippen), TPSA, H-bond donors
  and acceptors (Lipinski NH+OH and N+O counts), rotatable bonds, rings, aromatic rings, Fsp3, QED, Ro5
  violations, Bemis-Murcko `scaffold` and `generic_scaffold`, and the names of the PAINS, Brenk and NIH
  alerts it matches; each top target also gets `best_ligand_efficiency`.
- Measurement rows of `find_ligands_for_target`, `substructure_search` and `similarity_search` add
  `ligand_efficiency` (1.37 × p_affinity / heavy atoms, kcal/mol per heavy atom), `lipe` (p_affinity −
  cLogP) and `pains_alerts`. Both are computed from whichever affinity type the row has.
- Those three tools take a `properties` filter: `max_mw`, `min_heavy_atoms`, `max_heavy_atoms`, `min_clogp`, `max_clogp`,
  `max_tpsa`, `max_hbd`, `max_hba`, `max_rotatable_bonds`, `max_ro5_violations`, `min_qed`,
  `exclude_alerts` (catalogs: `pains`, `brenk`, `nih`), `scaffold` (SMILES of a molecule or scaffold:
  compounds with the same Bemis-Murcko scaffold) and the per-measurement `min_ligand_efficiency` and
  `min_lipe`. Like the affinity filters, they apply before the result limit.
- `find_ligands_for_target` ranks by `order_by` (`potency`, `ligand_efficiency` or `lipe`), and with
  `group_by_scaffold` returns one row per scaffold of the target's ligands (`scaffold_smiles`, compounds,
  measurements, best and median p_affinity, the most potent compound), most compounds first;
  `generic_scaffold` groups on generic scaffolds instead (all atoms carbon, all bonds single).

PAINS (pan-assay interference compounds) alerts flag substructures that often give false positives in
screening assays, so a potent PAINS hit is worth checking. Brenk alerts (unwanted groups for screening
libraries) match about a third of BindingDB's compounds, including many drugs, and are no reason by
themselves to doubt a measurement.

## SAR tools

`decompose_r_groups`, `matched_molecular_pairs` and `activity_cliffs` work on one target at a time and
need RDKit (the `substructure` extra), but not the structure-search index. All three read the same
ligand set, built so that a difference between two compounds is a difference in chemistry rather than in
assay:

- exact measurements only (`relation = '='`, nM): a bound such as `< 50 nM` cannot be subtracted from
  another value;
- one affinity type, named with `affinity_type` or else the target's most measured one, reported back in
  the result, because an IC50 and a Ki are not comparable;
- one row per compound, its most potent qualifying measurement, with `n_measurements` so a value resting
  on a single report can be spotted;
- the parent of each structure (largest fragment), so a counter-ion is never mistaken for a substituent;
- most potent first, capped by `max_compounds` — the cap is what bounds the runtime, and a note says
  when it cut the set off.

They take the same target arguments as `find_ligands_for_target` (`target_id` with `target_kind`, or
`uniprot` with optional `include_variants`) and the same `properties` filter.

**`decompose_r_groups`** takes a `core` as SMILES or SMARTS — a scaffold from
`find_ligands_for_target(group_by_scaffold=True)` is a natural input — and returns one row per matching
compound with a column per R-group position (`R1`, `R2`, ...), the potency, and `smiles` so
`draw_structure_grid` can show whole structures aligned on the returned `matched_core`. The series
itself is shown with `draw_r_group_table` (below), which takes that `matched_core` and the rows'
R-group cells: a substituent SMILES such as `CCC[*:1]` is an input to that tool, not something to put
in a table or an answer. A position is
hydrogen where the compound carries none (`H`), and a position no matching compound substitutes is
dropped rather than returned as a column of nulls. Marking positions in the core (`[*:1]`, `[*:2]`)
decomposes only there and is taken literally: a compound substituted elsewhere on the core does not
match. Without marks, every open position of the core becomes a column, and a ring fused to the core
fills two of them. `summarize` (on by default) adds, per position, the substituents it carries with
their compounds' best and median potency, computed over every match rather than the returned page.

**`matched_molecular_pairs`** finds compounds that differ by a single group, by cutting one acyclic
single bond of each molecule and matching the halves: compounds sharing a constant part and differing in
the variable part form a pair. A pair found through several constant parts keeps the largest, which
leaves the smallest change as the transformation. Each pair reads from the smaller group to the larger,
so `delta_p_affinity` (and `fold_change`, below 1 when potency was lost) is the effect of making that
change. `include_hydrogen_changes` (on by default) also cuts carbon-hydrogen bonds, which is the only
way a pair that *adds* a group is found — without it there are no `[H][*:1] >> F[*:1]` pairs at all; it
costs about four times the fragmentation time. `transformation` keeps only pairs making one given
change, written as two fragment SMILES around `>>` (either direction matches), and
`group_by_transformation` returns one row per change with how often it was made, the median, smallest
and largest effect, and how many pairs it improved — the answer to "what does adding a fluorine do on
this target?". `max_variable_atoms` (13) bounds how large a changed group may be.

**`activity_cliffs`** compares every pair of the ligand set by Tanimoto on Morgan fingerprints and keeps
those at or above `min_similarity` (0.8) whose potency differs by at least `min_delta_p` log units
(1.5), ranked by SALI, the potency difference per unit of structural distance. Two compounds whose
fingerprints are identical have no defined SALI; they are listed first, and `same_structure` says
whether they are literally the same molecule under two monomerids — one compound curated twice with
different reported values, which is a data-quality finding rather than SAR. A cliff resting on a single
measurement is worth confirming with `get_activity` before being believed.

## create_transcript

Modelled on `create_chat_transcript` in [mcp-okn](https://github.com/sbl-sdsc/mcp-okn). The server logs
every successful tool call as it runs (tool, arguments, UTC timestamp, result); failed calls,
`describe_tables` and the transcript tools are not logged. The model supplies what the server cannot
see: its exact model id, and each prompt with its full answer (`exchanges`). The document has a header
(date, model, optional skills and other MCP servers used, BindingDB release, and a Contents line with
counts) and the conversation as 👤 User / 🧠 Assistant blocks.

The tool calls are left out by default, also when the analysis used SQL. Only when the user asks for
them does the model set `include_tool_calls`, and a "BindingDB tool calls" section follows the conversation:
each call's arguments verbatim (SQL in a `sql` block for `run_sql`), then its result, with lists of rows
as tables capped at `max_result_rows` (default 5; the true row count is kept). The header then also gives
the active window from the first to the last call. `format="json"` returns the same fields unrendered,
with full results.

The log lives in the server process and covers everything since the server started or since
`reset_tool_log`. Claude Desktop runs one server process for all chats, so the log mixes chats; the
server cannot tell them apart. When including tool calls, the model therefore lists the log with
`get_tool_log` and passes the indices of its own calls to `create_transcript` as `calls`; without
`include_tool_calls`, `calls` is ignored, so a transcript never shows tool calls the user did not ask for.

Figures made with `draw_structure_grid` or added with `add_figure` are placed under the answer whose
`figures` lists their ids (or, if no answer lists any, in a Figures section), numbered 1, 2, … in the
order they appear; the ids themselves keep counting across `reset_tool_log` and chats. The Markdown links to each
figure's image in `figures/`, with the title and caption of an added image under it;
when a transcript has figures, the server also saves the `.md` next to that folder so the links work.

### Where transcripts are written

With `output_dir` (an absolute path, e.g. the folder the user named for the results), `create_transcript`
and `transcript_to_html` write the transcript there as `<file_name>.md` or `.html` (`file_name` defaults to
the title), replacing a file of the same name. A Markdown transcript's figures go into
`<output_dir>/figures/` as `<file_name>-figure-<n>.png` (or `.svg`, …), so regenerating the transcript
replaces them and removes copies of figures it no longer has; other files there are left alone. The model is told to pass the user's folder rather than copy files afterwards.
Without `output_dir`, files go to `transcripts/` next to the database, time-stamped; `--transcript-dir` or
the environment variable `MCP_BINDINGDB_TRANSCRIPT_DIR` changes that folder. Because they can replace
files, both tools are annotated as destructive.

In a tool call's result, the molecules it is about (the query of a substructure or similarity search, a
structure looked up by name, the compound from `get_compound`) are listed in a `name | smiles` table.

## HTML transcripts

`create_transcript` with `format="html"` builds the Markdown transcript and converts it in the same
call, so a user can simply ask for an HTML transcript. `transcript_to_html` does the conversion alone,
for a Markdown transcript that already exists: by default the one the last `create_transcript` call
returned, or Markdown passed as `markdown` (e.g. a transcript the user edited).
Figures are embedded, and every table with a column whose header contains "SMILES", in the answers as well
as in the tool calls, gets a structure column before it, unless a figure under the same answer already
draws all of its molecules. The molecules of a column are aligned on their
largest common substructure (when it has at least 6 atoms), which is highlighted, and drawn in one frame,
so the core sits in the same place in every row and all are at the same scale. RDKit draws the structures
on the server as SVG images embedded in
the page, so it opens offline; cells that are not valid SMILES (or SMARTS) are left empty, and without
RDKit there are no drawings. Answer text and data are shown as text, never as HTML. A drawing is about
20 KB, too much to pass through the chat, so the server writes the page itself (see
[Where transcripts are written](#where-transcripts-are-written)) and returns the path plus a link to the resource
`transcript://session/latest.html` for clients of a remote server.

## draw_structure_grid

Draws compounds side by side, like a figure in a paper: each with a name, subtitle, structure, caption and
bars for its binding to its main targets (log scale, coloured by Ki, Kd, IC50 or EC50, which each bar must
give, lighter for thin evidence). The structures are aligned on `align_to` (SMILES or SMARTS; its first atom is drawn on the left)
or else on their largest common substructure, which is highlighted, and drawn in one shared frame, so the
core sits on the same pixels in every column. Layouts use RDKit's CoordGen, which places the rest of each
molecule around the fixed core with few clashes.

The tool returns the figure as a PNG and logs it with an id. In MCP Apps clients such as Claude Desktop,
which would show the PNG only as a small thumbnail, the figure appears in a panel in the chat
(`ui://bindingdb/figure.html`, built from `web/structure-editor/ui/figure.*`); other clients show the PNG.
Claude Desktop does not pass the image on to the panel, so the panel loads the saved PNG (`figure_file` in
the result) with the panel-only tool `figure_image`. The PNG is saved in
`transcripts/figures/`; HTML transcripts embed an HTML version of the figure. It needs RDKit (the
`substructure` extra, which brings Pillow for the PNG); without it the tool is not offered. The tool tells
the model to refer to the figure in its answer rather than repeat its structures and values as tables.

## draw_r_group_table

Draws one chemical series the way a medicinal-chemistry paper does: the core once at the top, with each
`[*:n]` position named `R1`, `R2`, ..., and under it a table whose cells are the substituents
themselves, drawn, with the compound's name, its potency bars, and a note per column for naming the
position on the core (`{"R1": "N1"}`). Hydrogen is written as `H` and a position a compound does not
have as `–`; a cell whose SMILES cannot be parsed is written out and reported in the result. Each
substituent is drawn with its attachment point as the bond stub where it joins the core, growing to the
right, and a methyl as `H₃C–` rather than a bare line.

The `core` and the rows' `r_groups` are what `decompose_r_groups` returns (`matched_core` and the `R1`,
`R2`, ... columns), so the table is one call after the decomposition; summary rows work too, one per
substituent at a position, with `n_compounds` as the subtitle and the median potency as the bar — for
those, `row_heading` renames the first column and `core_caption` replaces the sentence beside the core,
which otherwise says that everything but the named positions is the same in every row. Like
`draw_structure_grid` it returns a PNG, logs the figure with an id, saves it in `transcripts/figures/`,
and gives HTML transcripts an HTML version; it needs RDKit. The tool tells the model to refer to the
table in its answer and to name groups in prose ("an 8-cyclopentyl") rather than list their SMILES.

## add_figure

Adds an image made with other tools, such as a matplotlib heat map, as a figure: `create_transcript` can
only include figures in the server's log, so without this the model would have to edit the transcript
files itself. Pass `path` (a PNG, JPEG, GIF, WebP or SVG file on the machine running the server) or, when
the image was made where the server cannot read it, `data` (the image base64-encoded, which puts it
through the chat), plus a `title` and optional `caption`. The server copies the image into
`transcripts/figures/` and returns its figure id. HTML transcripts embed the image; Markdown transcripts
link to the copy. It needs no RDKit.

## Data notes

- Ki/Kd/IC50/EC50 are in nM, kon in M⁻¹s⁻¹, koff in s⁻¹; `p_affinity = 9 − log10(nM)`.
- `>` values (e.g. `>10000`) usually mean inactive at the highest concentration tested; potency filters exclude them.
- `monomer.display_name` holds only the BDBM id; names are in `compound_name` / `compound.name`.
- `monomer.chembl_id` is empty in this release; ChEMBL ids appear as synonyms instead.
- Mutant and construct targets are separate rows sharing a UniProt accession (`uniprot_raw` like `P00533[L858R]`).
- Text comparisons in DuckDB are case-sensitive (MySQL's were not): use `ILIKE` or `lower()`.
