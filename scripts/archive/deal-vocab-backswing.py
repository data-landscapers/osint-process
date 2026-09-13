#!/usr/bin/env python3
"""spent — one-off DEAL-VOCAB backswing: normalises Instrument / Status / Beneficiary type
in every `## Deal record` to `lookups/deal-vocabs.csv`, moving any wording the vocabulary
value does not carry into `## Notes`. Run once, 2026-08-20; kept for the audit trail.

Usage: python scripts/deal-vocab-backswing.py [--apply]
"""
import csv
import glob
import re
import sys

DATE = "2026-08-20"
FIELDS = {
    "Instrument": ("lookups/deal-instrument-map.csv", "instrument"),
    "Status": ("lookups/deal-status-map.csv", "status"),
    "Beneficiary type": ("lookups/deal-beneficiary-type-map.csv", "beneficiary_type"),
}

# Step 2 — the eight wordings the map left at REVIEW, ruled from their sources.
RULED = {
    "Program-for-Results (PforR)": ("Commercial Loan", "PAD3541: an IBRD operation for Seychelles, a non-IDA borrower"),
    "Standard loan (IATI finance-type 421)": ("Commercial Loan", "BOAD sovereign lending on terms the activity does not state; IATI 421 is the generic loan code and carries no concessionality"),
    "Procurement contract award": ("Grant", "UNDP-funded supply of ICT equipment, non-repayable"),
    "Funding + technology + technical support": ("Grant", "foundation money; the technology and technical-support components are not separately priced"),
    "Investment under NTRA data-centre licence": ("Self Funded", "Hassan Allam capitalising its own licensed build"),
    "Mixed": ("Self Funded", "a corporate own-balance-sheet envelope; the quantified sub-components are held as their own records with their own instruments"),
    "5G spectrum licences": ("Self Funded", "operator capital committed to 5G; the licence fee runs operator-to-state, which DEAL-VOCAB.md section 4 leaves open as a question about the register rather than about this instrument"),
    "Spectrum award (410 MHz)": ("Self Funded", "operator capital committed to 5G; the licence fee runs operator-to-state, which DEAL-VOCAB.md section 4 leaves open as a question about the register rather than about this instrument"),
}

# Step 1 — this wording is a pointer to an explanation already in ## Notes, not content to move.
POINTER = "Concessional loan *(source label, unverified — see Notes)*"

