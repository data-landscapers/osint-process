#!/usr/bin/env python3
"""trim-verify.py — standing. Verify rewritten intersection pages against git HEAD.

Written 2026-09-24 for housekeeping jobs 190-202 (the append-log trim); the
check every sub-agent runs under `wiki/append-log-trim.md` before it reports.

usage: python scripts/trim-verify.py <slug> [<slug> ...]   (from the repo root)

Per page: line endings match HEAD; every HEAD `sources:` slug still present;
places/topics/entities/place/topic/type/title unchanged; every [[link]] target in
the HEAD body still present somewhere in the new file (self-links excepted); every
raw/ slug cited in the new body is in `sources:`. Prints body words before/after
(counted up to the first `## Links`/`## Sources`) and how many content headings
are dated. Exit 1 on any problem; exit 2 on a slug with no page.
"""
import pathlib
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = pathlib.Path(__file__).resolve().parent.parent
LINK = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
DATED = re.compile(r"\((?:[^)]*\d{4}-\d{2}|[^)]*\b(?:19|20)\d{2}\b)[^)]*\)\s*$")


def split(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        return text[:end], text[end + 4:]
    return "", text


def fm_line(fm, key):
    m = re.search(rf"^{key}:.*$", fm, re.M)
    return m.group(0) if m else None


def fm_list(fm, key):
    line = fm_line(fm, key)
    return {x.strip() for x in re.findall(r"\[([^\[\]]+)\]", line)} if line else set()


def words(body):
    body = re.split(r"^## (?:Links|Sources)\s*$", body, flags=re.M)[0]
    return len(re.findall(r"\S+", LINK.sub("x", body)))


def main(slugs):
    missing_pages = [s for s in slugs if not (ROOT / f"wiki/intersections/{s}.md").exists()]
    if not slugs or missing_pages:
        print(f"trim-verify: no page for {missing_pages or 'any slug'} under wiki/intersections/")
        return 2
    raw_slugs = {p.stem for p in (ROOT / "raw").rglob("*.md")}
    ok_all = True
    for slug in slugs:
        rel = f"wiki/intersections/{slug}.md"
        old = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True).stdout.decode("utf-8")
        new = (ROOT / rel).read_bytes().decode("utf-8")
        probs = []
        old_crlf = old.count("\r\n") > 0 and old.count("\n") == old.count("\r\n")
        new_crlf = new.count("\n") == new.count("\r\n")
        if old_crlf != new_crlf:
            probs.append(f"EOL mismatch (HEAD crlf={old_crlf}, now crlf={new_crlf})")
        ofm, obody = split(old.replace("\r\n", "\n"))
        nfm, nbody = split(new.replace("\r\n", "\n"))
        nsrc = fm_list(nfm, "sources")
        lost_src = fm_list(ofm, "sources") - nsrc
        if lost_src:
            probs.append(f"sources lost: {sorted(lost_src)}")
        for key in ("places", "topics", "entities", "place", "topic", "type", "title"):
            if fm_line(ofm, key) != fm_line(nfm, key):
                probs.append(f"frontmatter {key} changed")
        olinks = {l.strip() for l in LINK.findall(obody)} - {slug}
        nall = {l.strip() for l in LINK.findall(nbody)} | nsrc | fm_list(nfm, "entities")
        lost_links = olinks - nall
        if lost_links:
            probs.append(f"links lost ({len(lost_links)}): {sorted(lost_links)[:30]}")
        uncited = ({l.strip() for l in LINK.findall(nbody)} & raw_slugs) - nsrc
        if uncited:
            probs.append(f"body-cited raw slugs missing from sources ({len(uncited)}): {sorted(uncited)[:10]}")
        heads = [h for h in re.findall(r"^## (.+)$", nbody, re.M)
                 if h.strip() not in ("Links", "Sources") and not h.startswith("Extracted from")]
        dated = [h for h in heads if DATED.search(h)]
        print(f"{slug}: words {words(obody):,} -> {words(nbody):,}; sections {len(heads)}, dated {len(dated)}; {'OK' if not probs else 'PROBLEMS'}")
        for p in probs:
            ok_all = False
            print("   - " + p)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
