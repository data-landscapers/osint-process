# osint-process

The procedures, scripts and vocabularies that collect and classify the evidence behind **[Corpus](https://corpus.data-landscapers.io/)** — reports and datasets on digital transformation, digital public infrastructure and data governance across Africa.

Corpus is built by two repositories. The collection repository searches, fetches, screens, classifies and stores public documents; it is private because it holds their full text. The publishing repository, [data-landscapers/corpus](https://github.com/data-landscapers/corpus), turns the resulting metadata into the site and is public. This repository is the process layer of the private one, published so that anyone can read how the evidence base is built without reading the base.

For the method in plain language, start with the site: [Methodology](https://corpus.data-landscapers.io/methodology/), [Document lifecycle](https://corpus.data-landscapers.io/methodology/document-lifecycle/) and [Process inventory](https://corpus.data-landscapers.io/methodology/process-inventory/). This repository is the source those pages describe.

## What is here

| Path | What it holds |
| --- | --- |
| `*.md` at the root | The procedures. Each is an instruction document Claude Code reads and follows: the sweeps, `INGEST`, `RECONCILE`, `ACQUIRE`, `LINT`, `PRUNE`, `RULES`. `SWEEP-CYCLE.md` is the nightly run and the place to start; `CLAUDE.md` holds the standing rules. |
| `scripts/` | The Python that checks, indexes and compiles what the procedures produce. |
| `lookups/` | The controlled vocabularies: countries, taxonomy, deal and financier maps, the FX table, and the source lists each sweep works. |
| `wiki/` | The specifications the compiled pages are written to: schemas, facets, the capture rule, the origin screen, the finance record spec. |
| `documentation/` | Method notes, including the budget-extraction records. |
| `.githooks/`, `.claude/settings.json` | Repository hooks and agent settings. |
| `PROCESS-FROM` | The private commit this copy was exported from, and when. |

## What is not here

- **`raw/`** — the full text of every document. Withheld for copyright.
- **The compiled wiki** — the country, topic and intersection pages. They are the product; Corpus publishes them as reports.
- **Logs and review queues** — in-flight operational state.
- **History.** This repository starts at its first export. The private repository's earlier commits are not published: they carry the names and paths of held documents.

## How it is kept current

This is a one-way copy. At the close of each nightly collection cycle, `scripts/export-process-mirror.py` copies an allowlist of files from the private repository and pushes them here, refusing if a file carries a long block quote (a possible source body) or a secret. Nothing here is edited by hand.

**So this repository takes no pull requests** — a change merged here would be overwritten by the next export. Corrections and questions go to [info@data-landscapers.io](mailto:info@data-landscapers.io).

## Running it

It is not packaged to run elsewhere. The files name the machines and paths they run on (`C:\OSINT`, `C:\CORPUS`, mapped drives), and the procedures assume a vault of documents that is not here. Read it as a specification; to reuse it, supply your own paths and corpus.

## Licence

[MIT](LICENSE). Corpus's reports and datasets are published separately under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
