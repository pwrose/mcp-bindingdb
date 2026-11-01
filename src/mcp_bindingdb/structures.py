"""Superposed PDB complexes of one target's ligands (overlay_binding_site).

Each requested entry is read from a PDBe "updated" mmCIF file (its atoms carry SIFTS UniProt numbers), or
the RCSB file when PDBe lacks it, cached under data/pdb-cache/. In each entry:

1. The ligand is the instance of its PDB ligand code with the most protein atoms within 4.5 Å; when some
   chains map (SIFTS) to the target's UniProt accessions, contacts with those count first.
2. Its binding-site chains are the protein chains touching it (within 4.5 Å), leaving out a chain with only
   a few atoms there (under a tenth of the most touching chain's), such as a crystal-packing neighbour.
3. Residues are paired with the reference entry's binding-site chains by sequence alignment, so mutants,
   other strains and records whose UniProt accession differs from the PDB's (BindingDB lists HIV-1 protease
   as P04585, SIFTS maps the PDB chains to P03366) still pair up. For a homo-oligomer every assignment of
   chains to reference chains is tried and the best fitting one kept.
4. A first fit on the paired Cα atoms places the ligand; the pocket is then the reference residues within
   `cutoff` Å of the reference ligand or of this one, and the final fit uses only their Cα atoms. That
   aligns the binding site itself, which a whole-chain fit can shift when a domain or loop moves. Both fits
   reject outliers as PyMOL's `align` does (refit without pairs more than twice the RMSD apart, up to five
   times), so a loop that moved 30 Å (CDK2's activation loop) does not drag the rest. The pocket RMSD is
   over the pairs the fit kept, and the pocket residues more than MOVED Å from their reference position are
   listed, so a changed site still shows.

Hydrogen bonds are polar contacts: ligand N/O to protein N/O 2.5-3.5 Å apart (proline's backbone N, which
has no hydrogen, excluded). No angles are checked, because the files have no hydrogens to check them with.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import re
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import gemmi
except ImportError:  # optional extra "structures"
    gemmi = None

PDBE_URL = "https://www.ebi.ac.uk/pdbe/entry-files/download/{id}_updated.cif.gz"
RCSB_URL = "https://files.rcsb.org/download/{ID}.cif.gz"
RCSB_GRAPHQL = "https://data.rcsb.org/graphql"
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
LIGAND_CACHE_DAYS = 30  # PDB ligands of a UniProt accession are fetched again after this many days
PDB_ID = re.compile(r"[0-9][0-9A-Za-z]{3}")
LIGAND_CONTACT = 4.5  # Å, protein atoms counted when choosing the ligand instance
MINOR_CHAIN = 0.1  # a touching chain with under this fraction of the top chain's contact atoms is left out
CONTACT = 4.0  # Å, residues listed as contacts
HBOND = (2.5, 3.5)  # Å, polar contact range
MOVED = 2.0  # Å, a pocket residue (Cα) this far from its reference position after the fit has moved
MIN_POCKET = 6  # Cα pairs needed for a pocket fit; fewer and the global fit stands
MAX_CHAIN_ASSIGNMENTS = 4  # chains per side for trying every assignment
#: Entry colours in the viewer and contact map, colour-blind safe first (Okabe-Ito), then more.
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00", "#F0E442", "#000000",
           "#8C564B", "#7F7F7F", "#BCBD22", "#17BECF", "#9467BD", "#AEC7E8", "#FF9896", "#98DF8A"]


class StructureError(Exception):
    """A structure could not be fetched or used; the message says why."""


def available() -> bool:
    return gemmi is not None


def normalize_pdb_id(pdb_id: str) -> str:
    pdb_id = pdb_id.strip().upper()
    if not PDB_ID.fullmatch(pdb_id):
        raise StructureError(f"{pdb_id!r} is not a PDB id (four characters, starting with a digit)")
    return pdb_id


class PdbCache:
    """mmCIF files by PDB id, downloaded once into `directory`."""

    def __init__(self, directory: Path, network: bool = True, timeout: float = 30.0) -> None:
        self.directory = directory
        self.network = network
        self.timeout = timeout

    def path(self, pdb_id: str) -> Path:
        pdb_id = normalize_pdb_id(pdb_id)
        file = self.directory / f"{pdb_id.lower()}.cif.gz"
        if file.is_file():
            return file
        if not self.network:
            raise StructureError(f"{pdb_id} is not in the structure cache and network lookups are disabled")
        errors = []
        for url in (PDBE_URL.format(id=pdb_id.lower()), RCSB_URL.format(ID=pdb_id)):
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as response:
                    data = response.read()
                if data[:2] != b"\x1f\x8b":
                    raise ValueError("not a gzip file")
                self.directory.mkdir(parents=True, exist_ok=True)
                partial = file.with_suffix(f".{os.getpid()}.tmp")
                partial.write_bytes(data)
                partial.replace(file)
                return file
            except Exception as e:  # noqa: BLE001 - any failure falls through to the next source
                errors.append(f"{url.split('/')[2]}: {e}")
        raise StructureError(f"Could not download {pdb_id} ({'; '.join(errors)})")


def resolutions(pdb_ids: list[str], timeout: float = 20.0) -> dict[str, float | None]:
    """Resolution (Å) of each entry from the RCSB Data API, None for entries without one (e.g. NMR). One
    request for all; {} when it fails, so callers fall back to their own order."""
    if not pdb_ids:
        return {}
    query = {"query": "query($ids:[String!]!){entries(entry_ids:$ids){rcsb_id rcsb_entry_info{resolution_combined}}}",
             "variables": {"ids": [normalize_pdb_id(p) for p in pdb_ids]}}
    request = urllib.request.Request(RCSB_GRAPHQL, data=json.dumps(query).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            entries = json.load(response)["data"]["entries"] or []
    except Exception:  # noqa: BLE001
        return {}
    out = {}
    for e in entries:
        values = (e.get("rcsb_entry_info") or {}).get("resolution_combined") or []
        out[e["rcsb_id"].upper()] = min(values) if values else None
    return out



def ligand_inchikeys(codes: list[str], timeout: float = 20.0) -> dict[str, str]:
    """InChIKey of each PDB ligand code (chemical component) from the RCSB Data API, for ligands BindingDB
    does not link to an entry. One request for all; {} when it fails."""
    codes = sorted({c.strip().upper() for c in codes if re.fullmatch(r"[0-9A-Za-z]{1,5}", c.strip())})
    if not codes:
        return {}
    query = {"query": "query($ids:[String!]!){chem_comps(comp_ids:$ids){chem_comp{id} "
                      "rcsb_chem_comp_descriptor{InChIKey}}}", "variables": {"ids": codes}}
    request = urllib.request.Request(RCSB_GRAPHQL, data=json.dumps(query).encode(),
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            comps = json.load(response)["data"]["chem_comps"] or []
    except Exception:  # noqa: BLE001
        return {}
    return {c["chem_comp"]["id"].upper(): key for c in comps if c
            and (key := (c.get("rcsb_chem_comp_descriptor") or {}).get("InChIKey"))}


def _post_json(url: str, body: dict[str, Any], timeout: float) -> Any:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response) if response.status != 204 else {}


def entry_ligands(pdb_ids: list[str], timeout: float = 30.0) -> list[dict[str, str]]:
    """The small-molecule ligands of PDB entries with their InChIKeys, from the RCSB Data API:
    [{pdb_id, het, inchi_key}]. Raises StructureError when the API cannot be reached."""
    out = []
    ids = sorted({normalize_pdb_id(p) for p in pdb_ids})
    query = ("query($ids:[String!]!){entries(entry_ids:$ids){rcsb_id nonpolymer_entities{nonpolymer_comp{"
             "chem_comp{id} rcsb_chem_comp_descriptor{InChIKey}}}}}")
    for start in range(0, len(ids), 200):
        try:
            entries = _post_json(RCSB_GRAPHQL, {"query": query, "variables": {"ids": ids[start:start + 200]}},
                                 timeout)["data"]["entries"] or []
        except Exception as e:  # noqa: BLE001
            raise StructureError(f"RCSB Data API: {e}") from None
        for entry in entries:
            for entity in entry.get("nonpolymer_entities") or []:
                comp = entity.get("nonpolymer_comp") or {}
                key = (comp.get("rcsb_chem_comp_descriptor") or {}).get("InChIKey")
                if key:
                    out.append({"pdb_id": entry["rcsb_id"].upper(), "het": comp["chem_comp"]["id"].upper(),
                                "inchi_key": key})
    return out


def accession_ligands(accessions: set[str], cache_dir: Path, network: bool = True,
                      timeout: float = 30.0) -> list[dict[str, str]]:
    """The ligands (with InChIKeys) of every PDB entry with a chain of these UniProt accessions, from the RCSB
    Search and Data APIs, cached in `cache_dir` for LIGAND_CACHE_DAYS: [{pdb_id, het, inchi_key}]. For
    compounds BindingDB has no PDB link for (nilotinib in 3CS9). [] without network or when RCSB fails."""
    accs = sorted({a.strip().upper() for a in accessions if a and re.fullmatch(r"[A-Z0-9-]{4,12}", a.strip().upper())})
    if not accs:
        return []
    cache = cache_dir / f"rcsb-ligands-{'_'.join(accs)[:120]}.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text())
            fresh = (datetime.now(timezone.utc) - datetime.fromisoformat(data["fetched"])).days < LIGAND_CACHE_DAYS
            if fresh or not network:
                return data["ligands"]
        except (ValueError, KeyError, OSError):
            pass
    if not network:
        return []
    search = {"query": {"type": "terminal", "service": "text", "parameters": {
        "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
        "operator": "in", "value": accs}}, "return_type": "entry", "request_options": {"return_all_hits": True}}
    try:
        result = _post_json(RCSB_SEARCH, search, timeout)
        ligands = entry_ligands([r["identifier"] for r in result.get("result_set") or []], timeout)
    except Exception:  # noqa: BLE001 - BindingDB's own links still work
        return []
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        partial = cache.with_suffix(f".{os.getpid()}.tmp")
        partial.write_text(json.dumps({"fetched": datetime.now(timezone.utc).isoformat(), "accessions": accs,
                                       "ligands": ligands}))
        partial.replace(cache)
    except OSError:
        pass
    return ligands

# --- one entry -------------------------------------------------------------------------------------------

@dataclass
class Request:
    """An entry to overlay: the PDB id, the ligand code to find in it, and what to show about the ligand."""
    pdb_id: str
    het: str
    info: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProteinChain:
    subchain: str  # label_asym_id, unique in the entry
    name: str  # auth chain name, as shown
    residues: list[Any]  # gemmi.Residue with a CA atom, in chain order
    accessions: set[str]


@dataclass
class Site:
    request: Request
    structure: Any  # gemmi.Structure, first model only, no hydrogens, waters or alternative conformations
    ligand: Any  # gemmi.Residue
    ligand_chain: str
    chains: list[ProteinChain]  # binding-site chains
    resolution: float | None
    method: str
    title: str
    unp: dict[tuple[str, str], tuple[str, int]]  # (subchain, seqid) -> SIFTS (accession, number)
    mapped: bool  # some binding-site chain maps (SIFTS) to the target's UniProt accessions
    primary: ProteinChain  # the chain with the most atoms touching the ligand
    #: The ligand's bonds from the file's chemical component dictionary (atom names, order 1-3); empty if absent.
    bonds: list[tuple[str, str, int]] = field(default_factory=list)


def _is_amino_acid(residue: Any) -> bool:
    info = gemmi.find_tabulated_residue(residue.name)
    return info is not None and info.is_amino_acid()


def _one_letter(residue: Any) -> str:
    info = gemmi.find_tabulated_residue(residue.name)
    code = info.one_letter_code.upper() if info is not None else " "
    return code if code.strip() else "X"


def _seqid(residue: Any) -> str:
    return f"{residue.seqid.num}{residue.seqid.icode.strip()}"


def _sifts(block: Any) -> dict[tuple[str, str], tuple[str, int]]:
    """(label_asym_id, auth seq id + insertion code) -> (UniProt accession, number), from the per-atom SIFTS
    columns of a PDBe updated mmCIF; empty for other files."""
    table = block.find("_atom_site.", ["label_asym_id", "auth_seq_id", "?pdbx_PDB_ins_code",
                                       "?pdbx_sifts_xref_db_acc", "?pdbx_sifts_xref_db_num",
                                       "?pdbx_sifts_xref_db_name"])
    if not table.has_column(3) or not table.has_column(4):
        return {}
    out: dict[tuple[str, str], tuple[str, int]] = {}
    for row in table:
        if table.has_column(5) and row.str(5) != "UNP":
            continue
        acc, num = row.str(3), row.str(4)
        if not acc or not num.lstrip("-").isdigit():
            continue
        icode = row.str(2) if table.has_column(2) else ""
        out.setdefault((row.str(0), row.str(1) + icode), (acc.split("-")[0], int(num)))
    return out


def load_site(path: Path, request: Request, accessions: set[str]) -> Site:
    """Read an entry and find the ligand and its binding-site chains; StructureError if the ligand is not
    there or touches no protein."""
    try:
        block = gemmi.cif.read(str(path)).sole_block()
        st = gemmi.make_structure_from_block(block)
    except Exception as e:  # noqa: BLE001
        raise StructureError(f"{request.pdb_id}: could not read the file ({e})") from None
    while len(st) > 1:
        del st[1]
    st.setup_entities()
    st.remove_alternative_conformations()
    st.remove_hydrogens()
    st.remove_waters()
    unp = _sifts(block)
    model = st[0]
    het = request.het.upper()

    proteins: dict[str, ProteinChain] = {}
    for chain in model:
        residues = [r for r in chain if r.entity_type == gemmi.EntityType.Polymer and _is_amino_acid(r)
                    and r.find_atom("CA", "*") is not None]
        if residues:
            subchain = residues[0].subchain
            accs = {unp[(subchain, _seqid(r))][0] for r in residues if (subchain, _seqid(r)) in unp}
            proteins[subchain] = ProteinChain(subchain, chain.name, residues, accs)
    if not proteins:
        raise StructureError(f"{request.pdb_id}: no protein chain")
    mapped = {s for s, c in proteins.items() if c.accessions & accessions}

    ns = gemmi.NeighborSearch(model, st.cell, LIGAND_CONTACT + 1).populate()

    def near(residue: Any, radius: float) -> dict[str, set[tuple[str, str, str]]]:
        """Protein atoms within radius of residue, by subchain."""
        found: dict[str, set[tuple[str, str, str]]] = {}
        for atom in residue:
            for mark in ns.find_atoms(atom.pos, "\0", radius=radius):
                cra = mark.to_cra(model)
                if cra.residue.subchain in proteins:
                    found.setdefault(cra.residue.subchain, set()).add((_seqid(cra.residue), cra.residue.name,
                                                                        cra.atom.name))
        return found

    best, best_score, best_chain = None, None, ""
    for chain in model:
        for residue in chain:
            if residue.name != het or residue.entity_type == gemmi.EntityType.Polymer:
                continue
            contacts = near(residue, LIGAND_CONTACT)
            score = (sum(len(v) for s, v in contacts.items() if s in mapped), sum(len(v) for v in contacts.values()))
            if best_score is None or score > best_score:
                best, best_score, best_chain = residue, score, chain.name
    if best is None:
        if any(r.name == het for c in model for r in c):
            raise StructureError(f"{request.pdb_id}: ligand {het} is part of a polymer chain, not a separate ligand")
        others = sorted({r.name for c in model for r in c if r.entity_type == gemmi.EntityType.NonPolymer})
        raise StructureError(f"{request.pdb_id}: ligand {het} is not in the entry (its ligands: "
                             f"{', '.join(others) or 'none'})")
    if not best_score[1]:
        raise StructureError(f"{request.pdb_id}: ligand {het} touches no protein")
    touching = near(best, LIGAND_CONTACT)
    top = max(len(v) for v in touching.values())
    site_chains = {s for s, atoms in touching.items() if len(atoms) >= MINOR_CHAIN * top}
    use_mapped = bool(mapped & site_chains)
    chains = [c for s, c in proteins.items() if s in site_chains and (s in mapped or not use_mapped)]
    primary = max(chains, key=lambda c: len(touching.get(c.subchain, ())))
    resolution = st.resolution or None
    method = block.find_value("_exptl.method") or ""
    title = block.find_value("_struct.title") or ""
    return Site(request, st, best.clone(), best_chain, chains, resolution, gemmi.cif.as_string(method),
                gemmi.cif.as_string(title), unp, use_mapped, primary, _component_bonds(block, best.name))


BOND_ORDERS = {"SING": 1, "DOUB": 2, "TRIP": 3}  # aromatic rings are given in Kekulé form, as in the CCD


def _component_bonds(block: Any, comp_id: str) -> list[tuple[str, str, int]]:
    """Bonds of one component from the entry's _chem_comp_bond table (PDBe files have it, RCSB files not)."""
    table = block.find("_chem_comp_bond.", ["comp_id", "atom_id_1", "atom_id_2", "value_order"])
    return [(gemmi.cif.as_string(row[1]), gemmi.cif.as_string(row[2]),
             BOND_ORDERS.get(gemmi.cif.as_string(row[3]).upper(), 1))
            for row in table if gemmi.cif.as_string(row[0]) == comp_id]


