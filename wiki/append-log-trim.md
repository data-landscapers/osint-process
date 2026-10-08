<!-- reader: cc; type: spec -->
# append-log-trim.md — the sub-agent brief for trimming an append-log page back to synthesis

*(Written 2026-09-24, from housekeeping jobs 189–202, which trimmed 317 append-log intersections with this brief and the scripts it names. It is the driver for the **append-log** flavour of `operations.md` §8; a housekeeping job that registers append-log pages cites it as its remedy.)*

**How a job uses it.** The session reads the job's page list, splits it into groups of four to six pages, and dispatches one sub-agent per group with a one-paragraph prompt: *read `wiki/append-log-trim.md` and follow it; your pages are …*. Pages never overlap between agents. When every agent has reported, `python scripts/trim-job.py <N>` checks the whole job against its finish line, and `python scripts/trim-job.py <N> --commit "<slice label>" <calls-file>` logs, commits, pushes and strikes it. The calls file is the commit body's paragraph of judgement calls — corrections made from `raw/`, and conflicts stated rather than resolved — written by the session from the agents' reports. Mirror after, per `SWEEP-CYCLE.md` → *Mirror*.

---

## The brief — what each sub-agent does

You edit **only** the pages you are assigned, under `wiki/intersections/`. Do not commit, do not touch any other file, do not run git commands that change state.

### Why

`CLAUDE.md` → *Structure*: synthesis pages hold current state, not chronology. These pages have accreted a dated section per nightly ingest ("X happened (2026-09-14)") and now read as a log of what was ingested. Exemplars of the finished shape: `wiki/intersections/kenya--dpi-govtech.md`, `sudan--dpi-pay.md`, `south-africa--tech-ai.md`.

- **Rewrite the body as current-state synthesis in 5–9 undated thematic sections.** Headings name a theme ("Election technology", "Revenue administration and customs"), never a date or a date range.
- **Keep every dated figure and every dated absence** ("no published figure since 2018 (checked 2026-09-22)"). Time-varying figures stay written dated: "ranked 156th (2020)", never "ranks 156th". Money stays in the announcing party's currency; any USD conversion stays dated.
- **Collapse runs of events to the current position**, with at most one dated prior where the trajectory means something. A sequence "announced → consulted → gazetted → delayed" becomes the current state plus, if meaningful, the one prior step.
- **Where sources disagree, state the conflict once** — both values, both sources — never silently pick one.
- **Cut repetition hard**: these pages restate the same finding under several dated headings. Say it once, in the right theme. Aim for roughly 35–50% of the current body; a page dense with dated figures or statute detail may keep more, but it must read as synthesis.
- **Add nothing from your own knowledge.** Everything on the rewritten page comes from the page as it stands, or from the raw source it cites if a detail needs checking (`raw/` is greppable by slug filename). Where the page contradicts its own raw source, the raw source wins; say so in your report.
- House style: cautiously outspoken, evidence-led, polemical about systems not people, for non-technical governance readers.

### Must survive — `scripts/trim-verify.py` checks all of these

1. **Frontmatter**: every field untouched except `last_reviewed:` (set to today) and `sources:`, to which you **add** any raw source slug the body cites (`[[slug]]`) that is missing. Never remove a `sources:` slug. Keep the `[[a], [b]]` list format exactly.
2. **Every `[[link]]` in the current body appears somewhere in the new file** (body, `## Links` or `## Sources`) — place codes, concept slugs, entity slugs, other intersections, every source citation. A self-link to the page's own slug may go. Keep citations inline on the claims they support; when you cut a sentence, move its citation onto the surviving sentence that carries the same point.
3. **`## Links` and `## Sources` stay at the bottom** (add to them, never remove). A page with neither gets a `## Links`; a `## See also`, `## Related` or `## Places` may be renamed `## Links` with its content kept. A `## Links` sitting mid-page moves to the bottom.
4. **A `## Length — reviewed …` section is deleted** — a ruling on the page as it was, which no longer exists.
5. **An `## Extracted from [[<concept>]] → By place …` section is folded into the themes** (most of it duplicates the body) and replaced by a one-line pointer in `## Links`, e.g. `By-place summary: [[tech.ai]]`. Its links must survive (rule 2).
6. **Line endings match the page's HEAD endings exactly** — most pages are LF, some CRLF. The verifier compares against HEAD and flags any mismatch. UTF-8, no BOM.
7. **One line per paragraph. Never hard-wrap.**
8. **The lede** (the first paragraph under the `# Title` heading) states the page's current reading. An italic extraction note standing in as the lede is replaced.

### Verify before you report

From `C:\OSINT`:

```
python scripts/trim-verify.py <slug> [<slug> ...]
python scripts/page-index.py wiki/intersections/<slug>.md
python scripts/reflow-md.py --check wiki/intersections/<slug>.md
```

`trim-verify.py` must print `OK` for each page. `page-index.py` should show 5–9 content sections, none dated in the heading. Fix and re-run until clean. **The verifier's "before" word count stops at the first `## Links`**, so it undercounts a page whose old `## Links` sat mid-page; say so rather than chase it.

### Report back — under 150 words

Per page: words before → after and section count. Then any judgement calls: a conflict stated, a claim corrected because the cited raw source said otherwise, anything left unresolved. Do not paste page content.
