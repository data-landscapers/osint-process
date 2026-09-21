# UPDATE-WIKI.md — the update-wiki orchestrator

Trigger: **"update wiki"** / **"run update-wiki"**, and **"update wiki backfill"** for **one iteration** of it with `INGEST.md`'s backfill lane open (*Lanes* below). Callable manually, or from a sweep or batch (*Running it* below). Not called from the nightly cycle: `SWEEP-CYCLE.md` calls `INGEST.md`'s Phase A directly, and the rotation's deliberative catch-up is `WIKI-SYNC.md`. **Capped at 3 iterations and governed by the stop rule under *Termination*; `update wiki backfill` runs one.**

This file runs **no research and files nothing itself**. It only invokes the existing passes — ingest's Phase A, `WIKI-SYNC.md`'s Phase B, reconcile, acquire — in a loop until the queues are empty **or hold only what the loop itself generated**. **It does not lint**; the caller lints separately (the sweep cycle, or a manual `full lint`). Every rule governing the work lives in those passes and in `CLAUDE.md` / `wiki/reference.md`; **this file is only the loop.**

**It does not drain `new-budget/`.** Budget extraction is a step of `COUNTRY-BUDGET-BATCH.md`, run **before** update wiki, so its records are already in `new/` when this loop opens. If `new-budget/` is non-empty when this loop finishes, **say so and stop**; `run budget extract` is the process that drains it.

---

## Statuses — the loop's gates

Read all three at the **top of each iteration**. Their counts, commands and the tally line are defined in **`STATUS.md`**; don't redefine them here. In brief: **awaiting ingest** = items in `new/`; **contradictions** = files in `reviews/contradictions/open/`; **acquisitions** = open items in `reviews/acquisitions.md`.

## The loop

```
repeat:
    read gates (awaiting ingest, contradictions, acquisitions)

    if all three are 0:
        break                            # nothing left to do

    if awaiting ingest > 0:           run ingest(N, lane)  # INGEST.md — Phase A only,
                                                          #   drains new/ to raw/ + a delta.
                                                          #   PASS THE LANE — news unless the
                                                          #   trigger said backfill, and then per
                                                          #   item off scripts/ingest-lane.py.
                                                          #   PASS THE ITERATION N into every
                                                          #   Phase A slice's spawn prompt:
                                                          #   only N == 1 may write acquisition lines
                                                          #   (INGEST.md step 8). N > 1 writes the
                                                          #   absence as a dated horizon instead.
                                                          #   (ingest self-runs finance compile if it
                                                          #   admitted any finance record)
    if ingest-pending-writes:         run Phase B          # WIKI-SYNC.md's procedure — the page writes
    if contradictions  > 0:          run reconcile(N)     # RECONCILE.md — pass the iteration:
                                                          #   only N == 1 may re-route an item
                                                          #   to acquisitions.md. N > 1 writes the
                                                          #   position onto the page and deletes
                                                          #   the brief.
    if acquisitions    > 0:          run acquire          # ACQUIRE.md
```

**Announce every pass before it runs**, one line naming the process and the iteration, per `STATUS.md` (`▶ running: ingest — update-wiki iteration 2`). Also emit a **broad progress line** (`STATUS.md` → *Progress*): `iteration 2 — ingest 8 left, acquire 3 left`.

Order within an iteration is **ingest's Phase A → Phase B → reconcile → acquire**, as written. Phase A is first because reconcile and acquire both feed `new/`, so the *next* iteration's Phase A picks up whatever they produced.

**Ingest may raise an acquisition, and reconcile may re-route one, on iteration 1 only** (`INGEST.md` step 8; `RECONCILE.md` → *Re-routing*; the rules bind every caller). Acquire feeds `new/` and ingest feeds `acquisitions.md`; closing **both** feeds into `acquisitions.md` after the first iteration leaves acquire→ingest running, which drains what was queued when the run opened, and closes the cycle.

**The iteration is the parent's to pass, and a slice defaults to 1 if it is not told.** The counter belongs in the call, per the pseudocode above, not in anyone's memory.

**Finance compile is not a queue-draining pass** and has no count in the status line; it recomputes hub Financing sections from `raw/`, idempotently. It runs immediately after any ingest that admitted a finance record, and **that trigger is owned by ingest itself** (`INGEST.md` → *Ending the run*), so update-wiki does not call it separately.

## Lanes

**`update wiki backfill` opens `INGEST.md`'s backfill lane for the run; every other trigger runs news-only.** The lane is that file's rule and this file only carries it: the loop passes it into every Phase A slice's spawn prompt exactly as it passes the iteration, and a slice not told its lane is a news slice.

**The lane is a per-item whitelist, not a blanket.** In a backfill run `python scripts/ingest-lane.py` partitions `new/`: `status-acquire-*`, `progress-filler-*` and `dataset-*` batches to the backfill lane, everything else to news, so an acquire fetch or a hand clip in the same queue is still screened in full. Slice from the two lists rather than from a bare listing of `new/`.

**`update wiki backfill` runs one iteration, and its iteration is Phase A then Phase B** *(Bill, 2026-09-17, strategic review 4 task 10)*. The contradictions and acquisition lines its ingest files are not worked in the same sitting: they stand in `reviews/` for the sweep cycle's close, which runs `RECONCILE` and `ACQUIRE` whenever their queues have items, and whatever acquire fetches is ingested the next night. A backfill batch is already screened, so the second and third laps it used to take were spent almost wholly on its own tail — 39 rows took three iterations on one run. The hard cap and the stop rule below govern the news-lane loop; a backfill run has nothing for them to stop.

