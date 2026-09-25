<!-- reader: cc; type: runbook -->
# LINT.md — the lint pass

Trigger: **"full lint"** (also **"run lint"**). Checks #1–#41: **"quick lint"** at every cycle close, **"full lint"** at every night's close (`SWEEP-CYCLE.md` → *The nightly close*). **`update wiki` does not lint.**

Procedure only: §3 is `layout.md`, §4 `schemas.md`, §8–9 `operations.md`, dedup `CLAUDE.md` → *Duplicates*; the reasoning behind a check is `wiki/lint-checks.md`. **Check numbers are permanent handles** — never renumber, never reuse; the order below is run order.

## Lint acts and logs. It does not report.

Every check has one correct action; lint takes it, in git, and records a count. It surfaces **only** a genuine contradiction, to `reviews/contradictions/open/` — **never a to-do list**; a wrong auto-fix is a revert.

## Cadence

**nightly** — quick lint runs the check's script and applies only fixes needing no reading of page content. **nightly (new records)** — **#6, #4, #5, #34, #14, #20, #7**: quick lint also reads and judges, over the `raw/` files this run admitted (`git diff --name-only --diff-filter=A <ingest-commit>^ <ingest-commit> -- raw/`); **#6 runs whole-corpus every time**. **batched** — **#8, #9, #23, #13, #17 and #3's fix half**: full lint only; a whole-vault check moves to nightly once it carries a looked-and-left stamp. A check finding nothing reports a zero.

## Running it

**Step zero: `python scripts/lint-deterministic.py`** — the mechanical checks; reports, never edits; `--check N`, `--all` for soft findings. **#12 before #4**, **#15 before #7**, **#6 before #17**.

## The checks

**39. Artefact md5 collisions** — surface, scripted, nightly. `--check 39`, over `lookups/artefact-md5-index.csv` (appended at `INGEST.md` step 11; never rebuilt here). A legitimate collision is ruled with its reason in `lookups/artefact-md5-allowed.csv`; a retirement is never automatic.

**37. Process mirror current** — surface, scripted, nightly. `python scripts/export-process-mirror.py --check`. Never auto-fix (`SWEEP-CYCLE.md` → *The process mirror*); exit 2 is GitHub unreachable, not a defect.

**36. Entity slugs with no referent** — surface, scripted, nightly. A `wiki/` `entities:` slug no `raw/` source tags: fix a typo, allow a real actor. Soft; rulings in `lookups/entity-slugs-ruled.csv`.

**1. Schema integrity** — auto-fix, scripted, nightly. Fill missing required frontmatter from what the page carries; where it cannot be inferred, surface — never guess.

**35. Hard-wrapped paragraphs** — auto-fix, scripted, nightly. `python scripts/reflow-md.py` over `wiki/`, `reviews/`, `logs/`; it refuses `raw/` and the append-only ledgers.

**12. Link-list convention** — auto-fix, scripted, nightly. Normalise `sources:` / `entities:` to `[[a], [b]]`.

**2. Vocabulary** — auto-fix, scripted, nightly. Correct a `topics` or place slug to the controlled value; a genuinely new value → surface.

**11. Missing date prefix, or wrong shard** — auto-fix, scripted, nightly. Rename to the `YYYY-MM-DD` prefix, updating links; unestablished → `date_source: proxy` at best precision; a corrected date moves the file.

**4. Orphans & dead links** — auto-fix, scripted, nightly. Index absent pages; rewire or retire broken `[[links]]` per §9's bands, never touching entity slugs, the intentional-dead whitelist, convention files or dated logs.

**5. Untagged sources** — auto-fix, nightly (new records). Tag per `CLAUDE.md` → *Entities*; sparse `entities` on thematic sources are not defects.

**38. De-accented Romance titles** — surface, scripted, nightly (new records). `--check 38`. **Never auto-fix and never spell it yourself**: refetch the source's own heading and correct `title:` only. Pre-2026-09-17 sources are one soft backlog line; `DEACCENT_EXEMPT` holds two permanent exemptions.

**34. Catalogue hero** — auto-fix, scripted detect, nightly (new records). `--check 34`. A missing or malformed post-contract hero is **written or rewritten** per `schemas.md` §4, with `scripts/catalogue-hero-set.py` past a handful; nothing is surfaced. Pre-contract sources are one soft line.

**32. Place bar** — surface, scripted, nightly (new records). `python scripts/lint-scope.py --since <the run's date>`, never whole-vault. **xgl** is reported, never a defect; **unaccounted** has floor 0.

**15. `body_completeness` backfill** — auto-resolve, scripted, nightly. Set from the stored body by markers; ambiguous → inspect or leave blank. Never set `full` on a body no check has passed over.

**7. Duplicates** — auto-fix, nightly (new records). `scripts/lint-duplicate-deals.py` and `scripts/lint-duplicate-sources.py` cluster on **event + entities + date** — candidates, never verdicts; adjudications to `reviews/source-duplicate-decisions.csv`. Resolve per `CLAUDE.md` → *Duplicates*; a retirement rewires `sources:` in `wiki/` **and `raw/`**, removes the URL-index row, appends a `dropped` URL-log line and names the `survivor`. Differing payloads → keep both, or #9.

**14. `url:` quality** — auto-fix, nightly (new records). A bare-domain, blank or missing `url:` needs the document URL, found and verified by title and date, never constructed from a pattern; exhausted → `url unrecovered as of YYYY-MM-DD`. Never edit `published`.

