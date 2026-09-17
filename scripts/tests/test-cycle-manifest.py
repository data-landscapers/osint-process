"""Unit test of scripts/cycle-manifest.py — the parsers, the stamp writer, the staleness check.

The manifest is read by the other system and by nothing here, so a defect in it is
invisible on this side by construction: CORPUS would publish from a well-formed file
saying the wrong thing. Four things are therefore pinned. **The rotation parser** reads
its columns by name, so a column added to `logs/sweep-cycle_log.md` must not shift the
values under it and a column renamed must leave its field absent rather than wrong.
**The collection reader** returns exactly what `--stamp` last wrote to
`logs/collection-stamp.json`, and **the stamp writer** refuses a malformed or future value
rather than writing one — the two defects that used to be caught after the fact in
`ingested_log.md`'s headers are now refused at the write instead. And **`--check`** must
fail on a manifest naming an earlier commit — the one failure mode that looks exactly like
success from the reading side.

Run: python scripts/tests/test-cycle-manifest.py
"""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

REPO = str(pathlib.Path(__file__).resolve().parents[2])
sys.path.insert(0, os.path.join(REPO, "scripts"))
SCRIPT = os.path.join(REPO, "scripts", "cycle-manifest.py")
spec = importlib.util.spec_from_file_location("cm", SCRIPT)
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

TMP = tempfile.mkdtemp()

# --- the rotation table ------------------------------------------------------------
TABLE = """# heading prose, not a table

| Day | Jobs                | Gate | Skip | Start            | End              | Duration | Prev Duration | New-Start |
| --- | ------------------- | ---- | ---- | ---------------- | ---------------- | -------- | ------------- | --------- |
| 1   | SWEEP-A, SWEEP-B    |      |      | 2026-08-25 19:49 | 2026-08-25 22:57 | 3:08     | 3:04          |           |
| 2   | SWEEP-C             |      | x    | 2026-08-26 20:30 | 2026-08-27 03:55 | 7:25     | 4:29          |           |
| 3   | SWEEP-D             |      |      | 2026-08-27 19:07 | 2026-08-27 21:31 | 2:24     | 7:23          | 2026-08-28 20:00 |
| 4   | SWEEP-E             |      |      |                  |                  |          |               |           |
"""
cm.CYCLE_LOG = os.path.join(TMP, "cycle.md")
open(cm.CYCLE_LOG, "w", encoding="utf-8").write(TABLE)
r = cm.rotation()
assert r["days"] == 4, r
assert r["newest_close"]["day"] == "3", r["newest_close"]
assert r["newest_close"]["jobs"] == ["SWEEP-D"], r["newest_close"]
assert r["newest_close"]["end"] == "2026-08-27 21:31"
assert r["in_progress"] == ["3"], r["in_progress"]

# a day that has never run is honest rather than absent, and never the newest close
assert [d for d in [r["newest_close"]] if d["end"]], "a closed day must carry its End"

# columns read by name: a column added to the table must not shift the values
WIDER = """| Day | Notes | Jobs             | Gate | Skip | Start            | End              | Duration | Prev Duration | New-Start |
| --- | ----- | ---------------- | ---- | ---- | ---------------- | ---------------- | -------- | ------------- | --------- |
| 1   | n     | SWEEP-A, SWEEP-B |      |      | 2026-08-25 19:49 | 2026-08-25 22:57 | 3:08     | 3:04          |           |
| 3   | n     | SWEEP-D          |      |      | 2026-08-27 19:07 | 2026-08-27 21:31 | 2:24     | 7:23          |           |
"""
open(cm.CYCLE_LOG, "w", encoding="utf-8").write(WIDER)
wider = cm.rotation()
assert wider["newest_close"]["day"] == "3", wider["newest_close"]
assert wider["newest_close"]["end"] == "2026-08-27 21:31", wider["newest_close"]
assert wider["newest_close"]["jobs"] == ["SWEEP-D"], wider["newest_close"]

