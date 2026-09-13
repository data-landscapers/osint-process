# -*- coding: utf-8 -*-
"""One-shot generator for the BEN FY2024-FY2026 domestic-state finance records.

Written by the 2026-07-25 budget-extract pass over new-budget/BEN/{2024,2025,2026}.
Kept in scripts/ so the record set is reproducible and auditable against the
archived CSVs in budget-archive/BEN/.
"""
import os, sys

sys.stdout.reconfigure(encoding="utf-8")
NEW = "new"

LAW = {
    2024: ("loi n° 2023-01 du 20 décembre 2023 portant loi de finances pour la gestion 2024", "2023-12-20"),
    2025: ("loi n° 2024-34 du 12 décembre 2024 portant loi de finances pour la gestion 2025", "2024-12-12"),
    2026: ("loi n° 2025-22 du 4 décembre 2025 portant loi de finances pour la gestion 2026", "2025-12-04"),
}
VOL25 = ("Tableaux de classifications croisées des dépenses de l'État sur la période pluriannuelle 2022-2027, budget LF 2025",
         "https://budgetbenin.bj/wp-content/uploads/2025/01/Tableaux-de-Classifications-croisees-des-depenses-de-l-Etat-sur-la-periode-pluriannuelle-2022-2027-budget-LF-2025.xlsx",
         "2025-01-16-ben-tableaux-classifications-croisees-lf-2025", "2025", "lf2025")
VOL26 = ("Tableaux de classifications croisées des dépenses de l'État sur la période pluriannuelle 2022-2028, budget LF 2026",
         "https://budgetbenin.bj/wp-content/uploads/2026/02/Tableaux-de-Classifications-croisees-des-depenses-de-l-Etat-sur-la-periode-pluriannuelle-2022-2028-budget-LF-2026.xlsx",
         "2026-02-06-ben-classifications-croisees-2022-2028-lf-2026", "2026", "lf2026")
VOL = {2024: VOL25, 2025: VOL25, 2026: VOL26}

PLFR_URL = "https://budgetbenin.bj/wp-content/uploads/2026/06/Note-de-presentation-du-PLFR-2026.pdf"
PLFR_TITLE = "Note de présentation du projet de loi de finances rectificative pour la gestion 2026"

TOTALS = {
    2024: "2 551 700 000",
    2025: "2 778 519 000, with a stated 1 200 000 residual",
    2026: "3 065 132 710, no residual",
}

P = {
    "111": dict(
        vo="Numérique", slug="numerique",
        mlabel="Ministère du Numérique et de la Digitalisation (M.N.D)",
        mslug="ministry-of-digital-benin",
        topics="[dpi.govtech, infra.connect, finance.budget]", scope="whole",
        basis="Budget programme whose entire stated purpose is digital transformation — the sector programme of the ministry responsible for le numérique",
    ),
    "100": dict(
        vo="Pilotage et soutien aux services du MND", slug="pilotage-mnd",
        mlabel="Ministère du Numérique et de la Digitalisation (M.N.D)",
        mslug="ministry-of-digital-benin",
        topics="[gov.policy, finance.budget]", scope="partial",
        basis="Administration and steering programme of the digital ministry; carries the ministry's own running costs, which serve both the digital (111) and media (109) programmes — digital share not separable and deliberately not apportioned",
    ),
    "109": dict(
        vo="Médias", slug="medias",
        mlabel="Ministère du Numérique et de la Digitalisation (M.N.D)",
        mslug="ministry-of-digital-benin",
        topics="[infra.connect, finance.budget]", scope="partial",
        basis="Media programme of the digital ministry; contains the télévision numérique terrestre (TNT) switchover build and media modernisation alongside non-digital broadcast subsidy — digital share not separable and deliberately not apportioned",
    ),
    "044": dict(
        vo="Modernisation de l'administration publique", slug="modernisation-administration-publique",
        mlabel="Ministère du Travail et de la Fonction Publique (M.T.F.P)",
        mslug="ministere-travail-fonction-publique-benin",
        topics="[dpi.govtech, finance.budget]", scope="whole",
        basis="Programme narrative, PAP 2026 conclusion (verbatim): « mettre en place les outils informatiques nécessaires afin d'assurer une certaine célérité dans la prise des actes ainsi que l'accessibilité aux informations et actes par les agents de l'État et les citoyens à partir de n'importe quel point du territoire national »",
    ),
    "108": dict(
        vo="Modernisation des régies financières", slug="modernisation-regies-financieres",
        mlabel="Ministère de l'Économie et des Finances (M.E.F) — compte d'affectation spéciale",
        mslug="ministere-economie-finances-benin",
        topics="[dpi.govtech, finance.budget]", scope="whole",
        basis="Ring-fenced special-appropriation programme for the modernisation of the revenue administrations (DGI, Douanes, Trésor) — tax and customs systems funded outside the ordinary ministry votes",
    ),
    "014": dict(
        vo="Dotation pour l'Autorité de Protection des Données à Caractère Personnel", slug="apdp",
        mlabel="Autorité de Protection des Données à Caractère Personnel (APDP)",
        mslug="apdp-benin",
        topics="[gov.protect, finance.budget]", scope="whole",
        basis="Single-mandate body carve-out (driver → Scope): the APDP's entire statutory mandate is personal-data protection, so its whole dotation is the digital line and the figure is not recoverable from any sub-line",
    ),
}

