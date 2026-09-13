# Off-list sweep — procedure

Trigger: **"run the off-list sweep"**. The open-web companion to the domain-scoped daily sweep (`SWEEP-DAILY-LIST.md`). Where that one sweeps only the journals on `lookups/sweep-daily.csv`, this one sweeps **everything off that list** — the open web — on two thematic tracks, as an **acquisition sweep that files candidates**, not a read-only briefing.

Run in the sweep cycle (`SWEEP-CYCLE.md`) after the daily sweep. Like it, it **stages candidates into `new/`** and shares all its machinery — so read `SWEEP-DAILY-LIST.md`; **this file specifies only what differs.**

## What differs from the daily sweep

- **No domain firewall.** The daily sweep's admissibility firewall *is* domain-scoping every query to the curated list. This sweep is open-web, so that firewall is gone and the **admissibility screen carries the entire load** — see *The firewall* below.
- **Two thematic tracks, not a source loop.** It runs two fixed query clusters (A, B below) open-web, not a per-domain loop.
- **Deep discovery, not standard search.** The discovery instrument is the Exa **deep Agent** (`agent_run`), not the daily sweep's domain-scoped `web_search_exa`. Load `agent_run` via ToolSearch if deferred (match the tool-name suffix; the server prefix is session-specific). The Agent *finds* candidates; the daily sweep's shared **fetch → verify → classify → stage** machinery and the admissibility firewall below still vet every one. If `agent_run` is unavailable, fall back to open-web `web_search_exa` and note it. The domain-scoped sweeps stay on standard search — their hard domain-scoping is a firewall the Agent cannot enforce.
- **Mixed remit.** Track A is **Africa-focused**; Track B is **worldwide**.

Everything else is `SWEEP-DAILY-LIST.md`'s and is not restated here: the **24h high-water window**, conservative **dedup**, **fetch → verify → classify → stage** to `new/YYYY-MM-DD-slug.md`, the **full-verbatim-body standing capture rule**, the candidate **frontmatter schema**, and the **status line**.

## The two tracks

Run each track as a **deep Agent objective** (`agent_run`, `effort: "medium"` by default, `high` for a wide run): give it the track's beat and vocabulary below, the 24h window, the remit constraint (Track A Africa-scoped; Track B worldwide but Africa-bearing), and an instruction to return primaries with title, date, source and link. The clusters below are the *content* of those objectives, not literal query strings. Then take the surfaced primaries through the shared firewall and staging pipeline.

**The Agent's reported dates are not evidence.** `SWEEP-DAILY-LIST.md` step 4 — never trust a search result's date — applies to `agent_run` output too: establish every date from the fetched page. An unscreened origin is likewise not a bad origin — screen it in the run rather than dropping it as a precaution.

**Track A — Systems & infrastructure (Africa).** The physical and platform layer, wherever it is reported — not only the listed journals. Beat: `infra.*` and the systems that ride on it.

- EN: *data centre, cloud region, submarine cable, terrestrial fibre backbone, internet exchange, satellite / NGSO connectivity, spectrum, compute / AI infrastructure, or power for digital infrastructure in Africa*
- FR: *centre de données, câble sous-marin, dorsale fibre, point d'échange internet, connectivité satellitaire, spectre, infrastructure de calcul, énergie pour le numérique en Afrique*
- (AR / PT variants for North-African and Lusophone stories.)

Africa-scoped — constrain to African states / regions. Government systems on this layer (national backbone, government cloud, e-gov platforms) are in; a single ministry's IT project also belongs to the daily and domestic-finance sweeps, so stage it and let ingest dedup.

**Track B — Policy, governance & citizen feedback (worldwide).** Cast globally — the global digital-sovereignty contest directly shapes the terrain African states operate on — with each item earning its place by **bearing on Africa's digital-governance position** (`CLAUDE.md` → *Purpose*), not by being datelined in Africa. Beat: `gov.*` plus the citizen-voice side. **Run Track B as two objectives**: an Africa-datelined leg, and a worldwide leg explicitly instructed **not** to return items datelined in Africa — a single worldwide objective comes back Africa-datelined and silently loses the global layer the track exists for.

