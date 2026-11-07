<!-- reader: cc; type: spec -->
# finance-iati-driver.md — IATI activity → finance record

The driver `wiki/finance-record-spec.md` calls for an IATI activity. `SWEEP-IATI.md` selects which activities reach it; this file says how one becomes a record. **The method it shares with the OECD CRS — region, subject, cross-reference, the QA line and the drop rules — is `wiki/finance-donor-reporting.md`**; this file holds IATI's field mapping.

**It runs over selected activities only** — the poll's step 6, never over the datastore. Input is one activity's structured JSON; output is one record in `new/`, for ordinary ingest.

---

## Request the structured representation, never the flattened default

`…/datastore/activity/select?q=iati_identifier:"<id>"&fl=iati_json&wt=json&rows=2`, with the key as `Ocp-Apim-Subscription-Key`.

The Datastore's default flat JSON returns multi-value fields as **separate parallel arrays** — `transaction_value`, `transaction_type`, `sector_code`, `sector_percentage` — whose elements cannot be paired. `iati_json` mirrors the XML tree, so each `transaction` keeps its own type, value, currency and date together.

Parse `response.docs[0].iati_json`; the activity is `iati-activity[0]`. Attributes are `@name`, element text `text()`, repeated elements arrays. Empty `docs`, or more than one activity for a single-identifier query: log and skip, never merge.

