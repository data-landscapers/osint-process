#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Extract Cameroon PLF programme tables by page geometry.

The Cameroonian *projet de loi de finances* carries the whole appropriation as one
table: CHAPITRE (FY2024-25) or SECTION (FY2026) -> programme, with
`N° CODE | LIBELLE | OBJECTIF | INDICATEUR | AE | CP`, scale `Milliers FCFA`.

Two properties force a geometry parse rather than `pdftotext -layout`:

1. **Thousands are separated by a space**, so `18 611 000` arrives as three separate
   words. Numeric tokens must be re-joined by x-gap before they mean anything.
2. **The code column is stacked.** Where a vote has several programmes, the printed
   table puts three codes together above three amounts, and `-layout` interleaves them
   unpredictably. Rows must be bound by `top`, as archetype M's SIM_ba variant requires.

Usage:  python scripts/cmr-plf-extract.py <pdf> <out.csv> [--unit CHAPITRE|SECTION]
"""
import sys, csv, re, io
import pdfplumber

DIGITS = re.compile(r"^\d+$")


def norm(s):
    return re.sub(r"[\s  ]+", " ", s or "").strip()


def rows_of(page, tol=2.5):
    """Group words into visual rows keyed on `top`."""
    buckets = {}
    for w in page.extract_words(use_text_flow=False, keep_blank_chars=False):
        buckets.setdefault(round(w["top"] / tol), []).append(w)
    for k in sorted(buckets):
        yield sorted(buckets[k], key=lambda w: w["x0"])


def join_numbers(words, max_gap=7.0):
    """Re-join space-separated digit groups into whole numbers.

    Returns [(value, x0, x1), ...] left to right. A gap wider than `max_gap`
    starts a new number, which is what separates the AE column from the CP column.
    """
    out, cur = [], []
    for w in words:
        if not DIGITS.match(w["text"]):
            if cur:
                out.append(cur); cur = []
            continue
        if cur and (w["x0"] - cur[-1]["x1"]) > max_gap:
            out.append(cur); cur = []
        cur.append(w)
    if cur:
        out.append(cur)
    res = []
    for grp in out:
        val = "".join(g["text"] for g in grp)
        if val.isdigit():
            res.append((int(val), grp[0]["x0"], grp[-1]["x1"]))
    return res


def extract(pdf_path, unit_word):
    recs = []
    vote = vote_label = None
    pat = re.compile(r"^%s\s*(\d{2})\s*-?\s*(.*)$" % unit_word)
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            W = page.width
            money_x = W * 0.60          # amounts live right of this
            label_lo, label_hi = W * 0.13, W * 0.46
            for words in rows_of(page):
                left = [w for w in words if w["x1"] <= money_x]
                right = [w for w in words if w["x0"] > money_x]
                text = norm(" ".join(w["text"] for w in left))
                amounts = join_numbers(right)

                m = pat.match(text)
                if m:
                    vote = m.group(1)
                    lbl = norm(m.group(2))
                    vote_label = lbl or vote_label
                    recs.append(dict(page=pno, vote=vote, vote_label=vote_label, kind="vote-total",
                                     internal="", code="", label=vote_label or "",
                                     ae=amounts[0][0] if amounts else "",
                                     cp=amounts[-1][0] if len(amounts) > 1 else
                                        (amounts[0][0] if amounts else "")))
                    continue

                if vote is None or not amounts:
                    continue
                # a programme amount is >= 4 digits; ignore page numbers and indicator numerals
                amounts = [a for a in amounts if a[0] >= 1000]
                if not amounts:
                    continue
                codes = [w["text"] for w in words
                         if w["x1"] < label_lo and DIGITS.match(w["text"]) and len(w["text"]) <= 3]
                label = norm(" ".join(w["text"] for w in words
                                      if label_lo <= w["x0"] < label_hi))
                recs.append(dict(page=pno, vote=vote, vote_label=vote_label, kind="programme",
                                 internal=codes[0] if len(codes) > 1 else "",
                                 code=codes[-1] if codes else "",
                                 label=label,
                                 ae=amounts[0][0],
                                 cp=amounts[-1][0] if len(amounts) > 1 else amounts[0][0]))
    return recs


def main():
    pdf, out = sys.argv[1], sys.argv[2]
    unit = "CHAPITRE"
    if "--unit" in sys.argv:
        unit = sys.argv[sys.argv.index("--unit") + 1]
    recs = extract(pdf, unit)
    with io.open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["page", "vote", "vote_label", "kind",
                                          "internal", "code", "label", "ae", "cp"],
                           lineterminator="\n")
        w.writeheader()
        for r in recs:
            w.writerow(r)
    votes = {r["vote"] for r in recs}
    print("%s: %d rows, %d votes" % (out, len(recs), len(votes)))


if __name__ == "__main__":
    main()
