import json
from datetime import date
from pathlib import Path

import httpx
import respx

from public_salaries import api, cache

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sf.json").read_text())
URL = "https://data.sf.gov/resource/88g8-5mnd.json"
THIS_YEAR = date.today().year


def in_year(year: int) -> list[dict]:
    """The fixture rows moved to another year."""
    return [{**row, "year": str(year)} for row in FIXTURE]


def count_rows(conn) -> int:
    return conn.execute("SELECT count(*) FROM salaries").fetchone()[0]


@respx.mock
def test_second_fetch_makes_no_requests(tmp_path):
    route = respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    conn = cache.open_cache(tmp_path / "cache.db")

    assert api.fetch(conn, "san_francisco", [2025]) == (3, [])
    assert api.fetch(conn, "san_francisco", [2025]) == (0, [])
    assert route.call_count == 1


@respx.mock
def test_current_year_is_read_again(tmp_path):
    rows = in_year(THIS_YEAR)
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(200, json=rows), httpx.Response(200, json=rows[:1])]
    )
    conn = cache.open_cache(tmp_path / "cache.db")

    api.fetch(conn, "san_francisco", [THIS_YEAR])
    api.fetch(conn, "san_francisco", [THIS_YEAR])
    assert route.call_count == 2
    assert count_rows(conn) == 1


@respx.mock
def test_bad_row_is_skipped_and_year_stays_open(tmp_path):
    bad = {**FIXTURE[0], ":id": "row-bad", "salaries": "n/a"}
    respx.get(URL).mock(return_value=httpx.Response(200, json=[*FIXTURE, bad]))
    conn = cache.open_cache(tmp_path / "cache.db")

    rows, skipped = api.fetch(conn, "san_francisco", [2025])
    assert rows == 3
    assert len(skipped) == 1
    assert skipped[0].startswith(
        "ValueError(\"could not convert string to float: 'n/a'"
    )
    assert not cache.is_fetched(conn, "san_francisco", 2025)
