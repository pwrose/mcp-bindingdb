"""MCP App extension for pwrose/mcp-bindingdb. No remote asset host is needed."""

from __future__ import annotations
import gzip
import json
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Literal, Any
from mcp.server.apps import Apps, ResourceCsp, ResourcePermissions
from mcp.types import ToolAnnotations
from mcp.server.mcpserver.exceptions import ToolError

URI = "ui://bindingdb/structure-editor.html"
READ_ONLY = ToolAnnotations(
    readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False
)


def create_editor_extension(network: bool = True) -> Apps:
    apps = Apps()
    bundle_dir = Path(__file__).parent / "assets" / "structure-editor"
    html = gzip.decompress(
        b"".join(part.read_bytes() for part in sorted(bundle_dir.glob("*.gz.part")))
    ).decode("utf-8")
    apps.add_html_resource(
        URI,
        html,
        title="BindingDB Structure Studio",
        prefers_border=True,
        csp=ResourceCsp(resource_domains=["data:", "blob:"]),
        permissions=ResourcePermissions(clipboard_write={}),
    )

    @apps.tool(resource_uri=URI, annotations=READ_ONLY)
    def open_structure_editor(
        initial_query: str = "",
        input_type: Literal["smiles", "smarts", "name"] = "smiles",
        mode: Literal["exact", "substructure", "similarity"] = "exact",
    ) -> dict[str, Any]:
        """Open the interactive chemical editor inside ChatGPT or Claude. Prepare a query, inspect
        its exact representation and affinity range, and explicitly send it to chat. This tool never executes a search.
        In text-only clients, use the returned initial query with the regular BindingDB tools."""
        if len(initial_query) > 20000:
            raise ToolError("Initial query is too long")
        return {
            "initial_query": initial_query,
            "input_type": input_type,
            "mode": mode,
            "executed": False,
            "instructions": "Review the editor query. No BindingDB search has run.",
        }

    @apps.tool(
        resource_uri=URI,
        visibility=["app"],
        annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    )
    def editor_pubchem_candidates(cids: list[int]) -> dict[str, Any]:
        """Retrieve every additional PubChem candidate returned by an ambiguous name lookup."""
        if not network:
            raise ToolError("Network lookups disabled (--no-network)")
        if len(cids) > 19 or any(type(v) is not int or v < 1 for v in cids):
            raise ToolError("Expected at most 19 positive PubChem CIDs")
        if not cids:
            return {"candidates": []}
        url = (
            "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
            + ",".join(map(str, cids))
            + "/property/SMILES,InChIKey,Title/JSON"
        )
        with urllib.request.urlopen(url, timeout=14) as response:
            rows = json.load(response)["PropertyTable"]["Properties"]
        return {
            "candidates": [
                {
                    "smiles": r["SMILES"],
                    "title": r.get("Title"),
                    "cid": r["CID"],
                    "inchi_key": r.get("InChIKey"),
                    "source": "PubChem",
                }
                for r in rows
            ]
        }

    return apps


def register_exact_structure_search(mcp, db) -> None:
    """Add true whole-molecule equality; a fingerprint score of 1 is deliberately not used."""

    @mcp.tool(annotations=READ_ONLY)
    def exact_structure_search(smiles: str, limit: int = 50) -> dict[str, Any]:
        """Find the same complete molecule by canonical isomeric SMILES. Retains all fragments,
        stereo, isotope and charge information. Tautomers, protonation states, and unspecified stereo
        are distinct. Requires the optional RDKit extra. Uses stored InChIKey connectivity as a
        candidate screen, then verifies complete SMILES equality. Reports incomplete coverage when
        the local database has missing InChIKeys."""
        try:
            from rdkit import Chem
        except ImportError:
            raise ToolError(
                "Install mcp-bindingdb[substructure] for exact structure search"
            ) from None
        if not smiles.strip() or len(smiles) > 20000:
            raise ToolError(
                "Expected a non-empty molecular SMILES of at most 20,000 characters"
            )
        mol = Chem.MolFromSmiles(smiles)
        if (
            mol is None
            or not mol.GetNumAtoms()
            or any(a.GetAtomicNum() == 0 for a in mol.GetAtoms())
        ):
            raise ToolError(
                "Exact search requires concrete molecular SMILES, without query atoms"
            )
        canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
        key = Chem.MolToInchiKey(mol)
        if not key:
            raise ToolError("Could not create an InChIKey for candidate screening")
        rows = db.rows(
            "SELECT monomerid, bdbm_id, name, smiles, inchi_key, n_activities FROM compound WHERE inchi_key LIKE ?",
            [key[:14] + "-%"],
            limit=100000,
        )
        hits = []
        for row in rows:
            candidate = Chem.MolFromSmiles(row["smiles"] or "")
            if (
                candidate is not None
                and Chem.MolToSmiles(candidate, isomericSmiles=True) == canonical
            ):
                hits.append(row)
        missing = db.rows(
            "SELECT count(*) AS n FROM compound WHERE inchi_key IS NULL OR inchi_key = ''",
            limit=1,
        )[0]["n"]
        limit = max(1, min(500, limit))
        return {
            "query": {
                "input": smiles,
                "canonical": canonical,
                "inchi_key": key,
                "equality": "full canonical isomeric SMILES; no tautomer or salt normalization",
            },
            "rows": hits[:limit],
            "n_matches": len(hits),
            "truncated": len(hits) > limit,
            "coverage": {
                "missing_inchikey_compounds": missing,
                "complete": not missing and len(rows) < 100000,
            },
            "note": "Candidate screening relies on stored InChIKeys. Missing or stale identifiers can limit recall.",
        }


