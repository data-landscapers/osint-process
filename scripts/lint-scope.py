#!/usr/bin/env python3
"""lint-scope.py — does every source in `raw/` clear the place bar?

`CLAUDE.md` -> *The material* and `INGEST.md` step 1 state the bar as **an African
place, or `XGL`, or a `geopol.*` slug — else out**. Until 2026-08-20 the screen had
no geographic clause at all and 26 single-country non-African domestic stories
reached `raw/`; the clause is in now, and this is the instrument that says whether
it is holding. Three-way sort, matching CORPUS's `lint-scope.py`:

  in           an African place, or a `geopol.*` topic          nothing owed
  xgl          `XGL` and nothing else, no `geopol.*`            a reading, not a lint
  unaccounted  none of the above                                a defect

**`unaccounted` is the number that matters and its floor is 0.** A record there
passed a screen that should have rejected it, so any non-zero is tonight's leak,
not a backlog — run with `--since` after a night's ingest and it answers the only
question worth asking of this check.

**A ruled XGL record is not listed again.** Housekeeping job 71 read the whole XGL-only
set on 2026-08-23 and recorded its ruling in `lookups/xgl-ruled.csv`; those slugs are
counted `in` for this screen's purposes and drop out of the list, so what `--xgl` shows is
what has arrived since and still wants a reading.

**`xgl` is reported and never called a defect.** Whether an item earns the code is
a reading no lint can do: *Closing the Adoption Gap: How AI Is Being Built in the
Global South* plainly earns it and a Turkish national AI plan plainly does not, and
nothing in frontmatter separates them. `wiki/facets.md` -> PLACE carries the test
- would removing Africa from the world leave the item without a subject - and the
backlog settles as that reading is applied, not as a number is driven down.

Reads `raw/` frontmatter through the index, never a compiled or published view: the
derived layer carries titles and facets but not the reason a record is in the vault
at all. Report-only. Nothing here writes.
"""

import argparse
import os
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COUNTRIES = os.path.join(V.ROOT, "lookups", "countries.csv")


def african_codes():
    """Every place code except `XGL` — the tree's root is the one non-African place."""
    with open(COUNTRIES, newline="", encoding="utf-8-sig") as f:
        return {r["iso-3"].strip() for r in csv.DictReader(f)
                if r["iso-3"].strip() and r["iso-3"].strip() != "XGL"}


def sort_sources(since=None):
    african = african_codes()
    ruled = set()
    rp = os.path.join(V.ROOT, "lookups", "xgl-ruled.csv")
    if os.path.exists(rp):
        import csv as _csv
        for row in _csv.DictReader(open(rp, encoding="utf-8")):
            ruled.add(row["slug"].strip())
    inr, xgl, un = [], [], []
    for r in V.load_index():
        fm = r.get("fm") or {}
        if fm.get("type") != "source" or not r["path"].startswith("raw/"):
            continue
        when = str(fm.get("ingested") or fm.get("published") or "")
        if since and when < since:
            continue
        places = set(V.as_list(fm.get("places")))
        topics = V.as_list(fm.get("topics"))
        row = (when, r["path"], str(fm.get("title") or "")[:96])
        if places & african or any(str(t).startswith("geopol.") for t in topics):
            inr.append(row)
        elif "XGL" in places:
            # a ruled record is admissible and counted `in`; it is not listed again
            if os.path.splitext(os.path.basename(r["path"]))[0] in ruled:
                inr.append(row)
            else:
                xgl.append(row)
        else:
            un.append(row)
    return inr, xgl, un


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--since", metavar="YYYY-MM-DD",
                    help="only sources ingested (or published) on or after this date")
    ap.add_argument("--xgl", action="store_true",
                    help="list the XGL-only set too — a reading, not a defect list")
    ap.add_argument("--limit", type=int, default=40, help="lines per list (default 40)")
    a = ap.parse_args()

    inr, xgl, un = sort_sources(a.since)
    scope = f" since {a.since}" if a.since else ""
    print(f"lint-scope over {len(inr) + len(xgl) + len(un)} source(s) in raw/{scope}")
    print(f"  in          {len(inr):5d}  African place, or a geopol.* slug")
    print(f"  xgl         {len(xgl):5d}  XGL only, unruled — reported, never a defect")
    print(f"  unaccounted {len(un):5d}  neither — the place bar was not applied")

    if a.xgl and xgl:
        print("\nXGL only — does each earn the code? (facets.md -> PLACE)")
        for when, path, title in sorted(xgl, reverse=True)[:a.limit]:
            print(f"  {when}  {path}\n      {title}")
        if len(xgl) > a.limit:
            print(f"  … {len(xgl) - a.limit} more (--limit)")

    if un:
        print("\nunaccounted — no African place, no XGL, no geopol.*:")
        for when, path, title in sorted(un, reverse=True)[:a.limit]:
            print(f"  {when}  {path}\n      {title}")
        if len(un) > a.limit:
            print(f"  … {len(un) - a.limit} more (--limit)")
        print("\nEach is either a mis-tag (the place is simply missing) or out of remit.")
        print("Out of remit -> delete and `raw-url-index.py --reject out-of-remit URL`,")
        print("so the negative outlives the record and the next sweep does not re-admit it.")
    return 1 if un else 0


if __name__ == "__main__":
    sys.exit(main())
