#!/usr/bin/env python3
"""Decide which pages are drawings, so the reader stops setting them as prose.

The reader rebuilds every page from its OCR blocks and renders them as
paragraphs. Its only escape hatch fires when a page yields *zero* blocks, and a
schematic sheet almost never yields zero — tesseract finds plenty of marks on a
drawing and calls them words. So a dense sheet comes out as a page of
fluent-looking nonsense, which is what 10-Yard Fight's pages 31, 32 and 37 are.

What makes this hard is not spotting the nonsense. It is spotting the nonsense
without also hiding the illustrated parts lists, DIP-switch tables and pin-out
tables, which are the most useful pages in a service manual and which score
almost identically on every naive text measure — they are made of part numbers
and abbreviations, so they have as few long words as a drawing does. Measured
over a hand-read sample:

    page                     long-word rate   symbol density
    prose chapter                     0.407            0.006
    illustrated parts list            0.101            0.000
    DIP-switch table                  0.183            0.004
    schematic sheet                   0.060            0.048

Long words alone put the parts list and the schematic in the same bucket.
Symbol density — the share of characters that are neither letters, digits,
space nor ordinary punctuation — separates them, because what tesseract emits
off a drawing is full of the marks it could not resolve and a typeset table is
not. That is the discriminator this uses, and it is still only a score.

So nothing is hidden on a score alone. Two independent sources have to agree:

  named   the document's own outline calls that page a schematic, a PCB
          assembly, a wiring diagram, an illustrated parts list. This is the
          manual telling us what the page is, which beats anything computed
          from the OCR of it.
  reads   the page does not read as prose.

Pages where both fire are marked `draw`: the reader shows the scan instead of
the text. Pages where only the score fires are marked `noise`: the reader keeps
the text, because it may be a parts list, but says plainly that it came off a
drawing and should not be read as prose. Hiding a parts list would be a worse
failure than leaving some noise visible, so the ambiguous case keeps the text.
"""
import argparse, glob, json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# What a manual calls a page when the page is a drawing.
#
# STRICT names a kind of page that is a drawing whatever else is true of it —
# "POWER SUPPLY SCHEMATIC 1 of 1" is not the heading of a prose chapter.
STRICT = re.compile(
    r"\b(schematic|wiring\s+diagram|interconnect(?:ion)?\s+diagram|"
    r"pcb\s+assembly|assembly\s+drawing|parts?\s+illustration|"
    r"illustrated\s+parts|component\s+location|cabinet\s+wiring|"
    r"harness\s+(?:diagram|assembly))\b", re.I)

# LOOSE is suggestive rather than conclusive. "TOP PCB (M58-A-A)" heads a board
# drawing in 10-Yard Fight, but "PCB" and "diagram" both turn up in the headings
# of ordinary prose sections, so a LOOSE match is never enough on its own — it
# has to be corroborated by the page's own text scoring as drawing noise.
LOOSE = re.compile(r"\b(pcb|p\.c\.b|diagram|layout|drawing|figure)\b", re.I)

STOP = set("""the a an and or of to in on at for with from by is are was were be
been it its this that these those as if not no but which when where how then
than there their they you your we our will can may must should would shall each
other any all both more most such only same so up out off over under again
further once here who whom what while do does did done has have had""".split())

TOKEN = re.compile(r"[A-Za-z]{2,}")
# Everything a typeset page legitimately contains. What is left over is what
# tesseract invented off a drawing.
SYMBOL = re.compile(r"[^A-Za-z0-9\s.,;:()\-/+%'\"&#*=\[\]]")

# Below this there is not enough text to judge, and the reader's own
# empty-page fallback already covers those pages.
MIN_TOKENS = 40
# A page with fewer long words than this does not read as prose.
LONG_RATE = 0.20
# Symbol density at or above this is a drawing rather than a table, on the text
# alone. The gap in the sample is 0.006 against 0.037, so this sits in open
# space — but only just, and one hand-read parts list scores 0.037 because its
# dashed leader rules shed marks. That page is the reason the score alone never
# hides anything.
SYMBOL_RATE = 0.030
# Where the outline has already said the page is a board or a diagram, the text
# is corroborating evidence rather than the whole case, so it is held to a lower
# bar. 10-Yard Fight's CENTER PCB sheet scores 0.027: unambiguous rubbish to
# read (long-word rate 0.060), and it would fall through the uncorroborated
# threshold by three thousandths.
SYMBOL_CORROBORATE = 0.020

# Why a page was called a drawing. The distinction decides whether its scan is
# published, not whether it is a drawing:
#
#   a sheet inside a *manual* is referred to by the prose around it, and the
#   reader is mid-document when they reach it — that page earns its scan.
#
#   a page of a document that is *nothing but* schematics does not. The whole
#   document is the drawing, "see the original" already hands over exactly the
#   right thing, and inlining those 496 pages would add 135 MB to the deploy
#   to duplicate a link that already works. They still stop rendering as
#   prose, which is the actual complaint; they just link out for the image.
WHOLE_DOC = "the catalogue lists this document as a schematic and the page "\
            "reads as drawing noise"


def measure(page):
    """(tokens, long-word rate, symbol density) for one page's rendered text."""
    text = " ".join(b.get("t", "") for b in page.get("blocks", [])
                    if isinstance(b.get("t"), str))
    toks = [t.lower() for t in TOKEN.findall(text)]
    if not toks or not text:
        return 0, 0.0, 0.0
    return (len(toks),
            sum(len(t) >= 5 for t in toks) / len(toks),
            len(SYMBOL.findall(text)) / len(text))


