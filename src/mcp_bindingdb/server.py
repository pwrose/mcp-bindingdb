"""MCP server exposing read-only query tools over a local BindingDB DuckDB build."""

from __future__ import annotations

import argparse
import base64
import html
import os
import re
import statistics
import sys
import threading
from datetime import date as _date
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ImageContent, ResourceLink, TextContent, ToolAnnotations
from pydantic import BaseModel, Field

from . import depict, figures, names, sar, substructure, transcript, transcript_html
from . import properties as compound_properties
from .db import Database, QueryError, find_database
from .structure_editor import FIGURE_META, EditorSearches, add_editor_results_tool, create_editor_extension

AffinityType = Literal["Ki", "Kd", "IC50", "EC50", "kon", "koff"]
NameSource = Literal["bindingdb", "opsin", "pubchem"]
POTENCY_TYPES: list[str] = ["Ki", "Kd", "IC50", "EC50"]

INSTRUCTIONS = """\
BindingDB: ~3.2M measured binding affinities between ~1.5M small molecules ("compounds",
BindingDB monomers, ids shown as BDBM<monomerid>) and ~13k protein targets, curated from
articles, patents, PubChem and ChEMBL.

Workflow: resolve names to ids first (search_compounds / search_targets), then use
find_ligands_for_target, find_targets_for_compound, get_compound, get_target, get_activity.
chemical_name_to_smiles turns any compound name (trade name, IUPAC name, CAS number) into a structure
and the BindingDB compounds with that structure, also when the name is not a BindingDB synonym.
Requests to draw, sketch or edit a structure, molecule or compound, or for a structure editor or sketcher
("edit structure", "draw a molecule"), mean open_structure_editor: open it directly, with initial_query
when they name a compound, rather than asking what kind of structure they mean.
The user runs searches in the editor and sees the results there; you do not. When they ask about them,
call get_editor_results with the editor_id open_structure_editor returned.
Use run_sql for anything the curated tools do not cover; call describe_tables first.

Data notes:
- Ki/Kd/IC50/EC50 values are in nM; kon in M^-1 s^-1; koff in s^-1. p_affinity = 9 - log10(nM).
- relation is '=', '<' or '>'. '>' values (e.g. >10000 nM) usually mean inactive at the
  highest tested concentration; potency filters exclude them.
- One compound/target pair often has many measurements from different sources; values for
  different affinity types (IC50 vs Ki) are not directly comparable.
- Targets with mutations or constructs are separate entries with the same UniProt accession
  (uniprot_raw like 'P00533[L858R]'); `uniprot` holds the bare accession.
- source_id is a PubMed id, a patent number (US..., WO...) or a PubChem assay (aid...).
"""

READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

