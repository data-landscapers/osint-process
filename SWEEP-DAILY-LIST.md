# SWEEP-DAILY-LIST.md — the daily on-list sweep

Trigger: **"run the daily sweep"**. Sweeps the domains in `lookups/sweep-daily.csv` for what they published since the last run and stages candidates into `new/`.

Runs standalone, or first in `SWEEP-CYCLE.md`. Per-domain findings: `sweep/domains/{domain}.md`; dated run record: `sweep/daily/history.md`. Neither is needed to work a run.

---

## Boundaries

- **Acquisition, not briefing.** Output is candidate files in `new/`. Never write to `raw/` or any `wiki/` page — ingest is the only door to `raw/` (`intake.md` §7).
- **The list is the whole world.** Touch only the domains in `lookups/sweep-daily.csv`, the single source of truth for the list. Everything off it belongs to `SWEEP-DAILY-OFFLIST.md`. No double-searching.

## Before you start

1. **Read `lookups/sweep-daily.csv` fresh.** It changes. Columns: `url,title,notes_file`.
2. **Read `wiki/capture-rule.md`** and bake it into any sub-agent that fetches.
3. **Do not read `sweep/domains/{domain}.md` up front.** Open one only when that domain misbehaves.
4. **Recover state** from `sweep/daily/`:
   - `state.json` — `{ last_run_completed_utc, last_run_staged, last_run_window }`.
   - `seen.csv` — `url,published,retrieved,title`. **Append, never overwrite.** Prune rows older than 60 days at the end of the run.
   - First run: initialise both, empty ledger.

## Compute the window

```
window_end   = now (UTC)
window_start = min( last_run_completed_utc , now − 24h )      # 24h overlap floor
if (window_end − window_start) > 10 days:  window_start = now − 10 days
first run (no state.json): window_start = now − 24h
```

**Apply the drop test by date, not by hour.** An item is dropped only if its publication *date* precedes `window_start`'s date. A story published on the morning of the start day is IN.

**Two things make a window look empty, and neither is chased:** **index lag** (the newest ~48h is under-indexed by Exa; the 24h overlap absorbs it) and **the weekend** (weekday publishers). Record the nil; never ask a nil domain to prove which kind of nil it is.

## Delegation

**Batches of ~8–10 domains, one sub-agent each**, each returning the one-line tally specified in `SWEEP-CYCLE.md`. Bodies die with the batch.

**The batching is the caller's.** The `SWEEP-CYCLE.md` parent spawns one sub-agent per batch with its row range; **no sub-agent spawns another** (`SWEEP-CYCLE.md` → *Why the parent owns the spawn*). Standalone and watched, inline in the main session is fine.

---

## Procedure

### 1. Search

For each domain, run **one** query cluster — **D1**, or **D2** where the domain's file says its beat is infrastructure and economy rather than DPI and governance — as a domain-scoped `web_search_exa`, date-bounded to the window, `numResults` **10**. No month-slicing.

**FR and AR variants only where that domain has produced a non-English admitted source**, recorded in `sweep/domains/{domain}.md`.

### 2. Fetch the domain's own listing

**One instrument per domain.** The listing is the instrument: fetch it once, take what it holds, move on. **A nil from one listing is a nil** — recorded without a second instrument to confirm it; a miss self-corrects on the next run's overlap window.

Everything site-specific — live paths, dead paths, which tree holds what — is in `sweep/domains/{domain}.md`.

**Rule 0 — try the publisher's feed first, fetched locally, and never read it whole.** Most domains serve an RSS feed that `curl` / `Invoke-WebRequest` reads where Exa rejects it (`CRAWL_UNEXPECTED_CONTENT_TYPE`), with exact URLs and `pubDate`s; several carry the whole body (`content:encoded` or `description`). A feed read whole overflows the agent, so:

- **Parse in the shell, return only fields:** `[xml]$x = (Invoke-WebRequest $u).Content; $x.rss.channel.item | select title, link, pubDate`.
- **Where the feed carries the full body, write it straight to the staged file from the shell** — never through context.
- WordPress feeds page with `?paged=N`; keep paging until a page returns nothing in-window.

Some feeds are excerpt-only or carry the press office, not the news beat: Rule 0 goes *in front of* the rules below, not instead of them.

**Rule 1 — the search hits are a union with the listing, not a cross-check of it.** Take what both return, dedup, and go.

**Rule 2 — cache-bust only where the domain's file says that domain needs it.**

**Rule 3 — take every date from the article body.** Never from a listing or a page header; drift runs both ways.

**Rule 4 — where a domain's file records that its listing omits the beat, search is that domain's instrument instead.** One instrument either way; which one is the domain's property, not a judgement made per run.

### 3. Dedup — conservative

Drop a hit only if it is **(a)** an exact URL already in `seen.csv`, in the `raw/` index, or in a current `new/` candidate, or **(b)** confidently the same outlet's re-crawl of a story already held.

