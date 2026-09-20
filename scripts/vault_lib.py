#!/usr/bin/env python3
"""vault_lib.py — the vault read layer: frontmatter, URLs, and the rebuildable index.

Three things live here because three passes were each doing them differently.

1. **One frontmatter parser.** The vault's frontmatter is a YAML *subset* that no
   strict parser survives: 144 distinct keys, block scalars (`hub_line: >`), the
   canonical link-list form `[[a], [b]]` from `facets.md` §1, and — because
   lint #12 exists — the malformed hybrids it is there to fix. A strict loader
   would raise on exactly the files a lint pass most needs to see, so this one is
   deliberately tolerant and **records what it could not read** in `fm_warnings`
   instead of failing.

2. **One URL normalisation.** `INGEST.md` step 2 states the contract in prose and
   requires the sweeps' pre-fetch filter to apply it identically — "one
   normalisation, one index, or the two gates disagree". Prose cannot enforce
   that. `normalise_url()` is that contract as a function; both gates and the
   index now key on the same string by construction.

3. **The index** (`index/`) — a from-scratch rebuild of every artefact's
   frontmatter plus a link edge list, so the deterministic half of lint stops
   being model work. It is **derived, disposable and never committed**: the only
   writer is a full rebuild, so it cannot drift out of step with the vault the
   way a hand-maintained or append-at-ingest register would. That was the
   objection that withdrew it in July, and rebuilding the whole thing costs about
   a second, so there is no append path to get wrong. Nothing cites it, nothing
   stores a fact in it, and `CLAUDE.md` → *Working the base* still holds: querying
   is read-only, and results are snapshots, never sources.

Consumers call `load_index()`, which **rebuilds automatically if the vault has
moved underneath it**. A stale read is therefore not possible, which is what pays
for not committing the thing.
"""
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(ROOT, "index")
FILES_JSONL = os.path.join(INDEX_DIR, "files.jsonl")
LINKS_JSONL = os.path.join(INDEX_DIR, "links.jsonl")
META_JSON = os.path.join(INDEX_DIR, "meta.json")
DB_PATH = os.path.join(INDEX_DIR, "vault.db")

# Bumped when a row's shape changes, so an index built by an older builder is
# stale by definition rather than silently half-populated.
INDEX_VERSION = 1

# Walked in full. `logs/` is deliberately absent: it is append-only prose, not
# artefacts with frontmatter, and log.md alone would double the read.
INDEX_ROOTS = ("raw", "wiki", "new", "new-budget", "budget-archive", "reviews",
               "sweep")

# Markdown counterparts are indexed with their frontmatter; these are indexed by
# stat alone (path, size, mtime) so lint #22's artefact-basename match and the
# acquisition gate can resolve a held binary without opening 5 GB of PDFs.
ARTEFACT_EXT = (".pdf", ".xlsx", ".xls", ".csv", ".txt", ".docx", ".json", ".zip")

# Files that *document* the link convention rather than cite anything — quoted
# syntax is not a citation (LINT.md #4). Consumers of links.jsonl skip these.
LINK_CHECK_SKIP = {
    "wiki/reference.md",
    "wiki/facets.md",
    "wiki/layout.md",
    "wiki/schemas.md",
    "wiki/intake.md",
    "wiki/operations.md",
    "wiki/finance-record-spec.md",
    "wiki/finance-load-domestic-state.md",
    "wiki/finance-news-driver.md",
}

# Truncation evidence for `body_completeness` (lint #15, #21 class 3), scanned once
# at build time so the check reads a flag instead of 8,000 bodies.
#
# **Deliberately narrow, and the narrowness is measured.** The loose word list
# ("read more | subscribe | continue reading") was tested against 197 bodies read
# by hand in housekeeping job 12: it caught **zero** cuts the patterns below did
# not, and produced **120 false positives** — it fires on "12 million subscribers"
# in ordinary prose and on every "Read more" nav rail. Reproducing it here would
# have put 127 candidates in front of a check whose real class is about four.
# WALL states a condition on the *reader*; CHROME is site furniture that merely
# contains the same words, and suppresses the hit. `audit-machine-records.py`
# owns the full test, including the mid-sentence cut, which needs the prose block.
WALL_RE = re.compile(r"(become a .{0,20}insider|sign in to read the full|"
                     r"to continue reading, please subscribe|subscribe for full access|"
                     r"already have a subscription|register to begin your journey|"
                     r"create a free account to (read|continue)|unlock this article)", re.I)
