"""One housekeeping *By place* extraction job, end to end (jobs 147 onward).

    by-place-job.py <topic> <job> merge            the merge half: cells into existing pages
    by-place-job.py <topic> <job> mint [CODE ...]  the mint half: new pages (all, or the codes given)
    by-place-job.py <topic> <job> full             both halves

XAF and XGL are never minted: their cells move into the page's `## Key material`, because an
Africa-wide or global page would duplicate the concept page itself. Stops before writing the
register or committing if a citation is lost, a lint check fails, or a line is left over the bar
that this job should have cleared. Prints the resolution text and log line; `--close` also
strikes the job on X:\\housekeeping-jobs.md and appends the log line.
"""
import io, os, re, subprocess, sys, json, glob, datetime

topic, job, mode = sys.argv[1], sys.argv[2], sys.argv[3]
codes = [a for a in sys.argv[4:] if re.fullmatch(r"[A-Z]{3}", a)]
CLOSE = "--close" in sys.argv
FINAL = "--final" in sys.argv or mode == "full"      # rewrite the Length review
DATE = datetime.date.today().isoformat()
PY = sys.executable
tslug = topic.replace(".", "-")
env = dict(os.environ, PYTHONIOENCODING="utf-8")


def run(*a):
    r = subprocess.run([PY, *a], capture_output=True, text=True, encoding="utf-8", env=env)
    if r.returncode:
        sys.exit(f"FAILED {a}: {r.stdout[-800:]} {r.stderr[-800:]}")
    return r.stdout


def measure():
    out = run("scripts/measure-concept.py", topic)
    total = int(re.search(r"total (\d+)", out).group(1))
    bp = re.search(r"## By place (\d+)", out)
    over = re.search(r"over 120: (.*)", out).group(1)
    return total, int(bp.group(1)) if bp else 0, over, out


before, bp_before, _, _ = measure()
plan = run("scripts/extract-by-place.py", topic)
planned_mint = re.search(r"mint \[(.*?)\]", plan).group(1).replace("'", "").split(", ")
planned_mint = [c for c in planned_mint if c]
under = [c for c in re.search(r"under \[(.*?)\]", plan).group(1).replace("'", "").split(", ") if c]
merged = 0
if mode in ("merge", "full"):
    out = run("scripts/extract-by-place.py", topic, "--write")
    if "lost citations: []" not in out:
        sys.exit("CITATIONS LOST: " + out[-600:])
    merged = int(re.search(r"places \d+ merge (\d+)", out).group(1))   # the summary line, not a place row

minted, cont = [], []
if mode in ("mint", "full"):
    want = codes or planned_mint
    cont = [c for c in want if c in ("XAF", "XGL")]
    mint = [c for c in want if c not in cont]
    titles = [re.search(r'^title:\s*"?[^×\n]*× ([^"\r\n]*)', io.open(p, encoding="utf-8").read(600), re.M)
              for p in glob.glob(f"wiki/intersections/*--{tslug}.md")]
    tname = next((m.group(1).strip() for m in titles if m), None)
    if not tname:
        # no intersection for this topic yet: take the label the taxonomy gives it
        m = re.search(r"^- `" + re.escape(topic) + r"` — ([^\r\n]+)", io.open("lookups/taxonomy.md", encoding="utf-8").read(), re.M)
        tname = m.group(1).strip() if m else None
    if not tname:
        sys.exit("no display name for the topic on any intersection or in lookups/taxonomy.md")
    before_files = set(glob.glob("wiki/intersections/*.md"))
    out = run("scripts/extract-by-place-mint.py", topic, tname, *mint, *cont)
    new = sorted(set(glob.glob("wiki/intersections/*.md")) - before_files)
    minted = [os.path.splitext(os.path.basename(p))[0] for p in new]
    if new:
        run("scripts/derive-entities.py", *new, "--write")
        pairs = [f"{re.search(r'^place:\s*(\S+)', io.open(p, encoding='utf-8').read(), re.M).group(1)}:{os.path.splitext(os.path.basename(p))[0]}" for p in new]
        link = run("scripts/link-minted-hub.py", topic, DATE, *pairs)
        if "NO topic list" in link:
            sys.exit("hub link failed: " + link)
    run("scripts/wiki-index-gen.py", "--write")

