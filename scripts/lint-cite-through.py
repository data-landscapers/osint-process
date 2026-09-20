#!/usr/bin/env python3
"""lint-cite-through.py — retired captures still cited from `wiki/`, and whether the citation is deliberate.

`cite_through:` marks a record retired under `CLAUDE.md` -> *Duplicates* -> Replace:
a better capture of the same document survives, and citations are supposed to move
to it. **But a retired record legitimately stays cited where it holds payload the
survivor lacks** — four trade-press accounts of the 2026-07-27 SADC-RTGS kwanza
event are kept alongside the SADC primary precisely because each carries something
it does not. So a grep for retired slugs in `wiki/` returns two populations that
look identical: citations that should have been rewired and were not, and citations
that are correct and should stay.

**What this reports is the absence of a stated reason, not the citation.** A retired
record cited from `wiki/` is a finding only when nothing anywhere says why, because
the next session then has to re-derive the judgement from two bodies and a page —
which is the cost housekeeping job 90 was registered to remove.

**A reason counts wherever the corpus already writes one**, and it writes them in
three places:

  1. the inline YAML comment on `cite_through:` itself — the commonest form,
     e.g. `cite_through: <slug>  # REPLACE 2026-09-19: IFC's own release is the
     primary; this precis is retained as the secondary account`
  2. a `cite_through_note:` block, for a reason too long for one line
  3. the record's own leading italic ingest note, which is where the SADC four
     state theirs — and the reason a frontmatter-only search under-reports by
     roughly a quarter

**Naming the retired capture in the survivor's `hub_line_sources:` is a keep-both
ruling too**, and is reported as such: that key is how one event yields one hub
bullet while its co-sources stay cited.

Usage:
  python scripts/lint-cite-through.py                 summary
  python scripts/lint-cite-through.py --list          every unreasoned record and its pages
  python scripts/lint-cite-through.py --all           every cited retired record, reasoned or not
  python scripts/lint-cite-through.py --csv out.csv   machine-readable

Exit 1 while any cited retired record carries no stated reason anywhere.
"""
import argparse
import csv
import glob
import io
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
WIKI = os.path.join(ROOT, "wiki")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# A reason is prose, so this is a keyword test and deliberately generous: a false
# "reasoned" costs one unnoticed rewire, a false "unreasoned" costs a re-read of a
# judgement already made, and the second is the failure that made job 90 necessary.
KEEP = re.compile(r"\bkeep[- ]both\b|\bkept\b|\bretain(?:ed|s|ing)?\b|sole evidence|"
                  r"only evidence|does not carry|not carried|secondary account|"
                  r"cited for|separate event|its own bullet|stands as", re.I)
REWIRE = re.compile(r"cite (?:it|that one|the document|this one|the survivor)|"
                    r"strict superset|superseded|is the primary for|cite that", re.I)


def split_fm(text):
    """(frontmatter, body). Tolerant: a file whose fence never closes is all frontmatter."""
    if not text.startswith("---"):
        return "", text
    m = re.search(r"\n---[ \t]*(\r?\n|$)", text[3:])
    return (text[3:3 + m.start()], text[3 + m.end():]) if m else (text[:6000], text)


def read(path):
    return io.open(path, encoding="utf-8", errors="replace", newline="").read()


def scalar(fm, key):
    m = re.search(r"^%s:[ \t]*(.+?)[ \t]*$" % re.escape(key), fm, re.M)
    return m.group(1) if m else ""


def block(fm, key):
    m = re.search(r"^%s:[ \t]*>?-?[ \t]*\n((?:[ \t]+.*\n?)+)" % re.escape(key), fm, re.M)
    return " ".join(l.strip() for l in m.group(1).splitlines()).strip() if m else ""


def load():
    records = {}
    for path in glob.glob(os.path.join(RAW, "**", "*.md"), recursive=True):
        slug = os.path.basename(path)[:-3]
        fm, body = split_fm(read(path))
        records[slug] = (fm, body, os.path.relpath(path, ROOT).replace(os.sep, "/"))
    pages = {}
    for path in glob.glob(os.path.join(WIKI, "**", "*.md"), recursive=True):
        rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
        pages[rel] = split_fm(read(path))
    return records, pages


