#!/usr/bin/env python3
"""author-meta.py — the people a piece names as its authors, read from the page itself.

Reads, in this order, and stops at the first that names anyone:
  1. `citation_author` meta (Highwire / Google Scholar; journals and repositories) — every author, in order;
  2. JSON-LD `author` on an Article, NewsArticle, BlogPosting, Report, ScholarlyArticle or WebPage node;
  3. `<meta name="author">`, `article:author` (unless a URL), `parsely-author`, `sailthru.author`, `dc.creator`;
  4. a visible byline (`rel=author`, `.byline`, `.author-name`, and trafilatura's own byline reader).
The stored text is read first by `from_body()`, and the page only where that finds nothing.

A dead page (network error, 4xx/5xx) is retried once from the Wayback Machine's closest snapshot.
What comes back is the raw strings as the page gives them; `authors-normalise.py` turns them into `author:` / `byline:`.

    python scripts/author-meta.py --url URL                     # one page, prints JSON (ingest)
    python scripts/author-meta.py --in urls.csv --out res.jsonl # batch: csv with path,url; resumes
    python scripts/author-meta.py --apply raw/2026/x.md ...     # ingest: set author:, byline:, author_roles:

`--apply` reads `lookups/publications.csv` for the outlet's kind and touches only authored kinds
(newspaper, trade, agency, academic, thinktank, ngo, self). It exits 2 where a file's domain has no row:
add the row, then run it again. Fields: `wiki/schemas.md` §4 → Authors.
"""
import argparse, concurrent.futures as cf, csv, json, os, re, sys, threading, time
import html as html_lib
import urllib3
from lxml import html as LH

urllib3.disable_warnings()
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
HTTP = urllib3.PoolManager(num_pools=200, maxsize=4, cert_reqs="CERT_NONE",
                           headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                    "Accept-Language": "en,fr;q=0.8,pt;q=0.6"})
MAX = 4_000_000
ART = re.compile(r"(Article|BlogPosting|Report|ScholarlyArticle|WebPage|Posting|Thesis|CreativeWork)$", re.I)


def fetch(url, timeout=25):
    """(status, final_url, html) — html is '' for a non-HTML or failed fetch."""
    try:
        r = HTTP.request("GET", url, timeout=urllib3.Timeout(connect=10, read=timeout),
                         retries=urllib3.Retry(total=2, redirect=6, raise_on_status=False),
                         preload_content=False)
        ct = (r.headers.get("Content-Type") or "").lower()
        data = r.read(MAX, decode_content=True)
        url = getattr(r, "url", None) or url
        r.release_conn()
        if r.status >= 400:
            return r.status, url, ""
        if "html" not in ct and not data.lstrip()[:200].lower().startswith((b"<!doctype", b"<html")):
            return r.status, url, "" if "pdf" not in ct else "%PDF"
        enc = r.headers.get("Content-Type", "").split("charset=")[-1].split(";")[0].strip() if "charset=" in ct else "utf-8"
        try:
            return r.status, url, data.decode(enc or "utf-8", errors="replace")
        except LookupError:
            return r.status, url, data.decode("utf-8", errors="replace")
    except Exception as e:  # network, TLS, timeout
        return 0, url, ""


def wayback(url):
    st, _, body = 0, url, ""
    try:
        r = HTTP.request("GET", "https://archive.org/wayback/available?url=" + urllib3.util.parse_url(url).url,
                         timeout=20, retries=1)
        snap = json.loads(r.data.decode("utf-8", "replace")).get("archived_snapshots", {}).get("closest", {})
        if snap.get("available") and snap.get("url"):
            s = re.sub(r"/web/(\d+)/", r"/web/\1id_/", snap["url"], count=1)
            st, _, body = fetch(s)
            return st, s, body
    except Exception:
        pass
    return 0, url, ""


