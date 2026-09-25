<!-- reader: cc; type: reference -->
# Budget extraction — strategy library

**How to get figures out of a shape of document.** One entry per *structural
archetype*, not per country and not per document. Read by `BUDGET-EXTRACT.md`,
which is the pass that runs this.

Started 2026-07-22 from the ZAF FY2024/25 corpus (9 documents). Everything here
is provisional and expected to be wrong in places — it improves by being run.

## What belongs here, and what does not

**Here: strategy.** How this shape of document is laid out, which tool reads it,
where the numbers are, what breaks.

**Not here: judgement.** Whether a line is digital, whether an envelope is a
record, how to date or tag it — that is `wiki/finance-load-domestic-state.md` (the
rules) and `documentation/domestic-budget-extraction.md` (per-country vocabulary,
where digital lines hide). Restate either here and the two will drift.

The distinction in one line: *this file gets the table out; those files decide
what the table means.*

## Keep it bounded

**One entry per archetype, and archetypes are rare.** There are perhaps six or
eight budget-document structures across the continent, not fifty-four. A new
document either **matches an existing archetype** — in which case add nothing,
just note the match in the run log — or **reveals a new one**, which earns an
entry.

Country-specific quirks belong in the country's section of
`domestic-budget-extraction.md`, not as new archetypes here. A file that grows an
entry per document becomes case law and stops being readable, which is the failure
`CLAUDE.md` names.

## Baseline: the toolchain

**`pdftotext -layout` is the workhorse and it is enough.** Every document in the
first corpus has a clean embedded text layer; `-layout` preserves column
alignment well enough to read tables directly. Confirmed across InDesign, XPP,
PScript and Word producers.

**Every invocation carries `-enc UTF-8`, including the ones that only count bytes.** *(2026-08-21, housekeeping job 31 — the trap was recorded against CAF FY2025 and Ghana FY2024 in `domestic-budget-extraction.md` but never written into this list, so it kept recurring.)* `pdftotext` emits **Latin-1 by default** here. Read as UTF-8, every accented character becomes a replacement character, `données` stops matching a grep for `données`, and a cross-vote keyword scan returns a clean zero it has not earned — the CAF FY2025 volume was recorded as containing the term zero times when it contains it twelve. Nothing warns you. Where a bare `pdftotext -layout` or `pdftotext -table` appears below as the name of a behaviour rather than a command to run, the flag is still implied.

So, in order:

1. `pdfinfo` — page count, producer. Producer is a decent archetype hint.
2. `pdftotext -enc UTF-8 -layout <f> -` piped to `grep -n` — locate the tables by their
   captions before extracting anything.
3. `pdftotext -enc UTF-8 -layout -f <first> -l <last>` — pull just the pages that matter.
4. **`pdftotext -table` — reach for this the moment `-layout` misaligns a wide
   table, before pdfplumber.** *(Added 2026-07-25, Benin.)* `-layout` preserves
   horizontal position, which is not the same as preserving columns: on a wide
   machine-generated table it wraps figures onto neighbouring lines and offsets
   them from their row labels by several rows, so money silently attaches to the
   wrong line. That is the failure behind the Kenya "map by order, then verify by
   arithmetic" workaround (Archetype G). `-table` reads column structure instead
   of position and fixed a 13-column SIGFP execution annex outright, first
   attempt, where `-layout` produced unusable rubbish. Its one cost is that digit
   groups come back space-separated inside a number (`12   372  151  413`), so
   strip whitespace before parsing.
5. `pdfplumber` — **only** where both `-layout` and `-table` fail. Slower, needs
   per-table tuning, still not needed once.
6. **`python scripts/ocr-pdf.py <f> --lang fra --pages 40-95 -o <f>.ocr.txt`** —
   only if `pdftotext` returns near-zero characters across the whole document,
   i.e. a scan. *(OCR landed 2026-07-25; `eng`/`fra`/`por`/`ara`, combine with
   `+`.)* The sidecar has the same form feeds and column spacing as
   `pdftotext -layout`, so steps 2–5 read it unchanged — but it runs at roughly a
   page a second, so range it. See `BUDGET-EXTRACT.md` §1 for when to stop.

**What OCR is calibrated to do, measured 2026-07-25 on held documents.** Prose is
solved: the Angolan enacted *Lei n.º 15/23* (`por`) and Arabic body text come back
essentially clean, accents and all. Ordinary tables are workable: the Burundi *PTBA
modifié* (`fra`) returns its 26-digit LITERA codes, tâche labels and amounts
readably. **Dense wide numeric tables on a low-DPI scan are not** — the Benin RAPEX
*Synthèse des mouvements de crédits* is a 200 dpi landscape table whose figures a
reader can read and OCR cannot: it returns `3 104 942 341` for `3 104 932 343`,
wrong in the middle, plausible throughout. Upsampling does not help (there is no
information to recover), and neither `--psm 6`, `--threshold 2` nor `--digits` on a
column crop got it to cross-foot. Treat that class as still blocked, and record
nothing from it. The rule holds because the arithmetic check catches it.

**Always verify an extraction against the document's own arithmetic before
recording it.** A table that prints its own subtotals, percentages and residuals
is self-checking: `dotation − engagement = disponible`, `engagement ÷ dotation =
taux`, `capital + recurrent = total`. A row that fails is a misread, not a
finding. This caught nothing in Benin precisely because `-table` was right — which
is the point: it is what made "`-table` is right" a claim rather than a hope.

**Check the text layer first**: `pdftotext -enc UTF-8 <f> - | wc -c`. A low count on the
first pages means a graphical cover, not a scan — measure the whole document
before concluding anything.

---

## Archetype A — per-vote programme-budget chapter

*Seen as: South Africa ENE Vote 30 (2024, 36pp).* **The richest structure in the
corpus and the primary extraction target.**

**Layout.** A budget-summary table (programme × economic classification × 3
years), then narrative, then one table per programme giving **sub-programme ×
economic classification** across ~7 year-columns: several audited outcome years,
an adjusted appropriation for the current year, and three medium-term estimate
years. Programme tables are numbered (`Table 30.14`) and continue across pages
with a `(continued)` caption.

**Strategy.**

1. `grep -n "^Table [0-9]*\.\|Programme [0-9]:"` to index the tables.
2. Read the scale from the **table stub** — the cell above the first data column,
   typically `R million` or `R thousand`. It varies *between tables in the same
   document*, so read it per table, never once per document.
3. Take the sub-programme block and the economic-classification block separately;
   they are two tables stacked under one caption, each ending in a `Total` row
   that must match.
4. Identify the current-year column by its header (`2024/25`), not by position —
   column count varies with how many audited years are shown.

**Traps.**

- **Row labels wrap onto continuation lines** ("ICT Infrastructure Development
  and / Support"). Join a line with no numeric cells to the line above.
- **`–` (en dash) means nil, not missing.** Record `0` where the source states a
  dash in a figure column; leave blank only where the cell is genuinely absent.
- **Percentage and growth-rate columns sit between the year columns** — average
  growth rate, expenditure share. Do not mistake them for money.
- **A `Change to <year> Budget estimate` row** carries parenthesised negatives.
  Parentheses are minus signs.
- **`of which:` blocks** under goods and services are a partial decomposition, not
  a complete one — the components do not sum to the parent, by design.

**What it yields.** `appropriated` (or `proposed`, pre-enactment) records at
sub-programme grain, with capital/recurrent split available from the economic
classification.

---

## Archetype B — consolidated appropriation schedule

*Seen as: South Africa Appropriation Bill B5-2024 (40pp), Adjustments
Appropriation Bill B14-2024 (20pp).*

**Layout.** One block per vote: a total line, then numbered programmes, each with
five columns — total, compensation of employees, goods and services, transfers
and subsidies, payments for capital assets. Purpose text between blocks.
Sub-programmes are **not** shown. Always in the smallest unit (`R'000`).

**Strategy.** `grep -n -A15 "<vote name>"` — the vote block is short and
self-contained. Read the vote total from the header line and the programme lines
beneath it.

**Traps.**

- **Coarser than Archetype A** — it is the legally authoritative statement of the
  amount, but it will not give a digital line below programme level. Use it for
  the **stage and the authority**, and Archetype A for the detail.
- `Of which` sub-lines (e.g. named household transfers) appear under programmes
  and are not programmes.

**What it yields.** Confirms `appropriated` / `revised`, and the `doc_locator`
that makes the record legally citable.

---

## Archetype C — adjustments schedule

*Seen as: South Africa AENE Vote 30 (2024, 8pp).*

**Layout.** A summary of the original appropriation, decreases and increases, and
the adjusted appropriation; then a per-programme decomposition of the adjustment
into named columns — unforeseeable/unavoidable, virements and shifts, roll-overs,
emergency, other.

**Strategy.** This archetype is what `budget_version` and `supplementary_basis`
were built for. The column headers tell you the basis directly: a document
presenting *original + adjustments = adjusted* is a **`restated-total`**, not an
increment, so the adjusted figure supersedes rather than adds.

**Traps.**

- **A zero net adjustment is not "no change".** ZAF Vote 30 FY2024/25 shows
  −R2.789m and +R2.789m netting to zero at the vote, while money moved *between*
  programmes. The vote total is unchanged and the programme totals are not.
  Extract at programme level or the movement is invisible.
- Decreases are parenthesised.

**What it yields.** `revised` records, and the virement trail that explains a
later underspend.

---

## Archetype D — cross-vote statistical annexure

*Seen as: South Africa Budget 2025 statistical tables (40pp).*

**Layout.** One row per vote, columns spanning several years and stages (outcome,
budget estimate, adjusted appropriation, revised estimate).

**Strategy.** Locate the vote by name, then map columns by reading the header
block above — which may be **two or three rows deep**, with year spanners above
column names.

**Trap — this archetype is right-labelled.** In the ZAF tables **the vote name
sits at the END of the row and the columns read leftward from it.** A parser that
assumes label-then-values will attach every figure to the wrong vote. Always
eyeball one known row against a figure you have from another document before
trusting a whole table.

**What it yields.** The `revised` estimate, and — its real value — cross-vote
coverage for the scope problem: which *other* votes carry digital money.

---

## Archetype E — annual report with audited appropriation statement

*Seen as: DCDT Annual Report 2024/25 (279pp).* **The outturn, and the most
valuable single document in the chain.**

**Layout.** A long performance narrative, then annual financial statements. The
appropriation statement gives, per programme: approved budget, shifting of funds,
virement, **final budget, actual expenditure, variance, expenditure as % of final
budget**, plus the prior year's final and actual.

**Strategy.**

1. `grep -n "APPROPRIATION STATEMENT"` — it recurs as a running header, so take
   the **first occurrence after the table of contents**, around two-thirds
   through.
2. Scale is `R'000`, stated in the column header block.
3. Take the whole row: approved → final → actual is three `budget_stage` values
   for one line, and they are the point.

**Traps.**

- **Heavy left indentation** from the page furniture; strip leading whitespace
  before parsing columns.
- Programme names are UPPERCASE and hyphenate across lines
  (`ICT INFRA-` / `STRUCTURE`). Rejoin before matching.
- The report covers the department, not the vote's transfers to entities — an
  entity's own spending is in *its* annual report.

**What it yields.** `actual` and `audited` records, and the **execution rate**,
which is the finding this whole dataset exists to produce. First corpus: Vote 30
Programme 5 approved R1,922.7m → final R1,768.9m → actual R755.2m, 42.7%.

---

## Archetype F — narrative audit report

*Seen as: AGSA Consolidated General Report PFMA 2024-25 (280pp).*

**Layout.** Prose findings with figures embedded in sentences, plus infographic
tables that do not survive text extraction cleanly.

**Strategy.** Do not attempt table extraction. `grep -n -i` for the ICT terms and
read the surrounding paragraphs.

**What it yields — and does not.** **No deal records.** It yields context,
contradiction leads (spend reported against systems never used), and named
programmes worth chasing. Treat it as a source page, not an extraction target.

---

## Cross-document reconciliation — required, and it works

The archetypes check each other, and in the first corpus they agreed **to the
rand**: R3,968,611 thousand appears identically in the ENE (A), the Appropriation
Bill (B), the AENE (C), the statistical annexure (D) and the annual report's
approved-budget column (E).

Run these before writing any record:

| Check | Across |
|---|---|
| Vote total = sum of programme totals | within each document |
| Sub-programme total = programme total | A |
| Capital + recurrent + transfers = total | A, B |
| Appropriation = ENE main appropriation | A ↔ B |
| Adjusted appropriation = adjustments schedule | C ↔ B |
| Final budget = original + adjustments | C ↔ E |
| Prior-year actual = that year's outturn | E ↔ previous E |

**A mismatch is either an extraction error or a finding, and you cannot tell
which without looking.** Resolve it before recording. If it resolves as a genuine
disagreement between documents, it is a contradiction
(`reviews/contradictions/`), not a rounding issue.

## Scale — per table, never per document

The first corpus carried `R million`, `R thousand` and `R'000` **within the same
country-year**, and the ENE varies scale between tables in a single document.
Read the stub of every table. Store normalised to units. Check
capital + recurrent = total as the arithmetic proof that the scale was read right.

## The cross-vote scan — required, not optional

**Digital money is not in the digital ministry's vote.** *(Bill's catch,
2026-07-22, confirmed against the ZAF FY2024 full ENE.)* Sector-vote-only capture
systematically understates domestic digital spend, and by a lot: scanning all 42
ZAF votes turned up genuine digital sub-programme lines in **seven votes outside
Vote 30**.

