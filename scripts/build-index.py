#!/usr/bin/env python3
"""build-index.py — rebuild `index/`, the vault's derived index.

The index is **rebuildable, disposable and untracked**. Its only writer is a
from-scratch rebuild — there is no append-at-ingest path, which is what makes it
incapable of drifting out of step with the vault, and it costs about a second
over 10k artefacts. It is not committed: a 10k-line artefact rewritten on every
rebuild would churn every commit, grow `.git` against `PRUNE.md`'s purpose, and
collide with the other writer in the vault, for a file nobody reads.

What it holds, in `index/`:

  files.jsonl   one row per artefact — `path`, the file's **frontmatter verbatim**
                (`fm`), and a derived block (`d`): slug, kind, shard, file_date,
                normalised url, registrable domain, word count, body sha1,
                truncation markers, section sizes, frontmatter warnings.
  links.jsonl   the citation graph — frontmatter `sources`/`entities`/`artefact`/
                `cite_through` edges and body `[[wikilinks]]`, with line numbers.
  meta.json     build stamp, counts, and the mtime high-water mark the staleness
                check reads.
  vault.db      a scratch SQLite flattening of both, for ad-hoc SQL. Built on
                demand by `--sql` (and by `--db`), and **deleted by any rebuild
                that does not refresh it** -- so it is either current or absent,
                never a stale copy of an older vault, and its mtime carries no
                meaning worth reading. It is on no citation-resolution path:
                `build_db()` is its only writer and `--sql` its only reader.

Keeping `fm` verbatim rather than mapping it onto fixed columns is deliberate:
144 distinct keys are in use across five page types plus the finance and budget
extensions, and a fixed schema would need re-specifying every time a key is
minted. It also means a row *is* a frontmatter object, so the schema file can
validate index rows directly.

Usage:
  python scripts/build-index.py                 rebuild (prints a summary)
  python scripts/build-index.py --db            rebuild + keep index/vault.db
  python scripts/build-index.py --check         report freshness, build nothing
  python scripts/build-index.py --if-stale      rebuild only if the vault moved
  python scripts/build-index.py --sql "SELECT kind, count(*) FROM files GROUP BY 1"

`--check` exits 1 when the index is stale, so a pass can gate on it. Everything
else exits 0. Consumers normally never run this at all: `vault_lib.load_index()`
rebuilds automatically when the vault has moved underneath it.
"""
import argparse
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vault_lib as V                                                # noqa: E402

# The vault is UTF-8 and this console is cp1252; a title with an en dash in it
# would otherwise kill the summary after the work was done.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def summarise(meta):
    rows = V.load_index(auto=False)
    kinds = Counter(r["d"].get("kind") or "?" for r in rows)
    print(f"index built {meta['built']} in {meta['build_seconds']}s")
    print(f"  {meta['files']:,} files, {meta['links']:,} links, "
          f"{meta['fm_warning_files']:,} files with frontmatter warnings")
    print("  " + ", ".join(f"{k} {n:,}" for k, n in kinds.most_common(10)))
    sizes = []
    for p in (V.FILES_JSONL, V.LINKS_JSONL, V.DB_PATH):
        if os.path.exists(p):
            sizes.append(f"{os.path.basename(p)} {os.path.getsize(p)/1e6:.1f} MB")
    print("  " + ", ".join(sizes))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--db", action="store_true", help="also build index/vault.db")
    ap.add_argument("--check", action="store_true",
                    help="report freshness and exit 1 if stale; build nothing")
    ap.add_argument("--if-stale", action="store_true",
                    help="rebuild only when the vault has moved")
    ap.add_argument("--sql", help="run one query against index/vault.db and print rows")
    a = ap.parse_args()

    if a.check:
        state, meta, reason = V.index_state()
        built = meta["built"] if meta else "never"
        print(f"index: {state}" + (f" - {reason}" if reason else "") + f" (built {built})")
        return 0 if state == "fresh" else 1

    if a.sql:
        V.ensure_fresh(db=False)
        if not os.path.exists(V.DB_PATH) or \
           os.path.getmtime(V.DB_PATH) < os.path.getmtime(V.FILES_JSONL):
            V.build_db()
        import sqlite3
        con = sqlite3.connect(V.DB_PATH)
        cur = con.execute(a.sql)
        if cur.description:
            print(" | ".join(c[0] for c in cur.description))
            for row in cur.fetchall():
                print(" | ".join("" if v is None else str(v) for v in row))
        con.close()
        return 0

    if a.if_stale:
        state, meta, reason = V.index_state()
        if state == "fresh":
            print(f"index fresh (built {meta['built']}) - nothing to do")
            return 0
        print(f"index {state}: {reason}")

    meta = V.build_index(db=a.db)
    summarise(meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
