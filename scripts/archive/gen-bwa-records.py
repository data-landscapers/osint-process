# -*- coding: utf-8 -*-
"""One-shot generator for the BWA FY2024/25-FY2026/27 domestic-state finance records.

Written by the 2026-07-25 budget-extract pass over new-budget/BWA/{2024,2025,2026}.
Kept in scripts/ so the record set is reproducible and auditable against the
archived CSVs in budget-archive/BWA/.

Every figure here was read from the volume's own printed tables and cross-footed to
a printed DEPARTMENT TOTAL / MINISTRY TOTAL before it was written down. The origin
gate is printed in the source: the development half of every Botswana estimates
volume carries a SOF (Source of Financing) column and every line in scope reads
`DDF` (Domestic Development Fund); Table IV of the FY2026/27 Financial Statements
volume puts the national development budget at 99.29% domestically financed.
"""
import os, sys

sys.stdout.reconfigure(encoding="utf-8")
NEW = "new"
TODAY = "2026-07-25"

# --------------------------------------------------------------------------
# Fiscal years (April-March)
# --------------------------------------------------------------------------
FY = {
    2024: ("2024/2025", "2024-04-01", "2025-03-31"),
    2025: ("2025/2026", "2025-04-01", "2026-03-31"),
    2026: ("2026/2027", "2026-04-01", "2027-03-31"),
}

# Documents (companion page stem in budget-archive, title, url)
VOL24 = ("2024-02-05-bwa-estimates-of-expenditure-consolidated-development-funds-2024-25",
         "Estimates of Expenditure from the Consolidated and Development Funds 2024/25",
         "https://www.finance.gov.bw/images/DevelopmentandBudget/2024-25/Estimates2024-2025FINALSB3july-compressed.pdf")
VOL25 = ("2025-02-01-bwa-estimates-of-expenditure-consolidated-development-fund-2025-26",
         "Estimates of Expenditure from the Consolidated and Development Fund 2025/26",
         "https://www.finance.gov.bw/images/2025-26/ESTIMATES%20OF%20EXPENDITURE%202025-26.pdf")
VOL26 = ("2026-02-01-bwa-expenditure-estimates-2026-27",
         "Expenditure Estimates 2026/27",
         "https://www.finance.gov.bw/images/Budget-Tables/EXPENDITURE_ESTIMATES_26-27_FINAL_DRAFT.pdf")
FS26 = ("2026-02-01-bwa-financial-statements-tables-estimates-revenues-2026-27",
        "Financial Statements, Tables and Estimates of the Consolidated and Development Funds Revenues 2026/2027",
        "https://www.finance.gov.bw/images/Budget-Tables/FINANCIAL_STATEMENTS_TABLES_26-27.pdf")
COS_IEC = ("2026-03-10-bwa-cos-1600-independent-electoral-commission-2026-27",
           "Committee of Supply Speech 2026/2027 — Independent Electoral Commission",
           "https://botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/IEC.pdf")
COS_PARL = ("2026-03-01-bwa-cos-0100-parliament-2026-27",
            "Committee of Supply Speech 2026/2027 — Parliament",
            "https://botswanaspeaks.gov.bw/media/COMMITTEE%20OF%20SUPPPLY%20SPEECHES/PARLIAMENT.pdf")

FISC = "Ministry of Finance (Botswana) — the Consolidated Fund and the Development Fund"
FISC_SLUG = "ministry-of-finance-botswana"

# organisation code -> (current name, entity slug, topics, recipient label)
ORG = {
    "0100": ("Parliament", "parliament-of-botswana", "[dpi.govtech, finance.budget]"),
    "0200": ("Ministry for State President, Defence and Security", "ministry-for-state-president-botswana", "[dpi.govtech, infra.connect, finance.budget]"),
    "0300": ("Ministry of Finance", "ministry-of-finance-botswana", "[dpi.govtech, finance.budget]"),
    "0400": ("Ministry of Labour and Home Affairs", "ministry-of-labour-and-home-affairs-botswana", "[dpi.id, dpi.registry, finance.budget]"),
    "0500": ("Ministry of Lands and Agriculture", "ministry-of-lands-and-agriculture-botswana", "[dpi.govtech, finance.budget]"),
    "0600": ("Ministry of Child Welfare and Basic Education", "ministry-of-child-welfare-and-basic-education-botswana", "[dpi.govtech, finance.budget]"),
    "0700": ("Ministry of Trade and Entrepreneurship", "ministry-of-trade-and-entrepreneurship-botswana", "[dpi.govtech, finance.budget]"),
    "1100": ("Ministry of Health", "ministry-of-health-botswana", "[dpi.exchange, dpi.mis, finance.budget]"),
    "1200": ("Administration of Justice", "administration-of-justice-botswana", "[dpi.govtech, finance.budget]"),
    "1600": ("Independent Electoral Commission", "independent-electoral-commission-botswana", "[dpi.id, dpi.registry, finance.budget]"),
    "1700": ("Office of the Ombudsman", "office-of-the-ombudsman-botswana", "[dpi.govtech, finance.budget]"),
    "2000": ("Ministry of Environment and Tourism", "ministry-of-environment-and-tourism-botswana", "[dpi.govtech, finance.budget]"),
    "2100": ("Industrial Court", "industrial-court-botswana", "[dpi.govtech, finance.budget]"),
    "2300": ("Ministry of Transport and Infrastructure", "ministry-of-transport-and-infrastructure-botswana", "[dpi.govtech, dpi.registry, finance.budget]"),
    "2400": ("Ministry of Communications and Innovation", "ministry-of-communications-and-innovation-botswana", "[dpi.govtech, infra.connect, finance.budget]"),
    "2900": ("Ministry of Justice and Correctional Services", "ministry-of-justice-and-correctional-services-botswana", "[dpi.govtech, finance.budget]"),
    "3000": ("Ministry of Entrepreneurship", "ministry-of-entrepreneurship-botswana", "[dpi.govtech, finance.budget]"),
    "3100": ("Office of the Receiver", "office-of-the-receiver-botswana", "[dpi.govtech, finance.budget]"),
    "3300": ("Ministry of Higher Education", "ministry-of-higher-education-botswana", "[dpi.govtech, finance.budget]"),
    "3400": ("Ministry of Sport and Arts", "ministry-of-sport-and-arts-botswana", "[dpi.govtech, finance.budget]"),
    "3500": ("Botswana Prisons Service", "botswana-prisons-service", "[dpi.govtech, finance.budget]"),
}

