# Token-reduction tasks — 2026-08-10

Context: weekly Max limit now binding; country budgets iced; nightly sweeps must run ≥5 nights/week within budget. Scope of the project is collection, classification, and the nightly refresh of outputs\ (excluding outputs\budgets\ while finance is suspended) — the outputs feed the website and are its USP; their currency is non-negotiable. Theme of this round: the 2026-08-02 review's caps were written in prose and broke within a week (60-word note cap ignored; log.md regrew 852 KB → 1.41 MB in 7 days). This time every limit is enforced by script or removed. Work these in four separate sessions, not one — a single session will exhaust context and degrade on the later tasks. Session 1: sections A, B (except 7) and C — spec and procedure edits. Session 2: task 7 alone — the backlog triage. Session 3: sections D and F, plus 20a and 24 — cadence, catalogue fix, runner, repo weight. Session 4: section E remainder — the model trial and subagent setup. Mark each task done with a one-line log entry; a session that finishes early does not pull tasks from a later session.

## A. Reporting and logs

1. Log entries become telegraphic one-liners: `date · pass · what · revert-hint`. Rewrite the log-entry spec in CLAUDE.md and STATUS.md accordingly. Target 10:1 compression on current practice. Logs are for CC's own recall, not for Bill.
2. Mechanical log rotation: script truncates logs/log.md to the last ~400 lines at every cycle close (git holds the rest). Wire it into SWEEP-CYCLE close, not into prose.
3. On-screen close report = the single STATUS count line plus run-cost line. Delete every mandated explanation (e.g. INGEST's "a non-zero uncited-sources reading is not optional to explain" → one line + note instead).
4. Resolve the struck-note retention contradiction: CLAUDE.md says 14 days, post-run-notes.md says 3. Make it 3 everywhere.

## B. Post-run notes and housekeeping

5. Enforce the 60-word note cap in scripts/lint-deterministic.py: over-length notes are flagged and truncated at next cycle. Notes 144, 148, 165, 178, 201 currently run 150–300+ words.
6. Only [DECIDE] items enter post-run-notes.md. [FYI] becomes a log one-liner; [FETCH] already goes to fetch-list.md. Cap open [DECIDE] at 10: at the cap, CC takes the conservative option itself and logs it, per "Act. Log after. Never ask."
7. One triage session over the current backlog (41 open notes, 20 housekeeping jobs): close everything CC can close, delete anything untouched a month per CLAUDE.md's own rule. Exit state ≤10 notes, ≤5 jobs.
8. Housekeeping intake bar: a job is registered only if it names the script or the session that closes it. Anything else is deleted at intake.

## C. Edge-case cuts — the 95/5 rule

Principle: one instrument, one attempt, rule over judgement. A miss self-corrects next sweep; dedup catches the echo.

9. SWEEP-DAILY-LIST: single instrument per domain. Drop the two-instrument nil-verification and the mandatory cache-busted refetch. A nil from one listing is a nil.
10. SWEEP-DAILY-LIST: one query cluster per domain, numResults 25 → 10. Keep FR/AR variants only for domains that have actually produced non-English hits; drop them elsewhere.
11. Truncated capture: no retry fetch. One-line flag, move on.
12. INGEST: drop the second origin screen for items that arrived via sweep — the sweep already ran it.
13. INGEST tier-3 dedup by rule, not model judgement: same event, different outlet → drop unless the newcomer is a clear tier upgrade (primary over secondary, full body over excerpt). "Replace" stays rare; "keep both" needs a stated payload difference in one line.
14. Slice death: requeue only. Files still in new/ are the resume state by construction; delete the three-step new/-vs-raw/ reconcile.
15. Gap probes leave routine runs (note 201: ~20% of a run's cost). They belong to the acquire pass alone.
16. Strip the two embedded 2026-08-09 incident narratives from INGEST.md; distil each to one rule line or move to reference.md. Cap INGEST.md at 250 lines. Extend "no new rule without deleting one" to every root procedure file, enforced by a line-count check in lint-deterministic.

## D. Cadence — ration passes, not item quality

17. LINT: deterministic checks (script, ~1s) nightly; all model-performed checks move to one weekly session. The 08-02 review already named nightly model-lint the single largest recurring cost.
18. Hub recompiles: nightly only where a hub feeds a nightly output; weekly or on demand elsewhere (adjust SWEEP-CYCLE accordingly).
19. Formally suspend the domestic-state budget layer only: mark DOMESTIC-FINANCE-SWEEP, BUDGET-EXTRACT, SWEEP-COUNTRY-BUDGET and COUNTRY-BUDGET-BATCH suspended in wiki/index.md, and remove their touchpoints from lint and status so the iced layer stops leaking cost into live passes. The non-state layer is untouched and stays nightly: SWEEP-FINANCIERS, SWEEP-IATI, and FINANCE-COMPILE / FINANCE-PAGES — which build outputs\non-state-finance\ — remain live; while suspended they skip only the domestic budget export, leaving the last-built budget CSVs frozen in place, not deleted.
20. Nightly output refresh is a first-class phase of the cycle: everything under outputs\ except outputs\budgets\ regenerates every run. Script-driven compilation (report-render.py, build-catalogue.py, compile-hubs.py) does the bulk; model-written narrative blocks are the expensive part, so cap them at N per night, oldest-stale first, and drain the "(narrative not yet written)" backlog under that cap rather than in one costly push. A run that hits budget stops narratives first, never the script-driven refresh.
20a. Catalogue staleness — immediate: outputs\catalogue\ last updated 2026-08-03 while reports\ and non-state-finance\ ran 2026-08-10, so build-catalogue.py has dropped out of the cycle. Rerun it now, find why SWEEP-CYCLE stopped invoking it, and rewire it into cycle close.
20b. Output freshness check in lint-deterministic (pattern of lint-mirror-freshness): every outputs\ subfolder except budgets\ must have file mtimes newer than the last cycle; a stale folder is a [DECIDE] note, not a silent drift.

## E. Models and automation

21. Default model Sonnet for every pass. No pass invokes Opus by default.
22. Opus trial before Opus spend: run ~20 ingest items through Sonnet and Opus separately, diff the dispositions and frontmatter. Keep Opus only for steps where Sonnet materially errs — expected candidates are tier-3 replace/keep judgement and contradiction reconciliation, nothing else.
23. If the trial justifies it, define a declared subagent in .claude/agents/ (e.g. `adjudicator`, `model: opus`) invoked only for those steps. A Sonnet session spawning an Opus subagent is supported natively — this removes the "can't change model mid-stream" constraint without splitting the night into manual jobs.
24. Recreate the overnight runner: a .bat that runs `claude -p "run the sweep cycle" --model sonnet` with the preflight the old runner had — the cycle covering sweep → ingest → output refresh (task 20) — then mirror.bat. Hand-triggered only, always — no automatic or scheduled trigger of any kind; that was never agreed and a stray one built 2026-08-10 caused a real incident (`logs/log.md`, 2026-08-11).
25. Nightly sub-agent budget: replace the flat 200-cap with a budget derived from the weekly limit ÷ 7 nights of headroom; at budget, the run stops clean at a slice boundary and logs one line — it never part-completes narratives or explanations.

## F. Repo weight

26. .git is 5.2 GB of a 15 GB repo: run `git gc --aggressive` / repack, and move budget-archive/ (6.3 GB) outside the repo while the finance layer is suspended — the FreeFileSync mirror covers it.
27. Update wiki/index.md → Processes in the same edits as every change above, per CLAUDE.md.

## G. Amendments (added 2026-08-10, after session 4 started)

28. Supersedes task 25's stop-at-budget rule (Bill's ruling, 2026-08-10): a run that exceeds its nightly budget **completes the entire job** — nothing is cut, including narratives — and raises a [DECIDE] note stating the overrun size and where it went. The budget is a monitor and an alarm, never a brake. Amend whatever task 25 put in place (SWEEP-CYCLE, STATUS.md, runner) to match; if task 25 is not yet implemented, implement it in this form directly. Task 20's "stops narratives first" clause falls with it.
