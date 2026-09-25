<!-- reader: cc; type: runbook -->
# STATUS.md — read and show wiki status

Trigger: **"wiki status"** / **"display status"**. **Single source of truth** for the counts, the gates, the standing tally line, the one-line `log.md` entry form, the announce banner and the close report; no pass file redefines them.

**"wiki status"** *calculates*: `python scripts/status.py` runs the counts and gates below and **always writes the reading to `logs/status.md`**; `--fast` skips the uncited walk. **"display status"** *reads*: `cat logs/status.md`, nothing recomputed; the file's timestamp says how old it is. `logs/status.md` is git-ignored.

---

## The counts

- **awaiting ingest** — **every item in `new/`, whatever its extension**; exclude only dotfiles and any `README`: `ls -A new/ | grep -v '^\.' | grep -vi readme | wc -l`
- **contradictions** — files in `reviews/contradictions/open/`, **excluding the folder's `README.md`**: `ls reviews/contradictions/open/*.md 2>/dev/null | grep -vi readme | wc -l`
- **acquisitions** — **every list line under the one `## Open items` heading** of `reviews/acquisitions.md`, never by marker or URL: `awk '/^## Open items/{f=1;next} /^## /{f=0} f' reviews/acquisitions.md | grep -cE '^\s*[-*] '`
- **housekeeping** — unstruck numbered jobs in `X:\housekeeping-jobs.md` (a struck job carries an `x` prefix): `grep -cE '^[0-9]+\. ' /x/housekeeping-jobs.md`
- **rule-candidates** — open lines in `reviews/rule-candidates.md`, the queue `RULES.md` drains: `grep -cE '^- ' reviews/rule-candidates.md`. The pass runs as every night's last stage (`SWEEP-CYCLE.md`), so this reads as the **open** queue — cases still under three occurrences and under 21 days old — not as a backlog waiting on a trigger. **A number that climbs is a case recurring**, which is what it is there to show.
- **osint-notes** — open notes in `X:\notes-for-osint.md`, the CORPUS→OSINT queue. Both note files hold unresolved issues only (resolved ones move to the `-resolved` file), so every entry counts. **Both entry shapes count**, the bold lead `**N** (date) —` and the `### N. [TAG]` heading: `grep -cE '^(\*\*[0-9]+\*\*[ (]|#{2,3} [0-9]+[. ])' /x/notes-for-osint.md`
- **corpus-notes** — open notes in `X:\notes-for-corpus.md`, the OSINT→CORPUS queue; the **same** pattern: `grep -cE '^(\*\*[0-9]+\*\*[ (]|#{2,3} [0-9]+[. ])' /x/notes-for-corpus.md`
- **fetch** — unstruck lines in `X:\fetch-list.md`, documents **only Bill's browser** can get; same `x` convention: `grep -cE '^[0-9]+[a-z]?\. ' /x/fetch-list.md`
- **commits** — dirty paths in the working tree **after CC has committed its own work**: `git status --porcelain | wc -l`. **A job commits what it changed, as its last act**, in one commit naming what and why. What remains is inherited, or output CC will not commit unreviewed. **A file mixing CC's edits with another session's is committed, and the message says so.** Never commit another session's substantive output to tidy the number.

The commands are indicative; verify against the files if a count looks wrong.

**The count is the queue.** A binary artefact in `new/` (artefact + companion source page, `layout.md` §3) is **counted like any other item**.

## Gates — half-finished states no tally shows

**A queue counts work waiting to start; a gate marks a pass that stopped half-way.** Gates are reported **separately, in prose, never folded into the tally line**, and checked at the end of every job.

