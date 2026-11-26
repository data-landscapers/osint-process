#!/usr/bin/env python3
r"""inventory.py — write `X:\documentation\inventory-osint.csv` and its sortable page, one row an object.

The objects are OSINT's processes (root `*.md`), scripts, tests, lookups, logs, records, queues and documents. The columns are CORPUS's (its `inventory-corpus.csv`), so the two inventories read side by side: `object,kind,purpose,purpose_from,read_by,written_by`.

*purpose* is the object's own first heading or docstring line, or a CSV's header when it has neither. *read_by* and *written_by* come from a search of the processes, specs and scripts for the object's name: a mentioning file whose mentioning lines carry a write cue is a writer, otherwise a reader. It is a heuristic and says so; it is regenerated every cycle and never edited.

Usage: python scripts/inventory.py [--out-dir X:/documentation] [--check]
"""
import argparse
import csv
import html
import io
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARE = Path("X:/")
TEXT_EXT = {".md", ".py", ".bat", ".json", ".csv", ".txt", ".jsonl"}
# OSINT's own queues (CLAUDE.md -> Working the base, Reporting). The X: ones are OSINT's to drain.
QUEUES = ["reviews/acquisitions.md", "reviews/contradictions/", "reviews/rule-candidates.md", "reviews/post-run-notes.md", "new/", "new-budget/"]
SHARE_QUEUES = ["osint-housekeeping.md", "osint-notes.md", "fetch-list.md"]
# A writer says it writes the object: a prose verb on the mentioning line of a process or spec; in code, a write on that line or on a line using the path variable that line assigns.
WRITE_MD = re.compile(r"\b(write|writes|wrote|appends?|rewrites?|truncates?|regenerates?)\b", re.I)
ASSIGN = re.compile(r"\s*([A-Za-z_]\w*)\s*(?::[^=]*)?=(?!=)")
WRITE_PY = re.compile(r"open\([^)]*['\"][wa]b?\+?['\"]|mode\s*=\s*['\"][wa]|write_text|write_bytes|\.to_csv|json\.dump|csv\.(Dict)?[wW]riter|shutil\.(move|copy)", re.I)


def writes(f, lines, hits):
    if not f.endswith(".py"):
        return any(WRITE_MD.search(ln) for ln in hits)
    if any(WRITE_PY.search(ln) for ln in hits):
        return True
    names = {m.group(1) for ln in hits if (m := ASSIGN.match(ln))}
    return any(WRITE_PY.search(ln) and any(re.search(r"(?<!\w)" + re.escape(n) + r"(?!\w)", ln) for n in names) for ln in lines)


def first_line(text):
    for ln in text.splitlines():
        s = ln.strip()
        if s and not s.startswith("<!--"):
            return s
    return ""


def purpose_of(p):
    """Return (purpose, purpose_from) for path p."""
    if p.is_dir():
        for name in ("README.md", "readme.md"):
            if (p / name).exists():
                return purpose_of(p / name)[0], rel(p / name)
        n = sum(1 for f in p.rglob("*") if f.is_file())
        return f"folder of {n} file(s)", rel(p)
    try:
        text = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return "", ""
    if p.suffix == ".py":
        m = re.search(r'^[rRuU]?("""|\'\'\')(.*?)\1', re.sub(r"\A(#.*\n)+", "", text), re.S | re.M)
        doc = first_line(m.group(2)) if m else ""
        return doc[:240], rel(p) if doc else ""
    if p.suffix == ".md":
        for ln in text.splitlines():
            if ln.startswith("# "):
                return ln[2:].strip()[:240], rel(p)
        return first_line(text)[:240], rel(p)
    if p.suffix == ".csv":
        return "columns: " + first_line(text)[:200], rel(p)
    if p.suffix == ".bat":
        rem = [ln[3:].strip() for ln in text.splitlines() if ln.lower().startswith("rem ")]
        return (rem[0] if rem else first_line(text))[:240], rel(p)
    return first_line(text)[:240], rel(p)


def rel(p):
    try:
        return p.relative_to(ROOT).as_posix() + ("/" if p.is_dir() else "")
    except ValueError:
        return "X:/" + p.relative_to(SHARE).as_posix()


def objects():
    out = []
    for p in sorted(ROOT.glob("*.md")):
        out.append((p, "document" if p.name in ("CLAUDE.md", "README.md") else "process"))
    for p in sorted((ROOT / "scripts").iterdir()):
        if p.name == "__pycache__":
            continue
        if p.name == "tests":
            out += [(t, "test") for t in sorted(p.glob("*.py"))]
        elif p.name == "batches":
            out += [(t, "script") for t in sorted(p.iterdir()) if t.is_file()]
        elif p.is_file():
            out.append((p, "document" if p.suffix == ".md" else "script"))
    out += [(p, "lookup") for p in sorted((ROOT / "lookups").iterdir()) if p.is_file()]
    out += [(p, "log") for p in sorted((ROOT / "logs").iterdir())]
    out += [(ROOT / q.rstrip("/"), "queue") for q in QUEUES if (ROOT / q.rstrip("/")).exists()]
    out += [(SHARE / q, "queue") for q in SHARE_QUEUES if (SHARE / q).exists()]
    qset = {(ROOT / q.rstrip("/")) for q in QUEUES}
    out += [(p, "record") for p in sorted((ROOT / "reviews").iterdir()) if p not in qset]
    out += [(p, "document") for d in ("wiki", "documentation") for p in sorted((ROOT / d).glob("*.md"))]
    out += [(ROOT / "cycle-manifest.json", "record")]
    return [(p, k) for p, k in out if p.exists()]


