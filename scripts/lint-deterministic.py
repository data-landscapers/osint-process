#!/usr/bin/env python3
"""lint-deterministic.py — the mechanical half of LINT.md, as a script.

Nine of lint's checks ask questions with exactly one right answer: does this
file carry the keys its type requires, is that place code in `countries.csv`, is
this filename in the shard its own date prefix names, does this `[[link]]` resolve.
They were performed by the model, over the whole vault, every cycle — the single
largest recurring cost in the system, growing with the corpus on a fixed cadence.
This answers all nine in about a second, off `index/`, against
`lookups/frontmatter-schema.json`.

  #1   schema integrity     required keys, enums, patterns, the finance rules
  #2   vocabulary           places vs countries.csv, topics vs taxonomy.md, legacy lens
  #3   freshness            `last_reviewed` absent or over 90 days
  #4   orphans & dead links unresolved `[[targets]]`, banded per §9; pages nothing cites
  #11  filenames            date prefix, shard, intersection form
  #12  link-list convention `[[[a]], [[b]]]` and unclosed lists
  #15  body_completeness    missing on a source; `full` over a wall/elision marker
  #23  region place code    3+ countries of one region, no region code — soft, a person rules
  #10  stranded queue       anything left in `new/`
  #24  register caps        post-run notes: 60 words each, 10 open, `[CRITICAL]` only
  #25  procedure length     `CLAUDE.md` over its line cap - that file only, from 2026-08-20
  #28  deal-record vocab    Instrument/Status/Beneficiary type against `deal-vocabs.csv`
  #34  catalogue hero       the subtitle every post-contract source carries, and its shape
  #8   page bloat          over §8's ~2,500-word classify line, by shape; hubs' compiled chronology exempt

**#24 and #25 exist because the same limits were written as prose and broke inside a
week** (2026-08-10, token review tasks 5, 6 and 16): the 60-word note cap was ignored on
five notes running 150–300+ words, and `log.md` regrew 852 KB → 1.41 MB. A limit is
enforced by a script or it is removed; there is no third state.

**It reports; it does not edit.** Lint's disposition for most of these is
auto-fix, and the fix is still CC's to make — what was expensive was never the
edit, it was finding the twelve files out of twelve thousand. The judgment halves
stay with the model and are deliberately absent here: #3's undated-figure reading,
#4's "is there enough material for a page", #6's origins, #7's payload comparison,
#9's contradictions.

Usage:
  python scripts/lint-deterministic.py              summary of all checks
  python scripts/lint-deterministic.py --check 1    every defect in one check
  python scripts/lint-deterministic.py --check 4 --limit 40
  python scripts/lint-deterministic.py --json       machine-readable, all defects

Exit 1 if any HARD defect exists, so a pass can gate on it. Soft findings — the
`x-expected` keys a type usually but not always carries — never gate.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SCHEMA_PATH = os.path.join(V.ROOT, "lookups", "frontmatter-schema.json")
COUNTRIES = os.path.join(V.ROOT, "lookups", "countries.csv")
TAXONOMY = os.path.join(V.ROOT, "lookups", "taxonomy.md")
FRESH_DAYS = 90

NOTES = os.path.join(V.ROOT, "reviews", "post-run-notes.md")
NOTE_WORD_CAP = 60          # CLAUDE.md → Reporting; post-run-notes.md → The bar
NOTE_OPEN_CAP = 10          # at the cap CC rules for itself and logs it

# The same cap over the two exchange note files, from 2026-08-27 (strategic review task 4).
# Both are on the shared drive, both are co-written, and open notes there ran 409 and 2,386
# words against the same stated 60. `**NN** [BAND] (date)` is the shape `status.py` counts by;
# a note's block is measured whole, annotations included, because a dated comment prepended to
# a note is part of what the reader has to get through to reach the ask.
XCHG = "X:" + os.sep if os.name == "nt" else "/x/"
XCHG_NOTES = ("notes-for-osint.md", "notes-for-corpus.md")
XCHG_INBOX, XCHG_OUTBOX = XCHG_NOTES
# The `Affects:` line, from 2026-08-28 (strategic review task 16). The three things a check
# can honestly count: present, not a way of saying nothing, and naming something a reader can
# reach: a path or an artefact in code font, work already commissioned cited by number, or a
# published thing named in words. That last one needs a small vocabulary, because README lets
# a line say "the daily bulletin's byline" and no punctuation rule can tell that from "your
# repo size". Kept short deliberately — a word missing from it costs the writer a rewording,
# where a list long enough to cover everything would pass everything.
XCHG_AFFECTS_RE = re.compile(r"^\**Affects:\**\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
XCHG_AFFECTS_EMPTY = {"n/a", "na", "none", "nothing", "nothing yet", "general", "tbd",
                      "unknown", "-", "—", "various", "everything"}
XCHG_AFFECTS_NAMES = re.compile(
    r"[`/]|\.(?:md|py|csv|json|html|pdf)\b|"
    r"\b(?:task|note|job)\s+\d+|"
    r"\b(?:bulletin|report|monthly|catalogue|dataset|page|site|ledger|index|brief|"
    r"byline|publication|output|manifest|chart|table|feed|compile|hub)\b", re.IGNORECASE)
XCHG_NOTE_RE = V.XCHG_NOTE_RE        # one parser, shared with status.py

# The share's conventions live once, in `X:\README.md`, and every other file there carries a
# pointer and its own content. Two things follow, and #24 asserts both. A **preamble cap**: the
# text above a file's own substance is held to 250 words, measured to a boundary named per file
# because "the header" is not the same shape twice — a register's is what sits above the bar, a
# resolved archive's is what sits above the first entry. And **no rule stated twice**: a
# convention copied out of README -> Conventions is a rule that will disagree with itself, so a
# copy is a defect where it lands, and README dropping one is a defect at home — a check that
# can disarm itself by deleting its own reference is not a check.
XCHG_README = "README.md"
XCHG_PREAMBLE_CAP = 250
# file -> the line prefix its preamble runs to. Owned files gate the exit code; a file the run
# may not edit is reported and never fails, because a lint that fails on someone else's work is
# one that gets skipped.
XCHG_PREAMBLES = {
    "housekeeping-jobs.md": ("## Rough sizing", False),
    "housekeeping-jobs-resolved.md": ("## Done", False),
    "notes-for-corpus.md": ("## Unresolved", False),
    "notes-for-corpus-resolved.md": ("## ", False),
    "notes-for-osint.md": ("## Standing constraints", True),
}
# Fingerprints of the conventions, normalised the way `xchg_fold` normalises: a distinctive
# clause each, long enough that ordinary prose does not trip it and short enough to survive a
# rewrap. Cite a convention by pointer; never by copying its sentence.
XCHG_RULES = (
    "the bar for writing a note at all is high",
    "reasoning lives in the repo that owns it",
    "closing means moving, and nothing is left at the number",
    "numbers are never reused and the gap stays",
    "answering a note does not let you assign work in it",
    "both sides write, so re-read before editing",
    "corpus does the committing here; osint writes and stops",
    "a commit that is not pushed is not delivered",
    "the same repository, two drive letters",
    "if a later run can undo it, it is not",
)

# §9's intentional-dead whitelist: controlled-vocabulary values that are tags, not
# pages, and dead by design. Kept as a rule (these two + any taxonomy slug) rather
# than a list, so a new taxonomy value never has to be added here to stop being noise.
#
# The lens facet is retired (Bill, 2026-09-08 — facets.md §1): nothing writes `lens:`
# any more and it is no longer in the schema. These two values stay here for the
# 17,036 legacy ones still in the corpus, which are left in place rather than cleared
# — the whitelist keeps their body wikilinks out of §9, and #2 below still refuses an
# out-of-vocabulary lens so an invented value cannot slip in behind the retirement.
#
# `analysis` and `reference` are legacy values the corpus already carries. They were
# never in the vocabulary, but schemas.md §4 forbids clearing a retired key in passing,
# so #2 was reporting three findings no pass was permitted to fix — permanent noise,
# which trains the reader to ignore the check exactly as LINK_SKIP_PREFIX below says.
# Admitting them keeps the guard doing its one job: refusing a value that is genuinely
# new, since nothing writes `lens:` any more.
LENS_VALUES = {"sovereignty", "colonialism", "analysis", "reference"}

# §9 again: files whose job is to DOCUMENT the link convention, and the dated logs.
# Quoted syntax is not a citation, and a check that keeps reporting it trains the
# reader to ignore the check.
LINK_SKIP_PREFIX = ("logs/", "sweep/", "documentation/", "reviews/")


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def load_vocab():
    places = set()
    with open(COUNTRIES, encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            if row and row[0].strip() and row[0].strip().lower() != "iso-3":
                places.add(row[0].strip())
    topics = set()
    for line in open(TAXONOMY, encoding="utf-8"):
        m = re.match(r"^-\s+`([a-z][a-z0-9]*\.[a-z0-9-]+)`", line.strip())
        if m:
            topics.add(m.group(1))
    return places, topics


class Defects:
    """Collected findings. `hard` gates the exit code; `soft` never does."""

    def __init__(self):
        self.rows = []

    def add(self, check, path, defect, detail="", soft=False):
        self.rows.append({"check": check, "path": path, "defect": defect,
                          "detail": detail, "soft": soft})

    def of(self, check):
        return [r for r in self.rows if r["check"] == check]


# --------------------------------------------------------------------------- #
# #1 schema integrity — a small validator over the subset the schema uses
# --------------------------------------------------------------------------- #

def _type_ok(value, want):
    if isinstance(want, list):
        return any(_type_ok(value, w) for w in want)
    if want == "string":
        return isinstance(value, str)
    if want == "array":
        return isinstance(value, list)
    if want == "object":
        return isinstance(value, dict)
    return True


def validate_value(key, value, spec, path, d, check="1"):
    """One frontmatter value against one property schema. Reports, never raises."""
    if "const" in spec and value != spec["const"]:
        d.add(check, path, f"{key}: expected `{spec['const']}`, found `{value}`")
        return
    if "enum" in spec:
        if isinstance(value, list):
            for v in value:
                if v not in spec["enum"]:
                    d.add(check, path, f"{key}: `{v}` is not one of {spec['enum']}")
        elif value not in spec["enum"]:
            d.add(check, path, f"{key}: `{value}` is not one of {spec['enum']}")
        return
    if "type" in spec and not _type_ok(value, spec["type"]):
        d.add(check, path, f"{key}: expected {spec['type']}, found {type(value).__name__}")
        return
    if isinstance(value, str):
        if "pattern" in spec and not re.search(spec["pattern"], value):
            d.add(check, path, f"{key}: `{value[:60]}` does not match {spec['pattern']}")
        if spec.get("minLength") and len(value.strip()) < spec["minLength"]:
            d.add(check, path, f"{key}: empty")
        if spec.get("maxLength") and len(value) > spec["maxLength"]:
            d.add(check, path, f"{key}: {len(value)} characters, cap is {spec['maxLength']}")
    if isinstance(value, list) and "items" in spec:
        for v in value:
            validate_value(key + "[]", v, spec["items"], path, d, check)


def resolve(schema, ref):
    node = schema
    for part in ref.lstrip("#/").split("/"):
        node = node[part]
    return node


# Mojibake detection, derived rather than spelled out: every mangled character is
# just its own utf-8 bytes read back as cp1252, so the table builds itself from the
# correct characters and this file stays ASCII. `Ã`/`â‚¬` front
# the mangled accents and dashes respectively and are vanishingly rare in correct
# text, which is what makes the byte prefilter below cheap enough to run on every
# artefact. (Note 33, 2026-08-20: 16 files had accreted before anyone counted, and
# only the two that reached a `title:` were visible from a catalogue.)
_ORIGINALS = ("éèêàçôüáóí"
              "ñâîöùûÉÀ°«"
              "» ’“”–—…‘"
              "ÁÂÃÇÊÍÎÏÐ"
              "ÓÔÕÚÜÝ")


def _mangle(ch):
    """utf-8 bytes read as cp1252 - exactly what the bad fetcher did.

    Byte by byte, because cp1252 leaves 0x81/0x8D/0x8F/0x90/0x9D undefined and the
    readers that do this damage pass those bytes straight through rather than
    failing. Decoding the whole character at once raises instead, which is how the
    five accents carrying those bytes - A-acute, I-acute, I-diaeresis, Eth,
    Y-acute - fell out of the table and went uncounted.
    """
    out = []
    for b in ch.encode("utf-8"):
        try:
            out.append(bytes([b]).decode("cp1252"))
        except UnicodeDecodeError:
            out.append(chr(b))
    return "".join(out)


MOJIBAKE = tuple(m for m in (_mangle(c) for c in _ORIGINALS) if len(m) > 1)
_MOJ_LEAD = tuple(sorted({m[0].encode("utf-8") for m in MOJIBAKE}))


def count_mojibake(rel):
    """Bytes first, decode only on a hit - this runs over every artefact."""
    try:
        with open(os.path.join(V.ROOT, rel), "rb") as f:
            data = f.read()
    except OSError:
        return 0
    if not any(lead in data for lead in _MOJ_LEAD):
        return 0
    text = data.decode("utf-8", errors="replace")
    return sum(text.count(m) for m in MOJIBAKE)


def check_schema(rows, schema, d):
    dispatch = schema["x-dispatch"]["map"]
    for r in rows:
        fm, path = r["fm"], r["path"]
        if not fm:
            continue
        kind = fm.get("type")
        if kind not in dispatch:
            d.add("1", path, f"type: `{kind}` is not a page type",
                  "schemas.md §4 defines source / concept / place / entity / "
                  "intersection / query / query-result")
            continue
        spec = resolve(schema, dispatch[kind])
        props = spec.get("properties", {})
        for key in spec.get("required", []):
            v = fm.get(key)
            if v is None or (isinstance(v, str) and not v.strip()):
                # `parent` is empty on XGL alone, which is the root of the tree.
                if key == "parent" and fm.get("code") == "XGL":
                    continue
                # A blank `url:` is admissible with `url_note:` — a document with no
                # online posting anywhere (reference.md, note 111). Without the note it
                # is still a defect; with it, #1 reported a state the spec now sanctions
                # and the file could never be cleared.
                if key == "url" and str(fm.get("url_note") or "").strip():
                    continue
                d.add("1", path, f"missing required `{key}`")
        for folder, keys in (spec.get("x-required-in") or {}).items():
            if path.startswith(folder):
                for key in keys:
                    if not fm.get(key):
                        d.add("1", path, f"missing `{key}` (required under {folder})")
        for key in spec.get("x-expected", []):
            if key not in fm:
                d.add("1", path, f"no `{key}`", "expected on this type, not required",
                      soft=True)
        # Mojibake: utf-8 bytes read as cp1252 somewhere upstream, so `Türkiye` is
        # stored `TÃ¼rkiye`. Hard, because a verbatim body is the record and a
        # mis-encoded one silently fails every grep for the word it mangled. Sixteen
        # files had accreted before anyone counted (note 33, 2026-08-20 — which saw
        # only the two that reached a title, because a catalogue carries no bodies).
        n_moj = count_mojibake(path)
        if n_moj:
            d.add("1", path, f"mojibake — {n_moj} mis-encoded character(s)",
                  "utf-8 read as cp1252 upstream; repair the text, then find the fetcher")
        for key, value in fm.items():
            if key in props and value not in (None, ""):
                sub = props[key]
                if "$ref" in sub:
                    sub = resolve(schema, sub["$ref"])
                validate_value(key, value, sub, path, d)
        if fm.get("finance_origin"):
            check_finance(fm, path, schema, d)


def check_finance(fm, path, schema, d):
    """finance-record-spec.md's rules, applied on top of the source schema."""
    spec = schema["$defs"]["financeRecord"]
    for key in spec["required"]:
        if not fm.get(key):
            d.add("1", path, f"finance record missing `{key}`")
    if fm.get("date_source") == "proxy":
        d.add("1", path, "finance record carries `date_source: proxy`",
              "forbidden by finance-record-spec.md → Dates; lint #21 class 1")
    ents = set(V.as_list(fm.get("entities")))
    ps = fm.get("primary_subject")
    if ps and ps not in V.as_list(fm.get("topics")):
        d.add("1", path, f"primary_subject `{ps}` is not in topics")
    fs = fm.get("financier_slug")
    if fs and fs not in ents:
        d.add("1", path, f"financier_slug `{fs}` is not in entities")
    rs = fm.get("recipient_slug")
    if rs and rs not in ents:
        d.add("1", path, f"recipient_slug `{rs}` is not in entities",
              "soft: the entity pass reconciles recipients", soft=True)


