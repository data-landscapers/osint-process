#!/usr/bin/env python3
"""lint-pdftotext-enc.py -- LINT #31, surface-only.

`pdftotext` emits **Latin-1 by default** on this toolchain. Read as UTF-8, every
accented character becomes a replacement character: `donnees` with an accent stops
matching a grep for itself, and a cross-vote keyword scan returns a clean zero it has
not earned. Nothing warns you -- the run reads as successful and the finding is simply
absent.

It has bitten twice. The CAF FY2025 volume was recorded as containing the term zero
times when it contains it twelve (2026-07-26), and an OCR splice carried 107 mangled
characters into a `raw/` sidecar (2026-08-21, housekeeping job 31). Both times the fix
was written into `documentation/` and never reached the procedure files a run actually
follows, which is why this is a check and not a third note.

**What counts as a finding: a command, not a name.** A backticked span is an invocation
if, after `pdftotext` and its flags, something is left -- a file, `-`, a pipe, a redirect.
`pdftotext -layout <f> -` and `pdftotext | wc -c` are invocations. A span that is only
`pdftotext -layout` is the name of a behaviour ("`pdftotext -layout` drifts amounts by
four rows"), which is prose; the standing rule in `BUDGET-EXTRACT.md` section 1 covers
those. Python `subprocess` argument lists are checked as invocations always.

`raw/`, `sweep/`, `logs/`, `reviews/` and `wiki/` are never read: those record what was
run, not what to run, and `raw/` is immutable besides.

Usage:  python scripts/lint-pdftotext-enc.py [--list]
Exit 0 clean, 1 on any finding.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP = {".git", "raw", "sweep", "logs", "reviews", "wiki", "new", "new-budget",
        "budget-archive", "outputs", "scratchpad", "__pycache__", "archive"}

SPAN = re.compile(r"`([^`\n]+)`")
CALL = re.compile(r"""\[\s*["']pdftotext["'][^\]]*\]""")
# Flags that take a value, so the value is not mistaken for a file argument.
VALUED = {"-f", "-l", "-enc", "-opw", "-upw", "-cfg", "-r"}


def is_invocation(span):
    """A backticked pdftotext span with an argument, pipe or redirect left after its flags."""
    toks = span.split()
    if not toks or toks[0] != "pdftotext":
        return False, False
    rest, skip = [], False
    for t in toks[1:]:
        if skip:
            skip = False
            continue
        if t in VALUED:
            skip = True
            continue
        if t.startswith("-") and len(t) > 1 and not t == "-":
            continue
        rest.append(t)
    return bool(rest), "-enc" in toks


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="print every finding")
    args = ap.parse_args()

    me = pathlib.Path(__file__).name
    findings = []
    for path in sorted(ROOT.rglob("*")):
        if path.is_dir() or path.suffix not in (".md", ".py", ".sh") or path.name == me:
            continue
        if any(p in SKIP for p in path.relative_to(ROOT).parts[:-1]):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(ROOT).as_posix()
        for n, line in enumerate(text.split("\n"), 1):
            for span in SPAN.findall(line):
                cmd, enc = is_invocation(span)
                if cmd and not enc:
                    findings.append((rel, n, span))
            for call in CALL.findall(line):
                if "-enc" not in call:
                    findings.append((rel, n, call))

    if not findings:
        print("#31 pdftotext -enc UTF-8 -- 0 finding(s)")
        return 0
    print(f"#31 pdftotext -enc UTF-8 -- {len(findings)} invocation(s) missing the flag")
    for f, n, hit in (findings if args.list else findings[:20]):
        print(f"  {f}:{n}  {hit[:100]}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
