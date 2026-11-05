#!/usr/bin/env python3
"""
sweep-stats.py — append one night's per-sweep statistics to `logs/sweep-stats.csv`.

One row per sweep process the night ran: `SWEEP-DAILY` (the list and off-list sweeps
together) plus each unprefixed job in the night's rotation row, so a Day 1 night writes
five rows and a Day 2 night four. Template: `X:\\documentation\\sweep-stats.csv`, with
`dropped-other` and `needs-clip` added so a row reconciles.

Every figure is read from a data file, never from a tally's prose:

- `staged`     files added under `new/` by any commit whose `sweep_batch` is
               `<sweep>-<night>` (git, so ingest moving them out does not lose them);
               never fewer than ingested + ingest drops + still in `new/`, for a night
               whose sweep commit did not carry `new/`.
- `fetched`    staged + every row of the sweep's own drop logs for the night
               (`sweep/<folder>/*drop*-<night>*.csv`): every in-window search hit the sweep
               put aside is a drop row (`wiki/brief-sweep.md` -> *A discard is a drop*).
- `ingested`   `raw/` records carrying a `sweep_batch` of `<sweep>-<night>`.
- `dup-same-url` sweep and ingest drops coded already-seen or duplicate-*: this URL was
               already ruled on (admitted or dropped) or caught by a sibling tonight.
- `dup-same-story` drops coded already-held or syndicated-copy: a new URL for a story
               `raw/` already holds or tonight's run already staged.
- `out-of-scope` sweep and ingest drops coded off-topic or off-place.
- `dropped-other` every other sweep or ingest drop (no-development, out-of-window, ...).
- `needs-clip` staged files carrying `needs_clip: true`.

The night is the sweep_batch date, which is the rotation row's `Start` date at the close.
A night already in the CSV is replaced, so a re-run is idempotent.

Usage:
  python scripts/sweep-stats.py                      # the newest closed rotation row
  python scripts/sweep-stats.py --night 2026-11-03 --day 1
  python scripts/sweep-stats.py --night 2026-11-03 --day 1 --print
"""
import argparse
import csv
import glob
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

OUT = os.path.join(V.ROOT, "logs", "sweep-stats.csv")
CYCLE_LOG = os.path.join(V.ROOT, "logs", "sweep-cycle_log.md")
COLS = ["date", "sweep", "fetched", "staged", "ingested", "dup-same-url", "dup-same-story",
        "out-of-scope",
        "dropped-other", "needs-clip"]
# process name -> (sweep/ folders holding its drop logs, sweep_batch keys)
SWEEPS = {
    "SWEEP-DAILY": (["daily", "off-list"], ["daily", "off-list", "offlist"]),
    "SWEEP-NEWSPAPERS": (["newspapers"], ["newspapers"]),
    "SWEEP-JOURNALS": (["journals"], ["journals"]),
    "SWEEP-THINKTANKS": (["thinktanks"], ["thinktanks"]),
    "SWEEP-REGIONAL": (["regional"], ["regional"]),
    "SWEEP-FINANCIERS": (["financiers"], ["financiers", "fin"]),
    "SWEEP-IATI": (["iati"], ["iati"]),
    "SWEEP-COUNTRY-DEEP": (["country-deep"], ["country-deep", "deep"]),
}
SAME_URL = {"already-seen"}                      # plus duplicate-*: this URL was ruled on
SAME_STORY = {"already-held", "syndicated-copy"}  # a new URL for a story held or staged
SCOPE = {"off-topic", "off-place"}
BATCH_RE = re.compile(r"^sweep_batch:\s*[\"']?([^\"'\r\n]+)", re.M)
CLIP_RE = re.compile(r"^needs_clip:\s*[\"']?true", re.M | re.I)


def batch_key(batch, night):
    """`country-deep-2026-11-02` -> `country-deep` when dated `night`, else None."""
    batch = (batch or "").strip()
    i = batch.rfind(night)
    if i < 0:
        return None
    key = batch[:i].rstrip("-") or batch[i + len(night):].strip("-")
    return re.sub(r"-\d+$", "", key).lower() or None


def proc_of(key):
    for name, (_, keys) in SWEEPS.items():
        if key in keys:
            return name
    return None


def kind(code):
    code = (code or "").strip()
    if code in SAME_URL or code.startswith("duplicate"):
        return "dup-same-url"
    if code in SAME_STORY:
        return "dup-same-story"
    if code in SCOPE:
        return "out-of-scope"
    return "dropped-other"


