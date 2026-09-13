# reference.md — directory of the shared specs

`CLAUDE.md` holds the principles and is what CC reasons from. The operational detail it demoted — vocabularies, layout, schemas, intake mechanics, hygiene thresholds — lives in five spec files, each keeping the section numbers it had when this was one file, so a `§N` reference resolves by filename alone. Look things up there; decide from `CLAUDE.md`, which wins where they disagree.

| File | Sections | Holds |
|---|---|---|
| [facets.md](facets.md) | §1 | place, subject and entity vocabularies (lens retired 2026-09-08); blocs are entities; finance subject vs deal entity; the `[[a], [b]]` link-list convention |
| [layout.md](layout.md) | §2–3 | folder structure, who owns each lookup table, filename rules and date padding |
| [schemas.md](schemas.md) | §4–5a | frontmatter schemas for source, concept, place and intersection pages; `last_reviewed`; entities are tags only; admissibility detail |
| [intake.md](intake.md) | §6–7a | draining `new/`, the two run logs, sweep intake and the containment boundary, the gap probe |
| [operations.md](operations.md) | §8–11a | page hygiene and scaling, dead-link triage, querying, lint, the standing whitelist |
