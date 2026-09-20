# layout.md — folder structure and filenames

Split out of `reference.md`; section numbers are kept so a `§N` reference resolves unchanged. `CLAUDE.md` holds the principles and wins where the two disagree.

---

## 2. Folder structure

```
new/                      # unprocessed intake queue — clips AND sweep candidates land here; drained on ingest
new-queue/                # not a sweep target; sweep writes straight to new/
  done/                   # BILL'S. Human-owned; CC does not read, write or drain it
new-budget/               # budget documents awaiting extraction — NOT an ingest queue
  {ISO3}/{FY}/            #   artefact (PDF/XLSX) + its companion markdown, together
  manifest.csv            #   what is held and which country-year it belongs to
budget-archive/           # budget documents already extracted (BUDGET-EXTRACT.md)
  {ISO3}/{FY}/            #   artefact + companion + the extracted tables as CSV
                          #   source PDFs untracked (.gitignore); companions, CSVs, .txt
                          #   sidecars and the .xlsx primaries all tracked. A fresh clone
                          #   has the text, not the PDFs: re-extract needs the backup mirror.
sweep/                    # acquisition-sweep STATE (procedures are root SWEEP-DAILY-LIST.md /
                          #   DOMESTIC-FINANCE-SWEEP.md / SWEEP-{NEWSPAPERS,JOURNALS,THINKTANKS}.md — upstream of new/):
                          #   daily/           (daily sweep state, manifests, drop logs,
                          #     and history.md — the dated record; not operative)
                          #   domestic/        (domestic finance sweep state)
                          #   donor/           (the IATI poll's state: seen-ids.txt,
                          #     the scoped activity-ID memory, plus its manifests
                          #     and drop logs — SWEEP-IATI.md)
                          #   journals/ newspapers/ thinktanks/   (content-sweep folders:
                          #     drop logs only — the sweeps are stateless, windowed by
                          #     the cycle from sweep-cycle_log.md)
                          #   domains/         (per-domain handling notes, one file per
                          #     sweep-daily.csv row — dead paths, cache-bust strings,
                          #     yield inversions. Loaded ONLY when a domain misbehaves)
                          #   archive/         (completed Phase-2 back-fill apparatus)
                          #   recapture/       (SPENT TOOLING — see note below)
raw/                      # admitted sources, sharded by publication year — immutable
                          #   after ingest (one bounded exception: verbatim fidelity
                          #   re-capture, schemas.md §4)
  2026/                   # the shard is the filename's own YYYY- prefix, so a file's
                          #   folder is derivable from its name and nothing else (§3)
    2026-06-16-cassava-nvidia-deal.md
    2026-06-16-cassava-nvidia-deal.pdf
                          # an artefact sits beside its companion page — same date
                          #   prefix, therefore same shard, so `artefact:` stays a bare
                          #   filename and resolves as a sibling
                          # (no _leads/ — ingest has four dispositions,
                          #  raw / contradiction / acquisition / delete — no parking folder)
logs/                     # the operation record — append-only, not pages. wiki/ is pages only.
  log.md                  # append-only operation log (Decisions live here). Newest first;
                          #   scripts/rotate-log.py truncates it to ~400 lines at every cycle
                          #   close, git holds the rest
  ingest-pending-writes.md# TRANSIENT: ingest Phase B's queue (page writes owed after the
                          #   items were filed). Non-empty = a half-finished ingest; deleted
                          #   when drained, not aged
  sweep-url_log.md        # machine INDEX: every adjudicated URL + disposition, normalised.
                          #   Sweeps grep it to filter returns (pruned to one rotation by
                          #   SWEEP-CYCLE.md)
  collection-stamp.json   # GIT-IGNORED: sweep_closed/ingest_started/last_admission from
                          #   whichever pass most recently closed ingest (cycle-manifest.py
                          #   --stamp), read into cycle-manifest.json's collection block at
                          #   the next close. Single overwritten object, never pruned.
  drop-list.csv           # inadmissible-origin list (origin-screen.md). PROCESS-WRITTEN:
                          #   any pass that runs the screen appends its own row

lookups/                  # controlled vocabularies and source lists — the tables the passes
                          #   read. wiki/ is pages only.
                          # OWNERSHIP IS PER FILE, NOT PER FOLDER — see below.
  taxonomy.md             # SUBJECT controlled vocabulary (authority)        [PROPOSE]
  countries.csv           # PLACE controlled vocabulary (authority)          [PROPOSE]
  sweep-daily.csv         # daily sweep input list (read fresh each run)     [BILL]
                          #   cols: url,title,notes_file -> sweep/domains/{domain}.md
  sweep-journals.csv      # content sweep: journals (url, Title, Description) [BILL]
  sweep-newspapers.csv    # content sweep: newspapers (URL, iso-3, Title)    [BILL]
  sweep-thinktanks.csv    # content sweep: organisations (URL, Title, Focus) [BILL]
  sweep-regional-orgs.csv # regional sweep: institutions                     [BILL]
  financier-names.csv     # financier_slug -> canonical display name         [CC]
  intersection-names.csv  # place -> the prefix its intersection pages use   [CC]
                          #   cols: place,name,kind,prefix — one row per
                          #   place in countries.csv, so a slice reads the
                          #   prefix instead of deriving it (§3). Job 96.
  fx-imf-annual.csv       # IMF annual average rates, (currency, year)       [CC]
  budget-init-backlog.csv # countries not yet budget-initialised             [CC]
  raw-url-index.csv       # the raw/ dedup lookup (INGEST.md step 2, the      [CC]
                          #   sweeps' section 3).
                          #   cols: url_normalized,slug_key,file,published —
                          #   one row per unique `url:` held in raw/. Written
                          #   by ingest only (a sweep reads it, section 7);
                          #   scripts/raw-url-index.py, lint #27.
  region-membership.csv   # slug,entity_type,places — the institution half   [CC]
                          #   of a region's scope; a frozen snapshot read
                          #   by CORPUS's report-region-init.py, never by
                          #   anything in OSINT. scripts/build-region-membership.py
  frontmatter-schema.json # schemas.md §4's schemas, machine-readable — what  [CC]
                          #   lint's deterministic checks validate against. A
                          #   restatement, never a second authority: where they
                          #   disagree, §4 wins and the schema is the thing
                          #   that is wrong

reviews/
  contradictions/
    open/                 # one file per unresolved contradiction — the reconcile worklist
                          # (no done/ — a resolved brief is deleted, not filed: the
                          #  resolution lives on the page and in log.md, and git holds
                          #  the brief. No research/ either.)
  acquisitions.md         # fetch list for AUTOMATED fetches: documents the wiki wants and
                          #   lacks, one attempt each, drained by the acquisition pass
                          #   (the residue — documents whose automated route is PROVEN dead
                          #    and that Bill's browser gets in one click — moved to
                          #    X:\fetch-list.md, 2026-09-07)
  jobs-archive/           # completed batch runs: <filestem>-YYYY-MM-DD-HHMM.md (archived on completion)
outputs/                  # DERIVED exports — OSINT's own compile, not a website feed
                          #   (CORPUS authors the published output layer from raw/ / wiki/)
  budgets/                # {ISO3}-budget.csv — domestic budget line-years
  non-state-finance/      # {ISO3}-nonstate.csv, {ISO3}-summary.csv, all-nonstate.csv
                          #   (build-finance-page.py; not sources, never hand-edited)
                          #   what REPORT-LINT checks A–E reconcile against and
                          #   compile-hub-financing.py reads
index/                    # UNTRACKED derived index (build-index.py) — files.jsonl,
                          #   links.jsonl, meta.json, optional vault.db. Rebuilt from
                          #   scratch, never appended to, so it cannot drift; a
                          #   consumer rebuilds it itself when the vault has moved.
                          #   Derived, never a store: nothing cites it, and no fact
                          #   lives there that is not in a file
wiki/
  concepts/               # one page per SUBJECT topic
  places/                 # country + region hub pages (one page type)
                          # No entities/: companies, orgs, gov bodies, initiatives,
                          #   people, deals, resources and instruments are a tag
                          #   only (`entities:`), never a page
  intersections/          # topic × place — created LAZILY, only when substantive
  index.md                # master table of contents
  topics-index.md         # faceted navigation by subject
  places-index.md         # faceted navigation by place
  reference.md            # directory of the specs: facets.md, layout.md (this file),
                          #   schemas.md, intake.md, operations.md
  finance-record-spec.md  # the finance record spec (store of record, merging, compile)
  finance-load-domestic-state.md  # driver: domestic-state budgets/expenditure (invoked by ingest 2a)
  finance-news-driver.md  # driver: finance from prose sources (invoked by ingest 2a; back-swing)
scripts/                  # the tooling — see scripts/README.md for the directory
  archive/                #   SPENT: ran, cannot recur, kept for the audit trail
  extractors/{ISO3}/      #   BESPOKE: one country's document layout, may re-run
  tests/                  #   the fixture tests, for the scripts that move files
```