# --------------------------------------------------------------------------- #
# the rest
# --------------------------------------------------------------------------- #

def check_vocabulary(rows, places, topics, d):
    for r in rows:
        fm, path = r["fm"], r["path"]
        for p in V.as_list(fm.get("places")) + ([fm["place"]] if fm.get("place") else []):
            if p not in places:
                d.add("2", path, f"place `{p}` is not in countries.csv")
        for t in V.as_list(fm.get("topics")):
            if t not in topics:
                d.add("2", path, f"topic `{t}` is not in taxonomy.md")
        if fm.get("type") == "concept" and fm.get("slug") not in topics:
            d.add("2", path, f"concept slug `{fm.get('slug')}` is not in taxonomy.md")
        # **The vocabulary clause is retired and replaced by its own inverse**
        # (2026-09-20, register R50): `lens:` was cleared from the whole corpus —
        # 15,372 records in `raw/`, then 1,696 files everywhere else — so a check
        # that reads the value had nothing left to read. What can still happen is a
        # pass starting to write the key again, which `schemas.md` §4 names as the
        # thing to catch, so presence is the finding and the value is irrelevant.
        # **`LENS_VALUES` stays** — `check_links` whitelists `sovereignty` and
        # `colonialism` from it as intentional-dead wikilink targets in body prose,
        # which the strip never touched (`operations.md` §9).
        if "lens" in fm:
            d.add("2", path, "`lens:` is retired and was cleared corpus-wide",
                  "schemas.md §4: nothing writes it, so a carrier means something "
                  "has started again")


