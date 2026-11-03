import pytest

from public_salaries.cli import main


@pytest.fixture(autouse=True)
def no_wait(monkeypatch):
    """Tests hit mocked portals, so the polite gap between requests only slows them."""
    monkeypatch.setattr("public_salaries.portals.http.MIN_GAP_SECONDS", 0)


@pytest.fixture
def run_cli(capsys):
    """Run the CLI in-process; returns exit code, stdout and stderr."""

    def run(*args: str) -> tuple[int | str | None, str, str]:
        try:
            main(list(args))
            code = 0
        except SystemExit as error:
            code = error.code
        out = capsys.readouterr()
        return code, out.out, out.err

    return run
