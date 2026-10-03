<!-- reader: cc; type: runbook -->
# FINANCE-PAGES.md — the per-country finance exports

Trigger: **"rebuild finance pages"** (all countries) or **"rebuild finance page for <country>"** (one). Runs `scripts/build-finance-page.py`.

This builds **OSINT's own compile**: the per-country deal exports, under `outputs/`. It reads the finance records already in `raw/` and the financier record; it **ingests nothing, admits nothing, moves nothing**. The exports are derived snapshots — *do not hand-edit; changes belong in the records or in the engine.* They are **not a website feed** — CORPUS compiles its own published copy from the same `raw/` records. OSINT's copy is the substrate `REPORT-LINT` checks A–E reconcile against and the file `compile-hub-financing.py` reads to write the hub prose.

## What it writes, per country

- **`outputs/non-state-finance/{ISO3}-nonstate.csv`** — one row per deal.
- **`outputs/non-state-finance/all-nonstate.csv`** — the combined deal export, `--all` only.

Every row carries the filename of its `raw/` record in a `record` column.

## Running it

```
python scripts/build-finance-page.py --all      # every country — the full rebuild
python scripts/build-finance-page.py ZAF        # one country
```

**`--all` is the full refresh.** It rescans the whole corpus once and rewrites every CSV, so after any change to the engine or the column sets, one `--all` run brings everything into line. Both paths use the same place-based scan, so a single-country rebuild and `--all` produce byte-identical files.

## Relationship to finance-compile

`FINANCE-COMPILE.md` step 4 calls `build-finance-page.py {ISO3}` for each place it recomputes, so **routine, incremental** export refreshes happen automatically whenever ingest admits a finance record for a country — one record rebuilds that country's exports, and only that country's. This process is the **manual / full** counterpart: a from-scratch rebuild of everything, for a layout change or a first run.

## Inputs

`financier-names.csv` is an **input** to the build, not an output of it, and lives in `lookups/` with the other controlled vocabularies. Nothing the exports carry is read back in.
