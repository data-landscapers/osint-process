<!-- reader: cc; type: runbook -->
# INGEST.md — the ingest pass

Trigger: **"run ingest"**. Drains `new/`, **the only door into the base**. Never `new-budget/`.

**Four dispositions**, one per item: **1. `raw/`** (admitted); **2. contradiction** — a brief (step 7), item deleted; **3. acquisition** — a line (step 8), item deleted; **4. delete**. A source may *also* spawn either; leaving `new/` is not admission.

**Budget documents** are admitted as companion records (`source_tier: budget-document`); a bare budget artefact is catalogued on the spot per `BUDGET-COLLECT.md` steps 2–3.

**Only the procedure lives here**: schemas in `layout.md`, `schemas.md` §4–5, `intake.md` §6–7; the reasoning in `wiki/ingest-judgment.md`. **Step numbers are permanent handles** — never renumber.

---

## The shape, the slicing, and a dead slice

**Ingest never opens a place hub** (`hub_line`, 4a; `HUB-COMPILE.md` at the close). **Phase A decides per item; Phase B** (steps 5, 6, 9, 10, draining `logs/ingest-pending-writes.md`) **is `WIKI-SYNC.md`'s**, off the nightly path.

Above ~15 items, **slice Phase A into sub-agents of ~10** on explicit file lists, **spawned by the parent in parallel batches**; each slice gets `wiki/brief-ingest.md` and returns its tally line plus its delta lines **verbatim, never a summary**. No slice writes `logs/log.md` or spawns another.

**In a parallel run a slice writes only `logs/sweep-url_log.md`, through its locking appender**; its rows for the URL and md5 indexes, pending writes and acquisitions go to a slice-named file, and the parent appends them and reconciles before Phase B (`ingest-judgment.md` §1). Run alone, a slice writes the registers directly. The register and deletion rules are the brief's.

**A dead slice is requeued**: re-dispatch what is still in `new/`, in smaller slices; never reconcile `new/` against `raw/`.

## Two lanes

**The backfill lane skips exactly the three rows below.** It opens on `update wiki backfill` and on the cycle's Phase A over `X:\new-queue\` batches; `python scripts/ingest-lane.py` assigns it off `sweep_batch:`, and **the parent names the lane in every spawn prompt** — a slice not told is news.

| Step | News lane | Backfill lane |
|---|---|---|
| 1 origin | script, then per-item adjudication where no `sweep_batch:` | script only |
| 2 dedup | tiers 1–3 | **tier 1 only**, no model judgment |
| 4a hub line | authored, or a recorded refusal | `hub_line_none: <date>  # backfill lane — baseline, not news` |

**`catalogue_hero` (3a) is written in both lanes.** **Skipping tier 3 does not license admitting a twin step 3's read makes visible** — dispose of it under `CLAUDE.md` → *Duplicates*, a `FLAG-SLUG` included, and check the target `raw/YYYY/` path for a same-slug file before the move (`ingest-judgment.md` §2).

---

# Phase A — decide (per item)

## 1. Intake screen (first, always)

