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

**It tests every open line, and it strikes almost none of them** (housekeeping job
111, 2026-09-20). Two failures were measured over five nights and both are fixed here:

  * **It passed over the lines it exists for.** Testing was conditional on the line
    carrying a URL, and ingest raises most lines without one, so the check reported
    `nothing to check` against live queues of nine, ten and twenty-three. A URL-less
    line is now matched on the document's own **name, instrument number and year**
    against `raw/` frontmatter `title:`, and reported as a **candidate** the acquire
    run confirms by eye. A name match never strikes: titles are written by people.

  * **It over-struck.** Two lines were struck whose held URL was the *announcement
    of* a document rather than the document — the World Bank's Seychelles Country
    Growth and Jobs Report, struck on the brief page the wiki held, and Vodafone's
    *Network Shutdowns in a Connected World*, struck on the news item the line's own
    text names as the announcement. The Seychelles report was acquirable and was
    acquired in full the same night, so a slice trusting the strike would have lost
    it. **A URL match now strikes only when the held record's `title:` is also the
    document the line names**; where the titles diverge, or where the line's own
    text says the held body is a landing page, a contents list or a capture cut at
    the fetch cap, the match is reported as a candidate and the line stands.

**Matched mechanically, never by title similarity — for a strike.** Two exact signals:

  1. the item's URL is already a `url:` (or `source:`) on a source in `raw/`;
  2. the item's linked filename matches a held `artefact:` basename, in `raw/`
     or `budget-archive/`.

Title similarity does real work, but only ever to *propose*: it either downgrades a
URL strike to a candidate, or surfaces a URL-less line that would otherwise go
untested. A fuzzy match that could strike would flag every acquisition line naming a
document the wiki holds *a different edition of*, which is a real and common thing to
want.

**`--markers` counts and `--fix-markers` repairs list lines under `## Open items`
that carry no `- ` marker**, because `STATUS.md`'s `acquisitions` count greps for one
and a line without it is invisible to the status line while being perfectly visible
to a human (the count read 7 for a queue of 9, 2026-09-14).

Usage:
  python scripts/lint-acquisition-held.py           check the open items
  python scripts/lint-acquisition-held.py --url U   check one URL before adding it
  python scripts/lint-acquisition-held.py --markers      report marker-less items
  python scripts/lint-acquisition-held.py --fix-markers  add the missing markers
Exit code 1 if any open acquisition names a held document.
"""
import argparse
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources                                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ACQ = os.path.join(ROOT, "reviews", "acquisitions.md")


def normalise(u):
    """The URL contract from INGEST.md step 2 — same normalisation, same index.

    A gate that normalises differently from the one that wrote the index is a gate
    that misses. The backtick is in the strip set because the register writes its
    URLs in code spans, and a trailing backtick was silently defeating every URL
    test on the live queue.
    """
    u = (u or "").strip().strip("<>()[],.;\"'`")
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


# --------------------------------------------------------------------------- #
# the name layer — proposes, never strikes
# --------------------------------------------------------------------------- #

STOP = set("""a an and as at by de des du for from in la le les of on or the to
und une a l d et sur pour avec dans par au aux del da do dos das e o os as em
no na report rapport document text texte version final draft its own""".split())

# `n° 2019-29`, `No. 102 of 2011`, `Loi 019/AN/23`, `Decreto 36/2026`, `23/010`
INSTRUMENT = re.compile(r"(?:n[o°º]\.?|no\.|nr\.?|number)?\s*"
                        r"\b(\d{1,4}\s*[-/]\s*[\w]{1,6}(?:\s*[-/]\s*[\w]{1,6})?)\b", re.I)


def fold(s):
    """Lower-case, strip diacritics, keep word characters — for comparison only."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()


def tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", fold(s)) if len(w) > 2 and w not in STOP}


def instruments(s):
    """Normalised instrument numbers in a string: `n° 019/AN/23` -> `019/an/23`."""
    out = set()
    for m in INSTRUMENT.finditer(s or ""):
        out.add(re.sub(r"\s+", "", fold(m.group(1))))
    return out


