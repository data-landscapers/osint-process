#!/usr/bin/env python3
"""compile-hub-financing.py — FINANCE-COMPILE.md step 2, as a script.

Rewrites the derived sentences of a place hub's `## Financing` section from the
finance records, so hub and per-country page can never drift (the two outputs the
pass promises come from one aggregation). Reads
`outputs/non-state-finance/{ISO3}-nonstate.csv`, which `build-finance-page.py`
writes from `raw/` — same scan, same numbers.

**What it rewrites, and only this:**
  - the `**Non-state** — …` paragraph (total, deal count, year range, non-USD note,
    top financiers grouped on `financier_slug`, leading subjects);
  - the counts in `Instrument mix: …`;
  - the *as of* date in the section's italic header — **only when one of those two
    actually moved** (2026-08-22, note 34, closing post-run note 207). It was stamped
    with today's date unconditionally, so every hub differed from a recompile on any
    day the compile had not already been re-run: REPORT-LINT check B reported all 58
    as drifted every time it ran, and three sessions rewrote 58 hubs to move one date
    each. The stamp dates the figures, not the run — if the aggregate has not moved,
    neither has the date on which it was established. Run with the fix in place, the
    corpus reports 0 rewrites and 58 unchanged: there was never any drift.

**What it never touches:** the `**Domestic state**` block, the `Material deals:`
line, and any hand-written caveat following the instrument counts. Those carry
judgment a script cannot reproduce — a Kenyan domestic block runs to fifteen lines
of stage-ladder analysis, and clobbering it to regenerate a total would lose far
more than it fixed. A caveat sentence after the mix counts is preserved verbatim.

Usage:  python scripts/compile-hub-financing.py [--write] [ISO3 ...]
Default is a dry run listing what would change.
"""
import csv, datetime, os, re, sys
from collections import defaultdict

FIN = "outputs/non-state-finance"
PLACES = "wiki/places"
# The compile date, stamped into each section's "as of". Defaults to today —
# never a constant: a hardcoded date silently backdates every later run, which is
# exactly the staleness CLAUDE.md -> Currency exists to keep visible.
# (Was pinned at 2026-07-28 until housekeeping job 11, 2026-07-29.)
ASOF = os.environ.get("COMPILE_ASOF") or datetime.date.today().isoformat()


def money(m):
    """US$m float -> the house rendering: US$1.23bn / US$576m / US$14m / US$0.4m."""
    if m >= 1000:
        return "US$%.2fbn" % (m / 1000)
    if m >= 1:
        return "US$%.0fm" % m
    return "US$%.2fm" % m


def load(iso3):
    p = os.path.join(FIN, "%s-nonstate.csv" % iso3)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def non_state_paragraph(rows):
    with_usd = [r for r in rows if (r.get("commitment_usd_m") or "").strip()]
    without = len(rows) - len(with_usd)
    years = sorted({r["start_year"] for r in rows if (r.get("start_year") or "").strip()})
    span = "%s–%s" % (years[0], years[-1]) if years else ""

    subj = defaultdict(float)
    for r in rows:
        if (r.get("sector") or "").strip():
            subj[r["sector"].strip()] += 1
    lead = ", ".join("`%s`" % s for s, _ in sorted(subj.items(), key=lambda kv: (-kv[1], kv[0]))[:3])
    lead_clause = " Leading subjects: %s." % lead if lead else ""

    if not rows:
        # A place whose last deal was withdrawn: say so, rather than "0 deals held ()".
        return "**Non-state** — no deal records held."

    if not with_usd:
        return ("**Non-state** — %d deals held (%s); amounts stated only in non-USD "
                "currencies, so no USD total is computed.%s" % (len(rows), span, lead_clause))

    total = sum(float(r["commitment_usd_m"]) for r in with_usd)
    by_fin = defaultdict(float)
    names = {}
    for r in with_usd:
        slug = (r.get("financier_slug") or "").strip() or (r.get("financier") or "").strip()
        by_fin[slug] += float(r["commitment_usd_m"])
        names.setdefault(slug, (r.get("financier") or slug).strip())
    top = sorted(by_fin.items(), key=lambda kv: -kv[1])[:3]
    tops = "; ".join("%s (%s)" % (names[s], money(v)) for s, v in top)

    # "1 further deal carry" — the noun was inflected and the verb was not. The verb
    # takes the -s in the singular and the noun in the plural, so they move oppositely:
    # "1 further deal carries", "2 further deals carry".
    note = (" (%d further deal%s carr%s only a non-USD amount, not summed.)"
            % (without, "" if without == 1 else "s",
               "ies" if without == 1 else "y")) if without else ""

    # The rule (Bill, 2026-07-29): always commitment; where none exists, disbursed —
    # and say so. `amount_basis` is written per row by build-finance-page.py, so the
    # composition is stated rather than inferred. Older CSVs lack the column; absent it
    # the clause is simply omitted rather than guessed at.
    fell_back = sum(1 for r in with_usd if (r.get("amount_basis") or "").strip() == "disbursed")
    if fell_back:
        basis = (" Commitments, except %d carrying only a disbursed figure because no "
                 "commitment is published." % fell_back)
    else:
        basis = ""

    # An interpolated amount is CONSTRUCTED, not published: a straight-line increment
    # between anchored milestones, built so the series sums to a source-stated
    # cumulative. The total is real and no single row is, so the aggregate has to say
    # so rather than let a reader take every row as reported (note 101, Bill 2026-08-03).
    interp = sum(1 for r in with_usd if (r.get("amount_quality") or "").strip() == "interpolated")
    if interp:
        basis += (" %d amount%s interpolated between anchored milestones, not stated by any "
                  "source — the series sums to a published cumulative, the annual split "
                  "does not." % (interp, " is" if interp == 1 else "s are"))

    return ("**Non-state** — %s across %d deals (%s).%s%s Top financiers: %s.%s"
            % (money(total), len(with_usd), span, basis, note, tops, lead_clause))


