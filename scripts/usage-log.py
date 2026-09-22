#!/usr/bin/env python3
r"""
usage-log.py — read the weekly and 5-hour plan limits used, and record the reading: a row at the top of `logs/usage-log.csv`, a per-stage reading in `logs/usage-stages.jsonl`, or both.

**Why it exists.** Bill wants the cost of a night visible against the plan's token limits (2026-09-13). `SWEEP-CYCLE.md` writes a CSV row twice a night — first act, and after the night's last commit — so a night's cost is the difference between its two rows. **Since 2026-09-17 (strategic review 4 R4) it also reads at every stage boundary** of the night, into a buffer that `cycle-manifest.py --usage` writes into the manifest's `usage` block at the close, so a stage's cost is the difference between its reading and the one before it.

**Where the numbers come from.** The same endpoint Claude Code's `/usage` reads, `api.anthropic.com/api/oauth/usage`, authorised by the login in `~/.claude/.credentials.json`; the fields are `seven_day.utilization` and `five_hour.utilization`. The endpoint is undocumented, so a failure never blocks the cycle: the reading is written as `n/a` (CSV) or `null` (buffer) and the script exits 0.

Usage:
  python scripts/usage-log.py                               a CSV row only (the original call)
  python scripts/usage-log.py --stage sweep                 a buffer reading only
  python scripts/usage-log.py --reset --stage start --csv   empty the buffer, then both, from one reading

CSV columns: `Date`, `Time (UTC)`, `7d usage`, `Session usage`, whole percentages. `Session usage` is the row's `7d usage` less the row below's — D2 = C2 − C3 — recomputed for every row at each write, blank on the oldest row or beside an `n/a`; where the weekly limit reset between the two it is the row's own reading *(Bill, 2026-09-22, replacing the 5-hour column)*. Newest row first, directly under the header; creates the file if absent, and rewrites an older header to the current one.

Buffer: one JSON object a line, `{"stage", "time_utc", "seven_day", "five_hour"}`, percentages to one decimal place — a stage costs a point or two, which whole percentages would round away. Git-ignored; emptied by `--reset` at the night's first act, never by the manifest, so a rewritten manifest reads the same night again.
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
LOG = REPO / "logs" / "usage-log.csv"
STAGES = REPO / "logs" / "usage-stages.jsonl"
CREDS = pathlib.Path.home() / ".claude" / ".credentials.json"
URL = "https://api.anthropic.com/api/oauth/usage"
HEADER = ["Date", "Time (UTC)", "7d usage", "Session usage"]


def usage():
    """(seven_day, five_hour) utilisation as floats, or (None, None) on any failure."""
    try:
        token = json.loads(CREDS.read_text(encoding="utf-8"))["claudeAiOauth"]["accessToken"]
        req = urllib.request.Request(URL, headers={"Authorization": f"Bearer {token}", "anthropic-beta": "oauth-2025-04-20"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        return float(data["seven_day"]["utilization"]), float(data["five_hour"]["utilization"])
    except Exception as e:
        print(f"usage-log: could not read usage ({type(e).__name__}: {e}); writing n/a", file=sys.stderr)
        return None, None


def session(week, prior):
    """This row's weekly reading less the row below it, in whole points; blank where either is unreadable or there is no row below. A negative difference means the weekly limit reset in between, so the reading itself is the usage since."""
    pct = lambda v: int(v.rstrip("%")) if v.rstrip("%").isdigit() else None
    w, p = pct(week), pct(prior or "")
    if w is None or p is None:
        return ""
    return f"{w - p if w >= p else w}%"


def write_csv(now, week, five):
    cell = lambda v: "n/a" if v is None else f"{v:.0f}%"
    rows = []
    if LOG.exists():
        with LOG.open(newline="", encoding="utf-8") as f:
            rows = [r for r in csv.reader(f) if r][1:]
    rows = [[now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), cell(week)]] + [(r + [""] * 3)[:3] for r in rows]
    rows = [r + [session(r[2], rows[i + 1][2] if i + 1 < len(rows) else None)] for i, r in enumerate(rows)]
    with LOG.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerows([HEADER] + rows)


def write_stage(stage, now, week, five, reset):
    rnd = lambda v: None if v is None else round(v, 1)
    line = json.dumps({"stage": stage, "time_utc": now.strftime("%Y-%m-%d %H:%M"), "seven_day": rnd(week), "five_hour": rnd(five)}, ensure_ascii=False)
    with STAGES.open("w" if reset else "a", newline="\n", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--stage", metavar="NAME", help="record this reading in the per-stage buffer under NAME")
    ap.add_argument("--csv", action="store_true", help="with --stage, also write the CSV row (without --stage the CSV row is the default)")
    ap.add_argument("--reset", action="store_true", help="with --stage, empty the buffer before recording")
    a = ap.parse_args()
    if a.reset and not a.stage:
        ap.error("--reset needs --stage: an emptied buffer with no reading in it is a night with no start")

    now = dt.datetime.now(dt.timezone.utc)
    week, five = usage()
    if a.stage:
        write_stage(a.stage, now, week, five, a.reset)
    if a.csv or not a.stage:
        write_csv(now, week, five)
    shown = lambda v: "n/a" if v is None else f"{v:.1f}%"
    tail = f" · stage {a.stage}" if a.stage else ""
    print(f"usage-log: {now:%Y-%m-%d %H:%M} UTC · 7d {shown(week)} · 5h {shown(five)}{tail}")


if __name__ == "__main__":
    main()