def wanted_name(text):
    """The document a register line names: its first bold span, minus the place.

    The house shape is `- **Country — *Title*, a note** [marker] — url, prose`, so
    the italic run inside the bold span is the document's own name where there is
    one, and the bold span with any leading `Place — ` cut is the fallback.
    """
    m = re.search(r"\*\*(.+?)\*\*", text, re.S)
    if not m:
        return ""
    bold = m.group(1).strip("*").strip()
    it = re.search(r"\*+(.+?)\*+", bold, re.S)
    if it and len(it.group(1).strip("*")) > 8:
        return it.group(1).strip("*").strip()
    return re.sub(r"^[^—–:]{0,40}[—–:]\s*", "", bold).strip().strip("*").strip()


_ISO3 = None


def iso3_of(name):
    """ISO-3 for a country name, from `lookups/countries.csv` — the vocabulary, not a guess."""
    global _ISO3
    if _ISO3 is None:
        import csv
        _ISO3 = {}
        path = os.path.join(ROOT, "lookups", "countries.csv")
        if os.path.isfile(path):
            with open(path, encoding="utf-8-sig", newline="") as fh:
                for row in csv.DictReader(fh):
                    _ISO3[fold(row.get("country-name", ""))] = fold(row.get("iso-3", ""))
    return _ISO3.get(fold(name), "")


def place_of(text):
    """(folded name, iso3) for the place a register line names — what stands before
    the first dash in the bold span."""
    m = re.search(r"\*\*\*?(.+?)[—–:]", text)
    name = fold(m.group(1)).strip().strip("*").strip() if m else ""
    return name, iso3_of(name)


def place_agrees(place, slug, title):
    """Does a candidate record belong to the place the line names?

    Slug parts are compared, never substrings: `com` for Comoros occurs inside
    `commission` and `.com`, and a substring test would make a Chadian cyber-strategy
    a candidate for a Comorian one — which it did, on the bench for job 111.
    """
    name, iso = place
    if not name:
        return True
    if name in fold(title) or name in fold(slug):
        return True
    return bool(iso) and any(part == iso or part.startswith(name[:5])
                             for part in fold(slug).split("-"))


def years(s):
    return set(re.findall(r"\b(19|20)\d{2}\b", s or "")) and \
        set(re.findall(r"\b((?:19|20)\d{2})\b", s or ""))


def name_score(want, title):
    """(score, why) for a register line's document name against a held title."""
    wi, ti = instruments(want), instruments(title)
    shared_i = wi & ti
    wt, tt = tokens(want), tokens(title)
    shared = wt & tt
    if not wt:
        return 0.0, ""
    overlap = len(shared) / len(wt)
    wy, ty = years(want), years(title)
    year_ok = not wy or not ty or bool(wy & ty)
    if shared_i and overlap >= 0.5 and year_ok:
        return 0.5 + overlap / 2, ("instrument %s and %d of %d name words"
                                   % (", ".join(sorted(shared_i)), len(shared), len(wt)))
    if overlap >= 0.6 and len(shared) >= 3 and year_ok:
        return overlap / 2, "%d of %d name words shared" % (len(shared), len(wt))
    return 0.0, ""


# The pass's two markers, written on every line for its own workflow (ACQUIRE.md).
# They are what tells an item that forgot its `- ` from the run-log prose under the
# same heading, which also opens in bold: a marker-less paragraph is a narrative,
# a marker-less `**...** [untried]` is an item the status count cannot see.
MARKER = re.compile(r"\[(untried|blocked)", re.I)


# the line's own text saying the held capture is not the document it wants
COMPLETION = re.compile(
    r"wanted\s+\*{0,2}as an artefact|already the `?url:|already held|table of contents|"
    r"contents list|landing page|cut at the fetch cap|fetch cap|re-?capture|completion|"
    r"promulgation notice|announcement of|the announcement|press release|brief page|"
    r"news item|"
    # A document re-issued in place at a stable URL (the AU's treaty status lists): the want
    # is the *current edition* of a held path, and the URL alone can never show it is met (R74).
    r"current edition|re-?issued in place|overwritten in place", re.I)


