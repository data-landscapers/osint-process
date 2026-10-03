<!-- reader: cc; type: runbook -->
# Domestic-state finance sweep

**Invocation: "run domestic finance sweep for `<country>` `<year>`"**: a country-year's budget, outturn and audit documents, ministerial statements and on-the-record reporting of state digital spending.

**A bare year is the year the fiscal year begins**: `2024` in Nigeria, `2024/25` in South Africa and Kenya, Ethiopia's from July 2024. **State the resolution, with its dates, at the top of the run.**

## The unit is country × fiscal year

Re-run as the year matures, for new stages. A stage-coverage gap is stated, dated, on the page (`CLAUDE.md` → *Currency*).

**In scope: fiscal years beginning on or after 1 January 2024** (Kenya: 2024/25); staging earlier is a regression.

**A multi-year document is fetched once, kept whole, every year in `fiscal_years_covered`**, deduped on URL across runs. **Blocks 1–3 (documents)** are hard-scoped to the fiscal year; **Blocks 4–7 (statements, reporting, scrutiny)** are **date-windowed**, `fy_start` minus six months to `fy_end` plus twelve; `fy` blank with the reason noted is a valid record.

## Boundaries

- **Acquisition, not record-building**: no five-fact test, budget lines or deal records — only *is this document worth holding*.
- **National tier only**; `state_level: sub-national`, when turned on, is a separate invocation with its own cap. Own-source national bodies (service funds, levy bodies, regulators) **are** in scope.
- **Containment** (`intake.md` §7): writes only to `new/`, `new-budget/` and its own `sweep/domestic/` state — never `raw/` or `wiki/`.
- **Distinct from the daily trade-journal sweep and the digest.**

## Track A — fiscal institutions

**A thin harvest is not evidence the documents don't exist** — Exa is weak on finance-ministry PDFs. Domain-scope every query to the country's institutions; beyond them — reporting, Track B — **run the origin screen (`wiki/origin-screen.md`)** on every hit.

| Role | Typical holder |
|---|---|
| Budget authority; execution | Ministry of Finance, Budget Office, Treasury; budget controller |
| Legislature; audit | Parliament, its budget office; Auditor-General / Cour des comptes |
| Sector | ICT ministry; ICT regulator (own, spectrum-funded budget) |
| Own-source funds | Universal service fund; ICT levy body |
| Programme owners | National ID authority; e-government agency; statistics office |
| **Other spending ministries** | **Justice, home affairs, revenue/customs, corrections, health, education: large systems, never called "digital" (Block 4b)** |
| **Procurement portal** | **Procurement authority's annual plans** |
| Portal | Open-budget or IFMIS portal |

Also scope **IMF Article IV and programme documents** (aggregates, execution rates).

## Track B — direct enumeration

For the budget authority and the procurement and open-budget portals, fetch the **document library page** and take the fiscal year's links. A document not reached in one attempt goes to `reviews/acquisitions.md` (`CLAUDE.md` → *Working the base*), then a stated absence.

## The query blocks

**Separate queries**, never blended, in the country's own vocabulary — in Francophone, Lusophone and Arabophone states, **in the document's language**.

**Block 1 — appropriation.** *Approved estimates and appropriation act: allocations by vote, head, programme and agency.* Scope: budget authority, legislature — estimates volumes, assented act, budget speech.

**Block 2 — execution and outturn.** *Implementation reviews: actual against allocated spending, exchequer releases, absorption rates.* Scope: treasury, budget controller, legislature. Weight the effort here.

**Block 3 — audit.** *Auditor-general's report on ministry and agency accounts and ICT procurement irregularities.* Scope: audit institution, legislature.

**Block 4 — the digital line, sector side.** *Spending on digital transformation, e-government, digital identity, national data centre, connectivity, ICT systems.* Scope: sector ministry, regulator, funds, press.

**Block 4b — the digital line in OTHER ministries.** *Court case management, prison and border systems, tax and customs, IFMIS, statistical modernisation, health and education information systems.* Scope: the table's other spending ministries and statistics — **not** the ICT ministry.

**Identity and data exchange (DPI: `dpi.id`, `dpi.exchange`) are almost never in the ICT vote.** Query them by name:

- **Identity** — population register, CRVS, national ID card, biometric enrolment, ABIS, passport systems, voter register, social and beneficiary registries. Usually home affairs, interior or an identity authority.
- **Data exchange** — interoperability layer, government service bus, API gateway, data-sharing or shared-services platform, master data management, trade single window, one-stop portal. Usually finance, public service or a delivery unit.

**Block 4c — governance structures.** *Budgets of the data protection authority, ICT regulator, cybersecurity agency or CSIRT, digital delivery units, statistical governance; the cost of a new authority, legislation, standards, consultation.* Look under *Administration*, *Policy* or *Corporate services*. A single-mandate body's total budget *is* the digital line, at `scope_confidence: whole` (`wiki/finance-load-domestic-state.md` → *Scope*): the mandate decides, not the name. Donor-funded governance spend is `non-state` — capture it; a levy-funded regulator is Block 6. **An authority established in law and never appropriated for is the finding, not the failure: record the absence, dated, on the place hub.** Where a data protection law exists, seek the authority's line deliberately; report even a nil.

