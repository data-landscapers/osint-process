<!-- reader: cc; type: reference -->
# Data Landscapers Intelligence Wiki — master index

A compounding intelligence base on **data governance and digital transformation across Africa**, feeding the long-form output at data-landscapers.com. Built to **depth on demand**: deep where Bill is writing or asking, thin elsewhere. Thin coverage of a country nobody is writing about is the correct state, not a gap.

Built and maintained by the agent per [CLAUDE.md](../CLAUDE.md) (principles) and the specs [reference.md](reference.md) indexes (operational detail); the human curates sources and directs analysis.

## Authorities (controlled vocabularies)

- **Places** — [countries.csv](../lookups/countries.csv) — 54 ISO-3 countries + 8 `X__` regions.
- **Subjects** — [taxonomy.md](../lookups/taxonomy.md) — 10 Level-1 categories, ~36 Level-2 slugs.
- **Entity types** — `company` `organisation` `government-body` `initiative` `person` `deal` `resource` (a standing data asset — database/dataset/registry/tool/portal, e.g. PeeringDB) `instrument` (a published standard, taxonomy, framework, or policy/legal instrument, e.g. the World Bank's theme taxonomy, POPIA). **Tag only — no page is ever minted.**

Values outside the vocabularies are rejected.

## Faceted navigation

- [places-index.md](places-index.md) — browse by place (country / region).
- [topics-index.md](topics-index.md) — browse by subject.
- **No entity index** — an entity is a tag only; `raw/` is greppable.

## Operations

- [log.md](../logs/log.md) — operation log.
- [sweep-url_log.md](../logs/sweep-url_log.md) — machine index of every URL already adjudicated, with its disposition; sweeps `grep` it before fetching. Pruned to **one rotation** by `SWEEP-CYCLE.md`.
- `reviews/contradictions/` — the reconcile worklist.
- `reviews/acquisitions.md` — the fetch list.
- `X:\osint-housekeeping.md` — the housekeeping register: lint-type jobs too big for a batch, worked one session at a time. Open jobs only; `X:\osint-housekeeping-resolved.md` beside it. Not in this repository — OSINT writes it, CORPUS commits it.
- `X:\strategic-reviews\` — the review series and numbered task lists, both systems', oldest 2026-07-24. On the share, not in this repository. A dated record: read for the commissioning of a task, never edited after its own date.

## Processes

Every runnable process, its trigger phrase, and what it does. Each has a procedure file that governs it; this table is only a directory. Orchestrators call the passes; the passes do the work.

**Orchestrators & batch**

| Trigger | File | Function |
|---|---|---|
| `update wiki` / `update wiki backfill` | [UPDATE-WIKI.md](../UPDATE-WIKI.md) | On-demand loop: ingest Phase A → `WIKI-SYNC.md` Phase B → reconcile → acquire, until the queues are empty; hard cap 3 iterations. `update wiki backfill` runs one iteration with `INGEST.md`'s backfill lane open. Does not lint; never drains `new-budget/`. Not called by the nightly cycle. |
| `run wiki sync` | [WIKI-SYNC.md](../WIKI-SYNC.md) | Drains `logs/ingest-pending-writes.md` — Phase B and nothing else; Phase A first only if `new/` holds something. A nightly close step, or on demand. |
| `run the budget collect batch for <country>` · `run the budget collect sweep` | [BUDGET-COLLECT.md](../BUDGET-COLLECT.md) | Collects one country's budget documents for FY2024–2026 and catalogues each as a source; the sweep form takes the next three blank rows of `lookups/budget-init-backlog.csv`. No extraction. Off the rotation; runs on Bill's "start the budget sprint" only. |
| `run the sweep cycle` | [SWEEP-CYCLE.md](../SWEEP-CYCLE.md) | Nightly orchestrator, typed by hand: Exa canary (on failure the collecting half is skipped), daily and off-list sweeps, the rotation's day (`logs/sweep-cycle_log.md`), one `INGEST` Phase A pass, quick lint, reconcile and acquire if their queues have items, close; then full lint, one housekeeping job (`BACKLOG`) and rules, every night, rules last. Everything on Opus; no budget brake. Prunes `sweep-url_log.md` and truncates `logs/log.md` (`scripts/rotate-log.py`). |
| `run the bulletin sweep` | [SWEEP-BULLETIN.md](../SWEEP-BULLETIN.md) | Late-morning top-up, typed by hand: the daily and off-list sweeps on a today-only window, `INGEST` Phase A over this run's files, commit, mirror to `O:\`. State in `sweep/bulletin/`. |
| `run status acquire` | [STATUS-ACQUIRE.md](../STATUS-ACQUIRE.md) | Absorbs a CORPUS status-acquire batch (a country's `X:\africa-acquire.csv` rows, drop list on `X:\prepared\`) via `scripts/status-acquire.py --absorb`: registers `not-a-document` URLs in `lookups/rejected-urls.csv` and closes rows to `X:\acquire-done.csv`, its only writer. Run by the cycle's close every night; the trigger is the repair path. |
| `wiki status` | [STATUS.md](../STATUS.md) | Calculates the queue counts and the standing tally (`scripts/status.py`, writes `logs/status.md`). The canonical status object. |
| `display status` | [STATUS.md](../STATUS.md) | Reads `logs/status.md`; recomputes nothing. |

**Core passes** (each drains one queue)

| Trigger | File | Function |
|---|---|---|
| `run ingest` | [INGEST.md](../INGEST.md) | Drains `new/`, Phase A only — the one door into `raw/`. Four dispositions: admitted, contradiction brief, acquisition line, deleted. Two lanes, assigned per item by `scripts/ingest-lane.py`: backfill (`status-acquire-*`, `progress-filler-*`, `dataset-*` batches) skips origin adjudication, tier-3 dedup and the authored `hub_line`; news screens origins and dedups tier 3 drop-by-default. Schemas in [schemas.md](schemas.md). |
| `run reconcile` | [RECONCILE.md](../RECONCILE.md) | Resolves `reviews/contradictions/open/`: one research attempt per brief, then a dated resolution or a dated statement on the page. Nightly when the queue has items, or on demand. |
| `run acquisitions` | [ACQUIRE.md](../ACQUIRE.md) | Works the whole `reviews/acquisitions.md` list — one automated attempt per line, then ingest-and-strike or drop. Owns the gap probe ([intake.md](intake.md) §7a), stamping `probe_at`. Nightly when the list has open lines, or on demand. |
| `full lint` | [LINT.md](../LINT.md) | The hygiene checks, numbered #1–#38 (numbers permanent). Acts and logs; surfaces only genuine contradictions. A nightly close step, or on demand. Thresholds in [operations.md](operations.md) §8. |
| `quick lint` | [LINT.md](../LINT.md) | Nightly: the scripted checks and no-reading fixes, plus the incremental band over the run's admissions. The cycle's fixed closing step. |
| `run report lint` | [REPORT-LINT.md](../REPORT-LINT.md) | Six read-only checks (A–F) over the finance and hub compile; `scripts/report-lint.py`. At the close of finance compile, or on demand. |
| `run prune` | [PRUNE.md](../PRUNE.md) | The single retention register: what ages out, when, and which pass deletes it. Called by `full lint` as check #18, or standalone. |
| `run rules` | [RULES.md](../RULES.md) | Drains `reviews/rule-candidates.md` as every night's **last stage**, or on the manual trigger — the only place a rule changes, and the parent's own work, never a sub-agent's. |
| `run the backlog` | [BACKLOG.md](../BACKLOG.md) | One housekeeping job, oldest first, prepared work on `X:\prepared\` applied first. Called by the sweep cycle's close every night, before rules, or on demand. |
| `run housekeeping` / `run housekeeping job N` | `X:\osint-housekeeping.md` | Works the housekeeping register in a session of its own, under `BACKLOG.md`'s rules without the one-job limit. |

**Finance**

**Domestic-state record-building is retired** (R57, 2026-09-24): `BUDGET-EXTRACT`, `COUNTRY-BUDGET-BATCH` and `SWEEP-COUNTRY-BUDGET` are gone, OSINT mints no budget-line records, and finance compile builds no domestic export. Collection survives as `BUDGET-COLLECT` over `DOMESTIC-FINANCE-SWEEP`, both by name only. The non-state layer is live and nightly — `SWEEP-FINANCIERS`, `SWEEP-IATI`, `FINANCE-COMPILE` / `FINANCE-PAGES`, building `outputs\non-state-finance\`.

| Trigger | File | Function |
|---|---|---|
| `run deal vocab` | [DEAL-VOCAB.md](../DEAL-VOCAB.md) | The controlled vocabularies for a `## Deal record`'s Instrument, Status and Beneficiary type, in `lookups/deal-vocabs.csv` with its `source_value → value` maps. Held by lint #28. A spec, not a recurring pass. |
| `run hub compile` | [HUB-COMPILE.md](../HUB-COMPILE.md) | Recomputes each place hub's Recent developments from the `hub_line` fields in `raw/`; fired by ingest for the places it touched; aggregates only. Pre-cut-over content is a frozen legacy block. |
| `run finance compile` | [FINANCE-COMPILE.md](../FINANCE-COMPILE.md) | Recomputes each place hub's `## Financing` section and the per-country CSV exports under `outputs/` from the finance records in `raw/`. |
| `rebuild finance pages` | [FINANCE-PAGES.md](../FINANCE-PAGES.md) | Full rebuild of the per-country CSV exports (`scripts/build-finance-page.py --all`, or one country). |
| `run domestic finance capture` / `load` / `back-swing` | [wiki/finance-load-domestic-state.md](finance-load-domestic-state.md) | Builds domestic-state budget records, stages folded into a `## Stage history`. Suspended with the layer. |
| *(called by the IATI poll)* | [wiki/finance-iati-driver.md](finance-iati-driver.md) | Turns one selected IATI activity into a finance record. Requests `iati_json`; financier is the `reporting-org` unless `@secondary-reporter` is set. |
| `run finance back-swing` | [wiki/finance-news-driver.md](finance-news-driver.md) | Extracts finance records from prose sources — news, releases, filings. |

**Sweeps** (acquire and stage candidates into `new/`; the containment boundary is [intake.md](intake.md) §7; every row's admissibility screen is [origin-screen.md](origin-screen.md), called by each sweep listed below)

| Trigger | File | Function |
|---|---|---|
| `run the daily sweep` | [SWEEP-DAILY-LIST.md](../SWEEP-DAILY-LIST.md) | Scans the sources in `sweep-daily.csv` since the last run and stages candidates into `new/`. State in `sweep/daily/`, dated record in `sweep/daily/history.md`. Stage-only inside the cycle. |
| `run the off-list sweep` | [SWEEP-DAILY-OFFLIST.md](../SWEEP-DAILY-OFFLIST.md) | Open-web companion — everything off `sweep-daily.csv`, on two tracks. State in `sweep/off-list/`. |
| `run domestic finance sweep for <country> <year>` | [DOMESTIC-FINANCE-SWEEP.md](../DOMESTIC-FINANCE-SWEEP.md) | By name only, or as `BUDGET-COLLECT.md` step 1. One country-year's budget documents and statements, staged to `new-budget/{ISO3}/{FY}/`. State in `sweep/domestic/`. |
| `run the journals sweep` | [SWEEP-JOURNALS.md](../SWEEP-JOURNALS.md) | Content sweep over `lookups/sweep-journals.csv` since `last_swept_day`; state in `sweep/journals/`. Stage-only. |
| `run the newspapers sweep` | [SWEEP-NEWSPAPERS.md](../SWEEP-NEWSPAPERS.md) | Content sweep over `lookups/sweep-newspapers.csv` (place from each row's `iso-3`); state in `sweep/newspapers/`. |
| `run the thinktanks sweep` | [SWEEP-THINKTANKS.md](../SWEEP-THINKTANKS.md) | Content sweep over `lookups/sweep-thinktanks.csv`; state in `sweep/thinktanks/`. Pruning dead orgs is manual. |
| `run the country deep sweep` | [SWEEP-COUNTRY-DEEP.md](../SWEEP-COUNTRY-DEEP.md) | Four Exa Agent briefs per country over `countries.csv`; overlap with other sweeps is settled at ingest. Stateless; drop log in `sweep/country-deep/`. Stage-only. |
| `run the IATI poll` | [SWEEP-IATI.md](../SWEEP-IATI.md) | Rotation sweep of the donors' own reporting: diffs activity ids (`sweep/donor/iati/last-poll-ids.txt`), selects by geography then topic — never by DAC sector code — and builds finance records through the IATI driver into `new/`. |
| `run the financiers sweep` | [SWEEP-FINANCIERS.md](../SWEEP-FINANCIERS.md) | Rotation sweep: one Exa Agent brief per financier in `lookups/sweep-financiers.csv`; stages candidate sources, never deal records; no amount gate. Stateless; drop log in `sweep/financiers/`. Stage-only. |
| `run the regional sweep` | [SWEEP-REGIONAL.md](../SWEEP-REGIONAL.md) | Regional institutions (`lookups/sweep-regional-orgs.csv`) and the X-region rows of `countries.csv`, one Exa Agent brief each. Stateless; drop log in `sweep/regional/`. Stage-only. |

**Shared objects** (no trigger — called by the processes above)

| Object | File | Called by |
|---|---|---|
| Capture rule | [capture-rule.md](capture-rule.md) | The verbatim-capture rule (the `excerpt` / `paywalled` dispositions, local fetch first) and *Fetching without spending context*. Baked into every fetching sub-agent's instructions. |
| Origin screen | [origin-screen.md](origin-screen.md) | The inadmissible-origin gate: `logs/drop-list.csv`, the `watch → drop` promotion, the `inadmissible-origin` drop reason. Called by every sweep at its admissibility screen and by ingest at step 1. |
| Ingest judgment | [ingest-judgment.md](ingest-judgment.md) | The reasoning behind `INGEST.md`'s rules. |
| Lint checks | [lint-checks.md](lint-checks.md) | The reasoning and finer detail behind `LINT.md`'s checks, by check number. |
| Sweep cycle notes | [sweep-cycle-notes.md](sweep-cycle-notes.md) | The reasoning and finer detail behind `SWEEP-CYCLE.md`'s wiring, by its own headings. |
| Standing briefs | [brief-sweep.md](brief-sweep.md), [brief-ingest.md](brief-ingest.md) | What every sweep slice and ingest Phase A slice is given, pasted verbatim by the cycle parent (`SWEEP-CYCLE.md` → *What every sub-agent prompt carries*). |
| The specs | [reference.md](reference.md) | Directory of the five shared specs — [facets.md](facets.md) §1, [layout.md](layout.md) §2–3, [schemas.md](schemas.md) §4–5a, [intake.md](intake.md) §6–7a, [operations.md](operations.md) §8–11a. |

**Reporting**

| Trigger | File | Function |
|---|---|---|
| `repo status` | [REPO-STATUS.md](../REPO-STATUS.md) | Read-only corpus report over `raw/**/*.md` — by publication year, month and place. Writes `reviews/repo-status.md` via `scripts/repo-status.py`. |
| *(helper, by hand)* | [scripts/page-index.py](../scripts/page-index.py) | Reports a synthesis page's shape without reading it — section sizes, `## By place` cells against `operations.md` §8; `--all --over N` ranks concept pages. Read-only. |
| *(lint #22; `ACQUIRE.md` step 0)* | [scripts/lint-acquisition-held.py](../scripts/lint-acquisition-held.py) | Strikes an acquisition line naming a held document — exact URL or `artefact:` basename, never a title match. Read-only. |
| *(every sub-agent that logs; lint #29)* | [scripts/log-append.py](../scripts/log-append.py) | The only sanctioned writer of `logs/log.md`: assembles the entry form, stamps UTC itself, inserts at the top. `--check` audits the file — lint #29, surface-only. |
| *(`SWEEP-CYCLE.md`, before each stage commit)* | [scripts/assert-containment.py](../scripts/assert-containment.py) | Write-set assertion at a stage boundary: `--stage sweep\|ingest\|lint\|close` against `git status`, exit 1 = do not commit. Deny set in every stage: `CLAUDE.md`, the `wiki/` specs, every root procedure. `--allow-extra` is the parent's explicit exception; `--list` prints the sets. **`--patch <dir>`** reads a CORPUS `format-patch` series' own file set before `git am`: `scripts/`, `lookups/` and the two faceted index pages only; exit 2 on a directory with no patch in it. Read-only. |
| *(lint #21)* | [scripts/audit-machine-records.py](../scripts/audit-machine-records.py) | Audits the machine-loaded `raw/` records for three defect classes; `--persist` appends a dated row to `logs/machine-record-audit.csv` and exits non-zero if class 1 (`date_source: proxy` on a finance record) or class 3 (`full` on a truncated body) rose. |
| *(lint #20)* | [scripts/lint-unsourced-figures.py](../scripts/lint-unsourced-figures.py) | Lists hubs whose lede carries an unsourced ranking, market-size or penetration figure. Read-only. |
| *(ingest; lint #6)* | [scripts/origin-screen.py](../scripts/origin-screen.py) | The mechanical half of [origin-screen.md](origin-screen.md): screens `new/` (or bare `--domain`s) against `logs/drop-list.csv`, exits non-zero on `DROP` / `WATCH`, computes `NOVEL`; `--held` lists the hold queue lint #6 drains. Read-only. |
| *(the directory of every script)* | [scripts/README.md](../scripts/README.md) | What each script is, what calls it, and its lifecycle — standing (`scripts/`), bespoke (`scripts/extractors/{ISO3}/`), spent (`scripts/archive/`). `vault_lib` reads the vault; `finance_lib` knows what a deal record is. |
| *(no caller since `BUDGET-EXTRACT.md` retired)* | [scripts/archive-budget-docs.py](../scripts/archive-budget-docs.py) | Archives extracted budget documents to `budget-archive/{ISO3}/{FY}/`; dry-run by default; `--verify`. Kept for re-archiving. |
| *(`BUDGET-COLLECT.md`, between groups)* | [scripts/promote-budget-companions.py](../scripts/promote-budget-companions.py) | Catalogues held `budget-archive/` companions into `raw/`, skipping anything already held. Dry-run by default; `--write` applies. |
| *(step zero of `full lint`)* | [scripts/lint-deterministic.py](../scripts/lint-deterministic.py) | The mechanical checks in one command: #1 schema, #2 vocabulary, #3 `last_reviewed`, #4 wikilinks, #10 stranded `new/`, #11 filenames and shards, #12 link-list convention, #15 `body_completeness`, #24 register caps, #25 `CLAUDE.md` line cap, #28 deal-record fields, #34 catalogue hero, #38 de-accented Romance titles. Reports, never edits; `--check N`, `--all`, `--json`; exit 1 on any hard finding. |
| *(any script that reads the vault)* | [scripts/build-index.py](../scripts/build-index.py) | Rebuilds `index/` — frontmatter verbatim plus a derived block per artefact, and `links.jsonl` — untracked, from scratch, never appended to; `--sql` builds `index/vault.db` on demand and any rebuild that does not refresh it deletes it; `--check` exits 1 if stale. |
| *(unwired)* | [scripts/build-catalogue.py](../scripts/build-catalogue.py) | Retired from the cycle — CORPUS builds its own catalogue. Left standing. |
| *(lint #26)* | [scripts/lint-output-freshness.py](../scripts/lint-output-freshness.py) | Newest mtime in `outputs\non-state-finance\` against the last cycle close in `logs/sweep-cycle_log.md`. Report-only. |
| *(`SWEEP-CYCLE.md`, after the notes commit)* | [scripts/pull-new-queue.py](../scripts/pull-new-queue.py) | Moves every `X:\new-queue\` folder carrying `READY` flat into `new/`, adds `sweep_batch:` where a backfill folder's candidates carry none, leaves a `delivered-YYYY-MM-DD` marker; a name already in `new/` stays queued. Dry run by default, `--apply` moves. |
| *(`SWEEP-CYCLE.md`'s close)* | [scripts/rotate-log.py](../scripts/rotate-log.py) | Truncates `logs/log.md` to its newest ~400 lines. `--apply` acts, `--keep N` sets the budget. |
| *(`SWEEP-CYCLE.md`, first act, every stage boundary, and before the manifest)* | [scripts/usage-log.py](../scripts/usage-log.py) | Inserts `Date`, `Time (UTC)`, `7d usage` and `Session usage` at the top of `logs/usage-log.csv`, newest first; `--stage NAME` records the reading in the git-ignored buffer `logs/usage-stages.jsonl` instead (`--csv` both, `--reset` empties it first), which `cycle-manifest.py --usage` writes as the manifest's `usage` block. Never blocks: a failed read writes `n/a`. |
| *(helper, by hand)* | [scripts/uncited-sources.py](../scripts/uncited-sources.py) | Lists admitted sources no `wiki/` page cites. `--recent 1` after a run should read 0. Read-only. |
| *(`WIKI-SYNC.md` step 9)* | [scripts/wiki-index-gen.py](../scripts/wiki-index-gen.py) | Regenerates the *Every intersection* block in `places-index.md` and `topics-index.md` from `wiki/intersections/`; owns its markers, asserts nothing outside them moved, refuses a page carrying no `place:` or `topic:`. `--check` exits 1 when a block is stale, `--diff` shows the change, `--shape` picks the row form, `--gaps` writes the per-page measurement. |

**Archived** ([archived-procs/](../archived-procs/) — kept for reference, not run)

| Was | File | Why archived |
|---|---|---|
| `run non-state finance load` | [finance-load-nonstate-csv.md](../archived-procs/finance-load-nonstate-csv.md) | One-off initial load of the non-state deal CSV; finished. |
| `run budget consolidation` | [BUDGET-CONSOLIDATE.md](../archived-procs/BUDGET-CONSOLIDATE.md) | One-off migration to the accreting per-line/year shape; finished. |
| Country ingest workflow | [country-ingest-workflow.md](../archived-procs/country-ingest-workflow.md) | Country-by-country procedure over the `external-datasets/` corpus. Superseded. |
| `backfill <ISO3>` | [BACKFILL.md](../archived-procs/BACKFILL.md) | Drained a country's pre-staged content from `X:\new-queue\<ISO3>\`. Archived 2026-09-08 (Bill). |
| `backfill batch` | [BACKFILL-BATCH.md](../archived-procs/BACKFILL-BATCH.md) | The loop around `backfill <ISO3>`. Archived 2026-09-08 (Bill). |

The folder also holds those runs' data artefacts — inputs and records, not processes.

## Page types & folders

| Folder | Page type | Notes |
|---|---|---|
| `new/` | (intake queue) | Unprocessed clips **and sweep candidates** land here; drained on ingest. Folder = state. |
| `sweep/` | (staging) | Sweep state and logs. The sweep writes candidates straight to `new/`; `new-queue/done/` remains Bill's. |
| `raw/` | source | Admitted sources, `YYYY-MM-DD`-prefixed and sharded `raw/YYYY/` on that prefix; immutable after ingest (one bounded exception: verbatim fidelity re-capture). |
| `wiki/concepts/` | concept | One page per subject slug. |
| `wiki/places/` | place | Country and region hubs (one type). |
| *(no folder)* | — | Entities are a tag only (`entities:`), never a page. |
| `wiki/intersections/` | intersection | Topic × place — created lazily when substantial. |
| `outputs/non-state-finance/` | export (derived) | `{ISO3}-nonstate.csv`, `all-nonstate.csv`, same compiler. Outputs only: the compiler's input, `lookups/financier-names.csv` (the financier record), lives with the other vocabularies. |

## State — not kept here

- **Corpus counts** — `repo status` ([REPO-STATUS.md](../REPO-STATUS.md)), which writes `reviews/repo-status.md` from `scripts/repo-status.py`.
- **Queue counts** — `wiki status` ([STATUS.md](../STATUS.md)): the standing counts and the half-finished-state gates.

Batch-by-batch ingest history is in [log.md](../logs/log.md) and git. This page holds structure, not chronology.
