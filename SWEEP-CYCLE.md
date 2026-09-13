# SWEEP-CYCLE.md — the nightly sweep orchestrator

Trigger: **"run the sweep cycle"**, typed by hand in an interactive session; **no automatic or scheduled trigger exists or is planned.** Each run works **one numbered day** from the rotation in `logs/sweep-cycle_log.md`. **There is no time envelope**: no step checks a clock.

This file is **only the wiring**; the rules governing the work live in the processes it calls.

## Execution model

One CC run; the parent is a **thin loop** that selects the day, runs its processes one at a time, holds only the tallies they return and keeps the log. It reads only this file and the cycle log, never a delegated process file and never a body: `ls new/` for a count, never `cat`.

**One level of sub-agent (the Task tool); the parent owns every spawn.** A non-batching step (`INGEST` Phase A, `LINT`) is one sub-agent; a batching step is N, **~8–10 rows or countries each**, never one per country. The parent reads the list's row count (`wc -l`) and nothing else. **Each batch gets its own suffix for every per-run file the sweep writes, never for a sweep's persistent high-water state** (`state.json`). At most **20 running at once**.

### Why the parent owns the spawn

**No sub-agent spawns another**; the parent counts every spawn it makes, because only the parent can see them. Every spawn is synchronous in ordering; never a background agent, never `SendMessage`.

**The parent never ends a turn on a waiting line.** It holds the turn while a spawn is outstanding (`Monitor` with an until-loop on the agent's output, or the next independent item on the day's list). If a turn must end with work outstanding, its last line is `outstanding: <step> · resumes on its own · no input needed`.

**No sub-agent may stall on a permission prompt**: `.claude/settings.json` (git-tracked) sets `permissions.defaultMode` to `bypassPermissions` and denies `AskUserQuestion`.

### Model

