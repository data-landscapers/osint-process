<!-- reader: cc; type: spec -->
# sweep-cycle-notes.md — why the sweep cycle is wired as it is

*(The reasoning and finer detail behind `SWEEP-CYCLE.md`, which keeps the wiring. By the runbook's own headings.)*

## Why the parent owns the spawn

Only the parent can see every spawn, so only the parent can count them. A slice that spawned its own would put work outside anything the night can account for. A file no slice may suffix, a sweep's `state.json` or `seen.csv`, is otherwise a file every slice writes whole, and the last writer wins; hence the parent advances state once all batches have returned. A turn that ends on a waiting line hands the night to a human who is not there.

## Model

The 2026-09-18 trial screened 480 candidates on Sonnet and re-screened all 312 drops on Opus: no false drops. So screening moved to Sonnet, and nothing downstream of `new/` changed model: ingest is where value is judged, and it is the expensive stage. The model attaches to the night, not the lane, so the night's `usage` block measures one thing and a stage-cost table can read it. Day 2 ran one more night on Opus, while its `Start` was before 2026-09-19, to give a sweep-stage figure to compare against; that clause is spent and was removed on 2026-09-25.

## The screening monitor

A standing check, not a second trial, hence the 30-row cap. It re-screens in the batch's own window: the daily and off-list lanes run on their own high-water mark, and the wrong window makes a re-screen more permissive than the screen, so it measures nothing. The retirement count lives in the sweep commits' bodies, so it needs no register or state file.

## Budget and usage

The 90-sub-agent brake, its override and the run-cost line were removed on 2026-09-08; `budget-check.py` and `run-cost.py` are deleted. `usage-log.py` inserts `Date`, `Time (UTC)`, `7d usage` and `Session usage` (the weekly plan limit used and its rise since the row below) at the top of `logs/usage-log.csv`. It is a record, not a budget: nothing reads the CSV back and nothing is stopped by it. The per-stage buffer, `logs/usage-stages.jsonl`, is what the manifest's `usage` block reads; a stage's cost is its reading less the one before. An unreadable figure is written `n/a`. The closing row lands after the last commit and rides the next night's first commit.

## What every sub-agent prompt carries

The parent used to write the briefs each night, from memory and the night before's copy, and they reached 2,109 and 1,251 words carrying incident histories forward. As templates they are capped by lint #41, and a rule changes in one file.

## Step 0 — the Exa canary

The canary proves the instrument, so it gates every pass that reaches outside the vault and nothing else. There is no fallback because a sweep that cannot search would report a nil that is its own blindness, not evidence of a quiet day. The rotation does not move because the day's collection is what did not happen, so the day is still due; the manifest is still written after the final commit, carrying the last real collection window forward.

## Draining notes, pulling the queue, absorbing

Notes go first because a note's fix can bear on anything the night does. A note that only raises a question its writer could have answered stays open for CORPUS. A fix landing on `CLAUDE.md`, a `wiki/` spec or a root procedure takes `--allow-extra` per file.

`pull-new-queue.py` gives a backfill-prefixed folder's candidates their `sweep_batch:` where they carry none, and deletes a folder once all its files are in `new/`. A folder without `READY` is still being written and is left alone; a name already in `new/` stays queued and is retried the next night. The queue's deletions on `X:\` are CORPUS's to commit. The backfill lane takes `status-acquire-`, `progress-filler-`, `dataset-` and `budget-poll-` batches; every other folder stays news. A `budget-poll-{ISO3}` folder is CORPUS's `budget-watch.py poll` output: companion and artefact, already screened against the URL and md5 indexes, admitted as `source_tier: budget-document` records.

A status-acquire country is due for absorbing once its batch folder no longer carries `READY`, so the absorb lands on the night that pulled it. A night that absorbed something writes one `logs/log.md` line.

## Ingest, once, at the close

`sweep_closed` is the sweep-stage commit because the staging sweeps have all returned, so nothing more could be caught. The `@`-prefixed jobs run after ingest and stage for the next night, so they never move it. CORPUS reads `collection.sweep_closed` with no fall-back (notes-for-osint 132): the rotation's close is no substitute, since its jobs finish hours after collection stops, and publishing that as *Last updated* would overstate coverage. `logs/sweep-url_log.md` is written per item at disposition, which is why every sweep also cross-checks `new/`.

## Reconcile and acquire

Both cite the primaries they stage, and the night's one ingest has already run, so without a second Phase A over their catch the night would close on citations resolving to nothing in `raw/`. `REPORT-LINT`'s checks A–F run from `FINANCE-COMPILE.md` whenever ingest admits a finance record.

## The nightly close

Full lint, housekeeping and rules used to run only on the rotation's Day B row, retired on 2026-09-24. Rules run last because every other pass reads the rules they write: a rule changing with a step still to come would leave that step working to a different file from the steps before it. The rules pass is the parent's own because a spawned agent runs a process and does not amend one.

## The cycle manifest

It is git-ignored and written after the last commit because `head` must name the commit actually on `O:\`, which a file committed inside that commit cannot do. Counts are passed in because a wrong count is invisible and an absent one is not. `screened` and `screen_dropped` sum every sweep step's return, including every batch and the final return of a re-spawned step; a canary-failure night writes neither. `pages_over_line` is written only on a night full lint ran. `--drops` counts drops per sweep per code from the sweeps' drop-logs and ingest's coded ones (schema 3, strategic review 5 R70); `--hygiene` measures the rise in the housekeeping register's `NEXT JOB NUMBER` and the words Phase B's over-line rewrites trimmed since the previous manifest (R83). Lint #19 asserts that the mirror's manifest names the mirror's HEAD.

## Mirror

`O:\` is `\\bill-vivobook\osint`, mirrored with `.git` and with deletions propagated. The second instrument is the newest HTML log under `%APPDATA%\FreeFileSync\Logs\`. Stdout proves nothing: a bare call has returned empty and copied nothing.

## The change log

CORPUS publishes the log and writes its own entries; only this side knows when one of ours has happened. The entry's shape is `X:\README.md`'s, and notes-for-corpus 29 is the worked example. A night that drafts none says nothing.

## The process mirror

It copies root procedures, `scripts/`, `documentation/`, the vocabulary lookups and the `wiki/` specs on the script's allowlist from `HEAD` to the public repository, through checkout `..\osint-process`. `raw/`, the compiled wiki, `logs/` and `reviews/` never go. It refuses on a markdown block quote over 200 characters or on a secret, and reports a new root file, lookup or spec as *unclassified*. The ruling on a refusal is `REVIEWED_QUOTES`, `PUBLISH` or `WITHHELD`. An unchanged published file means no commit.

## Concurrency

The cycle needs exclusive access to `new/`, `reviews/contradictions/open/` and `reviews/acquisitions.md`.
