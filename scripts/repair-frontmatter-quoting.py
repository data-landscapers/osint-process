#!/usr/bin/env python
"""repair-frontmatter-quoting.py — quote the frontmatter scalars that make a record unparseable.

Housekeeping job 95. `raw/` is what CORPUS reads, and a record whose frontmatter fails
`yaml.safe_load` is invisible to the consumer rather than merely untidy. Almost every case
is one fault: an **unquoted scalar containing `": "`**, which YAML reads as a nested mapping —

    title: Uganda: The Experience of Cross Border Travel Using National ID

Quoting a scalar that already fails to parse cannot change its meaning, which is what makes
this half of the job scripted rather than read-and-judge. The script therefore refuses every
case where that argument does not hold:

  * it only ever touches a file whose frontmatter fails to parse **now**;
  * it only rewrites a **single-line, top-level, unquoted** scalar;
  * it re-parses the repaired block and **reverts the file unless it now loads as a mapping
    and every other key's value is byte-identical** to what a hand-read would give;
  * anything it cannot fix this way is printed, not guessed at.

Line endings are preserved per file: the vault holds both terminators deliberately
(`.gitattributes`), and this writes back exactly the terminator each line arrived with.

A second fault is handled on the same terms: a flow sequence written with semicolons,
`fiscal_years_covered: ["2025/26"; "2026/27"]`, which YAML cannot read at all. The
separator is replaced only where the repaired sequence loads as a list whose items are
exactly the quoted scalars that were already on the line.

    python scripts/repair-frontmatter-quoting.py            # dry run, the default
    python scripts/repair-frontmatter-quoting.py --write
    python scripts/repair-frontmatter-quoting.py --diff     # dry run, printing each rewrite
    python scripts/repair-frontmatter-quoting.py raw budget-archive wiki   # pick the trees
"""
import glob
import io
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*):(?:[ \t]+(.*))?$')
FM = re.compile(r'^(---\r?\n)(.*?)(\r?\n---\r?\n)', re.S)
SEQ_ITEM = re.compile(r'"([^"]*)"')


def parses(block):
    """The frontmatter loads, and loads as a mapping."""
    try:
        d = yaml.safe_load(block)
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def quote(v):
    """A double-quoted YAML scalar carrying exactly the characters of `v`."""
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def repair(block):
    """Return (new_block, keys_quoted) or (None, reason) where the argument does not hold."""
    lines = block.split("\n")
    out = list(lines)
    quoted, seqs = {}, {}
    for i, line in enumerate(lines):
        # this vault holds both terminators deliberately; keep whichever this line has
        cr = "\r" if line.endswith("\r") else ""
        m = KEY.match(line[:-1] if cr else line)
        if not m:
            continue
        key, val = m.group(1), (m.group(2) or "")
        val = val.rstrip()
        if not val:
            continue
        # the value has to end on its own line: the next line is another key, or the end
        if i + 1 < len(lines):
            nxt = lines[i + 1].rstrip("\r")
            if nxt.strip() and not KEY.match(nxt):
                continue                       # a continuation line — read it, don't guess
        if val.startswith("[") and val.endswith("]") and ";" in val:
            # a flow sequence whose items were separated with semicolons
            items = SEQ_ITEM.findall(val)
            if not items:
                continue
            fixed = "[" + ", ".join('"%s"' % t for t in items) + "]"
            if yaml.safe_load(fixed) != items:
                continue
            out[i] = "%s: %s%s" % (key, fixed, cr)
            seqs[key] = items
            continue
        if val.startswith(("'", '"', "[", "{", "|", ">", "#", "&", "*")):
            continue
        if ": " not in val and not val.endswith(":"):
            continue
        out[i] = "%s: %s%s" % (key, quote(val), cr)
        quoted[key] = val
    if not quoted and not seqs:
        return None, "nothing quotable"
    new = "\n".join(out)
    d = parses(new)
    if d is None:
        return None, "still unparseable after quoting"
    # every rewritten key must come back as exactly what was on the line
    for key, val in quoted.items():
        if d.get(key) != val:
            return None, "value changed by quoting: %s" % key
    for key, items in seqs.items():
        if d.get(key) != items:
            return None, "value changed by re-separating: %s" % key
    return new, sorted(list(quoted) + list(seqs))


def main():
    write = "--write" in sys.argv
    show = "--diff" in sys.argv
    fixed = refused = clean = 0
    reasons = {}
    roots = [a for a in sys.argv[1:] if not a.startswith("--")] or ["raw"]
    paths = []
    for root in roots:
        paths += glob.glob(os.path.join(ROOT, root, "**", "*.md"), recursive=True)
    for path in sorted(paths):
        raw = io.open(path, "rb").read()
        try:
            s = raw.decode("utf-8")
        except UnicodeDecodeError:
            continue
        m = FM.match(s)
        if not m:
            continue
        block = m.group(2)
        if parses(block) is not None:
            clean += 1
            continue
        new, why = repair(block)
        rel = os.path.relpath(path, ROOT).replace("\\", "/")
        if new is None:
            refused += 1
            reasons.setdefault(why, []).append(rel)
            continue
        fixed += 1
        if show:
            print("--- %s" % rel)
            for a, b in zip(block.split("\n"), new.split("\n")):
                if a != b:
                    print("  - %s\n  + %s" % (a[:120], b[:120]))
        if write:
            out = m.group(1) + new + m.group(3) + s[m.end():]
            io.open(path, "w", encoding="utf-8", newline="").write(out)
    print("%s: %d repaired, %d refused, %d already parse"
          % ("written" if write else "dry run", fixed, refused, clean))
    for why, files in sorted(reasons.items()):
        print("  refused (%s): %d" % (why, len(files)))
        for f in files:
            print("      %s" % f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
