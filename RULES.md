# RULES.md — the rules pass

Trigger: **the sweep cycle's last stage, every night** (`SWEEP-CYCLE.md` → *Rules, the night's last act*), or **"run rules"** by hand. Either way it is over the whole of `reviews/rule-candidates.md`. No selection: if CC finds itself asking which candidates to take, the answer is all of them.

**Rules change here and nowhere else.** A run that meets an edge case takes the conservative option, records it in the commit body, and drops one candidate line. It does not edit a process file, a spec, or `CLAUDE.md` — not to record what it learned, not to stop the case recurring, not while the case is fresh. That is `CLAUDE.md` → *How CC works*, and this file is the pass it points at.

---

## Why the rule cannot be written in the run that met the case

A rule written mid-run is written by the only party inconvenienced by the case, at the moment it is most inconvenient, with a sample size of one. It reads as obviously correct and is unfalsifiable, because the case that prompted it is the only evidence it will ever be tested against. Two symptoms followed: one rule edited twice in three minutes as a single item was worked, and a note reversing a rule written four days earlier.

Batching fixes it without needing anyone to be more disciplined. A candidate that has earned its line three separate times is visibly a rule; one that has earned it once is visibly an item that came out awkwardly, and the pass deletes it unread by any process file.

## The candidate line

One line in `reviews/rule-candidates.md`, appended by whatever run met the case:

```
YYYY-MM-DD · <file the rule would land in> · <the case, in a clause> · <what the run did instead>
```

The last field is the load-bearing one: it records the conservative option actually taken, so the pass can see whether it was in fact costly. A candidate with no *what I did instead* is not a candidate — the run had a free choice and made it.

**A line is appended, never edited.** The same case met a second time appends a second line. Recurrence is counted by how many lines name it, so merging them destroys the only evidence the pass has.

## The loop

For each distinct case in `reviews/rule-candidates.md`:

1. **Count its lines.** Three or more from separate runs is a rule; one or two is not, whatever the case looks like written down. **Separate runs, not separate slices**: ten slices of one night meeting the same case is one line's worth of evidence, however many of them wrote it down.

2. **Ask whether an existing principle already covers it.** It usually does — `CLAUDE.md` → *Keeping this file short*. A case covered by a principle that a run failed to apply is not a new rule; it is evidence the principle is in the wrong file or is written too abstractly to reach for, and the pass may move or sharpen it without adding anything.

3. **Write it once, in the file that owns it**, in the register `CLAUDE.md` sets: the rule, not the incident that produced it, and no dated-ruling citation. If it lands in `CLAUDE.md`, delete a rule to pay for it, and surface the change before it lands.

4. **Delete the lines of a case the pass ruled on** — became a rule, or was already covered by one. **A case still under three lines stays**, with its dates, because those lines are the only evidence of recurrence there will ever be.

**A line ages out at 21 days.** Nightly, the pass ran the same evening the case arose, so "a case that recurs will earn its lines again" is no longer true of a same-night deletion: delete a singleton tonight and the recurrence three days from now reads as its first occurrence, for ever. Ageing is what the weekly boundary used to do implicitly — a fortnight and a bit of ordinary running is long enough for a real pattern to show a second line, and long enough that a case which has not is genuinely an item that came out awkwardly. **The count on the standing tally is therefore the open queue, not the night's arrivals**, and a number that climbs is a case recurring rather than a pass not running.

## What is not a candidate

A defect is not a rule. A script that mis-parses, a check that fires on the wrong thing, a stale claim in a process file — those are fixed in the run that finds them, immediately, and logged. The distinction is whether the file is **wrong** or **silent**: a wrong file is repaired on sight; a silent one waits for this pass.

A one-off ruling is not a rule either. `CLAUDE.md` → *Act. Log after. Never ask.* already disposes of it: take the conservative option, record it in the commit body, move on.

## Ending the pass

Append **one entry** to `logs/log.md` via `scripts/log-append.py` — one line, 40 words, counts and objects: candidates read, rules written and where, candidates dropped. A change to `CLAUDE.md` is surfaced on screen before it lands, per that file. Then the tally:

`contradictions - NN ; acquisitions - NN ; awaiting ingest - NN ; housekeeping - NN ; rule-candidates - NN ; osint-notes - NN ; corpus-notes - NN ; fetch - NN ; commits - NN ; decisions logged - NN`

An empty `reviews/rule-candidates.md` at the *start* is a quiet night, not a skipped pass; a queue holding only lines under three occurrences and under 21 days old is the ordinary end state.

## Where it runs, and why last

**Last in the night, after housekeeping and after nothing** (`SWEEP-CYCLE.md`), or in its own session on the manual trigger. No other pass runs while rules are being rewritten, because every other pass reads them — which is why it cannot sit anywhere *else* in the cycle: a rule that changes with a step still to come leaves that step working to a different file from the ones before it, and `CLAUDE.md` → *How CC works* forbids exactly that. Placed last, there is no such step, and the queue drains on the same automatic cadence as every other one.

**It amends process files, so it is the parent's own work and never a sub-agent's**, and `assert-containment.py --stage rules` names each amended file with `--allow-extra` — the deny set holds, the exception is per file, and the night's log line says which rules moved.
