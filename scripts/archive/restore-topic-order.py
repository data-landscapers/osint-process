#!/usr/bin/env python3
"""
restore-topic-order.py  —  one-off repair.

`consolidate-budget-lines.py` wrote `topics: [{", ".join(sorted(set(...)))}]`, so
every consolidated domestic-state record came out alphabetised. The first
non-`finance.*` slug is the record's primary subject (reference.md -> Facets), so
alphabetising silently re-filed lines: SA Connect moved from `infra.connect` to
`digital.rural`, and ZAF's aggregate reported Connectivity at US$1m.

This recovers the original order from the pre-consolidation records in git
(81e2337c^) and rewrites `topics:` in place. Topics present now but not in the
recovered order are appended, so the tag set is never changed — only its order.

    python scripts/restore-topic-order.py            # dry-run
    python scripts/restore-topic-order.py --apply
"""
import os, re, sys, subprocess, collections

# scripts/ is the parent now — this file moved to scripts/archive/ on 2026-08-03
# (review task 25). Spent, but still importable, which is the point of archiving
# rather than deleting.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from finance_lib import raw_sources   # noqa: E402

PRE = "81e2337c^"                      # last commit before the consolidation
STAGES = ("proposed", "appropriated", "revised", "released", "actual", "audited", "unclear")


def split_front(text):
    m = re.match(r'^---\r?\n(.*?)\r?\n---\r?\n?(.*)$', text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def fm_get(fm, key, default=""):
    m = re.search(r'^' + re.escape(key) + r':[ \t]*(.*)$', fm, re.M)
    return m.group(1).strip().strip('"') if m else default


def topics_of(fm):
    m = re.search(r'^topics:\s*\[([^\]]*)\]', fm, re.M)
    return [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []


def norm_key(deal_id):
    """Old per-stage deal_id -> the consolidated stem: drop the stage suffix and
    collapse the two-part year form (zaf-2024-25-…, civ-2024-2025-…) to the bare
    start year."""
    d = deal_id.strip().lower()
    for s in STAGES:
        if d.endswith("-" + s):
            d = d[: -len(s) - 1]
            break
    d = re.sub(r'-(\d{4})-\d{2}(?=-|$)', r'-\1', d)
    d = re.sub(r'-(\d{4})-\d{4}(?=-|$)', r'-\1', d)
    return d


def read_pre():
    """deal_id stem -> topics in first-seen order, oldest record first."""
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", PRE, "raw/"],
                           capture_output=True, text=True, check=True).stdout.split("\n")
    names = [n for n in names if n.endswith(".md")]
    order = collections.defaultdict(list)
    seen = collections.defaultdict(set)
    blobs = subprocess.run(["git", "cat-file", "--batch"],
                           input="".join(f"{PRE}:{n}\n" for n in names).encode(),
                           capture_output=True).stdout          # BYTES: sizes are byte counts
    # walk the batch output: "<sha> blob <size>\n<contents>\n"
    pos, idx = 0, 0
    while pos < len(blobs) and idx < len(names):
        nl = blobs.find(b"\n", pos)
        if nl < 0:
            break
        hdr = blobs[pos:nl].split()
        if len(hdr) != 3:
            break
        size = int(hdr[2])
        body = blobs[nl + 1: nl + 1 + size].decode("utf-8", "replace")
        pos = nl + 1 + size + 1
        idx += 1
        if "finance_origin: domestic-state" not in body:
            continue
        fm, _ = split_front(body)
        did = fm_get(fm, "deal_id")
        if not did:
            continue
        k = norm_key(did)
        for t in topics_of(fm):
            if t not in seen[k]:
                seen[k].add(t)
                order[k].append(t)
    return order


def main():
    apply = "--apply" in sys.argv
    pre = read_pre()
    print(f"recovered topic order for {len(pre)} pre-consolidation line-year stems\n")
    changed = resub = unmatched = 0
    for fn, p in raw_sources("raw"):
        with open(p, encoding="utf-8", newline="") as f:
            text = f.read()
        if "finance_origin: domestic-state" not in text:
            continue
        fm, _ = split_front(text)
        cur = topics_of(fm)
        if len(cur) < 2:
            continue
        k = norm_key(fm_get(fm, "deal_id"))
        want = pre.get(k)
        if not want:
            unmatched += 1
            continue
        new = [t for t in want if t in cur] + [t for t in cur if t not in want]
        if new == cur:
            continue
        changed += 1
        old_primary = next((t for t in cur if not t.startswith("finance.")), "")
        new_primary = next((t for t in new if not t.startswith("finance.")), "")
        if old_primary != new_primary:
            resub += 1
            print(f"  SUBJECT {old_primary:20} -> {new_primary:20} {fn[:64]}")
        if apply:
            out = re.sub(r'^topics:\s*\[[^\]]*\]',
                         "topics: [" + ", ".join(new) + "]", text, count=1, flags=re.M)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(out)
    print(f"\n{changed} records reordered ({resub} change primary subject); "
          f"{unmatched} had no pre-consolidation match")
    print("APPLIED" if apply else "dry-run — rerun with --apply")


if __name__ == "__main__":
    main()
