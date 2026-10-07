#!/usr/bin/env python3
"""
prune-dated.py — standing. The dated-file rows of `PRUNE.md`'s retention register, run at
every night's close (`SWEEP-CYCLE.md`).

  15 days   every per-run record under `sweep/`, at any depth: manifest, drop-log, drops,
            tally, notes, row-health, batch, rows, monitor, qa, topic-decisions,
            region-unmapped — dated by the first YYYY-MM-DD in the name. 15 days is
            several times the longest read-back (drop-digest.py: one rotation). **Never a folder's newest manifest or drop-log**:
            `STATUS.md` reads those against `state.json` to spot a sweep that died between
            staging and state.
   3 days   the night's parent-to-slice handoffs: `sweep/ingest-lists-*/`,
            `sweep/phaseb-lists-*/`, and `sweep/_*-YYYY-MM-DD*` (briefs, lint scope). No
            pass reads them after the night that wrote them; 3 days covers a resumed night.

Never aged: `work-order-*.json` (a queue — `SWEEP-IATI.md` deletes it when its records are
built), undated per-country back-fill logs in `sweep/archive/`, and live state.

Any other file under `sweep/` with no date in its name and not on the live list is
reported as **unowned** and left alone: `PRUNE.md` says a file class with no owner is the
finding, not something to delete in passing.

Usage:  python scripts/prune-dated.py [--apply] [--today YYYY-MM-DD]
        (no --apply = report only; --sweep is accepted and ignored)
Exit:   0 always.
"""
import datetime
import os
import re
import shutil
import sys

RUN_DAYS = 15
HANDOFF_DAYS = 3
DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')
RUN_RECORD = re.compile(r'^(manifest|drop-log|drops|tally|notes|row-health|batch|rows|monitor|qa'
                        r'|topic-decisions|region-unmapped)-(\d{4}-\d{2}-\d{2})')
HANDOFF_DIR = re.compile(r'^(ingest-lists|phaseb-lists)-(\d{4}-\d{2}-\d{2})')
HANDOFF_FILE = re.compile(r'^_[a-z-]+-(\d{4}-\d{2}-\d{2})')
LIVE_NAMES = {"seen.csv", "state.json", "history.md", "README.md", ".gitkeep", "row-health.csv",
              "build-last-poll-ids.py", "iati-guidance.md", "last-poll-ids.txt"}
LIVE_DIRS = {os.path.join("sweep", "domains"), os.path.join("sweep", "archive")}


def date_of(s):
    return datetime.date.fromisoformat(s)


def main():
    argv = sys.argv[1:]
    apply_ = "--apply" in argv
    today = datetime.date.today()
    if "--today" in argv:
        today = date_of(argv[argv.index("--today") + 1])
    run_cut = today - datetime.timedelta(days=RUN_DAYS)
    hand_cut = today - datetime.timedelta(days=HANDOFF_DAYS)

    doomed_files, doomed_dirs, unowned = [], [], []
    for entry in sorted(os.listdir("sweep")):
        m = HANDOFF_DIR.match(entry)
        if m and os.path.isdir(os.path.join("sweep", entry)) and date_of(m.group(2)) < hand_cut:
            doomed_dirs.append(os.path.join("sweep", entry))

    for root, dirs, files in os.walk("sweep"):
        dirs[:] = [d for d in dirs if not (root == "sweep" and HANDOFF_DIR.match(d))]
        newest = {}
        for name in files:
            m = RUN_RECORD.match(name)
            if m and m.group(1) in ("manifest", "drop-log"):
                newest[m.group(1)] = max(newest.get(m.group(1), (m.group(2), name)), (m.group(2), name))
        keep = {v[1] for v in newest.values()}
        for name in sorted(files):
            path = os.path.join(root, name)
            m = RUN_RECORD.match(name)
            h = HANDOFF_FILE.match(name) if root == "sweep" else None
            if m:
                if name not in keep and date_of(m.group(2)) < run_cut:
                    doomed_files.append(path)
            elif h:
                if date_of(h.group(1)) < hand_cut:
                    doomed_files.append(path)
            elif name.startswith("work-order-") or name in LIVE_NAMES or root in LIVE_DIRS:
                continue
            elif not DATE.search(name):
                unowned.append(path)

    print(f"prune sweep: {len(doomed_files)} run records older than {run_cut} / handoffs older than {hand_cut};"
          f" {len(doomed_dirs)} handoff folders; {len(unowned)} unowned")
    for p in doomed_dirs + doomed_files:
        print("   ", p)
        if apply_:
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    for p in unowned:
        print("    unowned:", p)
    if not apply_:
        print("(report only - pass --apply to act)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
