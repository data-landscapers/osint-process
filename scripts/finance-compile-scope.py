#!/usr/bin/env python3
"""finance-compile-scope.py — repo-review task 22.

FINANCE-COMPILE recomputes the `## Financing` section on every place that has
finance records (58 hubs as of 2026-07-24). A single sweep usually changes one
country's records, so recompiling all 58 is wasted work. This helper scopes the
compile to **only the places whose finance records changed since the last
compile**, keyed off git (no manifest needed — task 19).

State: `reviews/finance-compile-state.json` =
  {"last_compile_commit": "<sha>", "last_compile_time": "<iso8601 committer date>"}.

**The time is the point.** A bare sha is not a durable anchor: every ref this file
held before 2026-08-20 named an object that is in neither this tree nor origin
(housekeeping job 62). `--commit` stored whatever `git rev-parse HEAD` returned, and
where that commit was later discarded -- an amend, a reset, a sub-agent worktree HEAD
that never landed on master -- it was orphaned and gc pruned it. The next scope call
found a ref it could not resolve and fell all the way back to a 58-place full scope,
which is precisely the work the scoping exists to avoid. So: `--commit` refuses to
store a commit unreachable from `master` (it stores the merge-base instead), and a
ref that has gone stale anyway is re-anchored **by date** to the newest commit at or
before `last_compile_time`. Full scope is now the last resort, not the first.

Usage:
  python scripts/finance-compile-scope.py            # print places to recompile
  python scripts/finance-compile-scope.py --all      # print ALL finance places (full rebuild)
  python scripts/finance-compile-scope.py --commit    # advance the state ref to HEAD

Scope logic (default): the places tagged on every finance record (`finance_origin`)
that appears in `git diff <last_compile_commit> -- raw/` (ref vs working tree, so it
catches committed *and* not-yet-committed records). Deleted records are resolved from
the ref version so a place isn't stranded with a stale aggregate.
No state ref at all => --all (establish the baseline, then --commit). A ref that no
longer resolves => re-anchored by date; only if that fails too does it degrade to --all.
"""
import argparse, glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "reviews", "finance-compile-state.json")

def git(*args):
    """git, decoded as UTF-8 rather than the console's locale codec.

    `text=True` alone decodes with `locale.getpreferredencoding()` — cp1252 on this
    machine — so any non-ASCII byte in a path or a diff raised
    `UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d` inside the reader
    thread. The exception surfaced as a traceback while the process still printed a
    place list and exited 0, so the gate read as a full house of 75 places and looked
    like a pass (note 119, 2026-08-05). A gate that crashes must not read like a gate
    that succeeded.
    """
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")

def places_of(text):
    m = re.search(r"^places:\s*(.*)$", text, re.M)
    return set(re.findall(r"[A-Z]{3}|X[A-Z]{2}", m.group(1))) if m else set()

def is_finance(text):
    fm_end = text.find("\n---", 3)
    fm = text[:fm_end] if fm_end > 0 else text
    return re.search(r"^finance_origin:", fm, re.M) is not None

def all_finance_places():
    places = set()
    for p in glob.glob(os.path.join(ROOT, "raw", "**", "*.md"), recursive=True):
        t = open(p, encoding="utf-8").read()
        if is_finance(t):
            places |= places_of(t)
    return places

def read_state():
    try:
        d = json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return None, None
    return d.get("last_compile_commit"), d.get("last_compile_time")


def resolve(rev):
    """The sha `rev` names, or None if this tree no longer holds that commit."""
    if not rev:
        return None
    r = git("rev-parse", "--verify", "--quiet", "%s^{commit}" % rev)
    return r.stdout.strip() or None


def anchor_by_date(when):
    """Newest commit on the current history at or before `when`.

    The recovery path for a ref whose object is gone: the *date* the compile ran is
    still true even when the commit it ran at is not, and whatever was current at
    that moment is a correct — if slightly coarse — diff base.
    """
    if not when:
        return None
    r = git("rev-list", "-1", "--before=%s" % when, "HEAD")
    return r.stdout.strip() or None


def durable_head():
    """HEAD if it is reachable from master, else the merge-base with master.

    A commit that never lands on master does not survive: sub-agent worktree branches
    are torn down, amended and reset commits are orphaned, and gc collects both. The
    merge-base always survives, and diffing from it is conservative — it can widen
    the scope, never silently narrow it. Returns (sha_to_store, unreachable_head).
    """
    head = resolve("HEAD")
    if not head:
        return None, None
    if not resolve("master"):
        return head, None
    if git("merge-base", "--is-ancestor", head, "master").returncode == 0:
        return head, None
    base = git("merge-base", head, "master").stdout.strip()
    return (base or head), head

def changed_places(ref):
    # ref vs working tree, name-status so we can resolve deletions from the ref side
    r = git("diff", "--name-status", ref, "--", "raw/")
    if r.returncode != 0:
        return None  # bad ref -> caller falls back to --all
    lines = list(r.stdout.splitlines())

    # ...plus untracked records. `git diff` never lists them, and on the normal path —
    # ingest admitting records and firing the compile before anything is committed —
    # every new record is untracked. Without this the helper returned nothing to
    # recompile for exactly the records that triggered it. (Post-run note 35, fixed
    # 2026-07-28.)
    u = git("ls-files", "--others", "--exclude-standard", "--", "raw/")
    if u.returncode == 0:
        lines += ["A\t" + p for p in u.stdout.splitlines() if p.strip()]

    places = set()
    for line in lines:
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if not path.endswith(".md"):
            continue
        if status.startswith("D"):
            show = git("show", "%s:%s" % (ref, path))
            text = show.stdout if show.returncode == 0 else ""
        else:
            fp = os.path.join(ROOT, path)
            text = open(fp, encoding="utf-8").read() if os.path.exists(fp) else ""
        if text and is_finance(text):
            places |= places_of(text)
    return places

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args()

    if a.commit:
        sha, unreachable = durable_head()
        if not sha:
            sys.stderr.write("cannot resolve HEAD -> state left unchanged\n")
            return 1
        if unreachable:
            sys.stderr.write("HEAD %s is not on master; storing merge-base %s instead\n"
                             % (unreachable[:8], sha[:8]))
        when = git("show", "-s", "--format=%cI", sha).stdout.strip()
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump({"last_compile_commit": sha, "last_compile_time": when},
                  open(STATE, "w", encoding="utf-8"), indent=2)
        print("finance-compile baseline set to", sha, "(%s)" % when)
        return 0

    if a.all:
        places = all_finance_places()
    else:
        ref, when = read_state()
        if not ref:
            sys.stderr.write("no compile ref -> full scope (baseline run)\n")
            places = all_finance_places()
        else:
            live = resolve(ref)
            if not live:
                live = anchor_by_date(when)
                if live:
                    sys.stderr.write("compile ref %s is gone -> re-anchored by date "
                                     "(%s) to %s\n" % (ref[:8], when, live[:8]))
                else:
                    sys.stderr.write("compile ref %s is gone and no usable date "
                                     "-> full scope\n" % ref[:8])
            places = changed_places(live) if live else None
            if places is None:
                places = all_finance_places()

    for pl in sorted(places):
        print(pl)

if __name__ == "__main__":
    sys.exit(main() or 0)
