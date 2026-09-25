<!-- reader: cc; type: brief -->
# Standing brief — ingest Phase A slice

*(The parent pastes this file verbatim into every Phase A slice's brief, under the night's own facts: the lane, the iteration, the list directory, the sibling count and the origin-screen tally. Rules only; the incidents behind them are in git.)*

**Read `C:\OSINT\INGEST.md` in full — it is the procedure; this is the wiring.** Lean form: you **file** a contradiction or an acquisition line and never research one; you open **no** Phase B page; your deltas go to the pending-writes shape `INGEST.md` step 11 quotes.

## Your list is your slice, and it is closed

Your spawn names one list file. Every path in it is yours and no path outside it is. Do not enumerate `new/`, do not pick up a sibling's item, never reconcile `new/` against `raw/`. **Remove a candidate only by its exact path from your list, one file at a time** — never a glob, a `find`, or a match on frontmatter.

## Shared registers

- `logs/sweep-url_log.md` — **you** write it, at each disposition, only through `url-log-append.py` (a drop carries `--code` and `--batch`, step 11).
- `lookups/raw-url-index.csv`, `lookups/artefact-md5-index.csv`, `logs/ingest-pending-writes.md`, `reviews/acquisitions.md` — **the parent** writes them. Your rows for them go to a file of your own, named for your slice, and you return its path (`INGEST.md` → *The shape, the slicing*).
- Remove a row only by its own text, edit only rows you wrote, and run no whole-file formatter over a register.

**Return your delta lines verbatim, never a summary** — the parent reconciles against them, and they are the only copy if a register loses a block.

## Judgment, briefly

- **Scope, two halves**: data governance and digital transformation, **and** an African place, `XGL` or a `geopol.*` slug — else out.
- **Four dispositions, no fifth**: admitted, contradiction brief, acquisition line, deleted.
- **Duplicates**: drop, replace or keep both; replace only on a clear tier upgrade. Sweeps overlap by design, so expect twins; `raw/` is the check.
- **Academic papers and named-analyst opinion are first-class**; sparse entities and no dated event are their normal shape.
- **Currency**: time-varying figures dated; the event date is not the publication date; a late old source is a baseline.
- **The tail is not the work**: dispose of the awkward item once.

## Never

- Write `logs/log.md` or `reviews/rule-candidates.md` — put it in your return.
- Edit a root process file, `CLAUDE.md` or any `wiki/` spec.
- Run a git command that writes, or any tree-wide one.
- Spawn a sub-agent, or wait on a prompt: take the conservative option and say so.

## Files

Line endings as at `git show HEAD:<path>`, tested with bytes (`python -c "b=open(PATH,'rb').read(); print('CRLF' if b.count(b'\r\n') else 'LF')"`); scratch only under your own slice-named subdirectory.

## Your return

The tally line, then your delta lines verbatim:

```
step=INGEST-A-<slice> stopped=<complete|context|error> items=N admitted=N contradiction=N acquisition=N deleted=N remaining=N notes=<≤10 words>
```

`context` with `remaining=N` means the parent re-spawns you; an errored instrument is `stopped=error`, never a clean nil.
