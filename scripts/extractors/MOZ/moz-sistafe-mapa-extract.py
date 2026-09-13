#!/usr/bin/env python
"""Extract a Mozambican SISTAFE PESOE *mapa* (organic classification) to CSV.

Mapas E/F/G (despesas para funcionamento) render one logical row as **three
baselines about half a point apart**, with a wrapped description **vertically
centred** on the code's baseline -- so its first line sits ABOVE the code and its
continuation BELOW. Neither `pdftotext -layout` nor plain baseline grouping
recovers that: the money attaches to the wrong institution, quietly.

The binding that works: anchor on the organic code (`52A000141`, x0 < 65), assign
every right-aligned amount to the nearest code baseline by its **right edge**, and
assign every description word to the nearest code baseline. Then cross-foot: the
eleven component columns must sum to the printed `Total` on every row, and the rows
must sum to the mapa's own printed total.

Mapas H/I/J (investimento) are single-baseline and parse with the same anchor.

    python scripts/extractors/MOZ/moz-sistafe-mapa-extract.py MAPA.pdf -o out.csv
"""
import argparse
import csv
import re
import sys

import pdfplumber

CODE_RE = re.compile(r"^\d{2}[A-Z]\d{6}$")
AMT_RE = re.compile(r"^-?[\d.]+,\d{2}$")


def to_float(s):
    return float(s.replace(".", "").replace(",", "."))


def columns_from(page_words, tol=3.0):
    """Right edges of the amount columns, clustered from every amount on the page."""
    edges = sorted(w["x1"] for w in page_words if AMT_RE.match(w["text"]))
    cols, cur = [], []
    for e in edges:
        if cur and e - cur[-1] > tol:
            cols.append(sum(cur) / len(cur))
            cur = []
        cur.append(e)
    if cur:
        cols.append(sum(cur) / len(cur))
    return cols


def extract(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            words = page.extract_words()
            cols = columns_from(words)
            anchors = sorted(
                (w["top"], w["text"]) for w in words if w["x0"] < 65 and CODE_RE.match(w["text"])
            )
            if not anchors:
                continue
            tops = [a[0] for a in anchors]

            def nearest(top, limit):
                best = min(range(len(tops)), key=lambda i: abs(tops[i] - top))
                return best if abs(tops[best] - top) <= limit else None

            desc = [[] for _ in anchors]
            amts = [{} for _ in anchors]
            for w in words:
                if 65 <= w["x0"] < 200 and not AMT_RE.match(w["text"]):
                    i = nearest(w["top"], 12)
                    if i is not None:
                        desc[i].append((w["top"], w["x0"], w["text"]))
                elif AMT_RE.match(w["text"]):
                    i = nearest(w["top"], 3)
                    if i is None:
                        continue
                    ci = min(range(len(cols)), key=lambda c: abs(cols[c] - w["x1"]))
                    if abs(cols[ci] - w["x1"]) <= 3:
                        amts[i][ci] = to_float(w["text"])
            for i, (top, code) in enumerate(anchors):
                label = " ".join(t for _, _, t in sorted(desc[i]))
                vals = [amts[i].get(c) for c in range(len(cols))]
                rows.append({"code": code, "description": label, "values": vals, "ncols": len(cols)})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out")
    ap.add_argument("--check", action="store_true", help="only report the cross-foot")
    args = ap.parse_args()

    rows = extract(args.pdf)
    ncols = max(r["ncols"] for r in rows)
    bad = 0
    for r in rows:
        v = [x for x in r["values"] if x is not None]
        if len(v) < 2:
            bad += 1
            continue
        total = r["values"][-1]
        parts = [x for x in r["values"][:-1] if x is not None]
        if total is None or abs(sum(parts) - total) > 0.02:
            bad += 1
            print(f"CROSS-FOOT FAIL {r['code']} {r['description'][:40]}: "
                  f"sum {sum(parts):,.2f} vs total {total}", file=sys.stderr)
    print(f"{len(rows)} rows, {ncols} amount columns, {bad} cross-foot failures", file=sys.stderr)
    grand = sum(r["values"][-1] for r in rows if r["values"][-1] is not None)
    print(f"sum of row totals = {grand:,.2f}", file=sys.stderr)

    if args.out and not args.check:
        with open(args.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["code", "description"] + [f"c{i + 1}" for i in range(ncols)])
            for r in rows:
                w.writerow([r["code"], r["description"]] +
                           ["" if x is None else f"{x:.2f}" for x in r["values"]])


if __name__ == "__main__":
    sys.exit(main())
