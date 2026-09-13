#!/usr/bin/env python3
"""audit-machine-records.py — repo-review task 9.

Script-audit the machine-loaded raw/ records for three mechanically-detectable
defect classes and emit a defect table by class, segmented by record family.
This AUDITS only; task 10 fixes.

Defect classes:
  1  date_source: proxy on a FINANCE record  (finance-record-spec -> Dates forbids
     it; a finance record with no real event date is not a dated fact). Proxy on a
     sweep/news source is NOT a defect — LINT #11 sanctions it — so it is reported
     separately as context, not counted as a defect.
  2  empty `entities: []`  (a record that names actors but tags none)
  3  body marked `body_completeness: full` but the prose is truncated
     (3a ends mid-sentence, no terminal punctuation; 3b carries a paywall/
     continuation marker). Heuristic -> "candidates", confirmed in task 10.

Families: finance-load (finance_origin/deal_id/amount_total/budget_stage) |
          sweep (sweep_batch) | other.

**--persist is what makes this a check rather than a one-off.** For nine days the
script's only defect table was a figure in a document, so nothing could tell whether
the number was rising: an audit that leaves no series cannot detect deterioration,
only report a level. `--persist` appends one dated row to
`logs/machine-record-audit.csv` and rewrites the per-file list to
`logs/machine-record-audit-defects.csv`, then **exits non-zero if any defect class
rose against the previous row**. That is LINT check #21, run at the cycle close.

One append-only series, not a file per night: the series IS the artefact — a row is
meaningless except against the row before it — and a file per night would be a
retention problem for `PRUNE.md` to own for no gain.

Usage: python scripts/audit-machine-records.py [--root DIR] [--csv OUT.csv] [--persist]
"""
import argparse, glob, os, re, csv, collections, datetime, sys

if hasattr(sys.stdout, "reconfigure"):      # the vault is UTF-8, this console is cp1252
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PAYWALL = re.compile(r"(read more|continue reading|subscribe|sign in to read|"
                     r"read the full|to continue reading)", re.I)
# explicit elision marker: [...] / […] / [�] (mojibake of an ellipsis)
ELISION = re.compile(r"\[\s*(?:\.\.\.|…|�)\s*\]")
# A real wall states a condition on the reader. Trailing SITE CHROME merely
# contains the same words: a sponsor footer, a related-stories rail, a cookie
# banner, a social-follow block, an ad blob. Both end a scrape; only the first
# means the article body is cut.
#
# Checked before PAYWALL, and only against the tail. Housekeeping job 12
# (2026-07-29) read all 197 flagged sweep/other bodies: 76 were real walls, 120
# were complete articles with chrome after them, 1 was a genuine mid-quote cut.
# Without this guard the audit reported those 120 as defects on every run, which
# is how a check stops being read.
CHROME = re.compile(
    r"(site sponsor|signiflow"                      # ITWeb sponsor footer
    r"|read more about cookies|accept policy|save & accept|powered by"   # cookie banners
    r"|scroll to top|\b1 2 3\b"                     # pagination rails
    r"|leave a comment|followers\s+(like|follow)|subscribers\s+subscribe"  # social blocks
    r"|read more about:\s*\["                       # ConnectingAfrica keyword rail
    r"|brought to you by|in depth: sponsored|follow us:"                 # sponsored rails
    r"|googlesyndication|doubleclick|&adurl=|&sig=Cg0"                   # ad blobs
    r")", re.I)

# A real wall states a CONDITION ON THE READER to see the rest. Keep these
# phrases specific: bare "premium content" and "create a free account" also occur
# in newsletter self-descriptions and sponsored rails, and matched two complete
# bodies when first tried.
WALL = re.compile(r"(become a .{0,20}insider|sign in to read the full|"
                  r"to continue reading, please subscribe|subscribe for full access|"
                  r"already have a subscription|register to begin your journey|"
                  r"create a free account to (read|continue)|unlock this article)", re.I)
# dangling function words that only appear at a sentence end when the text is cut
DANGLING = re.compile(r"\b(and|or|of|the|to|a|an|in|for|with|at|by|from|that|which|"
                      r"as|is|was|were|has|had|will|would|its|their|on|de|des|le|la|"
                      r"les|du|un|une|et|pour|dans|sur|avec)$", re.I)

def fm_body(t):
    if not t.startswith("---"):
        return "", t
    e = t.find("\n---", 3)
    return (t[3:e], t[e+4:]) if e > 0 else ("", t)

def val(fm, k):
    m = re.search(r"^%s:[ \t]*(.*)$" % re.escape(k), fm, re.M)
    return m.group(1).strip() if m else None

def family(fm):
    keys = set(re.findall(r"^([a-z_]+):", fm, re.M))
    if keys & {"finance_origin", "deal_id", "amount_total", "budget_stage"}:
        return "finance-load"
    if "sweep_batch" in keys:
        return "sweep"
    return "other"

