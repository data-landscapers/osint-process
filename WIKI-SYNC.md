<!-- reader: cc; type: runbook -->
# WIKI-SYNC.md — the deliberative catch-up pass

Trigger: **"run wiki sync"** / **"wiki sync"**. Called by the rotation at every cycle close (`SWEEP-CYCLE.md`), or on demand. **It is one thing: Phase B.** Phase A runs first only where something is sitting in `new/`, since a pending write's delta has to exist before it can be written.

## Phase B's cadence

Phase B — writing the pages Phase A's deltas are waiting on — is the one thing that genuinely batches: draining the queue opens each concept page **once per run**, where writing per item opens the same page every time and produces accretion where a batch produces synthesis. It runs at the nightly close, counting against that night's sub-agent budget like any other close step: one page, one open, for whatever a single night's catch queued.

Reconcile and acquire are not this pass's: neither batches — a contradiction gets harder to settle as the trail cools, and an acquisition's targets rot — so they run at the cycle close, the night their queue rows are raised (`SWEEP-CYCLE.md` → *Reconcile and acquire*).

---

## The pass

```
if new/ is non-empty:                    run INGEST     — Phase A only (INGEST.md)
if logs/ingest-pending-writes.md
   is non-empty:                         run Phase B    — below
```

**One pass, no loop.** Phase A files what is staged, Phase B writes the deltas that produces; anything still in `new/` at the end is the next cycle's ingest.

**Announce every pass before it runs**, per `STATUS.md` (`▶ running: phase B — wiki sync`). Emit a broad progress line too (`STATUS.md` → *Progress*).

## Phase B — write (per page)

Drain `logs/ingest-pending-writes.md` **grouped by target page**, opening each once; delete the file when empty. **Every write is idempotent**: `grep -F "[[<source-slug>]]"` **the row's own target page, in its body** — present there means a previous attempt wrote it, which is what makes this re-runnable. **Both halves are load-bearing**: a whole-wiki grep silently skips a row whose source is cited on another page, and a frontmatter `sources:` entry is not a citation (`CLAUDE.md` → *Output*). **The page's `sources:` line is extended only with `python scripts/sources-add.py <page> <slug>…`**, never by parsing and rewriting the frontmatter, which splits old comma-bearing entries. **A page keeps its HEAD line endings**, tested by counting `b'\r\n'` in its bytes: `sed -i` and the Edit tool flatten CRLF.

**The test is run immediately before each write, against the page the row will actually land on, and a clean grep is where reading starts, not where it ends.** Before each write, because a sibling or concurrent pass can write or retire a source mid-slice. Against the landing page: where step 6 routes the depth to a `{place}--{topic}` intersection, that intersection is the target, and the concept page's pointer is not the write. Then read the landing page for the *story*, not the slug: the same development held under another source's slug is a merge into that entry, never a second bullet, and a row that completes a body the page calls "not held" corrects the absence rather than leaving it. Only a double-bracketed `[[slug]]` in prose counts as present. A single-bracketed one is repaired, and a bare mention in an absence note is not a citation.

**A landing page over its line is rewritten, never appended to.** Before the write, `python scripts/page-length.py <landing page>` — lint #8's own measure. `under` or `ruled`: write as below. `OVER` (exit 1): the write **rewrites the landing section as synthesis** — current state with the new source folded in, dated per-ingest bullets merged, every citation kept inline on its claim, events left to their source pages (`CLAUDE.md` → *Structure*). Nothing an ingest bullet said is lost. Then `python scripts/page-length.py --trimmed <page> --before <N>`, which records both word counts in `logs/phaseb-trims.csv` and exits 2 (`GREW`) on a rewrite that grew the page by more than a clause, which the slice redoes. **The rewrite may not grow the page**: the new source takes the words of what it supersedes or merges with, and where nothing gives way it goes in as one clause. A page still over after its section is rewritten stays over; the next write to it rewrites the next landing section.

**A slice removes its drained rows by matching each row's own text, never by line number** — siblings are draining the same file, so every index shifts under it — and appends nothing to a row it did not write.

**5. For each place — *nothing to write*.** Hubs are compiled, not written; only tag regions where the item is genuinely region-level, so the compile puts it on the right hubs.

**6. For each subject.** Update the concept page; if place-specific and substantial, create or update the intersection and link from both sides.

**9. Indexes — run the generator, once per run.** `python scripts/wiki-index-gen.py --write` rebuilds the *Every intersection* block in both `topics-index.md` and `places-index.md` from `wiki/intersections/` itself; it touches no byte outside its markers, so the curated cells above stay hand-written. **Run it unconditionally**, never only when a run introduces a new place or topic: a new page for a pair whose halves are both listed triggers no delta test, and the unconditional run also repairs pages minted outside this pass. There is no entities index.

**10. Set `last_reviewed`** on every page touched, then write the run's `log.md` line — one line, the pass's result. A judgment call the run made goes in the commit body, not a second line.

## Splitting Phase B

**The partition is by target page, computed from the deltas — never by subject.** A subject's own routing rules send its writes onto pages another subject holds, so two subject-sliced agents edit one file concurrently, and the pages no subject owns — place hubs, indexes, `{place}--{topic}` intersections — are left with no slice to write them. **Before dispatch, the parent writes the page map**: every landing page (after step-6 routing) is assigned to exactly one slice, and every row goes to exactly one slice, the one that owns its page. A row that names several pages is split into one row per page, never copied into each slice that touches one. This covers the pages every slicing touches too: concept `## By place` cells, a page two topics route to, a multi-place row. A partition by subject or by place cannot produce this map, so it is not a Phase B partition.

**Partitioning by subject slug looks safe and is not**: step 6 sends place-specific depth to an intersection, which belongs to no slug, so every slice defers it and a queue reporting itself drained has written none of it.

**Where a page-based partition is genuinely impractical, the residue is named and owned, not dropped.** Each slice writes the instructions it cannot own to a file the parent collects, and **the parent works them as a closing step before the stage commit** — they are part of the queue, not leftovers from it. A slice that has deferred work says so in its return; a slice that reports `remaining=0` has written everything its rows instructed, including the cross-page ones, or it has told the parent who will.

**A slice may mint a page its rows require.** A missing intersection or concept page is no reason to leave material on the wrong page: the containment line bars writing outside the slice's own pages, never bringing one into existence. Index the page in the same edit, so it is never an orphan.

## Termination

**The pass ends when `logs/ingest-pending-writes.md` is empty, and the file is deleted.** Where the run is interrupted before the file is drained, **what remains is what the next sync inherits**: note the row count in `log.md`, end the pass, never chase it. The gate on the rotation row is what stops that remainder growing to a night-sized block unattended.

## Concurrency

One `WIKI-SYNC` run at a time, and no other CC session writing to the vault while it runs — it needs exclusive access to `new/` and `logs/ingest-pending-writes.md`, the same worklists `SWEEP-CYCLE.md`'s nightly ingest needs. The two do not overlap, since the nightly close runs `WIKI-SYNC` after the night's ingest has finished.

## Logging

Each pass writes its own terse `log.md` entry and status line; `WIKI-SYNC` neither suppresses nor duplicates that. **When Phase B is split into sub-agents**, no slice writes `log.md` — each returns what it changed to the parent, which folds every slice into this pass's single closing entry (`STATUS.md` → *The `log.md` entry*). At the end it appends **one** terse closing entry: which passes fired, rows drained, what (if anything) is still open, then the standing status line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

`python scripts/uncited-sources.py --recent 1` **should read 0** once this pass's Phase B has run — a source admitted since the last sync and cited by no page means Phase B missed one; write the delta it skipped.