ELISION_RE = re.compile(r"\[\s*(?:\.\.\.|…|�)\s*\]")
CHROME_RE = re.compile(r"(site sponsor|signiflow|read more about cookies|accept policy|"
                       r"save & accept|powered by|scroll to top|leave a comment|"
                       r"followers\s+(like|follow)|subscribers\s+subscribe)", re.I)
# An in-body adjudication that check #15 has already inspected this file's truncation
# marker and ruled it a false positive — added 2026-08-10, token review task 7, note 196.
# A detector that fires on the same settled case every night makes a clean run and a
# dirty run look identical; a dated line the detector itself can read is the fix, the
# same way #9 whitelists intentionally-dead links rather than re-flagging them forever.
ADJUDICATED_15_RE = re.compile(r"lint note.{0,40}\(#15\).{0,400}do not re-open", re.I | re.S)

# Query parameters that identify a *reader*, not a document. Everything else is
# kept: some publishers carry the article ID in the query string, and stripping
# it would map two articles to one key and drop a genuine source invisibly
# (INGEST.md step 2 — err towards a duplicate, never towards a false match).
TRACKING_PARAMS = ("utm_", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid",
                   "igshid", "ref_src", "spm")

# Hosts where the `#fragment` **is** the document identity, not a scroll position.
# An IATI d-portal activity is addressed *by* its fragment —
# `ctrack.html#view=act&aid=<activity-id>` — so stripping it maps every activity a
# publisher has ever filed onto one key and reports the second onward as DUP-EXACT.
# Fragments are noise on every ordinary article URL, so this is a host-scoped
# exception and never a general retreat from stripping them. Matched against the
# host after `www.` is dropped and the host is lower-cased.
FRAGMENT_IS_IDENTITY = ("d-portal.org", "d-portal.iatistandard.org")

# Second-level labels that are registry suffixes, not the registrable name.
# `co.ke`, `org.ng`, `ac.za`, `gov.gh` — taking the last two labels there would
# collapse every Kenyan site to `co.ke` and screen the whole country as one origin.
SLD = {"co", "com", "org", "net", "gov", "gouv", "edu", "ac", "or", "go", "mil", "sch",
       "ne", "web"}

