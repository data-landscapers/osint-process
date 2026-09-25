<!-- reader: cc; type: spec -->
# Finance record — builder spec (source-agnostic)

Given a **single finance item** — a commitment, investment, guarantee, MoU or agreement, from any source — produce **one structured markdown record in `new/`**, ready for the normal ingest pass. This spec defines the record's shape and how to derive every field. **It never reads a particular file.** A **driver** pulls the fields out of a given source and hands them here: `wiki/finance-news-driver.md` (prose; back-swing and capture modes), `wiki/finance-load-domestic-state.md` (domestic-state budgets), `wiki/finance-iati-driver.md` (IATI activities), and the finished `archived-procs/finance-load-nonstate-csv.md`.

Values must be traceable to the source (or the primary at its URL); when a value can't be derived safely, **leave it blank and say why** — never guess, never write `0` for an unknown.

## The five-fact test — what makes an item a finance record

**No item becomes a finance record unless all five facts are present in the source itself.** Not inferred, not carried in from the wiki, not filled by the builder. Every driver runs this test before handing anything here, and names it rather than restating it.

1. **The financier is identified.** A named party providing the money. Resolvable to a canonical slug against the wiki's entity set (a financier with no existing entity is minted one consistent new slug, not a failure — see *Entities*). "An investor consortium", "development partners", "unnamed backers" — fail. For a domestic-state record the financier is the **fisc** — a named treasury, ministry of finance, sub-national government, levy fund or SOE spending its own revenue — an institution, never the officeholder announcing it.
2. **The recipient country or region is identified.** Must resolve to a `countries.csv` ISO-3 or `X__` region. This is the test, **not** the recipient organisation: a blank `recip_org` is normal and is handled per *Entities* below. "Across Africa" with no bounded region — fail.
3. **An amount that can be treated as a commitment is identified.** A figure the source presents as *committed, approved, signed or pledged* — **or a disbursement figure**, which evidences money actually moved and stands as the commitment where no commitment total is stated. Record which it is: a disbursed-only record carries `disbursed_usd` with `commit_usd` blank, never the disbursement copied into both. What fails is a figure that is neither — an "up to", an intention to invest, a mobilisation target, a valuation or market size. Carry the amount in the announcing party's own currency per `CLAUDE.md` → *Currency*. For a domestic-state record, a **budget figure at any stage** satisfies this — proposed (tabled), appropriated, released, executed, audited — with the stage recorded, never conflated: `budget_stage` carries the epistemic status, so a tabled figure is a record at `proposed`, not a failure. **MTEF and medium-term outer-year projections still fail**: they are indicative planning figures, the budget equivalent of an "up to".
4. **A date of the commitment is identified — a year is enough.** The commitment/approval/signature event, never the publication date. Padded to `YYYY-01-01` per *Dates*, or carried at its true precision where the driver knows one.
5. **The purpose can be matched to our taxonomy.** The test is **mappability, not completed classification**. The source must say what the money is *for*, in terms a `taxonomy.md` slug could be resolved from — but the resolving need not have happened yet. A stated purpose that is in-scope and specific enough to map admits the record, flagged for classification if the slug is genuinely uncertain. **What fails is an unspecified commitment**: money to a country with no stated use, or "digital transformation" as a bare slogan with no named activity. Never substitute a default slug — see *Subject tag* §1. For a domestic-state record this is where the **scope test** sits: the unit is the programme or project line whose stated purpose is a digital activity, never a ministry's total vote, and a mixed line's digital share is **never computed** — it is recorded whole and flagged (`scope_confidence`), so it can be reported apart from the clean total rather than silently inflating it.

**Failing the test is a routing decision, not a rejection.** An admissible, in-scope item that fails any of the five is still a source: it takes the ordinary `raw/` route with its `finance.*` and entity tags, and simply has no deal record. It is **not** counted in any hub aggregate. This holds for **fact 4** too: an item of unknown vintage takes the `raw/` route with the event date **recorded as unestablished** (`CLAUDE.md` → *Currency*), and the date is a candidate for a reconcile provenance hunt. Nothing is parked (`INGEST.md`). Record which fact failed, in one line.

