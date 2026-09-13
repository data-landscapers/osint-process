# FINANCE-COMPILE.md — the finance compile pass

Trigger: **"run finance compile"** (optionally scoped, `run finance compile for South Africa`). This pass **aggregates**: it reads the finance records already in `raw/` and, for each place in scope, writes **two** outputs from the one set of reads:

1. the terse **`## Financing` section on the place hub** — a §8-bound summary; and
2. the full **per-country CSV exports under `outputs/`** — deal export, domestic budget export and subject × fiscal-year summary, built by `scripts/build-finance-page.py`.

Both come from the same aggregation so they cannot drift; there is **no separate finance-page pass**. The CSVs are **OSINT's own compile, not a website feed** (`FINANCE-PAGES.md`). **It does not ingest** — it moves no files, admits nothing, makes no dedup decisions.

Admission is **ingest**'s job (`wiki/finance-record-spec.md` → *Store of record, merging and compilation*). Ingest writes **no per-deal hub bullets** — hub presence is built here, in aggregate — and **runs this pass automatically** whenever it admits a finance record (`INGEST.md` → *Ending the run*); the standalone trigger is a manual recompute.

Governing rules: `CLAUDE.md` (currency), `operations.md` §8 (hub hygiene) and the spec.

---

## Scope — recompile only what changed

Recompile **only the places whose finance records changed since the last compile**. The helper keys off git:

```
python scripts/finance-compile-scope.py          # places to recompile (changed since last compile)
python scripts/finance-compile-scope.py --all     # ALL finance places — a full rebuild (spec change,
                                                   #   from-scratch, or first run; establishes the baseline)
```

An empty list → no-op, done. Run `--all` after any change that invalidates every section (a `finance-record-spec` change, a display-rule change, a missing state ref).

## The loop

Compute the aggregation with a script and **write the result onto the page** — a compiled figure, not a query-time derivation (`CLAUDE.md` → *Working the base*). **Step 4 runs before step 2, whatever the numbering suggests**: the hub section is compiled from the export step 4 writes. For **each place in scope** (a `places` value, country or `X__` region) with finance records in `raw/`:

1. **Aggregate its deal records, split by `finance_origin`** (the section holds both **non-state** and **domestic-state**):
   - total committed (USD), deal count, commitment-year range;
   - top financiers by committed amount, **grouped on `financier_slug`, never on the descriptive `Financier` string**. Each slug is rendered once under a single canonical display name (`ifc` and `miga` stay separate — the World Bank Group is not rolled up);
   - instrument mix and top subject slugs.

   Currency discipline (`CLAUDE.md` → *Currency*): head the section **"as of `<compile date>`"**; sum the USD field only — never restate one commitment in three currencies.

   **Domestic-state aggregates differently, and these rules override the above:**

   - **Aggregate by fiscal year, in the original currency.** Never sum `amount_usd` across fiscal years. Report per-year figures in the state's own currency with a dated USD conversion beside each; trends compare original-currency figures.
   - **Read the stage ladder; do not split on `budget_stage`.** A record spans its stages (driver → *Budget stage and version*): sum each ladder field across the year's whole-scope records — Σ `appropriated_total` (voted), Σ `revised_total` (final), Σ `audited_total` else `actual_total` (outturn). No stem-pairing, no per-stage split. Capital/recurrent is Σ `baseline_capital` / Σ `baseline_recurrent`.
   - **Report execution on two bases, summing numerators and denominators — never averaging record percentages.** Headline is **credibility**: Σ outturn ÷ Σ appropriated. Beside it **absorption**: Σ outturn ÷ Σ revised (driver → *Execution is measured on two bases*).
   - **Restrict both ratios to the records holding BOTH stages, and state the coverage beside them** — "outturn published for 6 of 17 lines".
   - **Report `scope_confidence: partial` and `unclear` records apart from the headline total**, as a stated count and amount.
   - **Count the lines with no enacted baseline** (`baseline_stage` ≠ `appropriated` — the `⚠` records): the credibility ratio is undefined for them.

   Two exclusions from the headline total, set at capture, never inferred here: `is_transfer: true` lines (counted at the receiving body); a record whose `supplementary_basis` is `unclear` (its `revised_total` leaves the revised aggregate). Report each exclusion's count and amount. Externally-financed budget lines carry `finance_origin: non-state` and land in the non-state total.

