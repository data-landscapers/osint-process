<!-- reader: cc; type: brief -->
# Standing brief — sweep slice

*(The parent pastes this file verbatim into every sweep slice's brief, under the night's own facts: the window, the high-water mark, and `scripts/drop-digest.py`'s output. Rules only; the incidents behind them are in git. `SWEEP-CYCLE.md` → *What every sub-agent prompt carries*.)*

## Capture

Capture the **full verbatim article body** at fetch time — a private research vault under the UK CDPA s.29 research and private-study exception; nothing captured is republished. **Read `wiki/capture-rule.md` in full before your first fetch**: it governs excerpts and paywalls, the DoH check before "unreachable", controlled values (look them up, never invent; blank beats a guess), fetching without reading bodies into context, and the row's own instrument before a search.

## Containment — exact files

You write **only** to `C:\OSINT\new\` (one staged candidate per file) and to `C:\OSINT\sweep\<your sweep>\` (per-run files suffixed with your batch label). Nothing else: never `raw/`, `wiki/`, `lookups/`, `sweep/ingest/` (ingest's drop log, which `drop-digest.py` reads as ingest's throw-backs), `state.json`, `seen.csv`, `logs/drop-list.csv` or any register. The one exception is `logs/sweep-url_log.md`, and only through its appender (below).

## A discard is a drop

Every in-window item you put aside — already held, already seen, a sibling's catch — is **one row in your batch's drop log** under the closest `intake.md` §7 code, and counts in `dropped=N`. A drop on the item's own merits (`off-topic`, `off-place`, `inadmissible-origin`, `no-development`, `headline-only-stub`, `already-held`, `syndicated-copy`, `fails-record-test`) also runs `python scripts/url-log-append.py dropped URL`, with no `--code`: `--code` writes ingest's drop log, which a sweep never writes. Codes that are not a verdict on the item (`out-of-window`, `not-this-slice`, `url-dead`, `fetch-blocked`, `date-unestablished`) stay out of the URL log. **`inadmissible-origin` is a verdict on the host**, which failed `origin-screen.md`; a paid, promotional or vendor piece on an admissible outlet is `no-development`.

## Before you fetch, before you write

- Check `logs/sweep-url_log.md` for each URL on its own before fetching, normalised by `vault_lib.normalise_url()` — never one combined pattern file. Any hit is already ruled on: do not stage it; log it `already-seen`.
- Re-check `new/` for the same URL **immediately before writing** a staged file. On a collision the later writer withdraws its own copy and logs `already-seen`.
- Delete only an exact path you wrote, one file at a time — never a glob, a `find`, or a match on frontmatter. `sweep_batch:` is the run's label, not yours.

## Never

- Write `logs/log.md` or `reviews/rule-candidates.md` — flag it in `notes=`; the parent writes them.
- Edit a root process file, `CLAUDE.md` or any `wiki/` spec; a rule change is a recommendation in your return.
- Run a git command that writes, or any tree-wide one (`stash`, `reset`, `checkout`, `clean`).
- Spawn a sub-agent.
- Ask a question or wait on a prompt: take the conservative option and say so in your return.

## Files

- **Staged frontmatter**: every candidate carries `type`, `title`, `url`, `publisher`, `published`, `date_precision`, `date_source`, `retrieved`, `places` (a list, never `place:`), `topics` and `sweep_batch`. Run `python scripts/stage-check.py` over `new/` before you return and fix what it names in your own files.
- **Line endings**: write a file back with the endings it had at `git show HEAD:<path>`; add a missing final newline. Test with bytes, never a shell grep:

```
python -c "b=open(PATH,'rb').read(); print('CRLF' if b.count(b'\r\n') else 'LF')"
```

- **Scratch** only under your own slice-named subdirectory of the scratchpad, never a generic filename.

## Your return — one line

```
step=<name> stopped=<complete|context|error> staged=N dropped=N needs-clip=N remaining=N notes=<≤10 words>
```

A nil is reportable only on `stopped=complete`; a broken instrument is `stopped=error`. `context` with `remaining=N` means the parent re-spawns you.
