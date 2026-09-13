#!/usr/bin/env python3
"""hub-line-partition.py — why each `raw/` source has no `hub_line`.

Housekeeping job 68's instrument. `HUB-COMPILE.md`'s contract is that a source
carries the hub bullet it earns; a source with no `hub_line` reaches no place hub
and can only ever be written in by hand. 7,852 of the vault's 10,334 sources carry
none, and the question the register asked is which of them is a *miss* and which is
*correct*.

The answer is not one number, because the population is not one thing. Every class
below is correct-by-rule except the last, and the rules are stated in `INGEST.md`
-> *The `hub_line` gate* — this script is the count, not the authority.

    FINANCE       finance / budget record. Reaches the hub through
                  FINANCE-COMPILE.md's aggregate, never a per-deal bullet
                  (INGEST.md 2a).
    HELD          origin_status: hold. Admitted, not propagated, until lint #6
                  clears the origin (INGEST.md step 1).
    CITE-THROUGH  cite_through: set. The primary it cites through carries the
                  bullet; two bullets for one claim is the thing to avoid.
    NO-PLACE      empty places:. There is no hub for the bullet to reach.
    UNDATED       no parseable published:. compile-hubs.py cannot place it.
    DECLINED      hub_line_none: set. Adjudicated and refused, with the reason on
                  the line — the blank is a decision, not a gap.
    PRE-CONTRACT  ingested before the hub_line contract (2026-07-30). Never
                  adjudicated, because the field did not exist. Backfilled on
                  demand, never by sweep — see INGEST.md for why.
    RESIDUAL      ingested under the contract and left without one. Ingest read
                  the full text and declined the bullet, which is the editorial
                  gate working — *unless* the source is also cited nowhere, in
                  which case it reaches nothing at all and is the real work.

`--uncited` splits RESIDUAL on that last test, which is the only split in here
that costs anything to compute (it scans `wiki/`). **RESIDUAL-UNCITED is the
number to watch and it is 0**: job 68 adjudicated all 135 on 2026-08-22, so a
non-zero reading means a run since then admitted a source that reaches neither a
hub nor a page. RESIDUAL-CITED is rule-covered like PRE-CONTRACT — on a page, off
the hub, backfilled on demand.

Usage:
  python scripts/hub-line-partition.py                  counts
  python scripts/hub-line-partition.py --uncited        counts, RESIDUAL split
  python scripts/hub-line-partition.py --list RESIDUAL  the slugs in one class
  python scripts/hub-line-partition.py --csv out.csv    class,slug,published,ingested,places,title
"""
import argparse, csv, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
WIKI = os.path.join(ROOT, "wiki")

# The date `hub_line` was minted (HUB-COMPILE.md, commit 58315738). Not a
# preference: every source ingested before it carries none by construction, so
# the split is a fact about the schema's history, not a judgement about the source.
CONTRACT = "2026-07-30"

ORDER = ["RESIDUAL", "PRE-CONTRACT", "FINANCE", "DECLINED", "CITE-THROUGH", "HELD",
         "NO-PLACE", "UNDATED"]
BY_RULE = set(ORDER) - {"RESIDUAL"} | {"RESIDUAL-CITED"}

DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
FM_LIST_RE = re.compile(r"^(?:sources|entities):[ \t]*\[(.*)\][ \t\r]*$", re.M)
FM_ITEM_RE = re.compile(r"\[([^\[\]]+)\]")
# Same exclusion lint #4 and uncited-sources.py make: a file documenting the link
# convention quotes slugs, it does not cite them.
SKIP_WIKI = {"reference.md", "facets.md", "layout.md", "schemas.md", "intake.md", "operations.md", "finance-record-spec.md", "finance-load-domestic-state.md",
             "finance-news-driver.md", "capture-rule.md", "origin-screen.md"}


def read(path):
    return open(path, "rb").read().decode("utf-8", "surrogateescape")


def fm_of(text):
    # CRLF-tolerant: the vault is mixed-EOL by design and an LF-only anchor here
    # dropped every CRLF-headed source silently once already (compile-hubs.py).
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", text, re.S)
    return m.group(1) if m else None


