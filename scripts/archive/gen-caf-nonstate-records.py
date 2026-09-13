#!/usr/bin/env python3
"""Four CAF finance records the ingest finance branch (INGEST.md §2a) produced from
reporting rather than from a budget document: three `non-state` flows and one
own-source regulator budget. Each passed the five-fact test in
`wiki/finance-record-spec.md`; the origin gate decided which dataset it belongs to.
"""
import io
import os

RECS = [
    dict(
        fn="2024-04-08-caf-undp-2024-digitalisation-administration-publique-phase-2.md",
        title="UNDP signs a US$1,600,000 agreement with the Central African finance ministry for phase 2 of Digitalisation de l'administration publique",
        url="https://oubanguimedias.com/2024/04/14/le-pnud-et-le-gouvernement-centrafricain-signent-un-accord-de-1-6-millions-de-dollars-pour-le-projet-de-digitalisation/",
        publisher="Oubangui Médias",
        published="2024-04-08",
        topics="finance.new, dpi.govtech, dpi.registry",
        entities=["undp", "ministere-des-finances-et-du-budget-rca"],
        financier="undp",
        recipient="ministere-des-finances-et-du-budget-rca",
        deal_id="caf-undp-2024-digitalisation-administration-publique-p2",
        origin="non-state",
        amount=1600000,
        currency="USD",
        scope="whole",
        body=(
            "The **United Nations Development Programme** and the Central African Republic's "
            "**Ministère des Finances et du Budget** signed a financing agreement of "
            "**US$1,600,000** on **8 April 2024**, for phase 2 of *Digitalisation de "
            "l'administration publique en RCA* — consolidating and bringing into full operation "
            "the four platforms funded under phase 1, and supporting the **e-cadastre** pilot."
        ),
        table=[
            ("Financier", "United Nations Development Programme"),
            ("Recipient", "Ministère des Finances et du Budget (République Centrafricaine)"),
            ("Instrument", "Financing agreement (accord de financement)"),
            ("Amount", "US$1,600,000"),
            ("Event date", "2024-04-08 — the signature"),
            ("Purpose", "Phase 2 of *Digitalisation de l'administration publique en RCA*: full operationalisation of the four platforms, and the e-cadastre"),
            ("Prior phase", "US$600,000, lettre d'accord signed 2023 — stated by the minister as « un peu plus de trois cents soixante millions de francs CFA »"),
            ("source_tier", "reporting"),
        ],
        notes=[
            "**Origin gate: `non-state`.** UNDP money spent inside a Central African ministry is "
            "not the Central African state's own resource, so it belongs to the non-state dataset "
            "even though it finances a national vote (driver → *Origin*). Recording it "
            "`domestic-state` would double-count it against the budget lines it pays for.",
            "**Definite-match found nothing.** The wiki holds no prior UNDP record for this "
            "country, so this is a new record rather than a merge. The only held CAF financier "
            "record is the World Bank's *Public Sector Digital Governance Project* (2022), which "
            "is a different instrument.",
            "**This is the counterpart to the budget finding.** The FY2025 and FY2026 estimates "
            "volumes show the finance ministry's *Projet de numérisation* carried entirely in the "
            "`Dons` column at 200 000 milliers a year, funder unnamed. This is one of the funders.",
        ],
    ),
    dict(
        fn="2024-11-13-caf-france-2024-appui-budgetaire-reformes-mfb-simba-sydonia-etax.md",
        title="France earmarks FCFA 3.28 billion of a €10m budget-support convention to the Central African finance ministry's reforms — Si_mba, SYDONIA World and e-TAX",
        url="https://abangui.com/",
        publisher="Ministère des Finances et du Budget (RCA), relayé par abangui.com",
        published="2024-11-13",
        topics="finance.new, dpi.govtech",
        entities=["government-of-france", "ministere-des-finances-et-du-budget-rca"],
        financier="government-of-france",
        recipient="ministere-des-finances-et-du-budget-rca",
        deal_id="caf-france-2024-appui-budgetaire-reformes-mfb",
        origin="non-state",
        amount=3280000000,
        currency="XAF",
        scope="whole",
        body=(
            "The **Government of France** and the Central African Republic's **Ministère des "
            "Finances et du Budget** signed a budget-support convention on **13 November 2024**. "
            "Of the total, the French ambassador stated that **FCFA 3,28 billion is earmarked to "
            "the finance ministry's reforms**, which the ministry's own account names as the "
            "implementation of **Si_mba, SYDONIA World and e-TAX**."
        ),
        table=[
            ("Financier", "Government of France (budget support, signed by the ambassador)"),
            ("Recipient", "Ministère des Finances et du Budget (République Centrafricaine)"),
            ("Instrument", "Convention d'appui budgétaire"),
            ("Amount (digital earmark)", "FCFA 3,280,000,000"),
            ("Amount (whole convention)", "€10 million, reported as about FCFA 6.55 billion — a source-stated conversion at the November 2024 rate"),
            ("Other earmarks stated", "FCFA 1,97 bn to clearing domestic arrears for schoolbook distribution; FCFA 1,3 bn as France's contribution to the local elections"),
            ("Event date", "2024-11-13 — the signature"),
            ("Named systems", "Si_mba (budget preparation and execution), SYDONIA World (customs), e-TAX"),
            ("source_tier", "official-statement"),
        ],
        notes=[
            "**Origin gate: `non-state`, and this is the textbook case the gate exists for.** "
            "Budget support arrives as general revenue and is spent through national votes, so it "
            "looks domestic in every budget document. It is not the state's own resource. The "
            "amount recorded is the **stated earmark**, not an apportioned share of the €10m — "
            "the driver forbids computing a digital share of a mixed line.",
            "**It prices what the estimates volumes leave unpriced.** The same three systems — "
            "Si_mba, SYDONIA World, e-TAX — appear in the FY2026 programme budget at FCFA "
            "10 000 000, 420 000 000 and 3 000 000 respectively. One year of French support to "
            "the reform is roughly eight times the state's own recurring spend on the systems.",
            "**Currency.** Carried in FCFA, the currency the earmark was announced in "
            "(`CLAUDE.md` → *Currency*). The €10m headline is a second announced figure in a "
            "second currency and is recorded in the table, not converted.",
        ],
    ),
    dict(
        fn="2026-04-15-caf-arcep-2026-projet-de-budget-proposed.md",
        title="Central African Republic FY2026 — ARCEP's own draft budget: FCFA 6.2 billion",
        url="https://www.agenceecofin.com/actualites-numerique/2104-137723-centrafrique-la-mise-en-uvre-effective-du-fonds-du-service-universel-prevue-pour-2026",
        publisher="Agence Ecofin",
        published="2026-04-15",
        topics="finance.budget, gov.standards, include.access",
        entities=["arcep-central-african-republic", "ministere-de-l-economie-numerique-des-postes-et-telecommunications-rca"],
        financier="arcep-central-african-republic",
        recipient="arcep-central-african-republic",
        deal_id="caf-2026-arcep-board-budget-proposed",
        origin="domestic-state",
        amount=6200000000,
        currency="XAF",
        scope="partial",
        state_level="regulator",
        tier_name="Autorité de Régulation des Communications Electroniques et de la Poste (ARCEP)",
        stage="proposed",
        body=(
            "The **Autorité de Régulation des Communications Electroniques et de la Poste** "
            "presented its **draft budget for 2026** at a session on **15 April 2026**, at "
            "**FCFA 6,2 billion** (about US$11.2 million). Effective implementation of the "
            "**fonds de service universel** was among the priorities set out."
        ),
        table=[
            ("Financier", "ARCEP — own resources (regulatory and licence fee income)"),
            ("Spending entity", "ARCEP (Autorité de Régulation des Communications Electroniques et de la Poste)"),
            ("Instrument", "Board-approved draft budget (projet de budget)"),
            ("Budget stage", "proposed — presented to the budget session of 15 April 2026, not shown as adopted"),
            ("Fiscal year label", "2026 (calendar year)"),
            ("Amount", "FCFA 6,200,000,000"),
            ("funding_source", "own-source"),
            ("state_level", "regulator"),
            ("scope_confidence", "partial"),
            ("scope_basis", "Mandate test, not name test: ARCEP regulates electronic communications *and* post, so its whole budget is not a digital line and the digital share is not separable."),
            ("source_tier", "reporting"),
        ],
        notes=[
            "**The first ARCEP budget figure the wiki has been able to obtain for this country.** "
            "The FY2024 sweep searched for one and found nothing: `arcep.cf` returns « Site en "
            "construction » and 404s on every path — the minister's 30 January 2026 address "
            "explains why, the regulator's institutional website being a World Bank-financed "
            "project not yet delivered — and ARCEP is absent from the state's own parapublic "
            "portfolio report.",
            "**Read alongside the state transfer, and date both.** The FY2026 estimates carry "
            "*Appui à l'ARCEP* at FCFA 1,6 bn (CDMT activity `8508303240000XXXX01`); the FY2025 "
            "estimates carried 1,4 bn. Set against this 6,2 bn draft, the fisc funds of the order "
            "of a quarter of the regulator, and did so in both years — **a level, not a change**. "
            "An earlier reading that put the FY2025 transfer at 0,5 bn, and so reported a rise "
            "from ~8% to ~26%, was wrong and is withdrawn (post-run note 28).",
            "**No double count with the state transfer record.** `caf-2026-85-8508303240000xxxx01-proposed` "
            "is the appropriation *to* ARCEP; this record is ARCEP's own spending budget. The "
            "compile pass counts the receiving body's own spend where both are held, so the "
            "transfer record carries `is_transfer: false` only because this record is `proposed` "
            "reporting rather than an adopted board budget — flagged here so the pair is not "
            "summed.",
            "**TRAP recorded on the FY2024 run and still live:** `arcep.ne` is **Niger's** ARCEP "
            "and its figures rank highly on CAR-phrased queries. This figure is CAR's.",
        ],
    ),
    dict(
        fn="2026-07-16-caf-greenline-technologies-2026-socatel-relance-data-center-tier-3.md",
        title="Greenline Technologies confirms a US$150 million recapitalisation of SOCATEL, including a Tier 3 data centre",
        url="https://www.lebrief.ma/afrique/centrafrique-la-relance-socatel-passe-a-150-millions-usd-100160257/",
        publisher="LeBrief",
        published="2026-07-16",
        topics="finance.new, infra.store, infra.connect",
        entities=["greenline-technologies", "socatel"],
        financier="greenline-technologies",
        recipient="socatel",
        deal_id="caf-greenline-2026-socatel-relance",
        origin="non-state",
        amount=150000000,
        currency="USD",
        scope="partial",
        body=(
            "**Greenline Technologies**, an American company, and the Central African government "
            "confirmed on **16 July 2026** the implementation of a protocole d'accord concluded in "
            "**September 2025** to recapitalise the state telecom operator **SOCATEL**. The "
            "announced investment is **US$150 million**, covering network and equipment "
            "modernisation and the construction of a **Tier 3 data centre**."
        ),
        table=[
            ("Financier", "Greenline Technologies (United States) — announced as the investor"),
            ("Recipient", "SOCATEL — Société Centrafricaine de Télécommunications (state operator)"),
            ("Instrument", "Protocole d'accord, September 2025, confirmed in implementation 16 July 2026"),
            ("Amount", "US$150,000,000"),
            ("Event date", "2026-07-16 — the confirmation meeting in Bangui"),
            ("Purpose", "Network and equipment modernisation; a Tier 3 data centre for domestic hosting"),
            ("source_tier", "reporting"),
        ],
        notes=[
            "**Origin gate: `non-state`.** The money is announced as an investment *by* Greenline, "
            "not an appropriation, so the fisc is not the financier. What the state budget "
            "actually carries for SOCATEL is FCFA 250 000 000 of the administration's unpaid "
            "telephone bills — `caf-2026-85-8508403160000xxxx09-proposed` — and nothing else. "
            "**No appropriation for this US$150m appears anywhere in three years of estimates.**",
            "**`scope_confidence: partial`** — telecom network modernisation is mostly "
            "connectivity infrastructure; the Tier 3 data centre is squarely in scope and is not "
            "separately priced, so the digital share is not separable.",
            "**Do not assume this is the same facility as the Huawei Tier III data centre** "
            "announced eight weeks earlier (26 May 2026) by a different route. Two national "
            "Tier III data centres are announced within eight weeks; nothing on file establishes "
            "that they are one project, and neither carries a visible appropriation.",
        ],
    ),
]

