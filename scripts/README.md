# scripts/ — what is here, and what happens to it

*(Written 2026-08-03, review task 25. The wiki was at 53 scripts with 40 countries still to initialise and roughly four one-off scripts per country: the arithmetic said 170 more. This file, the lifecycle labels and the two shared libraries are what stop that.)*

## Two libraries, and the line between them

**`vault_lib.py` is the read layer.** One frontmatter parser, one URL normalisation, and `index/` — the rebuildable index of every artefact's frontmatter plus the citation graph. Anything that needs to know *what the vault holds* imports this.

**`finance_lib.py` is the finance and budget domain.** Record parsers, the FX table, canonical financier names, the place tree. Anything that knows what a *deal record* or a *budget line* is imports this.

A new script imports both rather than re-implementing either. The one duplication that is deliberate: `finance_lib`'s `fm_get` reads one key out of a record whose shape the caller knows, in a hot loop over 8,000 files, while `vault_lib.parse_frontmatter` builds a complete typed object with warnings. Both are right for their job.

## A check that reads nothing must never look like a check that found nothing

*(2026-08-22, note 34 — CORPUS hit this in its own `report-register-check.py --unit all`, which matched a unit literally named `all`, ran over nothing and printed a clean pass while the same command with no `--unit` reported 78 failures.)*

**A filter argument that selects nothing is refused, exit 2 — never reported as a clean run.** A mistyped check number, ISO-3 or unit is the most likely reason a selector matches nothing, and the two outcomes are indistinguishable from the outside: zero findings over everything, and zero findings over nothing. Three of OSINT's own scripts had the shape and were repaired the same day — `lint-deterministic.py --check N`, `report-lint.py --check ABCDEF`, `compile-hub-financing.py ISO3`. **Any new script taking a filter names its known values in the refusal**, so the typo is visible in the message rather than in a silence.

## Three lifecycles

| Label | Where it lives | Test |
|---|---|---|
| **standing** | `scripts/` | A procedure calls it, or a standing script imports it. It runs again next week. |
| **bespoke** | `scripts/extractors/{ISO3}/` | Written for one country's documents and **plausibly re-run for that country** — next year's volume has the same layout. |
| **spent** | `scripts/archive/` | Its job is done and cannot recur: a completed migration, a housekeeping job that closed, a one-shot generator whose output is in the vault. |

**Spent is archived, not deleted** — the same rule `archived-procs/` applies to procedures. A one-shot generator is how a record set is *reproducible and auditable*, which is worth keeping even though it will never run again. Git holds it either way; the folder is what tells a reader which of the three it is without opening it.

**A new script declares its label in its docstring, on the first line, and lands in the right folder on the day it is written.** The cost of this file was one sweep of 53 scripts; keeping it true costs nothing.

## Standing

**Libraries**

