#!/usr/bin/env python3
r"""poll-loop.py — the nightly trigger: open a Claude session on the sweep cycle from 20:00.

*(Bill, 2026-10-30.)* Replaces typing "run the sweep cycle" by hand, on the pattern of CORPUS's
own poll loop. It runs in the `OSINT-POLL` terminal tab, which starts it, and checks every five
minutes. **A check costs no model turn**: it reads `logs/sweep-cycle_log.md`, and the cycle
itself runs in a new tab as an interactive session, so Bill can watch or step in.

**The cycle may open any time from `START` to `STOP`**, across midnight, so a machine asleep at
20:00 or a tab opened at 20:40 still runs the night. After `STOP` the night is skipped: a cycle
takes three to four hours, and one opened later would close after CORPUS's poll stops at 06:00.

A night runs from noon to noon, so a cycle opened at 00:30 belongs to the evening before. The
loop never opens a second cycle in one night: it stands down when a row's `Start` or `New-Start`
falls in tonight (a night already run, by hand or otherwise, or one in progress), and when its
own claim file says it opened one tonight. A `New-Start` from an earlier night is an interrupted
run, and the cycle resumes it, so that one fires. A launch that fails writes no claim and is
tried again at the next check.

**A night's hours can be moved** *(Bill, 2026-11-03)*: a row in `lookups/poll-window.csv`
(`night`, the date the evening falls on; `start`; `stop`; `reason`) replaces `START`-`STOP` for
that night only, and a night with no row keeps the default. The file is read at every check and
every pause, so an edit needs no restart of a loop running this version. CORPUS's poll has the
same file in its own `lookups/`.

Only the trigger checks a clock; the cycle still never does (`SWEEP-CYCLE.md`).

Usage:  python scripts/poll-loop.py               # in the OSINT-POLL tab
        python scripts/poll-loop.py --now         # one check now, ignoring the window, then stop
        python scripts/poll-loop.py --interval 10
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CYCLE_LOG = os.path.join(ROOT, "logs", "sweep-cycle_log.md")
WINDOWS = os.path.join(ROOT, "lookups", "poll-window.csv")
CLAIM = os.path.join(tempfile.gettempdir(), "osint-poll-claim.txt")
PROMPT = "run the sweep cycle"

# The window: the cycle opens from START to STOP, across midnight (Bill, 2026-10-30; start 20:00, 2026-11-10).
START, STOP = dt.time(20, 0), dt.time(1, 0)

ROW = re.compile(r"^\|\s*\d+\s*\|")
STAMP = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


def night_of(t: dt.datetime) -> dt.date:
    """The evening a moment belongs to: noon to noon."""
    return (t - dt.timedelta(hours=12)).date()


def as_date(v: str) -> dt.date | None:
    """`2026-11-03`, or `03/11/2026` as Excel saves it on a UK machine (day first)."""
    v = v.strip()
    for f in ("%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y"):
        try:
            return dt.datetime.strptime(v, f).date()
        except ValueError:
            pass
    return None


def as_time(v: str) -> dt.time:
    """`01:00`, `1:00` or `1:00:00`."""
    h, m, *_ = (v.strip() + ":0").split(":")
    return dt.time(int(h), int(m))


def window(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """The hours of the night whose evening falls on `day`: its row in WINDOWS, else the
    default. A stop at or before the start is the next morning's."""
    start, stop = START, STOP
    try:
        with open(WINDOWS, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                if as_date(r.get("night") or "") == day:
                    start, stop = as_time(r["start"]), as_time(r["stop"])
    except (OSError, ValueError, KeyError) as e:
        print(f"poll: {WINDOWS} unreadable ({e}); default hours", flush=True)
    a = dt.datetime.combine(day, start)
    b = dt.datetime.combine(day if stop > start else day + dt.timedelta(days=1), stop)
    return a, b


def in_window(now: dt.datetime) -> bool:
    return any(a <= now < b for a, b in (window(now.date() - dt.timedelta(days=1)), window(now.date())))


def run_tonight(night: dt.date) -> list[str]:
    """Rotation cells (Start, New-Start) whose stamp falls in tonight."""
    hits = []
    with open(CYCLE_LOG, encoding="utf-8") as fh:
        for line in fh:
            if not ROW.match(line):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            day, start, new_start = cells[0], cells[3], cells[-1]
            for name, cell in (("Start", start), ("New-Start", new_start)):
                m = STAMP.match(cell)
                if m and night_of(dt.datetime.strptime(m.group(), "%Y-%m-%d %H:%M")) == night:
                    hits.append(f"Day {day} {name} {cell}")
    return hits


def claimed(night: dt.date) -> bool:
    try:
        with open(CLAIM, encoding="utf-8") as fh:
            return fh.read().strip() == night.isoformat()
    except OSError:
        return False


def open_claude(title: str, prompt: str) -> None:
    """A new tab in the main Terminal window, running an interactive session on `prompt`."""
    subprocess.Popen(["wt.exe", "-w", "main", "new-tab", "--title", title, "-d", ROOT,
                      "pwsh", "-NoExit", "-Command",
                      f"claude -n {title.lower()} --model opus --dangerously-skip-permissions '{prompt}'"])


def check() -> str:
    night = night_of(dt.datetime.now())
    if claimed(night):
        return "opened tonight, standing down"
    hits = run_tonight(night)
    if hits:
        return "already ran or running tonight, standing down · " + " · ".join(hits)
    try:
        open_claude("OSINT-CYCLE", PROMPT)
    except OSError as e:
        return f"launch failed, retrying next check · {e}"
    with open(CLAIM, "w", encoding="utf-8") as fh:
        fh.write(night.isoformat() + "\n")
    return "sweep cycle opened in a new tab"


def next_slot(now: dt.datetime, minutes: int) -> dt.datetime:
    """The next check on the interval's grid, moved to the next night's start if it falls outside."""
    t = now.replace(second=0, microsecond=0)
    t += dt.timedelta(minutes=minutes - t.minute % minutes)
    if not in_window(t):
        t = min(a for a, _ in (window(now.date()), window(now.date() + dt.timedelta(days=1))) if a > now)
    return t


def main() -> int:
    ap = argparse.ArgumentParser(description="The nightly trigger for the sweep cycle.")
    ap.add_argument("--interval", type=int, default=5, help="minutes between checks")
    ap.add_argument("--now", action="store_true", help="one check now, ignoring the window")
    args = ap.parse_args()
    if args.now:
        print(f"{dt.datetime.now():%H:%M}  {check()}", flush=True)
        return 0
    a, b = window(night_of(dt.datetime.now()))
    print(f"poll: sweep cycle opens tonight {a:%H:%M}-{b:%H:%M} (default {START:%H:%M}-{STOP:%H:%M}), "
          f"checked every {args.interval} min. Ctrl+C stops it.", flush=True)
    now = dt.datetime.now()
    when = now if in_window(now) else next_slot(now, args.interval)
    last = ""
    while True:
        if when > dt.datetime.now() + dt.timedelta(minutes=args.interval + 1):
            print(f"{dt.datetime.now():%H:%M}  waiting until {when:%a %H:%M}", flush=True)
        # Sleep in short steps, so a machine that sleeps through a slot checks on waking, and
        # re-read the night's hours at each step, so an edit to poll-window.csv moves a pause.
        while dt.datetime.now() < when:
            time.sleep(min(60, max(1, (when - dt.datetime.now()).total_seconds())))
            now = dt.datetime.now()
            if when - now > dt.timedelta(minutes=args.interval):
                when = now if in_window(now) else next_slot(now, args.interval)
        if in_window(dt.datetime.now()):
            line = check()
            if line != last:  # a stand-down repeats every check; print it once
                print(f"{dt.datetime.now():%H:%M}  {line}", flush=True)
                last = line
        when = next_slot(dt.datetime.now(), args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\npoll: stopped")
        sys.exit(0)
