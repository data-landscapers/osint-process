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

- [log.md](../logs/log.md) — operation log and decisions.
- [sweep-url_log.md](../logs/sweep-url_log.md) — machine index of every URL already adjudicated, with its disposition. Sweeps `grep` it to filter their returns before fetching. Pruned to **one rotation** by `SWEEP-CYCLE.md`.
- `reviews/contradictions/` — the reconcile worklist.
- `reviews/acquisitions.md` — the fetch list.
- `X:\housekeeping-jobs.md` — the housekeeping register: lint-type jobs too big for a batch, worked one session at a time. On the share, with `X:\housekeeping-jobs-resolved.md` beside it; open jobs only in the live file. Not in this repository — OSINT writes it, CORPUS commits it.
- `X:\strategic-reviews\` — the review series and its numbered task lists, both systems' reviews together, oldest 2026-07-24. On the share; not in this repository *(moved out of `documentation/reviews/` 2026-09-08)*. A dated record: read for the commissioning of a task, never edited after its own date.

## Processes

Every runnable process, its trigger phrase, and what it does. Each has a procedure file that governs it; this table is only a directory. Orchestrators call the passes; the passes do the work.

**Orchestrators & batch**

| Trigger | File | Function |
|---|---|---|
| `update wiki` / `update wiki backfill` | [UPDATE-WIKI.md](../UPDATE-WIKI.md) | On-demand loop: ingest Phase A → `WIKI-SYNC.md` Phase B → reconcile → acquire until the queues are empty or hold only what the loop itself generated; hard cap 3 iterations. `update wiki backfill` opens `INGEST.md`'s backfill lane for every slice and runs **one** iteration — Phase A then Phase B — leaving what it raises to the nightly close's reconcile and acquire; every other trigger runs news-only. Does not lint, files nothing itself, never drains `new-budget/`. Not called by the nightly cycle. |
| `run wiki sync` | [WIKI-SYNC.md](../WIKI-SYNC.md) | Drains `logs/ingest-pending-writes.md` — Phase B and nothing else; Phase A first only if `new/` holds something. A nightly close step, or on demand. |
| `run the country budget batch for <country>` | [COUNTRY-BUDGET-BATCH.md](../COUNTRY-BUDGET-BATCH.md) | **Suspended** with the domestic-state layer; runs by name only. Initialises one country over 2024–2026: domestic finance sweep per year, budget extract, `update wiki`. |
| `run the sweep cycle` | [SWEEP-CYCLE.md](../SWEEP-CYCLE.md) | Nightly orchestrator, typed by hand — no scheduled trigger exists. Exa canary first (on failure the collecting half is skipped and the processing half still runs), daily and off-list sweeps, the rotation's numbered day (`logs/sweep-cycle_log.md` decides which sweeps and how many nights), one `INGEST` Phase A pass over the night's catch, quick lint, reconcile and acquire if their queues have items, close; on the Day B night (the row carrying `@BACKLOG`) full lint, `BACKLOG` and rules follow, rules last. Everything on Opus; no budget brake and no cost report. Prunes `sweep-url_log.md` by rotation and truncates `logs/log.md` (`scripts/rotate-log.py`). |
| `run the bulletin sweep` | [SWEEP-BULLETIN.md](../SWEEP-BULLETIN.md) | Late-morning top-up, typed by hand: Exa canary, then the daily and off-list sweeps on a today-only window (feed only, no query cluster), `INGEST` Phase A over this run's staged files only, commit, mirror to `O:\`. Advances neither sweep's high-water mark; no lint, no Phase B. State in `sweep/bulletin/`. |
| `run status acquire` | [STATUS-ACQUIRE.md](../STATUS-ACQUIRE.md) | Absorbs a status-acquire batch: CORPUS screens, fetches and stages a country's `X:\africa-acquire.csv` rows and leaves its drop list on `X:\prepared\`; `scripts/status-acquire.py --absorb` applies the classes, registers the `not-a-document` URLs in `lookups/rejected-urls.csv` and closes the rows to `X:\acquire-done.csv` (still that CSV's only writer). **The cycle's close runs it every night**, so the trigger is the repair path; the ingest is the night's own backfill Phase A. |
| `wiki status` | [STATUS.md](../STATUS.md) | Calculates the queue counts and the standing tally (`scripts/status.py`, writes `logs/status.md`). The canonical status object: the counts, the one-line `log.md` entry form, and the close report — the tally line, nothing else. |
| `display status` | [STATUS.md](../STATUS.md) | Reads `logs/status.md` with its timestamp; recomputes nothing. |

**Core passes** (each drains one queue)

| Trigger | File | Function |
|---|---|---|
| `run ingest` | [INGEST.md](../INGEST.md) | Drains `new/`, Phase A only — the one door into `raw/`. Four dispositions: admitted, contradiction brief, acquisition line, deleted. Schemas in [schemas.md](schemas.md). Two lanes: the backfill lane (`status-acquire-*`, `progress-filler-*` and `dataset-*` batches, opened by `update wiki backfill` and by the sweep cycle's ingest, assigned per item by `scripts/ingest-lane.py`) skips origin adjudication, tier-3 dedup and the authored `hub_line`; the news lane screens origins where there is no `sweep_batch:`, dedups tier 3 on titles and ledes drop-by-default, and requeues a dead slice. |
| `run reconcile` | [RECONCILE.md](../RECONCILE.md) | Resolves `reviews/contradictions/open/`: one brief, one research attempt, primaries ingested, a dated resolution applied — else a dated statement on the page, never a further pass. A nightly close step when the queue has items, or on demand. |
| `run acquisitions` | [ACQUIRE.md](../ACQUIRE.md) | Works the whole `reviews/acquisitions.md` list — one automated attempt per line, then ingest-and-strike or drop. Owns the gap probe ([intake.md](intake.md) §7a): one Exa search for any line without a URL, `probe_at` stamped either way; no other pass probes. A nightly close step when the list has open lines, or on demand. |
| `full lint` | [LINT.md](../LINT.md) | The hygiene checks, numbered #1–#38 (numbers permanent). Acts and logs; surfaces only genuine contradictions. The whole-vault band is a Day B close step, or on demand. Thresholds in [operations.md](operations.md) §8. |
| `quick lint` | [LINT.md](../LINT.md) | Nightly: every scripted check, the fixes needing no page reading, plus the incremental band (#6, #4, #5, #14, #20, #7) over the records this run admitted. The cycle's fixed closing step. |
| `run report lint` | [REPORT-LINT.md](../REPORT-LINT.md) | Six checks (A–F) over the finance and hub compile; `scripts/report-lint.py`; read-only — verifies, never compiles. Runs at the close of finance compile, or on demand. |
| `run prune` | [PRUNE.md](../PRUNE.md) | The single retention register: what ages out, when, and which pass deletes it. Runs the jobs no other pass owns; `logs/log.md` is `scripts/rotate-log.py`'s. Called by `full lint` as check #18, or standalone. |
| `run rules` | [RULES.md](../RULES.md) | Drains `reviews/rule-candidates.md` as the Day B night's **last stage**, or on the manual trigger in its own session — the only place a rule changes, and the parent's own work, never a sub-agent's. Three lines from separate runs is a rule, fewer is not; a ruled case's lines are deleted, an unruled one's age out at 21 days. |
| `run the backlog` | [BACKLOG.md](../BACKLOG.md) | One housekeeping job, oldest first, prepared work on `X:\prepared\` applied first; split above 120 minutes, otherwise whole job or largest slice. Called by the sweep cycle's close on the Day B night, before rules, or on demand. |
| `run housekeeping` / `run housekeeping job N` | `X:\housekeeping-jobs.md` | Works the housekeeping register in a session of its own, under `BACKLOG.md`'s rules without the one-job limit. The register holds the jobs. |

**Finance**

The domestic-state layer is **suspended**: `COUNTRY-BUDGET-BATCH`, `BUDGET-EXTRACT`, `DOMESTIC-FINANCE-SWEEP` and `SWEEP-COUNTRY-BUDGET` run by name only. The non-state layer is live and nightly — `SWEEP-FINANCIERS`, `SWEEP-IATI`, `FINANCE-COMPILE` / `FINANCE-PAGES`, building `outputs\non-state-finance\`. Finance compile skips only the domestic budget export, so `outputs\budgets\` stays at its last-built content.

| Trigger | File | Function |
|---|---|---|
| `run deal vocab` | [DEAL-VOCAB.md](../DEAL-VOCAB.md) | The controlled vocabularies for the three filterable fields of a `## Deal record` — Instrument, Status, Beneficiary type — in `lookups/deal-vocabs.csv` with three `source_value → value` maps beside it, and the rules for writing the fields. Held by lint #28. A spec and a closed pass, not a recurring one. |
| `run hub compile` | [HUB-COMPILE.md](../HUB-COMPILE.md) | Recomputes each place hub's Recent developments from the `hub_line` fields of the sources in `raw/`; fired by ingest, scoped to the places it touched; aggregates only. Content before the cut-over is a frozen legacy block the compiler never touches. |
| `run finance compile` | [FINANCE-COMPILE.md](../FINANCE-COMPILE.md) | Recomputes each place hub's `## Financing` section and the per-country CSV exports under `outputs/` from the finance records in `raw/`. Aggregates only. |
| `rebuild finance pages` | [FINANCE-PAGES.md](../FINANCE-PAGES.md) | Full rebuild of the per-country CSV exports (`scripts/build-finance-page.py --all`, or one country). OSINT's own compile, not a website feed; derived snapshots. |
| `run domestic finance capture` / `load` / `back-swing` | [wiki/finance-load-domestic-state.md](finance-load-domestic-state.md) | Builds domestic-state budget records — one accreting record per line × fiscal year, stages folded into a `## Stage history`. Suspended with the layer. |
| *(called by the IATI poll)* | [wiki/finance-iati-driver.md](finance-iati-driver.md) | Turns one selected IATI activity into a finance record: where each of the five facts is found, the narrative, date, transaction and FX rules, the region mapping. Requests `iati_json`, never the flattened default; financier is the `reporting-org` unless `@secondary-reporter` is set; a multi-country activity aggregates to the region with the amount whole. |
| `run finance back-swing` | [wiki/finance-news-driver.md](finance-news-driver.md) | Extracts finance records from prose sources — news, releases, filings. |
| `run budget extract` | [BUDGET-EXTRACT.md](../BUDGET-EXTRACT.md) | **Suspended**; by name only. Extracts budget lines from `new-budget/` and archives each document once read — the only thing that drains it. |

