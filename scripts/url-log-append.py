#!/usr/bin/env python3
"""url-log-append.py — write one disposition line into logs/sweep-url_log.md.

INGEST.md step 11: the line is written **at the item's disposition**, not batched at the
end of the run, so a run that dies takes no adjudication record with it. All four
dispositions, not just admissions — a dropped item is exactly the one a sweep must not
fetch again.

Usage:  python scripts/url-log-append.py admitted https://example.com/a-story
        python scripts/url-log-append.py dropped  URL [URL ...]
Normalisation is INGEST.md step 2's, shared with the sweeps' pre-fetch filter.

Concurrency: every write takes an exclusive lock (`<log>.lock`), because up to thirty
Phase A slices write this file at once and every loss here has been silent.

`acquisition` is refused for a URL whose disposition is already `admitted` — see
`already_admitted()` — and the call exits 3 having written its other URLs.

Ingest's drops also carry a code (INGEST.md step 11):
        python scripts/url-log-append.py dropped --code off-topic --batch deep-3-2026-09-24 URL
`--code` writes one row per URL to `sweep/ingest/drop-log-YYYY-MM-DD.csv`
(`sweep_batch,url,reason`, the sweeps' own drop-log columns) under the same lock, so the
manifest can join what ingest threw back to the sweep that staged it. The code is refused
unless it is in DROP_CODES. A sweep calling `dropped` passes no `--code`: its drop-log is
its own.
"""
import csv, re, sys, os, time, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vault_lib import normalise_url

LOG = "logs/sweep-url_log.md"
INDEX = "lookups/raw-url-index.csv"
LOCK = LOG + ".lock"
LOCK_STALE_SECS = 30
LOCK_TIMEOUT_SECS = 10
# TRACK and FRAGMENT_IS_IDENTITY now live in vault_lib, with normalise_url() itself.
VALID = ("admitted", "dropped", "contradiction", "acquisition")
# intake.md §7's closed vocabulary, plus `no-value` — the one reason only ingest can give
# (CLAUDE.md -> *Duplicates*, "Drop"). Change it there first, then here.
DROP_CODES = (
    "out-of-window", "already-seen", "duplicate-in-run", "inadmissible-origin", "off-topic",
    "off-place", "no-development", "headline-only-stub", "url-dead", "fetch-blocked",
    "already-held", "syndicated-copy", "date-unestablished", "not-this-slice",
    "fails-record-test", "no-value",
)
INGEST_DROP_LOG = "sweep/ingest/drop-log-{}.csv"


def norm(u):
    """The one normalisation contract, `vault_lib.normalise_url()`.

    This was a second implementation until 2026-09-22, and the two drifted exactly
    where it mattered: `vault_lib` percent-decodes and this did not, so a non-ASCII
    URL was keyed one way in this log and another in `lookups/raw-url-index.csv`,
    and a tier-1 `grep -F` never matched its own log row. `raw-url-index.py` already
    states the rule this now follows: the function is never re-implemented, or the
    gates disagree about what is held.
    """
    return normalise_url(u)


def acquire_lock(timeout=LOCK_TIMEOUT_SECS, interval=0.1):
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except OSError:
            # `except OSError`, not `except FileExistsError`. On Windows a file that
            # another process is deleting sits in a delete-pending state, and an O_EXCL
            # create against it raises PermissionError (EACCES) rather than
            # FileExistsError — so the moment one caller released the lock while another
            # was taking it, the taker crashed with a traceback and its row was never
            # written. Measured 2026-09-16: 7 of 288 rows lost across 24 concurrent
            # writers, then 1 of 288 on the rerun. That is the same silent loss this lock
            # was added to stop, arriving through the lock's own error handling.
            # Any failure to create the lock now means "held, or momentarily
            # uncreatable" — wait and retry; a genuinely impossible path falls out at the
            # timeout below, which fails loudly.
            try:
                if time.time() - os.path.getmtime(LOCK) > LOCK_STALE_SECS:
                    os.remove(LOCK)          # stale lock from a crashed caller
                    continue
            except OSError:
                pass
            if time.time() > deadline:
                sys.exit("url-log-append.py: could not acquire %s within %ss" % (LOCK, timeout))
            time.sleep(interval)


def release_lock():
    try:
        os.remove(LOCK)
    except OSError:
        pass


def already_admitted(normed, text):
    """Is this URL's disposition already `admitted` — held in raw/, or logged so here?

    `acquisition` is the one verb that cannot be true of such a URL. An acquisition is a
    document the wiki *wants and does not hold* (`CLAUDE.md` -> *Working the base*), and
    `INGEST.md` step 2 tells the sweeps' tier-1 gate that an `acquisition` row is **not an
    adjudication**. So a second row carrying that verb against a URL the base already holds
    makes the gate return two answers for one key, one of which disclaims itself.

    It is written by mistake in one specific shape, five times on 2026-09-16 alone: an
    *admitted* source raises an acquisition for some other document that has no URL of its
    own, and the slice, having only this appender and a verb, writes the row against the
    admitting item's URL. The document is not this URL and never was.
    """
    if re.search(r'^\d{4}-\d{2}-\d{2} \| admitted \| ' + re.escape(normed) + r'(\s|$)', text, re.M):
        return "already logged `admitted` here"
    try:
        with open(INDEX, encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh):
                if row and row[0] == normed:
                    return "already held in raw/ (%s)" % (row[2] if len(row) > 2 else "?")
    except OSError:
        pass
    return None