def instrument_counts(rows):
    c = defaultdict(int)
    for r in rows:
        i = (r.get("instrument") or "").strip()
        i = re.sub(r'\s*\*\(.*', '', i).strip()   # drop an in-field caveat: the label, not the note
        if i:
            c[i] += 1
    if not c:
        return None
    return ", ".join("%s %d" % (k, v) for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def rewrite(iso3, write=False):
    rows = load(iso3)
    p = os.path.join(PLACES, "%s.md" % iso3)
    if rows is None:
        return None                      # no export for this place: nothing to compile
    if not os.path.exists(p):
        return ("no hub page", iso3)
    raw = open(p, "rb").read().decode("utf-8")
    if "## Financing" not in raw:
        # This compiler replaces a section; it does not mint one. That is deliberate
        # — where the section goes on the page is an editorial call — but returning
        # None made it indistinguishable from "no deals", so a place that gained its
        # first deal was skipped in silence. XSA was the live instance (one unpriced
        # pipeline grant, no section, nothing said). Name it instead.
        return ("no section", iso3, len(rows))

    # keepends: each line keeps its own terminator, so a mixed-EOL file (this repo has
    # them) comes back byte-identical apart from the lines actually rewritten. An
    # earlier version normalised the whole file and showed 160 phantom changed lines.
    lines = raw.splitlines(keepends=True)
    para = non_state_paragraph(rows)
    mix = instrument_counts(rows)
    changed, in_fin = False, False
    asof_at = None            # index of the italic header; stamped only if content moved

    for i, ln in enumerate(lines):
        body = ln.rstrip("\r\n")
        eol = ln[len(body):]
        if body.startswith("## "):
            in_fin = body.strip() == "## Financing"
        if not in_fin:
            continue
        new = body
        if body.startswith("*Aggregate of tracked digital-transformation finance"):
            asof_at = i
            continue
        elif body.startswith("**Non-state** — "):
            new = para
        elif body.startswith("Instrument mix: ") and mix:
            m = re.match(r'Instrument mix: .*?\.((?:\s\*\*.*)?)$', body)
            new = "Instrument mix: %s.%s" % (mix, m.group(1) if m else "")
        elif body.startswith("Instrument mix: ") and not rows:
            new = None     # no deals, so no mix: the line goes
        if new is None:
            lines[i] = ""
            if i + 1 < len(lines) and not lines[i + 1].strip():
                lines[i + 1] = ""
            changed = True
        elif new != body:
            lines[i] = new + eol
            changed = True

    # The stamp follows the figures. Advancing it on a run that changed nothing is what
    # made REPORT-LINT check B a guaranteed daily false positive over all 58 hubs.
    if changed and asof_at is not None:
        body = lines[asof_at].rstrip("\r\n")
        eol = lines[asof_at][len(body):]
        lines[asof_at] = re.sub(r'(\*\*as of )\d{4}-\d{2}-\d{2}(\*\*)',
            r'\g<1>' + ASOF + r'\g<2>', body) + eol

    if not changed:
        return ("unchanged", iso3)
    if write:
        open(p, "wb").write("".join(lines).encode("utf-8"))
    return ("rewritten", iso3)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    write = "--write" in sys.argv
    known = sorted(os.path.basename(f).split("-")[0]
                   for f in os.listdir(FIN) if f.endswith("-nonstate.csv")
                   and not f.startswith("all-"))
    isos = args or known
    # A mistyped ISO-3 selects nothing and would print "0 hub sections / unchanged: 0"
    # — a run that compiled nothing looking exactly like a run with nothing to compile
    # (2026-08-22, note 34). Refuse it instead.
    unknown = [i for i in isos if i not in known]
    if unknown:
        sys.stderr.write("compile-hub-financing: no export for %s — known: %s\n"
                         % (" ".join(unknown), " ".join(known)))
        return 2
    done = defaultdict(list)
    for iso in isos:
        r = rewrite(iso, write)
        if r:
            done[r[0]].append(iso)
    print("%s: %d hub sections" % ("rewritten" if write else "would rewrite",
                                   len(done["rewritten"])))
    if done["rewritten"]:
        print("  " + " ".join(done["rewritten"]))
    print("unchanged: %d" % len(done["unchanged"]))
    # A place with deals and no section to replace used to return None and vanish.
    for state, note in (("no section", "have no `## Financing` section to land in"),
                        ("no hub page", "have no hub page at all")):
        if done[state]:
            print("\n%d place(s) %s — this compiler replaces a section, it does not "
                  "mint one, so these are skipped and named rather than silently dropped: %s"
                  % (len(done[state]), note, " ".join(done[state])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
