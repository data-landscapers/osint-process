#!/usr/bin/env python3
"""
log-append.py — standing. The only sanctioned writer of `logs/log.md`.

`logs/log.md` is newest-at-top and stamped in **UTC**, while the machine clock is UTC+1.
Both facts were prose, and both broke on 2026-08-20: seven sub-agents were handed a local
clock and twelve of their lines landed an hour ahead on tomorrow's date, while the sweeps
appended at the *foot* of the file, where `rotate-log.py` — which truncates from the bottom —
ate all ten of them at the close. Neither was a judgment failure. An agent that must format
a timestamp and choose an insertion point will eventually get one of them wrong, so it does
neither: this script reads the clock itself and inserts at the top.

The entry form is `STATUS.md`'s and is assembled here, never passed in whole:

    YYYY-MM-DD HH:MM · <pass> · <what changed> · revert: <hint>

**Only a process's own result, or a fatal error, earns a line** *(Bill, 2026-09-08)*. Not a
decision — a ruling about how a pass should behave belongs in the commit body beside the diff
that carries it. Not a per-item call, which rides the pass's own line. Not an agent: a slice is
not a process. And **there is no cost field** (`--cost` removed with the run-cost line it fed).

The pass name is written **in bold capitals** — `**WIKI-STATUS**` — normalised here from
whatever the caller passes, so no caller has to remember the convention and the file can be
scanned by eye for one process's history.

Usage:
  python scripts/log-append.py "<pass>" "<what changed>" "<revert hint>"
  python scripts/log-append.py "sweep cycle" "day 1 closed, 76 admitted" "git revert HEAD"
  python scripts/log-append.py ... --at 2026-08-20T23:20     # a measured time, not now
  python scripts/log-append.py --check                       # write nothing, audit the file

`--at` exists for one case only: the parent correcting a nested line against **its own
measurement** (`SWEEP-CYCLE.md`). It takes UTC, and it is never an estimate. **A `--at` ahead of
now is refused** *(2026-08-22, notes-for-osint 36)*: a measurement is of something that has
already happened, so a future one is a narrated estimate or a local clock read as UTC, and both
are the fault this script exists to remove. A past `--at` is not checked — correcting a nested
line legitimately reaches backwards, sometimes hours.

`--check` audits the file for the same two defects after the fact, whoever wrote the line —
a stamp ahead of now, or an entry sitting more than `--tolerance` hours out of position. It
is **`LINT.md` check #29**, surface-only and nightly: the offset to subtract and the place a
line belongs are both judgment, and a check that silently re-sorted this file would rewrite
CC's own recall.

`--check` no longer reads `logs/ingested_log.md`, retired 2026-09-07 — the future-stamp defect
that check caught there (CORPUS bylines the bulletin off `cycle-manifest.json`'s `collection`
block, and a stamp ahead of now was the one error a reader could not explain away) is now
refused at write time by `cycle-manifest.py --stamp` instead, which is what closes ingest now.
Catching it at the write means there is nothing left here to audit after the fact.

**An entry is capped at 40 words and the cap is refused, not reported** *(strategic review
2026-08-27, task 4)*. One line was the rule and it held; telegraphic was the rule and it did
not — entries averaged 54 words against a form whose worked example runs 19, with one at 429.
The pattern in every long one is self-justification, the reasoning attached to prove the action
was sound, and that reasoning is already in git with the diff it explains. A refused entry is
not a lost one: cut it to counts and objects, and put the argument in the commit body.

`--check` counts over-length entries already in the file but does **not** gate on them. Nothing
rewrites CC's own recall, and nothing needs to: `rotate-log.py` keeps the newest ~400 lines at
every cycle close, so the backlog leaves on its own inside two days.

Exit 0 on success, 1 on a malformed entry or a failed `--check`. Prints the line it wrote.
"""
import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

for _s in (sys.stdout, sys.stderr):          # a refusal is read on stderr, arrows and all
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

LOG = os.path.join(V.ROOT, "logs", "log.md")

