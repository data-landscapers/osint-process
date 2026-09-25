<!-- reader: cc; type: spec -->
# operations.md — page hygiene, dead-link triage, querying, lint, the standing whitelist

Split out of `reference.md`; section numbers are kept so a `§N` reference resolves unchanged. `CLAUDE.md` holds the principles and wins where the two disagree.

---

## 8. Page hygiene and scaling

The corpus can grow without bound; a single *operation* cannot. Each ingest touches a small local working set, so synthesis pages stay roughly constant-sized and linear growth lands in `raw/` and source pages.

**Word figures are diagnostic prompts, not hard caps.**

| Figure | Meaning |
|---|---|
| a few hundred – **~1,500 words** | target range for entity / concept / place pages |
| **~2,500 words** | stop and **classify** — not a ceiling a genuine bounded synthesis can't exceed |

Crossing ~2,500 means asking **which of three flavours** the length is:

- **Append-log** (chronology has accreted) → trim back to synthesis; the dates live in `sources` and git.
- **Verbose** (lean content, wordy prose) → tighten.
- **Matrix** (lean content that is structurally N repeating cells — a concept page carrying one block per country) → **extract intersections**. A tighten won't help; the page is a concept plus N cells wearing one filename. **First confirm it is genuinely matrix-shaped:** the length must be structural repetition — separable per-place (or per-entity) blocks — not a thematic argument with place detail woven through. Extract the former; leave the latter. Splitting a thematic page shreds its through-line — when in doubt, don't.

A page may be over threshold and the right action be "leave it": a dense, already-lean synthesis that doesn't decompose into cells is allowed to be long.

**Extraction obeys a materiality bar.** Size decides *whether to look*; it never decides *what to extract*. When splitting a matrix page, a `{place}--{topic}` (or `{entity}--{place}`) intersection is created **only for cells that stand on their own** — concretely:

- roughly **≥120 words** of substance, **or**
- **≥2 cited sources**, **or**
- **≥3 distinct developments/points**.

Cells below that bar stay **on the parent as a single indexed one-line entry each**. The parent then becomes an index: full links out to the material cells, terse one-liners for the long tail. No thin stubs minted just to hit a word count.

**Keep indexes greppable.** The faceted indexes grow with the whole corpus and are read often. If one gets large, **shard it** (by region, or by entity type) so CC reads a section, not the whole file.

**Batch size.** A batch touching dozens of pages is the heaviest single operation. Prefer smaller ingest batches.

Trimming and splitting are safe: git and the source pages hold the detail, so refactoring a page loses nothing.

---

## 9. Dead-link triage

Dead links are triaged, not blanket-fixed — a dead link is often a signal, not an error. Four outcomes, applied by rule — **but an entity slug never reaches this table at all**: `check_links` in `scripts/lint-deterministic.py` whitelists any `[[target]]` that appears anywhere as an `entities:` tag value, the same way it whitelists topic slugs and the retired lens values below, so a dead link to an entity is never read as a page to mint — however many referrers it carries.

| Referrers | Action |
|---|---|
| whitelisted | **Intentionally dead → ignore** |
| **≥10** | **Wanted page → create** it from the referencing material |
| **3–9** | **Middle band** → create if there is enough real material for a genuine page; otherwise leave and list in the digest. Lean toward creating where material exists |
| **1–2** | **Stray → fix or delete** — typo, curly/straight-apostrophe mismatch, or renamed target: repair the link or remove it |

**Whitelist of intentionally-dead links** — controlled-vocabulary codes that are tags rather than pages, meant to have no page, and "dead" forever by design:

