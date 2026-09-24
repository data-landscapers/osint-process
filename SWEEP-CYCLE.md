# SWEEP-CYCLE.md — the nightly sweep orchestrator

Trigger: **"run the sweep cycle"**, typed by hand in an interactive session; **no automatic or scheduled trigger exists or is planned.** Each run works **one numbered day** from the rotation in `logs/sweep-cycle_log.md`. **There is no time envelope**: no step checks a clock.

This file is **only the wiring**; the rules governing the work live in the processes it calls.

## Execution model

One CC run; the parent is a **thin loop** that selects the day, runs its processes one at a time, holds only the tallies they return and keeps the log. It reads only this file and the cycle log, never a delegated process file and never a body: `ls new/` for a count, never `cat`.

**One level of sub-agent (the Task tool); the parent owns every spawn.** A non-batching step (`INGEST` Phase A, `LINT`) is one sub-agent; a batching step is N, **~8–10 rows or countries each**, never one per country. The parent reads the list's row count (`wc -l`) and nothing else. **Each batch gets its own suffix for every per-run file the sweep writes, never for a sweep's persistent high-water state** (`state.json`). **That state is the parent's to write, never a slice's**: slices return their counts, and the parent advances `state.json` and appends `seen.csv` once they all have — a file no slice may suffix is otherwise a file every slice writes whole, and the last writer wins. At most **20 running at once**.

### Why the parent owns the spawn

**No sub-agent spawns another**; the parent counts every spawn it makes, because only the parent can see them. Every spawn is synchronous in ordering; never a background agent, never `SendMessage`.

**The parent never ends a turn on a waiting line.** It holds the turn while a spawn is outstanding (`Monitor` with an until-loop on the agent's output, or the next independent item on the day's list). If a turn must end with work outstanding, its last line is `outstanding: <step> · resumes on its own · no input needed`.

**No sub-agent may stall on a permission prompt**: `.claude/settings.json` (git-tracked) sets `permissions.defaultMode` to `bypassPermissions` and denies `AskUserQuestion`.

### Model

