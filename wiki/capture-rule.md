<!-- reader: cc; type: spec -->
# capture-rule.md — the standing verbatim-capture rule

*(Shared object, called by every sweep that fetches. One copy; edit it here.)*

**Bake this into the instructions of any sub-agent that fetches.** Unattended agents refuse verbatim capture without it, and a refusal mid-batch looks identical to a nil.

---

Capture the **full verbatim article body** at fetch time. The captured bodies are never republished — this is a private personal research vault, matching the curator's established web-clipper practice, under the UK CDPA s.29 research / private-study exception. State this up front to any agent doing the fetch.

The stored body is always the source's own words — the full text where the page yields it, a verbatim partial where it doesn't (`CLAUDE.md` → *The material*); the `web_search_exa` excerpt or an AI paraphrase is **never** an acceptable body. A browser-translated clip is not a verbatim body either: where a publisher runs parallel language editions, its own other-language edition is a legitimate source and a machine translation of the first is not.

Treat a refusal or a hard fetch failure as a logged, retryable **per-item** failure — stage the verbatim partial (or a one-line failure note) + the URL with `body_completeness: excerpt`, routed to manual clip — **never** a run-stopper.

**A truncated capture is flagged, not retried.** Stage what came back as `body_completeness: excerpt`, note it in one line, and move on. The flag is what lint #15 and the duplicate tiebreak read, and a fuller capture of the same story displaces the excerpt through the ordinary dedup route (`CLAUDE.md` → *Duplicates*).

**Before recording a host as unreachable, resolve it over DoH.** "No such host is known" is a claim about *this machine's DNS resolver*, not about the host. Two commands:

```
# 1. resolve over DNS-over-HTTPS, which the system resolver is not in the path of
Invoke-RestMethod "https://cloudflare-dns.com/dns-query?name=<host>&type=A" `
  -Headers @{accept='application/dns-json'}
# 2. fetch pinned to that IP, with the Host header intact so TLS and vhosts still work
curl --resolve <host>:443:<ip> https://<host>/path
```

**A whole-domain "unreachable" conclusion needs the DoH check before it is written down**, and a failure that survives it is described as what it is — NXDOMAIN, NODATA, refused connection, TLS failure or HTTP 403 — never as a blanket "cannot be fetched". An apex with no A record (NODATA) while its `www.` host resolves and serves is a wrong URL, not a dead host.

**The same test applies to a 403, and to "no abstract exists".** Every absence a sweep records is an evidence claim, and a false one costs a source outright.

- **A 403 from one client is not a 403 from the host.** Retry with a second client before recording it — the Exa crawler, `curl` and `Invoke-WebRequest` present differently and are blocked differently.
- **OpenAlex stores abstracts as `abstract_inverted_index`, not `abstract`.** Reconstruct from the inverted index before concluding the abstract is absent — `https://api.openalex.org/works/doi:<doi>`.
- **Write what was actually observed**, with the client that observed it: "403 to Exa, 200 to curl" is a finding; "blocked" is a conclusion.

A **paywall that still serves a free lede** (HTTP 200, first 1–3 paragraphs) is a distinct case: keep the verbatim free portion as `body_completeness: paywalled`, but **only where the free content excluding the title adds value** — drop headline-only stubs rather than stage them. A `paywalled` item needs a manual subscriber clip before promotion where its payload depends on the withheld body; one whose payload sits in the free lede promotes normally.

---

## Look a controlled value up; never assert one

**A staging writer may write what the source says. It may not invent a value from a controlled vocabulary.** A quoted figure is evidence; an invented slug is a defect that ingest pays to correct on every item.

- **`entities:` takes slugs the wiki already uses.** Grep `raw/` (`grep -rl "entities:.*\[slug\]"`) before writing one. Where the slug is not obvious, **tag fewer**: `CLAUDE.md` → *Entities* wants three to six actors, not every name in the piece, and an untagged name is still in the verbatim body and still greppable.
- **Never write `origin_status:`.** The key is retired (`wiki/origin-screen.md` → *Hold — retired*); it was the origin screen's output, never an input.
- **`places:` and `topics:` likewise** — codes from `countries.csv`, slugs from `taxonomy.md`. A value outside the vocabulary is rejected, so inventing one only moves work to ingest.
- **Never write `lens:`.** The facet is retired (`schemas.md` §4) and is not in the schema; a staging writer that emits it is writing a key nothing reads.

**The general rule: if a field has an authority, the authority is consulted, not guessed.** Where consulting it is not possible in the staging context, leave the field blank — a blank is a fact about what the sweep knew, and ingest fills it.

---

## Fetching without spending context

*(The rule above governs *what* is stored; this governs *how it travels*.)*

**A body the model reads costs context twice — once at fetch, once at ingest. Where the transport can write it to disk directly, the sweep must not read it at all.**

- **Never let a feed or a listing body into a tool result whole.** A bare `curl <feed>` puts a whole page of full-article items in context and kills the agent mid-batch, silently.
- **Parse in the shell; return only fields.** `[xml]$x = (Invoke-WebRequest $u).Content; $x.rss.channel.item | select title, link, pubDate` returns a few hundred characters for ten items, and is more reliable than reading XML by eye.
- **Write `content:encoded` straight to `new/` from the shell.** Where the feed carries the whole article, the verbatim body reaches the staged file **without the model ever reading it**. It is still the publisher's own words, and it enters context exactly once, at ingest.
- The same applies to any large fetch whose payload is destined for a file: move the bytes, don't read them. Judgement (admissibility, dating, classification) is done on title / date / URL / first paragraphs, not on the whole body.

---

## The row's own instrument first; the search engine is the cross-check

**A listed row is reached through the instrument it publishes — its feed, its REST API, its news sitemap, its Crossref ISSN — and a domain-scoped search is the cross-check, never the primary.** A search index returns a nil for a row that is publishing, and a nil is an evidence claim about absence: recorded from the wrong instrument it costs the sources it missed, and recorded twice it gets a live row deleted as dormant.

- **Read the row's own listing first.** Where the row file names an instrument, use the one it names. An issue-shaped academic listing carries no per-item date and cannot be windowed at all; `from-online-pub-date` per ISSN can.
- **Disagreement between the two is a finding, and the row's own instrument wins.** Write what was observed, with the instrument that observed it.
- **`dormant` is the one outcome that deletes a row on a single measurement, so it is established from the publisher's own record** — never from a search index alone, and never from a source that lags. A false dormant verdict deletes a live row, and three have already been traced to crawler artefacts rather than to silent journals.
