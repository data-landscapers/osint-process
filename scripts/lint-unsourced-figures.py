#!/usr/bin/env python3
"""lint-unsourced-figures.py — LINT.md check #20, the narrative layer.

Lint #3 catches an **undated** figure. Nothing caught an **unsourced** one, and the
two failures look nothing alike: a stale figure is visibly stale, whereas a number
with no source behind it reads exactly like a number with one. The class that
accumulates is the synthesis lede — rankings, market sizes and penetration rates,
written to frame a page, load-bearing by construction, and traceable to nothing.
Post-run note 98 found two such figures on Somalia pages that none of their own
cited sources carried.

**Scope: ledes only** — the prose between a page's `# H1` and its first `## `
heading, on place hubs. That is deliberate and it is where the class lives:

  - a hub's `## Recent developments` is compiled and every bullet ends in its
    `Source:` (HUB-COMPILE.md), and `## Financing` is compiled from the records;
  - the lede is the one block that is pure CC synthesis with no provenance
    machinery attached to it at all.

*(Entity pages retired 2026-08-16, R11 — this used to scope to them too.)*

**What counts as a source, in the lede itself:** a wikilink to a dated `raw/` slug
(`[[2026-04-25-...]]`, or the legacy `[[2024-12-09 Title]]` form), or an inline
URL. A `[[topic]]` or `[[entity]]` link is navigation, not provenance, and does not
count — which is the whole point, since an uncited lede is usually thick with them.

**Three figure classes, and nothing else.** Kept narrow on purpose: lint #3's
line-level money scan ran ~90% false-positive and stopped being read.

Usage:
  python scripts/lint-unsourced-figures.py            place hubs
  python scripts/lint-unsourced-figures.py --dir wiki/concepts
  python scripts/lint-unsourced-figures.py --show     print the whole offending lede
Exit code 1 if any lede carries an unsourced figure.
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIRS = ["wiki/places"]

# The vault is UTF-8; this console is cp1252. Without this an en dash inside a
# quoted figure kills the run mid-report, which is a check that stops being read.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The single-letter currency prefixes bind TIGHT to their digits. `R\s?` with the
# case-insensitive flag on matched "...r 2025**" in a French plan title and reported it
# as a market size; `R2 trillion` (SARS) is the form that is actually written.
MONEY = (r"(?:US\$|\$|€|£|₦|GH₵|KSh|CFA|XAF|XOF|ZAR|MAD|EGP|NGN|KES|R(?=\d))"
         r"\s?~?\d[\d,.\s]*(?:bn|billion|m|million|tn|trillion)?")

# 1. Ranking — "183rd of 193", "ranked 156th", "ranks 12th of 54".
RANK = [
    re.compile(r"\b\d{1,3}(?:st|nd|rd|th)\b[^.\n]{0,20}?\b(?:of|out of)\s+\d{1,3}\b"),
    re.compile(r"\brank(?:ed|s|ing|)\b[^.\n]{0,40}?\b\d{1,3}(?:st|nd|rd|th)\b", re.I),
    re.compile(r"\b\d{1,3}(?:st|nd|rd|th)\b[^.\n]{0,30}?\brank(?:ed|s|ing)?\b", re.I),
]

# 2. Market size — money adjacent to a market/sector/economy noun. NOT a deal:
#    a commitment lives in a finance record and reaches a page through the compile.
SIZE_NOUN = (r"market|sector|industry|economy|economies|revenues?|turnover|"
             r"GDP|GNI|valuation|worth|opportunity|spend(?:ing)?")
SIZE = [
    re.compile(MONEY + r"[^.\n]{0,45}?\b(?:" + SIZE_NOUN + r")\b", re.I),
    re.compile(r"\b(?:" + SIZE_NOUN + r")\b[^.\n]{0,45}?" + MONEY, re.I),
]

# 3. Penetration / share — a percentage attached to a coverage or share claim.
PEN_NOUN = (r"penetration|adoption|coverage|uptake|of GDP|of the population|of adults|"
            r"of households|banked|unbanked|subscriber|internet users|connected|"
            r"literacy|electrif|access rate|have access|market share")
PCT = r"~?\d[\d.,]*\s*(?:–|—|-|to)?\s*(?:\d[\d.,]*)?\s*%"
PEN = [
    re.compile(PCT + r"[^.\n]{0,45}?\b(?:" + PEN_NOUN + r")\b", re.I),
    re.compile(r"\b(?:" + PEN_NOUN + r")\b[^.\n]{0,45}?" + PCT, re.I),
]

CLASSES = [("ranking", RANK), ("market-size", SIZE), ("penetration", PEN)]

# Provenance, not navigation: a dated raw/ slug, or a URL.
CITED = re.compile(r"\[\[\s*\d{4}-\d{2}-\d{2}|\]\(\s*https?://|(?<![\[\w])https?://")


def lede(text):
    """The prose between the `# H1` and the first `## ` heading, with its offset.

    Returns ("", 0) where there is no H1 — a page with no title has no lede, and
    guessing one would scan the frontmatter.
    """
    body = text
    if body.startswith("---"):
        end = body.find("\n---", 3)
        if end > 0:
            body = body[end + 4:]
    m = re.search(r"^#\s+\S.*$", body, re.M)
    if not m:
        return "", 0
    rest = body[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    seg = rest[:nxt.start()] if nxt else rest
    # A blockquote in a lede is a standing rule or a worked example, not a claim —
    # `un-egdi.md`'s own "cite it dated: 189th of 193, 0.1785" is the instruction
    # for how to write the figure, and flagging it would be flagging the rule.
    # Fenced code is the same case. Neither ever carries the page's own assertions.
    seg = re.sub(r"^```.*?^```", "", seg, flags=re.M | re.S)
    seg = "\n".join(ln for ln in seg.splitlines() if not ln.lstrip().startswith(">"))
    line_no = body[:m.end()].count("\n") + (text[:len(text) - len(body)].count("\n") + 1)
    return seg, line_no


def findings(seg):
    """[(class, matched text)] for every figure in an UNSOURCED lede.

    Whole-lede granularity, not per sentence: a lede is one framing paragraph and
    its citations sit wherever they read best in it. Per-sentence would flag the
    second half of every properly-cited lede — the failure mode that made lint #3's
    old money scan unreadable.
    """
    if not seg.strip() or CITED.search(seg):
        return []
    out = []
    for name, pats in CLASSES:
        for p in pats:
            for m in p.finditer(seg):
                out.append((name, " ".join(m.group(0).split())))
                break                       # one exemplar per class per page
            else:
                continue
            break
    return out


def pages(dirs):
    for d in dirs:
        full = d if os.path.isabs(d) else os.path.join(ROOT, d)
        if not os.path.isdir(full):
            continue
        for fn in sorted(os.listdir(full)):
            if fn.endswith(".md") and not fn.startswith("_"):
                yield os.path.join(d, fn).replace("\\", "/"), os.path.join(full, fn)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", nargs="*", default=None)
    ap.add_argument("--show", action="store_true", help="print the offending lede")
    a = ap.parse_args()

    n = 0
    for rel, path in pages(a.dir or DEFAULT_DIRS):
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        seg, ln = lede(text)
        hits = findings(seg)
        if not hits:
            continue
        n += 1
        print("%s:%d" % (rel, ln))
        for cls, snip in hits:
            print("    %-12s %s" % (cls, snip[:110]))
        if a.show:
            print("    lede: %s" % " ".join(seg.split())[:400])

    print("\n%d lede%s carry a ranking, market-size or penetration figure with no source "
          "link in the lede." % (n, "" if n == 1 else "s"))
    if n:
        print("Fix: cite the source on the claim, or - where nothing establishes it - "
              "write the dated absence and drop the figure (CLAUDE.md -> Currency).")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
