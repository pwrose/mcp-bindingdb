"""Figure rendering that needs no database: the R-group table's columns, cells and two renderings."""

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
