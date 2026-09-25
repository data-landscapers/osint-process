#!/usr/bin/env python3
"""trim-job.py — standing. Finish-line check, and close, for a page-trim housekeeping job.

Written 2026-09-24 for housekeeping jobs 190-202 (the append-log trim), worked
under `wiki/append-log-trim.md`. Reads the job's page list from its entry in
`X:\\housekeeping-jobs.md` (every `` `slug` (N,NNN) `` pair).

usage (from the repo root):
  python scripts/trim-job.py <N>                              check only
  python scripts/trim-job.py <N> --commit "<slice label>" <calls-file>

The check runs `trim-verify.py`, lint #8 (--all), #4 and #12, reflow, and counts
the `sources:` slugs added. It fails if the verifier fails, any page still reads
append-log or unsectioned, a page under the classify line still has 40% or more
of its headings dated, lint #4/#12 hit a page, or reflow finds wrapping.

--commit, only on a clean check: one BACKLOG line via `log-append.py`, stage the
pages and the log, `assert-containment.py --stage housekeeping`, commit (body:
page list, lint reading, words, sources added, then the calls file — the
session's corrections and conflicts, written from the agents' reports), push,
then `housekeeping-strike.py`. Mirror afterwards by hand.
"""
import argparse
import datetime
import os
import pathlib
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
PY = sys.executable
TEMP = pathlib.Path(os.environ.get("TEMP", "."))


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, encoding="utf-8", errors="replace")


def check(n):
    reg = pathlib.Path("X:/housekeeping-jobs.md").read_text(encoding="utf-8")
    m = re.search(rf"^{n}\. (.*)$", reg, re.M)
    if not m:
        print(f"trim-job: no open entry {n} in X:\\housekeeping-jobs.md")
        sys.exit(2)
    entry = m.group(1)
    pages = re.findall(r"`([a-z0-9-]+--[a-z0-9-]+)` \([\d,]+\)", entry)
    if not pages:
        print(f"trim-job: entry {n} names no `slug` (N,NNN) pages")
        sys.exit(2)
    # the registered total is the largest word figure in the bold title: a title can name the band
    # first ("between 2,000 and 2,500 words, 58,136 words"), which the first match would take
    title = entry.split(".**", 1)[0]
    before = max(re.findall(r"([\d,]+) words", title), key=lambda s: int(s.replace(",", "")))
    r = {"pages": pages, "before": before, "fail": []}
    print(f"job {n}: {len(pages)} pages, registered {r['before']} words")
    v = run(PY, "scripts/trim-verify.py", *pages)
    if v.returncode:
        r["fail"].append("verifier")
        print(v.stdout)
    else:
        print("verifier: all OK")
    dated = {l.split(":")[0]: re.search(r"sections (\d+), dated (\d+)", l).groups() for l in v.stdout.splitlines() if " words " in l}
    l8 = run(PY, "scripts/lint-deterministic.py", "--check", "8", "--all", "--limit", "100000").stdout
    cls = {}
    for p in pages:
        m = re.search(r"/" + re.escape(p) + r"\.md\n(.*)\n", l8)
        if m:
            k = re.search(r"(append-log|synthesis|unsectioned|verbose|matrix)", m.group(1))
            k = k.group(1) if k else "ruled"
        else:
            k = "under line"
            s, d = (int(x) for x in dated.get(p, ("1", "0")))
            if s and d / s >= 0.4:
                k = "under line, append-log-shaped"
        cls.setdefault(k, []).append(p)
    for k, ps in cls.items():
        print(f"  {k}: {len(ps)}" + (f" {ps}" if k not in ("synthesis", "under line") else ""))
        if k in ("append-log", "unsectioned", "under line, append-log-shaped"):
            r["fail"].append(k)
    r["syn"], r["under"] = len(cls.get("synthesis", [])), len(cls.get("under line", []))
    for c in ("4", "12"):
        hits = [l for l in run(PY, "scripts/lint-deterministic.py", "--check", c, "--limit", "100000").stdout.splitlines() if any(p in l for p in pages)]
        print(f"lint #{c} on these pages: {len(hits)}")
        if hits:
            r["fail"].append(f"lint #{c}")
    rf = run(PY, "scripts/reflow-md.py", "--check", *[f"wiki/intersections/{p}.md" for p in pages])
    print("reflow:", rf.stdout.strip().splitlines()[-1] if rf.stdout.strip() else rf.stderr[-200:])
    if rf.returncode:
        r["fail"].append("reflow")
    added = 0
    for p in pages:
        o = run("git", "show", f"HEAD:wiki/intersections/{p}.md").stdout
        nw = pathlib.Path(f"wiki/intersections/{p}.md").read_text(encoding="utf-8")
        f = lambda t: len(re.findall(r"\[\[?[^\[\]]+\]", re.search(r"^sources:.*$", t, re.M).group(0)))
        added += f(nw) - f(o)
    r["added"] = added
    after = 0
    for p in pages:
        o = run(PY, "scripts/page-index.py", f"wiki/intersections/{p}.md").stdout
        after += int(re.search(r"- ([\d,]+) words", o).group(1).replace(",", ""))
    r["after"] = f"{round(after, -2):,}"
    print(f"sources added: {added}; words now ~{r['after']} (page-index, links included)")
    print("FAIL: " + ", ".join(r["fail"]) if r["fail"] else "finish line met")
    return r