**`new-queue/done/` is Bill's.** Human-owned staging. CC does not read it, write to it, drain it, or count it in any tally.

**`{FY}` is always the bare start year — `2024`, never `2024-25`.** It means the fiscal year *beginning* in that year, so `2024` is South Africa's and Kenya's 2024/25 and Nigeria's calendar 2024 alike — the same resolution rule that governs instructions (`wiki/finance-load-domestic-state.md` → *Fiscal years*). One form everywhere: the instruction, the folder and the run identifier all read `2024`.

The document's own `fiscal_year_label` stays **verbatim** in its frontmatter (`2024/25`, `2024-2025`, `2017 EFY`). The folder is a path, not a citation.

`{ISO3}/{FY}/` applies to `new-budget/` and `budget-archive/` alike, so a document keeps its shape when it moves between them, and a country swept for several years cannot mix them.

**`new-budget/` is outside the ingest path, deliberately.** It holds budget documents — appropriation acts, estimates volumes, outturn reports, IFMIS and procurement extracts — staged by the domestic finance sweep (`DOMESTIC-FINANCE-SWEEP.md`) and drained by `BUDGET-EXTRACT.md`, which runs as **step 4 of `COUNTRY-BUDGET-BATCH.md`** or on demand. Nothing else drains it — `update wiki` does not.

