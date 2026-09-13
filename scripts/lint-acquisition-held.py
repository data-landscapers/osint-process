#!/usr/bin/env python3
"""lint-acquisition-held.py — LINT.md check #22 / ACQUIRE.md step 0.

**An acquisition line naming a document the wiki already holds cannot stand.**

The failure it prevents is specific and has happened twice: `body_completeness:
excerpt` gets read as "incomplete — chase it", and an acquisition line is written
for a document already sitting on disk as an `artefact:`. §4 is explicit that a
structured extract of a tabular document, and a journal abstract with its citation,
are `excerpt` **and stay `excerpt`** — they are the normal and complete record for
that document, not a defect awaiting repair. The pass then spends a real fetch
attempt re-acquiring what it has.

It is one grep, which is why it should be a script rather than a thing to remember.

**Matched mechanically, never by title similarity.** Two signals, both exact:

  1. the item's URL is already a `url:` (or `source:`) on a source in `raw/`;
  2. the item's linked filename matches a held `artefact:` basename, in `raw/`
     or `budget-archive/`.

A fuzzy title match would flag every acquisition line naming a document the wiki
holds *a different edition of*, which is a real and common thing to want. Better
to catch the exact case cleanly than the general case unreliably.

Usage:
  python scripts/lint-acquisition-held.py           check the open items
  python scripts/lint-acquisition-held.py --url U   check one URL before adding it
Exit code 1 if any open acquisition names a held document.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ACQ = os.path.join(ROOT, "reviews", "acquisitions.md")


def normalise(u):
    """The URL contract from INGEST.md step 2 — same normalisation, same index.

    A gate that normalises differently from the one that wrote the index is a gate
    that misses.
    """
    u = (u or "").strip().strip("<>()[],.;\"'")
    u = re.sub(r"^[a-z][a-z0-9+.-]*://", "", u, flags=re.I)
    u = u.split("#")[0]
    host, _, path = u.partition("/")
    host = re.sub(r"^www\.", "", host.lower())
    path = re.sub(r"[?&](utm_[^&=]*|fbclid|gclid|msclkid|mc_cid|mc_eid|igshid|ref_src|spm)=[^&]*",
                  "", "/" + path)
    return (host + path.rstrip("/?&")).rstrip("/")


def fm_of(text):
    if not text.startswith("---"):
        return ""
    e = text.find("\n---", 3)
    return text[3:e] if e > 0 else ""


def held_index():
    """({normalised url: slug}, {artefact basename: slug}) over the whole base."""
    urls, arts = {}, {}
    for name, path in raw_sources(os.path.join(ROOT, "raw")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            fm = fm_of(fh.read(6000))
        if not fm:
            continue
        slug = name[:-3]
        for key in ("url", "source", "source_url", "canonical"):
            m = re.search(r"^%s:[ \t]*(\S.*)$" % key, fm, re.M)
            if m:
                urls.setdefault(normalise(m.group(1).strip().strip("\"'")), slug)
        m = re.search(r"^artefact:[ \t]*(.*)$", fm, re.M)
        if m:
            for a in re.findall(r"[^,\[\]]+", m.group(1)):
                a = a.strip().strip("\"'")
                if a:
                    arts.setdefault(os.path.basename(a).lower(), slug)
    # binaries the budget pipeline archives outside raw/
    ba = os.path.join(ROOT, "budget-archive")
    for d, _s, files in os.walk(ba):
        for f in files:
            arts.setdefault(f.lower(), os.path.relpath(os.path.join(d, f), ROOT))
    return urls, arts


def open_items(path=ACQ):
    """(line number, text) for every open acquisition line.

    **An item is every list line under the `## Open items` heading (to the next
    `## `) that carries a URL** — not a line matching a marker. *(Changed 2026-08-10,
    token review task 7, note 148, option (b).)* The marker-matching version below
    was tried first and broke twice: a run once raised `[attempted]`, `[untried by
    search]` and `[blocked — retry route: …]`, none of which the literal-string
    match saw (3 open items reported against 36 live wants); a prefix match fixed
    that, but **a line raised with no marker at all — the larger half of that
    run's invisible wants — still could not be seen**, because seeing it depended
    on the raiser remembering to write one. A count keyed on *where a line lives*
    rather than *what bracket it carries* cannot be fooled by a forgotten marker.
    `[untried]` / `[blocked]` remain useful annotations for the acquisition pass's
    own workflow (which needs to know what has already been tried), but they are
    no longer what makes a line visible — being under the one heading is.
    """
    out = []
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as fh:
        in_open = False
        for i, ln in enumerate(fh, 1):
            if re.match(r"^##\s+Open items\s*$", ln):
                in_open = True
                continue
            if in_open and re.match(r"^##\s+\S", ln):
                in_open = False
            if in_open and re.match(r"^\s*[-*]\s", ln) and re.search(r"https?://", ln):
                out.append((i, ln.strip()))
    return out


def check(text, urls, arts):
    """([(why, slug)] strikes, [(why, slug)] provenance-only) for this line.

    **Only the line's FIRST url is the document being asked for** (note 128, 2026-08-05).
    A well-evidenced line also cites where it learned of the document — the ZAF FHIA line
    cited its `sacj.org.za` provenance while the document wanted sat on `health.gov.za`
    and was not held. Matching any URL on the line made the check propose striking exactly
    the lines that documented themselves best, which would have deleted a real want. So a
    match on a later URL is reported, but never as a reason to strike.
    """
    found = re.findall(r"https?://[^\s)>\]\"']+", text)
    strikes, provenance = [], []
    for idx, u in enumerate(found):
        into = strikes if idx == 0 else provenance
        n = normalise(u)
        if n in urls:
            into.append(("URL already held", urls[n]))
        base = os.path.basename(n.split("?")[0]).lower()
        if base and base in arts:
            into.append(("artefact already held (%s)" % base, arts[base]))
    return strikes, provenance


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", nargs="*", help="test URLs instead of the register")
    a = ap.parse_args()

    urls, arts = held_index()
    items = ([(0, u) for u in a.url] if a.url else open_items())
    if not items:
        print("no open acquisition items with a URL — nothing to check "
              "(%d urls / %d artefacts indexed)" % (len(urls), len(arts)))
        return 0

    bad = noted = 0
    for ln, text in items:
        strikes, provenance = check(text, urls, arts)
        if not strikes and not provenance:
            continue
        print("acquisitions.md:%d  %s" % (ln, text[:100]))
        for why, slug in strikes:
            print("    %-34s -> %s" % (why, slug))
        for why, slug in provenance:
            print("    %-34s -> %s" % ("(provenance only, not a strike) " + why, slug))
        bad += 1 if strikes else 0
        noted += 1 if provenance and not strikes else 0

    print("\n%d open item(s) checked, %d name a document already held." % (len(items), bad))
    if noted:
        print("%d further line(s) cite a held URL only as provenance — left alone: the "
              "document asked for is the line's first URL." % noted)
    if bad:
        print("Strike the line. An `excerpt` body is not an incomplete one "
              "(schemas.md §4) — re-fetching it acquires nothing.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