# Step 3 — records holding no row for a field. Instrument and beneficiary type are read from
# the source; status is Unknown throughout, since none of the fifty sources states one and
# inferring it from project-progress prose is the currency error CLAUDE.md forbids.
FILL_INSTRUMENT = {
    "2015-01-01-zte-cmr-001-record.md": ("Grant", 'the source: "an agreement for a grant worth $12,119,042 USD"'),
    "2015-03-31-eximbank-cn-uga-001-record.md": ("Concessional Loan", 'the source: "a preferential loan framework agreement"'),
    "2017-01-01-ceiec-ago-2017-angola-civil-criminal-id-platform-bw01.md": ("Line of Credit", 'the despacho: "uma linha de crédito comercial a negociar"'),
    "2017-01-01-eximbank-cn-ken-002-record.md": ("Concessional Loan", 'the source: "an RMB 438,000,000 government concessional loan (GCL) agreement"'),
    "2017-01-01-eximbank-cn-nga-001-record.md": ("Buyer's Credit", 'the source: "an $84 million syndicated buyer\'s credit facility agreement"'),
    "2017-05-20-eximbank-cn-cog-001-record.md": ("Buyer's Credit", 'the source: "a preferential buyer\'s credit (PBC) agreement"'),
    "2017-05-20-eximbank-cn-cog-003-record.md": ("Buyer's Credit", 'the source: "a preferential buyer\'s credit (PBC) agreement"'),
    "2017-12-22-eximbank-cn-gmb-001-record.md": ("Concessional Loan", 'the stated terms: 2% interest, a 7-year grace period'),
    "2018-02-08-china-mofcom-sen-001-record.md": ("Concessional Loan", 'the source: "an RMB 1.05 billion government concessional loan"'),
    "2018-02-22-boc-cmr-001-record.md": ("Commercial Loan", 'the source: "a $41,780,769 (CFA 23 billion) commercial loan agreement"'),
    "2018-08-31-boc-civ-003-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2018-08-31-boc-civ-004-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2018-09-28-eximbank-cn-mli-001-record.md": ("Concessional Loan", 'the source: "an RMB 1.134 billion government concessional loan (GCL) agreement"'),
    "2019-05-22-boc-civ-006-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2019-05-22-boc-civ-007-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2020-01-01-eximbank-cn-cod-002-record.md": ("Concessional Loan", 'the source: "an RMB 1,050,000,000 government concessional loan (GCL) agreement"'),
    "2020-01-01-icbc-zaf-007-record.md": ("Buyer's Credit", 'the source: "a ZAR 2.251 billion syndicated buyer\'s credit loan agreement"'),
    "2020-01-01-world-bank-swz-2020-eswatini-cbhis-health-mis-bw01.md": ("Unknown", "PAD3539 states a US$20m project and no instrument"),
    "2020-04-24-boc-civ-009-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2020-04-30-boc-civ-010-record.md": ("Commercial Loan", "Bank of China lending on unstated terms, per the map's reading of a bare loan"),
    "2020-10-30-eximbank-cn-gha-005-record.md": ("Concessional Loan", 'the source: "a $218,490,000.00 concessional loan agreement"'),
    "2020-10-30-eximbank-cn-gha-006-record.md": ("Concessional Loan", 'the source: "a $39 million concessional loan agreement"'),
    "2023-01-01-world-bank-ago-2023-projecto-njila-registration-bw10.md": ("Unknown", 'the source says only "um financiamento de 250 milhões de dólares"'),
    "2024-01-01-african-development-bank-cmr-2024-prsec-electricity-reform-bw12.md": ("Unknown", "the source states the AfDB contribution and not its instrument"),
    "2024-01-01-world-bank-cmr-2024-prsec-electricity-reform-bw12.md": ("Unknown", "PforR is the lending modality; Cameroon is an IDA-blend borrower and the source does not say which window"),
    "2025-01-01-african-startup-fund-algeria-xaf-2025-startup-financing-bw05.md": ("Unknown", "the source states a USD 1bn commitment routed through a fund and no instrument"),
    "2025-01-01-axian-telecom-xea-2025-partner2connect-4g-pledge-bw03.md": ("Self Funded", "an operator's own capital commitment to its 4G build"),
    "2025-01-01-eib-mrt-2025-ellalink-submarine-cable-connection-bw04.md": ("Unknown", "the source states no instrument"),
    "2025-01-01-google-zaf-2025-google-cloud-region-johannesburg-bw03.md": ("Self Funded", "Google's own capital in its own cloud region"),
    "2025-01-01-jica-ago-2025-angola-dtt-broadcasting-bw05.md": ("Unknown", 'the source says only that Japan "is investing approximately $10 million"'),
    "2025-01-01-mtn-cameroon-cmr-2025-network-capex-pledge-bw03.md": ("Self Funded", "an operator's own network capex"),
    "2025-01-01-rand-merchant-bank-wingu-africa-2025-data-centres-east-africa-bw03.md": ("Commercial Loan", 'the source: funding "provided by a corporate and investment bank"'),
    "2025-01-01-world-bank-lbr-2025-liberia-great-digital-id-bw03.md": ("Concessional Loan", 'the source: "the World Bank\'s ID Credit Program"; Liberia borrows from IDA'),
    "2026-01-01-european-union-ken-2026-02-digital-partnership-bw13.md": ("Unknown", "the source states a commitment and no instrument"),
    "2026-01-01-google-wethinkcode-2026-soweto-innovation-centre-bw14.md": ("Grant", "a philanthropic commitment to build a centre, non-repayable"),
    "2026-01-01-government-of-china-nam-2026-windhoek-smart-city-bw14.md": ("Unknown", "the source states a committed sum and no instrument"),
    "2026-01-01-islamic-development-bank-mrt-2026-mauritania-digital-transformation-bw11.md": ("Unknown", "terms still under negotiation at the principle agreement"),
    "2026-01-01-telkom-zaf-2026-ai-institute-bw14.md": ("Self Funded", "Telkom's own capital in its own institute"),
    "2026-01-01-world-bank-tgo-2026-wuri-digital-id-top-up-bw15.md": ("Unknown", "the source states five financing agreements and no instrument for this one"),
    "2026-03-24-european-union-nga-2026-global-gateway-digitalisation-bw10.md": ("Unknown", "the source states an investment package and no instrument"),
    "2026-06-01-world-bank-mar-2026-morocco-digital-transformation-acceleration.md": ("Commercial Loan", "World Bank lending to Morocco, an IBRD borrower"),
}

