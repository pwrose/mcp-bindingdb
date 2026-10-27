"""Figures for transcripts: structure grids and R-group tables the server draws, and images made elsewhere.

A structure grid (draw_structure_grid) shows compounds aligned on a shared core, with binding bars. An
R-group table (draw_r_group_table) shows one chemical series: the core drawn once with its positions
named R1, R2, ..., then a row per compound whose cells are the substituents themselves, drawn, never
their SMILES. Both are rendered twice from the same layout: an HTML block that HTML transcripts embed,
and a PNG that Markdown transcripts link to and the tool shows in the chat. RDKit draws the structures
(see depict); Pillow, which comes with RDKit, draws the PNG.

An image figure (add_figure) is a PNG, JPEG, GIF, WebP or SVG made with other tools, e.g. a matplotlib
plot, embedded as it is.
"""

from __future__ import annotations

import base64
import functools
import html
import io
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field

from . import depict

#: Fonts for the PNG, first found wins; else Pillow's built-in font, which lacks some characters.
FONT_FILES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",  # macOS
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Debian/Ubuntu
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",  # Fedora
    "C:\\Windows\\Fonts\\arial.ttf",
]
TYPE_COLOURS = {"Ki": "#2f6f8f", "Kd": "#3f8a5c", "IC50": "#7a5aa6", "EC50": "#a8662d"}
CORE_COLOUR = "#e8892e"
SMILES_KEY = "smiles"  # PNG text chunk: the SMILES of the compounds drawn, as a JSON list


class GridBar(BaseModel):
    label: str = Field(description="Target, e.g. 'RAF1'")
    value_nm: float = Field(gt=0, description="Affinity in nM; drawn on a log scale, longer = more potent")
    type: Literal["Ki", "Kd", "IC50", "EC50"] = Field(description="Measurement type of the value (sets the "
                                                      "bar colour); values of different types are not "
                                                      "comparable")
    note: str = Field("", description="Small print under the bar, e.g. 'n = 32 · Kd 230 nM (4)'")
    faint: bool = Field(False, description="Thin evidence (e.g. fewer than 3 measurements): drawn lighter")


class GridCompound(BaseModel):
    smiles: str = Field(description="The compound's SMILES")
    title: str = Field(description="Name, e.g. 'Sorafenib'")
    subtitle: str = Field("", description="One line under the name, e.g. 'FDA 2005 · Kidney, liver and "
                          "thyroid cancer'")
    caption: str = Field("", description="Short text under the structure, e.g. where the core sits")
    bars: list[GridBar] = Field(default_factory=list, description="Binding data for its main targets")


class RGroupRow(BaseModel):
    r_groups: dict[str, str] = Field(description="The row's substituents, as decompose_r_groups gives "
                                     "them: {'R1': 'CCC[*:1]', 'R2': 'H'}. Each is drawn in its column; "
                                     "'H' is written as text and a position the compound lacks is left "
                                     "out. The columns are the union of the rows' positions, in order")
    title: str = Field(description="Compound name or id, e.g. 'DPCPX'")
    subtitle: str = Field("", description="One line under the name, e.g. 'BDBM50058235 · 45 measurements'")
    bars: list[GridBar] = Field(default_factory=list, description="Potency of this row, one bar per target "
                                "or assay")


@dataclass
class Figure:
    id: int
    timestamp: str
    title: str
    file: str  # image file name, under the transcripts' figures/ folder
    html: str
    data: bytes  # the image file's content
    spec: dict[str, Any] = field(default_factory=dict)
    caption: str | None = None  # image figures: shown under the image in transcripts (grids have their own)


def _fmt(nm: float) -> str:
    """Three significant figures, without exponents: 0.25, 18, 48,000."""
    rounded = float(f"{nm:.3g}")
    return f"{rounded:,.0f}" if rounded >= 1000 else f"{rounded:g}"


def _scale(compounds: list[GridCompound]) -> tuple[float, float] | None:
    """The bar scale in nM: (empty, full), whole decades around all values."""
    values = [b.value_nm for c in compounds for b in c.bars]
    if not values:
        return None
    lo, hi = 10 ** math.floor(math.log10(min(values))), 10 ** math.ceil(math.log10(max(values)))
    return (hi * 10 if hi == lo else hi), lo


def _fraction(nm: float, scale: tuple[float, float]) -> float:
    empty, full = scale
    f = (math.log10(empty) - math.log10(nm)) / (math.log10(empty) - math.log10(full))
    return min(1.0, max(0.03, f))