# Stage -> (published date, precision, source-of-date note)
STAGE_DATE = {
    (2024, "appropriated"): ("2024-04-01", "month",
        "the Appropriation (2024/25) Act, 2024 is held image-only and its assent date is not established, so `published` is the fiscal-year start at month precision per the driver"),
    (2024, "revised"): ("2025-02-09", "day",
        "the revised estimates for FY2024/25 were presented with the 2025 Budget Speech of 9 February 2025 (§VIII)"),
    (2024, "actual"): ("2025-03-31", "day", "the fiscal year end; the outturn is the year's closing position"),
    (2025, "appropriated"): ("2025-03-31", "day",
        "date of assent of the Appropriation (2025/2026) Act, 2025 (Act No. 8 of 2025); commencement 1 April 2025"),
    (2025, "revised"): ("2025-08-01", "month",
        "the development revision was dated to August 2025 by the Minister of Finance (2026 Budget Speech)"),
    (2025, "actual"): ("2025-12-05", "day",
        "the cut-off printed on the FY2026/27 volume's actual column, `Actual Expenditure (05 December 2025)` — a part-year figure, not a full-year outturn"),
    (2026, "appropriated"): ("2026-04-01", "month",
        "the Appropriation (2026/2027) Act is not published on any Ministry of Finance category and is not held (see acquisitions); the estimates were approved organisation by organisation in Committee of Supply during February-March 2026 and the fiscal year began 1 April 2026, so `published` is the fiscal-year start at month precision"),
}

# --------------------------------------------------------------------------
# The record set.  Fields:
#   (fy, org, code, stage, capital, recurrent, total, scope, title_line, desc,
#    scope_basis, doc, locator, notes[])
# --------------------------------------------------------------------------
R = []


def rec(fy, org, code, stage, *, capital=None, recurrent=None, total,
        scope, label, desc, basis, doc, locator, notes=(), version="original",
        classlabels="Organisation / Department / Project (development) — Botswana estimates of expenditure",
        econ="Development Fund (capital) — Estimated Expenditure by Project",
        topics=None, key=None):
    R.append(dict(fy=fy, org=org, code=code, stage=stage, capital=capital,
                  recurrent=recurrent, total=total, scope=scope, label=label,
                  desc=desc, basis=basis, doc=doc, locator=locator,
                  notes=list(notes), version=version, classlabels=classlabels,
                  econ=econ, topics=topics, key=key))


DDF = ("The line's Source of Financing is printed in the volume as `DDF` — Domestic Development Fund. "
       "No external grant or loan code appears against it, so the origin gate is the document's own and "
       "the whole amount is domestic-state.")
SCALE = ("Pula, **full units** — the Botswana estimates volumes carry no thousands or millions multiplier "
         "anywhere, so there is no 1,000x trap in this corpus. Verified by summing the department lines to "
         "the printed MINISTRY TOTAL.")

# ==========================================================================
# FY2024/25
# ==========================================================================
rec(2024, "2400", "11631", "appropriated", capital=736601447, total=736601447, scope="whole",
    label="project 11631 « Information and Communications Technology », development estimate: P736,601,447",
    desc="Information and Communications Technology.",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL24, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2024-25, organisation 2400, departments 2404 and 2406, project 11631",
    notes=["Two departments carry the same project code and are summed here: 2404 Telecommunications and Postal Services P567,873,447 and 2406 Information Technology P168,728,000. Both cross-foot to their printed DEPARTMENT TOTAL, and the four project lines sum to the printed MINISTRY TOTAL of P1,728,445,447.",
           "The volume names no systems. The People's Guide to the 2024/2025 Budget describes the ministry's P1.73bn as covering “ICT Projects such as Online Services Implementation, Government Data Network Expansion”, and the 2024 Budget Speech (para 54) gives a cross-ministry *Innovation and Digital Transformation* thematic line of P1.83bn which is **not a vote** and is not recorded as one."])

rec(2024, "2400", "11631", "revised", capital=266648447, total=266648447, scope="whole",
    label="project 11631 « Information and Communications Technology », revised development estimate: P266,648,447",
    desc="Information and Communications Technology.",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, column `2024-25`, organisation 2400, departments 2404 and 2406, project 11631",
    version="revised",
    notes=["A cut of 63.8% on the appropriation (P736,601,447 → P266,648,447), inside the year. Department 2404 fell P567,873,447 → P176,373,447 (−68.9%) and department 2406 P168,728,000 → P90,275,000 (−46.5%).",
           "Botswana approved **no supplementary budget** in FY2024/25 or FY2025/26 as a matter of stated policy (2026 Budget Speech, para 16). The revision is therefore an in-year reallocation restated in the following year's estimates volume, not a supplementary appropriation — `supplementary_basis` is `restated-total`."])

rec(2024, "2400", "11637", "appropriated", capital=983694000, total=983694000, scope="unclear",
    label="project 11637 « Research and Development », development estimate: P983,694,000",
    desc="Research and Development.",
    basis="Development project of the digital ministry's research departments (2407 Research, Science and Technology). The volume names no systems and the ministry's research portfolio spans satellite, nuclear and biotechnology work as well as digital, so the line is identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL24, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2024-25, organisation 2400, department 2407, project 11637",
    notes=["The 2024 Budget Speech puts the R&D development budget at P1.02bn, +280.9% on FY2023/24.",
           "Reported apart from the headline digital total per the driver — a mixed line's digital share is never computed."])

rec(2024, "2400", "11637", "revised", capital=511419000, total=511419000, scope="unclear",
    label="project 11637 « Research and Development », revised development estimate: P511,419,000",
    desc="Research and Development.",
    basis="Development project of the digital ministry's research departments. Identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, column `2024-25`, organisation 2400, departments 2407 and 2409, project 11637",
    version="revised",
    notes=["Two departments carry project 11637 at the revision: 2407 P279,735,000 and **2409 Research and Knowledge Business P231,684,000**, a department created during the year (its TNDP TEC is printed as `–` and its revised TEC as P280,000,000, the signature of a project created mid-year).",
           "So the fall from P983,694,000 to P511,419,000 (−48.0%) is a cut **plus a reorganisation**: P231,684,000 of the P703,959,000 taken off department 2407 reappeared in a new department running the same project."])