_INCHIKEY = re.compile(r"^[A-Z]{14}(-[A-Z]{10}-[A-Z])?$")
_BDBM = re.compile(r"^(?:BDBM)?(\d+)$", re.IGNORECASE)
_UNIPROT = re.compile(r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$")

TABLE_DOCS = {
    "activity": "Derived. One row per measured value with parsed numeric value, unit, relation, "
    "p_affinity, and denormalized compound, target, assay and citation columns. Start here.",
    "compound": "Derived. One row per small molecule: preferred name, InChIKey, SMILES, formula, "
    "weight, activity/target counts.",
    "compound_property": "Derived (RDKit, computed for the largest fragment). One row per compound "
    "(join on monomerid): heavy_atoms, mw, clogp (Crippen), tpsa, hbd/hba (Lipinski NH+OH, N+O), "
    "rotatable_bonds, rings, aromatic_rings, fsp3, qed, ro5_violations, Bemis-Murcko scaffold and "
    "generic_scaffold (canonical SMILES; NULL without a ring), and the names of matching PAINS, Brenk and "
    "NIH structural alerts (lists, empty if none). Ligand efficiency = 1.37 * p_affinity / heavy_atoms "
    "(kcal/mol per heavy atom); LipE = p_affinity - clogp.",
    "compound_name": "Derived. Compound synonyms (names, CHEMBL ids, PubChem cid_N, patent labels).",
    "target": "Derived. One row per target (polymer or complex) with UniProt accession, organism, counts.",
    "target_name": "Derived. Target synonyms (display names, gene/short names, UniProt entry names).",
    "ki_result": "Raw measurements (Ki, Kd, IC50, EC50, kon, koff as text; pH, temp in K, assay ref).",
    "enzyme_reactant_set": "Raw. Links a measurement to its target (polymer/complex) and ligand (monomer).",
    "monomer": "Raw small molecules (SMILES, InChI, InChIKey, PDB ligand ids). display_name is only the BDBM id.",
    "polymer": "Raw protein targets (sequence, organism, taxid, UniProt fields unpid1/unpid2, PDB ids).",
    "complex": "Raw multi-component targets; complex_component lists their polymers/monomers.",
    "assay": "Raw assay names and descriptions, keyed by (entryid, assayid).",
    "entry": "Raw deposition records (title, measurement technique, date).",
    "article": "Raw publications/patents: pmid (also patent numbers, PubChem aids), doi, title, year.",
    "cobweb_bdb": "Raw denormalized target-inhibitor best-affinity summary used by the BindingDB website.",
    "itc_result_a_b_ab": "Raw isothermal titration calorimetry results (dH, dS, dG, K, stoichiometry).",
    "pdb_bdb": "Raw PDB id to BindingDB id mappings (comma-separated id strings).",
}

COMPOUND_COLUMNS = "monomerid, bdbm_id, name, inchi_key, smiles, n_activities"

ACTIVITY_COLUMNS = """ki_result_id, affinity_type, relation, value, unit, p_affinity, monomerid,
       compound_name, polymerid, complexid, target_name, uniprot_raw, organism, ph, temp_k,
       assay_name, source_id, doi, year"""


def _target_where(target_id: int | None, uniprot: str | None, include_variants: bool,
                  target_kind: str) -> tuple[str, list[Any]]:
    """SQL on activity for one target's measurements, selected by id or by UniProt accession."""
    if (target_id is None) == (uniprot is None):
        raise ToolError("Give exactly one of target_id or uniprot")
    if target_id is not None:
        return ("polymerid = ?" if target_kind == "polymer" else "complexid = ?"), [target_id]
    return ("uniprot = ?" if include_variants else "uniprot_raw = ?"), [uniprot.strip().upper()]


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def _check_range(min_value_nm: float | None, max_value_nm: float | None) -> None:
    if min_value_nm is not None and max_value_nm is not None and min_value_nm > max_value_nm:
        raise ToolError(f"min_value_nm ({min_value_nm:g}) is above max_value_nm ({max_value_nm:g})")


STRUCTURE_INSTRUCTIONS = """
Structure search: substructure_search finds compounds containing a SMILES or SMARTS fragment;
similarity_search finds compounds similar to a molecule (Tanimoto on Morgan fingerprints). Both can be
restricted to compounds with a measurement in an affinity range (affinity_types, min_value_nm,
max_value_nm; applied before the result limit), to compounds whose properties pass a `properties`
filter, or to compounds measured against one target, or summarize the targets their hits were measured
against.
"""


IMAGE_INSTRUCTIONS = """
Figures in transcripts: create_transcript includes only figures in its log. For an image you made with
other tools (e.g. a matplotlib plot saved as PNG), call add_figure with its path and list the figure id
it returns in the exchange; never add images to a transcript, or edit its files, yourself.
"""

PROPERTY_INSTRUCTIONS = """
Compound properties: compound_property holds RDKit properties of each compound's parent (largest
fragment): heavy atoms, MW, cLogP, TPSA, HBD/HBA, QED, Ro5 violations, Bemis-Murcko scaffold, and PAINS,
Brenk and NIH structural alerts. find_ligands_for_target and the structure searches take a `properties`
filter (e.g. max_mw, max_ro5_violations, exclude_alerts, scaffold, min_ligand_efficiency) and give each
measurement's ligand_efficiency (1.37 * p_affinity / heavy atoms, kcal/mol per heavy atom) and lipe
(p_affinity - cLogP), from whichever affinity type the row has. find_ligands_for_target ranks by them
(order_by) or groups a target's ligands by scaffold (group_by_scaffold). A PAINS match flags a potent hit as
a possible assay artefact worth checking; Brenk alerts match about a third of all compounds and are no
reason by themselves to doubt a measurement.
"""


SAR_INSTRUCTIONS = """
Structure-activity relationships, one target at a time: decompose_r_groups tabulates a series (the
target's ligands containing a core, with each R-group position in its own column);
matched_molecular_pairs finds compounds that differ by one group and what the change did to potency, or
aggregates those transformations; activity_cliffs finds near-identical compounds with very different
potency. All three use exact ('=') measurements of a single affinity type, picked as the target's most
measured type unless you name one, so the potency differences are comparable. Show a series from
decompose_r_groups with draw_r_group_table, which draws the core with its positions named R1, R2, ... and
each substituent in its column; a fragment SMILES ('CCC[*:1]') is an input to that tool, never something
to put in a table or an answer.
"""

FIGURE_INSTRUCTIONS = """
Structure figures: to show several compounds' structures together (e.g. in a grid, aligned on a shared
substructure, with binding data), use draw_structure_grid rather than drawing them yourself; for one
series varying at a few positions, draw_r_group_table draws the core with R1, R2, ... named and every
substituent in its column. Their figures appear in the chat and in transcripts. The figure already shows
the structures and binding values: refer to it in your answer instead of repeating them (no table of the
same compounds' SMILES or of the values the bars show; a table only for data the figure lacks).
"""


AFFINITY_FILTER_DOC = "Affinity filter: "
TARGET_ID_FIELD = Field(description="Only compounds measured against this target: polymerid (or complexid "
                        "with target_kind='complex')")
AFFINITY_TYPES_FIELD = Field(description=AFFINITY_FILTER_DOC + "only compounds with a measurement of these "
                             "types (default Ki, Kd, IC50, EC50)")
MAX_VALUE_FIELD = Field(ge=0, description=AFFINITY_FILTER_DOC + "only measurements <= this many nM "
                        "(excludes '>' values)")
MIN_VALUE_FIELD = Field(ge=0, description=AFFINITY_FILTER_DOC + "only measurements >= this many nM "
                        "(excludes '<' values)")

# PropertyFilter field -> (SQL over activity joined with compound_property AS cp, comparison)
PROPERTY_CONDITIONS = {
    "max_mw": ("cp.mw", "<="), "min_heavy_atoms": ("cp.heavy_atoms", ">="), "max_heavy_atoms": ("cp.heavy_atoms", "<="),
    "min_clogp": ("cp.clogp", ">="),
    "max_clogp": ("cp.clogp", "<="), "max_tpsa": ("cp.tpsa", "<="), "max_hbd": ("cp.hbd", "<="),
    "max_hba": ("cp.hba", "<="), "max_rotatable_bonds": ("cp.rotatable_bonds", "<="),
    "max_ro5_violations": ("cp.ro5_violations", "<="), "min_qed": ("cp.qed", ">="),
    "min_ligand_efficiency": (compound_properties.LIGAND_EFFICIENCY_SQL, ">="),
    "min_lipe": (compound_properties.LIPE_SQL, ">="),
}
ACTIVITY_WITH_PROPERTIES = "activity LEFT JOIN compound_property cp USING (monomerid)"
EFFICIENCY_COLUMNS = f""", round({compound_properties.LIGAND_EFFICIENCY_SQL}, 2) AS ligand_efficiency,
       round({compound_properties.LIPE_SQL}, 2) AS lipe,
       CASE WHEN len(cp.pains) > 0 THEN cp.pains END AS pains_alerts"""
OrderBy = Literal["potency", "ligand_efficiency", "lipe"]


class PropertyFilter(BaseModel):
    """Conditions on the compound_property values of a compound's parent (largest fragment)."""
    max_mw: float | None = Field(None, description="Molecular weight at most this (Da)")
    min_heavy_atoms: int | None = Field(None, description="At least this many heavy atoms, e.g. to leave out "
                                        "fragments when ranking by ligand efficiency")
    max_heavy_atoms: int | None = Field(None, description="At most this many heavy atoms")
    min_clogp: float | None = Field(None, description="Crippen cLogP at least this")
    max_clogp: float | None = Field(None, description="Crippen cLogP at most this")
    max_tpsa: float | None = Field(None, description="Topological polar surface area at most this (Å²)")
    max_hbd: int | None = Field(None, description="At most this many H-bond donors (NH + OH)")
    max_hba: int | None = Field(None, description="At most this many H-bond acceptors (N + O)")
    max_rotatable_bonds: int | None = Field(None, description="At most this many rotatable bonds")
    max_ro5_violations: int | None = Field(None, ge=0, le=4, description="At most this many Lipinski "
                                           "rule-of-five violations; 0 = fully compliant")
    min_qed: float | None = Field(None, ge=0, le=1, description="Drug-likeness (QED) at least this")
    exclude_alerts: list[Literal["pains", "brenk", "nih"]] | None = Field(
        None, description="Leave out compounds matching a structural alert of these catalogs")
    scaffold: str | None = Field(None, description="SMILES of a molecule or scaffold: only compounds with the "
                                 "same Bemis-Murcko scaffold (ring systems and linkers) as it")
    min_ligand_efficiency: float | None = Field(None, description="Only measurements with ligand efficiency "
                                                "at least this (kcal/mol per heavy atom; 0.3 is a common "
                                                "bar for leads)")
    min_lipe: float | None = Field(None, description="Only measurements with LipE (p_affinity - cLogP) at "
                                   "least this (5 or more is often sought)")


PROPERTIES_FIELD = Field(description="Only compounds whose properties pass these conditions (computed for "
                         "the largest fragment); see PropertyFilter")

# Shared arguments of the tools that work on one target's measurements (find_ligands_for_target, the
# SAR tools): the target, and the single affinity type a potency difference has to come from.
TargetIdArg = Annotated[int | None, Field(description="polymerid from search_targets (or complexid with "
                                          "target_kind='complex')")]
UniprotArg = Annotated[str | None, Field(description="UniProt accession instead of target_id, e.g. P00533")]
IncludeVariantsArg = Annotated[bool, Field(description="With uniprot: also include mutant/construct "
                                           "targets of that accession")]
TargetKindArg = Annotated[Literal["polymer", "complex"], Field(description="Kind of target_id")]
OneAffinityTypeArg = Annotated[Literal["Ki", "Kd", "IC50", "EC50"] | None, Field(
    description="The affinity type the potencies come from; values of different types are not "
                "comparable, so only one is used. Default: the target's most measured type")]
MaxCompoundsArg = Annotated[int, Field(description="Compounds to work on, most potent first; a lower "
                                       "number is faster, a higher one covers more of the target")]
EXACT_MEASUREMENT = "relation = '=' AND unit = 'nM' AND p_affinity IS NOT NULL"

VERSION = "0.1.0"
LATEST_HTML_URI = "transcript://session/latest.html"
FIGURE_ID_NOTE = ("Transcripts include it under the exchange whose `figures` lists id {id}. They number "
                  "their figures 1, 2, … in the order they appear, whatever the ids: in your answer, refer to "
                  "a figure by that number or its place ('the figure below'), never by its id.")
OUTPUT_DIR_FIELD = Field(description="The folder to write the transcript to, as an absolute path on the "
                         "machine running this server (e.g. the folder the user named for the results). "
                         "Default: the server's transcripts folder")
FILE_NAME_FIELD = Field(description="With output_dir: the file name without extension, e.g. "
                        "'chloroaniline-drugs-transcript'; a file of that name is replaced. Default: from "
                        "the title")


class Exchange(BaseModel):
    prompt: str = Field(description="The user's prompt, verbatim")
    answer: str = Field("", description="Your full answer to that prompt as the user saw it, verbatim, "
                        "including tables and lists; not a summary")
    figures: list[int] = Field(default_factory=list, description="Ids of the figures (from "
                               "draw_structure_grid or add_figure) shown with this answer; the transcript "
                               "numbers its figures 1, 2, … in order")


class BindingDBServer(MCPServer):
    """MCPServer that records every successful tool call for create_transcript."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.tool_log = transcript.ToolLog()
        self.last_markdown: str | None = None
        self.last_html: str | None = None
        self.figure_copies: dict[str, Any] = {}  # file name of a figure copied to an output_dir -> the figure

    async def call_tool(self, name: str, arguments: dict[str, Any], context: Context | None = None) -> Any:
        result = await super().call_tool(name, arguments, context)
        if name not in transcript.UNLOGGED_TOOLS and isinstance(result, CallToolResult) and not result.is_error:
            content = result.structured_content
            if content is None:
                content = "\n".join(c.text for c in result.content if c.type == "text")
            self.tool_log.record(name, arguments, content)
        return result


def load_substructure_index(db: Database) -> substructure.SubstructureIndex | None:
    """The structure index next to the database, if RDKit is installed and the index matches the release."""
    path = substructure.index_path(db.path)
    if not path.is_file():
        return None
    disabled = "substructure_search and similarity_search disabled"
    if not substructure.rdkit_available():
        print(f"mcp-bindingdb: {path.name} found but RDKit is not installed (install the 'substructure' "
              f"extra); {disabled}", file=sys.stderr)
        return None
    rebuild = "rebuild it with scripts/build_substructure_index.py"
    try:
        index = substructure.SubstructureIndex(path)
    except ValueError as e:  # an index written by an older version
        print(f"mcp-bindingdb: {e}; {rebuild}. {disabled}", file=sys.stderr)
        return None
    release = db.build_info().get("release")
    if index.release != release:
        print(f"mcp-bindingdb: {path.name} is for release {index.release}, the database is {release}; "
              f"{rebuild}. {disabled}", file=sys.stderr)
        return None
    return index


def build_server(db: Database, index: substructure.SubstructureIndex | None = None,
                 network: bool = True, transcript_dir: Path | None = None) -> BindingDBServer:
    """`index` enables substructure_search and similarity_search (see load_substructure_index);
    `network` lets chemical_name_to_smiles ask PubChem; HTML transcripts are written to `transcript_dir`
    (default: transcripts/ next to the database)."""
    info = db.build_info()
    has_properties = "properties" in info  # compound_property (scripts/compute_properties.py)
    # Not logged here (BindingDBServer.call_tool) but where the assistant fetches it: get_editor_results.
    editor_searches = EditorSearches(lambda tool, arguments: MCPServer.call_tool(mcp, tool, arguments),
                                     db.path.parent / "editor-searches")
    mcp = BindingDBServer(
        name="mcp-bindingdb",
        extensions=[create_editor_extension(network=network, searches=editor_searches)],
        title="BindingDB",
        version=VERSION,
        instructions=INSTRUCTIONS + (STRUCTURE_INSTRUCTIONS if index else "")
        + (PROPERTY_INSTRUCTIONS if has_properties else "")
        + (SAR_INSTRUCTIONS if sar.available() else "")
        + IMAGE_INSTRUCTIONS + (FIGURE_INSTRUCTIONS if depict.available() else "")
        + f"\nLoaded release: {info.get('release', 'unknown')}.",
    )

    def run(sql: str, params: list[Any] | None = None, limit: int = 100) -> dict[str, Any]:
        try:
            return db.query(sql, params, limit).as_dict()
        except QueryError as e:
            raise ToolError(str(e)) from None

    def potency_filter(affinity_types: list[str] | None, max_value_nm: float | None,
                       min_value_nm: float | None = None) -> tuple[str, list[Any]]:
        types = affinity_types or POTENCY_TYPES
        clauses = ["affinity_type IN (SELECT unnest(?))", "value IS NOT NULL"]
        params: list[Any] = [types]
        if max_value_nm is not None:
            clauses.append("unit = 'nM' AND relation <> '>' AND value <= ?")
            params.append(max_value_nm)
        if min_value_nm:  # a '<' value may lie below the minimum
            clauses.append("unit = 'nM' AND relation <> '<' AND value >= ?")
            params.append(min_value_nm)
        return " AND ".join(clauses), params

    def require_properties(what: str) -> None:
        if not has_properties:
            raise ToolError(f"{what} needs compound properties, which this database lacks; add them with "
                            "scripts/compute_properties.py")

    def property_filter(props: PropertyFilter | None) -> tuple[str, list[Any]]:
        """SQL conditions for `props` on compound_property, joined as cp (ACTIVITY_WITH_PROPERTIES);
        ('', []) when it sets none."""
        conditions = props.model_dump(exclude_none=True) if props else {}
        if not conditions:
            return "", []
        require_properties("The properties filter")
        clauses, params = [], []
        for name, value in conditions.items():
            if name == "scaffold":
                if compound_properties.Chem is None:
                    raise ToolError("The scaffold filter needs RDKit, which is not installed on the server")
                scaffold = compound_properties.murcko_scaffold(value)
                if scaffold is None:
                    raise ToolError(f"scaffold {value!r} is not SMILES of a molecule with a ring")
                clauses.append("cp.scaffold = ?")
                params.append(scaffold)
            elif name == "exclude_alerts":
                clauses += [f"len(cp.{catalog}) = 0" for catalog in dict.fromkeys(value)]
            else:
                expr, op = PROPERTY_CONDITIONS[name]
                clauses.append(f"{expr} {op} ?")
                params.append(value)
        return " AND ".join(clauses), params

    def measurement_filter(affinity_types: list[str] | None, max_value_nm: float | None,
                           min_value_nm: float | None = None,
                           props: PropertyFilter | None = None) -> tuple[str, list[Any], str]:
        """potency_filter and property_filter combined, with the table they apply to: activity, or
        ACTIVITY_WITH_PROPERTIES when there are property conditions."""
        pf, params = potency_filter(affinity_types, max_value_nm, min_value_nm)
        prf, prparams = property_filter(props)
        if not prf:
            return pf, params, "activity"
        return f"{pf} AND {prf}", [*params, *prparams], ACTIVITY_WITH_PROPERTIES

    @mcp.tool(annotations=READ_ONLY)
    def search_compounds(
        query: Annotated[str, Field(description="Compound name or synonym (e.g. 'imatinib'), ChEMBL id, "
                                    "PubChem 'cid_5291', BDBM id / monomerid, or InChIKey (full or 14-char block)")],
        limit: Annotated[int, Field(description="Max results (1-100)")] = 20,
    ) -> dict[str, Any]:
        """Find BindingDB compounds by name, synonym, identifier or InChIKey.

        Exact matches rank first, then substring matches; ties are ordered by number of measurements."""
        q = query.strip()
        limit = _clamp(limit, 1, 100)
        cols = "c.monomerid, c.bdbm_id, c.name, c.inchi_key, c.smiles, c.mol_weight, c.n_activities, c.n_targets"
        if m := _BDBM.match(q):
            return run(f"SELECT {cols} FROM compound c WHERE monomerid = ?", [int(m.group(1))], limit)
        if _INCHIKEY.match(q.upper()):
            return run(
                f"SELECT {cols} FROM compound c WHERE inchi_key = ? OR inchi_key LIKE ? || '-%' "
                "ORDER BY n_activities DESC",
                [q.upper(), q.upper()[:14]],
                limit,
            )
        return run(
            f"""
            WITH hits AS (
              SELECT monomerid, min(CASE WHEN lower(name) = lower(?) THEN 0 ELSE 1 END) AS rank,
                     arg_min(name, length(name)) AS matched_name
              FROM compound_name WHERE name ILIKE '%' || ? || '%'
              GROUP BY monomerid
            )
            SELECT {cols}, h.matched_name
            FROM hits h JOIN compound c USING (monomerid)
            ORDER BY h.rank, c.n_activities DESC, c.monomerid
            """,
            [q, q],
            limit,
        )

    unavailable = {"opsin": names.opsin_unavailable_reason(),
                   "pubchem": None if network else "network lookups disabled (--no-network)"}

    def name_in_bindingdb(name: str) -> dict[str, Any] | None:
        result = run(
            f"""SELECT {COMPOUND_COLUMNS} FROM compound
                WHERE monomerid IN (SELECT monomerid FROM compound_name WHERE lower(name) = lower(?))
                ORDER BY n_activities DESC, monomerid""",
            [name],
            10,
        )
        rows = result["rows"]
        if not rows:
            return None
        best = next((r for r in rows if r["smiles"]), rows[0])
        skeletons = {r["inchi_key"][:14] if r["inchi_key"] else r["monomerid"] for r in rows}
        return {"smiles": best["smiles"], "inchi_key": best["inchi_key"], "monomerid": best["monomerid"],
                "ambiguous": len(skeletons) > 1 or result["truncated"], "candidates": rows}

    def name_in_service(source: str, name: str) -> dict[str, Any] | None:
        s = names.opsin_lookup(name) if source == "opsin" else names.pubchem_lookup(name)
        if s is None:
            return None
        found = {"smiles": substructure.canonical_smiles(s.smiles) or s.smiles, "inchi_key": s.inchi_key}
        extra = {"pubchem_name": s.title, "pubchem_cid": s.cid, "other_pubchem_cids": s.other_cids or None,
                 "warning": s.warning}
        found.update({k: v for k, v in extra.items() if v is not None})
        found["bindingdb_matches"] = run(
            f"""SELECT {COMPOUND_COLUMNS}, inchi_key = ? AS exact_match FROM compound
                WHERE inchi_key LIKE ? || '-%'
                ORDER BY exact_match DESC, n_activities DESC, monomerid""",
            [s.inchi_key, s.inchi_key[:14]],
            10,
        )["rows"] if s.inchi_key else []
        return found

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=network))
    def chemical_name_to_smiles(
        name: Annotated[str, Field(description="Compound name: synonym or trade name (e.g. 'Ibrance'), "
                                   "systematic IUPAC name, or CAS number")],
        sources: Annotated[list[NameSource] | None, Field(description="Sources to try, in this order "
                                                          "(default: bindingdb, opsin, pubchem)")] = None,
    ) -> dict[str, Any]:
        """Convert a chemical name to SMILES, trying BindingDB synonyms (exact, case-insensitive), then
        OPSIN (systematic IUPAC names, offline), then a PubChem name lookup; stops at the first that
        knows the name.

        A BindingDB name can belong to several compounds (stereoisomers, or a label such as 'compound 5'):
        all are returned as candidates, most measured first, with ambiguous=true when their InChIKey
        first blocks differ. A structure from OPSIN or PubChem is matched back to BindingDB by InChIKey
        (bindingdb_matches): the same compound first (exact_match), then compounds with the same first
        block, such as other stereoisomers. Use the SMILES with similarity_search or substructure_search."""
        q = name.strip()
        if not q:
            raise ToolError("Empty name")
        out: dict[str, Any] = {"query": q, "resolved": False}
        tried = []
        for source in dict.fromkeys(sources or ["bindingdb", "opsin", "pubchem"]):
            if reason := unavailable.get(source):
                tried.append({"source": source, "status": "unavailable", "detail": reason})
                continue
            try:
                found = name_in_bindingdb(q) if source == "bindingdb" else name_in_service(source, q)
            except names.NameLookupError as e:
                tried.append({"source": source, "status": "error", "detail": str(e)})
                continue
            tried.append({"source": source, "status": "found" if found else "not found"})
            if found:
                out.update(resolved=True, source=source, **found)
                break
        out["sources_tried"] = tried
        return out

    @mcp.tool(annotations=READ_ONLY)
    def search_targets(
        query: Annotated[str, Field(description="Target name, gene/short name (e.g. 'EGFR'), UniProt entry "
                                    "name (EGFR_HUMAN) or UniProt accession (P00533)")],
        organism: Annotated[str | None, Field(description="Optional organism filter, e.g. 'Homo sapiens'")] = None,
        limit: Annotated[int, Field(description="Max results (1-100)")] = 20,
    ) -> dict[str, Any]:
        """Find BindingDB targets (proteins and protein complexes).

        Mutants and constructs are separate targets; for a UniProt accession all variants are returned.
        Results are ordered by exact match first, then number of measurements."""
        q = query.strip()
        limit = _clamp(limit, 1, 100)
        cols = ("t.target_kind, t.target_id, t.name, t.uniprot, t.uniprot_raw, t.organism, t.type, "
                "t.n_activities, t.n_compounds")
        org_clause, org_params = ("AND t.organism ILIKE '%' || ? || '%'", [organism]) if organism else ("", [])
        if _UNIPROT.match(q.upper()):
            return run(
                f"SELECT {cols} FROM target t WHERE t.uniprot = ? {org_clause} "
                "ORDER BY t.uniprot_raw = t.uniprot DESC, t.n_activities DESC",
                [q.upper(), *org_params],
                limit,
            )
        return run(
            f"""
            WITH hits AS (
              SELECT target_kind, target_id,
                     min(CASE WHEN lower(name) = lower(?) THEN 0 ELSE 1 END) AS rank,
                     arg_min(name, length(name)) AS matched_name
              FROM target_name WHERE name ILIKE '%' || ? || '%'
              GROUP BY ALL
            )
            SELECT {cols}, h.matched_name
            FROM hits h JOIN target t USING (target_kind, target_id)
            WHERE true {org_clause}
            ORDER BY h.rank, t.n_activities DESC, t.target_id
            """,
            [q, q, *org_params],
            limit,
        )

    @mcp.tool(annotations=READ_ONLY)
    def get_compound(
        monomerid: Annotated[int, Field(description="BindingDB monomer id (the number in BDBM<id>)")],
        max_synonyms: Annotated[int, Field(description="Max synonyms to return (0-200)")] = 30,
    ) -> dict[str, Any]:
        """Compound details: structure identifiers, synonyms, PDB ligand ids, and a per-target summary
        of its most potent measurements (top 25 targets by best p_affinity). With compound properties in
        the database, also its properties (MW, cLogP, TPSA, QED, Ro5 violations, ...), Bemis-Murcko
        scaffold, structural alerts (PAINS, Brenk, NIH) and its best ligand efficiency per target."""
        try:
            compound = db.one(
                """SELECT c.*, m.inchi, m.pdb_ids_exact, m.pdb_ids_sub
                   FROM compound c JOIN monomer m USING (monomerid) WHERE monomerid = ?""",
                [monomerid],
            )
            if compound is None:
                raise ToolError(f"No compound with monomerid {monomerid}")
            synonyms = db.rows(
                "SELECT name FROM compound_name WHERE monomerid = ? ORDER BY length(name), name",
                [monomerid],
                limit=_clamp(max_synonyms, 0, 200),
            )
            targets = db.rows(
                """SELECT polymerid, complexid, any_value(target_name) AS target_name,
                          any_value(uniprot_raw) AS uniprot_raw, any_value(organism) AS organism,
                          count(*) AS n_measurements, max(p_affinity) AS best_p_affinity,
                          list(DISTINCT affinity_type ORDER BY affinity_type) AS affinity_types
                   FROM activity WHERE monomerid = ?
                   GROUP BY polymerid, complexid
                   ORDER BY best_p_affinity DESC NULLS LAST, n_measurements DESC, polymerid, complexid LIMIT 25""",
                [monomerid],
                limit=25,
            )
            props = (db.one("SELECT * EXCLUDE (monomerid) FROM compound_property WHERE monomerid = ?", [monomerid])
                     if has_properties else None)
        except QueryError as e:
            raise ToolError(str(e)) from None
        out = {"compound": compound, "synonyms": [s["name"] for s in synonyms], "top_targets": targets}
        if props:
            out["properties"] = props
            for row in targets:  # as LIGAND_EFFICIENCY_SQL
                if row["best_p_affinity"] is not None and props["heavy_atoms"]:
                    row["best_ligand_efficiency"] = round(1.37 * row["best_p_affinity"] / props["heavy_atoms"], 2)
        return out

    @mcp.tool(annotations=READ_ONLY)
    def get_target(
        target_id: Annotated[int, Field(description="polymerid (or complexid when target_kind='complex')")],
        target_kind: Annotated[Literal["polymer", "complex"], Field(description="Target kind")] = "polymer",
        include_sequence: Annotated[bool, Field(description="Include the amino-acid sequence")] = False,
    ) -> dict[str, Any]:
        """Target details: identifiers, organism, synonyms, PDB ids, complex components, and counts of
        measurements by affinity type."""
        try:
            target = db.one("SELECT * FROM target WHERE target_kind = ? AND target_id = ?", [target_kind, target_id])
            if target is None:
                raise ToolError(f"No {target_kind} target with id {target_id}")
            if target_kind == "polymer":
                extra = db.one(
                    "SELECT unpid2, common_name, topology, weight, pdb_ids"
                    + (", sequence" if include_sequence else "")
                    + " FROM polymer WHERE polymerid = ?",
                    [target_id],
                )
                components = None
                id_col = "polymerid"
            else:
                extra = db.one("SELECT pdb_ids, comments FROM complex WHERE complexid = ?", [target_id])
                components = db.rows(
                    """SELECT cc.type, cc.polymerid, p.display_name AS polymer_name, p.unpid1 AS uniprot_raw,
                              cc.monomerid
                       FROM complex_component cc LEFT JOIN polymer p USING (polymerid)
                       WHERE cc.complexid = ?""",
                    [target_id],
                )
                id_col = "complexid"
            synonyms = db.rows(
                "SELECT name FROM target_name WHERE target_kind = ? AND target_id = ? ORDER BY length(name), name",
                [target_kind, target_id],
                limit=50,
            )
            by_type = db.rows(
                f"""SELECT affinity_type, count(*) AS n_measurements, count(DISTINCT monomerid) AS n_compounds,
                           max(p_affinity) AS best_p_affinity
                    FROM activity WHERE {id_col} = ? GROUP BY affinity_type ORDER BY n_measurements DESC""",
                [target_id],
            )
        except QueryError as e:
            raise ToolError(str(e)) from None
        out = {"target": {**target, **(extra or {})}, "synonyms": [s["name"] for s in synonyms],
               "measurements_by_type": by_type}
        if components is not None:
            out["components"] = components
        return out

    @mcp.tool(annotations=READ_ONLY)
    def find_ligands_for_target(
        target_id: Annotated[int | None, Field(description="polymerid from search_targets (or complexid "
                                               "with target_kind='complex')")] = None,
        uniprot: Annotated[str | None, Field(description="UniProt accession instead of target_id, e.g. P00533")] = None,
        include_variants: Annotated[bool, Field(description="With uniprot: also include mutant/construct "
                                                "targets of that accession")] = False,
        target_kind: Annotated[Literal["polymer", "complex"], Field(description="Kind of target_id")] = "polymer",
        affinity_types: Annotated[list[AffinityType] | None, Field(description="Default: Ki, Kd, IC50, EC50")] = None,
        max_value_nm: Annotated[float | None, Field(description="Only measurements <= this many nM "
                                                    "(excludes '>' values)")] = None,
        best_per_compound: Annotated[bool, Field(description="One row per compound (its most potent "
                                                 "measurement) instead of every measurement")] = True,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        order_by: Annotated[OrderBy, Field(description="Rank by potency (p_affinity), ligand_efficiency or "
                                           "lipe")] = "potency",
        group_by_scaffold: Annotated[bool, Field(description="Instead of compounds, one row per Bemis-Murcko "
                                                 "scaffold of the ligands: compounds, best and median "
                                                 "p_affinity, its most potent compound; most compounds "
                                                 "first")] = False,
        generic_scaffold: Annotated[bool, Field(description="With group_by_scaffold: group on generic "
                                                "scaffolds (all atoms carbon, all bonds single), merging "
                                                "scaffolds that differ only in heteroatoms or bond "
                                                "orders")] = False,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Compounds measured against a target, most potent first. With compound properties in the
        database, each row also gives ligand_efficiency, lipe and any PAINS alerts (pains_alerts)."""
        where, params = _target_where(target_id, uniprot, include_variants, target_kind)
        limit = _clamp(limit, 1, 500)
        if group_by_scaffold:
            return _scaffold_groups(where, params, affinity_types, max_value_nm, properties, generic_scaffold,
                                    limit)
        if order_by != "potency":
            require_properties(f"order_by={order_by!r}")
        return _activity_query(where, params, affinity_types, max_value_nm,
                               "monomerid" if best_per_compound else None, limit, props=properties,
                               efficiency=True, order_by=order_by)

    def _scaffold_groups(where: str, params: list[Any], affinity_types: list[str] | None,
                         max_value_nm: float | None, props: PropertyFilter | None, generic: bool,
                         limit: int) -> dict[str, Any]:
        """The scaffolds of the compounds measured where `where` holds, with their compounds' potency."""
        require_properties("group_by_scaffold")
        pf, pparams, _ = measurement_filter(affinity_types, max_value_nm, None, props)
        column = "generic_scaffold" if generic else "scaffold"
        result = run(
            f"""WITH best AS (  -- each compound's most potent measurement
                  SELECT monomerid, any_value(compound_name) AS compound_name, max(p_affinity) AS p_affinity,
                         count(*) AS n_measurements, any_value(cp.{column}) AS scaffold
                  FROM {ACTIVITY_WITH_PROPERTIES} WHERE {where} AND {pf} GROUP BY monomerid
                )
                SELECT scaffold AS scaffold_smiles, count(*) AS n_compounds, sum(n_measurements) AS n_measurements,
                       max(p_affinity) AS best_p_affinity, round(median(p_affinity), 2) AS median_p_affinity,
                       arg_max(monomerid, p_affinity) AS best_monomerid,
                       arg_max(compound_name, p_affinity) AS best_compound_name,
                       count(*) OVER () AS n_scaffolds, sum(count(*)) OVER () AS n_compounds_total
                FROM best GROUP BY scaffold
                ORDER BY n_compounds DESC, best_p_affinity DESC NULLS LAST, scaffold_smiles NULLS LAST""",
            [*params, *pparams],
            limit,
        )
        totals = {"n_scaffolds": 0, "n_compounds": 0}
        for row in result["rows"]:
            totals = {"n_scaffolds": row.pop("n_scaffolds"), "n_compounds": int(row.pop("n_compounds_total"))}
        note = ("scaffold_smiles is null for compounds without a ring" if not generic else
                "Generic scaffolds: all atoms carbon, all bonds single; null for compounds without a ring")
        return {"grouped_by": column, **totals, **result, "note": note}

    @mcp.tool(annotations=READ_ONLY)
    def find_targets_for_compound(
        monomerid: Annotated[int | None, Field(description="BindingDB monomer id")] = None,
        inchi_key: Annotated[str | None, Field(description="InChIKey instead of monomerid; the 14-char first "
                                               "block matches all stereoisomers/salts")] = None,
        affinity_types: Annotated[list[AffinityType] | None, Field(description="Default: Ki, Kd, IC50, EC50")] = None,
        max_value_nm: Annotated[float | None, Field(description="Only measurements <= this many nM "
                                                    "(excludes '>' values)")] = None,
        best_per_target: Annotated[bool, Field(description="One row per target (its most potent "
                                               "measurement) instead of every measurement")] = True,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Targets a compound was measured against (its activity/selectivity profile), most potent first."""
        if (monomerid is None) == (inchi_key is None):
            raise ToolError("Give exactly one of monomerid or inchi_key")
        if monomerid is not None:
            where, params = "monomerid = ?", [monomerid]
        else:
            key = inchi_key.strip().upper()
            where, params = ("inchi_key = ?", [key]) if len(key) > 14 else ("inchi_key LIKE ? || '-%'", [key])
        return _activity_query(where, params, affinity_types, max_value_nm,
                               "coalesce(polymerid, -complexid)" if best_per_target else None,
                               _clamp(limit, 1, 500))

    def _activity_query(where: str, params: list[Any], affinity_types: list[str] | None,
                        max_value_nm: float | None, best_per: str | None, limit: int,
                        min_value_nm: float | None = None, with_smiles: bool = False,
                        props: PropertyFilter | None = None, efficiency: bool = False,
                        order_by: OrderBy = "potency") -> dict[str, Any]:
        """Measurements matching `where` and the filters, most potent first (or by order_by); `efficiency`
        adds ligand_efficiency, lipe and pains_alerts when the database has compound properties."""
        pf, pparams, source = measurement_filter(affinity_types, max_value_nm, min_value_nm, props)
        efficiency = efficiency and has_properties
        cols = ACTIVITY_COLUMNS + (EFFICIENCY_COLUMNS if efficiency else "")
        source = ACTIVITY_WITH_PROPERTIES if efficiency else source
        order = "(relation = '>'), p_affinity DESC NULLS LAST, value, ki_result_id"
        ranked = order if order_by == "potency" else f"{order_by} DESC NULLS LAST, {order}"
        if best_per:
            sql = f"""
                SELECT {cols}, count(*) OVER w AS n_measurements
                FROM {source} WHERE {where} AND {pf}
                WINDOW w AS (PARTITION BY {best_per})
                QUALIFY row_number() OVER (PARTITION BY {best_per} ORDER BY {order}) = 1
                ORDER BY {ranked}"""
        else:
            sql = f"SELECT {cols} FROM {source} WHERE {where} AND {pf} ORDER BY {ranked}"
        if with_smiles:  # structure searches: the compounds' structures, e.g. for draw_structure_grid
            sql = f"SELECT q.*, c.smiles FROM ({sql}) q LEFT JOIN compound c USING (monomerid) ORDER BY {ranked}"
        return run(sql, [*params, *pparams], limit)

    @mcp.tool(annotations=READ_ONLY)
    def get_activity(
        ki_result_id: Annotated[int, Field(description="Measurement id (ki_result_id) from another tool")],
    ) -> dict[str, Any]:
        """Full record for one measurement: all values and uncertainties, conditions, assay description,
        compound, target, entry and publication/patent details."""
        try:
            k = db.one("SELECT * FROM ki_result WHERE ki_result_id = ?", [ki_result_id])
            if k is None:
                raise ToolError(f"No measurement with ki_result_id {ki_result_id}")
            measurement = {key: v for key, v in k.items() if v is not None}
            reactants = db.one(
                """SELECT r.enzyme AS target_label, r.inhibitor AS ligand_label, r.substrate, r.e_prep, r.i_prep,
                          r.s_prep, a.monomerid, a.compound_name, a.inchi_key, a.polymerid, a.complexid,
                          a.target_name, a.uniprot_raw, a.organism
                   FROM enzyme_reactant_set r
                   JOIN (SELECT * FROM activity WHERE ki_result_id = ? LIMIT 1) a USING (reactant_set_id)""",
                [ki_result_id],
            )
            assay = db.one("SELECT assay_name, description FROM assay WHERE entryid = ? AND assayid = ?",
                           [k["entryid"], k.get("assayid")])
            entry = db.one("SELECT entryid, entrytitle, meas_tech, entrydate, ezid FROM entry WHERE entryid = ?",
                           [k["entryid"]])
            articles = db.rows(
                """SELECT ar.articleid, ec.art_purp, ar.title, j.jour_name AS journal, ar.year, ar.volume,
                          ar.firstpage, ar.pmid AS source_id, ar.doi,
                          (SELECT string_agg(trim(coalesce(firstname, '') || ' ' || coalesce(lastname, '')), ', '
                                             ORDER BY auth_seq)
                           FROM art_aut au WHERE au.articleid = ar.articleid) AS authors
                   FROM entry_citation ec JOIN article ar USING (articleid)
                   LEFT JOIN journal j USING (journalid)
                   WHERE ec.entryid = ?""",
                [k["entryid"]],
            )
        except QueryError as e:
            raise ToolError(str(e)) from None
        return {"measurement": measurement, "reactants": reactants, "assay": assay, "entry": entry,
                "citations": articles}

    @mcp.tool(annotations=READ_ONLY)
    def describe_tables(
        table: Annotated[str | None, Field(description="Table name for its columns; omit to list tables")] = None,
    ) -> dict[str, Any]:
        """List tables with descriptions and row counts, or the columns and types of one table.
        Use before writing run_sql queries."""
        try:
            if table is None:
                tables = db.rows(
                    "SELECT table_name, estimated_size AS approx_rows, column_count FROM duckdb_tables() "
                    "WHERE database_name = current_database() AND NOT temporary ORDER BY table_name",
                    limit=200,
                )
                for t in tables:
                    t["description"] = TABLE_DOCS.get(t["table_name"], "")
                return {"tables": tables, "tip": "Prefer the derived tables (activity, compound, target, "
                        "compound_name, target_name); raw tables mirror the BindingDB MySQL schema."}
            cols = db.rows(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                "WHERE table_name = ? ORDER BY ordinal_position",
                [table],
                limit=200,
            )
            if not cols:
                raise ToolError(f"Unknown table {table!r}; call describe_tables without arguments")
            sample = db.rows(f'SELECT * FROM "{table}" LIMIT 3', limit=3)
        except QueryError as e:
            raise ToolError(str(e)) from None
        return {"table": table, "description": TABLE_DOCS.get(table, ""), "columns": cols, "sample_rows": sample}

    @mcp.tool(annotations=READ_ONLY)
    def run_sql(
        sql: Annotated[str, Field(description="A DuckDB SQL query (read-only; file and network access disabled)")],
        limit: Annotated[int, Field(description="Max rows returned (1-1000)")] = 200,
    ) -> dict[str, Any]:
        """Run a read-only DuckDB SQL query against BindingDB and return up to `limit` rows.

        Text comparisons are case-sensitive: use ILIKE or lower(). Queries time out after 30 s.
        Prefer aggregating in SQL over fetching many rows."""
        return run(sql, None, _clamp(limit, 1, 1000))

    if index is not None:
        _add_structure_tools(mcp, db, index, run, _activity_query, measurement_filter)
    if substructure.rdkit_available():
        _add_exact_search(mcp, db, run, _activity_query, "inchi_keys" in info)
    if sar.available():
        _add_sar_tools(mcp, db, property_filter)
    add_editor_results_tool(mcp, editor_searches)
    _add_transcript_tools(mcp, info.get("release", "unknown"), transcript_dir or db.path.parent / "transcripts")
    return mcp


def _add_transcript_tools(mcp: BindingDBServer, release: str, transcript_dir: Path) -> None:
    figures_dir = transcript_dir / "figures"
    writes = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
    replaces = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)  # same-name files

    def destination(output_dir: str | None, file_name: str | None, title: str, ext: str) -> Path:
        """Where to write a transcript: <output_dir>/<file_name or the title's slug><ext>, or else a
        time-stamped file in transcript_dir."""
        if not output_dir:
            return transcript_dir / f"{_slug(title)}-{datetime.now():%Y-%m-%d-%H%M%S}{ext}"
        folder = Path(output_dir).expanduser()
        if not folder.is_absolute():
            raise ToolError(f"output_dir must be an absolute path (or start with ~), not {output_dir!r}")
        stem = Path(file_name).name if file_name else _slug(title)
        stem = stem[:-len(Path(stem).suffix)] if Path(stem).suffix.lower() in (".md", ".html", ".htm") else stem
        if not stem.strip(" ."):
            raise ToolError(f"file_name {file_name!r} is not a usable file name")
        return folder / f"{stem}{ext}"

    def write(path: Path, text: str) -> str:
        """Write a transcript file; returns ' (replaced an existing file)' if there was one."""
        existed = path.exists()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except OSError as e:
            raise ToolError(f"Could not write {path}: {e.strerror or e}") from None
        return " (replaced an existing file)" if existed else ""

    def copy_figures(copies: dict[str, figures.Figure], folder: Path, stem: str) -> None:
        """Write the figures of a Markdown transcript <stem>.md into folder/figures/ under the names its
        links use (<stem>-figure-<n><ext>), and remove copies of figures it no longer has."""
        target = folder / "figures"
        try:
            target.mkdir(parents=True, exist_ok=True)
            for name, figure in copies.items():
                (target / name).write_bytes(figure.data)
            ours = re.compile(re.escape(stem) + r"-figure-\d+(" + "|".join(map(re.escape, figures.IMAGE_TYPES)) + ")")
            for old in target.iterdir():
                if ours.fullmatch(old.name) and old.name not in copies:
                    old.unlink()
        except OSError as e:
            raise ToolError(f"Could not write the figures to {target}: {e.strerror or e}") from None
        mcp.figure_copies.update(copies)

    @mcp.tool(annotations=writes)
    def reset_tool_log() -> dict[str, Any]:
        """Clear the log of tool calls and figures that create_transcript reports. Call at the start of a
        new analysis, so the transcript holds only its calls."""
        calls, figs = mcp.tool_log.reset()
        return {"cleared": calls, "figures_cleared": figs}

    @mcp.tool(annotations=READ_ONLY)
    def get_tool_log() -> dict[str, Any]:
        """List the logged tool calls (index, UTC time, tool and arguments; no results) and figures (id,
        time, title), oldest first.

        The log is shared by every chat this server process has served (Claude Desktop runs one process
        for all chats), so it can hold calls from other chats. Pick the indices of the calls you made in
        this chat and pass them to create_transcript as `calls`, and your figures' ids in `exchanges`."""
        return {"calls": mcp.tool_log.listing(),
                "figures": [{"id": f.id, "timestamp": f.timestamp, "title": f.title} for f in mcp.tool_log.figures]}

    def find_figure(file: str, folder: Path | None = None) -> transcript_html.Figure | None:
        """A figure by its file name: from the log or the copies in output folders, or else its image from
        the server's figures folder or folder/figures/."""
        figure = next((f for f in mcp.tool_log.figures if f.file == file), None) or mcp.figure_copies.get(file)
        if figure is not None:
            return transcript_html.Figure(figure.html, [c["smiles"] for c in figure.spec.get("compounds", [])])
        name = Path(file).name
        path = next((p for d in (figures_dir, folder and folder / "figures") if d and (p := d / name).is_file()), None)
        if path is None or path.suffix not in figures.IMAGE_TYPES:
            return None
        data = path.read_bytes()
        return transcript_html.Figure(figures.image_html(path.stem, data, path.suffix),
                                      figures.png_smiles(data) if path.suffix == ".png" else [])

    def log_figure(title: str, data: bytes, ext: str, html_block: str, spec: dict[str, Any],
                   caption: str | None = None) -> tuple[figures.Figure, str]:
        """Log a figure with the next id and save its image in figures/; returns it and where it was saved."""
        log = mcp.tool_log
        figure_id, log.next_figure_id = log.next_figure_id, log.next_figure_id + 1
        file = f"{_slug(title)}-{datetime.now():%Y-%m-%d-%H%M%S}-{figure_id}{ext}"
        try:
            figures_dir.mkdir(parents=True, exist_ok=True)
            (figures_dir / file).write_bytes(data)
            saved = f"Saved as {figures_dir / file}."
        except OSError as e:
            saved = f"Could not save the image in {figures_dir}: {e}; HTML transcripts still include it."
        figure = figures.Figure(id=figure_id, timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                title=title, file=file, html=html_block, data=data, spec=spec, caption=caption)
        log.figures.append(figure)
        return figure, saved

    @mcp.tool(annotations=writes)
    def add_figure(
        title: Annotated[str, Field(description="Figure title, e.g. 'Kinase selectivity heat map'")],
        path: Annotated[str | None, Field(description="The image file (PNG, JPEG, GIF, WebP or SVG) on the "
                                          "machine running this server, e.g. a plot you saved")] = None,
        data: Annotated[str | None, Field(description="The image itself, base64-encoded, only when the server "
                                          "cannot read the file (e.g. it was made in a sandbox elsewhere)")] = None,
        caption: Annotated[str, Field(description="A sentence or two under the figure: what it shows")] = "",
    ) -> str:
        """Add an image made with other tools (e.g. a matplotlib plot) as a figure for transcripts, which
        include only figures in this server's log. Returns its id: list it in the `figures` of the
        exchange it belongs to in create_transcript. HTML transcripts embed the image; Markdown transcripts
        link to the copy the server keeps in its figures/ folder. Never add images to a transcript, or edit
        its files, yourself.

        Pass `path` when the file is on the machine running this server; `data` puts the whole image
        through the chat, so use it only when there is no such path. Structure grids are drawn with
        draw_structure_grid instead."""
        if (path is None) == (data is None):
            raise ToolError("Give either path or data")
        if path is not None:
            source = Path(path).expanduser()
            try:
                if source.stat().st_size > figures.MAX_IMAGE_BYTES:
                    raise ToolError(f"{source} is larger than {figures.MAX_IMAGE_BYTES:,} bytes")
                content = source.read_bytes()
            except OSError as e:
                raise ToolError(f"Cannot read {source} on the machine running mcp-bindingdb ({e.strerror}); "
                                "if the image was made elsewhere, pass it as `data` (base64)") from None
        else:
            encoded = data.split(",", 1)[1] if data.startswith("data:") else data
            try:
                content = base64.b64decode(encoded, validate=True)
            except ValueError:
                raise ToolError("data is not valid base64") from None
            if len(content) > figures.MAX_IMAGE_BYTES:
                raise ToolError(f"The image is larger than {figures.MAX_IMAGE_BYTES:,} bytes")
        ext = figures.image_type(content)
        if ext is None:
            raise ToolError(f"{'The data' if path is None else source} is not a PNG, JPEG, GIF, WebP or SVG image")
        figure, saved = log_figure(title, content, ext, figures.image_html(title, content, ext),
                                   {"source": str(source) if path is not None else "data"}, caption.strip())
        return "\n".join([f"Figure id {figure.id}: '{title}' ({ext[1:].upper()}, {len(content):,} bytes).", saved,
                          FIGURE_ID_NOTE.format(id=figure.id)])

    def write_html(source: str, output_dir: str | None = None, file_name: str | None = None) -> list[Any]:
        """Convert a Markdown transcript to HTML, write it (to output_dir, else transcript_dir), and
        summarize the result."""
        title = next((line[2:].strip() for line in source.splitlines() if line.startswith("# ")), "transcript")
        path = destination(output_dir, file_name, title, ".html")
        page, drawn, n_figures = transcript_html.markdown_to_html(source, lambda f: find_figure(f, path.parent))
        mcp.last_html = page
        try:
            replaced = write(path, page)
        except ToolError as e:
            raise ToolError(f"{e}; the page is still available at {LATEST_HTML_URI}") from None
        header = [line for line in source.splitlines() if line.startswith(("- **Date:**", "- **Contents:**"))]
        parts = [transcript.plural(n_figures, "figure")] if n_figures else []
        parts.append(f"{transcript.plural(drawn, 'structure')} drawn in tables" if drawn else "no table structures")
        summary = [
            f"HTML transcript of '{title}' written ({len(page):,} bytes; {', '.join(parts)})."
            + ("" if depict.available() else " RDKit is not installed on the server."),
            *header,
            f"- File: {path}{replaced} (on the machine running mcp-bindingdb)",
            f"- Resource: {LATEST_HTML_URI} (fetch it from there when the server runs remotely)",
            "Deliver this file as is; do not write, edit or copy an HTML transcript yourself"
            + ("." if output_dir else " (pass output_dir to have it written where the user wants it)."),
        ]
        return [TextContent(type="text", text="\n".join(summary)),
                ResourceLink(type="resource_link", name=path.name, title=title, uri=LATEST_HTML_URI,
                             mimeType="text/html", size=len(page.encode()))]

    if depict.available():
        @mcp.tool(annotations=writes, meta=FIGURE_META)
        def draw_structure_grid(
            title: Annotated[str, Field(description="Figure heading")],
            compounds: Annotated[list[figures.GridCompound], Field(min_length=1, max_length=24,
                                                                   description="The compounds, in grid order")],
            align_to: Annotated[str | None, Field(description="SMILES or SMARTS of the shared core to align "
                                                  "on and highlight, e.g. 'Nc1ccc(Cl)cc1'; its first atom is "
                                                  "drawn on the left. Default: the compounds' largest common "
                                                  "substructure")] = None,
            columns: Annotated[int, Field(ge=1, le=6, description="Compounds per row")] = 3,
            description: Annotated[str, Field(description="A sentence or two under the heading")] = "",
            notes: Annotated[list[str] | None, Field(description="Short notes under the figure, e.g. "
                                                     "caveats about the data")] = None,
        ) -> CallToolResult:
            """Draw compounds side by side in a grid, aligned on a shared core that is highlighted, each with
            a name, subtitle, caption and bars for its binding to its main targets (log scale, coloured by
            Ki/Kd/IC50/EC50).

            Use it whenever you show several compounds' structures together (e.g. "show them in a grid,
            aligned by the substructure"), instead of drawing them yourself. The image is shown in the chat,
            and transcripts include it: list its id in the `figures` of the exchange it belongs to. HTML
            transcripts embed it; Markdown transcripts link to its PNG.

            The figure is the answer's display of these compounds: refer to it ("the figure below") rather than
            repeating it. Do not also give a table of the same compounds' SMILES or of the values the bars
            show; add a table only for data the figure lacks (e.g. other targets or measurement types)."""
            if align_to and depict.parse(align_to) is None:
                raise ToolError(f"align_to {align_to!r} is not valid SMILES or SMARTS")
            block, png, lay = figures.structure_grid(title, compounds, align_to, columns, description, notes)
            figure, saved = log_figure(title, png, ".png", block, {"compounds": [c.model_dump() for c in compounds],
                                                                   "align_to": align_to})
            if any(lay.cores):
                alignment = f"aligned on {align_to}" if align_to else "aligned on their largest common substructure"
            elif align_to:
                alignment = f"not aligned: no compound contains {align_to}"
            else:
                alignment = "not aligned: they share no core of 6 or more atoms"
            bad = [c.title for c, mol in zip(compounds, lay.mols) if mol is None]
            text = [f"Figure id {figure.id}: '{title}', {transcript.plural(len(compounds), 'compound')}, {alignment}.",
                    *([f"Not drawn (SMILES not understood): {', '.join(bad)}."] if bad else []),
                    saved,
                    FIGURE_ID_NOTE.format(id=figure.id),
                    "The user sees this image: in your answer, refer to it instead of repeating its structures "
                    "or values in tables."]
            # The figure panel shows the saved file: hosts may strip the image from the result they give it.
            saved_file = figure.file if (figures_dir / figure.file).is_file() else None
            return CallToolResult(
                content=[ImageContent(type="image", data=base64.b64encode(png).decode(), mimeType="image/png"),
                         TextContent(type="text", text="\n".join(text))],
                structured_content={"figure_id": figure.id, "figure_file": saved_file})

        @mcp.tool(annotations=writes, meta=FIGURE_META)
        def draw_r_group_table(
            title: Annotated[str, Field(description="Figure heading, e.g. '4-anilinoquinazolines at EGFR'")],
            core: Annotated[str, Field(description="The series' core with its positions marked, e.g. "
                                       "'[*:1]Nc1ccc2ncnc(N[*:2])c2c1' — normally the `matched_core` "
                                       "decompose_r_groups returned. It is drawn once above the table with "
                                       "each [*:n] named Rn")],
            rows: Annotated[list[figures.RGroupRow], Field(min_length=1, max_length=30,
                                                           description="One per compound, in table order")],
            description: Annotated[str, Field(description="A sentence or two under the heading")] = "",
            column_notes: Annotated[dict[str, str] | None, Field(description="A short note under a column "
                                                                 "heading, e.g. {'R1': 'N1', 'R3': 'C8'} to "
                                                                 "name the position on the core")] = None,
            notes: Annotated[list[str] | None, Field(description="Short notes under the figure, e.g. "
                                                     "caveats about the data")] = None,
            core_caption: Annotated[str, Field(description="The sentence beside the core. Default: that "
                                               "its named positions are the columns and the rest is the "
                                               "same in every row — replace it when that is not true, "
                                               "e.g. for one row per substituent at one position")] = "",
            row_heading: Annotated[str, Field(description="Heading of the first column, e.g. 'Compound' "
                                              "(default) or 'Group' for a row per substituent")] = "Compound",
        ) -> CallToolResult:
            """Draw an R-group table of one chemical series: the core at the top with its positions named
            R1, R2, ..., then a row per compound whose cells are the substituents themselves, drawn, with
            bars for its potency.

            This is how a series from decompose_r_groups is shown. Never write the substituents' SMILES in
            a table or in your answer: the table draws them, and in prose you name a group ('a propyl at
            N1', 'the 8-cyclopentyl'). The image is shown in the chat, and transcripts include it: list its
            id in the `figures` of the exchange it belongs to.

            The figure is the answer's display of this series: refer to it ('the table below') instead of
            repeating its groups or values."""
            if depict.parse(core) is None:
                raise ToolError(f"core {core!r} is not valid SMILES or SMARTS")
            block, png, labels, undrawn = figures.r_group_table(title, core, rows, description,
                                                               column_notes, notes, core_caption,
                                                               row_heading)
            if not labels:
                raise ToolError("No row has an R-group: give each row's substituents as "
                                "r_groups, e.g. {'R1': 'CCC[*:1]', 'R2': 'H'}")
            figure, saved = log_figure(title, png, ".png", block,
                                       {"core": core, "rows": [r.model_dump() for r in rows]})
            text = [f"Figure id {figure.id}: '{title}', {transcript.plural(len(rows), 'compound')} over "
                    f"{', '.join(labels)}.",
                    *([f"Not drawn (not understood as a substituent): {', '.join(undrawn)}."]
                      if undrawn else []),
                    saved,
                    FIGURE_ID_NOTE.format(id=figure.id),
                    "The user sees this image: in your answer, refer to it instead of listing the "
                    "substituents or their SMILES."]
            saved_file = figure.file if (figures_dir / figure.file).is_file() else None
            return CallToolResult(
                content=[ImageContent(type="image", data=base64.b64encode(png).decode(), mimeType="image/png"),
                         TextContent(type="text", text="\n".join(text))],
                structured_content={"figure_id": figure.id, "figure_file": saved_file})

        @mcp.tool(annotations=READ_ONLY, meta={"ui": {**FIGURE_META["ui"], "visibility": ["app"]}})
        def figure_image(file: str) -> dict[str, Any]:
            """For the figure panel: a saved figure's image, by the figure_file draw_structure_grid returned."""
            path = figures_dir / file
            if Path(file).name != file or path.suffix.lower() not in figures.IMAGE_TYPES or not path.is_file():
                raise ToolError(f"No saved figure {file!r}")
            return {"mime_type": figures.IMAGE_TYPES[path.suffix.lower()],
                    "data": base64.b64encode(path.read_bytes()).decode()}

    @mcp.tool(annotations=replaces)
    def create_transcript(
        model: Annotated[str, Field(description="The exact model id that produced the analysis (e.g. "
                                    "'claude-opus-5-5'), from session metadata or the user; never a family "
                                    "name like 'Claude' or a guess. Ask the user if you do not know it")],
        exchanges: Annotated[list[Exchange] | None, Field(description="The conversation turns, in order: "
                                                         "each prompt with your full, verbatim answer and the "
                                                         "ids of its figures")] = None,
        title: Annotated[str, Field(description="Heading of the transcript")] = "BindingDB Chat Transcript",
        date: Annotated[str | None, Field(description="ISO date of the session (default: today)")] = None,
        include_tool_calls: Annotated[bool, Field(description="Add the BindingDB tool calls with their "
                                                  "results after the conversation. Only when the user's "
                                                  "request asks for them; never on your own judgment, e.g. "
                                                  "because the analysis used run_sql")] = False,
        calls: Annotated[list[int] | None, Field(description="With include_tool_calls: only these, by the "
                                                 "1-based index get_tool_log shows, in log order. Ignored "
                                                 "without include_tool_calls. Default: every logged call")] = None,
        max_result_rows: Annotated[int | None, Field(description="Rows shown per result table, and items per "
                                                     "list; the true counts are kept. null shows all")] = 5,
        skills: Annotated[list[str] | None, Field(description="Agent skills that shaped the analysis, as "
                                                  "'<name> v<version>'; only ones actually followed")] = None,
        external_mcp_servers: Annotated[list[str] | None, Field(description="Other MCP servers this session "
                                                                "actually called for evidence, e.g. "
                                                                "['PubMed']")] = None,
        format: Annotated[Literal["markdown", "html", "json"], Field(
            description="markdown: a document to save. html: a web page with structure drawings, written "
            "to a file by the server. json: the structured fields")] = "markdown",
        output_dir: Annotated[str | None, OUTPUT_DIR_FIELD] = None,
        file_name: Annotated[str | None, FILE_NAME_FIELD] = None,
    ) -> Any:
        """Build a transcript of this session: each user prompt with your answer and its figures. The
        server cannot see your prose, so pass each answer in full via `exchanges`, not a summary.

        Figures appear under the answer whose `figures` lists their ids. If no exchange lists any, every
        logged figure is added in a Figures section. Only logged figures can be included: structure grids
        from draw_structure_grid, and images made with other tools (e.g. matplotlib plots) once added with
        add_figure. Interactive pages or artifacts you built cannot be included.

        Tool calls are left out unless the user asks for them (e.g. "with the tool calls", "with the
        queries and results", "a reproducible record"). Do not add them on your own, not even when the
        analysis is SQL or the queries seem instructive, and do not tell the reader the answer's SQL is
        listed below: when a query matters to the answer, quote it in the answer itself. Only when the user
        asks, set include_tool_calls and the transcript
        adds every BindingDB call that ran (arguments verbatim, SQL for run_sql) with its result. The
        server logs calls as they run (failed calls and describe_tables are not), so do not re-supply
        them. The log is shared by every chat this server process has served, so it can hold calls and
        figures from other chats: list your figures' ids in `exchanges`, and when including tool calls,
        unless reset_tool_log was called at the start of this analysis, call get_tool_log first and pass
        the indices of this chat's calls as `calls`.

        Where the files go: whenever the user has named a folder for the results (or you are writing them
        to one), pass it as `output_dir`; the server writes the transcript there, with the figures a
        Markdown transcript links to in its figures/ subfolder, and replaces a file of the same name. Do
        not copy or rewrite the files yourself.

        Markdown (default): with output_dir, the server writes the .md file. Without it, save the
        returned Markdown verbatim to a .md file (or a Markdown artifact): do not retype, reorder or
        summarize it, and never say the transcript is saved unless you wrote the file; with figures, the
        server also saves the .md next to the figures/ folder its image links point to.

        format='html' whenever the user asks for an HTML transcript: the server builds the same Markdown
        and converts it in this one call (see transcript_to_html), embedding the figures and drawing the
        structures of every table with a SMILES column. The page is too large to pass through the chat,
        so the server writes it to a file (in output_dir, if given) and returns its path; never write an
        HTML transcript yourself."""
        when = date or _date.today().isoformat()
        turns = [e.model_dump() for e in exchanges or []]
        log = mcp.tool_log
        if calls is not None and (bad := [i for i in calls if not 1 <= i <= len(log.entries)]):
            raise ToolError(f"calls {bad} are not in the log, which has {len(log.entries)} calls; "
                            "see get_tool_log")
        if not include_tool_calls:
            selected = []
        elif calls is not None:
            selected = [log.entries[i - 1] for i in sorted(set(calls))]
        else:
            selected = list(log.entries)
        listed = [i for t in turns for i in t["figures"]]
        if missing := sorted({i for i in listed if log.figure(i) is None}):
            raise ToolError(f"figures {missing} are not in the log; it has "
                            f"{[f.id for f in log.figures] or 'none'} (see get_tool_log)")
        placed = [log.figure(i) for i in dict.fromkeys(listed)]
        unplaced = [] if listed else list(log.figures)
        skill_list = transcript.clean_entries(skills)
        server_list = transcript.clean_entries(external_mcp_servers)
        generated_by = f"{mcp.name} v{VERSION}"
        if format == "json":
            out: dict[str, Any] = {"title": title, "date": when, "model": model, "bindingdb_release": release,
                                   "exchanges": turns, "tool_calls": selected, "generated_by": generated_by}
            if placed or unplaced:
                numbers = transcript.figure_numbers(turns, unplaced)
                out["figures"] = [{"number": numbers[f.id], "id": f.id, "timestamp": f.timestamp, "title": f.title,
                                   "file": f.file, **({"caption": f.caption} if f.caption else {}), **f.spec}
                                  for f in placed + unplaced]
            if skill_list:
                out["skills"] = skill_list
            if server_list:
                out["external_mcp_servers"] = server_list
            return out
        copies: dict[str, figures.Figure] = {}  # Markdown in an output_dir: figures named after the transcript
        if format == "markdown" and output_dir:
            path = destination(output_dir, file_name, title, ".md")
            by_id = {f.id: f for f in placed + unplaced}
            copies = {f"{path.stem}-figure-{n}{Path(by_id[i].file).suffix}": by_id[i]
                      for i, n in transcript.figure_numbers(turns, unplaced).items()}
        mcp.last_markdown = transcript.render_transcript(
            title=title, when=when, model=model, release=release, generated_by=generated_by, exchanges=turns,
            calls=selected, max_rows=None if max_result_rows is None else max(max_result_rows, 0),
            skills=skill_list, mcp_servers=server_list, figures=placed, unplaced_figures=unplaced,
            figure_files={f.id: name for name, f in copies.items()})
        if format == "html":
            return write_html(mcp.last_markdown, output_dir, file_name)
        if output_dir:
            replaced = write(path, mcp.last_markdown)
            copy_figures(copies, path.parent, path.stem)
            note = (f"Saved as {path}{replaced}"
                    + (f", with its {transcript.plural(len(copies), 'figure')} in {path.parent / 'figures'}"
                       if copies else "")
                    + ". Deliver this file as is; do not rewrite or copy it.")
            return [TextContent(type="text", text=mcp.last_markdown), TextContent(type="text", text=note)]
        if not (placed or unplaced):
            return mcp.last_markdown
        path = destination(None, None, title, ".md")
        try:
            path.write_text(mcp.last_markdown, encoding="utf-8")
            note = (f"This transcript is also saved as {path}, next to the figures/ folder its image links "
                    "point to; a copy saved elsewhere shows the figures only if that folder is copied along.")
        except OSError as e:
            note = f"Could not save the transcript next to its figures in {transcript_dir}: {e}."
        return [TextContent(type="text", text=mcp.last_markdown), TextContent(type="text", text=note)]

    @mcp.tool(annotations=replaces)
    def transcript_to_html(
        markdown: Annotated[str | None, Field(description="A transcript's Markdown, e.g. one the user edited "
                                              "or one from an earlier session. Default: the transcript the "
                                              "last create_transcript call returned")] = None,
        output_dir: Annotated[str | None, OUTPUT_DIR_FIELD] = None,
        file_name: Annotated[str | None, FILE_NAME_FIELD] = None,
    ) -> Any:
        """Convert a Markdown transcript into a standalone HTML page with its figures embedded and structure
        drawings: every table with a SMILES column, in the answers as well as in the tool calls, gets a
        structure column, aligned on the molecules' shared core.

        For a new HTML transcript, call create_transcript with format='html' instead; use this tool to
        convert a Markdown transcript the user already has (the last one, or one passed in). The page
        holds the drawings, so it is too large to pass through the chat: the server writes it to a file
        (in output_dir: pass the folder the user wants it in) and returns its path and a link to the
        resource transcript://session/latest.html. Check the title and contents in the summary, then give
        the user the path; never write, edit or copy an HTML transcript yourself."""
        source = markdown if markdown is not None else mcp.last_markdown
        if not source or not source.strip():
            raise ToolError("No transcript to convert: call create_transcript first, or pass `markdown`")
        return write_html(source, output_dir, file_name)

    @mcp.resource(LATEST_HTML_URI, name="Latest HTML transcript", mime_type="text/html",
                  description="The most recent HTML transcript, with its figures and structure drawings.")
    def latest_html_transcript() -> str:
        return mcp.last_html or ("<!doctype html><title>No transcript yet</title><p>Call "
                                 "<code>create_transcript</code> with <code>format='html'</code> first.</p>")


def _slug(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-").lower()[:60] or "transcript"


def _add_exact_search(mcp: MCPServer, db: Database, run, activity_query, computed_keys: bool) -> None:
    @mcp.tool(annotations=READ_ONLY)
    def exact_structure_search(
        smiles: Annotated[str, Field(description="The whole molecule as SMILES, including any salt or solvent")],
        affinity_types: Annotated[list[AffinityType] | None, AFFINITY_TYPES_FIELD] = None,
        max_value_nm: Annotated[float | None, MAX_VALUE_FIELD] = None,
        min_value_nm: Annotated[float | None, MIN_VALUE_FIELD] = None,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Find the BindingDB compounds that are the same molecule as the query.

        Same molecule means the same canonical isomeric SMILES: all fragments (salts), stereo, charges and
        isotopes must match, and tautomers or protonation states count as different (similarity_search
        with threshold 1.0 ignores stereo and salts). Default: the matches with their measurement counts.
        With affinity filters: only matches with a measurement that passes them, each with its most potent
        such measurement and its SMILES. Needs RDKit but not the structure-search index."""
        _check_range(min_value_nm, max_value_nm)
        try:
            mol = substructure.parse_molecule(smiles)
        except substructure.QueryParseError as e:
            raise ToolError(str(e)) from None
        if any(a.GetAtomicNum() == 0 for a in mol.GetAtoms()):
            raise ToolError("Give a whole molecule; use substructure_search for queries with '*'")
        key = substructure.Chem.MolToInchiKey(mol)
        if not key:
            raise ToolError("RDKit cannot make an InChIKey for this molecule; try similarity_search with "
                            "threshold 1.0")
        want = substructure.Chem.MolToSmiles(mol)
        about = {"input": smiles, "canonical": want, "inchi_key": key,
                 "match": "same canonical isomeric SMILES (salts, stereo, charges and isotopes included)"}
        limit = _clamp(limit, 1, 500)
        # Same molecule implies the same InChIKey connectivity block; tautomers and stereoisomers share it too.
        candidates = run("SELECT monomerid, smiles FROM compound WHERE inchi_key LIKE ?", [key[:14] + "-%"],
                         10_000)["rows"]
        ids = [r["monomerid"] for r in candidates if substructure.canonical_smiles(r["smiles"] or "") == want]
        filtered = affinity_types is not None or max_value_nm is not None or bool(min_value_nm)
        result: dict[str, Any] = {"row_count": 0, "truncated": False, "rows": []}
        if ids and not filtered:
            result = run(
                """SELECT monomerid, bdbm_id, name, smiles, mol_weight, n_activities, n_targets
                   FROM compound WHERE monomerid IN (SELECT unnest(?))
                   ORDER BY n_activities DESC, monomerid""",
                [ids],
                limit,
            )
        elif ids:
            result = activity_query("monomerid IN (SELECT unnest(?))", [ids], affinity_types, max_value_nm,
                                    "monomerid", limit, min_value_nm, with_smiles=True)
        out = {"query": about, **result, "n_exact_matches": len(ids)}
        if not computed_keys:
            out["note"] = ("This database has BindingDB's own InChIKeys, which are missing or non-standard for "
                           "many compounds, so matches can be missed; run scripts/compute_inchikeys.py on it")
        return out


def _add_sar_tools(mcp: MCPServer, db: Database, property_filter) -> None:
    """SAR over one target's ligands: decompose_r_groups, matched_molecular_pairs, activity_cliffs.

    All three read the same ligand set: one row per compound with its most potent exact measurement of a
    single affinity type, so that a difference between two compounds is a difference in chemistry and
    not in assay. Only RDKit is needed, not the substructure index.
    """

    def affinity_type_for(where: str, params: list[Any], affinity_type: str | None) -> str:
        """The requested affinity type, or the one the target has most exact measurements of."""
        if affinity_type is not None:
            return affinity_type
        row = db.one(f"""SELECT affinity_type FROM activity
                         WHERE {where} AND {EXACT_MEASUREMENT} AND affinity_type IN (SELECT unnest(?))
                         GROUP BY affinity_type ORDER BY count(*) DESC, affinity_type""",
                     [*params, POTENCY_TYPES])
        if row is None:
            raise ToolError("That target has no exact ('=') Ki, Kd, IC50 or EC50 measurement in nM, so "
                            "there is nothing to compare; find_ligands_for_target shows what it does have")
        return row["affinity_type"]

    def ligand_set(where: str, params: list[Any], affinity_type: str, max_value_nm: float | None,
                   props: PropertyFilter | None, max_compounds: int) -> tuple[list[dict[str, Any]], bool]:
        """(compounds, whether max_compounds cut the set off), most potent first, with their structures."""
        prf, prparams = property_filter(props)
        source = "activity JOIN compound USING (monomerid)"
        if prf:
            source += " LEFT JOIN compound_property cp USING (monomerid)"
        clauses = [where, "affinity_type = ?", EXACT_MEASUREMENT, "smiles IS NOT NULL"]
        values: list[Any] = [*params, affinity_type, *prparams]
        if prf:
            clauses.append(prf)
        if max_value_nm is not None:
            clauses.append("value <= ?")
            values.append(max_value_nm)
        try:
            result = db.query(
                f"""SELECT monomerid, any_value(compound_name) AS compound_name, any_value(smiles) AS smiles,
                           round(max(p_affinity), 2) AS p_affinity, min(value) AS value_nm,
                           count(*) AS n_measurements
                    FROM {source} WHERE {' AND '.join(clauses)}
                    GROUP BY monomerid ORDER BY p_affinity DESC, monomerid""",
                values,
                max_compounds,
            )
        except QueryError as e:
            raise ToolError(str(e)) from None
        if not result.rows:
            raise ToolError(f"No compound has an exact {affinity_type} value in nM against that target "
                            "under these filters")
        return result.rows, result.truncated

    def scanned_note(compounds: list[dict[str, Any]], truncated: bool, what: str) -> str | None:
        if not truncated:
            return None
        return (f"Only the {len(compounds):,} most potent compounds were {what}; raise max_compounds to "
                "cover more of the target, at the cost of time.")

    @mcp.tool(annotations=READ_ONLY)
    def decompose_r_groups(
        core: Annotated[str, Field(description="The shared core, as SMILES or SMARTS, e.g. "
                                   "'c1ncnc2ccccc12' (quinazoline) or a scaffold from "
                                   "find_ligands_for_target(group_by_scaffold=True). Mark the positions "
                                   "to tabulate with [*:1], [*:2], ... to decompose only there; without "
                                   "marks every substituted position of the core becomes a column")],
        target_id: TargetIdArg = None,
        uniprot: UniprotArg = None,
        include_variants: IncludeVariantsArg = False,
        target_kind: TargetKindArg = "polymer",
        affinity_type: OneAffinityTypeArg = None,
        max_value_nm: Annotated[float | None, Field(description="Only compounds at least this potent "
                                                    "(nM)")] = None,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        summarize: Annotated[bool, Field(description="Also, per position, the substituents it carries "
                                         "with their potency, over every matching compound")] = True,
        max_compounds: MaxCompoundsArg = 5000,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """An SAR table of one chemical series: the target's ligands that contain `core`, each R-group
        position in its own column (R1, R2, ...), with the compound's potency.

        Show the result with draw_r_group_table, passing `matched_core` and each row's R-group cells: it
        draws the core with its positions named and every substituent as a structure. The substituent
        SMILES in these rows are for that tool and for your own reasoning — do not put them in a table or
        an answer; name the groups instead ('an 8-cyclopentyl'). Rows also carry the compound's `smiles`,
        for draw_structure_grid when whole structures are what you want to show."""
        where, params = _target_where(target_id, uniprot, include_variants, target_kind)
        try:
            query, query_type = substructure.parse_query(core)
        except substructure.QueryParseError as e:
            raise ToolError(str(e)) from None
        affinity_type = affinity_type_for(where, params, affinity_type)
        compounds, truncated = ligand_set(where, params, affinity_type, max_value_nm, properties,
                                          _clamp(max_compounds, 1, 50_000))
        decomposition = sar.decompose(query, sar.molecules([c["smiles"] for c in compounds]))
        rows = [{"monomerid": c["monomerid"], "compound_name": c["compound_name"], **groups,
                 "p_affinity": c["p_affinity"], "value_nm": c["value_nm"],
                 "n_measurements": c["n_measurements"], "smiles": c["smiles"]}
                for c, groups in zip(compounds, decomposition.rows) if groups is not None]
        limit = _clamp(limit, 1, 500)
        notes = [scanned_note(compounds, truncated, "decomposed")]
        if len(decomposition.labels) > 4 and not sar.has_attachment_points(query):
            notes.append(f"The core leaves {len(decomposition.labels)} substitutable positions, so the "
                         "table has that many columns, and a fused ring can fill two of them. Marking the "
                         "positions you care about ([*:1], [*:2], ...) gives a table of just those.")
        if not rows:
            marked = sar.has_attachment_points(query)
            notes.append(f"The core matches none of the {len(compounds):,} compounds. " + (
                "It marks its attachment points, so a compound substituted at any other position of the "
                "core does not match; drop the [*:n] marks to allow that."
                if marked else "substructure_search with this query and target_id shows whether any "
                "compound contains it at all."))
        out = {"core": {"query": core, "query_type": query_type, "matched_core": decomposition.core},
               "affinity_type": affinity_type, "r_groups": decomposition.labels,
               "n_compounds_scanned": len(compounds), "n_compounds_matched": len(rows),
               "row_count": min(len(rows), limit), "truncated": len(rows) > limit, "rows": rows[:limit]}
        if summarize and rows:
            out["r_group_summary"] = {
                label: _substituent_stats(rows, label) for label in decomposition.labels}
        return _with_notes(out, notes)

    @mcp.tool(annotations=READ_ONLY)
    def matched_molecular_pairs(
        target_id: TargetIdArg = None,
        uniprot: UniprotArg = None,
        include_variants: IncludeVariantsArg = False,
        target_kind: TargetKindArg = "polymer",
        affinity_type: OneAffinityTypeArg = None,
        max_value_nm: Annotated[float | None, Field(description="Only compounds at least this potent "
                                                    "(nM)")] = None,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        min_delta_p: Annotated[float, Field(ge=0, description="Only pairs whose potency differs by at "
                                            "least this many log units (1 = tenfold)")] = 0.0,
        transformation: Annotated[str | None, Field(description="Only pairs that make this change, as the "
                                                    "two fragment SMILES of a transformation separated by "
                                                    "'>>', e.g. '[H][*:1] >> F[*:1]' for adding a "
                                                    "fluorine; either direction matches")] = None,
        include_hydrogen_changes: Annotated[bool, Field(description="Also pair a compound with its "
                                                        "unsubstituted analogue (H -> F, H -> methyl). "
                                                        "This is the only way an added group shows up; "
                                                        "turning it off is about four times faster")] = True,
        group_by_transformation: Annotated[bool, Field(description="Instead of pairs, one row per "
                                                       "transformation: how often it was made and what it "
                                                       "did to potency, most frequent first")] = False,
        max_variable_atoms: Annotated[int, Field(ge=1, le=30, description="The largest group a "
                                                 "transformation may change, in heavy atoms")] = 13,
        max_compounds: MaxCompoundsArg = 1000,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Pairs of the target's ligands that differ by a single group, with what that change did to
        potency: the evidence for 'what does adding a fluorine do here?'. Each pair reads from the
        smaller group to the larger, so delta_p_affinity is the effect of making that change."""
        where, params = _target_where(target_id, uniprot, include_variants, target_kind)
        affinity_type = affinity_type_for(where, params, affinity_type)
        wanted = _transformation_filter(transformation)
        compounds, truncated = ligand_set(where, params, affinity_type, max_value_nm, properties,
                                          _clamp(max_compounds, 2, 5000))
        mols = sar.molecules([c["smiles"] for c in compounds])
        variants = [[] if mol is None else
                    sar.single_cut_variants(mol, max_variable_atoms, include_hydrogen_changes)
                    for mol in mols]
        pairs, hit_cap = sar.matched_pairs(variants)
        rows = []
        for (i, j), (constant, variable_i, variable_j) in pairs.items():
            a, b = compounds[i], compounds[j]
            from_group, to_group = sar.tidy_fragment(variable_i), sar.tidy_fragment(variable_j)
            if sar.heavy_atoms(from_group) > sar.heavy_atoms(to_group) or (
                    sar.heavy_atoms(from_group) == sar.heavy_atoms(to_group) and from_group > to_group):
                a, b, from_group, to_group = b, a, to_group, from_group
            delta = round(b["p_affinity"] - a["p_affinity"], 2)
            if abs(delta) < min_delta_p or (wanted and {from_group, to_group} != wanted):
                continue
            rows.append({"transformation": f"{from_group} >> {to_group}", "delta_p_affinity": delta,
                         "fold_change": sar.fold_change(delta),
                         "constant_part": sar.tidy_fragment(constant),
                         "monomerid_from": a["monomerid"], "compound_name_from": a["compound_name"],
                         "p_affinity_from": a["p_affinity"], "value_nm_from": a["value_nm"],
                         "monomerid_to": b["monomerid"], "compound_name_to": b["compound_name"],
                         "p_affinity_to": b["p_affinity"], "value_nm_to": b["value_nm"],
                         "smiles_from": a["smiles"], "smiles_to": b["smiles"]})
        rows.sort(key=lambda r: (-abs(r["delta_p_affinity"]), r["monomerid_from"], r["monomerid_to"]))
        limit = _clamp(limit, 1, 500)
        notes = [scanned_note(compounds, truncated, "paired"),
                 f"Pairs were capped at {sar.MAX_PAIRS:,}, so the result is partial." if hit_cap else None,
                 "A pair comes from cutting one acyclic single bond, so it is a change of substituent, "
                 "not of scaffold; fold_change below 1 means the change cost potency." if rows else
                 f"No pair of the {len(compounds):,} compounds differs by a single group under these "
                 "filters; a larger max_compounds or max_variable_atoms finds more."]
        out = {"affinity_type": affinity_type, "n_compounds": len(compounds), "n_pairs": len(rows)}
        if group_by_transformation:
            grouped = _group_transformations(rows, limit)
            return _with_notes({**out, **grouped}, notes)
        return _with_notes({**out, "row_count": min(len(rows), limit), "truncated": len(rows) > limit,
                            "rows": rows[:limit]}, notes)

    @mcp.tool(annotations=READ_ONLY)
    def activity_cliffs(
        target_id: TargetIdArg = None,
        uniprot: UniprotArg = None,
        include_variants: IncludeVariantsArg = False,
        target_kind: TargetKindArg = "polymer",
        affinity_type: OneAffinityTypeArg = None,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        min_similarity: Annotated[float, Field(gt=0, le=1, description="Tanimoto on Morgan fingerprints "
                                               "the two compounds must reach")] = 0.8,
        min_delta_p: Annotated[float, Field(gt=0, description="How far their potency must differ, in log "
                                            "units (1 = tenfold, 2 = hundredfold)")] = 1.5,
        max_compounds: MaxCompoundsArg = 2000,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Activity cliffs: pairs of the target's ligands that are structurally close but differ sharply
        in potency, strongest first by SALI (potency difference per unit of structural distance). A cliff
        is where the SAR is steep — or where one of the two measurements is wrong."""
        where, params = _target_where(target_id, uniprot, include_variants, target_kind)
        affinity_type = affinity_type_for(where, params, affinity_type)
        compounds, truncated = ligand_set(where, params, affinity_type, None, properties,
                                          _clamp(max_compounds, 2, 5000))
        measured = [(c, mol) for c, mol in zip(compounds, sar.molecules([c["smiles"] for c in compounds]))
                    if mol is not None]
        close, hit_cap = sar.similar_pairs([substructure.morgan_fingerprint(mol) for _, mol in measured],
                                           min_similarity)
        rows = []
        for i, j, similarity in close:
            (a, mol_a), (b, mol_b) = measured[i], measured[j]
            if a["p_affinity"] < b["p_affinity"]:
                (a, mol_a), (b, mol_b) = (b, mol_b), (a, mol_a)
            delta = round(a["p_affinity"] - b["p_affinity"], 2)
            if delta < min_delta_p:
                continue
            rows.append({"similarity": similarity, "delta_p_affinity": delta,
                         "fold_change": sar.fold_change(delta), "sali": sar.sali(delta, similarity),
                         "same_structure": similarity == 1.0 and sar.same_molecule(mol_a, mol_b),
                         "monomerid_potent": a["monomerid"], "compound_name_potent": a["compound_name"],
                         "p_affinity_potent": a["p_affinity"], "value_nm_potent": a["value_nm"],
                         "n_measurements_potent": a["n_measurements"],
                         "monomerid_weak": b["monomerid"], "compound_name_weak": b["compound_name"],
                         "p_affinity_weak": b["p_affinity"], "value_nm_weak": b["value_nm"],
                         "n_measurements_weak": b["n_measurements"],
                         "smiles_potent": a["smiles"], "smiles_weak": b["smiles"]})
        rows.sort(key=lambda r: (r["sali"] is not None, -(r["sali"] or 0), -r["delta_p_affinity"]))
        limit = _clamp(limit, 1, 500)
        duplicates = sum(r["same_structure"] for r in rows)
        indistinguishable = sum(r["sali"] is None and not r["same_structure"] for r in rows)
        notes = [scanned_note(compounds, truncated, "compared"),
                 f"Pairs were capped at {sar.MAX_PAIRS:,}, so the result is partial." if hit_cap else None,
                 f"{duplicates} pair(s) are the same structure under two monomerids (same_structure), so "
                 "they are not SAR at all: they are one compound curated twice with different reported "
                 "values." if duplicates else None,
                 f"{indistinguishable} pair(s) have identical fingerprints without being the same "
                 "structure (sali is null, listed first): they differ in stereochemistry or in something "
                 "a Morgan radius-2 fingerprint does not see." if indistinguishable else None,
                 "Check n_measurements before believing a cliff: a single measurement on either side is "
                 "worth looking up with get_activity." if rows else
                 f"No pair among the {len(compounds):,} compounds is this similar and this far apart; "
                 "lower min_similarity or min_delta_p."]
        return _with_notes({"affinity_type": affinity_type, "n_compounds": len(measured),
                            "n_cliffs": len(rows), "row_count": min(len(rows), limit),
                            "truncated": len(rows) > limit, "rows": rows[:limit]}, notes)


def _with_notes(out: dict[str, Any], notes: list[str | None]) -> dict[str, Any]:
    kept = [note for note in notes if note]
    return {**out, "note": " ".join(kept)} if kept else out


def _value_nm(p_affinity: float) -> float:
    """The affinity in nM behind a p_affinity, to three significant figures."""
    return float(f"{10 ** (9 - p_affinity):.3g}")


def _substituent_stats(rows: list[dict[str, Any]], label: str, top: int = 8) -> list[dict[str, Any]]:
    """The substituents at one R-group position, most common first, with their compounds' potency.

    The nM values are there so a position's substituents can go straight into draw_r_group_table, one
    row per substituent with its median or best potency as the bar.
    """
    by_group: dict[str, list[float]] = {}
    for row in rows:
        by_group.setdefault(row[label], []).append(row["p_affinity"])
    ranked = sorted(by_group.items(), key=lambda item: (-len(item[1]), -max(item[1]), item[0]))
    return [{"substituent": group, "n_compounds": len(values), "best_p_affinity": max(values),
             "best_value_nm": _value_nm(max(values)),
             "median_p_affinity": round(statistics.median(values), 2),
             "median_value_nm": _value_nm(statistics.median(values))} for group, values in ranked[:top]]


def _transformation_filter(transformation: str | None) -> set[str] | None:
    """The two fragments of a 'A >> B' transformation, canonical and as a set, so either direction and
    either spelling of a fragment matches."""
    if transformation is None:
        return None
    parts = [part.strip() for part in transformation.split(">>")]
    if len(parts) != 2 or not all(parts):
        raise ToolError(f"transformation {transformation!r} is not two fragment SMILES separated by '>>'")
    if any(sar.Chem.MolFromSmiles(part, sanitize=False) is None for part in parts):
        raise ToolError(f"transformation {transformation!r}: both sides must be fragment SMILES with an "
                        "attachment point, e.g. '[H][*:1] >> F[*:1]'")
    return {sar.tidy_fragment(part) for part in parts}


def _group_transformations(pairs: list[dict[str, Any]], limit: int) -> dict[str, Any]:
    """One row per transformation: how often it was made, and what it did to potency."""
    by_change: dict[str, list[dict[str, Any]]] = {}
    for pair in pairs:
        by_change.setdefault(pair["transformation"], []).append(pair)
    rows = []
    for change, made in by_change.items():
        deltas = [pair["delta_p_affinity"] for pair in made]
        best = max(made, key=lambda pair: pair["delta_p_affinity"])
        rows.append({"transformation": change, "n_pairs": len(made),
                     "median_delta_p_affinity": round(statistics.median(deltas), 2),
                     "min_delta_p_affinity": min(deltas), "max_delta_p_affinity": max(deltas),
                     "n_improved": sum(delta > 0 for delta in deltas),
                     "best_monomerid_from": best["monomerid_from"], "best_monomerid_to": best["monomerid_to"]})
    rows.sort(key=lambda row: (-row["n_pairs"], -row["median_delta_p_affinity"], row["transformation"]))
    return {"grouped_by": "transformation", "n_transformations": len(rows),
            "row_count": min(len(rows), limit), "truncated": len(rows) > limit, "rows": rows[:limit]}


def _add_structure_tools(mcp: MCPServer, db: Database, index: substructure.SubstructureIndex,
                         run, activity_query, measurement_filter) -> None:
    time_limit_s = db.timeout_s * 0.8  # leave time for the SQL that follows the search
    empty: dict[str, Any] = {"row_count": 0, "truncated": False, "rows": []}

    def candidates_for(target_id: int | None, target_kind: str, affinity_types: list[str] | None,
                       max_value_nm: float | None, min_value_nm: float | None,
                       props: PropertyFilter | None) -> tuple[str | None, list[int]]:
        """(id column, monomerids that pass the affinity and property filters), measured against the
        target if one is given; the id column is None without a target."""
        id_col = None if target_id is None else "polymerid" if target_kind == "polymer" else "complexid"
        pf, pparams, source = measurement_filter(affinity_types, max_value_nm, min_value_nm, props)
        where, params = (pf, pparams) if id_col is None else (f"{id_col} = ? AND {pf}", [target_id, *pparams])
        try:
            rows = db.rows(f"SELECT DISTINCT monomerid FROM {source} WHERE {where}", params, limit=10_000_000)
        except QueryError as e:
            raise ToolError(str(e)) from None
        return id_col, [r["monomerid"] for r in rows]

    def no_candidates(about: dict[str, Any], target_id: int | None, target_kind: str) -> dict[str, Any]:
        measured = "" if target_id is None else f" measured against {target_kind} {target_id}"
        return {"query": about, **empty, "compounds_searched": 0, "search_set_size": 0,
                "note": f"No compounds{measured} pass the affinity and property filters"}

    def best_measurements(id_col: str | None, target_id: int | None, monomerids: list[int],
                          affinity_types: list[str] | None, max_value_nm: float | None,
                          min_value_nm: float | None, props: PropertyFilter | None, limit: int) -> dict[str, Any]:
        """The compounds' most potent measurement that passes the filters (against the target, if any)."""
        where, params = "monomerid IN (SELECT unnest(?))", [monomerids]
        if id_col is not None:
            where, params = f"{id_col} = ? AND {where}", [target_id, monomerids]
        return activity_query(where, params, affinity_types, max_value_nm, "monomerid", limit, min_value_nm,
                              with_smiles=True, props=props, efficiency=True)

    def summarize_targets(monomerids: list[int], affinity_types: list[str] | None, max_value_nm: float | None,
                          min_value_nm: float | None, props: PropertyFilter | None, limit: int) -> dict[str, Any]:
        """Targets the compounds were measured against: compounds, measurements, best p_affinity per target."""
        if not monomerids:
            return {"n_targets": 0, "n_compounds_measured": 0, **empty}
        pf, pparams, source = measurement_filter(affinity_types, max_value_nm, min_value_nm, props)
        params = [monomerids, *pparams]
        rows = run(
            f"""SELECT CASE WHEN complexid IS NULL THEN 'polymer' ELSE 'complex' END AS target_kind,
                       coalesce(polymerid, complexid) AS target_id,
                       any_value(target_name) AS target_name, any_value(uniprot_raw) AS uniprot_raw,
                       any_value(organism) AS organism, count(DISTINCT monomerid) AS n_compounds,
                       count(*) AS n_measurements,
                       list(DISTINCT affinity_type ORDER BY affinity_type) AS affinity_types,
                       max(p_affinity) AS best_p_affinity
                FROM {source} WHERE monomerid IN (SELECT unnest(?)) AND {pf}
                GROUP BY polymerid, complexid
                ORDER BY n_compounds DESC, best_p_affinity DESC NULLS LAST, target_kind, target_id""",
            params,
            limit,
        )
        totals = run(
            f"""SELECT count(DISTINCT coalesce(polymerid, -complexid)) AS n_targets,
                       count(DISTINCT monomerid) AS n_compounds_measured
                FROM {source} WHERE monomerid IN (SELECT unnest(?)) AND {pf}""",
            params,
        )["rows"][0]
        return {**totals, **rows}

    def finish(about: dict[str, Any], result: dict[str, Any], searched: int, total: int,
               stopped_early: bool = False) -> dict[str, Any]:
        out = {"query": about, **result, "compounds_searched": searched, "search_set_size": total}
        if searched < total and not stopped_early:
            out["note"] = (f"Time limit reached after {searched:,} of {total:,} compounds; results are partial. "
                           "A more specific query screens faster.")
        return out

    @mcp.tool(annotations=READ_ONLY)
    def substructure_search(
        query: Annotated[str, Field(description="Substructure as SMILES or SMARTS, e.g. 'c1ncnc2ccccc12' "
                                    "(quinazoline) or '[NX3;H2]c1ccccc1' (primary arylamine)")],
        query_type: Annotated[substructure.QueryType, Field(
            description="auto (default): SMILES, falling back to SMARTS when the query has '*', is not valid "
            "SMILES, is written aromatic but is not a valid aromatic molecule, or has a bracket atom without "
            "H such as [#7] (a radical as SMILES). SMILES queries ignore H counts in brackets ([NH2] "
            "matches any amine N); use smarts to enforce them")] = "auto",
        target_id: Annotated[int | None, TARGET_ID_FIELD] = None,
        target_kind: Annotated[Literal["polymer", "complex"], Field(description="Kind of target_id")] = "polymer",
        summarize_by_target: Annotated[bool, Field(description="Instead of compounds, list every target the "
                                                   "matching compounds were measured against, with the number "
                                                   "of compounds per target")] = False,
        affinity_types: Annotated[list[AffinityType] | None, AFFINITY_TYPES_FIELD] = None,
        max_value_nm: Annotated[float | None, MAX_VALUE_FIELD] = None,
        min_value_nm: Annotated[float | None, MIN_VALUE_FIELD] = None,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        use_chirality: Annotated[bool, Field(description="Require stereocentres in the query to match")] = False,
        count_only: Annotated[bool, Field(description="Only count matching compounds (whole database; "
                                          "ignores the target, affinity and property filters)")] = False,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Find compounds that contain a substructure, or the targets they were measured against.

        Default: matching compounds with their measurement counts. If more match than `limit`, the result
        is truncated and favours the compounds with the most measurements; use count_only for the total.
        With affinity or property filters: only compounds with a measurement that passes them (filtered
        before `limit`), each with its most potent such measurement and its SMILES, most potent first. With
        target_id: every compound measured against that target is searched, and the matches are returned
        with their most potent measurement against it, most potent first. With summarize_by_target: all matching
        compounds, grouped by target (compounds, measurements, best p_affinity), most compounds first; use
        max_value_nm (e.g. 10000) to count only compounds that bind."""
        _check_range(min_value_nm, max_value_nm)
        try:
            mol, kind = substructure.parse_query(query, query_type)
        except substructure.QueryParseError as e:
            raise ToolError(str(e)) from None
        chem = substructure.Chem
        about = {"input": query, "interpreted_as": kind,
                 "canonical": chem.MolToSmiles(mol) if kind == "smiles" else chem.MolToSmarts(mol)}
        limit = _clamp(limit, 1, 500)
        filtered = (affinity_types is not None or max_value_nm is not None or bool(min_value_nm)
                    or bool(properties and properties.model_dump(exclude_none=True)))

        if count_only:
            n, searched, total = index.count(mol, time_limit_s, use_chirality)
            out = {"query": about, "n_matching_compounds": n, "compounds_searched": searched,
                   "compounds_indexed": total}
            if searched < total:
                out["note"] = (f"Time limit reached after {searched:,} of {total:,} compounds; the count is a "
                               "lower bound. A more specific query screens faster.")
            return out

        if summarize_by_target:
            if target_id is not None:
                raise ToolError("summarize_by_target lists every target; omit target_id")
            matches = index.search(mol, index.n_compounds, time_limit_s, use_chirality)
            result = {"n_matching_compounds": len(matches.monomerids),
                      **summarize_targets(matches.monomerids, affinity_types, max_value_nm, min_value_nm,
                                          properties, limit)}
        elif target_id is None and not filtered:
            matches = index.search(mol, limit, time_limit_s, use_chirality)
            result = dict(empty)
            if matches.monomerids:
                result = run(
                    """SELECT monomerid, bdbm_id, name, smiles, mol_weight, n_activities, n_targets
                       FROM compound WHERE monomerid IN (SELECT unnest(?))
                       ORDER BY n_activities DESC, monomerid""",
                    [matches.monomerids],
                    limit,
                )
            result["truncated"] = matches.hit_max_results
        else:
            id_col, candidates = candidates_for(target_id, target_kind, affinity_types, max_value_nm, min_value_nm,
                                                properties)
            if not candidates:
                return no_candidates(about, target_id, target_kind)
            # Against one target, search all its compounds so the most potent come first; otherwise take the
            # first `limit` matches among those that pass the filters (most-measured first).
            matches = index.search(mol, len(candidates) if id_col else limit, time_limit_s, use_chirality,
                                   within=candidates)
            result = dict(empty)
            if matches.monomerids:
                result = best_measurements(id_col, target_id, matches.monomerids, affinity_types, max_value_nm,
                                           min_value_nm, properties, limit)
            if id_col:
                result["n_matching_compounds"] = len(matches.monomerids)
            else:
                result["truncated"] = matches.hit_max_results
        return finish(about, result, matches.searched, matches.total, matches.hit_max_results)

    @mcp.tool(annotations=READ_ONLY)
    def similarity_search(
        smiles: Annotated[str, Field(description="Query molecule as SMILES; salts are reduced to the largest "
                                     "fragment")],
        threshold: Annotated[float, Field(ge=0, le=1, description="Minimum Tanimoto similarity (Morgan radius 2, "
                                          "2048 bits). Roughly: 1.0 same structure ignoring stereo and salts, "
                                          ">= 0.7 close analogues, 0.4-0.6 often the same series")] = 0.7,
        target_id: Annotated[int | None, TARGET_ID_FIELD] = None,
        target_kind: Annotated[Literal["polymer", "complex"], Field(description="Kind of target_id")] = "polymer",
        summarize_by_target: Annotated[bool, Field(description="Instead of compounds, list every target the "
                                                   "similar compounds were measured against, with the number "
                                                   "of compounds per target")] = False,
        affinity_types: Annotated[list[AffinityType] | None, AFFINITY_TYPES_FIELD] = None,
        max_value_nm: Annotated[float | None, MAX_VALUE_FIELD] = None,
        min_value_nm: Annotated[float | None, MIN_VALUE_FIELD] = None,
        properties: Annotated[PropertyFilter | None, PROPERTIES_FIELD] = None,
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Find compounds similar to a molecule (Tanimoto on Morgan fingerprints), most similar first.

        Default: similar compounds with their similarity and measurement counts. With affinity or property
        filters: only compounds with a measurement that passes them (filtered before `limit`), each with its
        most potent such measurement and its SMILES. With target_id: only compounds measured against that
        target, each with its most potent measurement against it. With summarize_by_target: all compounds above the
        threshold, grouped by target (compounds, measurements, best p_affinity), most compounds first; use
        max_value_nm (e.g. 10000) to count only compounds that bind."""
        _check_range(min_value_nm, max_value_nm)
        try:
            mol = substructure.parse_molecule(smiles)
        except substructure.QueryParseError as e:
            raise ToolError(str(e)) from None
        about = {"input": smiles, "canonical": substructure.Chem.MolToSmiles(mol), "threshold": threshold,
                 "fingerprint": "Morgan radius 2, 2048 bits, largest fragment"}
        limit = _clamp(limit, 1, 500)
        filtered = (affinity_types is not None or max_value_nm is not None or bool(min_value_nm)
                    or bool(properties and properties.model_dump(exclude_none=True)))

        def similar(within: list[int] | None = None) -> substructure.Similar:
            return index.similar(mol, threshold, time_limit_s, within=within)

        if summarize_by_target:
            if target_id is not None:
                raise ToolError("summarize_by_target lists every target; omit target_id")
            hits = similar()
            result = {"n_similar_compounds": len(hits.monomerids),
                      **summarize_targets(hits.monomerids, affinity_types, max_value_nm, min_value_nm,
                                          properties, limit)}
            return finish(about, result, hits.searched, hits.total)

        if target_id is None and not filtered:
            hits = similar()
        else:
            id_col, candidates = candidates_for(target_id, target_kind, affinity_types, max_value_nm, min_value_nm,
                                                properties)
            if not candidates:
                return no_candidates(about, target_id, target_kind)
            hits = similar(candidates)
        top = hits.monomerids[:limit]
        similarity = dict(zip(top, hits.similarities))
        result = dict(empty)
        if top:
            if target_id is None and not filtered:
                result = run(
                    """SELECT monomerid, bdbm_id, name, smiles, mol_weight, n_activities, n_targets
                       FROM compound WHERE monomerid IN (SELECT unnest(?))""",
                    [top],
                    limit,
                )
            else:
                result = best_measurements(id_col, target_id, top, affinity_types, max_value_nm, min_value_nm,
                                           properties, limit)
            for row in result["rows"]:
                row["similarity"] = similarity[row["monomerid"]]
            result["rows"].sort(key=lambda r: (-r["similarity"], -(r.get("p_affinity") or 0),
                                               -(r.get("n_activities") or 0), r["monomerid"]))
        result["truncated"] = len(hits.monomerids) > limit
        result["n_similar_compounds"] = len(hits.monomerids)
        return finish(about, result, hits.searched, hits.total)


def main() -> None:
    p = argparse.ArgumentParser(prog="mcp-bindingdb", description="BindingDB MCP server")
    p.add_argument("--db", help="DuckDB file (default: $BINDINGDB_DUCKDB or newest data/bindingdb_*.duckdb)")
    p.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--timeout", type=float, default=30.0, help="Per-query time limit in seconds")
    p.add_argument("--no-network", action="store_true",
                   help="Do not look names up in PubChem (chemical_name_to_smiles)")
    p.add_argument("--transcript-dir", default=os.environ.get("MCP_BINDINGDB_TRANSCRIPT_DIR"),
                   help="Where transcripts and figures go unless a call gives output_dir (default: "
                   "$MCP_BINDINGDB_TRANSCRIPT_DIR, else transcripts/ next to the database)")
    args = p.parse_args()

    db = Database(Path(args.db) if args.db else find_database(), timeout_s=args.timeout)
    index = load_substructure_index(db)
    if index is not None:  # loading takes several seconds; start now so the first search does not wait
        threading.Thread(target=index.preload, daemon=True).start()
    server = build_server(db, index, network=not args.no_network,
                          transcript_dir=Path(args.transcript_dir).expanduser() if args.transcript_dir else None)
    if args.transport == "stdio":
        server.run("stdio")
    else:
        server.run("streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
