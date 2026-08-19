#!/usr/bin/env python3
"""Fetch, rasterise and OCR the arcadertfm PDF corpus.

Every upstream PDF is a flat scan with no text layer and no vector content, so
each page has to be rendered to an image and OCR'd to make it searchable.

Per document it produces:
  cache/pdf/<id>.pdf              original, byte-for-byte (uploaded to R2)
  cache/pages/<id>/p####.webp     150 dpi reading images
  cache/hi/<id>/p####.webp        300 dpi, schematic-bearing docs only
  cache/text/<id>.json            {pages:[{n,text,words}], meta}

Resumable: completed doc ids are checkpointed and skipped on re-run.
"""
import json, os, re, sys, subprocess, tempfile, shutil, time, argparse, urllib.parse, urllib.request
import concurrent.futures as cf
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import (ocr_page, classify_headings, build_outline,
                    build_blocks, page_text, running_headers)

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
STATE = os.path.join(ROOT, "data", "ingest-state.json")
UA    = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
        "(KHTML, like Gecko) Chrome/126 Safari/537.36"

READ_DPI, HI_DPI = 150, 300
_lock = Lock()

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"done": {}, "failed": {}}

def save_state(st):
    with _lock:
        tmp = STATE + ".tmp"
        json.dump(st, open(tmp, "w"))
        os.replace(tmp, STATE)

def fetch(url, dest, attempts=4):
    """Upstream URLs contain raw spaces and parentheses, so quote the path only.

    Retries with backoff: a brief loss of connectivity previously failed 847
    documents in one run, all of which were individually fine.
    """
    p = urllib.parse.urlsplit(url)
    safe = urllib.parse.urlunsplit(
        (p.scheme, p.netloc, urllib.parse.quote(p.path), p.query, p.fragment))
    req = urllib.request.Request(safe, headers={"User-Agent": UA})
    last = None
    for i in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
            return os.path.getsize(dest)
        except urllib.error.HTTPError as e:
            if e.code in (403, 404, 410):     # genuinely absent; do not retry
                raise
            last = e
        except Exception as e:                # transport-level: worth retrying
            last = e
        if i < attempts - 1:
            time.sleep(2 ** i * 3)
    raise last

def page_count(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    return 0

def render(pdf, outdir, dpi, fmt="png"):
    """pdftoppm needs -r as a separate arg, and numbers pages without zero
    padding, so sort numerically -- lexical sort puts p-10 before p-2."""
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", str(dpi), "-" + fmt, pdf,
                    os.path.join(outdir, "p")],
                   capture_output=True, timeout=1800)
    files = [f for f in os.listdir(outdir) if f.endswith("." + fmt)]
    def pageno(f):
        m = re.search(r"-(\d+)\.", f)
        return int(m.group(1)) if m else 0
    return sorted(files, key=pageno)

def to_webp(src, dst, quality=82, maxpx=2600):
    from PIL import Image
    # These are trusted local renders, and D-size drawings legitimately exceed
    # Pillow's 179 Mpx bomb guard (Arm Wrestling is 266 Mpx).
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if max(im.size) > maxpx:
        r = maxpx / max(im.size)
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=quality, method=4)

def ocr(png):
    """Return (text, word_count, lines). One tesseract pass yields both the
    plain text and the line geometry used for heading detection."""
    try:
        txt, lines = ocr_page(png, psm="1")
        return txt, len(txt.split()), lines
    except subprocess.TimeoutExpired:
        return "", 0, []

def process(doc):
    did, hi = doc["id"], doc["schematic"]
    pdf = os.path.join(CACHE, "pdf", did + ".pdf")
    os.makedirs(os.path.dirname(pdf), exist_ok=True)
    if not os.path.exists(pdf) or os.path.getsize(pdf) == 0:
        fetch(doc["src"], pdf)

    n = page_count(pdf)
    if not n:
        raise RuntimeError("unreadable pdf")

    pages_dir = os.path.join(CACHE, "pages", did)
    text_out  = os.path.join(CACHE, "text", did + ".json")
    os.makedirs(os.path.dirname(text_out), exist_ok=True)

    tmp = tempfile.mkdtemp(prefix="crt-")
    try:
        pngs = render(pdf, tmp, READ_DPI)
        if not pngs:
            raise RuntimeError(f"render produced no pages (pdfinfo said {n})")
        os.makedirs(pages_dir, exist_ok=True)
        pages, page_lines = [], []
        for i, fn in enumerate(pngs, 1):
            src = os.path.join(tmp, fn)
            to_webp(src, os.path.join(pages_dir, f"p{i:04d}.webp"))
            txt, wc, lines = ocr(src)
            pages.append({"n": i, "words": wc})
            page_lines.append(lines)

        # Heading detection needs the whole document: a heading is defined
        # relative to the body-text size of the document it sits in.
        heads = classify_headings(page_lines)
        skip = running_headers(page_lines)
        for pg, h, lines in zip(pages, heads, page_lines):
            if h:
                pg["heads"] = h
            # Blocks are the readable document; plain text is derived from them
            # for search rather than stored twice.
            pg["blocks"] = build_blocks(lines, h, skip=skip)
        outline = build_outline(heads)

        json.dump({"id": did, "pages": pages, "outline": outline,
                   "meta": {"pageCount": len(pages), "bytes": os.path.getsize(pdf),
                            "words": sum(p["words"] for p in pages),
                            "blocks": sum(len(p.get("blocks", [])) for p in pages),
                            "sections": len(outline)}},
                  open(text_out, "w"), separators=(",", ":"))
        return len(pages), sum(p["words"] for p in pages)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", help="comma-separated machine slugs to do first")
    ap.add_argument("--schematics-first", action="store_true")
    a = ap.parse_args()

    docs = json.load(open(os.path.join(ROOT, "data", "index", "docs.json")))
    st = load_state()

    if a.only:
        want = set(a.only.split(","))
        docs = [d for d in docs if d["machine"] in want]
    if a.schematics_first:
        docs.sort(key=lambda d: not d["schematic"])

    todo = [d for d in docs if d["id"] not in st["done"]]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(todo)} documents to ingest ({len(st['done'])} already done)", flush=True)

    t0, done = time.time(), 0
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(process, d): d for d in todo}
        for fut in cf.as_completed(futs):
            d = futs[fut]
            done += 1
            try:
                pc, wc = fut.result()
                st["done"][d["id"]] = {"pages": pc, "words": wc}
                st["failed"].pop(d["id"], None)
            except Exception as e:
                st["failed"][d["id"]] = str(e)[:200]
                print(f"  FAIL {d['title'][:50]}: {str(e)[:90]}", flush=True)
            if done % 10 == 0 or done == len(todo):
                save_state(st)
                el = time.time() - t0
                rate = done / el if el else 0
                eta = (len(todo) - done) / rate / 60 if rate else 0
                pg = sum(v["pages"] for v in st["done"].values())
                print(f"  [{done}/{len(todo)}] {pg} pages OCR'd | "
                      f"{rate*60:.1f} docs/min | ETA {eta:.0f} min", flush=True)
    save_state(st)
    print(f"done={len(st['done'])} failed={len(st['failed'])}")

if __name__ == "__main__":
    main()
