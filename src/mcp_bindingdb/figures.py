"""Structure-grid figures (draw_structure_grid): compounds aligned on a shared core, with binding bars.

Each figure is rendered twice from the same layout: an HTML block that HTML transcripts embed, and a PNG
that Markdown transcripts link to and the tool shows in the chat. RDKit draws the structures (see
depict); Pillow, which comes with RDKit, draws the PNG.
"""

from __future__ import annotations

import base64
import html
import io
import json
import math
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


@dataclass
class Figure:
    id: int
    timestamp: str
    title: str
    file: str  # PNG file name, under the transcripts' figures/ folder
    html: str
    png: bytes
    spec: dict[str, Any] = field(default_factory=dict)


def _fmt(nm: float) -> str:
    return f"{nm:.3g}"


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
.sg-row{display:grid;grid-template-columns:7em minmax(0,1fr) 6.5em;column-gap:8px;align-items:center;font-size:13px}
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
    legend = _legend(compounds, scale, any(lay.cores))
    note_lines = [ln for n in notes for ln in _wrap(measure, "• " + n, f_text, total_w - 2 * pad)]
    labels = [b.label for c in compounds for b in c.bars]
    label_w = min(max((measure.textlength(t, font=f_text) for t in labels), default=0) + 10 * s, plate_w * 0.4)
    rows = [cards[i:i + columns] for i in range(0, len(cards), columns)]
    row_h = [max(c[4] for c in row) for row in rows]
    total_h = (pad + lh(f_title) + len(head) * lh(f_text) + 10 * s + sum(row_h) + gap * (len(rows) - 1)
               + (10 * s + lh(f_text) if legend else 0) + len(note_lines) * lh(f_text) + pad)

    image = Image.new("RGB", (total_w, total_h), (255, 255, 255))
    d = ImageDraw.Draw(image)
    y = pad
    d.text((pad, y), _plain(f_title, title), font=f_title, fill=ink)
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
            value_w = 84 * s
            track_x0, track_x1 = x + label_w, x + plate_w - value_w - 6 * s
            for b in c.bars:
                colour = TYPE_COLOURS[b.type]
                rgb = tuple(int(colour[i:i + 2], 16) for i in (1, 3, 5))
                if b.faint:
                    rgb = tuple(round(v * 0.4 + 255 * 0.6) for v in rgb)
                mid = cy + lh(f_text) // 2
                d.text((x, cy), _plain(f_text, b.label), font=f_text, fill=ink)
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
