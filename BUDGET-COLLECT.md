<!-- reader: cc; type: runbook -->
# Budget collect batch — procedure

**Collects one country's budget documents for FY2024, FY2025 and FY2026 and catalogues them as sources.** It does not read them for figures. **Trigger: "run the budget collect batch for `<country>`"** runs one country by name. **"run the budget collect sweep"** runs the next three blank rows of `lookups/budget-init-backlog.csv`, one at a time.

**Collection is OSINT's half; extraction is CORPUS's.** CORPUS builds its budget rows from the documents, and it can cite only what `raw/` catalogues. So this batch fetches the documents, files each artefact where CORPUS can read it, and admits each companion page as a source. **There is no five-fact test, no budget-line record and no extraction.** OSINT no longer mints domestic-state records. Those already in `raw/` stand, because CORPUS's migrated rows cite them.

## The queue — `lookups/budget-init-backlog.csv`

One row per place in run order, with two columns: `iso-3` and `Budget Done`.

| value | meaning |
|---|---|
| `Yes` | **all three years swept and nothing left staged** — never selected again |
| *(blank)* | pending |
| `n/a` | not a candidate: the eight `X` regions, which have no national budget |

Reordering the queue is a file edit. The sweep takes the first three blank rows in file order. A country that stops short stays blank and is re-selected next time; re-running it re-sweeps, and dedup absorbs the overlap.

## Steps, per country

1. **Domestic finance sweep, FY2024, FY2025, FY2026** (`DOMESTIC-FINANCE-SWEEP.md`), in its collect scope: **priority tiers 0–3, plus the own-source funds and the data-protection authority's budget (Blocks 4c and 6)**. The prose blocks (4, 4b, 5, 7) run only where they are cheap, meaning the document library already fetched names the item. Budget documents stage to `new-budget/{ISO3}/{FY}/`, artefact and companion together. Manifest rows go to `new-budget/{ISO3}/manifest-rows.csv`, never straight to the shared `new-budget/manifest.csv`.
2. **Catalogue.** Each staged companion page becomes a source record in `new/`, on the shape `new/2026-07-16-mdg-lfr-2026-tome-2-livre-1-companion.md` shows:
   - **filename:** the companion's own filename;
   - **frontmatter keeps:** the publisher URL, `source_tier: budget-document`, `doc_type` from the closed list in `lookups/budget-doc-types.csv` (its `stages` column names the ladder stage the type evidences: where two are named the document's own cover decides, `none` evidences no stage, `as-stated` is the stage the source states), `fiscal_years_covered`, `catalogue_hero`, and `hub_line_none:` with its reason;
   - **frontmatter drops:** any `artefact:` key, because the manifest row is the declaration (`wiki/schemas.md` §4);
   - **body:** `## Document` (instrument, scope, currency and printed scale, extent), `## Source` and `## Notes`, with `body_completeness: excerpt`.
3. **Archive.** Each artefact and its companion move to `budget-archive/{ISO3}/{FY}/`. Its manifest row gets the new paths and `archive_path`, leaving `extracted` blank. `new-budget/{ISO3}/` is then deleted.
4. **A document not reached in one attempt goes to `reviews/acquisitions.md`**, and its absence is stated, dated, on the place hub (`CLAUDE.md` → *Working the base*). One attempt, then the stated absence. Never a second theory.

**Done means `Yes`:** all three years swept, `new-budget/{ISO3}/` gone, and every staged document either catalogued in `new/` or recorded as an acquisition. Only then write `Yes`.

**Expect uneven years.** FY2026 usually yields an appropriation and little else, and FY2024 is the year most likely to carry the full chain. A microstate yielding one appropriation has been collected correctly.

## Close

The caller merges each country's `manifest-rows.csv` into `new-budget/manifest.csv` and deletes it. `new-budget/` must hold only `manifest.csv` at every stop. Then comes one ingest over `new/`. After it, the caller does three things:

- rebuilds `lookups/artefact-md5-index.csv` (`python scripts/artefact-md5-index.py --rebuild`);
- commits, pushes and mirrors, because CORPUS reads only the mirror;
- writes one `[ACT]` note to `X:\notes-for-corpus.md` per group, with `Affects: budgets/{ISO3}/`, listing the companion slugs per country-year and every year where nothing is published.

It logs one line to `logs/log.md` and ends on the standing status line.

## Delegation and concurrency

**One writer at a time is the rule.** Standalone, the batch runs one country after another in the main session, and nothing else writes the vault meanwhile.

**The budget sprint is the one exception** (notes-for-osint 168, from Bill's "start the budget sprint" until the weekly reset at 20:00 on 2026-09-26). Three countries run at once, one sub-agent each. Each agent writes only:

- its own `new-budget/{ISO3}/`;
- its own `budget-archive/{ISO3}/`;
- its own `new/` records under its batch prefix (`sweep_batch: domestic-finance-{ISO3}-{FY}-{date}`);
- its own `sweep/domestic/{ISO3}-*` run files.

No agent touches `new-budget/manifest.csv` or runs ingest; the caller does both at the group's close. Every spawn carries the four standing lines (`SWEEP-CYCLE.md` → *What every sub-agent prompt carries*), and returns one line: `iso3=… years=… catalogued=N archived=N acquisitions=N stopped=<complete|context|error>`.

**Between groups, or once the queue is empty, promote what is already held**: `python scripts/promote-budget-companions.py` catalogues the `budget-archive/` companions of full estimates volumes, appropriation and finance laws, outturn reports and audit reports into `raw/`, country by country. The script's own docstring gives the order and the test.
