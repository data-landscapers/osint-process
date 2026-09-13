---
title: Method notes — drafting the South Africa status, monthly and progress reports
compiled: 2026-08-03
audience: CC
status: notes, not a procedure — operationalise as you see fit
---

# Method notes: how the three South Africa reports were drafted

These are notes on method only. They cover how the three documents in `outputs/country-narratives/zaf/` were produced — what was read, in what order, what was delegated, what was verified, and what went wrong. Nothing here is about South Africa. Decide yourself which parts are worth turning into a procedure file, which belong in `wiki/reference.md` as shared vocabulary, and which are one-off scaffolding not worth keeping.

The three outputs were a **status report** (current state across the full taxonomy), a **monthly update** (events in one month) and a **progress report** (movement across twelve months). They are three different questions asked of the same base, and keeping them genuinely different turned out to be the main editorial problem.

## 1. Build the source index before writing anything

The single highest-value step, and the one to script first. The wiki cites sources as wikilinks; a report for a human reader needs resolvable URLs. Everything downstream depends on a reliable mapping between them.

```python
import os, re, json
out = {}
for root, dirs, files in os.walk('raw'):
    for f in files:
        if not f.endswith('.md'): continue
        text = open(os.path.join(root, f), encoding='utf-8', errors='replace').read(4000)
        m = re.search(r'^url:\s*(\S+)', text, re.M)
        if not m: continue
        pl = re.search(r'^places:\s*\[(.*?)\]', text, re.M)
        ti = re.search(r'^title:\s*(.*)$', text, re.M)
        out[f[:-3]] = {'url': m.group(1),
                       'places': pl.group(1) if pl else '',
                       'title': (ti.group(1) if ti else '').strip('"')}
json.dump(out, open('scratchpad/srcindex.json', 'w'))
```

Reading only the first 4,000 bytes of each file keeps this fast across the whole of `raw/` — 7,770 sources indexed in a few seconds, of which 541 carried ZAF. A country subset is a one-line filter on `places`.

Two things to know about the index. Sources without a `url:` field are silently absent, so a slug that fails to resolve is not necessarily a bad slug — one held PDF artefact had no URL and correctly produced no link. And the index is the authority: if a slug is not in it, the correct move is to say so and drop the claim, never to reconstruct a plausible URL.

## 2. Verify links mechanically, and do it every time

I invented one URL from memory while drafting the monthly update — a plausible MyBroadband article path with a wrong article number. It looked entirely correct. It was caught only because every link is checked against the index before the file is presented.

```python
import re, json
held = set(v['url'] for v in json.load(open('scratchpad/srcindex.json')).values())
text = open(target, encoding='utf-8').read()
for u in re.findall(r'\]\((https?://[^)]+)\)', text):
    if u not in held: print("NOT HELD:", u)
```

Treat this as non-optional. The failure mode is not laziness, it is that a URL synthesised from a remembered pattern is indistinguishable from a real one by inspection. Only the set-membership test catches it. Run it after every edit pass, not once at the end, because edits reintroduce links.

## 3. Word counting: decide what counts before you promise a limit

Naive `len(text.split())` over markdown counts URL path segments as words and inflates a 1,950-word document to 2,350. Strip links to their anchor text first:

```python
body = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', body)
```

Once inventory tables were introduced in iteration 3, the tables themselves ran to roughly 900 words against 1,400 of prose. I counted them separately and reported both, treating the limit as applying to prose on the argument that a table is reference matter rather than reading. That was a judgement call and it was flagged rather than buried. If word limits are going to be a standing constraint on report procedures, define once whether tables count — otherwise the same argument recurs every time.

## 4. Reading strategy: never open the hub whole

`wiki/places/ZAF.md` is 151KB. Reading it in full would have consumed most of the context budget for nothing. The structure is doing work, so use it:

- The **intersection pages** (`wiki/intersections/<country>--<slug>.md`) are the compiled current state. For a status report they are the primary input; twelve of them covered South Africa at roughly 195KB total.
- The hub's **Recent developments** is chronology. Useful for a monthly update, actively harmful for a status report, which is supposed to be state rather than log.
- The hub's **Active topics** section is the fastest map of which taxonomy slugs have substantive coverage and which are one-liners. Read it before deciding how to allocate effort.
- The hub's **Financing** block is the only compiled aggregate and has no source URL, because it is the wiki's own compilation. That needs stating in the text rather than linking.

