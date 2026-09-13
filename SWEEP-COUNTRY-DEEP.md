# Sweep — country deep (procedure)

**Per-country deep research.** Four Exa Agent briefs per country — non-state finance, governance, data exchange, demand/political economy — for the *institutional and analytical* depth the news sweeps skim past. The one sweep that deliberately overlaps the others; the overlap is managed at staging, not avoided (§0, §5).

Run by `SWEEP-CYCLE.md` on its rotating day; standalone trigger "**run the country deep sweep**". It holds a day of the rotation in `logs/sweep-cycle_log.md`, which is what the cycle reads; nothing in `SWEEP-CYCLE.md` names it, so moving its day is a log edit, never an orchestrator edit.

## 0. Purpose and the overlap it accepts

This sweep **expects to re-surface material the cycle has already seen** — a deep topic search reaches the analysis behind an event, not just the event. **The duplicate load lands on ingest, which settles it** (drop / replace / keep-both, `CLAUDE.md` → *Duplicates*) with the full text in hand.

**No value judgement at staging.** Ingest is the only door and owns the "does this add over what the wiki holds" decision. Stage what the briefs surface.

**Scope is not value, and off-topic is dropped here.** `CLAUDE.md` → *The material* governs, and rejects when in doubt; what is simply not our subject is dropped as `off-topic` (code from `intake.md` §7), not carried to ingest.

## 1. Shape

- **Outer loop:** the 54 countries — ISO-3s from `lookups/countries.csv` **excluding X-prefixed region codes** (`facets.md` §1).
- **Inner:** for each country, the **four Agent briefs** in §4.
- **Output:** candidate files in `new/` only. Never `raw/`, never a `wiki/` page — ingest is the only door (§5).

## 2. Target

| Trigger | Drives the loop | Per-item scope | Seek |
|---|---|---|---|
| **`SWEEP-CYCLE.md`, or "run the country deep sweep"** | `countries.csv` (non-`X` rows) | place = the row's ISO-3 | the four briefs in §4 |

## 3. Method — an Agent brief, not a query

Each search runs on the **Exa Agent** (`agent_run`, `effort: "medium"`), which takes a natural-language objective and composes its own searches — so §4 defines a *brief*, not a query string. For every country, hand the Agent:

- the **objective** — the brief's Intent, with `{country}` filled in;
- the **window** (§6), as an explicit date range;
- **what to report per item** — URL, title, publisher, date, one line on why it matters;
- **prefer primary and official sources** over secondary syndication.

**Exclusions are stated in the brief, then enforced at staging.** `agent_run` has no hard domain-exclude list, so a brief's exclusions are guidance, not a filter; the firewall is the brief's framing, URL-dedup against `logs/sweep-url_log.md`, and ingest's dedup with the body in hand. Never claim the exclusion is enforced at search time.

### 3a. The Agent returns leads, never bodies — fetch every one

**Nothing the Agent writes is ever staged.** `agent_run` output is a synthesis (`CLAUDE.md` → *The material*). The Agent is **discovery only**; each candidate goes through the shared **fetch → verify → classify → stage** machinery as in `SWEEP-DAILY-OFFLIST.md`, and what reaches `new/` is **the source's own full verbatim body** under `wiki/capture-rule.md`. A body that is the Agent's summary is a defect, not a thin capture.

**Never trust the Agent's dates.** `SWEEP-DAILY-LIST.md` step 4 applies to `agent_run` output too: **establish `published` from the fetched page**, with the fallback chain and `date_source: proxy` (`layout.md` §3) when the page will not yield one. A wrong date smuggles an item in from outside the window.

**Frontmatter and staging shape are the daily sweep's**: flat to `new/YYYY-MM-DD-slug.md`, best-effort frontmatter, `sweep_batch: country-deep-YYYY-MM-DD`.

## 4. The four searches — each separately defined

*Each is one Agent brief, scoped to the current country. Topic head-starts are guidance for the staged frontmatter, finalised at ingest — real Level-2 slugs (`taxonomy.md`), never a `*` wildcard, dominant subject first (`topics:` order is load-bearing; `primary_subject` follows it).*

### Search 1 — Non-state finance
- **Intent:** Every discussion, MoU, commitment or actual deal financing any aspect of the wiki's scope in `{country}`. Excludes the financiers' own portfolio lists and portals, and the daily-list sources — both covered by other sweeps.
- **Seek:** Any item naming a financier or recipient; an intent to finance; deal or MoU detail; a change to an existing deal or MoU; third-party comment or critique on one.
- **Topic head-start:** place = ISO-3; a `finance.*` slug first (`finance.new` / `finance.mou`), plus the sector topic(s) financed.

### Search 2 — Governance (institutions and instruments, excluding data exchange)
- **Intent:** The institutions and individuals responsible for governing the wiki's scope in `{country}`, and progress on policies, strategies, plans, laws and regulations — **except** data-exchange governance, which is Search 3's.
- **Seek:** Any institution, committee or individual playing a pivotal role; any discussion, pre-planning or draft of a policy, strategy, plan, law or regulation.
- **Topic head-start:** place = ISO-3; the relevant `gov.*` slug(s) — `gov.policy`, `gov.legislate`, `gov.protect`, `gov.regional`.

