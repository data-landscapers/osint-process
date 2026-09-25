<!-- reader: cc; type: runbook -->
# FINANCE-PAGES.md — the per-country finance exports

Trigger: **"rebuild finance pages"** (all countries) or **"rebuild finance page for <country>"** (one). Runs `scripts/build-finance-page.py`.

This builds **OSINT's own compile**: three CSV exports per country, under `outputs/`. It reads the finance records already in `raw/` and the FX table; it **ingests nothing, admits nothing, moves nothing**. The exports are derived snapshots — *do not hand-edit; changes belong in the records or in the engine.* They are **not a website feed** — CORPUS compiles its own published copy from the same `raw/` records. OSINT's copy is the substrate `REPORT-LINT` checks A–E reconcile against and the file `compile-hub-financing.py` reads to write the hub prose. There is no per-country report page; the one thing a page would carry that the data does not is preserved as *Nothing leaves the aggregate silently* below.

## What it writes, per country

- **`outputs/non-state-finance/{ISO3}-nonstate.csv`** — one row per deal.
- **`outputs/non-state-finance/{ISO3}-summary.csv`** — aggregates by origin × subject × fiscal year, non-state and domestic-state both in US$m (ball-park), plus the exclusion rows below. Always written.
- **`outputs/budgets/{ISO3}-budget.csv`** — domestic budget by year × vote × programme-line (stage ladder as columns, execution vs voted / vs revised). **Only where budget data exists**, so the gap is visible at a glance; a stale one left by an earlier run is deleted by the build. While the domestic-state layer is suspended no new domestic record lands to move it, so a re-run writes the same file, not a stale one.
- **`outputs/non-state-finance/all-nonstate.csv`** — the combined deal export, `--all` only.

Every row carries the filename of its `raw/` record in a `record` column.

## Two things the exports state rather than hide

- **Nothing leaves the domestic aggregate silently.** Every domestic record is either in the subject × fiscal-year total or in an **`origin: excluded`** row of `{ISO3}-summary.csv`, by reason, with a count in `excluded_lines` and an amount in `excluded_usd_m` — no enacted baseline (the `⚠` revised/outturn-only lines), partial- or unclear-scope, transfers counted at their spending end, unclear supplementaries, no FX rate held, no subject tag. The reasons and the exclusions are `FINANCE-COMPILE.md`'s, so hub and exports agree.
- **Currency is never assumed.** Every budget row carries its own `currency` column, so a country whose lines are not all in one currency cannot have its column summed by accident.

## Running it

```
python scripts/build-finance-page.py --all      # every country — the full rebuild
python scripts/build-finance-page.py ZAF        # one country
```

**`--all` is the full refresh.** It rescans the whole corpus once and rewrites every CSV, so after any change to the engine or the column sets, one `--all` run brings everything into line. Both paths use the same place-based scan, so a single-country rebuild and `--all` produce byte-identical files.

## Relationship to finance-compile

`FINANCE-COMPILE.md` step 4 calls `build-finance-page.py {ISO3}` for each place it recomputes, so **routine, incremental** export refreshes happen automatically whenever ingest admits a finance record for a country — one record rebuilds that country's exports, and only that country's. This process is the **manual / full** counterpart: a from-scratch rebuild of everything, for a layout change or a first run.

## USD conversion

Domestic amounts are converted to USD for the summary at the **IMF annual-average** rate for the currency and the fiscal year's start year, from `lookups/fx-imf-annual.csv` (ball-park; 100% accuracy not required). Missing years fall back to the nearest held year for that currency; a currency absent from the table leaves that country's domestic-USD blank until rows are added. The table covers all African currencies in scope; volatile and war-economy rates are flagged in its `source` column and should be refined before serious use.

`fx-imf-annual.csv` and `financier-names.csv` are **inputs** to the build, not outputs of it, and live in `lookups/` with the other controlled vocabularies. Nothing the exports carry is read back in.