Grep the headings first (`grep -n "^#"`) and read by line range. It costs one extra call and saves tens of thousands of tokens.

## 5. Delegation: one agent per theme, with an output contract

All three reports were built on parallel subagents — four for the status report, three for the progress report. The pattern that worked:

- **Partition by taxonomy branch**, not by file count. Each agent got three to five intersection pages plus the topic slugs it owned.
- **Give the agent the index path** and require it to resolve slugs itself. Passing back unresolved slugs for the parent to resolve wastes a round trip.
- **Specify the output shape exactly.** What I asked for was: a one-or-two-sentence maturity verdict, then six to ten dated facts each formatted `fact — [slug] URL`, then anything the wiki itself flags as unreconciled. Agents follow a format specification closely; vague requests come back as essays.
- **Instruct them to report missing data rather than fill it.** The phrasing that worked was "if a slug is missing from the index, say so rather than guessing a URL". One agent duly returned an unresolved slug with a note; another flagged a held PDF with no URL. Both were correct behaviours that a differently-worded prompt would have turned into fabrications.
- **Forbid web search explicitly.** "Do NOT search the web. Local files only." This project is output design, not collection, and an agent that helpfully fetches a fresh source has broken the containment boundary and put uningested material into a deliverable.

Cost, for planning purposes: the four status-report agents came to roughly 60–160k tokens each. Three parallel agents for the progress report were the practical ceiling before returns diminished.

For the progress report the contract was different and more demanding. Each agent returned a **movement ledger**: name, position at the start of the period with date and source, position at the end with date and source, a movement verdict from a closed list, and one sentence of concrete evidence. Requiring both ends to be dated is what surfaced the coverage cliff described in section 8 — an agent cannot pretend to a baseline it does not have if the format demands a date for it.

## 6. Cover the taxonomy, including where it is empty

The subject taxonomy has around 36 level-2 slugs. South Africa had intersection pages for twelve. A report claiming full taxonomy coverage cannot simply omit the other twenty-four.

I ran a dedicated agent whose only job was the residual topics, with an explicit instruction: *"Where the wiki genuinely holds little or nothing on a topic, SAY SO explicitly — a thin or absent evidence base is a finding I want reported, not padded over."* That produced the most useful single output of the exercise: digital literacy has no measurement at all, sectoral management information systems are close to unrecorded, three of the five geopolitics slugs have one substantive item each.

Reporting an absence is cheap, honest and actionable. Padding a thin topic to parity with a thick one is the failure mode to design against, and the prompt has to say so, because the default behaviour is to produce balanced-looking prose.

## 7. Closed vocabularies for status and movement

Iteration 3 introduced a five-value status scale — *Implemented, Piloting, In development, Planned, Discontinued* — plus a distinct marker, ***Not held***, for items where the base carries no reliable statement. The progress report needed a different, six-value scale for movement: *Advanced, Advanced/slipped, Stalled, Regressed, Closed, Baseline not held*.

Three observations. Firstly, the vocabularies must be defined in the document itself, immediately before first use; a reader cannot infer the boundary between "Planned" and "In development". Secondly, the not-held marker has to be visually distinct from the real status values, because its whole function is to be counted and chased. Thirdly, "Advanced, slipped" earned its place — without it, real progress against a moved deadline gets recorded either as success or as failure, and both are wrong.

If these reports become recurring, both vocabularies belong in `wiki/reference.md` rather than being restated per document, and the not-held rows should probably feed the acquisitions queue directly.

## 8. Check the shape of the base before promising a period comparison

Before writing the twelve-month report I counted sources per month:

```python
import collections
c = collections.Counter(k[:7] for k, v in index.items()
                        if 'ZAF' in v['places'] and '2025-08' <= k[:7] <= '2026-07')
```

The result: 29 sources for August–December 2025, against 348 for January–July 2026. That is not a minor imbalance, it is a cliff, and it means a large share of any "twelve-month movement" is really the arrival of coverage rather than change in the world.

