"""SAR tools: the algorithms (need RDKit) and the tools over them (also need the DuckDB build)."""

import pytest

from mcp_bindingdb import sar

if not sar.available():
    pytest.skip("RDKit not installed (substructure extra)", allow_module_level=True)

from mcp import Client  # noqa: E402

from mcp_bindingdb import substructure  # noqa: E402
from mcp_bindingdb.db import Database, find_database  # noqa: E402
from mcp_bindingdb.server import build_server  # noqa: E402

QUINAZOLINE = "c1ncnc2ccccc12"
ANILINOQUINAZOLINE = "[*:2]Nc1ncnc2cc([*:1])c([*:3])cc12"  # gefitinib's core, positions marked
SERIES = [  # 4-anilinoquinazolines differing at one position, plus a molecule off the series
    "COc1cc2ncnc(Nc3ccccc3)c2cc1",
    "CCOc1cc2ncnc(Nc3ccccc3)c2cc1",
    "Clc1cc2ncnc(Nc3ccccc3)c2cc1",
    "CCO",
]


def molecules(smiles=None):
    return sar.molecules(smiles if smiles is not None else SERIES)


def test_decompose_labels_and_misses():
    core, _ = substructure.parse_query(QUINAZOLINE)
    out = sar.decompose(core, molecules())
    assert out.n_matched == 3 and out.rows[-1] is None  # ethanol has no quinazoline
    assert out.labels and all(label.startswith("R") for label in out.labels)
    assert out.core and "[*:" in out.core
    assert set(out.rows[0]) == set(out.labels)


def test_decompose_marks_hydrogen_and_drops_empty_columns():
    core, query_type = substructure.parse_query(ANILINOQUINAZOLINE)
    assert query_type == "smarts"  # '*' in the query
    out = sar.decompose(core, molecules([*SERIES[:3], "c1ccc2ncnc(Nc3ccccc3)c2c1"]))
    assert len(out.labels) == 2  # the third marked position is hydrogen throughout, so RDKit drops it
    assert "c1ccc([*:2])cc1" in out.rows[0].values()  # the anilino substituent
    assert "H" in out.rows[-1].values()  # the analogue without a ring substituent, not '[H][*:1]'
    assert all(value is not None for row in out.rows if row for value in row.values())


def test_decompose_core_that_matches_nothing():
    core, _ = substructure.parse_query("C1CC1S(=O)(=O)N")
    out = sar.decompose(core, molecules())
    assert out.labels == [] and out.core is None and out.rows == [None] * len(SERIES)


def test_substituent_and_fragment_tidying():
    assert sar.substituent("[H][*:1]") == "H" and sar.substituent("") is None
    assert sar.substituent("CO[*:1]") == "CO[*:1]"
    assert sar.tidy_fragment("[H]C([H])([H])O[*:1]") == "CO[*:1]"
    assert sar.tidy_fragment("[H][*:1]") == "[H][*:1]"  # a hydrogen substituent keeps its spelling
    assert sar.heavy_atoms("[H][*:1]") == 0 and sar.heavy_atoms("F[*:1]") == 1


def test_single_cut_variants_keeps_the_smaller_half():
    mol = molecules(["Cc1ccc(C(=O)N)cc1"])[0]
    variants = sar.single_cut_variants(mol)
    assert ("NC(=O)c1ccc([*:1])cc1", "C[*:1]") in variants
    assert all(sar.heavy_atoms(variable) <= sar.heavy_atoms(constant) for constant, variable in variants)
    assert not sar.single_cut_variants(mol, max_variable_atoms=0)


def test_single_cut_variants_with_hydrogens():
    mol = molecules(["Fc1ccccc1"])[0]
    assert not any(variable == "[H][*:1]" for _, variable in sar.single_cut_variants(mol))
    with_h = sar.single_cut_variants(mol, include_hydrogens=True)
    assert any(variable == "[H][*:1]" for _, variable in with_h)


