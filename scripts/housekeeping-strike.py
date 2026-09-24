#!/usr/bin/env python3
"""housekeeping-strike.py — standing. Strike a job from `X:\\housekeeping-jobs.md`.

Written 2026-09-24 for housekeeping jobs 190-202. Does `BACKLOG.md` §5's strike
in one move: removes entry N and its *Rough sizing* row from the register, and
appends `xN. *(cleared YYYY-MM-DD)* <entry text> <closing text>` to
`X:\\housekeeping-jobs-resolved.md`. Writes the share only; commits nothing.

usage: python scripts/housekeeping-strike.py <N> <closing-text-file> [--date YYYY-MM-DD]
Exit 2 if entry N or its sizing row is not found exactly once.
"""
import argparse
import datetime
import pathlib
import sys

REG = pathlib.Path("X:/housekeeping-jobs.md")
RES = pathlib.Path("X:/housekeeping-jobs-resolved.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n")
    ap.add_argument("closing_file")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    closing = pathlib.Path(a.closing_file).read_text(encoding="utf-8").strip()
    lines = REG.read_text(encoding="utf-8").split("\n")
    idx = [i for i, l in enumerate(lines) if l.startswith(f"{a.n}. ")]
    rows = [i for i, l in enumerate(lines) if l.startswith(f"| {a.n} |")]
    if len(idx) != 1 or len(rows) != 1:
        print(f"housekeeping-strike: job {a.n} found {len(idx)} time(s), sizing row {len(rows)} time(s) — expected once each")
        return 2
    entry = lines[idx[0]]
    drop = {idx[0], rows[0]}
    if idx[0] + 1 < len(lines) and lines[idx[0] + 1] == "":
        drop.add(idx[0] + 1)
    REG.write_text("\n".join(l for i, l in enumerate(lines) if i not in drop), encoding="utf-8", newline="")
    struck = f"x{a.n}. *(cleared {a.date})* {entry[len(a.n) + 2:]} {closing}"
    RES.write_text(RES.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + struck + "\n", encoding="utf-8", newline="")
    print("struck", a.n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