FILL_BENEFICIARY = {
    "PUBLIC": [
        "2015-01-01-zte-cmr-001-record.md", "2015-03-31-eximbank-cn-uga-001-record.md",
        "2017-01-01-eximbank-cn-ken-002-record.md", "2017-05-20-eximbank-cn-cog-001-record.md",
        "2017-05-20-eximbank-cn-cog-003-record.md", "2017-12-22-eximbank-cn-gmb-001-record.md",
        "2018-02-08-china-mofcom-sen-001-record.md", "2018-02-22-boc-cmr-001-record.md",
        "2018-08-31-boc-civ-003-record.md", "2018-08-31-boc-civ-004-record.md",
        "2018-09-28-eximbank-cn-mli-001-record.md", "2019-05-22-boc-civ-006-record.md",
        "2019-05-22-boc-civ-007-record.md", "2020-01-01-eximbank-cn-cod-002-record.md",
        "2020-01-01-icbc-zaf-007-record.md", "2020-04-24-boc-civ-009-record.md",
        "2020-04-30-boc-civ-010-record.md", "2020-10-30-eximbank-cn-gha-005-record.md",
        "2020-10-30-eximbank-cn-gha-006-record.md",
        "2024-01-01-african-development-bank-cmr-2024-prsec-electricity-reform-bw12.md",
        "2024-01-01-banco-santander-cmr-2024-urban-video-surveillance-bw12.md",
        "2024-01-01-china-citic-bank-cmr-2024-urban-video-surveillance-bw12.md",
        "2024-01-01-ifc-sen-2024-senegal-agricultural-payments-digitisation-bw12.md",
        "2024-01-01-world-bank-cmr-2024-prsec-electricity-reform-bw12.md",
        "2024-01-01-world-bank-mar-2024-morocco-social-protection-registry-bw12.md",
        "2024-04-08-caf-undp-2024-digitalisation-administration-publique.md",
        "2024-11-13-caf-france-2024-appui-budgetaire-reformes-mfb-simba.md",
        "2025-01-01-china-citic-bank-cmr-2025-urban-video-surveillance-bw12.md",
        "2025-01-01-cybastion-angola-telecom-2025-cybastion-angola-telecom-bw05.md",
        "2025-01-01-european-union-nga-2025-eu-nigeria-digital-economy-bw07.md",
        "2025-01-01-societe-generale-ago-2025-angola-earth-observation-bw05.md",
        "2025-01-01-world-bank-nga-2025-bridge-fibre-bw08.md",
        "2026-01-01-african-development-bank-nga-2026-nigeria-project-bridge-bw14.md",
        "2026-01-01-commercial-bank-cameroun-cmr-2026-camtel-mne-bw14.md",
        "2026-01-01-egypt-mobile-operators-egy-2026-spectrum-5g-bw08.md",
        "2026-01-01-european-union-ken-2026-cyber-resilience-bw08.md",
        "2026-01-01-gates-foundation-rwa-2026-horizon1000-ai-health-bw08.md",
        "2026-01-01-genew-technologies-cod-2026-congo-river-fibre-bw14.md",
        "2026-01-01-government-of-china-nam-2026-windhoek-smart-city-bw14.md",
        "2026-01-01-islamic-development-bank-mrt-2026-mauritania-digital-transformation-bw11.md",
        "2026-01-01-japan-ben-2026-malaria-ai-geospatial-bw14.md",
        "2026-01-01-sysroad-gmb-2026-gamtel-broadband-ppp-bw07.md",
        "2026-01-01-telkom-zaf-2026-ai-institute-bw14.md",
        "2026-01-01-world-bank-cmr-2026-antic-cirt-cybersecurity-bw14.md",
        "2026-01-01-yas-tanzania-tza-2026-zanzibar-broadband-ppp-bw14.md",
        "2026-06-04-convalt-energy-lso-2026-ai-data-centre-mou-bw14.md",
        "2026-07-27-indo-aid-mdg-2026-maritime-single-window.md",
    ],
    "PRIVATE": [
        "2017-01-01-eximbank-cn-nga-001-record.md",
        "2023-01-01-european-union-tun-2023-viatunisia-cef-digital-bw02.md",
        "2025-01-01-vantage-zaf-2025-johannesburg-data-centre-jv-bw06.md",
        "2025-01-01-wingu-africa-tza-2025-tanzania-data-centre-phase-bw06.md",
        "2026-01-01-equinix-zaf-2026-south-africa-data-centre-expansion-bw14.md",
        "2026-01-01-finnfund-ssd-2026-south-sudan-crei-solar-telecom-bw14.md",
        "2026-01-01-google-akuna-group-2026-ai-creative-education-bw14.md",
        "2026-01-01-ifc-airtel-africa-2026-network-expansion-loan-bw14.md",
        "2026-01-01-mars-growth-capital-nala-2026-payment-rails-facility-bw14.md",
        "2026-01-01-mtn-group-zaf-2026-south-africa-ict-investment-bw14.md",
        "2026-01-01-world-bank-bdi-2026-burundi-pafen-lumitel-bw07.md",
        "2026-03-31-helios-towers-cod-2026-drc-telecom-tower-investment.md",
        "2026-04-08-nexus-core-systems-mar-2026-nexus-ai-factory-bw14.md",
    ],
    "NGO": ["2026-01-01-google-wethinkcode-2026-soweto-innovation-centre-bw14.md"],
}
BENEFICIARY_VALUE = {"PUBLIC": "Public Sector", "PRIVATE": "Private Sector", "NGO": "NGO"}
BENEFICIARY_BASIS = {
    "PUBLIC": "the recipient is a government, ministry or state-owned entity",
    "PRIVATE": "the recipient is a private company",
    "NGO": "the recipient is a not-for-profit training body",
}

