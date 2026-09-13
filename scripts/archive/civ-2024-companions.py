#!/usr/bin/env python3
"""Stage the CIV FY2024 domestic-finance sweep: rename artefacts to the
date-prefixed convention, write a companion page beside each, and append the
manifest rows. Sweep-side only -- fills the manifest up to `pages`; the
extraction pass sets everything after it.
"""
import csv
import io
import os
import re
import subprocess
import sys

ROOT = r"C:\Users\bill\OSINT"
DIR = os.path.join(ROOT, "new-budget", "CIV", "2024")
MANIFEST = os.path.join(ROOT, "new-budget", "manifest.csv")
BATCH = "domestic-finance-CIV-2024-2026-07-26"
RETRIEVED = "2026-07-26"

DGBF = "https://www.dgbf.ci/wp-content/uploads/"
CC = "https://courdescomptes.ci/fichiers/"
MTND = "https://www.telecom.gouv.ci/new/uploads/publications/"

# original filename -> (slug, published, precision, date_source, title, publisher,
#                       url, doc_type, fy_covered, scale, entities, notes)
DOCS = [
    ("Loi-de-Finances-Portant-Budget-de-lEtat-pour-lannee-2024.pdf",
     "civ-loi-de-finances-2024", "2023-12-18", "day", "source",
     "Loi de Finances n\u00b0 2023-1000 du 18 d\u00e9cembre 2023 portant Budget de l'Etat pour l'ann\u00e9e 2024",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/Loi-de-Finances-Portant-Budget-de-lEtat-pour-lannee-2024.pdf",
     "appropriation-act", '["2024"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,ministry-of-digital-transition-cote-divoire,ansut,artci",
     "THE FULL ESTIMATES VOLUME. Native, 0 OCR. Six table types: Recapitulatif des Ressources / par Grande Nature / par Section et Programme-Dotation / par Section et Grande Nature / du Service de la Dette / Detail du Budget General Hors Dette et Hors Comptes Speciaux. Grain: section (3-digit) > programme (5) > action (7) > nature de depense (1-4) > activite (11-digit), AE and CP columns. NO source-of-financing column anywhere -- origin gate is NOT printed at line grain (contrast BFA/BWA/CAF). Article 18 lists every Compte d'Affectation Speciale by activity code. ARCHETYPE M: pdftotext -layout drifts amounts by 1-4 rows in the summary tables; the Detail pages align cleanly. Cross-foot before recording."),

    ("Rapport-de-presentation-de-la-loi-de-finances-portant-budget-de-lEtat.pdf",
     "civ-lf-2024-rapport-de-presentation", "2023-12-18", "day", "source",
     "Rapport de pr\u00e9sentation de la Loi de Finances portant Budget de l'Etat pour l'ann\u00e9e 2024",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/Rapport-de-presentation-de-la-loi-de-finances-portant-budget-de-lEtat.pdf",
     "budget-estimates", '["2024"]', "FCFA / milliards",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,assemblee-nationale-cote-divoire",
     "Explanatory memorandum to the LF 2024; aggregates by mission and nature."),

    ("ANNEXE-4-Documents-de-Programmation-Pluriannuelle-des-Depenses-Projets-Annuels-de-Performance-DPPD-PAP-2024-2026.pdf",
     "civ-lf-2024-annexe-4-dppd-pap-2024-2026", "2023-12-18", "day", "source",
     "Annexe 4 : Documents de Programmation Pluriannuelle des D\u00e9penses - Projets Annuels de Performance (DPPD-PAP) 2024-2026",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/ANNEXE-4-Documents-de-Programmation-Pluriannuelle-des-Depenses-Projets-Annuels-de-Performance-DPPD-PAP-2024-2026.pdf",
     "budget-estimates", '["2024", "2025", "2026"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,ministry-of-digital-transition-cote-divoire,ansut",
     "The programme-budget half of the estimates volume: per-ministry PAP with Tableau 1 cartographie administrative (services / organismes sous tutelle / PROJETS PIP / PROJETS HORS PIP), Tableau 6 synthese par nature de depenses, Tableau 7 budget detaille du programme, all with 2024 + 2025 + 2026 columns. MTND at pp. 661-670: Programme 1 Administration generale 1 243 627 278 + Programme 2 Economie numerique et poste 17 935 498 592 + Programme 3 Comptes Speciaux du Tresor 36 470 000 000 = 55 649 125 870, cross-foots exactly. Names the PIP/hors-PIP projects the vote structure hides (RNHD fibre ANSUT, ZBTIC, PARAE e-governance)."),

    ("ANNEXE-2-Rapport-Economique-et-Financier-pour-lannee-2024.pdf",
     "civ-lf-2024-annexe-2-rapport-economique-et-financier", "2023-12-18", "day", "source",
     "Annexe 2 : Rapport \u00c9conomique et Financier pour l'ann\u00e9e 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2024/03/ANNEXE-2-Rapport-Economique-et-Financier-pour-lannee-2024.pdf",
     "budget-estimates", '["2022", "2023", "2024"]', "milliards FCFA",
     "ministere-des-finances-et-du-budget-cote-divoire,assemblee-nationale-cote-divoire",
     "Macro-fiscal framing annexed to the LF; the telecoms sector growth series lives here."),

    ("ANNEXE-3-Documents-de-Programmation-Budgetaire-et-Economique-Pluriannuelle-DPBEP-2024-2026.pdf",
     "civ-lf-2024-annexe-3-dpbep-2024-2026", "2023-12-18", "day", "source",
     "Annexe 3 : Document de Programmation Budg\u00e9taire et \u00c9conomique Pluriannuelle (DPBEP) 2024-2026",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/ANNEXE-3-Documents-de-Programmation-Budgetaire-et-Economique-Pluriannuelle-DPBEP-2024-2026.pdf",
     "mtef", '["2024", "2025", "2026"]', "milliards FCFA",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire",
     "The MTEF layer; ministry ceilings 2024-2026."),

    ("Annexe-5-Catalogue-des-mesures-nouvelles-pour-lannee-2024.pdf",
     "civ-lf-2024-annexe-5-catalogue-des-mesures-nouvelles", "2023-12-18", "day", "source",
     "Annexe 5 : Catalogue des mesures nouvelles pour l'ann\u00e9e 2024",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/Annexe-5-Catalogue-des-mesures-nouvelles-pour-lannee-2024.pdf",
     "budget-estimates", '["2024"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire",
     "What is NEW in FY2024 as against the FY2023 base, by ministry -- the fastest route to the year's incremental digital decisions."),

    ("Annexe-6-Budgets-des-Etablissements-Publics-Nationaux-1.pdf",
     "civ-lf-2024-annexe-6-budgets-des-epn", "2023-12-18", "day", "source",
     "Annexe 6 : Budgets des \u00c9tablissements Publics Nationaux",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/Annexe-6-Budgets-des-Etablissements-Publics-Nationaul-1.pdf",
     "board-budget", '["2024"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,oneci,esatic",
     "BLOCK 6 PRIMARY. Per-EPN budgets annexed to the finance law under art. 45 LOLF; art. 20 puts the State's contribution to EPN at 329 177 353 201 FCFA inside the Budget General. This is where ONECI's and ESATIC's own budgets sit. URL in this row is the site's own (note the site path ends -Nationaux-1.pdf)."),

    ("ANNEXE-7-DOTATIONS-DES-INSTITUTIONS-2024.pdf",
     "civ-lf-2024-annexe-7-dotations-des-institutions", "2023-12-18", "day", "source",
     "Annexe 7 : Dotations des Institutions 2024",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/ANNEXE-7-DOTATIONS-DES-INSTITUTIONS-2024.pdf",
     "budget-estimates", '["2024"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,cour-des-comptes-cote-divoire",
     "IMAGE-ONLY over 869pp (53 670 chars total, i.e. cover text only) -- the ONE substantially scanned document in the FY2024 appropriation chain. OCR is a precondition for the 32 dotations, which include the Cour des comptes and the Assembly."),

    ("Annexe-9-Situation-Economique-et-Financiere-des-Entreprises-du-portefeuille-de-lEtat-_-Rapport-au-titre-de-lexercice-2022-2023-et-Concours-Financiers-de-lEtat-2022-2024.pdf",
     "civ-lf-2024-annexe-9-entreprises-du-portefeuille-de-letat", "2023-12-18", "day", "source",
     "Annexe 9 : Situation \u00c9conomique et Financi\u00e8re des Entreprises du portefeuille de l'Etat \u2013 Rapport au titre de l'exercice 2022-2023 et Concours Financiers de l'Etat 2022-2024",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/Annexe-9-Situation-Economique-et-Financiere-des-Entreprises-du-portefeuille-de-lEtat-\u2013-Rapport-au-titre-de-lexercice-2022-2023-et-Concours-Financiers-de-lEtat-2022-2024.pdf",
     "board-budget", '["2022", "2023", "2024"]', "FCFA full units",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire,sndi-cote-divoire,la-poste-cote-divoire",
     "The state-portfolio companies with the State's financial concours 2022-2024 -- SNDI (the national IT company, contracted across votes by 'convention d'assistance technique'), La Poste CI, VITIB. Turnover and subsidy per company."),

    ("ANNEXE-13-Declaration-sur-les-Risques-Budgetaires-2024-2026.pdf",
     "civ-lf-2024-annexe-13-declaration-risques-budgetaires", "2023-12-18", "day", "source",
     "Annexe 13 : D\u00e9claration sur les Risques Budg\u00e9taires 2024-2026",
     "Minist\u00e8re du Budget et du Portefeuille de l'Etat",
     DGBF + "2024/03/ANNEXE-13-Declaration-sur-les-Risques-Budgetaires-2024-2026.pdf",
     "budget-estimates", '["2024", "2025", "2026"]', "milliards FCFA",
     "ministere-du-budget-et-du-portefeuille-de-letat-cote-divoire",
     "Fiscal-risk statement; PPP and SOE contingent liabilities, which is where a vendor-financed digital project would surface if it surfaces at all."),

    ("BUDGET-CITOYEN_2024_30-12-23_B_WEB.pdf",
     "civ-budget-citoyen-2024", "2023-12-30", "day", "source",
     "Budget Citoyen 2024",
     "Direction G\u00e9n\u00e9rale du Budget et des Finances",
     DGBF + "2024/03/BUDGET-CITOYEN_2024_30-12-23_B_WEB.pdf",
     "budget-estimates", '["2024"]', "milliards FCFA",
     "direction-generale-du-budget-et-des-finances-cote-divoire",
     "Native but heavily illustrated (38 MB for 81pp). Aggregates and mission shares; the plain-language statement of what the fiscal year is for."),

    ("CCM-EXECUTION-BUDGETAIRE-FIN-MARS-ROLE-2024.pdf",
     "civ-ccm-execution-budgetaire-fin-mars-2024", "2024-08-01", "month", "inferred",
     "Communication en Conseil des Ministres relative \u00e0 l'ex\u00e9cution du budget de l'Etat \u00e0 fin mars 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2024/08/CCM-EXECUTION-BUDGETAIRE-FIN-MARS-ROLE-2024.pdf",
     "implementation-report", '["2024"]', "milliards FCFA",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "Q1 execution point. IMAGE-ONLY (9 chars over 10pp) -- OCR precondition. Date is the upload month, not a printed date."),

    ("CCM-A-FIN-JUIN-2024.pdf",
     "civ-ccm-execution-budgetaire-fin-juin-2024", "2024-09-01", "month", "inferred",
     "Communication en Conseil des Ministres relative \u00e0 l'ex\u00e9cution du budget de l'Etat \u00e0 fin juin 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2024/09/CCM-A-FIN-JUIN-2024.pdf",
     "implementation-report", '["2024"]', "milliards FCFA",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "H1 execution point. IMAGE-ONLY (10 chars over 11pp) -- OCR precondition."),

    ("CCM-FIN-SEPTEMBRE-2024.pdf",
     "civ-ccm-execution-budgetaire-fin-septembre-2024", "2025-02-01", "month", "inferred",
     "Communication en Conseil des Ministres relative \u00e0 l'ex\u00e9cution du budget de l'Etat \u00e0 fin septembre 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/02/CCM-FIN-SEPTEMBRE-2024.pdf",
     "implementation-report", '["2024"]', "milliards FCFA",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "Q3 execution point. IMAGE-ONLY (10 chars over 11pp) -- OCR precondition."),

    ("CCM-FIN-DECEMBRE-2024.pdf",
     "civ-ccm-execution-budgetaire-fin-decembre-2024", "2025-03-01", "month", "inferred",
     "Communication en Conseil des Ministres relative \u00e0 l'ex\u00e9cution du budget de l'Etat \u00e0 fin d\u00e9cembre 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/03/CCM-FIN-DECEMBRE-2024.pdf",
     "implementation-report", '["2024"]', "milliards FCFA",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "FULL-YEAR execution point and the only NATIVE one of the four quarterly CCMs (30 715 chars over 11pp) -- the inverse of the usual pattern, where the current-year report is native and the older ones are scans. Take this one first."),

    ("REVUE-DE-MILIEU-DANNEE-A-FIN-JUIN-2024.pdf",
     "civ-revue-de-milieu-dannee-fin-juin-2024", "2024-09-01", "month", "inferred",
     "Revue de milieu d'ann\u00e9e \u00e0 fin juin 2024",
     "Direction G\u00e9n\u00e9rale du Budget et des Finances",
     DGBF + "2024/09/REVUE-DE-MILIEU-DANNEE-A-FIN-JUIN-2024.pdf",
     "implementation-report", '["2024"]', "milliards FCFA",
     "direction-generale-du-budget-et-des-finances-cote-divoire",
     "Native, 34pp. Annexe 2 is 'Analyse de l'execution Budgetaire des Programmes par Ministere a fin juin 2024 (hors avances, CST et Administration Generale)' -- H1 execution AT PROGRAMME GRAIN, and it explicitly excludes the CST, so the digital ministry's H1 rate can be read net of the ANSUT and ARTCI levies. Annexe 3 is the same by ministry. Published under the UEMOA transparency directive 01/2009 and against IBP norms."),

    ("Loi-de-Reglement-pour-lannee-2024.pdf",
     "civ-loi-de-reglement-2024", "2025-12-19", "day", "source",
     "Loi n\u00b02025-986 du 19 d\u00e9cembre 2025 portant r\u00e8glement du Budget de l'Etat pour l'ann\u00e9e 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Loi-de-Reglement-pour-lannee-2024.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire,assemblee-nationale-cote-divoire,ansut",
     "THE SETTLEMENT LAW, enacted 19-Dec-2025 for FY2024. Art. 1 ratifies +116 841 164 097 FCFA of supplementary credits opened by ministerial arretes (13 720 704 581 985 -> 13 837 545 746 082), i.e. THE REVISED STAGE IS RATIFIED HERE, NOT BY AN LFR. Carries the executed CST table: ANSUT levy transfer EXECUTED 24 442 126 915 FCFA against 32 300 000 000 appropriated."),

    ("Rapport-de-presentation-de-la-Loi-de-Reglement-2024.pdf",
     "civ-lr-2024-rapport-de-presentation", "2025-12-19", "day", "source",
     "Rapport de pr\u00e9sentation de la Loi de R\u00e8glement 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Rapport-de-presentation-de-la-Loi-de-Reglement-2024.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "Native, 135pp. Its Annexe XIII is the 'liste des actes modificatifs du budget' -- the only justification the Cour des comptes was given for the in-year modifications, and the Cour says so. The revised stage, document by arrete."),

    ("Comptes-et-etats-financiers-pour-lannee-2024.pdf",
     "civ-comptes-et-etats-financiers-2024", "2025-12-19", "day", "source",
     "Comptes et \u00c9tats Financiers pour l'ann\u00e9e 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Comptes-et-etats-financiers-pour-lannee-2024.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "Accrual accounts and state balance sheet for FY2024, annexed to the loi de reglement."),

    ("Rapport-Annuel-de-Performance-2024-Tome-1.pdf",
     "civ-rapport-annuel-de-performance-2024-tome-1", "2025-12-19", "day", "source",
     "Rapports Annuels de Performance 2024 \u2013 Tome 1",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Rapport-Annuel-de-Performance-2024-Tome-1.pdf",
     "implementation-report", '["2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "1164pp native. Per-ministry RAP; each carries 'Budget initial | Collectif | Budget Actuel | Budget Execute | Ecart | Taux d'execution' by nature de depense AND by action. THE COLLECTIF COLUMN IS THE REVISED STAGE AT PROGRAMME GRAIN. Tome 1 covers the first half of the section list."),

    ("Rapport-Annuel-de-Performance-2024-Tome-2.pdf",
     "civ-rapport-annuel-de-performance-2024-tome-2", "2025-12-19", "day", "source",
     "Rapports Annuels de Performance 2024 \u2013 Tome 2",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Rapport-Annuel-de-Performance-2024-Tome-2.pdf",
     "implementation-report", '["2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire,ministry-of-digital-transition-cote-divoire",
     "1158pp native. Contains the MTND RAP at pp. 637-660 (Programme 1 initial 1 243 627 278 -> collectif 1 505 459 066, +21,05%, executed 95,09%; Programme 2 initial 17 935 498 592 -> revised 18 185 498 592, executed 99,99%; ministry budget execution 99,69%, PTA physical 90% = 45 of 50 activities). Also names the arretes that created four new activities mid-year, including PARAE and PADCI."),

    ("Rapport-General-sur-la-Performance-2024.pdf",
     "civ-rapport-general-sur-la-performance-2024", "2025-12-19", "day", "source",
     "Rapport G\u00e9n\u00e9ral sur la Performance 2024",
     "Minist\u00e8re des Finances et du Budget",
     DGBF + "2025/12/Rapport-General-sur-la-Performance-2024.pdf",
     "implementation-report", '["2022", "2023", "2024"]', "FCFA full units",
     "ministere-des-finances-et-du-budget-cote-divoire",
     "The cross-government synthesis of the RAPs. Gives the CST movement: 33 CST in 2023 -> 38 in 2024; CST voted 1 300 573 176 811 -> budget actuel 1 222 596 989 710. Whole-of-programmes voted 5 422 753 683 ... -> actuel 6 668 368 148 113."),

    ("CC-Rapport-sur-lExecution-de-la-Loi-de-Finances-2024.pdf",
     "civ-cc-rapport-execution-loi-de-finances-2024", "2026-01-16", "day", "inferred",
     "Rapport sur l'ex\u00e9cution de la loi de finances en vue du r\u00e8glement du budget de l'Etat pour l'ann\u00e9e 2024",
     "Cour des comptes de C\u00f4te d'Ivoire",
     CC + "1768604969RapportsurlExecutiondelaLoideFinances2024.pdf",
     "audited-accounts", '["2023", "2024"]', "FCFA full units",
     "cour-des-comptes-cote-divoire,ministere-des-finances-et-du-budget-cote-divoire",
     "THE AUDIT STAGE, native, 98pp, contradictory procedure with the Minister's replies transcribed in full. Establishes that NO loi de finances rectificative was passed in FY2024 because the modification rate was 0,85%, under the 1% art.25 ceiling -- so the revised stage is by arrete and ratified in the loi de reglement. Also flags that Annexe XIII of the presentation report was the ONLY justification supplied for those modifications. Published date is the site's own upload timestamp in the filename (1768604969), not a printed date."),

    ("CC-Declaration-Generale-de-Conformite-2024.pdf",
     "civ-cc-declaration-generale-de-conformite-2024", "2026-01-16", "day", "inferred",
     "D\u00e9claration g\u00e9n\u00e9rale de conformit\u00e9 \u2013 exercice 2024",
     "Cour des comptes de C\u00f4te d'Ivoire",
     CC + "1768604868DeclarationGeneraledeConformite2024.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "cour-des-comptes-cote-divoire",
     "Art. 50/84 LOLF conformity declaration between the ordonnateurs' and the comptables publics' accounts. 6pp native."),

    ("CC-Rapport-dAudit-de-Performance-des-Programmes-2024.pdf",
     "civ-cc-rapport-audit-performance-programmes-2024", "2026-01-16", "day", "inferred",
     "Rapport d'audit de performance des programmes \u2013 exercice 2024",
     "Cour des comptes de C\u00f4te d'Ivoire",
     CC + "1768604754RapportdAuditdePerormancedesProgrammes2024.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "cour-des-comptes-cote-divoire",
     "The Cour's own audit of programme performance -- the independent check on the RAP's self-reported execution rates. 82pp native. Note the site's filename misspells 'Perormance'."),

    ("CC-Rapport-Public-Annuel-2024.pdf",
     "civ-cc-rapport-public-annuel-2024", "2025-05-19", "day", "source",
     "Rapport public annuel de la Cour des comptes \u2013 exercice 2024",
     "Cour des comptes de C\u00f4te d'Ivoire",
     CC + "1751494018RAPPORT%20COUR%20DES%20COMPTES%202024_19052025%20B_Site.pdf",
     "audited-accounts", '["2024"]', "FCFA full units",
     "cour-des-comptes-cote-divoire",
     "IMAGE-ONLY: 83 MB for 75pp and 74 extractable characters. The only wholly scanned Cour des comptes document of the four. OCR precondition. Date taken from the internal '19052025' in the site's own filename."),

    ("MTND-Presentation-Projet-de-Budget-2025-AN-2024-11-20.pdf",
     "civ-mtnd-presentation-projet-de-budget-2025", "2024-11-20", "day", "source",
     "Pr\u00e9sentation du projet de budget 2025 du Minist\u00e8re de la Transition Num\u00e9rique et de la Digitalisation \u00e0 la Commission des Affaires \u00c9conomiques et Financi\u00e8res de l'Assembl\u00e9e Nationale",
     "Minist\u00e8re de la Transition Num\u00e9rique et de la Digitalisation",
     MTND + "173214119048.pdf",
     "statement", '["2023", "2024", "2025"]', "FCFA full units",
     "ministry-of-digital-transition-cote-divoire,assemblee-nationale-cote-divoire,ansut,artci",
     "BLOCK 5 / the naming companion. The minister's own budget-defence deck. Reports FY2023 execution (38 380 184 733 budget, 38 362 092 561 executed, 99,95%) and restructures the ministry into FOUR programmes from FY2025, splitting the two CST out as Programme 3 (ANSUT levy) and Programme 4 (telecom-regulation levy) -- which is why the FY2024 three-programme structure and the FY2025 four-programme structure are not directly comparable. Prices individual FY2025 activities the estimates volume only names."),

    ("MTND-Presentation-Projet-de-Budget-2026-AN-2025-11.pdf",
     "civ-mtnd-presentation-projet-de-budget-2026", "2025-11-20", "day", "inferred",
     "Pr\u00e9sentation du projet de budget 2026 du Minist\u00e8re de la Transition Num\u00e9rique et de la Digitalisation \u00e0 la Commission des Affaires \u00c9conomiques et Financi\u00e8res de l'Assembl\u00e9e Nationale",
     "Minist\u00e8re de la Transition Num\u00e9rique et de la Digitalisation",
     MTND + "176366961723.pdf",
     "statement", '["2024", "2025", "2026"]', "FCFA full units",
     "ministry-of-digital-transition-cote-divoire,assemblee-nationale-cote-divoire",
     "BLOCK 5, and the source of the run's open contradiction. Gives the ministry's OWN FY2024 final position: Administration Generale 1 505 459 066 (2,86%) / Economie Numerique et Poste 23 437 413 869 (44,54%) / Comptes Speciaux du Tresor 27 676 208 542 (52,6%) = 52 619 081 477, executed 52 542 091 114 = 99,85%. The RAP 2024 gives Programme 2 revised as 18 185 498 592 and leaves the CST at 36 470 000 000. Same ministry, same fiscal year, two figures. Date inferred from the site's upload timestamp (1763669617)."),
]


def norm(s):
    return s


def main():
    rows = []
    for (orig, slug, pub, prec, dsrc, title, publisher, url, dtype,
         fy_cov, scale, ents, notes) in DOCS:
        src = os.path.join(DIR, orig)
        if not os.path.exists(src):
            print("MISSING: " + orig, file=sys.stderr)
            continue
        new_pdf = "%s-%s.pdf" % (pub, slug)
        new_md = "%s-%s-companion.md" % (pub, slug)
        dst = os.path.join(DIR, new_pdf)
        if src != dst:
            os.rename(src, dst)
        txt = subprocess.run(["pdftotext", "-enc", "UTF-8", dst, "-"],
                             capture_output=True).stdout.decode("utf-8", "replace")
        pages = txt.count("\f") + 1
        chars = len(txt)
        layer = "native" if chars > pages * 200 else (
            "image-only" if chars < 200 else "sparse/partial")
        ent_list = "[" + ", ".join("[[%s]]" % e for e in ents.split(",")) + "]"
        body = u"""---
type: source
title: {title}
url: {url}
publisher: {publisher}
published: {pub}
date_precision: {prec}
date_source: {dsrc}
places: [CIV]
topics: [finance.budget]
entities: {ents}
lens: []
retrieved: {ret}
sweep_batch: {batch}
fiscal_years_covered: {fy}
doc_type: {dtype}
source_tier: {tier}
artefact: {pdf}
body_completeness: full
---

# {title}

**Artefact:** `{pdf}` (sibling, same folder) — {pages} pp, {chars} extractable
characters, **{layer}**.

**Scale and currency printed:** {scale}. Côte d'Ivoire's fiscal year is the
calendar year (FY2024 = 2024-01-01 to 2024-12-31).

**Held, not yet extracted.** This page is a head start for the extraction pass,
not an admitted source.

## Why it was staged

{notes}
""".format(title=title, url=url, publisher=publisher, pub=pub, prec=prec,
           dsrc=dsrc, ents=ent_list, ret=RETRIEVED, batch=BATCH, fy=fy_cov,
           dtype=dtype,
           tier=("official-statement" if dtype == "statement" else "budget-document"),
           pdf=new_pdf, pages=pages, chars="{:,}".format(chars), layer=layer,
           scale=scale, notes=notes)
        with io.open(os.path.join(DIR, new_md), "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write(body)
        rows.append([
            "CIV", "2024", fy_cov.replace('"', "").replace("[", "").replace("]", ""),
            dtype, title, url,
            "new-budget/CIV/2024/" + new_pdf,
            "new-budget/CIV/2024/" + new_md,
            RETRIEVED, scale, "XOF", str(pages), "", "", "", "",
            "%s; %s" % (layer, notes.replace("\n", " ")),
        ])

    with io.open(MANIFEST, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        for r in rows:
            w.writerow(r)
    print("staged %d documents" % len(rows))


if __name__ == "__main__":
    main()
