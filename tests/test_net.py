"""HTTPS requests verify certificates with the operating system's trust store (net.py)."""

import re
from pathlib import Path

import truststore

from mcp_bindingdb import net

SRC = Path(__file__).resolve().parents[1] / "src" / "mcp_bindingdb"


def test_requests_use_the_system_trust_store():
    assert isinstance(net.ssl_context(), truststore.SSLContext)


def test_every_request_goes_through_net():
    """A plain urlopen uses Python's own CA file, which rejected data.rcsb.org (November 2026)."""
    direct = [f"{p.relative_to(SRC)}:{i}" for p in SRC.rglob("*.py") if p.name != "net.py"
              for i, line in enumerate(p.read_text().splitlines(), 1)
              if re.search(r"\burlopen\(", line) and "net.urlopen(" not in line]
    assert not direct, direct
