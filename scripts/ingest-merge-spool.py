#!/usr/bin/env python3
"""Merge ingest slice spool files into the canonical logs.

Written 2026-07-31 for the sweep-cycle Day-2 update-wiki run. INGEST.md step 11
requires each slice to write its sweep-url_log line and its Phase B delta at the
item's disposition, so the record survives a slice that dies. With ~19 slices
running concurrently, direct appends to one file cannot be done safely with the
edit tooling, so each slice appends to its own spool file and this merges them.
The per-item-at-disposition property is preserved: the line is written by the
slice, at the item, to durable disk.

Usage:
    python scripts/ingest-merge-spool.py            # merge and clear the spool
    python scripts/ingest-merge-spool.py --dry      # report only
    python scripts/ingest-merge-spool.py --help     # this text, and NOTHING else

**`--help` must never merge.** Until 2026-08-25 there was no argument guard at
all: the only inspection of `sys.argv` was the `--dry` test, so any other flag —
`--help` included — fell through to a live merge. A slice probing `--help` on the
2026-08-25 cycle filed 20 sibling URL lines under the stale default heading below
and archived six spool files. An unrecognised argument is now an error, not a run.
"""
import os, re, sys, io, glob

ARGS = set(sys.argv[1:])
KNOWN = {'--dry'}
if ARGS & {'--help', '-h'}:
    print(__doc__)
    sys.exit(0)
_unknown = ARGS - KNOWN
if _unknown:
    print('ingest-merge-spool: unrecognised argument(s): %s' % ', '.join(sorted(_unknown)),
          file=sys.stderr)
    print('run with --help for usage; refusing to merge on an argument I do not know.',
          file=sys.stderr)
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOOL = os.path.join(ROOT, 'logs', '_spool')

# **The readers and the archiver take their patterns from here, once.** They were
# written out separately and drifted immediately: the archiver said 'pending-*.txt'
# while the reader says 'pending-*.md', so a merged pending spool was never retired
# and would have been merged a second time on the next run (2026-08-25).
PAT_URL = 'url-*.txt'
PAT_PENDING = 'pending-*.md'
PAT_ENTITY = 'entity-*.txt'
MERGED_PATTERNS = (PAT_URL, PAT_PENDING, PAT_ENTITY)
DRY = '--dry' in sys.argv
# **The default heading is computed, never a frozen date.** It was hard-coded to
# 2026-07-31 until 2026-08-25, so every later run that did not set the env var filed
# its lines under a heading nearly a month stale. `HH:MM` is required on the heading.
import datetime as _dt
SECTION = os.environ.get(
    'INGEST_SPOOL_SECTION',
    _dt.datetime.now().strftime('## %Y-%m-%d %H:%M - ingest'))


def read_lines(pattern):
    out = []
    for p in sorted(glob.glob(os.path.join(SPOOL, pattern))):
        with open(p, encoding='utf-8', errors='replace') as f:
            for ln in f:
                ln = ln.rstrip('\r\n')
                if ln.strip():
                    out.append(ln)
    return out


def merge_urls():
    lines = read_lines(PAT_URL)
    seen, uniq = set(), []
    for ln in lines:
        parts = [p.strip() for p in ln.split('|')]
        key = parts[-1].lower() if parts else ln
        if key in seen:
            continue
        seen.add(key)
        uniq.append(ln)
    if not uniq:
        return 0
    path = os.path.join(ROOT, 'logs', 'sweep-url_log.md')
    with open(path, encoding='utf-8', newline='') as f:
        t = f.read()
    nl = '\r\n' if '\r\n' in t else '\n'
    block = SECTION + nl + nl + nl.join(uniq) + nl + nl
    i = t.index('## 2026-')
    if not DRY:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(t[:i] + block + t[i:])
    return len(uniq)


def merge_pending():
    lines = read_lines(PAT_PENDING)
    if not lines:
        return 0
    path = os.path.join(ROOT, 'logs', 'ingest-pending-writes.md')
    header = ('# ingest-pending-writes.md - Phase B queue\n\n'
              'Transient. Non-empty means Phase B is outstanding. Deleted when drained.\n\n')
    existing = ''
    if os.path.exists(path):
        existing = open(path, encoding='utf-8', errors='replace').read()
    else:
        existing = header
    if not DRY:
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(existing.rstrip('\n') + '\n' + '\n'.join(lines) + '\n')
    return len(lines)


def apply_entities():
    """Append the source slug to sources: on entity pages that already exist."""
    reqs = {}
    for ln in read_lines(PAT_ENTITY):
        if '|' not in ln:
            continue
        slug, src = [x.strip() for x in ln.split('|', 1)]
        slug = slug.strip('[]')
        src = src.strip('[]').removesuffix('.md')
        if slug and src:
            reqs.setdefault(slug, set()).add(src)
    applied = missing = 0
    for slug, srcs in sorted(reqs.items()):
        p = os.path.join(ROOT, 'wiki', 'entities', slug + '.md')
        if not os.path.exists(p):
            missing += 1
            continue
        with open(p, encoding='utf-8', newline='') as f:
            t = f.read()
        nl = '\r\n' if '\r\n' in t else '\n'
        m = re.search(r'^sources:\s*(.*)$', t, re.M)
        add = [s for s in sorted(srcs) if ('[%s]' % s) not in t]
        if not add:
            continue
        if m:
            cur = m.group(1).strip()
            items = re.findall(r'\[([^\[\]]+)\]', cur)
            items += add
            newline_ = 'sources: [' + ', '.join('[%s]' % i for i in items) + ']'
            t2 = t[:m.start()] + newline_ + t[m.end():]
        else:
            # insert before closing frontmatter delimiter
            parts = t.split('---', 2)
            if len(parts) < 3:
                missing += 1
                continue
            newline_ = 'sources: [' + ', '.join('[%s]' % i for i in add) + ']'
            t2 = parts[0] + '---' + parts[1].rstrip() + nl + newline_ + nl + '---' + parts[2]
        if not DRY:
            with open(p, 'w', encoding='utf-8', newline='') as f:
                f.write(t2)
        applied += len(add)
    return applied, missing, len(reqs)


if __name__ == '__main__':
    u = merge_urls()
    p = merge_pending()
    a, miss, tot = apply_entities()
    print('url lines merged: %d' % u)
    print('pending-write deltas merged: %d' % p)
    print('entity source-appends applied: %d across %d entities (%d slugs had no page)'
          % (a, tot - miss, miss))
    # **Archive whenever anything merged, not only when URL lines did.** The guard
    # was `if not DRY and u:` until 2026-08-25, so a run that merged pending deltas
    # but no URL lines left its spool in place — and the next run merged those same
    # deltas a second time.
    if not DRY and (u or p or a):
        n = 0
        # **Archive only what this script actually reads.** It globbed '*' until
        # 2026-08-25 and so retired `ingested-*` spools it never merges — 14 sibling
        # rows were one run away from being lost silently on the 2026-08-25 cycle.
        archivable = set()
        for pat in MERGED_PATTERNS:
            archivable.update(glob.glob(os.path.join(SPOOL, pat)))
        for f in sorted(archivable):
            if f.endswith('.done'):
                continue          # already archived by an earlier merge
            dest, i = f + '.done', 2
            while os.path.exists(dest):
                dest, i = '%s.%d.done' % (f, i), i + 1   # a resumed run's tail
            os.rename(f, dest)
            n += 1
        print('spool archived (.done): %d files' % n)
