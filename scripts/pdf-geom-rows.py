#!/usr/bin/env python
"""Dump a PDF's pages as geometry-bound rows: characters grouped by baseline, columns split by x-gap.

The generic form of the binding that `caf-simba-extract.py`, `cmr-plf-extract.py` and
`gha-appropriation-extract.py` each re-implement, and the answer to the drift trap that
`pdftotext -layout` produces on any table whose label, code and amount columns are laid
out as independent vertical text stacks (strategy library, archetypes M/Q and the COG
gazette variant): the text stream interleaves them, the geometry does not.

Reads `page.chars`, never `extract_words()` -- word-level extraction silently drops
glyphs on some producers (COG gazette: the last digit of every amount).

    python scripts/pdf-geom-rows.py DOC.pdf --pages 3-9
    python scripts/pdf-geom-rows.py DOC.pdf --pages 1 --tol 2.0 --gap 4 --sep " | "

Prints one line per visual row, cells separated by --sep. Parses nothing: read the
figures and cross-foot them yourself.
"""
import argparse
import sys

import pdfplumber


def parse_pages(spec, npages):
    if not spec:
        return list(range(npages))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return [p for p in out if 0 <= p < npages]


def rows_from_page(page, tol, gap, rotated=False):
    """Group chars into visual rows, then split each row into cells by the in-line gap.

    `rotated=True` reads a 90/270-rotated table (pdfplumber `upright: False`): the
    line axis is `x0` and text runs bottom-to-top, so rows group on x and cells
    split on a gap in descending `top`. A rotated page is native text in a rotated
    CTM -- never send it to OCR.
    """
    axis = (lambda c: c["x0"]) if rotated else (lambda c: c["top"])
    lines = {}
    for ch in page.chars:
        lines.setdefault(round(axis(ch) / tol), []).append(ch)
    for key in sorted(lines):
        if rotated:
            chars = sorted(lines[key], key=lambda c: -c["top"])
            start, end = (lambda c: -c["bottom"]), (lambda c: -c["top"])
        else:
            chars = sorted(lines[key], key=lambda c: c["x0"])
            start, end = (lambda c: c["x0"]), (lambda c: c["x1"])
        cells, cur, prev = [], "", None
        for ch in chars:
            if prev is not None and start(ch) - prev > gap:
                cells.append(cur.strip())
                cur = ""
            cur += ch["text"]
            prev = end(ch)
        if cur.strip():
            cells.append(cur.strip())
        cells = [c for c in cells if c]
        if cells:
            yield round(min(axis(c) for c in chars), 1), cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="1-based, e.g. 3-9 or 1,4,7 (default: all)")
    ap.add_argument("--tol", type=float, default=2.5, help="row grouping tolerance (pt)")
    ap.add_argument("--gap", type=float, default=4.0, help="column split gap (pt)")
    ap.add_argument("--sep", default=" | ")
    ap.add_argument("--top", action="store_true", help="prefix each row with its y position")
    ap.add_argument("--rot", action="store_true",
                    help="page is rotated 90/270 (pdfplumber upright: False) -- read along x")
    args = ap.parse_args()

    with pdfplumber.open(args.pdf) as pdf:
        for pno in parse_pages(args.pages, len(pdf.pages)):
            page = pdf.pages[pno]
            print(f"===== page {pno + 1} ({page.width:.0f}x{page.height:.0f}) =====")
            for top, cells in rows_from_page(page, args.tol, args.gap, args.rot):
                prefix = f"{top:7.1f}  " if args.top else ""
                print(prefix + args.sep.join(cells))


if __name__ == "__main__":
    sys.exit(main())
