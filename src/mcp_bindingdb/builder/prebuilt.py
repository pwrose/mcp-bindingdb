"""Prebuilt databases: download a release's finished database and index from a mirror instead of building them.

A mirror is a folder with three files per release, named after it:

    202611.duckdb.zst   the database, compressed with zstd
    202611.sslib.zst    the structure-search index, compressed with zstd
    202611.json         what they are: {"release", "db_format", "built_at", "source_zip_sha256", "packaged_by",
                        "files": {"duckdb": {"size", "sha256", "raw_size"}, "sslib": {...}}}

$MCP_BINDINGDB_MIRROR (or the builder's --mirror; DEFAULT_MIRROR if unset, "none" for none) names the folder: a shared Google Drive folder's link, a web
address the files are under (<address>/202611.json, ...), or a local path. A Google Drive folder or a local one is
listed, so the mirror's releases are known; under a web address, a release is looked for by name. Adding a
release is adding its three files, so the folder's link stays the same. scripts/package_prebuilt.py writes them
from a finished build.

The builder (pipeline.build) tries the mirror first and builds the release itself if the mirror does not have it
or anything goes wrong, so a mirror only ever saves time. The compressed files are checked against the SHA-256 in
the release's .json, the decompressed ones against zstd's checksum and the size there, and the database against
the release and DB_FORMAT.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Callable

import duckdb

MIRROR_ENV = "MCP_BINDINGDB_MIRROR"
#: The mirror used when $MCP_BINDINGDB_MIRROR is not set: a shared Google Drive folder, for now, until the
#: prebuilt databases have a permanent home. "none" in $MCP_BINDINGDB_MIRROR turns mirrors off.
DEFAULT_MIRROR = "https://drive.google.com/drive/folders/1TjCVRiUdS_iJWtGZBjzVIoYQZoTFB7MO"
NO_MIRROR = ("none", "off", "no", "false", "0")
KINDS = ("duckdb", "sslib")  # the files of a release, by suffix; the database is renamed into place last
#: zstd settings of package_prebuilt.py: level 19 with long-distance matching in a 128 MB window, which
#: decompresses with zstd's default memory limit (a larger window would need about as much memory as it spans).
LEVEL, WINDOW_LOG = 19, 27
CHUNK = 1 << 20

_RELEASE_FILE = re.compile(r"(\d{6})\.(json|duckdb\.zst|sslib\.zst)")
_DRIVE_FOLDER = re.compile(r"https://drive\.google\.com/(?:drive/(?:u/\d+/)?folders/|open\?id=)([\w-]+)")
_DRIVE_FILE = re.compile(r"https://drive\.google\.com/(?:file/d/|uc\?(?:[^#]*&)?id=)([\w-]+)")
# An entry of Google Drive's embedded folder view: its file id, then its name.
_DRIVE_ENTRY = re.compile(r'id="entry-([\w-]+)".*?class="flip-entry-title">([^<]*)<', re.S)


def file_names(release: str) -> dict[str, str]:
    """A release's files on a mirror, by kind ('info' is the .json)."""
    return {"info": f"{release}.json", "duckdb": f"{release}.duckdb.zst", "sslib": f"{release}.sslib.zst"}


def mirror_url() -> str | None:
    """$MCP_BINDINGDB_MIRROR; DEFAULT_MIRROR if it is unset, empty or a bundle setting the host left
    unsubstituted; None if it is "none" (or off, no, false, 0)."""
    url = os.environ.get(MIRROR_ENV, "").strip()
    if url.lower() in NO_MIRROR:
        return None
    return url if url and "${" not in url else DEFAULT_MIRROR


def drive_download(file_id: str) -> str:
    """A Google Drive file's direct download; confirm=t skips the "can't scan for viruses" page of large files."""
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"


def open_url(url: str, timeout: float, headers: dict[str, str] | None = None) -> Any:
    """Open a URL or a local path (a Google Drive file's sharing link opens its download)."""
    if match := _DRIVE_FILE.match(url):
        url = drive_download(match[1])
    if "://" not in url:
        url = Path(url).expanduser().resolve().as_uri()
    request = urllib.request.Request(url, headers={"User-Agent": "mcp-bindingdb", **(headers or {})})
    return urllib.request.urlopen(request, timeout=timeout)


def mirror_host(location: str) -> str:
    """Where a mirror is, for messages."""
    if _DRIVE_FOLDER.match(location) or _DRIVE_FILE.match(location):
        return "Google Drive"
    if "://" not in location:
        return location
    return urllib.parse.urlparse(location).hostname or location


