#!/usr/bin/env python3
"""lint-duplicate-sources.py — same-event clustering over ordinary `raw/` narrative sources.

The non-finance half of `LINT.md` #7. `lint-duplicate-deals.py` covers finance records by
keying on the amount; nothing played the same role for the prose corpus, so the check was
carried by hand and, in practice, by whichever slice of ingest happened to see both items in
one batch. Cross-batch and cross-night pairs were invisible.

**The key is `LINT.md` #7's own — event + entities + date — never title-word overlap alone.**
A crude proxy (same/adjacent date, overlapping places, >=3 shared title words) was tried at
intake and produced 288 candidate pairs since 2026-07-25 and 586 across the year, most of them
false: "digital", "africa" and a country name are enough to collide two unrelated stories. Three
things fix that here:

  * **Shared `entities:` are required.** Two accounts of one development name at least one actor
    in common. This is the signal the proxy lacked entirely and it does most of the work.
  * **Title tokens are IDF-weighted against the corpus's own title vocabulary.** "digital",
    "africa", "data" and every country name earn almost nothing because almost every title
    carries them; "bayobab", "asycuda", "e-kori" are close to decisive on their own. Nothing is
    hand-listed as a stopword — the corpus supplies the weights.
  * **A shared place is required**, since two same-named actors in different countries are a
    different development.

Output is a **candidate report, never a verdict** — the same discipline as the deals script. A
regulator really does issue two adjacent statements naming the same parties, so each cluster is
read and adjudicated per `CLAUDE.md` -> *Duplicates* (Drop / Replace / Keep both).

**Pairs already linked by `hub_line_sources:` are excluded and counted separately.** That link
*is* a prior keep-both ruling: the wiki decided both accounts are held and merged their hub
bullet, which is exactly what #7 would conclude. Reporting them again would be re-litigating a
settled call every run.

An adjudicated cluster goes in `reviews/source-duplicate-decisions.csv` and is never reported
again, so the report converges instead of re-presenting the same reads. Both settled verdicts
suppress: `DISTINCT` (not the same event — a false positive) and `KEEP-BOTH` (the same event,
but each source holds payload the other lacks, which `CLAUDE.md` -> *Duplicates* keeps).

Usage:
    python scripts/lint-duplicate-sources.py                     # whole corpus
    python scripts/lint-duplicate-sources.py --since 2026-07-01  # by publication date
    python scripts/lint-duplicate-sources.py --days 1            # tighter date window
    python scripts/lint-duplicate-sources.py --min-score 0.55    # tighter title bar
    python scripts/lint-duplicate-sources.py --csv out.csv       # full list for working
Exit 1 where candidates are found, so a caller can gate on it.
"""
import argparse
import csv
import datetime as dt
import glob
import math
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DECISIONS = os.path.join(ROOT, "reviews", "source-duplicate-decisions.csv")

LIST_RE = lambda k: re.compile(rf"(?m)^{k}:\s*\[(.*?)\]\s*$", re.S)
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'-]{2,}")


def frontmatter(text):
    return text.split("\n---", 1)[0]


def scalar(fm, key):
    m = re.search(rf"(?m)^{key}:\s*(.*)$", fm)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def listval(fm, key):
    m = LIST_RE(key).search(fm)
    if not m:
        return []
    return [v.strip().strip("[]") for v in m.group(1).split(",") if v.strip().strip("[]")]


def is_finance(fm, text):
    return bool(scalar(fm, "deal_id") or scalar(fm, "financier_slug")
                or "## Deal record" in text)


