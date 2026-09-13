# Subject taxonomy — controlled vocabulary

The SUBJECT facet for the Data Landscapers wiki. Ten Level-1 categories, ~36
Level-2 topics. **Tag pages with the slug**, never the label.

## Rules

- Strict single-parent tree: each Level-2 has exactly one Level-1
- A *page* may carry several slugs. Cross-listing is done by multi-tagging, not
  by giving a topic two parents (e.g. cross-border data → `dpi.exchange` +
  `gov.regional`; cybercrime law → `infra.cybersec` + `gov.legislate`).
- Roll-up is by parent: "everything in Governance" = every page tagged with any
  `gov.*` slug.
- `finance.*` is the *subject* of investment/agreements. A specific transaction
  or MoU is a **deal entity**, not just a tag — see CLAUDE.md.

## Vocabulary

### ICT Infrastructure
- `infra.connect` — Connectivity
- `infra.store` — Data Storage
- `infra.energy` — Energy
- `infra.capacity` — Technical Capacity
- `infra.cybersec` — Cybersecurity

### DPI
- `dpi.exchange` — Data Exchange
- `dpi.id` — Digital Identity and CRVS
- `dpi.pay` — Digital Payments and Fintech
- `dpi.registry` — Registries (population, land, address, etc.). **At country level, registry material files under `--dpi-id`, not a separate `--dpi-registry` intersection** *(ruled 2026-08-10, token review task 7, housekeeping job 37)*: in practice registry and identity development has always been reported together, so no `{place}--dpi-registry` page is minted — a country's registry facts live in its `--dpi-id` page and `dpi.registry` itself stays a thematic page with `## By place` as index-plus-links, same as any other concept page's over-bar cells (`reference.md` §8).
- `dpi.mis` — Sectoral management information systems (HMIS, EMIS, etc.)
- `dpi.govtech` — Other GovTech and e-Gov

### Governance
- `gov.legislate` — Legislation and regulation
- `gov.policy` — Strategies, plans and policies
- `gov.regional` — Regional collaboration
- `gov.standards` — Standards
- `gov.protect` — Data protection
- `gov.discourse` — Public debate and participation in policymaking

**`gov.discourse` vs `gov.policy` (curator ruling, 2026-07-31).** `gov.policy` is the *formal
instrument* — an adopted or drafted strategy, plan or policy. `gov.discourse` is the *debate about
it* — named-analyst opinion, op-eds, public-participation and advocacy pieces on the quality,
framing, inclusiveness and politics of digital policymaking. A piece takes its topical slug too
(`tech.ai`, `dpi.id` …) plus `gov.discourse`; the new slug is what makes the opinion corpus
roll-up-able. Individually minor, collectively load-bearing.

### Inclusion
- `include.divides` — Digital divides
- `include.access` — Access to services

### Technology
- `tech.ai` — AI
- `tech.industry` — ICT Industry
- `tech.innovate` — Innovation ecosystem

### Geopolitics
- `geopol.usa` — US / hyperscaler activities
- `geopol.china` — China activities
- `geopol.eu` — EU activities
- `geopol.india` — India activities
- `geopol.gulf` — Gulf/UAE activities

**Scope (curator ruling, 2026-07-20).** `geopol.*` means **geopolitics** — great-power positioning,
rivalry and strategic influence — **not foreign assistance**. Bilateral aid, donor funding,
development cooperation and project financing (e.g. Japan, Korea, UK or Russia grants and MoUs) are
**not** `geopol` items: tag them by `finance.*` and the topics they fund. This list is **closed** — no
new per-country `geopol` slug is minted on the strength of aid/cooperation activity. (Settles
ISSUE-014 and ISSUE-017.)

**And a `geopol.*` slug does not by itself carry a non-African record into the base (2026-08-20,
settling note 30's open tagging question).** The facet names the acting power because the wiki
tracks that power's positioning **toward Africa and the developing world** — so where a record has
no African place, it earns the slug only if the positioning *is* the story and its bearing reaches
beyond the acting power's own borders. A `geopol` power's purely domestic act — an EU member
state's own procurement rule, a US state's own privacy report, a national regulator's guidance to
its own market — is that country's domestic story and the place bar in `CLAUDE.md` → *The
material* rejects it, however cleanly it reads as data governance. Where the act sets a standard,
precedent or supply condition others must then live with, that is positioning and it earns the
slug. **The list stays closed**: a power not on it — Korea, Japan, the UK, Russia — has no slug to
earn, so its domestic story is simply out.

### Capacity
- `capacity.literacy` — Literacy
- `capacity.training` — Training and skills
- `capacity.research` — Research institutions

### Digitalisation
- `digital.rural` — Rural digital data capture
- `digital.localgov` — Digitalisation of sub-national government

### Data
- `data.statistics` — National statistics
- `data.open` — Open data
- `data.satellite` — Use of satellite data

### Finance
- `finance.new` — New investments
- `finance.mou` — MoUs and other agreements
- `finance.budget` — Domestic budget appropriations and expenditure
