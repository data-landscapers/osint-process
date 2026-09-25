<!-- reader: cc; type: spec -->
# ingest-judgment.md — why ingest's rules are shaped as they are

*(The reasoning behind `INGEST.md`, which keeps each rule as one sentence and points here. Read it when a rule's edge is unclear; the runbook is what a slice follows.)*

## 1. Parallel slices and the shared registers

A sequential run multiplies wall time by the slice count, the largest cost a big ingest pays, and nothing in one slice's work waits on another's: each holds its own file list and no `raw/` file another slice owns. The risk parallelism carries is concurrent writes to the few files every slice shares, and those losses have been silent every time: a whole slice's block gone while every slice reported success.

So only a register with a locking appender is written by slices in parallel (today `logs/sweep-url_log.md`, through `url-log-append.py`). An appender with no lock, or one that rewrites the whole file, loses a sibling's rows however carefully each slice appends. A slice-named file survives a session that dies before the merge, so the resume merges it rather than re-deriving it. The parent reconciles each slice's returned delta count against the rows in `logs/ingest-pending-writes.md`, and `git diff`s the other registers. That is why a slice returns its delta lines verbatim: twice the returned report was the only surviving copy of a clobbered block. Fall back to sequential spawning only where a batch's own history shows the reconciliation failing.

Registers are appended, rows removed by their own text and never by line number, because siblings shift every index; no whole-file formatter runs over one, because its line breaks are records. A candidate leaves `new/` only by the exact path on the slice's list: `sweep_batch:` is the run's label, not the slice's, and `new/` is untracked, so what a pattern takes from a sibling git cannot return.

## 2. Why a clean tier 1 settles nothing

Tier 1 checks two different things, and neither substitutes for the other. `lookups/raw-url-index.csv` holds admissions only, so a URL a previous run dropped returns CLEAN from it for ever; `logs/sweep-url_log.md` is the only record of the three non-admitting dispositions.

Twins are systematically not URL-shaped. The shapes met repeatedly: the same document at a reordered query string; one ministry PDF at a second host; a publisher's own other-language edition; a machine translation of an agency release; a syndicated wire rewrite; two tabs of one reference page, one body a strict subset of the other; and a landing page against its own file. A record admitted on a catalogue landing page and the same document's PDF differ in URL by construction, so tier 1 returns CLEAN on exactly the completions most worth making — the statutes, strategies and diagnostics held at a fraction of their length. Obeying "drop, never read the body" on a `DUP-SLUG` once cost a 3.5x fuller capture of a held truncation, which is why the completion test runs on step 3's read as well as on a tier-1 hit.

The backfill lane skips tier 3, but it does not stop the step-3 read from seeing things. A backfill batch carries whatever URL a search surfaced, while the vault holds whatever URL an earlier acquire resolved to, so the two differ for exactly the documents most worth holding. So a twin that the step-3 read makes visible is disposed of under *Duplicates*, never admitted just because tier 1 came back clean. A same-slug file already at the target `raw/YYYY/` path is itself a duplicate signal, and an unnoticed overwrite loses the richer record silently.

Tier 3's drop-by-default is a rule about cost, not precedence. An institution's own primary of a held secondary is a *Replace* — dropping it leaves the wiki citing a rewrite of a document it could cite directly. An arrival carrying a dated figure, named party or primary link the held record lacks is a *keep both*. Both show in the title and lede tier 3 already reads, so neither costs a body open.

## 3. Staged facets are a producer's guesses

A staged facet that is merely *invalid* surfaces later; one that is **valid but wrong** passes every mechanical gate and reaches `raw/` as fact. The shapes met: a blanket topic applied to a whole batch; a place taken from the publisher's nationality where the story names none; a date stamped `YYYY-01-01 / year / proxy` over an item whose page states the day; a date and place contradicting the document's own printed imprint. Invalid slugs arrive as a compound `<slug>--<suffix>` or a plausible slug not in the vocabulary, and surface only when Phase B opens a concept page that does not exist. The value most often wrong is `geopol.*`: bilateral aid and project finance are not geopolitics whichever country funds them. `scripts/stage-check.py` now catches the mechanical half at the sweep commit; the judged half stays with ingest, and the producer is told once, not per item.

A fetch-failure note is not an `excerpt`: an excerpt is a verbatim portion of the document, and a note carrying facts from elsewhere puts unsourced claims into `raw/`.

## 4. Hub lines: grouping, and the classes that correctly get none

The bullet is a claim that a dated development happened in a place. The event is established from the bodies, and the date is evidence for it, never the grouping key: two accounts published a day apart are the commonest shape, and a date key cannot see them. Grouping runs against the held corpus inside a date window, not against one run's output, because the second account usually arrives nights after the first. A collapse is not complete until each loser carries `hub_line_none:`. A carrier's `hub_line_sources:` beside a loser that keeps its own `hub_line:` compiles as two bullets, and lint #7 reads that as a settled keep-both.

Correctly none, and never a gap (`scripts/hub-line-partition.py`; RESIDUAL-UNCITED should read 0): finance and budget records and budget-document companions; `cite_through:` captures; no `places:` or no parseable `published:`; a standing page under a proxy date; an older source arriving late; reference studies and academic or named-analyst work; forward notices, convenings and profiles. Two backlog classes are backfilled on demand, never by sweep: PRE-CONTRACT (ingested before `hub_line` existed) and RESIDUAL-CITED (already on a concept or intersection page).

The catalogue hero is not gated like this: it is the record's public subtitle, owed by every class above alike.
