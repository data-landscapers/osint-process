"""Unit tests of the guards other passes lean on without reading: the containment patch
check, the URL-log appender's admission gate, the log-entry composer, the ingest lane
whitelist, the page-length growth gate, lint #15's inspection stamp, and the budget
companion promoter's no-duplicate rule.

Each guard exists because the failure it stops was silent the first time. A guard nobody
tests is one refactor away from passing everything, which reads exactly like a clean run.

Run: python scripts/tests/test-guards.py
"""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))
FAILS = []


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(label, cond):
    print(("ok    " if cond else "FAIL  ") + label)
    if not cond:
        FAILS.append(label)


# --- assert-containment.py --patch ------------------------------------------------- #
AC = load("assert_containment", "assert-containment.py")


def patch_verdict(*paths):
    with tempfile.TemporaryDirectory() as d:
        body = "".join(f"diff --git a/{a} b/{b}\n" for a, b in paths)
        open(os.path.join(d, "0001-x.patch"), "w", encoding="utf-8").write(body)
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            return AC.check_patch(d)


check("patch: scripts/ and lookups/ pass", patch_verdict(("scripts/a.py", "scripts/a.py"), ("lookups/x.csv", "lookups/x.csv")) == 0)
check("patch: an index page passes", patch_verdict(("wiki/places-index.md", "wiki/places-index.md")) == 0)
check("patch: raw/ is refused", patch_verdict(("raw/2026/x.md", "raw/2026/x.md")) == 1)
check("patch: a rename out of raw/ is refused on its source", patch_verdict(("raw/2026/x.md", "scripts/x.md")) == 1)
check("patch: a process file is refused", patch_verdict(("CLAUDE.md", "CLAUDE.md")) == 1)
check("patch: scripts/../raw is refused", patch_verdict(("scripts/../raw/x.md", "scripts/../raw/x.md")) == 1)
check("patch: a wiki page is refused", patch_verdict(("wiki/concepts/tech.ai.md", "wiki/concepts/tech.ai.md")) == 1)

# --- url-log-append.py: admission is ingest's -------------------------------------- #
with tempfile.TemporaryDirectory() as d:
    os.makedirs(os.path.join(d, "logs"))
    os.makedirs(os.path.join(d, "lookups"))
    open(os.path.join(d, "logs", "sweep-url_log.md"), "w", encoding="utf-8").write("# log\n\n")
    open(os.path.join(d, "lookups", "raw-url-index.csv"), "w", encoding="utf-8").write("url_normalized,slug_key,file,published\n")

    def run(*args):
        return subprocess.run([sys.executable, str(SCRIPTS / "url-log-append.py"), *args],
                              cwd=d, capture_output=True, text=True)

    r = run("admitted", "https://example.org/a-story-here")
    check("url-log: `admitted` without --ingest is refused", r.returncode != 0 and "ingest" in r.stderr)
    log = open(os.path.join(d, "logs", "sweep-url_log.md"), encoding="utf-8").read()
    check("url-log: the refused admission wrote nothing", "example.org" not in log)
    r = run("admitted", "--ingest", "https://example.org/a-story-here")
    log = open(os.path.join(d, "logs", "sweep-url_log.md"), encoding="utf-8").read()
    check("url-log: `admitted --ingest` writes", r.returncode == 0 and "example.org" in log)
    r = run("dropped", "--code", "not-a-code", "https://example.org/b")
    check("url-log: an unknown drop code is refused", r.returncode != 0)
    r = run("dropped", "https://example.org/c-story-here")
    check("url-log: a sweep's plain `dropped` writes", r.returncode == 0)

# --- log-append.py: the entry form -------------------------------------------------- #
LA = load("log_append", "log-append.py")
line = LA.compose("wiki status", "3 counts", "none")
check("log: pass named in bold capitals", "**WIKI-STATUS**" in line)
check("log: revert hint present once", line.count("revert:") == 1)
check("log: a 'revert:' prefix is not doubled", LA.compose("lint", "x", "revert: git revert a").count("revert:") == 1)
for bad, label in [(("decision", "x", "none"), "a decision earns no line"),
                   (("agent", "x", "none"), "an agent earns no line"),
                   (("lint", "word " * 40, "none"), "over 40 words is refused"),
                   (("lint", "a\nb", "none"), "a newline is refused")]:
    try:
        LA.compose(*bad)
        check("log: " + label, False)
    except ValueError:
        check("log: " + label, True)
try:
    LA.stamp("2999-01-01T00:00")
    check("log: a future --at is refused", False)
except ValueError:
    check("log: a future --at is refused", True)

