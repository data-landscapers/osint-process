#!/usr/bin/env python3
"""lint-finance-slugs.py — LINT.md check #16 (finance slug resolution).

Every finance record (frontmatter carries `finance_origin`) must key its
financier — and its recipient where one is named — on a canonical entity slug,
not the free-text descriptive string. String-keying is what split *World Bank
Group* from *World Bank* into two hub lines for one financier (repo-review
tasks 6-8). This check enforces `wiki/finance-record-spec.md` -> *Entities*.

Exit status:
  0  no hard defects (soft/novel-financier notes may still print)
  1  hard defects found — FAIL LOUDLY. A blank or non-canonical financier_slug
     silently fragments a hub aggregate, so it must never pass quietly.

Severity follows the spec's own model (`finance-record-spec.md` -> *Entities*): a
bad FINANCIER slug fragments a hub aggregate, so it fails loudly; RECIPIENT drift
is "cheap" and reconciled by the entity pass, so it is surfaced, not failed.

Hard defects — FINANCIER only (exit 1):
  A  finance record with no financier_slug            (empty entities -> build error)
  B  malformed financier_slug (not lowercase kebab-case)
  C  financier_slug value absent from the record's `entities:`
  D  known NON-CANONICAL financier alias (e.g. world-bank-group -> world-bank)
  E  financier_slug with no row in lookups/financier-names.csv (the financier record)
  F  malformed financier-names.csv row: origin not ISO-3 or MULTI, financier_type
     outside FIN_TYPES, african not true/false, or african set without an origin

Soft notes — surfaced for a human glance, never failed (exit 0):
  R  recipient_slug malformed / non-canonical alias / absent from `entities:`
  O  financier-names.csv row with origin not established (origin and african blank)
  N  novel financier_slug — well-formed, in `entities`, not aliased, and used
     by only this one record. Minting a new consistent slug is allowed
     (spec); this just flags a one-off for a second look. **Used to also
     require "no wiki/entities/ page" as a corroborating signal — dropped
     2026-08-16 (R11), entity pages retired, so usage count is what's left.**

Usage:  python scripts/lint-finance-slugs.py [--root DIR] [--strict] [--quiet]
        --strict  treat soft novel-financier notes as failures too
"""
import argparse, glob, os, re, sys, collections

# Known non-canonical financier aliases -> the slug that must be used instead.
# Seed from the World Bank Group / World Bank split (task 7). IFC and MIGA are
# distinct WBG institutions and keep their own slugs — do NOT map them here.
ALIASES = {
    "world-bank-group": "world-bank",
    "the-world-bank": "world-bank",
    "worldbank": "world-bank",
    "international-bank-for-reconstruction-and": "world-bank",  # truncated IBRD slug
    "china-government-unspecified": "government-of-china",  # 2015 Chinese-donations load
}

# Sovereign-borrower aliases (housekeeping job 28). Same defect as the IBRD one above,
# on the recipient side: two loads named the same state two ways — the Chinese-lender
# load wrote `government-of-ghana`, the World Bank IDA/IBRD load wrote `republic-of-ghana`
# — so a recipient aggregate split by *lender*, the one axis it must not split by.
# The canonical form is `government-of-<country>`; the full map with per-slug reasons is
# `reviews/sovereign-slug-map.csv`, and `scripts/sovereign-slug-apply.py` applies it.
def _sovereign_aliases():
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "reviews", "sovereign-slug-map.csv")
    if not os.path.exists(p):
        return {}
    import csv as _csv
    with open(p, encoding="utf-8") as fh:
        return {r["slug"]: r["target"] for r in _csv.DictReader(fh)
                if r["decision"] == "merge" and r["target"]}

ALIASES.update(_sovereign_aliases())

# financier-names.csv is the financier record: one row per slug, carrying
# origin (ISO-3 of the owning state, MULTI for a multilateral), type, url and
# whether the owner is African. `wiki/finance-record-spec.md` -> *Entities*.
# origin: by ownership, not headquarters — a subsidiary takes its parent's (Vodacom
# GBR, Airtel Africa IND); headquarters only where ownership is not public; blank
# where neither is established. african: true where the owner is African — an
# African state, African-owned capital, or a multilateral owned by African states
# (AfDB, Afreximbank, BOAD); blank exactly when origin is. url: the financier's
# own site, entered only once it has resolved.
FIN_TYPES = {"multilateral", "bilateral-agency", "bilateral-dfi", "domestic-state",
             "state-owned", "foundation", "nonprofit", "private"}
ORIGIN_RE = re.compile(r"^(?:[A-Z]{3}|MULTI)$")

def load_financiers(root):
    import csv as _csv
    p = os.path.join(root, "lookups", "financier-names.csv")
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as fh:
        return {r["financier_slug"].strip(): r for r in _csv.DictReader(fh) if r.get("financier_slug")}

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def fm_of(text):
    if not text.startswith("---"): return None
    end = text.find("\n---", 3)
    return text[3:end] if end != -1 else None

def line(fm, key):
    m = re.search(r"^%s:[^\r\n]*" % re.escape(key), fm, re.M)
    return m.group(0) if m else None

