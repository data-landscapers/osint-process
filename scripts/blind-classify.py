#!/usr/bin/env python3
r"""
blind-classify.py — sample a night's admissions for a blind second reading of place and subject, and score it.

**Why it exists** *(strategic review 8 R189, 2026-11-26)*. Nothing measured how often ingest's place and subject calls would be made the same way twice. A fresh sub-agent that sees only a record's body, and the two vocabularies, classifies thirty of a night's admissions; its answers are scored against the filed frontmatter. A month gives about 900 judged records and the facet that disagrees most. The driver is `wiki/blind-classify.md`.

**The sample.** Records whose `ingested:` is the night or the day after (a night runs past midnight), excluding finance and budget records, which a loader classifies, not a reader. Random, seeded by the night, so a rerun picks the same thirty.

**The worksheet** is a folder the caller names: `NN.md`, each record's body with its frontmatter removed, and `key.json`, which maps NN to the record. The sub-agent is given the `NN.md` files and the vocabularies, never `key.json` or `raw/`, and writes `answers.csv`: `n,places,primary_subject`, places `;`-separated ISO-3 or region codes.

**The score.** Place agrees when the two code sets are equal. Subject agrees when the blind primary subject is the filed one: `primary_subject:`, or else the first non-`finance.*` slug in `topics:` (`wiki/facets.md`). One row a record to `logs/blind-classify.csv`, tracked and append-only; `cycle-manifest.py` reads the night's rows as its `classify` block.

Usage:
  python scripts/blind-classify.py --pick 30 --night 2026-11-26 --out <scratch dir>
  python scripts/blind-classify.py --score <scratch dir>
  python scripts/blind-classify.py --status          nights logged, agreement by facet
"""
import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vault_lib as V                                                # noqa: E402

LOG = os.path.join(V.ROOT, "logs", "blind-classify.csv")
COLS = ["night", "file", "places_filed", "places_blind", "place_agree",
        "subject_filed", "subject_blind", "subject_agree"]
FM = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
MACHINE = re.compile(r"^(finance_origin|deal_id|retired_deal_id|budget_[a-z_]+):", re.M)


def field(fm, name):
    m = re.search(rf"^{name}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else ""


def codes(v):
    """`[KEN, XEA]` or `KEN; XEA` as a sorted list of codes."""
    return sorted({c for c in re.split(r"[\s,;\[\]'\"]+", v or "") if c})


def primary(fm):
    p = field(fm, "primary_subject").strip("'\"")
    if p:
        return p
    for t in re.split(r"[\s,\[\]'\"]+", field(fm, "topics")):     # in order: the order is load-bearing
        if t and not t.startswith("finance."):
            return t
    return ""


def admitted(night):
    nxt = (dt.date.fromisoformat(night) + dt.timedelta(days=1)).isoformat()
    out = []
    for root, _, files in os.walk(os.path.join(V.ROOT, "raw")):
        for f in files:
            if not f.endswith(".md"):
                continue
            path = os.path.join(root, f)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    head = fh.read(4000)
            except OSError:
                continue
            m = FM.match(head)
            if not m:
                continue
            fm = m.group(1)
            if field(fm, "ingested") in (night, nxt) and not MACHINE.search(fm):
                out.append(os.path.relpath(path, V.ROOT).replace(os.sep, "/"))
    return sorted(out)


def pick(n, night, out):
    pool = admitted(night)
    chosen = random.Random(night).sample(pool, min(n, len(pool)))
    os.makedirs(out, exist_ok=True)
    key = {}
    for i, rel in enumerate(chosen, 1):
        text = open(os.path.join(V.ROOT, rel), encoding="utf-8", errors="replace").read()
        m = FM.match(text)
        body = text[m.end():] if m else text
        name = f"{i:02d}.md"
        open(os.path.join(out, name), "w", encoding="utf-8").write(body)
        key[f"{i:02d}"] = rel
    json.dump({"night": night, "records": key}, open(os.path.join(out, "key.json"), "w", encoding="utf-8"), indent=1)
    print(f"blind-classify: {len(chosen)} of {len(pool)} admissions for {night} → {out}")
    return 0


def score(out):
    key = json.load(open(os.path.join(out, "key.json"), encoding="utf-8"))
    night, recs = key["night"], key["records"]
    answers = {}
    with open(os.path.join(out, "answers.csv"), encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            answers[str(r.get("n", "")).strip().zfill(2)] = r
    rows = []
    for n, rel in recs.items():
        fm = FM.match(open(os.path.join(V.ROOT, rel), encoding="utf-8", errors="replace").read()).group(1)
        a = answers.get(n, {})
        pf, pb = codes(field(fm, "places")), codes(a.get("places", ""))
        sf, sb = primary(fm), (a.get("primary_subject") or "").strip()
        rows.append([night, rel, ";".join(pf), ";".join(pb), int(pf == pb), sf, sb, int(sf == sb)])
    new = not os.path.exists(LOG)
    with open(LOG, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(COLS)
        w.writerows(rows)
    n = len(rows)
    pa, sa = sum(r[4] for r in rows), sum(r[7] for r in rows)
    print(f"blind-classify: {night} · {n} records · place {pa}/{n} · subject {sa}/{n}")
    return 0


def night_block(night):
    """The manifest's `classify` block for one night, or None where none was scored."""
    try:
        with open(LOG, encoding="utf-8", newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r["night"] == night]
    except OSError:
        return None
    if not rows:
        return None
    n = len(rows)
    return {"records": n,
            "place_agree": round(sum(int(r["place_agree"]) for r in rows) / n, 3),
            "subject_agree": round(sum(int(r["subject_agree"]) for r in rows) / n, 3)}


def status():
    try:
        with open(LOG, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError:
        rows = []
    nights = sorted({r["night"] for r in rows})
    n = len(rows) or 1
    pa = sum(int(r["place_agree"]) for r in rows) / n
    sa = sum(int(r["subject_agree"]) for r in rows) / n
    print(f"blind-classify: {len(nights)} nights · {len(rows)} records · place {pa:.0%} · subject {sa:.0%}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--pick", type=int, metavar="N")
    ap.add_argument("--night", metavar="YYYY-MM-DD")
    ap.add_argument("--out", metavar="DIR", help="the worksheet folder, in the session scratchpad")
    ap.add_argument("--score", metavar="DIR", help="score DIR/answers.csv against DIR/key.json")
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if a.pick:
        if not (a.night and a.out):
            ap.error("--pick needs --night and --out")
        return pick(a.pick, a.night, a.out)
    if a.score:
        return score(a.score)
    if a.status:
        return status()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