- **entity slugs** — any `[[target]]` matching a value in some source's `entities:` list, computed live from the corpus every run, not a fixed list here. There are no entity pages; the tag is a terminal state, not a page deferred (`CLAUDE.md` → *Entities*).
- **`sovereignty`**, **`colonialism`** — the retired lens values (`facets.md` §1, retired 2026-09-08). They are no longer a facet and no longer written anywhere, but the words remain wikilinked in legacy body prose and have no page and are never going to get one. **Write the word, or name the concept page that actually carries the argument.** The existing ones are left alone — never cleared in passing. **This entry outlives the facet and has to**: `lens:` was cleared from the whole corpus on 2026-09-20 (`schemas.md` §4), but lint #4 whitelists these two targets from `LENS_VALUES`, a constant rather than the frontmatter, and the words are still wikilinked in body prose. Delete the constant with the retired check-#2 clause and every one of those links becomes a §9 dead-link finding.
- taxonomy slugs used purely as tags
- **Link syntax quoted inside a procedure or spec file is not a link.** `[[a], [b], [c]]` in `facets.md` §1's bracket convention, `[[…companion]]` in the domestic-state driver, `[[link]]`, `[[...]]` and the worked slugs in the examples above are *showing the form*, not citing a page. **The dead-link check skips the `wiki/` specs (`reference.md` and the files it indexes), `finance-record-spec.md`, `finance-load-domestic-state.md` and any other file whose job is to document the convention** — the set is `LINK_CHECK_SKIP` in `scripts/vault_lib.py` — and skips `log.md`, a dated record of what was true when written.

Maintain the whitelist so these stop surfacing as lint noise.

---

## 10. Querying

Querying is read-only (`CLAUDE.md` → *Working the base*): ask in session; CC greps the wiki, opens the relevant compiled pages, and answers. **Nothing is written to disk.**

**The saved-query workspace is retired** *(Bill, 2026-09-08 — `queries/` deleted, last used 2026-07-24; git holds it)*. A question worth keeping is answered on the page it bears on, dated, where the next reader will actually meet it — a parallel folder of question-and-answer files is a second store of record that nothing drains and no pass reads.

**An answer given in session is a derived view, never a source**: do-not-ingest, never written into `raw/`, never used to corroborate a wiki claim, and stale the moment the base grows. Where it rests on thin or single-sourced coverage, say so with the answer. The base is canonical.

**Reconciling a contradiction is external research, not a query** — its brief lives with the `reviews/contradictions/` item.

---

## 11. Lint

**The lint pass is [`LINT.md`](../LINT.md)**, triggered by "full lint", a first-class pass alongside reconcile and acquire. Its numbered checks keep their numbers there, so a "§11" reference resolves. This heading is the pointer; the thresholds and schemas the checks enforce live in the specs — `layout.md` §3 filenames, `schemas.md` §4 frontmatter, §8 page hygiene and scaling, §9 dead-link triage — and the dedup rules are `CLAUDE.md` → *Duplicates*.

---

## 11a. Standing whitelist — one-command actions CC may take unattended

**This section overrides a process file's "never automatic" for the listed commands only.** Where `HUB-COMPILE.md` or any other driver says a command is never run unattended, that remains true unless the command is on this list. A process file that says *"run it per place and read the diff"* is written for a human reader; registering work CC could have actioned converts CC's judgement into Bill's backlog (`CLAUDE.md` → *How CC works*), and this list is what stops that.

**The bar — all four.** A command earns a place here only if it is:

- **One command, no arguments CC has to invent** beyond an obvious scope (a place code, a file path already identified);
- **Deterministic** — same inputs, same output, no model judgement inside it;
- **Fully reversible by `git revert`** — it touches tracked files only, and never `raw/` bodies, which are immutable;
- **Diff-readable** — its whole effect can be checked by reading the diff it produces, in one sitting.

**The conditions, every time.** CC runs it, **reads the diff before committing**, commits it alone in a commit naming the command, and logs one line under **Decisions** with what it ran and what changed. **If the diff is not what the command promised, revert and raise it** — the authorisation is to run the command, not to accept its output.

| Command | Scope it may be run on | What it does |
|---|---|---|
| `python scripts/compile-hubs.py --init {ISO3}` | a place hub reporting `no-markers` | Inserts the compile markers and moves existing bullets into `### Before <date>`, verbatim. Content-moving, not content-writing. |

**Adding a row needs Bill.** CC may propose one — in the log, with the four bar tests answered — but never write it in itself. That is the whole point of a whitelist.

A pass closes on the one line defined in `STATUS.md`, per `CLAUDE.md` → *Reporting*; nothing here adds to it.