| Vote | Line | 2024/25 |
|---|---|---|
| 25 Justice and Constitutional Development | Justice Modernisation | R661.2m |
| 22 Correctional Services | Information Technology | R358.0m |
| 14 Statistics South Africa | Business Modernisation | R60.2m |
| 11 Public Service and Administration | e-Government Services and Information | R25.3m |
| 35 Science and Innovation | Various institutions: ICT | R22.5m |
| 39 Trade, Industry and Competition | Digital market inquiry | R20.1m |
| 8 National Treasury | Digitisation: Distribution capability; integrated financial management system | — |

Justice Modernisation alone exceeds four of Vote 30's six programmes. The two
largest come to over R1bn against Vote 30's R3,968.6m total — and that scan missed
home affairs' identity spend, so the true understatement is worse.

**So the cross-vote instrument is the full estimates volume** (archetype A × N),
and it is not the redundant document an earlier draft of this file called it. Run
this scan on **every** country-year that holds one:

1. Index the vote chapters — in the ZAF volume, a line matching `^\s*Vote\s+\d+\s*$`
   with the vote name on the next non-blank line. 42 found cleanly.
2. Walk every line, attributing it to the vote chapter it falls in.
3. Keep lines that carry a digital term **and** look like a budget row (a label
   plus several money-shaped cells) — narrative mentions are not lines.
4. Hand the survivors to the driver's scope test like any other candidate. Most
   will be `whole`; some, like a modernisation programme mixing systems with
   buildings, will be `partial`.

**Trap — `ict` is a substring of `district`, `conflict` and `restrict`.** Six of
thirteen hits in the first scan were district-health and conviction-rate rows.
Match on word boundaries, and prefer the longer terms (`digitis`, `e-gov`,
`information technology`, `broadband`, `modernisation`) over bare `ict`.

**Trap — the sector vote is still the anchor.** The cross-vote scan finds lines,
not context: a name like "Business Modernisation" gives no purpose. Confirm
against the programme's narrative before recording, and mark
`scope_confidence: unclear` where the volume never says what the money buys.

**Two categories the keyword scan will miss by construction**, both worth a
deliberate hand-search of the volume's contents page rather than a grep:

- **Identity and data exchange.** Named for their function, never for their
  technology — *population register*, *civil registration*, *national identity
  card*, *biometric enrolment*, *passport systems*; *interoperability framework*,
  *government service bus*, *shared services platform*, *single window*, *master
  data management*. They sit in home affairs, interior, finance or a
  cross-government delivery unit, because data exchange is plumbing between
  departments and gets funded by whoever coordinates them.
- **Governance structures and processes.** The regulator, the data protection
  authority, the CSIRT, the digital transformation unit. These hide in
  *Administration*, *Policy* and *Corporate services* programmes, are mostly
  compensation of employees, and read as overhead. Find them by looking up the
  **body** in the volume's vote index, not by searching for a digital term.
  Where the body is a single-mandate authority, its whole appropriation is the
  line — see the envelope carve-out flagged in
  `DOMESTIC-FINANCE-SWEEP.md` → *Notes for Bill*.

**And record what the volume does *not* contain.** A data protection authority
with no appropriation, in a state that has passed a data protection act, is a
finding — arguably the sharpest this dataset produces. The scan should end with a
short list of governance bodies looked for and not found, so the absence reaches
the place hub as a dated statement rather than being lost as a null result.

**This changes what the sweep must fetch.** A country-year without its full
estimates volume can only produce sector-vote coverage, and any total built from
it should say so on the page — an understated total presented as a total is worse
than a stated gap.

## Archetype G — Kenya Programme Based Budget (PBB) chapter, and its supplementary form

*Seen as: Kenya PBB FY2024/25 (1,149pp), PBB Supplementary I/III (977/740pp), all June 2024 – June 2025.*

**Layout.** One chapter per vote: Parts A–E are mandate, narrative and performance indicators
(no money except targets); **Part F** is the money summary — programme and sub-programme ×
year — and **Part H** repeats each sub-programme × economic classification. The original
estimates carry columns `Baseline 2023/24 | Estimates 2024/25 | two projection years`; a
**supplementary** PBB carries `Approved | Supplementary | Change` — and its Approved column is
the *previous* supplementary's outcome, so **Supp III's Approved column recovers Supp II's
values** even when the Supp II volume itself is lost. Absolute KShs, no scale factor.

**Strategy.** `grep -n "Total Expenditure for Vote <n>"` → read ~35 lines back for the whole
Part F block. Sub-programme codes are 7-digit (`0210010`), programmes end in `000`. Reconcile:
sub-programmes must sum to the programme row and programmes to the vote total (exact, no
rounding — confirmed on Vote 1122: 278,922,194 + 17,388,445,150 + 4,687,513,408 = 22,354,880,752).

**Traps.**

- **Supplementary Part F rows wrap badly under `-layout`**: programme labels stack in one column
  and figures in another, offset by several lines — map by *order*, then verify each mapped
  triple satisfies `approved + change = supplementary`. Any row that fails the arithmetic is a
  misread, not a finding.
- Part G (vote × economic classification) scrambles worse than Part F under `-layout`; prefer
  Part H (per-sub-programme) where the split matters.
- Parentheses are minus signs; `-` is nil.

**Companion form 2B (Kenya development/recurrent books, incl. supplementaries).** Itemised
project heads (`1071108500`) with `GROSS | A-I-A | NET` under Approved and Amended blocks. Same
wrap problem, same defence: `approved + amendment = amended` must hold per row.

**What it yields.** `appropriated` (original) and `revised` (each supplementary) at
sub-programme grain; combined with the COB BIRR (Archetype H) it gives the full
stage-split series.

## Archetype H — Kenya COB Budget Implementation Review Report (BIRR)

*Seen as: NG-BIRR FY2024/25 annual (409pp, 102MB, scanned + OCR).*

**Layout.** Per-MDA sections: narrative stating the vote's full revision chain verbatim
("original ... revised to ... in Supplementary Estimates I/II/III"), then a
programme/sub-programme table `Revised Estimates (rec/dev/total) | Expenditure (rec/dev/total) |
Absorption %`, then a non-financial KPI table.

**Strategy.** `grep -n "<State Department name>"` → the section narrative is the cleanest carrier
of the four stage totals; take absorption percentages from the table; cross-foot actuals against
the stated overall absorption before recording.

**Traps.** OCR noise corrupts digits in tables ("l2.06", "16.,l5") — trust the narrative's
letters-and-context reading, verify any table digit by arithmetic (rec + dev = total;
actual/revised = stated %). Where a table digit cannot be made to cross-foot, do not record it.

**What it yields.** `released` (exchequer issues incl. Article 223) and `actual` stages with
absorption — the execution half of the series, which Kenya uniquely publishes four-monthly.

### Francophone variant — the SIGFP execution annex *(added 2026-07-25, Benin)*

Same family, native text, and it can arrive **embedded in an unrelated document**. Benin's
*Note de présentation du PLFR 2026* carries, as its Annexe n° 2, raw SIGFP output titled
`SITUATION D'EXECUTION DU BUDGET PAR PROGRAMME` — per programme and dotation: `DOTATION INITIALE`
and `DOTATION FINALE` (both AE and CP), `ENGAGEMENT`, `MANDAT ORD.`, `OP NON REGULARISE`,
`PAIEMENT`, `MONTANT DISPONIBLE`, **`TAUX ENG. %`** and **`TAUX ORD. %`**, each decomposed into
`DO`/`DC` and by economic nature, with capital further split into **`Contribution Budgétaire`**
(domestic) and **`Emprunt`** (external).

**Why it is worth hunting for.** It is the per-programme *executed* grain that a country's
never-published performance reports were supposed to supply, and the domestic/emprunt split means
the origin gate runs on the execution side, not just the appropriation side — which is where the
interesting number is. Benin's programme *Numérique* executed 0.62% of its gross credits at
30 April 2026 against an all-programmes 15.43%; on the domestic portion alone it is 1.32%, because
the external loan tranche had drawn nothing.

**So: look inside every rectificative's explanatory note, not just the bill.** The bill itself was
image-only; the note was native and carried everything.

**Traps.** Read it with `-table`, never `-layout`. Scale headers lie — in the same document
Annexe n° 1 prints *« en milliers de francs CFA »* over figures that are in francs, and Annexe n° 2
is in francs and unlabelled. `DOTATION FINALE` equal to `DOTATION INITIALE` means no credit
movement yet, not a missing column.

## Archetype I — francophone programme-execution canevas (native spreadsheet)

*Seen as: Burundi T3 execution canevas FY2025/26 — `CANEVAS-RAPPORT_<INST>_2025-2026_T3.xlsx`, one file per institution (MFBEN 762 rows, MIDCSP 504, MCM 183, CENI 33), 64 columns.* **The first machine-readable (spreadsheet) budget archetype in the corpus** — no PDF, no OCR, read with `openpyxl`.

**Layout.** One row per **PAP activity/tâche**, nested `ministère → programme → action → activité PAP → tâche révisée`. Key columns: `INTITULE MINISTERE` (col 2), `INTITULE PROGRAMME` (7), `PROGRAMME PRIORITAIRE` (13), `CODE NOMENCLATURE` (14, the LITERA join key), `ACTIVITE PAP` (26), `TACHE REVISEE` (30), quarterly revised quantities/budgets (33–42), **`BUDGET ANNUEL REVISE` (43)** — the revised appropriation — then transfers (47–48) and execution (`ENG BUDGETAIRE`/`LIQUIDATION`/`Taux de liquidation`/`PAIEMENT`/`DECAISSEMENT`/`EXECUTION FINANCIERE CUMULE`, cols 50–63).

**Strategy.** Load `data_only=True`; take `BUDGET ANNUEL REVISE` (col 43) as the **revised-stage** figure; filter digital lines at the **tâche** grain (col 30 + col 26), not the programme label.

**Traps.**
- **The programme name is an envelope, not a scope signal.** Burundi labels a whole ministry's budget `PRG01: Programme de digitalisation de l'administration publique` — including radio, newspaper, fuel and missions. Recording at programme level double-counts and mis-scopes; match on the tâche text (`digitalis|logiciel|biométri|serveur|données|télécentre|facturation électronique|interconnex…`) and exclude overhead (`carburant|mission|bâtiment|véhicule|journal`).
- **Execution columns are often empty formulas.** `Taux de liquidation` (col 53) is `=AZ5/AO5`; `LIQUIDATION`/`PAIEMENT`/`DECAISSEMENT` returned `None` under `data_only` (the workbook was filed without cached execution values). So a T3 canevas can yield **revised appropriations only, no execution rate** — verify before claiming an outturn.
- Substitutes for a missing PTBA modifié: the revised column *is* the revised per-programme volume when the standalone modifié is unpublished/OCR-blocked.

**What it yields.** `revised` records at PAP-activity grain, cross-ministry, with the LITERA code as the join key — and, where the execution columns are populated, `actual`/`released` with absorption.

## Archetype J — francophone procurement plan (PPM, native text)

*Seen as: Burundi ARMP `Plan Prévisionnel de Passation des Marchés` per spending unit (MININTER, SETIC, FSU, MFBEN), 1–14 pp, native text.* A short table: `N° | Objet du marché | Mode de passation | LITERA | Budget prévu | Source de financement | dates`. Sections headed by a **LITERA classification string** (the join key back to the PTBA/canevas). `Source de financement` distinguishes `Budget de l'État` (domestic-revenue) from `FSU` (own-source levy) from a project (external).