def held_index():
    """({url: slug}, {artefact: slug}, {slug: title}) over the whole base."""
    urls, arts, titles = {}, {}, {}
    for name, path in raw_sources(os.path.join(ROOT, "raw")):
        with open(path, encoding="utf-8", errors="replace") as fh:
            fm = fm_of(fh.read(6000))
        if not fm:
            continue
        slug = name[:-3]
        m = re.search(r"^title:[ \t]*(.*)$", fm, re.M)
        titles[slug] = (m.group(1).strip().strip("\"'") if m else "")
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
    ba = os.path.join(ROOT, "budget-archive")
    for d, _s, files in os.walk(ba):
        for f in files:
            arts.setdefault(f.lower(), os.path.relpath(os.path.join(d, f), ROOT))
    return urls, arts, titles


def open_items(path=ACQ):
    """(line number, text, has_marker) for every open acquisition line.

    **An item is every list line under the `## Open items` heading** (to the next
    `## `) — not a line matching a marker, and no longer only a line carrying a URL.
    *(Marker independence: 2026-08-10, token review task 7, note 148, option (b);
    URL independence: housekeeping 111, 2026-09-20.)* The marker-matching version
    broke twice — a run raised `[attempted]`, `[untried by search]` and
    `[blocked — retry route: …]`, none of which a literal match saw, and a line with
    no marker at all still could not be seen. A count keyed on *where a line lives*
    cannot be fooled by a forgotten marker.

    A line under the heading that opens with bold but carries no `- ` marker is
    returned too, flagged, because `STATUS.md` counts by the marker and cannot see it.
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
            if not in_open:
                continue
            if re.match(r"^\s*[-*]\s", ln):
                out.append((i, ln.strip(), True))
            elif re.match(r"^\*\*\S", ln) and MARKER.search(ln):
                out.append((i, ln.strip(), False))   # an item that forgot its marker
    return out


def check(text, urls, arts, titles):
    """(strikes, candidates, provenance) for one register line.

    **Only the line's FIRST url is the document being asked for** (note 128, 2026-08-05).
    A well-evidenced line also cites where it learned of the document — the ZAF FHIA line
    cited its `sacj.org.za` provenance while the document wanted sat on `health.gov.za`
    and was not held. Matching any URL on the line made the check propose striking exactly
    the lines that documented themselves best, which would have deleted a real want. So a
    match on a later URL is reported, but never as a reason to strike.
    """
    found = re.findall(r"https?://[^\s)>\]\"'`]+", text)
    want = wanted_name(text)
    completion = bool(COMPLETION.search(text))
    strikes, candidates, provenance = [], [], []

    for idx, u in enumerate(found):
        n = normalise(u)
        hits = []
        if n in urls:
            hits.append(("URL already held", urls[n]))
        base = os.path.basename(n.split("?")[0]).lower()
        if base and base in arts:
            hits.append(("artefact already held (%s)" % base, arts[base]))
        for why, slug in hits:
            if idx:
                provenance.append((why, slug))
                continue
            if completion:
                candidates.append((why + " — but the line asks for a completion of it", slug))
                continue
            score, _w = name_score(want, titles.get(slug, "")) if want else (1.0, "")
            if want and score == 0.0 and titles.get(slug):
                candidates.append((why + " — but its title is a different document (%s)"
                                   % titles[slug][:60], slug))
            else:
                strikes.append((why, slug))

    if not found and want:
        place = place_of(text)
        best = []
        for slug, title in titles.items():
            score, why = name_score(want, title)
            if not score:
                continue
            agrees = place_agrees(place, slug, title)
            if not agrees and not instruments(want) & instruments(title):
                continue      # a generic name that agrees on nothing but words is noise
            if agrees and place[0]:
                score += 0.25
                why += ", place agrees"
            best.append((score, slug, why))
        for score, slug, why in sorted(best, reverse=True)[:3]:
            candidates.append(("name match on `title:` (%s)" % why, slug))
    return strikes, candidates, provenance


def fix_markers(path=ACQ):
    """Prepend `- ` to marker-less items under `## Open items`. Returns the count."""
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    eol = "\r\n" if text.count("\r\n") > text.count("\n") - text.count("\r\n") else "\n"
    lines = text.split(eol)
    in_open, n = False, 0
    for i, ln in enumerate(lines):
        if re.match(r"^##\s+Open items\s*$", ln):
            in_open = True
            continue
        if in_open and re.match(r"^##\s+\S", ln):
            in_open = False
        if in_open and re.match(r"^\*\*\S", ln) and MARKER.search(ln):
            lines[i] = "- " + ln
            n += 1
    if n:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(eol.join(lines))
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", nargs="*", help="test URLs instead of the register")
    ap.add_argument("--markers", action="store_true", help="report marker-less open items")
    ap.add_argument("--fix-markers", action="store_true", help="add the missing `- ` markers")
    a = ap.parse_args()

    if a.fix_markers:
        n = fix_markers()
        print("%d marker-less open item(s) repaired." % n if n
              else "every open item carries a `- ` marker.")
        return 0

    urls, arts, titles = held_index()
    items = ([(0, u, True) for u in a.url] if a.url else open_items())

    if a.markers:
        bad = [(ln, t) for ln, t, mk in items if not mk]
        for ln, t in bad:
            print("acquisitions.md:%d  no `- ` marker — invisible to the status count\n    %s"
                  % (ln, t[:110]))
        print("\n%d of %d open item(s) carry no marker."
              % (len(bad), len(items)) if items else "no open items.")
        return 1 if bad else 0

    if not items:
        print("no open acquisition items — nothing to check "
              "(%d urls / %d artefacts / %d titles indexed)" % (len(urls), len(arts), len(titles)))
        return 0

    n_url = n_name = n_untested = 0
    bad = cand = noted = markerless = 0
    for ln, text, marker in items:
        has_url = bool(re.search(r"https?://", text))
        strikes, candidates, provenance = check(text, urls, arts, titles)
        if has_url:
            n_url += 1
        elif wanted_name(text):
            n_name += 1
        else:
            n_untested += 1
        if not marker:
            markerless += 1
        if not (strikes or candidates or provenance or not marker):
            continue
        print("acquisitions.md:%d  %s" % (ln, text[:100]))
        if not marker:
            print("    %-34s" % "no `- ` marker (--fix-markers)")
        for why, slug in strikes:
            print("    STRIKE     %-52s -> %s" % (why, slug))
        for why, slug in candidates:
            print("    CANDIDATE  %-52s -> %s" % (why, slug))
        for why, slug in provenance:
            print("    (provenance only, never a strike) %-24s -> %s" % (why, slug))
        bad += 1 if strikes else 0
        cand += 1 if candidates and not strikes else 0
        noted += 1 if provenance and not strikes and not candidates else 0

    print("\n%d open line(s): %d tested by URL, %d tested by name, %d could not be tested."
          % (len(items), n_url, n_name, n_untested))
    print("%d strike(s) proposed, %d candidate(s) for the acquire run to confirm by eye."
          % (bad, cand))
    if n_untested:
        print("A line with no URL and no bold document name cannot be tested here — "
              "that is a partial check, not a clean one.")
    if markerless:
        print("%d line(s) carry no `- ` marker and are invisible to STATUS.md's count "
              "(--fix-markers)." % markerless)
    if noted:
        print("%d further line(s) cite a held URL only as provenance — left alone: the "
              "document asked for is the line's first URL." % noted)
    if bad:
        print("Strike the line. An `excerpt` body is not an incomplete one "
              "(schemas.md §4) — re-fetching it acquires nothing.")
    if cand:
        print("A candidate is never struck by this script: read the held record and rule.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
