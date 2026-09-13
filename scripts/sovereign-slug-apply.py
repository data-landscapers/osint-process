# -*- coding: utf-8 -*-
r"""Housekeeping job 28 — collapse the sovereign-borrower slug class to one form per state.

The finance records' `recipient_slug` is what the Financing compile groups on
(`wiki/finance-record-spec.md` -> *Entities*), and lint #16 treats recipient drift as
soft precisely because "the entity pass reconciles it". It had not been reconciled: the
same sovereign arrived under two conventions from two different loads —

  * the Chinese-lender load wrote  `government-of-ghana`
  * the World Bank IDA/IBRD load wrote `republic-of-ghana`

— so "who has Ghana borrowed from" split by *lender*, which is the one axis it must not
split by. Congo-Brazzaville had three forms plus a fourth on the financier side.

A second, different defect rode along: ~22 slugs jam two names into one and were cut
mid-phrase by the slugifier — `government-of-angola-ministry-of`,
`government-of-nigeria-bank-of`, and `democratic-republic-of-so-tom`, which is
"São Tomé and Príncipe" with the accents mangled away. The body's `Recipient` cell
carries the full string in every case, so these are recoverable by reading, not guessing.

The map is `reviews/sovereign-slug-map.csv`, one row per variant with its reason:

  sovereign-form  a spelling of the state          -> government-of-<country>
  composite       state + counterparty in one slug -> the counterparty where the wiki
                                                      pages it, else the sovereign
  keep            not in the class                 -> untouched, with the reason

Rewrites `financier_slug:`, `recipient_slug:`, `entities:` lists and `[[wikilinks]]`
together — a record whose slug field moved but whose `entities:` did not would fail
lint #16 check C. Line endings are preserved: this repo is mixed CRLF/LF.

Usage:  python scripts/sovereign-slug-apply.py [--write]
"""
import csv, glob, io, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(ROOT, "reviews", "sovereign-slug-map.csv")
DIRS = ["raw", "wiki", "reviews", "sweep", "documentation", "new", "new-queue",
        "budget-archive", "prototypes", "lookups"]

ENTITIES_LINE = re.compile(r"(?m)^(entities:[ \t]*)\[(.*)\][ \t]*(\r?)$")


def load():
    with io.open(MAP, encoding="utf-8") as fh:
        return {r["slug"]: r["target"] for r in csv.DictReader(fh)
                if r["decision"] == "merge" and r["target"]}


def rewrite_entities(text, m):
    """`entities:` is a list of single-bracket tokens — `entities: [[a], [b]]` — not a
    list of `[[wikilinks]]`. Collapsing can leave the canonical slug twice; dedupe in
    place, order preserved."""
    def fix(mo):
        head, body, cr = mo.group(1), mo.group(2), mo.group(3)
        seen, out = set(), []
        for tok in re.findall(r"\[([^\[\]]+)\]", body):
            tok = m.get(tok.strip(), tok.strip())
            if tok not in seen:
                seen.add(tok)
                out.append(tok)
        return head + "[" + ", ".join("[%s]" % t for t in out) + "]" + cr
    return ENTITIES_LINE.sub(fix, text)


def main():
    write = "--write" in sys.argv
    m = load()
    if not m:
        raise SystemExit("empty map")
    keys = sorted(m, key=len, reverse=True)
    alt = "|".join(re.escape(k) for k in keys)
    link = re.compile(r"\[\[(" + alt + r")(\]\]|\|)")
    # ⚠ match the \r explicitly and re-emit it: `\s*$` would swallow it and silently
    # drop the line to LF in a mixed-EOL repo.
    slugf = re.compile(r"(?m)^((?:financier|recipient)_slug:[ \t]*)(" + alt + r")[ \t]*(\r?)$")

    touched, hits = 0, collections.Counter()
    for d in DIRS:
        for f in sorted(glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True)):
            raw = io.open(f, encoding="utf-8", errors="replace", newline="").read()
            new = link.sub(lambda mo: "[[" + m[mo.group(1)] + mo.group(2), raw)
            new = slugf.sub(lambda mo: mo.group(1) + m[mo.group(2)] + mo.group(3), new)
            new = rewrite_entities(new, m)
            if new != raw:
                for k in keys:
                    n = (len(re.findall(r"\[" + re.escape(k) + r"\]", raw))
                         + len(re.findall(r"(?m)^(?:financier|recipient)_slug:[ \t]*"
                                          + re.escape(k) + r"[ \t]*\r?$", raw)))
                    if n:
                        hits[k] += n
                touched += 1
                if write:
                    io.open(f, "w", encoding="utf-8", newline="").write(new)

    print("%s %d files; %d variant slugs collapsed"
          % ("rewrote" if write else "would rewrite", touched, len(hits)))
    for k, n in hits.most_common():
        print("   %-64s %3d -> %s" % (k[:64], n, m[k]))
    left = sorted(set(keys) - set(hits))
    if left:
        print("\n  in the map but not found in the vault: %s" % ", ".join(left))


if __name__ == "__main__":
    main()
