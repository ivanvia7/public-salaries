import os
from collections.abc import Iterator

from public_salaries.portals.http import get_json

PAGE_SIZE = 50_000


def auth_headers() -> dict[str, str]:
    token = os.environ.get("SOCRATA_APP_TOKEN")
    return {"X-App-Token": token} if token else {}


def resource_url(host: str, dataset: str) -> str:
    return f"https://{host}/resource/{dataset}.json"


def read(host: str, dataset: str, where: str, select: str = "*") -> Iterator[dict]:
    offset = 0

    while True:
        params = {
            "$select": select,
            "$where": where,
            "$order": ":id",
            "$limit": str(PAGE_SIZE),
            "$offset": str(offset),
        }
        page = get_json(resource_url(host, dataset), params, auth_headers())
        yield from page

        if len(page) < PAGE_SIZE:
            return
        offset += PAGE_SIZE


def year_filter(source: dict, year: int) -> str:
    where = f"{source['columns']['year']} = '{year}'"
    extra = source.get("where")
    return f"{where} AND {extra}" if extra else where


def count_year(source: dict, year: int) -> int:
    """Rows the portal holds for one year, counted there, not fetched."""
    params = {"$select": "count(*) AS n", "$where": year_filter(source, year)}
    (row,) = get_json(
        resource_url(source["host"], source["dataset"]), params, auth_headers()
    )
    return int(row["n"])


def read_year(source: dict, year: int) -> Iterator[dict]:
    # Neither city has a row id of its own; the portal's :id is asked for by name.
    source_id = source["columns"]["source_id"]
    select = f"*, {source_id}" if source_id.startswith(":") else "*"
    where = year_filter(source, year)
    yield from read(source["host"], source["dataset"], where, select)


def sample(source: dict, columns: list[str], size: int) -> list[dict]:
    """The newest rows; the portal rejects a column it does not have."""
    params = {
        "$select": ", ".join(columns),
        "$order": f"{source['columns']['year']} DESC",
        "$limit": str(size),
    }
    if "where" in source:
        params["$where"] = source["where"]

    url = resource_url(source["host"], source["dataset"])
    return get_json(url, params, auth_headers())
