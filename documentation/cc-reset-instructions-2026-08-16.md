---
type: doc
title: Reset instructions — migration + sweep-cycle reform
created: 2026-08-16
audience: CC sessions in OSINT
status: to be worked in order, Sessions 1→3
---

# Reset instructions, 2026-08-16

*(Context: OSINT was dark 2026-08-12 → 2026-08-16 after credit exhaustion. The 08-11 night shows why: update-wiki alone spent 33 sub-agents over ~7h, ingest 31 over ~6h40m, and one evening run cost ~$83 — most of it adjudication and keep-both/replace deliberation. Two rulings from Bill, 2026-08-16, govern everything below: CORPUS now owns the output layer, and no regular sweep may consume more than 10% of usage. Perfect has become the enemy of good; the review-and-comparison machinery goes.)*

**Work these as three sessions, in order.** Each session commits as it goes, logs one-line entries per `STATUS.md`, and updates `wiki/index.md` → *Processes* in the same edit that creates, changes or retires a process. Sonnet everywhere; by the end of Session 2 nothing in the vault invokes Opus.

## Session 1 — action the migration

`documentation/osint-migration.md` is the brief; every ruling it was waiting on has been made, so nothing in it is an open question. **All retirements are permanent** *(Bill, 2026-08-16)* — nothing retired here is rescheduled, parked or kept as an option.

1. **R10's boundary statement into `CLAUDE.md` first.** OSINT collects and classifies; CORPUS compiles, reports and analyses over a read-only view; OSINT writes nothing to CORPUS and reads nothing from it. Per `CLAUDE.md`'s no-new-rule-without-deleting-one, fold it into *Purpose* or *Output* rather than adding a section.
2. **R8's live half.** Commit the unstaged `mirror.bat` / `Repo-mirrors.ffs_batch` deletions, cut the `run mirror.bat` close step and `## Mirror` section from `SWEEP-CYCLE.md`, retire `LINT` #19 outright (never repoint it at CORPUS's log).
3. **R1, R2, R3, R6 together** — report layer, output refresh, REPORT-LINT's G–K half, and `outputs/reports/` + `outputs/catalogue/` out of git. Confirm CORPUS has a clean build first; keep one tagged commit as fallback. Rescope `LINT` #26 to `outputs/non-state-finance/` only. Checks A–F stay, folded into `LINT` or `FINANCE-COMPILE`.
4. **R4 as documented** — the finance export stays as OSINT's own compile; change nothing in the script or step, only what the docs say the folder is for. R5 needs no action.
5. **R7** — remove the report-layer specs and `scripts/report-*.py` per its list, grepping first as it directs. `report-lint.py` and `compile-hub-financing.py` stay.
6. ~~**R9** — wire `ACQUIRE` (and the deep/country sweeps) to read `C:\CORPUS\logs\requests-for-osint.csv`, read-only, the single exception to the one-way boundary. Land a real request in it before wiring, or there is nothing to test against.~~ **Withdrawn** *(Bill, 2026-08-16, `documentation/osint-no-request-feed.md`)* — `C:\CORPUS` is not reachable from the machine OSINT runs on, and the feed was unnecessary besides: Bill hands open requests to a session as its brief, and `ACQUIRE` already knows what to do with one. The boundary loses the exception rather than gaining a workaround — OSINT reads nothing from CORPUS, ever.
7. **R11 with its precondition** — write the 291-row region-membership lookup (slug, `entity_type`, place codes) to `lookups/` and name the file in `osint-migration.md` before deleting `wiki/entities/` pages, `entities-index*.md` and `ENTITY-PASS.md`. Keep the `entities:` tag on sources. Rewrite `CLAUDE.md` → *Entities*, `reference.md` §5/§9 and `LINT` #4 in the same change: a tag is a terminal state, not a page deferred.
8. **R10's pruning last** — strip retired-pass references from `SWEEP-CYCLE`, `STATUS.md`, `wiki/index.md`, `CLAUDE.md`, `reviews/housekeeping-jobs.md`, `reviews/acquisitions.md`, and `REPORT-LINT.md`'s cross-references to the departed G–K.

Respect the guardrail list in `osint-migration.md` → *What OSINT keeps* throughout — but note Session 2 amends how some of the kept processes run, not whether they exist.

## Session 2 — the lean sweep night

**The regular night does five things and stops: find new content; check for duplicates; check for relevance; classify by place and subject; write to `raw/`.** *(Bill, 2026-08-16.)* Everything model-deliberative beyond that leaves the nightly path. Rewrite `SWEEP-CYCLE.md` and `INGEST.md` to the shape below, deleting the superseded text rather than layering on it.

### The new nightly sequence

```
Exa canary — on failure STOP, write nothing
select day D from the rotation (unchanged mechanics: oldest Start, Skip, Gate, New-Start)
run SWEEP-DAILY-LIST, SWEEP-DAILY-OFFLIST, then D's jobs   (stage-only, as now)
run INGEST Phase A over the night's catch                   (lean form, below)
scoped script compiles — compile-hubs.py and FINANCE-COMPILE fire from ingest as now
quick lint — mechanical nightly subset only
prune sweep-url_log, rotate log.md, close the day
```

Gone from the night, permanently: REPORT-UPDATE, output refresh, REPORT-LINT as a pass (Session 1), the mirror (Session 1), and — moved, not retired — Phase B, reconcile and acquire (below).

