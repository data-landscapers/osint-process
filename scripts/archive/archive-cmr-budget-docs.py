# -*- coding: utf-8 -*-
"""Archive CMR budget documents and set their manifest columns (budget-extract steps 5a and 6)."""
import io, os, csv, shutil

ROOT = "C:/Users/bill/OSINT"
MAN = os.path.join(ROOT, "new-budget/manifest.csv")
DATE = "2026-07-29"

# stem-fragment -> (extracted_scope, re_extract)
RULES = [
 ("projet-de-loi-de-finances", "cross-vote",
  "no"),
 ("ordonnance-2024-001", "sector-vote",
  "revised columns read for chapitre 45 only; the restated article 81 covers all 59 chapitres and would yield cross-vote revised figures"),
 ("ordonnance-2025-001", "sector-vote",
  "revised columns read for chapitre 45 only; cross-vote revised figures not extracted"),
 ("loi-2023-019", "n/a",
  "page-image scan; appropriation table not read. The PLF 2024 and the ordonnance's AE VOTE column were used instead"),
 ("finance-law-2024-english-ocr", "n/a",
  "OCR layer present but amounts are locators only; superseded by the native PLF 2024 for every figure used"),
 ("loi-2024-013", "n/a",
  "page-image scan (2 158 chars over 110pp); PLF 2025 used instead"),
 ("loi-2025-012", "n/a",
  "page-image scan (112 MB / 2 265 chars); PLF 2026 used instead. Reading it is what would convert FY2026 from proposed to appropriated"),
 ("finance-law-2026-english", "n/a",
  "page-image scan, no OCR layer"),
 ("loi-2025-011", "n/a",
  "page-image scan; the settled FY2024 accounts are unread. Would yield the audited stage"),
 ("settlement-law-2024-english", "n/a",
  "page-image scan, no OCR layer"),
 ("chambre-des-comptes-rapport-execution", "narrative",
  "per-ministry x programme execution table located (dotation / execution / ecart, full FCFA) but rows drift against labels under pdftotext -layout; needs geometry binding to yield actual and audited stages for chapitre 45 and 37"),
 ("chambre-des-comptes-rapport-certification", "narrative",
  "MINPOSTEL named 3 times; certification exceptions not read line by line"),
 ("chambre-des-comptes-compte-general", "narrative",
  "internal-control findings on public financial management systems not extracted"),
 ("chambre-des-comptes-avis", "narrative", "no"),
 ("rapport-execution-budget-etat-fin-juin-2024", "narrative",
  "half-year execution review carries no MINPOSTEL or chapitre-level breakdown; aggregate only"),
 ("state-budget-execution-report", "narrative",
  "English edition of the above; same aggregate-only limitation"),
 ("budget-citoyen", "narrative",
  "BIP-by-ministry and CAS tables read; not a source of programme lines"),
 ("tofe", "n/a",
  "aggregate government finance statistics, no ministry detail; supports no line record"),
 ("rapport-situation-perspectives", "n/a",
  "page-image scan, 0 extractable characters; OCR not attempted this pass"),
 ("dpebmt", "n/a",
  "MTEF scan; outer-year figures are indicative and fail the stage test by design"),
 ("expose-des-motifs", "narrative", "no"),
 ("plf-2025-annexe-rapports", "narrative",
  "151pp of per-ministry narrative not read; the most likely home of named digital systems behind the programme lines"),
 ("plf-2025-annexe-analyse-risque", "narrative",
  "CAMTEL and CAMPOST state-enterprise exposure not extracted"),
 ("plf-2025-annexe-decentralisation", "n/a", "sub-national, out of scope for this sweep"),
 ("plf-2025-annexe-repartition", "n/a", "headcount ceilings, not money"),
 ("expose-dgb", "narrative", "no"),
 ("expose-minmap", "narrative",
  "procurement-reform slides; no priced digital lines"),
 ("circulaire", "n/a",
  "page-image scan; structural procedure, supports no record"),
]


def scope_for(stem):
    for frag, scope, re_x in RULES:
        if frag in stem:
            return scope, re_x
    return "n/a", "unclassified by the archive pass"


rows = list(csv.reader(io.open(MAN, encoding="utf-8", newline="")))
hdr, body = rows[0], rows[1:]
ix = {k: i for i, k in enumerate(hdr)}
moved = 0

for r in body:
    if r[ix["iso3"]] != "CMR" or r[ix["extracted"]]:
        continue
    art = r[ix["artefact_path"]]
    comp = r[ix["companion_path"]]
    fy = r[ix["fiscal_year"]]
    stem = os.path.basename(art)
    scope, re_x = scope_for(stem)
    dest_dir = os.path.join(ROOT, "budget-archive/CMR", fy)
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    for src_rel in (art, comp):
        src = os.path.join(ROOT, src_rel)
        if os.path.exists(src):
            shutil.move(src, os.path.join(dest_dir, os.path.basename(src_rel)))
            moved += 1
    r[ix["extracted"]] = DATE
    r[ix["extracted_scope"]] = scope
    r[ix["re_extract"]] = re_x
    r[ix["archive_path"]] = "budget-archive/CMR/%s/%s" % (fy, stem)

with io.open(MAN, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(hdr)
    for r in body:
        w.writerow(r)

# delete emptied folders
base = os.path.join(ROOT, "new-budget/CMR")
for fy in sorted(os.listdir(base)) if os.path.isdir(base) else []:
    d = os.path.join(base, fy)
    if os.path.isdir(d) and not os.listdir(d):
        os.rmdir(d)
        print("removed", d)
if os.path.isdir(base) and not os.listdir(base):
    os.rmdir(base)
    print("removed", base)

print("files moved:", moved)
