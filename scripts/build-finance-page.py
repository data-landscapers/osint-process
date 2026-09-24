#!/usr/bin/env python3
"""
build-finance-page.py {ISO3} | --all  —  the per-country finance exports.

Called by FINANCE-COMPILE.md (step 4) for each place in scope. Reads that place's
finance records from raw/ and writes three CSV exports:

  1. {ISO3}-nonstate.csv  (one row per deal)
  2. {ISO3}-budget.csv    (one row per year x vote/head x programme-line; stages as columns)
  3. {ISO3}-summary.csv   (aggregates by origin x subject x FY, US$m ball-park,
                           plus one `excluded` row per reason a domestic line sits
                           outside the total — nothing leaves the aggregate silently)

Every row links to its raw/ record. DERIVED — do not hand-edit; rebuilt each compile.

Outputs land in outputs/, OSINT's own compile — no longer a website feed
(2026-08-16, R4): CORPUS compiles its own published copy from the same raw/
records now, and this stays as the substrate REPORT-LINT checks A-E reconcile
against and compile-hub-financing.py reads. The build's two INPUTS
(fx-imf-annual.csv, financier-names.csv) stay in lookups/ (Bill, 2026-08-03).
The same 2026-08-03 change retired the per-country {ISO3}.md report page: it
was a human-readable view of these same three tables and nothing read it. Its
exclusions note survives as the `excluded` rows of the summary export.
"""
import os, re, sys, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import (split_front, fm_get, section, deal_table, raw_sources,  # noqa: E402
                         load_fx, fx_rate, fin_name)                            # noqa: E402

RAW = "raw"
BUDGET_OUT = "outputs/budgets"                 # {ISO3}-budget.csv
NONSTATE_OUT = "outputs/non-state-finance"     # {ISO3}-nonstate.csv, {ISO3}-summary.csv, all-nonstate.csv

# ---------------------------------------------------------------- small helpers
def taxonomy_labels():
    lab = {}
    for ln in open("lookups/taxonomy.md", encoding="utf-8"):
        m = re.match(r'^-\s*`([^`]+)`\s*[—-]\s*(.+?)\s*$', ln)
        if m:
            # A few entries (dpi.registry) carry an editorial ruling after the first
            # sentence, and everything after the dash used to land in the label - so the
            # `sector` and `subject` columns of every export holding such a slug carried
            # ~500 characters of governance prose where "Registries" belongs (housekeeping
            # job 102). Bound it at the first sentence, which is what vault_lib's
            # load_taxonomy() has always done with the same file.
            lab[m.group(1)] = re.split(r'\.\s', m.group(2), maxsplit=1)[0].strip()
    return lab

def fy_label_from_year(y):        # commitment year -> fiscal-year label starting that year
    return f"{y}/{str(int(y)+1)[-2:]}" if y and y.isdigit() else (y or "—")

def primary_subject(rec):
    """The subject a record is filed under: the explicit `primary_subject:`
    override where set, else the first non-finance slug in `topics:`
    (facets.md -> Facets — the order is load-bearing and never sorted)."""
    over = fm_get(rec["fm"], "primary_subject")
    if over and over in rec["topics"]:
        return over
    for t in rec["topics"]:
        if t and not t.startswith("finance."):
            return t
    return ""

def num(s):
    """Accepts '123', '123.45', '-123'. Returns int (rounded) or None.
    Decimals matter: an accounting-system extract reports cents, and the previous
    isdigit() test silently dropped every such figure to None (ETH, 2026-07-27)."""
    if s is None:
        return None
    t = str(s).strip()
    if not t:
        return None
    try:
        return int(round(float(t)))
    except ValueError:
        return None

