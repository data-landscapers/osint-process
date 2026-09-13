#!/usr/bin/env python3
"""origin-screen.py — the mechanical half of `wiki/origin-screen.md`.

The screen has always been the right control, and it operated **detect-after-
publish**: both fabricated origins on `logs/drop-list.csv` reached synthesis pages
before anyone noticed, and on the `streamlinefeed.co.ke` recurrence the list was
not consulted at all — a judgment step, skipped the way judgment steps are. This
script makes the consultation mechanical, so it cannot be skipped and costs one
command for a whole run rather than one decision per item.

It decides nothing about *content*. It answers one question per candidate — **what
does the base already know about this origin?** — in four verdicts:

  DROP   on the list as `drop`      -> never stage, never ingest (origin-screen.md)
  WATCH  on the list as `watch`     -> screen out AND promote the row to `drop`
  NOVEL  unlisted, no admitted source in raw/ from this domain
                                    -> REPORT ONLY. Nothing follows. The hold this
                                       used to impose was retired 2026-08-26 - see
                                       wiki/origin-screen.md for the measurement.
  KNOWN  unlisted, N admitted sources already held -> clean, proceed

**`NOVEL` is not an accusation, and since 2026-08-26 it is not a gate either.** It
says the wiki has no track record with this origin, which is true of every good
source the first time it appears. The hold it used to impose was retired: it never
drained (143 outstanding), 67 of those sat on government, multilateral or academic
hosts - a first-party publisher is a first sighting on its own domain by
construction - and it caught neither of the fabrications it was built from. The
`drop`/`watch` list is the gate that stays.

Usage:
  python scripts/origin-screen.py                     screen every candidate in new/
  python scripts/origin-screen.py --dir new-budget    screen another queue
  python scripts/origin-screen.py --domain a.com b.net   screen bare domains
  python scripts/origin-screen.py --held              list held sources in raw/
                                                      (what lint #6 drains)
Exit code is 1 if any candidate screened DROP or WATCH, so it doubles as a gate.
"""
import argparse
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources                                   # noqa: E402
# `registrable()` lived here and was copied wherever else a domain had to be
# keyed. One definition now, in the read layer, so the screen and the index
# cannot key `drop-list.csv` two different ways (2026-08-03).
from vault_lib import SLD, registrable                                # noqa: E402,F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DROP_LIST = os.path.join(ROOT, "logs", "drop-list.csv")

# The vault is UTF-8; this console is cp1252. Reconfigure or a note field with an
# en dash in it kills the screen mid-run.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_list(path=DROP_LIST):
    """{registrable domain: (status, network)} from logs/drop-list.csv."""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            d = registrable(row.get("domain", ""))
            if d:
                out[d] = ((row.get("status") or "").strip().lower(),
                          (row.get("network") or "").strip())
    return out


def frontmatter(text):
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[3:end] if end > 0 else ""


def fm_val(fm, key):
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(key), fm, re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def _budget_companion_domains():
    """{registrable domain: count} from budget-archive/ and new-budget/ companions.

    Added 2026-08-10, token review task 7, note 188. A budget document takes
    `INGEST.md`'s fifth route to `new-budget/`/`budget-archive/` and never reaches
    `raw/`, so a publisher whose *only* admitted material is budget documents
    screened `NOVEL` on every single one — Madagascar's finance ministry twice in
    two days. The screen is asking "has this publisher's material been admitted
    before", and a budget volume plainly has been; these companions carry `type:
    source` and a `url:` exactly like a `raw/` source, so they count the same way.
    """
    c = Counter()
    for base in ("budget-archive", "new-budget"):
        top = os.path.join(ROOT, base)
        if not os.path.isdir(top):
            continue
        for dirpath, _dirs, files in os.walk(top):
            for fn in files:
                if not fn.endswith("-companion.md"):
                    continue
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace") as fh:
                        head = fh.read(4096)
                except OSError:
                    continue
                d = registrable(fm_val(frontmatter(head), "url"))
                if d:
                    c[d] += 1
    return c


