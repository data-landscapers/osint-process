<!-- reader: cc; type: runbook -->
# SWEEP-IATI.md — the donor-finance sweep

Trigger: **"run the IATI poll"**, or its day of the rotation (`logs/sweep-cycle_log.md`).

Every other sweep watches *publications*, so it sees a donor commitment only if somebody wrote about it. The IATI Datastore is the donors' own reporting, in a structured schema with amounts and dates attached — the one instrument the wiki has for **the commitment nobody reported**.

**Method: `sweep/donor/iati/iati-guidance.md`** (from IATI's own side); the record shape is **`wiki/finance-record-spec.md`** through the driver **`wiki/finance-iati-driver.md`**.

---

## Scope is never in the query

**Never scope the query by DAC sector code.** DAC is provenance, not the classifier (`wiki/finance-iati-driver.md`): digital work lands in unrelated DAC codes and hides under generic public-sector, ICT and statistics codes. **Scope is decided on content, over the diff — never in the query.**

## What the run does

**Pull ids for everything. Parse only the diff.** The full sweep is a field-limited id pull; every expensive step runs over the ids that are actually new.

1. **The master list is `sweep/donor/iati/last-poll-ids.txt`** — every activity id a poll has seen. It is the sweep's memory and the only state it keeps. It records what a poll *has seen*, not what exists; never size a night's work from `numFound` — the manifest measures the diff each time.
2. **Pull today's full id list.** `q=*:*`, `fl=iati_identifier,iati_activities_document_id`, `rows=1000`, paged. `iati_activities_document_id`, taken in the same call, traces each activity to its source dataset and URL.
3. **Diff.** Today's list minus the master list. Everything downstream runs on this set alone.
4. **Fetch the diff's metadata**: `recipient_country_code`, `recipient_region_code`, `recipient_region_vocabulary`, `title_narrative`, `description_narrative`, plus `activity_date_iso_date` and `activity_date_type`. Batched by id, ~1 request per 1,000 new ids; the flat Solr fields are safe for selection.
5. **Select, in stages, cheapest first.**
   - **Geography, mechanically — after parent inheritance** (§ *Hierarchy*). Keep an activity whose `recipient_country_code` resolves to a `countries.csv` ISO-3, **or** whose `recipient_region_code` is one of the [codelist's](https://iatistandard.org/en/iati-standard/203/codelists/region/) seven African regions — **189** North of Sahara, **289** South of Sahara, **298** Africa, **1027** Eastern, **1028** Middle, **1029** Southern, **1030** Western — which map one-to-one onto the seven African rows of `countries.csv`. `998` Developing countries, unspecified is **not** African and is not kept.
   - **Report every region code seen, not only the ones kept.** `recipient-region/@vocabulary` defaults to `1` (OECD DAC); a publisher using `2` (UN M49) writes Africa as `002`. The manifest carries **the distinct (vocabulary, code) pairs with counts across the whole diff**; an unmapped pair is a line to extend the mapping from, not an activity that vanished.
   - **Vintage, mechanically — drop anything that started before 2015** (§ *Two drop rules*), on the fields pulled in step 4, before the per-record pull.
   - **Topic, by reading.** Over the survivors only, read title and description against `taxonomy.md` and keep what is a digital-transformation subject. This is judgement over prose and is not mechanised. Record the phrase that justified each keep.
6. **Pull the full record for the selected ids only** — `fl=iati_json&wt=json`, one request each — and build a finance record per `wiki/finance-iati-driver.md`, into `new/`. Structured JSON, never the flattened default: parse 2 must pair transaction values with their types and sectors with their percentages. **An activity whose transactions carry no value is dropped here and never staged** (§ *Two drop rules*).
7. **Cross-reference what the wiki already holds.** Where the activity is already on file — by `iati_project_id`, or unambiguously the same deal — the record says so and ingest's ordinary duplicate handling settles it (`CLAUDE.md` → *Duplicates*).

Then **advance the master list to today's full id list** — last, and over everything pulled, not only what was staged. An activity skipped for want of an amount has still been seen.

**`work-order-YYYY-MM-DD.json` is therefore a queue, in exactly the way `new/` is.** An activity kept on geography but never turned into a record will not reappear in any future diff, and the work order is the only thing holding that set: it is not deleted until its records are built, and a run that ends with one outstanding says so on its closing line. The file's presence is its state.

## Boundaries

- **Output is candidate records in `new/` and state in `sweep/donor/iati/`.** Nothing reaches `raw/` except through ingest — the containment boundary, `intake.md` §7.
- **The driver applies the mechanical half of the five-fact test only** — a recipient that resolves, an amount, a date. Whether the amount is a *commitment* in the spec's sense, whether the reporting organisation resolves to a canonical financier slug, and admission itself are ingest's.
- **Origin screen** (`wiki/origin-screen.md`) on every candidate. IATI is a primary publisher and will nearly always read `KNOWN`; the gate is not conditional on expecting to pass it.

## Hierarchy — the child is the record, the parent is context

**Never build a record from a parent, and never sum children onto one.** **Each child is its own record.** A parent is read only to supply fields the child does not publish.

Donors split the fields differently, and in opposite directions:

| | `GB-GOV-3` (FCDO International Programmes) | `SE-0` (Sida) |
|---|---|---|
| Parent (hierarchy 1) carries | `sector_code`, `default_aid_type_code`, title | `recipient_country_code`, `sector_code`, title |
| Parent lacks | transactions, recipient country | transactions |
| Child (hierarchy 2) carries | transactions, `recipient_country_code`, title, description | transactions, `default_aid_type_code`, `default_finance_type_code`, `policy_marker_code`, title |
| Child lacks | `sector_code`, aid type | **`recipient_country_code`**, `sector_code` |

A child that publishes no recipient country fails the geography screen while its parent, which carries the country, fails drop rule 1 for having no money — so the screens run in this order:

1. **Resolve the parent before screening.** A candidate with `related_activity_type` `1` names its parent in the matching `related_activity_ref`. One extra lookup per child, bounded by the diff.
2. **Inherit only what the child is silent on.** `recipient_country_code` / `recipient_region_code`, `sector_code`, `default_aid_type_code`, `default_finance_type_code`, and `description_narrative`. **Never overwrite a value the child publishes** — the child is the reporting unit and its own value always wins.
3. **Screen geography after inheritance, not before.**
4. **Drop rule 1 still applies to the child's own transactions.** A child with no value is dropped like any other activity. A parent is never staged, whatever it carries.
5. **Record that inheritance happened** — the record's QA line names each inherited field and the parent id it came from. An inherited recipient country is not the child's own claim.

**Do not generalise the field list to other donors without looking.** A third publisher may split the fields differently again, and inheriting a field a donor deliberately left blank would manufacture a fact.

## Two drop rules — no money, and no recent vintage

**Both are drops, not routings, and both are this sweep's alone.**

**1. No monetary value, no record — and nothing staged.** An activity whose transactions carry no value is dropped at step 6 and never reaches `new/`. **This is a deliberate, scoped departure from `finance-record-spec.md` → *Failing the test is a routing decision, not a rejection*.** An amount-less IATI activity is a database row, not a piece of reporting. **The general rule stands everywhere else; this sweep overrides it for itself and says so.**

**2. Started before 2015, dropped.** The test is the activity's **start date** — planned or actual, whichever it publishes — and where it publishes none, its commitment date.

**The floor is 2015 and it is a constant, not a rolling window** — it matches the range `lookups/fx-imf-annual.csv` carries rates for, so a kept activity is a convertible one. Moving the floor means extending that table first.

**Both rules are drops, so both are logged, never silent.** The closing tally carries `dropped-no-amount=N` and `dropped-pre-2015=N` as their own counts, not folded into a general dropped figure.

## Updated activities are out of scope

IATI carries no per-version marker. Detecting a changed activity means hashing every activity in any dataset whose `iati_activities_document_hash` moved, or holding the whole corpus on disk — **that is parsing the datastore, and this sweep only parses the diff.** A material change to an activity the wiki already holds surfaces through a source that reports it.

## Running it

```
python scripts/iati-poll.py --dry-run     # poll, report, write nothing
python scripts/iati-poll.py               # select, build records, advance the master list
python scripts/iati-poll.py --baseline    # rebuild the master list, select nothing
python scripts/iati-poll.py --limit 40    # cap a night's record-building
```

`IATI_API_KEY` comes from `.env`, sent as `Ocp-Apim-Subscription-Key`. Two failure modes: the gateway **403s a default `python-urllib` User-Agent** and wants a browser string, and it **429s** readily — back off on `Retry-After` and give up loudly rather than silently short-polling.

**A poll that cannot reach the API returns `stopped=error`, never `staged=0 stopped=complete`** (`SWEEP-CYCLE.md`). A nil is reportable only when the instrument demonstrably ran.

## State, and what is versioned

`last-poll-ids.txt` is rewritten every poll and **is not versioned**; `build-last-poll-ids.py` reconstructs it from the API, and the working copy is mirrored twice daily (`SWEEP-CYCLE.md` → *Mirror*). Losing it costs one rebuild, not a gap in the record.

## Close

Write `sweep/donor/iati/manifest-YYYY-MM-DD.md` — ids pulled, diff size, kept on geography, kept on topic, **dropped pre-2015 and dropped for no amount as their own counts** (§ *Two drop rules*), records built, one line per skipped class, **the distinct region (vocabulary, code) pairs seen**, and **the commitment/disbursement split by financier** — then report the standing sweep line:

`step=SWEEP-IATI stopped=complete staged=N dropped=N needs-clip=0 remaining=0 notes=<≤10 words>`
