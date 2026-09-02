#!/usr/bin/env python3
"""Ingest a PDF that is already vector, without OCR'ing it.

The arcade corpus has none of these: measured over 2,405 upstream PDFs, none
has a text layer and none has vector artwork, so `ingest.py` rasterises every
page and reads it with tesseract. The Sony service manuals surveyed in
data/sources/gamingdoc.json are the opposite — the SCPH-30000 manual is 78 of
82 pages of native vector whose schematic sheets carry their net names,
designators and component values as real text. Running tesseract over a render
of that would be transcribing a document we can simply read.

Output is byte-compatible with ingest.py's, so everything downstream —
build_search, build_doc_stats, build_assets, the reader — is unchanged:

  cache/pdf/<id>.pdf              the original
  cache/pages/<id>/p####.webp     150 dpi reading images
  cache/svg/<id>/p####.svgz       sheets, as vector, gzipped
  cache/text/<id>.json            {id, pages:[{n,words,heads?,blocks}], outline, meta}

Only line extraction differs. `pdftotext -bbox-layout` emits the same
block/line/word hierarchy tesseract's TSV does, so once lines are in ocrlib's
shape the heading classifier, running-header filter, block builder and outline
builder are reused verbatim. Coordinates are scaled from points to the same
150 dpi the raster path works in, because _body_height() discards lines shorter
than 8 units and 9pt type would fall through that at 72 dpi.

What does have to be decided fresh is which pages are drawings. build_drawings.py
answers that from OCR debris — symbol density, the marks tesseract could not
resolve — and a vector page has no debris to measure. The signal here is
structural instead: a schematic sheet is hundreds of one-word blocks scattered
across the page, and a parts list or a prose page is not. Measured against the
SCPH-30000 manual read by hand (64 drawing pages, 16 not):

    page                       blocks   words   prose-word share
    prose chapter                  27     261              0.808
    electrical parts list         131    1585              0.725
    exploded view                  27      76              0.342
    schematic sheet              1201    2162              0.147

"prose-word share" is the fraction of a page's words living in blocks of eight
words or more. It separates the parts list from the sheet, which block count
alone does not. The rule below finds 53 of the 64 drawings and wrongly hides
none — the 11 it misses are mixed pages, a drawing beside a real CAUTION
paragraph, which keep their text. That is the same trade build_drawings.py
makes and for the same reason: hiding a parts list is worse than showing a
drawing's labels.

Flags are written into cache/text/ here rather than into data/drawings.json,
which is the one place this departs from the raster path. For a scan the flag
is a downstream judgement about OCR that must not contaminate the ingest's
checkpoint; here it is a property of the extraction itself — we know the page
is a sheet because we read its geometry — so it belongs with the extraction.
build_drawings.py skips any document whose meta says `via: vector`.
"""
import argparse, glob, gzip, json, os, re, shutil, statistics, subprocess, sys, tempfile
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import classify_headings, build_outline, build_blocks, running_headers

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
STATE = os.path.join(ROOT, "data", "ingest-state.json")
SURVEY = os.path.join(ROOT, "data", "sources", "gamingdoc.json")

NS = "{http://www.w3.org/1999/xhtml}"
READ_DPI = 150
PT_TO_PX = READ_DPI / 72.0          # pdftotext reports points; ocrlib expects pixels

# A page is a sheet when its words are scattered rather than set in paragraphs.
SHEET_BLOCKS   = 400                # this many blocks is a schematic whatever else is on it
SHEET_MIN_BLKS = 100                # otherwise: scattered *and* busy,
SHEET_MAX_WORDS = 120               # or scattered and nearly empty (a small diagram)
PROSE_SHARE    = 0.50
PROSE_BLOCK    = 8                  # words in a block for it to count as prose
# Words per block is what stops a parts list being taken for a sheet. Measured:
# schematic 1.1-2.0, electrical parts list 4.7-12.1, prose 10-25. The PSP-2000
# parts lists sit at 4.7-5.3 with a low prose share, because their cells are
# too short to count as prose blocks, and the share test alone hid all four.
SHEET_MAX_WPB  = 3.0


def sh(*args, timeout=1800):
    return subprocess.run(args, capture_output=True, timeout=timeout).stdout