**Use it for** the fisc-side digital line where the programme volume is OCR-blocked — but **prefer the programme table where one is machine-readable**: a PPM line and its canevas/PTBA programme are the *same money under two naming systems* (the AGO PAC↔OGE rule), so record from one and treat the other as procurement/vendor detail. **Scope call:** record software/systems/digitalisation/connectivity/biometric lines; treat generic office-IT hardware (ordinateurs, matériel informatique, réseau) as operational overhead, not a digital-activity line.

## Archetype K — the state's own budget open-data API

*Seen as: Benin, `backdata.budgetbenin.bj/public/api` (2026-07-25) — 5,351 rows, seven datasets,
no auth.* **The first archetype that is not a document.**

**How to find it.** The public-facing site (`opendata.budgetbenin.bj`) is a JavaScript
single-page app; **the API base URL sits in its main JS bundle**. Routes were `/agregats` (the
dataset list) and `/agregats/{slug}` (detail — `institutions`, `categories`, `headers`,
`expenses`). Look for this wherever a finance ministry has an "open budget" portal that renders
charts rather than serving files: the charts have to be fed from somewhere.

**Layout.** One row per line × year × economic category:
`{annee, institution_id, agregat_id, category_id, code, dotation_initiale, dotation_finale,
engage, ordonance}`. `institution_id` resolves through a lookup dict that means *ministry* in one
dataset and *programme* in another. Scale is declared per dataset (`amount_unit: million`).

**Why it is worth the trouble.** **The value columns are budget stages** — appropriated / revised
/ committed / ordonnancé — which is the cleanest stage mapping in this corpus, and it reaches back
further than any published volume (2008 at ministry grain).

**Traps, and they are severe.**

- **Execution columns are usually null.** All of `dotation_finale`, `engage` and `ordonance` were
  null for every year 2021–2024. A null is a gap in the portal, never zero execution.
- **Aggregates do not reconcile to the budget.** Per-line figures cross-checked exactly against
  the workbook and the ministries' own reports; the classification totals covered only a subset of
  the state budget (debt service, special accounts and the pension fund sat outside). Reconcile
  before totalling anything.
- **The economic labels are unreliable.** For one programme the API and the workbook carried the
  *same six numbers under different labels*, permuting transfers against capital and grants
  against loans. Totals agree; the split does not.
- **It can be flatly wrong on a line, and it can contradict itself.** One programme was 5.3× its
  true value — while the API's *own* administrative classification agreed with the workbook
  against its own programmatic classification. That self-contradiction is the tell.
- **It stops.** Vote-grain coverage ended at FY2024 while the portal's macro datasets ran on.
  Verify the year range per dataset, live; never plan a run around an API being current.

**So treat an API as a corroborating source, not the source of record**, wherever a published
volume also exists. Where one does not, it is still the estimates volume — just one that has to be
checked line by line against anything else available.

## Archetype L — multi-year cross-classification estimates workbook (native spreadsheet)

*Seen as: Benin, *Tableaux de classifications croisées des dépenses de l'État sur la période
pluriannuelle*, posted annually as XLSX by the Direction générale du Budget (LF 2025 and LF 2026
editions).* A **LOLF/UEMOA-directive artefact**, so expect it across francophone West Africa.

**Layout.** One sheet, `Classif Prog-Admin-Eco`. Ministry header rows (label in column 1, no code)
alternate with programme/dotation rows (code in column 1, name in column 2). Then **one column
block per fiscal year, six or seven years wide**, and within each block **nine economic columns**:
dépenses de personnel ; d'acquisitions de biens et services ; de transfert ; **total ordinaires** ;
capital ressources intérieures ; capital ressources extérieures (dons) ; capital ressources
extérieures (prêts) ; **total capital** ; **total des prévisions**. Scale declared once, in a note
row near the top (`en milliers de francs CFA`).

**Why it is the best artefact a francophone budget can offer.** It is the estimates volume with no
OCR problem — in Benin the enacted loi de finances itself was image-only three years running while
this workbook was native — and, uniquely, it **states the interior/exterior split per programme**,
which is exactly what the origin gate needs and what no narrative document supplies.

**Strategy.** Read with `openpyxl`, `data_only=True`. Find the year header row by scanning the
first ~10 rows for four or more integers in 2015–2040; those cells *are* the block starts. Read
the economic column headers two rows below. Classify each row by whether column 2 is populated.
Then reconcile: programme and dotation lines must sum to the printed `TOTAL BUDGET DE L'ETAT`.

**Traps.**

- **The block stride changes between editions** — 9 columns in one year's edition, 8 or 9
  irregularly in the next. Never hard-code offsets; derive them from the year header row.
- **⚠ Prior-year columns are restated, and nothing says so.** A later edition's figures for a
  closed year differ across the board from the edition contemporaneous with that year — in Benin
  the whole-budget total, the digital ministry and three programmes all moved, one by 26%. The
  contemporaneous edition is the one that matches the enacted law and the ministries' own
  performance reports. **For an appropriation, use the year's own edition; treat later editions'
  prior-year columns as unlabelled restatements** and say so rather than guessing the stage.
- **Ministry header totals need not equal their own lines.** Two ministries in one edition
  disagreed with the sum beneath them (an unallocated reserve in one, a fund listed under a
  ministry but excluded from its header in the other). Reconcile at the grand total, and treat a
  ministry-level mismatch as a finding to note, not an extraction error to chase.
- **Retired programme codes are carried at zero** rather than dropped, so a zero is not always an
  unfunded programme.

**What it yields.** `appropriated` (and, from the PLF-stage edition, `proposed`) at programme
grain, cross-vote, with the capital/recurrent and domestic/external splits — the full input the
driver's origin gate and amount fields want.

## Archetype M — LOLF full estimates volume that states its own origin split

*Seen as: Burkina Faso, *Loi de finances pour l'exécution du budget de l'Etat* published whole —
1 544 pp (FY2024), 1 560 (FY2025), 1 480 (FY2026), native text throughout the tables.* A
**UEMOA/LOLF artefact in PDF**, so expect the shape across francophone West Africa wherever the
finance law is published as one volume rather than as a law plus separate annexes.

**Layout.** One chapter per **section** (ministries and constitutional institutions alike),
each giving, in this order: *PREVISION DES DEPENSES GLOBALES PAR NATURE* → *…PAR PROGRAMME* →
*…PAR PROGRAMME ET PAR NATURE* → *PREVISION DES DEPENSES PAR ACTIONS* → *PREVISIONS DES DEPENSES
PAR PROGRAMMES, ACTIONS, PAR CHAPITRES ET PAR ACTIVITES*, then a performance framework. AE and
CP over three years. Scale declared per table, `en milliers de F CFA`.

**Why it is worth the trouble.** The *par nature* table breaks capital into **Etat Seul / Etat
(Contrepartie) / Subvention / Prêt** — the origin gate printed on the face of the vote, which
almost no other estimates volume supplies. Archetype L (the Benin workbook) gives the same split
per programme; this gives it per section, which is coarser but is a PDF you will actually find.

**Strategy.**

1. `pdftotext -table -enc UTF-8` the whole volume once (~4 s for 1 500 pp); `-layout` renders
   digit groups with single spaces and is unusable here.
2. Locate sections by grepping `Section NN :` — **printed page ≠ PDF page** (printed 1058 = PDF
   1103 in the FY2026 edition), so the SOMMAIRE's numbers will not find them.
3. Read the four summary tables per section; take programme figures from *PAR PROGRAMME*, never
   from the activity table.
4. Attribute the origin split to programmes by **arithmetic, not apportionment**: identify the
   named *Etat Seul* chapters and check they sum to the section's *Etat Seul* line. Where a
   *Contrepartie* line could sit under either of two externally-financed chapters, it is **not
   attributable** and the programme's domestic figure is a floor — say so rather than splitting it.

**Traps.**

- **⚠ The activity table double-counts personnel.** A staff line appears twice — once
  parenthesised against its own action, once at the section's `SOLDE MENSUELLE` chapter. So the
  activity table's programme subtotal exceeds the *PAR PROGRAMME* table's, by exactly the
  parenthesised amount. **Parentheses here mean "carried at another chapitre", not a negative.**
  Always take programme and action figures from the summary tables.