**Block 5 — statements.** *Ministerial or presidential statement or decree authorising spending on a named digital programme: cost, funding, status.* Scope: sector ministry, budget authority, presidency, press. Include **executive instruments by local name** — *despachos presidenciais*, procurement authorisations, supplementary-credit orders.

**Block 6 — own-source bodies.** *Universal service fund, ICT levy and regulator budgets and annual reports.* Scope: funds, regulator, sector ministry.

**Block 7 — scrutiny.** *Committee questioning, civil-society budget analysis, investigative reporting on digital-programme spending, overruns, procurement.* Scope: legislature, press, budget-transparency bodies. **Analysis is a lead**, mined for its primary (`CLAUDE.md` → *The material*); on-the-record investigative reporting is a source.

## Capture rules

- **Query for phrases, not headlines**: `allocated / also allocated / également alloué / financés à hauteur de / a coûté / aprovou a despesa / autorizou a despesa / crédito adicional suplementar`.
- **"Government invests" headlines are usually external money.** Not the sweep's call: stage the funding-source language in the companion for the origin gate.
- **A ministry's total vote is not a record.** Stage and flag it; once the country's pattern is clear, spend no more cap on envelopes.
- **Multi-year plan envelopes always fail as records.** If one is all that surfaces, **add the annual finance law's programme annexes to `reviews/acquisitions.md` by name** — *loi de finances annexes*, *lettres d'engagement*.

## Priority and stopping

**Run from `BUDGET-COLLECT.md`, the scope is tiers 0–3 plus own-source funds and the data-protection authority's budget (Blocks 4c, 6)**; prose blocks run only where cheap.

**Cap: 40 items per run.** Take the FY's documents in this order, stopping once tiers 1–3 are exhausted:

0. **The full estimates volume (all votes)** — the only instrument for the cross-vote scan; fetch it even if its sector chapter duplicates a standalone extract.
1. Appropriation act / approved estimates
2. Budget implementation / outturn report
3. Auditor-general report
4. Budget speech, MTEF or fiscal strategy
5. Executive instrument or official statement on a named digital programme
6. Procurement plan; own-source-fund budgets and annual reports
7. Reporting and scrutiny on any of the above

**Dedup before fetching**: grep `raw/` and `new/` for URL and programme names — exact URL or confident re-crawl only (`intake.md` §7).

## Staging

**Split by what a thing is, not its extension.**

- **Prose sources → `new/`** (news, statements, releases, decrees, investigative reporting; the driver's case-4 material): flat, date-prefixed, best-effort frontmatter, `retrieved:` and never `ingested:` (`intake.md` §7).
- **Budget documents → `new-budget/{ISO3}/{FY}/`** — artefact **and companion markdown together, same folder, same date prefix**. **`{FY}` is always the bare start year** — `new-budget/ZAF/2024/`, never `2024-25` (`layout.md` §2). A companion never goes to `new/` alone; the pair's folder is its state, *held, not yet extracted* (`CLAUDE.md` → *Structure*).

**Nothing in `new-budget/` counts as `awaiting ingest`** or is drained by ingest (`layout.md` §2, §7). **A `new-budget/` folder always means work outstanding.** Append a row per document to **`new-budget/{ISO3}/manifest-rows.csv`**, never the shared `new-budget/manifest.csv`, which the batch merges into at the close:

```csv
iso3, fiscal_year, fiscal_years_covered, doc_type, title, url, artefact_path, companion_path, retrieved, scale, currency, pages, extracted, extracted_scope, re_extract, archive_path, notes
```

The sweep fills up to `pages`; `BUDGET-COLLECT.md` sets the paths and `archive_path` on filing; `extracted` stays blank (extraction is CORPUS's).

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
doc_type: <one value from the closed list in lookups/budget-doc-types.csv.
           Do not extend it here — one vocabulary, one home.>
source_tier: <budget-document | official-statement | project-document | reporting>
artefact: <sibling filename, where this is a companion page in new-budget/>
body_completeness: <full | excerpt>
---
```

A companion page in `new-budget/` is **not yet a source** (no `ingested:`, no wiki links) until `BUDGET-COLLECT.md` step 2 catalogues it into `new/`. **For a tabular or PDF artefact** it also records the **sheet/tab, header row, printed scale and currency** at staging — the scale header (`N'000`, *en milliers*, "bilião") is the 1,000× error.

## Close

**Write the run file first — the run's state object**: `sweep/domestic/<ISO3>-<FY>-run-<date>.md` — what was staged, stage coverage, re-run triggers.

Then report tersely (`CLAUDE.md` → *Reporting*): documents staged by `doc_type`, acquisition lines added, **fiscal-year stages still uncovered**, and **whether the full estimates volume was obtained** — if not, every downstream total must say it supports sector-vote coverage only. Then the status line.

**The sweep ends at staging.** Only `BUDGET-COLLECT.md` catalogues and archives what it staged; run outside that batch, it leaves `new-budget/` populated until the batch's steps 2–3 run for the country.
