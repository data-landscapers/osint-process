#!/usr/bin/env python3
"""Extract the Central African Republic CDMT sectoriels (BUDGET DETAILLE PAR ACTIVITE).

CAR's budget-programme, published 24-Mar-2026 `a titre experimental` for FY2026 and
therefore carrying no legal force. 183pp, native, A4 landscape.

Layout: `PROGRAMME (5 digits) -> ACTION (7) -> ACTIVITE (19 chars, ...XXXXnn)`, with
AE and CP columns for 2026, 2027 and 2028. Scale is **full francs**, not milliers —
unlike the PLF volume it restates.

Column right edges (measured): AE26 ~427 | CP26 ~506 | AE27 ~583 | CP27 ~662 |
AE28 ~745 | CP28 ~823.

Usage: python scripts/caf-cdmt-extract.py DOC.pdf -o out.csv
"""
import argparse
import csv
import re

import pdfplumber

COLS = [
    ("ae2026", 415, 440),
    ("cp2026", 493, 518),
    ("ae2027", 572, 598),
    ("cp2027", 650, 676),
    ("ae2028", 735, 760),
    ("cp2028", 810, 836),
]

CODE = re.compile(r"^(\d{5}|\d{7}|\d{7}\d{6}[A-Z]{4}\d{2}|\d{2})$")


def join_numbers(tokens):
    out = []
    for w in tokens:
        t = w["text"]
        if re.fullmatch(r"\d{1,3}", t):
            if out and out[-1]["num"] and (w["x0"] - out[-1]["x1"]) < 8:
                out[-1]["text"] += t
                out[-1]["x1"] = w["x1"]
            else:
                out.append({"text": t, "x0": w["x0"], "x1": w["x1"], "num": True})
        else:
            out.append({"text": t, "x0": w["x0"], "x1": w["x1"], "num": False})
    return out


def run(path):
    rows = []
    with pdfplumber.open(path) as pdf:
        for pno, pg in enumerate(pdf.pages, 1):
            buckets = {}
            for w in pg.extract_words(use_text_flow=False, keep_blank_chars=False):
                buckets.setdefault(round(w["top"] / 3), []).append(w)
            for k in sorted(buckets):
                ws = sorted(buckets[k], key=lambda w: w["x0"])
                code = ""
                label_toks = []
                for w in ws:
                    if w["x0"] < 60 and re.fullmatch(r"[\dA-Z]{2,19}", w["text"]):
                        code = w["text"]
                    elif w["x0"] < 380:
                        label_toks.append(w["text"])
                amts = {c: "" for c, _, _ in COLS}
                for t in join_numbers([w for w in ws if w["x0"] >= 380]):
                    if not t["num"]:
                        continue
                    for name, lo, hi in COLS:
                        if lo <= t["x1"] <= hi:
                            amts[name] = t["text"]
                            break
                label = " ".join(label_toks).strip()
                if not code and not label and not any(amts.values()):
                    continue
                if label.startswith("BUDGET DETAILLE") or label.startswith("MINISTERE DES FINANCES"):
                    continue
                lvl = (
                    "activite"
                    if len(code) > 10
                    else "action"
                    if len(code) == 7
                    else "programme"
                    if len(code) == 5
                    else "section"
                    if len(code) == 2
                    else ""
                )
                rows.append({"page": pno, "level": lvl, "code": code, "label": label, **amts})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    rows = run(a.pdf)
    cols = ["page", "level", "code", "label"] + [c for c, _, _ in COLS]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {a.out}")


if __name__ == "__main__":
    main()