def load():
    docs = []
    for p in glob.glob(os.path.join(ROOT, "raw", "**", "*.md"), recursive=True):
        try:
            text = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        fm = frontmatter(text)
        if scalar(fm, "type") != "source" or is_finance(fm, text):
            continue
        pub = scalar(fm, "published")[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", pub):
            continue
        docs.append({
            "slug": os.path.basename(p)[:-3],
            "path": os.path.relpath(p, ROOT).replace("\\", "/"),
            "published": pub,
            "date": dt.date.fromisoformat(pub),
            "title": scalar(fm, "title"),
            "publisher": scalar(fm, "publisher"),
            "url": scalar(fm, "url"),
            "completeness": scalar(fm, "body_completeness"),
            "places": set(listval(fm, "places")),
            "entities": set(listval(fm, "entities")),
            "cosources": set(listval(fm, "hub_line_sources")),
            "has_hub": bool(re.search(r"(?m)^hub_line:", fm)),
        })
    return docs


def idf_weights(docs):
    """Document frequency over title tokens — the corpus decides what is distinctive."""
    df = Counter()
    for d in docs:
        df.update(set(TOKEN_RE.findall(d["title"].lower())))
    n = max(1, len(docs))
    return {t: math.log(n / (1 + c)) for t, c in df.items()}


def title_score(a, b, w):
    ta = set(TOKEN_RE.findall(a["title"].lower()))
    tb = set(TOKEN_RE.findall(b["title"].lower()))
    if not ta or not tb:
        return 0.0
    shared = sum(w.get(t, 0.0) for t in ta & tb)
    total = sum(w.get(t, 0.0) for t in ta | tb)
    return shared / total if total else 0.0


def load_decisions():
    ruled = set()
    if not os.path.exists(DECISIONS):
        return ruled
    with open(DECISIONS, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            if (row.get("verdict") or "").strip():
                ruled.add(frozenset([row["slug_a"].strip(), row["slug_b"].strip()]))
    return ruled


def confidence(shared_ents, gap, score):
    """Title similarity leads; the entity count supports it, and never gates it.

    A first cut made >=2 shared entities a condition of HIGH, which inverted the ranking: pairs
    with *identical* titles and one shared actor — a wire story and its pickup, which is the
    commonest true duplicate in this corpus — were filed WEAK beneath loose three-entity matches.
    An identical title is the strongest single signal available and outranks the actor count.
    """
    if score >= 0.60 or (score >= 0.45 and len(shared_ents) >= 2 and gap <= 1):
        return "HIGH"
    if score >= 0.40 or (score >= 0.32 and len(shared_ents) >= 2):
        return "CHECK"
    return "WEAK"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, default=3,
                    help="max gap in published dates (default 3)")
    ap.add_argument("--min-score", type=float, default=0.30,
                    help="min IDF-weighted title similarity (default 0.30)")
    ap.add_argument("--since", help="only sources published on/after YYYY-MM-DD")
    ap.add_argument("--csv", help="write the full candidate list here")
    ap.add_argument("--include-cosourced", action="store_true",
                    help="also report pairs already linked by hub_line_sources")
    a = ap.parse_args()

    docs = load()
    if a.since:
        docs = [d for d in docs if d["published"] >= a.since]
    docs.sort(key=lambda d: d["date"])
    w = idf_weights(docs)
    ruled = load_decisions()

    by_date = defaultdict(list)
    for d in docs:
        by_date[d["date"]].append(d)

    pairs, cosourced, seen = [], 0, set()
    for d in docs:
        for off in range(0, a.days + 1):
            for e in by_date.get(d["date"] + dt.timedelta(days=off), []):
                if e["slug"] == d["slug"]:
                    continue
                key = frozenset([d["slug"], e["slug"]])
                if key in seen:
                    continue
                seen.add(key)
                if key in ruled:
                    continue
                if not (d["places"] & e["places"]):
                    continue
                shared = d["entities"] & e["entities"]
                if not shared:
                    continue
                if e["slug"] in d["cosources"] or d["slug"] in e["cosources"]:
                    cosourced += 1
                    if not a.include_cosourced:
                        continue
                score = title_score(d, e, w)
                if score < a.min_score:
                    continue
                gap = abs((e["date"] - d["date"]).days)
                pairs.append((confidence(shared, gap, score), score, d, e, sorted(shared), gap))

    order = {"HIGH": 0, "CHECK": 1, "WEAK": 2}
    pairs.sort(key=lambda r: (order[r[0]], -r[1]))

    # #7 adjudicates a *cluster*, not a pair: one launch reported by five outlets is five
    # sources and one decision, not ten pairwise ones. Union-find over the surviving pairs.
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    for _, _, d, e, _, _ in pairs:
        union(d["slug"], e["slug"])
    clusters = defaultdict(set)
    for slug in parent:
        clusters[find(slug)].add(slug)

    tally = Counter(p[0] for p in pairs)
    print(f"lint duplicate-sources: {len(docs):,} narrative sources, "
          f"{len(pairs)} candidate pair(s) "
          f"[HIGH {tally['HIGH']} / CHECK {tally['CHECK']} / WEAK {tally['WEAK']}]")
    print(f"  window {a.days}d, title bar {a.min_score}, shared entity + shared place required")
    print(f"  {cosourced} pair(s) already linked by hub_line_sources — a prior keep-both ruling, "
          f"{'shown' if a.include_cosourced else 'excluded'}")
    sizes = Counter(len(v) for v in clusters.values())
    print(f"  {len(clusters)} cluster(s) after transitive merge — "
          + ", ".join(f"{n} x {size} sources" for size, n in sorted(sizes.items())))
    if ruled:
        print(f"  {len(ruled)} pair(s) already adjudicated in {os.path.relpath(DECISIONS, ROOT)} — never re-reported")

    for conf, score, d, e, shared, gap in pairs:
        print(f"\n  [{conf}] score {score:.2f}  gap {gap}d  shared: {', '.join(shared[:5])}")
        print(f"      {d['published']}  {d['slug']}")
        print(f"          {d['title'][:104]}  ({d['publisher'][:34]}, {d['completeness']})")
        print(f"      {e['published']}  {e['slug']}")
        print(f"          {e['title'][:104]}  ({e['publisher'][:34]}, {e['completeness']})")

    if a.csv:
        with open(a.csv, "w", encoding="utf-8", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["confidence", "score", "gap_days", "shared_entities",
                         "slug_a", "published_a", "title_a", "publisher_a", "completeness_a",
                         "slug_b", "published_b", "title_b", "publisher_b", "completeness_b"])
            for conf, score, d, e, shared, gap in pairs:
                wr.writerow([conf, f"{score:.3f}", gap, " ".join(shared),
                             d["slug"], d["published"], d["title"], d["publisher"], d["completeness"],
                             e["slug"], e["published"], e["title"], e["publisher"], e["completeness"]])
        print(f"\n  full list -> {a.csv}")

    return 1 if pairs else 0


if __name__ == "__main__":
    sys.exit(main())
