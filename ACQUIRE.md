# ACQUIRE.md — the acquisition pass

Trigger: **"run acquisitions"**. No selection. The pass takes **every item in `reviews/acquisitions.md`**. One automated attempt each, then the item is resolved one way or the other — nothing is carried for a human loop.

**A dead domain is not a dead document — ask the Internet Archive before concluding either.** `http://archive.org/wayback/available?url=<url>` names the nearest capture, and `http://web.archive.org/cdx/search/cdx?url=<host>&matchType=domain&fl=timestamp,original,statuscode&collapse=urlkey` lists everything a host once served. Both are ordinary automated fetches inside the one attempt, not a second one. **A live 404 dates the absence; it does not date the document.** Any finding of the form *this site publishes nothing* is unsafe until the archive has been asked, and a `raw/` deletion or a *Record not held* line resting on one says which was tested.

Governing rules: `CLAUDE.md` (admissibility, currency) and the `wiki/` specs — `layout.md` (filing), `schemas.md` (schemas). This file is only the loop.

---

## The loop

**0. First, once, for the whole list: `python scripts/lint-acquisition-held.py`, and read every strike it proposes before applying it.** It strikes any item the wiki already holds — the URL is already a `url:` in `raw/`, or the file is already a held `artefact:`. **An `excerpt` body is not an incomplete one** (`schemas.md` §4): a structured extract of a tabular document and a journal abstract with its citation are the complete record for those documents. Striking costs nothing; fetching costs the item's one attempt. Same check as lint #22.

**The script matches on URL alone, and that is the wrong instrument for this register, so its output is a suggestion and never an instruction.** It fails in both directions at once. It **over-strikes**, because a line raised by ingest usually carries the URL of the *announcement of* a document rather than the document — a publisher's abstract, a brief page, a news item naming a report — and striking on that loses an acquirable want. And it **under-sees**, because most open lines carry no URL at all, so the check passes over them silently and reports nothing. **The hand-grep is what does the work**: before spending a line's one attempt, grep `raw/` and `lookups/raw-url-index.csv` by the document's **own identity** — its title, its instrument number, its author and year — not by the URL the line happens to carry. A line whose own prose says the URL is an announcement is a line the script cannot rule on.

**The strike is a URL match, and it is wrong in both directions — read it, never apply it blind.** It **over-strikes** a line whose own text says the held body is a landing page or was cut at the fetch cap and asks for the same URL again: that line is a completion the bounded re-capture exception exists to serve (`schemas.md` §4), and striking it silently drops a want the wiki has already stated. It **under-strikes** the document held under a different URL from the one a failed fetch happened to try — so **before raising a line at all** (`INGEST.md` step 8), grep `raw/` for the document's own identity, title and instrument number, at the one moment a slice has it in hand. A page that says a law is not held while the vault holds it is a false statement about the wiki's own evidence, which is worse than a wasted fetch.

For each remaining item in `reviews/acquisitions.md`:

0a. **No URL on the line → probe for one. This pass owns the gap probe, and no other does** (`intake.md` §7a). **One Exa search per line — a lookup, not a research task** — and it is the line's *locating* half, not a second attempt: found, it feeds step 1; not found, the line is dropped at step 3 like any other. Run them **in one batch at the top of the pass**, in parallel, before any fetch. **Stamp `probe_at` whether or not anything came back**, so an absence the wiki publishes is one that was searched for on a date. A gap probed against an unchanged base is not re-probed. **A probe never establishes a date** — never write a `published` from a URL path or a probe report; ingest reads it from the document.

1. **Attempt the fetch — once, properly.** In order of what the item needs:
   - a direct document URL (government PDF, gazette, project document) → fetch it;
   - a normal page → Exa fetch (`web_fetch_exa`);
   - **a JS-rendered document library → resolve the file URL, don't render the index.** The index needs a browser; the PDF it points at almost always sits on a static path that fetches fine. Get the URL from the publisher's own announcement page, a site-scoped `filetype:pdf` search, or the media/downloads path — then fetch the file. Chrome MCP needs Bill's browser open and per-site permission, so it is **not an automated route** and never the plan. An item is `[blocked — JS shell]` only when the *file itself* resists, not when its library does.

   One real attempt. Do **not** loop, retry variants, or hunt for mirrors.

2. **Got it → ingest.** Stage the document in `new/` as a normal clip — full verbatim body, date-prefixed filename, proper frontmatter — and let the normal ingest file it to `raw/`. Then **strike the line** from `reviews/acquisitions.md`.

3. **Couldn't get it → drop it.** Anything the one attempt cannot retrieve — paywall, cookie wall, 403, bot-block, subscriber-only, anything that would need a hand-clip — is **deleted from `reviews/acquisitions.md`, not parked.** Where the item bears on a specific page, add **one dated line** to that page recording the document is not held (e.g. "Gazetted text not held as of 2026-07-20"). Where it maps to no page cleanly, just delete and log the drop. No manual queue, ever.

   **A document only a hand-clip could get is dropped like any other, and the dated absence is the whole of the record** — no post-run note. That register takes only what is irreversible or already public (`CLAUDE.md` → *Reporting*), and a document nobody has fetched is neither. Identify it **exactly** on the page's own dated line — number, filename, URL — so a reader who does have a route to it knows precisely what is missing.

There is no third state. After the pass, `reviews/acquisitions.md` holds only its header.

## Ending the pass

Append **one entry** to `logs/log.md` via `scripts/log-append.py` — one line, 40 words, counts and objects: acquired / dropped (with reason class), pages that gained a dated not-held line. Then:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

`acquisitions - 00` is the expected end state.

## Concurrency

One pass at a time, and no other CC session writing to the vault while it runs.
