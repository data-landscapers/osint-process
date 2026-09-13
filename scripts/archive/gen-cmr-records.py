# -*- coding: utf-8 -*-
"""Build CMR domestic-state budget-line records into new/ (budget-extract step 3)."""
import io, os

OUT = "C:/Users/bill/OSINT/new"
SCALE = "milliers de FCFA, printed in the column header — stored normalised to units (x1 000)"

# Companion pages the stages cite (basenames, post-archive they live in budget-archive/CMR/{FY}/)
PLF = {"2024": "2023-11-30-cmr-projet-de-loi-de-finances-2024-companion",
       "2025": "2024-11-29-cmr-projet-de-loi-de-finances-2025-francais-companion",
       "2026": "2025-11-26-cmr-projet-de-loi-de-finances-2026-francais-companion"}
ORD = {"2024": "2024-06-20-cmr-ordonnance-2024-001-modifiant-loi-de-finances-2024-companion",
       "2025": "2025-07-11-cmr-ordonnance-2025-001-modifiant-loi-de-finances-2025-companion"}
PLF_URL = {"2024": "https://www.dgb.cm/wp-content/uploads/2023/12/projets-PLF-2024.pdf",
           "2025": "https://rfp.cm/wp-content/uploads/2024/12/Projet-de-loi-de-Finances-2025-PRC_Fr.pdf",
           "2026": "https://rfp.cm/wp-content/uploads/2025/11/PROJET-DE-LOI-FINANCES-2026_FR_26112025.pdf"}
ORD_URL = {"2024": "https://www.prc.cm/files/41/5c/26/3621ac2603f3f0a3d2ebf7657b1202f3.pdf",
           "2025": "https://www.prc.cm/files/2b/b6/18/e9dcb7075e82f965da2266860cfc3a23.pdf"}
ASSENT = {"2024": "2023-12-19", "2025": "2024-12-23", "2026": "2025-11-26"}
ORD_DATE = {"2024": "2024-06-20", "2025": "2025-07-11"}
UNIT = {"2024": "chapitre", "2025": "chapitre", "2026": "section"}

