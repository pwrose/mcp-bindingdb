"""Substructure and similarity search over BindingDB compounds.

Substructure search uses an RDKit SubstructLibrary; similarity search uses Tanimoto on Morgan
fingerprints, computed with numpy bit counts. Both come from one index file, built by
scripts/build_substructure_index.py and stored next to the DuckDB file (data/bindingdb_<release>.sslib).
RDKit is optional: install it with the `substructure` extra. Without RDKit or the index file the
server simply does not offer these searches.
"""

from __future__ import annotations

import functools
import pickle
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

try:
    import numpy as np
    from rdkit import Chem, DataStructs, RDLogger, rdBase
    from rdkit.Chem import rdFingerprintGenerator, rdSubstructLibrary
    from rdkit.Chem.MolStandardize import rdMolStandardize
except ImportError:  # the `substructure` extra is not installed
    Chem = None

FORMAT_VERSION = 3
CHUNK = 100_000  # compounds per GetMatches call or Tanimoto block; the time limit is checked between chunks
MORGAN = {"radius": 2, "fp_size": 2048}  # ECFP4-like; computed on the largest fragment

QueryType = Literal["auto", "smiles", "smarts"]


def rdkit_available() -> bool:
    return Chem is not None


def index_path(db_path: Path) -> Path:
    return db_path.with_suffix(".sslib")


def write_index(path: Path, meta: dict[str, Any], monomerids: Any, smiles: list[str], fingerprints: Any,
                morgan: Any) -> None:
    """Write the index as two pickles, a small header first so it can be read without the payload.

    The payload is plain arrays (monomerids, canonical SMILES, pattern-fingerprint bits, Morgan
    fingerprint bits) rather than SubstructLibrary.Serialize(): rebuilding the library from them
    takes a few seconds and about a fifth of the memory that deserializing RDKit's archive format does.
    """
    with open(path, "wb") as f:
        pickle.dump({"format_version": FORMAT_VERSION, "morgan": MORGAN, **meta}, f,
                    protocol=pickle.HIGHEST_PROTOCOL)
        pickle.dump({"monomerids": monomerids, "smiles": "\n".join(smiles).encode(),
                     "fingerprints": fingerprints, "morgan": morgan}, f, protocol=pickle.HIGHEST_PROTOCOL)


@functools.cache
def _morgan_tools() -> tuple[Any, Any]:
    return (rdFingerprintGenerator.GetMorganGenerator(radius=MORGAN["radius"], fpSize=MORGAN["fp_size"]),
            rdMolStandardize.LargestFragmentChooser())


def morgan_fingerprint(mol: Any) -> bytes:
    """Raw bits of the Morgan fingerprint of the largest fragment, so salts and solvates score as the parent."""
    generator, largest = _morgan_tools()
    _quiet = rdBase.BlockLogs()  # LargestFragmentChooser logs every call
    return DataStructs.BitVectToBinaryText(generator.GetFingerprint(largest.choose(mol)))


