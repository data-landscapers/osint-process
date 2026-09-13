#!/usr/bin/env python3
"""page-index.py — read a synthesis page's *shape* without reading the page.

Written 2026-08-03, after a housekeeping session on `tech.ai` (jobs 30/32) in
which the same ad-hoc measurement was hand-written three times. The pages that
most need trimming are the ones too large to open cheaply — `tech.ai` alone is
10% of all concept prose, and the top 8 concept pages are 45% of it — so the
step that makes a trim session affordable is seeing the structure first and
opening only the bullets that need rewriting.

This script reports **shape, never content**: section sizes, a numbered bullet
index with lead-ins, and `## By place` cells measured against `operations.md`
§8's materiality bar. It changes nothing.

Usage:
  python scripts/page-index.py wiki/concepts/tech.ai.md          # sections + headline numbers
  python scripts/page-index.py wiki/concepts/tech.ai.md -b       # bullet index (largest section)
  python scripts/page-index.py wiki/concepts/tech.ai.md -b -s "Key material"
  python scripts/page-index.py wiki/concepts/tech.ai.md -c       # By place cells vs the §8 bar
  python scripts/page-index.py --all                             # every concept page by size
  python scripts/page-index.py --all --over 2500                 # only those past the §8 prompt

§8's bar for extracting a `{place}--{topic}` intersection: roughly >=120 words,
or >=2 cited sources, or >=3 distinct developments. Cells below it stay on the
parent as one-line index entries.
"""
import argparse, os, re, sys

# The corpus is multilingual and headings carry em-dashes; a cp1252 console
# would otherwise mangle or crash on printed page text.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAR_WORDS, BAR_SOURCES = 120, 2
SECTION_RE = re.compile(r"^##+ ")
BULLET_RE = re.compile(r"^- \*\*")
CELL_RE = re.compile(r"^- \*\*\[\[([A-Z]{3})\]\]")
LINK_RE = re.compile(r"\[\[(\d{4}-[^\]|]+?)(?:\|[^\]]*)?\]\]")


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", errors="replace").replace("\r\n", "\n").split("\n")


def sections(lines):
    """[(heading, start, end)] over the whole file."""
    idx = [i for i, l in enumerate(lines) if SECTION_RE.match(l)]
    out = []
    for k, i in enumerate(idx):
        j = idx[k + 1] if k + 1 < len(idx) else len(lines)
        out.append((lines[i].lstrip("# ").strip(), i, j))
    return out


def group(lines, lo, hi, pattern):
    """Fold continuation lines into their bullet. -> [(start, end, text)]"""
    out, cur, start = [], None, None
    for i in range(lo, hi):
        if pattern.match(lines[i]):
            if cur is not None:
                out.append((start, i, cur))
            cur, start = lines[i], i
        elif cur is not None:
            cur += " " + lines[i]
    if cur is not None:
        out.append((start, hi, cur))
    return out


def lead(text, width):
    t = re.sub(r"^- \*\*", "", re.sub(r"\s+", " ", text))
    return t[:width]


def show_sections(path, lines):
    total = len(" ".join(lines).split())
    print(f"{os.path.relpath(path, ROOT)} - {total:,} words, {len(lines):,} lines\n")
    print(f"{'words':>8}  {'share':>6}  section")
    for name, a, b in sections(lines):
        w = len(" ".join(lines[a:b]).split())
        print(f"{w:>8,}  {100*w/total:>5.0f}%  {name}")
    return total


def show_bullets(lines, want, width):
    secs = sections(lines)
    if want:
        hit = [s for s in secs if want.lower() in s[0].lower()]
        if not hit:
            sys.exit(f"no section matching {want!r}; have: {[s[0] for s in secs]}")
        name, a, b = hit[0]
    else:
        name, a, b = max(secs, key=lambda s: len(" ".join(lines[s[1]:s[2]]).split()))
    bl = group(lines, a + 1, b, BULLET_RE)
    print(f"\n## {name} — {len(bl)} bullets, "
          f"{len(' '.join(lines[a:b]).split()):,} words\n")
    print(f"{'#':>3} {'line':>6} {'words':>6} {'src':>4}  lead-in")
    for k, (s, _e, t) in enumerate(bl):
        print(f"{k:>3} {s+1:>6} {len(t.split()):>6} {len(set(LINK_RE.findall(t))):>4}  {lead(t, width)}")


