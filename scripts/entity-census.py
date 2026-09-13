#!/usr/bin/env python3
"""Entity census — the input to the entity pass (ENTITY-PASS.md).

Counts how many SOURCES tag each entity slug, and reports which slugs are over
the schemas.md §5 paging bar without a page, which pages exist below it, and
which slugs look like drift variants of one another.

    python scripts/entity-census.py                 # summary
    python scripts/entity-census.py --csv OUT.csv   # + per-slug rows
    python scripts/entity-census.py --mintable      # just the over-bar, unpaged list

Counts are of tagging sources in raw/ only — a wiki/ page citing an entity is not
independent evidence that it is material.
"""
import argparse, csv, glob, os, re, sys, collections, difflib

RAW = "raw/*/*.md"          # raw/ is sharded raw/YYYY/ (housekeeping 18)
ENTDIR = "wiki/entities"
WATCHLIST = os.path.join(ENTDIR, "_watchlist.md")

def entity_tags(text):
    """Slugs from an `entities: [[a], [b]]` frontmatter list."""
    m = re.search(r'^entities:\s*\[(.*?)\]\s*$', text[:4000], re.M | re.S)
    if not m:
        return []
    return [s.strip() for s in re.findall(r'\[([^\[\]]+)\]', m.group(1)) if s.strip()]

def load():
    counts = collections.Counter()
    for p in glob.glob(RAW):
        try:
            t = open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        for slug in set(entity_tags(t)):        # one source counts once
            counts[slug] += 1
    paged = {os.path.splitext(os.path.basename(p))[0]
             for p in glob.glob(os.path.join(ENTDIR, "*.md"))
             if not os.path.basename(p).startswith("_")}
    watch = ""
    if os.path.exists(WATCHLIST):
        watch = open(WATCHLIST, encoding='utf-8', errors='replace').read().lower()
    return counts, paged, watch

def settled_pairs():
    """Pairs already adjudicated in `reviews/entity-slug-pairs.csv` (housekeeping job 24).

    A settled pair is not proposed again — whether it was merged (in which case the
    variant is gone anyway) or recorded as two distinct entities. Without this the census
    re-proposes `google` / `google-deepmind` on every run for ever, and the real drift is
    buried under ~700 permanent false positives."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "reviews", "entity-slug-pairs.csv")
    if not os.path.exists(p):
        return set()
    import csv as _csv
    with open(p, encoding="utf-8") as fh:
        return {tuple(sorted((r["slug_a"], r["slug_b"]))) for r in _csv.DictReader(fh)}


def drift_pairs(counts, paged, include_settled=False):
    """Slugs that look like variants of one entity: one is a prefix of the other,
    or they are within one edit of each other. Reported, never auto-merged.

    Pairs recorded in `reviews/entity-slug-pairs.csv` are suppressed unless
    `include_settled` — which is how job 24's decider sees the whole field."""
    settled = set() if include_settled else settled_pairs()
    slugs = sorted(set(counts) | paged)
    out = []
    by_head = collections.defaultdict(list)
    for s in slugs:
        by_head[s.split('-')[0]].append(s)
    for head, group in by_head.items():
        if len(group) < 2 or len(head) < 4:
            continue
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if tuple(sorted((a, b))) in settled:
                    continue
                if a.startswith(b) or b.startswith(a) or \
                   difflib.SequenceMatcher(None, a, b).ratio() > 0.86:
                    out.append((a, counts.get(a, 0), b, counts.get(b, 0)))
    return out

def settled_mints(include_settled=False):
    """Slugs already adjudicated in `reviews/entity-mint-decisions.csv` (housekeeping
    job 27). A slug the entity pass looked at and left as a tag — because the mentions
    are passing, because it is the finance records' sovereign recipient key, because
    its agencies are the real actors — is not a backlog item. Without this the census
    re-proposes the same ~160 rejections for ever and the real new arrivals are buried
    under them. Pass --all to see the raw list."""
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "reviews", "entity-mint-decisions.csv")
    if include_settled or not os.path.exists(p):
        return set()
    with open(p, encoding="utf-8") as fh:
        return {r["slug"] for r in csv.DictReader(fh)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--mintable", action="store_true")
    ap.add_argument("--all", action="store_true",
                    help="ignore reviews/entity-mint-decisions.csv and show every over-bar slug")
    ap.add_argument("--bar", type=int, default=3)
    a = ap.parse_args()

    counts, paged, watch = load()
    tagged = set(counts)
    settled = settled_mints(a.all)

    over = sorted((s for s in tagged if counts[s] >= a.bar and s not in paged
                   and s not in settled),
                  key=lambda s: -counts[s])
    onwatch = sorted(s for s in tagged
                     if s not in paged and s not in over
                     and re.search(re.escape(s.replace('-', '[ -]')), watch))
    under_paged = sorted((s for s in paged if counts.get(s, 0) < a.bar),
                         key=lambda s: counts.get(s, 0))
    orphan_pages = sorted(s for s in paged if s not in tagged)

    if a.mintable:
        for s in over:
            print("%4d  %s" % (counts[s], s))
        return

    print("entity census")
    print("  distinct slugs tagged in raw/ : %d" % len(tagged))
    print("  entity pages                  : %d" % len(paged))
    print("  tagged but unpaged            : %d" % len(tagged - paged))
    print()
    print("  OVER THE BAR (>=%d sources) and unpaged : %d   <- the mint list" % (a.bar, len(over)))
    if settled:
        print("  (settled in entity-mint-decisions.csv    : %d, suppressed; --all to show)"
              % len(settled))
    print("  on the watchlist and unpaged            : %d" % len(onwatch))
    print("  paged but under the bar                 : %d" % len(under_paged))
    print("  pages with zero tagging sources         : %d" % len(orphan_pages))
    print()
    print("  top of the mint list:")
    for s in over[:15]:
        print("    %4d  %s" % (counts[s], s))

    pairs = drift_pairs(counts, paged)
    print()
    print("  possible slug drift pairs (report only, never auto-merged): %d" % len(pairs))
    for x in pairs[:10]:
        print("    %s (%d)  ~  %s (%d)" % x)

    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["slug", "sources", "has_page", "band"])
            for s in sorted(tagged | paged, key=lambda x: -counts.get(x, 0)):
                n = counts.get(s, 0)
                band = "over-bar" if n >= a.bar else ("1-2" if n else "0")
                w.writerow([s, n, s in paged, band])
        print("\n  wrote %s" % a.csv)

if __name__ == "__main__":
    main()