def checkpoint(did, pages, words):
    """Record the document as done in ingest.py's own state file.

    Not optional. ingest.py skips what the state says is done, and without
    this it re-reads every vector document through tesseract and overwrites
    the extraction with a worse one — measured, the SCPH-30000 went from
    52,241 exact words to 22,164 OCR'd ones before this was added.
    """
    st = json.load(open(STATE)) if os.path.exists(STATE) else {"done": {}, "failed": {}}
    st["done"][did] = {"pages": pages, "words": words, "via": "vector"}
    st["failed"].pop(did, None)
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w"))
    os.replace(tmp, STATE)


def bbox_xml(pdf):
    """pdftotext -bbox-layout, with a fallback for PDFs that crash it.

    The SCPH-9000 manual's Producer string is mojibake — a broken multi-byte
    run in "Acrobat Distiller 3.0.2J (Power Mac…)" — and poppler dies writing
    the XML header with an uncaught std::out_of_range, leaving a truncated
    document and exit status 0. Rewriting the file through pdftocairo drops
    the metadata and the same extraction then succeeds on all 28 pages.
    """
    xml = sh("pdftotext", "-bbox-layout", pdf, "-").decode("utf-8", "replace")
    try:
        return ET.fromstring(xml)
    except ET.ParseError:
        pass
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        clean = tmp.name
    try:
        sh("pdftocairo", "-pdf", pdf, clean, timeout=600)
        if not os.path.getsize(clean):
            raise RuntimeError("pdftotext produced malformed XML and the "
                               "rewrite failed — send this one to ingest.py")
        xml = sh("pdftotext", "-bbox-layout", clean, "-").decode("utf-8", "replace")
        try:
            return ET.fromstring(xml)
        except ET.ParseError as e:
            raise RuntimeError(f"unreadable text layer even after rewrite: {e}")
    finally:
        os.unlink(clean)


def page_lines(pdf):
    """Lines per page, in ocrlib's shape: {b, pa, t, x, y, w, h, c}.

    Confidence is 100 throughout — this is the document's own text, not a
    reading of it — which keeps classify_headings' min_conf gate a no-op.
    """
    root = bbox_xml(pdf)
    out = []
    for page in root.iter(NS + "page"):
        lines, block_sizes = [], []
        for bi, block in enumerate(page.iter(NS + "block")):
            words_in_block = 0
            for li, line in enumerate(block.iter(NS + "line")):
                words = [w for w in line.iter(NS + "word")]
                text = " ".join((w.text or "") for w in words).strip()
                if not text:
                    continue
                words_in_block += len(words)
                x0 = float(line.get("xMin")); y0 = float(line.get("yMin"))
                x1 = float(line.get("xMax")); y1 = float(line.get("yMax"))
                lines.append({
                    "b": bi, "pa": li, "t": text,
                    "x": int(x0 * PT_TO_PX), "y": int(y0 * PT_TO_PX),
                    "w": int((x1 - x0) * PT_TO_PX),
                    "h": max(int((y1 - y0) * PT_TO_PX), 1),
                    "c": 100.0,
                })
            block_sizes.append(words_in_block)
        out.append((lines, block_sizes))
    return out


def is_sheet(block_sizes):
    """True when the page reads as a drawing rather than as something to set."""
    total = sum(block_sizes)
    if not total:
        return True                                  # a page of pure artwork
    nb = len(block_sizes)
    if nb >= SHEET_BLOCKS:
        # Decisive on its own. The two densest SCPH-30000 sheets carry a notes
        # panel that lifts their words-per-block to 4.8, and gating them on
        # that would set 2,900 net labels as paragraphs.
        return True
    if total / nb >= SHEET_MAX_WPB:          # blocks are cells or sentences, not labels
        return False
    prose = sum(n for n in block_sizes if n >= PROSE_BLOCK)
    share = prose / total
    return share < PROSE_SHARE and (nb >= SHEET_MIN_BLKS or total < SHEET_MAX_WORDS)


def raster_pages(pdf):
    """Pages carrying an embedded image — the ones that are scans after all."""
    hit = set()
    for line in sh("pdfimages", "-list", pdf).decode().splitlines()[2:]:
        p = line.split()
        if p and p[0].isdigit():
            hit.add(int(p[0]))
    return hit


def to_webp(src, dst, quality=82, maxpx=2600):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(src)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if max(im.size) > maxpx:
        r = maxpx / max(im.size)
        im = im.resize((int(im.width * r), int(im.height * r)), Image.LANCZOS)
    im.save(dst, "WEBP", quality=quality, method=4)


