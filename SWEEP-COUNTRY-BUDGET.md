# Sweep — country budget (procedure)

**Runs `COUNTRY-BUDGET-BATCH.md` over the next countries in the initialisation queue** — three a run, one at a time, in the order `lookups/budget-init-backlog.csv` holds. **Trigger: "run the country budget sweep".** **Suspended**: off the rotation (`logs/sweep-cycle_log.md` holds no row for it); runs by trigger only.

## 0. What it is, and what it is not

**It is wiring, not method.** Every rule about *how* a country's budget material is found, read and recorded lives in `COUNTRY-BUDGET-BATCH.md` and the processes it calls (`DOMESTIC-FINANCE-SWEEP.md`, `BUDGET-EXTRACT.md`). This file decides only **which countries run, in what order, and when one counts as done.**

**It is an initialiser, and so is everything it calls.** The batch assumes the wiki holds **nothing** for the country and builds FY2024, FY2025 and FY2026 from scratch. This sweep selects **only countries that have never been initialised** — never one already built.

**Bringing built countries forward is a separate, unbuilt process.** When the queue empties, this file's selection is rewritten against held state; it never loops back to the top (§10).

**It is not a fetching sweep.** It stages nothing itself, holds no search brief, runs no origin screen (`wiki/origin-screen.md`) — the sweeps the batch calls each run the screen themselves — and has no window.

## 1. The queue is the register — `lookups/budget-init-backlog.csv`

**That file is the queue.** This process holds no copy of it and names no country. Two columns, `iso-3` and `Budget Done`, one row per place in **run order**:

| value | meaning |
|---|---|
| `Yes` | initialised — never selected again |
| *(blank)* | pending — the queue |
| `n/a` | not a candidate. The eight `X` regions: a region has no national budget to initialise, and `DOMESTIC-FINANCE-SWEEP.md` is national-tier only. |

**Re-ordering the queue is a file edit**, never a process edit. One queue, no second register. The order carries no judgement about which country matters more.

**Three countries per run.** The one number this file states. Change it here.

## 2. Selection

Take the **first rows in file order whose `Budget Done` is blank** — three of them. Write **`Yes`** on a row only when that country passes §4's test; a country that stops short stays blank.

That is the whole interrupted-run mechanism: a blank row is re-selected next run and re-run from scratch (`COUNTRY-BUDGET-BATCH.md` → *On interruption*) — re-running re-sweeps only the unfinished years and dedup absorbs the overlap. There is no in-progress marker.

**Do not skip a country because it looks unpromising.** A microstate that yields one appropriation and nothing else has been initialised correctly, and the wiki then states the absence dated (`CLAUDE.md` → *Currency*).

## 3. What it runs — the batch, per country, sequentially

For each selected country, in order, run **`COUNTRY-BUDGET-BATCH.md` steps 1–4**:

1–3. domestic finance sweep FY2024, FY2025, FY2026 — stage-only, to `new-budget/{ISO3}/{year}/` and `new/`.
4. **budget extract**, scoped to that country's staged years — reading the documents, the cross-vote scan, the three-year reconciliation, records and source pages into `new/`, each document archived to `budget-archive/{ISO3}/{FY}/`.

**One country is finished before the next is started**: step 4 reconciles a country's documents *against each other* (`COUNTRY-BUDGET-BATCH.md` → *Same country every time*).

**Step 5 — `update wiki` — is not run per country.** In the cycle the parent owns the single `INGEST` Phase A pass at the close, over the whole night's catch (`SWEEP-CYCLE.md` → *Ingest, once, at the close*), and it drains the batch's records with everything else. **Run standalone, this sweep is stage-only like every other sweep**: it ends at `new/` and the caller drains it.

**Nothing else is skipped.** Steps 1–4 are the batch in full; step 4 is not optional (§4).

## 4. When a country counts as done

**`new-budget/{ISO3}/` empty and `budget-archive/{ISO3}/` holding 2024, 2025 and 2026.** Only then write `Yes` on its row.