def read_header(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return pickle.load(f)


class QueryParseError(ValueError):
    pass


def parse_query(query: str, query_type: QueryType = "auto") -> tuple[Any, str]:
    """Parse a substructure query; returns (mol, 'smiles' | 'smarts').

    auto: SMILES, so Kekulé and aromatic forms match the same compounds, except SMARTS when the query
    contains '*', is not valid SMILES, or would silently become something that matches nothing as
    SMILES: a fragment written aromatic that is not aromatic as a molecule (ring nitrogens lacking
    their H or substituent), or a bracket atom without H such as '[#7]' or '[N]', which SMILES makes a
    radical. H counts written in brackets are enforced only by SMARTS.
    """
    q = query.strip()
    if not q:
        raise QueryParseError("Empty query")
    RDLogger.DisableLog("rdApp.*")
    try:
        if query_type == "smiles" or (query_type == "auto" and "*" not in q):
            mol = Chem.MolFromSmiles(q)
            if mol is not None and (query_type == "smiles" or not _misread_as_smiles(q, mol)):
                return mol, "smiles"
            if query_type == "smiles":
                raise QueryParseError(f"Not valid SMILES: {q!r}")
        mol = Chem.MolFromSmarts(q)
        if mol is None:
            raise QueryParseError(f"Not valid SMILES or SMARTS: {q!r}" if query_type == "auto"
                                  else f"Not valid SMARTS: {q!r}")
        return mol, "smarts"
    finally:
        RDLogger.EnableLog("rdApp.*")


def _misread_as_smiles(query: str, smiles_mol: Any) -> bool:
    """True if SMILES parsing made a radical, or made an atom written aromatic (lowercase) non-aromatic."""
    if any(a.GetNumRadicalElectrons() for a in smiles_mol.GetAtoms()):
        return True
    written = Chem.MolFromSmarts(query)  # atoms in the same order, aromaticity as written
    if written is None or written.GetNumAtoms() != smiles_mol.GetNumAtoms():
        return False
    return any(a.GetIsAromatic() and not smiles_mol.GetAtomWithIdx(a.GetIdx()).GetIsAromatic()
               for a in written.GetAtoms())


def parse_molecule(smiles: str) -> Any:
    """Parse a whole-molecule SMILES for similarity search."""
    RDLogger.DisableLog("rdApp.*")
    try:
        mol = Chem.MolFromSmiles(smiles.strip()) if smiles.strip() else None
    finally:
        RDLogger.EnableLog("rdApp.*")
    if mol is None or mol.GetNumAtoms() == 0:
        raise QueryParseError(f"Not valid SMILES: {smiles!r}")
    return mol


@dataclass
class Similar:
    monomerids: list[int]  # most similar first
    similarities: list[float]
    searched: int
    total: int

    @property
    def complete(self) -> bool:
        return self.searched >= self.total


@dataclass
class Matches:
    monomerids: list[int]
    searched: int  # compounds searched before stopping
    total: int  # compounds in the search set
    hit_max_results: bool  # stopped because max_results matches were found

    @property
    def complete(self) -> bool:
        return self.searched >= self.total


class SubstructureIndex:
    """A SubstructLibrary and Morgan fingerprints over all compounds, ordered by number of measurements
    (most first).

    The index is loaded on first use (or by preload()). Substructure searches are serialized with a
    lock because a target-restricted search sets the library's search order; each uses all CPU cores.
    """

    def __init__(self, path: Path):
        self.path = path
        self.header = read_header(path)
        if self.header.get("format_version") != FORMAT_VERSION:
            raise ValueError(f"{path}: unsupported index format {self.header.get('format_version')}")
        self._lib = None
        self._morgan = None  # (n, fp_size/64) uint64
        self._morgan_bits = None  # set bits per compound
        self._ids = None  # monomerid per library index
        self._sorted_ids = None
        self._order = None
        self._load_lock = threading.Lock()
        self._search_lock = threading.Lock()

    @property
    def release(self) -> str | None:
        return self.header.get("release")

    @property
    def n_compounds(self) -> int:
        return self.header["n_compounds"]

    def preload(self) -> None:
        self._load()

    def _load(self) -> None:
        with self._load_lock:
            if self._lib is not None:
                return
            with open(self.path, "rb") as f:
                pickle.load(f)  # header
                payload = pickle.load(f)
            ids = np.asarray(payload["monomerids"], dtype=np.int64)
            mols = rdSubstructLibrary.CachedTrustedSmilesMolHolder()
            for smiles in payload.pop("smiles").decode().split("\n"):
                mols.AddSmiles(smiles)
            fps = rdSubstructLibrary.PatternHolder()
            for row in payload.pop("fingerprints"):
                fps.AddFingerprint(DataStructs.CreateFromBinaryText(row.tobytes()))
            self._morgan = np.ascontiguousarray(payload.pop("morgan")).view(np.uint64)
            self._morgan_bits = np.bitwise_count(self._morgan).sum(axis=1, dtype=np.int32)
            self._order = np.argsort(ids, kind="stable")
            self._sorted_ids = ids[self._order]
            self._ids = ids
            self._lib = rdSubstructLibrary.SubstructLibrary(mols, fps)

    def _indices_for(self, monomerids: list[int]) -> list[int]:
        """Library indices of the given monomerids (those not in the index are dropped), in index order."""
        sub = np.unique(np.asarray(monomerids, dtype=np.int64))
        pos = np.searchsorted(self._sorted_ids, sub).clip(0, len(self._sorted_ids) - 1)
        found = self._sorted_ids[pos] == sub
        return sorted(self._order[pos[found]].tolist())

    def search(self, query: Any, max_results: int, time_limit_s: float, use_chirality: bool = False,
               within: list[int] | None = None) -> Matches:
        """Matching monomerids, in index order (most-measured compounds first).

        `within` restricts the search to those monomerids. Stops at max_results matches or when the
        time limit passes (checked between chunks), so a Matches may be incomplete.
        """
        self._load()
        deadline = time.monotonic() + time_limit_s
        with self._search_lock:
            if within is not None:
                order = self._indices_for(within)
                if not order:  # an empty search order would mean "search everything"
                    return Matches([], 0, 0, False)
                total = len(order)
                self._lib.SetSearchOrder(order)
            else:
                total = len(self._ids)
            found: list[int] = []
            searched = 0
            try:
                while searched < total and len(found) < max_results and time.monotonic() < deadline:
                    end = min(searched + CHUNK, total)
                    hits = self._lib.GetMatches(query, searched, end, recursionPossible=True,
                                                useChirality=use_chirality, useQueryQueryMatches=False,
                                                numThreads=-1, maxResults=max_results - len(found))
                    found.extend(hits)
                    searched = end
            finally:
                if within is not None:
                    self._lib.SetSearchOrder([])
        hit_max = len(found) >= max_results
        return Matches([int(self._ids[i]) for i in found[:max_results]], searched, total, hit_max)

    def count(self, query: Any, time_limit_s: float, use_chirality: bool = False) -> tuple[int, int, int]:
        """(matches, compounds searched, total compounds); searched < total if the time limit passed."""
        self._load()
        deadline = time.monotonic() + time_limit_s
        total = len(self._ids)
        n = searched = 0
        with self._search_lock:
            while searched < total and time.monotonic() < deadline:
                end = min(searched + CHUNK, total)
                n += self._lib.CountMatches(query, searched, end, recursionPossible=True,
                                            useChirality=use_chirality, useQueryQueryMatches=False,
                                            numThreads=-1)
                searched = end
        return n, searched, total

    def similar(self, mol: Any, threshold: float, time_limit_s: float, within: list[int] | None = None) -> Similar:
        """Compounds with Tanimoto similarity >= threshold on Morgan fingerprints, most similar first
        (ties: most-measured first). `within` restricts the search to those monomerids."""
        self._load()
        deadline = time.monotonic() + time_limit_s
        q = np.frombuffer(morgan_fingerprint(mol), dtype=np.uint64)
        q_bits = int(np.bitwise_count(q).sum())
        rows = np.arange(len(self._ids)) if within is None else np.asarray(self._indices_for(within), dtype=np.int64)
        idx_parts, sim_parts = [], []
        searched = 0
        while searched < len(rows) and time.monotonic() < deadline:
            r = rows[searched:searched + CHUNK]
            block = self._morgan[r[0]:r[-1] + 1] if within is None else self._morgan[r]
            common = np.bitwise_count(block & q).sum(axis=1, dtype=np.int32)
            union = self._morgan_bits[r] + q_bits - common
            sim = np.divide(common, union, out=np.zeros(len(r), dtype=np.float64), where=union > 0)
            keep = sim >= threshold
            idx_parts.append(r[keep])
            sim_parts.append(sim[keep])
            searched += len(r)
        idx = np.concatenate(idx_parts) if idx_parts else np.zeros(0, dtype=np.int64)
        sim = np.concatenate(sim_parts) if sim_parts else np.zeros(0)
        order = np.lexsort((idx, -sim))
        return Similar(self._ids[idx[order]].tolist(), np.round(sim[order], 3).tolist(), searched, len(rows))
