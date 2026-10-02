"""Country-year by document-type table of what budget-archive/ holds.

OSINT's half of check A in the budget data review (X:\\documentation\\budget-data-review.md).
One row per country and fiscal year 2024-2026, from the companions' `doc_type`, filed by
folder year. Writes lookups/budget-archive-holdings.csv, which CORPUS can read.

hole:
  no-year    nothing held for the year
  no-core    documents held, but no estimates, appropriation act or enacting instrument
  thin-set   estimates and act volumes under half the country's fullest year
             (countries publishing a volume per ministry)

The documents are the manifest's rows (new-budget/manifest.csv) plus any archive page it
lacks. no_page counts artefacts with no companion page, which CORPUS cannot cite.

disposition, from lookups/budget-archive-hole-dispositions.csv, closes a flagged hole the
archive alone cannot: absence-stated (a dated absence on the place hub) or not-a-hole
(the year's published set is that shape). A hole with no disposition is open work.

    python scripts/budget-archive-holdings.py [--check]
"""
import csv
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE = ROOT / "budget-archive"
OUT = ROOT / "lookups" / "budget-archive-holdings.csv"
DISPOSITIONS = ROOT / "lookups" / "budget-archive-hole-dispositions.csv"
YEARS = ["2024", "2025", "2026"]
CORE = ("appropriation-act", "budget-estimates", "executive-instrument")


def doc_types():
    with open(ROOT / "lookups" / "budget-doc-types.csv", encoding="utf-8-sig") as f:
        return [r["doc_type"] for r in csv.DictReader(f)]


def countries():
    with open(ROOT / "lookups" / "budget-init-backlog.csv", encoding="utf-8-sig") as f:
        return [r["iso-3"] for r in csv.DictReader(f) if r["Budget Done"].strip() != "n/a"]


def documents():
    """{(iso, fy): [(doc_type, has_page)]} from the manifest, plus any page it lacks.

    A companion's own doc_type wins over the manifest's, which can lag a correction."""
    docs = {}
    seen = set()
    with open(ROOT / "new-budget" / "manifest.csv", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            parts = r["archive_path"].split("/")
            if len(parts) < 4:
                continue
            page = None
            if r["companion_path"]:
                # an older row can still name its pre-archive new-budget/ path
                page = ROOT / r["companion_path"]
                if not page.exists():
                    page = ARCHIVE / parts[1] / parts[2] / page.name
            t = page_type(page) if page and page.exists() else None
            docs.setdefault((parts[1], parts[2]), []).append((t or r["doc_type"], bool(page and page.exists())))
            seen.add(Path(r["archive_path"]).stem)
            if page:
                seen.add(page.stem)
    for p in ARCHIVE.glob("*/*/*.md"):
        if p.stem in seen or re.sub(r"-companion$", "", p.stem) in seen:
            continue
        docs.setdefault((p.parent.parent.name, p.parent.name), []).append((page_type(p) or "unknown", True))
    return docs


def page_type(p):
    m = re.search(r"^doc_type:\s*(\S+)", p.read_text(encoding="utf-8", errors="replace"), re.M)
    return m.group(1) if m else None


def dispositions():
    if not DISPOSITIONS.exists():
        return {}
    with open(DISPOSITIONS, encoding="utf-8-sig") as f:
        return {(r["iso3"], r["fy"]): f'{r["disposition"]} ({r["as_of"]})' for r in csv.DictReader(f)}


def build():
    types = doc_types()
    disp = dispositions()
    docs = documents()
    rows = []
    for iso in countries():
        per = {fy: Counter(t for t, _ in docs.get((iso, fy), [])) for fy in YEARS}
        bare = {fy: sum(1 for _, has in docs.get((iso, fy), []) if not has) for fy in YEARS}
        vols = {fy: per[fy]["budget-estimates"] + per[fy]["appropriation-act"] for fy in YEARS}
        vol_max = max(vols.values())
        for fy in YEARS:
            c = per[fy]
            n = sum(c.values())
            if n == 0:
                hole = "no-year"
            elif not any(c[t] for t in CORE):
                hole = "no-core"
            elif vol_max >= 6 and vols[fy] * 2 < vol_max:
                hole = "thin-set"
            else:
                hole = ""
            rows.append({"iso3": iso, "fy": fy, "documents": n, **{t: c[t] or "" for t in types},
                         "no_page": bare[fy] or "", "hole": hole,
                         "disposition": disp.get((iso, fy), "") if hole else ""})
    return ["iso3", "fy", "documents", *types, "no_page", "hole", "disposition"], rows


def main():
    fields, rows = build()
    if "--check" not in sys.argv:
        with open(OUT, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    holes = Counter(r["hole"] for r in rows if r["hole"])
    open_ = [f'{r["iso3"]} {r["fy"]}' for r in rows if r["hole"] and not r["disposition"]]
    print(f"{len(rows)} country-years; holes: " + ", ".join(f"{k} {v}" for k, v in sorted(holes.items()))
          + f"; open {len(open_)}" + (": " + ", ".join(open_) if open_ else ""))


if __name__ == "__main__":
    main()