# (fy, code) -> (recurrent, capital_domestic, ext_dons, ext_prets) in FCFA units
ORD = {
    (2024, "111"): (125678000, 6530725000, 2388571000, 3656448000),
    (2024, "100"): (2495650000, 0, 0, 0),
    (2024, "109"): (6461195000, 2698282000, 0, 0),
    (2024, "044"): (1545017000, 200000000, 165000000, 0),
    (2024, "108"): (6000000000, 0, 0, 0),
    (2024, "014"): (488277000, 0, 0, 0),
    (2025, "111"): (150645000, 6236213000, 0, 10042000000),
    (2025, "100"): (2401717000, 0, 0, 0),
    (2025, "109"): (6587521000, 3615870000, 0, 0),
    (2025, "044"): (1612438000, 200000000, 0, 0),
    (2025, "108"): (6000000000, 0, 0, 0),
    (2025, "014"): (638277000, 0, 0, 0),
    (2026, "111"): (135938181, 5736213232, 0, 6500000000),
    (2026, "100"): (2184235167, 0, 0, 0),
    (2026, "109"): (7454237919, 5227411054, 0, 0),
    (2026, "044"): (1579754024, 200000000, 0, 0),
    (2026, "108"): (6000000000, 0, 0, 0),
    (2026, "014"): (738277000, 0, 0, 0),
}

# FY2026 execution at 30/04/2026: code -> (ord_recurrent, ord_capital, engagement_gross, taux_eng_gross, taux_ord_gross)
ACT = {
    "111": (15622968, 61625000, 80075082, "0.65", "0.62"),
    "100": (439474918, 0, 712468402, "32.62", "20.12"),
    "109": (60014487, 174432356, 2368013705, "18.67", "1.85"),
    "044": (92244238, 0, 136680983, "7.68", "5.18"),
    "108": (957413666, 0, 1597809166, "26.63", "15.96"),
    "014": (184569250, 0, 184569250, "25.00", "25.00"),
}

# PAP corroboration (gross CP, francs) for the three MND programmes and 044
PAP = {
    (2024, "100"): "2 495 649 850", (2025, "100"): "2 401 716 795", (2026, "100"): "2 184 235 167",
    (2024, "109"): "9 159 477 348", (2025, "109"): "10 203 390 887", (2026, "109"): "12 681 648 973",
    (2024, "111"): "12 701 421 802", (2025, "111"): "16 428 858 510", (2026, "111"): "12 372 151 413",
    (2024, "044"): "1 910 016 619", (2025, "044"): "1 812 438 146", (2026, "044"): "1 779 754 024",
}
PAP_DOC = {
    "100": "PAP VLF 2026 du MND", "109": "PAP VLF 2026 du MND", "111": "PAP VLF 2026 du MND",
    "044": "PAP VLF 2026 du MTFP",
}


def fm(n):
    return "{:,}".format(n).replace(",", " ")


