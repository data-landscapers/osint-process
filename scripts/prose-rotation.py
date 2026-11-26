#!/usr/bin/env python3
r"""
prose-rotation.py — pick tonight's intersection pages for the prose rotation, and record each one done.

**Why it exists** *(strategic review 8 R191, 2026-11-26)*. Phase B writes to `X:\documentation\prose-style.md` (R149), but only on the pages a night's sources land on. 8,300 of 11,810 wiki blocks still failed the sheet on 2026-11-26, and nothing else rewrote them. The rotation takes ten intersection pages a night through a whole-page rewrite to the sheet and under the line: the 333 over-line pages clear in about five weeks, all 2,064 intersections in about seven months. The driver is `wiki/prose-rotation.md`.

**The order.** Over-line pages first, the least over first, since cutting a 13,000-word page to its line in one sitting is the riskiest rewrite and is better met last; then the rest, never-rotated before oldest-rotated. A page rotated in the last `RECENT_DAYS` goes to the back whatever its length, so one that stays over after a rewrite cannot take the slot every night. The measure is lint #8's own, through `page-length.py`, so the picker and the lint agree about which pages are over.

**The record** is `logs/prose-rotation.csv`, `date,page,before,after`, one row a rewrite, appended by `--done` and never edited. The last row for a page is its rotation date.

Usage:
  python scripts/prose-rotation.py --pick 10              tonight's pages, one path a line
  python scripts/prose-rotation.py --done PAGE --before N records a rewrite; exit 2 if it grew,
                                                          3 if it dropped the wiki's last citation of a slug
  python scripts/prose-rotation.py --status               pages over the line, rotated, never rotated

The stand-down is the caller's: `usage-log.py --opened-above 70 && …` (`SWEEP-CYCLE.md`), the same test the maturity-study pulls use.
"""
import argparse
import csv
import datetime as dt
import glob
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vault_lib as V                                                # noqa: E402

spec = importlib.util.spec_from_file_location("page_length", os.path.join(HERE, "page-length.py"))
PL = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PL)

LOG = os.path.join(V.ROOT, "logs", "prose-rotation.csv")
PAGES = os.path.join(V.ROOT, "wiki", "intersections", "*.md")
RECENT_DAYS = 30
LINE = 2500


def last_rotated():
    """{page: date} from the record, the last row winning."""
    seen = {}
    try:
        with open(LOG, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                seen[r["page"]] = r["date"]
    except OSError:
        pass
    return seen


def candidates(today=None):
    today = today or dt.date.today()
    cutoff = (today - dt.timedelta(days=RECENT_DAYS)).isoformat()
    seen = last_rotated()
    rows = []
    for path in glob.glob(PAGES):
        rel, m = PL.measure(path)
        if not m:
            continue
        when = seen.get(rel)
        recent = bool(when and when > cutoff)
        rows.append((recent, not m["over"], m["effective"] if m["over"] else 0, when or "", rel, m))
    rows.sort(key=lambda r: r[:5])
    return rows


LINK = re.compile(r"\[\[([^\]|#]+)")


def orphaned(rel):
    """Slugs the committed page cited and the rewrite does not, that no other wiki page cites either: a rewrite may move a citation, never lose the wiki's last one."""
    try:
        old = subprocess.run(["git", "-C", V.ROOT, "show", f"HEAD:{rel}"], capture_output=True,
                             text=True, encoding="utf-8", errors="replace").stdout
        new = open(os.path.join(V.ROOT, rel), encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    gone = set(LINK.findall(old)) - set(LINK.findall(new))
    if not gone:
        return []
    for path in glob.glob(os.path.join(V.ROOT, "wiki", "**", "*.md"), recursive=True):
        if os.path.relpath(path, V.ROOT).replace(os.sep, "/") == rel:
            continue
        try:
            gone -= set(LINK.findall(open(path, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
        if not gone:
            break
    return sorted(gone)


def record(rel, before, after):
    new = not os.path.exists(LOG)
    with open(LOG, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(["date", "page", "before", "after"])
        w.writerow([dt.date.today().isoformat(), rel, before, after])


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--pick", type=int, metavar="N", help="list tonight's N pages")
    ap.add_argument("--done", metavar="PAGE", help="record a finished rewrite of PAGE")
    ap.add_argument("--before", type=int, help="with --done: the page's effective words before the rewrite")
    ap.add_argument("--status", action="store_true", help="counts: over the line, rotated, never rotated")
    a = ap.parse_args()
    if a.pick:
        for r in candidates()[:a.pick]:
            print(r[4])
        return 0
    if a.done:
        if a.before is None:
            ap.error("--done needs --before, measured with page-length.py before the rewrite")
        rel, m = PL.measure(a.done)
        after = m["effective"]
        if after > a.before:
            print(f"prose-rotation: {rel} GREW {a.before:,} → {after:,} words; redo once, else revert")
            return 2
        lost = orphaned(rel)
        if lost:
            print(f"prose-rotation: {rel} dropped the wiki's last citation of {', '.join(lost)}; put it back or revert")
            return 3
        record(rel, a.before, after)
        state = "OVER" if m["over"] else "under"
        print(f"prose-rotation: {rel} {a.before:,} → {after:,} words, {state}")
        return 0
    if a.status:
        rows = candidates()
        over = sum(1 for r in rows if r[5]["over"])
        done = len(last_rotated())
        print(f"prose-rotation: {len(rows):,} pages · {over:,} over the line · {done:,} rotated · {len(rows) - done:,} never")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