rec(2024, "2400", "development", "actual", capital=514090181, total=514090181, scope="partial",
    label="organisation 2400 Development Fund outturn FY2024/25: P514,090,181",
    desc="Development Fund actual expenditure, organisation 2400 Communications, Knowledge and Technology.",
    basis="Organisation-level Development Fund outturn. Botswana publishes no per-project actuals, so this is the finest grain the outturn exists at; it includes the radiation-protection project 11638 alongside the ICT and R&D projects, hence `partial`",
    doc=FS26, locator="TABLE II — SUMMARY OF DEVELOPMENT FUND EXPENDITURE 2019/2020 TO 2026/2027, OLD MINISTRIES column 2024/25, organisation 2400",
    notes=["**This closes a gap the FY2024/25 sweep declared unrecoverable.** That run established that a Botswana estimates volume carries a prior-year *recurrent* actual column and concluded the capital outturn could not be recovered. It can — from Table II of the Financial Statements volume, which gives Development Fund actual expenditure by organisation for 2019/20 to 2024/25.",
           "Against the appropriation of P1,728,445,447 that is an execution rate of **29.7%**; against the revised P789,717,447 it is **65.1%**. Botswana's digital ministry spent less than a third of what Parliament voted it.",
           "Botswana published **none** of its four FY2024/25 quarterly execution reports — the Ministry of Finance's own page printed “(Unavailable)” against all of them — and the Auditor-General's report for the year ended 31 March 2025, statutorily due 31 December 2025, was still not published at 2026-07-25."],
    econ="Development Fund (capital) — actual expenditure",
    classlabels="Organisation — Table II summary of Development Fund expenditure")

# MCI recurrent, department grain
for code, dept, app, rev, act, pct in [
    ("2404", "Department of Digital Communications, Infrastructure and Business", 13246620, 13126140, 12341893, "93.2%"),
    ("2406", "Department of Shared Digital Services", 587270280, 555644290, 487118818, "82.9%"),
]:
    rec(2024, "2400", code, "appropriated", recurrent=app, total=app, scope="whole",
        label="department %s « %s », recurrent estimate: P%s" % (code, dept, format(app, ",")),
        desc=dept + ".",
        basis="Departmental recurrent vote of a department whose entire stated function is digital — %s" % dept.lower(),
        doc=VOL24, locator="Ministry 2400, organisation summary, column `Estimate 2024-25`, department %s" % code,
        econ="Consolidated Fund (recurrent) — organisation summary by department",
        classlabels="Organisation / Department / Parent account / Account — Botswana estimates of expenditure (recurrent)",
        notes=["Departments 2401 (Headquarters), 2407 and 2409 (research) and 2408 (radiation protection) are **not** recorded on the recurrent side: 2401 is the ministry's administration envelope and the rest are outside or only partly inside scope. Their figures are in `budget-archive/BWA/2024/bwa-2024-mci-recurrent-by-department.csv`.",
               "The volume's recurrent and development halves give **different names to the same department code** in FY2024/25 — 2404 is *Digital Communications, Infrastructure and Business* here and *Telecommunications and Postal Services* in the development section; 2406 is *Shared Digital Services* / *Information Technology*. Join on the code, never the name."])
    rec(2024, "2400", code, "revised", recurrent=rev, total=rev, scope="whole",
        label="department %s « %s », revised recurrent estimate: P%s" % (code, dept, format(rev, ",")),
        desc=dept + ".", version="revised",
        basis="Departmental recurrent vote of a department whose entire stated function is digital — %s" % dept.lower(),
        doc=VOL25, locator="Ministry 2400, organisation summary, column `Authorised Expenditure 2024-25`, department %s" % code,
        econ="Consolidated Fund (recurrent) — organisation summary by department",
        classlabels="Organisation / Department / Parent account / Account — Botswana estimates of expenditure (recurrent)",
        notes=["Ministry recurrent was revised from P977,321,140 to P928,501,580, a cut of 5.0% — an order of magnitude smaller than the 54.3% taken off the development budget in the same year.",
               "The `Authorised Expenditure` column is **not always a restatement**: in FY2025/26 it reproduced the original estimate department by department, because recurrent was not revised at all that year. The equality must be checked, never assumed."])
    rec(2024, "2400", code, "actual", recurrent=act, total=act, scope="whole",
        label="department %s « %s », recurrent outturn FY2024/25: P%s" % (code, dept, format(act, ",")),
        desc=dept + ".",
        basis="Departmental recurrent vote of a department whose entire stated function is digital — %s" % dept.lower(),
        doc=VOL26, locator="Ministry 2400, organisation summary, column `Actual Expenditure to 31-03-25`, department %s" % code,
        econ="Consolidated Fund (recurrent) — organisation summary by department",
        classlabels="Organisation / Department / Parent account / Account — Botswana estimates of expenditure (recurrent)",
        notes=["Execution against the appropriation: **" + pct + "**. The ministry as a whole executed 86.4% of its recurrent vote (P844,338,028 of P977,321,140), but the two smallest and most forward-looking departments spent least — 2407 Technology and Commercialization 55.0% and 2409 Research and Knowledge Business 40.1% — while Headquarters ran at 98.2%.",
               "**The printed MINISTRY TOTAL of P844,338,028 exceeds the sum of its own department rows by one Pula** (P844,338,027). Recorded as printed for the departments; the residual is in the source, not the extraction."])

