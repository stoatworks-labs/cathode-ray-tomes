#!/usr/bin/env python3
"""Recover the tables that reached the corpus as paragraphs.

A DIP-switch table, an option-switch chart, a connector pin-out: tesseract
reads each row onto one line and sets its cells apart by whitespace an order
of magnitude wider than a word space. `ocr_page` then joined the words with
single spaces, and the geometry was gone. What the reader received was a
sentence made of two rows:

    cache/text  Off 70 seconds per coin F On 90 seconds per coin $ N

    the page    Off      70 seconds per coin           F
                On       90 seconds per coin      $    N

Nothing downstream was missing: `build_blocks` has emitted `tr` for a line
with two or more wide gaps since tables were added, and the reader splits a
`tr` on those gaps into cells. The machinery worked and nothing fed it.

`ocrlib.table_rows` is the part that was missing, and it needs the page rather
than the line: a gap wide enough to be a column is also wide enough to be the
hole OCR leaves where it dropped a word, and the two are told apart by whether
the cell start *repeats* down the page. That is also what keeps a two-column
prose page safe -- a page must show three columns before anything is split,
and two is what prose in two columns looks like.

So the pages are re-read from their cached scans, as `parts_rows.py` re-reads
the parts lists, and for the same reason: `cache/text/` holds blocks, and the
word boxes that say where a cell began are not in them. The whole document is
read, not the page, because a heading is defined relative to the body text of
the document it sits in and `build_blocks` needs those headings to know which
lines stand alone.

A page is kept only when it gained a table *and* still says exactly what it
said before. That is the guard that makes this safe to run over 4,000
documents: a page whose re-read does not reproduce its own published text did
not read the same way twice, and is left exactly as it was.

    python3 tools/page_tables.py --all           # every document
    python3 tools/page_tables.py --doc <id>      # one, with its pages listed
    python3 tools/page_tables.py --all --force   # ignore what is already done

`cache/text/` is not written to. It is the ingest's checkpoint and stays the
OCR as it came out; the tables are merged into the published document by
`build_assets.py`, exactly as `build_drawings.py` merges its flags.
"""
import argparse, glob, json, os, re, sys, time
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import (ocr_page, classify_headings, build_blocks,  # noqa: E402
                    running_headers)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
DOCS = os.path.join(ROOT, "web", "data", "doc")
OUT = os.path.join(ROOT, "data", "tables")
# Which documents have been read. A document with no tables writes no file, so
# without this a second --all would re-read every one of them -- which is most
# of the corpus, and hours of it.
STATE = os.path.join(CACHE, "tables-state.json")
# {document id: tesseract language}, written by tools/detect_language.py. The
# 43 Japanese manuals have to be re-read in Japanese or the re-read does not
# reproduce the text it is checked against, and every page of them is dropped.
_LANG_PATH = os.path.join(ROOT, "data", "languages.json")
LANGUAGES = json.load(open(_LANG_PATH)) if os.path.exists(_LANG_PATH) else {}


def _same_text(a, b):
    """Whether two readings of a page say the same thing.

    A word hyphenated across a line break is rejoined within a block but not
    across one, so a row breaking out of a paragraph can leave `Desig-` and
    `nator` where `Designator` stood. That is the one difference allowed here,
    because rejecting it would throw away the parts lists it happens on.
    Anything else means the page did not read the same way twice.
    """
    norm = lambda s: re.sub(r"-\s+", "", " ".join(s.split()))
    return norm(a) == norm(b)


def _reference(did):
    """The reading a page is checked against: what is published, if anything is.

    Not `cache/text/` on its own. The checkpoint is per checkout and can be
    behind the corpus -- this one still held the 43 Japanese manuals in the
    English they were first read in, while `web/data/doc/` had them in
    Japanese -- and a page checked against the stale reading passes while
    replacing the shipped text with something else entirely. The published
    document is what a table is spliced into, so it is what has to agree.
    """
    for path in (os.path.join(DOCS, did + ".json"),
                 os.path.join(CACHE, "text", did + ".json")):
        if os.path.exists(path):
            try:
                return json.load(open(path))
            except Exception:
                pass
    return None


