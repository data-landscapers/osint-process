# SWEEP-BULLETIN.md — the late-morning top-up

Trigger: **"run the bulletin sweep"**, typed by hand, typically late morning. Manual only — like `SWEEP-CYCLE.md`, **no automatic or scheduled trigger exists or is planned**.

**The gap it fills.** CORPUS builds a daily bulletin covering **today and yesterday**; the overnight sweep supplies yesterday and nothing of today. This process sweeps today, ingests what it finds, and mirrors.

**It is wiring, not a new sweep.** It runs existing processes in order, with one delta each — a today-only window and a scoped ingest. Every rule governing the actual work stays in `SWEEP-DAILY-LIST.md`, `SWEEP-DAILY-OFFLIST.md`, `INGEST.md`, `CLAUDE.md` and the `wiki/` specs.

**Never run it while the cycle is running.** Two runs staging into `new/` at once double-fetch and race on the same files. If a night is still running, wait for it.

## The sequence

```
run the Exa canary — one trivial search; on failure STOP, write nothing      # § Step 0

run SWEEP-DAILY-LIST     (today-only, stage-only, feed instrument)           # § The two legs
run SWEEP-DAILY-OFFLIST  (today-only, stage-only)

assert-containment.py --stage sweep   — exit 1 = do not commit as it stands
git commit — the bulletin's staged catch

run INGEST Phase A — over this run's staged files only, by explicit list     # § Scoped ingest

assert-containment.py --stage ingest
git commit — ingest + compile

stamp sweep_closed / ingest_started — measured, parent-written               # § The collection window

write cycle-manifest.json — cycle-manifest.py, after the final commit          # § Mirror
mirror the tree to O:\ — FreeFileSync.exe SyncSettings.ffs_batch            # § Mirror
```

No lint, no reconcile, no acquire, no Phase B. The bulletin needs today's sources in `raw/` and the mirror carrying them; everything deliberative stays on `WIKI-SYNC.md`'s cadence.

## Step 0 — the Exa canary

**`SWEEP-CYCLE.md` § Step 0, unchanged and not optional.** One `web_search_exa`, `"data protection Africa"`, `numResults: 1`, before anything is selected or written. On an error, an exception, an empty result set or an absent connector: write one line to `logs/log.md` — `bulletin sweep: Exa canary failed — <the error> — not run` — and **stop**. No fallback tool, no reduced run, no legs run anyway. On a today-only window a dead instrument and a quiet morning produce the same output, and the bulletin would publish the difference.

## The window — today, and only today

`window_start = window_end = today`. **Drop test by date, as always** (`SWEEP-DAILY-LIST.md` § *Compute the window*): an item survives only if its publication date, **established from the fetched page**, is today. Everything else is dropped `out-of-window` to the drop log.

**Yesterday is the overnight run's and is not re-swept here.** A yesterday item the night missed is the cycle's overlap window's job.

## No state is written — the one hard rule of this process

**The bulletin advances neither sweep's high-water mark, and writes to neither `sweep/daily/state.json` nor `sweep/off-list/state.json`.** It holds no state of its own either; its window is the calendar, not a ledger. Those two files are the cycle's window ledger: advancing them in the morning sets tonight's `window_start` to this morning, and everything the today-only filter dropped is lost from both instruments, silently.

It keeps its own folder, **`sweep/bulletin/`** — `manifest-YYYY-MM-DD.md` and `drop-log-YYYY-MM-DD.csv`, same shapes as the daily sweep's. Both `seen.csv` files are **read for dedup and never appended to**. What stops tonight re-fetching what the bulletin ingested is the **`raw/` URL index** (`python scripts/raw-url-index.py --check -`), written by ingest at admission.

## The two legs

Both are **stage-only** and both stage flat to `new/YYYY-MM-DD-slug.md` with `sweep_batch: bulletin-YYYY-MM-DD`. Frontmatter, capture rule, origin screen ([`wiki/origin-screen.md`](wiki/origin-screen.md), run on every candidate), conservative dedup and the drop-log discipline are their own files' and are unchanged.

### Leg 1 — the list, on its feeds

`SWEEP-DAILY-LIST.md` over the domains in `lookups/sweep-daily.csv`, read fresh, in **one sub-agent**.

**Run the publisher's feed or listing only — no query cluster.** The newest ~48h is under-indexed by Exa and a today-only window sits wholly inside that lag, so the search leg's nils would be index lag rather than evidence. The listing is already that sweep's declared instrument (§2, *one instrument per domain*). **Rule 0 holds — feed first, parsed in the shell, bodies written straight to the staged file, never read whole.**

**The one carve-out survives.** Where a domain's `sweep/domains/{domain}.md` records that its listing omits the beat (Rule 4), search *is* that domain's instrument and runs, date-bounded to today.

**A nil is a nil**, recorded and not chased — on a today-only window most domains will be nil most mornings.

### Leg 2 — off-list, on the Agent

`SWEEP-DAILY-OFFLIST.md`, both tracks, `agent_run` at `effort: "medium"`, each objective told the window is **today** and that the date applies to publication. **Track B runs as two objectives** — the worldwide leg explicitly instructed not to return Africa-datelined items (`SWEEP-DAILY-OFFLIST.md` → *The two tracks*). Three objectives, one sub-agent.

