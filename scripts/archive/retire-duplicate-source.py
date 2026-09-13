"""Retire one narrative source as a LINT #7 duplicate — the whole retirement, in one move.

Usage:  python scratchpad/drop-source.py <drop-slug> <keep-slug> "<reason>"

Does the four things #7 requires and refuses to do any of them by halves:
  1. rewires every `[[drop-slug]]` citation in `wiki/` to the keeper;
  2. deletes the `raw/` file;
  3. removes its row from `lookups/raw-url-index.csv` (the stale row is the dangerous half —
     it silently drops a live candidate against a source no longer held);
  4. appends the ruling to `reviews/source-duplicate-decisions.csv`.

Refuses if either slug does not resolve, so a typo cannot delete the wrong file.
"""
import csv, glob, os, re, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
drop, keep, reason = sys.argv[1], sys.argv[2], sys.argv[3]

idx = {os.path.basename(p)[:-3]: p for p in glob.glob("raw/**/*.md", recursive=True)}
if drop not in idx:
    sys.exit(f"refusing: drop slug does not resolve — {drop}")
if keep not in idx:
    sys.exit(f"refusing: keep slug does not resolve — {keep}")

# 1. rewire citations — raw/ as well as wiki/. A retired slug is also named in other
#    sources' hub_line_sources lists and ingest prose; stopping at wiki/ leaves those dangling.
rewired = []
for p in glob.glob("wiki/**/*.md", recursive=True) + glob.glob("raw/**/*.md", recursive=True):
    with open(p, encoding="utf-8", newline="") as fh:
        s = fh.read()
    if drop not in s:
        continue
    out = s.replace(f"[[{drop}]]", f"[[{keep}]]").replace(f"[{drop}]", f"[{keep}]")
    if out != s:
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(out)
        rewired.append(p)

# 2. delete the file
path = idx[drop]
os.remove(path)

# 3. prune the index row
rows = list(csv.reader(open("lookups/raw-url-index.csv", encoding="utf-8", newline="")))
kept = [r for r in rows if not (len(r) > 2 and r[2].replace("\\", "/").endswith(f"{drop}.md"))]
pruned = len(rows) - len(kept)
with open("lookups/raw-url-index.csv", "w", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerows(kept)

# 4. record the ruling
with open("reviews/source-duplicate-decisions.csv", "a", encoding="utf-8", newline="") as fh:
    csv.writer(fh).writerow([keep, drop, "DROP", "2026-08-21", reason])

print(f"dropped {drop}\n  kept {keep}\n  citations rewired in {len(rewired)} page(s): "
      f"{', '.join(rewired) or 'none'}\n  index rows pruned: {pruned}")