FY = {"2026": ("2026-01-01", "2026-12-31")}

for r in RECS:
    fm = ["---", "type: source", f'title: "{r["title"]}"', f"url: {r['url']}",
          f'publisher: "{r["publisher"]}"', f"published: {r['published']}",
          "date_precision: day", "date_source: source", "places: [CAF]",
          f"topics: [{r['topics']}]",
          "entities: [" + ", ".join(f"[{e}]" for e in r["entities"]) + "]",
          f"financier_slug: {r['financier']}", f"recipient_slug: {r['recipient']}",
          "lens: []", f"deal_id: {r['deal_id']}", f"finance_origin: {r['origin']}"]
    if r["origin"] == "domestic-state":
        fm += [f"state_level: {r['state_level']}", f'spending_tier_name: "{r["tier_name"]}"',
               'fiscal_year_label: "2026"', "fy_start: 2026-01-01", "fy_end: 2026-12-31",
               f"budget_stage: {r['stage']}", "budget_version: original",
               "source_tier: reporting", 'supplementary_basis: ""']
    fm += [f"scope_confidence: {r['scope']}", "is_transfer: false",
           f"amount_total: {r['amount']}", f"currency: {r['currency']}",
           "ingested: 2026-07-26", "retrieved: 2026-07-26", "body_completeness: excerpt", "---", ""]
    out = [f"# {r['title']}", "", r["body"], "", "## Deal record", "", "| Field | Value |", "|---|---|",
           f"| Deal ID | {r['deal_id']} |"]
    out += [f"| {k} | {v} |" for k, v in r["table"]]
    out += ["", "## Source", "",
            f"*{r['publisher']}* — <{r['url']}>. The full verbatim report is held at "
            f"`raw/` under its own filename; this page is the deal record built from it "
            f"(`INGEST.md` §2a).", "", "## Notes", ""]
    out += [f"- {n}" for n in r["notes"]]
    out.append("")
    io.open(os.path.join("new", r["fn"]), "w", encoding="utf-8", newline="").write(
        "\n".join(fm) + "\n".join(out))
print(f"{len(RECS)} non-budget-document finance records written to new/")
