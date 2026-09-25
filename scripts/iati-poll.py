#!/usr/bin/env python3
"""iati-poll.py — the mechanical half of SWEEP-IATI.md.

Pulls ids for every activity, diffs against the master list, fetches metadata for the diff
alone, inherits a missing recipient country from the parent activity where one is declared,
applies the **geography** filter to the result, and writes a work order of survivors. Step 5 of
the procedure sets that order: inherit, then screen. It stops there:
**topic selection and record-building are judgement** and belong to the model, through
`wiki/finance-iati-driver.md`. A script that classified subjects from a code is the defect this
sweep was rebuilt to remove.

    python scripts/iati-poll.py --dry-run   # poll, report, write nothing
    python scripts/iati-poll.py             # work order + manifest, advance the master list
    python scripts/iati-poll.py --baseline  # rebuild the master list, select nothing
    python scripts/iati-poll.py --limit 40  # cap the work order

Exit 0 on a complete poll, 2 on an instrument failure — a nil is reportable only when the
instrument demonstrably ran (SWEEP-CYCLE.md).
"""
import argparse
import collections
import csv
import datetime
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vault_lib  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = vault_lib.ROOT
STATE = os.path.join(ROOT, "sweep", "donor", "iati")
MASTER = os.path.join(STATE, "last-poll-ids.txt")
PARTIAL = os.path.join(STATE, "pull-partial.tsv")        # ids so far, appended and fsynced per page
PARTIAL_MARK = os.path.join(STATE, "pull-partial.json")  # {date, cursor} — tiny, rewritten per page
API = "https://api.iatistandard.org/datastore/activity/select"

# The gateway 403s a default python-urllib User-Agent and wants a browser string.
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# IATI region codelist (vocabulary 1, replicated from OECD DAC/CRS):
# https://iatistandard.org/en/iati-standard/203/codelists/region/
# All seven African entries, which map one-to-one onto the seven African rows of
# countries.csv. 1028 "Middle Africa" is the UN M49 name for what the wiki calls Central
# Africa. 998 "Developing countries, unspecified" is deliberately absent: it is not African.
AFRICA_REGIONS = {
    "189": "XNA",    # North of Sahara, regional
    "289": "XSS",    # South of Sahara, regional
    "298": "XAF",    # Africa, regional
    "1027": "XEA",   # Eastern Africa, regional
    "1028": "XCA",   # Middle Africa, regional
    "1029": "XSA",   # Southern Africa, regional
    "1030": "XWA",   # Western Africa, regional
}

# IATI speaks ISO-2; countries.csv is ISO-3 and carries no ISO-2 column. The map lives here
# because it is this API's requirement, not the wiki's vocabulary.
ISO2_TO_ISO3 = {
    "AO": "AGO", "BI": "BDI", "BJ": "BEN", "BF": "BFA", "BW": "BWA", "CF": "CAF",
    "CI": "CIV", "CM": "CMR", "CD": "COD", "CG": "COG", "KM": "COM", "CV": "CPV",
    "DJ": "DJI", "DZ": "DZA", "EG": "EGY", "ER": "ERI", "EH": "ESH", "ET": "ETH",
    "GA": "GAB", "GH": "GHA", "GN": "GIN", "GM": "GMB", "GW": "GNB", "GQ": "GNQ",
    "KE": "KEN", "LR": "LBR", "LY": "LBY", "LS": "LSO", "MA": "MAR", "MG": "MDG",
    "ML": "MLI", "MZ": "MOZ", "MR": "MRT", "MU": "MUS", "MW": "MWI", "NA": "NAM",
    "NE": "NER", "NG": "NGA", "RW": "RWA", "SD": "SDN", "SN": "SEN", "SL": "SLE",
    "SO": "SOM", "SS": "SSD", "ST": "STP", "SZ": "SWZ", "SC": "SYC", "TD": "TCD",
    "TG": "TGO", "TN": "TUN", "TZ": "TZA", "UG": "UGA", "ZA": "ZAF", "ZM": "ZMB",
    "ZW": "ZWE",
}