# Hyphens are allowed in keys: `needs-review: true` is in use on five sources, and
# a key regex without it read them as unparsable lines.
KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
BLOCK_RE = re.compile(r"^[|>][-+]?$")
DATE_PREFIX_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
WIKILINK_RE = re.compile(r"\[\[([^\[\]|]+?)(?:\|[^\[\]]*)?\]\]")
BRACKET_ITEM_RE = re.compile(r"\[+\s*([^\[\]]+?)\s*\]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


# --------------------------------------------------------------------------- #
# URLs
# --------------------------------------------------------------------------- #

def normalise_url(url):
    """`INGEST.md` step 2's normalisation contract, as a function.

    Strip the scheme, a leading `www.`, the `#fragment` and known tracking params;
    lower-case the **host only**, never the path; strip a trailing `/`. Other query
    strings are kept.

    https://www.Example.com/A/b/?id=7&utm_source=x#top  ->  example.com/A/b?id=7

    Percent-decoded first (%27 and a literal ' are the same URL), so two
    fetches of the same document that differ only in escaping still collide.

    **`FRAGMENT_IS_IDENTITY` hosts keep the fragment**, because on them it is what
    names the document: `d-portal.org/ctrack.html#view=act&aid=SE-0-SE-6-71002318`.
    The fragment is percent-decoded but never case-folded — an IATI activity id is
    case-bearing.
    """
    s = (url or "").strip()
    if not s:
        return ""
    s = re.sub(r"^[A-Za-z][A-Za-z0-9+.-]*://", "", s)
    s, _hash, frag = s.partition("#")
    s = urllib.parse.unquote(s)
    s = re.sub(r"^www\.", "", s, flags=re.I)
    host, sep, rest = s.partition("/")
    host = host.lower()
    path, qsep, query = rest.partition("?")
    if query:
        kept = [p for p in query.split("&")
                if p and not any(p.lower().startswith(t) for t in TRACKING_PARAMS)]
        query = "&".join(kept)
    out = host + (sep + path if sep else "")
    if query:
        out += "?" + query
    out = out.rstrip("/")
    frag = urllib.parse.unquote(frag).strip()
    if frag and host in FRAGMENT_IS_IDENTITY:
        out += "#" + frag
    return out


def registrable(host_or_url):
    """The registrable domain: what `drop-list.csv` keys on, subdomains included.

    news.example.co.ke -> example.co.ke ;  https://www.Example.COM/a?b -> example.com
    """
    s = (host_or_url or "").strip().lower()
    s = re.sub(r"^[a-z][a-z0-9+.-]*://", "", s)      # scheme
    s = s.split("/")[0].split("?")[0].split("#")[0]  # host only
    s = s.split("@")[-1].split(":")[0]               # userinfo, port
    s = re.sub(r"^www\.", "", s).strip(".")
    if not s:
        return ""
    parts = s.split(".")
    if len(parts) <= 2:
        return s
    if len(parts[-1]) == 2 and parts[-2] in SLD:     # co.ke, org.ng, ac.za
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def is_bare_domain(url_norm):
    """No path and no query — cites the publisher, not the document (lint #14)."""
    return bool(url_norm) and "/" not in url_norm and "?" not in url_norm


# --------------------------------------------------------------------------- #
# Frontmatter
# --------------------------------------------------------------------------- #

def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _decomment(v):
    """Strip a trailing YAML comment from an unquoted scalar.

    Only a **whitespace-preceded** `#` starts a comment, which is why a URL
    fragment (`...page#top`) survives this and `published: 2026-01-01  # date
    approximate` parses as a date. Quoted values are left whole.
    """
    v = v.strip()
    if v[:1] in "\"'":
        return v
    if v.startswith("#"):                      # the whole value is a comment
        return ""
    return re.split(r"\s+#\s", v, 1)[0].rstrip()


def _parse_flow(inner, warnings, key):
    """A `[...]` list. Two shapes, one parser.

    Plain values (`places: [KEN, ZAF]`) split on commas. A **link list**
    (`entities: [[a], [b]]`) does not: `facets.md` §1 notes that the brackets
    *pair*, so a body-wikilink regex matches none of it and a comma split breaks
    on any slug containing one. Items are read as bracketed groups instead.
    """
    inner = inner.strip()
    if not inner:
        return []
    if "[" in inner:
        if re.search(r"\[\s*\[", inner):
            # `[[[a]], [[b]]]` or a hybrid — readable, but lint #12's business.
            warnings.append("link-list-nonstandard:" + key)
        return [_unquote(m) for m in BRACKET_ITEM_RE.findall(inner)]
    return [_unquote(p) for p in inner.split(",") if p.strip()]


def parse_frontmatter(text):
    """(fm, warnings, body) from a markdown file's text.

    Tolerant by design — see the module docstring. `warnings` is what the reader
    could not make canonical sense of, and is what lint #1 and #12 act on.
    """
    warnings = []
    if not text.startswith("---"):
        return {}, ["no-frontmatter"], text
    # This closes on the first line *opening* `---`, not the first line that *is*
    # one, so a body's horizontal rule can close the frontmatter for a record whose
    # own fence is missing. Tightening it to an exact fence is not free: a record
    # whose fence has body text glued to it (`---MESRI : une nouvelle...`) then
    # stops parsing at all, and the loose read recovers that one losslessly. Both
    # shapes are malformed data, both were repaired on 2026-09-08, and one night is
    # not enough evidence to choose which the parser should favour. Left as it is,
    # and queued.
    end = text.find("\n---", 3)
    if end < 0:
        return {}, ["frontmatter-unclosed"], text
    head = text[text.find("\n") + 1:end]
    body = text[end + 4:].lstrip("\r\n")
    if body.startswith("-\n") or body.startswith("-\r\n"):   # `----` fence residue
        body = body[2:]

    fm = {}
    lines = head.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].rstrip("\r")
        i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = KEY_RE.match(line)
        if not m:
            if re.match(r"^\s*-\s+\S", line):
                continue                       # consumed by the block-list branch
            warnings.append("unparsed-line:" + line.strip()[:48])
            continue
        key, val = m.group(1), _decomment(m.group(2))
        if key in fm:
            warnings.append("duplicate-key:" + key)

        if BLOCK_RE.match(val):                # `key: |` / `key: >`
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].rstrip("\r").strip())
                i += 1
            fm[key] = " ".join(b for b in block if b).strip()
        elif val.startswith("[") and val.endswith("]"):
            fm[key] = _parse_flow(val[1:-1], warnings, key)
        elif val == "":                        # a block list, a nested map, or empty
            items, nested = [], {}
            while i < len(lines):
                nxt = lines[i].rstrip("\r")
                if re.match(r"^\s*-\s+\S", nxt):
                    items.append(_unquote(_decomment(re.sub(r"^\s*-\s+", "", nxt))))
                elif re.match(r"^\s+[A-Za-z_][A-Za-z0-9_-]*:", nxt):
                    k2, _s, v2 = nxt.strip().partition(":")
                    v2 = _decomment(v2)
                    nested[k2] = (_parse_flow(v2[1:-1], warnings, k2)
                                  if v2.startswith("[") and v2.endswith("]") else _unquote(v2))
                else:
                    break
                i += 1
            fm[key] = items or nested or ""
        else:
            if val.startswith("["):
                # Starts a list and never closes it. Keep the raw text rather than
                # the fragment that parses: `author: [[bill]], Bernard Sabiti and
                # Sam Wozniak` is a scalar with a link in it, and reading it as a
                # one-item list would silently delete two of the three authors.
                warnings.append("list-unclosed:" + key)
                fm[key] = val
            else:
                # A plain or quoted YAML scalar may fold onto following indented
                # lines. Those lines used to fall through as `unparsed-line` and
                # the value kept only its first line — silently, so a 625-character
                # note reached the catalogue as 75 characters. Absorb them, and
                # keep the exclusions narrow: an indented `- item` or `key:` is
                # still ambiguous and still warns rather than being swallowed.
                cont = []
                while i < len(lines):
                    nxt = lines[i].rstrip("\r")
                    if not nxt.strip() or nxt[:1] not in (" ", "\t"):
                        break
                    if (nxt.lstrip().startswith("#")
                            or re.match(r"^\s*-\s+\S", nxt)
                            or re.match(r"^\s+[A-Za-z_][A-Za-z0-9_-]*:", nxt)):
                        break
                    cont.append(nxt.strip())
                    i += 1
                fm[key] = _unquote(" ".join([val] + cont).strip() if cont else val)

    # The reader above is deliberately tolerant, which is why it cannot be the test of
    # whether the block is readable. CORPUS parses `raw/` with a real YAML parser, so a
    # record this reader recovers happily can still be invisible to the consumer — on
    # 2026-09-20 that was 371 records against the 19 lint #1 was reporting (job 95).
    # One `yaml.safe_load` here closes that gap and stops the defect regrowing unseen.
    try:
        import yaml
        if not isinstance(yaml.safe_load(head), dict):
            warnings.append("yaml-unparseable:loads, but not as a mapping")
    except ImportError:
        pass
    except Exception as exc:
        warnings.append("yaml-unparseable:" + str(exc).split("\n")[0][:70])
    return fm, warnings, body


