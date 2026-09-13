#!/usr/bin/env python3
"""Build CAF domestic-state finance records into new/ from the extracted CAR volumes.

Sources, all native and all cross-footed before use:
  * PLF 2026 charges volume (602pp, SIM_ba) — proposed FY2026 + `Collectif 2025` column
  * CDMT sectoriels 2026 (183pp)            — FY2026 at activity grain, full francs
  * PLF 2025 charges volume (579pp, SIM_ba) — proposed FY2025 + `Collectif 2024` column

Origin gate: CAR prints it twice — as the `Financement interieur / exterieur (Dons |
Emprunt)` column set, and as the imputation's own last segment (`.11` domestic,
`.25` grant, `.44` loan). Every record below is `.11` / `Financement interieur`.
"""
import os
import re
import unicodedata

OUT = "new"
FIN = "ministere-des-finances-et-du-budget-rca"
MEN = "ministere-de-l-economie-numerique-des-postes-et-telecommunications-rca"

FY = {
    "2024": ("2024-01-01", "2024-12-31"),
    "2025": ("2025-01-01", "2025-12-31"),
    "2026": ("2026-01-01", "2026-12-31"),
}

DOCS = {
    "cdmt2026": dict(
        title="Cadre des Dépenses à Moyen Terme sectoriels 2026 à titre expérimental — Budget détaillé par activité",
        url="http://www.finances.gouv.cf/sites/default/files/2026-03/Cadre%20des%20D%C3%A9penses%20%C3%A0%20Moyen%20Terme%202026.pdf",
        companion="budget-archive/CAF/2026/2026-03-24-cdmt-sectoriel-2026.md",
        scale="francs CFA, full units (the CDMT prints full francs where the PLF prints milliers)",
        doc_type="budget-estimates",
    ),
    "plf2026": dict(
        title="Projet de loi de finances 2026 — volume des charges",
        url="http://www.finances.gouv.cf/sites/default/files/2025-11/PLF%202026.pdf",
        companion="budget-archive/CAF/2026/2025-11-18-plf-2026.md",
        scale="milliers de FCFA, printed in the column header — stored normalised to units (×1 000)",
        doc_type="budget-estimates",
    ),
    "plf2025": dict(
        title="Projet de loi de finances 2025 — volume des charges",
        url="http://www.finances.gouv.cf/sites/default/files/2024-12/3-%20PLF2025%2004%2012%202024.pdf",
        companion="budget-archive/CAF/2025/2024-12-10-plf-2025-charges.md",
        scale="milliers de FCFA, printed in the column header — stored normalised to units (×1 000)",
        doc_type="budget-estimates",
    ),
}

STAGE_NOTE = {
    "proposed": "proposed — tabled in the projet de loi de finances, not yet enacted",
    "revised": "revised — the enacted collectif budgétaire for the year, restated as the prior-year comparator column of the following year's projet de loi de finances",
}