def val(fm, key):
    l = line(fm, key)
    return l.split(":", 1)[1].strip() if l else None

def entity_slugs(fm):
    l = line(fm, "entities") or ""
    return re.findall(r"\[([a-z0-9][a-z0-9-]*)\]", l)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    recs = []
    for p in glob.glob(os.path.join(a.root, "raw", "**", "*.md"), recursive=True):
        t = open(p, encoding="utf-8").read()
        fm = fm_of(t)
        if fm and "finance_origin" in fm:
            recs.append((os.path.relpath(p, a.root), fm))

    fin_usage = collections.Counter(val(fm, "financier_slug") for _, fm in recs if val(fm, "financier_slug"))
    hard = collections.defaultdict(list)   # class -> [(file, detail)]
    soft = collections.defaultdict(list)

    fins = load_financiers(a.root)
    FN = "lookups/financier-names.csv"
    for slug, r in sorted(fins.items()):
        origin, ftype, afr = ((r.get(k) or "").strip() for k in ("origin", "financier_type", "african"))
        if origin and not ORIGIN_RE.match(origin):
            hard["F malformed financier record"].append((FN, "%s origin=%r" % (slug, origin)))
        if ftype not in FIN_TYPES:
            hard["F malformed financier record"].append((FN, "%s financier_type=%r" % (slug, ftype)))
        if afr not in ("true", "false", ""):
            hard["F malformed financier record"].append((FN, "%s african=%r" % (slug, afr)))
        elif bool(afr) != bool(origin):
            hard["F malformed financier record"].append((FN, "%s african and origin must both be set or both blank" % slug))
        if not origin:
            soft["O financier origin not established"].append((FN, slug))

    for rel, fm in recs:
        ents = set(entity_slugs(fm))
        fin = val(fm, "financier_slug")
        rec = val(fm, "recipient_slug")
        # --- primary_subject: hard, since 2026-07-28 (post-run note 37) ---
        # The compiled pages file a record under one subject. Leaving that to `topics:`
        # order means any sort re-files it silently: consolidate-budget-lines.py did
        # exactly that on 2026-07-26 and left ZAF reporting US$1m of connectivity spend.
        ps = val(fm, "primary_subject")
        topics = [t.strip() for t in
                  (re.search(r"^topics:\s*\[(.*?)\]\s*$", fm, re.M | re.S).group(1).split(",")
                   if re.search(r"^topics:\s*\[(.*?)\]\s*$", fm, re.M | re.S) else []) if t.strip()]
        if not ps:
            hard["P missing primary_subject"].append((rel, "required on finance records"))
        elif ps not in topics:
            hard["P primary_subject not in topics"].append((rel, "primary_subject=%s" % ps))
        elif ps.startswith("finance."):
            hard["P primary_subject is a finance tag"].append((rel, "primary_subject=%s" % ps))
        # --- financier: hard ---
        if not fin:
            hard["A missing financier_slug"].append((rel, "empty entities -> build error"))
            continue
        if not SLUG_RE.match(fin):
            hard["B malformed financier_slug"].append((rel, "financier_slug=%r" % fin))
        if fin in ALIASES:
            hard["D non-canonical financier alias"].append((rel, "%s -> use %s" % (fin, ALIASES[fin])))
        if fin not in ents:
            hard["C financier_slug not in entities"].append((rel, "financier_slug=%s" % fin))
        if fin not in fins:
            hard["E financier_slug has no financier record"].append((rel, "add %s to %s" % (fin, FN)))
        # --- recipient: soft (entity pass owns recipient drift) ---
        if rec:
            if not SLUG_RE.match(rec):
                soft["R recipient_slug malformed"].append((rel, "recipient_slug=%r" % rec))
            elif rec in ALIASES:
                soft["R recipient_slug non-canonical"].append((rel, "%s -> use %s" % (rec, ALIASES[rec])))
            elif rec not in ents:
                soft["R recipient_slug not in entities"].append((rel, "recipient_slug=%s" % rec))
        # --- novel financier: soft ---
        if SLUG_RE.match(fin) and fin in ents and fin not in ALIASES:
            if fin_usage[fin] <= 1:
                soft["N novel financier_slug (confirm not a variant)"].append((rel, "financier_slug=%s" % fin))

    n_hard = sum(len(v) for v in hard.values())
    n_soft = sum(len(v) for v in soft.values())
    if not a.quiet:
        print("finance records checked: %d | distinct financiers: %d" % (len(recs), len(fin_usage)))
        for cls in sorted(hard):
            print("\n[HARD] %s — %d" % (cls, len(hard[cls])))
            for rel, d in hard[cls][:200]:
                print("   %s  (%s)" % (rel, d))
        for cls in sorted(soft):
            print("\n[soft] %s — %d" % (cls, len(soft[cls])))
            for rel, d in soft[cls][:200]:
                print("   %s  (%s)" % (rel, d))
    print("\nRESULT: %d hard (financier) defects, %d soft notes" % (n_hard, n_soft))
    fail = n_hard > 0 or (a.strict and n_soft)
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