def _legend(compounds: list[GridCompound], scale: tuple[float, float] | None, core: bool) -> list[tuple[str, str]]:
    """(colour, text) legend entries."""
    entries = [(CORE_COLOUR, "shared core")] if core else []
    types = list(dict.fromkeys(b.type for c in compounds for b in c.bars))
    entries += [(TYPE_COLOURS[t], t) for t in types]
    if any(b.faint for c in compounds for b in c.bars):
        entries.append(("#c8cfcb", "thin evidence"))
    if scale:
        entries.append(("", f"Bar length: log scale, {scale[0]:.10g} nM (empty) to {scale[1]:.10g} nM (full)"))
    return entries


_CSS = """
.sg{margin:1.5em 0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#1c2321}
.sg h3{margin:0 0 4px;font-size:1.3em}
.sg-desc{margin:0 0 14px;color:#5c6763;max-width:75ch}
.sg-grid{display:grid;gap:14px}
.sg-card{border:1px solid #dfe3e0;border-radius:8px;padding:14px;display:grid;grid-row:span 5;grid-template-rows:subgrid;row-gap:8px;min-width:0;background:#fff}
.sg-card h4{margin:0;font-size:1.25em}
.sg-sub{margin:0;color:#5c6763;font-size:13px}
.sg-plate{border:1px solid #dfe3e0;border-radius:4px;padding:2px;background:#fff}
.sg-plate img{display:block;width:100%;height:auto}
.sg-cap{margin:0;border-left:3px solid #e8892e;padding-left:8px;font-size:13px;align-self:start}
.sg-cap:empty{border:0}
.sg-bars{list-style:none;margin:0;padding:0;display:grid;gap:7px;align-content:start}
.sg-row{display:grid;grid-template-columns:7em minmax(0,1fr) 8.5em;column-gap:8px;align-items:center;font-size:13px}
.sg-track{height:9px;background:#eceeec;border-radius:2px;overflow:hidden}
.sg-bar{display:block;height:100%;border-radius:2px}
.sg-faint .sg-bar{opacity:.4}
.sg-val{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;text-align:right;white-space:nowrap}
.sg-val i{font-style:normal;color:#5c6763;font-size:11px}
.sg-note{grid-column:2/4;font-size:11px;color:#5c6763;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.sg-legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin:12px 0 0;font-size:12px;color:#5c6763}
.sg-legend span{display:inline-flex;align-items:center;gap:6px}
.sg-sw{width:13px;height:9px;border-radius:2px;display:inline-block}
.sg-notes{margin:10px 0 0;padding-left:1.2em;font-size:13px;color:#5c6763}
@media (max-width:800px){.sg-grid{grid-template-columns:minmax(0,1fr)!important}}
"""


def _html(title: str, description: str, compounds: list[GridCompound], lay: depict.Layout, columns: int,
          notes: list[str]) -> str:
    e = html.escape
    scale = _scale(compounds)
    cards = []
    for k, c in enumerate(compounds):
        svg = depict.svg(lay, k)
        plate = (f'<div class="sg-plate"><img alt="{e(c.smiles)}" src="data:image/svg+xml;base64,'
                 f'{base64.b64encode(svg.encode()).decode()}"></div>') if svg else f"<p><code>{e(c.smiles)}</code></p>"
        rows = []
        for b in c.bars:
            colour = TYPE_COLOURS[b.type]
            width = f"{100 * _fraction(b.value_nm, scale):.1f}%" if scale else "0"
            rows.append(
                f'<li class="sg-row{" sg-faint" if b.faint else ""}"><span>{e(b.label)}</span>'
                f'<span class="sg-track"><span class="sg-bar" style="width:{width};background:{colour}"></span></span>'
                f'<span class="sg-val">{_fmt(b.value_nm)} nM <i>{e(b.type)}</i></span>'
                + (f'<span class="sg-note">{e(b.note)}</span>' if b.note else "") + "</li>")
        # Always the same five parts, so the subgrid lines them up across the cards of a row.
        cards.append(f'<article class="sg-card"><h4>{e(c.title)}</h4><p class="sg-sub">{e(c.subtitle)}</p>{plate}'
                     f'<p class="sg-cap">{e(c.caption)}</p><ul class="sg-bars">{"".join(rows)}</ul></article>')
    swatch = '<i class="sg-sw" style="background:{}"></i>'
    legend = "".join(f"<span>{swatch.format(c) if c else ''}{e(t)}</span>"
                     for c, t in _legend(compounds, scale, any(lay.cores)))
    return (
        f'<figure class="sg"><style>{_CSS}</style><h3>{e(title)}</h3>'
        + (f'<p class="sg-desc">{e(description)}</p>' if description else "")
        + f'<div class="sg-grid" style="grid-template-columns:repeat({columns},minmax(0,1fr))">{"".join(cards)}</div>'
        + (f'<p class="sg-legend">{legend}</p>' if legend else "")
        + (f'<ul class="sg-notes">{"".join(f"<li>{e(n)}</li>" for n in notes)}</ul>' if notes else "")
        + "</figure>\n"
    )


