---
type: doc
title: OSINT migration — what CORPUS took over, and what OSINT now retires
last_reviewed: 2026-08-16
audience: OSINT (Bill, or a colleague's session run *in* OSINT)
status: written in Corpus — to be actioned in an OSINT session (X:
otes-for-osint.md)
---

# OSINT migration — the retirement list

*(Written from CORPUS, for OSINT. It briefs an OSINT session on what CORPUS has taken over and lists, as tasks, what OSINT should now retire. Action this **before** `X:
otes-for-osint.md`, which assumes the boundary below is already in force. One line per paragraph, OSINT house style.)*

*(**Read Sequencing first — the list is not in the order it should be done in.** Two tasks come before R1. Every ruling this list was waiting on has now been made, so nothing below is an open question for an OSINT session to decide. Verified against both trees on 2026-08-16, which is where the file counts and dates below come from.)*

## What CORPUS is

CORPUS (`C:\CORPUS`, its own git repo) is the public-site layer for **corpus.data-landscapers.com**: country and regional reports, a source catalogue, and non-state-finance and budget data, served over the private research base that OSINT maintains.

Until 2026-08-13 CORPUS was a **mirror**: it pulled OSINT's `outputs/` and rendered it. That is no longer true. CORPUS now **authors** the output layer itself. The current architecture is CORPUS's `documentation/migration-report-layer.md`; this file is its OSINT-facing half.

## The relationship now — two repos, one direction

**OSINT collects and classifies. CORPUS compiles, reports, and analyses.**

CORPUS reads OSINT **read-only** — `raw/`, `lookups/` and the internal `wiki/`, and *not* `index/`, which it builds for itself — and writes only into its own tree. It never writes to OSINT, in any form. OSINT does not read CORPUS, and gains no publication step in its night. *(R9 originally carved a single exception here — the request feed — withdrawn 2026-08-16, `documentation/osint-no-request-feed.md`: `C:\CORPUS` is unreachable from an OSINT session, and Bill hands requests over as a session's brief instead.)*

CORPUS runs as two jobs on Bill's machine: **BUILD** (OSINT evidence → CORPUS `outputs/`) and **RENDER** (`outputs/` → the site). BUILD's compiles are pure functions of `raw/`; its report-update stage is a model pass; RENDER produces the site and backs both repos up (`mirror.bat`, which reads OSINT read-only).

*(**Void from 2026-08-20 — and the correction is larger than a reversed backup rule** *(Bill)*. `O:\`, OSINT's workroot until 2026-08-19, is now **CORPUS's read-only copy of the vault**, supplied by a one-way FreeFileSync mirror (`SyncSettings.ffs_batch`) that runs as the last act of `SWEEP-CYCLE.md`. So OSINT does keep a sync of its own, and it is not a backup: **it is CORPUS's read path.** Two consequences. The paragraph below — "OSINT runs none and keeps none of its own", "a session should not restore any of them" — must not be actioned. And **every statement in this file that CORPUS reads OSINT's working tree through workroot junctions is void**; CORPUS reads the mirror. The read-only boundary itself is unchanged: still one-way, still nothing of CORPUS's readable from OSINT. `LINT` #19 stays retired, so nothing checks the mirror's freshness — a gap that now costs more than it did, because a stale `O:\` is CORPUS compiling from yesterday's evidence rather than merely a late backup.)*

**All backups are CORPUS's** *(Bill, 2026-08-16)*. OSINT runs none and keeps none of its own: one `mirror.bat`, in CORPUS, mirrors both working trees and both git histories to Dropbox and copies both repos to `D:`. This is a property of the boundary rather than a detail of R8 — it is why OSINT's mirror, its FreeFileSync batch, its close step and its `LINT` #19 all go, and why a session should not restore any of them.

**What OSINT must keep stable, because CORPUS reads it:** `raw/`, `lookups/`, `wiki/` — git-tracked, committed, and with stable slugs. **`index/` is not one of them and owes CORPUS nothing** *(2026-08-14)*: CORPUS builds its own index from `raw/` and `wiki/` rather than reading OSINT's, so OSINT's index is OSINT's business entirely. These are the standing constraints; they live in `X:
otes-for-osint.md`, not here.

## The retirement list — tasks for OSINT

Most are *retire X, because CORPUS now owns it, keeping Y*. Do them once CORPUS is confirmed authoritative for the output layer (it is, as of the 2026-08-13 render). Three do not fit that shape and are numbered here anyway, because a reader working the list needs to find them: **R4** retires a purpose rather than an artefact, **R5** is resolved and asks for nothing, and **R11** is initiated by OSINT rather than CORPUS and listed because CORPUS reads what it removes.

**R1 — Retire the report layer.** Remove `REPORT-UPDATE`, `REPORT-COUNTRY`, `REPORT-REGION`, `REPORT-MONTHLY` as processes and drop the `REPORT-UPDATE` step from `SWEEP-CYCLE`'s nightly run (the line after `UPDATE-WIKI`). CORPUS authors ledgers and reports now. The ledgers, `considered.txt`, `gaps.csv` and issued documents under `outputs/reports/` are CORPUS-owned going forward; OSINT's copies become dead once R6 runs.

**R2 — Retire the nightly output refresh.** Remove the `run the output refresh` step (`outputs\ except budgets\, catalogue + capped narrative drain`) from `SWEEP-CYCLE`, and the `## Output refresh` section that documents it. CORPUS builds the catalogue (`build-catalogue.py`) and authors report narrative itself. `scripts/report-narrative-backlog.py` falls with the phase — it exists only to feed the capped narrative drain — and is easy to leave standing. Retire it in the same change.

**`LINT` #26 narrows rather than dies** *(2026-08-16, following R4)*. `scripts/lint-output-freshness.py` asserts the refresh regenerated `outputs\`, which after this task nothing does — but the finance exports R4 keeps are still written, by `FINANCE-COMPILE` firing from ingest rather than by this phase. Rescope #26 to `outputs\non-state-finance\` alone and it becomes *more* useful than it was: with the refresh's blanket rebuild gone, an ingest-fired compile scoped to the wrong places is exactly the miss nothing else would catch, and #26 is what sees it. `outputs\budgets\` stays excluded, frozen on purpose as before.

**R3 — Retire the report half of REPORT-LINT.** *(Corrected 2026-08-14 — an earlier draft of this task told OSINT to drop A and D. It should not. Bill's ruling of 2026-08-13: "REPORT-LINT splits along a seam already inside it — checks A–F stay in OSINT next to what they verify; G–K travel to Corpus.")*

**Checks A–F all stay in OSINT.** They verify the finance and hub compiles against `raw/`, and `raw/` is OSINT's — a check belongs next to the records it reconciles, not next to the CSV it happens to have produced. **Checks G–K travel to CORPUS** (link-held, prose-vs-ledger, vocabulary, as-of, register), because they verify the report layer, which is CORPUS's. Retire `REPORT-LINT` as a report-layer pass; fold A–F into `LINT` or `FINANCE-COMPILE`. Nothing here asks OSINT to give up a check — `scripts/report-lint.py` stays, and is deliberately absent from R7's removal list.

**That last sentence only became true when the export those checks read was carved out of R4 and R6** *(Bill, 2026-08-16)*. Checks A–E all read `outputs/non-state-finance/{ISO3}-nonstate.csv`: A rebuilds each place's deal rows from `raw/` and compares them *to that export*, D reads its `financier` column, and B and C run `compile-hub-financing.py`, which reads it. As first drafted, R4 stopped producing that file and R6 deleted the folder, which would have left only F standing. **The non-state export therefore stays** — see R4, which is now a change of purpose rather than a retirement. Nothing about A–F moves.

**R4 — The finance CSV export stays. What retires is its job of feeding a website.** *(Rewritten 2026-08-16 on Bill's ruling. This task previously said "retire the finance/budget CSV export"; carving the non-state CSV out of it is what keeps `REPORT-LINT` A–E alive — see R3.)*

`build-finance-page.py` (via `FINANCE-COMPILE` step 4 / `FINANCE-PAGES`) writes `{ISO3}-nonstate.csv`, `{ISO3}-summary.csv` and `all-nonstate.csv` into `outputs/non-state-finance/`, plus `{ISO3}-budget.csv` into `outputs/budgets/`. **Change nothing about the script or the step.** It writes all four in one pass per place, with no flag to do half, so splitting it would be code work bought for nothing — and the budget exports are frozen anyway while the domestic-state layer is suspended.

What changes is what the folder is *for*. It was the website's feed; CORPUS now compiles its own from the same `raw/` records, so OSINT's copy is no longer published and no longer read across the boundary. It stays as **OSINT's own compile** — the substrate checks A–E reconcile against, and the file `compile-hub-financing.py` reads to write the hub prose. Two copies now exist, but they are pure functions of the same records rather than two authorities over an authored document, and check A is what holds OSINT's to its evidence. If they ever disagree, CORPUS's is the published one and the disagreement is a bug in one of the two compiles.

**Keep all finance and budget COLLECTION** — `DOMESTIC-FINANCE-SWEEP`, `BUDGET-EXTRACT`, `COUNTRY-BUDGET-BATCH`, `SWEEP-COUNTRY-BUDGET`, `SWEEP-FINANCIERS`, `SWEEP-IATI` — because those write the finance and budget *records* into `raw/`, which is exactly what CORPUS reads. `COUNTRY-BUDGET-BATCH.md`'s *budget-line record* section, which specifies `FINANCE-COMPILE` building `outputs/budgets/{ISO3}-budget.csv` from the records, is now simply accurate and needs no edit.

**R5 — Resolved by R4's ruling; nothing to do.** *(2026-08-16.)* This task existed because `compile-hub-financing.py` rewrites a hub's `## Financing` sentences from `outputs/non-state-finance/{ISO3}-nonstate.csv`, and R4 as drafted stopped producing that file — leaving a script reading a dead path, with three unattractive ways out. R4 no longer stops producing it, so the coupling survives intact and is now deliberate rather than accidental: the hub prose, checks A–E and the export are one self-contained OSINT loop reading only OSINT's own evidence, which is what option (a) was trying to reach by a longer road. **The seam is recorded, not retired** — anything that later stops writing `{ISO3}-nonstate.csv` breaks the hub prose and five checks together, and this is where to look.

**R6 — Retire `outputs/reports/` and `outputs/catalogue/`; keep `outputs/non-state-finance/` and `outputs/budgets/`.** *(Narrowed 2026-08-16 on the R4 ruling — this said "retire OSINT's `outputs/`", whole.)*

Once R1 and R2 stop producing them, the reports and the catalogue are read by nothing: CORPUS authors its own reports and builds its own catalogue, and reads `raw/`/`lookups/`/`wiki/` for both. Remove those two folders from git to reclaim space and end the two-authorities risk over authored documents, which is the risk this task was always about. Confirm CORPUS has a clean build first; keep one tagged commit as a fallback.

**The finance folders are not part of it.** They stay under R4 as OSINT's own compile, still written every ingest-fired `FINANCE-COMPILE`, still what checks A–E and the hub prose read. So `outputs/` survives as a smaller, wholly internal thing rather than disappearing.

**R7 — Retire the report-layer specs and scripts.** `wiki/report-layer.md`, `wiki/report-country-skeleton.md`, `wiki/report-region-skeleton.md`, and `scripts/report-*.py` (`report-render`, `report-scan`, `report-register-check`, `report-country-init`, `report-region-init`) — CORPUS holds its own copies: the scripts in `scripts/`, and the three specs in `documentation/` as of 2026-08-14, adapted rather than mirrored (the register now points at CORPUS's own, and the gaps loop at the request feed). Nothing in CORPUS reads these three files from OSINT any more, so their removal breaks nothing here. Remove from OSINT unless something else in the vault imports them; grep first, scoped to the process files, `scripts/` and `wiki/` — a whole-tree grep also returns a dozen `raw/` sources that merely mention a skeleton by name, and `reviews/acquisitions.md` and `reviews/housekeeping-jobs.md`, which are expected hits and R10's to prune. `scripts/report-lint.py` and `scripts/compile-hub-financing.py` are **not** on this list: R3 keeps checks A–F, and R4 keeps the export the second one reads.

**R8 — Retire OSINT's own mirror.** CORPUS's `mirror.bat` now backs up **both** repos: OSINT and CORPUS working trees + `git bundle` to Dropbox, plus one FreeFileSync pass (`repos-to-flash.ffs_batch`) copying both repos to `D:`. Remove the `run mirror.bat` close step from `SWEEP-CYCLE`, and the `## Mirror` section that documents it, and retire OSINT's `mirror.bat` + `Repo-mirrors.ffs_batch`.

**Half of this has already happened, and the half that has not is live** *(checked 2026-08-16 — do this one ahead of the rest of the list)*. Both files are gone from OSINT's working tree but still tracked: `git status` shows them as unstaged deletions. `SWEEP-CYCLE` meanwhile still carries `run mirror.bat` as the last command of the night, so the cycle's close step points at a file that is not there. Commit the deletion and cut the step and the section together. **`LINT` #19 is already false-alarming on this**: it compares the newest line of `logs/mirror_log.md` against the newest `End` in the cycle log, and OSINT's mirror log stops at 2026-08-11 20:10 while CORPUS's mirror has been running the OSINT legs since — 2026-08-14 20:50 in CORPUS's own `logs/mirror_log.md`. So OSINT has been reporting an unmirrored vault, nightly, while the backup ran. **Retire #19 outright — do not repoint it at CORPUS's log** *(Bill, 2026-08-16: all backups are done by CORPUS)*. Repointing was the obvious repair and it is closed off by the boundary: it would make an OSINT lint read a CORPUS file every night, and the one-way rule has no exception at all *(R9 originally carved one here; withdrawn 2026-08-16, `documentation/osint-no-request-feed.md`)*. A backup OSINT does not perform is not OSINT's to verify.

**But the check has to exist somewhere, and today it does not** *(flagged for CORPUS, 2026-08-16 — this is CORPUS's to build, and is noted here only so OSINT knows why #19 leaves without a replacement)*. `LINT` #19 was written because the mirror once went a week stale in silence, and it is the only automated freshness check either repo has. CORPUS's `mirror.bat` writes a dated `ok`/`FAIL` line to its own `logs/mirror_log.md`, but nothing reads it back: `RENDER.md` asks a *human* to confirm a line dated within the last few minutes, in the same passage that explains why the exit code cannot be trusted. So retiring #19 with nothing built removes the last automated guard at the moment one mirror became responsible for both repos.

There is no longer an independent-OSINT-backup option to weigh: **all backups are CORPUS's**, which is why this task is unconditional.

~~**R9 — Wire the request feed (the only OSINT-ward channel).** CORPUS writes a machine-readable `logs/requests-for-osint.csv` — gaps and named documents a report needs, that OSINT's sweeps should chase. Give `ACQUIRE` (and the deep/country sweeps) a step that reads it and takes each request as a brief; what they fetch lands in `raw/` the ordinary way, and CORPUS's next scan settles the gap. This replaces the CORPUS-side half of the old report→gaps→acquire loop.~~

~~**The contract, since OSINT has to code against it.** The file is `C:\CORPUS\logs\requests-for-osint.csv`, columns `raised,unit,row_id,name,subject,type,request,url,status`. **OSINT reads it and never writes it** — this is the single exception to *OSINT does not read CORPUS*, and it stays one-way, so a request is closed by CORPUS's next scan finding the record in `raw/` and not by OSINT marking the row. It holds a header and one empty record today, so land a real request in it before wiring `ACQUIRE` against it; otherwise there is nothing to test the step on.~~

**Withdrawn** *(Bill, 2026-08-16, `documentation/osint-no-request-feed.md`)* — `C:\CORPUS` is not reachable from the machine OSINT runs on, and the feed was unnecessary regardless: the requests only ever needed to reach an OSINT session, and Bill runs both sides — he hands the open requests over as the session's brief, and `ACQUIRE` already knows what to do with one. The boundary loses the exception rather than gaining a workaround.

**R10 — Update the vault's own docs — but the boundary statement goes first, not last.** This task splits in two, and only one half belongs at the end.

**The boundary into `CLAUDE.md` before anything else on this list.** OSINT's `CLAUDE.md`, `SWEEP-CYCLE.md` and `ACQUIRE.md` mention CORPUS nowhere at all today — the word does not appear in any of them. Until that sentence lands, every OSINT session opens under the pre-migration model with nothing to anchor this file against, including the sessions that action the tasks above. State it plainly: OSINT collects and classifies; CORPUS compiles, reports and analyses over a read-only view; OSINT writes nothing to CORPUS and reads nothing from it.

**The pruning last, once the shape is settled.** `SWEEP-CYCLE`, `STATUS.md`, `wiki/index.md`, `CLAUDE.md`, `reviews/housekeeping-jobs.md` and `reviews/acquisitions.md` lose their references to the retired passes. `REPORT-LINT.md` needs its own pass: the file survives on checks A–F, so what goes is its cross-references to `wiki/report-layer.md` §6 and to checks G–K, both of which travel to CORPUS at R3. Keep `wiki/index.md`'s Processes directory current, per OSINT's own rule.

**R11 — Retire the entity *pages*; keep the entity *tags*.** *(Bill, 2026-08-16 — populating them costs time and tokens for a level of detail the work does not need. The first retirement OSINT initiates rather than CORPUS; it is listed here because CORPUS reads what it removes.)*

`ENTITY-PASS.md` opens by saying exactly what it is: the pass that turns entity *tags* into entity *pages*. `INGEST.md` step 4 deliberately does not mint pages — ingest tags, and the pass decides later with a count in hand — so the tags are written on the hot path and are already paid for, and the pages are the model work. **Retiring `ENTITY-PASS`, the 1,891 pages under `wiki/entities/` (9.4 MB) and the ten `entities-index*.md` files (2,206 lines) takes the whole saving.** The `entities:` field on sources stays: it costs nothing further, 9,174 of 9,407 sources carry one, and it is a published column in CORPUS's `raw-catalogue.csv` and a facet count in `raw-catalogue.json`.

**Precondition — lift the region map out first, or CORPUS's region reports silently narrow.** `report-region-init.py` scopes a region by both halves of a rule: sources carrying the place code, *and* sources that reach the region only through an institution. The second half is built from the entity pages' own frontmatter — `entity_type` in (`organisation`, `government-body`, `initiative`, `instrument`) plus a regional `places` list — so removing the pages removes half the scope, with no error to show for it and a shorter source list as the only symptom. **291 pages carry that membership** (XAF 162, XGL 121, XSS 52, XWA 29, XEA 14, XSA 12, XCA 11, XNA 1). A lookup of slug, `entity_type` and place codes carries all of it; write it to `lookups/` before the pages go and name the file here, so CORPUS can repoint. **Written 2026-08-16, session 1: `lookups/region-membership.csv`** (`slug,entity_type,places` — `places` is the page's full places list, semicolon-joined; generated by `scripts/build-region-membership.py`, counts verified against the breakdown above exactly). The other two CORPUS reads of the pages are cosmetic and can simply go — a financier's display-name fallback in `finance_lib.py`, and the reading list a region work order prints — though losing the first makes `lookups/financier-names.csv` coverage load-bearing and so raises the stakes on REPORT-LINT check D.

**`LINT` #4 will ask for the pages back.** It rewires or retires broken `[[links]]` per `wiki/reference.md` §9's referrer bands, and the top band reads **≥10 → create the wanted page**. With the pages gone and the tags kept, several hundred slugs sit above that bar and the check reads them as a backlog to mint — undoing R11 one lint at a time. So `CLAUDE.md` → *Entities*, `reference.md` §5 (the paging bar) and §9 (the bands), and `LINT` #4 all move in the same change, to say that a tag is now a terminal state rather than a page deferred. `ENTITY-PASS`'s backlog in `reviews/housekeeping-jobs.md` goes with them.

## What OSINT keeps — the guardrail against over-retiring

Do **not** retire any of these; CORPUS depends on them or they are OSINT's core:

- **Collection & classification:** every `SWEEP-*`, `INGEST`, `UPDATE-WIKI`. *(`ENTITY-PASS` was on this list until R11 retired it. The tagging survives it — that is `INGEST`'s, and it stays.)*
- **The `entities:` tag on sources** — kept explicitly by R11 when the pages go. CORPUS publishes it as a catalogue column and counts a region's institutions with it.
- **Quality & gaps loops:** `ACQUIRE`, `RECONCILE`, `PRUNE`.
- **Finance/budget record collection:** the sweeps and extractors named in R4.
- **`outputs/non-state-finance/` and the compile that writes it** — `build-finance-page.py`, `FINANCE-COMPILE` step 4, `compile-hub-financing.py`. Carved out of R4 and R6 by Bill's ruling of 2026-08-16: they are no longer a website feed, but checks A–E and the hub `## Financing` prose all read them, and they are OSINT's own.
- **The wiki:** `HUB-COMPILE` (hub prose), concepts, intersections, place hubs — CORPUS reads the place hubs and `wiki/intersections/` when it initialises a new report.
- **`LINT`** — vault hygiene, but **not unchanged**: #19 (mirror freshness) goes with the mirror at R8, #26 (output freshness) narrows to the finance exports at R2, and #4's referrer bands are rewritten at R11. Everything else stands.
- **`raw/`, `lookups/`, `wiki/`** — committed and stable; these are the evidence CORPUS reads, from the working tree through its workroot junctions. **`index/`** it does not read at all: it builds its own.

## Sequencing

**Two things come before the numbered order.** R10's boundary sentence goes into `CLAUDE.md` first, because every session that actions the rest needs it. Then R8's live half — commit the mirror deletion and cut the dead close step — because until that is done the cycle's last command points at a file that is not there, and `LINT` #19 reports a failure that is not real.

**Both rulings this list was waiting on have been made** *(Bill, 2026-08-16)*. Carving the non-state CSV out of R4 and R6 is why R4 is now a change of purpose, R5 is nothing to do, and R6 retires two folders instead of four. All backups being CORPUS's is why R8 is unconditional and `LINT` #19 goes without a repoint. Nothing on the list is blocked on a decision.

R1, R2, R3 and R6 are the report layer and can go together. R4 is a documentation change and can go with them or before them; **R5 needs no change at all**, and is worth reading only to know which seam not to cut later. **R9 is withdrawn** *(Bill, 2026-08-16, `documentation/osint-no-request-feed.md`)* — skip it; the gaps loop reaches OSINT as a session brief instead, not a file OSINT reads. R11 is independent of all of it and can go at any point, provided its own precondition — the 291-row region lookup — lands before the pages do. R10's pruning last, once the shape is settled.
