<!-- reader: cc; type: runbook -->
# PRUNE.md — retention and register maintenance

Trigger: **"run prune"**. Also **lint #18**, which is this file's call — the numbered handle is permanent, cited by `RECONCILE.md` and both registers.

**One place for every "this ages out" rule.** This file is the view of what the vault keeps, for how long, and who deletes it, and the runner for the jobs no other pass owns.

**The principle every rule here serves** (`CLAUDE.md` → *Keeping this file short*): closed work is **deleted, not archived**. Git holds it. A register is a worklist; its history is git's job.

---

## The retention register

Everything in the vault that ages out, and who does it. **A rule lives in exactly one place — its owner.** Where the owner is another pass, this table is a pointer, not a second copy.

| What | Rule | Owner |
|---|---|---|
| `reviews/post-run-notes.md` | closed entries deleted **3 days** after their cleared date | **this pass** |
| `X:\housekeeping-jobs.md` | struck jobs **moved to `X:\housekeeping-jobs-resolved.md`, not deleted** — the move happens when the job is struck, so nothing here ages | the striking session |
| `reviews/acquisitions.md` | a section with no `[untried]`/`[blocked]` line left is deleted **3 days** after its heading / drained date | **this pass** |
| `X:\fetch-list.md` | struck (`x`-prefixed) lines deleted **3 days** after their fetched date | **this pass** |
| `logs/collection-stamp.json` | never — a single overwritten object, not a rolling log | — |
| `reviews/contradictions/open/` | brief deleted **on closure** — never aged | `RECONCILE.md` |
| `logs/sweep-url_log.md` | pruned to **one rotation** at the close of each night | `SWEEP-CYCLE.md` |
| `sweep/daily/seen.csv` | rows older than **60 days**, at the end of each run | `SWEEP-DAILY-LIST.md` |
| `sweep/*/manifest-YYYY-MM-DD*.md`, `drop-log-YYYY-MM-DD*.csv` | deleted **60 days** after the date in the name — never a folder's newest of either | **this pass** |
| `logs/log.md` | the newest **~400 lines**, at every cycle close (`scripts/rotate-log.py`) | `SWEEP-CYCLE.md` |
| `logs/machine-record-audit.csv` | **never pruned** — one row a night, and a row means nothing except against the row before it | `LINT.md` #21 |
| `logs/machine-record-audit-defects.csv` | **not aged — rewritten whole** each run; it states the present, not a history | `LINT.md` #21 |

**Nothing in the vault ages without an owner.** A file class that appears in neither this table nor another pass's rule is the finding — report it by name rather than inventing a threshold for it in passing.

## Jobs this pass runs

### `logs/log.md` — not this pass's

**`SWEEP-CYCLE.md` owns it**, mechanically: `python scripts/rotate-log.py --apply` at every cycle close keeps the newest ~400 lines, whole entries only. There is no monthly date rotation here, and no duplicate-entry or descending-date assertion: a line budget applied every night makes a horizon rule, a shape rule and a `--log` mode all redundant.

### `sweep/*/manifest-*.md` and `drop-log-*.csv` — 60 days

`python scripts/prune-dated.py --sweep` (report) / `--apply` (act).

Delete every dated manifest and drop-log whose name is more than **60 days** old, across every sweep folder — not `daily/` alone; each sweep writes the same pair.

**60 days is `sweep/*/seen.csv`'s horizon**, deliberately: the drop-log is the evidence for one run's screening, and once a URL has aged out of the dedup memory the drop can no longer be re-tested against the record it explains. What is durable is extracted by the sweep itself — per-domain findings to `sweep/domains/{domain}.md`, run history to the sweep's own `history.md`.

**Never delete a folder's newest manifest or newest drop-log**, whatever its date. `STATUS.md` reads the newest of each against `state.json.last_run_completed_utc` to detect a sweep that died between staging and state; a folder pruned empty would silence that check instead of answering it.

Undated per-country logs (`sweep/archive/drop-log-{ISO3}.csv`) are not in scope — they are a completed back-fill's record, not a run's.

### The 3-day rule

**Once an item is closed, it is deleted 3 days later.** Report the count deleted per register. Git holds every version, and these are work queues, not archives.

- **Never touch an open item.**
- **Never renumber.** The numbers are permanent handles and the gaps pruning leaves are correct.
- **A closed item with no recoverable date is stamped, not deleted** — for the two numbered registers, write today's *(cleared YYYY-MM-DD)* so it serves its full three days.

| Register | Closed means | Ages from |
|---|---|---|
| `reviews/post-run-notes.md` | `x`-prefixed | *(cleared YYYY-MM-DD)* on the entry |
| `X:\housekeeping-jobs.md` | `x`-prefixed | — *(not aged; struck jobs leave the file at once)* |
| `reviews/acquisitions.md` | no `[untried]`/`[blocked]` line left in the section | the section heading / drained note |
| `X:\fetch-list.md` | `x`-prefixed | *(YYYY-MM-DD)* on the struck line |

**A struck fetch line is actioned before it is deleted.** It carries Bill's outcome and nothing else does: struck bare, the document is in `new/` and ingest has it; struck with a reason (`login only`, `gone`), the route is dead — **write the absence dated on the page it bears on** and record the domain so no sweep re-lists it. Delete only after that. This is the one register where pruning a line can lose a fact.

### Section discipline

**Both numbered registers keep two sections — open first, then `Done`, each oldest first.** Striking an entry **moves it into `Done`** with its number; pruning removes it from there. Never reorder within a section.

### The next-number counter

**Because pruning shrinks the file, the next number cannot be derived from it.** Pruning removes high numbers, so `max(present) + 1` re-issues numbers already used — the counter has to outlive the entries. Both numbered registers carry it in their header:

| Register | Header line |
|---|---|
| `reviews/post-run-notes.md` | `## NEXT NOTE NUMBER: N` |
| `X:\housekeeping-jobs.md` | `## NEXT JOB NUMBER: N` |

Take it, write the entry, increment the line.

**Assert it on every run.** `N` must exceed every number in the file, struck or not. If it does not, the counter went stale — raise it to `max + 1` (auto-fix; too low is the dangerous direction) and **surface it**, because an entry may already have been filed under a duplicate number.

**Also assert that no number is used twice.** The counter only proves the next number is safe; it cannot see a number reused below itself — which is what happens when a writer derives its number from the file instead of taking the header. Collect every handle in the file, struck and open, and report any that appears more than once. **Never auto-fix this one** — resolving a collision means deciding which entry keeps the number, and a cited handle must not move: reissue the mis-filed entry at the top of the counter and letter-suffix a struck twin (`x43` → `x43b`).

The header is `##`-prefixed so the tally greps in `STATUS.md`, which match a number at the left margin, can never read it as an entry.

## Adding a pruning job

When a new "this ages out" rule appears:

1. **Add a row to the register above**, with its owner.
2. **If no other pass owns it, it is this pass's** — write the job under *Jobs this pass runs*, and nowhere else.
3. **If another pass owns it, the row is a pointer.** Do not restate the rule here; two copies of a retention rule is how a horizon becomes a contradiction.
4. **Deleted, not archived** — a new rule that moves files to an archive folder needs an argument for why git is insufficient.

## Concurrency and logging

Runs inside `full lint` (as #18) or standalone; either way it wants no other CC session writing the registers. The three registers are read and ruled on; the two dated rows are `python scripts/prune-dated.py --apply`, which reports what it deleted and exits non-zero only where a decision is owed. One terse `logs/log.md` line: the count deleted per register and per dated row, any counter it raised, and any file class it found with no owner.
