import importlib.util
from pathlib import Path

import pytest

from public_salaries import cache, sources
from public_salaries.schema import to_salary

SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_sample.py"
spec = importlib.util.spec_from_file_location("verify_sample", SCRIPT)
assert spec is not None and spec.loader is not None
verify_sample = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_sample)


def test_a_source_too_small_to_sample_fails(tmp_path):
    rows = [{"year": "2025", ":id": "row-1", "employee_identifier": "A"}]
    source = sources.load("san_francisco")
    conn = cache.open_cache(tmp_path / "cache.db")
    cache.save_year(
        conn, "san_francisco", 2025, [to_salary(source, row) for row in rows], True
    )

    with pytest.raises(SystemExit) as exit_info:
        verify_sample.main(["--cache", str(tmp_path / "cache.db"), "--size", "80"])
    assert exit_info.value.code == 1


def test_a_missing_cache_is_named_not_created(tmp_path):
    path = tmp_path / "cache.db"

    with pytest.raises(SystemExit, match="no cache at"):
        verify_sample.main(["--cache", str(path)])
    assert not path.exists()


def test_an_empty_cache_is_not_a_pass(tmp_path):
    cache.open_cache(tmp_path / "cache.db")

    with pytest.raises(SystemExit, match="holds no rows"):
        verify_sample.main(["--cache", str(tmp_path / "cache.db")])


@pytest.mark.parametrize("size", ["0", "-1"])
def test_a_size_below_one_is_rejected(tmp_path, size):
    with pytest.raises(SystemExit) as exit_info:
        verify_sample.main(["--cache", str(tmp_path / "cache.db"), "--size", size])
    assert exit_info.value.code == 2


def test_a_file_that_is_not_a_cache_is_named(tmp_path):
    path = tmp_path / "cache.db"
    path.write_bytes(b"")

    with pytest.raises(SystemExit, match="not a public-salaries cache"):
        verify_sample.main(["--cache", str(path)])