def as_list(v):
    """Facet accessor — a key may be absent, a scalar, or a list."""
    if v is None or v == "":
        return []
    return list(v) if isinstance(v, list) else [v]


# --------------------------------------------------------------------------- #
# Building
# --------------------------------------------------------------------------- #

def _walk(roots=INDEX_ROOTS):
    """(relpath, abspath) for every indexable file, sorted, POSIX separators."""
    out = []
    for root in roots:
        base = os.path.join(ROOT, root)
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
            for fn in filenames:
                ext = os.path.splitext(fn)[1].lower()
                if ext != ".md" and ext not in ARTEFACT_EXT:
                    continue
                ap = os.path.join(dirpath, fn)
                out.append((os.path.relpath(ap, ROOT).replace(os.sep, "/"), ap))
    out.sort()
    return out


def _expects_frontmatter(rel):
    """Where a missing `---` block is a defect rather than the normal shape.

    Sources and pages carry frontmatter; sweep manifests, drop logs, registers and
    the hand-written `wiki/` index pages never did. Warning on all of them would
    put 111 non-defects in front of lint #1 and bury the ones that matter — there
    are none in `raw/`.
    """
    if rel.rsplit("/", 1)[-1].startswith("_"):     # `_watchlist.md`, `__query-template.md`
        return False
    if rel.startswith(("raw/", "new/")):
        return True
    return rel.startswith(("wiki/concepts/", "wiki/places/",
                           "wiki/intersections/"))


