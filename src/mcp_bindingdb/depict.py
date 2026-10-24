"""Structure drawings for transcripts and figures: molecules aligned on a shared core, drawn in one frame.

Molecules that share a core (given, or else their maximum common substructure) get 2D coordinates that
put the core at the same place and orientation, and are drawn in a frame that holds all of them, so the
core sits on the same pixels in every drawing and all are at the same scale. RDKit is optional (the
`substructure` extra); without it nothing is drawn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

try:
    import numpy as np
    from rdkit import Chem, Geometry, rdBase
    from rdkit.Chem import rdDepictor, rdFMCS, rdMolTransforms
    from rdkit.Chem.Draw import rdMolDraw2D
except ImportError:  # the `substructure` extra is not installed
    Chem = None

BOND_PX = 24  # drawing scale: the length of a bond in pixels
MARGIN = 0.6  # frame margin around the atoms, in bond lengths (room for atom labels)
MIN_CORE_ATOMS = 6  # a smaller common substructure (e.g. one ring) is not worth aligning on
MCS_TIMEOUT_S = 2
HIGHLIGHT = (0.96, 0.62, 0.25, 0.55)  # the core


def available() -> bool:
    return Chem is not None


@dataclass
class Layout:
    """Molecules with 2D coordinates, their core atoms, and the frame they are drawn in."""

    mols: list[Any]  # None where the SMILES (or SMARTS) could not be parsed
    cores: list[tuple[int, ...]]  # core atom indices per molecule (empty: not aligned)
    lo: Any  # Point2D, lower-left corner of the shared frame; None: each molecule in its own frame
    hi: Any
    bond: float  # bond length in coordinate units

    def frame(self, k: int) -> tuple[Any, Any]:
        return (self.lo, self.hi) if self.lo is not None else _bounds([self.mols[k]], self.bond)

    def size(self, k: int) -> tuple[int, int]:
        """Pixel size of drawing k."""
        lo, hi = self.frame(k)
        px = BOND_PX / self.bond
        return round((hi.x - lo.x) * px), round((hi.y - lo.y) * px)


def parse(text: str) -> Any:
    if not text:
        return None
    _quiet = rdBase.BlockLogs()
    mol = Chem.MolFromSmiles(text) or Chem.MolFromSmarts(text)
    if mol is None or mol.GetNumAtoms() == 0:
        return None
    try:
        mol.UpdatePropertyCache(strict=False)
        Chem.GetSymmSSSR(mol)
    except (RuntimeError, ValueError):
        return None
    return mol


def canonical(text: str) -> str:
    """A molecule's canonical SMILES, to tell whether two SMILES are the same molecule; the text itself
    if it cannot be parsed."""
    mol = parse(text) if available() else None
    return Chem.MolToSmiles(mol) if mol is not None else text.strip()


def _core(mols: list[Any], align_to: str | None) -> Any:
    """The core to align on: `align_to`, or else the molecules' maximum common substructure."""
    if align_to:
        return parse(align_to)
    if len(mols) < 2:
        return None
    result = rdFMCS.FindMCS(mols, timeout=MCS_TIMEOUT_S, ringMatchesRingOnly=True, completeRingsOnly=True)
    if result.canceled or result.numAtoms < MIN_CORE_ATOMS:
        return None
    return Chem.MolFromSmarts(result.smartsString)


def _orient(mol: Any, core_atoms: tuple[int, ...]) -> None:
    """Rotate mol so its core runs left to right: from the core's first atom to the core atom farthest
    from it (for 4-chloroaniline, Nc1ccc(Cl)cc1: from N on the left to Cl on the right)."""
    conf = mol.GetConformer()
    first = conf.GetAtomPosition(core_atoms[0])
    far = max(core_atoms, key=lambda i: (conf.GetAtomPosition(i) - first).LengthSq())
    v = conf.GetAtomPosition(far) - first
    if v.LengthSq() == 0:
        return
    a = -math.atan2(v.y, v.x)
    rot = np.array([[math.cos(a), -math.sin(a), 0, 0], [math.sin(a), math.cos(a), 0, 0],
                    [0, 0, 1, 0], [0, 0, 0, 1]])
    rdMolTransforms.TransformConformer(conf, rot)


