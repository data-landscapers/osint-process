#!/usr/bin/env python3
"""raw-url-index.py — the `raw/` URL index: dedup by lookup, not by corpus scan.

`lookups/raw-url-index.csv`, one row per source in `raw/` carrying a `url:`.
Columns: `url_normalized,slug_key,file,published`. Read once per run in place of a
per-candidate `grep -rF` over `raw/` (10.8s each, cold, at 10k files).

**Normalisation is `vault_lib.normalise_url()`** — INGEST.md step 2's contract, the
same function `sweep-url_log.md` and the sweeps' pre-fetch filter use. Never
re-implemented here, or the gates disagree.

`slug_key` is the path-insensitive layer: the final path segment, extension stripped,
percent-decoded, diacritic-folded, lower-cased — **empty, and never matched**, where that
segment is numeric-only, under 16 characters, or fewer than three hyphen-separated words. It catches the same outlet
re-publishing one item under a second canonical path (Atlantic Council, 2026-08-19:
`/blog-post/...` staged 08-17, `/in-depth-research-reports/issue-brief/...` back 08-19).

Usage:
  raw-url-index.py --rebuild                       # regenerate from raw/ frontmatter (~2s)
  raw-url-index.py --append URL FILE [PUBLISHED]   # one row, at INGEST.md step 11
  raw-url-index.py --remove URL [URL ...]          # on retire/replace — a stale row
                                                   #   silently drops a live candidate
  raw-url-index.py --reject REASON URL [URL ...]   # a permanent negative adjudication
  raw-url-index.py --check URL [URL ...]           # or `--check -` to read URLs on stdin
  raw-url-index.py --lint                          # row count vs raw/ — mismatch: rebuild

`--check` prints one tab-separated line per URL, in order:
  DUP-EXACT <url> <file>   same normalised URL held        -> drop, `duplicate-raw`
  DUP-SLUG  <url> <file>   same host, same slug, new path  -> drop, `duplicate-raw-slug`,
                                                              log the file as `kept_twin`
  FLAG-SLUG <url> <file>   different host, same slug       -> NOT a drop: stage it with a
                                                              duplicate-event flag, ingest
                                                              lint #7 adjudicates on text
  REJECTED  <url> <reason> <decided>  permanently out  -> drop, never fetch, never read
  CLEAN     <url>
Exit: 0 all clean, 1 any DUP or REJECTED, 2 only FLAGs.

**`lookups/rejected-urls.csv` is a second, non-derived store, and deliberately not a column
here.** This index is a pure derivation of `raw/` — `--rebuild` regenerates it from frontmatter
and would wipe any state a deleted record left behind, which is the whole failure a negative
adjudication has to survive. A URL rejected on the remit or scope bar has no file in `raw/` by
construction, so its record must outlive the positive one: it lives in its own file, is never
rebuilt, and is read by `--check` alongside the index. `logs/drop-list.csv` is the same idea at
domain level; `logs/sweep-url_log.md` reaches back only one rotation, which is why neither of
those closes it. (INGEST.md step 1, the place bar; step 2 tier 1 reads the verdict.)

**Not every pass may gate on `--check`.** One document URL legitimately fans out across
many records — one budget PDF covers dozens of appropriation records — so those report
`DUP-EXACT` by design and by `INGEST.md` step 2's own carve-out. A pass whose dedup key
is a `deal_id`, not a URL (the budget route), must not use this gate.

**d-portal was not one of those, and no longer reports as one.** An IATI activity is
addressed *by* its fragment, so every activity a publisher has filed used to normalise to
`d-portal.org/ctrack.html` and the second onward read `DUP-EXACT` against an unrelated
activity. `vault_lib.FRAGMENT_IS_IDENTITY` now keeps the fragment on those two hosts, so
each activity holds its own row. `slug_key` still reads the path only — the fragment names
the document but is not a slug, and keying on it would make one activity id on two host
spellings a `FLAG-SLUG` for nothing.
"""
import csv
import datetime
import os
import sys
import unicodedata
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V

# The index holds URLs percent-encoding Arabic and French; the Windows console is cp1252,
# so printing a row back raised UnicodeEncodeError *after* the CSV write had committed —
# a success that reads as a failure, and invites a caller to append the row twice.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