def _sections(body):
    """[[heading, words], ...] — lint #8 measures per section, not per page."""
    out, cur, count = [], None, 0
    for line in body.split("\n"):
        h = HEADING_RE.match(line)
        if h and len(h.group(1)) == 2:
            if cur is not None:
                out.append([cur, count])
            cur, count = h.group(2).strip(), 0
        elif cur is not None:
            count += len(line.split())
    if cur is not None:
        out.append([cur, count])
    return out


def _row(rel, st, text=None):
    """One artefact -> one index row. The row *is* the frontmatter, plus `d`.

    Keeping `fm` verbatim rather than mapping it onto fixed columns is what stops
    the index needing a re-spec every time a key is minted (`cite_through` and
    `origin_status` were both minted in the fortnight before it was built) — and
    it is what lets a JSON Schema validate a row directly.
    """
    ext = os.path.splitext(rel)[1].lower()
    parts = rel.split("/")
    d = {"folder": parts[0],
         "slug": os.path.splitext(parts[-1])[0],
         "ext": ext,
         "bytes": st.st_size,
         "mtime": int(st.st_mtime)}
    md = DATE_PREFIX_RE.match(parts[-1])
    if md:
        d["file_date"] = md.group(0)
    if parts[0] == "raw" and len(parts) > 2:
        d["shard"] = parts[1]

    if ext != ".md":
        d["kind"] = "artefact"
        return {"path": rel, "fm": {}, "d": d}, ""

    fm, warnings, body = parse_frontmatter(text)
    if "no-frontmatter" in warnings and not _expects_frontmatter(rel):
        warnings = [w for w in warnings if w != "no-frontmatter"]

    # LF-normalised before hashing: the vault is mixed CRLF/LF, and a hash that
    # moved when a file's line endings did would report every such file changed.
    norm = body.replace("\r\n", "\n").strip()
    d["kind"] = fm.get("type") or ("index" if parts[0] == "wiki" else parts[0])
    d["words"] = len(norm.split())
    d["body_sha1"] = hashlib.sha1(norm.encode("utf-8")).hexdigest()
    if warnings:
        d["fm_warnings"] = warnings
    url = fm.get("url")
    if isinstance(url, str) and url.strip():
        d["url_norm"] = normalise_url(url)
        d["domain"] = registrable(url)
        if is_bare_domain(d["url_norm"]):
            d["bare_domain"] = True
    tail = norm[-400:]
    if not CHROME_RE.search(tail) and not ADJUDICATED_15_RE.search(norm):
        hits = []
        if WALL_RE.search(tail):
            hits.append("wall")
        if ELISION_RE.search(norm[-60:]):
            hits.append("elision")
        if hits:
            d["trunc_markers"] = hits
    if parts[0] == "wiki":
        d["sections"] = _sections(norm)
    return {"path": rel, "fm": fm, "d": d}, body


