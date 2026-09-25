<!-- reader: cc; type: runbook -->
# Sweep — regional (procedure)

**Institution- and region-scoped deep research, in two loops.** The **first loop** walks the **regional institutions** in `lookups/sweep-regional-orgs.csv` (maintained by Bill); the **second loop** walks the **regions** — the X-region rows of `lookups/countries.csv`, **with XSS "Sub-Saharan Africa" and XAF "Africa" conflated into a single entry**.

Run by `SWEEP-CYCLE.md` on its rotating day; also runnable standalone ("**run the regional sweep**"). `logs/sweep-cycle_log.md` holds which day it runs on; this file names no day of its own.

## 0. One-line purpose and the overlap it accepts

Deep research on the **regional layer**. This sweep **expects to re-surface material the cycle has already seen**; **the duplicate load lands on ingest, and ingest is where it is settled** (`CLAUDE.md` → *Duplicates*).

**This sweep makes no value judgement at staging** — ingest owns that decision. **Stage what the briefs surface, in scope (§5), and let ingest sort it out.**

## 1. Shape — two loops

**Two independent loops, run one after the other; each iterates its own list and runs one Agent brief (§4) per item.** Lists are loaded by the parent (§7).

- **Loop 1 — regional institutions.** `lookups/sweep-regional-orgs.csv` (columns name, abbrev, category). Per institution, run **the institution brief** (§4A) — `{institution}` fills the brief.
- **Loop 2 — regions.** The `lookups/countries.csv` X-region rows naming a **region of Africa**: XCA, XEA, XNA, XSA, XWA, plus the **XAF/XSS pair conflated into one entry**. **XGL "Global/Developing Countries" is excluded.** Per region, run **the region brief** (§4B) — `{region}` fills the brief.
- **Output:** candidate source files in `new/` only. Never `raw/`, never a `wiki/` page — ingest is the only door (§5).

## 2. Target

| Loop | Drives the loop | Per-item scope | Seek |
|---|---|---|---|
| **Loop 1 — institutions** | `lookups/sweep-regional-orgs.csv` | entity = the institution | the institution brief (§4A) |
| **Loop 2 — regions** | `countries.csv` X-region rows (XGL excluded; XAF+XSS conflated) | place = the region code | the region brief (§4B) |

## 3. Method — an Agent brief, not a query

Each search is run with the **Exa Agent** (`agent_run`, `effort: "medium"`), which composes its own searches from a **natural-language objective** — so §4 defines a *brief*, not a query string. For every loop item, hand the Agent:

- the **objective** — the brief's Intent, with `{institution}` or `{region}` filled in **using the item's name**, not a code ("West Africa"; "Africa / Sub-Saharan Africa" for the conflated XAF/XSS entry);
- the **window** — passed in by the caller (§6), stated explicitly;
- **what to report per item** — URL, title, publisher, date, and one line on why it matters;
- a standing instruction to **prefer primary and official sources**.

**Exclusions are stated in the brief, then enforced at staging** — `agent_run` has no hard domain-exclude list. Never claim an exclusion is enforced at search time.

### 3a. The Agent returns leads, never bodies — fetch every one

**Nothing the Agent writes is ever staged.** `agent_run` output is a synthesis (`CLAUDE.md` → *The material*). The Agent's job is **discovery only**; each candidate goes through `SWEEP-DAILY-OFFLIST.md`'s **fetch → verify → classify → stage** machinery, and what reaches `new/` is **the source's own full verbatim body** under `wiki/capture-rule.md`. A staged file whose body is the Agent's summary is a defect.

**Never trust the Agent's dates** (`SWEEP-DAILY-LIST.md` step 4). **Establish `published` from the fetched page**, with the fallback chain and `date_source: proxy` (`layout.md` §3) when the page will not yield one.

**Frontmatter and staging shape are the daily sweep's**: flat to `new/YYYY-MM-DD-slug.md`, best-effort frontmatter, `sweep_batch: regional-YYYY-MM-DD`. **Two fields this sweep gets wrong often enough to state here** — `entities:` (slugs, never display names, in one outer list: `[[sadc], [south-african-reserve-bank]]`; lint #12) and `places:` (`countries.csv` codes only; a non-African country merely mentioned is not a place). Vocabularies: `facets.md` §1. When a slug is not obvious, tag fewer.

## 4. The searches — one per loop

*Topic head-starts are guidance for the staged frontmatter, finalised at ingest — write real Level-2 slugs (`taxonomy.md`), never a `*` wildcard, and put the dominant subject first (`topics:` order is load-bearing; `primary_subject` follows it).*

### 4A. Institution brief (Loop 1) — scoped to `{institution}`

- **Intent:** Every development within the window, by or about `{institution}`, that falls **within the wiki's scope — data governance and digital transformation**. Their health, agriculture, energy, transport and trade-in-goods work is **not** our subject and is not wanted. Excludes the daily-list domains.
- **Seek:** Organisational matters and individuals; policies, plans and programmes; relationships with other organisations; third-party critique of the institution's activities; financing.
- **Topic head-start:** entity = the institution; place = `XAF` unless the item is specific to one country or sub-region, then that ISO-3 or X-region code. A `gov.*` slug first for instruments and institutional matters (`gov.regional`, `gov.policy`, `gov.legislate`, `gov.standards`); a `finance.*` slug first where the item is a financing development.