## Core fields the driver supplies

The driver maps its source into these fields (blank where genuinely unknown): **financier**; **recipient** (+ ISO-3 place); beneficiary type; **title**; **description**; **instrument**; status; commitment USD; original amount + currency; co-financing (amount + names); lead-financier flag; **commitment / start / end year**; disbursed USD; amount quality; **subject category**; digital-ID and digital-payments flags; native project ID; IATI ID; **source URL**; source type; access date; notes. Bold fields are the ones a record is built around.

**A driver may add origin-specific fields** as extra `## Deal record` rows without amending this list (`wiki/finance-load-domestic-state.md` is the worked example). Only fields the compile and lint passes **filter on** go into frontmatter; everything else stays in the body table.

**Admission is decided by the five-fact test, not by this list.** `title`, `description` and `instrument` are recorded whenever the source states them and are **not** gates. Beyond the five facts, supply every field the source gives and leave the rest blank. The **subject category** resolves to one `taxonomy.md` slug either way it arrives (*Subject tag*).

## Provenance gate

Admissible only if the item's source is **primary** (`CLAUDE.md` → *The material*). A second-hand synthesis is a **lead, not a source**: flag it, don't build a record.

## Subject tag

1. **Primary slug.** From a WB-DT label, take the crosswalk's `mapped_slug` (`archived-procs/non-state-finance-crosswalk.csv` — load-only); where it gives no slug, infer from `title` + `description`; a `review` row that carries a slug uses it. From an unclassified item, classify from content directly. Log the justifying phrase whenever the slug is inferred. **Where the purpose is stated but the slug is uncertain, build the record and flag it for classification. Where no purpose is stated at all, the item fails fact 5 and no record is built. Never substitute a default slug in either case.** **Scope is checked here too**: a source whose subject falls outside data governance and digital transformation is rejected and deleted, not filed as a lead (`CLAUDE.md` → *The material*). A dataset's scope is not the wiki's.
2. **Always add a finance tag:** `finance.new` for an investment/commitment, `finance.mou` for an MoU, framework agreement or letter of intent, `finance.budget` for a domestic budget appropriation or expenditure line.
3. **Flag-derived:** `dpi.id` if the digital-ID flag is set, `dpi.pay` if the digital-payments flag is set.
4. Valid `taxonomy.md` slugs only; dedupe; usually 2–3 slugs.
5. **`primary_subject:` is required, and must be one of the record's own `topics:`.** It names the subject the record is filed under; a compiled page never infers it from list order. `topics:` is still never sorted. Where the dominant subject is arguable, the record decides, once and visibly.

## Places

Tag the recipient's place (ISO-3, or a `X__` region) from `countries.csv`. Add the parent region only when the item is explicitly regional. Reject values outside the vocabulary.

## Entities

Tag two actors — the **financier** and the **recipient** — and a third, the **vendor/contractor**, where a driver supplies one and the source names it.

**The resolved slugs are recorded as typed frontmatter fields — `financier_slug` and `recipient_slug` — not left implicit in the positional `entities:` list.** `financier_slug` is **mandatory**. `recipient_slug` is mandatory **whenever the source names a recipient** and blank otherwise, with `recipient unspecified` in `## Notes`. Both take **entity-vocabulary values only** — the exact canonical slug the wiki already uses (`world-bank`, never a fresh `world-bank-group`) — and must also appear in `entities:`; the descriptive `Financier` / `Recipient` strings in the body table are carried **alongside** them, never in their place. The typed fields are what the Financing compile groups on and what lint checks.

- **Financier** — resolve to the slug the wiki already uses, by checking `raw/`'s `entities:` tags (there are no entity pages to check against). Where no slug exists yet, mint one consistent new slug and use it thereafter — never slug ad hoc, never a second variant for a financier already tagged elsewhere. The initial load's financier crosswalk in `archived-procs/` is finished and not consulted.
- **Recipient** — best-effort canonical kebab-case (strip descriptive suffixes; prefer an obvious short stem). Residual drift here is cheap — lint #16 surfaces it soft, fix by hand when noticed. **Where the recipient is blank in the source, emit the financier only** and record `recipient unspecified` in `## Notes` — never substitute the country, the place tag or any other stand-in.

