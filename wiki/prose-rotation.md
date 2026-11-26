<!-- reader: cc; type: runbook -->
# prose-rotation.md — ten intersection pages a night, rewritten to the sheet

Called by `WIKI-SYNC.md` → *The pass*, after Phase B, every night, whether or not Phase B had a queue. It is not a separate pass: its pages are written inside the lint stage's write-set and its result rides Phase B's log line. *(Strategic review 8 R191, 2026-11-26; R147 stands: the whole sheet binds the wiki.)*

**Why.** Phase B only rewrites the pages a night's sources land on, so a page nobody cites tonight keeps its old prose for ever. On 2026-11-26, 8,300 of 11,810 wiki blocks failed `X:\documentation\prose-style.md` and 309 intersection pages were over their line.

## When it stands down

`python scripts/usage-log.py --opened-above 70` exits 1: the rotation does not run that night, the same test that holds the maturity-study pulls. No reading means it runs. A night with no Phase B queue still runs the rotation.

## The pages

`python scripts/prose-rotation.py --pick 20` prints the next twenty. The order is the script's: over-line pages first, least over first, then never-rotated pages, then the oldest rotated. The parent takes the first ten that tonight's Phase B page map does not name, since those pages have just been written to the sheet.

## The rewrite

One sub-agent per page, in its own scratch folder, given the page path and nothing else. For each page:

1. `python scripts/page-length.py <page>` and note the effective words: the `before`.
2. Read `prose-style.md`, then `prose-exemplars.md` beside it, last, just before writing.
3. Rewrite the whole page as current-state synthesis to the sheet. Every claim keeps its inline wikilink citation on the claim it supports, and every dated figure stays dated. Events stay in their source pages (`CLAUDE.md` → *Structure*). Commentary and officeholder names give way before a fact; a fact gives way before a citation is lost.
4. **The page ends under its line and never longer than it began.** Where it cannot hold everything, what it drops stays in the cited source, which `raw/` already holds; the source's slug stays cited on the page wherever a claim from it remains.
5. Frontmatter is untouched except `last_reviewed`, set to today.
6. `python scripts/prose-rotation.py --done <page> --before <N>`. Exit 2 means the page grew; exit 3 means it dropped the wiki's last citation of a slug, which it names. Either way the agent fixes the rewrite once, then reverts the page with `git checkout -- <page>` if it still fails. It does not try a third time, and only exit 0 records the page.

A page the agent cannot bring under its line without dropping a cited claim stays over, keeps its rewrite if shorter, and is recorded as done; the script sends it to the back of the queue for 30 days.

## After the slices

The parent reverts any changed page that `prose-rotation.csv` has no row for tonight, since only a passing `--done` writes one. The pages are committed with the lint stage, and the commit body names them. Phase B's log line gains `rotated N`. There is no new lint: CORPUS's nightly wiki prose count and `pages_over_line` measure the rotation.
