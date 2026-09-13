# -*- coding: utf-8 -*-
r"""Housekeeping job 27 — apply the decisions in reviews/entity-mint-decisions.csv.

The register is the settled record of what the entity pass decided about every slug
that crossed the schemas.md §5 paging bar: `mint` (a page was written), `reject`
(it stays a tag, with the reason), `merge` (it was a variant or an over-tagged
officeholder and its references now point at the canonical slug) and `drop` (it was
not an entity at all, or the institution was already tagged on every source).

This script applies only the two that rewrite files — `merge` and `drop`.

Three things it is careful about, all learned the hard way:

* **Line endings.** The repo is mixed CRLF/LF and the edit is a substring replacement
  on the raw text, so nothing is normalised. A `$` anchor without `\r?` silently skips
  every CRLF file; a `\s*$` swallows the `\r` and drops the line to LF.
* **`entities:` is a list of single-bracket tokens** — `entities: [[a], [b]]` — not a
  list of `[[wikilinks]]`. Reading it as wikilinks matches only the first element.
* **Scope.** Some slugs collided: one tag standing for two entities (`anpdp` was both
  Algeria's and Sao Tome's data-protection authority; `arpce` could have been either
  Congo's or Algeria's), or one officeholder whose portfolio changed mid-corpus. Those
  rows carry a scope and are resolved per file, from the file's own frontmatter:

      place:XXX       apply only where `places:` names XXX
      before:DATE     apply only to sources dated before DATE (from the filename)
      from:DATE       apply only to sources dated on or after DATE
      notfile:TEXT    apply except where the filename contains TEXT

  An unscoped row applies everywhere, including `[[wikilinks]]` and the finance
  records' `financier_slug:` / `recipient_slug:` fields. A scoped row applies only
  inside the files it selects.

Usage:  python scripts/entity-mint-apply.py [--write]
"""
import csv, glob, io, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "reviews", "entity-mint-decisions.csv")
DIRS = ["raw", "wiki", "reviews", "sweep", "documentation", "new", "new-queue",
        "budget-archive", "prototypes", "lookups"]

ENTITIES_LINE = re.compile(r"(?m)^(entities:[ \t]*)\[(.*)\][ \t]*(\r?)$")
DATE_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


def load():
    """-> (global map, scoped rules). A map value of None means 'drop the tag'."""
    glob_map, scoped = {}, []
    for r in csv.DictReader(io.open(REG, encoding="utf-8")):
        if r["decision"] not in ("merge", "drop"):
            continue
        target = r["target"].strip() or None
        if r["scope"].strip():
            scoped.append((r["slug"], target, r["scope"].strip()))
        else:
            glob_map[r["slug"]] = target
    return glob_map, scoped


def scope_matches(scope, path, text):
    kind, _, val = scope.partition(":")
    if kind == "place":
        m = re.search(r"(?m)^places:[ \t]*\[(.*?)\]", text[:4000])
        return bool(m) and val in m.group(1)
    if kind in ("before", "from"):
        m = DATE_IN_NAME.search(os.path.basename(path))
        if not m:
            return False
        return m.group(1) < val if kind == "before" else m.group(1) >= val
    if kind == "notfile":
        return val not in os.path.basename(path)
    raise SystemExit("unknown scope: %s" % scope)


def rewrite_entities(text, m):
    def fix(mo):
        head, body, cr = mo.group(1), mo.group(2), mo.group(3)
        seen, out = set(), []
        for tok in re.findall(r"\[([^\[\]]+)\]", body):
            tok = tok.strip()
            if tok in m:
                tok = m[tok]
                if tok is None:          # drop
                    continue
            if tok not in seen:
                seen.add(tok)
                out.append(tok)
        return head + "[" + ", ".join("[%s]" % t for t in out) + "]" + cr
    return ENTITIES_LINE.sub(fix, text)


