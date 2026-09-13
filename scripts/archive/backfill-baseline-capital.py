#!/usr/bin/env python3
"""
backfill-baseline-capital.py  —  one-shot completion of the back-swing.

The back-swing was applied by a script version that did not yet carry the
capital/recurrent split, so the consolidated records lack `baseline_capital` /
`baseline_recurrent`. Those figures survive on the pre-back-swing per-stage
records still in git HEAD. This reads them from HEAD and inserts the two fields
(after `execution_pct_vs_revised`) into the live consolidated records — additive,
touches nothing else.

DRY-RUN by default; --apply writes.
"""
import os, re, sys, subprocess, importlib.util

RAW = "raw"
spec = importlib.util.spec_from_file_location("cbl", "scripts/consolidate-budget-lines.py")
cbl = importlib.util.module_from_spec(spec); spec.loader.exec_module(cbl)

def head_capital_files():
    """HEAD raw records that carry a (possibly blank) amount_capital field."""
    out = subprocess.run(["git", "grep", "-l", "amount_capital:", "HEAD", "--", "raw/*.md"],
                         capture_output=True, text=True).stdout
    return [ln.split(":", 1)[1] for ln in out.splitlines() if ":" in ln]

def batch_show(paths):
    """Read many HEAD:blobs in one `git cat-file --batch` call. -> {path: content}."""
    refs = "".join(f"HEAD:{p}\n" for p in paths).encode()
    proc = subprocess.run(["git", "cat-file", "--batch"], input=refs, capture_output=True)
    buf, out, i = proc.stdout, {}, 0
    for p in paths:
        nl = buf.index(b"\n", i)
        header = buf[i:nl].decode()
        i = nl + 1
        if "missing" in header:
            continue
        size = int(header.split()[2])
        out[p] = buf[i:i + size].decode("utf-8", "replace")
        i += size + 1  # skip trailing newline
    return out

def untracked_domestic():
    """Live consolidated records are the untracked raw/*.md files."""
    out = subprocess.run(["git", "ls-files", "--others", "--exclude-standard", "--", "raw/*.md"],
                         capture_output=True, text=True).stdout
    return [ln for ln in out.splitlines() if ln.endswith(".md")]

STAGE_RANK = {s: i for i, s in enumerate(cbl.STAGE_ORDER)}

def strict_get(fm, key):
    """Same-line value only — never spill onto the next line for a blank field."""
    m = re.search(r'^%s:[ \t]*(\S[^\n]*?)[ \t]*$' % re.escape(key), fm, re.M)
    return m.group(1) if m else ""

def main():
    apply = "--apply" in sys.argv
    # 1. map new_deal_id -> (capital, recurrent), preferring the appropriated stage
    cap = {}
    hp = head_capital_files()
    contents = batch_show(hp)
    for path, t in contents.items():
        fm, _ = cbl.split_front(t)
        if not fm:
            continue
        c = strict_get(fm, "amount_capital"); r = strict_get(fm, "amount_recurrent")
        if not (c or r):                       # genuinely blank -> nothing to carry
            continue
        deal = strict_get(fm, "deal_id")
        iso3, tier, fy, sig, _ = cbl.parse_deal(deal, fm)
        nd = cbl.new_deal_id(iso3, tier, fy, sig)
        stage = strict_get(fm, "budget_stage") or "unclear"
        rank = STAGE_RANK.get(stage, 99)
        # keep the earliest (appropriated-preferred) stage's split
        if nd not in cap or rank < cap[nd][2]:
            cap[nd] = (c, r, rank)
    print(f"line-years with a capital/recurrent split in HEAD: {len(cap)}")

    # 2. patch live consolidated records (the untracked raw/*.md files)
    patched = skipped_have = skipped_nomap = 0
    for p in untracked_domestic():
        try:
            t = open(p, encoding="utf-8").read()
        except Exception:
            continue
        if "finance_origin: domestic-state" not in t:
            continue
        fm, _ = cbl.split_front(t)
        if not fm:
            continue
        # idempotent: strip any prior backfill lines (including earlier garbage) first
        t2 = re.sub(r'^baseline_(?:capital|recurrent):.*\n', '', t, flags=re.M)
        nd = strict_get(fm, "deal_id")
        if nd not in cap:
            if t2 != t:                        # had garbage but no genuine split -> clean only
                skipped_nomap += 1
                if apply:
                    open(p, "w", encoding="utf-8").write(t2)
            else:
                skipped_nomap += 1
            continue
        c, r, _ = cap[nd]
        ins = f"baseline_capital: {c}\nbaseline_recurrent: {r}\n"
        new_t, n = re.subn(r'(^execution_pct_vs_revised:.*\n)', r'\1' + ins, t2, count=1, flags=re.M)
        if n == 0:  # fallback: before the closing --- of frontmatter
            new_t = re.sub(r'\n---\n', "\n" + ins + "---\n", t2, count=1)
        patched += 1
        if apply:
            open(p, "w", encoding="utf-8").write(new_t)
    print(f"{'PATCHED' if apply else 'WOULD PATCH'}: {patched} | already had it: {skipped_have} | "
          f"no split in HEAD (blank/ZAF/uncommitted): {skipped_nomap}")
    if not apply:
        print("Dry-run. Re-run with --apply to write.")

if __name__ == "__main__":
    main()
