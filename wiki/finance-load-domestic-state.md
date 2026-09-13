# Driver — domestic-state finance (budgets and expenditure)

Feeds `wiki/finance-record-spec.md` from **national and sub-national budget documents and from reporting and official statements about them**. **One record per budget line, per fiscal year**: a single object that accretes every stage it is observed at, the appropriation its baseline.

Invocation: **"run domestic finance capture"** (one document or item at a time), **"run domestic finance load"** (a prepared CSV of lines), or **"run domestic finance back-swing"** (a pass over `raw/` items already carrying `finance.*` that report domestic state spend and have no `deal_id`). `INGEST.md` step 2a also calls it for any item tagged `finance.budget`. Run it from Claude Code.

**The domestic-state layer is suspended** (`wiki/index.md` → *Processes*); this file governs the procedure whenever it runs.

## Provenance — budget documents *and* reporting

Primary, all of them: the **budget document** (appropriation act, estimates, implementation report, audited accounts); the government's **own statements** (press releases, budget speeches, official portals); **auditor-general and parliamentary budget office reports**; **IFMIS / open-budget extracts** where the portal is the government's own; and **on-the-record reporting** of any of these. Leads, not sources, per `CLAUDE.md` → *The material*: AI syntheses, aggregators and digests, third-party portal mirrors.

**`source_tier`** — `budget-document` | `official-statement` | `project-document` | `reporting` — records which the record was built from.

**`project-document`** is a **financier's** appraisal document evidencing **domestic** money — a World Bank PAD's counterpart-funding row (PROJECT FINANCING DATA block) stating the government's own share of a co-financed project. It ranks **below** the state's own budget document and **above** reporting for case 5.

## The five cases

1. **Budget document exists** — build from it: full classification chain, codes, scale, `doc_locator`; `source_tier: budget-document`.
2. **Each line and each year is its own record; every stage folds into it.** Appropriated and actual are two stages of the one FY record, each a dated entry in its `## Stage history` (spec → *Store of record*). A record first created at a later stage is flagged (*Baseline, stage history and the missing appropriation*).
3. **Both exist** — the budget document is the record; the reporting is **linked, not merged into the fields**: a dated attributed line in `## Development history` (spec → *Store of record*).
4. **Only reporting exists** — build the record if it passes the spec's five-fact test; `source_tier: reporting`. Classification codes, scale and `doc_locator` are **left blank, not inferred**; the stage is recorded only where the source states it, else `unclear`.
5. **A budget document later surfaces for a record built from reporting — the document becomes the master.** Its figures become the record's **baseline** and its `## Description` (the appropriation's stated purpose, verbatim); the `deal_id` stem is kept; the superseded reporting folds into `## Stage history` as a dated, attributed line (`CLAUDE.md` → *Duplicates*). Log the reset. **A figure that disagrees is a contradiction**, filed to `reviews/contradictions/`, never overwritten.

## Origin — the double-counting gate

**A budget line financed externally is `finance_origin: non-state`, not `domestic-state`.** Run the gate on every line, before building anything:

| Budget line's stated funding source | `finance_origin` | Then |
|---|---|---|
| Domestic revenue; domestic borrowing; own-source (levy or fee income of a levy fund or regulator) | `domestic-state` | build normally |
| External loan; external grant; development-partner financed | `non-state` | **definite-match first** (below) |
| Counterpart / matching funds against an external project | **split** | see below |
| Not stated | `domestic-state`, flagged | record `funding source unstated` in `## Notes` |

**`funding_source`** (closed): `domestic-revenue` | `domestic-borrowing` | `own-source` | `external-loan` | `external-grant` | `counterpart` | `unstated`.

**Externally-financed lines are definite-matched before anything is built** (spec → *Store of record*); a match is one dated attributed line in the held deal's `## Development history`, and the diverted line **drops `finance.budget` and carries `finance.new`**.

Where no held record matches, build a new `non-state` record whose **financier is the external funder, not the treasury**: resolve an instrument name to the funding institution's existing entity slug. A line naming no funder beyond "external" **fails fact 1** — route it as an ordinary source and say so.

**Counterpart funding splits only where the document states both parts separately**: the government's share `domestic-state`, the external share `non-state` through the gate above. A combined figure is one line at its stated origin with the blending noted — never apportioned.