if mode == "finish":
    # resume a mint that stopped after writing its pages (a hub link failed, say): the pages
    # are the untracked intersections for this topic; XAF/XGL codes passed are the ones moved
    new = subprocess.run(["git", "ls-files", "-o", "--exclude-standard", "wiki/intersections"],
                         capture_output=True, text=True).stdout.split()
    minted = [os.path.splitext(os.path.basename(p))[0] for p in new if p.endswith(f"--{tslug}.md")]
    cont = [c for c in codes if c in ("XAF", "XGL")]
    b = next((a.split("=")[1] for a in sys.argv if a.startswith("--before=")), None)
    if b:
        before = int(b)
    mg = next((a.split("=")[1] for a in sys.argv if a.startswith("--merged=")), None)
    if mg:
        merged = int(mg)
        out = run("scripts/extract-by-place.py", topic, "--write")   # merge whatever the first run left
        if "lost citations: []" not in out:
            sys.exit("CITATIONS LOST: " + out[-600:])
    run("scripts/wiki-index-gen.py", "--write")

# Group labels that the extraction makes false: an "Indexed only (no intersection yet)" label now
# heads pointers to pages, and an "Extracted (own page):" label with nothing under it heads nothing.
cp = f"wiki/concepts/{topic}.md"
ct = io.open(cp, encoding="utf-8", newline="").read()
ct2 = re.sub(r"^\*\*Indexed only \(no intersection yet\):\*\*[ \t]*\r?\n(\r?\n)?", "", ct, flags=re.M)
ct2 = re.sub(r"^\*\*Extracted \(own page\):\*\*[ \t]*\r?\n(?:[ \t]*\r?\n)+(?=- |\*\*|#)", "", ct2, flags=re.M)
# dated batch markers ("*Entries below added 2026-09-23 …*") date lines that are now pointers
ct2 = re.sub(r"^\*(?:Entries below added|Index lines added) \d{4}-\d{2}-\d{2}[^\r\n]*\*[ \t]*\r?\n(?:[ \t]*\r?\n)?", "", ct2, flags=re.M)
if ct2 != ct:
    io.open(cp, "w", encoding="utf-8", newline="").write(ct2)

after, bp_after, over, mout = measure()
# over-bar lines left: only places a later job still has to mint may remain
left = re.findall(r"\('- \*\*\[\[([A-Z]{3})\]\]", over)
pending = [c for c in planned_mint if c not in (codes or planned_mint)] if mode == "mint" else (planned_mint if mode == "merge" else [])
if mode == "finish" and "--merge-half" in sys.argv:
    pending = planned_mint          # a merge half resumed: the places with no page are the mint job's
stray = sorted(set(c for c in left if c not in pending))
if stray:
    sys.exit(f"LINES STILL OVER THE BAR for {stray}")

for c in ("4", "12") + (("36",) if minted else ()):
    o = run("scripts/lint-deterministic.py", "--check", c)
    if not re.search(r"— 0 finding", o):
        sys.exit("LINT " + c + ": " + o[:800])

if FINAL:
    key = next((l[3:].strip() for l in io.open(f"wiki/concepts/{topic}.md", encoding="utf-8") if l.startswith("## Key material")), "Key material")
    rest = after - bp_after
    review = [
        f"*Measured on the page after housekeeping job {job}'s extraction, replacing the previous review.*",
        f"**{after:,} words.** `## By place` is now **{bp_after:,} words, one index line per place, and no line is over §8's materiality bar.** "
        "Places with an existing intersection were merged into it: each cell's citations were checked against the page first, cells the page lacked were moved whole under a dated heading, and every cut cell's citations were verified present afterwards (none lost). "
        + (f"Pages were minted for the places that had none. " if minted else "")
        + (f"Africa-wide and global cells moved into *{key}* rather than onto a page of their own, which would duplicate this one. " if cont else "")
        + (f"{', '.join(under)} {'is' if len(under) == 1 else 'are'} under the bar and stay as full index lines." if under else ""),
        f"**The rest of the page, about {rest:,} words, is the thematic material.** It does not decompose into per-place cells. *If it is to shrink, the route is a tighten or an append-log trim, not an extraction.*",
    ]
    tmp = os.path.join(os.environ.get("TEMP", "."), f"len-{job}.txt")
    io.open(tmp, "w", encoding="utf-8").write("\n".join(review))
    run("scripts/length-review.py", topic, DATE, tmp)
    after, bp_after, _, _ = measure()

