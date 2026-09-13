"""Write companion pages for the BWA FY2025/26 domestic-finance sweep (batch job 18)."""
import os

D = 'new-budget/BWA/2025/'
FM = """---
type: source
title: "{title}"
url: {url}
publisher: {pub}
published: {pubdate}
date_precision: {prec}
date_source: {dsrc}
places: [BWA]
topics: [{topics}]
entities: [{ents}]
lens: []
retrieved: 2026-07-25
sweep_batch: domestic-finance-BWA-2025-2026-07-25
fiscal_years_covered: [{fyc}]
doc_type: {dt}
source_tier: budget-document
artefact: {art}
body_completeness: excerpt
---

"""
MOF = '[[ministry-of-finance-botswana]]'
MCI = '[[ministry-of-communications-and-innovation-botswana]]'

docs = [
("2025-03-31-bwa-appropriation-2025-26-act-2025", dict(
 title="Appropriation (2025/2026) Act, 2025",
 url="https://www.finance.gov.bw/images/2025-26/Appropriation2025_2026Act.pdf",
 pub="Parliament of Botswana", pubdate="2025-03-31", prec="day", dsrc="source",
 topics="finance.budget, gov.legislate", ents=MOF, fyc='"2025/26"', dt="appropriation-act"),
"""The enacted appropriation for the year ending 31 March 2026. **Native text this year** --
3,541 characters over 2 pages, against the FY2024/25 Act's 3 characters. The image-only
problem that made the FY2024/25 instrument unusable did not recur.

`Date of Assent: 31.03.2025`, `Date of Commencement: 01.04.2025`, `No. 8 of 2025`, passed by
the National Assembly on **25 March 2025** -- all read from the document, not inferred.

Consolidated Fund **P89,571,721,181**; Development Fund **P23,749,171,200**. Both reconcile
exactly to the estimates volume's SUBTOTALS line.

**The Schedule reconciles organisation by organisation to the estimates volume**, including
`2400 Ministry of Communications and Innovation = P966,373,090`. That equality is what lets
the volume stand in for the Act, and it is now verified for this year rather than assumed.

**EXTRACTION TRAP -- the Schedule is offset under `pdftotext -layout`.** Organisation `0400`
prints no amount inline, so from that row on the label and figure columns are out of step by
one and `2400` appears to carry P62,493,310 (which is in fact Industrial Court's). Decode by
taking the amount column as an ordered sequence against the organisation list, and cross-foot
to the printed TOTAL. An independent copy on CABRI
(`cabri-sbo.org/uploads/bia/Botswana_2025_Approval_External_EnactedBudget_Institution_SADC_English_43561a.pdf`)
prints the Schedule as clean prose and was used to confirm the decode.

**Organisations abolished for FY2025/26:** `2500 Ministry of Defence and Security` (absorbed
into `0200`), `3000 Ministry of Entrepreneurship` (into `0700`), and `0223 Counter Terrorism
Analysis and Fusion Agency`. New: `3300 Ministry of Higher Education`, `3400 Ministry of
Sports and Arts`. **No organisation for the Information and Data Protection Commission.**"""),

("2025-02-11-bwa-peoples-summary-2025-26-budget", dict(
 title="People's Summary of the 2025/2026 Budget",
 url="https://www.finance.gov.bw/images/2025-26/Peoples_Summary_of_The_2025-2026_Budget_11_Feb_2025.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2025-02-11", prec="day", dsrc="source",
 topics="finance.budget, dt.strategy", ents=MOF, fyc='"2024/25"; "2025/26"', dt="budget-estimates"),
"""The citizen's budget, and -- as in FY2024/25 -- **the only document that says in plain words
what the digital money is meant to buy.** The estimates volume names no systems at all, so
this is the `scope_basis` for the year.

Para 28, *Innovation and Digital Transformation*: **a development budget of P1.47 billion**,
to fast-track the national digital transformation strategy (**SmartBots**); the **Village
Connectivity Programme phases 2, 3 and 4** connecting **over 1,000 public facilities** by
2025/2026; **over 500 schools** connected through the **Botswana Research and Education
Network (BotsREN)**; and the **Digital Competency Framework (DCF)**.

**The P1.47 billion is a cross-ministry thematic line, not a vote.** It is again larger than
the digital ministry's entire development appropriation (P853,907,763) because it spans
ministries. It has no organisation and no project code and **must not be recorded as a
ministry or programme figure** -- the same trap flagged for FY2024/25's P1.83 billion. The
series is **P2.62bn (FY2023/24) -> P1.83bn (FY2024/25) -> P1.47bn (FY2025/26)**.

Table 1 gives the full ministerial split; those are envelopes, not records.

Block 4b material: BURS is named as introducing **VAT on digital trade**, an **Electronic VAT
Invoicing Solution** and a **track & trace** fiscal marking system, plus the **One Stop Border
Post** at Mamuno/Trans-Kalahari. None of these appear as a line in the estimates volume."""),

("2025-02-09-bwa-key-features-2025-26-budget", dict(
 title="Key Features of the 2025/2026 Budget",
 url="https://www.finance.gov.bw/images/2025-26/key_features-new_compressed.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2025-02-09", prec="day", dsrc="inferred",
 topics="finance.budget", ents=MOF, fyc='"2025/26"', dt="budget-estimates"),
"""The budget-day slide deck. **Native this year** (15,051 characters over 30 pages) against
the FY2024/25 edition's 32 characters -- the second of the two FY2024/25 image-only documents
to come back readable.

Aggregate frame: Recurrent **BWP 65.95bn**, Development **BWP 23.75bn**, Statutory
**BWP 22.70bn**. Carries the four national priorities with their development budgets, of which
*Innovation and Digital Transformation* is **P1.47 billion**, and a per-ministry allocation
page (MCI: Recurrent BWP 966.37m / Development BWP 853.91m -- envelopes).

Also sets out the budget calendar (April year start; June-July technical hearings; September
MDA bids; October budget/project review; November Estimates Committee; December Cabinet;
February budget speech; March parliamentary approval) -- useful for dating the stages.

Duplicates its native siblings (People's Summary, Budget-in-Brief) on substance. **Low
extraction priority.**"""),

("2025-03-04-bwa-mof-committee-of-supply-speech-2025-26", dict(
 title="Committee of Supply Speech for Organisation 0300 for both Recurrent and Development Expenditure Estimates 2025/2026",
 url="https://www.gov.bw/sites/default/files/2025-03/Ministry%20of%20Finace%20Committee%20of%20Supply%20Speech%20%2004.03.2025%20final__0.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2025-03-04", prec="day", dsrc="source",
 topics="finance.budget, dpi.exchange", ents=MOF, fyc='"2024/25"; "2025/26"', dt="budget-estimates"),
"""The finance ministry's own defence of its FY2025/26 estimates, at **programme grain** -- the
grain the volume does not print for the recurrent side and prints only as a project code for
the development side.

**Independently corroborates the cross-vote scan.** Para 52(i): *MOF ICT Development* at
**P84,571,040** -- exactly the figure read from the estimates volume's development-by-project
table for `0301 Headquarters (MoF), project 11061 MoF Computerisation`. Two documents, two
extraction routes, same number.

Development budget requested **P864,487,720** (down 5.4% on FY2024/25's P913,853,592), split:
MOF ICT Development P84,571,040; Statistical Surveys and Studies P125,286,680; Consultancies
P11,500,000; Infrastructure P143,130,000; **State Owned Enterprises Financing P500,000,000**.
Recurrent requested **P3,055,755,260** -- matching the Act.

Block 4c/6: names the subventions inside the MoF recurrent vote, including **Statistics
Botswana P116,549,760** and the **Public Procurement Regulatory Authority P67,548,690** -- two
bodies with no organisation of their own, whose funding is otherwise invisible.

Block 4b / `dpi.exchange`: the **interoperable National Retail Payment System (NRPS)** led by
the Bank of Botswana, overseen by a task force including the Ministry of Communications and
Innovation and BotswanaPost. No budget line is attached to it here."""),

("2026-02-02-bwa-budget-speech-2026-27", dict(
 title="2026 Budget Speech, delivered to the National Assembly on 09 February 2026",
 url="https://www.finance.gov.bw/images/Budget-Tables/2026_2027_Budget_Speech.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2026-02-09", prec="day", dsrc="source",
 topics="finance.budget", ents=MOF, fyc='"2024/25"; "2025/26"; "2026/27"', dt="budget-estimates"),
"""Gaolathe's second budget. **Staged for section VIII, *2025/2026 Financial Year Revised
Budget Estimates*** -- the state's own account of the run year's revision.

Para 125: deficit for FY2025/26 estimated at **P25.48 billion**; total revenue and grants
revised down to **P71.22bn** from P75.49bn (mineral revenue P15.75bn -> P12.06bn; SACU up
P631.1m to P24.99bn; VAT up P1.62bn to P13.71bn; non-mineral income tax down P2.69bn to
P16.32bn); total expenditure and net lending revised down to **P96.70bn** from P97.61bn.
**"Recurrent expenditure estimates are maintained at their original budget levels, while
development expenditure estimates have been revised downward by P903.32 million to P22.85
billion."**

**That sentence is the key to the whole country-year.** It confirms from the state's own mouth
that (a) the FY2025/26 recurrent budget was *not* revised -- so appropriated = revised for every
recurrent line, which is why the FY2026/27 volume's `Authorised Expenditure 2025-26` column
reproduces the FY2025/26 volume's `Estimate 2025-26` exactly; and (b) the whole-of-government
development revision is **P903,320,512**, against which the digital ministry's own
P319,012,857 is **35.3%** and digital lines together are **65.3%**.

Para 16 closes a standing FY2024/25 question: **"over the last two financial years, 2024/25 and
2025/2026, no supplementary budget requests have been approved."** So the Supplementary
Appropriation instrument that the FY2023/24 cadence implied for FY2024/25 will not exist -- a
stated policy break, not a publication gap.

**The published date is taken from the 09 February 2026 delivery date printed on the cover**,
not from the undated `Budget-Tables` URL directory. The file is also mirrored at
`gov.bw/sites/default/files/2026-02/` and `bankofbotswana.bw`."""),

("2026-02-02-bwa-budget-in-brief-2026-27", dict(
 title="Budget-in-Brief 2026/2027",
 url="https://www.finance.gov.bw/images/Budget-Tables/2026-2027_Budget_In_Brief.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2026-02-09", prec="day", dsrc="inferred",
 topics="finance.budget", ents=MOF, fyc='"2024/25"; "2025/26"; "2026/27"', dt="budget-estimates"),
"""Carries the medium-term fiscal series across the run year. Staged because the FY2025/26
Budget-in-Brief **was never published** -- the ministry's own library page prints
*"(will be uploaded shortly)"* against it -- so this is the nearest equivalent and supplies the
FY2025/26 revised aggregates in the citizen-budget format.

Envelope caution applies to its ministerial tables: they are not records."""),

("2026-02-02-bwa-peoples-summary-2026-27-budget", dict(
 title="People's Summary of the 2026/2027 Budget",
 url="https://www.finance.gov.bw/images/Budget-Tables/PEOPLE%20SUMMARY.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2026-02-09", prec="day", dsrc="inferred",
 topics="finance.budget, dt.strategy", ents=MOF, fyc='"2025/26"; "2026/27"', dt="budget-estimates"),
"""The FY2026/27 citizen's budget, staged as the successor to the document that supplied
FY2025/26's `scope_basis`, and for its FY2025/26 comparators.

**Low text density -- 7,681 characters over 20 pages** (384 per page). It is a designed,
graphic-heavy deck; the text layer is present but thin, and figures sitting inside graphics may
not extract. **Verify any figure against the Budget-in-Brief or the speech before use.**"""),

("2026-02-26-bwa-mof-committee-of-supply-speech-2026-27", dict(
 title="Committee of Supply Speech for Organisation 0300 for Recurrent and Development Estimates 2026/2027",
 url="https://www.botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/Ministry%20of%20FInance%20Committee%20of%20Supply%20Speech%2026-02-2026%20-%20Final.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2026-02-26", prec="day", dsrc="source",
 topics="finance.budget", ents=MOF, fyc='"2025/26"; "2026/27"', dt="budget-estimates"),
"""The finance ministry's FY2026/27 supply speech, staged for its **FY2025/26 revised figures**.

Para 71: the FY2025/26 **revised** MoF budget was **P3,720,242,980** against the approved
P3,920,242,980 -- a **P200 million** in-year reduction. Para 77: the FY2025/26 development
budget is given as **P664,487,720** against the P864,487,720 approved in March 2025, so the
whole P200m came off the development side, and the *State Owned Enterprises Financing* line is
the only candidate large enough to carry it.

Para 78(iv): **MOF ICT Development rises to P123,172,400 for FY2026/27** from P84,571,040 --
matching the FY2026/27 volume's project `12041` line exactly.

Note the FY2025/26 recurrent is described as "Warranted provision ... P3,055,755,260",
i.e. unchanged -- consistent with the budget speech's statement that recurrent estimates were
maintained at original levels."""),

("2026-03-16-bwa-mci-committee-of-supply-speech-2026-27", dict(
 title="Organisation: 2400 -- 2026/2027 Recurrent and Development Budget Proposals Presented to the Committee of Supply",
 url="https://www.botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/2026%20MCI%20COMMITTEE%20OF%20SUPPLY%20-%20%2016%2003%202026%20REVISED%20FINAL%20(%20Hon%20Minister)%201.pdf",
 pub="Ministry of Communications and Innovation (Botswana)", pubdate="2026-03-17", prec="day", dsrc="source",
 topics="finance.budget, dt.egov, infra.broadband", ents=MCI, fyc='"2025/26"; "2026/27"', dt="budget-estimates"),
"""**The single most valuable document of this country-year, and the answer to FY2024/25's
"the estimates name no systems at all".** They are named here. Minister David Tshere, cover
date **17 March 2026** (the filename says 16 03 2026 -- the cover date is used).

**Section III, *2025/2026 Financial Year Budget Utilisation*, is the only execution reporting
Botswana produces for the run year.**

- **Para 53 -- recurrent:** allocated **P966,373,090** for the ministry and its **20
  parastatals**; **P661,769,517 or 68% expended as at 31 December 2025**. Highest: Headquarters
  **85%** (SOE subventions to BDIH, BITRI and BotswanaPost; office rental; postal charges;
  computer system consumables; office equipment) and Radiation Protection Inspectorate **80%**.
  Para 54: balance P304,603,573 or 32%. **661,769,517 + 304,603,573 = 966,373,090 exactly.**
- **Para 56 -- development:** **P853,907,763 approved by the Committee in March 2025**, then
  **reduced by P319,012,857 or 37% to P534,894,906 in AUGUST 2025**; **P294,278,725 or 55%
  expended as at 12 March 2026**. Every one of those figures matches the estimates volumes
  independently, and the speech supplies what the volumes cannot: **the revision happened in
  August 2025**, five months into the year.
- **Para 57 -- spend by project, FY2025/26:** Government Data Network Expansion III
  **P74,034,562**; National Backbone Network **P34,365,298**; Government Online (e-Services)
  **P32,992,324**.

**ARITHMETIC INCONSISTENCY IN THE SOURCE -- do not build on it.** Para 57's "remaining balance
of P324,037,239" reconciles to neither the revised budget (534,894,906 - 294,278,725 =
240,616,181) nor the approved (559,629,038). Recorded as printed; the executed figure
P294,278,725 is the usable one because it is stated twice, in Pula and as a percentage.

**Named systems and programmes (the `scope_basis` the volume withholds):**

- **1Gov-1Citizen platform** -- accessible e-Services raised **from 33 to 52** during the year.
- **194 public-facing e-Services developed last year were WITHHELD** because of technical
  problems with the **Government Accounting and Budgeting System (GABS)**; the redesigned
  payment platform is under procurement, to enable direct revenue collection to the Bank of
  Botswana. This continues the GABS failure the wiki already holds from March 2025.
- **Delta Digital Data Centre (DDDC)** -- Tier III, owned and operated by **BoFiNet**;
  migration of government systems **commenced November 2025**, financed by **P100 million from
  the Universal Service and Access Fund** -- own-source levy money, not appropriation. A second
  accredited data centre outside Gaborone is intended.
- **Local Access Network** -- Ramotswa, Taung and Moshupa completed end January 2026, Thamaga
  due end April 2026; 136 jobs; 207 government/business premises added; **13,456 essential
  facilities connected cumulatively**.
- **Research Fund** -- "over P200 million" approved for FY2025/26, **revised to P50 million**,
  of which **P9,583,636.25 spent**; 45 projects approved in 2024 continued, no new projects.
- Revenue: estimated P1,870,310, collected P711,479 at 25 February 2026, the shortfall blamed
  on the breakdown of the sole Dosimetry Evaluation System at the National Dosimetry Laboratory.

**FY2026/27 proposals (out of run FY, but the first priced cyber line in this corpus):**
ICT programme **P251,000,000** -- Government Data Network Expansion III P75,000,000; Government
Online Services (e-Services) P70,000,000; National Backbone Network P65,000,000; **Cyber
Security project P13,000,000**; International Connectivity P10,000,000. Radioactive detection
P8,500,000 (Orphan Radioactive Storage Facility, Palapye P8,000,000; Border Detection System,
Pioneer Border Gate P500,000).

Recurrent FY2026/27 P949,920,900: Department of Information Technology **P587,310,850 (62%)**
-- of which Postal Charges P142,577,380, Computer Systems Consumables P76,940,620, Application
System Administration P31,584,550, office equipment P47,580,570 -- and Headquarters
P300,001,130 (32%), of which P187,599,700 is SOE subventions."""),

("2026-01-01-bwa-budget-strategy-paper-2026-27", dict(
 title="2026-27 Budget Strategy Paper (Draft)",
 url="https://www.finance.gov.bw/images/Budget-Strategy-Papers/2026-27_Budget_Strategy_Paper_-_Draft.pdf",
 pub="Ministry of Finance (Botswana)", pubdate="2026-01-01", prec="month", dsrc="inferred",
 topics="finance.budget", ents=MOF, fyc='"2025/26"; "2026/27"', dt="mtef"),
"""The pre-budget statement for FY2026/27, published **January 2026 -- inside the run fiscal
year** -- and therefore an in-year fiscal document for FY2025/26 as well as the requested stage
for the year after.

**It is not on the Budget Documents library page.** Budget Strategy Papers live in a *separate*
Joomla category, `id=26`, which the FY2024/25 run did not enumerate; category 23 lists the title
without a link. Category 26 also holds a *People's Summary of the 2025-2026 Budget Strategy
Paper* not previously held.

Its date is inferred to January 2026 from Econsult's citation ("the Budget Strategy Paper
released in January 2026") and from the December-publication cadence of the two prior editions;
**read the printed date at extraction and correct.**

Treat with the FY2024/25 caution: a BSP's projections are **not** a proxy for the appropriation
-- the FY2024/25 edition missed the eventual proposal by 15%. Use it for narrative and for
first-half FY2025/26 outturn, not as a stage."""),

("2026-05-01-bwa-forensic-audit-summary-report-2026", dict(
 title="Forensic Audit Summary Report 2026",
 url="https://www.gov.bw/sites/default/files/2026-05/Forensic%20Audit%20Summary%20Report%202026.pdf",
 pub="Government of Botswana", pubdate="2026-05-01", prec="month", dsrc="inferred",
 topics="finance.budget, gov.oversight", ents=MOF, fyc='"2024/25"; "2025/26"', dt="audited-accounts"),
"""A Presidential-directive forensic audit programme: **phase 1 risk assessment across 92 public
sector entities, phase 2 thirty forensic audits conducted between June 2025 and March 2026**,
focused principally on April 2014 - March 2024 with later matters considered where relevant.

**NOT the Auditor-General's annual certification.** It does not supply the audited stage for any
fiscal year and must not be read as one. `doc_type: audited-accounts` is the nearest value in
the canonical vocabulary; the distinction is stated here so extraction does not mistake it.

Staged because the audits ran *through* FY2025/26 and the entity list is the only published map
of where the state itself thinks its financial-control risk sits -- including bodies that run
large systems. Date inferred from the URL directory (`2026-05`); read the printed date at
extraction."""),
]

for stem, meta, body in docs:
    art = stem + '.pdf'
    assert os.path.exists(D + art), art
    meta['art'] = art
    with open(D + stem + '-companion.md', 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(FM.format(**meta) + body.rstrip() + '\n')
    print('wrote', stem + '-companion.md')