def _links(row, body_text):
    """Edge list rows: frontmatter citations and body wikilinks.

    Separate from the file row because lint #4 (orphans and dead links) is the
    check that is genuinely graph-shaped, and a per-file row cannot hold a graph.
    """
    out = []
    src = row["path"]
    fm = row["fm"]
    for via in ("sources", "entities", "cite_through", "artefact"):
        for target in as_list(fm.get(via)):
            t = str(target).strip()
            if t:
                out.append({"from": src, "to": t.split("|")[0].split("#")[0],
                            "via": via, "line": 0})
    if body_text:
        for n, line in enumerate(body_text.split("\n"), 1):
            for target in WIKILINK_RE.findall(line):
                t = target.strip()
                if t:
                    out.append({"from": src, "to": t.split("#")[0].strip(),
                                "via": "body", "line": n})
    return out


def build_index(roots=INDEX_ROOTS, db=False, quiet=True):
    """Rebuild `index/` from scratch. The only writer there is."""
    t0 = time.time()
    os.makedirs(INDEX_DIR, exist_ok=True)
    files, links = [], []
    mtime_max, warn_files = 0, 0
    for rel, ap in _walk(roots):
        try:
            st = os.stat(ap)
        except OSError:
            continue                                    # vanished mid-walk; next build gets it
        mtime_max = max(mtime_max, st.st_mtime)   # float, to match index_state()
        text = ""
        if rel.lower().endswith(".md"):
            text = open(ap, "rb").read().decode("utf-8", "replace")
        row, body = _row(rel, st, text)
        files.append(row)
        if row["d"].get("fm_warnings"):
            warn_files += 1
        if row["d"]["ext"] == ".md":
            links.extend(_links(row, body))

    _write_jsonl(FILES_JSONL, files)
    _write_jsonl(LINKS_JSONL, links)
    meta = {"version": INDEX_VERSION,
            "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "built_epoch": int(time.time()),
            "roots": list(roots),
            "files": len(files),
            "links": len(links),
            "mtime_max": mtime_max,
            "fm_warning_files": warn_files,
            "build_seconds": round(time.time() - t0, 2)}
    with open(META_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=2)
        fh.write("\n")
    if db:
        build_db(files, links)
        meta["db"] = True
    elif os.path.exists(DB_PATH):
        # The DB is a scratch cache of these two files, and `db=False` is the
        # default, so a rebuild that does not refresh it would leave a copy of
        # the *previous* vault on disk wearing a plausible filename. Its only
        # reader (`build-index.py --sql`) rebuilds it when it is missing or
        # older than the JSONL, so nothing breaks by removing it -- and the
        # index stops carrying an artefact whose mtime means nothing.
        os.remove(DB_PATH)
    if not quiet:
        print(f"index: {len(files):,} files, {len(links):,} links, "
              f"{meta['build_seconds']}s")
    return meta


def _write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Freshness and loading
# --------------------------------------------------------------------------- #

def index_state(roots=INDEX_ROOTS):
    """('fresh'|'missing'|'stale-version'|'stale', meta|None, reason).

    The check is a stat sweep over the indexed roots — about a fifth of a second
    over 10k files, against a rebuild of about a second. Cheap enough that every
    consumer can afford it on every call, which pays for the index not being
    committed.

    It does not make a stale read impossible, and saying so here was wrong: this
    compares a high-water mark, so a file whose new mtime lands *below* the tree's
    newest mtime is invisible to it, and the file count catches only additions and
    deletions. A batched pass rewriting files in place read `fresh` over 700 of its
    own writes on 2026-09-08. Force `build_index()` after a bulk in-place rewrite.
    """
    if not (os.path.exists(FILES_JSONL) and os.path.exists(META_JSON)):
        return "missing", None, "no index/"
    try:
        meta = json.load(open(META_JSON, encoding="utf-8"))
    except (ValueError, OSError):
        return "missing", None, "meta.json unreadable"
    if meta.get("version") != INDEX_VERSION:
        return "stale-version", meta, f"built by v{meta.get('version')}, now v{INDEX_VERSION}"
    if list(meta.get("roots", [])) != list(roots):
        return "stale", meta, "roots changed"
    n, newest = 0, 0
    for _rel, ap in _walk(roots):
        try:
            st = os.stat(ap)
        except OSError:
            continue
        n += 1
        newest = max(newest, st.st_mtime)   # not int(): truncation hid sub-second rewrites
    if n != meta.get("files"):
        return "stale", meta, f"{n:,} files on disk, {meta.get('files'):,} in index"
    if newest > meta.get("mtime_max", 0):
        return "stale", meta, "a file changed since the build"
    return "fresh", meta, ""


