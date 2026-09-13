# BUDGET-EXTRACT.md — the budget extraction pass

Trigger: **"run budget extract"**, optionally scoped (`run budget extract for South Africa 2024`). Drains `new-budget/` one country-year at a time: reads the held budget documents, builds finance records into `new/`, and archives what it has processed.

This file is the loop. The strategy library (`documentation/budget-extraction-strategies.md`) holds how to read each document shape; `wiki/finance-load-domestic-state.md` and `documentation/domestic-budget-extraction.md` hold what a figure means.

## Where things sit

| Folder | State | In git? |
|---|---|---|
| `new-budget/{ISO3}/{FY}/` | held, not yet extracted | markdown yes, PDFs no |
| `budget-archive/{ISO3}/{FY}/` | extracted; the artefact and its extracted tables | CSVs yes, PDFs no |
| `new/` | records and source pages awaiting ingest | yes |
| `raw/` | admitted | yes |

Artefacts (`*.pdf`, `*.xlsx`) are git-ignored and sync via Dropbox; the manifest row, companion page and extracted tables are committed.

## Scope of a run

**Work country-year by country-year, over all of that year's documents at once, never a selection.** A run is one `new-budget/{ISO3}/{FY}/` folder; two fiscal years never mix.

**`{FY}` is always the bare start year** — `new-budget/ZAF/2024/`, never `2024-25` (`layout.md` §2).

The folder and `manifest.csv`'s `fiscal_year` say which run acquired the document; the companion page's `fiscal_years_covered` says which years it supports. Extract by folder; build records by `fiscal_years_covered`.

**Run over every country-year folder present**; anything still in `new-budget/` is unfinished work for this pass. Never clear a populated folder; drain it.

## Re-extract — reopening archived documents

**Trigger: "run budget re-extract"**, optionally scoped. Re-extract is how a capability added to the library later reaches an archived document. Two manifest columns record *what* was extracted:

- **`extracted_scope`** — `sector-vote` | `cross-vote` | `narrative` | `n/a`.
- **`re_extract`** — `no`, or a note naming what is missing and why.

### The loop

1. **Select** documents whose `re_extract` is not `no`; if blank, set it by comparing `extracted_scope` with what the library can now do.
2. **Read the archived artefact in place**; never move it back.
3. **Extract only the newly-in-scope rows** to additional CSVs named for the new scope (`b5-2024-cross-vote-schedule.csv`); never overwrite the originals.
4. **Definite-match before creating** (spec → *Store of record*): same `deal_id` stem → merge or drop.
5. **A disagreeing figure is a contradiction**, filed, never resolved by preferring the newer read.
6. **Set `extracted_scope` and `re_extract: no`.** Nothing moves.

**Never re-extract candidates**: the statistical annexure (vote-total granularity) and any department's annual report (an acquisition). An "Of which" earmark nesting inside a held record is annotated there, never re-opened as a separate line.

## When it runs

**As step 4 of `COUNTRY-BUDGET-BATCH.md`** — after its three sweeps and **before** its `update wiki` — and on demand. **This pass is the only thing that drains `new-budget/`**; `update wiki` neither drains it nor gates on it. Full chain: **sweep → budget extract → update wiki [ingest → finance compile].** Extract writes to `new/` and stops. After a batch run, review the archetype entries step 4 added unreviewed.

## The loop

### 1. Inspect

Read every document's structure before extracting: `pdfinfo` for pages and producer, `pdftotext -enc UTF-8 | wc -c` for the text layer, `pdftotext -enc UTF-8 -layout | grep -n` for table captions. Name the archetype each document matches.

**Always pass `-enc UTF-8`** on every `pdftotext` invocation, including a bare `| wc -c`; the Latin-1 default mangles accented characters. LINT #31 checks it.

**No text layer → OCR it.** If `pdftotext -enc UTF-8 | wc -c` returns near-zero, run `python scripts/ocr-pdf.py DOC.pdf --lang fra -o DOC.ocr.txt` and read the sidecar as `pdftotext -layout` output. Languages `eng`, `fra`, `por`, `ara`, combined with `+`. About a page a second, so give it a page range once the tables are located. The sidecar is committed beside the PDF.

**OCR digits are not evidence until they cross-foot** (archetype H, every scanned document): prefer a narrative statement of a figure over a table; verify every table digit by the document's own arithmetic; a digit that will not cross-foot is not recorded. Try `--psm 6`, `--threshold 2` (faded print) and `--digits` (numeric-column crop) before giving up on a table.

Where OCR yields nothing usable, record the dated absence on the affected page (one acquisition line if the fuller volume is wanted), then archive per §6 with `extracted_scope: n/a` and `re_extract: OCR-illegible`. Documents archived `re_extract: OCR-needed` are re-extract's, not this pass's.

Order the documents by **stage** — appropriation, adjustments, outturn, audit. Later stages are **folded into the same line-year record**, never written as new per-stage files (driver → *Budget stage and version*).

### 2. Review the strategy library

