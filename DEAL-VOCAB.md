<!-- reader: cc; type: spec -->
# DEAL-VOCAB.md

Trigger: **"run deal vocab"**. The controlled vocabularies for the three filterable fields of a `## Deal record` — **Instrument**, **Status**, **Beneficiary type** — the rules for writing them, and what a bulk edit of deal records must do afterwards. Held by lint #28 (`LINT.md`), which surfaces and never auto-fixes.

## 1. The vocabularies

**`lookups/deal-vocabs.csv` is the authority on what may be written.** One file for all three fields — `field, sort order, value, definition` — so a value is added or reworded in one place. `sort order` is the order values appear in on a page or in a filter: the lifecycle for status, rough likelihood elsewhere, never the alphabet. **The definitions live there, one line each, and are not repeated here.**

**Three map files say what a legacy wording becomes**: `lookups/deal-instrument-map.csv`, `lookups/deal-status-map.csv`, `lookups/deal-beneficiary-type-map.csv`, each `value, source_value, review, note`. They are remediation, not vocabulary — their job is to catch a legacy wording arriving late from IATI or a re-ingest. A row is a **mapping**: that wording, wherever it appears, becomes that value. A row whose value is blank and whose `review` reads `REVIEW` is a wording nobody has ruled on.

**Every `value` a map produces must exist in `deal-vocabs.csv` for that field.**

- **Instrument** — Bond, Buyer's Credit, Commercial Loan, Concessional Loan, Equity, Grant, Guarantee, Joint Venture, Line of Credit, Mezzanine, MoU, PPP, Self Funded, Technical Assistance, Unknown.
- **Status** — Pipeline, Approved, Active, Closed, Cancelled, Suspended, Unknown.
- **Beneficiary type** — Public Sector, Private Sector, NGO, Multilateral, Research, Fund, Multi-stakeholder, Individuals, PPP, Unknown.

**Five values carry a rule rather than a description.** `Concessional Loan` takes IDA credits. `MoU` is only for an agreement whose instrument is genuinely unstated — never shorthand for unclear. `Unknown` is not the same as blank. `Fund` is deliberately not `Private Sector`: it is one step removed from the ultimate recipient. `NGO` takes not-for-profit membership bodies and industry associations.

**`PPP` appears in two of the three vocabularies and means a different thing in each** — a concession, BOT or similar as an instrument; a public-private vehicle receiving as one party as a beneficiary type. Never merge them.

## 2. Rules for writing a deal record

**The three fields take a value from the vocabulary, spelled exactly as the vocabulary spells it.** Nothing else is admissible. This overrides `wiki/finance-news-driver.md` ("nothing is normalised") *for these three fields only* — the rest of the record keeps the source's own words (`wiki/finance-record-spec.md`).

**Where the source says more than the value carries, the extra goes in `## Notes`, never in the cell.** A table cell holds a value. A source label, an "unverified" flag or a correction written beside the value — `Concessional loan *(source label, unverified — see Notes)*`, `IDA grant *(corrected from the source's "Concessional loan"; PAD00070 records an SDR 69.5m IDA grant)*` — belongs in Notes, where it can be read, not in a column where it splits the count.

**Never write a sentence in one of these cells.** `Not stated; project's own dates (2023-03-01 to 2024-04-30) have elapsed as of this capture` is a Notes entry with `Unknown` in the cell.

**Never leave one blank.** `Unknown` means the source does not state it; a blank means nobody has looked, and an absence cannot be counted. The absent row is the worse defect of the two.

**In a value of the form `X — Y`, the later clause governs.** `Approved — project activities launched 2026-07-29` is **Active**: the approval is the older fact and the launch the newer. This decides most compound statuses.

**Do not carry an IATI code into the cell.** `Standard grant (IATI finance-type 110)` maps to `Grant`; the code, if worth keeping, goes in Notes. **Do not infer concessionality from a finance-type code** — IATI 421 is the generic loan code and says nothing about terms.

**A concession is not a concessional loan.** False friends.

**Map matching is case- and whitespace-insensitive.** Case is what a writer varies without noticing.

**A wording that maps to nothing takes a ruling, recorded as a map row**: a value from the vocabulary, a new vocabulary value — added to `deal-vocabs.csv` and the map in the same edit — or a decision that the record is not a deal at all (money flowing *to* the state for a spectrum or licence award runs the opposite direction from everything else in the register). A value outside the vocabulary after a pass is a bug in the pass, not a new vocabulary member.

## 3. After a bulk edit of deal records

**Scope.** Every file under `raw/*/` carrying a `## Deal record` section. Records retired by merge — no `finance_origin:`, a `retired_deal_id:` and a `cite_through:` instead — are out of scope: their stale deal tables may be left or stripped and reach no output either way.

**Where the original wording carried more than the new value does, move that text to `## Notes` in the same edit.** That is the whole difference between a mapping pass and a data loss.

**OSINT: compile first, `finance-compile-scope.py --commit` second, never the reverse.** `finance-compile-scope.py` scopes FINANCE-COMPILE to the places whose finance records changed since `last_compile_commit`, diffing the ref against the *working tree*, so it sees the edits whether or not they are committed. `--commit` advances the state ref to HEAD; run it before the compile and the edits fall behind the ref, the next scope reports nothing to do, and the recompile never happens — silently, because an empty scope is indistinguishable from an up-to-date one. Expect a bulk edit to scope to every place; budget for a full compile.

**The hub prose changes too, not only the CSVs.** `compile-hub-financing.py --write` (FINANCE-COMPILE step 2) rebuilds the `Instrument mix: …` line of each place hub's `## Financing` section from the `instrument` column and is not optional after a pass over instruments. Status and beneficiary type do not reach the hub.

**CORPUS: both stages must run — the compile, then the render.** CORPUS has no queue: `rebuild.py --finance` runs `build-finance-page.py --all`, and `scan_all()` walks every record under `raw/` on every run, so edited records are picked up because they are read. The compile rewrites `outputs/non-state-finance/*.csv`; the render turns that into pages, and `editions.publish` cuts a new dated edition of each CSV because the bytes moved. Compile and stop, and the site still serves yesterday's values from yesterday's edition.

**Verify.** After compile and render, check the distinct values in `outputs/non-state-finance/all-nonstate.csv`: every value in the vocabulary for its field, and no blanks in any of the three.
