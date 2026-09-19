# INGEST.md — the ingest pass

Trigger: **"run ingest"**. Drains `new/`, **the only door into the base**. Never `new-budget/`.

**Four dispositions**, one per item. **1. `raw/`**: admitted. **2. Contradiction**: a brief (step 7); item deleted. **3. Acquisition**: a line (step 8); item deleted. **4. Delete**. A source may *also* spawn either (steps 7–8); leaving `new/` is not admission.

**Fifth route, budget documents only** (estimates volumes, appropriation acts, budget annexes): `new-budget/{ISO3}/{FY}/` per `layout.md` §2, artefact plus `manifest.csv` row, for `BUDGET-EXTRACT.md`; URL logged to `sweep-url_log.md` as `admitted`.

**Only the procedure lives here**; the schemas are `layout.md` §2–3, `schemas.md` §4–5, `intake.md` §6–7, `operations.md` §8 and `wiki/finance-record-spec.md`. **Step numbers are permanent handles** cited from `raw/` frontmatter and the specs: never renumber. Run order below, numbering non-sequential by design.

---

## The shape, the slicing, and a dead slice

**Ingest never opens a place hub** (`hub_line`, 4a; `HUB-COMPILE.md` at the close). **Phase A decides per item. Phase B** (steps 5, 6, 9, 10: draining `logs/ingest-pending-writes.md` grouped by target page, idempotent) **is `WIKI-SYNC.md`'s, off the nightly path.**

A normal run is **10–80 items**. Above ~15, **slice Phase A into sub-agents of ~10 items** on explicit file lists, each returning `SWEEP-CYCLE.md`'s tally line plus its delta list. **A slice never writes `logs/log.md`** (`STATUS.md` → *The `log.md` entry*) — it returns its tally and deltas to the parent, which folds every slice into the run's own single closing entry. **The cycle parent spawns the slices** (no sub-agent spawns another).

**Spawn same-run slices in parallel batches, not one at a time.** A sequential run multiplies wall time by the slice count — the single largest cost a large ingest run pays — and nothing about a slice's work depends on another slice of the same run having finished; each holds its own file list and touches no `raw/` file another slice owns. The genuine risk parallel spawning carries is concurrent writes to the handful of files every slice shares (`logs/sweep-url_log.md`, `lookups/raw-url-index.csv`, `logs/ingest-pending-writes.md`, `reviews/acquisitions.md`), and the losses have been silent every time — a whole slice's block gone while every slice reported success.

**A slice appends to a shared file and never rewrites it**, removes a row **by matching the row's own text, never by line number**, edits only rows it wrote itself, and runs **no whole-file formatter** over one — the line breaks in these registers are records, not wrapping. **The parent reconciles before it dispatches Phase B**: each slice's returned delta count against the rows actually in `logs/ingest-pending-writes.md`, and `git diff` over the other three. That reconciliation is why **a slice returns its delta lines verbatim and never a summary** — twice now the returned report was the only surviving copy of a clobbered block, and a summary would have made the work unrecoverable.

Fall back to sequential spawning only where a batch's own history shows the reconciliation actually failing, not by default caution.

**A dead slice is requeued, and nothing else**: re-dispatch what is still in `new/` in smaller slices; never reconcile `new/` against `raw/`.

## Two lanes

**The backfill lane skips exactly the three rows below and changes nothing else.** **Two triggers open it: `update wiki backfill`, and the sweep cycle's one Phase A pass, which ingests the batches it pulls from `X:\new-queue\`** (`SWEEP-CYCLE.md` → *Pulling X:\new-queue\*; Bill, 2026-09-17); under any other trigger every item is news. `python scripts/ingest-lane.py` assigns the lane per item off `sweep_batch:` (whitelist: `status-acquire-`/`progress-filler-` batches; artefacts follow their companion) and lists each lane (`--lane backfill|news`). **The parent names the lane in every Phase A slice's spawn prompt**, as it names the iteration; a slice not told its lane is a news slice.

| Step | News lane | Backfill lane |
|---|---|---|
| 1 origin | script, then per-item adjudication where no `sweep_batch:` | script only |
| 2 dedup | tiers 1–3 | **tier 1 only**, no model judgment |
| 4a hub line | authored, or a recorded refusal | `hub_line_none: <date>  # backfill lane — baseline, not news` |

**`catalogue_hero` (3a) is written in both lanes** — it is the catalogue's subtitle, not a news claim, so the backfill lane owes it exactly as the news lane does.

Everything else binds both lanes. **The lane changes the work, never the model** — every slice runs on Opus (`SWEEP-CYCLE.md` → *Model*).

