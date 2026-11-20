import json
from pathlib import Path

import httpx
import respx

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sf.json").read_text())
URL = "https://data.sf.gov/resource/88g8-5mnd.json"


@respx.mock
def test_check_source_command(run_cli):
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))

    code, out, _ = run_cli("check-source", "san_francisco")

    assert code == 0
    assert out == "ok san_francisco: 3 live rows read, 0 unreadable\n"


def test_fetch_rejects_a_backwards_range(run_cli):
    code, _, err = run_cli("fetch", "--source", "new_york", "--years", "2026-2020")

    assert code == 2
    assert "range runs backwards" in err


def test_fetch_rejects_a_year_before_the_source_starts(run_cli):
    code, _, err = run_cli("fetch", "--source", "massachusetts", "--years", "2009")

    assert code == 2
    assert "massachusetts publishes from 2010, not 2009" in err


def test_fetch_names_every_unknown_source(run_cli):
    code, _, err = run_cli(
        "fetch", "--source", "atlantis,new_york,mars", "--years", "2025"
    )

    assert code == 2
    assert "unknown source atlantis, mars; known:" in err


@respx.mock
def test_fetch_prints_one_line_per_year(run_cli, tmp_path):
    respx.get(URL).mock(
        side_effect=[httpx.Response(200, json=FIXTURE), httpx.Response(200, json=[])]
    )
    cache = str(tmp_path / "cache.db")

    code, out, _ = run_cli(
        "fetch", "--source", "san_francisco", "--years", "2025-2026", "--cache", cache
    )
    assert code == 0
    assert out.splitlines() == [
        "san_francisco 2025: 3 rows read, 0 unreadable rows skipped",
        "san_francisco 2026: no rows on the portal, cached rows kept",
    ]

    code, out, _ = run_cli(
        "fetch", "--source", "san_francisco", "--years", "2025", "--cache", cache
    )
    assert out == "san_francisco 2025: cached, --refresh reads it again\n"


@respx.mock
def test_stats_prints_the_median_of_the_last_year(run_cli, tmp_path):
    respx.get(URL).mock(return_value=httpx.Response(200, json=FIXTURE))
    cache = str(tmp_path / "cache.db")
    run_cli("fetch", "--source", "san_francisco", "--years", "2025", "--cache", cache)

    code, out, _ = run_cli("stats", "--cache", cache)

    totals = sorted(float(row["total_salary"]) for row in FIXTURE)
    assert code == 0
    assert out == (
        "san_francisco: 3 rows, 2025 to 2025, 100.0% with total pay,"
        f" median 2025 total pay ${totals[1]:,.0f}\n"
    )