# A wording carries more than the vocabulary value when it is annotated: a parenthetical,
# an emphasis block, a dash clause, a semicolon, a joined pair, a figure, or a sentence.
ANNOTATED = re.compile(r"[(*—–;+:]|\d")


def normalise(value):
    return re.sub(r"[^a-z0-9]", "", value.lower())


def load_maps():
    maps, vocab = {}, {}
    for row in csv.DictReader(open("lookups/deal-vocabs.csv", encoding="utf-8")):
        vocab.setdefault(row["field"], {})[normalise(row["value"])] = row["value"]
    for label, (path, field) in FIELDS.items():
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        key = list(rows[0].keys())[0]
        maps[label] = {" ".join((r["source_value"] or "").split()).lower(): (r[key] or "").strip() for r in rows}
    return maps, vocab


def read_cell(text, label):
    m = re.search(r"^\|\s*" + re.escape(label) + r"\s*\|(.*?)\|[ \t]*$", text, re.M)
    return (m.group(1).strip(), m) if m else (None, None)


def append_note(text, line):
    idx = text.find("\n## Notes")
    if idx < 0:
        return text.rstrip("\n") + "\n\n## Notes\n\n" + line + "\n"
    end = text.find("\n## ", idx + 1)
    if end < 0:
        return text.rstrip("\n") + "\n\n" + line + "\n"
    return text[:end].rstrip("\n") + "\n\n" + line + text[end:]


