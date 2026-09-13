# -*- coding: utf-8 -*-
"""Housekeeping job 22 — `body_completeness: excerpt` on wiki-generated sources.

`reference.md` §4: anything the wiki *generated* rather than *captured* — a finance
deal record built from a CSV row, an artefact's companion page, a statistic capsule
lifted from a dataset — has no "as published" body to be complete. So `full` is simply
false, and `excerpt` is correct and final. The field feeds the paywalled-promotion gate
and the `full > excerpt` dedup tiebreak, so a wrong `full` wins tiebreaks it should lose
against a real prose primary.

Three cohorts, detected from the file itself rather than from a list:

  finance-record   `deal_id:` or `finance_origin:` in frontmatter
  companion-page   `artefact:` in frontmatter, OR a body that names itself the
                   companion source page of an artefact (two such pages carry no
                   `artefact:` field — that is how they were missed before)
  statistic-capsule  none found distinct from the above; a *captured* statistics web
                   page (e.g. the CBK national-payments page) is a real capture and
                   keeps `full`. Deliberately not guessed at.

Line endings are preserved per file — this repo is mixed CRLF/LF.

Usage:  python scripts/fix-body-completeness-generated.py [--write]
"""
import glob, io, re, sys

FM = re.compile(r"^---\r?\n(.*?)\r?\n---(.*)$", re.S)
COMPANION = re.compile(r"companion (source )?page for the artefact|Companion page (to|for)", re.I)


def cohort(head, body):
    if re.search(r"^(deal_id|finance_origin):\s*\S", head, re.M):
        return "finance-record"
    if re.search(r"^artefact:\s*\S", head, re.M):
        return "companion-page"
    if COMPANION.search(body):
        return "companion-page (no artefact: field)"
    return None


def main():
    write = "--write" in sys.argv
    changed, by_cohort, by_from = [], {}, {}
    for f in sorted(glob.glob("raw/*/*.md")):        # raw/ is sharded raw/YYYY/
        raw = io.open(f, "r", encoding="utf-8", errors="replace", newline="").read()
        m = FM.match(raw)
        if not m:
            continue
        head, body = m.group(1), m.group(2)
        c = cohort(head, body)
        if not c:
            continue
        # \r? before $ matters: this repo is mixed CRLF/LF, and without it every CRLF
        # file silently fails to match and is skipped (600+ of them, on first run).
        bm = re.search(r"^(body_completeness:[ \t]*)(\S+)[ \t]*\r?$", head, re.M)
        if not bm or bm.group(2) == "excerpt":
            continue
        old = bm.group(2)
        by_cohort[c] = by_cohort.get(c, 0) + 1
        by_from[old] = by_from.get(old, 0) + 1
        changed.append(f)
        if write:
            # Splice the one line in place. Do NOT reconstruct the frontmatter: some
            # files carry a stray LF among CRLF lines, and rebuilding normalises those
            # too — rewriting lines this job has no business touching.
            lo = 4 + bm.start(2)          # 4 = len("---\n"); FM matched at offset 0
            if raw[:4] != "---\n":        # CRLF file: the opening fence is "---\r\n"
                lo = 5 + bm.start(2)
            hi = lo + len(old)
            assert raw[lo:hi] == old, (f, raw[lo:hi], old)
            io.open(f, "w", encoding="utf-8", newline="").write(raw[:lo] + "excerpt" + raw[hi:])

    print("%s %d generated sources" % ("rewrote" if write else "would rewrite", len(changed)))
    print("  by cohort:", by_cohort)
    print("  from:     ", by_from)


if __name__ == "__main__":
    main()
