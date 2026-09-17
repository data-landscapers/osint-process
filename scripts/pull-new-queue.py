#!/usr/bin/env python3
r"""
pull-new-queue.py — move CORPUS's finished batches from `X:\new-queue\` into `new/`, the sweep cycle's first act.

**Why it exists.** `X:\new-queue\` was a hand-carry: CORPUS staged, Bill moved the files into `OSINT\new\`, and a batch waited on his hands *(2026-08-20)*. Strategic review 4 retired that (ruling R8, register R09, 2026-09-17): the cycle pulls a batch itself, and ingest still decides admission — pulling is delivery, not endorsement.

**What it pulls.** Every top-level folder of `X:\new-queue\` that carries a `READY` file. CORPUS writes `READY` last, so a folder without one is a batch still being written and is left alone. A folder holding a `delivered-YYYY-MM-DD` marker and nothing else is a batch already pulled; loose files at the root of the queue are not batches and are left alone.

**Where it puts it.** Flat into `new/`, which is how every producer stages (`STATUS-ACQUIRE.md` → *Staging*): a filler batch's `baseline/` and `progress/` subfolders flatten with it. A name already in `new/` is not overwritten — the file stays in the queue, is named in the output, and the folder is not marked delivered, so the next night retries it. A byte-identical file already in `new/` is a previous interrupted pull: the queue's copy is removed and counted as delivered.

**The lane.** `scripts/ingest-lane.py` reads the lane off `sweep_batch:`. A `.md` candidate that carries no `sweep_batch:`, in a folder named with a backfill prefix (`status-acquire-`, `progress-filler-`), gets `sweep_batch: <folder>-<YYYY-MM-DD>` inserted as the first frontmatter key — the prefix from the folder name, exactly as the register line says. A candidate that already carries one keeps it, and a folder with any other name adds nothing, so its items take the news lane at full price: the whitelist's own default.

**Copy, verify, then delete.** `X:\` is another drive, so each file is copied, its bytes compared, and only then removed from the queue; an interrupted pull leaves duplicates the next run recognises, never a loss. The queue's deletions are CORPUS's to commit on the share (`X:\README.md` → *Conventions*); this script commits nothing.

Usage:
  python scripts/pull-new-queue.py            dry run: what would move
  python scripts/pull-new-queue.py --apply    move it

Prints one line per folder and a summary line. Exit 0 always: a queue that cannot be pulled tonight is pulled tomorrow, and never stops the cycle.
"""
import argparse
import datetime as dt
import os
import pathlib
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import util as _util                                   # noqa: E402

_spec = _util.spec_from_file_location("ingest_lane", os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingest-lane.py"))
_lane = _util.module_from_spec(_spec)
_spec.loader.exec_module(_lane)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = pathlib.Path(__file__).resolve().parent.parent
QUEUE = pathlib.Path("X:/new-queue")
NEW = REPO / "new"
READY = "READY"
MARKER = "delivered-"


def batches(queue):
    """(folder, reason) for every top-level folder; reason is None for one that is due."""
    out = []
    for d in sorted(p for p in queue.iterdir() if p.is_dir()):
        names = [p.name for p in d.iterdir()]
        if not (d / READY).is_file():
            delivered = names and all(n.startswith(MARKER) for n in names)
            out.append((d, "delivered" if delivered else "no READY"))
        else:
            out.append((d, None))
    return out


def with_batch(data, batch):
    """The file's bytes with `sweep_batch: <batch>` inserted if its frontmatter has none; None if unchanged."""
    text = data.decode("utf-8", errors="strict")
    nl = "\r\n" if "\r\n" in text.split("\n", 1)[0] + "\n" else "\n"
    lines = text.split(nl)
    if not lines or lines[0].strip() != "---":
        return None
    for ln in lines[1:]:
        if ln.strip() == "---":
            break
        if ln.strip().startswith("sweep_batch:"):
            return None
    else:
        return None
    lines.insert(1, f"sweep_batch: {batch}")
    return nl.join(lines).encode("utf-8")


def pull(folder, today, apply, new):
    backfill = folder.name.startswith(_lane.BACKFILL_PREFIXES)
    batch = folder.name if folder.name[-10:].count("-") == 2 and folder.name[-10:-6].isdigit() else f"{folder.name}-{today}"
    moved = tagged = 0
    blocked = []
    files = sorted(p for p in folder.rglob("*") if p.is_file() and p.name != READY and not p.name.startswith(MARKER))
    for src in files:
        dest = new / src.name
        data = src.read_bytes()
        if backfill and src.suffix.lower() == ".md":
            try:
                changed = with_batch(data, batch)
            except UnicodeDecodeError:
                changed = None
            if changed is not None:
                data = changed
                tagged += 1
        if dest.exists():
            if dest.read_bytes() == data:
                if apply:
                    src.unlink()
                moved += 1
            else:
                blocked.append(src.relative_to(folder).as_posix())
            continue
        if apply:
            tmp = dest.with_name("." + dest.name + ".pulling")
            tmp.write_bytes(data)
            if tmp.read_bytes() != data:
                tmp.unlink()
                blocked.append(src.relative_to(folder).as_posix())
                continue
            tmp.replace(dest)
            src.unlink()
        moved += 1
    if apply and not blocked:
        for sub in sorted((p for p in folder.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            try:
                sub.rmdir()
            except OSError:
                pass
        (folder / READY).unlink(missing_ok=True)
        (folder / f"{MARKER}{today}").write_text(f"{moved} files pulled into OSINT new/ at {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC\n", encoding="utf-8")
    return moved, tagged, blocked, backfill


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--apply", action="store_true", help="move the files; without it, a dry run")
    ap.add_argument("--queue", default=str(QUEUE), help=argparse.SUPPRESS)
    ap.add_argument("--new", default=str(NEW), help=argparse.SUPPRESS)
    a = ap.parse_args()
    queue = pathlib.Path(a.queue)
    verb = "pulled" if a.apply else "would pull"
    if not queue.is_dir():
        print(f"pull-new-queue: {queue} not reachable — nothing pulled; the queue waits for tomorrow")
        return 0
    today = dt.date.today().isoformat()
    folders = files = 0
    waiting = []
    for folder, reason in batches(queue):
        if reason == "delivered":
            continue
        if reason:
            waiting.append(folder.name)
            print(f"  {folder.name}: {reason} — left in the queue")
            continue
        moved, tagged, blocked, backfill = pull(folder, today, a.apply, pathlib.Path(a.new))
        folders += 1
        files += moved
        lane = "backfill" if backfill else "news"
        extra = f", {tagged} given sweep_batch" if tagged else ""
        print(f"  {folder.name}: {verb} {moved} files ({lane} lane{extra})")
        for b in blocked:
            print(f"    blocked: {b} — a different file of that name is already in new/; left in the queue, folder not marked delivered")
    print(f"pull-new-queue: {verb} {files} files from {folders} folders" + (f"; {len(waiting)} without READY left" if waiting else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