### Transfers inside the state — the second double-count

**Capture at the spending end, once.** Where a line is a transfer to a body whose budget is also captured, set **`is_transfer: true`** and record the receiving body; the record stands, and the compile pass excludes `is_transfer` lines from the total. Where the receiving body's budget is *not* held, the line counts normally: `is_transfer: false`, with a note why.

## Scope — which lines are digital

- **Never compute a digital share of a mixed line.** No percentages, no apportionment (spec → *Subject tag* §1).
- **A ministry's total vote is not digital-transformation finance.** The unit of capture is the programme, sub-programme or project line whose stated purpose is a digital activity.

**One carve-out — the single-mandate body.** **Where a body's entire statutory mandate falls within data governance or digital transformation, its total appropriation is a record at `scope_confidence: whole`, not an envelope.** The test is the **mandate, not the name**: a regulator that also licenses broadcast content is multi-purpose; record its digital programmes and mark the rest `partial`. State which test was applied in `scope_basis`.

Every record carries:

- **`scope_confidence`** — `whole` (stated purpose entirely a digital activity) | `partial` (demonstrably contains digital spend, amount not separable) | `unclear` (identified on weaker grounds — say so).
- **`scope_basis`** — one line on *how* the line was identified: programme title, project code, classification tag, narrative paragraph, named system.

`partial` and `unclear` records are built and held; the finance compile pass reports them **separately from the headline total**, never folded in.

**Extraction methods accumulate in `documentation/domestic-budget-extraction.md`**, per country and document type. Append on every run, failures included.

## Fiscal years

### A bare year in an instruction means the year the fiscal year *begins*

"FY2024", "2024", or "run … for 2024" all mean **the fiscal year beginning in 2024**, whatever the country labels it. Scope cut: **FY2024 onwards = fiscal years beginning on or after 1 January 2024**; Kenya's 2023/24 is out.

**The bare start year is the form everywhere CC names a fiscal year** — the invocation, the `new-budget/` and `budget-archive/` folders, `sweep_batch`, the run log, the `{fy}` element of a `deal_id`: `zaf-2024-…`, never `zaf-2024-25-…`.

Every record carries:

- **`fiscal_year_label`** — verbatim as the document writes it (`2024/25`, `FY2025`, `2017 EFY`, `NDP 12`). Never normalised.
- **`fy_start` / `fy_end`** — ISO dates.
- **`fy_calendar`** — `gregorian` | `ethiopian` (Ethiopian-calendar labels also carry the Gregorian equivalent in `fy_start`/`fy_end`).

`published` anchors on the **appropriating or reporting event** at day precision where stated. Failing that, `published` = **`fy_start`** with **`date_precision: month`**, not `year`; the spec's year-padding rule does not apply. The document's publication date is never the event date where the two differ (`CLAUDE.md` → *Currency*).

## Budget stage and version

**Stages** — `proposed` (tabled) | `appropriated` (enacted) | `revised` (supplementary or in-year revision) | `released` (warranted to the MDA by treasury) | `actual` (outturn) | `audited` (auditor-general verified). `budget_stage` is not a record-level field: the record carries `baseline_stage` / `current_stage` plus the per-stage totals (*Additional frontmatter*).

**`budget_version`** — `original` | `supplementary-1`, `-2`, … | `revised`.

**A supplementary states either an increment or a restated total; record which** — `supplementary_basis`: `increment` | `restated-total` | `unclear`. `restated-total` **supersedes** the original for totalling; both stand (`CLAUDE.md` → *Currency*). `unclear` excludes the line from totals.

**MTEF outer-year projections are not records** (fact 3). Capture the budget year only; note an outer-year figure in `## Notes` if informative.

**A later stage does not overwrite an earlier one, and is not a contradiction.** Both are held on the one record, each dated in `## Stage history`; the compile pass reads the execution rate off it.

### Execution is measured on two bases, never one

- **`execution_pct_vs_appropriated`** = outturn ÷ **original appropriated** — *budget credibility*; the **headline** basis.
- **`execution_pct_vs_revised`** = outturn ÷ **revised/final** — *absorption*.

