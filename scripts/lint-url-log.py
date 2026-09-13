#!/usr/bin/env python3
"""lint-url-log.py — does every adjudication in `logs/sweep-url_log.md` have a record?

`sweep-url_log.md` is the gate every sweep and every ingest reads *before* doing any
expensive work: a URL on it is never fetched again. That makes a **wrong line on it
permanently invisible**. An `admitted` line whose file was never written leaves the
story unheld and unfetchable; a `dropped` line for an item that was never really
adjudicated buries a live story forever, and nothing downstream will ever notice —
`raw-url-index.py --check` returns CLEAN for exactly these, because CLEAN is what it
says about a URL the base does not hold.

Found the hard way, ingest Phase A 2026-08-21 slice 3/10: three items carrying an
`admitted` line dated 2026-08-18 with no file in `raw/`. They surfaced only because
they happened to still be sitting in `new/`. Housekeeping job 64.

The check is a join, in this order, and the first hit wins:

  either   -> the `(no url — hand-clip artefact …)` sentinel         -> NO-URL

  admitted -> `lookups/raw-url-index.csv` (exact normalised URL)     -> HELD
           -> the same index, percent-decoded and casefolded         -> HELD-DECODED
           -> the same index on the URL's stem (see `stem()`)        -> HELD-STEM
           -> `url:` frontmatter in new/, new-budget/, budget-archive/ -> STAGED
           -> same host + same `slug_key` held (a path variant)      -> HELD-SLUG
           -> the same URL logged `dropped` elsewhere in this log    -> SUPERSEDED
           -> an inline `(...)` note on the log line                 -> NOTED
           -> nothing                                                -> ORPHAN   [defect]

  acquisition -> held in raw/ (the fetch landed)                    -> HELD
           -> still on `reviews/acquisitions.md`                     -> QUEUED
           -> neither: one attempt spent and the line struck         -> SPENT

  dropped  -> the URL, or its stem, held in raw/                     -> HELD-AFTER
           -> an inline `(...)` reason on the log line               -> ANNOTATED
           -> `lookups/rejected-urls.csv`                            -> REJECTED
           -> registrable domain on `logs/drop-list.csv`             -> DOMAIN
           -> same host + same `slug_key` held (the kept twin)       -> TWIN
           -> nothing                                                -> BARE

**`BARE` is not a defect and is not reported as one.** Most drops are ordinary
off-scope calls that no rule ever asked to annotate, and flagging two hundred of them
would make this check unreadable. What *is* a defect is a bare drop sitting in a slice
that also lost admissions — because the discriminator for dead-slice residue is not
the individual line, it is **the slice**: a run that died mid-write took admissions
and drops alike with it. So a section that lost at least `MIN_ORPHANS` admissions,
and at least `ORPHAN_RATE` of them, puts its bare drops on the report as `SUSPECT`.
The **rate** matters, not the count: one orphan in a ninety-line night is one bad
line, and promoting that section's forty-seven bare drops would bury the finding.

Two independent cross-checks on the same evidence, both cheap:

- **Section arithmetic.** Most section headers declare their own counts ("10 items:
  9 admitted, 1 dropped"). A header that disagrees with the lines beneath it is a
  write that stopped early — the defect this whole check exists for, stated by the
  log about itself.
- **Ghost citations.** A `raw/…` path named in a line's own reason, checked against the
  tree. A drop justified by a file that is not there justifies nothing, and a plausible
  slug is exactly what a hallucinated citation looks like.
- **Contradictions.** The same URL logged both `admitted` and `dropped`. Reported,
  never a defect: it is the ordinary shape of a sweep staging an item and ingest then
  ruling it out, and the admitted side already reads `SUPERSEDED`.

Usage:
  python scripts/lint-url-log.py              # report: defects, then the tallies
  python scripts/lint-url-log.py --all        # every line's verdict, not just defects
  python scripts/lint-url-log.py --csv        # line,date,disposition,verdict,url,...
  python scripts/lint-url-log.py --log FILE   # another log (a rotated copy)

Exit: 0 clean, 1 any ORPHAN, SUSPECT, ghost citation, or header count mismatch.
"""
import argparse
import csv
import os
import re
import sys
import unicodedata
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V