def ensure_fresh(roots=INDEX_ROOTS, db=False, quiet=True):
    state, meta, reason = index_state(roots)
    if state != "fresh":
        if not quiet:
            print(f"index {state} ({reason}) - rebuilding", file=sys.stderr)
        return build_index(roots, db=db, quiet=quiet)
    return meta


def load_index(auto=True, quiet=True):
    """[row, ...] — every indexed artefact. Rebuilds first if the vault moved."""
    if auto:
        ensure_fresh(quiet=quiet)
    with open(FILES_JSONL, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_links(auto=True, quiet=True):
    if auto:
        ensure_fresh(quiet=quiet)
    with open(LINKS_JSONL, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def slug_map(rows=None):
    """slug -> [path, ...]. What a `[[wikilink]]` resolves against."""
    out = {}
    for r in rows if rows is not None else load_index():
        out.setdefault(r["d"]["slug"], []).append(r["path"])
    return out


# --------------------------------------------------------------------------- #
# SQLite (a cache of the JSONL, never a store)
# --------------------------------------------------------------------------- #

def build_db(files=None, links=None, path=DB_PATH):
    """Flatten the rows into `index/vault.db` for ad-hoc SQL.

    The hot path never needs this — 10k rows load from JSONL in well under a
    second. It exists so a one-off question is one SQL line instead of one more
    single-use script in `scripts/`.
    """
    import sqlite3
    if files is None:
        files = load_index()
    if links is None:
        links = load_links()
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE files (path TEXT PRIMARY KEY, slug TEXT, kind TEXT, folder TEXT,
            shard TEXT, file_date TEXT, ext TEXT, title TEXT, url TEXT, url_norm TEXT,
            domain TEXT, publisher TEXT, published TEXT, date_precision TEXT,
            date_source TEXT, ingested TEXT, last_reviewed TEXT, status TEXT,
            body_completeness TEXT, origin_status TEXT, deal_id TEXT,
            retired_deal_id TEXT, financier_slug TEXT, recipient_slug TEXT,
            primary_subject TEXT, finance_origin TEXT, words INTEGER, bytes INTEGER,
            mtime INTEGER, body_sha1 TEXT, has_hub_line INTEGER, bare_domain INTEGER,
            trunc_markers TEXT, fm_warnings TEXT, fm_keys TEXT);
        CREATE TABLE facets (path TEXT, facet TEXT, value TEXT);
        CREATE TABLE links (src TEXT, dst TEXT, via TEXT, line INTEGER);
        """)
    cols = [c.strip().split()[0] for c in
            "path slug kind folder shard file_date ext title url url_norm domain publisher "
            "published date_precision date_source ingested last_reviewed status "
            "body_completeness origin_status deal_id retired_deal_id financier_slug "
            "recipient_slug primary_subject finance_origin words bytes mtime body_sha1 "
            "has_hub_line bare_domain trunc_markers fm_warnings fm_keys".split()]
    frows, facets = [], []
    for r in files:
        fm, d, p = r["fm"], r["d"], r["path"]
        v = {"path": p, "title": fm.get("title") if isinstance(fm.get("title"), str) else None,
             "url": fm.get("url") if isinstance(fm.get("url"), str) else None,
             "has_hub_line": 1 if fm.get("hub_line") else 0,
             "bare_domain": 1 if d.get("bare_domain") else 0,
             "trunc_markers": ",".join(d.get("trunc_markers", [])) or None,
             "fm_warnings": ";".join(d.get("fm_warnings", [])) or None,
             "fm_keys": ",".join(sorted(fm))}
        for k in ("slug", "kind", "folder", "shard", "file_date", "ext", "words",
                  "bytes", "mtime", "body_sha1", "url_norm", "domain"):
            v.setdefault(k, d.get(k))
        for k in ("publisher", "published", "date_precision", "date_source", "ingested",
                  "last_reviewed", "status", "body_completeness", "origin_status",
                  "deal_id", "retired_deal_id", "financier_slug", "recipient_slug",
                  "primary_subject", "finance_origin"):
            val = fm.get(k)
            v.setdefault(k, val if isinstance(val, (str, int, float)) else None)
        frows.append(tuple(v.get(c) for c in cols))
        for facet in ("places", "topics", "entities", "lens", "sources"):
            for item in as_list(fm.get(facet)):
                facets.append((p, facet, str(item)))
    con.executemany(f"INSERT OR REPLACE INTO files ({','.join(cols)}) "
                    f"VALUES ({','.join('?' * len(cols))})", frows)
    con.executemany("INSERT INTO facets VALUES (?,?,?)", facets)
    con.executemany("INSERT INTO links VALUES (?,?,?,?)",
                    [(l["from"], l["to"], l["via"], l["line"]) for l in links])
    con.executescript("""
        CREATE INDEX idx_files_url ON files(url_norm);
        CREATE INDEX idx_files_kind ON files(kind);
        CREATE INDEX idx_files_pub ON files(published);
        CREATE INDEX idx_files_deal ON files(deal_id);
        CREATE INDEX idx_facets_v ON facets(facet, value);
        CREATE INDEX idx_facets_p ON facets(path);
        CREATE INDEX idx_links_dst ON links(dst);
        CREATE INDEX idx_links_src ON links(src);
        """)
    con.commit()
    con.close()
    return path


TAXONOMY_PATH = os.path.join(ROOT, "lookups", "taxonomy.md")


def load_taxonomy(path=None):
    """(order, label, l1_of) parsed from `lookups/taxonomy.md`'s Level-1/Level-2 vocabulary.

    `order[slug] = (l1_index, l2_index)` is the sort key every report render uses so a
    section's rows follow the taxonomy's own order rather than CSV row order or however a
    run happened to add them. `label[slug]` is the Level-2 description ("Connectivity"),
    used for report sub-headings. `l1_of[slug]` is the Level-1 category label ("ICT
    Infrastructure"). One parser, because report-render.py and any future taxonomy-ordered
    view both need the same order and the same labels."""
    path = path or TAXONOMY_PATH
    order, label, l1_of = {}, {}, {}
    l1_idx = l2_idx = -1
    current_l1 = None
    in_vocab = False
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith("## "):
                in_vocab = line.strip() == "## Vocabulary"
                continue
            if not in_vocab:
                continue
            m1 = re.match(r"^### (.+)$", line)
            if m1:
                l1_idx += 1
                l2_idx = -1
                current_l1 = m1.group(1).strip()
                continue
            m2 = re.match(r"^- `([a-z.]+)` — (.+)$", line)
            if m2 and current_l1 is not None:
                l2_idx += 1
                slug, lbl = m2.group(1), m2.group(2).strip()
                # A few entries (dpi.registry) carry a long editorial gloss after the
                # first sentence — take the description, not the annotation, so a label
                # used as a report sub-heading stays a heading rather than a paragraph.
                lbl = re.split(r"\.\s", lbl, maxsplit=1)[0].strip()
                order[slug] = (l1_idx, l2_idx)
                label[slug] = lbl
                l1_of[slug] = current_l1
    return order, label, l1_of


def blank_csv_row(row):
    """True for a csv.DictReader row that carries nothing.

    Opening a CSV in an editor can leave a trailing newline, which DictReader returns as a row of
    empty strings — and against a header the file predates, the surplus field arrives under the
    `None` restkey as a *list*, so a naive `.strip()` over `row.values()` raises. Both cases are
    the same fact: the row is not data. One copy, because three report scripts need it and a
    header-only shell plus one phantom row reads as an initialised country."""
    for v in row.values():
        for cell in (v if isinstance(v, list) else [v]):
            if (cell or "").strip():
                return False
    return True
