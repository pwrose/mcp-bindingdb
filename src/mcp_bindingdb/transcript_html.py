"""The HTML transcript: the Markdown transcript as one standalone page, with structure drawings.

Modelled on mcp-okn's transcript_render. Structures are drawn by RDKit on the server and embedded as
SVG data: images, so the page needs no network when opened. Without RDKit the page has no drawings.
"""

from __future__ import annotations

import base64
import html as _html
from typing import Any

from markdown_it import MarkdownIt

from . import substructure

_SVG_URI = "data:image/svg+xml;base64,"

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


def depict(text: str, smarts: bool = False) -> str | None:
    """A Markdown image of a SMILES (or SMARTS) drawn by RDKit, or None if it cannot be drawn."""
    svg = substructure.depict_svg(text, smarts)
    if svg is None:
        return None
    return f"![structure]({_SVG_URI}{base64.b64encode(svg.encode()).decode()})"


def _renderer() -> MarkdownIt:
    """A GitHub-like renderer. Raw HTML is escaped, not passed through: answers and result cells are
    shown as text, never run. The only images allowed besides the defaults are SVG data URIs."""
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    default_validate = md.validateLink
    md.validateLink = lambda url: url.startswith(_SVG_URI) or default_validate(url)

    def image(self: Any, tokens: Any, idx: int, options: Any, env: Any) -> str:
        token = tokens[idx]
        if str(token.attrGet("src") or "").startswith(_SVG_URI):
            token.attrSet("class", "structure")
        return self.image(tokens, idx, options, env)

    md.add_render_rule("image", image)
    md.add_render_rule("table_open", lambda *_: '<div class="table-wrap"><table>\n')
    md.add_render_rule("table_close", lambda *_: "</table></div>\n")
    return md


def markdown_to_html(markdown: str, title: str, drawn: bool) -> str:
    """The transcript Markdown as a standalone HTML page; `drawn` says whether structures were drawn."""
    note = ("Structures drawn with RDKit." if drawn
            else "Structures are not drawn: RDKit is not installed on the server.")
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n"
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        f"{_renderer().render(markdown)}<footer>{note}</footer>\n</body>\n</html>\n"
    )
