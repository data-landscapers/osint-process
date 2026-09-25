#!/usr/bin/env python3
"""page-length.py — is a wiki page over its line, by lint #8's own measure?

Strategic review 5 R81 (Bill's ruling R66): Phase B never appends to a page over its line;
it rewrites the landing section as synthesis at the write, and lint #8 registers nothing.
This is the writer's half of that gate. It measures a page exactly as lint #8 does — it
calls `lint-deterministic.py`'s `measure_page()` — so the slice and the lint cannot
disagree about where the line is.

    python scripts/page-length.py wiki/intersections/ken--dpi-id.md
        OVER  2,913 words (line 2,500) · synthesis · wiki/intersections/ken--dpi-id.md
    python scripts/page-length.py --trimmed PAGE --before 2913
        records one row in logs/phaseb-trims.csv: date,page,before,after

Run it on the landing page before the write. `OVER` (exit 1) means the write is a rewrite of
the landing section as synthesis (`WIKI-SYNC.md` → *A landing page over its line*); `under`
(exit 0) means an ordinary write, and `ruled` is under a current `## Length — reviewed` note.
After a rewrite, `--trimmed` measures the page again and records before and after — the
report `cycle-manifest.py` sums as `words_trimmed` (R83). The append takes a lock, because
Phase B slices run in parallel.
"""
import argparse
import datetime
import importlib.util
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vault_lib as V                                                # noqa: E402

spec = importlib.util.spec_from_file_location("lint_det", os.path.join(HERE, "lint-deterministic.py"))
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

TRIMS = os.path.join(V.ROOT, "logs", "phaseb-trims.csv")
LOCK = TRIMS + ".lock"


def measure(path):
    ap = os.path.abspath(path)
    rel = os.path.relpath(ap, V.ROOT).replace(os.sep, "/")
    text = open(ap, "rb").read().decode("utf-8", "replace")
    row, _ = V._row(rel, os.stat(ap), text)
    return rel, L.measure_page(row)


def record(rel, before, after):
    deadline = time.time() + 10
    while True:
        try:
            os.close(os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
            break
        except OSError:
            try:
                if time.time() - os.path.getmtime(LOCK) > 30:
                    os.remove(LOCK)             # stale lock from a crashed caller
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                sys.exit("page-length.py: could not take %s" % LOCK)
            time.sleep(0.1)
    try:
        new = not os.path.exists(TRIMS)
        with open(TRIMS, "a", encoding="utf-8", newline="") as fh:
            if new:
                fh.write("date,page,before,after\n")
            fh.write("%s,%s,%d,%d\n" % (datetime.date.today().isoformat(), rel, before, after))
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("pages", nargs="*")
    ap.add_argument("--trimmed", metavar="PAGE", help="record a rewrite of PAGE")
    ap.add_argument("--before", type=int, help="PAGE's words before the rewrite (--trimmed)")
    a = ap.parse_args()

    if a.trimmed:
        if a.before is None:
            sys.exit("page-length.py: --trimmed needs --before N, the count this script "
                     "printed before the write")
        rel, m = measure(a.trimmed)
        if m is None:
            sys.exit("page-length.py: %s is not a page lint #8 measures" % rel)
        record(rel, a.before, m["effective"])
        print("recorded  %s  %d -> %d words" % (rel, a.before, m["effective"]))
        return 0

    worst = 0
    for p in a.pages:
        rel, m = measure(p)
        if m is None:
            print("n/a   not a concept, place or intersection page · %s" % rel)
            continue
        state = "OVER" if m["over"] else "ruled" if m["over_line"] else "under"
        worst = max(worst, 1 if m["over"] else 0)
        print("%-5s %s words (line %s) · %s · %s" % (
            state, format(m["effective"], ","), format(L.CLASSIFY_LINE, ","), m["shape"], rel))
    return worst


if __name__ == "__main__":
    sys.exit(main())