def git(*args):
    r = subprocess.run(["git", "-C", V.ROOT, *args], capture_output=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else ""


def rotation_day(night, day=None):
    """(day, [unprefixed jobs]) for `--day`, else the row whose Start is dated `night`."""
    head, rows = None, []
    for ln in open(CYCLE_LOG, encoding="utf-8", errors="replace"):
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- :"):
            continue
        if head is None:
            head = [c.lower() for c in cells]
            continue
        rows.append(dict(zip(head, cells)))
    for r in rows:
        if (day and r.get("day") == str(day)) or (not day and (r.get("start") or "").startswith(night)):
            return r["day"], [j.strip() for j in r.get("jobs", "").split(",")
                              if j.strip() and not j.strip().startswith("@")]
    return None, []


def newest_night():
    best = None
    for ln in open(CYCLE_LOG, encoding="utf-8", errors="replace"):
        m = re.search(r"\|\s*(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}\s*\|", ln)
        if m and (best is None or m.group(1) > best):
            best = m.group(1)
    return best


def collect(night, procs):
    st = {p: dict.fromkeys(COLS[2:], 0) for p in procs}
    floor = dict.fromkeys(procs, 0)          # ingest drops + still in new/, per sweep

    # staged and needs-clip: files added under new/ since the day before, read at their commit
    seen = set()
    import datetime
    since = datetime.date.fromisoformat(night) - datetime.timedelta(days=1)
    log = git("log", f"--since={since} 00:00", "--diff-filter=A", "--name-only",
              "--format=@%H", "--", "new/")
    commit = None
    for ln in log.splitlines():
        if ln.startswith("@"):
            commit = ln[1:]
            continue
        if not ln.endswith(".md") or ln in seen:
            continue
        text = git("show", f"{commit}:{ln}")[:4000]
        m = BATCH_RE.search(text)
        p = proc_of(batch_key(m.group(1), night)) if m else None
        if p in st:
            seen.add(ln)
            st[p]["staged"] += 1
            st[p]["needs-clip"] += bool(CLIP_RE.search(text))

    # sweep-side drops
    for p in procs:
        for folder in SWEEPS[p][0]:
            for path in glob.glob(os.path.join(V.ROOT, "sweep", folder, f"*drop*-{night}*.csv")):
                with open(path, encoding="utf-8", errors="replace", newline="") as fh:
                    for r in csv.DictReader(fh):
                        st[p]["fetched"] += 1
                        st[p][kind(r.get("reason") or r.get("code"))] += 1

    # ingest-side drops (ingest's drop logs carry the sweep_batch)
    for path in glob.glob(os.path.join(V.ROOT, "sweep", "ingest", "drop-log-*.csv")):
        with open(path, encoding="utf-8", errors="replace", newline="") as fh:
            for r in csv.DictReader(fh):
                p = proc_of(batch_key(r.get("sweep_batch"), night))
                if p in st:
                    st[p][kind(r.get("reason"))] += 1
                    floor[p] += 1

    # ingested: raw/ records from the night's batches
    for root, _, files in os.walk(os.path.join(V.ROOT, "raw")):
        for f in files:
            if not f.endswith(".md"):
                continue
            with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                m = BATCH_RE.search(fh.read(3000))
            if m and night in m.group(1):
                p = proc_of(batch_key(m.group(1), night))
                if p in st:
                    st[p]["ingested"] += 1

    # still awaiting ingest
    for f in glob.glob(os.path.join(V.ROOT, "new", "*.md")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            m = BATCH_RE.search(fh.read(3000))
        p = proc_of(batch_key(m.group(1), night)) if m else None
        if p in st:
            floor[p] += 1

    for p in procs:
        # a night whose sweep commit did not carry new/ still left its catch downstream
        st[p]["staged"] = max(st[p]["staged"], floor[p] + st[p]["ingested"])
        st[p]["fetched"] += st[p]["staged"]
    return [dict(date=night, sweep=p, **st[p]) for p in procs]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--night", metavar="YYYY-MM-DD", help="default: newest Start in the rotation")
    ap.add_argument("--day", help="rotation Day; default: the row whose Start is dated --night")
    ap.add_argument("--print", dest="show", action="store_true", help="write nothing")
    a = ap.parse_args()
    night = a.night or newest_night()
    day, jobs = rotation_day(night, a.day)
    if not day:
        print(f"sweep-stats: no rotation row for {night}; pass --day", file=sys.stderr)
        return 2
    procs = ["SWEEP-DAILY"] + [j for j in jobs if j in SWEEPS]
    rows = collect(night, procs)

    if a.show:
        w = csv.DictWriter(sys.stdout, COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        return 0
    old = []
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8", newline="") as fh:
            old = [r for r in csv.DictReader(fh) if r.get("date") != night]
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, COLS, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(old + rows, key=lambda r: r["date"]))
    print(f"logs/sweep-stats.csv: {night} Day {day}, {len(rows)} rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