| Script | Called by | What |
|---|---|---|
| `vault_lib.py` | every script below that reads the vault | Frontmatter parser, `normalise_url()` (INGEST step 2's contract as a function), `registrable()`, and the `index/` build/load surface. |
| `finance_lib.py` | the finance builds and lints | Record parsers (`split_front`, `fm_get`, `section`, `deal_table`, `raw_sources`), CSV helpers, `lookups/` readers: FX rates, financier names, the place tree. |

**The index and the catalogue**

| Script | Called by | What |
|---|---|---|
| `build-index.py` | any consumer, automatically | Rebuilds `index/` from scratch (~3s over 12k artefacts). `--db` for SQLite, `--sql` for a one-off question, `--check` to gate. |
| `build-catalogue.py` | run when the website is updated | `outputs/catalogue/` — the published, filterable catalogue of everything in `raw/`. Metadata only. |

**Lint and audit**

| Script | Called by | What |
|---|---|---|
| `lint-deterministic.py` | `LINT.md` step zero | Checks #1, #2, #3, #4, #10, #11, #12, #15, #23 over the whole vault in ~1s against `lookups/frontmatter-schema.json`, plus **#24** the register caps on `post-run-notes.md` and the 60-word note cap on the two `X:\` exchange files, **#25** the `CLAUDE.md` line cap and **#28** the three controlled deal-record fields against `lookups/deal-vocabs.csv`. Reports, never edits; `--ratchet` lowers #25's caps after a deliberate cut. |
| `lint-finance-slugs.py` | LINT #16 | `primary_subject` present and in `topics`; financier keyed on a canonical slug. Exits non-zero, so it doubles as an ingest gate. |
| `lint-acquisition-held.py` | LINT #22, `ACQUIRE.md` step 0 | Strikes an acquisition line naming a document already held. |
| `lint-unsourced-figures.py` | LINT #20 | Ledes carrying a ranking, market size or penetration figure with no source link. |
| `export-process-mirror.py` | `SWEEP-CYCLE.md` close, LINT #37 | Publishes the process layer to `data-landscapers/osint-process` from an allowlist, refusing on a long block quote or a secret; `--check` asks whether the last push has been exported. |
| `lint-mirror-head.py` | LINT #19 | Did the mirror actually run — `git -C O:\ rev-parse HEAD` against the local one. `O:\` is CORPUS's read path, so a mirror that stops publishes yesterday's evidence rather than losing any. It also asserts that the mirror's `cycle-manifest.json` names that same commit — the right tree with the wrong account of it is the same silent publication, one level in. Surface only; `--gate` exits 1 for a close step. Replaced `lint-mirror-freshness.py` on 2026-08-27, which read a log nothing writes any more. |
| `cycle-manifest.py` | `SWEEP-CYCLE.md`, `SWEEP-BULLETIN.md` — the close; `INGEST.md`'s close calls `--stamp` | Writes `cycle-manifest.json`, the one file CORPUS reads about a run: the commit the mirror carries, the collection window from `logs/collection-stamp.json` (written by `--stamp`, whatever pass most recently closed ingest), the rotation's newest close, the counts the pass passed in, and — schema 2, with `--usage`, the sweep cycle only — the night's per-stage plan-usage readings from `logs/usage-stages.jsonl` as a `usage` block keyed by stage. Git-ignored and written **after** the final commit, so `head` names the commit that is actually on `O:\`. `--check` asserts it names the local HEAD; counts are given, never inferred. Retires CORPUS's forensic parsing of OSINT's logs (strategic review task 14). Both files are gitignored and therefore unrestorable if removed — see the `.gitignore` warning above them and notes-for-osint 133, which cost a night's cycle to a stray deletion. |
| `effort-cap.py` | LINT #33 | What the run kept returning to — any item named in 3+ of the run's `log.md` entries is over, and is dropped or written up as a dated absence. Matches adjacent word pairs from `raw/`, `wiki/` and open-brief filenames against each entry's `<what changed>`, so the vocabulary is the vault's own and there is no stoplist to maintain. |
| `lint-duplicate-deals.py` | reconcile / LINT #7 | Cross-family duplicate deals — keys on financier + place + amount, deliberately not on recipient or year. |
| `lint-scope.py` | LINT #32 | Every `raw/` source sorted against the place bar in `CLAUDE.md` -> *The material* — **in** (African place or a `geopol.*` slug), **xgl** (`XGL` alone), **unaccounted** (neither, and the floor is 0). Reads frontmatter through the index, never a compiled view. `--since YYYY-MM-DD` is the nightly form and answers whether tonight's catch leaked; `--xgl` lists the standing set, which is a reading (housekeeping job 71) and never a defect. Exit 1 on any unaccounted. |
| `lint-url-log.py` | LINT #30 | Every `admitted`/`dropped`/`acquisition` line in `logs/sweep-url_log.md` joined against `lookups/raw-url-index.csv`, the staging folders, `rejected-urls.csv` and `drop-list.csv` — an `admitted` line with no `raw/` file is the defect #27 cannot see, because a URL the base does not hold reads CLEAN. Also asserts section-header arithmetic, `raw/` paths cited in a line's own reason, and URLs carrying two dispositions. `--all`, `--csv`, `--log FILE`. |
| `lint-pdftotext-enc.py` | LINT #31 | Every command-shaped `pdftotext` invocation in a procedure file, `documentation/` or a live script must pass `-enc UTF-8` — the default is Latin-1, and reading that as UTF-8 silently mangles every accented character, so a keyword scan reports a zero it has not earned. A backticked span naming a *behaviour* rather than running a command is left alone. `--list`. |
| `lint-duplicate-sources.py` | LINT #7 (narrative half) | Same-event clustering over ordinary `raw/` sources — shared entity + shared place + IDF-weighted title similarity, `hub_line_sources` pairs excluded as prior keep-both rulings. Reports candidates; rulings go in `reviews/source-duplicate-decisions.csv`. |
| `log-append.py` | every sub-agent that logs; LINT #29 (`--check`) | The only sanctioned writer of `logs/log.md` — reads the clock in **UTC** and inserts at the **top**, so no caller formats a timestamp or picks a position. **Refuses an entry over 40 words** (2026-08-27) — the reasoning that overruns it belongs in the commit body. Writes the pass in **bold capitals** (`**WIKI-STATUS**`) and **refuses a `decision`, `agent` or `slice` line outright** (2026-09-08): only a process's result and a fatal error earn one. `--check` audits the stamp and position defects after the fact and counts over-length entries without gating on them. |
| `assert-containment.py` | `SWEEP-CYCLE.md`, before each stage commit | The stage's write-set asserted against `git status`, with an absolute deny set on `CLAUDE.md`, the `wiki/` specs (`reference.md` and the five it indexes) and every root procedure. Exit 1 = do not commit as it stands. **`--patch <dir>`** is the same guard on a CORPUS patch series before `git am` (strategic review 4 R1): the paths its `diff --git` headers name, both sides so a rename counts on its source, against `scripts/`, `lookups/` and `wiki/places-index.md` / `wiki/topics-index.md`; `raw/` is refused by name because frontmatter work travels as a script and its input. A `BASE` file beside the patches is reported held or missing. Exit 2 on a directory holding no patch — a check that passes over nothing is worse than no check. |
| `audit-machine-records.py` | LINT #21 | The machine-record defect series. `--persist` appends the dated row and exits non-zero on deterioration. |
| `origin-screen.py` | `INGEST.md` step 1, LINT #6 | The inadmissible-origin gate: `DROP` / `WATCH` / `NOVEL` / `KNOWN`, and `--held` for the hold queue. |
| `report-lint.py` | `REPORT-LINT.md`, finance compile | The six checks (A–F) over OSINT's own finance/hub compile. Verifies, never compiles. |

**Compile and export**

| Script | Called by | What |
|---|---|---|
| `compile-hubs.py` | `HUB-COMPILE.md` | Place-hub *Recent developments*, compiled from each source's `hub_line`. |
| `hub-line-partition.py` | `INGEST.md` → *The `hub_line` gate* | Why each `raw/` source carries no `hub_line`, split by rule. **`--uncited` is the reading that matters**: `RESIDUAL-UNCITED` is the sources reaching neither a hub nor a page, and it is 0 (job 68, 2026-08-22) — non-zero means a run admitted one and wrote it nowhere. |
| `hub-line-set.py` | standing; hand-driven | Rewrite, add or strike a `hub_line` across many `raw/` sources from a JSONL of `{slug, hub_line}` / `{slug, strike}` edits. Dry run by default, `--write` applies; preserves EOL and leaves the rest of the file byte-identical, and writes the bullet as a one-line folded scalar so the diff is one line per edit. Written for job 70's bullet trim (2026-08-22) and kept: `hub_line` is bookkeeping, not evidence (`schemas.md` §4), so bulk edits to it recur. |
| `compile-hub-financing.py` | `FINANCE-COMPILE.md` step 2 | The hub `## Financing` aggregates. |
| `build-finance-page.py` | `FINANCE-COMPILE.md` step 4, `FINANCE-PAGES.md` | The per-country CSV exports in `outputs/`. `--all` for a full rebuild. |
| `finance-compile-scope.py` | `FINANCE-COMPILE.md`, `INGEST.md` | Which places' records changed since the last compile — 58 hubs down to typically one. |

**Entities**

**`ENTITY-PASS.md` retired 2026-08-16 (R11)** — the pass that minted and refreshed entity *pages* is gone; the `entities:` *tag* stays and is `INGEST.md`'s. The five scripts below were only ever called by that pass and are now orphaned — left standing, not deleted, in case a slug-drift or sovereign-naming fix is ever needed by hand again.

| Script | Was called by | What |
|---|---|---|
| `entity-census.py` | `ENTITY-PASS.md` | The census: who is tagged, how often, who is over the (now-retired) §5 paging bar. |
| `entity-mint-apply.py` | `ENTITY-PASS.md` | Applies `reviews/entity-mint-decisions.csv`. |
| `entity-slug-pairs-decide.py` | the entity pass | Adjudicates census drift pairs into `reviews/entity-slug-pairs.csv`. **Writes that register on a bare run** — pass it a flag knowingly. |
| `entity-slug-merge.py` | the entity pass | Applies the merges that register decided. Dry-run by default. |
| `sovereign-slug-apply.py` | `ENTITY-PASS.md` | One slug form per sovereign borrower. Dry-run by default. **`reviews/sovereign-slug-map.csv` itself stays live** — `lint-finance-slugs.py` (LINT #16) reads it directly; only this apply script is orphaned. |

**Budget and intake**

| Script | Called by | What |
|---|---|---|
| `archive-budget-docs.py` | `BUDGET-EXTRACT.md` steps 5a and 6 | Sets the four manifest columns and moves artefact + companion into `budget-archive/{ISO3}/{FY}/`, for **any** country, from a small scope CSV the pass writes. Replaced four per-country copies. Tested: `scripts/tests/test-archive-budget-docs.py`. |
| `ocr-pdf.py` | `BUDGET-EXTRACT.md` → Inspect | OCR an image-only PDF to pdftotext-compatible text. |
| `ingest-lane.py` | `INGEST.md` → *Two lanes*, `UPDATE-WIKI.md` | Which lane each candidate in `new/` takes, off `sweep_batch:` — `status-acquire-*`, `progress-filler-*` and `dataset-*` are the backfill lane, everything else is news. A whitelist, so an unrecognised producer costs a full-price run rather than a silent skip. `--lane backfill` prints just that list, for slicing. Assigns the lane; only `update wiki backfill` opens it. |
| `url-log-append.py` | sweeps and ingest | Writes one disposition line into `logs/sweep-url_log.md`, normalised. Takes an exclusive `<log>.lock` around the read-modify-write, because thirty Phase A slices write this file at once. Refuses `acquisition` for a URL whose disposition is already `admitted` — held in `raw/`, or logged so — and exits 3 having written its other URLs: an acquisition raised *by* an admitted source names some other document, and a document with no URL of its own has no key in a URL-keyed log and belongs on `reviews/acquisitions.md` alone. |
| `raw-url-index.py` | the sweeps' dedup (section 3), `INGEST.md` steps 2 and 11, LINT #27 | The `raw/` URL index — `--check` a candidate against `lookups/raw-url-index.csv` in ~0.3s instead of a corpus grep, `--append` on admission, `--remove` on retire/replace, `--rebuild` (~3s) as the only scan, `--lint` for the count. Adds `slug_key`: same host, same final path segment, new path is a duplicate exact-URL matching misses. The key is **percent-decoded and diacritic-folded**, so `communiqu%C3%A9-…` and `communique-…` are one key — 213 of the index's keys carried an escape and the fold creates zero new same-host collisions. It never folds a hyphen against a letter: ANGOP writes a diacritic as a hyphen, but its lone-letter segments are mostly the Portuguese words *e* and *a*. |
| `status-acquire.py` | `STATUS-ACQUIRE.md`, every step | The row ledger over `X:\africa-acquire.csv` — CORPUS's list of sources it cited in the country status reports and OSINT does not hold. `--list` the outstanding rows per ISO3, `--select ISO3` writes the run manifest to `sweep/status-acquire/` pre-marking rows the vault already holds or has rejected, `--mark` records an outcome from URLs on stdin, `--close` moves the country's rows into `X:\acquire-done.csv`. **The only writer of either CSV** — CORPUS writes to the same file. |

**Reading and hygiene**

| Script | Called by | What |
|---|---|---|
| `repo-status.py` | `REPO-STATUS.md` | The corpus report — by year, by month, by place. Capture intensity, not activity. |
| `page-index.py` | by hand | A page's *shape* without reading the page: section sizes, bullet index, `## By place` cells against the §8 bar. |
| `uncited-sources.py` | `INGEST.md` close | Admitted sources no `wiki/` page cites — the inverse of lint #4. **`--fm-only`** reports the other half: sources registered in a page's frontmatter `sources:` and written into no body prose anywhere, which the default count reads as *cited* (291 corpus-wide, 2026-08-21). |
| `wiki-index-gen.py` | `WIKI-SYNC.md` step 9 | The intersection enumeration, generated into both faceted indexes. A pure function of `wiki/intersections/`, so `--check` is a true invariant and never fights an editor; the curated cells above the block stay hand-written. Jobs 89 and 117. |
| `reflow-md.py` | `CLAUDE.md` → Writing | One line per paragraph. `--check` reports what still wraps. |
| `prune-dated.py` | `PRUNE.md`, LINT #18 | The dated retention row: `sweep/*/` manifests and drop-logs at 60 days, never a folder's newest of either. Report by default; `--apply` acts. Its `logs/log.md` job moved to `rotate-log.py` on 2026-08-10. |
| `pull-new-queue.py` | `SWEEP-CYCLE.md`, after the notes commit | Moves every `X:\new-queue\` folder carrying `READY` flat into `new/`: copy, byte-compare, then delete from the queue; adds `sweep_batch: <folder>-<date>` to a `status-acquire-`/`progress-filler-`/`dataset-` folder's candidates that carry none; leaves a `delivered-YYYY-MM-DD` marker. A different file of the same name already in `new/` stays queued and the folder is retried. Dry run by default, `--apply` moves; exits 0 always. |
| `rotate-log.py` | `SWEEP-CYCLE.md` close | Truncates `logs/log.md` to its newest ~400 lines at an entry boundary, keeping the header; git holds the rest. Report by default; `--apply` acts, `--keep N` sets the budget. |
| `usage-log.py` | `SWEEP-CYCLE.md`, first act, every stage boundary, and before the manifest | Inserts `Date`, `Time (UTC)`, `7d usage`, `Session usage` (weekly plan limit used, %, and its rise since the row below) at the top of `logs/usage-log.csv`, newest first, read from the endpoint `/usage` uses. `--stage NAME` writes the reading to the git-ignored buffer `logs/usage-stages.jsonl` instead, to one decimal place; `--csv` writes both from one reading; `--reset` empties the buffer first. Never blocks; a failed read writes `n/a` (CSV) or `null` (buffer). |
| `repair-eol.py` | by hand, after a sub-agent stage | Repairs line-ending flips against HEAD, preserving each file's own mixture — the defect `assert-containment.py` refuses a stage for. Listed here 2026-09-08; it was standing and unregistered. |
| `pdf-geom-rows.py` | by hand, writing an extractor | Dumps a PDF's pages as geometry-bound rows (characters by baseline, columns by x-gap) — the generic form of the binding the `extractors/{ISO3}/` scripts each hard-code. Needs `pdfplumber`. |

## Bespoke — `extractors/{ISO3}/`

A country's documents have a layout, and the layout recurs annually. These are the extractors that earned a home rather than an archive.

| Script | Country | What |
|---|---|---|
| `extractors/BFA/bfa-volume-scan.py` | Burkina Faso | Cross-vote scan of a *loi de finances* volume (`pdftotext -table`). |
| `extractors/CAF/caf-cdmt-extract.py` | Central African Republic | The CDMT sectoriels — budget détaillé par activité. |
| `extractors/CAF/caf-simba-extract.py` | Central African Republic | SIM_ba volume, PLF charges. |
| `extractors/CMR/cmr-plf-extract.py` | Cameroon | PLF programme tables, by page geometry. |

All four need `pdfplumber`, which is not a dependency of anything standing.

## Spent — `archive/`

Kept for the audit trail, not for running. Twenty-three scripts, the newest two archived 2026-09-08 with housekeeping job 30 long closed — `byplace-extract.py` (its step b) and `lint-index-dates.py` (step d, which called itself a standing check that no `LINT.md` number ever named, so nothing ran it): the four per-country `archive-*-budget-docs.py` (replaced by `archive-budget-docs.py`), the five `gen-*-records.py` one-shot generators whose records are in `raw/` and whose figures were hand-read from the printed volumes, the BEN/BWA/CIV staging and companion writers, and the closed migrations — `consolidate-budget-lines.py` and `backfill-baseline-capital.py` (with `archived-procs/BUDGET-CONSOLIDATE.md`, which instructed its own archiving), `shard-raw.py` (housekeeping 18), `fix-body-completeness-generated.py` (22), `restore-topic-order.py`, and `deal-vocab-backswing.py` (`DEAL-VOCAB.md` section 3, run 2026-08-20 over 1,260 deal records).

**The `gen-*-records.py` family was not merged into one generator, deliberately.** Their bulk is not logic — it is figures read off a printed volume by hand and cross-footed to a printed total, plus that country's own findings written as record notes. A shared template would have forced the next country's genuine findings into somebody else's sentences. What *was* shared out of them is in `finance_lib`.

## Where a new script goes

1. Does a standing script already do it? Extend that one.
2. Is the logic country-independent and the country-specific part **data**? Then it is standing, and the data is a CSV the pass writes — that is what `archive-budget-docs.py` is.
3. Is it one country's document layout? `extractors/{ISO3}/`.
4. Will it run exactly once? Write it, run it, and move it to `archive/` in the same session — not "later".
