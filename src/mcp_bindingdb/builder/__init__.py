"""Build a BindingDB DuckDB database from BindingDB's MySQL dump, without MySQL or Docker (pipeline.build).

The server runs it on first use (mcp_bindingdb.local_build), and scripts/build_duckdb.sh runs it on the command
line: python -m mcp_bindingdb.builder.
"""

DEFAULT_RELEASE = "202610"  # the BindingDB release this version of the server builds
