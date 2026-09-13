# Country budget batch — orchestrator

**Initialises one country** across **FY2024, FY2025 and FY2026**, then extracts every staged country-year and drains what that produced. **Trigger: "run the country budget batch for `<country>`"** — e.g. *run the country budget batch for Côte d'Ivoire*.

**No year argument. The years are fixed: 2024, 2025, 2026.** A bare year means the year the fiscal year begins (`DOMESTIC-FINANCE-SWEEP.md`), so this is FY2024/25, FY2025/26 and FY2026/27 in South Africa and Kenya, and calendar 2024/2025/2026 in Nigeria and Côte d'Ivoire — one instruction, three fiscal years, every country.

**This is an initialiser, not an updater.** It assumes the wiki holds **nothing** for the country and builds the first three years from scratch. It does not check what is already held, does not skip a year that is covered, and does not reconcile against a prior build. **Never run it on a country already initialised** — it re-sweeps ground the wiki has, and the drain then spends its budget on dedup.

**Which country runs is not decided here.** Invoked by name, it is Bill's choice; invoked by `SWEEP-COUNTRY-BUDGET.md`, it is the next blank row of `lookups/budget-init-backlog.csv`. This file takes a country and initialises it — it holds no queue and no order. **Nothing else calls it.**

**Bringing an already-initialised country forward is a separate process, and it does not exist yet.** That process has to read what is held before it acts — which year stages are complete, which documents are archived `re_extract`, which contradictions are open — and sweep only the gap. Do not extend this file to do it; the two have opposite starting assumptions.

**Called from the sweep, step 5 is not run per country.** The cycle owns a single ingest over the whole night's catch (`SWEEP-CYCLE.md` → *Ingest, once, at the close*), so the batch ends at step 4 with its records staged in `new/`. Steps 1–4 are unchanged and none is optional — **`new-budget/` must still be empty before a country is called finished.**

**"Budget", not "finance".** In this vault **finance covers both state and non-state** — `FINANCE-COMPILE.md` aggregates the two on every hub, and `finance_origin` is the field that separates them. This batch touches only the **domestic-state** half: appropriations, outturns and audits from a state's own budget documents.

**A sweep is never separated from its extraction.** A domestic finance sweep leaves `new-budget/` populated by design — staging is where it stops — so **the sweeps and the budget-extract are one invocation**, and `new-budget/` is empty when it finishes; no later pass inherits anything. Acquiring documents and reading them are halves of one job, and the three hours this file budgets are mostly the reading.

## Steps, strictly in order, one writer at a time

1. **Domestic finance sweep, FY2024** (`DOMESTIC-FINANCE-SWEEP.md`) — this country, that fiscal year. Stages budget documents to `new-budget/{ISO3}/2024/` and prose candidates to `new/`. **Stage-only.**
2. **Domestic finance sweep, FY2025** — same country. Stage-only.
3. **Domestic finance sweep, FY2026** — same country. Stage-only.
4. **Budget extract** (`BUDGET-EXTRACT.md`) — **the step the batch exists for.** It drains **every** country-year now staged in `new-budget/` — reading the documents, running the cross-vote scan, reconciling the three years against each other, building finance records and source pages into `new/`, and archiving each document to `budget-archive/{ISO3}/{FY}/`. It ends at `new/`; it does not call ingest.

   **The batch is not finished until `new-budget/` is empty.** An unextracted PDF is inert. If this step is cut short with country-years still staged, the batch has failed, not merely paused — say so, and finish it with `run budget extract` before anything else touches the vault.
5. **Update wiki** (`UPDATE-WIKI.md`) — the drain. Its first ingest admits the records step 4 staged into `new/` (and self-runs finance compile), then it reconciles and acquires, looping until the three queues are empty. **It does not lint** — run `full lint` after the batch if the run warrants one.

**Extraction is its own step, not the drain's first pass.** `update wiki` is purely the drain — it never touches `new-budget/`, so a batch that dies mid-extraction cannot be papered over by a later unrelated `update wiki` quietly picking the documents up.

**Expect the three years to be uneven, and do not treat that as failure.** FY2026 is current, so it will usually hold an appropriation and little else; FY2024 is the year most likely to carry a complete chain. A full chain for 2024, appropriation-plus-outturn for 2025 and appropriation only for 2026 is the **expected** shape, not a short run.

**Same country every time.** Different countries do not share a drain: their country-years reconcile against each other's documents in the extraction, and mixing them is how a cross-foot silently straddles two states. One country per invocation.

## Why sweep all three years before extracting any

Budget documents answer each other **across** years, and the extraction is where that pays:

- A year's **revised** stage is often only in the *next* year's volume — the comparator column (archetype M, SIM_ba variant, in the strategy library `documentation/budget-extraction-strategies.md`). **The FY2026 sweep is what closes FY2025's revised stage**, and is worth running even when FY2026 itself yields only an appropriation.
- The **audit** of year N is published during year N+2, so a 2024–2026 window is what makes a complete appropriated → revised → executed → audited chain likely for the oldest year.
- Extraction reconciles a country's own documents against one another; having all three years in front of it at once is the difference between a reconciliation and a guess.

So: **sweep wide, extract once** — the sweep cycle's stage-then-process-once (`SWEEP-CYCLE.md`), applied to years instead of sweeps.

## The budget-line record — specified

The record this batch emits is specified in `wiki/finance-load-domestic-state.md`: **one record per country × year × vote × programme-line**, accreting its stages (proposed → appropriated → revised → released → actual → audited) in a `## Stage history`, keyed on a stage-less `deal_id` — the domestic-state analogue of the deal record. A line has a stable identity, case 5 (`BUDGET-EXTRACT.md` §5) resets against it, and `FINANCE-COMPILE.md` builds both the hub total and the per-country finance exports (`outputs/budgets/{ISO3}-budget.csv`) from the records. Budget-extract §3 hands each digital line to that driver.

## On interruption

Each sweep finalises **its own state** at its own last step, so a completed sweep has advanced its high-water mark. Re-running the batch re-sweeps only the unfinished years and re-drains what is staged; dedup absorbs the overlap. **`new-budget/` is the resume marker** — anything still in it is unfinished work, and the next `run budget extract` picks up exactly that (`BUDGET-EXTRACT.md` → *Scope of a run*). Safe to re-run; at worst a year is re-swept.

**If step 4 or 5 is what ran out of session**, do not re-run the batch — the sweeps are already done. Resume from where it stopped: `run budget extract` if `new-budget/` still holds a country-year, then `update wiki`. Nothing else drains `new-budget/`, so it will not clear itself.

## Concurrency

Never alongside the daily batch, another sweep, `update wiki`, or any session writing the vault — including a second invocation of itself, which is why `SWEEP-COUNTRY-BUDGET.md` finishes one country before starting the next. The sweeps and the drain each need exclusive access to `new/`, `new-budget/` and the shared worklists.

## Show progress as it runs

Per `STATUS.md` → *Progress*, a step banner before each — `▶ step 1/5: domestic finance sweep CIV 2024`, `▶ step 4/5: budget extract`, `▶ step 5/5: update wiki` — plus each step's own pass banners and broad counts. **Foreground, in the main session**, so it is watchable; a detached subagent hides the progress.

End on the standing status line (`STATUS.md`); each step also emits its own. A clean finish reads zero across all four gates, `new-budget/` included.
