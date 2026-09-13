# -*- coding: utf-8 -*-
"""Housekeeping job 24 — apply the merges decided in reviews/entity-slug-pairs.csv.

Rewrites every reference to a variant slug so it points at the group's canonical slug:
wikilinks (`[[slug]]` and `[[slug|Alias]]`), `entities:` lists, and the finance records'
`financier_slug:` / `recipient_slug:` fields.

Two things it is careful about:

* **Line endings.** This repo is mixed CRLF/LF and the edit is a substring replacement
  on the raw text, so nothing is normalised.
* **Duplicates.** Merging can leave the canonical slug twice in one `entities:` list.
  Those are de-duplicated in place, order preserved.

Page files are NOT deleted here. Where a variant has its own page the merge is a content
decision, not a rewrite, and is done by hand first — this run had exactly one
(`paratus-group` into `paratus`).

Usage:  python scripts/entity-slug-merge.py [--write]
"""
import csv, glob, io, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "reviews", "entity-slug-pairs.csv")
DIRS = ["raw", "wiki", "reviews", "sweep", "documentation", "new", "new-queue",
        "budget-archive", "prototypes", "lookups"]


def load_map():
    groups = collections.defaultdict(set)
    for r in csv.DictReader(io.open(REG, encoding="utf-8")):
        if r["decision"] == "merge":
            groups[r["canonical"]].update((r["slug_a"], r["slug_b"]))
    m = {}
    for canon, members in groups.items():
        for v in members:
            if v != canon:
                m[v] = canon
    return m


ENTITIES_LINE = re.compile(r"(?m)^(entities:[ \t]*)\[(.*)\][ \t]*(\r?)$")


def rewrite_entities(text, m):
    """`entities:` is a list of single-bracket tokens — `entities: [[a], [b]]` — NOT a
    list of `[[wikilinks]]`. Reading it as wikilinks matches only the first element and
    silently leaves every other tag unmerged, which is how the first run of this script
    reported 5 referenced variants when the true number was 44.

    ⚠ A minority of files carry the **bare** form `entities: [a, b]` instead. The
    bracket scan finds nothing inside those, and re-emitting an empty `out` wrote
    `entities: []` over the file's whole tag list — 49 files would have been silently
    stripped on the job-65 run had the dry run not been diffed token-by-token rather
    than counted. The bare form is now mapped in place and re-emitted bare: this script
    merges slugs, it does not migrate a file's serialisation."""
    def fix(mo):
        head, body, cr = mo.group(1), mo.group(2), mo.group(3)
        bracketed = re.findall(r"\[([^\[\]]+)\]", body)
        bare = not bracketed and body.strip()
        toks = bracketed if bracketed else [t for t in body.split(",") if t.strip()]
        seen, out = set(), []
        for tok in toks:
            tok = m.get(tok.strip(), tok.strip())
            if tok not in seen:
                seen.add(tok); out.append(tok)
        inner = ", ".join(out) if bare else ", ".join("[%s]" % t for t in out)
        return head + "[" + inner + "]" + cr
    return ENTITIES_LINE.sub(fix, text)


def main():
    write = "--write" in sys.argv
    m = load_map()
    if not m:
        print("no merges in the register"); return
    pat = re.compile(r"\[\[(" + "|".join(re.escape(k) for k in sorted(m, key=len, reverse=True)) + r")(\]\]|\|)")
    # ⚠ `\s*$` would swallow the CRLF's \r and the replacement would not put it back,
    # silently converting one line per file to LF in a mixed-EOL repo. Match the \r
    # explicitly and re-emit it.
    slugfield = re.compile(r"(?m)^((?:financier|recipient)_slug:[ \t]*)(" +
                           "|".join(re.escape(k) for k in sorted(m, key=len, reverse=True)) +
                           r")[ \t]*(\r?)$")
    touched, hits = 0, collections.Counter()
    for d in DIRS:
        for f in glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True):
            raw = io.open(f, encoding="utf-8", errors="replace", newline="").read()
            new = pat.sub(lambda mo: "[[" + m[mo.group(1)] + mo.group(2), raw)
            new = slugfield.sub(lambda mo: mo.group(1) + m[mo.group(2)] + mo.group(3), new)
            new = rewrite_entities(new, m)
            if new != raw:
                for k in m:
                    n = (len(re.findall(r"\[\[" + re.escape(k) + r"(?:\]\]|\|)", raw))
                         + len(re.findall(r"\[" + re.escape(k) + r"\]", raw)))
                    if n: hits[k] += n
                touched += 1
                if write:
                    io.open(f, "w", encoding="utf-8", newline="").write(new)
    print("%s %d files; %d variant slugs still referenced" % (
        "rewrote" if write else "would rewrite", touched, len(hits)))
    for k, n in hits.most_common(12):
        print("   %-52s %4d -> %s" % (k[:52], n, m[k]))


if __name__ == "__main__":
    main()
