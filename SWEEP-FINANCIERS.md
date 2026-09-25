<!-- reader: cc; type: runbook -->
# Sweep — financiers (procedure)

**Financier-scoped deep research, one loop.** It walks `lookups/sweep-financiers.csv` (maintained by Bill) and runs one Exa Agent brief per financier, hunting what the money is doing — commitments, plans, reviews and the critique of them — from the *financier's* side rather than the recipient's.

Run by `SWEEP-CYCLE.md` on its rotating day; also runnable standalone ("**run the financiers sweep**"). `logs/sweep-cycle_log.md` holds which day it runs on; this file names no day of its own.

## 0. One-line purpose, and the overlap it accepts

Deep research on the **financier layer**. **Every other finance instrument is scoped by the recipient; this one walks the funder**, whose own strategy is reported at the financier and has no single recipient to be found under.

**It will re-surface material the cycle already holds.** The overlap is **managed at staging, not avoided** (§5) and settled at ingest — `CLAUDE.md` → *Duplicates*, plus `wiki/finance-record-spec.md` → *Merging later reporting into a record*. **No value judgement at staging**: the bar is scope, not novelty (`SWEEP-REGIONAL.md` §0).

## 1. Shape — one loop

**One loop, one Agent brief per financier.** The **parent** loads and parses both lookup files at run-time, resolves each slug to its canonical name, and hands each sub-agent its rows inline (§7).

- **`lookups/sweep-financiers.csv`** is a bare list of financier slugs, one per line, and **is the rotation's subject list** — the financiers Bill wants watched. Adding a line adds a financier; nothing else changes.
- **Slugs in, names out.** `lookups/financier-names.csv` maps `financier_slug,canonical_name` and covers every slug in the sweep list. **The parent resolves the name and passes the name to the brief**, never the slug. Keep the sweep list as slugs (the finance compile groups on `financier_slug`).
- **A slug with no row in `financier-names.csv` is a run-time error, not a silent skip** — the parent notes it in the closing line and passes over that financier.
- **Output:** candidate source files in `new/` only. Never `raw/`, never a `wiki/` page — ingest is the only door (§5).

## 2. Target

| Drives the loop | Per-item scope | Seek |
|---|---|---|
| `lookups/sweep-financiers.csv`, resolved through `lookups/financier-names.csv` | entity = the financier | the financier brief (§4) |

## 3. Method — an Agent brief, not a query

`SWEEP-REGIONAL.md` §3 unchanged: **Exa Agent** (`agent_run`, `effort: "medium"`), one brief per item, exclusions stated in the brief and enforced at staging. Hand the Agent §4's Intent with `{financier}` filled in **using the canonical name**; the window (§6), stated explicitly **as applying to the publication date** (§6a); §4's report fields; and a standing instruction to **prefer primary and official sources** — the financier's own newsroom, board papers, country strategies, evaluation and audit units, and the recipient's own announcements.

### 3a. The Agent returns leads, never bodies — fetch every one

`SWEEP-REGIONAL.md` §3a in full: **nothing the Agent writes is ever staged**; every candidate is fetched and reaches `new/` as **the source's own full verbatim body** (`wiki/capture-rule.md`); **never trust the Agent's dates**; the three habitually wrong fields. Staging shape: flat to `new/YYYY-MM-DD-slug.md`, best-effort frontmatter, `sweep_batch: financiers-YYYY-MM-DD`. This sweep carries *two* dates and the Agent will hand back both: §6a.

### 3b. What the sweep does *not* build

**This sweep stages sources. It does not build deal records.** Every candidate, however unmistakable the deal, is staged as an **ordinary candidate source**; the finance record is built at ingest by `wiki/finance-news-driver.md` in capture mode (`INGEST.md` step 2a), against `wiki/finance-record-spec.md`. A sweep may write only `new/` and its own `sweep/` folder (`intake.md` §7).

**The report fields are a head-start, not a record.** Carry what the Agent returned and what the fetched page states into a `## Sweep note` section on the staged candidate — place, topic, recipient organisation, the pledge/commitment/disbursement figure in the announcing party's own currency, and the date of the deal. Ingest verifies it against the body; it is not evidence and nothing downstream may cite it.

### 3c. There is no amount gate at staging

**A financier item without a figure is fully in scope.** The five-fact test is **ingest's routing rule, not this sweep's admission rule** (`finance-record-spec.md` → *Failing the test is a routing decision, not a rejection*). Stage it; the driver decides whether it becomes a record.

## 4. The search — one brief per financier

*Topic head-starts are guidance for the staged frontmatter, finalised at ingest — write real Level-2 slugs (`taxonomy.md`), never a `*` wildcard, and put the dominant subject first (`topics:` order is load-bearing; `primary_subject` follows it).*

### Financier brief — scoped to `{financier}`