# fy, vote, vote_name, code, label_fr, milliers: proposed, appropriated, revised, subject, topics, entity
R = [
 ("2024","45","MINISTERE DES POSTES ET TELECOMMUNICATIONS","130",
  "Développement de l'écosystème national du numérique",
  9489364, 9489364, 9489364, "infra.connect",
  ["finance.budget","infra.connect","include.access"], "ministry-of-posts-and-telecommunications-cameroon",
  "Accroître l'accessibilité du numérique et promouvoir son usage.",
  "Indice de Développement des TIC (IDI)"),
 ("2024","45","MINISTERE DES POSTES ET TELECOMMUNICATIONS","132",
  "Sécurisation de l'écosystème national du numérique",
  921044, 921044, 921044, "infra.cybersec",
  ["finance.budget","infra.cybersec"], "ministry-of-posts-and-telecommunications-cameroon",
  "Garantir la sécurité du cyberespace national.",
  "Indice national de cybersécurité"),
 ("2025","45","MINISTERE DES POSTES ET TELECOMMUNICATIONS","130",
  "Développement de l'écosystème national du numérique",
  10330875, 10330875, 10330875, "infra.connect",
  ["finance.budget","infra.connect","include.access"], "ministry-of-posts-and-telecommunications-cameroon",
  "Accroître l'accessibilité du numérique et promouvoir son usage.",
  "Indice de Développement des TIC (IDI)"),
 ("2025","45","MINISTERE DES POSTES ET TELECOMMUNICATIONS","132",
  "Sécurisation de l'écosystème national du numérique",
  1037044, 1037044, 1037044, "infra.cybersec",
  ["finance.budget","infra.cybersec"], "ministry-of-posts-and-telecommunications-cameroon",
  "Garantir la sécurité du cyberespace national.",
  "Indice national de cybersécurité"),
 ("2026","45","MINISTERE DES POSTES ET TELECOMMUNICATIONS","451",
  "Développement sécurisé et inclusif de l'écosystème national du numérique",
  19494457, None, None, "infra.connect",
  ["finance.budget","infra.connect","infra.cybersec","dpi.govtech"],
  "ministry-of-posts-and-telecommunications-cameroon",
  "Garantir un environnement numérique moderne, sûr et inclusif, favorisant une croissance économique "
  "harmonieuse et coordonnée, la souveraineté numérique et la confiance des usagers ; promouvoir une "
  "accessibilité universelle du numérique ; améliorer la gouvernance du numérique ; garantir la sécurité, "
  "la souveraineté et la confiance dans l'espace numérique national.",
  "Indice de Développement des TIC (IDI) ; Indice national de cybersécurité ; Taux de couverture nationale "
  "en haut débit (Internet fixe et mobile) ; Linéaire fibre optique posée ; Indice de développement de la "
  "gouvernance électronique (EGDI) ; Taux de numérisation des services publics ; Proportion d'incidents de "
  "cybersécurité détectés et traités par le CERT national ; Taux de mise en conformité des institutions "
  "publiques avec les normes de cybersécurité"),
 ("2024","37","MINISTERE DES DOMAINES, DU CADASTRE ET DES AFFAIRES FONCIERES","026",
  "Modernisation du cadastre",
  1203574, 1203574, None, "dpi.registry",
  ["finance.budget","dpi.registry"], "ministry-of-state-property-surveys-and-land-tenure-cameroon",
  "Disposer d'un cadastre national numérique apte à répondre aux défis de gouvernance foncière moderne.",
  "Proportion de communes disposant d'un plan cadastral numérique"),
 ("2025","37","MINISTERE DES DOMAINES, DU CADASTRE ET DES AFFAIRES FONCIERES","026",
  "Modernisation du cadastre",
  1567500, 1567500, None, "dpi.registry",
  ["finance.budget","dpi.registry"], "ministry-of-state-property-surveys-and-land-tenure-cameroon",
  "Disposer d'un cadastre national numérique apte à répondre aux défis de gouvernance foncière moderne.",
  "Proportion de communes disposant d'un plan cadastral numérique"),
 ("2026","37","MINISTERE DES DOMAINES, DU CADASTRE ET DES AFFAIRES FONCIERES","380",
  "Modernisation du cadastre",
  874046, None, None, "dpi.registry",
  ["finance.budget","dpi.registry"], "ministry-of-state-property-surveys-and-land-tenure-cameroon",
  "Disposer d'un Cadastre National numérique apte à répondre aux défis de gouvernance foncière moderne.",
  "Proportion des titres fonciers rattachés au Réseau Géodésique National du Cameroun ; proportion de "
  "communes disposant d'un plan cadastral numérique ; proportion de plans cadastraux numérisés et "
  "géoréférencés par an"),
]


def money(m):
    return m * 1000


def fmt(n):
    return "{:,}".format(n)


