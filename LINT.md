# LINT.md — the lint pass

Trigger: **"full lint"** (also **"run lint"**). Hygiene checks #1–#38 over the vault, in two cadences — **"quick lint"** at every cycle close and **"full lint"** at the Day B night's close (`SWEEP-CYCLE.md` → *The Day B night*), either also callable on demand. **`update wiki` does not lint** — the caller does.

Procedure only: §3 is `layout.md`, §4 `schemas.md`, §8–9 `operations.md`; dedup is `CLAUDE.md` → *Duplicates*. **Check numbers are permanent handles** — never renumber, never reuse; the order below is the run order, not the numeric order.

## Lint acts and logs. It does not report.

Every check has one correct action; lint takes it, in git, and records a count. It surfaces to Bill **one thing only**: a genuine contradiction, filed to `reviews/contradictions/open/`. **Never a to-do list.** A wrong auto-fix is a revert.

## Cadence

**The cadence test is whether the work scales with the night's catch.** **nightly** — quick lint runs the check's script and applies only fixes needing no reading of page content. **nightly (new records)** — **#6, #4, #5, #34, #14, #20, #7**: quick lint also reads and judges, over the `raw/` files this run admitted only (`git diff --name-only --diff-filter=A <ingest-commit>^ <ingest-commit> -- raw/`; on demand, what the caller names); **#6 runs whole-corpus every time**. **batched** — **#8, #9, #23, #13, #17 and #3's fix half**: full lint only, whole-vault work that costs the same at any cadence; a whole-vault check moves to nightly once it carries a looked-and-left stamp (as #6 does in `origin_status`). A check finding nothing reports a zero.

## Running it

**Step zero: `python scripts/lint-deterministic.py`** — the mechanical checks, whole vault, against `lookups/frontmatter-schema.json`; reports, never edits; `--check N` for one check, `--all` adds the soft findings. **Scripted** below means a script finds it; the rest are judged. Order dependencies: **#12 before #4** (a truncated slug reads as dead), **#15 before #7** (the tiebreak trusts `body_completeness`), **#6 before #17** (#6 writes the `drop-list.csv` rows #17 checks).

## The checks

**39. Artefact md5 collisions** — surface, scripted, nightly. `python scripts/lint-deterministic.py --check 39`. Two artefacts with one md5 and no documented reason. A document served from two routes defeats both of the gates that exist — ingest's tier-3 dedup reads titles and ledes, `lookups/raw-url-index.csv` reads normalised URLs — and both companion pages then read as legitimate records to every other check (job 106, found by accident nine days late). The check reads `lookups/artefact-md5-index.csv`, which `artefact-md5-index.py --append` keeps current at `INGEST.md` step 11; it never rebuilds, because hashing 2,249 files takes minutes, and it reports a row count that has fallen behind the trees, since an index nothing appends to is a check that has stopped looking. **A collision is a finding, not a defect.** Three of the four shapes are legitimate: one document evidencing two different records (a report and its launch notice, two loans on one project phase), a budget document held in both `budget-archive/` and `raw/`, a table reprinted in the next year's document. Ruling one legitimate means a row with its reason in `lookups/artefact-md5-allowed.csv` — nine are there from 2026-09-20 — because a check that reports the same nine every night is one that gets ignored along with a real one. The retirement call itself is `CLAUDE.md` → *Duplicates* and never automatic.

**37. Process mirror current** — surface, scripted, nightly. `python scripts/export-process-mirror.py --check`: a published file that differs between the public mirror's `PROCESS-FROM` and `origin/master` means the last night's export did not land. Never auto-fix — the export is the close's act and a refusal is a ruling (`SWEEP-CYCLE.md` → *The process mirror*). Exit 2 is GitHub unreachable, reported and not a defect.

