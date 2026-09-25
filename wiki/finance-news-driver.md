<!-- reader: cc; type: spec -->
# Driver — finance from prose sources (news, releases, filings)

Feeds `wiki/finance-record-spec.md` from **narrative sources** rather than a dataset: an on-the-record news report, a DFI or foundation press release, a company statement, a filing. One source may yield **zero, one or several** deal records.

This driver does two things: apply the spec's **five-fact test** to prose, and extract the core fields from sentences rather than columns. All record-shaping, tagging, dating, enrichment, merging and verification live in the spec — not restated here.

Two modes, same logic:

- **Back-swing** — a periodic pass over finance items already in `raw/`. Invocation: **"run finance back-swing"**.
- **Capture** — one item at a time, invoked from the ingest branch (`INGEST.md` step 2a). Not separately triggered.

## The gate

Run the spec's **five-fact test** verbatim. In prose the failures cluster predictably, so read for these:

| Fact | Passes on | Fails on |
|---|---|---|
| 1 financier | a named institution or firm | "development partners", "investors", "a consortium", an unnamed government fund |
| 2 recipient place | a country, or a bounded region in `countries.csv` | "across Africa", "several countries" with no list, a purely corporate story with no operating geography |
| 3 commitment amount | "committed", "approved", "signed", "pledged", "a $Xm facility" — **or a disbursement actually made** | "plans to invest"; "up to $X" with no basis; "aims to mobilise $Xbn"; a market-size or valuation figure |
| 4 date | a stated commitment/approval/signature date or year | only the article's own publication date |
| 5 purpose | a stated, specific use the money is put to — **mappable**, even if the slug isn't settled yet | money to a country with no stated use; "digital transformation" as a bare slogan with no named activity |

**Two traps specific to prose.**

- **The publication date is not the event date.** An article dated 2026-07 reporting a commitment "made last year" gives fact 4 as `2025`, precision year — never `2026`. If the source only dates its own publication, fact 4 fails.
- **Announcement ≠ commitment.** An intention to invest, a target, an MoU *aspiration* or a fundraising goal is not a commitment amount. A signed MoU with a stated sum *is* a record (tagged `finance.mou`, `status: Approved` or `Pipeline` as the source supports); an ambition to "mobilise $Xbn" is not.

**Origin screen — this driver builds non-state records only.** A **domestic-state** item — the funder is the recipient country's own government, a ministry or an entity it owns (an annual ministry budget or appropriation, a sovereign guarantee, a state-agency allocation) — is **out of scope for this driver, and is handed to `wiki/finance-load-domestic-state.md`**, which carries the budget-cycle, fiscal-year and classification fields those items need. It is not a gate failure. Prose is a legitimate source there, exactly as it is here: case 4 of that driver's *five cases* builds a record from reporting alone where the five-fact test passes.

An item passing the test with **several distinct deals** yields one record each, provided each deal independently carries all five facts. A deal named only in passing, without its own amount or date, is not a record — it stays in the verbatim body.

## Prose → core fields

Everything is read from the source's own words; nothing is normalised — **except Instrument, Status and Beneficiary type**, which take a controlled value from `lookups/deal-vocabs.csv` (`DEAL-VOCAB.md`). The source's own wording for those three goes in `## Notes`, not the cell.

| Core field | Where it comes from |
|---|---|
| financier | the named funder; resolve to a slug already used in `raw/`'s `entities:` tags — mint one consistent new slug only if none exists, never slug ad hoc. (There are no entity pages to check against. The load's financier crosswalk is finished and archived; don't consult or extend it) |
| recipient / place | the named counterparty (blank is fine) + its ISO-3 or `X__` |
| title | a plain descriptive title CC writes: `<financier> — <recipient or purpose>, <year>`. The article's headline is usually editorialised; don't reuse it |
| description | **the source's own sentences describing the deal**, quoted, not paraphrased |
| instrument | only if stated (loan, grant, equity, guarantee, concessional facility). **Blank is normal and is not a failure** |
| status | only if stated; map to the enum (`Approved` / `Active` / `Closed` / `Pipeline`) |
| commitment / original amount + currency | the announcing party's own currency; a USD figure written as a dated conversion per `CLAUDE.md` → *Currency* |
| co-financing | named co-funders and sums if given; they stay in the body, not as entity tags |
| commitment / start / end year | the event year per fact 4 |
| disbursed | only if separately stated |
| amount quality | `reported` for a press figure; `verified` only where a primary confirms it |
| subject category | **unclassified** route — classify from content straight to a `taxonomy.md` slug (spec §Subject tag) |
| project_id / IATI ID | if the source names one — these are what make a later merge *definite*, so capture them whenever present |
| source URL / type / access date | the source page itself |
| `finance_origin` | always **`non-state`** in this driver's output (DFI, foundation, private, bilateral, multilateral). Read the origin to APPLY the *Origin screen* above — a **`domestic-state`** item (funder = the recipient's own government or an entity it owns) is skipped, not recorded, and awaits the domestic-state driver. Never default it |

`deal_id`: `<financier-slug>-<recipient-slug-or-iso3>-<year>`, suffixed `-02`, `-03` on collision. Stable, so a re-encounter of the same deal collides rather than duplicating.

## Merge or create

Per the spec's *Store of record*: **definite match → merge** (shared `project_id` / `iati_project_id`, or unambiguously the same financier + recipient + native project identity) — fold only the genuine added detail into `## Development history` as one dated attributed line, and update status/disbursed. **Fuzzy match → cross-reference, never merge**, and don't count it in the aggregate.

A source that passes the test but reports a deal the wiki already holds in full adds nothing: note it in one line, no record, source filed normally.

## Back-swing mode

Candidate set: `raw/` items carrying `finance.new` or `finance.mou`, **excluding** those that already have a `deal_id`. Work the whole set in one pass, not a selection.

For each: apply the gate → build record(s) into `new/` → the ordinary ingest pass admits them. **The source page stays where it is and is not rewritten** — the record cites it. A back-swing record is a structuring of held material, so enrichment is optional; where the held body is an excerpt, the primary is worth one fetch.

Log per item: `deal_id | source file | pass | failed-fact NN`. Failures are one-liners, not a queue — a failed item is already correctly filed as a source.

## Capture mode

Invoked at ingest for any item tagged `finance.*`. Gate → build record → the record enters `new/` alongside, and the source itself files to `raw/` as normal. **No per-deal hub bullet** — hub presence is built by `FINANCE-COMPILE.md` in aggregate.

## Close

Terse per `CLAUDE.md` → *Reporting*: records built, merged, and the failed-fact distribution. Then the status line.