def render_svg(pdf, page, dst):
    """One page as SVG, gzipped. These are large — a dense sheet is ~700 KB of
    path data — and gzip takes about 80% of that back off."""
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        path = tmp.name
    try:
        sh("pdftocairo", "-svg", "-f", str(page), "-l", str(page), pdf, path,
           timeout=300)
        if not os.path.getsize(path):
            return 0
        with open(path, "rb") as f, gzip.open(dst, "wb", compresslevel=9) as g:
            shutil.copyfileobj(f, g)
        return os.path.getsize(dst)
    finally:
        os.unlink(path)


def process(did, pdf, svg=True, images=True):
    per_page = page_lines(pdf)
    if not per_page:
        raise RuntimeError("no text layer — this is a job for ingest.py")
    rasters = raster_pages(pdf)

    sheets = {i for i, (_, sizes) in enumerate(per_page, 1) if is_sheet(sizes)}

    # Headings are relative to the document's own body text, so the classifier
    # needs every page — but a sheet's scattered labels are not body text and
    # would drag the median down. Feed it the prose pages and apply the result
    # back by page number.
    prose_idx = [i for i in range(1, len(per_page) + 1) if i not in sheets]
    prose_lines = [per_page[i - 1][0] for i in prose_idx]
    heads = classify_headings(prose_lines) if prose_lines else []
    skip = running_headers(prose_lines) if prose_lines else set()
    head_by_page = dict(zip(prose_idx, heads))

    pages = []
    for n, (lines, _) in enumerate(per_page, 1):
        words = sum(len(l["t"].split()) for l in lines)
        page = {"n": n, "words": words}
        if n in sheets:
            # The labels go in as one block rather than a field of their own.
            # `draw` already stops the reader setting them as prose, and every
            # other consumer — the postings builder, the in-document search,
            # the word count under the sheet — reads blocks and would other-
            # wise miss the most searchable text in the corpus.
            page["draw"] = True
            page["vec"] = True
            page["blocks"] = [{"k": "p", "t": " ".join(l["t"] for l in lines)}]
        else:
            h = head_by_page.get(n) or []
            if h:
                page["heads"] = h
            page["blocks"] = build_blocks(lines, h, skip=skip)
        pages.append(page)

    outline = build_outline([head_by_page.get(i) or [] for i in
                             range(1, len(per_page) + 1)])

    svg_bytes = 0
    if svg:
        out = os.path.join(CACHE, "svg", did)
        os.makedirs(out, exist_ok=True)
        for n in sorted(sheets):
            if n in rasters:                 # a scanned page among vector ones
                continue
            svg_bytes += render_svg(pdf, n, os.path.join(out, f"p{n:04d}.svgz"))

    webp_bytes = 0
    if images:
        out = os.path.join(CACHE, "pages", did)
        # Sheets are published, the rest are not. A page the reader rebuilds as
        # text has no use for its own scan; a sheet is nothing but the scan, and
        # the reader needs dw/dh to reserve its height or a lazy image never
        # enters the viewport and never loads.
        pub = os.path.join(ROOT, "web", "pages", did)
        os.makedirs(out, exist_ok=True)
        os.makedirs(pub, exist_ok=True)
        by_n = {p["n"]: p for p in pages}
        tmp = tempfile.mkdtemp(prefix="crt-vec-")
        try:
            sh("pdftoppm", "-r", str(READ_DPI), "-png", pdf, os.path.join(tmp, "p"))
            for f in sorted(os.listdir(tmp)):
                m = re.search(r"-(\d+)\.png$", f)
                if not m:
                    continue
                n = int(m.group(1))
                dst = os.path.join(out, "p%04d.webp" % n)
                to_webp(os.path.join(tmp, f), dst)
                webp_bytes += os.path.getsize(dst)
                if n in sheets:
                    shutil.copyfile(dst, os.path.join(pub, "p%04d.webp" % n))
                    from PIL import Image
                    with Image.open(dst) as im:
                        by_n[n]["dw"], by_n[n]["dh"] = im.size
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # A text layer can be present and still not readable: a subsetted font with
    # no usable ToUnicode map gives correctly positioned U+FFFD. Four of the
    # five manuals measured are clean; the SCPH-70000 is 3.6% overall and 58%
    # on its worst page. Record it rather than shipping the garbage quietly —
    # a document above a few percent wants the OCR path instead.
    all_text = "".join((p.get("sheetText") or
                        " ".join(b["t"] for b in p["blocks"])) for p in pages)
    undecoded = all_text.count("�") / max(len(all_text), 1)

    text_out = os.path.join(CACHE, "text", did + ".json")
    os.makedirs(os.path.dirname(text_out), exist_ok=True)
    json.dump({"id": did, "pages": pages, "outline": outline,
               "meta": {"pageCount": len(pages), "bytes": os.path.getsize(pdf),
                        "words": sum(p["words"] for p in pages),
                        "blocks": sum(len(p["blocks"]) for p in pages),
                        "sections": len(outline),
                        "via": "vector", "sheets": len(sheets),
                        "undecoded": round(undecoded, 4)}},
              open(text_out, "w"), separators=(",", ":"))

    words = sum(p["words"] for p in pages)
    checkpoint(did, len(pages), words)

    return {"pages": len(pages), "sheets": len(sheets),
            "words": words, "sections": len(outline),
            "undecoded": undecoded,
            "svgBytes": svg_bytes, "webpBytes": webp_bytes}