def commit(n, label, calls_file, r):
    pages, syn, under = r["pages"], r["syn"], r["under"]
    calls = pathlib.Path(calls_file).read_text(encoding="utf-8").strip()
    state = f"synthesis ({syn}) or under the line ({under})" if syn and under else ("synthesis" if syn else "under the line")
    log = run(PY, "scripts/log-append.py", "BACKLOG",
              f"job {n} closed — {len(pages)} append-log intersections to {state}, {r['before']} → ~{r['after']} words, {r['added']} slugs added to sources:",
              f"git revert this commit; restore entry {n} from X:\\housekeeping-jobs-resolved.md")
    print(log.stdout.strip(), log.stderr.strip())
    if log.returncode:
        sys.exit(1)
    subprocess.run(["git", "add", "logs/log.md", *[f"wiki/intersections/{p}.md" for p in pages]], check=True)
    c = run(PY, "scripts/assert-containment.py", "--stage", "housekeeping")
    print(c.stdout.strip()[:160])
    if c.returncode:
        sys.exit(1)
    lint_read = (f"Lint #8 reads {syn} as synthesis and {under} as under the classify line; none reads append-log." if syn
                 else f"Lint #8 reads all {under} as under the classify line; none reads append-log.")
    msg = f"""housekeeping {n}: {len(pages)} append-log intersections trimmed back to synthesis

{label}: {', '.join(pages)}. Each is rewritten as current-state synthesis in undated thematic sections under wiki/append-log-trim.md, dated figures and dated absences kept, runs of events collapsed to the current position. {lint_read} Registered at {r['before']} words, now about {r['after']} (page-index, links included).

No source lost its link: every old sources: slug kept, {r['added']} body-cited slugs added, every [[link]] in each old body survives bar self-links (scripts/trim-verify.py against HEAD). Line endings match HEAD, reflow clean, lint #4 and #12 clean.

{calls}

Revert: git revert this commit.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
"""
    mf = TEMP / f"trim-job-{n}-msg.txt"
    mf.write_text(msg, encoding="utf-8")
    subprocess.run(["git", "commit", "-q", "-F", str(mf)], check=True)
    sha = run("git", "rev-parse", "--short=9", "HEAD").stdout.strip()
    p = run("git", "push", "-q")
    print("commit", sha, "push", "ok" if p.returncode == 0 else "FAILED " + p.stderr.strip()[-200:])
    closing = (f"**Closed {datetime.date.today().isoformat()}** (commit `{sha}`). All {len(pages)} pages rewritten as current-state synthesis in undated thematic sections; "
               f"`lint-deterministic.py --check 8 --all` reads {syn} as synthesis and {under} as under the classify line, none as append-log. "
               f"**Words fell from {r['before']} to about {r['after']}.** **No source lost its link**: every old `sources:` slug kept, {r['added']} body-cited slugs added. "
               "Line endings match HEAD, lint #4 and #12 clean. Conflicting figures stated once rather than resolved; corrections are in the commit body.")
    cf = TEMP / f"trim-job-{n}-close.txt"
    cf.write_text(closing, encoding="utf-8")
    subprocess.run([PY, "scripts/housekeeping-strike.py", n, str(cf)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("n")
    ap.add_argument("--commit", nargs=2, metavar=("LABEL", "CALLS_FILE"))
    a = ap.parse_args()
    r = check(a.n)
    if a.commit:
        if r["fail"]:
            print("trim-job: finish line not met — nothing committed")
            return 1
        commit(a.n, a.commit[0], a.commit[1], r)
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
