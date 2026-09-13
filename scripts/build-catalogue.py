#!/usr/bin/env python3
"""build-catalogue.py — the catalogue of everything held in `raw/`.

**Retired from the nightly cycle and from git 2026-08-16 (R2/R6)** — CORPUS now
builds and publishes its own catalogue from `raw/` and `wiki/`, so this script's
output, `outputs/catalogue/`, is no longer tracked or wired into anything. Left
standing in case OSINT ever wants its own local copy again.

What it built: a **committed, self-contained, filterable list of the holdings**,
where `index/` is local scaffolding — untracked, rebuilt, 14 MB of parser detail
nobody outside a script should read. This was the published view of it: one JSON
file, one CSV for everything else, and the facet counts a filter UI needs so it
does not have to scan the rows to build its own menus.

**Metadata only, deliberately.** Title, publisher, date, facets, URL, and whether
a document is held — enough to filter, search and cite. It carries no body text:
the bodies are other people's words held for the wiki's own use, and a catalogue
is not a place to republish them. The `url` sends a reader to the publisher.

Usage:
  python scripts/build-catalogue.py                 write outputs/catalogue/
  python scripts/build-catalogue.py --check         report drift, write nothing
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

OUT_DIR = os.path.join(V.ROOT, "outputs", "catalogue")
JSON_PATH = os.path.join(OUT_DIR, "raw-catalogue.json")
CSV_PATH = os.path.join(OUT_DIR, "raw-catalogue.csv")

CSV_COLS = ["slug", "title", "publisher", "author", "published", "date_precision",
            "places", "topics", "entities", "lens", "body_completeness", "finance",
            "artefact", "words", "ingested", "url"]


def items(rows):
    out = []
    artefacts = {r["path"].rsplit("/", 1)[-1]
                 for r in rows if r["d"].get("kind") == "artefact"}
    for r in rows:
        if not r["path"].startswith("raw/") or r["d"]["ext"] != ".md":
            continue
        fm, d = r["fm"], r["d"]
        held = [a for a in V.as_list(fm.get("artefact")) if a in artefacts]
        out.append({
            "slug": d["slug"],
            "path": r["path"],
            "title": fm.get("title") if isinstance(fm.get("title"), str) else d["slug"],
            "publisher": fm.get("publisher") or "",
            "author": fm.get("author") if isinstance(fm.get("author"), str) else "",
            "published": fm.get("published") or "",
            "date_precision": fm.get("date_precision") or "",
            "url": fm.get("url") if isinstance(fm.get("url"), str) else "",
            "places": V.as_list(fm.get("places")),
            "topics": V.as_list(fm.get("topics")),
            "entities": V.as_list(fm.get("entities")),
            "lens": V.as_list(fm.get("lens")),
            "body_completeness": fm.get("body_completeness") or "",
            "finance": bool(fm.get("finance_origin")),
            "artefact": held,
            "words": d.get("words", 0),
            "ingested": fm.get("ingested") or "",
        })
    out.sort(key=lambda x: (x["published"], x["slug"]), reverse=True)
    return out


def facets(rows):
    """Counts a filter UI can render its menus from without scanning the rows."""
    f = {}
    for key in ("places", "topics", "lens", "entities"):
        c = Counter(v for r in rows for v in r[key])
        # entities has a long single-reference tail by design (CLAUDE.md ->
        # Entities); a filter menu wants the ones that actually filter.
        f[key] = dict(c.most_common(200 if key == "entities" else None))
    f["publisher"] = dict(Counter(r["publisher"] for r in rows if r["publisher"]).most_common())
    f["year"] = dict(sorted(Counter(r["published"][:4] for r in rows if r["published"]).items()))
    f["body_completeness"] = dict(Counter(r["body_completeness"] for r in rows).most_common())
    return f


def write(rows, meta):
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = {"built": meta["built"][:10],
           "count": len(rows),
           "note": "Catalogue of sources held in raw/. Metadata only — follow `url` "
                   "to the publisher. Derived by scripts/build-catalogue.py; do not edit.",
           "facets": facets(rows),
           "items": rows}
    # One item per line: this file is tracked and rebuilt often, so a pretty-printed
    # array would show a 7,700-row rewrite whenever one source changed, while a
    # single minified line would show a whole-file diff. A line per source diffs
    # like the vault does — one changed line per changed source.
    head = {k: v for k, v in doc.items() if k != "items"}
    with open(JSON_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("{\n")
        for k, v in head.items():
            fh.write(f' {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)},\n')
        fh.write(' "items": [\n')
        for n, item in enumerate(rows):
            fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True))
            fh.write(",\n" if n < len(rows) - 1 else "\n")
        fh.write(" ]\n}\n")
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            flat = dict(r)
            for k in ("places", "topics", "entities", "lens", "artefact"):
                flat[k] = "; ".join(flat[k])
            w.writerow(flat)
    return doc


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true",
                    help="report how far the written catalogue is from the vault")
    a = ap.parse_args()

    meta = V.ensure_fresh()
    rows = items(V.load_index(auto=False))

    if a.check:
        if not os.path.exists(JSON_PATH):
            print(f"catalogue: not written yet ({len(rows):,} sources would be)")
            return 1
        held = json.load(open(JSON_PATH, encoding="utf-8"))
        drift = len(rows) - held.get("count", 0)
        print(f"catalogue: {held.get('count', 0):,} rows written {held.get('built')}, "
              f"{len(rows):,} in the vault ({drift:+,})")
        return 0 if drift == 0 else 1

    doc = write(rows, meta)
    print(f"catalogue: {doc['count']:,} sources -> outputs/catalogue/")
    print(f"  raw-catalogue.json {os.path.getsize(JSON_PATH)/1e6:.1f} MB, "
          f"raw-catalogue.csv {os.path.getsize(CSV_PATH)/1e6:.1f} MB")
    print(f"  facets: {len(doc['facets']['places'])} places, "
          f"{len(doc['facets']['topics'])} topics, "
          f"{len(doc['facets']['publisher'])} publishers, "
          f"{len(doc['facets']['year'])} years")
    return 0


if __name__ == "__main__":
    sys.exit(main())