def _names(v):
    """Strings from a JSON-LD author value (str, dict, list)."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        n = v.get("name")
        if isinstance(n, list):
            n = " ".join(map(str, n))
        if not n and (v.get("givenName") or v.get("familyName")):
            n = f"{v.get('givenName','')} {v.get('familyName','')}".strip()
        return [n] if isinstance(n, str) and n else []
    if isinstance(v, list):
        return [x for i in v for x in _names(i)]
    return []


def _jsonld(doc):
    out = []
    for s in doc.xpath('//script[contains(@type,"ld+json")]/text()'):
        try:
            d = json.loads(s.strip().rstrip(";"))
        except Exception:
            continue
        stack = [d]
        while stack:
            x = stack.pop()
            if isinstance(x, list):
                stack.extend(x); continue
            if not isinstance(x, dict):
                continue
            if "@graph" in x:
                stack.append(x["@graph"])
            t = x.get("@type")
            t = " ".join(t) if isinstance(t, list) else str(t or "")
            if ART.search(t) and x.get("author"):
                out += _names(x["author"])
    return out


def _meta(doc, *keys):
    vals = []
    for k in keys:
        vals += doc.xpath(f'//meta[translate(@name,"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz")="{k}"]/@content')
        vals += doc.xpath(f'//meta[@property="{k}"]/@content')
    return [v.strip() for v in vals if v and v.strip()]


def page_title(page):
    """og:title, else <title> — what `authors-normalise.py` matches against the stored title."""
    try:
        doc = LH.fromstring(page)
    except Exception:
        return ""
    t = _meta(doc, "og:title", "citation_title") or [x.strip() for x in doc.xpath("//title/text()") if x.strip()]
    return t[0][:200] if t else ""


def from_html(page, url=""):
    """(authors, how) from a page's HTML."""
    try:
        doc = LH.fromstring(page)
    except Exception:
        return [], ""
    a = _meta(doc, "citation_author", "dc.creator", "dcterms.creator") if doc.xpath('//meta[@name="citation_title"]') else []
    if a:
        return a, "citation"
    a = _jsonld(doc)
    if a:
        return a, "jsonld"
    a = [v for v in _meta(doc, "author", "article:author", "parsely-author", "sailthru.author", "dc.creator", "twitter:creator")
         if not v.startswith(("http", "@", "www."))]
    if a:
        return a[:1] if len(set(a)) > 1 and len(a) > 3 else list(dict.fromkeys(a)), "meta"
    a = [t.strip() for t in doc.xpath('//a[@rel="author"]//text() | //*[contains(@class,"author-name") or contains(@class,"byline__name") or @itemprop="author"]//text()') if t.strip()]
    if a:
        return list(dict.fromkeys(a))[:6], "byline"
    try:
        import trafilatura
        m = trafilatura.extract_metadata(page, default_url=url)
        if m and m.author:
            return [m.author], "trafilatura"
    except Exception:
        pass
    return [], ""


BY = re.compile(r"^\s*(?:[*_#>\s]*)(?:by|par|por|written by|auteur|author|authors|auteurs)\s*[:\-–]?\s+(?P<n>[A-ZÀ-Ý][^\n|]{2,120}?)\s*[*_]*\s*$", re.I | re.M)


def from_body(body):
    """Byline from the stored text: a `By X` / `Par X` / `Author: X` line near the top."""
    head = "\n".join(body.splitlines()[:60])
    m = BY.search(head)
    if not m:
        return [], ""
    n = re.sub(r"\s*[\|•·,]\s*(\d{1,2}\s+\w+\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}-\d\d-\d\d).*$", "", m.group("n"))
    n = re.sub(r"\]\(.*?\)|[\[\]*_]", "", n).strip(" .-–")
    if not n or len(n.split()) > 14 or re.search(r"\b(the|this|our|using|which|of the)\b", n.split(",")[0], re.I) and len(n.split()) > 6:
        return [], ""
    return [n], "body"


# --------------------------------------------------------------------------- #
# Normalising: raw byline strings -> (people, non-person byline)
# --------------------------------------------------------------------------- #

