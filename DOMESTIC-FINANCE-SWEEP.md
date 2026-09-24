# Domestic-state finance sweep — procedure

**Acquisition sweep for one country and one fiscal year**, gathering the budget documents CORPUS extracts from and the wiki catalogues as sources: budget documents, outturn and audit reports, ministerial statements, on-the-record reporting of state digital spending.

**Invocation: "run domestic finance sweep for `<country>` `<year>`"** — e.g. *run domestic finance sweep for South Africa 2024*.

**A bare year means the year the fiscal year begins**: `2024` in Nigeria, `2024/25` in South Africa and Kenya, the Ethiopian year beginning July 2024. **State the resolution at the top of the run** ("South Africa 2024 → FY2024/25, 2024-04-01 to 2025-03-31").

## The unit is country × fiscal year

One country, one fiscal year, one run — the driver's grain of one line, one year, one stage. Re-run the same invocation as the year matures to pick up the stages that did not exist the first time. Coverage is a matrix of country × fiscal year × stage; a gap is stated, dated, on the page (`CLAUDE.md` → *Currency*).

**In scope: fiscal years beginning on or after 1 January 2024.** Earlier years are out however easily found; staging one is a regression. Kenya's first in-scope year is 2024/25.

### The fiscal year is a search target, not a filter on what gets built

**A document covering several years is fetched once and kept whole.** Record every year in `fiscal_years_covered`, dedup on URL across runs, and let extraction take whichever years it supports.

**Statements and reporting are date-windowed, not fiscal-year-filtered**; `fy` blank with the reason noted is a valid record.

- **Blocks 1–3 (documents)** — hard-scoped to the run's fiscal year.
- **Blocks 4–7 (statements, reporting, scrutiny)** — a **date window** from six months before `fy_start` to twelve months after `fy_end`; extraction assigns the year where it can.

## Boundaries

- **Acquisition, not record-building.** No five-fact test, no budget lines, no deal records. The only question is *is this document worth holding*.
- **National tier only.** `state_level: sub-national` stays in the driver; when turned on it is a separate invocation with its own cap. Own-source national bodies — universal service funds, ICT levy bodies, regulators — **are** in scope.
- **Containment** (`intake.md` §7): writes only to `new/`, `new-budget/` and its own `sweep/domestic/` state. Never to `raw/` or any `wiki/` page.
- **Distinct from the daily trade-journal sweep and the digest.**

## Two tracks

Exa is strong on prose and weak on budget PDFs on ministry-of-finance domains. **Never read a thin document harvest as evidence that the documents don't exist.**

### Track A — fiscal institutions, domain-scoped

Domain-scope every query to the country's own institutions. Where a track leaves that scope — reporting, Track B — **run the origin screen (`wiki/origin-screen.md`)** on every hit.

| Role | Typical holder |
|---|---|
| Budget authority | Ministry of Finance / Budget Office / Treasury |
| Execution and release | Treasury; budget controller |
| Legislature | National Assembly / Parliament; parliamentary budget office |
| Audit | Auditor-General / Cour des comptes |
| Sector ministry | Ministry of ICT / Digital Economy / Communications |
| Sector regulator | Communications/ICT regulator (own budget, spectrum-funded) |
| Own-source funds | Universal service fund; ICT development levy body |
| Programme owners | National ID authority; e-government agency; statistics office |
| **Other spending ministries** | **Justice, home affairs, revenue/customs, correctional services, health, education — they run large systems and never call it "digital" (Block 4b)** |
| **Procurement portal** | **Public-procurement authority — annual procurement plans** |
| Portal | The government's own open-budget or IFMIS portal |

Also scope the country's **IMF Article IV and programme documents** for aggregates and execution rates.

### Track B — direct enumeration

For the budget authority, the procurement portal and the open-budget portal, fetch the **document library page** directly and take the links matching the run's fiscal year. One fetch of an index page beats ten semantic queries.

A document not reached in one attempt goes to `reviews/acquisitions.md` (`CLAUDE.md` → *Working the base*). One attempt, then a stated absence.

## Semantic context — the query blocks

**Separate queries**, never blended. Substitute the country's own vocabulary from its section in the extraction notes. In Francophone, Lusophone and Arabophone states **query in the document's language**.

**Block 1 — the appropriation.** *Approved budget estimates and appropriation act for the fiscal year, showing votes, heads and programme allocations by ministry, department and agency.* Scope: budget authority, legislature. Look for estimates volumes, the act as assented, the budget speech and its annexes.

