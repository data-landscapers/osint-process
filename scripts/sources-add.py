#!/usr/bin/env python3
"""sources-add.py — standing. Add source slugs to a wiki page's `sources:` line, as text.

Phase B slices kept rebuilding `sources:` by parsing the frontmatter as YAML and writing it
back, and an old-style entry whose title carries a comma (`[2026-01-11 The Year of the
Teeth Data Protection in Africa Roundup, 2025, Projections for 2026]`) split into two at
the comma — five pages on 2026-09-30, gov.protect on 2026-10-02. This edits the one line as
text: it appends `, [slug]` before the closing bracket, never re-reads the existing entries,
and touches no other byte, so the dominant line ending and every other key come back as
they were.

    python scripts/sources-add.py wiki/concepts/gov.protect.md 2026-10-02-foo 2026-10-02-bar

A slug already on the line is skipped (idempotent). A page with no `sources:` key gets one
at the end of its frontmatter. Exit 1 on a page with no frontmatter.
"""
import re
import sys


def add(path, slugs):
    raw = open(path, "rb").read().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", raw, re.S)
    if not m:
        sys.exit(f"sources-add: {path} has no frontmatter")
    fm_start, fm_end = m.start(1), m.end(1)
    fm = raw[fm_start:fm_end]
    line = re.search(r"^sources:[ \t]*(.*?)[ \t\r]*$", fm, re.M)
    if line:
        held = line.group(1)
        new = [s for s in slugs if f"[{s}]" not in held]
        if not new:
            return 0
        inner = held[1:-1].strip() if held.startswith("[") and held.endswith("]") else held.strip()
        joined = ", ".join(f"[{s}]" for s in new)
        value = f"[{inner}, {joined}]" if inner else f"[{joined}]"
        fm = fm[:line.start(1)] + value + fm[line.end(1):]
    else:
        new = list(dict.fromkeys(slugs))
        fm = fm + eol + "sources: [" + ", ".join(f"[{s}]" for s in new) + "]"
    out = raw[:fm_start] + fm + raw[fm_end:]
    open(path, "wb").write(out.encode("utf-8"))
    return len(new)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__.split("\n\n")[2])
    n = add(sys.argv[1], [s.strip().strip("[]") for s in sys.argv[2:] if s.strip()])
    print(f"sources-add: {n} added to {sys.argv[1]}")
