"""Load BindingDB's MySQL dump straight into DuckDB, without a MySQL server.

The dump (mysqldump output) is read as a stream, from the zip or the unzipped .dmp: each CREATE TABLE becomes
a DuckDB table with the same columns (MySQL types mapped as DuckDB's mysql extension maps them). Each extended
INSERT is rewritten as CSV lines (MySQL's backslash escapes turned into doubled quotes, one line per row) into
a temporary file per table, which DuckDB's CSV reader then loads: running the INSERTs themselves through
DuckDB's SQL parser is about 20 times slower. The tables with passwords and personal contact details
(PII_TABLES) are skipped.
"""

from __future__ import annotations

import io
import re
import tempfile
import zipfile
from pathlib import Path
from typing import IO, Callable, Iterator

import duckdb

# Tables holding passwords or personal contact details; never copied.
PII_TABLES = {"regusers", "person"}

_CREATE = re.compile(r"CREATE TABLE `(\w+)` \(")
_COLUMN = re.compile(r"^\s+`(\w+)` (\w+)(?:\((\d+)(?:,(\d+))?\))?( unsigned)?")
_INSERT = re.compile(rb"INSERT INTO `(\w+)` VALUES ")
_ESCAPE = re.compile(rb"\\(.)", re.DOTALL)
# MySQL's escape sequences in quoted strings (https://dev.mysql.com/doc/refman/8.4/en/string-literals.html)
_UNESCAPED = {b"0": b"\x00", b"b": b"\b", b"n": b"\n", b"r": b"\r", b"t": b"\t", b"Z": b"\x1a", b"'": b"''",
              b'"': b'"', b"\\": b"\\", b"%": b"\\%", b"_": b"\\_"}

_TYPES = {"int": "INTEGER", "integer": "INTEGER", "mediumint": "INTEGER", "smallint": "SMALLINT",
          "tinyint": "TINYINT", "bigint": "BIGINT", "float": "FLOAT", "double": "DOUBLE", "real": "DOUBLE",
          "date": "DATE", "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP", "time": "TIME", "year": "INTEGER",
          "char": "VARCHAR", "varchar": "VARCHAR", "tinytext": "VARCHAR", "text": "VARCHAR",
          "mediumtext": "VARCHAR", "longtext": "VARCHAR", "enum": "VARCHAR", "set": "VARCHAR", "json": "VARCHAR",
          "blob": "BLOB", "longblob": "BLOB", "mediumblob": "BLOB", "binary": "BLOB", "varbinary": "BLOB"}
_UNSIGNED = {"TINYINT": "UTINYINT", "SMALLINT": "USMALLINT", "INTEGER": "UINTEGER", "BIGINT": "UBIGINT"}


def duckdb_type(mysql_type: str, precision: str | None, scale: str | None, unsigned: bool) -> str:
    t = mysql_type.lower()
    if t in ("decimal", "numeric"):
        return f"DECIMAL({precision or 10},{scale or 0})"
    if t not in _TYPES:
        raise ValueError(f"unsupported MySQL column type {mysql_type!r}")
    duck = _TYPES[t]
    return _UNSIGNED.get(duck, duck) if unsigned else duck


def _unescape(m: re.Match[bytes]) -> bytes:
    return _UNESCAPED.get(m.group(1), m.group(1))


def open_dump(path: Path) -> IO[bytes]:
    """The dump as a binary stream: the .dmp member of a zip (read without unpacking it), or the file."""
    if path.suffix == ".zip":
        archive = zipfile.ZipFile(path)
        name = next(n for n in archive.namelist() if n.endswith(".dmp"))
        return archive.open(name)
    return open(path, "rb")


def dump_size(path: Path) -> int:
    """Bytes the dump stream will yield (for progress)."""
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            return next(i.file_size for i in archive.infolist() if i.filename.endswith(".dmp"))
    return path.stat().st_size


def _statements(stream: IO[bytes]) -> Iterator[tuple[bytes, int]]:
    """The dump's lines (each INSERT is one line), with the bytes read so far."""
    done = 0
    for line in io.BufferedReader(stream, 1 << 20):  # type: ignore[arg-type]
        done += len(line)
        yield line, done


def rows_as_csv(values: bytes) -> bytes:
    """An INSERT's VALUES list, "(1,'a''b',NULL),(2,...)" after unescaping, as CSV lines "1,'a''b',NULL\n2,...".
    Rows end at "),(" outside quotes: a split inside a string leaves an odd number of quotes before it."""
    parts = values[1:-1].split(b"),(")
    if not any(p.count(b"'") & 1 for p in parts):
        return b"\n".join(parts) + b"\n"
    rows, pending = [], None
    for part in parts:
        pending = part if pending is None else pending + b"),(" + part
        if not pending.count(b"'") & 1:
            rows.append(pending)
            pending = None
    if pending is not None:
        raise ValueError("unbalanced quotes in an INSERT")
    return b"\n".join(rows) + b"\n"


def load(dump: Path, con: duckdb.DuckDBPyConnection,
         progress: Callable[[int, int, str], None] | None = None) -> dict[str, int]:
    """Create the dump's tables (except PII_TABLES) in `con` and fill them; returns rows per table.
    `progress(bytes_done, bytes_total, table)` is called after each INSERT statement."""
    total = dump_size(dump)
    counts: dict[str, int] = {}
    types: dict[str, dict[str, str]] = {}
    table: str | None = None
    columns: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="bindingdb-load-") as tmp, open_dump(dump) as stream:
        csv_table: str | None = None
        csv_file: IO[bytes] | None = None

        def flush() -> None:  # load the finished table's CSV
            nonlocal csv_table, csv_file
            if csv_file is None:
                return
            csv_file.close()
            spec = ", ".join(f"'{c}': '{t}'" for c, t in types[csv_table].items())
            con.execute(f"""INSERT INTO "{csv_table}" SELECT * FROM read_csv(?, columns = {{{spec}}}, header = false,
                            delim = ',', quote = '''', escape = '''', nullstr = 'NULL', allow_quoted_nulls = false,
                            new_line = '\\n', strict_mode = true, parallel = true)""", [csv_file.name])
            Path(csv_file.name).unlink()
            csv_table = csv_file = None

        for line, done in _statements(stream):
            if line.startswith(b"INSERT INTO "):
                m = _INSERT.match(line)
                if m is None:
                    raise ValueError(f"unexpected INSERT: {line[:80]!r}")
                name = m.group(1).decode()
                if name in PII_TABLES:
                    continue
                if name != csv_table:
                    flush()
                    csv_table, csv_file = name, open(Path(tmp) / f"{name}.csv", "wb")  # noqa: SIM115
                values = _ESCAPE.sub(_unescape, line[m.end():].rstrip().rstrip(b";"))
                csv_file.write(rows_as_csv(values))
                if progress:
                    progress(done, total, name)
                continue
            if csv_file is not None:
                flush()
            text = line.decode("utf-8")
            if table is None:
                if m := _CREATE.match(text):
                    table, columns = m.group(1), {}
                continue
            if text.startswith(")"):  # end of CREATE TABLE
                if table not in PII_TABLES:
                    defs = ", ".join(f'"{c}" {t}' for c, t in columns.items())
                    con.execute(f'CREATE TABLE "{table}" ({defs})')
                    types[table] = columns
                    counts[table] = 0
                table = None
            elif m := _COLUMN.match(text):
                columns[m.group(1)] = duckdb_type(m.group(2), m.group(3), m.group(4), bool(m.group(5)))
        flush()
    for name in counts:
        counts[name] = con.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
    return counts
