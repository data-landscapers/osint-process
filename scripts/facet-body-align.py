#!/usr/bin/env python3
"""facet-body-align.py — check a page's `sources:` facet against what its body actually cites.

The `sources:` frontmatter facet is meant to list exactly the sources the page cites.
Nothing in lint checks this, and housekeeping job 30 found real drift in both directions
on every page it measured:

  orphans  — slugs in the facet the body cites nowhere. Worse than a missing one: the page
             looks sourced where it is not, and `uncited-sources.py` is fooled into thinking
             the material was used.
  missing  — slugs the body cites that the facet omits.
  dupes    — the same slug entered twice in the facet.

Also reports body citations that resolve to no file in `raw/` (fabricated or mistyped).

Usage:  facet-body-align.py wiki/concepts/data.open.md [more pages ...]
        facet-body-align.py --all          every concept page
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

RAW_GLOB = "raw/**/*.md"
CITE_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")


def raw_index() -> set[str]:
    return {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(RAW_GLOB, recursive=True)}


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end], text[end + 4:]


def facet_sources(fm: str) -> list[str]:
    """Parse `sources: [[a], [b], ...]` — flow style, possibly spanning lines."""
    m = re.search(r"^sources:(.*)$", fm, re.M)
    if not m:
        return []
    tail = fm[m.start(1):]
    # take up to the next top-level key
    stop = re.search(r"^\w[\w-]*:", tail[1:], re.M)
    blob = tail[: stop.start() + 1] if stop else tail
    return [s.strip() for s in re.findall(r"\[([^\[\]]+)\]", blob) if s.strip()]


def body_citations(body: str) -> set[str]:
    """Wikilinks in the body that name a dated source (`YYYY-MM-DD...`)."""
    out = set()
    for target in CITE_RE.findall(body):
        t = target.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}", t):
            out.add(t)
    return out


def check(path: str, raw: set[str]) -> int:
    text = open(path, encoding="utf-8", errors="replace").read()
    fm, body = split_frontmatter(text)
    facet = facet_sources(fm)
    seen, dupes = set(), []
    for s in facet:
        if s in seen:
            dupes.append(s)
        seen.add(s)
    cited = body_citations(body)
    orphans = sorted(seen - cited)
    missing = sorted(cited - seen)
    unresolved = sorted(c for c in cited if c not in raw)
    facet_unresolved = sorted(s for s in seen if s not in raw)

    bad = len(orphans) + len(missing) + len(dupes) + len(unresolved) + len(facet_unresolved)
    print(f"{path} — facet {len(seen)} unique / {len(facet)} entries, body cites {len(cited)}")
    if not bad:
        print("  aligned: 0 orphans, 0 missing, 0 duplicates, 0 unresolved")
        return 0
    for label, items in (
        ("orphan (in facet, body cites nowhere)", orphans),
        ("missing (body cites, not in facet)", missing),
        ("duplicate facet entry", dupes),
        ("body citation resolves to no raw/ file", unresolved),
        ("facet slug resolves to no raw/ file", facet_unresolved),
    ):
        if items:
            print(f"  {len(items)} {label}:")
            for i in items:
                print(f"    {i}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--all", action="store_true", help="every concept page")
    args = ap.parse_args()

    pages = args.pages
    if args.all:
        pages = sorted(glob.glob("wiki/concepts/*.md"))
    if not pages:
        ap.error("give one or more pages, or --all")

    raw = raw_index()
    total = 0
    for p in pages:
        total += check(p, raw)
        print()
    print(f"{len(pages)} page(s), {total} finding(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