**Everything runs on Opus** *(Bill, 2026-09-08 — the tiered model policy and the backfill run's Sonnet override are removed)*. Start the session on `--model opus`; the parent and every agent it spawns inherit it, whatever the step, the trigger or the item's lane. No spawn names a model, and no step is assigned one.

### No budget, no cost report

**No step checks a budget, no step is stopped by one, and the night's cost is neither measured nor reported** *(Bill, 2026-09-08 — the 90-sub-agent brake, its `--nobrake` override and the run-cost line all removed; `scripts/budget-check.py` and `scripts/run-cost.py` are deleted)*. The night runs the day it selected to its close and reports the standing tally line (`STATUS.md`).

### Usage log

**`python scripts/usage-log.py`, twice a night: the first act, before draining notes, and after the cycle manifest, before the last mirror** *(Bill, 2026-09-13)*. It inserts `Date`, `Time (UTC)`, `7d usage` and `5h usage` — the weekly and 5-hour plan limits used, as percentages — at the top of `logs/usage-log.csv`, newest first — a record, not a budget: nothing reads it back, nothing is stopped by it, and it goes on no closing line. It never fails the night; an unreadable figure is written `n/a`. The closing row lands after the last commit, so it rides the next night's first commit — the mirror carries it either way.

### What every sub-agent prompt carries

**Pasted verbatim, never paraphrased or summarised**, and the containment line **names exact files, never a bare folder** — a boundary stated loosely is a boundary a slice reads generously.

- **[`wiki/capture-rule.md`](wiki/capture-rule.md), baked in**, with *never read a feed whole*.
- **The containment boundary** (`intake.md` §7): a sweep writes **only** to `new/` and its own `sweep/`; never `raw/`, never a wiki page, not even to reformat.
- **`logs/log.md` only through `scripts/log-append.py`**, and **`logs/log.md` and `reviews/rule-candidates.md` are the parent's to write** — a slice flags them in its return. The parent corrects a nested line with `--at` (UTC) against its own measurement.
- **Runs a process, never amends one, and runs no git command that writes**: no edit to a root process file, `CLAUDE.md` or `wiki/reference.md`; no commit, add, checkout, restore or reset; **and no tree-wide git command at all** — `stash`, `reset`, `checkout`, `clean` — because a slice cannot see what its siblings hold uncommitted. A rule change returns as a recommendation the parent applies; `assert-containment.py` enforces this (§ *Commit at boundaries*).
- **Spawns nothing**: no `Agent` tool, no sub-agent of its own. A general-purpose agent carries every tool unless told otherwise.
- **Writes each file back with the line endings it already had** — read the file's own convention and preserve it; never normalise to LF or CRLF, and never assume a corpus-wide convention, because both directions have been "corrected" wrongly.
- **Writes scratch files only under its own slice-unique subdirectory**, named for the slice. Concurrent slices otherwise share one scratchpad and overwrite each other's helpers and downloads.
- **Cross-checks `new/` again immediately before it writes a staged file, not only at enumeration.** Concurrent slices enumerate before they fetch, so the pre-fetch check cannot see a sibling that stages the same URL while the fetch is in flight. **On a collision the later writer withdraws its own copy** and logs the item `already-seen`, so ingest sees one candidate.
- **A nil is reportable only on `stopped=complete`** (§ *What a sub-agent returns*).

### The watchdog

`scripts/stall-watch.py`, armed at Step 0 under `Monitor` and left running all night; its stdout lines re-invoke the parent.

```
python scripts/stall-watch.py --quiet-minutes 25
```

On waking, if the outstanding step's work has not moved, the parent **kills that spawn and re-spawns it once**. Not a deadline.

### What a sub-agent returns — one line, always

```
step=<name> stopped=<complete|context|error> staged=N dropped=N needs-clip=N remaining=N notes=<≤10 words>
```

Anything longer goes to a file the parent does not read. `context` is distinct from `complete`: `remaining=N` on `context` means re-spawn, not a nil. An errored or absent instrument returns `stopped=error`, never `staged=0 stopped=complete`; the parent **re-spawns an `error` step once** before recording it. No pause state, no timeout loops; a failed run is re-run.

## Commit at boundaries

**Commit at each stage boundary, never once at the end**, each preceded by `python scripts/assert-containment.py --stage <sweep|ingest|lint|close>`; exit 1 = do not commit as it stands. Allowed prefixes and the absolute deny set (`CLAUDE.md`, `wiki/reference.md`, every root procedure) live in the script; `--list` prints them. To commit outside a stage's set, pass `--allow-extra <path>` and say why in the log line.

```
usage-log.py                                        # first act of the night; see § Usage log
drain X:\notes-for-osint.md — act on every open note, close to -resolved (X:\README.md -> Conventions)
assert-containment.py --stage notes [--allow-extra <path> ...] ; git commit  # only if this repo changed

Exa canary — on failure skip every line marked [exa] below; the rest of the night runs
arm stall-watch.py under Monitor, all night
select day D: Skip, then oldest Start (blank sorts oldest); New-Start = now        [exa]
window from D's (old) Start                                                        [exa]

SWEEP-DAILY-LIST, SWEEP-DAILY-OFFLIST              stage-only, batched             [exa]
D's unprefixed Jobs, in order                      stage-only, batched; unbuilt -> "Day D: <NAME> not built" in logs/log.md   [exa]
assert-containment.py --stage sweep ; git commit

INGEST Phase A, once, lean form                    compile-hubs.py and FINANCE-COMPILE fire from it, scoped
cycle-manifest.py --stamp                           parent-measured sweep_closed/ingest_started; see below   [exa]
assert-containment.py --stage ingest ; git commit

D's @-prefixed Jobs, in order                                                      [exa]
quick lint ; RECONCILE if open/ has items [exa] ; ACQUIRE if acquisitions.md has open lines [exa]
WIKI-SYNC Phase B if logs/ingest-pending-writes.md is non-empty
full lint's batched checks
assert-containment.py --stage lint ; git commit

prune sweep-url_log.md before D's (old) Start (skip if blank) [exa] ; rotate-log.py --apply
close D: Prev Duration = Duration; Duration = now - New-Start (H:MM); Start = New-Start; End = now; clear New-Start   [exa]
assert-containment.py --stage close ; git commit

mirror to O:\

housekeeping: oldest open entry in X:\housekeeping-jobs.md — whole job, or its largest tractable slice
assert-containment.py --stage housekeeping [--allow-extra <path> ...] ; git commit

rules: drain reviews/rule-candidates.md — RULES.md, the parent's own work, no sub-agent
assert-containment.py --stage rules [--allow-extra <each process file amended>] ; git commit

cycle-manifest.py --pass "sweep cycle" --count ...  # after the night’s LAST commit, before the last mirror
usage-log.py                                        # before the last mirror
git push ; mirror to O:\
export-process-mirror.py  # after the push; a refusal goes on the closing line and never blocks
```

## The cycle manifest

**`python scripts/cycle-manifest.py --pass "sweep cycle" --count items_in=N --count admitted=N --count dropped=N`, after the night’s last commit — the rules commit, not the close commit — and before the last mirror.** It writes `cycle-manifest.json` at the repo root, and that file is the whole of what CORPUS reads about a run: the commit the mirror carries, the collection window, the rotation's newest close, and the counts this pass measured. It is git-ignored and written after the commit on purpose — `head` has to name the commit that is actually on `O:\`, which a file committed inside that commit cannot do. **Counts are passed in, never inferred**: a pass that measured none writes none, because an absent count is visible and a wrong one is not. Lint #19 asserts that the manifest on the mirror names the mirror's own HEAD.

## Mirror

**The night's last act, after the final commit: `"C:\Program Files\FreeFileSync\FreeFileSync.exe" SyncSettings.ffs_batch`**, a one-way mirror of `C:\OSINT` to `O:\` (`\\bill-vivobook\osint`), `.git` included, deletions propagated. **`O:\` is CORPUS's read-only copy of this vault, not a backup.** A failed mirror is re-run by hand.

**Assert on `git -C O:\ rev-parse HEAD` matching local, never on stdout**, and only **after the `FreeFileSync` processes exit**; the newest HTML log under `%APPDATA%\FreeFileSync\Logs\` is the second instrument. The same check is `LINT` #19 (`scripts/lint-mirror-head.py`), surface-only; `--gate` stops on it.

## The process mirror

**After the final push and mirror: `python scripts/export-process-mirror.py`.** It copies the process layer — root procedures, `scripts/`, `documentation/`, the vocabulary lookups and the thirteen `wiki/` specs, on the allowlist in the script — from `HEAD` to the public repository `data-landscapers/osint-process` (checkout `..\osint-process`, cloned if absent) and pushes. It has nothing to do with `O:\`: this is what lets anyone read how the vault is built without reading the vault. `raw/`, the compiled wiki, `logs/` and `reviews/` never go.

**A refusal is not a failure of the night.** The script refuses on a markdown block quote over 200 characters or a secret, and reports any new root file, lookup or `wiki/` spec as *unclassified*. Put the line on the closing line; the ruling — acknowledge the quote's hash in `REVIEWED_QUOTES`, or add the path to `PUBLISH` or `WITHHELD` — is a housekeeping or rules act, never a sub-agent's. No change to a published file means no commit. LINT #37 catches an export that did not land.

## Housekeeping, after the night's close

**Runs once, after the first mirror — the register's oldest open entry, and no other.** Selection is `X:\housekeeping-jobs.md` → *Jobs — oldest first*, top entry. An empty register: skip, say `no housekeeping job open` on the closing line.

**Writes to `X:\housekeeping-jobs.md` and `-resolved.md`, commits nothing there** — the same boundary as draining notes-for-osint, `X:\README.md` → *Conventions* governs closing an entry. **Commits whatever it changed in `C:\OSINT`** — the pages, scripts or fixes the job actually produced — at its own boundary, gated by `assert-containment.py --stage housekeeping`.

**One sub-agent**: housekeeping is read-and-judge work throughout, the same class as a Phase B page write.

**An entry sized above 120 minutes is split before it is worked** (`housekeeping-jobs.md` → *Rough sizing*) — the night's housekeeping act is then the split itself, plus the first of the new jobs if there is room. Slicing an oversized entry night after night is what the sizing rule exists to stop.

**Whole job if it closes within the night; otherwise the largest tractable slice**, logged as a dated annotation on the still-open entry — job 30's own pattern, run here on a fixed nightly cadence instead of an ad hoc one. This is the one exception to `housekeeping-jobs.md` → *How a job is worked*'s "split into numbered jobs before starting": the entry stays oldest and is picked again the next night, until it can honestly be struck. A job that closes is struck (`x` prefix, cleared date) and moved to `housekeeping-jobs-resolved.md`, exactly as a manually-triggered session would close it. **Updates `housekeeping-jobs.md` → *Rough sizing* in the same pass** — drop the row on a strike, adjust it where the slice changed the job's known scope.

## Rules, the night's last act

**`RULES.md` over the whole of `reviews/rule-candidates.md`, after housekeeping and after nothing.** It is last because every other pass reads the rules it writes: a rule that changes with a step still to come leaves that step working to a different file from the ones before it, which is the mid-run rule change `CLAUDE.md` forbids. At the end of the night there is no such step, so the objection is spent — and the queue drains on the same nightly cadence as every other one rather than waiting on somebody to notice it.

**The parent's own work, never a sub-agent**: a spawned agent runs a process and does not amend one, and this is the pass that amends them.

**`assert-containment.py --stage rules` names every process file it touched with `--allow-extra`** — the deny set still stands, so the exception is per file and the night's log line lists exactly which rules changed. An empty queue: skip, say `no rule candidates` on the closing line, which is the ordinary state of a good week.

**Then push and mirror, once, covering housekeeping and rules together** — the only push in this file, so a same-night change reaches GitHub and `O:\` before tomorrow's mirror rather than waiting on it.

## Draining notes-for-osint

**First act of the night, before the Exa canary — unconditional, and it runs even on a canary failure.** Read every open note in `X:\notes-for-osint.md`; act on each and close it. `X:\README.md` → *Conventions* holds the rules this pass follows, not a copy of them here: the bar for writing a note, what closing means (full text and every dated annotation carried to `X:\notes-for-osint-resolved.md`, nothing left behind, numbers never reused), and that a note carrying its own fix is a task — do it and log it. A note that only raises a question the writer could have answered stays open, for CORPUS.

**Writes to `X:\`, commits nothing there** — `X:\README.md` → *Conventions*: CORPUS does the committing on that share, OSINT writes and stops.

**Commits whatever it changed in `C:\OSINT`, its own boundary before the four below.** A note's fix routinely reaches this repo — a script, a wiki page, a process file — and that is committed here, not folded into `sweep`, `ingest`, `lint` or `close`, whose write-sets it may not fit. `python scripts/assert-containment.py --stage notes` (write-set `*`) governs it; the absolute deny set still applies, so a fix landing on `CLAUDE.md`, a `wiki/` spec or another root procedure takes `--allow-extra <path>` per file, named in the log line, exactly as the parent already does at any other stage. Skip the commit if nothing in this repo changed — a run that only touched `X:\` has nothing to commit here.

## Step 0 — the Exa canary

**First act, before selecting a day or writing anything**: one `web_search_exa`, `"data protection Africa"`, `numResults: 1`.

**On failure (error, exception, empty result set, absent connector) the collecting half of the night does not run — the processing half does** *(Bill, 2026-09-08)*. The canary proves the instrument, so what it gates is every pass that reaches outside the vault, and nothing else. **No fallback tool and no reduced sweep**: a sweep that cannot search does not run at all, because a nil it reports would be its own blindness rather than evidence of a quiet day.

- **Does not run**: every sweep, the day's jobs, `RECONCILE` (its research step is Exa) and `ACQUIRE` (its one attempt and its gap probe are Exa). Their queues stand.
- **Runs as normal**: `INGEST` Phase A over whatever is already in `new/` — a primary it cannot download becomes an acquisition line, which is step 8's ordinary path — then `WIKI-SYNC` Phase B, the compiles, quick and full lint, `PRUNE`, housekeeping, rules, the commits and the mirror. None of them touches the network, and the vault's own work does not depend on tonight's weather.
- **The rotation does not move**: select no day, write no `New-Start`, close no day. The day's collection is what did not happen, so the day is still due.
- **No `cycle-manifest.py --stamp`**: nothing was collected, so there is no window to stamp, and the manifest carries the last real one forward. The manifest itself is still written after the final commit — it must name the commit the mirror carries (lint #19).

Write the fatal line: `**SWEEP-CYCLE** · FATAL: Exa canary <the error> — sweeps skipped, processing ran`.

**Every sweep runs `wiki/origin-screen.md` itself**; ingest is the only door (lint #17). **Sweeps run stage-only**, into `new/`. **Lint runs only here** (`WIKI-SYNC.md` never lints): **quick lint every night**, `LINT.md`'s nightly bands **plus the incremental checks (#6, #4, #5, #14, #20, #7) over the records this run admitted**; **full lint's whole-vault batched checks run every night too**, at the close (§ *Commit at boundaries*).

## Reconcile and acquire

At the close, each **only if its queue has items**: `RECONCILE` for `reviews/contradictions/open/`, `ACQUIRE` for open lines in `reviews/acquisitions.md`, **`WIKI-SYNC` Phase B for `logs/ingest-pending-writes.md`**. Their write-set is inside the `lint` stage's. **`REPORT-LINT`'s checks A–F do not run here**; `FINANCE-COMPILE.md`'s closing step runs them whenever ingest admits a finance record.

## Ingest, once, at the close

**One `INGEST` Phase A pass drains the whole night's catch**, lean form: it files (never researches) any contradiction or acquisition line and opens no Phase B page. Volume is handled by Phase A's own slicing (`INGEST.md`), never by splitting the pass. `logs/sweep-url_log.md` is written per item at disposition (`INGEST.md` step 11), so every sweep **also cross-checks `new/`** on the same normalised URL.

**The parent measures the collection window for every close this pass's ingest makes** — `intake.md` §6a, which binds every path that puts material into `raw/`, and this is the path that collects most. `sweep_closed` is the **sweep-stage commit**: the staging sweeps have all returned, so nothing more could have been caught. `ingest_started` is the **first Phase A slice's spawn**. The `@`-prefixed jobs run after this pass and stage for the next night, so they never move `sweep_closed`. **Unstamped, `cycle-manifest.json` carries no `collection` block at all — CORPUS reads `collection.sweep_closed` directly with no fall-back behind it** (notes-for-osint 132: the rotation's close is not a substitute, since its jobs finish hours after collection stops and publishing it as *Last updated* would overstate coverage). A close that skips `--stamp` is a defect, not a graceful degradation.

## The cycle log

`logs/sweep-cycle_log.md` is boss; its header defines the columns, `Skip`, the `@` prefix and the duration ageing, and this file holds no copy. **The rotation is however many rows it has**; nothing in the vault states the length as a number.

**Selection**: oldest `Start`; **blank counts as oldest, two blanks tie-break on the lower `Day`**. Test **`Skip`**, taking the next-oldest row on it, `Start` untouched. The cycle never sets or clears `Skip` and names a skipped row on the closing line. **No row due**: run the common prefix and the close, close no day, say `no day due` on the closing line.

**The day's window**: the rotating day's sweeps hold no state; the cycle passes them `window_start = D's (old) Start's date − 1 day`, `window_end = today`. **Blank old `Start`**: `window_start = today − one rotation`. `Start` is not advanced until the day closes, so a re-run after a failure sweeps the same window. The daily and off-list sweeps keep their own high-water state.

**Close** in the sequence's order; a first-ever run leaves `Prev Duration` blank. **A day whose jobs are *all* unbuilt, or all end `stopped=error` after their one re-spawn, does not close**: run the common prefix and close as normal, **leave `Start`, `Duration` and `Prev Duration` unadvanced**, and say `day D: no job built, day not closed` or `day D: <NAME> errored, day not closed` on the closing line. **A populated `New-Start` is the interrupted-run signal**; the day stays oldest, is picked again and re-runs from scratch.

## Concurrency

One cycle at a time, and no other CC session writing to the vault: the cycle needs exclusive access to `new/`, `reviews/contradictions/open/` and `reviews/acquisitions.md`.

## Logging

Each process writes its own `logs/log.md` line. The cycle adds one closing line, with any row passed over for a skip and the standing status line per `STATUS.md`. On screen the pass closes on the standing count line (`STATUS.md`).
