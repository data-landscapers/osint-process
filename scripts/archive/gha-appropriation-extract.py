#!/usr/bin/env python3
"""Extract Ghana's Appropriation Act Fourth Schedule to CSV.

The Fourth Schedule -- *Summary of Expenditure by Programme, Economic Item and
Funding* -- is the whole state at programme grain with the funding origin
printed on every line (GoG / IGF / Funds-Others / Donors), which is what the
domestic-state driver's origin gate wants and what no Ghanaian narrative
document supplies. The Third Schedule is the same table at MDA grain and is
read here too, because MDA totals are the cross-foot for the programme rows.

The text stream is unusable: `pdftotext -layout` drifts figures several rows
away from their labels, and a wrapped programme label puts its own figures on
the *following* visual row. Bind by page geometry instead -- group `page.chars`
by `top`, join tokens by x-gap, and assign each amount to a column by its
RIGHT edge (the columns are right-aligned, so a left-edge parse drifts with
magnitude).

Usage
  python scripts/gha-appropriation-extract.py ACT.pdf -o out.csv
  python scripts/gha-appropriation-extract.py ACT.pdf --schedule third -o out.csv
"""

import argparse
import csv
import re
import sys

import pdfplumber

# Right edges of the fifteen money columns, measured off the FY2026 Act
# (Act 1163) and stable across its eight schedule pages. Verified by
# cross-footing every MDA: GoG comp+goods+capex = GoG total, likewise IGF and
# Donors, and the three totals + Funds/Others = Grand Total.
COLUMNS = [
    ("gog_compensation", 170.8),
    ("gog_goods_services", 222.1),
    ("gog_capex", 270.2),
    ("gog_total", 321.5),
    ("igf_compensation", 366.4),
    ("igf_goods_services", 414.5),
    ("igf_capex", 459.4),
    ("igf_total", 507.5),
    ("statutory", 555.6),
    ("abfa", 600.5),
    ("others", 645.4),
    ("donors_goods_services", 684.7),
    ("donors_capex", 729.6),
    ("donors_total", 777.7),
    ("grand_total", 829.0),
]
COL_TOL = 6.0

MONEY = re.compile(r"^[\d,]+$")
MDA = re.compile(r"^(\d{3})\s*-\s*(.+)$")
PROGRAMME = re.compile(r"^(\d{5})\s*-\s*(.+)$")
SECTOR = re.compile(r"^(\d{2})\s*-\s*(.+)$")


def row_tokens(chars, gap=1.2):
    """Chars of one visual row -> [(text, x0, x1)], joined on x-gap."""
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


def visual_rows(page, tol=2.5):
    rows = {}
    for c in page.chars:
        rows.setdefault(round(c["top"] / tol), []).append(c)
    return [(min(c["top"] for c in cs), row_tokens(cs)) for _, cs in sorted(rows.items())]


def amounts(tokens):
    """Map money tokens to columns by right edge. Returns {} if none."""
    got = {}
    for text, _x0, x1 in tokens:
        if not MONEY.match(text) or len(text) < 3:
            continue
        best, dist = None, COL_TOL
        for name, edge in COLUMNS:
            d = abs(x1 - edge)
            if d < dist:
                best, dist = name, d
        if best:
            got[best] = int(text.replace(",", ""))
    return got


def crossfoot(row):
    """The table's own arithmetic. Returns a list of failures.

    The Act rounds to the cedi, so a one-cedi residual is the document's own
    and not a misread; anything larger is an extraction failure.
    """
    bad = []
    for block in ("gog", "igf", "donors"):
        parts = [row.get(f"{block}_{k}") or 0
                 for k in ("compensation", "goods_services", "capex")]
        total = row.get(f"{block}_total")
        if total and abs(sum(parts) - total) > 1:
            bad.append(f"{block}: {'+'.join(str(p) for p in parts)} != {total}")
    blocks = sum(row.get(f"{b}_total") or 0 for b in ("gog", "igf", "donors"))
    blocks += sum(row.get(k) or 0 for k in ("statutory", "abfa", "others"))
    grand = row.get("grand_total")
    if grand and abs(blocks - grand) > 1:
        bad.append(f"grand: {blocks} != {grand}")
    return bad


def extract(path, schedule="fourth"):
    want = "Summary of Expenditure by Programme" if schedule == "fourth" else \
           "Summary of Expenditure by Ministries"
    out = []
    with pdfplumber.open(path) as pdf:
        for pi, page in enumerate(pdf.pages, 1):
            head = page.extract_text() or ""
            if want not in head:
                continue
            rows = visual_rows(page)
            sector = mda = None
            pending = None          # a label whose figures are on the next row
            for top, tokens in rows:
                if top < 110:       # header block
                    continue
                label = tokens[0][0] if tokens else ""
                money = amounts(tokens)
                m_prog, m_mda, m_sec = (PROGRAMME.match(label), MDA.match(label),
                                        SECTOR.match(label))
                if m_prog or m_mda or m_sec:
                    if pending and not money:
                        out.append(pending)     # previous label never got figures
                    kind = "programme" if m_prog else ("mda" if m_mda else "sector")
                    m = m_prog or m_mda or m_sec
                    if kind == "mda":
                        mda = (m.group(1), m.group(2).strip())
                    if kind == "sector":
                        sector = (m.group(1), m.group(2).strip())
                    rec = {
                        "page": pi, "level": kind,
                        "sector_code": sector[0] if sector else "",
                        "sector": sector[1] if sector else "",
                        "mda_code": mda[0] if mda else "",
                        "mda": mda[1] if mda else "",
                        "code": m.group(1), "label": m.group(2).strip(),
                    }
                    rec.update({k: money.get(k) for k, _ in COLUMNS})
                    if money:
                        out.append(rec)
                        pending = None
                    else:
                        pending = rec           # wrapped label; figures follow
                elif pending is not None and money:
                    pending.update({k: money.get(k) for k, _ in COLUMNS})
                    out.append(pending)
                    pending = None
                elif pending is not None and label and not money:
                    pending["label"] += " " + label     # label continuation
            if pending:
                out.append(pending)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--schedule", choices=["third", "fourth"], default="fourth")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    rows = extract(args.pdf, args.schedule)
    fields = ["page", "level", "sector_code", "sector", "mda_code", "mda",
              "code", "label"] + [k for k, _ in COLUMNS] + ["crossfoot"]
    fails = 0
    for r in rows:
        bad = crossfoot(r)
        r["crossfoot"] = "; ".join(bad) if bad else "ok"
        fails += bool(bad)

    stream = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.DictWriter(stream, fieldnames=fields)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in fields})
    if args.out:
        stream.close()
    print(f"{len(rows)} rows, {fails} failing cross-foot", file=sys.stderr)


if __name__ == "__main__":
    main()
