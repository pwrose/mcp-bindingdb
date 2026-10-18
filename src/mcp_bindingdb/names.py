"""Chemical name to structure with OPSIN (systematic IUPAC names, offline) and PubChem (any name, network).

OPSIN is optional: install it with the `name` extra (pyopsin, which bundles the OPSIN jar and runs it
in-process through JPype; it needs a Java runtime). The JVM starts on the first OPSIN lookup (about 1 s).
"""

from __future__ import annotations

import functools
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

try:
    import jpype
    import jpype.config
    from pyopsin.jar import packaged_jar_path
except ImportError:  # the `name` extra is not installed
    jpype = None

PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/property/SMILES,InChIKey,Title/JSON"


@dataclass
class Structure:
    smiles: str
    inchi_key: str | None
    title: str | None = None  # PubChem's preferred name
    cid: int | None = None
    other_cids: list[int] = field(default_factory=list)  # further PubChem compounds with this name
    warning: str | None = None  # OPSIN's message when it parsed the name with a warning


class NameLookupError(RuntimeError):
    """The service could not be asked (as opposed to: it does not know the name)."""


def opsin_unavailable_reason() -> str | None:
    """None if OPSIN can be used, else why not."""
    if jpype is None:
        return "pyopsin not installed (install the 'name' extra)"
    if not packaged_jar_path().is_file():
        return "the installed pyopsin has no bundled OPSIN jar (needs pyopsin >= 1.1)"
    if not jpype.isJVMStarted():
        try:
            jpype.getDefaultJVMPath()
        except jpype.JVMNotFoundException:
            return "no Java runtime found"
    return None


_opsin_lock = threading.Lock()
_opsin: tuple[Any, Any, Any] | None = None


def _opsin_parser() -> tuple[Any, Any, Any]:
    global _opsin
    with _opsin_lock:
        if _opsin is None:
            if not jpype.isJVMStarted():
                # Tool calls run in worker threads, and destroying a JVM started outside the main thread
                # hangs at interpreter exit; the process is ending anyway, so skip it.
                jpype.config.destroy_jvm = False
                jpype.startJVM("--enable-native-access=ALL-UNNAMED", classpath=[str(packaged_jar_path())])
            from uk.ac.cam.ch.wwmm import opsin
            _opsin = opsin.NameToStructure.getInstance(), opsin.NameToStructureConfig(), opsin.NameToInchi
        return _opsin


def opsin_lookup(name: str) -> Structure | None:
    """Parse a systematic name with OPSIN; None if OPSIN cannot interpret it."""
    try:
        nts, config, to_inchi = _opsin_parser()
        result = nts.parseChemicalName(name, config)
        status = str(result.getStatus().name())
        if status == "FAILURE" or result.getSmiles() is None:
            return None
        key = to_inchi.convertResultToStdInChIKey(result)
    except Exception as e:  # JVM start-up or a Java exception
        raise NameLookupError(f"OPSIN: {e}") from None
    return Structure(str(result.getSmiles()), str(key) if key else None,
                     warning=str(result.getMessage()) if status == "WARNING" else None)


@functools.lru_cache(maxsize=1024)
def pubchem_lookup(name: str, timeout_s: float = 10.0) -> Structure | None:
    """Look a name up in PubChem (synonyms, trade names, CAS numbers, ...); None if PubChem has no match.

    The name is POSTed rather than put in the URL, so names containing '/' work."""
    request = urllib.request.Request(PUBCHEM_URL, data=urllib.parse.urlencode({"name": name}).encode(),
                                     headers={"User-Agent": "mcp-bindingdb"})
    try:
        with urllib.request.urlopen(request, timeout=timeout_s) as response:
            properties = json.load(response)["PropertyTable"]["Properties"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise NameLookupError(f"PubChem: HTTP {e.code} {e.reason}") from None
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        raise NameLookupError(f"PubChem: {e}") from None
    first = properties[0]
    return Structure(first["SMILES"], first.get("InChIKey"), title=first.get("Title"), cid=first.get("CID"),
                     other_cids=[p["CID"] for p in properties[1:] if "CID" in p])
