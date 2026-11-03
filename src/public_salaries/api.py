import os
import sqlite3
from collections.abc import Iterable, Iterator
from datetime import date
from pathlib import Path

from public_salaries import cache, sources
from public_salaries.portals import PORTALS
from public_salaries.schema import Salary, to_salary


def default_cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache"
    return Path(base) / "public-salaries" / "cache.db"


def parse_rows(
    source: dict, rows: Iterator[dict], skipped: list[str]
) -> Iterator[Salary]:
    """One unreadable row is skipped and noted, not allowed to stop the fetch."""
    for row in rows:
        try:
            yield to_salary(source, row)
        except (KeyError, TypeError, ValueError) as error:
            skipped.append(f"{error!r} in {row}")


def fetch_year(
    conn: sqlite3.Connection, source: dict, year: int, skipped: list[str]
) -> int:
    rows = PORTALS[source["portal"]].read_year(source, year)
    before = len(skipped)
    salaries = list(parse_rows(source, rows, skipped))
    # ponytail: the current year is still being paid, so it is re-read every fetch.
    settled = year < date.today().year and len(skipped) == before and bool(salaries)
    return cache.save_year(conn, source["slug"], year, salaries, settled)


def fetch(
    conn: sqlite3.Connection, slug: str, years: Iterable[int]
) -> tuple[int, list[str]]:
    """Fetch every year not already cached; returns rows saved and rows skipped."""
    source = sources.load(slug)
    fetched = 0
    skipped: list[str] = []
    for year in years:
        if cache.is_fetched(conn, slug, year):
            continue
        try:
            fetched += fetch_year(conn, source, year, skipped)
        except (RuntimeError, ValueError) as error:
            raise RuntimeError(f"{slug} {year}: {error}") from error
    return fetched, skipped
