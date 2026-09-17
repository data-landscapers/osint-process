#!/usr/bin/env python3
"""Compute the wiki status counts and gates, print them, and write logs/status.md.

`wiki status` runs this (calculate + write). `display status` just reads
logs/status.md, which is why this script always writes the file.
Definitions live in STATUS.md; this is only their mechanisation.
"""
import json, os, re, subprocess, sys, datetime, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X = "X:\\" if os.name == "nt" else "/x/"

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=900).stdout
    except Exception:
        return ""

def count_lines(path, pattern):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for ln in f if re.match(pattern, ln))
    except OSError:
        return 0

def count_notes(path, pattern):
    """Open notes in an exchange file, counted once each.

    The house shape opens a note twice - `### 141. [ACT] <title>` and then `**141** [ACT]
    (date) - <summary>` - and NOTE_ENTRY matches both, so every open note counted as two
    and this line reported double. A repeat of the number just seen is the same note
    continuing. The same defect was fixed the same night in `lint-deterministic.py`'s
    `read_xchg_notes`, which truncated each note's body at its own second opening."""
    try:
        seen, last = 0, None
        with open(path, encoding="utf-8", errors="replace") as f:
            for ln in f:
                m = re.match(pattern, ln)
                if not m:
                    continue
                num = re.search(r"[0-9]+", m.group(0)).group(0)
                if num != last:
                    seen += 1
                last = num
        return seen
    except OSError:
        return 0

def awaiting_ingest():
    try:
        return len([n for n in os.listdir(os.path.join(ROOT, "new"))
                    if not n.startswith(".") and "readme" not in n.lower()])
    except OSError:
        return 0

def contradictions():
    return len([p for p in glob.glob(os.path.join(ROOT, "reviews/contradictions/open/*.md"))
                if "readme" not in os.path.basename(p).lower()])

def acquisitions():
    path = os.path.join(ROOT, "reviews/acquisitions.md")
    n, inblock = 0, False
    try:
        for ln in open(path, encoding="utf-8", errors="replace"):
            if ln.startswith("## Open items"):
                inblock = True; continue
            if ln.startswith("## "):
                inblock = False
            if inblock and re.match(r"^\s*[-*] ", ln):
                n += 1
    except OSError:
        pass
    return n

def sweep_gate():
    """Manifest or drop-log dated later than the folder's high-water mark."""
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, "sweep", "*"))):
        if not os.path.isdir(d):
            continue
        # Only `daily` and `off-list` keep a high-water mark; the other folders'
        # state.json was deleted 2026-07-30 (intake.md §7) and the cycle log is
        # their record, so they have no mark an artefact could run ahead of.
        sf = os.path.join(d, "state.json")
        if not os.path.exists(sf):
            continue
        try:
            mark = json.load(open(sf, encoding="utf-8")).get("last_run_completed_utc", "") or ""
        except Exception:
            mark = ""
        dated = sorted(os.path.basename(p) for p in
                       glob.glob(os.path.join(d, "manifest-*.md")) + glob.glob(os.path.join(d, "drop-log-*.csv")))
        if not dated:
            continue
        newest = max(re.findall(r"\d{4}-\d{2}-\d{2}", " ".join(dated)) or [""])
        # Artefact names carry the LOCAL date; the mark is UTC. Compare like with
        # like, or every run closing after local midnight reads as interrupted.
        mark_local = mark[:10]
        if mark:
            try:
                mark_local = (datetime.datetime.strptime(mark, "%Y-%m-%dT%H:%M:%SZ")
                              .replace(tzinfo=datetime.timezone.utc)
                              .astimezone()
                              .strftime("%Y-%m-%d"))
            except Exception:
                pass
        if newest and newest > mark_local:
            out.append(f"{os.path.basename(d)}: artefact {newest} ahead of mark {mark_local}")
    return out

NOTE_ENTRY = r"^(?:\*\*[0-9]+\*\*[ (]|#{2,3} [0-9]+[.\u00a0 ])"

