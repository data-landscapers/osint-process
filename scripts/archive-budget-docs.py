#!/usr/bin/env python3
"""archive-budget-docs.py — BUDGET-EXTRACT.md steps 5a and 6, for any country.

Four copies of this script existed — `archive-ben-budget-docs.py`,
`-bwa-`, `-caf-`, `-cmr-` — and they differed in three things: the ISO-3 code, the
date, and a table of `artefact stem -> (extracted_scope, re_extract)`. Everything
else was the same forty lines: set the four manifest columns, move the artefact
and its companion into `budget-archive/{ISO3}/{FY}/`, then delete the emptied
`new-budget/` folders. At four scripts a country and forty countries left to
initialise, that arithmetic is the whole of review task 25.

The per-country part is not configuration in any reusable sense — it is a
**finding of that extraction run** ("read at sector-vote; the revised columns
cover chapitre 45 only"). So it stays data, written by the pass as a small CSV,
and this script is the logic:

    stem,extracted_scope,re_extract
    2024-02-05-bwa-estimates-of-expenditure-...,cross-vote,no
    2023-11-30-cmr-projet-de-loi-de-finances-2024,sector-vote,revised columns read for chapitre 45 only

`stem` matches by **substring against the artefact's filename**, so a fragment is
enough — that is how the retired scripts keyed it, and it survives a rename that
keeps the distinctive middle.

**The move is the last step, per BUDGET-EXTRACT.md §6**: an interrupted run
resumes on exactly the documents not yet processed. Nothing here is destructive
to the record — manifest rows are never deleted, only completed.

Usage:
  python scripts/archive-budget-docs.py --country CMR --scope scope.csv          # dry run
  python scripts/archive-budget-docs.py --country CMR --scope scope.csv --apply
  python scripts/archive-budget-docs.py --country CMR --verify                   # what is already recorded

  --date YYYY-MM-DD   the `extracted` stamp (default: today)
  --keep-folders      do not remove the emptied new-budget/{ISO3}/{FY}/ folders

Exit 1 if any document in scope has no row in the scope file — that is a document
the pass did not account for, which is the one thing this script must not let
through silently.
"""
import argparse
import csv
import os
import shutil
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finance_lib as F                                              # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST = os.path.join(F.ROOT, "new-budget", "manifest.csv")
COLUMNS = ("extracted", "extracted_scope", "re_extract", "archive_path")
SCOPES = ("sector-vote", "cross-vote", "narrative", "n/a")


def load_scope(path):
    """{stem fragment: (extracted_scope, re_extract)} from the pass's own CSV."""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            stem = (row.get("stem") or "").strip()
            if not stem:
                continue
            scope = (row.get("extracted_scope") or "").strip()
            if scope not in SCOPES:
                sys.exit(f"{path}: extracted_scope `{scope}` for {stem} is not one of {SCOPES}")
            out[stem] = (scope, (row.get("re_extract") or "no").strip() or "no")
    if not out:
        sys.exit(f"{path}: no rows")
    return out


def match(stem_table, path):
    """The scope row whose stem fragment appears in this artefact's filename."""
    name = os.path.basename(path or "")
    hits = [k for k in stem_table if k and k in name]
    if not hits:
        return None
    return stem_table[max(hits, key=len)]        # longest fragment wins


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--country", required=True, help="ISO-3, as in the manifest")
    ap.add_argument("--scope", help="CSV: stem,extracted_scope,re_extract")
    ap.add_argument("--apply", action="store_true", help="write; without this it is a dry run")
    ap.add_argument("--date", default=str(date.today()), help="the `extracted` stamp")
    ap.add_argument("--keep-folders", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="report what the manifest already records for this country")
    ap.add_argument("--root", default=F.ROOT,
                    help="repo root — only for testing this script against a fixture")
    a = ap.parse_args()
    iso = a.country.upper()
    root = a.root
    manifest = os.path.join(root, "new-budget", "manifest.csv")

    with open(manifest, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        fields, rows = reader.fieldnames, list(reader)
    mine = [r for r in rows if (r.get("iso3") or "").upper() == iso]
    if not mine:
        sys.exit(f"no manifest rows for {iso}")

    if a.verify:
        done = [r for r in mine if r.get("extracted")]
        print(f"{iso}: {len(mine)} documents, {len(done)} archived")
        for r in mine:
            print(f"  {r.get('extracted') or '(open)':<12} {r.get('extracted_scope') or '':<12} "
                  f"{os.path.basename(r.get('artefact_path') or '?')}")
            if r.get("re_extract") and r["re_extract"] != "no":
                print(f"               re_extract: {r['re_extract'][:90]}")
        return 0
    if not a.scope:
        ap.error("--scope is required unless --verify")

    table = load_scope(a.scope)
    todo = [r for r in mine if not r.get("extracted")]
    if not todo:
        print(f"{iso}: nothing open — every document already carries `extracted`. "
              f"--verify to see them.")
        return 0

    unknown, moves = [], []
    for r in todo:
        hit = match(table, r.get("artefact_path") or r.get("companion_path"))
        if not hit:
            unknown.append(r.get("artefact_path") or "(no artefact_path)")
            continue
        scope, reex = hit
        fy = r.get("fiscal_year") or ""
        dest = f"budget-archive/{iso}/{fy}"
        art = r.get("artefact_path") or ""
        r[COLUMNS[0]] = a.date
        r[COLUMNS[1]] = scope
        r[COLUMNS[2]] = reex
        r[COLUMNS[3]] = f"{dest}/{os.path.basename(art)}" if art else ""
        for src in (art, r.get("companion_path")):
            if src:
                moves.append((src, f"{dest}/{os.path.basename(src)}"))

    print(f"{iso}: {len(todo)} open document(s), {len(moves)} file(s) to move "
          f"({'APPLY' if a.apply else 'dry run'})")
    for src, dst in moves:
        state = "" if os.path.exists(os.path.join(root, src)) else "  [missing on disk]"
        print(f"  {src}\n    -> {dst}{state}")
    if unknown:
        print("\nNO SCOPE ROW — every open document needs one (step 5a):")
        for u in unknown:
            print("  " + u)
        return 1

    if not a.apply:
        print("\ndry run — nothing written. Re-run with --apply.")
        return 0

    for src, dst in moves:
        s, d = os.path.join(root, src), os.path.join(root, dst)
        if os.path.exists(s):
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.move(s, d)
    with open(manifest, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"manifest updated: {len(todo)} row(s)")

    if not a.keep_folders:
        base = os.path.join(root, "new-budget", iso)
        for fy in sorted(os.listdir(base)) if os.path.isdir(base) else []:
            d = os.path.join(base, fy)
            if os.path.isdir(d) and not os.listdir(d):
                os.rmdir(d)
                print(f"removed new-budget/{iso}/{fy}")
            elif os.path.isdir(d):
                print(f"STILL POPULATED new-budget/{iso}/{fy}: {os.listdir(d)}")
        if os.path.isdir(base) and not os.listdir(base):
            os.rmdir(base)
            print(f"removed new-budget/{iso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