def corpus_files():
    files = list(ROOT.glob("*.md")) + list((ROOT / "wiki").glob("*.md")) + list((ROOT / "documentation").glob("*.md"))
    files += [p for p in (ROOT / "scripts").rglob("*") if p.is_file() and p.suffix in {".py", ".bat", ".md"} and "__pycache__" not in p.parts]
    return {rel(p): p.read_text(encoding="utf-8-sig", errors="replace").splitlines() for p in files}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="X:/documentation")
    ap.add_argument("--check", action="store_true", help="print the count and write nothing")
    a = ap.parse_args()
    objs = objects()
    texts = corpus_files()
    names = [p.name for p, _ in objs]
    rows = []
    for p, kind in objs:
        r = rel(p)
        bare = r[3:] if r.startswith("X:/") else r
        # An ambiguous basename (log.md, status.md, README.md) must be named by its path.
        needle = p.name if names.count(p.name) == 1 and p.name.lower() not in {"readme.md", "index.md"} else bare.rstrip("/")
        pat = re.compile(r"(?<![\w.-])" + re.escape(needle.rstrip("/")) + r"(?![\w-])")
        readers, writers = [], []
        for f, lines in texts.items():
            if f == r:
                continue
            hits = [ln for ln in lines if pat.search(ln)]
            if hits:
                (writers if writes(f, lines, hits) else readers).append(f)
        purpose, pfrom = purpose_of(p)
        rows.append([r, kind, purpose, pfrom, "; ".join(sorted(readers)), "; ".join(sorted(writers))])
    if a.check:
        from collections import Counter
        print(len(rows), "objects:", dict(Counter(k for _, k, *_ in rows)))
        return 0
    out = Path(a.out_dir)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["object", "kind", "purpose", "purpose_from", "read_by", "written_by"])
    w.writerows(rows)
    (out / "inventory-osint.csv").write_text(buf.getvalue(), encoding="utf-8", newline="")
    cell = lambda s: "<br>".join(html.escape(x) for x in s.split("; ")) if s else ""
    body = "\n".join("<tr>" + "".join(f"<td>{cell(c) if i >= 4 else html.escape(c)}</td>" for i, c in enumerate(row)) + "</tr>" for row in rows)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OSINT inventory</title>
<style>
body{{font:14px/1.4 system-ui,sans-serif;margin:1rem;color:#222;background:#fff}}
input{{font:inherit;padding:.3rem;width:20rem;max-width:100%;margin-bottom:.6rem}}
table{{border-collapse:collapse;width:100%}}
th,td{{border-bottom:1px solid #ddd;padding:.3rem .5rem;vertical-align:top;text-align:left}}
th{{position:sticky;top:0;background:#f4f4f4;cursor:pointer;white-space:nowrap}}
td:first-child{{font-family:ui-monospace,monospace;white-space:nowrap}}
td:nth-child(5),td:nth-child(6){{font-size:12px;color:#555}}
</style></head><body>
<h1>OSINT inventory</h1>
<p>{len(rows)} objects. Written by <code>scripts/inventory.py</code> each cycle; never edited. <i>read by</i> and <i>written by</i> are a name search, not a parse. Click a heading to sort; type to filter.</p>
<input id="q" placeholder="Filter" autofocus>
<table id="t"><thead><tr><th>object</th><th>kind</th><th>purpose</th><th>purpose from</th><th>read by</th><th>written by</th></tr></thead><tbody>
{body}
</tbody></table>
<script>
const t=document.getElementById('t'),q=document.getElementById('q');
q.oninput=()=>{{const v=q.value.toLowerCase();for(const r of t.tBodies[0].rows)r.hidden=!r.textContent.toLowerCase().includes(v);}};
t.tHead.onclick=e=>{{const th=e.target.closest('th');if(!th)return;const i=th.cellIndex,b=t.tBodies[0],d=th.dataset.d=th.dataset.d==='1'?'-1':'1';
[...b.rows].sort((x,y)=>x.cells[i].textContent.localeCompare(y.cells[i].textContent)*d).forEach(r=>b.appendChild(r));}};
</script></body></html>
"""
    (out / "inventory-osint.html").write_text(page, encoding="utf-8", newline="\n")
    print(f"inventory: {len(rows)} objects -> {out / 'inventory-osint.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
