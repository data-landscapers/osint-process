#!/usr/bin/env python3
r"""
lint-mirror-head.py — LINT #19, reinstated 2026-08-27 on a different instrument.

The mirror to `O:\` is CORPUS's read path, not a backup: `SWEEP-CYCLE.md`'s last act
copies the working tree there, and everything CORPUS compiles, reports and publishes is
read from that copy. A mirror that silently stops does not lose evidence — it publishes
yesterday's, which is worse, because nothing about the output looks wrong.

The old #19 measured this by comparing the newest line of `logs/mirror_log.md` against the
newest cycle close, and it was retired in August when the mirror moved out of OSINT and the
log it read stopped being written. It has moved back; the log has not. So the check returns
on the assertion `SWEEP-CYCLE.md` already names as the cheapest one available:

    git -C O:\ rev-parse HEAD  ==  git rev-parse HEAD

Nothing has to be written for this to work, so nothing can go stale. It reads two commit
ids and compares them.

**And the manifest beside them.** `cycle-manifest.json` is the only file CORPUS reads about
a run (`scripts/cycle-manifest.py`), and it is written after the final commit, so the copy
sitting on the mirror must name the commit the mirror is holding. A manifest naming an
earlier one is read as a statement about this tree and is a statement about a previous
one — the same silent-publication failure as a stopped mirror, one level in.

**Surface only, and never gating.** A mismatch is normal for the minutes between a commit
and the mirror that follows it, and the repair is to run the mirror, which is a decision
about whether the run is finished — not a fix a lint pass makes for itself. An unreachable
`O:\` is reported as unreachable and is not a defect of the vault.

Usage:
  python scripts/lint-mirror-head.py            compare, print, exit 0
  python scripts/lint-mirror-head.py --gate     exit 1 on a mismatch, for a close step
  python scripts/lint-mirror-head.py --mirror D:\somewhere   a different destination

Exit 0 unless `--gate` is given and the two ids differ.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MIRROR_DEFAULT = "O:\\" if os.name == "nt" else "/o"


def head(path):
    """The commit id at `path`, or None if it is not a readable git tree."""
    try:
        r = subprocess.run(["git", "-C", path, "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def manifest_head(mirror):
    """The commit `cycle-manifest.json` on the mirror names, or None if there is none."""
    try:
        with open(os.path.join(mirror, "cycle-manifest.json"), encoding="utf-8") as fh:
            return json.load(fh).get("head")
    except (OSError, ValueError):
        return None


def behind_by(mirror, local_head, mirror_head):
    """How many local commits the mirror is missing — context, not a verdict.

    Counted in the local repository, which holds both ids whenever the mirror is a copy
    of it. An unrelated id (a mirror pointed somewhere else) simply yields nothing."""
    try:
        r = subprocess.run(["git", "rev-list", "--count",
                            f"{mirror_head}..{local_head}"],
                           cwd=V.ROOT, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--mirror", default=MIRROR_DEFAULT,
                    help=f"the destination to check (default {MIRROR_DEFAULT})")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 on a mismatch — for a close step that wants to stop")
    a = ap.parse_args()

    local = head(V.ROOT)
    if not local:
        print("lint-mirror-head: no commit id here — not a git tree?", file=sys.stderr)
        return 1

    remote = head(a.mirror)
    if not remote:
        print(f"{a.mirror}: unreachable, or holds no git tree — the mirror cannot be "
              f"checked from here, which is not the same as knowing it is stale.")
        return 1 if a.gate else 0

    if remote == local:
        mh = manifest_head(a.mirror)
        if mh == local:
            print(f"{a.mirror}: HEAD {local[:9]} matches, manifest agrees — CORPUS reads "
                  f"this run's evidence.")
            return 0
        where = f"names {mh[:9]}" if mh else "is absent or unreadable"
        print(f"{a.mirror}: HEAD {local[:9]} matches, but cycle-manifest.json {where} — "
              f"CORPUS has the right tree and the wrong account of it. Run "
              f"scripts/cycle-manifest.py after the final commit, then mirror again.")
        return 1 if a.gate else 0

    n = behind_by(a.mirror, local, remote)
    gap = f", {n} commit(s) behind" if n and n != "0" else ""
    print(f"{a.mirror}: HEAD {remote[:9]} against local {local[:9]}{gap} — CORPUS is "
          f"reading an older vault than this one. Run the mirror "
          f"(SyncSettings.ffs_batch), then re-check.")
    return 1 if a.gate else 0


if __name__ == "__main__":
    sys.exit(main())
