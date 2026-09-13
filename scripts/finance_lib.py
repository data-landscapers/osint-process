#!/usr/bin/env python3
"""finance_lib.py — the finance and budget domain layer.

Two libraries, and the split is deliberate:

- **`vault_lib`** is the **read layer** — one frontmatter parser, one URL
  normalisation, the rebuildable `index/`. Anything that needs to know *what the
  vault holds* goes there.
- **`finance_lib`** (this file) is the **finance domain** — the record parsers the
  finance pages and lints were already sharing, plus the lookup tables the passes
  read: FX rates, canonical financier names, place codes. Anything that knows what
  a *deal record* or a *budget line* is goes here.

It deliberately keeps its own light frontmatter helpers rather than importing
`vault_lib`'s: they answer a different question. `fm_get` reads one key out of a
record whose shape the caller already knows, in a hot loop over 8,000 files;
`vault_lib.parse_frontmatter` builds a complete typed object with warnings. Both
are right for their job, and collapsing them would make the cheap one expensive.

Grown 2026-08-03 (review task 25) from four helpers to the shared layer the
per-country scripts draw on — the FX and financier-name loaders came out of
`build-finance-page.py`, which now imports them rather than defining them.
"""
import csv
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _abs(path):
    """Resolve against the repo root, so a script works from any directory."""
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


# --------------------------------------------------------------------------- #
# Reading records
# --------------------------------------------------------------------------- #

def raw_sources(raw="raw", ext=".md"):
    """(filename, path) for every source in `raw/`, which is sharded `raw/YYYY/`.

    Yields the bare filename as well as the path because callers key on the
    filename — it is the source's slug and carries its date prefix — while the
    path is now a year deeper (housekeeping 18, 2026-08-03). Sorted by filename,
    so iteration order is chronological across the whole corpus exactly as it was
    when `raw/` was flat, not year-by-year.
    """
    base = _abs(raw)
    out = []
    for year in os.listdir(base):
        d = os.path.join(base, year)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if ext and not fn.endswith(ext):
                continue
            out.append((fn, os.path.join(d, fn)))
    out.sort()
    return out


def split_front(text):
    """(frontmatter, body) from a '--- ... ---' markdown file, else (None, None)."""
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)


def fm_get(fm, key, default=""):
    # [ \t]* not \s* — \s eats the newline and spills a blank field onto the next line
    m = re.search(r'^%s:[ \t]*"?([^\n]*?)"?[ \t]*$' % re.escape(key), fm, re.M)
    return m.group(1).strip() if m else default


def section(body, name):
    """Text of a '## name' section, up to the next '## ' or end."""
    m = re.search(r'(?m)^##\s+%s\s*\n(.*?)(?=^##\s|\Z)' % re.escape(name), body, re.S)
    return m.group(1).strip() if m else ""


def deal_table(body):
    """Parse a '| Field | Value |' table into a dict."""
    d = {}
    for k, v in re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$', body, re.M):
        if k.strip() and k.strip() != "Field":
            d[k.strip()] = v.strip()
    return d


# --------------------------------------------------------------------------- #
# CSV, with the house conventions in one place
# --------------------------------------------------------------------------- #

def read_csv(path):
    """[dict] — utf-8-sig, because half the lookup tables were saved with a BOM."""
    with open(_abs(path), encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path, rows, fields=None):
    """Write [dict] with LF endings — the vault is mixed CRLF/LF and a rewritten
    export should not show up as a whole-file diff because the tool changed."""
    fields = fields or (list(rows[0]) if rows else [])
    p = _abs(path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    return p


# --------------------------------------------------------------------------- #
# Places — lookups/countries.csv (§1's PLACE vocabulary)
# --------------------------------------------------------------------------- #

_PLACES = None


def places(path="lookups/countries.csv"):
    """{code: (name, parent)} for all 62 codes — 54 countries and 8 X__ regions."""
    global _PLACES
    if _PLACES is None:
        _PLACES = {}
        for row in read_csv(path):
            code = (row.get("iso-3") or "").strip()
            if code:
                _PLACES[code] = ((row.get("country-name") or "").strip(),
                                 (row.get("Region") or "").strip())
    return _PLACES


def place_name(code):
    return places().get((code or "").strip(), ("", ""))[0]


def is_region(code):
    """§1: a region is a first-class place, not a container — it just starts X."""
    return (code or "").startswith("X")


def parents(code):
    """The chain up §1's single-parent tree: KEN -> XEA -> XAF -> XGL."""
    out, seen = [], set()
    cur = places().get((code or "").strip(), ("", ""))[1]
    while cur and cur not in seen:
        out.append(cur)
        seen.add(cur)
        cur = places().get(cur, ("", ""))[1]
    return out


# --------------------------------------------------------------------------- #
# Money — FX and canonical financier names
# --------------------------------------------------------------------------- #

def load_fx(path="lookups/fx-imf-annual.csv"):
    """{(currency, year): units per USD} — IMF/WB annual averages."""
    fx = {}
    if os.path.exists(_abs(path)):
        for row in read_csv(path):
            try:
                fx[(row["currency"], row["year"])] = float(row["per_usd"])
            except (KeyError, ValueError, TypeError):
                pass
    return fx


def fx_rate(fx, cur, yr):
    """Exact (currency, year) rate, else the nearest year held for that currency.

    `CLAUDE.md` → *Currency*: money is carried in the announcing party's own
    currency and a USD figure is a **dated conversion**. This returns the rate;
    dating the conversion on the page is the caller's job, and spot-converting a
    fiscal-year figure is forbidden by the domestic-state driver.
    """
    if (cur, yr) in fx:
        return fx[(cur, yr)]
    years = [int(y) for (c, y) in fx if c == cur and y.isdigit()]
    if not years or not str(yr).isdigit():
        return None
    return fx[(cur, str(min(years, key=lambda y: abs(y - int(yr)))))]


_FINNAME = None


def load_financier_names(path="lookups/financier-names.csv"):
    """{financier_slug: canonical display name} — the approved map (lint #16,
    REPORT-LINT check D)."""
    global _FINNAME
    if _FINNAME is None:
        _FINNAME = {}
        if os.path.isfile(_abs(path)):
            for row in read_csv(path):
                if row.get("financier_slug"):
                    _FINNAME[row["financier_slug"].strip()] = \
                        (row.get("canonical_name") or "").strip()
    return _FINNAME


def fin_name(slug):
    """Canonical display name for a financier slug.

    The approved map first; then the entity page's own title; then a prettified
    slug. A slug that reaches the third fallback is a missing row in
    `financier-names.csv`, which REPORT-LINT check D is what catches.
    """
    slug = (slug or "").strip()
    if not slug:
        return ""
    names = load_financier_names()
    if slug in names:
        return names[slug]
    p = os.path.join(ROOT, "wiki", "entities", slug + ".md")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as r:
            for line in r:
                if line.startswith("title:"):
                    return line.split(":", 1)[1].strip().strip('"')
    small = {"of", "and", "the", "de", "du", "des", "for"}
    return " ".join(w if (w in small and i) else w.capitalize()
                    for i, w in enumerate(slug.split("-")))