# --- superposition ---------------------------------------------------------------------------------------

def _aligned_pairs(a: ProteinChain, b: ProteinChain) -> tuple[list[tuple[int, int]], float]:
    """Residue index pairs of two chains from a global sequence alignment, and the identity (%)."""
    sa, sb = [_one_letter(r) for r in a.residues], [_one_letter(r) for r in b.residues]
    result = gemmi.align_string_sequences(sa, sb, [], gemmi.AlignmentScoring("b"))
    ga, gb = result.add_gaps("".join(sa), 1), result.add_gaps("".join(sb), 2)
    pairs, i, j = [], 0, 0
    for ca, cb in zip(ga, gb):
        if ca != "-" and cb != "-":
            pairs.append((i, j))
        i += ca != "-"
        j += cb != "-"
    return pairs, result.calculate_identity()


def sequence_identity(chain: ProteinChain, sequence: str) -> float:
    """Identical residues (%) of the chain's modelled residues in a global alignment with a sequence."""
    sa = [_one_letter(r) for r in chain.residues]
    sb = [c for c in sequence.upper() if c.isalpha()]
    if not sa or not sb:
        return 0.0
    result = gemmi.align_string_sequences(sa, sb, [], gemmi.AlignmentScoring("b"))
    ga, gb = result.add_gaps("".join(sa), 1), result.add_gaps("".join(sb), 2)
    return 100.0 * sum(a == b and a != "-" for a, b in zip(ga, gb)) / len(sa)


