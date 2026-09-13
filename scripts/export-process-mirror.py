#!/usr/bin/env python3
r"""
export-process-mirror.py — publish OSINT's process layer to `data-landscapers/osint-process`.

The public repository is a one-way copy of the procedures, scripts, vocabularies and specs
that build this vault — never `raw/`, never the compiled wiki, never the logs. It is exported
from a commit, never edited in place and never merged back, on the model of CORPUS's
`DATATABLE-FROM`: one canonical upstream, a copy, and a marker naming the commit it came from.
The specification is CORPUS's `documentation/osint-process-mirror.md`.

**An allowlist, never a denylist.** `PUBLISH` names what goes out; everything else stays. A new
root procedure, lookup or wiki spec is invisible to the mirror until it is added here — the
script reports it as *unclassified* so that the omission is seen, and adding it to `PUBLISH` or
`WITHHELD` is the ruling. A denylist would publish the first new folder a pass writes before
anyone noticed.

**Read from a commit, not the working tree.** Files come out of `git archive <commit>`, so an
uncommitted edit is never published and `.env` — gitignored, so never in a commit — cannot be.

**Two gates before anything is pushed**, and both refuse rather than filter:
  1. a markdown block quote longer than 200 characters — the realistic leak is a procedure
     illustrating itself with a real source body. A quote read and found to be a rule is
     acknowledged by its hash in `REVIEWED_QUOTES`; a changed quote is a new quote.
  2. any value from `.env`, or a token-shaped string, in a published file.

**No commit when nothing published changed.** `PROCESS-FROM` then keeps naming the older commit,
which is still accurate: the process layer is identical at both. Staleness is therefore not
"PROCESS-FROM != HEAD" but "a published path differs between PROCESS-FROM and the last push",
which is what `--check` (LINT #37) measures.

Usage:
  python scripts/export-process-mirror.py                 export HEAD, commit, push
  python scripts/export-process-mirror.py --no-push       export and commit, do not push
  python scripts/export-process-mirror.py --dry-run       list, gate, write nothing
  python scripts/export-process-mirror.py --check         LINT #37: is the mirror stale?
  --mirror PATH    checkout of the public repo (default ../osint-process, cloned if absent)
  --commit REF     export a commit other than HEAD
  --against REF    what --check compares with (default origin/master, the last push)

Exit 0 on success or no change; 1 on a gate failure, a stale mirror, or a git error;
2 when --check cannot reach the mirror.
"""
import argparse
import datetime
import fnmatch
import hashlib
import io
import os
import re
import shutil
import subprocess
import sys
import tarfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REMOTE = "https://github.com/data-landscapers/osint-process.git"
BRANCH = "main"
MARKER = "PROCESS-FROM"
# Files the public repository owns itself; the export never writes or deletes them.
MIRROR_OWNED = {".git", "README.md", "LICENSE", MARKER}

# fnmatch patterns over repo-relative paths; `*` crosses `/`, so `scripts/*` is the whole tree.
PUBLISH = [
    # Root procedures — every one except those in WITHHELD.
    "ACQUIRE.md", "BUDGET-EXTRACT.md", "CLAUDE.md", "COUNTRY-BUDGET-BATCH.md", "DEAL-VOCAB.md",
    "DOMESTIC-FINANCE-SWEEP.md", "FINANCE-COMPILE.md", "FINANCE-PAGES.md", "HUB-COMPILE.md",
    "INGEST.md", "LINT.md", "PRUNE.md", "RECONCILE.md", "REPO-STATUS.md", "REPORT-LINT.md",
    "RULES.md", "STATUS-ACQUIRE.md", "STATUS.md", "SWEEP-BULLETIN.md", "SWEEP-COUNTRY-BUDGET.md",
    "SWEEP-COUNTRY-DEEP.md", "SWEEP-CYCLE.md", "SWEEP-DAILY-LIST.md", "SWEEP-DAILY-OFFLIST.md",
    "SWEEP-FINANCIERS.md", "SWEEP-IATI.md", "SWEEP-JOURNALS.md", "SWEEP-NEWSPAPERS.md",
    "SWEEP-REGIONAL.md", "SWEEP-THINKTANKS.md", "UPDATE-WIKI.md", "WIKI-SYNC.md",
    ".gitignore", ".gitattributes",
    "scripts/*",
    "documentation/*",
    ".githooks/*",
    ".claude/settings.json",
    # Vocabularies — the lookups that are a controlled list, not the corpus in another shape.
    "lookups/countries.csv", "lookups/taxonomy.md", "lookups/frontmatter-schema.json",
    "lookups/deal-beneficiary-type-map.csv", "lookups/deal-instrument-map.csv",
    "lookups/deal-status-map.csv", "lookups/deal-vocabs.csv", "lookups/financier-names.csv",
    "lookups/fx-imf-annual.csv", "lookups/region-membership.csv",
    "lookups/report-region-sections.csv", "lookups/sweep-*.csv",
    # Wiki specs — by name; the compiled pages beside them are the product, not the process.
    "wiki/index.md", "wiki/intake.md", "wiki/schemas.md", "wiki/facets.md", "wiki/layout.md",
    "wiki/reference.md", "wiki/capture-rule.md", "wiki/origin-screen.md", "wiki/operations.md",
    "wiki/finance-iati-driver.md", "wiki/finance-load-domestic-state.md",
    "wiki/finance-news-driver.md", "wiki/finance-record-spec.md",
]

