"""MCP server exposing read-only query tools over a local BindingDB DuckDB build."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from .db import Database, QueryError, find_database

AffinityType = Literal["Ki", "Kd", "IC50", "EC50", "kon", "koff"]
POTENCY_TYPES: list[str] = ["Ki", "Kd", "IC50", "EC50"]

INSTRUCTIONS = """\
BindingDB: ~3.2M measured binding affinities between ~1.5M small molecules ("compounds",
BindingDB monomers, ids shown as BDBM<monomerid>) and ~13k protein targets, curated from
articles, patents, PubChem and ChEMBL.

Workflow: resolve names to ids first (search_compounds / search_targets), then use
find_ligands_for_target, find_targets_for_compound, get_compound, get_target, get_activity.
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

ACTIVITY_COLUMNS = """ki_result_id, affinity_type, relation, value, unit, p_affinity, monomerid,
       compound_name, polymerid, complexid, target_name, uniprot_raw, organism, ph, temp_k,
       assay_name, source_id, doi, year"""


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


def build_server(db: Database) -> MCPServer:
    info = db.build_info()
    mcp = MCPServer(
        name="mcp-bindingdb",
        title="BindingDB",
        version="0.1.0",
        instructions=INSTRUCTIONS + f"\nLoaded release: {info.get('release', 'unknown')}.",
    )

    def run(sql: str, params: list[Any] | None = None, limit: int = 100) -> dict[str, Any]:
        try:
            return db.query(sql, params, limit).as_dict()
        except QueryError as e:
            raise ToolError(str(e)) from None

    def potency_filter(affinity_types: list[str] | None, max_value_nm: float | None) -> tuple[str, list[Any]]:
        types = affinity_types or POTENCY_TYPES
        clauses = ["affinity_type IN (SELECT unnest(?))", "value IS NOT NULL"]
        params: list[Any] = [types]
        if max_value_nm is not None:
            clauses.append("unit = 'nM' AND relation <> '>' AND value <= ?")
            params.append(max_value_nm)
        return " AND ".join(clauses), params

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
        of its most potent measurements (top 25 targets by best p_affinity)."""
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
        except QueryError as e:
            raise ToolError(str(e)) from None
        return {"compound": compound, "synonyms": [s["name"] for s in synonyms], "top_targets": targets}

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
        limit: Annotated[int, Field(description="Max rows (1-500)")] = 50,
    ) -> dict[str, Any]:
        """Compounds measured against a target, most potent first."""
        if (target_id is None) == (uniprot is None):
            raise ToolError("Give exactly one of target_id or uniprot")
        if target_id is not None:
            where, params = ("polymerid = ?" if target_kind == "polymer" else "complexid = ?"), [target_id]
        elif include_variants:
            where, params = "uniprot = ?", [uniprot.strip().upper()]
        else:
            where, params = "uniprot_raw = ?", [uniprot.strip().upper()]
        return _activity_query(where, params, affinity_types, max_value_nm,
                               "monomerid" if best_per_compound else None, _clamp(limit, 1, 500))

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
                        max_value_nm: float | None, best_per: str | None, limit: int) -> dict[str, Any]:
        pf, pparams = potency_filter(affinity_types, max_value_nm)
        order = "(relation = '>'), p_affinity DESC NULLS LAST, value, ki_result_id"
        if best_per:
            sql = f"""
                SELECT {ACTIVITY_COLUMNS}, count(*) OVER w AS n_measurements
                FROM activity WHERE {where} AND {pf}
                WINDOW w AS (PARTITION BY {best_per})
                QUALIFY row_number() OVER (PARTITION BY {best_per} ORDER BY {order}) = 1
                ORDER BY {order}"""
        else:
            sql = f"SELECT {ACTIVITY_COLUMNS} FROM activity WHERE {where} AND {pf} ORDER BY {order}"
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

    return mcp


def main() -> None:
    p = argparse.ArgumentParser(prog="mcp-bindingdb", description="BindingDB MCP server")
    p.add_argument("--db", help="DuckDB file (default: $BINDINGDB_DUCKDB or newest data/bindingdb_*.duckdb)")
    p.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--timeout", type=float, default=30.0, help="Per-query time limit in seconds")
    args = p.parse_args()

    db = Database(Path(args.db) if args.db else find_database(), timeout_s=args.timeout)
    server = build_server(db)
    if args.transport == "stdio":
        server.run("stdio")
    else:
        server.run("streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
