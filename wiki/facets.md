<!-- reader: cc; type: spec -->
# facets.md — facets and vocabularies — place, subject, entity types, the link-list bracket convention

Split out of `reference.md`; section numbers are kept so a `§N` reference resolves unchanged. `CLAUDE.md` holds the principles and wins where the two disagree.

---

## 1. Facets and vocabularies

Every item is classified along facets held in **frontmatter**, never in a folder matrix. Folders are organised by page *type*.

| Facet | Rank | Authority | Value form |
|---|---|---|---|
| **PLACE** | primary | `lookups/countries.csv` | ISO-3 country code, or `X__` region code |
| **SUBJECT** (`topics:`) | primary | `lookups/taxonomy.md` | Level-2 **slug** (e.g. `gov.protect`), never the label |
| **ENTITY** | secondary | tag only (`schemas.md` §5) | entity slug, lower-case kebab |

Reject values outside the vocabularies.

**`topics:` is ordered, and the order is load-bearing.** The first non-`finance.*` slug is the item's **primary subject** — the one it is filed under wherever a compiled page needs a single subject per record (the finance pages' sector column and their aggregates-by-subject tables). Write the dominant subject first. **Never sort `topics:`** — alphabetising it silently re-files the record, and a wrong order is indistinguishable from a right one on the page. `scripts/archive/restore-topic-order.py` recovers an order from git.

**`primary_subject:` names that subject explicitly, and on a finance record it is required** — one of the record's own `topics:` slugs, validated by lint #16. On other page types it stays optional, and where absent the first non-`finance.*` slug is used. The ordering rule above is not withdrawn; the field exists because a sort cannot re-file an explicit value.

### PLACE

- Countries (ISO-3) and regions (`X__`) are the **same facet**; a region is a first-class place, not a container.
- **Single-parent tree**: country → subregion → `XAF` → `XGL`. Roll up by walking parents.
- **The `XSS` rule.** `XSS` (Sub-Saharan Africa) is defined *by rule* as **all `XAF` children except `XNA`**, since no country points to it.
- **`XGL` and `XSS` are groupings, never a country's home region** — apply them to pan-SSA or genuinely global items. Both have hub pages and are compiled like any other place.
- **`XGL` is earned by the item's subject, not by the absence of an African one.** It is the place for material treating **the global south, or the field as a whole, with Africa inside its own subject** — a global-south study, a multilateral instrument, a standard or a review of the field. It is **not** a residue code for anything that is not about Africa: a single non-African country's domestic story is out on the place bar (`CLAUDE.md` → *The material*) and tagging it `XGL` does not carry it in. **The test is whether removing Africa from the world would leave the item without a subject**; if it would not, the item is somebody else's domestic story.
- **Never roll sub-regions up into `XSS`.** `XSS` *contains* `XEA`/`XWA`/`XSA`/`XCA`, so summing those into an `XSS` total double-counts every deal already tagged `XSS`. Aggregation is **by literal tag only**. The safeguard is on the tagging side: an item scoped to **one** sub-region takes that sub-region's code, and `XSS` is reserved for what is genuinely pan-SSA or spans **two or more** sub-regions.
- **Tag a region only when the item is genuinely region-level — and the test is the development, not the cast list.** A region code is earned by an act of a regional body or of an instrument it owns; by a system, standard or framework that spans **three or more** of the region's countries; or by an analysis whose subject is the region itself. `XAF` takes the continent-wide equivalent.
- **A place is the item's own subject, never the batch that reached it.** Staging files a country's batch under that country, so a regional body's act, a multilateral report or a continental facility arrives wearing whichever ISO-3 code happened to fetch it — and then renders on that country's hub as its development. Read the source, not its provenance.
- **A source naming many states is placed at first admission, because no later pass gets the chance.** The second country to meet it drops it at tier 1, correctly and irreversibly, and its own coverage inside that document goes with it. So the first admitter decides for all of them: the region code where the document's subject is the region, every state the body names where it is genuinely a per-country instrument. The first admitter's own batch is an arbitrary place for that decision to be made, which is why it has to be made deliberately.
- **What does not earn one, however many countries are tagged**: a **national implementation** of a regional programme (a country's WURI enrolment, one bank joining a regional payment rail, a lender's country financing under a regional series), a **single company's presence in several markets**, and a **bilateral**. These are national facts, correctly tagged with their countries — the regional programme they sit under is carried by its **entity tag**, and a reader looking for it greps the entity, not the place. Lint #23 surfaces the genuine cases.