HONORIFIC = re.compile(r"^(?:(?:H\.?E\.?|His Excellency|Her Excellency|S\.?E\.?|Hon(?:ourable)?\.?|Rt\.? Hon\.?|Dr\.?|Prof(?:essor)?\.?|Pr\.?|Mr\.?|Mrs\.?|Ms\.?|Miss|Mme\.?|Mlle\.?|M\.|Me\.?|Sir|Dame|Rev(?:erend)?\.?|Eng\.?|Engr\.?|Ing\.?|Arch\.?|Amb\.?|Ambassador|Chief|Alhaji|Alh\.?|Hajia|Sheikh|Col\.?|Gen\.?|Maj\.?|Capt\.?|Lt\.?)\s+)+", re.I)
SPLIT = re.compile(r"\s*(?:;|\||\s&\s|\b(?:and|And|AND|et|ET|e|y|with|avec|com|na)\b|,)\s*")
NONPERSON = re.compile(r"\b(staff|editor(?:s|ial)?|r[ée]daction|redac|admin(?:istrator)?|team|desk|newsroom|correspondents?|reporters?|contributors?|guest|writer|webmaster|journalist|communication|communiqu[ée]|press|presse|media|m[ée]dias|news|nouvelles|not[ií]cias|agency|agence|ag[êe]ncia|online|digital|times|daily|herald|post|tribune|journal|magazine|review|radio|tv|television|t[ée]l[ée]vision|channel|group|groupe|grupo|ltd|limited|inc|llc|llp|plc|sa|sarl|corp|company|bank|banque|banco|ministry|minist[èe]re|minist[ée]rio|government|gouvernement|governo|department|office|bureau|unit|authority|autorit[ée]|commission|council|conseil|secretariat|programme|program|project|projet|initiative|foundation|fondation|institute|institut|instituto|university|universit[ée]|universidade|centre|center|association|network|r[ée]seau|forum|union|alliance|partnership|coalition|society|organisation|organization|world|africa|afrique|[áa]frica|african|africain|international|national|global|nations|consulting|partners|associates|solutions|technologies|systems|services|research|policy|lab|labs|hub|platform|wire|aps|afp|reuters|xinhua|bloomberg|apa|pana|map|mena|angop|anp|acp|aip|agp|ani|gna|nan|tap|aps|anadolu|sputnik|allafrica|rfi|bbc|cnn|apo|prnewswire|businesswire|wam|kna|ena|suna|lusa|efe|dpa|ips|unknown|anonymous|author|auteur|autor|[ée]quipe|waandishi|mwandishi|wetu|wandishi|comms|analyst|analysts|wire|mediapart)\b", re.I)
PARTICLE = {"de","da","do","dos","das","du","des","van","von","der","den","el","al","bin","ibn","ben","bint","la","le","di","del","y","wa","ould","ag","mac","st","st."}
NAMEWORD = re.compile(r"^(?:[A-ZÀ-ÖØ-ÞĀ-Ž][\w'’.\-À-ÿĀ-ž]*|[A-Z]\.(?:[A-Z]\.)*|O[’']\w+|Mc\w+|d[’']\w+|[a-z]{1,4})$")