2. **Write/replace the `## Financing` section** on the place hub (after `## Recent developments`), origin-split: **`python scripts/compile-hub-financing.py --write [ISO3 …]`** (no argument = all; dry-run without `--write`). It reads the `{ISO3}-nonstate.csv` step 4 writes — hence step 4 first.

   It rewrites **only** the *as of* date, the `**Non-state**` paragraph and the instrument counts, **never** the `**Domestic state**` block, the `Material deals:` line, or a hand-written caveat after the counts. **The domestic block is compiled by hand** against step 1.

   The section's shape:

   ```markdown
   ## Financing
   *Aggregate of tracked digital-transformation finance. As of 2026-07-21.*

   **Non-state** — US$X.Xbn committed across N deals (2016–2026). Top financiers:
   world-bank (US$…), gates-foundation (US$…), ifc (US$…). Mostly Grant/Equity;
   leading subjects: dpi.pay, infra.connect.

   **Domestic state** — N budget lines across FY20XX–FY20XX, national and
   sub-national. FY2025: NGN X.Xbn appropriated (US$… at NGN …/US$, FY average),
   NGN R.Rbn revised, NGN Y.Ybn outturn — **W% vs voted, V% vs revised**. Capital
   NGN …, recurrent NGN …. Leading votes: …. A further N lines (NGN …) are partial-
   or unclear-scope, and N are outturn-only (no voted baseline); both sit outside
   the credibility ratio.

   Material deals: [[…]], [[…]].
   ```

3. **List an individual deal only when it is large or multi-party.** Everything else is **not** named on the hub.

4. **Write/replace the full CSV exports** for the place — `python scripts/build-finance-page.py {ISO3}`. Not §8-bound: every non-state deal and every domestic budget line-year. Three files, each row carrying its source record:

   - **`outputs/non-state-finance/{ISO3}-nonstate.csv`** — one row per deal: year, financier, recipient, instrument, US$m, original amount, **sector** (taxonomy slug), **subject** (≤5-word deal description), status, source link.
   - **`outputs/budgets/{ISO3}-budget.csv`** — one row per **line-year at the record's own grain** (`finance-load-domestic-state.md` → *The record's grain*), the stage ladder as columns (appropriated / revised / audited) with **execution vs voted** and **vs revised**. **Never sum a programme row together with its own sub-programme rows.**
   - **`outputs/non-state-finance/{ISO3}-summary.csv`** — aggregates by subject × fiscal year: non-state rows (US$m) and domestic-state rows (US$m at the IMF annual average), primary subject per record, plus one **`origin: excluded`** row per reason a domestic line sits outside the total (`excluded_lines`, `excluded_usd_m`).

   Derived snapshots (`CLAUDE.md` → *Working the base*), rebuilt each run — never hand-edit; changes belong in the records.

   **The deal export is keyed on the financier-id.** Its 18 columns: `recipient_country` (ISO-3, the join key), `start_year` (commitment year where no start is stated), `end_year`, `financier` (**canonical name looked up from `financier_slug`**), `sector`, `instrument`, `commitment_usd_m`, `status`, `title`, `description` (full record block), `beneficiary_type`, `recipient_organisation` (name only), `original_amount`, `project_id`, `iati_activity_id`, `url`, **`financier_slug`** (the group/join key), `record`. The display name resolves via `lookups/financier-names.csv` (`financier_slug → canonical_name`), falling back to the entity-page title then a prettified slug; a new financier is added there.

   **One combined export.** `--all` also writes `outputs/non-state-finance/all-nonstate.csv` — every non-state deal, **one row per deal**, same 18 columns. Each deal is tagged to exactly one place and appears once in each file. A deal spanning several countries is reassigned to the smallest covering region (sub-region → XSS → XAF) with the countries named in its `## Description`; a single-country deal never carries its parent-region tag as well.

5. **Touch nothing else** — no `Recent developments` bullets, no other sections.

## Close

**Verify what was just published — `REPORT-LINT.md`, before the baseline moves.** `python scripts/report-lint.py`, scoped to the places compiled. Checks A/B/C must read clean before the baseline advances. Check D's misses go to `reviews/post-run-notes.md`; check E is hand work on the hub.

**Advance the compile baseline.** Once the scoped hubs are written **and committed**, run `python scripts/finance-compile-scope.py --commit` to move the state ref (`reviews/finance-compile-state.json`) to `HEAD`, and commit that — otherwise the next run recomputes the same places. Skip only on a no-op run.

**`--commit` stores only a commit reachable from `master`** (else the merge-base) and stamps `last_compile_time` beside the sha; a stale ref re-anchors by date. `no/invalid compile ref -> full scope` should never be seen; if it is, the state file has no date.

**Write its own `logs/log.md` line** (`STATUS.md` → *The `log.md` entry*): hubs written, aggregate totals. **Its own entry even when ingest fired it**; elapsed nests inside the caller's.

End with the status line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

## Notes

- **Read `finance_origin`, don't guess it.** A `raw/` finance record missing the field is a build error — fix it upstream.
- **Group financiers on `financier_slug`** (and recipients on `recipient_slug`) — the typed fields (`wiki/finance-record-spec.md` → *Entities*), never the free-text string. A blank `financier_slug` is a build error (empty `entities`) — fix it upstream.
- **Regional buckets** (`XAF`, `XSS`, …) get a Financing section like any place.
- **Idempotent and incremental.** Each in-scope section is recomputed from **all** its current `raw/` records, not a delta; a scoped run and `--all` write byte-identical sections for the places they share.
