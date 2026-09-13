---
type: doc
title: OSINT — withdraw R9, there is no request feed
last_reviewed: 2026-08-16
audience: OSINT (Bill, or a colleague's session run *in* OSINT)
status: written in Corpus — to be actioned in an OSINT session
---

# Withdraw R9: OSINT reads nothing from CORPUS

*(Written from CORPUS, for OSINT. **Self-contained** — it assumes nothing about `osint-migration.md` or `cc-reset-instructions-2026-08-16.md` and needs neither read first. One line per paragraph, OSINT house style.)*

**Run this once session 1 of `cc-reset-instructions-2026-08-16.md` has finished** *(Bill, 2026-08-16)*. It is not urgent and it does not interrupt: the wiring it removes reads a path that does not resolve, so it cannot have done anything, and running it alongside session 1 would only have two passes editing `CLAUDE.md` at once.

By then most of what follows will already have happened — R9 wired, R10's pruning run, the boundary sentence possibly reworded. **So every step below tests the file in front of it rather than assuming a history, and does nothing if it is already satisfied.** Work them in order; none depends on session 1 having stopped anywhere in particular.

## Why

R9 asked OSINT to read CORPUS's request feed, `C:\CORPUS\logs\requests-for-osint.csv`, as the single exception to *OSINT does not read CORPUS*. **It is withdrawn** *(Bill, 2026-08-16)*.

**`C:\CORPUS` is not reachable from the machine OSINT runs on.** The 2026-08-16 09:44 and 10:40 entries in `logs/log.md` both record it: this session reaches OSINT over `\\bill-vivobook\OSINT`, and only that share and `\Users` are exposed. CORPUS is a directory on a different machine. This is topology, not a permission that could be granted, and **the repair is not to share the folder** — that would reopen a dependency being closed deliberately, for the reason below.

It was also unnecessary, which is the better reason. The requests only ever needed to reach an OSINT *session*, and a file was one assumption about how. Bill runs both sides; he hands the open requests to the session as its brief, and `ACQUIRE` already knows what to do with a brief.

So the boundary loses its exception rather than gaining a workaround: **CORPUS reads OSINT, read-only. OSINT reads nothing from CORPUS and writes nothing to it.** One direction, no exceptions, nothing to keep in step.

## 1. Withdraw task 6 in the reset brief

**`documentation/cc-reset-instructions-2026-08-16.md`**, session 1, **item 6** is R9 in full: *"wire `ACQUIRE` (and the deep/country sweeps) to read `C:\CORPUS\logs\requests-for-osint.csv`."*

Strike it, in place, marking it withdrawn on this file's authority rather than deleting the line — a numbered list that silently loses an item reads as a transcription error later.

**Item 1** of the same list quotes the boundary sentence with the exception in it (*"reads only the R9 request feed"*). Correct it to say OSINT neither writes to CORPUS nor reads from it.

Correcting a brief whose tasks are already done is not bookkeeping for its own sake: this file is the record of what was asked, it is committed in `documentation/`, and an uncorrected item 6 is a standing instruction for the next session that reads it to wire the feed again.

## 2. Unwire R9 if it was built

**Check: does `ACQUIRE.md` contain a `## Pulling in CORPUS's request feed` section?** If not, R9 was never wired and this step is already satisfied — go to step 3.

If it does, it was landed by commit **`759f6492`** — *"R9: wire ACQUIRE and the country-deep sweep to CORPUS's request feed"* — across four files:

- **`ACQUIRE.md`** — the `## Pulling in CORPUS's request feed` section before the loop, which reads the CSV and appends open rows to `reviews/acquisitions.md`, deduped on `row_id`. Remove the section whole.
- **`SWEEP-COUNTRY-DEEP.md`** — a fifth per-country item, *Search 5*, one locate-and-fetch task per open row whose `unit` matches the country. Remove it and restore the four-item shape.
- **`wiki/index.md`** — the `ACQUIRE.md` and `SWEEP-COUNTRY-DEEP.md` rows were rewritten to describe the new steps. Restore their previous wording.
- **`logs/log.md`** — **do not revert this file.** It is append-only and its 10:40 entry is a true record of what happened. Leave it and append a new entry recording the unwind, as the vault's own rule requires.

`git revert 759f6492` is the fast path **only** with `logs/log.md` excluded, and note that R7 (`1d83c41c`) landed afterwards and also touched `wiki/index.md`, so expect a conflict there. Reverting the two process files and the two index rows by hand is the safer route.

Both process files carry an honest flag, written by the session that wired them, saying `C:\CORPUS` was unreachable and the steps could not be tested. Those come out with the steps they annotate.

Also check `reviews/acquisitions.md`: if any row was appended citing a `CORPUS row_id`, remove it. Nothing was reachable to read, so there should be none.

## 3. Correct the boundary in `CLAUDE.md`

**Check the boundary paragraph** — in *Purpose*, where R10 placed it. It reads, as landed:

> **OSINT collects and classifies; CORPUS (`C:\CORPUS`) compiles, reports and analyses**, over a read-only view of `raw/`, `lookups/` and `wiki/`. OSINT writes nothing to CORPUS, and reads only CORPUS's request feed (`logs/requests-for-osint.csv`) — the one exception to that boundary.

Cut everything from *and reads only* onward and close the sentence so it says OSINT neither writes to CORPUS nor reads from it — no exception, and no mention of a request feed. State plainly that an OSINT session cannot see `C:\CORPUS` and is not meant to.

If the sentence already reads that way, this step is done.

## 4. Correct OSINT's copy of the migration brief

**`documentation/osint-migration.md`** is a snapshot taken before the withdrawal, and three places still carry the exception:

- the boundary paragraph near the top — *"with one exception (the request feed, task R9)"*;
- **R9** itself, which still instructs a reader to wire it;
- **R10**'s quoted boundary sentence — *"reads only the R9 request feed"*.

Strike R9 as withdrawn and correct the other two. CORPUS's copy is authoritative and already corrected; this one only needs to stop contradicting it.

## Nothing else moves

No sweep other than `SWEEP-COUNTRY-DEEP`, no lint, no script, and no process file beyond the ones named above.

## How the requests reach OSINT instead

CORPUS keeps writing `logs/requests-for-osint.csv` — gaps and named documents its reports are missing. **That file is now purely CORPUS's own record**, not an interface: nothing in OSINT reads it, and OSINT does not need to know it exists.

When Bill opens an OSINT session with acquisitions to chase, he hands over the open requests as the session's brief. From OSINT's side there is nothing new to learn: a request is a brief, `ACQUIRE` runs as it always has, and what it fetches lands in `raw/` the ordinary way.

**Nothing is ever reported back.** A request is settled when CORPUS's next scan finds the record in `raw/` — CORPUS watches the evidence rather than waiting on a reply. So an OSINT session never marks a request closed, never edits a status, and never writes anywhere outside its own tree. If a request cannot be met, that is an ordinary dated absence in OSINT's own queues, and CORPUS will see the gap persist and raise it again.