### 4B. Region brief (Loop 2) — scoped to `{region}`

- **Intent:** Every development within the window in `{region}` that falls **within the wiki's scope — data governance and digital transformation** *and* is of relevance to the whole region or at least three of its countries. Bilateral issues do not belong here. Excludes the daily-list domains.
- **Seek:** Regional infrastructure initiatives (connectivity and storage); efforts to harmonise governance instruments; details of meetings or committees/working groups aimed at increasing coordination and collaboration; evidence and critique on the lack of harmonisation; key individuals driving regional integration; sovereignty/localisation issues; cross-border data transfers.
- **Topic head-start:** place = the region code. `gov.regional` first for harmonisation, coordination and cross-border items; `infra.connect` / `infra.store` first for infrastructure; `gov.protect` for localisation and sovereignty.

## 5. Boundaries — the firewall (`intake.md` §7)

**Two mechanical filters and a scope filter.** Everything past them is ingest's.

- **Acquisition, not briefing.** Output is candidate files in `new/`; ingest adjudicates.
- **Origin screen — run `wiki/origin-screen.md`** on every candidate; log any `inadmissible-origin` drop to `sweep/regional/drop-log-YYYY-MM-DD.csv` (loop and item as columns). Nothing discarded silently.
- **Scope — drop what is not our subject**, as `off-topic`. This is the one judgement the sweep makes: the subject is a sweep's call; whether the wiki already has it is ingest's alone. Every drop is logged with a code from `intake.md` §7 — that table is closed; never invent one.
- **Dedup against `logs/sweep-url_log.md`** before fetching — a `grep -F` on a normalised URL, before any body is pulled. **Also cross-check `new/`**: its URLs reach `sweep-url_log.md` only at ingest.
- **And the `raw/` index, in the same pass** — `python scripts/raw-url-index.py --check -`, the run's URLs one per line on stdin; read-only here, ingest alone writes it (`SWEEP-DAILY-LIST.md` §3). `DUP-EXACT` and `DUP-SLUG` (same host, same final path segment) both skip; **`FLAG-SLUG` — *different* host, same slug — never does**.
- **Conceptual overlap on a different URL is not filtered here** — that is ingest's dedup and it needs the body.

**A lower admit rate than the other sweeps is not a fault.** If `new/` load makes ingest the night's bottleneck, the lever is the **briefs' framing** or the **cadence** (§9), never a judgement call at staging.

## 6. Window — supplied by the caller

This sweep holds **no state of its own**. Its window is **passed in**:

- **In the cycle** (`SWEEP-CYCLE.md`): from the rotating day's `Start` in `logs/sweep-cycle_log.md`, `window_start = Start's date − 1 day`, `window_end = today`. `Start` is not advanced until the day *closes*, so a failed run re-runs the **same** window.
- **Standalone**, supply the window yourself (`since <date>`, defaulting to **one rotation** — the cycle interval).

Note the wall-clock start time (for §8's duration line). Nothing is written back — advancing the rotation is the cycle's job at close.

## 7. Delegation — one sub-agent per loop (split Loop 1 only if its list is long)

- Do **not** hold everything in one context.
- **The parent owns list-loading and every spawn; no sub-agent spawns another** (`SWEEP-CYCLE.md` → *Why the parent owns the spawn*). Under `SWEEP-CYCLE.md` that is the cycle parent. It parses the institution list via `bash` on the mount path, inlines the six region entries, and passes each sub-agent only its slice as literal rows in the spawn prompt. **Loop sub-agents never open the repo lists.**
- **Each loop is its own sub-agent**; if Loop 1's fetched bodies would overflow one context, split it into batches of ~8–10 institutions, one sub-agent each — the regions loop (6 entries) is always a single sub-agent. Each runs one brief per item it was handed, screens + stages to `new/`, and returns **only a terse tally** — staged / dropped counts and drop-reasons per brief, not the bodies.
- **Label each sub-agent** — **`regional inst`** and **`regional regions`**, or **`regional inst 2/3 A–M`** when the institution list is batched.

## 8. Finishing

1. **Stage-only — this sweep never runs `update wiki`.** The **caller** drains `new/` — in the cycle, `SWEEP-CYCLE.md`'s own `update wiki`; standalone, the next drain.
2. **The sweep — not each sub-agent — writes one terse line** to `logs/log.md` on close, aggregating the tallies — the run, not the catch. **One line for the whole sweep, both loops folded in**, never one per loop:

   `YYYY-MM-DD hh:mm — regional sweep, window <start>→<end>, took <Nm>; staged inst/region = N/N, dropped N.`

3. **A row yielding nil across its briefs twice running, or an Agent error** → `sweep/row-health.csv`, and named on the sweep's own log line. **Not `reviews/post-run-notes.md`**: that file takes `[CRITICAL]` alone (`CLAUDE.md` → *Reporting*) and row health is explicitly not a note.
4. **End on the standing status line** (`CLAUDE.md` → *Reporting*, counts defined in `STATUS.md`):

   `contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

## 9. Cadence

- **Cost:** **(rows in `sweep-regional-orgs.csv` + 6 region entries) × 1 brief** `agent_run` calls, at `medium`. Take the formula, not a figure.
- **Cadence is settled on §8's log line.**
- The rotation row is in `logs/sweep-cycle_log.md`; moving or renaming this day is a log edit, not an edit to this file.