*(The poll's **selection** parse may use the flat fields, because it needs presence and text and never pairs two arrays.)*

## The five facts, from IATI

**`finance-record-spec.md` owns the test. This says where each fact is found, and nothing else.**

1. **Financier** — the longest English `reporting-org/narrative`, with `@ref`. **Unless `reporting-org/@secondary-reporter` is `1`**: a secondary reporter publishes on another party's behalf and is not the funder, so take `participating-org[@role="1"]` (Funding) instead. Where that is absent too, **fact 1 fails** — do not fall back to the reporter.
2. **Recipient** — see *Recipient and region* below.
3. **Amount** — Σ of `transaction` type `2` in USD (**commitment**). Where the activity carries none, Σ of types `3` and `4` stands as the record, with `commit_usd` **blank** and `disbursed_usd` filled — never the same figure in both. *(Fact 3 admits a disbursed-only record.)*
4. **Date** — the commitment year is the year of the **earliest type-2 transaction**; on a disbursed-only record, of the earliest type-3/4. Where no transaction carries a date, fall back to the activity start date.
5. **Purpose** — see *Subject* below. The test is mappability, not a completed classification.

**Whether the amount is a commitment *in the spec's sense*, whether the financier resolves to a canonical slug, and admission itself are ingest's.** This driver supplies the mechanical half and says so on the record's face.

**Two exceptions, where the caller drops rather than builds**: an activity with **no transaction carrying a value**, and one **committed before 2015** (commitment year, else start year) (`finance-donor-reporting.md` → *Two drop rules*). Neither takes `finance-record-spec.md`'s ordinary "routing, not rejection" path.

## Inherited fields — read the parent before the five facts

**Where the activity is a child (`hierarchy` 2), some of the five facts may be on its parent.** `SWEEP-IATI.md` → *Hierarchy* holds the rule; what it means here is that **the caller hands this driver an activity whose `recipient_country_code`, `sector_code`, `default_aid_type_code`, `default_finance_type_code` or `description_narrative` may have been inherited**, because the child published none.

- **The amount and the dates are never inherited.** They are the child's own transactions, always.
- **An inherited recipient is still the recipient** for fact 2 and for the region mapping below.
- **Say so on the record.** The QA line names each inherited field and the parent id, so nobody later reads an inherited country as the child's own claim.
- **Never inherit the financier.** `reporting-org` is on the child and is authoritative there; the `@secondary-reporter` rule is unaffected.

## Recipient and region

**The shared rule** (`finance-donor-reporting.md` → *Recipient and region*): one country → its ISO-3; several → the narrowest region, amount whole, never split by `recipient-country/@percentage`; a region instead → `recipient-region/@code` through the shared DAC table.

**Check the vocabulary before trusting the code.** `recipient-region/@vocabulary` defaults to `1` (OECD DAC), the vocabulary the shared table is in; a publisher using `2` (UN M49) writes Africa as `002` and Sub-Saharan as `202`. A region code in an unmapped vocabulary is **not** guessed at — the activity is logged as `region-unmapped` with the pair, and the poll's manifest carries the counts so the mapping can be extended from evidence.

## Narratives — title, description, financier name, sector labels

A narrative repeats once per language. **Always the longest English one:**

1. Keep narratives whose `@xml:lang` is `en`.
2. An untagged narrative counts as English **only if** the activity's own `@xml:lang` is `en`.
3. Of those, take the most characters.
4. No English narrative at all: leave blank and say so in the QA line — never substitute another language.

Collapse internal whitespace, trim.

## Dates

From `activity-date`, each with `@type` and `@iso-date`: **start** = type `2` (actual) else type `1` (planned); **end** = type `4` (actual) else type `3` (planned). `YYYY-MM-DD`, time truncated. Neither present: blank.

## Transactions and currency

Iterate `transaction[]`. Each has `transaction-type/@code`, `value/text()`, `value/@currency`, and a date — prefer `value/@value-date`, else `transaction-date/@iso-date`.

- **Commitment USD** = Σ of type `2`. **Disbursed USD** = Σ of types `3` and `4`.
- **Convert each transaction individually, then sum**, and round the sum to whole USD.
- The currency is `value/@currency`, else the activity `@default-currency`. The conversion year is **that transaction's own year**, not the activity's.
- Rates from `lookups/fx-imf-annual.csv`, the only sanctioned FX source. A missing `(currency, year)` is **not** approximated from a neighbouring year: the transaction is unconvertible, the **whole total is left blank**, and the QA line names which transaction blocked it. A partial sum silently understates the deal.
- No qualifying transactions in a group: blank, never `0`.

**Original amount and currency** carry the announcing party's own figures (`CLAUDE.md` → *Currency*). Mixed currencies: list each distinct code, so the mixing is visible.

## Subject

**The shared rule** (`finance-donor-reporting.md` → *Subject*), reading title, description **and every `sector/narrative` across all vocabularies**, with the DAC `sector/@code` as bracketed provenance.

## Fields beyond the five facts

| Record field | From the activity |
|---|---|
| co-financing names | the other `participating-org[@role="1"]` — **names only**, since IATI rarely apportions |
| lead-financier flag | true where the financier is also the `reporting-org` |
| instrument | `default-finance-type`, else `transaction/finance-type/@code` — 110 → `Grant`, 410 → `Concessional Loan` where the funding `participating-org` is IDA (`44002`), else the loan term `DEAL-VOCAB.md` settles. The cell takes the bare vocabulary term; the code goes in `## Notes` |
| status | `activity-status/@code` — 1 pipeline, 2 implementation, 3 finalisation, 4 closed, 5 cancelled, 6 suspended |
| start / end year | from *Dates* above |
| amount quality | `stated` — these are the publisher's own figures, not the wiki's arithmetic |
| IATI ID | `iati-identifier` → `iati_project_id`, the key a second sighting dedups on |
| native project ID | `other-identifier` |
| source URL | `https://d-portal.iatistandard.org/ctrack.html#view=act&aid=<iati-identifier>` — **never** the Datastore API query URL |
| source type | dataset |
| access date | the run date |

**Source URL is the public d-portal view, not the API query.** The Datastore query URL only resolves for a caller holding `IATI_API_KEY`, so a citation built from it is a dead link to every reader but this wiki. `d-portal.iatistandard.org` mirrors the same Datastore content keyless, and its `ctrack.html#view=act&aid=<id>` view takes the bare `iati-identifier` — unencoded, no surrounding quotes. Only the URL written onto the record's face is affected: the request this driver makes (§ *Request the structured representation*) and the polling calls in `iati-guidance.md` / `build-last-poll-ids.py` stay on the keyed API.

Everything the activity does not state is **left blank with a reason**, never guessed and never `0`.

## Cross-reference, QA line, manifest

**All shared** (`finance-donor-reporting.md`): cross-reference by `iati_project_id`, or a CRS sighting whose `ProjectNumber` matches `other-identifier` or `iati-identifier`, and never fill a missing fact from the wiki. The QA line also names each inherited field and its parent id.
