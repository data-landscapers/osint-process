#!/usr/bin/env python3
"""citations-merge.py — merge new citation rows into X:\\citations.csv, newest first.

SWEEP-CITATIONS.md. The sweep writes its verified finds to a CSV with the same four columns
(Date,Title,Author,u.r.l); this script folds them into the register, deduplicates on the URL
(trimmed, trailing slash and scheme ignored), drops blank rows, and sorts by Date descending.
A month-only date ("2026-10") sorts after that month's dated rows. The header and the UTF-8 BOM
are kept as the register has them. Prints `citations: +N new, M total`.

usage: python scripts/citations-merge.py <new-rows.csv> [--register X:/citations.csv] [--dry-run]
"""
import argparse
import csv
import io
import sys

HEADER = ["Date", "Title", "Author", "u.r.l"]


def key(url):
    u = url.strip().lower()
    for p in ("https://", "http://"):
        if u.startswith(p):
            u = u[len(p):]
    if u.startswith("www."):
        u = u[4:]
    return u.rstrip("/")


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if rows and [c.strip() for c in rows[0]] == HEADER:
        header, rows = rows[0], rows[1:]
    else:
        header = HEADER
    out = []
    for r in rows:
        r = (r + ["", "", "", ""])[:4]
        r = [c.strip() for c in r]
        if any(r) and r[3]:
            out.append(r)
    return header, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("--register", default="X:/citations.csv")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    header, held = read(a.register)
    _, new = read(a.new)
    seen = {key(r[3]) for r in held}
    added = 0
    for r in new:
        k = key(r[3])
        if k not in seen:
            seen.add(k)
            held.append(r)
            added += 1
    held.sort(key=lambda r: r[0], reverse=True)

    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(held)
    if not a.dry_run:
        with open(a.register, "w", encoding="utf-8-sig", newline="") as f:
            f.write(buf.getvalue())
    print(f"citations: +{added} new, {len(held)} total" + (" (dry run)" if a.dry_run else ""))


if __name__ == "__main__":
    sys.exit(main())