def prose_block(body):
    """The main prose to check for truncation. For a finance record use the
    ## Description section; otherwise the text between the H1 and the first ##."""
    m = re.search(r"^##+\s*Description\s*$(.*?)(^##\s|\Z)", body, re.M | re.S)
    if m:
        seg = m.group(1)
    else:
        # strip the leading '# Title', take up to the first '## ' section
        b = re.sub(r"\A\s*#[^\n]*\n", "", body)
        seg = re.split(r"^##\s", b, maxsplit=1, flags=re.M)[0]
    return seg.strip()

def last_prose_line(seg):
    for ln in reversed(seg.splitlines()):
        s = ln.strip()
        if not s:
            continue
        if s.startswith(("|", "#", "-", "*", ">")) or re.fullmatch(r"\[\[.*\]\]", s):
            return None  # ends on a table/list/heading — not a prose truncation
        return s
    return None

TERMINAL = tuple(list(".!?…”’)]") + ['"', "'"])

def truncated(body, fam):
    seg = prose_block(body)
    if not seg:
        return None
    tail = seg[-400:]
    if CHROME.search(tail):
        return None          # site furniture after a complete body — not a cut
    if WALL.search(tail):
        return "3b paywall wall — reader must sign in/subscribe to finish"
    if ELISION.search(seg[-40:]):
        return "3b explicit elision marker"
    # NOTE: the old loose PAYWALL word list ("read more|subscribe|…") is
    # deliberately NOT tested here. Measured over the 197 bodies read by hand in
    # housekeeping job 12 it caught 0 cuts that WALL/ELISION/3a did not, and
    # produced 120 false positives — it fires on "12 million subscribers" in
    # ordinary prose and on every "Read more" nav rail. It survives only as
    # PAYWALL below, for the paywall *reporting* count, not the truncation test.
    ln = last_prose_line(seg)
    if ln is None:
        return None
    # normalise trailing junk before the terminal-stop check: mojibake, a short
    # closed parenthetical citation "(Artigo 2.º)", then markdown/quote wrappers.
    QW = "*_`\"'»«”“‘’�"                            # quote / emphasis / mojibake wrappers
    tail = re.sub(r"[%s\s]+$" % re.escape(QW), "", ln)
    tail = re.sub(r"\s*\([^()]{0,40}\)$", "", tail)     # trailing short parenthetical citation
    tail = re.sub(r"[%s\s\]\)\}]+$" % re.escape(QW), "", tail)
    if not tail:
        return None
    if tail.endswith((",", ";")):
        return "3a ends on comma/semicolon"
    if DANGLING.search(tail):
        return "3a ends on dangling function word"
    # finance descriptions are full prose paragraphs, so a missing terminal
    # stop is itself a truncation signal; sweep/news bodies end on bylines and
    # headlines, so there we require the stronger comma/dangling signal above.
    if fam == "finance-load" and not tail.endswith(TERMINAL):
        return "3a finance description ends without terminal stop"
    return None

SERIES = os.path.join("logs", "machine-record-audit.csv")
DEFECTS = os.path.join("logs", "machine-record-audit-defects.csv")
# The defect classes, in the order they are carried in the series. Adding a class
# means adding a column here; the reader tolerates an older row missing it.
COLS = ["1 finance date_source:proxy", "2 empty entities[]", "3 truncated but full"]

# Only these gate the check. Class 1 is forbidden outright by finance-record-spec
# (Dates) and class 3 is a false assertion about a body — both are defects on any
# record, in any family.
#
# **Class 2 is carried and never gated.** CLAUDE.md -> The material: academic papers
# and named-analyst opinion are thematic rather than event-driven, so sparse or
# empty `entities` on them is their normal shape and no pass may penalise it — and
# that is most of what the class holds. Gating on it would fail the cycle every time
# the journals sweep admitted a paper, which is how a check stops being read. The
# number stays in the series so the trend is visible; it is context, exactly like
# `proxy_nonfinance`.
GATED = ["1 finance date_source:proxy", "3 truncated but full"]
SERIES_HEADER = (["run_date", "total", "finance-load", "sweep", "other"]
                 + COLS + ["defect_rows", "proxy_nonfinance"])


