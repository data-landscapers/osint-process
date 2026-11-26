<!-- reader: cc; type: runbook -->
# blind-classify.md — thirty of a night's admissions, classified again blind

Called by `SWEEP-CYCLE.md`'s lint stage, after the ingest commit, every night. It is a measure, not a pass: it changes no record, and its result rides the manifest's `classify` block, not a log line. *(Strategic review 8 R189, 2026-11-26.)*

**Why.** Ingest files each record under a place and a subject, and nothing measured whether a second reader would file it the same way. Thirty records a night for a month says which facet disagrees most, and so where the filing rules in `wiki/facets.md` need work.

## When it stands down

`python scripts/usage-log.py --opened-above 70` exits 1: it does not run that night. No reading means it runs. A night with no admissions has nothing to sample.

## The night

1. `python scripts/blind-classify.py --pick 30 --night <ingest night> --out <scratchpad>/blind-classify`. The night is the collection stamp's `ingest_started` date. The script writes `NN.md`, each record's body without its frontmatter, and `key.json`.
2. One fresh sub-agent, told nothing about the records or the night. It is given the folder's `NN.md` files, `lookups/countries.csv`, `lookups/taxonomy.md` and `wiki/facets.md`. It is told not to open `key.json`, `raw/` or `wiki/`. It writes `answers.csv` in the folder: `n,places,primary_subject`, one row a file, places `;`-separated codes from `countries.csv`, and one subject slug from the taxonomy.
3. `python scripts/blind-classify.py --score <folder>` appends one row a record to `logs/blind-classify.csv`, which the lint stage commits.

A missing or malformed answer counts as a disagreement. The parent does not rerun the agent to improve the score, and it never edits a record because the blind reader disagreed: a disagreement is a measurement, not a correction.

## After a month

The night `blind-classify.py --status` first reports 30 nights, the parent writes one paragraph to `X:\bill-notes.md` as a block of its own: which facet disagrees most, at what rate, and the commonest pair of filed and blind values behind it. The rows are in the log, so the paragraph names them and does not reargue them.
