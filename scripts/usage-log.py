#!/usr/bin/env python3
r"""
usage-log.py — insert one row at the top of `logs/usage-log.csv`: the weekly and 5-hour plan limits used, as percentages.

**Why it exists.** Bill wants the cost of a night visible against the plan's token limits (2026-09-13). `SWEEP-CYCLE.md` calls it twice: first act of the night, and after the night's last commit, before the last mirror — so a night's cost is the difference between its two rows.

**Where the numbers come from.** The same endpoint Claude Code's `/usage` reads, `api.anthropic.com/api/oauth/usage`, authorised by the login in `~/.claude/.credentials.json`; the fields are `seven_day.utilization` and `five_hour.utilization`. The endpoint is undocumented, so a failure never blocks the cycle: the row is written with `n/a` and the script exits 0.

Columns: `Date`, `Time (UTC)`, `7d usage`, `5h usage`. Newest row first, directly under the header; creates the file if absent, and rewrites an older header to the current one, leaving a missing cell blank.
"""
import csv
import datetime as dt
import json
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
LOG = REPO / "logs" / "usage-log.csv"
CREDS = pathlib.Path.home() / ".claude" / ".credentials.json"
URL = "https://api.anthropic.com/api/oauth/usage"
HEADER = ["Date", "Time (UTC)", "7d usage", "5h usage"]


def pct(block):
    return f"{float(block['utilization']):.0f}%"


def usage():
    token = json.loads(CREDS.read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]
    req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return pct(data["seven_day"]), pct(data["five_hour"])


def main():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        week, five = usage()
    except Exception as e:
        print(f"usage-log: could not read usage ({type(e).__name__}: {e}); writing n/a", file=sys.stderr)
        week = five = "n/a"
    rows = []
    if LOG.exists():
        with LOG.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if r][1:]
    rows = [[now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), week, five]] + [(r + [""] * len(HEADER))[:len(HEADER)] for r in rows]
    with LOG.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows([HEADER] + rows)
    print(f"usage-log: {now:%Y-%m-%d %H:%M} UTC · 7d {week} · 5h {five}")


if __name__ == "__main__":
    main()