**36. Entity slugs with no referent** — surface, scripted, nightly. *(Filed as #30 on 2026-08-23 against a handle taken on 2026-08-21; renumbered 2026-09-08 — a handle is never reused.)* A `wiki/` `entities:` slug no `raw/` source tags: typo or stale registration → fix; a real untagged actor → allowed. Soft; `lookups/entity-slugs-ruled.csv` holds prior rulings.

**1. Schema integrity** — auto-fix, scripted, nightly. Fill missing required frontmatter from what the page carries; where it cannot be inferred, surface — never guess.

**35. Hard-wrapped paragraphs** — auto-fix, scripted, nightly. `python scripts/reflow-md.py` over `wiki/`, `reviews/`, `logs/` (`--check` reports without writing). One line per paragraph is `CLAUDE.md` → *Writing*: a hand-wrapped paragraph diffs as a rewritten paragraph for a one-word change. Refuses `raw/` (immutable, verbatim) and a named set of `logs/` append-only ledgers, where one line is one record and never a paragraph — nothing here needs reading before applying; the fix is entirely mechanical.

**12. Link-list convention** — auto-fix, scripted, nightly. Normalise `sources:` / `entities:` to `[[a], [b]]`.

**2. Vocabulary** — auto-fix, scripted, nightly. Correct a `topics` or place slug to the controlled value; a genuinely new value → surface.

**11. Missing date prefix, or wrong shard** — auto-fix, scripted, nightly. Rename to `YYYY-MM-DD` prefix, updating links; unestablished → `date_source: proxy` at best precision (§3). Shard is prefix (§3): a corrected date moves the file too.

**4. Orphans & dead links** — auto-fix, scripted, nightly. Index absent pages; rewire or retire broken `[[links]]` per §9's bands. Entity slugs are whitelisted (§9); never touch the intentional-dead whitelist. Skip convention-documenting files and dated logs.

**5. Untagged sources** — auto-fix, nightly (new records). Tag per `CLAUDE.md` → *Entities*; untagged mentions and sparse `entities` on thematic sources are not defects.

**38. De-accented Romance titles** — surface, scripted, nightly (new records). `python scripts/lint-deterministic.py --check 38`. A `raw/` source whose `title:` carries no accented character **and** a spelling neither Portuguese nor French uses — a `-cao`/`-coes` ending, `n.o`, `Politica`, `Seguranca`, `Tecnico`, `donnees`, `numerique` — is a title a staging lane transliterated (job 81). **Never auto-fix and never spell it yourself**: refetch from the source's own heading and correct `title:` only, because a reconstructed title is a fabricated one on a gazette citation. The accent test alone over-reports by a quarter, which is why the flattened spelling is required with it. Sources ingested before 2026-09-17 are one soft line — the standing backlog, counted, never a defect. Two records are permanently exempt in the script (`DEACCENT_EXEMPT`): their own sources cannot state their titles.

**34. Catalogue hero** — auto-fix, scripted detect, nightly (new records). `python scripts/lint-deterministic.py --check 34`. A post-contract `raw/` source with no `catalogue_hero`, or one over 120 characters, running to two lines, carrying markdown, ending in a full stop or repeating its own title: **write it or rewrite it** per `schemas.md` §4, with `scripts/catalogue-hero-set.py` for anything past a handful. Nothing here is surfaced — the record is in the public catalogue either way, so there is no refusal form to record and no judgment for Bill to make. **Pre-contract sources carry none by construction**: they are counted as one soft line and are a backfill process's work, never this check's.

**32. Place bar** — surface, scripted, nightly (new records). `python scripts/lint-scope.py --since <the run's date>`, never whole-vault. **xgl** is reported, never a defect (`facets.md` §1 → PLACE); **unaccounted** has floor 0 — every one a leak to fix.

**15. `body_completeness` backfill** — auto-resolve, scripted, nightly. Set from the stored body by marker-matching; ambiguous → inspect or leave blank. Never set `full` on a body no check has passed over.

**7. Duplicates** — auto-fix, nightly (new records). `scripts/lint-duplicate-deals.py` (finance) and `scripts/lint-duplicate-sources.py` (narrative) cluster on **event + entities + date**; candidates, never verdicts; adjudications to `reviews/source-duplicate-decisions.csv`. Retire only where unique figures and parties are empty or chrome; resolve per `CLAUDE.md` → *Duplicates*; neither better → keep the first by filename. Rewire `sources:` in `wiki/` **and `raw/`**, `raw-url-index.py --remove` the retired URL, name the keeper in `survivor`, log kept + pruned. Differing payloads → keep both, or #9.

**14. `url:` quality** — auto-fix, nightly (new records). A bare-domain, blank or missing `url:` needs the document URL: own `source:`-type key first, then title, document ID/DOI, publisher search, archive, byte-compare of a held artefact — no attempt limit. Verify title and date; a 200 is not proof; never construct from a pattern. A homepage capture with no dated event is not a defect. Exhausted → `url unrecovered as of YYYY-MM-DD`. Never edit `published` (#3's).

**16. Finance record keys** — auto-fix + defect list, nightly (defects → batched); finance records only. `scripts/lint-finance-slugs.py` (exits non-zero on a financier defect — an ingest gate). Fix the mechanical (slug from `entities[0]`, `ALIASES`); surface the rest as a defect list drained like a contradiction. `recipient_slug` drift is soft.

**21. Machine-record audit** — auto-fix, surface on a rise, nightly (a rise → batched). `python scripts/audit-machine-records.py --persist`; class 2 (empty `entities: []`) never gates. Fix a rise from `logs/machine-record-audit-defects.csv`; surface only what cannot be fixed.

**3. Freshness** — auto-resolve, partly scripted; nightly detect, batched fix. `last_reviewed` over **90 days**; newest source over **2 years** old while the topic has sources under **6 months** old; undated time-varying figures; money breaking `CLAUDE.md` → *Currency*. Date, rephrase, or write the dated absence; re-stamp `last_reviewed`. A figure inherits its bullet's date, except a one-line index bullet. Never invent a rate.

**20. Unsourced lede figures** — auto-resolve, nightly (new records). `python scripts/lint-unsourced-figures.py`. A `[[topic]]` or `[[entity]]` link is not provenance. Grep `raw/` and cite what is held; else write the dated absence and drop the figure.

**8. Page bloat** — auto-resolve, **scripted from 2026-09-20**, batched. `python scripts/lint-deterministic.py --check 8 --all`. Over §8's ~2,500-word classify line, or an append-log: trim or split per `CLAUDE.md` → *Structure*; shard an oversized index. Hub *Recent developments* exempt. Detect by where the date sits; measure per section. **This entry described a check that did not exist** (repaired on sight, `RULES.md`: a wrong process file is not a rules-pass question). Until 2026-09-20 `--check 8` answered `no check #8`, every count was measured ad hoc — 199 pages on 2026-08-30, 295 on 09-05, 342 on 09-16, 394 on 09-17, each disagreeing with the last — and **the hub exemption above was specified here and applied nowhere**, so `places/NGA.md` was counted at 56,296 words when 51,665 of them are that one compiled block and 60 hubs sat permanently in a count nothing could clear. **Three things the script settles.** Every finding is **soft and always will be**: §8 says word figures are diagnostic prompts, a page over the line may correctly be left alone, so this reports where to look and never gates a pass. It reports **`concepts/`, `places/` and `intersections/` as three counts**, because they have three remedies — concept-page heads are housekeeping jobs 97 and 99's, a hub is a derived view read on its hand-written sections only, and the intersections are the growing population. And **links, sources and a `Length` note are exempt as furniture, a dated *Record not held* is not** — an absence stated with a date is a finding, not padding. The shape test the script applies, and the `## Length — reviewed` convention it reads, are in its own docstring pending the rules pass.

**13. Quarantine leaks** — auto-fix, batched. A `wiki/` page citing `reviews/contradictions/research/` or a `DO-NOT-INGEST` file: rewire to the ingested primary or remove. Prose *about* the folders is not a defect.

**6. Inadmissible sources** — auto-resolve, nightly (new records). Origin failing `CLAUDE.md` → *The material*, or re-rendering the wiki: demote to a lead, or strike and mark for re-sourcing. A domain origin: screen against `wiki/origin-screen.md`, write its `drop` / `watch` row to `logs/drop-list.csv` **in the same edit**; a `NOVEL` origin showing one of the five shapes → *After a promotion to `drop`*. No hold to drain. **Scripted half**: `lint-deterministic.py` reports every `raw/` record whose `url:` host sits on a `drop` domain, and flags an `origin_status: cleared` stamp that predates its own domain's adjudication — the promoting session's residue, which nothing asked for until housekeeping 104 found four records surviving three promotions. It matches the full host, never the registrable domain, so one tenant of a shared host does not condemn another. The origins themselves stay judged.

**17. Sweeps call the origin screen** — auto-fix, batched. Every root `*SWEEP*.md` and `wiki/index.md` → *Sweeps* file must reference `wiki/origin-screen.md`; insert the standard call where missing. Every `drop-list.csv` row has `status` `drop`/`watch`; every #6 domain has its row.

**40. A record no parser can read** — auto-fix, nightly. `lint-deterministic.py` reads every `raw/*.md` **as bytes** and asserts its frontmatter block matches the same regex every reader in the vault uses. A record whose closing `---` carries a doubled CR, or has lost its newline, reads as having *no* frontmatter rather than as malformed — not an orphan, not bad YAML, not a missing key — so every text-mode check here passes over it silently. Three Somali records sat unread until `catalogue-hero-set.py` refused one outright (housekeeping 118). **Hard finding**: a record nothing can read is worse than a record with a bad value in it. A doubled CR inside the body is the soft half of the same capture fault. **The repair is a terminator fix and never a re-capture** — assert that stripping every CR from both sides leaves the bytes identical, then write.

**22. Acquisition names a held document** — auto-fix, nightly. `python scripts/lint-acquisition-held.py` (also `ACQUIRE.md` step 0); apply what it marks **STRIKE**, read and rule on what it marks **CANDIDATE**, and never the other way round — a candidate is a URL match whose held record is a different document, or a URL-less line matched on name, instrument, year and place. `excerpt` on a structured extract or abstract is the complete record (§4). `--fix-markers` repairs an open line whose missing `- ` hides it from the status count.

**27. `raw/` URL index matches `raw/`** — rebuild on mismatch, scripted, nightly. `python scripts/raw-url-index.py --lint`; mismatch → `--rebuild`, never an investigation. A retire or replace removes its row in the same edit (#7).

**30. Every adjudication in `sweep-url_log.md` has a record** — surface, scripted, nightly. `python scripts/lint-url-log.py`. Never auto-fix — an orphaned admission may be out-of-scope, held elsewhere, or a loss, each a different line.

**18. Register pruning** — auto-fix, nightly. Run `PRUNE.md`; report what it deleted; surface a stale next-number counter. No handle is ever used twice.

**29. The hand-stamped log** — surface, scripted, nightly. `python scripts/log-append.py --check` (UTC per `STATUS.md`; position unchecked below `--tolerance`). Never auto-fix; `scripts/log-append.py` is the writer. The collection stamp's own future-value defect is refused at the write instead (`cycle-manifest.py --stamp`), so there is nothing left here to check for it.

**19. Mirror HEAD matches local HEAD** — surface, scripted, nightly. `python scripts/lint-mirror-head.py`; `O:\` is CORPUS's read path, and the mirror's `cycle-manifest.json` must name that same commit — the right tree with the wrong account of it is the same silent publication, one level in. Never gating; `--gate` exits 1 for a close step that wants it.

**33. Per-item effort cap** — surface, scripted, nightly. `python scripts/effort-cap.py`. An item named in three or more of the run's `log.md` entries: drop it, or write what is not established onto the page, dated — never a fourth pass.

**24. Register caps** — auto-fix, scripted, nightly. `post-run-notes.md` against `CLAUDE.md` → *Reporting*: truncate to claim and question; `[FYI]` → `log.md` line, `[FETCH]` → `X:\fetch-list.md`, `[ACT]` → act and log. Over the open cap, do not write — take the conservative option, log it, say so on the close line. `X:\notes-for-osint.md` / `X:\notes-for-corpus.md`: soft, worst three listed, nothing trimmed. **The share's conventions live once, in `X:\README.md` → *Conventions***: a preamble over 250 words to the boundary named per file — which is the file's **first substantive section**, a table the file is required to keep current being substance and not preamble — and any convention restated outside README, are both failures — hard on the files OSINT owns, soft on the other side's, because a check that fails on work the run may not edit is one that gets skipped. README dropping a rule the check watches is itself hard: a check that can disarm itself is not a check. CORPUS asserts the same from `scripts/lint-preambles.py`. **And every open note names the output it bears on**: one `Affects:` line — an artefact, work already commissioned cited by number, or a published thing named in words — present, not a way of saying *nothing*, and naming something a reader can reach. Whether it is *true* is the writer's; a check that adjudicated that would pass everything or argue with its writer. Hard on `notes-for-corpus.md`, OSINT's outbox, soft on the inbox; CORPUS's `scripts/lint-notes.py` is the mirror.

**25. `CLAUDE.md` length** — surface, scripted, nightly. `CLAUDE_MD_CAP` (123), that file only. Never auto-fix; raising the cap is deliberate. **And the freeze's own end date**: a standing rule read past the date it names is read as live and is not, so a lapsed `frozen until YYYY-MM-DD` is a hard finding — renew the paragraph with a new date or delete it.

**31. `pdftotext` carries `-enc UTF-8`** — surface, scripted, nightly. `python scripts/lint-pdftotext-enc.py`. A command is a finding, a name is not (`BUDGET-EXTRACT.md` §1 covers names); `subprocess` lists count; `raw/`, `sweep/`, `logs/`, `reviews/`, `wiki/` never read.

**26. Output freshness** — surface, scripted, nightly. `python scripts/lint-output-freshness.py`; `outputs\budgets\` excluded while the budget layer is suspended. Never fix — `FINANCE-COMPILE` is the fix.

**9. Contradictions** — surface, batched. File any conflict uncovered — sources disagreeing, a duplicate-cluster payload mismatch — to `reviews/contradictions/open/`; report the count.

**23. Region place code** — surface, scripted, batched (judgment). Three or more countries of one region, no `X__` code → candidate (`facets.md` §1 → PLACE). Soft: a cross-border framework earns it, one operator in three markets does not. Rule on the new ones only.

**28. Deal-record vocabulary** — surface, scripted, nightly. Controlled fields against `lookups/deal-vocabs.csv`, plus the absent row (`DEAL-VOCAB.md`). Never auto-fix — a map row or a ruling.

**10. Stranded queue items** — surface, scripted, nightly. Anything left in `new/` after an ingest is unfinished. Lint does not ingest it; report the count.

## Close

Close on the line `STATUS.md` defines — the standing count line — plus one line per check that acted. Nothing else reaches Bill; equal duplicates are settled by #7, not surfaced.
