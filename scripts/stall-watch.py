#!/usr/bin/env python
"""stall-watch.py - the sweep cycle's watchdog.

The parent is woken by a sub-agent *completing*. A sub-agent that hangs completes
nothing, so no notification is ever raised, the parent is never re-invoked, and the
night sits silent until a human types something. That is not a slow night; it is a
stopped one, and on Bill's screen a stopped run is indistinguishable from a question.

Measured 2026-08-27: ingest slice 03 hung on its first tool call and sat for ~5 hours
with its ten items untouched in `new/`. Nine siblings finished normally. Nothing
detected it.

This script is the missing wake signal. It is run under the `Monitor` tool, whose
stdout lines become notifications that re-invoke the parent, so a line printed here
is a parent that wakes up and looks.

**It keys on work, not on transcripts.** The obvious signal - the sub-agent transcript
file - does not work: on the 08-27 run nearly every `.output` file was 0 bytes
*whatever the outcome*, the successful `SWEEP-DAILY-LIST` included, and none of that
night's agents wrote a `subagents/agent-*.jsonl` at all. A watchdog reading either
would have stayed silent through the stall. What a working agent always does is touch
files: a sweep writes `new/` and its `sweep/` manifests, an ingest slice empties `new/`
and fills `raw/`, everything writes `logs/`. So the signal is the newest mtime across
the working set, and total silence across all of it is the anomaly.

Deliberately dumb: it says "nothing has moved for N minutes", never which agent or why.
Diagnosis belongs to the parent once it is awake - it can see which spawns are still
outstanding and which slice's items are still staged, which this script cannot.

Usage, armed once at Step 0 alongside the Exa canary and left running all night:

    python scripts/stall-watch.py --quiet-minutes 25

Exits 0 on --max-minutes. Prints one line per stall, then backs off, so a genuinely
long stall wakes the parent repeatedly without becoming a firehose.
"""

import argparse
import os
import sys
import time

# Watched because every agent in the cycle touches at least one of them. `raw/` is
# scoped to the current year - the rest of it is immutable and cannot move.
WATCHED = ["new", "logs", "sweep", "reviews", "wiki", "raw/%d" % time.gmtime().tm_year]

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".claude"}


def newest_mtime(root):
    """Max mtime under the watched paths. Returns (mtime, path) or (0.0, None)."""
    best, best_path = 0.0, None
    stack = [os.path.join(root, w) for w in WATCHED]
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d) as it:
                for e in it:
                    try:
                        if e.is_dir(follow_symlinks=False):
                            if e.name not in SKIP_DIRS:
                                stack.append(e.path)
                            continue
                        m = e.stat(follow_symlinks=False).st_mtime
                        if m > best:
                            best, best_path = m, e.path
                    except OSError:
                        continue
        except (FileNotFoundError, NotADirectoryError, PermissionError):
            continue
    return best, best_path


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root (default: cwd)")
    ap.add_argument("--quiet-minutes", type=float, default=25.0,
                    help="minutes of total silence across the working set before "
                         "the first stall line (default 25)")
    ap.add_argument("--repeat-minutes", type=float, default=30.0,
                    help="minutes between repeat stall lines while still quiet "
                         "(default 30)")
    ap.add_argument("--poll-seconds", type=float, default=60.0,
                    help="seconds between checks (default 60)")
    ap.add_argument("--max-minutes", type=float, default=0.0,
                    help="exit after this long; 0 means run until stopped")
    ap.add_argument("--once", action="store_true",
                    help="check once, print a stall line if quiet, and exit")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    started = time.time()
    last_emit = 0.0

    while True:
        mt, path = newest_mtime(root)
        now = time.time()

        if mt == 0.0:
            # Nothing readable at all - that is itself worth waking for, once.
            if now - last_emit >= args.repeat_minutes * 60:
                print("STALL watched paths unreadable under %s - check the tree" % root,
                      flush=True)
                last_emit = now
        else:
            quiet_min = (now - mt) / 60.0
            if quiet_min >= args.quiet_minutes:
                due = last_emit == 0.0 or (now - last_emit) >= args.repeat_minutes * 60
                if due:
                    print("STALL nothing written for %d min across new/ logs/ sweep/ "
                          "reviews/ wiki/ raw/ - newest is %s - a spawn is probably "
                          "hung; check which items are still staged"
                          % (int(quiet_min), os.path.relpath(path, root)), flush=True)
                    last_emit = now
            else:
                last_emit = 0.0  # tree moved again; re-arm the first-stall line

        if args.once:
            return 0
        if args.max_minutes and (now - started) >= args.max_minutes * 60:
            return 0
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    sys.exit(main())