- EN (policy / governance): *data-protection or privacy law, AI governance or regulation, digital-public-infrastructure policy, digital-identity governance, platform or online-safety regulation, cross-border data rules, cybersecurity policy*
- EN (citizen feedback): *public consultation, civil-society or digital-rights response, complaints or petitions, participatory governance, or public backlash on digital policy, identity systems or surveillance*
- (FR / AR / PT variants.)

**Remit.** The bearing is often direct, not a transferable lesson: EU–US (and EU–US–China) fights over data flows, cloud, platform regulation and standards; GDPR-style model laws African data-protection regimes track; the geopolitics of who supplies Africa's DPI — core subject-matter (`CLAUDE.md` → *Purpose*), tagged `sovereignty`/`colonialism`, not a reference shelf. Carry `places: []` (or the specific state) — the value is the bearing on Africa, however the story is datelined.

**But bearing does not by itself admit.** With no African place and no `XGL`, an item files only under a `geopol.*` slug, and that list is **closed** (`lookups/taxonomy.md`; `CLAUDE.md` → *The material*): a power not on it has no slug to earn, and its own domestic instrument is out however plainly it bears. What the acting power does *to* others — a standard, precedent or supply condition they must then live with — is positioning, and that is in. The test is mechanical, not a judgement: where no admissible `topics` value exists for the item, there is nothing left to weigh.

**The sweep does not judge "bearing on Africa" from a snippet**; ingest does, reading the full body. A high ingest-side reject rate on Track B is that design's known cost, cheaper than either instrument missing a story that does bear.

## The firewall — the whole job, open-web

Domain-scoping did this for the daily sweep; here the **admissibility screen is all there is**, so run it hard (`CLAUDE.md` → *The material*, and `SWEEP-DAILY-LIST.md` step 4 — *Fetch, verify, classify*):

- **Primaries only.** Official announcements, regulations, filings, court records, company statements, datasets, on-the-record reporting, primary documents, published academic / named-analyst work. **Second-hand syntheses are leads, not sources** — mine an AI-synthesis / aggregator / listicle for the primary it cites, stage *that*, discard the synthesis.
- **Origin screen — run `wiki/origin-screen.md`** on every hit: it owns `logs/drop-list.csv`, the hostile shapes, the `watch → drop` promotion and the mining rule. This is the sweep that meets them: an un-scoped open-web query is exactly how a generated-content farm reaches the queue.
- **Digests / newsletters** are dropped outright, never lead-mined; only a publisher's standalone articles are admitted.
- **Prefer canonical over syndicated** — no aggregator carve-out here.
- An un-scoped open-web query returns content-mirrors and AI-synthesis blogs by the fistful. **Expect to discard most hits at this screen.** A low stage-count off a wide search is the screen working, not the sweep failing.

## Window, state, dedup, staging, hand-off

As `SWEEP-DAILY-LIST.md`, with these deltas:

- **State** lives in `sweep/off-list/` (`state.json`, `seen.csv`) — its own high-water mark, **24h** overlap floor, 10-day cap.
- **Dedup** also against the **daily sweep's fresh `new/` output** in the same batch: the two overlap at the edges (an infra story can sit on a listed journal *and* the open web), so cross-check `new/` before staging, not just `seen.csv` and `raw/`.
- **Stage** flat to `new/` with best-effort frontmatter and the full verbatim body; `sweep_batch: off-list-YYYY-MM-DD`.
- **Hand-off:** in the cycle this sweep is **stage-only** — it does *not* run ingest itself; `SWEEP-CYCLE.md` runs `INGEST`'s Phase A once after the daily sweeps. Run standalone (outside the cycle), finish by running `update wiki` yourself.

## End every run with the standing status line

Per `CLAUDE.md` / `STATUS.md`:

```
contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN
```

plus a one-line sweep tally: `off-list sweep: staged N · dropped N · needs-clip N · window <start>→<end> · trackA N / trackB N`.
