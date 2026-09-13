# -*- coding: utf-8 -*-
"""Driver case 3 — attach the held reporting to the budget-document records it clarifies.

The budget document is the record; the reporting is linked as a dated attributed line in
`## Development history`, never merged into the fields (wiki/finance-load-domestic-state.md).
"""
import os, sys

sys.stdout.reconfigure(encoding="utf-8")

HIST = {
    # ---- FY2024 MND: parliament left the ministry total alone and moved money between programmes
    "2023-12-20-ben-2024-pilotage-mnd-100-appropriated.md": [
        "- **2023-11-20** — at the projet-de-loi stage the minister for digital affairs put this programme at **2 490 650 000 FCFA** before the Assemblée nationale; the enacted figure is 5 000 000 FCFA higher. [Léconomiste du Bénin, 2023-11-21](https://leconomistebenin.bj/243-milliards-fcfa-pour-le-numerique-et-la-digitalisation/)",
    ],
    "2023-12-20-ben-2024-numerique-111-appropriated.md": [
        "- **2023-11-20** — at the projet-de-loi stage this programme was tabled at **12 792 586 000 FCFA**; **91 164 000 FCFA was taken out of it during passage**, of which 86 164 000 went to the Médias programme and 5 000 000 to the ministry's pilotage programme. The MND's total was unchanged at 24 356 549 000 FCFA. [Léconomiste du Bénin, 2023-11-21](https://leconomistebenin.bj/243-milliards-fcfa-pour-le-numerique-et-la-digitalisation/)",
    ],
    "2023-12-20-ben-2024-medias-109-appropriated.md": [
        "- **2023-11-20** — tabled at **9 073 313 000 FCFA**; gained 86 164 000 FCFA during passage, taken from the Numérique programme. [Léconomiste du Bénin, 2023-11-21](https://leconomistebenin.bj/243-milliards-fcfa-pour-le-numerique-et-la-digitalisation/)",
    ],
    # ---- FY2025 MND
    "2024-12-12-ben-2025-pilotage-mnd-100-appropriated.md": [
        "- **2024-11-18** — tabled at **2 568 302 575 FCFA**; **166 585 780 FCFA was moved out of this programme into Médias during passage**, leaving the ministry total unchanged. [Léconomiste du Bénin, 2024-11-18](https://leconomistebenin.bj/ministere-du-numerique-plus-de-29-milliards-fcfa-en-2025-pour-booster-la-digitalisation-et-les-medias/)",
    ],
    "2024-12-12-ben-2025-numerique-111-appropriated.md": [
        "- **2024-11-18** — tabled at **16 428 858 510 FCFA** and enacted unchanged. The minister defended the ministry's gestion-2025 budget before the Assemblée nationale the same day. [Léconomiste du Bénin, 2024-11-18](https://leconomistebenin.bj/ministere-du-numerique-plus-de-29-milliards-fcfa-en-2025-pour-booster-la-digitalisation-et-les-medias/)",
    ],
    "2024-12-12-ben-2025-medias-109-appropriated.md": [
        "- **2024-11-18** — tabled at **10 036 805 107 FCFA**; gained 166 585 780 FCFA during passage, taken from the ministry's pilotage programme. [Léconomiste du Bénin, 2024-11-18](https://leconomistebenin.bj/ministere-du-numerique-plus-de-29-milliards-fcfa-en-2025-pour-booster-la-digitalisation-et-les-medias/)",
    ],
    # ---- FY2026 MND: tabled = enacted, to the franc
    "2025-12-04-ben-2026-pilotage-mnd-100-appropriated.md": [
        "- **2025-11-27** — the ministry's own account of its budget defence gives this programme at **2 184 235 167 FCFA**, identical to the enacted figure. [numerique.gouv.bj, 2025-11-28](https://www.numerique.gouv.bj/publications/actualites/budget-2026-du-ministere-du-numerique-et-de-la-digitalisation-face-aux-deputes-aurelie-adam-soule-zoumarou-reaffirme-les-priorites-strategiques-du)",
    ],
    "2025-12-04-ben-2026-numerique-111-appropriated.md": [
        "- **2025-11-25** — reported at CFA 12.3 bn for \"nationwide digital transformation\" when the ministry's proposed budget was presented to the Assemblée nationale. [We Are Tech Africa, 2025-11-27](https://www.wearetech.africa/en/fils-uk/news/tech/benin-cuts-digital-budget-by-6-32-despite-expanding-tech-ambitions)",
        "- **2025-11-27** — the ministry's own account gives **12 372 151 413 FCFA**, identical to the enacted figure, and names four flagship projects for the year. [numerique.gouv.bj, 2025-11-28](https://www.numerique.gouv.bj/publications/actualites/budget-2026-du-ministere-du-numerique-et-de-la-digitalisation-face-aux-deputes-aurelie-adam-soule-zoumarou-reaffirme-les-priorites-strategiques-du)",
    ],
    "2025-12-04-ben-2026-medias-109-appropriated.md": [
        "- **2025-11-27** — the ministry's own account gives **12 681 648 973 FCFA**, identical to the enacted figure. [numerique.gouv.bj, 2025-11-28](https://www.numerique.gouv.bj/publications/actualites/budget-2026-du-ministere-du-numerique-et-de-la-digitalisation-face-aux-deputes-aurelie-adam-soule-zoumarou-reaffirme-les-priorites-strategiques-du)",
    ],
    # ---- APDP
    "2023-12-20-ben-2024-apdp-014-appropriated.md": [
        "- **2024-11-27** — the APDP's president cited **488 277 000 FCFA** as the authority's 2024 appropriation when defending its 2025 budget before the Assembly's budget committee — an independent confirmation of the figure in the estimates volume. [Léconomiste du Bénin, 2024-12-03](https://leconomistebenin.bj/travaux-budgetaires-au-parlement-les-budgets-2025-de-la-cbdh-et-de-lapdp-presentes/)",
    ],
    "2024-12-12-ben-2025-apdp-014-appropriated.md": [
        "- **2024-11-27** — the APDP's president defended a **638 277 000 FCFA** budget for 2025 before the Assembly's budget committee, a 30.7% rise on 2024 traced to a parliamentary recommendation made during the **2023** budget debates — a three-year lag from legislative ask to appropriation. [Léconomiste du Bénin, 2024-12-03](https://leconomistebenin.bj/travaux-budgetaires-au-parlement-les-budgets-2025-de-la-cbdh-et-de-lapdp-presentes/)",
        "- **2024-12-11** — of that budget, **40 million FCFA** is for intrusion-testing and compliance tooling and 150 million for awareness work. [Cadreco, 2024-12-11](https://cadreco.media/numerique/2024/protection-des-donnees-personnelles-lapdp-mise-sur-un-budget-de-pres-de-640-millions-de-fcfa-en-2025)",
    ],
    # ---- 044, 108: the mid-2026 machinery change, sourced
    "2025-12-04-ben-2026-modernisation-administration-publique-044-appropriated.md": [
        "- **2026-05-24** — décret n° 2026-314 dissolved the MTFP and moved this programme to a new Ministère du Budget et des Finances Publiques. [Bénin Web TV, 2026-05-26](https://beninwebtv.bj/benin-mahuna-akplogan-prend-les-commandes-du-nouveau-ministere-de-lia/)",
        "- **2026-06-22** — the Assemblée nationale adopted loi n° 2026-10, the rectificative for gestion 2026, raising the state budget to 4 148.357 bn FCFA. The enacted text is not held. [La Nation, 2026-06-22](https://www.lanation.bj/actualites/assemblee-nationale-le-budget-de-letat-gestion-2026-rehausse-a-4-148357-milliards-f-cfa)",
    ],
    "2025-12-04-ben-2026-modernisation-regies-financieres-108-appropriated.md": [
        "- **2026-06-09** — the projet de loi de finances rectificative drops this programme from the programme list entirely and zeroes its 6 000 000 000 FCFA. Two other special funds are zeroed identically, so this reads as a comptes-spéciaux restructure rather than a cut to digital spending.",
        "- **2026-06-22** — loi n° 2026-10 was adopted; its text is not published, so whether the abolition survived into the enacted rectificative is **not established as at 2026-07-25**. [La Nation, 2026-06-22](https://www.lanation.bj/actualites/assemblee-nationale-le-budget-de-letat-gestion-2026-rehausse-a-4-148357-milliards-f-cfa)",
    ],
}


def main():
    n = 0
    for fn, lines in HIST.items():
        p = os.path.join("new", fn)
        t = open(p, encoding="utf-8").read()
        assert "## Development history\n" in t, p
        t = t.replace("## Development history\n\n", "## Development history\n\n" + "\n".join(lines) + "\n\n", 1)
        open(p, "w", encoding="utf-8", newline="").write(t)
        n += 1
    print("added development history to", n, "records")


if __name__ == "__main__":
    main()
