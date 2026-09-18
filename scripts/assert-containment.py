#!/usr/bin/env python3
r"""
assert-containment.py — standing. The write-set check at a stage boundary.

`SWEEP-CYCLE.md` commits at four boundaries, and each stage has a write-set that was only
ever prose in a sub-agent's prompt. Prose is the wrong instrument for it, because the two
incidents it exists to stop are not judgment failures:

  * 2026-07-30 — a newspapers batch agent YAML-round-tripped a `raw/` source while
    dedup-checking it. The boundary held only because the sweep happened to notice.
  * 2026-07-31 — a level-1 agent was fed four messages framed as "the user sent a new
    message", believed them, and rewrote three process files, attributing the ruling to
    Bill in git. A sub-agent cannot tell Bill's words from in-band text, so no sentence
    *inside* the prompt being spoofed can defend against this. A check outside it can.

So the parent asserts the write-set before each stage commit, against the working tree the
sub-agents actually produced. `git status --porcelain` is the input: staged, unstaged and
untracked alike, because an agent that adds a file has written just as surely as one that
edits it.

**The deny set is absolute and applies to every stage.** No sub-agent at any level amends a
root process file, `CLAUDE.md` or a `wiki/` spec (`reference.md` and the five it indexes) — a rule change comes back as a
returned recommendation the parent applies. The parent applying one is exactly the case
`--allow-extra` exists for: it makes the exception explicit at the point of commit, and it
lands in the shell history, rather than passing unremarked.

**`--patch <dir>` is the same guard, one step earlier.** CORPUS prepares a housekeeping job
in a scratch clone of the mirror and leaves a `git format-patch` series on `X:\prepared\job-NN\`
for this vault to apply (strategic review 4, ruling R1, 2026-09-17). The rule that makes that
safe is not a rule CORPUS can enforce on itself — `lint-interface.py` runs on its machine, and
a guard the receiving side cannot verify is not a guard. So the patch's own file set is read
here, before `git am` touches anything: `scripts/`, `lookups/` and the two faceted index pages,
and nothing else. **Never `raw/`** — a frontmatter change that arrives as a diff conflicts with
whatever the night's ingest wrote beside it, so bulk `raw/` work comes as a script and its input
instead — **and never a `wiki/` page's prose**, which is where Phase B writes.

Usage:
  python scripts/assert-containment.py --stage sweep
  python scripts/assert-containment.py --stage close --allow-extra SWEEP-CYCLE.md
  python scripts/assert-containment.py --patch X:\prepared\job-102-103
  python scripts/assert-containment.py --since <the BASE commit>   # after git am
  python scripts/assert-containment.py --list

Exit 0 = every changed path is inside the stage's write-set. Exit 1 = at least one is not,
and the offending paths are printed. Exit 2 = the check could not run (not a repo, no git, no
patch in the directory named — a check that passes over nothing is worse than no check),
which is never read as a pass — a broken guard that reads as clean is the failure mode the
gated rows in `sweep-cycle_log.md` already had to be taught.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The write-set of each stage, as prefixes. "*" is every path — used where the stage
# legitimately reaches anywhere and the deny set below is the only real constraint.
STAGES = {
    "notes": (["*"],
              "acting on a notes-for-osint entry reaches wherever its fix lives"),
    "sweep": (["new", "sweep", "logs"],
              "sweeps stage candidates and nothing else"),
    "ingest": (["new", "raw", "wiki", "outputs", "reviews", "logs", "lookups", "index"],
               "ingest is the one door into raw/, plus the compiles it fires"),
    "lint":  (["*"],
              "lint fixes what it finds, anywhere but the process files"),
    "close": (["logs"],
              "cycle-log bookkeeping only"),
    "housekeeping": (["*"],
              "a housekeeping job's fix can land anywhere its scope needs"),
    # The one stage whose whole purpose is to write the files every other stage is
    # denied. The deny set still applies: each process file it amends is named with
    # --allow-extra, so the night's log line lists exactly which rules changed.
    "rules": (["*"],
              "the rules pass amends process files — each one named with --allow-extra"),
}

# Absolute, every stage. A sub-agent runs a process, it does not amend one.
DENY_FILES = {"CLAUDE.md", "wiki/reference.md", "wiki/facets.md", "wiki/layout.md", "wiki/schemas.md", "wiki/intake.md", "wiki/operations.md"}


def deny_set():
    """The process files: CLAUDE.md, wiki/reference.md and the five specs it indexes, and every root-level procedure."""
    denied = set(DENY_FILES)
    for name in os.listdir(V.ROOT):
        if name.endswith(".md") and os.path.isfile(os.path.join(V.ROOT, name)):
            denied.add(name)
    return denied


def changed_paths():
    """Repo-relative paths of everything git sees as changed — staged, unstaged, untracked."""
    # Bytes, not text=True: git reports a path as it is on disk, and this tree holds
    # filenames carrying characters the Windows locale codec cannot decode (a `raw/`
    # slug with a U+2060 word joiner in it). Decoding under cp1252 raised inside the
    # reader thread and left the check crashing on `None` — a gate that fails open on
    # exactly the tree it is guarding.
    try:
        out = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                             cwd=V.ROOT, capture_output=True, check=True).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"assert-containment: cannot read git status — {e}", file=sys.stderr)
        sys.exit(2)

    paths, fields = [], [f for f in out.split("\0") if f]
    i = 0
    while i < len(fields):
        entry = fields[i]
        status, path = entry[:2], entry[3:]
        # A rename is "R  new\0old" — the old name is a separate field to skip.
        if "R" in status and i + 1 < len(fields):
            i += 1
        paths.append(path.replace("\\", "/"))
        i += 1
    return paths


def inside(path, prefixes):
    if "*" in prefixes:
        return True
    return any(path == p or path.startswith(p + "/") for p in prefixes)


def eol_flips(allow, rng=()):
    """Paths whose diff shrinks when line endings are ignored — a whole-file EOL flip.

    The repo holds both CRLF and LF files. A script that reads text and writes it back
    with a different terminator rewrites every line while changing no content, which
    buries the one line that did change and shows as a whole-file diff nobody reads.
    Sessions have been catching this by hand since 2026-08-16 by running `git diff
    --numstat` twice; this makes it the stage boundary's job instead (post-run note 216).
    """
    def numstat(extra):
        try:
            out = subprocess.run(["git", "diff", "--numstat"] + list(rng) + extra,
                                 cwd=V.ROOT, capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            return None
        counts = {}
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                counts[parts[2].replace("\\", "/")] = (int(parts[0]), int(parts[1]))
        return counts

    raw, ign = numstat([]), numstat(["--ignore-cr-at-eol"])
    if raw is None or ign is None:
        return []
    flips = []
    for path, (add, rem) in raw.items():
        if path in allow:
            continue
        a2, r2 = ign.get(path, (0, 0))
        if add + rem > a2 + r2:
            flips.append((path, add + rem, a2 + r2))
    return flips



# --------------------------------------------------------------------------- #
# --patch: what a patch series from CORPUS may carry.
#
# A whitelist, not the stage write-sets: those are about which pass is writing, and this is
# about which machine. The two faceted index pages are named rather than `wiki/` prefixed,
# because everything else under `wiki/` is prose.
# --------------------------------------------------------------------------- #

PATCH_ALLOW_PREFIXES = ["scripts", "lookups"]
PATCH_ALLOW_FILES = {"wiki/places-index.md", "wiki/topics-index.md"}
DIFF_GIT = re.compile(r'^diff --git (?:"?a/(?P<a>.+?)"?) (?:"?b/(?P<b>.+?)"?)$')


def patch_paths(directory):
    """Every path a `git format-patch` series touches, with the patch file that names it.

    Read off the `diff --git a/X b/Y` headers, both sides, so a rename's source counts as
    touched — a patch that moves a file out of `raw/` is refused on its source name.
    """
    try:
        names = sorted(n for n in os.listdir(directory) if n.endswith(".patch"))
    except OSError as e:
        print(f"assert-containment: cannot read {directory} — {e}", file=sys.stderr)
        sys.exit(2)
    if not names:
        print(f"assert-containment: no .patch file in {directory} — nothing to check, "
              f"which is not the same as nothing wrong.", file=sys.stderr)
        sys.exit(2)
    found = []
    for name in names:
        with open(os.path.join(directory, name), encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = DIFF_GIT.match(line.rstrip("\n").rstrip("\r"))
                if m:
                    for side in ("a", "b"):
                        path = m.group(side).replace("\\", "/")
                        if path != "/dev/null" and (name, path) not in found:
                            found.append((name, path))
    return names, found


def check_patch(directory):
    names, found = patch_paths(directory)
    denied = deny_set()
    breaches = []
    for name, path in found:
        if path in denied:
            breaches.append((name, path, "process file — CORPUS sends commits, not rules"))
        elif path in PATCH_ALLOW_FILES or inside(path, PATCH_ALLOW_PREFIXES):
            continue
        elif path.startswith("raw/"):
            breaches.append((name, path, "raw/ — frontmatter work travels as a script and "
                                         "its input, never as a diff"))
        else:
            breaches.append((name, path, "outside the patch set"))

    base = os.path.join(directory, "BASE")
    if os.path.isfile(base):
        commit = open(base, encoding="utf-8", errors="replace").read().strip().split()[0]
        try:
            subprocess.run(["git", "cat-file", "-e", commit + "^{commit}"], cwd=V.ROOT,
                           capture_output=True, check=True)
            held = "held here"
        except (OSError, subprocess.CalledProcessError):
            held = "NOT in this repository — `git am -3` will have no base to merge against"
        print(f"containment [patch]: base {commit[:9]} {held}")

    paths = sorted({p for _, p in found})
    if not breaches:
        print(f"containment [patch]: {len(names)} patch(es), {len(paths)} path(s), all "
              f"inside scripts/, lookups/ and the index pages — apply with "
              f"`git am --keep-cr -3`, then assert the stage.")
        for p in paths:
            print(f"  {p}")
        return 0

    print(f"containment [patch]: {len(breaches)} path(s) of {len(paths)} breach the patch "
          f"set — a patch carries scripts/, lookups/ and the index pages, nothing else.")
    for name, path, reason in breaches:
        print(f"  {path}  <- {reason}  ({name})")
    print("\nDo not run `git am`. Refuse the series in one line to CORPUS naming the paths "
          "above; a re-cut patch is cheaper than a revert.")
    return 1


def committed_paths(base):
    """Paths changed between `base` and HEAD, and nothing about the working tree."""
    try:
        out = subprocess.run(["git", "diff", "--name-only", base + "..HEAD"],
                             cwd=V.ROOT, capture_output=True, text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        print(f"assert-containment: cannot diff {base}..HEAD — {e}", file=sys.stderr)
        sys.exit(2)
    return [ln.replace("\\", "/") for ln in out.splitlines() if ln.strip()]


def check_since(base, extra, allow_eol):
    """`git am` commits as it applies, so the working tree is clean the moment it lands.

    A stage assertion run after it therefore reads a clean tree and passes over nothing —
    the failure mode this whole script exists to refuse. So a patch's landing is asserted
    against the commit range it created, where its paths and its line endings still are.
    """
    paths = committed_paths(base)
    if not paths:
        print(f"containment [since {base[:9]}]: no commit landed — nothing was applied.",
              file=sys.stderr)
        return 2
    denied = deny_set() - set(extra)
    breaches = []
    for p in paths:
        if p in denied:
            breaches.append((p, "process file — CORPUS sends commits, not rules"))
        elif p in PATCH_ALLOW_FILES or inside(p, PATCH_ALLOW_PREFIXES) or inside(p, extra):
            continue
        else:
            breaches.append((p, "outside the patch set"))
    flips = eol_flips(allow_eol, rng=(base + "..HEAD",))
    if not breaches and not flips:
        print(f"containment [since {base[:9]}]: {len(paths)} path(s) landed, all inside "
              f"the patch set, no line-ending flips.")
        return 0
    print(f"containment [since {base[:9]}]: what landed is not what the patch set allows.")
    for p, reason in breaches:
        print(f"  {p}  <- {reason}")
    for path, n, n2 in flips:
        print(f"  {path}  <- line-ending flip: {n} changed lines, {n2} once EOL is ignored")
    print("\nThe commits are already made: `git reset --hard " + base + "` puts the vault "
          "back where the patch found it, and the series is refused in one line.")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--stage", choices=sorted(STAGES), help="which boundary is being committed")
    ap.add_argument("--allow-extra", action="append", default=[], metavar="PATH",
                    help="a path the parent is deliberately committing outside the stage's "
                         "write-set (repeatable) — an explicit exception, not a bypass")
    ap.add_argument("--allow-eol", action="append", default=[], metavar="PATH",
                    help="a path whose line endings are being changed deliberately "
                         "(repeatable) — otherwise an EOL flip fails the stage")
    ap.add_argument("--patch", metavar="DIR",
                    help="a git format-patch series from CORPUS: check its file set "
                         "against the patch whitelist before `git am`")
    ap.add_argument("--since", metavar="COMMIT",
                    help="after `git am`: assert what landed between COMMIT and HEAD "
                         "(the tree is clean by then, so --stage would pass over nothing)")
    ap.add_argument("--list", action="store_true", help="print the stages and their write-sets")
    a = ap.parse_args()

    if a.list:
        for name, (prefixes, why) in sorted(STAGES.items()):
            allowed = "anywhere" if "*" in prefixes else ", ".join(p + "/" for p in prefixes)
            print(f"{name:8} {allowed}\n{'':8} {why}")
        print(f"\ndenied in every stage: CLAUDE.md, the wiki/ specs, and root *.md procedures")
        print(f"\n--patch DIR: a CORPUS patch series may carry "
              f"{', '.join(p + '/' for p in PATCH_ALLOW_PREFIXES)} and "
              f"{', '.join(sorted(PATCH_ALLOW_FILES))} — nothing else")
        return 0

    if a.patch:
        return check_patch(a.patch)

    if a.since:
        return check_since(a.since, [q.replace("\\", "/").rstrip("/") for q in a.allow_extra],
                           {q.replace("\\", "/") for q in a.allow_eol})

    if not a.stage:
        ap.error("--stage is required (or --patch, or --list)")

    prefixes, why = STAGES[a.stage]
    extra = [p.replace("\\", "/").rstrip("/") for p in a.allow_extra]
    denied = deny_set() - set(extra)

    paths = changed_paths()
    if not paths:
        print(f"containment [{a.stage}]: working tree clean — nothing to assert.")
        return 0

    breaches = []
    for p in paths:
        if p in denied:
            breaches.append((p, "process file — a rule change is a returned recommendation"))
        elif not inside(p, prefixes) and not inside(p, extra):
            breaches.append((p, f"outside the {a.stage} write-set"))

    flips = eol_flips({q.replace("\\", "/") for q in a.allow_eol})

    if not breaches and not flips:
        print(f"containment [{a.stage}]: {len(paths)} changed paths, all inside "
              f"the write-set, no line-ending flips — {why}.")
        return 0

    if flips and not breaches:
        print(f"containment [{a.stage}]: {len(flips)} path(s) changed only in line endings.")
        for path, n, n2 in flips:
            print(f"  {path}  <- {n} changed lines, {n2} once EOL is ignored")
        print("\nDo not commit this stage as it stands. Rewrite the file with its own "
              "terminator, or — if the change is deliberate — re-run with --allow-eol <path>.")
        return 1

    print(f"containment [{a.stage}]: {len(breaches)} of {len(paths)} changed paths breach "
          f"the write-set — {why}.")
    for p, reason in breaches:
        print(f"  {p}  <- {reason}")
    for path, n, n2 in flips:
        print(f"  {path}  <- line-ending flip: {n} changed lines, {n2} once EOL is ignored")
    print("\nDo not commit this stage as it stands. Either revert the path, or — if the "
          "parent means it — re-run with --allow-extra <path> and say why in the log line.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