def _clean(s):
    s = html_lib.unescape(html_lib.unescape(s)).replace(" ", " ")
    s = re.sub(r"<[^>]+>|https?://\S+|\S+@\S+|@\w+", " ", s)
    s = re.sub(r"\((?:[^)]*)\)", " ", s)                      # bracketed notes: (PDF metadata), (photos …)
    s = re.sub(r"^\s*(?:by|par|por|written by|posted by|author|auteur|autor|authors|auteurs)\s*[:\-–]?\s+", "", s, flags=re.I)
    s = re.sub(r"\s+[—–-]\s+.*$", "", s)                     # "Name — Outlet — date"
    s = re.sub(r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+\w+,?\s+\d{4}|\w+\s+\d{1,2},?\s+\d{4}|\d{4}-\d\d-\d\d|\d+\s+min read.*)$", "", s, flags=re.I)
    s = re.sub(r"\bet al\.?", "", s, flags=re.I)
    s = re.sub(r"\s+(?:posted\s+)?(?:on|le|du|em|el|publi[ée] le)\s+(?:\d|janv|f[ée]v|mars|avr|mai|juin|juil|ao[uû]|sept|oct|nov|d[ée]c|jan|feb|mar|apr|may|jun|jul|aug|sep|dec).*$", "", s, flags=re.I)
    s = re.sub(r"\s+posted\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+(?:on|le|du|em|el)\s*[,.]?\s*$", "", s)
    s = re.sub(r"[.,]?\s*\b(?:edited|translated|reviewed|photos?|illustrations?|additional reporting|with reporting)\s+by\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip(" ,:;-–—*_\"'")
    s = re.sub(r"(?<![A-Z])\.+$", "", s).strip(" ,:;-–—·")
    return "" if s.lower() in ("par", "por", "by", "de", "written", "posted", "log", "auteur", "author") else s


def is_person(n):
    w = n.split()
    if not 2 <= len(w) <= 5 or re.search(r"\d", n) or NONPERSON.search(n):
        return False
    if re.fullmatch(r"[A-Z]{2,4}", w[0]):
        return False                                         # DRF Comms, ONEP: an acronym leads
    caps = [x for x in w if x.lower() not in PARTICLE]
    if len(caps) < 2 or not all(NAMEWORD.match(x) for x in caps):
        return False
    return not (n.isupper() and len(n) <= 6)                 # an acronym


def _case(n):
    """A word printed in capitals is title-cased (BBALIGOJJA -> Bbaligojja); initials stay."""
    return " ".join(x.title() if x.isupper() and len(x.replace(".", "")) > 2 else x for x in n.split())


def _inverted(s, citation):
    """'Heeks, Richard' / 'LARIZGOITIA JAUREGUI, Iciar' -> 'Richard Heeks': a citation_author value
    always, elsewhere only where the surname side is in capitals (the bibliographic convention)."""
    m = re.fullmatch(r"([^,]{2,60}),\s*([^,]{1,40})", s)
    if not m:
        return s
    last, first = m.group(1).strip(), m.group(2).strip()
    if NONPERSON.search(s) or len(first.split()) > 3 or len(last.split()) > 3:
        return s
    if citation or (last.isupper() and not first.isupper()):
        return f"{first} {last}"
    return s


def _is_outlet(p, publication, domain):
    """'New Dawn' on The New Dawn, 'Addis Insight' on addisinsight.net: the outlet, not a writer."""
    toks = {t for t in re.findall(r"\w{2,}", p.lower())}
    ptoks = {t for t in re.findall(r"\w{2,}", (publication or "").lower())}
    label = re.sub(r"[^a-z0-9]", "", (domain or "").split(".")[0].lower())
    flat = re.sub(r"[^a-z0-9]", "", p.lower())
    return bool(toks) and (toks <= ptoks or (len(flat) > 4 and (flat in label or label and label in flat)))


def normalise(strings, publication="", citation=False, domain=""):
    """(people, byline): people as printed, honorifics off, deduplicated in order; byline the
    non-person credit ('' where people were found or nothing was given)."""
    people, other = [], []
    for raw in strings:
        if not isinstance(raw, str) or not raw.strip():
            continue
        s = _inverted(_clean(raw), citation)
        if not s:
            continue
        # "Name, Outlet" / "Name, Kenya Correspondent": keep the head where the head is a person
        parts = [p for p in SPLIT.split(s) if p and p.strip()]
        got = []
        for p in parts:
            p = HONORIFIC.sub("", re.sub(r"(?<![A-Z])\.$", "", p.strip())).strip()
            if is_person(p) and not _is_outlet(p, publication, domain):
                got.append(_case(p))
            elif got and (NONPERSON.search(p) or (publication and p.lower() in publication.lower())):
                continue                                     # trailing outlet/role after a name
            elif got:
                continue
            else:
                other.append(raw.strip())
                break
        for g in got:
            if g not in people:
                people.append(g)
    if people:
        return people, ""
    byl = _clean(other[0]) if other else ""
    return [], byl[:120]


