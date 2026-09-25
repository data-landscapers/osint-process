<!-- reader: cc; type: runbook -->
# RECONCILE.md — the reconcile pass

Trigger: **"run reconcile"**. No argument, no selection, no scoping question. The pass takes **every item in `reviews/contradictions/open/`**. If CC finds itself asking which items to do, the answer is all of them.

Rules governing the work are in `CLAUDE.md` (currency, admissibility, duplicates) and the `wiki/` specs — `schemas.md` (schemas), `layout.md` (filing) — with `LINT.md` for lint. This file is only the loop.

---

## The loop

For each file in `reviews/contradictions/open/`:

1. **Read the brief.** It states the claim, each competing value, who asserts each, and the source URLs the wiki already holds. Take the question from the brief, not from the wiki page — the brief is deliberately wiki-agnostic.

2. **Research it externally.** Exa by default (`web_search_exa` / `web_fetch_exa`). Seek the **primary**: the gazette, the regulator's bulletin, the filing, the court record, the statistical release. Secondary reporting settles nothing that a primary can settle.

3. **Ingest what you find.** Primaries are filed as normal sources — full verbatim body, date-prefixed filename, proper frontmatter. **Research notes and search output are not sources and are not written to disk at all**: they stay in the session and are discarded. There is no research or quarantine folder; do not create one. Anything worth keeping is worth ingesting as a primary; anything not worth ingesting is not worth filing. The page fix cites the primary, never the synthesis.

4. **Apply the resolution** to every affected page. **The precedence call — which value wins, and whether what the research turned up settles it or is a third value needing its own line — is this pass's own judgment**, reasoned against the primaries just ingested, not from a title or a filename. Prefer the newest value. Write the resolved figure dated, and keep at most one dated prior where the trajectory means something. Clear `needs-review`.

5. **Close it.** Record the resolution and its date **on the affected page and in `logs/log.md`**, then **delete the brief** from `reviews/contradictions/open/`. Deleting is the **last** step, so an interrupted pass resumes cleanly — whatever is still in `open/` is still open. There is no `done/` folder; git holds the deleted brief.

## When an item won't close

**One brief, one attempt.** A contradiction this pass cannot settle is disposed of where it stands:

- Write the position onto the page it bears on — dated, and honest about what is not established. A known vacuum is a finding, not a silence.
- **Delete the brief**, having first written what was tried onto that page. The page carries the finding; the brief was only the worklist entry.

There is no attempt counter to record, because there is no second attempt to count towards. If the evidence arrives later it arrives attached to something — a source ingested, a figure that stops matching — and a brief written then is the brief to write.

## Re-routing

An item that turns out to be a **specific document the wiki simply doesn't hold** is not a contradiction. Strike it from `reviews/contradictions/open/` and add it to `reviews/acquisitions.md` — a fetch list drained by the acquisition pass (`run acquisitions`), never by reconcile.

**Only the run's first reconcile may re-route** — the second half of `INGEST.md` step 8's rule. A later reconcile in the same run does what *When an item won't close* does: **write the position onto the page it bears on, dated and honest about what is not established, then delete the brief.** The item leaves `open/` either way; the difference is that no line lands in `reviews/acquisitions.md`, so acquire cannot fetch it, ingest cannot admit the fetch and raise another absence, and the run reaches its own end.

**Absent a stated iteration, a reconcile is the first one** — standalone `run reconcile` and the nightly cycle's close both are. `UPDATE-WIKI.md` is the only caller that loops and the only one that must pass the counter.

## Discipline

**Cite only links you actually hold** (`CLAUDE.md` → *Working the base*). Where nothing is on file, say so — that absence is the finding, and for many briefs it is the whole finding.

**Never overwrite silently.** If the research produces a *third* value rather than settling the two, that is a live contradiction: record it, don't pick.

## Ending the pass

The durable resolution lives **on the affected page and in `logs/log.md`** — which is why closing a brief deletes it.

Append **one entry** to `logs/log.md` via `scripts/log-append.py` — one line, 40 words, counts and objects: researched / resolved / re-routed / closed-unresolved, primaries ingested. Then the tally:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

## Concurrency

One reconcile pass at a time, and no other CC session writing to the vault while it runs. `reviews/contradictions/open/` is a shared worklist and a second writer corrupts it.
