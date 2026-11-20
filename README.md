# public-salaries

US public employee pay from states and cities in one table: same columns, read straight from each employer's open-data portal. For reporters, researchers and pay analysts who compare jobs across employers without learning each portal.

Today: New York City (fiscal 2014 on), San Francisco (fiscal 2013 on) and the Commonwealth of Massachusetts (calendar 2010 on).

## Install

```
pip install git+https://github.com/ivanvia7/public-salaries
public-salaries fetch --source san_francisco --years 2025 --out pay.csv
public-salaries stats
```

The fetch takes under a minute and writes 43,239 rows:

```
source,source_id,year,employer,name,title,department,base_pay,overtime_pay,other_pay,total_pay
san_francisco,row-2226.cizu~s9ym,2025,City and County of San Francisco,Joselyn Caceres,Eligibility Worker Supervisor,Human Services Agency,122627.53,8066.32,1560.0,132253.85
san_francisco,row-222z~xw55-6vqw,2025,City and County of San Francisco,Michael Vieira,"Lieutenant, Fire Suppression",Fire Department,169343.46,31409.72,38886.65,239639.83
```

All three sources for one year took 4 minutes 22 seconds on 2026-11-20:

```
$ public-salaries fetch --source new_york,san_francisco,massachusetts --years 2025
new_york 2025: 550,219 rows read, 0 unreadable rows skipped
san_francisco 2025: 43,239 rows read, 0 unreadable rows skipped
massachusetts 2025: 162,459 rows read, 0 unreadable rows skipped
$ public-salaries stats
massachusetts: 162,459 rows, 2025 to 2025, 100.0% with total pay, median 2025 total pay $63,339
new_york: 550,219 rows, 2025 to 2025, 100.0% with total pay, median 2025 total pay $50,450
san_francisco: 43,239 rows, 2025 to 2025, 100.0% with total pay, median 2025 total pay $113,668
```

New York and Massachusetts for 2020-2025 is 4.4 million rows and about 20 minutes. Each year prints a line as it is saved.

`--out` writes `.csv`, `.jsonl`, `.db` (SQLite) or `.parquet` (needs `pip install "public-salaries[parquet] @ git+https://github.com/ivanvia7/public-salaries"`).

## One row per job per year

No source publishes a stable person id, so a person with two jobs has two rows, and two people with the same name cannot be told apart.

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
- San Francisco publishes names from 2017; 2013 to 2016 carry a numeric employee id instead.
- Massachusetts years are calendar years, from 2010. Buyouts of unused leave count in `total_pay` only.
- The current year is read again on every fetch, because sources keep adding pay periods. Past years are read once; `fetch --refresh` reads them again when a portal republishes.

## Commands

| Command | Does |
|---|---|
| `fetch` | read pay rows into the local SQLite cache, optionally write `--out` |
| `stats` | rows, years, share with total pay and median total pay of the last year, per cached source |
| `sources` | list source slugs |
| `check-source <slug>` | read 100 live rows through the source file; fails on a missing column |

The cache lives at `~/.cache/public-salaries/cache.db` (or under `$XDG_CACHE_HOME`). Set `SOCRATA_APP_TOKEN` for higher portal rate limits; it is optional.

## Checked against the portals

`uv run scripts/verify_sample.py` takes 80 random cached rows per source and reads each one again from its portal. It builds the expected values from the raw portal columns, without this tool's mapping, and compares year, name, title, department and the four pay fields. On 2026-11-20, with seed 20261120 over 2020-2025, all 240 rows matched. With no error in 240 rows, the error rate is below 1.25% at 95% confidence, not zero.

A weekly GitHub Action runs `check-source` on every source, so a renamed portal column shows up as a failed run. GitHub turns scheduled runs off after 60 days with no repository activity; `gh workflow enable sources.yml` turns them back on.

## Add a source

A source is one `.toml` file in [`src/public_salaries/sources/`](src/public_salaries/sources/): the portal, the dataset id and which portal column feeds each of ours. Copy [`massachusetts.toml`](src/public_salaries/sources/massachusetts.toml), then run `public-salaries check-source <slug>`. A link to a payroll dataset is a contribution too.

## License

MIT. The data belongs to each employer; see `source_url` in each source file.
