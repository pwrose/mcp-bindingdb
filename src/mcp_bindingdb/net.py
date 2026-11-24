"""HTTPS requests that verify certificates the way the operating system does.

Python's own OpenSSL checks a server against a CA file of its own and does not fetch missing intermediate
certificates, so it can reject a site that browsers and curl accept: OpenSSL 3.0 (Python 3.12.7) rejects
data.rcsb.org's certificate of November 2026, and the PDB resolution lookup then fails silently. truststore
verifies with the operating system's trust store instead (Keychain on macOS, the Windows certificate store,
the system CA bundle on Linux).
"""

from __future__ import annotations

import functools
import ssl
import urllib.request
from typing import Any


@functools.cache
def ssl_context() -> ssl.SSLContext:
    """The operating system's certificate verification, or Python's default without truststore."""
    try:
        import truststore
    except ImportError:
        return ssl.create_default_context()
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


def urlopen(request: str | urllib.request.Request, timeout: float) -> Any:
    """urllib.request.urlopen with ssl_context()."""
    return urllib.request.urlopen(request, timeout=timeout, context=ssl_context())
