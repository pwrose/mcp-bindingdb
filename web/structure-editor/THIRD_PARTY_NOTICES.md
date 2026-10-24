# Third-party components

The generated HTML embeds these components; retain their license notices when redistributing it.

| Component | Version/source | License |
| --- | --- | --- |
| JSME | vendored from `jsme-editor/jsme-editor.github.io`, commit `74de5c7b3a594bd9cef753c6391819a656a3335a` | BSD-3-Clause |
| RDKit.js | `@rdkit/rdkit` 2026.9.1, pinned in package-lock.json | BSD-3-Clause |
| MCP Apps SDK | `@modelcontextprotocol/ext-apps` 2.0.3, pinned in package-lock.json | MIT |

Full notices are packaged under `src/mcp_bindingdb/assets/licenses/`. The app's source follows the
repository's BSD-3-Clause license. The generated asset contains bundled JavaScript/WebAssembly;
rebuild it using `npm ci && npm run build` rather than editing it directly.

Large vendored JSME scripts are stored as lossless `.js.gz` files and decompressed during the build.
