"""Unit test of scripts/lint-scope.py — the three-way sort, on rows rather than the vault.

The sort is three rules and each one has already been got wrong in prose. **`geopol.*`
admits regardless of place**, which is what carries a great-power positioning story with
no African country in it. **`XGL` alone is a bucket, not an admission** — the whole point
of note 30 was that the code had been doing duty as "not about Africa", so it must not
fall into `in`. And **`unaccounted` is everything else**, including the empty `places:`
that let 26 records through a screen with no geographic clause.

`--since` reads `ingested` and falls back to `published`, because the finance and
hand-clip records carry no `ingested` and would otherwise vanish from every dated run.

Run: python scripts/tests/test-lint-scope.py
"""
import importlib.util
import os
import pathlib
import sys

REPO = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRIPT = os.path.join(REPO, "scripts", "lint-scope.py")

spec = importlib.util.spec_from_file_location("lint_scope", SCRIPT)
LS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(LS)


def row(path, places, topics=(), ingested=None, published=None, kind="source"):
    fm = {"type": kind, "places": list(places), "topics": list(topics), "title": path}
    if ingested:
        fm["ingested"] = ingested
    if published:
        fm["published"] = published
    return {"path": path, "fm": fm, "d": {}}


ROWS = [
    row("raw/2026/ken.md", ["KEN"], ["gov.policy"], ingested="2026-08-21"),
    row("raw/2026/region.md", ["XWA"], [], ingested="2026-08-21"),
    row("raw/2026/geopol-no-place.md", [], ["geopol.china"], ingested="2026-08-21"),
    row("raw/2026/geopol-xgl.md", ["XGL"], ["geopol.eu"], ingested="2026-08-21"),
    row("raw/2026/xgl-only.md", ["XGL"], ["tech.ai"], ingested="2026-08-21"),
    row("raw/2026/no-place.md", [], ["tech.ai"], ingested="2026-08-21"),
    row("raw/2026/old-xgl.md", ["XGL"], [], ingested="2026-07-01"),
    row("raw/2026/pubdate-only.md", [], [], published="2026-08-21"),
    row("wiki/places/KEN.md", [], [], ingested="2026-08-21", kind="place"),
    row("new/staged.md", [], [], ingested="2026-08-21"),
]

LS.V.load_index = lambda *a, **k: ROWS


def names(rows):
    return sorted(r[1] for r in rows)


def check(label, got, want):
    assert got == want, f"{label}: {got!r} != {want!r}"
    print(f"  {label}  OK")


inr, xgl, un = LS.sort_sources()
# `wiki/` is not a source and `new/` is not in `raw/` — neither is this check's business.
check("in", names(inr), ["raw/2026/geopol-no-place.md", "raw/2026/geopol-xgl.md",
                         "raw/2026/ken.md", "raw/2026/region.md"])
check("xgl", names(xgl), ["raw/2026/old-xgl.md", "raw/2026/xgl-only.md"])
check("unaccounted", names(un), ["raw/2026/no-place.md", "raw/2026/pubdate-only.md"])

inr, xgl, un = LS.sort_sources(since="2026-08-20")
check("--since drops the July XGL row", names(xgl), ["raw/2026/xgl-only.md"])
check("--since keeps a published-only row", names(un),
      ["raw/2026/no-place.md", "raw/2026/pubdate-only.md"])

inr, xgl, un = LS.sort_sources(since="2026-09-01")
check("--since ahead of everything is empty", (len(inr), len(xgl), len(un)), (0, 0, 0))

print("ok - lint-scope - all assertions passed")