PAGE = 1000     # ids per request on the full sweep
CHUNK = 100     # ids per metadata request — a 1,000-id q= would exceed the URL limit


def api_key(env_path=".env"):
    p = os.path.join(ROOT, env_path)
    if os.path.isfile(p):
        for ln in io.open(p, encoding="utf-8"):
            if ln.strip().startswith("IATI_API_KEY"):
                return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("IATI_API_KEY", "")


class ApiError(RuntimeError):
    """An API failure that says what went wrong.

    Solr puts the actual reason in `error.msg` and it is the whole diagnosis — "cursor
    functionality requires a sort containing a uniqueKey field tie breaker" is a one-line fix,
    where a bare `HTTPError` is a probe session. An error class name is not a diagnosis.
    """


def query(key, params, tries=6):
    """One Solr call. Backs off on Retry-After and gives up loudly rather than short-polling."""
    url = API + "?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={
            "Ocp-Apim-Subscription-Key": key, "User-Agent": UA, "Cache-Control": "no-cache"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < tries - 1:
                time.sleep(float(e.headers.get("Retry-After") or 2 ** attempt))
                continue
            detail = ""
            try:
                detail = json.loads(e.read().decode("utf-8", "replace"))["error"]["msg"]
            except Exception:                                       # noqa: BLE001
                pass
            raise ApiError(f"HTTP {e.code} {e.reason}" + (f" — {detail}" if detail else "")) from e
        except urllib.error.URLError as e:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise ApiError(f"unreachable: {e.reason}") from e
    raise ApiError("retries exhausted")


def load_partial(today):
    """A checkpoint from **today**, or nothing.

    An older partial describes a datastore that has moved on, and resuming into it would splice
    two walks — so it is ignored rather than repaired. Discarding a stale checkpoint costs one
    pull; resuming one costs a wrong master list, and a wrong master list is silent.
    """
    if not (os.path.isfile(PARTIAL) and os.path.isfile(PARTIAL_MARK)):
        return None
    try:
        mark = json.loads(io.open(PARTIAL_MARK, encoding="utf-8").read())
    except (ValueError, OSError):
        return None
    if mark.get("date") != today or not mark.get("cursor"):
        return None
    out, doc_of, seen = [], {}, set()
    for ln in io.open(PARTIAL, encoding="utf-8"):
        parts = ln.rstrip("\n").split("\t")
        if not parts[0] or parts[0] in seen:
            continue
        seen.add(parts[0])
        out.append(parts[0])
        if len(parts) > 1 and parts[1]:
            doc_of[parts[0]] = parts[1]
    return out, doc_of, mark["cursor"], seen


def clear_partial():
    for p in (PARTIAL, PARTIAL_MARK):
        if os.path.isfile(p):
            os.remove(p)


