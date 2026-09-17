# CLAUDE.md — Data Landscapers Intelligence Wiki

*(In force from 2026-07-20. This file is principles; CC reasons from here. **Every standalone runnable process lives in the repo root as its own procedure file; `wiki/` holds the drivers and specs those processes call, and `wiki/reference.md` holds the shared schemas, thresholds and vocabularies they draw on.** `wiki/index.md` → *Processes* is the directory of them — every trigger phrase and what it does — and is **kept current** whenever a process is added, moved or retired: the same edit that creates or moves the file updates the index. This file names no process, because a second list is a list that goes stale — the one deleted here had drifted by six.)*

## Writing

**One line per paragraph. Never wrap by hand.** A hard-wrapped paragraph is harder to read, and it diffs badly: change one word near the start and every following line reflows, so the diff shows a rewritten paragraph instead of a changed word. This holds for everything CC writes — process files, wiki pages, logs, registers, commit bodies. It does **not** apply where the break carries meaning: frontmatter, code blocks, tables, and the verbatim body of a source in `raw/`, which is someone else's text and immutable besides. `scripts/reflow-md.py` applies it; `--check` reports what still wraps.

## Purpose

A compounding intelligence base on data governance and digital transformation across Africa, built to feed the long-form output at data-landscapers.com.

**It is built to depth on demand.** The wiki goes deep where Bill is writing, thinking or asked a question, and stays thin everywhere else. It does not try to cover 54 states × 36 topics evenly — that ambition generates infinite work by construction and was the engine behind an unmanageable backlog. Thin coverage of a country nobody is writing about is the correct state, not a gap.

The test for any piece of work: **does it change what the wiki can say?** If not, don't do it, and don't record that it wasn't done.

**OSINT collects and classifies; CORPUS (`C:\CORPUS`) compiles, reports and analyses — and each side reads the other's evidence and nothing else of it.** CORPUS reads `raw/`, `lookups/`, `wiki/` and `cycle-manifest.json`, the account of the run written at every close; OSINT reads what CORPUS leaves on the shared drive `X:\` *(Bill, 2026-08-20)*, the one place both may write. **Neither reads the other's `logs/`, `reviews/`, `documentation/` or process files, and the curiosity budget for the other's internal state is zero.** An interface nobody states is one where each side reads everything and polices what it finds; an observation about the other side that names no artefact of your own is not logged, not noted, not raised. An OSINT session cannot see `C:\CORPUS` at all, and is not meant to.

