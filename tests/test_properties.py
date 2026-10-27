"""Compound properties, scaffolds and structural alerts (needs RDKit)."""

import pytest

from mcp_bindingdb import properties

if properties.Chem is None:
    pytest.skip("RDKit not installed (substructure extra)", allow_module_level=True)

IMATINIB = "Cc1ccc(NC(=O)c2ccc(CN3CCN(C)CC3)cc2)cc1Nc1nccc(-c2cccnc2)n1"


def values(smiles):
    return dict(zip([name for name, _ in properties.COLUMNS[1:]], properties.compute(smiles)))


def test_aspirin():
    v = values("CC(=O)Oc1ccccc1C(=O)O")
    assert (v["heavy_atoms"], v["mw"], v["clogp"], v["hbd"], v["hba"]) == (13, 180.16, 1.31, 1, 4)
    assert v["ro5_violations"] == 0
    assert v["scaffold"] == "c1ccccc1" and v["generic_scaffold"] == "C1CCCCC1"
    assert v["pains"] == [] and v["brenk"] == ["phenol_ester"]


def test_alerts_and_acyclic():
    assert values("Oc1ccccc1O")["pains"] == ["catechol_A(92)"]
    v = values("CCCC")
    assert v["scaffold"] is None and v["generic_scaffold"] is None


def test_computed_for_the_parent():
    assert properties.compute("CS(=O)(=O)c1ccc(cc1)C1CCCC1.Cl") == properties.compute("CS(=O)(=O)c1ccc(cc1)C1CCCC1")
    assert properties.compute("not smiles") is None


def test_scaffold_of_a_scaffold_is_itself():
    scaffold = properties.murcko_scaffold(IMATINIB)
    assert scaffold == values(IMATINIB)["scaffold"] and properties.murcko_scaffold(scaffold) == scaffold
    assert properties.murcko_scaffold("CCO") is None and properties.murcko_scaffold("xx") is None
