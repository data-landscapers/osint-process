#!/usr/bin/env python3
"""Cross-vote scan of a Burkinabe loi de finances volume (`pdftotext -enc UTF-8 -table`).

The volume is `section -> programme -> action -> chapitre -> activite`, AE/CP over
three years, `en milliers de F CFA`.  This walks the coded lines, attributes each to
the section it falls under, and reports the ones whose label carries a digital term
-- the cross-vote scan BUDGET-EXTRACT.md section 4a requires.

It is a LOCATOR, not an extractor -- it prints each hit's figures verbatim as the
document sets them and parses none of them.  See the note above `numeric_tail`.

Usage:  python scripts/bfa-volume-scan.py /tmp/bfa/vol2024.txt 2024 [--all] [--section NN]
"""
import argparse
import re
import sys

SECTION_RE = re.compile(r"^\s*Section\s+(\d{2})\s*:\s*(.+?)\s*$")
CODE_RE = re.compile(
    r"^(\s*)(?:(Programme)\s+(\d{3})|(Action)\s+(\d{5})|(Chap\.)\s+(\d{10})|(Activ\.)\s+(\d{7}))\s+(.*)$"
)
TERMS = [
    r"num[ée]ri", r"digital", r"t[ée]l[ée]com", r"internet", r"backbone", r"haut d[ée]bit",
    r"large bande", r"fibre optique", r"connectivit", r"data ?cent", r"cyber",
    r"biom[ée]tri", r"CNIB", r"passeport", r"[ée]tat.civil", r"fichier [ée]lectoral",
    r"interop[ée]rabilit", r"plateforme", r"logiciel", r"d[ée]mat[ée]rialis",
    r"t[ée]l[ée]proc[ée]dure", r"en ligne", r"e-gouv", r"administration [ée]lectronique",
    r"SIGASPE", r"SIGED", r"SIMP\b", r"RESINA", r"WURI", r"G-?Cloud", r"serveur",
    r"syst[èe]mes? d.informat", r"informatis", r"informatique", r"guichet unique",
    r"archivage [ée]lectronique", r"ANPTIC", r"ANSSI", r"ONI\b", r"CIL\b",
    r"protection des donn[ée]es", r"donn[ée]es [àa] caract[èe]re personnel",
    r"intelligence artificielle", r"facture normalis", r"identification",
    r"registre unique", r"carte d.identit",
]
TERM_RE = re.compile("|".join(TERMS), re.IGNORECASE)

# labels that match a term but are not digital-activity spend
EXCLUDE = re.compile(
    r"r[ée]seau (routier|hydrographique|[ée]lectrique|d.adduction|de distribution"
    r"|hydraulique|de transport|d.assainissement|g[ée]od[ée]sique|de nivellement|urbain|de pistes)"
    r"|r[ée]seaux? d.AEP|r[ée]mun[ée]ration du personnel|indemnit[ée]s de d[ée]part"
    r"|prise en charge des ressources humaines|SOLDE MENSUELLE"
    r"|d.information et de sensibilisation|campagnes? d.information"
    r"|consommables informatiques|mat[ée]riels? informatiques? et p[ée]ri",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Amounts are NOT parsed here, deliberately.
#
# `pdftotext -table` renders a within-number digit-group gap and a between-column
# gap with the same character, and its per-page column model does not align the
# `AE CP AE CP AE CP` header row with the data rows (measured 2026-07-25 on the
# FY2024 volume: header AE at col 107, the row's own first figure at col 115).  So
# neither a numeric regex nor positional slicing can be trusted -- both return a
# plausible number from the wrong year, which is exactly the silent failure the
# strategy library warns about.
#
# This scan is therefore a LOCATOR, per BUDGET-EXTRACT.md 4a and the strategy
# library ("the cross-vote scan finds lines, not context"): it says which sections
# and which coded lines carry digital money.  The figures are read by hand from the
# `-table` text of those pages and cross-footed against the section totals before
# anything is recorded.
# ---------------------------------------------------------------------------


def numeric_tail(tail, label):
    """The row's figures as printed, verbatim -- for the eye, not for arithmetic."""
    rest = tail[len(label):] if tail.startswith(label) else tail
    return re.sub(r"\s{2,}", "  ", rest).strip()


def scan(path):
    section = section_name = None
    prog = prog_name = action = action_name = chap = chap_name = None
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            m = SECTION_RE.match(line)
            if m:
                section, section_name = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
                continue
            m = CODE_RE.match(line)
            if not m:
                continue
            kind = ("programme" if m.group(2) else "action" if m.group(4)
                    else "chapitre" if m.group(6) else "activite")
            code = m.group(3) or m.group(5) or m.group(7) or m.group(9)
            tail = m.group(10)
            # the label is everything before the first run of 2+ spaces that is
            # followed by a digit -- i.e. before the figures start.
            msplit = re.search(r"\s{2,}(?=[\d(])", tail)
            raw_label = tail[: msplit.start()] if msplit else tail
            label = re.sub(r"\s+", " ", raw_label).strip()
            figures = numeric_tail(tail, raw_label)
            if kind == "programme":
                prog, prog_name = code, label
                action = chap = None
            elif kind == "action":
                action, action_name = code, label
                chap = None
            elif kind == "chapitre":
                chap, chap_name = code, label
            rows.append(dict(
                lineno=lineno, kind=kind, section=section, section_name=section_name,
                programme=prog, programme_name=prog_name, action=action,
                action_name=action_name, chapitre=chap, chapitre_name=chap_name,
                code=code, label=label, figures=figures,
            ))
    return rows


def is_digital(r):
    if EXCLUDE.search(r["label"] or ""):
        return False
    hay = " ".join(filter(None, [r["label"], r.get("programme_name") or "",
                                 r.get("action_name") or "", r.get("chapitre_name") or ""]))
    return bool(TERM_RE.search(hay))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("year")
    ap.add_argument("--all", action="store_true", help="print every coded line, not just hits")
    ap.add_argument("--section", help="restrict to one section code")
    args = ap.parse_args()

    rows = scan(args.path)
    sel = [r for r in rows if (args.all or is_digital(r))]
    if args.section:
        sel = [r for r in sel if r["section"] == args.section]
    print(f"{args.path}: {len(rows)} coded lines, {len(sel)} selected")
    by_section = {}
    for r in sel:
        by_section.setdefault((r["section"], r["section_name"]), []).append(r)
    for (sec, name), rs in sorted(by_section.items(), key=lambda kv: kv[0][0] or ""):
        print(f"\n=== Section {sec} : {name}")
        for r in rs:
            print(f"  {r['kind'][:5]:5} {r['code']:10} "
                  f"[p{r['programme']}/{r['action']}/{r['chapitre']}] "
                  f"{r['label'][:62]:62} | {r['figures']}")


if __name__ == "__main__":
    main()