**CORPUS sends work as patches and scripts on `X:\prepared\`; `master` has one writer, and it is here** *(Bill, 2026-09-17)*. A `git format-patch` series is applied only through `assert-containment.py --patch <dir>`, which reads the paths the patch itself names and refuses anything outside `scripts/`, `lookups/` and the two index pages — then `git am --keep-cr -3`, because a repo that holds both terminators loses its CRLFs to a plain `am`, and `assert-containment.py --since <BASE>` after, because `am` commits as it applies, so a stage check would read a clean tree and pass over nothing. A script arriving the same way is dry-run and read before it writes. Nothing from the share is trusted because of where it came from: the check is the trust, and a refusal is one line back to CORPUS, never a repair of someone else's patch.

## How CC works

**Act. Log after. Never ask.**

Everything runs in git, so every action is reversible and a wrong call is a revert, not a cleanup. CC therefore makes the call — including judgment calls the rules don't settle — actions it, and **records it in the commit body, beside the diff that carries it**, which is where the evidence for it already is. **Not in `logs/log.md`**: that file takes a process's result and a fatal error, nothing else (*Reporting*, below). Bill reviews after the fact and reverts anything he disagrees with.

CC does not maintain queues of things for Bill to decide. There is no pending-decision register. If CC finds itself wanting to ask, it should choose the more conservative option and do it.

**Rules change in the rules pass — the last stage of the Day B night, after every other pass has finished** (`RULES.md`). A run that meets an edge case takes the conservative option, records it in the commit body, and drops **one** candidate line in `reviews/rule-candidates.md`; the pass rules on the whole batch at once, where a candidate that has earned its line three times **in three separate runs** is visibly a rule and one that has earned it once is visibly not. Editing a rule inside the run that tripped over it is how a file becomes case law, and it is settled by an audience of one. A change to *this* file is still surfaced before it lands — not for permission, but because a rule change is worth reading rather than discovering.

**Good beats perfect, at roughly 90% — not 95%. Dispose of the edge case in one move.**

Every pass has a long tail of awkward items — the source that won't parse, the entity that fits no type, the date no instrument will settle. **The tail is not the work.** Do the ordinary case well, then dispose of the awkward one *once*: drop it, or write a post-run note. Never a second theory, never a rabbit hole. An edge case that recurs is a candidate line for the rules pass; an edge case chased once is time the wiki gets nothing for — and if it matters it comes back, with more evidence attached.

This governs the *item*, never the *run*: a pass still finishes everything it was asked to do.

## Keeping this file short

**No new rule without deleting one.** This file grew unmanageable by accreting a clause for every edge case that ever arose, until it read as case law rather than principles. If a situation seems to need a new rule, first ask whether an existing principle already covers it — it usually does. Never cite issue numbers or past rulings in these rules; a principle that only makes sense with its history attached is a bad principle.

Anything not touched in a month is deleted, not archived. Git holds it.

## The material

**Only primary or first-hand evidence becomes a source**: official announcements, regulations, filings, court records, company statements, datasets, on-the-record reporting, primary documents, published academic work. A source need not break news — a dated explainer, methodology note or reference report is fine.

**Academic papers and named-analyst opinion are a valued, first-class part of the base, not second-class.** They carry ideas and argument rather than events, so being thematic and light on named actors — sparse `entities`, no single dated event — is their normal shape, never a defect. No pass flags, penalises or trims them for it.

**Second-hand syntheses are leads, not sources.** AI outputs (Perplexity, ChatGPT, NotebookLM and the like) have already compressed and paraphrased their inputs, so ingesting them launders errors into authoritative-looking pages and breaks the audit trail. Mine them for the primaries they cite, ingest those, discard the synthesis. Recurring news digests are discarded outright; only standalone articles are admitted. Paid placement, awards PR and vendor thought-leadership report no development — tag any standing object they name, then discard.

**Out of scope is rejected and deleted.** Scope has two halves and an item passes both or neither. **Subject**: data governance and digital transformation. **Place**: Africa — non-African material is admissible only where it files under a `geopol.*` slug (great-power positioning, rivalry, strategic influence) or treats the global south generally, which is the `XGL` place; a single non-African country's domestic story is out, however transferable the lesson looks *(Bill, 2026-08-20)*. So: **an African place, or `XGL`, or `geopol.*` — else out.** A first-hand, admissible item failing either half is deleted (git-reversible). When scope is in doubt, reject. **There is no parking folder.** An item that isn't admitted as a source is turned into a contradiction brief or an acquisition line if it has residual value, and otherwise deleted — nothing is held in limbo. (See `INGEST.md` → the four dispositions.)

**Bill's published work is expert third-party analysis** — cited by author, tagged as analysis not evidence, and free to shape the wiki's framing like any other named analyst's. His unpublished notes and drafts are not sources. Never use a piece to corroborate a claim drawn from that same piece.

**Store the full verbatim body**, never a paraphrase or a search-result excerpt. Where a paywall serves only a free lede, keep it verbatim and mark it as such — unless the free text adds nothing beyond the headline, in which case drop it. A stored paraphrase or partial capture may be overwritten with the source's own fuller words; that completes the record rather than rewriting it.

## Currency

This is where the wiki earns its keep, and where errors actually happen.

- **Every time-varying figure is written dated**: "ranked 156th (2020)", never "ranks 156th". No staleness threshold — it's a phrasing rule, so staleness stays visible on the page. Structural facts — a law's provisions, a treaty's terms — are not time-varying and are not dated. Exchange rates are time-varying too: carry money in the announcing party's own currency, and write any USD figure as a dated conversion — otherwise one commitment becomes three "different" numbers.
- **The event date is not the publication date.** When a source re-reports an older announcement, establish the event date from the primary or mark it unknown. A secondary outlet's own date must never become the event's "as of".
- **Dates are honest about their precision.** Record when a date is padded or inferred rather than published.
- **An older source arriving late is a baseline, not news.** It never outranks fresher state.
- **Supersession is not contradiction.** Keep the current value plus at most one dated prior, and only where the trajectory means something.
- **Where a fact is genuinely unestablished, say so on the page, dated.** A known vacuum — no data-protection law, no published figure since 2018 — is a finding worth stating, not a silence to be tracked elsewhere.
- **Reference studies are cited, not absorbed.** Don't promote a global index's figures into country pages as current state.

## Structure

Folders organise by page *type*; classification lives in frontmatter facets — **place** (countries and regions from `countries.csv`, a single-parent tree), **subject** (slugs from `taxonomy.md`) and **entity**. Blocs like the AU or ECOWAS are entities, not places. Reject values outside the vocabularies.

`new/ → raw/` is a physical pipeline: a file's folder is its state, and moving it out of `new/` is the last step of processing it, so an interrupted run resumes cleanly. Sources in `raw/` are named by publication date and are immutable. *(The sweep containment boundary — sweeps write only to `new/` and `sweep/`, and candidates enter the base only through ingest — is `intake.md` §7, stated there in full.)*

**Synthesis pages hold current state, not chronology** — with one exception: place hubs keep a dated, reverse-chronological **Recent developments** section, which is **compiled from the sources, never written by hand** (`HUB-COMPILE.md`); a hub is a derived view, not a document. Elsewhere, events live in the dated source pages that cite them. If a page reads like a log, trim it; if its length is really N repeating per-country cells, split the substantial ones out and leave the rest as one-line index entries. If it's a long thematic argument, leave it alone.

## Duplicates

A source covering ground the wiki already holds is admitted **only if it substantially adds value** — a fact, figure, date, named party, quote or primary link that changes what a page can say. Marginal detail is not value. Three outcomes:

- **Drop** — adds nothing material. Not admitted; note it in one line.
- **Replace** — adds little, but is *better than what's held*: primary rather than secondary, canonical rather than syndicated, full body rather than excerpt, finer date precision. Ingest it, rewire the citations, retire the held one. **A later, better source displaces an earlier one** — quality beats primacy. Only replace on a clear tier upgrade, never for marginal betterness, or the wiki churns its own citations for nothing.
- **Keep both** — only where each holds payload the other lacks. This should be the rare case.

Same story moved on → an update: revise the pages, keep the prior "as of" dated. Sources that disagree → a contradiction, not a duplicate.

## Entities

**Tag the actors, not every mention. A tag is a terminal state, never a page deferred** *(R11, 2026-08-16 — entity pages retired; populating them cost time and tokens for a level of detail the work does not need)*. Nothing is lost by not tagging — the name sits in the verbatim body, and `raw/` is greppable; when an entity starts to matter, grep for it.

Tag an entity if it is **an actor in the development the source reports** — not merely named in it. Most sources should tag three to six entities, not twenty. *(The core-entities watchlist retired with the pages, 2026-08-16 — it existed to fast-track minting, which no longer happens.)*

**Tag institutions, not officeholders.** A minister announcing his ministry's programme is the ministry's development. Tag a person only when the person is the story. Officeholders churn and generate the longest tail.

## Working the base

**Contradictions** are the first queue CC keeps: when sources disagree, never overwrite silently — record it in `reviews/contradictions/`, and the reconcile pass researches it, ingests the primaries it finds, and applies a resolution. Prefer the newest value; record the conflict rather than erasing it.

**Acquisitions** is the second: specific known documents the wiki wants and doesn't hold. It is a fetch list **for automated fetches**, not a research register — drained by the acquisition pass, never by reconcile. One automated attempt each; a document that only a hand-clip could get is dropped and its absence stated on the page, dated and naming the document exactly — never parked as a standing chore, and never a post-run note, which takes only what is irreversible or already public.

**Housekeeping** is the third: lint-type work that is real and CC's to close, but too big for a batch — a corpus-wide sweep, a recompile of every hub. Registered in `X:\housekeeping-jobs.md` and worked in **the Day B session** — the rotation night that gives up its heavy sweeps to it (`BACKLOG.md`), one job a night, never folded into another pass.

Three queues, each drained by CC by its own pass — reconcile for contradictions, acquire for acquisitions, the Day B session for housekeeping — over the whole queue at once, never a selection. Anything that can't be closed by any of them isn't work; it's a horizon, and belongs on the relevant page as a dated statement of what isn't established.

**CC cites only links it actually holds.** In a contradiction brief or anywhere else, never suggest a source from your own knowledge as though the wiki held it. Say plainly that nothing is on file — that absence is the finding.

**Capture is not endorsement.** Profiling an entity, or holding a source, implies no view of it.

**Querying is read-only.** Results are derived snapshots, never sources, and never flow back into `raw/`. Never re-derive at query time what a compiled page already holds — that is what compiling was for. Research output from a reconcile pass is working material: it earns its place only as an ingested primary.

## Output

Work from the compiled wiki, cite the underlying pages, and follow the house style — cautiously outspoken, evidence-led, polemical about systems not people, for governance and policy readers who aren't technical. Cite as inline hyperlinks placed on the claim they support, not gathered at the end.

## Reporting

**A log entry is one line, and `logs/log.md` is CC's own recall — not Bill's reading.** The form is `YYYY-MM-DD HH:MM · **PASS** · what changed · revert: <hint>`, the process named in bold capitals, defined once in `STATUS.md`. **Only a process's own result and a fatal error earn a line** *(Bill, 2026-09-08)* — never a decision, which goes in the commit body; never a call about one record; never an agent, which is not a process. Never a narrative, never a section, never a second line: the detail is in git, and a log too long to skim defeats its own purpose. A script truncates the file at every cycle close, so length is not a discipline anyone has to keep.

**On screen a pass closes on one line and nothing else** — the standing count line, defined in `STATUS.md` ("wiki status"), which is the canonical status object. **A pass neither calculates nor reports what it cost** *(Bill, 2026-09-08)*. **No pass mandates an explanation of its own numbers.** Announce each pass by name as it runs (see there).

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

**Three bands, and the escalation test is reversibility, not importance** *(Bill, 2026-08-20)*. **`[CRITICAL]`** — irreversible or already public: evidence loss with no backup, a published page stating something false, leaked source text, a legal or licensing exposure, a slug reissued under a live citation; if a later run can undo it, it is not `[CRITICAL]`, and a band that fires often is one that gets skimmed. **`[ACT]`** — decided; the reader executes, never adjudicates. **`[FYI]`** — on the record, asks nothing; a log line, or the queue where the other side owns it. *(`[DECIDE]` retires into `[ACT]` — under the reversibility test a ruling only Bill can give is very nearly the empty set; `[FETCH]` was never a band but a destination, `X:\fetch-list.md`.)* **Only `[CRITICAL]` goes to `reviews/post-run-notes.md`**: numbered, **≤60 words**, oldest first, **capped at 10 open**; at the cap CC takes the conservative option itself and logs it, per *Act. Log after. Never ask.* A number is prefixed with `x` when done — by Bill once absorbed, or by CC when it actions the note in-session — never renumbered, and a struck entry is deleted **3 days** after its cleared date.