POSWORD = re.compile(r"\b(director|head|chief|officer|manager|lead|leader|editor|professor|lecturer|researcher|fellow|associate|analyst|adviser|advisor|consultant|specialist|coordinator|founder|co-founder|ceo|cto|coo|chair|chairman|chairperson|president|vice|secretary|minister|partner|counsel|lawyer|attorney|economist|scientist|engineer|expert|student|candidate|programme|program|policy|senior|junior|principal|deputy|executive|correspondent|reporter|journalist|writer|commissioner|governor|ambassador|representative|directeur|directrice|chef|responsable|chercheur|chercheuse|professeur|enseignant|conseiller|conseill[eè]re|chargé|chargée|fondateur|fondatrice|président|présidente|secrétaire|ministre|avocat|avocate|ingénieur|analyste|doctorant|doctorante|diretor|diretora|investigador|investigadora)\b", re.I)


ROLE_VERB = re.compile(r",?\s+(?P<v>is|was|serves as|est|é)\s+(?:currently\s+|actuellement\s+)?(?:(?:a|an|the|le|la|un|une|o|um|uma)\s+|l['’])?(?P<rest>[^.;:\n()]{5,220})")
ROLE_STOP = re.compile(r",\s+(?:where|and|a|an|which|who|based|with|où|et|qui)\b|\s+(?:where|who|focusing|with over|based in|since|depuis|currently)\b")
SEP_EN = [re.compile(r"\s+at\s+(?:the\s+)?"), re.compile(r"\s+with\s+(?:the\s+)?"), re.compile(r"\s+(?:of|for|in)\s+(?:the\s+)?")]
SEP_FR = [re.compile(r"\s+chez\s+"), re.compile(r"\s+(?:à\s+la|à\s+l['’]|au|aux|à)\s+"), re.compile(r"\s+(?:de\s+la|de\s+l['’]|du|des|de|da|do)\s+")]
ROLE_NOT = re.compile(r"\b(said|says|told|added|according|announced|déclaré|indiqué|expected|set to|likely)\b", re.I)


def roles_from_body(body, people):
    """`Name | Position | Organisation` for each author whose post the piece itself states:
    a bio line — "X is Director of Y at Z", "X est chercheur au Z". Nothing is inferred.
    The split is on the last "at" ("Professor of AI at Umeå University"), else the first "of"."""
    out = []
    text = re.sub(r"[*_]{1,3}", "", body)
    for n in people:
        m = re.search(r"\b" + re.escape(n) + r"\s*(?:\([^)]*\)\s*)?" + ROLE_VERB.pattern, text)
        if not m:
            continue
        rest = ROLE_STOP.split(m.group("rest"))[0].strip(" ,")
        seps = SEP_FR if m.group("v") in ("est", "é") else SEP_EN
        pos = org = ""
        for i, sep in enumerate(seps):
            hits = list(sep.finditer(rest))
            if hits:
                h = hits[-1] if i < 2 else hits[0]
                pos, org = rest[:h.start()], rest[h.end():]
                break
        pos, org = pos.strip(" ,"), org.strip(" ,")
        if not pos or not org or not org[0].isupper() or not POSWORD.search(pos):
            continue
        if len(pos.split()) > 12 or len(org.split()) > 10 or ROLE_NOT.search(pos):
            continue
        out.append(f"{n} | {pos[0].upper() + pos[1:]} | {org}")
    return out


# --------------------------------------------------------------------------- #
# Writing the fields
# --------------------------------------------------------------------------- #

SPECIAL = re.compile(r"""^[\s\-?:,\[\]{}#&*!|>'"%@`]|:\s|\s#|\s$|^$""")


def _q(v):
    return json.dumps(v, ensure_ascii=False) if SPECIAL.search(v) else v