`new-budget/` is the resume marker, and **a staged document is inert**. Marking a country done with documents still staged retires it from the queue with its three sweeps spent and no records built, so the test is the folders, not the sub-agent's word for it.

If a country stops short: leave the row blank, say so in the closing line, and name what is still staged. The next run re-selects it.

**Expect the three years to be uneven** — a full chain for 2024, appropriation plus outturn for 2025, appropriation only for 2026 is the *expected* shape, not a short run (`COUNTRY-BUDGET-BATCH.md`).

## 5. No window, and no state of its own

**This sweep ignores the window the cycle computes** (`SWEEP-CYCLE.md` → *The day's window*). The batch's years are fixed at 2024, 2025, 2026 and its unit is a country, not a date range.

The register is this sweep's only state.

## 6. Boundaries

**The containment boundary that applies is each called process's own, not the ordinary sweep boundary.** A fetching sweep writes only to `new/` and its own `sweep/` folder (`intake.md` §7); this one runs a batch whose step 4 writes `new/`, drains `new-budget/` and archives to `budget-archive/` — budget-extract's charter. **Nothing here writes to `raw/` or to any `wiki/` page**, and no record enters the base except through the ingest the caller runs.

The one file this sweep writes on its own account is `lookups/budget-init-backlog.csv` — and `logs/log.md` at the close.

## 7. Delegation

Per `SWEEP-CYCLE.md` → *Execution model*, **the caller spawns every agent this sweep uses and no sub-agent spawns another.** Under the cycle the caller is the cycle parent; run standalone it is the session itself.

- **One sub-agent per country**, labelled with its position and ISO-3 — `country-budget 2/3 COM`. It runs that country's steps 1–4 and returns one line.
- **Within a country, one sub-agent per fiscal-year sweep and one for the extract.** The extract is the long one and gets its own context.
- Every spawn carries the four standing lines (`SWEEP-CYCLE.md` → *What every sub-agent prompt carries*): the capture rule, the containment boundary, the current local date and time, and *a sub-agent runs a process, it does not amend one*.
- **Returns are one line**, always: `step=<name> stopped=<complete|context|error> staged=N dropped=N needs-clip=N remaining=N notes=<≤10 words>`. `stopped=context` on an extract means the country is **not** done (§4).

## 8. Duration and concurrency

**The batch runs about three hours per country**, most of it in step 4. The cycle has **no time envelope** (`SWEEP-CYCLE.md`), so this is not a fault to trim around; **if three is too many, §1's number is the edit.**

**Concurrency:** one country at a time, and no other session writing the vault. The batch inherits exclusivity over `new/`, `new-budget/` and the shared worklists.

## 9. Finishing

1. **Stage-only in the cycle** (§3) — the caller's ingest drains what step 4 built.
2. **Write the register** — `Yes` on each country that passed §4's test, and nothing on one that did not.
3. **One terse line to `logs/log.md`**, aggregating the countries' tallies:

   `YYYY-MM-DD hh:mm — country-budget sweep: <ISO3>, <ISO3>, <ISO3>; done N/3, took <Nh>; docs archived N, records staged N; queue remaining N.`

4. Anything for Bill → `reviews/post-run-notes.md`, numbered — a country whose documents are unreachable, a fiscal calendar the batch's fixed years fit badly, a run that stopped short twice.
5. **End on the standing status line** (`STATUS.md`).

## 10. The end state

When the register has no blank `Budget Done` left, **this sweep has nothing to do and says so and stops** — one line to `logs/log.md`, no work.

The updater form is a rewrite of §2 and §3 against held state — which years are complete, which documents are archived `re_extract`, which contradictions are open — and it is the process `COUNTRY-BUDGET-BATCH.md` says does not exist yet. **Do not anticipate it here**, and never let selection quietly start choosing built countries: an initialiser that has become an incremental pass no longer initialises anything.