class Mirror:
    """A folder of prebuilt releases (see the module docstring)."""

    def __init__(self, location: str) -> None:
        self.location = location.strip()
        self.host = mirror_host(self.location)
        self._listing: dict[str, str] | None = None

    def listing(self, timeout: float) -> dict[str, str] | None:
        """The release files in the folder, name -> URL; None for a web address, which cannot be listed.
        Raises OSError or ValueError if the folder cannot be read."""
        if self._listing is not None:
            return self._listing
        if match := _DRIVE_FOLDER.match(self.location):
            url = f"https://drive.google.com/embeddedfolderview?id={match[1]}"
            with open_url(url, timeout) as response:
                page = response.read(1 << 23).decode("utf-8", "replace")
            entries = [(file_id, html.unescape(name).strip()) for file_id, name in _DRIVE_ENTRY.findall(page)]
            if not entries and "flip-entry" not in page:
                raise ValueError("the Google Drive folder could not be listed: is it shared with 'Anyone with the "
                                 "link'?")
            files: dict[str, str] = {}
            for file_id, name in entries:
                if _RELEASE_FILE.fullmatch(name):
                    files.setdefault(name, drive_download(file_id))
            self._listing = files
        elif "://" not in self.location:
            folder = Path(self.location).expanduser()
            if not folder.is_dir():
                raise FileNotFoundError(f"no mirror folder {folder}")
            self._listing = {p.name: str(p) for p in folder.iterdir() if _RELEASE_FILE.fullmatch(p.name)}
        return self._listing

    def url(self, name: str, timeout: float) -> str | None:
        """The URL of one of the folder's files, or None if a listed folder does not have it."""
        files = self.listing(timeout)
        if files is not None:
            return files.get(name)
        return f"{self.location.rstrip('/')}/{name}"

    def releases(self, timeout: float = 15) -> list[str] | None:
        """The releases in a listed folder with all three files, oldest first; None for a web address."""
        files = self.listing(timeout)
        if files is None:
            return None
        named = {m[1] for m in map(_RELEASE_FILE.fullmatch, files) if m}
        return sorted(r for r in named if all(n in files for n in file_names(r).values()))

    def release(self, release: str, db_format: int, timeout: float = 15) -> dict[str, Any] | None:
        """The release's .json, with the URL of each file added (files.<kind>.url), if the mirror has it in layout
        `db_format`; else None. Raises OSError or ValueError if the mirror cannot be read."""
        names = file_names(release)
        urls = {kind: self.url(name, timeout) for kind, name in names.items()}
        if any(u is None for u in urls.values()):
            return None
        try:
            with open_url(urls["info"], timeout) as response:
                text = response.read(1 << 20).decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        try:
            info = json.loads(text)
        except ValueError:
            raise ValueError(f"{names['info']} on the mirror is not JSON" + (
                " (Google Drive sent a web page: is the folder shared with 'Anyone with the link'?)"
                if text.lstrip().startswith("<") else "")) from None
        if info.get("release") != release or info.get("db_format") != db_format:
            return None
        if not all(isinstance((info.get("files") or {}).get(k), dict) for k in KINDS):
            raise ValueError(f"{names['info']} on the mirror does not describe both files")
        for kind in KINDS:
            info["files"][kind]["url"] = urls[kind]
        return info

    def newest(self, db_format: int, timeout: float = 5, today: date | None = None) -> str | None:
        """The newest release on the mirror in layout `db_format`: of a listed folder's releases, or, under a web
        address, of this month's and the three before, tried by name."""
        listed = self.releases(timeout)
        if listed is None:
            today = today or date.today()
            year, month, listed = today.year, today.month, []
            for _ in range(4):
                listed.insert(0, f"{year}{month:02d}")
                year, month = (year, month - 1) if month > 1 else (year - 1, 12)
        for release in reversed(listed):
            try:
                if self.release(release, db_format, timeout) is not None:
                    return release
            except (OSError, ValueError):
                continue
        return None


def newest_release(db_format: int, location: str | None = None, timeout: float = 5) -> str | None:
    """The newest usable release on the mirror (`location`, else $MCP_BINDINGDB_MIRROR), or None if there is no
    mirror, it cannot be read, or it has none."""
    location = location or mirror_url()
    if not location:
        return None
    try:
        return Mirror(location).newest(db_format, timeout)
    except (OSError, ValueError):
        return None


def download_size(info: dict[str, Any]) -> int:
    return sum(int(info["files"][k]["size"]) for k in KINDS)


