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
    salaries = list(parse_rows(source, rows, skipped))

    # The current year is still being paid, so it is read again on every fetch.
    settled = year < date.today().year and not skipped and bool(salaries)
    return cache.save_year(conn, source["slug"], year, salaries, settled)


def fetch(
    conn: sqlite3.Connection, slug: str, years: Iterable[int], refresh: bool = False
) -> Iterator[tuple[int, int | None, list[str]]]:
    """Per year: rows saved (None when cached) and the rows skipped.

    A settled year is not read again unless refresh is set, because portals
    sometimes republish an old year.
    """
    source = sources.load(slug)

    for year in years:
        if not refresh and cache.is_fetched(conn, slug, year):
            yield year, None, []
            continue
        skipped: list[str] = []
        try:
            rows = fetch_year(conn, source, year, skipped)
        except (RuntimeError, ValueError) as error:
            raise RuntimeError(f"{slug} {year}: {error}") from error
        yield year, rows, skipped