**Slugging traps:** cut a descriptive suffix only at an **em/en dash** or a **spaced hyphen**, never at an internal hyphen (else *Export-Import Bank of China* → `export`); fold accents before stripping (else *Côte d'Ivoire* → `c-te-d`). Co-financiers and officeholders stay in the verbatim body, not as tags.

## Dates

Anchor on the **commitment/approval event**, not a publication date:

- `published` = commitment year, else start year, padded to `YYYY-01-01`; `date_precision: year`, `date_source: source`.
- **Where the driver has a dated event or a known period boundary, use it at its true precision** rather than padding: an appropriation act's assent date at `day`, a fiscal-year start at `month`. Padding is for a bare year only, never for a date actually known. `date_precision` states which case applies.
- **If neither year exists, do not build a record.** The item takes the ordinary `raw/` route (source, no deal record) with its event date recorded as unestablished — a candidate for a reconcile provenance hunt. **Never fall back to the access date with `date_source: proxy`** — a finance record with no event year is not a dated fact (`scripts/lint-deterministic.py` check #1 fails any finance record carrying `date_source: proxy`; lint #21 class 1).
- The filename date prefix equals `published`, so `new/` sorts by commitment year.
- Record the specific years in the body table regardless — they carry the currency discipline onto the page.

## Enrichment — light touch

Explore the primary **once**, to **fill blanks and pull one or two highlights**, never to re-audit. **Fill only blank fields; never overwrite a supplied value** (a contradiction is a one-line note in `## Notes`; for a batch, a file in `reviews/contradictions/open/`). Mark each filled field `(enriched from source, <date>)`.

**One exception — dates: use the more accurate date.** Where enrichment yields a **verified event date** from the primary — a board-approval date, an IATI transaction date — and its **year agrees with the source's commitment/start year**, promote it into `published` and set `date_precision: day`. **If the years disagree, do not promote** — keep the source year and record the divergence in `## Notes` (a systematic pattern of disagreement is a contradiction). Capture at most a sentence or two of verbatim highlight. Set `body_completeness`: `full` if the primary's substantive text was captured, `excerpt` for a portion, omit if not fetched.

**Routes** (require network + the IATI key — run from Claude Code, not a restricted sandbox; prefer the structured route over scraping a JS portal):

- **World Bank** (`project_id` like `P180693`): `https://search.worldbank.org/api/v2/projects?format=json&id=<project_id>` (approval and closing dates, borrower, implementing agency, status, themes, sectors). Documents: `https://projects.worldbank.org/en/projects-operations/document-detail/<project_id>`.
- **IATI activity** (`iati_project_id` present): the **Datastore API** with the key — `…/datastore/activity/select?q=iati_identifier:%22<id>%22&fl=iati_json&wt=json&rows=2`, header `Ocp-Apim-Subscription-Key: <IATI_API_KEY>` (parsing per `wiki/finance-iati-driver.md`) — **or**, keyless, **d-portal**: `https://d-portal.iatistandard.org/q.xml?aid=<iati_project_id>` (plain HTTP XML; fetch directly, not via Exa).
- **DFI / foundation / press pages:** fetch the HTML (Exa `web_fetch_exa`, per `prefer-exa-search`, or a plain GET).

One attempt per route; on failure log `enrich: failed <reason>` and proceed with the item as-is.

## Output template

Filename: `{YYYY-MM-DD}-{id}-{short-title-slug}.md` in `new/`, where the date is the padded commitment date and `id` is the driver's stable record key (the CSV's `deal_id`, or for a news item a slug of financier+recipient+year). Example: `2024-01-01-wb-ago-001-angola-digital-acceleration.md`.

```markdown
---
type: source
title: <title>
url: <source_url — first URL only if several>
publisher: <financier>
published: <YYYY-01-01 from commitment|start year; or a known event date / period
                             boundary at its true precision — see Dates>
date_precision: year        # day | month | year — a record always has an event date
date_source: source         # source (no proxy dating — see Dates)
places: [<recip ISO-3>]
topics: [<crosswalk/derived slug>, finance.new, <dpi.id/dpi.pay if flagged>]
primary_subject: <the subject this record is filed under — mandatory; must appear in topics>
entities: [[<financier-slug>], [<recipient-slug>]]
financier_slug: <canonical entity-set slug — mandatory; must also appear in entities>
recipient_slug: <canonical entity-set slug — omit if recipient unspecified; must also appear in entities>
deal_id: <record key>
finance_origin: non-state   # non-state | domestic-state — set by the driver; drives the hub Financing split
ingested: <today>
retrieved: <access date, YYYY-MM-DD>
body_completeness: full     # full | excerpt | (omit if not fetched)
catalogue_hero: <=120 chars — money, instrument, recipient, date; see below>
---

# <title>

<one-sentence plain summary: who funded whom, for what, how much>

## Deal record
<!-- domestic-state budget-line records title this section `## Budget line record`
     (a budget line is not a deal) and carry the budget fields instead — see
     wiki/finance-load-domestic-state.md. The shape is the same. -->

| Field | Value |
|---|---|
| Deal ID | … |
| Financier | … |
| Recipient | <recipient> (<ISO-3>) |
| Beneficiary type | *a `beneficiary_type` value from `lookups/deal-vocabs.csv`* |
| Instrument | *an `instrument` value from `lookups/deal-vocabs.csv`* |
| Status | *a `status` value from `lookups/deal-vocabs.csv`* |
| Commitment (USD) | … |
| Original amount | … |
| Co-financing (USD) | … |
| Co-financiers | … |
| Lead financier | … |
| Commitment year | … |
| Start year | … |
| End year | … |
| Disbursed (USD) | … |
| Amount quality | … |
| WB DT category | <source label> → <slug> |
| Digital ID flag | … |
| Digital payments flag | … |
| Capital origin | <if set> |
| Project ID | … |
| IATI activity ID | … |

## Description

<description verbatim; plus any short enrichment highlight, marked as enriched>

## Source

<source_url> — <source_type>, accessed <access date>

## Development history

<empty at build. Each **definite**-match news item appends one dated, attributed
line — only its genuine added detail, never its body:
`- **2026-03-11** — first disbursement US$Y; phase-2 fibre contract signed. [<url>]`>

## Notes

<notes verbatim; then processing notes: inferred-slug justification, enrichment
result, any drift or contradiction flag>
```

**`catalogue_hero` on a finance record is composed from the record, not written fresh.** The catalogue subtitle (`schemas.md` §4) is owed by every source, and a deal record's is the one case where it assembles mechanically: **amount in the announcing currency, instrument, recipient, date**, in that order, cut to 120 characters — *USD 45m concessional loan to Kenya Power, signed 2026-03-11*. Drop the tail rather than the money, and where the record's title already carries the amount, lead on the instrument and the stage instead — the hero complements the title, it never restates it.

Render only body-table rows that have a value. Frontmatter keeps `deal_id` (the dedup/traceability key), `financier_slug` / `recipient_slug` (the Financing-compile grouping keys) and whichever driver-supplied fields the compile and lint passes filter on.

**Beneficiary type, Instrument and Status take a controlled value** (`DEAL-VOCAB.md`) — spelled exactly as `lookups/deal-vocabs.csv` spells it, never a sentence, never blank (`Unknown` where the source does not state it); extra wording goes in `## Notes`. They are the only normalised cells in the table. Held by lint #28.

**`amount_quality`.** The body table carries *Amount quality* (`Exact`, `Rounded`, `Estimated`, `Imputed`, `reported`). Where the amount is **constructed rather than published** — a straight-line increment between two anchored milestones, written so the series sums to a source-stated cumulative — record **`amount_quality: interpolated` in frontmatter**, not only in the table: `build-finance-page.py` exports it and `compile-hub-financing.py` states it in the aggregate sentence; a body-table value reaches nothing. `Estimated` is not the value for this case — an interpolation asserts a number no source states. Interpolated records are kept, flagged as derived, with their totals.

**`amount_basis` — a derived export column, not a field anyone writes.** It records *which money cell the exported figure came from*; never put it in frontmatter or the body table. `deal_usd()` in `scripts/build-finance-page.py` applies **always use commitment; where no commitment exists, use disbursed and note it**. Three values, no others: **`commitment`** (from *Commitment (USD)*), **`disbursed`** (no commitment stated; from *Disbursed (USD)*), **empty** (neither cell parseable; `commitment_usd_m` blank too). It sits in every `outputs/non-state-finance/*.csv` beside `commitment_usd_m`, ahead of `amount_quality`; `compile-hub-financing.py` counts the `disbursed` rows so a hub's `## Financing` aggregate states the composition of its total. Basis says *which number*; quality says *how it was arrived at*.

**Section heading by origin.** A non-state deal titles the section `## Deal record`; a **domestic-state budget-line record titles it `## Budget line record`** and accretes a `## Stage history` in place of `## Development history` (`wiki/finance-load-domestic-state.md` → *Baseline, stage history and the missing appropriation*). Same shape, origin-appropriate labels.

**A recorded `0` is permitted where the source states nil** — and only there. A stated nil is a fact (voted, released nothing): mark it `0` with the source's own wording in `## Notes`; leave genuinely unknown blank.

## Store of record, merging and compilation

**These records are the living store of record, in `raw/`.** A finance deal record **accretes** — it is the durable object for its deal, and later reporting is folded into it rather than spawning a fresh page per event. This is a deliberate, scoped **exception to `raw/` immutability**.

**Compilation is aggregate, never per-deal bullets.** Each place hub carries a compiled **Financing section** — total committed, deal count, date range, instrument mix, top financiers, subject breakdown — computed from its deal records. An individual deal surfaces there only when it clears the deal-entity bar (`schemas.md` §5); one-bullet-per-deal breaks the `operations.md` §8 hygiene thresholds.

**One shared Financing space, split by origin.** Non-state and domestic-state records compile into the *same* hub Financing section, with the rollup carrying the origin cut; the builder here is origin-neutral — only the driver differs.

**Merging later reporting into a record — definite only.**

- **Definite match → merge.** Definite = a shared unique key (`project_id` or `iati_project_id`) or unambiguously the same deal (same financier, recipient and native project identity). Fold in **only the genuine added value** — a new figure, disbursement, milestone, named party, status change — as one dated, attributed line in `## Development history`, and update the current-state fields (status, disbursed). Never copy the whole body. A disagreement is a contradiction (`reviews/contradictions/`), not a silent overwrite. Reporting that adds nothing material is dropped with a one-line note.
- **Fuzzy match → reference, never merge.** Anything resting on approximate amount/date/name similarity stays its own source with a `possibly the same deal as [[…]]` cross-link, and is **not counted in the aggregate** as a distinct deal. If it later proves distinct it becomes its own record.

The same rule governs overlaps between a load and finance the wiki already holds: shared identity merges/replaces per `CLAUDE.md` → *Duplicates*; a resemblance is cross-referenced.

**Ingest is match-or-create, not the news bullet path.** Definite-match a held record → merge; no match but clearly a new deal → create; not deal-specific (a trend or multi-deal piece) → a normal source with `finance.*` tags. `INGEST.md` step 2a must not drain these into the per-event bullet path.

## Verification (per record)

1. Every supplied field is represented; every blank is genuinely blank (no `0`, no fabrication).
2. Topics are valid `taxonomy.md` slugs, the primary came from the crosswalk (or was inferred-and-logged), and a `finance.*` tag is present.
3. Places are valid `countries.csv` codes.
4. `published` and the filename prefix agree; `date_source`/`date_precision` are honest.
5. No source value was normalised except where a driver mandates it.
6. Enrichment stayed light — blanks filled, nothing supplied overwritten, each filled field marked, each failed fetch logged.
7. The source is primary; a second-hand source was flagged as a lead.
8. `financier_slug` is a canonical entity-set slug; `recipient_slug` is present whenever a recipient is named (blank only with `recipient unspecified` noted); both appear in `entities:`; neither is a second variant of a slug already in use.