def _write_csv(path, header, rows):
    # newline="" for the csv module, lineterminator="\n" to pin the EOL: text mode
    # on Windows would write CRLF and every regeneration would diff as a whole file.
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def persist(root, fam_count, defects, rows, proxy_nonfinance, today):
    """Append today's row, rewrite the defect list, and report deterioration.

    Returns the list of classes that grew since the previous row (empty on a first
    run — there is nothing to compare a baseline against, and a baseline is not a
    regression).
    """
    sp = os.path.join(root, SERIES)
    hist, prev = [], None
    if os.path.isfile(sp):
        with open(sp, encoding="utf-8-sig", newline="") as fh:
            hist = list(csv.DictReader(fh))
        # Idempotent per day: a re-run REPLACES today's row rather than appending a
        # second one, and compares against the last row that is not today's. A cycle
        # re-run after a failure would otherwise write a row that is its own baseline
        # and could never show deterioration.
        hist = [r for r in hist if r.get("run_date") != today]
        if hist:
            prev = hist[-1]

    row = ([today, sum(fam_count.values()), fam_count["finance-load"],
            fam_count["sweep"], fam_count["other"]]
           + [sum(defects[c].values()) for c in COLS]
           + [len(rows), proxy_nonfinance])

    worse = []
    if prev:
        for c in GATED:
            was = prev.get(c)
            now = row[SERIES_HEADER.index(c)]
            if was not in (None, "") and int(was) < int(now):
                worse.append("%s %s -> %d" % (c, was, now))

    _write_csv(sp, SERIES_HEADER,
               [[r.get(c, "") for c in SERIES_HEADER] for r in hist] + [row])
    _write_csv(os.path.join(root, DEFECTS), ["file", "family", "defect_class"], sorted(rows))
    return worse, prev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--csv")
    ap.add_argument("--persist", action="store_true",
                    help="append the dated row to logs/machine-record-audit.csv and "
                         "exit 1 on deterioration (LINT #21)")
    ap.add_argument("--date", help="run date to stamp (default today)")
    a = ap.parse_args()

    fam_count = collections.Counter()
    defects = collections.defaultdict(lambda: collections.Counter())  # class -> family -> n
    rows = []
    proxy_nonfinance = 0

    for p in glob.glob(os.path.join(a.root, "raw", "**", "*.md"), recursive=True):
        t = open(p, encoding="utf-8").read()
        fm, body = fm_body(t)
        if not fm:
            continue
        fam = family(fm)
        fam_count[fam] += 1
        rel = os.path.relpath(p, a.root).replace("\\", "/")
        # class 1
        if val(fm, "date_source") == "proxy":
            if fam == "finance-load":
                defects["1 finance date_source:proxy"][fam] += 1
                rows.append((rel, fam, "1 finance date_source:proxy"))
            else:
                proxy_nonfinance += 1
        # class 2
        ent = val(fm, "entities")
        if ent is not None and re.fullmatch(r"\[\s*\]", ent):
            defects["2 empty entities[]"][fam] += 1
            rows.append((rel, fam, "2 empty entities[]"))
        # class 3
        if val(fm, "body_completeness") == "full":
            tr = truncated(body, fam)
            if tr:
                defects["3 truncated but full"][fam] += 1
                rows.append((rel, fam, "3 truncated but full (%s)" % tr))

    fams = ["finance-load", "sweep", "other"]
    W = 30
    print("=== record families ===")
    for f in fams:
        print("  %-14s %5d" % (f, fam_count[f]))
    print("  %-14s %5d" % ("TOTAL", sum(fam_count.values())))
    print("\n=== defect table (rows = class, cols = family) ===")
    print("  %-*s %12s %8s %8s %8s" % (W, "class", "finance-load", "sweep", "other", "TOTAL"))
    for cls in sorted(defects):
        d = defects[cls]
        print("  %-*s %12d %8d %8d %8d" % (W, cls, d["finance-load"], d["sweep"], d["other"],
                                           sum(d.values())))
    print("\n  context: date_source:proxy on non-finance (sanctioned by LINT #11, NOT a defect): %d" % proxy_nonfinance)
    print("  total defect rows: %d" % len(rows))

    if a.csv:
        _write_csv(a.csv, ["file", "family", "defect_class"], sorted(rows))
        print("  wrote per-file list -> %s" % a.csv)

    if not a.persist:
        return 0

    today = a.date or datetime.date.today().isoformat()
    worse, prev = persist(a.root, fam_count, defects, rows, proxy_nonfinance, today)
    print("\n  persisted %s -> %s (+ %s)" % (today, SERIES, DEFECTS))
    if prev is None:
        print("  first row: a baseline, nothing to compare against.")
        return 0
    if not worse:
        print("  no gated defect class rose against %s. OK." % prev["run_date"])
        print("  (gated: %s. Class 2 is carried, never gated — sparse `entities` on a "
              "thematic source is its normal shape.)" % "; ".join(GATED))
        return 0
    print("  DETERIORATION against %s:" % prev["run_date"])
    for w in worse:
        print("    %s" % w)
    print("  Fix the new records, or state on the page why the class grew. The per-file "
          "list in %s says which." % DEFECTS)
    return 1


if __name__ == "__main__":
    sys.exit(main())
