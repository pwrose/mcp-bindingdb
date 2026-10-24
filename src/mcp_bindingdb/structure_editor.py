"""MCP App extension for pwrose/mcp-bindingdb. No remote asset host is needed."""

from __future__ import annotations

import gzip
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Literal

from mcp.server.apps import Apps, ResourceCsp, ResourcePermissions
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

URI = "ui://bindingdb/structure-editor.html"
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


def create_editor_extension(network: bool = True) -> Apps:
    apps = Apps()
    bundle_dir = Path(__file__).parent / "assets" / "structure-editor"
    html = gzip.decompress(
        b"".join(part.read_bytes() for part in sorted(bundle_dir.glob("*.gz.part")))
    ).decode("utf-8")
    apps.add_html_resource(
        URI,
        html,
        title="BindingDB Structure Studio",
        prefers_border=True,
        csp=ResourceCsp(resource_domains=["data:", "blob:"]),
        permissions=ResourcePermissions(clipboard_write={}),
    )

    @apps.tool(resource_uri=URI, annotations=READ_ONLY)
    def open_structure_editor(
        initial_query: str = "",
        input_type: Literal["smiles", "smarts", "name"] = "smiles",
        mode: Literal["exact", "substructure", "similarity"] = "exact",
    ) -> dict[str, Any]:
        """Open the interactive chemical editor inside ChatGPT or Claude. Prepare a query, inspect
        its exact representation and affinity range, and explicitly send it to chat. This tool never executes a search.
        In text-only clients, use the returned initial query with the regular BindingDB tools."""
        if len(initial_query) > 20000:
            raise ToolError("Initial query is too long")
        return {
            "initial_query": initial_query,
            "input_type": input_type,
            "mode": mode,
            "executed": False,
            "instructions": "Review the editor query. No BindingDB search has run.",
        }

    @apps.tool(
        resource_uri=URI,
        visibility=["app"],
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def editor_pubchem_candidates(cids: list[int]) -> dict[str, Any]:
        """Retrieve every additional PubChem candidate returned by an ambiguous name lookup."""
        if not network:
            raise ToolError("Network lookups disabled (--no-network)")
        if len(cids) > 19 or any(type(v) is not int or v < 1 for v in cids):
            raise ToolError("Expected at most 19 positive PubChem CIDs")
        if not cids:
            return {"candidates": []}
        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
            + ",".join(map(str, cids))
            + "/property/SMILES,InChIKey,Title/JSON"
        )
        with urllib.request.urlopen(url, timeout=14) as response:
            rows = json.load(response)["PropertyTable"]["Properties"]
        return {
            "candidates": [
                {
                    "smiles": r["SMILES"],
                    "title": r.get("Title"),
                    "cid": r["CID"],
                    "inchi_key": r.get("InChIKey"),
                    "source": "PubChem",
                }
                for r in rows
            ]
        }

    return apps