Outturn is `audited_total` where held, else `actual_total`. On an earmarked-revenue line (a *compte d'affectation spéciale*, a levy fund) the appropriation is written down to collections and `…_vs_revised` reads ~100%; read the modifications column before quoting a *taux d'exécution*.

## Baseline, stage history and the missing appropriation

**The appropriation is the baseline.** The record is anchored on its `appropriated` stage; its `## Description` is the **appropriation line's stated purpose, verbatim**, carried forward unchanged as later stages accrete.

**`## Stage history`** — one dated, attributed entry per stage observed, oldest first, each carrying the stage's figure(s), the document and its `doc_locator`:

```
## Stage history
- **2024-02-21** appropriated **R1,894,596,000** (capital R400k, current R1,922.3m)
  — ENE 2024 Vote 30, p.581. [[…companion]]
- **2024-10-30** adjusted to R1,895,296,000; virement −R154,662,000 → final
  **R1,740,634,000** — AENE 2024 Vote 30. [[…companion]]
- **2025-10-01** audited actual **R734,841,000**; execution 42.2% of final —
  DCDT Annual Report 2024/25, p.205. [[…companion]]
```

**Where no appropriation is held, highlight it.** Set **`baseline_stage`** to the earliest stage actually held; where that is not `appropriated`, the first line of `## Notes` is `⚠ no appropriation stage held — baseline is <stage>`. The record stands.

**`proposed` and the merge.** A pre-document figure is a real record at `baseline_stage: proposed`, `source_tier: official-statement` or `reporting` (case 4). When the appropriation document surfaces (**case 5**), `appropriated` becomes the baseline and supplies the `## Description`; the `proposed` figure stays as the first entry in `## Stage history`. A disagreement is a contradiction, filed.

## Classification — codes, not just names

**Codes are the join key** across years and between budget and outturn. Capture name and code verbatim; never invent a code that isn't printed.

| Field | Anglophone | Francophone (LOLF-style) |
|---|---|---|
| `admin_head` + `admin_head_code` | Vote / Head | Section / Ministère |
| `spending_entity` + `spending_entity_code` | MDA | Institution / Service |
| `programme` + `programme_code` | Programme | Programme |
| `sub_programme` + `sub_programme_code` | Sub-programme / Project | Action / Activité |

Keep the document's own label for each level in `classification_labels`. **`econ_class`** — the economic classification as stated (GFS-style); verbatim, never mapped to a house vocabulary.

### The record's grain — the finest level the document publishes

**A record is one line-year at the finest classification level the document prints for that line.** Where a programme is broken into sub-programmes, **each digital sub-programme is its own record**; where the document stops at programme, the programme is the record and `sub_programme` is blank — meaning *the document published no finer level*, never *nobody looked*.

**Never hold a programme record and its own sub-programme records for the same year** — they would sum. When the sub-programme records are written, the parent is not a record.

**The sum of the digital sub-programmes is normally *less* than the printed programme total, and that is correct** (`scope_confidence: partial`). A shortfall inside the *digital* set is a reconciliation failure.

**A finer document supersedes a coarser one.** Where a later document publishes the sub-programme breakdown, the sub-programme records replace the programme-grain record (`CLAUDE.md` → *Duplicates*). Retire the parent; never keep both.

## Amounts

- **Amounts attach to a stage.** Each stage's total is a frontmatter stage-ladder field (`appropriated_total`, `revised_total`, `audited_total`, …) and a figure in its `## Stage history` entry.
- **`baseline_capital`** and **`baseline_recurrent`** — separate numeric fields in the original currency, at the **baseline** stage. Where only a combined figure is given, fill the stage total and leave the split blank — never split it ourselves.
- **`amount_scale`** — **the first thing to establish.** Record the scale as printed (`N'000`, `en milliers de FCFA`) **and store all amounts normalised to units**. Check `amount_capital + amount_recurrent = amount_total` wherever all three are given; on a mismatch the line is not recorded until it resolves.
- **`currency`** — ISO-4217, the announcing state's own currency (`CLAUDE.md` → *Currency*). Record the code in force in that fiscal year, never back-convert across a redenomination, and note the break where a series spans one.
- **`amount_usd`** — a **dated conversion** carrying `fx_rate`, `fx_rate_date`, `fx_rate_source` and `fx_rate_basis`. Use the **fiscal-year average rate** from a named source (IMF IFS, or the central bank's published average), never spot at capture. Fallbacks, in order: **(a)** the mean of the twelve monthly averages spanning `fy_start`–`fy_end`, `fx_rate_basis: fy-average-computed`; **(b)** for an incomplete fiscal year, the rate at `fy_start`, `fx_rate_basis: fy-start-spot` — provisional, recomputed when the year closes. Under a multiple or managed rate, say which rate was used.
- **Never sum USD across fiscal years** in a compiled total. Aggregate within a year, or in original currency.

## State level — what counts as domestic state

**`state_level`** — `national` | `sub-national` | `soe` | `levy-fund` | `regulator`.

- **`place` is always the country ISO-3** — `countries.csv` has no sub-national vocabulary. The sub-national unit is an **entity** (`lagos-state-government`) plus **`spending_tier_name`** verbatim.
- For `levy-fund` and `regulator`, the stage is usually `appropriated` (board-approved budget) or `actual`; funding source `own-source`, origin `domestic-state`.
- **SOEs: the origin of the money decides.** An SOE spending commercial revenue or its own borrowing is a **non-state** funder and belongs to the news driver. This driver captures the **state → SOE flow**: a subvention, recapitalisation or appropriation to an SOE is a `domestic-state` record with the fisc as financier and the **SOE as recipient**, `state_level: soe`.

## Entities

Per `CLAUDE.md` → *Entities*, and the spec. Three actors:

- **Financier** — the fisc: the treasury/ministry of finance, or the levy fund / regulator spending its own income. An institution, never the minister; never an SOE.
- **Spending entity** — the MDA. Resolve against the `entities:` slugs already used in `raw/`.
- **`vendor`** — the contractor or supplier, **where the document names one**. Tag as an entity.

## Record key and filename

`deal_id`: `{ISO3}[-{tier-slug}]-{fy}-{admin_head_code}-{programme_code}[-{sub_programme_code}]`, lowercased, non-alphanumerics to hyphens — `nga-2025-0522-erp01`, `nga-lagos-state-2025-05-erp01`. **No `-{stage}` suffix: the stem is itself the record id — one file per line-year.**

**The `{sub_programme_code}` segment is present exactly when the record is at sub-programme grain.** A record that gains sub-programme grain gains a new id: a rename plus a retirement of the parent, not an edit in place.

**`{fy}` is the bare start year** (*Fiscal years*). **The tier slug is mandatory for anything not `state_level: national`**; vote numbering is never assumed unique across sub-national units. Where a code is genuinely absent, use a slug of the name and note it.

Filename: **`{published}-{deal_id}.md`** in `new/` — no `-{short-title-slug}`. The line description lives in the `title` and the `## Budget line record` table.

## Source citation

Every record carries **`doc_type`** and **`doc_locator`**:

- `doc_type` — **the canonical list, one vocabulary for both the record and the sweep's staging frontmatter**:

  `appropriation-act` | `budget-estimates` | `mtef` | `implementation-report` | `audited-accounts` | `ifmis-extract` | `treasury-release` | `board-budget` | `procurement-plan` | `executive-instrument` | `project-document` | `statement` | `reporting`

  `executive-instrument` covers a decree, despacho or supplementary-credit order; `project-document` a financier's appraisal or financing document.
- `doc_locator` — page, table and line reference as printed (`p. 412, head 0522, line 23050113`).

Both apply to `source_tier: budget-document`; a record built from reporting or a statement cites that source per the spec and leaves both blank.

### The budget document gets one companion source page

The document is stored **once**, as a companion source page per `layout.md` §3, holding the citation, the document's scope, the classification structure and the scale/currency headers — `body_completeness: excerpt`, with a note that the body is a structured extract of a tabular document, not a withheld text. Every record from that document links to it.

Each record's `## Description` carries the **line's stated purpose, verbatim**, and nothing else; where the document gives only a title, the description is blank. **Capture the title and description in the document's own language**; add a translation in `## Notes` where it aids the reader.

**A budget document that cannot be fetched goes to `reviews/acquisitions.md`**, one automated attempt (`CLAUDE.md` → *Working the base*). Records built from reporting stand meanwhile. If it stays unobtainable, state the absence on the place hub as a dated finding.

## Additional frontmatter

Frontmatter carries **what the compile pass aggregates or filters on**; everything else renders as rows in the `## Deal record` table. On top of the spec's schema:

```yaml
finance_origin: domestic-state   # or non-state, per the origin gate above
state_level: national            # national | sub-national | soe | levy-fund | regulator
spending_tier_name: ""           # verbatim, required unless state_level: national
fiscal_year_label: "2024/25"
fy_start: 2024-04-01
fy_end: 2025-03-31
budget_version: original
source_tier: budget-document     # tier of the CURRENT baseline source
supplementary_basis: ""          # increment | restated-total | unclear (supplementaries only)
scope_confidence: whole          # whole | partial | unclear
is_transfer: false
currency: ZAR
# --- classification chain (§Classification; codes are the cross-year join key) ---
admin_head: "Vote 30 — Communications and Digital Technologies"
admin_head_code: "30"
spending_entity: "Department of Communications and Digital Technologies"
spending_entity_code: ""         # blank where the document prints no code
programme: "ICT Infrastructure Development and Support"
programme_code: "5"
sub_programme: "Broadband"       # blank where the document stops at programme
sub_programme_code: "5.4"
econ_class: "Transfers and subsidies"   # verbatim, as stated
# --- stage ladder (one record per line-year; a total is blank until that stage is observed) ---
baseline_stage: appropriated     # earliest stage held; ⚠-note in Notes where not 'appropriated'
current_stage: audited           # latest stage held — the record's headline
proposed_total:                  # a pre-document figure, superseded once appropriated arrives
appropriated_total: 1894596000   # normalised to units, original currency
revised_total: 1740634000        # adjusted / final, where a supplementary or AENE restates
released_total:
actual_total:
audited_total: 734841000
execution_pct_vs_appropriated: 38.8   # HEADLINE — outturn ÷ original appropriated (budget credibility)
execution_pct_vs_revised: 42.2        # outturn ÷ revised/final (absorption); ~100% on written-down levy lines
# capital/recurrent split at the BASELINE stage (salaries vs build)
baseline_capital: 400000
baseline_recurrent: 1922300000
amount_usd: 105000000            # dated conversion of the current-stage total
fx_rate: 18.0
fx_rate_basis: fy-average        # fy-average | fy-average-computed | fy-start-spot
```

The stage ladder, FX fields, classification chain and `econ_class` sit in frontmatter; render the classification chain and `econ_class` as rows in the `## Budget line record` table **as well**. In the body table, not frontmatter: `funding_source`, `fy_calendar`, `amount_scale`, `fx_rate_date`, `fx_rate_source`, `classification_labels`, `vendor`, `scope_basis`, `doc_type`, `doc_locator`.

## Loop

For each budget line: **scope** test → **origin gate** → the spec's five-fact test → map fields → **match on the `deal_id` stem: an existing line-year record → fold this stage into its ladder and `## Stage history` (and, if this stage is `appropriated` and the held baseline was `proposed`, promote it to master per case 5); no match → create the record** → hand to `wiki/finance-record-spec.md` → write the file to `new/` → append one line to `documentation/domestic-finance-run-log.csv` (`deal_id, file, country, state_level, fy, stage, version, origin, funding_source, scope_confidence, is_transfer, amount_total, currency, doc_locator, matched_to, warnings`) → append any new extraction method to `documentation/domestic-budget-extraction.md`. Moving the file into `new/` is the last step.

Work a document at a time, over all its digital lines at once, never a selection.

**Back-swing mode.** Candidate set: `raw/` items carrying a `finance.*` tag that report domestic state spend and have no `deal_id` — including everything the news driver logged `origin: domestic-state — skipped`. Work the whole set in one pass; each item runs the five cases. **The source page is not rewritten** — the record cites it. Log per item: `deal_id | source file | case | source_tier | failed-fact NN`.

## Close

Report terse (`CLAUDE.md` → *Reporting*): documents processed, records built by stage and origin, lines diverted to merge, lines that failed scope or the five-fact test and why. End with the status line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`
