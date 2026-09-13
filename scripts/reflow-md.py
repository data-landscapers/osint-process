#!/usr/bin/env python3
"""reflow-md.py — one line per paragraph, no manual wrapping.

The house rule (Bill, 2026-08-03): hard-wrapped paragraphs are hard to read, and a
paragraph broken across eight lines also diffs badly — change one word near the start
and every following line shifts, so `git diff` shows a rewritten paragraph instead of a
changed word. One line per paragraph fixes both.

What it joins: ordinary paragraphs, list items (a wrapped continuation folds back into
its item), and blockquote bodies (the `>` prefix is preserved).

What it never touches, because the line break is meaningful there:
  - YAML frontmatter
  - fenced code blocks (``` and ~~~) and indented code blocks
  - tables (any line starting `|`)
  - headings, horizontal rules, and reference-style link definitions
  - a standalone HTML comment: `<!-- narrative: key -->` and its closer delimit the
    model-owned block in a compiled hub or report, and a marker joined onto the prose
    below it stops matching
  - a line ending in two spaces — that is markdown's explicit hard break
  - `raw/` is refused outright: those bodies are verbatim captures of someone else's
    published text and `raw/` is immutable (CLAUDE.md -> Structure). Reflowing one
    would rewrite the evidence.
  - a handful of `logs/` append-only ledgers are refused outright too, for a different
    reason: one line *is* one record there (STATUS.md's log.md entry form; INGEST.md
    step 11's pending-write; job 83's url-log disposition; a phaseb-batches queued
    row), with no blank line between consecutive records. This tool absorbs any run
    of non-blank lines into one paragraph, so run over a boundary-sensitive ledger it
    does the opposite of the house rule: it fuses many records onto one line instead
    of keeping one line per record (found 2026-09-07, housekeeping 75 — logs/log.md
    had exactly this fusion at HEAD, 1,566 entries collapsed into a few dozen lines).
    Named here rather than left to a blank-line heuristic, so a new ledger is an
    addition someone makes on purpose: `logs/log.md`, `logs/sweep-url_log.md`,
    `logs/ingest-pending-writes.md`, `logs/phaseb-batches/batch-*.md`.

Usage:
    python scripts/reflow-md.py CLAUDE.md              # in place
    python scripts/reflow-md.py --check wiki/**/*.md   # report only, exit 1 if any wrap
    python scripts/reflow-md.py --dry-run FILE         # show what would change
"""
import argparse, os, re, sys

FENCE = re.compile(r'^\s{0,3}(```|~~~)')
TABLE = re.compile(r'^\s*\|')
HEADING = re.compile(r'^\s{0,3}#{1,6}\s')
HRULE = re.compile(r'^\s{0,3}([-*_])(\s*\1){2,}\s*$')
LISTITEM = re.compile(r'^(\s*)([-*+]|\d+[.)])\s+')
QUOTE = re.compile(r'^(\s*>+\s?)')
LINKDEF = re.compile(r'^\s{0,3}\[[^\]]+\]:\s')
# A standalone HTML comment is a marker, not prose. HUB-COMPILE.md and the report layer
# both delimit script-owned and model-owned text with `<!-- narrative: key -->` on its own
# line, and joining one onto the paragraph below it silently breaks the marker.
COMMENT = re.compile(r'^\s*<!--.*-->\s*$')
INDENTED_CODE = re.compile(r'^(\t| {4,})\S')

# Boundary-sensitive append-only ledgers: one line is one record, never a wrapped
# paragraph. See the module docstring's "never touches" list for why these are named
# rather than left to a blank-line heuristic.
LEDGERS = {"logs/log.md", "logs/sweep-url_log.md", "logs/ingest-pending-writes.md"}
LEDGER_DIR = re.compile(r'(^|/)logs/phaseb-batches/batch-[^/]*\.md$')


def is_ledger(norm):
    return norm in LEDGERS or bool(LEDGER_DIR.search(norm))


