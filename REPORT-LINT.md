<!-- reader: cc; type: runbook -->
# REPORT-LINT.md — the verification pass over OSINT's own finance/hub compile

Trigger: **"run report lint"**. Runs as the closing step of `FINANCE-COMPILE.md`, which itself fires from ingest whenever a run admits a finance record; not at the cycle close. Read-only.

`LINT.md`'s checks stop at `raw/` and page hygiene. This pass verifies what the compile layer publishes — the finance exports and the hubs' `## Financing`/`## Recent developments` prose — against `raw/`, which is OSINT's own evidence. A compiled aggregate is reconciled against its own record set; a hub's CC-authored `## Financing` prose is compared against the export it must agree with; a display name is checked against the canonical map.

**Checks A–F live in OSINT.** The report-layer checks they fed (G–K) belong to CORPUS with the report layer itself.

**Check letters are permanent handles**, like `LINT.md`'s numbers. Never renumber, never reuse.

---

## It verifies. It does not compile.

Every failure here has a known repair, and REPORT-LINT deliberately does not run it. **A check that silently fixes what it measures can never tell you the compile is not being run.** `--fix` prints the command; a human or the calling pass issues it.

This is the one place the vault's "lint acts, it does not report" rule is inverted: `LINT.md` repairs *the vault*, where a wrong auto-fix is a revert. REPORT-LINT measures *whether a pass ran*, and repairing that in place destroys the measurement.

## Run

```
python scripts/report-lint.py                 all checks, every place with an export
python scripts/report-lint.py KEN MOZ         scope to places
python scripts/report-lint.py --check AB      a subset
python scripts/report-lint.py --fix           print the repair command per failing check
```

Exit code 1 on any failure. Checks A and C each scan `raw/`.

**The script imports the compilers rather than reimplementing them.** A checker carrying its own copy of the aggregation is checking its copy, not the compile. So a check A or B failure always means *the compile has not been run*, never a disagreement about how to compute it.

| Check | What it asserts | On failure |
|---|---|---|
| **A** | aggregate vs records — every export rebuilds identically from `raw/` | rebuild: `build-finance-page.py --all` |
| **B** | hub vs export — the hub's Financing prose is what a recompile would write | `compile-hub-financing.py --write` |
| **C** | as-of freshness — the stamp is not older than the newest record it aggregates | `compile-hub-financing.py --write` |
| **D** | display names — every `financier_slug` resolves through the approved map | **surface** — see below |
| **E** | prose vs compile — hand-written non-state text is carried by the records | hand-edit; no script owns this text |
| **F** | hub bullets vs sources — `## Recent developments` is what a recompile would write | `compile-hubs.py --write` |

---

## The checks

**A. Aggregate vs records.** Rebuilds each place's deal rows in memory from `raw/` and compares **deal identities and the USD column**, not a total. A total can agree while two rows are wrong in opposite directions, and a double-count is exactly the shape that hides inside one. Also asserts that `all-nonstate.csv` is a clean partition of the per-place exports — the same deal set, deduped by record.

**B. Hub vs export.** Runs `compile-hub-financing.py`'s own dry run. Anything it *would* rewrite is drift already published.

**C. As-of freshness.** The `**as of YYYY-MM-DD**` stamp in the section's italic header must not be older than the newest `published` among that place's finance records. **Compared against the data, never a file mtime** — mtimes do not survive a clone, and the question is whether the page has been compiled since the records moved.

**D. Display names.** Every `financier_slug` in the exports must have a row in `lookups/financier-names.csv`, and the `financier` column must equal what that map gives. `fin_name()` falls back to an entity-page title and then to a prettified slug, so an unmapped slug still renders something plausible. The fallback is the right runtime behaviour and the wrong thing to leave unaudited.

**This check fixes.** `financier-names.csv` is a `[CC]` table (`layout.md` §2 → *Who owns a lookup table*): the map is policed by lint #16 and by this check, so a missing row is a defect CC detects and closes. Add the row — canonical name as the financier publishes it, the parenthetical short form where the corpus uses one (`African Development Bank (AfDB)`) — then rebuild the exports so the display layer takes it.

**Surface only where the name is a genuine question** — a financier the wiki cannot identify confidently, or one whose canonical form is contested. A *mismatch* between the map and the export is a third thing again: that is a stale export, and check A's rebuild is the fix.

**E. Prose vs compile.** The compiler rewrites three lines of `## Financing` and leaves the rest alone by design — the domestic block, the `Material deals:` line and any caveat carry judgment a script cannot reproduce — which makes this text the one part of the section nothing else verifies. Two assertions:

- every dated `[[slug]]` in `Material deals:` is a deal in that place's export — this is how a **record retired by merge stays linked from a hub**, since the merge rewires `sources:` and no script owns the hub's prose;
- every money figure in the hand-written **non-state** text is carried by a record, compared **by value rather than by rendering** — the hub writes `US$1.39bn`, the record `US$1,390,000,000`, the export `1390`.

**Scoped to the non-state part, and deliberately so.** The `**Domestic state**` block is drawn from the *budget* export and is mostly derived analysis — subtotals, exclusion reasons, per-programme reasoning — so nearly every honest sentence in it holds a figure that sits in no single record cell, and checking figures there reads ~90% false-positive. **The gap is stated here rather than papered over with a noisy check**; closing it needs a check against `{ISO3}-budget.csv` that understands derivation, and that is a different piece of work.

**F. Hub bullets vs sources.** **Financing is not the only compiled aggregate on a hub.** `HUB-COMPILE.md` builds `## Recent developments` from the sources' `hub_line` fields, and it is fired by ingest and scoped to the places that run touched — so a source admitted by a slice that died, or by a run whose compile was scoped elsewhere, leaves a bullet written on the source and never placed on the page. It is the same assertion as B against the other compiler. It also reports a hub with no compile markers at all, which is the `--init` case.

Unlike the finance checks, F runs over **every** hub, not only the ones with a finance export: a hub with no deals still has Recent developments.

## Where it runs

- **`FINANCE-COMPILE.md`, last step** — the compile has just run, so A/B/C must read clean. A failure here means the compile did not do what it claims. `FINANCE-COMPILE.md` fires from ingest whenever a run admits a finance record, so this runs the same night a record lands.
- **Not at the cycle close** — the finance-compile step above already covers the night's ingest. Callable on demand (`run report lint`).

## Logging

One line in `logs/log.md`: the letters that ran and the failure count per letter. Check D's genuine misses are surfaced as an `[ACT]` line. Nothing else reaches Bill — a failure with a known repair is repaired by the calling pass, not reported.
