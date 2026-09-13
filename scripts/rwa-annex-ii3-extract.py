#!/usr/bin/env python3
"""Extract Rwanda's ANNEX II-3 (development budget by agency, project and
funding type) to CSV.

ANNEX II-3 is the origin gate for the Rwandan development budget: every
project line carries its split between the agency's own allocation, GoR
counterpart, external loans and external grants. It is a Crystal Reports
rendering, so the rows are geometrically perfect and the *text layer is not* --
`pdftotext -layout` and `pdfplumber.extract_text` both drift a project's
figures onto a neighbouring row, which silently attaches money to the wrong
project (FY2023/24: the text stream reads E-Gates at Frw 8,524,696,694 where
the page prints 2,538,577,501).

So bind by geometry: group `page.chars` by `top`, join tokens on x-gap, and
assign each amount to a column by its RIGHT edge. Then cross-foot -- project
lines must sum to their agency row, agencies to their ministry row.

The funding columns changed shape between editions; the header row is read
per document rather than assumed.

Usage
  python scripts/rwa-annex-ii3-extract.py ANNEX.pdf -o out.csv
"""

import argparse
import csv
import re
import sys
from collections import OrderedDict

import pdfplumber

MONEY = re.compile(r"^-?[\d,]+$")
MINISTRY = re.compile(r"^(\d{2})\s+(.+)$")
AGENCY = re.compile(r"^(\d{4})\s+(.+)$")
PROJECT = re.compile(r"^([A-Z0-9]{3})\s+(.+)$")

# Right edges measured off the FY2023/24 and FY2024/25 annexes. The stride is
# stable within an edition; a column absent from an edition simply never
# matches.
COLUMNS = OrderedDict([
    ("agency_allocation", 480.0),
    ("gor_counterpart", 543.6),
    ("external_loan", 612.0),
    ("external_grant", 678.0),
    ("total", 756.0),
])
COL_TOL = 7.0


def row_tokens(chars, gap=1.5):
    chars = sorted(chars, key=lambda c: c["x0"])
    out, cur, x0, x1 = [], "", None, None
    for c in chars:
        if cur and c["x0"] - x1 > gap:
            out.append((cur.strip(), x0, x1))
            cur = ""
        if not cur:
            x0 = c["x0"]
        cur += c["text"]
        x1 = c["x1"]
    if cur:
        out.append((cur.strip(), x0, x1))
    return [t for t in out if t[0]]


def cluster_rows(chars, tol=3.5):
    """Group chars into visual rows by clustering `top`, not by rounding it.

    Where a project label wraps over two or three lines the renderer centres
    the figures on the block and emits them a fraction of a point ABOVE the
    label's first line -- 208.1 against 208.9 on the Ngoma district page. A
    fixed grid puts those in different buckets and the row's money is lost,
    which is how a district block ends up short of its own printed total.
    """
    groups = []
    for c in sorted(chars, key=lambda c: c["top"]):
        if groups and c["top"] - groups[-1][0] <= tol:
            groups[-1][1].append(c)
        else:
            groups.append((c["top"], [c]))
    return [g[1] for g in groups]


def amounts(tokens):
    got = {}
    for text, _x0, x1 in tokens:
        if not MONEY.match(text):
            continue
        best, dist = None, COL_TOL
        for name, edge in COLUMNS.items():
            d = abs(x1 - edge)
            if d < dist:
                best, dist = name, d
        if best:
            got[best] = int(text.replace(",", ""))
    return got


def extract(path):
    out = []
    # An agency block runs across the page break -- NCSA's Frw 945m cyber
    # security building is the first row of the next page -- so the current
    # ministry and agency carry over pages and are NOT reset per page.
    ministry = agency = None
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            for cs in cluster_rows(page.chars):
                top = min(c["top"] for c in cs)
                if top < 165:                       # title and header block
                    continue
                tokens = row_tokens(cs)
                if not tokens:
                    continue
                label, lx0, _ = tokens[0]
                money = amounts(tokens)
                if not money:
                    continue
                # The indent is what says which level a row is: ministry rows
                # start at the left margin, agencies one stop in, projects two.
                if lx0 < 30:
                    m = MINISTRY.match(label)
                    kind, ministry, agency = "ministry", (m.group(1), m.group(2).strip()) if m else ministry, None
                elif lx0 < 55:
                    m = AGENCY.match(label)
                    kind = "agency"
                    if m:
                        agency = (m.group(1), m.group(2).strip())
                else:
                    m = PROJECT.match(label)
                    kind = "project"
                if not m:
                    continue
                rec = {
                    "page": pi, "level": kind,
                    "ministry_code": ministry[0] if ministry else "",
                    "ministry": ministry[1] if ministry else "",
                    "agency_code": agency[0] if agency else "",
                    "agency": agency[1] if agency else "",
                    "code": m.group(1), "label": m.group(2).strip(),
                }
                rec.update({k: money.get(k) for k in COLUMNS})
                out.append(rec)
    return out


def crossfoot(rows):
    """Project lines must sum to their agency row; agencies to their ministry."""
    fails = []
    by_agency, by_ministry = {}, {}
    for r in rows:
        if r["level"] == "project":
            by_agency.setdefault((r["ministry_code"], r["agency_code"]), []).append(r)
        elif r["level"] == "agency":
            by_ministry.setdefault(r["ministry_code"], []).append(r)
    for r in rows:
        if r["level"] == "agency":
            kids = by_agency.get((r["ministry_code"], r["code"]), [])
            if kids:
                s = sum(k["total"] or 0 for k in kids)
                if abs(s - (r["total"] or 0)) > 1:
                    fails.append(f"agency {r['code']} {r['label'][:30]}: {s} != {r['total']}")
        elif r["level"] == "ministry":
            kids = by_ministry.get(r["code"], [])
            if kids:
                s = sum(k["total"] or 0 for k in kids)
                if abs(s - (r["total"] or 0)) > 1:
                    fails.append(f"ministry {r['code']} {r['label'][:30]}: {s} != {r['total']}")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    rows = extract(args.pdf)
    fails = crossfoot(rows)
    fields = (["page", "level", "ministry_code", "ministry", "agency_code",
               "agency", "code", "label"] + list(COLUMNS))
    stream = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.DictWriter(stream, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    if args.out:
        stream.close()

    n = {k: sum(1 for r in rows if r["level"] == k) for k in ("ministry", "agency", "project")}
    print(f"{len(rows)} rows {n}; {len(fails)} cross-foot failures", file=sys.stderr)
    for f in fails[:20]:
        print("  " + f, file=sys.stderr)


if __name__ == "__main__":
    main()
