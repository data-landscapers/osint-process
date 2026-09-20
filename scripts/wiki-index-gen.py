#!/usr/bin/env python3
r"""wiki-index-gen.py — the intersection enumeration, generated into the two indexes.

Housekeeping jobs 89 and 117, strategic review 4 register R45. `places-index.md` names 608
of the 1,091 pages under `wiki/intersections/` and `topics-index.md` names 633; **310 are
named by neither**, so they are reachable only by someone who already knows the slug. The
cause is structural rather than one run's slip: `WIKI-SYNC.md` step 9 opens an index when a
run introduces a *new place or topic*, and a new intersection page for an already-listed
pair introduces neither — which is the normal case and has fired several hundred times.

**A generated block is the answer, not a bigger hand-maintained cell.** Job 89 states the
difficulty exactly: 483 more pointers will not fit the `Lead topics` prose cell without
making it unreadable. They do not have to. That cell is a **curated lead** — a topic with a
gloss, in the editor's order — and an enumeration is a different job. So this owns a block
of its own, appends it if it is not there, replaces it if it is, and **never touches a byte
outside its own markers**, which is asserted before anything is written.

**One line per place, one per topic, and the pointers labelled by the other axis.** A
reader who has chosen Angola wants the topics, not 28 repetitions of the word Angola. So a
place line reads `[[angola--dpi-id|dpi.id]], …` and a topic line reads
`[[angola--infra-store|AGO]], …`. The whole enumeration is **94 pointer-bearing lines across the two
files** rather than 1,091, which is what makes completeness affordable. Pointers are
ordered by the taxonomy inside a place line and by place code inside a topic line, so two
runs a month apart produce the same bytes from the same tree.

**The row shape is OSINT's ruling and this proposes one.** `--shape` takes `inline` (the
above) or `bullets` (a sub-list per place or topic, one pointer a line, 2,352 lines against 135) so the
alternative can be seen rather than imagined before it is ruled on.

**It is a script OSINT runs, not a patch.** The two index files were edited three times in
the week to 2026-09-17, and a whole-file patch cut against a mirror would conflict with
whichever edit landed next. A block regenerated in place does not.

Usage:
  python wiki-index-gen.py --check                 # exit 1 if a block is out of date
  python wiki-index-gen.py --diff                  # the unified diff it would produce
  python wiki-index-gen.py --shape bullets --diff  # the other shape, to compare
  python wiki-index-gen.py --write

Exit: 0 the blocks are current or a clean dry run, 1 out of date (`--check`) or a refusal,
2 the wiki or a lookup is not where the script was pointed.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                    # noqa: E402

BEGIN = "<!-- BEGIN GENERATED: intersections (scripts/wiki-index-gen.py) -->"
END = "<!-- END GENERATED: intersections -->"
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END), re.S)
# A region code, as `countries.csv` and `places-index.md` both write it. Regions and
# countries are the same facet, and the page says so; they are listed apart only because
# a reader looking for a continental page is not looking through 54 country lines.
REGION_RE = re.compile(r"^X[A-Z]{2}$")
SHAPES = ("inline", "bullets", "gaps")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ---------------------------------------------------------------- the tree

def intersections(root):
    """[(slug, place, topic, title)] for every page under `wiki/intersections/`.

    A page missing `place:` or `topic:` is returned with the key blank rather than
    skipped: the generator reports it and refuses, because a page the enumeration cannot
    file is exactly the page this job exists to stop losing.
    """
    base = os.path.join(root, "wiki", "intersections")
    out = []
    for fn in sorted(os.listdir(base)):
        if not fn.lower().endswith(".md"):
            continue
        text = open(os.path.join(base, fn), "rb").read().decode("utf-8", "replace")
        fm, _, _ = V.parse_frontmatter(text)
        out.append((fn[:-3], str(fm.get("place") or ""), str(fm.get("topic") or ""),
                    str(fm.get("title") or "")))
    return out


def place_names(root):
    """code -> name, from `lookups/countries.csv` — the authority `places-index.md` names."""
    path = os.path.join(root, "lookups", "countries.csv")
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {r["iso-3"].strip(): r["country-name"].strip()
                for r in csv.DictReader(fh) if (r.get("iso-3") or "").strip()}


# ------------------------------------------------------------ the two blocks

def link(target, label):
    return "[[%s|%s]]" % (target, label)


def lines_for(groups, order, shape, label_of):
    """The body of one section: `groups` is key -> [(target, label)], already ordered."""
    out = []
    for key, heading, items in order:
        if not items:
            continue
        if shape == "inline":
            out.append("- **%s** %s — %s" % (key, heading,
                                             ", ".join(link(t, l) for t, l in items)))
        else:
            out.append("- **%s** %s" % (key, heading))
            out.extend("    - %s" % link(t, l) for t, l in items)
    return out


def places_block(rows, names, tax_order, shape):
    by_place = {}
    for slug, place, topic, _ in rows:
        by_place.setdefault(place, []).append((slug, topic))
    regions, countries = [], []
    for place in sorted(by_place, key=lambda p: (not REGION_RE.match(p), p)):
        items = [(s, t) for s, t in sorted(by_place[place],
                                           key=lambda p: (tax_order.get(p[1], (99, 99)), p[0]))]
        entry = (place, names.get(place, place), items)
        (regions if REGION_RE.match(place) else countries).append(entry)
    body = ["## Every intersection, by place", "",
            "Generated from `wiki/intersections/` — **{:,} pages across {:,} places**. The "
            "`Lead topics` cell above is the curated lead and carries the glosses; this is "
            "the enumeration, and it is complete by construction."
            .format(len(rows), len(by_place)),
            ""]
    for title, entries in (("Regions", regions), ("Countries", countries)):
        if not entries:
            continue
        body += ["**%s**" % title, ""]
        body += lines_for(None, entries, shape, None)
        body += [""]
    return body


def topics_block(rows, tax_order, tax_label, tax_l1, shape):
    by_topic = {}
    for slug, place, topic, _ in rows:
        by_topic.setdefault(topic, []).append((slug, place))
    body = ["## Every intersection, by topic", "",
            "Generated from `wiki/intersections/` — **{:,} pages across {:,} topics**. The "
            "`places:` list above each is the concept page's own roll-up; this names the "
            "page that holds each of them.".format(len(rows), len(by_topic)),
            ""]
    current = None
    for topic in sorted(by_topic, key=lambda t: (tax_order.get(t, (99, 99)), t)):
        l1 = tax_l1.get(topic, "Unclassified")
        if l1 != current:
            # A blank line before the heading as well as after it. Without it the `###`
            # sits directly under the previous topic's list item, which renders as a
            # heading in some parsers and as list text in others — and a block whose
            # rendering depends on the parser is not an index anyone can rely on.
            if body and body[-1] != "":
                body += [""]
            body += ["### %s" % l1, ""]
            current = l1
        items = sorted(by_topic[topic], key=lambda p: (p[1], p[0]))
        body += lines_for(None, [(topic, tax_label.get(topic, ""), items)], shape, None)
        if shape == "bullets":
            body += [""]
    if shape == "inline":
        body += [""]
    return body


def render(body):
    return "\n".join([BEGIN, ""] + body + [END])


# ---------------------------------------------------------------- splicing

def splice(text, block):
    """(new_text, action). The block replaces itself, or is appended once.

    **Nothing outside the markers moves**, which `verify` then proves rather than trusts.
    """
    if BLOCK_RE.search(text):
        return BLOCK_RE.sub(lambda _: block, text, count=1), "replaced"
    sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
    return text + sep + block + "\n", "appended"


def verify(before, after, path):
    """Everything outside the markers is unchanged, byte for byte."""
    def outside(text):
        m = BLOCK_RE.search(text)
        if not m:
            return text
        return text[:m.start()] + text[m.end():]
    a, b = outside(before), outside(after)
    if a == b or b.rstrip("\n") == a.rstrip("\n"):
        return None
    for i, (x, y) in enumerate(zip(a.split("\n"), b.split("\n"))):
        if x != y:
            return "%s: line %d outside the block changed: %r -> %r" % (path, i + 1, x, y)
    return "%s: the text outside the block changed length" % path


def diff(before, after, path):
    return "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        "a/" + path, "b/" + path))


# ---------------------------------------------------------------- the run

def already_named(root, rel):
    """Intersection slugs the file names *outside* the generated block.

    Both indexes already point at intersection pages — 608 from `places-index.md`'s
    `Lead topics` cells and 633 from `topics-index.md`'s rows — and **every one of those
    pointers carries an editorial gloss the generator cannot reproduce**. They are a
    curated lead, not a partial enumeration, which is why nothing here removes them and
    why `inline` accepts naming a page twice. `gaps` is the other reasonable answer, and
    it is offered rather than argued for: it lists only what nothing else names, so there
    is no duplication — at the cost of a block whose content depends on hand-written prose
    and therefore churns whenever a gloss is edited.
    """
    text = open(os.path.join(root, rel), "rb").read().decode("utf-8", "replace")
    outside = BLOCK_RE.sub("", text)
    return {m for m in re.findall(r"\[\[([a-z0-9-]+--[a-z0-9-]+)(?:\|[^\[\]]*)?\]\]",
                                  outside)}


def build(root, shape):
    rows = intersections(root)
    unfiled = [s for s, p, t, _ in rows if not p or not t]
    tax_order, tax_label, tax_l1 = V.load_taxonomy(
        os.path.join(root, "lookups", "taxonomy.md"))
    names = place_names(root)
    blocks, overlap = {}, {}
    for rel, make in (
            ("wiki/places-index.md",
             lambda r, sh: places_block(r, names, tax_order, sh)),
            ("wiki/topics-index.md",
             lambda r, sh: topics_block(r, tax_order, tax_label, tax_l1, sh))):
        named = already_named(root, rel)
        overlap[rel] = sorted({s for s, _, _, _ in rows} & named)
        keep = [r for r in rows if r[0] not in named] if shape == "gaps" else rows
        blocks[rel] = render(make(keep, "inline" if shape == "gaps" else shape))
    return rows, unfiled, blocks, overlap


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=".", help="the repository root (default: cwd)")
    ap.add_argument("--shape", default="inline", choices=SHAPES,
                    help="the proposed row shape (default: inline)")
    ap.add_argument("--check", action="store_true", help="exit 1 if a block is out of date")
    ap.add_argument("--diff", action="store_true", help="print the diff it would produce")
    ap.add_argument("--gaps", default=None,
                    help="write the per-page gap table here (jobs 89 and 117's measurement)")
    ap.add_argument("--write", action="store_true", help="write the two index files")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    if not os.path.isdir(os.path.join(root, "wiki", "intersections")):
        print("no wiki/intersections/ under %s" % root, file=sys.stderr)
        return 2
    if not os.path.isfile(os.path.join(root, "lookups", "taxonomy.md")):
        print("no lookups/taxonomy.md under %s" % root, file=sys.stderr)
        return 2

    rows, unfiled, blocks, overlap = build(root, args.shape)
    print("{:,} intersection page(s), shape {}".format(len(rows), args.shape))
    if unfiled:
        print("\nREFUSED: %d page(s) carry no place: or topic: and cannot be filed"
              % len(unfiled))
        for slug in unfiled[:20]:
            print("    %s" % slug)
        return 1

    stale, problems, pending = [], [], []
    for rel, block in sorted(blocks.items()):
        path = os.path.join(root, rel)
        before = open(path, "rb").read().decode("utf-8", "replace")
        after, action = splice(before, block)
        bad = verify(before, after, rel)
        if bad:
            problems.append(bad)
            continue
        named = len(BLOCK_RE.findall(before))
        counted = before.count("[[")
        if after == before:
            print("  %-24s current" % rel)
            continue
        stale.append(rel)
        pending.append((rel, path, before, after))
        print("  %-24s block %s  (%d marker block(s) present, %d links in the file before)"
              % (rel, action, named, counted))

    for rel in sorted(overlap):
        n = len(overlap[rel])
        if n:
            print("  %-24s %d page(s) it names are also named outside the block%s"
                  % (rel, n, " — excluded, shape gaps" if args.shape == "gaps" else ""))
    for line in problems:
        print("PROBLEM %s" % line)
    if problems:
        return 1

    if args.gaps:
        # **Two gap lists, not one.** Job 117 asks for them separately because they are
        # different defects: a page absent from `topics-index.md` has no row at all, while
        # a page absent from a `places-index.md` row is a link missing from a cell that
        # exists. The CSV carries both columns per page so either can be read off it.
        in_p = set(overlap["wiki/places-index.md"])
        in_t = set(overlap["wiki/topics-index.md"])
        with open(args.gaps, "w", encoding="utf-8-sig", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=["slug", "place", "topic", "title",
                                                "in_places_index", "in_topics_index",
                                                "in_neither"])
            wr.writeheader()
            for slug, place, topic, title in rows:
                p_, t_ = slug in in_p, slug in in_t
                wr.writerow({"slug": slug, "place": place, "topic": topic, "title": title,
                             "in_places_index": "yes" if p_ else "no",
                             "in_topics_index": "yes" if t_ else "no",
                             "in_neither": "yes" if not (p_ or t_) else ""})
        print("\n%d row(s) -> %s  (%d missing from places, %d from topics, %d from both)"
              % (len(rows), args.gaps, len(rows) - len(in_p), len(rows) - len(in_t),
                 sum(1 for s_, _, _, _ in rows if s_ not in in_p and s_ not in in_t)))

    if args.diff:
        for rel, _, before, after in pending:
            print()
            print(diff(before, after, rel), end="")

    if args.check:
        print("\n%s" % ("out of date: " + ", ".join(stale) if stale
                        else "both blocks are current"))
        return 1 if stale else 0
    if not args.write:
        print("\ndry run — nothing written. Add --write.")
        return 0
    for rel, path, _, after in pending:
        with open(path, "wb") as fh:
            fh.write(after.encode("utf-8"))
    print("\nwrote %d file(s)." % len(pending))
    return 0


if __name__ == "__main__":
    sys.exit(main())