def string_identity(a: str, b: str) -> float:
    """Identical residues (%) of two sequences in a global alignment, relative to the shorter one."""
    sa, sb = [c for c in a.upper() if c.isalpha()], [c for c in b.upper() if c.isalpha()]
    if not sa or not sb:
        return 0.0
    result = gemmi.align_string_sequences(sa, sb, [], gemmi.AlignmentScoring("b"))
    ga, gb = result.add_gaps("".join(sa), 1), result.add_gaps("".join(sb), 2)
    return 100.0 * sum(x == y and x != "-" for x, y in zip(ga, gb)) / min(len(sa), len(sb))


def _ca(residue: Any) -> Any:
    return residue.find_atom("CA", "*").pos


@dataclass
class Fit:
    transform: Any  # gemmi.Transform taking the entry onto the reference
    global_rmsd: float  # all paired Cα atoms, under the global fit
    n_global: int
    pocket_rmsd: float | None  # the pocket Cα pairs the fit kept (outliers rejected)
    n_pocket: int
    n_core: int  # pairs the final fit used, after outlier rejection
    identity: float
    # entry residue (subchain, index) -> reference residue (subchain, index)
    pairs: dict[tuple[str, int], tuple[str, int]]
    moved: list[tuple[tuple[str, int], float]] = field(default_factory=list)  # reference pocket residue, Å