def show_cells(lines, width):
    secs = [s for s in sections(lines) if s[0].lower().startswith("by place")]
    if not secs:
        sys.exit("no '## By place' section on this page")
    name, a, b = secs[0]
    cells = group(lines, a + 1, b, CELL_RE)
    seen, dupes = {}, []
    print(f"\n## {name} — {len(cells)} cells, "
          f"{len(' '.join(lines[a:b]).split()):,} words")
    print(f"(s8 bar: >={BAR_WORDS}w or >={BAR_SOURCES} sources)\n")
    print(f"{'iso':<5}{'line':>6}{'words':>7}{'src':>5}  {'bar':<9} target / lead-in")
    over = 0
    for s, _e, t in cells:
        iso = CELL_RE.match(t).group(1)
        w, n = len(t.split()), len(set(LINK_RE.findall(t)))
        bar = "OVER-BAR" if (w >= BAR_WORDS or n >= BAR_SOURCES) else ""
        over += bool(bar)
        tgt = re.search(r"\[\[([a-z][a-z0-9-]*--[a-z0-9-]+)\]\]", t)
        note = tgt.group(1) if tgt else "(no intersection)"
        if iso in seen:
            dupes.append((iso, seen[iso], s + 1))
        else:
            seen[iso] = s + 1
        print(f"{iso:<5}{s+1:>6}{w:>7}{n:>5}  {bar:<9} {note}")
    print(f"\n{over} of {len(cells)} cells are over the s8 bar")
    if dupes:
        print("\n!! DUPLICATE CELLS — one place, two entries. Check whether the "
              "second corrects the first before merging:")
        for iso, first, second in dupes:
            print(f"   {iso}: lines {first} and {second}")
    else:
        print("no duplicate place cells")


def show_all(over):
    d = os.path.join(ROOT, "wiki", "concepts")
    rows = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".md"):
            rows.append((len(" ".join(read(os.path.join(d, f))).split()), f))
    rows.sort(reverse=True)
    total = sum(w for w, _ in rows)
    shown = [r for r in rows if r[0] >= over]
    print(f"{len(rows)} concept pages, {total:,} words total\n")
    print(f"{'words':>8}  {'cum%':>5}  page")
    run = 0
    for w, f in shown:
        run += w
        print(f"{w:>8,}  {100*run/total:>4.0f}%  {f}")
    if over:
        print(f"\n{len(shown)} of {len(rows)} pages at or past {over:,} words "
              f"- {100*sum(w for w,_ in shown)/total:.0f}% of all concept prose")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("page", nargs="?", help="path to a markdown page")
    ap.add_argument("-b", "--bullets", action="store_true", help="numbered bullet index")
    ap.add_argument("-c", "--cells", action="store_true", help="'## By place' cells vs the s8 bar")
    ap.add_argument("-s", "--section", help="section to index (default: the largest)")
    ap.add_argument("-w", "--width", type=int, default=88, help="lead-in width (default 88)")
    ap.add_argument("--all", action="store_true", help="every concept page by size")
    ap.add_argument("--over", type=int, default=0, help="with --all, only pages at/past N words")
    a = ap.parse_args()

    if a.all:
        return show_all(a.over)
    if not a.page:
        ap.error("give a page, or --all")
    path = a.page if os.path.isabs(a.page) else os.path.join(ROOT, a.page)
    if not os.path.exists(path):
        sys.exit(f"no such file: {a.page}")
    lines = read(path)
    show_sections(path, lines)
    if a.bullets:
        show_bullets(lines, a.section, a.width)
    if a.cells:
        show_cells(lines, a.width)


if __name__ == "__main__":
    main()