# a column this does not know is absent, never guessed from a neighbour
RENAMED = TABLE.replace("| End              |", "| Finished         |", 1)
open(cm.CYCLE_LOG, "w", encoding="utf-8").write(RENAMED)
assert cm.rotation()["newest_close"] is None, "no End column means no closed day, not a wrong one"

cm.CYCLE_LOG = os.path.join(TMP, "absent.md")
assert cm.rotation() is None, "an unreadable rotation is absent, never a guess"

# --- the collection window ---------------------------------------------------------
cm.STAMP = os.path.join(TMP, "collection-stamp.json")

# nothing stamped yet -> absent, not a guess
assert cm.collection() is None, "no stamp file means no collection window, not an empty one"

v = cm.write_stamp("2026-08-27 19:58", "2026-08-27 20:08", "2026-08-27 20:36")
assert v["sweep_closed"] == "2026-08-27 19:58", v
c = cm.collection()
assert c["last_admission"] == "2026-08-27 20:36", c
assert c["sweep_closed"] == "2026-08-27 19:58", "collection, not admission"
assert c["ingest_started"] == "2026-08-27 20:08", c

# a later stamp overwrites the whole object -- one object, not a rolling log
cm.write_stamp("2026-08-28 09:00", "2026-08-28 09:10", "2026-08-28 09:30")
c = cm.collection()
assert c["sweep_closed"] == "2026-08-28 09:00", "the newest stamp, not the oldest"

# malformed or future values are refused, and nothing is written on refusal
before = open(cm.STAMP, encoding="utf-8").read()
try:
    cm.write_stamp("not-a-date", "2026-08-28 09:10", "2026-08-28 09:30")
    raise AssertionError("a malformed sweep_closed must raise")
except ValueError:
    pass
try:
    cm.write_stamp("2099-01-01 00:00", "2026-08-28 09:10", "2026-08-28 09:30")
    raise AssertionError("a future sweep_closed must raise")
except ValueError:
    pass
assert open(cm.STAMP, encoding="utf-8").read() == before, "a refused --stamp must not write"

# --- --check: a manifest naming an earlier commit is the failure that looks like success
cm.MANIFEST = os.path.join(TMP, "cycle-manifest.json")
assert cm.check() == 1, "an absent manifest fails"

local = cm.git("rev-parse", "HEAD")
assert local, "the test needs a git tree"


def write(**over):
    m = {"schema": cm.SCHEMA, "head": local, "written_utc": "2026-08-28 08:00", "pass": "t"}
    m.update(over)
    open(cm.MANIFEST, "w", encoding="utf-8").write(json.dumps(m))


write()
assert cm.check() == 0
write(head="0" * 40)
assert cm.check() == 1, "a stale head must fail"
write(schema=cm.SCHEMA + 1)
assert cm.check() == 1, "a schema the reader does not know must fail"
open(cm.MANIFEST, "w", encoding="utf-8").write("{not json")
assert cm.check() == 1, "an unreadable manifest fails rather than raising"

# --- the usage block (schema 2): buffered stage readings, keyed by stage, in order
cm.STAGES = os.path.join(TMP, "usage-stages.jsonl")
assert cm.usage_block() is None, "no buffer, no block"
assert "usage" not in cm.build("t", {}, usage=True), "an absent buffer writes no usage block"
open(cm.STAGES, "w", encoding="utf-8").write(
    '{"stage": "start", "time_utc": "2026-09-17 18:00", "seven_day": 60.0, "five_hour": 10.0}\n'
    'not json\n'
    '{"stage": "sweep", "time_utc": "2026-09-17 19:00", "seven_day": 63.5, "five_hour": null}\n'
    '{"stage": "sweep", "time_utc": "2026-09-17 19:10", "seven_day": 64.0, "five_hour": 30.0}\n')
b = cm.usage_block()
assert list(b) == ["start", "sweep"], "stages keep their order; a malformed line is skipped"
assert b["sweep"]["seven_day"] == 64.0, "a stage read twice keeps its last reading"
assert "usage" not in cm.build("t", {}), "without --usage there is no block, buffer or not"
m = cm.build("t", {}, usage=True)
assert m["schema"] == 2 and m["usage"] == b

print("test-cycle-manifest: all assertions pass")