def _superpose(ref_pos: list[Any], pos: list[Any], cycles: int = 5) -> tuple[Any, int]:
    """A least-squares fit of pos onto ref_pos that drops outlier pairs (more than twice the RMSD and 1 Å
    apart) and refits, keeping at least half the pairs: the fit and the number of pairs it used."""
    keep = list(range(len(pos)))
    result = gemmi.superpose_positions(ref_pos, pos)
    for _ in range(cycles):
        limit = max(2 * result.rmsd, 1.0)
        distances = [ref_pos[k].dist(gemmi.Position(result.transform.apply(pos[k]))) for k in keep]
        kept = [k for k, d in zip(keep, distances) if d <= limit]
        if len(kept) == len(keep) or len(kept) < max(3, len(pos) // 2):
            break
        keep = kept
        result = gemmi.superpose_positions([ref_pos[k] for k in keep], [pos[k] for k in keep])
    return result, len(keep)


def _distances(ref_pos: list[Any], pos: list[Any], transform: Any) -> list[float]:
    return [r.dist(gemmi.Position(transform.apply(p))) for r, p in zip(ref_pos, pos)]


def _rmsd(ref_pos: list[Any], pos: list[Any], transform: Any) -> float:
    return math.sqrt(sum(d * d for d in _distances(ref_pos, pos, transform)) / len(pos))


def _within(residues: list[tuple[str, int, Any]], ligand_positions: list[Any], radius: float) -> set[tuple[str, int]]:
    out = set()
    for subchain, index, residue in residues:
        if any(atom.pos.dist(p) <= radius for atom in residue for p in ligand_positions):
            out.add((subchain, index))
    return out


def fit(site: Site, ref: Site, cutoff: float) -> Fit:
    """Superpose site onto ref: the chain assignment with the best global fit, then a pocket refit."""
    if site is ref:
        pairs = {(c.subchain, i): (c.subchain, i) for c in ref.chains for i in range(len(c.residues))}
        return Fit(gemmi.Transform(), 0.0, len(pairs), 0.0, len(pairs), len(pairs), 100.0, pairs)
    alignments = {(e.subchain, r.subchain): _aligned_pairs(e, r) for e in site.chains for r in ref.chains}
    entry_chains, ref_chains = site.chains[:MAX_CHAIN_ASSIGNMENTS], ref.chains[:MAX_CHAIN_ASSIGNMENTS]
    k = min(len(entry_chains), len(ref_chains))
    candidates = []
    for chosen in itertools.permutations(entry_chains, k):
        for target in itertools.permutations(ref_chains, k):
            pairs = {}
            identities = []
            for e, r in zip(chosen, target):
                index_pairs, identity = alignments[(e.subchain, r.subchain)]
                identities.append(identity)
                pairs.update({(e.subchain, i): (r.subchain, j) for i, j in index_pairs})
            if len(pairs) >= 3:
                candidates.append((pairs, sum(identities) / len(identities)))
    if not candidates:
        raise StructureError(f"{site.request.pdb_id}: its chains do not align with {ref.request.pdb_id}")
    entry_res = {c.subchain: c.residues for c in site.chains}
    ref_res = {c.subchain: c.residues for c in ref.chains}

    def positions(pairs: dict[tuple[str, int], tuple[str, int]]) -> tuple[list[Any], list[Any]]:
        keys = list(pairs)
        return ([_ca(ref_res[pairs[k][0]][pairs[k][1]]) for k in keys],
                [_ca(entry_res[k[0]][k[1]]) for k in keys])

    most = max(len(p) for p, _ in candidates)
    scored = []
    for pairs, identity in candidates:
        if len(pairs) >= 0.9 * most:
            ref_pos, pos = positions(pairs)
            result, n_core = _superpose(ref_pos, pos)
            scored.append((result.rmsd, n_core, _rmsd(ref_pos, pos, result.transform), pairs, identity, result))
    # the assignment whose core fits best, among those whose core keeps most pairs
    _, n_core, global_rmsd, pairs, identity, result = min(scored, key=lambda s: (-s[1] // 10, s[0]))

    ligand = [gemmi.Position(result.transform.apply(a.pos)) for a in site.ligand]
    ref_residues = [(c.subchain, i, r) for c in ref.chains for i, r in enumerate(c.residues)]
    pocket = _within(ref_residues, [a.pos for a in ref.ligand] + ligand, cutoff)
    pocket_pairs = {k: v for k, v in pairs.items() if v in pocket}
    transform, pocket_rmsd = result.transform, None
    if len(pocket_pairs) >= MIN_POCKET:
        ref_pos, pos = positions(pocket_pairs)
        refit, n_core = _superpose(ref_pos, pos)
        transform, pocket_rmsd = refit.transform, refit.rmsd
    else:
        ref_pos, pos = positions(pocket_pairs) if pocket_pairs else ([], [])
    moved = [(v, d) for v, d in zip(pocket_pairs.values(), _distances(ref_pos, pos, transform)) if d > MOVED]
    return Fit(transform, global_rmsd, len(pairs), pocket_rmsd, len(pocket_pairs), n_core, identity, pairs, moved)


# --- interactions ----------------------------------------------------------------------------------------

def _label(residue: Any, chain: str) -> str:
    return f"{_one_letter(residue)}{_seqid(residue)}:{chain}"


def interactions(site: Site, ref: Site, pairs: dict[tuple[str, int], tuple[str, int]]) -> tuple[list[str], list[dict[str, Any]]]:
    """The residues within CONTACT Å of the ligand and its hydrogen bonds (polar contacts), in the
    superposed coordinates. Residues are named by their reference counterpart (e.g. 'D25:A'), so the same
    position has the same name in every entry; a residue with no counterpart keeps its own name with the
    entry's PDB id."""
    ref_res = {c.subchain: (c.name, c.residues) for c in ref.chains}
    index = {(c.subchain, _seqid(r)): (c, i) for c in site.chains for i, r in enumerate(c.residues)}

    def name(chain: ProteinChain, i: int) -> str:
        counterpart = pairs.get((chain.subchain, i))
        if counterpart is None:
            return f"{_label(chain.residues[i], chain.name)} ({site.request.pdb_id})"
        ref_chain, residues = ref_res[counterpart[0]]
        return _label(residues[counterpart[1]], ref_chain)

    model = site.structure[0]
    ns = gemmi.NeighborSearch(model, site.structure.cell, CONTACT + 1).populate()
    contacts: dict[str, None] = {}
    hbonds = []
    for atom in site.ligand:
        for mark in ns.find_atoms(atom.pos, "\0", radius=max(CONTACT, HBOND[1])):
            cra = mark.to_cra(model)
            key = (cra.residue.subchain, _seqid(cra.residue))
            if key not in index:
                continue
            chain, i = index[key]
            distance = atom.pos.dist(cra.atom.pos)
            if distance <= CONTACT:
                contacts[name(chain, i)] = None
            polar = atom.element.name in ("N", "O") and cra.atom.element.name in ("N", "O")
            if polar and HBOND[0] <= distance <= HBOND[1] and not (cra.residue.name == "PRO" and cra.atom.name == "N"):
                hbonds.append({"ligand_atom": atom.name, "residue": name(chain, i), "atom": cra.atom.name,
                               "distance": round(distance, 2),
                               "a": [round(v, 3) for v in atom.pos.tolist()],
                               "b": [round(v, 3) for v in cra.atom.pos.tolist()]})
    order = {n: k for k, n in enumerate(_residue_order(ref))}
    return sorted(contacts, key=lambda n: (order.get(n, len(order)), n)), hbonds


def _residue_order(ref: Site) -> list[str]:
    return [_label(r, c.name) for c in ref.chains for r in c.residues]


# --- output ----------------------------------------------------------------------------------------------

def _sub_structure(site: Site, with_protein: bool, with_ligand: bool) -> Any:
    st = gemmi.Structure()
    st.name = site.request.pdb_id
    model = gemmi.Model("1")
    if with_protein:
        for c in site.chains:
            chain = gemmi.Chain(c.name)
            for r in c.residues:
                chain.add_residue(r)
            model.add_chain(chain)
    if with_ligand:
        chain = gemmi.Chain(site.ligand_chain)
        chain.add_residue(site.ligand)
        model.add_chain(chain)
    st.add_model(model)
    st.setup_entities()
    return st


def _pdb(st: Any, bonds: list[tuple[str, str, int]] = ()) -> str:
    """PDB text with only atom records: the viewer needs no ANISOU, CRYST1 or other records. With `bonds`
    (atom names), CONECT records follow, repeated once per bond order: 3Dmol draws those as double and
    triple bonds."""
    text = st.make_pdb_string(gemmi.PdbWriteOptions(minimal_file=True))
    lines = [line for line in text.splitlines(keepends=True) if line.startswith(("ATOM", "HETATM", "TER"))]
    serial = {line[12:16].strip(): int(line[6:11]) for line in lines if line.startswith("HETATM")}
    for a, b, order in bonds:
        if a in serial and b in serial:  # atoms missing from the model have no bond
            for _ in range(order):
                lines.append(f"CONECT{serial[a]:5d}{serial[b]:5d}\n")
                lines.append(f"CONECT{serial[b]:5d}{serial[a]:5d}\n")
    return "".join(lines)


@dataclass
class Overlay:
    reference: str
    entries: list[dict[str, Any]]
    skipped: list[dict[str, str]]
    residues: list[str]  # contact residues over all entries, in reference order
    notes: list[str] = field(default_factory=list)
    sites: list[Site] = field(default_factory=list, repr=False)
    cutoff: float = 8.0  # Å, the pocket: reference residues this close to a ligand

    def summary(self) -> list[dict[str, Any]]:
        keys = ["pdb_id", "het", "name", "monomerid", "affinity", "resolution", "pocket_rmsd", "global_rmsd",
                "n_pocket", "n_core", "moved", "identity", "target_identity", "chains", "contacts", "potencies",
                "hbond_partners", "note"]
        return [{k: e.get(k) for k in keys} for e in self.entries]

    def viewer_data(self, title: str) -> dict[str, Any]:
        """What the viewer draws: per entry the protein chains and the ligand as PDB text, and H-bonds."""
        return {"title": title, "reference": self.reference, "residues": self.residues,
                "entries": self.entries, "skipped": self.skipped, "notes": self.notes, "pocket_cutoff": self.cutoff}

    def write(self, folder: Path, title: str) -> dict[str, Path]:
        """Superposed complexes as mmCIF (one file per entry) and the viewer data as JSON."""
        folder.mkdir(parents=True, exist_ok=True)
        files = {}
        for site, entry in zip(self.sites, self.entries):
            name = f"{entry['pdb_id']}_{entry['het']}"
            path = folder / f"{name}.cif"
            _sub_structure(site, True, True).make_mmcif_document().write_file(str(path))
            files[name] = path
        (folder / "overlay.json").write_text(json.dumps(self.viewer_data(title)))
        files["json"] = folder / "overlay.json"
        return files


MIN_TARGET_IDENTITY = 40.0  # %, below it the ligand's chain is taken to be another protein


def build_overlay(requests: list[Request], cache: PdbCache, accessions: set[str], reference: str | None = None,
                  cutoff: float = 8.0, sequences: list[str] | None = None) -> Overlay:
    """Fetch, superpose and analyse the entries. With the target's `sequences`, an entry whose ligand sits on a
    chain less than MIN_TARGET_IDENTITY % identical to all of them is skipped as a complex of another protein.
    Entries that fail are listed in `skipped` with the reason; StructureError when none is left."""
    sites, skipped, identities = [], [], {}
    for request in requests:
        try:
            site = load_site(cache.path(request.pdb_id), request, accessions)
        except StructureError as e:
            skipped.append({"pdb_id": request.pdb_id, "reason": str(e)})
            continue
        if sequences:
            identity = max(sequence_identity(site.primary, s) for s in sequences)
            if identity < MIN_TARGET_IDENTITY:
                skipped.append({"pdb_id": request.pdb_id, "reason": (
                    f"{request.pdb_id}: ligand {request.het} is bound to another protein (chain "
                    f"{site.primary.name} is {identity:.0f}% identical to the target)")})
                continue
            identities[request.pdb_id] = round(identity, 1)
        sites.append(site)
    if not sites:
        raise StructureError("No entry could be used: " + "; ".join(s["reason"] for s in skipped))
    if reference:
        ref = next((s for s in sites if s.request.pdb_id == normalize_pdb_id(reference)), None)
        if ref is None:
            raise StructureError(f"The reference {reference} is not among the usable entries")
    else:
        ref = min(sites, key=lambda s: (s.resolution is None, s.resolution or 0.0))
    sites.sort(key=lambda s: s is not ref)  # reference first

    ref_chains = {c.subchain: (c.residues, c.name) for c in ref.chains}
    entries, kept = [], []
    for site in sites:
        try:
            result = fit(site, ref, cutoff)
        except StructureError as e:
            skipped.append({"pdb_id": site.request.pdb_id, "reason": str(e)})
            continue
        site.structure[0].transform_pos_and_adp(result.transform)
        site.ligand = next(r for c in site.structure[0] for r in c
                           if r.name == site.ligand.name and r.seqid == site.ligand.seqid
                           and r.subchain == site.ligand.subchain).clone()
        for chain in site.chains:  # residues were copies; take the moved ones
            moved = {(r.subchain, _seqid(r)): r for c in site.structure[0] for r in c}
            chain.residues = [moved[(chain.subchain, _seqid(r))] for r in chain.residues]
        contacts, hbonds = interactions(site, ref, result.pairs)
        info = site.request.info
        entries.append({
            "pdb_id": site.request.pdb_id, "het": site.request.het.upper(),
            "name": info.get("name"), "monomerid": info.get("monomerid"), "affinity": info.get("affinity"),
            "p_affinity": info.get("p_affinity"), "affinity_type": info.get("affinity_type"),
            "value_nm": info.get("value_nm"), "n_measurements": info.get("n_measurements"),
            "potencies": info.get("potencies") or {}, "measured_on": info.get("measured_on"),
            "resolution": site.resolution, "method": site.method, "title": site.title,
            "pocket_rmsd": None if result.pocket_rmsd is None else round(result.pocket_rmsd, 2),
            "global_rmsd": round(result.global_rmsd, 2), "n_pocket": result.n_pocket, "n_core": result.n_core,
            "moved": [f"{_label(ref_chains[s][0][i], ref_chains[s][1])} ({d:.1f} Å)" for (s, i), d in result.moved],
            "identity": round(result.identity, 1),
            "chains": [c.name for c in site.chains], "ligand_chain": site.ligand_chain,
            "ligand_residue": f"{site.ligand.name} {site.ligand_chain}{_seqid(site.ligand)}",
            "target_identity": identities.get(site.request.pdb_id),
            "contacts": contacts, "hbonds": hbonds,
            "hbond_partners": sorted({h["residue"] for h in hbonds}),
            "note": "pocket fit not possible, whole-chain fit used" if result.pocket_rmsd is None else "",
            "protein_pdb": _pdb(_sub_structure(site, True, False)),
            "ligand_pdb": _pdb(_sub_structure(site, False, True), site.bonds),
        })
        kept.append(site)
    for k, entry in enumerate(entries):
        entry["colour"] = PALETTE[k % len(PALETTE)]
    order = {n: k for k, n in enumerate(_residue_order(ref))}
    residues = sorted({c for e in entries for c in e["contacts"]}, key=lambda n: (order.get(n, len(order)), n))
    notes = []
    if accessions and not any(s.mapped for s in kept):
        notes.append(f"No chain maps to the target's UniProt accession ({', '.join(sorted(accessions))}) in SIFTS; "
                     "the chains around each ligand were used")
    return Overlay(ref.request.pdb_id, entries, skipped, residues, notes, kept, cutoff)