def scalar(fm, key):
    """A frontmatter value, block scalars ('>' folded, '|' literal) included."""
    m = re.search(r"^%s:[ \t]*(\||>)?[ \t]*(.*)$" % re.escape(key), fm, re.M)
    if not m:
        return ""
    style, inline = m.group(1), m.group(2).strip()
    if not style:
        return inline
    body, started = [], False
    for line in fm[m.end():].splitlines():
        if not started and not line.strip():
            continue
        if line[:1] in (" ", "\t"):
            body.append(line.strip())
            started = True
        elif started or line.strip():
            break
    return " ".join(body).strip()


def listval(fm, key):
    v = (scalar(fm, key) or "").strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [x.strip().strip("\"'").strip("[]").strip()
            for x in v.split(",") if x.strip(" []\"'")]


def classify(fm):
    if scalar(fm, "hub_line"):
        return None                                   # has one; not our population
    if scalar(fm, "hub_line_none").strip():
        return "DECLINED"
    if any(scalar(fm, k).strip() for k in
           ("finance_origin", "deal_id", "retired_deal_id", "budget_version")):
        return "FINANCE"
    if scalar(fm, "origin_status").strip() == "hold":
        return "HELD"
    if scalar(fm, "cite_through").strip():
        return "CITE-THROUGH"
    if not (listval(fm, "places") or listval(fm, "place")):
        return "NO-PLACE"
    if not DATE_RE.match(re.sub(r"\s+#.*$", "", scalar(fm, "published")).strip()):
        return "UNDATED"
    if (scalar(fm, "ingested").strip() or "0000-00-00") < CONTRACT:
        return "PRE-CONTRACT"
    return "RESIDUAL"


def cited_slugs():
    """Every slug any wiki/ page links or registers. Same reckoning as lint #4."""
    seen = set()
    for dp, _, fns in os.walk(WIKI):
        for fn in fns:
            if not fn.endswith(".md") or fn in SKIP_WIKI:
                continue
            text = read(os.path.join(dp, fn))
            seen.update(LINK_RE.findall(text))
            for lst in FM_LIST_RE.findall(text):
                seen.update(FM_ITEM_RE.findall(lst))
    return {s.strip() for s in seen}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uncited", action="store_true",
                    help="split RESIDUAL on whether any wiki/ page cites it")
    ap.add_argument("--list", metavar="CLASS")
    ap.add_argument("--csv", metavar="PATH")
    a = ap.parse_args()

    want_cited = a.uncited or (a.list or "").upper().startswith("RESIDUAL-")
    cited = cited_slugs() if want_cited else None

    rows = []
    for name, path in raw_sources(RAW):
        fm = fm_of(read(path))
        if fm is None:
            continue
        cls = classify(fm)
        if cls is None:
            continue
        slug = name[:-3]
        if cls == "RESIDUAL" and cited is not None:
            cls = "RESIDUAL-CITED" if slug in cited else "RESIDUAL-UNCITED"
        rows.append((cls, slug, scalar(fm, "published").strip(),
                     scalar(fm, "ingested").strip(),
                     " ".join(listval(fm, "places") or listval(fm, "place")),
                     scalar(fm, "title").strip()))

    order = ORDER if cited is None else \
        ["RESIDUAL-UNCITED", "RESIDUAL-CITED"] + [c for c in ORDER if c != "RESIDUAL"]

    if a.list:
        pick = a.list.upper()
        for r in sorted(x for x in rows if x[0] == pick):
            print("%s  %s  %-24s %s" % (r[2], r[3], r[4][:24], r[1]))
        return
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["class", "slug", "published", "ingested", "places", "title"])
            w.writerows(sorted(rows, key=lambda r: (order.index(r[0]), r[1])))
        print("wrote %d rows -> %s" % (len(rows), a.csv))
        return

    counts = {c: 0 for c in order}
    for r in rows:
        counts[r[0]] = counts.get(r[0], 0) + 1
    print("sources with no hub_line: %d\n" % len(rows))
    for c in order:
        flag = "" if c in BY_RULE else "   <- adjudicate"
        print("%6d  %-16s%s" % (counts[c], c, flag))
    if cited is not None:
        print("\nRESIDUAL-CITED reaches a page but no hub; RESIDUAL-UNCITED reaches nothing.")


if __name__ == "__main__":
    main()
