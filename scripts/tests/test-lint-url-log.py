"""Unit test of scripts/lint-url-log.py — the joins, and the two rules that are judgement.

The check exists because a wrong line in `sweep-url_log.md` is invisible downstream, so
its own joins are asserted rather than trusted. Two of them are not lookups but rulings
and are the ones worth pinning: **`stem()`**, which must join a tidied log URL to the
file it belongs to without joining two unrelated pages on the same host, and the
**dead-slice rate**, which must promote a slice that lost several admissions while
leaving a single bad line in a long night alone — the case that would otherwise bury
forty-seven ordinary drops under one orphan.

Run: python scripts/tests/test-lint-url-log.py
"""
import importlib.util
import os
import pathlib
import sys

REPO = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRIPT = os.path.join(REPO, "scripts", "lint-url-log.py")
spec = importlib.util.spec_from_file_location("lul", SCRIPT)
lul = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lul)

# --- stem(): what may join, and what may not --------------------------------------
assert lul.stem("nymag.com/intelligencer/article/china-us-ai-regulation.html") == \
       lul.stem("nymag.com/intelligencer/article/china-us-ai-regulation")
assert lul.stem("obs.com/news/lta-signs-a-new-satellite-framework/article_e178022e-dcdf-47e5") == \
       lul.stem("obs.com/news/lta-signs-a-new-satellite-framework")
assert lul.stem("example.com/news") == "", "a bare path must key nothing"
assert lul.stem("a.com/one-story-about-things") != lul.stem("a.com/another-story-entirely")

# --- the joins ---------------------------------------------------------------------
IDX = (
    {"a.com/held-story-here": "raw/2026/2026-01-01-held.md",
     "b.com/tidied-story-path-here.html": "raw/2026/2026-01-02-stem.md",
     "c.com/%d8%a3%d8%b7%d8%a8": "raw/2026/2026-01-03-arabic.md",
     "d.com/twin-story-goes-here": "raw/2026/2026-01-04-twin.md"},
    {}, {}, {})
IDX[1].update({lul.loose(k): v for k, v in IDX[0].items()})
IDX[2].update({lul.stem(k): v for k, v in IDX[0].items() if lul.stem(k)})
IDX[3].update({(lul.host_of(k), lul.slug_key(k)): v
               for k, v in IDX[0].items() if lul.slug_key(k)})


def row(disp, url, tail="", section="S", nourl=False):
    return {"section": section, "line": 1, "date": "2026-08-21", "disp": disp,
            "url": url, "norm": url, "tail": tail, "nourl": nourl}


def verdicts(rows, rejected=None, droplist=None, queued=None):
    lul.adjudicate(rows, IDX, {}, rejected or {}, droplist or {}, queued or set())
    return [r["verdict"] for r in rows]


assert verdicts([row("admitted", "a.com/held-story-here")]) == ["HELD"]
assert verdicts([row("admitted", "b.com/tidied-story-path-here")]) == ["HELD-STEM"]
assert verdicts([row("admitted", "c.com/أطب")]) == ["HELD-DECODED"]
assert verdicts([row("admitted", "z.com/nothing-at-all-here")]) == ["ORPHAN"]
assert verdicts([row("admitted", "z.com/x", nourl=True)]) == ["NO-URL"]
assert verdicts([row("admitted", "z.com/gone-story", "(captured via a syndication)")]) == ["NOTED"]

# an admission the same log later drops is a re-adjudication, not a lost file
assert verdicts([row("admitted", "z.com/two-minds-on-this"),
                 row("dropped", "z.com/two-minds-on-this")]) == ["SUPERSEDED", "BARE"]

assert verdicts([row("dropped", "a.com/held-story-here")]) == ["HELD-AFTER"]
assert verdicts([row("dropped", "z.com/x-story", "(out of scope on place)")]) == ["ANNOTATED"]
assert verdicts([row("dropped", "z.com/x-story")], rejected={"z.com/x-story": "remit"}) == \
       ["REJECTED"]
assert verdicts([row("dropped", "bad.example/x-story")], droplist={"bad.example": "drop"}) == \
       ["DOMAIN"]
assert verdicts([row("dropped", "d.com/archive/twin-story-goes-here")]) == ["TWIN"]

# an acquisition has no raw/ file by construction; only the register or a landed fetch
assert verdicts([row("acquisition", "z.com/wanted-document-here")]) == ["SPENT"]
assert verdicts([row("acquisition", "z.com/wanted-document-here")],
                queued={"z.com/wanted-document-here"}) == ["QUEUED"]
assert verdicts([row("acquisition", "a.com/held-story-here")]) == ["HELD"]

# --- the dead-slice rate: promote a lost slice, spare a long clean night ------------
dead = ([row("admitted", "z.com/lost-one-story-here", section="dead"),
         row("admitted", "z.com/lost-two-story-here", section="dead"),
         row("admitted", "a.com/held-story-here", section="dead"),
         row("dropped", "z.com/collateral-drop-here", section="dead")])
assert verdicts(dead)[-1] == "SUSPECT", "two of three admissions lost is a dead slice"

night = [row("admitted", "z.com/lost-one-story-here", section="night")]
night += [row("admitted", "a.com/held-story-here", section="night") for _ in range(30)]
night += [row("dropped", "z.com/ordinary-drop-here", section="night") for _ in range(20)]
assert set(verdicts(night)[-20:]) == {"BARE"}, "one orphan in thirty-one is not a dead slice"

# --- header arithmetic: a header itemising its drops declares their sum -------------
assert lul.header_counts("slice-003 (6 admitted incl. 1 finance record, 2 dropped as "
                         "tier-3 duplicates, 2 dropped as out-of-scope)") == (6, 4)
assert lul.header_counts("slice 5/10 (10 items: 6 admitted, 4 dropped)") == (6, 4)
assert lul.header_counts("a run with nothing declared") == (None, None)

# --- ghost citations: the reason names a file, the file is checked -----------------
assert lul.RAWREF.search("(duplicate of held raw/2026/2026-01-01-held.md)").group(0) == \
       "raw/2026/2026-01-01-held.md"
assert not lul.RAWREF.search("(out of scope on place, nothing held)")

print("ok — lint-url-log — all assertions passed")