def audit():
    records, pages = load()

    retired = {}
    for slug, (fm, body, _) in records.items():
        raw = scalar(fm, "cite_through")
        if not raw:
            continue
        retired[slug] = dict(
            survivor=raw.split("#")[0].strip().strip("[]").strip(),
            comment=raw.split("#", 1)[1].strip() if "#" in raw else "",
            fnote=block(fm, "cite_through_note"),
            # Only the leading italic blocks: an ingest note sits at the top of a
            # body, and scanning the whole verbatim text would match the source's
            # own emphasis.
            bnote=" ".join(m.group(0) for m in re.finditer(r"\*[^*]{40,2000}\*", body[:4000])),
        )

    cited = defaultdict(list)
    for slug in retired:
        needle_body, needle_fm = "[[%s]]" % slug, "[%s]" % slug
        for rel, (fm, body) in pages.items():
            if needle_body in body or needle_body in fm or needle_fm in fm:
                cited[slug].append(rel)

    out = []
    for slug in sorted(cited):
        v = retired[slug]
        surv = v["survivor"]
        surv_fm, surv_body = records.get(surv, ("", "", ""))[:2]
        where, reason = [], []
        for label, text in (("cite_through comment", v["comment"]),
                            ("cite_through_note", v["fnote"]),
                            ("body ingest note", v["bnote"])):
            if text and (KEEP.search(text) or REWIRE.search(text)):
                where.append(label)
                reason.append(text)
        if slug in scalar(surv_fm, "hub_line_sources") or slug in block(surv_fm, "hub_line_sources"):
            where.append("survivor's hub_line_sources")
        if slug in surv_body[:4000]:
            where.append("named in the survivor's own note")
        joined = " ".join(reason)
        if not where:
            verdict = "UNREASONED"
        elif REWIRE.search(joined) and not KEEP.search(joined):
            verdict = "rewire stated"
        elif KEEP.search(joined) or "hub_line_sources" in " ".join(where):
            verdict = "keep-both stated"
        else:
            verdict = "UNREASONED"        # named somewhere, but no reason given
        out.append(dict(retired=slug, survivor=surv, survivor_held=surv in records,
                        pages=len(cited[slug]), verdict=verdict,
                        where="; ".join(where), reason=joined[:500],
                        page_list=" | ".join(sorted(cited[slug]))))
    return retired, out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="every unreasoned record and its pages")
    ap.add_argument("--all", action="store_true", help="every cited retired record")
    ap.add_argument("--csv", help="write the full table")
    a = ap.parse_args()

    retired, rows = audit()
    bad = [r for r in rows if r["verdict"] == "UNREASONED"]
    dead = [r for r in rows if not r["survivor_held"]]

    print("raw/ records retired by cite_through: %d" % len(retired))
    print("  cited from at least one wiki/ page: %d, over %d (page, record) pairs"
          % (len(rows), sum(r["pages"] for r in rows)))
    for k, n in Counter(r["verdict"] for r in rows).most_common():
        print("    %-18s %2d records, %3d pairs"
              % (k, n, sum(r["pages"] for r in rows if r["verdict"] == k)))
    if dead:
        print("\n  %d cite_through pointer(s) name a survivor not in raw/ — a dead retirement:" % len(dead))
        for r in dead:
            print("     %s -> %s" % (r["retired"], r["survivor"]))

    if a.csv:
        with io.open(a.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("\nwrote %s" % a.csv)

    if a.list or a.all:
        show = rows if a.all else bad
        print("\n%d record(s):" % len(show))
        for r in show:
            print("  %-62s %2d page(s)  %s" % (r["retired"][:62], r["pages"], r["verdict"]))
            print("      survivor: %s" % r["survivor"])
            if r["where"]:
                print("      reason in: %s" % r["where"])
            for p in sorted(r["page_list"].split(" | ")):
                print("        %s" % p)

    if not bad:
        print("\nEvery cited retired capture carries a stated reason. Nothing to re-derive.")
    else:
        print("\n%d record(s) cited with no reason stated anywhere — rewire the citation, "
              "or write the reason where one of the three places above will hold it." % len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
