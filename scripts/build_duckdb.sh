#!/usr/bin/env bash
# Build data/bindingdb_${RELEASE}.duckdb from the BindingDB MySQL dump.
#
#   scripts/build_duckdb.sh [--release 202610] [--keep-mysql] [--include-pii] [--no-substructure]
#
# Steps: download + unzip dump, load into a temporary MySQL 8.4 container,
# copy into DuckDB (scripts/convert_to_duckdb.py), add derived query tables
# (scripts/add_derived_tables.py), build the RDKit substructure index
# (scripts/build_substructure_index.py), tear the container down.
# Requires Docker (daemon running) and uv.
set -euo pipefail

RELEASE=202610
KEEP_MYSQL=0
SUBSTRUCTURE=1
CONVERT_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --release) RELEASE="$2"; shift 2 ;;
    --keep-mysql) KEEP_MYSQL=1; shift ;;
    --include-pii) CONVERT_ARGS+=(--include-pii); shift ;;
    --no-substructure) SUBSTRUCTURE=0; shift ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RAW="$ROOT/data/raw"
URL="https://www.bindingdb.org/rwd/bind/BDB-mySQL_All_${RELEASE}_dmp.zip"
ZIP="$RAW/BDB-mySQL_All_${RELEASE}_dmp.zip"
DMP="$RAW/BDB-mySQL_All_${RELEASE}.dmp"
OUT="$ROOT/data/bindingdb_${RELEASE}.duckdb"
CONTAINER=bdb-mysql
VOLUME=bdb-mysql-data
PORT=3307

log() { echo "[$(date +%H:%M:%S)] $*"; }

# 1. Download and unzip
mkdir -p "$RAW"
expected=$(curl -sIL "$URL" | awk 'tolower($1)=="content-length:" {v=$2} END {gsub(/\r/,"",v); print v}')
if [[ ! -f "$ZIP" || "$(stat -f%z "$ZIP" 2>/dev/null || stat -c%s "$ZIP")" != "$expected" ]]; then
  log "Downloading $URL ($expected bytes)"
  curl -fL -C - -o "$ZIP" "$URL"
fi
actual=$(stat -f%z "$ZIP" 2>/dev/null || stat -c%s "$ZIP")
[[ "$actual" == "$expected" ]] || { echo "size mismatch: $actual != $expected" >&2; exit 1; }
[[ -f "$DMP" ]] || { log "Unzipping"; unzip -n -q "$ZIP" -d "$RAW"; }

# 2. Load into a temporary MySQL 8.4
docker info >/dev/null 2>&1 || { echo "Docker daemon is not running" >&2; exit 1; }
if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  log "Starting MySQL 8.4 container"
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  docker volume rm "$VOLUME" >/dev/null 2>&1 || true
  docker run -d --name "$CONTAINER" -p "127.0.0.1:${PORT}:3306" \
    -e MYSQL_ALLOW_EMPTY_PASSWORD=yes -e MYSQL_DATABASE=bindingdb \
    -v "$VOLUME:/var/lib/mysql" mysql:8.4 \
    --skip-log-bin --innodb-buffer-pool-size=4G --innodb-flush-log-at-trx-commit=0 \
    --innodb-doublewrite=0 --max-allowed-packet=1G >/dev/null
fi
log "Waiting for MySQL"
until docker exec "$CONTAINER" mysql -uroot -e 'SELECT 1' bindingdb >/dev/null 2>&1; do sleep 3; done

# A marker written only after a successful load, so a failed load is redone.
if ! docker exec "$CONTAINER" test -f /var/lib/mysql/.bdb_loaded; then
  log "Loading dump (this takes a while)"
  docker exec "$CONTAINER" mysql -uroot -e 'DROP DATABASE IF EXISTS bindingdb; CREATE DATABASE bindingdb'
  t0=$(date +%s)
  docker exec -i "$CONTAINER" mysql -uroot --max-allowed-packet=1G bindingdb < "$DMP"
  docker exec "$CONTAINER" touch /var/lib/mysql/.bdb_loaded
  log "Dump loaded in $(( $(date +%s) - t0 ))s"
else
  log "Dump already loaded; skipping"
fi

# 3. Convert to DuckDB
log "Converting to DuckDB"
# Build into a side file and rename at the end, so a running MCP server (which holds a
# read lock on $OUT) keeps working and picks up the new file on restart.
BUILDING="$OUT.building"
uv run --project "$ROOT" python "$ROOT/scripts/convert_to_duckdb.py" \
  --release "$RELEASE" --output "$BUILDING" --zip "$ZIP" --source-url "$URL" \
  --port "$PORT" ${CONVERT_ARGS[@]+"${CONVERT_ARGS[@]}"}
log "Adding derived tables"
uv run --project "$ROOT" python "$ROOT/scripts/add_derived_tables.py" "$BUILDING"
mv "$BUILDING" "$OUT"

# 4. Substructure index (data/bindingdb_${RELEASE}.sslib, used by substructure_search)
if [[ "$SUBSTRUCTURE" -eq 1 ]]; then
  log "Building substructure index"
  uv run --project "$ROOT" --extra substructure python "$ROOT/scripts/build_substructure_index.py" "$OUT"
fi

# 5. Clean up
if [[ "$KEEP_MYSQL" -eq 0 ]]; then
  log "Removing MySQL container and volume"
  docker rm -f "$CONTAINER" >/dev/null
  docker volume rm "$VOLUME" >/dev/null
fi
log "Done: $OUT"