- **⚠ Do not parse the money with a regex or by column position.** `-table` renders a
  within-number digit-group gap and a between-column gap with the same character, and its
  per-page column model does not align the `AE CP AE CP AE CP` header row with the data rows
  (measured: header `AE` at col 107, the row's own first figure at col 115). A greedy numeric
  regex silently returns the **third year's** column. Scan for the *lines*
  (`scripts/bfa-volume-scan.py` prints each hit's figures verbatim and parses none of them), then
  read the figures for the handful of tables that matter by eye and cross-foot them.
- **Chapitre codes are reused across sections** — `1801900311` is PACTDIGITAL in section 31 and
  "acquisition de motos d'escorte" in section 01. Always qualify a chapitre by its section.
- **The embedded law articles are a scan even where the tables are native** (a bad OCR layer in
  one edition, zero characters in the next two). Judge the file by its tables, not its first 50
  pages, and get the articles from the parliament's own copy.

**What it yields.** `appropriated` (and `proposed`, from the PLF-stage edition of the same
volume) at programme, action and chapitre grain, cross-vote, with the domestic/external split —
and, paired with archetype H's execution annexes, the full appropriation↔outturn series.


### Francophone SIM_ba variant — the volume states its origin twice *(added 2026-07-26, Central African Republic)*

*Seen as: Central African Republic, *projet de loi de finances — volume des charges*, 579 pp
(FY2025), 602 (FY2026), native throughout, 43–44 sections, every page footed `Edité par
SIM_ba le …` and labelled `Version : Projet de loi`.* Same LOLF ancestry as the Burkina
volume above, but a **budget de moyens** — section → service → TITRE II–V → imputation, with
no programme structure at all. **Extend archetype M rather than treating it as new**; the four
properties below are what differ.

**Layout.** Columns run `Fonction` (4-digit) → `Imputation` (the full chart-of-accounts key,
`85.88.00.20.120000.6439.11`) → `Intitulé` (economic nature) → **prior-year `Collectif YYYY`**
→ **`Financement intérieur`** → **`Financement extérieur` → `Dons` / `Emprunt`** → `Crédit
YYYY` → `Variation` (valeur, %). Scale `milliers de FCFA`, printed. Free-text activity labels
sit in a **separate left-hand column of their own**, not in `Intitulé`.

1. **⚠ The origin gate is in the account key as well as the columns.** The imputation's last
   segment is the funding source: **`.11` domestic, `.25` external grant, `.44` external
   loan**. Verified over **10 898 imputation rows in two volumes with no exceptions**. This
   matters because it survives on a *single line* — a procurement notice, an execution annex,
   an OCR'd fragment — where a column set needs the whole table. Test it before trusting it on
   another state, but test it: it is the cheapest origin gate in this corpus.
2. **⚠ The prior-year column is the *enacted collectif*, so a native volume closes a scanned
   year.** `Collectif 2024` in the FY2025 volume is the FY2024 revised budget, line by line —
   and CAR's actual collectif volumes are 700-page image-only scans. **The revised stage for
   year N is therefore extractable, without OCR, from year N+1's draft budget.** Same property
   as archetype N's `Authorised` column, in a francophone volume. Cross-foot the comparator
   column against its own printed subtotals, which it satisfies exactly.
3. **⚠ Bind free-text labels by page geometry, never by the text stream.** `pdftotext -layout`
   interleaves the three left-hand columns unpredictably. Read `pdfplumber.extract_words()`,
   group by `top`, and the columns are unambiguous: **x≈35 `Fonction` | x≈60 `Imputation` |
   x≈79 the activity LABEL | x≈177 `Intitulé` | x≥425 the amounts, right-aligned**. The rule is
   that **a label at x≈79 belongs to the imputation row immediately BELOW it**. Assign amounts
   by each number's **right edge**, not its left — the columns are right-aligned and a
   left-edge parse drifts with magnitude. `scripts/caf-simba-extract.py` implements this;
   ~75 s for a 600-page volume.
4. **⚠ TRAP — the first block of a section chapter is not the section.** Each chapter opens
   with the *Cabinet du Ministre* service block, whose `TITRE II`…`TITRE V` lines look exactly
   like section totals. The section recapitulation is the **last page of the chapter**
   (`TOTAL NN MINISTERE …` followed by `Total chapitres`). Reading the first block as the
   section understated CAR's FY2026 digital investment by half and inverted its direction
   (34 000 / −66% published, against a true 70 000 / −30%). **The tell is free: the Cabinet
   TITREs do not sum to the stated section total.** Cross-foot before publishing.

**The companion document: a programme restatement with no legal force.** CAR publishes a
*Cadre des Dépenses à Moyen Terme sectoriels … à titre expérimental* (183 pp, native, full
francs not milliers) whose running head is `BUDGET DÉTAILLÉ PAR ACTIVITÉ` — `PROGRAMME (5) →
ACTION (7) → ACTIVITÉ (19)`, AE and CP over three years. It **reconciles to the legal volume to
the franc** and it names the activity behind every line the *budget de moyens* leaves as
`Transferts courants aux autres unités administratives`. Use it for **purpose and for
verification**, never as the appropriating instrument: record the finance law as the
instrument and the CDMT as the source of the description. Where a state publishes both, expect
them to **group differently** — the same money can be one activity here and three imputations
there — so cite the grain you read and never net one against the other.

**What it yields.** `proposed` at imputation grain, cross-vote, with the domestic/external
split on every line; `revised` for the preceding year from the comparator column; and, where
the programme restatement exists, a purpose label for every figure. **Not** `appropriated` —
the enacted law is a separate, scanned document, and until it is read no figure from the draft
may claim that stage.

## Archetype N — anglophone line-item estimates volume with a printed Source-of-Financing column

*Seen as: Botswana, *Estimates of Expenditure from the Consolidated and Development Funds* — 564 pp
(FY2024/25), 621 (FY2025/26), 612 (FY2026/27), native text throughout, one volume per year covering
every organisation.* A **Westminster line-item (not programme) budget**, so expect the shape wherever a
state never adopted programme budgeting: the recurrent half is chart-of-accounts detail, not
programmes.

**Layout.** Two halves under one cover.

- **Recurrent** — `Organisation → Department → Parent account → Account`, each department's accounts
  listed to four-figure codes (`00110 Salaries and Allowances`, `04349 Computer Replacement`), then a
  per-organisation summary table `Actual Expenditure to <prior FY end> | Authorised Expenditure
  <prior FY> | Estimate <FY>`.
- **Development** — `Organisation → Department → Project`, columns `TEC | REVISED TEC | Estimated
  Expenditure <prior FY> | Estimated Expenditure <FY> | Balance of TEC | **SOF** | Allocation by SOF`.

**Why it is worth the trouble — two properties that solve problems other archetypes leave open.**

1. **The origin gate is a printed column.** `SOF` (Source of Financing) sits on every capital line. In
   Botswana every entry reads `DDF` (Domestic Development Fund) and no external code appears anywhere,
   so the domestic share is the document's own and needs no apportionment — the same job archetype M's
   *Etat Seul* split does, in one column instead of four. The national check is the companion
   *Financial Statements, Tables and Estimates of Revenues* volume, whose **Table IV** splits the whole
   development budget into External Grants / External Loans / Domestic Loans / Domestic Development
   Fund, every column summing exactly to its printed total.
2. **⚠ Every volume carries prior-year columns, so a later volume closes an earlier year.** The
   recurrent summary's `Authorised` column is year N−1's **revised** estimate and its `Actual` column
   year N−2's **outturn**; the development table's first estimate column is year N−1 **revised**, and
   from the NDP 12 edition there is also an `Actual Expenditure (<date>)` column. **This is the whole
   extraction strategy where a state publishes no execution reports** — Botswana published none of its
   FY2024/25 quarterly reports (its own page printed "(Unavailable)") and its Auditor-General was seven
   months overdue, yet appropriated / revised / actual are all obtainable by reading three consecutive
   volumes. The **development** outturn is not in the estimates volume at all: it is in **Table II** of
   the Financial Statements volume, by organisation, running six years back.

**Strategy.**

1. `pdftotext -table` the whole volume (~2 s for 600 pp). **`-layout` is offset on every summary page**
   — recurrent organisation summaries and the Appropriation Act's Schedule alike.
2. Index organisations by grepping `^\s*Organisation\s+\d{4}` in the development half and
   `Ministry\s*:?\s*\d{4}` in the recurrent half; departments the same way one level down.
3. Read the project lines. **Verify each row by the table's own arithmetic** — `REVISED TEC − revised
   estimate − current estimate = Balance of TEC`, and the last column (`Allocation by SOF`) **equals
   the current-year estimate**, which is the cheapest single check available.
4. Sum department lines to the printed `DEPARTMENT TOTAL` and those to `MINISTRY TOTAL`.

**Traps.**

- **⚠ A blank cell shifts every column right of it.** Where the actual column is empty the row's
  remaining figures move left by one, so a positional parse silently reads the *balance* as the
  estimate. This is what makes the `Allocation by SOF` check load-bearing, not optional.
- **The two halves name the same department code differently** (Botswana FY2024/25: `2404` is
  *Digital Communications, Infrastructure and Business* in the recurrent half and *Telecommunications
  and Postal Services* in the development half). **Join on the code, never the name.**
- **The `Authorised` column is not always a restatement.** Where the state declines to revise
  recurrent — Botswana FY2025/26, by stated policy — it reproduces the original estimate line for line.
  Check the equality; do not assume either way, and do not build a `revised` record that merely
  duplicates the appropriation.
- **Project codes are reissued when the national development plan changes** (Botswana TNDP `11631` →
  NDP 12 `12481`, and the same for every line). A development series keyed on project code needs a
  mapping row at the plan boundary.
- **Page numbers leak into the text stream** and prefix a project row (`28 11861 MoE
  Computerisation …`), so anchor a row regex on the code, not on line-start.
- **`ict` and `information` are substrings of `district`, `restrict`, `Industrial Court` and
  `Performance Management System`.** Botswana's `11551 IC Infrastructure` is *Industrial Court*
  infrastructure — P19.8m that inflates a cross-vote total by 4% if taken.

**The companion document: the Committee of Supply speech.** In a Westminster estimates system the
volume names no systems at all — Botswana's says only `<Ministry> Computerisation` — and the **minister's
Committee of Supply speech is where the systems are named and, often, priced**. The FY2026/27 season
put figures on the biometric identity card, electronic voter registration, a health information
exchange keyed on the national ID number and four separate court case-management builds, none of which
appears in 1,800 pages of estimates. **But the speeches itemise selectively**: read them for names,
sub-lines and execution commentary, and take the totals from the volume — a cross-vote total built from
speeches came to 42% of the one the volume gives.

**What it yields.** `appropriated`, `revised` and `actual` at project grain for capital and department
grain for recurrent, cross-vote, with the domestic/external split printed — and, from the speeches,
named systems and sub-lines that can be recorded where the speech states their own figure.

## Archetype O — bilingual single-year estimates workbook with a printed four-way source-of-finance column

*Seen as: Ethiopia, *Federal Government Budget Proclamation Part Two* / *Executive Budget Proposal*, published annually as XLSX by the Ministry of Finance (EFY 2017, 2018 and 2019 editions read).* An **anglophone-plus-national-script programme budget in a spreadsheet**, so expect the shape wherever a state runs programme budgeting, publishes in two languages side by side, and posts the estimates as a workbook rather than a volume.

**Layout.** Eight sheets. The two that matter are `RECURRENTin AMha` (~2,050 rows) and `CAPITAL in AMHAric` (~2,250–2,650 rows) — **the names lie: both carry the national-script block in the left columns and a complete English block in the right columns.** Six summary sheets sit alongside (`Sum. of Revenue`, `Gov't Expend. & Its Financing`, `Fed. Gov't sum of Exp.`, `Revenue`, `Kelel Degoma Summary`, `Kelel SDG fund`).

Header row **4**, sub-header row **5**, data from row 6. The hierarchy is expressed by which code column is populated, not by indentation:

- **Recurrent** — `Pub. Body code | Program | Activity | Description | Treasury | Retained Revenue | Total`
- **Capital** — `Pub. Body Code | Program | Activity | Sub-Program | Project | Description | Treasury | Retained Revenue | Assistance | Loan | Total`

A row with a 3-digit code in the body column is a **public body** (or, where it ends in `0` or `00`, a function/sub-function aggregate — the leaf 3-digit codes are the bodies). Rows beneath it carry a programme code, then an activity code, then in the capital sheet a sub-programme and a named project. **Walk the block between one 3-digit code and the next**; there is no other delimiter.

**Why it is worth the trouble — the origin gate is four printed columns, at project grain.**

`Treasury / Retained Revenue / Assistance / Loan` sits on every capital line and `Treasury / Retained Revenue` on every recurrent line. This is finer than archetype M's *Etat Seul* split and finer than archetype N's single `SOF` code: it separates **domestic tax money, the body's own fee income, external grant and external loan**, per project, as the state's own disclosure. Two things fall out that no other archetype gives cheaply:

1. **The domestic share of a headline is directly readable.** Ethiopia's *Digital Economy and ICT* programme reads 2,058,850,000 birr in EFY 2017 and is **10.0% Ethiopian money** — 206,750,000 Treasury against 1,852,100,000 Loan.
2. **`Retained Revenue` answers the regulator question the sweep's Block 4c exists to ask.** Ethiopia's data protection authority (the communications regulator) is 67–70% funded from its own licence and spectrum fees in every year read, and its national registry body takes **zero** treasury money. Neither fact is visible in the body's total.

**Strategy.**

1. `openpyxl`, `data_only=True`. **Set `PYTHONIOENCODING=utf-8` before anything** — a national-script cell kills a default Windows console read on the first sheet.
2. Read header row 4 and **locate every column by header name, per year** (see the trap below).
3. Index public bodies by `re.fullmatch(r"\d{3}", code)`; slice each body's block to the next such row.
4. Classify rows inside a block by which of `Program` / `Activity` / `Sub-Program` / `Project` is populated.
5. Reconcile: body totals to the printed function subtotals to the grand total, and the grand total to the appropriation article of the proclamation.

**Traps.**

- **⚠ THE COLUMN LAYOUT SHIFTS BETWEEN EDITIONS AND THE FAILURE IS SILENT.** Ethiopia's EFY 2017 recurrent sheet has a spacer column that EFY 2018 and EFY 2019 do not: `Pub. Body code` is col 9 in one year and col 8 in the next, `Total` col 15 then col 14. A parser carrying the previous year's offsets **returns an empty result set rather than raising** — it finds no 3-digit codes where it looks and reports the country has no digital bodies. Locate by header name every time.
- **The sheet names describe only the left-hand block.** `RECURRENTin AMha` and `CAPITAL in AMHAric` both contain full English. Do not transliterate or machine-translate; the English is already there.
- **The summary sheets can shrink without the detail shrinking.** Ethiopia's EFY 2019 edition has `Sum. of Revenue` at 25 rows against 386 the year before, and `Revenue` at 251 against 614, while both detail sheets stay full size. Any cross-foot that leaned on a summary sheet must be re-derived from detail.
- **`dc:title` is a stale template.** All three Ethiopian editions carry `Federal Governemnt Budget Proclamation 2008 I` (sic) in `docProps/core.xml`. It says nothing about the file. **`dcterms:modified`, however, is load-bearing — see the stage trap below.**
- **Project descriptions carry the state's own typos** — `Natiobal ICT Infrstructure anf Expansation`, `Statstics Digitalization`, `Data Warehouse & Business Intellegence System`. Quote them verbatim; do not correct them, and do not key a lookup on the spelling.
- **A 3-digit code ending in `0` or `00` is a function aggregate, not a body.** Summing all 3-digit rows double-counts the whole budget.

**⚠ THE STAGE TRAP — read the file timestamp against the enactment date, every year.**

A ministry that publishes the proclamation from a template may publish it **before** the legislature passes it, leaving `PROCLAMATION NO. -----------------` unfilled — and may publish the *proposal* under a label that says *Proclamation*. Ethiopia did both:

| Edition | `docProps` modified | Enactment | What the lines actually are |
|---|---|---|---|
| EFY 2017 | 2024-06-25 | 2024-07-04 | **`proposed`** — and the same file is served under two labels, byte-identical, one of them *Executive Budget Proposal* |
| EFY 2018 | 2025-06-26 | 2025-07-03 | pre-enactment, but totals equal the reported approval → `appropriated` with the caveat recorded |
| EFY 2019 | 2026-07-09 | 2026-07-07 | **post-enactment → `appropriated` cleanly**; filename gains an `_updated` suffix |

**The unfilled proclamation number is not the test — the timestamp is**, because it stays blank in all three years including the one published after enactment. Check `docProps/core.xml` `dcterms:modified` (XLSX) and `CreationDate` (PDF) against the reported ratification date before setting `baseline_stage`.

**What it yields.** `proposed` or `appropriated` (per the stage trap) at programme, activity and named-project grain, cross-vote, with a four-way origin split printed on every capital line and a two-way split on every recurrent line.

## Archetype P — accounting-system year-end extract carrying three budget stages in one table

*Seen as: Ethiopia, *FY 2017 Fourth Quarter Federal Budget Vs Expenditure Summary Report*, XLSX, published by the Ministry of Finance from IFMIS/IBEX; the Q1 edition of the same series is a PDF.* Output of the government's own financial-management information system rather than a drafted document, so expect the shape wherever a state publishes IFMIS extracts — and **prefer it to every narrative execution report**, because it is machine-readable and carries the ladder.

**Layout.** A long preamble (introduction, notes, contents) then a single table beginning around row 62–65. The header block states the ledger, fiscal year and **`Period Name`**, which is what identifies the quarter:

```
Ledger Name : Federal MCL Ledger Set   Fiscal Year : 2017   Period Name : Sene-2017
Public Body | Description | Approved Budget | Adjusted Budget | YTD | Fourth Quarter | Over/Under
```

Rows alternate **5-digit public-body codes** with **7-digit economic-classification codes** beneath each (`2100000` Compensation to Employees, `2200000` Use of Goods and Services, `2300000` Expenditures on Fixed Assets and Construction, `2600000` Grants, `2800000` Other Expenses). **Parse on code width**; there is no other marker.

**Why it is the most valuable single artefact in an execution-poor corpus.** Three stages in one table:

| Column | `budget_stage` |
|---|---|
| `Approved Budget` | **appropriated** — the enacted appropriation as loaded to the accounting system |
| `Adjusted Budget` | **revised** — post-supplementary and post-transfer |
| `YTD`, in the year-end period file | **actual** |

In Ethiopia this is also the **only** enacted figure the state publishes at all, because the estimates workbook is pre-enactment (archetype O's stage trap). So the two documents are read together: the workbook gives composition and origin, the IFMIS extract gives the enacted, revised and executed totals — and the difference between the workbook's total and the `Approved Budget` column **is the legislature's amendment during passage**, which is otherwise invisible. Ethiopia's EFY 2017: seven digital bodies passed unchanged, while the communications regulator was cut by 100,000 birr, the AI institute by 12,650,000 and the space institute by 32,450,000.

**Strategy.**

1. Read the header block for `Fiscal Year` and `Period Name`; **the period, not the filename, identifies the quarter.**
2. Take rows whose first cell matches `\d{5}` as bodies; the 7-digit rows beneath give the economic split.
3. Map the 5-digit accounting codes to the estimates volume's 3-digit budget codes **by name and by cross-footing the totals** — they are different code systems and there is no published crosswalk.
4. Cross-foot every body used: estimates recurrent + capital against `Approved Budget`.

**Traps.**

- **⚠ COVERAGE IS PARTIAL AND THE TOTALS WILL NOT TIE TO THE APPROPRIATION ACT.** The Ethiopian report states 174 federal public sites of which **118 use IFMIS and 56 use IBEX**, reported in separate sections. Administration & General shows 128,727,319,961.98 approved against the proclamation's 150,184,732,667 for the same function; the gap is the IBEX population, not an error. **Never present an IFMIS total as a national total.**
- **⚠ The accounting system's body codes are not the budget's body codes, and one budget body can appear under several.** Ethiopia's Statistics Service appears as `10028 Central Statistics` (which ties exactly to the volume) and `11035 Ethiopian Statistics Service` (which is a third of it). Picking the wrong one produced a 2.7bn birr phantom variance. Cross-foot before trusting a mapping, and where no code ties, **claim no execution rate for that body**.
- **The introductory prose is copy-pasted between quarters.** Ethiopia's Q4 file says in its own notes *"the report consists of 3rd Quarter financial report"*. The title row, `Period Name` and the quarter column header are authoritative; the prose is not.
- **A missing quarter can hide behind a mislabelled link.** Ethiopia's library offers a "2nd Quarter" file that is a second copy of Q3 (same `Period Name`, identical rows). Check `Period Name` on every file before staging; the series was Q1 → Q3 → Q4 with **no Q2 published**.

**⚠ WHAT THIS ARCHETYPE FINDS THAT NOTHING ELSE DOES — externally-financed programmes with a zero appropriation.**

Donor-financed projects enter the budget **mid-year**, under the provision that lets public bodies record additional loan and assistance funds on their own heads (Ethiopia: Article 3(3) of the budget proclamation). They therefore appear with **`Approved Budget` = 0**, a large `Adjusted Budget`, and near-100% execution — and they are **invisible in the estimates volume entirely**. Ethiopia FY2024/25:

```
14485  MoIT - Ethiopian Digital Foundation Project      0 | 7,041,485,908 | 7,041,485,908  (100.0%)
14166  OPM - Ethiopia Digital ID for Inclusion          0 | 3,055,354,504 | 3,055,354,503  (100.0%)
11037  Ministry of Innovation and Technology  2,754,552,330 | 2,947,641,829 |   989,820,128  (35.9%)
```

**Grep the body list for zero-approved rows with non-zero YTD before anything else** — that one filter surfaced the two largest digital programmes in the country, both of which the origin gate routes to `non-state` and both of which definite-matched to World Bank deals the wiki already held. It also produced the sharpest fact in the Ethiopian corpus: the donor project was **2.6× the ICT ministry's entire voted budget and 7.1× what the ministry actually spent**.

**What it yields.** `appropriated`, `revised` and `actual` at public-body × economic-classification grain, both execution bases, the legislature's amendments during passage, and — uniquely — the externally-financed programmes that never appear in the estimates at all.

## Archetype Q — compact programme-budget summary table, space-separated thousands and a stacked code column

*Seen as: Cameroon, *projet de loi de finances* — 122 pp (FY2024), 111 (FY2025), 154 (FY2026),
native text throughout, 59 votes.* **Not archetype M.** M is a 1 500-page line-item LOLF volume;
this is the *whole appropriation of a state in about a hundred pages*, because it stops at
programme grain — no action, no activity, no imputation, no economic nature and **no origin
split**. The trade is coverage for depth: one short native file gives every vote, but nothing
below the programme, so the domestic/external split has to come from elsewhere entirely.

**Layout.** One continuous table, votes running on from each other rather than one chapter apiece.
Header `N° CODE | LIBELLE | OBJECTIF | INDICATEUR | AE | CP`, scale printed per page as
`(Unité : Milliers FCFA)` / `(En millier de FCFA)`. A vote row —
`CHAPITRE 45 - MINISTERE DES POSTES ET TELECOMMUNICATIONS` with its total on the right — is
followed by one row per programme carrying **two codes** (an internal sequence number and the
programme code: `149 129`), the programme label, its objective, its indicator, and AE / CP.
**AE equals CP on every line seen** across three years and 59 votes.

**⚠ The vote unit is renamed between years.** Cameroon's FY2024 and FY2025 volumes say `CHAPITRE`;
FY2026 says `SECTION`, and simultaneously renumbers every programme. Parameterise the unit word —
do not hard-code it — and expect the renaming to carry a programme-code restructure with it.

**Strategy.** Parse by page geometry (`scripts/cmr-plf-extract.py`, ~10 s a volume):

1. Group `pdfplumber.extract_words()` by `top` (tolerance ≈ 2.5) into visual rows.
2. **Re-join numeric tokens by x-gap before reading any figure.** Split on a gap wider than
   about 7 pt; that gap is also what separates the AE column from the CP column.
3. Take codes as the short integers left of ≈ 0.13 × page width, amounts as the joined numbers
   right of ≈ 0.60 × width, and require ≥ 4 digits to exclude page numbers and indicator numerals.
4. Cross-foot every vote: the programme rows must sum to the printed vote total.

**Traps.**

- **⚠ Thousands are separated by a space, so `18 611 000` arrives as three words.** Any parse that
  reads word-by-word silently returns `18`. This is the single thing that breaks a naive extractor
  here, and it breaks it quietly — `18` is a plausible-looking number.
- **⚠ The code column is stacked and `-layout` interleaves it.** Where a vote has four programmes
  the renderer prints `149 129 / 150 130 / 151 131` together *above* the amounts, so codes and
  figures drift apart and a text-stream parse pairs the wrong ones. Bind by row `top`; the
  geometry is unambiguous where the text stream is not. (Same lesson as archetype M's SIM_ba
  variant, in a much smaller volume.)
- **⚠ Labels wrap across rows, so a narrow label band drops them.** Amounts and codes bind
  reliably; **labels do not** — a label column read at a fixed x-band returns fragments
  (`130 L'ECOSYSTEME NATIONAL DU numérique`). Take figures from the geometry parse and **read the
  labels off `pdftotext -layout` for the handful of votes that matter**. A cross-vote keyword scan
  run against geometry-derived labels will return **zero hits and look like a clean negative** —
  it is not. Scan the `-layout` text, then bind the figures.
- **The enacted law is a scan; only the bill is native** — so everything this archetype yields is
  `proposed` until the enacted text is read. See the Cameroon section of
  `domestic-budget-extraction.md`.

**What it yields.** `proposed` at programme grain, **cross-vote, all 59 votes, in one short native
file** — with the objective and indicator text attached to each programme, which is unusually rich
and is where a state's digital policy targets are actually written down. **Not** the
domestic/external split, **not** economic nature, and **not** `appropriated`.

### Gazette variant — the finance law as published in the *Journal officiel* *(added 2026-08-03, Republic of the Congo)*

*Seen as: Republic of the Congo, `Journal officiel … édition spéciale` carrying the whole finance law — 92 pp (LF2024), 84 (LF2025), 114 (LF2026), 80 (LFR2025), plus the PLF editions at 140 and 202 pp, all native.* Same compact whole-state shape as archetype Q and the same three-independent-vertical-stacks drift, so **extend Q rather than adding a letter**. Six properties differ, and four of them are traps Q does not carry.

1. **⚠ THE GAZETTE IS NATIVE WHERE THE MINISTRY'S COPY IS A SCAN, AND THIS IS THE CHEAPEST WIN IN THE FRANCOPHONE CORPUS.** `finances.gouv.cg` publishes Congolese finance laws as page images (LF2024 **150 chars over 150 pp**, LF2025 144 over 144, LF2026 **0 over 238**); `sgg.cg`, the publication of record, publishes the identical instrument with a text layer (307 225, 274 497, **615 522**). **Before commissioning OCR on any francophone finance law, look for the gazette.** And where the gazette serves several renderings of one issue, **the smaller file is the native one** — `congo-jo-2026-21-2.pdf` is 625 KB of text against `congo-jo-2026-21.pdf` at 2.7 MB of page images. Follow the index link; never construct the bare `…-NN.pdf` path.
2. **The law carries two tables, not one, and they cross-foot against each other.** A *programmes* table (`Code NN` ministry → three-digit programme → CP) and, ten pages later, an *institution et ministère* table (`Code NN` → `Titre 2` personnel / `Titre 3` biens et services / `Titre 4` transferts / `Sous-total` / `Titre 5` investissement / `Total`). Archetype Q's Cameroonian volume has no economic nature at all; here **the capital/recurrent split is printed**, and the two tables agreeing at the ministry total is the free arithmetic proof that both were read right. Congo FY2026: 1 065 948 780 + 30 139 589 283 = 31 205 538 063 = 2 479 538 063 + 28 726 000 000.
3. **⚠ USE `page.chars`, NOT `extract_words()`. Word-level extraction silently DROPS GLYPHS on these files.** In the FY2025 execution report `extract_words()` returns `Code4` for `Code 45` and `2407866578` for `24 078 665 787` — **the last digit of every amount in the table**, which divides the figure by ten and still looks like money. Character-level binding on the same page returns both correctly. This is a worse failure than drift, because drift attaches a *right* number to a *wrong* row and this returns a *wrong* number. Group `page.chars` by `top` (tol ≈ 2.5), sort by `x0`, then split the numeric side into columns by x-gap (> 4 pt) — the amount columns run together in the character stream (`…numérique24 078 665 7873 630 627 58215,1`) and only geometry separates them.
4. **⚠ A state mid-LOLF-transition changes its own grain between years, inside one corpus.** Congo's `Article trente-huitième` of LF2024 presents programme budgets *« à titre expérimental »* for **six pilot ministries** and by ministry-and-titre for everyone else; from LF2025 all 136 (then 139) programmes are published. So the same vote is a **ministry envelope in FY2024 and a programme in FY2025**, and the two figures are not comparable. Check which article governs the year before assuming the previous year's grain, and say on the record which it was.
5. **The comptes spéciaux du trésor are a second appropriating table and they are where the digital money outside the vote sits.** Each account gets its own recettes/dépenses table (`Total Recettes (2)` / `Total Dépenses (3)` / `Dépenses ordinaires` / `Dépenses en capital` by titre) and the accounts sum exactly to the article's stated ceiling — Congo FY2026, twelve accounts summing to 171 653 000 000 to the franc. Two of them are digital single-purpose funds. **A cross-vote scan that stops at the programme table misses them.**
6. **The `n° N-YYYY` special-edition number means nothing.** Congo gazettes the finance law in whichever special edition falls next — n° 6-2023 for LF2024, n° 15-2024 for LF2025, n° 1-2026 for the settlement law, n° 2-2026 for the rectificative, n° 3-2026 for LF2026. **Identify by opening page 2.** One document in this corpus was staged on the pattern and turned out to be machinery-of-government decrees.

**Minor traps.** The `fi` ligature does not extract (`finances` → `fi nances`; grep `fi ?nance`). A ceiling stated in words is rounded to the million while the detail tables are exact, so a 428 571 FCFA residual against a stated total is the *words*, not a misread. Scale is **full francs CFA with space-separated thousands and no header** on the programme and ministry tables, while the equilibrium tables in the same document are `En milliards de FCFA` — read the header per table.

**What it yields.** `proposed` (PLF edition), `appropriated` (enacted gazette) and `revised` (rectificative, which in Congo *replaces* the initial law rather than amending it, so it is a `restated-total`) at programme grain cross-vote, plus the capital/recurrent split at ministry grain and the special-account appropriations — and, paired with the state's execution report, the full ladder.

## Archetype R — Lusophone *Boletim Oficial* estimates volume with a programme × financing-type mapa and an earmarked-revenue annex *(added 2026-08-04, Cabo Verde)*

*Seen as: Cabo Verde, `Lei n.º 35/X/2023` (OE 2024, 128 pp), `Lei n.º 45/X/2024` (OE 2025, 166 pp), `Lei n.º 69/X/2025` (OE 2026, 266 pp), all published whole in the Boletim Oficial and all native.* The Lusophone counterpart of archetype M: the finance law *is* the estimates volume, mapas and all, so tier 0 closes without an acquisition. Expect the shape wherever a Lusophone state publishes the OE as one BO issue.

**Layout.** Articulated law, then `Mapa I` to `Mapa XV` (receitas económica; despesas económica; **despesas orgânica**; despesas funcional; receita and despesa of the *serviços e fundos autónomos*, one mapa per ministry plus a total; **despesa por programa e tipo de financiamento**; segurança social; municipal transfers; public enterprises; gender), then — in some years — the Assembly's own *Orçamento Privativo* as a numbered *Resolução*, and the *receitas consignadas* annex.

**⚠ Trap 1 — the mapa pages may be printed rotated 90°, and rotation is not a property of the series.** FY2024 and FY2025 rotate; **FY2026 does not**. On a rotated page `pdftotext -layout` recovers the character order but scrambles the row/column alignment, and `pdfplumber` returns the text **character-reversed** (`oiretsiniM aD aimonocE latigiD`). This is native text in a rotated CTM and must **never** be sent to OCR. Recipe: `extract_words()`, group by `round(x0/6)`, sort each group by descending `top`, reverse each token; then every row cross-foots. **A BO page that returns reversed strings is a rotation; a page that returns nothing is a scan. Test which, every year.**

**⚠ Trap 2 — `Mapa III` is ministry × programme *type*, not ministry × programme.** Its three money columns are `Programa de Investimento | Programa Finalístico | Programa de Gestão e Apoio Administrativo`. There is no programme breakdown on the organic axis at any published grain, so a ministry row is an **envelope** and the driver's envelope rule bites.

**⚠ Trap 3 — and the reason this archetype earns its letter: `Mapa VII — Despesa por Programa e Tipo de Financiamento` is where purpose and origin are printed together.** Columns `Tesouro | OFN (Outras Fontes Nacionais) | FCP AAL (Fundo de Contravalor / Ajuda Alimentar) | Donativo | Empréstimo | Total`, rows `Pilar (Eixo) / Programa` across the whole state. **`Tesouro + OFN` is the domestic share; `Donativo + Empréstimo` is external.** The origin gate is handed over ready-made at the only grain where a line's stated purpose is digital. The same mapa reappears in the `Conta Geral do Estado` and in every quarterly `Conta Provisória` with `OI | ORP | EXE` columns, so **one table carries the whole stage ladder, cross-vote, with the origin split on both the reprogrammed and the executed side.** Build the records here.

**⚠ Trap 4 — `Mapa VII`'s programme perimeters are not stable between years.** Cabo Verde's *Modernização do Estado e da Administração Pública* runs 609,582,068 → 5,434,369,323 → 976,042,125 CVE across FY2024–FY2026 while the corresponding ministry vote runs 368,989,734 → 269,785,474 → 292,594,728. Each year's pillar column cross-foots, so these are real reclassifications. **Never read a trend off two years of this axis without checking the pillar subtotals.** Organic codes move too (state modernisation `01.03.10` → `01.03.11`).

**⚠ Trap 5 — the `receitas consignadas e respectivas contrapartidas em despesas` annex is where DPI, the universal-service fund and the one-stop-shop are financed, and it is invisible to every classification.** Required by the budget framework law (Cabo Verde: `Lei n.º 55/IX/2019` art. 36 h)). It pairs an earmarked revenue with its counterpart expenditure: an identity-document fee funding a national identity system, an operator contribution and spectrum fee funding a universal-service fund, a one-stop-shop service fee funding e-government projects. **None of it appears in `Mapa III`, `Mapa IV`, `Mapa VII` or the FSA mapas by name, so no keyword scan finds it.** Read the annex. **And check whether the *enacted* volume reprints it**: Cabo Verde's FY2025 and FY2026 laws do and its FY2024 law does not, so the same lines are `appropriated` in two years and only `proposed` in the third.

**⚠ Trap 6 — the independent authorities are in the legislature's own budget.** The data-protection authority, the media regulator, the ombudsman and the electoral commission are appropriated as *órgãos externos* inside the Assembly's *Orçamento Privativo*, published as a `Resolução` alongside the law. A cross-vote scan of the ministerial mapas would report that the state does not fund its DPA at all. **And the resolution is not published every year** — Cabo Verde's FY2026 volume carries none, and the electoral commission moved into `Mapa III` while the DPA did not surface anywhere.

**⚠ Trap 7 — the gender mapa is not an origin mapa.** `Mapa XV — Orçamento Por Níveis de Género e Orgânica` carries columns `Nível G0 | G1 | G2 | G3 | Total Contribuição Género`. These are gender-responsiveness levels and the "contribuição" is the gender contribution. A sweep read them as an external-contribution split and reported a false 47.5% external share for a ministry; the arithmetic gives it away, because the printed rate divides the G1–G3 execution by the G1–G3 budget, not the outturn by anything.

**Minor traps.** Four thousands separators can appear inside one country-year — full stops in one year's mapas, commas in the next, spaces in the provisional account, full stops in the *privativo*. Parse per table. Scale is **full escudos with no header anywhere**; prove it by cross-footing to the grand total. The `Anexo Informativo` and the `Relatório IPSAS` are native but text-sparse — use `extract_tables`. Strip the `kiosk.incv.cv` watermark and the copyright boilerplate. The proposal-stage mapas are published unrotated as standalone PDFs and are the cheaper target **only where the two versions agree** — the Assembly amends the package every year, and in FY2026 it amended the digital ministry's own rows.

**What it yields.** `proposed` (the tabled proposta and its mapas), `appropriated` (the enacted BO), `revised` (the quarterly `Conta Provisória`'s ORP column, which in a state with no rectificative statute *is* the revised stage) and `actual` (the same account's EXE column, and the `Conta Geral do Estado` at year end) — **at programme grain, cross-vote, with the domestic/external split printed at every stage.** The one stage it does not yield is `audited`.

## Archetype S — anglophone programme-based budget whose narrative is native and whose every financial table is a pasted image *(added 2026-08-05, Ghana)*

*Seen as: Ghana, `2024 Programme-Based Budget Estimates` per MDA — one volume per entity, ~120 pp, published by the Ministry of Finance from a Word template.* **The trap is not that it is a scan — it is that it is native text everywhere the money is not.** `pdftotext -enc UTF-8 | wc -c` returns 149,000 characters over 119 pages and every "is this native?" test passes; then the money is nowhere in the stream, because **all 23 financial pages are screenshots of the ministry's Hyperion output pasted into Word**. A pass that trusts the text layer concludes the volume carries no budget at all, which is what it looks like: policy narrative, non-financial performance indicators, and a Public Investment Plan project list at the end.

**How to spot it in one command.** Split the text stream on form feeds and count characters per page. The image pages come back at **exactly 26 characters** — the running footer `NN | 2024 BUDGET ESTIMATES` and nothing else. Confirm with `pdfplumber`: those pages carry `len(page.images) == 2` (the coat of arms plus the table) against `len(page.chars) ≈ 30`.

**Layout, once the pages are read.** Four table families, each repeated per programme: **`1.5 Appropriation Bill — Summary of Expenditure by Sub-Programme, Economic Item and Funding`** (the one that matters), then `2.6`, `2.8` and `3.x` chart-of-account restatements of the same money at different cuts. The 1.5 table is the whole entity on one page: rows are programme (5-digit) and sub-programme (8-digit) codes, columns are **four funding origins × three economic items** — `GoG` (compensation / goods and services / non-financial assets / total), `IGF` (the same four), `Funds / Others` (Statutory / ABFA / Others), `Donors` (goods and services / non-financial assets / total), then `Grand Total`.

**Why it is worth the trouble.** **The origin gate is four printed column blocks at sub-programme grain**, which is what archetype O gives in a spreadsheet and archetype N gives as a single code — here it separates treasury money, the body's own fee income, earmarked funds (including the oil Annual Budget Funding Amount) and donor money on every line. And the table cross-foots four ways, so a misread cannot survive.

**Strategy.**

1. `python scripts/ocr-pdf.py DOC.pdf --lang eng --pages <the 26-char pages> --dpi 400 --psm 6 --force` — `--force` is required because the document *does* have a text layer; it is just not on these pages. ~7 pages a second.
2. **Then render the 1.5 page and read it directly** (`pypdfium2` `.render(scale=300/72)`). OCR gets the labels and most of the digits, but drops whole rows out of a dense wide table; the render is legible and settles them. OCR is for locating the table and grepping it later, not for taking the figure.
3. Cross-foot before recording anything: each origin block's three economic items to its own total; the origin totals to the Grand Total; sub-programmes to their programme; programmes to the printed Grand Total.

**Traps.**

- **⚠ THE NARRATIVE NAMES MORE PROGRAMMES THAN THE APPROPRIATION FUNDS, AND NOTHING FLAGS IT.** Ghana's MLGRD volume describes **seven** programmes in Part B and appropriates **six**: *Births and Deaths Registration* — the country's civil-registration function, and the CRVS spine of its identity system — has no line in table 1.5 at any grain. Its whole digitisation programme (system consolidation, digitisation of manual records, a bandwidth upgrade, an electronic statistical reporting dashboard) is described in the narrative as World Bank PSRRP, HISWAP and UNICEF work. **Always diff the programmes in the narrative against the codes in the table**; the gap is a finding, not a parse error. It may also mean the body is appropriated under its own entity code in a different volume — say which you established and which you did not.
- **The narrative prices nothing.** Part B is objectives, descriptions, output indicators and an operations-and-projects list with no money anywhere. Every figure in the volume is in the image tables and the PIP.
- **The Public Investment Plan at the back is capital only and is not a digital seam.** Ghana's MLGRD PIP is 77 lines of admin blocks, staff bungalows and regional police commands. Its closing note — *"the difference between the Annual Ceiling and the Total Allocation for Projects … is earmarked for Non Infrastructure Capex. Ie Vehicles, Computers, Furniture etc."* — is the only place computers appear, and it prices nothing.
- **Sub-programme labels carry the state's own typos** (`Human Settlements and Land Use Reaseach and Policy`). Quote them verbatim; key on the code.
- **One volume is one entity.** The cross-vote scan cannot run from a PBB volume — it needs the Appropriation Act's Fourth Schedule (below).

**What it yields.** `appropriated` at sub-programme grain for one MDA, with a four-way origin split and the capital/recurrent split, for whichever year's volume you hold. **Not** cross-vote coverage, **not** any later stage, and **not** a programme the narrative describes but the table omits.

### Companion instrument — Ghana's Appropriation Act Fourth Schedule is the whole state at programme grain *(added 2026-08-05)*

*Seen as: Ghana, `Appropriation (No. 2) Act, 2025 (Act 1163)`, 20 pp, native text.* Same compact whole-state shape as archetype Q, so **extend Q rather than adding a letter** — but with two properties the Cameroonian volume lacks, and it is the cross-vote instrument for a state whose estimates are published one MDA at a time.

Four schedules: **First** the appropriation by economic classification; **Second** the retained internally generated funds by MDA; **Third** expenditure by MDA, economic item and funding; **Fourth** the same by **programme**. The Fourth Schedule is the record instrument — 57 MDAs, 170 programmes, eight pages, and it sums to the Act's own total appropriation (GHS 357,105,639,081 against a printed 357,105,639,080, a one-cedi rounding).

1. **The origin split is printed on every programme line** — the same fifteen columns as archetype S's table 1.5. So the origin gate runs cross-vote, at programme grain, off a twenty-page file.
2. **⚠ The text stream is unusable and the failure is the quiet kind.** `pdftotext -layout` drifts amounts several rows from their labels — the Second Schedule renders *Ministry of Communication, Digital Technology and Innovations* against 108,218,423, a figure belonging to another ministry entirely. **Bind by geometry**: group `page.chars` by `top`, join tokens on x-gap, assign each amount to a column by its **right edge**. `scripts/gha-appropriation-extract.py` does it; 234 rows, every one cross-footing.
3. **⚠ A wrapped programme label puts its own figures on the row BELOW the label.** `02603 - ICT Infrastructure,Regulation and` occupies one row and `Capacity Building` the next, with all twelve of its amounts on that second row. Carry a pending row forward rather than dropping a label that arrives without money.
4. **The Act rounds to the cedi**, so a one-cedi residual against a printed total is the document's own and not a misread. Anything larger is.
5. **⚠ THE CROSS-VOTE SCAN'S HANDLE IS THE PROGRAMME NAME, AND A TERM SEARCH RETURNS ALMOST NOTHING.** A digital-vocabulary regex over all 170 Ghanaian programmes returns five rows. Reading the names ministry by ministry adds the identity seam a term search cannot reach — `00903 Passport Administration` (GHS 148.8m, Ministry of Foreign Affairs) — and flags `00110 Information Management` (GHS 273.7m, Office of Government Machinery) as a line whose name will not say whether it is government communications or government IT. **Read the 170 names once; it takes a minute and it is where the identity money is.**
6. **The named digital-governance bodies are not votes.** Ghana's Data Protection Commission, Cyber Security Authority and National Information Technology Agency appear nowhere in 57 MDAs; on the vote structure they are funded inside one programme, `02603 ICT Infrastructure, Regulation and Capacity Building`. **The Right to Information Commission, by contrast, is its own MDA** (082) — so the absence of the others is a fact about them, not about how Ghana appropriates to independent bodies, and that contrast is what makes it worth stating.

**What it yields.** `appropriated` at programme grain, cross-vote, all 57 MDAs, with a four-way origin split and the capital/recurrent split on every line — the whole state in one short native file. **Not** sub-programme grain, and **not** any later stage.

### The FY2026 volumes, and how to read an image-only one *(added 2026-08-09)*

**⚠ Nativeness varies by volume within one season, so test every file — the FY2024 rule does not carry.** Ghana's FY2026 set holds all three cases at once: **MLGCRA is native throughout including its financial tables** (372,000 characters over 195 pages, table 1.5 parsing straight); **MOCD and OGM are page images end to end** (103 characters over 103 pages, 117 over 117). The FY2024 MLGRD volume was the mixed case — native narrative, screenshot tables. One ministry, one printer, three behaviours.

**⚠ And the money page is rotated.** In both image-only volumes table 1.5 is a landscape table on a portrait page, so a straight OCR returns the text mirrored (`ainpow 1e8png SIWSID` for `GIFMIS Budget Module`) and reads as garbage rather than as an error. Render, rotate 270°, and check which rotation gives readable running heads before OCRing anything.

**The reliable recipe for the money, and it is not OCR.** `pypdfium2` `.render(scale=350/72)` → `.rotate(270, expand=True)` → crop into a left half (labels + first origin block) and a right half (remaining blocks + Grand Total) → **read the two crops directly**. OCR at 300 dpi recovers the headings and most digits but drops whole cells out of a fifteen-column table; the render is legible at 350 dpi and settles every figure. OCR the volume once anyway and commit the sidecar — it is what makes the narrative greppable, and the narrative is where the bodies are named.

**A native volume is read the same way, minus the render.** `scripts/pdf-geom-rows.py --rot` reads a rotated *native* page directly (`upright: False`: group on `x0`, run cells bottom-to-top). MLGCRA's table 1.5 came back complete on the first attempt.

**⚠ The narrative names more sub-programmes than the table funds, one level down from the FY2024 finding.** MoCDTI's Programme 2 description lists **eight** sub-programmes and table 1.5 funds **five codes**: the **National Communications Authority**, **GIFEC** and **Ghana Digital Centres** have no code and no line, and on the evidence of the volume sit inside `02603001 ICT Infrastructure and Regulation` — whose internally-generated funds of GHS 494.3m is what a regulator's fee income looks like. The same volume describes a *Digital Technology (DTD)* and an *Innovations* sub-programme under Programme 1 and funds neither. **Always diff the narrative's sub-programme list against the codes in table 1.5**, exactly as archetype S already says for programmes.

**⚠ A PBB volume does not always tie to the Appropriation Act, and the difference is one programme wide.** MOCD (printed 19 Nov) and MLGCRA (17 Nov) reproduce Act 1163's MDA lines **to the cedi**; OGM (27 Nov) does not — its `00105 Investment Promotion Management` carries GHS 1,655,667 less internally-generated funds than the Act, and the whole MDA total differs by exactly that. Two of three tie, so the tie is the norm and the third is a late amendment during passage, not an extraction error — but **cross-foot each volume against the Act separately** and record which stage each figure is.

**Births and deaths registration is still unfunded, and that is now a two-year finding.** The FY2026 MLGCRA volume's programme structure names `P4. Births and Deaths Registration`, its narrative reports 432,925 births registered in 2025 and a Civil Registration and Vital Statistics strategic plan 2025–2030, and **table 1.5 carries no code for it** — the codes run 01101, 01102, 01103, 01104, then jump to 01107. Neither does Act 1163. The country's CRVS spine has no appropriation line in either instrument, two years running.

## Archetype T — Lusophone SISTAFE mapa set: organic classification only, published as one PDF per mapa, with the origin split on the investment mapa *(added 2026-08-09, Mozambique)*

*Seen as: Mozambique, `Plano Económico e Social e Orçamento do Estado para o Ano de 2026 — Mapas finais A–M` — thirteen separate PDFs, 33 MB in total, native text throughout, footed `SISTAFE`.* Not archetype R: Cabo Verde's mapas are bound into the *Boletim Oficial* with the law and carry a programme axis; **these carry no programme axis at all** — the classification is `organic unit × economic nature`, and the appropriating law is published somewhere else entirely (and, in the year read, not published at all). Expect the shape wherever a Lusophone state runs SISTAFE and posts its mapas as separate files.

**Layout.** One mapa per file. `A` equilíbrio orçamental, `B` receitas por nível, `C` despesas por nível, `D` pilares do plano quinquenal, **`E`/`F`/`G` despesas para funcionamento by organic classification and grupo de despesa (central / provincial / distrital)**, **`H`/`I`/`J` despesas para investimento by organic classification and origem do financiamento**, `K`/`L` transfers to municipalities, `M` decentralised-governance ceilings. Scale is printed on every mapa — `Unidades: 10^3 MT`. The organic code is nine characters, `52A000141`: sector, a level letter (`A` central, `B`…`L` the provinces), unit, suffix.

**Why it is worth the trouble — the origin gate is two printed columns at institution grain.** Mapa H prints `Interno | Externo | Total` for every central spending unit, so the domestic/external split runs on the *body*, not the sector. That is what makes Mozambique's digital ministry legible: `52A000141 MINISTERIO DAS COMUNICACOES E TRANSFORMACAO DIGITAL` reads **Interno 0,00 | Externo 2.637.800,00**, a whole ministry's capital budget with no domestic money in it, against a national central average of 14.8% domestic.

**Strategy.** `scripts/extractors/MOZ/moz-sistafe-mapa-extract.py`, then cross-foot.

1. Anchor every row on the organic code (`^\d{2}[A-Z]\d{6}`, `x0 < 65`).
2. Cluster the amount columns from the right edges of every amount on the page, and assign each figure to the nearest column by **right edge** — the columns are right-aligned.
3. Assign description words (`65 ≤ x0 < 200`) to the nearest code baseline.
4. Check that the eleven component columns sum to the printed `Total` **on every row**, then that the rows sum to the mapa's printed grand total and column totals.

**Traps.**

- **⚠ One logical row is rendered on three baselines about half a point apart, and a wrapped description is centred on the code's line — so its first line sits ABOVE the code and its continuation BELOW.** `pdftotext -layout` attaches money to the wrong institution, and so does plain baseline grouping at any tolerance: at tol 1.0 the rows separate but the description is orphaned, and at tol 3.0 the descriptions merge across rows. The nearest-anchor assignment is what fixes it. The investment mapas (H/I/J) are single-baseline and parse straight.
- **⚠ Verify by arithmetic, because the failure is silent.** Mozambique's Mapa E returned **231 rows with zero cross-foot failures** and reproduced its own printed grand total of 280,937,450.81 and all eleven column totals; that is what makes the binding a claim rather than a hope. A `-layout` read of the same page pairs CEDSIF's 657,832.01 with the disaster-risk institute's row.
- **⚠ The label column is two lines wide and the document itself truncates long names** — *INSTITUTO NACIONAL DE TECNOLOGIAS DE INFORMACAO E*, *CENTRO DE DESENVOLVIMENTO DE SISTEMAS DE INFORMACAO DE*. Record the truncation verbatim and give the full name in a note; never reconstruct it into the field.
- **⚠ The thousands separator changes between mapas in one set.** A–L use a full stop; **Mapa M uses a comma**. Parse per mapa.
- **⚠ The provincial units of a national body can sit under a different sector prefix from the body itself.** Mozambique's statistics institute is `26A000541` (Planificação) while its eleven provincial delegations run `27B003041`…`27L003041` (Finanças), and those delegations are **larger in aggregate than the national body**. A join on the sector prefix loses half the institution.
- **The distrital mapas (G, J) are province aggregates**, coded `04B`…`04K` with no organic unit, and support no record.
- **The mapa set does not carry its own stage.** The publisher distinguishes `mapas-finais` from `mapas-propostos` by folder and nothing else; the enacting statute may be unpublished. Take the stage from the series label and say so.

**What it yields.** `appropriated` at organic-unit grain, cross-vote, at three tiers of government, with the capital/recurrent split from the funcionamento mapas and the domestic/external split from the investment mapas. **Not** a programme axis, **not** a purpose statement for any line, and **not** the appropriating instrument.

### Vote-total-only appropriation schedule — extends archetype B *(added 2026-08-09, Namibia)*

*Seen as: Namibia, `Appropriation Act, 2026 (Act No. 1 of 2026)`, Government Gazette 8930, three pages.* Archetype B without the programme lines: a gazette schedule of `VOTE NO. | TITLE | APPROPRIATION AMOUNTS N$'000` and nothing else. **It supports no record at any grain** — every line is a ministry envelope — so a country-year holding only this yields a stated absence, not a total. Say so on the place hub and put the estimates volume on the acquisition list; do not treat the zero-record outcome as a failed extraction.

**⚠ The one trap is worth carrying: the three schedule columns are three independent PDF text streams, and a plain `pdftotext -layout` dump pairs each amount with the FOLLOWING vote.** Bind by geometry (`scripts/pdf-geom-rows.py`) and anchor the result on one known row — Namibia's vote 09 Finance = 12,877,000 — before trusting the table. The vote totals then cross-foot to the printed TOTAL exactly (29 votes, N$87,928,148 thousand, delta zero).

## Not worth extracting

Recorded so later runs don't repeat the effort:

- **Treasury cash-flow / s32-style statements** — aggregate revenue and
  expenditure only, no vote or programme detail. Support no record. The sweep
  should stop fetching them.
- **End-of-year statistical annexes at economic-nature grain** — Benin's
  *Tableaux statistiques du rapport de fin d'année*, a native XLSX carrying full-year
  prévisions / engagements / ordonnancements split personnel, biens et services,
  transferts, capital intérieur/extérieur. **Machine-readable and still supports no
  record**, because there is no ministry and no programme: it is the national envelope
  only. Worth holding for a place hub's dated statement of the year's outturn and for
  the national interior/exterior split; not worth extracting for lines.
  *(2026-07-25 — a useful reminder that "native" and "useful" are different axes.)*
- **MTEF / DPBEP volumes and their annexes** — outer-year figures are indicative
  planning, not appropriations, and fail the spec's fact 3 (driver → *Budget stage*).
  Read them for narrative and priorities; build nothing. Five of these were held for
  Benin across three years and none yielded a record.
- ~~The full estimates volume~~ — **struck 2026-07-22.** An earlier draft called it
  redundant because its sector-vote chapter duplicates the standalone extract.
  That was wrong: the duplication is beside the point, and the other 41 chapters
  are where a quarter or more of the spend turns out to live. It is a **required**
  fetch and a required scan — see *The cross-vote scan* above.

### Francophone variant — the origin gate lives in the *settlement* law *(added 2026-07-26, Côte d'Ivoire)*

*Seen as: Côte d'Ivoire, LF 2024 (521 pp, native) + Loi de Règlement 2024 rapport de présentation
(native).* Same LOLF ancestry as the Burkina volume, section (3) → programme (5) → action (7) →
nature (1–4) → activité (11-digit), AE and CP. **But the appropriation volume prints no
source-of-financing column anywhere** — unlike BFA, BWA and CAF, the origin gate is simply not on
the face of the vote.

**It is in the loi de règlement instead.** The LR's *rapport de présentation* carries, as numbered
annexes, everything the appropriation volume withholds:

- **ANNEXE-VI** — execution by **nature × programme**, five columns: `budget initial`,
  `modifications`, `budget actuel`, `exécution`, `écart`, `taux`. This is the revised stage *and*
  the outturn in one table, at programme grain, for every section.
- **ANNEXE-X** — investment **by project**, columns `budget initial`, `budget actuel`,
  `exécution`, `écart`, `taux`. **It has two blocks, and the block is the origin gate.**
  *(Structure established 2026-07-26; an intermediate note that day claimed the split was absent
  altogether — that was wrong, and was caused by looking for the source rows with too strict a
  pattern.)*
  - **`PROJETS COFINANCES` comes first** (FY2024: PDF pp. 70–80) and every project in it carries
    **`1 Trésor` / `2 Don` / `3 Emprunt` sub-rows** giving that project's split, each with its own
    budget/execution columns. This is where externally-financed lines live, so **a digital project
    appearing here fails the origin gate as `domestic-state`** — its Don/Emprunt share is
    `non-state` and belongs to the news driver; only its `1 Trésor` counterpart row is domestic.
  - **Everything after it** (FY2024: pp. 81–129) is the ordinary per-section project listing with
    **no source sub-rows, because those projects are Trésor-financed by construction.** A digital
    project found only here is `funding_source: domestic-revenue`, established rather than
    inferred.
  - **So the gate is positional: which block is the project in.** Find where the cofinancé block
    ends by the last page carrying `1 Trésor` rows.
  - **⚠ The Trésor/Don/Emprunt rows are easy to miss.** They render as `1 Trésor  92 239 503 899
    …`, i.e. a bare digit, a word, then figures — no indentation, no obvious label column. A
    pattern anchored on `SOURCE`/`FINANCEMENT` finds nothing and the annexe looks like it carries
    no split at all.
  - **FY2024 worked example:** none of the 18 named digital lines captured cross-vote sit in the
    cofinancé block, so all are Trésor. Four digital projects *are* in it and are therefore not
    domestic-state records — `90046090200 PADCI` (the World Bank Digital Acceleration Project),
    `78046000460 Intégrer le digital dans le secteur agricole` (FCFA 10,4 bn),
    `90076000005` health digital transformation, `90043500010` electricity digitisation.
- **ANNEXE-XI** — transfers to **comptes d'affectation spéciale**, by line, naming the beneficiary
  and giving `prévision` against `transferts effectués`. This is where earmarked-levy delivery is
  established.

**The practical rule: for a francophone state whose appropriation volume has no origin column, do
not record the split as unestablished until the loi de règlement has been read.** The gate is one
document downstream, not absent — and in Côte d'Ivoire it is *positional* (which ANNEXE-X block a
project sits in) rather than a column, which is why it is easy to conclude wrongly that it is
missing.