def usd_millions(s):
    """'US$355,000,000' -> 355 ; 'US$1.30bn' -> 1300 ; 'US$45m' -> 45 ;
    'US$6 200 000 000' -> 6200.

    Space-separated thousands are read as thousands, not as a truncation. Lint #3's
    dated-conversion rewrite reformats money in place, and on 2026-07-28 one such
    rewrite turned `6200000000` into `6 200 000 000 *(dated conversion …)*` — which
    this function read as **6**, silently reporting a US$6.2bn deal as US$6m
    (LSO/Convalt). A percentage is not an amount either: a `Disbursed (USD)` cell
    reading '100% disbursement rate …' must not parse as US$100m.

    A **bare number is dollars, always.** The old `v > 100000` heuristic read a bare
    number below that as already-in-millions, which turned MWI/National Bank of
    Malawi's **US$43,516** sponsorship (MWK 75.5m) into **US$43.5bn** — 44 times
    Malawi's entire tracked finance, and it was sitting in the continental aggregate.
    A sweep of all 1,235 deals on 2026-07-28 found that record was the *only* one the
    heuristic touched, so nothing legitimately encodes millions as a bare number.
    Record millions explicitly (`US$45m`) — never as a bare `45`."""
    if not s:
        return None
    s = s.replace(",", "")
    s = re.sub(r'(?<=\d)[    ](?=\d{3}(?!\d))', '', s)   # 6 200 000 000 -> 6200000000
    m = re.search(r'([\d.]+)\s*(bn|billion|m|million)?', s, re.I)
    if not m:
        return None
    if s[m.end():m.end() + 1] == "%":
        return None
    v = float(m.group(1)); unit = (m.group(2) or "").lower()
    if unit.startswith("b"):
        return v * 1000
    if unit.startswith("m") or unit.startswith("mi"):
        return v
    return v / 1e6                           # a bare number is DOLLARS, always

