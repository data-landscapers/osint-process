#!/usr/bin/env python3
r"""
usage-log.py — append one row to `logs/usage-log.csv`: the weekly plan limit used, as a percentage.

**Why it exists.** Bill wants the cost of a night visible against the weekly token limit (2026-09-13). `SWEEP-CYCLE.md` calls it twice: first act of the night, and after the night's last commit, before the last mirror — so a night's cost is the difference between its two rows.

**Where the number comes from.** The same endpoint Claude Code's `/usage` reads, `api.anthropic.com/api/oauth/usage`, authorised by the login in `~/.claude/.credentials.json`; the field is `seven_day.utilization`. The endpoint is undocumented, so a failure never blocks the cycle: the row is written with `n/a` and the script exits 0.

Columns: `Date`, `Time (UTC)`, `7d usage`. Appends only; creates the file with its header if absent.
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
HEADER = ["Date", "Time (UTC)", "7d usage"]


def weekly_percent():
    token = json.loads(CREDS.read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]
    req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    return f"{float(data['seven_day']['utilization']):.0f}%"


def main():
    now = dt.datetime.now(dt.timezone.utc)
    try:
        usage = weekly_percent()
    except Exception as e:
        print(f"usage-log: could not read usage ({type(e).__name__}: {e}); writing n/a", file=sys.stderr)
        usage = "n/a"
    new = not LOG.exists()
    with LOG.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if new:
            w.writerow(HEADER)
        w.writerow([now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), usage])
    print(f"usage-log: {now:%Y-%m-%d %H:%M} UTC · 7d {usage}")


if __name__ == "__main__":
    main()
