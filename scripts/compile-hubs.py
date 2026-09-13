#!/usr/bin/env python3
"""compile-hubs.py — HUB-COMPILE.md, as a script.

Rebuilds each place hub's `## Recent developments` bullets from the `hub_line:`
fields of the sources in `raw/`, so a hub is a derived view and never a document
typed by hand. The counterpart of compile-hub-financing.py, same contract.

**What it rewrites, and only this:** the lines between

    <!-- compiled by HUB-COMPILE.md — do not edit between these markers -->
    <!-- /compiled -->

**What it never touches:** everything else in the file, byte for byte — including
`### Not established` (dated absences: findings with no source page to live on)
and `### Before YYYY-MM-DD`, the frozen legacy block. At cut-over, 1,287 of the
vault's 1,565 hub bullets (82%) were traceable to no source at all: their analysis
was written into the hub and never onto the source page. Compiling over them would
delete them. They are frozen, and housekeeping job 29 backfills them
opportunistically.

A source earns a bullet only by carrying `hub_line:` — that is the editorial gate,
and it lives at ingest (INGEST.md step 4a) where the judgment is made. Where two
sources report one event, only one carries the hub_line and names the others in
`hub_line_sources:`, so one event yields one bullet.

Usage:
  python scripts/compile-hubs.py [ISO3 ...]           dry run (default)
  python scripts/compile-hubs.py --write [ISO3 ...]   apply
  python scripts/compile-hubs.py --init  [ISO3 ...]   one-time cut-over: insert the
                                                      markers and move the existing
                                                      bullets into the frozen block
"""
import datetime, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources   # noqa: E402

RAW = "raw"
PLACES = "wiki/places"
OPEN_M = "<!-- compiled by HUB-COMPILE.md — do not edit between these markers -->"
CLOSE_M = "<!-- /compiled -->"
SECTION = "## Recent developments"
# Never a constant: a hardcoded date silently backdates every later cut-over.
TODAY = os.environ.get("COMPILE_ASOF") or datetime.date.today().isoformat()


def read(path):
    """(text, dominant-eol). Read as bytes so odd encodings survive a round trip.

    Dominant, not "CRLF if any": 11 of the 62 hubs are mixed, and two of them
    (COD, UGA) are LF files carrying a single stray CRLF. Keying off presence
    injected CRLF into an LF file and rewrote blank lines that should not have
    been touched.
    """
    b = open(path, "rb").read()
    crlf = b.count(b"\r\n")
    return b.decode("utf-8", "surrogateescape"), ("\r\n" if crlf * 2 > b.count(b"\n") else "\n")


def fm_of(text):
    # Accept CRLF as well as LF. The vault is mixed-EOL by design, and an LF-only
    # anchor here dropped every CRLF-headed source from every hub *silently* — no
    # bullet, no counter, no error. 49 sources carrying a hub_line were invisible
    # when this was found (2026-08-05).
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


def scalar(fm, key):
    """A frontmatter value, including YAML block scalars ('>' folded, '|' literal).

    fm_get() in finance_lib handles one-liners only; hub_line is routinely folded
    over several lines, and reading just the first would truncate the bullet.
    """
    m = re.search(r"^%s:[ \t]*(\||>)?[ \t]*(.*)$" % re.escape(key), fm, re.M)
    if not m:
        return ""
    style, inline = m.group(1), m.group(2).strip()
    if not style:
        return inline.strip("\"'")
    out, rest = [], fm[m.end():].split("\n")[1:]
    for ln in rest:
        if ln.strip() and not ln.startswith((" ", "\t")):
            break                      # dedented: the next key
        out.append(ln.strip())
    while out and not out[-1]:
        out.pop()
    return ("\n" if style == "|" else " ").join(out).strip()


def listval(fm, key):
    # Two shapes coexist in frontmatter: the canonical bracketed-item form
    # `[[a], [b]]` (facets.md §1) and the bare `[a, b]`. The old body was
    # `v.strip("[]").split(",")`, and `strip` eats EVERY bracket at each end, so
    # `[[a], [b]]` became "a]" and "[b" — wrong slugs, silently, wherever a
    # bracketed list was read. Strip exactly one outer layer, then clear any
    # per-item brackets. (Post-run note 96 predicted this class after lint #3
    # was caught doing the same thing; fixed 2026-08-03.)
    v = (scalar(fm, key) or "").strip()
    if v.startswith("[") and v.endswith("]"):
        v = v[1:-1]
    return [x.strip().strip("\"'").strip("[]").strip()
            for x in v.split(",") if x.strip(" []\"'")]


def places_of(fm):
    return listval(fm, "places") or listval(fm, "place")


def collect():
    """place -> [(published, slug, hub_line, [co-source slugs])]"""
    by_place = defaultdict(list)
    skipped = held = 0
    for name, path in raw_sources(RAW):
        fm, _ = fm_of(read(path)[0])
        if not fm:
            continue
        line = scalar(fm, "hub_line")
        if not line:
            continue                                   # no hub_line, no bullet
        if scalar(fm, "origin_status") == "hold":
            held += 1                                  # origin-screen.md -> Hold
            continue   # first-sighting domain: admitted, but its claims do not
                       # reach a synthesis page until lint #6 clears the origin.
                       # Ingest should not have written a hub_line at all; this is
                       # the backstop, and a non-zero count here says it did.
        # Strip a trailing YAML comment. `published: 2025-01-01  # "January 2025";
        # exact date approximate` is legal YAML and two sources carry it; without
        # this the whole line fails every pattern below and the source is reported
        # as undated — a silent drop for a date the file states plainly.
        pub = re.sub(r"\s+#.*$", "", scalar(fm, "published")).strip()
        # A month- or year-precision date is honest, not missing (layout.md §3:
        # "Padding is for sorting; the frontmatter keeps the honesty"). Pad it to
        # place the bullet and display the precision the source actually asserts —
        # otherwise every report, bulletin and strategy is dropped from every hub.
        if re.match(r"^\d{4}$", pub):
            sort_key, shown = pub + "-01-01", pub
        elif re.match(r"^\d{4}-\d{2}$", pub):
            sort_key, shown = pub + "-01", pub
        elif re.match(r"^\d{4}-\d{2}-\d{2}$", pub):
            sort_key = shown = pub
        else:
            skipped += 1                               # genuinely undated: cannot be placed
            continue
        slug = name[:-3]
        for p in places_of(fm):
            by_place[p].append((sort_key, slug, line,
                                listval(fm, "hub_line_sources"), shown))
    return by_place, skipped, held


