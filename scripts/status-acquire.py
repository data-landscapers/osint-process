#!/usr/bin/env python3
"""standing — the row ledger behind `STATUS-ACQUIRE.md`.

`X:\\africa-acquire.csv` is CORPUS's list of sources it cited when building the
country status reports and OSINT does not hold. This script is the only thing that
reads or writes it: it selects one country's rows into a run manifest under
`sweep/status-acquire/`, records each row's outcome, and at the close moves the
rows out of `africa-acquire.csv` into `X:\\acquire-done.csv`. The pass itself does
the fetching and never edits either CSV by hand — a shared file CORPUS also writes
is not a thing to sed.

**CORPUS screens, fetches and stages; this side selects, registers and closes**
(strategic review 4, R24). CORPUS works one country with its own `status-stage.py`,
leaves the batch on `X:\\new-queue\\status-acquire-{ISO3}\\` with `READY` written last,
and leaves its drop list on `X:\\prepared\\status-acquire-{ISO3}-drops.csv` — the classes
are stated for it in `X:\\status-acquire.md`. `--absorb` is this side's whole half: it
reads that drop list, writes the permanent negatives through `raw-url-index.py --reject`
and closes the country's rows. The ingest step is the cycle's own backfill Phase A.

Usage:
  status-acquire.py --list                    # outstanding rows per ISO3
  status-acquire.py --due                     # countries whose drop list is ready to absorb
  status-acquire.py --absorb [ISO3]           # the close's one command; every due country if bare
  status-acquire.py --select ISO3             # write the run manifest, pre-marking held rows
  status-acquire.py --mark ISO3 STATUS [--note TEXT]   # URLs on stdin, one per line
  status-acquire.py --close ISO3              # move the marked rows to acquire-done.csv

Statuses: staged | held | rejected | dropped   (every row carries one before --close)
"""

import argparse
import csv
import os
import subprocess
import sys
from collections import Counter
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V  # noqa: E402

ACQUIRE = r"X:\africa-acquire.csv"
DONE = r"X:\acquire-done.csv"
PREPARED = r"X:\prepared"
QUEUE = r"X:\new-queue"
STATE = os.path.join(V.ROOT, "sweep", "status-acquire")
STATUSES = ("staged", "held", "rejected", "dropped")

# CORPUS's drop classes (`X:\status-acquire.md`) mapped to this ledger's four statuses.
# Only `not-a-document` earns a row in `lookups/rejected-urls.csv`: that file is the
# permanent negatives and pre-marks a URL rejected in every later country, so a failed
# fetch — true of one attempt on one day — never goes on it.
DROP_CLASSES = {"not-a-document": "dropped", "duplicate-row": "dropped",
                "unfetchable": "dropped", "held": "held", "rejected": "rejected"}
REGISTERED = ("not-a-document",)
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


def cmd_select(iso3, quiet=False):
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
    if quiet:                       # --absorb wants the count, not 28 lines at the close
        return
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


def drops_path(iso3):
    return os.path.join(PREPARED, f"status-acquire-{iso3}-drops.csv")


def awaiting_pull(iso3):
    """True while the batch folder still carries `READY` — CORPUS has staged it and the
    cycle has not pulled it yet. The pull's `delivered-` marker is not the test: CORPUS
    removes the emptied folder once it has committed the marker, so absence proves
    nothing. `READY` present is the one durable statement that the batch is still owed."""
    folder = os.path.join(QUEUE, f"status-acquire-{iso3}")
    return os.path.exists(os.path.join(folder, "READY"))


def cmd_due():
    live = read_csv(ACQUIRE)
    due = [i for i in sorted({r["iso3"] for r in live})
           if os.path.exists(drops_path(i)) and not awaiting_pull(i)]
    for iso3 in due:
        n = sum(1 for r in live if r["iso3"] == iso3)
        print(f"{iso3}\t{n} rows\t{drops_path(iso3)}")
    waiting = [i for i in sorted({r["iso3"] for r in live})
               if os.path.exists(drops_path(i)) and awaiting_pull(i)]
    for iso3 in waiting:
        print(f"{iso3}\t-\tstill carries READY — absorbs on the night that pulls it")
    print(f"--\t{len(due)} country(ies) due")
    return due


def cmd_absorb(iso3=None):
    """CORPUS's drop list applied, registered and closed — the close's one command.

    The country's own rows are the denominator: a row named in the drop list takes its
    class, every other row was staged. A pre-mark from `--select` wins over the drop
    list, because this side's normalisation is the authoritative one for `held` and
    `rejected` and a URL the vault already holds is never registered as a negative.
    """
    targets = [iso3] if iso3 else cmd_due()
    if not targets:
        print("status-acquire: nothing to absorb.")
        return
    for iso in targets:
        path = drops_path(iso)
        if not os.path.exists(path):
            sys.exit(f"no drop list at {path} — CORPUS writes it with the batch")
        if not os.path.exists(manifest_path(iso)):
            cmd_select(iso, quiet=True)
        rows = read_csv(manifest_path(iso))
        by_url = {V.normalise_url(r["url"]): r for r in rows}
        register, unmatched, counts = [], [], Counter()
        for d in read_csv(path):
            cls = (d.get("class") or "").strip()
            if cls not in DROP_CLASSES:
                sys.exit(f"{path}: unknown class {cls!r} — one of: "
                         f"{' '.join(sorted(DROP_CLASSES))}")
            r = by_url.get(V.normalise_url(d.get("url", "")))
            if r is None:
                unmatched.append(d.get("url", ""))
                continue
            if r["status"] in STATUSES:          # --select's pre-mark stands
                counts["pre-marked"] += 1
                continue
            r["status"] = DROP_CLASSES[cls]
            r["notes"] = (d.get("note") or cls).strip()
            if cls in REGISTERED:
                register.append(r["url"])
        for r in rows:
            if r["status"] not in STATUSES:
                r["status"] = "staged"
        write_csv(manifest_path(iso), rows, COLS)
        if register:
            subprocess.run([sys.executable,
                            os.path.join(V.ROOT, "scripts", "raw-url-index.py"),
                            "--reject", "not-a-document"] + register, check=True)
        for u in unmatched:
            print(f"  ! {iso}: drop list names a URL this feed has no row for — {u}")
        if counts["pre-marked"]:
            print(f"  · {iso}: {counts['pre-marked']} row(s) kept the pre-mark --select gave them")
        cmd_close(iso)
        os.replace(path, os.path.join(
            PREPARED, f"status-acquire-{iso}-drops-absorbed-{date.today().isoformat()}.csv"))


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--due", action="store_true")
    g.add_argument("--absorb", nargs="?", const="", metavar="ISO3")
    g.add_argument("--select", metavar="ISO3")
    g.add_argument("--mark", nargs=2, metavar=("ISO3", "STATUS"))
    g.add_argument("--close", metavar="ISO3")
    p.add_argument("--note", default="", help="--mark: note written on every row matched")
    a = p.parse_args()
    if a.list:
        cmd_list()
    elif a.due:
        cmd_due()
    elif a.absorb is not None:
        cmd_absorb(a.absorb.upper() or None)
    elif a.select:
        cmd_select(a.select.upper())
    elif a.mark:
        cmd_mark(a.mark[0].upper(), a.mark[1], a.note)
    else:
        cmd_close(a.close.upper())


if __name__ == "__main__":
    main()