**⚠ TRAP — a 100% execution rate can be the record of a collection failure.** Côte d'Ivoire's MTND
programme 23209 (Comptes Spéciaux) reports **100,0% executed** for FY2024. ANNEXE-VI shows why: a
**−8 793 791 458 in-year modification** wrote the appropriation down from 36 470 000 000 to
27 676 208 542 *by exactly the amount the levies failed to collect*, after which spending against
the reduced figure was total. **Always read the `modifications` column before quoting a `taux
d'exécution`**, and where it is large and negative, go to ANNEXE-XI for the delivery figures. The
headline rate is arithmetically true and substantively the opposite of what it appears to say.

**⚠ The RAP is not a substitute for the LR.** Côte d'Ivoire's Rapport Annuel de Performance 2024
restates the same ministry at 56 160 957 658 where the LR gives 52 619 081 477 — because the RAP
chapter carries the Comptes Spéciaux at their *voted* level and never applies the write-down. Two
official documents, same ministry, same year, 3 541 876 181 apart. **The settlement law is the
authority; the performance report is a partial restatement.**

**What it yields.** `appropriated` at activity grain cross-vote (from the LF); `proposed` from the
PLF-stage volume where the bill batch is live — for FY2026 the bill and the enacted law agree at
every section-356 line, so `proposed_total` is populatable at no extra reading cost; `revised`
and `executed` at programme × nature grain (ANNEXE-VI, **which must be summed across its four
*nature de dépense* pages** — a section appears once per nature, not once per section);
per-project investment execution (ANNEXE-X); and earmarked-levy delivery by beneficiary
(ANNEXE-XI). It yields the origin split too, but positionally — see ANNEXE-X above.

