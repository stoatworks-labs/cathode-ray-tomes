#!/usr/bin/env python3
"""Rebuild a parts-list page's rows from the geometry the flat text threw away.

`cache/text/` stores a page as an ordered list of blocks, which is right for
prose and wrong for a table. Tesseract puts the two halves of a ruled parts
list in *separate blocks* — the vertical rule between the columns is a block
boundary — so flattening the page emits every item, part number and quantity
first and every description afterwards. The extractor then pairs each row's
part number with the *next* row's item number and calls that its description:

    cache/text  31 281-0004-12 33 281-0014-28 37 281-0134-12 … SCR, 8-32 x
                .750 PN HD PHIL  SCR 8-18 x .750 PN HD PHIL  …
    what it     item=31  part=281-0004-12  desc=''       (the description it
    gave        found was row 33's data, and was dropped as junk)

The rows are not lost, only unlabelled: every cell still knows where it sat on
the page. Re-reading the cached page image gives the word boxes back, and
banding the lines by their vertical centre puts each row together again:

    banded      31 281-0004-12 1   SCR, 8-32 x .750 PN HD PHIL

which is exactly the shape `extract_parts.RECORD` already reads, quantity
column and all. Nothing downstream changes; it is fed better text.

Only the pages that need it are re-read — the ones whose rows came out with no
description — so a page the flat text handled correctly is never disturbed.
Results are cached in `cache/rows/<id>.json`, keyed by page number.

    python3 tools/parts_rows.py --all          # every document that needs it
    python3 tools/parts_rows.py --doc <id>     # one
    python3 tools/parts_rows.py --all --force  # ignore the cache

`cache/text/` is not written to. It is the ingest's checkpoint and stays the
OCR as it came out, exactly as `build_drawings.py` leaves it.
"""
import argparse, glob, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import ocr_page
from extract_parts import from_document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(CACHE, "rows")

# Two cells a row is a page with one column of text beside another, which is
# what prose in two columns looks like; a table has at least three. Banding
# prose would interleave its columns, which is the one thing that must never
# happen to this text.
MIN_CELLS = 2
CELL_GAP = "   "        # what extract_parts and ocrlib read as a column gap


def band(lines):
    """Lines regrouped into rows by vertical centre, cells left to right."""
    if not lines:
        return []
    hs = sorted(l["h"] for l in lines)
    med = hs[len(hs) // 2]
    bands = {}
    for l in lines:
        # Centre, not top: a row's cells share a baseline but not always a
        # height, and a cell set in a larger face lands in the band above.
        bands.setdefault(round((l["y"] + l["h"] / 2) / max(med * 0.8, 1)),
                         []).append(l)
    rows = []
    for key in sorted(bands):
        cells = sorted(bands[key], key=lambda l: l["x"])
        rows.append(CELL_GAP.join(c["t"] for c in cells))
    return rows


def pages_needing_rows(doc):
    """Pages whose extracted rows came out with no description."""
    return sorted({r["page"] for r in from_document(doc) if not r["desc"]})


def rebuild(did, doc, force=False):
    """-> (pages read, pages that were already cached), writing cache/rows/."""
    want = pages_needing_rows(doc)
    if not want:
        return 0, 0
    path = os.path.join(OUT, did + ".json")
    have = {}
    if os.path.exists(path) and not force:
        have = json.load(open(path))
    read = cached = 0
    for n in want:
        if str(n) in have:
            cached += 1
            continue
        img = os.path.join(CACHE, "pages", did, "p%04d.webp" % n)
        if not os.path.exists(img):
            continue
        _text, lines = ocr_page(img)
        rows = band(lines)
        # A page that does not band into rows is left to the flat text rather
        # than replaced by something worse.
        if sum(1 for r in rows if r.count(CELL_GAP) >= MIN_CELLS - 1) < 3:
            continue
        have[str(n)] = "\n".join(rows)
        read += 1
    if have:
        os.makedirs(OUT, exist_ok=True)
        json.dump(have, open(path, "w"), separators=(",", ":"))
    return read, cached


def load(did):
    """The banded rows for a document, as {page number: text}."""
    path = os.path.join(OUT, did + ".json")
    if not os.path.exists(path):
        return {}
    return {int(k): v for k, v in json.load(open(path)).items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", help="one document id")
    ap.add_argument("--all", action="store_true", help="every document that needs it")
    ap.add_argument("--force", action="store_true", help="ignore the cache")
    a = ap.parse_args()
    if not (a.doc or a.all):
        sys.exit("pass --doc <id> or --all")

    ids = [a.doc] if a.doc else sorted(
        os.path.basename(p)[:-5]
        for p in glob.glob(os.path.join(CACHE, "text", "*.json")))

    t0 = time.time()
    docs = read = cached = 0
    for did in ids:
        fp = os.path.join(CACHE, "text", did + ".json")
        if not os.path.exists(fp):
            continue
        try:
            doc = json.load(open(fp))
        except Exception:
            continue
        r, c = rebuild(did, doc, force=a.force)
        if r or c:
            docs += 1
            read += r
            cached += c
            if a.doc:
                print(f"{did}: {r} page(s) read, {c} already cached")
    print(f"{read} page(s) re-read across {docs} document(s) "
          f"({cached} already cached) in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