# Ruled out, with the reason. Anything at these levels in neither list is reported.
WITHHELD = {
    "HANDOVER-corpus-osint-link.md": "machine and network configuration, with a credential",
    "SyncSettings.ffs_batch": "machine configuration",
    "SyncSettings.ffs_gui": "machine configuration",
    "lookups/raw-url-index.csv": "the private corpus in index form",
    "lookups/rejected-urls.csv": "corpus-derived; names third-party URLs with a reason",
    "lookups/xgl-ruled.csv": "rulings on held documents, by title",
    "lookups/entity-slugs-ruled.csv": "rulings citing compiled wiki pages",
    "lookups/budget-init-backlog.csv": "operational state",
    "wiki/places-index.md": "compiled content",
    "wiki/topics-index.md": "compiled content",
}
# The levels a new file can appear at unnoticed. Whole folders outside these are withheld by
# omission and need no listing: raw/, wiki/*/, logs/, reviews/, sweep/, new*/, outputs/, ...
WATCHED = [re.compile(r"^[^/]+$"), re.compile(r"^lookups/[^/]+$"), re.compile(r"^wiki/[^/]+$")]

QUOTE_LIMIT = 200
# sha1[:16] of a reviewed block quote's text -> where it was read. Reviewed 2026-09-13 (CORPUS).
REVIEWED_QUOTES = {
    "ad3c658b49cb3063": "documentation/osint-no-request-feed.md — the division-of-labour rule",
}

TOKEN_SHAPES = re.compile(
    r"ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-ant-[A-Za-z0-9_-]{20,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")


def git(*args, cwd=ROOT, check=True, binary=False):
    r = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.quotepath=false", *args],
                       cwd=cwd, capture_output=True, text=not binary,
                       encoding=None if binary else "utf-8",
                       errors=None if binary else "replace")
    if check and r.returncode != 0:
        err = r.stderr if not binary else r.stderr.decode("utf-8", "replace")
        sys.exit(f"git {' '.join(args)} failed in {cwd}:\n{err.strip()}")
    return r


def published(path):
    return any(fnmatch.fnmatchcase(path, p) for p in PUBLISH) and path not in WITHHELD


def manifest(commit):
    tracked = git("ls-tree", "-r", "--name-only", "-z", commit).stdout.split("\0")
    tracked = [p for p in tracked if p]
    files = sorted(p for p in tracked if published(p))
    unclassified = sorted(p for p in tracked if not published(p) and p not in WITHHELD
                          and any(w.match(p) for w in WATCHED))
    return files, unclassified


def extract(commit, files):
    """{path: bytes} for `files` at `commit`, via one git archive."""
    blob = git("archive", "--format=tar", commit, "--", *files, binary=True).stdout
    out = {}
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for m in tar.getmembers():
            if m.isfile():
                out[m.name] = tar.extractfile(m).read()
    return out


def env_values():
    path = os.path.join(ROOT, ".env")
    vals = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8", errors="replace"):
            if "=" in line and not line.lstrip().startswith("#"):
                v = line.split("=", 1)[1].strip().strip("'\"")
                if len(v) >= 12:
                    vals.append(v)
    return vals


