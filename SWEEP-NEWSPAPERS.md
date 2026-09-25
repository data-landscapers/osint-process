<!-- reader: cc; type: runbook -->
# Sweep — newspapers (procedure)

**Content-scoped, not time-scoped** (unlike the daily sweep): works the newspaper sources listed in `lookups/sweep-newspapers.csv` and picks up what those sources have published since it last ran. Run by `SWEEP-CYCLE.md` on **Day 1** of the nightly rotation; also runnable standalone from Claude Code on demand.

One of three content sweeps — newspapers, journals, thinktanks — on shared machinery; the target list, state folder and one per-target rule are what differ.

## Target

| Trigger | List (`lookups/`) | State (`sweep/`) | Columns | Seek |
|---|---|---|---|---|
| **"run the newspapers sweep"** | `sweep-newspapers.csv` | `sweep/newspapers/` | `URL, iso-3, Title` | new stories (place = the row's `iso-3`) |

**Column 1 (the URL) is the only field the sweep needs** — always the source's URL/domain, whatever the header says (the CSV carries a BOM and mixed header case; ignore it and take column 1). Everything else is an **optional head-start** for the staged frontmatter, validated at ingest: `Title` → `publisher`, and `iso-3` → `place`.

**Row health.** Record every non-clean row outcome in `sweep/row-health.csv` and mark a row that fails **twice consecutively**, or is `dormant`, `reported` there: the ledger is the report, and it is never copied into `reviews/post-run-notes.md` — `intake.md` §7 → *Row health*. Never edit the sweep source lists in `lookups/` — they are Bill's (`layout.md` §2).

## Search priorities

This search should make the assumption that the technical trade journals will cover basic news on infrastructure and systems. What we are looking for here is political nuance, governance issues, statements (official or non-official) about infrastructure and system developments.

## Boundaries — same firewall as the daily sweep

- **Acquisition, not briefing.** Output is candidate source files in `new/`; it never writes to `raw/` or any `wiki/` page. Ingest is the only door to `raw/`.
- **The list is its whole world.** This sweep touches **only the domains in `sweep-newspapers.csv`**. Domain-scope every Exa query to the row's domain — this is also the admissibility firewall against content-mirrors and AI-synthesis blogs. Never run an un-scoped "latest Africa news" query.
- **Origin screen — run `wiki/origin-screen.md`** anyway: a listed source can syndicate or republish, and a row can be added to a CSV faster than its origin is adjudicated. **Log any `inadmissible-origin` drop to `sweep/newspapers/drop-log-YYYY-MM-DD.csv`** — nothing is discarded silently (`intake.md` §7).
- **Disjoint from the other sweeps.** The universal sweep of everything off the lists is **`SWEEP-DAILY-OFFLIST.md`**; the domain daily list is **`SWEEP-DAILY-LIST.md`**; journals and thinktanks have their own sweeps. No double-searching.

## Window — supplied by the caller

This sweep holds **no state of its own**. Its window is **passed in**:

- **In the cycle** (`SWEEP-CYCLE.md`) the cycle computes the window from the rotating day's `Start` in `logs/sweep-cycle_log.md` — `window_start = Start's date − 1 day` (the one-day overlap stops boundary items slipping through), `window_end = today` — and hands it to this sweep. `Start` is not advanced until the day *closes*, so a failed run re-runs the **same** window, not a short one.
- **Standalone**, supply the window yourself (`since <date>`, defaulting to **one rotation** — the interval this sweep runs at in the cycle, not a fixed number of days).

Note the wall-clock start time (for the duration line below), then sweep the window under *The loop*. There is nothing to write back — advancing the rotation is the cycle's job at close.

## Delegation — one sub-agent per batch, and the parent spawns it

Run *The loop* below over **the rows this agent was handed** — a slice of ~8–10 sources. Do **not** fetch the whole list in one context: a fetched body stays in context after it is staged, and the whole list would overflow. Each batch runs the search + `web_fetch_exa` for its domains, stages hits into `new/`, and returns only a **tally** (sources done, items staged, failures); the bodies die with it. **Bake [`wiki/capture-rule.md`](wiki/capture-rule.md) into every batch sub-agent's instructions** — unattended agents refuse verbatim capture without it, and it carries the *never read a feed whole* rule that keeps a batch agent alive.

**The batching is the caller's, not this file's.** Under `SWEEP-CYCLE.md` the cycle parent reads the CSV's row count, spawns one sub-agent per batch and hands each its row range; **no sub-agent spawns another** (`SWEEP-CYCLE.md` → *Why the parent owns the spawn*). Run standalone, the session itself is the parent and batches the same way.

## The loop

Read `sweep-newspapers.csv` fresh (it changes). For each row:

- **Domain-scope an Exa query** to the row's URL/domain for items published within `[window_start, window_end]`, **in the outlet's own language** — infer it from the row's `iso-3` (e.g. SEN/CIV → French, MOZ/AGO → Portuguese, EGY/DZA → Arabic) and query that language; an English-only query returns little or nothing from a Francophone, Lusophone or Arabophone paper. Prefer `web_search_exa` scoped to the domain; fetch bodies with `web_fetch_exa`.
- **Stage each hit flat into `new/`** as `new/YYYY-MM-DD-slug.md` (publication-date prefix), full verbatim body, best-effort frontmatter: `publisher` = the row's Title; `sweep_batch: newspapers-YYYY-MM-DD` (this run's date); `place` from the row's `iso-3` — **but the `iso-3` is the *publisher's* country, not necessarily the story's** (a Nigerian paper reporting on Kenya still carries `iso-3` NGA); ingest validates and fixes it. Staged frontmatter is a head-start, validated at ingest — never a substitute for it.
- **Filter against `logs/sweep-url_log.md` before fetching.** Normalise the hit's URL (`vault_lib.normalise_url()`, `INGEST.md` step 2) and `grep -F` it; a hit means the base has already adjudicated it — admitted or rejected — so skip it and fetch nothing.
- **And cross-check `new/`, on the same normalised URL.** The nightly daily and off-list sweeps stage into `new/` before this one runs, and their URLs do not reach `sweep-url_log.md` until the cycle's closing `INGEST` Phase A pass; without this check the night's earlier catch is re-fetched.
- **And the `raw/` index, in the same pass** — `python scripts/raw-url-index.py --check -`, the run's URLs one per line on stdin. `sweep-url_log.md` reaches back one rotation; the index reaches back for ever. `DUP-EXACT` and `DUP-SLUG` (same host, same final path segment, new path) both skip; **`FLAG-SLUG` — *different* host, same slug — never does**, that being one story two outlets ran. Read-only here: ingest alone writes it (`SWEEP-DAILY-LIST.md` §3).
- **Everything past that filter is ingest's job.** Keep no seen-ledger here; the one-day overlap may re-surface a boundary item, and ingest's dedup (event + entities + date) drops it.

## Finishing

1. **Stage-only — this sweep never runs ingest itself.** It ends with its candidates sitting in `new/`, and the **caller** drains them: in the sweep cycle, `SWEEP-CYCLE.md`'s own `INGEST` Phase A pass after the day's sweeps; run standalone, `update wiki`. The sweep itself files nothing to `raw/`.
2. **Log one terse line** to `logs/log.md` — the **duration** and window, not what was captured or dropped (`raw/` and `logs/sweep-url_log.md` are that record):

   `newspapers sweep — window <start>→<end>, took <Nm>, staged <N>.`

## Concurrency

One sweep at a time, and no other CC session writing to the vault while it runs (it stages into the shared `new/`, and the caller's hand-off runs ingest).