# FY2024/25 cross-vote
XV24 = [
    ("0200", "11015", "MSP Computerisation", 156890000, 156890000,
     "The only cross-vote computerisation line held **exactly flat** through a revision that cut the digital ministry's capital budget by 54.3%. Village Connectivity and E-Cabinet are delivered from this line, not from the digital ministry's.", "whole"),
    ("0600", "11161", "MESD Computerisation", 120510000, 70510000, "", "whole"),
    ("0400", "11081", "Computerisation", 56500000, 22494000,
     "Botswana's national identity spend sits inside this line: organisation 0400 contains department 0411 Department of Civil and National Registration, which produces the Omang. **The estimates name no systems at all** — only `<Ministry> Computerisation` — so the identity money is invisible at volume grain in FY2024/25 and only becomes nameable in the FY2026/27 Committee of Supply season.", "whole"),
    ("0300", "11061", "MoF Computerisation", 48739941, 35181175, "", "whole"),
    ("1100", "11335", "MoH Computerisation", 33240000, 16335935, "", "whole"),
    ("0500", "11116", "MoA Computerisation", 33150000, 31150000,
     "Two departments: 0501 Headquarters P3,150,000 and 0510 Animal Health P30,000,000.", "whole"),
    ("0700", "11212", "MTI Computerisation", 8000000, 8120320, "One of only two lines to rise through the revision.", "whole"),
    ("2000", "11503", "MET Computerisation", 7709700, 4453000,
     "Three departments: 2001 Headquarters P315,000, 2004 Meteorological Services P3,243,000 and 2008 National Museum, Monuments and Art Gallery P4,151,700.", "whole"),
    ("3000", "11861", "MoE Computerisation", 7338240, None,
     "Two departments. Organisation 3000 was **abolished at 2025-04-01** and absorbed into 0700; the FY2025/26 volume carries no restated FY2024/25 figure for project 11861, so this line has no revised stage and never will.", "whole"),
    ("2900", "11832", "Computerisation", 7109454, 2800000,
     "Two departments: 2901 Headquarters (Ministry of Justice) P5,631,543 and 2903 Office of the Receiver P1,477,911. From FY2025/26 the Office of the Receiver becomes its own organisation (3100) and the project splits.", "whole"),
    ("1200", "11382", "AoJ Computerisation", 4908495, 2849897, "", "whole"),
    ("2300", "11584", "Information and Communications", 3657150, 19055750,
     "Rose 5.2x through the revision — the largest proportionate increase of any cross-vote line in the year.", "whole"),
]
for org, code, proj, app, rev, note, sc in XV24:
    extra = [note] if note else []
    rec(2024, org, code, "appropriated", capital=app, total=app, scope=sc,
        label="project %s « %s », development estimate: P%s" % (code, proj, format(app, ",")),
        desc=proj + ".",
        basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation project, whose whole stated purpose is the digitisation of that ministry's business",
        doc=VOL24, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2024-25, organisation %s, project %s" % (org, code),
        notes=extra + ["**Botswana's cross-vote digital capital is systematic, not incidental: every ministry carries its own `<Ministry> Computerisation` development project.** The twelve of them total **P487,752,980** appropriated for FY2024/25, against the digital ministry's own ICT projects at P736,601,447 — so a sector-vote-only view of Botswana's FY2024/25 capital digital spend understates it by about two fifths. Whole-of-government computerisation and ICT: **P1,224,354,427**.",
                       "False positive caught and excluded: `11551 IC Infrastructure` under organisation 2100 is **Industrial Court** infrastructure, not infocomms — P19,797,690 that would otherwise have inflated the cross-vote total by 4%."])
    if rev is not None:
        rec(2024, org, code, "revised", capital=rev, total=rev, scope=sc,
            label="project %s « %s », revised development estimate: P%s" % (code, proj, format(rev, ",")),
            desc=proj + ".", version="revised",
            basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation project",
            doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, column `2024-25`, organisation %s, project %s" % (org, code),
            notes=extra + ["Cross-vote computerisation was revised from P487,752,980 to **P369,840,077** in-year, −24.2% (excluding organisation 3000, abolished and not restated). The digital ministry's own ICT projects were cut 63.8% over the same revision, so **the cut was not government-wide** — the sector vote took a disproportionate share."])

# ==========================================================================
# FY2025/26
# ==========================================================================
rec(2025, "2400", "11631", "appropriated", capital=369079545, total=369079545, scope="whole",
    label="project 11631 « Information and Communications Technology », development estimate: P369,079,545",
    desc="Information and Communications Technology.",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, organisation 2400, departments 2404 and 2406, project 11631",
    notes=["Departments 2404 P159,079,545 and 2406 P210,000,000; both cross-foot to their printed DEPARTMENT TOTAL and the five project lines sum to the printed MINISTRY TOTAL of P853,907,763.",
           "Half the FY2024/25 appropriation (P736,601,447 → P369,079,545, −49.9%). Over the same year cross-vote computerisation **rose** 14.3%, so the composition of Botswana's digital capital inverted: cross-vote became **60.5%** of it, against 39.8% the year before."])

rec(2025, "2400", "11631", "revised", capital=338683428, total=338683428, scope="whole",
    label="project 11631 « Information and Communications Technology », revised development estimate: P338,683,428",
    desc="Information and Communications Technology.", version="revised",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Estimated Expenditure 2025-26`, organisation 2400, departments 2404 and 2406, project 12481",
    notes=["**The project code changed with the plan.** The Transitional National Development Plan's `11631` becomes NDP 12's `12481` between the FY2025/26 and FY2026/27 volumes, and so does every cross-vote line. A Botswana development series keyed on project code breaks at 2026-04-01 and needs a mapping row.",
           "Department 2406's ICT line was **not touched at all** (P210,000,000 in both columns); the whole reduction fell on department 2404 (−19.1%). The ministry's cut was concentrated in research, not connectivity — project 11637 lost two thirds.",
           "The minister dated the development revision to **August 2025**, five months into the year. Government-wide the development budget was cut P903,320,512 (−3.8%), of which the digital ministry's P319,012,857 is 35.3% and cross-vote computerisation's P266,091,865 a further 29.5% — **digital capital is 5.94% of the development budget and took roughly 65% of the year's reduction.**"])

rec(2025, "2400", "11631", "actual", capital=142712599, total=142712599, scope="whole",
    label="project 11631 « Information and Communications Technology », expenditure to 5 December 2025: P142,712,599",
    desc="Information and Communications Technology.",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Actual Expenditure (05 December 2025)`, organisation 2400, departments 2404 and 2406, project 12481",
    notes=["**A part-year figure, not an outturn** — the column's own cut-off is 5 December 2025, eight months into a twelve-month year. 42.1% of the revised estimate at that date. The full-year FY2025/26 development actual will appear in Table II of the FY2027/28 Financial Statements volume, around February 2027.",
           "The MCI Committee of Supply speech of 17 March 2026 reports the same programme at **P294,278,725, 55% of the revised budget**, at 12 March 2026 — by project: Government Data Network Expansion III P74,034,562, National Backbone Network P34,365,298, Government Online (e-Services) P32,992,324.",
           "That speech's para 57 gives a “remaining balance of P324,037,239” which reconciles to neither the revised budget (534,894,906 − 294,278,725 = 240,616,181) nor the appropriation. Recorded here as printed in the volume; the speech's arithmetic inconsistency is noted, not adopted."])

rec(2025, "2400", "11637", "appropriated", capital=477403718, total=477403718, scope="unclear",
    label="project 11637 « Research and Development », development estimate: P477,403,718",
    desc="Research and Development.",
    basis="Development project of the digital ministry's research departments (2407 and 2409). Identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, organisation 2400, departments 2407 and 2409, project 11637",
    notes=["Departments 2407 P435,804,299 and 2409 P41,599,419."])

rec(2025, "2400", "11637", "revised", capital=185786978, total=185786978, scope="unclear",
    label="project 11637 « Research and Development », revised development estimate: P185,786,978",
    desc="Research and Development.", version="revised",
    basis="Development project of the digital ministry's research departments. Identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Estimated Expenditure 2025-26`, organisation 2400, departments 2407 and 2409, project 12482",
    notes=["Department 2407's R&D line lost two thirds (P435,804,299 → P141,917,899, −67.4%) while department 2409's rose 5.5%. The MCI Committee of Supply speech gives the same story in narrative: the **Research Fund** was approved “over P200 million” for FY2025/26, **revised to P50 million**, and had spent **P9,583,636.25**."])

