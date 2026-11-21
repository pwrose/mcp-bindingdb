#!/usr/bin/env bash
# Build dist/mcp-bindingdb.mcpb, an MCP bundle that Claude Desktop installs with a double-click.
#
#   scripts/build_bundle.sh
#
# The bundle holds the source, pyproject.toml and uv.lock (no database, no virtual environment): Claude Desktop
# installs the Python dependencies with uv, and the server builds the database on the user's computer on first
# use (mcp_bindingdb.local_build).
# Requires Node.js (for npx @anthropic-ai/mcpb).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$ROOT/dist/bundle"
VERSION=$(sed -n 's/^version = "\(.*\)"/\1/p' "$ROOT/pyproject.toml" | head -1)
OUT="$ROOT/dist/mcp-bindingdb.mcpb"  # a fixed name, so releases/latest/download/mcp-bindingdb.mcpb works

grep -q "\"version\": \"$VERSION\"" "$ROOT/bundle/manifest.json" || {
  echo "bundle/manifest.json's version differs from pyproject.toml's ($VERSION)" >&2; exit 1; }

# Claude Desktop installs the lock with no compilers at hand, so each platform must get a wheel of every package
# (uv lock's required-environments lets packages with a source distribution through). Intel Macs are the usual
# casualty: see [tool.uv] in pyproject.toml.
REQS="$(mktemp -d)"
trap 'rm -rf "$REQS"' EXIT
(cd "$ROOT" && uv export --frozen --extra substructure --extra structures --extra opsin --no-hashes --no-emit-project \
  > "$REQS/requirements.txt")
for platform in aarch64-apple-darwin x86_64-apple-darwin x86_64-pc-windows-msvc \
                x86_64-manylinux_2_28 aarch64-manylinux_2_28; do
  for python in 3.11 3.14; do
    uv pip install --dry-run --quiet --no-deps --only-binary :all: --python-platform "$platform" \
      --python-version "$python" --target "$REQS/target" -r "$REQS/requirements.txt" || {
      echo "uv.lock has no wheel for some package on $platform, Python $python" >&2; exit 1; }
  done
done

# Stage only what the server needs, so data/, .venv/ and the rest of the repository stay out.
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp "$ROOT/bundle/manifest.json" "$ROOT/pyproject.toml" "$ROOT/uv.lock" "$ROOT/README.md" "$ROOT/LICENSE" "$STAGE/"
rsync -a --exclude '__pycache__' --exclude '*.pyc' "$ROOT/src" "$STAGE/"

npx -y @anthropic-ai/mcpb@2 validate "$STAGE/manifest.json"
rm -f "$OUT"  # a new file rather than an overwrite, so its creation date (which Finder shows) is the build's
npx -y @anthropic-ai/mcpb@2 pack "$STAGE" "$OUT"
echo "Built $OUT"