**Sweeps** (acquire and stage candidates into `new/`; the containment boundary is [intake.md](intake.md) §7; every row's admissibility screen is [origin-screen.md](origin-screen.md), called by each sweep listed below)

| Trigger | File | Function |
|---|---|---|
| `run the daily sweep` | [SWEEP-DAILY-LIST.md](../SWEEP-DAILY-LIST.md) | Scans the sources in `sweep-daily.csv` for items since the last run and stages candidates into `new/`. One instrument per domain and one query cluster, `numResults` 10; FR/AR variants only where the domain has produced a non-English source; a truncated capture is flagged, not refetched. State in `sweep/daily/`, dated record in `sweep/daily/history.md`. Stage-only inside the cycle. |
| `run the off-list sweep` | [SWEEP-DAILY-OFFLIST.md](../SWEEP-DAILY-OFFLIST.md) | Open-web companion — everything off `sweep-daily.csv`, on two tracks (A: Africa infrastructure; B: worldwide policy, governance and citizen feedback, admitted as Africa-bearing reference). State in `sweep/off-list/`. |
| `run domestic finance sweep for <country> <year>` | [DOMESTIC-FINANCE-SWEEP.md](../DOMESTIC-FINANCE-SWEEP.md) | **Suspended**; by name only. Budget documents, outturn and audit reports, ministerial statements for one country-year. State in `sweep/domestic/`. |
| `run the journals sweep` | [SWEEP-JOURNALS.md](../SWEEP-JOURNALS.md) | Content sweep over `lookups/sweep-journals.csv` since `last_swept_day` (state in `sweep/journals/`). Stage-only. |
| `run the newspapers sweep` | [SWEEP-NEWSPAPERS.md](../SWEEP-NEWSPAPERS.md) | Content sweep over `lookups/sweep-newspapers.csv` (place from each row's `iso-3`); state in `sweep/newspapers/`. |
| `run the thinktanks sweep` | [SWEEP-THINKTANKS.md](../SWEEP-THINKTANKS.md) | Content sweep over `lookups/sweep-thinktanks.csv`; state in `sweep/thinktanks/`. Pruning dead orgs is manual. |
| `run the country deep sweep` | [SWEEP-COUNTRY-DEEP.md](../SWEEP-COUNTRY-DEEP.md) | Four Exa Agent briefs per country (non-state finance, governance, data exchange, demand) over `countries.csv`. Deliberately overlaps the other sweeps; the overlap is managed at staging, not avoided, and no value judgement is made there — ingest owns it. Stateless; drop log in `sweep/country-deep/`. Stage-only. |
| `run the country budget sweep` | [SWEEP-COUNTRY-BUDGET.md](../SWEEP-COUNTRY-BUDGET.md) | **Suspended** and off the rotation. Runs `COUNTRY-BUDGET-BATCH.md` steps 1–4 over `lookups/budget-init-backlog.csv`, three countries a night. |
| `run the IATI poll` | [SWEEP-IATI.md](../SWEEP-IATI.md) | Rotation sweep — the donors' own reporting; the 9-day cadence throttle was dropped 2026-09-01, rotation alone decides when it runs. Pulls ids for every activity and parses only the diff (`sweep/donor/iati/last-poll-ids.txt` is the only state); selects by geography mechanically (`countries.csv` ISO-3, or DAC region 189/289/298) then by topic from title and description — never by DAC sector code. Selected activities become finance records through the IATI driver, into `new/`. Updated activities are out of scope. |
| `run the financiers sweep` | [SWEEP-FINANCIERS.md](../SWEEP-FINANCIERS.md) | Rotation sweep. One Exa Agent brief per financier over `lookups/sweep-financiers.csv`, slugs resolved to names through `lookups/financier-names.csv`. The window screens the publication date, not the deal date; stages candidate sources, never deal records; no amount gate. Stateless; drop log in `sweep/financiers/`. Stage-only. |
| `run the regional sweep` | [SWEEP-REGIONAL.md](../SWEEP-REGIONAL.md) | Two loops — regional institutions (`lookups/sweep-regional-orgs.csv`) and the X-region rows of `countries.csv` (XAF+XSS conflated), one Exa Agent brief each. Overlaps the others by design; value settled at ingest. Stateless; drop log in `sweep/regional/`. Stage-only. |

**Shared objects** (no trigger — called by the processes above)

| Object | File | Called by |
|---|---|---|
| Capture rule | [capture-rule.md](capture-rule.md) | The verbatim-capture rule (the `excerpt` / `paywalled` dispositions, local fetch first) and *Fetching without spending context* — parse in the shell, write bodies straight to `new/`. Baked into every fetching sub-agent's instructions. |
| Origin screen | [origin-screen.md](origin-screen.md) | The inadmissible-origin gate: `logs/drop-list.csv`, the hostile shapes, the `watch → drop` promotion, the mining rule, the `inadmissible-origin` drop reason. Called by every sweep at its admissibility screen and by ingest at step 1. |
| The specs | [reference.md](reference.md) | Directory of the five shared specs — [facets.md](facets.md) §1, [layout.md](layout.md) §2–3, [schemas.md](schemas.md) §4–5a, [intake.md](intake.md) §6–7a, [operations.md](operations.md) §8–11a. |

**Reporting**

| Trigger | File | Function |
|---|---|---|
| `repo status` | [REPO-STATUS.md](../REPO-STATUS.md) | Read-only corpus report over `raw/**/*.md` — by publication year, by month, by place. Writes `reviews/repo-status.md` via `scripts/repo-status.py`. |
| *(helper, by hand)* | [scripts/page-index.py](../scripts/page-index.py) | Reports a synthesis page's shape without reading it — section sizes, a bullet index, `## By place` cells against `operations.md` §8; `--all --over N` ranks concept pages. Read-only. |
| *(lint #22; `ACQUIRE.md` step 0)* | [scripts/lint-acquisition-held.py](../scripts/lint-acquisition-held.py) | Strikes an acquisition line naming a held document — exact URL or `artefact:` basename, never a title match. Read-only. |
| *(every sub-agent that logs; lint #29)* | [scripts/log-append.py](../scripts/log-append.py) | The only sanctioned writer of `logs/log.md`: assembles the entry form, stamps UTC itself, inserts at the top. `--check` audits the file — lint #29, surface-only. |
| *(`SWEEP-CYCLE.md`, before each stage commit)* | [scripts/assert-containment.py](../scripts/assert-containment.py) | Write-set assertion at a stage boundary: `--stage sweep\|ingest\|lint\|close` against `git status`, exit 1 = do not commit. Deny set in every stage: `CLAUDE.md`, the `wiki/` specs, every root procedure. `--allow-extra` is the parent's explicit exception; `--list` prints the sets. **`--patch <dir>`** reads a CORPUS `format-patch` series' own file set before `git am`: `scripts/`, `lookups/` and the two faceted index pages only, never `raw/`, never wiki prose; exit 2 on a directory with no patch in it. Read-only. |
| *(lint #21)* | [scripts/audit-machine-records.py](../scripts/audit-machine-records.py) | Audits the machine-loaded `raw/` records for three defect classes; `--persist` appends a dated row to `logs/machine-record-audit.csv` and exits non-zero if class 1 (`date_source: proxy` on a finance record) or class 3 (`full` on a truncated body) rose. Class 2 (empty `entities`) is carried, never gated. |
| *(lint #20)* | [scripts/lint-unsourced-figures.py](../scripts/lint-unsourced-figures.py) | Lists every hub whose lede carries a ranking, market-size or penetration figure with no source link in the lede. Read-only. |
| *(ingest; lint #6)* | [scripts/origin-screen.py](../scripts/origin-screen.py) | The mechanical half of [origin-screen.md](origin-screen.md): screens `new/` (or bare `--domain`s) against `logs/drop-list.csv`, exits non-zero on `DROP` / `WATCH`, computes `NOVEL`; `--held` lists the hold queue lint #6 drains. Read-only. |
| *(the directory of every script)* | [scripts/README.md](../scripts/README.md) | What each script is, what calls it, and its lifecycle — standing (`scripts/`), bespoke (`scripts/extractors/{ISO3}/`), spent (`scripts/archive/`). `vault_lib` reads the vault; `finance_lib` knows what a deal record is. |
| *(`BUDGET-EXTRACT.md` steps 5a/6)* | [scripts/archive-budget-docs.py](../scripts/archive-budget-docs.py) | Archives a country's extracted budget documents to `budget-archive/{ISO3}/{FY}/` from the pass's scope CSV; dry-run by default; aborts if a document has no scope row; `--verify`. |
| *(step zero of `full lint`)* | [scripts/lint-deterministic.py](../scripts/lint-deterministic.py) | The mechanical checks in one command: #1 schema, #2 vocabulary, #3 `last_reviewed`, #4 wikilinks, #10 stranded `new/`, #11 filenames and shards, #12 link-list convention, #15 `body_completeness`, #24 register caps, #25 `CLAUDE.md` line cap, #28 deal-record fields, #34 catalogue hero, #38 de-accented Romance titles. Reports, never edits; `--check N`, `--all`, `--json`; exit 1 on any hard finding. |
| *(any script that reads the vault)* | [scripts/build-index.py](../scripts/build-index.py) | Rebuilds `index/` — frontmatter verbatim plus a derived block per artefact, and `links.jsonl`. Untracked, from scratch, never appended to; `--sql` builds `index/vault.db` on demand and any rebuild that does not refresh it deletes it; `--check` exits 1 if stale. |
| *(unwired)* | [scripts/build-catalogue.py](../scripts/build-catalogue.py) | Retired from the cycle — CORPUS builds its own catalogue from `raw/` and `wiki/`. Left standing. |
| *(lint #26)* | [scripts/lint-output-freshness.py](../scripts/lint-output-freshness.py) | Newest mtime in `outputs\non-state-finance\` against the last cycle close in `logs/sweep-cycle_log.md`. Report-only. |
| *(`SWEEP-CYCLE.md`, after the notes commit)* | [scripts/pull-new-queue.py](../scripts/pull-new-queue.py) | Moves every `X:\new-queue\` folder carrying `READY` flat into `new/`, adds `sweep_batch: <folder>-<date>` to a backfill-prefixed folder's candidates that carry none, leaves a `delivered-YYYY-MM-DD` marker; a name already in `new/` stays queued. Dry run by default, `--apply` moves. Replaces the hand-carry. |
| *(`SWEEP-CYCLE.md`'s close)* | [scripts/rotate-log.py](../scripts/rotate-log.py) | Truncates `logs/log.md` to its newest ~400 lines at an entry boundary, keeping the header. `--apply` acts, `--keep N` sets the budget. |
| *(`SWEEP-CYCLE.md`, first act, every stage boundary, and before the manifest)* | [scripts/usage-log.py](../scripts/usage-log.py) | Inserts `Date`, `Time (UTC)`, `7d usage` and `Session usage` (weekly plan limit used, and its rise since the row below, %) at the top of `logs/usage-log.csv`, newest first, from the endpoint `/usage` reads; `--stage NAME` records the reading in the git-ignored buffer `logs/usage-stages.jsonl` instead (`--csv` both, `--reset` empties it first), which `cycle-manifest.py --usage` writes as the manifest's `usage` block. Never blocks: a failed read writes `n/a`. |
| *(helper, by hand)* | [scripts/uncited-sources.py](../scripts/uncited-sources.py) | Lists admitted sources no `wiki/` page cites (finance and budget records excluded). `--recent 1` after a run should read 0. Read-only. |
| *(`WIKI-SYNC.md` step 9)* | [scripts/wiki-index-gen.py](../scripts/wiki-index-gen.py) | Regenerates the *Every intersection* block in `places-index.md` and `topics-index.md` from `wiki/intersections/` — one line per place and per topic, each pointer labelled by the other axis. Owns its markers and asserts nothing outside them moved before it writes; refuses a page carrying no `place:` or `topic:`. `--check` exits 1 when a block is stale, `--diff` shows what it would change, `--shape` picks the row form, `--gaps` writes the per-page measurement. |

**Archived** ([archived-procs/](../archived-procs/) — kept for reference, not run)

| Was | File | Why archived |
|---|---|---|
| `run non-state finance load` | [finance-load-nonstate-csv.md](../archived-procs/finance-load-nonstate-csv.md) | One-off initial load of the non-state deal CSV; finished. Ongoing capture runs through the spec. |
| `run budget consolidation` | [BUDGET-CONSOLIDATE.md](../archived-procs/BUDGET-CONSOLIDATE.md) | One-off migration to the accreting per-line/year shape; finished, with its two scripts in `scripts/archive/`. |
| Country ingest workflow | [country-ingest-workflow.md](../archived-procs/country-ingest-workflow.md) | Country-by-country procedure over the `external-datasets/` corpus. Superseded. |
| `backfill <ISO3>` | [BACKFILL.md](../archived-procs/BACKFILL.md) | Drained a country's pre-staged content from `X:\new-queue\<ISO3>\`. Archived 2026-09-08 (Bill). |
| `backfill batch` | [BACKFILL-BATCH.md](../archived-procs/BACKFILL-BATCH.md) | The loop around `backfill <ISO3>` over every folder in `X:\new-queue\`. Archived 2026-09-08 (Bill). |

The folder also holds those runs' data artefacts — source CSVs, crosswalks, run logs, `external-datasets/` — inputs and records, not processes.

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
| `outputs/budgets/` | export (derived) | `{ISO3}-budget.csv` — one row per domestic budget line-year, compiled from the finance records by `build-finance-page.py`. Not sources; do not hand-edit. |
| `outputs/non-state-finance/` | export (derived) | `{ISO3}-nonstate.csv`, `{ISO3}-summary.csv`, `all-nonstate.csv`, same compiler. Outputs only: the compiler's two inputs — `lookups/fx-imf-annual.csv` (USD-conversion rates) and `lookups/financier-names.csv` (the approved `financier_slug → canonical_name` map) — live with the other vocabularies. |

## State — not kept here

Two live surfaces hold it, and this page holds neither:

- **Corpus counts** — `repo status` ([REPO-STATUS.md](../REPO-STATUS.md)), which writes `reviews/repo-status.md` from `scripts/repo-status.py`: documents by publication year, by month for the current year, and by country/place.
- **Queue counts** — `wiki status` ([STATUS.md](../STATUS.md)): the standing counts and the half-finished-state gates, defined once and read live.

Batch-by-batch ingest history is not kept here either — it is in [log.md](../logs/log.md) and git. This page holds structure, not chronology.