def write(fn, text):
    with open(os.path.join(NEW, fn), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def appropriated(fy, code, d):
    rec, cap, dons, prets = ORD[(fy, code)]
    tot = rec + cap
    ext = dons + prets
    gross = tot + ext
    lawname, lawdate = LAW[fy]
    voltitle, volurl, volstem, volyr, voltag = VOL[fy]
    did = "ben-{}-{}-{}-appropriated".format(fy, d["slug"], code)
    title = ("Bénin LF {} — programme {} « {} », crédits ouverts "
             "(part domestique) : {} FCFA".format(fy, code, d["vo"], fm(tot)))
    if fy < 2026:
        scale = ("milliers de FCFA (thousand FCFA), as printed in the workbook (row 3); "
                 "stored normalised to units")
    else:
        scale = ("francs CFA (units), read from the PLFR execution annex; the workbook prints "
                 "milliers de FCFA and agrees to the thousand")
    if ext:
        parts = []
        if dons:
            parts.append("ressources extérieures (dons) {} FCFA".format(fm(dons)))
        if prets:
            parts.append("ressources extérieures (prêts) {} FCFA".format(fm(prets)))
        extline = ("External financing on the same programme is **excluded** from `amount_total` "
                   "by the origin gate: " + " + ".join(parts) +
                   " — gross programme {} FCFA.".format(fm(gross)))
    else:
        extline = ("The programme carries **no external financing** this year, so the domestic "
                   "figure is the whole programme.")
    pap = ""
    if (fy, code) in PAP:
        pap = ("\n- **Independently corroborated.** The {} — the ministry's own SIGFP-generated "
               "Projet annuel de performance, voted-law edition — gives this programme's gross "
               "crédits de paiement for {} as **{} FCFA**, matching the workbook to the franc. "
               "Extracted schedule at `budget-archive/BEN/2026/pap-vlf-2026-echeancier-cp-programmes-"
               "numeriques.csv`.".format(PAP_DOC[code], fy, PAP[(fy, code)]))
    disputed = ""
    if fy == 2024 and code == "044":
        disputed = ("\n- **⚠ Figure disputed by one held source, and resolved against it.** The DGB "
                    "open-data API's *Classification programatique* gives 10 205.448 M FCFA for this "
                    "programme and year — 5.3× the workbook. The workbook is preferred: the API's "
                    "own *Classification administrative* puts the whole M.T.F.P at 7 682.7 M (siding "
                    "with the workbook against itself), the workbook's three MTFP programmes sum "
                    "exactly to that total, and the MTFP's own PAP gives 1 910 016 619 FCFA to the "
                    "franc. Open brief: "
                    "`reviews/contradictions/open/2026-07-25-ben-programme-044-modernisation-"
                    "administration-2024.md`.")
    if code == "014":
        transfer = ("\n- **`is_transfer: false`.** The dotation is a transfer to an independent "
                    "authority, but the wiki holds no separate APDP board budget, so this line is the "
                    "only record of the money and counts normally (driver → *Transfers inside the "
                    "state*).")
    elif code == "108":
        transfer = ("\n- **`is_transfer: false`.** The programme is wholly *dépenses de transfert* to "
                    "the revenue administrations, whose own budgets the wiki does not hold, so the "
                    "transfer line is the only record of the money and counts normally.")
    else:
        transfer = ""
    moved = ""
    if fy == 2026 and code == "044":
        moved = ("\n- **The spending ministry was abolished mid-year.** Décret n° 2026-314 du 24 mai "
                 "2026 dissolved the MTFP and moved programme 044 to a new Ministère du Budget et des "
                 "Finances Publiques (MBFP). This record is keyed to the ministry that held the "
                 "programme when the loi de finances was enacted; any series keyed on ministry breaks "
                 "at 2026-05-24.")
    if fy == 2026 and code in ("111", "100", "109"):
        moved = ("\n- **The spending ministry was split mid-year.** Décret n° 2026-314 du 24 mai 2026 "
                 "split the MND into the MTDI (programmes 100 and 111, plus the national AI strategy) "
                 "and the MCM (programme 109, renamed *Communication et Médias*). This record is "
                 "keyed to the ministry that held the programme when the loi de finances was enacted.")
    if fy == 2026 and code == "108":
        moved = ("\n- **Proposed for abolition three months later.** The PLFR 2026 (9 June 2026) drops "
                 "programme 108 from the programme list entirely and zeroes it; two other special "
                 "funds are zeroed identically, so this reads as a comptes-spéciaux restructure "
                 "rather than a cut to digital spending. The enacted loi de finances rectificative "
                 "(loi n° 2026-10) is not held, so no `revised` record is built.")
    proposed_note = ""
    if fy == 2026:
        proposed_note = ("\n- **Proposed = enacted.** The PLF-stage edition of the same workbook "
                         "(2022-2028, budget PLF 2026, posted 2025-12-03) carries an identical figure "
                         "for this programme and an identical `TOTAL BUDGET DE L'ETAT` "
                         "(3 065 132 710 milliers de FCFA), so no separate `proposed` record is built "
                         "for it.")

    return did, lawdate, """---
type: source
title: "{title}"
url: {volurl}
publisher: Direction générale du Budget, Ministère de l'Économie et des Finances (Bénin)
published: {lawdate}
date_precision: day
date_source: source
places: [BEN]
topics: {topics}
entities: [[ministere-economie-finances-benin], [{mslug}], [direction-generale-budget-benin]]
financier_slug: ministere-economie-finances-benin
recipient_slug: {mslug}
lens: []
deal_id: {did}
finance_origin: domestic-state
state_level: national
spending_tier_name: ""
fiscal_year_label: "{fy}"
fy_start: {fy}-01-01
fy_end: {fy}-12-31
budget_stage: appropriated
budget_version: original
source_tier: budget-document
supplementary_basis: ""
scope_confidence: {scope}
is_transfer: false
amount_total: {tot}
amount_capital: {cap}
amount_recurrent: {rec}
currency: XOF
retrieved: 2026-07-25
body_completeness: excerpt
---

# {title}

Programme **{code} « {vo} »** of {mlabel}, as opened by {lawname}. The **domestically-financed** portion of the appropriation is **{tot_f} FCFA** — dépenses ordinaires {rec_f} plus dépenses en capital sur ressources intérieures {cap_f}.

## Deal record

| Field | Value |
|---|---|
| Deal ID | {did} |
| Financier | National fisc — Ministère de l'Économie et des Finances / Direction générale du Budget (Bénin) |
| Spending entity | {mlabel} |
| Instrument | Budget appropriation (programme line, loi de finances {fy}) |
| Budget stage | appropriated — crédits ouverts par la loi de finances |
| Budget version | original |
| Fiscal year label | {fy} (calendar year; gestion {fy}) |
| fy_calendar | gregorian |
| Amount (domestic-state) | XOF {tot_f} |
| — dépenses ordinaires | XOF {rec_f} |
| — dépenses en capital, ressources intérieures | XOF {cap_f} |
| Excluded as external (origin gate) | XOF {ext_f} |
| Gross programme, all financing sources | XOF {gross_f} |
| funding_source | domestic-revenue |
| amount_scale | {scale} |
| programme | {vo} |
| programme_code | {code} |
| admin_head | {mlabel} |
| classification_labels | Ministère / Programme — LOLF-style, per the loi organique n° 2013-14 du 27 septembre 2013 relative aux lois de finances |
| econ_class | Dépenses de personnel ; d'acquisitions de biens et services ; de transfert ; dépenses en capital — ressources intérieures / extérieures (dons) / extérieures (prêts) |
| scope_confidence | {scope} |
| scope_basis | {basis} |
| vendor | — (not named) |
| doc_type | budget-estimates |
| doc_locator | *{voltitle}*, sheet `Classif Prog-Admin-Eco`, row `{code}`, {fy} column block |

## Description

Programme {code} — {vo}. {mlabel}.

## Source

*{voltitle}* — Direction générale du Budget (Bénin), native XLSX, <{volurl}>. Companion source page: `{volstem}`. Extracted table: `budget-archive/BEN/{volyr}/{voltag}-classifications-croisees-{fy}.csv`.

## Development history

## Notes

- **Origin gate applied.** {extline} The workbook states the interior/exterior split per programme, so this is a documented split and not an apportionment (driver → *Origin — the double-counting gate*).
- **Reconciliation.** The volume's programme and dotation lines sum exactly to its printed `TOTAL BUDGET DE L'ETAT` for {fy} ({total} milliers de FCFA), and `ordinaires + capital = total` holds on this line.{pap}{disputed}{transfer}{moved}{proposed_note}
- **amount_usd left blank.** The XOF is pegged to the euro at a fixed 655.957, but no named fiscal-year-average XOF/USD rate is held and the driver forbids spot-converting a fiscal-year figure. Carried in the announcing state's own currency only.
- **`published` is the promulgation date of the appropriation act**, not the workbook's posting date (`CLAUDE.md` → *Currency*).
""".format(
        title=title, volurl=volurl, lawdate=lawdate, topics=d["topics"], mslug=d["mslug"],
        did=did, fy=fy, scope=d["scope"], tot=tot, cap=cap, rec=rec, code=code, vo=d["vo"],
        mlabel=d["mlabel"], lawname=lawname, tot_f=fm(tot), rec_f=fm(rec), cap_f=fm(cap),
        ext_f=fm(ext), gross_f=fm(gross), scale=scale, basis=d["basis"], voltitle=voltitle,
        volstem=volstem, volyr=volyr, voltag=voltag, extline=extline, total=TOTALS[fy],
        pap=pap, disputed=disputed, transfer=transfer, moved=moved, proposed_note=proposed_note,
    )


def actual(code, d):
    rec, cap, eng, teng, tord = ACT[code]
    tot = rec + cap
    app_rec, app_cap, _, app_prets = ORD[(2026, code)]
    app = app_rec + app_cap
    rate = 100.0 * tot / app
    did = "ben-2026-{}-{}-actual".format(d["slug"], code)
    title = ("Bénin gestion 2026 — programme {} « {} », exécution au 30 avril 2026 "
             "(part domestique ordonnancée) : {} FCFA".format(code, d["vo"], fm(tot)))
    ext_note = ""
    if app_prets:
        ext_note = ("\n- **The external tranche executed nothing.** The annex books the programme's "
                    "{} FCFA *Emprunt* line at zero engagement and zero ordonnancement at 30 April "
                    "2026, so the whole of the execution shown here is domestically financed. That "
                    "is why the domestic rate ({:.2f}%) is roughly double the gross rate the document "
                    "prints ({}%).".format(fm(app_prets), rate, tord))
    return did, """---
type: source
title: "{title}"
url: {plfr_url}
publisher: Direction générale du Budget, Ministère de l'Économie et des Finances (Bénin)
published: 2026-04-30
date_precision: day
date_source: source
places: [BEN]
topics: {topics}
entities: [[ministere-economie-finances-benin], [{mslug}], [direction-generale-budget-benin]]
financier_slug: ministere-economie-finances-benin
recipient_slug: {mslug}
lens: []
deal_id: {did}
finance_origin: domestic-state
state_level: national
spending_tier_name: ""
fiscal_year_label: "2026"
fy_start: 2026-01-01
fy_end: 2026-12-31
budget_stage: actual
budget_version: original
source_tier: budget-document
supplementary_basis: ""
scope_confidence: {scope}
is_transfer: false
amount_total: {tot}
amount_capital: {cap}
amount_recurrent: {rec}
currency: XOF
retrieved: 2026-07-25
body_completeness: excerpt
---

# {title}

Cumulative execution of programme **{code} « {vo} »** for the period **1 January – 30 April 2026**, as reported by the SIGFP output embedded in the *Note de présentation du PLFR 2026*. Ordonnancements on the domestically-financed portion: **{tot_f} FCFA** against a domestic appropriation of {app_f} FCFA — an execution rate of **{rate:.2f}%** at one third of the year.

## Deal record

| Field | Value |
|---|---|
| Deal ID | {did} |
| Financier | National fisc — Ministère de l'Économie et des Finances / Direction générale du Budget (Bénin) |
| Spending entity | {mlabel} |
| Instrument | Budget execution (ordonnancement against the programme line) |
| Budget stage | actual — *mandat ordonnancé*, cumulative 01/01/2026 to 30/04/2026 |
| Budget version | original |
| Fiscal year label | 2026 (calendar year; gestion 2026) |
| fy_calendar | gregorian |
| Amount ordonnancé (domestic-state) | XOF {tot_f} |
| — dépenses ordinaires | XOF {rec_f} |
| — dépenses en capital (contribution budgétaire) | XOF {cap_f} |
| Engagements, gross programme | XOF {eng_f} |
| Domestic appropriation for the year | XOF {app_f} |
| **Execution rate, domestic** | **{rate:.2f}%** at 30/04/2026 |
| Execution rate as printed, gross programme | taux eng. {teng}% / taux ord. {tord}% |
| All-programmes comparator, as printed | taux eng. 19.87% / taux ord. 15.43% |
| funding_source | domestic-revenue |
| amount_scale | francs CFA (units) — unlabelled in this annex; verified against the workbook's milliers figures |
| programme | {vo} |
| programme_code | {code} |
| admin_head | {mlabel} |
| econ_class | Dépenses ordinaires (DO) / dépenses en capital (DC) — contribution budgétaire vs emprunt |
| scope_confidence | {scope} |
| scope_basis | {basis} |
| vendor | — (not named) |
| doc_type | implementation-report |
| doc_locator | *{plfr_title}*, Annexe n° 2, *Situation d'exécution du budget par programme*, gestion 2026, période du 01/01/2026 au 30/04/2026, line `{code}` |

## Description

Programme {code} — {vo}. {mlabel}. Exécution cumulée au 30 avril 2026.

## Source

*{plfr_title}* (9 June 2026, 54 pp, native text), Annexe n° 2 — raw SIGFP output embedded in the rectificative's explanatory note, <{plfr_url}>. Extracted table: `budget-archive/BEN/2026/plfr-2026-execution-par-programme-lignes-numeriques.csv`.

## Development history

## Notes

- **This is a four-month execution point, not a full-year outturn.** Benin has never published a Rapport annuel de performance at programme grain; this annex is the first per-programme executed figure the wiki holds for the country. A Q2/Q3 point should be sought before the rate is read as a trend.
- **Origin gate applied to the execution side too.** The annex decomposes capital into *Contribution Budgétaire* (domestic) and *Emprunt* (external), so the domestic portion of both the appropriation and the ordonnancement is documented rather than apportioned.{ext_note}
- **Arithmetic verified.** Every line used here cross-foots against the document's own printed columns: `dotation initiale CP − engagement CP = montant disponible CP`, `engagement CP / dotation initiale CP = taux eng.` and `mandat ordonnancé / dotation initiale CP = taux ord.` all hold exactly.
- **A `revised` stage exists and is identical.** The annex's `DOTATION FINALE` equals `DOTATION INITIALE` for this programme at 30 April 2026 — no credit movement had touched it in the first four months — so no separate `revised` record is built.
- **⚠ 1 000× trap in the parent document.** Annexe n° 1 (pp. 19–29) prints *« en milliers de francs CFA »* over figures that are in francs. Annexe n° 2, used here, is in francs and unlabelled. Both were checked against the workbook before use.
- **amount_usd left blank**, per the appropriation records for the same year.
""".format(
        title=title, plfr_url=PLFR_URL, topics=d["topics"], mslug=d["mslug"], did=did,
        scope=d["scope"], tot=tot, cap=cap, rec=rec, code=code, vo=d["vo"], mlabel=d["mlabel"],
        tot_f=fm(tot), rec_f=fm(rec), cap_f=fm(cap), eng_f=fm(eng), app_f=fm(app), rate=rate,
        teng=teng, tord=tord, basis=d["basis"], plfr_title=PLFR_TITLE, ext_note=ext_note,
    )


def main():
    n = 0
    for fy in (2024, 2025, 2026):
        for code, d in P.items():
            did, lawdate, body = appropriated(fy, code, d)
            write("{}-{}.md".format(lawdate, did), body)
            n += 1
    for code, d in P.items():
        did, body = actual(code, d)
        write("2026-04-30-{}.md".format(did), body)
        n += 1
    print("wrote", n, "records to", NEW)


if __name__ == "__main__":
    main()