def main():
    write = "--write" in sys.argv
    glob_map, scoped = load()
    if not glob_map and not scoped:
        raise SystemExit("nothing to apply")

    def link_pat(keys):
        return re.compile(r"\[\[(" + "|".join(re.escape(k) for k in
                          sorted(keys, key=len, reverse=True)) + r")(\]\]|\|)")

    def slug_pat(keys):
        return re.compile(r"(?m)^((?:financier|recipient)_slug:[ \t]*)(" +
                          "|".join(re.escape(k) for k in sorted(keys, key=len, reverse=True)) +
                          r")[ \t]*(\r?)$")

    renames = {k: v for k, v in glob_map.items() if v}
    gl_link = link_pat(renames) if renames else None
    gl_slug = slug_pat(renames) if renames else None

    touched, hits, dropped_links = 0, collections.Counter(), collections.Counter()
    scope_hits = collections.Counter()
    unscoped_elsewhere = collections.Counter()
    outcome = collections.defaultdict(collections.Counter)
    for d in DIRS:
        for f in sorted(glob.glob(os.path.join(ROOT, d, "**", "*.md"), recursive=True)):
            raw = io.open(f, encoding="utf-8", errors="replace", newline="").read()
            m = dict(glob_map)
            # Scoped rules resolve from a source's own frontmatter, so they only make
            # sense on `raw/`. A concept page lists thirty countries and would match
            # both halves of a collision — `gov.protect.md` names both DZA and STP, so
            # either anpdp rule would fire and the last would silently win. Those are
            # reported instead, and fixed by reading the page.
            if d == "raw":
                for slug, target, scope in scoped:
                    if scope_matches(scope, f, raw):
                        m[slug] = target
                        if re.search(r"\[" + re.escape(slug) + r"\]", raw):
                            scope_hits["%s [%s] -> %s" % (slug, scope, target or "(dropped)")] += 1
            else:
                for slug, _t, _s in scoped:
                    if re.search(r"(\[|\[\[)" + re.escape(slug) + r"(\]|\]\]|\|)", raw):
                        unscoped_elsewhere["%s in %s" % (slug, os.path.relpath(f, ROOT))] += 1
            new = raw
            if gl_link:
                new = gl_link.sub(lambda mo: "[[" + renames[mo.group(1)] + mo.group(2), new)
                new = gl_slug.sub(lambda mo: mo.group(1) + renames[mo.group(2)] + mo.group(3), new)
            local = {k: v for k, v in m.items() if k not in renames and v}
            if local:
                lp, sp = link_pat(local), slug_pat(local)
                new = lp.sub(lambda mo: "[[" + local[mo.group(1)] + mo.group(2), new)
                new = sp.sub(lambda mo: mo.group(1) + local[mo.group(2)] + mo.group(3), new)
            # a slug being dropped must not be left behind as a dangling [[link]]
            for k, v in m.items():
                if v is None and re.search(r"\[\[" + re.escape(k) + r"(?:\]\]|\|)", new):
                    dropped_links[k] += 1
            new = rewrite_entities(new, m)
            if new != raw:
                for k in m:
                    n = len(re.findall(r"\[" + re.escape(k) + r"\]", raw))
                    if n:
                        hits[k] += n
                        outcome[k][m[k] or "(dropped)"] += n
                touched += 1
                if write:
                    io.open(f, "w", encoding="utf-8", newline="").write(new)

    print("%s %d files; %d slugs rewritten" %
          ("rewrote" if write else "would rewrite", touched, len(hits)))
    for k, n in hits.most_common(15):
        print("   %-52s %3d -> %s" % (k[:52], n,
              ", ".join("%s x%d" % (t, c) for t, c in outcome[k].most_common())))
    if scope_hits:
        print("\n  scoped rules, files matched:")
        for k, n in sorted(scope_hits.items()):
            print("     %-72s %d" % (k, n))
    if unscoped_elsewhere:
        print("\n  ⚠ collided slugs referenced outside raw/ — resolve by reading the page:")
        for k, n in sorted(unscoped_elsewhere.items()):
            print("     %s" % k)
    if dropped_links:
        print("\n  ⚠ dropped slugs still present as [[wikilinks]] (fix by hand):")
        for k, n in dropped_links.most_common():
            print("     %-50s %d" % (k, n))


if __name__ == "__main__":
    main()
