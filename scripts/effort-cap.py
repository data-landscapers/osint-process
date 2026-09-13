#!/usr/bin/env python3
r"""
effort-cap.py — LINT #33. Which item this run spent itself on.

`CLAUDE.md` -> *Good beats perfect* says dispose of the awkward item in one move, and the
rule loses to curiosity every time it is only prose. On one day in August a single municipal
population figure took 35 of 68 log entries, two acquire passes, two ingest passes and three
provincial PDFs, and closed with the residual standing at one person. No individual step was
wrong; each was justified on its own, which is why the pattern is invisible from inside it
and has to be counted from outside.

The script reads the run's own entries out of `logs/log.md` and reports **any item named in
three or more of them**. At the third the item is over: drop it, or write what is not
established onto the page it bears on, dated. Never a fourth pass.

**An item is a name the vault already uses**, never a word picked out of prose. The
vocabulary is every **adjacent word pair** in a `raw/`, `wiki/` or open-brief filename —
`luanda cacuaco`, `include divides`, `rgph 2024` — matched against the same pairs in the
entry's `<what changed>` field. A pair is a name; a single word is usually furniture, and
counting single words made *written*, *lines* and *pages* the run's biggest items. Nothing
is maintained: a new place or topic joins the vocabulary the day something is filed under it,
and no stoplist of common words exists to go stale.

The entry's grammar is not read — not the stamp, the pass name, the cost or the revert hint.
Counting those makes every judgment call a mention of *decision* and every `revert: git
checkout` a mention of *checkout*.

**Surface only.** The disposal is a judgment — drop it, or state the absence dated — and a
script that made it would be deciding what the wiki says.

Usage:
  python scripts/effort-cap.py                 the last 12 hours of entries
  python scripts/effort-cap.py --window 3      a shorter run
  python scripts/effort-cap.py --cap 5         a different threshold
  python scripts/effort-cap.py --json          machine-readable

Exit 0 always. A run that concentrated on one item is a finding to read, not a failure.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = os.path.join(V.ROOT, "logs", "log.md")
ENTRY_RE = re.compile(r"^(?:## )?(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\b")
WINDOW_HOURS = 12
MENTION_CAP = 3

# Below four characters a "word" is a date fragment, an ISO code or a stray abbreviation, and
# every pair of them matches something.
MIN_TOKEN = 4

VAULT_DIRS = ("raw", "wiki", os.path.join("reviews", "contradictions"))


def words(text):
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if len(t) >= MIN_TOKEN]


def pairs(toks):
    return set(zip(toks, toks[1:]))


def vault_names():
    """Every adjacent word pair the vault uses in a filename.

    Filenames are the right source and page *bodies* are not: `raw/` is named by date and
    slug, `wiki/` by page stem, a brief by the question it holds. Reading bodies would pull
    in every word the corpus contains, which is the prose heuristic this deliberately is not."""
    names = set()
    for base in VAULT_DIRS:
        for dirpath, _dirs, files in os.walk(os.path.join(V.ROOT, base)):
            for fn in files:
                if fn.endswith(".md"):
                    names |= pairs(words(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fn[:-3])))
    return names


def run_entries(window_hours):
    """The entries of the current run — everything within `window_hours` of the newest.

    A run has no marker in `log.md` and does not need one: passes write as they close, so
    the night's work is a contiguous block and the window is what separates it from the
    last one. `--window` is there for the run that was shorter or longer than usual."""
    rows = []
    with open(LOG, encoding="utf-8") as fh:
        for ln in fh.read().split("\n"):
            m = ENTRY_RE.match(ln)
            if m:
                rows.append((dt.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M"), ln))
    if not rows:
        return []
    edge = max(t for t, _ in rows) - dt.timedelta(hours=window_hours)
    return [ln for t, ln in rows if t >= edge]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    ap.add_argument("--window", type=float, default=WINDOW_HOURS, metavar="HOURS",
                    help=f"how far back the run reaches (default {WINDOW_HOURS})")
    ap.add_argument("--cap", type=int, default=MENTION_CAP,
                    help=f"entries naming one item before it is over (default {MENTION_CAP})")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    a = ap.parse_args()

    if not os.path.exists(LOG):
        print("logs/log.md: not present — nothing to read.", file=sys.stderr)
        return 0

    entries = run_entries(a.window)
    known = vault_names()

    hits = Counter()
    for ln in entries:
        body = " ".join(f for f in ln.split(" · ")[2:]
                        if not f.startswith(("revert:", "cost:")))
        # One entry counts once for an item however often it names it: what is measured is
        # how many times the run came back to it, not how it was written up.
        for name in pairs(words(body)) & known:
            hits[name] += 1

    over = [(" ".join(p), n) for p, n in hits.most_common() if n >= a.cap]

    if a.json:
        print(json.dumps({"entries": len(entries), "window_hours": a.window,
                          "cap": a.cap, "over": over}, indent=2))
        return 0

    if not over:
        print(f"effort-cap: {len(entries)} entries in the last {a.window:g}h, nothing named "
              f"in {a.cap} or more — no item took the run over.")
        return 0

    for name, n in over[:12]:
        print(f"  {name}: {n} of {len(entries)} entries — the cap is {a.cap}. Drop it, or "
              f"write what is not established onto the page it bears on, dated. Not a "
              f"fourth pass.")
    if len(over) > 12:
        print(f"  and {len(over) - 12} more over the cap.")
    print(f"effort-cap: {len(over)} item(s) named in {a.cap}+ of {len(entries)} entries "
          f"over {a.window:g}h.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