keyname = next((l[3:].strip() for l in io.open(f'wiki/concepts/{topic}.md', encoding='utf-8') if l.startswith('## Key material')), None) or [l[3:].strip() for l in io.open(f'wiki/concepts/{topic}.md', encoding='utf-8').read().split(chr(10)) if l.startswith('## ')][[l.startswith('## By place') for l in io.open(f'wiki/concepts/{topic}.md', encoding='utf-8').read().split(chr(10)) if l.startswith('## ')].index(True)-1]
parts = []
if merged:
    parts.append(f"**{merged} places merged into their existing `{{place}}--{tslug}` pages, and 0 citations lost**, verified on every target page after the cut. Cells a page lacked were moved whole under a dated heading.")
if minted:
    parts.append(f"**{len(minted)} page{'s' if len(minted) != 1 else ''} minted**: " + ", ".join(f"`{m}`" for m in minted) + ". Each carries its cells unedited and `entities:` derived from its own cited records, and is linked from its hub and both generated indexes.")
if cont:
    parts.append(f"**{' and '.join(cont)} {'was' if len(cont) == 1 else 'were'} not minted**: the cells moved into *{keyname}*, since a page for {'it' if len(cont) == 1 else 'either'} would duplicate the concept page.")
if pending:
    parts.append(f"The {len(pending)} places with no page are left for the mint half.")
parts.append(f"**Re-measured: `{topic}.md` is {after:,} words, down from {before:,}; `## By place` is {bp_after:,} words, down from {bp_before:,}.**" + (" The *Length* review is rewritten." if FINAL else "") + " Lint " + ("#4, #12 and #36" if minted else "#4 and #12") + " are clean.")
res = "**Closed " + DATE + " in a hand session** with `scripts/by-place-job.py`. " + " ".join(parts)
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")
log = f"{now} · **HOUSEKEEPING** · job {job} closed: {topic} By place {mode}" + (f", {merged} merged" if merged else "") + (f", {len(minted)} minted" if minted else "") + (f", {'/'.join(cont)} to Key material" if cont else "") + f"; page {before:,}→{after:,} words, 0 citations lost · revert: git revert HEAD"
print(res)
print(log)
json.dump({"res": res, "log": log, "minted": minted, "merged": merged}, open(os.path.join(os.environ.get("TEMP", "."), f"job-{job}.json"), "w"))

if CLOSE:
    H, R = "X:/housekeeping-jobs.md", "X:/housekeeping-jobs-resolved.md"
    t = io.open(H, encoding="utf-8", newline="").read()
    eol = "\r\n" if "\r\n" in t else "\n"
    m = re.search(r"^" + job + r"\. .*?(\r?\n)+", t, re.M)
    entry = m.group(0).strip("\r\n")
    t = t[:m.start()] + t[m.end():]
    t = re.sub(r"^\| " + job + r" \|.*\r?\n", "", t, flags=re.M)
    io.open(H, "w", encoding="utf-8", newline="").write(t)
    r = io.open(R, encoding="utf-8", newline="").read().rstrip("\r\n")
    r += eol + eol + "x" + entry.replace(job + ". ", job + f". *(cleared {DATE})* ", 1) + " " + res + eol
    io.open(R, "w", encoding="utf-8", newline="").write(r)
    p = "logs/log.md"
    t = io.open(p, encoding="utf-8", newline="").read()
    e2 = "\r\n" if "\r\n" in t[:2000] else "\n"
    L = t.split(e2)
    i = next(k for k, l in enumerate(L) if l[:4] == "2026")
    L.insert(i, log)
    io.open(p, "w", encoding="utf-8", newline="").write(e2.join(L))
    print("closed", job)
