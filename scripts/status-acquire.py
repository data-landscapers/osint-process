#!/usr/bin/env python3
"""standing — the row ledger behind `STATUS-ACQUIRE.md`.

`X:\\africa-acquire.csv` is CORPUS's list of sources it cited when building the
country status reports and OSINT does not hold. This script is the only thing that
reads or writes it: it selects one country's rows into a run manifest under
`sweep/status-acquire/`, records each row's outcome, and at the close moves the
rows out of `africa-acquire.csv` into `X:\\acquire-done.csv`. The pass itself does
the fetching and never edits either CSV by hand — a shared file CORPUS also writes
is not a thing to sed.

Usage:
  status-acquire.py --list                    # outstanding rows per ISO3
  status-acquire.py --select ISO3             # write the run manifest, pre-marking held rows
  status-acquire.py --mark ISO3 STATUS [--note TEXT]   # URLs on stdin, one per line
  status-acquire.py --close ISO3              # move the marked rows to acquire-done.csv

Statuses: staged | held | rejected | dropped   (every row carries one before --close)
"""

import argparse
import csv
import os
import sys
from collections import Counter
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V  # noqa: E402

ACQUIRE = r"X:\africa-acquire.csv"
DONE = r"X:\acquire-done.csv"
STATE = os.path.join(V.ROOT, "sweep", "status-acquire")
STATUSES = ("staged", "held", "rejected", "dropped")
COLS = ["iso3", "published", "publisher", "title", "url", "sub_section",
        "found", "status", "notes"]


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, cols):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def manifest_path(iso3):
    return os.path.join(STATE, f"{iso3}.csv")


def held_lookup():
    """Normalised URL -> what already adjudicated it: a `raw/` file, or a rejection."""
    seen = {}
    for r in read_csv(os.path.join(V.ROOT, "lookups", "raw-url-index.csv")):
        seen[r["url_normalized"]] = ("held", r["file"])
    for r in read_csv(os.path.join(V.ROOT, "lookups", "rejected-urls.csv")):
        seen.setdefault(r["url_normalized"], ("rejected", r["reason"]))
    return seen


def cmd_list():
    rows = read_csv(ACQUIRE)
    counts = Counter(r["iso3"] for r in rows)
    for iso3, n in sorted(counts.items()):
        print(f"{iso3}\t{n}")
    print(f"--\t{len(rows)} rows outstanding, {len(counts)} countries")
    done = read_csv(DONE)
    print(f"--\t{len(done)} rows closed in acquire-done.csv")


def cmd_select(iso3):
    rows = read_csv(ACQUIRE)
    mine = [r for r in rows if r["iso3"] == iso3]
    if not mine:
        known = sorted({r["iso3"] for r in rows})
        sys.exit(f"no outstanding rows for {iso3!r}. Outstanding: {' '.join(known)}")
    seen = held_lookup()
    for r in mine:
        verdict = seen.get(V.normalise_url(r["url"]))
        if verdict:
            r["status"], r["notes"] = verdict[0], verdict[1]
        else:
            r["status"], r["notes"] = "", ""
    os.makedirs(STATE, exist_ok=True)
    write_csv(manifest_path(iso3), mine, COLS)
    pre = Counter(r["status"] for r in mine if r["status"])
    print(f"{manifest_path(iso3)} — {len(mine)} rows"
          + (f", pre-marked {dict(pre)}" if pre else ""))
    for i, r in enumerate(mine, 1):
        flag = f"[{r['status']}] " if r["status"] else ""
        print(f"{i}\t{r['published']}\t{r['sub_section']}\t{flag}{r['title'][:70]}\t{r['url']}")


def cmd_mark(iso3, status, note):
    if status not in STATUSES:
        sys.exit(f"status must be one of: {' '.join(STATUSES)}")
    path = manifest_path(iso3)
    if not os.path.exists(path):
        sys.exit(f"no manifest at {path} — run --select {iso3} first")
    rows = read_csv(path)
    wanted = {V.normalise_url(u.strip()) for u in sys.stdin if u.strip()}
    if not wanted:
        sys.exit("no URLs on stdin")
    hit = 0
    for r in rows:
        if V.normalise_url(r["url"]) in wanted:
            r["status"], hit = status, hit + 1
            if note:
                r["notes"] = note
    write_csv(path, rows, COLS)
    missed = len(wanted) - hit
    print(f"{hit} rows marked {status}" + (f"; {missed} URLs matched no row" if missed else ""))


def cmd_close(iso3):
    path = manifest_path(iso3)
    if not os.path.exists(path):
        sys.exit(f"no manifest at {path} — run --select {iso3} first")
    marked = read_csv(path)
    blank = [r for r in marked if r["status"] not in STATUSES]
    if blank:
        sys.exit(f"{len(blank)} rows carry no status — every row leaves the queue "
                 f"with one of: {' '.join(STATUSES)}\n"
                 + "\n".join("  " + r["url"] for r in blank[:10]))
    today = date.today().isoformat()
    keys = {(r["iso3"], V.normalise_url(r["url"])) for r in marked}
    live = read_csv(ACQUIRE)
    kept = [r for r in live if (r["iso3"], V.normalise_url(r["url"])) not in keys]
    moved = len(live) - len(kept)
    done = read_csv(DONE)
    for r in marked:
        r["found"] = r.get("found", "")
        r["closed"] = today
    write_csv(DONE, done + marked, COLS + ["closed"])
    write_csv(ACQUIRE, kept, COLS)
    os.remove(path)
    print(f"{moved} rows moved to {DONE} ({dict(Counter(r['status'] for r in marked))}); "
          f"{len(kept)} rows left outstanding")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--select", metavar="ISO3")
    g.add_argument("--mark", nargs=2, metavar=("ISO3", "STATUS"))
    g.add_argument("--close", metavar="ISO3")
    p.add_argument("--note", default="", help="--mark: note written on every row matched")
    a = p.parse_args()
    if a.list:
        cmd_list()
    elif a.select:
        cmd_select(a.select.upper())
    elif a.mark:
        cmd_mark(a.mark[0].upper(), a.mark[1], a.note)
    else:
        cmd_close(a.close.upper())


if __name__ == "__main__":
    main()