LOG = os.path.join(V.ROOT, "logs", "sweep-url_log.md")
INDEX = os.path.join(V.ROOT, "lookups", "raw-url-index.csv")
REJECTED = os.path.join(V.ROOT, "lookups", "rejected-urls.csv")
DROPLIST = os.path.join(V.ROOT, "logs", "drop-list.csv")
ACQUISITIONS = os.path.join(V.ROOT, "reviews", "acquisitions.md")
STAGING = ["new", "new-budget", "budget-archive"]

LINE = re.compile(r"^(\d{4}-\d{2}-\d{2}) \| (\w+) \| (\S+)(.*)$")
HEAD = re.compile(r"^## (.*)$")
MIN_SLUG_LEN, MIN_SLUG_WORDS = 16, 3

# A citation ends at a delimiter and names a file. Neither held before 2026-08-24, so a
# trailing `:` was captured into the slug and a bare date in prose (`raw/2023/2023-11-01`)
# read as a path - five false ghosts a night, on a check whose whole value is that a real
# hallucinated citation stands out.
RAWREF = re.compile(r"raw/(?:\d{4}/)?[0-9][^\s,;:)\]]*")

DEFECTS = {"ORPHAN", "SUSPECT"}
MIN_ORPHANS, ORPHAN_RATE = 2, 0.10


def slug_key(url_norm):
    """`raw-url-index.py`'s own function, verbatim — the two must never disagree."""
    path = url_norm.split("?", 1)[0].rstrip("/")
    if "/" not in path:
        return ""
    seg = path.rsplit("/", 1)[-1].lower()
    if "." in seg:
        stem, _, ext = seg.rpartition(".")
        if stem and 2 <= len(ext) <= 5 and ext.isalnum():
            seg = stem
    if (len(seg) < MIN_SLUG_LEN or seg.replace("-", "").isdigit()
            or seg.count("-") < MIN_SLUG_WORDS - 1):
        return ""
    return seg


def host_of(url_norm):
    return url_norm.split("/", 1)[0].split("?", 1)[0]


EXT = re.compile(r"\.(html?|php|aspx?|jsp|shtml)$", re.I)
ARTICLE_ID = re.compile(r"/article_[0-9a-f][0-9a-f-]{7,}$", re.I)


def stem(url_norm):
    """The URL with a trailing extension and a trailing opaque `article_<id>` segment cut.

    A log line is written by hand and gets tidied on the way: `nymag.com/…/china-us-ai-
    regulation` for a file holding `…-regulation.html`, `liberianobserver.com/news/lta-
    signs-new-satellite-framework…` for one holding `…/article_e178022e-….html`. The
    story is held; only the string differs. Empty below a real path length, so a bare
    host never joins to anything.
    """
    p = url_norm.split("?", 1)[0].rstrip("/")
    p = ARTICLE_ID.sub("", EXT.sub("", p))
    return loose(p) if len(p) - len(host_of(p)) >= 20 else ""


def loose(url_norm):
    """Percent-decoded, NFC-composed, casefolded — for the encoding-variant join only.

    One capture writes `hespress.com/%d8%a3%d8%b7...` where another writes the Arabic
    itself; both are the same page, and `normalise_url` keeps them apart — correctly,
    because it is not in the business of guessing an encoding.
    """
    try:
        d = urllib.parse.unquote(url_norm)
    except Exception:
        d = url_norm
    return unicodedata.normalize("NFC", d).casefold()