# STATUS.md -> *The `log.md` entry*. Counted over the assembled line, stamp and revert
# hint included, because that is what a reader reads. The form's own worked example is
# 19 words, and a pass that needs more is writing a commit body in the wrong file.
ENTRY_WORD_CAP = 40

# Same two entry forms rotate-log.py recognises, anchored left so a quoted example inside
# an entry body cannot open a phantom entry.
ENTRY_RE = re.compile(r"^(?:## )?\d{4}-\d{2}-\d{2} \d{2}:\d{2}\b")
AT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})$")


def stamp(at=None):
    """UTC, to the minute. Read here so no caller ever formats one."""
    now = dt.datetime.now(dt.timezone.utc)
    if at:
        m = AT_RE.match(at.strip())
        if not m:
            raise ValueError(f"--at must be YYYY-MM-DDTHH:MM (UTC), got {at!r}")
        given = f"{m.group(1)} {m.group(2)}:{m.group(3)}"
        # A measurement is of something that already happened. Ahead of now it is a
        # narration, or a local clock read as UTC -- refuse rather than record it.
        if dt.datetime.strptime(given, "%Y-%m-%d %H:%M") > now.replace(tzinfo=None):
            raise ValueError(
                f"--at {given} is ahead of now ({now:%Y-%m-%d %H:%M}Z) — a measured time "
                f"cannot be in the future. Local clock read as UTC (machine is UTC+1), or "
                f"an estimate? Drop --at and the clock is read here.")
        return given
    return now.strftime("%Y-%m-%d %H:%M")


BANNED_PASS = {"decision", "decisions", "agent", "sub-agent", "slice", "batch"}


def pass_field(name):
    """`**WIKI-STATUS**` from `wiki status`, and a refusal for what earns no line at all."""
    bare = name.strip().strip("*").strip()
    if bare.lower().rstrip("s") in {b.rstrip("s") for b in BANNED_PASS}:
        raise ValueError(
            f"`{bare}` is not a process, so it earns no log line (STATUS.md → *The `log.md` "
            f"entry*). A ruling about how a pass should behave goes in the commit body with "
            f"the diff that carries it; a call about one record rides the pass's own line; a "
            f"slice returns to its parent, which writes the run's single entry.")
    return "**" + re.sub(r"[\s_]+", "-", bare).upper() + "**"


def compose(pass_name, changed, revert, at=None):
    parts = [stamp(at), pass_field(pass_name), changed.strip()]
    hint = revert.strip()
    if hint.lower().startswith("revert:"):
        hint = hint[len("revert:"):].strip()
    parts.append(f"revert: {hint}")
    line = " · ".join(parts)
    if "\n" in line or "\r" in line:
        raise ValueError("an entry is one line — no newlines. Detail goes in git.")
    n = len(line.split())
    if n > ENTRY_WORD_CAP:
        raise ValueError(
            f"the entry runs {n} words against a cap of {ENTRY_WORD_CAP}. Counts and "
            f"objects, not sentences — the reasoning belongs in the commit body, with "
            f"the diff it explains. Cut it, or split one entry per thing changed.")
    return line


def insert_at_top(line):
    """Put the entry above the newest existing one, below the header block."""
    with open(LOG, encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)

    nl = "\r\n" if lines and lines[0].endswith("\r\n") else "\n"
    first = next((i for i, ln in enumerate(lines) if ENTRY_RE.match(ln)), len(lines))
    lines.insert(first, line + nl)

    with open(LOG, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(lines))


MISPLACED_HOURS = 6