- **Ingest never drains it.** A 600-page appropriation act is not a source to be read and filed; it is a structure to be learned.
- **The artefact and its companion markdown sit together**, same folder, same date prefix — not split across `new-budget/` and `new/`. The companion is a *description of a document not yet processed*, so filing it as a source would put a page in `raw/` whose `finance.budget` tag routes it to the domestic-state driver with no budget lines in it to find. The pair stays together until the pair is processed.
- **It is not counted as `awaiting ingest`** in `STATUS.md` — it has its own staging gate there, **awaiting budget-extract**, which stays off the standing tally line. Nothing reads that gate to decide whether to extract; the batch runs the pass unconditionally at its step 4. The sweep reports what it staged; `manifest.csv` is the standing record.
- **Nothing enters `raw/` from here except through the extraction pass** (`BUDGET-EXTRACT.md`, "run budget extract"). That pass produces source pages and finance records into `new/`, and ingest is still the only door. On completion it moves the artefact and its companion to **`budget-archive/{ISO3}/{FY}/`** alongside the tables it extracted as CSV — folder as state, as everywhere else — and **removes the emptied `new-budget/` folders**, so a folder that still exists always means work outstanding.

**`sweep/recapture/` is spent tooling**, not part of any standing procedure: the scripts and ledger of a one-off bulk verbatim re-capture (`run.py`, `retry.py`, `extract.py`, `progress.sh`, `ledger.csv`, `done/exa-recovery.csv`). The **ledger has provenance value** and records which held sources were re-captured; the scripts are reusable if another bulk re-capture is ever needed. Nothing reads it on a normal pass. Under `CLAUDE.md`'s month rule it is a deletion candidate — git holds it.

**The intake pipeline is physical** (`CLAUDE.md` → *Structure*). `new/` = not yet processed, `raw/` = admitted as a source. Everything not admitted leaves `new/` by deletion (its residual value captured first as a contradiction brief or an acquisition line) — there is no parking folder. The web clipper points at `new/`. "What's new" is the contents of `new/` — no diffing against the log. Each item's move out of `new/` is the **last** step of processing it, so an interrupted run leaves exactly the unfinished items in `new/` and re-running resumes cleanly.

### Who owns a lookup table — by file, not by folder

`lookups/` holds three different kinds of table, and only one of them is a curatorial choice. The folder map above marks each file; the bands are:

| Band | What it is | Who writes it |
|---|---|---|
| **[BILL]** | the **sweep source lists** — which publications the wiki reads | **Bill only.** This is editorial curation: what the wiki looks at is his call, and a pass adding its own sources would quietly redefine the corpus. A sweep records row health in `sweep/row-health.csv` and edits nothing (`intake.md` §7). |
| **[PROPOSE]** | the **controlled vocabularies** — `taxonomy.md`, `countries.csv` | **CC proposes, Bill rules.** A new subject slug or place code re-files every page that could carry it, so it is a modelling decision, not maintenance. Lint #2 already surfaces rather than invents one. |
| **[CC]** | the **derived and mechanical tables** the passes need to run — canonical name maps, published FX rates, work queues | **CC writes them**, in git, reviewed after the fact like any other write. |

