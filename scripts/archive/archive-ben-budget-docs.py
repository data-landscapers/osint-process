# -*- coding: utf-8 -*-
"""Archive the BEN 2024/2025/2026 budget documents after the 2026-07-25 extract pass.

Sets extracted / extracted_scope / re_extract / archive_path on every BEN manifest row,
moves each artefact and its staging companion from new-budget/ to budget-archive/,
then removes the emptied country-year folders.
"""
import csv, os, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")
TODAY = "2026-07-25"
MANIFEST = "new-budget/manifest.csv"

# stem -> (extracted_scope, re_extract)
SCOPE = {
    # --- FY2024 ---
    "2026-07-25-ben-dgb-opendata-budget-classifications": (
        "cross-vote",
        "no - all 80 programmes and 33 institutions read for FY2024; programme 044 figure rejected as a portal error against the workbook and the MTFP PAP"),
    "2025-01-16-ben-tableaux-classifications-croisees-lf-2025": (
        "cross-vote",
        "no - all 107 programme/dotation lines read for FY2024 and FY2025, with the interior/exterior split"),
    "2023-12-20-ben-loi-2023-01-loi-de-finances-2024": (
        "n/a", "OCR-needed (task 28) - scanned with dirty OCR; digits not safely readable"),
    "2023-10-04-ben-plf-2024-projet-loi-finances": (
        "n/a", "OCR-needed (task 28) - scanned with dirty OCR"),
    "2024-01-08-ben-rapport-presentation-lf-2024": (
        "narrative", "no - narrative context; the estimates volume carries the figures"),
    "2023-05-09-ben-dpbep-2024-2026-document-principal": (
        "narrative", "no - MTEF outer years are not records (driver: MTEF projections fail fact 3)"),
    "2023-05-09-ben-dpbep-2024-2026-annexes": (
        "narrative", "no - MTEF outer years are not records"),
    "2023-12-10-ben-rapport-special-budget-mnd-2024": (
        "sector-vote",
        "no - per-project credits read; they are prior-year comparators, not FY2024 appropriations"),
    "2023-12-10-ben-rapport-special-budget-apdp-2024": (
        "sector-vote", "no - APDP 488 277 000 FCFA confirmed against the workbook and the API"),
    "2023-12-10-ben-rapport-special-budget-mef-2024": ("narrative", "no"),
    "2023-12-10-ben-rapport-special-budget-justice-2024": ("narrative", "no"),
    "2023-12-10-ben-rapport-special-budget-interieur-2024": ("narrative", "no"),
    "2023-12-10-ben-rapport-special-budget-cena-2024": ("narrative", "no"),
    "2024-06-17-ben-rapex-31-mars-2024": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan; per-ministry digits unreadable"),
    "2024-09-13-ben-rapex-30-juin-2024": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan"),
    "2024-11-13-ben-rapex-30-septembre-2024": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan"),
    "2025-03-14-ben-rapex-31-decembre-2024": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan; the FY2024 annual outturn"),
    "2024-09-18-ben-an-rapport-special-apdp": (
        "n/a", "OCR-needed (task 28) - image-only, 0 characters"),
    "2024-12-03-ben-an-rapport-commission-rapex-30-juin-2024": (
        "n/a", "OCR-needed (task 28) - image-only, 0 characters"),
    "2024-12-03-ben-an-rapport-commission-rapex-31-mars-2024": (
        "n/a", "OCR-needed (task 28) - image-only, 0 characters"),
    "2024-12-11-ben-an-rapport-special-ministere-numerique-digitalisation": (
        "n/a", "OCR-needed (task 28) - image-only, 0 characters"),
    "2024-12-13-ben-rapport-decryptage-lf-2024": ("narrative", "no"),
    "2025-05-05-ben-arcep-rapport-annuel-activites-2024": (
        "narrative",
        "no - ARCEP own resources 6 520 742 720 FCFA read; own-source regulator, outside the loi de finances"),
    # --- FY2025 ---
    "2024-12-30-ben-loi-de-finances-gestion-2025": (
        "n/a", "OCR-needed (task 28) - image-only enacted law"),
    "2024-10-02-ben-plf-2025-projet-loi-finances": ("n/a", "OCR-needed (task 28)"),
    "2024-09-18-ben-decret-2024-1113-transmission-plf-2025": ("narrative", "no"),
    "2024-10-02-ben-rapport-presentation-plf-2025": ("narrative", "no"),
    "2025-01-02-ben-rapport-presentation-lf-2025": ("narrative", "no"),
    "2024-10-03-ben-dpbep-2025-2027-document-principal": (
        "narrative", "no - MTEF outer years are not records"),
    "2024-10-03-ben-dpbep-2025-2027-annexes": ("narrative", "no - MTEF outer years are not records"),
    "2024-10-03-ben-note-orientations-strategiques-investissements-publics-2025-2027": (
        "narrative", "no"),
    "2024-10-07-ben-discours-mef-citoyens-plf-2025": ("narrative", "no"),
    "2024-12-11-ben-an-rapport-special-interieur-2025": ("narrative", "no"),
    "2024-12-11-ben-an-rapport-special-justice-2025": ("narrative", "no"),
    "2024-12-11-ben-an-rapport-special-mef-2025": ("narrative", "no"),
    "2024-12-30-ben-comptes-speciaux-tresor-gestion-2025": (
        "sector-vote", "no - CAS 108 Modernisation des regies financieres 6 000 000 kFCFA confirmed"),
    "2024-12-31-ben-dob-2025-2027": ("narrative", "no"),
    "2025-01-03-ben-analyse-risques-budgetaires-lf-2025": ("narrative", "no"),
    "2025-01-07-ben-instructions-modalites-execution-budgets-2025": ("narrative", "no"),
    "2025-06-20-ben-rapex-31-mars-2025": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan"),
    "2025-09-09-ben-rapex-30-juin-2025": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan"),
    "2025-12-08-ben-rapex-30-septembre-2025": (
        "n/a", "OCR-needed (task 28) - dirty OCR layer over a scan"),
    "2026-03-27-ben-rapex-31-decembre-2025": (
        "n/a",
        "OCR-needed (task 28) - HIGHEST-VALUE UNBLOCK: p.59 carries Synthese des mouvements de credits par ministere (dotation initiale / annule / complementaire / finale), the only FY2025 revised stage"),
    "2025-07-18-ben-examen-parlement-plf-2025": ("narrative", "no"),
    "2025-09-18-ben-article-decryptage-lf-2025": ("narrative", "no"),
    "2026-05-01-ben-arcep-rapport-annuel-activites-2025": (
        "narrative",
        "no - ARCEP own resources 4 768 581 763 FCFA (-26.9%) read; own-source regulator, outside the loi de finances"),
    "2026-07-08-ben-tableaux-statistiques-rapport-fin-annee-2025": (
        "narrative",
        "no - NATIVE XLSX but economic-nature grain only, no ministry or programme; supports no digital line record (see strategy library, Not worth extracting)"),
    # --- FY2026 ---
    "2026-02-06-ben-classifications-croisees-2022-2028-lf-2026": (
        "cross-vote", "no - all programme and dotation lines read for FY2026 with the interior/exterior split"),
    "2025-12-03-ben-classifications-croisees-2023-2028-plf-2026": (
        "cross-vote", "no - PLF-stage edition; proposed equals enacted on every digital line"),
    "2026-06-09-ben-note-de-presentation-plfr-2026": (
        "cross-vote",
        "no - Annexe 2 read at programme grain for all six digital lines, with the domestic/emprunt execution split"),
    "2025-12-30-ben-pap-vlf-mnd-2026": (
        "sector-vote", "no - AE/CP schedules for programmes 100, 109, 111 across 2023-2028"),
    "2025-12-30-ben-pap-vlf-mtfp-2026": (
        "sector-vote",
        "no - AE/CP schedule for programme 044 across 2023-2028; the arbiter of the open 044 contradiction"),
    "2025-12-30-ben-pap-vlf-mef-2026": ("sector-vote", "no - no digital programme beyond CAS 108"),
    "2025-12-30-ben-pap-vlf-mjl-2026": (
        "sector-vote",
        "no - programme 020 Services judiciaires is a multi-purpose envelope; no separable justice-modernisation line"),
    "2026-01-01-ben-dppd-2026-2028-mnd": (
        "narrative", "no - three-year programming; outer years are not records"),
    "2025-12-31-ben-tableau-a-annexe-lf-2026": (
        "cross-vote", "no - per-section credits; the workbook carries the same money at finer grain"),
    "2025-12-31-ben-tableau-b-annexe-lf-2026": ("cross-vote", "no"),
    "2026-06-09-ben-tableau-a-annexe-plfr-2026": (
        "cross-vote",
        "no - read for the Credits initiaux reconstitues crosswalk across the 24-May-2026 ministry split; MTDI 14 556 387 -> 16 262 316 kFCFA"),
    "2026-06-09-ben-liste-des-dotations-plfr-2026": ("cross-vote", "no"),
    "2026-06-14-ben-liste-des-programmes-plfr-2026": (
        "cross-vote", "no - confirms programme 108 dropped from the list and 044 moved to the MBFP"),
    "2025-12-31-ben-tableau-matriciel-administrative-economique-2026": ("cross-vote", "no"),
    "2025-12-31-ben-tableau-matriciel-programmatique-economique-2026": ("cross-vote", "no"),
    "2025-12-29-ben-comptes-speciaux-du-tresor-gestion-2026": (
        "sector-vote", "no - CAS 108 confirmed at 6 000 000 kFCFA in the enacted LF 2026"),
    "2026-01-01-ben-programme-investissement-public-2026-2028": (
        "cross-vote",
        "no - project grain with financing source; corroborates the origin split, no separable digital project beyond the programme lines already recorded"),
    "2025-12-31-ben-loi-de-finances-2026": ("n/a", "OCR-needed (task 28) - image-only, 15 pp"),
    "2026-06-09-ben-plfr-2026-projet-loi-finances-rectificative": (
        "n/a", "OCR-needed (task 28) - image-only, 17 pp"),
    "2026-06-09-ben-decret-de-saisine-plfr-2026": (
        "n/a", "OCR-needed (task 28) - image-only, 13 pp"),
    "2026-06-16-ben-rapex-au-31-mars-2026": (
        "n/a", "OCR-needed (task 28) - no text layer at all, 0 characters, 78 pp"),
    "2025-12-31-ben-rapport-de-presentation-lf-2026": ("narrative", "no"),
    "2025-12-29-ben-dpbep-2026-2028-document-principal": (
        "narrative", "no - MTEF outer years are not records; text layer regressed to near-image"),
    "2025-12-29-ben-annexes-au-dpbep-2026-2028": ("narrative", "no - MTEF outer years are not records"),
    "2025-09-18-ben-article-dob-2026-2028": ("narrative", "no"),
    "2025-10-09-ben-rapport-economique-et-financier-plf-2026": ("narrative", "no"),
    "2025-12-22-ben-examen-au-parlement-plf-2026": ("narrative", "no"),
    "2026-01-02-ben-declaration-risques-budgetaires-lf-2026": ("narrative", "no"),
    "2026-06-25-ben-article-sur-le-plfr-2026": ("narrative", "no"),
}

