<!-- reader: cc; type: runbook -->
# STATUS.md — read and show wiki status

Trigger: **"wiki status"** / **"display status"**. **Single source of truth** for everything below; no pass file redefines it.

**"wiki status"** *calculates*: `python scripts/status.py` runs the counts and gates below and **always writes the reading to `logs/status.md`** (git-ignored); `--fast` skips the uncited walk. **"display status"** *reads*: `cat logs/status.md`, nothing recomputed; its timestamp gives its age.

---

## The counts

- **awaiting ingest** — **every item in `new/`, whatever its extension**, bar dotfiles and `README`: `ls -A new/ | grep -v '^\.' | grep -vi readme | wc -l`
- **contradictions** — files in `reviews/contradictions/open/`, **excluding the folder's `README.md`**: `ls reviews/contradictions/open/*.md 2>/dev/null | grep -vi readme | wc -l`
- **acquisitions** — **every list line under the one `## Open items` heading** of `reviews/acquisitions.md`, never by marker or URL: `awk '/^## Open items/{f=1;next} /^## /{f=0} f' reviews/acquisitions.md | grep -cE '^\s*[-*] '`
- **housekeeping** — unstruck numbered jobs in `X:\osint-housekeeping.md` (a struck job carries an `x` prefix): `grep -cE '^[0-9]+\. ' /x/osint-housekeeping.md`
- **rule-candidates** — open lines in `reviews/rule-candidates.md`, the queue `RULES.md` drains: `grep -cE '^- ' reviews/rule-candidates.md`. The pass is every night's last stage (`SWEEP-CYCLE.md`), so this is the **open** queue: cases under three occurrences and 21 days old. **A climbing number is a recurring case.**
- **osint-notes** — open notes in `X:\notes-for-osint.md`, the CORPUS→OSINT queue. Resolved notes move to the `-resolved` file, so every entry counts. **Both entry shapes count**, the bold lead `**N** (date) —` and the `### N. [TAG]` heading: `grep -cE '^(\*\*[0-9]+\*\*[ (]|#{2,3} [0-9]+[. ])' /x/notes-for-osint.md`
- **corpus-notes** — open notes in `X:\notes-for-corpus.md`, the OSINT→CORPUS queue; the **same** pattern: `grep -cE '^(\*\*[0-9]+\*\*[ (]|#{2,3} [0-9]+[. ])' /x/notes-for-corpus.md`
- **fetch** — unstruck lines in `X:\fetch-list.md`, documents **only Bill's browser** can get; same `x` convention: `grep -cE '^[0-9]+[a-z]?\. ' /x/fetch-list.md`
- **commits** — dirty paths **after CC has committed its own work**: `git status --porcelain | wc -l`. **A job commits what it changed as its last act**, naming what and why. **A file mixing CC's edits with another session's is committed, and the message says so.** Never commit another session's substantive output to tidy the number.

Commands are indicative; check the files if one looks wrong.

**The count is the queue.** A binary artefact in `new/` (with its companion page, `layout.md` §3) is **counted like any other item**.

## Gates — half-finished states no tally shows

**A queue counts work waiting to start; a gate marks a pass that stopped half-way.** Gates are checked at the end of every job and reported **separately, in prose, never in the tally line**.

- **awaiting budget collect.** A `new-budget/{ISO3}/` folder means a collect batch stopped short (`new-budget/` holds only `manifest.csv` at every stop): `find new-budget -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l`, cleared by `BUDGET-COLLECT.md` for that country.
- **finance-compile baseline** — places whose finance records changed since the last compile: `python scripts/finance-compile-scope.py | wc -l`. Ingest fires the compile (`INGEST.md` → *Ending the run*), so it reads 0 on a healthy tree. `FINANCE-COMPILE.md` → *Close* advances the baseline with `finance-compile-scope.py --commit` only after the hubs are **committed**. A full-house scope means that step was skipped: repair the baseline, do not recompute every hub.
- **an interrupted sweep** — a sweep writes its manifest, appends `seen.csv`, and advances `state.json` **last** (`SWEEP-DAILY-LIST.md` step 6, *Manifest and state*), so a newest `manifest-*.md` / `drop-log-*.csv` ahead of the folder's `sweep/*/state.json.last_run_completed_utc` is an interrupted run.
- **pending writes from an ingest** — `test -s logs/ingest-pending-writes.md && wc -l < logs/ingest-pending-writes.md`. Phase B (`WIKI-SYNC.md`) writes concept pages and indexes from it: **an empty `new/` does not mean the ingest finished**. Place hubs are not in it (`HUB-COMPILE.md`). Only Phase B drains it, idempotently.
- **sources this run left uncited** — admitted to `raw/`, **cited by no `wiki/` page**: `python scripts/uncited-sources.py --recent 1`. **Reads 0 on a healthy run**; a hit means **Phase B missed a page**. A gate **only over the run's own window**; the corpus-wide count is housekeeping. Finance and budget records are excluded (`FINANCE-COMPILE.md` aggregates, not `[[wikilinks]]`).

