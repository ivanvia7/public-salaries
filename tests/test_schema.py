import json
from pathlib import Path

import pytest

from public_salaries.schema import COLUMNS, money, to_salary, year_of

FIXTURES = Path(__file__).parent / "fixtures"

# Piece 3 moves these two dicts into sources/nyc.toml and sources/sf.toml.
NYC = {
    "slug": "nyc",
    "employer": "City of New York",
    "columns": {
        "source_id": ":id",
        "year": "fiscal_year",
        "name": ["first_name", "mid_init", "last_name"],
        "title": "title_description",
        "department": "agency_name",
        "base_pay": "regular_gross_paid",
        "overtime_pay": "total_ot_paid",
        "other_pay": "total_other_pay",
    },
}
SF = {
    "slug": "sf",
    "employer": "City and County of San Francisco",
    "columns": {
        "source_id": ":id",
        "year": "year",
        "name": "employee_identifier",
        "title": "job",
        "department": "department",
        "base_pay": "salaries",
        "overtime_pay": "overtime",
        "other_pay": "other_salaries",
        "total_pay": "total_salary",
    },
}


def rows(name: str) -> list[dict]:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_money_and_year_helpers():
    assert money("$95,897.00") == 95897.0
    assert money("") is None
    assert year_of("2025-06-30T00:00:00.000") == 2025
    with pytest.raises(ValueError, match="unreadable"):
        year_of("FY25")


def test_nyc_total_is_the_sum_of_its_parts():
    pay = [to_salary(NYC, row) for row in rows("nyc")]
    assert pay[1].name == "MATTHEW P OTERO"
    assert pay[1].total_pay == 108186.13


def test_sf_keeps_its_own_total():
    pay = [to_salary(SF, row) for row in rows("sf")]
    assert pay[2].total_pay == 98986.87
    assert {p.year for p in pay} == {2025}
    assert len(COLUMNS) == 11
