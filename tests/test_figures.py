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


# Six JAK1 inhibitors of about 40 atoms each, from example 3.6. rdFMCS reaches their 32-atom common core
# in well under a second but never proves it maximal, so it reports `canceled` however long it is given.
JAK_SERIES = [
    "COC[C@H](C(=O)Nc1cccc2c(-c3nc(Nc4ccc(C(=O)OC)nc4)ncc3F)c[nH]c12)N1CCN(C)CC1",
    "COC[C@H](C(=O)Nc1cccc2c(-c3nc(Nc4ccc(-c5ncco5)nc4)ncc3F)c[nH]c12)N1CCN(C)CC1",
    "COC[C@H](C(=O)Nc1cccc2c(-c3nc(Nc4ccc(OCC(=O)OC)nc4)ncc3F)c[nH]c12)N1CCN(C)CC1",
    "CCOC(=O)c1ccc(Nc2ncc(F)c(-c3c[nH]c4c(NC(=O)[C@@H](COC)N5CCN(C)CC5)cccc34)n2)cn1",
    "CCOC(=O)Cc1ccc(Nc2ncc(F)c(-c3c[nH]c4c(NC(=O)[C@@H](COC)N5CCN(C)CC5)cccc34)n2)cn1",
    "COC[C@H](C(=O)Nc1cccc2c(-c3nc(Nc4ccc5scnc5c4)ncc3F)c[nH]c12)N1CCN(C)CC1",
]


def test_a_series_whose_mcs_search_times_out_is_still_aligned_on_its_core():
    # A timed-out search still carries the largest core it reached; dropping it left a congeneric series
    # drawn in whatever orientation each molecule happened to get, with no core highlighted.
    lay = depict.layout(JAK_SERIES)
    assert all(len(core) >= 30 for core in lay.cores)  # every molecule matched, not just the reference
    assert lay.lo is not None  # one shared frame, so they are drawn at the same scale

    def core_start(k):
        return lay.mols[k].GetConformer().GetAtomPosition(lay.cores[k][0])

    first = core_start(0)
    assert all(abs(core_start(k).x - first.x) < 0.1 and abs(core_start(k).y - first.y) < 0.1
               for k in range(len(JAK_SERIES)))


def test_molecules_with_no_shared_core_are_not_aligned():
    lay = depict.layout(["c1ccccc1O", "C1CCCCC1C(=O)NCCN", "CCOCC"])
    assert lay.cores == [(), (), ()] and lay.lo is None


IMATINIB_SERIES = [
    "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1",
    "Cc1ccc(NC(=O)c2ccc(CN3CCN(CC)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1",
    "Cc1ccc(NC(=O)c2ccc(CN3CCOCC3)cc2)cc1Nc1nccc(-c2cccnc2)n1",
    "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2ccccc2)n1",
]
CAFFEINE = "Cn1cnc2c1c(=O)n(C)c(=O)n2C"


def test_a_core_needs_min_core_atoms_and_matching_bonds():
    # A benzene and a cyclohexane ring are not one core: bonds must match, aromatic only aromatic. Each
    # ring with its ethyl group shares 8 atoms with the other only when single and aromatic bonds match.
    lay = depict.layout(["c1ccccc1CCO", "C1CCCCC1CCO"])
    assert lay.cores == [(), ()] and lay.core is None and lay.core_atoms < depict.MIN_CORE_ATOMS
    # Two phenethylamides share 12 atoms (all of the first): enough for the default minimum of 8, not for 13.
    pair = ["c1ccccc1CCNC(=O)C", "c1ccccc1CCNC(=O)CCO"]
    lay = depict.layout(pair)
    assert lay.core_atoms == 12 and all(len(c) == 12 for c in lay.cores) and lay.core
    assert depict.layout(pair, min_core_atoms=13).cores == [(), ()]
    assert depict.core_size("[NX3;H2]") == 1 and depict.core_size("Nc1ccc(Cl)cc1") == 8
    assert depict.core_size("[H]Nc1ccccc1") == 7 and depict.core_size("not a core (") == 0


def test_an_outlier_does_not_cost_a_series_its_core():
    # In all five molecules the largest common part is tiny; four of the five (0.8, rounded up) share 26
    # atoms. The series is aligned on those, and caffeine is drawn unaligned in a frame of the same size.
    lay = depict.layout([*IMATINIB_SERIES, CAFFEINE])
    assert [len(c) for c in lay.cores] == [26, 26, 26, 26, 0] and lay.core_atoms == 26
    assert lay.lo is not None and list(lay.own) == [4]
    assert len({lay.size(k) for k in range(5)}) == 1  # one frame size, so one scale at any fixed width
    lo, hi = lay.own[4]
    xs = lay.mols[4].GetConformer().GetPositions()[:, 0]
    assert lo.x < xs.min() and xs.max() < hi.x and abs((lo.x + hi.x) / 2 - (xs.min() + xs.max()) / 2) < 1e-6
    # Required in all of them (min_core_share=1), there is no core; and with four molecules, 0.8 rounds up
    # to all four, so one outlier among four is not tolerated.
    assert depict.layout([*IMATINIB_SERIES, CAFFEINE], min_core_share=1).core is None
    assert depict.layout([*IMATINIB_SERIES[:3], CAFFEINE]).core is None
    # A core shared by all is preferred when it is big enough, even if most share a bigger one.
    lay = depict.layout(IMATINIB_SERIES)
    assert all(len(c) == 26 for c in lay.cores) and not lay.own


def test_grid_alignment_says_which_core_and_who_lacks_it():
    compounds = [figures.GridCompound(smiles=s, title=t) for s, t in
                 zip([*IMATINIB_SERIES, CAFFEINE], ["A", "B", "C", "D", "Caffeine"])]
    lay = depict.layout([c.smiles for c in compounds])
    text = figures.grid_alignment(compounds, lay, None, 8)
    assert text.startswith("aligned on their largest common substructure (26 atoms: ")
    assert text.endswith("; Caffeine lacks it and is drawn unaligned, without a highlight.")
    lay = depict.layout([c.smiles for c in compounds], min_core_share=1)
    assert figures.grid_alignment(compounds, lay, None, 8).startswith(
        "not aligned: their largest common substructure has ")
    lay = depict.layout([c.smiles for c in compounds], "Nc1ccc(Cl)cc1")
    assert figures.grid_alignment(compounds, lay, "Nc1ccc(Cl)cc1", 8) == \
        "not aligned: no compound contains Nc1ccc(Cl)cc1."
