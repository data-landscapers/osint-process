#!/usr/bin/env python3
"""artefact-md5-index.py — the artefact md5 index: catch a document held twice under two slugs.

`lookups/artefact-md5-index.csv`, one row per binary artefact held in `raw/`,
`budget-archive/`, `new-budget/` and `new/`. Columns: `md5,bytes,artefact,record`.

Housekeeping job 106. Two `raw/` records were found on 2026-09-10 holding the same
6,106,386-byte PDF under different slugs, differing only in which URL each companion page
cites. **Nothing in the vault would have caught it**: ingest's tier-3 dedup works on titles
and ledes and `lookups/raw-url-index.csv` works on normalised URLs, so a document served
from two routes defeats both and both pages read as legitimate records to every check that
runs. The bytes are the one thing that does not lie about it.

**A collision is a finding, not a defect.** Three shapes turned up in the first measurement
and only one of them is a duplicate to retire: one document captured by two routes; one
document evidencing two different records (a report and its launch notice, two loans on one
project phase, a budget table reprinted in the next year's document); and a stray file no
record declares. The allowed list, `lookups/artefact-md5-allowed.csv`, is where a collision
that has been read and ruled legitimate is recorded with its reason — without it the check
reports the same nine every night until it is ignored along with a real one.

**Trees, and why `budget-archive/` is in scope.** A budget document also ingested as a
source is held in both stores, and four of the eleven groups in the first measurement are
exactly that. They are legitimate — `budget-archive/README.md` says nothing there is a
source and nothing there is ever deleted — but a check that hashed only `raw/` would not
have seen them at all, and the next cross-tree collision might not be legitimate.

Usage:
  artefact-md5-index.py --rebuild          # walk and hash every tree (minutes)
  artefact-md5-index.py --append PATH ...  # one row per new artefact, at INGEST.md step 11
  artefact-md5-index.py --check            # collisions not on the allowed list (reads the CSV)
  artefact-md5-index.py --lint             # row count vs the trees -- mismatch: rebuild

Exit: 0 clean, 1 a collision with no documented reason (or, for `--lint`, a stale index), 2
the repository root is not where the script was pointed.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import os
import re
import sys

TREES = ("raw", "budget-archive", "new-budget", "new")
INDEX = os.path.join("lookups", "artefact-md5-index.csv")
ALLOWED = os.path.join("lookups", "artefact-md5-allowed.csv")
FIELDS = ("md5", "bytes", "artefact", "record")
CHUNK = 1 << 20
ARTEFACT_RE = re.compile(r"^artefact:\s*(.*?)\s*$")
ITEM_RE = re.compile(r"^\s+-\s*(.+?)\s*$")


def declared(value, rest):
    """The filenames an `artefact:` key names, in any of the three forms it takes.

    `artefact:` is written as a bare name, as a flow list, or as a block list under an
    empty key — that last is how a multi-page image capture or a bilingual edition is
    always written. Reading only the bare form reports every file of a multi-file record
    as declared by nobody, which is what this did when it was written (R38) and what
    `notes-for-osint` 150 caught. A value is also allowed to be a path, so what comes back
    is basenames: the index joins on the name, and a declaration that has to resolve
    against the record's own directory is a second way to be wrong about the same file.
    """
    names = []
    if not value:
        for line in rest:
            m = ITEM_RE.match(line)
            if not m:
                break
            names.append(m.group(1))
    elif value.startswith("["):
        inner, quote, buf = value[1:].rsplit("]", 1)[0], "", ""
        for ch in inner:
            if quote:
                if ch == quote:
                    quote = ""
                else:
                    buf += ch
            elif ch in "'\"":
                quote = ch
            elif ch == ",":
                names.append(buf)
                buf = ""
            else:
                buf += ch
        names.append(buf)
    else:
        names.append(value)
    out = []
    for n in names:
        # A trailing ` # ...` is a YAML comment, not part of a filename; a `#` with no
        # space before it can be.
        n = re.split(r"\s+#", n, maxsplit=1)[0].strip().strip("'\"").strip()
        # `artefact: [[name.pdf]]` is a fourth form — the wikilink spelling, which YAML
        # reads as a list holding a list. Stripping the brackets off the ends is what
        # flattening it comes to, and no filename in the corpus ends in one.
        n = n.strip("[]").strip()
        if n:
            out.append(os.path.basename(n.replace("\\", "/")))
    return out


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


# Files a tree keeps for its own bookkeeping. They are not documents any record holds, so
# counting them as undeclared artefacts puts a floor under the counter that no amount of
# work can reach.
NOT_ARTEFACTS = (".gitkeep", ".gitignore", "manifest.csv", "thumbs.db", ".ds_store")


def artefacts(root):
    """Every non-Markdown file under the trees — what a record holds rather than writes."""
    out = []
    for tree in TREES:
        base = os.path.join(root, tree)
        if not os.path.isdir(base):
            continue
        for dirpath, _, filenames in os.walk(base):
            for fn in sorted(filenames):
                if fn.lower() in NOT_ARTEFACTS:
                    continue
                if not fn.lower().endswith(".md"):
                    out.append(os.path.join(dirpath, fn))
    return out


def holders(root):
    """artefact basename -> [slug], from every record's `artefact:` key.

    Read from the frontmatter directly rather than from `index/`, because lint has to be
    able to run when the index has not been built and because one key on one line does not
    need a parser.
    """
    out = collections.defaultdict(list)
    for tree in TREES:
        base = os.path.join(root, tree)
        if not os.path.isdir(base):
            continue
        for dirpath, _, filenames in os.walk(base):
            for fn in sorted(filenames):
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(dirpath, fn)
                # Read to the closing `---`, not a fixed prefix: a record whose
                # `hub_line:` and `note:` run long carries `artefact:` well past any
                # guess, and a truncated read reports it as declared by nothing.
                with open(p, "rb") as fh:
                    head = fh.read(262144).decode("utf-8", "replace")
                body = head.splitlines()
                for i, line in enumerate(body[1:], 1):
                    if line.strip() == "---":
                        break
                    m = ARTEFACT_RE.match(line)
                    if m:
                        for name in declared(m.group(1), body[i + 1:]):
                            out[name].append(fn[:-3])
    return out


def rel(root, p):
    return os.path.relpath(p, root).replace(os.sep, "/")


def read_index(root):
    path = os.path.join(root, INDEX)
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_index(root, rows):
    path = os.path.join(root, INDEX)
    rows = sorted(rows, key=lambda r: (r["md5"], r["artefact"]))
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def allowed(root):
    """md5 -> reason, the collisions read and ruled legitimate."""
    path = os.path.join(root, ALLOWED)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["md5"]: r.get("reason", "") for r in csv.DictReader(fh) if r.get("md5")}


BUDGET_TREES = ("budget-archive", "new-budget")
BUDGET_MANIFEST = os.path.join("new-budget", "manifest.csv")


def budget_declared(root):
    """basename -> manifest row label, for every document `new-budget/manifest.csv` names.

    **`budget-archive/` declares its artefacts by manifest row, not by an `artefact:` key**
    (`BUDGET-EXTRACT.md`: "the manifest row, companion page and extracted tables are
    committed"; `budget-archive/README.md` splits a document into artefact, companion and
    extracted tables). Reading only `artefact:` therefore reported every budget document in
    the tree as held by nobody -- 73 of them at housekeeping 120 -- when each one is named
    twice over, as `artefact_path` and as `archive_path`.
    """
    out = {}
    path = os.path.join(root, BUDGET_MANIFEST)
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            label = "%s %s %s" % (row.get("iso3", ""), row.get("fiscal_year", ""),
                                  (row.get("doc_type") or "document"))
            for col in ("artefact_path", "archive_path"):
                v = (row.get(col) or "").strip().replace("\\", "/")
                if v:
                    out.setdefault(os.path.basename(v), label.strip())
    return out


def extracted_table(p, root):
    """A `.csv` under a budget tree: the extraction's own output, never an artefact.

    `budget-archive/README.md` lists the extracted tables as a third thing beside the
    artefact and the companion page, and the tracked one -- "a lost PDF is re-fetchable
    from the manifest's URL; a lost figure is not". Counting them as undeclared artefacts
    put 160 rows under the counter that no amount of work could clear.
    """
    rel_p = os.path.relpath(p, root).replace(os.sep, "/")
    return (rel_p.split("/")[0] in BUDGET_TREES) and rel_p.lower().endswith(".csv")


SIDECAR_EXT = (".pdf", ".docx", ".xlsx", ".pptx")


def sidecar_of(name, held):
    """The declared artefact a `.txt` is the working extract of, or None.

    `wiki/schemas.md` §4 (2026-09-20, job 108): a `.txt` extraction sitting beside a
    declared artefact of the same stem is a working file, not a second document, and is
    **not** named in `artefact:` — the record's own body is the text. It is not an orphan
    either, so it does not report as one; 62 of them would otherwise sit in the undeclared
    count for ever and the counter could never reach zero. Both spellings occur: `x.txt`
    beside `x.pdf`, and `x.pdf.txt`.
    """
    if not name.lower().endswith(".txt"):
        return None
    bases = [name[:-4]]
    # `x.ocr.txt` is the third spelling, for a scan read by OCR rather than extracted.
    if bases[0].lower().endswith(".ocr"):
        bases.append(bases[0][:-4])
    # `x.p83-85.ocr.txt` is the fourth: a page-range read out of a long budget volume,
    # which is the same working extract cut smaller (job 120).
    for b in list(bases):
        m = re.search(r"\.p\d+(?:-\d+)?$", b)
        if m:
            bases.append(b[:m.start()])
    for base in bases:
        for cand in (base,) + tuple(base + ext for ext in SIDECAR_EXT):
            if cand in held:
                return cand
    return None


def row_for(root, p, held, budget=None):
    name = os.path.basename(p)
    budget = budget or {}
    slugs = held.get(name) or []
    if slugs:
        record = "; ".join(slugs)
    elif name in budget:
        record = "(manifest: %s)" % budget[name]
    elif extracted_table(p, root):
        record = "(extracted table)"
    else:
        twin = sidecar_of(name, held) or sidecar_of(name, budget)
        record = "(sidecar of %s)" % twin if twin else "(none)"
    return {"md5": md5(p), "bytes": str(os.path.getsize(p)), "artefact": rel(root, p),
            "record": record}


def collisions(rows, ok):
    """[(md5, [rows])] for every digest on more than one artefact and not documented."""
    by_hash = collections.defaultdict(list)
    for r in rows:
        by_hash[r["md5"]].append(r)
    return [(h, rs) for h, rs in sorted(by_hash.items())
            if len(rs) > 1 and h not in ok]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="the repository root (default: cwd)")
    ap.add_argument("--rebuild", action="store_true", help="walk and hash every tree")
    ap.add_argument("--append", nargs="+", metavar="PATH", help="add one row per artefact")
    ap.add_argument("--check", action="store_true", help="collisions with no documented reason")
    ap.add_argument("--lint", action="store_true", help="row count against the trees")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(os.path.join(root, "raw")):
        print("no raw/ under %s -- point --root at the repository root" % root,
              file=sys.stderr)
        return 2

    if args.rebuild:
        held = holders(root)
        budget = budget_declared(root)
        rows = [row_for(root, p, held, budget) for p in artefacts(root)]
        print("%s: %d row(s)" % (INDEX, write_index(root, rows)))
        args.check = True

    if args.append:
        held = holders(root)
        budget = budget_declared(root)
        rows = read_index(root)
        have = {r["artefact"] for r in rows}
        added, replaced, new_rows = 0, False, []
        for p in args.append:
            p = os.path.abspath(p)
            if not os.path.isfile(p):
                print("  absent  %s" % p, file=sys.stderr)
                return 1
            r = row_for(root, p, held, budget)
            if r["artefact"] in have:
                rows = [x for x in rows if x["artefact"] != r["artefact"]]
                replaced = True
            rows.append(r)
            new_rows.append(r)
            added += 1
        # A new row is appended, never a rewrite of the file: a rewrite re-sorts every row,
        # so a concurrent writer's rows move and can be lost (R74, 2026-09-25). Only a row
        # that replaces an existing one needs the whole file written.
        if replaced or not os.path.isfile(os.path.join(root, INDEX)):
            total = write_index(root, rows)
        else:
            with open(os.path.join(root, INDEX), "a", encoding="utf-8", newline="") as fh:
                csv.DictWriter(fh, FIELDS, lineterminator="\n").writerows(new_rows)
            total = len(rows)
        print("%s: %d row(s), %d added" % (INDEX, total, added))
        args.check = True

    if args.lint:
        rows = read_index(root)
        n = len(artefacts(root))
        if len(rows) != n:
            print("%s holds %d row(s), the trees hold %d artefact(s) -- rebuild"
                  % (INDEX, len(rows), n))
            return 1
        print("%s: %d row(s), matching the trees" % (INDEX, len(rows)))

    if args.check:
        rows = read_index(root)
        ok = allowed(root)
        found = collisions(rows, ok)
        print("%d artefact(s), %d documented collision(s), %d undocumented"
              % (len(rows), len(ok), len(found)))
        for digest, members in found:
            print("\n  md5 %s -- %s bytes, %d artefact(s)"
                  % (digest, format(int(members[0]["bytes"]), ","), len(members)))
            for r in members:
                print("      %s   record %s" % (r["artefact"], r["record"]))
        if found:
            print("\nRead each pair, then either retire the lesser record "
                  "(`CLAUDE.md` -> *Duplicates*) or record the reason in %s." % ALLOWED)
            return 1
        return 0

    if not (args.rebuild or args.append or args.lint):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
