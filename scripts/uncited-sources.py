#!/usr/bin/env python3
"""uncited-sources.py — admitted sources that no wiki page cites.

Written 2026-08-03. Lint #4 covers the *forward* direction — a `[[link]]`
pointing at nothing, and pages missing from their indexes. Nothing covered the
inverse: a source admitted to `raw/` that no page in `wiki/` cites. That gap is
invisible by construction, because an uncited source breaks nothing; it simply
stops being part of the argument. It surfaced when a housekeeping merge on
`tech.ai` silently dropped the last citation of a source and only a hand-written
check caught it.

An uncited source is **not automatically a defect** — it is a question:
ingest admitted it as worth holding, so either a page should be using it, or
the admission was marginal. Read the list, don't drain it.

**Finance and budget records are excluded by design.** They carry
`finance_origin` / `deal_id` / `retired_deal_id` and reach the wiki through
`FINANCE-COMPILE.md`'s aggregates, not through `[[wikilinks]]` — 1,600+ of them
would otherwise drown the signal. A record retired by `cite_through:` is
reported separately, since it is *meant* to be cited through its survivor.

**A budget-document companion cited only by those records counts as cited**
(added 2026-08-23, housekeeping job 30, `finance.budget`). `wiki/finance-load-domestic-state.md`
-> *The budget document gets one companion source page* has every line-item record
link the companion rather than repeat the citation, so the companion is used exactly
as designed and no wiki page will ever link it. Scanning `wiki/` alone could not see
that, and reported 19 of them as backlog on this page — permanently, since nothing a
session could do would clear them. They are now counted and reported on their own line.

Usage:
  python scripts/uncited-sources.py                 # summary + counts by year
  python scripts/uncited-sources.py --list          # every uncited source
  python scripts/uncited-sources.py --list -n 40    # first 40
  python scripts/uncited-sources.py --year 2026     # only sources published in 2026
  python scripts/uncited-sources.py --place KEN     # only sources tagged with a place
  python scripts/uncited-sources.py --recent 30     # ingested in the last N days (the useful one)
  python scripts/uncited-sources.py --csv out.csv   # slug,published,ingested,places,title
  python scripts/uncited-sources.py --fm-only       # registered in frontmatter, written nowhere

The recency filter is the one to reach for after a run: a source ingested today
and cited nowhere usually means a Phase B write was missed.
"""
import argparse, csv, os, re, sys
from collections import Counter
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finance_lib import raw_sources   # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
WIKI = os.path.join(ROOT, "wiki")

LINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
# A frontmatter link-list is `sources: [[a], [b], [c]]` (facets.md §1) — the
# brackets PAIR, so only the list's own outer bracket doubles up and LINK_RE sees
# none of it. Frontmatter `sources:` is what lint #4/#12 read and is the authority
# for which sources a page cites, so a scan that misses it under-reports every page
# whose citations live there. Found 2026-08-03, when 186 concept-page citations
# moved from a duplicated body list into frontmatter and the count appeared to drop.
FM_LIST_RE = re.compile(r"^(?:sources|entities):[ \t]*\[(.*)\][ \t\r]*$", re.M)
FM_ITEM_RE = re.compile(r"\[([^\[\]]+)\]")
AGGREGATED_RE = re.compile(r"^(finance_origin|deal_id|retired_deal_id):", re.M)
CITE_THROUGH_RE = re.compile(r"^cite_through:", re.M)
# Files that *document* the link convention rather than citing — same exclusion
# lint #4 makes. A quoted example is not a citation.
SKIP_WIKI = {"reference.md", "facets.md", "layout.md", "schemas.md", "intake.md", "operations.md", "finance-record-spec.md", "finance-load-domestic-state.md",
             "finance-news-driver.md", "capture-rule.md", "origin-screen.md"}


