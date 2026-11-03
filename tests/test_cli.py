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