def track_record(raw="raw"):
    """{registrable domain: how many admitted, CLEARED sources came from it}.

    This is what makes "unadjudicated" computable. A domain the base has admitted
    before has been read, screened and lived with; a domain appearing for the first
    time has not, whatever it looks like.

    **A source still on `origin_status: hold` does not count** *(fixed 2026-08-10,
    token review task 7, note 151)*. The hold exists precisely because that domain
    has not yet been adjudicated — counting it toward `seen` made the hold
    one-shot-per-domain: the first held source made the domain read `KNOWN` to
    every later screen, so a second candidate from it was never held and lint #6
    never got a second chance to adjudicate. Excluding held sources means a domain
    stays `NOVEL` until at least one of its sources actually clears.

    **Budget companions in `budget-archive/`/`new-budget/` count too** (note 188) —
    see `_budget_companion_domains()`. They carry no `origin_status`, so nothing to
    exclude there; a budget publisher clears the same way any other does, on being
    admitted once.
    """
    c = Counter()
    for _, path in raw_sources(os.path.join(ROOT, raw)):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                head = fh.read(4096)
        except OSError:
            continue
        fm = frontmatter(head)
        if fm_val(fm, "origin_status") == "hold":
            continue
        d = registrable(fm_val(fm, "url"))
        if d:
            c[d] += 1
    c.update(_budget_companion_domains())
    return c


def candidates(dirname):
    """(filename, domain) for every markdown candidate in a queue folder."""
    out = []
    d = dirname if os.path.isabs(dirname) else os.path.join(ROOT, dirname)
    if not os.path.isdir(d):
        return out
    for root, _, files in os.walk(d):
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            with open(p, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            fm = frontmatter(text)
            url = fm_val(fm, "url") or fm_val(fm, "source_url") or fm_val(fm, "source")
            out.append((os.path.relpath(p, ROOT), registrable(url)))
    return out


def held_sources(raw="raw"):
    """Sources in raw/ carrying `origin_status: hold` — the queue lint #6 drains."""
    out = []
    for name, path in raw_sources(os.path.join(ROOT, raw)):
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(4096)
        fm = frontmatter(head)
        if fm_val(fm, "origin_status") == "hold":
            out.append((name, registrable(fm_val(fm, "url"))))
    return out


def verdict(domain, listed, seen):
    if not domain:
        return "NOMAIN", "no url on the candidate — screen it by hand"
    st = listed.get(domain)
    if st and st[0] == "drop":
        return "DROP", st[1] or "adjudicated inadmissible"
    if st and st[0] == "watch":
        return "WATCH", "%s - screen out AND promote the row to drop" % (st[1] or "one prior sighting")
    n = seen.get(domain, 0)
    if n:
        return "KNOWN", "%d admitted source%s held" % (n, "" if n == 1 else "s")
    return "NOVEL", "no admitted source held from this domain - HOLD its claims"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="new", help="queue folder to screen (default new/)")
    ap.add_argument("--domain", nargs="*", default=None, help="screen bare domains instead")
    ap.add_argument("--held", action="store_true", help="list raw/ sources on hold")
    a = ap.parse_args()

    listed = load_list()

    if a.held:
        rows = held_sources()
        for name, dom in rows:
            print("  hold  %-28s %s" % (dom or "?", name))
        print("%d source%s on hold" % (len(rows), "" if len(rows) == 1 else "s"))
        return 0

    seen = track_record()

    if a.domain is not None:
        items = [("(--domain)", registrable(d)) for d in a.domain]
    else:
        items = candidates(a.dir)
        if not items:
            print("no candidates in %s/" % a.dir)
            return 0

    tally = Counter()
    for name, dom in items:
        v, why = verdict(dom, listed, seen)
        tally[v] += 1
        print("  %-6s %-28s %s" % (v, dom or "-", name))
        if v in ("DROP", "WATCH", "NOVEL"):
            print("         %s" % why)

    print("\nscreened %d: %s" % (len(items),
                                 ", ".join("%s %d" % (k, tally[k]) for k in sorted(tally))))
    if tally["NOVEL"]:
        print("NOVEL is a report, not a gate (hold retired 2026-08-26): the base has "
              "no track record with this origin, and nothing follows from that.")
    return 1 if (tally["DROP"] or tally["WATCH"]) else 0


if __name__ == "__main__":
    sys.exit(main())
