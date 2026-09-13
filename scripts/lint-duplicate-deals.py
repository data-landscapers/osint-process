#!/usr/bin/env python3
"""lint-duplicate-deals.py — cross-family duplicate detection over non-state deals.

Lint #7 keys on `deal_id`, so it only sees duplicates that share an ID pattern. The
Boston University *Chinese Loans to Africa* back-swing created second records for deals
already held under a different pattern, and every such pair was invisible to it — while
both records were counted in the country's hub aggregate. MOZ was reporting China
Eximbank at US$464m on two identical US$132m Tmcel records: an 11% overstatement of the
country's whole non-state total, on the flagship output.

**The key is (financier_slug, place, amount) — deliberately NOT recipient_slug or year.**
The obvious key is (financier, recipient, amount, year); it would have missed the very
pair that prompted this check. `eximbank-cn-moz-002` carries `recipient_slug: tmcel` and
year 2020; `eximbank-cn-moz-004` carries `mozambique-telecom-sa` and 2022 — one company
under two slugs, two years apart, the same US$132,000,000. Slug drift and re-dated
re-captures are *normal* between two sources describing one deal, so neither can sit in
the key. **The amount is the fingerprint**; recipient and year are reported so a reader
can adjudicate, and a matching recipient slug only raises confidence.

Output is a **candidate** report, never a verdict. A financier really does lend one
country equal tranches for different projects, so each group is read against the two
titles and adjudicated per housekeeping job 36's method — retire by merge, never
deletion. Confidence is annotated:

    HIGH   identical amount, same recipient_slug
    DRIFT  identical amount, different recipient_slug   (also an entity-pass signal)
    CHECK  near-identical amount within tolerance

Records already merged away (`retired_deal_id:` and no `finance_origin:`) are skipped —
they are in no aggregate.

Usage:
    python scripts/lint-duplicate-deals.py                  # all financiers
    python scripts/lint-duplicate-deals.py --financier china-eximbank
    python scripts/lint-duplicate-deals.py --amount-tol 0   # identical amounts only
Exit status is 1 where candidates are found, so a cycle step can gate on it.
"""
import argparse, os, re, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import split_front, fm_get, deal_table, raw_sources   # noqa: E402

RAW = "raw"
DECISIONS = "reviews/deal-duplicate-decisions.csv"


def group_key(grp):
    """Stable identity for an adjudicated group: its deal_ids, sorted."""
    return "|".join(sorted(r["deal_id"] for r in grp))


def load_decisions():
    """Groups already ruled on. Without this the same round-number collisions —
    US$15m to three different funds — are re-reported every cycle until the check
    is ignored, which is how a check dies. Same device as the entity pass's
    `entity-mint-decisions.csv`."""
    seen = set()
    if not os.path.exists(DECISIONS):
        return seen
    import csv as _csv
    with open(DECISIONS, encoding="utf-8-sig") as fh:
        for row in _csv.DictReader(fh):
            if row.get("deal_ids"):
                seen.add("|".join(sorted(x.strip() for x in row["deal_ids"].split("|"))))
    return seen


def usd(s):
    """'US$132,000,000' -> 132000000.0 ; 'US$1.3bn' -> 1.3e9 ; '' -> None."""
    if not s:
        return None
    s = s.replace(",", "")
    s = re.sub(r'(?<=\d)[   ](?=\d{3}(?!\d))', '', s)
    m = re.search(r'([\d.]+)\s*(bn|billion|m|million)?', s, re.I)
    if not m or s[m.end():m.end() + 1] == "%":
        return None
    v = float(m.group(1))
    u = (m.group(2) or "").lower()
    return v * 1e9 if u.startswith("b") else (v * 1e6 if u.startswith("m") else v)


def deal_year(fm, T):
    for k in ("Commitment year", "Start year"):
        m = re.search(r'(\d{4})', T.get(k, "") or "")
        if m:
            return int(m.group(1))
    m = re.search(r'(\d{4})', fm_get(fm, "published") or "")
    return int(m.group(1)) if m else None


def load():
    out = []
    for fn, path in raw_sources(RAW):
        t = open(path, encoding="utf-8").read()
        if "finance_origin: non-state" not in t:
            continue                      # domestic-state lines and non-records
        fm, body = split_front(t)
        if not fm or fm_get(fm, "retired_deal_id"):
            continue                      # already merged away
        T = deal_table(body)
        pm = re.search(r'places:\s*\[([^\]]*)\]', fm)
        places = re.findall(r'[A-Z]{3}', pm.group(1)) if pm else []
        amt = usd(T.get("Commitment (USD)", "")) or usd(T.get("Disbursed (USD)", ""))
        if not amt or not fm_get(fm, "financier_slug"):
            continue
        out.append(dict(fn=fn, deal_id=fm_get(fm, "deal_id") or "(none)",
                        fin=fm_get(fm, "financier_slug"),
                        rcp=fm_get(fm, "recipient_slug") or "(none)",
                        place=places[0] if places else "(none)",
                        title=(fm_get(fm, "title") or "").strip('"'),
                        amt=amt, yr=deal_year(fm, T)))
    return out


def confidence(a, b):
    if a["amt"] == b["amt"]:
        return "HIGH " if a["rcp"] == b["rcp"] else "DRIFT"
    return "CHECK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--financier", help="restrict to one financier_slug")
    ap.add_argument("--amount-tol", type=float, default=0.0,
                    help="fractional tolerance on the amount (default 0 = identical amounts only; "
                         "widen for an investigation sweep, e.g. 0.15)")
    ap.add_argument("--all", action="store_true",
                    help="include groups already adjudicated in the decisions register")
    a = ap.parse_args()

    decided = load_decisions()
    recs = load()
    if a.financier:
        recs = [r for r in recs if r["fin"] == a.financier]

    buckets = defaultdict(list)
    for r in recs:
        buckets[(r["fin"], r["place"])].append(r)

    groups = []
    for key, rs in buckets.items():
        rs.sort(key=lambda r: r["amt"])
        used = set()
        for i, x in enumerate(rs):
            if i in used:
                continue
            grp = [x]
            for j in range(i + 1, len(rs)):
                if j in used:
                    continue
                y = rs[j]
                if abs(x["amt"] - y["amt"]) <= a.amount_tol * max(x["amt"], y["amt"]):
                    grp.append(y)
                    used.add(j)
            if len(grp) > 1:
                if not a.all and group_key(grp) in decided:
                    continue          # adjudicated once; never re-reported
                groups.append((key, grp))

    if not groups:
        print(f"lint duplicate-deals: {len(recs)} non-state records, no candidate duplicates.")
        return 0

    dupes = 0
    for (fin, place), grp in sorted(groups, key=lambda g: g[0]):
        fams = {re.sub(r'[-_]\d+$', '', r["deal_id"]) for r in grp}
        conf = confidence(grp[0], grp[1])
        print(f"\n[{conf}] {fin} -> {place}"
              + ("   ** cross-family **" if len(fams) > 1 else ""))
        for r in grp:
            print(f"    {r['deal_id']:<34} US${r['amt']:>14,.0f}  {r['yr']}  "
                  f"{r['rcp']}\n        {r['title'][:96]}\n        {r['fn']}")
        dupes += len(grp) - 1
    print(f"\n{len(groups)} candidate group(s); {dupes} record(s) potentially double-counted.")
    print("HIGH/DRIFT = identical amount. Adjudicate per housekeeping job 36 — "
          "retire by merge, never deletion.")
    print("A group ruled DISTINCT goes in %s and is never reported again." % DECISIONS)
    return 1


if __name__ == "__main__":
    sys.exit(main())