def test_matched_pairs_finds_one_change_only():
    mols = molecules()
    pairs, hit_cap = sar.matched_pairs([sar.single_cut_variants(m) if m else [] for m in mols])
    assert not hit_cap
    assert set(pairs) == {(0, 1), (0, 2), (1, 2)}  # the three analogues, pairwise; not ethanol
    constant, from_group, to_group = pairs[(0, 1)]
    # The largest shared context wins, so the methoxy/ethoxy pair is a change at the oxygen, not of it.
    assert {from_group, to_group} == {"C[*:1]", "CC[*:1]"} and "O[*:1]" in constant


def test_matched_pairs_needs_a_shared_context():
    mols = molecules(["c1ccccc1F", "CCCCCCO"])
    pairs, _ = sar.matched_pairs([sar.single_cut_variants(m) for m in mols])
    assert pairs == {}


def test_similar_pairs_and_sali():
    fingerprints = [substructure.morgan_fingerprint(m) for m in molecules() if m is not None]
    pairs, hit_cap = sar.similar_pairs(fingerprints, 0.3)
    assert not hit_cap and pairs
    assert all(i < j and 0.3 <= similarity <= 1 for i, j, similarity in pairs)
    assert sar.similar_pairs(fingerprints, 1.01)[0] == []
    assert sar.similar_pairs(fingerprints[:1], 0.1)[0] == []
    assert sar.sali(2.0, 0.9) == 20.0 and sar.sali(1.0, 1.0) is None


def test_fold_change_and_same_molecule():
    assert sar.fold_change(0) == 1.0 and sar.fold_change(3) == 1000
    assert sar.fold_change(0.5) == 3.2 and sar.fold_change(-2.7) == 0.002
    a, b, c = molecules(["c1ccccc1O", "Oc1ccccc1", "c1ccccc1N"])
    assert sar.same_molecule(a, b) and not sar.same_molecule(a, c)


# --- the tools, against the real build ---

try:
    DB = Database(find_database())
except FileNotFoundError:
    DB = None
needs_db = pytest.mark.skipif(DB is None, reason="BindingDB DuckDB file not built")
EGFR = 520
pytestmark = [pytest.mark.anyio, needs_db]


@pytest.fixture(scope="module")
def server():
    return build_server(DB)


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def call(server, tool, **args):
    async with Client(server) as client:
        return await client.call_tool(tool, args)


async def ok(server, tool, **args):
    result = await call(server, tool, **args)
    assert not result.is_error, result.content
    return result.structured_content


async def test_decompose_r_groups_table(server):
    out = await ok(server, "decompose_r_groups", core=ANILINOQUINAZOLINE, target_id=EGFR,
                   max_value_nm=100, max_compounds=400, limit=10)
    assert out["affinity_type"] == "IC50"  # EGFR's most measured exact type
    assert out["r_groups"] == ["R1", "R2", "R3"]
    assert 0 < out["n_compounds_matched"] <= out["n_compounds_scanned"] <= 400
    rows = out["rows"]
    assert len(rows) == out["row_count"] <= 10
    for row in rows:  # one column per R-group position, and the structure for a figure
        assert set(out["r_groups"]) <= set(row) and row["smiles"] and row["p_affinity"]
    assert [row["p_affinity"] for row in rows] == sorted((r["p_affinity"] for r in rows), reverse=True)
    summary = out["r_group_summary"]
    assert set(summary) == {"R1", "R2", "R3"}
    counts = [group["n_compounds"] for group in summary["R2"]]
    assert counts == sorted(counts, reverse=True) and sum(counts) <= out["n_compounds_matched"]


