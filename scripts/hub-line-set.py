#!/usr/bin/env python3
"""hub-line-set.py — rewrite, add or strike a source's `hub_line:`, in bulk.

The mechanical half of housekeeping job 70. `INGEST.md` 4a asks for "one plain
sentence"; the corpus had drifted to a median of 137 words a bullet, so most of
the 2,535 bullets needed rewriting and 17 needed withdrawing. Doing that by hand
is 1,900 hand-edits to YAML block scalars, which is how frontmatter gets
corrupted; doing it with sed is worse.

`hub_line` is CC's own bookkeeping, not evidence (`schemas.md` §4), so editing
it in place is maintenance rather than a breach of `raw/` immutability. Nothing
else in the file is touched: the dominant EOL, the body and every other key come
back byte-identical.

Input is JSONL, one object per line:

    {"slug": "2026-08-04-foo", "hub_line": "**Claim.** dated specifics ([[a.b]])"}
    {"slug": "2026-08-10-bar", "hub_line": "...", "insert": true}
    {"slug": "2026-08-05-baz", "strike": "standing page under a capture date"}
    {"slug": "2026-08-06-qux", "none": "a forward notice; the meeting's output is not in the source"}

`hub_line` is written as a one-line folded scalar (`>`), which YAML folds back to
the same string and keeps the diff to one line per edit. `insert` adds the key to
a source that carries none, as the last key in the frontmatter. `strike` replaces
the block with `hub_line_struck: <today>  # <reason>` — the source keeps its page
and its citations, it just stops producing a bullet. `none` writes
`hub_line_none: <today>  # <reason>` onto a source that never carried one, which is
`INGEST.md` 4a's recorded refusal — the case `strike` cannot express, since a bullet
withdrawn and a bullet never earned are different facts.

Usage:
  python scripts/hub-line-set.py patch.jsonl            dry run: what would change
  python scripts/hub-line-set.py patch.jsonl --write    apply
"""
import argparse, datetime, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources   # noqa: E402

RAW = "raw"
TODAY = os.environ.get("COMPILE_ASOF") or datetime.date.today().isoformat()
FM = re.compile(r"^---\r?\n(.*?\r?\n)---\r?\n", re.S)


def read(path):
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    return b.decode("utf-8"), ("\r\n" if crlf * 2 > b.count(b"\n") else "\n")


def block_extent(lines, i):
    """Lines [i, j) covering the key at line i and its block-scalar continuation."""
    j = i + 1
    while j < len(lines):
        s = lines[j]
        if s.strip() and not s.startswith((" ", "\t")):
            break
        j += 1
    # A trailing run of blank lines belongs to whatever follows, not to this key.
    while j - 1 > i and not lines[j - 1].strip():
        j -= 1
    return j


def apply(text, eol, new_line=None, strike=None, insert=False, none=None):
    """(text, note). Returns the text unchanged with a note when nothing applies."""
    m = FM.match(text)
    if not m:
        return text, "no-frontmatter"
    fm = m.group(1)
    nl = eol if eol in fm else "\n"
    lines = fm.split(nl)               # ends in "" — the capture keeps its newline
    at = next((k for k, ln in enumerate(lines) if re.match(r"^hub_line:", ln)), None)
    if none is not None:
        # A refusal recorded on a source that never earned a bullet. If one is
        # present the caller wanted `strike`, not `none`; say so rather than guess.
        if at is not None:
            return text, "has-hub_line"
        was = next((k for k, ln in enumerate(lines)
                    if re.match(r"^hub_line_none:", ln)), None)
        at = was if was is not None else len(lines) - 1
        j = block_extent(lines, at) if was is not None else at
        repl = ["hub_line_none: %s  # %s" % (TODAY, none)]
    elif at is None:
        if strike or not insert:
            return text, "no-hub_line"
        at = j = len(lines) - 1        # append as the last key, before the closing ---
        repl = ["hub_line: >", "  " + new_line.strip()]
    else:
        j = block_extent(lines, at)
        repl = (["hub_line_struck: %s  # %s" % (TODAY, strike)] if strike
                else ["hub_line: >", "  " + new_line.strip()])
    joined = nl.join(lines[:at] + repl + lines[j:])
    return text[:m.start(1)] + joined + text[m.end(1):], "ok"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patch")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    index = {n[:-3]: p for n, p in raw_sources(RAW)}
    counts = {"ok": 0, "missing": 0, "no-hub_line": 0, "has-hub_line": 0,
              "no-frontmatter": 0, "noop": 0}
    for raw_line in open(a.patch, encoding="utf-8"):
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        rec = json.loads(raw_line)
        slug = rec["slug"]
        path = index.get(slug)
        if not path:
            counts["missing"] += 1
            print("MISSING %s" % slug)
            continue
        text, eol = read(path)
        new, note = apply(text, eol, rec.get("hub_line"), rec.get("strike"),
                          rec.get("insert", False), rec.get("none"))
        if note != "ok":
            counts[note] += 1
            print("%s %s" % (note.upper(), slug))
            continue
        if new == text:
            counts["noop"] += 1
            continue
        counts["ok"] += 1
        if a.write:
            open(path, "wb").write(new.encode("utf-8"))
    print("%s: %s" % ("written" if a.write else "dry run",
                      "  ".join("%s %d" % (k, v) for k, v in counts.items() if v)))
    return 1 if (counts["missing"] or counts["no-hub_line"] or counts["has-hub_line"]
                 or counts["no-frontmatter"]) else 0


if __name__ == "__main__":
    sys.exit(main())