- **`python scripts/origin-screen.py` first**; **`DROP`/`WATCH` is the gate, `NOVEL` a report.**
- An item without `sweep_batch:` also gets a per-item origin adjudication (lint #17).
- **Second-hand or AI synthesis**: stage the primaries it cites and **delete the synthesis**.
- **Out of scope** (`CLAUDE.md` → *The material*): reject and delete; **in doubt, reject**, once.
- **Undated or unattributed but load-bearing**: a provenance hunt in `reviews/contradictions/open/`; delete the item.

## 2. Deduplication — three tiers, cheapest first

**Tier 1, mechanical, never skipped, before any body is read**: `grep -F` the normalised URL in `logs/sweep-url_log.md` **and** run `python scripts/raw-url-index.py --check URL`; neither substitutes for the other. A prior adjudication, `DUP-EXACT`, `DUP-SLUG` or `REJECTED`: **drop, log one line, never read the body** — unless the held record is a landing page, an excerpt or a cap-truncated capture, when **the arrival is its completion**: overwrite the held body in place, no second record, no citation rewired (`schemas.md` §4). `FLAG-SLUG` goes to tier 3. An `acquisition` line is not an adjudication; **a budget record dedups on `deal_id`**, a hit merges.

**A clean tier 1 settles nothing**: twins are not URL-shaped (`ingest-judgment.md` §2). Where step 3's read makes a twin or a completion visible, `CLAUDE.md` → *Duplicates* governs, including retiring the held record; a grep of `raw/` by the document's title and identity settles it without opening a body.

**Tier 2, narrow**: `raw/` filenames within a few days of `published` sharing a place or an entity. **Tier 3, one judgment on titles and ledes, drop-by-default**: match event + entities + date, never open a held body, **drop unless clearly a new event** — except an institution's own primary of a held secondary (*Replace*) and an arrival carrying a dated figure, named party or primary link the held record lacks (*keep both*). Sources that **disagree** are a contradiction (step 7), never a duplicate.

## 2a. Finance branch

`finance.new` or `finance.mou` runs `wiki/finance-news-driver.md` first — its five-fact test decides merge, a new deal record into `new/`, or an ordinary source with the failed fact stated unestablished. `finance.budget` runs no driver. Finance items get no hub bullet and no place delta.

## 2b. Amendment branch

An item that **amends, supersedes, repeals, replaces or postpones** a named instrument: grep the corpus for its name, number and the superseded value; **add every page stating the old value to step 11's deltas**; correct as supersession — new value dated, at most one dated prior, no brief.

## 3. Create the source page

Frontmatter per `schemas.md` §4, **`catalogue_hero:` included** (3a), facets per `facets.md` §1, the **full verbatim body**. `body_completeness:` is `full`, `paywalled` (free lede only) or `excerpt` (truncated or unavailable: **flag, never retry**).

- **Every `topics:` value is checked against `lookups/taxonomy.md`**: truncate a compound to its valid prefix, correct or drop anything else. Bilateral aid, donor funding and project finance are `finance.*`, never `geopol.*`.
- **Staged `published:`, `places:`, `topics:` and `body_completeness:` are guesses: check them against the document's own imprint**, which wins — dateline, masthead, gazette number, the place the story is about; a disagreement goes in `note:` (`ingest-judgment.md` §3).
- **Read the body against its title**: another document, navigation or a stub is not the source; a fetch-failure note is not an `excerpt`.
- **Download the primary document** an item announces or links, as artefact plus companion (`layout.md` §3); one attempt, then step 8's line naming the document.

## 3a. Write the catalogue hero

**Every source gets a `catalogue_hero:`, gated by nothing, never refused** — the contract is `schemas.md` §4 (≤120 characters, one line, complementing the title). A slice writes its batch with `python scripts/catalogue-hero-set.py`.

## 4a. Author the hub line

**`hub_line:` is one plain sentence** on the source page — a bolded claim, then dated specifics and topic wikilinks, date and place from the frontmatter. **No `hub_line`, no bullet**; a refusal is recorded, never blank: `hub_line_none: <date>  # <reason>`.

**One event, several accounts**: before `HUB-COMPILE.md`, group by **place + event against the held corpus** (`lint-duplicate-sources.py --max-gap`); one carrier keeps `hub_line:`, the rest go in its `hub_line_sources:` **and each gets `hub_line_none:`**. Grouping, and the classes that correctly get none: `ingest-judgment.md` §4.

## 4. Entities — tag, never page

Tag the actors (`CLAUDE.md` → *Entities*); bold the name in prose, never a `[[wikilink]]`.

## 7. Flag contradictions

**Whether a conflict is genuine** (not a trajectory, nor one account a superset of another) **is the pass's judgment. File, never research; never overwrite silently**: `needs-review` on affected pages and one brief per conflict in `reviews/contradictions/open/` — the claim, each value and who asserts it, the URLs held, an instruction to investigate and date each.

## 8. Absences

A specific **document** the wiki wants and does not hold is a line in `reviews/acquisitions.md`; ingest never searches for gaps. **Only the run's first ingest writes acquisition lines**; later ones write a horizon. An ingest is the first unless its prompt states otherwise (`UPDATE-WIKI.md`).

## 11. Move the item out of `new/` — its last step

Move it to **`raw/YYYY/`**, prefixed `YYYY-MM-DD` from `published`; an artefact shares its companion's prefix.

**Append its deltas to `logs/ingest-pending-writes.md`**, one line per affected **subject**, exactly `` - `subject` — [[slug]] — what to write `` (em dashes; `status.py` and `WIKI-SYNC.md` count only that shape). **A delta never asserts an absence the slice has not just checked**: re-grep `raw/` and the URL index by the document's identity first, and say what was checked and when.

**At disposition, per item, never batched**: `python scripts/url-log-append.py {admitted|dropped|contradiction|acquisition} URL`; for an admission `python scripts/raw-url-index.py --append URL FILE PUBLISHED`, plus `python scripts/artefact-md5-index.py --append <artefact>` for a binary artefact. **A drop carries its code and batch** — `url-log-append.py dropped --code CODE --batch <sweep_batch:> URL`, the code from `intake.md` §7 (scope `off-topic`/`off-place`, origin `inadmissible-origin`, tier 1 `already-seen`, a twin `already-held`, a *Duplicates* drop `no-value`). In a parallel run every row but the URL-log line goes to the slice's own file.

---

# Ending the run

**Run `FINANCE-COMPILE.md` if any finance record was admitted, then `HUB-COMPILE.md` scoped to the places touched** — whatever invoked ingest. Confirm every adjudicated item has its URL-log line.

**Write the run's one `logs/log.md` line**, folding every slice's tally, **then stamp the collection window**: `python scripts/cycle-manifest.py --stamp --sweep-closed <> --ingest-started <> --last-admission <that line's stamp>` (`intake.md` §6a). **Report the one line of `STATUS.md` → *The close report*.** Pending writes left for `WIKI-SYNC.md` are the normal end state.
