#!/usr/bin/env python3
"""OCR an image-only PDF to text, in pdftotext-compatible form.

Renders each page with pypdfium2 and runs Tesseract over it, emitting one
text stream with pages separated by form feeds -- the same shape
`pdftotext -layout` produces, so every downstream grep in BUDGET-EXTRACT.md
works unchanged.

Usage
  python scripts/ocr-pdf.py DOC.pdf --lang fra
  python scripts/ocr-pdf.py DOC.pdf --lang por --pages 40-95 -o out.txt
  python scripts/ocr-pdf.py DOC.pdf --lang ara --dpi 400
  python scripts/ocr-pdf.py DOC.pdf --lang fra --psm 6 --digits --threshold 2

Languages installed: eng, fra, por, ara (combine with '+', e.g. fra+eng).

Environment, verified 2026-09-08 (housekeeping 77). Everything this script needs
is already installed persistently and nothing has to be added to run it:

  * Tesseract 5.4.0.20240606, a machine install at
    C:\\Program Files\\Tesseract-OCR\\tesseract.exe -- invoked as a subprocess,
    NOT through pytesseract.
  * tessdata at ~/tools/tessdata: eng, fra, por, ara, osd, rus, spa.
  * pypdfium2 and Pillow, both importable in the interpreter the repo's scripts
    run under (C:\\Users\\bill-\\AppData\\Local\\Python\\pythoncore-3.14-64).

`pytesseract` is NOT importable in that interpreter and is NOT required -- it is
not imported anywhere in this file. An acquisition pass recorded "OCR
unavailable" on 2026-08-25 having tested for pytesseract; that blocker was false
and cost a year of Ivorian statute text. Test THIS script against a real PDF
before recording OCR as unavailable.

Prose comes back clean. Wide numeric tables do not: on a low-DPI scan the
digits read plausibly and wrongly, so cross-foot every figure against the
document's own arithmetic before recording it (BUDGET-EXTRACT.md ss1).

Refuses documents that already carry a usable text layer unless --force:
OCR is slower and worse than the native layer, and running it on a native
PDF is always a mistake.
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import pypdfium2 as pdfium

# Tesseract lives outside the user profile (machine install); the language
# data lives in a user-writable dir because Program Files is not writable.
TESSERACT = os.environ.get("TESSERACT_EXE") or shutil.which("tesseract") or (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)
TESSDATA = os.environ.get("TESSDATA_PREFIX") or os.path.expanduser(
    os.path.join("~", "tools", "tessdata")
)

# Text-layer chars per page below which a PDF counts as image-only.
NATIVE_THRESHOLD = 100


def parse_pages(spec, n_pages):
    """'3', '3-20', '3-' -> a 0-based page index list."""
    if not spec:
        return list(range(n_pages))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            lo, _, hi = part.partition("-")
            lo = int(lo) if lo else 1
            hi = int(hi) if hi else n_pages
        else:
            lo = hi = int(part)
        out.extend(range(lo - 1, min(hi, n_pages)))
    return out


def text_layer_chars(doc, sample):
    """Mean characters per page across a sample of pages."""
    total = 0
    for i in sample:
        total += len(doc[i].get_textpage().get_text_bounded().strip())
    return total / max(1, len(sample))


def ocr_page(png, lang, psm, digits, threshold):
    """Run tesseract over one rendered page; return its text."""
    cmd = [
        TESSERACT, "stdin", "stdout",
        "-l", lang,
        "--psm", str(psm),
        "--tessdata-dir", TESSDATA,
        "-c", "preserve_interword_spaces=1",
        "-c", f"thresholding_method={threshold}",
    ]
    if digits:
        # The language model is what corrupts isolated figures -- it reads
        # 8 as R, 5 as S, 0 as u because it wants words. Whitelisting kills it.
        cmd += ["-c", "tessedit_char_whitelist=0123456789 .,"]
    r = subprocess.run(cmd, input=png, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip())
    return r.stdout.decode("utf-8", "replace")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--lang", default="eng",
                    help="tesseract language(s): eng, fra, por, ara, or 'fra+eng'")
    ap.add_argument("--pages", help="page range, 1-based: '40-95', '3', '10-'")
    ap.add_argument("--dpi", type=int, default=300,
                    help="render resolution (default 300; 400 for dense tables)")
    ap.add_argument("--psm", type=int, default=3,
                    help="tesseract page segmentation mode (3 auto, 6 uniform block)")
    ap.add_argument("--digits", action="store_true",
                    help="whitelist digits and separators -- for numeric columns, "
                         "where the language model corrupts figures into letters")
    ap.add_argument("--threshold", type=int, default=0, choices=(0, 1, 2),
                    help="binarisation: 0 Otsu (default), 1 Leptonica Otsu, "
                         "2 Sauvola (best on faded or low-contrast print)")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("-o", "--out", help="output file (default: stdout)")
    ap.add_argument("--force", action="store_true",
                    help="OCR even if the PDF already has a text layer")
    args = ap.parse_args()

    if not os.path.exists(TESSERACT):
        sys.exit(f"tesseract not found at {TESSERACT} -- set TESSERACT_EXE")

    doc = pdfium.PdfDocument(args.pdf)
    n = len(doc)
    pages = parse_pages(args.pages, n)
    if not pages:
        sys.exit("no pages selected")

    sample = pages[:: max(1, len(pages) // 10)][:10]
    chars = text_layer_chars(doc, sample)
    if chars >= NATIVE_THRESHOLD and not args.force:
        sys.exit(
            f"{args.pdf} already has a text layer ({chars:.0f} chars/page over "
            f"{len(sample)} sampled pages). Use pdftotext -enc UTF-8 -layout, "
            f"not OCR. "
            f"Pass --force to override."
        )

    print(f"OCR {os.path.basename(args.pdf)}: {len(pages)}/{n} pages, "
          f"lang={args.lang}, {args.dpi}dpi, psm={args.psm}, {args.jobs} jobs "
          f"(text layer {chars:.0f} chars/page)", file=sys.stderr)

    scale = args.dpi / 72.0
    results = [None] * len(pages)
    started = time.time()
    done = 0

    # pdfium is not thread-safe, so render on the main thread and hand the
    # rendered bitmaps to the pool. Render in chunks so a 900-page scan does
    # not hold 900 bitmaps in memory at once.
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        chunk = args.jobs * 2
        for start in range(0, len(pages), chunk):
            batch = pages[start:start + chunk]
            futures = []
            for idx in batch:
                bitmap = doc[idx].render(scale=scale, grayscale=True)
                buf = bitmap.to_pil()
                png = io.BytesIO()
                buf.save(png, format="PNG")
                futures.append(pool.submit(ocr_page, png.getvalue(), args.lang,
                                           args.psm, args.digits, args.threshold))
            for offset, fut in enumerate(futures):
                try:
                    results[start + offset] = fut.result()
                except Exception as exc:  # a page that will not OCR is blank, not fatal
                    print(f"  page {batch[offset] + 1}: FAILED {exc}", file=sys.stderr)
                    results[start + offset] = ""
                done += 1
            rate = done / max(0.001, time.time() - started)
            print(f"  {done}/{len(pages)} pages ({rate:.1f} pp/s, "
                  f"{(len(pages) - done) / max(0.001, rate):.0f}s left)",
                  file=sys.stderr)

    text = "\f".join(r or "" for r in results)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {args.out} ({len(text):,} chars)", file=sys.stderr)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
