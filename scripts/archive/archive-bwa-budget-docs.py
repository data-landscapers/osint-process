# -*- coding: utf-8 -*-
"""Archive the BWA FY2024/25-FY2026/27 budget documents after the 2026-07-25
budget-extract pass: move artefact + companion from new-budget/BWA/{FY}/ to
budget-archive/BWA/{FY}/, and set extracted / extracted_scope / re_extract /
archive_path on each manifest row.

Moving the file is the LAST step (BUDGET-EXTRACT.md §6), so an interrupted run
resumes on exactly the documents not yet processed.
"""
import csv, os, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")
MAN = "new-budget/manifest.csv"
TODAY = "2026-07-25"

# artefact filename stem -> (extracted_scope, re_extract)
SCOPE = {
    # --- the three estimates volumes: read across every organisation ---
    "2024-02-05-bwa-estimates-of-expenditure-consolidated-development-funds-2024-25": ("cross-vote", "no"),
    "2025-02-01-bwa-estimates-of-expenditure-consolidated-development-fund-2025-26": ("cross-vote", "no"),
    "2026-02-01-bwa-expenditure-estimates-2026-27": ("cross-vote", "no"),
    # --- financial statements volumes ---
    "2026-02-01-bwa-financial-statements-tables-estimates-revenues-2026-27": ("cross-vote", "no"),
    "2024-02-05-bwa-financial-statements-tables-estimates-revenues-2024-25": ("narrative", "Tables I-IV not read; the FY2026/27 edition supersedes them for every year in scope"),
    "2025-02-01-bwa-financial-statements-tables-estimates-revenues-2025-26": ("narrative", "Tables I-IV not read; the FY2026/27 edition supersedes them for every year in scope"),
}
# everything else defaults to narrative / no unless listed here
OCR_BLOCKED = {
    "2024-03-31-bwa-appropriation-2024-25-act-2024": ("n/a", "OCR-needed - image-only (3 chars); organisation totals are reproduced in the FY2024/25 estimates volume summary, so nothing depends on it"),
    "2024-02-05-bwa-key-features-2024-25-budget": ("n/a", "OCR-needed - image-only (32 chars); duplicates the native Budget-in-Brief and People's Guide"),
}

rows = list(csv.DictReader(open(MAN, encoding="utf-8")))
fields = rows[0].keys()
moved = skipped = 0
for r in rows:
    if r["iso3"] != "BWA":
        continue
    art = r["artefact_path"]
    comp = r["companion_path"]
    if not art.startswith("new-budget/"):
        continue
    stem = os.path.splitext(os.path.basename(art))[0]
    fy = r["fiscal_year"]
    dest_dir = "budget-archive/BWA/%s" % fy
    os.makedirs(dest_dir, exist_ok=True)
    scope, reex = SCOPE.get(stem, OCR_BLOCKED.get(stem, ("narrative", "no")))
    r["extracted"] = TODAY
    r["extracted_scope"] = scope
    r["re_extract"] = reex
    new_art = "%s/%s" % (dest_dir, os.path.basename(art))
    new_comp = "%s/%s" % (dest_dir, os.path.basename(comp)) if comp else ""
    r["archive_path"] = new_art
    r["artefact_path"] = new_art
    if comp:
        r["companion_path"] = new_comp
    for src, dst in ((art, new_art), (comp, new_comp)):
        if src and os.path.exists(src):
            shutil.move(src, dst)
            moved += 1
        elif src:
            skipped += 1

with open(MAN, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(fields))
    w.writeheader()
    w.writerows(rows)

# remove emptied folders
for fy in ("2024", "2025", "2026"):
    d = "new-budget/BWA/%s" % fy
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
        print("removed", d)
if os.path.isdir("new-budget/BWA") and not os.listdir("new-budget/BWA"):
    os.rmdir("new-budget/BWA")
    print("removed new-budget/BWA")
print("moved %d files, %d already gone" % (moved, skipped))
