# REPO-STATUS.md — repository status report

Trigger: **"repo status"**. Read-only. Counts what's in `raw/` and writes a markdown report to `reviews/repo-status.md`. Ingests nothing, touches no wiki page, changes no state — run it any time.

Distinct from `wiki status` (STATUS.md), which reports the three live **queue** counts. This reports the **corpus**: how many sources are held, and how they break down by year, month and place.

## Run

```
python scripts/repo-status.py --out reviews/repo-status.md
```

Omit `--out` to print to stdout instead of writing the file. Run from the repo root.

## What it counts

The unit is a markdown source in `raw/`. **PDFs are excluded** — every PDF in `raw/` has a markdown counterpart that is counted, so counting both would double every scanned document.

- **By year** — publication year from each file's `published:` frontmatter field (not the filename: a few companion files aren't date-named, but all carry `published:`). The year total equals the total md count.
- **2026 by month** — same field, month component. Sources dated to year precision only (`published: 2026-01-01` written where only the year is known still resolves to a month; a bare `2026` would not) are carried in the year total but not the month table, so the month table can total slightly less than the year row. The report notes the difference. **Every table measures capture, not the world**, and the by-month one is where that gets mistaken. Its shape is set by when the sweeps ran, which countries were being initialised and how many rotation nights completed — not by how much happened. A rise is the wiki collecting more, never Africa doing more, and it is exactly the figure a reader would otherwise quote as activity. The generated report states this above the table so the caveat travels with the number.

- **By country** — the `places:` facet, each ISO-3 mapped to a name via `lookups/countries.csv`. A source tagged with several places is counted under **each**, so this column sums to more than the document total — it measures coverage, not documents. Region/bloc codes (XAF, XSS, XWA …) and any code not in `countries.csv` are tabled separately, and untagged sources are noted.

## Extending it

The report is meant to grow — "for starters" was the brief. Add a section by adding a counter in `scripts/repo-status.py` (frontmatter is already parsed for `published` and `places`; extend `parse_frontmatter` for other facets such as `topics` or `entities`) and appending a table block. Keep it read-only.
