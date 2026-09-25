#!/usr/bin/env python3
r"""
cycle-manifest.py — write `cycle-manifest.json`, the one thing CORPUS reads about a run.

**Why it exists.** CORPUS compiles and publishes from `O:\`, the mirror of this vault, and
it needs facts a copy of the tree does not state: which commit it is holding, when
collection stopped, and how much arrived. Until now it established them by parsing OSINT's
`logs/ingested_log.md` and `logs/sweep-cycle_log.md` — prose files written for a human
reader, whose shape has changed under it more than once, and which the interface rule puts
out of bounds anyway. This file states them instead, as data, once per close.

**`logs/ingested_log.md` retired 2026-09-07** (Bill — it was losing rows to concurrent slice
writes). The `collection` block survives it: CORPUS reads `collection.sweep_closed` directly
with no fall-back behind it (`rotation.newest_close.end` is not a substitute — the rotation's
jobs finish hours after collection stops, so publishing it as *Last updated* would overstate
coverage, which the byline may never do — notes-for-osint 132). Rather than parse a heading
back out of a file about to disappear, the pass that closes ingest now **stamps its own
measured values** with `--stamp`, into `logs/collection-stamp.json` — a single overwritten
object, not a rolling log, so it carries no retention rule of its own. `--pass` reads it at
the next close exactly as it read the heading before: same three keys, same local-time
format, same place in the schema.

**Where it sits, and why not in `logs/`.** The repository root, so it is on the mirror at
`O:\cycle-manifest.json` and inside nothing CORPUS may not read. It is git-ignored, like
`logs/status.md`: it is written **after** the run's final commit, so that `head` names the
commit the mirror actually carries, which is the assertion worth having and cannot be made
by a file committed inside that commit. Nothing is lost — every field is derived from a
tracked file or from git.

**What it does not carry.** OSINT's own queues and gates — housekeeping, fetch, the note
counts, an outstanding Phase B. They are the state of OSINT's work, not facts about the
evidence, and a manifest that carried them would re-open the reading the interface rule
closed. `awaiting ingest` is the exception and is here because it is a statement about
evidence not yet visible in `raw/`.

**Counts are given, never inferred.** The pass that measured them passes them in; a pass
that gives none writes none. Re-deriving an ingest tally by parsing the prose heading it was
written into would move the forensics rather than retire them, and a wrong count is worse
than an absent one — an absent one is visible.

**Schema 2 (2026-09-17, strategic review 4 R4): the `usage` block.** With `--usage`, the
per-stage plan-usage readings `usage-log.py --stage` buffered through the night in
`logs/usage-stages.jsonl` are written as `usage`, an object keyed by stage in the order
taken — `{"start": {"time_utc", "seven_day", "five_hour"}, "notes": {...}, ...}` — so a
stage's cost is its reading less the one before it. A stage read twice keeps its last
reading. Without `--usage`, or with an empty buffer, there is no `usage` block: an absent
block is visible, where a block borrowed from another pass's night would be wrong. Only the
sweep cycle passes it; CORPUS's reader accepts schemas 1 and 2 (register R07).

**Schema 3 (2026-09-25, strategic review 5 R70): the `drops` block.** With `--drops`, the
night's drops per sweep per code, from data files rather than prose: every sweep's own
`sweep/*/…drop-log-*{night}*.csv` (`reason` column) as `sweep`, and ingest's coded drops
(`sweep/ingest/drop-log-*.csv`, R69) whose `sweep_batch` is dated the night as `ingest`,
beside `admitted` — the `raw/` records carrying such a `sweep_batch`. `ingest_drop_rate` is
ingest drops over ingest drops plus admissions, per sweep: the number review 6 reads. A sweep
is its batch label less the date (`domestic-finance-*` is `domestic`, the folder its drop-logs
live in). The night is the collection stamp's `ingest_started` date unless `--night` names
one. Where no ingest drop-log carries the night, `ingest` and the rate are absent, not zero —
a night before R69 did not code its drops.

**The `hygiene` block (2026-09-25, strategic review 5 R83; additive, schema 3 unchanged).** With
`--hygiene`, what the night's writers left for a cleaner: `housekeeping_registered`, the rise
in `X:\housekeeping-jobs.md`'s `NEXT JOB NUMBER`, and `words_trimmed` (with
`pages_rewritten`), summed over the `logs/phaseb-trims.csv` rows Phase B's over-line rewrites
added (R81). Both are measured since the previous manifest, whose `hygiene` block carries the
two counters, and both should read near zero. Only the sweep cycle passes it, so "since the
previous manifest" is the night. The first manifest to carry the block has nothing to
compare with and writes the counters alone.

Usage:
  python scripts/cycle-manifest.py --pass "sweep cycle" --usage \
      --count items_in=294 --count admitted=185 --count dropped=108
  python scripts/cycle-manifest.py --stamp --sweep-closed "2026-09-07 19:58" \
      --ingest-started "2026-09-07 20:08" --last-admission "2026-09-07 20:36"
  python scripts/cycle-manifest.py --check      # exists, parses, head matches local HEAD
  python scripts/cycle-manifest.py --print      # write nothing, show what would be written

`--stamp` writes only `logs/collection-stamp.json`, never `cycle-manifest.json` — it is what
`INGEST.md`'s close calls, whichever pass wrapped it (sweep cycle, bulletin, `update wiki`,
or standalone), so the values survive to whichever pass next mirrors and writes the manifest.
All three are required together, local machine-clock time (`intake.md` §6a's shape,
unconverted — see `rotation()`'s note), and a value ahead of local now is refused: a
measurement is of something that already happened, the same rule `log-append.py --at` keeps.

Exit 0 on success; 1 if `--check` fails or `--stamp` is given a malformed or future value.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANIFEST = os.path.join(V.ROOT, "cycle-manifest.json")
CYCLE_LOG = os.path.join(V.ROOT, "logs", "sweep-cycle_log.md")
STAMP = os.path.join(V.ROOT, "logs", "collection-stamp.json")
STAGES = os.path.join(V.ROOT, "logs", "usage-stages.jsonl")
SWEEP_DIR = os.path.join(V.ROOT, "sweep")
SCHEMA = 3
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
CODE_RE = re.compile(r"[a-z]+(-[a-z]+)*")

STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")


def git(*args):
    try:
        r = subprocess.run(["git", "-C", V.ROOT, *args], capture_output=True,
                           text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


def utc(iso):
    """A git ISO-8601 stamp with offset, as `YYYY-MM-DD HH:MM` UTC."""
    if not iso:
        return None
    try:
        return (datetime.datetime.fromisoformat(iso)
                .astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"))
    except ValueError:
        return None


def rotation():
    """The rotation table as rows, plus the day that closed most recently.

    The header defines the columns and this reads them by name, so a column added or moved
    in `logs/sweep-cycle_log.md` does not silently shift the values — a rename that this
    cannot find leaves the field absent rather than wrong.

    **`start`/`end` are local machine-clock time, copied out of `logs/sweep-cycle_log.md`
    unconverted — not UTC, despite sitting in the same document as `written_utc` and
    `head_committed_utc`, which are.** notes-for-osint 55 raised exactly this ambiguity;
    settled here rather than by converting, since a conversion is a process change and
    `CLAUDE.md`'s process freeze (to 2026-09-27) holds it. A reader wanting UTC applies the
    machine's known offset itself in the meantime."""
    try:
        lines = open(CYCLE_LOG, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return None
    head, rows = None, []
    for ln in lines:
        if not ln.strip().startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("- :"):          # the separator rule
            continue
        if head is None:
            head = [c.lower() for c in cells]
            continue
        rows.append(dict(zip(head, cells)))
    if not rows:
        return None

    def cell(row, name):
        v = (row.get(name) or "").strip()
        return v or None

    days = []
    for r in rows:
        days.append({"day": cell(r, "day"), "jobs": [j.strip() for j in
                                                     (cell(r, "jobs") or "").split(",") if j.strip()],
                     "start": cell(r, "start"), "end": cell(r, "end"),
                     "duration": cell(r, "duration"),
                     "skipped": bool(cell(r, "skip")),
                     "in_progress": bool(cell(r, "new-start"))})
    closed = [d for d in days if d["end"]]
    newest = max(closed, key=lambda d: d["end"]) if closed else None
    return {"days": len(days), "newest_close": newest,
            "in_progress": [d["day"] for d in days if d["in_progress"]]}


def collection():
    """The most recently stamped collection window, from `logs/collection-stamp.json`.

    A single overwritten object, not a rolling log — the newest `--stamp` call is always the
    whole of it, so there is no heading to find and no retention rule to run. Read exactly as
    written, in the same local machine-clock time `rotation()` carries; see its note."""
    try:
        with open(STAMP, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError):
        return None
    return {k: d.get(k) for k in ("last_admission", "sweep_closed", "ingest_started")}


def write_stamp(sweep_closed, ingest_started, last_admission):
    """Validate and write `logs/collection-stamp.json`. Raises ValueError, writes nothing, on
    a malformed or future value — the two defects `log-append.py --check` used to catch after
    the fact in `ingested_log.md`'s headers; catching them at write time instead means there
    is nothing left to audit."""
    values = {"sweep_closed": sweep_closed, "ingest_started": ingest_started,
              "last_admission": last_admission}
    now = datetime.datetime.now()
    for k, v in values.items():
        if not v or not STAMP_RE.match(v.strip()):
            raise ValueError(f"--{k.replace('_', '-')} must be 'YYYY-MM-DD HH:MM', got {v!r}")
        when = datetime.datetime.strptime(v.strip(), "%Y-%m-%d %H:%M")
        if when > now:
            raise ValueError(
                f"--{k.replace('_', '-')} {v.strip()} is ahead of local now "
                f"({now:%Y-%m-%d %H:%M}) — a measured time cannot be in the future.")
        values[k] = v.strip()
    with open(STAMP, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(values, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return values


def awaiting_ingest():
    try:
        return len([n for n in os.listdir(os.path.join(V.ROOT, "new"))
                    if not n.startswith(".") and "readme" not in n.lower()])
    except OSError:
        return None


def raw_sources():
    """Source pages in `raw/` — a cheap integrity signal against a half-copied mirror."""
    n = 0
    for _, _, files in os.walk(os.path.join(V.ROOT, "raw")):
        n += sum(1 for f in files if f.endswith(".md"))
    return n


def usage_block():
    """The night's buffered stage readings, keyed by stage in the order taken; None if none.

    A malformed line is skipped rather than failing the close — the block is a measurement
    of cost, and the manifest's other blocks are what CORPUS cannot do without."""
    block = {}
    try:
        with open(STAGES, encoding="utf-8") as fh:
            for ln in fh:
                try:
                    r = json.loads(ln)
                    stage = str(r["stage"])
                except (ValueError, KeyError, TypeError):
                    continue
                block.pop(stage, None)
                block[stage] = {"time_utc": r.get("time_utc"),
                                "seven_day": r.get("seven_day"),
                                "five_hour": r.get("five_hour")}
    except OSError:
        return None
    return block or None


def sweep_of(batch):
    """`country-deep-2026-09-24` -> (`country-deep`, `2026-09-24`); the date is the last one."""
    dates = DATE_RE.findall(batch or "")
    if not dates:
        return None, None
    key = batch[:batch.rfind(dates[-1])].rstrip("-")
    key = re.sub(r"-[A-Z]{3}(-\d{4})?$", "", key)            # per-country, per-FY batches
    if key.startswith("domestic-finance"):
        key = "domestic"
    return key or None, dates[-1]


def drops_block(night):
    """Drops per sweep per code for one night; see the module note (schema 3)."""
    import csv
    import glob
    sweeps = {}

    def entry(k):
        return sweeps.setdefault(k, {"sweep": {}, "ingest": {}, "admitted": 0})

    for path in glob.glob(os.path.join(SWEEP_DIR, "*", f"*drop-log-*{night}*.csv")):
        folder = os.path.basename(os.path.dirname(path))
        if folder in ("ingest", "archive"):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace", newline="") as fh:
                for r in csv.DictReader(fh):
                    code = (r.get("reason") or "").strip() or "uncoded"
                    if not CODE_RE.fullmatch(code):
                        code = "malformed"        # a mis-quoted row shifts free text here
                    d = entry(folder)["sweep"]
                    d[code] = d.get(code, 0) + 1
        except OSError:
            continue

    coded = False
    for path in glob.glob(os.path.join(SWEEP_DIR, "ingest", "drop-log-*.csv")):
        try:
            with open(path, encoding="utf-8", errors="replace", newline="") as fh:
                for r in csv.DictReader(fh):
                    key, day = sweep_of(r.get("sweep_batch"))
                    if day != night:
                        continue
                    coded = True
                    d = entry(key)["ingest"]
                    code = r.get("reason") or "uncoded"
                    d[code] = d.get(code, 0) + 1
        except OSError:
            continue

    batch_re = re.compile(r"^sweep_batch:\s*[\"']?([^\"'\r\n]+)", re.M)
    for root, _, files in os.walk(os.path.join(V.ROOT, "raw")):
        for f in files:
            if not f.endswith(".md"):
                continue
            try:
                with open(os.path.join(root, f), encoding="utf-8", errors="replace") as fh:
                    head = fh.read(3000)
            except OSError:
                continue
            m = batch_re.search(head)
            if m and night in m.group(1):
                key, day = sweep_of(m.group(1).strip())
                if day == night:
                    entry(key)["admitted"] += 1

    for k, e in sweeps.items():
        for side in ("sweep", "ingest"):
            e[side] = dict(sorted(e[side].items(), key=lambda kv: (-kv[1], kv[0])))
        if not coded:
            del e["ingest"]
            continue
        n = sum(e["ingest"].values())
        e["ingest_drop_rate"] = round(n / (n + e["admitted"]), 3) if n + e["admitted"] else None
    return {"night": night, "ingest_coded": coded, "sweeps": dict(sorted(sweeps.items()))}


HOUSEKEEPING = "X:\\housekeeping-jobs.md" if os.name == "nt" else "/x/housekeeping-jobs.md"
TRIMS = os.path.join(V.ROOT, "logs", "phaseb-trims.csv")


def hygiene_block(prev):
    """What the writers left for a cleaner since the previous manifest (R83); see the note.

    Both figures are deltas of a counter, never a parse of prose: the register's
    `NEXT JOB NUMBER` line (numbers are never reused, so its rise is jobs registered) and the
    row count of `logs/phaseb-trims.csv` (R81), whose rows past the previous count are summed
    as `before - after`. The previous manifest carries both counters; with none to compare
    against, the deltas are absent rather than zero."""
    nxt = None
    try:
        with open(HOUSEKEEPING, encoding="utf-8", errors="replace") as fh:
            m = re.search(r"^## NEXT JOB NUMBER:\s*(\d+)", fh.read(), re.M)
            nxt = int(m.group(1)) if m else None
    except OSError:
        pass
    rows = []
    try:
        import csv
        with open(TRIMS, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        pass
    b = {"housekeeping_next": nxt, "trims_rows": len(rows)}
    p = (prev or {}).get("hygiene") or {}
    if nxt is not None and isinstance(p.get("housekeeping_next"), int):
        b["housekeeping_registered"] = nxt - p["housekeeping_next"]
    if isinstance(p.get("trims_rows"), int) and p["trims_rows"] <= len(rows):
        new = rows[p["trims_rows"]:]
        b["words_trimmed"] = sum(int(r["before"]) - int(r["after"]) for r in new
                                 if r.get("before", "").isdigit() and r.get("after", "").isdigit())
        b["pages_rewritten"] = len(new)
    if prev:
        b["since"] = prev.get("written_utc")
    return b


def build(pass_name, counts, usage=False, night=None, hygiene=False):
    head = git("rev-parse", "HEAD")
    m = {
        "schema": SCHEMA,
        "written_utc": datetime.datetime.now(datetime.timezone.utc)
                       .strftime("%Y-%m-%d %H:%M"),
        "pass": pass_name,
        "head": head or None,
        "head_committed_utc": utc(git("show", "-s", "--format=%cI", "HEAD")),
        "collection": collection(),
        "rotation": rotation(),
        "counts": dict(counts, awaiting_ingest=awaiting_ingest(),
                       raw_sources=raw_sources()),
    }
    if usage:
        block = usage_block()
        if block:
            m["usage"] = block
    if night:
        m["drops"] = drops_block(night)
    if hygiene:
        m["hygiene"] = hygiene_block(read())
    return m


def read():
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def check():
    """Is the manifest present, readable, and describing the commit that is here?

    A manifest naming an older commit is the failure this exists to make visible: CORPUS
    would read it as a statement about the tree it is holding, and it would be a statement
    about a previous one."""
    m = read()
    if m is None:
        print("cycle-manifest.json: absent or unreadable — CORPUS has nothing to read "
              "about this run. Write it at the close, after the final commit.")
        return 1
    if m.get("schema") != SCHEMA:
        print(f"cycle-manifest.json: schema {m.get('schema')} against {SCHEMA} — "
              "the reader and the writer disagree about the shape.")
        return 1
    local = git("rev-parse", "HEAD")
    if m.get("head") != local:
        print(f"cycle-manifest.json: names {str(m.get('head'))[:9]} against local "
              f"{local[:9]} — it describes an earlier commit. Rewrite it after the "
              "final commit, then mirror.")
        return 1
    print(f"cycle-manifest.json: HEAD {local[:9]}, written {m.get('written_utc')} UTC, "
          f"pass '{m.get('pass')}' — current.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--pass", dest="pass_name",
                    help="the process name from STATUS.md's announce banner")
    ap.add_argument("--count", action="append", default=[], metavar="KEY=N",
                    help="a count this pass measured; repeatable")
    ap.add_argument("--usage", action="store_true",
                    help="write the night's per-stage usage readings as the `usage` block")
    ap.add_argument("--hygiene", action="store_true",
                    help="write housekeeping_registered and words_trimmed since the last manifest")
    ap.add_argument("--drops", action="store_true",
                    help="write the night's drops per sweep per code as the `drops` block")
    ap.add_argument("--night", metavar="YYYY-MM-DD",
                    help="the night --drops counts (default: the stamp's ingest_started date)")
    ap.add_argument("--check", action="store_true",
                    help="exists, parses, and names the local HEAD")
    ap.add_argument("--print", dest="show", action="store_true",
                    help="write nothing; print what would be written")
    ap.add_argument("--stamp", action="store_true",
                    help="write only logs/collection-stamp.json from the three flags below")
    ap.add_argument("--sweep-closed", metavar="YYYY-MM-DD HH:MM",
                    help="local time collection stopped (--stamp only)")
    ap.add_argument("--ingest-started", metavar="YYYY-MM-DD HH:MM",
                    help="local time this close's Phase A began (--stamp only)")
    ap.add_argument("--last-admission", metavar="YYYY-MM-DD HH:MM",
                    help="local time this close's own run-log line (--stamp only)")
    a = ap.parse_args()

    if a.check:
        return check()

    if a.stamp:
        try:
            v = write_stamp(a.sweep_closed, a.ingest_started, a.last_admission)
        except ValueError as e:
            print(f"cycle-manifest --stamp: {e}", file=sys.stderr)
            return 1
        print(f"logs/collection-stamp.json: sweep_closed {v['sweep_closed']}, "
              f"ingest_started {v['ingest_started']}, last_admission {v['last_admission']}.")
        return 0

    if not a.pass_name:
        print("cycle-manifest: --pass is required — a manifest that cannot say which "
              "pass wrote it cannot be read as a statement about one.", file=sys.stderr)
        return 2

    counts = {}
    for pair in a.count:
        if "=" not in pair:
            print(f"cycle-manifest: --count {pair} is not KEY=N", file=sys.stderr)
            return 2
        k, v = pair.split("=", 1)
        counts[k.strip()] = int(v) if v.strip().lstrip("-").isdigit() else v.strip()

    night = None
    if a.drops:
        night = a.night or ((collection() or {}).get("ingest_started") or "")[:10]
        if not DATE_RE.fullmatch(night or ""):
            print("cycle-manifest: --drops needs --night YYYY-MM-DD or a stamped "
                  "ingest_started", file=sys.stderr)
            return 2
    m = build(a.pass_name, counts, usage=a.usage, night=night, hygiene=a.hygiene)
    text = json.dumps(m, indent=1, ensure_ascii=False) + "\n"
    if a.show:
        print(text, end="")
        return 0
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    c = m["collection"] or {}
    print(f"cycle-manifest.json: HEAD {str(m['head'])[:9]}, pass '{a.pass_name}', "
          f"sweep_closed {c.get('sweep_closed') or 'absent'}, "
          f"{m['counts']['raw_sources']:,} sources in raw/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
