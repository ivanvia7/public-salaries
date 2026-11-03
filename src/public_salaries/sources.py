import tomllib
from importlib.resources import files

SOURCE_DIR = files("public_salaries") / "sources"


def slugs() -> list[str]:
    return sorted(
        path.name.removesuffix(".toml")
        for path in SOURCE_DIR.iterdir()
        if path.name.endswith(".toml")
    )


def require(wanted: list[str]) -> None:
    """Raise one error naming every unknown slug and the known ones."""
    known = slugs()
    unknown = sorted(set(wanted) - set(known))
    if unknown:
        raise ValueError(
            f"unknown source {', '.join(unknown)}; known: {', '.join(known)}"
        )


def load(slug: str) -> dict:
    require([slug])
    path = SOURCE_DIR / f"{slug}.toml"
    return tomllib.loads(path.read_text(encoding="utf-8"))
