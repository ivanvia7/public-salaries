import sqlite3
from collections.abc import Iterable
from dataclasses import astuple
from pathlib import Path

from public_salaries.schema import COLUMNS, Salary

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS salaries (
    {", ".join(COLUMNS)},
    PRIMARY KEY (source, source_id)
);
CREATE TABLE IF NOT EXISTS fetched_years (
    source TEXT NOT NULL,
    year INTEGER NOT NULL,
    rows INTEGER NOT NULL,
    PRIMARY KEY (source, year)
);
"""


def open_cache(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def save_year(
    conn: sqlite3.Connection,
    source: str,
    year: int,
    salaries: Iterable[Salary],
    settled: bool,
) -> int:
    """Replace one source's year; :id can change when a portal republishes."""
    rows = [astuple(s) for s in salaries]
    marks = ", ".join("?" for _ in COLUMNS)
    with conn:
        conn.execute(
            "DELETE FROM salaries WHERE source = ? AND year = ?", (source, year)
        )
        conn.executemany(f"INSERT OR REPLACE INTO salaries VALUES ({marks})", rows)
        if settled:
            conn.execute(
                "INSERT OR REPLACE INTO fetched_years VALUES (?, ?, ?)",
                (source, year, len(rows)),
            )
    return len(rows)


def is_fetched(conn: sqlite3.Connection, source: str, year: int) -> bool:
    query = "SELECT 1 FROM fetched_years WHERE source = ? AND year = ?"
    return conn.execute(query, (source, year)).fetchone() is not None