def publish(did):
    """Re-copy a document's sheet scans from the cache into web/pages/.

    The scans are a build output that lives in git, so anything that resets the
    tree loses them while the cache still has everything needed to put them
    back. Re-running the whole extraction to recover a file copy is the wrong
    shape, hence this.
    """
    text = os.path.join(CACHE, "text", did + ".json")
    if not os.path.exists(text):
        return 0
    doc = json.load(open(text))
    if doc.get("meta", {}).get("via") != "vector":
        return 0
    src_dir = os.path.join(CACHE, "pages", did)
    pub = os.path.join(ROOT, "web", "pages", did)
    n = 0
    for page in doc.get("pages", []):
        if not page.get("draw"):
            continue
        name = "p%04d.webp" % page["n"]
        src = os.path.join(src_dir, name)
        if not os.path.exists(src):
            continue
        os.makedirs(pub, exist_ok=True)
        shutil.copyfile(src, os.path.join(pub, name))
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish-only", action="store_true",
                    help="re-copy sheet scans from the cache; no extraction")
    ap.add_argument("--doc", help="document id from data/sources/gamingdoc.json")
    ap.add_argument("--pdf", help="a PDF to read directly, for trying one out")
    ap.add_argument("--id", help="document id to file --pdf under")
    ap.add_argument("--all", action="store_true", help="every doc classed vector")
    ap.add_argument("--no-svg", action="store_true")
    ap.add_argument("--no-images", action="store_true")
    a = ap.parse_args()

    if a.publish_only:
        total = pages = 0
        for f in sorted(glob.glob(os.path.join(CACHE, "text", "*.json"))):
            n = publish(os.path.basename(f)[:-5])
            if n:
                total += 1; pages += n
        print(f"republished {pages} sheet scans across {total} documents")
        return

    jobs = []
    if a.pdf:
        jobs.append((a.id or os.path.basename(a.pdf)[:12], a.pdf, os.path.basename(a.pdf)))
    else:
        survey = json.load(open(SURVEY))["documents"]
        want = [d for d in survey
                if d.get("ingest") == "vector" and (a.all or d["id"] == a.doc)]
        if not want:
            sys.exit("no matching vector documents; pass --doc <id> or --all")
        for d in want:
            jobs.append((d["id"], os.path.join(CACHE, "gamingdoc", d["id"] + ".pdf"),
                         d["title"]))

    for did, pdf, title in jobs:
        if not os.path.exists(pdf):
            print(f"  ! {did}: no cached PDF — run tools/survey_gamingdoc.py")
            continue
        r = process(did, pdf, svg=not a.no_svg, images=not a.no_images)
        warn = "  ⚠ text does not decode" if r["undecoded"] > 0.02 else ""
        print(f"{did}  {r['pages']:4d}p  {r['sheets']:3d} sheets  "
              f"{r['words']:7,d} words  {r['sections']:3d} sections  "
              f"svg {r['svgBytes']/1e6:5.1f} MB  webp {r['webpBytes']/1e6:5.1f} MB  "
              f"{title[:40]}{warn}", flush=True)


if __name__ == "__main__":
    main()