**16. Finance record keys** — auto-fix + defect list, nightly (defects batched). `scripts/lint-finance-slugs.py` (non-zero on a financier defect — an ingest gate). Fix the mechanical; surface the rest as a defect list drained like a contradiction.

**21. Machine-record audit** — auto-fix, surface on a rise, nightly. `python scripts/audit-machine-records.py --persist`; fix a rise from the defects CSV; a class-3 hit read as complete goes to `logs/machine-record-audit-cleared.csv`.

**3. Freshness** — auto-resolve, partly scripted; nightly detect, batched fix. `last_reviewed` over 90 days; newest source over 2 years old on a topic with sources under 6 months; undated time-varying figures; money breaking `CLAUDE.md` → *Currency*. Date, rephrase or write the dated absence; never invent a rate.

**20. Unsourced lede figures** — auto-resolve, nightly (new records). `python scripts/lint-unsourced-figures.py`. A `[[link]]` is not provenance: cite what `raw/` holds, else write the dated absence and drop the figure.

**8. Page bloat** — **count only, scripted, batched; it trims nothing and registers no job.** `--check 8 --all` prints `pages_over_line` for the manifest; the gate is at the writer (`WIKI-SYNC.md` → *A landing page over its line*), so a climbing count is a writer missing it. Shard an oversized index.

**13. Quarantine leaks** — auto-fix, batched. A `wiki/` citation of `reviews/contradictions/research/` or a `DO-NOT-INGEST` file: rewire to the primary or remove.

**6. Inadmissible sources** — auto-resolve, nightly (new records). An origin failing `CLAUDE.md` → *The material*: demote to a lead, or strike and mark for re-sourcing. Screen a domain against `wiki/origin-screen.md` and write its `drop-list.csv` row **in the same edit**. **Scripted half**: `raw/` records whose `url:` host is on a `drop` domain, matched on the full host.

**17. Sweeps call the origin screen** — auto-fix, batched. Every root `*SWEEP*.md` references `wiki/origin-screen.md`; every `drop-list.csv` row is `drop`/`watch`; every #6 domain has its row.

**40. A record no parser can read** — auto-fix, nightly. `raw/*.md` read **as bytes** against the one frontmatter regex; a doubled CR or lost newline at the fence is a **hard finding**. Repair the terminators only, asserting that stripping every CR leaves both sides identical — never a re-capture.

**22. Acquisition names a held document** — auto-fix, nightly. `python scripts/lint-acquisition-held.py`: apply **STRIKE**, read and rule on **CANDIDATE**, never the other way round. `--fix-markers` repairs a line hidden from the count.

**27. `raw/` URL index matches `raw/`** — rebuild on mismatch, scripted, nightly. `python scripts/raw-url-index.py --lint`; mismatch → `--rebuild`, never an investigation.

**30. Every adjudication in `sweep-url_log.md` has a record** — surface, scripted, nightly. `python scripts/lint-url-log.py`. Never auto-fix.

**18. Register pruning** — auto-fix, nightly. Run `PRUNE.md`; report what it deleted; surface a stale next-number counter.

**29. The hand-stamped log** — surface, scripted, nightly. `python scripts/log-append.py --check`. Never auto-fix; `log-append.py` is the writer.

**19. Mirror HEAD matches local HEAD** — surface, scripted, nightly. `python scripts/lint-mirror-head.py`; the mirror's `cycle-manifest.json` must name the same commit. Never gating; `--gate` exits 1 for a close step that wants it.

**33. Per-item effort cap** — surface, scripted, nightly. `python scripts/effort-cap.py`. An item named in three of the run's `log.md` entries: drop it, or write the dated absence — never a fourth pass.

**24. Register caps** — auto-fix, scripted, nightly. `post-run-notes.md` against `CLAUDE.md` → *Reporting*; over the open cap, take the conservative option and say so. On the share, an over-cap preamble or a convention restated outside `X:\README.md` → *Conventions* fails, and every open note needs a reachable `Affects:` line — hard on OSINT's files, soft on CORPUS's.

**41. Documentation caps** — surface, scripted, nightly. `python scripts/lint-docs.py --report`: every root, `documentation/` and `wiki/*.md` file names its reader on its first line and stays under `CLAUDE.md` → *Documentation caps*. A missing reader is stamped on sight; **a length breach is listed, never trimmed by lint**.

**25. `CLAUDE.md` length** — surface, scripted, nightly. `CLAUDE_MD_CAP` (123 lines). Never auto-fix. A lapsed `frozen until YYYY-MM-DD` is a hard finding: renew or delete it.

**31. `pdftotext` carries `-enc UTF-8`** — surface, scripted, nightly. `python scripts/lint-pdftotext-enc.py`.

**26. Output freshness** — surface, scripted, nightly. `python scripts/lint-output-freshness.py`; never fix — `FINANCE-COMPILE` is the fix.

**9. Contradictions** — surface, batched. File any conflict uncovered to `reviews/contradictions/open/`; report the count.

**23. Region place code** — surface, scripted, batched (judgment). Three countries of one region with no `X__` code is a candidate: a cross-border framework earns it, one operator in three markets does not.

**28. Deal-record vocabulary** — surface, scripted, nightly. Controlled fields against `lookups/deal-vocabs.csv` (`DEAL-VOCAB.md`). Never auto-fix.

**10. Stranded queue items** — surface, scripted, nightly. Anything left in `new/` after an ingest; report the count.

## Close

Close on `STATUS.md`'s standing count line, plus one line per check that acted.