def pop_flag(args, name):
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args):
        sys.exit("url-log-append.py: %s needs a value" % name)
    value = args[i + 1]
    del args[i:i + 2]
    return value


def append_drop_codes(today, code, batch, normed):
    """One `sweep_batch,url,reason` row per URL; called under the log's lock."""
    path = INGEST_DROP_LOG.format(today)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        if new:
            w.writerow(["sweep_batch", "url", "reason"])
        for n in normed:
            w.writerow([batch, n, code])


def main():
    args = sys.argv[1:]
    code, batch = pop_flag(args, "--code"), pop_flag(args, "--batch") or ""
    if len(args) < 2 or args[0] not in VALID:
        sys.exit("usage: url-log-append.py {%s} [--code CODE --batch SWEEP_BATCH] URL [URL ...]"
                 % "|".join(VALID))
    disp, urls = args[0], args[1:]
    if code is not None and (disp != "dropped" or code not in DROP_CODES):
        sys.exit("url-log-append.py: --code goes with `dropped` and one of: %s" % ", ".join(DROP_CODES))
    today = datetime.date.today().isoformat()

    refused = []
    acquire_lock()
    try:
        b = open(LOG, "rb").read()
        eol = "\r\n" if b"\r\n" in b else "\n"
        t = b.decode("utf-8")

        normed = [norm(u) for u in urls]
        if disp == "acquisition":
            kept = []
            for n in normed:
                why = already_admitted(n, t)
                if why:
                    refused.append((n, why))
                else:
                    kept.append(n)
            normed = kept

        lines = [f"{today} | {disp} | {n}" for n in normed]
        new_content = (eol.join(lines) + eol) if lines else ""

        # Match the section header by PREFIX, not exact string equality — a header
        # commonly carries a time and pass suffix ("## 2026-09-07 20:23 - ingest"),
        # so an exact "## " + today match almost never fires and the append silently
        # no-ops. The topmost line starting with "## " + today is today's most recent
        # section (the log is newest-first); append inside it.
        # `[^\r\n]*`, not `.*$`: `.` matches a carriage return and multiline `$` matches
        # before the `\n`, so on a CRLF log the old pattern ended *between* the `\r` and
        # the `\n` and the row was spliced in there — a fused header line, and the exact
        # shape of the 2026-08-29..09-01 fusions. The live log is LF, so this never fired
        # on it; it would have fired on the first CRLF one.
        line_re = re.compile(r'^## ' + re.escape(today) + r'[^\r\n]*', re.M)
        m = line_re.search(t)
        if not lines:
            pass                      # nothing admissible to write; leave the file alone
        elif m:
            pos = m.end()
            if t[pos:pos + len(eol)] == eol:
                pos += len(eol)
                if t[pos:pos + len(eol)] == eol:
                    pos += len(eol)
            else:
                # The header is the file's last line and carries no terminator, so an
                # append here would fuse the first row onto it. Terminate it first: an
                # unterminated append is the mechanism behind the 167 fused lines holding
                # 16,980 dispositions that this log carried between 2026-08-27 and
                # 2026-09-07 (measured over every revision in git, housekeeping job 83).
                new_content = eol + eol + new_content
            t = t[:pos] + new_content + t[pos:]
        else:
            header = "## " + today
            m2 = re.search(r'^## \d{4}-\d{2}-\d{2}', t, re.M)
            block = header + eol + eol + new_content + eol
            if m2:
                t = t[:m2.start()] + block + t[m2.start():]
            else:
                t = t + ("" if (not t or t.endswith(eol)) else eol) + eol + block

        if lines:
            # Write a sibling file and swap it in, never rewrite the log in place: an
            # in-place `open(LOG, "wb")` that fails mid-write (EINVAL under concurrent
            # readers on Windows) leaves the shared log truncated. The swap is retried
            # because Windows refuses os.replace while another process holds the target.
            tmp = LOG + ".tmp"
            with open(tmp, "wb") as f:
                f.write(t.encode("utf-8"))
            for attempt in range(50):
                try:
                    os.replace(tmp, LOG)
                    break
                except OSError:
                    if attempt == 49:
                        raise
                    time.sleep(0.1)
        if code is not None and normed:
            append_drop_codes(today, code, batch, normed)
    finally:
        release_lock()

    for ln in lines:
        print(ln)

    if refused:
        for n, why in refused:
            sys.stderr.write(
                "url-log-append.py: refused `acquisition` for %s - %s.\n"
                "  This log is keyed by URL and holds one disposition per key; that key's\n"
                "  disposition is `admitted`. An acquisition raised *by* an admitted source\n"
                "  names a different document, and if that document has no URL of its own it\n"
                "  has no key here: record it on reviews/acquisitions.md and nowhere else.\n"
                % (n, why))
        sys.exit(3)


if __name__ == "__main__":
    main()