rec(2025, "2400", "11637", "actual", capital=42771544, total=42771544, scope="unclear",
    label="project 11637 « Research and Development », expenditure to 5 December 2025: P42,771,544",
    desc="Research and Development.",
    basis="Development project of the digital ministry's research departments. Identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Actual Expenditure (05 December 2025)`, organisation 2400, departments 2407 and 2409, project 12482",
    notes=["A part-year figure at 5 December 2025 — 23.0% of the revised estimate with roughly a quarter of the year left."])

for code, dept, app in [
    ("2404", "Department of Digital Communications, Infrastructure and Business", 13737390),
    ("2406", "Department of Shared Digital Services", 594362280),
]:
    rec(2025, "2400", code, "appropriated", recurrent=app, total=app, scope="whole",
        label="department %s « %s », recurrent estimate: P%s" % (code, dept, format(app, ",")),
        desc=dept + ".",
        basis="Departmental recurrent vote of a department whose entire stated function is digital — %s" % dept.lower(),
        doc=VOL25, locator="Ministry 2400, organisation summary, column `Estimate 2025-26`, department %s" % code,
        econ="Consolidated Fund (recurrent) — organisation summary by department",
        classlabels="Organisation / Department / Parent account / Account — Botswana estimates of expenditure (recurrent)",
        notes=["**No revised record is built for FY2025/26 recurrent, because there was no revision.** “Recurrent expenditure estimates are maintained at their original budget levels” (2026 Budget Speech, para 125), and the FY2026/27 volume's `Authorised Expenditure 2025-26` column reproduces this figure department by department. Recording an identical `revised` record would create a second same-stage line for the compile to sum.",
               "The ministry executed **68%** of its recurrent vote by 31 December 2025 — P661,769,517 of P966,373,090, balance P304,603,573, the two summing exactly (MCI Committee of Supply speech, 17 March 2026). Headquarters was highest at 85%, an inversion of FY2024/25's departmental pattern. The figure is ministry-level; the speech gives no departmental split, so no departmental `actual` record is built for FY2025/26."])

XV25 = [
    ("0600", "12104", "MCWBE Computerisation", 270000000, 38819833, 0,
     "**The largest single capital computerisation line in the FY2025/26 budget is not in the digital ministry** — it is in basic education, and it is bigger than either of the digital ministry's two ICT departments. It was then cut **85.6%** and had spent **nothing** by 5 December 2025."),
    ("0200", "12024", "MSP Computerisation", 104080000, 64074943, 41740940,
     "Village Connectivity and E-Cabinet are delivered from the State President's line."),
    ("0300", "12041", "MoF Computerisation", 84571040, 84571040, 5154933,
     "Held **exactly flat** through the revision, and independently confirmed by the Ministry of Finance's own Committee of Supply speech (para 52(i), *MOF ICT Development*) — two documents, two extraction routes, the same number. That agreement is the check that validates the whole cross-vote scan."),
    ("2300", "12461", "Information and Communications Technology", 27597281, 13597281, 3663284, ""),
    ("0500", "12084", "MLA Computerisation", 25000000, 25000000, 5100,
     "Held flat through the revision and then almost entirely unspent — P5,100 of P25,000,000 by 5 December 2025."),
    ("0400", "12061", "Computerisation", 18700000, 12200000, 4425317, ""),
    ("1100", "12244", "MoH Computerisation", 10800000, 9500000, 1587158, ""),
    ("3400", "12621", "MoSA Computerisation", 8751006, 8751006, 2164874,
     "Organisation 3400 was created at 2025-04-01; the FY2025/26 volume prints this project's code as `NEW` and it becomes `12621` under NDP 12."),
    ("1200", "12263", "AoJ Computerisation", 4760000, 4760000, 166931,
     "Held flat through the revision and then 3.5% spent by 5 December 2025."),
    ("3100", "12562", "OTR Computerisation", 4564988, 500000, 0,
     "Cut **89.0%** with no expenditure at all. The Office of the Receiver's procurement of the **Confiscated Property and Asset Management (CPAM) system was cancelled** after a potential irregularity was identified, and the re-tender closed 27 February 2026."),
    ("3300", "12601", "MHE Computerisation", 3950000, 3950000, 3950000,
     "The only cross-vote line fully spent by 5 December 2025."),
    ("2900", "12523", "MJCS Computerisation", 3654291, 3654291, None,
     "The FY2026/27 volume's actual column is blank for this line; no part-year figure is recorded."),
    ("2000", "12403", "MET Computerisation", 0, 14800000, 1000000,
     "**Nil appropriated, then funded at the revision.** The three departments carrying project 11503 all show a dash in the FY2025/26 volume's `2025-26` column — a stated nil, recorded as `0` — and P14,800,000 appears against them in the FY2026/27 volume's revised column."),
    ("0700", "12122", "MTE Computerisation", 0, 7000000, 190992,
     "**Nil appropriated, then funded at the revision** — the second of two such lines in the year."),
]
for org, code, proj, app, rev, act, note in XV25:
    extra = [note] if note else []
    common = ["Cross-vote computerisation across fourteen organisations totals **P566,428,606** appropriated for FY2025/26, against the digital ministry's own ICT projects at P369,079,545 — so **cross-vote is 60.5% of Botswana's capital computerisation money, and a sector-vote-only view now misses the majority of it.** At the revision the two fall to P300,336,741 and P338,683,428."]
    rec(2025, org, code, "appropriated", capital=app, total=app, scope="whole",
        label="project %s « %s », development estimate: P%s" % (code, proj, format(app, ",")),
        desc=proj + ".",
        basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation project, whose whole stated purpose is the digitisation of that ministry's business",
        doc=VOL25, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2025-26, organisation %s, project %s (TNDP code)" % (org, code),
        notes=extra + common)
    rec(2025, org, code, "revised", capital=rev, total=rev, scope="whole",
        label="project %s « %s », revised development estimate: P%s" % (code, proj, format(rev, ",")),
        desc=proj + ".", version="revised",
        basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation project",
        doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Estimated Expenditure 2025-26`, organisation %s, project %s" % (org, code),
        notes=extra + common)
    if act is not None:
        rec(2025, org, code, "actual", capital=act, total=act, scope="whole",
            label="project %s « %s », expenditure to 5 December 2025: P%s" % (code, proj, format(act, ",")),
            desc=proj + ".",
            basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation project",
            doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Actual Expenditure (05 December 2025)`, organisation %s, project %s" % (org, code),
            notes=extra + ["**A part-year figure, not an outturn** — the column's cut-off is 5 December 2025, eight months into the year. Cross-vote computerisation had spent P65,419,018 of a revised P300,336,741 (21.8%) at that date."])

