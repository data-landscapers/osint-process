#!/usr/bin/env python3
"""lint-index-dates.py — job 30 step (d), as a standing check.

`CLAUDE.md` -> Currency: every time-varying figure is written dated. The scope ruling
folded into housekeeping job 30 says an index bullet is no exception — a bare percentage
reads as current however old it is, and an index line is read more often than the page
it summarises.

This reports bare time-varying figures in `## Active topics` / `## By place` / `## Topics`
index bullets only. Body prose is out of scope: it is covered by the Currency rule
directly and by whatever pass last touched the page.

A bullet counts as dated if a year, an "as of/at", a quarter or an FY appears anywhere in
it, or in the heading above it. Expect false positives on contract values, fund sizes, a
plant's design capacity and ordinals that name an event rather than a rank — none of those
is time-varying, and the right fix there is to make that plain in the prose, not to hang a
date on it.

Usage: lint-index-dates.py            # whole wiki
"""
import collections, glob, os, re, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIG = re.compile(
    r"(?<![\w.])("
    r"\d{1,3}(?:[.,]\d+)?\s*%"
    r"|\d{1,3}(?:st|nd|rd|th)\b"
    r"|(?:US\$|\$|EUR|€|£|R|KES|NGN|ZAR|GHS|FCFA|MRU)\s?\d[\d,. ]*(?:bn|m|k|billion|million|thousand|tn)?"
    r"|\d[\d,. ]*\s*(?:Gbps|Tbps|Mbps|MW|GW|km)\b"
    r")"
)
YEAR = re.compile(r"\b(19|20)\d{2}\b|\bas (?:of|at)\b|\bQ[1-4]\b|\bFY\d")
SKIP = re.compile(r"\b(?:section|article|s\.|art\.|chapter|part|no\.|act|si|version)\s*\d", re.I)
INDEX = ("## active topics", "## by place", "## topics")


def check(path):
    t = open(path, encoding="utf-8", errors="replace").read().replace("\r\n", "\n")
    body = t.split("\n---\n", 1)[-1]
    hits, inside, dated = [], False, False
    for ln, line in enumerate(body.split(chr(10)), 1):
        if line.startswith("## "):
            inside = line.strip().lower().startswith(INDEX)
            dated = bool(YEAR.search(line))
            continue
        if line.startswith("### "):
            dated = bool(YEAR.search(line))
            continue
        if not inside or dated:
            continue
        if not line.lstrip().startswith(("-", "*")) or YEAR.search(line):
            continue
        for m in FIG.finditer(line):
            if SKIP.search(line[max(0, m.start() - 60):m.end() + 60]):
                continue
            hits.append((ln, m.group(0), line.strip()[:130]))
    return hits


if __name__ == "__main__":
    byf, total = {}, 0
    for p in sorted(glob.glob("wiki/**/*.md", recursive=True)):
        h = check(p)
        if h:
            byf[p] = h
            total += len(h)
    for p, h in sorted(byf.items(), key=lambda x: -len(x[1])):
        print(f"\n{p} — {len(h)}")
        for ln, fig, line in h:
            print(f"  L{ln}  {fig!r}  {line}")
    print(f"\n{len(byf)} file(s), {total} bare figure(s) in INDEX bullets")
