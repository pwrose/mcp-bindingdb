#!/usr/bin/env bash
# Build data/bindingdb_${RELEASE}.duckdb and its structure-search index from BindingDB's MySQL dump.
#
#   scripts/build_duckdb.sh [--release 202610] [--workers N]
#
# Runs mcp_bindingdb.builder: downloads the dump from bindingdb.org (kept in data/ for rebuilds), loads it into
# DuckDB without MySQL, adds the derived query tables, computes standard InChIKeys and compound properties, and
# builds the RDKit substructure index. The PII tables (regusers, person) are never copied. A build that stops
# resumes where it ended. Requires uv. The server does the same on first use when it finds no database.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --release|--workers) ARGS+=("$1" "$2"); shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

exec uv run --project "$ROOT" --extra substructure python -m mcp_bindingdb.builder \
  --dir "$ROOT/data" --keep-zip ${ARGS[@]+"${ARGS[@]}"}
