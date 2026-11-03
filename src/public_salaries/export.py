import csv
import json
import sqlite3
import tempfile
from collections.abc import Iterator
from pathlib import Path

from public_salaries.cache import SCHEMA
from public_salaries.schema import COLUMNS

PARQUET_TYPES = {
    "year": "INTEGER",
    "base_pay": "DOUBLE",
    "overtime_pay": "DOUBLE",
    "other_pay": "DOUBLE",
    "total_pay": "DOUBLE",
}


def select_rows(
    conn: sqlite3.Connection, slugs: list[str], years: list[int]
) -> Iterator[tuple]:
    source_marks = ", ".join("?" for _ in slugs)
    year_marks = ", ".join("?" for _ in years)

    query = (
        f"SELECT * FROM salaries WHERE source IN ({source_marks})"
        f" AND year IN ({year_marks}) ORDER BY source, year, source_id"
    )
    return conn.execute(query, (*slugs, *years))


def to_csv(rows: Iterator[tuple], path: Path) -> int:
    count = 0

    # utf-8-sig adds the byte-order mark Excel needs to read UTF-8.
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(COLUMNS)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def to_jsonl(rows: Iterator[tuple], path: Path) -> int:
    count = 0

    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            record = dict(zip(COLUMNS, row, strict=True))
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
            count += 1
    return count


def to_sqlite(rows: Iterator[tuple], path: Path) -> int:
    path.unlink(missing_ok=True)
    out = sqlite3.connect(path)
    marks = ", ".join("?" for _ in COLUMNS)

    with out:
        out.executescript(SCHEMA)
        count = out.executemany(f"INSERT INTO salaries VALUES ({marks})", rows).rowcount
    out.close()
    return count


def to_parquet(rows: Iterator[tuple], path: Path) -> int:
    import duckdb  # only needed here; plain installs skip it

    columns = {column: PARQUET_TYPES.get(column, "VARCHAR") for column in COLUMNS}
    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / "rows.jsonl"
        count = to_jsonl(rows, staged)
        duckdb.sql(
            f"COPY (SELECT * FROM read_json({sql_text(staged)}, columns={columns}))"
            f" TO {sql_text(path)} (FORMAT parquet, COMPRESSION zstd)"
        )
    return count


def sql_text(path: Path) -> str:
    """Quote a path for duckdb SQL, which takes no parameters in COPY."""
    return "'" + str(path).replace("'", "''") + "'"


WRITERS = {".csv": to_csv, ".jsonl": to_jsonl, ".db": to_sqlite, ".parquet": to_parquet}


def export(
    conn: sqlite3.Connection, slugs: list[str], years: list[int], path: Path
) -> int:
    writer = WRITERS.get(path.suffix)
    if writer is None:
        raise ValueError(f"--out must end with one of {', '.join(WRITERS)}")
    return writer(select_rows(conn, slugs, years), path)
