<!-- reader: cc; type: runbook -->
# SWEEP-CITATIONS.md — the daily citations sweep

Trigger: **"run the citations sweep"**. Finds pages and social-media posts published in the window that cite Data Landscapers — `data-landscapers.com`, `data-landscapers.io` and its `corpus.` subdomain, the `datalandscapers.io` spelling, or the organisation by name — and adds them to Bill's register `X:\citations.csv`, newest first. Runs every night in `SWEEP-CYCLE.md` after the off-list sweep, one Sonnet sub-agent, or standalone.

**It is a register, not a source pass.** Nothing goes to `new/`, `raw/` or the wiki; a citing page that is also in scope reaches the wiki only through the ordinary sweeps.

## Window and state

The daily sweep's: **36h look-back**, `window_start = min(last_run_completed_utc − 12h, now − 36h)`, 10-day cap, drop by date not hour (`SWEEP-DAILY-LIST.md` → *Compute the window*). State in `sweep/citations/state.json`, the parent's to write after the step returns; first run with no state takes `now − 36h`.

## Search — standard, not the Agent

`web_search_advanced_exa`, `startPublishedDate`/`endPublishedDate` set to the window, `numResults` 25, `textMaxCharacters` 3000, `excludeDomains` `data-landscapers.com`, `data-landscapers.io`, `datalandscapers.io`, one call per query:

1. `"Data Landscapers"` with `includeText: ["Data Landscapers"]`
2. `"datalandscapers.io"` with `includeText: ["datalandscapers"]`
3. `"data-landscapers.com"` or `"data-landscapers.io"`, one call each, with `includeText: ["data-landscapers"]`
4. `"post mentioning Data Landscapers"` with `includeText: ["Landscapers"]` and `includeDomains` `linkedin.com`, `x.com`, `twitter.com`, `bsky.app`, `facebook.com`, `threads.net`, `mastodon.social`

## Verify, then write

- **A hit is a citation only if the fetched text names or links Data Landscapers.** A search snippet is not evidence; fetch (`web_fetch_exa`) when the returned text does not show it. Data Landscapers' own pages and Bill's own posts are not citations.
- **Originals only.** A republished, syndicated or rewritten copy of another outlet's article is dropped; where the original is not already in the register, record the original instead.
- **Social media: new posts only.** Someone else's original post counts; a comment, repost or share (with or without added text) does not.
- `includeText` filters loosely, so expect most hits to fail this and drop them silently.
- **Date from the page**, as precise as it states: `YYYY-MM-DD`, or `YYYY-MM` when only the month is given; a search result's date is never trusted.
- **Author** is the byline; where none, the publishing organisation.
- Write the verified rows to `sweep/citations/new-<date>.csv` (`Date,Title,Author,u.r.l`, LF), then `python scripts/citations-merge.py sweep/citations/new-<date>.csv` — it dedups on URL, drops blank rows and sorts newest first. Never edit the register by hand.

## Return

`step=citations stopped=<complete|error> staged=N dropped=N needs-clip=0 remaining=0 notes=<≤10 words>`, where `staged` is the merge's `+N` and `dropped` the hits that failed verification. A nil is normal.
