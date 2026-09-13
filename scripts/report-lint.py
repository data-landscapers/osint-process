#!/usr/bin/env python3
"""report-lint.py — REPORT-LINT.md, the verification pass over the reporting layer.

Lint's checks stop at `raw/` and page hygiene. **Nothing verified what the compile
layer publishes**, and that is where the wiki's numbers actually reach a reader:

  - nothing reconciled a compiled aggregate against its own record set, which is why
    the MOZ China Eximbank double-count survived and overstated non-state finance by
    US$132m until someone read the deals by hand;
  - nothing compared a hub's `## Financing` against the export it must agree with —
    two hubs sat stamped `as of 2026-07-20` while their records moved on;
  - nothing checked a display name against the canonical map, so the July financier
    defect was fixed at the slug layer and left standing at the display layer.

The country, region and topic reports (`REPORT-COUNTRY.md`, task 29) inherit whatever this
layer publishes, unverified. This is the check that has to exist first.

**It verifies; it does not compile.** Every failure here has a known repair — run
`FINANCE-PAGES.md` or `FINANCE-COMPILE.md` — and REPORT-LINT deliberately does not
run it, because a check that silently fixes what it measures can never tell you the
compile is not being run. Use `--fix` to have it print the exact commands.

The five checks (permanent handles, cited from REPORT-LINT.md):

  A  aggregate vs records   the exports rebuild identically from raw/
  B  hub vs export          the hub's Financing prose matches a recompile
  C  as-of freshness        the hub's as-of is not older than its newest record
  D  display names          every financier_slug resolves through financier-names.csv
  E  prose vs compile       every figure and deal link in the hand-written part of
                            `## Financing` is carried by the records

Usage:
  python scripts/report-lint.py            all checks, all places
  python scripts/report-lint.py KEN MOZ    scope to places
  python scripts/report-lint.py --check A  one check
  python scripts/report-lint.py --fix      print the repair commands for what failed
Exit code 1 if any check fails.
"""
import argparse
import csv
import importlib.util
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIN_OUT = "outputs/non-state-finance"
PLACES = "wiki/places"
FINNAMES = "lookups/financier-names.csv"


def load(name, filename):
    """Import a hyphenated sibling script as a module.

    The compilers are imported rather than reimplemented **on purpose**: a checker
    that carries its own copy of the aggregation is checking its copy, not the
    compile. Two copies of one rule is the failure this vault keeps relearning.
    """
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, "scripts", filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------ small helpers
def read_text(path):
    return open(path, "rb").read().decode("utf-8", "surrogateescape")


def hub_path(iso3):
    return os.path.join(ROOT, PLACES, "%s.md" % iso3)


def financing_section(iso3):
    """The lines of a hub's `## Financing` section, or None."""
    p = hub_path(iso3)
    if not os.path.exists(p):
        return None
    lines = read_text(p).splitlines()
    out, inside = [], False
    for ln in lines:
        if ln.startswith("## "):
            if inside:
                break
            inside = ln.strip() == "## Financing"
            continue
        if inside:
            out.append(ln)
    return out if inside or out else None


def csv_rows(path):
    p = os.path.join(ROOT, path)
    if not os.path.isfile(p):
        return None
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def all_hubs():
    return sorted(f[:-3] for f in os.listdir(os.path.join(ROOT, PLACES)) if f.endswith(".md"))


def isos_with_exports():
    d = os.path.join(ROOT, FIN_OUT)
    return sorted(f.split("-")[0] for f in os.listdir(d)
                  if f.endswith("-nonstate.csv") and not f.startswith("all-"))


MULT = {"": 1, "m": 1e6, "mi": 1e6, "bn": 1e9, "bi": 1e9, "tn": 1e12, "tr": 1e12}
# (?<![A-Za-z]) is load-bearing: with re.I the single-letter rand prefix otherwise
# matches the "r 2024" inside "13 Novembe|r 2024| ..." and reports the year as a
# figure the records do not carry.
MONEY_RE = re.compile(r"(?<![A-Za-z])(?:US\$|\$|€|£|R|₦|GH₵|FCFA|CFA|XAF|XOF|RMB|EUR|USD|Kz)\s?"
                      r"([\d][\d,.\s  ]*?)\s*"
                      r"(bn|billion|m|million|tn|trillion|mil milhões)?(?![\w.])",
                      re.I)