def field(head, name):
    m = re.search(rf"^{name}: *(.+)$", head, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def scan_raw():
    """-> {slug: meta} for prose sources, plus the excluded counts and the set of
    slugs those excluded records cite (the budget-document companions)."""
    prose, aggregated, cited_through, by_record = {}, 0, {}, set()
    for f, path in raw_sources(RAW):
        slug = f[:-3]
        with open(path, "rb") as fh:
            raw_bytes = fh.read()
        head = raw_bytes[:2400].decode("utf-8", errors="replace")
        if AGGREGATED_RE.search(head):
            aggregated += 1
            # A finance record links its budget-document companion instead of
            # repeating the citation, so those links are real citations.
            text = raw_bytes.decode("utf-8", errors="replace")
            by_record |= {s.strip() for s in LINK_RE.findall(text)}
            for inner in FM_LIST_RE.findall(text):
                by_record |= {s.strip() for s in FM_ITEM_RE.findall(inner)}
            continue
        meta = {"published": field(head, "published"), "ingested": field(head, "ingested"),
                "places": field(head, "places") or field(head, "place"),
                "title": field(head, "title")}
        if CITE_THROUGH_RE.search(head):
            cited_through[slug] = meta
            continue
        prose[slug] = meta
    by_record.discard("")
    return prose, aggregated, cited_through, by_record


def scan_wiki():
    """-> (every [[target]] referenced anywhere under wiki/, those written into body prose,
    {slug: [pages]} for frontmatter registrations).

    The split matters and the reason is a blind spot found on 2026-08-21 (housekeeping job 30,
    `tech.innovate`): a source listed in a page's frontmatter `sources:` and written into no
    prose on that page — or on any other — reads as *cited* to this script, because frontmatter
    IS the citation authority for pages that keep their citations there (see FM_LIST_RE above).
    The two rules are individually right and together they hide a whole class of source. On
    `tech.innovate` 21 of 120 registered sources had no prose behind them, and one of them was
    the citation a job-10 split had taken off with the text it belonged to. Corpus-wide the
    figure was 292. `--fm-only` reports them; nothing else changes.
    """
    seen, in_body, fm_pages = set(), set(), {}
    for d, _dirs, files in os.walk(WIKI):
        for f in files:
            if not f.endswith(".md") or f in SKIP_WIKI:
                continue
            path = os.path.join(d, f)
            with open(path, "rb") as fh:
                text = fh.read().decode("utf-8", errors="replace")
            parts = text.split("---", 2)
            head, body = (parts[1], parts[2]) if len(parts) >= 3 and text.lstrip().startswith("---") else ("", text)
            seen |= set(LINK_RE.findall(text))
            in_body |= set(LINK_RE.findall(body))
            for inner in FM_LIST_RE.findall(head):
                for s in FM_ITEM_RE.findall(inner):
                    fm_pages.setdefault(s.strip(), []).append(os.path.relpath(path, ROOT))
                    seen.add(s.strip())
    return seen, in_body, fm_pages


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", action="store_true", help="print every uncited source")
    ap.add_argument("-n", "--limit", type=int, help="cap the printed list")
    ap.add_argument("--year", help="only sources whose published date starts with this")
    ap.add_argument("--place", help="only sources whose places facet contains this code")
    ap.add_argument("--recent", type=int, metavar="DAYS",
                    help="only sources ingested within the last N days")
    ap.add_argument("--csv", metavar="PATH", help="write the full list as CSV")
    ap.add_argument("--fm-only", action="store_true",
                    help="instead: sources registered in a frontmatter sources: list and written "
                         "into no body prose anywhere (invisible to the default count)")
    a = ap.parse_args()

    prose, aggregated, through, by_record = scan_raw()
    cited, in_body, fm_pages = scan_wiki()
    companions = {s for s in prose if s not in cited and s in by_record}
    cited = cited | companions
    uncited = {s: m for s, m in prose.items() if s not in cited}

    if a.fm_only:
        ghosts = {s: m for s, m in prose.items() if s not in in_body and s in fm_pages}
        print(f"registered in a frontmatter sources: list, written into no body prose anywhere: "
              f"{len(ghosts):,}")
        print("These read as CITED to the default count. Either the page owes them prose, or the "
              "registration is stale and belongs off its frontmatter." + chr(10))
        for s in sorted(ghosts, key=lambda x: ghosts[x]["published"] or ""):
            pages = fm_pages[s]
            print(f"  {ghosts[s]['published'] or '?':<11} {s[:70]}")
            print(f"              on: {', '.join(pages)}")
        return 0

    if a.year:
        uncited = {s: m for s, m in uncited.items() if m["published"].startswith(a.year)}
    if a.place:
        uncited = {s: m for s, m in uncited.items()
                   if re.search(rf"\b{re.escape(a.place)}\b", m["places"])}
    if a.recent:
        floor = (date.today() - timedelta(days=a.recent)).isoformat()
        uncited = {s: m for s, m in uncited.items() if m["ingested"] and m["ingested"] >= floor}

    total = len(prose)
    print(f"raw/ prose sources:       {total:,}   "
          f"(excluded: {aggregated:,} finance/budget records, aggregated not cited)")
    print(f"cited somewhere in wiki/: {total - len(prose.keys() - cited):,}")
    print(f"cited NOWHERE:            {len(uncited):,}"
          + (f"   [filtered]" if (a.year or a.place or a.recent) else ""))
    if companions:
        print(f"cited only by a record:   {len(companions):,}   "
              f"(budget-document companions; the line-item records link them "
              f"instead of repeating the citation — used as designed, not backlog)")
    if through:
        orphan_through = [s for s in through if s not in cited]
        print(f"\nretired by cite_through:  {len(through)}"
              f"   ({len(orphan_through)} of them also cited nowhere — check the survivor "
              f"carries the citation)")
        for s in orphan_through[:10]:
            print(f"   {s}")

    if uncited and not (a.list or a.csv):
        years = Counter((m["published"] or "?")[:4] for m in uncited.values())
        print("\nby publication year:")
        for y, n in sorted(years.items(), reverse=True):
            print(f"  {y}  {n:>4}")
        print("\nRe-run with --list to see them, or --recent 30 for the ones a "
              "recent run should have written.")

    if a.list:
        print()
        for s in sorted(uncited, key=lambda x: uncited[x]["published"] or "", reverse=True)[:a.limit]:
            m = uncited[s]
            print(f"  {m['published'] or '?':<11} {m['places'][:18]:<20} {s[:78]}")

    if a.csv:
        path = a.csv if os.path.isabs(a.csv) else os.path.join(ROOT, a.csv)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["slug", "published", "ingested", "places", "title"])
            for s in sorted(uncited):
                m = uncited[s]
                w.writerow([s, m["published"], m["ingested"], m["places"], m["title"]])
        print(f"\nwrote {len(uncited):,} rows -> {os.path.relpath(path, ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
