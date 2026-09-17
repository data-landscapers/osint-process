#!/usr/bin/env python3
r"""test-taxonomy-labels.py - one file, two parsers, one label.

    python scripts/test-taxonomy-labels.py

`lookups/taxonomy.md` is read by two functions that must agree:
`build-finance-page.py`'s `taxonomy_labels()`, whose labels become the `sector` and
`subject` columns of every finance export, and `vault_lib.load_taxonomy()`, whose labels
become report sub-headings. They disagreed until housekeeping job 102: a line carrying an
editorial ruling after its first sentence - `dpi.registry` is the standing case - gave the
report a heading and the export roughly 500 characters of governance prose in a CSV cell.

So the assertion is not "the label looks right", which is a matter of taste, but **the two
parsers return the same label for every slug they both know**, over the real file. A future
gloss on any other line is then caught by whichever parser is not changed with it.

Exit 0 all agree, 1 a disagreement, with the slug and both readings printed.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import vault_lib as V                                                    # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_finance_page", os.path.join(HERE, "build-finance-page.py"))
bfp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bfp)

failures = 0


def check(name, got, want):
    global failures
    ok = got == want
    failures += not ok
    print(f"  {'ok  ' if ok else 'FAIL'} {name}")
    if not ok:
        print(f"         got:  {got!r}")
        print(f"         want: {want!r}")


# A fixture first, because the real file may one day carry no glossed line at all and a
# check that then tests nothing would still print ok.
print("a line carrying a ruling after its first sentence")
fixture = (
    "## Vocabulary\n"
    "\n"
    "### DPI\n"
    "- `dpi.registry` — Registries (population, land, address, etc.). **At country level, "
    "registry material files under `--dpi-id`** *(ruled 2026-08-10)*: a long editorial "
    "gloss that is not a label.\n"
    "- `dpi.id` — Digital Identity and CRVS\n"
)
tmp = tempfile.mkdtemp(prefix="taxonomy-labels-")
os.makedirs(os.path.join(tmp, "lookups"), exist_ok=True)
with open(os.path.join(tmp, "lookups", "taxonomy.md"), "w", encoding="utf-8") as fh:
    fh.write(fixture)
cwd = os.getcwd()
try:
    os.chdir(tmp)                       # taxonomy_labels() reads a relative path
    lab = bfp.taxonomy_labels()
finally:
    os.chdir(cwd)
check("the glossed label stops at the first sentence", lab.get("dpi.registry"),
      "Registries (population, land, address, etc.)")
check("an unglossed label is untouched", lab.get("dpi.id"), "Digital Identity and CRVS")
check("no label runs past a heading's length", max(len(v) for v in lab.values()) < 120, True)

print("\nthe two parsers over the real lookups/taxonomy.md")
os.chdir(ROOT)
export = bfp.taxonomy_labels()
_order, report, _l1 = V.load_taxonomy()
shared = sorted(set(export) & set(report))
check("both parsers read the same file and find slugs", len(shared) > 20, True)
for slug in shared:
    if export[slug] != report[slug]:
        failures += 1
        print(f"  FAIL {slug}\n         export: {export[slug]!r}\n         report: {report[slug]!r}")
print(f"  {'ok  ' if not failures else 'FAIL'} {len(shared)} slug(s) agree between the "
      f"export and the report parser")

print()
if failures:
    print(f"{failures} case(s) FAILED")
    sys.exit(1)
print("all cases passed")