**⚠ Use `pdftotext -table`, never `-layout`, on Ivorian volumes.** *(Added 2026-07-26.)* The
FY2024 sweep recorded that the recapitulative tables 'drift amounts by one to four rows' and
warned them off; that is a `-layout` artefact, not a property of the document. Under `-table`
the *Récapitulatif Par Section et Programme/Dotation* returns section 356 at 55 649 125 870 for
FY2024, which cross-foots exactly against its three programme rows. **The recapitulatives are
usable and are the fastest route to programme-grain appropriations.** The archetype's standing
warning about not parsing `-table` money with a regex still applies and is easy to trip: collapse
runs of three or more spaces to a delimiter and read the columns, rather than matching numbers.

### Budget-de-moyens variant — ministère × service × nature with COFOG, and a scan whose handle is the *designation* column *(added 2026-08-04, Comoros)*

*Seen as: Union des Comores, `Décret N°24-186/PR` promulgating the LF2025 (146 pp, `ANNEXE VI`) and `Décret N°26-003/PR` promulgating the LF2026 (153 pp, `CLASSIFICATION PAR MINISTERE ET ECONOMIQUE` pp.39–140 plus `tableaux des emplois` pp.142–149), both page-image scans.* Same LOFE/*budget de moyens* ancestry as archetype M's SIM_ba variant — no programme structure at all — but printed as **one continuous classification for the whole state** rather than one chapter per section. **Extend M rather than adding a letter.** Five properties differ and four of them are traps.

**Layout.** `CODE | Service | COFOG | Designation | <prior-year column> | <budget-year column>`. A ministry header row (2-digit CODE), then per service a title row (4-digit service code) followed by exactly four nature rows — `Salaire`, `Biens et service`, `Transfert`, `Investissement` — and a `Total service` row; each ministry closes with `TOTAL MINISTERE`. Full national-currency units, space-separated thousands, **no scale header anywhere**.

1. **⚠ THE PRIOR-YEAR COLUMN IS THE *REVISED* STAGE, AND ITS OWN CAPTION CAN SAY OTHERWISE.** The Comorian FY2026 volume is headed `LFR 2025 | LFA 2026` while one `Article 11` caption above the same table reads `Ecart ( LFA2026-LFA2025)`. **The header is right and the caption is wrong**, and the test is arithmetic, not typography: the comparator read 223 337 645 against an `LFA 2025` known from three other instruments to be 235 315 816, the printed écart cross-foots against the comparator as printed, and the service rows sum to the comparator exactly. **So a rectificative that was adopted and never published is recoverable, at full service grain, from the next year's law** — the general move already recorded for CAR's `Collectif` column and Botswana's `Authorised` column, here delivering a stage the state itself never printed. Always check *which* stage the column is rather than trusting its caption.
2. **⚠ AN EMBEDDED TEXT LAYER CAN BE BOTH CORRUPT AND MIS-PAGINATED, AND THE SECOND FAILURE IS THE DANGEROUS ONE.** The Comorian FY2026 volume returns ~192 000 characters to `pdfplumber` with no OCR step, so every "is this native?" test passes. The digits are corrupted (`62 791 " Oao` for `62 791 000 000`) — and, worse, **the layer's page N is not the image's page N**: its "page 78" carries services that the image of PDF p.78 does not, while pp.87–88 match exactly. It behaves like the text of an earlier draft with different page breaks. **Consequence: an embedded layer may not be used even as a corroborating read, because you cannot tell which page you are corroborating.** Render the page (`pypdfium2` `.render(scale=dpi/72)`) and read the image; use the embedded layer only to *locate* a service by name, never to take a figure. Test for it with `len(page.images)==1` over a full-page bbox plus a generic font.
3. **⚠ TESSERACT LOSES THIS TABLE AT EVERY SETTING, AND THE ARITHMETIC IS WHAT SAVES IT.** `--psm 3`, `--psm 6`, 400–600 dpi and a digits whitelist all returned unusable grids on the boxed classification pages — and, on one service, a *plausible and wrong* pair (`6 028 000 / 5 000 000` where the page prints `6 128 000 / 3 000 000`, which does not cross-foot to the printed `Total service`). **The four nature rows summing to `Total service`, and the service totals summing to `TOTAL MINISTERE`, and that summing to the law's `Article 11` line, is a three-deep self-check that catches every misread.** Where a cell is obscured (stamp, fold), derive it by subtraction from the ministry total and say so on the record — but never derive two cells from one equation.
4. **⚠ THE CROSS-VOTE SCAN'S HANDLE IS THE `Designation` COLUMN, NOT THE AMOUNTS.** In a *budget de moyens* the economic natures are four generic buckets, so no keyword reaches an IT purchase and a keyword scan returns a clean-looking negative. **Three Comorian sweeps concluded cross-vote digital spend was structurally unfindable; it was findable, and it was the second-largest digital line in the country** — `08 0825 Direction Générale de Système d'Information et de Communication` inside the finance ministry, 277 128 000 KMF against the digital ministry's whole 338 724 932. **Read the service *names*, ministry by ministry, once.** The service that runs the state's financial information systems, the civil-registry directorate and the statistics institute are all named for their function and are all invisible to a term search. Expect the body to be **renamed between years on a stable code** (`0825` was *Direction Générale de l'informatique* the year before) — join on the code.
5. **Template directorates appear government-wide in a single year and are not programme lines.** The Comorian FY2026 volume adds *affaires financières*, *ressources humaines*, *programmation et communication* and *affaires juridiques* to every ministry at a flat 1 400 000 KMF of goods and services, zero salary and zero established posts, following a decree on the general organisation of administrative structures. A cross-vote extraction that reads them as substantive lines invents spend in twenty ministries.

**Two companion instruments worth the fetch.** The ***lettre de cadrage budgétaire*** annexes the **economic nomenclature** — the chart of accounts, where the IT-specific codes live (`2432 Matériels informatiques`, `6021 Fournitures de bureau et matériel informatique`, `6122 Entretiens des matériels informatiques…`). And the ***recueil des arrêtés***, a scanned annual compilation of ministerial orders, carries **virement arrêtés at nature × service grain with their own cross-footing tables** — that is where a fourth IT code surfaced (`6153 Site Web et Consommation Internet`) together with a dated in-year movement the finance laws do not publish. **In a means-based budget, read the framing letter's annexes and the year's arrêté compilation before concluding the state cannot resolve IT spend.**

**What it yields.** `appropriated` at service × nature grain, cross-vote, with COFOG; `revised` for the preceding year from the comparator column; the capital/recurrent split on every line; and, from the *recueil*, in-year `revised` movements at economic-nature grain. **Not** a domestic/external origin split — that is in the law's `Article 7` capital table (`ÉTAT | BAILLEURS`), at ministry grain only.