def _amount(digits, unit):
    """A money string -> its value in base units, or None.

    The corpus is multilingual and the separators disagree: `FCFA 3,28 billion`
    (French decimal comma), `FCFA 69 673 862 396` (space thousands), `US$1,390,000`
    (comma thousands). Reading the comma one way corpus-wide misreads the other, so
    the shape decides — a comma followed by exactly three digits is a separator,
    otherwise it is a decimal point.
    """
    s = re.sub(r"(?<=\d)[\s  ](?=\d{3}(?!\d))", "", digits.strip())
    s = s.rstrip(" .,")
    if re.fullmatch(r"\d{1,3}(,\d{3})+(\.\d+)?", s):
        s = s.replace(",", "")
    elif re.fullmatch(r"\d+,\d{1,2}", s):
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s) * MULT.get((unit or "").lower()[:2], 1)
    except ValueError:
        return None


def money_tokens(text):
    """Every money figure in the text, as a set of normalised magnitudes.

    Compared by VALUE, never by rendering: the hub writes `US$1.39bn` where the
    record writes `US$1,390,000,000` and the export writes `1390`. Three renderings,
    one number — matching the strings would flag every correctly-compiled hub.
    """
    out = set()
    for m in MONEY_RE.finditer(text):
        v = _amount(m.group(1), m.group(2))
        if v:
            out.add("%.6g" % v)
    return out


# ------------------------------------------------------------------------ CHECK A
def check_a(bfp, isos):
    """Every export rebuilds identically from raw/.

    The strong form: rebuild the row set in memory and compare the deal identities
    and the USD column, not just a total. A total can agree while two rows are
    wrong in opposite directions, and the MOZ double-count is exactly the shape
    that hides inside a total.
    """
    fails = []
    by_place = bfp.scan_all()
    lab = bfp.taxonomy_labels()
    for iso in isos:
        bucket = by_place.get(iso, {"ns": [], "dom": []})
        want = {r["fn"][:-3]: bfp._ns_row(r, iso, lab) for r in bucket["ns"]}
        held = csv_rows("%s/%s-nonstate.csv" % (FIN_OUT, iso))
        if held is None:
            if want:
                fails.append((iso, "no %s-nonstate.csv, but raw/ holds %d deals" % (iso, len(want))))
            continue
        have = {r["record"]: r for r in held}
        missing = sorted(set(want) - set(have))
        extra = sorted(set(have) - set(want))
        if missing:
            fails.append((iso, "%d deal(s) in raw/ but not in the export: %s"
                          % (len(missing), ", ".join(missing[:3]))))
        if extra:
            fails.append((iso, "%d row(s) in the export with no record in raw/: %s"
                          % (len(extra), ", ".join(extra[:3]))))
        idx = bfp.NS_HEADER.index("commitment_usd_m")
        for k in sorted(set(want) & set(have)):
            w = str(want[k][idx] or "")
            h = str(have[k].get("commitment_usd_m") or "")
            if w != h:
                fails.append((iso, "%s: commitment_usd_m export=%r rebuild=%r" % (k, h, w)))
    # the combined export is a partition of the per-place ones, deduped by record
    allrows = csv_rows("%s/all-nonstate.csv" % FIN_OUT)
    if allrows is not None:
        union = {r["fn"][:-3] for b in by_place.values() for r in b["ns"]}
        got = {r["record"] for r in allrows}
        if union != got:
            fails.append(("all", "all-nonstate.csv holds %d deals, raw/ holds %d (%d missing, "
                                 "%d orphaned)" % (len(got), len(union),
                                                   len(union - got), len(got - union))))
    return fails


# ------------------------------------------------------------------------ CHECK B
def check_b(chf, isos):
    """The hub's Financing prose is what a recompile would write.

    Reuses the compiler's own dry run, so drift here means the compile has not been
    run since the records changed - never a disagreement about how to compute it.
    """
    fails = []
    for iso in isos:
        r = chf.rewrite(iso, write=False)
        if r and r[0] == "rewritten":
            fails.append((iso, "hub `## Financing` differs from a recompile — "
                               "the aggregate on the page is stale"))
    return fails


# ------------------------------------------------------------------------ CHECK C
def check_c(bfp, isos):
    """The as-of stamp is not older than the newest record it claims to aggregate.

    Compared against the DATA, never a file mtime: mtimes do not survive a clone,
    and the question is whether the page has been compiled since the records moved.
    """
    fails = []
    by_place = bfp.scan_all()
    for iso in isos:
        sec = financing_section(iso)
        if not sec:
            continue
        m = re.search(r"\*\*as of (\d{4}-\d{2}-\d{2})\*\*", "\n".join(sec))
        recs = by_place.get(iso, {"ns": [], "dom": []})
        newest = max([(r["published"] or "") for r in recs["ns"] + recs["dom"]] or [""])
        if not m:
            if recs["ns"] or recs["dom"]:
                fails.append((iso, "`## Financing` carries no **as of** stamp"))
            continue
        if newest and m.group(1) < newest:
            fails.append((iso, "as of %s, but the newest finance record is %s — "
                               "not compiled since" % (m.group(1), newest)))
    return fails


