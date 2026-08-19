#!/usr/bin/env python3
"""Add heading/outline structure to documents ingested before structure
detection existed.

Re-OCRs from the cached page images rather than re-rendering the PDF, and
rewrites the existing text JSON in place. Documents that already carry an
outline are skipped, so this is safe to re-run.
"""
import json, os, sys, glob, argparse, time
import concurrent.futures as cf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import (ocr_page, classify_headings, build_outline,
                    build_blocks, running_headers)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")

def needs_backfill(fp, force=False):
    try:
        d = json.load(open(fp))
    except Exception:
        return False
    if force:
        return True
    if "outline" not in d:
        return True
    # documents from before block extraction still carry a flat text field
    return any("blocks" not in p for p in d.get("pages", []))

def process(fp):
    doc = json.load(open(fp))
    did = doc["id"]
    pngs = sorted(glob.glob(os.path.join(CACHE, "pages", did, "*.webp")))
    if not pngs:
        return did, 0, "no cached pages"
    page_lines = []
    for img in pngs:
        _, lines = ocr_page(img, psm="1")
        page_lines.append(lines)
    heads = classify_headings(page_lines)
    skip = running_headers(page_lines)
    for pg, h, lines in zip(doc.get("pages", []), heads, page_lines):
        if h:
            pg["heads"] = h
        else:
            pg.pop("heads", None)
        pg["blocks"] = build_blocks(lines, h, skip=skip)
        pg.pop("text", None)          # superseded by blocks
    outline = build_outline(heads)
    doc["outline"] = outline
    meta = doc.setdefault("meta", {})
    meta["sections"] = len(outline)
    meta["blocks"] = sum(len(p.get("blocks", [])) for p in doc.get("pages", []))
    tmp = fp + ".tmp"
    json.dump(doc, open(tmp, "w"), separators=(",", ":"))
    os.replace(tmp, fp)
    return did, len(outline), None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--force", action="store_true",
                    help="regenerate outlines that already exist (after a classifier change)")
    a = ap.parse_args()

    files = [f for f in sorted(glob.glob(os.path.join(CACHE, "text", "*.json")))
             if needs_backfill(f, a.force)]
    if a.limit:
        files = files[: a.limit]
    print(f"{len(files)} documents need structure backfill", flush=True)

    t0, done, sections = time.time(), 0, 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        for did, n, err in ex.map(process, files):
            done += 1
            sections += n
            if err:
                print(f"  skip {did}: {err}", flush=True)
            if done % 10 == 0 or done == len(files):
                el = time.time() - t0
                rate = done / el * 60 if el else 0
                print(f"  [{done}/{len(files)}] {sections} sections | "
                      f"{rate:.1f} docs/min | ETA {(len(files)-done)/max(rate,0.1):.0f} min",
                      flush=True)
    print(f"backfilled {done} documents, {sections} sections")

if __name__ == "__main__":
    main()
