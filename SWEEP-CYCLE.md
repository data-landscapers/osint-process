<!-- reader: cc; type: runbook -->
# SWEEP-CYCLE.md — the nightly sweep orchestrator

Trigger: **"run the sweep cycle"**, typed by hand; **no scheduled trigger exists or is planned.** Each run works **one numbered day** from the rotation in `logs/sweep-cycle_log.md`; **no step checks a clock.** This file is **only the wiring**; the rules live in the processes it calls (every sweep screens origins against [`wiki/origin-screen.md`](wiki/origin-screen.md) itself, lint #17), and the reasoning in `wiki/sweep-cycle-notes.md`.

## Execution model

One CC run; the parent is a **thin loop** — it selects the day, runs its processes one at a time, holds only the tallies they return and keeps the log. It reads this file and the cycle log, never a delegated process file and never a body (`ls new/` for a count, never `cat`).

### Why the parent owns the spawn

**One level of sub-agent; the parent owns every spawn**, synchronously, never a background agent or `SendMessage`. A non-batching step (`INGEST` Phase A, `LINT`) is one sub-agent; a batching step is N, **~8–10 rows or countries each**, at most **20 running at once**. Each batch suffixes every per-run file it writes; **a sweep's persistent state (`state.json`, `seen.csv`) is the parent's to write** once all batches return.

**The parent never ends a turn on a waiting line**: it holds the turn while a spawn is outstanding (`Monitor` on the agent's output), or ends on `outstanding: <step> · resumes on its own · no input needed`. `.claude/settings.json` sets `bypassPermissions` and denies `AskUserQuestion`, so no spawn stalls on a prompt.

### Model

**Screening runs on Sonnet; everything else on Opus** *(Bill, 2026-09-18)*. Start the session on `--model opus`; **the sweep-stage batches name `sonnet` on the spawn and are the only spawns that name a model.** Every screening batch a night runs takes the same model.

### The screening monitor — until it retires

**On every Sonnet-screened night, one Opus sub-agent re-screens the largest drop log the night's batches wrote**, capped at **30 rows**, in that batch's own window, after the sweeps return and before the sweep commit. It returns `false_drops=N`: a false drop is staged, and the count, zero included, goes in the sweep commit's body. **It retires after three consecutive Sonnet nights with `false_drops=0`** — the rules pass deletes this subsection on the third night; a finding restarts the count, read from the sweep commits' bodies.

### Budget and usage

**No step checks a budget and the night's cost is neither measured nor reported** *(Bill, 2026-09-08)*. `python scripts/usage-log.py` writes the plan's usage percentages: `--reset --stage start --csv` first, `--stage <name>` after each stage boundary into a git-ignored buffer the manifest reads, `--stage end --csv` after the last commit. It never fails the night.

### What every sub-agent prompt carries

**A slice's brief is its template pasted verbatim** — [`wiki/brief-sweep.md`](wiki/brief-sweep.md) or [`wiki/brief-ingest.md`](wiki/brief-ingest.md) — under a few lines of the night's own facts: for a sweep the window, the high-water mark and **`python scripts/drop-digest.py`'s output**; for ingest the lane, iteration, list directory, sibling count and origin tally. **A rule a slice needs goes into its template, never into a night's copy.**

**`python scripts/stall-watch.py --quiet-minutes 25`**, armed under `Monitor` at step 0 and left all night: on waking, if the outstanding step has not moved, **kill that spawn and re-spawn it once**.

**A sub-agent returns one line**: `step=<name> stopped=<complete|context|error> staged=N dropped=N needs-clip=N remaining=N notes=<≤10 words>`. `context` with `remaining=N` means re-spawn; a broken instrument is `stopped=error`, never a clean nil; **an `error` step is re-spawned once** before it is recorded.

## Commit at boundaries

**Commit at each stage boundary, never once at the end**, each preceded by `python scripts/assert-containment.py --stage <stage>`, never piped (its exit code gates) — exit 1 means do not commit; `--allow-extra <path>` commits outside a stage's set and is named in the log line. **`python scripts/stage-check.py --apply` runs over `new/` before the sweep commit**; what it reports and cannot fix, the parent fixes where the record shows the answer or leaves for ingest — a finding never holds the night.

```
usage-log.py --reset --stage start --csv
drain X:\notes-for-osint.md                         # § Draining notes-for-osint
assert-containment.py --stage notes ; git commit ; usage-log.py --stage notes   # only if this repo changed
pull-new-queue.py --apply                           # § Pulling X:\new-queue\

Exa canary — on failure skip every line marked [exa]; the rest of the night runs
arm stall-watch.py under Monitor, all night
select day D; New-Start = now                                                      [exa]
window from D's (old) Start                                                        [exa]

SWEEP-DAILY-LIST, SWEEP-DAILY-OFFLIST              stage-only, batched, sonnet     [exa]
D's unprefixed Jobs, in order                      stage-only, batched, sonnet; unbuilt -> "Day D: <NAME> not built" in logs/log.md   [exa]
screening monitor                                   # Opus, <=30 rows, until retired
stage-check.py --apply
assert-containment.py --stage sweep ; git commit ; usage-log.py --stage sweep

INGEST Phase A, once, lean form, both lanes open   compile-hubs.py and FINANCE-COMPILE fire from it, scoped
cycle-manifest.py --stamp                           parent-measured sweep_closed/ingest_started   [exa]
assert-containment.py --stage ingest ; git commit ; usage-log.py --stage ingest

D's @-prefixed Jobs, in order                                                     [exa]
quick lint ; RECONCILE if open/ has items [exa] ; ACQUIRE if acquisitions.md has open lines [exa]
INGEST Phase A over any catch reconcile/acquire staged, before Phase B
WIKI-SYNC Phase B if logs/ingest-pending-writes.md is non-empty
full lint's batched checks
assert-containment.py --stage lint ; git commit ; usage-log.py --stage lint

status-acquire.py --absorb                          # any pulled status-acquire batch
prune sweep-url_log.md before D's (old) Start (skip if blank) [exa] ; rotate-log.py --apply
close D: Prev Duration = Duration; Duration = now - New-Start (H:MM); Start = New-Start; End = now; clear New-Start   [exa]
assert-containment.py --stage close --allow-extra lookups/rejected-urls.csv ; git commit ; usage-log.py --stage close

mirror to O:\
BACKLOG.md — one housekeeping job, oldest first; X:\prepared\ work applied first
assert-containment.py --stage housekeeping ; git commit ; usage-log.py --stage backlog
RULES.md over reviews/rule-candidates.md — the parent's own work, no sub-agent
assert-containment.py --stage rules --allow-extra <each process file amended> ; git commit ; usage-log.py --stage rules

reader-visible change tonight? -> "Add to change log" note in X:\notes-for-corpus.md
usage-log.py --stage end --csv                      # after the night's LAST commit
cycle-manifest.py --pass "sweep cycle" --usage --drops --hygiene --count items_in=N --count admitted=N --count dropped=N --count screened=N --count screen_dropped=N --count pages_over_line=N
git push ; mirror to O:\
export-process-mirror.py                            # a refusal goes on the closing line, never blocks
```

## Step 0 — the Exa canary

**First act after the notes and the queue pull**: one `web_search_exa`, `"data protection Africa"`, `numResults: 1`. **On failure the collecting half does not run and the processing half does** *(Bill, 2026-09-08)*: no sweep, no day's job, no `RECONCILE`, no `ACQUIRE`; ingest over what `new/` holds, Phase B, the compiles, both lints, `BACKLOG`, rules, the commits and the mirror all run. **No fallback tool and no reduced sweep. The rotation does not move and there is no `--stamp`.** The fatal line: `**SWEEP-CYCLE** · FATAL: Exa canary <the error> — sweeps skipped, processing ran`.

## Draining notes-for-osint, pulling the queue, absorbing

**Notes first, unconditional**: act on and close every open note in `X:\notes-for-osint.md` under `X:\README.md` → *Conventions*; write to `X:\` and commit nothing there. A fix reaching this repo commits at the `notes` boundary (write-set `*`, the deny set still standing).

**`python scripts/pull-new-queue.py --apply`, unconditional**: every `X:\new-queue\` folder carrying `READY` moves flat into `new/`; delivery is not admission — the night's one Phase A adjudicates it, backfill lane open for the whitelisted batches. It commits nothing of its own.

**`python scripts/status-acquire.py --absorb` at the close, unconditional**: closes a pulled country's rows into `X:\acquire-done.csv` and writes permanent negatives to `lookups/rejected-urls.csv` (hence the close's `--allow-extra`). `STATUS-ACQUIRE.md` holds the rest.

## Ingest, once, at the close

**One `INGEST` Phase A pass drains the whole night's catch**, lean form; volume is handled by its own slicing, never by splitting the pass. **The parent measures the window**: `sweep_closed` is the **sweep-stage commit**, `ingest_started` the **first Phase A slice's spawn**, stamped with `cycle-manifest.py --stamp` at ingest's close. A catch reconcile or acquire staged is ingested before Phase B with the same two values, so only `last_admission` moves. **A close that skips `--stamp` is a defect**: CORPUS bylines from it with no fall-back.

## Reconcile and acquire

**Lint runs only here.** **Quick lint every night** — `LINT.md`'s nightly bands plus the incremental checks over the records this run admitted; **full lint's batched checks every night** at the close. `RECONCILE`, `ACQUIRE` and `WIKI-SYNC` Phase B each run **only if their queue has items**, inside the lint stage's write-set. `REPORT-LINT` does not run here.

## The nightly close

**Full lint, then one housekeeping job (`BACKLOG.md`), then the rules pass (`RULES.md`), with rules last** — every other pass reads the rules it writes, so none may run after it. All three run on a canary failure. An empty candidate queue says `no rule candidates` on the closing line. **The tail — change-log note, manifest, `usage-log.py`, push, mirror, process export — is the only push in this file.**

## The cycle manifest

**`cycle-manifest.py --pass "sweep cycle" …` after the night's last commit and before the last mirror** writes `cycle-manifest.json`, the whole of what CORPUS reads about a run: the commit on `O:\`, the collection window, the rotation's newest close and the night's counts. **Counts are passed in, never inferred**: `items_in`/`admitted`/`dropped` from ingest; `screened` (staged + dropped + needs-clip) and `screen_dropped` summed from every sweep step's return; `pages_over_line` from full lint #8. `--drops` adds drops per sweep per code and the ingest drop rate; `--hygiene` jobs registered and words trimmed since the last manifest (`wiki/sweep-cycle-notes.md` → *The manifest*).

## Mirror

`"C:\Program Files\FreeFileSync\FreeFileSync.exe" SyncSettings.ffs_batch`, a one-way copy of `C:\OSINT` to `O:\` — **CORPUS's read-only copy, not a backup**. Assert with `python scripts/lint-mirror-head.py`, never on stdout, after FreeFileSync exits; a failed mirror is re-run by hand.

## The change log

A change a site reader could notice — a new sweep list, source type or country, a taxonomy change, a bulk correction — goes to CORPUS as a note titled *Add to change log*. Routine sweeping and ingest earn nothing.

## The process mirror

`python scripts/export-process-mirror.py` after the final push copies the process layer to `data-landscapers/osint-process`. **A refusal goes on the closing line and never fails the night**; its ruling is a housekeeping or rules act. LINT #37 catches an export that did not land.

## The cycle log

`logs/sweep-cycle_log.md` is boss: its header defines the columns, `Skip`, the `@` prefix and duration ageing. **Selection**: oldest `Start`, blank counting oldest and two blanks tie-breaking on the lower `Day`; a `Skip` row passes to the next-oldest, `Start` untouched, named on the closing line. **No row due**: run the common prefix and the close, and say `no day due`.

**Window**: `window_start = D's (old) Start − 1 day`, `window_end = today`; a blank old `Start` gives `today − one rotation`. The daily and off-list sweeps keep their own high-water state. `Start` advances only at the close, so a re-run sweeps the same window.

**A day whose jobs are all unbuilt, or all `error` after their one re-spawn, does not close**: leave `Start`, `Duration` and `Prev Duration` unadvanced and say why on the closing line. **A populated `New-Start` is the interrupted-run signal**: the day re-runs from scratch.

## Concurrency and logging

One cycle at a time, no other session writing the vault. Each process writes its own `logs/log.md` line; the cycle adds one closing line and closes on screen with `STATUS.md`'s count line.
