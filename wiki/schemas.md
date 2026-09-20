# schemas.md — frontmatter schemas, entity tagging, admissibility detail

Split out of `reference.md`; section numbers are kept so a `§N` reference resolves unchanged. `CLAUDE.md` holds the principles and wins where the two disagree.

---

## 4. Frontmatter schemas

**These schemas are also machine-readable**, as `lookups/frontmatter-schema.json` — what `scripts/lint-deterministic.py` validates the whole vault against (checks #1, #2, #3, #4, #10, #11, #12, #15). It is a *restatement*, not a second authority: where the two disagree, this section wins and the schema is what gets corrected. The JSON carries two things the examples below do not: `date_source` also takes `inferred` (a fiscal year read off the document) and `derived`; and an **expected-but-not-required** tier — `ingested` is required in `raw/` and absent from archived companions — which reports softly and never gates.

**`lens:` is retired** *(Bill, 2026-09-08)*, **and cleared from `raw/` on 2026-09-20** *(Bill, over his own 2026-09-08 note)*. It is written by nothing: not by a sweep's staged frontmatter, not by a finance record, not by a page written or recompiled. It is not in the schema and no pass adds it. The 2026-09-08 note said to leave the files carrying it exactly as they were and not to register a job to clear them; the strategic review's task 20a is that job, and Bill ruled for it once CORPUS stopped reading the key — the catalogue was still counting a `lens` facet, and a menu built from a key nothing writes empties itself with no error to say so (register R34a). **15,372 `raw/` records lost the key on 2026-09-20** (register R36), one line removed from each as bytes so nothing else in the file moved; **2,841 of them carried a value** — 2,543 `[sovereignty]`, 200 `[sovereignty, colonialism]`, 69 `[colonialism]`, 26 the reverse, 2 `[analysis]`, 1 `[reference]` — and those classifications now exist only in git history. **And the 1,696 files outside `raw/` lost it on 2026-09-20 too** (register R50, task 20b), which finishes the key: **nothing in the corpus carries `lens:` any more.** The four roots were 1,089 under `wiki/` (1,051 of them intersections), 599 `budget-archive/` companions, 6 in `new-budget/` and 2 in `scratchpad/`; **588 of them carried a value** — 586 `wiki/` pages (516 `[sovereignty]`, 60 `[sovereignty, colonialism]`, 6 `[colonialism]`, 4 the reverse) and 2 in `scratchpad/` — and those classifications now exist only in git history, except the two under `scratchpad/`, which is gitignored and therefore has no history to hold them. The budget roots were the 607 the review's two tasks did not name, and they were carried by their published counts rather than by a path list, because CORPUS may not read those trees: the count matching was the check, and any other number would have skipped the root rather than stripped it. One line removed per file as bytes, every removal reconstructed and compared before it was written, so CRLF, BOMs and the three files with no trailing newline are as they were. **Check #2's `lens` clause is retired with the key** — a guard with nothing left to read — but `LENS_VALUES` stays in `lint-deterministic.py`: `check_links` whitelists `sovereignty` and `colonialism` from that constant, and the words are still wikilinked in legacy *body prose*, which nothing here touched. Nothing writes the key anywhere, so a new carrier means something has started again.

**`artefact:` names the documents a record holds, and a working extract is not one** *(2026-09-20, jobs 108/109)*. It takes a bare filename resolved beside the record, a flow list, a block list, or the wikilink spelling `[[name.pdf]]`; a record holding several files uses one of the list forms, which is how every page-image capture and every bilingual edition is written. **A `.txt` extraction sitting beside a declared artefact of the same stem is a sidecar, not a second document, and is not named here** — the record's own body is that text. Three spellings occur and all three are recognised: `x.txt`, `x.pdf.txt` and `x.ocr.txt` beside `x.pdf`. `scripts/artefact-md5-index.py` reads all four declaration forms and labels a sidecar as one, so an artefact reported as declared by nothing is a real orphan and lint #39's counter can reach zero. Where a record declares a file that is not in the tree, the key is false and goes: **`artefact_none: YYYY-MM-DD  # why`** states the absence where a reader meets it.

**`artefact:` is a `raw/` key, and the budget trees declare by manifest instead** *(2026-09-20, job 120)*. A document under `budget-archive/` or `new-budget/` is named twice in `new-budget/manifest.csv`, as `artefact_path` and as `archive_path`, and that row **is** its declaration — `BUDGET-EXTRACT.md`: *“the manifest row, companion page and extracted tables are committed”*. Its companion page carries no `artefact:` key and is not required to. **Two further classes under those trees are not artefacts at all.** An extracted table (`.csv`) is the extraction's own output, listed by `budget-archive/README.md` beside the artefact and the companion as the third and only git-tracked part — *“a lost PDF is re-fetchable from the manifest's URL; a lost figure is not”*. And a `.txt` extraction is the same sidecar the `raw/` rule above names, including the **page-range spelling** `x.p83-85.ocr.txt`, which is that working extract cut smaller. `scripts/artefact-md5-index.py` reads all of it, so an artefact reported as held by nothing is a real orphan in either tree and the counter reaches zero — which it does, 2,243 artefacts, 0 undeclared.

### Source (in `raw/`, immutable)

```yaml
---
type: source
title: Cassava–NVIDIA GPU partnership announcement
url: https://...
publisher: ...
published: 2026-06-16
date_precision: day       # day | month | year — precision of published (default day)
date_source: source       # source | proxy — 'proxy' if the date fell back to ingested/created
ingested: 2026-07-10
places: [ZAF]
topics: [infra.store, tech.ai, geopol.usa]
entities: [[cassava-technologies], [nvidia]]
body_completeness: full   # full | excerpt | paywalled
catalogue_hero: GPU cluster for African model training; first NVIDIA deployment south of the Sahara
---
```

`body_completeness` values:

| Value | Meaning |
|---|---|
| `full` | complete verbatim body as published |
| `excerpt` | verbatim *portion* kept when the full text is genuinely unavailable (fetch failure, hard paywall serving nothing usable) |
| `paywalled` | HTTP-200 paywall serving only a free lede; kept **only** where the free body *excluding the title* adds value |
| *(missing)* | **unverified** — completeness not asserted. New ingests always set the field; a blank is a legacy source, and `full` is never assumed of it. Backfilled from body evidence by lint #15. |

**`url:` may be blank, and only with `url_note:`.** A document with no online posting is a real case, not a capture failure: the artefact *is* the record. A blank `url:` is admissible **when `url_note:` states dated evidence that the search was exhausted** — what was tried, when, and why the absence is treated as final. Without that note a blank `url:` is a defect (lint #14).

**`catalogue_hero:` is required on every source, and there is no refusal form.** It is the record's subtitle in the public catalogue at `corpus.data-landscapers.io/catalogue/`, so a record without one is a catalogue row that says only its own title. The contract, in full:

- **≤120 characters, English, one line.** The cap is hard — the catalogue lays the row out to it, and an over-long hero is truncated by the page rather than by CC.
- **Terse grammar is correct.** It is a subtitle, not a sentence: drop articles and copulas where they cost characters, and take no terminal full stop. Internal punctuation — a semicolon, a dash, a comma series — is how two facts fit.
- **It complements the title; it never repeats it.** The title says what the thing is called. The hero says what the reader gets by opening it: the figure, the date, the named party, the consequence. A hero the title already contains is a wasted row.
- **Plain text.** No bolding, no `[[wikilinks]]`, no citation, no markdown of any kind — it is rendered as a subtitle by something that is not this vault.

**It is `hub_line`'s shorter, blunter sibling, and it is not gated.** `hub_line` is an editorial claim that a dated development happened in a place, and the classes at `INGEST.md` → *The `hub_line` gate* correctly earn none. **Every one of them still earns a `catalogue_hero`**, because every record is in the catalogue — a finance record, an artefact companion, a reference study, a `cite_through:` capture alike. A hero is always derivable from the title and body in hand, which is why there is no `catalogue_hero_none:`.

**The contract runs from 2026-09-05**, the first ingest after the field was minted. A source ingested before it carries none, is not a defect, and is the backfill lane's work: lint #34 counts that backlog and never fails on it.

**Optional source keys.**

- **`artefact:`** — the binary document this page is companion to (`layout.md` §3), by filename. **Accepts one value or a list.** An announcement that publishes two PDFs has two artefacts and *one* companion page. The key is `artefact:`, never `artefacts:`, however many files it names.
- **`origin_status:` / `origin_held:` — never write either key.** `hold` does not exist as a value. Sources still carrying `origin_status: cleared` keep it as a historical value that asserts nothing; nothing reads it.
- **`cite_through:`** — this capture is **retained**, but the claim it carries should be cited from the named source: the primary the wiki went on to acquire. **It records both duplicate outcomes that keep the file**: the *keep-both* case, where citations consolidate on the primary, and the *Replace* case (`CLAUDE.md` → *Duplicates*) where the retired record cannot simply be deleted because it is the sole evidence for something the survivor lacks — the `published` date the survivor is dated by, a DOI, a register entry. **Delete a replaced record only where it carries no unique payload; otherwise `cite_through` it.** Either way the page stays and no pass may treat it as a deletion candidate — but a `cite_through` record **carries no `hub_line:`**: move the line to the survivor and name the retired capture in `hub_line_sources:`, or the hub re-cites the retired capture at every recompile.

**A held record whose body is a landing page, an excerpt or a cap-truncated capture is completed, never duplicated.** The bounded verbatim re-capture overwrites the body and `body_completeness:` in place and adds the `artefact:`, whether or not the completing capture shares the held record's URL — `url:` is immutable evidence of where the held text came from. This is the ordinary end state of every acquisition that succeeds against a landing page, not an edge case, and it is why a `DUP-EXACT` or `FLAG-SLUG` against such a record routes here rather than to a drop (`INGEST.md` step 2).

**There is deliberately no `superseded_by:`.** Supersession (`CLAUDE.md` → *Currency*) is a **value** moving — a date, a figure, a ceiling — applied to the pages stating the old value by `INGEST.md` step 2b, which finds them by grep from the amending source's own text. It leaves no key on either source.

**These keys, and `hub_line`/`hub_line_sources`/`catalogue_hero`, are CC's own bookkeeping and are not frozen by immutability.** `raw/` is immutable to prevent retroactive reinterpretation of the **evidence** — body, `url`, `published`, `publisher`, dates, `body_completeness`. A field recording CC's analysis or how to cite the page is not evidence; correcting one is maintenance.

**Finance records extend this schema.** A source built by a finance driver adds `deal_id`, `finance_origin`, the **required `financier_slug`** and — where a recipient is named — **`recipient_slug`** (canonical entity slugs that also appear in `entities:`), plus whichever driver-supplied fields the compile pass aggregates — see `wiki/finance-record-spec.md` → *Entities* and the drivers. Lint does not validate the driver-specific fields, **but it does validate the two slug fields**: `financier_slug` resolution is **lint #16** (`scripts/lint-finance-slugs.py`), which fails loudly on a missing or non-canonical financier key, since a bad key fragments a hub Financing aggregate.

**A duplicate deal record is retired by merge, never by deletion** — with `retired_deal_id:` and `cite_through:`. Where two records describe one deal, the weaker record **keeps its file** and is neutralised in place: `deal_id:` is renamed **`retired_deal_id:`**, **`cite_through:`** is set to the survivor's `deal_id`, and `finance_origin:` is **removed** so no compile counts it. Any payload it holds is carried into the survivor's `## Development history` first, and citations pointing at it are rewired to the survivor. `scripts/lint-duplicate-deals.py` finds the pairs, keying on financier + place + amount — deliberately **not** on `recipient_slug` or year.

**Whatever the pass and whatever the reason, a retirement names its survivor.** Where a record is retired into another — a duplicate dropped or replaced under lint #7, a deal record merged by the keys above, a byte-identical artefact collapsed — the register recording the ruling carries **both slugs and which one survives**: `survivor` in `reviews/source-duplicate-decisions.csv`, `cite_through:` on a merged deal. A downstream tree that cited the retired slug can then repoint mechanically onto the twin, and no claim loses its evidence.

**A slug is a permanent public identifier — retire one, never reissue one.** Once published it is the target of a provenance link inside a document someone has already downloaded. Retiring a slug is survivable; reusing it for a different record silently redirects an old citation onto unrelated evidence — the failure `CLAUDE.md`'s reversibility test calls `[CRITICAL]`. A replaced or corrected source therefore takes a **new** slug, never the old one. Once the site is live, **deleting a `raw/` record is a publishing decision as well as a vault one**: the retirement names the survivor, and where there is none, the page says what was withdrawn rather than falling silent. `index/` is rebuilt from scratch and is not the mechanism at risk; the exposure is the citation already published.

**A structured extract of a tabular document is `excerpt` and stays `excerpt`.** The overwrite-with-fuller-text rule below targets paraphrase and truncation of *prose*. A budget document's companion source page holds its citation, structure and headers by design; re-capturing the tables would not complete the record.

**A journal abstract with its citation is `excerpt` and stays `excerpt`.** Where a publisher serves the abstract and withholds the full text, the abstract captured **verbatim** alongside a complete citation — title, authors, journal, DOI, date, URL — is the **normal and accepted record** for that paper, not a defect awaiting repair. So: **no `needs_clip`, no acquisition line, no post-run note.**

**A clip is worth asking for when a specific paper becomes load-bearing** — a claim the wiki wants to rest on, an argument being written against — never because the paper exists. If the full text later becomes reachable by an ordinary route, completing it is still right under the re-capture exception below.

**The same holds for anything the wiki generated rather than captured** — a finance deal record built from a CSV row, an artefact's companion page, a statistic capsule lifted from a dataset. There is no "as published" body to be complete, so `full` is false and blank asserts nothing; `excerpt` is correct and final, and it makes the `full > excerpt` dedup tiebreak resolve the right way when a prose primary for the same event turns up. **Never chase a re-capture for one.**

**Paywalled-stub gate — resolved at ingest, never deferred.** A `paywalled` item whose **full payload sits in the free lede promotes normally**. One whose payload **depends on the withheld body is dropped**, as is a headline-only item (free body adds nothing beyond the title). **There is no clip queue.** State the absence dated on the page and move on.

**A held document with a dead or gated source link is complete, not defective.** Where the wiki holds the file — a PDF behind an email opt-in, a download that needed a form — the record is **the document plus where it came from**, and that is the whole requirement. Do not flag it, queue it, re-attempt the link, or treat the dead link as a defect in the source.

**Immutability has one bounded exception — verbatim fidelity re-capture.** `raw/` is immutable to stop retroactive reinterpretation of the record; it does not freeze a known fidelity defect. A source whose stored body is a **paraphrase, AI summary or partial `excerpt`** may be overwritten with the **source's own verbatim words** under bounded conditions:

- the **URL is identical**;
- the change **only** replaces a non-verbatim/partial body with the fuller verbatim text — it never edits facts, framing, or any frontmatter beyond `body_completeness`;
- the **filename, `published`, `retrieved`/`sweep_batch` and other frontmatter are kept**;
- `body_completeness` is flipped to `full` (or `paywalled` where a paywall still caps it);
- log each instance.

**Excerpts are overwritten with the complete body wherever possible.** This completes the record rather than rewriting it.

### Concept (subject page, in `wiki/concepts/`)

```yaml
---
type: concept
title: Data protection
slug: gov.protect
places: [KEN, NGA, ZAF]
entities: [[data-protection-authority-kenya]]
status: active            # active | stub | needs-review
last_reviewed: 2026-07-10
sources: [[2026-06-16-cassava-nvidia-deal]]    # bare, never a path — see §3
---
```

### Place (hub page, in `wiki/places/` — countries and regions alike)

```yaml
---
type: place
title: Kenya
code: KEN                 # ISO-3 for countries, X__ for regions
parent: XEA               # from countries.csv; regions point upward too
place_kind: country       # country | region
topics: [gov.protect, infra.store]
status: active
last_reviewed: 2026-07-10
---
```

Place pages open with a dated, reverse-chronological **Recent developments** section, then sections per active topic linking to concept and intersection pages.

### Intersection (topic × place, in `wiki/intersections/`)

Created **only when a place-specific treatment of a topic is substantial** — e.g. `kenya--gov-protect.md`. Do not pre-create empty cells.

- Naming: **`{place-slug}--{topic-slug}.md`**
- Link from **both** the place hub and the concept page.

### `last_reviewed` semantics

`last_reviewed` = the date of the last **substantive** check, not a trivial edit. A review includes **re-checking the currency of the page's dated figures**, not just its structure. Set it on every page touched during ingest (`intake.md` §6 step 10).

---

## 5. Entities — tag only, no page

Tagging rules are in `CLAUDE.md` → *Entities* (tag the actors, not every mention; institutions not officeholders; three to six per source). **There is no paging bar and no `wiki/entities/`**: a tag is a terminal state, not a page deferred. An entity lives only as a tag plus its mentions in source prose, and `raw/` is greppable when it starts to matter.

**One body, one slug — and the form is ruled** *(job 116, 2026-09-20)*. **A new slug takes the body's own name in the body's own language, suffixed with its country where the body is national** — `macra-malawi`, `ministere-sante-mauritanie`. The suffix is what keeps `national-communication-centre-kenya` from contesting `ncc`. **Where a slug for that body already exists, use it; where two exist, the most-used one wins** (job 105's ruling, the same night: there is no convention to appeal to, so only what the vault already writes can decide it). **The second clause is the load-bearing one** — most of this defect is not a new slug but a writer reaching for a second name for a body that already has one, so **grep the slug before minting one**. Nothing lints a split slug: both halves have referents, every page reads correct, and a grep for the body silently finds part of its record.

**Entity types (`facets.md` §1) still classify the tag**, distinguishing a `company` from a `person` from an `instrument` and so on — that vocabulary guides *what to tag and how*, independent of whether anything is ever minted from it.

**What CORPUS reads.** `lookups/region-membership.csv` (`slug,entity_type,places`) holds the institutions that reach a region without carrying its place code, read by CORPUS's `report-region-init.py`. It is a frozen snapshot, not a live feed: nothing in OSINT updates it.

**Discard means genuine non-intelligence artefacts only**: **the wiki's own** config and vocabulary files (`taxonomy.md`, `countries.csv`, scaffolding), blank or failed captures, duplicated scaffolding. **External** published standards, taxonomies and policy instruments are *never* discards — they are `instrument` references, tagged on the sources that cite them (§5a).

A dated fact you pull about an entity or *from* it (a country ratifying the Malabo Convention, or "PeeringDB lists 14 IXPs in Kenya as of 2026-07-10") is a normal source that cites the entity as an ordinary tag.

---

## 5a. Admissibility details not covered by CLAUDE.md

Tiers, primary-vs-synthesis and the author's-own-work regime live in `CLAUDE.md` → *The material*. These operational clauses do not, and are carried here.

**Academic work.** Theses and dissertations are admissible on their content. Single authorship or student authorship is **not** grounds for rejection. An old thesis is a historical baseline, not stale news — file it dated and treat it as such.

**No circular self-corroboration.** Beyond the `CLAUDE.md` rule that a piece never corroborates a claim drawn from that same piece:

- Do **not** ingest a publication that merely re-renders the wiki's own pages — that is the wiki citing itself through a laundering step.
- Where a piece of analysis states factual claims, trace them to the underlying primaries and cite those for the facts; cite the piece itself for its analysis.

**External standards are sources, not config.** A published framework, taxonomy or standard from an outside body (e.g. the World Bank theme taxonomy) is an `instrument` and is ingested. This is distinct from the wiki's *own* configuration files — `taxonomy.md`, `countries.csv` — which are never sources.

**A platform is not a provenance — the account is.** An institution's own post is that institution's own words, and a ministry, regulator or agency that publishes to Facebook or LinkedIn when its own site is dormant is admitted as the official announcement it is. A **third party's** post about an event is second-hand — a lead to mine, never a source — on every platform alike. So **do not ban a domain**: the question is always whether the account is the first-hand party, which `CLAUDE.md` → *The material* already decides.

Two cautions that do apply, neither of them about the domain: a social post is **ephemeral and often login-walled**, so capture the body verbatim at fetch time and expect `excerpt` to be final rather than a defect; and where the post *summarises* a document, the document is the source and the post is not (`INGEST.md` step 3).

---
