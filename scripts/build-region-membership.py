#!/usr/bin/env python3
"""
build-region-membership.py — the R11 region-membership lookup (2026-08-16).

wiki/entities/ is being retired (R11 — the OSINT/CORPUS migration): pages
go, the `entities:` tag on sources stays. CORPUS's report-region-init.py
scopes a region by two halves — sources carrying the region's place code,
and sources that reach the region only through an institution. The second
half was built from the entity pages' own frontmatter: entity_type in
(organisation, government-body, initiative, instrument) plus a regional
`places` list. Losing the pages loses that half silently unless it is
lifted out first.

Writes lookups/region-membership.csv: slug, entity_type, places (the page's
full places list, semicolon-joined) — one row per entity page whose
entity_type is one of the four kinds above AND whose places list carries
at least one X-prefixed region code.

Usage: python scripts/build-region-membership.py [--check]
  --check   report the count and per-region breakdown without writing
Exit: 0 always (a report script, not a lint) unless the folder is missing.
"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTITIES = os.path.join(ROOT, "wiki", "entities")
OUT = os.path.join(ROOT, "lookups", "region-membership.csv")

WANTED_TYPES = {"organisation", "government-body", "initiative", "instrument"}
REGION_RE = re.compile(r"^X[A-Z]{2}$")

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_list_field(fm_text, key):
    """`key: [A, B, C]` on one line, or `key: A` — the shape every entity page uses."""
    m = re.search(rf"^{key}:\s*(.+)$", fm_text, re.MULTILINE)
    if not m:
        return []
    raw = m.group(1).strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [v.strip() for v in raw.split(",") if v.strip()]


def parse_scalar_field(fm_text, key):
    m = re.search(rf"^{key}:\s*(\S+)\s*$", fm_text, re.MULTILINE)
    return m.group(1).strip() if m else None


def main():
    check_only = "--check" in sys.argv

    if not os.path.isdir(ENTITIES):
        print(f"build-region-membership: {ENTITIES} does not exist.")
        return 1

    rows = []
    region_counts = {}
    for fn in sorted(os.listdir(ENTITIES)):
        if not fn.endswith(".md") or fn.startswith("_"):
            continue
        path = os.path.join(ENTITIES, fn)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        m = FRONTMATTER_RE.match(text)
        if not m:
            continue
        fm = m.group(1)

        entity_type = parse_scalar_field(fm, "entity_type")
        if entity_type not in WANTED_TYPES:
            continue

        places = parse_list_field(fm, "places")
        regions = [p for p in places if REGION_RE.match(p)]
        if not regions:
            continue

        slug = fn[:-3]
        rows.append((slug, entity_type, ";".join(places)))
        for r in regions:
            region_counts[r] = region_counts.get(r, 0) + 1

    print(f"build-region-membership: {len(rows)} entity pages carry region membership "
          f"(entity_type in {sorted(WANTED_TYPES)}, places carries an X-prefixed code)")
    for r in sorted(region_counts):
        print(f"  {r} {region_counts[r]}")

    if check_only:
        return 0

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "entity_type", "places"])
        for row in rows:
            w.writerow(row)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