# ------------------------------------------------------------------------ CHECK D
def check_d(bfp, isos):
    """Every financier_slug in the exports resolves through financier-names.csv.

    fin_name() falls back to an entity-page title and then to a prettified slug, so
    an unmapped slug still renders something plausible - which is how nine World
    Bank variants reached the display layer after the slug layer was fixed. The
    fallback is the right runtime behaviour and the wrong thing to leave unaudited.
    """
    fails = []
    # The approved map, read from the shared library rather than from the build's
    # own copy of it (review task 25, 2026-08-03) — this check compares the build's
    # output against the map, so it must not read the map through the build.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import finance_lib                                               # noqa: E402
    mapped = set(finance_lib.load_financier_names())
    seen = defaultdict(set)
    for iso in isos:
        for r in csv_rows("%s/%s-nonstate.csv" % (FIN_OUT, iso)) or []:
            slug = (r.get("financier_slug") or "").strip()
            if slug:
                seen[slug].add(iso)
            shown = (r.get("financier") or "").strip()
            if slug and shown and shown != bfp.fin_name(slug):
                fails.append((iso, "%s: export shows %r, the map gives %r"
                              % (slug, shown, bfp.fin_name(slug))))
    for slug in sorted(set(seen) - mapped):
        where = sorted(seen[slug])
        fails.append((where[0] if len(where) == 1 else "%d places" % len(where),
                      "financier_slug `%s` is in no row of %s — displayed by fallback"
                      % (slug, FINNAMES)))
    return fails


# ------------------------------------------------------------------------ CHECK E
GENERATED = ("*Aggregate of tracked digital-transformation finance",
             "**Non-state** — ", "Instrument mix: ")


def check_e(isos):
    """A deal link or a non-state figure in the HAND-WRITTEN part of `## Financing`,
    carried by no record.

    The compiler rewrites three lines and leaves the rest alone by design — the
    domestic block, the `Material deals:` line and any caveat carry judgment a
    script cannot reproduce. That exemption is right, and it also means this text is
    the one part of the section nothing verifies: it is CC-authored, so it cannot be
    checked by re-running anything, and a figure in it goes stale invisibly.

    **Scoped to the non-state part** — the lines before `**Domestic state**` — and
    tables are skipped. The domestic block is drawn from the *budget* export and is
    mostly derived analysis (subtotals, exclusions, per-programme reasoning), so
    every honest sentence in it holds a figure that is in no single record cell. A
    figure check there reads ~90% false-positive, which is precisely how lint #3's
    old money scan stopped being read. The limit is stated in `REPORT-LINT.md`
    rather than papered over with a noisy check.
    """
    fails = []
    for iso in isos:
        sec = financing_section(iso)
        if not sec:
            continue
        rows = csv_rows("%s/%s-nonstate.csv" % (FIN_OUT, iso)) or []
        records = {r["record"] for r in rows}
        corpus = " ".join(" ".join(str(v) for v in r.values()) for r in rows)
        held = money_tokens(corpus)
        # the export carries the USD column in millions, unprefixed
        millions = {r["commitment_usd_m"].strip()
                    for r in rows if (r.get("commitment_usd_m") or "").strip()}
        held |= {"%.6g" % (float(v) * 1e6) for v in millions}
        # ...and it ROUNDS that column to whole millions, so the export cannot carry a
        # figure the record states precisely. CIV's two Bank of China loans are
        # US$83,851,564 each and reach the CSV as `84`, so prose citing US$83.85m — the
        # right figure — read as unsourced. Accept a prose value that rounds onto a held
        # million. This is the export's own precision, not an arbitrary tolerance.
        held_m = {round(float(v)) for v in millions}
        domestic = False
        for ln in sec:
            s = ln.strip()
            if s.startswith("**Domestic state**"):
                domestic = True
            elif s.startswith("Material deals:"):
                domestic = False              # the deal list sits BELOW the domestic block
            if domestic or not s or s.startswith(GENERATED) or s.startswith("|"):
                # the domestic block cites budget records, not deals — both tests
                # are exempt there, same as the docstring's stated exemption
                continue
            for slug in re.findall(r"\[\[([^\]|#]+)", ln):
                t = slug.strip()
                if re.match(r"^\d{4}-\d{2}-\d{2}", t) and t not in records:
                    fails.append((iso, "`Material deals:` cites [[%s]], which is not a "
                                       "deal in %s-nonstate.csv" % (t, iso)))
            for tok in money_tokens(ln):
                if tok in held or round(float(tok) / 1e6) in held_m:
                    continue
                fails.append((iso, "figure %s in hand-written non-state prose is "
                                   "carried by no deal record: %s" % (tok, s[:80])))
    return fails


