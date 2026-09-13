# -*- coding: utf-8 -*-
"""Append the BEN 2026-07-25 budget-extract records to the domestic finance run log."""
import csv, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

rows = []
for fn in sorted(os.listdir("new")):
    if not fn.endswith(".md"):
        continue
    path = os.path.join("new", fn)
    text = open(path, encoding="utf-8").read()
    m = re.search(r"^deal_id: (.+)$", text, re.M)
    if not m or not m.group(1).startswith("ben-"):
        continue

    def g(key, default=""):
        mm = re.search(r"^" + key + r": (.*)$", text, re.M)
        return mm.group(1).strip().strip('"') if mm else default

    loc = re.search(r"\| doc_locator \| (.+?) \|", text)
    warnings = []
    if "Figure disputed" in text:
        warnings.append("API figure disputed; open contradiction brief")
    if g("budget_stage") == "actual":
        warnings.append("four-month execution point (01/01-30/04/2026), not a full-year outturn")
    if g("scope_confidence") != "whole":
        warnings.append("partial scope - reported separately from the headline total")
    if "Excluded as external" in text and "XOF 0 " not in text:
        pass
    rows.append([
        m.group(1),
        path.replace(os.sep, "/"),
        "BEN",
        g("state_level"),
        g("fiscal_year_label"),
        g("budget_stage"),
        g("budget_version"),
        g("finance_origin"),
        "domestic-revenue",
        g("scope_confidence"),
        g("is_transfer"),
        g("amount_total"),
        g("currency"),
        loc.group(1) if loc else "",
        "",
        "; ".join(warnings),
    ])

with open("documentation/domestic-finance-run-log.csv", "a", newline="", encoding="utf-8") as f:
    csv.writer(f).writerows(rows)
print("appended", len(rows), "run-log rows")