def register_filtered_structure_search(mcp, db, index=None) -> None:
    """Intersect affinity-qualified compounds with structure matches before limiting results."""

    @mcp.tool(annotations=READ_ONLY)
    def filtered_structure_search(
        query: str,
        mode: Literal["exact", "substructure", "similarity"] = "exact",
        query_type: Literal["smiles", "smarts"] = "smiles",
        affinity_type: Literal["Any", "Ki", "Kd", "IC50", "EC50"] = "Any",
        min_value_nm: float = 0,
        max_value_nm: float = 1000,
        threshold: float = 0.85,
        use_chirality: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search structures with at least one qualifying affinity measurement in an inclusive nM
        range. Any accepts Ki, Kd, IC50 or EC50, without converting between measurement types.
        Affinity is applied BEFORE structural search/result limits. Returns a qualifying measurement
        for each hit. '>' lower bounds never establish a finite range; '<' upper bounds qualify only
        when min_value_nm=0 and their bound is <= max_value_nm. Missing/unparseable values are excluded.
        Exact retains salts/stereo/tautomers, using stored InChIKeys as a candidate screen. Other modes
        require the server's structure index and report partial coverage/time limits explicitly."""
        import math

        try:
            from rdkit import Chem
        except ImportError:
            raise ToolError(
                "Install mcp-bindingdb[substructure] for structure search"
            ) from None
        if (
            not all(math.isfinite(v) and v >= 0 for v in (min_value_nm, max_value_nm))
            or min_value_nm > max_value_nm
        ):
            raise ToolError(
                "Expected finite affinity limits: 0 <= min_value_nm <= max_value_nm"
            )
        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ToolError("Similarity threshold must be between 0 and 1")
        if not query.strip() or len(query) > 20000:
            raise ToolError(
                "Expected a non-empty structure of at most 20,000 characters"
            )
        if mode != "substructure" and query_type != "smiles":
            raise ToolError("Exact and similarity searches require molecular SMILES")
        mol = (
            Chem.MolFromSmarts(query)
            if query_type == "smarts"
            else Chem.MolFromSmiles(query)
        )
        if mol is None or not mol.GetNumAtoms():
            raise ToolError("Invalid structure query")
        if mode != "substructure" and any(
            a.GetAtomicNum() == 0 for a in mol.GetAtoms()
        ):
            raise ToolError(
                "Exact and similarity searches require concrete molecular SMILES"
            )
        if mode != "exact" and index is None:
            raise ToolError("This search requires the BindingDB structure index")
        types = (
            ["Ki", "Kd", "IC50", "EC50"] if affinity_type == "Any" else [affinity_type]
        )
        # Only measured values or bounds that establish membership in the entire requested interval.
        predicate = """a.affinity_type IN (SELECT unnest(?)) AND a.unit = 'nM'
            AND isfinite(a.value) AND a.value >= 0 AND a.value <= ?
            AND ((a.relation = '=' AND a.value >= ?)
                 OR (? = 0 AND a.relation IN ('<', '<=') AND a.value > 0))"""
        params = [types, max_value_nm, min_value_nm, min_value_nm]
        limit = max(1, min(500, limit))
        about = {
            "input": query,
            "mode": mode,
            "query_type": query_type,
            "affinity": {
                "type": affinity_type,
                "min_value_nm": min_value_nm,
                "max_value_nm": max_value_nm,
                "inclusive": True,
            },
        }
        notes = [
            "At least one reported measurement must qualify. Measurement types are not interconverted.",
            "'>' values are excluded; '<' values qualify only for a zero minimum and an upper bound within the range.",
        ]
        scores = {}
        coverage = {}
        if mode == "exact":
            canonical = Chem.MolToSmiles(mol, isomericSmiles=True)
            key = Chem.MolToInchiKey(mol)
            if not key:
                raise ToolError(
                    "Could not create an InChIKey for exact candidate screening"
                )
            candidates = db.rows(
                """SELECT c.monomerid, c.smiles FROM compound c
                WHERE c.inchi_key LIKE ? AND EXISTS (SELECT 1 FROM activity a
                    WHERE a.monomerid = c.monomerid AND """
                + predicate
                + ") ORDER BY c.monomerid",
                [key[:14] + "-%", *params],
                limit=100001,
            )
            screened_all = len(candidates) <= 100000
            ids = []
            for row in candidates[:100000]:
                candidate = Chem.MolFromSmiles(row["smiles"] or "")
                if (
                    candidate is not None
                    and Chem.MolToSmiles(candidate, isomericSmiles=True) == canonical
                ):
                    ids.append(row["monomerid"])
            missing = db.rows(
                "SELECT count(*) AS n FROM compound WHERE inchi_key IS NULL OR inchi_key = ''",
                limit=1,
            )[0]["n"]
            coverage = {
                "missing_inchikey_compounds": missing,
                "candidate_screen_complete": screened_all,
            }
            complete = screened_all and not missing
            about.update(canonical=canonical, inchi_key=key)
            notes.append(
                "Exact uses full canonical isomeric SMILES. Missing or stale stored InChIKeys can limit recall."
            )
        else:
            eligible = (
                db.rows(
                    "SELECT list(DISTINCT a.monomerid ORDER BY a.monomerid) AS ids FROM activity a WHERE "
                    + predicate,
                    params,
                    limit=1,
                )[0]["ids"]
                or []
            )
            time_limit = getattr(db, "timeout_s", 30) * 0.8
            if eligible:
                if mode == "similarity":
                    hits = index.similar(mol, threshold, time_limit, within=eligible)
                    scores = dict(zip(hits.monomerids, hits.similarities))
                    about["threshold"] = threshold
                else:
                    hits = index.search(
                        mol, limit + 1, time_limit, use_chirality, within=eligible
                    )
                    about["use_chirality"] = use_chirality
                ids = hits.monomerids
                coverage = {
                    "eligible_compounds": len(eligible),
                    "indexed_eligible_compounds": hits.total,
                    "compounds_searched": hits.searched,
                }
                complete = hits.searched == hits.total and hits.total == len(eligible)
                if mode == "substructure" and hits.hit_max_results:
                    complete = False
            else:
                ids, complete = [], True
                coverage = {
                    "eligible_compounds": 0,
                    "indexed_eligible_compounds": 0,
                    "compounds_searched": 0,
                }
            if not complete:
                notes.append(
                    "Results are partial: a result/time limit was reached or some affinity-qualified compounds are missing from the structure index."
                )
        selected = ids[:limit]
        rows = []
        if selected:
            rows = db.rows(
                """SELECT c.monomerid, c.bdbm_id, c.name, c.smiles,
                    a.ki_result_id AS affinity_measurement_id, a.affinity_type,
                    a.relation AS affinity_relation, a.value AS affinity_value_nm
                FROM compound c JOIN activity a ON a.monomerid = c.monomerid
                WHERE c.monomerid IN (SELECT unnest(?)) AND """
                + predicate
                + """
                QUALIFY row_number() OVER (PARTITION BY c.monomerid ORDER BY a.value, a.ki_result_id) = 1""",
                [selected, *params],
                limit=limit,
            )
            positions = {v: i for i, v in enumerate(selected)}
            rows.sort(key=lambda row: positions[row["monomerid"]])
            if mode == "similarity":
                for row in rows:
                    row["similarity"] = scores[row["monomerid"]]
        return {
            "query": about,
            "rows": rows,
            "row_count": len(rows),
            "truncated": len(ids) > limit,
            "search_complete": complete,
            "n_matches": len(ids) if complete else None,
            "n_matches_lower_bound": len(ids),
            "coverage": coverage,
            "notes": notes,
        }
