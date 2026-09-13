# -*- coding: utf-8 -*-
"""Ingest step 4 + step 11 for the BEN 2026-07-25 run.

Appends the run's sources to the `sources:` list of entity pages that already exist,
then moves every item from new/ to raw/ with its published-date prefix.
"""
import os, re, shutil, sys

sys.stdout.reconfigure(encoding="utf-8")

# entity slug -> source stems to append (only entities that already have a page)
APPEND = {
    "apdp-benin": [
        "2023-12-20-ben-2024-apdp-014-appropriated",
        "2024-12-12-ben-2025-apdp-014-appropriated",
        "2025-12-04-ben-2026-apdp-014-appropriated",
        "2026-04-30-ben-2026-apdp-014-actual",
        "2024-12-03-ben-apdp-cbdh-budgets-devant-parlement",
        "2024-12-11-ben-apdp-budget-2025-640-millions",
    ],
    "asin-benin": [
        "2025-09-24-ben-e-procurement-appel-offres-infructueux",
        "2026-02-06-ben-classifications-croisees-2022-2028-lf-2026",
    ],
    "arcep-benin": [
        "2026-02-06-ben-classifications-croisees-2022-2028-lf-2026",
    ],
    "dgi-benin": [
        "2025-12-04-ben-2026-modernisation-regies-financieres-108-appropriated",
        "2026-04-30-ben-2026-modernisation-regies-financieres-108-actual",
    ],
}


def append_sources():
    touched = 0
    for slug, stems in APPEND.items():
        p = os.path.join("wiki", "entities", slug + ".md")
        if not os.path.exists(p):
            print("  skip (no page):", slug)
            continue
        t = open(p, encoding="utf-8").read()
        m = re.search(r"^sources: \[(.*)\]\s*$", t, re.M)
        if not m:
            print("  skip (no sources list):", slug)
            continue
        existing = m.group(1)
        add = [s for s in stems if s not in existing]
        if not add:
            continue
        new_list = existing + (", " if existing.strip() else "") + ", ".join("[[%s]]" % s for s in add)
        t = t[:m.start()] + "sources: [" + new_list + "]" + t[m.end():]
        t = re.sub(r"^last_reviewed: .*$", "last_reviewed: 2026-07-25", t, count=1, flags=re.M)
        open(p, "w", encoding="utf-8", newline="").write(t)
        print("  appended %d source(s) to %s" % (len(add), slug))
        touched += 1
    return touched


def admit():
    moved = []
    for fn in sorted(os.listdir("new")):
        if not fn.endswith(".md") or fn.lower().startswith("readme"):
            continue
        src = os.path.join("new", fn)
        t = open(src, encoding="utf-8").read()
        m = re.search(r"^published: (\d{4}-\d{2}-\d{2})", t, re.M)
        if not m:
            print("  NO published:", fn)
            continue
        pub = m.group(1)
        base = fn if fn.startswith(pub) else pub + "-" + re.sub(r"^\d{4}-\d{2}-\d{2}-", "", fn)
        # stamp ingested:
        if "\ningested:" not in t:
            t = re.sub(r"^retrieved: (.*)$", r"ingested: 2026-07-25\nretrieved: \1", t, count=1, flags=re.M)
            if "\ningested:" not in t:
                t = t.replace("\n---\n", "\ningested: 2026-07-25\n---\n", 1)
        # staging-only frontmatter keys have no place in raw/
        t = re.sub(r"^sweep_batch: .*\n", "", t, flags=re.M)
        t = re.sub(r"^fiscal_years_covered: .*\n", "", t, flags=re.M)
        open(src, "w", encoding="utf-8", newline="").write(t)
        dst = os.path.join("raw", base)
        if os.path.exists(dst):
            print("  COLLISION, not moved:", base)
            continue
        shutil.move(src, dst)
        moved.append((base, re.search(r'^title: "?(.*?)"?\s*$', t, re.M).group(1),
                      re.search(r"^places: \[(.*)\]", t, re.M).group(1)))
    return moved


if __name__ == "__main__":
    print("step 4 — entity source lists:")
    append_sources()
    print("step 11 — admitting to raw/:")
    rows = admit()
    print("admitted", len(rows))
    with open("/tmp/ben_admitted.txt", "w", encoding="utf-8") as f:
        for base, title, places in rows:
            f.write("%s\t%s\t%s\n" % (places, title, base))
