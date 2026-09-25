#!/usr/bin/env python3
r"""
pull-new-queue.py — move CORPUS's finished batches from `X:\new-queue\` into `new/`, the sweep cycle's first act.

**Why it exists.** `X:\new-queue\` was a hand-carry: CORPUS staged, Bill moved the files into `OSINT\new\`, and a batch waited on his hands *(2026-08-20)*. Strategic review 4 retired that (ruling R8, register R09, 2026-09-17): the cycle pulls a batch itself, and ingest still decides admission — pulling is delivery, not endorsement.

**What it pulls.** Every top-level folder of `X:\new-queue\` that carries a `READY` file. CORPUS writes `READY` last, so a folder without one is a batch still being written and is left alone. **Once a folder's files are all in `new/`, the folder is deleted** *(Bill, 2026-09-21, `notes-for-osint` 158 — the `delivered-YYYY-MM-DD` marker it used to leave is retired)*, so the queue shows only work not yet delivered; a folder still holding nothing but an old marker is deleted on sight. **Loose files at the root are pulled too** *(Bill, 2026-09-21, `notes-for-osint` 155)*: the root is where Bill drops items by hand, CORPUS never writes there, so every root file is his. They take the **news lane** — no `sweep_batch:` is inserted — and a file **modified in the last ten minutes is left for the next run**, because it may still be saving.

**Where it puts it.** Flat into `new/`, which is how every producer stages (`STATUS-ACQUIRE.md` → *Staging*): a filler batch's `baseline/` and `progress/` subfolders flatten with it. A name already in `new/` is not overwritten — the file stays in the queue, is named in the output, and the folder is kept with its `READY`, so the next night retries it. A byte-identical file already in `new/` is a previous interrupted pull: the queue's copy is removed and counted as delivered.

**The lane.** `scripts/ingest-lane.py` reads the lane off `sweep_batch:`. A `.md` candidate that carries no `sweep_batch:`, in a folder named with a backfill prefix (`status-acquire-`, `progress-filler-`, `dataset-`, `budget-poll-`), gets `sweep_batch: <folder>-<YYYY-MM-DD>` inserted as the first frontmatter key — the prefix from the folder name, exactly as the register line says. A candidate that already carries one keeps it, and a folder with any other name adds nothing, so its items take the news lane at full price: the whitelist's own default.

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
import time
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


SETTLING = 600  # seconds; a file this new may still be being written


def loose(queue, apply, new):
    """Move the files at the root of the queue into `new/`. Bill's own picks, news lane.

    Same copy-verify-delete discipline and the same collision rule as a batch; no
    `sweep_batch:` is inserted, so `ingest-lane.py` reads them at full price. A file
    younger than SETTLING seconds is left where it is and pulled on a later run.
    """
    now = time.time()
    moved, waiting, blocked = 0, [], []
    for src in sorted(p for p in queue.iterdir() if p.is_file()):
        if now - src.stat().st_mtime < SETTLING:
            waiting.append(src.name)
            continue
        data = src.read_bytes()
        dest = new / src.name
        if dest.exists():
            if dest.read_bytes() == data:
                if apply:
                    src.unlink()
                moved += 1
            else:
                blocked.append(src.name)
            continue
        if apply:
            tmp = dest.with_name("." + dest.name + ".pulling")
            tmp.write_bytes(data)
            if tmp.read_bytes() != data:
                tmp.unlink()
                blocked.append(src.name)
                continue
            tmp.replace(dest)
            src.unlink()
        moved += 1
    return moved, waiting, blocked


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
        remove(folder)
    return moved, tagged, blocked, backfill


def remove(folder):
    """Delete a spent batch folder: its `READY`, any old `delivered-` marker, then the folder itself."""
    for p in folder.iterdir():
        if p.is_file() and (p.name == READY or p.name.startswith(MARKER)):
            p.unlink()
    try:
        folder.rmdir()
    except OSError:
        pass


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
            if a.apply:
                remove(folder)
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
            print(f"    blocked: {b} — a different file of that name is already in new/; left in the queue, folder kept")
    root_moved, root_waiting, root_blocked = loose(queue, a.apply, pathlib.Path(a.new))
    if root_moved or root_waiting or root_blocked:
        print(f"  (root): {verb} {root_moved} loose file(s) (news lane)")
        for n in root_waiting:
            print(f"    still settling: {n} — modified in the last {SETTLING // 60} minutes, left for the next run")
        for n in root_blocked:
            print(f"    blocked: {n} — a different file of that name is already in new/; left in the queue")
    files += root_moved
    print(f"pull-new-queue: {verb} {files} files from {folders} folders"
          + (f" and the queue root" if root_moved else "")
          + (f"; {len(waiting)} without READY left" if waiting else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
