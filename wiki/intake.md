# intake.md — filing rules, the two run logs, sweep intake and containment, the gap probe

Split out of `reference.md`; section numbers are kept so a `§N` reference resolves unchanged. `CLAUDE.md` holds the principles and wins where the two disagree.

---

## 6. Filing rules — draining the `new/` queue

**The ingest procedure is [`INGEST.md`](../INGEST.md)**, triggered by "run ingest", a first-class pass alongside reconcile and acquire. Its numbered filing steps — including the **step-2a finance branch** and the **step-10 `last_reviewed`** stamp — keep their numbers there, so a "§6 step N" reference resolves. This heading is the pointer; the schemas and folder rules the steps apply live in the specs — `layout.md` §2 folders and §3 filenames, `schemas.md` §4 frontmatter and §5 entity bar, §7 sweep intake below, `operations.md` §8 hygiene. `new/` only — `new-budget/` is never drained (`layout.md` §2).

### 6a. The run logs — shapes

Written by ingest; their **shapes** are schemas and live here, so `INGEST.md` stays a procedure.

**The collection window — `sweep_closed` and `ingest_started`, local machine-clock time, unconverted** (`cycle-manifest.py` → `rotation()`'s note; notes-for-osint 55 settled this by documentation rather than conversion, since a conversion is a process change and `CLAUDE.md`'s freeze to 2026-09-27 holds it). Any path that puts material into `raw/` records the moment **after which nothing more could have been caught** and the moment ingest **began**. Ingest's own close stamps a third value alongside them, `last_admission` — its `logs/log.md` line's own timestamp. All three are written together, at the close, by `python scripts/cycle-manifest.py --stamp --sweep-closed … --ingest-started … --last-admission …` (`logs/ingested_log.md`, retired 2026-09-07, held this same triple as a heading and a stamps line; `--stamp` replaces the heading with a single overwritten `logs/collection-stamp.json`, not a rolling log — see the script's own docstring). Where a path also keeps a manifest, the same two measured values still go at its own top too, as that run's own record — a second, independent copy, not the read path.

- **The parent stamps them, not a slice** — it is the only actor that measured `sweep_closed`/`ingest_started`. Written from measurement, never estimated; `--at` on `log-append.py` exists for this class of value, and `--stamp` itself refuses a value ahead of local now.
- **`last_admission` stamps admission, which is not collection**, and the bulletin's *Last updated* byline is a claim about collection. The byline reaches CORPUS through `cycle-manifest.json`'s `collection` block, which `--stamp` feeds directly — CORPUS reads `collection.sweep_closed` with no fall-back behind it (notes-for-osint 132), so a close that skips `--stamp` leaves that block naming a stale run rather than this one.
- Where a run collected nothing itself and only drained a queue others staged, `sweep_closed` is the **newest `retrieved:`** across the items it admitted.

**`logs/sweep-url_log.md` — the index sweeps grep.** Written **per item at its disposition** (`INGEST.md` step 11), not at the close. `YYYY-MM-DD | disposition | normalised-url`, in dated sections, newest first.

- **All four dispositions, not just admissions:** `admitted`, `dropped`, `contradiction`, `acquisition`. A rejected item is exactly the one a sweep must not fetch again.
- **One line per unique normalised URL per run** (a budget document fans out into many records sharing one URL). Across runs, duplicates are harmless and a re-appearance keeps the URL alive past a prune.
- Normalised by `vault_lib.normalise_url()` — **the same function the sweeps' pre-fetch filter uses**, or the two gates disagree. Pruned to **one rotation** by `SWEEP-CYCLE.md`.

**`lookups/raw-url-index.csv` is the `raw/` half of that same gate.** `sweep-url_log.md` reaches back one rotation; the index reaches back for ever. Same normalisation, plus a `slug_key` — the final path segment — for the case exact URLs miss: one outlet re-publishing an item under a second canonical path. Appended per admission at `INGEST.md` step 11, its row removed on retire or replace, rebuilt by `scripts/raw-url-index.py --rebuild`, count checked by lint #27.

---

## 7. Sweep intake (`new/` and `sweep/`)

Acquisition sweeps run *upstream* of the wiki and stage into `new/`.

- **Daily sweep** (the workhorse) — procedure in **`SWEEP-DAILY-LIST.md`**. Run manually from CC; loops the domains in `lookups/sweep-daily.csv` (read fresh each run) over a high-water-mark window; stages **flat** candidate files into `new/` (no per-place subfolders); keeps its state in `sweep/daily/`.
- **Content sweeps** (newspapers, journals, thinktanks) — three procedures, **`SWEEP-NEWSPAPERS.md` / `SWEEP-JOURNALS.md` / `SWEEP-THINKTANKS.md`**, content-scoped rather than time-scoped. Each works a list (`lookups/sweep-{newspapers,journals,thinktanks}.csv`) over a window it is **given**, not one it keeps: **stateless**, windowed by `SWEEP-CYCLE.md` from the rotating day's `Start`, so the cycle log is the single record of when a day last ran. `sweep/{newspapers,journals,thinktanks}/` hold drop logs only. Stages flat into `new/`. **Stage-only** — they never call `update wiki`; the caller drains `new/`.
- **Off-list sweep** — the universal sweep of everything *except* the listed domains; procedure in **`SWEEP-DAILY-OFFLIST.md`**, two tracks (Africa infrastructure; worldwide policy/governance/citizen feedback), state in `sweep/off-list/`. It **does** stage into `new/`.
- **Phase-2 back-fill** (completed) — the 2025→2026 national-press + trade-journal catch-up. Apparatus archived at **`sweep/archive/`** (procedure, query recipes, ledger, drop logs). Its `new-queue/done/` remains Bill's, untouched by CC (`layout.md` §2).

**Rules binding every sweep:**

- **Containment boundary.** The sweep writes **only** to `new/` (candidate source files with best-effort frontmatter), to `new-budget/` (budget documents and their companion pages, which ingest does not drain — `layout.md` §2), to `sweep/` (its own state/logs), and to `logs/drop-list.csv` (the origin screen's own append — below). It **never** writes to `raw/` or any `wiki/` page, not even to reformat.
- Candidates enter the base only by being **processed**: `new/ →` ingest `→ raw/`. The sweep stages straight to `new/`; ingest is the gate, so a raw sweep candidate can never become a source by accident. From `new/`, the filing rules in §6 apply unchanged.
- **Sweep-time dedup is conservative** — exact URL or confident same-outlet re-crawl only, logged per run. Nothing is discarded silently. The aggressive pass is the post-ingest duplicate lint (#7), with full text in hand.
- **A sweep may drop on scope; it may never drop on value.** **Scope** is whether the item is about data governance and digital transformation at all — `CLAUDE.md` → *The material* rejects what isn't, and rejects when in doubt; a sweep can judge that from a title and a search result. **Value** is whether the item adds to what the wiki already holds — that needs the body and the compiled base, so it is ingest's alone (`CLAUDE.md` → *Duplicates*). The line is: *is this our subject* versus *do we already have it*.
- **Drop reasons are a closed vocabulary**, one per line in `sweep/*/drop-log-YYYY-MM-DD.csv`.

  | Code | Meaning |
  |---|---|
  | `out-of-window` | published outside the run's window |
  | `already-seen` | URL already adjudicated in `logs/sweep-url_log.md`, or already staged in `new/` |
  | `duplicate-in-run` | same URL or confident same-outlet re-crawl within this run |
  | `inadmissible-origin` | failed [`origin-screen.md`](origin-screen.md) |
  | `off-topic` | outside data governance and digital transformation — the subject half of the scope drop above |
  | `off-place` | on subject, but its place is neither African nor `XGL` and it files under no `geopol.*` slug — the place half of scope (`CLAUDE.md` → *The material*) |
  | `no-development` | digest, paid placement, awards PR or vendor thought-leadership: reports no development |
  | `headline-only-stub` | free text adds nothing beyond the headline (`capture-rule.md`) |
  | `url-dead` | 404/410, or NXDOMAIN/NODATA **after** the DoH check — never on the system resolver alone |
  | `fetch-blocked` | reachable but refusing us — 403, paywall, JS wall; routed to manual clip |
  | `already-held` | the URL is new but the story is already in `raw/` under a different URL, host or syndication — the dedup index or the slug check says so |
  | `syndicated-copy` | the URL is new but this run has already staged the same story under a different URL — a syndicated repost of the canonical, or the same outlet's other-language edition; a story that is instead dropped elsewhere is coded on its own merits |
  | `date-unestablished` | in scope, but no instrument settles a publication date at all, so the window cannot be applied either way |
  | `not-this-slice` | in scope and wanted, but belongs to a row, financier or place this slice was not handed — it is another slice's or another night's |
  | `fails-record-test` | polled from a structured feed and rejected on that feed's own required fields — geography, vintage or amount — rather than on scope |

  **No free-text code and no `other`.** Where none fits, use the closest, and return the gap as a recommendation — a sub-agent does not amend this table.

  **`already-held` is distinct from `already-seen` and from `duplicate-in-run`, and the distinction is what the sweep knew.** `already-seen` means this URL was adjudicated before; `duplicate-in-run` means a sibling caught it tonight; `already-held` means the vault holds the story and this URL never would have matched. Coding the third as either of the first two, or as `out-of-window`, records a reason the sweep did not have.
- **Origin screen.** Every sweep runs [`origin-screen.md`](origin-screen.md) — the shared inadmissible-origin gate (`logs/drop-list.csv`, the hostile shapes, the `watch → drop` promotion, the mining rule). It is a called object, not a pass, so a new sweep adopts it in one line and writes no origin rules of its own. Ingest runs it again at step 1, because ingest is the only door into the base.
- **The drop list is process-written, and a sighting is written in the same edit as the screen-out.** Any pass running the screen appends its own `watch` or `drop` row to `logs/drop-list.csv` — sweep, ingest or lint alike, without waiting for Bill, who reviews after the fact like any other CC write. An adjudication that is noted but not written is the failure the screen exists to prevent. The list only ever grows; it is a screen, not a source list, and lives in `logs/`.
- **Stage the primary document, not just the announcement.** A hit that announces or links a gazette, plan, roadmap, strategy or report gets the **file** fetched and staged alongside it (`INGEST.md` step 3 → *Download the primary document*). A JS-rendered document library does not stop this: the index needs a browser, the file on its static path does not.
- The admissibility screen and the `published`-date discipline (fallback chain, `date_source: proxy`, `date_precision`) apply at **fetch/staging time** exactly as at ingest.
- **Staged candidates carry `retrieved:` but never `ingested:`.** `ingested:` is set only when the item is actually ingested.
- **Row health — ignore the first failure, report the second.** One failure is more likely a blip than a dead row; two consecutive runs of the same list failing the same row is the signal. Ledger: **`sweep/row-health.csv`** — `run_date,list,url,outcome,newest_item,reported` — one line per row whose outcome was **not** clean. **Absence from the ledger is health**; no line means the row worked.

  Outcomes, kept apart because the remedies differ:

  | Outcome | Meaning | Remedy |
  |---|---|---|
  | `unreachable` | DNS, connection or TLS failure — **only after the DoH check** (`capture-rule.md`), never on the system resolver alone | delete the row, or correct the host |
  | `blocked` | HTTP 403 or `robots.txt` disallow — reachable, refusing *us* | a different fetch route may still work; keep the row |
  | `no-listing` | HTTP 200 but no parseable listing, feed or sitemap (a JS shell, a department page) | wrong entry point — find the real one, or delete |
  | `dormant` | a live listing whose newest item is **over 12 months** old | delete the row; its nil is permanent, not a thin week |
  | `paywalled` | the site serves only ledes — every item's payload sits behind a subscription wall | **report it so the row can be removed**; the sweep cannot use it |

  Three rules on top:

  - **Report once, then stop.** Set `reported`. A row already raised is never re-raised each rotation.
  - **`dormant` needs no second strike.** It is a *measurement*, not a failure: the sweep already reads the listing's newest-item date to apply its window. Two-strike is for failures, which are transient; dormancy is not.
  - **A nil is not a failure.** A live listing with nothing *in this window* is a healthy row and writes no line. The sweep's output is an evidence claim about absence, and conflating the two would corrupt the claim.

  **The ledger is the report.** `sweep/row-health.csv` names the row, the outcome and the run, and `reported` stops it being raised twice; **the sweep source lists are Bill's** (`layout.md` §2), so this is what he curates them from, and the containment boundary puts them out of a sweep's reach anyway. It is never copied into a queue or into `reviews/post-run-notes.md`. It is a row-health ledger, not a window mark — the cycle log is the only record of windows, and no per-sweep `state.json` duplicates it.

---

## 7a. Gap probe — the acquire pass's, and no other's

**A gap found is a gap searched — by `ACQUIRE.md`, and by no other pass.** A pass that establishes the wiki does not hold something specific and named writes the acquisition line and stops there. It does not search. `ACQUIRE.md` probes — one search per line that carries no URL — because that pass already makes exactly one automated attempt per named document. A gap recorded without a search is a claim about the world made from a claim about the wiki; the probe is what turns it into a finding.

**What a discovering pass does instead** — the ordinary four dispositions, never a standing chore:

- a **named document** an automated fetch could plausibly get → a `reviews/acquisitions.md` line, `[untried]`, **with no `published` date guessed onto it**;
- a document only a browser can get → `X:\fetch-list.md`, and **only where the automated route is proven dead**;
- **two sources found disagreeing** → a contradiction brief;
- **nothing published at all** → a dated absence stated on the page it bears on, which is a finding and not a gap any more.

**`probe_at` is stamped by the acquire pass, whether or not anything was found**, and a probed gap is not re-probed until that unit's base moves. An absence the wiki publishes must be one that was searched for on a date — and the date it carries is the date *acquire* searched, not the date some other pass noticed.

**Two things a probe never establishes.** It does not establish a **date**: never carry a `published` date from a probe report, a URL path or a CMS upload folder into an acquisition line as though the document had said it. And it does not establish that the document is still the **operative** one. Both checks belong at **ingest, with the text in hand** (`INGEST.md` steps 3 and 2b); where a fetched document turns out to be superseded, the acquisition is satisfied by its successor with the substitution stated on the page.

**Where a probe finds a document, it also records what the document does not settle.** A decree that vests a power but publishes no list under it is an acquisition *and* leaves the list an absence; both go on the record, or the acquisition quietly overstates itself.

---
