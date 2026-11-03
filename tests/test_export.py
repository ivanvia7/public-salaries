import csv
import json
from pathlib import Path

import pytest

from public_salaries import cache, export, sources
from public_salaries.schema import COLUMNS, to_salary

FIXTURE = json.loads((Path(__file__).parent / "fixtures" / "sf.json").read_text())


@pytest.fixture
def conn(tmp_path):
    """A cache holding the 3 San Francisco fixture rows for 2025."""
    source = sources.load("san_francisco")
    salaries = [to_salary(source, row) for row in FIXTURE]

    conn = cache.open_cache(tmp_path / "cache.db")
    cache.save_year(conn, "san_francisco", 2025, salaries, settled=True)
    return conn


@pytest.mark.parametrize("suffix", [".csv", ".jsonl", ".db", ".parquet"])
def test_every_format_writes_every_row(conn, tmp_path, suffix):
    path = tmp_path / f"out{suffix}"
    assert export.export(conn, ["san_francisco"], [2025], path) == 3
    assert path.stat().st_size > 0


def test_csv_has_header_and_excel_mark(conn, tmp_path):
    path = tmp_path / "out.csv"
    export.export(conn, ["san_francisco"], [2025], path)

    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    with path.open(encoding="utf-8-sig", newline="") as file:
        header, *rows = csv.reader(file)
    assert header == list(COLUMNS)
    assert len(rows) == 3


def test_jsonl_keeps_pay_as_numbers(conn, tmp_path):
    path = tmp_path / "out.jsonl"
    export.export(conn, ["san_francisco"], [2025], path)

    first = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert first["name"] == "Ofelia Ruiz"
    assert first["total_pay"] == 98986.87


def test_other_years_are_left_out(conn, tmp_path):
    assert export.export(conn, ["san_francisco"], [2024], tmp_path / "out.csv") == 0