def join(parts):
    """Join a wrapped paragraph back into one line.

    A word hyphenated across the break — "pending-" then "decision register" — must close
    up, not gain a space. Only when a letter precedes the hyphen and a lowercase letter
    follows it, so an em-dash, a numeric range or a trailing list dash is untouched."""
    out = parts[0].rstrip()
    for nxt in parts[1:]:
        if re.search(r'[A-Za-z]-$', out) and re.match(r'[a-z]', nxt):
            out += nxt.rstrip()
        else:
            out += " " + nxt.rstrip()
    return out.rstrip()


def reflow(text, eol):
    lines = text.split(eol) if eol in text else text.split("\n")
    out, i, n = [], 0, len(lines)

    # frontmatter passes through untouched
    if lines and lines[0].strip() == "---":
        out.append(lines[0])
        i = 1
        while i < n and lines[i].strip() != "---":
            out.append(lines[i]); i += 1
        if i < n:
            out.append(lines[i]); i += 1

    in_fence = None
    while i < n:
        ln = lines[i]
        if in_fence:
            out.append(ln)
            if FENCE.match(ln):
                in_fence = None
            i += 1
            continue
        m = FENCE.match(ln)
        if m:
            in_fence = m.group(1)
            out.append(ln); i += 1
            continue
        if (not ln.strip() or TABLE.match(ln) or HEADING.match(ln) or HRULE.match(ln)
                or LINKDEF.match(ln) or INDENTED_CODE.match(ln) or COMMENT.match(ln)):
            out.append(ln); i += 1
            continue

        # a paragraph / list item / quote: absorb continuation lines
        buf = [ln.rstrip()]
        is_list = bool(LISTITEM.match(ln))
        qpref = QUOTE.match(ln).group(1) if QUOTE.match(ln) else ""
        i += 1
        while i < n:
            nxt = lines[i]
            if not nxt.strip() or TABLE.match(nxt) or HEADING.match(nxt) or HRULE.match(nxt):
                break
            if COMMENT.match(nxt):              # a marker line, not a continuation
                break
            if FENCE.match(nxt) or LINKDEF.match(nxt):
                break
            if buf[-1].endswith("  "):          # explicit hard break — respect it
                break
            if LISTITEM.match(nxt):             # the next item, not a continuation
                break
            if qpref and not QUOTE.match(nxt):
                break
            if not qpref and QUOTE.match(nxt):
                break
            if not is_list and not qpref and INDENTED_CODE.match(nxt):
                break
            cont = nxt.strip()
            if qpref:
                cont = QUOTE.sub("", nxt).strip()
            buf.append(cont)
            i += 1
        out.append(join(buf))
    return (eol if eol else "\n").join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if any file would change")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    changed = []
    for p in a.paths:
        norm = os.path.normpath(p).replace("\\", "/")
        if norm.startswith("raw/") or "/raw/" in norm:
            print("refused (raw/ is immutable and verbatim): %s" % p, file=sys.stderr)
            continue
        if is_ledger(norm):
            print("refused (append-only ledger, one line is one record): %s" % p, file=sys.stderr)
            continue
        if not p.endswith(".md") or not os.path.isfile(p):
            continue
        b = open(p, "rb").read()
        eol = "\r\n" if b"\r\n" in b else "\n"
        t = b.decode("utf-8")
        new = reflow(t, eol)
        if new != t:
            changed.append(p)
            if not (a.check or a.dry_run):
                open(p, "wb").write(new.encode("utf-8"))
            if a.dry_run:
                before = sum(1 for _ in t.splitlines())
                after = sum(1 for _ in new.splitlines())
                print("%s: %d -> %d lines" % (p, before, after))

    if a.check:
        for p in changed:
            print("hard-wrapped: %s" % p)
        print("%d of %d file(s) carry manual wrapping." % (len(changed), len(a.paths)))
        return 1 if changed else 0
    print("%s %d file(s)." % ("would reflow" if a.dry_run else "reflowed", len(changed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
