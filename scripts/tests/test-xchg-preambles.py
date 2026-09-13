"""Unit test of lint #24's share half — the preamble cap and the one-statement rule.

Both halves are cheap to state and easy to get wrong in the same direction: a cap that
measures the wrong thing passes everything, and a duplicate check that can be satisfied
by deleting README's own sentence disarms itself. So four things are pinned here — the
**boundary** (frontmatter is not preamble, and the file's own substance is not either),
the **fold** (a convention copied and rewrapped is still a copy), the **ownership split**
(OSINT's files gate the exit code, a file the run may not edit is reported), and the
**self-disarm guard** (README losing a fingerprint is itself a hard finding).

Run: python scripts/tests/test-xchg-preambles.py
"""
import importlib.util
import os
import pathlib
import sys
import tempfile

REPO = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRIPT = os.path.join(REPO, "scripts", "lint-deterministic.py")
spec = importlib.util.spec_from_file_location("ld", SCRIPT)
ld = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ld)

RULE = "closing means moving, and nothing is left at the number"
assert RULE in ld.XCHG_RULES

# --- the fold: a rule survives emphasis, curly punctuation and a hard wrap ----------
assert RULE in ld.xchg_fold("**Closing means moving, and nothing is\nleft at the number**")
assert RULE in ld.xchg_fold("`Closing means moving, and nothing is left at the number`")
assert RULE not in ld.xchg_fold("closing a note means moving it, and nothing is left behind")

# --- the boundary: frontmatter out, the file's own substance out --------------------
DOC = ("---\ntype: doc\ntitle: t\n---\n\n"
       "# Register\n\n" + "word " * 300 + "\n\n## The bar\n\n" + "body " * 900 + "\n")
assert ld.xchg_preamble(DOC, "## The bar") == 302, ld.xchg_preamble(DOC, "## The bar")
assert ld.xchg_preamble("# T\n\n## Done\n\n" + "x " * 400, "## Done") == 2

# --- the check, over a fabricated share --------------------------------------------
README = ("# share\n\n## Conventions\n\n"
          + "\n\n".join(f"**{r.capitalize()}.**" for r in ld.XCHG_RULES) + "\n")


class Rows:
    def __init__(self):
        self.rows = []

    def add(self, check, path, defect, detail="", soft=False):
        self.rows.append((path, defect, soft))


def run(files, readme=README):
    tmp = tempfile.mkdtemp()
    open(os.path.join(tmp, ld.XCHG_README), "w", encoding="utf-8").write(readme)
    for name, text in files.items():
        open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)
    keep, ld.XCHG = ld.XCHG, tmp + os.sep
    try:
        d = Rows()
        ld.check_xchg_preambles(d)
        return d.rows
    finally:
        ld.XCHG = keep


CLEAN = "# Register\n\n*(Pointer to README.)*\n\n## The bar\n\nreal substance\n"
assert run({"housekeeping-jobs.md": CLEAN}) == []

# an over-long preamble on an OSINT file is hard; the same on CORPUS's is reported
LONG = "# Register\n\n" + "word " * 400 + "\n\n## The bar\n\nreal substance\n"
rows = run({"housekeeping-jobs.md": LONG})
assert len(rows) == 1 and "preamble runs 402 words" in rows[0][1] and rows[0][2] is False
rows = run({"notes-for-osint.md": "# Notes\n\n" + "word " * 400
            + "\n\n## Standing constraints\n\nx\n"})
assert len(rows) == 1 and rows[0][2] is True, rows

# a convention restated away from home is a finding wherever in the file it sits
rows = run({"housekeeping-jobs.md": "# R\n\n*(P.)*\n\n## The bar\n\n"
            "**Closing means moving, and nothing is\nleft at the number.**\n"})
assert len(rows) == 1 and rows[0][1] == "restates a share convention", rows

# --- the self-disarm guard ---------------------------------------------------------
rows = run({"housekeeping-jobs.md": CLEAN}, readme=README.replace(RULE.capitalize(), "gone"))
assert len(rows) == 1 and rows[0][0] == ld.XCHG_README and rows[0][2] is False, rows

# --- the live share, if it is mounted ----------------------------------------------
if os.path.isdir(ld.XCHG):
    d = Rows()
    ld.check_xchg_preambles(d)
    hard = [r for r in d.rows if not r[2]]
    assert not hard, f"the share carries hard #24 findings: {hard}"

print("test-xchg-preambles: all assertions pass")
