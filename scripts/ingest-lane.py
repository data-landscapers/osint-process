#!/usr/bin/env python3
r"""
ingest-lane.py — which ingest lane each candidate in `new/` takes.

`INGEST.md` -> *Two lanes*. Ingest prices every item as unscreened news — a per-item origin
adjudication, a tier-3 dedup judgment, an authored `hub_line`. Backfill arrives already
screened: `STATUS-ACQUIRE.md` screens the origins of the rows it fetches, and a
progress-filler batch is staged by CORPUS against this vault's own origin screen. Paying the
news price on it buys nothing, so the backfill lane skips those three steps.

The lane is read off `sweep_batch:` and is a **whitelist**: a batch prefixed
`status-acquire-` or `progress-filler-` is backfill, and everything else — including an item
carrying no `sweep_batch:` at all — is news. A new producer therefore costs a full-price run
rather than a silent skip.

A file that is not a `.md` candidate is an artefact riding with its companion page; it is
counted and listed apart, and takes whatever lane the companion takes.

This script assigns a lane; it does not decide whether the run may use it. Only
`update wiki backfill` opens the backfill lane — under any other trigger every item takes
the news lane whatever it carries.

Usage:
  python scripts/ingest-lane.py                 the partition, with counts
  python scripts/ingest-lane.py --lane backfill just those paths, one per line, for slicing
  python scripts/ingest-lane.py --lane news     likewise
  python scripts/ingest-lane.py --dir new       a different queue
  python scripts/ingest-lane.py --json          machine-readable

Exit 0 always. A partition is a reading, not a check.
"""
import argparse
import json
import pathlib
import sys

BACKFILL_PREFIXES = ("status-acquire-", "progress-filler-")


def sweep_batch(path):
    """The `sweep_batch:` value from the file's frontmatter, or '' if it carries none."""
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            if fh.readline().strip() != "---":
                return ""
            for line in fh:
                stripped = line.strip()
                if stripped == "---":
                    return ""
                if stripped.startswith("sweep_batch:"):
                    return stripped.split(":", 1)[1].strip().strip("\"'")
    except OSError:
        return ""
    return ""


def partition(root):
    backfill, news, artefacts = [], [], []
    for path in sorted(p for p in root.rglob("*")
                       if p.is_file() and not p.name.startswith(".")):
        rel = path.relative_to(root).as_posix()
        if path.suffix.lower() != ".md":
            artefacts.append(rel)
            continue
        batch = sweep_batch(path)
        row = (rel, batch)
        if batch.startswith(BACKFILL_PREFIXES):
            backfill.append(row)
        else:
            news.append(row)
    return backfill, news, artefacts


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dir", default="new", help="the queue to partition (default: new)")
    ap.add_argument("--lane", choices=("backfill", "news"),
                    help="print only that lane's paths, one per line")
    ap.add_argument("--json", action="store_true", help="machine-readable")
    args = ap.parse_args()

    root = pathlib.Path(args.dir)
    if not root.is_dir():
        print(f"no such queue: {root}", file=sys.stderr)
        return 0

    backfill, news, artefacts = partition(root)

    if args.lane:
        for rel, _ in (backfill if args.lane == "backfill" else news):
            print(rel)
        return 0

    if args.json:
        print(json.dumps({
            "dir": root.as_posix(),
            "backfill": [{"file": r, "sweep_batch": b} for r, b in backfill],
            "news": [{"file": r, "sweep_batch": b} for r, b in news],
            "artefacts": artefacts,
        }, indent=2))
        return 0

    print(f"{root.as_posix()}: {len(backfill)} backfill, {len(news)} news, "
          f"{len(artefacts)} artefacts")
    for label, rows in (("backfill", backfill), ("news", news)):
        if not rows:
            continue
        batches = {}
        for _, batch in rows:
            batches[batch or "(no sweep_batch)"] = batches.get(batch or "(no sweep_batch)", 0) + 1
        print(f"\n{label} - {len(rows)}")
        for batch, count in sorted(batches.items()):
            print(f"  {count:>4}  {batch}")
    if artefacts:
        print(f"\nartefacts - {len(artefacts)}, each taking its companion page's lane")
    return 0


if __name__ == "__main__":
    sys.exit(main())