def insert_row(text, label, value, after):
    """Insert `| label | value |` immediately after the first row named in `after`."""
    for anchor in after:
        m = re.search(r"^\|\s*" + re.escape(anchor) + r"\s*\|.*?\|[ \t]*$", text, re.M)
        if m:
            return text[: m.end()] + f"\n| {label} | {value} |" + text[m.end():], True
    m = re.search(r"^\|---\|---\|[ \t]*$", text, re.M)
    if m:
        return text[: m.end()] + f"\n| {label} | {value} |" + text[m.end():], True
    return text, False


def main():
    apply = "--apply" in sys.argv
    maps, vocab = load_maps()
    sep = chr(92)
    stats = {"files": 0, "changed": 0, "cells": 0, "notes": 0, "inserted": 0, "unresolved": []}

    for path in sorted(glob.glob("raw/**/*.md", recursive=True)):
        path = path.replace(sep, "/")
        text = original = open(path, encoding="utf-8").read()
        if "## Deal record" not in text or "retired_deal_id:" in text:
            continue
        stats["files"] += 1
        name = path.split("/")[-1]
        notes = []

        # Order matters: each insertion anchors on the row above it.
        for label in ("Beneficiary type", "Instrument", "Status"):
            field = FIELDS[label][1]
            value, match = read_cell(text, label)

            if value is None:
                if label == "Status":
                    target, basis = "Unknown", "the source states no status"
                elif label == "Instrument":
                    if name not in FILL_INSTRUMENT:
                        stats["unresolved"].append((name, label))
                        continue
                    target, basis = FILL_INSTRUMENT[name]
                else:
                    bucket = next((b for b, files in FILL_BENEFICIARY.items() if name in files), None)
                    if bucket is None:
                        target, basis = "Unknown", "the source names no recipient organisation"
                    else:
                        target, basis = BENEFICIARY_VALUE[bucket], BENEFICIARY_BASIS[bucket]
                anchors = {
                    "Beneficiary type": ["Recipient", "Financier", "Deal ID"],
                    "Instrument": ["Beneficiary type", "Recipient", "Financier"],
                    "Status": ["Instrument", "Beneficiary type", "Recipient"],
                }[label]
                text, ok = insert_row(text, label, target, anchors)
                if not ok:
                    stats["unresolved"].append((name, label + " (no anchor)"))
                    continue
                stats["inserted"] += 1
                notes.append(f"DEAL-VOCAB backswing {DATE} — {label}: no row was held; set to `{target}` — {basis}.")
                continue

            key = " ".join(value.split()).lower()
            if key in maps[label] and maps[label][key]:
                target = maps[label][key]
            elif value in RULED:
                target = RULED[value][0]
            else:
                stats["unresolved"].append((name, f"{label} = {value!r}"))
                continue

            if target not in vocab[field].values():
                stats["unresolved"].append((name, f"{label} target {target!r} not in vocabulary"))
                continue

            if value != target:
                text = text[: match.start(1)] + f" {target} " + text[match.end(1):]
                stats["cells"] += 1
                if normalise(value) != normalise(target) and value != POINTER and ANNOTATED.search(value):
                    basis = f' The ruling rests on {RULED[value][1]}.' if value in RULED else ""
                    notes.append(f'DEAL-VOCAB backswing {DATE} — {label}: source wording "{value}" normalised to `{target}`.{basis}')

        for line in notes:
            text = append_note(text, line)
            stats["notes"] += 1

        if text != original:
            stats["changed"] += 1
            if apply:
                open(path, "w", encoding="utf-8", newline="").write(text)

    print(f"in scope       {stats['files']}")
    print(f"files changed  {stats['changed']}")
    print(f"cells rewritten{stats['cells']:>6}")
    print(f"rows inserted  {stats['inserted']}")
    print(f"notes appended {stats['notes']}")
    print(f"unresolved     {len(stats['unresolved'])}")
    for name, why in stats["unresolved"][:40]:
        print(f"   {name}: {why}")
    print("DRY RUN — pass --apply to write" if not apply else "APPLIED")


if __name__ == "__main__":
    main()