def all_ids(key, today, resume=True):
    """Every activity id, via cursorMark.

    **Not `start`/`rows`.** Deep paging by offset degrades badly and is capped on large result
    sets; a cursor over a sorted unique field is the only way to walk ~931k rows reliably. The
    document id rides along free — a second pass to get it would cost another ~950 requests.

    **Checkpointed per page**, because this is a ~950-request walk and a run killed at 90% should
    not start over. The page is written and fsynced **before** the cursor advances, so a run that
    dies between the two re-fetches one page and dedups it. That is the safe direction: a repeated
    page costs a request, a skipped one costs a silent hole in the master list.
    """
    resumed = load_partial(today) if resume else None
    if resumed:
        out, doc_of, cursor, seen = resumed
        print(f"  resuming from a checkpoint: {len(out):,} ids already pulled")
    else:
        clear_partial()
        out, doc_of, cursor, seen = [], {}, "*", set()
    seen_cursors = set()
    fh = io.open(PARTIAL, "a", encoding="utf-8", newline="\n")
    try:
        while True:
            # sort MUST be on `id`, the collection's uniqueKey: Solr rejects a cursor whose sort
            # carries no uniqueKey tie breaker, and `iati_identifier` is not it. (Measured 400,
            # 2026-08-04: "Cursor functionality requires a sort containing a uniqueKey field tie
            # breaker".) The walk order does not matter here — we take the whole set.
            r = query(key, {"q": "*:*", "fl": "iati_identifier,iati_activities_document_id",
                            "rows": PAGE, "wt": "json", "sort": "id asc",
                            "cursorMark": cursor})
            page = []
            for d in r["response"]["docs"]:
                i = d.get("iati_identifier")
                if not i or i in seen:
                    continue
                seen.add(i)
                out.append(i)
                doc = d.get("iati_activities_document_id")
                doc = (doc if isinstance(doc, str) else (doc[0] if doc else "")) or ""
                if doc:
                    doc_of[i] = doc
                page.append(i + "\t" + doc)
            if page:
                fh.write("\n".join(page) + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            nxt = r.get("nextCursorMark")
            print(f"\r  {len(out):,} ids", end="", flush=True)
            if not nxt or nxt == cursor or nxt in seen_cursors:
                break
            seen_cursors.add(cursor)
            cursor = nxt
            io.open(PARTIAL_MARK, "w", encoding="utf-8", newline="\n").write(
                json.dumps({"date": today, "cursor": cursor}))
    finally:
        fh.close()
    print()
    return out, doc_of


def metadata(key, ids):
    """Country, region, vocabulary, title and description for the diff — and only the diff.

    The flat Solr fields are correct here: selection needs presence and text and never pairs two
    parallel arrays. Pairing is parse 2's problem and parse 2 uses `iati_json`.
    """
    docs = []
    fl = ("iati_identifier,recipient_country_code,recipient_region_code,"
          "recipient_region_vocabulary,title_narrative,description_narrative,"
          "related_activity_ref,related_activity_type")
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        q = "iati_identifier:(%s)" % " OR ".join('"%s"' % c.replace('"', '') for c in chunk)
        r = query(key, {"q": q, "fl": fl, "rows": CHUNK, "wt": "json"})
        docs.extend(r["response"]["docs"])
        print(f"\r  metadata {min(i + CHUNK, len(ids)):,}/{len(ids):,}", end="", flush=True)
    if ids:
        print()
    return docs


def as_list(v):
    return [] if v is None else (v if isinstance(v, list) else [v])


def wiki_places():
    """The ISO-3 codes countries.csv actually carries — a place outside it is rejected by
    facets.md §1, so polling one would only produce a candidate lint #2 would reject."""
    out = set()
    with io.open(os.path.join(ROOT, "lookups", "countries.csv"),
                 encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            code = (row.get("iso-3") or "").strip()
            if code and not code.startswith("X"):
                out.add(code)
    return out


def geography(doc, places_held):
    """(places, region codes seen) — the mechanical filter. Places are ISO-3 or a wiki region."""
    places = []
    for c in as_list(doc.get("recipient_country_code")):
        iso3 = ISO2_TO_ISO3.get(str(c).strip().upper())
        if iso3 and iso3 in places_held:
            places.append(iso3)
    regions = [str(r).strip() for r in as_list(doc.get("recipient_region_code"))]
    for r in regions:
        if r in AFRICA_REGIONS:
            places.append(AFRICA_REGIONS[r])
    return sorted(set(places)), regions


def parent_refs(doc):
    """The parent activity ids this activity declares — related-activity type 1, and only that.

    SWEEP-IATI.md step 5 says screen geography **after** inheritance. A reporter that puts the
    recipient country on a transaction-less parent and the money on children that publish no
    country of their own — Sweden's `SE-0` is the standing example — loses every child to a
    geography screen that never looks up. Solr returns the two related-activity fields as
    parallel arrays, so they are paired by index and only where the lengths agree; where they
    do not, a lone type-1 against a lone ref is still unambiguous and anything else is skipped
    rather than guessed at.
    """
    refs = [str(r).strip() for r in as_list(doc.get("related_activity_ref")) if str(r).strip()]
    types = [str(t).strip() for t in as_list(doc.get("related_activity_type"))]
    if not refs or not types:
        return []
    if len(refs) == len(types):
        return [r for r, t in zip(refs, types) if t == "1"]
    if types.count("1") == 1 and len(refs) == 1:
        return refs
    return []


def load_master():
    if not os.path.isfile(MASTER):
        return set()
    return {ln.strip() for ln in io.open(MASTER, encoding="utf-8") if ln.strip()}


def save_master(ids):
    os.makedirs(STATE, exist_ok=True)
    with io.open(MASTER, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(ids) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--baseline", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--no-resume", action="store_true",
                    help="ignore any checkpoint and pull from the start")
    a = ap.parse_args()

    key = api_key()
    if not key:
        print("step=SWEEP-IATI stopped=error notes=no IATI_API_KEY", file=sys.stderr)
        return 2
    today = datetime.date.today().isoformat()
    os.makedirs(STATE, exist_ok=True)

    try:
        print("pulling every activity id...")
        ids, doc_of = all_ids(key, today, resume=not a.no_resume)
    except ApiError as exc:
        print(f"step=SWEEP-IATI stopped=error notes={exc}", file=sys.stderr)
        return 2
    if not ids:
        # An empty result on a query that cannot be empty is a claim about the tool.
        print("step=SWEEP-IATI stopped=error notes=empty id sweep", file=sys.stderr)
        return 2

    clear_partial()          # the pull completed; the checkpoint has done its job
    master = load_master()
    fresh = [i for i in ids if i not in master]
    print(f"{len(ids):,} ids pulled; master held {len(master):,}; {len(fresh):,} new")

    if a.baseline:
        if not a.dry_run:
            save_master(ids)
        print(f"step=SWEEP-IATI stopped=complete staged=0 dropped=0 remaining=0 "
              f"notes=baseline {len(ids)} ids")
        return 0

    docs = metadata(key, fresh) if fresh else []
    # A publisher that double-publishes one activity (Sida does) returns it twice here, and
    # both copies reached the work order through the orphan inheritance (R74). First wins.
    seen_ids = set()
    docs = [d for d in docs if not (d.get("iati_identifier") in seen_ids
                                    or seen_ids.add(d.get("iati_identifier")))]
    places_held = wiki_places()
    kept, region_census = [], collections.Counter()
    orphans = []
    for d in docs:
        vocabs = as_list(d.get("recipient_region_vocabulary")) or ["1"]
        places, regions = geography(d, places_held)
        for r in regions:
            region_census[(str(vocabs[0]), r)] += 1
        if places:
            kept.append({"id": d.get("iati_identifier"), "places": places,
                         "title": " ".join(as_list(d.get("title_narrative")))[:400],
                         "description": " ".join(as_list(d.get("description_narrative")))[:1200],
                         "dataset": doc_of.get(d.get("iati_identifier"), "")})
        elif parent_refs(d):
            orphans.append(d)

    # Step 5 of the procedure: inherit, then screen. An activity that publishes no country of
    # its own is not a claim that it has none — it is a claim that its parent holds it. One
    # extra metadata pull over the parents the orphans name settles it; without this the whole
    # of a hierarchical reporter's output is dropped unseen and the run reports a clean nil.
    inherited = 0
    if orphans:
        wanted = sorted({r for d in orphans for r in parent_refs(d)})
        print(f"{len(orphans):,} activities publish no country but name a parent; "
              f"pulling {len(wanted):,} parents")
        parent_places = {}
        for pd in metadata(key, wanted):
            pl, _ = geography(pd, places_held)
            if pl:
                parent_places[pd.get("iati_identifier")] = pl
        for d in orphans:
            pl = sorted({c for r in parent_refs(d) for c in parent_places.get(r, [])})
            if pl:
                inherited += 1
                kept.append({"id": d.get("iati_identifier"), "places": pl,
                             "title": " ".join(as_list(d.get("title_narrative")))[:400],
                             "description": " ".join(as_list(d.get("description_narrative")))[:1200],
                             "dataset": doc_of.get(d.get("iati_identifier"), ""),
                             "places_from": "parent"})
        print(f"  {inherited:,} inherited an African place from a parent")
    if a.limit:
        kept = kept[:a.limit]

    # Two different things, and the first version conflated them into one "unmapped" count. A
    # vocabulary-1 code that is not African is **correctly excluded** — 589 Middle East is not a
    # finding. A code in any other vocabulary is **unreadable**: a publisher on UN M49 writes
    # Africa as 002, and a DAC reading drops it silently. Only the second needs a ruling, and
    # reporting them together hides it inside a number that looks alarming and usually is not.
    other_region = {k: v for k, v in region_census.items()
                    if k[0] == "1" and k[1] not in AFRICA_REGIONS}
    unreadable = {k: v for k, v in region_census.items() if k[0] != "1"}

    # The census is a finding, not a mutation, so a dry run prints it too. Suppressing it would
    # hide the one check that says whether the geography filter is dropping Africa.
    print("\nregion codes across the diff — vocabulary, code, activities, mapped to:")
    for (voc, code), n in sorted(region_census.items(), key=lambda kv: -kv[1]):
        where = AFRICA_REGIONS.get(code, "not African") if voc == "1" else "UNREADABLE VOCABULARY"
        print(f"  {voc:<3} {code:<6} {n:>6}  {where}")
    if unreadable:
        print(f"** {sum(unreadable.values())} activities carry a region in a vocabulary this poll "
              "cannot read, and were dropped. Extend the mapping before trusting a nil.")

    if not a.dry_run:
        io.open(os.path.join(STATE, f"work-order-{today}.json"), "w", encoding="utf-8",
                newline="\n").write(json.dumps(kept, indent=1, ensure_ascii=False))
        with io.open(os.path.join(STATE, f"manifest-{today}.md"), "w", encoding="utf-8",
                     newline="\n") as fh:
            fh.write(f"# IATI poll — {today}\n\n")
            fh.write(f"- ids pulled: {len(ids):,}\n- master list held: {len(master):,}\n")
            fh.write(f"- diff: {len(fresh):,}\n- kept on geography: {len(kept):,}\n")
            fh.write("- topic selection and record-building are the model's, per "
                     "`wiki/finance-iati-driver.md`\n\n## Region codes seen across the diff\n\n")
            fh.write("| vocabulary | code | activities | mapped to |\n|---|---|---|---|\n")
            for (voc, code), n in sorted(region_census.items(), key=lambda kv: -kv[1]):
                fh.write(f"| {voc} | {code} | {n} | "
                         f"{AFRICA_REGIONS.get(code, 'not African') if voc == '1' else 'UNREADABLE'} |\n")
            if unreadable:
                fh.write(f"\n**{sum(unreadable.values())} activities carry a region in a vocabulary "
                         "this poll cannot read, and were dropped.** A publisher on UN M49 writes "
                         "Africa as `002`. Extend the vocabulary handling from this evidence rather "
                         "than from a code list. Vocabulary-1 codes marked *not African* are "
                         "correctly excluded and need nothing.\n")
        save_master(ids)

    print(f"\nregion codes: {len(region_census)} distinct, {len(other_region)} non-African, "
          f"{len(unreadable)} in an unreadable vocabulary")
    print(f"step=SWEEP-IATI stopped=complete staged={len(kept)} "
          f"dropped={len(fresh) - len(kept)} needs-clip=0 remaining=0 "
          f"notes={len(fresh)} new, {len(kept)} on geography, {inherited} inherited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
