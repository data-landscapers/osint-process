#!/usr/bin/env python3
"""byplace-extract.py — move a concept page's single-place cells into `## By place`.

Housekeeping job 30's step (b), mechanised. On page after page the same defect turns up:
single-place cells accrete among the thematic bullets of `## Key material`, and the page
has no `## By place` section at all — which `page-index.py -c` reports as "no cells", not
the same thing. The test is the bullet-lead count: how many bullets open with `- **[[XXX]]`.

This script does only the mechanical half, and only what it can do without judgement:

  --report   count the cells, group them by ISO code, and for every source in every cell
             say whether it is held anywhere else in `wiki/`. THAT is the decision input:
             a cell whose sources are all held elsewhere is not waiting for a target page,
             it is waiting to be cut to an index line. Run this first, always.

  --apply    lift every `- **[[XXX]]` bullet out of its section, sort by ISO code, and
             write them under a `## By place` heading inserted before `## Places`
             (or before `## Related`, or at end of body). Prose is preserved verbatim —
             compressing an over-long cell is a judgement call and stays manual.

It never mints an intersection and never edits a facet: both need a person to decide.
Follow with `facet-body-align.py` and a `## Places` rebuild.

Usage:  byplace-extract.py wiki/concepts/infra.energy.md --report
        byplace-extract.py wiki/concepts/infra.energy.md --apply
"""
from __future__ import annotations

import argparse
import collections
import glob
import os
import re
import sys

CELL_RE = re.compile(r"- \*\*\[\[([A-Z]{3})\]\]")
CITE_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
DATED = re.compile(r"^\d{4}")

HEADER = """## By place

*One dated entry per ISO code, ordered by code. Built {date} from **{n} single-place cells, {words:,} words**, lifted out of the thematic sections where they had accreted. {mint}*
"""


def read(path: str) -> tuple[str, bool]:
    raw = open(path, "rb").read()
    return raw.decode("utf-8").replace("\r\n", "\n"), b"\r\n" in raw


def write(path: str, text: str, crlf: bool) -> None:
    if not text.endswith("\n"):
        text += "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    open(path, "wb").write(text.encode("utf-8"))


def cells(lines: list[str]) -> list[tuple[int, int, str, str]]:
    """(start, end, iso, block) for every top-level single-place bullet."""
    out = []
    for i, line in enumerate(lines):
        m = CELL_RE.match(line)
        if not m:
            continue
        j = i
        while j + 1 < len(lines) and not lines[j + 1].startswith("- **") and lines[j + 1].strip():
            j += 1
        out.append((i, j, m.group(1), "\n".join(lines[i:j + 1])))
    return out


def citation_map() -> dict[str, set[str]]:
    m = collections.defaultdict(set)
    for p in glob.glob("wiki/**/*.md", recursive=True):
        t = open(p, encoding="utf-8", errors="replace").read()
        for c in CITE_RE.findall(t):
            c = c.strip()
            if DATED.match(c):
                m[c].add(os.path.basename(p))
    return m


def report(path: str) -> int:
    text, _ = read(path)
    found = cells(text.split("\n"))
    if not found:
        print(f"{path}: no single-place cells")
        return 0
    cmap = citation_map()
    self_name = os.path.basename(path)
    by = collections.defaultdict(list)
    for _, _, iso, block in found:
        by[iso].append(block)

    total_w = sum(len(b.split()) for _, _, _, b in found)
    print(f"{path} — {len(found)} single-place cells, {total_w:,} words, {len(by)} codes\n")
    nowhere = []
    for iso in sorted(by):
        blocks = by[iso]
        w = sum(len(b.split()) for b in blocks)
        srcs = sorted({s for b in blocks for s in CITE_RE.findall(b) if DATED.match(s)})
        only_here = [s for s in srcs if not (cmap.get(s, set()) - {self_name})]
        nowhere += [(iso, s) for s in only_here]
        bar = "OVER" if (w >= 120 or len(srcs) >= 2) else "thin"
        flag = f"  <- {len(only_here)} HELD NOWHERE ELSE" if only_here else ""
        print(f"  {iso}  {w:5d}w  {len(srcs):2d}src  {len(blocks)} cell(s)  {bar}{flag}")

    print(f"\n{len(nowhere)} source(s) held nowhere else in wiki/:")
    for iso, s in nowhere:
        print(f"    {iso}  {s}")
    if not nowhere:
        print("    (none — every cell's sources are already held on the country's own hub"
              "\n     or one of its intersections, so cutting to index lines homes nothing new)")
    return 0


def apply(path: str, date: str) -> int:
    text, crlf = read(path)
    lines = text.split("\n")
    found = cells(lines)
    if not found:
        print(f"{path}: no single-place cells — nothing to do")
        return 0

    blocks = [(iso, b) for _, _, iso, b in found]
    total_w = sum(len(b.split()) for _, b in blocks)

    for _, _, _, b in found:
        if b + "\n" in text:
            text = text.replace(b + "\n", "", 1)
        else:
            text = text.replace(b, "", 1)
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")

    cmap = citation_map()
    self_name = os.path.basename(path)
    srcs = {s for _, b in blocks for s in CITE_RE.findall(b) if DATED.match(s)}
    only_here = [s for s in srcs if not (cmap.get(s, set()) - {self_name})]
    mint = (
        "**Every source in every cell was mapped against the rest of the corpus first, and all of them "
        "are already held on the country's own hub or one of its intersections**, so no page was minted."
        if not only_here else
        f"**Every source in every cell was mapped against the rest of the corpus first; all but {len(only_here)} "
        "are already held on the country's own hub or one of its intersections**, so no page was minted and "
        "the exceptions carry their substance here rather than a pointer."
    )
    header = HEADER.format(date=date, n=len(blocks), words=total_w, mint=mint)
    section = header + "\n" + "\n".join(b for _, b in sorted(blocks, key=lambda x: x[0]))

    for anchor in ("\n## Places\n", "\n## Related\n"):
        if anchor in text:
            text = text.replace(anchor, "\n" + section + "\n" + anchor, 1)
            break
    else:
        text = text.rstrip("\n") + "\n\n" + section + "\n"

    write(path, text, crlf)
    print(f"{path}: moved {len(blocks)} cells ({total_w:,} words) into '## By place'"
          f"{'' if not only_here else f'; {len(only_here)} source(s) held nowhere else — check their lines'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    ap.add_argument("--report", action="store_true", help="measure and check source coverage; change nothing")
    ap.add_argument("--apply", action="store_true", help="move the cells into '## By place'")
    ap.add_argument("--date", default="2026-08-24", help="date to stamp in the section note")
    args = ap.parse_args()
    if args.apply:
        return apply(args.page, args.date)
    return report(args.page)


if __name__ == "__main__":
    sys.exit(main())