- **awaiting budget collect.** A `new-budget/{ISO3}/` folder means a collect batch stopped short, since `new-budget/` holds only `manifest.csv` at every stop: `find new-budget -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l`, cleared by `BUDGET-COLLECT.md` for that country. Off the standing tally line.
- **finance-compile baseline** — places whose finance records changed since the last compile: `python scripts/finance-compile-scope.py | wc -l`. Ingest fires the compile itself (`INGEST.md` → *Ending the run*), so this reads 0 on a healthy tree. `FINANCE-COMPILE.md` → *Close* advances the baseline with `finance-compile-scope.py --commit` only after the hubs are **committed**. A full-house scope means that step was skipped: repair the baseline, do not recompute every hub.
- **an interrupted sweep** — a sweep writes its manifest, appends `seen.csv`, then advances `state.json` **last**, so an interruption re-sweeps rather than skips (`SWEEP-DAILY-LIST.md` step 6, *Manifest and state*). Compare `sweep/*/state.json.last_run_completed_utc` against the newest `manifest-*.md` / `drop-log-*.csv` in the same folder; a manifest ahead of the mark is an interrupted run.
- **pending writes from an ingest** — `logs/ingest-pending-writes.md` exists and is non-empty: `test -s logs/ingest-pending-writes.md && wc -l < logs/ingest-pending-writes.md`. Phase B (`WIKI-SYNC.md`) writes the concept pages and indexes from this file, so **an empty `new/` does not mean the ingest finished**. Place hubs are not in it (`HUB-COMPILE.md`). Only Phase B drains it; its writes are idempotent.
- **sources this run left uncited** — an item admitted to `raw/` that **no page in `wiki/` cites**: `python scripts/uncited-sources.py --recent 1`. **Reads 0 on a healthy run**; a hit means **Phase B missed a page**. A gate **only over the run's own window**; the corpus-wide count is housekeeping. The script excludes finance and budget records (`FINANCE-COMPILE.md` aggregates, not `[[wikilinks]]`).

**Not a gate, by design:** the sweep high-water marks; a stale mark is a wider next window, not outstanding work.

## The `log.md` entry — one telegraphic line

```
2026-08-10 21:14 · **DAILY-SWEEP** · staged 34 · 9 domains nil · window 08-09→08-10 · revert: none
2026-08-10 19:02 · **SWEEP-CYCLE** · FATAL: Exa canary absent — night not run · revert: none
```

`YYYY-MM-DD HH:MM · **<PASS>** · <what changed> · revert: <hint>`

- **The timestamp is UTC, read from a real clock (`date -u`), never estimated.**
- **One line, at most 40 words.** No section, no bullets, no second line; `scripts/log-append.py` refuses a longer entry. Reasoning that overruns the cap belongs in the commit body; split one entry per thing changed.
- **Two things earn a line and nothing else does: what a process did, and a fatal error** *(Bill, 2026-09-08)*. **No decision lines** — a ruling about how a pass should behave is recorded in the commit body with the diff that carries it, where the evidence for it already sits; **no per-item calls** — admitting, dropping, merging, retagging or deduping a specific source rides the pass's own line; **no agents** — a sub-agent, batch or slice is not a process and never appears, neither writing a line nor counted on one.
- **`<pass>` is the process name in bold capitals** — `**WIKI-STATUS**`, `**SWEEP-CYCLE**`, `**INGEST**`: the announce banner's name uppercased, spaces to hyphens, which is also its procedure file's stem. `scripts/log-append.py` writes it that way from whatever it is given, so a reader scanning the file can find one process's history by eye.
- **A fatal error is logged as that process's own line**, saying what failed and that the run stopped — a canary that did not answer, an instrument that was absent. Nothing lesser: a retried step, a nil result and an awkward item are the run working, not errors.
- **Only the orchestrating pass writes `log.md`, and only once, at its own close.** A spawned sub-agent, batch or Phase A slice never calls `scripts/log-append.py` — it returns its tally and delta list to whatever spawned it, and that parent folds the whole run into the single closing entry. A log full of per-batch lines is as unreadable as a log full of per-item ones, and the fix is the same: aggregate at the level the reader actually checks.
- **`<what changed>`** is telegraphic: counts and objects, not sentences; several `·`-separated fields are fine.
- **`revert:`** names what to undo: a commit, a file, a register line. Wrote nothing → `revert: none`.
- **Existing entries are not retrofitted**: `scripts/rotate-log.py` truncates the file at every cycle close.

