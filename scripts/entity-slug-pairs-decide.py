# -*- coding: utf-8 -*-
"""Housekeeping job 24 — adjudicate the entity-census drift pairs.

`entity-census.py` proposes pairs that *look* like variants of one entity. It never
merges them, by design: a prefix match is evidence, not proof. This script turns the
proposal into a decision per pair, and writes `reviews/entity-slug-pairs.csv`, which the
census then reads so a settled pair is never proposed again.

Three rules, applied in order. Each is auditable — the rule that fired is recorded on
the row, so a wrong call is visible as a wrong *rule*, not an opaque judgement.

  1. LEGAL-FORM SUFFIX. One slug is the other plus only legal-form words (ltd, plc, inc,
     group, holdings, sa, …). Same name, same entity -> MERGE to the shorter form.
     `vodacom` / `vodacom-group`.
  2. NORMALISES EQUAL. Strip grammatical filler (of, and, the, de, la, du, d', …),
     fold s/z spelling, drop separators. If the two then match exactly, they are one
     entity written two ways -> MERGE. `ministry-digital-transition-morocco` /
     `ministry-of-digital-transition-morocco`; `digitalisation` / `digitalization`.
  3. Otherwise DISTINCT. Sharing a prefix is not identity: `google` / `google-deepmind`,
     `starlink` / `starlink-airtel-d2c-partnership`, `bank-of-ghana` / `bank-of-uganda`,
     `alsat-3a` / `alsat-3b` are all two objects.

**Manual overrides carry the cases no rule should decide**, and they are the point of
the exercise rather than an embarrassment to it: `ecocash` (entity_type `initiative`,
the mobile-money service) and `ecocash-holdings` (`company`) pass rule 1 and are
nonetheless two objects. Checked by reading both pages.

Canonical side, where a merge fires: the slug that has a page; if both or neither do,
the one with more references; ties break to the shorter slug.
"""
import csv, io, os, re, sys, collections, difflib, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "reviews", "entity-slug-pairs.csv")
ENT = os.path.join(ROOT, "wiki", "entities")

LEGAL = {"limited", "ltd", "plc", "inc", "incorporated", "corporation", "corp",
         "company", "co", "group", "holdings", "holding", "sa", "nv", "bv", "ag",
         "gmbh", "llc", "spa", "srl", "pty", "the"}
FILLER = {"of", "and", "the", "de", "des", "du", "da", "do", "la", "le", "les", "l",
          "d", "et", "for", "a", "au", "aux", "el", "al"}

# Pairs no rule should decide. (a, b) sorted -> (decision, reason)
OVERRIDE = {
    ("ecocash", "ecocash-holdings"):
        ("distinct", "ecocash is entity_type: initiative (the mobile-money service); "
                     "ecocash-holdings is entity_type: company. Two objects, checked on the pages."),
}


ROMAN = re.compile(r"^[ivx]+$")


def norm(slug):
    parts = [p for p in slug.split("-") if p and p not in FILLER]
    # ⚠ Roman numerals are content, not spelling. Keep them whole and marked, or
    # `apis-growth-fund-i` and `apis-growth-fund-ii` normalise to the same string and a
    # rule designed to catch spelling drift silently merges two different funds. Caught
    # on review, 2026-07-29 — the reason this script prints its proposals before applying.
    out = []
    for p in parts:
        out.append("#" + p + "#" if ROMAN.match(p) or p.isdigit() else p)
    s = "".join(out)
    s = s.replace("z", "s")                 # digitalisation / digitalization
    s = s.replace("c", "s")                 # defence / defense
    return s


def decide(a, b, refs, paged):
    key = tuple(sorted((a, b)))
    if key in OVERRIDE:
        d, why = OVERRIDE[key]
        return d, "override", why, ""
    short, long_ = (a, b) if len(a) < len(b) else (b, a)
    if long_.startswith(short + "-"):
        tail = long_[len(short) + 1:].split("-")
        if all(p in LEGAL for p in tail):
            return "merge", "legal-form-suffix", \
                   "%s is %s plus legal-form words only" % (long_, short), canonical(a, b, refs, paged)
        return "distinct", "prefix-plus-content", \
               "%s names a different object, not a spelling of %s" % (long_, short), ""
    if norm(a) == norm(b):
        return "merge", "normalises-equal", \
               "same name written two ways (filler words / s-z spelling)", canonical(a, b, refs, paged)
    return "distinct", "not-a-variant", "similar strings, different entities", ""


def canonical(a, b, refs, paged):
    pa, pb = a in paged, b in paged
    if pa != pb:
        return a if pa else b
    if refs.get(a, 0) != refs.get(b, 0):
        return a if refs.get(a, 0) > refs.get(b, 0) else b
    return a if len(a) <= len(b) else b


def main():
    spec = importlib.util.spec_from_file_location("ec", os.path.join(ROOT, "scripts", "entity-census.py"))
    ec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec)
    counts, paged, _ = ec.load()
    pairs = ec.drift_pairs(counts, paged, include_settled=True)  # re-examine the whole field

    rows, tally = [], collections.Counter()
    for a, ca, b, cb in sorted(pairs):
        d, rule, why, canon = decide(a, b, counts, paged)
        tally[(d, rule)] += 1
        rows.append([a, b, d, canon, rule, why])

    # Close the chains. `africell` / `africell-holding` / `africell-holding-limited` is
    # three pairwise merges; decided pair-by-pair they pick two different canonicals and
    # the rewrite would leave the corpus split rather than joined. Union the merge pairs
    # and elect one canonical per group by the same rule.
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in rows:
        if r[2] == "merge":
            ra, rb = find(r[0]), find(r[1])
            if ra != rb:
                parent[rb] = ra
    groups = collections.defaultdict(set)
    for r in rows:
        if r[2] == "merge":
            groups[find(r[0])].update((r[0], r[1]))
    elected = {}
    for g in groups.values():
        best = sorted(g)[0]
        for s in g:
            best = canonical(best, s, counts, paged)
        for s in g:
            elected[s] = best
    for r in rows:
        if r[2] == "merge":
            r[3] = elected[r[0]]
    print("merge groups after closure: %d" % len(groups))

    with io.open(REG, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["slug_a", "slug_b", "decision", "canonical", "rule", "reason"])
        for r in rows:
            w.writerow(r)

    for (d, rule), n in tally.most_common():
        print("%-9s %-22s %4d" % (d, rule, n))
    print("\npairs decided: %d  ->  %s" % (len(rows), REG))
    merges = {(r[0], r[1], r[3]) for r in rows if r[2] == "merge"}
    print("merges: %d, touching %d slugs" % (len(merges), len({x for m in merges for x in m[:2]})))


if __name__ == "__main__":
    main()
