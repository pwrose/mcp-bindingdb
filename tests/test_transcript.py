"""Markdown of transcripts and notebooks: SMILES and other values show as written, not as Markdown."""

import pytest
from markdown_it import MarkdownIt

from mcp_bindingdb import depict, notebook, transcript, transcript_html

# A SMILES that Markdown reads as a link ([C@@H](c1ccccc1)), and attachment points it reads as emphasis.
LINKED = "O=C(N[C@@H](c1ccccc1)C1CC1)c1cc(=O)[nH]cn1"
STARRED = "[*:1]c1ccc([*:2])cc1"


def _html(markdown: str) -> str:
    return MarkdownIt("commonmark").enable("table").render(markdown)


def test_table_cells_show_smiles_as_written():
    rows = [{"smiles": LINKED, "note": "a|b"}, {"smiles": STARRED, "note": "x_y_z <10 nM> $5"}]
    html = _html("\n".join(transcript._rows_to_table(rows)))
    assert "<a " not in html and "<em>" not in html
    assert f"<td>{LINKED}</td>" in html
    assert f"<td>{STARRED}</td>" in html
    assert "<td>a|b</td>" in html  # still one cell
    assert "<td>x_y_z &lt;10 nM&gt; $5</td>" in html


@pytest.mark.skipif(not depict.available(), reason="needs RDKit")
def test_html_transcript_draws_an_escaped_smiles():
    markdown = "\n".join(["# T", "", *transcript._rows_to_table([{"name": "a", "smiles": LINKED}])])
    page, drawn, _ = transcript_html.markdown_to_html(markdown)
    assert drawn == 1
    assert f'alt="{LINKED}"' in page
    assert 'href="c1ccccc1"' not in page


@pytest.mark.parametrize("text", [
    f"The best is {LINKED}, at 3 nM.",
    f"| compound | smiles |\n| --- | --- |\n| A | {LINKED} |",
])
def test_a_smiles_in_an_answer_is_not_a_link(text):
    html = _html(transcript.escape_false_links(text))
    assert "<a " not in html
    assert LINKED in html


@pytest.mark.parametrize("link", [
    "[Example 3.5](../03-compound-target/3.5-protein-complexes/3.5-protein-complexes.html)",
    "[PubMed](https://pubmed.ncbi.nlm.nih.gov/36201859/)",
    "[the table](#potency)",
    "[Figure 1](figures/grid.png)",
    "[notebook](3.6-notebook/README.md)",
])
def test_real_links_stay_links(link):
    assert transcript.escape_false_links(f"See {link}.") == f"See {link}."


def test_code_is_left_alone():
    text = f"Query `{LINKED}` or\n\n```\n{LINKED}\n```\nthen {LINKED}"
    out = transcript.escape_false_links(text).split("\n")
    assert out[0] == f"Query `{LINKED}` or"
    assert out[3] == LINKED  # fenced
    assert out[5] == "then " + LINKED.replace("[C@@H](", "\\[C@@H](")


def test_overlay_viewer_is_not_a_bare_iframe():
    assert notebook.overlay_viewer("<p>x</p>").startswith("<div><iframe ")