def render(rows, eol):
    out = []
    for pub, slug, line, extra, shown in sorted(rows, key=lambda r: (r[0], r[1]), reverse=True):
        cite = ", ".join("[[%s]]" % s for s in [slug] + extra)
        label = "Sources" if extra else "Source"
        out.append("- **%s** — %s %s: %s" % (shown, line, label, cite))
    return eol.join(out)


def block_span(lines):
    """(open_idx, close_idx) of the compiled markers, or None."""
    o = c = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s == OPEN_M:
            o = i
        elif s == CLOSE_M and o is not None:
            c = i
            break
    return (o, c) if o is not None and c is not None else None


def compile_place(code, rows, write):
    p = os.path.join(PLACES, "%s.md" % code)
    if not os.path.exists(p):
        return "no-hub"
    text, eol = read(p)
    lines = text.splitlines(keepends=True)
    span = block_span(lines)
    if not span:
        return "no-markers"                            # needs --init
    o, c = span
    body = render(rows, eol)
    inner = body + eol if body else ""
    # Compare the joined text, not the line lists: `inner` is one string with
    # embedded newlines, while the file re-reads as N separate lines, so a list
    # comparison never matches and every run reports a rewrite.
    if "".join(lines[o + 1:c]) == inner:
        return "unchanged"
    if write:
        out = lines[:o + 1] + ([inner] if inner else []) + lines[c:]
        open(p, "wb").write("".join(out).encode("utf-8", "surrogateescape"))
    return "rewritten"


def init_place(code, write):
    """Cut-over: insert the markers, move existing bullets to the frozen block.

    Deliberately separate from the normal run and never automatic — it moves
    irreplaceable hand-written content, so it wants to be reviewed as its own diff.
    """
    p = os.path.join(PLACES, "%s.md" % code)
    if not os.path.exists(p):
        return "no-hub"
    text, eol = read(p)
    lines = text.splitlines(keepends=True)
    if block_span(lines):
        return "already-init"
    start = next((i for i, l in enumerate(lines) if l.strip() == SECTION), None)
    if start is None:
        return "no-section"
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith("## ")), len(lines))
    # Keep the legacy lines verbatim, interior blanks and all — trim only the
    # leading/trailing blank runs. Dropping blank lines would silently reflow
    # paragraph breaks and loose lists in content that cannot be regenerated.
    legacy = lines[start + 1:end]
    while legacy and not legacy[0].strip():
        legacy.pop(0)
    while legacy and not legacy[-1].strip():
        legacy.pop()
    head = [lines[start], eol, OPEN_M + eol, CLOSE_M + eol, eol]
    if legacy:
        head += ["### Before %s%s" % (TODAY, eol), eol,
                 "<!-- Frozen hand-authored legacy. Not compiled, not touched by any pass."
                 " Housekeeping job 29 backfills these onto their sources. -->" + eol, eol]
        head += legacy + [eol]
    if write:
        open(p, "wb").write("".join(lines[:start] + head + lines[end:])
                            .encode("utf-8", "surrogateescape"))
    return "initialised (%d legacy lines kept)" % len(legacy)


def main():
    argv = sys.argv[1:]
    write = "--write" in argv
    init = "--init" in argv
    codes = [a for a in argv if not a.startswith("--")]

    by_place, undated, held = collect()
    known = sorted(f[:-3] for f in os.listdir(PLACES) if f.endswith(".md"))
    if not codes:
        codes = known
    else:
        # A mistyped code selects nothing and the dry run reads as a clean pass over
        # everything (2026-08-22, note 34). --init is the exception: it exists to make
        # a hub that does not exist yet.
        unknown = [c for c in codes if c not in known]
        if unknown and not init:
            print("compile-hubs: no hub page for %s — known: %s"
                  % (" ".join(unknown), " ".join(known)), file=sys.stderr)
            return 2

    res = defaultdict(list)
    for code in codes:
        r = (init_place(code, write) if init
             else compile_place(code, by_place.get(code, []), write))
        res[r.split(" (")[0]].append(code)

    verb = "" if write else "would "
    for k in sorted(res):
        print("%s%-14s %3d   %s" % (verb if k in ("rewritten", "initialised") else "",
                                    k, len(res[k]), " ".join(res[k][:12])))
    if undated:
        print("\n%d source(s) carry hub_line but no valid published date — no bullet."
              % undated)
    if held:
        print("\n%d source(s) carry hub_line but are on origin_status: hold — no bullet. "
              "Ingest should not have written one (INGEST.md 4a); lint #6 drains the hold."
              % held)
    empty = [c for c in codes if c in res.get("rewritten", []) and not by_place.get(c)]
    if empty:
        print("compiled block came out EMPTY for: %s" % " ".join(empty))
        print("  (no scoped source carried a hub_line — usually correct, occasionally a miss)")
    if not write:
        print("\nDry run. Re-run with --write to apply.")


if __name__ == "__main__":
    sys.exit(main())