Region codes in `countries.csv` (54 ISO-3 countries + 8 `X__` regions = 62 codes):

```
XAF,Africa,XGL
XCA,Central Africa,XAF
XEA,East Africa,XAF
XGL,Global/Developing Countries,
XNA,North Africa,XAF
XSA,Southern Africa,XAF
XSS,Sub-Saharan Africa,XAF
XWA,West Africa,XAF
```

### SUBJECT

`lookups/taxonomy.md` — 10 Level-1 categories, ~36 Level-2 slugs. Strict single-parent tree, but a page may carry several slugs (cross-border data is both `dpi.exchange` and `gov.regional`).

### LENS — retired *(Bill, 2026-09-08)*

There is no lens facet. `lens:` is not in the schema, no template carries it and no pass writes one — **and as of 2026-09-20 no file carries one either**: the key was cleared from `raw/` (15,372 records) and then from every other root (1,696 files) by the strategic review's tasks 20a and 20b, so the values that sat in existing frontmatter are now in git history only (`schemas.md` §4). **A carrier appearing anywhere now means something has started writing it again.** Where the sovereignty or colonialism reading is the point of an item, **write it in the body prose** — which is where the argument was always doing its work, since a two-value facet nothing filtered on classified nothing.

### Blocs are entities, not places

Because the place facet is *geographic*, political and economic blocs — AU, ECOWAS, SADC, EAC, COMESA, AfCFTA, Smart Africa — are **entities** (`entity_type: organisation` or `initiative`).

> Worked example: the **Malabo Convention** tags to the **AU entity plus the affected countries**, not to a geographic region.

### Entity types (eight values)

`company` · `organisation` · `government-body` · `initiative` · `person` · `deal` · `resource` · `instrument`

- A **resource** is a standing OSINT asset you consult repeatedly — a database, dataset, registry, tool or portal (PeeringDB, GLEIF, an open-contracting portal, a national statistics portal).
- An **instrument** is a published standard, taxonomy, framework, or policy/legal instrument that exists as a reference object in the domain (the Malabo Convention, the AU Data Policy Framework, the World Bank DT taxonomy, MOSIP specs, GDPR, a flagship national data strategy).

Neither is a dated source nor a lead.

### Finance subject vs deal entity

`finance.new` / `finance.mou` / `finance.budget` are **SUBJECT** tags meaning "this is about investment / agreements / state budget allocation".

- A *specific* transaction or MoU is recorded as a **dated fact** on the pages it touches (the parties' entity tags + `finance.mou` + places/topics). `deal` is a tagging value only: no deal, however large or multi-party, becomes its own page.
- A piece on funding *trends* carries `finance.new` with no single deal.

### Canonical link-list bracket convention

Write **one bracket layer per item** inside the outer list brackets:

```yaml
sources: [[a], [b], [c]]
entities: [[cassava-technologies], [nvidia]]
```

This is the **canonical** form. Do **not** write the double-bracket-per-item style `sources: [[[a]], [[b]]]`, and never a hybrid (`[[[a], [[b]…`): a parser reading one convention mis-reads the other. When appending to a page written in the other style, **convert the whole line to canonical** rather than matching the local style. Lint #12 checks this.

**Frontmatter `sources:` is the only source list a page carries.** A synthesis page does **not** end in a `## Sources` section restating it: two lists of one thing is how both become wrong. Frontmatter is what lint #4 and #12 read and what the website renders from, so it is the authority.

**A tool that reads citations must read this form.** In `[[a], [b], [c]]` the brackets *pair*, so a `\[\[…\]\]` regex written for body wikilinks matches **none of it**; any new reader inherits the trap.

---
