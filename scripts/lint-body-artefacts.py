#!/usr/bin/env python3
"""lint-body-artefacts.py — crawler failure strings spliced into a stored verbatim body.

`CLAUDE.md` -> *The material* requires the stored body to be the source's own
verbatim text. The capture step can append one fetch's failure into a **different**
document's body, and when it does the result reads as part of the source: a
Moroccan commercial-code capture ended mid-sentence on `Error fetching
https://collectivites-territoriales.gov.ma/...`, and an Angolan NIF decree ended on
a `minjusdh.gov.ao` failure followed by a bare heading from a different instrument.
Housekeeping job 93 found 16 of these and trimmed them on 2026-09-20.

**The discriminator is the bare form, and it is the whole of the check.** A body
legitimately contains prose *about* a fetch failure — an ingest note saying "Exa's
crawler returned `CRAWL_LIVECRAWL_TIMEOUT`" is correct and must be left alone, and
14 records carry exactly that. What is never legitimate is the machine's own
unadorned output:

    Error fetching <URL>: <CODE>

Nothing writes that but the crawler, and nothing should carry it but a log. Tested
against the corpus on 2026-09-20: it matched all 16 corrupt records and none of the
14 records whose notes describe a failure in prose.

**It reports; the trim is CC's.** Most are a bounded cut at end of body, but not
all — two of the 16 had the error spliced mid-sentence, which means the body was
truncated there and `body_completeness` has to be read rather than assumed.

Usage:
  python scripts/lint-body-artefacts.py            summary
  python scripts/lint-body-artefacts.py --list     every hit, with its context
  python scripts/lint-body-artefacts.py --csv out.csv

Exit 1 if any body carries one.
"""
import argparse
import csv
import glob
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The crawler's own unadorned output. Prose about a failure never takes this shape.
BARE = re.compile(r"Error fetching (https?://\S+?): ([A-Z][A-Z_]+)")


def split_fm(text):
    if not text.startswith("---"):
        return "", text
    m = re.search(r"\n---[ \t]*(\r?\n|$)", text[3:])
    return (text[3:3 + m.start()], text[3 + m.end():]) if m else (text, "")


def host(url):
    return re.sub(r"^https?://(www\.)?", "", url or "").split("/")[0].lower()


def audit():
    rows = []
    for path in sorted(glob.glob(os.path.join(RAW, "**", "*.md"), recursive=True)):
        text = io.open(path, encoding="utf-8", errors="replace", newline="").read()
        fm, body = split_fm(text)
        hits = list(BARE.finditer(body))
        if not hits:
            continue
        own = re.search(r"^url:[ \t]*(.+?)[ \t]*$", fm, re.M)
        own_host = host(own.group(1) if own else "")
        for m in hits:
            tail = body[m.end():].strip()
            rows.append(dict(
                slug=os.path.basename(path)[:-3],
                path=os.path.relpath(path, ROOT).replace(os.sep, "/"),
                own_host=own_host,
                error_host=host(m.group(1)),
                foreign=host(m.group(1)) != own_host,
                code=m.group(2),
                at_end=not tail,
                chars_after=len(tail),
                before=re.sub(r"\s+", " ", body[max(0, m.start() - 90):m.start()]).strip()[-90:],
            ))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--csv")
    a = ap.parse_args()

    rows = audit()
    if a.csv and rows:
        with io.open(a.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote %s" % a.csv)

    if not rows:
        print("No stored body carries a bare crawler failure string.")
        return 0

    files = len({r["path"] for r in rows})
    print("%d bare crawler failure string(s) in %d stored body/bodies." % (len(rows), files))
    print("  naming a host that is not the record's own: %d" % sum(1 for r in rows if r["foreign"]))
    print("  not at the end of the body (text follows, read it): %d"
          % sum(1 for r in rows if not r["at_end"]))
    if a.list:
        for r in rows:
            print("\n  %s" % r["slug"])
            print("      %s -> %s (%s)%s" % (r["own_host"] or "(no url)", r["error_host"], r["code"],
                                             "  FOREIGN" if r["foreign"] else ""))
            print("      ...%s |ERROR|%s" % (r["before"],
                                             "" if r["at_end"] else " + %d chars follow" % r["chars_after"]))
    print("\nTrim the artefact, not the source. Where text follows, or the error is spliced "
          "mid-sentence, the body was truncated there and `body_completeness` has to be read.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
