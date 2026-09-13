#!/usr/bin/env python3
"""url-log-append.py — write one disposition line into logs/sweep-url_log.md.

INGEST.md step 11: the line is written **at the item's disposition**, not batched at the
end of the run, so a run that dies takes no adjudication record with it. All four
dispositions, not just admissions — a dropped item is exactly the one a sweep must not
fetch again.

Usage:  python scripts/url-log-append.py admitted https://example.com/a-story
        python scripts/url-log-append.py dropped  URL [URL ...]
Normalisation is INGEST.md step 2's, shared with the sweeps' pre-fetch filter.
"""
import re, sys, os, time, datetime

LOG = "logs/sweep-url_log.md"
LOCK = LOG + ".lock"
LOCK_STALE_SECS = 30
LOCK_TIMEOUT_SECS = 10
TRACK = ("utm_", "fbclid", "gclid", "msclkid", "mc_cid", "mc_eid", "igshid", "ref_src", "spm")
# Hosts where the `#fragment` is the document identity, not a scroll position — an IATI
# d-portal activity is addressed by its fragment, so stripping it wrote every activity
# from one publisher into this log under one key. Mirrors vault_lib.FRAGMENT_IS_IDENTITY;
# the two must not drift, or the log and the index disagree about what is held.
FRAGMENT_IS_IDENTITY = ("d-portal.org", "d-portal.iatistandard.org")
VALID = ("admitted", "dropped", "contradiction", "acquisition")


def norm(u):
    u = re.sub(r'^https?://', '', u.strip())
    u, _hash, frag = re.sub(r'^www\.', '', u).partition('#')
    if '?' in u:
        base, q = u.split('?', 1)
        keep = [kv for kv in q.split('&') if kv and not any(kv.lower().startswith(t) for t in TRACK)]
        u = base + ('?' + '&'.join(keep) if keep else '')
    head, _, tail = u.partition('/')
    out = (head.lower() + ('/' + tail if tail else '')).rstrip('/')
    if frag.strip() and head.lower() in FRAGMENT_IS_IDENTITY:
        out += '#' + frag.strip()
    return out


def acquire_lock(timeout=LOCK_TIMEOUT_SECS, interval=0.1):
    deadline = time.time() + timeout
    while True:
        try:
            fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return
        except FileExistsError:
            # steal a stale lock left by a crashed caller rather than hang forever
            try:
                if time.time() - os.path.getmtime(LOCK) > LOCK_STALE_SECS:
                    os.remove(LOCK)
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


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in VALID:
        sys.exit("usage: url-log-append.py {%s} URL [URL ...]" % "|".join(VALID))
    disp, urls = sys.argv[1], sys.argv[2:]
    today = datetime.date.today().isoformat()

    acquire_lock()
    try:
        b = open(LOG, "rb").read()
        eol = "\r\n" if b"\r\n" in b else "\n"
        t = b.decode("utf-8")
        lines = [f"{today} | {disp} | {norm(u)}" for u in urls]
        new_content = eol.join(lines) + eol

        # Match the section header by PREFIX, not exact string equality — a header
        # commonly carries a time and pass suffix ("## 2026-09-07 20:23 - ingest"),
        # so an exact "## " + today match almost never fires and the append silently
        # no-ops. The topmost line starting with "## " + today is today's most recent
        # section (the log is newest-first); append inside it.
        line_re = re.compile(r'^## ' + re.escape(today) + r'.*$', re.M)
        m = line_re.search(t)
        if m:
            pos = m.end()
            if t[pos:pos + len(eol)] == eol:
                pos += len(eol)
                if t[pos:pos + len(eol)] == eol:
                    pos += len(eol)
            t = t[:pos] + new_content + t[pos:]
        else:
            header = "## " + today
            m2 = re.search(r'^## \d{4}-\d{2}-\d{2}', t, re.M)
            block = header + eol + eol + new_content + eol
            t = (t[:m2.start()] + block + t[m2.start():]) if m2 else (t + eol + block)

        open(LOG, "wb").write(t.encode("utf-8"))
    finally:
        release_lock()

    for ln in lines:
        print(ln)


if __name__ == "__main__":
    main()
