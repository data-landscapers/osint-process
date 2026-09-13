# for-OSINT — raw/ URL index: dedup without a corpus scan

*Design note from Cowork, 2026-08-19. For CC to implement. Reference implementation at the end.*

**Implemented 2026-08-19** (`scripts/raw-url-index.py`, `lookups/raw-url-index.csv`, 9,084 rows; all four migration steps done — `INGEST.md` steps 2 and 11, `SWEEP-DAILY-LIST.md` §3, LINT #27). Three departures from the reference implementation, each logged as a decision in `logs/log.md`: normalisation is `vault_lib.normalise_url()`, not a second implementation (INGEST step 2's contract); the lint counts **unique normalised URLs**, not files, because one budget or IATI document URL fans out across dozens of records; and `--rebuild` walks `raw/` directly, the network-drive premise having died with the machine swap — 10,115 files in 2.9s. Validated live: the Atlantic Council re-surface is caught as `DUP-SLUG`, zero same-host slug collisions exist across the 9,084 held sources (so the rule would never have mis-dropped one), and a `--check` of the 132 URLs now in `new/` runs in 0.26s and finds 5 exact duplicates plus 1 further path-insensitive one.

## Problem

Sweep dedup (`SWEEP-DAILY-LIST.md` §3, shared by the off-list sweep) checks candidates against `raw/` frontmatter by scanning the corpus. `raw/2026` now holds ~6,000 files (2.8GB) on a network drive, so the scan times out (9-minute grep, `ls` not returning in 240s — off-list run 2026-08-19), every sweep and ingest pass pays it, and the cost grows with the corpus forever. The Thunderbolt cable will cut the latency; it will not change the shape of the cost.

Separately, exact-URL matching missed a re-surface under a second canonical URL (Atlantic Council brief staged 2026-08-17 as `/blog-post/…`, returned 2026-08-19 as `/in-depth-research-reports/issue-brief/…` — caught by eye, same run note).

## Design

One derived CSV, proposed at `lookups/raw-url-index.csv` (CC's call if it belongs elsewhere — it is state like `seen.csv`, not a vocabulary). Columns: `url_normalized,slug_key,file,published`. One row per source in `raw/`. At the current corpus that is a ~500KB file read once per run, replacing thousands of per-file round-trips.

**Normalization** (applied identically at index time and lookup time): lowercase; strip scheme and leading `www.`; strip fragment; strip tracking query params (`utm_*`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, `ref`, `source`) but keep all others (some CMSs address articles by query); strip trailing slash. Deliberately conservative — a normalization that merges too eagerly drops real sources, which is worse than a duplicate ingest lint #7 catches anyway.

**Slug key** (the path-insensitive layer, for the Atlantic Council case): the final non-empty path segment, extension stripped, lowercased. Set empty — never matched — when the segment is numeric-only, shorter than 16 characters, or fewer than three hyphen-separated words: `index`, `2026`, `article` must not collide.

## Lookup rules (sweep side)

This replaces only the `raw/` leg of dedup. The `seen.csv` and current-`new/` checks are unchanged.

- **Exact `url_normalized` match** → drop, reason `duplicate-raw`, as today's rule (a).
- **Same host + same `slug_key`, different path** → confidently the same outlet's re-crawl, today's rule (b) → drop, reason `duplicate-raw-slug`, log the matched file as `kept_twin`.
- **Different host + same `slug_key`** → not a drop. Stage with a duplicate-event flag for ingest lint #7 — *same event, different outlet* survives, per the standing conservative rule.

## Maintenance

- **Ingest appends** one row per admission, after the file is written to `raw/` and before the candidate leaves `new/` — an interrupted run then at worst duplicates a row, which rebuild collapses, rather than losing one.
- **Retire/replace removes the row** in the same edit that retires the source. A stale row is the one dangerous state: it silently drops a live candidate against a source no longer held.
- **Rebuild** (`--rebuild`) regenerates the whole index from `raw/` frontmatter. Run once as backfill — on the machine that hosts the drive, or after the cable arrives — and thereafter only on suspicion. It is the only operation that still scans the corpus.
- **Lint check**: index row count equals `raw/` file count; a mismatch triggers rebuild, not investigation.

## Migration (CC's sequence, per division of labour)

1. Place `scripts/raw-url-index.py` (below), run `--rebuild` once, commit the index.
2. `INGEST.md`: append on admission, remove on retire/replace.
3. `SWEEP-DAILY-LIST.md` §3 and the off-list delta: replace the `raw/` scan with `--check`; also closes the 2026-08-19 run note's path-insensitive-dedup recommendation.
4. Add the lint count check.

## Reference implementation — `scripts/raw-url-index.py`

```python
#!/usr/bin/env python3
"""raw/ URL index: O(1) dedup lookup instead of a corpus scan.

Usage:
  raw-url-index.py --rebuild                          # regenerate from raw/ frontmatter
  raw-url-index.py --append URL FILE PUBLISHED        # one row, after admission to raw/
  raw-url-index.py --remove URL                       # on retire/replace
  raw-url-index.py --check URL [URL ...]              # per URL prints one line:
  #   DUP-EXACT <file> | DUP-SLUG <file> | FLAG-SLUG <file> | CLEAN
Exit code on --check: 0 all clean, 1 any DUP, 2 only FLAGs.
"""
import csv, re, sys
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl, urlencode

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "lookups" / "raw-url-index.csv"
RAW = ROOT / "raw"
FIELDS = ["url_normalized", "slug_key", "file", "published"]
TRACKING = re.compile(r"^(utm_|fbclid$|gclid$|mc_cid$|mc_eid$|ref$|source$)")

def normalize(url: str) -> str:
    s = urlsplit(url.strip())
    host = s.netloc.lower().removeprefix("www.")
    path = s.path.rstrip("/")
    q = [(k, v) for k, v in parse_qsl(s.query, keep_blank_values=True)
         if not TRACKING.match(k.lower())]
    query = ("?" + urlencode(q)) if q else ""
    return f"{host}{path}{query}".lower()

def slug_key(url_norm: str) -> str:
    path = url_norm.split("?")[0]
    seg = path.rsplit("/", 1)[-1] if "/" in path else ""
    seg = re.sub(r"\.[a-z0-9]{2,5}$", "", seg)
    if len(seg) < 16 or seg.replace("-", "").isdigit() or seg.count("-") < 2:
        return ""
    return seg

def host_of(url_norm: str) -> str:
    return url_norm.split("/", 1)[0]

def load():
    if not INDEX.exists():
        return []
    with open(INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save(rows):
    seen, out = set(), []
    for r in rows:
        if r["url_normalized"] not in seen:
            seen.add(r["url_normalized"])
            out.append(r)
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

def frontmatter(path: Path) -> dict:
    fm, inside = {}, False
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i > 100:
                break
            if line.strip() == "---":
                if inside:
                    break
                inside = True
                continue
            if inside and ":" in line:
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip("'\"")
    return fm

def cmd_rebuild():
    rows = []
    for p in sorted(RAW.rglob("*.md")):
        fm = frontmatter(p)
        url = fm.get("url", "")
        if not url:
            continue
        n = normalize(url)
        rows.append({"url_normalized": n, "slug_key": slug_key(n),
                     "file": str(p.relative_to(ROOT)).replace("\\", "/"),
                     "published": fm.get("published", "")})
    save(rows)
    print(f"rebuilt: {len(rows)} rows")

def cmd_append(url, file, published):
    rows = load()
    n = normalize(url)
    rows.append({"url_normalized": n, "slug_key": slug_key(n),
                 "file": file, "published": published})
    save(rows)

def cmd_remove(url):
    n = normalize(url)
    rows = [r for r in load() if r["url_normalized"] != n]
    save(rows)

def cmd_check(urls):
    rows = load()
    by_url = {r["url_normalized"]: r for r in rows}
    by_slug = {}
    for r in rows:
        if r["slug_key"]:
            by_slug.setdefault(r["slug_key"], []).append(r)
    worst = 0
    for url in urls:
        n = normalize(url)
        if n in by_url:
            print(f"DUP-EXACT {by_url[n]['file']}")
            worst = max(worst, 2)
            continue
        k, h, hit = slug_key(n), host_of(n), None
        for r in by_slug.get(k, []) if k else []:
            same_host = host_of(r["url_normalized"]) == h
            if same_host:
                hit = ("DUP-SLUG", r)
                break
            hit = hit or ("FLAG-SLUG", r)
        if hit:
            print(f"{hit[0]} {hit[1]['file']}")
            worst = max(worst, 2 if hit[0] == "DUP-SLUG" else 1)
        else:
            print("CLEAN")
    sys.exit({0: 0, 1: 2, 2: 1}[worst])

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--rebuild"]:
        cmd_rebuild()
    elif a[:1] == ["--append"] and len(a) == 4:
        cmd_append(a[1], a[2], a[3])
    elif a[:1] == ["--remove"] and len(a) == 2:
        cmd_remove(a[1])
    elif a[:1] == ["--check"] and len(a) >= 2:
        cmd_check(a[1:])
    else:
        sys.exit(__doc__)
```