Does `budget-extraction-strategies.md` hold an archetype that covers the document? **Yes → 3. No → 4.** A match is noted in the run log; the library grows only on genuine structural novelty.

### 3. Extract

Follow the archetype's strategy. Before writing anything:

- **Run the reconciliation table** in the strategy library. Resolve a mismatch before recording; file a genuine disagreement to `reviews/contradictions/`.
- **Confirm the scale per table**, not per document: capital + recurrent = total.
- Write the extracted tables to `budget-archive/{ISO3}/` as CSV, one per source table, named for the document and table.

**Extract to the finest level the document prints**: sub-programmes where printed, with the full classification chain (`admin_head`, `spending_entity`, `programme`, `sub_programme`, each with its printed code) and the economic classification. Never record both a programme and its own sub-programmes — they would sum (`finance-load-domestic-state.md` → *The record's grain*).

Then hand each digital line to `wiki/finance-load-domestic-state.md` (five-fact test, scope test, origin gate, record shape). Records land in `new/`.

### 4. Modify the strategy library, then extract

Add **one archetype entry** in the shape of the existing ones: layout, strategy, traps, what it yields. Then go to 3.

**One modification attempt per document.** If it still resists, stop: log `extraction failed — <reason>`, record what was tried in the country's section of `domestic-budget-extraction.md`, move on, and state the absence on the place hub, dated, if it matters.

### 4a. Cross-vote scan — do not stop at the sector vote

**Where the country-year holds a full estimates volume, scan every vote in it**, per *The cross-vote scan* in the strategy library. **A total built from the sector vote is not a total.**

Two categories — **identity and data exchange** and **governance structures** — are named for function or institution, never technology, and need a hand-search of the vote index rather than a keyword grep (vocabulary in the strategy library).

**End the scan with what was looked for and not found** — a data protection authority with no appropriation is a finding — as a dated statement on the place hub of what is not established (`CLAUDE.md` → *Currency*).

**Where no full volume is held**, say so in the close and on the place hub — *sector-vote coverage only; cross-vote digital spend not established as at &lt;date&gt;* — and add the volume to `reviews/acquisitions.md`.

### 5. Case 5 — the budget document becomes master for records built from reporting

Before finishing the country-year, grep `raw/` frontmatter for this country's `finance_origin: domestic-state` records for the fiscal year whose **`source_tier` is not `budget-document`** (`reporting` and `official-statement` alike). Case 5 in the driver: the document's `appropriated` stage **becomes the record's baseline and master** on the same `deal_id` stem; the superseded figure becomes a dated `## Stage history` entry, never a sibling file; **a figure disagreement is filed as a contradiction, never overwritten**. Do not skip it.

### 5a. Record what was extracted, not just that it was

As the extraction finishes, set **`extracted_scope`** and **`re_extract`** for every document in a three-column CSV — `stem,extracted_scope,re_extract`, the stem any distinctive fragment of the artefact's filename — which is step 6's input. `sector-vote` when the library could only do sector-vote is not a failure; it becomes a work item when the library grows.

### 6. Archive

```
python scripts/archive-budget-docs.py --country {ISO3} --scope scope.csv          # dry run
python scripts/archive-budget-docs.py --country {ISO3} --scope scope.csv --apply
```

It moves the artefact and companion page to `budget-archive/{ISO3}/{FY}/`, sets `extracted`, `extracted_scope`, `re_extract` and `archive_path` from step 5a's CSV, and removes the emptied folders. **A document with no scope row aborts the run before anything moves.**

**Moving the file is the last step**, so an interrupted run resumes on the documents not yet processed; a row already carrying `extracted` is never touched. `--verify` reports the manifest without changing anything.

**Delete the emptied folders** — `new-budget/{ISO3}/` too if no year folders remain. Never delete **`manifest.csv` rows**, **anything in `budget-archive/`**, or a folder still holding an unprocessed document.

## Close

Report terse (`CLAUDE.md` → *Reporting*):

- documents processed, by archetype; archetypes added
- records built, by `budget_stage`
- **cross-vote coverage**: votes beyond the sector vote that yielded lines, or no full volume held
- **execution rates found**
- reconciliation mismatches, and how each resolved
- case-5 resets applied, and contradictions filed
- documents that failed extraction, and why
- what was appended to `domestic-budget-extraction.md`

Then the status line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

`new-budget/` is **not** counted in *awaiting ingest* (`layout.md` §2); report what remains in it as a separate line.

Then run **update wiki** — its ingest admits the records and self-runs **finance compile** (`INGEST.md` → *Ending the run*). Inside `COUNTRY-BUDGET-BATCH.md` that is step 5; after a hand-run extract, run it yourself.

## Notes

- **This pass reads documents; it does not fetch them.** A document the wiki wants and lacks goes to `reviews/acquisitions.md`.
- **Not idempotent.** Re-running over an archived country-year would rebuild admitted records; scope re-runs to `new-budget/` contents.
- **Feed the sweep back.** A document that supports no record is noted in the run log and the strategy library's *Not worth extracting* section, so `DOMESTIC-FINANCE-SWEEP.md` stops fetching it.