# ------------------------------------------------------------------------ CHECK F
def check_f(chb, isos):
    """`## Recent developments` is what a recompile would write.

    Financing is not the only compiled aggregate on a hub. `HUB-COMPILE.md` builds
    the Recent developments block from the sources' `hub_line` fields, and it is
    fired by ingest — so a source admitted by a slice that died, or by a run whose
    compile was scoped to other places, leaves a bullet written and never placed.
    Same assertion as B, other compiler.
    """
    fails = []
    by_place, _undated, _held = chb.collect()
    # Every hub, not only the ones with a finance export: this check is about
    # hub_lines, and a hub with no deals still has Recent developments.
    for iso in isos:
        r = chb.compile_place(iso, by_place.get(iso, []), write=False)
        if r == "rewritten":
            fails.append((iso, "`## Recent developments` differs from a recompile — "
                               "hub_lines are written but not placed"))
        elif r == "no-markers":
            fails.append((iso, "`## Recent developments` has no compile markers — "
                               "never cut over (compile-hubs.py --init)"))
    return fails


# --------------------------------------------------------------------------- main
CHECKS = "ABCDEF"
TITLE = {"A": "aggregate vs records", "B": "hub vs export", "C": "as-of freshness",
         "D": "display names", "E": "prose vs compile", "F": "hub bullets vs sources"}
REPAIR = {
    "A": "python scripts/build-finance-page.py --all        (FINANCE-PAGES.md)",
    "B": "python scripts/compile-hub-financing.py --write    (FINANCE-COMPILE.md step 2)",
    "C": "python scripts/compile-hub-financing.py --write    (FINANCE-COMPILE.md step 2)",
    "D": "add the slug to lookups/financier-names.csv, then rebuild the exports",
    "E": "hand-edit the hub: re-source the figure, or delete it (no script owns this text)",
    "F": "python scripts/compile-hubs.py --write               (HUB-COMPILE.md)",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("places", nargs="*")
    ap.add_argument("--check", default=CHECKS, help="subset of ABCDE")
    ap.add_argument("--fix", action="store_true", help="print the repair command per failure")
    a = ap.parse_args()

    os.chdir(ROOT)                       # the compilers use repo-relative paths
    bfp = load("bfp", "build-finance-page.py")
    chf = load("chf", "compile-hub-financing.py")
    chb = load("chb", "compile-hubs.py")

    isos = a.places or isos_with_exports()
    hubs = a.places or all_hubs()          # F is about hub_lines, not deals
    run = [c for c in CHECKS if c in a.check.upper()]
    # A --check naming no real check would run nothing and still print the full place
    # count and "0 failure(s)" — a check that read nothing looking exactly like a check
    # that found nothing (2026-08-22, note 34). Refuse it instead.
    if not run:
        print("report-lint: --check %r names no check — known: %s"
              % (a.check, CHECKS), file=sys.stderr)
        return 2
    unknown = sorted(set(a.check.upper()) - set(CHECKS))
    if unknown:
        print("report-lint: ignoring unknown check(s) %s — known: %s"
              % ("".join(unknown), CHECKS), file=sys.stderr)
    results = {}
    for c in run:
        results[c] = {"A": lambda: check_a(bfp, isos),
                      "B": lambda: check_b(chf, isos),
                      "C": lambda: check_c(bfp, isos),
                      "D": lambda: check_d(bfp, isos),
                      "E": lambda: check_e(isos),
                      "F": lambda: check_f(chb, hubs)}[c]()

    total = 0
    for c in run:
        f = results[c]
        total += len(f)
        print("%s  %-22s %s" % (c, TITLE[c], "OK" if not f else "%d failure(s)" % len(f)))
        for where, why in f[:40]:
            print("     %-6s %s" % (where, why))
        if len(f) > 40:
            print("     ... and %d more" % (len(f) - 40))
        if f and a.fix:
            print("     fix: %s" % REPAIR[c])

    print("\n%d place(s) checked, %d failure(s)." % (len(isos), total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
