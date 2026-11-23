"""MCP App extension for sbl-sdsc/mcp-bindingdb. No remote asset host is needed."""

from __future__ import annotations

import asyncio
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
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ToolAnnotations
from pydantic import Field

URI = "ui://bindingdb/structure-editor.html"
# Shows a figure tool's image in the chat; hosts show an image in a tool result only as a small thumbnail.
FIGURE_URI = "ui://bindingdb/figure.html"
FIGURE_META = {"ui": {"resourceUri": FIGURE_URI}}
# Shows overlay_binding_site's superposed complexes in 3D (web/structure-editor/ui/overlay.js).
OVERLAY_URI = "ui://bindingdb/overlay.html"
OVERLAY_META = {"ui": {"resourceUri": OVERLAY_URI}}
OVERLAY_ASSET = Path(__file__).parent / "assets" / "overlay-viewer.html.gz"
OVERLAY_DATA_SLOT = "window.__OVERLAY_DATA__=null"
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


EDITOR_REPLY = "The structure editor is open. If it doesn't appear, ask me to open it again."
# Claude Desktop 4.23118.0 shows no panel for a call in the first turn of a new chat that runs through this
# computer (a remote_cowork session), not even for a second call in that turn; the first call of the next turn
# shows it (docs/structure-editor.md). The server cannot tell from the call, so the editor page reports itself
# with editor_opened once it loads (EditorSearches.mark_opened), and check_editor_shown waits for that.
NOT_SHOWN = ("The editor has not appeared in the chat: its page never loaded. This is the chat app not showing the "
             "panel, not something you did. Call open_structure_editor again with the same arguments, without "
             "asking.")
# Also in open_structure_editor's description and the server instructions, for when the call never reaches the
# server: in the first turn of a new chat the linked computer may not be connected yet.
NEXT_MESSAGE_REPLY = ("The editor didn't open on the first try, which can happen in a new chat. "
                      "Please send your request again.")
WAIT_FOR_EDITOR = 10  # seconds check_editor_shown waits for the page; it reports itself about 1 s after the call
RETRY_WITHIN = 30 * 60  # seconds after a missed editor in which open_structure_editor counts as the retry
UI_EXTENSION = "io.modelcontextprotocol/ui"  # MCP Apps: clients that can show panels declare it
_EDITOR_ID = re.compile(r"[0-9a-z]{1,32}")


