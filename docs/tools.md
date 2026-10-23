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
| `create_transcript` | Markdown (or JSON) transcript of the session: prompts and answers, optionally followed by the logged tool calls with their results |
| `transcript_to_html` | Converts a Markdown transcript to an HTML page, drawing the structures in every SMILES column |
| `get_tool_log` | The logged tool calls (index, time, arguments), to pick this chat's calls for `create_transcript` |
| `reset_tool_log` | Clear the tool-call log that `create_transcript` reports |

## Safety

All tools are read-only, except that `transcript_to_html` writes its HTML file. The database connection is opened read-only with file, network and extension access
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

In a tool call's result, the molecules it is about (the query of a substructure or similarity search, a
structure looked up by name, the compound from `get_compound`) are listed in a `name | smiles` table.

## transcript_to_html

Converts a Markdown transcript into a standalone HTML page: by default the one the last
`create_transcript` call returned, or Markdown passed as `markdown` (e.g. a transcript the user edited).
Every table with a column whose header contains "SMILES", in the answers as well as in the tool calls,
gets a structure column before it. RDKit draws the structures on the server as SVG images embedded in
the page, so it opens offline; cells that are not valid SMILES (or SMARTS) are left empty, and without
RDKit there are no drawings. Answer text and data are shown as text, never as HTML. A drawing is about
20 KB, too much to pass through the chat, so the server writes the page itself, to `transcripts/` next to
the database (`--transcript-dir` changes this), and returns the path plus a link to the resource
`transcript://session/latest.html` for clients of a remote server.

## Data notes

- Ki/Kd/IC50/EC50 are in nM, kon in M⁻¹s⁻¹, koff in s⁻¹; `p_affinity = 9 − log10(nM)`.
- `>` values (e.g. `>10000`) usually mean inactive at the highest concentration tested; potency filters exclude them.
- `monomer.display_name` holds only the BDBM id; names are in `compound_name` / `compound.name`.
- `monomer.chembl_id` is empty in this release; ChEMBL ids appear as synonyms instead.
- Mutant and construct targets are separate rows sharing a UniProt accession (`uniprot_raw` like `P00533[L858R]`).
- Text comparisons in DuckDB are case-sensitive (MySQL's were not): use `ILIKE` or `lower()`.
