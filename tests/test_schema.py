import json
from pathlib import Path

import pytest

from public_salaries import sources
from public_salaries.schema import COLUMNS, money, to_salary, year_of

FIXTURES = Path(__file__).parent / "fixtures"


def rows(name: str) -> list[dict]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_money_and_year_helpers():
    assert money("$95,897.00") == 95897.0
    assert money("") is None
    assert year_of("2025-06-30T00:00:00.000") == 2025
    with pytest.raises(ValueError, match="unreadable"):
        year_of("FY25")


def test_nyc_total_is_the_sum_of_its_parts():
    pay = [to_salary(sources.load("new_york"), row) for row in rows("nyc")]
    assert pay[1].name == "MATTHEW P OTERO"
    assert pay[1].total_pay == 108186.13


def test_sf_keeps_its_own_total():
    pay = [to_salary(sources.load("san_francisco"), row) for row in rows("sf")]
    assert pay[2].total_pay == 98986.87
    assert {p.year for p in pay} == {2025}
    assert len(COLUMNS) == 11


def test_every_source_file_has_the_required_keys():
    assert sources.slugs() == ["new_york", "san_francisco"]
    for slug in sources.slugs():
        source = sources.load(slug)
        assert source["slug"] == slug
        assert {"source_id", "year"} <= source["columns"].keys()


def test_unknown_source_names_known_ones():
    with pytest.raises(ValueError, match="new_york, san_francisco"):
        sources.load("atlantis")
