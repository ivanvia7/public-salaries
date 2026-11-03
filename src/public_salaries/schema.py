from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class Salary:
    source: str
    source_id: str
    year: int
    employer: str
    name: str | None
    title: str | None
    department: str | None
    base_pay: float | None
    overtime_pay: float | None
    other_pay: float | None
    total_pay: float | None


COLUMNS = tuple(f.name for f in fields(Salary))


def money(value: str | float | None) -> float | None:
    """'95,897.00' or '$1,200' -> a float; blank -> None."""

    if value in (None, ""):
        return None
    return float(str(value).replace("$", "").replace(",", ""))


def year_of(value: str) -> int:
    """'2025' or '2025-06-30T00:00:00.000' -> 2025."""

    if not value[:4].isdigit():
        raise ValueError(f"unreadable year {value!r}")
    return int(value[:4])


def column_text(row: dict, source: str | list[str] | None) -> str | None:
    """A list of columns is joined with spaces, e.g. first + middle + last name."""

    if source is None:
        return None
    if isinstance(source, str):
        return row.get(source)
    parts = [row[name] for name in source if row.get(name)]
    return " ".join(parts) or None


def required_text(row: dict, column: str) -> str:

    value = row.get(column)
    if value in (None, ""):
        raise ValueError(f"blank {column}")
    return str(value)


def total(given: float | None, *parts: float | None) -> float | None:
    """The source's own total; else the sum of the parts it publishes."""

    if given is not None:
        return given
    present = [p for p in parts if p is not None]
    return round(sum(present), 2) if present else None


def to_salary(source: dict, row: dict) -> Salary:
    col = source["columns"]

    def text(name: str) -> str | None:
        return column_text(row, col.get(name))

    base = money(text("base_pay"))
    overtime = money(text("overtime_pay"))
    other = money(text("other_pay"))

    return Salary(
        source=source["slug"],
        source_id=required_text(row, col["source_id"]),
        year=year_of(required_text(row, col["year"])),
        employer=text("employer") or source["employer"],
        name=text("name"),
        title=text("title"),
        department=text("department"),
        base_pay=base,
        overtime_pay=overtime,
        other_pay=other,
        total_pay=total(money(text("total_pay")), base, overtime, other),
    )
