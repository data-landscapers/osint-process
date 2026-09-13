# Origin screen — the shared inadmissible-origin gate

**A shared object, not a pass. It has no trigger.** Every sweep calls it at its admissibility screen (before staging), and `INGEST.md` step 1 calls it again on whatever reaches `new/` by any other route. A new sweep adopts it in one line — *"apply the origin screen (`wiki/origin-screen.md`)"* — and needs no rules of its own.

It screens **where an item came from**, not what it says. Content screening — scope, tier, second-hand synthesis, digests — stays in `CLAUDE.md` → *The material*. A hostile origin is fluent, correctly dated, on-topic and specific enough to compile straight onto a page, so it cannot be caught by reading the item.

**It is called twice on purpose.** The sweep call stops the fetch; the ingest call catches hand-dropped clips, mined leads and anything a sweep let through. Ingest is the only door into the base, so at ingest the gate is never optional.

---

## The list

`logs/drop-list.csv` — `domain,network,status,rule,added,note`.

| `status` | Meaning | Action |
|---|---|---|
| `drop` | Adjudicated inadmissible. | **Never stage, never ingest.** Log the drop as **`inadmissible-origin`**. |
| `watch` | One sighting of a hostile shape; not yet adjudicated. | Screen out this item as `inadmissible-origin` **and** promote the row to `drop` — a second sighting is the adjudication. |

**Consulting the list is mechanical, not a judgment step.** `python scripts/origin-screen.py` screens every candidate in `new/` against the list in one command and exits non-zero on any `drop` or `watch`. It also takes bare domains — `--domain a.com b.net` — for a sweep screening before it fetches. One command per run, or per batch; the list is never consulted by eye.

Match on the **registrable domain**, subdomains included. The list is a *by-origin* list, not a quality bar: a merely weak or thin outlet never goes on it. Reserve it for origins that **misreport** — fabricate, rewrite without attribution, or launder someone else's reporting under their own byline.

**A hosting domain is not an origin.** A first-party document served from a CDN or a hosted site takes its **host** as its registrable-domain key — a court's own practice direction in an S3 bucket reads as `amazonaws.com` — and a `drop` row against a CDN would screen out every document any publisher hosts there. **Screen the publisher, not the rack**: where the URL's registrable domain is a hosting or CDN provider and the document is plainly the named publisher's own, clear it on the publisher and write no row. `NOVEL` on such a domain is noise, not a first sighting.

**Adding a row is the same edit as the adjudication.** A domain adjudicated in a lint, a reconcile or a sweep and not written to the CSV in that edit is not on the list.

---

## The screen

Run in order, on every candidate, before fetching a body:

1. **Listed?** Apply the `status` table above. Then go to *Mining*.
2. **Unlisted — does it show a shape?** Test against the five shapes below. A match is a screen-out (`inadmissible-origin`) plus a **new `watch` row** written in the same edit. Never wait for Bill; never carry a candidate over to the next run to decide.
3. **Unlisted, no shape, and the base has never admitted this domain?** → **nothing follows.** The script reports it as `NOVEL`; the item proceeds.
4. **Clean origin** → continue with the ordinary admissibility screen.

### The five shapes

| Shape | Markers |
|---|---|
| **Fabricated news** | Invented figures, MoUs, officials or venues around a real-sounding event; served body is site chrome plus a teaser truncated at an ellipsis; bylines visible only in search indexes; headlines that append an economic-stakes clause to an unrelated story. |
| **Unattributed rewrite** | A real event, restyled — invented operational colour, drifted framing, an editorial comparison no primary carries; **publication date presented as the event date**; injected ad chrome inside the captured body. |
| **Verbatim mirror** | Byte-level or near-verbatim republication of a named outlet, reposted minutes after the original; high volume, on-topic, correctly dated; often the most prolific hit for a given country query. |
| **Excerpt aggregator** | Stored "body" is a truncated excerpt block prefixed with the site's own name; the underlying event is always covered better elsewhere. |
| **AI assembly with self-declared references** | Reads as well-sourced and **openly lists its own "verified references"** — yet the references do not support the claims, and the piece conflates two documents, two publishers or two studies into one attribution. **The most dangerous shape, precisely because its sourcing display invites trust.** |

---

## Hold — retired

**The `NOVEL` verdict withholds nothing. It is reported and nothing follows from it.** `scripts/origin-screen.py` computes it — no admitted source in `raw/` carries a `url:` on this registrable domain — and prints it, because knowing the base has no track record with an origin is worth a line. It is not a gate, a status or a queue: a first-party publisher is a first sighting on its own domain by construction, and the registrable domain measures where a file is served, not who wrote it.

**`origin_status:` is never written** (`schemas.md` §4); `origin-screen.py --held` reads 0 and nothing refills it. Lint #6 keeps its origin-adjudication half — it writes `drop-list.csv` rows — and drains no hold.

**What gates.** The `drop`/`watch` list above, applied mechanically by one command per run. Beyond it, a hostile origin is caught by `CLAUDE.md` → *The material*, which asks whether the account is the first-hand party, and `INGEST.md` step 1, which applies it.

## Mining, and what may cross the gate

A screened-out item is still **mined** for the primaries it cites — mining is the value, and it is not admission.

- Stage each cited primary as its own candidate, on its own merits. Where a cited primary cannot be fetched, add an acquisition line.
- **Nothing else crosses.** No figure, date, attribution, quote or framing travels from a screened-out item into the wiki, not even as "reported by". An attribution asserted only by a screened-out origin is **unestablished**, and where it bears on a page it is written there as a dated absence.
- If real reporting exists *only* on a screened-out origin and no original can be found, **drop it** and state the absence on the page. There is no parking folder.
- The husk is deleted once mined (`INGEST.md` step 1).

---

## After a promotion to `drop`

A domain moving to `drop` may already be in the base. In the same session:

1. `grep` `raw/` for the domain.
2. Hand every hit to **lint #6** — retire the source, rewire or strike its citations, and re-source or date-as-absent every claim that rested on it.
3. The retire/rewire count rides the calling pass's own `log.md` line.

## Logging

- Every screen-out goes to the calling sweep's drop log with reason **`inadmissible-origin`** — never `off-topic`, never `second-hand-ai-synthesis`. The reason string is how a recurrence is spotted.
- Screen-outs are not surfaced to Bill individually; the counts ride the sweep's tally line.
