<!-- reader: cc; type: runbook -->
# STATUS-ACQUIRE.md — absorbing CORPUS's status-report batches

Trigger: **"run status acquire"**. The close runs it unattended every night (`SWEEP-CYCLE.md`), so the trigger is the repair path, not the normal one.

CORPUS builds a country status report over sources this vault does not hold — see [AGO](https://corpus.data-landscapers.io/reports/AGO/AGO-status.html) for the shape. `X:\africa-acquire.csv` is the list those reports were built from: one row per source CORPUS cited and this vault has no capture of. **CORPUS now works that list itself** *(strategic review 4, R24, 2026-09-18)*. This file is what remains on this side.

## The split — two scripts, two names, one per machine

**CORPUS owns the feed, the screen, the fetch and the staging**, through its own `status-stage.py`. The drop classes it screens by, the URL normalisation it matches on and the shape of the list it returns are stated for it in `X:\status-acquire.md`, because it may not read this file or `CLAUDE.md`.

**This side owns `--select`, the run manifest, the rejection register and the close**, through `scripts/status-acquire.py` — still the only thing that reads or writes `X:\africa-acquire.csv` and `X:\acquire-done.csv`. Never sed either; a shared file CORPUS also writes is not a thing to hand-edit.

**The ingest is nobody's step here.** The cycle pulls the batch at its first act and INGEST Phase A adjudicates it in the backfill lane with everything else.

## What arrives

| On the share | What it is |
|---|---|
| `X:\new-queue\status-acquire-{ISO3}\` | the staged candidates, with `READY` written last |
| `X:\prepared\status-acquire-{ISO3}-drops.csv` | `url,iso3,class,note` — every row of the country that was **not** staged, exactly once |

A row is staged or dropped and there is no third state, so the country's own rows are the denominator: what the drop list does not name was staged.

## The close absorbs it

```
python scripts/status-acquire.py --absorb
```

**Unconditional, every night, at the close.** A night with nothing due prints one line and stops. Bare, it takes every due country; `--absorb {ISO3}` takes one. `--due` lists what it would take.

**Due** = the drop list is on the share **and** the batch folder no longer carries `READY`. The pull's `delivered-` marker is not the test — CORPUS removes the emptied folder once it has committed the marker, so its absence proves nothing, where `READY` present is a durable statement that the batch is still owed.

Per country it selects the rows (pre-marking `held` and `rejected` off `lookups/raw-url-index.csv` and `lookups/rejected-urls.csv`), applies each drop class, marks every unnamed row `staged`, registers the permanent negatives, closes the rows into `X:\acquire-done.csv`, and renames the drop list `…-drops-absorbed-YYYY-MM-DD.csv` — because CORPUS appends to the feed, and a stale drop list would otherwise be read against a later batch's rows.

| CORPUS's class | Status recorded | Registered in `lookups/rejected-urls.csv`? |
|---|---|---|
| `not-a-document` | `dropped` | **yes**, through `raw-url-index.py --reject not-a-document` |
| `duplicate-row` | `dropped` | no |
| `unfetchable` | `dropped` | **no** — one attempt on one day is not an adjudication, and that file pre-marks a URL rejected in every later country |
| `held` | `held` | no |
| `rejected` | `rejected` | no — already there |

**A pre-mark from `--select` wins over the class CORPUS sent.** This side's normalisation is the authoritative one, and a URL the vault already holds is never written to the register. Disagreements print one line each; an unknown class refuses the country in one line.

**`staged` records that the document reached the queue, not that it was admitted.** Delivery is not admission: ingest may still drop it on scope, duplication or dating, and the row stays closed either way — one automated attempt per row, then the row is resolved. A `dropped` row that bears on a specific page still earns one dated line on that page saying the document is not held (`CLAUDE.md` → *Working the base*); where only a hand-clip could get it, `X:\fetch-list.md` takes it.

## Containment

`--absorb` writes `lookups/rejected-urls.csv` (through `raw-url-index.py`, that register's only writer), its manifest under `sweep/status-acquire/` — created and removed inside the run, so the tree shows nothing — and the two CSVs on `X:\`, which are outside this repo. The close's check is therefore

```
python scripts/assert-containment.py --stage close --allow-extra lookups/rejected-urls.csv
```

and the allow is a no-op on a night that absorbed nothing.

## By hand

If the close did not absorb — the run broke, or the drop list landed after it — run the same command. It is idempotent by construction: a country whose rows have left `africa-acquire.csv` is no longer due, and its drop list has been renamed.

## Ending the pass

One line to `logs/log.md` via `scripts/log-append.py`, **only where it absorbed something**:

`status acquire — STP 28 rows: 20 staged, 5 dropped, 3 rejected; 2 URLs registered not-a-document`

Then the standing count line (`STATUS.md` → *wiki status*).

## Concurrency

One absorb at a time. `X:\africa-acquire.csv` is shared with CORPUS, and a country is closed whole or not at all.
