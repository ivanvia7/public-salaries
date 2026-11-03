# public-salaries

US public employee pay from states and cities in one table: same columns, read straight from each employer's open-data portal.

Today: New York City, San Francisco and the Commonwealth of Massachusetts, over 10 million pay rows.

```
$ public-salaries fetch --source new_york,san_francisco,massachusetts --years 2025
new_york: 550219 rows read, 0 unreadable rows skipped
san_francisco: 43239 rows read, 0 unreadable rows skipped
massachusetts: 162460 rows read, 0 unreadable rows skipped
$ public-salaries stats
massachusetts: 162460 rows, 2025 to 2025, 100.0% with total pay
new_york: 550219 rows, 2025 to 2025, 100.0% with total pay
san_francisco: 43239 rows, 2025 to 2025, 100.0% with total pay
```

That one fetch took about 5 minutes. Median 2025 total pay: San Francisco $113,683, Massachusetts $63,524, New York $50,573.

## Install

```
pip install public-salaries
public-salaries fetch --source new_york,massachusetts --years 2020-2025 --out pay.csv
public-salaries stats
```

`--out` writes `.csv`, `.jsonl`, `.db` (SQLite) or `.parquet` (needs `pip install "public-salaries[parquet]"`).

## One row per person per year

| Column | Meaning |
|---|---|
| `source` | slug: `new_york`, `san_francisco`, `massachusetts` |
| `source_id` | the source's own row id, or the portal's row id when it has none |
| `year` | pay year as the source publishes it (fiscal or calendar, see below) |
| `employer` | the government that paid |
| `name` | as published |
| `title` | job title |
| `department` | agency or department |
| `base_pay` | regular pay actually paid in the year |
| `overtime_pay` | overtime paid |
| `other_pay` | other pay the source lists |
| `total_pay` | the source's own total; when it has none, base + overtime + other |

## Good to know

- New York years are fiscal years (July to June). The source has no total column, so `total_pay` is the sum of the parts.
- New York's `base_salary` column is a rate per year, day or hour; `base_pay` uses `regular_gross_paid` instead.
- New York fiscal 2026 has no agency names in the source, so `department` is empty for that year.
- San Francisco publishes every year twice, by calendar and by fiscal year; only the fiscal rows are kept.
- San Francisco publishes no names; `name` is the city's employee number.
- Massachusetts years are calendar years, from 2010. Buyouts of unused leave count in `total_pay` only.
- The current year is read again on every fetch, because sources keep adding pay periods.

## Commands

| Command | Does |
|---|---|
| `fetch` | read pay rows into the local SQLite cache, optionally write `--out` |
| `stats` | rows, years and share with total pay, per cached source |
| `sources` | list source slugs |
| `check-source <slug>` | read 100 live rows through the source file; fails on a missing column |

The cache lives at `~/.cache/public-salaries/cache.db` (or under `$XDG_CACHE_HOME`). Set `SOCRATA_APP_TOKEN` for higher portal rate limits; it is optional.

## Add a source

A source is one `.toml` file in [`src/public_salaries/sources/`](src/public_salaries/sources/): the portal, the dataset id and which portal column feeds each of ours. Copy [`massachusetts.toml`](src/public_salaries/sources/massachusetts.toml), then run `public-salaries check-source <slug>`. A link to a payroll dataset is a contribution too.

## License

MIT. The data belongs to each employer; see `source_url` in each source file.
