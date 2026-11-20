"""Check cached rows against the same rows read fresh from each portal.

Usage: uv run scripts/verify_sample.py [--cache PATH] [--size 80] [--seed 20261120]

The expected values are built here from the raw portal columns, on purpose
without the source files or to_salary, so a wrong mapping in the tool shows
up as a mismatch instead of agreeing with itself.
"""

import argparse
import json
import random
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

from public_salaries.api import default_cache_path

PORTALS = {
    "new_york": ("data.cityofnewyork.us", "k397-673e", ":id"),
    "san_francisco": ("data.sf.gov", "88g8-5mnd", ":id"),
    "massachusetts": ("cthru.data.socrata.com", "9ttk-7vz6", "id"),
}


def portal_rows(slug: str, source_id: str) -> list[dict]:
    host, dataset, id_column = PORTALS[slug]
    query = urllib.parse.urlencode(
        {"$select": "*, :id", "$where": f"{id_column} = '{source_id}'"}
    )
    url = f"https://{host}/resource/{dataset}.json?{query}"
    for attempt in range(1, 5):
        try:
            with urllib.request.urlopen(url, timeout=90) as response:
                return json.load(response)
        except OSError:
            if attempt == 4:
                raise
            time.sleep(5 * attempt)
    return []


def money(value: str | None) -> float | None:
    return None if value in (None, "") else float(value)


def joined(row: dict, *columns: str) -> str | None:
    parts = [row[column].strip() for column in columns if row.get(column, "").strip()]
    return " ".join(parts) or None


def expected(slug: str, row: dict) -> dict:
    if slug == "new_york":
        parts = [
            money(row.get(column))
            for column in ("regular_gross_paid", "total_ot_paid", "total_other_pay")
        ]
        present = [part for part in parts if part is not None]
        return {
            "year": int(row["fiscal_year"][:4]),
            "name": joined(row, "first_name", "mid_init", "last_name"),
            "title": row.get("title_description"),
            "department": row.get("agency_name"),
            "base_pay": parts[0],
            "overtime_pay": parts[1],
            "other_pay": parts[2],
            "total_pay": round(sum(present), 2) if present else None,
        }
    if slug == "san_francisco":
        return {
            "year": int(row["year"][:4]),
            "name": row.get("employee_identifier"),
            "title": row.get("job"),
            "department": row.get("department"),
            "base_pay": money(row.get("salaries")),
            "overtime_pay": money(row.get("overtime")),
            "other_pay": money(row.get("other_salaries")),
            "total_pay": money(row.get("total_salary")),
        }
    return {
        "year": int(row["year"][:4]),
        "name": joined(row, "name_first", "name_last"),
        "title": row.get("position_title"),
        "department": row.get("department_division"),
        "base_pay": money(row.get("pay_base_actual")),
        "overtime_pay": money(row.get("pay_overtime_actual")),
        "other_pay": money(row.get("pay_other_actual")),
        "total_pay": money(row.get("pay_total_actual")),
    }


def same(ours: object, theirs: object) -> bool:
    if isinstance(ours, float) and isinstance(theirs, float):
        return abs(ours - theirs) < 0.005
    return ours == theirs


def check(conn: sqlite3.Connection, slug: str, size: int, seed: int) -> int:
    """Print every mismatch; returns the number of wrong rows."""
    query = "SELECT source_id FROM salaries WHERE source = ? ORDER BY source_id"
    ids = [row[0] for row in conn.execute(query, (slug,))]
    if len(ids) < size:
        print(f"{slug}: only {len(ids)} cached rows, fetch more or lower --size")
        return size

    wrong = 0
    for source_id in random.Random(seed).sample(ids, size):
        ours = conn.execute(
            "SELECT * FROM salaries WHERE source = ? AND source_id = ?",
            (slug, source_id),
        ).fetchone()
        found = portal_rows(slug, source_id)
        if len(found) != 1:
            print(f"  {slug} {source_id}: {len(found)} rows on the portal")
            wrong += 1
            continue
        mismatches = {
            field: (ours[field], value)
            for field, value in expected(slug, found[0]).items()
            if not same(ours[field], value)
        }
        if mismatches:
            print(f"  {slug} {source_id}: ours, portal = {mismatches}")
            wrong += 1
    print(f"{slug}: {size - wrong} of {size} rows match the portal")
    return wrong


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache", type=Path, default=default_cache_path())
    parser.add_argument("--size", type=int, default=80)
    parser.add_argument("--seed", type=int, default=20261120)
    args = parser.parse_args(argv)
    if args.size < 1:
        parser.error("--size must be 1 or more")

    if not args.cache.is_file():
        raise SystemExit(f"no cache at {args.cache}; run fetch first")
    conn = sqlite3.connect(args.cache)
    conn.row_factory = sqlite3.Row
    try:
        cached = [
            row[0] for row in conn.execute("SELECT DISTINCT source FROM salaries")
        ]
    except sqlite3.DatabaseError as error:
        raise SystemExit(
            f"{args.cache} is not a public-salaries cache: {error}"
        ) from None
    slugs = sorted(slug for slug in cached if slug in PORTALS)
    if not slugs:
        raise SystemExit(f"{args.cache} holds no rows from a known source")
    wrong = sum(check(conn, slug, args.size, args.seed) for slug in slugs)
    raise SystemExit(1 if wrong else 0)


if __name__ == "__main__":
    main()