- **Intent:** Every development **published within the window** relating to `{financier}`'s actual, proposed, planned or possible **financial investments in Africa**, that falls **within the wiki's scope — data governance and digital transformation**.
- **Two bounds the brief must state explicitly: bound to Africa, and bound to our subject** — connectivity and data infrastructure, data governance and protection, digital public infrastructure and digital ID/payments, digital government and services, digital skills and the digital economy. Health, agriculture, energy, transport and trade-in-goods financing is **not** our subject even when the financier calls it a digital programme.
- **Seek:**
  - new commitments, approvals, signatures, guarantees, MoUs and disbursements;
  - **the pipeline** — proposed, planned or possible investments, calls for proposals, country strategies and programme frameworks;
  - **future intentions, including negative ones** — a cut, a pause, a wind-down, a withdrawal, a change of priority or of instrument;
  - **the financier's own reviews of what it has already funded** — evaluations, audits, completion and results reports, portfolio reviews;
  - **third-party critique and citizen feedback** — civil-society analysis, academic assessment, parliamentary or audit-office scrutiny, recipient-side complaint about conditions, procurement or outcomes.
- **Report per item:** URL; title; publisher; **publication date**; **place** (recipient country or region); **topic**; **recipient organisation** where named; **the pledge, commitment or disbursement** with figure and currency as the source states them, or explicitly *none stated*; **the date of the deal** where reported; and one line on why it matters.
- **Topic head-start:** entity = the financier, plus the recipient where named; place = the recipient ISO-3, or the region code where genuinely regional, and **`XAF` only where the item really is Africa-wide** — a global announcement mentioning Africa in passing is out of scope. A `finance.*` slug first (`finance.new` for a commitment, `finance.mou` for an MoU or framework; never `finance.budget`, which is domestic-state); `gov.*` first where the item is a strategy, policy or critique carrying no money.

## 5. Boundaries — the firewall (`intake.md` §7)

`SWEEP-REGIONAL.md` §5 applies whole — the origin screen [`wiki/origin-screen.md`](wiki/origin-screen.md) run on every candidate, URL dedup against `logs/sweep-url_log.md`, `new/` and the `raw/` index, conceptual overlap left to ingest. Two things differ:

- **The drop log is `sweep/financiers/drop-log-YYYY-MM-DD.csv`**, with the financier as a column. Nothing discarded silently.
- **Scope drops both what is not our subject (`off-topic`) and what is not about Africa.** The brief's two bounds (§4) leak; the drop filter is what holds. Every drop takes a code from `intake.md` §7 — that table is closed; never invent one.

**A low admit rate is not a fault.** If the `new/` load makes ingest the night's bottleneck, the lever is the **brief's bounds** or the **cadence** (§9), never a judgement call at staging.

## 6. Window — supplied by the caller

`SWEEP-REGIONAL.md` §6: **no state of its own**. In the cycle, `window_start = the day's Start date − 1 day`, `window_end = today`, and a failed run re-runs the **same** window; standalone, `since <date>`, defaulting to **one rotation**. Note the wall-clock start time for §8's line; nothing is written back.

### 6a. The window screens the *report*, not the *deal* — and both dates are kept

**The window applies to the publication date.** A report published inside the window about a commitment signed years earlier **is in scope**; a report published before the window about a deal signed yesterday is not — what this sweep watches is **the financier disclosing something**.

- **The publication date** screens; it is established **from the fetched page**, never from the Agent's report, and is the staged candidate's **`published:`**. Never back-date a staged candidate to its deal year: the filename prefix orders `new/`.
- **The date of the deal** is the event date, goes in the `## Sweep note` (§3b), and becomes the finance record's `published` at ingest if a record is built (`finance-record-spec.md` → *Dates*).

**Not a licence to admit old news** — `CLAUDE.md` → *Currency*: an older source arriving late is a **baseline, not news**, and a re-report of a held deal is a duplicate settled at ingest. The rule admits a **newly published** document about older money.

## 7. Delegation — batches of ~8–10 financiers

`SWEEP-REGIONAL.md` §7 applies — the parent owns list-loading and every spawn, **no sub-agent spawns another**, and each returns **only a terse tally**. Here the parent passes literal `slug, Canonical Name` rows; batches are **~8–10 financiers, one sub-agent each**, labelled **`financiers 1/N`** … **`financiers N/N`**. The five lines every spawn carries are `SWEEP-CYCLE.md` → *What every sub-agent prompt carries*.

## 8. Finishing

`SWEEP-REGIONAL.md` §8: **stage-only, never `update wiki`**; one terse line to `logs/log.md` from the sweep, not each sub-agent; post-run notes numbered; end on the standing status line (`CLAUDE.md` → *Reporting*, `STATUS.md`). The log line here is:

`YYYY-MM-DD hh:mm — financiers sweep, window <start>→<end>, took <Nm>; N financiers, staged N, dropped N (off-topic N, non-Africa N, origin N, dup N).`

Two things are recorded when this sweep meets them: **a financier returning nil twice running**, and **a slug that failed to resolve** (§1). Both are row health and go to `sweep/row-health.csv` — `nil-in-window` for the first, `unreachable` for the second — and are named on the sweep's own log line. **Neither is a post-run note**: that file takes `[CRITICAL]` alone (`CLAUDE.md` → *Reporting*), and a repeat nil is neither irreversible nor already public.

## 9. Cadence

- **Cost:** **rows in `sweep-financiers.csv` × 1 brief** `agent_run` calls, at `medium`. Take the formula, not a figure.
- **Cadence is settled on §8's line.** Watch the **drop ratio**: scope drops dominating means tighter brief bounds (§4), not a cadence change.
- The rotation row is in `logs/sweep-cycle_log.md`; moving or renaming the day is a log edit, not an edit to this file.