rows = list(csv.DictReader(open(MANIFEST, encoding="utf-8")))
fields = rows[0].keys()
moved = missed = 0
unknown = []

for r in rows:
    if r["iso3"] != "BEN":
        continue
    art = r["artefact_path"]
    stem = os.path.splitext(os.path.basename(art))[0]
    if stem not in SCOPE:
        unknown.append(stem)
        continue
    scope, reex = SCOPE[stem]
    dest_dir = os.path.dirname(art).replace("new-budget", "budget-archive")
    os.makedirs(dest_dir, exist_ok=True)
    r["extracted"] = TODAY
    r["extracted_scope"] = scope
    r["re_extract"] = reex
    r["archive_path"] = os.path.join(dest_dir, os.path.basename(art)).replace(os.sep, "/")
    for src in (art, r["companion_path"]):
        if src and os.path.exists(src):
            shutil.move(src, os.path.join(dest_dir, os.path.basename(src)))
            moved += 1
        elif src:
            missed += 1

with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(fields))
    w.writeheader()
    w.writerows(rows)

print("moved", moved, "files;", missed, "already absent")
if unknown:
    print("NO SCOPE ENTRY for:", *unknown, sep="\n  ")

# remove emptied folders
for fy in ("2024", "2025", "2026"):
    d = os.path.join("new-budget", "BEN", fy)
    if os.path.isdir(d):
        left = os.listdir(d)
        if not left:
            os.rmdir(d)
            print("removed", d)
        else:
            print("STILL POPULATED", d, left)
d = os.path.join("new-budget", "BEN")
if os.path.isdir(d) and not os.listdir(d):
    os.rmdir(d)
    print("removed", d)
