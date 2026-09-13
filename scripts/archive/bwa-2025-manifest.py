"""Append BWA FY2025/26 manifest rows (batch job 18)."""
import csv, os

D = 'new-budget/BWA/2025/'
ROWS = [
 ("2025-03-31-bwa-appropriation-2025-26-act-2025", "2025/26", "appropriation-act",
  "Appropriation (2025/2026) Act, 2025",
  "https://www.finance.gov.bw/images/2025-26/Appropriation2025_2026Act.pdf",
  "Pula, full units", "BWP", "2",
  "NATIVE this year (3,541 chars) against the FY2024/25 Act's 3 chars - the image-only problem did not recur. Assent 31.03.2025, commencement 01.04.2025, No. 8 of 2025, passed 25-Mar-2025. Consolidated Fund P89,571,721,181; Development Fund P23,749,171,200. Schedule reconciles organisation-by-organisation to the estimates volume, MCI 2400 = P966,373,090. TRAP: the Schedule is OFFSET under -layout (org 0400 prints no inline amount, so labels and figures fall out of step by one from that row on and 2400 appears to carry Industrial Court's P62,493,310); decode as an ordered sequence and cross-foot to the printed TOTAL. CABRI mirror confirms. Organisations abolished for FY2025/26: 2500 Defence, 3000 Entrepreneurship, 0223 CTAFA. New: 3300 Higher Education, 3400 Sports and Arts. NO organisation for the Information and Data Protection Commission."),

 ("2025-02-11-bwa-peoples-summary-2025-26-budget", "2024/25;2025/26", "budget-estimates",
  "People's Summary of the 2025/2026 Budget",
  "https://www.finance.gov.bw/images/2025-26/Peoples_Summary_of_The_2025-2026_Budget_11_Feb_2025.pdf",
  "Pula (billions)", "BWP", "14",
  "THE scope_basis document - the estimates volume names no systems, this one does. Para 28: Innovation and Digital Transformation development budget P1.47 billion, funding SmartBots, Village Connectivity Programme phases 2/3/4 (over 1,000 public facilities), 500+ schools via BotsREN, and the Digital Competency Framework. The P1.47bn is a CROSS-MINISTRY THEMATIC LINE, larger than MCI's whole development appropriation of P853,907,763 - not a vote, not a record. Series 2.62 -> 1.83 -> 1.47 bn. Block 4b: BURS VAT on digital trade, Electronic VAT Invoicing Solution, track & trace, One Stop Border Post - none appear as budget lines."),

 ("2025-02-09-bwa-key-features-2025-26-budget", "2025/26", "budget-estimates",
  "Key Features of the 2025/2026 Budget",
  "https://www.finance.gov.bw/images/2025-26/key_features-new_compressed.pdf",
  "Billion Pula", "BWP", "30",
  "NATIVE this year (15,051 chars) against the FY2024/25 deck's 32 chars. Recurrent BWP 65.95bn, Development BWP 23.75bn, Statutory BWP 22.70bn. Carries the budget calendar. Duplicates the People's Summary and Budget-in-Brief on substance - LOW extraction priority."),

 ("2025-03-04-bwa-mof-committee-of-supply-speech-2025-26", "2024/25;2025/26", "budget-estimates",
  "Committee of Supply Speech for Organisation 0300 for both Recurrent and Development Expenditure Estimates 2025/2026",
  "https://www.gov.bw/sites/default/files/2025-03/Ministry%20of%20Finace%20Committee%20of%20Supply%20Speech%20%2004.03.2025%20final__0.pdf",
  "Pula, full units", "BWP", "25",
  "CORROBORATES THE CROSS-VOTE SCAN INDEPENDENTLY: para 52(i) MOF ICT Development P84,571,040 = exactly the figure read from the volume's project 11061 line. Development requested P864,487,720 (-5.4%); split MOF ICT 84,571,040 / Statistical Surveys 125,286,680 / Consultancies 11,500,000 / Infrastructure 143,130,000 / SOE Financing 500,000,000. Recurrent P3,055,755,260 = the Act. Names subventions otherwise invisible: Statistics Botswana P116,549,760, PPRA P67,548,690. dpi.exchange: interoperable National Retail Payment System led by Bank of Botswana, task force includes MCI and BotswanaPost, no budget line attached."),

 ("2026-02-02-bwa-budget-speech-2026-27", "2024/25;2025/26;2026/27", "budget-estimates",
  "2026 Budget Speech, delivered to the National Assembly on 09 February 2026",
  "https://www.finance.gov.bw/images/Budget-Tables/2026_2027_Budget_Speech.pdf",
  "Billion Pula", "BWP", "46",
  "STAGED FOR SECTION VIII = the FY2025/26 REVISED stage. Para 125: 'recurrent expenditure estimates are maintained at their original budget levels, while development expenditure estimates have been revised downward by P903.32 million to P22.85 billion'. That single sentence establishes appropriated = revised for EVERY recurrent line in FY2025/26, and sizes the whole-of-government development revision at P903,320,512 - against which MCI's own P319,012,857 is 35.3% and all digital lines together are 65.3%. FY2025/26 deficit P25.48bn; revenue revised to P71.22bn from P75.49bn; expenditure to P96.70bn from P97.61bn. Para 16: NO supplementary budget requests approved in either 2024/25 or 2025/26 - so the FY2024/25 Supplementary Appropriation Act will never exist. Date from the printed cover, not the undated URL directory."),

 ("2026-02-02-bwa-budget-in-brief-2026-27", "2024/25;2025/26;2026/27", "budget-estimates",
  "Budget-in-Brief 2026/2027",
  "https://www.finance.gov.bw/images/Budget-Tables/2026-2027_Budget_In_Brief.pdf",
  "Million Pula (framework tables)", "BWP", "26",
  "Staged because the FY2025/26 Budget-in-Brief WAS NEVER PUBLISHED - the ministry's own library page prints '(will be uploaded shortly)' against it. Nearest equivalent for the FY2025/26 revised aggregates in citizen-budget format. Ministerial tables are envelopes, not records."),

 ("2026-02-02-bwa-peoples-summary-2026-27-budget", "2025/26;2026/27", "budget-estimates",
  "People's Summary of the 2026/2027 Budget",
  "https://www.finance.gov.bw/images/Budget-Tables/PEOPLE%20SUMMARY.pdf",
  "Pula (billions)", "BWP", "20",
  "Successor to the FY2025/26 scope_basis document; staged for FY2025/26 comparators. LOW TEXT DENSITY: 7,681 chars over 20 pages (384/page) - a graphic-heavy deck whose figures may sit inside images. Verify any figure against the Budget-in-Brief or the speech before use."),

 ("2026-02-26-bwa-mof-committee-of-supply-speech-2026-27", "2025/26;2026/27", "budget-estimates",
  "Committee of Supply Speech for Organisation 0300 for Recurrent and Development Estimates 2026/2027",
  "https://www.botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/Ministry%20of%20FInance%20Committee%20of%20Supply%20Speech%2026-02-2026%20-%20Final.pdf",
  "Pula, full units", "BWP", "21",
  "Staged for FY2025/26 REVISED figures. Para 71: MoF FY2025/26 revised P3,720,242,980 vs approved P3,920,242,980 = a P200m in-year cut. Para 77: FY2025/26 development given as P664,487,720 vs P864,487,720 approved, so the whole P200m came off development - SOE Financing (P500m) is the only line big enough to carry it. Para 78(iv): MOF ICT Development rises to P123,172,400 for FY2026/27, matching the FY2026/27 volume's project 12041. Recurrent described as 'warranted provision P3,055,755,260', i.e. unchanged."),

 ("2026-03-16-bwa-mci-committee-of-supply-speech-2026-27", "2025/26;2026/27", "budget-estimates",
  "Organisation: 2400 - 2026/2027 Recurrent and Development Budget Proposals Presented to the Committee of Supply",
  "https://www.botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/2026%20MCI%20COMMITTEE%20OF%20SUPPLY%20-%20%2016%2003%202026%20REVISED%20FINAL%20(%20Hon%20Minister)%201.pdf",
  "Pula, full units", "BWP", "30",
  "THE KEY DOCUMENT OF THIS COUNTRY-YEAR - section III is the ONLY execution reporting Botswana produces for FY2025/26, and it names the systems the estimates volume never does. Minister David Tshere, cover date 17-Mar-2026 (filename says 16 03 2026). Para 53 recurrent: P966,373,090 allocated for the ministry and its 20 parastatals, P661,769,517 or 68% expended at 31-Dec-2025 (HQ 85%, Radiation Protection Inspectorate 80%); para 54 balance P304,603,573 - sums exactly. Para 56 development: P853,907,763 approved March 2025, REDUCED BY P319,012,857 or 37% TO P534,894,906 IN AUGUST 2025, P294,278,725 or 55% expended at 12-Mar-2026. Para 57 spend by project: Government Data Network Expansion III P74,034,562; National Backbone Network P34,365,298; Government Online (e-Services) P32,992,324. ARITHMETIC INCONSISTENCY IN SOURCE: para 57's 'remaining balance P324,037,239' reconciles to neither the revised nor the approved budget - do not build on it. Named systems: 1Gov-1Citizen (e-Services 33 -> 52); 194 e-Services WITHHELD over GABS problems; Delta Digital Data Centre (BoFiNet, Tier III) migration from Nov-2025 funded by P100m from the Universal Service and Access Fund (own-source, NOT appropriation); Local Access Network Ramotswa/Taung/Moshupa/Thamaga, 13,456 facilities cumulative; Research Fund 200m -> 50m revised, P9,583,636.25 spent. FY2026/27 proposals include the FIRST PRICED CYBER LINE in this corpus: Cyber Security P13,000,000."),

 ("2026-01-01-bwa-budget-strategy-paper-2026-27", "2025/26;2026/27", "mtef",
  "2026-27 Budget Strategy Paper (Draft)",
  "https://www.finance.gov.bw/images/Budget-Strategy-Papers/2026-27_Budget_Strategy_Paper_-_Draft.pdf",
  "Billion Pula", "BWP", "39",
  "Published January 2026, INSIDE the run fiscal year - an in-year fiscal document for FY2025/26 as well as the requested stage for FY2026/27. NOT on the Budget Documents library page: Budget Strategy Papers sit in a SEPARATE Joomla category id=26 (category 23 lists the title with no link). Category 26 also holds a People's Summary of the 2025-26 BSP not previously held. Date INFERRED from Econsult's citation and the prior December cadence - read the printed date at extraction. Do NOT use as a stage: the FY2024/25 edition missed the eventual proposal by 15%."),

 ("2026-05-01-bwa-forensic-audit-summary-report-2026", "2024/25;2025/26", "audited-accounts",
  "Forensic Audit Summary Report 2026",
  "https://www.gov.bw/sites/default/files/2026-05/Forensic%20Audit%20Summary%20Report%202026.pdf",
  "Pula", "BWP", "70",
  "Presidential-directive forensic audit programme: phase 1 risk assessment across 92 public sector entities, phase 2 thirty forensic audits June 2025 - March 2026, focused on April 2014 - March 2024. NOT the Auditor-General's annual certification and DOES NOT supply the audited stage for any fiscal year - doc_type is the nearest canonical value only. Staged because the audits ran through FY2025/26 and the entity list is the only published map of where the state thinks its financial-control risk sits. Date inferred from the URL directory."),
]

hdr_cols = 17
out = []
for stem, fyc, dt, title, url, scale, cur, pages, notes in ROWS:
    art = D + stem + '.pdf'
    comp = D + stem + '-companion.md'
    assert os.path.exists(art) and os.path.exists(comp), stem
    out.append(["BWA", "2025", fyc, dt, title, url, art, comp, "2026-07-25",
                scale, cur, pages, "", "", "", "", notes])

with open('new-budget/manifest.csv', 'a', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, lineterminator='\n')
    for r in out:
        assert len(r) == hdr_cols, len(r)
        w.writerow(r)
print('appended', len(out), 'rows')