**Not a gate:** a stale sweep high-water mark, which only widens the next window.

## The `log.md` entry — one telegraphic line

```
2026-08-10 21:14 · **DAILY-SWEEP** · staged 34 · 9 domains nil · window 08-09→08-10 · revert: none
2026-08-10 19:02 · **SWEEP-CYCLE** · FATAL: Exa canary absent — night not run · revert: none
```

`YYYY-MM-DD HH:MM · **<PASS>** · <what changed> · revert: <hint>`

- **The timestamp is UTC, read from a real clock (`date -u`), never estimated.**
- **One line, at most 40 words.** No section, bullets or second line; `scripts/log-append.py` refuses a longer entry. Reasoning goes in the commit body; split one entry per thing changed.
- **Two things earn a line and nothing else does: what a process did, and a fatal error** *(Bill, 2026-09-08)*. **No decision lines** — a ruling goes in the commit body with its diff; **no per-item calls** — a call on one source rides the pass's own line; **no agents** — a sub-agent, batch or slice is not a process.
- **`<pass>` is the process name in bold capitals** — `**WIKI-STATUS**`, `**INGEST**`: the announce banner's name uppercased, spaces to hyphens — its procedure file's stem. `scripts/log-append.py` normalises whatever it is given.
- **A fatal error is logged as that process's own line**, saying what failed and that the run stopped. A retried step, a nil result and an awkward item are not errors.
- **Only the orchestrating pass writes `log.md`, once, at its own close.** A sub-agent, batch or Phase A slice never calls `scripts/log-append.py`; it returns its tally and delta list to its parent.
- **`<what changed>`**: counts and objects, `·`-separated.
- **`revert:`** names what to undo: a commit, a file, a register line. Wrote nothing → `revert: none`.
- **Existing entries are not retrofitted**: `scripts/rotate-log.py` truncates the file at every cycle close.

## The standing tally line

Every CC job ends on this line (per `CLAUDE.md` → *Reporting*):

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

**decisions logged** is the count of `decision` lines this job wrote to `logs/log.md`, a per-job tally, ordinarily zero. **The pass passes its own count in**: `python scripts/status.py --decisions=N`, defaulting to 0. **Name any gate above zero on the same line.**

**Only the first three clear by running the next pass.** `housekeeping` clears as jobs are worked, `osint-notes` as CC resolves them, `corpus-notes` only by CORPUS, `fetch` only in Bill's browser, `commits` as jobs commit. Never run a pass merely to move one down.

**The line is restated in every pass file, deliberately.** A change to it is one mechanical sweep, `grep -rln 'decisions logged - NN' -- *.md wiki/*.md | xargs sed -i 's/old/new/'`, then check `CLAUDE.md` → *Reporting* matches.

## Announce which process is running

Whenever a pass runs, and on **every** `update-wiki` iteration, print **one line naming it before it starts**:

```
▶ running: ingest — update-wiki iteration 2
```

Names: `ingest`, `reconcile`, `acquire`, `rules`, `full lint`, `prune`, `daily sweep`, `off-list sweep`, `newspapers sweep`, `journals sweep`, `thinktanks sweep`, `sweep cycle`, `hub compile`, `finance compile`, `budget collect`, `wiki sync`. Display only, not logged. **Note the time as you print it**: the elapsed clock starts here.

## Progress

For a long pass or batch, emit a **broad progress line** per step boundary and rough milestone, **not** per item:

- **Batch step** (`SWEEP-CYCLE.md`, `BUDGET-COLLECT.md`): `▶ step 2/3: off-list sweep`.
- **Within a pass:** `ingest: 12/30 processed`.
- **update-wiki loop:** `iteration 2 — ingest 8 left, acquire 3 left`.

### The close report

On screen, the standing tally line above, and nothing after it.

**Cost is neither calculated nor reported** *(Bill, 2026-09-08; `scripts/run-cost.py` removed)*: no pass counts sub-agents, prices a token, or carries a `· cost:` field. A sweep log's own duration is not a cost report.

**No pass mandates an explanation of a number it produced.** A reading needing a ruling is CC's call (`CLAUDE.md` → *Act. Log after. Never ask.*); one needing work is the next pass's.

**To watch a run, run it in the foreground**, not as a background agent.

## Say when CC's own context is the limit

**When CC's remaining context, not the work, is stopping a run, say so, recommend a fresh session and leave a clean restart point.** Do not silently shorten the run, and **do not split the work into more registered jobs**; only work genuinely too big for a session is split, per `X:\osint-housekeeping.md` → *How a job is worked*.

**A clean restart point**: everything committed, the register consolidated, the method worked out written onto the job.

**Three of the same compromise in a row is one pattern, not three decisions**: stop and name it. **If any half of a job is going to be taken, take the hard half.**