async def test_decompose_r_groups_core_without_marks_and_errors(server):
    out = await ok(server, "decompose_r_groups", core=QUINAZOLINE, target_id=EGFR, max_compounds=200,
                   summarize=False, limit=5)
    assert len(out["r_groups"]) > 3 and "note" in out  # a loose core: a column per open position
    assert "r_group_summary" not in out
    missing = await ok(server, "decompose_r_groups", core="C1CC1S(=O)(=O)NC1CC1", target_id=EGFR,
                       max_compounds=200)
    assert missing["n_compounds_matched"] == 0 and "matches none" in missing["note"]
    bad = await call(server, "decompose_r_groups", core="not a structure", target_id=EGFR)
    assert bad.is_error
    both = await call(server, "decompose_r_groups", core=QUINAZOLINE, target_id=EGFR, uniprot="P00533")
    assert both.is_error and "exactly one" in both.content[0].text


async def test_matched_molecular_pairs(server):
    out = await ok(server, "matched_molecular_pairs", target_id=EGFR, max_compounds=300,
                   include_hydrogen_changes=False, min_delta_p=1.0, limit=20)
    assert out["affinity_type"] == "IC50" and out["n_compounds"] <= 300
    rows = out["rows"]
    assert rows and len(rows) == out["row_count"]
    for row in rows:
        assert abs(row["delta_p_affinity"]) >= 1.0
        assert row["delta_p_affinity"] == round(row["p_affinity_to"] - row["p_affinity_from"], 2)
        assert " >> " in row["transformation"] and row["monomerid_from"] != row["monomerid_to"]
        assert "[H]" not in row["constant_part"]  # tidied for reading
    deltas = [abs(row["delta_p_affinity"]) for row in rows]
    assert deltas == sorted(deltas, reverse=True)


async def test_matched_molecular_pairs_one_transformation(server):
    adds_fluorine = "[H][*:1] >> F[*:1]"
    out = await ok(server, "matched_molecular_pairs", target_id=EGFR, max_compounds=600,
                   transformation=adds_fluorine, limit=10)
    assert out["rows"], "no H -> F pair found among EGFR's most potent compounds"
    assert {row["transformation"] for row in out["rows"]} == {adds_fluorine}
    bad = await call(server, "matched_molecular_pairs", target_id=EGFR, transformation="F[*:1]")
    assert bad.is_error and ">>" in bad.content[0].text


async def test_matched_molecular_pairs_grouped(server):
    out = await ok(server, "matched_molecular_pairs", target_id=EGFR, max_compounds=400,
                   group_by_transformation=True, limit=15)
    assert out["grouped_by"] == "transformation" and out["n_transformations"] >= len(out["rows"])
    counts = [row["n_pairs"] for row in out["rows"]]
    assert counts == sorted(counts, reverse=True)
    for row in out["rows"]:
        assert row["min_delta_p_affinity"] <= row["median_delta_p_affinity"] <= row["max_delta_p_affinity"]
        assert 0 <= row["n_improved"] <= row["n_pairs"]


async def test_activity_cliffs(server):
    out = await ok(server, "activity_cliffs", target_id=EGFR, max_compounds=600, min_similarity=0.8,
                   min_delta_p=1.5, limit=20)
    rows = out["rows"]
    assert rows and out["affinity_type"] == "IC50"
    for row in rows:
        assert row["similarity"] >= 0.8 and row["delta_p_affinity"] >= 1.5
        assert row["p_affinity_potent"] > row["p_affinity_weak"]
        assert row["sali"] is None or row["sali"] == pytest.approx(
            row["delta_p_affinity"] / (1 - row["similarity"]), abs=0.01)
        assert row["same_structure"] is False or row["similarity"] == 1.0
    identical = [row for row in rows if row["sali"] is None]
    assert rows[:len(identical)] == identical  # undefined SALI means the strongest cliff: listed first


async def test_sar_tools_honour_an_explicit_affinity_type(server):
    out = await ok(server, "activity_cliffs", target_id=EGFR, affinity_type="Ki", max_compounds=200,
                   min_similarity=0.7, min_delta_p=1.0, limit=5)
    assert out["affinity_type"] == "Ki"
    empty = await call(server, "matched_molecular_pairs", target_id=EGFR, affinity_type="EC50",
                       max_value_nm=0.0001)
    assert empty.is_error and "exact EC50" in empty.content[0].text