**Screening runs on Sonnet; everything else runs on Opus** *(Bill, 2026-09-18, strategic review 4 R21, on R20's trial — 480 screened, all 312 drops re-screened, 0 false drops; supersedes the 2026-09-08 everything-on-Opus rule, which itself removed a tiered policy)*. Start the session on `--model opus`: the parent, `INGEST`, `LINT`, reconcile, acquire, the compiles, housekeeping and rules all inherit it. **The sweep-stage batches name `sonnet` on the spawn, and they are the only spawns that name a model at all** — the daily and off-list sweeps and the day's jobs, the steps that screen candidates and stage into `new/`. Nothing downstream of `new/` changes model: ingest is where value is judged, and it is the expensive stage.

**The model attaches to the night, not to the lane.** Every screening batch a night runs takes the same model, so the night's `usage` block measures one thing and a stage-cost table can read it.

**Day 2 runs its next night on Opus, and every night after that on Sonnet** *(Bill, 2026-09-18)*: the night is due anyway, so one heavy schema-2 night on Opus buys a sweep-stage figure to compare against at no extra cost. The test is the row's own `Start`, so nothing has to be remembered — **Day 2 screens on Opus while its `Start` is earlier than 2026-09-19, and on Sonnet once it is not.** Day 1 screens on Sonnet from tonight.

### The screening monitor — one rotation, then it goes

**On every night whose screening ran on Sonnet, one Opus sub-agent re-screens one batch's drop log**, after the sweeps have all returned and before the sweep commit. Take the **largest drop log** that night's batches wrote, capped at **30 rows**: this is a standing check, not a second trial. Hand it that batch's own window — the daily and off-list lanes run on their own high-water mark, not the cycle window, and the wrong window makes a re-screen more permissive than the screen and so measures nothing. It returns `false_drops=N` and the rows.

**A false drop is a finding**: the item is staged and the finding goes in the sweep commit's body. A zero goes in the commit body too, in a clause.

**It retires when three consecutive Sonnet nights return `false_drops=0`**, at the hands of the rules pass on the night of the third, which deletes this subsection. A night that finds one restarts the count. **The count is read from the sweep commits' bodies** — no register, no state file. Day 2's Opus night runs no monitor and counts neither way.

### No budget, no cost report

**No step checks a budget, no step is stopped by one, and the night's cost is neither measured nor reported** *(Bill, 2026-09-08 — the 90-sub-agent brake, its `--nobrake` override and the run-cost line all removed; `scripts/budget-check.py` and `scripts/run-cost.py` are deleted)*. The night runs the day it selected to its close and reports the standing tally line (`STATUS.md`).

### Usage log

**`python scripts/usage-log.py`, twice a night into the CSV: the first act, before draining notes, and after the night's last commit, before the cycle manifest** *(Bill, 2026-09-13)*. **And at every stage boundary in between, into a buffer the manifest reads** *(Bill, 2026-09-17, strategic review 4 R4 — amending "nothing reads it back" for the buffer only)*: `usage-log.py --stage <name>` straight after each stage's commit, or where the commit would be when the stage commits nothing, named for the stage (`notes`, `sweep`, `ingest`, `lint`, `close`, `backlog`, `rules`). The first act is `--reset --stage start --csv` and the last `--stage end --csv`, so each is one reading serving both. `cycle-manifest.py --usage` writes the buffer as the manifest's `usage` block, keyed by stage, and a stage's cost is its reading less the one before it. It inserts `Date`, `Time (UTC)`, `7d usage` and `Session usage` — the weekly plan limit used, and its rise since the row below, as percentages — at the top of `logs/usage-log.csv`, newest first — a record, not a budget: nothing reads it back, nothing is stopped by it, and it goes on no closing line. It never fails the night; an unreadable figure is written `n/a`. The closing row lands after the last commit, so it rides the next night's first commit — the mirror carries it either way. The buffer, `logs/usage-stages.jsonl`, is git-ignored.

### What every sub-agent prompt carries

**Pasted verbatim, never paraphrased or summarised**, and the containment line **names exact files, never a bare folder** — a boundary stated loosely is a boundary a slice reads generously.

- **[`wiki/capture-rule.md`](wiki/capture-rule.md), baked in**, with *never read a feed whole*.
- **The containment boundary** (`intake.md` §7): a sweep writes **only** to `new/` and its own `sweep/`; never `raw/`, never a wiki page, not even to reformat.
- **A discard is a drop: logged and counted, every time.** An in-window item put aside as already-held, already-seen or a sibling's catch is a drop — **one row in this batch's own drop log** under the closest code in `intake.md` §7, and counted in `dropped=N`. Returning `dropped=0` and writing no row is the silent discard §7 forbids: it understates the denominator every screening measurement rests on, and it hides the one class of adjudication a re-screen can check most cheaply.
- **A drop on the item's own merits also goes into the URL log, so no other lane and no later night fetches it again.** At the drop, write the URL with `python scripts/url-log-append.py dropped URL`. That covers `off-topic`, `off-place`, `inadmissible-origin`, `no-development`, `headline-only-stub`, `already-held`, `syndicated-copy` and `fails-record-test`. Every sweep's pre-fetch filter already reads `logs/sweep-url_log.md`, but a drop that lives only in one sweep's drop-log is invisible to every other lane and to the next night's boundary day, so the same trade-press accounts get fetched and screened again. **Codes that are not a verdict on the item stay out of the log**: `out-of-window`, `not-this-slice`, `url-dead`, `fetch-blocked` and `date-unestablished` may be right for a different lane or a later night, and a `dropped` line would bury them. `already-seen` and `duplicate-in-run` are already covered. The appender takes a lock, so parallel slices call it directly.
- **`logs/log.md` only through `scripts/log-append.py`**, and **`logs/log.md` and `reviews/rule-candidates.md` are the parent's to write** — a slice flags them in its return. The parent corrects a nested line with `--at` (UTC) against its own measurement.
- **Runs a process, never amends one, and runs no git command that writes**: no edit to a root process file, `CLAUDE.md` or `wiki/reference.md`; no commit, add, checkout, restore or reset; **and no tree-wide git command at all** — `stash`, `reset`, `checkout`, `clean` — because a slice cannot see what its siblings hold uncommitted. A rule change returns as a recommendation the parent applies; `assert-containment.py` enforces this (§ *Commit at boundaries*).
- **Spawns nothing**: no `Agent` tool, no sub-agent of its own. A general-purpose agent carries every tool unless told otherwise.
- **Writes each file back with the line endings it already had, and tests it with a byte count** — read the file's own convention and preserve it; never normalise to LF or CRLF, and never assume a corpus-wide convention, because both directions have been "corrected" wrongly. **The test is `python -c "b=open(PATH,'rb').read(); print('CRLF' if b.count(b'\r\n') else 'LF')"`, never a shell grep for a carriage return**, which reports CRLF on an LF file. A file's own convention is what `git show HEAD:<path>` holds, not what the tree happens to carry mid-run. **A missing final newline is not a convention** — add one.
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
usage-log.py --reset --stage start --csv            # first act of the night; see § Usage log
drain X:\notes-for-osint.md — act on every open note, close to -resolved (X:\README.md -> Conventions)
assert-containment.py --stage notes [--allow-extra <path> ...] ; git commit  # only if this repo changed
usage-log.py --stage notes                          # and after every stage boundary below, named for it
pull-new-queue.py --apply                           # X:\new-queue\ READY folders into new/; see § Pulling X:\new-queue\

Exa canary — on failure skip every line marked [exa] below; the rest of the night runs
arm stall-watch.py under Monitor, all night
select day D: Skip, then oldest Start (blank sorts oldest); New-Start = now        [exa]
window from D's (old) Start                                                        [exa]

SWEEP-DAILY-LIST, SWEEP-DAILY-OFFLIST              stage-only, batched             [exa]
D's unprefixed Jobs, in order                      stage-only, batched; unbuilt -> "Day D: <NAME> not built" in logs/log.md   [exa]
screening monitor: one Opus re-screen of one Sonnet batch's drops, <=30 rows       # see § The screening monitor
assert-containment.py --stage sweep ; git commit ; usage-log.py --stage sweep

INGEST Phase A, once, lean form, both lanes open   compile-hubs.py and FINANCE-COMPILE fire from it, scoped
cycle-manifest.py --stamp                           parent-measured sweep_closed/ingest_started; see below   [exa]
assert-containment.py --stage ingest ; git commit ; usage-log.py --stage ingest

D's @-prefixed Jobs, in order                                                     [exa]
quick lint ; RECONCILE if open/ has items [exa] ; ACQUIRE if acquisitions.md has open lines [exa]
WIKI-SYNC Phase B if logs/ingest-pending-writes.md is non-empty
full lint's batched checks                          # every night; see § The nightly close
assert-containment.py --stage lint ; git commit ; usage-log.py --stage lint

status-acquire.py --absorb                          # any pulled status-acquire batch; see § Absorbing a status-acquire batch
prune sweep-url_log.md before D's (old) Start (skip if blank) [exa] ; rotate-log.py --apply
close D: Prev Duration = Duration; Duration = now - New-Start (H:MM); Start = New-Start; End = now; clear New-Start   [exa]
assert-containment.py --stage close --allow-extra lookups/rejected-urls.csv ; git commit ; usage-log.py --stage close

── every night, after the close ──
mirror to O:\
BACKLOG.md — one housekeeping job, oldest first; prepared work on X:\prepared\ applied first
assert-containment.py --stage housekeeping [--allow-extra <path> ...] ; git commit ; usage-log.py --stage backlog
rules: drain reviews/rule-candidates.md — RULES.md, the parent's own work, no sub-agent
assert-containment.py --stage rules [--allow-extra <each process file amended>] ; git commit ; usage-log.py --stage rules

── every night ──
reader-visible change tonight? -> draft entries into X:\notes-for-corpus.md, titled "Add to change log"
usage-log.py --stage end --csv                      # after the night’s LAST commit, whichever it is
cycle-manifest.py --pass "sweep cycle" --usage --count ... --count screened=N --count screen_dropped=N
git push ; mirror to O:\
export-process-mirror.py  # after the push; a refusal goes on the closing line and never blocks
```

## The cycle manifest

**`python scripts/cycle-manifest.py --pass "sweep cycle" --usage --count items_in=N --count admitted=N --count dropped=N --count screened=N --count screen_dropped=N`, after the night’s last commit — the rules commit, or the housekeeping commit if the rules queue is empty — and before the last mirror.** It writes `cycle-manifest.json` at the repo root, and that file is the whole of what CORPUS reads about a run: the commit the mirror carries, the collection window, the rotation's newest close, and the counts this pass measured. It is git-ignored and written after the commit on purpose — `head` has to name the commit that is actually on `O:\`, which a file committed inside that commit cannot do. **Counts are passed in, never inferred**: a pass that measured none writes none, because an absent count is visible and a wrong one is not. **`screened` and `screen_dropped` measure the sweeps' own screen, upstream of `new/`**, where `items_in`/`admitted`/`dropped` measure ingest: the parent sums them from the one-line returns (§ *What a sub-agent returns*) of every sweep step the night ran — the daily and off-list sweeps and D's unprefixed jobs, every batch, the final return of a re-spawned step — as `screened = staged + dropped + needs-clip` and `screen_dropped = dropped`. A night that ran no sweep (a canary failure) writes neither. They sit in `counts`, so the schema does not change *(strategic review 4 R3–R4, register R06, 2026-09-17: the denominator the screening trial needs)*. Lint #19 asserts that the manifest on the mirror names the mirror's own HEAD.

## Mirror

**The night's last act, after the final commit: `"C:\Program Files\FreeFileSync\FreeFileSync.exe" SyncSettings.ffs_batch`**, a one-way mirror of `C:\OSINT` to `O:\` (`\\bill-vivobook\osint`), `.git` included, deletions propagated. **`O:\` is CORPUS's read-only copy of this vault, not a backup.** A failed mirror is re-run by hand.

**Assert on `git -C O:\ rev-parse HEAD` matching local, never on stdout**, and only **after the `FreeFileSync` processes exit**; the newest HTML log under `%APPDATA%\FreeFileSync\Logs\` is the second instrument. The same check is `LINT` #19 (`scripts/lint-mirror-head.py`), surface-only; `--gate` stops on it.

## The change log

**A change a reader of the published site could notice is drafted here as a change-log entry and sent to CORPUS as a note titled *Add to change log*** *(Bill, 2026-09-17)*. CORPUS publishes the log and writes its own entries; only this side knows when one of ours has happened, so nobody else can draft them.

**What earns one**: a new sweep list, source type or country coverage; a taxonomy or lookup change; a correction reaching many records; records struck or re-dated in bulk. **What does not**: routine sweeping and ingest, and internal process changes. Most nights earn nothing, and a night that drafts none says nothing rather than saying there was no change.

**The entry's shape is CORPUS's, not restated here** — `X:\README.md` → *Conventions* governs the note, and `notes-for-corpus` 29 is the worked example. CORPUS adds the entries as sent, editing only for length and house style.

## The process mirror

**After the final push and mirror: `python scripts/export-process-mirror.py`.** It copies the process layer — root procedures, `scripts/`, `documentation/`, the vocabulary lookups and the thirteen `wiki/` specs, on the allowlist in the script — from `HEAD` to the public repository `data-landscapers/osint-process` (checkout `..\osint-process`, cloned if absent) and pushes. It has nothing to do with `O:\`: this is what lets anyone read how the vault is built without reading the vault. `raw/`, the compiled wiki, `logs/` and `reviews/` never go.

**A refusal is not a failure of the night.** The script refuses on a markdown block quote over 200 characters or a secret, and reports any new root file, lookup or `wiki/` spec as *unclassified*. Put the line on the closing line; the ruling — acknowledge the quote's hash in `REVIEWED_QUOTES`, or add the path to `PUBLISH` or `WITHHELD` — is a housekeeping or rules act, never a sub-agent's. No change to a published file means no commit. LINT #37 catches an export that did not land.

## The nightly close

**Every night closes with full lint's whole-vault checks, then one housekeeping job (`BACKLOG.md`), then the rules pass (`RULES.md`), in that order, with rules last** *(Bill, 2026-09-24; these three used to run only on the rotation's Day B row, which is retired)*. They run on a night the Exa canary fails too, since none of the three needs Exa. Full lint sits in the lint stage, before the close commit; housekeeping and rules come after the close and the first mirror.

## Housekeeping, every night

**Runs `BACKLOG.md`, once, after the first mirror** — one housekeeping job, oldest first, with any work CORPUS prepared on `X:\prepared\` applied first. Selection, sizing, the slice, closing an entry and the commit boundary (`assert-containment.py --stage housekeeping`) are that file's, not this one's.

## Rules, the night's last act

**`RULES.md` over the whole of `reviews/rule-candidates.md`, after housekeeping and after nothing.** It is last because every other pass reads the rules it writes: a rule that changes with a step still to come leaves that step working to a different file from the ones before it, which is the mid-run rule change `CLAUDE.md` forbids. At the end of the night there is no such step, so the objection is spent — and the queue drains every night rather than waiting on somebody to notice it.

**The parent's own work, never a sub-agent**: a spawned agent runs a process and does not amend one, and this is the pass that amends them.

**`assert-containment.py --stage rules` names every process file it touched with `--allow-extra`** — the deny set still stands, so the exception is per file and the night's log line lists exactly which rules changed. An empty queue: skip, say `no rule candidates` on the closing line, which is the ordinary state of a good week.

**Then the every-night tail: the manifest, `usage-log.py`, push and mirror** — the only push in this file, covering housekeeping and rules together, so a same-night change reaches GitHub and `O:\` before tomorrow's mirror rather than waiting on it.

## Pulling X:\new-queue\

**After the notes commit, before the Exa canary — unconditional, and it runs on a canary failure too**: `python scripts/pull-new-queue.py --apply`. It moves every `X:\new-queue\` folder that carries a `READY` file flat into `new/`, gives a backfill-prefixed folder's candidates their `sweep_batch:` where they carry none, and leaves a `delivered-YYYY-MM-DD` marker in the emptied folder *(Bill, 2026-09-17, strategic review 4 R8 — the hand-carry retires)*. A folder without `READY` is still being written and is left; a name already in `new/` is left in the queue and retried the next night. The script's docstring holds the rules. **Delivery is not admission**: the night's one `INGEST` Phase A pass adjudicates the pulled items with everything else, **with the backfill lane open** (`INGEST.md` → *Two lanes*), so `status-acquire-`, `progress-filler-` and `dataset-` batches take it and every other item — sweeps' catch and any other producer's folder — stays news. Commits nothing of its own: the files ride the sweep and ingest commits (`new/` is in both write-sets), and the queue's deletions on `X:\` are CORPUS's to commit.

## Absorbing a status-acquire batch

**At the close, before the log prune — unconditional**: `python scripts/status-acquire.py --absorb`. CORPUS screens, fetches and stages a country's `X:\africa-acquire.csv` rows and leaves its drop list on `X:\prepared\status-acquire-{ISO3}-drops.csv`; this closes the country's rows into `X:\acquire-done.csv` and writes the permanent negatives to `lookups/rejected-urls.csv` — which is why the close's containment check carries `--allow-extra lookups/rejected-urls.csv`, a no-op on a night that absorbed nothing. **A country is due once its batch folder no longer carries `READY`**, so the absorb lands on the night that pulled it and never before. `STATUS-ACQUIRE.md` holds the classes and the by-hand repair; the ingest is the night's own Phase A, in the backfill lane, like any other pulled batch. A night that absorbed something writes one `logs/log.md` line; a night that did not writes none.

## Draining notes-for-osint

**First act of the night, before the Exa canary — unconditional, and it runs even on a canary failure.** Read every open note in `X:\notes-for-osint.md`; act on each and close it. `X:\README.md` → *Conventions* holds the rules this pass follows, not a copy of them here: the bar for writing a note, what closing means (full text and every dated annotation carried to `X:\notes-for-osint-resolved.md`, nothing left behind, numbers never reused), and that a note carrying its own fix is a task — do it and log it. A note that only raises a question the writer could have answered stays open, for CORPUS.

**Writes to `X:\`, commits nothing there** — `X:\README.md` → *Conventions*: CORPUS does the committing on that share, OSINT writes and stops.

**Commits whatever it changed in `C:\OSINT`, its own boundary before the four below.** A note's fix routinely reaches this repo — a script, a wiki page, a process file — and that is committed here, not folded into `sweep`, `ingest`, `lint` or `close`, whose write-sets it may not fit. `python scripts/assert-containment.py --stage notes` (write-set `*`) governs it; the absolute deny set still applies, so a fix landing on `CLAUDE.md`, a `wiki/` spec or another root procedure takes `--allow-extra <path>` per file, named in the log line, exactly as the parent already does at any other stage. Skip the commit if nothing in this repo changed — a run that only touched `X:\` has nothing to commit here.

## Step 0 — the Exa canary

**First act, before selecting a day or writing anything**: one `web_search_exa`, `"data protection Africa"`, `numResults: 1`.

**On failure (error, exception, empty result set, absent connector) the collecting half of the night does not run — the processing half does** *(Bill, 2026-09-08)*. The canary proves the instrument, so what it gates is every pass that reaches outside the vault, and nothing else. **No fallback tool and no reduced sweep**: a sweep that cannot search does not run at all, because a nil it reports would be its own blindness rather than evidence of a quiet day.

- **Does not run**: every sweep, the day's jobs, `RECONCILE` (its research step is Exa) and `ACQUIRE` (its one attempt and its gap probe are Exa). Their queues stand.
- **Runs as normal**: `INGEST` Phase A over whatever is already in `new/` — a primary it cannot download becomes an acquisition line, which is step 8's ordinary path — then `WIKI-SYNC` Phase B, the compiles, quick lint, `PRUNE`, the commits and the mirror. So do full lint, `BACKLOG` and rules (§ *The nightly close*). None of them touches the network, and the vault's own work does not depend on tonight's weather.
- **The rotation does not move**: select no day, write no `New-Start`, close no day. The day's collection is what did not happen, so the day is still due.
- **No `cycle-manifest.py --stamp`**: nothing was collected, so there is no window to stamp, and the manifest carries the last real one forward. The manifest itself is still written after the final commit — it must name the commit the mirror carries (lint #19).

Write the fatal line: `**SWEEP-CYCLE** · FATAL: Exa canary <the error> — sweeps skipped, processing ran`.

**Every sweep runs `wiki/origin-screen.md` itself**; ingest is the only door (lint #17). **Sweeps run stage-only**, into `new/`. **Lint runs only here** (`WIKI-SYNC.md` never lints): **quick lint every night**, `LINT.md`'s nightly bands **plus the incremental checks (#6, #4, #5, #14, #20, #7) over the records this run admitted**; **full lint's whole-vault batched checks run every night**, at the close (§ *The nightly close*).

## Reconcile and acquire

At the close, each **only if its queue has items**: `RECONCILE` for `reviews/contradictions/open/`, `ACQUIRE` for open lines in `reviews/acquisitions.md`, **`WIKI-SYNC` Phase B for `logs/ingest-pending-writes.md`**. Their write-set is inside the `lint` stage's. **If reconcile or acquire staged anything to `new/`, an `INGEST` Phase A over exactly that catch runs before Phase B and quick lint.** Both passes cite the primaries they stage, and the night's one ingest has already run, so without this the night closes on citations that resolve to nothing in `raw/`. That Phase A's `--stamp` carries the night's own `--sweep-closed` and `--ingest-started` unchanged, so only `last_admission` moves. **`REPORT-LINT`'s checks A–F do not run here**; `FINANCE-COMPILE.md`'s closing step runs them whenever ingest admits a finance record.

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
