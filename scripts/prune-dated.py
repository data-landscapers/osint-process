#!/usr/bin/env python3
"""
prune-dated.py — standing. The dated-file row of `PRUNE.md`'s retention register.

It was *unowned* until 2026-08-03 (strategic review task 23), and it is the kind of rule
nobody can execute by eye.

  --sweep   `sweep/*/manifest-YYYY-MM-DD*.md` and `drop-log-YYYY-MM-DD*.csv`: deleted 60
            days after the date in the name — `seen.csv`'s horizon, because past it the
            drop can no longer be re-tested against the record it explains. **Never a
            folder's newest of either**: `STATUS.md` reads those two against
            `state.json` to spot a sweep that died between staging and state.

Undated per-country logs (`sweep/archive/drop-log-{ISO3}.csv`) are a completed back-fill's
record, not a run's, and are out of scope.

`logs/log.md` was this script's other job until 2026-08-10 (token review task 2). It is
now `scripts/rotate-log.py`, run at every cycle close on a flat line budget — which makes
the monthly horizon and the two shape assertions redundant, so they were deleted rather
than kept as a second, slower answer.

Usage:  python scripts/prune-dated.py [--sweep] [--apply] [--today YYYY-MM-DD]
        (no --apply = report only)
Exit:   0 always.
"""
import datetime
import glob
import os
import re
import sys

SWEEP_DAYS = 60         # matches sweep/*/seen.csv
DATED = re.compile(r'^(manifest|drop-log)-(\d{4}-\d{2}-\d{2})[a-z]?\.(md|csv)$')


def prune_sweep(today, apply_):
    cutoff = today - datetime.timedelta(days=SWEEP_DAYS)
    doomed = []
    for folder in sorted(glob.glob("sweep/*/")):
        dated = {"manifest": [], "drop-log": []}
        for name in os.listdir(folder):
            m = DATED.match(name)
            if m:
                dated[m.group(1)].append((m.group(2), name))
        for kind, files in dated.items():
            if not files:
                continue
            newest = max(files)[1]          # never the folder's newest of either kind
            for d, name in sorted(files):
                if name != newest and datetime.date.fromisoformat(d) < cutoff:
                    doomed.append(os.path.join(folder, name))

    print(f"prune sweep: {len(doomed)} dated manifests/drop-logs older than {cutoff}")
    for p in doomed:
        print("   ", p)
        if apply_:
            os.remove(p)
    if apply_ and doomed:
        print(f"   deleted: {len(doomed)}")
    return 0


def main():
    argv = sys.argv[1:]
    apply_ = "--apply" in argv
    today = datetime.date.today()
    if "--today" in argv:
        today = datetime.date.fromisoformat(argv[argv.index("--today") + 1])
    rc = prune_sweep(today, apply_)
    if not apply_:
        print("(report only - pass --apply to act)")
    return rc


if __name__ == "__main__":
    sys.exit(main())
