"""End-to-end test of scripts/archive-budget-docs.py against a fixture repo."""
import csv, os, pathlib, shutil, subprocess, sys, tempfile

REPO = str(pathlib.Path(__file__).resolve().parents[2])
FIELDS = ["iso3", "fiscal_year", "fiscal_years_covered", "doc_type", "title", "url",
          "artefact_path", "companion_path", "retrieved", "scale", "currency", "pages",
          "extracted", "extracted_scope", "re_extract", "archive_path", "notes"]

root = tempfile.mkdtemp(prefix="archtest-")
os.makedirs(os.path.join(root, "new-budget", "XTS", "2025"))
rows = []
for n, (stem, fy) in enumerate([("2025-01-01-xts-estimates-2025", "2025"),
                                ("2025-02-02-xts-citizens-budget-2025", "2025")], 1):
    art = f"new-budget/XTS/{fy}/{stem}.pdf"
    comp = f"new-budget/XTS/{fy}/{stem}-companion.md"
    for p in (art, comp):
        open(os.path.join(root, p), "w", encoding="utf-8").write("x")
    rows.append({f: "" for f in FIELDS} | {"iso3": "XTS", "fiscal_year": fy,
                                           "artefact_path": art, "companion_path": comp,
                                           "title": stem})
# one row already archived: the script must leave it alone
rows.append({f: "" for f in FIELDS} | {"iso3": "XTS", "fiscal_year": "2024",
                                       "artefact_path": "new-budget/XTS/2024/old.pdf",
                                       "extracted": "2026-01-01", "extracted_scope": "narrative"})
man = os.path.join(root, "new-budget", "manifest.csv")
with open(man, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

scope = os.path.join(root, "scope.csv")
open(scope, "w", encoding="utf-8", newline="").write(
    "stem,extracted_scope,re_extract\n"
    "xts-estimates-2025,cross-vote,no\n"
    "xts-citizens-budget-2025,narrative,BIP tables not read\n")


def run(*args):
    return subprocess.run([sys.executable, os.path.join(REPO, "scripts", "archive-budget-docs.py"),
                           "--country", "XTS", "--root", root, *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace")

# 1. a scope file missing a document must fail, and write nothing
partial = os.path.join(root, "partial.csv")
open(partial, "w", encoding="utf-8", newline="").write(
    "stem,extracted_scope,re_extract\nxts-estimates-2025,cross-vote,no\n")
r = run("--scope", partial, "--apply")
assert r.returncode == 1, r.stdout
assert "NO SCOPE ROW" in r.stdout
assert os.path.exists(os.path.join(root, "new-budget/XTS/2025/2025-01-01-xts-estimates-2025.pdf")), \
    "a failed run must move nothing"
print("1. incomplete scope file -> exit 1, nothing moved   OK")

# 2. dry run writes nothing
r = run("--scope", scope, "--date", "2026-08-03")
assert r.returncode == 0 and "dry run" in r.stdout, r.stdout
assert list(csv.DictReader(open(man, encoding="utf-8")))[0]["extracted"] == ""
print("2. dry run -> nothing written                       OK")

# 3. apply
r = run("--scope", scope, "--date", "2026-08-03", "--apply")
assert r.returncode == 0, r.stdout + r.stderr
got = list(csv.DictReader(open(man, encoding="utf-8")))
a, b, old = got
assert (a["extracted"], a["extracted_scope"], a["re_extract"]) == ("2026-08-03", "cross-vote", "no")
assert a["archive_path"] == "budget-archive/XTS/2025/2025-01-01-xts-estimates-2025.pdf"
assert (b["extracted_scope"], b["re_extract"]) == ("narrative", "BIP tables not read")
assert (old["extracted"], old["extracted_scope"]) == ("2026-01-01", "narrative"), "archived row touched"
for stem in ("2025-01-01-xts-estimates-2025", "2025-02-02-xts-citizens-budget-2025"):
    for ext in (".pdf", "-companion.md"):
        assert os.path.exists(os.path.join(root, f"budget-archive/XTS/2025/{stem}{ext}")), stem + ext
        assert not os.path.exists(os.path.join(root, f"new-budget/XTS/2025/{stem}{ext}"))
assert not os.path.isdir(os.path.join(root, "new-budget", "XTS")), "emptied folders not removed"
print("3. apply -> 4 files moved, 4 columns set, folders removed, archived row untouched   OK")

# 4. idempotent: a second run finds nothing open
r = run("--scope", scope, "--apply")
assert r.returncode == 0 and "nothing open" in r.stdout, r.stdout
print("4. re-run -> nothing open (resumable, not repeatable)  OK")

shutil.rmtree(root, ignore_errors=True)
print("\nall 4 checks passed")
