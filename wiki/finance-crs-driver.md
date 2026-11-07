<!-- reader: cc; type: spec -->
# finance-crs-driver.md — OECD CRS deal → finance record

The driver `wiki/finance-record-spec.md` calls for the OECD Creditor Reporting System. **The method is `wiki/finance-donor-reporting.md`**, shared with IATI; this file holds the CRS field mapping and the screens only the CRS needs.

**It runs over the CRS harvest's African extract**, one year at a time. The harvest runs in RESEARCH each January (`scripts/crs-africa-extract.py`, built and run for 2015–2024) and stages the records as `X:\new-queue\dataset-crs-{YYYY}\`, `READY` written last; `pull-new-queue.py` brings them in and the `dataset-` prefix puts them in the backfill lane. Ingest decides admission, as for any record.

**Expect duplicates.** A CRS year is more than a year old when it arrives, so much of it is already held from IATI or the news. **Every deal is cross-referenced against the held records before it is staged** (`finance-donor-reporting.md` → *Cross-reference, not enrichment*), and the manifest counts how many matched.

---

## The input — the African extract, not the bulk file

The extract is the bulk `CRS {YYYY} data.zip` screened on geography (`finance-donor-reporting.md` → *Selection* 1), with every OECD column kept and `iso3` and `region` inserted after `RecipientName`. The DAC recipient code maps to ISO-3 through RESEARCH's `DAC-CRS-recipient-codes.csv`; Seychelles (DAC 270, graduated 2018) is added by hand, and Saint Helena (DAC 276) is out.

**The bulk `.txt` is not what its readme says.** Only the header is quoted. `LongDescription` holds bare `\n` and stray `"`, and records end in `\r\n`. Split on `\r\n` and `|` with no quote handling, and stop on any record whose field count differs from the header's. A standard CSV reader misparses it. The extract the script writes is an ordinary CSV.

`RegionName` is DAC's grouping, not the wiki's: Malawi, Mozambique, Zambia and Zimbabwe are `XSA` here and Eastern Africa to DAC; São Tomé is `XWA` here and Middle Africa to DAC. The four sub-regional codes were not used in 2015–17 (1028 starts in 2018, the other three in 2019).

## The CRS's own screens

**Mechanical, after geography and before the shared vintage floor.** They are the CRS's, as IATI's hierarchy rule is IATI's.

1. **Commitment rows only: `USD_Commitment` ≠ 0, compared as a number** (the file writes zero as `0.000000`). A CRS file is one year's flows of an activity; a disbursement-only row belongs to a commitment in an earlier year's file, and where that year is before 2015 the floor drops it anyway. **So the CRS builds no disbursed-only record.**
2. **Negative commitments are kept and netted** into the deal's sum, as IATI's are. They are rare: 105 rows across 2015–24, mostly tiny de-obligations. **A negative row with no positive commitment in its own year amends the held deal with the same donor and `CrsID`**: it goes through the cross-reference step and is not staged as a deal of its own.
3. **`Bi_Multi` ≠ 2.** These are the multilateral outflows the OECD added in April 2026; its readme says to exclude them to avoid double counting.
4. **A deal is donor + `CrsID` + `Year`.** One activity's commitment is split across rows by sector or channel, so its rows are summed into one record, and screened, read and built as one.

Then the shared pre-screen runs, over title and both descriptions, because of volume. In a 2024 test it kept 4,316 of 76,641 commitment rows (5.6%) on a topic pattern, with known noise from "programming" under `capacity.training`, and 2,112 more on a bare *digital* or *data*.

## The five facts, from the CRS

**`finance-record-spec.md` owns the test. This says where each fact is found.**

1. **Financier** — `DonorName`, with `AgencyName` as the agency in `## Notes`. **`ChannelName` is the implementer, never the financier.**
2. **Recipient** — `iso3`, else `region`, from the extract. A deal whose rows name more than one recipient aggregates as the shared rule says.
3. **Amount** — Σ `USD_Commitment` × 10⁶ over the deal's rows, rounded to whole USD. **Amounts are already USD million at current prices, so there is no FX.**
4. **Date** — `CommitmentDate`, at day precision, else `Year`, padded.
5. **Purpose** — the shared *Subject* rule over `ProjectTitle`, `ShortDescription` and `LongDescription`, with `PurposeCode` as the bracketed DAC provenance.

**The vintage floor tests `CommitmentDate`'s year, else `Year`**; `ExpectedStartDate` plays no part.

## Fields beyond the five facts

| Record field | From the CRS |
|---|---|
| title | `ProjectTitle`, else `ShortDescription` |
| description | `LongDescription`, else `ShortDescription` |
| instrument | `Finance_T` (110 grant, 4xx loan), else `FlowName`, through `DEAL-VOCAB.md`; the code goes in `## Notes` |
| status | blank: the CRS carries none |
| start / end year | `ExpectedStartDate` / `CompletionDate` — a bare four-digit year or blank; 1900 is a CRS placeholder and blanks the cell |
| original amount + currency | the USD figure: `Commitment_National` is not used, since `CurrencyCode` is a DAC numeric code and the field reads equal to USD in a 2023 sample |
| co-financing | blank: one donor per deal |
| lead-financier flag | true |
| amount quality | `stated` |
| native project ID | `CrsID`, plus `ProjectNumber` — the key the IATI cross-reference matches on |
| IATI ID | blank, unless the cross-reference finds one |
| digital flag | `DIG` in `## Notes`, as provenance only |
| deal key | `crs-{DonorCode}-{CrsID}-{Year}`, the record's filename id |
| source URL | below |
| source type | dataset |
| access date | the run date |

Everything the deal does not state is **left blank with a reason**, never guessed and never `0`.

## Source URL — the donor → recipient → year view

The CRS has no public page per activity, and the Data Explorer's project drill-down (`MD_DIM=DD`) returns nothing through the API. So the URL is the narrowest view that works, **the donor's commitments to the recipient in that year**, from the row's `DEDonorcode` and `DERecipientcode`:

```
https://data-explorer.oecd.org/vis?lc=en&df[ds]=DcdDisseminateFinalDMZ&df[id]=DSD_CRS%40DF_CRS&df[ag]=OECD.DCD.FSD&dq={DEDonorcode}.{DERecipientcode}.1000.._T._T.C.Q._T..&pd={Year}%2C{Year}&to[TIME_PERIOD]=false
```

The key's dimensions, in order: donor, recipient, sector (1000 = all), measure (blank = all), channel, modality, flow type (`C` commitments), price base (`Q` current), drill-down (`_T`), microdata ID, unit, then time. `DEDonorcode` reads e.g. `CAN`, `5WB001`, `9PRIV1626`; `DERecipientcode` e.g. `BEN`, or `F_X` for Africa regional.

**Where either code is blank, use the dataflow at that year alone**: the same URL with `dq=DAC..1000.100._T._T.C.Q._T..`.

## The yearly re-run

**Each January run also re-runs the previous year**, because the OECD revises past years *(Bill, 2026-11-05)*. The two extracts are diffed by deal key and **only what changed is staged**: new deals, changed amounts, and deals that disappeared. Each goes through the cross-reference step, so ingest updates the held record and adds no second one. The run's manifest carries the diff counts beside the shared ones, and the CRS screens' own: rows dropped as disbursement-only, as `Bi_Multi` 2, and negatives routed as amendments.