def write_fields(path, people, byline="", roles=None, checked=True):
    """Set `author:` (people, '; '-joined), `byline:` and `author_roles:` in one file's frontmatter.

    Replaces existing `author:` / `byline:` / `author_roles:` lines in place; a new field goes after
    `publisher:`. `checked=False` with no people writes nothing (never checked stays absent).
    Keeps the file's own line ending. Returns True where the file changed.
    """
    raw = open(path, "rb").read()
    t = raw.decode("utf-8")
    nl = "\r\n" if "\r\n" in t[:t.find("\n") + 1] else "\n"
    if not t.startswith("---"):
        return False
    end = t.find(nl + "---", 3)
    if end < 0:
        return False
    head = t[:end].split(nl)
    if not people and not checked:
        return False
    new = []
    if people or checked:
        new.append("author: " + _q("; ".join(people)) if people else 'author: ""')
    if byline and not people:
        new.append("byline: " + _q(byline))
    if roles:
        new.append("author_roles:")
        new += ["  - " + json.dumps(r, ensure_ascii=False) for r in roles]
    out, i, placed = [], 0, False
    while i < len(head):
        ln = head[i]
        if re.match(r"^(author|byline|author_roles):", ln):
            i += 1
            while i < len(head) and re.match(r"^\s+(-\s|\S)", head[i]) and not re.match(r"^\S", head[i]):
                i += 1                                   # its continuation / block items
            if not placed:
                out += new; placed = True
            continue
        out.append(ln)
        i += 1
        if not placed and re.match(r"^publisher:", ln):
            while i < len(head) and head[i][:1] in (" ", "\t"):
                out.append(head[i]); i += 1
            out += new; placed = True
    if not placed:
        out += new
    t2 = nl.join(out) + t[end:]
    if t2 == t:
        return False
    try:
        import yaml
        yaml.safe_load(nl.join(out[1:]))
    except ImportError:
        pass
    open(path, "wb").write(t2.encode("utf-8"))
    return True


def one(url):
    st, final, page = fetch(url)
    via = "live"
    if not page or page == "%PDF":
        if page == "%PDF":
            return {"url": url, "status": st, "via": "pdf", "authors": [], "how": ""}
        st2, final2, page2 = wayback(url)
        if page2 and page2 != "%PDF":
            st, final, page, via = st2, final2, page2, "wayback"
    if not page or page == "%PDF":
        return {"url": url, "status": st, "via": "dead", "authors": [], "how": ""}
    a, how = from_html(page, url)
    return {"url": url, "status": st, "via": via, "final": final, "title": page_title(page), "authors": a, "how": how}


# --------------------------------------------------------------------------- #
# One file, end to end (ingest)
# --------------------------------------------------------------------------- #

AUTHORED = {"newspaper", "trade", "agency", "academic", "thinktank", "ngo", "self"}
PUBS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lookups", "publications.csv")


def publications():
    return {r["domain"]: r for r in csv.DictReader(open(PUBS, encoding="utf-8"))}


def title_ok(a, b):
    """The fetched page is the stored piece: 40% of the shorter title's words in common."""
    import unicodedata
    tok = lambda s: set(re.findall(r"[a-z0-9]{4,}", unicodedata.normalize("NFKD", (s or "").lower())))
    A, B = tok(a), tok(b)
    return bool(A and B) and len(A & B) / min(len(A), len(B)) >= 0.4


def same_page(r, title):
    """The fetch landed on the stored piece: its title matches, or it was not redirected away
    (the final path is the requested one, and not a home page)."""
    if title_ok(r.get("title", ""), title):
        return True
    want = urllib3.util.parse_url(r["url"]).path or "/"
    got = r.get("final") or ""
    got = (urllib3.util.parse_url(got).path or "") if got.startswith("http") else got
    if r.get("via") == "wayback":
        got = re.sub(r"^/web/\d+id_/(?:https?://)?[^/]+", "", got or "")
    return len(want.strip("/")) > 3 and got.rstrip("/") == want.rstrip("/")


