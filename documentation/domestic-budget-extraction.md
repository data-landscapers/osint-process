# Domestic budget extraction — accumulated method notes

Working notes on **how to find the digital lines** in state budget documents, by
country and document type. Appended to on every domestic finance run, including
the failures — an approach that didn't work is worth as much as one that did.

*(Curator ruling, 2026-07-22: isolating domestic digital spend is a challenge for
all evidence and won't be solved by a rule. It is learned, and the learning has to
be written down somewhere it compounds. This is that file.)*

Not a source and not a wiki page: it is procedure, read by
`wiki/finance-load-domestic-state.md` at the start of a run.

## How to use it

Before capturing a country, read its section. After capturing, append what you
learned: what the digital lines were actually called, which classification codes
carried them, where they hid, what you looked for and didn't find.

## Per-country notes

### Angola — press reporting of despachos and procurement plans (back-swing, 2026-07-22)
- **Digital lines found under:** presidential despachos reported by Novo Jornal/Angop — grep "aprovou a despesa" / "autorizou a despesa" / "manda abrir crédito adicional suplementar no OGE" / "inscrito no Programa de Investimento Público (PIP) do OGE" + a numbered "Despacho Presidencial n.º XX/YY". Richest domestic-state seam in the whole corpus (4 of 23 records).
- **Where they hid:** appropriations surface at the vendor-contract-signing or despacho-report event, never at budget enactment; the despacho's own date and the revenue source are routinely unstated.
- **Language:** amounts often stated in USD or EUR directly, even for OGE-funded lines — record as announced. The mandatory per-ministry PAC (procurement plan, Lei 41/20) on the Portal de Compras Públicas is a recurring annual source worth sweeping.
- **Scale trap:** Novo Jornal's "bilião/biliões" is unreliable — verify 10⁹ vs 10⁶ against an internal equivalence (e.g. a known co-financing figure) before storing; its own USD conversions can be garbled.

### Burkina Faso — executive accountability events (back-swing, 2026-07-22)
- **Digital lines found under:** the PM's report to the Transitional Legislative Assembly (March), inauguration ceremonies via the state daily Sidwaya ("a coûté X milliards F CFA", "financés à hauteur de"), and ministry project launches.
- **Where they hid:** figures attach to works (data centres, RESINA restoration, zones blanches), never to votes; FY and stage are never stated → `budget_stage: unclear` is the norm.
- **Blending:** universal-service spend blends FASU (own-source levy) with World Bank PACTDIGITAL money, parts never separable — record whole, flag the overlap against the held WB deal.
- **False positive:** the ministry's CASEM-approved Annual Work Plan budget (late Dec) is headlined as a "digital projects budget" but is the full ministry envelope including postal activities.

### Senegal — DGB document library behind a transport wall (sweep, 2026-07-23)
- **budget.sec.gouv.sn is the model Track-B target**: one listing page enumerates LFI/LFR/PLF/annexes for every year as UUID download links (`/documents/public_download/<uuid>/telechargement`). But **TLS fails from this network even IP-pinned** — Exa crawls it; curl cannot. Verified UUIDs go to acquisitions for a browser session.
- **Mirrors that ARE reachable:** vie-publique.sn (dashboards + document pages per year) and archives.sn/docs/budget. Their per-year indexes are the entry point when DGB is walled.
- **RTEB (rapport trimestriel d'exécution budgétaire)** is Senegal's execution series — quarterly, actuals vs LFR. Q4-2024: dépenses 6,506.16 mds (103.7%), >500 mds arrears folded in.
- **The MCTN envelope splits into three sectors** (Communication / Économie Numérique / Postal) and the split surfaces in Assembly finance-committee reporting each December — the digital slice is recordable per the SEN slice rule; the per-programme annexe converts it to lines.
- **Trap: finances.ml is Mali.** Its RTEB format is near-identical to Senegal's and surfaces in Senegal-phrased searches.

### Kenya — budget-speech sub-programme reporting (back-swing, 2026-07-22)
- **Digital lines found under:** State-Department sub-programme names ("population management services", "migration and citizen services") in tech-press coverage at budget-speech time (June), with source-stated USD conversions.
- **Didn't work:** the reporting never states tabled-vs-enacted → stage lands `unclear`.

### Kenya — Treasury document chain, FY2024/25 (sweep, 2026-07-23)
- **treasury.go.ke is mid-migration (WordPress → Drupal 10) and its own links rot:** live files sit under `/sites/default/files/Budget Books/…`; anything under `/wp-content/uploads/…` or listed only on `/index.php/budget-books` may serve a Drupal 404 soft-page (~50KB HTML, HTTP 200). **Check `head -c 8` for `%PDF` on every fetch** — three of twelve fetches this run were soft-404s (Dev Vol I original, Supp II PBB × two hosts).
- **The budget-books page enumerates cleanly** — one fetch of `/budget-books` yields the whole per-FY directory tree (estimates, supplementaries I–III, per-volume). Vol ranges: Recurrent 1011–1162/1166–2151; Development I 1011–1083 (Interior/Immigration = identity), II 1091, III 1092–2141 (ICT votes 1122/1123).
- **cob.go.ke and oagkenya.go.ke did not resolve from this network** (treasury.go.ke and ca.go.ke fine). Workaround that worked: **Parliament's DSpace library (libraryir.parliament.go.ke) mirrors COB and OAG reports** — item page → `/bitstreams/<uuid>/download`. The COB annual BIRR FY2024/25 (102MB) came through it; the OAG Blue Book FY2024/25 (630MB) is there too.
- **The COB BIRR is the prize:** Art. 228(6) four-monthly implementation reports + annual, with exchequer issues, absorption by MDA and Article-223 spending — released *and* actual stages from one document. Scanned+OCR, noisy but extractable.
- **FY2024/25 had four budget values** (Finance Bill withdrawal): 4.49tn → 4.37tn (Supp I, Aug 2024) → 4.64tn (Supp II) → 4.37tn (Supp III). June-2024 budget-speech reporting (the back-swing's Kenya seam) is all **proposed**-stage; anything citing it needs a stage label and a Supp-I check.
- **SHA Sh104.9bn health-IT system: not an appropriation.** Fully outsourced 10-year user-fee contract (Ndii on the record), unbudgeted and outside the MTEF per the FY2023/24 audit; only the Sh7.02bn installation/training slice is fisc-side. The origin/instrument gates must catch this or the dataset gains a phantom Sh105bn line.
- **FY2026/27 restructured Vote 1122** — programme codes are NOT stable across years: 0210020 renamed (BPO/Konza transfers gone), 0217000 split into four function-named sub-programmes, new 0222000 ICT Security & Data Protection Services (incl. the first visible data-protection line, 917.27m). Series built on programme codes need a mapping row at every restructure.
- **The PBB baseline column carries the prior year's latest revised at print time** — FY2026/27 baselines equal FY2025/26 Supp I exactly, which is how a missing or ambiguous supplementary's values get recovered or corroborated a year later.
- **Statement + Mwananchi live under `/Latest updates/` and `/Budget summary/` for the newest year**, then migrate or die - fetch them in the budget-day-adjacent sweep, not later.
- **Searched, found nothing:** an ODPC budget line in reporting (expect it inside the ICT vote in the PBB — single-mandate carve-out applies); a per-programme eCitizen appropriation (eCitizen is revenue-side, KSh 50 convenience fee).
- **COB and OAG hosts fail only on local DNS** — resolve via DoH (`cloudflare-dns.com/dns-query`) and pin with `curl --resolve host:443:IP`. cob.go.ke = 41.80.37.59 (2026-07-23).
- **COB's JS download-manager is defeatable without a browser:** fetch `/download/<slug>/` (slugs are in the static HTML of `cob.go.ke/publications/national-reports/` and `/reports/national-government-budget-implementation-review-reports/`), read the `?wpdmdl=<id>` from the returned package page, then fetch `/download/<slug>/?wpdmdl=<id>` — serves the PDF directly. In-year BIRRs (3/6/9-month) acquired this way for FY2025/26; both are **native PDFs**, unlike the scanned annual.
- **KIPPRA's repository mirrors Treasury documents behind a DSpace 7 API**: `/server/api/core/items/<uuid>/bundles` → ORIGINAL bundle → `/server/api/core/bitstreams/<uuid>/content`. Used for the FY2025/26 Budget Statement after Treasury's own wp-content copy 404'd.
- **FY2025/26 shape:** only two supplementaries (Supp I April 2026, Supp II June 2026); annual BIRR and audit not yet published as of 2026-07-23 — the re-run next year picks them up.

### Côte d'Ivoire / Benin / Gabon — francophone budget-session reporting (back-swing, 2026-07-22)
- **Pattern:** Oct–Dec committee/assembly-stage reporting (WeAreTech, TechAfrica, Ecofin) gives the digital ministry's total vote with YoY comparator — an envelope, excluded by rule. Only occasionally (Benin: "programme numérique et digitalisation", XOF 12.3bn) does reporting give the programme split that yields a recordable line.
- **The acquirable unit** that would convert envelopes into lines: the loi de finances annexes / the CIV "Lettres d'engagement" issued per budget programme.

### Botswana — development-plan documents (back-swing, 2026-07-22)
- **Digital lines found under:** NDP 12 / PIP coverage — the clean line hides inside a mixed ministry ask, called out as "ICT development projects" with named systems (national payment switch, accounting system); named systems are the scope_basis.

### Egypt — recipient-side accounts (back-swing, 2026-07-22)
- **New pattern:** central-bank incentive schemes (CBE PoS campaign) surface only as income lines in the recipient company's filings (Fawry), quoted in fintech profiles — the state's own cost is never published. Capture from the recipient side, flag the judgment.

### World Bank PADs — the counterpart sliver (back-swing, 2026-07-22)
- **Where it hides:** the PROJECT FINANCING DATA block, "Counterpart Funding / National Government" rows plus a footnote naming which country carries which share; the component-cost table includes it while the IDA Resources table excludes it — a small mismatch between the two tables (60.00 vs 60.50) is the tell.

### South Africa — Treasury document chain, FY2024/25 (sweep, 2026-07-22)

- **Fiscal year:** April–March; "2024" = FY2024/25 (2024-04-01 → 2025-03-31); document label `2024/25`.
- **Document chain confirmed and mostly fetchable by direct URL** (Track B beats search here):
  ENE per-vote chapters at `treasury.gov.za/documents/national budget/{yyyy}/ene/Vote NN Name.pdf`
  (Budget Day, late Feb); AENE per-vote at `/documents/mtbps/{yyyy}/aene/Vote NN Name.pdf` (MTBPS day,
  late Oct); bills at `/legislation/bills/{yyyy}/[BN-yyyy] Name.pdf` — **exact filename matters**
  (B14's real name is `[B14-2024] (Adjustments Appropriation).pdf`; the obvious guess soft-404s);
  monthly s32 statements at `/comm_media/press/monthly/{yymm}/press.pdf` where **{yymm} is the
  publication month, one–two months after the reporting month** (2505 = as at 31 March 2025).
- **Soft-404 trap:** treasury.gov.za serves HTTP-200 HTML for wrong paths — check content-type,
  never trust the status code. Home Affairs' ENE chapter name resisted guessing; use the FullENE
  volume instead of probing.
- **The digital vote is Vote 30 (DCDT)** in 2024: 6 programmes; the recordable lines are programme-level
  (SA Connect under *ICT Infrastructure Development and Support*, R1,922.7m FY2024/25; entity transfers
  under *ICT Enterprise and Public Entity Oversight*, R1,596.9m). Cross-vote digital spend (Home Affairs
  digital ID, SITA via departments, SARS modernisation) needs the FullENE volume.
- **Scale flips between documents in the same chain:** ENE chapter summary in **R million**, AENE in
  **R thousand** — the 1,000× trap sits between the appropriation and its revision.
- **Stage coverage available:** proposed (B5 bill + ENE), revised (AENE + B14: FY2024/25 total unchanged
  at R3,968,611k, virement R2.789m CP→transfers), actual-aggregate (year-end s32; per-vote actuals NOT
  in the 3-page press statement), revised-per-vote (May-2025 Budget statistical annexure, Table 4).
  **Audited/outturn per vote sits in the DCDT Annual Report (Phoca-gated) and AGSA PFMA GR
  (bot-guarded) — both in acquisitions.** AGSA's GR has a dedicated government-ICT-function section.
- **Budget-vote speeches (July, post-GNU-formation in 2024) state programme allocations** the press
  never carries: Malatsi 2024-07-15 gives SA Connect Ph1+2 = **R1.858bn FY2024/25** — the figure that
  should case-5-test the held `zaf-2025-26-dcdt-sa-connect-phase-2` record (>R3bn, stage unclear,
  FY ambiguous): the two may be different FYs of the same programme, to settle at extraction.
- **Didn't work:** AGSA direct PDF (bot-guard HTML even with UA + versioned URL); DCDT Phoca Download
  raw link (no href on page); guessing ENE chapter names other than Vote 30.

**First extraction run (2026-07-22, ZAF/2024 — 8 of 9 documents extracted, FullENE deferred):**
- **The appropriation statement's layout offsets row labels from values** under `pdftotext -layout`
  (labels stack left, figures stack right) — decode by summing to the verified totals; every block in
  this corpus reconciled exactly once the offset was understood.
- **Vote 30 grain settled:** P5 records at subprogramme grain (Broadband = SA Connect carrier; BDM;
  ICT Support), other programmes at programme grain; Administration and P5 Programme Management not
  recorded (admin overhead). P4 recorded partial (SAPO/SABC in the transfers).
- **Treasury's May-2025 "revised estimate" for Vote 30 (R3,854.8m) was far above the audited actual
  (R2,915.2m)** — treat revised estimates as projections, never outturn evidence.
- **The MTEF cliff is a lead-generator:** Broadband 1,894.6 → 267.4 (2025/26 estimate) exposed the
  SA Connect Phase 2 funding question and produced a contradiction against Budget-2026 reporting.

**Cross-vote scan run (2026-07-22, ZAF/2024 FullENE, 42 votes — step 4a's first execution):**
- **10 records from 6 votes outside Vote 30, totalling ~R2.96bn appropriated — 1.4× Vote 30's own
  clean whole-scope total (R2.11bn).** The sector-vote bias was worse than the first scan suggested:
  DHA's Transversal IT Management subprogramme alone is R1,190.1m (eVisa, kiosks, births automation,
  smart-ID rollout named in the narrative), plus Identification Services R184.7m and a narrative-stated
  R208m PNR line.
- **Single-mandate carve-out first applied:** Information Regulator (Justice vote, Table 25.14) —
  R110.9m FY2024/25, ramp R29.9m (2020/21) → R141.0m (2026/27 MTEF). The DPA funding trajectory is a
  single row in the Justice chapter and invisible from the sector vote.
- **Uniform grain rule adopted (logged decision):** an identifiable departmental IT/digital
  subprogramme line records as whole (Correctional IT, StatsSA ICT, DHA Transversal IT) — Bill's own
  scan set the precedent with Correctional's "Information Technology". What stays out: mixed non-IT
  programmes and whole votes.
- **Narrative-stated project allocations are recordable:** the volume itself names amount+year+purpose
  for lines inside mixed subprogrammes (DHA PNR R208m; eVisa R100m within Transversal IT) — the chapter
  narrative is part of the document, not reporting.
- **Extraction failures (one attempt each, logged):** Science & Innovation "Various institutions: ICT"
  transfer line and Treasury's Financial Systems (IFMS) subprogramme — both garbled under
  `pdftotext -layout` column collapse; pdfplumber candidates for a future pass.
- **Looked for, not found / not recorded:** no separately-appropriated national CSIRT line (the
  Cybersecurity Hub is funded inside Vote 30's programmes, not a vote line); CPSI (Vote 42, R47.9m) is
  general public-service innovation, not single-mandate digital; GCIS is communications, not digital
  transformation.

**Re-extract run (2026-07-22, b5-2024 + b14-2024 → cross-vote):**
- **The Appropriation Bill rescues figures the ENE garbles**: the Science ICT transfer (R22,529k) was
  illegible in the ENE's collapsed transfer table but legible in B5's schedule — when an ENE row fails,
  check the bill's transfer detail before reaching for pdfplumber.
- **B5's "Of which" earmarks are the enacted legal grain**: DHA "Information and Modernisation Systems:
  Operations" R736,994k nests inside the ENE's Transversal IT subprogramme (R1,190.1m) — earmark = ops
  share; the projects (~R453m) are not separately earmarked. Annotate, don't double-record.
- **B14 exposes in-year movements the sector view misses**: DHA +R1.6bn (election year), Justice −R545.9m
  hitting the programme that houses Justice Modernisation and the Information Regulator. Per-subprogramme
  impact needs the per-vote AENE chapters — the standing acquirable for any vote with a material B14 move.

**ZAF 2025 sweep (2026-07-22):** the 2025 budget was tabled **three times** (Feb withdrawn, Mar revised,
**May enacted — "Budget 3.0", 2025-05-21**); the enacted chain lives under `/documents/National
Budget/2025May/`. Bills: `[B16-2025] Appropriation.pdf`, `[B27-2025] Adjustments Appropriation Bill.pdf`.
AENE 2025 under `/documents/mtbps/2025/aene/` incl. `FullAENE.pdf`. FullENE 2025 has a page-count
metadata quirk (reports 30pp; actually full volume, 37 vote markers, 4.5M chars). PMG hosts Portfolio
Committee budget-performance reports as dated PDFs (`pmg.org.za/files/…pccommreport.pdf`) — block-7
scrutiny with quarterly execution figures the budget documents never carry. FY2025/26 outturn/audit not
yet published (DCDT AR ~Oct 2026; AGSA GR ~Mar 2027) — stage gaps, not acquisitions.

**ZAF 2026 sweep (2026-07-22):** Budget 2026 (2026-02-25) under `/documents/National Budget/2026/ene/`;
bill filename pattern changed to `B4-2026 (Appropriation).pdf` (no square brackets); a Special
Appropriation Bill (B3-2026) also exists. **Vote 30 restructured** — programme names all change
(Media and Content; Digital Communication, Access and Services; Digital Infrastructure and Technologies;
Digital Society and Economy): join series on function, not name; the Broadband subprogramme persists
inside Digital Infrastructure and Technologies. Budget-vote speeches moved to May (2026-05-12).
AENE 2026 ~Nov 2026; FY2025/26 outturn (DCDT AR) ~Oct 2026 — the year-later re-runs' targets.

### Template for an entry

```markdown
### <Country> — <document type>, <fiscal year>
- **Document:** <title, URL, how obtained>
- **Structure:** <how the classification chain is laid out; is it machine-readable>
- **Digital lines found under:** <vote/programme names and codes that carried them>
- **Language used:** <the terms the document actually uses — "ICT", "automation",
  "e-governance", "digitalisation", a named system>
- **Where they hid:** <lines that were digital but not obviously so>
- **False positives:** <lines that looked digital and weren't>
- **Outturn available?** <yes/no, which document, how far behind>
- **Scope calls made:** <which lines were whole / partial / unclear, and why>
- **Didn't work:** <what was tried and failed>
```

### Rwanda — the best-published chain in the corpus, and a project-code restructure that breaks it (sweep, 2026-07-27)

**FY runs 1 July - 30 June.** 2024 -> FY2024/25, 2025 -> FY2025/26, 2026 -> FY2026/27.

- **minecofin.gov.rw is a TYPO3 filelist and enumerates completely.** The whole budget tree hangs off
  `/1/publications/reports` under `tx_filelist_filelist[path]=/user_upload/Minecofin/Publications/REPORTS/National_Budget/`:
  `Annual_State_Finance_Laws`, `Budget_Execution_Reports`, `Budget_Framework_Paper`, `Budget_Speech`,
  `Budget_Citizen_Guide`, `Budget_Fact_Sheet`, `Budget_Call_Circular`, `District_Budget`. Folders paginate at 10
  via `tx_filelist_filelist[currentPage]`, and **cHash is per-path so URLs cannot be hand-built** - walk the
  links. Files then live at plain `/fileadmin/user_upload/...` and fetch with no transport problem at all.
  This is the model Track-B target Senegal's DGB was supposed to be.
- **The prize is a ZIP, and it is not in the budget-law folder.** Each year's `Budget_Framework_Paper/<span>_Executive_Budget_Proposal/`
  carries a `BUDGET_ESTIMATES.zip` holding the full annexe set as **native-text PDFs**: ANNEX II-1 detailed budget
  by agency, **II-2 budget by institution/programme/sub-programme**, **II-3 development budget by agency, project
  and funding type**, II-4 economic classification, II-5..II-9 the three-year MTEF cuts, plus Annex 10 performance-based
  budgeting. II-2 is the record grain and II-3 is the origin gate. A run that fetches only the Finance Law gets a
  577-page trilingual gazette and none of these.
- **The Finance Law is an Official Gazette, trilingual, native text.** FY2024/25 = Itegeko n 066/2024 of 26/06/2024
  (OG Special 29/06/2024), 577pp; revised = Itegeko n 008/2025 of 17/03/2025 (OG Special 18/03/2025), 572pp.
  FY2025/26 revised is OG n 10 Bis of 09/03/2026. **Every year in scope has both an original and a revised law**,
  so the revised stage is native here and does not have to be recovered from the next year's comparator column.
- **Execution is quarterly and cumulative** (`Budget_Execution_Reports/<FY>/Q1..Q4`), each quarter shipping the
  report plus `BudgetExecProgSubprog`, `BudgetExecCofog` and a climate annexe. **Q4 is the annual outturn**
  (July-June). FY2024/25 has all four; FY2025/26 had Q1-Q3 as at 2026-07-27.
- **The audit is at oag.gov.rw** `/publications/announcements-2-3` (title "Audit Reports"), named by calendar year:
  `ANNUAL_AUDIT_REPORT_2025.pdf` is the report **for the year ended 30 June 2025**, i.e. the FY2024/25 audit. It
  summarises 257 financial/compliance audits, 18 performance audits and **6 IS audits of key Government information
  systems** - the IS audits are the digital-relevant seam and are worth reading directly.
- **So FY2024/25 has a complete appropriated -> revised -> executed -> audited chain.** That is the shape
  `COUNTRY-BUDGET-BATCH.md` calls the best case, and Rwanda delivers it on the state's own site.

**TWO SILENT STRUCTURAL CHANGES between FY2024/25 and FY2025/26 - both series-breaking:**

1. **Project codes were restructured.** FY2024/25 uses short alphanumeric codes (`483`, `F80` E-PASSPORT, `FCH` AFIS,
   `CQ2` Digital Identification and Authentication). FY2025/26 and FY2026/27 use 10-digit structured codes
   (`P010218001` E-PASSPORT, `P010219002` AFIS). **Nothing signals the change and no mapping is published** - a
   series keyed on project code silently starts a new line at FY2025/26. Match on project *name* across the boundary
   and record the code pair. Same failure mode as Kenya's FY2026/27 programme-code restructure.
2. **ANNEX II-3's funding columns went 6 -> 5.** FY2024/25: `GoR Budget | Domestic Loan | Budget Counterpart |
   External Loans | External Grants | Total`. FY2025/26+: `Agency Budget Allocation | GoR Counterpart |
   External Loans | External Grants | Total` - **the Domestic Loan column is gone**. Any domestic/external split
   compared across that boundary is comparing two different definitions. Sum the non-external columns and say so.

**What the cross-vote scan found (ANNEX II-3, all votes, all three years):**

| FY | digital project lines | non-external (RWF) | total allocated (RWF) |
|---|---|---|---|
| 2024/25 | 44 | 19.09bn | 79.91bn |
| 2025/26 | 43 | 12.60bn | 85.15bn |
| 2026/27 | 41 | 14.65bn | 117.94bn |

- **The headline finding: MINICT's digital development budget is almost entirely donor-financed, and the
  domestically-financed digital state sits somewhere else.** In FY2024/25 MINICT carried Digital Identification and
  Authentication (RWF 8.95bn), Last Mile Connectivity (8.57bn), Modernizing Government Network (5.59bn), E-Service in
  key sectors (4.86bn) and Digital Ambassadors (3.17bn) - **all 100% external** - against roughly 2.76bn of GoR money
  (One Government Network 0.70bn, Telecom House network/security 2.00bn, ICT Ecosystem 0.06bn).
- **The GoR-funded digital lines are security and identity, and they are outside the ICT vote**: PRESIREP/General
  Secretariat NISS - E-PASSPORT 1.60bn, Special ICT Equipment 1.70bn, Automated Fingerprint Identification System
  102.6m; **National Cyber Security Authority 2.56bn, 100% GoR** (a Block 4c governance body and a single-mandate
  carve-out candidate); Rwanda Space Agency satellite teleport 3.09bn and National Geospatial HUB 3.30bn.
- **E-PASSPORT went 1.60bn (FY2024/25) -> 7.01bn (FY2025/26), 100% GoR throughout**, and a new **Border Management
  System** line (259.7m) appears in FY2025/26. E-Gates 2.00bn.
- **Genuine cross-vote lines outside both MINICT and PRESIREP**: MINECOFIN Electronic Single Window (355.7m,
  external), MINAGRI Smart Agriculture Information System (565.2m, mixed), MINEDUC Rwanda Smart Education (2.35bn),
  MINALOC Disability Management Information System (400.0m). A total built from the MINICT vote would miss all of it.

**Method note.** All Rwandan budget PDFs carry a **native text layer** - no OCR needed anywhere in this corpus.
`pdfplumber` with `extract_text(layout=True)` reproduces the column structure well enough to regex the annexe tables
directly; sidecar `.txt` files were written beside every PDF (extract once, grep for ever).

**Searched, not yet established:** whether any line exists for a **data protection authority** - Rwanda's
data-protection supervisory function sits with the National Cyber Security Authority rather than a standalone body,
so the NCSA appropriation may be the whole of it; this needs confirming against ANNEX II-2 and the law before the
absence or the carve-out is stated on the hub.

### Rwanda — first budget-extract of the FY2024/25–FY2026/27 chain (extract, 2026-07-27)

- **ANNEX II-2 is the record instrument, not ANNEX II-3.** II-3 (development projects) is what a keyword scan
  finds first, but it carries only the development budget. **II-2 gives institution × programme × sub-programme
  with recurrent / development-domestic / development-external in one table** — the deal_id grain and the origin
  gate together. Records were built from II-2; II-3 was used for project-level `scope_basis`.
- **The recurrent grain is where the governance money is, and II-3 cannot see it.** PRESIREP carries three
  governance programmes invisible in the development annexe: **FP Cyberspace Protection**, **FQ Cybersecurity
  Standards & Skills**, and **FR Data Protection and Privacy**. A run that scans only development projects
  reports that Rwanda spends nothing on data protection. It spends very little — but "very little" and "nothing"
  are different findings.
- **`5. BudgetExecProgSubprog` closes the chain at the same grain.** Columns are `Allocated | Q1 | Q2 | Q3 | Q4`,
  the quarters are **discrete not cumulative** (they sum to ≈ Allocated), and the *Allocated* column is the
  **revised** domestic figure, not the enacted one — for programme B9 it reads 3 305 312 860 against an enacted
  2 166 312 861. So one document yields both the revised and actual stages. **Caveat recorded on every record:**
  this identification of *Allocated* as revised is inferred from the arithmetic, not stated by the document.
- **Text-extraction trap:** in the execution report the header word "Budget" overlaps the first data row's figure
  under `layout=True`, producing `B 8u80d,3g6e6t,5 91,366` for `800,366,591,366`. Only the first row is affected,
  but any parser must reject rows whose columns do not cross-foot rather than trusting them.
- **Cross-foot results:** II-3 project lines against agency subtotals — 93/96, 86/86, 86/89 exact. The misses are
  ±1 RWF document rounding plus three agri/district blocks with a wrapped line; **no digital agency is affected**.
  II-2 hierarchy — programmes into institutions 52/53, 53/53, 50/52; sub-programmes into programmes 473/475,
  431/431, 461/462.
- **Two wholly-external programme-years were NOT built as records** (PRESIREP F5 Space Programme, FY2025/26 and
  FY2026/27, RWF 4 521 771 882 each). The annexe names no funder beyond "externally financed", so they fail
  fact 1; recording them against the fisc would have credited the state with donor money.
- **Execution findings, FY2024/25** (the only year with a full chain): **FR Data Protection and Privacy — enacted
  RWF 150m, revised down to 100m, actual 52.71m, all of it in Q1 and nothing in Q2–Q4** (35.1% of enacted).
  **FQ Cybersecurity Standards & Skills 11.5%** of enacted. **F5 Space Programme 32.3%**. Against those,
  **B9 National Identification executed 140.7% of enacted** (revised up mid-year) and **14/ES ICT in Education
  executed 252.4% of its revised allocation** — Q3 alone was RWF 2.23bn against a 938m allocation.
- **Not extracted, and worth a later pass:** the OAG report's **6 IS-audit chapters** (the audited stage is held
  but unread for every line), ANNEX II-1 agency-level detail, and the revised gazettes' own annexes.

### Nigeria — a scanned Act, a native Bill that rescues it, and a regulator that is not in the budget (sweep + extract, 2026-07-27)

**FY is the calendar year.** 2024 -> FY2024, and so on.

- **budgetoffice.gov.ng is a Joomla/com_edocman library and enumerates cleanly.** Per-year folders under
  `/index.php/resources/internal-resources/budget-documents/<YEAR>-budget` and
  `/reports/quarterly-budget-implementation/<YEAR>-budget-implementation-report`. Documents are
  `<a class="edocman-document-title-link" href="/index.php/<alias>/<alias>/download">`, with size and date beside
  them. **Downloads are slow** — the 2024 Act is 61.63 MB and the 2025 Act 331.82 MB; use a long timeout and
  verify the byte count against the stated size, because a truncated PDF still opens as a file and then fails
  to parse.
- **Take the "as Passed" copy, not the headline one.** For FY2025 the library offers `2025 Appropriation ACT`
  at **331.82 MB** and `2025 Appropriation ACT as Passed` at **26.86 MB**. The smaller one is native text and
  fully usable; the giant one is not worth the download.
- **THE 2024 APPROPRIATION ACT IS AN IMAGE-ONLY SCAN.** 2,050 pages, no text layer beyond the contents page.
  Full-document OCR at 300dpi/psm3 produced unusable numeric columns; a second pass at **`--psm 6 --threshold 2`**
  on the located summary pages recovered clean rows. Even then only NIGCOMSAT cross-footed exactly; the
  Communications HQ row missed its printed total by **20**.
- **The rescue: the 2024 Appropriation *Bill* (Details) IS native text** (2,290pp, ~3,200 ch/pg) and is a
  separate download from the Act. Acquired by the acquisition pass, it did two things at once: it **supplied the
  digit OCR had dropped** (overhead 530,455,762, read as ...742 — restoring an exact cross-foot on the enacted
  row) and it **independently corroborated** the OCR, since Bill and Act agree exactly on NIGCOMSAT's personnel
  and overhead while capital rose NGN 199,000,000 during passage. **On a scanned Act, fetch the Bill: it is the
  cross-check the cross-foot rule asks for.** Where no Act row survives, the Bill still supports a record at
  `baseline_stage: proposed`.
- **Two structures, both usable.** The Acts/Bills carry (a) per-ministry **Summary by MDA** tables —
  `N.<10-digit code> <NAME> PERSONNEL OVERHEAD CAPITAL TOTAL` — and (b) per-MDA detail blocks ending in
  `TOTAL PERSONNEL / OVERHEAD / CAPITAL / ALLOCATION`. Parse either and **gate on
  personnel+overhead+capital == total**; that gate alone rejects every bad OCR row. The 2026 Bill has no
  per-agency summary at all (its summary is 7-column and ministry-level), so use the block totals there.
- **Line-item descriptions cannot be attributed automatically.** In the detail blocks a project description
  wraps **both above and below** its `ERGP########` code row, with no marker separating one item's tail from the
  next item's head. Any parser that reads "preceding lines = this item's description" mis-assigns them. Use the
  ERGP rows for codes and amounts; verify any description page-by-page before quoting it.

**THE ORIGIN GATE IS THE WHOLE GAME IN NIGERIA.** The FY2025 Communications ministry HQ vote is
**NGN 422,135,762,340**, of which **NGN 400,629,709,813** is one line the Act itself labels
`MULTILATERAL/BILATERAL TIED LOAN - NATIONAL INFORMATION COMMUNICATION TECHNOLOGY INFRASTRUCTURE BACKBONE
(NICTIB) PHASE II`. The domestic vote is **NGN 21.5bn**. In FY2026 the same line is NGN 30bn and the domestic
vote NGN 16.06bn. There are **23 tied-loan lines** across the FY2025 Act. Grep `TIED LOAN|MULTILATERAL/BILATERAL`
in every MDA before setting an amount — this is the cross-cutting "government invests = external money in state
clothing" warning in its purest documented form.

**What is not in the budget is the finding.** **NITDA, the NCC and the NDPC carry no appropriation line** —
they are levy- and licence-funded (Block 6 own-source bodies). The **Nigeria Data Protection Commission appears
in the FY2025 Act only as the named implementing agency for zonal constituency projects** inside the
Communications vote: data-protection induction training in Ogun Central (NGN 227,210,795) alongside school
materials, classroom furnishing and solar street lights. A sweep that looks only for a "data protection" vote
concludes Nigeria spends nothing; the truth is stranger and worth stating carefully.

**No execution stage exists for any in-scope year.** The **Auditor-General for the Federation publishes to 2021
only** (`oaugf.ng` — note `oaugf.gov.ng` fails TLS from this network), a three-year lag. And **Appendix I of the
2024 Fourth Quarter and Consolidated Budget Implementation Report — the MDA release-and-utilisation table — is
cited at p.38 of both the consolidated and standalone volumes and published in neither.** The consolidated
volume does carry **project-level narrative** for monitored agencies ("In the 2024 budget, the sum of
N166.50 million was appropriated, while N163.22 million was released and utilized to achieve 80% level of
completion"), which is a usable release/actual seam for individual projects but not for MDA totals.

### Cabo Verde FY2024–FY2026 — the extraction pass: the records are on the programme axis, the origin gate is in `Mapa VII`, and the identity and universal-service money was in the annexes all along (budget extract, 2026-08-04)

*(All three CPV country-years drained in one pass — 91 documents, 30 finance records, 10 source pages. The three sweep sections above hold the reconnaissance; this one holds what reading the documents changed. New archetype **R** in the strategy library.)*

- **⚠⚠ THE RECORDS ARE BUILT ON `Mapa VII`, NOT ON THE VOTE TABLE, AND THAT IS THE CENTRAL METHOD DECISION OF THIS PASS.** `Mapa III` publishes ministry × programme *type* (Investimento / Finalístico / Gestão e Apoio Administrativo) — a programme-type split, not a programme, so a ministry row is an **envelope** and the driver's envelope rule bars it. **`Mapa VII — Despesa por Programa e Tipo de Financiamento` is the finest published grain at which a line's stated purpose is digital, and the only table in the whole budget that prints the origin split.** It reappears with `OI | ORP | EXE` columns in the `Conta Geral do Estado` and in every quarterly `Conta Provisória`, so one table carries the whole stage ladder cross-vote with the domestic/external split on both the reprogrammed and the executed side. **Recording both axes would double-count the same escudos**, so the organic figures are carried in each record's `## Notes` and in the source pages and are not records. The two axes are not each other's subtotals and neither should be quoted without the other.
- **THE ORIGIN GATE IS PRINTED: `Tesouro | OFN | FCP AAL | Donativo | Empréstimo`.** `OFN` is *Outras Fontes Nacionais* (the CGE's own narrative table names it in full) and `FCP AAL` is the *Fundo de Contravalor / Ajuda Alimentar*. **`Tesouro + OFN` is the domestic-state share.** For FY2024 the *Cabo Verde Plataforma Digital e da Inovação* programme totals CVE 1,828,303,885 of which **only CVE 568,184,541 (31%) is the state's own money**; the rest is loan and grant finance. No external record was built from any of it — the mapa names only "Donativo" and "Empréstimo", never a financier, so those lines fail the spec's fact 1.
- **⚠⚠ CORRECTION TO THE FY2025 SWEEP SECTION: THE `G0–G3` COLUMNS ARE GENDER LEVELS, NOT FUNDING ORIGIN.** The FY2025 run recorded "THE ORIGIN GATE IS PRINTED ON THE PAGE, pp.79–80 OF THE CONTA PROVISÓRIA … 47.5% of the digital ministry's reprogrammed budget is external contribution, and 4.5% of it was drawn." **That is wrong.** The table is `Mapa XV — Orçamento Por Níveis de Género e Orgânica`; `Nível G0–G3` are gender-responsiveness levels and `Total Contribuição Género` is the gender contribution. The CGE 2024's copy proves it: Economia Digital ORP 1,483,485,681 = G0 1,443,559,905 + G1 39,925,776, EXE 489,920,474 = G0 463,247,395 + G1 26,673,079, and the printed **66.8%** is 26,673,079 ÷ 39,925,776 — a ratio of two gender columns, not of outturn to anything. **`Mapa VII` puts the FY2025 digital programme's external share at 64% of ORP, not 47.5%.** General rule: a "contribuição" column in a Lusophone budget mapa is as likely to be gender budgeting as external financing; check the mapa's own title before treating it as an origin split.
- **⚠⚠ THE RE-READ THE FY2026 SWEEP ASKED FOR PAID: SNIAC AND FUSI WERE IN THE FY2024 AND FY2025 PACKAGES ALL ALONG, AT IDENTICAL FIGURES.** `Sistema Nacional de Identificação Civil — SNIAC` **CVE 306,516,802** (PEC 141,524,912 + CNI 109,383,546 + TRE 22,500,000 + 33,108,344, cross-footing exactly) and `Fundo de Serviço Universal e Desenvolvimento da Sociedade de Informação (FUSI)` **CVE 122,073,633** appear **unchanged to the escudo in FY2024, FY2025 and FY2026**. Only the label of sub-line 9.4 changed, from `Funcionamento do SNIAC` to `Instituto Modernização e Inovação da Justiça`. The FY2024 and FY2025 runs both closed with "searched, found nothing: any universal-service fund; any ICT levy body" — **the fund was in the tabled `Anexo Informativo` of the volume they already held.** *A three-year unchanged earmarked ceiling is itself a finding: these are fee-financed authorisations rolled forward, not re-estimated against receipts.*
- **⚠ AND THE STAGE DIFFERS BY YEAR, BECAUSE THE ENACTED VOLUME DOES NOT ALWAYS REPRINT THE ANNEX.** The FY2025 and FY2026 laws carry the `receitas consignadas` table inside the Boletim Oficial; **the FY2024 law does not** — a full-text search of the 128-page enacted volume returns no occurrence of `SNIAC`, `Passaporte`, `Universal`, `FUSI`, `306 516 802` or `122 073 633`. So the identical figures are `appropriated` for FY2025 and FY2026 and only `proposed` for FY2024. **Never carry an annex's stage across years; search the enacted volume for the figure.**
- **The earmarked lines were tested for nesting before being recorded, and the test is reusable.** A counterpart expenditure is inside *some* vote by construction, so the question is whether it is inside a vote this pass also records. `50.01.01.01.109.01 — SNIAC` appears in the December 2024 virement register **under `GOV - Ministério da Justiça`**, whose pillar programme (*Justiça e Paz Social*) is not recorded — so the four SNIAC lines are recorded normally. `50.01.01.04.40 — Espaço Cidadão - Comunidade Integrada` appears **under Modernização do Estado**, which *is* recorded — so the Casa do Cidadão lines are noted, not recorded. FUSI appears in no mapa and no virement row at all, so its carrying vote is unresolved: recorded with **`is_transfer: true`**, which keeps it out of the compiled headline total while preserving the figure. **The virement register is the instrument that settles nesting questions, because it prints the organic code beside the project name.**
- **⚠ THE `Mapa VII` PROGRAMME PERIMETERS ARE NOT STABLE AND ONE OF THEM MOVES EVERY YEAR.** *Modernização do Estado e da Administração Pública*: CVE **609,582,068 → 5,434,369,323 → 976,042,125** across FY2024–FY2026. Every year's pillar column cross-foots exactly (FY2025 Soberania Tesouro: 1,945,833,907 + 98,987,103 + 2,458,200,046 + 2,336,332,334 + 5,434,369,323 + 6,808,598,661 = 19,082,321,374), so these are real reclassifications. **The three records carry the warning in their own `## Notes`; do not read a trend off them.** The organic vote is the stabler measure over the same period (368,989,734 → 269,785,474 → 292,594,728) — and its **code moved too**, `01.03.10` → `01.03.11`.
- **The digital platform programme's domestic share is the number that survives all of this**: CVE **568,184,541 → 597,668,565 → 476,994,724** (FY2024–FY2026), a 16% fall in two years, against an **87.5% fall in the digital ministry's vote**. Executed domestic: 368,518,763 (64.9% of the vote) in FY2024; **593,300,771 (99.3% of the vote, 74.4% of the revised)** in FY2025; 135,335,579 at Q1 2026. **What did not move in FY2025 was the borrowed money, not the voted money** — the 37.9% organic headline and the 99.3% programme-domestic figure are the same year seen from two perimeters, and quoting either alone misleads.
- **A Q1 execution figure is not an outturn and is not stored as one.** All three FY2026 programme records carry `current_stage: revised` with `actual_total` blank and the 31 March 2026 execution held as a dated `## Stage history` line. A three-month figure in `actual_total` would let the compile read it as the year's outturn and compute a false execution rate.
- **⚠⚠ THE CNPD'S FY2026 APPROPRIATION IS NOT ESTABLISHED, AND THAT CLOSES THE FY2026 SWEEP'S OPEN ITEM AS AN ABSENCE.** The FY2026 volume carries **no** Assembly *Orçamento Privativo* resolution and **no occurrence of `CNPD`, `Protecção de Dados` or `ORGÃOS EXTERNOS` in its 266 pages**. The `Comissão Nacional de Eleições`, which sat in the privativo in FY2024 and FY2025, appears in FY2026's `Mapa III` as its own OSOB row at CVE 46,300,000 — the órgãos externos moved and the DPA did not surface with them. **Stated as a dated absence (2026-08-04), not a nil**; the FY2026 resolution is a separate instrument this pass did not find published. FY2024 CVE 35,255,451 and FY2025 CVE 36,313,115 are both recorded, both `Receita Próprias 0`, and **neither year publishes an outturn for the line** — the accounts report the Assembly as one organic row.
- **A first cybersecurity budget unit, and it is only in the narrative.** `Lei n.º 69/X/2025`, BO p.126: *"inscrições de unidade orçamental: 'Ciber Segurança' com 20 milhões de CVE"*, under the function `Serviços Públicos Gerais`. No mapa breaks it out, so the record carries the law's own rounding to millions and says so. **Both earlier years carry no cybersecurity rubric at any grain** despite `Decreto-lei n.º 9/2021` and the CSIRT's October 2025 launch — the money was inside NOSi.
- **NOSi is recorded at its `Protocolos` line only, `state_level: soe`, `is_transfer: true`, and the line is CVE 333,345,000 in all three years.** The forecast total runs 1,016,801 → 1,486,249 → 1,094,297 mCVE against a digital ministry vote of 1,390,965,632 → 369,781,930 → 174,200,533 CVE — a ratio of **0.73× → 4.0× → 6.3×**. `Projetos Financiados` (donor) falls 269,638 → 234,465 → **111,581** mCVE, which is what *Digital Cabo Verde* winding down looks like from the implementing agency's side. **⚠ The PAO is the only CPV artefact in `mCVE`, in all three years.** The FY2024 components sum to 1,016,802 against a printed total of 1,016,801 — a one-thousand-escudo rounding, noted and not corrected.
- **The rotation trap is not a property of the series.** FY2024 and FY2025 rotate the mapa pages; **FY2026 does not** — `pdftotext -table` reads it upright, first attempt. Probe each year's file.
- **`pdftotext -table` beats both `-layout` and pdfplumber on the unrotated Cabo Verdean mapas**, including the 226-page CGE, where `-layout` mis-assigns money to the wrong ministry row by several lines and would have produced confidently wrong records. On the *rotated* pages neither works and the de-rotation recipe is required.
- **The `Conta Geral do Estado`'s `Mapa VII` is the single best artefact in a CPV country-year** — programme grain, origin split, `OI | ORP | EXE | Taxa`, cross-vote, native, at PDF pp.179–180 of the CGE 2024. The quarterly `Mapas_Contas_{n}º_Trim_{year}_Site.xlsx` carries the same table machine-readable and is better still. **Fetch that XLSX for every quarter of every future CPV run.**
- **Case 5: nothing to reset.** The wiki held **no** CPV `domestic-state` records before this pass, so no reporting-built record was superseded. **No contradictions were filed**: every cross-document check reconciled — the enacted `Mapa III`, `Mapa VII` and the CGE agree to the escudo on every digital row, all three years' grand totals cross-foot, and the FY2025 Assembly amendment (128,759,798 CVE moved into the Assembly's own programme) leaves both digital ministries' rows untouched.
- **OCR: one attempt, one terminal state.** The ARAP *Plano Anual de Aquisições* is a 4-page zero-text scan in all three years. One OCR run (`--lang por`, 300 dpi, psm 3) returned 11,242 characters of unusable output — headers dissolved into noise, no figure cross-footable. **All three are archived `n/a` / `OCR-illegible`; a second and third identical attempt would establish nothing.** The sidecar is committed beside the FY2024 PDF so nobody repeats it. The `ROE 2025` and `ROE 2026` image PDFs were **not** OCR'd: the enacted volumes and the `Diretrizes`/`Directivas` carry the same ground natively, so the OCR spend buys nothing.
- **The virement register supports evidence, not records.** `Alterações Orçamentais` rows are `ANULAÇÃO`/`REFORÇO` movements, not stage totals, so no per-virement records were built. What the series *is* for: settling which vote carries a line (the organic code is printed beside the project name), and naming projects no mapa names — `65.05.02.02.117 Cabo Verde Digital`, `50.01.01.01.109.01 SNIAC`, `50.01.01.04.40 Espaço Cidadão - Comunidade Integrada`, `50.01.01.01.357 Parque Tecnológico PHASE II`, `55.04.01.05.42 Produção de Dados Estatísticos`, `55.04.01.05.35 Produção de Dados e População`, `50.01.01.01.324 Reforma Digital ++`, `50.01.01.03.71 Unidade de Tecnologias, Inovação e Comunicação`, `40.10.30.02 CSMJ — Sistema de Informatização de Justiça`, `40.10.32.02 CSMP — Sistema de Informatização de Justiça`, `50.05.01.03.69.02 Sistema de Informação Criminal CGJ`.
- **Tax expenditure is read and not recorded.** The FY2026 `Justificação dos Benefícios Fiscais` prices relief for `Tecnologias de Informação`, the `Zona Económica Especial para Tecnologias (ZEET)`, digital terrestrial television rollout and data-centre, computer and tablet imports. **Foregone revenue is not an appropriation** and must never be recorded as one — but it is the only place the state prices what it gives up on digital, and it is worth a dated place-hub line.

### Ghana — first budget-extract: the estimates are one MDA per volume with the money in screenshots, and the Act is the only cross-vote instrument (extract, 2026-08-05, FY2024 + FY2026)

**FY is the calendar year.** 2024 -> FY2024, 2026 -> FY2026. First Ghanaian budget documents extracted; the wiki previously held no GHA `domestic-state` record.

- **Two artefacts, two jobs, and neither substitutes for the other.** The **programme-based budget estimates** (`mofep.gov.gh/sites/default/files/pbb-estimates/{year}/{year}-PBB-{MDA}_.pdf`) give sub-programme grain for **one MDA**; the **Appropriation Act** gives programme grain for **all of them**. A run that fetches only PBB volumes can never scan cross-vote, and a run that fetches only the Act can never get below programme. Fetch the Act first — it is twenty pages and it tells you which PBB volumes are worth the fetch.
- **⚠ THE PBB'S FINANCIAL TABLES ARE PASTED IMAGES INSIDE A NATIVE DOCUMENT** — see archetype S. 23 of the MLGRD volume's 119 pages return exactly 26 characters (the running footer) and hold every figure in the book. A pass that trusts `pdftotext -enc UTF-8 | wc -c` reports that a Ghanaian ministry published a budget with no budget in it.
- **The digital vocabulary is thin and the money is not where the words are.** Across all 170 programmes of the FY2026 Act, a digital-term regex returns five rows. The identity seam — `00903 Passport Administration`, GHS 148,820,843 under Foreign Affairs — is reachable only by reading the programme names.
- **Digital lines found under:** vote 026 `02602 ICT Capacity Development` and `02603 ICT Infrastructure, Regulation and Capacity Building`; MDA 082 `Right to Information Commission`; vote 009 `00903 Passport Administration`; and, in the MLGRD PBB, sub-programmes `01101004 Research; Statistics and Information Management` and `01109001 Human Settlements and Land Use Reaseach and Policy`.
- **THE HEADLINE FINDING — Ghana's digital state is 11.4% treasury-financed.** Programme 02603, the largest digital line in the budget, is GHS 729,947,850: **GoG 83,007,265 (11.4%), internally generated funds 508,940,585 (69.7%), donors 138,000,000 (18.9%)**. The regulator's and agencies' own licence and levy income, not the fisc, is what pays for Ghanaian digital infrastructure and regulation. Only `02602 ICT Capacity Development` (GHS 100,000,000) is wholly treasury money, and it carries no compensation of employees at all.
- **THE SECOND FINDING — three of the four named digital-governance bodies are not votes.** The **Data Protection Commission**, the **Cyber Security Authority** and the **National Information Technology Agency** appear nowhere among the Act's 57 MDAs; on the vote structure they are funded inside programme 02603, and the Act publishes no sub-programme, so the split between them is **not established**. The **Right to Information Commission is** its own MDA (082, GHS 20,413,271, 100% GoG) — so this is a fact about those three bodies, not about how Ghana appropriates to independent bodies.
- **THE THIRD FINDING — the MLGRD volume describes seven programmes and funds six.** *Births and Deaths Registration* — the CRVS spine of Ghana's identity system — has **no appropriation line at any grain** in its parent ministry's FY2024 estimates, while the narrative describes its system consolidation, digitisation of manual records, bandwidth upgrade and electronic statistical reporting dashboard as **World Bank PSRRP, HISWAP and UNICEF** work. Whether the Registry is appropriated under its own entity code is not established from this document; its own PBB volume is on the acquisition list.
- **Scope calls made:** `02602` and `082` and `02603` whole; `00903 Passport Administration` partial (the Act prints no split between the biometric passport system and consular issuance); `01101004` and `01109001` partial. **Not recorded:** `02601` ministry administration; `02604 Meteorological Services`; `02605 Postal and Courier Services`; and — deliberately — **`00110 Information Management` (Office of Government Machinery, GHS 273,682,461)**, whose name will not say whether it is government communications or government IT and which the Act does not break down. That is the largest unresolved candidate in the Ghanaian budget and it needs the OGM PBB volume.
- **The origin gate is printed, four ways, on both artefacts** — `GoG | IGF | Funds/Others (Statutory, ABFA, Others) | Donors`, each split into compensation / goods and services / non-financial assets. Internally generated funds are `domestic-state` (state revenue by another route); the donor block is `non-state` and, because the column heading is the only funder named, **fails fact 1 and builds no record** — GHS 138,000,000 of programme 02603 is therefore stated on the record and not counted.
- **Stage.** The PBB's money table is headed *1.5 Appropriation Bill … Base Version*, which reads pre-enactment — but the file was **created 2024-04-09**, three months into the fiscal year and well after the Appropriation Act 2024 passed. Per the Ethiopian stage trap (archetype O), the timestamp beats the caption: recorded `appropriated`, `budget_version: original`. Act 1163 carries no assent or gazette date on its face, so both years take `published = fy_start` at `date_precision: month`, per the driver.
- **Didn't work:** the Act's **Third** Schedule (MDA grain) has different column x-positions from the Fourth and the shared extractor returns nothing usable for it — no matter, because the Fourth Schedule carries MDA rows too and cross-foots. OCR alone was not enough for the PBB's dense 1.5 table: it drops whole rows, and the figures were taken off a 300 dpi render instead.

### Rwanda — the FY2023/24 back-year, and the extractor that finally cross-foots (extract, 2026-08-05, FY2023)

- **No records built. FY2023/24 begins 1 July 2023 and falls outside the wiki's FY2024-onwards scope cut** (`finance-load-domestic-state.md` -> *Fiscal years*). The annex is extracted, cross-footed and archived as the dated prior-year **baseline** for the FY2024/25 series, per `CLAUDE.md` -> *Currency* ("an older source arriving late is a baseline, not news").
- **⚠ THE TEXT LAYER OF ANNEX II-3 IS OFFSET AND THE OFFSET IS PLAUSIBLE.** `pdftotext -layout` reads *482 E-Gates* at Frw 8,524,696,694; the page prints **2,538,577,501**, and the 8,524,696,694 belongs to an agency row above. Every figure in the block is attached to the wrong project and every one of them looks like a budget. `scripts/rwa-annex-ii3-extract.py` binds by page geometry instead: **1,040 rows (52 ministries, 101 agencies, 887 projects), zero cross-foot failures** — every project sums to its agency and every agency to its ministry, exactly.
- **Two bugs worth naming, because both are silent.** (a) **An agency block runs across the page break** — NCSA's Frw 945,000,000 cyber-security building is the first row of the next page — so ministry and agency must carry over pages, not reset per page. (b) **Where a project label wraps, the renderer emits its figures a fraction of a point ABOVE the label's first line** (top 208.1 against 208.9). Grouping rows by `round(top/3)` puts them in different buckets and the money vanishes; cluster on `top` with a ~3.5pt threshold instead. Together these two accounted for 37 of 37 district and ministry shortfalls.
- **The FY2023/24 annex already has the FIVE-column funding shape** — `Agency Budget Allocation | GoR Counterpart | External Loans | External Grants | Total` — i.e. the post-FY2025/26 form, not the six-column FY2024/25 form the 2026-07-27 sweep note describes. **So the six-column edition is the outlier, not the boundary**; a domestic/external comparison across FY2023/24 -> FY2024/25 -> FY2025/26 is comparing three definitions, not two.
- **Correction to the companion page's first-pass figures:** the NCSA block is confirmed exactly (FFD 1,766,676,491; FFE 251,000,000; FFF 500,000,000; FMW 945,000,000; agency total **3,462,676,491, 100% GoR**), but **Rwanda Space Agency's Frw 1,094,665,900 is its agency-allocation column, not its total** — the agency total is **6,012,259,369**, the difference a Frw 4,917,593,469 external loan carried on project FMY *National Geospatial HUB*.
- **The FY2023/24 baseline for the series that matters.** RISA: agency allocation 6,383,972,823 + GoR counterpart 72,700,000 against external loans 27,949,381,823 + external grants 4,019,963,856 — **Frw 38,426,018,502 total, 83.2% external**. The GoR-funded lines are the same security-and-identity cluster the FY2024/25 extraction found: General Secretariat NISS, agency total 13,407,708,609 and 100% GoR, of which *E-Gates* 2,538,577,501, *Special ICT Equipment* 1,700,000,000, *E-PASSPORT* 1,596,051,426, *API/PNR* 443,486,704 and *AFIS* 102,613,560. RISA's own GoR money is *PUBLIC CCTV* 1,500,000,000, *Strengthening Telecom House IT Network and Security* 2,500,000,000, *One Government Network* 1,200,000,000, *Microsoft Enterprise Agreement* 800,000,000, *National Public Key Infrastructure* 332,876,023 and *Government Command Center* 51,096,800.
- **Not extracted:** ANNEX II-2 for FY2023/24 (the record instrument, and the one the FY2024/25 records were built from) is **not held** — only II-3 was acquired. It is not on the acquisition list because the year is out of scope; if the scope cut ever moves, that is the fetch.

## Cross-cutting observations

*(patterns that hold across several countries — promote them here once seen more
than once, so a country section doesn't have to restate them)*

**From the 2026-07-22 back-swing (894 sources screened, 23 records, ~2.6% hit rate):**

- **Fact 3 (no amount at a budget stage) is the systematic failure point** for domestic items in sweep news. Reporting gives the instrument without the appropriation figure: fund launches with mobilisation targets (CIV F2it, Algeria FNI), guarantee mechanisms, "quote-part" counterpart promises stated qualitatively, Cabinet/strategy approvals with USD price tags but no FY/stage/funding source (Ghana $250m AI centre).
- **Domestic figures hide mid-paragraph inside stories about something else** — an MoU, a donor project, a summit speech. Grep bodies for "allocated|budgeted|also allocated|également alloué|additional|a coûté|financés à hauteur de|aprovou a despesa" rather than trusting headlines. Government top-ups ride donor-project coverage as "the government has also allocated…".
- **"Government invests" headlines are usually external money in state clothing** (Chad PMICE = Eximbank; Cameroon videosurveillance = Chinese banks; Nigeria's 49% BRIDGE SPV stake = capitalised from the IDA credit) or vendor-financed DBFOT deals where no fisc money moves at signature (Gambia–Margins ID). Check the funding source and the delivery-model phrase before crediting the fisc.
- **SOE stories in the sweep are all own-revenue or inbound money** — no state→SOE subvention appeared in 894 sources. Privatisation proceeds and spectrum sales are state *revenue*, not spend. Sovereign guarantees (Cabo Verde aval for CV Telecom) involve no cash outlay.
- **Multi-year plan envelopes (PND, "Digital Nation", Tchad Connexion 2030) always fail** — MTEF-like indicative figures; the capture target is the annual loi de finances line beneath them. Supplementaries (DRC collectif budgétaire) are where deferred figures eventually surface.
- **Ministry-envelope near-misses are the commonest domestic signal** (CIV, BEN, GAB, BFA, SEN, SA Home Affairs). Rule held: envelopes are not records; a source-stated *investment slice* tied to digital priorities (SEN) or a *programme line* (BEN) is.

### Angola — OGE package via minfin CMS, FY2024 (sweep, 2026-07-23)
- **minfin CMS is IP-pinnable, not locally resolvable.** `cms.minfin.gov.ao` fails on local DNS
  (curl exit 6); DoH→`20.87.80.66` + `curl --resolve cms.minfin.gov.ao:443:20.87.80.66` fetches the
  OGE-package PDFs directly. Assets are UUID-keyed `/api/assets/portal-minfin/<uuid>/` (also
  `portal-sncp` for the procurement portal). This is the Track-B entry for every AGO year — the
  portal exposes Fundamentação, Mapas Orçamentais, and the **Relatório de Execução Trimestral**
  (quarterly; the **IV Trimestre = full-year outturn**, the prize, SIGFE-sourced).
- **Scale trap confirmed at source:** Portuguese **`bilião` = 10¹²**, `mil milhões` = 10⁹; tables use
  full values with **decimal comma + space thousands** (`24 715 263 134 196,00`). Novo Jornal's
  "bilião" is unreliable (back-swing note) — but the *ministry's own* documents are consistent 10¹².
- **Digital lines are NOT in the Fundamentação** (functional envelope only: dívida 57,8%, social
  20,1%, …). They live in the **Mapas Orçamentais** (Dotações por Órgãos × programa × projecto — in
  acquisitions) and the outturn's **ANEXO 13 (por projecto)** / **ANEXO 12/16 (por UO)** — extract
  there for named systems (Angosat, redes, plataformas, identificação) under MINTTICS / MAT /
  Interior / Justiça.
- **In-year appropriation surfaces via decretos, not a revised volume:** créditos adicionais
  suplementares + **DP 278/24** contrapartidas intersectoriais (saldos ociosos). The Assembly does
  not re-vote a *revisão* — reconcile revised vs initial through the trimestral execução reports.
- **Procurement portal (SNCP):** the **RACPA** (Relatório Anual da Contratação Pública Angolana,
  `portal-sncp/…`) gives per-ministry PCP counts (2024: MINTTICS 41 procedures, 80,3 mil M Kz); the
  per-EPC **PAC** (mandatory under Lei 41/20, art. 442) carries the project-level digital lines —
  MINTTICS PAC is the recurring annual seam (2025 PAC: Angosat-3 278 bi, banda larga, centro de
  dados — heavily reported by pti.ao / Novo Jornal; the *actualização* corrects wild scale swings).

### Angola — OGE 2025 package, FY2025 (sweep, 2026-07-23)
- **Same Track-B route holds:** DoH `cms.minfin.gov.ao`→20.87.80.66, UUID-keyed
  `/api/assets/portal-minfin/<uuid>/`. **Exa surfaces the asset UUIDs directly** — one search
  returned the whole 2025 execução-trimestral series: I `df341d44-…`, II `37498c08-…`, III
  `b5aa3d45-…`, **IV `6fb282a3-…` (the full-year outturn, finalised 12-Mar-2026)**. The 2025
  Fundamentação minfin canonical UUID did NOT surface (2024 was `b95da7f3-…`); the reachable copy
  is the **CABRI BIA mirror** (`cabri-sbo.org/uploads/bia/Angola_2025_Formulation_…4db698.pdf`,
  ~6 MB) — MINFIN's own document, fetchable by plain curl+UA.
- **The IV-Trimestre report is NARRATIVE ONLY (57pp).** ANEXO 13 (por projecto) and ANEXO 16 (por
  UO) are **TOC-listed but not printed** in it — a *separate anexos volume*. So the outturn PDF gives
  aggregate + functional/sector taxas de execução, but **no per-project/UO digital lines**. Same
  almost certainly true of the 2024 IV-Trim already staged: to get executed digital lines you need
  the anexos volume, not the report. **This changes the acquisition target** — queue the anexos, not
  just the Mapas.
- **The digital envelope is in reporting, not the Fundamentação:** pti.ao read the OGE 2025 MINFIN
  document and gives the **Comunicações e Tecnologias de Informação sector = Kz 226,4 mil milhões
  (~7× OGE 2024)** and the programme **"Expansão e Modernização das Comunicações" Kz 229,3 mil
  milhões**. The Fundamentação carries only the functional envelope (confirmed again). Grep pti.ao by
  programme/rubrica name for the appropriated split before the Mapas land.
- **PAC scale-trap realised at source:** the first MINTTICS PAC 2025 (21-Jan) totalled Kz 616,7
  *biliões* — larger than the whole OGE (34 bi). The **actualização (27-Fev, pub. 05-Mar)** corrected
  it to Kz 225,6 *mil milhões*; satellite Kz 298,7 bi → 712,7 M, earth-obs 10,4 bi → 77,7 M. **Always
  take the actualização, never the first PAC** — the held Angosat-3 278 bn record is a first-PAC
  artefact (contradiction filed 2026-07-23).
- **Identity money surfaces as a despacho, not a vote:** **DP 169/25 (19-Set-2025)** opened a
  crédito adicional suplementar of **USD 218,5 M** for the Bilhete de Identidade universalisation,
  afecto ao **Min. Justiça** — stated in USD, in OGE 2025. lex.ao reproduces DR text verbatim (good
  Block-5 source). Grep lex.ao / DR by "Crédito Adicional Suplementar" + programme name for the
  in-year DPI appropriations the vote structure hides.

### Angola — OGE 2026 package, FY2026 in-year (sweep, 2026-07-23)
- **Same Track-B route holds:** DoH `cms.minfin.gov.ao`→20.87.80.66, UUID-keyed
  `/api/assets/portal-minfin/<uuid>/`. **Exa surfaced the Fundamentação OGE 2026 UUID directly**
  (`8983392b-8784-45d7-a23d-1aa35cf938b4`; native PDF, 75pp). But the **I-Trimestre 2026 execução
  UUID did NOT surface** (Exa returns only the prior-year 2025 quarterly series — I `df341d44`, II
  `37498c08`, III `b5aa3d45`, IV `6fb282a3`); the current-year execution report lags the search
  index → queued, not fetched. Lesson: for an in-year run, the appropriation doc is Exa-findable but
  the just-published quarterly execution is not — expect to queue it.
- **The 2026 Fundamentação embeds the full Lei articulado** (ARTIGO 1-33 + fiscal measures + DR
  summary + media note), unlike the 2024/2025 Fundamentações (fiscal-strategy narrative only). One
  fetch gives both the exposição de motivos AND the OGE-2026 law text. Still **no programme/project
  digital lines** — functional envelope only; the Mapas remain the acquirable for per-organ detail.
- **OGE 2026 total FELL:** Kz 33,24 biliões, −4% vs OGE 2025 (34,63 bi) — first drop in the series
  (24,72 → 34,63 → 33,24). Enacted 15-Dez-2025 as **Lei 01/V/4.ª/2026-2027** (proposta total held).
- **The digital communications programme was cut, not grown:** "Expansão e Modernização das
  Comunicações" **159,2 mil milhões** (−30,5% vs 229,3 in 2025); 4G 62,7 (−42%); cyber-index
  programme 32,3 (−54%); "Cobertura 3G" line removed. The 2025 ~7× spike partly reversed —
  reporting reads the OGE "Despesa por Programa Detalhado" rubric (pti.ao by programme name).
- **In-year appropriations surface as January despachos, well before the execution-rules decree:**
  **DP 12/26 (7-Jan, Kz 9,2 mM telecoms/hosting MINFIN)** and **DP 11/26 (13-Jan, Kz 8,6 mM Microsoft
  licences whole admin via IMA)** were both signed *before* the OGE-2026 execution rules (DP 74/26,
  23-Abr) existed, so they cite the *prior year's* rules (DP 42/25). angolex.com reproduces despacho
  text verbatim (as lex.ao does) — grep angolex/lex.ao by "É autorizada a despesa" + January of the
  FY year for the earliest in-year digital appropriations. The Microsoft one is a **cross-government**
  e-gov line (via IMA), invisible from the MINTTICS vote.
- **The Q1 execution report is newly per-organ:** for FY2026 MINFIN published, "for the first time",
  a *quadro detalhado de Execução Financeira por Órgão do Governo* — the per-ministry Q1 execution
  (MINTTICS 3%; 20/50 programmes <5%), reported by Diário dos Negócios / Expansão. This is the
  per-organ executed-digital route in-year, ahead of the IV-Trim anexos — worth acquiring the report
  (`ago-execucao-i-2026`) for the MINTTICS/Justiça/Interior rows.
- **DPI legislation catching up with the money:** the **Lei da Identificação Civil e Criminal**
  (Conselho de Ministros → Assembly, Apr-2026) sets the legal regime for BI + criminal-record data —
  the framework arriving a year after DP 169/25's USD 218,5 M ID crédito. Pair them on the AGO hub.

### Angola — PAC procurement estimates track the OGE vote (ingest, 2026-07-23)

- **The corrected MINTTICS PAC 2025 appears to be re-based on the enacted OGE, with different line
  names.** Two lines match the OGE 2025 programme figures *exactly*: "Implementação da Rede Nacional
  de Banda Larga" **Kz 107,8 mil milhões** = the OGE "Expansão da rede 4G" line, and "Plataforma
  Analítica, Centro de Dados Principal, Back Up e Plataforma Nacional de Nuvens" **Kz 70,5 mil
  milhões** = the OGE "melhoria da posição no Índice Global de Cibersegurança" line. The PAC total
  (Kz 225,6 mil milhões) also near-matches the OGE digital sector envelope (Kz 226,4 mil milhões).
  **Practical consequence: never build finance records from both the PAC and the OGE programme
  table for the same fiscal year — they are the same money under two naming systems.** Prefer the
  OGE line (it carries a budget stage); treat the PAC as procurement detail and as the vendor route.
- **Corollary for scope:** the *cybersecurity-index* programme name is a policy target
  ("improve the country's ranking on the Global Cybersecurity Index"), not a description of what is
  bought. If the PAC equivalence holds, the money behind it is a **data centre / analytics / cloud**
  procurement. Do not infer the object from a programme title alone.
- **Parent/child double-count trap in the OGE programme table.** pti.ao reports both the programme
  total ("Expansão e Modernização das Comunicações") and its named sub-lines (4G, 3G, cyber-index).
  Recording both inflates the domestic total. Capture the **parent once**, hold the sub-lines in the
  record body — until the Mapas give a clean per-project table.
- **Origin risk to carry forward:** the OGE 4G line may be the China Eximbank-financed RNBL wearing
  a domestic label. No source on file states the funding source of any OGE digital line, so the
  origin gate defaults them to `domestic-state`, flagged. The Mapas (`ago-oge2025-mapas`,
  `ago-oge2026-mapas`) are the arbiter — this is the single highest-value AGO acquisition.

### Angola — enacted OGE volumes come from mirrors, not the ministry (acquisition, 2026-07-23)

- **Three sweep passes failed to surface a minfin CMS UUID for any enacted OGE volume. Two mirrors
  delivered them on one attempt each** — and both use plain, unguarded, directly `curl`-able paths:
  - **CABRI Budget Information Archive** — `cabri-sbo.org/uploads/bia/<Country>_<year>_<stage>_…pdf`.
    Gave **Lei n.º 18/24 (OGE 2025), 671 pp, 68.1 MB**, and previously the OGE 2025 Fundamentação.
    The country profile (`/en/countries/angola`) is the index; **for Angola it holds 2025 only** — no
    2024 or 2026. Try CABRI **first** for any African enacted budget before fighting a ministry CMS.
  - **Development Workshop Angola** — `dw.angonet.org/wp-content/uploads/<YYYYMMDD>-Lei-…pdf`. Gave
    **Lei n.º 15/23 (OGE 2024), 94.5 MB** as a gazette scan. A civil-society document library is a
    live route for Angolan gazette PDFs.
- **Both enacted volumes are scanned — no text layer at all.** `pdftotext` returns form-feeds only
  across sampled pages. The budget tables are legible to a reader and useless to the current
  toolchain (`pdftotext`, no `pdfplumber`, no OCR). **Extraction of Angolan enacted budgets needs an
  OCR step that does not yet exist**; acquiring the document is no longer the bottleneck.
  Contrast the Fundamentação reports and quarterly execution reports, which are **native PDFs** with
  clean text — which is why the narrative side of Angola is well covered and the tabular side is not.
- **Naming correction:** the OGE 2026 appropriation act is **Lei n.º 14/25** (aprovada 15-Dez-2025,
  Kz 33 240 843 683 427,00). The string "Lei 01/V/4.ª/2026-2027" recorded by the AGO 2026 sweep is
  the **Assembly's *diário* reference** (DIÁRIO II SÉRIE N.º 01-V-4.ª-2025-2026), not a law number.
  Angolan budget laws run `15/23` → `18/24` → `14/25`; take the number from angolex/lex.ao, not from
  the parliamentary diário filename.
- **Still closed after one attempt:** `compraspublicas.minfin.gov.ao` (the PAC portal) times out —
  no Angolan Plano Anual de Contratação is held for any year; and the minfin CMS exposes the 2025
  quarterly execution reports by UUID but **no anexos volume and no 2026 series at all**.

### Burundi — the whole chain is a scan, and the digital line is donor-side (sweep, 2026-07-23)

- **Fiscal year is July–June**; documents label it `2024/2025`. Programme budget since the
  **loi organique n°1/20 du 20 juin 2022**: credits are voted by *programme* (≈5 per ministry,
  one transversal) or, for Présidence/Primature/Ombudsman, by simple *dotation*.
- **`finances.gov.bi` is a clean WordPress document library behind the same local-DNS wall as
  Kenya, Senegal and Angola.** DoH (`cloudflare-dns.com/dns-query`) → **41.79.224.90**, then
  `curl --resolve finances.gov.bi:443:41.79.224.90`. Categories `/index.php/category/lois/`,
  `/index.php/budget/`, `/index.php/ptba/`; each post carries exactly one
  `wp-content/uploads/YYYY/MM/<Name>.pdf` link. One category fetch = the whole per-year chain.
- **The estimates volume is called the PTBA** (*Plan de Travail et Budget Annuel*), published as
  *"Ventilation des dépenses par programme ou dotation sur les ressources nationales"*. It is
  the per-programme volume and the only route to a cross-vote scan — **but it covers domestic
  resources only** (*sur les ressources nationales*), so donor-financed digital spend is out of
  it by construction. An initial and a *modifié* volume are published per year, the second after
  the loi de finances rectificative; they are **differently produced scans** (265 MB vs 44 MB at
  more page objects) — do not assume shared layout or scale.
- **OCR is a hard precondition for Burundi.** Of nine FY2024/25 documents captured, only the
  **Exposé des motifs** (12 pp) and the two **ministry procurement plans** are native PDFs. The
  appropriation act (462 MB), the rectificative (246 MB), both PTBA volumes, the FSU plan and
  the Cour des comptes RPGA are image-only — `pdftotext` returns a few hundred bytes across
  hundreds of pages. Same wall as the enacted Angolan OGE volumes, but here it covers the
  *entire* chain rather than just the gazette scans.
- **Verify every large fetch against `Content-Length`.** The first PTBA download silently
  truncated at 41.5 MB of 265.4 MB and still began `%PDF` — size-check, don't magic-byte-check.
- **The procurement portal is the richest fisc-side seam, and it is the Angola-PAC analogue.**
  `armp.bi` 403s to curl ("This website has been deactivated"); the live host is
  **`armp.gov.bi`**. Its *Plan de Passation des Marchés <FY>* section paginates over 8 pages of
  `/archives/<id>` posts, one per spending unit, each linking one PDF. The ministry plans are
  **native text**, give **Budget prévu in full BIF units**, name the **Source de financement**
  (`Budget de l'Etat` vs project), and — the key — section themselves under a **LITERA budget
  classification string**, e.g. `LITERA: 11 00 002 00 4 21450 11 000 0311 01`. *That string is
  the join key from a procurement line back to a PTBA programme.* Capture it with every line.
  Successive revisions of the same year's plan are published (`révisé 3`, `révisé 6`); take the
  highest.
- **What the fisc actually buys (FY2024/25):** MININTER — *logiciel de biométrie pour la gestion
  de carrière* 791 990 000 BIF, *matériel et équipements informatiques* for the **Commissariat
  Général Migrations** 721 245 000, police network training 50 169 500. MFBPE — ordinateurs
  489 500 000, *maintenance du réseau informatique* 356 506 000, équipements informatiques
  226 200 000, entretien/réparation 435 884 000 (**gré à gré**). All `Budget de l'Etat`.
  Hardware and maintenance, not systems.
- **The systems are donor money and they are not in the budget documents at all.** PAFEN
  (World Bank P176396, IDA US$50m + US$42m AF) carries the IFMIS **SIGFP_BI** (~US$30m), the
  tax platform **e-KORI**, the e-government strategy, the identity diagnostic and the SETIC
  site — procured on `pafen.gov.bi`, not through ARMP. A BDI domestic-state total that does not
  state this reads as near-zero digital spending. **The CNI biométrique crosses to the fisc only
  in FY2026/27** (16 milliards BIF in the budget bill; ~15 mds stated as whole-project cost).
- **Own-source:** the **Fonds de Service Universel des TIC** (décret n°100/186 du 16 octobre
  2017, restructured by **décret n°100/054 du 29 mars 2024** — own directorate, `fsu.gov.bi`)
  levies **1% of operators' turnover**. Its FY2024/25 procurement plan is on ARMP but is a scan.
  Watch the origin phrasing: an FSU tender states *« financé à 100% Par le Fonds de Service
  Universel sur le budget général de l'exercice 2024-2025 »* — own-source fund, *sur le budget
  général*, in one sentence.
- **Audit: the fiscal-year instrument is the PLR, and it has stopped.** Cour des comptes
  publishes `courdescomptes.bi/assets/images/PLR<YYYY>_<YYYY>.pdf` (report on the projet de loi
  de règlement). The series ends at **PLR2022_2023**; PLR2023_2024 and PLR2024_2025 both 404 as
  at 2026-07-23 — so Parliament adopted the FY2024/25 règlement law with no published audit of
  it. The **RPGA** (`rpga<YYYY>.pdf`, latest rpga2024) is a *calendar-labelled* annual report
  against a July–June fisc: never assume which fiscal year an RPGA edition covers.
- **Reporting route (ingest, 2026-07-24).** Of the FY2024/25 *reporting* sources swept, the
  **loi de règlement** as reported (Le Renouveau, 13 May 2026) gives **whole-budget aggregates
  only** — resources realised 3 234bn BIF = **76.79%** of the 4 211bn revised target — with **no
  per-ministry or per-programme actuals**, so it cannot settle any digital line's execution; the
  **PTBA S2 implementation report** (7 Oct 2025) establishes crédits were **moved between
  programmes at will** (2.7% overrun), qualifying any appropriated-vs-actual comparison. The **only
  recordable digital line from this batch** was the **FY2026/27 CNI 16bn BIF** from the minister's
  11 Jun 2026 statement (`proposed`, `official-statement`) — every FY2024/25 budget figure either
  failed scope (ministry envelope, e.g. MINCOTIM 131.7bn) or was a whole-budget aggregate.
- **Searched, found nothing:** a data protection authority budget line (the law is **Loi n°1/03
  du 10 mars 2026** — no DPA existed in FY2024/25, and no supervisory authority is publicly
  identified even now); any national CSIRT/cybersecurity agency appropriation; a MINCOTIM
  FY2024/25 procurement plan (absent from ARMP though other ministries' are there); the PAP /
  DPBEP / PIP / CDMT instrument set named in the exposé des motifs.
- **Trap:** `arct.bi` does not resolve — the regulator is `arct.gov.bi`, and its annual-report
  series stops at 2021-2022.

### Burundi — FY2025/26: the execution side goes machine-readable (sweep, 2026-07-24)

- **Law chain established (via Exa, not the scans):** appropriation act **Loi n°1/12 du 24 juin
  2025**; rectificative **Loi n°1/09 du 31 décembre 2025** (modifying 1/12), adopted Assembly
  24 Dec / Senate 27 Dec 2025. Numbers came from the finances.gov.bi post title and the **OBR
  `lois et règlements` page** (`obr.bi/index.php/en/lois-et-reglements`) — a second Burundi
  budget-law index worth grepping, and it also lists a *Tableau des dispositions révisées de la
  Loi des Finances 2025-2026 Modifiée* (a summary table, likely native — not yet fetched).
- **The scanned volumes shrank but are still image-only.** Loi 14.9 MB/~214 pp, PTBA 53 MB/~437
  pp, modifiée 40 MB/249 pp — vs FY2024/25's 462/265/246 MB. `pdftotext` returns 200–450 bytes
  each. Lower DPI, no text layer: **OCR still required for the appropriation act and PTBA.**
- **NEW and high-value: the T3 canevas execution reports are native XLSX.** finances.gov.bi
  publishes, per institution, `CANEVAS-RAPPORT_<INST>_2025-2026_T3.xlsx` (found via `?s=canevas`;
  ~24 institutions, dated 2026-07-04). Each is a 64-column programme→action→**PAP activity**
  spreadsheet carrying `BUDGET ANNUEL REVISE`, quarterly revised budgets, and
  `ENG BUDGETAIRE / ENG JURIDIQUE / LIQUIDATION / ORDONNANCEMENT / PAIEMENT / DECAISSEMENT` at T3
  with `Taux de liquidation` / `Taux de réalisation physique`, plus a LITERA-equivalent
  `CODE NOMENCLATURE`. This is **the first machine-readable BDI budget artefact** — it yields a
  cross-vote *revised + in-year-executed* scan with no OCR, and **substitutes for the missing
  standalone PTBA modifié** (revised figures are the `BUDGET ANNUEL REVISE` column). The blank
  `canevas-annuel-<inst>` posts (dated 2025-07-02) are the *template* versions; the filled reports
  are the `canevas-rapport_…_t3` posts.
- **Ministry acronyms churn between the annual templates and the T3 reports** (June-2025 reshuffle):
  the économie-numérique portfolio sits with **MFBEN** (finance); ICT/télécoms/médias with **MCM**
  (Ministère de la Communication et des Médias) which carries "PRG01: Programme de digitalisation
  de l'administration publique"; identity/état-civil/migrations with **MIDCSP** (interior). Decode
  each acronym from the sheet's `INTITULE MINISTERE/INSTITUTION` cell — do NOT guess (MRMEICT
  looked digital but is Mines/Énergie/Industrie/Commerce/Tourisme).
- **Digital lines found under (native XLSX):** MFBEN — Programme de digitalisation des services
  publics, comité de pilotage/technique de la digitalisation, 40 licences sécurité des données,
  serveur d'archivage/gestion des données SPP. MIDCSP — logiciel permis de conduire, logiciel de
  digitalisation, **30 communes digitalisées en recettes communales**, sites CGM internet IP
  dédié. MCM — the PRG01 digitalisation programme. SETIC (PPM) — équipements de sécurité
  218,100,000 BIF and fibre/bande passante IP 213,033,569 BIF on BGE 2025-2026.
- **armp FY2025/26:** listing at `/passation-des-marches-2025-2026/` (18 pages, `/archives/<id>`
  per unit); MFBEN reaches **Révisé 6**, FSU has two revisés (take `/8946`), and **SETIC** files a
  plan (the e-gov body, not in the T3 ministry set). Native text + LITERA throughout.
- **Searched, found nothing / nil:** no exposé des motifs 2025-2026 (the one readable narrative —
  unpublished this year → acquisition); no standalone PTBA modifié 2025-2026 → acquisition; no
  audit (PLR series ends FY2022/23, structurally absent). Donor systems (SIGFP_BI, e-KORI) remain
  off-budget via PAFEN — the ressources-nationales PTBA understates digital by construction.

### Burundi — FY2026/27: the PTBA lags the law, but the strategy layer finally surfaces (sweep, 2026-07-24)

- **Appropriation act = Loi n°1/10 du 30 juin 2026** (promulgated 30 Jun, posted to finances.gov.bi
  4 Jul, in force 1 Jul 2026; adopted unanimously by the Assemblée Nationale 13 Jun, minister
  **Dr Alain Ndikumana**). Reported aggregates: **dépenses ~7 020 mds BIF / recettes 6 296,03 mds BIF,
  +23,76 %** vs FY2025/26's 5 352 mds — a large nominal jump. The enacted PDF is **9.9 MB / ~267 pp**
  (vs FY2024/25's 462 MB): **law + summary annexes only, still image-only** — OCR precondition holds.
- **The PTBA 2026-2027 estimates volume is NOT yet published** (only the blank template
  `FORMAT-DES-PTBA-SPP-2026-2027.xlsx`). So for the first time in the BDI series a sweep landed the law
  **without** the per-programme volume — the run supports **sector-vote coverage only** until the PTBA
  posts (FY2025/26's came 2 Jul 2025, so expect it within days–weeks). Queued to acquisitions.
- **The DPBEP/CDMT strategy layer, a standing FY2024/25 absence, is now on the portal** — and the
  **DPBEP 2025-2028 is native .docx** (first machine-readable BDI fiscal-planning doc). It is the
  *projet* (v.25-Jan-2025), lead year FY2025/26, programming FY2026/27–2027/28 as **indicative outer
  years** (MTEF rule: not appropriations). The **lettre de cadrage budgétaire 2026-2027** (sector-ceiling
  circular, image-only, ~20 pp) sits with it. A **CDMT sectoriel 2026-2027 / mesures nouvelles** post
  exists but exposes no attachment.
- **The finance ministry is now "Ministère des Finances, du Budget et de l'Économie Numérique"** —
  numérique folded into finance (canonical entity slug already
  `ministere-des-finances-du-budget-et-de-leconomie-numerique-burundi`).
- **finances.gov.bi went post-based:** links are `/index.php/YYYY/MM/DD/<slug>/` now, not clean category
  archives; `?s=2026-2027` / `?s=ventilation` / `?s=expose` are the reliable finders. Still DoH→41.79.224.90.
- **ARMP FY2026/27 opened the week of 2026-07-18** at `/plan-de-passation-des-marches-2026-2027` (no
  trailing slash — the `/passation-des-marches-…` form 404s). ~10 units posted so far; **FSU révisé** is
  the only digital-relevant one (native, own-source, `Source: FSU`) and its FY2026/27 plan is **pure
  connectivity/DPI-access**: IP-transit internet to 25 pilot health structures / 25 secondary schools /
  télécentres communautaires polyvalents (equip + LAN), 41 tablets — lines `3.750.000.000`,
  2×`1.250.000.000`, `1.244.133.380`, `143.500.000` Fbu. The digital **ministry** PPMs (MFBEN, SETIC,
  MIDCSP, MCM) are **not yet posted** — re-run trigger ~August.
- **Cour des comptes scrutiny of the FY2026/27 budget is on the record** (Léonidas Kabura to the Senate,
  17 Jun 2026, via Burundi Eco): debt-transparency gaps — ~80 mds BIF flagged for repayment but the
  residual stock left unstated — a soutenabilité concern. This is *scrutiny of the appropriation*, not
  the missing audit (PLR series still ends FY2022/23; structurally absent).
- **Searched, found nothing / not-yet-due:** PTBA 2026-2027 (unpublished → acquisition); exposé des motifs
  2026-2027 (unpublished → acquisition); any FY2026/27 rectificative/execution/audit (not yet due). CNI
  biométrique **16 mds BIF** fisc line already held in `raw/` (min. statement, 11 Jun 2026). Donor systems
  remain off-budget via PAFEN.

### Burundi — first budget-extract of the FY2024/25–2026/27 chain (extract, 2026-07-24)

First budget-extract run over the 25 staged BDI documents. **11 domestic-state digital records built**;
**13 documents OCR-archived** (image-only, no text layer — the two appropriation acts and two rectificatives,
both PTBA volumes, the PTBA modifié, the 2024/25 FSU plan, the RPGA audit, the FY2026/27 loi and lettre de
cadrage). Records came from the **native-text procurement plans** and the **native XLSX T3 execution canevas**
(new Archetypes J and I in the strategy library).

- **The digital lines actually recorded:** MFBEN e-facturation (machines à facturation électronique)
  **17.2bn BIF** (FY2025/26 revised — the largest BDI digital line by far); MFBEN interconnexion-ministères
  824.6m, data-security licences 545.3m, système biométrique de gestion 185.8m, serveur d'archivage 90.5m;
  **SETIC** whole operating appropriation **1.17bn** (single-mandate carve-out); MIDCSP secure-document-production
  software **2.5bn**, digitalisation des recettes communales **2.0bn**, logiciel permis de conduire 120.1m;
  MININTER FY2024/25 logiciel de biométrie 792.0m; FSU (own-source) Villages Numériques **4.81bn** (FY2025/26)
  and institution-connectivity **11.4bn** (FY2026/27).
- **The envelope-mislabel trap (important):** Burundi names an entire ministry's budget
  `PRG01: Programme de digitalisation de l'administration publique`. MCM (communication/media) sits wholly under
  it, yet is running the national radio, the newspaper and media coverage — **not** digital transformation.
  Never scope by the programme-prioritaire label; scope by the tâche text. MCM yielded **no clean record**;
  CENI none (the electronic voter register is not in its canevas).
- **Execution columns empty:** the T3 canevas were filed with `LIQUIDATION`/`PAIEMENT`/`DECAISSEMENT` blank, so
  every canevas record is `revised`-stage only — no execution rate established for FY2025/26.
- **No case-5 reset possible:** the held CNI biométrique record (16bn, FY2026/27, `official-statement`) would be
  reset by the FY2026/27 appropriation act, but that act (Loi n°1/10) is **image-only/OCR-blocked**.
- **Scope calls (logged):** generic office IT hardware (ordinateurs 489.5m, matériel informatique 226.2m,
  network-maintenance equipment 356.5m in the MFBEN 2024/25 PPM; CGM IT equipment 721.2m in MININTER) recorded
  as **operational overhead, not digital-activity lines**. Software/systems/digitalisation/connectivity/biometric
  lines recorded; hardware excluded.
- **Double-count avoided:** for FY2025/26, the ministry PPMs (MFBEN révisé 6, MININTER MICSP, SETIC) are the same
  money as the canevas programme lines — recorded from the canevas, PPMs kept as procurement/vendor detail. The
  **FSU** procurement is own-source (levy, 1% operator turnover) and does **not** overlap the state canevas, so it
  is recorded separately. New entity minted: `fonds-service-universel-tic-burundi`.
- **Governance bodies looked for, not found (fiscal side):** no data-protection-authority budget line
  (DPA law Loi n°1/03 du 10 mars 2026; no funded supervisory authority yet), no national CSIRT appropriation,
  no ARCT own-budget in the machine-readable set.

### Angola — first budget-extract of the FY2024/FY2025/FY2026 documents (extract, 2026-07-24)

**Zero records.** The **Fundamentação** reports (native text, 68–206kB text layer) carry only the functional/sector
envelope — "Comunicações e Tecnologias da Informação" appears as a functional share (e.g. 1.4% / 31.4, 0.0%
execution), which the envelope rule bars from recording. The **enacted OGE volumes (Lei n.º 15/23, 18/24)** are
**image-only** (496 / 671 bytes of text over the whole volume) → OCR-archived. The **IV-Trimestre execution reports**
are narrative outturn; the per-project ANEXO 13/16 digital lines are in a separate anexos volume (not held). So no
programme/project digital line is machine-readable, and **no case-5 reset** of the held pti.ao-sourced AGO programme
records is possible until the Mapas or an OCR step lands. (Note: the FY2024 IV-Trimestre report's internal
"~24% annual" execution figures read like a Q1, not a full year — a possible companion mislabel, flagged; it drove
no record.)

### Benin — the state publishes a budget API, and it is the estimates volume (sweep, 2026-07-25)

- **Fiscal year:** calendar (Jan–Dec); "2024" = gestion 2024. Documents label it *gestion 2024*.
- **The Tableau A credit annex is not published.** Articles 35–37 of the loi de finances open credits
  "comme indiqué dans le tableau A annexé à la présente loi", but the annex bound into every copy located
  (`api.impots.bj` mirror, tresorbenin.bj, documentation-anbenin.org, budgetbenin.bj) is the
  *dispositions modificatives du Code général des impôts*. The only per-ministry table in the law is the
  **ETPT staff-ceiling table** (Art. 43). Don't keep hunting for a per-ministry credit PDF — there isn't one.
- **Instead: `backdata.budgetbenin.bj/public/api` is the DGB's own open-data back end, and it carries the
  whole estimates volume natively.** `opendata.budgetbenin.bj` is an Angular SPA; the API base sits in the
  main JS bundle. Routes: `/agregats` (list, 113 aggregates across 3 menus) and `/agregats/{slug}` (detail —
  `institutions`, `categories`, `headers`, `expenses`). No auth; 52 calls ran clean.
  **Row shape:** `{annee, institution_id, agregat_id, category_id, code, dotation_initiale,
  dotation_finale, engage, ordonance}`. **The four value columns are four budget stages** —
  appropriated / revised / committed / ordonnancé — which is the cleanest stage mapping in the corpus.
  `institution_id` resolves to a **ministry** in *Classification administrative* (excel 9) and to a
  **budget programme** in *Classification programatique* (excel 2). **Scale: million FCFA**, declared per
  dataset as `amount_unit`. FY2024: 33 institutions, 80 programmes.
- **Trap: 2024 has `dotation_initiale` only.** The execution columns are populated for 2022 but null for
  2024 — the portal lags. So the API gives appropriated at full grain and nothing else; don't read a null
  `ordonance` as zero execution.
- **Trap: the classification totals don't equal the budget.** FY2024 administrative rows sum to 1,872,283 M
  and programmatic to 1,914,681 M against the law's budget général of **2,428,200 M** — debt service, CAS
  and FNRB appear to sit outside the classification tables. Per-line figures cross-check exactly;
  aggregates do not. Reconcile before totalling.
- **Two checks that validated the extract** (worth repeating on any API-sourced budget): programmes 111 +
  100 + 109 = 24,356.6 M = institution 28 (M.N.D) 24,356.5 M; and APDP 488.3 M matches the **488,277,000
  FCFA** printed in the Assembly's own special report. Both passed, so `dotation_initiale` is the enacted
  LFI figure.
- **Digital lines found under:** programme **111 *Numérique*** (12,701.4 M, MND); **044 *Modernisation de
  l'administration publique*** (~~10,205.4 M~~ → **1,910.0 M**, MTFP) and the ring-fenced CAS
  **108 *Modernisation des régies financières*** (6,000.0 M, a standing line in both LF 2023 and LF 2024,
  i.e. tax/customs systems funded outside the ordinary votes). Plus **020 *Services Judiciaires***
  23,723.3 M (a multi-purpose envelope, not recorded).
  **⚠ Corrected 2026-07-25.** This entry originally read *"those two alone are 16.2 bn against the
  sector programme's 12.7 bn"*, on the API's 044 figure. **That figure is a portal error** — the MTFP's
  own PAP and its own account of its budget defence both put programme 044 at 1 910 016 619 FCFA and
  the whole ministry at 7 682 736 688 FCFA. **The correct comparison is 7,910.0 M against 12,701.4 M**:
  the cross-vote lines are worth about **62%** of the sector programme, not 128% of it. See
  the reconcile pass of 2026-07-25 (brief deleted on closure; see `logs/log.md` and git).
- **Block 4c is the good case here: the APDP is its own budget institution** (administrative code 7), not a
  line inside a ministry programme — so the data-protection authority's whole appropriation is visible
  three ways over (API, Assembly special report, press). **488.3 M in 2024, down 11.6 % from 552.4 M in
  2023**, then +30.7 % to 638.3 M in 2025 *on a parliamentary recommendation from the 2023 budget debates*.
  Single-mandate carve-out applies.
- **Programme codes are NOT stable across years** (same as Kenya): 2022–2023 carry *Digitalisation de
  l'Administration, des entreprises et de la société*; 2024 carries **111 *Numérique*** instead. Any series
  on programme code or name needs a mapping row at this restructure.
- **The MND's headline 21.6 % fall (31,075,081 → 24,356,549 thousand FCFA) is an external-loan line
  collapsing** — financement extérieur (emprunts) 10,700,000 → 3,656,448 (−65.8 %) while financement
  intérieur *rose*. A "Benin cut its digital budget" reading is wrong on the fisc side; the origin gate
  must catch this.
- **Track B routes.** `budgetbenin.bj` (DGB) is WordPress: the library is **category 7 "publications"
  (218 posts)**, enumerable via `wp-json/wp/v2/posts?categories=7&per_page=100`; attachments under
  `/storage/YYYY/MM/` and `/wp-content/uploads/YYYY/MM/` (aliases). **Search the media library, not just
  the posts** — the annual outturn `RAPPORT-D-EXECUTION-au-31-12-2024-Final.pdf` exists only in
  `wp-json/wp/v2/media?search=`; the corresponding post carries only the *version citoyenne*. Same trick on
  `assemblee-nationale.bj` surfaces the per-ministry **rapports spéciaux** and the commission reports on the
  RAPEX. `api.impots.bj/media/` carries the enacted loi de finances when the finance ministry's site does not.
- **The per-vote parliamentary "rapports spéciaux" are Benin's ENE-chapter equivalent** and they are
  **native text**: a synoptic credit table (2023 vs 2024, thousand FCFA) plus **per-project `crédit ouvert`
  with physical and financial execution rates**. The MND one names six projects (internet haut débit ph.2
  8,412,600,000 ; usages et confiance numérique 1,500,000,000 ; SMART GOUV ph.2 1,500,000,000 ;
  transformation numérique des collectivités locales 4,379,048,000 ; TNT 5,800,000,000 ; modernisation des
  médias 500,000,000 — all *source de financement: Intérieure (Budget National)*). **Caution: those are
  prior-year credits reported as the comparator, not the run year's appropriations.** Mixed scale — francs
  in the narrative, thousands in the tables; check every header.
- **Outturn available?** Yes, and unusually: **a four-point quarterly RAPEX series** (31 mars / 30 juin /
  30 sept / 31 déc) plus the Assembly's commission reports on Q1 and H1. **Audited:** loi n° 2026-06 du
  21 mai 2026 settles gestion 2024 and the Cour des comptes certified the compte bilan — but neither the
  law's text nor the RELF 2024 is published (`courdescomptes.bj/rapports` lists only two items ever; ids
  98–99 return 500, 100+ return 404). Lois de règlement post to `budgetbenin.bj/reddition-de-comptes/` with
  a ~2-month lag, so expect it soon.
- **The constraint is OCR, not availability — the mirror image of Burundi.** Native text: the API, the six
  FY2024 rapports spéciaux, the rapport de présentation, both DPBEP volumes, the ARCEP annual report.
  Scanned with dirty OCR: **the loi de finances itself** (`TIVRE` for `LIVRE`, `l` for `1`, columns
  transposed) **and all four RAPEX volumes** — the per-ministry line `015. MINISTÈRE DU NUMÉRIQUE ET DE LA
  DIGITALISATION` is legible as a label but its digits are not. Image-only: the four
  assemblee-nationale.bj PDFs. So *appropriated* is machine-readable and *executed* is OCR-blocked.
- **Block 6:** ARCEP is funded from redevances under the Code du numérique (art. 133 mandates the annual
  report) and never appears in the loi de finances. 2024 own resources **6,520,742,720 FCFA**; separately it
  **mobilised 66,129,397,493 FCFA for the State** — that second figure is **revenue, not spend**. Figures are
  written out in words, so there is no scale header and no 1,000× trap.
- **Didn't work / searched and not found:** `marches-publics.bj/plan-de-passation` renders "0 Plans de
  passation" (the national procurement portal is empty — Benin has no fetchable PAC equivalent to Angola's);
  `budget.bj` does not resolve; `budgetbenin.bj/reddition-de-comptes/` is Elementor-rendered and its document
  links are absent from the static HTML; **Rapports Annuels de Performance gestion 2024** are required by the
  LOLF and promised in the LF 2024 rapport de présentation but are not in the 218-post library — they are the
  only route to per-programme *executed* figures and remain the standing gap.

### Benin — FY2025: the API stops, an XLSX annexe takes over (sweep, 2026-07-25)

- **The DGB open-data API stops at 2024 for vote grain.** Verified live, not inferred:
  `/agregats/{slug}` for excel 9 (*Classification administrative*) returns 2008–2024 and excel 2
  (*Classification programatique*) returns 2022–2024. Only excel 12 (*fonctionnelle*, 60 rows) and
  excel 13 (FADeC) carry 2025. **So the FY2024 headline artefact does not repeat** — do not plan a
  BEN 2025+ run around the API. Two datasets the FY2024 run never captured are macro series, not
  vote grain, and are not worth staging: excel 5 *Indicateurs économiques* (to 2024) and excel 14
  *Données financières* (**stops at 2014**).
- **Instead, the estimates volume is an annual native XLSX:** *Tableaux de classifications croisées
  des dépenses de l'État sur la période pluriannuelle, budget LF NNNN*, posted to the DGB media
  library each January. Sheet `Classif Prog-Admin-Eco`: ministry / programme / dotation rows ×
  6 years × 9 economic columns, **thousand FCFA** (declared in row 3). Year blocks begin at cols 3,
  12, 21, 30, 39, 48; within a block: personnel, acquisitions b&s, transfert, TOTAL ORDINAIRES,
  capital ressources intérieures, capital ext-dons, capital ext-prêts, TOTAL CAPITAL, TOTAL
  PRÉVISIONS. **This is the better artefact**: it reconciles to the enacted `TOTAL BUDGET DE
  L'ETAT` (2,778,519,000 kFCFA in 2025; 2,551,700,000 in 2024, residual a constant 1,200,000) and
  it carries the ordinary/capital and interior/exterior split per programme, which the origin gate
  needs. **The 2023-2028 / PLF 2026 edition is already posted (2025-12-03) — make it the first
  target of the BEN 2026 run.**
- **This resolves the FY2024 note's open caveat.** The API totals could not be reconciled to "the
  law's budget général of 2,428,200 M" because *budget général* ≠ *budget de l'État*: the full 2024
  total is **2,551,700,000 kFCFA**, matching the appropriated figure in the settlement-law reporting
  already held.
- **⚠ The API's programme 044 figure is disputed, and an FY2024 headline depends on it.** The
  workbook and the API agree exactly on **69 of 80** FY2024 programme codes, but give
  **044 *Modernisation de l'administration publique*** as 10,205.4 M (API) against 1,910.0 M
  (workbook). The workbook's MTFP programmes sum exactly to its ministry total (7,682.737 M); the
  API's do not — and **the API's own administrative classification puts M.T.F.P at 7,682.7 M**,
  siding with the workbook against itself. If the workbook is right, the FY2024 note's
  *"16.2 bn outside the sector vote … understates by more than half"* becomes **7,910.0 M against
  12,701.4 M** and the conclusion reverses. **Do not quote the 16.2 bn figure** until
  `reviews/contradictions/open/2026-07-25-ben-programme-044-modernisation-administration-2024.md`
  is settled.
- **⚠ The API's economic labels are not reliable.** For programme 111 both sources carry the *same
  six numbers under different labels* — the API books 6,530.725 as *Dépenses de transfert* where
  the workbook books it as capital *Ressources intérieures*, and permutes dons against emprunts.
  Totals agree, the split does not. Cross-check any API-derived economic classification.
- **The FY2025 RAPEX volumes look native and are not.** They extract as text, but it is a **dirty
  OCR layer over a scan** — `corrmerce`, `ministàes`, `l'EtaQ`, and on the per-ministry table
  `:9ltt 49? {t6`. Labels legible, **digits not**. Judge these files by character quality, not by
  extract length. Conversely the **enacted loi de finances 2025 is fully image-only** (0 chars),
  worse than the FY2024 law.
- **New: the revised stage exists for FY2025.** p.59 of the RAPEX au 31-12-2025 carries *SYNTHÈSE
  DES MOUVEMENTS DE CRÉDITS PAR MINISTÈRE (HORS CRÉDITS GLOBAUX - CST - FNRB)* — Dotation Initiale /
  Crédit Annulé / Crédit Complémentaire / Dotation Finale, in AE and CP, per ministry. FY2024 had
  no revised stage at all. **OCR on this one page is now the highest-value unblock for Benin.**
- **Origin gate, and it inverts year on year.** FY2024's MND fall was an external-loan line
  collapsing; FY2025's 19.2% rise is that line returning while the domestic side goes backwards.
  Programme 111 *Numérique*: ext-prêts 3,656,448 → 10,042,000 kFCFA, ext-dons 2,388,571 → 0,
  ressources intérieures 6,530,725 → 6,236,213. **Domestically-financed Numérique falls 4.1%
  (6,656,403 → 6,386,858) while the headline rises 29.3%.** Both directions of this trap have now
  been seen in consecutive Benin years — treat the MND headline as untrustworthy without the split.
- **Retired programme codes stay in the table at zero.** 066 *Sécurité Numérique*, 104
  *Digitalisation de l'Administration* and 106 *Infrastructure et Usages Numériques* are carried at
  zero in both 2024 and 2025. Combined with the 2024 restructure already noted, any series on
  programme code needs explicit handling.
- **The APDP moved classification without moving substance.** Administrative *institution* 7 in
  FY2024; **dotation 014** in the LF 2025 workbook, grouped with the Assembly, the courts and the
  Présidence. Still a single-mandate body, still fully visible: **638,277 kFCFA, +30.7%**, of which
  **40 M FCFA** for intrusion-testing and compliance tooling. The rise traces to a parliamentary
  recommendation from the **2023** budget debates — a three-year lag from legislative ask to
  appropriation.
- **Block 6: ARCEP's own resources fell 26.9%** — 4,768,581,763 FCFA in 2025 against 6,520,742,720
  in 2024. Figures are written out in words, so still no scale header and no 1,000× trap. The
  "mobilisé pour le compte de l'État" figure remains **revenue, not spend**.
- **Track B, updated.** *Search the media library, not just the posts* is now proven twice — the
  Q3 FY2025 RAPEX, the enacted LF 2025 and the cross-classification XLSX are all media-only. But
  the endpoint is **flaky**: `wp-json/wp/v2/media?search=` 500s on `RAPEX`, `reglement`, `tableau`,
  `numerique`, `decryptage` while working on `gestion 2025`, `budget 2025`, `RAPEX 2025` — vary the
  term before concluding absence. On `assemblee-nationale.bj`, the *rapports spéciaux* URLs contain
  a raw U+2019 and a dropped apostrophe (`Ministère-de-lIntérieur-…`); percent-encode the path from
  the API's own `source_url` rather than reconstructing it.
- **Procurement: the FY2024 `[blocked]` verdict was too strong.** ANIP's own avis state its PPM was
  "publié sur le portail web des marchés publics le 05 Mars 2025" and "révisé … le 19 Septembre
  2025" — **the plans exist and are dated**; `marches-publics.bj/plan-de-passation` merely renders
  empty. And **décret n° 2025-169 du 9 avril 2025** retires SIGMaP and that portal for a new
  e-Procurement platform (3.3 bn FCFA, World Bank PGEDS-financed; first tender declared
  *infructueux* 16-09-2025), so the durable route will be the successor system.
- **Audited cadence, now measurable:** gestion 2023 settled by **loi n° 2025-21 du 8 décembre
  2025**; gestion 2024 by **loi n° 2026-06 du 21 mai 2026**. Neither the 2024 law's text nor any
  RELF after 2023 is published — `courdescomptes.bj/rapports` server-renders two headings
  (*RESUME FINAL DU RELF 2023*, *PLAN STRATÉGIQUE 2025-2027*) and **zero PDF links**. So FY2025's
  audit is **not yet due**, and that is the correct thing to state on the page.
- **Proposed vs enacted is worth checking at Benin, and cheaply.** The MND's enacted split moves
  **166,586,000 FCFA** from *Pilotage* (2,568,303 → 2,401,717 k) to *Médias* (10,036,805 →
  10,203,391 k); ministry total and programme *Numérique* unchanged. Press reports the **proposed**
  figures. Cite the workbook for the appropriation.

### Benin — FY2026: the state publishes more, and the ministry is split mid-year (sweep, 2026-07-25)

- **The estimates volume route held.** *Tableaux de classifications croisées … 2022-2028, budget
  LF 2026* (posted 2026-02-06) is the annual native XLSX the FY2025 note predicted. Sheet
  `Classif Prog-Admin-Eco`, 152 x 64, **thousand FCFA** (row 3), year blocks at cols
  **3/11/20/29/38/47/56**. It reconciles **exactly**: programmes 2,256,226,468 + dotations
  808,906,242 = TOTAL BUDGET DE L'ETAT 3,065,132,710 kFCFA, with **no residual** (2024 and 2025
  both carried a constant 1,200,000). **Proposed = enacted this year**: the PLF-stage edition
  (2023-2028, 2025-12-03) gives the same 2026 total to within 1 kFCFA.
- **The FY2024 note's "there is no Tableau A" is wrong from LF 2025 onward.** `Tableau-A-Annexe-
  LF-2025.pdf` (2024-12-30), `Tableau-A-Annexe-PLF-2025-VF01-10-24.pdf` (2024-10-02),
  `TABLEAU-A-Annexe-LF-2026.pdf` and `TABLEAU-A-Annexe-PLFR2026.pdf` all exist and are **native
  text, one page each**: per section, prior year against current, split personnel / acquisitions /
  transfert / TOTAL ORDINAIRES / financement intérieur / extérieur (dons) / extérieur (emprunts) /
  TOTAL CAPITAL / TOTAL / Poids / Variation. The FY2024 statement stands only for gestion 2024.
- **⚠ Section codes and dotation codes disagree.** The APDP is **section 010** in Tableau A but
  **dotation 014** in the workbook and the PLFR dotation list; the Senate is **section 044** in
  Tableau A and **dotation 128** in the list. Cross-walk before keying a series on either.
- **The single richest artefact in three Benin runs is a rectificative's explanatory note.** The
  *Note de présentation du PLFR 2026* (2026-06-09, 54 pp, native) embeds raw SIGFP output:
  **pp. 19-29** `RECAPITULATIF DES MOUVEMENTS DE CREDITS PAR MINISTERE 2026, 01/01-30/04/2026`
  (per ministry **and economic nature**, AE/CP, movement type broken out: fongibilites et
  virements / affectations et transferts / fonds de concours / credits supplementaires / credits
  annules / report de credits -> previsions finales); **pp. 31-54** `SITUATION D'EXECUTION DU
  BUDGET PAR PROGRAMME` (dotation initiale / finale / engagement / mandat ord. / OP / non
  regularise / paiement / disponible / **taux eng. % / taux ord. %**, decomposed DO/DC and by
  economic nature). **This is the per-programme executed grain the RAP series has never
  supplied.** Look for the same embed in every future PLFR note.
- **⚠ 1,000x trap in that document.** Pages 19-29 print *"(en milliers de francs CFA)"* and the
  figures are in **francs** (MND reads 27,238,035,553). Pages 31-54 are francs and unlabelled.
  Check the digits against a known line before trusting the header.
- **Execution finding: programme 111 *Numerique* had engaged 0.65% and ordonnance 0.62% of its
  credits at 30 April 2026**, against an all-programmes 19.87% / 15.43%. Its pilotage programme
  (100) executes normally at 32.62%, so this is programme-specific, not ministry paralysis.
  APDP is exactly 25.00% on both — a flat quarterly subvention, not a performance signal.
- **The machinery of government broke mid-year and the codes moved with it.** Decret n° 2026-314
  du 24 mai 2026 split the **MND** into **MTDI** (programmes 100 + 111, plus the national AI
  strategy) and **MCM** (programme 109, renamed *Communication et Medias*, plus new pilotage
  programme 065); **programme 044 moved from MTFP to a new MBFP**; the MEF split into
  MEF/MBFP/MFF/MMG. The PLFR Tableau A's **"Credits initiaux reconstitues"** column is the
  crosswalk, and the split is exact to the thousand. **CAS 108 *Modernisation des regies
  financieres* goes 6,000,000 -> 0 and vanishes from the programme list** (81 programmes; only
  CST 107 remains) — two other funds are zeroed identically, so it is a CST restructure, not a
  digital cut. Third consecutive year in which Benin's programme structure has moved.
- **⚠ The workbook's prior-year columns are restated between editions, unlabelled.** FY2024 in the
  LF 2026 edition: TOTAL 2,507,185,810 (vs 2,551,700,000 in the LF 2025 edition); MND 21,910,673
  (vs 24,356,549); prog. 111 14,464,064 (vs 12,701,422); prog. 044 1,418,740 (vs 1,910,017);
  prog. 108 3,929,400 (vs 6,000,000). FY2023 moves too. Most likely a **dotation finale**
  restatement once a year closes — 2,507.2 bn sits between 2,551.7 appropriated and 1,940.6
  executed — but **nothing prints a stage label and the API's `dotation_finale` is null
  everywhere**, so it is inference. This answers question 3 of the open programme-044 brief.
  **And the LF 2026 edition's 2022 column is simply broken** (509,916,718 against 2,242,560,838).
- **The API is dead as an execution source, confirmed live.** `dotation_finale`, `engage` and
  `ordonance` are **null for every year 2021-2024** on the administrative classification. The
  FY2024 "watch the execution columns" trigger is moot.
- **New document families on `budgetbenin.bj` for LF 2026**, none of which existed in the FY2024
  or FY2025 harvests: **Tableau A / Tableau B annexes**; **PAP** (projets annuels de performance,
  per ministry, in **PLF** and **VLF** = *version loi de finances* editions, ~16 ministries);
  **DPPD** (per-ministry three-year programming, ~20 ministries, both editions); **Programme
  d'investissement public 2026-2028** (238 pp, native, **project grain with financing source** —
  the best origin-gate artefact Benin has produced). Fetch the **VLF** edition, not the PLF one.
- **`assemblee-nationale.bj` has stopped publishing budget documents.** The per-vote *rapports
  speciaux* exist for gestion 2024 and 2025 and **not for gestion 2026**: `wp-json/wp/v2/media?
  after=2025-10-01&before=2026-02-20` returns **7 items, all JPEGs**. Verify this by date range,
  not by search term. Since 2026-02 the library is the Assembly's own procurement notices.
- **Media-search flakiness, third run, third set of failing terms.** HTTP 500 on `DPBEP`,
  `rectificative`, `REGLEMENT DEFINITIF`, `GESTION 2024`, `TABLEAU A`; clean on `LF 2026`,
  `PLF 2026`, `gestion 2026`, `RAPEX 2026`, `orientation budgetaire`, `2026-2028`,
  `Annexe LF 2025`, `TABLEAU B`. **`2026-2028` is what finally surfaced the DPBEP.** Never
  conclude absence from one 500.
- **The DGB now posts lois de reglement** — `LOI N°2025-21 … GESTION 2023` appeared 2026-02-20, a
  route that failed on both prior runs. But **loi n° 2026-06 (gestion 2024) is still not posted**
  two months after enactment.
- **OCR got worse on the execution side.** FY2024 RAPEX: scan + dirty OCR. FY2025: scan + dirty
  OCR. **FY2026 Q1 RAPEX: no text layer at all (0 characters, 78 pp).** So is the **enacted loi
  de finances 2026** (15 pp), the **PLFR bill** (17 pp) and the **decret de saisine** (13 pp).
  The **DPBEP document principal regressed** from fully native in FY2025 to near-image. What
  rescues the year is that the credits and the execution are both readable elsewhere, natively.
- **Block 4c asymmetry worth stating on the page.** The APDP is fully visible (dotation 014,
  738,277 kFCFA, +15.7%, single-mandate carve-out). **ASIN — national CSIRT, datacenter, PKI,
  convener of the Conference des RSSI — has no visible budget line anywhere in the estimates
  volume**; it is funded inside the sector vote. The data-protection authority is legible and the
  cybersecurity agency is not.
- **Block 6: no FY2026 own-source figure exists yet and that is the right answer.** ARCEP's
  annual report is mandated by art. 133 of the Code du numerique and lands each May for the prior
  year; the 2025 edition (own resources 4,768,581,763 FCFA) was published 2026-05-01 and is
  already held. The 2026 figure is due ~May 2027.
- **New cross-vote territory: the MISP.** Programme 080 *Pilotage et soutien aux services du
  MISP* goes 4,519,646 -> 16,936,716 kFCFA (**+274.7%**) on a **10,739,415 kFCFA external-loan
  capital line that did not exist in 2024 or 2025**. The budget documents never name it; the only
  public statement of purpose is press reporting of the PLFR — *"le renforcement de la securite
  interieure par la video-protection"*. Purpose sourced, amount inferred.
- **Origin gate, third year, third pattern.** Programme 111: FY2024 an external loan collapsing,
  FY2025 that loan returning while domestic money fell, **FY2026 both falling** — ext-prets
  10,042,000 -> 6,500,000 and interieures 6,236,213 -> 5,736,213 kFCFA. Domestically-financed
  *Numerique* falls **8.1%** against a **24.7%** headline. The MND headline has now misled in
  three different directions in three years; never quote it without the split.

### Benin — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-07-25)

**76 documents drained in one pass; 25 records built; the estimates volume held for all three
years.** This is the first country in the corpus where appropriation *and* execution are both
machine-readable at programme grain, and the first where the origin gate could be run on the
execution side.

- **Read the workbook, not the API, and not the law.** Three routes to Benin's estimates existed
  and only one survives contact: the enacted loi de finances is image-only in all three years; the
  DGB open-data API is wrong on one programme by a factor of 5.3 and unreliable on economic
  labels everywhere; the **annual cross-classification XLSX is native, complete, reconciles
  exactly and carries the interior/exterior split**. Make it the first fetch of any future Benin
  run. (New archetypes K and L in the strategy library.)
- **The ministries' own PAPs are the corroborating voice, and they are free.** The *Projets
  annuels de performance*, **version loi de finances** edition, are SIGFP-generated, native, and
  carry a six-year AE/CP schedule per programme. The MND's PAP agrees with the DGB workbook **to
  the franc** on programmes 100, 109 and 111 across 2024, 2025 and 2026. Fetch the `VLF` edition,
  never the `PLF` one.
- **The open programme-044 contradiction is resolved by the MTFP's own PAP: 1 910 016 619 FCFA for
  FY2024**, matching the workbook to the franc and rejecting the API's 10 205.4 M. So the FY2024
  run's *"16.2 bn outside the sector vote"* headline **does not survive** — the pair is 7 910.0 M
  against programme 111's 12 701.4 M, i.e. the cross-vote lines are worth about 62% of the sector
  programme, not 128% of it. Block 4b still matters for Benin; that specific claim does not.
- **And the same document settles what a later workbook edition's prior-year column is.** The
  LF 2026 edition gives FY2024 programme 111 as 14 464 064 kFCFA where the LF 2025 edition and
  both the API and the ministry's PAP give 12 701 422. **The contemporaneous edition is the
  appropriation; later editions restate closed years without labelling the stage.** Never build an
  appropriation from a later edition's comparator column.
- **`pdftotext -table` broke the wall that `-layout` could not.** The PLFR note's execution annex
  is a 13-column SIGFP table that `-layout` scrambles into unusable offsets; `-table` read it
  first attempt, and every extracted line then cross-footed against the document's own
  `disponible` and `taux` columns. This is now step 4 of the standing toolchain.
- **The execution finding, with the origin gate applied.** At 30 April 2026 programme 111
  *Numérique* had ordonnancé **0.62%** of its gross credits against an all-programmes **15.43%**.
  Its own pilotage programme (100) ran at 20.12%, so this is programme-specific, not ministry
  paralysis. On the **domestic** portion alone the rate is **1.32%** — the whole of the execution
  was domestic, because the 6.5 bn FCFA external loan tranche had engaged nothing. Both numbers
  are worth holding: the gross rate is what the document prints, the domestic rate is what the
  fisc actually did.
- **Block 4c, stated as an asymmetry.** The **APDP is fully visible** — its own budget institution
  in FY2024 (code 7), dotation 014 thereafter — at 488 277 / 638 277 / 738 277 kFCFA across the
  three years, and it drew exactly 25.00% at one quarter, a flat subvention. **ASIN, the national
  CSIRT, datacenter and PKI operator, has no visible budget line anywhere in the estimates
  volume** in any of the three years; it is funded inside programme 111. **ANIP**, which runs the
  national identity system, likewise carries no programme of its own. **ARCEP** never appears in
  the loi de finances at all — it is own-source funded from redevances (6 520 742 720 FCFA in 2024;
  4 768 581 763 in 2025, −26.9%). So the data-protection authority is legible and the
  cybersecurity and identity agencies are not: the gap is in the *institutions*, not the volume.
- **Cross-vote scan, complete for all three years, and it is short.** Beyond the sector ministry
  the only genuine digital programmes are **044** *Modernisation de l'administration publique*
  (MTFP, ~1.8 bn) and **108** *Modernisation des régies financières* (MEF special account,
  6.0 bn). Looked for and **not found**: any identity, état civil or interoperability programme;
  any e-justice line separable from programme 020 *Services judiciaires* (a multi-purpose
  envelope, confirmed against the MJL's own PAP); any statistics-modernisation line. Programme 080
  *Pilotage MISP* triples in FY2026 on a 10 739 415 kFCFA external-loan capital line that the
  budget documents never describe — press reporting says video-protection — so **purpose is
  sourced and amount is not attributable**: no record, stated as an absence instead.
- **Three digital programme codes are carried at zero** in every year since 2024: 066 *Sécurité
  Numérique*, 104 *Digitalisation de l'Administration* and 106 *Infrastructure et Usages
  Numériques*. Retired codes kept in the table, not unfunded programmes.
- **What is still missing, and it is one page.** The FY2025 *revised* stage exists only on p. 59 of
  the OCR-blocked RAPEX au 31 décembre 2025 (*Synthèse des mouvements de crédits par ministère*).
  That single page is the highest-value OCR unblock in the Benin corpus. FY2024 has no revised
  stage at all, and no full-year outturn is readable in any of the three years — every RAPEX
  volume is a scan, and the FY2026 Q1 edition has no text layer whatsoever.

### Burkina Faso — the whole chain is native, and the volume carries its own origin split (sweep, 2026-07-25)

- **Fiscal year:** calendar (Jan–Dec); "2024" = *exercice 2024*. Programme budgeting under
  **loi organique n°073-2015/CNT du 06 novembre 2015 (LOLF)**: credits are voted by *section*
  (39 of them — ministries and constitutional institutions alike), decomposed into *programmes*,
  then *actions*, *chapitres* and *activités*.
- **The Track-B target is not the ministry site. `dgb.gov.bf` is under construction and its own
  banner redirects you:** *« Site en construction pour toute consultation veuillez voir le site
  intermediaire https://budgetouvert.wordpress.com »*. Its `/documentation/`,
  `/lois-de-reglement/`, `/programmation-budgetaire/`, `/boost/` pages render category headings
  with **zero document links in the static HTML**, and its `wp-json` media library is 156 items
  of mostly photographs. A thin harvest there is not evidence of absence.
- **`budgetouvert.wordpress.com` IS the DGB library, and one API call is the whole chain.**
  `public-api.wordpress.com/rest/v1.1/sites/budgetouvert.wordpress.com/posts/?number=100` →
  **18 posts** carrying ~180 document links, 2010–2026, organised as *Exécution du budget YYYY*
  (one post per year), *Loi_finance*, *Lois_règlement*, *Circulaire_budgétaire*, *LES DPBEP*,
  *Budget_Citoyen*. No scraping, no pagination, no download manager. **The best Track-B target in
  this series so far** — better than Benin's WordPress media library, because nothing is
  media-only and no search term 500s.
- **The estimates volume is the loi de finances itself, published whole and NATIVE.**
  `loi-de-finances-2024-2026-vf2.pdf`, **1 544 pages**, scale declared *en milliers de F CFA*.
  Per section it gives: *PREVISION DES DEPENSES GLOBALES PAR NATURE*, *…PAR PROGRAMME*, *…PAR
  PROGRAMME ET PAR NATURE*, then *PREVISIONS DES DEPENSES PAR PROGRAMMES, ACTIONS, PAR CHAPITRES
  ET PAR ACTIVITES* — plus the performance framework (indicators with baseline and targets, and
  the responsible body named, e.g. ONI against *taux de burkinabè possédant la CNIB ou le
  Passeport*). AE and CP, three years each. The SOMMAIRE maps every section to its printed page
  range; PDF page ≠ printed page (printed 981 = PDF 1091), so locate sections by grepping
  `Section NN :`, not by the SOMMAIRE's numbers. **Section→PDF-page ranges for FY2024:** 09 MATDS
  218–296 · 10 Justice 297–361 · 14 MEFP 450–520 · **31 MTD-PCE 1187–1208** · **59 CIL 1436–1455** ·
  99 Dépenses Communes Interministérielles ~1540 · CAST annex from 1497.
- **⚠ The volume's embedded copy of the law articles is a dirty scan** (`L'ASSEM'BLEE`,
  `r?sol ution`, `1cr janvier` for `1er janvier`) while **the tables are native**. Don't judge the
  file by its first 100 pages. Use the `an.bf` copy (`/storage/Loi/<key>.pdf`, 104 pp, clean) for
  the law text.
- **THE ORIGIN GATE IS A ROW IN THE DOCUMENT.** Capital is broken out as **Etat Seul / Etat
  (Contrepartie) / Subvention / Prêt**. No other country in this corpus states the domestic share
  of a digital programme inside the estimates volume. Use it: the MTD-PCE's FY2024 headline is
  **CP 20 119 980** (milliers) of which domestic capital is only **1 275 951 + 157 850 = 1 433 801**.
- **The execution reports are native and their annexes are the domestic executed grain.** Five
  points per year: quarterly *Rapport sur la situation d'exécution du budget et de la trésorerie
  de l'Etat* (au 31 mars / 30 juin / 30 septembre / 31 décembre) **plus** the statutory *revue à
  mi-parcours au 31 juillet*, whose conclusions go to the Conseil des ministres and which is the
  instrument that triggers the LFR. The full-year edition is 69 pp with 16 annexes. **Annexe 6** is
  the one to read: *…Crédits de paiement par ministère et institution et par programme budgétaire,
  **hors charges dette, dépenses de personnel, et financements extérieurs** (en FCFA)*, columns
  `CP_INIT | CP_AJUST | ANNULATIONCP | OUVERTURECP | CP_CORRIGE | ENGAGES VISES | ENGAGES
  COMPTABILISES | LIQUIDES | ORDONNANCES`, each with a taux. Annexe 7 the same for AE. **`pdftotext
  -table` reads all of it first attempt**; `-layout` scrambles it (same as Benin's PLFR annex).
- **The reconciliation that validates the pair:** volume *Etat Seul + Contrepartie* for section 31
  = 1 433 801 (milliers) and Annexe 5's investment CP_INIT = 1 433 801 000 F CFA. Exact. Do this
  check first on any Burkinabè year — it confirms the *milliers* scale and confirms the annexes are
  domestic-only.
- **Digital lines found under:** section **31** programmes **095** *Developpement d'infrastructures
  de communications électroniques*, **096** *Appui au sous-secteur postal*, **097** *Pilotage et
  soutien aux structures du MDENP* (note: the programme label still says MDENP, the ministry's
  former name), **136** *Transformation et écosystème numérique*. **Programme 136 is 95% one
  chapter: `1801800311 PROGRAMME WURI`, activité 1360126 « METTRE EN ŒUVRE LE PROGRAMME WURI », CP
  14 221 850 of 14 990 460 milliers** — the World Bank identity credit wearing a domestic programme
  label. Chapitre codes are the join key to the executing body (`1018000311 DGTD`, `1801800311
  PROGRAMME WURI`).
- **Block 4c is unusually good: the data-protection authority is its own budget section.**
  **Section 59, single programme 122 *Protection des données à caractère personnel*** — the CIL.
  FY2024: ordinaires 692 062 (biens et services 597 575 + transferts 94 487), capital 165 000 all
  *Etat Seul*, **total CP 857 062 milliers**, executed 799 459 500 F CFA (100,00%). **No personnel
  line** — staff are *agents publics mis à disposition* (loi n°001-2021/AN art. 54). **The MTEF
  years cut it 39% (857 062 → 523 838 → 524 796) with capital to zero**, and the COMFIB asked the
  CIL's president why, given the new headquarters was programmed for the same period — a
  headquarters being built under a **PPP**. Single-mandate carve-out applies.
- **Block 4b sits at *action* and *activité* grain, not in programme titles** — a keyword scan of
  programme names returns almost nothing, a scan of the 6 090 activity lines returns 14 sections.
  The identity cluster is **section 09 MATDS** (ONI, CNIB, passeport, biométrie, and its own
  **programme 015 *Etat civil***); the voter register is **section 58 CENI**; consular biometrics
  **section 12**; tax/finance systems **section 14** (SIMP, téléprocédures); **SIGASPE** appears in
  section 32 and **SIGED** in section 24. **And RESINA is in section 99 *Dépenses Communes
  Interministérielles*** — activité 1560215 *« Réaliser l'interconnexion à RESINA »* — cross-government
  connectivity money in the interministerial pot, invisible from every sector vote. Also
  **CAS n°129 « Soutien à la modernisation de l'administration publique »** (Fonction publique), one
  of 13 comptes d'affectation spéciale authorised for FY2024.
- **⚠ Ministry perimeters move mid-year and credits are re-based accordingly.** **Décret
  n°2024-0908/PRES/PN du 1er août 2024** (composition du gouvernement) caused **132 839 392 000
  F CFA of credits to be cancelled** in the LFR 2024, on top of **187 661 513 000** of ordinary
  *régulations*. Any BFA series keyed on section or programme codes needs a mapping row at
  **2024-08-01**. Third country in this corpus (after Kenya and Benin) where the machinery of
  government breaks the code series.
- **In-year cancellation, not under-spending, is the Burkinabè pattern.** Programme 095's domestic
  CP went 1 304 009 000 → 273 482 000 (**−54%**, ANNULATIONCP 704 383 000) and the remainder was then
  ordonnancé at 99,49%. Read `CP_INIT` vs `CP_CORRIGE` before reading any taux: a 99% rate against a
  gutted base is not delivery.
- **False positive, confirmed and quantified.** The back-swing already flagged the ministry's
  **CASEM** Plan de Travail Annuel as a ministry envelope including postal activities. It also
  reports a *taux d'exécution financière* — **9,06%** (1 069 478 840 of 11 805 795 000 F CFA at
  30-11-2024) against 79,88% physical. That 9% is **not** the fisc failing: the PTA denominator
  includes external financing that did not disburse, and Annexe 6 shows the ministry drawing 99,89%
  of its domestic non-personnel CP. Never quote the CASEM financial rate as a state-execution rate.
- **The government blames its own systems for under-execution.** The revue à mi-parcours 2024 names
  *l'instabilité du réseau informatique de l'administration (RESINA) et des applications métiers
  (SI-N@FOLO, SIMP et SIGASPE)* among the causes of low investment execution; the COMFIB records
  G-Cloud instability abandoning e-services, SIGED/SIGEPE deployment delays, and **sabotage of eight
  PADTIC pylon sites** (Lalgaye, Yamba, Dira, Sanaba, Aorèma, Biliga, Boni, Dargo). Useful
  first-hand material on why DPI spending under-delivers in a conflict state.
- **Block 6 is a nil return, and it is a real one.** The **ARCEP *Rapport d'activités 2024*** (106 pp,
  native, via the WPDM route `arcep.bf/download/rapport-dactivites-2024/?wpdmdl=50059`) gives the
  sector's finances — CA HT 533,86 mds F CFA (+4,20%), sector investment 87,22 mds (down from
  118,81), taxes collected 155 mds — but **searched end to end it states neither ARCEP's own budget
  nor any FASU account**, though the FASU is levied at 2% of operator turnover and administered by
  ARCEP. Benin's ARCEP prints own resources to the franc; Burkina's does not. Separately, the revue
  à mi-parcours records ARCEP's **dévolution de résultats to the Treasury, 23,48 mds F CFA** for 2024
  and 2025 by anticipation — **revenue, not spend**.
- **Audit: produced but not published, and the RPA is a year behind its label.** The Cour des comptes
  *Rapport public annuel 2024* (353 pp, native) reports the Cour's **2024 activity** but the RELF
  bound into it is for **exercice 2023** — so never assume an RPA edition audits the year in its
  title. FY2024's RELF should appear in the RPA 2025 (due late 2026). The RPA 2024 also carries the
  Cour's own budget hors personnel (2024: besoins 936 000 000, dotations définitives 832 045 000
  F CFA) and a conformity audit of **all PPP contracts 2015–2022** finding the procedure rules were
  not respected — relevant to the CIL's PPP headquarters.
- **Procurement rotates and is therefore perishable.**
  `dgcmef.gov.bf/fr/plan-de-passation-des-march-s-publics` carries **the current year only** (as at
  2026-07-25: 2026 plans, incl. the MTD-PCE's). Site search returns the sidebar, not results, and
  guesses at the exercice-2024 statistics bulletin under `/sites/default/files/2025-0*/` all 404.
  **Sweep Burkinabè PPMs in-year or lose them.** The *Quotidien / Revue des marchés publics* (daily
  bulletin, `Quotidien N°NNNN.pdf`) is also current-window only and is the route to award-level
  vendor detail.
- **No DNS tricks needed anywhere** — `finances.gov.bf`, `an.bf`, `alt.bf`, `dgb.gov.bf`, `arcep.bf`,
  `dgcmef.gov.bf`, `arcop.bf`, `anptic.gov.bf`, `oni.bf` all resolve and serve directly, unlike
  Kenya, Senegal, Angola and Burundi. **Traps:** `cour-comptes.gov.bf` is the Cour des comptes and
  it has **no A record at all** (nor does `courdescomptes.gov.bf`) — the Rapport public annuel came
  from the `minute.bf` mirror; the digital ministry is **`mdenp.gov.bf`**, not
  `transitiondigitale.gov.bf`; `armp.bf` does not resolve (procurement regulation is `arcop.bf`,
  control is `dgcmef.gov.bf`).
- **`an.bf` stores parliamentary papers under opaque per-type paths** — `/storage/Loi/<key>.pdf`,
  `/storage/libelrapportcomfib/<key>.pdf`, `/storage/libelcranal/<key>.pdf`, with random keys. Exa
  surfaces them; path guessing cannot. The **COMFIB report on the PLF** is Burkina's equivalent of
  Benin's per-vote *rapports spéciaux* but in one 144-page native document, and it is the richest
  Block-4c/Block-7 source in the country: hearings ministry by ministry, credit-evolution tables for
  priority ministries, and the deputies' questions verbatim. `alt.bf/loip` is the law index (ends
  December 2024).
- **Searched, found nothing:** any separately appropriated national CSIRT or **BCLCC** (Brigade
  centrale de lutte contre la cybercriminalité) line; any FASU account; an ARCEP own-budget figure;
  a **CIL annual report for 2024** — the Centre national de presse Norbert Zongo records (2025-02-11)
  that *« En 2024, la CIL n'a pas rendu public un rapport »*, though art. 61 of loi n°001-2021/AN
  requires an annual public report; the exercice-2024 DGCMEF procurement statistics bulletin; the
  FY2024 loi de règlement and RELF.
- **The happy headline: Burkina Faso needs no OCR.** All 19 documents staged for FY2024 are native
  text, including both 1 000+-page volumes. It is the exact inverse of Burundi (whole chain
  image-only) and the complement of Benin (appropriation native, execution OCR-blocked): here both
  sides are native, and the binding constraint is neither availability nor OCR but the *audited*
  stage simply not being published yet.

### Burkina Faso FY2025 — the same chain, three silent definition changes, and a vendor named in the vote (sweep, 2026-07-25)

Read this section **with** the FY2024 section above; it records only what differs, and the
differences are the point. Nineteen documents were staged for FY2024, sixteen for FY2025, and
the FY2025 set is **not a like-for-like series with FY2024** in three places.

- **The Track-B route is unchanged and still the best in this corpus.** One call to
  `public-api.wordpress.com/rest/v1.1/sites/budgetouvert.wordpress.com/posts/?number=100`
  returned the same **18 posts** and the whole FY2025 chain in a single request: the estimates
  volume, the projet, the avant-projet, two exposés des motifs, four quarterly execution
  reports, the budget citoyen, the DPBEP, the projet de LFR and its exposé. `dgb.gov.bf` is
  still under construction and still redirects to it. **Repeat this call, don't re-discover it.**
- **The estimates volume is again the loi de finances published whole**
  (`2025/01/loi-de-finances-pour-lexecution-du-budget-de-letat-exercice-2025.pdf`, **1 560 pp**,
  *en milliers de F CFA*), same `section → programme → action → chapitre → activité` grain, same
  AE/CP over three years, same **Etat Seul / Contrepartie / Subvention / Prêt** origin split.
  `pdftotext -table` again reads it first attempt.
- **⚠ CHANGE 1 — the embedded law is now a *pure* scan, not a dirty one.** FY2024's law pages
  had a bad OCR layer; **FY2025's PDF pp. 5–86 return zero characters**. Use the `an.bf` copy
  (`/storage/Loi/FU4cnAqfHyREj0BsvgaPYtIa7qTRtT8piMrO4EIN.pdf`, 83 pp, native). Note
  `budgetouvert`'s own standalone copy of the law (`2025/01/loi-de-finances-2025.pdf`, 82 pp) is
  **also image-only** — and the CABRI mirror is byte-identical to the an.bf file. Four copies,
  two of them useless: for Burkinabè budget papers, **dedup on content, not URL**.
- **⚠ CHANGE 2 — 36 sections, not 39.** The machinery-of-government change of décret
  n°2024-0908/PRES/PN du 1er août 2024 has landed in the vote structure: section 09 is now
  *Administration Territoriale et de la Mobilité* (was *…Décentralisation et Sécurité*), and
  **Sécurité is a new section 13**. Any BFA series keyed on section codes needs its **second**
  mapping row, at 2025-01-01, on top of the 2024-08-01 one. Section→PDF-page ranges for FY2025
  are in the volume's companion page; **31 MTD-PCE 1188–1210**, **59 CIL 1479–1491**,
  **09 MATDS 181–256**, **99 Dépenses Communes 1503–1511**.
- **⚠ CHANGE 3 — and this is the one that silently invalidates a comparison — ANNEXE 6 OF THE
  OUTTURN CHANGED DEFINITION.** FY2024's Annexe 6 was *…par ministère et institution et par
  programme budgétaire, hors charges dette, dépenses de personnel, **et financements
  extérieurs*** — which is why the FY2024 note calls it the domestic executed grain. FY2025's is
  *…par **section** et par programme budgétaire, **hors dépenses de personnel*** only. External
  financing is **back in**, and the `ANNULATIONCP / OUVERTURECP / CP_CORRIGE` columns were
  dropped. Proof by arithmetic: section 31's FY2025 Annexe-6 `CP_INIT` is **24 532 888 000 F
  CFA** = the volume's section total CP 26 874 174 minus its personnel line 2 341 286 (milliers).
  **Never compare a FY2024 Annexe-6 figure with a FY2025 one.**
- **The domestic grain for FY2025 is ANNEXE 5** (*dépenses d'investissement exécuté par l'Etat,
  par ministère et institution*), and **the FY2024 reconciliation still works**: Annexe 5's
  section-31 `CP_INIT` is **6 643 398 000 F CFA**, exactly the volume's *Etat Seul* 5 138 758 +
  *Contrepartie* 1 504 640 (milliers). **Run this check first on every Burkinabè year** — it
  fixes the scale *and* tells you which annexe is domestic that year. Cost: Annexe 5 is
  **ministry grain only**, so FY2025's domestic executed view is **coarser** than FY2024's, which
  had programme grain. Say so on anything built from it.
- **⚠ Two more basis shifts, both undeclared by the documents.** (a) The quarterly reports moved
  from *engagé-visé* (FY2024) to **engagé-comptabilisé** (FY2025) while still printing
  prior-year comparatives, so a naive two-year execution-rate series is wrong. (b) The **revue à
  mi-parcours moved from *au 31 juillet* to *au 30 juin***, so it now coincides with Q2 instead
  of sitting between Q2 and Q3.
- **THE FINDING OF THE YEAR: a vendor is a budget chapter.** Section 31, programme 136, **chap.
  1800900311 « MICROSOFT », AE = CP = 4 086 853 milliers de F CFA** in 2025, **zero in 2026 and
  2027**. And the section's whole *Etat Seul* line reconciles to it exactly:
  `MICROSOFT 4 086 853 + Réseau Administratif 1 000 000 + Projet d'équipement 15 225 + 36 680 =
  5 138 758`. So **79,5 % of the digital ministry's entire domestically-financed capital
  appropriation for FY2025 is a single chapter named after a foreign software vendor** — while
  the two donor programmes (WURI 13 088 057 CP; **PACTDIGITAL, now its own chapitre
  1801900311**, 3 827 599 CP) carry the Subvention and Prêt lines. Chapitre codes remain the join
  key to the executing body. Cross-check: the Prime Minister directed a move to *outils
  numériques souverains … en substitution progressive aux solutions tierces* on 3 February 2026.
- **The origin split moved sharply.** MTD-PCE capital FY2025: **Etat Seul 5 138 758 ·
  Contrepartie 1 504 640 · Subvention 6 818 057 · Prêt 8 592 959** (milliers), so domestic capital
  is **6 643 398 against FY2024's 1 433 801 — a 4,6× rise**. The ministry's headline CP went
  20 119 980 → 26 874 174. Burkina Faso is putting materially more of its own money into the
  digital vote; the WURI/PACTDIGITAL donor share fell from 95 % of programme 136 to about 69 %.
- **In-year cancellation is confirmed as the Burkinabè pattern, and it got much bigger.**
  Section 31 domestic investment: `CP_INIT` 6 643 398 000 → `CP_AJUST` **2 094 407 522** → ordonnancé
  2 094 406 682 (**100,00 %**). A **68,5 % in-year cancellation**, 4,55 bn F CFA, then a perfect
  draw-down of what was left. On the total-hors-personnel view, programme **096 (postal) was cut
  99,3 %** (606,2 M → 4,3 M) and **136 cut 77,5 %**; only **095** was increased. **Read `CP_INIT`
  against `CP_AJUST` before reading any taux** — FY2025 no longer gives you the cancellation
  column, so you must difference it yourself.
- **Block 4c: the CIL's cut happened exactly as the COMFIB feared.** Section 59, single programme
  **122, renamed *Protection des personnes à l'égard du traitement des données à caractère
  personnel***: total CP **498 999** milliers, **all ordinary, capital ZERO**, still **no
  personnel line**, and the MTEF holds it flat (499 452 / 500 542). That is **−41,8 % on FY2024's
  857 062**. Executed 480 297 496 F CFA of 480 298 000 (100,00 %). By action, enforcement —
  *12202 Contrôle des traitements de données personnelles* — gets **56 646** milliers, 11,4 % of
  the authority. Meanwhile the CIL **validated its rapport public 2024 on 26 June 2025** (so the
  FY2024 "no report" finding is now superseded on the *validation* side, though the document is
  still unpublished) and adopted control guides for videosurveillance and digital platforms in
  July 2025. **Doctrine expanding, budget contracting** — the cleanest statement of that pattern
  this corpus has.
- **Block 4b pays out through the Conseil des ministres, not the volume.** Two authorisations,
  both explicitly *financement assuré par le budget de l'Etat, exercice 2025*: the MTD-PCE's
  **5 895 000 000 F CFA TTC** of 2 July 2025 (supervision centres for Backbone/Datacenters/RESINA
  and the cyberespace 4 000 M; RESINA rehabilitation equipment 1 600 M; cybersecurity tools 95 M;
  suivi-contrôle 200 M) and the **MEF's projet smart douane « SOLUTION DOUANIERE INTELLIGENTE »,
  3 313 000 000 F CFA TTC**, plus 17 non-intrusive scanners at 1 130 000 000, of 18 June 2025.
  **The customs pair alone is two-thirds of the digital ministry's whole domestic capital
  appropriation** and is invisible from section 31. **The Conseil des ministres communiqué is
  Burkina Faso's richest Block-4b instrument** — itemised, costed, dated, and origin-stated. Sweep
  it systematically. The official PDFs (`PP-G N°0NN-YYYY`) are mirrored on `burkina24.com`
  `/wp-content/uploads/` and reproduced verbatim by `rtb.bf`, `wakatsera.com`, `libreinfo.net`.
- **A new stage exists in Burkina Faso: the *avant-projet*.** `budgetouvert` posts
  `avant-projet-de-loi-de-finances-exercice-2025.pdf` (1 343 pp) — the ministries' consolidated
  request **before** the presidential arbitrages of 18–29 October 2024 — alongside the *projet*
  (1 339 pp) and the enacted volume (1 560 pp). That gives a **requested → arbitrated → enacted**
  comparison at section grain, which no other country-year in this corpus supports, and it is the
  only instrument that would show what the CIL asked for before being cut 41,8 %.
- **The fiscal-risk statement stopped being its own document.** FY2024 had `drb_2024_vf1.pdf`;
  FY2025's risk statement is Part VI of the **DPBEP 2025-2027**. Record as a transparency
  regression, not a sweep gap.
- **MTEF outer years are non-predictive here, quantifiably.** The FY2024 volume projected the
  MTD-PCE at 11 851 833 milliers for 2025; the enacted figure is 26 874 174 — the outer year
  understated by **2,3×**. Never carry a Burkinabè MTEF outer year as an expectation.
- **The government blames its own systems for under-execution, a second year running.** The revue
  à mi-parcours 2025 names *« l'instabilité du réseau informatique de l'administration (RESINA)
  et des applications métiers (SI-N@FOLO, SIMP et SIGASPE) »* among the causes — the same four
  systems, near-verbatim, as 2024.
- **The CASEM financial rate is a trap in both directions.** FY2025: PTA of **131 activités /
  30 377 644 070 F CFA**, consumed **3 281 196 260** at 30 June = **10,80 %** financial against
  43,61 % physical; 78,05 % physical at 30 November. But the same ministry drew **100,00 %** of
  its adjusted domestic investment credits. And its *own* FY2024 rate moved from **9,06 % at
  30 November 2024** to **69,89 % at 31 December 2024** — supersession, not contradiction, but it
  means **any Burkinabè PTA financial rate read before December is close to meaningless**. Never
  quote either as a state-execution rate. PTA 2026 is 156 activités / 61 mds F CFA.
- **Procurement is confirmed perishable — the FY2024 prediction came true.** At 2026-07-25
  `dgcmef.gov.bf/fr/plan-de-passation-des-march-s-publics` carries **2026 only**; the FY2025 PPMs
  are gone. **Sweep Burkinabè PPMs in-year or lose them** is now an established rule, not a
  guess. (The FY2026 MTD-PCE and MATDS plans are live now and are targets for the BFA 2026 run.)
- **Blocks 3 and 6 are unchanged nil returns, and both are real.** The Cour des comptes' latest is
  still the **RPA 2024** (carrying the FY2023 RELF), released 5 December 2025 — so the FY2024 RELF
  is still unpublished and FY2025's is not due. ARCEP's `rapports-dactivites` page still ends at
  **2024**. The **enacted LFR 2025** and the **enacted loi de règlement 2024** (adopted the same
  day, 14 October 2025) are both unpublished — the first is a genuine regression on FY2024.
- **Hosts, unchanged:** no DNS tricks needed for `budgetouvert.wordpress.com`, `finances.gov.bf`,
  `an.bf`, `assembleenationale.bf`, `arcep.bf`, `dgcmef.gov.bf`, `cil.bf`, `mdenp.gov.bf`,
  `primature.gov.bf`, `rtb.bf`. `cour-comptes.gov.bf` still does not resolve. The revue à
  mi-parcours is again on `finances.gov.bf`, under `/fileadmin/user_upload/storage/**fichiers**/`
  this year rather than `/storage/` — the path moved, so search rather than guess.
- **OCR: one document out of sixteen.** Only the *circulaire d'orientations* (n°2025-029/PM/CAB
  du 18 février 2025, 15 pp) is image-only. Burkina Faso remains the corpus's native-text
  outlier — but "no OCR at all", true for FY2024, is no longer true.

### Burkina Faso FY2026 — the vendor chapter vanishes, the ANSSI arrives, and a whole section is abolished (sweep, 2026-07-25)

Read this **with** the FY2024 and FY2025 sections above; it records only what differs. Nineteen
documents were staged for FY2024, sixteen for FY2025, **seventeen for FY2026**.

- **Track B is unchanged and remains the best route in this corpus.** One call to
  `public-api.wordpress.com/rest/v1.1/sites/budgetouvert.wordpress.com/posts/?number=100`
  returned the same **18 posts** and **14 of the 17 documents** in a single request.
  `dgb.gov.bf` is still under construction and still redirects there. **Repeat the call.**
- **The estimates volume is again the loi de finances published whole**
  (`2026/01/loi-de-finances-pour-lexecution-du-budget-de-letat-exercice-2026.pdf`, **1 480 pp**,
  *en milliers de F CFA*), same grain, same AE/CP over three years, same **Etat Seul /
  Contrepartie / Subvention / Prêt** origin split. `pdftotext -table` reads it first attempt.
  **The FY2026 edition is published as the *Journal officiel du Faso, spécial n°1 du 2 janvier
  2026*** — loi **n°021-2025/ALT du 27 décembre 2025**, promulgated by **décret n°2025-1660/PF**
  of 30 December 2025.
- **⚠ The law-article pages are an image scan again**, PDF pp. ~6–46, returning ~65 characters a
  page (the running header only). The tables from p. 47 are native. Same defect as FY2025; the
  fix is the same — get the clean articles from `an.bf/storage/Loi/<key>.pdf`. Neither `an.bf`
  nor `dgi.bf` surfaced one this year, so it is on the acquisition list.
- **⚠ CHANGE — 36 sections, not 37, and the one that went is SECTION 58, the CENI.** The
  **Commission électorale nationale indépendante was dissolved** by a law adopted unanimously by
  the ALT on **28 October 2025** (origin instrument: Conseil des ministres of 16 July 2025,
  PP-G n°023-2025). Art. 2 devolves all its competences and missions, and art. 3 all its assets,
  documents and archives — **including the electoral register** — to the **ministère chargé de
  l'Administration territoriale, section 09**. Its FY2025 vote was **CP 498 365 milliers**
  (programme 121 *Elections*, all ordinary, capital zero, no personnel line), which corroborates
  the minister's public *« 500 millions F CFA hors temps électoral »* to the franc. **Any BFA
  series keyed on section codes now needs its THIRD mapping row, at 2026-01-01**, after
  2024-08-01 (décret n°2024-0908) and 2025-01-01 (Sécurité split out as section 13). Three
  machinery breaks in three years — Burkina Faso is now the worst offender in this corpus.
- **Section → PDF page for FY2026** (first page of each block): 01 74 · 02 96 · 03 106 · 04 122 ·
  06 126 · **09 MATM 132** · 10 202 · 11 267 · 12 293 · 13 344 · **14 MEF 397** · 17 471 ·
  18 514 · 20 562 · 21 665 · 22 735 · 23 791 · 24 868 · 25 917 · 26 951 · 27 999 · 30 1071 ·
  **31 MTD-PCE 1103** · 37 1124 · 38 1191 · 42 1225 · 50 1303 · 51 1310 · 52 1321 · 54 1334 ·
  55 1346 · 56 1356 · 57 1366 · **59 CIL 1376** · 61 1388 · **99 1399**. Printed ≠ PDF page
  (printed 1058 = PDF 1103); locate by grepping `Section NN :`.
- **THE FINDING OF THE YEAR: the MICROSOFT chapter is gone, and it took the domestic capital line
  with it.** FY2025's chapitre **1800900311 « MICROSOFT »** (AE = CP 4 086 853 milliers, 79,5 %
  of the ministry's domestic capital) was programmed to zero in 2026-2027 by the FY2025 volume.
  **The enacted FY2026 volume has no such chapitre.** *Etat Seul* reconciles exactly to what
  remains: **Réseau Administratif 1 000 000 + Projet d'équipement 235 146 = 1 235 146**.

  | Section 31 (milliers) | FY2024 | FY2025 | FY2026 |
  |---|---|---|---|
  | Etat Seul | 1 275 951 | 5 138 758 | **1 235 146** |
  | Contrepartie | 157 850 | 1 504 640 | 579 261 |
  | **domestic capital** | **1 433 801** | **6 643 398** | **1 814 407** |
  | headline CP | 20 119 980 | 26 874 174 | **29 634 565** |

  So **FY2025's 4,6× rise in domestic digital capital was, almost entirely, one vendor chapter**,
  and FY2026 gives back 72,7 % of it while the headline keeps rising on external money. The
  Prime Minister's *outils numériques souverains* directive is dated **3 February 2026**; the
  volume that removed the chapter was enacted **27 December 2025**. The budget moved first.
- **⚠ PACTDIGITAL has moved programme.** It was chapitre 1801900311 under programme 136 in
  FY2025; in FY2026 it sits under **programme 095, action 09503**, CP 8 592 331 (2026) and
  25 530 090 (2027). **PROGRAMME WURI** (1801800311, under 136) runs to CP 15 248 300 in 2026 and
  **zero in 2027-2028** — the identity programme closing. Consequence: programme 136's CP falls
  17 164 911 → **1 702 330** in 2027, a 90 % drop. Never build a 136 time series across
  2025→2026 without the chapitre-level move.
- **THE ANSSI IS APPROPRIATED — a two-year "searched, found nothing" is superseded.**
  **Section 31, programme 136, action 13604 *Sécurisation des systèmes d'information nationaux*,
  chapitre 1020000311 DIT**: activité *1360410 Assurer le fonctionnement de l'ANSSI* **324 200** +
  *1360411 ressources humaines de l'ANSSI* **165 036** = **489 236 milliers**, flat at 488 936
  (2027) and 502 136 (2028). Still no separate section; funded inside the digital ministry's vote.
  The Conseil des ministres of **16 April 2026** named its first director-general. The **BCLCC**
  and any national CSIRT remain absent, as do any **FASU** account and any **ARCEP own-budget**
  figure — all third-year nil returns, all real.
- **THE DEFINITIONS HELD STILL.** After FY2025's three undeclared changes, **FY2026 changed
  nothing**: Annexe 5 is still *investissement exécuté par l'Etat, par ministère* (domestic grain,
  ministry level); Annexe 6 is still *par section et par programme, hors dépenses de personnel*
  with external financing included; the execution basis is still *engagé-comptabilisé*; the
  mid-year cut-off is still *au 30 juin*. Annexe 7 now says ***hors financements extérieurs***
  explicitly for AE.
- **The reconciliation now closes in both directions — run it first on every Burkinabè year.**
  Downward: Annexe 5 section-31 `CP_INIT` **1 814 407 000 F CFA** = volume *Etat Seul* 1 235 146 +
  *Contrepartie* 579 261 (milliers), exact; Annexe 6 section-31 `CP_INIT` **27 447 428 000** =
  section CP 29 634 565 − personnel 2 187 137, exact. **Upward: Annexe 5's `Total général`
  `CP_INIT` is 876 100 000 000 F CFA, which is precisely the *investissements financés sur
  ressources propres* of 876,1 milliards the Minister of Finance quoted to the Assembly on
  27 December 2025.** That is the first external confirmation in this corpus that a country's
  domestic-capital grain ties to a published national total.
- **⚠ At Q1, `CP_AJUST` = `CP_INIT` almost everywhere.** The in-year cancellations that define the
  Burkinabè pattern (−68,5 % on section 31 in FY2025, −54 % on programme 095 in FY2024) happen
  later in the year. **No Q1 taux is a full-year signal**, in either direction.
- **Q1 2026, the contrast worth carrying:** on Annexe 5 (domestic), section 31's investment
  execution at 31 March 2026 is **literally zero** against an all-ministries 14,21 % engaged /
  6,16 % ordonnancé. On Annexe 6 (hors personnel), section 31 engaged **1,87 %** — programmes 095
  and 096 **0,00 %**, 136 **2,38 %** — while **the CIL engaged 52,31 %** against an all-sections
  17,62 %. The data-protection authority is committing four times faster than the ministry that
  runs the country's digital infrastructure.
- **Block 4c: the CIL, three years of contraction and two of zero capital.** Section 59, programme
  122: total CP **489 799** milliers (biens et services 411 312 + transferts 78 487), **capital
  ZERO**, AE zero, no personnel line; MTEF flat at 485 836 / 486 833. Against FY2024's 857 062
  that is **−42,9 %**. Enforcement (*12202*) **54 814 = 11,2 %** of the authority, below
  *Information et sensibilisation* 174 450 and *Pilotage et soutien* 137 658. The PPP
  headquarters is still programmed against a zero capital line, and the *rapport public 2024* —
  validated in plenary 26 June 2025 — is **still unpublished**. But note the counterweight: it is
  the fastest-committing body in the cluster at Q1.
- **Block 4b: the Conseil des ministres remains the richest instrument, and the channel is being
  re-regulated as it is used.** **16 April 2026 — MTD-PCE *projets spécifiques* 2026,
  9 113 100 000 F CFA hors taxes**, *« Le financement est assuré par le budget de l'Etat, exercice
  2026 »*: **Elites IT**, the **« Zama Tchè »** citizen houses (Bobo-Dioulasso + 8 regional
  capitals + **50 rural communes**), **datacenter reinforcement**, **RESINA reinforcement**,
  institutional capacity. ⚠ **That is five times section 31's entire domestic capital
  appropriation (1,814 bn)** — establish whether it draws on ordinary credits, *dotations
  communes*, or anticipates the LFR before building a record. ⚠ **And do not add it to the
  ministry's PPM**, whose line 2026.0014.00 (RESINA equipment, AOOD) is **665 398 382 F CFA** —
  two procurement channels, one vote. On **23 July 2026** the Conseil adopted a décret
  **tightening the conditions for recourse to *projets spécifiques*** (sovereignty, strategic
  character, threat to public order or service continuity) *and* a **37 951 315 686 F CFA TTC**
  BN-GPB package under that same route.
- **A NEW STAGE DOCUMENT: the arbitrage rapport.** `budgetouvert` posts
  `8-rapport-conseil-budget-2026-vf13-10-2025-revu.pdf` — **rapport en Conseil des ministres
  n°2025-501/MEF/CAB du 13 octobre 2025**, 17 pp native, the instrument by which the
  *avant-projet* was submitted to the President and the Conseil. Burkina Faso now documents
  **requested → arbitrated → enacted** with a dated instrument at each step, which no other
  country-year in this corpus does.
- **⚠ The PND 2026-2030's *enjeux* count drifts across three official documents in four months** —
  **six** (presidential budget circular, 02-07-2025), **eight** (MEF Conseil des ministres
  rapport, 13-10-2025), **seven** (exposé des motifs and COMFIB report). The referential was being
  formulated throughout. Not a contradiction; but **never cite "the N enjeux" without its document
  and date**.
- **⚠ The legislature was renamed mid-year.** The Assemblée législative de transition became the
  **Assemblée législative du Peuple** on adoption of the **Charte de la Révolution, 1 April 2026**.
  The FY2026 finance law is still *loi n°021-2025/**ALT***; the LFR 2026 goes to the ALP. Entity
  mapping row at **2026-04-01**.
- **Procurement was swept in-year and the perishability rule is proven a third time.**
  `dgcmef.gov.bf/fr/plan-de-passation-des-march-s-publics` at 2026-07-25 carries **2026 only** —
  MTD-PCE (27-02-2026, 4 pp), MATM (10-07-2026, 12 pp), CSC (11-02-2026), CNDH, an *Avis général*,
  a scanned recueil and the daily *Quotidien* (n°4442-4451). All native except the recueil, and
  **every line carries a funding-source column reading *Budget de l'Etat - Central***, plus
  reservation codes for micro/small/medium, women-led, youth-led and disability-owned Burkinabè
  firms (101/102/103/201/202/203) — a procurement-policy dimension no other country in this corpus
  prints on the face of the plan. ⚠ **The MATM plan names no CNIB, biométrie, passeport, état
  civil or fichier électoral line**: the identity systems are appropriated in section 09 but not
  procured through the ministry's own PPM. Several lines are UGP/UCP **PREGOLS** — externally
  financed activity riding on the plan; check origin before treating any as domestic.
- **Hosts: two changes.** `mdenp.gov.bf/documentation/` now returns **HTTP 500** (its *Annuaire
  statistique* series is a Block-6-adjacent target when it comes back). Everything else is as
  FY2025: no DNS tricks needed for `budgetouvert.wordpress.com`, `finances.gov.bf`, `an.bf`,
  `assembleenationale.bf`, `arcep.bf`, `dgcmef.gov.bf`, `cil.bf`, `dgi.bf`, `burkina24.com`,
  `minute.bf`; **`cour-comptes.gov.bf` still has no A record**.
- **Copy proliferation, and the dedup rule earns its keep again.** Two exposé des motifs versions
  (13-10 *amendé* and 17-10 *vf*) that **genuinely differ by ~800 characters** — both kept; a
  `dgi.bf` copy of the exposé that is the same document at 20× the file size — dropped; a 16 pp
  scan of the presidential circular alongside its 17 pp native — dropped. **Dedup on content, not
  URL.**
- **OCR: three documents out of seventeen**, plus the volume's law pages — both April-2026
  circulaires (the 149 pp *complet avec annexes* and the 14 pp *orientations 2026-2027*) and the
  8 pp PPM recueil. ⚠ **The 149 pp file is labelled 2026 but was posted in April 2026, after the
  FY2026 budget was enacted, so it may in fact be the circulaire budgétaire 2027** — establish the
  exercice from page 1 before use. Burkina Faso remains the corpus's native-text outlier: the
  orientations circular is the one document type that is image-only every single year.

### Burkina Faso — what the extraction found that the sweeps did not (budget-extract, 2026-07-25)

The three BFA sweeps read the volumes for *findings*; this pass read them for *records*, over all
36–39 sections rather than the digital vote, and that turned up two corrections and one method
lesson. Read this **after** the three sweep sections above; it amends them.

- **⚠ CORRECTION — the ANSSI was appropriated in FY2024, and it moved ministry.** The FY2024 and
  FY2025 sections record "searched, found nothing" for a national CSIRT or cybersecurity agency,
  and the FY2026 section reports the ANSSI's appearance in section 31 as *superseding a two-year
  absence*. **It was never absent.** The FY2024 volume carries **section 03 Primature, programme
  006, action 00601, chapitre 4013000311 « ANSSI », CP 444 200 milliers** — activités: fonctionnement
  96 882 + rémunération 153 118 + complément salarial 34 000 + **acquisition de licence pour le
  fonctionnement du SOC 100 000** + acquisition de deux adresses IP publiques pour le SOC 20 000 +
  loyers 40 200, summing exactly. What actually happened is a **move**: the agency sat under the
  Prime Minister's office in FY2024 and under the **digital ministry, section 31 programme 136
  action 13604**, from FY2025 (498 036 milliers) and FY2026 (489 236). The real finding is not
  "first appropriation" but *the cybersecurity agency changed political master, and its SOC tooling
  line did not survive the move* — from FY2025 the appropriation is fonctionnement and ressources
  humaines only. **Lesson: a "searched, found nothing" that only searched the sector vote is not a
  nil return.** Both earlier nil returns were sector-vote-scoped.
- **⚠ CORRECTION — PACTDIGITAL did not move programme.** The FY2026 section warns that chapitre
  1801900311 *« Projet d'accélération de la transformation digitale »* "was under programme 136 in
  FY2025; in FY2026 it sits under programme 095". It was under **programme 095, action 09503**, in
  FY2025 too — verified in the FY2025 volume's own chapitre table alongside *Réseau Administratif*.
  No mapping row is needed for it. (What is genuinely true is that **PROGRAMME WURI** stays under
  136 throughout and runs to zero after 2026.)
- **The identity cluster moved section twice, and that one is real.** *Documents biométriques
  d'identification* is **section 09 action 01208** in FY2024, **section 13 (the new Ministère de la
  Sécurité) action 01208** in FY2025, and **section 13 programme 168 action 16803** in FY2026 — so a
  series keyed on the action code breaks at 2026-01-01 as well as at the section level. Contents are
  stable: Projet IRAPOL (chapitre 1802400311) flat at CP 2 000 000 milliers all three years, the ONI
  (4008000311), and from FY2025 a *Projet de Sécurisation Visas* (1802700311) at 700 000.
- **The finance ministry is the second-largest identified carrier of digital money, and it was cut
  79 %.** Section 14, programme 038, action 03805 *Gestion des systèmes d'information et archivage*,
  chapitre **1803100311 « Projets Informatiques »**: CP **1 450 000 → 300 000 → 500 000** milliers
  across FY2024-26. And the FY2024 activité 0330105 *« Opérationnaliser la facture normalisée et les
  téléprocédures »* (500 000 milliers) is **zeroed in FY2025 and FY2026** — the e-invoicing mandate
  found in the FY2025 law has no money behind it in either year.
- **The domestic execution series closes end to end for FY2024 and only for FY2024.** Annexe 6's
  `CP_INIT` ties to the volume's domestic figures **exactly** at programme grain — 095: 1 304 009 000
  = capital *Etat Seul* 1 275 951 + biens et services 28 058 (milliers); 136: 665 119 000 =
  *Contrepartie* 157 850 + biens et services 34 961 + transferts 472 308; 122 (CIL): 857 062 000, the
  whole programme. **FY2025's Annexe 6 dropped the *hors financements extérieurs* clause**, so the
  same tie is impossible and the only domestic FY2025 outturn at programme grain is the CIL's, which
  works solely because section 59 has no external financing line at all. That is why this pass built
  three FY2024 executed records and one for FY2025.
- **The FY2024 domestic investment cancellation is bigger at section grain than at programme
  grain.** Annexe 5: section 31 `CP_INIT` 1 433 801 000 → `CP_CORRIGE` 420 794 000 (**−70,7 %**) →
  ordonnancé 419 789 258, i.e. **29,3 % of the original appropriation actually paid**. The FY2024
  sweep's "−54 % on programme 095" is the Annexe-6 (hors personnel) view of the same year. Quote the
  grain with the number.
- **No case-5 resets were available, and the reason is a finding.** Three held BFA `domestic-state`
  records are `source_tier: reporting` — network restoration in insecure areas (CFA 3 bn, FY2025),
  *zéro zone blanche* (37,5 bn, FY2025), two government mini data centres (16 bn, FY2026). **None is
  traceable to a line in the volumes**, because each announces an envelope larger than the whole
  matching domestic appropriation: section 31's FY2025 domestic investment credit was 6,64 bn
  appropriated and 2,09 bn paid, and its FY2026 domestic capital is 1,81 bn. The announced envelopes
  are not visible in the vote. They stand as reporting records; the gap is the story.
- **Method: the cross-vote scan must be a locator, not an extractor, on this archetype.** A first
  attempt parsed the amounts with a numeric regex and returned the **2026** column for FY2024 rows
  throughout — plausible figures, wrong year, no arithmetic tripwire. Positional slicing failed too:
  `-table` does not align the page's `AE CP` header row with its data rows. The scan now prints each
  hit's figures verbatim and parses none; see archetype M. `scripts/bfa-volume-scan.py` is the tool.
- **Scope traps confirmed, and not recorded.** Section 09/13's action *Système d'information
  mutualisée* looks like a digital line and is **86 % police payroll** (FY2024: CP 7 178 962 milliers
  gross, of which DGPN personnel 5 901 003); only the DGTI chapter, 290 000, is digital activity, and
  it is below the materiality this pass recorded at. Section 30's *réseau géodésique*, *réseau de
  nivellement* and *cartographie numérique* lines are survey and mapping infrastructure, not data
  governance — excluded, and the scan's EXCLUDE list now carries them. Section 31's programme 096
  (postal) and 097 (ministry pilotage) are not digital lines and were not recorded.
- **What was left for a re-extract, honestly.** The **proposed** stage (the PLF volumes) and the
  **requested** stage (the *avant-projet*, unique to Burkina Faso in this corpus) were not built into
  records this pass, nor was the enacted **LFR 2024**; all three are marked in the manifest's
  `re_extract`. Burkina Faso is the only country-year set here that could support a
  requested → arbitrated → proposed → enacted → executed series, and it remains the most valuable
  outstanding extraction in the corpus.

### Botswana FY2024/25 — the outturn is in a volume published two years later (sweep, 2026-07-25)

*(Supersedes nothing in the 2026-07-22 back-swing note above, which remains correct: the clean
lines do hide inside mixed ministry asks, and NDP/PIP coverage does name the systems. This
adds the document chain.)*

- **Fiscal year:** April–March; "2024" = FY2024/25 (2024-04-01 → 2025-03-31); documents label
  it `2024-25` or `2024/2025`.
- **`finance.gov.bw` is the best Track-B target in the series after Burkina Faso's WordPress
  API, and it is simpler.** It is a Joomla site, and
  `index.php?option=com_content&view=category&id=23` returns, in one page, hrefs to **every
  budget document from 2017/18 to 2026/27** — estimates volumes, appropriation acts, financial
  statements, budget speeches, citizen budgets, budget strategy papers, financial papers
  (supplementary estimates), budget monitoring reports and cash-flow series. **One curl is the
  whole chain.**
  **Critical:** Exa's renderer strips the hrefs and returns only the link *text*. **Fetch the
  page with curl and read the raw HTML** — otherwise the library looks like a list of titles
  with no files. Filenames are irregular and unguessable
  (`Estimates2024-2025FINALSB3july-compressed.pdf`,
  `EXPENDITURE_ESTIMATES_26-27_FINAL_DRAFT.pdf`) and the parent directory changes name between
  years (`/images/DevelopmentandBudget/2024-25/`, then `/images/2025-26/`, then
  `/images/Budget-Tables/`). **Enumerate; never guess a path.**
- **The page's own annotations are evidence.** The FY2024/25 entry prints **"(Unavailable)"**
  against all eight in-year report slots (four quarters × budget execution report + government
  operations statement). That is the state saying it did not publish them — record it as a
  dated absence, do not queue it as an acquisition.
- **THE METHOD FINDING: every Botswana estimates volume carries a prior-year actual column, so
  the outturn is recoverable two volumes later.** Each department page prints
  `Actual Expenditure to 31-03-{Y-1} | Authorised Expenditure {Y} | Estimate {Y+1}`. Therefore:
  - **appropriated** = the FY2024/25 volume's `Estimate 2024-25`
  - **revised** = the FY2025/26 volume's `Authorised Expenditure 2024-25`
  - **executed** = the FY2026/27 volume's `Actual Expenditure to 31-03-25`

  This is how a country-year with no published execution report, no annual statements of
  accounts since 2023 and an overdue audit still yields three stages. **Apply it to any
  April–March country whose volumes carry an actual column before concluding the outturn is
  unobtainable.** Caveat: it works for **recurrent only** — the FY2026/27 development half
  switched to an `Actual Expenditure (05 December 2025)` column reporting the *current* year,
  so the capital outturn is not recoverable this way.
- **Structure:** the volume has two halves with **different classification chains and different
  department names for the same department codes** — a real trap.
  Recurrent: `organisation (4-digit) → department (4-digit) → parent account → account`, a
  **line-item / economic-classification budget with no programmes at all**. Development:
  `organisation → department → project (5-digit)`, with TEC, revised TEC, two years of
  estimated expenditure, balance, and **SOF**. Department 2404 is *Digital Communications,
  Infrastructure and Business* in the recurrent half and *Telecommunications and Postal
  Services* in the development half; 2406 is *Shared Digital Services* / *Information
  Technology*; 2407 is *Technology and Commercialization* / *Research, Science and Technology*.
- **Scale: Pula, FULL UNITS throughout.** No thousands, no millions, no *en milliers*. The
  1,000× trap does not exist in this corpus. Recurrent uses commas as thousands separators,
  development uses spaces.
- **The origin gate is a printed column.** `SOF` = Source of Financing, and **every entry in
  the FY2024/25 development estimates is `DDF` (Domestic Development Fund)**. No external, loan
  or grant code appears at all. Cleaner than Burkina Faso, which prints a four-way split that
  must then be applied. **Test it at extraction against Statement 4 of the Annual Statements of
  Accounts**, which splits Development Fund sources into foreign and domestic — the volume is
  an estimate, the accounts are the check.
- **Extraction tooling:** `pdftotext -layout` gives the **offset layout** on ministry-summary
  pages (labels stack left, figures stack right) — the same failure mode as the ZAF ENE.
  Decode by summing to the printed `MINISTRY TOTAL`, which reconciles exactly. **`pdftotext
  -table` is clean and trustworthy on the development pages**, returning aligned rows including
  the SOF column. Unlike BFA (post-run note 16, archetype M), `-table` did **not** return the
  wrong year's column here — but every figure was still cross-footed against a printed total
  before use, and that check is what distinguishes the two cases. **Always cross-foot; never
  trust the extractor's column alignment on faith.**
- **Digital lines found under:** the **department** is the recordable grain, because the digital
  departments are separable from the roads and transport departments inside the same ministry.
  MCKT/MCI = organisation **2400**; digital departments **2404, 2406, 2407, 2409**. Development
  projects **11631** (Information and Communications Technology, in two departments) and
  **11637** (Research and Development).
- **Block 4b — the systematic pattern: every ministry carries its own `<Ministry>
  Computerisation` development project.** MSP, MoF, MLHA (as plain "Computerisation"), MoA,
  MESD, MTI, MoH, AoJ, MET, MoJ, MoE. FY2024/25 cross-vote total **P487,752,980 against MCKT's
  own ICT projects of P736,601,447 — 66.2%**, so the sector-vote view understates by about two
  fifths. This is the easiest cross-vote scan in the series: grep the development section for
  `Computerisation`.
- **False positive: `11551 IC Infrastructure` is INDUSTRIAL COURT infrastructure**
  (organisation 2100), not infocomms. P19,797,690 — 4% of the cross-vote total. **"IC" is not
  always information and communications.**
- **Where they hid / what is NOT there: the estimates name no systems whatsoever.** Every
  capital digital line is called "`<Ministry>` Computerisation". There is no project for the
  Omang, the population register, CRVS, passports, biometrics, the voter register, an
  interoperability layer or a single window — national identity spend sits inside **11081
  Computerisation** under MLHA Headquarters (0401), the ministry containing `0411 Department of
  Civil and National Registration`. **The `scope_basis` has to come from outside the volume**:
  the *People's Guide* names "Online Services Implementation, Government Data Network
  Expansion"; the budget speech names Village Connectivity phases 2–4 and the online-services
  count; the Committee of Supply names GABS and Vehicle Registration and Driver Licensing.
  This is coarser than ZAF's chapter narrative and much coarser than BFA's *activité* grain.
- **ANNEXURE I is the lead-generator.** *TNDP Total Estimated Cost Revisions*, at the back of
  the volume, gives per-project narrative for every TEC change **and names the destination of
  the money**. Four of the five named computerisation revisions in FY2024/25 are cuts, each
  stating a non-digital recipient: MSP −P86.4m to DPSM/NAHPA; MoF −P80m to a state-owned bank;
  MESD −P315m to SOE financing and an agricultural university; AoJ −P13m to AGC services.
- **Block 4c — the data-protection authority is not in the budget.** Zero occurrences of "data
  protection", "Information and Data", "privacy" or "Access to Information" across all 564
  pages, in the fiscal year the Data Protection Act 2024 was assented (24-Oct-2024) and
  commenced (14-Jan-2025). Two bodies created in the same wave *do* have organisations —
  `0223 Counter Terrorism Analysis And Fusion Agency`, `2800 Ethics and Integrity Directorate`.
  **The comparison is the finding**: it is not that new bodies go unfunded, it is that this one
  did.
- **Block 4c corollary — check the regulator before concluding a function is unfunded.**
  Botswana's **CSIRT is inside BOCRA** (est. 2020), own-source funded from licence and spectrum
  revenue, which is why the volume has no cyber line. BOCRA also says it has "acquired the
  necessary resources" for consumer online data protection. A function carried by an own-source
  regulator is a different governance fact from an absent one, and only the regulator's annual
  report distinguishes them.
- **Machinery of government breaks twice, both mid-series.** (1) **Government Notice No. 742 of
  2024**, after the October 2024 election, renamed MCKT to *Ministry of Communications and
  Innovation*; **department codes 2401–2409 survive, ministry names do not — join on code.**
  (2) Between FY2025/26 and FY2026/27 the plan changed from **TNDP to NDP 12**, the column
  header changed with it, **and project codes were reissued**: MCI's ICT project is `11631` then
  `12481`. Departments 2402 and 2403 disappear from MCI. **A development series keyed on project
  code needs a mapping row there.**
- **Envelope caution, and the one exception.** Ministerial totals in the *People's Guide* Table
  1 and the *Budget-in-Brief* are envelopes and are not records. But the budget speech's
  **"Innovation and Digital Transformation" thematic line (P1.83bn FY2024/25) is worse than an
  envelope — it is larger than the digital ministry's entire development budget (P1.73bn)**
  because it spans ministries. It exists in no budget document, has no vote and no programme.
  Record it, if at all, only as a stated thematic total, never as a ministry or programme
  figure. Series: **P2.62bn (FY2023/24) → P1.83bn (FY2024/25) → P1.47bn (FY2025/26)**.
- **The Budget Strategy Paper is not a proxy for the appropriation.** The FY2024/25 edition
  (Sept 2023) projected total expenditure of P88.78bn against the P102.28bn proposed five
  months later — a 15% miss. Use it for prior-year comparators and narrative, not as a stage.
- **Didn't work / not found:** the `gov.bw/publications` index returned a crawl error on one
  attempt; no Auditor-General report later than FY2019/20 surfaced anywhere (the FY2024/25 one
  was statutorily due 31-Dec-2025 and is overdue); no Annual Statements of Accounts later than
  31-Mar-2023 on the MoF's own *Publications & Reports* category; no Committee of Supply speech
  for MCKT FY2024/25 on `finance.gov.bw` (its category `id=27` holds mainly finance-ministry
  speeches and stops at 2022/23); **no Financial Paper (supplementary estimate) for FY2024/25
  at all**, though 2022/23 and 2023/24 each have three.
- **Botswana's supplementary appropriation is retrospective by about a year.** The FY2023/24
  excess (P2,062,782,860, of which MCKT P51m) was regularised by a Bill tabled April 2025. The
  FY2024/25 instrument is therefore due around April 2026 — a re-run trigger, and the only
  place an in-year overspend can surface.
- **No network workarounds needed for any Botswana host.** No DoH pinning, no TLS
  IP-pinning, no bot-guard evasion, no WPDM download manager, no DSpace API. Plain curl on the
  first attempt for `finance.gov.bw`, `gov.bw`, `npc.gov.bw`, `bocra.org.bw`,
  `bankofbotswana.bw`, `dailynews.gov.bw`. A first for this series. **One quirk:** BOCRA's 2025
  files sit under a **doubled** path segment
  (`/sites/default/files/sites/default/files/documents/…`) — copy the href, do not normalise it.
- **Trap avoided, worth recording:** `dailynews.gov.bw/news-detail/71295` surfaces on
  FY2024/25-phrased queries and reads as a current budget-allocation story naming MCKT at
  P876.20 million. **It is dated 06 February 2023 and reports the FY2023/24 budget speech.**
  DailyNews article pages carry their date only in a footer field (`Date : 06 Feb 2023`) below
  the body — **read the footer before staging any DailyNews item.**

### Botswana FY2025/26 — the supply speeches are where the systems and the execution are (sweep, 2026-07-25)

*(Second BWA run. Everything in the FY2024/25 note above still stands except the two items
explicitly corrected below.)*

- **CORRECTION TO THE FY2024/25 NOTE — the in-year capital cut was −54.3%, not −67.7%.** The
  MCKT development revised total for FY2024/25 is **P789,717,447**, not P558,033,447. The first
  reading summed the **four** departments that existed at appropriation (2404, 2406, 2407, 2408)
  and missed a **fifth created during the year**: `2409 Research and Knowledge Business`,
  project `11637`, **P231,684,000**, printed on the same page with TNDP TEC "–" and a revised
  TEC of P280,000,000. The printed `MINISTRY TOTAL` says P789,717,447, and so does the volume's
  own summary-by-organisation table. **Archetype: a department that does not exist in the
  appropriation appears in the revised column, so summing "the departments" silently
  under-counts. Cross-foot to the printed ministry total, never to the department set you
  expected.** It also changes the meaning: of the P703,959,000 taken off department 2407,
  P231,684,000 reappeared in 2409 running the same project, so combined R&D fell −48.0%, not
  −71.6%. This was a large cut **plus a reorganisation**. The FY2024/25 cross-vote figures were
  re-verified line by line and are unaffected.
- **CORRECTION — `finance.gov.bw` now bot-guards.** A default `curl` user-agent gets
  `403: Access Forbidden — Malware detected` (a Joomla WAF page, 847 bytes). **Send a browser
  `User-Agent`**; nothing else is needed. The FY2024/25 note's "no workarounds needed for any
  Botswana host" no longer holds for this one host, though it still does for `gov.bw`,
  `botswanaspeaks.gov.bw`, `dailynews.gov.bw`, `mmegi.bw` and `na.co.bw`.
- **THE METHOD FINDING OF THIS RUN: `botswanaspeaks.gov.bw` carries the per-ministry Committee
  of Supply speeches, and they are the richest budget documents Botswana produces.**
  `/category/4/parliament-business` lists a speech for **every organisation**, plus Bills and
  Extraordinary Gazettes; PDFs sit under `/media/COMMITTEE OF SUPPPLY SPEECHES/` (**three P's** —
  the directory name is misspelled). The FY2024/25 run searched `finance.gov.bw` category 27,
  found speeches stopping at 2022/23, and concluded the MCKT speech did not exist. It does; it
  is hosted by Parliament, not the finance ministry. **Check the parliamentary portal before
  concluding a supply speech is unpublished.**
- **Those speeches solve two standing Botswana problems at once.** (1) *The estimates name no
  systems* — the supply speech does: 1Gov-1Citizen, Government Data Network Expansion III,
  National Backbone Network, Government Online (e-Services), Cyber Security, the Delta Digital
  Data Centre, the Local Access Network towns by name. (2) *Botswana publishes no execution
  report* — the supply speech **is** one: section III of the MCI speech is headed "2025/2026
  Financial Year Budget Utilisation" and gives recurrent spend at 31 December and development
  spend at 12 March, in Pula and as percentages, plus **the date of the in-year revision**
  (August 2025), which no volume records.
- **The prior-year-actual-column trick was not needed this year and should not be the first
  resort.** Prefer the supply speech (direct, dated, at project grain, published within the
  year) and use the volume column for the *full-year* outturn, which arrives two volumes later.
- **`Authorised Expenditure {Y}` is NOT always a revision.** For FY2025/26 the FY2026/27
  volume's `Authorised Expenditure 2025-26` column reproduces the FY2025/26 volume's
  `Estimate 2025-26` **department by department**, because — as the 2026 Budget Speech para 125
  states outright — "recurrent expenditure estimates are maintained at their original budget
  levels". In FY2024/25 the same comparison showed a real 5.0% cut. **Test the equality each
  year; do not assume the column is a restatement.**
- **NEW EXTRACTION TRAP — a broken font on the summary pages of the FY2026/27 volume.** Pages
  11–12 (*Summary by Organisation*) extract as mojibake with the **figures dropped entirely**:
  `6800$5<%<25*$1,6$7,212)(67,0$7('(;3(1',785(…` for `SUMMARY BY ORGANISATION OF ESTIMATED
  EXPENDITURE…`, `25*` for `ORG`, `0,1,675<` for `MINISTRY`. Every other page of the same PDF
  extracts cleanly. Organisation-level totals must be built from the department pages. **A
  garbled page in an otherwise clean PDF is a font problem, not a scan — do not conclude the
  document is image-only from one page.**
- **The Appropriation Act's Schedule is offset under `-layout`**, the same failure mode as the
  ministry summary pages: organisation `0400` prints no inline amount, so labels and figures
  fall out of step from that row on and `2400` appears to carry Industrial Court's figure.
  Decode as an ordered sequence against the organisation list and cross-foot to the printed
  TOTAL. **`cabri-sbo.org` mirrors Botswana's enacted budget documents as clean text** and is
  the quickest independent confirmation.
- **The FY2025/26 Act, and the Key Features deck, are NATIVE** — both were image-only in their
  FY2024/25 editions. All 11 documents staged this run are native. **Do not assume a Botswana
  document type is image-only from one year's experience.**
- **Cross-vote scan, second year: the composition inverted.** MCI's own ICT projects fell
  736,601,447 → **369,079,545** (−49.9%) while cross-vote computerisation rose 487,752,980 →
  **557,677,600** (+14.3%), so cross-vote is now **60.2%** of Botswana's capital computerisation
  money against 39.8% in FY2024/25. **The largest single capital computerisation line in the
  FY2025/26 budget is `MCWBE Computerisation` at P270,000,000** — in the basic-education
  ministry, bigger than either MCI ICT department — then cut 85.6% with nothing spent by 5
  December 2025. The grep is still `Computerisation` plus MTI's `Information and Communications`;
  **exclude `Rural Village Electrification and Network` and `Water Supply and Sanitation
  Networks`, which the word "network" pulls in.** The FY2024/25 false positive `11551 IC
  Infrastructure` = Industrial Court does not recur (renumbered).
- **Independent corroboration route for the cross-vote scan:** the *finance ministry's own*
  supply speech prints `MOF ICT Development` at **P84,571,040** for FY2025/26 and
  **P123,172,400** for FY2026/27 — matching the volume's project `11061`/`12041` lines exactly.
  Two documents, two extraction routes, same number.
- **Machinery of government: FY2025/26 is the first volume carrying the post-election
  reorganisation in full**, and it is a bigger break than GN 742/2024's renaming. Abolished as
  organisations: `2500 Defence and Security` (into `0200`, whose recurrent vote goes P2.65bn →
  P12.55bn), `3000 Entrepreneurship` (into `0700`), **`0223 Counter Terrorism Analysis and
  Fusion Agency`**. Created: `3300 Higher Education`, `3400 Sports and Arts`, and `3500 Botswana
  Prisons Service` in FY2026/27. `11161 Computerisation` now runs under **both** `0600` and
  `3300`. **Mapping rows are needed at 2025-04-01 as well as 2026-04-01.**
- **Block 4c, resolved further: the IDPC is not unfunded, it is unlocated.** Still zero
  occurrences of "data protection", "Information and Data", "privacy", "Access to Information"
  or "cyber" in the FY2025/26 **or** FY2026/27 volumes, and no entry in the enacted Act's
  Schedule. But a parliamentary answer of 29 July 2025 establishes that the Commission **sits
  inside the Ministry for State President (organisation 0200)**, which answers for it and is
  recruiting its staff — three contract officers in post, no premises, no website, no deputy or
  directors. By 11 February 2026 it had its inaugural Commissioner (Kepaletswe Somolekae) and
  was enforcing. **A body invisible in the estimates may be inside another ministry's vote;
  check Hansard before writing "unfunded".** Note also that `0223 CTAFA`, one of the two
  same-wave comparators the FY2024/25 note used, has itself vanished from the estimates.
- **Own-source money doing appropriation's work, with a number:** the **Universal Service and
  Access Fund put P100 million into the government's Delta Digital Data Centre migration**
  (from November 2025), a BoFiNet-owned Tier III facility hosting government core systems. It
  appears nowhere in MCI's P534.9m revised development budget. **The UASF/appropriation boundary
  must be established before any Botswana digital-capital total is formed.**
- **A source can be internally inconsistent — record, don't reconcile.** MCI supply speech para
  57 gives a "remaining balance of P324,037,239" that matches neither the revised budget
  (534,894,906 − 294,278,725 = 240,616,181) nor the approved (559,629,038). The executed figure
  P294,278,725 is usable because it is stated twice, in Pula and as a percentage.
- **Aggregate cross-check that worked:** the FY2026/27 volume's development **grand total** for
  `Estimated Expenditure 2025-26` is **P22,845,850,688**, and 23,749,171,200 − 22,845,850,688 =
  **P903,320,512** — exactly the minister's stated "P903.32 million" revision. Summing the
  per-ministry `MINISTRY TOTAL` rows out of `pdftotext -table` over the whole development
  section is a cheap and reliable way to get a national denominator.
- **Contradiction opened:** the 2026/27 Budget Strategy Paper (January 2026, para 47) gives the
  FY2025/26 deficit as **P9.2bn**, total expenditure **P77.9bn** and development spending
  **P13.9bn**; the 2026 Budget Speech three weeks later gives **P25.48bn**, **P96.70bn** and
  **P22.85bn**. Use the **speech** figures — they reconcile to the estimates volume to the Pula.
  The BSP may be projecting a cash outturn; if so, the finance ministry expected to spend only
  P13.9bn of a P22.85bn development budget.
- **Botswana approved no supplementary budget in FY2024/25 or FY2025/26**, by stated policy
  (2026 Budget Speech, para 16). This **closes the FY2024/25 note's "supplementary appropriation
  is retrospective by about a year" re-run trigger** — the FY2024/25 instrument will not exist.
  Ministries absorbed pressures by reallocation instead, which is the mechanism behind the
  August 2025 digital cut.
- **The library is several Joomla categories, not one.** `id=23` Budget Documents, **`id=26`
  Budget Strategy Papers**, `id=24` Budget Pitso, `id=27` speeches (stops 2022/23). The
  FY2024/25 run enumerated only 23 and so reported the newest BSP as absent; it is in 26.
  Category 23 lists some documents (BSP 2026/27, Appropriation 2026/27 Act) as **text with no
  link** — the title appearing is not evidence the file is there.
- **Didn't work / not found:** no Mid-Year Budget Statement for FY2025/26 on any category,
  though the speech and Econsult both confirm it exists; no MCI supply speech for FY2025/26 on
  `botswanaspeaks.gov.bw`, which carries only the 2026 season; no Auditor-General report later
  than FY2019/20 (second run, second failure); no Annual Statements of Accounts later than
  31 March 2023; **the FY2025/26 in-year reports block does not even itemise the four quarters**
  the FY2024/25 block itemised and marked "(Unavailable)"; the FY2025/26 **Budget-in-Brief was
  never published** ("will be uploaded shortly").
- **Envelope trap of the year:** the US *Country Commercial Guide* (trade.gov, 8 Dec 2025)
  reports "$66.8 million (966.37 million pula)" as Botswana's FY2025/26 allocation to MCI. That
  is the **recurrent vote only** and understates the ministry by 47%, omitting the P853.9m
  development budget. **A foreign commercial guide quoting a single ministry number is quoting
  one fund, not the ministry.**

### Botswana FY2026/27 — the Financial Statements volume is the outturn and the origin gate, and the whole supply-speech season is published (sweep, 2026-07-25)

*(Third BWA run. Everything in the FY2024/25 and FY2025/26 notes above still stands except the two
items explicitly corrected below.)*

- **CORRECTION TO THE FY2024/25 NOTE — the development outturn IS recoverable, from a different
  volume.** That note concluded the prior-year-actual trick "works for **recurrent only** — the
  capital outturn is not recoverable this way", because the FY2026/27 *Expenditure Estimates*
  development half carries an `Actual Expenditure (05 December 2025)` column reporting the
  **current** year. True of that volume — but the wrong volume was being read. **`TABLE II —
  SUMMARY OF DEVELOPMENT FUND EXPENDITURE` in the *Financial Statements, Tables and Estimates of the
  Consolidated and Development Funds Revenues* gives Development Fund ACTUAL expenditure by
  organisation for 2019/20 to 2024/25**, plus revised 2025/26 and budget 2026/27, in one table.
  Organisation 2400 FY2024/25 actual = **P514,090,181** against an appropriation of P1,728,445,447
  and a revised P789,717,447 — **29.7% of appropriation, 65.1% of revised**. `TABLE I` does the same
  for the Consolidated Fund (2400 FY2024/25 actual **P844,338,028**).
  **Generalise: in an April–March country, check the revenue/financial-statements companion volume
  before concluding a capital outturn is unobtainable. It is a different document from the estimates
  volume and carries different columns.**
- **THE ORIGIN GATE IS A PRINTED NATIONAL TABLE.** `TABLE IV — SUMMARY OF FINANCING DEVELOPMENT
  EXPENDITURE`, same volume, rows **External Grants / External Loans / Domestic Loans / Domestic
  Development Fund / TOTAL**, columns 2019/20 to 2026/27. FY2026/27: DDF **23,209,795,685** of
  **23,375,815,203** = **99.29% domestic**. FY2025/26 revised 98.43%. FY2024/25 actual 80.3%, the gap
  being a **one-off P3,370,750,000 Domestic Loans** entry present in no other year. Every column sums
  exactly, and the FY2025/26 and FY2026/27 totals match the volumes and the Appropriation Bill to the
  Pula. **This is the test the FY2024/25 note asked for ("test SOF=DDF against Statement 4 of the
  accounts") and it passes at national level.**
- **NEW TRAP — `TABLE I` mixes old and new organisation definitions across its own columns and does
  not label the break; `TABLE II` does label it** (`OLD MINISTRIES 2018-2024` / `NEW MINISTRIES`,
  printed as column-group headers). So a Table I row is **not** a continuous series across 2024/25:
  organisation 0200 runs on the pre-2025 definition to FY2024/25 (2,504,894,706) and then jumps to
  12,547,724,010 when Defence merges in. **Where two adjacent tables in one volume differ on whether
  they warn you, assume the silent one is the trap.**
- **`pdftotext -table` is clean on Tables I–IV; `-layout` is offset on all four**, the same failure
  mode as the ministry-summary pages and the Appropriation Act Schedule. That is now three document
  classes in this corpus where `-layout` is unusable and `-table` is fine.
- **THE METHOD FINDING OF THIS RUN: the whole Committee of Supply season is published on
  `botswanaspeaks.gov.bw`, and it is where the systems are named and priced.** The FY2025/26 run
  found the portal and took two speeches. `/category/4/parliament-business` is a **single unpaginated
  page of 203 articles** — the pagination markup is commented out in the HTML — and it carries an
  FY2026/27 supply speech for **28 of the 29 organisations** in the Appropriation Bill's Schedule.
  What three years of 564–621pp estimates volumes never named, the season prices:
  - **identity** — MLHA `12061` Computerisation P42,019,862, of which **Electronic National
    Identification System (Biometric Omang) P31,700,000**; MLHA is also the only speech in the season
    printing **NDP 12 project codes**;
  - **voter register** — IEC *Review of Electoral Processes* **P50,000,000** = "installation of
    electronic voter registration systems"; a new **Elections Management System** was designed,
    installed and data-migrated in FY2025/26 **with no cost stated anywhere**;
  - **data exchange** — MoH **Health Information Exchange**, with a **Client Registry keyed on Omang
    or passport number** and a **Facilities Registry**, both "ready for deployment"; and MoHE
    reporting the Labour Market Information System's **completed integration with the National
    Identification System**, CIPA and the **1Gov SMS Gateway**;
  - **connectivity** — **MSP Computerization P148,200,000** covering **Village Connectivity and
    E-Cabinet**, i.e. the programme is the State President's line, not the digital ministry's;
  - **revenue-side systems** — MTI **ICT P107,000,000** for the Driver Licensing, Vehicle
    Registration & Licensing, Road Transport Permit and Road Worthiness systems, with the minister
    stating the systems are "obsolete and highly vulnerable to manipulation".

  **Enumerate the whole season, not the sector ministry's speech. In Botswana the cross-vote scan is
  a reading exercise, not just a grep of the volume.**
- **Cross-vote is 60.3% of named digital capital in FY2026/27** (P380.5m outside organisation 2400
  against MCI's own P251.0m ICT programme), after 60.2% in FY2025/26 and 39.8% in FY2024/25.
  **Speech-derived and not yet cross-footed to the volume** — the extraction pass must redo it the
  FY2025/26 way, by grepping `Computerisation` and reconciling to printed ministry totals.
- **The one speech missing is the one that matters most.** Organisation **0600 Child Welfare and
  Basic Education** has no FY2026/27 supply speech on the portal, and it held the **largest single
  capital computerisation line in FY2025/26** (`MCWBE Computerisation` P270,000,000, cut 85.6%,
  nothing spent by 5 December 2025). Its FY2026/27 development budget is P1,080,159,215.
- **Article IDs on `botswanaspeaks.gov.bw` are upload order, not delivery order.** The MSP speech of
  24 February is article 188, sitting between two March speeches. **Never date a speech from its
  position in the listing.** Nine of the twenty staged speeches print no cover date at all; those are
  month-precision and inferred.
- **A filename year is not a date, either.** The Minerals and Energy speech is filed as
  `... CoS Speech 4 MARCH 2025.pdf`; the printed cover date is **4 March 2026** and the content is
  FY2026/27 throughout. Same class of error as the DailyNews footer trap.
- **Filename encoding can defeat a fetch.** The Trade and Entrepreneurship speech is linked with a
  **triple HTML-escaped ampersand**; no unescaping variant resolved. Also, on this machine
  **`python3` is the Windows Store stub** and fails silently inside shell command substitution — use
  `python`.
- **Exa's renderer decodes the Appropriation Bill's Schedule correctly where `pdftotext -layout` is
  offset by about five rows.** Worth keeping as a last-resort decode for offset tables; it was
  cross-checked against Table I, which gives the same 29 figures independently.
- **The Bill's Schedule is recurrent only** — s.5 appropriates the Development Fund as a single
  undifferentiated sum. Development grain must come from the estimates volume or Table II. Note also
  that Botswana **gazettes the Appropriation Bill before the Budget Speech** (23 January 2026 vs 9
  February 2026), the reverse of the usual order.
- **Block 4c, fourth year, and the position finally moves.** Still zero occurrences of "data
  protection" in the FY2026/27 estimates volume **or** the Financial Statements volume — but the
  **MSP supply speech has a section headed `DATA PROTECTION`**: ~**120 organisations had designated
  Data Protection Officers by January 2026**; **"so far implementation of the Data Protection Act has
  been slow"**; an **Information and Data Protection Tribunal** is being established. **Still no
  organisation, no line, no figure** — the Commission is two paragraphs inside a P13,050,492,660
  vote. Then on **17 July 2026** it issued a **Determination and Enforcement Notice against DPSM**,
  suspending the government ePayslip portal for, among other things, **no DPIA before deployment** —
  DPSM being a directorate of the same ministry that funds the Commission. **When a body is invisible
  in the estimates, read the housing ministry's supply speech, not just Hansard.**
- **The comparator has sharpened.** `2800 Ethics and Integrity Directorate` has an organisation, a
  vote (recurrent P25,614,640), a development budget (P3,500,000, up from P800,000) **and a named
  data-governance project** — digitisation of the asset declaration system, establishing a **digital
  Register accessible to the public on payment of a prescribed fee** and designed to **interface with
  external systems**. The IDPC has none of these.
- **Cybersecurity: an Act, an Authority, and no money.** The **Cybersecurity Act, 2025 (Act 21 of
  2025)**, assent **05.11.2025**, commencement **"ON NOTICE"**, establishes a **National
  Cybersecurity Authority** with a Board, a CEO, licensing powers over cybersecurity service
  providers and power to **approve software before it is placed on the market**. It takes precedence
  over other cybersecurity law **except the Data Protection Act**. **No line for the Authority
  appears anywhere in the FY2026/27 budget**; the only priced cyber item is MCI's **P13,000,000**.
  The gazette supplement PDF also contains an unrelated anti-doping Act on its last pages — **check
  where a gazette supplement's Act actually ends before treating the file as one document.**
- **The justice estate, read across four speeches, is the clearest failure cluster in this corpus:**
  AoJ replacing a **court records system that collapsed**, with digital tools funded by **SecFin
  Africa**; the Industrial Court building its **own** court management system; the **Ombudsman's CMS
  non-operational since April 2025** with the **Digital Transformation Coordination Office**
  migrating its servers; and the Office of the Receiver's **CPAM System procurement cancelled** after
  a potential irregularity, development cut **P52,870,531 → P7,500,000 with zero spend**, and
  re-tendered (closing 27 February 2026). **Four systems, four votes, no stated interoperability.**
- **The Digital Transformation Coordination Office is a department of MCI doing work inside other
  organisations' votes** (Ombudsman servers, Transport's 1Gov-1Citizen onboarding). A
  cross-government delivery unit with no separately identifiable budget — the Block 4c coordination
  case, now evidenced.
- **Procurement, with a number at last.** The inaugural **National Procurement Pitso** (17–18 March
  2026): **78,800 tenders worth P33.5 billion in FY2024/25, 12.4% of GDP**, citizen-owned companies
  P8.7 billion (36%). Against a FY2024/25 Development Fund outturn of P18.31 billion, procurement is
  **1.8x the whole development budget**. **The PPRA states it has no real-time data on procurement
  transactions** and cannot follow a transaction between stages. The **National e-Procurement
  System** is due "beginning of 2027" off a strategy approved 17 June 2025.
- **Annual procurement plans are findable and native.**
  `statsbots.org.bw/sites/default/files/tenders/` and `botswanapost.post/sites/default/files/notices/`
  both publish s.71 plans. Statistics Botswana's FY2026/27 plan names **Microsoft Office 4 licences
  P396,000**, risk-management software licences P1,629,648, whistleblowing software, board-management
  software, and email/antivirus renewals — the same "foreign vendor named in a public financial
  instrument" pattern as Burkina Faso's MICROSOFT budget chapter, at a fraction of the scale but
  itemised. **Use `-table`; `-layout` interleaves its eleven date columns into the description column
  and drops amounts.**
- **A fourth machinery mapping row is needed at 2026-04-01:** `3500 Botswana Prisons Service` becomes
  a full organisation (recurrent **P906,692,740**), carved out of `2900`, whose recurrent falls
  **P1,015,314,690 → P153,295,560**. The Bill's Schedule now lists **29 organisations**. Botswana now
  needs rows at 2024-10-01, 2025-04-01 and 2026-04-01, plus the TNDP → NDP 12 project-code reissue.
- **`9100 Appropriations from Revenue` has never been scanned by any Botswana run** and carries
  **P23,490,555,685** — 25.7% of the Consolidated Fund. Its FY2024/25 actual was P29,966,196,024
  against P16,665,893,777 in FY2023/24, an 80% jump unexplained in any document held. **An
  unattributed cross-government systems transfer would sit here.** Lead, not a finding.
- **Three years, three chains, zero OCR.** All 25 documents staged this run are native, as were all
  11 in FY2025/26. Botswana's corpus is now entirely machine-readable.
- **Didn't work / not found:** the Appropriation (2026/2027) **Act as assented** — listed on category
  23 as plain text with no link, as in FY2025/26; the FY2026/27 **in-year reports** — the block now
  prints "will be available during the fiscal year" with **no slots itemised at all**, a regression
  even on FY2024/25's eight "(Unavailable)" slots, so Botswana has published no in-year execution
  report for any year in scope; the **IDS digital-ID country report** full text (the DOI resolves to
  an abstract; the OpenDocs record returned HTTP 202 with an empty body); **NDP 12**, still not on
  `npc.gov.bw`; **UASF and BOCRA annual reports for y/e 31 March 2026** (not due until about October
  2026 — BOCRA's *State of ICTs, 2026* covers only to September 2025 and **does not mention the Delta
  Digital Data Centre at all**, so the UASF's P100m contribution still cannot be sized).

### Botswana — first budget-extract of the FY2024/25–FY2026/27 chain (budget-extract, 2026-07-25)

*52 documents drained from `new-budget/BWA/{2024,2025,2026}`; **107 records** built, all
`domestic-state`, all `budget-document` tier. Method entry is `budget-extraction-strategies.md` →
**Archetype N** (new this run). Extracted tables in `budget-archive/BWA/`.*

- **Digital lines found under:** development-side project titles — `<Ministry> Computerisation`
  (project `11015/11061/11081/11116/11161/11212/11335/11382/11503/11832/11861` under TNDP, reissued
  `12024/12041/12061/12084/12104/12122/12244/12263/12403/12523/12562/12601/12621` under NDP 12),
  `Information and Communications Technology` (`11631` → `12481`, the digital ministry's own, and
  `11584` → `12461` in transport), and `<Body>-ICT Development` (`12362` Ombudsman, `12423` Industrial
  Court, `12523` Justice, `12562` Receiver, `12643` Prisons). Recurrent-side: department codes `2404`
  and `2406` of organisation 2400, plus small named accounts (`00442 ICT Software Licenses`,
  `01342 Health Information Systems`, `00670 Passenger Information`).
- **Language used:** "Computerisation" is the operative word and it is nearly the only one; the
  volumes say nothing else. Systems are named only in the Committee of Supply speeches.
- **Where they hid:** the entire national identity spend sits inside `0400 Computerisation` with no
  system named until the FY2026/27 supply speech priced the **Biometric Omang at P31,700,000**; the
  **voter register** has no project of its own at all and is a P50,000,000 sub-line of `12341
  Facilitation of Elections`, stated only in the IEC's speech; **Village Connectivity** is the State
  President's `12024`, not the digital ministry's.
- **False positives:** `11551 IC Infrastructure` = **Industrial Court** (P19,797,690);
  `01217 Performance Management System` = the public-service performance-management reform, present in
  ~30 departments' recurrent accounts and not an IT line; `12382 Water Supply and Sanitation
  **Networks**`; `01806 District Health Teams`; professional registration boards and councils.
- **Outturn available?** Yes, and by two routes neither of which is an execution report. Recurrent:
  the estimates volume of year N+2 carries `Actual Expenditure to 31-03-<N+1>` by department. Capital:
  **Table II of the Financial Statements volume**, by organisation, six years deep — which is how
  FY2024/25's development outturn was closed at **P514,090,181, 29.7% of appropriation**, after the
  FY2024/25 sweep had declared it unrecoverable.
- **Scope calls made:** ministry Computerisation and ICT projects → `whole` (a dedicated project, not
  an envelope). The digital ministry's `11637`/`12482` **Research and Development** → `unclear`: it is
  a project of the ministry's research departments, the volume names nothing, and the portfolio spans
  satellite, nuclear and biotechnology work — flagged, never apportioned. Organisation 2400's
  Development Fund **outturn** → `partial`, because the only grain the outturn exists at is the
  organisation, which includes radiation protection. Recurrent departments 2401 (headquarters), 2407,
  2408 and 2409 → not recorded; 2401 is the administration envelope.
- **Two figures in the sweeps corrected by the volumes.** (1) The FY2026/27 cross-vote total: the
  sweep built it from supply speeches and got **P380,519,862 (60.3%)**; the estimates volume gives
  **P895,462,597 (78.1%)**, 2.35x more, because several ministries publish no speech (0600) or do not
  name the line in it (0300, 0700, 2900, 3500). (2) The FY2025/26 cross-vote appropriated total is
  **P566,428,606**, not P557,677,600 — the sweep read `3400 MoSA Computerisation` P8,751,006 as having
  no appropriation when the volume's `2025-26` column carries it; and the revised total is
  **P300,336,741**, not P287,024,103, once `12523` MJCS, `12562` OTR and `12643` Prisons are included.
  Also: the supply speech's Office of the Receiver "P24,564,988" is the **department** total, of which
  the ICT line is P4,564,988 and infrastructure P20,000,000.
- **Didn't work:** nothing. All three volumes are native and `pdftotext -table` read every table used;
  the only two image-only documents in the corpus (the FY2024/25 Appropriation Act and Key Features
  deck) were not needed, because the Act's organisation totals are reproduced in the volume's own
  summary and the deck duplicates two native siblings. **Three country-years, 52 documents, no OCR.**

### Botswana — NDP 12 acquired, and what a Public Investment Programme adds (budget-extract iteration 2, 2026-07-25)

- **Route (the correction to two runs' "not located on npc.gov.bw"):** `npc.gov.bw/publications` links
  NDP 12 as a **Google Drive folder**, not a file. Parse the folder page for its file IDs
  (`aria-label="<name>.pdf"` with `data-id` in the preceding markup) and fetch each through
  `https://drive.usercontent.google.com/download?id=<id>&export=download&confirm=t`. Three parts:
  I narrative (191 pp, image-only), **II Public Investment Programme (109 pp)**, III indicator framework.
- **The PIP is the naming layer the estimates volume lacks — and a third one.** Botswana now has three:
  the **volume** carries the money at `<Ministry> Computerisation` grain; the **Committee of Supply
  speech** names the year's major sub-lines; the **PIP** names *every* project in the plan. For the
  digital ministry it lists **24 ICT projects and 20 research projects** — including *Government
  Integrated Data Centre*, *Enterprise Architecture*, *Aggregation of Citizen Identifiers*, *Digital
  Signature Infrastructure*, *API Management and Licensing*, *National eService Integrity Nexus*, *SIEM*,
  *Land & GIS Management System*, *Documents and Records Management Systems* and *AI Policy development* —
  none of which is nameable from any estimates volume. **Where a country's budget names nothing, look for
  the development plan's PIP, not just the supply speech.**
- **The PIP's tables are images and its digits do not survive OCR.** `--force` was needed (the file has a
  thin heading text layer that fools the text-layer check). Prose and project names come back clean;
  cluster and year totals do not cross-foot (ICT cluster ongoing 327.0 + 94.7 + 181.7 + 180.3 = 783.7
  against a printed 1,707.1) and were **not recorded**. Only per-project TECs where the printed
  `Total = Ongoing + New` were carried, and only as plan context — **plan-period figures build no record**
  (driver → *Budget stage*), so nothing here becomes a finance record whatever the OCR quality.
- **Didn't work:** the PPRA's per-ministry annual procurement plans. `ipms.ppadb.co.bw/openProcumentPlan`
  is a genuine live search over every procuring entity's plan, but its year/ministry/department selects
  are built client-side and a plain fetch returns an empty `<option>` template. It is the only route to
  line-level Botswana procurement and is worth a browser session if one is ever run.

### Central African Republic — a complete chain that is entirely a scan (sweep, 2026-07-25)

- **Fiscal year:** calendar. The Budget Citoyen states it: *"L'exercice budgétaire s'étend du 1er janvier au 31 décembre."* Document label `2024`.
- **`finances.gouv.cf` is the easiest Track-B target in this corpus so far.** One fetch of `/documentations` returns a **single 300-row HTML table for the entire library** — date, category, title, size, and direct `sites/default/files/YYYY-MM/…` links — with **no pagination, no JS shell, no bot guard, no DNS/TLS trouble, and a default curl UA accepted**. Also fetch the per-category pages (`/finances/les-lois-de-finances-ldf`, `/finances/execution-budgetaire`, `/marches-publics/plans-de-passation-des-marches`): a *single* `/documentations` row can conceal up to 22 separate file links, and only the category page exposes them all.
- **The filenames and posted dates lie — trust the title page.** The FY2024 finance law sits under a `2024-03/` path with a `2024-01-05` display date. The parapublic performance report whose internal title is **2023-2024** is filed as `RAPPORT ANNUEL DE PERFORMANCEOK 2025.pdf` under `2026-05/`. Neither error is recoverable from the URL.
- **OCR is the binding constraint, not availability and not access.** CAR publishes appropriated, revised *and* a full four-point quarterly execution series, on its own site, on time — and **17 of 19 documents staged are page-image scans with 0 extractable characters**, including the 675pp Loi de Finances 2024 (187 MB) and the 717pp Collectif 2024 (164 MB). The rectificative is *longer* than the initial law, so it restates the estimates line for line rather than listing movements: appropriated and revised are directly comparable once OCR lands.
- **The only native documents in the whole FY2024 chain** are the 14pp **Budget Citoyen** (aggregates, printed *en milliers de FCFA* for the régie tables), the PND-RCA 2024-2028 (UN mirror), and the MFB's parapublic performance report. Everything else is a scan.
- **The origin gate is a printed column.** The DGMP's *Situation générale des marchés aboutis au contrat au titre de l'année 2024* is a 13-page landscape table, one row per contract, with a ***Mode de financement*** column carrying **`Fonds Propres`**, plus contract number and date, object, vendor, beneficial owner and **Montant du Marché (F CFA) in full units**. Same property as Botswana's printed `SOF`. This single artefact is what converts CAR's opaque means-based vote into named, priced, origin-tagged digital purchases — already legible through the scan: *Fourniture de Connexion Internet par Satellite au profit du MFB* (N°0455 du 05/04/2024), *Renforcement de Circuit de Transmission des Données* (TAZOUN TELECOM CENTRAFRIQUE), *Installation des Kits VSAT*, a surveillance-camera lot, and a Ministère du Genre *Digitalisation* line. **Take this document first on any CAR run.**
- **FY2024 is a *budget de moyens*, not a budget-programme.** The Budget Citoyen says the government intended to switch **from 2025** — so do not look for programme structure or *projets annuels de performance* in FY2024. The compact statement of the vote vocabulary in force is **Arrêté n°1099 du 13-Nov-2023 fixant la liste des programmes et des dotations budgétaires** (3pp, scan, names *l'Economie Numérique*): fetch it as the codebook whenever the volume is unreadable.
- **The audit stage does not exist and will not soon.** The *Lois de Finances* library carries lois de règlement for **2016, 2017, 2018 and 2019 only** — the 2018 and 2019 ones posted on **11 November 2025**. The most recent settled accounts are for exercice **2019, six years late**. The Cour des Comptes (loi n°97.003 du 12 mai 1997) publishes nothing findable and has no reachable site. **The REB 4ème trimestre is CAR's outturn**, unaudited.
- **Digital lines found under:** nothing at all on the sector side. No FY2024 figure for the Ministère de l'Economie Numérique surfaced anywhere, and **the DGMP published no procurement plan for it** among the 22 posted on 07-Mar-2024. The spend lives in the finance ministry (Sim_Ba, e-Tax, eTVA, SYDONIA World, SYGADE, Girafe payroll, Pata paye mobile-money salaries, Pata polele — all named on the record by their project leads in Africa24's 12-Jul-2024 reportage, **none carrying a published appropriation**) and in the electoral register.
- **Every named digital financing in FY2024 is external.** UNDP US$600k (2023) then **US$1.6m (08-Apr-2024)** for the four platforms and the e-cadastre; France's **€10m budget support (13-Nov-2024) with 3.28 bn FCFA flagged onto Si_mba, SYDONIA World and e-TAX**; the World Bank PGNSP underneath. The electoral register likewise: EU €2m, MINUSCA US$1,341,727, Cameroon 250m FCFA, Canada US$75k, all pooled in the UNDP-managed PAPEC basket. **The domestic share visible anywhere in FY2024 is a 300,000,000 FCFA government advance to the ANE**, which the ANE reports as late and partial.
- **Malformed printed amounts are common in CAR reporting — carry them verbatim.** The ANE's submitted enrolment budget is printed `13.32.400.200 FCFA`, well-formed under no thousands convention; Cameroon's contribution is printed `250 000 000 millions F CFA`. Do not normalise either without a second source.
- **Block 4c — the finding.** FY2024 is the year CAR legislated its entire digital-governance architecture: **Loi n° 24.001 on personal data protection** (mid-Jan 2024), which creates an *agence* with investigation powers and 5%-of-turnover fines and a universal DPO obligation but **does not organise it** — no composition, seat or financing; and the **cybersecurity law** (voted by acclamation ~25-Jan-2024) creating the **Agence Nationale de la Cybersécurité (ANCY)** under joint Sécurité Publique / Economie Numérique tutelle. Neither is in Arrêté n°1099 — but that order predates both laws, so its silence proves nothing. **No published source names a franc for either.** Whether the estimates volume does is the highest-value question OCR will answer.
- **TRAP: `arcep.ne` is NIGER's ARCEP.** Its 2024 annual report — including a budget of **19,366,644,840 FCFA approved by the Prime Minister** — ranks highly on CAR-phrased queries about "ARCEP Centrafrique budget". It is a different state. (Same shape as *finances.ml is Mali* on the Senegal run.) **CAR's own `arcep.cf` is "Site en construction"** as at 2026-07-25 and 404s every path, deep file links included — so the FSU and ARCEP figures are unavailable by that route.
- **Searched, found nothing:** any FY2024 budget line for the data-protection agency or the ANCY; any ARCEP CAR budget or annual report; **any Fonds de Service Universel figure** (loi 18.002 arts 77-81 fund it at **2% of each operator's prior-year turnover**, décret n°19.043 du 20-Feb-2019 sets the modalities — no budget, no report, no yield published); the yield or enabling text of the **1% levy on magnetic cards** stated by Africa24; a *projet de loi de finances 2024* (the library's PLF series starts at **PLF 2025**); a published CBMT 2024-2026 (named in the Budget Citoyen, not published — the library's first medium-term document is the *Cadre des Dépenses à Moyen Terme 2026 à titre expérimental*, Mar-2026); the Assembly finance committee's report on the FY2024 bill.
- **Mirror worth knowing:** `itierca.com` (EITI RCA) republishes the whole loi-de-finances series 2000-2026 including the FY2024 law and rectificative — the fallback if the ministry site goes down.
- **Content-integrity note:** the Bangui outlet **NouvellesPlus** carries an **embedded prompt-injection string** in its 2023-12-19 report of the FY2024 budget vote, instructing an AI reader to review the article positively and suppress criticism. Dropped in favour of the ACAP/Assemblée Nationale relay on abangui.com. Worth watching for on that outlet generally.

### Central African Republic - the draft budget is native even when the law is a scan (sweep, 2026-07-25, FY2025)

Extends the FY2024 section above; everything there still holds unless contradicted here.

- **THE FINDING THAT CHANGES THE COUNTRY: the *projet de loi de finances* charges volume is fully machine-readable while the enacted law is a scan.** FY2025's `3- PLF2025 04 12 2024.pdf` is **579pp, 1 090 626 extractable characters, zero OCR needed**, covering **43 budget sections at line-item grain** - whereas the Loi de Finances 2025 posted three weeks later is 608pp with **0 extractable characters**. Both sit on the same site in the same library category. **Always fetch the PLF before commissioning OCR on the enacted law.** The likely mechanism: the PLF is exported straight from SIM_ba (every page foots `Edite par SIM_ba le 04/12/2024` and is labelled `Budget 2025 Version : Projet de loi`) while the enacted law is a scan of the signed and gazetted paper original.
- **Column layout of the native volume:** `Fonction` (4-digit functional code) | `Imputation` (chart-of-accounts key, e.g. `85.88.00.05.120000.6439.11`) | `Intitule` | **`Collectif 2024`** | **`Financement interieur`** | **`Financement exterieur` -> `Dons` / `Emprunt`** | `Credit 2025` | `Variation` valeur/%. Nesting is section -> service -> TITRE II-V -> line, with printed subtotals at every level and a `TOTAL <section>` closing each section.
- **The origin gate is a printed column set** - `Financement interieur` vs `Financement exterieur (Dons | Emprunt)` beside every line. Same property as Botswana's printed `SOF` and Burkina Faso's *Etat Seul / Contrepartie / Subvention / Pret*. CAR is the third such case in this corpus, but Francophone and at the **proposed** stage rather than the appropriated one.
- **Scale is `milliers de FCFA`, printed in the header.** The 1 000x trap, live.
- **Extraction method, and its limit.** Plain `pdftotext` destroys row-to-amount association. `pdftotext -layout` reconstructs the columns legibly, **but rows still drift one or two positions inside the transfer blocks**, and free-text activity labels ("Appui a l'ARCEP", "Agence Centrafricaine du Developpement du Digital (ACDD)") sit on their own lines and cannot be bound to an imputation from the text stream at all. **Section totals and TITRE subtotals cross-foot and are safe; individual transfer amounts are not.** Bind labels from the rendered page. Archetype M applies - locator only until cross-footed, the same lesson as BFA post-run note 16.
- **A worked cross-foot, for calibration.** Section 85 (digital ministry) FY2025: TITRE II 541 826 + III 293 750 + IV 3 000 000 + V 100 000 = **3 935 576**, matching the printed section total exactly. The Collectif 2024 column sums to 3 467 589 against a printed 3 467 588 - a one-unit rounding difference, which is the tolerance to expect.
- **The digital ministry is a pass-through.** FY2025: **76% transfers, 14% personnel, 7% goods and services, 2.5% investment** - FCFA 100 million of investment for the whole ministry, all `Financement interieur`. Named transfer beneficiaries, **bound and cross-footed by budget-extract 2026-07-26** (Credit 2025, milliers): the unlabelled 85.84.00.75 line 250 000; **V-care 500 000**; **ARCEP 1 400 000**; **ACDD 200 000**; **SOCAPOST 380 000**; **SOCATEL arrears 250 000** - summing to the printed TITRE IV subtotal 2 980 000 exactly. **[Corrected 2026-07-26: this bullet originally gave ARCEP as "500 000, flat year on year". That is the V-care line. See post-run note 28.]** Do not read the ministry's envelope as digital spend; most of it leaves immediately.
- **Cross-vote seams, located by section:** **14** Administration du Territoire (*Projet de soutien a la modernisation de l'etat civil*, *Projet d'appui au processus electoral*, Direction de l'Etat Civil et de la Demographie); **30** Finances (*Projet de numerisation de l'administration publique*, SYDONIA World deployment and migration, *Appui a la Digitalisation*); **32** Fonction Publique (Direction du Systeme reseau, de l'Interconnexion et de la Telematique); **60** Sante (*Appui a la digitalisation du systeme de sante*); **50** Communication (*Numerisation des archives audiovisuelles*). **Section 10 is the ANE itself**, carrying entries in both the domestic and the external columns.
- **Block 4c, settled from the primary: `cyber` occurs ZERO times in 579 native pages, and no data-protection or cybersecurity body appears under any wording.** Two years after CAR legislated a data-protection agency (Loi n 24.001) and the ANCY into existence, its own complete draft budget names neither. **[Corrected 2026-07-26 by the FY2026 run — this bullet originally also claimed `donnees` occurs zero times. It does not: `donnees` occurs 12 times in the FY2025 volume and 13 in FY2026. The zero was an artefact of reading `pdftotext`'s Latin-1 output as UTF-8, which replaces every accented character and makes any accented search term unmatchable. Always extract with `pdftotext -enc UTF-8`. The 12 hits are ordinary data handling — a data-entry room, statistical collection, `Centre de Donnees Forestieres`, `Direction de Gestion Integree des Donnees` — none a data-protection body, so the conclusion stands on the corrected evidence. See post-run note 26.]** The only *Agence* entries are Developpement Agricole, **Developpement du Digital**, Centrafrique Presse, Comptable Centrale du Tresor, Investigation Financiere, Developpement de l'Elevage, Eau et Assainissement, Judiciaire du Tresor and an IAEA contribution; the only *Autorite* entries are the Haute Autorite chargee de la Bonne Gouvernance and the ANE. **ARCEP is not a budget section** - it exists only as a transfer object. This converts the FY2024 "searched, found nothing" into evidence of absence.
- **New body to track: the Agence Centrafricaine du Developpement du Digital (ACDD)**, a named transfer beneficiary under section 85, validated in the *Centrafrique Digital 2028* strategy (Aug-2022) and listed among completed reforms in 2025 - **with no creating instrument located**. Until its mandate is known the single-mandate carve-out cannot be applied to its transfer.
- **FY2025 is still a *budget de moyens*.** Most lines read `Pas de Programme / Activite generale`. The Budget Citoyen 2024 said the switch to budget-programme would come "from 2025"; **it did not.** The Plan e-Finances publiques (Mar-2025) still lists "preparer la bascule en budget-programme" as a *structural* action out to 2027.
- **Track B, updated.** `/documentations` still returns the whole 300-row library in one fetch with a default UA, no pagination and no bot guard. Fetch the category pages too - this year their value was **negative evidence**: the *Plans de passation des marches* category proved there is **no 2025 procurement-plan batch at all** (23 files for 2024, 15 for 2026, nothing between), and *Avis d'attributions* proved only an **H1-2025** contract-award table exists where FY2024 got a full year. **The filenames still lie**: the single most important document in the FY2025 chain is named `3- PLF2025 04 12 2024.pdf`.
- **The Budget Citoyen contradicts itself.** The FY2025 edition gives external resources as **160,20 mds** in one place and **131,34 mds ("45,00% des recettes totales")** a page later, while its own components (27,30 + 125,40 + 7,50) sum to 160,20. Its deficit of **20 717 975 000 FCFA** is exactly 365,92 - 345,20 and is self-consistent; the Assembly-floor report of the same vote gives 26,02 mds and external resources of 162,20 mds. Treat the difference as one of basis and say which, rather than opening a brief.
- **A Sango-language Budget Citoyen is published alongside the French one** (same day, same library row, `BD VSango.pdf`). Same figures - but the fact of national-language publication is itself a budget-transparency finding.
- **Own-source, updated:** the **Fonds de Service Universel's governance organ finally exists** - the CDCE's activities were launched in **July 2025**, closing the FY2024 "committee never formed" finding; implementation is targeted for 2026 and **no collected amount, balance or allocation has ever been published**. **ARCEP's own draft budget is 6,2 mds FCFA (about US$11.2m), presented 15-Apr-2026**, against a state *appui* of 0,5 mds - roughly 8% state-funded. `arcep.cf` is still "Site en construction" and 404s every path.
- **Domestic origin, reversed from FY2024:** the ANE's president stated on 17-Dec-2025 that **the government carried three quarters of the election budget**, with an exceptional contribution of **US$7.8m** to the UNDP-managed PAPEC basket alone. **No total is stated anywhere**, so the domestic figure cannot be derived - the denominator is the acquisition.
- **A fourth financing mode: vendor pre-financing.** The Dunia platform at the MEPCI (launched 23-Feb-2026) was built by the Central African firm **EDEN TiiiT**, whose principal **pre-financed the earlier phases from his own funds** with no stated recovery mechanism. That leaves no trace in an appropriation *or* a donor ledger - worth looking for elsewhere in the corpus.
- **Provenance note:** **Pravda RCA** (`rca.news-pravda.com`) is Bangui-datelined with named reporters but sits in the Russian state-linked Rossiya Segodnya / Sputnik network. Usable as first-hand reporting where no alternative exists, but the alignment must travel with the citation. **NouvellesPlus remains unused** per the FY2024 prompt-injection finding.

### Central African Republic - the budget is published twice, and only the powerless copy explains it (sweep, 2026-07-26, FY2026)

Extends the FY2024 and FY2025 sections above; everything there still holds unless contradicted here.

- **The native-PLF finding is structural, not a one-off.** FY2026 repeats FY2025 exactly: the enacted **Loi de Finances 2026 is 624pp / 137 MB with 624 extractable characters** (a scan), while the **projet de loi is 602pp and fully machine-readable** (1 343 916 chars, zero OCR), same SIM_ba export, same 43 sections, same printed `Financement interieur` / `Financement exterieur (Dons | Emprunt)` origin columns, same `milliers de FCFA` scale. FY2026 improves on FY2025 in one respect: the PLF is **one file** where FY2025 needed three. **Fetch the PLF before commissioning OCR on the enacted law** is now a two-year rule for this country.
- **NEW DOCUMENT TYPE, and the most valuable artefact CAR has produced: the *Cadre des Depenses a Moyen Terme sectoriels 2026 a titre experimental*** (posted 24-Mar-2026, footer `Imprime, le 22/12/2025`). Its running head is **`BUDGET DETAILLE PAR ACTIVITE`**; it is **183pp, native (735 958 chars)**, and it is **CAR's budget-programme** - `PROGRAMME (5 digits) -> ACTION (7) -> ACTIVITE (19)`, with **AE and CP columns for 2026, 2027 and 2028**. The Budget Citoyen 2024 promised the switch "from 2025" and the FY2025 run established it had not happened; this is where it arrives, **in a document published `a titre experimental` with no legal force**. **Scale differs from the PLF: full francs, not milliers.**
- **The two volumes reconcile to the franc**, which is what makes both usable: section 85 CP 2026 = `5 548 540 000` in the CDMT = `5 548 540` milliers in the PLF. The CDMT cross-foots exactly at every level (programmes 85082 + 85083 + 85084 = the section total; each action = the sum of its activities). **Nothing in the CDMT is a locator - it is the first CAR budget document whose figures are cross-footed and safe.**
- **ARCHETYPE M IS SOLVED FOR THIS CORPUS, and the fix is page geometry.** FY2025 recorded that free-text activity labels "cannot be bound to an imputation from the text stream at all". They can be bound from word bounding boxes. Read with `pdfplumber.extract_words()`, group by `top` into rows, and the SIM_ba layout is unambiguous: **x~34 `Fonction` | x~60 `Imputation` | x~79 the programme/activite LABEL column | x~177 `Intitule` | x>=430 the amounts**. The rule is that **a label at x~79 belongs to the imputation row immediately BELOW it**. `pdftotext -layout` interleaves those three left-hand columns unpredictably; the coordinates do not. **Verified, not assumed:** every transfer bound this way in section 85 matches the corresponding CDMT activity to the franc, and the eight TITRE IV lines cross-foot to the printed subtotal 4 438 000 exactly. Apply this to every Francophone SIM_ba volume.
- **ALWAYS EXTRACT WITH `pdftotext -enc UTF-8`.** `pdftotext` emits Latin-1 by default. Reading that as UTF-8 replaces every accented character, so **any accented search term silently returns zero** and the zero looks like a finding. This corrupted a headline of the FY2025 run (`donnees` reported as 0 occurrences; the true count is 12). Unaccented terms such as `cyber` are unaffected, which is exactly what makes the failure hard to notice. **Corroborate any "zero occurrences" claim with an unaccented term or a whitespace-collapsed phrase test before publishing it.** Post-run note 26.
- **The digital ministry FY2026: the vote grows and the ministry shrinks.** Section 85 rises **+29,33%** to 5 548 540 milliers (FCFA 5,549 bn), **100% `Financement interieur`** - while **TITRE V investment falls 30,00% to 70 000 milliers (FCFA 70 million)** and **transfers reach 80,4% of the vote (4 463 000)**. The pass-through shape found in FY2025 has intensified. **[Corrected 2026-07-26: originally "falls 66,00% to 34 000 milliers". 34 000 is the *Cabinet du Ministre* service block; the section recapitulation on PLF p. 515 gives TITRE II 727 790 / III 287 750 / IV 4 463 000 / V 70 000, which cross-foots to 5 548 540 exactly, and the CDMT's independent AE total of 70 000 000 full francs confirms it. **The lesson: read the printed `TOTAL <section>` recapitulation page, not the first service block.** See post-run note 27.]**
- **The transfer beneficiaries, bound and confirmed (CP 2026, full FCFA):** ARCEP **1 600 000 000** (against 500 000 milliers proposed for FY2025); **V-care 1 000 000 000** (+25%); **Mossi 500 000 000 (NEW - a private company named nowhere else)**; SOCAPOST 390 000 000; SOCATEL telephone arrears 250 000 000; **ACDD 300 000 000**, which the CDMT reveals is for `Construction des boucles optiques urbaines`; and **`Paiement des arrieres de six (06) mois de salaires de 2024 (ACDD)` 118 000 000 - the agency went half of 2024 without paying staff.** Two private companies' invoices (1,5 bn) are **44x** the ministry's entire investment budget.
- **Block 4c, restated on corrected evidence and sharper for it.** `cyber` = **0** in both volumes; `protection des donnees` = **0** on a whitespace-collapsed test; `ANCY`, `biometr`, `identite`, `interoperab` = **0**. But **the CDMT does budget this territory**: action `8508302 Renforcement de la securite des reseaux et systeme d'Information` = **FCFA 4 000 000** and programme `8508304 Renforcement de la confiance numerique au niveau national` = **FCFA 2 000 000**, for the year, for the country - against **FCFA 1 600 000 000** transferred to ARCEP from the same ministry, a ratio of about **267:1**. The finding is no longer "absent" but "priced at about US$10 500 a year".
- **The statutory deadline is the clincher, and it is in the law itself.** Loi n 24.001's transitional article gives the digital ministry **twelve months from promulgation** to establish the data-protection agency, and provides that meanwhile "les missions qui lui sont devolues sont assurees par le Ministere de tutelle". Promulgated January 2024 -> deadline **January 2025**. The agency is **eighteen months overdue** and unbudgeted across three consecutive years of estimates, with its 5%-of-turnover sanction power sitting in the ministry it was meant to be independent of. **A working mirror of the law text is `blog.africadataprotection.org` (5,85 MB, native, 50 670 chars)** - `arcep.cf` hosts a copy per Exa's index but 404s on live fetch.
- **Cross-vote, FY2026 (CP 2026, full FCFA):** section 30 **`Deployer SydoniaWorld au Terminal 3` 420 000 000** (the largest cross-vote digital line, and bigger than the digital ministry's entire non-transfer spend); section 31 `Fonds de Developpement de la Statistique` 175 000 000 and `donnees pour la Consommation (IPC)` 40 000 000 (**-50% on 2025**); section 32 `Digitalisation de l'administration et innovations numeriques` 16 000 000; section 50 `television numerique` 30 000 000, `systeme d'archivage` 30 000 000, `site internet de l'ACAP` 9 000 000; section 40 `Digitalisation du systeme educatif` 6 000 000; section 92 `Numeriser les archives` 8 000 000; section 83 `cadastre minier` 625 000 and `base de donnees petrolieres` 650 000.
- **A silent label change to watch:** imputation `01.00.00.00.240010` (Presidence) reads `Direction de l'Administration de Base de Donnees` in FY2025 and **`Direction des Statistiques et de Digitalisation` in FY2026**, at the same 3 000 milliers. Same code, new name - a series break for anyone keying on labels rather than codes.
- **The origin-gate artefact has not been published for eighteen months.** The DGMP *Situation/Tableau des marches aboutis au contrat* - the FY2024 run's "take this document first", carrying a printed *Mode de financement* column - stops at **H1-2025**. `marches-publics/avis-attributions` shows no full-year 2025 table and no 2026 table.
- **The FY2026 procurement-plan batch is a transparency regression.** 15 files posted 24-Feb-2026, **all image-only**, and named `numerisation0001.pdf` ... `numerisation0015.pdf` - the scanner's own output - so **not even the procuring entity is identifiable without OCR**. FY2024's batch named the ministry in each filename. (There was **no 2025 batch at all**.) OCR page 1 of each and rename before anything else.
- **Track B, unchanged and still the easiest in the corpus:** one fetch of `/documentations` returns the whole 300-row library, no pagination, no bot guard, default UA accepted. Category pages still earn their keep negatively. **The filenames still lie** - this run's most important document is posted as `Cadre des Depenses a Moyen Terme 2026.pdf`, which reads like a routine framework note and is a 183-page programme budget.
- **`arcep.cf` is still down.** Re-tested 2026-07-26: root returns "Site en construction", every path 404s including deep file links. An Exa result appeared to serve a PDF from `arcep.cf` - that is Exa's crawl cache, not a live route. **The minister's 30-Jan-2026 address explains the outage: the ARCEP's institutional website is a World Bank-financed project not yet delivered.**
- **New bodies to track:** the **ANECI** (creation process, named in the minister's 30-Jan-2026 address, expansion unknown, appears nowhere else in this corpus) and the **USCCE** (Unite speciale de controle des communications electroniques, directed to raise public revenue from its equipment).
- **Two unpriced vendor programmes, neither visible in any appropriation:** **Huawei** (26-May-2026 - Tier III national data centre, five faisceaux-hertziens interconnection sites, IP telephony, and an **eLTE radio network for army, police and gendarmerie**) and **Greenline Technologies / SOCATEL** (protocole d'accord Sept-2025, confirmed 16-Jul-2026, **US$150m**, including a Tier 3 data centre). **Two national Tier III data centres announced eight weeks apart by different routes** - do not assume they are the same facility. What the budget actually carries for SOCATEL is 250 000 000 FCFA of the administration's unpaid phone bills.

### Central African Republic — first budget-extract of the FY2024/FY2025/FY2026 chain (budget-extract, 2026-07-26)

Drained all three country-years (54 documents, 1.07 GB) against the three native volumes.
Everything below is cross-footed against a printed subtotal before it was recorded.

- **THE ORIGIN GATE IS IN THE ACCOUNT KEY, not only in the columns.** Beside the printed
  `Financement interieur` / `Financement exterieur (Dons | Emprunt)` column set, **the last
  segment of the imputation encodes the same fact**: `.11` = domestic, `.25` = grant,
  `.44` = external loan. Tested over **10 898 imputation rows across the FY2025 and FY2026
  volumes**, the two agree with **no exceptions** (5 115 + 4 691 `.11` rows all carry an
  interieur figure; 190 + 198 `.25` rows all carry a Dons figure; 22 + 25 `.44` rows all
  carry an Emprunt figure). This is stronger than a printed column because it survives on a
  single line: any CAR document that prints an imputation states its own funding origin.
  **Check it on the next francophone SIM_ba state before generalising.**
- **A whole-state origin split falls straight out of it.** Summing the line columns:
  FY2025 **interieur 232 968 525 / dons 125 400 000 / emprunt 7 500 000** milliers, and
  FY2026 **263 954 629 / 125 400 000 / 7 000 000**. Both reconcile exactly to the sum of the
  `Credit` column (365 868 525 and 396 354 629 milliers). **The Central African Republic
  proposes to finance 63,7% of its FY2025 budget and 66,6% of its FY2026 budget from its own
  resources**, and external grants are flat at 125,4 bn milliers in both years.
- **THE PRIOR-YEAR COLUMN CLOSES A YEAR NOBODY CAN READ.** Every SIM_ba volume prints the
  preceding year's **enacted collectif** as its comparator column — `Collectif 2024` in the
  FY2025 PLF, `Collectif 2025` in the FY2026 PLF. Both collectifs are image-only scans of
  600+ pages. **So the FY2024 and FY2025 *revised* stages are recoverable natively, without
  OCR, from the following year's draft budget.** This is archetype N's prior-year property
  (Botswana) appearing in a francophone LOLF volume, and it is what let this pass state a
  FY2024 figure for a ministry the FY2024 sweep could find no figure for anywhere. The
  columns cross-foot to their own printed subtotals.
- **READ THE PRINTED `TOTAL <SECTION>` RECAPITULATION PAGE, NOT THE FIRST SERVICE BLOCK.**
  The costliest error of this chain. Each section chapter opens with the *Cabinet du
  Ministre* block, whose TITRE lines look exactly like section totals and are not; the real
  recapitulation is the **last page of the chapter** (`TOTAL 85 MINISTERE…` then `Total
  chapitres`). Section 85 FY2026: Cabinet TITRE V = 34 000, **section TITRE V = 70 000**.
  The tell was available and missed — the Cabinet TITREs sum to 5 061 250 against a stated
  section total of 5 548 540. **A table that does not cross-foot is not a table you may
  publish.** Post-run note 27.
- **Section 85 recapitulations, cross-footed (milliers de FCFA):**

  | TITRE | Collectif 2024 | Credit 2025 | Collectif 2025 | Credit 2026 |
  |---|---|---|---|---|
  | II Charges de personnel | 632 581 | 541 826 | 496 590 | 727 790 |
  | III Biens et services | 223 758 | 293 750 | 293 750 | 287 750 |
  | IV Transferts | 2 475 000 | 3 000 000 | 3 400 000 | 4 463 000 |
  | V Investissement | 136 250 | 100 000 | 100 000 | 70 000 |
  | **TOTAL** | **3 467 588** | **3 935 576** | **4 290 340** | **5 548 540** |

  *(The FY2024 column sums to 3 467 589 against a printed 3 467 588 — a one-unit rounding
  difference, and the tolerance to expect. Every other column is exact.)*
- **The transfer series, bound by page geometry and confirmed against the CDMT** (milliers):

  | Imputation | Beneficiary | Coll. 2024 | Cred. 2025 | Coll. 2025 | Cred. 2026 |
  |---|---|---|---|---|---|
  | 85.88.00.20 | **ARCEP** | 1 300 000 | 1 400 000 | 1 400 000 | 1 600 000 |
  | 85.88.00.05 | **V-care** (private) | 500 000 | 500 000 | 800 000 | 1 000 000 |
  | 85.88.00.21 | **ACDD** | 50 000 | 200 000 | 300 000 | 300 000 |
  | 85.88.00.22 | SOCAPOST | 350 000 | 380 000 | 380 000 | 390 000 |
  | 85.88.00.23 | SOCATEL arrears | 100 000 | 250 000 | 250 000 | 250 000 |
  | 85.88.00.24 | ACDD 2024 salary arrears | — | — | — | 118 000 |
  | 85.88.00.27 | **Mossi** (private) | — | — | — | 500 000 |

  **The ACDD's transfer rose sixfold in two years while the agency went six months of 2024
  unpaid.** The two private companies' invoices reach FCFA 1,5 bn in FY2026, **21 times the
  section's entire investment title** (not 44x — that figure used the Cabinet block).
- **THE IDENTITY SEAM IS 100% DONOR-FINANCED, and the gate says so on the page.** The
  *Projet de soutien a la modernisation de l'etat civil en Republique Centrafricaine*
  (section 14, imputations `14.14.00.42.120000.*`, all suffix `.25`) carries **120 000 +
  840 000 + 240 000 = 1 200 000 milliers, entirely in the `Dons` column, in both FY2025 and
  FY2026**. Not one franc of domestic money. The finance ministry's *Projet de numerisation*
  (`30.31.00.09.120000.*`, suffix `.25`) is likewise **200 000 milliers of Dons** in both
  years. **Neither is a record**: the volume names no funder beyond "Dons", so they fail the
  spec's fact 1 (driver → *Origin*). They are stated on the place hub as dated findings
  instead, and they are the sharpest thing this chain produced — CAR's civil registration is
  built with other people's money, in a state that finances two thirds of its own budget.
- **Cross-vote, and the finance ministry beats the digital ministry.** The largest single
  domestic digital line in the FY2026 budget is section 30's `Deploier SydoniaWorld au
  Terminal3` at **FCFA 420 000 000** — larger than the whole of section 85's non-transfer
  spend. Also domestic: `plateforme de saisie des engagements des donnees` 38 000 000,
  `maintenance de l'applicatif Simba` 10 000 000, `Numeriser et moderniser les
  interconnections avec l'applicatif Simba` 3 125 000, `paiement electronique des droits et
  taxes` 3 000 000; section 32 `Digitalisation de l'administration et innovations
  numeriques` 16 000 000; section 41 **`Numeriser les Diplomes au SG-UB` 20 000 000 (new in
  FY2026, and confirmed in both volumes)**; section 50 `television numerique satellitaire`
  30 000 000, `systeme d'archivage` 30 000 000, `site internet de l'ACAP` 9 000 000.
- **The CDMT and the PLF group differently, and neither is wrong.** The CDMT's SydoniaWorld
  activity is 420 000 000 where the PLF's two Sydonia-labelled imputations (`Appui au
  deploiement` 115 000 + `Projet de migration` 130 000 milliers) come to 245 000 000. Both
  volumes cross-foot internally. **Do not net one against the other**; cite the grain you
  read. One genuine discrepancy is flagged rather than resolved: the PLF carries **two**
  `Numerisation des Archives` imputations of 8 000 milliers each in section 92 where the
  CDMT shows one activity at 8 000 000.
- **OCR: fast, and still not enough for the tables.** `scripts/ocr-pdf.py --lang fra` runs
  the REB quarterly reports at **~3 pages/second** and all nine (FY2024 Q1–Q4, FY2025 Q1–Q4,
  FY2026 Q1) plus both DGMP contract tables, arrete 1099 and the PLF 2025 law and revenue
  volumes were OCR'd and their **sidecars committed beside the artefacts** — OCR once, grep
  for ever. The REBs **do** carry per-ministry execution annexes (Annexe 1 personnel, 2
  biens et services, 3 transferts, each `dotation | dotation actuelle | realise`), and the
  ministry names read cleanly. **The digits do not.** At 300 and at 500 dpi with `--psm 6`
  the section-85 rows return figures that cannot be cross-footed against anything held — the
  Annexe 3 transfers row reads `1 987 500 | 1 987 500 | 1 745 171` against a collectif TITRE
  IV of 2 475 000, and no annexe total OCRs reliably enough to test the column. **So there
  is still no execution rate for CAR at any grain, for any year** — but the seam is now one
  good OCR pass away rather than un-attempted. `re_extract: OCR-partial` on all eleven.
- **The five estimates volumes were NOT OCR'd and that is the right call.** Three enacted
  laws and two collectifs, 600–720pp each, 137–187 MB. Every figure they would yield in
  scope is already held from a native volume — the collectifs through the following year's
  comparator column, the laws through the PLF they were voted from. What OCR of the enacted
  laws would settle is the one thing nothing else can: **whether the Assembly amended
  section 85 between the PLF and the vote**, and therefore whether any CAR figure may be
  labelled `appropriated`. Until then **every CAR record in this corpus is `proposed` or
  `revised`, and none is `appropriated`.** `re_extract: OCR-needed` on all five.
- **Case 5 is a no-op for this country.** `raw/` held no CAF `finance_origin: domestic-state`
  record of any tier before this pass, which is itself the FY2024 sweep's finding standing
  up: nothing about CAR's own digital spending was establishable from reporting alone.
- **Tooling added:** `scripts/caf-simba-extract.py` (geometry extraction of any SIM_ba
  charges volume, whole-volume run ~75s for 600pp) and `scripts/caf-cdmt-extract.py`
  (the CDMT at activity grain, 183pp in 6.5s). Both emit CSV to `budget-archive/CAF/`.

### Côte d'Ivoire — a complete five-stage chain, native, with no origin column (sweep, 2026-07-26, FY2024)

Supersedes the 2026-07-22 back-swing note *"Côte d'Ivoire / Benin / Gabon —
francophone budget-session reporting"* on the document side: the envelope problem
is solved for Côte d'Ivoire, because the estimates volume is published whole and
machine-readable and the "acquirable unit underneath the envelope" that note went
looking for turns out to be the annexed DPPD-PAP.

- **Fiscal year:** calendar. Loi de Finances n°2023-1000 du 18 décembre 2023, settled by loi n°2025-986 du 19 décembre 2025.
- **THE HOST IS `www.dgbf.ci`, NOT `dgbf.gouv.ci`.** `dgbf.gouv.ci` and `finances.gouv.ci` do not resolve at all; `dgmp.gouv.ci` does not resolve; `anrmp.ci` redirects to **`arcop.ci`**. `budget.gouv.ci` (the MBPE portal) resolves but its `loi-finance.html` is an Angular shell rendering no hrefs, and its `/doc/loi/` library stops in 2022. **Everything current is on `www.dgbf.ci`, a plain WordPress, and a default browser UA suffices — no DNS, TLS, IP-pin or bot-guard workaround was needed anywhere in this country, the second such case after Botswana.**
- **Track B is one fetch per document type, and the category pages are the index:** `/loi-de-finances-initiale/`, `/loi-de-finances-rectificative/`, `/projet-de-loi-de-finances/`, `/projet-de-loi-de-reglement/`, `/loi-de-reglement-2/`, `/pap/`, `/rap/`, `/rgp/`, `/revue-de-milieu-dannee/`, `/budget-citoyen/`, `/ccm/`, `/bulletin-mensuel-d-information-sur-lexecution-du-budget/`, `/arretes/`, `/decrets/`, `/lois/`, `/autres-documents/`, `/autres-textes-reglementaires/`, `/rapports-dactivites/`. Each lists direct `/wp-content/uploads/YYYY/MM/…pdf` links for all years, no pagination. **Do not use the homepage** — it carries the current year only.
- **THE FIRST COMPLETE FIVE-STAGE CHAIN IN THIS CORPUS, AND THE GAP IS AT THE FRONT, NOT THE BACK.** Appropriated, revised, executed and **audited** are all published for FY2024 at programme grain; the missing stage is **proposed** — `/projet-de-loi-de-finances/` still *lists* the November 2023 PLF batch and **all three of those `/2023/11/` URLs return the site's WordPress 404**. A live index onto dead files. Every other country in this series is missing the audit; Côte d'Ivoire is missing the bill.
- **THERE WAS NO LOI DE FINANCES RECTIFICATIVE IN FY2024, AND THE COUR DES COMPTES EXPLAINS WHY.** In-year modification was **+116 841 164 097 FCFA = 0,85%** of the voted budget, under the 1% ceiling of art. 25 LOLF, so "ce qui ne commande pas obligatoirement la présentation d'une Loi de finances rectificative". **The revised stage is therefore a set of ministerial arrêtés, ratified retrospectively by art. 1 of the loi de règlement**, and reported per programme in the RAP's **`Collectif`** column. The Cour also records that Annexe XIII of the presentation report (*liste des actes modificatifs du budget*) was the **only** justification it was given for those movements. **Look for the revised stage in the RAP and the loi de règlement, never in an LFR.**
- **The estimates volume: 521pp, native, activity grain, and no origin column.** Six table types — *Récapitulatif des Ressources / par Grande Nature de Dépense / par Section et Programme-Dotation / par Section et Grande Nature / du Service de la Dette / **Détail du Budget Général Hors Dette et Hors Comptes Spéciaux***. Grain: **section (3-digit) → programme (5) → action (7) → nature de dépense (1–4) → activité (11-digit)**, with AE and CP columns. **Unlike Burkina Faso (`État Seul / Contrepartie / Subvention / Prêt`), Botswana (`SOF`) and the Central African Republic (`Financement intérieur/extérieur` plus the `.11/.25/.44` account-key suffix), the Ivorian volume prints NO source-of-financing column at any grain.** The split exists only at the aggregate (art. 12 and the equilibrium table: *Dépenses d'investissement sur financement Trésor* 1 341 700 361 613 against *Financement extérieur des projets*). **The CIV origin gate must therefore come from outside the volume** — try annexe 5 (*Catalogue des mesures nouvelles*), the Rapport de présentation and the RAP's per-action tables; until one yields a per-line split, every CIV line carries its origin judgment as a flagged inference.
- **ARCHETYPE M, and the failure is loud enough to catch — if you cross-foot.** `pdftotext -layout` **drifts amounts by one to four rows in the recapitulative tables** while aligning cleanly on the *Détail du Budget Général* pages. The *Récapitulatif par Mission* prints **121 853 745 247** on the MTND row; that figure belongs to another ministry. The true section total is **55 649 125 870**, which the detail pages and the DPPD-PAP both give and which cross-foots (1 243 627 278 + 17 935 498 592 + 36 470 000 000). **Read the detail pages, not the recapitulatives, and cross-foot to a printed subtotal before recording anything.** Try the CAF pdfplumber-geometry method at extraction.
- **THE DIGITAL MINISTRY'S BIGGEST PROGRAMME IS AN OPERATOR LEVY, AND THE FINANCE LAW PRINTS IT.** Section 356 MTND FY2024 = **55 649 125 870**, of which **Programme 3 *Comptes Spéciaux du Trésor* is 36 470 000 000 (65,5%)**. Art. 18 lists every *Compte d'Affectation Spéciale* by activity code, and section 356's two are `78046000452 Transférer la Taxe pour le Développement des nouvelles technologies en zones rurales (**ANSUT**)` **32 300 000 000** and `78046000573 Soutenir l'activité de régulation du secteur des télécommunications` (**ARTCI**) **4 170 000 000** — summing to the printed programme total exactly. **Any total that reads the MTND envelope as state digital spending overstates it by two thirds.** The loi de règlement gives the ANSUT transfer **executed at 24 442 126 915**, a 24,3% shortfall on the levy. Contrast Botswana, where the UASF doing appropriation's work had to be found in a supply speech, and CAR, where the regulator appears only as an unexplained transfer object: here it is a coded line of the enacted budget, inside the sector vote.
- **BLOCK 4C, SETTLED FROM THE STATUTE: the data-protection authority IS the telecoms regulator, and it is funded by the industry it regulates.** `ARTCI`, `ANSSI`, `protection des données` and `données à caractère personnel` all occur **zero times** in 521 native pages — because under **loi n°2013-450 du 19 juin 2013, art. 45**, "les missions de l'Autorité de protection des données à caractère personnel sont confiées à l'Autorité administrative indépendante en charge de la Régulation des Télécommunications". ARTCI's only line in the state budget is the CST levy above. **The single-mandate carve-out cannot be applied** — ARTCI also regulates post, electronic transactions and domain names — so **no separable figure for the data-protection function exists in any held document**. What the ministry itself budgets under its own cyber heading is `78046000666 Assurer la promotion et l'appropriation de la stratégie nationale de cybersécurité` **FCFA 4 000 000** and `78046000670`, a legal-framework workshop, **FCFA 7 500 000**: FCFA 11,5 m for the year, for the country. ANSSI Côte d'Ivoire launched in February 2025 and so has no FY2024 line at all. *(Encoding check per post-run note 26: extracted with `pdftotext -enc UTF-8`, and the accented terms were confirmed against the unaccented `ARTCI` / `ANSSI`, which also return zero.)*
- **Block 4b — identity is in the Interior vote, and the systems are bought from a state company.** Section 016 carries `78016001644 Identifier les populations/ONECI`, `78016001649 Appuyer le processus de modernisation de l'État civil/ONECI`, `78016001808 transferts à l'ONECI … Dépenses d'Investissement`, `78016002230 SIPAO`, `78016002252 Centre National d'Archivage`. Separately the **SNDI** (Société Nationale de Développement Informatique) appears ten times and **always as somebody else's line** — `convention d'assistance technique` MEF/SNDI, MBPE/SNDI, DGMP/SNDI, plus `Nœud Internet/SNDI`, `Système de Gestion des EPN/SNDI`, `Déconcentration SIB/SNDI`, `Mise en place du SIB/SNDI`, `SIGOBE Institutions-Ambassades/SNDI`, `Migration GESPERS vers ORACLE/SNDI`. **Grep any Ivorian volume for `/SNDI` before anything else: it is the fastest cross-vote digital locator found in this corpus.** Also `78011202400 Moderniser et Sécuriser le SI du Trésor Public`, `78011201821 serveurs / refonte du SI des Douanes`, `78011202017 refonte du système d'information budgétaire`, `78011201795 DEMAT/DGMP`, `78013300683 identification biométrique des Fonctionnaires`.
- **The naming companion is the ministry's own budget-defence deck**, at `telecom.gouv.ci/new/uploads/publications/<unix-timestamp>.pdf`, listed under `index.php/publications/sous-categorie/4`. Same role as Botswana's Committee of Supply speeches: it prices individual activities the volume only names, and it restates the prior year's execution. **The library holds no upload earlier than April 2024**, so no FY2024 deck exists — the FY2025 and FY2026 decks are the route to FY2024 numbers. **The filenames are Unix timestamps**, and for most of these documents that is the only date they carry (the same is true of `courdescomptes.ci/fichiers/<unix-timestamp><Title>.pdf`).
- **Two official FY2024 revised figures for the same ministry — contradiction REV-CIV-001.** RAP 2024: Programme 1 collectif 1 505 459 066 (executed 95,09%), Programme 2 revised 18 185 498 592 (executed 99,99%), CST unchanged at 36 470 000 000 → implied total **56 160 957 658**, ministry execution 99,69%. The ministry's own PLF-2026 deck: AG **1 505 459 066** (agrees), Économie Numérique et Poste **23 437 413 869**, CST **27 676 208 542** → total **52 619 081 477**, executed 99,85%. Administration Générale is identical, so the *collectif* is not in dispute; the other two programmes are. Probably a difference of basis (voted vs *budget actuel* CST) but a 29% movement on Programme 2 is not explained by the +250 000 000 the RAP itself reports.
- **Reporting of the vote is unreliable in the last three digits.** The two ordinary programmes total **19 179 125 870** in the volume, **19 177 125 870** in Fraternité Matin's Assembly-committee report, and **19 171 125 870** in the ministry's own account of the Senate sitting. Three official-ish versions of one number; the volume settles it. Never build a record from a press figure when the volume is held.
- **Execution is published four ways, and the newest is the readable one.** Quarterly **CCM** (Communication en Conseil des Ministres) at `/ccm/`; monthly **BMIEB** at `/bulletin-mensuel-.../` (twelve for 2024); the **Revue de milieu d'année**, whose *Annexe 2* is H1 execution **by programme and by ministry, explicitly `hors avances, CST et Administration Générale`** — the one artefact that gives the digital ministry's rate net of the two levies; and the **RAP** Tomes 1–2 (2 322pp) with `Budget initial | Collectif | Budget Actuel | Budget Exécuté | Écart | Taux d'exécution` per nature *and* per action. **Of the four FY2024 CCMs only the end-December one is native** (30 715 chars over 11pp); March, June and September are image-only. The inverse of the usual pattern — take the full-year point first.
- **Only four of 28 documents need OCR:** `ANNEXE-7 Dotations des Institutions` (869pp, 53 670 chars = cover text only — the one substantially scanned appropriation document, and it holds the 32 dotations including the Cour des comptes and the Assembly); the Cour des comptes **Rapport public annuel** (83 MB, 75pp, **74 characters**); and CCM March/June/September.
- **Scrutiny lands on the identity money, not on the technology.** The Cour des comptes found that CNI and passport receipts collected by **ONECI** and by the private **SNEDAI** are **not in the State's accounts** (Treasury receipts on those documents were FCFA 792 000 for 2022); the Budget Minister answered that issuance and collection are no longer the Treasury's business, and SNEDAI says an escrow account exists. **The identity system is appropriated for on one side of the ledger and user-fee-funded outside the Treasury on the other** (CNI stamp FCFA 5 000, resident card FCFA 25 000, a published schedule of e-service charges on `oneci.ci` and `rnpp.ci`).
- **Series break at 2025-01-01.** From FY2025 the MTND has **four** programmes, the two CST split out as Programme 3 (ANSUT) and Programme 4 (regulation); FY2026 renames them again (*Appui au développement des nouvelles technologies en zones rurales* / *Appui à la Régulation…*). Any CIV series keyed on programme number needs a mapping row there. The ministry itself has since been renamed **Ministère de la Transition Numérique et de l'Innovation Technologique**.
- **Searched, found nothing:** a FY2024 procurement plan for the digital ministry (`dgmp.gouv.ci` dead; `arcop.ci` reached but not enumerated this run); an **ARTCI annual report for 2024**, which loi 2013-450 art. 45 obliges it to submit to the President and the Assembly; any FY2024 figure for ANSSI Côte d'Ivoire (it did not exist yet); any per-line origin split anywhere in the estimates volume.

## Côte d'Ivoire — FY2024 *(extraction discarded 2026-07-26)*

The FY2024-only extraction of 2026-07-26 was **discarded deliberately** (Bill's call): it
predated the one-record-per-line-year model and covered a single year, so it is being rebuilt
by `COUNTRY-BUDGET-BATCH.md` over FY2024–2026. **The 28 documents are kept**, restaged
unextracted in `new-budget/CIV/2024/` with their manifest rows reset — re-acquiring them was
not free (two PLF URLs are dead 404s, and the PADCI procurement plan only surfaced via the
World Bank repository).

**What survives, because it is knowledge about the documents rather than about the records:**
the archetype-M francophone variant in `budget-extraction-strategies.md` — *where the
appropriation volume prints no source-of-financing column, the origin gate is in the loi de
règlement's annexe X* — and its standing trap, *read the modifications column before quoting
any taux d'exécution*. Both were established from these documents and hold regardless of the
record model.

### Côte d'Ivoire — FY2025: the programme series breaks, and the drift gets worse (sweep, 2026-07-26)

Second CIV country-year. The FY2024 note above stands; these are the deltas.

- **THE PROGRAMME SERIES BREAKS AT 2025-01-01.** Section 356 goes from three programmes to
  **four**: the two *Comptes d'Affectation Spéciale* that FY2024 bundled inside Programme 3
  (*Comptes Spéciaux du Trésor*) are split out as **Programme 3 — Taxe pour le Développement des
  nouvelles technologies en zones rurales (ANSUT)** and **Programme 4 — Soutenir l'activité de
  régulation du secteur des télécommunications (ARTCI)**. Any CIV series keyed on programme
  number needs a mapping row here. The levy pass-through that FY2024 had to reconstruct from
  article 18's CAS list is now a line of the vote structure itself.
- **The ministry is renamed in the portal but NOT in the finance law.** The site now reads
  *Ministère de la Transition Numérique et de l'Innovation Technologique*; the LF 2025 still
  prints *Ministère de la Transition Numérique et de la Digitalisation*. **Key on the
  budget-document name.**
- **ARCHETYPE M IS WORSE IN FY2025 THAN FY2024, AND THE DRIFT IS NOW QUANTIFIED.** The
  *Récapitulatif par Section* prints the MTND at 97 200 000 000 while its four programme rows read
  64.8bn / 60.78bn / 1.857bn / 19.03bn (sum 146.5bn). The ministry's own budget-defence figure of
  US$96.8m converts at ~628 XOF/USD to **60 780 440 826 FCFA**, which is what the recapitulative
  prints on the *Programme 2* row — i.e. **the ministry total has drifted one row down**. Useful
  because it gives the drift a direction, not just a warning. Still: detail pages and DPPD-PAP only.
- **Machine-readability inverts.** FY2024's end-December CCM was the one native quarterly; in
  FY2025 end-March, end-September **and end-December** are all scanned (10pp, zero characters) and
  only end-June is native. **The December BMIEB is the native substitute for the full-year
  execution point** and should be reached for first, before OCR.
- **Portal routing correction:** `/rap/` is stale (stops at 2022). Current RAP, RGP and comptes
  come off **`/loi-de-reglement-2/`**. `/projet-de-loi-de-finances/` has been refreshed and now
  carries the full 2026 PLF batch, so the *proposed* stage is reachable for FY2026 — the stage
  FY2024 could not get. The 2024 batch's `/2023/11/` paths remain dead.
- **No LFR for 2024, 2025 or 2026.** Confirmed off `/loi-de-finances-rectificative/`. Ivorian
  in-year revision is by ministerial *arrêté* ratified in the loi de règlement — so a CIV
  `revised` stage is only fully readable ~12 months after the year closes.

### Côte d'Ivoire — FY2026: the proposed stage arrives, and it matches the law (sweep, 2026-07-26)

Third CIV country-year. Deltas on the FY2024 and FY2025 notes above.

- **THE `proposed` STAGE IS NOW REACHABLE, AND IT IS NEARLY IDENTICAL TO `appropriated`.**
  `/projet-de-loi-de-finances/` was a live index onto dead files at the FY2024 run; it has been
  refreshed and the whole 2026 bill batch is live. Bill vs enacted: estimates volume 583pp /
  1,761,898 ch against 584pp / 1,746,964 ch; **DPPD-PAP 1,230pp both, differing by 383
  characters**. The Assembly adopted the executive's budget essentially unchanged. So for CIV,
  populate `proposed_total` from the PLF, and treat any line that genuinely differs as a case-5
  contradiction -- against this baseline a real divergence is visible rather than buried.
- **Diff the pair; do not read both.** The documents are near-duplicates, so per-line comparison
  is cheap and reading them independently is wasted effort.
- **Programme wording moved between FY2025 and FY2026 without the structure changing.** Section
  356 keeps four programmes, but Programme 3 goes from '**Taxe** pour le Développement des
  nouvelles technologies en zones rurales' to '**Appui au** Développement...', and Programme 4
  from '**Soutenir l'activité de** régulation...' to '**Appui à la** régulation...'. The label
  stops naming the tax and starts naming the support. **Do not infer a mechanism change from the
  rename, or continuity from the structure.** It bears directly on the FY2024 headline that two
  thirds of the digital vote is a pass-through operator levy.
- **Scanned quarterly CCMs are the CIV norm; FY2024 was the outlier.** Three of four FY2025
  quarterlies and the sole FY2026 quarterly are scanned at 10pp / zero characters. FY2024's
  native end-December CCM is the exception, not the rule. **Reach for the monthly BMIEB first**
  -- it is consistently native and carries the same cumulative execution.
- **The 2026 batch adds a graphical cover page**, giving every file a ~10.5 MB floor where the
  FY2025 equivalents ran 0.8-4 MB. Cosmetic only: md5s are distinct and per-page text density is
  in line with FY2025. **Uniform file sizes in this corpus are not evidence of a bad download** --
  check md5 and per-page character density before assuming a fetch failure.
- **Volume growth:** the estimates volume runs 521pp (FY2024) -> 559pp (FY2025) -> 584pp (FY2026).

### Côte d'Ivoire — extraction pass, partial (2026-07-26, country budget batch step 4)

**METHOD FIX, and it supersedes the FY2024 note above: use `pdftotext -table`, NOT `-layout`.**
The FY2024 sweep recorded that `-layout` 'drifts amounts by one to four rows in the summary
tables' and warned the recapitulatives were dangerous. That is a `-layout` artefact, not a
property of the document. **`-table` renders the CIV recapitulatives correctly** -- the
*Récapitulatif Par Section et Programme/Dotation* returns 55.649.125.870 for section 356 FY2024,
which is the cross-footed figure, where `-layout` returned 121.853.745.247 (a different
ministry's row). Archetype M already mandates `-table`; the CIV variant note did not, and that is
why the drift looked like a document defect. **The recapitulatives are usable.**

**BUT the archetype's other warning stands and I tripped over it:** with `-table`, a within-number
digit-group gap and a between-column gap are the same character, so **a numeric regex silently
merges adjacent columns** (it returned '2,224,574,703,174,000,000,039,645,747,033,964,574,503'
for a row whose real first two figures are 2 224 574 703 and 1 740 000 000). Scan for the lines
programmatically; read the figures for the few tables that matter by eye. Collapsing runs of 3+
spaces to a delimiter (`re.sub(r'\s{3,}','  |',line)`) makes the columns readable without parsing.

**Section 356 appropriations, cross-footed against the section total in all three volumes:**

| FY | prog 21235 Admin | 22126 Économie num. | levy programmes | section total |
|---|---:|---:|---:|---:|
| 2024 | 1 243 627 278 | 17 935 498 592 | 23209 CST 36 470 000 000 | **55 649 125 870** |
| 2025 | 1 856 760 967 | 19 033 679 859 | 23237 ANSUT 35 300 000 000 + 23238 ARTCI 4 590 000 000 | **60 780 440 826** |
| 2026 | 1 704 184 519 | 45 991 319 076 | 23237 33 000 000 000 + 23238 2 580 000 000 | **83 275 503 595** |

**The pass-through share falls sharply in FY2026: 65,5% (2024) -> 65,6% (2025) -> 42,7% (2026)**,
because Économie numérique et poste more than doubles (19,03bn -> 45,99bn) while both levy
programmes shrink. The FY2024 headline -- that two thirds of the digital vote is an earmarked
operator levy passed straight through -- **stops being true in FY2026**, and that is a finding.

**PLF 2026 == LF 2026 at section 356, line for line.** All four programme figures and the section
total are identical in bill and enacted law, so `proposed_total` = `appropriated_total` for every
FY2026 MTND line.

**FY2024 stage ladder, from ANNEXE-VI summed across its four *nature de dépense* pages (49, 54,
58, 61 of the LR rapport de présentation):**

| | FCFA |
|---|---:|
| budget initial (LR) | 55 899 125 870 |
| modifications | -3 280 044 393 |
| budget actuel (revised) | **52 619 081 477** |
| exécution | **52 541 783 914** |
| taux vs revised | **99,85%** |
| taux vs voted (LF 55 649 125 870) | **94,42%** |

**REV-CIV-001 RESOLVES, and the ministry was right.** The FY2024 sweep opened a contradiction
because the ministry's November 2025 budget-defence deck gave a final position of 52 619 081 477
executed at 99,85%, against the RAP's 56 160 957 658. **ANNEXE-VI reproduces the ministry's
figures exactly** -- 52 619 081 477 actuel and 99,85% both fall straight out of the four nature
pages. The RAP is the outlier, for the reason the strategy library already gives: it carries the
Comptes Spéciaux at their voted level and never applies the write-down. **The settlement law and
the ministry agree; the performance report does not.**

**The CST write-down cross-foots to the franc.** Strategy-library figure for programme 23209
(-8 793 791 458) plus the two other programmes' modifications on that nature page
(+53 137 697, +722 850 000) = **-8 017 803 761**, which is exactly ANNEXE-VI's section-level
modification on p58. The 100,0% / 75,9% two-basis story for the levy line is confirmed.

**⚠ ONE UNRESOLVED RECONCILIATION, and no FY2024 record should be written until it is closed:**
the LR's *budget initial* for section 356 sums to 55 899 125 870 against the LF's voted
55 649 125 870 -- **a 250 000 000 gap**. The FY2024 sweep noted Programme 2 revised at
18 185 498 592, i.e. +250 000 000 on its voted 17 935 498 592, so the LR's 'initial' appears to
carry a transfer the LF's voted column does not. Establish whether that is a virement booked
before the collectif, a presentational difference, or a genuine disagreement -- and if the last,
file it. **`execution_pct_vs_appropriated` depends on which denominator is right** (94,42% on the
LF figure, 94,00% on the LR's).

### Ethiopia — a native chain where the published law is the *bill* and the accounting system is the appropriation (sweep, 2026-07-27, FY2024/25 / EFY 2017)

**The fiscal year is Ethiopian.** A bare year resolves to the EFY *beginning* in that Gregorian
year: **2024 → EFY 2017 → 8 July 2024 – 7 July 2025** (`Hamle 1, 2016 E.C.` to `Sene 30, 2017 E.C.`,
stated in Article 2 of the proclamation itself). Note the off-by-one that will trip a reader:
**EFY 2017 is our "2024"**, and MoF labels every file `2017`. Always carry both.

- **`mofed.gov.et` is a Wagtail/django-filer CMS and enumerates in one fetch.** `/resources/budget/`
  is the whole budget library back to EFY 2000 on a single page, no pagination; `/resources/government-account/`
  is the execution and audit library. Assets are `/media/filer_public/<xx>/<yy>/<uuid>/<name>.<ext>`.
  Downloads are small (5 MB is the largest here) but **slow** — allow a 180 s timeout; a 10-file
  batch took over two minutes.
- **MoF publishes the PRE-ENACTMENT text of both parts, and this is the central trap.**
  - *Part One* (the articulated law) reads `PROCLAMATION NO. -------------` and
    `No__________` — blanks unfilled. It is the bill as tabled.
  - *Part Two* (the detail volume) is served under **two different labels from two different
    UUIDs, byte-identical** — *"Budget Proclamation Part Two"* and *"Executive Budget Proposal
    (Part Two)"*, sha1 `6897b79db6f6`. Its `docProps/core.xml` `modified` is **2024-06-25**,
    nine days before enactment, and its `dc:title` is a stale template from EFY 2008.
  - **So every line in the detail volume is `proposed`, not `appropriated`.** Aggregate totals do
    equal the enacted Article 2 figures — the House passed it unchanged at summary level — but a
    582 bn birr supplementary followed in November, so that agreement means nothing at line grain.
- **THE RESCUE IS THE IFMIS EXTRACT, and it is better than what it rescues.** The quarterly
  *Budget vs Expenditure* reports (IFMIS/IBEX, on `/resources/government-account/`) have the shape
  `Public Body | Description | Approved Budget | Adjusted Budget | YTD | <Nth> Quarter | Over/Under`.
  That is **three stages in one table**: `Approved` = appropriated (the enacted proclamation as
  loaded to the accounting system, and the *only* enacted figure Ethiopia publishes), `Adjusted` =
  revised, and `YTD` in the **Sene** (year-end) file = actual. Rows alternate 5-digit **public-body**
  codes with 7-digit **economic-classification** codes beneath (`2100000` Compensation to Employees,
  `2200000` Use of Goods and Services, `2300000` Fixed Assets and Construction, `2600000` Grants,
  `2800000` Other Expenses) — parse on code width.
- **Do not cross-foot the IFMIS files to the proclamation.** They cover **IFMIS bodies only** —
  the report states 174 federal public sites, 118 on IFMIS and 56 on IBEX, reported in separate
  sections. Administration & General shows Approved 128,727,319,961.98 against the proclamation's
  150,184,732,667 for the same function; the gap is the IBEX population, not an error.
- **The origin gate is printed in the volume, at project grain.** The capital sheet splits every
  project four ways — **Treasury / Retained Revenue / Assistance / Loan**; recurrent splits two
  (Treasury / Retained Revenue). Finer than Burkina Faso's, and the only other volume in the corpus
  that carries its own origin column. **Retained Revenue is the one to watch for regulators.**
- **Scale: `በብር` = whole birr, NOT thousands.** Verified — the volume's grand total
  971,200,665,909 equals Article 2 to the birr. The *Citizens' Budget*, by contrast, is in rounded
  **billions**; never cross-foot the two.
- **Sheet names lie about language.** `RECURRENTin AMha` and `CAPITAL in AMHAric` both carry
  Amharic **and** English blocks side by side — Amharic in the left columns, English from col 9
  (recurrent) or col 13 (capital). Header row 4, sub-header row 5. Set `PYTHONIOENCODING=utf-8` or
  every read dies on cp1252.

**WHERE THE DIGITAL LINES ARE.** Ethiopia gives each digital body its own **public body code**, so
the sector-vote bias that Block 4b exists to correct is much weaker here — the bodies are already
separate. EFY 2017 recurrent: INSA **135** (1,300,000,000), Ethiopian Statistics Service **154**
(450,963,289), Ministry of Innovation and Technology **161** (439,452,330), Documents Authentication
and Registration Service **134** (424,112,295), Artificial Intelligence Institution **144**
(395,030,000), Space Science and Geospatial Institute **177** (290,737,500), Ethiopian
Communications Authority **183** (203,275,000), Ethiopian Technology Authority **164** (96,918,643),
Bio and Emerging Technology Institute **176** (91,309,608). Programme strings worth grepping:
*Civil Family Registration & National ID Service*, *Establishing Family Registration and National
Identification System*, *Conducting Statstics Digitalization* (sic), *Improving Tax Information
Technology*, *Modern Data Management System*, *Installed network and datacenter*, *Cyber Security
Control & System Implementation*.

**THE DIGITAL ID IS NOT IN THE APPROPRIATION — IT ARRIVES MID-YEAR, UNDER THE PRIME MINISTER.**
The Q4 EFY 2017 file, `Sheet1` row 83: `14166 OPM - Ethiopia Digital ID for Inclusion`, **Approved
Budget 0**, Adjusted 3,055,354,504, YTD 3,055,354,503.13 — 100% of adjusted, spent. The mechanism is
**Article 3(3)** of the proclamation, which authorises public bodies to record additional loan and
assistance funds, in cash or in kind, on their own budget heads; so a donor-financed programme
appears with a zero appropriation and a full outturn. It sits under the **Office of the Prime
Minister** (10002/11002), *not* MInT — so a search that walks the ICT ministry's vote finds nothing.
Almost certainly World Bank **P179040** (US$350m, financing agreement Dec 2023), which would put it
`non-state` at the origin gate. **This is the "government invests = external money in state
clothing" pattern with the paperwork visible.**

**Block 4c — Ethiopia has no standalone data protection authority.** Personal Data Protection
Proclamation **No. 1321/2024** (adopted 4 April 2024, in force 24 July 2024) designates the
**Ethiopian Communications Authority** as supervisory body. Unlike the usual finding, **ECA is
appropriated** (body 183, 203,275,000 birr recurrent). The live question is *which pocket*: ECA is
also licence- and spectrum-fee funded (Fees Directive No. 1024/2024), and the recurrent sheet's
**Treasury vs Retained Revenue** split answers it directly. Ask that question of every ETH year.

**Two library defects, both silent.** (1) The *"2017 Financial Report 2nd Quarter"* link serves a
**second copy of the Third Quarter report** (same `Period Name: Megabit-2017`, identical sampled
rows) — **there is no published Q2**; the series is Q1 → Q3 → Q4. (2) The **mid-year review is
filed under the wrong EFY** — `mid_year_budget_performance_report-final-april_2025.pdf` is listed
under EFY 2018 but an April 2025 mid-year review covers July–December 2024, i.e. **EFY 2017**.
Check `Period Name` and the title row of every quarterly file rather than trusting the label.

**Audit: OFAG is a publication gap, not a search failure.** The Office of the Federal Auditor
General **presented** its EFY 2017 report to the House (163 institutions, 39 performance audits) and
its own summary credits the **e-GP system** for falling cash shortages — but its downloadable library
(`/ofag/report_parliament/`, a WP-Filebase category tree) stops at **2016 E.C.**. Separately,
**`www.ofag.gov.et` does not resolve from this network** (ETIMEOUT on http and https); bare
`ofag.gov.et` only meta-refreshes to `/webmail/`. Reachable via an external cache. Two obstacles,
and the publication lag is the real one.

**Everything Ethiopian in this run is native text.** No OCR anywhere — proclamation, proposal,
citizens' budget, all four execution files. After Benin, CAR and Nigeria this is the cheapest
corpus in the collection to read.

#### Ethiopia FY2025/26 (EFY 2018) — the instrument improves, the execution side stops (sweep, 2026-07-27)

- **The proclamation grows from 8 pages to 178 and swallows Part Two.** For EFY 2018 MoF publishes
  the articulated law **with the detailed schedules inside it**: revenue detail pp.17–29, recurrent
  by public body → programme → activity in Amharic pp.30–100 and **English pp.101–150**, capital
  pp.151–177, SDG support p.178. The separate Part Two workbook is also published, so the two
  cross-check. **Still unnumbered** (`PROCLAMATION NO. -----------------`) — MoF publishes the
  pre-enactment text every year — but ENA reports a unanimous House approval of 1.93tn on
  2025-07-03 and the volume sums to exactly 1,927,689,143,793, so the schedules can be read as
  **appropriated** with the caveat noted rather than as bare `proposed`.
- **Article structure changed.** EFY 2017 put everything in Article 2; EFY 2018 splits it —
  **Article 6** federal budget (recurrent 1,183,697,146,435 + capital 415,235,003,313 =
  1,598,932,149,748), **Article 7** subsidies to regions, and Art. 7 **now discloses origin**:
  Domestic Source 313,822,387,645 vs External Assistance 934,606,400. EFY 2017 gave one
  undifferentiated subsidy figure. Real improvement in disclosure; say so.
- **THE WORKBOOK COLUMN LAYOUT SHIFTS ONE COLUMN LEFT BETWEEN YEARS.** Header row 4, sub-header
  row 5 in both, but recurrent `Pub. Body code` moves col 9 → **col 8** and `Total` col 15 → **col
  14**. A parser hard-coded to EFY 2017 offsets **returns an empty set rather than erroring** —
  the dangerous failure mode, and it happened here on the first pass. **Locate columns by header
  name, per year, always.**
- **THE EXECUTION SERIES STOPS DEAD.** `/resources/government-account/` re-read in full: newest
  execution document is the **4th Quarter 2017 Financial Report, uploaded 2025-10-20**. No EFY 2018
  Q1/Q2/Q3/Q4, no EFY 2018 mid-year review. On Ethiopia's own EFY 2017 cadence (Q1 published
  2025-02-04 for a quarter ended Sept 2024) EFY 2018 Q1 was due about February 2026. Five months
  late and the year is now closed. **As at 2026-07-27 Ethiopia has published no execution data for
  FY2025/26 at all** — a lapse, not a lag, and a hub-level stated absence rather than an
  acquisition line, because the documents do not exist to fetch.

**THE CURRENCY TRAP, AND IT GOVERNS EVERY ETHIOPIAN COMPARISON.** EFY 2017 → EFY 2018 is
971,200,665,909 → 1,927,689,143,793 birr, **+98.5% nominal — and it is mostly the birr float.**
Ethiopia moved to a floating rate in **late July 2024**, three weeks into EFY 2017; roughly 57
birr/USD became roughly 135 birr/USD. In dollars the federal budget **fell**, about US$22bn
(2023/24) to about US$14bn (2025/26), ~36% down, while rising 60% in birr. Every digital body looks
like it nearly doubled and none of them did: INSA 1,300,000,000 → 2,102,115,991 (+61.7%), AI
Institution 395,030,000 → 530,848,000 (+34.4%), MInT 439,452,330 → 573,999,360 (+30.6%) — all three
**fell** in real terms. **Write every ETH figure dated and in birr; give any USD conversion its own
date and rate** (`CLAUDE.md` → *Currency*). Source: Addis Standard, 2025-07-01, staged at
`new/2025-07-01-eth-addis-standard-deciphering-1-93tn-birr-budget.md` — which also documents the
recurrent share rising 26.2% (2018/19) → 61.4% (2025/26) while capital falls 32.7% → 21.6%.

**BLOCK 4c, NOW WITH A NUMBER — Ethiopia's data protection authority is majority-funded by the
industry it regulates.** ECA is the supervisory body under Proclamation 1321/2024, and its EFY 2018
recurrent budget is **Treasury 90,197,600 vs Retained Revenue 182,000,000, total 272,197,600** —
**66.9% self-funded** from licence and spectrum fees (Fees Directive No. 1024/2024), the fisc
supplying 33.1%. Stated by the budget, not inferred. **Second finding in the same column: the
Documents Authentication and Registration Service (134) takes zero treasury money** — 636,858,449
birr, entirely retained fees; a national registry body wholly outside the fisc. **Read the
Treasury/Retained split for every ETH regulator and registry body, every year** — it is the
question the two-column recurrent sheet exists to answer, and totals alone hide it.

**EFY 2018 digital bodies, recurrent (Treasury | Retained | Total, birr):** INSA **135**
2,102,115,991 | 0 | 2,102,115,991 · DARS **134** 0 | 636,858,449 | 636,858,449 · Statistics Service
**154** 584,085,990 | 0 | 584,085,990 · MInT **161** 573,999,360 | 0 | 573,999,360 · AI Institution
**144** 530,848,000 | 0 | 530,848,000 · Space Science & Geospatial **177** 333,500,800 | 7,479,600 |
340,980,400 · ECA **183** 90,197,600 | 182,000,000 | 272,197,600 · Technology Authority **164**
149,053,026 | 0 | 149,053,026 · Bio and Emerging Technology **176** 124,734,183 | 0 | 124,734,183 ·
Ministry of Revenue **156** 5,836,967,990 | 0 | 5,836,967,990.

**A proposed-stage volume exists for EFY 2018 and did not for EFY 2017.** *የተደገፈ በጀት ጥራዝ I*
(Recommended Budget, Volume I), 85pp native, cover-dated **ግንቦት 29/2017** = Ginbot 29, 2017 E.C. =
**6 June 2025**, four weeks before enactment. Ethiopian date conversion: 2017 E.C. began
11 September 2024, months are 30 days, Ginbot is month 9, so day-of-year 269. Holding it alongside
the proclamation gives EFY 2018 a real proposed-vs-appropriated diff.

**No EFY 2018 supplementary surfaced**, where EFY 2017 had one (581,982,390,117 birr, 2024-11-26).
Recorded as *not established*, not as *none*.

#### Ethiopia FY2026/27 (EFY 2019) — the publishing behaviour changes, and a disclosure is withdrawn (sweep, 2026-07-27)

- **THE PUBLISHED FILES FINALLY POSTDATE ENACTMENT.** The House ratified on **2026-07-07** (Fana
  Media Corporation; 30th regular session). The Part Two workbook is `modified 2026-07-09` — **two
  days after** — and its filename carries an `_updated` suffix; the Part One PDF was created
  **2026-07-23**. Set against the earlier years:

  | Year | Detail artefact | Enactment | Verdict |
  |---|---|---|---|
  | EFY 2017 | 2024-06-25 | 2024-07-04 | 9 days **before** → `proposed` |
  | EFY 2018 | 2025-06-26 | 2025-07-03 | 7 days **before** → appropriated only because totals match |
  | EFY 2019 | **2026-07-09** | **2026-07-07** | 2 days **after** → **`appropriated`, cleanly** |

  All three still carry the unnumbered `PROCLAMATION NO. -----------------` template, so **the
  blanks are not the test** — the timestamp is. Check `docProps/core.xml` `modified` (xlsx) and
  `CreationDate` (pdf) against the reported ratification date, every year, for every country that
  publishes a template like this.
- **THE ORIGIN DISCLOSURE LASTED ONE YEAR.** EFY 2018 split the appropriation into Article 6
  (federal) and Article 7 (subsidies to regions), and Art. 7 disclosed *Domestic Source
  313,822,387,645* vs *External Assistance 934,606,400*. **EFY 2019 reverts to the EFY 2017 single
  Article 2 with lettered items (A)–(D)** and the regional subsidy is one undifferentiated
  520,555,497,713. A dated hub statement, not a search failure. The **capital sheet's** project-level
  Treasury/Retained/Assistance/Loan split is unaffected and remains the real origin gate.
- **Article 2, EFY 2019:** recurrent 1,236,459,164,983 + capital 568,253,464,042 + subsidy
  520,555,497,713 + SDG 14,000,000,000 = **2,339,268,126,738**. Rise on EFY 2018 is
  411,578,982,945 / **+21.3%** — Fana's reported 411.6bn/21.3% agrees.
- **The currency distortion is confined to the FY2024→FY2025 step.** EFY 2017→2018 was +98.5%
  nominal and mostly the birr float; EFY 2018→2019 is +21.3% and broadly real. So the float
  correction has to be applied to exactly one year-on-year comparison in this batch, not all of them.
- **Column layout: EFY 2018 and EFY 2019 agree; EFY 2017 is the odd one out** (everything one column
  right). Recurrent English block for 2018/2019: code **8**, program 9, activity 10, description 11,
  Treasury **12**, Retained **13**, Total **14**.
- **The summary sheets shrank in EFY 2019** — `Sum. of Revenue` 25 rows against 386, `Revenue` 251
  against 614. Detail sheets are full size (RECURRENT 2042, CAPITAL 2249), so nothing substantive is
  lost, but re-derive from detail any cross-foot that leaned on the summaries.

**THE ANOMALY WORTH CHASING — the Ethiopian Statistics Service nearly doubles.** Body **154**:
584,085,990 → **1,100,000,037 birr, +88.3%**, in a year when the overall budget rose 21.3% and every
other digital body moved 14–47%. About +55% real, and the largest single anomaly in the Ethiopian
corpus. **Census preparation is the obvious hypothesis** — the population and housing census has
been postponed repeatedly since 2019 — **but nothing here establishes it.** Read body 154 at
programme grain (*Conducting Population and Social Statistics*, *Conducting Statstics Digitalization*
were among its EFY 2017 programme strings) and state what the volume says, including if it says
nothing.

**Block 4c, three-year series.** ECA — the data protection authority under Proclamation 1321/2024 —
keeps shifting onto its own fee income: EFY 2018 Treasury 90,197,600 / Retained 182,000,000 (66.9%
retained); **EFY 2019 Treasury 106,243,000 / Retained 245,573,000 (69.8% retained)**. EFY 2017's
split was not read by that sweep (total 203,275,000 only) — **read it to make the series
three-point**. **Documents Authentication and Registration Service (134)** takes zero treasury in
every year read so far: 636,858,449 (EFY 2018) → 935,001,984 (EFY 2019), +46.8%.

**EFY 2019 digital bodies, recurrent (Treasury | Retained | Total, birr):** Ministry of Revenue
**156** 7,629,432,000 | 0 | 7,629,432,000 · INSA **135** 2,628,049,744 | 0 | 2,628,049,744 ·
Statistics Service **154** 1,100,000,037 | 0 | 1,100,000,037 · DARS **134** 0 | 935,001,984 |
935,001,984 · AI Institution **144** 693,131,040 | 0 | 693,131,040 · MInT **161** 680,339,300 | 0 |
680,339,300 · Space Science & Geospatial **177** 419,281,541 | 7,853,600 | 427,135,141 · ECA **183**
106,243,000 | 245,573,000 | 351,816,000 · Technology Authority **164** 170,284,700 | 0 |
170,284,700 · Bio and Emerging Technology **176** 158,400,570 | 0 | 158,400,570.

**Correctly absent for EFY 2019:** no Citizens' Budget (EFY 2018's came 2.5 months after enactment,
so due ~September 2026), no recommended-budget volume, no execution, no audit. The year is 19 days
old.

### Ethiopia — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-07-27)

**14 documents, 3 country-years, no OCR, two new archetypes (O and P), 34 records, 2 donor merges.**

- **Two archetypes were needed and both are now in the strategy library.** **O** — bilingual
  single-year estimates workbook with a printed four-way source-of-finance column. **P** —
  accounting-system year-end extract carrying three budget stages in one table. Ethiopia is the
  first corpus where the estimates volume and the *accounting system* are both native and must be
  read **against each other**, because neither alone gives an enacted line.
- **THE STAGE PROBLEM, AND HOW IT RESOLVED.** MoF publishes the proclamation from a template whose
  number is never filled in, so `PROCLAMATION NO. -----------------` appears in all three years and
  **is useless as a test of enactment**. The timestamp is the test:
  EFY 2017 workbook `modified 2024-06-25` vs enactment 2024-07-04 → **`proposed`**;
  EFY 2018 `2025-06-26` vs 2025-07-03 → pre-enactment but totals equal the reported approval →
  `appropriated` with the caveat carried on every record;
  EFY 2019 `2026-07-09` vs 2026-07-07 → **`appropriated` cleanly**, the first year the published
  detail postdates enactment.
- **The IFMIS extract is what rescues FY2024/25**, and it does more than rescue it. Its
  `Approved Budget` column is the enacted appropriation at public-body grain — the only enacted
  figure Ethiopia publishes — so the difference between the volume and that column **is the
  legislature's amendment during passage**, otherwise invisible. Of fifteen bodies reconciled,
  **seven passed unchanged** (INSA, DARS, MInT, Ethiopian Technology Authority, Federal High Court,
  Federal First Instance Court, Ministry of Justice) and the rest were trimmed: the communications
  regulator by **100,000**, the AI institute by **12,650,000**, the space institute by
  **32,450,000**, the Supreme Court by **607,083**, Government Communication Service by
  **2,500,000**. *Aggregate agreement between proposal and enactment does not imply line-level
  agreement* — the EFY 2017 grand totals matched exactly while five of fifteen digital bodies moved.
- **⚠ The two code systems do not align and a wrong join invents billions.** IFMIS 5-digit body
  codes are not the budget's 3-digit codes, and one budget body can appear under several. The
  Ethiopian Statistics Service is `10028 Central Statistics` (ties exactly to the volume's
  4,195,642,689) *and* `11035 Ethiopian Statistics Service` (about a third of it); taking 11035
  produced a phantom 2.7bn birr variance. The Ministry of Revenue never ties at all under any code
  tried, so **no execution rate is claimed for it**. Cross-foot before trusting a mapping; where
  nothing ties, claim nothing.

**THE HEADLINE FINDING — Ethiopia's digital transformation is externally financed, and the domestic
money that was voted went largely unspent.** From the FY2017 IFMIS year-end extract:

| IFMIS body | Approved | Adjusted | Actual (YTD) | Execution |
|---|---|---|---|---|
| `14485` MoIT – Ethiopian Digital Foundation Project | **0** | 7,041,485,908 | 7,041,485,908 | **100.0%** |
| `14166` OPM – Ethiopia Digital ID for Inclusion | **0** | 3,055,354,504 | 3,055,354,503 | **100.0%** |
| `11037` Ministry of Innovation and Technology | 2,754,552,330 | 2,947,641,829 | 989,820,128 | **35.9%** |

The Digital Foundations project alone was **2.6× the ICT ministry's entire voted budget and 7.1×
what the ministry actually spent.** Both donor programmes entered with **zero appropriation**, under
**Article 3(3)** of the budget proclamation, which lets public bodies record additional loan and
assistance funds on their own heads — so **neither appears anywhere in the estimates volume**. The
Digital ID line sits under the **Office of the Prime Minister**, not MInT, so a sector-vote reading
misses it twice over. Both definite-matched to World Bank deals the wiki already held (`wb-eth-001`,
`wb-eth-002`) and were **merged into those records' development history rather than created as new
`non-state` records**, per the origin gate.

**The generalisable technique: grep the IFMIS body list for `Approved = 0` with non-zero `YTD`
before anything else.** That single filter surfaced the two largest digital programmes in the
country. Run it on every state that publishes an accounting-system extract.

**THE ORIGIN GATE, PRINTED.** The capital sheet splits every project `Treasury / Retained Revenue /
Assistance / Loan`. MInT's programme 03 *Digital Economy and ICT*: **FY2024/25 Treasury 206,750,000
vs Loan 1,852,100,000 — 10.0% Ethiopian; FY2025/26 157,650,000 vs 1,865,644,000 — 7.8%; FY2026/27
441,500,000 vs 254,500,000 — 63.4%.** The domestic share more than doubles in EFY 2019, **but the
programme's total capital falls 66%** (2.06bn → 696m). Ethiopia's digital-economy capital programme
became mostly domestically financed **by shrinking, not by the fisc stepping in** — a conclusion
available only because the split is printed.

**BLOCK 4c, SETTLED WITH THREE YEARS OF NUMBERS.** The ECA is Ethiopia's data protection authority
(Proclamation 1321/2024 designates it; there is no standalone body). Its recurrent split is
**EFY 2017 Treasury 63,275,000 / Retained 140,000,000 = 68.9% retained; EFY 2018 90,197,600 /
182,000,000 = 66.9%; EFY 2019 106,243,000 / 245,573,000 = 69.8%.** **Majority funded by the industry
it regulates, and the share is flat at roughly 67–70% — not rising.** *(The two-year read taken at
sweep time looked like a rising trend; the third point removed it. A caution worth carrying: two
points are not a trend, and the sweep files were corrected rather than left standing.)* And **no
data-protection programme line exists in any of the three volumes** — the ECA's five programmes are
all communications regulation. Ethiopia has enacted a data protection law and appropriates nothing
separately identifiable for enforcing it: a dated hub absence.

Second in the same column: **Documents Authentication and Registration Service (134) takes zero
treasury money in every year** — 424,112,295 → 636,858,449 → 935,001,984 birr, entirely retained
fees. A national registry body wholly outside the fisc, and its execution was **144.0% of its voted
figure** in FY2024/25 (adjusted 615,720,640, actual 610,579,414) — fee income arriving above budget.

**THE CROSS-VOTE SCAN PAID, AND THE BIGGEST DIGITAL PROJECT IS NOT IN THE ICT MINISTRY.** The
**Federal Supreme Court's entire EFY 2017 capital appropriation is one project — *Connecting Courts
through Wide Area Network*, 500,000,000 birr** — larger than MInT's whole domestic capital budget
(463,000,000). The **Ministry of Revenue** carries four named systems inside a vote that is
otherwise branch-office buildings: *Integrated Tax Adminstration System-ITAS* 26,671,900,
*Electronics Invoice System* 86,134,380, *Data Warehouse & Business Intellegence System* 88,507,100,
*Data Service Center* 174,053,120 — **375,366,500 together**, again of the same order as the ICT
ministry's domestic capital. A sector-vote total for Ethiopia would miss roughly 875m birr of named
digital capital in two votes alone.

**An anomaly resolved against its own hypothesis.** The FY2026 sweep flagged the Ethiopian
Statistics Service nearly doubling (584,085,990 → 1,100,000,037, +88.3%) and suggested census
preparation. **Extraction found the opposite**: programme 04 *Statstics Modernization and Capacity
Building* — the digitalisation programme — **fell 46.6%** (35,127,055 → 18,745,400) in the same
year. The body's growth is **not** digitalisation. Recorded on the record and corrected in the sweep
file. Worth generalising: **a body-level jump says nothing about the digital line inside it**, and
the sweep's job is to flag it while extraction's job is to answer it.

**Case 5: nothing to reset.** The wiki held **no** ETH `domestic-state` records before this run
(only non-state donor deals), which is the expected state for a country the batch is initialising.

**Not worth extracting.** The *Executive Budget Proposal* **PDF** (184pp) is figure-for-figure
identical to the XLSX detail volume and adds only printed page numbering for `doc_locator`; take the
workbook. The *Citizens' Budget* is rounded billions and supports no line.

**Left unread, and recorded as such in the manifest** (`re_extract` set, not `no`): the Q1 and Q3
IFMIS files (Q1's `Adjusted` column would isolate the November 2024 supplementary's effect per
body), the April 2025 mid-year review (the narrative behind MInT's 35.9%), and the EFY 2018
*Recommended Budget Volume I* (a proposed-vs-appropriated diff for that year). None blocks a record;
each is a real increment.

### DR Congo — the best-organised budget library in the collection, and a state that publishes the original OR the rectificative (sweep, 2026-07-27, FY2024/FY2025/FY2026)

**Calendar fiscal year.** *Exercice 2024* = 1 January – 31 December 2024. No resolution subtlety.

- **`budget.gouv.cd` is the cleanest enumeration met so far.** Separate sections for the draft
  (`/budget-YYYY/`), the enacted law (`/lois-de-finances/`), execution (`/exercice-YYYY/`,
  `/execution-mensuelle/`) and quarterly commitment plans
  (`/plan-dengagement-du-premier-trimestre-YYYY/`). One `requests.get` per page and a
  `href="…\.pdf"` regex returns everything; the FY2024 execution page alone yields 268 links.
- **⚠ THE UPLOAD PATH CONVENTION IS NOT STABLE ACROSS YEARS, so never construct a URL by analogy.**
  FY2024's enacted volume: `budget2024/vote/lf_2024_depenses.pdf`. FY2025's rectificative:
  `budget2025/budget2025_rect/lf_2025_depenses.pdf`. FY2026's enacted:
  `budget2026/lf_2026_depenses_final.pdf` (no subdirectory). Enumerate the year page every time.
- **⚠ The ministry's own `/lois-de-finances/` table labels the two FY2024 volumes the wrong way
  round.** It lists *"Volume 1: Développement par actes générateurs des recettes"* against
  `lf_2024_depenses.pdf` and *"Volume 2: Développement par titre des crédits"* against
  `lf_2024_recettes.pdf`. **The filenames are right and the labels are crossed** — `…depenses.pdf`
  is Volume 2 (expenditure detail, 1,217pp, **native**), `…recettes.pdf` is Volume 1 (revenue,
  214pp, **image-only**). Open the cover page; do not trust the table.
- One stray path in the FY2024 execution index reads `esb2023£4/` — a typo for `esb2024`. Harmless
  to a human, fatal to a naive crawler.

**THE STRUCTURAL FACT THAT GOVERNS EVERY DRC RECORD: the state publishes the ORIGINAL enacted law or
the RECTIFICATIVE, never both.**

| Year | Original enacted | Rectificative |
|---|---|---|
| FY2024 | **LF n°23/056 du 10 déc. 2023, Vol. 2, 1,217pp native** | *projet* only (Docs A/B/C, Sept 2024) — never published as enacted |
| FY2025 | **absent** — `/lois-de-finances/` stops at 2024; `budget2025/vote/…` returns 404 | **LFR n°25/044 du 28 juin 2025, Vol. 2, 1,225pp native** |
| FY2026 | **LF n°25/060 du 29 déc. 2025, Vol. 2, 1,288pp native** | none enacted; one is before the Assembly (May 2026) |

So **FY2025 has no `appropriated` stage at line grain** and its volume-built records are `revised`;
FY2024 and FY2026 have a true appropriated stage and no enacted revision. **Do not assume a
rectificative supersedes an original you also hold — in DRC you will only ever hold one of them.**

**THE EXECUTION DATA CHANGES SHAPE EVERY YEAR, AND ONLY ONE SHAPE IS USABLE FOR MINISTRY-LEVEL WORK.**

- **FY2024** — monthly *États de Situation Budgétaire* (ESB), twelve months, full `global/` fan:
  `par_fonction`, `par_fonction_et_sous_fonction`, `par_rubrique`, `par_rubrique_titre`,
  `par_titre`, `par_financement`, plus `dlcp/` (poverty-reduction) and `transfert/` (to provinces)
  sets. Six columns: **`Crédits Votés` (appropriated) | `Créd. Après Vir.` (revised) | `Engagements`
  | `Liquidations` | `Ordonnancements` (released) | `Paiements` (actual)**. `Engagements` and
  `Liquidations` are the French commitment chain and have no driver stage — context, not stages.
  **⚠ But every FY2024 cut is FUNCTIONAL or ECONOMIC, never administrative**, so the digital
  sub-function cannot be attributed to a ministry.
- **FY2025** — the same monthly fan to September, then for December a *single* file,
  `situation_prov_esb_fmi_31122025.pdf` (12pp native, IMF format). **Its Tableau 3 is BY
  ADMINISTRATIVE SECTION**, which is exactly what FY2024 lacks. **No FY2024 equivalent exists**
  (`situation_prov_esb_fmi_31122024.pdf` 404, two variants probed).
- **FY2026** — **nothing at all**, seven months in, where the two prior years published monthly from
  January. A lapse against the country's own cadence, and a dated hub absence rather than an
  acquisition.

**WHERE THE DIGITAL LINES ARE — AND THERE ARE TWO DIGITAL MINISTRIES.** The enacted volume's section
index (PDF p.3–4; **⚠ its page numbers are section-internal, not PDF pages**) carries **both**:

- **52 — POSTES, TELECOMMUNICATIONS ET NOUVELLES TECHNOLOGIES DE L'INFORMATION ET DE LA COMMUNICATION (PTNTIC)**
- **71 — NUMERIQUE**

plus **41 Recherche scientifique et innovation technologique**, **25 Intérieur et sécurité** (which
carries identification/ONIP), **32 Plan**, **77 CENI** (voter register) and **85 Cour des comptes**.
**A scan that finds section 52 and stops understates the digital vote.** In the functional
classification both collapse into sub-function **`04600 Poste, télécommunications et technologies de
l'information et de la communication`**, which is the join key to the FY2024 execution états — and
the reason FY2024's outturn cannot be split between the two ministries.

**Figures already read at sweep time (verify at extraction):**
FY2024 sub-function 04600 — Crédits Votés **158,331,308,819 FC**, Après Vir. **158,331,308,819**
(i.e. **not revised in-year**), Engagements **84,465,886,109**, Liquidations **84,288,257,101** —
about **53% committed**.
FY2025 section 71 Numérique — Crédit voté **60,627,481,411 FC**, Engagement **68,457,537,329**,
Ordonnancement **68,278,687,329**, **TOTAL PAIEMENT 31,358,784,468** — **51.7% of the voted credit
actually paid against 112.9% engaged**; the commitment chain ran far ahead of cash.
**⚠ Section 52's row in the FY2025 file extracts with badly interleaved characters** — read it by
table geometry, never from `extract_text()`.

**A GOVERNANCE COLUMN NO OTHER CORPUS OFFERS: the *urgence* procedure.** The FY2025 IMF-format file's
Tableau 1 splits all spending by payment procedure — **URGENCES 5,257,227,896,516 FC against
STANDARDS 28,335,370,529,376, i.e. ~15.7% of a 33,592,598,425,892 FC total bypassed the standard
chain** — and Tableau 3 gives a **`Tx. Urgence` per section**. For section 71 Numérique the urgence
column is empty; for some sections it exceeds 60%. That is a fact about *how* a state spends,
available per ministry, and worth carrying as context on any DRC record.

**Text layers are mostly native but the pattern inverts between years — check, never assume.**
FY2024: 12 of 14 native (exceptions: Volume 1 *Recettes*, and the December ESB *commentaires*).
FY2025: all native. FY2026: the **enacted** volume native but the **proposed** volume (Doc n°6,
912pp) a scan, and **all three quarterly PEB commitment plans image-only**. So the year with the best
enacted document has the worst draft.

**⚠ THE HALF-YEAR EXECUTION REPORT ON YEAR N IS FILED INSIDE YEAR N+1's BUDGET PACKAGE.** *Document
n°3* of the PLF package is always *"rapport d'exécution à fin juin"* for the **previous** year — the
FY2025 package carries the FY2024 report (33pp), the FY2026 package carries the FY2025 report (52pp).
**A sweep that reads only its own year's folder misses it in both directions**; pull Document n°3
from year N+1 whenever sweeping year N.

**The *projets annuels de performance* volume is growing very fast: 179pp (FY2024) → 520 (FY2025) →
870 (FY2026)**, all native. This is the programme-grain instrument — the enacted volumes are
organised by *section / rubrique / chapitre*, i.e. administratively and economically, so the PAP is
the only document that says what the money is *for*. **Whether the growth is programme budgeting
reaching more ministries or deeper per-ministry reporting is not established**; compare ministry
counts before characterising it.

**Block 4c — DRC is the textbook "law enacted, authority unfunded" case, pending confirmation.** The
**Code du numérique** (Ordonnance-loi n°23/010 du 13 mars 2023) regulates personal-data processing;
the practitioner consensus is that it creates **no independent authority with sanctioning powers**.
No data-protection body appears in the FY2024 section index. **Confirm against the full section lists
of all three enacted volumes before stating it on the hub** — an index is not a section list.

**The identity programme is the richest non-budget seam.** ONIP's FY2026 credit was *"moins
conséquente"* than needed (Actualite.cd, 2026-05-29), so it turned to a **PPP**; a 2026 *collectif
budgétaire* carrying its revised provisions is before the Assembly; and the previous
**Idemia/Afritech contract was US$1.2bn, cancelled after the Inspection générale des finances found
it over-invoiced** (confirmed by Actualite.cd with Lighthouse Reports and Bloomberg). The last
national identification was **1984**. The wiki now holds the enacted LF 2026, so **ONIP's actual
figure is recoverable** — convert the qualitative claim into a number at extraction.

### DR Congo — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-07-27)

**31 documents, 3 country-years, 6 records, no new archetype** — the enacted volumes are a
*développement par titre* in PDF and match **archetype M** (LOLF full estimates volume that states
its own origin split) closely enough that nothing was added to the library. What DRC adds is the
execution side, noted below.

**THE MACHINERY-OF-GOVERNMENT CHANGE IS THE HEADLINE, AND IT BREAKS BOTH SERIES.** The section names
in the enacted volumes change between FY2025 and FY2026:

| Section | FY2024 | FY2025 | FY2026 |
|---|--:|--:|--:|
| **52** *Postes, Télécoms **et NTIC** (PTNTIC)* → *Postes **et** Télécoms* | 132,595,229,324 | 145,650,630,007 | **55,095,958,006** |
| **71** *Numérique* → ***Économie** numérique* | 87,134,433,991 | 60,627,481,411 | **226,713,223,741** |

The **NTIC mandate is stripped from section 52 and the money follows**: 52 falls 62%, 71 rises 274%.
**Neither series is readable alone across that boundary.** Combined the two are 219,729,663,315 →
206,278,111,418 → 281,809,181,747 FC, i.e. **0.58% → 0.45% → 0.57% of the budget** — so section 71's
apparent explosion is mostly a transfer, and saying "DRC quadrupled its digital ministry" would be
wrong. Read the *Synthèse des dépenses par administration* pages (PDF ~p96–99 FY2024, ~p86–89 FY2025,
~p133–136 FY2026) for clean section totals; they are far more reliable than parsing the detail block.

**THE ORIGIN GATE IS PRINTED, AND IT IS DECISIVE FOR SECTION 52.** The detail block groups every
section into `Fonctionnement des Ministères`, `Interventions Économiques…`, **`Investissements sur
Ressources Extérieures`** and **`Investissements sur Ressources Propres`**. For PTNTIC the external
group is **72% of the whole section in both FY2024 (95,512,273,724 of 132,595,229,324) and FY2025
(105,512,273,724 of 145,650,630,007)**. Recording the section total as domestic spend would overstate
it nearly fourfold.

**⚠ AND THE FINANCIER IS NAMED IN ONE YEAR ONLY.** FY2024 reads
`193016 Banque mondiale / Projet CAB5 cinquième phase — 95,512,273,724 FC`. FY2025's external group is
three *unattributed* lines (*Acquisition d'equipements divers* 92,291,041,224 · *Rehabilitation du
batiment du SG* 12,591,650,000 · *Acquisition des vehicules…* 629,582,500). FY2026's section 71
external line is `261003 Projet d'appui à la transformation numérique en RDC /` — **the label ends at
a bare slash and no funder follows**. Per the origin gate a line naming no funder beyond "external"
**fails fact 1**, so no `non-state` record was built from the FY2025 or FY2026 lines and the fisc was
not credited with them; magnitudes are recorded in the notes. **Check for a financier string before
assuming the external group is anonymous — DRC names it sometimes.**

**⚠ THE FUNCTIONAL AND ADMINISTRATIVE CLASSIFICATIONS DO NOT MAP ONTO EACH OTHER.** FY2024's
execution états are published only by function; sub-function `04600 Poste, télécommunications et
technologies de l'information et de la communication` shows Crédits Votés **158,331,308,819 FC**,
which is **neither section 52 (132,595,229,324), nor section 71 (87,134,433,991), nor their sum
(219,729,663,315)**. **No FY2024 outturn was claimed for either section.** This is the trap that would
have produced a confident, wrong execution rate; the arithmetic is what caught it.

**THE EXECUTION DATA IS THE RICHEST IN THE COLLECTION — SIX COLUMNS — BUT ONLY ONE YEAR REPORTS BY
SECTION.** The ESB tables run `Crédits Votés | Créd. Après Vir. | Engagements | Liquidations |
Ordonnancements | Paiements` — appropriated, revised, then the French commitment chain, then released
and actual. FY2025's single year-end file `situation_prov_esb_fmi_31122025.pdf` (12pp, native) has a
**Tableau 3 by administrative section**, and its `Crédit voté` for section 71 is **60,627,481,411 FC —
matching the enacted volume to the franc**, which is the cross-foot that validates the whole join.

> **Section 71, FY2025: voted 60,627,481,411 · engagé 68,457,537,329 · ordonnancé 68,278,687,329 ·
> payé 31,358,784,468 — 51.7% paid against 112.9% engaged.**

**The commitment chain ran far ahead of cash.** That is a different failure from under-commitment and
is visible only because DRC publishes all six stages; a two-column extract would show either
over-commitment or under-spending but not both at once.

**⚠ FY2025 HAS NO APPROPRIATED STAGE AT ALL.** DRC published no original enacted LF 2025 —
`/lois-de-finances/` stops at 2024 and `budget2025/vote/lf_2025_depenses.pdf` returns 404. The only
enacted FY2025 detail is the **rectificative n°25/044 du 28 juin 2025**. So FY2025 records are
`baseline_stage: revised`, `execution_pct_vs_revised` is 51.7% and
**`execution_pct_vs_appropriated` is blank and must stay blank** — there is no published figure for
what parliament first voted, and reporting absorption as credibility is precisely what the driver's
two-basis rule forbids.

**THE NAMED PROJECTS, AND ONE FIGURE THAT LOOKS LIKE A TYPO AND IS NOT.** The domestic investment
groups cross-foot exactly, which is what licenses quoting the lines:

- **FY2024 section 52** → 16,197,837,429: *Etude de l'implémentation de Télécentres* 8,000,000,000 ·
  *Acquisition des équipements GATEWAY de contrôle* (SCPT) 4,193,837,429 · *Rehabilitation du batiment
  du SG* 2,000,000,000 · ***Accès au câble sous-marin EQUIANO*** (SCPT) 2,000,000,000 · *Optimisation
  du Data Center* (SCPT) 4,000,000.
- **FY2026 section 71** → 53,620,781,085: *Aquisition de Data Center National* (sic) **26,756,546,346**
  · *Acquisition d'un intranet du gouvernement* 20,219,907,700 · *Acquisition d'un centre des données
  du ministère* 5,502,672,861 · *Acquisition d'un système de gestion électronique* 1,121,000,000 ·
  **_Acquisition du système national d'identification_ 20,654,178**.

**That last line is twenty million francs — roughly US$7,000 — against a national data centre at
twenty-six billion.** It is not a transcription error; it cross-foots. And it corroborates, from the
enacted law, the ONIP official's statement that LF 2026 gave the identification programme far less
than it needed — the qualitative claim in the press becomes a figure from the budget.

**⚠ PARSING TRAP — the detail block bleeds past the section boundary.** A naive "read N pages from the
section header" walk runs into the following section's personnel lines, which are an order of
magnitude larger (a *Traitement de base du personnel* row of 5,941,817,204,453 FC appeared inside what
looked like section 52's investment group). **Gate every block on its printed group total**: each
`Investissements sur Ressources Propres` figure must equal the sum of the lines beneath it, and where
it does not, the block has over-run. That check is what separated the real lines from the bleed here,
and it should be mandatory rather than optional.

**Not worth extracting:** LF Volume 1 (*Recettes*) — image-only and revenue-side, no digital line.
The quarterly *Plans d'engagement budgétaire* — image-only, and in any case a commitment **plan**, not
a stage; never record them as `released` or `actual`.

**Case 5: nothing to reset.** The wiki held no COD `domestic-state` records before this run.

#### DR Congo — two corrections from the acquisition pass, same day (2026-07-27)

The COD sweeps and extract wrote two statements that the acquisition pass, run an hour later inside
`update wiki`, showed to be wrong. Both are corrected in the run files and on the hub; recording them
here because **the error was the same in both cases — treating "the budget ministry does not publish
it" as "it does not exist"**.

1. **The 2024 rectificative WAS enacted.** The batch recorded that whether it was enacted "is not
   established", because `budget.gouv.cd` publishes only the *projet* (Documents A/B/C, September
   2024) and `/lois-de-finances/` lists no 2024 rectificative. It exists: **loi de finances
   rectificative n°24/009 du 20 décembre 2024**, cited by title in both the Cour des comptes report
   and the *loi portant reddition des comptes*. Only its **volume** is unpublished.
2. **The 2024 accounts have been audited and closed.** The batch recorded that "no audit output
   exists for any in-scope year". The **Cour des comptes** published its *Rapport général sur le
   contrôle de l'exécution de la loi de finances n°23/056 … pour l'exercice 2024* on **31 December
   2025** (listed at `courdescomptes.cd/rapports-et-audit/`), tabled it in the Senate on 1 November
   2025, and restated the central-government balance at **−1,122.2 billion CDF**. Parliament then
   passed **loi n°25/059 du 23 décembre 2025 portant reddition des comptes**: recettes exécutées
   **35,514,367,066,272 FC (79.97%)**, dépenses **35,872,482,971,094.60 FC (80.78%)**, déficit
   **358,115,904,822.60 FC**.

**The generalisable lesson: DRC's audit and accountability documents live on `courdescomptes.cd`, not
on `budget.gouv.cd`, and the budget ministry publishes lois de finances but neither reddition laws nor
rectificative volumes.** Sweep the Court's site as a Track A institution in its own right for any
francophone state with a *Cour des comptes* — the budget ministry's library is not the whole state.
**`courdescomptes.cd` refuses connections from this network**; it reads through an external cache,
which returns the listing but not the files.

### Cameroon — the bill is native, the law is a scan, and the budget ministry's own site is unreachable (sweep, 2026-07-29, FY2024/FY2025/FY2026)

- **Fiscal year:** calendar. The *Budget citoyen 2025* says it in terms — the budget covers "une année civile, c'est-à-dire du 1er janvier au 31 décembre". Document label `2024` / `2025` / `2026`.
- **THE STRUCTURAL FINDING, and it is the CAR pattern again: the *projet de loi de finances* is fully machine-readable while the enacted law is a page-image scan.** Three years, three times: PLF 2024 122pp / 273 672 chars, PLF 2025 111pp / 239 875 chars, PLF 2026 154pp / 367 955 chars — all native, zero OCR needed. Against that: LF2024 (FR) **0 chars**, LF2025 110pp **2 158 chars**, LF2026 151pp and **112 MB for 2 265 chars**. **Always fetch the PLF before commissioning OCR on the enacted law.** This is now the third corpus where the rule holds (CAR, and Cameroon in both language editions).
- **One exception, and it is a trap: the FY2024 *English* promulgation carries an OCR layer** (262 081 chars, all 59 HEADs of SECTION EIGHTY-ONE). It looks native and is not. The `www.prc.cm` watermark is broken across lines by the OCR and injects stray `w`/`m`/`p`/`r`/`c` at line starts, and digit groups split and merge — `21459760` and `2154 9760` for one figure that should read `21 549 760`. **Treat every amount in it as a locator until cross-footed against the PLF.** The trick was not repeated: the FY2025 and FY2026 English promulgations, and the FY2024 settlement law in both languages, are scans with no text layer at all.
- **`www.dgb.cm` (195.24.207.193) is dead from this network** — connection refused or timeout on 443 *and* 80, over both Cloudflare and Google DoH, four attempts. It is the Direction Générale du Budget, the canonical publisher. **Two routes around it, both verified:**
  1. **The Internet Archive serves dgb.cm's PDFs byte-for-byte** via `web.archive.org/web/<ts>id_/<url>`. Watch for truncation — two of four fetches came back short and needed `curl -C -` to resume; check for a trailing `%%EOF` before trusting a file.
  2. **`rfp.cm` mirrors the DGB's entire PLF annexe set** and is directly fetchable, with an open WordPress REST API (`/wp-json/wp/v2/media?media_type=application`, 288 items). This is the better route and should be tried first on any future Cameroon run.
- **Track B: both national sites expose a WordPress REST media API, and that is the whole library in two fetches.** `minfi.gov.cm/wp-json/wp/v2/media?per_page=100&media_type=application` enumerates **489 documents**; `rfp.cm` the same for 288. No pagination scraping, no bot guard, default UA accepted. Where a ministry runs WordPress, hit the REST API rather than the document pages.
- **`prc.cm` is the promulgation archive and its file links are hidden in an iframe.** Act pages live at `/fr/actualites/actes/{lois,ordonnances}/<id>-<slug>`, the PDF at `/files/xx/yy/zz/<md5>.pdf`, exposed only as `src="…"` on the `/fr/multimedia/documents/<id>-<slug>` page — **not** on the act page itself, which is why a naive scrape of the act page returns nothing. English editions are separate documents under `/en/multimedia/documents/<id>`, usually at id−1 or −2 from the French.
- **The `chambredescomptes.cm` publications sit on a Nextcloud instance.** Page links are `drive.chambredescomptes.cm/s/<token>`; append **`/download`** and they serve the PDF directly, no auth. All four FY2024 audit documents came through this way.
- **Cameroon revises the budget by presidential *ordonnance*, ratified months later by law — not by a rectifying finance law.** Ordonnance n°2024/001 du 20-06-2024 (ratified by Loi 2024/010 du 24-07-2024) and Ordonnance n°2025/001 du 11-07-2025 (ratified by Loi 2025/014 du 17-12-2025). **Both ordonnances are readable** (129 728 and 92 002 chars) where the laws they amend are not — so *the revised stage is better documented than the appropriated one*. **The revised stage has two candidate dates**; say which is being used. Expect the FY2026 ordonnance around June–July 2026.
- **The vote unit is `CHAPITRE` in FY2024–25 and `SECTION` in FY2026** — 59 of them, at programme grain, with AE and CP columns, objective and indicator. Scale is printed **`(Unité : Milliers FCFA)`** / `(En millier de FCFA)`. The 1 000× trap, live.
- **MINPOSTEL is chapitre/section 45, and FY2026 breaks the series.** FY2024–25: programmes **129** densification du réseau postal, **130** développement de l'écosystème national du numérique, **131** gouvernance et appui institutionnel, **132** sécurisation de l'écosystème national du numérique (132 first appears in FY2025); internal codes 149/150/151/152. **FY2026 renumbers to 450 / 451 / 452 (internal 141/142/143) and fuses 130 and 132 into 451**, "développement sécurisé et inclusif de l'écosystème national du numérique" — the merger the CIEP/MINPOSTEL programme review had proposed for the 2026-2028 triennium. Same lesson as Kenya's Vote 1122 restructure: **a series keyed on programme code or label needs a mapping row at 2026.**
- **Programme 451's indicator set is the clearest statement of digital policy targets in this corpus**: EGDI, national cybersecurity index, national broadband coverage, linear metres of fibre laid, rate of digitisation of public services, share of incidents handled by the national CERT, and public-institution compliance with cybersecurity standards.
- **The regulators' money is in the finance law's articles, not the vote — and it is a clean dated series.** Each year an article caps the own-source revenue affected to each agency: **ANTIC** FCFA **5,5bn (2024) → 7,5bn (2025) → 8,0bn (2026)**, funded by a **0,5% levy on electronic-communications operators' turnover** plus security-provider licence fees, penalties and numbering/frequency shares; **ART** FCFA **15,0bn (2024) → 18,5bn (2025) → 18,5bn (2026)**, funded by a **1,5% levy on operators' ex-tax turnover** plus the same fee families. **These are ceilings on affected own revenue, not appropriations** — do not record them as budget lines without saying so.
- **The Special Telecommunications Development Fund was abolished in FY2024.** SECTION THIRTY-EIGHT of LF2024 repeals s.22 of LF2020, which had created the CAS, and folds its revenue and expenditure into the general budget. Its revenue base was **3% of operators' turnover**, universal-directory income, a share of authorisation fees and **50% of ART's year-end budget surplus**; its expenditure covered universal service, ICT development and **network and information-system security**. Cameroon's universal service fund therefore *ceases to be traceable as a fund* from 2024 — a real loss of visibility, and the reason a USF figure cannot be given for these years.
- **Three of the eleven Comptes d'Affectation Spéciale are digital** (2024, FCFA): *Fonds spécial de sécurité électronique* 1 500m, *Développement du secteur postal* 900m, *Production des titres de transport sécurisés* 6 000m. The CAS envelope then **nearly doubles for FY2026** (66,9 → 132,5bn, +98,1%) — worth reading against the 2024 abolition.
- **Identity money surfaces as revenue policy, not as a vote.** The FY2024 ordonnance raises the CNI stamp duty **2 800 → 10 000 FCFA**, fixes consular card duties at 20 000–30 000 FCFA by region, makes collection of passport and identity-title receipts **exclusively electronic**, and provides that it *"peut le cas échéant être concédé à un prestataire privé"*. So the identity system is being financed from its own fee stream through a concession, which is exactly the shape that leaves no appropriation to find. Look at the revenue articles, not the DGSN vote.
- **Block 4c — the finding, and it is a derogation.** Cameroon enacted **Loi n°2024/017 on personal data protection on 23 December 2024**. Across three native volumes totalling 387 pages, **no data-protection authority appears under any wording and no line funds one.** The phrase *protection des données à caractère personnel* occurs **once in the three volumes**, in FY2026, and it is **Article L 42 of the Livre des Procédures Fiscales overriding the law** so that tax officials may compel documents "sans que puissent leur être opposés … la loi sur la protection des données à caractère personnel". The first appearance of the statute in a finance law is its suspension. The supervisory function appears to sit with ANTIC, but **the gazette text of Loi 2024/017 is not held** (acquisitions), so the single-mandate carve-out cannot be applied to ANTIC's 8bn — its mandate plainly also covers cybersecurity and certification.
- **The audit stage is genuinely strong here, and unusually so for the region.** The **Chambre des Comptes de la Cour Suprême** published, in September 2025 for FY2024: a 162-page *rapport sur l'exécution de la loi de finances* (native), the *avis sur le projet de loi de règlement*, a *rapport de certification du compte général de l'État*, and a *rapport définitif sur le contrôle interne* — and Parliament then enacted the **loi de règlement (Loi n°2025/011 du 17-12-2025)**. That is a complete, on-time audited stage 12 months after year-end. **Part Three of the execution report audits the ministries' Rapports Annuels de Performance and finds them unreliable** — inconsistent data, wrong realisation rates, support programmes too large a share of the vote. Anyone building performance series from Cameroonian RAPs should read that chapter first.
- **MINPOSTEL's credit-consumption rates are published, and they are damning for the digital programme.** Per the CIEP/MINPOSTEL programme review on dgb.cm: programme 129 consumed 99,37% (2023) and 54,17% (2024); **programme 130 — the digital ecosystem programme — consumed 14,67% (2023) and 22,66% (2024)**; programme 132 consumed 97,15% and 100%. So the digital development line is appropriated and then overwhelmingly not spent, while the cybersecurity line is spent in full. **This is the single most useful execution fact found for this country** and it is not in any budget document — it is in a DGB news article.
- **MINPOSTEL's investment budget is small**: FCFA **15,1 milliards (2024)**, 1,3% of the infrastructure block and **0,23% of the general budget**, per the Budget citoyen 2024's BIP-by-ministry table.
- **Searched, found nothing:** any FY2025 execution report (the FY2024 one appeared about six months in arrears); any data-protection authority line in any year; any Fonds Spécial des Télécommunications figure after its 2024 abolition; ANTIC or ART annual reports; a FY2024 annexe set equivalent to FY2025's (rfp.cm's library starts at the FY2025 bill).
- **Mirrors worth knowing:** `rfp.cm` (the DGB annexe set, WP REST API), `cabri-sbo.org/uploads/bia/` (republishes the FY2024 execution review byte-identically), `impots.cm` and `faolex.fao.org` (both carry LF2025, both scans), `lc-doc.com` (Cameroonian document library, reachable).
- **TOFE and the *Rapport sur la situation et les perspectives* are aggregate-only or scanned** and will not yield digital lines: TOFE December 2024 is 19pp of image tables with 6 624 extractable characters and no ministry detail; the 2024 *Rapport sur la situation…* is a 49-page scan with zero.

### Cameroon — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-07-29)

- **Archetype Q added** for the compact programme-budget summary table (see the strategy library). Two properties force a geometry parse: **thousands are separated by a space**, so `18 611 000` arrives as three words and a word-wise parse silently returns `18`; and **the code column is stacked**, so `-layout` prints three programme codes above three amounts and pairs the wrong ones. `scripts/cmr-plf-extract.py` binds rows by `top` and re-joins numeric tokens by x-gap. Every vote cross-foots.
- **MINPOSTEL is chapitre/section 45. The series, CP, milliers FCFA, each year cross-footing exactly to the printed vote total:**

  | Programme | FY2024 | FY2025 | FY2026 |
  |---|--:|--:|--:|
  | 129 / 450 densification, then régulation du marché postal | 1 286 193 | 1 388 063 | 120 000 |
  | 130 développement de l'écosystème national du numérique | 9 489 364 | 10 330 875 | — |
  | 131 / 452 gouvernance et appui institutionnel | 3 389 399 | 5 855 018 | 9 994 543 |
  | 132 sécurisation de l'écosystème national du numérique | 921 044 | 1 037 044 | — |
  | 451 développement sécurisé et inclusif (130 + 132 merged) | — | — | 19 494 457 |
  | **Vote total** | **15 086 000** | **18 611 000** | **29 609 000** |

- **The postal programme is being defunded, and it is the sharpest number in the run.** Programme 129/450 falls from 1 388 063 to **120 000** between FY2025 and FY2026 — a **91,4% cut** — while the merged digital programme takes 19 494 457. Cameroon's posts-and-telecommunications ministry is, on these figures, ceasing to be a postal ministry.
- **THE ORDONNANCE IS THE KEY TO THE APPROPRIATED STAGE, and this is the country's most useful structural property.** The enacted finance law is a scan in every year, so on its own the corpus would carry `proposed` only. But **the mid-year ordonnance restates ARTICLE QUATRE-VINGT-UNIÈME in full, with four columns — `AE VOTE | AE MODIFIEE | CP VOTE | CP MODIFIE`** — at programme grain for all 59 chapitres. The `VOTE` columns *are* the enacted appropriation. So **a native ordonnance recovers the appropriated stage from a scanned law, and supplies the revised stage in the same table.** Same shape as CAR's `Collectif N-1` comparator column, but within the year rather than across years.
- **Reconciliation, and it holds.** The ordonnance's `AE VOTE` column matches the PLF programme by programme for chapitre 45 in both FY2024 and FY2025, and cross-foots to the same vote total. Bill and enacted law agree for this vote; `proposed` and `appropriated` therefore carry the same figure, which is a reconciliation and not a duplication. **One caveat:** the FY2024 ordonnance prints `CP VOTE 15 088 000` against an `AE VOTE` of `15 086 000` and a column that sums to `15 086 000`. The `8` is an OCR misread of `6`. Cross-footing caught it; a naive read would have carried a 2 000-thousand phantom.
- **Neither mid-year revision touched the digital programmes.** FY2024: only 129 moved, +182 000 (1 286 193 → 1 468 193). FY2025: only 129 moved, −71 000 (1 388 063 → 1 317 063). Programmes 130, 131 and 132 are identical in the `VOTE` and `MODIFIE` columns in both years. So Cameroon's +533bn FY2024 supplementary and its FY2025 revision both left digital spend exactly where the vote put it.
- **⚠ THE CROSS-VOTE TRAP, and it nearly produced a badly wrong record.** In the stacked layout, a vote's programme **codes, labels, objectives and amounts are four independent vertical stacks** paired only by position. A keyword scan over a ±5-line window therefore crosses the streams. Scanning MINDCAF (chapitre 37) FY2025 for `numérique` returned a hit beside **12 591 987** — which is *Protection et développement du patrimoine de l'État*, a buildings line. The word `numérique` belongs to the **objective of programme 026** four rows above. **Read the whole vote block and pair by position before recording anything from a cross-vote keyword scan.** The scan locates; it does not identify.
- **The genuine cross-vote digital line is the cadastre, and it is consistent across all three years.** MINDCAF programme **026 / 380 *Modernisation du cadastre***, objective *"Disposer d'un cadastre national **numérique** apte à répondre aux défis de gouvernance foncière moderne"*, indicator *"Proportion de communes disposant d'un plan cadastral **numérique**"*: **1 203 574 (FY2024) → 1 567 500 (FY2025) → 874 046 (FY2026)**, a 44% cut in the last year. FY2026 adds indicators for the *Réseau Géodésique National du Cameroun* and for plans *numérisés et géoréférencés*.
- **A `partial` candidate not recorded:** MINFOPRA (chapitre/section 50) programme 040/480 *Amélioration de la gestion des ressources humaines de l'État* (5 973 118 FY2024; 7 121 372 FY2026) names **SIGIPES** — the state HR and payroll information system — but only as one of seven listed tools ("SIGIPES, fiches de poste, plan de recrutement, plan de formation, fichier assaini, texte organique, cadre organique"). The digital share is not separable, so under the envelope rule this is `partial` at best; left unrecorded pending a reading of the annexe *rapports*, which is where the split would be if it exists anywhere.
- **THE EXECUTION STAGES ARE HELD AND NOT EXTRACTED — the main gap of this pass.** The Chambre des Comptes FY2024 execution report is native (250 615 chars) and **does carry a per-ministry × per-programme execution table** with three columns in full FCFA (dotation / exécution / écart), plus a performance-indicator table giving programme 130 a realisation figure of **17,42%**. Neither was recorded, because **the rows drift against their labels under `pdftotext -layout`** — the execution row reading `44 : MINPOSTEL 8 373 527 000 …` carries chapitre 45's label against a neighbouring ministry's figures, and there is no printed subtotal in reach to cross-foot against. Per the pass's own rule, digits that will not cross-foot are not recorded. **This is the single highest-value re-extract target for this country**: geometry binding of that table would yield `actual` and `audited` stages for FY2024 and turn a three-stage record into a five-stage one. Flagged in the manifest.
- **The half-year execution review is aggregate-only.** Despite being native and 44pp, it carries no chapitre or programme breakdown — no MINPOSTEL mention at all. Cameroon's in-year execution reporting does not reach ministry grain; only the audit does. Worth knowing before spending sweep cap on it again.
- **Case 5 did not apply.** The wiki held **no** CMR domestic-state records before this run — 25 non-state deals and nothing else — so there was no reporting-built figure for the budget documents to supersede. This is the clean case: the country's domestic-state corpus starts at budget-document tier.
- **8 records built**, all `scope_confidence: whole`: MINPOSTEL 130 and 132 for FY2024 and FY2025 (proposed → appropriated → revised), MINPOSTEL 451 for FY2026 (proposed only), and MINDCAF 026/380 for all three years. **FY2026 is `proposed` throughout** — its enacted law is a 112 MB scan and reading it is what would promote the year.

### Republic of the Congo — a well-run document library full of scans, and the one year with no bill (sweep, 2026-08-03, FY2024)

- **Fiscal year:** calendar. `Loi n° 39-2023 du 29 décembre 2023 portant loi de finances pour l'année 2024`, promulgated three days before the year it funds; the outturn table is `TOFE au 31.12.2024` with a `LF 2024` column running January to December. Document label `2024`. CEMAC convention, same as Cameroon and CAR.
- **Track B is a solved problem here, and it is the best-organised finance-ministry library in the corpus after DR Congo's.** `www.finances.gouv.cg` is **Drupal 7** with a `documentation` view at `/fr/documentation`. Three things make it enumerable in minutes: rows are a plain `<table class="views-table">` with a `dc:date` attribute per row; **the exposed date filter works, in US format** — `?field_document_date_value%5Bmin%5D%5Bdate%5D=10/01/2023&field_document_date_value%5Bmax%5D%5Bdate%5D=08/03/2026` cut 314 pages to 50; and every file is at a stable `/fr/download/file/fid/NNNN`, no auth, no bot guard, correct `Content-Type: application/pdf`. **`?keys=` free-text search works and pages; the `?term_node_tid_depth=` type filter silently returns empty even for valid tids** (39 = *Loi de Finance* returns `view-empty`). Use `keys`, not the type facet.
- **THE STRUCTURAL FINDING — the CAR/Cameroon rule holds a fourth time, and FY2024 is the year it cannot help.** The *projet de loi de finances* is fully machine-readable and the enacted *loi de finances* is a page-image scan. **PLF 2025: 400 688 chars, native. LF 2025: 144 chars. LF 2024: 150 chars over 150 pages. Loi 1-2024: 5 chars over 5 pages. Journal Officiel Spécial n°3-2024: 75 chars over 75 pages.** Every scan yields nothing but form feeds. **But there is no PLF 2024.** The library carries PLF 2019, 2020, 2021, 2022, 2023, 2025 and 2026 and no 2024 — the single gap in the series, falling exactly on the year asked for. **Always check the PLF series for the specific year before assuming the rule rescues you.**
- **No native document carries FY2024 allocations at all.** PLF 2025 prints `PREVISIONS 2025` with **no prior-year comparator column** — unlike CAR's `Collectif N-1` or Cameroon's ordonnance `AE VOTE` columns, Congo's bill gives you nothing about the year before. So OCR of the LF2024 scan is the only route, full stop.
- **The per-ministry allocation table is ARTICLE 41 of the finance law**, covering **57 institutions and ministries** — established not from the law (unreadable) but from a Congolese budget-analysis piece (`ekolo242.cg`) that cites the article number. **Reading local budget commentary to locate the article is cheaper than OCR'ing 150 pages to find it.**
- **The vote unit is `Code NN` (ministry/institution) → three-digit programme code.** Digital is **Code 45 Postes, télécommunications et économie numérique**, programmes **117 Pilotage de la politique du ministère** and **118 Poste, télécommunication et économie numérique**. Two programmes only — a much flatter structure than Cameroon's four.
- **Amounts are printed in FULL FRANCS CFA with space-separated thousands** (`1 820 078 590`), and there is **no `en milliers` header** — the opposite of Cameroon. But **the TOFE is printed `En milliards de FCFA`**. So within one country the same fiscal year is published at unit scale and at billion scale in two documents that will inevitably be compared. **Read the scale header on every artefact separately.**
- **The cross-vote trap applies unchanged.** In the PLF 2025 layout, a vote's codes, labels and amounts are independent vertical stacks paired only by position — programme rows regularly print an amount belonging to the row below. Bind by `top` coordinate; do not word-parse.
- **Execution reporting has a six-year hole and reopened for FY2025, not FY2024.** Series: `au 31 mars 2018`, `au 30 juin 2018`, `au 31 mars 2019` — then nothing until **`Au 31 décembre 2025`, posted 2026-03-02**. That FY2025 report is **native (103 818 chars)** and carries **`ANNEXE 4 : EXECUTION DES DEPENSES PAR PROGRAMME`** — `PREVISIONS REAJUSTEES | EXECUTION | % D'EXEC` at programme grain. **Code 45 shows 24 078 665 787 appropriated against 472 102 000 executed, 15,1%** — the same shape as MINPOSTEL's 14–22% consumption in Cameroon, and worth reading as a regional pattern rather than a Congolese quirk. Rows drift under `-layout`; geometry binding required. **No FY2024 equivalent exists.**
- **The TOFE is the only FY2024 execution document, and it is aggregate-only.** 3 pages, native, `Nature | LF 2024 | Janvier … Déc | T1–T4 | Réal au 31 déc | % LF`. Budget général **2 605,7 → 2 330,5 Mds, 89,4%**. **No ministry, vote or programme breakdown**, so it supports country-level context and no digital record. The whole 2015–2024 TOFE series was uploaded in one batch on **2026-04-08**, so its library date is a posting date, not a publication date.
- **Congo has not enacted a *loi de règlement* since exercice 2013** (`Loi n°47-2014 du 31-12-2014`, preceded by `Loi n°33-2013` for 2012). No settlement law, no audit report, nothing after that under `règlement`, `reddition` or `compte général`. The **Cour des comptes et de discipline budgétaire has no reachable domain** — `cour-des-comptes.cg` and `ccdb.cg` are both **NXDOMAIN over Cloudflare DoH**. **The audit stage does not exist for any recent Congolese year, and that is the finding.**
- **No *loi de finances rectificative* for 2023, 2024 or 2025.** LFRs exist for 2016, 2017, 2020, 2021, 2022. FY2024's only amendment is **Loi n° 1-2024 du 25 janvier 2024**, which reporting says touches **Article 36** — a fiscal provision, not the ceilings. Congo does **not** use the Cameroonian mid-year ordonnance, so there is no native instrument restating the vote.
- **⚠ `Journal Officiel Spécial n°3-2024 du 7 mars 2024` is staged on a pattern, not on content.** 75-page scan, no description on the node page. The identification as the gazetted LF2024 rests on the library's own `Journal officiel édition spéciale n° 3-2026 (Loi de finances 2026)` — special number **3** of its year. A pattern of one. **OCR page 1 before trusting it.**
- **Block 6 — the regulator's and the agency's money is set by article in the finance law, not appropriated in the vote.** The native PLF 2025 carries a revenue-sharing key table across **ETAT | ADEN | ARPCE | ARTF | Projet système de facturation**, with a `NUMERIQUE` row at **15% / 20% / 30%**, a licence-fee split across `Etat | ARPCE | ADEN | Opérateurs téléphonie | Prestataire`, and an article assigning **all VAT ARPCE collects from non-resident firms to the state budget**. Identical in shape to Cameroon's ANTIC/ART ceilings. **Read the finance law's articles, not the Code 45 vote.**
- **Sites and their states, 2026-08-03.** Reachable and useful: `finances.gouv.cg` (Drupal library, above), `sgg.cg` (Journal officiel at stable paths `sgg.cg/JO/YYYY/congo-jo-YYYY-NN.pdf`, plus *comptes rendus du conseil des ministres* at `sgg.cg/ccm/`), `aden.cg` (WordPress REST API, `?media_type=application` — but only **15** documents, almost all statutes), `presidence.cg`, `anssi.cg`, `armp.cg`. **Unreachable or useless:** `www.arpce.cg` is a **Nuxt SPA serving an identical 4 988-byte shell for every path** including `/sitemap.xml`, `/_payload.json` and `/api/*` (`robots.txt` is one byte; the entry bundle names `drf.`, `drp.`, `drsce.` and `ssfn.arpce.cg`, untried); `www.assemblee-nationale.cg` serves a **full-page maintenance placeholder**; `www.senat.cg` fails TLS; `armp.cg`'s `publications-reports.php` and `publications-statistics.php` carry **no document links at all**, so no procurement plans; `ptne.gouv.cg`, `budget.gouv.cg`, `dgb.gouv.cg`, `journal-officiel.cg` do not resolve. **`imf.org` returns HTTP 403 from this network** to both a browser-UA scripted fetch and WebFetch — the Congo 2024 Article IV (CR 2024/251) is an acquisition, not an absence.
- **Local budget journalism is unusually good and is the cheap way in.** `ekolo242.cg` ("Le Congo d'Abord") publishes per-title and per-ministry breakdowns of each finance law with the article numbers cited; the **French Treasury's** `tresor.economie.gouv.fr/Pays/CG` posts a budget note per year with the aggregates and the financing gap. Neither replaces the law, but between them they tell you **where in the law to look** before you commission OCR.
- **Searched, found nothing:** any FY2024 execution report; any *loi de règlement*, *reddition des comptes* or Cour des comptes output after 2013; any *budget citoyen*, DPBEP, CBMT or multi-year programming document; any procurement plan; any ARPCE, ADEN or FASUCE annual report or budget; any *annexe explicative* for 2024 (they exist for 2016, 2017, 2018 and 2022); any PLF 2024 under any wording.

### Republic of the Congo — the gazette is native where the ministry's copy is a scan, and it overturns four FY2024 findings (sweep, 2026-08-03, FY2025)

- **THE RULE, AND IT IS THE MOST TRANSFERABLE THING THIS COUNTRY HAS TAUGHT US.** `finances.gouv.cg` publishes finance laws as page-image scans; **`sgg.cg`, the *Journal officiel*, publishes the same laws with a text layer.** Five for five in this run: LF2024 **150 chars → 307 225**, Loi 1-2024 **5 → 4 283**, LF2025 **144 → 274 497**, plus a native LFR2025 (280 012) and a native settlement law. The FY2024 sweep called OCR of the LF2024 *"the single highest-value action available for Congo"* with *"no route around it"*; the route was one hop sideways to the publication of record. **Before commissioning OCR in any Francophone state, check whether the gazette carries the same instrument.**
- **`sgg.cg` mechanics.** Weekly issues and special editions both at `sgg.cg/JO/YYYY/congo-jo-YYYY-NN*.pdf`; indexes at `/m-journal-officiel/le-journal-officiel.html` and `/m-journal-officiel/journaux-speciaux.html`, paginated **`?page=N&row=230`** (not Joomla `?start=`). Comptes rendus du conseil des ministres at `sgg.cg/ccm/`. **The `fi` ligature does not extract**: `finances` comes out as `fi nances`, `définitivement` as `dé fi nitivement`. Grep `fi ?nance`, or you will conclude the finance law is not in the finance law.
- **The `n°3-YYYY = loi de finances` pattern is FALSE, and an artefact was staged on it.** JO spécial **n°3-2024 is a set of 6 March 2024 decrees reorganising the tax, customs and treasury directorates**; n°3-**2025** is an oil production-sharing contract; only n°3-2026 is a finance law. Congo gazettes its finance law in whichever special edition falls next — **n°6-2023 for LF2024, n°15-2024 for LF2025, n°1-2026 for the settlement law, n°2-2026 for the LFR2025, n°3-2026 for LF2026.** Identify by opening page 2, never by number.
- **CONGO HAS ENACTED SETTLEMENT LAWS SINCE 2013, AND THE FY2024 RUN'S CLAIM THAT IT HAS NOT MUST NOT REACH A PAGE.** `Loi n° 50-2021 du 31 décembre 2021` and **`Loi n° 40-2025 du 31 décembre 2025 portant loi de règlement, exercice 2024`** both exist. The FY2024 run searched the ministry library, which stops at 2014. What is true and narrower: **no *Cour des comptes* report accompanies the settlement law**, and that court has no reachable domain (`cour-des-comptes.cg` NODATA over DoH, `ccdb.cg` NXDOMAIN). Recettes définitives 2024 = **2 327 178 878 278 FCFA**; the per-titre execution sits in annexed **tables F–K**, whose grain is worth checking — it is the only candidate source of an FY2024 `actual` stage.
- **A *loi de finances rectificative* for 2025 exists too** — `Loi n° 41-2025 du 31 décembre 2025`, presented to both chambers 30 October 2025, gazetted 5 January 2026, **`Article premier : la présente loi remplace la loi n° 47-2024`**. A full replacement, not a patch, and **the programme structure moves with it: 21 dotations and 148 programmes against 136 in the initial law.** A Congolese FY2025 record must say which instrument its programme code came from. Again absent from the ministry library, again present in the gazette.
- **The vote unit and the drift are unchanged from FY2024, and the drift is the whole difficulty.** `Code NN` ministry → three-digit programme; digital is **Code 45**, programmes **117** and **118**. In every one of these documents the **codes, labels and amounts are three independent vertical stacks** offset by a variable number of rows — in the enacted LF2025 `Code 45` prints against *Production animale*. **Bind by `top` coordinate; never word-parse.**
- **Two independent cross-checks exist for calibrating that binding, and they are worth more than another hour of geometry.** (1) `ekolo242.cg` publishes a per-ministry breakdown whose three figures cross-foot: Code 45 = **29 858 482 624** = 117 **8 570 082 624** + 118 **21 288 400 000** — that is the **bill's** table. (2) The enacted Code 45 total **24 078 665 787** appears identically as `PREVISIONS REAJUSTEES 2025` in the FY2025 execution report and in the rectificative. **Two instruments printing the same number is the anchor; the printed row order is not.**
- **⚠ `ekolo242.cg` attributes the BILL's figures to the ENACTED law.** Its widely-cited piece cites *"Article trente-septième de la loi de finance 2025 du 30 décembre 2024"* with total **1 970 912 655 342** — but Article 37 and that total are the **PLF**; the enacted law is **Article 38** and **1 958 583 080 014**. Congolese budget commentary is unusually good and this is its characteristic error. **Check which instrument a local figure came from before recording it.**
- **Scale, and Congo prints three of them.** Programme and ministry tables in **full francs CFA**, space-separated thousands, no `en milliers` header. Equilibrium tables `En milliards de FCFA` — **inside the same document**. The TOFE is also `En milliards`. And the execution report's narrative is in milliards while its **`ANNEXE 4` is in full FCFA, six pages apart.** Read the header on every table, not every document.
- **⚠ `ANNEXE 4 : EXECUTION DES DEPENSES PAR PROGRAMME` is headed `(Hors dépenses du personnel)`.** Every execution figure excludes Titre 2. An execution rate read off it and compared to an appropriation that includes personnel is a category error, and the FY2024 run recorded the Code 45 row without noticing the qualifier. **Code 45: 24 078 665 787 appropriated / 472 102 000 executed / 15,1%, non-personnel.**
- **FY2025 is a four-stage year and all four instruments are native**: proposed (PLF, 400 688 chars), appropriated (Loi 47-2024, 274 497), revised (Loi 41-2025, 280 012), actual (execution report, 102 029). Parliament cut the digital vote from **29,86 Mds to 24,08 Mds**, and the ministry spent **~15%** of it. **This is the most complete Congolese fiscal year available and one of the most complete in the Francophone corpus** — a marked contrast with FY2024, which the previous run rated at one and a half stages and which is now three.
- **Block 6 — the own-source money is in two places and both are now readable.** A **named appropriation**: `Article dix-huitième` of the LF2025 opens 18 *comptes spéciaux du trésor* including **`fonds pour l'accès et le service universel des communications électroniques : 1 000 000 000`** (FASUCE, which the FY2024 run could not locate at all) and **`urbanisation des systèmes d'information de gestion des finances publiques : 3 500 000 000`** — a PFM-systems line outside the ICT vote. And **statutory keys**: the *redevance Hub numérique* split `ETAT 20% | ADEN 15% | ARPCE 15% | ARTF 20% | SFEC 30%`, the licence and traffic-tax splits, and the abolition of the FY2024 non-resident-VAT key with the whole of it reassigned to the state budget. **Read the finance law's articles and its comptes spéciaux, not the Code 45 vote.**
- **Block 5 — the comptes rendus du conseil des ministres are cheap and productive.** 14 in the window, ~13 000–25 000 chars each, native. Download, `pdftotext`, grep **accent-insensitively** (`num.rique|donn.es|t.l.communication|identit|informatique|cyber`) — an accent-sensitive grep returns almost nothing because the encoding mangles them. 3 of 14 carried payload, including one (23 July 2025) in which the finance minister reports **FY2024 execution at 2 323,8 Mds / 89,2%** — the state's own outturn statement for a year whose execution report was never published.
- **Sites.** `sgg.cg` (the find of this run), `finances.gouv.cg` (Drupal library *and* a separate unindexed `/fr/articles/` statement seam), `aden.cg` (13 documents, newest 2024-05, none budgetary), `fasuce.cg` (live, **zero PDF links**). Dead: **all four ARPCE data subdomains** — `drf.`, `drp.`, `drsce.`, `ssfn.arpce.cg` resolve to one host and serve **the same 4 325-byte Nuxt shell for every path** including `/api*` and `/sitemap.xml`, so the FY2024 acquisition's "untried subdomains" lead is closed; `www.assemblee-nationale.cg` still `Site en Maintenance`.
- **Searched, found nothing:** any `TOFE au 31.12.2025` (the series was backfilled 2015–2024 in one batch on 2026-04-08 and stops there); any *budget citoyen*, DPBEP or CBMT after the 2019 *cadre budgétaire à moyen terme 2020-2022*; any *annexe explicative des dispositions fiscales* or *rapport de la dépense fiscale* for 2025 (they exist for 2016, 2017, 2018, 2022 — both raised as acquisitions, since `Article troisième` says they exist); any procurement plan; any ARPCE, ADEN or FASUCE annual report or budget; any *décret portant ouverture de crédits d'avance* for exercice 2025; any budget line for the **Commission nationale de protection des données à caractère personnel** in the finance law, the rectificative or the execution report — provisionally an absence, but only provisionally, because a small line could sit inside a drifted stack.

### Republic of the Congo — three native years, no comparator column ever, and a device-identity register inside the budget law (sweep, 2026-08-03, FY2026)

- **Fiscal year:** calendar, confirmed a third time. `Loi n° 42-2025 du 31 décembre 2025 portant loi de finances pour l'année 2026`; `Article premier … au titre de l'année 2026`; `Décret n° 2026-179 … au titre de l'exercice 2026`.
- **THE FINDING THAT CHANGES HOW THE COUNTRY IS SWEPT: no Congolese finance instrument carries a prior-year comparator column, and this is now established over four instruments rather than guessed from one.** LF2026, PLF2026, LF2025 and PLF2025 all print `CODE | LIBELLE | PREVISIONS <year>` and nothing else — no `Collectif N-1` as in CAR, no `AE VOTE` as in Cameroon. **`COUNTRY-BUDGET-BATCH.md`'s reason for sweeping N+1 to close N's revised stage does not apply to Congo.** Close a Congolese year from its own rectificative and its own execution report, not from the next year's volume.
- **THE GAZETTE RULE EXTENDS: `sgg.cg` serves more than one rendering of the same issue, and the SMALLER file is the native one.** For *Journal officiel* n° 21-2026, which carries `Décret n° 2026-179`: `congo-jo-2026-21.pdf` is **2.7 MB with the per-ministry and per-programme tables as page images**; `congo-jo-2026-21-2.pdf` is **625 KB with the same tables as text**. The finance ministry's own extract (fid 10283, 2.4 MB, 6 237 chars over 11 pages) is the image version too. **The index at `/m-journal-officiel/le-journal-officiel.html` links the `-N` variant; follow the index link and never construct the bare `congo-jo-YYYY-NN.pdf` path.** Same for special editions — the LF2026 is `congo-jo-2026-3-3.pdf`, and `congo-jo-2026-3.pdf` is the weekly issue n° 3.
- **FY2026 is a three-stage year and all three instruments are native**: proposed (PLF 2026, 524 792 chars, 202pp), appropriated (`Loi n° 42-2025`, 615 522 chars, 114pp), revised-by-decree (`Décret n° 2026-179`, 224 644 chars). A fourth stage is enacted but not yet gazetted — the *loi de finances rectificative* 2026, adopted unanimously by both chambers on **23 July 2026**: recettes **2 778 016 000 000** against **2 550 540 000 000**, dépenses **2 561 069 000 000** against **2 320 167 000 000**.
- **The aggregates cross-foot, which is the cheap way to check a Congolese extraction.** `Article 38` budget général **2 139 267 000 000** + `Article 18` budgets annexes **9 247 000 000** + `Article 19` comptes spéciaux **171 653 000 000** = **2 320 167 000 000**, the *budget de l'État* figure the ministry quotes in prose. If a parse does not reproduce that identity, the parse is wrong.
- **A mid-year government reshuffle rewrites the ministry codes, and the decree is where you see it.** The presidential election of 12/15 March 2026 produced a new government on 24 April 2026; `Décret n° 2026-179` restates the budget against a structure carrying **codes 19, 20, 61, 70 and 91–99 that are not in `Loi n° 42-2025`**. A Congolese FY2026 record must name the instrument its ministry code came from, exactly as an FY2025 record must say `Loi n° 47-2024` or `Loi n° 41-2025`. **`Code 45` appears in neither the decree's cancellation nor its opening table**, so the digital vote was untouched by the réaménagement.
- **Drift is unchanged and is still the whole difficulty.** Codes, labels and amounts remain three independent vertical stacks. In the LF2026 `Article 34` table the `Code 45` row prints **20 272 823 267**, programme 117 prints **2 765 963 762** and programme 118 prints **31 205 538 063** — a ministry total smaller than one of its own programmes, which is proof of drift rather than a figure. **No Code 45 number may be recorded from any Congolese instrument before geometry binding.**
- **Block 6 — all three statutory keys moved in FY2026, and ANSSI and ACSI enter the finance law.** *Redevance Hub numérique*: `ETAT 20% | ADEN 10% | ARPCE 20% | ARTF 10% | ANSSI 10% | SFEC 30%`, against FY2025's `ETAT 20% | ADEN 15% | ARPCE 15% | ARTF 20% | SFEC 30%`. *Taxe sur les transferts de fonds*: `ETAT 45% | ARTF 30% | ACSI 5% | ANSSI 20%`, the ACSI share earmarked for "la finalisation des projets prévus par la loi n° 47-2024". The FY2019 *redevance de l'économie numérique (Timbre fiscal électronique)* is **abolished from 1 January 2026**. Named appropriations unchanged: FASUCE **1 000 000 000**, *urbanisation des systèmes d'information de gestion des finances publiques* **3 500 000 000**, among **12** comptes spéciaux against 18 in FY2025. **The regulator's, the agency's and now the security authority's money is legislated, not appropriated — read the articles, not the Code 45 vote.**
- **A national device-identity register is created by the budget law.** `PARAGRAPHE 7` institutes the **taxe sur les nouveaux terminaux numériques à carte SIM (RTN)** from 1 June 2026 and with it the **Registre Central d'Identité des Terminaux Numériques à Cartes SIM (RCIT)**: compulsory registration of every imported SIM-capable device, **operators legally required to interconnect their platforms with the RCIT** and transmit identification data "automatique, sécurisée, exhaustive, en temps réel", unregistered terminals disabled on GSM networks, tax 1 300 / 6 500 / 10 000 FCFA by generation, split **ETAT 60% | ADEN 40%**, with ADEN operating the assessment device. **The clearest case in this corpus that reading only the vote table misses the policy.**
- **`finances.gouv.cg/fr/articles/` is the richest single source in the Congolese corpus and it is not in the document library.** ~50 items over 4 pages of `?page=N`. The FY2026 run took 14. It carries the parliamentary presentations and adoptions of every finance bill, and a whole seam of named finance-ministry systems that appears nowhere else: **PDRCL** (dematerialisation of local-authority revenue, built by ACSI), **E-solde** (payroll), **SIGAS-TPV** (insurance data), the **Switch monétique national**, the **SIVL** forestry-revenue tax module, and the **COPIL de la Transformation numérique de la gestion des finances publiques**, first convened 15 July 2026 — the governance body over the 3 500 000 000 FCFA special account.
- **The SFEC/FOUTA/E-TAX programme is legislated and the instruments are all gazetted natively.** `Décret n° 2026-101 du 31 mars 2026` (JO 28-2026); `Arrêtés n° 1518, 1519, 1520, 1521 du 9 juillet 2026` (JO 29-2026) on homologation of terminals, versions and ERP systems, fiscal conformity, accompaniment measures and fees; `Arrêté n° 1009 du 22 mai 2026` making the **FOUTA** platform the sole channel for public-revenue payment (JO 24-2026). **Every one of these is a page-image scan on `finances.gouv.cg` and native on `sgg.cg`.** The décret's *visas* are a complete inventory of Congo's digital-law stack and name **four December 2025 decrees the wiki does not hold** — `2025-509` (organisations subject to mandatory security audit), `2025-512` (critical information infrastructure and operators of vital importance), `2025-514` (electronic-signature device), `2025-515` (audit scope and periodicity).
- **⚠ `acsi.cg` fails the system resolver and works over DoH.** "No such host is known" from `Invoke-WebRequest`; Cloudflare DoH returns **190.92.140.136**; `curl --resolve acsi.cg:443:190.92.140.136` returns **HTTP 200, 116 049 bytes**. The Agence congolaise des systèmes d'information is the state's in-house builder of SIFEC and the PDRCL, and it was one keystroke from being recorded as a dead host. Its own `actualités` are institutional colour; the substance is in the ministry's accounts of the same events.
- **Block 5 — Congo Telecom is recapitalised with state telecom assets.** Conseil des ministres of **6 May 2026**: the state transfers *Projet de couverture nationale* phase 1–3 infrastructure valued at **143 878 429 945 FCFA** to Congo Telecom (100% state-owned) against a capital increase taking its share capital to **157 297 453 418 FCFA**, absorbing accumulated losses of "un peu plus de 20 milliards" at 31 December 2024, and explicitly preparing a stock-market listing. Framed as making the operator "un des principaux piliers de notre souveraineté numérique". **This is the largest single Congolese digital-infrastructure figure in the corpus and it is not in any vote table.** The comptes rendus at `sgg.cg` remain cheap and productive: 10 mined for the window, 1 with real payload.
- **Block 4c — the data-protection authority has now been searched for and not found in three consecutive fiscal years.** No line for the *Commission nationale de protection des données à caractère personnel* in `Loi n° 42-2025` — not in the 139 programmes, not in the 22 dotations, not in the 12 comptes spéciaux. `Décret n° 2026-101` cites `loi n° 29-2019` in its visas and names no authority. Provisional pending geometry binding, but three years of the same result is a finding.
- **⚠ The ministry's scan of `Loi n° 42-2025` is 238 pages against the gazette's 114.** 35.5 MB, zero extractable characters. The FY2025 equivalent was 144 against 84. **The likeliest explanation is the *annexes budgétaires*, which is the line-grain unit this dataset most wants — but it is a guess until someone opens page 115.** Do that before commissioning any OCR.
- **Searched, found nothing:** any `TOFE au 31.12.2025` or `31.12.2026` (the series was backfilled 2015–2024 on 2026-04-08 and still stops there); any FY2026 execution report (the FY2025 edition appeared 2026-03-02, so expect March 2027); any gazetted FY2026 *loi de finances rectificative* (adopted 23 July 2026; special editions run only to n° 6 of 20 April 2026 and weeklies to n° 31 of 30 July 2026); any *budget citoyen*, DPBEP or CBMT — the `CBMT 2026-2028` is cited by the minister and is not published, raised as an acquisition; the *annexes budgétaires réaménagées* named in `Article 4` of `Décret n° 2026-179`, raised as an acquisition; any procurement plan; any ARPCE, ADEN or FASUCE annual report or budget; any French Treasury note on the FY2026 budget (the Congo budget series stops at 2025).

### Republic of the Congo — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-08-03)

**19 documents, 3 country-years, 11 records.** Every figure here was bound by **character geometry**, and where it disagrees with the three sweeps of the same night, the sweep was reading `pdftotext -layout` and was wrong. Archetype match: **Q, gazette variant** (added to the strategy library by this run); no new letter earned.

- **⚠ THE SWEEPS' TWO HEADLINE CODE-45 FIGURES WERE BOTH DRIFT ARTEFACTS, AND BOTH ARE RETRACTED.** (1) The FY2025 execution report does **not** show Code 45 executing 472 102 000 FCFA. It shows **3 630 627 582** — and 472 102 000 is programme **117**'s execution, one row down. The 15,1% rate quoted with it is right; the numerator is not, and 472 102 000 ÷ 24 078 665 787 = 2,0%, which should have been the tell. (2) The FY2026 law does **not** print Code 45 at 20 272 823 267; that is **Code 44 programme 061 *Transports terrestre et aérien***. Code 45 is **31 205 538 063**. No Congolese figure may be quoted from a `-layout` dump, in a run note or anywhere else.
- **⚠ A WORSE FAILURE MODE THAN DRIFT LIVES IN THESE FILES: `pdfplumber.extract_words()` DROPS GLYPHS.** On ANNEXE 4 of the FY2025 execution report it returns `Code4` for `Code 45` and **`2407866578` for `24 078 665 787`** — the last digit of every amount in the table. A tenth of the true figure, in plausible shape, with no error raised. `page.chars` bound by `top` returns both correctly. **Read Congolese tables at character level.** Full method in the strategy library.
- **FY2024 is a different budget from FY2025 and FY2026, and the difference is the grain.** `Article trente-huitième` of `Loi n° 39-2023` presents programme budgets *« à titre expérimental »* for **six pilot ministries** — budget, économie et finances, plan, santé, préscolaire/primaire, technique — and **Code 45 is not one of them**. FY2024 therefore publishes the digital vote only in `Article quarante et unième`'s institution × titre block, across **58 institution and ministry blocks**: **Titre 2 119 321 077 + Titre 3 602 840 066 + Titre 4 1 098 330 000 = sous-total 1 820 491 143, plus Titre 5 13 330 282 500 = 15 150 773 643**, both sums cross-footing to the printed totals. Recorded as `cog-2024-45` at `scope_confidence: partial` — a ministry envelope, on the DR Congo `cod-2024-52` precedent — and **not comparable with FY2025's programme 118**. From FY2025 the whole budget is by programme and the record moves to `cog-{fy}-45-118`.
- **The Code 45 series, geometry-bound, all three years** (`budget-archive/COG/code45-stage-series-2024-2026.csv`):

| FY | line | proposed | appropriated | revised | executed |
|---|---|---|---|---|---|
| 2024 | Code 45 (ministry) | — | **15 150 773 643** | — | — |
| 2025 | Code 45 (ministry) | 29 858 482 624 | 24 078 665 787 | 24 078 665 787 | 3 630 627 582 (15,1%) |
| 2025 | 117 Pilotage | 8 570 082 624 | 985 082 624 | 730 628 780 | 472 102 000 (64,6%) |
| 2025 | **118 Poste, télécom et économie numérique** | 21 288 400 000 | **23 093 583 163** | 23 348 037 007 | **3 158 525 582 (13,5%)** |
| 2026 | Code 45 (ministry) | 31 145 538 063 | 31 205 538 063 | untouched by the décret | — |
| 2026 | 117 Pilotage | 1 065 948 780 | 1 065 948 780 | — | — |
| 2026 | **118 Poste, télécom et économie numérique** | 30 079 589 283 | **30 139 589 283** | — | — |

- **Parliament reshapes this vote; it does not cut it.** The FY2025 bill asked 29,86 Mds and the law gave 24,08 — but the whole −5,78 Mds fell on the *pilotage* programme (−7,59 Mds) while the **operational digital programme gained 1,81 Mds**. The FY2026 passage added exactly **60 000 000 FCFA**, all of it to programme 118. A run that reads only the ministry total records a cut where the digital line rose.
- **⚠ THE EXECUTION RATE IS ON MIXED BASES AND IS A FLOOR.** ANNEXE 4 is headed *(Hors dépenses du personnel)* — but its `PREVISIONS REAJUSTEES 2025` column reproduces the rectificative **including Titre 2**, to the franc (23 348 037 007 for programme 118; 24 078 665 787 for Code 45). So the numerator excludes personnel and the denominator does not. Code 45's Titre 2 was 477 495 721, about 2% of the vote, so the distortion is small — but the FY2025 sweep's flat statement that *"every figure excludes Titre 2"* is too strong and is corrected here. **Carry the qualifier with the rate, always.**
- **The rectificative *replaces* the initial law.** `Article premier` of `Loi n° 41-2025`: *« la présente loi remplace la loi n° 47-2024 »*. So `supplementary_basis: restated-total`, never `increment`. It moved 254 453 844 FCFA from programme 117 to 118 and left the ministry total untouched at 24 078 665 787 — which is why the execution report's `PREVISIONS REAJUSTEES` for Code 45 equals the initial law's figure and looks like an unrevised year. It is not; the revision was internal to the vote.
- **Two digital comptes spéciaux du trésor in every year, and they are the money outside the vote.** Recorded at `scope_confidence: whole` under the single-mandate carve-out — each has one statutory object and no recoverable sub-line.

| Compte spécial du trésor | FY2024 | FY2025 | FY2026 |
|---|---|---|---|
| Fonds pour l'accès et le service universel des communications électroniques (FASUCE) | 1 000 000 000 | 1 000 000 000 | 1 000 000 000 |
| Fonds pour l'opérationnalisation de la fonction bancaire du Trésor public | 2 809 999 915 | 2 810 000 000 | **5 968 000 000** |
| Urbanisation des systèmes d'information de gestion des finances publiques | — (created 2025) | 3 500 000 000 | 3 500 000 000 |

- **The *urbanisation* account is the most valuable single article in the Congolese corpus.** `Article quinzième` of `Loi n° 47-2024` creates it *« pour financer les projets visant à moderniser, opérationnaliser et numériser les systèmes de gestion des régies financières »* and then **names thirteen systems**: SIGFIP, bancarisation du trésor / compte unique du trésor, **E-TAX** (Tome 1 and Tome 2 of the Code général des impôts), the natural-resource receivables payment system, **SICRAF**, **SIPAE**, **E-BOURSES**, **SYDONIA 4.4**, **SYGMAP**, gestion du portefeuille public, **SIDREP**, the state-receivables tracking modules and **SIDRCL**. It is fed by the *redevance informatique* instituted by paragraph B.4 of `Loi n° 10-2002` (LF 2003) and reset by paragraph 15 of `Loi n° 33-2003` — **a domestic IT levy running since 2003 that no Congolese source outside the finance law mentions.** `funding_source: own-source`.
- **The treasury account is a digital line hiding under a banking name.** `Fonds pour l'opérationnalisation de la fonction bancaire du Trésor public` reads as treasury reform; `Article 2` of its creating provision in `Loi n° 39-2023` says it funds *« le plan d'actions de mise en œuvre de la plateforme numérique du trésor public »*, and `Article 4` names **ACSI** as builder or delegated contracting authority. It **more than doubled** for FY2026 to 5 968 000 000, financed from *vente des cargaisons*. Neither sweep costed it.
- **Cross-foots that validate the whole extraction.** FY2026's twelve comptes spéciaux sum to **171 653 000 000** exactly, the figure `Article quarante-deuxième` states. FY2024's nineteen sum to 135 851 428 571 against a stated 135 851 000 000 — the article states its ceiling **in words, rounded to the million**, so the 428 571 residual is the wording and not a misread. Every Code 45 figure cross-foots twice, against the programme table and against the institution × titre table.

**§4a — the cross-vote scan, all three years, and what was looked for and not found.**

- **FY2025 (136 programmes + 21 dotations) and FY2026 (139 + 22) were walked line by line. There is no digital line outside the ICT vote.** Code 45 programme 118 is the whole of Congo's programmed digital spend. The near-misses, examined and **not** recorded: `109 Innovation technologique` (1 075 736 435 in FY2025 under Enseignement supérieur; 1 203 352 876 in FY2026 under the new Code 54 Recherche scientifique et innovation technologique) — the law states no purpose, and *technological innovation* in a research ministry is not established as digital; `137 / 047 Mobilisation des recettes` (23 279 421 239 → 28 213 505 123), the vote that in practice runs SFEC, E-TAX and FOUTA but is a revenue-administration programme, not a digital line; `005 Gestion des ressources humaines de l'Etat` (23 773 034 738 → 18 807 882 567), where E-solde sits, on the same reasoning.
- **FY2024 could not be scanned below ministry**, because the law publishes no programme for 52 of its 58 institution blocks. That is a stated limit of the year, not a null result: **Congo's FY2024 cross-vote digital spend outside Code 45 is not establishable from any published instrument.**
- **Identity and data exchange — hand-searched, absent.** No programme, dotation or compte spécial in any of the three years for a population register, *état civil* / CRVS, national identity card, biometric enrolment, passport system, interoperability layer, government service bus, single window or shared-services platform. Congo's *Intérieur* vote (Code 84 in FY2025, Code 23 in FY2026) runs six programmes — pilotage, administration du territoire, décentralisation, ordre public et sûreté nationale, risques et catastrophes, gendarmerie — and **none of them is civil registration**. The 2025 reporting of a *numérisation de l'état civil* and of Thales identity work has **no counterpart line at any grain the state publishes**.
- **Statistics — absent as a programme.** FY2025's Code 36 is *Plan, statistique et intégration régionale* and its three programmes are pilotage, planification et programmation, intégration régionale; there is no statistics programme. FY2026 renames the ministry (Code 88 *Economie, Plan et intégration régionale*, then Code 97 *Economie, plan, statistique et prospective* after the April 2026 reshuffle) and still prints none.
- **Governance structures — a third consecutive year of the same result, and it is now a finding rather than a provisional absence.** No line for the **Commission nationale de protection des données à caractère personnel** in FY2024, FY2025 or FY2026: not among the programmes, not among the dotations (901–922, which do fund the Cour des comptes, the CNDH, the Médiateur, the anti-corruption authority and eight consultative councils), not among the comptes spéciaux, not among the institution codes. **Congo enacted `loi n° 29-2019` on personal data protection and has appropriated nothing to the authority it creates, in every year the wiki holds.** Nor do **ARPCE**, **ADEN**, **ANSSI** or **ACSI** carry any appropriation: their money is legislated as revenue-share keys inside the finance law's fiscal articles — FY2026 *redevance Hub numérique* `ETAT 20 | ADEN 10 | ARPCE 20 | ARTF 10 | ANSSI 10 | SFEC 30`, *taxe sur les transferts de fonds* `ETAT 45 | ARTF 30 | ACSI 5 | ANSSI 20`. **Read the articles, not the vote table** — and record that the vote table is *empty* for every Congolese digital-governance body, which is the sharpest thing this country-year set produces.
- Also looked for and not found: any appropriation for the operator of FASUCE; any line for Congo Telecom (the 143 878 429 945 FCFA infrastructure transfer of 6 May 2026 is a capital operation outside the budget entirely); and any digital line inside the *Conseil supérieur de la liberté de communication*'s 1 017 100 000 dotation, which is broadcast-content regulation, not data governance.

**§5 — case 5: two candidates, no resets, one contradiction filed.**

`raw/` holds exactly two COG `finance_origin: domestic-state` records not built from a budget document — `cog-2025-anssi-operations` (US$1.3m to ANSSI operations, 2025) and `cog-2025-connectivity-sites-4g-upgrade` (US$3m, PATN 4G sites) — both `source_tier: reporting`, both `baseline_stage: unclear`, both with an entirely empty stage ladder. **Neither has a counterpart line at any grain the Congolese instruments publish**, so there is nothing for an appropriation to become master of and **no case-5 reset was applied**. The ANSSI case is filed as `reviews/contradictions/open/congo-anssi-2025-allocation-not-in-the-budget.md`, with the PATN one as its sibling: a reported state allocation that the whole native FY2025 chain does not contain is a disagreement worth settling, not a silence to absorb.

**Disposals and non-yields.**

- **`Journal Officiel Spécial n°3-2024` is not a finance law.** OCR of pp. 1–3 (`--lang fra`) returned the issue's own SOMMAIRE: `décrets n° 2024-90` to `2024-98 du 6 mars 2024` organising the ministry of the economy and finance and its directorates general, plus `décret n° 2022-1880`. `doc_type` corrected to `executive-instrument`, `fiscal_years_covered` emptied, companion rewritten, archived at `n/a`. The manifest row is kept as the permanent record of a document staged on a false pattern.
- **The ministry's 238-page `Loi n° 42-2025` is not the annexes budgétaires.** pp. 114–118 OCR'd: they are **Code général des impôts** text. The extra 124 pages over the gazette's 114 are the fiscal provisions at larger type, not programme detail. **No OCR job is justified for any Congolese finance law** — the gazette is native for every one of them, and this closes the FY2026 sweep's open question.
- **The FY2024 settlement law yields no digital record.** `Loi n° 40-2025` gazettes 8 pages: national recettes définitives 2 327 178 878 278 FCFA and a titre-level `Tableau d'ajustement des prévisions des dépenses`. Its per-titre and per-ministry execution is referred to annexed **tables F–K** and *annexe n° 6.1*, none of which is gazetted — raised as an acquisition. **FY2024 therefore has an appropriation and no outturn at any ministry grain**, the one Congolese year in the corpus that does.
- **The TOFE au 31.12.2024, the *Stratégie de gestion de la dette à moyen terme 2026-2028*, the budget speech of 30 October 2025 and the dissemination address of 2 June 2026 support no record** — aggregate, indicative or narrative. `Loi n° 1-2024` amends `Article 36` only, a treasury borrowing authorisation, and moves no ceiling; read natively from the gazette in 4 283 characters rather than OCR'd from a 5-character scan.
- **`Décret n° 2026-179` yields no revised stage for the digital vote.** Code 45 appears in neither its cancellation table (433 877 815 955 FCFA) nor its opening table (438 877 815 955), so the vote was untouched by the post-reshuffle réaménagement. `Article 4` refers the line detail to unpublished *annexes budgétaires réaménagées* (already an acquisition). The FY2026 rectificative adopted 23 July 2026 is not yet gazetted — a stated absence, not a gap to chase.
- **`amount_usd` left blank on all 11 records.** `lookups/fx-imf-annual.csv` carries XAF only as a ball-park euro-peg derivation, not a named fiscal-year average from IMF IFS or the BEAC, and the driver forbids spot-converting a fiscal-year figure.

### Comoros — the state does not publish its own finance law, the WTO does, and the rectificative is the Cameroonian ordonnance again (sweep, 2026-08-03, FY2024)

- **Fiscal year:** calendar, stated in terms. The *Budget Citoyen 2024*: the finance law covers *"une année fiscale (exercice budgétaire) qui court du 1er janvier au 31 décembre"*. Corroborated by the law's adoption on 27 November 2023 for the year beginning five weeks later, by the `TOFE 2024` running to `dec-24`, and by the `Compte administratif de l'année 2024`. Document label `2024`.
- **⚠ THE FINDING THAT ALMOST COST THE RUN, AND IT AMENDS THE STANDING DoH RULE: THE TWO PUBLIC RESOLVERS DISAGREE, AND CLOUDFLARE IS THE ONE THAT IS WRONG HERE.** `capture-rule.md` prescribes Cloudflare DoH. **Cloudflare returns `SERVFAIL` (status 2) for the entire `gouv.km` zone** — `gouv.km`, `finances.gouv.km`, `presidence.gouv.km`, `inseed.gouv.km`, `anrtic.gouv.km` — **and for `anaden.km` and `comorescables.km`. Google DoH (`dns.google/resolve`) returns A records for every one of them.** `finances.gouv.km` = 185.77.97.161 / 89.116.109.3, and pinned with `curl --resolve` it serves **HTTP 200, 259 411 bytes**. **The entire Comorian country-year came out of a host that a single-resolver check would have written off.** From now on: a SERVFAIL is checked against a second resolver before it is recorded as anything. NXDOMAIN on *both* resolvers is a real absence: `bcc.km`, `assemblee.km`, `armp.km`, `journal-officiel.km`, `coursdescomptes.km`, `finances.km`. (The central bank is at **`banque-comores.km`**, not `bcc.km`.)
- **⚠ THE APPROPRIATION IS NOT PUBLISHED BY THE COMORIAN STATE. IT IS PUBLISHED BY THE WTO.** `finances.gouv.km/lois-des-finances/` holds LF2019, LF2021, LF2022, the LFR2023 decree, the LFR2024, the LF2025 and LF2026 decrees and the *loi de règlement 2023* decree — **and no LF2024 in any form**. The law was found in the **WTO accession working party's legislative annexes**, `wto.org/english/thewto_e/acc_e/com_e/WT_ACC_COM_50_LEG1.pdf`, deposited during the accession completed at Abu Dhabi in February 2024: **13 pages, NATIVE, 29 000 chars**. The same directory holds `wtacccom12_leg_8.pdf` (the FY2016 law), so the deposit is a multi-year seam. **NEW GENERAL RULE: for a small state that has recently acceded to the WTO — or to any body that takes legislative deposits — check the accession annexes before concluding that a finance law is unpublished.** This is the second route-around-the-ministry found in the Francophone corpus, after Congo's `sgg.cg` gazette.
- **⚠ The WTO copy has a BLANK LAW NUMBER: `LOI N°23-______/AU`.** It is the text as adopted in plenary on **27 November 2023**, before the promulgation number was filled in, on Assembly letterhead and paginated *"Page N sur 13"*. The promulgating decree is not in the file and is not published. **The law's number and promulgation date are unestablished** — an acquisition, and a citation problem for every record built from it.
- **THE RECTIFICATIVE IS COMOROS' CAMEROONIAN ORDONNANCE, and it is the most useful structural property of the country.** `Loi n°24-013/AU du 27 août 2024` is a **page-image scan, 18pp, 0 extractable chars — but it OCRs cleanly with `tesseract --oem 1 -l fra`**, and **every table prints `LFA 2024` and `LFR 2024` side by side**. So one document carries the **appropriated and the revised stage together** and independently corroborates the WTO copy of the law to the franc. Same shape as Cameroon's mid-year ordonnance restating `ARTICLE QUATRE-VINGT-UNIÈME`. **The `LFA` column is the enacted appropriation; do not read it as a bill.**
- **⚠ CORRECTION TO A STANDING FINDING: THIS MACHINE CAN RASTERISE PDFs.** The COG FY2024 run recorded *"no PDF rasteriser (`pdftoppm`, PyMuPDF both absent)"* and treated OCR as blocked on tooling. **`pdfplumber`'s `page.to_image(resolution=N).save('x.png')` works and is installed**; every OCR result in this run came through it, at 180–300 dpi, into `tesseract --oem 1 -l fra`. `pdftotext`, `pdfinfo`, `pdftoppm` and `qpdf` are all absent; `pdfplumber`, `pypdf`, `openpyxl` and `pandas` are present. **No Congolese or Cameroonian OCR job is blocked on tooling.**
- **THE VOTE UNIT IS THE MINISTRY, AND THERE IS NOTHING BELOW IT — this is a property of the budget system, not a gap in the sweep.** Comoros runs a *budget de moyens*. The FY2024 execution report says on page 4 that the move to a *budget programme* has slipped to **2027** against the 2022 set by the 2022 LOFE, and that the DGB's own reorganisation decree **is still unsigned**. **Every Comorian record will be a ministry envelope at `scope_confidence: partial`** until that transition happens. No OCR job and no acquisition changes this; only the `Article 19` annexes (*tableaux des emplois*, detailed *tableau des recettes*) would, and they are published nowhere.
- **The digital vote, FY2024, full KMF, cross-footed three ways.** `Ministère des Postes, des Télécommunications et de l'Économie Numérique`: **LFR2023 337 232 800 → LFA2024 194 457 800 (−42,34%) → LFR2024 682 681 240 (+488 223 440, +251,07%)**. Both moves cross-foot exactly. **The August rectificative multiplied the digital ministry by 3,5 in the same instrument that cut the ministry block as a whole by 6,94%** (55 896 496 779 → 51 955 770 077). Appropriated corroborated by three independent instruments: the law's `Article 11`, the LFR's `LFA` column, and the Budget Citoyen's `194`.
- **⚠ SCALE TRAP, LIVE, INSIDE ONE COUNTRY-YEAR.** The law and the rectificative print the ministry table in **FULL FRANCS COMORIENS**, space-separated thousands, no `en milliers` header. **The Budget Citoyen prints the same table in `Millions KMF`.** The *dépenses fiscales* report uses **COMMA** thousands separators where everything else uses spaces. The `TOFE` is **full KMF units — NOT `en milliards`, unlike the Congolese TOFE**. Read the header and the separator on every artefact, and do not carry a regional assumption across.
- **`Article 7` gives capital by ministry with an `ETAT | BAILLEURS | TOTAL` split — the origin gate handed over ready-made**, and it is the best-shaped capital table in the Francophone corpus. **`Ministère des Postes, Télécommunications, de l'économie numérique` prints a literal `0`** — no state capital, no donor capital — and is **absent entirely** from the LFR's revised capital table. **The whole +488 223 440 is current spending.** Whatever digital investment happened in Comoros in 2024 happened outside the budget.
- **THE OUTTURN EXISTS, AT MINISTRY GRAIN, THREE MONTHS AFTER YEAR-END — better than Congo and better than Cameroon.** `Rapport d'exécution de l'exercice budgétaire 2024`, dated on its face **`Moroni, le 14/03/2025`** (the 2025-06-11 library upload is **not** the publication date). 21pp scan, OCRs cleanly. **⚠ STRUCTURE TRAP: execution is presented by economic nature first, then a SEPARATE per-ministry table under EACH nature.** There is no consolidated per-ministry outturn column; a ministry total must be summed across them. The `TRANSFERT` table (p.19) gives `MINISTERE DES POSTES, TELECOMMUNICATION` prévision 613 000 000 / exécution 140 000 000 / paiement 138 642 840 — **one nature only, and its prévision matches neither the LFA nor the LFR ministry total. Do not compute an execution rate from it.**
- **⚠ THE STATE'S TWO OUTTURN DOCUMENTS DISAGREE WITH EACH OTHER.** Non-fiscal revenue is **10 646 228 629** in the execution report and **10 069 456 148** in the TOFE; the deficit is **-19 071 207 296** and **-19 133 844 400**. Same year, same ministry, both published. Not reconciled.
- **The `TOFE 2024` is an XLSX and is the only natively structured budget artefact in the corpus** — sheet `TOFE`, A1:IK98, period columns `2024-03-01 / 2024-06-01 / 2024-09-01 / dec-24`, **cumulative from January so the quarters are not additive**. **Aggregate only: economic nature, no ministry grain anywhere, so it supports no digital record.** ⚠ It is published with **live `#N/A` and `#REF!` errors** (rows 14–15, 80–84) and empty island-transfer and CUT blocks (85–91). Served three times on the site under two names.
- **The Budget Citoyen is a genuine budget document here, not colour — and its filename hides it.** `Direction-generale-du-Budjet-2024.pdf` (with the typo) is 38pp **NATIVE**, 41 935 chars, and pp.30–33 are the `Répartition administrative des crédits budgétaires 2024` with a *Missions* narrative and SDG indicators per ministry. **⚠ Filenames on `finances.gouv.km` lie systematically**: the arrêté compilation is `Arrete-2024-PDF-270225-1.32.26.pdf`, the IMF ECF review is `1COMFA2025001-1.pdf`. **Enumerate and open; never search this library by title.**
- **TRACK B IS SOLVED: `finances.gouv.km` is WordPress 6.9.5 with an open REST API.** `/wp-json/wp/v2/media?per_page=100&media_type=application` returns `x-wp-total: 114` over two pages — no auth, no bot guard, default UA accepted. **Two fetches replaced the entire Track-B enumeration.** The Cameroon lesson (`minfi.gov.cm` 489 items, `rfp.cm` 288) transfers intact and is now three countries deep: **where a Francophone finance ministry runs WordPress, hit the REST media API.** `justice.gouv.km` runs WordPress too but its REST API returns **401** — its files are still directly fetchable under `/wp-content/uploads/`, and it is where the sector statutes live.
- **Block 6 — ANRTIC's money is legislated and never appropriated, for the third country running.** `Décret n°24-003/PR du 2 février 2024` promulgating `Loi n°23-024/AU` (adopted 26 December 2023), on `justice.gouv.km`, native 65pp / 147 615 chars. `Article 8`: **taxe de régulation at 2% (licence) / 1% (autorisation) / 0,5% (déclaration)** of prior-year ex-tax turnover, plus **10% of licence fees**, spectrum and numbering management and control charges, type-approval fees, property income, borrowings, **state subventions**, **40% of pecuniary sanctions**, gifts and legacies. **Identical in shape to Cameroon's ANTIC/ART ceilings and Congo's *redevance Hub numérique* keys. Read the sector statute, not the vote table.** `Article 8.IV` requires an annual public activity report; **none exists on `anrtic.km`** (acquisition). ⚠ `anrtic.km` returns **403 to a default UA and 200 to a browser UA**.
- **THE LARGEST STATE FISCAL COMMITMENT TO THE DIGITAL SECTOR IS A TAX EXPENDITURE, AND IT IS FIVE TIMES THE VOTE.** `Rapport d'évaluation des dépenses fiscales de fiscalité indirecte — Exercice 2024`, the new Unité de Politique Fiscale's first output, native 24pp. `Tableau 6`: **Télécommunication 985 845 035 KMF = 26,21%** of domestic consumption-tax expenditure (total 3 761 476 877 = 6,66% of tax revenue, 0,58% of GDP); *Transfert d'argent* a further 6 162 160. **986 million forgone against a 194 million appropriation.** It is a tax expenditure and must never be recorded as an appropriation — **but a Comoros digital-spend figure that omits it describes a fifth of what the state did.** New pattern worth watching in every country: *the tax-expenditure report is where the state's real transfer to the sector is quantified.*
- **Block 4c — the authority does not exist and is donor-funded to be created.** No data-protection, cybersecurity or regulator line anywhere in the FY2024 budget, hand-checked across `Article 11` (22 institutions and ministries), `Article 7`, and the *dépenses communes*. Comoros' data-protection provisions came via the **2023 revision of the 2014 electronic-communications law**, not a standalone statute, and no supervisory authority is publicly identified. The **IsDB/AfDB e-government project via ANADEN** lists under `Composante C` capacity-building for *"l'Autorité nationale de protection des données personnelles"* and an *"Observatoire national du numérique"* — **the authority is to be created with external money.** Against that, `Rapport du FMI n° 2025/154` scores **`Cybermenaces` at Élevée likelihood / Élevée impact**. A stated *"révolution numérique"* with a named e-gov portal — **« munganyo »** — funded by 194 million KMF and zero capital.
- **Block 4b — the cross-vote scan, all 22 rows, and it is nearly empty.** Only two digital items outside the sector ministry: **Gouvernorats *"matériels informatiques"* 4 000 000 KMF** (the only line in the whole budget naming IT equipment) and **Ministère des Finances *"financement de la banque postale et de la poste"* 1 798 980 000 KMF**, which the Budget Citoyen states is **financed by French budget aid** — a state capital participation on external grant money, and exactly what the origin gate exists to catch. The corporate event behind it (the **SNPSF split into Banque Postale des Comores and Poste Comores**) is inside the *recueil des arrêtés 2024*.
- **Identity, data exchange and statistics — hand-searched, wholly absent.** No line at any grain for a population register, *état civil* / CRVS, national ID, biometric enrolment, passport system, voter register, social registry, interoperability layer, service bus, single window or shared services. The Ministère de l'Intérieur's only named FY2024 line is *"Achat d'imprimerie d'alwatwan"*, 30 000 000 KMF. **Comoros' civil-registry digitisation and its EU/Expertise France e-administration work have no counterpart appropriation.** Same result as Congo, and the two together now make it a regional pattern rather than a national quirk.
- **The `released` stage has an identified instrument and unknown contents.** The Budget Citoyen states execution runs on **quarterly credit-opening arrêtés of the finance minister**, and LF2024 `Article 17` allocates credits to secondary ordonnateurs by ***arrêté de répartition***. The **`recueil des arrêtés 2024`** (127pp scan, OCRs with `-l fra`, **some pages bilingual French/Arabic needing `-l fra+ara`**) is the only candidate. **Whether the quarterly arrêtés are in it is not established — a full OCR pass is the highest-value open question for this country.**
- **The audit chain exists and runs about four years behind.** Comoros **does** enact settlement laws — `Loi n°24-017/AU` promulgated by `Décret n°24-187/PR du 19 décembre 2024` settles exercice 2023 — so **the FY2024 settlement law is overdue, not absent** (due ~Dec 2025 on that cadence). Separately the Cour Suprême's **Section des comptes** posted a native `ROD execution budget 2022` on 2026-03-03, and the Budget Citoyen confirms its controls covered the 2022 report. **Expect a COM FY2024 audit opinion around 2028.** Contrast Congo, where the court has no reachable domain at all.
- **`imf.org` was not needed: the ministry mirrors the Fund's reports.** `Rapport du FMI n° 2025/154` (4th ECF review, June 2025, French, native 98pp / 258 725 chars) is on `finances.gouv.km`. Given imf.org's HTTP 403 to this network on the same night's COG runs, **check the state's own library for IMF documents first.** Its Block 6 payload: the **IGF audited Comores Telecom, ONICOR and OCOPHARMA and planned SONEDE, ANRTIC and Comores Câbles for 2025** — stated twice, in the staff report and the authorities' memorandum.
- **Mirrors worth knowing:** **`cabri-sbo.org/uploads/bia/Comoros_2024_*`** republishes both the FY2024 execution report and the Budget Citoyen byte-for-byte (same pattern as its Cameroon holdings); `justice.gouv.km` for sector statutes and the customs code; `anaden.org` for the *Stratégie Comores Numérique 2028* (already held).
- **Searched, found nothing:** any *projet de loi de finances* for any year (Comoros publishes no PLF series, so the CAR/Cameroon/Congo "the bill is native where the law is a scan" rule has nothing to work with); any *loi de règlement* for 2024; any FY2024 quarterly execution report; any procurement plan (`/marches-publics-2/` holds signed contracts, not plans, and its coverage starts July 2025 — nil for FY2024); any CBMT or DPBEP; any ANRTIC, ANADEN, Comores Câbles or Comores Télécom budget or annual report; any universal-service fund; any *arrêté de répartition* identified as such; any *budget citoyen* before 2023.

### Comoros FY2025 — the annexed volume exists after all, the PLF exists after all, and both FY2024 findings are now year-specific (sweep, 2026-08-03, FY2025)

- **⚠ CORRECTION TO THE FY2024 ENTRY, AND IT IS THE MOST IMPORTANT LINE IN THIS SECTION. "THE VOTE UNIT IS THE MINISTRY AND THERE IS NOTHING BELOW IT" IS TRUE OF FY2024 AND FALSE OF FY2025.** `Décret N°24-186/PR du 19 décembre 2024`, promulgating `Loi N°24-016/AU du 02 décembre 2024`, is **146 pages** and carries **`ANNEXE VI — CLASSIFICATION PAR MINISTÈRE ET ÉCONOMIQUE` at SERVICE level with COFOG codes**, pp.18–145. Columns `CODE | Service | COFOG | Désignation | LFR 2024 | LFA 2025`; four economic natures per service (`Salaire`, `Biens et service`, `Transfert`, `Investissement`), a `Total service` line each, a `TOTAL MINISTERE` per ministry. **Scan, 0 extractable chars, OCRs cleanly with `tesseract --oem 1 -l fra` — 213 411 chars over all 146 pages.** Comoros still has no *programme* budget (transition still slated for 2027), but it does publish an administrative-and-economic classification below the ministry. **Read the FY2024 envelope finding as FY2024-specific; do not apply it to FY2025 records.**
- **⚠ CORRECTION 2: "COMOROS PUBLISHES NO PLF SERIES AT ALL" IS ALSO FALSE FOR FY2025.** `finances.gouv.km/wp-content/uploads/2024/12/PLFA-2025-1-2-.docx` is the **`PROJET DE LOI DE FINANCES DE L'ANNEE 2025`**, **NATIVE .docx, 17 802 chars**, on bilingual Arabic/French ministry letterhead, linked from no section page and findable only through the media API. **So the CAR/Cameroon/Congo rule — the bill is native where the law is a scan — applies to Comoros after all, and it is the single most useful artefact of the country-year**: its `Articles 1–23`, aggregate tables, `Article 7` capital table and `Article 11` *répartition administrative* are **identical to the enacted law to the franc**, so the whole first part of the law can be extracted natively and the OCR used only as a check. Already caught one OCR error: `Impôts sur le Revenu` LFR2024 reads `5 539 074 989` in OCR, `9 539 074 989` in the docx, and only the latter cross-foots to `Total Recettes fiscales 56 816 000 001`. **Where they disagree, the docx wins.**
- **⚠ THREE STRUCTURE TRAPS IN THE 146-PAGE VOLUME, ALL OF WHICH WILL CORRUPT AN EXTRACTION SILENTLY.** (i) **`ANNEXE VI` IS PRINTED TWICE** — PDF pp.18–76 and again pp.77–145, byte-identical, both carrying the same internal footer (`Page 35 / prevision des depenses 2025 VFinal`). **Deduplicate on the internal page number, not the PDF page number, or every figure doubles.** (ii) **PDF pp.12–17 are ROTATED 90°** (the detailed revenue annexe) — unrotated, OCR returns reversed gibberish; rotate before OCR. (iii) **The `09 0904` FY2025 cells are illegible on both print runs** (stamp or fold over the digits) — derive **56 016 514** by subtraction from the ministry total and **bind by geometry against the page image before recording it.**
- **The digital vote, FY2025, cross-footed three ways and now resolvable into five services.** `Ministère des Postes et des Télécommunications` (code `09`): **LFR2024 682 681 240 → LFA2025 235 315 816, écart −447 365 424, TV −65,53%** — the sharpest proportional cut in the whole FY2025 budget, against a ministry block growing 8,35%. Corroborated by the enacted law's `Article 11`, the native PLF's `Article 11`, and the *Budget Citoyen 2025* p.30 (`235`, ⚠ **millions KMF**). Services: `0901 Cabinet 44 585 900 → 40 107 058`; `0902 Secrétariat Général 16 959 335 → 16 192 244`; **`0903 ACRP 50 000 000 → 50 000 000`, transfert only**; `0904 Direction Générale des Postes et Télécommunications 498 136 005 → ~56 016 514`; **`0905 chambre du Numérique 73 000 000 → 73 000 000`, transfert only**. **The whole cut falls on `0904`; the two transfer-funded bodies were held flat while the operating directorate was gutted.** Against the LFA2024 base of 194 457 800 the durable movement is **+21,0%** — the FY2024 rectificative's ×3,5 spike did not carry forward.
- **⚠ THE BILL AND THE LAW ARE IDENTICAL ON THE MINISTRY TABLE.** The Assembly amended nothing between 19 November and 2 December 2024. **Do not build separate `proposed` and `appropriated` records off the same numbers without stating that they are the same numbers.** This is the first Francophone country-year in the corpus where that is demonstrable, because both instruments are held.
- **`chambre du Numérique` is a body created in FY2025 and funded entirely by transfer.** *Budget Citoyen 2025* p.42 lists it under new spending: *"Création de la Chambre Numérique (Subvention de 73 000 000 KMF)"* — **31% of the entire digital ministry's appropriation, with no salary, goods-and-services or capital line of its own.** The single-mandate carve-out has real work to do here, and so does `ACRP`, whose acronym the volume never expands.
- **CAPITAL: THE DIGITAL MINISTRY IS ABSENT FROM THE `Article 7` TABLE FOR A THIRD CONSECUTIVE INSTRUMENT.** Printed `0` in LF2024, absent from the LFR2024 revised table, absent from LF2025. **The whole 235 315 816 is current spending.** Meanwhile `Transports Maritimes et Aériens` takes `350 000 000 (État) + 51 440 527 606 (bailleurs)` — **77,7% of the entire capital budget in one ministry, on donor money**. And the FY2024 `Prise de participation aux Institutions Financières` (1 798 980 000, French budget aid, Banque Postale) is **−100,00% in FY2025**: it disappears from `Article 7` and reappears below the line in `Article 9` as `RECAPITALISATION BPC 898 490 439` and `RECAPITALISATION BDC, BFC 1 400 000 000`. **The origin gate needs both years to get that right.**
- **⚠ THE SCALE TRAP REPEATS EXACTLY.** Law and PLF in **full francs comoriens**, space-separated thousands, no header; **Budget Citoyen in `millions KMF`**. PIB reference `693 301 636 500`. Same country, same year, two scales — as in FY2024.
- **THE STATE'S FINANCIAL IT SYSTEMS ARE NAMED IN EXACTLY ONE PLACE, AND IT IS AN IMF ACRONYM TABLE.** `Union des Comores — Renforcer la transparence des finances publiques` (FAD, mission 29 janvier – 12 février 2025, `POUR USAGE OFFICIEL`, 45pp native, published by the ministry itself) lists **`SIGIT` — Système Intégré de Gestion des Impôts et Taxes** and **`SIM_ba` — Système d'Information de Modernisation des Budgets**. **Neither appears anywhere in the FY2025 law, its `ANNEXE VI`, the Budget Citoyen or any FY2024 document.** They are paid for inside unnamed `Biens et service` lines. **New general move: when a Francophone budget names no system, read the IMF TA report's abbreviation table — it is where the state names them.**
- **BLOCK 4b IS NOW STRUCTURALLY UNFINDABLE IN THE VOTE AND FINDABLE EVERYWHERE ELSE.** `ANNEXE VI` classifies by economic nature, so IT purchases sit inside `Biens et service` and no keyword reaches them. The FY2025 cross-vote digital spend was found in four non-vote places, all state activity: **customs** (IMF FAD Sept 2025 — SYDONIA in production but no electronic manifest and no advance lodgement; an in-house IT asset-management application **built and never put into production**; partner-funded **single-window interconnection**); **tax** (PAGF-SI AMI, Oct 2025 — study to interface **SIGIT with bank and mobile-operator mobile-banking platforms**, under the DGI and the Centre Informatique); **the finance ministry itself** (PAGF-SI tender, 22-12-2025 — **two datacentres, primary and backup**, LAN/WLAN, firewalls, IPS, SIEM, two NOCs; bid guarantee `5 686 274 KMF`, tender doc `100 000 KMF` = €204, an implied 490,2 KMF/€); and **education, agriculture and identity** (ANADEN — national **Data Center inaugurated 19 May 2025** with Comores Câbles, stated to support *"le DNS national, l'identité numérique et les portails e-services"*; **e-Msomo** and **e-Shiyo** with the education ministry and UNICEF, 5 June 2025; an **ANADEN–UCAEP national digital agricultural registry**; **PADEC** launched 27–28 March 2025 with the AfDB). **None of it is appropriated.**
- **⚠ PAGF-SI IS THE ORIGIN GATE'S HARDEST CASE IN THIS CORPUS AND IT MUST BE DECIDED EXPLICITLY.** The AFD project manual (`CKM1154-Manuel-des-procedures-V0.pdf`, 76pp native) gives the €10m component plan (C1 infrastructures SI GFP 3,70; C2 matériel utilisateurs 0,35; **C3 services numériques et interfaçages 1,70**; C4 outils métiers GFP 0,00; C5 formation 0,35; C6 pérennisation 0,15; C7 gestion de projet/AMOA 2,75; divers 1,00) **and states that "une partie de ce financement, estimée à 20% de l'enveloppe totale, sera destinée au REFINANCEMENT DE DÉPENSES PAYÉES SUR LE BUDGET NATIONAL" — €2m refinancing state spending on new staff, internet connections and application maintenance/publisher contracts.** Donor money, fisc expenditure, retroactive. **A Comoros digital-spend figure that treats it as wholly external is wrong, and one that treats it as wholly domestic is wrong too.** It also reveals that the Comorian budget *is* paying for connectivity and application maintenance somewhere inside ministry `Biens et service` lines, at a scale AFD thought worth €2m. The manual creates a **`PTAB` (plan de travail annuel budgétisé)** — the annual budgeted work plan for state financial-IT spending, and exactly the acquirable annual instrument this dataset wants. Not published.
- **IDENTITY: THE FIRST NAMED PROGRAMMES IN THE COMORIAN CORPUS, AND STILL NO LINE.** The **`Lettre de cadrage budgétaire 2025`** (`N°24-0_3/MFBSB/CAB`, Moroni 04-09-2024, 7pp scan, OCRs) names *"le démarrage du **Programme National Comorien d'intégration des permis de conduire biométrique**"* and *"la mise en œuvre du **code des mouvements migratoires**"*; the ministry's own *exposé des motifs* post repeats the biometric licence. **Neither has any line in `ANNEXE VI` at service grain.** Same result as FY2024 for population register, CRVS, national ID, biometric enrolment, passport, voter register, social registry, interoperability layer, service bus and single window: **absent at every grain.**
- **THE FRAMING LETTER IS COMOROS' WHOLE MEDIUM-TERM FISCAL-STRATEGY LAYER — there is no CBMT and no DPBEP, searched again and confirmed.** Type it `mtef`. Its Block 4c payload is a **cross-government instruction**: *"La digitalisation de la gestion budgétaire… en utilisant des logiciels de collecte, des traitement et d'analyse des données en renforçant la dématérialisation"* and *"la consolidation des Systèmes d'Information SI exploités, dans la Gestion Publique de l'Etat"*. **Digital-governance spend addressed to every ministry, invisible to any keyword search of a vote table. Read the framing letter, not the vote, for this block.**
- **BLOCK 6 — one FY2024 acquisition closes as a stated absence, on the regulator's own authority.** `anrtic.km/actualites/rapports` returns verbatim **"Aucun rapport trouvé — Aucun rapport n'a encore été publié. Revenez bientôt !"**, and `/actualites/etudes-enquetes` the same, against `Article 8.IV` of `Loi n°23-024/AU` which requires an annual public activity report. **ANRTIC now says on its own site that it has never published one — that is a dated finding for the place hub, not a standing chore.** ANRTIC remains absent from `ANNEXE VI` entirely: **legislated funding, never appropriated, for the second consecutive Comorian country-year.** The one FY2025 instrument located is `Décision N°25/001/ANRTIC/DG du 17 juillet 2025` approving the **catalogue d'accès de Comores Câbles SA 2025-2026** (2pp scan; the catalogue itself is a separate, unlocated document).
- **⚠ THE FY2025 REVISED STAGE EXISTS, WAS ADOPTED, AND IS PUBLISHED NOWHERE.** *Al-watwan*, 29-12-2025: the Assembly's last plenary of the year, Friday 26 December 2025, adopted five bills including **"le projet de loi de Finances rectificatives de l'année 2025"**. Corroborated by the IMF's fifth ECF review (`1COMFA2026001`): the LFR25 regularises extrabudgetary spending — airport social transfers (0,6 pt of GDP) and domestically financed generator-set investment (0,4 pt) — offset by cuts (0,4 pt each) and a wage-bill saving from suspended indexation, a recruitment freeze and ghost-worker removal (0,5 pt), for a revised internal primary deficit of **1,3% of GDP**. **Not in the media library's 114 items, not on `/lois-des-finances/`, no promulgating decree.** Acquisition, and the primary re-run trigger. **If it never surfaces, the `LFA 2025` comparator column of the FY2026 volume is the fallback.**
- **`imf.org` RETURNS HTTP 403 TO THIS NETWORK — re-confirmed twice** (`Invoke-WebRequest` and `curl` with full browser headers, Referer, Sec-Fetch-*) on `1COMFA2026001-source-pdf`. **The FY2024 route stands: the ministry mirrors the Fund's reports with a lag** — the fourth review appeared on `finances.gouv.km` in September 2025, the FAD customs report in October 2025, the fiscal-transparency report in May 2025. **Check the state's library first and wait, rather than fighting Akamai.**
- **⚠ THE DoH RULE NEEDS STRENGTHENING AGAIN, IN THE OPPOSITE DIRECTION TO THE FY2024 AMENDMENT.** The FY2024 run recorded that Cloudflare SERVFAILs on the `gouv.km` zone and **Google DoH resolves it**. **Tonight both SERVFAIL, and Quad9 errors — and `finances.gouv.km` still serves HTTP 200, 259 539 bytes, on a plain fetch.** The `.km` authoritative servers are flaky enough that every public DoH resolver can fail at once while the host is perfectly healthy. **The rule that survives: a DNS failure of any kind is never sufficient to write a host off. Attempt the fetch anyway; if that also fails, pin with `curl --resolve` against a previously recorded A record** (185.77.97.161 / 89.116.109.3 both served 200 when pinned). **The whole FY2025 country-year came out of a host that every available resolver declared unresolvable.**
- **TRACK B STILL SOLVED, AND THE SECTION PAGES ARE NOW DEMONSTRABLY INCOMPLETE.** `/wp-json/wp/v2/media?per_page=100&media_type=application` → `x-wp-total: 114`, two pages, no auth, no bot guard, default UA accepted. **The `Budget Citoyen 2025` is NOT linked from `/budget-citoyen/`**, which still shows only the 2024 edition, and the **PLF docx is linked from nowhere at all**. `/lois-des-finances/` (10 links) and `/rapports/` (12 links) were both scraped and both are subsets of the media API. **Enumerate the API; never trust a section page for completeness.** Filenames still lie: `PLFA-2025-1-2-.docx`, `comoros_cfr_2025_1.pdf` (an **AfDB** country report, not IMF), `Decret-N°24-186PR-du-19-decembre-2024-…`.
- **Searched, found nothing (FY2025):** any **LFR2025 text or decree**; any **FY2025 execution report** (`/rapports/` holds FY2020, FY2023, FY2024 — FY2024's dated 14-03-2025, uploaded 11-06-2025, so FY2025's is **overdue**); any **TOFE 2025**; any **`recueil des arrêtés 2025`** (2023 and 2024 compilations exist); any **`loi de règlement` for 2024 or 2025** (the FY2024 one is now over seven months overdue on the FY2023 cadence); any **CBMT or DPBEP**; any **procurement plan** (`/marches-publics-2/` holds individual signed contracts); any **universal-service fund**; any **ANADEN, Comores Câbles or Comores Télécom budget or annual report**; the **`Article 23` tableaux des emplois**; the **PAGF-SI `PTAB`/`PPA`**; the **Comores Câbles access catalogue** itself.
- **Seen and deliberately not staged, so it is not rediscovered:** `comoros_cfr_2025_1.pdf` (AfDB *Rapport-pays 2025*, 37pp native — third-party macro analysis, thin digital content, no state tables reproduced); `Bilan-synthese-Min-Finances.pdf` (**42 MB**, 24pp ministerial brochure — checked: **0** mentions of *numérique*, 1 of SYDONIA); `Bulletin Statistique de la dette Fin Décembre 2025` (pure debt stock; the AVD carries what is needed); `Décret N°25-002/PR du 22-01-2025` on public procurement (21pp scan, no money, no digital); `RAPPORT-DEXECUTION-BUDGETAIRE-2023.pdf` (FY2023, out of scope); the FY2026 framing letter and both FY2026 promulgation decrees (**⚠ there are TWO decrees for LF2026 — `2026/01/Decret-N°26-003PR…` and `2026/02/Decret-portant-promulgation-du-loi-des-finances-2026.pdf`; establish which is operative before building FY2026 records**); ANRTIC's 5G frequency attributions to Yas Comores and Comores Télécom (undated pages, no fee stated).

### Comoros FY2026 — the volume that closes the previous year's missing stage, and an IT nomenclature nobody had seen (sweep, 2026-08-03, FY2026)

- **⚠ THE FY2026 VOLUME'S COMPARATOR COLUMN IS `LFR 2025`, SO IT CARRIES THE FY2025 REVISED STAGE THAT IS PUBLISHED NOWHERE ELSE — THIS IS THE FINDING OF THE RUN.** The FY2025 run recorded its biggest gap as an LFR2025 adopted 26 December 2025 whose text never appeared, and named the FY2026 volume's comparator as the fallback. **The fallback works, and it is better than expected: the column is the *revised* FY2025, not the original.** Determinable, not assumed — the digital ministry's comparator reads `223 337 645` against a known `LFA 2025` of `235 315 816`, so the column cannot be the appropriation; the printed écart and TV cross-foot against the comparator as printed; and the nine service lines sum exactly to `223 337 645`. **⚠ One `Article 11` caption reads `Ecart ( LFA2026-LFA2025)` above a table headed `LFR 2025 | LFA 2026` — the header is right and the caption is wrong.** **The FY2025 rectificative cut the digital vote 235 315 816 → 223 337 645, −11 978 171 KMF, −5,09%**, establishable from no other document in three Comorian runs. **General move: when a Francophone rectificative is adopted but never published, take the NEXT year's law and read its comparator column — and check which stage that column actually is rather than trusting its caption.**
- **⚠ THE TWO LF2026 "DECREES" ARE ONE FILE. The FY2025 run's flagged question is closed.** Both `2026/01/Decret-N°26-003PR-du-16-jan-2026-…pdf` and `2026/02/Decret-portant-promulgation-du-loi-des-finances-2026.pdf` return **38 416 536 bytes, SHA256 `376CAB19EC145F6F8509E96FC8F3877C33913B40C9561A1E2371AEA37B2DB2DB`**. One instrument, uploaded twice under different names. **Hash before theorising about duplicate promulgations on a WordPress media library — the library re-uploads.**
- **⚠ THE VOLUME IS A SCAN WITH A PRE-BAKED OCR TEXT LAYER, AND THIS IS A NEW TRAP FOR THE CORPUS.** `pdfplumber` returns **192 077 characters** over 153 pages with no OCR step, so every "is it native?" test says yes. **It is not.** Each page is one full-page image with a `Times New Roman` character layer over it, and the layer is bad: `SECITON 3`, `L0I DE FINANCE`, `PREVIsloN`, `Ministère de l'Emergie, del'EagetdesHydrocarbures`, and **corrupted digits** — `Total Recettes fiscales` LFR 2025 prints `62 791 " Oao` for `62 791 000 000`. **Test for images as well as characters: `len(page.images)==1` with a full-page bbox plus a generic font is a scanned page, whatever `extract_text()` returns.** Re-OCR with `tesseract --oem 1 -l fra` via `pdfplumber` `page.to_image(resolution=200)` and treat the embedded layer as a second opinion only.
- **THE `Article 21` ANNEXES ARE ALL PRESENT — THE FY2024 AND FY2025 STANDING ACQUISITION IS CLOSED.** 153pp: law `Articles 1–21` pp.1–16; detailed revenue pp.24–33; **plan de trésorerie p.35**; **`CLASSIFICATION PAR MINISTERE ET ECONOMIQUE` at service grain + COFOG pp.39–140**; **`TABLEAUX DES EMPLOIS` pp.142–149** (`Ministère | Eff. | Mt/Annuel` by service); PIP pp.151–153. FY2024 promised these under `Article 19` and annexed nothing; FY2025 promised them under `Article 23` and annexed only the expenditure classification. **⚠ THE FY2025 DOUBLE-PRINTING TRAP DOES NOT RECUR** — the classification is printed ONCE, internal `Page 1`–`Page 102` mapping one-to-one onto PDF pp.39–140. **Do not import the FY2025 dedup rule; it would delete real data.** ⚠ pp.35, 37 and 151–153 are **landscape content on portrait pages, rotated 90°** — rotate before re-OCR, same trap as FY2025's revenue annexe.
- **⚠ THE FRAMING LETTER ANNEXES THE ECONOMIC NOMENCLATURE, AND IT HAS THREE IT-SPECIFIC CODES — THIS OVERTURNS THE STANDING BLOCK-4b CONCLUSION FOR COMOROS.** `LETTRE DE CADRAGE BUDGETAIRE POUR L'EXERCICE 2026` (35pp scan, OCRs to 52 324 chars) carries the state's chart of accounts: **`2432 Matériels informatiques`** (capital), **`6021 Fournitures de bureau et matériel informatique`**, **`6122 Entretiens des matériels informatiques, des machines et des matériels techniques`** (both biens et services). Both prior runs concluded Comorian cross-vote digital spend is structurally unfindable because the published classification aggregates to four natures. **That is true of what the state PUBLISHES and false of how the state CODES.** So the acquisition is now nameable exactly: **an execution extract or budget file at economic-nomenclature grain showing `2432`, `6021` and `6122` by ministry** — which is what `SIM_ba` holds. It replaces every vaguer standing request. **General move: read the framing letter's annexes for the chart of accounts before concluding a means-based budget cannot resolve IT spend.** The letter also annexes the administrative nomenclature by ministry and service.
- **The framing letter is now much more than a letter: 35pp against FY2025's 7pp.** It carries **FY2024 outturn** (internal revenue `63 821`m FC at 95,52% realisation; primary balance `−11 250`m = −1,74% of GDP) and **provisional H1-2025 execution** (internal revenue `31 495`m vs `33 480`m forecast = 94,1%; current expenditure `49 108`m; salaries `16 604`m; goods and services `15 896`m; internal investment `1 813`m) — **the only FY2025 execution figures located anywhere, aggregate only, so they support no ministry or digital record.** ⚠ **SCALE TRAP, third consecutive Comorian year, new pairing: the letter is in MILLIONS de FC while the law is in full francs.** ⚠ Its ceilings diverge from the enacted law — wage cap `33 690`m against enacted `37 810 000 000`, i.e. **the enacted wage bill exceeds the framing letter's own ceiling by 4 120m FC.** ⚠ Its dateline reads `Moroni le 23/0?/2025` with the month illegible; the library upload of 2025-09-04 is a proxy, not the signature date.
- **The digital vote, FY2026, at service grain, both columns cross-footing exactly.** `Ministère des Postes et des Télécommunications` code `09`: **LFR2025 `223 337 645` → LFA2026 `338 724 932`, écart `115 387 287`, TV `+51,66%`** — the third-largest proportional rise in the budget, behind Justice (+126,40%) and Affaires Étrangères (+76,35%), against a ministry block growing 3,78% and total expenditure falling 1,0%. Services: `0901 Cabinet 27 664 200 → 40 107 058`; `0902 Secrétariat Général 17 546 005 → 114 001 360`; **four NEW template directorates `0536`, `0537`, unnumbered *programmation et communication*, `0920`, each `0 → 1 400 000`**; **`0903 ACRP 50 000 000 → 73 000 000`**; `0904 Direction Générale 55 127 440 → 56 016 514`; **`0910 chambre du Numérique 73 000 000 → 50 000 000`**. Full series now five points: **194 457 800 (LFA24) → 682 681 240 (LFR24) → 235 315 816 (LFA25) → 223 337 645 (LFR25) → 338 724 932 (LFA26)**, i.e. **+74,2% on the FY2024 base**.
- **⚠ FOUR CAUTIONS ON THAT SERVICE TABLE, EACH OF WHICH WILL CORRUPT A RECORD SILENTLY.** (i) **`ACRP` and `chambre du Numérique` appear to have SWAPPED values** (50m/73m → 73m/50m), both transfer-only lines with no other nature — real reallocation or transcription swap, undecidable from this document; do not build a trajectory for either body. (ii) **`chambre du Numérique` changed service code `0905` → `0910`**; same body. (iii) **`09 0901` FY2026 reproduces the FY2025 appropriation to the franc** (`22 307 058` + `17 800 000` = `40 107 058`) — freeze or copy-forward, flag it. (iv) **`09 0904` FY2026 reads `56 016 514`, the exact figure the FY2025 run DERIVED BY SUBTRACTION for the same service's FY2025 cell when the scan was illegible** — unexplained; **neither number validates the other**, bind by geometry.
- **⚠ THE FOUR NEW DIRECTORATES ARE A MACHINERY-OF-GOVERNMENT CHANGE, NOT A DIGITAL EXPANSION, AND THEY WILL RECUR IN EVERY MINISTRY.** Each is `1 400 000` KMF of goods and services, zero salary, zero investment, **and zero established posts in the `tableaux des emplois`**. *Al-watwan*'s report of the FY2026 framing workshop records the ministry SG announcing a **new decree on the general organisation of administrative structures** creating exactly these directorates — RH, programmation et communication, affaires juridiques et coopération — government-wide. **A cross-vote extraction that reads them as programme lines will invent digital spend in twenty ministries.**
- **CAPITAL: THE DIGITAL MINISTRY GETS A STATE CAPITAL LINE FOR THE FIRST TIME IN THE CORPUS.** `Article 7`: **`Ministère des postes et télécommunication 50 000 000` (ÉTAT), no bailleurs** — against a literal `0` in LF2024, absence from the LFR2024 revised table, and absence from LF2025. It sits inside `09 0902 Investissement`, which is why the Secrétariat Général's total jumps to `114 001 360`. **~€102 000 at the peg; carry it in KMF.** Donor money remains **78,4%** of the whole capital budget (`48 279 000 001` of `61 600 000 001`).
- **⚠ THE BIGGEST DIGITAL-GOVERNANCE DEVELOPMENT IN THE COMORIAN CORPUS IS INSIDE THE FINANCE LAW AND HAS NO MONEY LINE.** `SECTION 3`, pp.9–14, inserts `Section 4 : de la télé déclaration et du télépaiement`, `Articles L.10 bis`–`L.10 Undecies`, into the *livre de procédures fiscales*: definitions of *télé procédures*, *télédéclaration*, *télépaiement* and ***plateforme fiscale***; compulsion by taxpayer tranche fixed by DG decision; **`L.10 Quinque` requiring the fiscal identifier (NIF) plus strong authentication and treating account-based filing as an electronic signature**; **`L.10 Sexies` binding fiscal data to professional secrecy *"et par la législation sur la protection des données personnelles"***; **`L.10 Septies` making platform logs evidence**; **`L.10 Decies` licensing banks, e-money institutions and mobile-payment operators by arrêté with daily reconciliation files over secure interfaces**. Plus **`Art. L46 bis`** obliging banks and microfinance institutions to report every business-account opening, modification and closure to the DGI's `Direction des Opérations Financières` within 30 days; **`Art. L44 bis`** requiring documents *"sous format électronique"* within 8 working days; and **`Art.L.1`** extended to *"l'exploitation de plateforme électronique"*. **⚠ `L.10 Sexies` cross-refers to data-protection legislation in a state whose supervisory authority does not exist and is scheduled to be created with IsDB/AfDB money — the gap between legal and fiscal commitment, written by the state itself.** **New general move: read the finance law's tax-procedure section, not just its vote tables — in a means-based budget it is where digital governance actually gets legislated.**
- **The whole téléprocédures chain is dated and none of it is appropriated:** framing letter *"digitalisation du recouvrement"* / *"Digitalisation des paiements"* (≤ Sept 2025) → PAGF-SI AMI to interface SIGIT with bank and mobile-operator platforms (Oct 2025) → LF2026 `Section 4` (adopted 26-12-2025) → **DGI validation workshop 15–17 April 2026, AFD-financed through PAGF-SI** (first-party account on `dgi.gouv.km`, plus *La Gazette*). The SG on the record: *"Au-delà de l'innovation technologique, il s'agit d'une réforme de gouvernance."*
- **⚠ `dgi.gouv.km` IS A NEW AND PRODUCTIVE TRACK-A TARGET, NOT INDEXED FROM THE FINANCE MINISTRY.** `/fr/actualite.php` is the tax administration's own newsroom and is where the *téléprocédures* rollout is reported. **Add it to the Comorian institution list.** It also carries a **DGI–ANPI meeting of 30 January 2026 on interconnecting their information systems** (`dpi.exchange` between tax and investment promotion) and confirms an **IMF mission in Moroni 27 October – 7 November 2025** for the fifth ECF review and Article IV.
- **BLOCK 4b, OUTSIDE THE VOTE — four state digital items, all priced or dated, none appropriated.** (i) **`Contrat n°08/MAPA/CVA/DNSAE`, `33 840 000` KMF to AMA SARL for computer equipment for the CRDEs**, agriculture ministry, start 04-03-2026 — **10,0% of the whole digital ministry appropriation, spent by another ministry.** ⚠ **Origin: the contract header prints a `DON:` (grant) field and the unit is a project UGP — almost certainly not fisc money.** (ii) **A prepaid payment system on public water standpipes**, `Cortex Ingelec`, `130 226 004` KMF, DGEF, from the beneficial-ownership list. (iii) **The BCC launched KomorPay (ATS), Komor Switch, Mali Ya Wakazi and a public securities market on 4 May 2026** — a national payment-interoperability layer, World Bank and IMF supported; KomorPay live since 23-04-2026 on a dedicated **120 km fibre network**, card interoperability from July 2026; **no cost stated in any of four sources**; 2024 baseline e-money float `2,7`bn KMF, `669 584` accounts of which 29,1% active, 39% banking rate. (iv) **IsDB general procurement notice `COM-1026`, 12-03-2026** — government portal, essential e-services, **digital payment system for the administration**, and an **interoperability and data-exchange platform**, Component B entirely IsDB-financed at 5 000 000 ID ≈ €5,96m; Component C funds capacity for the **`Autorité nationale de protection des données personnelles`** and the **`Observatoire national du numérique`**.
- **Identity, data exchange and statistics in the vote — absent for a THIRD consecutive year**, hand-checked across `Article 11`, `Article 7`, the full service-grain classification and the `tableaux des emplois`. No population register, CRVS, national ID, biometric enrolment, passport, voter register, social registry, interoperability layer, service bus, single window or shared services. **The FY2025 framing letter's `Programme National Comorien d'intégration des permis de conduire biométrique` has no FY2026 line either.** `Institut de la Statistique` appears only in the emplois annexe — **17 posts / `75 545 220` KMF** — establishment, no programme.
- **BLOCK 4c — ANRTIC absent from the volume for the third year, and still no activity report, re-verified.** `anrtic.km/actualites/rapports` returns verbatim **"Aucun rapport trouvé — Aucun rapport n'a encore été publié. Revenez bientôt !"** on 2026-08-04, unchanged from the FY2025 check, against `Article 8.IV` of `Loi n°23-024/AU`. **Three country-years, none published, on the regulator's own authority — a dated known vacuum for the place hub, not a chore.** ⚠ `anrtic.km` still needs a **browser UA** (403 to default). Its site was restructured and now carries an `Avis & Décisions` section. **`SIGIT` and `SIM_ba` appear nowhere in the LF2026 or the framing letter** — the FY2025 finding stands: the state names its financial IT systems only to the IMF.
- **⚠ THE `.km` DNS PICTURE CHANGED FOR A THIRD TIME AND THE STANDING RULE HELD.** FY2024: Cloudflare SERVFAILs the zone, Google resolves. FY2025: **both** SERVFAIL and the host still serves. **FY2026: no DNS check was needed — `finances.gouv.km`, `dgi.gouv.km`, `anrtic.km` and `banque-comores.km` all resolved and served on a plain `Invoke-WebRequest` first time.** Three runs, three DNS pictures, one host behaving identically throughout. **The rule is now confirmed three ways: a DNS failure of any kind is never sufficient to write a `.km` host off — attempt the fetch, pin with `curl --resolve` only if that also fails.** **`imf.org` is HTTP 403 to this network for the third consecutive run**, re-confirmed with full browser headers on `1COMFA2026001-source-pdf`.
- **TRACK B: the media API is STATIC.** `/wp-json/wp/v2/media?per_page=100&media_type=application` → **`x-wp-total: 114`, 113 distinct items, identical to the FY2025 enumeration**, newest item 2026-06-16. **That is what makes this run's absences evidence rather than failure to find** — the complete library was enumerated. Two fetches replaced the whole Track-B enumeration for a third consecutive Comorian run.
- **⚠ THE FY2026 BILL AND LAW ARE NOT IDENTICAL, UNLIKE FY2025.** No PLF2026 is published, but *Al-watwan*'s report of the rapporteur's presentation (held from the FY2025 run) gives the bill's figures and **they differ on the expenditure side while revenue is identical**: dépenses totales `142 733 536 170` reported vs `139 058 536 171` enacted; transferts `22 588 000 000` vs `20 595 000 000`; dépenses courantes primaires `90 687`m vs `88 694`m. **The FY2025 rule "do not build separate proposed and appropriated records off the same numbers" is FY2025-specific — the Assembly amended the FY2026 expenditure side.**
- **⚠ Two internal inconsistencies inside the FY2026 law's own aggregates**, to be resolved by re-OCR before use: `Article 3` gives FY2026 `Charge financière 2 085 536 170` / `Dépenses courantes 90 779 536 170` while `Article 12` gives `2 080 536 170` / `90 774 536 170`; and `Article 8` prints `Dépenses Totales` LFR2025 as `137 119 000 000` against `140 515 668 563` in `Article 3`. Separately, **`Aménagement du Territoire` and `Jeunesse, Emploi` both print `2 453 234 617` in the LFR 2025 column of `Article 11`** — a probable source error or OCR artefact; check both against the page image.
- **Searched, found nothing (FY2026):** any **`projet de loi de finances 2026`** (the FY2025 PLF docx has no FY2026 counterpart in the 113-item library — Comoros published a PLF once); any **`Budget Citoyen 2026`** (2024 and 2025 exist — **the first Comorian country-year in the corpus without one**, removing the usual third corroboration of the digital vote); any **LFR2025 text or decree** (acquisition **downgraded**, not closed — the numbers are now held, only the narrative and article-level provisions are missing); any **FY2025 execution report or TOFE 2025** (over four months overdue on the FY2024 cadence); any **`recueil des arrêtés` for 2025 or 2026** (2023 and 2024 remain the only two, so the `released` stage has an instrument and no document for two years); any **`loi de règlement` for 2024 or 2025** (the FY2024 one now ~8 months overdue); any **CBMT or DPBEP** (third year, the framing letter is the whole layer); any **procurement plan**; any **ANRTIC, ANADEN, Comores Câbles or Comores Télécom budget or annual report**; any **universal-service fund**; the **PAGF-SI `PTAB`/`PPA`**; any **cost figure** for Komor Switch, KomorPay or Mali Ya Wakazi.
- **Seen and deliberately not staged, so it is not rediscovered:** `2026/04/Analyse-de-la-Viabilite-de-la-Dette-1.pdf` (**duplicate** of the December 2025 DSA already staged under a different URL by the FY2025 run); `2026/01/AMI-Etude-pour-interfacage-du-paiement-via-Mobil-Banking.docx` (**re-upload** of the October 2025 AMI already staged); `Bulletin-sur-les-devises-et-evolution-des-taux-de-change.pdf` (11pp native, Sept 2025 FX outlook — no digital content, and the KMF/EUR peg is already stated in the framing letter); `Contrat-2026-MOBILIER-DE-BUREAU-MOM-SARL.pdf` (office furniture); the four **`ASCENT-Comores`** World Bank energy-access safeguard docx files (out of scope); `Rapport-sur-execution-de-la-lois-de-finances-2020.pdf` and `ROD-execution-budget-2022-VF.pdf` (**FY2020 and FY2022, out of scope** — recorded again because this ministry backfills and they keep surfacing); *Al-watwan*'s 2026-05-05 payment-systems article (**dropped as a duplicate** — its payload is covered between the BCC's first-party notice and *Mayotte Hebdo*'s figures); `dig.watch/countries/comoros` (second-hand synthesis, mined for leads only — it named Komor Switch and the transfer of `.km` domain technical management to ANADEN).

### Comoros — first budget-extract of the FY2024/FY2025/FY2026 chain (extract, 2026-08-04)

**22 documents, 3 country-years, 14 records.** Archetype match: **M, *budget de moyens* variant** (added to the strategy library by this run); no new letter earned. **Every figure below was read from a rendered page image and cross-footed**; where it disagrees with the three sweeps of the same night, the image reading is the record.

- **⚠ THE THREE SWEEPS' CENTRAL CROSS-VOTE FINDING IS WRONG AND IS RETRACTED. COMOROS HAS A DIGITAL LINE OUTSIDE THE SECTOR MINISTRY, IN EVERY YEAR IT PUBLISHES A SERVICE CLASSIFICATION, AND IN FY2026 IT IS THE LARGEST DIGITAL APPROPRIATION IN THE COUNTRY.** `08 0825`, COFOG `0133`, inside the finance ministry: **`Direction Générale de l'informatique` 9 128 000 (LFR2024) → 9 128 000 (LFA2025) → 0 (LFR2025) → renamed `Direction Générale de Système d'Information et de Communication` 277 128 000 (LFA2026)** — salaire 6 128 000 + biens et service 201 000 000 + investissement 70 000 000, cross-footing to the printed `Total service`. That is **82% of the whole *Ministère des Postes* vote** for FY2026 and a capital line **40% larger** than the digital ministry's. All three sweeps missed it because they searched the *amounts* of an economic-nature classification; **the handle is the `Designation` column**, and it has to be walked ministry by ministry once. The body was **renamed on a stable code**, so join on `0825`.
- **⚠ SECOND RETRACTION: "IDENTITY AND DATA EXCHANGE ARE ABSENT AT EVERY GRAIN" IS ALSO WRONG.** `06 0615 Direction de l'État Civil et Casier Judiciaire`, COFOG `0160`, in the justice ministry: **2 500 000 (LFR2024) → 3 000 000 (LFA2025) → 2 000 000 (LFR2025) → 4 000 000 (LFA2026)**, wholly *Biens et service*, **no salary line and no capital line in any column**. What the sweeps got right is that no line names a digital or registry-modernisation activity — recorded `scope_confidence: unclear` for exactly that reason. **The registry is a revenue centre and a donor project simultaneously**: the FY2026 revenue annexe books `727 Recettes des documents d'État Civil` **324 000 000** and `7162 Timbres fiscaux (Documents Biométriques Semlex)` **2 866 000 000** — the private concessionaire is named in the state's own revenue nomenclature — while the FY2026 PIP annexe carries *« Appui à la modernisation de l'état civil aux Comores — AMECC »*, financier **France**. **Roughly 800× more expected in fees than appropriated to spend, and modernisation entirely external.**
- **⚠ THE FY2024 OUTTURN IS ESTABLISHABLE AND THE FY2024 SWEEP'S "DO NOT COMPUTE AN EXECUTION RATE" IS SUPERSEDED.** That sweep saw the *transferts* row alone (prévision 613 000 000) and noted it matched neither the LFA nor the LFR. It matches neither **because it is one nature of three**: salaires 44 461 240 + biens et services 25 220 000 + transferts 613 000 000 = **682 681 240**, the LFR2024 ministry figure to the franc, which proves the three rows are the whole vote and that the denominator is the revised budget. **Exécution 41 223 675 + 2 362 400 + 140 000 000 = 183 586 075 — 94,41% of what parliament voted and 26,89% of what the rectificative promised.** There is no investment row, consistent with `Article 7`'s printed zero. **The story of Comorian FY2024 is that the August rectificative multiplied the digital vote by 3,5 and the money never arrived**; the +488 223 440 was almost entirely a transfer line delivered at 22,8%.
- **⚠ THE LF2026 VOLUME'S EMBEDDED TEXT LAYER IS NOT ONLY CORRUPT, IT IS MIS-PAGINATED — A NEW TRAP FOR THE CORPUS AND A HARDER ONE.** The FY2026 sweep established the corrupt-digits half. The rest: **the layer's page N is not the image's page N.** Its "page 78" carries services (`0112`, `0825`, `0829`) that the *image* of PDF p.78 does not (`0835`, `0836`, `0837`, `0814`), while pp.87–88 match exactly. It reads like the text of an earlier draft with different page breaks. **So the layer cannot be used even as a corroborating second opinion, because you cannot tell which page you are corroborating** — it may only be used to *locate a service by name*. Every figure in this extraction came from `pypdfium2` renders at 170–450 dpi.
- **⚠ AND TESSERACT LOSES THIS TABLE AT EVERY SETTING.** `--psm 3`, `--psm 6`, 400 and 600 dpi and a digits whitelist all returned unusable grids on the boxed classification pages; on `08 0825` a 600 dpi pass returned a **plausible and wrong** `6 028 000 / 5 000 000` where the page prints `6 128 000 / 3 000 000`. It was caught only because it failed the `Total service` cross-foot. **The three-deep self-check — four natures → `Total service` → `TOTAL MINISTERE` → `Article 11` — is what makes this document extractable at all.**
- **The digital vote, all six stages the corpus now holds, every figure cross-footed:** `194 457 800` (LFA2024) → `682 681 240` (LFR2024) → **`183 586 075` executed 2024** → `235 315 816` (LFA2025) → `223 337 645` (LFR2025) → `338 724 932` (LFA2026). **+74,2% on the FY2024 appropriated base.** The FY2026 volume's economic recapitulation independently re-sums the ministry's FY2026 salaire (84 904 932) and biens-et-service (30 820 000) from the same service rows exactly — a free second proof of the whole service table.
- **The FY2025 revised stage was built from the FY2026 law at service grain**, exactly as the FY2026 sweep directed: `0901 27 664 200`, `0902 17 546 005`, `0903 ACRP 50 000 000`, `0904 55 127 440`, `0910 chambre du Numérique 73 000 000`, summing to `223 337 645`. **A rectificative adopted 26 December 2025 and published nowhere is now held, line by line, from the next year's law.** The acquisition for the LFR2025 *text* stays open at low priority, for its narrative and article-level provisions only.
- **`ACRP` IS EXPANDED, AND IT IS OUT OF SCOPE.** Three sweeps recorded that the volume never expands the acronym. The ***Budget Citoyen 2024*** does, in a footnote on its *établissements publics* page: **`ACRP` = *Autorité Comorienne de Régulation Postale***. **Postal-services regulation is neither data governance nor digital transformation, so its 50 000 000 (FY2025) / 73 000 000 (FY2026) transfer is NOT recorded as a digital line** — a deliberate scope call, logged, and the reason the recorded services do not sum to `TOTAL MINISTERE`. *(The ICT regulator is ANRTIC, which carries no appropriation at all, in any of the three years.)*
- **⚠ A NAMED DIGITAL LINE, AND AN IN-YEAR CUT, LIVE IN THE ARRÊTÉ COMPILATION — NOT IN ANY FINANCE LAW.** The 127-page *recueil des arrêtés 2024* OCRs cleanly and contains one virement touching a digital nature: **`6153 Site Web et Consommation Internet`, service `9998` (dépenses communes), 45 000 000 → 15 000 000 in November 2024, the 30 000 000 moved to `6135 Frais de Gardiennage`**. The arrêté's own table cross-foots to 326 410 000 on both sides. **The state took two-thirds of its website-and-internet budget and spent it on security guarding, six weeks before year end.** This adds a **fourth** IT-specific economic-nature code to the three the FY2026 framing letter annexes. **General move: in a means-based budget the year's arrêté compilation is where nature-grain digital money becomes visible.**
- **THE `released` STAGE IS ANSWERED, AND THE ANSWER IS "INSTRUMENT PUBLISHED, TABLES NOT".** The FY2024 sweep called a full OCR of the *recueil* the highest-value open question for the country. Done: the compilation cites `Arrêté n°24-001/MFBSB/CAB du 22 janvier 2024 portant ouverture et répartition des crédits pour le 1er trimestre 2024` and `Arrêté n°24-047/MFBSB/CAB du 01 octobre 2024` for Q4, and reproduces a Q2 opening arrêté whose `Article 1` opens credits *« mentionnés dans les tableaux annexés au présent Arrêté »*. **The annexed tables are not in the compilation.** So Comoros warrants credits quarterly and publishes no per-service amounts — a dated absence, not a standing chore. **Close the question; do not re-OCR the recueil.**
- **THE LF2024's LAW NUMBER AND PROMULGATION DECREE ARE ESTABLISHED, FROM THE SAME RECUEIL.** The WTO copy carries a blank `LOI N°23-______/AU`; the *recueil des arrêtés 2024* cites, in its own *VU* clauses, **`Décret n°23-134/PR du 15 décembre 2023 portant promulgation de la loi n°23-019/AU du 27 novembre 2023, portant loi de finances 2024`**. The FY2024 acquisition line closes. **General move: when a finance law is recovered without its promulgation, read the year's arrêtés — every one of them recites it.**
- **Statistics: found, priced and deliberately not recorded.** `08 0808 Institut de la Statistique (INSEED)` 180 123 260 (LFR2025) → 149 865 220 (LFA2026), plus regional institutes `0835` 58 336 400, `0836` 27 990 400, `0837` 60 243 380 (FY2026). The three sweeps' "no statistics line" is wrong on the facts. **Not recorded as digital-finance lines** — statistical production is a distinct function, the taxonomy carries no statistics slug, and admitting whole statistical envelopes would import the statistical system into a digital-spend dataset. Figures are in `budget-archive/COM/com-cross-vote-digital-lines-2024-2026.csv` so a later ruling can promote them for the cost of writing the records.
- **Also looked for and not recorded, with reasons.** The FY2026 **template directorates** (`0536`, `0537`, unnumbered *programmation et communication*, `0920`) at a flat 1 400 000 each, zero salary, zero posts — a machinery-of-government change that will recur in every ministry. **`19 1914–1917 Direction Générale/Régionale de l'Information et de la Communication`** (COFOG `0830`) — government press and broadcasting, not digital transformation. **`05 0507/0529/0530/0531`** health planning-and-statistics directorates — mixed planning units, purpose not stated as digital or data. The FY2024 **Gouvernorats capital line 4 000 000**, *« Achat des mobiliers des bureaux et matériels informatiques »* — mixed furniture plus generic office IT, overhead rather than a digital-activity line (the Burundi PPM scope call). The **`Cortex Ingelec` prepaid water-standpipe payment system, 130 226 004 KMF** — a water works contract, and a contract is not an appropriation. The **`AMA SARL` CRDE computer-equipment contract, 33 840 000 KMF** — the contract header prints a `DON:` field and the spending unit is a project UGP, so it fails the origin gate as domestic-state, and it is a contract, not a budget line.
- **Case 5: no candidates, no resets, no contradictions filed.** `raw/` holds **no** COM `finance_origin: domestic-state` record at all — the FY2024 sweep's "the country's domestic-state corpus starting from zero" is confirmed. The twelve COM finance-tagged items in `raw/` are all donor-side or operator-side (AfDB, IsDB, IFC, China Eximbank, Axian/Yas, KomorPay). There is nothing for a budget document to become master of.
- **Internal inconsistencies in the LF2026, recorded and not resolved.** `Article 3` gives FY2026 *charge financière* 2 085 536 170 and *dépenses courantes* 90 779 536 170 where `Article 12` gives 2 080 536 170 and 90 774 536 170; `Article 8` prints FY2025 *dépenses totales* as 137 119 000 000 against 140 515 668 563 in `Article 3`; and **`Aménagement du Territoire` and `Jeunesse, Emploi` both print `2 453 234 617` in the `LFR 2025` column of `Article 11`** — confirmed on the page image, so it is the state's error and not an OCR artefact. None touches a digital line, so none is filed as a contradiction; recorded here so the next reader does not chase them. Likewise the `Article 11` caption reading `Ecart ( LFA2026-LFA2025)` above a table headed `LFR 2025 | LFA 2026`: the header is right on the arithmetic and the caption is wrong.
- **The FY2026 finance law legislates a digital-governance regime with no money line, and that is the country's largest data-governance development.** `SECTION 3`, pp.9–14, inserts `Section 4 : de la télé déclaration et du télépaiement` (`Articles L.10 bis`–`L.10 Undecies`) into the *livre de procédures fiscales* — a *plateforme fiscale*, NIF plus strong authentication, account-based filing constituting an electronic signature, platform logs as evidence, licensed banks / e-money institutions / mobile-payment operators with daily reconciliation files over secure interfaces, bank reporting of every business-account opening within 30 days, and `L.10 Sexies` binding fiscal data to *« la législation sur la protection des données personnelles »* — **in a state whose data-protection authority does not exist and is scheduled to be created with IsDB/AfDB money.** No appropriation anywhere carries it. Carried into the FY2026 records' notes; belongs on the place hub as a dated known vacuum.
- **`amount_usd` left blank on all 14 records.** `lookups/fx-imf-annual.csv` carries KMF only as a ball-park euro-peg derivation, not a named fiscal-year average, and the driver forbids spot-converting a fiscal-year figure. The franc is pegged at **491,96775 KMF = 1 EUR**; every euro figure in the records is flagged as a dated derived conversion.
- **Non-yields, so the sweep can stop spending its cap.** The **TOFE 2024** (aggregate only, no ministry grain), the ***Stratégie de réforme de la GFP 2024-2033***, the **IMF fourth ECF review**, the two **IMF/FAD technical-assistance reports**, the **PAGF-SI procedures manual**, the **debt-sustainability analysis**, the **STATCAP note**, the two ***budgets citoyens*** (corroboration and narrative only) and the ***liste des marchés et bénéficiaires effectifs*** support **no finance record**. The *dépenses fiscales* report quantifies a **985 845 035 KMF telecoms tax expenditure (26,21% of all domestic consumption-tax expenditure)** — five times the FY2024 digital vote — which is a tax expenditure and must never be recorded as an appropriation, but which no Comorian digital-spend figure should omit.

### Cabo Verde — the best-published chain in the collection, a Liferay library you walk by folder id, and a digital ministry that executed zero investment (sweep, 2026-08-03, FY2024)

- **Fiscal year:** calendar, stated in terms. `Lei n.º 35/X/2023`, `Artigo 1.º`: *"É aprovado o Orçamento do Estado para o **ano económico de 2024**"*, published in the **Boletim Oficial I Série n.º 134 of 31 December 2023** — the day before the year it appropriates for. Corroborated by `Decreto-lei n.º 1/2024` of 3 January 2024 setting execution rules *"para o ano económico de 2024"*, by the `Conta Provisória` running `I Trimestre` → `IV Trimestre 2024`, and by the `Síntese Informativa da Execução` running January→December. Document label `2024`.
- **⚠ THE FINANCE MINISTRY IS AT `mf.gov.cv`, NOT `minfin.gov.cv`.** `minfin.gov.cv` returns **NODATA on both Cloudflare and Google DoH** — it resolves as a name with no A record. That is a wrong hostname, not a dead host, and the distinction matters: **the apex `mf.gov.cv` also fails to connect; only `www.mf.gov.cv` serves.** Both public resolvers agreed on all 45 hostnames checked in this run — no repeat of the Comorian `SERVFAIL` divergence.
- **⚠ TRACK B IS SOLVED, AND IT IS A NEW SHAPE: LIFERAY 7 WITH THE JSON APIs SHUT AND THE PORTLET OPEN.** `www.mf.gov.cv` is Liferay 7, `scopeGroupId=198414`. **`/api/jsonws/dlapp/…` returns 403 and `/o/headless-delivery/v1.0/…` returns 404** — but the Document Library portlet renders **server-side** and can be walked directly:
  `{page}/-/document_library/{portletInstance}/view/{folderId}?_com_liferay_document_library_web_portlet_DLPortlet_INSTANCE_{instance}_delta=200`
  Sub-folders come back as `…/view/{id}` anchors with the folder label as the anchor text; **file entries come back as `data-title="…"` attributes** (and thumbnail URLs), and the download URL is simply `https://www.mf.gov.cv/documents/198414/{folderId}/{URL-encoded title}` — **no UUID, no auth, no bot guard, default UA accepted.** Two fetches per section replaced the whole enumeration. **This is the third CMS pattern in the corpus after WordPress-REST (Cameroon, Comoros) and the Angolan CMS: where a Lusophone finance ministry runs Liferay, walk the DLPortlet by folder id.**
- **The folder ids, recorded so no future CPV run re-derives them.** `/web/dnocp/orçamento-do-estado` instance `CCgzagQ0WG8I`: OE year folders 2005–2027, FY2024 = `3832853` → `3832857` *Proposta* → `3901068` ROE, `3901071` Lei, `3901074` Anexo, `3901077` Riscos, **`3901080` Mapas**; `3902308` Diretrizes. `/web/dnocp/contas-geral-estado` instance `0cIRfiy8xN0Z`: CGE 2005–2024, **FY2024 = `5884176`**. `/web/dnocp/contas-provisórias-do-estado` instance `LbXpmIbuZxlI`: `4473589` → quarters `4473592`, `4711334`, `4942098`, `5175492`. `/web/dnocp/alterações-orçamentais` instance `mn6WctW9iEJK`: **FY2024 = `4261174`**. `/web/dnocp/síntese-informativo-mensal` instance `UuLchBvGh5se`: **FY2024 = `4275663`**. Public debt (DGT): `92878/4408978` annual, `92878/4408981` quarterly.
- **⚠ `/web/dnocp/contas-geral-do-estado` (with the "do") IS AN EMPTY ASSET-PUBLISHER SHELL. The documents are at `/web/dnocp/contas-geral-estado` (without it).** Two near-identical slugs, one dead, both linked from the same site menu. A run that hits the first one and stops would record "no outturn published" for a country that publishes twenty years of them.
- **TIER 0 IS CLOSED WITHOUT AN ACQUISITION: THE ENACTED LAW *IS* THE ESTIMATES VOLUME.** `Lei n.º 35/X/2023` as printed in the BO is **128 pages, NATIVE, 425 638 extractable characters**, carrying `Mapa I` through `Mapa XV` at pp.34–123 — every vote, every autonomous fund, the functional and economic classifications, the social-security budget, municipal transfers, public-enterprise expenditure and a gender-disaggregated budget — plus `Resolução n.º 135/X/2023`, the Assembly's own budget, at pp.124–128. **There is no separate annexed volume to chase.**
- **⚠ ROTATION TRAP, AND IT IS THE MOST IMPORTANT PROCEDURAL LINE IN THIS SECTION.** Pages 34–123 are printed **rotated 90°** and `pdfplumber` returns their text **character-reversed**: `oiretsiniM aD aimonocE latigiD` is *Ministério Da Economia Digital*, `236.569.093.1` is `1.390.965.632`. **This is native text in a rotated CTM, NOT a scan.** Do not send it to OCR — you would replace perfect data with guesses. Group `extract_words()` by `x0`, sort each group by descending `top`, reverse each token. **New general rule: a Boletim Oficial page that returns reversed strings is a rotation, and a page that returns nothing is a scan; test which before choosing a tool.**
- **The same tables are ALSO published unrotated as standalone native PDFs at proposal stage** — `mf.gov.cv/documents/198414/3901080/Mapa1.pdf` … `Mapa4.pdf`, `Mapa5.1+GPM` … `Mapa5.16+Total`, `Mapa6.1+GPM` … `Mapa6.10+MCIC`, all reachable **without a UUID**. For every figure the two agree on, these are the cheaper target.
- **⚠ BUT THE PROPOSAL AND THE LAW DISAGREE BY 28 309 909 CVE IN THE PROGRAMME-TYPE SPLIT.** Both cross-foot to `Total Despesa 85 948 752 206`, but the proposal prints `Finalístico 53 601 207 578 / Apoio Administrativo 17 257 378 928` and the law prints `53 629 517 487 / 17 229 069 019`. **The two digital-named ministries' rows are identical in both**, so the shift is elsewhere — but every record built from the standalone mapas must carry `budget_version: proposed`, never `appropriated`. `Mapa VI` is also **incomplete**: only 10 of the 15 ministry files exist (it stops at `Mapa6.10+MCIC`) and there is no `Mapa6` total.
- **THE DIGITAL VOTE, FY2024.** `Mapa III — Despesas por Natureza de Programa segundo a Classificação Orgânica`: **`GOV - Ministerio Da Economia Digital` 553 090 000 (Investimento) + 811 792 545 (Finalístico) + 26 083 087 (Gestão e Apoio Administrativo) = 1 390 965 632 CVE**, against a total state expenditure of 85 948 752 206. **`Ministerio Da Modernização Do Estado E Da Administração Publica` 111 000 000 + 77 317 675 + 180 672 059 = 368 989 734.** Both cross-foot; both identical in proposal and law.
- **⚠⚠ THE FINDING: THE DIGITAL MINISTRY EXECUTED A PRINTED, LITERAL ZERO OF ITS INVESTMENT BUDGET.** `Conta Geral do Estado 2024`, **p.163**, `Mapa III` — columns `Total Inicial (OI) | ORP (Inv | Fin | Apoio | Total) | EXE (Inv | Fin | Apoio | Total) | Taxa EXE/ORP`. Row `01.03.02`: **OI 1 390 965 632 → ORP 1 483 485 681 (553 090 000 + 901 812 594 + 28 583 087) → EXE 489 920 474 (`0` + 464 756 445 + 25 164 029) = 33,0%.** Every cell cross-foots. **Against 91,0% for the Presidency, 86,7% for the Assembly, 91,6% for the Court of Auditors and 80,0% for Finance, the digital ministry is the outlier by more than forty points, and its capital execution is nil.** Do not read the `0` as a data gap: its row total cross-foots to it, and the thirty other rows on the page carry non-zero investment execution. **A state that legislated a Ministério da Economia Digital and published an *Estratégia da Economia Digital* in September 2024 spent nothing at all on digital capital that year.**
- **⚠ THE SCALE CHANGES BETWEEN TABLES INSIDE THE CGE.** p.163 is full escudos; **p.53 prints the same ministry as `1 391 | 93 | 1 483` in MILHÕES**; p.62 is percentages; p.188 breaks it down by financing source and ends `489 920 474 | 66,8%` on a different denominator. Read the header of every table. Also: the CGE's `Orçamento Inicial` for the Assembly is `1 170 329 912` (the *Orçamento Privativo* total), not `Mapa III`'s `1 057 041 423` — two perimeters, not a contradiction. And `Taxa` is computed against **ORP, not OI**.
- **⚠ THE CGE 2024's FIRST FIVE PAGES RETURN ALMOST NOTHING AND IT IS NOT A SCAN.** A short probe returns `Página 4 de 156 Página 5 de 156` because the front matter is a page-number overlay on an image cover. **400 085 characters are in the file.** Read the whole thing before concluding anything about it.
- **THE DATA-PROTECTION AUTHORITY IS APPROPRIATED THROUGH THE LEGISLATURE, NOT THE EXECUTIVE — AND THIS IS A FIRST FOR THE COLLECTION.** `Resolução n.º 135/X/2023` (BO p.2816), the Assembly's *Orçamento Privativo*, carries under `OUTRAS DESP. CORRENTES-ORGÃOS EXTERNOS`: **`CNPD (Comissão Nacional de Protecção de Dados)` 35 255 451 CVE**, `Dotação inscrita no Orçamento do Estado 35 255 451`, **`Receita Próprias 0`**; plus `ARC` 87 210 101, `Provedor de Justiça` 39 871 455, `CNE` 35 760 297. **Cabo Verde is the first country in this corpus whose DPA has a locatable, dated, domestic appropriation** — Comoros has no authority at all, and Congo, Cameroon and Comoros all fund the sector regulator by statute from operator levies, outside the vote. The CNPD has **no own-source revenue whatsoever**. The single-mandate carve-out applies cleanly: `scope_confidence: whole`. **A cross-vote scan of the ministerial `Mapa III` alone would wrongly report that Cabo Verde does not fund its data-protection authority. New general rule: in a state with a parliamentary *orçamento privativo*, read it — the independent authorities are in there.**
- **But the DPA's programme money is external.** `TdR — Estratégia de Comunicação da CNPD`, February 2024, is issued by the finance ministry's UGPE **under a US$20 million World Bank credit** (*Digital Cabo Verde*). Running costs domestic, capability-building donor-financed. The CNPD's own `Plano de Atividades 2024` (11pp, native, dated 27-12-2023) **contains no budget figures at all.**
- **⚠ CNPD PUBLICATION TRAP.** Every link under `cnpd.cv/relatorio-de-atividades/` for 2017–2023 points at a file named **`CNPD-Plano-de-Atividades-{year}.pdf`** — the plan, not the report. Only 2015 and 2016 have genuine `Relatorio` filenames. Whether the authority has published any activity report since 2016 is unresolved and worth settling.
- **THE STATE'S DIGITAL AGENCY IS A STATE ENTERPRISE AND ITS MONEY IS 73% THE SIZE OF THE WHOLE DIGITAL VOTE, WHOLLY OUTSIDE IT.** `NOSi, E.P.E. — Plano de Atividades e Orçamento 2024` (22pp, native, on `nosi.cv/documents/20121/2842828/`), p.14, **header `(mCVE)` — MILHARES of escudos**: `Total de Rendimentos 2024 **1 016 801** mCVE` = 1,02 bn CVE, of which **`Protocolos` 333 345** (money the state pays NOSi under inter-institutional protocols, sitting in the *buying* ministries' votes) and **`Projetos Financiados` 269 638** (donor). Costs `Total FSE 926 602`, `Gastos c/ Pessoal 338 995`. **A CPV digital-spend total built from `Mapa III` alone understates the state's actual outlay by roughly the size of NOSi**; the `Protocolos` slice must be flagged `is_transfer: true`. **⚠ THIS IS THE ONLY CPV ARTEFACT IN `mCVE`; every other one is in full escudos. Do not carry either assumption across.**
- **Cybersecurity has no vote line and lives inside NOSi.** No cybersecurity rubric appears at ministry grain anywhere in the FY2024 budget, despite `Decreto-lei n.º 9/2021` (regime jurídico de cibersegurança) and `Decreto-Regulamentar n.º 1/2021` creating the CSIRT. The `PAO 2024` commits NOSi to *"Implementar CSIRT RTPE e melhorar o ambiente de Cibersegurança Nacional"* and to ISO-27001 certification of its PKI, from its own revenue. **Same structural answer as the Francophone states — the money is outside the vote — but by a different mechanism: a state enterprise's trading revenue rather than a statutory levy.**
- **THE ONLY INSTRUMENT BELOW MINISTRY GRAIN IS THE MONTHLY `Alterações Orçamentais` XLSX SERIES, AND IT IS FULLY MACHINE-READABLE.** Folder `4261174`, single sheet `Alterações Orçamentais.rdl` (an SSRS export), **two-level layout, not flat**: header row `CABIMENTO | ORGÂNICA | CÓDIGO | UNIDADE / PROJETO` with money under two column pairs — **`TESOURO` → `ANULAÇÃO`/`REFORÇO` and `DONATIVO` → `ANULAÇÃO`/`REFORÇO`** — then detail rows carrying `NATUREZA`, **`FINANCIADOR`** and `RÚBRICA CLASSIF. ECONÓMICA` with their own amounts. **The origin gate is handed over ready-made, per virement**: a reinforcement in the `DONATIVO` columns is external money moving inside the state budget. December is 5 567 rows / 476 cabimentos, January 1 071 / 100; **the files are NOT cumulative**. **⚠ Eleven of twelve months are published — APRIL IS ABSENT from the folder listing.**
- **The named digital project codes, none of which appears in any published mapa:** **`65.05.02.02.117 — Cabo Verde Digital`** (Economia Digital); `50.01.01.01.225 — Desmaterialização Do Arquivo Da Dnap`; `50.01.01.04.40 — Espaço Cidadão - Comunidade Integrada`; `50.01.01.04.35.02 — Inovação E Aprendizagem - Gaa`; `40.10.42.02 — Planeamento, Orçamento E Gestão MMEAP`; `40.10.42.92.02 — Recrutamento Centralizado`.
- **Identity, data exchange and statistics — searched by name, absent at every published grain.** No line for a *registo civil* / CRVS, *bilhete de identidade*, biometric enrolment, ABIS, passport system, voter register, social registry, interoperability layer, service bus or single window in `Mapa III`, `Mapa IV` or the FSA mapas. The delivery vehicles exist — `autentika.gov.cv`, the *Sistema de Informação da Justiça*, `Porton di nos Ilha` — but they are **built by NOSi under protocol and financed by the World Bank's Digital Cabo Verde project**, so they carry no separable domestic appropriation. **Same result as Comoros and Congo; three countries now, so this is a regional pattern and not a national quirk.**
- **The ministry-envelope near-miss, with a number that does not match.** Before the 1ª Comissão Especializada on 16 November 2023 the State Modernisation minister gave her sector's OE24 total as **403 489 734$00**; `Mapa III` gives the *ministry* **368 989 734**. The difference, **34 500 000**, is suspiciously round — almost certainly an attached autonomous service, settled by the `Mapa VI` FSA tables. **Do not reconcile these by assumption.** In the same session she stated that the *"projetos de «Transformação Digital do Setor Público» … englobam a maior fatia do orçamento de investimento, **financiados pelo Banco Mundial**"* — a minister putting on the record that the largest slice of her investment budget is external credit. **That single sentence is worth more to the origin gate than the whole vote table.**
- **The `Anexo Informativo` is native but text-sparse — 49 878 chars over 101 pages. Use `extract_tables`, not `extract_text`.** Same for the `Relatório IPSAS` (10 783 chars over 19pp). **And the `Síntese Informativa da Execução` is a slide deck whose numbers are inside images — 2 385 chars over 15 pages, the one CPV artefact whose payload is not in its text layer.**
- **⚠ The `Síntese` filenames are inconsistent month to month** — separator, capitalisation and word order all change, and November's reads `Sintese Informativa da Execução Informativa Novembro_2024`. **Enumerate the folder; never construct these by pattern.** Same lesson as `finances.gouv.km`, now twice.
- **The `ROE 2024` is the country's richest narrative artefact — 101pp, 222 220 chars native — and its scale varies by table** (full escudos in the narrative, *milhares* or *milhões* in summary tables, percent of GDP in ratios). It is the one CPV FY2024 document where the 1 000× error is live.
- **The audit stage exists as a live series and is simply not due yet.** `tribunalcontas.cv/parecer-da-conta-geral-do-estado-{year}` runs 2020–2023, the last being `PCGE_2023_FINAL.pdf`; **`-2024` returns 404**. The CGE 2024 itself was only posted on **30 September 2025**, so the FY2024 *parecer* is expected late 2026 / 2027. **Overdue is the wrong word for this one; not yet is the right one.** Separately, **the court's `relatórios de acompanhamento da execução orçamental` series appears to have lapsed** — section pages exist for 2020–2023 and the 2023 page carries no documents — and its `relatórios de auditoria` listing stops at 2023, with **no audit of any digital or systems procurement located for any year**.
- **Public debt is a first-class instrument here, because the digital investment is credit-financed.** The DGT publishes an annual `Relatório de Execução da Dívida Pública` (32pp native, dateline *Setembro - 2025*) and a quarterly series. **In a country whose digital capital comes from an IDA credit and AfDB operations, the debt report is the check on whether a "government investment" headline is fisc money or borrowed money.**
- **`boe.incv.cv/Bulletins/Download/{integer}` serves whole Boletim Oficial issues by id** — `5554` is the 3 January 2024 issue carrying `Decreto-lei n.º 1/2024`. A second route to any CPV legal instrument when the ministry library does not hold it.
- **`med.gov.cv` — the Ministério da Economia Digital's own website — is a placeholder reading `WEBSITE EM CONSTRUÇÃO`**, and has been since 2022. It still serves documents under `/documents/40469/…` (the `EEDCV — Estratégia da Economia Digital de Cabo Verde`, September 2024). **The digital ministry has no publication channel of its own.**
- **`arme.cv` resolves on both public resolvers (41.221.192.154) and times out on TCP 443 and 80.** That is neither NXDOMAIN nor refused — describe it precisely. Exa holds a crawl of it, so it serves someone; a different network path is the only route.
- **Dead aliases to know:** `tcontas.gov.cv` and `arap.gov.cv` both return **503** (the live hosts are `tribunalcontas.cv` and `arap.cv`); `dnre.gov.cv` returns **502**; `ine.cv` is a 10 697-byte SPA stub with no server-rendered document list. **NXDOMAIN on both resolvers:** `contratacaopublica.cv`, `portaldocidadao.cv`, `porton.cv`, `ucrepcp.cv`, `tribunaldecontas.cv`, `www.arap.gov.cv`, `www.tcontas.gov.cv`, `www.minfin.gov.cv`. `asemana.publ.cv` **SERVFAILs on both**.
- **Searched, found nothing:** any *orçamento rectificativo* / *lei orçamental retificativa* for 2024 — **Cabo Verde passed one for 2026 but not for 2024, and the year's revisions ran entirely through the monthly *alterações orçamentais***; any government-wide procurement plan (`ecompras.gov.cv` redirects into `mf.gov.cv/web/ecompras` and carries none, and the only annual plan located anywhere is ARAP's own, for ARAP, with **2022 and 2023 missing from its series and no `orçamento` after 2021 and no `conta de gerência` at all**); any NOSi *relatório e contas* as opposed to its forward plan; any INE budget or annual report; any universal-service fund or ICT levy body; any IMF Article IV or programme document mirrored on `mf.gov.cv` (**unlike Comoros, the Cabo Verdean ministry does not mirror the Fund**); any CNPD activity report after 2023.
- **What Cabo Verde publishes that nobody else in this collection does:** twenty years of budget documents in one indexable library (OE 2005–2027, CGE 2005–2024, alterações 2017–2026, contas provisórias 2010–2026, sínteses 2017–2026); **quarterly cash-basis IPSAS statements**; a monthly execution bulletin; and a **project-grain virement register with the financier printed on every row**. FY2024 came out with six of seven stages held — proposed, appropriated, released, revised at project grain, in-year actual and final actual — **one scan in thirty-one artefacts**, and only the audit outstanding.

### Cabo Verde FY2025 — the digital vote cut 73% with capital appropriated at zero, a Liferay folder that changed shape, and a ROE that went from native to images (sweep, 2026-08-03, FY2025)

*(Second CPV run. The FY2024 section above holds the reconnaissance — hostnames, portlet instances, the rotation trap, the CNPD-in-the-Assembly finding. This section records only what FY2025 changed or added, and corrects one FY2024 error.)*

- **Fiscal year:** calendar, stated in terms. `Lei n.º 45/X/2024`, `Artigo 1.º`: *"É aprovado o Orçamento do Estado para o **ano económico de 2025**"*, published in the **Boletim Oficial I Série n.º 125, SUPLEMENTO, of 30 December 2024**. `Decreto-lei n.º 61/2024` of 31 December 2024 sets execution rules *"para o ano económico de 2025"*. Same shape as FY2024 — the law lands the day before the year it appropriates for.
- **⚠⚠ THE LIFERAY FOLDER SHAPE IS NOT STABLE YEAR TO YEAR, AND THIS IS THE MOST IMPORTANT PROCEDURAL LINE OF THIS RUN.** FY2024's `OE 2024` folder `3832853` had a `Proposta` subfolder with five sub-subfolders and **30 individual mapa PDFs** in `3901080`. **FY2025's `OE 2025` folder `4674538` is FLAT: ten files, no subfolders, and all 43 mapas ship as a single `ULTIMO_MAPAS_Oficial.zip` (32.8 MB).** A run that walks FY2024's shape against FY2025 finds no mapas and concludes wrongly. **Enumerate the year folder every time; never carry a subfolder layout across years.**
- **FY2025 folder ids:** `/web/dnocp/orçamento-do-estado` instance `CCgzagQ0WG8I` → **`4674538`** (flat). `/web/dnocp/alterações-orçamentais` instance `mn6WctW9iEJK` → **`5175585`** (all twelve months). `/web/dnocp/síntese-informativo-mensal` instance `UuLchBvGh5se` → **`5209609`** (all twelve). `/web/dnocp/contas-provisórias-do-estado` instance `LbXpmIbuZxlI` → `5400634` → `5400688` 1ºT, `5657664` 2ºT, `6016460` 3ºT, **`6298940` 4ºT**. `/web/dnocp/contas-geral-estado` instance `0cIRfiy8xN0Z` → **no 2025 folder; the year list ends at `Conta Geral do Estado 2024`.** Next-year folders already seen: `OE 2026` `5793427`, `OE 2027` `6566427`, alterações 2026 `6450176`, contas provisórias 2026 `6576055`, sínteses 2026 `6346096`.
- **⚠ THE DGT DEBT LIBRARY DOES NOT RENDER THROUGH THE DLPORTLET WALK, AND ITS FILENAMES ARE STORED IN NFD.** `/web/dgt/divida-publica` is a redirect shell; every `view/{folderId}` on instance `naJgsqcf3hne` returns the same 77 kB page with zero `data-title` entries. The only route is to construct `https://www.mf.gov.cv/documents/92878/{folder}/{title}` — and **the accented title must be Unicode-normalised to NFD (decomposed) before percent-encoding.** `RELATÓRIO 4º TRIMESTRE 2025.pdf` returns **404 in FormC and 200 in FormD**, on the identical visible string. Annual reports live in `92878/4408978`, quarterlies in `92878/5069889`. **New general rule: when a Liferay download 404s on a name you read off the page, try NFD before concluding the file is absent.**
- **⚠⚠ THE `ROE 2025` IS AN IMAGE PDF AND THE `ROE 2024` WAS NOT.** 120 pages, 23.2 MB, **11 741 extractable characters** — the text layer holds `Página | 60` and paragraph numbers and nothing else, with ~50 embedded images per page carrying the body. FY2024's ROE was 101pp and **222 220 characters, fully native.** This is a year-on-year regression in machine-readability, not a fetch failure. **NEEDS OCR (`-l por`).** Only pp.119–121 (the PEDS II programme tables) return real text. **General lesson: a document series' machine-readability is not a property of the series. Probe every year's file; do not inherit last year's verdict.**
- **The rotation trap recurs in the enacted law and the de-rotation recipe is confirmed.** Mapa pages of BO n.º 125 Sup are rotated 90° and return character-reversed text (`5202otnemaçrO` = *Orçamento2025*, `acinâgrO` = *Orgânica*). **Group `extract_words()` by `round(x0/6)`, sort each group by DESCENDING `top`, reverse each token** — that recovers Mapa III at p.31 perfectly and every row cross-foots. Still native text in a rotated CTM; still not a scan; still never OCR it.
- **⚠ THE THOUSANDS SEPARATOR CHANGED.** The FY2025 standalone mapas print `16,513,484,220` with **commas**; the FY2024 mapas printed full stops; the `Conta Provisória` prints `369 781 930` with **spaces**; the Assembly's `Orçamento Privativo` prints `1.299.089.710` with full stops. **Four separators inside one country-year. Parse per table, never per country.**
- **⚠⚠ THE FINDING: THE DIGITAL VOTE WAS CUT 73,4% AND ITS CAPITAL LINE APPROPRIATED AT A PRINTED ZERO — AFTER EXECUTING A PRINTED ZERO THE YEAR BEFORE.** `Mapa III`: **`GOV - Ministerio Da Economia Digital` FY2025 = 0 (Investimento) + 342 498 843 (Finalistico) + 27 283 087 (Apoio) = 369 781 930 CVE**, against FY2024's 553 090 000 + 811 792 545 + 26 083 087 = 1 390 965 632. **Total state expenditure ROSE 13,9% over the same year, 85 948 752 206 → 97 911 339 875.** `Ministerio Da Modernização Do Estado` went 368 989 734 → **269 785 474**, its investment line also from 111 000 000 to zero. **Both digital-named ministries were appropriated zero capital for FY2025.**
- **⚠⚠ AND THEN THE CAPITAL WAS RE-CREATED IN-YEAR AND STILL NOT SPENT.** `Conta Provisória IV Trimestre 2025`, **p.56**, row `01.03.02`: **OI 369 781 930 → ORP 661 584 487 + 783 864 315 + 27 283 087 = 1 472 731 889 → EXE 8 446 342 + 524 832 801 + 24 993 247 = 558 272 390 = 37,9%.** Investment execution **1,3%**. Every cell cross-foots. The whole state ran OI 97 911 339 793 → ORP 109 150 760 055 → EXE 86 331 285 267 = **79,1%**; Modernização do Estado 60,3%. **The digital ministry is 41 points below the state average, the same outlier position it held in FY2024 at 33,0%. Two consecutive years: 553 m appropriated and nil spent, then nil appropriated, 662 m conjured by virement and 1,3% spent. The reprogrammed totals are near-identical across the two years (1 483 485 681 and 1 472 731 889) — the money is re-created annually and annually not spent.**
- **THE ORIGIN GATE IS PRINTED ON THE PAGE, pp.79–80 OF THE CONTA PROVISÓRIA.** Economia Digital `Total Orçamento` 1 472 731 889 = **772 718 949 domestic + 700 012 940 `Contribuição` (level G0)** — 47,5% external; on the execution side **526 699 056 domestic + 31 573 334 contribution**, a contribution-drawdown rate of **4,5%**. No inference required. The G0–G3 levels are contribution tiers, not programme levels.
- **⚠ THE `Mapas_Contas_4º_Trim_2025_Site.xlsx` IS THE BEST EXTRACTION TARGET IN THE COUNTRY-YEAR AND HAS NO FY2024 EQUIVALENT.** Five sheets, fully machine-readable, full floating-point precision: `Mapa I_ Receitas do Estado` (222 rows), `Mapa II_ Despesas por Economica` (156), `Mapa III_ Despesas por Organica` (57), `Mapa IV_ Despesas por Funções` (118), **`Mapa VII_ Despesas por Programa` (44) — which has no counterpart in the OE mapas set.** Header split across rows 6–7, data from row 8. **Taxa columns are stored as FRACTIONS (0.9783…), not percentages**, and Mapa I row 6 carries a live `#REF!`. Row 41 of Mapa III is the TOTAL, `97911339792.7879 → 86331285266.57616`. **Check for this file in every future CPV quarter; the FY2024 Conta Provisória folder held PDFs only.**
- **⚠ THE ASSEMBLY AMENDED THE BUDGET AND THE AMENDMENT IS FULLY IDENTIFIABLE THIS YEAR.** Proposta `Mapa3.pdf` vs enacted law p.31, same grand total `97 911 339 875`: Finalistico 62 804 123 891 → **62 932 883 689**, Apoio 18 593 731 764 → **18 464 971 966**, `OSOB - Assembleia Nacional` 1 170 329 912 → **1 299 089 710**, `Min. Finanças` Apoio 13 877 447 202 → **13 748 687 404**. **All four deltas are exactly 128 759 798 CVE: the Assembly moved that sum out of the finance ministry's administrative-support programme and into its own.** In FY2024 the equivalent shift (28 309 909 CVE) could not be located to a row. **Both digital-named ministries' rows are identical in proposal and law in both years** — so the cheap unrotated mapas are safe for those figures, but still label `budget_version: proposed`.
- **⚠ THE TWO ASSEMBLY PERIMETERS RECONCILE IN FY2025 AND DID NOT IN FY2024.** `Resolução n.º 160/X/2024` `Artigo 2.º` puts the Assembly's receitas at `1.299.089.710$00`, **matching the enacted Mapa III exactly**; in FY2024 Mapa III said 1 057 041 423 and the privativo 1 170 329 912. **Do not carry the FY2024 "two perimeters, not a contradiction" caution forward without re-checking it.**
- **THE DPA IS STILL APPROPRIATED THROUGH THE LEGISLATURE, AND GOT AN UPLIFT IN THE YEAR THE DIGITAL MINISTRY LOST 73%.** `Resolução n.º 160/X/2024`, `OUTRAS DESP. CORRENTES-ORGÃOS EXTERNOS`: **`CNPD (Comissão Nacional de Protecção de Dados)` 36.313.115 CVE** (FY2024 35.255.451, **+3,0%**), `Dotação inscrita no Orçamento do Estado 36.313.115`, no own-source revenue line; plus `Provedor de Justiça` 41.067.598, `ARC` 89.826.404, `CNE` 36.833.106 — each up ~3% on FY2024. Single-mandate carve-out applies; `scope_confidence: whole`. **The rule holds and is now two-for-two: in a state with a parliamentary *orçamento privativo*, read it.**
- **⚠ NOSi'S MONEY IS NOW FOUR TIMES THE WHOLE DIGITAL VOTE, UP FROM 73% A YEAR EARLIER.** `PAO 2025` (35pp, native, 37 150 chars, `nosi.cv/documents/20121/3002157/PAO_2025.pdf.pdf/af80ba78-…`), **p.17, header `(mCVE)` — MILHARES**: `Total 2025 **1 486 249** mCVE` vs `Previsão 2024 1 016 802`, **+46%**. Components: Housing 27 432, IaaS 67 326, PaaS 9 431, SaaS 17 085, Comunicação 13 250, Acessórios 3 112, Bundled 68 620, **`Protocolos` 333 345 (UNCHANGED to the escudo year on year)**, Outros 16 788, Consultoria/Formação/Estágio 23 226, Certificados Digitais 1 082, **`Projetos` 671 089 (+213%)**, **`Projetos Financiados` 234 465 (−13%)**. **The state's digital money has migrated out of the appropriation and into a state enterprise's trading account: the vote fell 73% while NOSi's forecast revenue rose 46%.** `Protocolos` still needs `is_transfer: true`. **⚠ STILL THE ONLY CPV ARTEFACT IN mCVE.**
- **⚠ CORRECTION TO THE FY2024 SECTION: NOSi DOES PUBLISH `Relatório e Contas`.** The FY2024 run recorded "no NOSi annual report or accounts as opposed to its forward plan". Wrong. `nosi.cv/web/guest/publicações-corporativas` carries `relatorio-e-contas-nosi-2016` … **`Relatorio & Contas NOSi 2023`** (`/documents/20121/3055160/`). **The series stops at 2023**, so 2024 and 2025 are genuinely absent — but the correct finding is "the series lapsed after 2023", not "the series does not exist". **The corporate-publications page, not the homepage, is the enumerable index; the homepage exposes none of it.**
- **NO RECTIFICATIVE BUDGET FOR 2025, AND THIS IS THE COUNTRY'S NORMAL MECHANISM.** No rectificative law for 2025 exists in any year folder or anywhere else; **Cabo Verde passed one for 2026 (presented by PM Francisco Carvalho 29-07-2026, approved 31-07-2026 "sem aumentar a despesa pública") and one for 2026 only.** The FY2025 revision ran entirely through the monthly *alterações orçamentais*, which is why ORP exceeds OI by **11,5%** with no statute behind it. **In Cabo Verde the revised stage is a virement register, not a law — do not record "no revised stage" for a year with no rectificativo.**
- **ALL TWELVE MONTHS OF `Alterações Orçamentais` ARE PUBLISHED FOR 2025** (FY2024 was missing April), and **October and November are three to five times any other month**: janeiro 1 362 rows/126 cabimentos, fevereiro 1 840/190, março 2 133/187, abril 1 865/199, maio 2 104/240, junho 2 789/286, julho 2 600/287, agosto 2 286/249, setembro 3 362/349, **outubro 8 072/722, novembro 10 967/980**, dezembro 6 210/451 — 45 590 rows in the year. **The 661 584 487 CVE of in-year digital investment and the state's whole 11,5% ORP uplift are in those two months.** Structure unchanged from FY2024: sheet `Alterações Orçamentais.rdl`, header at row 8, `TESOURO`/`DONATIVO` × `ANULAÇÃO`/`REFORÇO`, detail rows carrying `NATUREZA`, **`FINANCIADOR`** (e.g. `TESOURO/RECEITAS INTERNAS`, `F.I.D.A./EMPRESTIMO EXTERNO`) and `RÚBRICA CLASSIF. ECONÓMICA`. Not cumulative.
- **The `Anexo Informativo` is again native-but-sparse (89pp, 39 114 chars) — `extract_tables`, not `extract_text`.** Same for the `Relatório IPSAS` (18pp, 10 499). **The `Síntese Informativa da Execução` is again a slide deck whose numbers are inside images (15pp, 1 252 chars)** — but the Conta Provisória and its XLSX carry the same ground at better grain, so OCR here is probably not worth it. **The `Síntese` filenames are again inconsistent month to month; enumerate the folder, never construct them.**
- **The `Diretrizes do OE 2025` (95pp, 203 290 chars, native) is now the package's richest narrative artefact**, the ROE having gone to images. Cover dateline `Abril 2024`, file created 2024-07-30. Ceilings, not appropriations. **Its 19-page companion deck sets the first-page title as vertical single characters (`D I R E T R I Z E S`), so a naive first-page title read fails.**
- **The audit institution has now missed two consecutive years.** `tribunalcontas.cv/parecer-da-conta-geral-do-estado-2025` **and `-2024` both 404** as at 2026-08-03; the series still ends at `PCGE_2023_FINAL.pdf`. Its `relatórios de auditoria` and `relatórios de acompanhamento da execução orçamental` landing pages carry **only `-2023` year links**. **No audit instrument of any kind covers FY2024 or FY2025, and no audit of any digital or systems procurement exists for any year.** The FY2024 run called the parecer "not yet rather than overdue"; a year on, that is getting harder to say.
- **CNPD published no `Plano de Atividades` for 2025** — the series runs 2017–2024 and stops — **and the mislabelling trap is confirmed unchanged**: every link under `/relatorio-de-atividades/` for 2017–2023 still points at `CNPD-Plano-de-Atividades-{year}.pdf`; only 2015 and 2016 have genuine `Relatorio` filenames. **The authority appears to have published no activity report since 2016.**
- **Unchanged from FY2024, re-verified:** `med.gov.cv` is still the 1 096-byte `WEBSITE EM CONSTRUÇÃO` placeholder — **the digital ministry has no publication channel of its own in the year its vote fell 73%**; `arme.cv` still resolves on Cloudflare DoH to 41.221.192.154 and still times out on TCP 443 and 80 (`curl --resolve` → `000`); ARAP publishes no `orçamento` after 2021 and no `conta de gerência` at all, and its PAA 2025 is again a **4-page scan with zero extractable text**; `ecompras.gov.cv` still carries no government-wide procurement plan; `mf.gov.cv` still does not mirror the IMF.
- **A ministerial forecast the enacted law falsified, worth holding for the pattern.** On 31 August 2024 the Vice-PM and Finance Minister put OE2025 at *"cerca de 92 milhões de contos, um crescimento de cerca de 7 ou 8% em relação ao orçamento de 2024"*. The enacted total is **97 911 339 875 CVE, +13,9%** — six points and six billion escudos out. **Pre-tabling ministerial aggregates in Cabo Verde are indicative, not the appropriation; never record one as a budget figure.**
- **⚠ A MULTI-YEAR ENVELOPE THAT DOES NOT CONVERT INTO ITSELF.** 10 March 2026, the same minister: *"praticamente 100 milhões de euros (cerca de 10 milhões de contos)"* for digital "nos próximos anos". **At the escudo's euro peg 100 m EUR is ~11,0 bn CVE, not 10 bn.** Carry it in EUR as announced, with the CVE figure recorded as the speaker's own rounding, and record neither as an appropriation. **The acquirable unit beneath it is the annual OE line — which this collection now holds for two consecutive years, and which shows the digital vote falling by three quarters, not rising.**
- **Identity, data exchange and statistics — searched by name, absent at every published grain, third year running.** Nothing for *registo civil* / CRVS, *bilhete de identidade*, biometric enrolment, ABIS, passport system, voter register, social registry, interoperability layer, service bus or single window in `Mapa III`, `Mapa IV`, `Mapa VII` or the FSA mapas. The vehicles were *delivered* in this window — NOSi formally handed the `Sistema de Informação da Justiça` to the justice ministry on 17-03-2026, `Portal GOV.CV` launched 02-2026, `Balcão Único do Paul` 08-2025, the national SOC and CSIRT 30-10-2025 — **and not one of them has a separable domestic appropriation, because NOSi builds them under protocol on World Bank credit.**
- **New national press source admitted:** `noticiasdonorte.publ.cv` — Notícias do Norte, named bylines, dated first-hand parliamentary reporting, its own WordPress REST API at `/wp-json/wp/v2/posts`. **`governo.cv` and `noticiasdonorte.publ.cv` both expose the WP REST API, which returns title, date, link and the full `content.rendered` in one call** — the cheap way to stage CPV prose verbatim without a page fetch.
- **Non-yields, so a future CPV run can stop spending its cap:** `parlamento.cv` (still an AngularJS SPA; initiative lists render client-side and no OE2025 document was reachable), `ine.cv` (SPA stub), `ecompras.gov.cv`, ARAP's `orçamento` and `conta de gerência` pages, the CNPD's post-2024 publications, and any IMF document on `mf.gov.cv`.
### Cabo Verde FY2026 — the Liferay walk was paginating at 30 files all along, the identity and universal-service money is in a table nobody had read, and the appropriation has stopped describing the spend (sweep, 2026-08-03/04, FY2026)

*(Third CPV run. The FY2024 section holds the reconnaissance; the FY2025 section holds the folder-shape and image-PDF findings. This section records what FY2026 changed or added, and **corrects a method error that ran through both earlier runs**.)*

- **⚠⚠ THE FILE-PAGINATION PARAMETER ON THE `mf.gov.cv` DLPortlet IS `_deltaEntry`, NOT `_delta`. `_delta` paginates FOLDERS.** Both earlier CPV runs used `_delta=200`, got back `Exibindo 1 - 30 de 47 resultados`, and recorded the first 30 entries as the complete listing. **Two stated absences in the earlier sections are therefore wrong:** the FY2024 note that the mapas set *"stopped at `Mapa6.10` with no `Mapa6` total"*, and the FY2025 note that `Mapa VII_ Despesas por Programa` *"has no counterpart in the OE mapas set"*. `Mapa6.16 Total` and `Mapa7.pdf` both exist. **General rule: read the `pagination-results` div (`Exibindo 1 - N de M resultados`) before concluding that any Liferay document library is exhausted, and treat a listing that ends on a round number as paginated until proved otherwise.** Correct call: `…_DLPortlet_INSTANCE_{instance}_deltaEntry=75`.
- **⚠ THE ROTATION TRAP IS ABSENT FROM THE FY2026 LAW. DO NOT APPLY THE DE-ROTATION RECIPE TO IT.** `Lei n.º 69/X/2025` (BO I Série n.º 133, 1.º Suplemento, 31-12-2025; 266pp, **594 563 chars NATIVE**) prints `Mapa I`–`Mapa XV` at PDF pp.169–266 **upright and in normal reading order**. Only the BO spine text in the page margin is reversed (`5202/X/96 º.n ieL`). FY2024 and FY2025 were both rotated. **Three years, three different renderings — probe each year's file, never inherit the verdict.** `Mapa III` (the vote table) is PDF p.178 = BO Pág. 179.
- **⚠ THE MAPAS FOLDER SHAPE CHANGED AGAIN — 47 individual PDFs.** FY2024 shipped ~30 individual files, FY2025 shipped one ZIP (`ULTIMO_MAPAS_Oficial.zip`), FY2026 ships 47 separate PDFs in folder **`5892446`** under OE-2026 folder **`5793427`**. New this year: **`Mapa16 Clima por Organica`** and **`Mapa17 Clima por Pilar e Programa`**. **Enumerate every run; the layout has never repeated.**
- **⚠ FILENAMES ARE A MIX OF NFC AND NFD ON THE SAME SERVER, IN THE SAME FOLDER.** The FY2025 run recorded NFD for the DGT library; it is broader than that. In the OE-2026 folder, `Relatório de Despesas Climáticas…` resolves on **FormD** and `Justificação dos Beneficios Fiscais_VF.pdf` on **FormC**; all six `Alterações Orçamentais` files are **FormC**. **Try FormD then FormC on every accented name** — one loop, two attempts, no thought required.
- **⚠ THE `ROE` IS AN IMAGE PDF FOR THE SECOND CONSECUTIVE YEAR — this is now settled practice, not a transient regression.** `ROE 2024` 101pp / 222 220 chars native; `ROE 2025` 120pp / 11 741; **`ROE 2026` 129pp / 9 495**. Budget the OCR (`-l por`); do not probe hopefully. **Much of the ROE narrative is duplicated inside the enacted law at BO pp.100–168, which IS native — prefer the law and OCR the ROE only for what the law omits.**
- **⚠ AND THE SÍNTESE SERIES WENT THE OTHER WAY — IT IS NATIVE NOW.** `Síntese Informativa da Execução` was 2 385 chars (Dec 2024) and 1 252 (Dec 2025), an image deck both years; **Maio 2026 is 14pp / 26 252 chars native.** A future run must probe rather than inherit either verdict.
- **⚠ THE PROPOSTA DE LEI IS A `.docx` THIS YEAR**, not a PDF (919 kB, folder `5793427`). Extract with `python-docx` or `pandoc`. The library also serves a `.docx.pdf` derivative at the same path.
- **THREE NEW BUDGET INSTRUMENTS WITH NO FY2024 OR FY2025 EQUIVALENT:** `Justificação dos Benefícios Fiscais` (22pp, 48 927 chars native — **tax expenditure, never to be recorded as an appropriation**, but it quantifies relief granted to `Tecnologias de Informação`, the `Zona Económica Especial para Tecnologias (ZEET)`, digital terrestrial television and data-centre/computer/tablet imports); `Relatório de Despesas Climáticas` (16pp, **1 620 chars — images, needs OCR**); and `Orçamento Cidadão 2026` (44pp, 56 678 chars native — **corroboration and narrative only, supports no finance record**).

- **⚠⚠ THE FINDING THAT OVERTURNS THREE RUNS' WORTH OF NIL RESULTS: THE IDENTITY AND UNIVERSAL-SERVICE MONEY IS IN THE `RECEITAS CONSIGNADAS` TABLE, NOT IN ANY MAPA.** The FY2024 and FY2025 sections both record, in terms, that no identity, CRVS, data-exchange or universal-service line appears "at any published grain", and generalise it to a regional pattern with Comoros and Congo. **That was true of `Mapa III`, `Mapa IV` and the FSA mapas and false of the law.** `Lei n.º 69/X/2025`, **BO p.137**, section 4, `RECEITAS CONSIGNADAS E RESPECTIVAS CONTRAPARTIDAS EM DESPESAS` (mandated by `Lei n.º 55/IX/2019` art.36 h)), **total 9 432 867 410 CVE**, carries:
  - **`Taxa pela emissão e substituição dos documentos de identificação civil` → `Sistema Nacional de Identificação Civil — SNIAC` 306 516 802 CVE**, split `Passaporte Eletrónico — PEC` **141 524 912**, `Cartão Nacional de Identificação — CNI` **109 383 546**, `Título de Residência de Estrangeiros — TRE` **22 500 000**, `Instituto Modernização e Inovação da Justiça` **33 108 344**. Cross-foots exactly. Revenue side visible in `Mapa I` as `01.04.02.02.01.00.01 — Taxa de serviços de passaportes 493 959 710`.
  - **`Contribuição das Operadoras de Comunicações e Taxa de Espetro Radioelétrico` → `Fundo de Serviço Universal e Desenvolvimento da Sociedade de Informação (FUSI)` 122 073 633 CVE.** **THE UNIVERSAL SERVICE FUND, which all three CPV runs had searched for and two had recorded as absent.** Block 6 is closed for Cabo Verde.
  - **`Taxa de Serviços Casa Cidadão` 74 050 000 → `Qualidade Prestação de Serviço` 49 850 000 and `Implementação Novas Infraestruturas Tecnológicas` 24 200 000** (and `Espaço Cidadão — Comunidade Integrada` and `Implementação Balcão Único`, both printed with no figure). The one-stop-shop programme, funded by its own service fee.
  - `Fundo de Modernização da Justiça` 180 000 000; `Programa da Cidadania Fiscal` 48 074 473.
  - **NEW GENERAL RULE, and it is the twin of the FY2024 "read the parliamentary *orçamento privativo*" rule: in a Lusophone state whose budget framework law mandates an annex of `receitas consignadas e respectivas contrapartidas em despesas`, READ THAT TABLE. Earmarked-fee financing is where DPI, regulators, universal-service funds and one-stop-shops are paid for, and it is invisible to the organic, functional and economic classifications alike.** **RE-READ TRIGGER on documents already held: section 4 of the FY2024 and FY2025 CPV laws, to establish whether SNIAC and FUSI existed in those years and at what figures. That is an extraction-pass job, not an acquisition.**
  - **⚠ BO p.137 renders with letter-spacing (`R E C E IT A S`) and interleaves some row labels with their figures** (`documentos de identificação3 c0i6v i5l16 802`). Every digit is present and the block cross-foots; de-interleave by x-position rather than trusting `extract_text` line order.
- **⚠ ORIGIN GATE ON THE IDENTITY LINES — BOTH THINGS ARE TRUE AT ONCE.** The SNIAC programme is **domestically appropriated through an earmarked fee** *and* **externally co-financed by the EU's GESTDOC project (5 million EUR via Camões IP)**. Record the SNIAC lines as `origin: state`; do not attribute the EU money to the fisc; do not let the co-financing disqualify the domestic line. Production moved from the Casa da Moeda de Portugal to the INCV's own *Gráfica de Segurança* on 18 May 2026.
- **A FIRST-EVER CYBERSECURITY BUDGET UNIT.** The law's narrative (BO p.126) records *"inscrições de unidade orçamental: 'Ciber Segurança' com 20 milhões de CVE"* under function `Serviços Públicos Gerais`. Both earlier runs recorded no cybersecurity line at any grain and located the money inside NOSi. **20 million CVE is small; a named budget unit is a categorically different governance fact from a line in a state enterprise's trading account.**

- **⚠⚠ THE HEADLINE OF THE THREE-YEAR CPV SERIES: THE APPROPRIATION HAS STOPPED DESCRIBING THE SPEND.** `Ministério da Economia Digital`, code `01.03.02`:

  | | FY2024 | FY2025 | FY2026 (at Q1) |
  |---|--:|--:|--:|
  | Appropriated (OI) | 1 390 965 632 | 369 781 930 | **174 200 533** |
  | — of which investment | 553 090 000 | **0** | **0** |
  | **Reprogrammed (ORP)** | **1 483 485 681** | **1 472 731 889** | **1 614 624 282** |
  | — of which investment | 553 090 000 | 661 584 487 | **653 127 161** |
  | Executed | 489 920 474 | 558 272 390 | 163 063 219 (Q1) |
  | Rate | 33,0% | 37,9% | 10,1% (Q1) |

  **The appropriation fell 87,5% in two years; the reprogrammed budget did not move.** By 31 March 2026 the ministry's budget is **9,3× what the Assembly voted it**, with 653 127 161 CVE of investment in existence that the budget law recorded as a printed zero. **In Cabo Verde the virement register is the budget for digital, and `Mapa III` is not. Any CPV digital-spend figure sourced from the appropriation alone is wrong by roughly an order of magnitude, and the direction of the error is not stable year to year.** State-wide at Q1 2026: OI 95 675 087 738 → ORP 102 678 336 652 (+7,3%) → EXE 19 117 570 518 = 18,62%.
- **The proposta and the law diverge on the digital ministry for the first time.** FY2024 and FY2025: the ministry's three cells were identical in both versions. **FY2026: proposta 175 523 533, enacted 174 200 533, Δ −1 323 000, all of it in `Apoio Administrativo`.** Grand total unchanged at 95 675 087 736 in both. **Never take this ministry's FY2026 figure from `Mapa3.pdf`.** Also moved between tabling and enactment: `OSOB - Comissão Nacional De Eleições` (46 300 000) appears in the enacted `Mapa III` and is absent from the proposta — **it sat in the Assembly's *orçamento privativo* in FY2024 and FY2025, so check where the CNPD sits this year rather than assuming.**
- **NEITHER DIGITAL-NAMED MINISTRY HAS ANY AUTONOMOUS SERVICE OR FUND.** The fifteen ministries with FSA in `Mapa V`/`Mapa VI` are MAPMJD, MF, MFIDS, MDN, MPIFE, MAI, MJ, ME, MS, MCIC, MTT, MM, MAA, MICE, MIOTH. Economia Digital and Modernização do Estado appear in neither. **Their votes are the whole of their money — no own-source revenue anywhere.**
- **⚠ THE `Mapas_Contas_{n}º_Trim_{year}_Site.xlsx` SERIES IS CONFIRMED AND RECURRING.** The FY2025 run found it for Q4 2025 and flagged it as possibly one-off; **Q1 2026 has it too.** Five sheets, fully machine-readable, full floating-point precision: `Mapa I_ Receitas do Estado` (219r), `Mapa II_ Despesas por Economica` (213r), **`Mapa III_ Despesas por Organica` (58r)**, `Mapa IV_ Despesas por Funções` (123r), `Mapa VII_ Despesas por Programa` (52r). **Header split rows 6–7, data from row 8; taxa columns stored as FRACTIONS not percentages; the digital ministry is row 22 and its label carries a double space (`GOV -  Ministerio…`); row 42 is the TOTAL.** **Check for this file in every future CPV quarter — it beats every PDF in the country-year.**
- **⚠ THE `Alterações Orçamentais` COLUMN COUNT VARIES BY MONTH — 21 in January and April 2026, 24 in February, March, May and June. Do not hard-code a column index across the series.** Row structure and the per-row `FINANCIADOR` under `TESOURO`/`DONATIVO` × `ANULAÇÃO`/`REFORÇO` are unchanged from FY2024/25. 16 712 rows over six months, the same running rate as FY2025's 45 590 over twelve.
- **⚠ THE EXECUTION DECREE MISSED ITS OWN STATUTORY DEADLINE.** `Lei n.º 55/IX/2019` requires it by 31 December of the preceding year. `Decreto-Lei n.º 1/2026` is dated **9 January 2026** (BO n.º 3, bulletin id `23881`, act id `89290`; 64pp, 125 069 chars native). FY2024's was 3 January, FY2025's was 31 December — one of three on time. **Its `Artigo 2.º` makes the `Plataforma Eletrónica da Contratação Pública` mandatory for all goods and services acquisition from 2026, and its `Artigo 46.º` makes `SIGOF` mandatory for the sovereign organs.** Both are data-governance mandates carried by a fiscal instrument.
- **`boe.incv.cv/Bulletins/DownloadAct?id={actId}` serves a single act as its own PDF**, which is cleaner than the whole-bulletin route (`/Bulletins/Download/{bulletinId}`) recorded in the FY2024 section. Act pages are at `/Bulletins/View/{actId}`.

- **⚠ CABO VERDE PASSED A RECTIFICATIVE BUDGET FOR 2026 — THE FIRST IN THE THREE YEARS SWEPT — AND IT IS NOT YET PUBLISHED.** The FY2024 and FY2025 sections both record that the country's normal revision mechanism is the monthly virement register, not a statute. **FY2026 breaks that, and the cause is a change of government:** legislative elections 17 May 2026, PAICV absolute majority, **Francisco Carvalho's government took office 19 June 2026** replacing Ulisses Correia e Silva's MpD administration, which had drafted and enacted the OE 2026. The rectificativo was presented 29 July and approved 30–31 July 2026 (37 PAICV for, 28 MpD against, 2 UCID abstentions). **OE 2026 voted at 95 675 million CVE; projected execution found on taking office at 104 011 million; rectificativo sets 103 888 million (−123 million, −0,1%).** As at 2026-08-04 it is **in neither the Boletim Oficial nor the ministry library** — a timing gap, not an absence. **It will carry the first statutory revised `Mapa III` this country has produced in the in-scope period.**
- **⚠ THE FY2026 VOLUME DOES NOT CLOSE THE FY2025 REVISED STAGE, AND IT CANNOT.** It prints FY2025 exactly twice, both as the original appropriation: `Anexo Informativo` p.57, functional table, columns **`2023 CGE | 2024 CGE | 2025 OE | 2026 OE`** *(em milhões de CVE)*; and p.71, treasury table, columns **`Execução 2023 | Execução 2024 | Estimativa 2025 | Previsão 2026`**. The law's 168-page narrative uses "OE 2025" (13×) and "a estimativa do OE 2025" throughout, and **contains zero occurrences of `retificativ`, `rectificativ`, `retificado`, `revisto` or `execução 2025`.** **This confirms the FY2025 run rather than superseding it: Cabo Verde passed no FY2025 rectificativo, so the FY2026 comparator column is the FY2025 appropriation.** FY2025's revised position remains carried by the `Conta Provisória IV Trimestre 2025` ORP column (109 150 760 055) and the twelve monthly virement files, both already held. **Nothing further is acquirable for that stage; do not raise one.**
- **⚠ THE COMPARATOR-COLUMN RULE NEEDS A QUALIFICATION.** `COUNTRY-BUDGET-BATCH.md` holds that a year's revised stage is often only in the next year's volume as the comparator column. **In a state whose revision mechanism is administrative rather than statutory, the next year's volume prints the prior year's *appropriation*, not its revised position — because no revised statute exists to print.** Cabo Verde is that case, three years running. **The instrument that carries the revised position in such a state is the fourth-quarter provisional account's ORP column, not the following budget.**
- **The head of government has now said in public what the virement files show.** Presenting the rectificativo, PM Francisco Carvalho put the drift between the voted 95 675 m and projected execution at **+8 336 m**; the Q1 2026 ORP of 102 678 m is that same drift measured three months earlier by the ministry's own account. The opposition's counter-claim (UCID: the rectificativo *increases* spending by more than eight million contos; PAICV: the previous government "exhausted allocations during the election period") is an argument about exactly the appropriation-versus-reprogramming gap this dataset measures.

- **Non-yields, so a future CPV run can stop spending its cap:** the **DGT public-debt library** (`92878/5069889` and `92878/4408978`) — it does **not** render through the DLPortlet walk and **`_deltaEntry` does not fix it**; all three folder ids return the same ~77 kB shell with zero `data-title` entries, and no FY2026 quarterly report resolves under the FY2025 name pattern. **`arme.cv` was not re-probed** — two runs have established that it resolves (41.221.192.154, both public resolvers) and times out on TCP 443 and 80, and a third identical probe would establish nothing. Also still nil: `med.gov.cv` (never built, since 2022); ARAP's `orçamento` (nothing after 2021) and `conta de gerência` (nothing ever); any government-wide procurement plan; the CNPD's post-2024 publications; any NOSi `Relatório e Contas` after 2023; any INE budget; any IMF document mirrored on `mf.gov.cv`, three years running. **The Tribunal de Contas has now published no `parecer`, no `relatório de auditoria` and no `relatório de acompanhamento` covering any year after 2023 — three consecutive unaudited accounts, and no audit of any digital or systems procurement for any year.**
- **`balai.cv` returns HTTP 403 to a local fetch even with a browser UA**, and `inforpress.cv` exposes no WP REST API and its on-site search returns nothing. `inforpress.cv` article pages themselves fetch cleanly. **`governo.cv`'s WP REST API remains the cheapest CPV prose route** — `?search=…&_fields=id,date,link,title` for triage, then `?slug=…&_fields=date,link,title,content` for the verbatim body, written to disk without the model reading it.

### Ghana FY2026 — the three PBB volumes that settle what the Act could not (extract, 2026-08-09)

**Follows the 2026-08-05 Ghana entry above, which recorded the split between the Data Protection Commission, the Cyber Security Authority and NITA as "not established" and named the OGM `00110 Information Management` line as the largest unresolved candidate in the budget. Both are now settled.**

- **Documents:** `2026-PBB-MOCD.pdf` (103 pp, image-only), `2026-PBB-OGM.pdf` (117 pp, image-only), `2026-PBB-MLGCRA.pdf` (195 pp, **native throughout, financial tables included**). All three read at table 1.5, *Appropriation Bill — Summary of Expenditure by Sub-Programme, Economic Item and Funding*. Method and traps are in the strategy library under archetype S.
- **THE HEADLINE — Ghana's data-protection authority receives no treasury money at all.** Programme `02603` breaks into five sub-programmes: `02603001 ICT Infrastructure and Regulation` (NITA) **GHS 674,745,448**, `02603003 Cyber Security and Regulations` (CSA) **GHS 25,346,198**, `02603002 ICT Capacity Development` (GI-KACE) **GHS 17,308,560**, `02603005 Data Management and Regulation` (**the Data Protection Commission**) **GHS 9,720,400 with every GoG column blank**, and `02603004 Domain Management and Regulation` (GDNR) **GHS 2,827,244 with no compensation of employees at all**. The volume says it in terms: *"The Commission is funded through internally generated funds."* The DPC is 1.3% of the programme it sits in and 0.77% of the ministry's vote.
- **The whole of the ministry's donor money — GHS 138,000,000 — lands on one sub-programme**, `02603001`, and the same sub-programme carries GHS 494,258,679 of internally generated funds. That is what a regulator's fee income looks like, and it is where the National Communications Authority is: **the volume describes NCA, GIFEC and Ghana Digital Centres as sub-programmes of 02603 and appropriates none of them a code**, so the split between NITA and the NCA is still not established. Programme 1 has the same problem: *Digital Technology (DTD)* and *Innovations* are described and unfunded.
- **`00110 Information Management` is government communications, not government IT.** The OGM volume splits its GHS 273,682,461 into `00110001 Electronic Media Services` GHS 133,446,287 and `00110002 Information Gathering and Dissemination Services` GHS 140,236,174. **No record built**, and a GHS 273.7m candidate is removed from the Ghanaian digital total for good. That negative is the whole return on the OGM acquisition and it was worth it.
- **Births and deaths registration is unfunded for a second year.** MLGCRA's programme structure names `P4. Births and Deaths Registration`, its narrative reports 432,925 births registered in 2025 and the CRVS strategic plan 2025–2030, and table 1.5 carries no code for it — the codes run 01101, 01102, 01103, 01104, then jump to 01107. Neither does Act 1163.
- **Where they hid:** `01109004 Spatial Planning` (GHS 36,454,968) is LUSPA redeveloping **LUPMIS** into a web-based platform for spatial planning, development control and street addressing, with a GIZ-supported workshop on data sharing and interoperability — none of which the label says. `01101004 Research, Statistics and Information Management` (GHS 500,000) is the ministry's databank, website and *"Digitalisation of processes (e-leave, e-memo, vehicle request)"*.
- **⚠ The sub-programme code moved and the line did not.** MLGCRA's spatial-planning money was `01109001 Human Settlements and Land Use Reaseach and Policy` in FY2024 and is `01109004 Spatial Planning` in FY2026. **Join the series on the programme code.**
- **⚠ A PBB volume does not always tie to the Act.** MOCD and MLGCRA reproduce Act 1163's MDA lines to the cedi; **OGM does not** — its `00105 Investment Promotion Management` is GHS 1,655,667 short on internally generated funds and its MDA total differs by exactly that. Two of three tie, so this is an amendment during passage, not a misread; it touches no digital line and no contradiction is filed.
- **Grain.** The five sub-programme records **replace** the held programme-grain record `gha-2026-026-02603`, which is retired (they sum to its GHS 591,947,850 domestic total exactly). `gha-2026-026-02602` **stays at programme grain**: its single sub-programme `02602000` carries the identical GHS 100,000,000, so the finer level is the same line and a rename would churn citations for nothing.
- **Didn't work:** OCR on the money tables. At 300 dpi it drops whole cells out of a fifteen-column table and returns a plausible partial row. The figures came off a 350 dpi render read directly; the OCR sidecars are committed for the narrative, which they handle cleanly.

### Zimbabwe FY2026 — a programme-grain Act for all 42 votes, and a regulator that is not in it (extract, 2026-08-09)

**FY is the calendar year.** First Zimbabwean budget documents extracted; the wiki previously held no ZWE `domestic-state` record.

- **Documents:** `Appropriation (2026) Act, 2025 (Act No. 6 of 2025)` (Government Gazette Extraordinary 95, via Veritas, native), the **2026 National Budget Statement** (323 pp, native) and the **2026 National Budget Speech** (38 pp, native). The Act is archetype B and is the record instrument; the Statement is the narrative and the only place any figure is broken below vote level.
- **Structure:** the Act's Schedule runs `Designation | Consolidated Revenue Fund | Retention Funds | Total`, one block per vote, programmes as Roman numerals with no numeric code. 42 votes, ~100 programmes, eight pages. **Read it with geometry** — the Total column is a separate text stack — and it then cross-foots vote by vote.
- **Digital lines found under:** Vote 23 Programme II *Information Communication Technology Development and Promotion* **ZiG505,225,000** (`whole`) and Programme I *Policy and Administration* ZiG258,292,000 (`partial` — the same ministry carries postal and courier services); Vote 18 Programme II *Civil Registration* **ZiG1,470,460,000** and Programme V *Migration Management* ZiG994,652,000 (both `partial`); and, from the Statement's Table 41, **ZIMRA *Automation* ZiG200,000,000** at `proposed`.
- **Where they hid:** the largest identity line in the budget is **Civil Registration**, three times the ICT ministry's own digital programme, and no keyword reaches it. The Statement's para 581 confirms the purpose — *"ZiG1.5 billion to capacitate the Civil Registry Department … to facilitate the issuance of IDs, birth certificates and other essential documents"* — and para 582 does the same for Migration Management and the **Online Border Management System**.
- **Looked for and not found:** **POTRAZ**, the sector regulator and the country's data protection authority under the Cyber and Data Protection Act, has **no appropriation in the Act at any grain** — it is levy-funded and sits outside the vote structure entirely. No universal service fund appears either. Vote 20 *Information, Publicity and Broadcasting Services* (ZiG463,132,000) is where the **ZimDigital Phase 2** analogue-to-digital migration is funded, and the Act publishes no programme line for it, so the digital share is **not established**. Vote 30's public-service modernisation — payroll digitisation, biometric proof-of-life for pensioners — is described in the Statement and carries no line of its own.
- **False positives avoided:** Vote 16 Programme III *Innovation, Science and Technology Development for Industrialisation and Modernisation* (ZiG717,634,000) is science and innovation, funding university innovation hubs and agro-industrial parks; not recorded. Vote 36 *Management of Elections and Referendums* names no digital system.
- **Outturn available?** Not for FY2026. The Statement's **Table 21** gives FY2025 budget utilisation to 30 September at **vote grain** — Vote 23: ZiG240m of ZiG741m, **32%**, or 43% adjusted for the exchange-rate outturn, against an all-MDA average of 56%. Vote grain is an envelope, so it supports no record; it belongs on the place hub as a dated statement.
- **⚠ Two arithmetic defects in the Act, both outside the digital lines.** Vote 6 (Auditor General) prints a Vote Total of 764,373,000 against programme lines summing to 794,373,000; the **grand total agrees with the programme lines**, so the Vote Total is the misprint — but the Budget Statement's Table 33 and the Speech both carry 764.4. Vote 7's Total column prints 104,555,000 where its Consolidated Revenue Fund column prints 134,555,000, and the CRF column is the one that cross-foots. 41 of 42 votes cross-foot exactly.
- **Statement against Act.** Table 33's vote allocations agree with the Act on every digital vote (23, 18, 20, 16) and disagree on votes 1, 2 and 5. Since no digital line is affected, this is recorded and not chased.
- **Didn't work:** there is no priced project list. The Statement names National Data Centre consolidation to Tier 4, government WAN modernisation, an ICT Lab per School scoping exercise over 300 schools, Community Information Centres, a Smart Government Communications suite at 174 health institutions and the National AI Strategy 2026–2030 — and prices **none** of them. The **Estimates of Expenditure (Blue Book)**, which the Act incorporates by reference, is the instrument that would, and it is not held.

### Namibia FY2026/27 — a three-page Act, and the whole of what a vote-total schedule can yield (extract, 2026-08-09)

- **Document:** `Appropriation Act, 2026 (Act No. 1 of 2026)`, Government Gazette 8930, three pages, via the Legal Assistance Centre. Signed 21 May 2026, gazetted 27 May 2026, for the year ending 31 March 2027.
- **Structure:** `VOTE NO. | TITLE | APPROPRIATION AMOUNTS N$'000`. Twenty-nine votes, N$87,928,148 thousand, cross-footing to the printed total exactly. **Nothing below the vote.**
- **Result: no records.** Vote 29 *Information and Communication Technology* is **N$682,000 thousand — 0.78% of the national appropriation** — and it is a ministry envelope, so the driver's envelope rule bars it. No other vote is a single-mandate digital body. **This country-year yields a stated absence, not a total**, and that is the honest outcome rather than a failed extraction.
- **⚠ Extraction trap:** the Schedule's three columns are three independent PDF text streams and a plain `pdftotext -layout` dump pairs each amount with the **following** vote. Bind by geometry and anchor on vote 09 Finance = 12,877,000.
- **Wanted:** the *Estimates of Revenue, Income and Expenditure* for the year ending 31 March 2027, which is where Namibia publishes programme and activity detail, and the ICT minister's committee-stage motivation speech — the press reported a N$78m tower rollout, N$17.4m cybersecurity and N$452.1m multimedia from it, and none of that is in any document the wiki holds. Both on the acquisition list.

### Mozambique FY2026 — the mapas are the estimates volume, and the digital ministry's capital budget is entirely external (extract, 2026-08-09)

**FY is the calendar year.** First Mozambican budget documents extracted; the wiki previously held no MOZ `domestic-state` record. Structure and extraction method are in the strategy library under **archetype T**.

- **Documents:** the *Proposta de Lei do PESOE 2026* (articulado and fundamentação, 11 pp) and the **thirteen `mapas finais` A–M**, all native. The proposta carries the national envelope and nothing below it; the mapas carry every spending unit.
- **Structure:** SISTAFE organic classification only — **no programme axis anywhere**. `Código | Descrição | eleven economic natures | Total` on the funcionamento mapas (E/F/G), `Código | Descrição | Interno | Externo | Total` on the investment mapas (H/I/J). Scale `10^3 MT`, printed.
- **THE HEADLINE — the Ministério das Comunicações e Transformação Digital's whole investment budget is externally financed.** Mapa H prints `52A000141` as **Interno 0,00 | Externo 2.637.800,00**: MZN 2.64 billion of capital, none of it Mozambican money, against a national central average of 14.8% domestic (Interno 12,490,189.89 of 84,224,019.76 in 10³ MT). Adding the ministry's operating budget of MZN 111,260,610, **4.0% of what the ministry will spend in 2026 comes from the state's own resources.** Under the origin gate the external capital is `non-state` and, the mapa naming no funder beyond *Externo*, it fails the spec's first fact and builds no record.
- **THE SECOND FINDING — the largest domestically-financed digital line is not in the digital ministry.** **CEDSIF**, the finance ministry's information-systems development centre (`27A001141`), takes MZN 657,832,010 operating plus MZN 100,000,000 investment, **all domestic** — nearly seven times the digital ministry's own operating budget and more than the whole of sector 52 put together (MZN 418,061,140). Two units of one state at opposite ends of the same column.
- **Digital lines found under:** sector 52 — `52A004041` **INAGE** (national e-government institute) MZN 93,280,160 and `52A001641` **INTIC** MZN 73,636,370, both `whole` single-mandate bodies, and `52A000141` the ministry itself, `partial`; sector 27 — `27A001141` **CEDSIF**, `whole`; sector 17 — `17A002741` **Direcção Nacional de Identificação Civil** MZN 230,819,650, `whole`; sector 26 — `26A000541` **Instituto Nacional de Estatística** MZN 211,296,440, `whole`.
- **⚠ The central line is half the institution.** INE's eleven provincial delegations total MZN 212,543,130 — **more than the national body** — and the identification directorate's eleven provincial services add MZN 19,950,060. They are deconcentrated units, so they are stated on the records rather than held as twenty-two more, but a reader who takes the central figure as the institution's budget is out by half. **And the delegations are coded under a different sector prefix from the body**: INE is `26A000541` and its delegations are `27B003041`…`27L003041`.
- **Looked for and not found:** **INCM**, the communications regulator, appears in **no mapa** — it is self-funded and outside the state budget entirely, as is any universal-access fund. No data-protection authority appears anywhere. Neither absence is visible from any classification; both had to be established by reading all 231 central and 664 provincial unit names.
- **Not recorded, and why:** `52A001241` Instituto Nacional de Meteorologia (MZN 80,592,000) and `52A004841` a polytechnic (MZN 13,134,400) sit under the digital ministry and are not digital activities; `52A001741` *Centro de Investigação e Transferência de Tecnologias* (MZN 46,157,600) is a subordinate unit of the same ministry whose mapa name is **truncated by the document** and whose mandate is not established — recorded here rather than built into an entity slug from a half-name; `45A003041` Fundo de Desenvolvimento dos Transportes e Comunicações (MZN 85,334,980) is a mixed transport-and-communications fund with no evidence of what its communications share buys; `19A000141` the state intelligence service and `27A001741` the financial intelligence unit are out of scope.
- **Stage.** MEF publishes `mapas-propostos` and `mapas-finais` under one folder and distinguishes them by nothing else. **The enacting statute, Lei n.º 13/2025, is not held** — MEF's own `lei-pesoe-2026` item serves a second copy of the bill's fundamentação in a font map that strips every digit. Recorded `appropriated` on the strength of the series label, with the caveat on every record.
- **What the proposta adds, at national grain only:** the bill fixed revenue and expenditure at **535,623,800.00 mil MT** (funcionamento 370,270,400.00, investimento 107,559,600.00); the finais come to **520,634,179.40** (funcionamento 363,102,800.00, capital 100,842,400.00). **The package was cut by 14,989,620.60 mil MT, 2.8%, between tabling and the final allocation** — visible only as an envelope, so no `proposed_total` is populated on any record.
- **⚠ Two document-internal inconsistencies, noted not chased.** Mapa E's total (280,937,450.81) exceeds Mapa C's central funcionamento (224,123,471.41) by the operações financeiras column plus **125,000** (10³ MT) of transferências correntes that the two mapas do not agree on. Neither touches a digital line.
- **Didn't work:** `pdftotext -layout` on any funcionamento mapa. It attaches money to the wrong institution and looks entirely plausible doing it.