INDEX = os.path.join(V.ROOT, "lookups", "raw-url-index.csv")
REJECTED = os.path.join(V.ROOT, "lookups", "rejected-urls.csv")
REJECT_FIELDS = ["url_normalized", "reason", "decided"]
RAW = os.path.join(V.ROOT, "raw")
FIELDS = ["url_normalized", "slug_key", "file", "published"]
MIN_SLUG_LEN = 16
MIN_SLUG_WORDS = 3


def _today():
    return datetime.date.today().isoformat()


def _fold(seg):
    """Percent-decode, then strip diacritics — so one slug written two ways is one key.

    An outlet that serves `communiqu%C3%A9-...` and `communique-...` for one article
    is publishing one document, and a key that keeps the escape can never match the
    plain form. 213 of the index's keys carry a `%XX` escape; folding them creates
    **zero** new same-host collisions across the held corpus, so the widening costs
    nothing and closes the miss going forward.

    It does not fold a hyphen against a letter. ANGOP writes a diacritic as a hyphen
    in some of its slugs (`refor-a` for `reforça`), but 35 of its 106 slugs carry a
    lone-letter segment and nearly all of them are the Portuguese words *e* and *a* —
    a fold that reached that far would collide unrelated articles, and tier 1 drops
    without reading the body.
    """
    seg = urllib.parse.unquote(seg)
    seg = unicodedata.normalize("NFKD", seg)
    return "".join(c for c in seg if not unicodedata.combining(c)).lower()


def slug_key(url_norm):
    """The final path segment, extension stripped, folded, lower-cased — "" if too weak.

    `index`, `2026`, `article`, `12345` must never collide, so a segment that is
    numeric-only, short, or fewer than three hyphenated words keys nothing at all.
    """
    path = url_norm.split("#", 1)[0].split("?", 1)[0].rstrip("/")
    if "/" not in path:
        return ""
    seg = _fold(path.rsplit("/", 1)[-1])
    if "." in seg:
        stem, _, ext = seg.rpartition(".")
        if stem and 2 <= len(ext) <= 5 and ext.isalnum():
            seg = stem
    if (len(seg) < MIN_SLUG_LEN or seg.replace("-", "").isdigit()
            or seg.count("-") < MIN_SLUG_WORDS - 1):
        return ""
    return seg


def host_of(url_norm):
    return url_norm.split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]


def row_for(url, file, published):
    n = V.normalise_url(url)
    return {"url_normalized": n, "slug_key": slug_key(n),
            "file": file.replace("\\", "/"), "published": published or ""}


def load():
    if not os.path.exists(INDEX):
        return []
    with open(INDEX, newline="", encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("url_normalized")]


def save(rows):
    """Written whole, first row per URL winning. Only --rebuild/--remove call this;
    --append appends, so an interrupted run at worst duplicates a row."""
    seen, out = set(), []
    for r in rows:
        if r["url_normalized"] not in seen:
            seen.add(r["url_normalized"])
            out.append({k: r.get(k, "") for k in FIELDS})
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    return len(out)


def raw_sources():
    """(relpath, url, published) for every `raw/` .md carrying a `url:`.

    Reads the frontmatter head only — the whole of `raw/` in ~2s on a local disk.
    """
    for dirpath, dirnames, filenames in os.walk(RAW):
        dirnames.sort()
        for name in sorted(filenames):
            if not name.lower().endswith(".md"):
                continue
            p = os.path.join(dirpath, name)
            with open(p, encoding="utf-8", errors="replace") as f:
                head = f.read(4096)
            if "url:" not in head:
                continue
            fm, _w, _b = V.parse_frontmatter(head)
            url = fm.get("url")
            if not isinstance(url, str) or not url.strip():
                continue
            rel = os.path.relpath(p, V.ROOT).replace("\\", "/")
            yield rel, url, str(fm.get("published") or "")


def cmd_rebuild():
    rows = [row_for(url, rel, pub) for rel, url, pub in raw_sources()]
    n = save(rows)
    print(f"rebuilt: {n} rows ({len(rows) - n} duplicate URLs collapsed)")