def check(tolerance_hours=MISPLACED_HOURS):
    """Both defects are detectable after the fact, whoever wrote the line.

    A stamp in the future is a local clock read where UTC was wanted, and that one is exact:
    any minute past now is wrong.

    Position is deliberately *not* exact. Several agents writing within the same minute
    invert each other constantly and it costs nothing — `rotate-log.py` truncates from the
    bottom, so what matters is an entry landing a long way from where it belongs, which is
    what ate the 2026-08-20 sweep lines (appended to the foot of a file whose foot was ten
    days old). So an inversion is reported only past `tolerance_hours`; below it, it is
    concurrency, not misplacement.
    """
    with open(LOG, encoding="utf-8") as fh:
        entries = [(i + 1, ln[3:] if ln.startswith("## ") else ln)
                   for i, ln in enumerate(fh.read().split("\n")) if ENTRY_RE.match(ln)]

    def when(line):
        return dt.datetime.strptime(line[:16], "%Y-%m-%d %H:%M")

    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    future = [(n, ln[:16]) for n, ln in entries if when(ln) > now]
    overlong = [(n, len(ln.split())) for n, ln in entries if len(ln.split()) > ENTRY_WORD_CAP]

    misplaced = []
    for k, (n, ln) in enumerate(entries):
        if not k:
            continue
        gap = (when(ln) - when(entries[k - 1][1])).total_seconds() / 3600
        if gap > tolerance_hours:
            misplaced.append((n, ln[:16], entries[k - 1][1][:16], gap))

    if overlong:
        # Counted, never gated, and never listed in full. `compose()` refuses a new one, so
        # what is here is a backlog with an expiry: rotate-log.py keeps ~400 lines, so it
        # clears itself inside two days. A check that printed 324 unfixable findings would
        # be skimmed by its second run, which is the failure a check exists to prevent.
        worst = max(w for _, w in overlong)
        print(f"  {len(overlong)} of {len(entries)} entries exceed the {ENTRY_WORD_CAP}-word "
              f"cap, longest {worst} — not a defect to fix: log-append refuses new ones and "
              f"rotate-log.py ages these out. Reported, not gated.")

    if not future and not misplaced:
        print(f"logs/log.md: {len(entries)} entries, newest first within {tolerance_hours}h, "
              f"no stamp ahead of {now:%Y-%m-%d %H:%M}Z — clean.")
        return 0

    for n, s in future:
        print(f"  line {n}: stamped {s} — ahead of now ({now:%Y-%m-%d %H:%M}Z); "
              f"a local clock read as UTC?")
    for n, s, prev, gap in misplaced:
        print(f"  line {n}: {s} sits below {prev}, {gap:,.0f}h out of place — the file is "
              f"newest-at-top and rotate-log.py truncates from the bottom")
    print(f"logs/log.md: {len(future)} future-stamped, {len(misplaced)} misplaced by more "
          f"than {tolerance_hours}h, of {len(entries)} entries.")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("pass_name", metavar="PASS", nargs="?",
                    help="the process name, or 'decision' for a process-level ruling")
    ap.add_argument("changed", metavar="WHAT-CHANGED", nargs="?",
                    help="telegraphic — counts and objects, not sentences")
    ap.add_argument("revert", metavar="REVERT", nargs="?",
                    help="what to undo: a commit, a file, a register line. Wrote nothing -> 'none'")
    ap.add_argument("--at", help="UTC 'YYYY-MM-DDTHH:MM' — a measured time, never an estimate")
    ap.add_argument("--check", action="store_true",
                    help="verify log.md is newest-first with no future stamps; write nothing")
    ap.add_argument("--tolerance", type=float, default=MISPLACED_HOURS, metavar="HOURS",
                    help=f"--check: hours of inversion to treat as concurrency (default {MISPLACED_HOURS})")
    a = ap.parse_args()

    if not os.path.exists(LOG):
        print("logs/log.md: not present — nothing to append to.", file=sys.stderr)
        return 1

    if a.check:
        return check(a.tolerance)

    if not (a.pass_name and a.changed and a.revert):
        ap.error("PASS, WHAT-CHANGED and REVERT are all required (or use --check)")

    try:
        line = compose(a.pass_name, a.changed, a.revert, a.at)
    except ValueError as e:
        print(f"log-append: {e}", file=sys.stderr)
        return 1

    insert_at_top(line)
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