def apply(path, pubs=None, fetch_page=True):
    """Set the author fields on one source; returns what was done, as one word plus detail."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import vault_lib as V
    fm, _w, body = V.parse_frontmatter(open(path, encoding="utf-8", errors="replace").read())
    if fm.get("type") != "source":
        return "skip: not a source"
    pubs = pubs if pubs is not None else publications()
    dom = V.registrable(fm.get("url") or "")
    row = pubs.get(dom)
    if not row:
        return f"NO-ROW: {dom or '(no url)'} has no lookups/publications.csv row"
    if row["kind"] not in AUTHORED:
        return f"skip: {row['kind']} ({dom})"
    held = fm.get("author") if isinstance(fm.get("author"), str) else "; ".join(V.as_list(fm.get("author")))
    strings, cit, checked = ([held] if held and held.strip() else []), False, bool(held and held.strip())
    if not strings and isinstance(fm.get("byline"), str) and fm["byline"].strip():
        strings, checked = [fm["byline"]], True
    people, byl = normalise(strings, row["publication"], domain=dom) if strings else ([], "")
    if not people and not strings:
        people, byl = normalise(from_body(body)[0], row["publication"], domain=dom)
        if not people:
            byl = ""
    if not people and not strings and fetch_page and (fm.get("url") or "").startswith("http"):
        r = one(fm["url"])
        if r["via"] in ("live", "wayback") and same_page(r, fm.get("title", "")):
            checked = True
            people, byl = normalise(r["authors"], row["publication"], citation=r["how"] == "citation", domain=dom)
    checked = checked or bool(people)
    if not checked:
        return "unchecked: page dead, mismatched or not fetched"
    if byl and byl.lower().replace(" ", "") in (row["publication"].lower().replace(" ", ""), dom):
        byl = row["publication"]
    roles = roles_from_body(body, people) if people else []
    write_fields(path, people, byl, roles)
    return f"author: {'; '.join(people)}" if people else f"byline: {byl or '(none)'}"



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--apply", nargs="+", metavar="FILE", help="set author fields on these source files")
    ap.add_argument("--no-fetch", action="store_true", help="with --apply: stored text only")
    ap.add_argument("--extra", help="with --apply: a slice's own domain,publication,kind,country rows, read as if in publications.csv")
    ap.add_argument("--in", dest="inp")
    ap.add_argument("--out")
    ap.add_argument("--workers", type=int, default=24)
    a = ap.parse_args()
    if a.url:
        print(json.dumps(one(a.url), ensure_ascii=False)); return
    if a.apply:
        pubs, bad = publications(), 0
        if a.extra and os.path.exists(a.extra):
            for r in csv.DictReader(open(a.extra, encoding="utf-8")):
                if r.get("kind") and r.get("domain"):
                    pubs[r["domain"].strip()] = r
        for f in a.apply:
            res = apply(f, pubs, not a.no_fetch)
            bad += res.startswith("NO-ROW")
            print(f"{f}: {res}")
        sys.exit(2 if bad else 0)
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out, encoding="utf-8"):
            try: done.add(json.loads(l)["path"])
            except Exception: pass
    todo = [r for r in csv.DictReader(open(a.inp, encoding="utf-8")) if r["path"] not in done]
    print(f"{len(done)} done, {len(todo)} to fetch", flush=True)
    lock, n, t0 = threading.Lock(), 0, time.time()
    with open(a.out, "a", encoding="utf-8") as fh, cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, r["url"]): r for r in todo}
        for f in cf.as_completed(futs):
            r = futs[f]
            try:
                res = f.result()
            except Exception as e:
                res = {"url": r["url"], "status": -1, "via": "error", "authors": [], "how": str(e)[:80]}
            res["path"] = r["path"]
            with lock:
                fh.write(json.dumps(res, ensure_ascii=False) + "\n"); fh.flush()
                n += 1
                if n % 500 == 0:
                    print(f"{n}/{len(todo)} {time.time()-t0:.0f}s", flush=True)
    print("finished", n, flush=True)


if __name__ == "__main__":
    main()
