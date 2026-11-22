"""Package a finished build for a folder of prebuilt databases (see mcp_bindingdb.builder.prebuilt).

    uv run python scripts/package_prebuilt.py compress --out ~/bindingdb-mirror [--release 202611] [--dir DATA]
    uv run python scripts/package_prebuilt.py check <link of the shared folder>

compress writes 202611.duckdb.zst, 202611.sslib.zst and 202611.json to --out (zstd level 19, long-distance
matching, 128 MB window: about 440 MB for the 1.7 GB of release 202611, in about two minutes). Upload the three
files to the shared folder (on Google Drive, shared with "Anyone with the link"); the folder's link is what the
server is given (MCP_BINDINGDB_MIRROR), and stays the same as releases are added. check lists the folder as the
server does, and tries the start of each release's files.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import duckdb

from mcp_bindingdb import notebook
from mcp_bindingdb.builder import DB_FORMAT, prebuilt
from mcp_bindingdb.builder.pipeline import database_path
from mcp_bindingdb.local_build import complete_releases, data_dir
from mcp_bindingdb.substructure import index_path

ZSTD_MAGIC = b"\x28\xb5\x2f\xfd"


def compress(args: argparse.Namespace) -> int:
    folder = args.dir.expanduser()
    releases = complete_releases(folder) if folder.is_dir() else []
    release = args.release or (releases[-1] if releases else None)
    if release not in releases:
        print(f"No complete release {release or ''} in {folder} (complete: {', '.join(releases) or 'none'})",
              file=sys.stderr)
        return 1
    db = database_path(folder, release)
    con = duckdb.connect(str(db), read_only=True)
    build_info = dict(con.execute("SELECT key, value FROM _build_info").fetchall())
    con.close()
    out = args.out.expanduser()
    out.mkdir(parents=True, exist_ok=True)
    names = prebuilt.file_names(release)
    files = {}
    for kind, source in (("duckdb", db), ("sslib", index_path(db))):
        dest = out / names[kind]
        t0 = time.time()
        print(f"compressing {source.name} ({source.stat().st_size / 1e6:.0f} MB)...", flush=True)
        prebuilt.compress(source, dest)
        files[kind] = {"size": dest.stat().st_size, "sha256": prebuilt.sha256(dest),
                       "raw_size": source.stat().st_size}
        print(f"  {dest} ({files[kind]['size'] / 1e6:.0f} MB, {time.time() - t0:.0f}s)")
    source = notebook.source_version()
    packaged_by = f"mcp-bindingdb {notebook.package_version()}" + (
        f", commit {source['commit']}" if source.get("commit") else "")
    info = prebuilt.release_info(release, build_info, files, packaged_by)
    (out / names["info"]).write_text(json.dumps(info, indent=1) + "\n")
    print(f"  {out / names['info']}\nUpload these three files to the shared folder: {', '.join(names.values())}")
    return 0


def check(args: argparse.Namespace) -> int:
    mirror = prebuilt.Mirror(args.folder)
    listed = mirror.releases()
    if listed is None:
        listed = [args.release] if args.release else []
        if not listed:
            print("A web address cannot be listed: give --release", file=sys.stderr)
            return 1
    print(f"{mirror.host}: releases {', '.join(listed) or 'none'}")
    failed = 0
    for release in listed:
        try:
            info = mirror.release(release, DB_FORMAT)
        except (OSError, ValueError) as e:
            print(f"  {release}: {type(e).__name__}: {e}")
            failed += 1
            continue
        if info is None:
            print(f"  {release}: not usable by this version (layout {DB_FORMAT}), or its .json is missing")
            continue
        for kind in prebuilt.KINDS:
            f = info["files"][kind]
            try:
                with prebuilt.open_url(f["url"], 30, {"Range": "bytes=0-3"}) as response:
                    head, content_type = response.read(4), response.headers.get("Content-Type") or ""
            except OSError as e:
                print(f"  {release} {kind}: {type(e).__name__}: {e}")
                failed += 1
                continue
            ok = head == ZSTD_MAGIC
            print(f"  {release} {kind}: {'ok' if ok else 'NOT a zstd file'} ({f['size'] / 1e6:.0f} MB"
                  + (", got a web page: is it shared with 'Anyone with the link'?" if "html" in content_type else "")
                  + ")")
            failed += not ok
    return 1 if failed else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = p.add_subparsers(dest="command", required=True)
    c = sub.add_parser("compress", help="compress a finished build into a release's three files")
    c.add_argument("--out", type=Path, required=True, help="folder to write them to")
    c.add_argument("--release", help="release to package (default: the newest complete one)")
    c.add_argument("--dir", type=Path, default=data_dir(), help=f"where the build is (default {data_dir()})")
    c.set_defaults(run=compress)
    h = sub.add_parser("check", help="list a shared folder as the server does and try each file")
    h.add_argument("folder", help="the folder's link (or path)")
    h.add_argument("--release", help="the release to try, under a web address (which cannot be listed)")
    h.set_defaults(run=check)
    args = p.parse_args()
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