def cmd_append(url, file, published):
    r = row_for(url, file, published)
    if not r["url_normalized"]:
        sys.exit("refusing to index an empty URL")
    new = not os.path.exists(INDEX)
    with open(INDEX, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(r)
    print("\t".join(r[k] for k in FIELDS))


def cmd_remove(urls):
    targets = {V.normalise_url(u) for u in urls}
    rows = load()
    kept = [r for r in rows if r["url_normalized"] not in targets]
    n = len(rows) - len(kept)
    print(f"removed: {n} row(s)")
    if not n:
        # A stale row is the one dangerous state — it silently drops a live candidate
        # against a source no longer held. A retire that matched nothing is loud.
        sys.exit("no row matched — pass the retired source's own `url:` verbatim")
    save(kept)


def load_rejected():
    """The permanent negatives. Absent file is the normal empty state, never an error."""
    if not os.path.exists(REJECTED):
        return {}
    with open(REJECTED, newline="", encoding="utf-8") as f:
        return {r["url_normalized"]: r for r in csv.DictReader(f)
                if r.get("url_normalized")}


def cmd_reject(reason, urls):
    """Append a permanent negative. Never rebuilt, so it outlives the record it replaces."""
    if not reason or reason.startswith("-"):
        sys.exit("--reject takes a REASON first, then one or more URLs")
    have = load_rejected()
    new = not os.path.exists(REJECTED)
    added = 0
    with open(REJECTED, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REJECT_FIELDS)
        if new:
            w.writeheader()
        for u in urls:
            n = V.normalise_url(u)
            if not n or n in have:
                continue
            w.writerow({"url_normalized": n, "reason": reason,
                        "decided": _today()})
            have[n] = 1
            added += 1
    print(f"rejected: {added} new row(s), {len(urls) - added} already held")


def cmd_check(urls):
    rows = load()
    rejected = load_rejected()
    by_url, by_slug = {}, {}
    for r in rows:
        by_url.setdefault(r["url_normalized"], r)
        if r["slug_key"]:
            by_slug.setdefault(r["slug_key"], []).append(r)
    worst = 0
    for url in urls:
        n = V.normalise_url(url)
        if n in rejected:
            r = rejected[n]
            print(f"REJECTED	{url}	{r.get('reason','')}	{r.get('decided','')}")
            worst = max(worst, 2)
            continue
        if n in by_url:
            print(f"DUP-EXACT\t{url}\t{by_url[n]['file']}")
            worst = max(worst, 2)
            continue
        k, h, hit = slug_key(n), host_of(n), None
        for r in by_slug.get(k, []) if k else []:
            if host_of(r["url_normalized"]) == h:
                hit = ("DUP-SLUG", r)
                break
            hit = hit or ("FLAG-SLUG", r)
        if hit:
            print(f"{hit[0]}\t{url}\t{hit[1]['file']}")
            worst = max(worst, 2 if hit[0] == "DUP-SLUG" else 1)
        else:
            print(f"CLEAN\t{url}")
    sys.exit({0: 0, 1: 2, 2: 1}[worst])


def cmd_lint():
    """Count, not content: a mismatch triggers --rebuild, never an investigation.

    Counted in **unique normalised URLs**, never in files: one budget or IATI document
    URL fans out across dozens of records (INGEST.md step 2's own carve-out), so 9,084
    URLs across 10,080 files is the healthy state, not a defect.
    """
    held = {V.normalise_url(url) for _rel, url, _pub in raw_sources()}
    rows = load()
    urls = {r["url_normalized"] for r in rows}
    if len(rows) == len(urls) == len(held):
        print(f"raw-url-index: OK — {len(held)} URLs, {len(rows)} rows")
        return
    missing, stale = len(held - urls), len(urls - held)
    print(f"raw-url-index: MISMATCH — raw/ holds {len(held)} unique URLs, index has "
          f"{len(rows)} rows ({len(urls)} unique; {missing} unindexed, {stale} stale). "
          f"Run: python scripts/raw-url-index.py --rebuild")
    sys.exit(1)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--rebuild"] and len(a) == 1:
        cmd_rebuild()
    elif a[:1] == ["--append"] and len(a) in (3, 4):
        cmd_append(a[1], a[2], a[3] if len(a) == 4 else "")
    elif a[:1] == ["--remove"] and len(a) >= 2:
        cmd_remove(a[1:])
    elif a[:1] == ["--reject"] and len(a) >= 3:
        cmd_reject(a[1], a[2:])
    elif a[:1] == ["--check"] and len(a) >= 2:
        cmd_check([ln.strip() for ln in sys.stdin if ln.strip()]
                  if a[1:] == ["-"] else a[1:])
    elif a[:1] == ["--lint"] and len(a) == 1:
        cmd_lint()
    else:
        sys.exit(__doc__)
