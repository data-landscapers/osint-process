#!/usr/bin/env python3
"""
consolidate-budget-lines.py  —  ONE-OFF back-swing.

Consolidates the domestic-state finance corpus from the old model
(one record per budget line PER STAGE) into the new one
(one record per budget line PER FISCAL YEAR, accreting its stages),
per wiki/finance-load-domestic-state.md as amended 2026-07-26.

For each group of records that share a line-year (same place, same
fiscal-year start, same line signature — stage and year-form stripped
from the deal_id), it writes ONE consolidated record:

  - deal_id            = stem with NO -{stage} suffix, year normalised to
                         the bare start year (fy_start.year)
  - baseline_stage     = earliest stage held (appropriated preferred as master)
  - current_stage      = latest stage held
  - stage ladder       = appropriated_total / revised_total / released_total /
                         actual_total / audited_total / proposed_total
                         (+ execution_pct_vs_appropriated / _vs_revised)
  - ## Stage history   = one dated entry per stage, oldest first
  - ## Description      = the appropriation line's purpose (else the baseline's)
  - a ⚠ Notes flag where no appropriation stage is held

It also: flags proposed-vs-appropriated figure disagreements as contradictions,
and rewires [[wikilinks]] that point at a retired per-stage record.

DRY-RUN BY DEFAULT.  Nothing is written or deleted without --apply.

Usage:
    python scripts/consolidate-budget-lines.py                 # dry-run, all places
    python scripts/consolidate-budget-lines.py --country ZAF   # dry-run, one place
    python scripts/consolidate-budget-lines.py --apply         # DO IT (git is the undo)
"""
import os, re, sys, argparse, collections, datetime

RAW = "raw"


def raw_sources(raw=RAW, ext=".md"):
    """(filename, path) for every source in the sharded `raw/YYYY/` tree.

    A local copy, not an import from finance_lib: this migration must stay
    self-contained to survive the move to archived-procs/, where a scripts/
    import would not resolve.
    """
    out = []
    for year in os.listdir(raw):
        d = os.path.join(raw, year)
        if not os.path.isdir(d):
            continue
        out += [(fn, os.path.join(d, fn)) for fn in os.listdir(d) if fn.endswith(ext)]
    out.sort()
    return out


def raw_path(fname):
    """Where a source belongs: its own YYYY- prefix names its shard."""
    return os.path.join(RAW, fname[:4], fname)
SCAN_DIRS = ["wiki"]                              # link rewiring (budget-line links live on hub/concept/intersection pages)
STAGE_ORDER = ["proposed", "appropriated", "revised", "released",
               "actual", "executed", "audited"]   # temporal; 'unclear' has no slot
STAGE_WORDS = set(STAGE_ORDER) | {"unclear"}
LADDER_FIELD = {                                   # stage -> frontmatter ladder key
    "proposed": "proposed_total", "appropriated": "appropriated_total",
    "revised": "revised_total", "released": "released_total",
    "actual": "actual_total", "executed": "actual_total", "audited": "audited_total",
}
CUR_SYMBOL = {"ZAR": "R"}