rec(2025, "3500", "12643", "revised", capital=9158347, total=9158347, scope="whole",
    label="project 12643 « Prisons - ICT Development », revised development estimate: P9,158,347",
    desc="Prisons - ICT Development.", version="revised",
    basis="Explicit project title in the Development Fund estimates — a dedicated ICT development project",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, column `Estimated Expenditure 2025-26`, organisation 3500, project 12643",
    notes=["Botswana Prisons Service became a full organisation only at 2026-04-01, carved out of organisation 2900. It has **no FY2025/26 appropriation of its own** — this revised figure is the FY2026/27 volume's restatement of money that sat inside organisation 2900 when it was voted, so there is no `appropriated` record to pair it with.",
           "P1,369,489 had been spent against it at 5 December 2025."])

# ==========================================================================
# FY2026/27
# ==========================================================================
rec(2026, "2400", "12481", "appropriated", capital=251000000, total=251000000, scope="whole",
    label="project 12481 « Information and Communications Technology », development estimate: P251,000,000",
    desc="Information and Communications Technology.",
    basis="Explicit project title in the Development Fund estimates — the project's whole stated purpose is information and communications technology",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, organisation 2400, departments 2404 (P95,000,000) and 2406 (P156,000,000), project 12481",
    notes=["**The volume and the ministry's own Committee of Supply speech agree to the Pula**: the speech of 17 March 2026 puts the ICT programme at P251,000,000 and itemises it — Government Data Network Expansion III P75,000,000; Government Online Services (e-Services) P70,000,000; National Backbone Network P65,000,000; **Cyber Security P13,000,000**; International Connectivity P10,000,000.",
           "The P13,000,000 cyber line is the **first priced cybersecurity item in this corpus for Botswana** — and the only one. The **Cybersecurity Act, 2025 (Act 21 of 2025)**, assented 5 November 2025, establishes a National Cybersecurity Authority as a body corporate with a Board, a CEO and licensing powers over cybersecurity service providers; **no organisation, vote or line for that Authority appears anywhere in the FY2026/27 budget.**",
           "P473,200,000 is the ministry's whole development budget — down 11.5% on the FY2025/26 **revised** figure but **44.6% on what was appropriated** for FY2025/26."])

rec(2026, "2400", "12482", "appropriated", capital=213700000, total=213700000, scope="unclear",
    label="project 12482 « Research and Development », development estimate: P213,700,000",
    desc="Research and Development.",
    basis="Development project of the digital ministry's research departments (2407 P73,774,000 and 2409 P139,926,000). Identified as digital only by its parent vote — flagged `unclear` rather than apportioned",
    doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, organisation 2400, departments 2407 and 2409, project 12482",
    notes=["Down 55.2% on the FY2025/26 appropriation of P477,403,718 and the third consecutive year of contraction for the ministry's research money."])

for code, dept, app in [
    ("2404", "Department of Digital Communications, Infrastructure and Business", 12692280),
    ("2406", "Department of Shared Digital Services", 587310850),
]:
    rec(2026, "2400", code, "appropriated", recurrent=app, total=app, scope="whole",
        label="department %s « %s », recurrent estimate: P%s" % (code, dept, format(app, ",")),
        desc=dept + ".",
        basis="Departmental recurrent vote of a department whose entire stated function is digital — %s" % dept.lower(),
        doc=VOL26, locator="Ministry 2400, organisation summary, column `Estimate 2026-27`, department %s" % code,
        econ="Consolidated Fund (recurrent) — organisation summary by department",
        classlabels="Organisation / Department / Parent account / Account — Botswana estimates of expenditure (recurrent)",
        notes=["Ministry recurrent P949,920,900, down 1.7% on FY2025/26. **Table I of the Financial Statements volume shows organisation 2400 falling from P1,900,336,306 in FY2019/20 to P844,338,028 actual in FY2024/25, but that is not a comparable series** — Table I mixes old and new organisation definitions across its own columns without labelling the break (unlike Table II, which labels its two halves), and the ministry lost its roads and transport departments in the interim."])