Two consequences for method. The caveat has to be stated once, prominently, near the top — not scattered through the text and not omitted. And the not-held rows should be counted and the count published: seventeen of fifty-three rows had no opening baseline, which tells the reader exactly how much weight the comparison bears. **Run this count before agreeing to any period-comparison report.** If the earlier half of the window is thin, either narrow the window or say plainly that it is a shorter comparison wearing a longer label.

## 9. Handling contradictions without adjudicating them

The base holds several genuinely unreconciled pairs — a regulator's press figures against its own gazette, a utility's capacity statement against its own risk analysis, two counts of the same bank channel over different periods, two AI-policy timelines.

In a reportorial register the correct construction is to state both with their dates and sources and add "the two accounts have not been reconciled", then stop. Do not pick a winner in a report; that is what the reconcile pass is for. Where the wiki has already resolved one — the spectrum figures were closed in favour of the instrument — cite the instrument and do not resurrect the dispute.

Related: attribute company-reported and vendor figures as such at the point of use, and carry sample caveats inline. One survey in the material was ten interviews and focus groups, which is executive judgement rather than measurement, and saying so in six words costs nothing.

## 10. Keeping three report types genuinely distinct

They overlap in subject matter and must not overlap in function.

- **Status** answers *where is this now*. State only. Chronology removed. The test: if a sentence would read oddly six weeks from now, it belongs in the monthly.
- **Monthly** answers *what happened in this window*. Events, with dates. It should not restate maturity.
- **Progress** answers *what moved between two dates*. It needs both endpoints and is the only one of the three that can honestly say nothing changed.

Where an object appears in more than one — the same reform programme surfaced in all three — the rule applied was that the monthly carries what moved, the status carries what it means for the current position, and the progress report carries the delta. One deliberate repetition was allowed, where the same quoted concession was the hinge of two documents.

Aligning the section headings across all three (Summary, Infrastructure, DPI, Governance and regulation, AI and technology, Inclusion/capacity/finance, gaps, comment) was Bill's instruction and it works well: it makes the three readable side by side and makes it obvious when a section is empty in one of them.

## 11. Register: separating fact from comment

Iteration 1 was drafted in Bill's own voice per `bill-writing-style`. That was wrong for this class of document, and the correction is instructive.

What had to change mechanically: remove first person; replace declarative argumentative headings with plain descriptors; remove the verdict sentences that carried each section; attribute every non-official claim with "according to", "the department reported", "the court held"; convert judgements into stated facts plus an unreconciled note; and move everything that survived as opinion into a short, explicitly labelled **Comment** section at the end.

The last part matters most. A conservative newspaper separates news from leader column, and the structural separation is what makes the reporting credible — not the absence of opinion. Keep the comment, label it, and keep it short. Three sentences of pattern-level observation at the end of a factual document is worth more than the same material dissolved through the body.

A quick tic check helps when converting register:

```python
for tic in [' we ', ' our ', ' I ', 'binding constraint', 'counter-example', 'the real question']:
    if tic in prose.lower(): print("tic:", tic)
```

## 12. Byproducts worth routing back into the base

Report drafting is a good detector of base defects, because it forces every claim through a resolution step. This exercise surfaced: one probable duplicate — the same quarterly report held under two slugs, one the primary PDF and one a news summary; one held artefact with no `url:` field, so uncitable by an automated pass; and a confirmation that a previously closed contradiction is still correctly closed on re-verification.

Worth deciding whether report passes should emit these as post-run notes automatically. They cost nothing to collect during a pass and are exactly the kind of thing that never gets found by looking for it.

## 13. What I would do differently

Firstly, build the index and run the source-count-by-month check before agreeing the scope of any report, not after drafting. Both are cheap and both change what can honestly be promised.

Secondly, settle the word-limit definition — prose only, or prose plus tables — at commissioning. The inventory tables were the right call editorially and they broke a limit that had already been agreed.

Thirdly, ask agents for the movement ledger format even when drafting a status report. Requiring a dated position at both ends is a stronger discipline than asking for current state, and the extra structure costs the agent almost nothing.

Fourthly, consider having the not-held rows written straight to `reviews/` as acquisition lines in the same pass, rather than existing only inside a deliverable a human has to re-read to action.
