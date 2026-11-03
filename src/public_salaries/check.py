from public_salaries import api, sources
from public_salaries.portals import PORTALS

SAMPLE_SIZE = 100


def named_columns(source: dict) -> list[str]:
    """Every portal column the source file names; name can be a list of parts."""
    names: list[str] = []
    for column in source["columns"].values():
        names.extend([column] if isinstance(column, str) else column)
    return names


def check_source(slug: str) -> tuple[int, int]:
    """Read the newest live rows through the source file; returns rows, unreadable."""
    source = sources.load(slug)
    where = f"{slug} ({source['host']} {source['dataset']})"

    try:
        columns = named_columns(source)
        rows = PORTALS[source["portal"]].sample(source, columns, SAMPLE_SIZE)
    except (RuntimeError, KeyError) as error:
        raise RuntimeError(f"{where}: {error!r}") from error
    if not rows:
        raise RuntimeError(f"{where}: portal returned no rows")

    skipped: list[str] = []
    salaries = list(api.parse_rows(source, iter(rows), skipped))
    if not salaries:
        raise RuntimeError(f"{where}: none of {len(rows)} rows readable: {skipped[0]}")
    return len(rows), len(skipped)
