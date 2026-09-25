<!-- reader: cc; type: runbook -->
# BACKLOG.md — one housekeeping job, unattended

Trigger: **`SWEEP-CYCLE.md`'s close**, at its housekeeping position — after the first mirror, before the rules pass. **It runs every night (`SWEEP-CYCLE.md`); this file decides what the night's backlog act is.** Also runnable by hand as **"run the backlog"**. A session spent on the register ("run housekeeping", "run housekeeping job N") works under the same rules below, minus the one-job limit.

**What it is.** The drain for `X:\housekeeping-jobs.md`: one job a night, oldest first, so the register counts down without a dedicated session. Status-acquire countries do not come here — their batches are ingested by the cycle itself.

---

## 0. Notes first, every job

**Read `X:\notes-for-osint.md` before starting a job, and action whatever is open** *(Bill, 2026-09-21)*. **Every job, not once a session**: a job can run an hour, CORPUS writes while OSINT works, and a note raised at 08:13 should not sit unread inside a page-fold.

**A note outranks a job by construction.** A housekeeping entry is lint-shaped — real, closable, and about how the wiki reads; a note is usually a **correctness defect in something already published**: a wrong date, a wrong amount, a row attributed to the wrong country. Fix the published thing first.

Close each note into `notes-for-osint-resolved.md` with its resolution, per the share's `README.md`. **A note that needs a primary the wiki does not hold is not left half-answered** — it becomes a contradiction brief or an acquisition line, and the note closes saying so.

## 1. Select

**The register's oldest open entry, and no other.** Selection is `X:\housekeeping-jobs.md` → *Jobs — oldest first*, top entry. A job that is merely large is split (§3), never skipped. An empty register: skip, and say `no housekeeping job open` on the closing line.

## 2. Prepared work first

**Before reading the job, look for `X:\prepared\job-NN\`** — or a folder naming NN among several (`job-102-103\`). CORPUS prepares there; what it holds is the job's first act, and the job is then whatever it leaves.

- **A brief** (a table, a CSV, side-by-side pairs) — read it in place of the search it replaces. The ruling or per-item call the register names stays this session's.
- **A script and its input** — run it dry, read the dry run, then `--write`. A dry run that prints a refusal, or a change outside the job's stated scope, is not written: annotate the entry with the one line it printed and work the job by hand.
- **A patch series** — applied only through the check `CLAUDE.md` names for patches from `X:\prepared\`. Where no such check is named, the patch is not applied; the job is worked by hand.

Nothing in `X:\prepared\` is deleted by this pass; CORPUS clears its own folders.

## 3. Size

**An entry sized above 120 minutes is split before it is worked** (`housekeeping-jobs.md` → *Rough sizing*): the night's act is then the split itself, plus the first of the new jobs if there is room. Slicing an oversized entry night after night is what the sizing rule exists to stop.

## 4. Work

**One sub-agent**: housekeeping is read-and-judge work throughout, the same class as a Phase B page write.

**Whole job if it closes within the night; otherwise the largest tractable slice**, logged as a dated annotation on the still-open entry. This is the one exception to `housekeeping-jobs.md` → *How a job is worked*'s "split into numbered jobs before starting": the entry stays oldest and is picked again next time, until it can honestly be struck.

## 5. Close

**A job that closes is struck** (`x` prefix, cleared date) **and moved to `X:\housekeeping-jobs-resolved.md`**, exactly as a hand session closes it. **Update *Rough sizing* in the same pass** — drop the row on a strike, adjust it where the slice changed the job's known scope.

**Writes to `X:\housekeeping-jobs.md` and `-resolved.md`, commits nothing there** — `X:\README.md` → *Conventions* governs the share. **Commits whatever it changed in `C:\OSINT`** — the pages, scripts or fixes the job actually produced — at its own boundary: `python scripts/assert-containment.py --stage housekeeping [--allow-extra <path> ...]`, then `git commit`. Nothing changed in this repository: no commit.

**One log line**, `**BACKLOG**`: the job number, closed or sliced, what changed, and the revert hint.
