<!-- reader: cc; type: runbook -->
# HUB-COMPILE.md — compile place hubs from their sources

Trigger: **"run hub compile"**. Recomputes each place hub's **Recent developments** section from the sources `raw/` already holds. **Aggregates only — ingests nothing, researches nothing.**

The counterpart to `FINANCE-COMPILE.md`, which does the same for the **Financing** section. A hub is a derived view, not a document (`CLAUDE.md` → *Structure*): nothing is written by hand into a hub's compiled section.

Fired automatically by ingest (`INGEST.md` → *Ending the run*), scoped to the places that run touched; or run standalone for one place, or all.

---

## The contract — the bullet lives on the source

**A source page carries the hub line it earns.** Ingest authors it in Phase A (`INGEST.md` 4a), with the full text in hand; the compiler only assembles.

```yaml
hub_line: >
  **The Digital Superhighway's constraint is named as legislative, not technical.**
  ICT PS **John Tanui** met … ([[gov.legislate]], [[gov.policy]]).
hub_line_sources: [2026-07-30-other-account-of-same-event]   # optional, see below
```

- **No `hub_line` → no bullet.** That is the editorial gate, and it stays at ingest. A marginal source earns none and is still fully held in `raw/`.
- **The bullet's date is the source's `published`**, never the ingest date.
- **The bullet's places are the source's `places:`.** One source can therefore appear on several hubs — correct, and it is written once.
- **One event, several accounts:** only one source carries the `hub_line`; it names the others in `hub_line_sources:`, and the compiled bullet cites them all.

## What the compiler does

For each place in scope:

1. Gather every `raw/` source whose `places:` contains it **and** which has a `hub_line`.
2. Sort by `published`, newest first.
3. Render each as `- **YYYY-MM-DD** — <hub_line> Source: [[slug]]` (or `Sources:` with the co-sources).
4. Replace **only** the compiled block, between the markers below. Everything outside them is untouched.

```markdown
## Recent developments

<!-- compiled by HUB-COMPILE.md — do not edit between these markers -->
- **2026-07-30** — …
<!-- /compiled -->

### Not established
<!-- hand-authored. Dated absences: a known vacuum is a finding (CLAUDE.md → Currency). -->

### Before 2026-07-30
<!-- hand-authored legacy; see "The legacy block" below. Frozen, not compiled. -->
```

**Idempotent by construction.** It reads `raw/` and rewrites a delimited block, so running it twice changes nothing and running it after a failure repairs rather than duplicates.

## Two things the compiler must never eat

**Dated absences.** A known vacuum is a finding, not a source, and `CLAUDE.md` → *Currency* requires it on the page, dated. It has no source page to live on, so it lives in `### Not established`, outside the markers, hand-authored.

**The legacy block.** See below. Outside the markers, frozen.

## The legacy block

Hub bullets dated before the **2026-07-30** cut-over were written into the hub and never onto a source page, so there is nothing for a compiler to compile. **They are frozen, not migrated.**

- Everything dated **before the cut-over** stays where it is, below the compiled block, under `### Before <cut-over date>`, hand-authored and untouched by any pass.
- Everything from the cut-over on is compiled, and is therefore derivable, rebuildable and linked to its evidence.
- The block shrinks by ordinary means — page-hygiene trimming (`LINT.md` #8), and opportunistic backfill when a pass is in a hub for another reason and can see which source a bullet came from. **It is registered nowhere**: it is not a prerequisite for anything and must never block a run. The same demand-driven rule governs pre-contract sources carrying no `hub_line` (`wiki/ingest-judgment.md` §4).

## Scope and cadence

As `FINANCE-COMPILE.md`: **only the places whose sources changed.** For an ingest that is exactly the places that run touched — never every hub — so a hub with nothing new tonight gets no nightly work. A **full recompile (`--write`, no place argument)** is not a nightly operation: weekly or on demand, the same cadence as full lint.

## The script

`scripts/compile-hubs.py`, on the `compile-hub-financing.py` pattern — **dry run by default**, `--write` to apply.

```
python scripts/compile-hubs.py [ISO3 ...]           # dry run: what would change
python scripts/compile-hubs.py --write [ISO3 ...]   # apply
python scripts/compile-hubs.py --init  [ISO3 ...]   # one-time cut-over, see below
```

No arguments = every hub. It rewrites **only** the lines between the markers, leaves the rest of the file byte-identical (CRLF included), and is idempotent — a second run reports `unchanged`. A source carrying a `hub_line` but no valid `published` date gets no bullet and is **reported**, not silently dropped.

**`--init` is the cut-over and is deliberately separate.** It inserts the markers and moves the hub's existing bullets into `### Before <date>`, verbatim — interior blank lines and all. It is never automatic — it moves content that cannot be regenerated; run it per place and read the diff.

**One exception, and only this one: `operations.md` §11a's standing whitelist.** CC may run `--init` **on a hub reporting `no-markers`**, unattended, on the conditions stated there — read the diff, commit it alone naming why, revert if the diff is not what the command promised. Nothing else about `--init` is automatic, and a hub that already has markers is still off-limits.

## Concurrency and logging

One compile at a time; no other session writing `wiki/places/`.

**Write its own `logs/log.md` line**, in the one-line form of `STATUS.md` → *The `log.md` entry*: places recompiled, bullets rendered, and any place whose compiled block came out empty (no scoped source carried a `hub_line` — usually correct, occasionally a missed one). End on the standing tally line.

**Its own entry even when ingest fired it.** A compile invoked by another pass is still a pass that ran. Elapsed nests inside the caller's; it does not add to it.
