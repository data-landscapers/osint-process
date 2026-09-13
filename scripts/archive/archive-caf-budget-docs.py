# -*- coding: utf-8 -*-
"""Archive the CAF FY2024-FY2026 budget documents after the 2026-07-26 budget-extract
pass: move artefact (+ any OCR sidecar) and companion from new-budget/CAF/{FY}/ to
budget-archive/CAF/{FY}/, and set extracted / extracted_scope / re_extract /
archive_path on each manifest row.

Moving the file is the LAST step (BUDGET-EXTRACT.md §6), so an interrupted run
resumes on exactly the documents not yet processed.
"""
import csv
import glob
import os
import shutil
import sys

sys.stdout.reconfigure(encoding="utf-8")
MAN = "new-budget/manifest.csv"
TODAY = "2026-07-26"

OCR_PARTIAL = (
    "OCR-partial - sidecar .ocr.txt written and committed beside the artefact; "
    "ministry rows are legible in structure but the digits do not cross-foot against "
    "anything held, so no figure was recorded (BUDGET-EXTRACT.md §1)"
)
OCR_NEEDED = (
    "OCR-needed - image-only; superseded for every figure in scope by the native "
    "projet de loi de finances of the following year, whose prior-year comparator "
    "column restates it"
)

# artefact filename stem -> (extracted_scope, re_extract)
SCOPE = {
    # --- the three native volumes: the whole extraction rests on these ---
    "2025-11-18-plf-2026": ("cross-vote", "no"),
    "2024-12-10-plf-2025-charges": ("cross-vote", "no"),
    "2026-03-24-cdmt-sectoriel-2026": ("cross-vote", "no"),
    # --- native supporting documents, read for aggregates and narrative ---
    "2024-03-20-budget-citoyen-2024": ("narrative", "no"),
    "2025-03-31-budget-citoyen-2025": ("narrative", "no"),
    "2026-02-19-budget-citoyen-2026": ("narrative", "no"),
    "2026-02-04-note-information-titres-publics-2026": ("narrative", "no"),
    "2025-11-18-risques-budgetaires-plf-2026": ("narrative", "no"),
    "2025-03-26-note-cadrage-e-finances-publiques": ("narrative", "no"),
    "2024-08-31-pnd-rca-2024-2028": ("narrative", "no"),
    "2026-02-01-rapport-annuel-performance-eep-2023-2024": ("narrative", "no"),
    # --- OCR'd this pass, sidecar held, digits not cross-footable ---
    "2024-05-15-reb-t1-2024": ("n/a", OCR_PARTIAL),
    "2024-08-05-reb-t2-2024": ("n/a", OCR_PARTIAL),
    "2024-11-22-reb-t3-2024": ("n/a", OCR_PARTIAL),
    "2025-02-19-reb-t4-2024": ("n/a", OCR_PARTIAL),
    "2025-05-17-reb-t1-2025": ("n/a", OCR_PARTIAL),
    "2025-08-28-reb-t2-2025": ("n/a", OCR_PARTIAL),
    "2025-11-11-reb-t3-2025": ("n/a", OCR_PARTIAL),
    "2026-02-24-reb-t4-2025": ("n/a", OCR_PARTIAL),
    "2026-05-20-reb-t1-2026": ("n/a", OCR_PARTIAL),
    "2025-01-17-marches-aboutis-contrat-2024": (
        "n/a",
        "OCR-partial - sidecar held; `Fonds Propres`, vendor names and several amounts "
        "are legible, but a 13-page landscape contract table has no internal arithmetic "
        "to cross-foot a row against, so it is a locator and not a source of figures",
    ),
    "2025-09-03-marches-aboutis-contrat-s1-2025": (
        "n/a",
        "OCR-partial - sidecar held; same limitation as the FY2024 contract table",
    ),
    "2023-11-13-arrete-1099-programmes-dotations": ("narrative", "OCR-partial - sidecar held; the programme/dotation codebook, read for vocabulary only"),
    "2024-12-10-plf-2025-texte-de-loi": ("narrative", "OCR-partial - sidecar held; the articulated law, no estimates"),
    "2024-12-10-plf-2025-ressources": ("narrative", "OCR-partial - sidecar held; revenue side only, supports no expenditure record"),
    # --- image-only, superseded by the native prior-year columns ---
    "2024-01-05-loi-de-finances-2024": ("n/a", "OCR-needed - image-only (0 chars, 675pp, 187 MB); the enacted FY2024 appropriation. Nothing in this pass depends on it: FY2024 revised is recovered from the native FY2025 PLF's `Collectif 2024` column"),
    "2024-11-04-collectif-budgetaire-2024": ("n/a", OCR_NEEDED),
    "2025-01-02-loi-de-finances-2025": ("n/a", "OCR-needed - image-only (0 chars, 608pp); the enacted FY2025 appropriation. Until it is read, no CAF figure may be labelled `appropriated`"),
    "2025-07-06-collectif-budgetaire-2025": ("n/a", OCR_NEEDED),
    "2025-12-29-loi-de-finances-2026": ("n/a", "OCR-needed - image-only (624 chars, 624pp, 137 MB); the enacted FY2026 appropriation. Until it is read, no CAF figure may be labelled `appropriated`"),
    "2025-04-04-tdr-recrutement-it-sim-ba": ("n/a", "OCR-needed - image-only terms of reference; supports no record"),
}
PPM_NOTE = (
    "OCR-needed - image-only procurement plan; the FY2026 batch is additionally "
    "anonymised (filenames are the scanner's own `numerisation00NN`), so the "
    "procuring entity is not identifiable without OCR"
)

rows = list(csv.DictReader(open(MAN, encoding="utf-8")))
fields = list(rows[0].keys())
moved = 0
touched = 0
for r in rows:
    if r["iso3"] != "CAF":
        continue
    art = r["artefact_path"]
    comp = r["companion_path"]
    if not art.startswith("new-budget/"):
        continue
    stem = os.path.splitext(os.path.basename(art))[0]
    fy = r["fiscal_year"]
    dest_dir = "budget-archive/CAF/%s" % fy
    os.makedirs(dest_dir, exist_ok=True)
    if stem in SCOPE:
        scope, reex = SCOPE[stem]
    elif "ppm-" in stem or "pppm-" in stem:
        scope, reex = "n/a", PPM_NOTE
    else:
        scope, reex = "narrative", "no"
    r["extracted"] = TODAY
    r["extracted_scope"] = scope
    r["re_extract"] = reex
    new_art = "%s/%s" % (dest_dir, os.path.basename(art))
    new_comp = "%s/%s" % (dest_dir, os.path.basename(comp)) if comp else ""
    r["archive_path"] = new_art
    r["artefact_path"] = new_art
    if comp:
        r["companion_path"] = new_comp
    pairs = [(art, new_art), (comp, new_comp)]
    sidecar = os.path.splitext(art)[0] + ".ocr.txt"
    if os.path.exists(sidecar):
        pairs.append((sidecar, os.path.splitext(new_art)[0] + ".ocr.txt"))
    for src, dst in pairs:
        if src and os.path.exists(src):
            shutil.move(src, dst)
            moved += 1
    touched += 1

with open(MAN, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

# remove emptied folders
for fy in ("2024", "2025", "2026"):
    d = "new-budget/CAF/%s" % fy
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
if os.path.isdir("new-budget/CAF") and not os.listdir("new-budget/CAF"):
    os.rmdir("new-budget/CAF")

print("manifest rows updated: %d ; files moved: %d" % (touched, moved))
left = glob.glob("new-budget/CAF/**/*", recursive=True)
print("left in new-budget/CAF: %d" % len(left))