def load_index():
    by_url, by_loose, by_stem, by_slug = {}, {}, {}, {}
    if not os.path.exists(INDEX):
        return by_url, by_loose, by_stem, by_slug
    with open(INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            n = r.get("url_normalized") or ""
            if not n:
                continue
            by_url.setdefault(n, r["file"])
            by_loose.setdefault(loose(n), r["file"])
            s = stem(n)
            if s:
                by_stem.setdefault(s, r["file"])
            k = r.get("slug_key") or ""
            if k:
                by_slug.setdefault((host_of(n), k), r["file"])
    return by_url, by_loose, by_stem, by_slug


def load_staged():
    """`url:` frontmatter across the staging folders — adjudicated but not yet filed."""
    out = {}
    for top in STAGING:
        base = os.path.join(V.ROOT, top)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames.sort()
            for name in sorted(filenames):
                if not name.lower().endswith(".md"):
                    continue
                p = os.path.join(dirpath, name)
                with open(p, encoding="utf-8", errors="replace") as f:
                    head = f.read(4096)
                if "url:" not in head:
                    continue
                fm, _w, _b = V.parse_frontmatter(head)
                u = fm.get("url")
                if isinstance(u, str) and u.strip():
                    rel = os.path.relpath(p, V.ROOT).replace("\\", "/")
                    out.setdefault(V.normalise_url(u), rel)
    return out


def load_rejected():
    if not os.path.exists(REJECTED):
        return {}
    with open(REJECTED, newline="", encoding="utf-8") as f:
        return {r["url_normalized"]: r.get("reason", "")
                for r in csv.DictReader(f) if r.get("url_normalized")}


def load_droplist():
    """Domain-level permanent negatives. `status` is `drop` or `watch`; both account."""
    out = {}
    if not os.path.exists(DROPLIST):
        return out
    with open(DROPLIST, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            d = (r.get("domain") or "").strip().lower()
            if d:
                out[d] = (r.get("status") or "").strip()
    return out


def load_queued(path=None):
    """Normalised URLs still on `reviews/acquisitions.md` — the ones not yet attempted."""
    path = path or ACQUISITIONS
    out = set()
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            for m in re.finditer(r"https?://[^\s)\]`>\"']+", line):
                out.add(V.normalise_url(m.group(0).rstrip(".,;")))
    return out


def parse_log(path):
    """(section, lineno, date, disposition, url, tail) in file order."""
    section = "(no section)"
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, raw in enumerate(f, 1):
            line = raw.rstrip("\n").rstrip("\r")
            h = HEAD.match(line)
            if h:
                section = h.group(1).strip()
                continue
            m = LINE.match(line)
            if m:
                yield section, i, m.group(1), m.group(2), m.group(3), m.group(4).strip()


def domain_hit(host, droplist):
    """The row may key a registrable domain while the URL carries a subdomain."""
    h = host.lower()
    if h in droplist:
        return h
    reg = V.registrable(h)
    if reg in droplist:
        return reg
    return ""


def adjudicate(rows, idx, staged, rejected, droplist, queued):
    by_url, by_loose, by_stem, by_slug = idx
    seen_disp = {}
    for r in rows:
        seen_disp.setdefault(r["norm"], set()).add(r["disp"])
    for r in rows:
        n, host, k = r["norm"], host_of(r["norm"]), slug_key(r["norm"])
        s = stem(n)
        held = by_url.get(n) or ""
        if r["nourl"]:
            r["verdict"], r["evidence"] = "NO-URL", "hand-clip artefact, url_note on file"
        elif r["disp"] == "acquisition":
            # A routed item has no `raw/` file by construction until the fetch lands, and
            # `ACQUIRE.md` strikes a line the moment one attempt fails — struck lines are
            # deleted three days later. So SPENT is the ordinary end state, not a defect:
            # the pass either got it (HELD) or dropped it and stated the absence on a page.
            if held or (s and by_stem.get(s)):
                r["verdict"], r["evidence"] = "HELD", held or by_stem[s]
            elif n in queued:
                r["verdict"], r["evidence"] = "QUEUED", "reviews/acquisitions.md"
            else:
                r["verdict"], r["evidence"] = "SPENT", "attempted and struck, or fetched under another URL"
        elif r["disp"] == "admitted":
            if held:
                r["verdict"], r["evidence"] = "HELD", held
            elif by_loose.get(loose(n)):
                r["verdict"], r["evidence"] = "HELD-DECODED", by_loose[loose(n)]
            elif s and by_stem.get(s):
                r["verdict"], r["evidence"] = "HELD-STEM", by_stem[s]
            elif staged.get(n):
                r["verdict"], r["evidence"] = "STAGED", staged[n]
            elif k and by_slug.get((host, k)):
                r["verdict"], r["evidence"] = "HELD-SLUG", by_slug[(host, k)]
            elif "dropped" in seen_disp[n]:
                r["verdict"], r["evidence"] = "SUPERSEDED", "re-adjudicated: dropped elsewhere in this log"
            elif r["tail"].startswith("("):
                r["verdict"], r["evidence"] = "NOTED", r["tail"][:70]
            else:
                r["verdict"], r["evidence"] = "ORPHAN", "no raw/ file, not staged"
        else:
            if held or (s and by_stem.get(s)):
                r["verdict"], r["evidence"] = "HELD-AFTER", held or by_stem[s]
            elif r["tail"].startswith("("):
                r["verdict"], r["evidence"] = "ANNOTATED", r["tail"][:70]
            elif n in rejected:
                r["verdict"], r["evidence"] = "REJECTED", rejected[n]
            elif domain_hit(host, droplist):
                d = domain_hit(host, droplist)
                r["verdict"], r["evidence"] = "DOMAIN", d + " (" + droplist[d] + ")"
            elif k and by_slug.get((host, k)):
                r["verdict"], r["evidence"] = "TWIN", by_slug[(host, k)]
            else:
                r["verdict"], r["evidence"] = "BARE", ""
        r["contradiction"] = ("admitted" in seen_disp[r["norm"]]
                              and "dropped" in seen_disp[r["norm"]])
    # Dead-slice promotion. A run that died mid-write lost admissions *and* drops
    # together, so an orphan **rate** is the signal; a single orphan in a 90-line
    # night is one bad line, not a dead slice, and promoting that section's 47 bare
    # drops would bury the finding it is supposed to surface.
    orph, adm = {}, {}
    for r in rows:
        if r["disp"] == "admitted":
            adm[r["section"]] = adm.get(r["section"], 0) + 1
        if r["verdict"] == "ORPHAN":
            orph[r["section"]] = orph.get(r["section"], 0) + 1
    bad = {s for s, n in orph.items()
           if n >= MIN_ORPHANS and n >= ORPHAN_RATE * max(adm.get(s, 0), 1)}
    for r in rows:
        if r["verdict"] == "BARE" and r["section"] in bad:
            r["verdict"] = "SUSPECT"
            r["evidence"] = "in a slice that lost %d of %d admissions" % (
                orph[r["section"]], adm.get(r["section"], 0))
    return rows


def header_counts(section):
    """What the header claims about itself. `None` where it claims nothing.

    **Summed, not first-wins.** A header routinely itemises its drops — "6 admitted,
    2 dropped as tier-3 duplicates, 2 dropped as out-of-scope" is four drops, not two —
    and reading only the first number manufactures a mismatch out of a correct header.
    """
    a = d = None
    for m in re.finditer(r"(\d+)\s+(admitted|dropped)", section):
        n, w = int(m.group(1)), m.group(2)
        if w == "admitted":
            a = n if a is None else a + n
        else:
            d = n if d is None else d + n
    return a, d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log", default=LOG)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--csv", action="store_true")
    args = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    idx, staged = load_index(), load_staged()
    rejected, droplist = load_rejected(), load_droplist()
    queued = load_queued()

    rows, order = [], []
    for section, ln, date, disp, url, tail in parse_log(args.log):
        if section not in order:
            order.append(section)
        rows.append({"section": section, "line": ln, "date": date, "disp": disp,
                     "url": url, "norm": V.normalise_url(url), "tail": tail,
                     "nourl": url.startswith("(no")})
    if not rows:
        sys.exit("no disposition lines in " + args.log)
    adjudicate(rows, idx, staged, rejected, droplist, queued)

    if args.csv:
        w = csv.writer(sys.stdout, lineterminator="\n")
        w.writerow(["line", "date", "disposition", "verdict", "url", "evidence",
                    "contradiction", "section"])
        for r in rows:
            w.writerow([r["line"], r["date"], r["disp"], r["verdict"], r["norm"],
                        r["evidence"], "yes" if r["contradiction"] else "",
                        r["section"][:60]])
        return

    tally = {}
    for r in rows:
        tally[(r["disp"], r["verdict"])] = tally.get((r["disp"], r["verdict"]), 0) + 1

    shown = [r for r in rows if args.all or r["verdict"] in DEFECTS]
    if shown:
        print("## Lines to answer for\n")
        for sec in order:
            block = [r for r in shown if r["section"] == sec]
            if not block:
                continue
            print("### " + sec)
            for r in block:
                flag = "  [both dispositions logged]" if r["contradiction"] else ""
                ev = "  <- " + r["evidence"] if r["evidence"] else ""
                print("  L%-5d %-12s %-12s %s%s%s"
                      % (r["line"], r["disp"], r["verdict"], r["norm"][:96], ev, flag))
            print()

    ghosts = []
    for r in rows:
        for m in RAWREF.finditer(r["tail"]):
            ref = m.group(0).rstrip(".")
            # A slug with no extension and no `-` is a date fragment in prose, not a path.
            if "." not in os.path.basename(ref) and "-" not in os.path.basename(ref)[10:]:
                continue
            for cand in (ref, ref + ".md"):
                if os.path.exists(os.path.join(V.ROOT, cand)):
                    break
            else:
                ghosts.append((r, ref))
    if ghosts:
        print("## Annotations citing a `raw/` file that does not exist\n")
        for r, ref in ghosts:
            print("  L%-5d %-10s %s" % (r["line"], r["disp"], ref))
            print("      " + r["norm"][:120])
        print()

    mismatches = []
    for sec in order:
        block = [r for r in rows if r["section"] == sec]
        ca, cd = header_counts(sec)
        ga = sum(1 for r in block if r["disp"] in ("admitted", "acquisition"))
        gd = sum(1 for r in block if r["disp"] == "dropped")
        if (ca is not None and ca != ga) or (cd is not None and cd != gd):
            mismatches.append((sec, ca, ga, cd, gd))
    if mismatches:
        print("## Sections whose header disagrees with its own lines\n")
        for sec, ca, ga, cd, gd in mismatches:
            print("  header says %s admitted / %s dropped; lines show %d / %d"
                  % (ca if ca is not None else "-", cd if cd is not None else "-",
                     ga, gd))
            print("      " + sec[:150])
        print()

    print("## Tallies\n")
    for disp in ("admitted", "acquisition", "dropped"):
        got = {v: n for (d, v), n in tally.items() if d == disp}
        if got:
            total = sum(got.values())
            parts = ", ".join("%s %d" % (v, n)
                              for v, n in sorted(got.items(), key=lambda x: -x[1]))
            print("  %-12s %5d   %s" % (disp, total, parts))
    n_def = sum(1 for r in rows if r["verdict"] in DEFECTS)
    n_con = sum(1 for r in rows if r["contradiction"])
    print("\n  %d lines over %d sections; %d defect(s), %d contradiction line(s), "
          "%d header mismatch(es)" % (len(rows), len(order), n_def, n_con,
                                      len(mismatches)))
    if ghosts:
        print("  %d annotation(s) cite a raw/ file that is not there" % len(ghosts))
    sys.exit(1 if (n_def or mismatches or ghosts) else 0)


if __name__ == "__main__":
    main()