def _bounds(mols: list[Any], bond: float) -> tuple[Any, Any]:
    pts = [p for m in mols if m is not None for p in m.GetConformer().GetPositions()]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    pad = MARGIN * bond
    return Geometry.Point2D(min(xs) - pad, min(ys) - pad), Geometry.Point2D(max(xs) + pad, max(ys) + pad)


def _bond_length(mols: list[Any]) -> float:
    """Median 2D bond length (the depiction's unit); 1.5 for molecules without bonds."""
    lengths = sorted(rdMolTransforms.GetBondLength(m.GetConformer(), b.GetBeginAtomIdx(), b.GetEndAtomIdx())
                     for m in mols if m is not None for b in m.GetBonds())
    return lengths[len(lengths) // 2] if lengths and lengths[len(lengths) // 2] > 0 else 1.5


def layout(texts: list[str], align_to: str | None = None) -> Layout:
    """Parse and lay out molecules (SMILES, or SMARTS for a query), aligned on a common core if any."""
    rdDepictor.SetPreferCoordGen(True)  # lays out the rest of a templated molecule with fewer clashes
    mols = [parse(t) for t in texts]
    valid = [m for m in mols if m is not None]
    core = _core(valid, align_to) if valid else None
    reference, ref_match = None, ()
    cores: list[tuple[int, ...]] = []
    for mol in mols:
        match = mol.GetSubstructMatch(core) if mol is not None and core is not None else ()
        if mol is None:
            cores.append(())
            continue
        if match and reference is None:
            rdDepictor.Compute2DCoords(mol)
            _orient(mol, match)
            reference, ref_match = mol, match
        elif match:
            try:
                rdDepictor.GenerateDepictionMatching2DStructure(mol, reference, list(zip(ref_match, match)))
            except ValueError:
                rdDepictor.Compute2DCoords(mol)
                match = ()
        else:
            rdDepictor.Compute2DCoords(mol)
        cores.append(tuple(match))
    bond = _bond_length(mols)
    aligned = [m for m, c in zip(mols, cores) if m is not None and c]
    lo, hi = _bounds(aligned, bond) if len(aligned) > 1 else (None, None)
    if lo is not None and len(aligned) < len(valid):  # some molecules lack the core: own frames for all
        lo = hi = None
    return Layout(mols, cores, lo, hi, bond)


def _draw(drawer: Any, lay: Layout, k: int, width: int, height: int) -> None:
    mol, core = lay.mols[k], lay.cores[k]
    opts = drawer.drawOptions()
    opts.setHighlightColour(HIGHLIGHT)
    opts.highlightBondWidthMultiplier = 12
    opts.highlightRadius = 0.45
    opts.minFontSize = 13
    opts.bondLineWidth = 1.5
    lo, hi = lay.frame(k)
    drawer.SetScale(width, height, lo, hi)
    bonds = [b.GetIdx() for b in mol.GetBonds() if b.GetBeginAtomIdx() in core and b.GetEndAtomIdx() in core]
    _quiet = rdBase.BlockLogs()
    drawer.DrawMolecule(mol, highlightAtoms=list(core), highlightBonds=bonds)
    drawer.FinishDrawing()


def svg(lay: Layout, k: int) -> str | None:
    """Drawing k of a layout as SVG, or None if that molecule could not be parsed or drawn."""
    if lay.mols[k] is None:
        return None
    width, height = lay.size(k)
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    try:
        _draw(drawer, lay, k, width, height)
    except (RuntimeError, ValueError):
        return None
    return drawer.GetDrawingText()


def png(lay: Layout, k: int, scale: float = 1.0) -> bytes | None:
    """Drawing k of a layout as PNG (scale > 1 for sharper output), or None if it cannot be drawn."""
    if lay.mols[k] is None:
        return None
    width, height = (round(v * scale) for v in lay.size(k))
    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    try:
        _draw(drawer, lay, k, width, height)
    except (RuntimeError, ValueError):
        return None
    return drawer.GetDrawingText()