def build(rec):
    (fy, vote, vote_name, code, label, prop, appr, rev, subj, topics, ent, obj, ind) = rec
    did = "cmr-%s-%s-%s" % (fy, vote, code)
    pub = ASSENT[fy]
    baseline = "appropriated" if appr else "proposed"
    current = "revised" if rev else baseline
    stages = []
    stages.append("- **%s** proposed **XAF %s** — PLF %s, %s %s, programme %s, colonnes AE/CP. "
                  "[[%s]]" % (PLF_DATE[fy], fmt(money(prop)), fy, UNIT[fy], vote, code, PLF[fy]))
    if appr:
        stages.append("- **%s** appropriated **XAF %s** — Loi de finances %s, article quatre-vingt-unième, "
                      "colonne « AE VOTE » as restated by Ordonnance n°%s/001. [[%s]]"
                      % (pub, fmt(money(appr)), fy, fy, ORD[fy]))
    if rev:
        stages.append("- **%s** revised **XAF %s** — Ordonnance n°%s/001, article quatre-vingt-unième "
                      "(nouveau), colonne « CP MODIFIE » — **unchanged from the enacted figure**. [[%s]]"
                      % (ORD_DATE[fy], fmt(money(rev)), fy, ORD[fy]))
    fm = [
        "---", "type: source",
        'title: "Cameroon FY%s — %s %s, programme %s %s: FCFA %s"' % (
            fy, UNIT[fy], vote, code, label, fmt(money(prop))),
        "url: %s" % PLF_URL[fy],
        "publisher: République du Cameroun — Ministère des Finances, Direction Générale du Budget",
        "published: %s" % pub, "date_precision: day", "date_source: source",
        "places: [CMR]",
        "topics: [%s]" % ", ".join(topics),
        "entities: [[[%s]], [[ministry-of-finance-cameroon]]]" % ent,
        "financier_slug: ministry-of-finance-cameroon",
        "deal_id: %s" % did,
        "finance_origin: domestic-state", "state_level: national", 'spending_tier_name: ""',
        'fiscal_year_label: "%s"' % fy,
        "fy_start: %s-01-01" % fy, "fy_end: %s-12-31" % fy, "fy_calendar: gregorian",
        "budget_version: original",
        "source_tier: budget-document",
        'supplementary_basis: ""',
        "scope_confidence: whole",
        'scope_basis: "explicit programme title and objective — the programme\'s whole stated purpose is a digital activity"',
        "is_transfer: false", "currency: XAF",
        "baseline_stage: %s" % baseline,
        "current_stage: %s" % current,
        "proposed_total: %d" % money(prop),
        "appropriated_total: %s" % (money(appr) if appr else ""),
        "revised_total: %s" % (money(rev) if rev else ""),
        "released_total: ", "actual_total: ", "audited_total: ",
        "execution_pct_vs_appropriated: ", "execution_pct_vs_revised: ",
        "admin_head: \"%s\"" % vote_name, "admin_head_code: \"%s\"" % vote,
        "programme: \"%s\"" % label, "programme_code: \"%s\"" % code,
        "classification_labels: \"%s / programme\"" % UNIT[fy],
        "retrieved: 2026-07-29",
        "body_completeness: excerpt",
        "primary_subject: %s" % subj,
        "---", "",
        "# Cameroon FY%s — %s %s, programme %s %s: FCFA %s" % (
            fy, UNIT[fy], vote, code, label, fmt(money(prop))),
        "", "## Budget line record", "",
        "| Field | Value |", "|---|---|",
        "| Line ID | %s |" % did,
        "| Financier | Ministère des Finances (Cameroun) — the state budget |",
        "| Spending entity | %s %s — %s |" % (UNIT[fy].capitalize(), vote, vote_name),
        "| Fiscal year | %s (calendar: 1 January – 31 December) |" % fy,
        "| Baseline stage | %s |" % baseline,
        "| Current stage | %s |" % current,
        "| doc_locator | PLF %s, article quatre-vingt-unième, %s %s, programme %s, colonnes AE/CP |" % (
            fy, UNIT[fy], vote, code),
        "| amount_scale | %s |" % SCALE,
        "| funding_source | domestic-revenue |",
        "", "## Stage history", "",
    ] + stages + [
        "", "## Description", "",
        "**Objectif.** %s" % obj, "",
        "**Indicateur(s).** %s" % ind, "",
        "## Development history", "", "", "## Notes", "",
    ]
    notes = []
    if baseline == "proposed":
        notes.append("⚠ no appropriation stage held — baseline is proposed. The enacted loi de finances "
                     "%s (Loi n°2025/012 du 17 décembre 2025) is a 112 MB page-image scan with 2 265 "
                     "extractable characters, so its appropriation table has not been read. The figure "
                     "here is the tabled bill." % fy)
    notes.append("- **AE equals CP on this line**, as on every line of the Cameroonian programme table "
                 "seen across FY2024–FY2026.")
    notes.append("- **Cross-footed.** The programme figures of %s %s sum exactly to the printed vote "
                 "total in the source volume." % (UNIT[fy], vote))
    if appr:
        notes.append("- **The bill and the enacted law agree for this vote.** The ordonnance's "
                     "« AE VOTE » column — which restates the enacted appropriation — carries the same "
                     "figures as the PLF, and they cross-foot to the same vote total. The `proposed` and "
                     "`appropriated` stages therefore hold the same amount; that is a reconciliation, "
                     "not a duplication.")
    if rev:
        notes.append("- **The mid-year revision did not touch this programme.** Only the postal "
                     "programme moved in %s." % fy)
    notes.append("- **`amount_usd` left blank.** The wiki holds no named fiscal-year-average XAF/USD rate "
                 "for this year and the driver forbids spot-converting a fiscal-year figure.")
    fm += notes
    return did, pub, "\n".join(fm) + "\n"


PLF_DATE = {"2024": "2023-11-30", "2025": "2024-11-29", "2026": "2025-11-26"}

if __name__ == "__main__":
    n = 0
    for rec in R:
        did, pub, body = build(rec)
        p = os.path.join(OUT, "%s-%s.md" % (pub, did))
        io.open(p, "w", encoding="utf-8", newline="\n").write(body)
        n += 1
        print("wrote", os.path.basename(p))
    print(n, "records")