def clean(s):                                # de-wikilink and de-pipe for a table cell
    s = re.sub(r'\[\[[^\]|]*\|([^\]]+)\]\]', r'\1', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', r'\1', s)
    return s.replace("|", "/").strip()

def fy_display(fm):                          # never a blank cell / blank link text
    return fm_get(fm, "fiscal_year_label") or fm_get(fm, "fy_start")[:4] or "—"

def deal_usd(T):
    """The rule (Bill, 2026-07-29): always use commitment; where no commitment exists,
    use disbursed and note it.

    Returns (value_or_None, basis) with basis in {"commitment", "disbursed", ""}, so
    every surface can *state* the composition of a total instead of leaving a reader to
    infer it. Before this, the fallback happened in two places and not in a third, and
    the page's own total contradicted the rows printed above it (housekeeping job 21).
    """
    v = usd_millions(T.get("Commitment (USD)", ""))
    if v:
        return v, "commitment"
    v = usd_millions(T.get("Disbursed (USD)", ""))
    if v:
        return v, "disbursed"
    return None, ""


# ------------------------------------------------- the domestic classification chain
def vote_num(rec):
    v = fm_get(rec["fm"], "admin_head_code")          # the field, where the record carries it
    if v:
        return v
    m = re.search(r'-vote-?(\d+)', rec["deal_id"])    # fallback: parse the id (pre-migration)
    return m.group(1) if m else ""

def cfield(rec, key, table_key=""):
    """A classification field: frontmatter first, body table as the migration fallback.

    finance-load-domestic-state.md moved the chain into frontmatter on 2026-08-01
    (codes are the cross-year join key, and the compile is scripted — it cannot parse
    prose). The corpus is mid-migration, so fall back to the body table where the
    field is absent. Drop the fallback once housekeeping job 34 is closed."""
    v = fm_get(rec["fm"], key)
    if not v and table_key:
        v = rec["table"].get(table_key, "")
    return clean(v)

def line_name(rec):
    """The programme/line name, from the record itself — not the bare deal_id."""
    T = rec["table"]
    prog = " — ".join(x for x in [cfield(rec, "programme", "Programme"),
                                  cfield(rec, "sub_programme", "Subprogramme")] if x)
    if prog:
        return clean(prog)
    m = re.search(r'[«"“](.+?)[»"”]', rec["title"])           # the quoted line name in the title
    if m:
        return clean(m.group(1))
    ent = re.sub(r'\s*\([^)]*\)\s*$', "", T.get("Spending entity", "")).strip()
    return clean(ent) or rec["deal_id"]

# ---------------------------------------------------------------- USD aggregation
# load_fx / fx_rate moved to finance_lib 2026-08-03 (review task 25) — the FX table
# is read by more than this build, and two loaders would eventually round differently.

def in_headline(r):
    """Domestic record counted in the headline total — matches FINANCE-COMPILE:
    whole-scope, not a transfer, not an unclear supplementary."""
    fm = r["fm"]
    return (fm_get(fm, "scope_confidence") == "whole"
            and fm_get(fm, "is_transfer") != "true"
            and fm_get(fm, "supplementary_basis") != "unclear")

EXCL_LABEL = {                                   # reported one line each, per FINANCE-COMPILE
    "nobase":   "no enacted baseline (⚠ no appropriated figure — revised/outturn only)",
    "scope":    "partial- or unclear-scope",
    "transfer": "transfers to a body counted at its own spending end",
    "supp":     "supplementaries of unclear basis",
    "nofx":     "no FX rate held for the currency",
    "nosubj":   "no subject tag",
}

def excl_reason(r, a, rate):
    """Why a domestic record sits outside the headline aggregate — first reason wins.
    Every domestic record lands in the total or in exactly one of these."""
    fm = r["fm"]
    if not primary_subject(r):
        return "nosubj"
    if a is None:
        return "nobase"                          # the ⚠ records: FINANCE-COMPILE wants this counted
    if rate is None:
        return "nofx"
    if fm_get(fm, "scope_confidence") != "whole":
        return "scope"
    if fm_get(fm, "is_transfer") == "true":
        return "transfer"
    if fm_get(fm, "supplementary_basis") == "unclear":
        return "supp"
    return ""

def aggregate3(ns, dom, fx):
    """Both blocks US$m (ball-park). Domestic converted at the IMF annual average for
    the currency and the fiscal year's START year. Excluded lines are reported apart,
    by reason — nothing leaves the aggregate silently."""
    nsb, doms = {}, {}
    fys_ns, fys_dom = set(), set()
    excl = {}                                    # reason -> [count, US$m where computable]
    for r in ns:
        s = primary_subject(r); fy = fy_label_from_year((r["published"] or "")[:4])
        u = usd_millions(r["table"].get("Commitment (USD)", ""))
        if s and u:
            nsb.setdefault(s, {}).setdefault(fy, 0); nsb[s][fy] += u; fys_ns.add(fy)
    for r in dom:
        s = primary_subject(r); fy = fm_get(r["fm"], "fiscal_year_label")
        a = num(fm_get(r["fm"], "appropriated_total"))
        rate = fx_rate(fx, fm_get(r["fm"], "currency"), fm_get(r["fm"], "fy_start")[:4])
        why = excl_reason(r, a, rate)
        if not why:
            doms.setdefault(s, {}).setdefault(fy, 0); doms[s][fy] += a / rate / 1e6; fys_dom.add(fy)
            continue
        e = excl.setdefault(why, [0, 0.0])
        e[0] += 1
        if a is not None and rate:
            e[1] += a / rate / 1e6
    return nsb, fys_ns, doms, fys_dom, excl

# ---------------------------------------------------------------- CSV exports
# Canonical financier display name (approved map -> entity-page title -> prettified
# slug) moved to finance_lib 2026-08-03: report-lint checks this build's output
# against the same function, so the two must be one function, not two copies.
# `fin_name` stays importable from here — report-lint calls it as `bfp.fin_name`.

def recip_org(T):
    """Recipient organisation, name only — no descriptive suffix, no trailing (ISO3)."""
    v = T.get("Recipient", "").strip()
    if not v or v.lower().startswith("recipient unspecified"):
        return ""
    v = re.split(r'\s[—–]\s|\s-\s', v)[0].strip()      # cut at em/en dash or spaced hyphen only
    v = re.sub(r'\s*\([A-Z]{3}\)\s*$', '', v).strip()  # drop a trailing country tag
    return clean(v)

NS_HEADER = ["recipient_country", "start_year", "end_year", "financier", "sector",
             "instrument", "commitment_usd_m", "amount_basis", "amount_quality", "status",
             "title", "description",
             "beneficiary_type", "recipient_organisation", "original_amount",
             "project_id", "iati_activity_id", "url", "financier_slug", "record"]


def amount_quality(rec):
    """How the amount was arrived at — frontmatter first, body table as fallback.

    `interpolated` is the one value that changes what a page may say: the figure is
    CONSTRUCTED, not published. Four Mastercard Foundation records carry straight-line
    annual increments between anchored milestones, built so the series sums to a
    source-stated cumulative — so the total is real and no single row is. It was
    recorded only as `Estimated` in a body table, which is what 98 genuine estimates
    of a disclosed figure also say, and which nothing downstream could read.
    (Note 101; Bill ruled 'flag them as derived', 2026-08-03.)"""
    return (fm_get(rec["fm"], "amount_quality")
            or rec["table"].get("Amount quality", "")).strip().lower()

def _ns_row(r, country, lab):
    T = r["table"]; fm = r["fm"]
    usd, basis = deal_usd(T)
    sec = primary_subject(r)
    start = T.get("Start year", "") or T.get("Commitment year", "") or (r["published"] or "")[:4]
    return [country, start, T.get("End year", ""),
            fin_name(fm_get(fm, "financier_slug")), lab.get(sec, sec),
            T.get("Instrument", ""), (f"{usd:.0f}" if usd else ""), basis,
            amount_quality(r), T.get("Status", ""),
            r["title"], section(r["body"], "Description"),
            T.get("Beneficiary type", ""), recip_org(T), T.get("Original amount", ""),
            T.get("Project ID", ""), T.get("IATI activity ID", ""),
            r["url"], fm_get(fm, "financier_slug"), r["fn"][:-3]]

def csv_nonstate(ns, lab, iso3, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:   # BOM for Excel
        w = csv.writer(f); w.writerow(NS_HEADER)
        for r in sorted(ns, key=lambda x: x["published"], reverse=True):
            w.writerow(_ns_row(r, iso3, lab))

def csv_nonstate_all(by_place, lab, path):
    """One combined file, one row per deal (deduped by record). recipient_country is
    the record's own place — each deal is tagged to exactly one place (country or, for
    multi-country deals, a region), so this is a clean partition with no double-count."""
    seen = {}
    for iso3, bucket in by_place.items():
        for r in bucket["ns"]:
            seen.setdefault(r["fn"], (r, iso3))   # a deal lives under exactly one place
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f); w.writerow(NS_HEADER)
        for r, iso3 in sorted(seen.values(), key=lambda x: (x[0]["published"] or ""), reverse=True):
            w.writerow(_ns_row(r, iso3, lab))
    return len(seen)

def csv_budget(dom, iso3, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:   # BOM for Excel
        w = csv.writer(f)
        # The classification chain, one column per level with its code — the codes are
        # the cross-year join key (finance-load-domestic-state.md § Classification).
        # programme_line stays as a trailing DISPLAY column: it is all 395 unmigrated
        # records carry. Drop it when housekeeping job 34 closes.
        w.writerow(["fy", "admin_head_code", "admin_head",
                    "spending_entity_code", "spending_entity",
                    "programme_code", "programme",
                    "sub_programme_code", "sub_programme", "econ_class",
                    "appropriated", "revised",
                    "actual", "audited", "exec_vs_voted", "exec_vs_revised",
                    "baseline_stage", "current_stage", "scope_confidence", "is_transfer",
                    "currency", "record", "programme_line"])
        def sk(r):
            n = vote_num(r); return (fm_get(r["fm"], "fy_start"), int(n) if n.isdigit() else 999, r["deal_id"])
        for r in sorted(dom, key=sk):
            fm = r["fm"]
            w.writerow([fy_display(fm), vote_num(r), cfield(r, "admin_head"),
                        cfield(r, "spending_entity_code"),
                        cfield(r, "spending_entity", "Spending entity"),
                        cfield(r, "programme_code"), cfield(r, "programme", "Programme"),
                        cfield(r, "sub_programme_code"),
                        cfield(r, "sub_programme", "Subprogramme"),
                        cfield(r, "econ_class"),
                        fm_get(fm, "appropriated_total"), fm_get(fm, "revised_total"),
                        fm_get(fm, "actual_total"), fm_get(fm, "audited_total"),
                        fm_get(fm, "execution_pct_vs_appropriated"), fm_get(fm, "execution_pct_vs_revised"),
                        fm_get(fm, "baseline_stage"), fm_get(fm, "current_stage"),
                        fm_get(fm, "scope_confidence"), fm_get(fm, "is_transfer"),
                        fm_get(fm, "currency"), r["fn"][:-3], line_name(r)])

def csv_summary(ns, dom, lab, path, fx):
    nsb, fys_ns, doms, fys_dom, excl = aggregate3(ns, dom, fx)
    fys = sorted(set(fys_ns) | set(fys_dom))
    with open(path, "w", newline="", encoding="utf-8-sig") as f:   # BOM for Excel
        w = csv.writer(f)
        blank = ["", ""]                       # the two exclusion columns, empty on a real row
        w.writerow(["origin", "unit", "subject_slug", "subject"] + fys
                   + ["excluded_lines", "excluded_usd_m"])
        for s in sorted(nsb, key=lambda k: -sum(nsb[k].values())):
            w.writerow(["non-state", "US$m", s, lab.get(s, s)]
                       + [(f"{nsb[s][fy]:.0f}" if nsb[s].get(fy) else "") for fy in fys] + blank)
        for s in sorted(doms, key=lambda k: -sum(doms[k].values())):
            w.writerow(["domestic-state", "US$m (IMF annual avg)", s, lab.get(s, s)]
                       + [(f"{doms[s][fy]:.0f}" if doms[s].get(fy) else "") for fy in fys] + blank)
        # Every domestic line is either in the total above or in exactly one row here.
        # These rows carry what the retired report page's "held but excluded" note carried;
        # without them the exclusions leave the aggregate silently, which is the one thing
        # aggregate3 exists to prevent.
        for k in ("nobase", "scope", "transfer", "supp", "nofx", "nosubj"):
            if k not in excl:
                continue
            n, usd = excl[k]
            w.writerow(["excluded", "", k, EXCL_LABEL[k]] + ["" for _ in fys]
                       + [n, (f"{usd:.0f}" if usd else "")])

# ---------------------------------------------------------------- assemble
def scan_all():
    """One pass over raw/: bucket every finance record under each place it tags."""
    by_place = {}
    for fn, path in raw_sources(RAW):
        t = open(path, encoding="utf-8").read()
        if "finance_origin:" not in t:      # cheap prefilter only — a superset, see below
            continue
        fm, body = split_front(t)
        if not fm:
            continue
        # The real test is the frontmatter key, never the file text. A record retired by
        # merge drops `finance_origin:` and says so in its retirement note — so the note's
        # own words passed the prefilter and the record was then bucketed as domestic,
        # putting a junk row in 8 budget exports. (Found and fixed 2026-08-03, housekeeping 38.)
        if not re.search(r'^finance_origin:\s*\S', fm, re.M):
            continue
        pm = re.search(r'places:\s*\[([^\]]*)\]', fm)
        places = re.findall(r'[A-Z]{3}|X[A-Z]{2}', pm.group(1)) if pm else []
        if not places:
            continue
        tm = re.search(r'topics:\s*\[([^\]]*)\]', fm)
        rec = dict(fn=fn, fm=fm, body=body, table=deal_table(body),
                   origin=fm_get(fm, "finance_origin"), published=fm_get(fm, "published"),
                   topics=[x.strip() for x in tm.group(1).split(",")] if tm else [],
                   url=fm_get(fm, "url"), title=fm_get(fm, "title"),
                   deal_id=fm_get(fm, "deal_id"), currency=fm_get(fm, "currency"))
        for pl in places:
            b = by_place.setdefault(pl, {"ns": [], "dom": []})
            b["ns" if rec["origin"] == "non-state" else "dom"].append(rec)
    return by_place

def build_one(iso3, ns, dom, lab, fx):
    csv_nonstate(ns, lab, iso3, os.path.join(NONSTATE_OUT, f"{iso3}-nonstate.csv"))
    csv_summary(ns, dom, lab, os.path.join(NONSTATE_OUT, f"{iso3}-summary.csv"), fx)
    # The domestic budget export (outputs/budgets/{ISO3}-budget.csv) is retired: budget rows
    # are CORPUS's (notes-for-osint 168, R57). The folder keeps its last-built content and
    # nothing here writes or deletes it. Domestic records still feed the summary above.
    return len(ns), len(dom)

def place_codes():
    """Every code `lookups/countries.csv` knows — 54 ISO-3 plus the X__ regions."""
    import csv as _csv
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                        "lookups", "countries.csv")
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {(r.get("iso-3") or r.get("iso3") or "").strip()
                for r in _csv.DictReader(fh)} - {""}


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "ZAF"
    # Any other flag was being read as a place code, so `--help` wrote
    # `--help-nonstate.csv` into outputs/ (found by review task 25's smoke test).
    if arg.startswith("-") and arg != "--all":
        print(__doc__.strip())
        return 0
    lab = taxonomy_labels()
    fx = load_fx()
    for d in (BUDGET_OUT, NONSTATE_OUT):
        os.makedirs(d, exist_ok=True)
    if arg == "--all":
        by_place = scan_all()
        for iso3 in sorted(by_place):
            nn, nd = build_one(iso3, by_place[iso3]["ns"], by_place[iso3]["dom"], lab, fx)
            print(f"  {iso3}: {nn} non-state, {nd} domestic")
        n_all = csv_nonstate_all(by_place, lab, os.path.join(NONSTATE_OUT, "all-nonstate.csv"))
        print(f"wrote CSV exports for {len(by_place)} places to {NONSTATE_OUT}/ and "
              f"{BUDGET_OUT}/ + all-nonstate.csv ({n_all} deals)")
    else:
        # A mistyped place code used to write an empty ZZZ-nonstate.csv and report
        # "wrote ZZZ CSV exports (0 non-state, 0 domestic)" — a run that exported
        # nothing looking exactly like a place with nothing to export, and leaving a
        # bogus export behind for the next reader of the folder (2026-08-22, note 34).
        if arg not in place_codes():
            print("build-finance-page: %s is not a place code in lookups/countries.csv"
                  % arg, file=sys.stderr)
            return 2
        by_place = scan_all()
        b = by_place.get(arg, {"ns": [], "dom": []})     # place-based, matches --all exactly
        nn, nd = build_one(arg, b["ns"], b["dom"], lab, fx)
        # The roll-up is derived from the whole of raw/, not from the scope, and
        # scan_all() has already read the whole of raw/ to find this one place. A
        # scoped run that left it stale guaranteed REPORT-LINT check A red by
        # exactly the number of records the run admitted — a check that cannot
        # pass after the compile its own process mandates. Writing it here costs
        # nothing and touches no budget export, which build_one alone writes.
        n_all = csv_nonstate_all(by_place, lab, os.path.join(NONSTATE_OUT, "all-nonstate.csv"))
        print(f"wrote {arg} CSV exports  ({nn} non-state, {nd} domestic) "
              f"+ all-nonstate.csv ({n_all} deals)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