XV26 = [
    ("0600", "12104", "MCWBE Computerisation", 253000000,
     "**The one ministry whose FY2026/27 Committee of Supply speech is not published is the one that held the largest capital computerisation line in FY2025/26** — organisation 0600. The volume nevertheless carries its FY2026/27 figure, so the line is not unnamed, only unexplained: P253,000,000 with no published statement of what it buys."),
    ("0200", "12024", "MSP Computerisation", 148200000,
     "The Committee of Supply speech of 24 February 2026 attributes this line to **Village Connectivity and E-Cabinet**. It is the State President's line, not the digital ministry's, and it is a 42% rise on the FY2025/26 appropriation and a 131% rise on the revision."),
    ("0500", "12084", "MLA Computerisation", 124328409,
     "Three departments: 0501 Headquarters P114,328,409, 0510 Animal Health P8,500,000 and 0513 Aquaculture and Apiculture P1,500,000. **The ministry's supply speech itemises only BAITS P8,500,000 and an IGIS upgrade P800,000** — P9.3m of a P124.3m line — so the speech is not a substitute for the volume here."),
    ("0300", "12041", "MoF Computerisation", 123172400,
     "The **National e-Procurement System** is due “beginning of 2027” off a strategy approved 17 June 2025. The Public Procurement Regulatory Authority stated in March 2026 that it “lacked real-time data on procurement transactions” and could not track a transaction between stages, against an FY2024/25 procurement aggregate of 78,800 tenders worth P33.5 billion (12.4% of GDP)."),
    ("2300", "12461", "Information and Communications Technology", 107000000,
     "Two departments: 2310 Road Transport Services P67,000,000 and 2311 Government Fleet Management P40,000,000, summing to the P107,000,000 the ministry's supply speech states. It funds the Driver Licensing, Vehicle Registration and Licensing, Road Transport Permit and Road Worthiness systems, which the minister describes as “obsolete and highly vulnerable to manipulation”."),
    ("0400", "12061", "Computerisation", 42019862,
     "**The first year a Botswana budget document prices the national identity system.** The Committee of Supply speech of 24 February 2026 itemises the line: **Electronic National Identification System (Biometric Omang) P31,700,000**; Development of a Library Management System P2,024,000; Computerisation of the Records Management System (NARMS) P2,195,863. The speech also records that the Electronic Identification System project “has not progressed due to change of scope to a broader digital identity ecosystem”. Separately, P108,505,050 of **recurrent** money covers Omang card production and maintenance of the Births and Deaths Registration System and the National Identification System."),
    ("1100", "12244", "MoH Computerisation", 28934000,
     "The Committee of Supply speech describes a **Health Information Exchange** with a **Client Registry keyed on the Omang or passport number** and a Facilities Registry, both “ready for deployment” — the clearest statement of a data-exchange layer any Botswana budget document has carried."),
    ("3300", "12601", "MoHE Computerisation", 16000000,
     "The ministry reports that its Labour Market Information System has **completed integration with the National Identification System**, CIPA and the 1Gov SMS Gateway."),
    ("0700", "12122", "MTE Computerisation", 12853196, ""),
    ("2000", "12403", "MET Computerisation", 10033212,
     "Department 2004 Meteorological Services only; the other three departments carrying project 12403 are nil."),
    ("3400", "12621", "MoSA Computerisation", 7800000, ""),
    ("1200", "12263", "AoJ Computerisation", 6250000,
     "A replacement **court records system** is being built “following the collapse of the old one”, and the speech records that digital tools are being developed “with assistance secured from SecFin Africa” — an external party financing a core justice system, which is an origin-gate case the budget document does not resolve. The ministry's whole development budget is P24,286,412, of which this line is the identifiable digital part."),
    ("2100", "12423", "Industrial Court-ICT Development", 5500000,
     "The Industrial Court has developed its **own** court management system with secure online filing, due within Q1 FY2026/27 — a third separate case-management build, alongside the Administration of Justice's and the Ombudsman's, with no stated interoperability between them."),
    ("3100", "12562", "OTR-ICT Development", 4564988,
     "The re-tendered **Confiscated Property and Asset Management (CPAM) system**. Note that the supply speech's P24,564,988 is the **department total**, which adds P20,000,000 of infrastructure to this P4,564,988 ICT line."),
    ("2900", "12523", "MJCS-ICT Development", 4006530, ""),
    ("3500", "12643", "Prisons - ICT Development", 1800000,
     "Organisation 3500 was carved out of 2900 at 2026-04-01, taking P906,692,740 of recurrent with it; organisation 2900's recurrent falls from P1,015,314,690 to P153,295,560. **A Botswana justice series keyed on organisation 2900 breaks here.**"),
    ("1700", "12362", "Ombuds ICT Development", 0,
     "**Nil.** The project exists in the NDP 12 schedule with a total estimated cost of P55,800,000 and is appropriated nothing for FY2026/27 — while the Ombudsman's **Case Management System has not been operational since April 2025**, the whole of FY2025/26, “due to persistent system errors”. Its phase 2 was to integrate the system with the 1Gov Portal for public case registration. Recorded as a stated nil, per the spec."),
]
for org, code, proj, app, note in XV26:
    extra = [note] if note else []
    rec(2026, org, code, "appropriated", capital=app, total=app, scope="whole",
        label="project %s « %s », development estimate: P%s" % (code, proj, format(app, ",")),
        desc=proj + ".",
        basis="Explicit project title in the Development Fund estimates — a dedicated ministry computerisation or ICT development project, whose whole stated purpose is the digitisation of that body's business",
        doc=VOL26, locator="ESTIMATED DEVELOPMENT EXPENDITURE BY PROJECT 2026-27, organisation %s, project %s" % (org, code),
        notes=extra + ["Cross-vote computerisation and ICT across seventeen organisations totals **P895,462,597** for FY2026/27, against the digital ministry's own ICT project at P251,000,000 — **cross-vote is 78.1% of Botswana's named digital capital, a third consecutive year above half and the highest yet.**",
                       "**This corrects the sweep's own figure.** The FY2026/27 sweep built its cross-vote table from the Committee of Supply speeches and reached P380,519,862 (60.3%); the estimates volume gives P895,462,597, 2.35x that, because the speeches itemise selectively and several ministries — 0600, 0300, 0700, 2900, 3500 — either publish no speech or do not name their computerisation line in it. **The volume is the instrument; a speech is a commentary on it.**"])

rec(2026, "1600", "12341-evr", "appropriated", capital=50000000, total=50000000, scope="whole",
    label="Review of Electoral Processes — installation of electronic voter registration systems: P50,000,000",
    desc="Review of Electoral Processes project — “the project involves installation of electronic voter registration systems and may straddle two or three financial years due to its technical complexities”.",
    basis="Sub-line of a development project, stated with its own figure by the appropriating body: the Independent Electoral Commission's Committee of Supply speech names the amount and the purpose. The parent project (12341 Facilitation of Elections, P336,870,640) is not itself a digital line and is not recorded, so there is no double count",
    doc=COS_IEC, locator="Committee of Supply Speech 2026/2027, Independent Electoral Commission, para 37",
    notes=["**The first time Botswana's voter register has carried a price in any document the wiki holds.** The IEC's whole development budget is P336,870,640 — the volume's project `12341 Facilitation of Elections`, which the speech's figure matches exactly — of which P50,000,000 is this project and P11,692,000 is construction; the bulk of the remainder is an anticipated National Referendum on a Constitutional Court.",
           "Recorded from the supply speech rather than the estimates volume because **the volume names no systems**: at project grain the IEC has one line and it is called *Facilitation of Elections*. This is the pattern the whole FY2026/27 Committee of Supply season establishes — the volume carries the money, the speeches carry the names."])

rec(2026, "0100", "12001-ict", "appropriated", capital=2000000, total=2000000, scope="whole",
    label="Parliament Computerisation: P2,000,000",
    desc="“This project is meant to support the Parliament Digital [transformation]… It will enable us to digitize our processes, reduce manual [work]”.",
    basis="Sub-line of a development project, stated with its own figure and purpose in Parliament's Committee of Supply speech. The parent project (12001 Modernisation of National Assembly Facilities and Services, P8,000,000) is not itself a digital line and is not recorded, so there is no double count",
    doc=COS_PARL, locator="Committee of Supply Speech 2026/2027, Parliament, para 53 — `i. Computerisation (P2,000,000)`",
    notes=["Parliament passed the **Digital Services Bill, 2025 (Bill No. 23 of 2025)** in the same session; the Digital Services Act came into force 21 November 2025 with a 24-month compliance window."])

# --------------------------------------------------------------------------
# Emit
# --------------------------------------------------------------------------
def money(n):
    return format(n, ",")