def gate(content):
    """Return a list of findings; empty means publishable."""
    findings = []
    secrets = env_values()
    for path, data in content.items():
        text = data.decode("utf-8", "replace")
        for v in secrets:
            if v in text:
                findings.append(f"{path}: contains a value from .env")
        for m in TOKEN_SHAPES.finditer(text):
            findings.append(f"{path}: token-shaped string {m.group(0)[:8]}…")
        if not path.endswith(".md"):
            continue
        block = []
        for line in text.splitlines() + [""]:
            s = line.lstrip()
            if s.startswith(">"):
                block.append(s.lstrip(">").strip())
                continue
            if block:
                quote = " ".join(block).strip()
                h = hashlib.sha1(quote.encode("utf-8")).hexdigest()[:16]
                if len(quote) > QUOTE_LIMIT and h not in REVIEWED_QUOTES:
                    findings.append(f"{path}: block quote of {len(quote)} chars [{h}] "
                                    f"\"{quote[:80]}…\"")
                block = []
    return findings


def ensure_checkout(path):
    if os.path.isdir(os.path.join(path, ".git")):
        git("fetch", "-q", "origin", cwd=path, check=False)
        if git("rev-parse", "--verify", "-q", f"origin/{BRANCH}", cwd=path, check=False).returncode == 0:
            git("checkout", "-q", BRANCH, cwd=path)
            git("merge", "-q", "--ff-only", f"origin/{BRANCH}", cwd=path)
        return
    r = subprocess.run(["git", "clone", "-q", REMOTE, path], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"cannot clone {REMOTE} into {path}:\n{r.stderr.strip()}")


def write_tree(path, content):
    for entry in os.listdir(path):
        if entry in MIRROR_OWNED:
            continue
        full = os.path.join(path, entry)
        shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
    for rel, data in content.items():
        if rel in MIRROR_OWNED:
            sys.exit(f"{rel} is published from OSINT and owned by the mirror — rename one")
        full = os.path.join(path, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)


def check(mirror, against):
    if git("fetch", "-q", "origin", cwd=mirror, check=False).returncode != 0:
        print(f"#37 mirror unreachable at {REMOTE}")
        return 2
    r = git("show", f"origin/{BRANCH}:{MARKER}", cwd=mirror, check=False)
    if r.returncode != 0:
        print(f"#37 no {MARKER} on the mirror — never exported")
        return 1
    source = r.stdout.split()[0]
    target = git("rev-parse", against).stdout.strip()
    changed = git("diff", "--name-only", "-z", source, target).stdout.split("\0")
    stale = sorted({p for p in changed if p and published(p)})
    if stale:
        print(f"#37 mirror stale: {len(stale)} published file(s) differ between {source[:9]} "
              f"and {against} ({target[:9]}), e.g. {', '.join(stale[:3])}")
        return 1
    print(f"#37 mirror current: {MARKER} {source[:9]}, nothing published differs at {against}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--mirror", default=os.path.join(os.path.dirname(ROOT), "osint-process"))
    ap.add_argument("--commit", default="HEAD")
    ap.add_argument("--against", default="origin/master")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    a = ap.parse_args()

    if a.check:
        ensure_checkout(a.mirror)
        return check(a.mirror, a.against)

    sha = git("rev-parse", a.commit).stdout.strip()
    files, unclassified = manifest(sha)
    content = extract(sha, files)
    size = sum(len(d) for d in content.values())
    print(f"export {sha[:9]}: {len(files)} files, {size / 1e6:.1f} MB")
    for p in unclassified:
        print(f"  unclassified, not published: {p} — add to PUBLISH or WITHHELD")

    findings = gate(content)
    if findings:
        print(f"refused: {len(findings)} gate finding(s)")
        for f in findings:
            print(f"  {f}")
        return 1
    if a.dry_run:
        return 0

    ensure_checkout(a.mirror)
    write_tree(a.mirror, content)
    git("add", "-A", cwd=a.mirror)
    git("add", "-f", "--", *files, cwd=a.mirror)
    pending = [l for l in git("status", "--porcelain", cwd=a.mirror).stdout.splitlines()
               if not l.endswith(MARKER)]
    if not pending:
        git("reset", "-q", "--hard", cwd=a.mirror)
        print("no change to the published layer; nothing committed")
        return 0

    when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(os.path.join(a.mirror, MARKER), "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{sha}\n{when}\n")
    git("add", MARKER, cwd=a.mirror)
    git("commit", "-q", "-m", f"Export from OSINT {sha[:12]}", cwd=a.mirror)
    print(f"committed {len(pending)} change(s) to {a.mirror}")
    if a.no_push:
        return 0
    git("push", "-q", "origin", f"HEAD:{BRANCH}", cwd=a.mirror)
    print(f"pushed to {REMOTE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