# ----------------------------------------------------------------------------- parsing
def split_front(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else (None, None)

def fm_get(fm, key, default=""):
    # [ \t]* not \s* — \s eats the newline and spills a blank field onto the next line
    m = re.search(r'^%s:[ \t]*"?([^\n]*?)"?[ \t]*$' % re.escape(key), fm, re.M)
    return m.group(1).strip() if m else default

def fm_places(fm):
    m = re.search(r'^places:\s*\[([^\]]*)\]', fm, re.M)
    return [p.strip() for p in m.group(1).split(",")] if m and m.group(1).strip() else []

def fm_topics(fm):
    m = re.search(r'^topics:\s*\[([^\]]*)\]', fm, re.M)
    return [p.strip() for p in m.group(1).split(",")] if m and m.group(1).strip() else []

def section(body, name):
    """Return the text of a '## name' section (until the next '## ')."""
    m = re.search(r'(?m)^##\s+%s\s*\n(.*?)(?=^##\s|\Z)' % re.escape(name), body, re.S)
    return m.group(1).strip() if m else ""

def deal_table(body):
    d = {}
    for k, v in re.findall(r'^\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*$', body, re.M):
        if k.strip() and k.strip() != "Field":
            d[k.strip()] = v.strip()
    return d

# ----------------------------------------------------------------------------- key
def fy_start_year(fm, tokens_year):
    m = re.search(r'^fy_start:\s*(\d{4})-\d\d-\d\d', fm, re.M)
    return m.group(1) if m else tokens_year

def parse_deal(deal_id, fm):
    """Return (iso3, tier_list, fy_year, line_signature, stage_from_id)."""
    toks = deal_id.split("-")
    iso3 = toks[0]
    i = 1
    tier = []
    while i < len(toks) and not re.fullmatch(r"\d{4}", toks[i]):
        tier.append(toks[i]); i += 1
    year_tok = toks[i] if i < len(toks) else ""
    i += 1
    # optionally swallow the FY second-half token (…-25 or …-2025), never a code
    if i < len(toks) and re.fullmatch(r"\d{2,4}", toks[i]) and year_tok:
        y = int(year_tok)
        if int(toks[i]) in (y + 1, (y + 1) % 100):
            i += 1
    rest = toks[i:]
    stage_from_id = ""
    if rest and rest[-1] in STAGE_WORDS:
        stage_from_id = rest[-1]; rest = rest[:-1]
    fy = fy_start_year(fm, year_tok)
    return iso3, tier, fy, "-".join(rest), stage_from_id

def new_deal_id(iso3, tier, fy, sig):
    parts = [iso3] + list(tier) + [fy, sig]
    return "-".join(p for p in parts if p)

# ----------------------------------------------------------------------------- load
def load_records():
    recs = []
    for fn, path in raw_sources(RAW):
        try:
            text = open(path, encoding="utf-8").read()
        except Exception:
            continue
        if "finance_origin: domestic-state" not in text:   # cheap guard before regex
            continue
        fm, body = split_front(text)
        if not fm or "finance_origin: domestic-state" not in fm:
            continue
        deal = fm_get(fm, "deal_id")
        if not deal:
            continue
        iso3, tier, fy, sig, stage_id = parse_deal(deal, fm)
        stage = fm_get(fm, "budget_stage") or stage_id or "unclear"
        recs.append(dict(
            fn=fn, text=text, fm=fm, body=body, deal=deal,
            iso3=iso3, tier=tuple(tier), fy=fy, sig=sig, stage=stage,
            places=fm_places(fm), topics=fm_topics(fm),
            title=fm_get(fm, "title"),
            amount=fm_get(fm, "amount_total"),
            capital=fm_get(fm, "amount_capital"),
            recurrent=fm_get(fm, "amount_recurrent"),
            currency=fm_get(fm, "currency"),
            fyl=fm_get(fm, "fiscal_year_label"),
            fy_start=fm_get(fm, "fy_start"), fy_end=fm_get(fm, "fy_end"),
            fy_calendar=fm_get(fm, "fy_calendar"),
            published=fm_get(fm, "published"),
            source_tier=fm_get(fm, "source_tier"),
            scope=fm_get(fm, "scope_confidence"),
            level=fm_get(fm, "state_level"),
            tier_name=fm_get(fm, "spending_tier_name"),
            financier=fm_get(fm, "financier_slug"),
            version=fm_get(fm, "budget_version"),
            supp=fm_get(fm, "supplementary_basis"),
            is_transfer=fm_get(fm, "is_transfer"),
            table=deal_table(body),
            desc=section(body, "Description"),
            notes=section(body, "Notes"),
            devhist=section(body, "Development history"),
        ))
    return recs

# ----------------------------------------------------------------------------- helpers
def stage_rank(s):
    return STAGE_ORDER.index(s) if s in STAGE_ORDER else len(STAGE_ORDER) + 1

def money(amount, currency):
    if not amount or not amount.strip("-").isdigit():
        return "(n/a)"
    n = int(amount)
    sym = CUR_SYMBOL.get(currency, currency + " ")
    return f"{sym}{n:,}"

def stem_key(r):
    return (r["iso3"], r["tier"], r["fy"], r["sig"])

# ----------------------------------------------------------------------------- build one
def build_group(recs):
    """recs: list sharing a line-year. Return (new_filename, new_text, meta)."""
    recs = sorted(recs, key=lambda r: (stage_rank(r["stage"]), r["published"]))
    stages_present = [r["stage"] for r in recs]
    appr = next((r for r in recs if r["stage"] == "appropriated"), None)
    baseline = appr or recs[0]
    baseline_stage = "appropriated" if appr else recs[0]["stage"]
    current = recs[-1]

    iso3, tier, fy, sig = stem_key(baseline)
    ndeal = new_deal_id(iso3, tier, fy, sig)

    # stage ladder
    ladder = {v: "" for v in ["proposed_total", "appropriated_total", "revised_total",
                              "released_total", "actual_total", "audited_total"]}
    for r in recs:
        f = LADDER_FIELD.get(r["stage"])
        if f and r["amount"]:
            ladder[f] = r["amount"]

    # revised/final: a 'revised' record sets revised_total; otherwise take the
    # 'Final budget' printed on an audited/actual record (the adjusted/written-down total).
    if not ladder["revised_total"]:
        for r in recs:
            fb = r["table"].get("Final budget", "")
            m2 = re.search(r'\d[\d,\. ]*\d', fb)
            if m2:
                ladder["revised_total"] = re.sub(r'[^\d]', '', m2.group(0)); break

    # Two execution bases (CC review 2026-07-26). Never one: on a written-down levy
    # line revised == outturn, so vs_revised is a 100% tautology; vs_appropriated
    # (budget credibility, PEFA basis) is the one that can surprise you.
    def pct(num, den):
        if num and den and num.strip("-").isdigit() and den.strip("-").isdigit() and int(den):
            return f"{100 * int(num) / int(den):.1f}"
        return ""
    outturn = ladder["audited_total"] or ladder["actual_total"]
    ex_appr = pct(outturn, ladder["appropriated_total"])                        # headline
    ex_rev = pct(outturn, ladder["revised_total"] or ladder["appropriated_total"])

    # contradictions: proposed vs appropriated
    contradiction = None
    prop = next((r for r in recs if r["stage"] == "proposed"), None)
    if prop and appr and prop["amount"] and appr["amount"]:
        if prop["amount"].strip("-").isdigit() and appr["amount"].strip("-").isdigit():
            a, b = int(prop["amount"]), int(appr["amount"])
            if b and abs(a - b) / max(b, 1) > 0.02:
                contradiction = (prop["amount"], appr["amount"])

    # ## Stage history
    hist = []
    for r in recs:
        loc = r["table"].get("doc_locator", "") or r["source_tier"]
        extra = ""
        if r["stage"] in ("audited", "actual", "executed"):
            fb = r["table"].get("Final budget", "")
            if fb:
                extra = f" (final {fb})"
        url = fm_get(r["fm"], "url")
        line = f"- **{r['published']}** {r['stage']} **{money(r['amount'], r['currency'])}**{extra} — {loc}."
        if url:
            line += f" [{url}]"
        hist.append(line)

    # description
    desc = (appr or baseline)["desc"].strip()

    # notes
    warn = "" if baseline_stage == "appropriated" else \
        f"⚠ no appropriation stage held — baseline is {baseline_stage}\n\n"
    merged_notes = []
    for r in recs:
        if r["notes"].strip():
            merged_notes.append(f"*({r['stage']})* {r['notes'].strip()}")
    if contradiction:
        merged_notes.insert(0, f"⚠ proposed {money(contradiction[0], baseline['currency'])} vs "
                               f"appropriated {money(contradiction[1], baseline['currency'])} — filed as contradiction.")
    notes = warn + "\n\n".join(merged_notes)

    # development history (union of lines)
    dev = []
    for r in recs:
        for ln in r["devhist"].splitlines():
            if ln.strip().startswith("-") and ln.strip() not in dev:
                dev.append(ln.strip())

    # deal-record table (from baseline/current)
    T = baseline["table"]
    trow = [("Line ID", ndeal),
            ("Financier", T.get("Financier", "")),
            ("Spending entity", T.get("Spending entity", "")),
            ("Vote", T.get("Vote", "")),
            ("Programme", T.get("Programme", "")),
            ("Subprogramme", T.get("Subprogramme", "")),
            ("Fiscal year", baseline["fyl"]),
            ("Baseline stage", baseline_stage),
            ("Current stage", current["stage"]),
            ("Appropriated", money(ladder["appropriated_total"], baseline["currency"]) if ladder["appropriated_total"] else ""),
            ("Revised / final", money(ladder["revised_total"], baseline["currency"]) if ladder["revised_total"] else ""),
            ("Audited actual", money(ladder["audited_total"] or ladder["actual_total"], baseline["currency"]) if (ladder["audited_total"] or ladder["actual_total"]) else ""),
            ("Execution vs voted", f"{ex_appr}%" if ex_appr else ""),
            ("Execution vs revised", f"{ex_rev}%" if ex_rev else ""),
            ("doc_locator", T.get("doc_locator", "")),
            ("amount_scale", T.get("amount_scale", "")),
            ("funding_source", T.get("funding_source", ""))]

    # frontmatter
    published = (appr or baseline)["published"]
    fmnew = ["---", "type: source",
             f'title: "{baseline["title"]}"',
             f'url: {fm_get(baseline["fm"], "url")}',
             f'publisher: {fm_get(baseline["fm"], "publisher")}',
             f'published: {published}',
             f'date_precision: {fm_get(baseline["fm"], "date_precision") or "day"}',
             'date_source: source',
             f'places: [{", ".join(baseline["places"])}]',
             # first-seen order, NEVER sorted: topics[0] is the primary subject
             # (reference.md -> Facets). Sorting it silently re-files the line.
             f'topics: [{", ".join(dict.fromkeys(sum((r["topics"] for r in recs), [])))}]',
             f'entities: [[{baseline["financier"]}]]',
             f'financier_slug: {baseline["financier"]}',
             f'deal_id: {ndeal}',
             'finance_origin: domestic-state',
             f'state_level: {baseline["level"]}',
             f'spending_tier_name: "{baseline["tier_name"]}"',
             f'fiscal_year_label: "{baseline["fyl"]}"',
             f'fy_start: {baseline["fy_start"]}',
             f'fy_end: {baseline["fy_end"]}',
             f'budget_version: {baseline["version"] or "original"}',
             f'source_tier: {current["source_tier"]}',
             f'supplementary_basis: "{next((r["supp"] for r in recs if r["supp"]), "")}"',
             f'scope_confidence: {baseline["scope"]}',
             f'is_transfer: {baseline["is_transfer"] or "false"}',
             f'currency: {baseline["currency"]}',
             f'baseline_stage: {baseline_stage}',
             f'current_stage: {current["stage"]}',
             f'proposed_total: {ladder["proposed_total"]}',
             f'appropriated_total: {ladder["appropriated_total"]}',
             f'revised_total: {ladder["revised_total"]}',
             f'released_total: {ladder["released_total"]}',
             f'actual_total: {ladder["actual_total"]}',
             f'audited_total: {ladder["audited_total"]}',
             f'execution_pct_vs_appropriated: {ex_appr}',
             f'execution_pct_vs_revised: {ex_rev}',
             f'baseline_capital: {(appr or baseline)["capital"]}',
             f'baseline_recurrent: {(appr or baseline)["recurrent"]}',
             f'ingested: {datetime.date.today().isoformat()}',
             f'retrieved: {fm_get(baseline["fm"], "retrieved")}',
             'body_completeness: excerpt',
             "---"]

    # assemble body
    tbl = "\n".join(f"| {k} | {v} |" for k, v in trow if v)
    parts = ["\n".join(fmnew), "",
             f'# {baseline["title"]}', "",
             "## Budget line record", "",
             "| Field | Value |", "|---|---|", tbl, "",
             "## Stage history", "", "\n".join(hist), "",
             "## Description", "", desc, "",
             "## Development history", "", "\n".join(dev), "",
             "## Notes", "", notes, ""]
    new_text = "\n".join(parts)

    # filename = published date + the new deal_id (which is itself the stable key);
    # the human-readable line description lives in the title and the record table.
    fname = re.sub(r'-+', '-', f"{published}-{ndeal}.md")

    meta = dict(ndeal=ndeal, stages=stages_present, baseline_stage=baseline_stage,
                current=current["stage"], missing_appr=(appr is None),
                contradiction=contradiction, nrec=len(recs),
                old_files=[r["fn"] for r in recs], old_deals=[r["deal"] for r in recs])
    return fname, new_text, meta

# ----------------------------------------------------------------------------- link map
def build_link_map(groups_meta):
    """old deal_id / old filename-stem  ->  new deal_id."""
    m = {}
    for fname, meta in groups_meta:
        new_stem = fname[:-3]
        for od in meta["old_deals"]:
            m[od] = meta["ndeal"]
        for of in meta["old_files"]:
            m[of[:-3]] = new_stem
    return m

def rewire_links(link_map, apply):
    hits = collections.Counter()
    if not link_map:
        return hits
    # one simple wikilink pattern; the dict decides what to rewrite (no huge alternation)
    pat = re.compile(r'\[\[([^\]|]+)(\]\]|\|)')
    counter = {"n": 0}
    def repl(m):
        tgt = m.group(1)
        if tgt in link_map:
            counter["n"] += 1
            return "[[" + link_map[tgt] + m.group(2)
        return m.group(0)
    for d in SCAN_DIRS:
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                p = os.path.join(root, fn)
                try:
                    t = open(p, encoding="utf-8").read()
                except Exception:
                    continue
                if "[[" not in t:
                    continue
                before = counter["n"]
                new_t = pat.sub(repl, t)
                if counter["n"] > before:
                    hits[p] += counter["n"] - before
                    if apply:
                        open(p, "w", encoding="utf-8").write(new_t)
    return hits

# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--country", help="limit to one ISO-3 place")
    args = ap.parse_args()

    recs = load_records()
    if args.country:
        recs = [r for r in recs if args.country in r["places"] or r["iso3"] == args.country.lower()]

    groups = collections.defaultdict(list)
    for r in recs:
        groups[stem_key(r)].append(r)

    built = []
    for key, grp in sorted(groups.items()):
        built.append(build_group(grp))

    groups_meta = [(fname, meta) for fname, _, meta in built]
    link_map = build_link_map(groups_meta)
    link_hits = rewire_links(link_map, args.apply)

    # ---- report
    singles = [m for _, m in groups_meta if m["nrec"] == 1]
    merges = [m for _, m in groups_meta if m["nrec"] > 1]
    missing = [m for _, m in groups_meta if m["missing_appr"]]
    contras = [m for _, m in groups_meta if m["contradiction"]]
    bycountry = collections.Counter(m["ndeal"].split("-")[0].upper() for _, m in groups_meta)

    print(f"{'APPLYING' if args.apply else 'DRY-RUN'} — domestic-state back-swing\n")
    print(f"  input records         : {len(recs)}")
    print(f"  consolidated records  : {len(built)}")
    print(f"    single-stage (rename): {len(singles)}")
    print(f"    multi-stage (merge)  : {len(merges)}")
    print(f"  ⚠ no appropriation held: {len(missing)}")
    print(f"  contradictions flagged : {len(contras)}")
    print(f"  files with links to fix: {len(link_hits)}")
    print("\n  by place (consolidated):",
          ", ".join(f"{k} {v}" for k, v in sorted(bycountry.items())))

    print("\n  --- multi-stage merges (sample) ---")
    for m in merges[:25]:
        flag = " ⚠no-appr" if m["missing_appr"] else ""
        c = " ‼contradiction" if m["contradiction"] else ""
        print(f"    {m['ndeal']:52} {'+'.join(m['stages'])}{flag}{c}")
    if len(merges) > 25:
        print(f"    … {len(merges)-25} more")

    if contras:
        print("\n  --- contradictions (proposed vs appropriated) ---")
        for m in contras:
            print(f"    {m['ndeal']}: {m['contradiction'][0]} vs {m['contradiction'][1]}")

    if args.apply:
        removed = set()
        for fname, text, meta in built:
            p = raw_path(fname)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(text)
            for of in meta["old_files"]:
                if of != fname:
                    removed.add(of)
        for of in removed:
            p = raw_path(of)
            if os.path.exists(p):
                os.remove(p)
        print(f"\n  WROTE {len(built)} consolidated records; REMOVED {len(removed)} old files;"
              f" rewired links in {len(link_hits)} files.")
        print("  Review `git diff`, then update FINANCE-COMPILE.md + lint for the stage ladder.")
    else:
        print("\n  Dry-run only. Re-run with --apply to write. (git is the undo.)")

if __name__ == "__main__":
    main()