## The standing tally line

Every CC job ends on this line (per `CLAUDE.md` → *Reporting*):

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

All but the last are the live counts above; **decisions logged** is the count of `decision` lines this job wrote to `logs/log.md`, a per-job tally, not a queue — ordinarily zero. `status.py` cannot know which job is running, so **the pass passes its own count in**: `python scripts/status.py --decisions=N`, defaulting to 0. It emitted the literal `NN` until 2026-09-08, and a placeholder nobody is forced to fill is one that reaches the reader unfilled. **Name any gate above zero on the same line**; the tally does not carry them.

**Only the first three clear themselves by running the next pass.** `housekeeping` clears when a session is spent on a job; `osint-notes` when CC resolves one; `corpus-notes` when CORPUS does the same, the one count no OSINT pass can move; `fetch` only in Bill's browser; `commits` as each job commits its own work. Never run a pass merely to move one down.

**The line is restated in every pass file, deliberately.** A change to it is one mechanical sweep, `grep -rln 'decisions logged - NN' -- *.md wiki/*.md | xargs sed -i 's/old/new/'`, then a check that `CLAUDE.md` → *Reporting* carries the same line.

## Announce which process is running

Whenever a pass runs, and on **every** iteration of the `update-wiki` loop, print **one clear line naming the process before it starts**:

```
▶ running: ingest — update-wiki iteration 2
```

The process names: `ingest`, `reconcile`, `acquire`, `rules`, `full lint`, `prune`, `daily sweep`, `off-list sweep`, `newspapers sweep`, `journals sweep`, `thinktanks sweep`, `sweep cycle`, `hub compile`, `finance compile`, `budget collect`, `wiki sync`. A display convention, not a log entry. **Note the time as you print it**: the elapsed clock starts here.

## Progress — a broad sense while it runs

For a long pass or a multi-step batch, also emit a **broad progress line** at each pass/step boundary and each rough milestone, **not** every item:

- **Batch step** (`SWEEP-CYCLE.md`, `BUDGET-COLLECT.md`): `▶ step 2/3: off-list sweep`.
- **Within a pass:** a rough count against the whole: `ingest: 12/30 processed`.
- **update-wiki loop:** the iteration and what it is draining: `iteration 2 — ingest 8 left, acquire 3 left`.

### The close report — one line on screen, and nothing else

The standing tally line above, and nothing after it.

**Cost is neither calculated nor reported** *(Bill, 2026-09-08 — the run-cost line, its per-step split, the `· cost:` field on a `log.md` entry and `scripts/run-cost.py` are all removed)*. No pass counts its sub-agents, prices a token, or carries a cost field on its `log.md` line. A sweep whose own log form records how long it took keeps that; a duration is not a cost report.

**No pass mandates an explanation of a number it produced.** A reading that needs a ruling is CC's own call, taken and logged (`CLAUDE.md` → *Act. Log after. Never ask.*); a reading that needs work is the next pass's.

**To watch a run, run it in the foreground**; a detached background agent hides all of this.

## Say when CC's own context is the limit

**When the thing stopping a run is CC's remaining context rather than the work, say so plainly and recommend a fresh session.** Do not silently shorten the run, and **do not split the work into more registered jobs**.

| The limit is… | Do |
|---|---|
| the work is genuinely too big for a session | split it, per `X:\housekeeping-jobs.md` → *How a job is worked* |
| **CC's remaining context in a long conversation** | **say so; recommend restarting; leave a clean restart point** |

**A clean restart point**: everything committed, the register consolidated, and the method already worked out written onto the job.

**Three of the same compromise in a row is one pattern, not three decisions**; when the same shape recurs, stop and name it rather than logging it a third time. **If any half of a job is going to be taken, take the hard half.**
