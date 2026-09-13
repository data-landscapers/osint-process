#!/usr/bin/env python3
"""Repair line-ending flips against HEAD, preserving each file's own mixture.

`assert-containment.py` refuses a stage when a path's diff is mostly line-ending
noise, because a 958-line diff hiding 2 real changes is unreviewable. The usual
cause is a sub-agent rewriting a CRLF file with LF. Normalising the whole file to
one terminator does NOT fix it: several files here carry a genuine mixture at HEAD
(`sweep/off-list/seen.csv` had 488 CRLF lines and 12 LF-only), so a uniform rewrite
just trades one spurious diff for another.

This aligns the working file against HEAD line by line and gives every UNCHANGED
line back the terminator HEAD gave it; genuinely new lines take the file's own
dominant terminator. What survives in the diff is the real change and nothing else.

    python scripts/repair-eol.py <path> [<path> ...]
    python scripts/repair-eol.py --stage lint      # every path assert-containment flagged

Written 2026-08-25, after three separate stages of one sweep cycle each needed the
same repair by hand.
"""
import difflib
import subprocess
import sys


def logical(d):
    """[(text, terminator)] for each line; terminator is b'\r\n', b'\n' or b''."""
    out, i = [], 0
    while i < len(d):
        j = d.find(b"\n", i)
        if j == -1:
            out.append((d[i:], b""))
            break
        line = d[i:j]
        if line.endswith(b"\r"):
            out.append((line[:-1], b"\r\n"))
        else:
            out.append((line, b"\n"))
        i = j + 1
    return out


def repair(path):
    head = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True)
    if head.returncode != 0:
        return None                      # untracked: nothing to align against
    h, w = logical(head.stdout), logical(open(path, "rb").read())
    crlf = sum(1 for _, e in h if e == b"\r\n")
    dominant = b"\r\n" if crlf >= len(h) - crlf else b"\n"
    sm = difflib.SequenceMatcher(None, [t for t, _ in h], [t for t, _ in w],
                                 autojunk=False)
    out = bytearray()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                out += h[i1 + k][0] + h[i1 + k][1]      # HEAD's own terminator
        elif tag in ("replace", "insert"):
            for k in range(j1, j2):
                out += w[k][0] + (dominant if w[k][1] else b"")
        # 'delete' emits nothing
    before = open(path, "rb").read()
    if bytes(out) == before:
        return False
    open(path, "wb").write(out)
    return True


def flagged(stage):
    """Paths assert-containment reports as line-ending-only for this stage."""
    r = subprocess.run([sys.executable, "scripts/assert-containment.py", "--stage", stage],
                       capture_output=True, text=True)
    paths = []
    for ln in (r.stdout + r.stderr).splitlines():
        if "line-ending" in ln or "changed lines" in ln:
            tok = ln.strip().split()
            if tok and ("/" in tok[0] or "\\" in tok[0]):
                paths.append(tok[0])
    return paths


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("--help", "-h"):
        print(__doc__)
        return 0
    if args[0] == "--stage":
        if len(args) < 2:
            print("repair-eol: --stage needs a stage name", file=sys.stderr)
            return 2
        targets = flagged(args[1])
        if not targets:
            print("repair-eol: nothing flagged for stage %s" % args[1])
            return 0
    else:
        targets = args
    fixed = skipped = 0
    for p in targets:
        r = repair(p)
        if r is None:
            print("  untracked, skipped: %s" % p)
            skipped += 1
        elif r:
            print("  repaired: %s" % p)
            fixed += 1
        else:
            print("  already clean: %s" % p)
    print("repair-eol: %d repaired, %d skipped" % (fixed, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
