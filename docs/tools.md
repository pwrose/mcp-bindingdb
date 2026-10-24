# Tools

| Tool | Purpose |
|---|---|
| `search_compounds` | By name/synonym, ChEMBL id, `cid_N`, BDBM id, or InChIKey (full or first block) |
| `chemical_name_to_smiles` | SMILES for a compound name (trade name, IUPAC name, CAS number) from BindingDB synonyms, OPSIN or PubChem, with the BindingDB compounds that have that structure |
| `search_targets` | By name, gene name, UniProt entry name or accession; optional organism filter |
| `get_compound` | Identifiers, synonyms, PDB ligands, most potent targets |
| `get_target` | Identifiers, synonyms, PDB ids, complex components, measurement counts |
| `find_ligands_for_target` | Most potent compounds for a target (by id or UniProt accession, optional variants) |
| `find_targets_for_compound` | Activity/selectivity profile of a compound |
| `get_activity` | Full record of one measurement, with assay description and citation |
| `describe_tables` | Table list with descriptions, or columns and sample rows of one table |
| `run_sql` | Arbitrary read-only DuckDB SQL |
| `substructure_search` | Compounds containing a SMILES/SMARTS fragment, optionally only those measured against a target with potency filters; every target the matching compounds hit, with compounds per target; or a count of matches (needs the structure-search index) |
| `similarity_search` | Compounds similar to a molecule (Tanimoto on Morgan fingerprints) above a threshold, with the same target filter and per-target summary (needs the structure-search index) |
| `create_transcript` | Markdown, HTML (with structure drawings) or JSON transcript of the session: prompts and answers, optionally followed by the logged tool calls with their results |
| `draw_structure_grid` | Compounds side by side, aligned on a shared core that is highlighted, with binding bars per target; shown in the chat and included in transcripts (needs RDKit) |
| `add_figure` | Adds an image made with other tools (e.g. a matplotlib plot) as a figure for transcripts |
| `transcript_to_html` | Converts an existing Markdown transcript to an HTML page, drawing the structures in every SMILES column |
| `get_tool_log` | The logged tool calls (index, time, arguments), to pick this chat's calls for `create_transcript` |
| `reset_tool_log` | Clear the tool-call log that `create_transcript` reports |

## Safety

All tools are read-only, except that `create_transcript`, `transcript_to_html`, `draw_structure_grid` and
`add_figure` write transcript and figure files (`add_figure` reads the image file it is given, and accepts only
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

## similarity_search

It takes a whole molecule as SMILES and returns compounds with Tanimoto similarity at or above
`threshold` (default 0.7), most similar first. Fingerprints are Morgan, radius 2, 2048 bits, computed on
the largest fragment, so a salt scores the same as its parent. Stereochemistry is ignored, so
stereoisomers score 1.0. Scoring all 1.46M compounds takes about 50 ms.

## create_transcript

Modelled on `create_chat_transcript` in [mcp-okn](https://github.com/sbl-sdsc/mcp-okn). The server logs
every successful tool call as it runs (tool, arguments, UTC timestamp, result); failed calls,
`describe_tables` and the transcript tools are not logged. The model supplies what the server cannot
see: its exact model id, and each prompt with its full answer (`exchanges`). The document has a header
(date, model, optional skills and other MCP servers used, BindingDB release, and a Contents line with
counts) and the conversation as 👤 User / 🧠 Assistant blocks.

The tool calls are left out by default. When the user asks for them, the model sets
`include_tool_calls` (or passes `calls`), and a "BindingDB tool calls" section follows the conversation:
each call's arguments verbatim (SQL in a `sql` block for `run_sql`), then its result, with lists of rows
as tables capped at `max_result_rows` (default 5; the true row count is kept). The header then also gives
the active window from the first to the last call. `format="json"` returns the same fields unrendered,
with full results.

The log lives in the server process and covers everything since the server started or since
`reset_tool_log`. Claude Desktop runs one server process for all chats, so the log mixes chats; the
server cannot tell them apart. The model therefore lists the log with `get_tool_log` and passes the
indices of its own calls to `create_transcript` as `calls`.

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

The tool returns the figure as a PNG, which shows in the chat, and logs it with an id. The PNG is saved in
`transcripts/figures/`; HTML transcripts embed an HTML version of the figure. It needs RDKit (the
`substructure` extra, which brings Pillow for the PNG); without it the tool is not offered. The tool tells
the model to refer to the figure in its answer rather than repeat its structures and values as tables.

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
