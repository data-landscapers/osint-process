#!/usr/bin/env python3
"""promote-budget-companions.py — catalogue held budget documents into raw/ (BUDGET-COLLECT.md, notes-for-osint 168 step 5).

    promote-budget-companions.py                 dry run over every country, in order
    promote-budget-companions.py ETH KEN         dry run, those countries only
    promote-budget-companions.py --write [ISO3]  write the raw/ records and the URL index/log lines
    promote-budget-companions.py --slug S [--slug S ...] [--write]
                                                 promote the named companions whatever their class (notes-for-osint 171:
                                                 a companion a published figure has to cite, outside the four classes below)

**What it promotes.** A `budget-archive/` companion page is promoted when it describes one of four classes:
- a full estimates volume: `budget-estimates` with `extracted_scope: cross-vote` on its manifest row;
- an appropriation or finance law: `appropriation-act`;
- an outturn report: `implementation-report` or `outturn-report`;
- an audit report: `audited-accounts`.
Sector-vote extracts, MTEFs, statements and procurement plans stay in the archive.

**The promotion is a copy.** The companion stays in `budget-archive/`, where the manifest's `companion_path` names it, and nothing there is ever deleted. The copy goes to `raw/{YYYY}/{slug}.md`, where the slug is the companion's own filename, on the shape of the notes 162/163 companions:
- `source_tier: budget-document`, `catalogue_hero`, `hub_line_none` and `ingested` are added;
- no `artefact:` key (`wiki/schemas.md` §4: the manifest row is the declaration);
- the "Not an admitted source" status paragraph is replaced with a one-line lead;
- a `## Source` line is added where the body lacks one.

**Skipped, and said so:**
- the slug is already in `raw/`;
- its URL is already held by a record that is not a domestic-state budget-line record (per-line records share their volume's URL, and one of them is not the catalogue entry);
- no URL, or a body still claiming it is not a source.

Order: ETH, KEN, NGA, BDI, AGO, BFA, BWA, BEN, SEN, COG, COM, CIV, CPV, RWA, CMR, COD, then the rest alphabetically.
"""
import csv, datetime, io, os, pathlib, re, subprocess, sys

ORDER = ["ETH", "KEN", "NGA", "BDI", "AGO", "BFA", "BWA", "BEN", "SEN", "COG", "COM", "CIV", "CPV", "RWA", "CMR", "COD"]
ALWAYS = {"appropriation-act", "implementation-report", "outturn-report", "audited-accounts"}
DROP = ("artefact", "note", "fiscal_year_label", "fy_start", "fy_end", "fiscal_year", "scale", "pages", "sweep_batch", "ingested")
STATUS = re.compile(r"^\*\(Companion page for (a )?budget documents? .*?\)\*[ \t]*$", re.M)
NOT_EXTRACTED = re.compile(r"^\*\*Not extracted here\.\*\*.*\n?", re.M)
TODAY = datetime.date.today().isoformat()
WRITE = "--write" in sys.argv
FORCE = {sys.argv[i + 1] for i, a in enumerate(sys.argv[:-1]) if a == "--slug"}
PY = sys.executable
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def manifest_scope():
    rows = csv.DictReader(open("new-budget/manifest.csv", encoding="utf-8", newline=""))
    return {r["companion_path"].split("/")[-1]: r.get("extracted_scope", "") for r in rows}


def url_index():
    out = {}
    for r in csv.DictReader(open("lookups/raw-url-index.csv", encoding="utf-8", newline="")):
        out.setdefault(r["url_normalized"], []).append(r["file"])
    return out


def normalise(u):
    sys.path.insert(0, "scripts")
    from vault_lib import normalise_url
    return normalise_url(u)


def is_line_record(path):
    try:
        head = open(path, encoding="utf-8", errors="replace").read(4000)
    except OSError:
        return True
    return bool(re.search(r"^(deal_id|finance_origin):", head, re.M))