def _font(size: int) -> Any:
    from PIL import ImageFont

    for path in FONT_FILES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow < 10.1 has no scalable default font
        return ImageFont.load_default()


def _plain(font: Any, text: str) -> str:
    """Text the font can draw: Pillow's built-in font has no dashes or bullets."""
    if getattr(font, "path", None):
        return text
    return text.translate(str.maketrans({"–": "-", "—": "-", "•": "-", "−": "-", "’": "'"}))


def _wrap(draw: Any, text: str, font: Any, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [""]:
        line = ""
        for word in paragraph.split():
            trial = f"{line} {word}".strip()
            if line and draw.textlength(trial, font=font) > width:
                lines.append(line)
                line = word
            else:
                line = trial
        lines.append(line)
    return lines


def _fit(draw: Any, text: str, font: Any, width: float) -> str:
    """`text`, shortened with an ellipsis if it is wider than `width`."""
    if width <= 0 or draw.textlength(text, font=font) <= width:
        return text
    while text and draw.textlength(text + "...", font=font) > width:
        text = text[:-1]
    return text + "..."


def _png(title: str, description: str, compounds: list[GridCompound], lay: depict.Layout, columns: int,
         notes: list[str], s: int = 2) -> bytes:
    """The figure as a PNG at `s` times its CSS pixel size."""
    from PIL import Image, ImageDraw, PngImagePlugin

    ink, muted, line = (28, 35, 33), (92, 103, 99), (223, 227, 224)
    f_title, f_name, f_text, f_small = _font(24 * s), _font(19 * s), _font(13 * s), _font(11 * s)
    pad, gap = 14 * s, 14 * s
    plate_w = max(max((lay.size(k)[0] for k in range(len(compounds)) if lay.mols[k] is not None), default=200),
                  240) * s
    card_w = plate_w + 2 * pad
    columns = max(1, min(columns, len(compounds)))
    total_w = columns * card_w + (columns - 1) * gap + 2 * pad
    scale = _scale(compounds)
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def lh(font: Any) -> int:
        return round(font.size * 1.35)

    # Lay out each card's lines first, to know its height. Subtitles in a row take the same number of lines,
    # so the structures (and their shared core) line up across the row.
    subs = [_wrap(measure, c.subtitle, f_text, plate_w) if c.subtitle else [] for c in compounds]
    for i in range(0, len(subs), columns):
        n = max(len(sub) for sub in subs[i:i + columns])
        for sub in subs[i:i + columns]:
            sub += [""] * (n - len(sub))
    cards = []
    for k, c in enumerate(compounds):
        structure = depict.png(lay, k, scale=s)
        img = Image.open(io.BytesIO(structure)).convert("RGB") if structure else None
        if img is not None and img.width > plate_w:
            img = img.resize((plate_w, round(img.height * plate_w / img.width)))
        sub = subs[k]
        cap = _wrap(measure, c.caption, f_text, plate_w - 10 * s) if c.caption else []
        bar_h = sum(lh(f_text) + (lh(f_small) if b.note else 0) + 4 * s for b in c.bars)
        height = (pad + lh(f_name) + len(sub) * lh(f_text) + 6 * s + (img.height if img else lh(f_text)) + 8 * s
                  + len(cap) * lh(f_text) + (6 * s if cap else 0) + bar_h + pad)
        cards.append((c, img, sub, cap, height))
    head = _wrap(measure, description, f_text, total_w - 2 * pad) if description else []
    head_title = _wrap(measure, title, f_title, total_w - 2 * pad)
    legend = _legend(compounds, scale, any(lay.cores))
    note_lines = [ln for n in notes for ln in _wrap(measure, "• " + n, f_text, total_w - 2 * pad)]
    labels = [b.label for c in compounds for b in c.bars]
    label_w = min(max((measure.textlength(t, font=f_text) for t in labels), default=0) + 10 * s, plate_w * 0.4)
    rows = [cards[i:i + columns] for i in range(0, len(cards), columns)]
    row_h = [max(c[4] for c in row) for row in rows]
    total_h = (pad + len(head_title) * lh(f_title) + len(head) * lh(f_text) + 10 * s + sum(row_h)
               + gap * (len(rows) - 1)
               + (10 * s + lh(f_text) if legend else 0) + len(note_lines) * lh(f_text) + pad)

    image = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    d = ImageDraw.Draw(image)
    y = pad
    for text in head_title:
        d.text((pad, y), _plain(f_title, text), font=f_title, fill=ink)
        y += lh(f_title)
    for text in head:
        d.text((pad, y), _plain(f_text, text), font=f_text, fill=muted)
        y += lh(f_text)
    y += 10 * s
    for row, height in zip(rows, row_h):
        x0 = pad
        for c, img, sub, cap, _ in row:
            d.rounded_rectangle((x0, y, x0 + card_w, y + height), radius=8 * s, outline=line, width=s)
            x, cy = x0 + pad, y + pad
            d.text((x, cy), _plain(f_name, c.title), font=f_name, fill=ink)
            cy += lh(f_name)
            for text in sub:
                d.text((x, cy), _plain(f_text, text), font=f_text, fill=muted)
                cy += lh(f_text)
            cy += 6 * s
            if img is not None:
                image.paste(img, (x, cy))
                d.rectangle((x, cy, x + img.width, cy + img.height), outline=line, width=s)
                cy += img.height
            else:
                d.text((x, cy), c.smiles, font=f_small, fill=muted)
                cy += lh(f_text)
            cy += 8 * s
            if cap:
                d.rectangle((x, cy, x + 2 * s, cy + len(cap) * lh(f_text)), fill=CORE_COLOUR)
                for text in cap:
                    d.text((x + 10 * s, cy), _plain(f_text, text), font=f_text, fill=ink)
                    cy += lh(f_text)
                cy += 6 * s
            value_w = max([84 * s] + [d.textlength(f"{_fmt(b.value_nm)} nM {b.type}", font=f_text)
                                      for other in compounds for b in other.bars])  # the same in every card
            track_x0, track_x1 = x + label_w, x + plate_w - value_w - 6 * s
            for b in c.bars:
                colour = TYPE_COLOURS[b.type]
                rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
                if b.faint:
                    rgb = tuple(round(v * 0.4 + 255 * 0.6) for v in rgb)
                mid = cy + lh(f_text) // 2
                d.text((x, cy), _fit(d, _plain(f_text, b.label), f_text, label_w - 8 * s),
                       font=f_text, fill=ink)
                d.rectangle((track_x0, mid - 4 * s, track_x1, mid + 4 * s), fill=(236, 238, 236))
                if scale:
                    end = track_x0 + (track_x1 - track_x0) * _fraction(b.value_nm, scale)
                    d.rectangle((track_x0, mid - 4 * s, end, mid + 4 * s), fill=rgb)
                value = f"{_fmt(b.value_nm)} nM {b.type}".strip()
                d.text((x + plate_w - d.textlength(value, font=f_text), cy), value, font=f_text, fill=ink)
                cy += lh(f_text)
                if b.note:
                    d.text((track_x0, cy), _plain(f_small, b.note), font=f_small, fill=muted)
                    cy += lh(f_small)
                cy += 4 * s
            x0 += card_w + gap
        y += height + gap
    y += 10 * s - gap
    if legend:
        x = pad
        for colour, text in legend:
            if colour:
                d.rectangle((x, y + 4 * s, x + 13 * s, y + 13 * s), fill=colour)
                x += 19 * s
            d.text((x, y), _plain(f_text, text), font=f_text, fill=muted)
            x += d.textlength(_plain(f_text, text), font=f_text) + 18 * s
        y += lh(f_text)
    for text in note_lines:
        d.text((pad, y), _plain(f_text, text), font=f_text, fill=muted)
        y += lh(f_text)
    out = io.BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text(SMILES_KEY, json.dumps([c.smiles for c in compounds]))  # see png_smiles
    image.save(out, format="PNG", optimize=True, pnginfo=info)
    return out.getvalue()


def png_smiles(png: bytes) -> list[str]:
    """The SMILES of the compounds a figure PNG draws, from its metadata; empty if it has none."""
    from PIL import Image

    try:
        smiles = json.loads(Image.open(io.BytesIO(png)).text.get(SMILES_KEY, "[]"))
    except (OSError, ValueError, AttributeError):
        return []
    return [s for s in smiles if isinstance(s, str)] if isinstance(smiles, list) else []


def structure_grid(title: str, compounds: list[GridCompound], align_to: str | None = None, columns: int = 3,
                   description: str = "", notes: list[str] | None = None) -> tuple[str, bytes, depict.Layout]:
    """The figure as (HTML block, PNG, layout)."""
    lay = depict.layout([c.smiles for c in compounds], align_to)
    columns = max(1, min(columns, len(compounds)))
    notes = [n for n in notes or [] if n.strip()]
    return (_html(title, description, compounds, lay, columns, notes),
            _png(title, description, compounds, lay, columns, notes), lay)


RG_MISSING = "–"  # a position the compound does not have at all
RG_HYDROGEN = re.compile(r"\[?H\]?(\[\*:?\d*\])?", re.IGNORECASE)  # 'H', '[H][*:1]': written, not drawn
RG_NONE = {"", "-", "–", "—", "none", "null", "n/a"}
RG_TRACK = 120  # bar track width in CSS pixels; the structures set the rest of the table's width


def _r_group_order(label: str) -> tuple[int, str]:
    """R1, R2, ... in numeric order, anything else after them in alphabetical order."""
    match = re.fullmatch(r"\s*R(\d+)\s*", label, re.IGNORECASE)
    return (int(match.group(1)), "") if match else (1_000_000, label)


def r_group_labels(rows: list[RGroupRow]) -> list[str]:
    """The table's columns: every position any row carries, R1, R2, ... first."""
    return sorted({label for row in rows for label in row.r_groups}, key=_r_group_order)


def _r_group_cells(rows: list[RGroupRow], labels: list[str]) -> list[list[tuple[str, str]]]:
    """Per row and column, ('mol', smiles) to draw or ('text', 'H' | '–') to write."""
    cells = []
    for row in rows:
        line = []
        for label in labels:
            value = (row.r_groups.get(label) or "").strip()
            if value.lower() in RG_NONE:
                line.append(("text", RG_MISSING))
            elif RG_HYDROGEN.fullmatch(value):
                line.append(("text", "H"))
            else:
                line.append(("mol", value))
        cells.append(line)
    return cells


@functools.lru_cache(maxsize=4096)
def _part(smiles: str, scale: int, core: bool) -> tuple[str | None, bytes | None, tuple[int, int]]:
    """One piece of an R-group table as (SVG, PNG, CSS pixel size); (None, None, (0, 0)) if unparsable.

    A core is drawn with its positions named R1, R2, ...; a substituent with its attachment point as the
    bond stub where it joins the core.
    """
    lay = depict.layout([smiles], label_r_groups=core, attachments=not core)
    if lay.mols[0] is None:
        return None, None, (0, 0)
    return depict.svg(lay, 0), depict.png(lay, 0, scale=scale), lay.size(0)


def _core_caption(labels: list[str]) -> str:
    if not labels:
        return "The core shared by every row."
    one = len(labels) == 1
    names = labels[0] if one else f"{', '.join(labels[:-1])} and {labels[-1]}"
    return (f"The core shared by every row. {names} {'is' if one else 'are'} the "
            f"{'column' if one else 'columns'} of the table; the rest of the structure is the same "
            "in every row.")


_RG_CSS = """
.rg{margin:1.5em 0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#1c2321}
.rg h3{margin:0 0 4px;font-size:1.3em}
.rg-desc{margin:0 0 14px;color:#5c6763;max-width:75ch}
.rg-core{display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin:0 0 16px}
.rg-plate{border:1px solid #dfe3e0;border-radius:8px;padding:6px;background:#fff}
.rg-plate img{display:block}
.rg-core-cap{margin:0;border-left:3px solid #e8892e;padding-left:10px;font-size:13px;color:#5c6763;max-width:48ch}
.rg-tab{border-collapse:collapse;width:100%;font-size:13px}
.rg-tab th,.rg-tab td{text-align:left;vertical-align:middle;padding:9px 10px;border-top:1px solid #eceeec}
.rg-tab thead th{border-top:0;border-bottom:1px solid #dfe3e0;font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:#5c6763}
.rg-tab thead th i{display:block;font-style:normal;text-transform:none;letter-spacing:0;color:#8d9793}
.rg-name{font-size:15px;font-weight:600;white-space:nowrap}
.rg-name i{display:block;font-style:normal;font-weight:400;color:#5c6763;font-size:12px;white-space:normal}
.rg-cell img{display:block}
.rg-plain{color:#5c6763;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.rg-bars{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.rg-row{display:grid;grid-template-columns:auto minmax(TRACKpx,1fr) auto;column-gap:8px;align-items:center}
.rg-track{height:9px;background:#eceeec;border-radius:2px;overflow:hidden}
.rg-bar{display:block;height:100%;border-radius:2px}
.rg-faint .rg-bar{opacity:.4}
.rg-val{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;text-align:right;white-space:nowrap}
.rg-val i{font-style:normal;color:#5c6763;font-size:11px}
.rg-note{grid-column:2/4;font-size:11px;color:#5c6763;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.rg-legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin:12px 0 0;font-size:12px;color:#5c6763}
.rg-legend span{display:inline-flex;align-items:center;gap:6px}
.rg-sw{width:13px;height:9px;border-radius:2px;display:inline-block}
.rg-notes{margin:10px 0 0;padding-left:1.2em;font-size:13px;color:#5c6763}
""".replace("TRACK", str(RG_TRACK))


def _rg_bars_html(bars: list[GridBar], scale: tuple[float, float] | None) -> str:
    e = html.escape
    rows = []
    for b in bars:
        width = f"{100 * _fraction(b.value_nm, scale):.1f}%" if scale else "0"
        rows.append(
            f'<li class="rg-row{" rg-faint" if b.faint else ""}"><span>{e(b.label)}</span>'
            f'<span class="rg-track"><span class="rg-bar" style="width:{width};'
            f'background:{TYPE_COLOURS[b.type]}"></span></span>'
            f'<span class="rg-val">{_fmt(b.value_nm)} nM <i>{e(b.type)}</i></span>'
            + (f'<span class="rg-note">{e(b.note)}</span>' if b.note else "") + "</li>")
    return f'<ul class="rg-bars">{"".join(rows)}</ul>' if rows else ""


def _rg_html(title: str, description: str, core: str, caption: str, heading: str, labels: list[str],
             column_notes: dict[str, str], rows: list[RGroupRow], cells: list[list[tuple[str, str]]],
             notes: list[str]) -> str:
    e = html.escape
    scale = _scale(rows)

    def plate(svg: str | None, size: tuple[int, int], alt: str, classes: str) -> str:
        if not svg:
            return f'<span class="rg-plain">{e(alt)}</span>'
        return (f'<span class="{classes}"><img alt="{e(alt)}" width="{size[0]}" height="{size[1]}" '
                f'src="data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"></span>')

    core_svg, _, core_size = _part(core, 1, True)
    head = "".join(f'<th>{e(label)}' + (f"<i>{e(column_notes[label])}</i>" if column_notes.get(label) else "")
                   + "</th>" for label in labels)
    def cell(kind: str, value: str) -> str:
        if kind != "mol":
            return f'<span class="rg-plain">{e(value)}</span>'
        svg, _, size = _part(value, 1, False)
        return plate(svg, size, value, "rg-cell-img")

    body = []
    for row, line in zip(rows, cells):
        drawn = "".join(f'<td class="rg-cell">{cell(kind, value)}</td>' for kind, value in line)
        body.append(f'<tr><th scope="row" class="rg-name">{e(row.title)}'
                    + (f"<i>{e(row.subtitle)}</i>" if row.subtitle else "") + "</th>"
                    + drawn + f'<td class="rg-data">{_rg_bars_html(row.bars, scale)}</td></tr>')
    swatch = '<i class="rg-sw" style="background:{}"></i>'
    legend = "".join(f"<span>{swatch.format(c) if c else ''}{e(t)}</span>"
                     for c, t in _legend(rows, scale, False))
    return (
        f'<figure class="rg"><style>{_RG_CSS}</style><h3>{e(title)}</h3>'
        + (f'<p class="rg-desc">{e(description)}</p>' if description else "")
        + f'<div class="rg-core">{plate(core_svg, core_size, core, "rg-plate")}'
        + f'<p class="rg-core-cap">{e(caption)}</p></div>'
        + f'<table class="rg-tab"><thead><tr><th>{e(heading)}</th>{head}<th>Affinity</th></tr></thead>'
        + f'<tbody>{"".join(body)}</tbody></table>'
        + (f'<p class="rg-legend">{legend}</p>' if legend else "")
        + (f'<ul class="rg-notes">{"".join(f"<li>{e(n)}</li>" for n in notes)}</ul>' if notes else "")
        + "</figure>\n"
    )


def _rg_png(title: str, description: str, core: str, caption: str, heading: str, labels: list[str],
            column_notes: dict[str, str], rows: list[RGroupRow], cells: list[list[tuple[str, str]]],
            notes: list[str], s: int = 2) -> bytes:
    """The R-group table as a PNG at `s` times its CSS pixel size."""
    from PIL import Image, ImageDraw, PngImagePlugin

    ink, muted, line, rule, track_bg = (28, 35, 33), (92, 103, 99), (223, 227, 224), (236, 238, 236), (236, 238, 236)
    f_title, f_name, f_text, f_small, f_head = (_font(24 * s), _font(16 * s), _font(13 * s), _font(11 * s),
                                                _font(12 * s))
    pad, cellpad = 14 * s, 9 * s
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    scale = _scale(rows)

    def lh(font: Any) -> int:
        return round(font.size * 1.35)

    def image_of(smiles: str, core_part: bool = False) -> Any:
        data = _part(smiles, s, core_part)[1]
        return Image.open(io.BytesIO(data)).convert("RGB") if data else None

    pictures = {value: image_of(value) for row in cells for kind, value in row if kind == "mol"}
    # Column widths: the structures decide, with room for the heading above them.
    col_w = []
    for i, label in enumerate(labels):
        width = measure.textlength(label.upper(), font=f_head)
        if column_notes.get(label):
            width = max(width, measure.textlength(_plain(f_small, column_notes[label]), font=f_small))
        for row in cells:
            kind, value = row[i]
            picture = pictures.get(value) if kind == "mol" else None
            width = max(width, picture.width if picture is not None else
                        measure.textlength(value if kind == "text" else "?", font=f_text))
        col_w.append(round(max(width, 48 * s)) + 2 * cellpad)
    names = [(_wrap(measure, r.title, f_name, 260 * s), _wrap(measure, r.subtitle, f_small, 260 * s) if r.subtitle
              else []) for r in rows]
    name_w = round(max([measure.textlength(t, font=f_name) for title, _ in names for t in title]
                       + [measure.textlength(t, font=f_small) for _, sub in names for t in sub]
                       + [measure.textlength(heading.upper(), font=f_head)])) + 2 * cellpad
    bars = [b for r in rows for b in r.bars]
    label_w = round(max((measure.textlength(b.label, font=f_text) for b in bars), default=0))
    value_w = round(max((measure.textlength(f"{_fmt(b.value_nm)} nM {b.type}", font=f_text) for b in bars),
                        default=0))
    bars_w = (label_w + RG_TRACK * s + value_w + 16 * s + 2 * cellpad) if bars else 0
    total_w = pad + name_w + sum(col_w) + bars_w + pad

    head_lines = _wrap(measure, description, f_text, total_w - 2 * pad) if description else []
    head_title = _wrap(measure, title, f_title, total_w - 2 * pad)
    note_lines = [ln for n in notes for ln in _wrap(measure, "• " + n, f_text, total_w - 2 * pad)]
    legend = _legend(rows, scale, False)
    core_img = image_of(core, True)
    core_h = (core_img.height + 12 * s + 2 * s) if core_img is not None else lh(f_text)
    core_cap = _wrap(measure, caption,
                     f_text, max(total_w - 2 * pad - (core_img.width + 12 * s if core_img else 0) - 24 * s, 180 * s))
    core_block = max(core_h, len(core_cap) * lh(f_text))
    header_h = lh(f_head) + (lh(f_small) if any(column_notes.get(label) for label in labels) else 0) + 10 * s
    row_h = []
    for (title_lines, sub_lines), line_cells, row in zip(names, cells, rows):
        picture_h = max([pictures[v].height for kind, v in line_cells if kind == "mol" and pictures.get(v)]
                        + [lh(f_text)])
        bar_h = sum(lh(f_text) + (lh(f_small) if b.note else 0) + 4 * s for b in row.bars)
        text_h = len(title_lines) * lh(f_name) + len(sub_lines) * lh(f_small)
        row_h.append(max(picture_h, bar_h, text_h) + 2 * cellpad)
    total_h = (pad + len(head_title) * lh(f_title) + len(head_lines) * lh(f_text) + 12 * s + core_block
               + 16 * s + header_h
               + sum(row_h) + (12 * s + lh(f_text) if legend else 0) + len(note_lines) * lh(f_text) + pad)

    image = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    d = ImageDraw.Draw(image)
    y = pad
    for text in head_title:
        d.text((pad, y), _plain(f_title, text), font=f_title, fill=ink)
        y += lh(f_title)
    for text in head_lines:
        d.text((pad, y), _plain(f_text, text), font=f_text, fill=muted)
        y += lh(f_text)
    y += 12 * s
    x = pad
    if core_img is not None:  # the core, drawn once, with its positions named
        d.rounded_rectangle((x, y, x + core_img.width + 12 * s, y + core_img.height + 12 * s), radius=8 * s,
                            outline=line, width=s)
        image.paste(core_img, (x + 6 * s, y + 6 * s))
        x += core_img.width + 12 * s + 14 * s
    cap_y = y + max(0, (core_block - len(core_cap) * lh(f_text)) // 2)
    d.rectangle((x, cap_y, x + 2 * s, cap_y + len(core_cap) * lh(f_text)), fill=CORE_COLOUR)
    for text in core_cap:
        d.text((x + 10 * s, cap_y), _plain(f_text, text), font=f_text, fill=muted)
        cap_y += lh(f_text)
    y += core_block + 16 * s

    columns = [pad, pad + name_w]
    for width in col_w:
        columns.append(columns[-1] + width)
    d.text((pad + cellpad, y), _plain(f_head, heading.upper()), font=f_head, fill=muted)
    for label, x0 in zip(labels, columns[1:]):
        d.text((x0 + cellpad, y), _plain(f_head, label.upper()), font=f_head, fill=muted)
        if column_notes.get(label):
            d.text((x0 + cellpad, y + lh(f_head)), _plain(f_small, column_notes[label]), font=f_small,
                   fill=(141, 151, 147))
    if bars:
        d.text((columns[-1] + cellpad, y), "AFFINITY", font=f_head, fill=muted)
    y += header_h
    d.line((pad, y - 5 * s, total_w - pad, y - 5 * s), fill=line, width=s)
    for k, ((title_lines, sub_lines), line_cells, row, height) in enumerate(zip(names, cells, rows, row_h)):
        if k:  # the header already has a rule under it
            d.line((pad, y, total_w - pad, y), fill=rule, width=s)
        ty = y + cellpad
        for text in title_lines:
            d.text((pad + cellpad, ty), _plain(f_name, text), font=f_name, fill=ink)
            ty += lh(f_name)
        for text in sub_lines:
            d.text((pad + cellpad, ty), _plain(f_small, text), font=f_small, fill=muted)
            ty += lh(f_small)
        for (kind, value), x0, width in zip(line_cells, columns[1:], col_w):
            picture = pictures.get(value) if kind == "mol" else None
            if picture is not None:
                image.paste(picture, (x0 + (width - picture.width) // 2,
                                      y + (height - picture.height) // 2))
            else:
                text = value if kind == "text" else value[:12]
                d.text((x0 + (width - measure.textlength(text, font=f_text)) // 2,
                        y + (height - lh(f_text)) // 2), _plain(f_text, text), font=f_text, fill=muted)
        by = y + (height - sum(lh(f_text) + (lh(f_small) if b.note else 0) + 4 * s for b in row.bars)) // 2
        track_x0 = columns[-1] + cellpad + label_w + 8 * s
        track_x1 = track_x0 + RG_TRACK * s
        for b in row.bars:
            colour = TYPE_COLOURS[b.type]
            rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
            if b.faint:
                rgb = tuple(round(v * 0.4 + 255 * 0.6) for v in rgb)
            mid = by + lh(f_text) // 2
            d.text((columns[-1] + cellpad, by), _plain(f_text, b.label), font=f_text, fill=ink)
            d.rectangle((track_x0, mid - 4 * s, track_x1, mid + 4 * s), fill=track_bg)
            if scale:
                end = track_x0 + (track_x1 - track_x0) * _fraction(b.value_nm, scale)
                d.rectangle((track_x0, mid - 4 * s, end, mid + 4 * s), fill=rgb)
            value = f"{_fmt(b.value_nm)} nM {b.type}"
            d.text((track_x1 + 8 * s, by), value, font=f_text, fill=ink)
            by += lh(f_text)
            if b.note:
                d.text((track_x0, by), _plain(f_small, b.note), font=f_small, fill=muted)
                by += lh(f_small)
            by += 4 * s
        y += height
    y += 12 * s
    if legend:
        x = pad
        for colour, text in legend:
            if colour:
                d.rectangle((x, y + 4 * s, x + 13 * s, y + 13 * s), fill=colour)
                x += 19 * s
            d.text((x, y), _plain(f_text, text), font=f_text, fill=muted)
            x += d.textlength(_plain(f_text, text), font=f_text) + 18 * s
        y += lh(f_text)
    for text in note_lines:
        d.text((pad, y), _plain(f_text, text), font=f_text, fill=muted)
        y += lh(f_text)
    out = io.BytesIO()
    info = PngImagePlugin.PngInfo()
    info.add_text(SMILES_KEY, json.dumps([core] + [v for row in cells for kind, v in row if kind == "mol"]))
    image.save(out, format="PNG", optimize=True, pnginfo=info)
    return out.getvalue()


def r_group_table(title: str, core: str, rows: list[RGroupRow], description: str = "",
                  column_notes: dict[str, str] | None = None, notes: list[str] | None = None,
                  core_caption: str = "", row_heading: str = "Compound"
                  ) -> tuple[str, bytes, list[str], list[str]]:
    """An R-group table as (HTML block, PNG, columns, parts that could not be drawn).

    The core is drawn once above the table with its positions named R1, R2, ...; every cell is the
    substituent itself, drawn, so no SMILES is shown.
    """
    labels = r_group_labels(rows)
    cells = _r_group_cells(rows, labels)
    column_notes = {k: v for k, v in (column_notes or {}).items() if v}
    notes = [n for n in notes or [] if n.strip()]
    caption = core_caption.strip() or _core_caption(labels)
    heading = row_heading.strip() or "Compound"
    undrawn = [text for text in [core] + sorted({v for row in cells for kind, v in row if kind == "mol"})
               if _part(text, 1, text == core)[0] is None]
    return (_rg_html(title, description, core, caption, heading, labels, column_notes, rows, cells, notes),
            _rg_png(title, description, core, caption, heading, labels, column_notes, rows, cells, notes),
            labels, undrawn)


#: Image formats add_figure accepts: file extension -> media type.
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp",
               ".svg": "image/svg+xml"}
MAX_IMAGE_BYTES = 20_000_000


def image_type(data: bytes) -> str | None:
    """The file extension for an image's content (see IMAGE_TYPES), or None if it is not one of them."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    head = data[:1000].lstrip(b"\xef\xbb\xbf \t\r\n").lower()
    if head.startswith((b"<svg", b"<?xml", b"<!doctype svg", b"<!--")) and b"<svg" in data[:5000].lower():
        return ".svg"
    return None


def image_html(title: str, data: bytes, ext: str) -> str:
    """An image figure as an HTML block; the image is embedded, so the page needs nothing else. Its title
    and caption follow as text in the transcript."""
    uri = f"data:{IMAGE_TYPES[ext]};base64,{base64.b64encode(data).decode()}"
    return f'<p><img class="figure" alt="{html.escape(title)}" src="{uri}"></p>\n'