**The announce banner names the lane**: `▶ running: ingest — update-wiki iteration 1, backfill lane (94 items) + news lane (6)`.

**The trigger fixes the lane, never the model**: every spawn this loop makes runs on Opus, like everything else (`SWEEP-CYCLE.md` → *Model*).

## Why a loop — the passes feed each other

One pass routinely refills another's queue:

- **ingest** drains `new/`, but can file contradictions into `open/` and add documents to `acquisitions.md`.
- **reconcile** drains `open/`, but can re-route items to `acquisitions.md` and ingest primaries into `new/`.
- **acquire** drains `acquisitions.md`, but stages every fetched document into `new/`.

The loop keeps going until a fresh read finds **all three empty**, **or until the only thing left in them is what the loop itself generated**, the stop rule below.

## Termination

Each pass is self-draining and anti-recurrence **by design**, so the queues strictly shrink:

- **ingest** always moves every item out of `new/` (admitted to `raw/`, or deleted after any contradiction brief / acquisition line is filed).
- **reconcile** closes every `open/` item: resolved, or the position written dated onto the page it bears on after its **one** attempt.
- **acquire** resolves every item in **one** attempt: ingest-and-strike, or drop.

**The stop rule — stop when the queue is only your own tail.** Read each iteration's queues and ask **who put this here**. A queue staged by something outside this run — a sweep, a hand clip, a batch, the night's cycle — is the work, and the loop drains it. A queue containing **only** what the *previous* iteration's own reconcile or acquire generated is the loop feeding itself: **stop, state the finding dated on the page it bears on, and leave the rest for the next run.** `new/` and `acquisitions.md` are persistent, and the next run opens on them.

This is `CLAUDE.md` → *Good beats perfect* applied to the loop: a tidy log of clean iterations camouflages the pattern (`STATUS.md` → *Say when CC's own context is the limit*). The judgement is not *can this go round again* but *was this round asked for*.

**The per-item cap: three entries and the item is over.** The iteration cap bounds the *run*; this bounds the *item*. **An item named in three of this run's `log.md` entries is disposed of at the third**: dropped, or written onto the page it bears on as a dated absence. Never a fourth. `scripts/effort-cap.py` (lint #33) reports what the run kept returning to; the disposal is this pass's own, taken during the run, not read off the report afterwards.

**Apply the value test at entry, not exit.** *Does it change what the wiki can say?* is asked before opening a contradiction or an acquire line, not after closing one. A figure no published page turns on fails it, however tractable it looks.

**Hard cap: 3 full iterations** (one for `update wiki backfill`, § *Lanes*). Reconcile and acquire stage primaries back into `new/`, so each iteration can refill the next one's input; the cap is the guard. If it is reached, exit and **flag it in `log.md`** rather than spinning: a run that hits it means a pass is failing to drain (repeated `529`s, a re-route cycle) and wants a human look, not another lap. A pass that errors out mid-run leaves its queue non-empty, so the loop retries it next iteration; a *persistent* failure is what the cap catches.

## Concurrency

**One update-wiki run at a time, and no other CC session writing to the vault while it runs.** The passes it calls each need exclusive access to their shared worklists (`new/`, `open/`, `acquisitions.md`).

## Logging

Each pass writes its **own** terse `log.md` entry and status line as it always does; update-wiki neither suppresses nor duplicates that. At the end, update-wiki appends **one** terse closing entry: iterations run, which passes fired, whether the cap was hit, then the standing status line, which on a clean run reads zero across the three queues:

`contradictions - 0 ; acquisitions - 0 ; awaiting ingest - 0 ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

## The collection window — two fields, on every run that admits anything

**Measure `sweep_closed` and `ingest_started`, local machine-clock time, for every iteration that admits anything**, feeding `INGEST.md`'s own close, which stamps them (with its own `last_admission`) via `cycle-manifest.py --stamp` into `logs/collection-stamp.json`. `intake.md` §6a holds the shape. This loop keeps no manifest, so that stamp is the whole of its record.

**This loop collects nothing**; it drains a queue others staged, so its `sweep_closed` is **the newest `retrieved:` across the items that iteration admitted**. `ingest_started` is when that iteration's Phase A began. Both are read, not estimated. `last_admission` stamps admission, not collection, and the bulletin's byline is a claim about collection — which is why the stamps exist and why the batch labels, being free text, cannot stand in. This loop does not mirror, so it writes no `cycle-manifest.json` itself; `--stamp`'s file is what carries its window forward to whichever pass next mirrors and writes one.

## Running it — two entry points

- **Manually:** `update wiki`.
- **From a sweep:** the daily trade-journal sweep (`SWEEP-DAILY-LIST.md`) stages candidates flat into `new/`, then hands off to update-wiki, which processes them through ingest and drains any contradictions / acquisitions they surface.
- **From a batch:** `COUNTRY-BUDGET-BATCH.md` (three sweeps → **budget extract** → this). The extraction has already staged its records into `new/`, so this loop's first ingest admits them; the loop itself never touches `new-budget/`.
