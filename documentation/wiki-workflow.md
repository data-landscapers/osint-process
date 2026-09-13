---
type: doc
title: Wiki workflow — whole-project lifecycle
last_reviewed: 2026-07-29
---

# Data Landscapers wiki — whole-project workflow

How material moves through the system. **`wiki/index.md` → *Processes* is the
authoritative directory** of every runnable process and its trigger phrase; this file
is the picture of how they fit together, and defers to it wherever they disagree.

**Rewritten 2026-07-29 (housekeeping job 13).** The previous version drew the
architecture as it stood on 2026-07-16 and had become actively misleading: it showed a
`reviews/gaps.md` register and a `contradictions/research/` quarantine (both withdrawn),
no sweeps, no acquisitions pass, no finance or budget layer, no housekeeping register,
and a `CLAUDE.md` ratification gate that no longer works that way. A fresh session
reading it would have rebuilt retired structures. The rendered `wiki-workflow.html` and
`wiki-workflow.svg` alongside it were exports of that same dead diagram and were deleted
rather than regenerated — the mermaid block below renders natively in Obsidian, so the
source is the artefact and there is nothing to keep in sync.

> **Colour key.** Blue = store of record · green = human touchpoint · amber = a pass ·
> grey = a queue or register.

```mermaid
---
config:
  layout: elk
  theme: base
---
flowchart TB
  subgraph HUMAN["Human (Bill)"]
    direction TB
    H_clip["Curate sources<br/>(web clipper → new/)"]
    H_trig["Trigger a batch,<br/>a job or a query"]
    H_notes["Read post-run-notes ·<br/>strike what's absorbed"]
    H_rev["Skim log.md ·<br/>revert what's wrong"]
  end

  subgraph COLLECT["Collection — sweeps stage candidates"]
    SW_D["daily sweep<br/>(sweep-daily.csv)"]
    SW_O["off-list sweep<br/>(open web, 2 tracks)"]
    SW_C["content sweep<br/>(journals · newspapers · orgs)"]
    SW_F["domestic finance sweep<br/>(one country-year)"]
    ORIGIN{{"origin screen<br/>shared admissibility gate"}}
  end

  subgraph QUEUE["Queues — folder is state"]
    NEW["new/<br/>awaiting ingest"]
    NEWB["new-budget/{ISO3}/{FY}/<br/>awaiting budget extract"]
  end

  subgraph LOOP["update wiki — loops until all three queues are empty"]
    ING{{"ingest<br/>4 dispositions"}}
    RECON{{"reconcile"}}
    ACQ{{"acquire"}}
    LINT{{"full lint"}}
  end

  subgraph REG["reviews/ — the three queues + two registers"]
    COPEN["contradictions/open/"]
    ACQL["acquisitions.md<br/>automated fetches only"]
    HOUSE["housekeeping-jobs.md<br/>own session each"]
    NOTES["post-run-notes.md<br/>for Bill"]
  end

  subgraph BASE["The base"]
    RAW[("raw/ — sources of record<br/>immutable · date-prefixed")]
    PAGES["wiki/ — concepts · places<br/>entities · intersections"]
    LOG[("log.md · append-only")]
  end

  subgraph FIN["Finance layer"]
    BEX{{"budget extract"}}
    FREC[("finance records in raw/<br/>accreting store of record")]
    FCOMP{{"finance compile<br/>scoped to changed places"}}
    FPAGE["hub ## Financing +<br/>outputs/ CSV exports"]
  end

  subgraph OUT["Read-only"]
    QUERY["queries/ — reads the base,<br/>never writes to raw/"]
    STATUS["wiki status · repo status"]
    PUB["Draft → data-landscapers.com"]
  end

  H_clip --> NEW
  H_trig --> SW_D & SW_O & SW_C & SW_F
  SW_D & SW_O & SW_C --> ORIGIN --> NEW
  SW_F --> NEWB
  H_trig --> BEX
  NEWB --> BEX --> NEW

  NEW --> ING
  ING -->|"1 · admitted"| RAW
  ING -->|"2 · contradiction brief"| COPEN
  ING -->|"3 · acquisition line"| ACQL
  ING -->|"4 · out of scope / mined"| LOG
  RAW --> PAGES

  COPEN --> RECON
  RECON -->|"primaries"| NEW
  RECON -->|"resolution applied"| PAGES
  ACQL --> ACQ
  ACQ -->|"acquired → staged"| NEW
  ACQ -.->|"one attempt failed → dropped,<br/>absence stated dated"| PAGES
  ING --> LINT
  LINT --> PAGES
  LINT -.->|"conflict found"| COPEN

  ING -->|"finance item"| FREC
  FREC --> FCOMP --> FPAGE
  FPAGE --> PAGES

  PAGES --> LOG
  LOG --> H_rev
  NOTES --> H_notes
  HOUSE --> H_trig
  PAGES --> QUERY & PUB
  LOG --> STATUS

  classDef store fill:#e8f0fe,stroke:#3b6cb7,color:#12325c;
  classDef human fill:#eaf7ec,stroke:#2e7d32,color:#1b4620;
  classDef pass fill:#fff4e5,stroke:#e08e0b,color:#7a4f05;
  classDef queue fill:#f2f2f2,stroke:#8a8a8a,color:#333333;
  class RAW,LOG,FREC store;
  class H_clip,H_trig,H_notes,H_rev human;
  class ING,RECON,ACQ,LINT,BEX,FCOMP,ORIGIN pass;
  class NEW,NEWB,COPEN,ACQL,HOUSE,NOTES queue;
```

## Reading it

- **`new/` is the only door.** Clips, sweep candidates, extracted budget records,
  primaries surfaced by reconcile, documents fetched by acquire — everything enters
  through the same queue and the same ingest screen. Nothing is admitted any other way.
- **Folder is state.** An item's folder *is* its processing status, and moving it out of
  `new/` is the last step of processing it — so an interrupted run resumes cleanly rather
  than half-committing.
- **Ingest has four dispositions and no parking limbo**: admitted to `raw/`; turned into
  a contradiction brief; turned into an acquisition line; or deleted. An item that is not
  admitted still leaves the queue.
- **The three queues each have exactly one draining pass** — contradictions/reconcile,
  acquisitions/acquire, `new/`/ingest — and `update wiki` loops all three because each
  refills the others. Housekeeping is the fourth register and is deliberately *not* in
  that loop: it gets its own session.
- **Finance records are the one exception to `raw/` immutability.** They accrete — later
  reporting is folded into the existing record as a dated line rather than spawning a new
  page — and they carry no per-deal hub bullet, because their hub presence is compiled in
  aggregate by finance compile.
- **`queries/` reads and never writes back.** Results are derived snapshots; research
  output from reconcile earns its place only by being ingested as a primary.
- **Oversight is git-backed.** CC acts and logs rather than asking; `log.md` records what
  changed and what to revert, and `post-run-notes.md` carries the few things that need
  Bill rather than a pass.

*(Not drawn, to keep the map legible: git underpins every store; `CLAUDE.md` governs the
whole pipeline; `wiki/reference.md` holds the schemas and thresholds every pass applies;
and a piece published on data-landscapers.com can re-enter through `new/` as admissible
third-party analysis.)*
