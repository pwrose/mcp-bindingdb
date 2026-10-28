"""Figure rendering that needs no database: the R-group table's columns, cells and two renderings."""

import re

import pytest

from mcp_bindingdb import depict

if not depict.available():
    pytest.skip("RDKit not installed (substructure extra)", allow_module_level=True)

from mcp_bindingdb import figures  # noqa: E402

XANTHINE = "O=c1n([*:1])c(=O)c2[nH]c([*:3])nc2n1[*:2]"


def row(groups, title="Compound", **kwargs):
    return figures.RGroupRow(r_groups=groups, title=title, **kwargs)


def test_columns_are_the_union_of_the_rows_in_numeric_order():
    rows = [row({"R2": "C[*:1]", "R10": "F[*:1]"}), row({"R1": "C[*:1]", "R2": "H"})]
    assert figures.r_group_labels(rows) == ["R1", "R2", "R10"]


def test_cells_draw_groups_and_write_hydrogen_and_absence():
    rows = [row({"R1": "CCC[*:1]", "R2": "H", "R3": "[H][*:1]"}), row({"R1": "", "R2": "C[*:1]"})]
    cells = figures._r_group_cells(rows, figures.r_group_labels(rows))
    assert cells[0] == [("mol", "CCC[*:1]"), ("text", "H"), ("text", "H")]
    assert cells[1] == [("text", figures.RG_MISSING), ("mol", "C[*:1]"), ("text", figures.RG_MISSING)]


def test_html_draws_the_core_and_every_group_but_no_smiles_text():
    rows = [row({"R1": "CCC[*:1]", "R3": "C1CCCC1[*:1]"}, "DPCPX", subtitle="BDBM50058235",
                bars=[figures.GridBar(label="A1", value_nm=0.47, type="Ki", note="n = 45")]),
            row({"R1": "C[*:1]", "R3": "H"}, "Theophylline",
                bars=[figures.GridBar(label="A1", value_nm=6200, type="Ki", faint=True)])]
    html, png, labels, undrawn = figures.r_group_table("Xanthines", XANTHINE, rows,
                                                       column_notes={"R1": "N1"})
    assert labels == ["R1", "R3"] and not undrawn
    assert html.count("<img") == 4  # the core, two R1 groups and one R3 group; the hydrogen is written
    assert "<i>N1</i>" in html and ">H</span>" in html
    body = html.split("<tbody>")[1]
    assert "CCC[*:1]" not in body.replace('alt="CCC[*:1]"', "")  # groups are drawn, never spelled out
    assert png[:4] == b"\x89PNG" and figures.png_smiles(png)[0] == XANTHINE


def test_a_group_that_cannot_be_drawn_is_reported():
    rows = [row({"R1": "not a group ("})]
    html, _, labels, undrawn = figures.r_group_table("Broken", XANTHINE, rows)
    assert labels == ["R1"] and undrawn == ["not a group ("]
    assert "not a group (" in html  # written as text, so the row is still readable


def test_a_core_without_marked_positions_still_draws():
    html, png, labels, undrawn = figures.r_group_table("Plain", "c1ccccc1", [row({"R1": "C[*:1]"})])
    assert not undrawn and labels == ["R1"] and html.count("<img") == 2 and png[:4] == b"\x89PNG"


def test_every_bar_in_a_figure_starts_and_ends_at_the_same_place():
    # Each bar row is its own grid: label and value columns sized per row would shift and shorten the bars.
    bars = [figures.GridBar(label="ABL1", value_nm=1900, type="IC50"),
            figures.GridBar(label="PDGFR-α/β", value_nm=320, type="Kd")]
    html, *_ = figures.r_group_table("Bars", XANTHINE, [row({"R1": "C[*:1]"}, bars=bars),
                                                        row({"R1": "H"}, bars=bars[:1])])
    widths = re.search(r'<figure class="rg" style="--rg-label:(\d+)px;--rg-value:(\d+)px"', html)
    assert widths and int(widths[1]) > 60 and int(widths[2]) > 90
    assert "grid-template-columns:var(--rg-label,auto) minmax(" in html and "var(--rg-value,auto)" in html
    grid, *_ = figures.structure_grid("Grid", [figures.GridCompound(smiles="c1ccccc1O", title="a", bars=bars),
                                                figures.GridCompound(smiles="c1ccccc1N", title="b")])
    assert re.search(r'<figure class="sg" style="--sg-label:\d+px;--sg-value:\d+px"', grid)


def test_a_legend_wider_than_the_figure_wraps():
    from PIL import Image, ImageDraw

    draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    font = figures._font(13)
    legend = [("#000000", "Kd"), ("#111111", "IC50"), ("#222222", "thin evidence"),
              ("", "Bar length: log scale, 100000 nM (empty) to 0.01 nM (full)")]
    lines = figures._legend_lines(draw, legend, font, 220, 1)
    assert len(lines) > 1 and [entry for line in lines for entry in line][:3] == legend[:3]
    for line in lines:
        width = sum((19 if c else 0) + draw.textlength(t, font=font) for c, t in line) + 18 * (len(line) - 1)
        assert width <= 220