def _download(url: str, dest: Path, size: int, progress: Callable[[int], None]) -> None:
    """Fetch `url` to `dest` (its size is known from the release's .json), resuming a partial download
    (dest.part)."""
    part = dest.with_name(dest.name + ".part")
    have = part.stat().st_size if part.is_file() else 0
    if have >= size:
        have = 0
        part.unlink(missing_ok=True)
    with open_url(url, 60, {"Range": f"bytes={have}-"} if have else None) as response:
        if have and getattr(response, "status", 200) != 206:  # the server ignored the Range: start over
            have = 0
        if "text/html" in (response.headers.get("Content-Type") or ""):
            raise ConnectionError(f"{dest.name}: the mirror sent a web page instead of the file (on Google Drive: "
                                  "is it shared with 'Anyone with the link'?)")
        with open(part, "ab" if have else "wb") as out:
            done = have
            progress(done)
            while block := response.read(CHUNK):
                out.write(block)
                done += len(block)
                progress(done)
    if part.stat().st_size != size:
        raise ConnectionError(f"the download of {dest.name} stopped at {part.stat().st_size:,} of {size:,} bytes; "
                              "it resumes on the next try")
    part.replace(dest)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(8 * CHUNK):
            h.update(block)
    return h.hexdigest()


def decompress(source: Path, dest: Path, progress: Callable[[int], None] = lambda _n: None) -> int:
    """Decompress a zstd file; returns the decompressed size. zstd checks the frame's checksum as it goes."""
    import zstandard

    done = 0
    with open(source, "rb") as f, open(dest, "wb") as out:
        reader = zstandard.ZstdDecompressor().stream_reader(f)
        while block := reader.read(8 * CHUNK):
            out.write(block)
            done += len(block)
            progress(done)
    return done


def compress(source: Path, dest: Path, level: int = LEVEL, window_log: int = WINDOW_LOG) -> None:
    """Compress a file as package_prebuilt.py does: zstd with a checksum and the content size, on all cores."""
    import zstandard

    params = zstandard.ZstdCompressionParameters.from_level(level, window_log=window_log, enable_ldm=True,
                                                            threads=-1, write_checksum=True,
                                                            write_content_size=True)
    with open(source, "rb") as f, open(dest, "wb") as out:
        zstandard.ZstdCompressor(compression_params=params).copy_stream(f, out, size=source.stat().st_size)


def check_database(path: Path, release: str, db_format: int) -> None:
    """Raise ValueError unless `path` is a database of `release` in layout `db_format`."""
    try:
        con = duckdb.connect(str(path), read_only=True)
        try:
            info = dict(con.execute("SELECT key, value FROM _build_info").fetchall())
        finally:
            con.close()
    except duckdb.Error as e:
        raise ValueError(f"the downloaded database cannot be opened: {e}") from None
    if info.get("release") != release or int(info.get("db_format", 1)) != db_format:
        raise ValueError(f"the downloaded database is release {info.get('release')}, layout "
                         f"{info.get('db_format', 1)}, not release {release}, layout {db_format}")


def fetch(info: dict[str, Any], release: str, folder: Path, targets: dict[str, Path], db_format: int,
          progress: Callable[[int, int], None], log: Callable[[str], None] = print) -> None:
    """Download, check and decompress a release's files (`info`: Mirror.release) into `targets` (by kind), the
    database last, so that it is complete only once both are there. Raises on any failure, leaving the
    compressed download (.part) to resume and nothing half-written under the target names."""
    total = download_size(info)
    base = 0
    zst: dict[str, Path] = {}
    for kind in KINDS:
        f = info["files"][kind]
        dest = folder / f"bindingdb_{release}.{kind}.zst"
        size, start = int(f["size"]), time.monotonic()
        if not (dest.is_file() and dest.stat().st_size == size):
            _download(f["url"], dest, size, lambda n, b=base: progress(b + n, total))
            log(f"  downloaded {file_names(release)[kind]} ({size / 1e6:.0f} MB) in {time.monotonic() - start:.0f}s")
        if sha256(dest) != f["sha256"]:
            dest.unlink()
            raise ValueError(f"{file_names(release)[kind]} does not match the SHA-256 in {release}.json (deleted; "
                             "downloaded again on the next try)")
        zst[kind] = dest
        base += size
    for kind in KINDS:  # the index first: the release counts as complete once the database is there too
        f, target = info["files"][kind], targets[kind]
        tmp = target.with_name(target.name + ".download")  # not .building: a local build's
        try:
            size = decompress(zst[kind], tmp)
            if f.get("raw_size") is not None and size != int(f["raw_size"]):
                raise ValueError(f"{file_names(release)[kind]} decompressed to {size:,} bytes, not "
                                 f"{int(f['raw_size']):,}")
            if kind == "duckdb":
                check_database(tmp, release, db_format)
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
        tmp.replace(target)
    for path in zst.values():
        path.unlink(missing_ok=True)


def release_info(release: str, build_info: dict[str, str], files: dict[str, dict[str, Any]],
                 packaged_by: str) -> dict[str, Any]:
    """A release's .json: its build info, and its compressed files' size, sha256 and raw_size."""
    return {"release": release, "db_format": int(build_info.get("db_format", 1)),
            "built_at": build_info.get("built_at"), "source_zip_sha256": build_info.get("source_zip_sha256"),
            "packaged_by": packaged_by, "files": {k: files[k] for k in KINDS}}
