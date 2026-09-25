#!/usr/bin/env python3
"""catalogue-hero-set.py — write or rewrite a source's `catalogue_hero:`, in bulk.

`catalogue_hero` is the record's subtitle in the public catalogue at
corpus.data-landscapers.io/catalogue/ — `schemas.md` §4 for the contract,
`INGEST.md` step 3a for where it is written. Unlike `hub_line` it has no
editorial gate and no refusal form: every source carries one, so this script
only ever sets a value, and the one thing it will not do is remove it.

It exists for the same reason `hub-line-set.py` does. A ten-item ingest slice
writing ten heroes by hand is ten edits to YAML frontmatter, which is how
frontmatter gets corrupted; the coming backfill over the pre-contract corpus is
the same edit some thousands of times. The hero is CC's own bookkeeping and not
evidence (`schemas.md` §4), so setting one in place is maintenance rather than a
breach of `raw/` immutability. Nothing else in the file is touched: the dominant
EOL, the body and every other key come back byte-identical.

Input is JSONL, one object per line:

    {"slug": "2026-08-04-foo", "hero": "USD 45m concessional loan to Kenya Power, signed 2026-03-11"}

The value is written as a **double-quoted one-line scalar**, which keeps the key
greppable and the diff to one line per edit. A hero is a plain-text subtitle, so
the only characters needing care are `"` and `\\`, and both are escaped here; a
value carrying a newline is refused rather than folded, because a two-line
subtitle is a defect the catalogue cannot render (lint #34).

The shape rules — 120 characters, no markdown, no terminal full stop, not a
restatement of the title — are asserted here as well as by lint #34, so a bad
hero is refused at the point of writing rather than found a cycle later.

Usage:
  python scripts/catalogue-hero-set.py patch.jsonl            dry run: what would change
  python scripts/catalogue-hero-set.py patch.jsonl --write    apply
"""
import argparse, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAW = "raw"
CAP = 120
FM = re.compile(r"^---\r?\n(.*?\r?\n)---\r?\n", re.S)
MARKUP = re.compile(r"\[\[|\*\*|\]\(")


def read(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    return b.decode("utf-8"), ("\r\n" if crlf * 2 > b.count(b"\n") else "\n")


def title_of(fm_text):
    m = re.search(r"^title:[ \t]*(.+?)[ \t]*$", fm_text, re.M)
    if not m:
        return ""
    t = m.group(1).strip()
    if len(t) > 1 and t[0] == t[-1] and t[0] in "\"'":
        t = t[1:-1]
    return t


def check(hero, title):
    """The contract, as the reasons a hero is refused. None means it passes."""
    if not hero.strip():
        return "empty"
    if "\n" in hero or "\r" in hero:
        return "more than one line"
    if len(hero) > CAP:
        return "%d characters, cap is %d" % (len(hero), CAP)
    if hero.rstrip().endswith("."):
        return "ends in a full stop"
    if MARKUP.search(hero):
        return "carries markdown"
    if title:
        a, b = hero.lower(), title.lower()
        # A hero *containing* a one- or two-word title (`IFMIS`, `Lusaka IX`) is naming what
        # it is about, not restating it; containment counts from three words (R74).
        if a == b or a in b or (b in a and len(b.split()) >= 3):
            return "repeats the title"
    return None


def apply(text, hero):
    """(text, note). The text comes back unchanged with a note when nothing applies."""
    m = FM.match(text)
    if not m:
        return text, "no-frontmatter"
    fm = m.group(1)
    bad = check(hero, title_of(fm))
    if bad:
        return text, bad
    nl = "\r\n" if "\r\n" in fm else "\n"
    lines = fm.split(nl)               # ends in "" — the capture keeps its newline
    value = 'catalogue_hero: "%s"' % hero.replace("\\", "\\\\").replace('"', '\\"')
    at = next((k for k, ln in enumerate(lines)
               if re.match(r"^catalogue_hero:", ln)), None)
    if at is None:
        # Appended as the last key, before the closing `---`. A one-line scalar has
        # no continuation to extend over, so there is nothing here to measure.
        lines = lines[:-1] + [value, lines[-1]]
    else:
        lines[at] = value
    return text[:m.start(1)] + nl.join(lines) + text[m.end(1):], "ok"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("patch", help="JSONL: one {\"slug\": ..., \"hero\": ...} per line")
    ap.add_argument("--write", action="store_true", help="apply; otherwise a dry run")
    a = ap.parse_args()

    index = {n[:-3]: p for n, p in raw_sources(RAW)}
    ok = noop = 0
    refused = []
    for raw_line in open(a.patch, encoding="utf-8"):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        rec = json.loads(raw_line)
        slug, hero = rec["slug"], rec.get("hero", "")
        path = index.get(slug)
        if not path:
            refused.append((slug, "no such source in raw/"))
            continue
        text, _ = read(path)
        new, note = apply(text, hero)
        if note != "ok":
            refused.append((slug, note))
            continue
        if new == text:
            noop += 1
            continue
        ok += 1
        if a.write:
            open(path, "wb").write(new.encode("utf-8"))

    for slug, why in refused:
        print("REFUSED %s — %s" % (slug, why))
    print("%s: %d set, %d already correct, %d refused"
          % ("written" if a.write else "dry run", ok, noop, len(refused)))
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