**Block 2 — execution and outturn.** *Budget implementation and expenditure review reporting actual spending against approved allocations by ministry and programme, including exchequer releases and absorption rates.* Scope: treasury, budget controller, legislature. Weight the effort here.

**Block 3 — audit.** *Auditor-general's report on the financial statements of ministries and agencies, including irregularities in ICT and systems procurement.* Scope: audit institution, legislature.

**Block 4 — the digital line, from the sector side.** *Government allocation and spending on digital transformation, e-government, digital identity, national data centre, connectivity and ICT systems in the national budget.* Scope: sector ministry, regulator, funds, national press.

**Block 4b — the digital line in OTHER ministries.** *Allocations for case management and court modernisation, prison and border systems, tax and customs administration systems, integrated financial management, statistical modernisation, health and education information systems.* Scope: justice, home affairs, treasury/revenue, statistics, health, education, correctional services — **not** the ICT ministry. Without this block every run inherits a one-vote bias.

**Identity and data exchange are almost never in the ICT vote.** Query them by name — both are DPI (`dpi.id`, `dpi.exchange`):

- **Identity** — population register, civil registration and vital statistics, CRVS, national identity card, biometric enrolment, ABIS, passport and travel document systems, voter register, social-registry and beneficiary registries. Usually home affairs, interior or an identity authority.
- **Data exchange** — interoperability framework or layer, government service bus, API gateway, data-sharing platform, integrated/shared services platform, master data management, single window (trade), one-stop government portal. Usually the finance or public-service ministry, or a cross-government delivery unit.

**Block 4c — governance structures and processes.** *Budget of the data protection authority or information regulator; the ICT or communications regulator; the cybersecurity agency or national CSIRT; digital transformation, e-government coordination or delivery units; statistical governance; the cost of establishing a new authority, drafting legislation, standards work and public consultation.* It sits in *Administration*, *Policy* or *Corporate services* programmes, where Blocks 1–4 miss it. For a single-mandate body the total budget *is* the digital line, recorded at `scope_confidence: whole` (`wiki/finance-load-domestic-state.md` → *Scope*); the test is the mandate, not the name. Donor-funded governance spend lands as `non-state` — capture it. A levy-funded regulator is Block 6. **An authority established in law and never appropriated for is the finding, not the failure: record the absence, dated, on the place hub.** Where the country has a data protection law, look for the authority's line deliberately and say what was found — including nothing.

**Block 5 — statements and clarifications.** *Minister's, permanent secretary's or head-of-state's statement or decree authorising expenditure on a named digital programme — its cost, its funding source, its implementation status.* Scope: sector ministry, budget authority, presidency, national press. Include **executive instruments by their local name** — *despachos presidenciais*, procurement authorisations, supplementary-credit orders.

**Block 6 — own-source bodies.** *Universal service fund, ICT levy and regulator budgets, their approved expenditure and their annual reports.* Scope: funds, regulator, sector ministry.

**Block 7 — contest and scrutiny.** *Parliamentary committee questioning, civil-society budget analysis or investigative reporting on digital-programme spending, cost overruns and procurement.* Scope: legislature, national press, budget-transparency organisations. **Analysis is a lead** — mine it for the primary it cites (`CLAUDE.md` → *The material*); on-the-record investigative reporting is a source.

## The extraction notes — apply at capture

`documentation/domestic-budget-extraction.md` **must be read before querying**. Four standing rules:

- **Query for phrases, not headlines**: `allocated / also allocated / également alloué / financés à hauteur de / a coûté / aprovou a despesa / autorizou a despesa / crédito adicional suplementar`. Domestic figures hide mid-paragraph inside stories about something else.
- **"Government invests" headlines are usually external money.** Not the sweep's call: stage the funding-source language in the companion page for the driver's origin gate.
- **A ministry's total vote is not a record.** Stage it, flag it, and spend no more cap on envelopes once the pattern is established for that country.
- **Multi-year plan envelopes always fail as records.** The acquirable unit underneath is the annual finance law's programme annexe — *loi de finances annexes*, *lettres d'engagement*. **Add those to `reviews/acquisitions.md` by name** when a plan envelope is all that surfaces.

Append to the country's section after every run, including what was searched and found nothing.

## Priority and stopping

**Run from `BUDGET-COLLECT.md`, the scope is tiers 0–3 plus own-source funds and the data-protection authority's budget (Blocks 4c and 6)**; the prose blocks run only where they are cheap.

