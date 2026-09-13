#!/usr/bin/env python3
"""repo-status.py — Repository status report for the Data Landscapers wiki.

Scans raw/**/*.md (PDFs are excluded: each PDF has a counted markdown counterpart)
and emits a markdown report with:
  1. Documents in raw/ by publication year
  2. Documents in raw/ for 2026 by month
  3. Documents in raw/ by country (places facet, mapped via lookups/countries.csv)

Publication year/month come from the `published:` frontmatter field, which every
raw source carries (more robust than the filename, since a handful of companion
files are not date-named). Country counts use the `places:` facet; a document
tagged with N places counts once under each, so the country column sums to more
than the document total. Region/bloc codes (XAF, XWA, ...) are reported in a
separate table from single countries.

Every table here measures CAPTURE, not the world. The by-month table especially:
it tracks when the sweeps ran and which countries were being initialised, not how
much happened. It carries that caveat in its own generated header, because it is
exactly the number a reader would otherwise quote as activity.

Usage:  python scripts/repo-status.py [--out reviews/repo-status.md]
Run from the repo root.
"""
import os
import re
import sys
import glob
from collections import Counter
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
COUNTRIES_CSV = os.path.join(ROOT, "lookups", "countries.csv")


def load_places():
    """Return (name_by_code, is_region_by_code) from countries.csv.

    Region codes are those whose iso-3 begins with 'X' (blocs / regions).
    """
    name = {}
    is_region = {}
    with open(COUNTRIES_CSV, encoding="utf-8-sig") as fh:
        header = fh.readline()
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split(",")
            code = parts[0].strip()
            cname = parts[1].strip() if len(parts) > 1 else ""
            name[code] = cname
            is_region[code] = code.startswith("X")
    return name, is_region


def parse_frontmatter(path):
    """Return dict with 'published' (str|None) and 'places' (list[str])."""
    published = None
    places = []
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if not text.startswith("---"):
        return {"published": None, "places": []}
    # frontmatter is between the first two '---' fences
    end = text.find("\n---", 3)
    fm = text[3:end] if end != -1 else text[3:]
    for line in fm.splitlines():
        m = re.match(r"\s*published:\s*(\S+)", line)
        if m:
            published = m.group(1).strip().strip('"').strip("'")
        m = re.match(r"\s*places:\s*\[(.*)\]", line)
        if m:
            inner = m.group(1)
            places = [p.strip() for p in inner.split(",") if p.strip()]
    return {"published": published, "places": places}


def main():
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    name_by_code, is_region = load_places()

    md_files = sorted(glob.glob(os.path.join(RAW, "*", "*.md")))   # raw/YYYY/
    total = len(md_files)

    by_year = Counter()
    by_2026_month = Counter()
    by_place = Counter()
    no_date = 0
    no_place = 0

    for path in md_files:
        fm = parse_frontmatter(path)
        pub = fm["published"]
        if pub and re.match(r"\d{4}", pub):
            year = pub[:4]
            by_year[year] += 1
            if year == "2026" and len(pub) >= 7 and re.match(r"\d{4}-\d{2}", pub):
                by_2026_month[pub[5:7]] += 1
        else:
            no_date += 1
        if fm["places"]:
            for code in fm["places"]:
                by_place[code] += 1
        else:
            no_place += 1

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    L = []
    L.append("# Repository Status Report")
    L.append("")
    L.append(f"*Generated {now} — source: `raw/**/*.md` (PDFs excluded; each has a "
             f"counted markdown counterpart).*")
    L.append("")
    L.append(f"**Total markdown documents in `raw/`: {total}**")
    L.append("")

    # 1. By year
    L.append("## 1. Documents by publication year")
    L.append("")
    L.append("| Year | Documents |")
    L.append("|------|----------:|")
    for year in sorted(by_year):
        L.append(f"| {year} | {by_year[year]} |")
    L.append(f"| **Total** | **{sum(by_year.values())}** |")
    if no_date:
        L.append("")
        L.append(f"*{no_date} document(s) had no parseable `published` date and are "
                 f"excluded from the year/month tables.*")
    L.append("")

    # 2. 2026 by month
    L.append("## 2. 2026 documents by month")
    L.append("")
    L.append("*This is **capture intensity, not publication activity**. It counts what the "
             "wiki holds, by the month each document was published — so it moves with when "
             "the sweeps ran, which countries were being initialised, and how many nights "
             "the rotation completed. A month with more documents is a month the wiki "
             "collected more, not a month in which more happened. It must never be quoted "
             "as a measure of policy, deal or publication activity in Africa.*")
    L.append("")
    months = {"01": "January", "02": "February", "03": "March", "04": "April",
              "05": "May", "06": "June", "07": "July", "08": "August",
              "09": "September", "10": "October", "11": "November", "12": "December"}
    L.append("| Month | Documents |")
    L.append("|-------|----------:|")
    for mm in sorted(by_2026_month):
        L.append(f"| {mm} {months.get(mm, '')} | {by_2026_month[mm]} |")
    L.append(f"| **Total** | **{sum(by_2026_month.values())}** |")
    L.append("")

    # 3. By country
    countries = {c: n for c, n in by_place.items() if not is_region.get(c, False)}
    regions = {c: n for c, n in by_place.items() if is_region.get(c, False)}
    L.append("## 3. Documents by country")
    L.append("")
    L.append("*A document tagged with several places is counted under each, so this "
             "column sums to more than the document total. Region/bloc codes are "
             "listed separately below.*")
    L.append("")
    L.append("| Country | Code | Documents |")
    L.append("|---------|------|----------:|")
    for code, n in sorted(countries.items(), key=lambda kv: (-kv[1], kv[0])):
        L.append(f"| {name_by_code.get(code, '?')} | {code} | {n} |")
    L.append("")
    if regions:
        L.append("### Regional / bloc tags")
        L.append("")
        L.append("| Region | Code | Documents |")
        L.append("|--------|------|----------:|")
        for code, n in sorted(regions.items(), key=lambda kv: (-kv[1], kv[0])):
            L.append(f"| {name_by_code.get(code, '?')} | {code} | {n} |")
        L.append("")
    unknown = {c: n for c, n in by_place.items() if c not in name_by_code}
    if unknown:
        L.append("### Unmapped place codes (not in countries.csv)")
        L.append("")
        L.append("| Code | Documents |")
        L.append("|------|----------:|")
        for code, n in sorted(unknown.items(), key=lambda kv: (-kv[1], kv[0])):
            L.append(f"| {code} | {n} |")
        L.append("")
    if no_place:
        L.append(f"*{no_place} document(s) carry no `places` tag.*")
        L.append("")

    report = "\n".join(L)
    if out_path:
        full = out_path if os.path.isabs(out_path) else os.path.join(ROOT, out_path)
        # newline="\n" pins the EOL. Text mode on Windows translates to CRLF, so
        # the report flipped LF -> CRLF the first time it was regenerated here and
        # showed all 121 lines as changed for a two-line edit. A derived file wants
        # a diff you can read.
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(report + "\n")
        print(f"Wrote {full}")
    else:
        print(report)


if __name__ == "__main__":
    main()