# --- ingest-lane.py: the whitelist --------------------------------------------------- #
IL = load("ingest_lane", "ingest-lane.py")
with tempfile.TemporaryDirectory() as d:
    root = pathlib.Path(d)
    for name, batch in [("a.md", "status-acquire-KEN"), ("b.md", "progress-filler-XAF"),
                        ("c.md", "dataset-x"), ("d.md", "budget-poll-1"), ("e.md", "country-deep-2026-10-01"),
                        ("f.md", None), ("g.md", "statusacquire-typo")]:
        fm = "---\ntitle: t\n" + (f"sweep_batch: {batch}\n" if batch else "") + "---\nbody\n"
        (root / name).write_text(fm, encoding="utf-8")
    (root / "a.pdf").write_bytes(b"%PDF")
    back, news, art = IL.partition(root)
    check("lane: four backfill prefixes", sorted(r for r, _ in back) == ["a.md", "b.md", "c.md", "d.md"])
    check("lane: no sweep_batch and a near-miss are news", {"f.md", "g.md", "e.md"} == {r for r, _ in news})
    check("lane: a binary rides apart", art == ["a.pdf"])

# --- page-length.py: a rewrite may not grow the page ------------------------------- #
PL = load("page_length", "page-length.py")
recorded = []
PL.record = lambda rel, b, a: recorded.append((rel, b, a))
for after, want in [(1000, 0), (1030, 0), (1100, 2)]:
    PL.measure = lambda p, after=after: ("wiki/intersections/x.md", {"effective": after})
    sys.argv = ["page-length.py", "--trimmed", "x", "--before", "1000"]
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        got = PL.main()
    check(f"page-length: 1000 -> {after} exits {want}", got == want)
check("page-length: every rewrite is recorded, grown or not", len(recorded) == 3)

# --- lint #15: an inspection stamp settles a false positive ------------------------ #
LD = load("lint_det", "lint-deterministic.py")


def c15(note):
    d = LD.Defects()
    fm = {"type": "source", "body_completeness": "full"}
    if note:
        fm["note"] = note
    LD.check_completeness([{"fm": fm, "path": "raw/x.md", "d": {"trunc_markers": ["elision"]}}], d)
    return len(d.of("15"))


check("lint #15: full over a marker is reported", c15(None) == 1)
check("lint #15: an inspected (lint #15) note settles it", c15("body_completeness `full` inspected 2026-09-22 (lint #15) and confirmed") == 0)
check("lint #15: a note that only says 'inspected' does not", c15("inspected by hand") == 1)

# --- promote-budget-companions.py: no second hub_line_none or lead ----------------- #
PB = load("promote", "promote-budget-companions.py")
with tempfile.TemporaryDirectory() as d:
    cwd = os.getcwd()
    os.chdir(d)
    try:
        comp = pathlib.Path("new-budget", "SEN", "2025", "2025-01-01-sen-lfi-2025-companion.md")
        comp.parent.mkdir(parents=True)
        lead = ("**Companion source page for a budget document.** Its artefact is filed at "
                "`budget-archive/SEN/2025/` and declared by its row in `new-budget/manifest.csv`.")
        comp.write_text("---\ntitle: \"Loi de finances 2025\"\nurl: https://finances.gouv.sn/lfi-2025.pdf\n"
                        "doc_type: appropriation-act\ntopics: [finance.budget]\n"
                        "hub_line_none: 2026-10-01  # staged\n---\n# Loi de finances 2025\n\n" + lead + "\n",
                        encoding="utf-8")
        res, err = PB.promote(comp, set(), {}, {})
        text = res[1] if res else ""
        check("promote: promotes an appropriation act", err is None and res is not None)
        check("promote: one hub_line_none, not two", text.count("hub_line_none:") == 1)
        check("promote: one lead, not two", text.count("**Companion source page for a budget document.**") == 1)
        hero = [l for l in text.splitlines() if l.startswith("catalogue_hero:")]
        check("promote: the hero is not the title", hero and "Loi de finances 2025" not in hero[0])
        check("promote: the hero is within 120 characters", hero and len(hero[0].split(":", 1)[1].strip().strip('"')) <= 120)
    finally:
        os.chdir(cwd)

# --- sources-add.py: append as text, never split a comma-bearing entry ------------- #
SA = load("sources_add", "sources-add.py")
with tempfile.TemporaryDirectory() as d:
    p = os.path.join(d, "page.md")
    old = "[2026-01-11 Roundup, 2025, Projections for 2026]"
    open(p, "wb").write(("---\r\ntitle: t\r\nsources: [" + old + ", [2026-02-01-a]]\r\ntopics: [x]\r\n---\r\nbody\r\n").encode())
    n = SA.add(p, ["2026-10-02-b", "2026-02-01-a"])
    t = open(p, "rb").read().decode()
    check("sources-add: adds the new slug only", n == 1 and "[2026-10-02-b]" in t and t.count("[2026-02-01-a]") == 1)
    check("sources-add: the comma-bearing entry survives whole", old in t)
    check("sources-add: CRLF kept, no bare LF", t.count("\n") == t.count("\r\n"))
    check("sources-add: a second run is a no-op", SA.add(p, ["2026-10-02-b"]) == 0)
    q = os.path.join(d, "bare.md")
    open(q, "w", encoding="utf-8", newline="").write("---\ntitle: t\n---\nbody\n")
    SA.add(q, ["2026-10-02-c"])
    check("sources-add: a page without the key gets one", "sources: [[2026-10-02-c]]\n---" in open(q, encoding="utf-8").read())

print(f"\n{len(FAILS)} failure(s)")
sys.exit(1 if FAILS else 0)