There is no listing to fall back on, so the Agent is the only instrument. A misdated older article is exactly what a "published today" brief attracts, so **verify every date at fetch** — the fetch-side date check is the leg's main filter, ahead of the firewall.

Expect thin. The firewall still carries the whole load (`SWEEP-DAILY-OFFLIST.md` § *The firewall*), and a low stage count off a wide search is the screen working.

## Scoped ingest — this run's files, nothing else

`INGEST.md` Phase A, run over **an explicit file list: the items this run staged**, taken from `sweep/bulletin/manifest-YYYY-MM-DD.md`.

**Anything else sitting in `new/` is left exactly where it is** — last night's undrained residue, an acquisition fetch, a hand clip. Those belong to the next full drain.

This is an ordinary Phase A slice: `INGEST.md` slices by explicit file list, and `scripts/origin-screen.py` runs per slice on that slice's list. Under ~15 items it runs inline, without a sub-agent. The four dispositions, the per-item `sweep-url_log.md` line at step 11, and the close (finance compile if any finance record landed, then hub compile scoped to the places touched) all fire as they always do. **`logs/ingest-pending-writes.md` grows and is not drained** — Phase B is `WIKI-SYNC.md`'s.

## The collection window — two fields, measured, and the parent's alone

**Measure `sweep_closed` and `ingest_started` for every run**, local machine-clock time, and carry them to two places: into `INGEST.md`'s own close, which stamps them (with its own `last_admission`) via `cycle-manifest.py --stamp`, and at the **top of `sweep/bulletin/manifest-YYYY-MM-DD.md`** as this run's own independent record. `intake.md` §6a holds the shape. **Blank-line separate the two in a manifest** — `scripts/reflow-md.py` joins consecutive non-blank lines as a hard-wrapped paragraph.

`sweep_closed` is **leg 2's return** — the moment after which nothing more could have been caught, which is also what the sweep-stage commit records. `ingest_started` is the **first Phase A slice's spawn**.

**The parent measures them and no slice does** — the parent is the only actor that measured both. Both come from measurement — the spawn you made, the commit you took — never from an estimate. `last_admission` stamps admission, not collection; CORPUS reads `cycle-manifest.json`'s `collection.sweep_closed` directly as the bulletin's *Last updated* byline, with no fall-back behind it (notes-for-osint 132) — with no rotation `End` row to read, these two fields are the only record that this morning's collection stopped, so a close that skips `--stamp` leaves the byline on a stale run.

## Commits

Two, at the same boundaries the cycle uses: without them a run that dies mid-ingest leaves a well-formed tree indistinguishable from a finished one. Each is preceded by its write-set assertion — `python scripts/assert-containment.py --stage sweep`, then `--stage ingest` — exit 1 meaning do not commit as it stands.

## Mirror

**First, the manifest**: `python scripts/cycle-manifest.py --pass "bulletin sweep" --count staged=N --count admitted=N --count dropped=N`, after the final commit and before the mirror, exactly as `SWEEP-CYCLE.md` § *The cycle manifest* specifies. This run mirrors, so it owes CORPUS an account of what it mirrored; the counts are this run's own measurements, passed in.

**The last act, after the final commit**, so everything the run produced is durable in git before it starts: `"C:\Program Files\FreeFileSync\FreeFileSync.exe" SyncSettings.ffs_batch`, exactly as `SWEEP-CYCLE.md` § *Mirror* specifies.

**Verify that it landed, and never rely on stdout to tell you.** `O:\` is CORPUS's read-only copy of this vault and this step is the only thing that supplies it. Invoked from this run the mirror **detaches, returns no output and sets no exit code** while completing normally in the background. **Assert on `git -C O:\ rev-parse HEAD` matching local** — that tests the thing CORPUS reads — and read the **HTML run log** under `%APPDATA%\FreeFileSync\Logs\`, newest file, whose header carries `Completed successfully`, the element count and the elapsed time. **The mirror is asynchronous — wait for the `FreeFileSync` processes to exit before asserting anything**, or the HEAD check reads a half-copied tree.

**It runs even on a nil morning.** The manifest, drop log and log line changed, and a mirror that always ran is one fewer thing to reason about when the bulletin looks wrong.

## Delegation

**Three sub-agents on a normal run** — one per leg, plus one for ingest only if the catch is large enough to want it. The five lines every spawn carries are `SWEEP-CYCLE.md` → *What every sub-agent prompt carries*, and none is optional: the capture rule, the containment boundary, `log-append.py`, no-amending-a-process, and the nil/`stopped=` rule. **A nil is reportable only on `stopped=complete`.**

## Finishing

One line to `logs/log.md`, written through `scripts/log-append.py`:

`YYYY-MM-DD HH:MM · bulletin sweep · staged N · admitted N · dropped N · mirror ok|FAILED · revert: <commit>`

A judgement call the run made goes in the commit body, never a second log line (`STATUS.md` → *The `log.md` entry*). Anything irreversible or already public → `reviews/post-run-notes.md`, numbered, ≤60 words.

Then the close report — the one line of `STATUS.md` and nothing else:

```
contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN
```

plus one bulletin line: `bulletin: staged N · admitted N · list N / off-list N · mirror <syncResult>`.