def tables_for(did):
    """-> {page number: blocks} for the pages of `did` that read as tables."""
    pngs = sorted(glob.glob(os.path.join(CACHE, "pages", did, "*.webp")))
    doc = _reference(did)
    if not pngs or doc is None:
        return {}

    lang = LANGUAGES.get(did, "eng")
    page_lines = [ocr_page(p, psm="1", lang=lang)[1] for p in pngs]
    heads = classify_headings(page_lines)
    skip = running_headers(page_lines)

    out = {}
    for pg, h, lines in zip(doc.get("pages", []), heads, page_lines):
        blocks = build_blocks(lines, h, skip=skip)
        if not any(b["k"] == "tr" for b in blocks):
            continue
        was = " ".join(b.get("t", "") for b in pg.get("blocks", []))
        now = " ".join(b["t"] for b in blocks)
        if _same_text(was, now):
            out[str(pg["n"])] = blocks
    return out


def rebuild(did):
    """-> (pages that became tables, rows recovered), writing data/tables/."""
    path = os.path.join(OUT, did + ".json")
    found = tables_for(did)
    os.makedirs(OUT, exist_ok=True)
    if found:
        tmp = path + ".tmp"
        json.dump(found, open(tmp, "w"), separators=(",", ":"))
        os.replace(tmp, path)
    elif os.path.exists(path):
        os.unlink(path)          # it used to find tables here and no longer does
    return len(found), sum(1 for b in sum(found.values(), []) if b["k"] == "tr")


def load(did):
    """The recovered tables for a document, as {page number: blocks}."""
    path = os.path.join(OUT, did + ".json")
    if not os.path.exists(path):
        return {}
    try:
        return {int(k): v for k, v in json.load(open(path)).items()}
    except Exception:
        return {}


def apply_tables(doc, rows):
    """Replace a document's pages with their recovered tables, in place.

    Shared with build_assets.py so the two cannot disagree about what is
    published, the way apply_flags is shared with build_drawings.py.
    """
    n = 0
    for page in doc.get("pages", []):
        blocks = rows.get(page["n"])
        if blocks:
            page["blocks"] = blocks
            n += 1
    return n


def _one(did):
    try:
        return (did, *rebuild(did), None)
    except Exception as e:                       # a scan tesseract cannot read
        return did, 0, 0, str(e)


def _load_state():
    try:
        return set(json.load(open(STATE)))
    except Exception:
        return set()


def _save_state(done):
    tmp = STATE + ".tmp"
    json.dump(sorted(done), open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, STATE)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", help="one document id")
    ap.add_argument("--all", action="store_true", help="every document")
    ap.add_argument("--force", action="store_true", help="ignore what is done")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if not (a.doc or a.all):
        sys.exit("pass --doc <id> or --all")

    ids = [a.doc] if a.doc else sorted(
        os.path.basename(p)[:-5]
        for p in glob.glob(os.path.join(CACHE, "text", "*.json")))
    seen = set() if a.force else _load_state()
    ids = [i for i in ids if i not in seen]
    if a.limit:
        ids = ids[: a.limit]
    print(f"{len(ids)} document(s) to read", flush=True)

    t0, done, docs, pages, rows = time.time(), 0, 0, 0, 0
    with cf.ProcessPoolExecutor(a.workers) as ex:
        for did, n, r, err in ex.map(_one, ids):
            done += 1
            if not err:
                seen.add(did)
            if err:
                print(f"  skip {did}: {err}", flush=True)
            if n:
                docs += 1
                pages += n
                rows += r
            if a.doc:
                for p in sorted(load(did)):
                    print(f"  page {p}")
            if done % 50 == 0 or done == len(ids):
                _save_state(seen)
                el = time.time() - t0
                rate = done / el * 60 if el else 0
                print(f"  [{done}/{len(ids)}] {pages} pages · {rows} rows | "
                      f"{rate:.0f} docs/min | ETA "
                      f"{(len(ids) - done) / max(rate, 0.1):.0f} min", flush=True)
    _save_state(seen)
    print(f"{pages} page(s) across {docs} document(s) read as tables, "
          f"{rows} rows recovered, in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
