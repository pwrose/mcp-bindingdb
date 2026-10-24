# Interactive structure editor

`open_structure_editor` serves a self-contained MCP App (`ui://bindingdb/structure-editor.html`).
JSME draws structures, RDKit.js validates and generates isomeric SMILES, and the official MCP Apps
bridge connects the widget to this server. The generated HTML is compressed into small bundled files
under `assets/structure-editor/` and assembled in memory by the server. These files are included in the Python wheel;
Node.js and the private Sites workspace are not needed to run the server.

## Add it to an existing installation

1. Check out this change in a separate working copy or branch, then install dependencies:

   ```bash
   uv sync --extra substructure --extra name
   ```

   All three search modes use RDKit. Substructure and similarity also need the existing `.sslib` index
   beside your DuckDB file, for the same release. Exact needs standard InChIKeys: run
   `uv run --extra substructure python scripts/compute_inchikeys.py /path/to/bindingdb.duckdb` once
   on an existing database ([InChIKeys](building-the-database.md#inchikeys)). Reuse your existing database and index. If the index
   is missing, follow [Structure-search index](building-the-database.md#structure-search-index).
   OPSIN is optional and uses the `name` extra and Java already described in that guide.

2. Run the automated checks without downloading a BindingDB database:

   ```bash
   uv run pytest tests/test_structure_editor.py
   uv run pytest -m "not network"
   ```

   The editor tests use a tiny DuckDB fixture and the repository's actual RDKit index format. They
   cover MCP Apps discovery/resources, registration in `build_server`, seed input, exact stereo/salt
   equality and computed InChIKeys, affinity endpoints/types/censored values, filtering before result
   limits, similarity scores, tool logging and disabled-network behavior. Existing tests that need a complete
   BindingDB database are skipped when it is absent.

3. Start the server with your existing database, initially as a test instance:

   ```bash
   uv run --extra substructure --extra name mcp-bindingdb --db /path/to/bindingdb.duckdb
   ```

   Keep your existing Claude Desktop stdio configuration, or your authenticated remote MCP connection
   for clients that use HTTP. Restart the test server and refresh its tools in the chat client. The
   private Site URL is not needed: the UI resource is served by this MCP server. A client must support
   MCP Apps to render the editor; a text-only client can keep using the ordinary chemistry tools.

## Manual chat checks

- Ask: **Open the BindingDB structure editor with aspirin.** Resolve the name, review the candidates,
  and select the intended structure. Automatic resolution uses the existing BindingDB → PubChem →
  OPSIN path. `--no-network` disables PubChem helpers, as in the rest of this server.
- Paste `CC(=O)Oc1ccccc1C(=O)O` as SMILES, load it, edit a bond, then expand **Inspect result**. Confirm
  that the generated SMILES follows the drawing and that editing the input invalidates stale output.
- Paste `[NX3][CX3](=[OX1])` as SMARTS. Confirm that Substructure is selected and the original query is
  preserved; Exact and Similarity require a concrete molecule.
- Select Similarity. Both the short slider and decimal field start at **0.85** and stay synchronized.
- Affinity starts enabled with **0 ≤ Any ≤ 1000 nM**. Choose Ki and set 10–100 nM. Reversed, missing or
  negative bounds block Run query. Unchecking Affinity removes the filter.
- Choose **Run query**. The app adds the reviewed query to model context and sends a concise user
  message asking the assistant to execute it. The assistant calls `exact_structure_search`,
  `substructure_search` or `similarity_search`, with the affinity filters when Affinity is on, and
  reports actual results in chat.
  Opening the editor or changing controls alone does not execute a database search.

The compact view was checked at 640×480, 480×520 and 360×520. Inspection is collapsed by default;
expanding it can require additional height in small chat hosts. Client-specific rendering and message
permissions still require a manual smoke test in your installed ChatGPT or Claude client.

## Search semantics

Exact (`exact_structure_search`) takes the compounds sharing the query's InChIKey first block and keeps
those whose canonical isomeric SMILES equals the query's. Stereo, salts, charge, isotopes and tautomers
remain distinct. It needs the standard InChIKeys computed when the database is built
([InChIKeys](building-the-database.md#inchikeys)).
Similarity follows this repository's Morgan radius 2, 2048-bit Tanimoto on the
largest fragment, without chirality; a score of 1 is not exact identity.

Affinity requires at least one qualifying Ki, Kd, IC50 or EC50 measurement in the inclusive nM range.
Any accepts any one of those types; it does not convert between types. Each hit carries its most
potent qualifying measurement (id, type, relation, value, target). Missing and non-nM values are excluded.
`>` bounds do not establish membership in a finite interval. `<` bounds qualify only when the minimum
is zero and their reported upper bound is within the range. Filtering occurs before result limits,
not just over the first page of unfiltered structural hits. Partial coverage and time limits are
reported rather than presented as a complete result set.

## Rebuild the bundled UI

Maintainers need Node.js 22.12+:

```bash
cd web/structure-editor
npm ci
npm test
npm run build
```

Commit the source changes and regenerated `src/mcp_bindingdb/assets/structure-editor/*.gz.part` together.
The bridge and RDKit versions are pinned by `package-lock.json`. JSME is vendored; its license and
provenance are documented in [third-party notices](../web/structure-editor/THIRD_PARTY_NOTICES.md).
The app loads no scripts from a CDN. Chemistry/name operations go through the MCP server; this PR
adds no external hosting, deployment configuration, credentials, or authentication changes.
