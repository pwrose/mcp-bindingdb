"""The HTML transcript: a Markdown transcript as one standalone page, with structure drawings.

Modelled on mcp-okn's transcript_render. Every table with a SMILES column (in the answers as well as in
the tool calls) gets a structure column before it. RDKit draws the structures on the server and they are
embedded as SVG data: images, so the page needs no network when opened. Without RDKit there are no
drawings.
"""

from __future__ import annotations

import base64
import html as _html
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token

from . import substructure

_CSS = """
:root { color-scheme: light; }
body {
  margin: 0 auto; max-width: 1200px; padding: 24px 16px 48px;
  font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  color: #1f2328; background: #ffffff;
}
h1, h2, h3, h4 { line-height: 1.25; margin: 1.6em 0 0.6em; }
h1 { font-size: 1.9em; border-bottom: 1px solid #d1d9e0; padding-bottom: 0.3em; }
h2 { font-size: 1.45em; border-bottom: 1px solid #d1d9e0; padding-bottom: 0.3em; }
h4 { font-size: 1.05em; }
a { color: #0969da; overflow-wrap: anywhere; }
hr { border: 0; border-top: 1px solid #d1d9e0; margin: 1.5em 0; }
code, pre { font: 12.5px/1.45 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
:not(pre) > code { background: #eff1f3; padding: 0.15em 0.35em; border-radius: 4px; }
pre { background: #f6f8fa; border: 1px solid #d1d9e0; border-radius: 6px; padding: 12px 14px; overflow-x: auto; }
blockquote { margin: 1em 0; padding: 0 1em; color: #59636e; border-left: 4px solid #d1d9e0; }
.table-wrap { overflow-x: auto; margin: 1em 0; }
table { border-collapse: collapse; font-size: 13px; }
th, td { border: 1px solid #d1d9e0; padding: 5px 10px; text-align: left; vertical-align: top; }
td { overflow-wrap: anywhere; max-width: 28em; }
th { background: #f6f8fa; }
img.structure { display: block; width: 180px; max-width: none; height: auto; }
footer { margin-top: 3em; color: #59636e; font-size: 12px; }
@media print {
  body { max-width: none; padding: 0; font-size: 11pt; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; }
  table, pre, img { break-inside: avoid; }
  h1, h2, h3, h4 { break-after: avoid; }
}
"""


def _renderer() -> MarkdownIt:
    """A GitHub-like renderer. Raw HTML in the Markdown is escaped, not passed through: answers and
    result cells are shown as text, never run. The structure images are added as tokens after parsing."""
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    md.add_render_rule("table_open", lambda *_: '<div class="table-wrap"><table>\n')
    md.add_render_rule("table_close", lambda *_: "</table></div>\n")
    return md


def _image(smiles: str) -> str | None:
    """An <img> of a SMILES (or SMARTS) drawn by RDKit, or None if it cannot be drawn."""
    svg = substructure.depict_svg(smiles)
    if svg is None:
        return None
    uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return f'<img class="structure" alt="{_html.escape(smiles)}" src="{uri}">'


def _cell(tag: str, attrs: dict[str, Any], children: list[Token]) -> list[Token]:
    """The tokens of one table cell."""
    return [Token(f"{tag}_open", tag, 1, attrs=dict(attrs)),
            Token("inline", "", 0, children=children),
            Token(f"{tag}_close", tag, -1)]


def _add_structure_columns(tokens: list[Token]) -> tuple[list[Token], int]:
    """Insert a structure column before every table column whose header mentions SMILES.

    Returns the new token list and the number of structures drawn."""
    out: list[Token] = []
    drawn = 0
    smiles_cols: list[int] = []  # of the current table
    col = 0
    for i, token in enumerate(tokens):
        if token.type == "table_open":
            smiles_cols = []
        elif token.type == "tr_open":
            col = 0
        elif token.type in ("th_open", "td_open"):
            content = tokens[i + 1].content.strip()
            if token.type == "th_open" and "smiles" in content.lower():
                smiles_cols.append(col)
            if col in smiles_cols:
                tag = token.tag
                if tag == "th":
                    children = [Token("text", "", 0, content="structure")]
                else:
                    img = _image(content.strip("`")) if content else None
                    children = [Token("html_inline", "", 0, content=img)] if img else []
                    drawn += img is not None
                out += _cell(tag, token.attrs, children)
            col += 1
        out.append(token)
    return out, drawn


def markdown_to_html(markdown: str) -> tuple[str, int]:
    """A transcript's Markdown as a standalone HTML page, and the number of structures drawn."""
    md = _renderer()
    env: dict[str, Any] = {}
    tokens, drawn = _add_structure_columns(md.parse(markdown, env))
    title = next((line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")), "Transcript")
    if drawn:
        note = f"{drawn} structure{'' if drawn == 1 else 's'} drawn with RDKit."
    elif not substructure.rdkit_available():
        note = "Structures not drawn: RDKit is not installed on the server."
    else:
        note = ""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"{md.renderer.render(tokens, md.options, env)}"
        + (f"<footer>{note}</footer>\n" if note else "")
        + "</body>\n</html>\n"
    ), drawn
