"""Shared test setup."""

import pytest


@pytest.fixture(autouse=True)
def no_default_mirror(monkeypatch):
    """No test downloads from the project's prebuilt-database folder unless it sets MCP_BINDINGDB_MIRROR itself."""
    monkeypatch.setenv("MCP_BINDINGDB_MIRROR", "none")
