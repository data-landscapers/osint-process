#!/usr/bin/env python3
r"""restore-drill.py — strategic review R180: rebuild OSINT on a machine that has never held it, from the git remote and the private R2 bucket alone.

A clone restores every tracked file. What git ignores (the PDFs and other originals in `raw/` and `budget-archive/`, about 28 GB) exists only on this laptop, its `O:\` mirror and CORPUS's private R2 bucket `osint-backup` (R196), whose keys are paths from the repository root. The drill passes when all four hold:

1. every bucket object is restored to its path and its MD5 matches the object's ETag (a multipart ETag, which is no MD5, is counted and not compared);
2. no bucket key falls outside `raw/` and `budget-archive/`;
3. `scripts/lint-deterministic.py` in the restored tree finds exactly what it finds in the live tree, check by check (the live tree carries standing hard findings, so "exits 0" could never pass; a missing original shows as new findings);
4. the restored `raw/` source-page count equals the live `cycle-manifest.json` count, read the same day.

Both live figures come from a baseline written on the live laptop the same day (`--baseline-out`, to `X:\restore-drill-baseline.json`); the restore checks out the baseline's commit, so the two trees are the same commit. It prints one line, which is R180's line. Re-running resumes: a file already present at the object's size and MD5 is not fetched again.

Needs Python 3.10+, git, `pip install boto3`, and an R2 key scoped read-only to the bucket, in the environment:
    R2_ENDPOINT=https://<account-id>.r2.cloudflarestorage.com  R2_ACCESS_KEY_ID=...  R2_SECRET_ACCESS_KEY=...

Usage:
    python scripts/restore-drill.py --baseline-out X:\restore-drill-baseline.json      # live laptop, same day; ~10 min
    python restore-drill.py --target D:\osint-restore --baseline X:\restore-drill-baseline.json   # restore machine
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REMOTE = "https://github.com/data-landscapers/OSINT.git"
ALLOWED = ("raw/", "budget-archive/")


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lint_table(tree):
    """{check number: hard count} from lint-deterministic's summary table, and its exit code."""
    r = subprocess.run([sys.executable, "scripts/lint-deterministic.py"], cwd=tree, capture_output=True, text=True, encoding="utf-8", errors="replace")
    rows = re.findall(r"^\s*(\d+)\s+(\d+)\s+\d+\s+\S", r.stdout, re.M)
    return {k: int(v) for k, v in rows}, r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline-out", help="on the live laptop: write HEAD, the manifest's raw_sources and the lint table here, and stop")
    ap.add_argument("--baseline", help="on the restore machine: the baseline written today")
    ap.add_argument("--target", help="an empty or absent folder, or a previous drill's to resume")
    ap.add_argument("--bucket", default="osint-backup")
    ap.add_argument("--remote", default=REMOTE)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.baseline_out:
        live = Path(__file__).resolve().parent.parent
        table, _ = lint_table(live)
        b = {"date": datetime.date.today().isoformat(),
             "head": subprocess.run(["git", "-C", str(live), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
             "raw_sources": json.load(open(live / "cycle-manifest.json", encoding="utf-8"))["counts"]["raw_sources"],
             "lint_hard": table}
        Path(a.baseline_out).write_text(json.dumps(b, indent=1), encoding="utf-8")
        print(f"baseline {b['date']} · {b['head'][:10]} · raw_sources {b['raw_sources']:,} · {sum(table.values())} hard lint findings over {len(table)} checks -> {a.baseline_out}")
        return 0
    if not (a.target and a.baseline):
        sys.exit("restore-drill: give --target and --baseline (or --baseline-out on the live laptop)")
    base = json.load(open(a.baseline, encoding="utf-8"))
    if base["date"] != datetime.date.today().isoformat():
        print(f"restore-drill: warning — the baseline is from {base['date']}, not today", file=sys.stderr)
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        sys.exit("restore-drill: pip install boto3")
    try:
        env = {k: os.environ[k] for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")}
    except KeyError as e:
        sys.exit(f"restore-drill: {e.args[0]} is not set")

    t = Path(a.target)
    if not (t / ".git").exists():
        subprocess.run(["git", "clone", "--quiet", a.remote, str(t)], check=True)
    subprocess.run(["git", "-C", str(t), "checkout", "--quiet", base["head"]], check=True)
    head = subprocess.run(["git", "-C", str(t), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()

    s3 = boto3.client("s3", endpoint_url=env["R2_ENDPOINT"], aws_access_key_id=env["R2_ACCESS_KEY_ID"], aws_secret_access_key=env["R2_SECRET_ACCESS_KEY"], region_name="auto", config=Config(retries={"max_attempts": 10, "mode": "standard"}))
    objs = [o for page in s3.get_paginator("list_objects_v2").paginate(Bucket=a.bucket) for o in page.get("Contents", [])]
    stray = [o["Key"] for o in objs if not o["Key"].startswith(ALLOWED)]

    def fetch(o):
        key, etag, size = o["Key"], o["ETag"].strip('"'), o["Size"]
        dest = t / key
        multipart = "-" in etag
        if dest.exists() and dest.stat().st_size == size and (multipart or md5(dest) == etag):
            return key, "held", multipart
        dest.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(a.bucket, key, str(dest))
        ok = dest.stat().st_size == size and (multipart or md5(dest) == etag)
        return key, "ok" if ok else "MISMATCH", multipart

    results = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(fetch, objs), 1):
            results.append(r)
            if i % 250 == 0:
                print(f"  {i:,}/{len(objs):,}", file=sys.stderr, flush=True)
    bad = [k for k, s, _ in results if s == "MISMATCH"]
    unchecked = sum(1 for *_, m in results if m)

    table, _ = lint_table(t)
    diff = {k: (base["lint_hard"].get(k, 0), table.get(k, 0)) for k in set(table) | set(base["lint_hard"]) if base["lint_hard"].get(k, 0) != table.get(k, 0)}
    pages = sum(1 for _, _, fs in os.walk(t / "raw") for f in fs if f.endswith(".md"))
    passed = bool(table) and not bad and not stray and not diff and pages == base["raw_sources"]
    day = datetime.date.today().isoformat()
    print(f"{day} · R180 restore drill {'PASSED' if passed else 'FAILED'} · clone {head} of {base['head'][:10]} + {len(objs):,} objects from {a.bucket} ({len(bad)} MD5 mismatches, {unchecked} multipart unchecked, {len(stray)} outside raw/ and budget-archive/) · lint {sum(table.values())} hard findings, {len(diff)} checks differing from live · raw/ {pages:,} pages vs manifest {base['raw_sources']:,}")
    for k, (was, now) in sorted(diff.items(), key=lambda kv: int(kv[0])):
        print(f"  lint #{k}: live {was}, restored {now}", file=sys.stderr)
    for k in (bad + stray)[:20]:
        print("  " + k, file=sys.stderr)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
