# WIKI-SYNC.md — the deliberative catch-up pass

Trigger: **"run wiki sync"** / **"wiki sync"**. Called by the rotation at every cycle close (`SWEEP-CYCLE.md`), or on demand. **It is one thing: Phase B.** Phase A runs first only where something is sitting in `new/`, since a pending write's delta has to exist before it can be written.

## Phase B's cadence

Phase B — writing the pages Phase A's deltas are waiting on — is the one thing that genuinely batches: draining the queue opens each concept page **once per run**, where writing per item opens the same page every time and produces accretion where a batch produces synthesis. Until 2026-08-31 that argued for its own rotation day, one batch every fourth night; the overnight logs then showed headroom to run it every night instead, so it moved to the nightly close, counting against that night's sub-agent budget like any other close step. The batching itself is unchanged — one page, one open, for whatever a single night's catch queued — it just now happens on a one-night cadence instead of a four-night one.

Reconcile and acquire are not this pass's. Neither batches — a contradiction gets harder to settle as the trail cools, and an acquisition's targets rot — so they run at the cycle close, the night their queue rows are raised (`SWEEP-CYCLE.md` → *Reconcile and acquire*).

---

## The pass

```
if new/ is non-empty:                    run INGEST     — Phase A only (INGEST.md)
if logs/ingest-pending-writes.md
   is non-empty:                         run Phase B    — below
```

**One pass, no loop.** Nothing this pass runs feeds anything else it runs: Phase A files what is staged, Phase B writes the deltas that produces, and there is nothing left to go round for. Anything still in `new/` at the end is the next cycle's ingest by construction.

**Announce every pass before it runs**, per `STATUS.md` (e.g. `▶ running: phase B — wiki sync`). Emit a broad progress line too (`STATUS.md` → *Progress*) — what each pass is draining.

## Phase B — write (per page)

Drain `logs/ingest-pending-writes.md` **grouped by target page**, opening each once; delete the file when empty. **Every write is idempotent**: `grep -F "[[<source-slug>]]"` **the row's own target page, in its body** — present there means a previous attempt wrote it, which is what makes this re-runnable. **Both halves of that are load-bearing.** Grepping the whole wiki reports "already drained" for a source legitimately cited on another page, and the row is silently skipped; counting a frontmatter `sources:` entry passes a page whose prose cites nothing, which `CLAUDE.md` → *Output* does not accept as a citation.

**The test is run immediately before each write, against the page the row will actually land on, and a clean grep is where reading starts, not where it ends.** Before each write, not once at slice start, because a sibling or a concurrent pass can write or retire a source mid-slice. Against the landing page: where step 6 routes the depth to a `{place}--{topic}` intersection, that intersection is the target, and the concept page's pointer is not the write. Then read the landing page for the *story*, not the slug: the same development held under another source's slug is a merge into that entry, never a second bullet, and a row that completes a body the page calls "not held" corrects the absence rather than leaving it. Only a double-bracketed `[[slug]]` in prose counts as present. A single-bracketed one is repaired, and a bare mention in an absence note is not a citation.

**A slice removes its drained rows by matching each row's own text, never by line number** — siblings are draining the same file, so every index shifts under it — and appends nothing to a row it did not write.

**5. For each place — *nothing to write*.** Hubs are compiled, not written; what remains is only to tag regions where the item is genuinely region-level, so the compile puts it on the right hubs.

**6. For each subject.** Update the concept page; if place-specific and substantial, create or update the intersection and link from both sides.

**9. Indexes — run the generator, once per run.** `python scripts/wiki-index-gen.py --write` rebuilds the *Every intersection* block in both `topics-index.md` and `places-index.md` from `wiki/intersections/` itself; it owns its markers, touches no byte outside them, and asserts that before it writes, so the curated cells above stay hand-written and stay the lead. **The old test is retired** — open an index only when a run introduces a place or topic *not already listed* — because it inferred staleness from a run's deltas and the normal case is a new page for a pair whose halves are both already listed: it introduces neither, triggers nothing, and had left **483 pages unreachable from `places-index.md`** by the time jobs 89 and 117 counted them (closed 2026-09-20). Running it unconditionally also repairs pages minted outside this pass, which no delta test can see. `--check` exits 1 when a block is out of date. There is no entities index.

**10. Set `last_reviewed`** on every page touched, then write the run's `log.md` line — one line, the pass's result. A judgment call the run made goes in the commit body, not a second line.

## Splitting Phase B

**The partition is by target page, computed from the deltas — never by subject.** A subject's own routing rules send its writes onto pages another subject holds, so two subject-sliced agents edit one file concurrently, and the pages no subject owns — place hubs, indexes, `{place}--{topic}` intersections — are left with no slice to write them. **Before dispatch, the parent writes the page map**: every landing page (after step-6 routing) is assigned to exactly one slice, and every row goes to exactly one slice, the one that owns its page. A row that names several pages is split into one row per page, never copied into each slice that touches one. This covers the pages every slicing touches too: concept `## By place` cells, a page two topics route to, a multi-place row. A partition by subject or by place cannot produce this map, so it is not a Phase B partition, however clean it looks.

**Partitioning by subject slug looks safe and is not.** One slug maps to one concept page, so the concept pages never collide and the split appears clean; the cost lands out of sight, in the routing step. Step 6 sends place-specific depth to the intersection, and an intersection belongs to no slug — so every slice defers it, and a queue that reports itself fully drained has silently written none of it.

**Where a page-based partition is genuinely impractical, the residue is named and owned, not dropped.** Each slice writes the instructions it cannot own to a file the parent collects, and **the parent works them as a closing step before the stage commit** — they are part of the queue, not leftovers from it. A slice that has deferred work says so in its return; a slice that reports `remaining=0` has written everything its rows instructed, including the cross-page ones, or it has told the parent who will.

**A slice may mint a page its rows require.** An intersection or concept page that does not exist yet is not a reason to leave substantial material on the wrong page — the containment line bars writing outside the slice's own pages, never bringing one of its own into existence, and a slice that reads it as a bar on minting leaves the queue undrained. Index the page in the same edit, so it is never an orphan.

## Termination

**The pass ends when `logs/ingest-pending-writes.md` is empty, and the file is deleted.** The queue is finite and nothing refills it mid-pass. Where the run is interrupted before the file is drained, **what remains is what the next sync inherits**: note the row count in `log.md`, end the pass, never chase it. The gate on the rotation row is what stops that remainder growing to a night-sized block unattended.

## Concurrency

One `WIKI-SYNC` run at a time, and no other CC session writing to the vault while it runs — it needs exclusive access to `new/` and `logs/ingest-pending-writes.md`, the same worklists `SWEEP-CYCLE.md`'s nightly ingest needs. The two do not overlap, since `WIKI-SYNC` runs on its own rotation night.

## Logging

Each pass writes its own terse `log.md` entry and status line as it always does — `WIKI-SYNC` neither suppresses nor duplicates that. **When Phase B itself is split into sub-agents over disjoint page sets** (large queues, same reasoning as `INGEST.md`'s Phase A slicing), no slice writes `log.md` — each returns what it changed to the parent, which folds every slice into this pass's own single closing entry (`STATUS.md` → *The `log.md` entry*). At the end it appends **one** terse closing entry: which passes fired, rows drained, what (if anything) is still open, then the standing status line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

`python scripts/uncited-sources.py --recent 1` **should read 0** once this pass's Phase B has run — a source admitted since the last sync and cited by no page means Phase B missed one; write the delta it skipped.
