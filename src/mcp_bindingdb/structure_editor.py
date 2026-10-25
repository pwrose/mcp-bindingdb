"""MCP App extension for pwrose/mcp-bindingdb. No remote asset host is needed."""

from __future__ import annotations

import gzip
import json
import os
import re
import time
import urllib.parse
import urllib.request
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.apps import Apps, ResourceCsp, ResourcePermissions
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ToolAnnotations
from pydantic import Field

URI = "ui://bindingdb/structure-editor.html"
# Shows a figure tool's image in the chat; hosts show an image in a tool result only as a small thumbnail.
FIGURE_URI = "ui://bindingdb/figure.html"
FIGURE_META = {"ui": {"resourceUri": FIGURE_URI}}
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


EDITOR_REPLY = ("The structure editor is open. If you don't see it, start a new chat without a folder attached "
                "(the editor doesn't appear in chats with a folder), or give me a compound name or SMILES and "
                "I'll run an exact, substructure or similarity search.")
_EDITOR_ID = re.compile(r"[0-9a-z]{1,32}")
SearchTool = Literal["exact_structure_search", "substructure_search", "similarity_search"]


class EditorSearches:
    """Searches the user ran with the editor's Run query, kept per editor so the assistant, which does not see
    the editor, can fetch them with get_editor_results. They are kept as files in `directory`, one per editor,
    because a host may run several server processes: Claude Desktop sends the editor's calls to one and the
    assistant's to another. `call` runs a server tool without logging it; get_editor_results is logged instead."""

    EDITORS = 20  # most recently used editors kept
    PER_EDITOR = 10

    def __init__(self, call: Callable[[str, dict[str, Any]], Awaitable[Any]], directory: Path) -> None:
        self.call = call
        self.directory = directory

    def _file(self, editor_id: str) -> Path:
        if not _EDITOR_ID.fullmatch(editor_id):
            raise ToolError(f"Invalid editor_id {editor_id!r}")
        return self.directory / f"{editor_id}.json"

    def searches(self, editor_id: str) -> list[dict[str, Any]]:
        try:
            return json.loads(self._file(editor_id).read_text())
        except FileNotFoundError:
            return []

    def latest_editor(self) -> str | None:
        files = sorted(self.directory.glob("*.json"), key=lambda f: f.stat().st_mtime)
        return files[-1].stem if files else None

    async def run(self, editor_id: str, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        file = self._file(editor_id)
        result = await self.call(tool, arguments)
        if not isinstance(result, CallToolResult) or result.is_error or result.structured_content is None:
            text = "\n".join(c.text for c in getattr(result, "content", []) if c.type == "text")
            raise ToolError(text or f"{tool} failed")
        searches = self.searches(editor_id)
        searches.append({"tool": tool, "arguments": arguments, "ran_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "result": result.structured_content})
        self.directory.mkdir(parents=True, exist_ok=True)
        partial = file.with_suffix(f".{os.getpid()}.tmp")  # readers never see a half-written file
        partial.write_text(json.dumps(searches[-self.PER_EDITOR:], default=str))
        partial.replace(file)
        for old in sorted(self.directory.glob("*.json"), key=lambda f: f.stat().st_mtime)[:-self.EDITORS]:
            old.unlink(missing_ok=True)
        return result.structured_content


def add_editor_results_tool(mcp: MCPServer, searches: EditorSearches) -> None:
    """get_editor_results is a plain tool: bound to the editor's UI, a host could open another editor for it."""

    @mcp.tool(annotations=READ_ONLY)
    def get_editor_results(
        editor_id: Annotated[str | None, Field(description="The editor_id open_structure_editor returned; "
                                                           "omit for the most recently used editor")] = None,
        all_searches: Annotated[bool, Field(description="Every search run in that editor (at most "
                                                        f"{EditorSearches.PER_EDITOR}), not only the latest")] = False,
    ) -> dict[str, Any]:
        """Results of searches the user ran in the structure editor (Run query). You do not see the editor, so
        call this when the user asks about, or follows up on, what they searched there. Each search has the tool
        and arguments it ran with and that tool's result."""
        editor_id = editor_id or searches.latest_editor()
        runs = searches.searches(editor_id) if editor_id else []
        if not runs:
            return {"editor_id": editor_id, "searches": [],
                    "note": "No searches have been run in this editor yet; the user runs them with Run query."}
        return {"editor_id": editor_id, "searches": runs if all_searches else runs[-1:], "n_searches": len(runs)}


def create_editor_extension(network: bool = True, searches: EditorSearches | None = None) -> Apps:
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
    apps.add_html_resource(
        FIGURE_URI,
        gzip.decompress((Path(__file__).parent / "assets" / "figure-viewer.html.gz").read_bytes()).decode("utf-8"),
        title="BindingDB figure",
        csp=ResourceCsp(resource_domains=["data:"]),
    )

    @apps.tool(resource_uri=URI, annotations=READ_ONLY, title="Chemical structure editor (draw a molecule)")
    def open_structure_editor(
        initial_query: Annotated[str, Field(description="A molecule to start from: SMILES, SMARTS or a compound "
                                                        "name the user gave (e.g. 'imatinib'); empty for a blank "
                                                        "canvas")] = "",
        input_type: Annotated[Literal["smiles", "smarts", "name"], Field(description="What initial_query is")]
        = "smiles",
        mode: Annotated[Literal["exact", "substructure", "similarity"], Field(
            description="The search the editor starts with: substructure for a fragment or core, similarity "
                        "for analogues")] = "exact",
    ) -> dict[str, Any]:
        """Open the chemical structure editor in the chat: a sketcher where the user draws or edits a molecule
        (or loads one from SMILES, SMARTS or a compound name) and searches BindingDB with it by exact
        structure, substructure or similarity, optionally only compounds with a Ki/Kd/IC50/EC50 in an
        affinity range. The results appear in the editor.

        Use it whenever the user wants to draw, sketch, edit, modify or build a chemical structure,
        molecule, compound, fragment or scaffold, or asks for a structure, molecule or chemical editor or
        sketcher, e.g. "edit structure", "draw a molecule", "let me sketch a compound", "edit imatinib". Open
        it directly rather than asking what kind of structure is meant. When the user names or gives a
        compound, pass it as initial_query.

        In clients that cannot show the editor, use the regular BindingDB tools instead."""
        if len(initial_query) > 20000:
            raise ToolError("Initial query is too long")
        editor_id = uuid.uuid4().hex[:12]
        return {
            "initial_query": initial_query,
            "input_type": input_type,
            "mode": mode,
            "editor_id": editor_id,
            "executed": False,
            # Claude Desktop shows no editor in chats with a folder attached, and the server cannot tell
            # (docs/structure-editor.md), so the reply always says what to do then.
            "instructions": "The editor explains itself. Reply with exactly this and nothing else: \""
                            + EDITOR_REPLY + "\" Your reply stays in the chat after the user runs searches, "
                            "so do not say no search has run. The user sees the results in the editor; you do "
                            "not. When the user asks about them or follows up, call "
                            f"get_editor_results(editor_id=\"{editor_id}\") first.",
        }

    @apps.tool(resource_uri=URI, visibility=["app"], annotations=READ_ONLY)
    async def editor_search(editor_id: str, tool: SearchTool, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run Query: run one BindingDB structure search for the editor and keep its result for get_editor_results."""
        if searches is None:
            raise ToolError("Searches from the editor are not available on this server")
        return await searches.run(editor_id, tool, arguments)

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

