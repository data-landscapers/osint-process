<!-- reader: cc; type: spec -->
# finance-donor-reporting.md — the method donor-reporting datasets share

IATI and the OECD CRS are the same kind of data: the donors' own reporting, structured, with amounts and dates attached. **They run one method with two drivers, so that a change to selection, classification or the drop rules is made once, here** *(Bill, 2026-11-05; notes-for-osint 291)*.

| Dataset | Run by | Driver | Arrives as |
|---|---|---|---|
| IATI Datastore | `SWEEP-IATI.md`, over each poll's id diff | `wiki/finance-iati-driver.md` | records in `new/` |
| OECD CRS | the yearly CRS harvest, each January, in RESEARCH | `wiki/finance-crs-driver.md` | `X:\new-queue\dataset-crs-{YYYY}\`, backfill lane |

The record shape is `wiki/finance-record-spec.md`. **This file says what is kept and how it is classified; a driver says where each field is found in its dataset, and holds the screens only its dataset needs.**

---

## Scope is never in the query, and DAC is provenance

**Never scope a pull, or classify a record, by the DAC purpose code.** Digital work lands in unrelated DAC codes and hides under generic public-sector, ICT and statistics codes, and the ICT and media codes also catch out-of-scope legacy telecoms and broadcasting. The codes predate the digital era. **Scope is decided on content, over the set the dataset hands in.** A DAC code, or a dataset's own marker such as the CRS `DIG` flag, is recorded as provenance and never decides a keep.

## Selection — in stages, cheapest first

1. **Geography, mechanically.** Keep a deal whose recipient country resolves to a `countries.csv` ISO-3, or whose recipient is one of the seven African DAC regional codes in *Recipient and region*. `998` Developing countries, unspecified is **not** African and is not kept. **Report every region code seen, not only the ones kept**: an unmapped code is a line to extend the mapping from, not a deal that vanished. The driver says how its dataset spells a region and what must happen before this screen (IATI resolves a child's parent first).
2. **Vintage, mechanically — the 2015 floor** (*Two drop rules*).
3. **A keyword pre-screen, where the volume calls for one.** `lookups/donor-keywords.csv` holds one regex per `taxonomy.md` topic and language (English and French), built for recall. A deal whose title or description matches no row is not read. **It is a net, never a classifier**: a hit does not choose the slug, and its false hits are the reading's to drop. Its `general` rows (a bare *digital* or *data*) are not a slug; a deal hitting only them still goes to the reading. The CRS uses it, because a CRS year is about 76,000 commitment rows; IATI's nightly diff does not need it.
4. **Topic, by reading.** Over the survivors only, read title and description against `taxonomy.md` and keep what is a digital-transformation subject. This is judgement over prose and is not mechanised. **Record the phrase that justified each keep.**

## Two drop rules — no money, and no recent vintage

**Both are drops, not routings, and both hold for every donor-reporting dataset.**

**1. No monetary value, no record — and nothing staged.** A deal that carries no value is dropped and never reaches `new/`. **This is a deliberate, scoped departure from `finance-record-spec.md` → *Failing the test is a routing decision, not a rejection*.** An amount-less dataset row is a database row, not a piece of reporting. The general rule stands everywhere else; a prose source reporting a financing development without a figure is still a source.

**2. Committed before 2015, dropped.** The test is the deal's **commitment year**, and where it publishes none, its start year, as `finance-record-spec.md` fact 4 says *(Bill, 2026-11-05; notes-for-osint 292)*. A deal that started before 2015 but was committed in or after it is kept. The driver names the fields.

**The floor is 2015 and it is a constant, not a rolling window.** It matches the range `lookups/fx-imf-annual.csv` carries rates for, so a kept deal is a convertible one. Moving the floor means extending that table first.

**Both are logged, never silent.** A run's closing tally carries `dropped-no-amount=N` and `dropped-pre-2015=N` as their own counts, not folded into a general dropped figure.

## Recipient and region

- **One recipient country** → its ISO-3 from `countries.csv`.
- **More than one** → **the narrowest `countries.csv` region containing every country named**, walking the parent column. The amount is **recorded whole on that one record**, never split by a published percentage, which would publish a figure no source states.
- **No country, a region instead** → the region code, mapped below.

| DAC region code | Place |
|---|---|
| 189 North of Sahara, regional | `XNA` |
| 289 South of Sahara, regional | `XSS` |
| 298 Africa, regional | `XAF` |
| 1027 Eastern Africa, regional | `XEA` |
| 1028 Middle Africa, regional | `XCA` |
| 1029 Southern Africa, regional | `XSA` |
| 1030 Western Africa, regional | `XWA` |

**All seven African DAC regional codes, mapping one-to-one onto the seven African rows of `countries.csv`.** 1028 *Middle Africa* is the UN M49 name for what the wiki calls Central Africa. A dataset's own regional grouping of a country is not the wiki's: the place comes from `countries.csv`, whatever region the dataset files it under.

**`XSS` is a sibling of `XEA`, `XWA`, `XCA`, `XSA` in `countries.csv`, not their parent.** So a multi-country deal spanning two sub-regions aggregates to `XAF`, and `XSS` arrives only from code 289 directly.

## Subject — classified from content, one slug

1. Read title, description **and any sector narrative the dataset carries**. A publisher-supplied label is often more specific than the DAC label, so weight the specific ones and never rely on the DAC code's generic label.
2. Assign the **single** closest Level-2 `taxonomy.md` slug: national ID / CRVS → `dpi.id`; instant and retail payments → `dpi.pay`; population, land and address registries → `dpi.registry`; interoperability → `dpi.exchange`; broadband and fibre → `infra.connect`; data centres and cloud → `infra.store`; data-protection law → `gov.protect`; strategy and policy → `gov.policy`.
3. Record the **slug**, then any DAC code in brackets as provenance: `dpi.pay (DAC 24040)`, or `(no DAC code)`.
4. Genuinely not a digital subject, or nothing fits: `unmapped` plus a reason, flagged for a ruling. Never force a slug.

**Record the phrase that justified the slug** in the QA line.

## Cross-reference, not enrichment

Where the wiki already holds the deal — same dataset key, or unambiguously the same deal — **say so on the record and let ingest settle it** (`CLAUDE.md` → *Duplicates*).

**One deal, two sightings — and the CRS is usually the second.** Many donors report the same activity to both IATI and the CRS, and **the CRS arrives more than a year after the commitment**: a year's file is released the following December or January. So much of any CRS batch is already held, from IATI's nightly poll or from the news that reported it. **Treat every CRS deal as a probable duplicate until the check says otherwise**, and under `CLAUDE.md` → *Currency* a late arrival is a baseline, never news that outranks the held state. **The match is the CRS `ProjectNumber` against IATI's `other-identifier` and `iati-identifier`**, where these agree, and the same financier and recipient. Where the identifiers are absent or disagree, the same financier, recipient and commitment year with a matching title or amount is a probable match: the record names the held one it may duplicate, and ingest decides. A match is cross-referenced as one deal, never staged as a second; which sighting is held is ingest's ordinary *Replace* / *Keep both* call.

**Do not fill a missing fact from the wiki.** `finance-record-spec.md`'s test requires each of the five to be present *in the source itself*, "not inferred, not carried in from the wiki". A deal that needs the wiki to complete it has failed the test.

## QA line — one per deal

Deal key, the record written or `SKIPPED`, and every blank with its reason: missing field, missing FX rate, no English narrative, unmapped region code, unmapped subject, and anything inherited or netted. That log is what makes a batch auditable, and it is where a pattern shows up.

## The run's manifest

Every run writes one, and carries at least: rows or ids handed in, kept on geography, kept on the pre-screen where one ran, kept on topic, **dropped pre-2015 and dropped for no amount as their own counts**, records built, one line per skipped class, **the distinct region codes seen, with counts**, and **the commitment/disbursement split by financier**. A driver adds its own dataset's counts.

**Watch the split.** Large donors report commitments; a big financier arriving disbursed-only, repeatedly, is more likely a defect in the extraction than in their reporting.
