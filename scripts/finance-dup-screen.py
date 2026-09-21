#!/usr/bin/env python3
r"""finance-dup-screen.py — non-state finance records that may be the same deal held twice.

Housekeeping job 140, from `notes-for-osint` 149's closing suggestion. Two unit reviews in
two countries each turned up one duplicate, and each cost real money on the published page:
the DR Congo pair overstated that country by US$170m, the Cameroon pair by US$46m, and the
Cameroon pair split one loan across two sectors so a whole subject total rested on it.

**The screen.** Cluster on `financier_slug` + place + commitment year, which is too coarse on
its own (171 clusters, 527 records), then require a **recipient-name token overlap of 50% or
better** with generic tokens stripped. That is what cuts it to a readable list and still
returns the confirmed Cameroon pair.

**It reports, it never edits.** Disposition is `CLAUDE.md` -> *Duplicates*: drop, replace, or
keep both. **A facility and a drawdown under it, or two tranches of one project, are *keep
both*** with each record saying so -- `boc-cmr-002` is the worked example. A screen hit is a
question, not a finding.

Usage:
  python scripts/finance-dup-screen.py              every pair, grouped by financier
  python scripts/finance-dup-screen.py --place COG  one place
  python scripts/finance-dup-screen.py --json       machine-readable, for a worklist

Exit 0 always: the screen is diagnostic and never gates a pass.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FM = {k: re.compile(r'^%s:\s*(.*?)\s*$' % k, re.M)
      for k in ('financier_slug', 'recipient_slug', 'deal_id', 'finance_origin', 'title')}
PLACES = re.compile(r'^places:\s*\[([A-Z]{3})', re.M)
ROW = re.compile(r'^\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*$', re.M)

# Words that say nothing about which deal this is.
GENERIC = {
    'the', 'of', 'and', 'for', 'de', 'la', 'le', 'du', 'des', 'et', 'ltd', 'limited',
    'plc', 'sa', 'sarl', 'inc', 'group', 'holdings', 'holding', 'company', 'co',
    'national', 'ministry', 'government', 'republic', 'state', 'authority', 'agency',
    'fund', 'project', 'programme', 'program', 'bank', 'telecom', 'telecoms',
    'telecommunications', 'unspecified', 'recipient', 'africa', 'african',
    # A recipient-name token that half the corpus shares is not evidence of a duplicate.
    # The gates-foundation grant pool is what made this list long: 289 of the first run's
    # 380 pairs matched on 'foundation' or 'university' alone.
    'foundation', 'university', 'universite', 'universidade', 'institute', 'institut',
    'international', 'development', 'global', 'association', 'corporation', 'services',
    'service', 'solutions', 'technologies', 'technology', 'digital', 'mobile', 'health',
    'center', 'centre', 'council', 'society', 'trust', 'college', 'school', 'research',
    'public', 'private', 'sector', 'general', 'regional', 'nations', 'united', 'world',
}

# Two records naming one body share more than one distinctive word. A single shared
# token at 50% is a two-word name colliding, not a duplicate.
MIN_SHARED = 2


def tokens(s):
    return {w for w in re.split(r'[^a-z0-9]+', (s or '').lower())
            if w and w not in GENERIC and len(w) > 2}


def read(path):
    t = open(path, 'rb').read().decode('utf-8', 'replace')
    if 'finance_origin: non-state' not in t:
        return None
    out = {k: (m.group(1).strip().strip('"') if (m := r.search(t)) else '')
           for k, r in FM.items()}
    out['place'] = (m.group(1) if (m := PLACES.search(t)) else '')
    cells = {k.strip(): v.strip() for k, v in ROW.findall(t)}
    out['year'] = cells.get('Commitment year', '')
    out['amount'] = cells.get('Commitment (USD)', '')
    out['recipient'] = cells.get('Recipient', '') or out['recipient_slug']
    out['path'] = path
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().split('\n')[0])
    ap.add_argument('--place', help='one ISO3 place')
    ap.add_argument('--root', default='raw')
    ap.add_argument('--overlap', type=float, default=0.5,
                    help='recipient token overlap required (default 0.5)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)

    recs = []
    for dp, _, fns in os.walk(a.root):
        for fn in fns:
            if fn.endswith('.md'):
                r = read(os.path.join(dp, fn).replace(os.sep, '/'))
                if r and (not a.place or r['place'] == a.place):
                    recs.append(r)

    clusters = collections.defaultdict(list)
    for r in recs:
        if r['financier_slug'] and r['year']:
            clusters[(r['financier_slug'], r['place'], r['year'])].append(r)

    pairs = []
    for key, group in clusters.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a_, b_ = group[i], group[j]
                ta, tb = tokens(a_['recipient']), tokens(b_['recipient'])
                if not ta or not tb:
                    continue
                shared = ta & tb
                ov = len(shared) / min(len(ta), len(tb))
                if ov >= a.overlap and len(shared) >= MIN_SHARED:
                    pairs.append(dict(financier=key[0], place=key[1], year=key[2],
                                      overlap=round(ov, 2), a=a_, b=b_))

    if a.json:
        print(json.dumps([{k: (v if not isinstance(v, dict)
                               else {x: v[x] for x in ('path', 'deal_id', 'recipient',
                                                       'amount', 'title')})
                           for k, v in p.items()} for p in pairs],
                         indent=1, ensure_ascii=False))
        return 0

    print('%d non-state record(s); %d cluster(s) on financier+place+year; '
          '%d pair(s) at overlap >= %.0f%%'
          % (len(recs), sum(1 for g in clusters.values() if len(g) > 1),
             len(pairs), a.overlap * 100))
    by = collections.Counter(p['financier'] for p in pairs)
    print('by financier: ' + ', '.join('%s %d' % kv for kv in by.most_common()))
    print()
    for p in sorted(pairs, key=lambda p: (p['financier'], p['place'], p['year'])):
        print('%-22s %s %s  overlap %.0f%%' % (p['financier'], p['place'], p['year'],
                                               p['overlap'] * 100))
        for r in (p['a'], p['b']):
            print('    %-14s %-12s %s' % (r['deal_id'][:14], r['amount'][:12],
                                          r['path'].split('/')[-1][:86]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
