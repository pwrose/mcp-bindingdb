"""Superposed binding sites (structures.py) on a bundled PDB entry, without network access."""

import gzip
import math
from pathlib import Path

import pytest

from mcp_bindingdb import figures, structures

gemmi = pytest.importorskip("gemmi")
FIXTURE = Path(__file__).parent / "data" / "2i4u.cif.gz"  # HIV-1 protease dimer with TMC-126 (DJR)
HIV_PROTEASE = "PQITLWQRPLVTIKIGGQLKEALLDTGADDTVLEEMNLPGRWKPKMIGGIGGFIKVRQYDQILIEICGHKAIGTVLVGPTPVNIIGRNLLTQIGCTLNF"


def moved_copy(directory: Path, pdb_id: str) -> None:
    """2I4U rotated and shifted, saved in the cache as `pdb_id` (an mmCIF without SIFTS columns)."""
    st = gemmi.read_structure(str(FIXTURE))
    turn = gemmi.Transform()
    c, s = math.cos(1.0), math.sin(1.0)
    turn.mat.fromlist([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    turn.vec.fromlist([30.0, -12.0, 7.0])
    st[0].transform_pos_and_adp(turn)
    st.setup_entities()
    doc = st.make_mmcif_document()
    doc[0].name = pdb_id
    (directory / f"{pdb_id.lower()}.cif.gz").write_bytes(gzip.compress(doc.as_string().encode()))


@pytest.fixture
def cache(tmp_path):
    (tmp_path / "2i4u.cif.gz").write_bytes(FIXTURE.read_bytes())
    moved_copy(tmp_path, "9ZZZ")
    return structures.PdbCache(tmp_path, network=False)


def test_finds_ligand_and_both_chains(cache):
    site = structures.load_site(cache.path("2I4U"), structures.Request("2I4U", "DJR"), {"P03366"})
    assert site.ligand.name == "DJR" and sorted(c.name for c in site.chains) == ["A", "B"]
    assert site.mapped and site.resolution == pytest.approx(1.5)
    assert structures.sequence_identity(site.primary, HIV_PROTEASE) > 90


def test_superposition_undoes_a_rigid_move(cache):
    overlay = structures.build_overlay(
        [structures.Request("2I4U", "DJR", {"name": "TMC-126"}), structures.Request("9ZZZ", "djr")],
        cache, {"P03366"}, sequences=[HIV_PROTEASE])
    assert overlay.reference == "2I4U" and not overlay.skipped
    moved = overlay.entries[1]
    assert moved["pocket_rmsd"] < 0.01 and moved["global_rmsd"] < 0.01 and moved["moved"] == []
    ligands = [s.ligand for s in overlay.sites]
    assert max(a.pos.dist(b.pos) for a, b in zip(*ligands)) < 0.01  # the copy's ligand is back in place
    # The same residues and hydrogen bonds are found in both, named after the reference.
    assert overlay.entries[0]["contacts"] == moved["contacts"]
    assert overlay.entries[0]["hbond_partners"] == moved["hbond_partners"]
    assert {"D25:A", "D225:B"} <= set(moved["hbond_partners"])  # the catalytic aspartates (chain B is 201-299)
    assert all(2.5 <= h["distance"] <= 3.5 for h in moved["hbonds"])
    assert moved["protein_pdb"].startswith("ATOM") and "HETATM" in moved["ligand_pdb"]
    # Bond orders from the file's component dictionary, as CONECT records repeated per order.
    ref_pdb = overlay.entries[0]["ligand_pdb"]
    serial = {line[12:16].strip(): line[6:11] for line in ref_pdb.splitlines() if line.startswith("HETATM")}
    assert ref_pdb.count(f"CONECT{serial['C4']}{serial['O5']}") == 2  # C4=O5, a carbonyl
    assert ref_pdb.count(f"CONECT{serial['C4']}{serial['N1']}") == 1  # C4-N1


def test_skips_entries_it_cannot_use(cache):
    overlay = structures.build_overlay(
        [structures.Request("2I4U", "DJR"), structures.Request("2I4U", "478"), structures.Request("1ABC", "XYZ")],
        cache, set(), sequences=[HIV_PROTEASE])
    reasons = " | ".join(s["reason"] for s in overlay.skipped)
    assert "478 is not in the entry (its ligands: DJR)" in reasons
    assert "1ABC is not in the structure cache and network lookups are disabled" in reasons
    with pytest.raises(structures.StructureError, match="bound to another protein"):
        structures.build_overlay([structures.Request("2I4U", "DJR")], cache, set(), sequences=["MKTAYIAKQR" * 30])


def test_writes_files_and_contact_map(cache, tmp_path):
    overlay = structures.build_overlay([structures.Request("2I4U", "DJR"), structures.Request("9ZZZ", "DJR")],
                                       cache, set())
    files = overlay.write(tmp_path / "out", "HIV-1 protease")
    assert (tmp_path / "out" / "2I4U_DJR.cif").is_file() and files["9ZZZ_DJR"].is_file()
    assert not list((tmp_path / "out").glob("*.pml"))  # no PyMOL script
    rows = [figures.ContactRow(e["pdb_id"], e["colour"], set(e["contacts"]), set(e["hbond_partners"]))
            for e in overlay.entries]
    block, png = figures.contact_map("HIV-1 protease", "", rows, overlay.residues)
    assert 'class="h"' in block and "D25:A" in block
    assert png is None or png.startswith(b"\x89PNG")


def test_rejects_bad_pdb_ids():
    with pytest.raises(structures.StructureError):
        structures.normalize_pdb_id("../etc")