def classify(doc, whole_doc_is_drawing=False):
    """-> ({page: reason} for drawings, [pages] that read as noise).

    `whole_doc_is_drawing` comes from the catalogue: the document is a
    schematic package or a wiring diagram, not a manual. Those carry no
    outline at all — there is no typeset text to recover headings from — so
    the per-page heading test can never fire on them, and they were the worst
    pages on the site precisely because nothing could reach them. For those,
    the catalogue entry is the corroborating source that the outline heading
    is elsewhere, and any page reading as drawing noise is a drawing.
    """
    strict = {o["p"] for o in doc.get("outline", [])
              if STRICT.search(o.get("t", ""))}
    loose = {o["p"] for o in doc.get("outline", [])
             if LOOSE.search(o.get("t", ""))}
    draw, noise = {}, []
    for p in doc.get("pages", []):
        n, long_rate, sym = measure(p)
        thin = n < MIN_TOKENS
        # Below MIN_TOKENS the prose test is not just weak, it inverts: a page
        # whose entire text is the heading "POWER SUPPLY SCHEMATIC 1 of 1"
        # scores 0.75 on long words and looks like the most prose-like page in
        # the corpus. So a thin page is never judged by its text at all.
        drawish = thin or long_rate < LONG_RATE

        if p["n"] in strict and drawish:
            draw[p["n"]] = "the outline names it a drawing"
            continue
        # A loose heading is corroborated, never taken alone. On a thin page
        # there is no text to corroborate it with, so it stays out.
        if p["n"] in loose and not thin and sym >= SYMBOL_CORROBORATE and drawish:
            draw[p["n"]] = "the outline calls it a board or diagram and its "\
                           "text reads as drawing noise"
            continue
        if thin:
            continue                      # reader already handles thin pages
        if sym >= SYMBOL_RATE and drawish:
            if whole_doc_is_drawing:
                draw[p["n"]] = WHOLE_DOC
            else:
                noise.append(p["n"])
    return draw, noise


def page_size(fid, n):
    """[width, height] of a page's cached scan, or None if it is not there."""
    src = os.path.join(ROOT, f"cache/pages/{fid}/p{n:04d}.webp")
    if not os.path.exists(src):
        return None
    try:
        from PIL import Image
        with Image.open(src) as im:
            return list(im.size)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true",
                    help="also copy the page scans for drawing pages into "
                         "web/pages/, which is what makes them show up")
    a = ap.parse_args()

    # The catalogue's own view of what each document is.
    cat = {d["id"]: d for d in
           json.load(open(os.path.join(ROOT, "data/index/docs.json")))}

    out, n_draw, n_noise, n_img, img_bytes = {}, 0, 0, 0, 0
    web_pages = os.path.join(ROOT, "web", "pages")
    if a.images and os.path.isdir(web_pages):
        shutil.rmtree(web_pages)

    for path in sorted(glob.glob(os.path.join(ROOT, "cache/text/*.json"))):
        fid = os.path.basename(path)[:-5]
        try:
            doc = json.load(open(path))
        except Exception:
            continue
        meta = cat.get(fid, {})
        kind = (meta.get("type") or "").lower()
        is_drawing_doc = bool(meta.get("schematic")) or any(
            w in kind for w in ("schematic", "drawing", "wiring"))
        draw, noise = classify(doc, is_drawing_doc)
        if not draw and not noise:
            continue
        rec = {}
        if draw:
            # The scan's pixel size travels with the flag so the reader can
            # reserve the right box before the image arrives. Without it the
            # img collapses to nothing, a lazy image that occupies no space
            # never intersects the viewport, and so it never loads at all —
            # the schematic silently stays missing, which is the bug this
            # whole file exists to fix.
            rec["draw"] = sorted(draw)
            # Only the pages whose scan is published carry a size, because the
            # size exists to reserve the image's box and there is no image for
            # the rest. The reader falls back to caption-and-link for those.
            shown = [n for n, why in sorted(draw.items()) if why != WHOLE_DOC]
            rec["size"] = {str(n): sz for n in shown if (sz := page_size(fid, n))}
        if noise:
            rec["noise"] = sorted(noise)
        out[fid] = rec
        n_draw += len(draw)
        n_noise += len(noise)

        if not a.images:
            continue
        for n in shown if draw else []:
            src = os.path.join(ROOT, f"cache/pages/{fid}/p{n:04d}.webp")
            if not os.path.exists(src):
                continue
            dst = os.path.join(web_pages, fid, f"p{n:04d}.webp")
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)
            n_img += 1
            img_bytes += os.path.getsize(dst)

    dst = os.path.join(ROOT, "data", "drawings.json")
    json.dump(out, open(dst, "w"), indent=0, sort_keys=True)
    n_linked = n_draw - sum(len(v.get("size", {})) for v in out.values())
    print(f"{n_draw} drawing pages across "
          f"{sum(1 for v in out if 'draw' in out[v])} documents "
          f"({n_draw - n_linked} shown as scans, {n_linked} linked out — "
          f"pages of documents that are nothing but schematics)")
    print(f"{n_noise} further pages read as coming off a drawing but keep their "
          f"text — they may be parts lists")
    print(f"wrote {dst}")
    if a.images:
        print(f"copied {n_img} page scans, {img_bytes/1e6:.0f} MB -> web/pages/")


if __name__ == "__main__":
    main()