**The `raw/` leg is one lookup, never a corpus scan** — `python scripts/raw-url-index.py --check -`, the run's URLs one per line on stdin. `DUP-EXACT` is (a). `DUP-SLUG` (same host, same final path segment, new path) **is (b)**: drop, reason `duplicate-raw-slug`, matched file as `kept_twin`. **`FLAG-SLUG` — *different* host, same slug — is never a drop**: stage it noting the twin, for lint #7. The sweep reads the index and never writes it; ingest alone does that.

Everything else survives — *same event, different outlet* and *same story, later date* both go through to ingest's lint #7. Dedup within the run too. **Log every drop** to `sweep/daily/drop-log-YYYY-MM-DD.csv` (`url,title,published,reason,kept_twin`). Nothing is dropped silently.

### 4. Fetch, verify, classify

For each survivor:

- **Establish `published` from the page** — dateline/body, or a `/YYYY/MM/DD/` URL path. **Never trust the search result's date**, `agent_run` output included. Watch for header clocks rendering *today*. Fall back (ingested → created) only if genuinely undated, with `date_source: proxy` and honest `date_precision`.
- **Drop out-of-window** items; log as `out-of-window`.
- **Run `wiki/origin-screen.md`** on every survivor first. It owns `logs/drop-list.csv`, the hostile shapes, the `watch → drop` promotion, the mining rule and `inadmissible-origin`. **Screen an unknown origin in the run — never drop it as a precaution.**
- **Admissibility.** Skip second-hand and AI syntheses. Prefer a canonical URL over a syndicated copy, except where a domain's file records an aggregator carve-out. **Newsletter and digest editions are dropped outright, never lead-mined.**
- **Classify** against `lookups/taxonomy.md`, `lookups/countries.csv` and known entities. Best-effort — ingest validates.
- **Capture the body per `wiki/capture-rule.md`.** Full verbatim text, never a snippet or a summary. **A truncated capture is flagged, not retried** — set `body_completeness: excerpt`, one line in the drop log, move on; lint #15 and the duplicate tiebreak read the flag.

### 5. Stage

Write each survivor to `new/YYYY-MM-DD-slug.md` — publication-date prefix, flat, no subfolders — with the frontmatter below and the full body.

### 6. Manifest and state — the last act

Write `sweep/daily/manifest-YYYY-MM-DD.md`, one line per staged item (`published | topics | places | source | title | why-new`). Append staged items to `seen.csv`; prune rows >60 days. **Last**, set `state.json.last_run_completed_utc = window_end`, so an interrupted run leaves the mark un-advanced and re-running resumes cleanly.

### 7. Hand off

Run **`update wiki`** (`UPDATE-WIKI.md`) — it drains `new/` through ingest and works any contradictions or acquisitions that surface. It does **not** lint.

**In `SWEEP-CYCLE.md` this step is skipped**: the sweep is stage-only and the cycle runs `INGEST`'s Phase A once after the daily sweeps. Skip it standalone only when deliberately staging without processing.

---

## Candidate frontmatter (the ingest contract)

```yaml
---
type: source
title: ...
url: https://...
publisher: ...                 # the row's title from sweep-daily.csv
published: 2026-07-18
date_precision: day            # day | month | year
date_source: source            # source | proxy
places: [KEN]                  # countries.csv; [] if genuinely none
topics: [dpi.pay, finance.new] # taxonomy.md slugs, dominant subject FIRST
entities: [[m-pesa]]           # best-effort
retrieved: 2026-07-19
sweep_batch: daily-2026-07-19
body_completeness: full        # full | excerpt | paywalled — see wiki/capture-rule.md
---
```

Never set `ingested:` — that belongs to ingest. Body = the full verbatim article text.

## Query clusters

Two broad angles per domain; this sweep loops *sources*, not countries. Keep these fixed so runs stay comparable; date any change in `sweep/daily/history.md`.

**D1 — DPI & governance**

- EN: *digital public infrastructure, digital ID, e-government, data protection, data governance, digital payments or mobile money news in Africa*
- FR: *identité numérique, infrastructure publique numérique, administration électronique, protection des données, paiement mobile en Afrique*

**D2 — Infrastructure & economy**

- EN: *telecom, connectivity, subsea cable, data centre, cloud, fintech, AI or cybersecurity news in Africa*
- FR: *télécom, connectivité, câble sous-marin, centre de données, cloud, fintech, intelligence artificielle en Afrique*

(AR variants for North-African stories: translate the same phrasings.)

## Failure modes

| Symptom | Response |
|---|---|
| **529** | Anthropic overloaded — back off and retry; drop concurrency if they cluster |
| **401 "run /login"** | Local auth expiry, unrelated to the sweep |
| **Repeated fetch failures on one domain** | Try a local fetch; then flag those items for manual clip and carry on |
| **Run dies** | Costs nothing — `state.json` advances only as the final act |

## Ending the run

The standing tally line per `STATUS.md`:

```
contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN
```

plus one sweep line: `daily sweep: staged N · dropped N · needs-clip N · window <start>→<end>`.

**Report absence honestly.** A nil day and an unworked day are indistinguishable unless the evidence is real: never relay an unverified figure — a sub-agent's, or your own before its result is in hand.