**The test is what the table decides, not where it sits.** A table that records *judgment about scope* is Bill's; a table that records *a fact CC can establish* or *state CC must keep* is CC's. `financier-names.csv` is a slug → display-name map that lint #16 and REPORT-LINT check D both police, so a missing row is a defect CC detects and can fix.

The sweep source lists are Bill's, the `intake.md` §7 containment boundary keeps sweeps out of `lookups/` entirely, and a new vocabulary value is surfaced rather than invented. **Adding a file to `lookups/` means giving it a band** in the map above; an unbanded file is `[PROPOSE]` until Bill says otherwise.

---

## 3. Filenames

Every source in `raw/` carries a **`YYYY-MM-DD` date prefix** taken from its true **publication date**. This keeps `raw/` chronologically sorted and greppable by date, and the prefix carries real meaning for the currency discipline.

**The prefix also names the folder.** `raw/` is sharded `raw/YYYY/`, and a file's shard is the first four characters of its own name — so the path is derivable from the filename and never needs looking up.

- **Bare `[[wikilinks]]` are unaffected by sharding.** They resolve by filename across the vault regardless of folder, and stems are unique by construction. Citations are wikilinks, so nothing in the citation layer depends on the shard.
- **`artefact:` stays a bare filename.** An artefact carries its companion page's date prefix, so it lands in the same shard and resolves as a sibling.
- **CC establishes `published`; it isn't handed to it.** The web clipper cannot reliably supply a publication date. During ingest, read the clip content (or the source page) for the real date and **set or correct the `published` frontmatter and the filename accordingly**. This is an active step, not a passive read of whatever the clipper left.
- **Fallback chain, flagged.** Only when a publication date genuinely can't be found, fall back to **`ingested`**, then **`created`**. When you fall back, mark the source `date_source: proxy` so a clip-dated file is never later reasoned about as though that were its publication date.
- **Partial dates are padded, and the precision recorded.** The filename is always a valid, sortable full date; record the true precision as `date_precision: year | month | day` (default `day`). Padding is for sorting; the frontmatter keeps the honesty.
  - year only → prefix `YYYY-01-01`
  - month only → prefix `YYYY-MM-01`
- **All file types, not just clips.** PDFs, images and other artefacts follow the same rule — the clipper only prefixes markdown clips, so anything added by other routes must be prefixed on ingest.
- **Binary artefacts get a companion source page.** A PDF or image can't hold YAML frontmatter, so create a date-prefixed markdown **source page** carrying the frontmatter (places, topics, entities, `published`, etc.) that links to or embeds the artefact. Prefix **both** the source page and the artefact with the same date so they sort together.
- **An intersection page is `{prefix}--{topic-slug}.md`, and the prefix is read from [`lookups/intersection-names.csv`](../lookups/intersection-names.csv) — never derived.** A region uses its X-code (`xwa--dpi-pay`), a country the readable name recorded there (`cote-divoire--dpi-id`, not `civ--dpi-id`). **The table exists because the name form is not derivable**: COD is `drc`, CPV `cabo-verde`, STP `sao-tome`, each a better answer than slugifying `countries.csv` and none of them deducible from it. A slice facing a place whose prefix is not obvious was guessing, and guessed both ways inside one pass — which is how 60 pages came to carry a second form (job 96, ruled 2026-09-20). A place added to `countries.csv` takes a row here in the same edit.
- **Renaming must not break links.** Source pages are referenced by `[[link]]` from `sources:` lists. Rename via Obsidian (which updates links), or, if renaming on disk, update every referencing link and confirm with the dead-link lint. Do renames in git so they're reversible.

**Artefacts over 90MB are held on disk, not in git.** Large budget PDFs are working documents, not distribution artefacts: the wiki cites them by filename, and the bytes live on the local disk and its backups. **Git LFS is not a way round the bar.** `.gitignore` cannot express a size rule, so the known files are listed there by path and the bar itself is enforced by `.githooks/pre-commit` (enable with `git config core.hooksPath .githooks`). A record whose `artefact:` names such a file is **not** broken — the document is held, just not cloned; treat a missing artefact in a fresh clone as expected, not as a defect.

---
