"""The HTML transcript: a Markdown transcript as one standalone page, with structure drawings.

Modelled on mcp-okn's transcript_render. Every table with a SMILES column (in the answers as well as in
the tool calls) gets a structure column before it, the molecules of a column aligned on the core they
share (see depict). Figure links (![…](figures/<file>.png), from draw_structure_grid) become the figure.
RDKit draws on the server and the drawings are embedded as SVG data: images, so the page needs no network
when opened. Without RDKit there are no structure columns.
"""

from __future__ import annotations

import base64
import html as _html
from collections.abc import Callable
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token

from . import depict

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
img.structure { display: block; max-width: 300px; height: auto; }
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


def _images(smiles: list[str]) -> list[str | None]:
    """<img> drawings of a table column's SMILES (or SMARTS), aligned on their common core; None for a
    cell that cannot be drawn."""
    if not depict.available():
        return [None] * len(smiles)
    lay = depict.layout(smiles)
    out: list[str | None] = []
    for k, text in enumerate(smiles):
        svg = depict.svg(lay, k)
        uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode() if svg else None
        out.append(f'<img class="structure" alt="{_html.escape(text)}" src="{uri}">' if uri else None)
    return out


def _cell(tag: str, attrs: dict[str, Any], children: list[Token]) -> list[Token]:
    """The tokens of one table cell."""
    return [Token(f"{tag}_open", tag, 1, attrs=dict(attrs)),
            Token("inline", "", 0, children=children),
            Token(f"{tag}_close", tag, -1)]


def _cells(tokens: list[Token]):
    """(token index, table number, column, is header, text) of every table cell."""
    table, col = -1, 0
    for i, token in enumerate(tokens):
        if token.type == "table_open":
            table += 1
        elif token.type == "tr_open":
            col = 0
        elif token.type in ("th_open", "td_open"):
            yield i, table, col, token.type == "th_open", tokens[i + 1].content.strip()
            col += 1


def _add_structure_columns(tokens: list[Token]) -> tuple[list[Token], int]:
    """Insert a structure column before every table column whose header mentions SMILES.

    Returns the new token list and the number of structures drawn."""
    columns: dict[tuple[int, int], list[str]] = {}  # (table, column) -> the column's SMILES
    for _, table, col, header, text in _cells(tokens):
        if header and "smiles" in text.lower():
            columns[table, col] = []
        elif (table, col) in columns and not header:
            columns[table, col].append(text.strip("`"))
    images = {key: iter(_images(values)) for key, values in columns.items()}
    inserts: dict[int, list[Token]] = {}
    drawn = 0
    for i, table, col, header, _ in _cells(tokens):
        if (table, col) not in columns:
            continue
        if header:
            children = [Token("text", "", 0, content="structure")]
        else:
            img = next(images[table, col])
            children = [Token("html_inline", "", 0, content=img)] if img else []
            drawn += img is not None
        inserts[i] = _cell(tokens[i].tag, tokens[i].attrs, children)
    out: list[Token] = []
    for i, token in enumerate(tokens):
        out += inserts.get(i, [])
        out.append(token)
    return out, drawn


def _add_figures(tokens: list[Token], figure_html: Callable[[str], str | None]) -> tuple[list[Token], int]:
    """Replace each paragraph that is only a figure link, ![…](figures/<file>), with the figure."""
    out: list[Token] = []
    n = 0
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if (token.type == "paragraph_open" and i + 2 < len(tokens) and tokens[i + 1].type == "inline"
                and len(tokens[i + 1].children or []) == 1 and tokens[i + 1].children[0].type == "image"):
            src = str(tokens[i + 1].children[0].attrGet("src") or "")
            block = figure_html(src[len("figures/"):]) if src.startswith("figures/") else None
            if block:
                out.append(Token("html_block", "", 0, content=block))
                n += 1
                i += 3
                continue
        out.append(token)
        i += 1
    return out, n


def markdown_to_html(markdown: str, figure_html: Callable[[str], str | None] = lambda _: None,
                     ) -> tuple[str, int, int]:
    """A transcript's Markdown as a standalone HTML page, with the number of structures drawn in tables
    and of figures embedded. `figure_html` gives the HTML of a figure by its file name, or None."""
    md = _renderer()
    env: dict[str, Any] = {}
    tokens, drawn = _add_structure_columns(md.parse(markdown, env))
    tokens, n_figures = _add_figures(tokens, figure_html)
    title = next((line[2:].strip() for line in markdown.splitlines() if line.startswith("# ")), "Transcript")
    if drawn:
        note = f"{drawn} structure{'' if drawn == 1 else 's'} drawn with RDKit."
    elif not depict.available():
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
    ), drawn, n_figures
