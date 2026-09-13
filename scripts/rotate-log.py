#!/usr/bin/env python3
"""
rotate-log.py — standing. Mechanical truncation of `logs/log.md` at every cycle close.

`logs/log.md` is CC's own recall, newest first, and it has no reader who scrolls to the
bottom. Prose caps on entry length were tried and broke inside a week (852 KB -> 1.41 MB in
seven days), so the limit is here instead: keep the newest ~400 lines, drop the rest, and
let git hold the history. Nothing to remember and nothing to enforce by hand.

The file's header block (everything above the first entry) is always kept. The cut is made
at an **entry boundary**, never inside one, so the tail is never a half-entry: the script
keeps entries until the budget is reached and then stops. Two entry forms are recognised —
the one-line form `YYYY-MM-DD HH:MM · pass · …` (STATUS.md, from 2026-08-10) and the older
`## YYYY-MM-DD HH:MM …` heading with a body beneath it.

Usage:
  python scripts/rotate-log.py                report what it would drop
  python scripts/rotate-log.py --apply        do it
  python scripts/rotate-log.py --keep 600     a different budget (default 400 lines)

Called by `SWEEP-CYCLE.md` at the close of the night. Exit 0 always — a log that is already
short is the normal case, not a failure.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = os.path.join(V.ROOT, "logs", "log.md")
KEEP_DEFAULT = 400

# An entry starts on either form. Anchored at the left margin so a quoted example
# inside an entry body cannot open a phantom entry.
ENTRY_RE = re.compile(r"^(?:## )?\d{4}-\d{2}-\d{2} \d{2}:\d{2}\b")


def entry_starts(lines):
    return [i for i, ln in enumerate(lines) if ENTRY_RE.match(ln)]


def rotate(lines, keep):
    """Return (kept_lines, n_entries_kept, n_entries_dropped).

    Keeps the header plus whole entries, newest first, until `keep` body lines are
    used. Always keeps at least one entry — a single very long entry is not a reason
    to return a file with no content in it.
    """
    starts = entry_starts(lines)
    if not starts:
        return lines, 0, 0
    header = lines[:starts[0]]
    bounds = starts + [len(lines)]
    used, kept_entries = 0, 0
    for n, (a, b) in enumerate(zip(bounds, bounds[1:])):
        size = b - a
        if kept_entries and used + size > keep:
            break
        used += size
        kept_entries += 1
    cut = bounds[kept_entries]
    return header + lines[starts[0]:cut], kept_entries, len(starts) - kept_entries


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--apply", action="store_true", help="write the truncated file")
    ap.add_argument("--keep", type=int, default=KEEP_DEFAULT,
                    help=f"body lines to keep (default {KEEP_DEFAULT})")
    a = ap.parse_args()

    if not os.path.exists(LOG):
        print("logs/log.md: not present — nothing to rotate.")
        return 0

    # newline="" keeps whatever line endings the file already has; this repo is mixed
    # CRLF/LF and a rewrite must not convert them.
    with open(LOG, encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)

    kept, n_kept, n_dropped = rotate(lines, a.keep)
    before_kb = sum(len(l.encode("utf-8")) for l in lines) / 1024
    after_kb = sum(len(l.encode("utf-8")) for l in kept) / 1024

    if n_dropped == 0:
        print(f"logs/log.md: {len(lines):,} lines, {n_kept} entries, {before_kb:,.0f} KB "
              f"— inside the {a.keep}-line budget, nothing dropped.")
        return 0

    print(f"logs/log.md: {len(lines):,} -> {len(kept):,} lines "
          f"({before_kb:,.0f} -> {after_kb:,.0f} KB); "
          f"{n_kept} entries kept, {n_dropped} dropped (git holds them).")
    if not a.apply:
        print("  report only — rerun with --apply.")
        return 0

    with open(LOG, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(kept))
    print("  applied.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
