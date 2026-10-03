"""Unit test of scripts/compile-hubs.py, over a fabricated raw/ and one hub.

Every rule tested here was once broken silently: CRLF-headed sources dropped from every
hub, a folded `hub_line` truncated to its first line, `[[a], [b]]` read as `a]` and `[b`,
year-precision sources dropped as undated, a retired capture re-cited on every run, and a
compile that rewrote an unchanged block every time. None of them raised.

Run: python scripts/tests/test-compile-hubs.py
"""
import importlib.util
import os
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
spec = importlib.util.spec_from_file_location("compile_hubs", REPO / "scripts" / "compile-hubs.py")
CH = importlib.util.module_from_spec(spec)
spec.loader.exec_module(CH)

# --- frontmatter readers -------------------------------------------------------------
assert CH.fm_of("---\r\ntitle: t\r\n---\r\nbody")[0] == "title: t", "CRLF frontmatter is read"
fm = "title: t\nhub_line: >\n  first half\n  second half\nplaces: [[KEN], [UGA]]\n"
assert CH.scalar(fm, "hub_line") == "first half second half", "a folded scalar is read whole"
assert CH.listval(fm, "places") == ["KEN", "UGA"], "the bracketed-item list form"
assert CH.listval("places: [KEN, UGA]", "places") == ["KEN", "UGA"], "the bare list form"
assert CH.places_of("place: KEN") == ["KEN"], "a singular place key is read"

# --- collect over a fabricated raw/ ---------------------------------------------------
tmp = tempfile.mkdtemp()
os.makedirs(os.path.join(tmp, "raw", "2026"))
os.makedirs(os.path.join(tmp, "wiki", "places"))


def src(name, body, eol="\n"):
    text = "---\n" + body + "---\nbody\n"
    open(os.path.join(tmp, "raw", "2026", name), "wb").write(text.replace("\n", eol).encode())


src("2026-09-01-a.md", "published: 2026-09-01\nplaces: [KEN]\nhub_line: \"Law passed\"\n")
src("2026-09-02-b.md", "published: 2026-09-02\nplaces: [KEN]\nhub_line: \"CRLF source\"\n", eol="\r\n")
src("2026-01-01-c.md", "published: 2026  # year only\nplaces: [KEN]\nhub_line: \"Year report\"\n")
src("2026-09-03-d.md", "published: 2026-09-03\nplaces: [KEN]\nhub_line: \"Held\"\norigin_status: hold\n")
src("2026-09-04-e.md", "published: 2026-09-04\nplaces: [KEN]\nhub_line: \"Retired\"\ncite_through: 2026-09-01-a\n")
src("2026-09-05-f.md", "published: unknown\nplaces: [KEN]\nhub_line: \"Undated\"\n")
src("2026-09-06-g.md", "published: 2026-09-06\nplaces: [KEN]\n")

cwd = os.getcwd()
os.chdir(tmp)
CH.RAW = os.path.join(tmp, "raw")            # finance_lib resolves a relative path against the repo
CH.PLACES = os.path.join(tmp, "wiki", "places")
try:
    by_place, skipped, held, retired = CH.collect()
    lines = [r[2] for r in by_place["KEN"]]
    assert sorted(lines) == ["CRLF source", "Law passed", "Year report"], lines
    assert (skipped, held, retired) == (1, 1, 1), (skipped, held, retired)
    year = [r for r in by_place["KEN"] if r[2] == "Year report"][0]
    assert year[0] == "2026-01-01" and year[4] == "2026", "a year date sorts padded and shows as given"

    out = CH.render(by_place["KEN"], "\n").split("\n")
    assert out[0].startswith("- **2026-09-02**"), "newest first"
    assert out[-1].startswith("- **2026**"), "the padded year sorts last"

    # --- compile_place: writes between the markers, keeps EOL, idempotent ----------------
    hub = os.path.join("wiki", "places", "KEN.md")
    open(hub, "wb").write(("# Kenya\r\n\r\n## Recent developments\r\n\r\n" + CH.OPEN_M + "\r\n- stale\r\n"
                           + CH.CLOSE_M + "\r\n\r\nLegacy text\r\n").encode())
    assert CH.compile_place("KEN", by_place["KEN"], write=True) == "rewritten"
    text = open(hub, "rb").read().decode()
    assert "- stale" not in text and "Law passed" in text and "Legacy text" in text
    assert text.count("\r\n") == text.count("\n"), "a CRLF hub stays CRLF"
    assert CH.compile_place("KEN", by_place["KEN"], write=True) == "unchanged", "a second run is a no-op"
    assert CH.compile_place("UGA", [], write=False) == "no-hub"
finally:
    os.chdir(cwd)

print("test-compile-hubs: all assertions pass")