**The lane skips tier 3's model judgment, not the evidence a slice already holds.** Tier 1 is a URL check, and a backfill batch is assembled from whatever URL a search surfaced while the vault holds whatever URL an earlier acquire resolved to — so the two systematically differ for exactly the documents most worth holding: statutes, gazettes, strategies, and an agency release an outlet has republished. Where step 3's own read makes a twin visible, **dispose of it under `CLAUDE.md` → *Duplicates* rather than admitting it because tier 1 came back clean** — and the answer may be to retire the *held* record, where the arriving capture is the better one. A `FLAG-SLUG` falls to that same test, since the tier 3 it is routed to does not run in this lane. Before the move, **check the target `raw/YYYY/` path for an existing file**: a same-slug collision is itself a duplicate signal, and an unnoticed overwrite loses the richer record silently.

---

# Phase A — decide (per item)

## 1. Intake screen (first, always)

- **`python scripts/origin-screen.py` first**, per run or per slice. **`DROP`/`WATCH`** (`logs/drop-list.csv`, non-zero exit) **is the gate; `NOVEL` is a report and nothing follows from it.**
- **Per-item origin adjudication is skipped for anything carrying `sweep_batch:`** (lint #17); **an item with none is adjudicated here in full.**
- **Second-hand or AI synthesis** (`CLAUDE.md` → *The material*): stage the primaries it cites, an un-fetchable one as an acquisition line (step 8); **delete the synthesis**.
- **No development, but a standing object**: capture it as that entity type.
- **Out of scope: reject and delete** (`CLAUDE.md` → *The material*); a digital-platform actor is in. **In doubt, reject.**
- **Undated/unattributed but load-bearing**: a **provenance hunt** in `reviews/contradictions/open/`; delete the item.

**Relevance is a scope check, nothing more**, applied once, no re-read.

## 2. Deduplication — three tiers, cheapest first

**Tier 1 is never skipped; tier 3 never runs un-narrowed.**

**Tier 1, mechanical — both checks, run as one paired step before any body is read.** Normalise `url:` with `vault_lib.normalise_url()`, never by eye; `grep -F` `logs/sweep-url_log.md` **and** run `python scripts/raw-url-index.py --check URL` (`intake.md` §6a). **They answer different questions and neither substitutes for the other**: the index holds admissions only, so a URL a previous run *dropped* returns CLEAN from it for ever, and the log is the only record of the three non-admitting dispositions. Any prior adjudication, `DUP-EXACT`, `DUP-SLUG` or `REJECTED`: **drop, log one line, never read the body.** `FLAG-SLUG` goes to tier 3. Not adjudications: an `acquisition` line (read the disposition) and a budget record's document URL; **a budget record dedups on `deal_id`**, a hit merges.

**A `DUP-EXACT` against a held record whose body is a landing page, an excerpt or a cap-truncated capture is not a duplicate — it is that record's completion** (`schemas.md` §4). Overwrite the body in place, whether or not the completing capture shares the held record's URL: no second record, no slug retired, no citation rewired, and every `[[…]]` already on a page starts resolving to the full text.

**The completion test runs on the step-3 body read, not only on a tier-1 hit, and `DUP-SLUG` goes to it too.** A record admitted on a publisher's catalogue landing page and the same document's PDF differ in URL by construction, so tier 1 returns CLEAN on exactly the completions most worth making — the statutes, strategies and diagnostics the vault holds at a fraction of their length. Obeying tier 1's "drop, never read the body" on a `DUP-SLUG` has cost a 3.5x fuller capture of a held truncation.

**Tier 1 is a URL check and a twin is systematically not URL-shaped, so a CLEAN tier 1 settles nothing about duplication.** The shapes it cannot see, each met repeatedly: the same document at a reordered query string; the same ministry PDF at a second host; a publisher's own other-language edition of its own story; a machine translation of an agency release; a syndicated wire rewrite; two tabs of one reference page where one body is a strict subset of the other; and a landing page against its own file. **Where step 3's read makes a twin visible, `CLAUDE.md` → *Duplicates* governs and tier 1's result does not override it** — in either direction, including retiring the held record where the arriving capture is the better one. A targeted grep of `raw/` by the document's own title and identity settles it without opening a body.

**Tier 2, narrow.** From `raw/` filenames, only sources within a few days of this item's `published` sharing a place or an entity.

**Tier 3, a single judgment, on titles and ledes only, drop-by-default.** Match on event + entities + date; never open a held candidate's body: **drop unless clearly a new event**, no replace/keep-both analysis, no tier-upgrade hunting. Sources that **disagree** on the same event are a contradiction (step 7), never a duplicate.

## 2a. Finance branch

Any `finance.*` tag runs the driver first (`wiki/finance-news-driver.md` for `finance.new`/`finance.mou`, `wiki/finance-load-domestic-state.md` for `finance.budget`), applying the **five-fact test**. **Passes, held record matched**: merge, one dated attributed line in `## Development history`, status/disbursed updated. **Passes, no match**: build a deal record into `new/`. **Fails any fact**: no record; ordinary source, `finance.*` tags kept, a failed date recorded as unestablished, dated. **Finance items get no per-deal hub bullet** (`FINANCE-COMPILE.md` aggregates them) and no place delta. Funding *trends* never enter here.

## 2b. Amendment branch

If the item **amends, supersedes, repeals, replaces or postpones** a named prior instrument: **grep the corpus** for the instrument's name and number and the superseded value as the pages write it; **add every page stating the old value to the step-11 delta list**; **correct as supersession, not contradiction**: new value dated, at most one dated prior, no brief.

## 3. Create the source page

Frontmatter per `schemas.md` §4 — **including `catalogue_hero:`, step 3a** — facets per `facets.md` §1, the **full verbatim body** (`CLAUDE.md` → *The material*);

**Every `topics:` value is checked against `lookups/taxonomy.md` before the record is written.** Staging invents slugs — a compound `<valid-slug>--<descriptive-suffix>`, or a plausible-looking slug that is simply not in the vocabulary — and an invalid one reaches `raw/` unnoticed and surfaces only when Phase B opens a concept page that does not exist. Truncate a compound to its valid prefix; correct anything else to the controlled value, or drop the facet. This is a frontmatter defect, fixed in place, never a contradiction. **The value staging most often gets wrong is `geopol.*`**, whose scope ruling in that file is already explicit and keeps being missed: bilateral aid, donor funding, development cooperation and project financing are **not** geopolitics, whichever country funds them — tag `finance.*` and the topics they fund, or drop the item if that is all it is.

 `body_completeness:` `full`, `paywalled` (free lede only) or `excerpt` (truncated or unavailable: **flag, do not retry**).

**Download the primary document, not just the announcement.** Where an item announces or links a gazette, plan, strategy, tariff, report or consultation paper, **the document is the source**: fetch and file it as artefact plus companion page (`layout.md` §3); the announcement is admitted only where it adds something. **One attempt on the night**; failure files an acquisition line naming the **document**, not the site (step 8). `ACQUIRE.md` gets its own one attempt later.

## 3a. Write the catalogue hero

**Every source gets a `catalogue_hero:`, and this step never ends in a refusal.** It is the record's subtitle in the public catalogue at `corpus.data-landscapers.io/catalogue/`, so a record without one is a row there that says only its own title. The contract is `schemas.md` §4 in full; the working shape is **≤120 characters, English, one line, terse, no markdown, no terminal full stop, and complementing the title rather than restating it** — the figure, the date, the named party or the consequence the reader gets by opening the record.

**It sits here, not at 4a, because it is not gated.** `hub_line` is an editorial claim that a dated development happened in a place, and the classes at 4a's gate correctly earn none; **a hero is owed by all of them alike** — a finance record from 2a, an artefact companion, a reference study, a `cite_through:` capture. Write it while the body is in hand, from the same evidence 4a would use and one register blunter. `python scripts/catalogue-hero-set.py` writes them in bulk from JSONL, which is what a slice of ten should use rather than ten hand-edits to frontmatter.

**Both lanes.** The backfill lane skips 4a's hub line; it does not skip this.

## 4a. Author the hub line

**Classification is the facets (place, subject, 3–6 entities, dates) plus `hub_line:`**, on the source page: **one plain sentence**, a bolded claim then the dated specifics and topic wikilinks, date and place taken from the frontmatter. Not analysis.

- **No `hub_line`, no bullet.**
- **One event, several accounts**: one carrier, the rest in its `hub_line_sources:`; **after the last slice and before `HUB-COMPILE.md`**, group by **place + event** and collapse each group. **The event is established from the bodies and the date is evidence for it, never the grouping key** — two accounts of one event published a day apart are the commonest shape and a date key cannot see them. **Group against the held corpus inside a date window, not against the run's own output**: the second account is usually ingested nights after the first, so a group formed from one run's new sources never contains the held record it duplicates. `lint-duplicate-sources.py --max-gap` is the candidate set. **A collapse is not complete until the loser carries `hub_line_none:`** — writing the carrier's `hub_line_sources:` while the loser keeps its own `hub_line:` compiles as two bullets and reads to lint #7 as a settled keep-both.
- **Record the refusal: `hub_line_none: <date>  # <one-clause reason>`**, never a blank.

### The `hub_line` gate — which sources correctly get none

**The bullet is a claim that a dated development happened in a place.** None of these is a gap (`scripts/hub-line-partition.py` counts them; RESIDUAL-UNCITED should read 0): finance and budget records and budget-document companion pages (2a); `cite_through:` captures; no `places:` or no parseable `published:`; a standing page under a capture date (`date_source: proxy`); an older source arriving late; reference studies and academic or named-analyst work; forward notices, convenings and profiles.

**Two backlog classes are backfilled on demand, never by sweep**: **PRE-CONTRACT** (ingested before `hub_line` existed) and **RESIDUAL-CITED** (adjudicated, already on a concept or intersection page). A pass in one of these sources for another reason writes its `hub_line` then.

## 4. Entities — tag, never page

Tag the actors (`CLAUDE.md` → *Entities*, `schemas.md` §5). **Never write an entity as a `[[wikilink]]` in prose**: bold the name, slug in `entities:`. A deal with a 2a record is not also written as a dated fact; one that failed the test is.

## 7. Flag contradictions

**Whether a genuine conflict exists (not a trajectory, a caption against a dateline, or one account a superset of another) is the pass's own judgment**, against what the affected page already states. **File, never research; never silently overwrite.** `needs-review` on affected pages, one item per conflict in `reviews/contradictions/open/` carrying a **paste-ready, wiki-agnostic research brief**: the claim, each competing value, who asserts each, the URLs CC holds (`CLAUDE.md` → *Working the base*), and a plain instruction to investigate and date each value. **The brief is the record at the time it's filed** — a slice names it in its returned tally (step 11's own count), and the run's one `logs/log.md` close (below) is where it's counted, not a line written here.

## 8. Absences

A specific known **document** the wiki wants and doesn't hold: `reviews/acquisitions.md`, drained by `run acquisitions`. **Gap probes are that pass's alone** (`intake.md` §7a); ingest does not search. Anything neither queue can close is a **horizon** (`CLAUDE.md` → *Working the base*).

**Only the run's first ingest may write an acquisition line, by any route** (this step, step 1, step 3, a 2a driver); later ingests write a horizon instead. **Absent a stated iteration, an ingest is the first**; **`UPDATE-WIKI.md`, the only caller that loops, alone must state the iteration**, in every Phase A slice's spawn prompt.

## 11. Move the item out of `new/` — the item's last step

Move it to **`raw/YYYY/`**, prefixed `YYYY-MM-DD` from `published` (`layout.md` §3); an artefact shares its companion's prefix.

**Append its deltas to `logs/ingest-pending-writes.md`**, one line per affected **subject**, naming the source slug and what Phase B is to write; places contribute nothing. Its existence means Phase B is outstanding.

**Write its `logs/sweep-url_log.md` line here, at disposition, for all four** (`python scripts/url-log-append.py {admitted|dropped|contradiction|acquisition} URL`) and for an admission `python scripts/raw-url-index.py --append URL FILE PUBLISHED`, after the file is in `raw/` and before the candidate leaves `new/`. Never batch these to the close.

---

# Ending the run

**If this run admitted any finance record, run `FINANCE-COMPILE.md`**. **Then `HUB-COMPILE.md`, scoped to the places this run touched.** Both fire however ingest was invoked and are never left pending. Confirm every adjudicated item has its step-11 `sweep-url_log.md` line.

**A delta row never asserts an absence the writing slice has not just checked.** "Not held", "an acquisition line is open" and "record as unestablished" are copied onto a wiki page as prose by Phase B, and they have been wrong in every run that measured it: documents held since before the row was written, documents the same night's acquire pass fetched an hour later, instruments held under a second name. **Re-grep `raw/` and `lookups/raw-url-index.csv` by the document's own identity — title, instrument number, author and year — immediately before writing the row**, and where the absence is real, say what was checked and when, so Phase B can see the claim's age. A row whose absence has gone stale by the time Phase B reads it is the writer's defect, not Phase B's.

**Write the run's one `logs/log.md` line here** (`STATUS.md` → *The `log.md` entry*), aggregating every slice's returned tally into a single close — items in, the four dispositions, contradictions/acquisitions raised. No slice writes its own. **Then stamp the collection window** — `python scripts/cycle-manifest.py --stamp --sweep-closed <> --ingest-started <> --last-admission <this line's own stamp>` (`intake.md` §6a holds what the first two mean and who measures them). Whichever pass next mirrors reads this stamp into `cycle-manifest.json`'s `collection` block, which is what CORPUS bylines the bulletin from — so a run that skips this step leaves that block stale, not absent.

**Report: the one line of `STATUS.md` → *The close report*, nothing else**, the tally line carrying items in and the four dispositions. **`logs/ingest-pending-writes.md` non-empty is the normal end state**: the close never runs Phase B and never checks `python scripts/uncited-sources.py`; both are `WIKI-SYNC.md`'s close.
