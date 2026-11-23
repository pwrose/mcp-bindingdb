"""Shared test setup."""

import pytest


@pytest.fixture(autouse=True)
def no_default_mirror(monkeypatch):
    """No test downloads from the project's prebuilt-database folder unless it sets MCP_BINDINGDB_MIRROR itself."""
    monkeypatch.setenv("MCP_BINDINGDB_MIRROR", "none")


def built_database():
    """The database the tests read: a clone's data/ as before, else the newest complete release of this layout
    in the user data folder, where the server and the Claude Desktop bundle keep theirs. It never starts a
    build, so a machine with no database still skips rather than downloading one."""
    from mcp_bindingdb import local_build
    from mcp_bindingdb.db import find_database

    try:
        return find_database()
    except FileNotFoundError:
        folder = local_build.data_dir()
        releases = local_build.complete_releases(folder) if folder.is_dir() else []
        # db_format reads the file, and returns 0 when it cannot: an earlier test module that opened this same
        # database at import holds it, and DuckDB refuses the second connection. 0 therefore means "in use", not
        # "wrong layout", and rejecting it skipped every module collected after the first one to open it.
        usable = [r for r in releases
                  if local_build.db_format(local_build.database_path(folder, r)) in (local_build.DB_FORMAT, 0)]
        if not usable:
            raise
        return local_build.database_path(folder, usable[-1])
