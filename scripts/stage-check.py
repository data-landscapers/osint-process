#!/usr/bin/env python3
"""stage-check.py — the staged candidates in `new/`, checked at the sweep commit.

Strategic review 5 R84. Ingest corrected the same staging defects seven times on 2026-09-24,
and note 171 fixed 36 more in budget companions: a gate at the writer is cheaper than a
correction at the reader. Run by the cycle parent over `new/` before the sweep stage commits
(`SWEEP-CYCLE.md` → *Commit at boundaries*).

    python scripts/stage-check.py            # report, exit 1 on any finding
    python scripts/stage-check.py --apply    # fix the mechanical ones, report the rest

Per staged `.md` candidate (artefacts are skipped; they follow their companion):

  ingested     `ingested:` present — a staged candidate never carries it (`intake.md` §7);
               --apply removes the line.
  required     a source key the schema requires and staging can know, missing or empty —
               type, title, url, publisher, published, date_precision, date_source,
               body_completeness, retrieved. (places, topics and entities may be blank:
               a blank is what the sweep knew, and ingest fills it.) Reported.
  topics       a value outside `lookups/taxonomy.md`. --apply truncates a compound
               `<slug>--<suffix>` to its valid prefix and drops anything else, leaving
               `topics: []` if nothing survives. A block-list `topics:` is reported only.
  places       a code outside `lookups/countries.csv`. Reported.
  non-verbatim a sweep's own note inside the body — "Sweep note", "[Dating note: …]", a
               truncation note. The body is the source's words only; the note belongs in
               frontmatter `note:`. Reported: moving prose is not a mechanical act.
  completeness `body_completeness: full` over a body that ends on a paywall, an elision
               marker or a truncation note. --apply sets it to `excerpt`, the claim a
               truncated body can make; ingest may upgrade it after a refetch.

Exit 0 when clean (after --apply, when only fixed findings were found); 1 otherwise.
"""
import argparse
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vault_lib as V                                                # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("lint_det", os.path.join(HERE, "lint-deterministic.py"))
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)

REQUIRED = ("type", "title", "url", "publisher", "published", "date_precision",
            "date_source", "body_completeness", "retrieved")
NOTE_RE = re.compile(
    r"^[ \t>*_#(\[]*(?:sweep|staging|capture|dating|fetch|crawler)[ -]note\b"
    r"|^[ \t>*_(]*\[(?:note|sweep|staging|dating|capture|fetch)\b[^\]]*\]"
    r"|^[ \t>*_(\[]*(?:body |capture |text )?truncated (?:at|by|here|—|-)",
    re.I | re.M)
FLOW_TOPICS = re.compile(r"^topics:[ \t]*\[([^\r\n]*)\][ \t]*(?=\r?$)", re.M)


def fm_span(text):
    """(start, end) of the frontmatter block's inner text, or None."""
    if not text.startswith("---"):
        return None
    m = V.FENCE_RE.search(text, 3)
    return (text.find("\n") + 1, m.start()) if m else None


def check_file(path, topics, places, apply_):
    raw = open(path, "rb").read()
    text = raw.decode("utf-8", "replace")
    eol = "\r\n" if b"\r\n" in raw else "\n"
    rel = os.path.relpath(path, V.ROOT).replace(os.sep, "/")
    row, body = V._row(rel, os.stat(path), text)
    fm = row["fm"]
    found, fixed = [], []
    span = fm_span(text)
    if span is None:
        return [("required", "no frontmatter block")], []
    head = text[span[0]:span[1]]
    new_head = head

    if "ingested" in fm:
        if apply_:
            new_head = re.sub(r"^ingested:[^\r\n]*(\r?\n)?", "", new_head, flags=re.M)
            fixed.append(("ingested", "removed"))
        else:
            found.append(("ingested", "a staged candidate never carries `ingested:`"))

    for k in REQUIRED:
        v = fm.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            found.append(("required", "`%s` missing or empty" % k))

    tv = [str(t).strip() for t in V.as_list(fm.get("topics")) if str(t).strip()]
    bad = [t for t in tv if t not in topics]
    if bad:
        m = FLOW_TOPICS.search(new_head)
        if apply_ and m:
            keep = []
            for t in tv:
                t = t if t in topics else t.split("--")[0]
                if t in topics and t not in keep:
                    keep.append(t)
            new_head = new_head[:m.start()] + "topics: [%s]" % ", ".join(keep) + new_head[m.end():]
            fixed.append(("topics", "%s -> [%s]" % (", ".join(bad), ", ".join(keep))))
        else:
            found.append(("topics", "not in taxonomy.md: %s" % ", ".join(bad)))

    badp = [p for p in (str(x).strip() for x in V.as_list(fm.get("places"))) if p and p not in places]
    if badp:
        found.append(("places", "not in countries.csv: %s" % ", ".join(badp)))

    notes = [m.group(0).strip()[:60] for m in NOTE_RE.finditer(body)]
    if notes:
        found.append(("non-verbatim", "sweep text in the body: %s" % " | ".join(notes[:3])))

    truncated = row["d"].get("trunc_markers") or (
        notes and NOTE_RE.search(body.rstrip()[-300:]))
    if fm.get("body_completeness") == "full" and truncated:
        if apply_:
            new_head = re.sub(r"^body_completeness:[^\r\n]*", "body_completeness: excerpt",
                              new_head, count=1, flags=re.M)
            fixed.append(("completeness", "full -> excerpt"))
        else:
            found.append(("completeness", "`full`, but the body ends truncated"))

    if new_head != head:
        out = text[:span[0]] + new_head + text[span[1]:]
        if eol == "\r\n":
            out = out.replace("\r\n", "\n").replace("\n", "\r\n")
        with open(path, "wb") as fh:
            fh.write(out.encode("utf-8"))
    return found, fixed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dir", default=os.path.join(V.ROOT, "new"))
    ap.add_argument("--apply", action="store_true", help="fix the mechanical findings")
    a = ap.parse_args()

    places, topics = L.load_vocab()
    n = n_found = n_fixed = 0
    for name in sorted(os.listdir(a.dir)):
        path = os.path.join(a.dir, name)
        if not name.endswith(".md") or not os.path.isfile(path) or "readme" in name.lower():
            continue
        n += 1
        found, fixed = check_file(path, topics, places, a.apply)
        for kind, what in fixed:
            print("  fixed  %-12s %s · %s" % (kind, what, name))
        for kind, what in found:
            print("  FIND   %-12s %s · %s" % (kind, what, name))
        n_found += len(found)
        n_fixed += len(fixed)
    print("stage-check: %d candidate(s), %d fixed, %d finding(s) left" % (n, n_fixed, n_found))
    return 1 if n_found else 0


if __name__ == "__main__":
    sys.exit(main())
