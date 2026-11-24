"""Structure drawings for transcripts and figures: molecules aligned on a shared core, drawn in one frame.

Molecules that share a core (given, or else their maximum common substructure) get 2D coordinates that
put the core at the same place and orientation, and are drawn in a frame that holds all of them, so the
core sits on the same pixels in every drawing and all are at the same scale. A molecule that lacks the
core (an outlier) is drawn unaligned in a frame of the same size, so it is at that scale too. RDKit is
optional (the `substructure` extra); without it nothing is drawn.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
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
MIN_CORE_ATOMS = 8  # a smaller common substructure (e.g. one ring) is not worth aligning on
MIN_CORE_SHARE = 0.8  # the share of the molecules a core found by search must be in (rounded up)
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
    attachments: bool = False  # draw '*' atoms as attachment points (a substituent of an R-group table)
    own: dict[int, tuple[Any, Any]] = field(default_factory=dict)  # outliers: a frame of the shared size
    core: str | None = None  # the core aligned on (SMARTS), or None
    core_atoms: int = 0  # its atoms; with no core, those of the largest common substructure found

    def frame(self, k: int) -> tuple[Any, Any]:
        if k in self.own:
            return self.own[k]
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


def core_size(text: str) -> int:
    """The atoms of a core given as SMILES or SMARTS, hydrogens left out; 0 if it cannot be parsed."""
    mol = parse(text) if available() else None
    return sum(1 for a in mol.GetAtoms() if a.GetAtomicNum() != 1) if mol is not None else 0


def _mcs(mols: list[Any], share: float) -> tuple[str, int]:
    """The largest substructure (SMARTS, atoms) in at least `share` of the molecules (rounded up).

    Bonds must match exactly, aromatic only aromatic, so a benzene ring is not one core with a cyclohexane;
    rings match only rings and only whole. `canceled` says the search ran out of time before proving the core
    maximal, not that it found none: it still carries the largest core it reached, which a congeneric series
    of drug-sized molecules routinely hits (six 40-atom JAK inhibitors share 32 atoms that no timeout proves
    optimal), so only its size decides."""
    result = rdFMCS.FindMCS(mols, timeout=MCS_TIMEOUT_S, threshold=share, ringMatchesRingOnly=True,
                            completeRingsOnly=True, bondCompare=rdFMCS.BondCompare.CompareOrderExact)
    return result.smartsString, result.numAtoms


def _core(mols: list[Any], align_to: str | None, min_atoms: int, min_share: float) -> tuple[Any, str | None, int]:
    """The core to align on (query, SMARTS, atoms): `align_to`; else the molecules' largest common
    substructure, if it has `min_atoms`; else the largest in `min_share` of them, if that has `min_atoms`, so
    one unrelated molecule does not cost a series its core. With no core: (None, None, the atoms of the
    largest common substructure found)."""
    if align_to:
        return parse(align_to), align_to, core_size(align_to)
    if len(mols) < 2:
        return None, None, 0
    smarts, atoms = _mcs(mols, 1.0)
    if atoms < min_atoms and min_share < 1 and math.ceil(min_share * len(mols) - 1e-9) < len(mols):
        smarts, atoms = max((smarts, atoms), _mcs(mols, min_share), key=lambda found: found[1])
    if atoms < min_atoms:
        return None, None, atoms
    return Chem.MolFromSmarts(smarts), smarts, atoms


def _run_left_to_right(mol: Any, start: int, atoms: tuple[int, ...]) -> None:
    """Rotate mol so the atom of `atoms` farthest from atom `start` lies to its right."""
    conf = mol.GetConformer()
    first = conf.GetAtomPosition(start)
    far = max(atoms, key=lambda i: (conf.GetAtomPosition(i) - first).LengthSq())
    v = conf.GetAtomPosition(far) - first
    if v.LengthSq() == 0:
        return
    a = -math.atan2(v.y, v.x)
    rot = np.array([[math.cos(a), -math.sin(a), 0, 0], [math.sin(a), math.cos(a), 0, 0],
                    [0, 0, 1, 0], [0, 0, 0, 1]])
    rdMolTransforms.TransformConformer(conf, rot)


def _orient(mol: Any, core_atoms: tuple[int, ...]) -> None:
    """Rotate mol so its core runs left to right: from the core's first atom to the core atom farthest
    from it (for 4-chloroaniline, Nc1ccc(Cl)cc1: from N on the left to Cl on the right)."""
    _run_left_to_right(mol, core_atoms[0], core_atoms)


def _orient_attachment(mol: Any) -> None:
    """Rotate a substituent so it grows to the right of its attachment point, the way it hangs off the
    core in an R-group table."""
    dummies = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 0]
    if len(dummies) == 1 and mol.GetNumAtoms() > 1:
        _run_left_to_right(mol, dummies[0], tuple(range(mol.GetNumAtoms())))


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


def _r_group_dummies(mol: Any, label: bool) -> Any:
    """Prepare the '[*:n]' positions of a core or a substituent for drawing.

    With `label` each dummy becomes the position's name ('R1'), which is how a core is drawn above an
    R-group table. Without it the map number is only dropped, so a drawing made with `attachments` shows
    the dummy as the bond stub where the group attaches rather than as an atom.
    """
    for atom in mol.GetAtoms():
        if atom.GetAtomicNum() == 0 and atom.GetAtomMapNum():
            if label:
                atom.SetProp("atomLabel", f"R{atom.GetAtomMapNum()}")
            atom.SetAtomMapNum(0)
    return mol


def layout(texts: list[str], align_to: str | None = None, label_r_groups: bool = False,
           attachments: bool = False, min_core_atoms: int = MIN_CORE_ATOMS,
           min_core_share: float = MIN_CORE_SHARE) -> Layout:
    """Parse and lay out molecules (SMILES, or SMARTS for a query), aligned on a common core if any: the
    `align_to` core, or the largest common substructure of at least `min_core_atoms` atoms in all of them,
    or else in `min_core_share` of them (see _core). Molecules without the core are drawn unaligned.

    `label_r_groups` names each '[*:n]' position R1, R2, ...; `attachments` draws the unnamed ones as
    attachment points. Both are for the parts of an R-group table: its core and its substituents.
    """
    rdDepictor.SetPreferCoordGen(True)  # lays out the rest of a templated molecule with fewer clashes
    mols = [parse(t) for t in texts]
    if label_r_groups or attachments:
        mols = [None if m is None else _r_group_dummies(m, label_r_groups) for m in mols]
    valid = [m for m in mols if m is not None]
    core, core_smarts, core_atoms = _core(valid, align_to, min_core_atoms, min_core_share) if valid else (None, None, 0)
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
    if attachments:
        for mol in mols:
            if mol is not None:
                _orient_attachment(mol)
    bond = _bond_length(mols)
    aligned = [m for m, c in zip(mols, cores) if m is not None and c]
    lo, hi = _bounds(aligned, bond) if len(aligned) > 1 else (None, None)
    own: dict[int, tuple[Any, Any]] = {}
    if lo is not None and len(aligned) < len(valid):
        # The outliers get frames of one size with the shared frame, each centred on its molecule, so all
        # are drawn at one scale wherever a drawing is shown at a fixed width.
        outliers = [k for k, (m, c) in enumerate(zip(mols, cores)) if m is not None and not c]
        boxes = {k: _bounds([mols[k]], bond) for k in outliers}
        width = max([hi.x - lo.x, *(b[1].x - b[0].x for b in boxes.values())])
        height = max([hi.y - lo.y, *(b[1].y - b[0].y for b in boxes.values())])
        lo, hi = _resized(lo, hi, width, height)
        own = {k: _resized(*box, width, height) for k, box in boxes.items()}
    return Layout(mols, cores, lo, hi, bond, attachments, own, core_smarts if any(cores) else None,
                  core_atoms)


def _resized(lo: Any, hi: Any, width: float, height: float) -> tuple[Any, Any]:
    """A frame of `width` x `height` with the centre of the frame lo-hi."""
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
    return Geometry.Point2D(cx - width / 2, cy - height / 2), Geometry.Point2D(cx + width / 2, cy + height / 2)


def _draw(drawer: Any, lay: Layout, k: int, width: int, height: int) -> None:
    mol, core = lay.mols[k], lay.cores[k]
    opts = drawer.drawOptions()
    opts.setHighlightColour(HIGHLIGHT)
    opts.highlightBondWidthMultiplier = 12
    opts.highlightRadius = 0.45
    opts.minFontSize = 13
    opts.bondLineWidth = 1.5
    opts.dummiesAreAttachments = lay.attachments
    opts.explicitMethyl = lay.attachments  # a substituent cell: a bare line would not read as a methyl
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
