"""Unit test of scripts/raw-url-index.py's two decisions: what keys, and what matches.

A dedup gate that goes wrong drops a live source silently, so the `slug_key` guards —
too short, numeric, too few words — are asserted rather than trusted, and the three
verdicts are checked against a fixture index carrying the case that motivated the index
(Atlantic Council, 2026-08-19: one brief, two canonical paths, exact-URL dedup blind).

Run: python scripts/tests/test-raw-url-index.py
"""
import contextlib
import importlib.util
import io
import os
import pathlib
import sys
import tempfile

REPO = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRIPT = os.path.join(REPO, "scripts", "raw-url-index.py")
spec = importlib.util.spec_from_file_location("rui", SCRIPT)
rui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rui)

root = tempfile.mkdtemp(prefix="ruitest-")
os.makedirs(os.path.join(root, "lookups"))
rui.INDEX = os.path.join(root, "lookups", "raw-url-index.csv")
rui.RAW = os.path.join(root, "raw")

fails = []


def eq(got, want, what):
    if got != want:
        fails.append(f"{what}: got {got!r}, want {want!r}")


def call(fn, *args):
    """Run a cmd_*, returning (stdout, exit code) — they print and sys.exit."""
    out, code = io.StringIO(), 0
    try:
        with contextlib.redirect_stdout(out):
            fn(*args)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    return out.getvalue(), code


# --- slug_key: what keys, and what deliberately does not ---------------------

def key(u):
    return rui.slug_key(rui.V.normalise_url(u))


AC_HELD = ("https://www.atlanticcouncil.org/blog-post/sovereignty-without-borders-"
           "decoding-the-transatlantic-digital-relationship-at-a-time-of-change/")
AC_SLUG = ("sovereignty-without-borders-decoding-the-transatlantic-digital-"
           "relationship-at-a-time-of-change")

eq(key(AC_HELD), AC_SLUG, "a real slug keys")
eq(key("https://example.com/news/a-long-enough-story-slug.html"),
   "a-long-enough-story-slug", "extension stripped")
eq(key("https://example.com/news/a-long-enough-story-slug?page=2"),
   "a-long-enough-story-slug", "query ignored")
eq(key("https://EXAMPLE.com/News/A-Long-Enough-Story-Slug"),
   "a-long-enough-story-slug", "path case folded into the key")
eq(key("https://gov.za/news/media-statements/communiqu%C3%A9-2nd-session-joint-commission"),
   key("https://gov.za/news/media-statements/communique-2nd-session-joint-commission"),
   "percent-encoded and plain forms of one slug fold to one key")
eq(key("https://gov.za/news/media-statements/communiqu\u00e9-2nd-session-joint-commission"),
   key("https://gov.za/news/media-statements/communique-2nd-session-joint-commission"),
   "a literal diacritic folds to the same key as its plain form")
ANGOP_HYPHEN = "https://angop.ao/noticias/economia/governo-refor-a-soberania-digital-com-data"
ANGOP_PLAIN = "https://angop.ao/noticias/economia/governo-reforca-soberania-digital-com-data"
if key(ANGOP_HYPHEN) == key(ANGOP_PLAIN):
    fails.append("a hyphen must never fold against a letter - ANGOP's -e- and -a- are words")

for weak, why in [("https://example.com/news/index", "'index' is too short"),
                  ("https://example.com/2026/08/19", "numeric-only segment"),
                  ("https://example.com/tag/data-governance", "under 16 characters"),
                  ("https://example.com/news/digital-sovereignty", "fewer than three words"),
                  ("https://example.com", "no path at all")]:
    eq(key(weak), "", f"{why} keys nothing")

# --- the three verdicts, against a fixture index -----------------------------
HELD_FILE = "raw/2026/2026-08-17-atlantic-council-transatlantic-digital-sovereignty.md"
call(rui.cmd_append, AC_HELD, HELD_FILE, "2026-08-17")

cases = [
    # the same brief back under a second canonical path — same host, same slug
    ("https://www.atlanticcouncil.org/in-depth-research-reports/issue-brief/"
     + AC_SLUG + "/", "DUP-SLUG", 1),
    # the held URL itself, scheme, www., tracking param and fragment all differing
    ("http://atlanticcouncil.org/blog-post/" + AC_SLUG + "?utm_source=x#top",
     "DUP-EXACT", 1),
    # another outlet on the same slug — one story, two outlets: never a drop
    ("https://example.org/2026/08/17/" + AC_SLUG + "/", "FLAG-SLUG", 2),
    ("https://example.org/2026/08/19/a-story-the-base-has-never-held-before/",
     "CLEAN", 0),
]
for url, want, want_exit in cases:
    out, code = call(rui.cmd_check, [url])
    eq(out.split("\t")[0].strip(), want, f"verdict for a {want} candidate")
    eq(code, want_exit, f"exit code for {want}")
    if want != "CLEAN":
        eq(out.rstrip("\n").split("\t")[-1], HELD_FILE, f"{want} names the held file")

# a run of many URLs reports the worst, one line each, in order
out, code = call(rui.cmd_check, [c[0] for c in cases])
eq([ln.split("\t")[0] for ln in out.strip().split("\n")],
   [c[1] for c in cases], "one line per URL, in order")
eq(code, 1, "a mixed run exits 1 — a DUP outranks a FLAG")

# --- the stale row, which is the dangerous state -----------------------------
eq(call(rui.cmd_remove, [AC_HELD])[1], 0, "--remove of a held URL succeeds")
eq(call(rui.cmd_check, [cases[0][0]])[0].split("\t")[0], "CLEAN",
   "a removed row stops matching")
eq(call(rui.cmd_remove, ["https://example.org/nothing-here-at-all-really/"])[1], 1,
   "--remove matching nothing is loud, never silent")

print("FAIL: " + "; ".join(fails) if fails else f"ok — {root} — all assertions passed")
sys.exit(1 if fails else 0)