def build(r):
    fy = r["fy"]
    label_fy, fy_start, fy_end = FY[fy]
    org, code, stage = r["org"], r["code"], r["stage"]
    orgname, slug, topics = ORG[org]
    topics = r["topics"] or topics
    pub, prec, datenote = STAGE_DATE[(fy, stage)]
    deal = "bwa-%d-%s-%s-%s" % (fy, org, code.lower(), stage)
    docstem, doctitle, docurl = r["doc"]
    title = "Botswana FY%s — organisation %s %s, %s" % (label_fy, org, orgname, r["label"])
    import re as _re
    slugpart = _re.sub(r"[^a-z0-9]+", "-", r["desc"].rstrip(".").lower()).strip("-")[:40]
    fname = "%s-%s-%s.md" % (pub, deal, slugpart)

    ents = sorted({slug, FISC_SLUG})
    entities = ", ".join("[%s]" % e for e in ents)

    if stage == "appropriated":
        stagetxt = "appropriated — voted in the estimates of expenditure for the year"
    elif stage == "revised":
        stagetxt = "revised — in-year revision restated in the following year's estimates volume"
    elif stage == "actual":
        stagetxt = "actual — expenditure recorded against the line"
    else:
        stagetxt = stage

    supp = "restated-total" if stage == "revised" else ""

    fm = ["---", "type: source", 'title: "%s"' % title.replace('"', "'"),
          "url: %s" % docurl,
          'publisher: "Ministry of Finance (Botswana)"',
          "published: %s" % pub,
          "date_precision: %s" % prec,
          "date_source: source",
          "places: [BWA]",
          "topics: %s" % topics,
          "entities: [%s]" % entities,
          "financier_slug: %s" % FISC_SLUG,
          "recipient_slug: %s" % slug,
          "lens: []",
          "deal_id: %s" % deal,
          "finance_origin: domestic-state",
          "state_level: national",
          'spending_tier_name: ""',
          'fiscal_year_label: "%s"' % label_fy,
          "fy_start: %s" % fy_start,
          "fy_end: %s" % fy_end,
          "budget_stage: %s" % stage,
          "budget_version: %s" % r["version"],
          "source_tier: budget-document",
          'supplementary_basis: "%s"' % supp,
          "scope_confidence: %s" % r["scope"],
          "is_transfer: false",
          "amount_total: %d" % r["total"]]
    if r["capital"] is not None:
        fm.append("amount_capital: %d" % r["capital"])
    if r["recurrent"] is not None:
        fm.append("amount_recurrent: %d" % r["recurrent"])
    fm += ["currency: BWP",
           "ingested: %s" % TODAY,
           "retrieved: 2026-07-25",
           "body_completeness: excerpt",
           "---", ""]

    b = ["# %s" % title, ""]
    b.append("Organisation **%s %s** of the Government of Botswana, %s, fiscal year %s "
             "(1 April %d – 31 March %d). The amount is **BWP %s**, wholly domestically financed."
             % (org, orgname, stagetxt, label_fy, fy, fy + 1, money(r["total"])))
    b.append("")
    b += ["## Deal record", "", "| Field | Value |", "|---|---|",
          "| Deal ID | %s |" % deal,
          "| Financier | %s |" % FISC,
          "| Spending entity | %s (organisation %s) |" % (orgname, org),
          "| Instrument | Budget appropriation — Botswana estimates of expenditure |",
          "| Budget stage | %s |" % stagetxt,
          "| Budget version | %s |" % r["version"]]
    if supp:
        b.append("| supplementary_basis | restated-total — the following year's volume restates the year's total, it does not state an increment |")
    b += ["| Fiscal year label | %s (April–March) |" % label_fy,
          "| fy_calendar | gregorian |",
          "| Amount (domestic-state) | BWP %s |" % money(r["total"])]
    if r["capital"] is not None:
        b.append("| — development (capital) | BWP %s |" % money(r["capital"]))
    if r["recurrent"] is not None:
        b.append("| — recurrent | BWP %s |" % money(r["recurrent"]))
    b += ["| Excluded as external (origin gate) | BWP 0 |",
          "| funding_source | domestic-revenue |",
          "| amount_scale | Pula, full units — no multiplier anywhere in the volume; stored as printed |",
          "| admin_head | Organisation %s — %s |" % (org, orgname),
          "| admin_head_code | %s |" % org,
          "| programme | %s |" % r["desc"].rstrip("."),
          "| programme_code | %s |" % code,
          "| classification_labels | %s |" % r["classlabels"],
          "| econ_class | %s |" % r["econ"],
          "| scope_confidence | %s |" % r["scope"],
          "| scope_basis | %s |" % r["basis"],
          "| vendor | — (not named) |",
          "| doc_type | budget-estimates |",
          "| doc_locator | %s |" % r["locator"],
          ""]
    b += ["## Description", "", r["desc"], ""]
    b += ["## Source", "",
          "*%s*, Ministry of Finance, Botswana — <%s>. Companion source page: `budget-archive/BWA/%d/%s-companion.md`. Extracted tables: `budget-archive/BWA/%d/`."
          % (doctitle, docurl, fy, docstem, fy), ""]
    b += ["## Notes", ""]
    b.append("- **Origin gate applied at capture.** " + DDF)
    b.append("- **Scale proved, not assumed.** " + SCALE)
    b.append("- **`published` anchors on the appropriating event** — %s (`CLAUDE.md` → *Currency*)." % datenote)
    for n in r["notes"]:
        b.append("- " + n)
    b.append("- **`amount_usd` left blank.** The wiki holds no named fiscal-year-average BWP/USD rate, and the driver forbids spot-converting a fiscal-year figure. Carried in the announcing state's own currency only.")
    b.append("")
    return fname, "\n".join(fm) + "\n".join(b) + "\n", deal


os.makedirs(NEW, exist_ok=True)
seen = set()
log = []
for r in R:
    fname, text, deal = build(r)
    assert deal not in seen, "duplicate deal_id " + deal
    seen.add(deal)
    with open(os.path.join(NEW, fname), "w", encoding="utf-8") as f:
        f.write(text)
    log.append((deal, fname, r))
print("wrote %d records" % len(log))

# run-log rows
with open("documentation/domestic-finance-run-log.csv", "a", encoding="utf-8") as f:
    for deal, fname, r in log:
        orgname, slug, _ = ORG[r["org"]]
        f.write("%s,%s,BWA,national,%d,%s,%s,domestic-state,domestic-revenue,%s,false,%d,BWP,\"%s\",,\n"
                % (deal, fname, r["fy"], r["stage"], r["version"], r["scope"],
                   r["total"], r["locator"].replace('"', "'")))
print("appended %d run-log rows" % len(log))