### Ingest, lean form

Phase A keeps its four dispositions and its step numbers, with these amendments:

- **Dedup is mechanical plus one cheap call, drop-by-default.** Tier 1 (URL grep) and tier 2 (candidate narrowing) stay as written. Tier 3 becomes a single Sonnet judgment on titles and ledes of the narrowed handful: **drop unless clearly a new event**. No reading of held full bodies, no replace/keep-both analysis, no tier-upgrade hunting. A near-duplicate admitted, or a marginally better copy dropped, is an accepted cost — `raw/` is greppable and a later pass can tidy. *(Decision taken drafting this, Bill expressed no preference — revert by restoring INGEST.md §2 tier 3 from git.)*
- **Delete `.claude/agents/adjudicator.md`** and every reference to it (`INGEST.md` §2/§7, `RECONCILE.md` step 4, `SWEEP-CYCLE.md` model policy). Opus is no longer invoked anywhere in the vault.
- **Relevance is a scope check, nothing more.** `CLAUDE.md` → *The material* as now: when in doubt, reject. No re-reads, no second opinions.
- **Classification is the frontmatter facets** — place, subject, 3–6 entities, dates — plus a `hub_line` written as **one plain sentence** from the text already in hand. Strike INGEST.md's "dense analysis… where much of the value is made" framing; the compile needs a bullet, not an essay. The one-carrier-per-event grouping sweep stays (it is one cheap pass).
- **Contradictions and acquisitions: keep filing, never research.** *(Bill, 2026-08-16.)* One-line briefs at the moment of tripping over them, exactly as INGEST.md §7–8 already direct; all research stays in the reconcile/acquire passes, which no longer run nightly.
- **Document-chase (step 3's primary-document rule) is time-boxed to one attempt** on the night; failure files an acquisition line and moves on.

### WIKI-SYNC — the deliberative work, off the nightly path

Create `WIKI-SYNC.md`: one process that drains `logs/ingest-pending-writes.md` (Phase B, per page, idempotent, as INGEST.md Phase B now specifies), then reconcile over all open contradictions, then acquire over all open lines, **looping at most 3 times** *(Bill, 2026-08-16)* since reconcile and acquire stage primaries back into `new/`. Queues still open after 3 iterations wait for the next sync — logged, never chased. Add it to the rotation as its own row (`@WIKI-SYNC`), giving it the same roughly-weekly cadence Day 8 gives LINT; it counts against its own night's budget like any other day. Move INGEST.md's Phase B text into it and leave a pointer.

### The 10% cap — a hard brake with a clean exit

This supersedes the 2026-08-10 "monitor and alarm, never a brake" ruling *(Bill, 2026-08-16)*.

- **The budget is the sub-agent count, enforced by script, not prose.** Set the nightly budget to **90** — the existing 130 was a proxy for weekly-limit ÷ 7 (~14%); 90 is the same proxy scaled to 10%. When someone reads the real weekly figure off `/usage`, replace 90 with that ÷ 10.
- **The brake fires between steps, never mid-step.** Extend `scripts/cycle-open.py` or add `scripts/budget-check.py`: the parent checks the count before each step and each Phase A slice; over budget, it finishes nothing new, writes the close (log lines, `braked=yes` on the closing line), and exits cleanly. `new/` is a physical queue, so an unstaged remainder is next night's work by construction — if the sweeps completed, close the day normally (the catch is staged; ingest resumes from `new/`); if a sweep itself was braked, leave the day open per the existing not-closed rule.
- **`--nobrake`** — typed as part of the trigger (`run the sweep cycle --nobrake`; `sweep.bat` deleted, note 22, 2026-08-17) — disables the brake for that night only. For special cases, hand-typed; nothing defaults to it.

### Model policy

Sonnet at every level, parent and sub-agents, no exceptions and no declared Opus subagent. If a class of error recurs that Sonnet demonstrably cannot handle, that is a `[DECIDE]` note with the evidence attached, not a re-instatement.

## Session 3 — the backlog

Five dark days plus the interrupted Day 1 (`New-Start` 2026-08-11 19:55, never closed; the 08-11 catch was ingested at 05:13–05:42 on 08-12, so `new/` should be near-empty — verify with `ls`, don't assume).

1. Run Sessions 1 and 2 first, so the catch-up runs on the thin night, not the old one.
2. Run the cycle with `--nobrake` *(Bill, 2026-08-16: the backlog is the special case the override exists for)*. Selection will pick Day 1 again (oldest `Start` 2026-08-04); its window computes from that old `Start`, so the dark days are covered by design — no manual window arithmetic.
3. **Bill runs this step by hand, night by night — CC never chains or automates it** *(Bill, 2026-08-16)*: repeat nightly runs (braked, normal) until every row's `Start` post-dates 2026-08-16, then one `WIKI-SYNC`. A session finishing step 2 stops there and reports; it does not launch the next run.
4. Check `reviews/post-run-notes.md` against the 10-note cap after the catch-up; action per the standing rule.

## Reporting

Unchanged: each pass one `log.md` line, the two-line close per `STATUS.md`. Add `braked=yes|no` and the sub-agent count to the run-cost line so the 10% cap is visible night by night without reading anything else.
