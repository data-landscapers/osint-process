#!/usr/bin/env python3
"""Extract rows from a Central African Republic SIM_ba budget volume (PLF charges).

Archetype M, solved by page geometry (see documentation/budget-extraction-strategies.md).
`pdftotext -layout` interleaves the three left-hand columns unpredictably; word
bounding boxes do not.

Column model (PLF 2025 and PLF 2026 alike, A4 landscape):

    x~35   Fonction (4-digit functional code)
    x~60   Imputation (chart-of-accounts key)
    x~79   free-text programme / activite LABEL column
    x~177  Intitule (economic-nature wording)
    x>=430 the amount columns, right-aligned:
             prev-year Collectif | Financement interieur | Dons | Emprunt |
             Credit <FY> | Variation valeur | Variation %

The binding rule: a label at x~79 belongs to the imputation row immediately BELOW it.

Usage:
    python scripts/caf-simba-extract.py DOC.pdf --first 506 --last 515 -o out.csv
    python scripts/caf-simba-extract.py DOC.pdf --scan            # cross-vote keyword scan
"""
import argparse
import csv
import re
import sys

import pdfplumber

# right-edge centres of the seven amount columns, measured on both volumes
AMOUNT_COLS = [
    ("prev", 470, 500),
    ("fin_int", 528, 558),
    ("dons", 578, 608),
    ("emprunt", 628, 660),
    ("credit", 698, 728),
    ("var_val", 748, 778),
    ("var_pct", 800, 830),
]

NUM_RE = re.compile(r"^-?[\d  ]*\d$")


def group_rows(words, tol=2.5):
    rows = []
    for w in sorted(words, key=lambda w: (w["top"], w["x0"])):
        if rows and abs(w["top"] - rows[-1][0]) <= tol:
            rows[-1][1].append(w)
        else:
            rows.append([w["top"], [w]])
    return [(t, sorted(ws, key=lambda w: w["x0"])) for t, ws in rows]


def join_numbers(tokens):
    """Merge adjacent digit-group tokens (French thousands separator is a space)."""
    out = []
    for w in tokens:
        txt = w["text"]
        if not re.fullmatch(r"-?\d{1,3}", txt) and not re.fullmatch(r"\d{1,3}", txt):
            out.append({"text": txt, "x0": w["x0"], "x1": w["x1"], "num": False})
            continue
        if out and out[-1]["num"] and (w["x0"] - out[-1]["x1"]) < 6:
            out[-1]["text"] += txt
            out[-1]["x1"] = w["x1"]
        else:
            out.append({"text": txt, "x0": w["x0"], "x1": w["x1"], "num": True})
    return out


def parse_row(top, ws):
    fonction = "".join(w["text"] for w in ws if 28 <= w["x0"] < 55)
    imput = " ".join(w["text"] for w in ws if 55 <= w["x0"] < 76).strip()
    label = " ".join(w["text"] for w in ws if 76 <= w["x0"] < 172).strip()
    intitule = " ".join(w["text"] for w in ws if 172 <= w["x0"] < 425).strip()
    amounts = {k: "" for k, _, _ in AMOUNT_COLS}
    toks = join_numbers([w for w in ws if w["x0"] >= 425])
    for t in toks:
        if not t["num"]:
            continue
        for name, lo, hi in AMOUNT_COLS:
            if lo <= t["x1"] <= hi:
                amounts[name] = t["text"]
                break
    return {
        "top": round(top, 1),
        "fonction": fonction,
        "imputation": imput,
        "label": label,
        "intitule": intitule,
        **amounts,
    }


def extract(path, first, last):
    out = []
    with pdfplumber.open(path) as pdf:
        for pno in range(first, last + 1):
            pg = pdf.pages[pno - 1]
            words = pg.extract_words(use_text_flow=False, keep_blank_chars=False)
            rows = [parse_row(t, ws) for t, ws in group_rows(words)]
            # drop running head / footer
            rows = [
                r
                for r in rows
                if not r["label"].startswith("Edit")
                and "SIM_ba" not in r["intitule"]
                and r["intitule"] != "Imputation"
            ]
            # bind a free-standing label to the imputation row below it
            pending = []
            for r in rows:
                if r["imputation"] and pending:
                    r["bound_label"] = " / ".join(pending)
                    pending = []
                elif (
                    r["label"]
                    and not r["imputation"]
                    and not r["label"].startswith("TITRE")
                    and not re.match(r"^\d\d ", r["label"])
                ):
                    pending.append(r["label"])
                    continue
                else:
                    r["bound_label"] = ""
                r["page"] = pno
                out.append(r)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--first", type=int, required=True)
    ap.add_argument("--last", type=int, required=True)
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    rows = extract(a.pdf, a.first, a.last)
    cols = [
        "page",
        "fonction",
        "imputation",
        "bound_label",
        "label",
        "intitule",
    ] + [k for k, _, _ in AMOUNT_COLS]
    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"{len(rows)} rows -> {a.out}")
    else:
        for r in rows:
            print(
                "|".join(
                    str(r.get(c, "")) for c in cols
                )
            )


if __name__ == "__main__":
    main()
