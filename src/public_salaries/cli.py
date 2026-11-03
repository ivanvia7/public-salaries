import argparse
from importlib.metadata import version
from pathlib import Path

from public_salaries import api, cache, sources


def parse_years(text: str) -> list[int]:
    """'2024' -> [2024]; '2020-2024' -> [2020, 2021, 2022, 2023, 2024]."""
    first, _, last = text.partition("-")
    if not first.isdigit() or not (last or first).isdigit():
        raise argparse.ArgumentTypeError(f"not a year or year range: {text!r}")
    return list(range(int(first), int(last or first) + 1))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="public-salaries")
    parser.add_argument(
        "--version", action="version", version=version("public-salaries")
    )
    commands = parser.add_subparsers(dest="command", required=True)

    fetch = commands.add_parser("fetch", help="fetch pay rows into the local cache")
    fetch.add_argument("--source", required=True, help="comma list, e.g. new_york")
    fetch.add_argument(
        "--years", required=True, type=parse_years, help="2024 or 2020-2024"
    )
    fetch.add_argument("--cache", type=Path, default=api.default_cache_path())
    fetch.set_defaults(run=fetch_command)

    stats = commands.add_parser("stats", help="rows and years per cached source")
    stats.add_argument("--cache", type=Path, default=api.default_cache_path())
    stats.set_defaults(run=stats_command)

    commands.add_parser("sources", help="list source slugs").set_defaults(
        run=lambda parser, args: print("\n".join(sources.slugs()))
    )
    return parser


def fetch_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    slugs = [slug.strip() for slug in args.source.split(",")]

    known = sources.slugs()
    unknown = sorted(set(slugs) - set(known))
    if unknown:
        parser.error(f"unknown source {', '.join(unknown)}; known: {', '.join(known)}")

    conn = cache.open_cache(args.cache)
    for slug in slugs:
        rows, skipped = api.fetch(conn, slug, args.years)
        print(f"{slug}: {rows} rows read, {len(skipped)} unreadable rows skipped")
        if skipped:
            print(f"  first skipped: {skipped[0][:300]}")


def stats_command(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if not args.cache.is_file():
        parser.error(f"no cache at {args.cache}; run fetch first")

    rows = cache.source_stats(cache.open_cache(args.cache))
    if not rows:
        print(f"{args.cache} holds no salaries")
    for row in rows:
        print(
            f"{row['source']}: {row['rows']} rows, {row['first_year']} to"
            f" {row['last_year']}, {row['with_total']:.1%} with total pay"
        )


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.run(parser, args)
    except RuntimeError as error:
        # Portal trouble is not a bug in this tool; one line says what failed where.
        raise SystemExit(f"error: {error}") from None
