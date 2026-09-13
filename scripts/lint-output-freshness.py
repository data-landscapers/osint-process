#!/usr/bin/env python3
r"""
lint-output-freshness.py — LINT.md check 26, as a script.

Rescoped 2026-08-16 (OSINT/CORPUS migration, R2): the nightly output-refresh
phase that used to regenerate all of `outputs\` is retired — CORPUS now
authors the published output layer itself. What's left under `outputs\` is
OSINT's own compile, `outputs\non-state-finance\`, written by FINANCE-COMPILE
firing from ingest rather than by a dedicated refresh phase. This check
narrows to that one folder: an ingest-fired compile scoped to the wrong
places is exactly the miss nothing else would catch.

`outputs\budgets\` stays excluded — the domestic-state budget layer is
suspended (token review task 19), so its CSVs are frozen on purpose and
staleness there is not a defect.

**Reports, never fixes.** A stale folder means FINANCE-COMPILE didn't fire
or didn't cover it; that is a `[DECIDE]` note, not something this script
repairs.

Usage:  python scripts/lint-output-freshness.py [--quiet]
Exit:   0 clean, 1 the folder is stale, 2 no cycle close recorded at all.
"""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS = os.path.join(ROOT, "outputs")
SCOPE = "non-state-finance"
CYCLE_LOG = os.path.join(ROOT, "logs", "sweep-cycle_log.md")

TS = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})'


def parse(ts):
    return datetime.datetime.strptime(ts, "%Y-%m-%d %H:%M")


def last_cycle_run():
    """`(start, end)` of the most recently *completed* run — the row with the newest `End`.

    **The watermark is the run's `Start`, not its `End`.** FINANCE-COMPILE fires from ingest,
    which happens *inside* the run, so an output written during a cycle is by construction
    older than that cycle's close. Comparing against the close therefore passed only when the
    check ran *before* the close — its nightly slot — and failed on every standalone run
    afterwards, measuring when lint happened to be invoked rather than whether the compile
    fired. *(Found 2026-08-21: all 121 files rebuilt at 23:55, close stamped 00:14, reported
    stale.)*

    **`Start` and `End` are found by header name, never by position.** They were read at
    fixed offsets 4 and 5, which assumed a `Gate` column; that column retired with the
    housekeeping row on 2026-08-31, every cell shifted left by one, and the check went on
    reading `End` and `Duration` — `Duration` never matches a timestamp, so no row parsed
    and the check reported `NO CYCLE CLOSE RECORDED` over a full table. A check that passes
    over nothing is worse than no check, so the columns are resolved from the header row.
    A bare max() over every timestamped cell is still wrong: it picks up `New-Start` too,
    which belongs to a run still in progress.
    """
    if not os.path.exists(CYCLE_LOG):
        return None
    runs, i_start, i_end = [], None, None
    for ln in open(CYCLE_LOG, encoding="utf-8"):
        if not ln.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if i_start is None:
            if "Start" in cells and "End" in cells:
                i_start, i_end = cells.index("Start"), cells.index("End")
            continue
        if len(cells) <= max(i_start, i_end):
            continue
        start, end = cells[i_start], cells[i_end]
        if re.fullmatch(TS, start) and re.fullmatch(TS, end):
            runs.append((parse(start), parse(end)))
    return max(runs, key=lambda r: r[1]) if runs else None


def newest_mtime(folder):
    newest = None
    for dirpath, _, files in os.walk(folder):
        for fn in files:
            m = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(dirpath, fn)))
            if newest is None or m > newest:
                newest = m
    return newest


def main():
    quiet = "--quiet" in sys.argv
    run = last_cycle_run()
    if run is None:
        print("lint 26 output freshness: NO CYCLE CLOSE RECORDED - logs/sweep-cycle_log.md is missing or empty.")
        return 2

    folder = os.path.join(OUTPUTS, SCOPE)
    if not os.path.isdir(folder):
        print(f"lint 26 output freshness: outputs\\{SCOPE}\\ does not exist.")
        return 2

    start, end = run
    newest = newest_mtime(folder)
    if newest is None or newest < start:
        when = f"{newest:%Y-%m-%d %H:%M}" if newest else "empty"
        print(f"lint 26 output freshness: outputs/{SCOPE}/ stale against the last completed "
              f"run {start:%Y-%m-%d %H:%M} - {end:%H:%M} - newest file {when}")
        print("  FINANCE-COMPILE should have regenerated this from ingest during that run.")
        return 1

    if not quiet:
        print(f"lint 26 output freshness: ok - outputs/{SCOPE}/ written {newest:%Y-%m-%d %H:%M}, "
              f"inside the last completed run {start:%Y-%m-%d %H:%M} - {end:%H:%M}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
