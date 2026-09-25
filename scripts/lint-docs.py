#!/usr/bin/env python3
"""lint-docs.py — every process and documentation file names its reader, and stays under that reader's cap.

    python scripts/lint-docs.py                 # root *.md, documentation/*.md, wiki/*.md
    python scripts/lint-docs.py --report        # list breaches, exit 0
    python scripts/lint-docs.py --root C:\\X --glob "*.md" --glob "wiki/*.md" --caps path\\to\\global-claude.md

**Strategic review 5, R65 and R86.** The rule and the cap table live in `documentation/global-claude.md`
→ *Writing*, and this reads the table from there, so the caps have one home. A CC file is capped
whole, by the class its `type:` falls in; a Bill file is capped per part: preamble, block and
register annotation. A missing `reader:` fails, and so does a CC file whose `type:` is in no class,
because a file with no class has no cap.

**The reader is in frontmatter, or on the first line as `<!-- reader: cc; type: runbook -->`** where
frontmatter would show (a public README) or would change what a parser makes of the file (OSINT's
process files and wiki specs, which carry none). The cap table is read from
`documentation/global-claude.md`, or from the root `CLAUDE.md` where that file is absent (OSINT). Words are counted outside frontmatter, fenced code and HTML comments.
`documentation/archived/` is the record and is not read.

Exit 0 clean (or `--report`), 1 on any breach, 2 when the cap table cannot be read.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(os.path.abspath(__file__))))
def caps_for(root: str) -> str:
    """The cap table's file for a tree: `documentation/global-claude.md`, else the root `CLAUDE.md`."""
    here = [os.path.join(root, "documentation", "global-claude.md"), os.path.join(root, "CLAUDE.md")]
    return next((p for p in here if os.path.exists(p)), here[0])


CAPS = caps_for(ROOT)
GLOBS = ["*.md", "documentation/*.md", "wiki/*.md"]

FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
FIRST_LINE = re.compile(r"\A<!--\s*(reader:[^>]*?)\s*-->")
CODE = re.compile(r"^```.*?^```", re.S | re.M)
COMMENT = re.compile(r"<!--.*?-->", re.S)
ROW = re.compile(r"^\|\s*(cc|bill)\s*\|\s*([a-z-]+)\s*\|\s*([^|]*)\|\s*([\d,]+) words\s*\|\s*$", re.M)
ANNOTATION = re.compile(r"\*Done\b[^*]*\*")


def load_caps(path: str) -> tuple[dict, dict]:
    """`({type: (class, cap)} for cc, {class: cap} for bill)` from the table in `global-claude.md`."""
    text = open(path, encoding="utf-8").read()
    cc, bill = {}, {}
    for reader, cls, types, cap in ROW.findall(text):
        cap = int(cap.replace(",", ""))
        if reader == "bill":
            bill[cls] = cap
            continue
        for t in (x.strip().strip("`") for x in types.split(",")):
            if t:
                cc[t] = (cls, cap)
    if not cc or not {"preamble", "block", "annotation"} <= set(bill):
        raise ValueError(f"no complete cap table in {path}")
    return cc, bill


def words(text: str) -> int:
    return len(text.split())


def split(text: str) -> tuple[dict, str]:
    """`(frontmatter fields, body)` with code and comments already out of the body."""
    fields, body = {}, text
    m = FM.match(text)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v and not line.startswith((" ", "\t")):
                fields[k.strip()] = v.strip()
        body = text[m.end():]
    else:
        first = FIRST_LINE.match(text)
        if first:
            for pair in first.group(1).split(";"):
                k, _, v = pair.partition(":")
                if v.strip():
                    fields[k.strip()] = v.strip()
    body = COMMENT.sub(" ", CODE.sub(" ", body))
    return fields, body


def blocks(body: str) -> list[str]:
    """Paragraphs and bullets: headings, tables and blank lines end a block; a bullet starts one."""
    out, cur = [], []
    for line in body.splitlines():
        s = line.strip()
        bullet = re.match(r"^([-*+]|\d+\.)\s", s)
        if not s or s.startswith(("#", "|")) or bullet:
            if cur:
                out.append(" ".join(cur))
            cur = [s[bullet.end():]] if bullet else []
            continue
        cur.append(s)
    if cur:
        out.append(" ".join(cur))
    return out


def check(path: str, rel: str, cc: dict, bill: dict) -> list[str]:
    fields, body = split(open(path, encoding="utf-8", errors="replace").read())
    reader = fields.get("reader", "").lower()
    if reader not in ("cc", "bill"):
        return [f"{rel}: no `reader: bill` or `reader: cc`" + (f" (has {reader!r})" if reader else "")]
    if reader == "cc":
        typ = fields.get("type", "").strip()
        if typ not in cc:
            return [f"{rel}: reader cc, `type: {typ or '(none)'}` is in no class, so no cap applies"]
        cls, cap = cc[typ]
        n = words(body)
        return [f"{rel}: {n:,} words, over the cc {cls} cap of {cap:,}"] if n > cap else []
    out = []
    head = re.split(r"(?m)^## ", body, maxsplit=1)[0]
    head = re.sub(r"(?m)^# .*$", " ", head)
    if words(head) > bill["preamble"]:
        out.append(f"{rel}: preamble {words(head)} words, over the bill cap of {bill['preamble']}")
    for b in blocks(body):
        if words(b) > bill["block"]:
            out.append(f"{rel}: block of {words(b)} words, over {bill['block']}: {b[:60]}…")
    for a in ANNOTATION.findall(body):
        if words(a) > bill["annotation"]:
            out.append(f"{rel}: annotation of {words(a)} words, over {bill['annotation']}: {a[:60]}…")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--glob", action="append", help="relative to --root; repeatable (default: root and documentation/)")
    ap.add_argument("--caps", help="the file holding the cap table (default: found under --root)")
    ap.add_argument("--report", action="store_true", help="list breaches and exit 0")
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        cc, bill = load_caps(a.caps or caps_for(a.root))
    except (OSError, ValueError) as e:
        print(f"lint-docs: cannot read the cap table - {e}")
        return 2
    files = sorted({p for g in (a.glob or GLOBS) for p in glob.glob(os.path.join(a.root, g))
                    if os.path.isfile(p) and "archived" not in os.path.relpath(p, a.root).split(os.sep)})
    breaches = []
    for p in files:
        breaches += check(p, os.path.relpath(p, a.root).replace(os.sep, "/"), cc, bill)
    for b in breaches:
        print(f"lint-docs: {b}")
    print(f"lint-docs: {'ok' if not breaches else 'FAIL'} - {len(files)} file(s), {len(breaches)} breach(es)")
    return 0 if a.report or not breaches else 1


if __name__ == "__main__":
    sys.exit(main())