counts = {
    "contradictions": contradictions(),
    "acquisitions": acquisitions(),
    "awaiting ingest": awaiting_ingest(),
    "housekeeping": count_lines(X + "housekeeping-jobs.md", r"^[0-9]+\. "),
    # The fifth queue, and the last to reach this line (2026-09-08). It filled for twelve days
    # to 77 lines before anyone looked, because nothing counted it anywhere a pass would see:
    # `RULES.md` is triggered by hand and its own concurrency rule keeps it out of the cycle,
    # so the count on this line is the whole of what makes it visibly due.
    "rule-candidates": count_lines(os.path.join(ROOT, "reviews", "rule-candidates.md"), r"^- "),
    # Both note files have carried two entry shapes - the original bold lead `**N** (date)`
    # and the `### N. [TAG]` heading their writers moved to - so match either. Pinning to one
    # is how osint-notes read 0 against a real queue of four (found by Bill, 2026-08-24): the
    # pattern went stale when the shape changed, and a zero looks exactly like an empty queue.
    "osint-notes": count_notes(X + "notes-for-osint.md", NOTE_ENTRY),
    "corpus-notes": count_notes(X + "notes-for-corpus.md", NOTE_ENTRY),
    "fetch": count_lines(X + "fetch-list.md", r"^[0-9]+[a-z]?\. "),
    "commits": len([l for l in sh("git status --porcelain").splitlines() if l.strip()]),
}
# `decisions logged` is a per-job tally, not a queue (STATUS.md) - the count of process-level
# `decision` lines THIS job wrote (never per-item admit/drop/merge calls, which carry no line
# of their own). The script cannot know which job is running, so it cannot compute it: what it
# printed until 2026-08-24 was every decision line surviving log rotation (162 that day), which
# reads as a queue and is wrong by two orders of magnitude. It printed the literal `NN` after
# that, for the pass to fill - and on 2026-09-08 that placeholder reached Bill on a close line,
# because a field nobody is forced to fill is a field that gets pasted through. So the pass
# passes its own count in and the default is the ordinary case, zero. Every other field on the
# line is a live count and is the script's.
counts["decisions logged"] = next(
    (int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--decisions=")), 0)
tally = " ; ".join(f"{k} - {v}" for k, v in counts.items())

# --- gates ---
gates = []
fin = [l for l in sh("python scripts/finance-compile-scope.py").split() if l.strip()]
if fin:
    gates.append(f"finance-compile baseline: {len(fin)} place(s) — {' '.join(fin[:12])}")

pw = os.path.join(ROOT, "logs/ingest-pending-writes.md")
if os.path.getsize(pw) if os.path.exists(pw) else 0:
    # The file's real shape is a markdown bullet per delta, em-dash separated:
    # "- `subject` — [[source-slug]] — what Phase B writes". The 2026-08-26 repair
    # encoded a pipe-delimited shape the file has never carried, so this gate reported
    # "0 page-writes across 0 source(s)" against every live queue since - and a zero is
    # exactly what an empty queue looks like, so the staleness was invisible by
    # construction, the same failure it was written to fix. (2026-09-09.)
    _delta = re.compile(r"^- `[a-z][a-z0-9.]*`\s+—\s+\[\[([^\]]+)\]\]")
    _pw_lines = open(pw, encoding="utf-8").read().splitlines()
    _hits = [m for m in (_delta.match(l) for l in _pw_lines) if m]
    rows = len(_hits)
    srcs = len({m.group(1).strip() for m in _hits})
    gates.append(f"pending writes from ingest: {rows} page-writes across {srcs} source(s) (Phase B outstanding)")

sg = sweep_gate()
if sg:
    gates.append("interrupted sweep: " + "; ".join(sg))

if "--fast" not in sys.argv:
    unc = sh("python scripts/uncited-sources.py --recent 1")
    m = re.search(r"cited NOWHERE:\s+([\d,]+)", unc)
    if m and m.group(1).replace(",", "") != "0":
        gates.append(f"sources uncited (last 1 day of admits): {m.group(1)}")

stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
body = [
    "# status — last computed snapshot",
    "",
    "*Written by `scripts/status.py` whenever status is calculated (`wiki status`); read verbatim by `display status`. Counts and gates are defined in `STATUS.md` — this file is only their last reading, and is stale the moment a pass runs.*",
    "",
    f"**As of {stamp} UTC** (git HEAD `{sh('git rev-parse --short HEAD').strip()}`)",
    "",
    "```",
    tally,
    "```",
    "",
    "## Gates",
    "",
]
body += [f"- {g}" for g in gates] if gates else ["*None open.*"]
body += ["", "## Newest log line", "", sh("head -7 logs/log.md | tail -1").strip() or "*none*", ""]

with open(os.path.join(ROOT, "logs/status.md"), "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(body))

print(tally)
for g in gates:
    print("gate - " + g)
