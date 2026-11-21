"""Build a BindingDB DuckDB database from BindingDB's MySQL dump, without MySQL or Docker (pipeline.build).

The server runs it on first use (mcp_bindingdb.local_build), and scripts/build_duckdb.sh runs it on the command
line: python -m mcp_bindingdb.builder.
"""

DEFAULT_RELEASE = "202610"  # the BindingDB release a new installation builds first

# The layout of the database the server expects, recorded in _build_info as db_format (databases built before it
# was recorded count as 1). Bump it when the build changes tables or columns the server reads, so that existing
# databases are rebuilt (local_build.locate) instead of failing in the tools.
DB_FORMAT = 1
