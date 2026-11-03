import tomllib
from importlib.resources import files

SOURCE_DIR = files("public_salaries") / "sources"


def slugs() -> list[str]:
    return sorted(
        path.name.removesuffix(".toml")
        for path in SOURCE_DIR.iterdir()
        if path.name.endswith(".toml")
    )


def load(slug: str) -> dict:
    path = SOURCE_DIR / f"{slug}.toml"
    if not path.is_file():
        raise ValueError(f"unknown source {slug!r}; known: {', '.join(slugs())}")
    return tomllib.loads(path.read_text(encoding="utf-8"))