def check_freshness(rows, today, d):
    import datetime
    for r in rows:
        fm, path = r["fm"], r["path"]
        if fm.get("type") not in ("concept", "place", "entity", "intersection"):
            continue
        lr = fm.get("last_reviewed")
        if not isinstance(lr, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", lr):
            continue                       # a missing/malformed value is #1's business
        try:
            age = (today - datetime.date.fromisoformat(lr)).days
        except ValueError:
            continue
        if age > FRESH_DAYS:
            d.add("3", path, f"last_reviewed {lr} — {age} days", "§4: over the 90-day bar")


def check_links(rows, links, d):
    smap = V.slug_map(rows)
    known = set(smap)
    topics_and_lens = {t for r in rows for t in V.as_list(r["fm"].get("topics"))} | LENS_VALUES
    # Entity slugs are dead-by-design, not a backlog to mint (R11, 2026-08-16 —
    # wiki/entities/ retired, the `entities:` tag kept). Built live from every
    # row's own `entities:` field rather than a snapshot, so it tracks the tag
    # as it grows. A `[[slug]]` body reference to a former entity page reads the
    # same as any other whitelisted tag: never "wanted page — create it".
    entity_slugs = {e for r in rows for e in V.as_list(r["fm"].get("entities"))}
    topics_and_lens = topics_and_lens | entity_slugs
    unresolved = defaultdict(list)
    for l in links:
        src = l["from"]
        if src in V.LINK_CHECK_SKIP or src.startswith(LINK_SKIP_PREFIX):
            continue
        # A stored body in `raw/` is someone else's text and is immutable, so a
        # bracket sequence inside one that parses as a wikilink has neither of
        # this check's dispositions available: the target cannot be minted and
        # the body cannot be edited. Markdown image-in-link syntax is the usual
        # source. The frontmatter of the same record is ours and stays in scope.
        if src.startswith("raw/") and l["via"] == "body":
            continue
        # `entities:` is NOT a link check. CLAUDE.md → Entities: below the paging
        # bar an entity lives as a tag with no page, and that is expected, not a
        # gap — treating the tag as a dead link reports 3,400 non-defects and
        # buries the ~200 real ones.
        if l["via"] not in ("sources", "body", "cite_through"):
            continue
        tgt = l["to"].strip()
        if not tgt or tgt in known:
            continue
        if tgt in topics_and_lens:
            continue                        # §9 whitelist: a tag, not a page
        # An artefact reference resolves by filename and is correct as written. This
        # test runs BEFORE the path-citation test below, and the order is the whole
        # point (note 108, 2026-08-05): §3 gives an artefact its companion page's own
        # stem, so `name.pdf` always has a matching `name` in `known` and the path
        # check claimed every well-formed embed. It reported 204, of which 1 was real.
        if tgt.endswith((".pdf", ".xlsx", ".csv", ".txt", ".docx", ".png", ".jpg")):
            continue                        # artefact reference, resolved by filename
        # A citation written as a path (`[[raw/2025/2025-12-04 Algeria …]]`) points
        # at a file that exists — §3 says citations are bare slugs, and the path form
        # broke the moment raw/ was sharded. A convention defect, not a dead link.
        stem = os.path.splitext(tgt.replace("\\", "/").rsplit("/", 1)[-1])[0]
        if stem in known:
            d.add("12", src, f"citation written as a path: [[{tgt[:70]}]]",
                  f"§3: bare slug, never a path — [[{stem[:60]}]]")
            continue
        unresolved[tgt].append((src, l["line"], l["via"]))
    for tgt, refs in sorted(unresolved.items(), key=lambda kv: -len(kv[1])):
        n = len(refs)
        band = ("wanted page — §9 says create it" if n >= 10 else
                "middle band — create if the material is there" if n >= 3 else
                "stray — fix or delete")
        where = "; ".join(f"{s}:{ln}" for s, ln, _v in refs[:3])
        d.add("4", refs[0][0], f"[[{tgt}]] resolves to nothing — {n} referrer(s)",
              f"{band} ({where})")

    # 4b: a page nothing cites. Not a defect on its own — an intersection reached
    # only from its hub is normal — but a page nothing at all points at is either
    # missing from its index or was never linked when it was written.
    cited = {l["to"] for l in links}
    for r in rows:
        if r["fm"].get("type") in ("concept", "entity", "intersection") \
           and r["d"]["slug"] not in cited:
            d.add("4", r["path"], "nothing links to this page",
                  "add it to its index, or link it from the pages it belongs to", soft=True)


def check_filenames(rows, schema, d):
    dispatch = schema["x-dispatch"]["map"]
    for r in rows:
        fm, path, dd = r["fm"], r["path"], r["d"]
        kind = fm.get("type")
        if kind not in dispatch:
            continue
        spec = resolve(schema, dispatch[kind])
        rule = spec.get("x-filename")
        if not rule:
            continue
        name = dd["slug"]
        if kind == "source" and not path.startswith(("raw/", "new/")):
            continue                        # companions in the archives file by folder
        if not re.match(rule["pattern"], name):
            d.add("11", path, f"filename does not match {rule['pattern']}", rule["note"])
            continue
        if kind == "source" and path.startswith("raw/"):
            shard = path.split("/")[1]
            if shard != name[:4]:
                d.add("11", path, f"filed in raw/{shard}/ but named {name[:4]}",
                      "§3: a file's shard is its own prefix — move it, and check what re-dated it")


def check_linklists(rows, d):
    for r in rows:
        for w in r["d"].get("fm_warnings", []):
            if w.startswith("link-list-nonstandard"):
                d.add("12", r["path"], f"non-canonical link list in `{w.split(':')[1]}:`",
                      "§1: write [[a], [b]] — one bracket layer per item")
            elif w.startswith("list-unclosed"):
                d.add("12", r["path"], f"`{w.split(':')[1]}:` opens a list and never closes it",
                      "quote the value, or close the bracket")
            elif w.startswith("duplicate-key"):
                d.add("1", r["path"], f"duplicate key `{w.split(':')[1]}`",
                      "two values for one key; the later one wins silently")
            elif w == "no-frontmatter":
                d.add("1", r["path"], "no frontmatter block")
            elif w == "frontmatter-unclosed":
                # 2026-08-09: vault_lib has always emitted this and #1 never mapped it, so two
                # admitted sources with no closing `---` passed a clean lint. Every field is
                # invisible to any reader that stops at the delimiter.
                d.add("1", r["path"], "frontmatter opens and never closes",
                      "add the closing `---`; until then no field on this page is readable")
            elif w == "frontmatter-fence-glued":
                d.add("1", r["path"], "closing `---` has body text glued to it",
                      "put the body text on its own line below the fence")
            elif w.startswith("unparsed-line"):
                d.add("1", r["path"], f"unreadable frontmatter line: {w.split(':', 1)[1]}")
            elif w.startswith("yaml-unparseable"):
                # 2026-09-20 (job 95): `unreadable frontmatter line` above is this file's
                # own tolerant reader complaining, and it caught 19 records while an actual
                # YAML parse failed on 371. raw/ is what CORPUS reads, so an unparseable
                # record is invisible to the consumer, not merely untidy.
                d.add("1", r["path"], f"frontmatter fails a YAML parse: {w.split(':', 1)[1]}",
                      "quote the scalar; a value that already fails to parse cannot change "
                      "meaning by being quoted (scripts/repair-frontmatter-quoting.py)")


def check_completeness(rows, d):
    for r in rows:
        fm, path = r["fm"], r["path"]
        if fm.get("type") != "source":
            continue
        bc = fm.get("body_completeness")
        if not bc:
            d.add("15", path, "no `body_completeness`",
                  "missing means unverified — establish it from the stored body, never assume `full`")
        elif bc == "full" and r["d"].get("trunc_markers"):
            d.add("15", path, "`full`, but the body carries a "
                               f"{'/'.join(r['d']['trunc_markers'])} marker",
                  "the dedup tiebreak and the paywall gate both trust this field")


def check_region_place(rows, d):
    """#23 — a source bearing on three or more countries of one region, carrying no region code.

    **Soft by design, and the design is the point.** The high-precision half of the rule is
    mechanical (three or more of a region's countries, no `X__` anywhere), but the half that
    decides is not: a cross-border framework spanning three states earns the code and one
    operator's presence in three markets does not, and only the body tells you which. So this
    surfaces a candidate and a person rules — the same division as #6 and #7.

    The converse is deliberately **not** checked. A national development that names a regional
    programme is correctly national (`facets.md` §1 -> PLACE), and a check that flagged those
    would ask for exactly the over-tagging the rule forbids."""
    parent = {}
    with open(COUNTRIES, encoding="utf-8-sig", newline="") as fh:
        for row in csv.reader(fh):
            if row and len(row) > 2 and row[0].strip().lower() != "iso-3":
                parent[row[0].strip()] = row[2].strip()
    kids = defaultdict(set)
    for code, up in parent.items():
        if code and not code.startswith("X") and up:
            kids[up].add(code)
    for r in rows:
        fm, path = r["fm"], r["path"]
        if fm.get("type") != "source":
            continue
        pl = [str(p).strip() for p in V.as_list(fm.get("places"))]
        if any(p.startswith("X") for p in pl):
            continue
        for region, members in sorted(kids.items()):
            hit = set(pl) & members
            if len(hit) >= 3:
                d.add("23", path, f"{len(hit)} {region} countries and no region code",
                      f"§1 PLACE: `{region}` if the development is regional; leave it if these are "
                      f"national facts reported together", soft=True)


NOTE_RE = re.compile(r"^(x?)(\d+[a-z]?)\.\s")


def read_notes():
    """[(number, struck, band, words, first_line)] for every entry in post-run-notes.md.

    An entry runs from its numbered line to the next numbered line or heading — the
    file's own convention (`## NEXT NOTE NUMBER`, `## Open`, `## Done`)."""
    if not os.path.exists(NOTES):
        return []
    lines = open(NOTES, encoding="utf-8", newline="").read().splitlines()
    starts = [i for i, ln in enumerate(lines) if NOTE_RE.match(ln)]
    out = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        body = []
        for ln in lines[i:end]:
            if ln.startswith("#") and ln is not lines[i]:
                break
            body.append(ln)
        text = " ".join(body)
        m = NOTE_RE.match(lines[i])
        band = next((b for b in ("[CRITICAL]", "[ACT]", "[DECIDE]", "[FETCH]", "[FYI]")
                     if b in text), "")
        out.append({"n": m.group(2), "struck": bool(m.group(1)), "band": band,
                    "words": len(text.split()), "line": i + 1})
    return out


def check_note_caps(d):
    """#24 — the two caps on `reviews/post-run-notes.md`, and the one band it takes.

    Written as prose on 2026-08-03 and broken by 2026-08-10 on every clause: five open
    notes ran 150–300+ words against a stated 60, and the file carried `[FYI]` entries
    that have nothing for Bill to rule on. Lint's disposition is to **truncate** an
    over-length note to its first sentence and move an off-band one to its own channel.

    **The band it takes is `[CRITICAL]`, from 2026-08-22 (note 34).** `CLAUDE.md` →
    *Reporting* retired `[DECIDE]` into `[ACT]` on the reversibility test — a ruling only
    Bill can give is very nearly the empty set — so a `[DECIDE]` note is now a decision CC
    owes itself, not an entry for this file. `[FETCH]` was never a band but a destination."""
    notes = read_notes()
    open_notes = [n for n in notes if not n["struck"]]
    for n in open_notes:
        if n["words"] > NOTE_WORD_CAP:
            d.add("24", f"reviews/post-run-notes.md:{n['line']}",
                  f"note {n['n']} runs {n['words']} words",
                  f"cap is {NOTE_WORD_CAP} — truncate to the claim and the question; "
                  "the detail belongs in logs/log.md")
        if n["band"] and n["band"] != "[CRITICAL]":
            dest = {"[FETCH]": "X:\\fetch-list.md",
                    "[FYI]": "logs/log.md as one line"}.get(
                        n["band"], "act on it now and log the decision")
            d.add("24", f"reviews/post-run-notes.md:{n['line']}",
                  f"note {n['n']} is banded {n['band']}",
                  f"only [CRITICAL] enters this file — {dest}")
    if len(open_notes) > NOTE_OPEN_CAP:
        d.add("24", "reviews/post-run-notes.md",
              f"{len(open_notes)} open notes — cap is {NOTE_OPEN_CAP}",
              "at the cap CC takes the conservative option itself and logs it "
              "(CLAUDE.md → Act. Log after. Never ask.)")


def read_xchg_notes(path):
    """[(number, words, line, body)] for every open note in an exchange note file.

    A note runs from its numbered line to the next numbered line or the next `## ` heading.
    Closed notes are not here to be counted — both files carry unresolved notes only, and a
    resolved one moves out wholesale to its `-resolved.md` twin.

    **The house shape opens a note twice** — `### 29. [ACT] <title>` and then `**29** [ACT]
    (date) - <summary>` — and both lines match. Read as two notes, the heading half ends
    before the `Affects:` line and reports as carrying none, which is a false finding on
    every note either side has ever written in that shape. A repeat of the number just
    opened is the same note continuing, so it does not start one."""
    lines = open(path, encoding="utf-8", newline="").read().splitlines()
    starts = []
    for i, ln in enumerate(lines):
        m = XCHG_NOTE_RE.match(ln)
        if not m:
            continue
        num = m.group(1) or m.group(2)
        if starts and num == starts[-1][1]:
            continue
        starts.append((i, num))
    starts = [i for i, _num in starts]
    out = []
    for k, i in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        body = [lines[i]]
        for ln in lines[i + 1:end]:
            if ln.startswith("## "):
                break
            body.append(ln)
        m = XCHG_NOTE_RE.match(lines[i])
        joined = "\n".join(body)
        out.append(((m.group(1) or m.group(2)), len(joined.split()), i + 1, joined))
    return out


def check_xchg_note_caps(d):
    """#24's second half — the 60-word cap over `notes-for-osint.md` and `notes-for-corpus.md`.

    **Soft, and never listed in full.** Both files are written from both sides, so an
    over-length note is as often CORPUS's message as OSINT's, and OSINT trimming the other
    side's words is not a fix available to it. What the finding is for is the writer's next
    note: the decision and the work, not the argument behind it, which belongs in the repo
    that owns it."""
    for name in XCHG_NOTES:
        path = os.path.join(XCHG, name)
        if not os.path.exists(path):
            continue
        try:
            over = [n for n in read_xchg_notes(path) if n[1] > NOTE_WORD_CAP]
        except OSError:
            continue                      # the share is not mounted; not a vault defect
        for num, words, line, _body in sorted(over, key=lambda n: -n[1])[:3]:
            d.add("24", f"{name}:{line}", f"note {num} runs {words} words",
                  f"cap is {NOTE_WORD_CAP} — the decision and the work; the reasoning goes "
                  f"in the repo that owns it", soft=True)
        if len(over) > 3:
            d.add("24", name, f"and {len(over) - 3} more notes over {NOTE_WORD_CAP} words",
                  "same disposition", soft=True)




def check_xchg_affects(d):
    r"""#24's fourth part - every open note names the output it bears on.

    `X:\README.md` -> *Conventions* is where the rule lives; this only counts it, and it
    counts the three things a check honestly can: **the line is there**, it does not say
    *nothing*, and it names something a reader can go to - a path or an artefact in code
    font, work already commissioned cited by number, or a published thing named in words
    against a short vocabulary. Whether the line is **true** is not a lint's to say, and a
    check built to try would either pass everything or argue with its own writer.

    **Hard on `notes-for-corpus.md`, which is OSINT's outbox, and soft on the inbox.** The
    rule does its work before a note is written, and the writer is the only one who can
    apply it; failing on the other side's note would be failing on work this run may not
    edit. CORPUS asserts the mirror of this from `scripts/lint-notes.py`."""
    for name, soft in ((XCHG_OUTBOX, False), (XCHG_INBOX, True)):
        path = os.path.join(XCHG, name)
        if not os.path.exists(path):
            continue
        try:
            notes = read_xchg_notes(path)
        except OSError:
            continue                      # the share is not mounted; not a vault defect
        for num, _words, line, body in notes:
            m = XCHG_AFFECTS_RE.search(body)
            if not m:
                d.add("24", f"{name}:{line}", f"note {num} carries no `Affects:` line",
                      "README.md -> Conventions: a note names the output it bears on, or it "
                      "is not sent", soft=soft)
                continue
            said = m.group(1).strip().strip("*_` .")
            if said.lower() in XCHG_AFFECTS_EMPTY:
                d.add("24", f"{name}:{line}",
                      f"note {num}'s `Affects:` line says '{said}'",
                      "a note whose Affects line would have to say nothing is not a note",
                      soft=soft)
            elif not XCHG_AFFECTS_NAMES.search(said):
                d.add("24", f"{name}:{line}",
                      f"note {num}'s `Affects:` line names nothing a reader can go to",
                      "an artefact - a path, a named page, the script that produces one - "
                      "or work already commissioned, cited by number", soft=soft)


def xchg_fold(text):
    """Lowercase, unwrap and strip emphasis, so a rule copied and rewrapped still matches.

    Hard wrapping is the reason this exists: a convention copied into another file and then
    reflowed is the same rule in two places, and a line-by-line comparison would miss it."""
    t = text.lower()
    for a, b in (("—", "-"), ("–", "-"), ("’", "'"), ("‘", "'"),
                 ("“", '"'), ("”", '"'), (" ", " ")):
        t = t.replace(a, b)
    t = re.sub(r"[*_`]", "", t)
    return re.sub(r"\s+", " ", t)


def xchg_preamble(text, boundary):
    """The words above a file's own substance. Frontmatter is not preamble."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i, ln in enumerate(lines[1:], 1):
            if ln.strip() == "---":
                lines = lines[i + 1:]
                break
    head = []
    for ln in lines:
        if ln.startswith(boundary):
            break
        head.append(ln)
    return len(" ".join(head).split())


def check_xchg_preambles(d):
    """#24's third part - the share's preamble cap and its one-statement rule.

    Both halves are asserted from CORPUS too, by `scripts/lint-preambles.py`; each side
    measures its own files hard and the other side's soft, so the measurement exists whichever
    session is open and neither side is asked to edit work it does not own."""
    try:
        home = xchg_fold(open(os.path.join(XCHG, XCHG_README), encoding="utf-8").read())
    except OSError:
        return                          # the share is not mounted; not a vault defect
    for rule in XCHG_RULES:
        if rule not in home:
            d.add("24", XCHG_README, "README no longer states a convention this check watches",
                  f"“{rule}” - restore it or retire the fingerprint; a check that "
                  "disarms itself by losing its own reference is not a check")
    for name, (boundary, soft) in XCHG_PREAMBLES.items():
        try:
            text = open(os.path.join(XCHG, name), encoding="utf-8", newline="").read()
        except OSError:
            continue
        words = xchg_preamble(text, boundary)
        if words > XCHG_PREAMBLE_CAP:
            d.add("24", name, f"preamble runs {words} words to `{boundary}`",
                  f"cap is {XCHG_PREAMBLE_CAP} - a pointer to README.md -> Conventions and the "
                  "file's own content, nothing else", soft=soft)
        body = xchg_fold(text)
        for rule in XCHG_RULES:
            if rule in body:
                d.add("24", name, "restates a share convention",
                      f"“{rule}” - it lives in README.md -> Conventions; a rule "
                      "stated twice is a rule that will disagree with itself", soft=soft)


CLAUDE_MD_CAP = 123
# A standing rule with an end date is the one kind that can rot quietly: nothing fails when it
# lapses, it simply stops being true while still being read. So the date is asserted.
FREEZE_RE = re.compile(r"frozen until (\d{4}-\d{2}-\d{2})")


def check_proc_length(d, today=None):
    """#25 - `CLAUDE.md` -> *Keeping this file short*, and only that file.

    Until 2026-08-20 this ratcheted a line cap over every root procedure file, from
    `lookups/procedure-caps.csv` (token review task 16, 2026-08-10). That was a
    token-cost measure, and the cost premise is gone: note 26 records nights running
    at roughly a tenth of the former spend. What it left behind was nine standing
    findings of 1-10 lines each, none ever actioned, and five capped files that no
    longer existed - a check firing often enough to be skimmed, which is the failure
    a check exists to prevent. Retired to the one file whose shortness is a stated
    principle rather than a budget: `CLAUDE.md` says of itself that it grew
    unmanageable by accreting a clause per edge case, and that is worth measuring.
    `SWEEP-CYCLE.md` was the case that made the point - it orchestrates, so its
    length tracks how much it coordinates, not how many rules it has accreted.
    """
    f = "CLAUDE.md"
    path = os.path.join(V.ROOT, f)
    if not os.path.exists(path):
        return
    text = open(path, encoding="utf-8", errors="replace").read()
    n = len(text.splitlines())
    if n > CLAUDE_MD_CAP:
        d.add("25", f, f"{n} lines against a cap of {CLAUDE_MD_CAP}",
              "no new rule without deleting one - cut one, or make the case and "
              "raise CLAUDE_MD_CAP in this script")
    m = FREEZE_RE.search(text)
    if m and today and m.group(1) < today.isoformat():
        d.add("25", f, f"the freeze ran out on {m.group(1)}",
              "renew the paragraph with a new date or delete it - a standing rule past "
              "its own end date is read as live and is not")


DEAL_FIELDS = {"Instrument": "instrument", "Status": "status",
               "Beneficiary type": "beneficiary_type"}


def check_deal_vocab(rows, d):
    """#28 — the three controlled fields of a `## Deal record`, per DEAL-VOCAB.md.

    Without this the vocabulary is true only until the next record is written: the
    backswing normalised 1,260 records and nothing else reads these three fields.
    """
    vocab = defaultdict(set)
    path = os.path.join(V.ROOT, "lookups", "deal-vocabs.csv")
    for row in csv.DictReader(open(path, encoding="utf-8")):
        vocab[row["field"]].add(row["value"])
    for r in rows:
        if not r["fm"].get("finance_origin"):
            continue
        try:
            text = open(os.path.join(V.ROOT, r["path"]), encoding="utf-8").read()
        except OSError:
            continue
        if "## Deal record" not in text:
            continue
        for label, field in DEAL_FIELDS.items():
            m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|(.*?)\|[ \t]*$", text, re.M)
            if m is None:
                d.add("28", r["path"], f"deal record holds no `{label}` row",
                      "DEAL-VOCAB.md → never leave one blank; `Unknown` is the value for "
                      "a source that does not state it")
            elif m.group(1).strip() not in vocab[field]:
                d.add("28", r["path"], f"{label} `{m.group(1).strip()}` is not a "
                      f"`{field}` value in lookups/deal-vocabs.csv",
                      "map the wording in the field's map file, or rule it a new "
                      "vocabulary value; the extra wording belongs in ## Notes")


def check_entity_referents(rows, d):
    """#36 - a frontmatter `entities:` slug on a wiki page that no source in `raw/` tags.

    The entity vocabulary is what `raw/` is greppable *by* (`CLAUDE.md` -> *Entities*:
    entity pages were retired on the reasoning that "when an entity starts to matter, grep
    for it"). That only holds if the slug on the page is the slug in the sources, so a slug
    nobody's sources carry is a grep that returns nothing and reads as an absence of
    evidence. Housekeeping job 73 read the standing set of 129 once and ruled it; this check
    exists so the set cannot regrow silently. Slugs already ruled sit in
    `lookups/entity-slugs-ruled.csv` and are not reported again; a slug that later gains a
    source tag simply stops matching. Regrow protection - a near-miss typo splits an entity's record in
    two and no other check sees it. **Soft**: the legitimate case is a real actor named on a
    page that no source happens to tag, which the tagging rule allows.
    """
    ruled = set()
    rp = os.path.join(V.ROOT, "lookups", "entity-slugs-ruled.csv")
    if os.path.exists(rp):
        for row in csv.DictReader(open(rp, encoding="utf-8")):
            ruled.add(row["slug"].strip())
    tagged = set()
    for r in rows:
        if not r["path"].startswith("raw/"):
            continue
        for s in r["fm"].get("entities") or []:
            tagged.add(str(s).strip())
    for r in rows:
        if not r["path"].startswith("wiki/"):
            continue
        for s in r["fm"].get("entities") or []:
            s = str(s).strip()
            if s and s not in tagged and s not in ruled:
                d.add("36", r["path"], f"entity `{s}` is tagged by no source in raw/",
                      "a typo splits an entity's record; a stale registration belongs off "
                      "the page; a real actor no source tags is legitimate - job 73's ruling",
                      soft=True)


# --------------------------------------------------------------------------- #
# #34 catalogue hero — the subtitle every record carries into the public catalogue
#
# `catalogue_hero` is rendered under the title at corpus.data-landscapers.io/catalogue/,
# so unlike `hub_line` it has no editorial gate: a record with no hero is a catalogue row
# that says only its own name. The contract is `schemas.md` §4 and it runs from the date
# below; a source ingested before it is the backfill lane's work and is counted, never
# failed — the same partition `hub_line` needed when it was minted.
# --------------------------------------------------------------------------- #

HERO_CONTRACT = "2026-09-05"
MARKUP = re.compile(r"\[\[|\*\*|\]\(")


def hero_words(text, n):
    return re.findall(r"[a-z0-9]+", text.lower())[:n]


def check_catalogue_hero(rows, d):
    backlog = 0
    for r in rows:
        fm, path = r["fm"], r["path"]
        if fm.get("type") != "source" or not path.startswith("raw/"):
            continue
        hero = fm.get("catalogue_hero")
        hero = hero.strip() if isinstance(hero, str) else ""
        if not hero:
            # `ingested` is absent from the budget-archive companions, which are
            # pre-contract by construction; a missing date is never post-contract.
            if str(fm.get("ingested") or "") >= HERO_CONTRACT:
                d.add("34", path, "missing `catalogue_hero`",
                      "required on every source ingested from %s (schemas.md §4)"
                      % HERO_CONTRACT)
            else:
                backlog += 1
            continue
        # The 120-character cap is #1's, read off the schema's `maxLength`, so a single
        # over-long hero is caught by the mechanical pass whether or not #34 runs.
        if "\n" in hero:
            d.add("34", path, "`catalogue_hero` runs to more than one line",
                  "it is a subtitle; the catalogue lays it out on one")
        if hero.endswith("."):
            d.add("34", path, "`catalogue_hero` ends in a full stop",
                  "terse grammar: internal punctuation yes, terminal full stop no")
        if MARKUP.search(hero):
            d.add("34", path, "`catalogue_hero` carries markdown",
                  "plain text only — it is rendered as a subtitle outside this vault")
        title = str(fm.get("title") or "").strip()
        if title:
            a, b = hero.lower(), title.lower()
            # Same test as catalogue-hero-set.py: a short title inside a hero is named, not
            # restated, so containment counts from three words (R74).
            if a == b or a in b or (b in a and len(b.split()) >= 3):
                d.add("34", path, "`catalogue_hero` repeats the title",
                      "the hero says what the reader gets by opening the record, "
                      "not what it is called")
            elif len(hero_words(hero, 4)) == 4 and \
                    hero_words(hero, 4) == hero_words(title, 4):
                d.add("34", path, "`catalogue_hero` opens on the title's own first "
                      "four words", "complement the title, do not restate it",
                      soft=True)
    if backlog:
        d.add("34", "raw/", "%d pre-contract source(s) carry no `catalogue_hero`"
              % backlog, "the backfill lane — counted, never a defect", soft=True)


# --------------------------------------------------------------------------- #
# #38 — a de-accented Romance title
#
# A staging lane transliterated Portuguese and French `title:` values to ASCII while
# the bodies beside them stayed correct UTF-8 (housekeeping job 81, 2026-08-27): `Lei
# n.o 11/02`, `Politica de Seguranca Cibernetica`, `Instrucao 003-03-2025`. `title:` is
# evidence (`reference.md` §4), so a flattened one is never reconstructed by inference —
# it is refetched from the source's own heading, and this check is what finds the next
# batch before a citation is built on it.
#
# **The test is a flattened spelling, not the absence of an accent.** "No accented
# character" alone over-reported by roughly a quarter of what it matched — 9 of 38
# records simply had titles whose Portuguese takes none (`Governo aprova proposta de Lei
# de Terras`). So a title is flagged only when it carries no accented character AND a
# word that is not spelled that way in either language: a `-cao`/`-coes` ending (ção /
# ções), `n.o` for nº, or one of the stems below. That is the same signature job 110's
# body measurement found, where intact text runs 29–34 accented characters per 1,000 and
# flattened text runs 0.0–0.3, with no population in between.
#
# **Two records are exempt and always will be**, because their own sources cannot state
# their titles: the Guinea-Bissau Boletim Oficial 24 scan, whose OCR layer renders its
# own masthead as `RIPUBTICADA GUNIüI§§ÀU`, and the CFE company-registry statistics page,
# whose domain `cfe.gw` is parked (no A record, Hostinger `dns-parking` SOA). Both were
# read against their sources on 2026-09-13 and left exactly as held. An exemption lives
# here rather than in the record because the record is evidence and this is lint's own
# bookkeeping.
# --------------------------------------------------------------------------- #

ACCENTED = re.compile(r"[À-ɏ]")
FLATTENED = re.compile(
    r"\b(?:\w+(?:cao|coes)|n\.o|politic[ao]s?|publico|publica|servicos?|seguranca|"
    r"tecnic[ao]s?|estatistic[ao]s?|relatorios?|anuario|codigo|numero|orcamento|"
    r"juridic[ao]s?|regiao|orgao|"
    r"donnees|numeriques?|arretes?|societe|ministere|annee|securite|identite)\b",
    re.IGNORECASE)
DEACCENT_CONTRACT = "2026-09-17"
DEACCENT_EXEMPT = {
    # cne.gw serves only the scan the record holds; its OCR masthead is unreadable.
    "2023-06-15-guine-bissau-boletim-oficial-24-mapa-oficial-legislativas-2023",
    # cfe.gw is a parked domain — nothing to refetch, not a transient outage.
    "2025-04-30-cfe-guine-bissau-estatisticas-registo-empresas",
    # The held PDFs' own all-caps headings print "L'ANNEE" unaccented; the title is
    # faithful to the source (checked against budget-archive/SEN/2024/, 2026-09-24).
    "2023-10-13-sen-plf-2024-companion",
    "2023-12-15-sen-lfi-2024-loi-2023-18-companion",
}


def check_deaccented_titles(rows, d):
    backlog = 0
    for r in rows:
        fm, path = r["fm"], r["path"]
        if fm.get("type") != "source" or not path.startswith("raw/"):
            continue
        title = str(fm.get("title") or "").strip()
        if not title or ACCENTED.search(title):
            continue
        hit = FLATTENED.search(title)
        if not hit:
            continue
        if os.path.splitext(os.path.basename(path))[0] in DEACCENT_EXEMPT:
            continue
        if str(fm.get("ingested") or "") < DEACCENT_CONTRACT:
            backlog += 1
            continue
        d.add("38", path, "`title:` reads as de-accented Portuguese or French "
              "(`%s`)" % hit.group(0),
              "refetch the accented form from the source's own heading and correct "
              "`title:` only — never spell it from your own Portuguese or French "
              "(job 81); a source that cannot state its own title is left as held and "
              "named in DEACCENT_EXEMPT here")
    if backlog:
        d.add("38", "raw/", "%d source(s) ingested before %s carry a de-accented "
              "title" % (backlog, DEACCENT_CONTRACT),
              "the standing backlog — counted, never a defect; job 81 repaired the "
              "batches it measured and a corpus-wide sweep is its own job",
              soft=True)


def check_unreadable_records(d):
    r"""A `raw/` record whose frontmatter block no parser in the vault can match.

    **This is the one defect shape nothing else is looking for.** Every frontmatter
    reader here matches `^---\r?\n`, so a record whose closing `---` carries a doubled
    CR, or has lost its newline entirely, reads as having *no frontmatter* rather than
    as malformed: not an orphan, not bad YAML, not a missing key. Lints and compiles
    that partition on the block skip it silently and report nothing. Three Somali
    records sat in that state until `catalogue-hero-set.py` refused one outright
    (housekeeping 118, found by the R31 hero sitting 2026-09-18).

    **Read as bytes, never as text**, because the defect IS the byte sequence: a reader
    that opens in text mode with universal newlines has already normalised it away,
    which is why every text-mode check in this file passes over it.

    The repair is a terminator fix and never a re-capture — it changes no character of
    anyone's words, which the job asserted by stripping every CR from both sides and
    comparing before writing.
    """
    root = os.path.join(V.ROOT, "raw") if hasattr(V, "ROOT") else "raw"
    block = re.compile(rb"^---\r?\n(.*?\r?\n)---\r?\n", re.S)
    doubled = 0
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, os.path.dirname(root)).replace(os.sep, "/")
            try:
                b = open(path, "rb").read()
            except OSError:
                continue
            if not block.match(b):
                d.add("40", rel,
                      "frontmatter block does not match the reader's own regex — every "
                      "parser in the vault reads this record as having no frontmatter",
                      "a terminator repair, not a re-capture: fix the bytes around the "
                      "`---` and leave the body's own words alone")
            elif b"\r\r\n" in b:
                doubled += 1
    if doubled:
        d.add("40", "raw/",
              "%d record(s) carry a doubled CR inside the body" % doubled,
              "cosmetic while the frontmatter still parses, but it is the same capture "
              "fault that made three records unreadable — one byte fix each, touching "
              "no word of the text",
              soft=True)


def check_drop_domains(rows, d):
    """A `raw/` record whose `url:` host sits on a domain adjudicated `drop`.

    The deterministic half of #6. `wiki/origin-screen.md` -> *After a promotion to
    `drop`* makes the promoting session hand every `raw/` hit to #6 in the same
    session, and four records survived three separate promotions because no script
    ever asked (housekeeping job 104). A retired record is still a finding until it
    leaves `raw/`, so the count is the enforcement.

    `origin_status: cleared` stamped before the promotion is the second half: a stamp
    that predates its own domain's adjudication says nothing and reads as if it did.
    """
    dropped = {}
    path = os.path.join(V.ROOT, "logs", "drop-list.csv") if hasattr(V, "ROOT") else "logs/drop-list.csv"
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if (row.get("status") or "").strip().lower() == "drop":
                    dom = (row.get("domain") or "").strip().lower().lstrip(".")
                    if dom:
                        dropped[dom] = (row.get("added") or "").strip()
    except OSError:
        return
    if not dropped:
        return
    for r in rows:
        fm, p = r["fm"], r["path"]
        if fm.get("type") != "source" or not p.startswith("raw/"):
            continue
        url = str(fm.get("url") or "")
        m = re.match(r'https?://([^/?#]+)', url, re.I)
        if not m:
            continue
        host = m.group(1).lower().split(":")[0]
        host = host[4:] if host.startswith("www.") else host
        hit = next((dom for dom in dropped
                    if host == dom or host.endswith("." + dom)), None)
        if not hit:
            continue
        added = dropped[hit]
        stamp = str(fm.get("origin_cleared") or fm.get("origin_held") or "")[:10]
        stale = " and still stamped `origin_status: cleared` (%s), which predates it" % stamp             if str(fm.get("origin_status") or "").strip() == "cleared" and stamp and added and stamp < added else ""
        d.add("6", p, "url sits on `%s`, adjudicated `drop` %s%s" % (hit, added or "(undated)", stale),
              "take the record's live claims, re-source them from an admissible origin or "
              "state the absence dated on the page that carries them, then retire the record "
              "and rewire its citations (`wiki/origin-screen.md` -> After a promotion to `drop`)")


def check_artefact_md5(d):
    """Two artefacts with one md5 and no documented reason (job 106).

    The index is read, never rebuilt: hashing 2,249 files takes minutes and lint runs
    nightly. `scripts/artefact-md5-index.py --append` keeps it current at ingest, and the
    count check below is what says whether it did — an index that has stopped being
    appended to is a check that has stopped looking, which is worse than no check.
    """
    import csv as _csv
    index = os.path.join(V.ROOT, "lookups", "artefact-md5-index.csv")
    allow = os.path.join(V.ROOT, "lookups", "artefact-md5-allowed.csv")
    if not os.path.isfile(index):
        d.add("39", "lookups/artefact-md5-index.csv", "the artefact md5 index is absent",
              "`python scripts/artefact-md5-index.py --rebuild`")
        return
    with open(index, encoding="utf-8-sig", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    ok = {}
    if os.path.isfile(allow):
        with open(allow, encoding="utf-8-sig", newline="") as fh:
            ok = {r["md5"]: r.get("reason", "") for r in _csv.DictReader(fh) if r.get("md5")}

    # Count the artefacts with the index's own walker rather than a second copy of it here:
    # two walkers that disagree about what an artefact is report a stale index every night
    # and there is nothing to fix.
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location(
        "artefact_md5_index", os.path.join(V.ROOT, "scripts", "artefact-md5-index.py"))
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    held = len(_mod.artefacts(V.ROOT))
    if held != len(rows):
        d.add("39", "lookups/artefact-md5-index.csv",
              "the index holds %d row(s) against %d artefact(s) held" % (len(rows), held),
              "an index that is not appended to at ingest stops seeing collisions — "
              "`python scripts/artefact-md5-index.py --rebuild`")

    by_hash = {}
    for r in rows:
        by_hash.setdefault(r["md5"], []).append(r)
    for digest, members in sorted(by_hash.items()):
        if len(members) < 2 or digest in ok:
            continue
        d.add("39", members[1]["artefact"],
              "byte-identical to %s" % members[0]["artefact"],
              "read both records: retire the lesser under `CLAUDE.md` -> *Duplicates*, "
              "or record the reason in lookups/artefact-md5-allowed.csv — a document "
              "served by two routes defeats both the title dedup and the URL index")


def check_stranded(d):
    new_dir = os.path.join(V.ROOT, "new")
    left = [f for f in os.listdir(new_dir) if not f.startswith(".")] \
        if os.path.isdir(new_dir) else []
    for f in left:
        d.add("10", "new/" + f, "left in new/ after an ingest",
              "lint does not ingest it — the count says the ingest did not complete")




# --------------------------------------------------------------------------- #
# #8 page bloat — over §8's classify line, by shape
# --------------------------------------------------------------------------- #

CLASSIFY_LINE = 2500          # operations.md §8: "stop and classify"
SMALL_SECTION = 400           # a section too short to be a theme
HUB_CHRONOLOGY = "Recent developments"   # compiled, not written — LINT.md #8 exempts it
RULED_HEADING = re.compile(r"^Length\s*[-\u2013\u2014]\s*reviewed\s*(\d{4}-\d{2}-\d{2})?")
SECTION_DATE = re.compile(r"(?:19|20)\d\d")
BLOAT_KINDS = ("concept", "place", "intersection")
# Page furniture: out of the word count and out of the shape test both, because
# it is neither synthesis nor chronology and a page cannot be trimmed by deleting
# its own links. `Reads`, `Record not held` and `Documents reached for` are NOT
# furniture — a dated statement of what is unestablished is a finding
# (`CLAUDE.md` -> *Currency*), so it counts as content and as a section.
FURNITURE = ("Links", "Sources", "Length", "Places", "Related")


def _shape(real, body_words):
    """§8's three flavours, as the ruling of housekeeping job 114 states them.

    `unsectioned` is not a flavour but a bar to diagnosing one: §8 asks which of
    three a page's length is, and the answer is invisible while the material is
    one block (job 115, mali--dpi-id). Section first, then classify.
    """
    if len(real) <= 1:
        return "unsectioned"
    biggest = max(n for _, n in real)
    if biggest > 0.6 * body_words:
        return "unsectioned"
    dated = sum(1 for h, _ in real if SECTION_DATE.search(h))
    small = sum(1 for _, n in real if n < SMALL_SECTION)
    if len(real) >= 6 and small >= 0.5 * len(real) and dated >= 0.4 * len(real):
        return "append-log"
    return "synthesis"


def measure_page(r):
    """#8's measure of one page, or None for a page #8 does not measure.

    Shared with `scripts/page-length.py`, which a Phase B slice runs on its landing
    page before and after a write (`WIKI-SYNC.md` → *A landing page over its line*),
    so the writer and the lint can never disagree about where the line is (R81).
    `over` is the gate: over the classify line and not under a current `Length`
    ruling — a ruled page's length was judged right, until an edit makes it stale.
    """
    dd = r["d"]
    if dd.get("kind") not in BLOAT_KINDS:
        return None
    secs = dd.get("sections") or []
    words = dd.get("words") or 0
    exempt = 0
    if dd.get("kind") == "place":
        exempt = sum(n for h, n in secs if h.startswith(HUB_CHRONOLOGY))
    furniture = sum(n for h, n in secs if h.startswith(FURNITURE))
    effective = words - exempt - furniture
    # The exempt block is out of the shape test as well as out of the count.
    # Leaving it in made every hub read `unsectioned`, since a compiled
    # chronology is by construction the largest section on its page.
    skip = FURNITURE + ((HUB_CHRONOLOGY,) if exempt else ())
    real = [(h, n) for h, n in secs if not any(h.startswith(s) for s in skip)]
    shape = _shape(real, effective) if real else "unsectioned"
    ruled = None
    for h, _ in secs:
        m = RULED_HEADING.match(h)
        if m:
            ruled = m.group(1) or "undated"
            break
    stale = bool(ruled and ruled != "undated"
                 and (r["fm"].get("last_reviewed") or "") > ruled)
    over_line = effective > CLASSIFY_LINE
    return {"words": words, "exempt": exempt, "furniture": furniture,
            "effective": effective, "real": real, "shape": shape, "ruled": ruled,
            "stale": stale, "over_line": over_line,
            "over": over_line and (not ruled or stale)}


def check_page_bloat(rows, d):
    """LINT.md #8, which was specified and never implemented.

    Every figure housekeeping job 87 carried — 199 pages on 2026-08-30, 295 on
    2026-09-05, 342 on 2026-09-16, 394 on 2026-09-17 — was measured ad hoc, which
    is why they disagree with each other and why **the hub exemption LINT.md
    already states had never once been applied**: `places/NGA.md` was counted at
    56,296 words when 51,668 of them are its compiled `## Recent developments`.

    Every finding here is SOFT by design. §8 is explicit that "word figures are
    diagnostic prompts, not hard caps", and a page over the line may correctly be
    left alone — so this reports where to look and never gates a pass.

    A page carrying a dated `## Length — reviewed` note has been ruled on, and is
    reported as ruled rather than as backlog. **The ruling goes stale when the
    page has been substantively edited since it was made** — `last_reviewed`
    newer than the note's own date — because a length judgment is made on the
    page that existed when it was made, and `tech.ai.md` has roughly doubled
    since its 2026-08-23 note.
    """
    for r in rows:
        m8 = measure_page(r)
        if not m8 or not m8["over_line"]:
            continue
        dd = r["d"]
        words, exempt, furniture, effective = (m8["words"], m8["exempt"],
                                               m8["furniture"], m8["effective"])
        real, shape, ruled = m8["real"], m8["shape"], m8["ruled"]
        biggest = max((n for _, n in real), default=effective)
        bigname = next((h for h, n in real if n == biggest), "(one block)")

        note = "{:,} words".format(effective)
        if exempt or furniture:
            parts = []
            if exempt:
                parts.append("the compiled `%s` block's {:,}".replace("%s", HUB_CHRONOLOGY).format(exempt))
            if furniture:
                parts.append("{:,} of links and sources".format(furniture))
            note = "{:,} words, of {:,} — {} exempt".format(
                effective, words, " and ".join(parts))
        note += "; {} {}section(s), largest {:,} — {}".format(
            len(real), "hand-written " if exempt else "", biggest, bigname[:60])

        if dd.get("kind") == "concept":
            note += " · concept-page heads are housekeeping jobs 97 and 99, not #8's to clear"
        if dd.get("kind") == "place":
            note += " · a hub is a derived view; only its hand-written sections are in scope"

        if ruled:
            stale = (ruled != "undated"
                     and (r["fm"].get("last_reviewed") or "") > ruled)
            if stale:
                d.add("8", r["path"],
                      "over §8's classify line; the `Length` ruling of %s predates the page's last substantive edit (%s)"
                      % (ruled, r["fm"].get("last_reviewed")),
                      note + " · %s — re-rule it" % shape, soft=True)
            else:
                d.add("8", r["path"],
                      "over §8's classify line, ruled %s" % ruled,
                      note + " · %s" % shape, soft=True)
        else:
            d.add("8", r["path"], "over §8's classify line, unruled — %s" % shape,
                  note, soft=True)

# --------------------------------------------------------------------------- #

TITLES = {"1": "schema integrity", "2": "vocabulary", "3": "freshness",
          "6": "`drop`-domain residue in raw/",
          "8": "page bloat (§8 classify line)",
          "4": "orphans & dead links", "10": "stranded queue items",
          "11": "filenames & shards", "12": "link-list convention",
          "15": "body_completeness", "23": "region place code",
          "24": "register caps", "25": "procedure length",
          "28": "deal-record vocabulary",
          "36": "entity slugs with no referent",
          "34": "catalogue hero",
          "38": "de-accented Romance titles",
          "39": "artefact md5 collisions",
          "40": "unreadable frontmatter block"}
ORDER = ["1", "40", "12", "2", "11", "4", "6", "15", "3", "8", "23", "10", "24", "25",
         "28", "34", "36", "38", "39"]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", help="print every defect in one check (LINT.md number)")
    ap.add_argument("--limit", type=int, default=25, help="lines per check (default 25)")
    ap.add_argument("--all", action="store_true",
                    help="with --check, include the soft findings too")
    ap.add_argument("--json", action="store_true", help="every defect, machine-readable")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD), for testing")
    a = ap.parse_args()

    import datetime
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()

    schema = load_schema()
    places, topics = load_vocab()
    all_rows = V.load_index()
    links = V.load_links(auto=False)
    rows = [r for r in all_rows if r["fm"]]

    d = Defects()
    check_schema(rows, schema, d)
    check_linklists(all_rows, d)
    check_vocabulary(rows, places, topics, d)
    check_filenames(rows, schema, d)
    check_links(all_rows, links, d)
    check_unreadable_records(d)
    check_drop_domains(rows, d)
    check_completeness(rows, d)
    check_freshness(rows, today, d)
    check_region_place(rows, d)
    check_stranded(d)
    check_note_caps(d)
    check_xchg_note_caps(d)
    check_xchg_preambles(d)
    check_xchg_affects(d)
    check_proc_length(d, today)
    check_deal_vocab(rows, d)
    check_entity_referents(rows, d)
    check_catalogue_hero(rows, d)
    check_deaccented_titles(rows, d)
    check_artefact_md5(d)
    check_page_bloat(all_rows, d)

    if a.json:
        json.dump(d.rows, sys.stdout, ensure_ascii=False, indent=1)
        return 1 if any(not r["soft"] for r in d.rows) else 0

    if a.check:
        # A check number nothing knows about selects nothing and would print a clean
        # "0 finding(s)" — a check that read nothing looking exactly like a check that
        # found nothing (2026-08-22, note 34). Refuse it instead.
        if a.check not in TITLES:
            print(f"lint: no check #{a.check} — known: {', '.join(sorted(TITLES, key=lambda k: int(k)))}",
                  file=sys.stderr)
            return 2
        rowset = d.of(a.check)
        if not a.all:
            rowset = [r for r in rowset if not r["soft"]]
        n_soft = len(d.of(a.check)) - len(rowset)
        print(f"#{a.check} {TITLES.get(a.check, '')} — {len(rowset)} finding(s)"
              + (f", {n_soft} soft hidden (--all)" if n_soft else "") + "\n")
        if a.check == "8" and rowset:
            # One number over three folders hides that they have three different
            # remedies, which is how this count came to be re-derived by hand four
            # times and ignored each time (housekeeping job 130).
            pop = defaultdict(Counter)
            for r in rowset:
                folder = r["path"].split("/")[1]
                state = ("ruled" if ", ruled" in r["defect"]
                         else "stale ruling" if "predates" in r["defect"]
                         else r["defect"].split("unruled — ")[-1])
                pop[folder][state] += 1
            for folder in ("concepts", "places", "intersections"):
                if folder in pop:
                    c = pop[folder]
                    print(f"  {folder:>14}: {sum(c.values()):>3} over the line  "
                          + ", ".join(f"{k} {v}" for k, v in c.most_common()))
            # The gate's count: over the line with no current ruling. It registers no job
            # (R66/R81) — the writer rewrites at the write — and goes on the manifest.
            gate = sum(1 for r in rowset if ", ruled" not in r["defect"])
            print(f"\n  pages_over_line={gate}  (unruled or stale ruling; the manifest's count, "
                  f"expected near zero)")
            print()
        for r in rowset[:a.limit]:
            flag = " (soft)" if r["soft"] else ""
            print(f"  {r['path']}\n      {r['defect']}{flag}"
                  + (f"\n      {r['detail']}" if r['detail'] else ""))
        if len(rowset) > a.limit:
            print(f"\n  … {len(rowset) - a.limit} more (--limit {len(rowset)} for all)")
        return 1 if any(not r["soft"] for r in rowset) else 0

    hard = Counter(r["check"] for r in d.rows if not r["soft"])
    soft = Counter(r["check"] for r in d.rows if r["soft"])
    print(f"lint-deterministic over {len(rows):,} artefacts "
          f"({len(links):,} links)\n")
    print(f"  {'#':>3}  {'hard':>5} {'soft':>5}  check")
    for c in ORDER:
        print(f"  {c:>3}  {hard.get(c, 0):>5} {soft.get(c, 0):>5}  {TITLES[c]}")
    total = sum(hard.values())
    print(f"\n  {total} hard finding(s), {sum(soft.values())} soft. "
          f"--check N for the list.")
    print("  Reports only — the fixes are lint's to make, and the judgment checks "
          "(#6, #7, #9, #3's figures) stay with the model.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