def slug(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


# (key, fy, stage, section, code, label_fr, amount, scope, scope_basis, recipient, econ, titre, doc, locator, extra_notes)
R = []


def rec(fy, stage, section, code, label, amount, scope, basis, recipient, econ, titre, doc, locator="", notes=(), vendor="", transfer=False, published=None, secname=""):
    R.append(dict(fy=fy, stage=stage, section=section, code=code, label=label, amount=amount,
                  scope=scope, basis=basis, recipient=recipient, econ=econ, titre=titre,
                  doc=doc, locator=locator, notes=list(notes), vendor=vendor, transfer=transfer,
                  published=published, secname=secname))


S85 = "MINISTERE DE L'ECONOMIE NUMERIQUE, DES POSTES ET TELECOMMUNICATIONS"

# ---------------------------------------------------------------- FY2026 proposed, section 85 (CDMT grain)
P26 = dict(fy="2026", stage="proposed", doc="cdmt2026", published="2025-11-18", section="85", secname=S85)
rec(**P26, code="8508201230000XXXX01", label="Coordonner, animer et mis en œuvre de la politique d’Extension du réseau Internet fixe et mobile",
    amount=13_000_000, scope="whole", basis="Activity of programme 85082 INFRASTRUCTURES NUMERIQUES ET POSTALES, action 8508201 Extension du réseau Internet — fixe et mobile. Stated purpose is entirely a connectivity activity.",
    recipient=MEN, econ="AE 9 000 000 / CP 13 000 000", titre="")
rec(**P26, code="8508201240000XXXX02", label="Elaborer un plan directeur de Développement des infrastructures Nationales large bande",
    amount=2_000_000, scope="whole", basis="Activity label states a national broadband infrastructure master plan.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="")
rec(**P26, code="8508201240000XXXX03", label="Elaboration la cartographie Numérique de la couverture nationale en réseaux des télécoms/TIC",
    amount=2_000_000, scope="whole", basis="Activity label states digital mapping of national telecoms/ICT network coverage.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="")
rec(**P26, code="8508201240000XXXX04", label="Construction des boucles optiques urbaines (ACDD)",
    amount=300_000_000, scope="whole", basis="Activity label states construction of urban optical fibre loops, executed by the ACDD. This is the activity behind the PLF's otherwise unexplained `Transferts courants aux autres unités administratives` at imputation 85.88.00.21.120000.6439.11.",
    recipient="agence-centrafricaine-du-developpement-du-digital", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["**The CDMT is what makes this line legible.** In the legally binding PLF volume this appropriation reads only `Transferts courants aux autres unités administratives`; the activity label naming urban fibre loops exists only in the programme budget, which has no legal force."])
rec(**P26, code="8508201240000XXXX06", label="Raccorder de tous les chefs- lieux de préfectures à Bangui via le back Bône National à fibre Optique",
    amount=2_000_000, scope="whole", basis="Activity label states connection of every prefecture capital to Bangui over the national fibre backbone.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="",
    notes=["FCFA 2 million (about US$3,500) is the whole year's payment credit for connecting every prefecture capital to the national backbone."])
rec(**P26, code="8508202240000XXXX01", label="Coordonner, animer et évaluer les activités de Renforcement du raccordement Internet au réseau mondial",
    amount=2_000_000, scope="whole", basis="Sole activity of action 8508202 Renforcement du raccordement Internet au réseau Mondial.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="")
rec(**P26, code="8508301230000XXXX04", label="Coordonner, animer et évaluer les activités liées au développement du digitalisation des secteurs économiques",
    amount=13_000_000, scope="whole", basis="Sole activity of action 8508301 Digitalisation des services publics et postaux.", recipient=MEN, econ="AE 9 000 000 / CP 13 000 000", titre="")
rec(**P26, code="8508302", label="Renforcement de la sécurité des réseaux et système d’Information",
    amount=4_000_000, scope="whole", basis="A whole action of programme 85083 DIGITALISATION, recorded at action grain because both of its activities (Contrôler et Lutter contre les Fraudes des Communications; Faire les études et programmer les Projets) are network- and information-system security. Cross-foots: 2 000 000 + 2 000 000 = 4 000 000.",
    recipient=MEN, econ="AE 0 / CP 4 000 000", titre="",
    notes=["**This is the whole of the Central African Republic's budgeted network and information-system security for the year — FCFA 4 000 000, about US$7 000.** The same ministry transfers FCFA 1 600 000 000 to the telecom regulator in the same budget, a ratio of 400:1 against this line.",
           "The string `cyber` occurs zero times in the 602-page PLF volume and zero times in the 183-page CDMT. Neither the Agence Nationale de la Cybersécurité, created by the cybersecurity law of January 2024, nor the data-protection agency created by Loi n° 24.001 appears in either volume under any wording."])
rec(**P26, code="8508303240000XXXX01", label="Appui à l\"Autorité de Régulation de Communication Electronique et de la Poste (ARCEP)",
    amount=1_600_000_000, scope="partial", basis="Mandate test, not name test: ARCEP regulates electronic communications *and* post, so the transfer is multi-purpose and the digital share is not separable. Recorded `partial` rather than `whole`.",
    recipient="arcep-central-african-republic", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", transfer=False,
    notes=["**The single largest line in the digital ministry's budget, and 28,8% of its whole vote.** Binds to PLF imputation 85.88.00.20.120000.6439.11, which carries the identical figure.",
           "`is_transfer: false` because the wiki holds no ARCEP board budget, so this line is the only record of the money (driver → *Transfers inside the state*). ARCEP's own draft budget was reported at 6,2 mds FCFA on 15-Apr-2026; on those two figures the fisc would fund roughly a quarter of the regulator, but the figures are from different instruments and different dates and no single-year comparison is established."])
rec(**P26, code="8508303240000XXXX02", label="Promouvoir les services numériques et digitaliser l\"administration et les établissements publics",
    amount=2_000_000, scope="whole", basis="Activity label states promotion of digital services and digitisation of the administration and public establishments.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="")
rec(**P26, code="8508303240000XXXX04", label="Normaliser les communication electroniques",
    amount=2_000_000, scope="whole", basis="Activity label states standardisation of electronic communications.", recipient=MEN, econ="AE 0 / CP 2 000 000", titre="")
rec(**P26, code="8508304", label="Renforcement de la confiance numérique au niveau national",
    amount=2_000_000, scope="whole", basis="A whole programme-level line of section 85, single activity `Proposer et Mettre en oeuvre le Programme Global de …`. Recorded at that grain because the action and its activity carry the same figure.",
    recipient=MEN, econ="AE 0 / CP 2 000 000", titre="",
    notes=["**National digital trust is budgeted at FCFA 2 000 000 — about US$3 500 — for the year, for the country.** Loi n° 24.001 of January 2024 gave the digital ministry twelve months to stand up an independent data-protection agency with powers to fine up to 5% of turnover; at the extraction date that deadline is eighteen months past and no agency appears in three consecutive years of estimates."])
rec(**P26, code="8508401160000XXXX05", label="Assurer le fonctionnement du Secrétariat Permanent de la Gouvernance Nationale des Communications Electronique",
    amount=33_000_000, scope="whole", basis="Single-mandate body carve-out (driver → *Scope*): the Secrétariat Permanent de la Gouvernance Nationale des Communications Electroniques does one thing, so its running cost is the digital line.",
    recipient=MEN, econ="AE 9 000 000 / CP 33 000 000", titre="")
rec(**P26, code="8508403160000XXXX06", label="Prise en charge des factures de la société Mossi",
    amount=500_000_000, scope="unclear", basis="A named private company's invoices carried in the digital ministry's transfer title. Neither volume states what the company supplies, so the line is identified as digital only by the vote it sits in.",
    recipient=MEN, econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", vendor="Mossi",
    notes=["**New line in FY2026** — imputation 85.88.00.27.120000.6439.11, which does not exist in the FY2025 volume. `la société Mossi` is named nowhere else in this corpus.",
           "Together with the V-care line, FCFA 1,5 billion of two private companies' invoices — **21 times the section's entire investment title of FCFA 70 million**."])
rec(**P26, code="8508403160000XXXX07", label="Prendre en charge des factures de la société V-care",
    amount=1_000_000_000, scope="unclear", basis="A named private company's invoices carried in the digital ministry's transfer title. Neither volume states what the company supplies.",
    recipient=MEN, econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", vendor="V-care",
    notes=["Binds to PLF imputation 85.88.00.05.120000.6439.11. The series runs FCFA 500 million proposed FY2025 → 800 million in the Collectif 2025 → **1 000 million proposed FY2026**, a doubling in two years."])
rec(**P26, code="8508403160000XXXX08", label="Paiement des arriérés de six (06) mois de salaires de 2024 (ACDD)",
    amount=118_000_000, scope="whole", basis="Single-mandate body carve-out: the Agence Centrafricaine du Développement du Digital's entire mandate is digital development, so its payroll is a digital line.",
    recipient="agence-centrafricaine-du-developpement-du-digital", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["**The state's digital development agency went six months of 2024 without paying its staff, and the FY2026 budget is where that is settled.** New imputation 85.88.00.24.120000.6439.11; no equivalent exists in FY2025.",
           "No creating instrument for the ACDD has been located, so the single-mandate carve-out is applied on the strength of the agency's name and its two budgeted activities (urban fibre loops; its own payroll), not on a statutory mandate."])
rec(**P26, code="8508403160000XXXX09", label="Payer les arriérés des consommations téléphoniques de l\"administration (SOCATEL)",
    amount=250_000_000, scope="partial", basis="Arrears on the administration's own telephone consumption, paid to the state telecom operator. Telecommunications service, not digital transformation investment; the digital component is not separable.",
    recipient="socatel", econ="Subventions aux entreprises publiques de télécommunication (TITRE IV)", titre="IV",
    notes=["Flat at FCFA 250 million across the Collectif 2025 and the FY2026 proposal. This is the only SOCATEL money visible in the state budget, against a US$150 million recapitalisation announced with Greenline Technologies and carrying no appropriation anywhere."])

# ---------------------------------------------------------------- FY2026 proposed, cross-vote (CDMT grain)
XV26 = dict(fy="2026", stage="proposed", doc="cdmt2026", published="2025-11-18")
rec(**XV26, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="3002601230000XXXX03",
    label="Déploier SydoniaWorld au Terminal3 (Bouar ; Bambari ; Kribi ; Gaaroua-Boulai ; Pointe Noire et Kenzo)",
    amount=420_000_000, scope="whole", basis="Activity label states deployment of the SYDONIA World customs system at named terminals.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="AE 180 000 000 / CP 420 000 000", titre="",
    notes=["**The largest cross-vote digital line in the state budget, and larger than the digital ministry's entire non-transfer spend.** The cross-vote scan is not optional for this country: the finance ministry, not the digital ministry, is where CAR's systems money sits."])
rec(**XV26, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="3002701230000XXXX07",
    label="réhabilitaion et équipement de la plateforme de saisie des engagements des données",
    amount=38_000_000, scope="whole", basis="Activity label states rehabilitation and equipping of the commitments data-entry platform.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="AE 38 000 000 / CP 38 000 000", titre="")
rec(**XV26, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="3002701230000XXXX04",
    label="Organiser les sessions de maintenance de l\"applicatif Simba",
    amount=10_000_000, scope="whole", basis="Activity label states maintenance of SIM_ba, the ministry's budget preparation and execution system.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="AE 0 / CP 10 000 000", titre="",
    notes=["SIM_ba is the system that produced the volume this record is extracted from — every page of the PLF foots `Edité par SIM_ba`."])
rec(**XV26, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="3002804230000XXXX04",
    label="Numériser et moderniser les interconnections avec l\"applicatif Simba",
    amount=3_125_000, scope="whole", basis="Activity label states digitisation and modernisation of interconnections with SIM_ba.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="AE 2 000 000 / CP 3 125 000", titre="")
rec(**XV26, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="3002603230000XXXX03",
    label="Opérationaliser le paiement électronique des droits et taxes",
    amount=3_000_000, scope="whole", basis="Activity label states operationalisation of electronic payment of duties and taxes.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="AE 0 / CP 3 000 000", titre="")
rec(**XV26, section="32", secname="MINISTERE DE LA FONCTION PUBLIQUE ET DE LA REFORME ADMINISTRATIVE", code="3203701",
    label="Digitalisation de l\"administration et innovations numériques",
    amount=16_000_000, scope="whole", basis="A whole action of the civil-service ministry's programme, stated purpose entirely digital.",
    recipient="ministere-de-la-fonction-publique-rca", econ="AE 0 / CP 16 000 000", titre="")
rec(**XV26, section="40", secname="MINISTERE DE L'EDUCATION NATIONALE", code="4004604",
    label="Digitalisation du système éducatif, gestion du système d\"information, renforcement du système éducatif",
    amount=6_000_000, scope="partial", basis="The action's stated purpose mixes digitisation of the education system and management of its information system with general strengthening of the education system; the digital share is not separable.",
    recipient="ministere-de-l-education-nationale-rca", econ="AE 0 / CP 6 000 000", titre="")
rec(**XV26, section="41", secname="MINISTERE DE L'ENSEIGNEMENT SUPERIEUR", code="4104901230000XXXX12",
    label="Numeriser les Diplômes au SG-UB",
    amount=20_000_000, scope="whole", basis="Activity label states digitisation of diplomas at the Université de Bangui secretariat-general.",
    recipient="ministere-de-l-enseignement-superieur-rca", econ="AE 0 / CP 20 000 000", titre="",
    notes=["Confirmed against the PLF at imputation 41.46.00.13.150002.6439.11 (`Numérisation des Diplômes`), 20 000 milliers, new in FY2026 — the two volumes agree to the franc."])
rec(**XV26, section="50", secname="MINISTERE DE LA COMMUNICATION ET DES MEDIAS", code="5005001230000XXXX03",
    label="Assurer l’ouverture d’accès à la télévision numérique satéllitaire (TNS) en République Centrafricaine",
    amount=30_000_000, scope="partial", basis="Digital-terrestrial/satellite television access — broadcasting infrastructure rather than data governance; recorded partial.",
    recipient="ministere-de-la-communication-et-des-medias-rca", econ="AE 30 000 000 / CP 30 000 000", titre="")
rec(**XV26, section="50", secname="MINISTERE DE LA COMMUNICATION ET DES MEDIAS", code="5005204630000XXXX01",
    label="Développer un système d\"archivage",
    amount=30_000_000, scope="whole", basis="Activity label states development of an archiving system; confirmed against the PLF's `Numérisation des archives` at imputation 50.52.00.43.120000.2446.11, 30 000 milliers.",
    recipient="ministere-de-la-communication-et-des-medias-rca", econ="AE 0 / CP 30 000 000", titre="")
rec(**XV26, section="50", secname="MINISTERE DE LA COMMUNICATION ET DES MEDIAS", code="5005103630000XXXX02",
    label="Restructurer le site internet de l\"ACAP",
    amount=9_000_000, scope="whole", basis="Activity label states restructuring of the national news agency's website.",
    recipient="ministere-de-la-communication-et-des-medias-rca", econ="AE 0 / CP 9 000 000", titre="")
rec(**XV26, section="31", secname="MINISTERE DE L'ECONOMIE, DU PLAN ET DE LA COOPERATION INTERNATIONALE", code="3103404240000XXXX04",
    label="Développer un système d\"archivage",
    amount=6_500_000, scope="whole", basis="Activity label states development of an archiving system.",
    recipient="ministere-de-l-economie-du-plan-rca", econ="AE 0 / CP 6 500 000", titre="")
rec(**XV26, section="92", secname="MINISTERE DE L'AGRICULTURE ET DU DEVELOPPEMENT RURAL", code="9209102240000XXXX01",
    label="Numériser les archives de la Numérisation des Archives de la DSNTIC",
    amount=8_000_000, scope="whole", basis="Activity label states archive digitisation by the ministry's DSNTIC.",
    recipient="ministere-de-l-agriculture-rca", econ="AE 8 000 000 / CP 8 000 000", titre="",
    notes=["**Reconciliation flag, not asserted.** The PLF carries *two* imputations labelled `Numérisation des Archives` in section 92 at 8 000 milliers each — 92.93.00.41.160000.2428.11 and 92.93.00.06.240008.2428.11 — where the CDMT shows one activity at FCFA 8 000 000. The ministry's true archive-digitisation total may therefore be FCFA 16 000 000. The CDMT figure is recorded because the CDMT cross-foots at every level; the discrepancy is stated rather than resolved."])
rec(**XV26, section="92", secname="MINISTERE DE L'AGRICULTURE ET DU DEVELOPPEMENT RURAL", code="9209302240000XXXX07",
    label="Mettre en place un Système Digitalisation du Ministère de l\"Agriculture et du Développement Rural",
    amount=2_000_000, scope="whole", basis="Activity label states establishment of a ministry digitisation system.",
    recipient="ministere-de-l-agriculture-rca", econ="AE 0 / CP 2 000 000", titre="")
rec(**XV26, section="83", secname="MINISTERE DES MINES ET DE LA GEOLOGIE", code="8307702240000XXXX01",
    label="Créer et gérer une base des données pétrolières",
    amount=650_000, scope="whole", basis="Activity label states creation and management of a petroleum database.",
    recipient="ministere-des-mines-rca", econ="AE 0 / CP 650 000", titre="")
rec(**XV26, section="83", secname="MINISTERE DES MINES ET DE LA GEOLOGIE", code="8307604240000XXXX07",
    label="Mettre à jour le cadastre minier",
    amount=625_000, scope="whole", basis="Activity label states updating of the mining cadastre — a public register.",
    recipient="ministere-des-mines-rca", econ="AE 0 / CP 625 000", titre="")

# ---------------------------------------------------------------- FY2025 proposed (PLF 2025, milliers ×1000)
P25 = dict(fy="2025", stage="proposed", doc="plf2025", published="2024-12-10")
rec(**P25, section="85", secname=S85, code="85.88.00.20.120000.6439.11", label="Appui à l'Autorité de Régulation de Communication Electronique et de la Poste (ARCEP)",
    amount=1_400_000_000, scope="partial", basis="Mandate test: ARCEP regulates electronic communications and post, so the transfer is multi-purpose.",
    recipient="arcep-central-african-republic", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["**This corrects the FY2025 sweep, which recorded the ARCEP transfer at 500 000 milliers `flat year on year`.** That figure is the V-care line. Bound by page geometry and cross-footed: the six TITRE IV lines of the Cabinet du Ministre block sum to the printed subtotal 2 980 000 exactly (250 000 + 500 000 + 1 400 000 + 200 000 + 380 000 + 250 000), and the `Collectif 2024` column sums to its printed 2 475 000 exactly. The FY2026 volume's `Collectif 2025` column independently carries 1 400 000 against the same imputation."])
rec(**P25, section="85", secname=S85, code="85.88.00.05.120000.6439.11", label="Prise en charge des factures de la société V-care",
    amount=500_000_000, scope="unclear", basis="A named private company's invoices carried in the digital ministry's transfer title; the volume does not state what the company supplies.",
    recipient=MEN, econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", vendor="V-care")
rec(**P25, section="85", secname=S85, code="85.88.00.21.120000.6439.11", label="Agence Centrafricaine du Développement du Digital (ACDD)",
    amount=200_000_000, scope="whole", basis="Single-mandate body carve-out: the agency's whole mandate is digital development.",
    recipient="agence-centrafricaine-du-developpement-du-digital", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["Quadrupled from 50 000 milliers in the Collectif 2024. The FY2026 volume shows the Collectif 2025 raised it again, to 300 000 milliers."])
rec(**P25, section="85", secname=S85, code="85.88.00.23.120000.6324.11", label="Arriérés des consommations téléphoniques de l'administration (SOCATEL)",
    amount=250_000_000, scope="partial", basis="Arrears on the administration's telephone consumption paid to the state telecom operator; telecommunications service rather than digital transformation.",
    recipient="socatel", econ="Subventions aux entreprises publiques de télécommunication (TITRE IV)", titre="IV")
rec(**P25, section="85", secname=S85, code="85.88.00.14.120000.2119.11", label="Etude de faisabilité de la réhabilitation du Faisceau Hertzien - RCA - Cameroun - Congo",
    amount=0, scope="whole", basis="Feasibility study for rehabilitating the RCA–Cameroon–Congo microwave link — a cross-border connectivity asset.",
    recipient=MEN, econ="Autres frais de recherches et de développement (TITRE V)", titre="V",
    notes=["**Zeroed.** The Collectif 2024 carried 11 250 milliers against this imputation; the FY2025 proposal carries nothing (`-100,00 %` printed in the variation column). Recorded at zero because a line withdrawn is a finding, and because the FY2024 revised record it supersedes needs a successor in the series."])
rec(**P25, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="30.33.02.05.120000.6014.11", label="Appui à la Digitalisation",
    amount=80_000_000, scope="whole", basis="Free-text activity label bound by page geometry to its imputation; stated purpose is support to digitalisation.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="Achat de fournitures et consommables pour le matériel informatique (TITRE III)", titre="III")
rec(**P25, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="30.31.00.68.120000.6693.11", label="Appui au déploiement de SYDONIA World",
    amount=115_000_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is support to the deployment of the SYDONIA World customs system.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="Rémunération du personnel sous contrat à l'intérieur (TITRE III)", titre="III")
rec(**P25, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="30.31.00.03.230002.6439.11", label="Projet de migration vers le SydoniaWorld",
    amount=130_000_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is migration to SYDONIA World.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV")
rec(**P25, section="50", secname="MINISTERE DE LA COMMUNICATION ET DES MEDIAS", code="50.52.00.43.120000.2446.11", label="Numérisation des archives",
    amount=50_000_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is digitisation of the broadcaster's archives.",
    recipient="ministere-de-la-communication-et-des-medias-rca", econ="Matériel et outillage audiovisuel et de télécommunications (TITRE V)", titre="V")
rec(**P25, section="60", secname="MINISTERE DE LA SANTE ET DE LA POPULATION", code="60.61.00.06.120000.6439.11", label="Appui à la digitalisation",
    amount=15_000_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is support to digitalisation of the health system.",
    recipient="ministere-de-la-sante-rca", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV")
rec(**P25, section="32", secname="MINISTERE DE LA FONCTION PUBLIQUE ET DE LA REFORME ADMINISTRATIVE", code="32.34.00.03.240009.6013.11", label="Direction de la Gouvernance Numérique",
    amount=1_000_000, scope="whole", basis="Single-mandate directorate: the Direction de la Gouvernance Numérique does one thing, so its running cost is the digital line.",
    recipient="ministere-de-la-fonction-publique-rca", econ="Achats de petits matériels, de mobiliers et fournitures de bureau (TITRE III)", titre="III")
rec(**P25, section="32", secname="MINISTERE DE LA FONCTION PUBLIQUE ET DE LA REFORME ADMINISTRATIVE", code="32.34.00.00.240012.6013.11", label="Direction de la Télématique",
    amount=1_000_000, scope="whole", basis="Single-mandate directorate: the Direction de la Télématique does one thing.",
    recipient="ministere-de-la-fonction-publique-rca", econ="Achats de petits matériels, de mobiliers et fournitures de bureau (TITRE III)", titre="III")

# ---------------------------------------------------------------- FY2025 revised (Collectif 2025 column of PLF 2026)
V25 = dict(fy="2025", stage="revised", doc="plf2026", published="2025-05-28")
rec(**V25, section="85", secname=S85, code="85.88.00.20.120000.6439.11", label="Appui à l'Autorité de Régulation de Communication Electronique et de la Poste (ARCEP)",
    amount=1_400_000_000, scope="partial", basis="Mandate test: ARCEP is multi-purpose (electronic communications and post).",
    recipient="arcep-central-african-republic", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["Unchanged by the collectif — the FY2025 proposal and the FY2025 revised budget carry the same 1 400 000 milliers."])
rec(**V25, section="85", secname=S85, code="85.88.00.05.120000.6439.11", label="Prise en charge des factures de la société V-care",
    amount=800_000_000, scope="unclear", basis="A named private company's invoices in the digital ministry's transfer title; purpose not stated in the volume.",
    recipient=MEN, econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", vendor="V-care",
    notes=["**The collectif raised this line 60% in-year**, from the 500 000 milliers proposed to 800 000 — the largest single in-year movement in the digital vote."])
rec(**V25, section="85", secname=S85, code="85.88.00.21.120000.6439.11", label="Agence Centrafricaine du Développement du Digital (ACDD)",
    amount=300_000_000, scope="whole", basis="Single-mandate body carve-out.",
    recipient="agence-centrafricaine-du-developpement-du-digital", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["Raised 50% in-year, from the 200 000 milliers proposed to 300 000 — in the same year the agency was six months in arrears on its own salaries."])
rec(**V25, section="85", secname=S85, code="85.88.00.23.120000.6324.11", label="Arriérés des consommations téléphoniques de l'administration (SOCATEL)",
    amount=250_000_000, scope="partial", basis="Arrears on the administration's telephone consumption paid to the state telecom operator.",
    recipient="socatel", econ="Subventions aux entreprises publiques de télécommunication (TITRE IV)", titre="IV")

# ---------------------------------------------------------------- FY2024 revised (Collectif 2024 column of PLF 2025)
V24 = dict(fy="2024", stage="revised", doc="plf2025", published="2024-10-30")
rec(**V24, section="85", secname=S85, code="85.88.00.20.120000.6439.11", label="Appui à l'Autorité de Régulation de Communication Electronique et de la Poste (ARCEP)",
    amount=1_300_000_000, scope="partial", basis="Mandate test: ARCEP is multi-purpose.",
    recipient="arcep-central-african-republic", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["**The first FY2024 figure the wiki has been able to state for the Central African Republic's digital vote.** The FY2024 sweep found no figure for the digital ministry anywhere and recorded the sector-side view as empty on published evidence; the enacted Loi de Finances 2024 and the Collectif 2024 are both image-only scans. This is recovered from the *prior-year comparator column* of the FY2025 draft budget, which is native."])
rec(**V24, section="85", secname=S85, code="85.88.00.05.120000.6439.11", label="Prise en charge des factures de la société V-care",
    amount=500_000_000, scope="unclear", basis="A named private company's invoices in the digital ministry's transfer title; purpose not stated.",
    recipient=MEN, econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV", vendor="V-care")
rec(**V24, section="85", secname=S85, code="85.88.00.21.120000.6439.11", label="Agence Centrafricaine du Développement du Digital (ACDD)",
    amount=50_000_000, scope="whole", basis="Single-mandate body carve-out.",
    recipient="agence-centrafricaine-du-developpement-du-digital", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["The ACDD's transfer runs 50 → 200 → 300 → 300 million FCFA across the FY2024 revised, FY2025 proposed, FY2025 revised and FY2026 proposed stages — a sixfold rise in two years."])
rec(**V24, section="85", secname=S85, code="85.88.00.23.120000.6324.11", label="Arriérés des consommations téléphoniques de l'administration (SOCATEL)",
    amount=100_000_000, scope="partial", basis="Arrears on the administration's telephone consumption paid to the state telecom operator.",
    recipient="socatel", econ="Subventions aux entreprises publiques de télécommunication (TITRE IV)", titre="IV")
rec(**V24, section="85", secname=S85, code="85.88.00.14.120000.2119.11", label="Etude de faisabilité de la réhabilitation du Faisceau Hertzien - RCA - Cameroun - Congo",
    amount=11_250_000, scope="whole", basis="Feasibility study for rehabilitating the RCA–Cameroon–Congo microwave link.",
    recipient=MEN, econ="Autres frais de recherches et de développement (TITRE V)", titre="V",
    notes=["Withdrawn entirely in the FY2025 proposal (`-100,00 %`)."])
rec(**V24, section="30", secname="MINISTERE DES FINANCES ET DU BUDGET", code="30.33.02.05.120000.6014.11", label="Appui à la Digitalisation",
    amount=80_000_000, scope="whole", basis="Free-text activity label bound by page geometry to its imputation.",
    recipient="ministere-des-finances-et-du-budget-rca", econ="Achat de fournitures et consommables pour le matériel informatique (TITRE III)", titre="III")
rec(**V24, section="50", secname="MINISTERE DE LA COMMUNICATION ET DES MEDIAS", code="50.52.00.43.120000.2446.11", label="Numérisation des archives",
    amount=49_996_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is digitisation of the broadcaster's archives.",
    recipient="ministere-de-la-communication-et-des-medias-rca", econ="Matériel et outillage audiovisuel et de télécommunications (TITRE V)", titre="V")
rec(**V24, section="60", secname="MINISTERE DE LA SANTE ET DE LA POPULATION", code="60.61.00.06.120000.6439.11", label="Appui à la digitalisation",
    amount=20_000_000, scope="whole", basis="Free-text activity label bound by page geometry; stated purpose is support to digitalisation of the health system.",
    recipient="ministere-de-la-sante-rca", econ="Transferts courants aux autres unités administratives (TITRE IV)", titre="IV",
    notes=["Cut 25% in the FY2025 proposal, to 15 000 milliers."])

TOPICS = {
    "85": "dpi.govtech", "30": "dpi.govtech", "32": "dpi.govtech", "40": "dpi.govtech",
    "41": "dpi.govtech", "50": "infra.connect", "31": "dpi.govtech", "92": "dpi.govtech",
    "83": "dpi.registry", "60": "dpi.mis",
}


def topics_for(r):
    t = ["finance.budget"]
    lab = r["label"].lower()
    if "arcep" in lab:
        t += ["gov.standards"]
    elif "securite des reseaux" in slug(r["label"]).replace("-", " ") or "confiance numerique" in slug(r["label"]).replace("-", " "):
        t += ["infra.cybersec"]
    elif any(k in slug(r["label"]) for k in ("optique", "internet", "large-bande", "backbone", "back-bone", "raccord", "television")):
        t += ["infra.connect"]
    elif "cadastre" in lab or "donnees petrolieres" in slug(r["label"]).replace("-", " "):
        t += ["dpi.registry"]
    else:
        t += [TOPICS.get(r["section"], "dpi.govtech")]
    return t


def build(r):
    d = DOCS[r["doc"]]
    fys, fye = FY[r["fy"]]
    code_slug = slug(r["code"])
    deal = f"caf-{r['fy']}-{r['section']}-{code_slug}-{r['stage']}"
    title_lab = r["label"] if len(r["label"]) < 90 else r["label"][:87] + "…"
    amt_fr = f"{r['amount']:,}".replace(",", " ")
    title = f"Central African Republic FY{r['fy']} — section {r['section']}, {title_lab}: FCFA {amt_fr}"
    fname = f"{r['published']}-{deal}-{slug(r['label'])[:48]}.md"
    ents = sorted({FIN, r["recipient"]})
    caps = {}
    if r["titre"] == "V":
        caps["amount_capital"] = r["amount"]
    elif r["titre"] in ("III", "IV"):
        caps["amount_recurrent"] = r["amount"]
    fm = [
        "---", "type: source",
        f'title: "{title}"',
        f"url: {d['url']}",
        'publisher: "Ministère des Finances et du Budget (République Centrafricaine)"',
        f"published: {r['published']}", "date_precision: day", "date_source: source",
        "places: [CAF]",
        f"topics: [{', '.join(topics_for(r))}]",
        "entities: [" + ", ".join(f"[{e}]" for e in ents) + "]",
        f"financier_slug: {FIN}",
        f"recipient_slug: {r['recipient']}",
        "lens: []",
        f"deal_id: {deal}",
        "finance_origin: domestic-state", "state_level: national", 'spending_tier_name: ""',
        f'fiscal_year_label: "{r["fy"]}"',
        f"fy_start: {fys}", f"fy_end: {fye}",
        f"budget_stage: {r['stage']}",
        "budget_version: " + ("revised" if r["stage"] == "revised" else "original"),
        "source_tier: budget-document",
        'supplementary_basis: ' + ('restated-total' if r["stage"] == "revised" else '""'),
        f"scope_confidence: {r['scope']}",
        f"is_transfer: {'true' if r['transfer'] else 'false'}",
        f"amount_total: {r['amount']}",
    ]
    for k, v in caps.items():
        fm.append(f"{k}: {v}")
    fm += ["currency: XAF", "ingested: 2026-07-26", "retrieved: 2026-07-26",
           "body_completeness: excerpt", "---", ""]

    stage_txt = STAGE_NOTE[r["stage"]]
    body = [f"# {title}", "",
            f"Section **{r['section']} {r['secname']}** of the budget of the Central African Republic, "
            f"{stage_txt}, fiscal year {r['fy']} (1 January – 31 December {r['fy']}). "
            f"The amount is **FCFA {amt_fr}**, wholly domestically financed.", "",
            "## Deal record", "", "| Field | Value |", "|---|---|",
            f"| Deal ID | {deal} |",
            f"| Financier | Ministère des Finances et du Budget (République Centrafricaine) — the state budget |",
            f"| Spending entity | Section {r['section']} — {r['secname']} |",
            "| Instrument | Budget appropriation — Central African Republic state budget |",
            f"| Budget stage | {stage_txt} |",
            "| Budget version | " + ("revised" if r["stage"] == "revised" else "original") + " |",
            f"| Fiscal year label | {r['fy']} (calendar year) |",
            "| fy_calendar | gregorian |",
            f"| Amount (domestic-state) | FCFA {amt_fr} |",
            "| Excluded as external (origin gate) | FCFA 0 |",
            "| funding_source | domestic-revenue |",
            f"| amount_scale | {d['scale']} |",
            f"| admin_head | Section {r['section']} — {r['secname']} |",
            f"| admin_head_code | {r['section']} |",
            f"| programme | {r['label']} |",
            f"| programme_code | {r['code']} |",
            "| classification_labels | " + ("Section / Programme / Action / Activité — CDMT sectoriels (budget-programme)"
                                            if r["doc"] == "cdmt2026" else
                                            "Section / Service / TITRE / Imputation — projet de loi de finances (budget de moyens)") + " |",
            f"| econ_class | {r['econ'] or '—'} |",
            f"| scope_confidence | {r['scope']} |",
            f"| scope_basis | {r['basis']} |",
            f"| vendor | {r['vendor'] or '— (not named)'} |",
            f"| doc_type | {d['doc_type']} |",
            f"| doc_locator | {r['locator']} |", "",
            "## Description", "",
            f"« {r['label']} »", "",
            "## Source", "",
            f"*{d['title']}*, Ministère des Finances et du Budget, République Centrafricaine — <{d['url']}>. "
            f"Companion source page: `{d['companion']}`. Extracted tables: `budget-archive/CAF/`.", "",
            "## Notes", ""]

    notes = list(r["notes"])
    notes.append(
        "**Origin gate applied at capture, and the Central African Republic prints it twice.** "
        "The estimates volume carries `Financement intérieur` and `Financement extérieur (Dons | Emprunt)` "
        "as columns beside every line, and the imputation's own last segment encodes the same fact — "
        "`.11` domestic, `.25` grant, `.44` loan. Tested across 10 898 imputation rows in the FY2025 and "
        "FY2026 volumes, the two agree without exception. This line is `Financement intérieur`."
    )
    if r["doc"] == "cdmt2026":
        notes.append(
            "**Figure taken from the CDMT sectoriels, the appropriating instrument is the finance law.** "
            "The CDMT restates the same budget at activity grain and reconciles to the projet de loi de "
            "finances to the franc (section 85: CP `5 548 540 000` = `5 548 540` milliers), but it is "
            "published *à titre expérimental* and has no legal force. `published` therefore anchors on the "
            "tabling of the draft budget (18 November 2025), not on the CDMT's own posting date of "
            "24 March 2026 (`CLAUDE.md` → *Currency*)."
        )
    if r["stage"] == "revised":
        notes.append(
            "**Recovered from the following year's volume, not from the collectif itself.** The enacted "
            f"collectif budgétaire {r['fy']} is an image-only scan with zero extractable characters. Its "
            "figures are readable because every Central African SIM_ba volume prints the prior year's "
            f"collectif as a comparator column — `Collectif {r['fy']}` in the FY{int(r['fy'])+1} projet de "
            "loi de finances, which is native. The column sums to its own printed subtotals exactly."
        )
    notes.append(
        "**`amount_usd` left blank.** The wiki holds no named fiscal-year-average XAF/USD rate for this "
        "year and the driver forbids spot-converting a fiscal-year figure. Carried in the announcing "
        "state's own currency only."
    )
    body += [f"- {n}" for n in notes]
    body.append("")
    return fname, "\n".join(fm) + "\n".join(body) + "\n"


LOCATORS = {
    "cdmt2026": "CDMT sectoriels 2026, *Budget détaillé par activité*, section {sec}, code {code}, colonne CP 2026",
    "plf2026": "PLF 2026, volume des charges, section {sec}, imputation {code}, colonne « Collectif 2025 »",
    "plf2025": "PLF 2025, volume des charges, section {sec}, imputation {code}, colonne « {col} »",
}

written = 0
for r in R:
    if r["doc"] == "plf2025":
        col = "Collectif 2024" if r["stage"] == "revised" else "Crédit 2025"
        r["locator"] = LOCATORS["plf2025"].format(sec=r["section"], code=r["code"], col=col)
    else:
        r["locator"] = LOCATORS[r["doc"]].format(sec=r["section"], code=r["code"])
    fname, text = build(r)
    with open(os.path.join(OUT, fname), "w", encoding="utf-8") as fh:
        fh.write(text)
    written += 1
print(f"{written} records written to {OUT}/")
