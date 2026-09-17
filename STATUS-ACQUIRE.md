# STATUS-ACQUIRE.md — the status-report acquisition pass

Trigger: **"run status acquire"**, or **"run status acquire for <country>"**. One country per run.

CORPUS builds a country status report over sources OSINT does not hold — see [AGO](https://corpus.data-landscapers.io/reports/AGO/AGO-status.html) for the shape. `X:\africa-acquire.csv` is the list those reports were built from: one row per source CORPUS cited and this vault has no capture of. This pass closes that gap a country at a time — fetch the rows, stage them into `new/`, drain `new/` through `update wiki backfill`, move the rows to `X:\acquire-done.csv`.

**It is not the acquisitions queue.** `reviews/acquisitions.md` is OSINT's own fetch list and `ACQUIRE.md` drains it; this list is CORPUS's, lives on `X:\`, and never touches that register or its counts. It borrows `ACQUIRE.md`'s discipline: **one automated attempt per row, then the row is resolved**, and the archive is asked before a document is called gone.

Governing rules: `CLAUDE.md` (admissibility, currency, duplicates), `wiki/layout.md` (filing) and `wiki/schemas.md` (schemas). This file is only the loop.

---

## 0. Announce and select

Print the banner and note the time (`STATUS.md` → *Announce which process is running*):

```
▶ running: status acquire — CAF (27 rows)
```

`python scripts/status-acquire.py --list` gives the outstanding rows per ISO3. **The country Bill named, or — with none named — the first ISO3 alphabetically still carrying rows.** No cherry-picking: the file drains in order.

`python scripts/status-acquire.py --select <ISO3>` writes the run manifest to `sweep/status-acquire/<ISO3>.csv` — the country's rows verbatim, plus the `status` and `notes` columns this pass fills — and prints them. **A row whose URL is already a `raw/` capture or already a rejection is pre-marked `held` / `rejected` and is never fetched**: the same check as `ACQUIRE.md` step 0 and lint #22, run once for the whole country against `lookups/raw-url-index.csv` and `lookups/rejected-urls.csv`.

That script is the **only** writer of `X:\africa-acquire.csv`. CORPUS writes to that file too — never sed it, never hand-edit it, and never open it for anything but reading.

## 1. Screen the rows before fetching

Cheap mechanical drops, all decided from the row alone, no fetch spent:

- **A drop-listed origin** — `python scripts/origin-screen.py` over the run's URLs (`wiki/origin-screen.md`). A listed publisher is not a screened one.
- **A generic global index or tool landing page with no dated document behind it** — `odin.opendatawatch.com/data`, the AWS regions reference, a World Bank indicator widget. `CLAUDE.md` → *Currency*: **reference studies are cited, not absorbed**, and a landing page has no body to capture and no event to date. Where the row names the study's actual publication (the ITU GCI 2024 PDF, an IIAG country profile) that is a document and it is fetched.
- **A landing page dropped here is dropped for every country** — register it once with `python scripts/raw-url-index.py --reject not-a-document <url>` and `--select` pre-marks it `rejected` in every other manifest. A decision taken once is taken once; likewise the first country to stage a global study makes it `held` for the rest, off `raw-url-index.csv`.
- **A row already in the manifest under a second URL** — the same document behind a publisher page and a bitstream link. Fetch the one that yields the document; drop the other as `duplicate-row`.

Mark each with its reason as you go:

```
printf '%s\n' <url> ... | python scripts/status-acquire.py --mark <ISO3> dropped --note "<reason>"
```

Everything else goes to the fetch. **Admissibility is ingest's call, not this pass's** — scope, duplicates and dating are adjudicated at the gate, on the document, never pre-judged from a CSV row.

## 2. Fetch — one attempt each, in batches

**One sub-agent per batch of ~8–10 rows, spawned by this session**, exactly as the content sweeps do it (`SWEEP-NEWSPAPERS.md` → *Delegation*): a country's worth of fetched bodies will not fit in one context. Each batch stages its hits into `new/` and returns **a tally and the outcome per URL** — nothing else; the bodies die with the agent. No sub-agent spawns another.

**Bake `wiki/capture-rule.md` into every batch agent's instructions.** Unattended agents refuse verbatim capture without it, and a refusal mid-batch is indistinguishable from a nil return.

The attempt, in the order the row needs (`ACQUIRE.md` step 1):

- a direct document URL — a PDF, a gazette, a project document → fetch it;
- an ordinary page → `web_fetch_exa`;
- a JS-rendered document library → **resolve the file URL, don't render the index**; the PDF an index points at almost always sits on a static path.

**A dead domain is not a dead document.** Inside the same one attempt, ask the Internet Archive before concluding a row is unfetchable — `http://archive.org/wayback/available?url=<url>`. A live 404 dates the absence, not the document. Before recording a host as unreachable, resolve it over DoH and retry with a second client (`capture-rule.md` carries both tests).

One real attempt. Do not loop, retry variants or hunt for mirrors.

**Staging.** Flat into `new/` as `new/YYYY-MM-DD-slug.md`, full verbatim body, frontmatter as a head-start for ingest:

| Field | From the row | Caveat |
|---|---|---|
| `url`, `publisher`, `title` | as given | the row's title is CORPUS's rendering; the document's own title wins |
| `published` | the row's `published` | **often year- or month-only — set `date_precision` to match, and the document's own date always wins.** The CSV date is the year CORPUS cited, not an event date |
| `places` | the row's `iso3` | validated at ingest; a global study cited for one country is `XGL`, not that country |
| `topics` | the row's `sub_section` | the CSV's values are live `taxonomy.md` slugs and carry through |
| `sweep_batch` | `status-acquire-<ISO3>-YYYY-MM-DD` | what a later grep finds this run by |
| `entities` | — | **leave blank.** `capture-rule.md` → *Look a controlled value up; never assert one* |

**Never write a frontmatter value the row does not carry.** A blank is a fact about what the fetch knew and ingest fills it; an invented slug is a defect ingest pays to correct.

## 3. Record every outcome

Every row leaves the queue carrying one of four statuses — there is no fifth state and nothing is parked:

| Status | Means |
|---|---|
| `staged` | fetched and sitting in `new/` for ingest to adjudicate |
| `held` | the vault already holds this URL (pre-marked at select) |
| `rejected` | already adjudicated and refused (pre-marked at select) |
| `dropped` | screened out at step 1, or the one attempt did not retrieve it — with the reason in `notes` |

```
printf '%s\n' <url> ... | python scripts/status-acquire.py --mark <ISO3> staged
```

**A `dropped` row that bears on a specific page earns one dated line on that page** recording that the document is not held (`CLAUDE.md` → *Working the base*). Where Bill could plainly get it by hand — a subscriber clip, a login — raise a post-run note **as well as** dropping the row, identifying the document exactly. The row still leaves the queue.

## 4. Drain, then close

**`update wiki backfill`.** The staged rows are ordinary candidates from here on: ingest screens, dedups and files them, Phase B writes the pages — **one iteration** (`UPDATE-WIKI.md` → *Lanes*), and the acquisitions and contradictions it raises wait for the nightly close. **The trigger carries the lane and this pass has no other way to open it**: everything staged here is a `status-acquire-` batch, which `INGEST.md`'s whitelist reads as backfill — already screened upstream, so a plain `update wiki` would pay the news lane's origin adjudication, tier-3 dedup and authored `hub_line` on every row of it. This pass files nothing to `raw/` itself and writes to no `wiki/` page.

Then, and only then:

```
python scripts/status-acquire.py --close <ISO3>
```

It refuses while any row is unmarked, naming them. It moves the country's rows out of `X:\africa-acquire.csv` into `X:\acquire-done.csv` with a `closed` date, and deletes the manifest. **Close after the drain, not before** — a run interrupted mid-fetch leaves the manifest and the CSV rows both in place, and re-running `--select` resumes from where it stopped.

## 5. Ending the pass

One line to `logs/log.md` via `scripts/log-append.py` — country, rows taken, staged / dropped / already-held:

`status acquire — CAF 27 rows: 21 staged, 4 dropped, 2 held; update wiki backfill drained new/`

Then the standing line:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

## Containment

The pass writes to `new/` (candidates), `sweep/status-acquire/` (its manifest), `logs/` (its own log lines and the origin screen's drop list), `lookups/rejected-urls.csv` (step 1's landing-page registrations) and the two CSVs on `X:\`, through `scripts/status-acquire.py` and nothing else. All but the rejection register sit inside the sweep boundary, so the check before the drain is `python scripts/assert-containment.py --stage sweep --allow-extra lookups/rejected-urls.csv` — step 1 mandates that write and a bare `--stage sweep` reports it as a breach. It never writes to `raw/` or to a `wiki/` page: `update wiki backfill` does that, under its own rules.

## Concurrency

One pass at a time, and no other CC session writing to the vault while it runs — it stages into the shared `new/` and then drains it. `X:\africa-acquire.csv` is shared with CORPUS, so a run that cannot complete closes the country it took rather than leaving rows checked out invisibly.