### Search 3 — Data exchange (content, not transport)
- **Intent:** Data exchange as an *institutional* problem in `{country}` — interoperability, common standards and data models — **not** the transport layer. Search 2 owns the rest of governance, so the two do not double-stage the same strategy.
- **Seek:** Data-standards bodies and inter-departmental working groups and their activity; draft and established standards and models; strategies, policies, plans and roadmaps for cross-government data exchange; policies, laws and plans on cross-border data transfer.
- **Topic head-start:** place = ISO-3; `dpi.exchange` first, plus `gov.standards`, `gov.policy` and `gov.regional` for cross-border items.

### Search 4 — Demand and political economy
- **Intent:** The demand side of the wiki's scope in `{country}`: what problem DPI solves, whether it meets citizens' needs, whether citizens are included, whether public and private actors are accountable. **The noisiest brief and the lowest admit rate** — hold the seek tight. The origin screen does not catch the primary/secondary line, so lean on primary material (surveys, minutes, first-hand testimony) and named-analyst opinion (`gov.discourse`, first-class).
- **Seek:** Documented citizen experience of DPI; named-analyst critique of functionality, accessibility or performance; evidence of citizen engagement in planning or monitoring; opinion polls or surveys (primary preferred). First-hand accounts, not aggregator "human-interest" repackaging.
- **Topic head-start:** place = ISO-3; `gov.discourse` first, plus the relevant `include.*` slug (`include.access` / `include.divides`).

## 5. Boundaries — the firewall (`intake.md` §7)

**Two mechanical filters and a scope filter.** Everything past them is ingest's.

- **Acquisition, not briefing.** Candidate files in `new/`; ingest adjudicates.
- **Origin screen — run `wiki/origin-screen.md`** on every candidate; log any `inadmissible-origin` drop to `sweep/country-deep/drop-log-YYYY-MM-DD.csv` (country as a column). Nothing discarded silently.
- **Scope — drop what is not our subject** as `off-topic` (§0): the one judgement the sweep makes, and no licence to weigh an item against what the wiki holds. Every drop carries a code from `intake.md` §7 — a closed table; never invent one.
- **Dedup before fetching**: `grep -F` on the normalised URL against `logs/sweep-url_log.md`; **cross-check `new/`**, where the nightly sweeps stage before their URLs reach the log; and the **`raw/` index** leg exactly as `SWEEP-DAILY-LIST.md` §3 (`python scripts/raw-url-index.py --check -`; `DUP-EXACT` and `DUP-SLUG` skip, `FLAG-SLUG` never; read-only here).
- **Conceptual overlap on a different URL is not filtered here** — that is ingest's dedup and it needs the body.

**Expect more staged and less admitted than the other sweeps.** If `new/` load makes ingest the bottleneck, the lever is the briefs' framing or the cadence, never a judgement call smuggled back into staging.

## 6. Window — supplied by the caller

This sweep holds **no state of its own**:

- **In the cycle**, `SWEEP-CYCLE.md` computes it from the rotating day's `Start` in `logs/sweep-cycle_log.md`: `window_start = Start's date − 1 day` (one-day overlap), `window_end = today`. `Start` advances only when the day closes, so a failed run re-runs the **same** window.
- **Standalone**, supply it yourself (`since <date>`, defaulting to **one rotation** — the interval this sweep runs at in the cycle, not a fixed number of days).

Note the wall-clock start (for §8's duration), pass the window into every brief, sweep under §7. Nothing is written back; advancing the rotation is the cycle's job at close.

## 7. Delegation — batch into sub-agents, by country

- Never hold all 54 countries in one context (`SWEEP-NEWSPAPERS.md` → *Delegation*).
- **Batches of ~8–10 countries, one sub-agent each.** Each runs all four briefs for its countries, screens and stages to `new/`, and returns **only a terse tally** — per-search staged / dropped counts and drop-reasons, never the bodies.
- **The batching is the caller's.** The `SWEEP-CYCLE.md` parent takes the day's country set from the rotation table and spawns one sub-agent per batch; **no sub-agent spawns another** (`SWEEP-CYCLE.md` → *Why the parent owns the spawn*).
- Batch **by country, not by search**, so one country's four briefs are worked and screened together.
- **Label each sub-agent with the batch's position and range** — `country-deep 3/6 KEN-MWI` — never a generic "run sweep".

## 8. Finishing

1. **Stage-only — never runs `update wiki`.** The caller drains `new/`: in the cycle, `SWEEP-CYCLE.md` → *Ingest, once, at the close*; standalone, the next drain.
2. **The sweep — not each sub-agent — writes one terse line** to `logs/log.md` on close, aggregating the tallies — the run, not the catch:

   `YYYY-MM-DD hh:mm — country-deep sweep, window <start>→<end>, took <Nm>; staged fin/gov/exch/dem = N/N/N/N, dropped N.`

3. Anything irreversible or already public (`CLAUDE.md` → *Reporting*) → `reviews/post-run-notes.md`, numbered. A country nil across all four briefs twice running, or an Agent error, is a process-level decision line in `logs/log.md` — never an item-level admit/drop call, which stays off it.
4. **End on the standing status line** (`STATUS.md`):

   `contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`