def client_info(ctx: Context | None) -> dict[str, Any]:
    """The calling client's name and version and whether it declared MCP Apps (UI_EXTENSION)."""
    try:
        caps = ctx.client_capabilities if ctx is not None else None
        params = ctx.session.client_params if ctx is not None else None
    except Exception:  # noqa: BLE001 - outside a request
        caps = params = None
    info = getattr(params, "client_info", None)
    declared = {**(getattr(caps, "extensions", None) or {}), **(getattr(caps, "experimental", None) or {})}
    return {"name": getattr(info, "name", None), "version": getattr(info, "version", None),
            "apps": UI_EXTENSION in declared}
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

    def mark_opened(self, editor_id: str) -> None:
        """Record that the editor's page loaded in the chat (kept with its searches, for every server process)."""
        marker = self._file(editor_id).with_suffix(".opened")
        self.directory.mkdir(parents=True, exist_ok=True)
        marker.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
        for old in sorted(self.directory.glob("*.opened"), key=lambda f: f.stat().st_mtime)[:-self.EDITORS]:
            old.unlink(missing_ok=True)

    def opened(self, editor_id: str) -> bool:
        return self._file(editor_id).with_suffix(".opened").is_file()

    async def wait_opened(self, editor_id: str, seconds: float) -> bool:
        """Whether the editor's page reports itself (mark_opened, from any server process) within `seconds`."""
        deadline = time.monotonic() + seconds
        while not self.opened(editor_id):
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.25)
        return True

    # Workaround for Claude Desktop showing no panel for some calls (docs/structure-editor.md): when an editor
    # does not appear, the assistant opens it once more, and that call must not ask for another check.
    def note_missed(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        (self.directory / "missed").write_text(str(time.time()))

    def take_missed(self) -> bool:
        """Whether an editor was missed in the last RETRY_WITHIN seconds; forgets it, so only one retry follows."""
        marker = self.directory / "missed"
        try:
            missed = float(marker.read_text())
            marker.unlink(missing_ok=True)
        except (FileNotFoundError, ValueError):
            return False
        return time.time() - missed < RETRY_WITHIN

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
        and arguments it ran with and that tool's result. editor_shown tells whether the editor appeared in the
        chat at all."""
        editor_id = editor_id or searches.latest_editor()
        runs = searches.searches(editor_id) if editor_id else []
        shown = bool(runs) or (editor_id is not None and searches.opened(editor_id))
        if not runs:
            return {"editor_id": editor_id, "editor_shown": shown, "searches": [],
                    "note": NOT_SHOWN if editor_id and not shown else
                    "No searches have been run in this editor yet; the user runs them with Run query."}
        return {"editor_id": editor_id, "editor_shown": True, "searches": runs if all_searches else runs[-1:],
                "n_searches": len(runs)}


def add_editor_check_tool(mcp: MCPServer, searches: EditorSearches) -> None:
    """check_editor_shown: the workaround for chats that show no panel for a call (open_structure_editor)."""

    @mcp.tool(annotations=READ_ONLY)
    async def check_editor_shown(
        editor_id: Annotated[str, Field(description="The editor_id open_structure_editor returned")],
    ) -> dict[str, Any]:
        """Wait until the structure editor open_structure_editor just opened has appeared in the chat (at most
        about 10 s). Call it right after open_structure_editor when its instructions say so."""
        searches._file(editor_id)  # validates the id
        if await searches.wait_opened(editor_id, WAIT_FOR_EDITOR):
            return {"editor_id": editor_id, "shown": True,
                    "instructions": "The editor appeared. Reply as open_structure_editor's instructions say."}
        searches.note_missed()
        return {"editor_id": editor_id, "shown": False,
                "instructions": "The editor did not appear: the chat app showed no panel for this call, which "
                                "is not something you did. Do not call open_structure_editor again in this reply: "
                                "Claude Desktop shows no editor in the first reply of a new chat, not even for a "
                                "second call. Reply with exactly this and nothing else: \"" + NEXT_MESSAGE_REPLY
                                + "\" When the user sends their next message, whatever it says, call "
                                "open_structure_editor first, with the same arguments as before, and follow its "
                                "instructions."}


def overlay_viewer_html(data: dict[str, Any] | None = None) -> str | None:
    """The overlay viewer page; with `data` (overlay_binding_site's viewer data) inlined, a standalone page
    that needs no MCP host. None when the viewer has not been built."""
    if not OVERLAY_ASSET.is_file():
        return None
    page = gzip.decompress(OVERLAY_ASSET.read_bytes()).decode("utf-8")
    if data is None:
        return page
    payload = json.dumps(data).replace("</", "<\\/")
    return page.replace(OVERLAY_DATA_SLOT, "window.__OVERLAY_DATA__=" + payload, 1)


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
    viewer = overlay_viewer_html()
    if viewer is not None:
        apps.add_html_resource(OVERLAY_URI, viewer, title="BindingDB binding-site overlay",
                               csp=ResourceCsp(resource_domains=["data:", "blob:"]))

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
        ctx: Context | None = None,
    ) -> dict[str, Any]:
        """Open the chemical structure editor in the chat: a sketcher where the user draws or edits a molecule
        (or loads one from SMILES, SMARTS or a compound name) and searches BindingDB with it by exact
        structure, substructure or similarity, optionally only compounds with a Ki/Kd/IC50/EC50 in an
        affinity range. The results appear in the editor.

        In the first reply of a new Claude Desktop chat, this call often fails as if the computer it runs on
        were asleep, offline or disconnected. It is not: the chat's link to it is still starting. If the call
        fails, do not mention the computer, the app or a connection, and do not suggest checking them; reply
        with exactly: "The editor didn't open on the first try, which can happen in a new chat. Please send
        your request again."

        Use it whenever the user wants to draw, sketch, edit, modify or build a chemical structure,
        molecule, compound, fragment or scaffold, or asks for a structure, molecule or chemical editor or
        sketcher, e.g. "edit structure", "draw a molecule", "let me sketch a compound", "edit imatinib". Open
        it directly rather than asking what kind of structure is meant. When the user names or gives a
        compound, pass it as initial_query.

        Claude Desktop shows it also in chats with a folder attached and in chats whose tools come through a
        linked computer (remote-devices tool names): open it there too. In clients that cannot show the editor, use the regular BindingDB tools instead."""
        if len(initial_query) > 20000:
            raise ToolError("Initial query is too long")
        editor_id = uuid.uuid4().hex[:12]
        reply = ("Reply with exactly this and nothing else: \"" + EDITOR_REPLY + "\" Your reply stays in the chat "
                 "after the user runs searches, so do not say no search has run. The user sees the results in the "
                 "editor; you do not. When the user asks about them or follows up, call "
                 f"get_editor_results(editor_id=\"{editor_id}\") first. If the user says the editor did not "
                 "appear, call open_structure_editor again with the same arguments right away, without asking: "
                 "the chat app sometimes shows no panel for a call, though the call worked. Do not guess why or "
                 "blame yourself.")
        # Claude Desktop sometimes shows no panel for a call, and a second call shows it: unless this call is
        # that retry, the assistant checks that the editor appeared and otherwise opens it once more.
        check = searches is not None and client_info(ctx)["apps"] and not searches.take_missed()
        return {
            "initial_query": initial_query,
            "input_type": input_type,
            "mode": mode,
            "editor_id": editor_id,
            "executed": False,
            "instructions": "The editor explains itself. " + (
                f"Before replying, call check_editor_shown(editor_id=\"{editor_id}\"), without telling the user: "
                "it waits until the editor has appeared in the chat. If it reports shown: false, follow its "
                "instructions instead. If it is shown, " + reply[0].lower() + reply[1:] if check else reply),
        }

    @apps.tool(resource_uri=URI, visibility=["app"], annotations=READ_ONLY)
    def editor_opened(editor_id: str) -> dict[str, Any]:
        """The editor's page reports that it loaded in the chat, so get_editor_results can tell whether it appeared."""
        if searches is not None:
            searches.mark_opened(editor_id)
        return {"editor_id": editor_id}

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
            raise ToolError("Network lookups disabled")
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

