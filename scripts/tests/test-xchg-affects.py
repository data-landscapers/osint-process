"""Unit test of lint #24's `Affects:` half — the rule that a note names the output it bears on.

The claim the rule rests on is the review's: around a third of the notes in the archive were
about the other side's internal housekeeping, and none of them could have filled this line
in, while none of the genuine interface defects would struggle to. That claim is what is
tested here — four notes of the shape it exists to block, and eight real interface defects
drawn from the archive that it must not.

The check counts three things and no more: the line is present, it does not say *nothing*,
and it names something a reader can go to. Whether the line is **true** is the writer's, and
a check built to adjudicate that would either pass everything or argue with its own writer.

Run: python scripts/tests/test-xchg-affects.py
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


class Rows:
    def __init__(self):
        self.rows = []

    def add(self, check, path, defect, detail="", soft=False):
        self.rows.append((path, defect, soft))


def run(**files):
    """Findings from `check_xchg_affects` over a fabricated share."""
    tmp = tempfile.mkdtemp()
    for name, text in files.items():
        open(os.path.join(tmp, name), "w", encoding="utf-8").write(text)
    keep, ld.XCHG = ld.XCHG, tmp + os.sep
    try:
        d = Rows()
        ld.check_xchg_affects(d)
        return d.rows
    finally:
        ld.XCHG = keep


def note(n, affects=None, title="Something happened."):
    body = f"**{n}** [ACT] (2026-08-28) - **{title}**\n\n"
    if affects is not None:
        body += f"Affects: {affects}\n\n"
    return body + "Some text about it.\n\n"


def outbox(*notes):
    return run(**{ld.XCHG_OUTBOX: "# Notes\n\n## Unresolved\n\n" + "".join(notes)})


# --- the four shapes the rule exists to block --------------------------------------
BLOCKED = [
    note(1, None, "Your repo is 15 GB and .git is a third of it."),
    note(2, "n/a", "The wording of your process file could be tighter."),
    note(3, "nothing", "Your sub-agent spend policy looks expensive."),
    note(4, "general housekeeping on your side", "Your log entries run long."),
]
for i, n in enumerate(BLOCKED, 1):
    rows = outbox(n)
    assert len(rows) == 1, f"blocked shape {i} passed: {rows}"
    assert rows[0][2] is False, "the outbox gates the exit code"

# --- eight genuine interface defects, none of which may be blocked -----------------
PASSES = [
    "`site/reports/AGO-status.md` - the not-held tally is wrong on the published page",
    "the daily bulletin's *Last updated* byline",                     # a named output
    "`scripts/lint-osint-freshness.py` and `osint_lib.py`",
    "outputs/non-state-finance/all-nonstate.csv - two rows for one deal",
    "strategic review task 14",
    "note 51, whose two exceptions this closes",
    "housekeeping job 79 - the IATI half",
    "`wiki/intersections/eswatini--dpi-pay.md`, which publishes the superseded series",
]
for a in PASSES:
    rows = outbox(note(9, a))
    assert rows == [], f"a genuine defect was blocked by {a!r}: {rows}"

# --- the ownership split -----------------------------------------------------------
rows = run(**{ld.XCHG_INBOX: "# Notes\n\n" + note(1, None)})
assert len(rows) == 1 and rows[0][2] is True, "the inbox is reported, never failed"

both = run(**{ld.XCHG_OUTBOX: "# N\n\n" + note(1, None),
              ld.XCHG_INBOX: "# N\n\n" + note(2, None)})
assert sorted(r[2] for r in both) == [False, True], both

# --- shape tolerances --------------------------------------------------------------
# emphasis on the label, and the line anywhere in the block rather than only under the title
assert outbox(note(5, None).replace("Some text about it.",
                                    "**Affects:** `wiki/places/AGO.md`")) == []
# a file with no notes at all is clean, and an absent file is not a vault defect
assert run(**{ld.XCHG_OUTBOX: "# Notes\n\n*(Nothing is open.)*\n"}) == []
assert run() == []

# --- the live share ----------------------------------------------------------------
if os.path.isdir(ld.XCHG):
    d = Rows()
    ld.check_xchg_affects(d)
    hard = [r for r in d.rows if not r[2]]
    assert not hard, f"OSINT's outbox carries a note with no Affects line: {hard}"

print("test-xchg-affects: all assertions pass")