def promote(comp, raw_slugs, idx, scope):
    b = comp.read_bytes(); eol = "\r\n" if b"\r\n" in b else "\n"
    t = b.decode("utf-8").replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if not m:
        return None, "no frontmatter"
    fm, body = m.group(1).split("\n"), t[m.end():]
    get = lambda k: next((l.split(":", 1)[1].strip().strip('"') for l in fm if l.startswith(k + ":")), "")
    doc = get("doc_type")
    if FORCE and comp.stem not in FORCE:
        return None, None
    if not (comp.stem in FORCE or doc in ALWAYS or (doc == "budget-estimates" and scope.get(comp.name) == "cross-vote")):
        return None, None                                    # not a class this promotes; silent
    slug = comp.stem
    if slug in raw_slugs:
        return None, "slug already in raw/"
    url = get("url")
    if not url:
        return None, "no url"
    held = [f for f in idx.get(normalise(url), []) if not is_line_record(f)]
    if held:
        return None, "url held by " + held[0]
    iso, fy = comp.parts[1], comp.parts[2]
    keys = [l.split(":", 1)[0] for l in fm]
    out = [l for i, l in enumerate(fm) if l.split(":", 1)[0] not in DROP
           and not (l.startswith(" ") and fm[i - 1].split(":", 1)[0] in DROP)]
    if "source_tier" not in keys:
        out.append("source_tier: budget-document")
    if "catalogue_hero" not in keys:
        hero = get("title")[:140].replace('"', "'")
        out.append(f'catalogue_hero: "{hero}"')
    out.insert(next(i for i, l in enumerate(out) if l.startswith("topics:")), f"ingested: {TODAY}")
    out.append(f"hub_line_none: {TODAY}  # budget-document companion, catalogued for citation (notes-for-osint {'171' if FORCE else '168, step 5'})")
    lead = (f"**Companion source page for a budget document.** Its artefact is filed at `budget-archive/{iso}/{fy}/` "
            f"and declared by its row in `new-budget/manifest.csv`. It is catalogued so that a figure read from the document can cite it by name.")
    if STATUS.search(body):
        body = STATUS.sub(lead, body, count=1)
    else:
        body = re.sub(r"^(# .*\n)", r"\1\n" + lead.replace("\\", "\\\\") + "\n", body, count=1, flags=re.M)
    body = NOT_EXTRACTED.sub("", body)
    # Older companions word the status note many ways and hard-wrap it. A short paragraph
    # saying "not an admitted source" is that note and nothing else, so it goes whole; the
    # lead above already says what the page is. A long one carries content too and is skipped.
    paras = body.split("\n\n")
    for i, p in enumerate(paras):
        if "not an admitted source" in p.lower():
            if len(p.split()) > 90:
                return None, "status note sits inside a long paragraph"
            paras[i] = None
    body = "\n\n".join(p for p in paras if p is not None)
    if lead not in body:
        body = re.sub(r"^(# .*\n)", r"\1\n" + lead.replace("\\", "\\\\") + "\n", body, count=1, flags=re.M)
    if not re.search(r"^## Source\b", body, re.M):
        ret = get("retrieved") or "date not recorded"
        body = body.rstrip("\n") + f"\n\n## Source\n\n<{url}>, accessed {ret}.\n"
    year = slug[:4] if re.match(r"\d{4}-", slug) else get("published")[:4]
    dest = pathlib.Path("raw", year, slug + ".md")
    return (dest, ("---\n" + "\n".join(out) + "\n---\n" + body).replace("\n", eol), url, get("published")), None


def main():
    only = [a for a in sys.argv[1:] if re.fullmatch(r"[A-Z]{3}", a)]
    countries = sorted({p.parts[1] for p in pathlib.Path("budget-archive").glob("*/*/*-companion.md")})
    order = [c for c in ORDER if c in countries] + [c for c in countries if c not in ORDER]
    if only:
        order = [c for c in order if c in only]
    raw_slugs = {p.stem for p in pathlib.Path("raw").rglob("*.md")}
    idx, scope = url_index(), manifest_scope()
    total, skipped = 0, []
    for iso in order:
        n = 0
        for comp in sorted(pathlib.Path("budget-archive", iso).glob("*/*-companion.md")):
            rec, why = promote(comp, raw_slugs, idx, scope)
            if why:
                skipped.append(f"{comp.as_posix()}: {why}")
            if not rec:
                continue
            dest, text, url, pub = rec
            n += 1
            if WRITE:
                dest.parent.mkdir(parents=True, exist_ok=True)
                assert not dest.exists(), dest
                dest.write_text(text, encoding="utf-8", newline="")
                raw_slugs.add(dest.stem)
                subprocess.run([PY, "scripts/raw-url-index.py", "--append", url, dest.as_posix(), pub], check=True, capture_output=True)
                subprocess.run([PY, "scripts/url-log-append.py", "admitted", url], check=True, capture_output=True)
        total += n
        print(f"{iso}: {n} {'promoted' if WRITE else 'to promote'}")
    print(f"total {total} {'promoted' if WRITE else 'to promote (dry run; --write to apply)'}; {len(skipped)} skipped")
    for s in skipped:
        print("  skip", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