**Cap: 40 items per country-year run.** Take documents in this order and stop early once tiers 1–3 are exhausted:

0. **The full estimates volume (all votes)** — the only instrument for the cross-vote scan; fetch it even though its sector chapter duplicates the standalone extract.
1. Appropriation act / approved estimates for the run's FY
2. Budget implementation / outturn report for the run's FY
3. Auditor-general report covering the run's FY
4. Budget speech, MTEF or fiscal strategy naming the run's FY
5. Executive instrument or official statement on a named digital programme
6. Procurement plan; own-source-fund budgets and annual reports
7. Reporting and scrutiny on any of the above

Eight documents covering appropriation *and* outturn beat forty news items.

**Dedup before fetching**: grep `raw/` and `new/` for the URL and the programme names — exact URL or confident re-crawl only (`intake.md` §7). On a re-run most of tier 1 is already held; that is success.

## Staging

**The split is by what a thing is, not by its file extension.**

- **Prose sources → `new/`** — news, statements, press releases, decrees, investigative reporting. Flat, date-prefixed, best-effort frontmatter; the driver's case-4 material.
- **Budget documents → `new-budget/{ISO3}/{FY}/`** — the artefact **and its companion markdown together, same folder, same date prefix**. **`{FY}` is always the bare start year** — `new-budget/ZAF/2024/`, never `2024-25` (`layout.md` §2). A companion page never goes to `new/` alone: the pair's folder is its state, *held, not yet extracted* (`CLAUDE.md` → *Structure*).

**Nothing in `new-budget/` counts as `awaiting ingest`**, and ingest never drains it (`layout.md` §2, §7). **A `new-budget/` folder existing always means work outstanding.** Append a row for each document staged to **`new-budget/{ISO3}/manifest-rows.csv`**, never straight to the shared `new-budget/manifest.csv`; the batch merges it at the close:

`iso3, fiscal_year, fiscal_years_covered, doc_type, title, url, artefact_path, companion_path, retrieved, scale, currency, pages, extracted, extracted_scope, re_extract, archive_path, notes`

The sweep fills everything up to `pages`; `BUDGET-COLLECT.md` sets the paths and `archive_path` when it files the document. `extracted` stays blank: extraction is CORPUS's.

Prose candidates carry `retrieved:` and never `ingested:` (`intake.md` §7).

```yaml
---
type: source
title: <document's own title, verbatim, in its own language>
url: <canonical URL>
publisher: <the institution, not the portal>
published: <publication date; padded + date_precision per layout.md §3>
date_precision: day
date_source: source
places: [<ISO-3>]
topics: [finance.budget, <sector slug where evident>]
entities: [[<institution-slug>]]
retrieved: <YYYY-MM-DD>
sweep_batch: domestic-finance-<ISO3>-<FY>-<YYYY-MM-DD>   # FY = bare start year, e.g. 2024
fiscal_years_covered: ["2024/25", "2025/26"]
doc_type: <one value from the canonical list in wiki/finance-load-domestic-state.md
           → Source citation. Do not extend it here — one vocabulary, one home.>
source_tier: <budget-document | official-statement | project-document | reporting>
artefact: <sibling filename, where this is a companion page in new-budget/>
body_completeness: <full | excerpt>
---
```

A companion page in `new-budget/` is **not yet a source** — no `ingested:`, not linked from any wiki page; it becomes one when `BUDGET-COLLECT.md` step 2 catalogues it into `new/`. **For a tabular or PDF artefact** it also records the **sheet/tab, header row, printed scale and currency** — the scale header (`N'000`, *en milliers*, "bilião") is the 1,000× error; capture it at staging.

## Close

**Write the run file first — the run's state object.** `sweep/domestic/<ISO3>-<FY>-run-<date>.md`: what was staged, the stage-coverage table, the re-run triggers. A completed run with no run file reads as a missing run.

Then terse per `CLAUDE.md` → *Reporting*: documents staged by `doc_type`, items sent to acquisitions, what was appended to the extraction notes, **which fiscal-year stages remain uncovered**, and **whether the full estimates volume was obtained** — if not, every total downstream must say the run supports sector-vote coverage only. Then the status line.

**The sweep ends at staging.** `BUDGET-COLLECT.md` catalogues and archives what it staged; a sweep run outside that batch leaves `new-budget/` populated until the batch's steps 2–3 are run for the country. Nothing else drains it.
