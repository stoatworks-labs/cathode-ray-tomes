#!/usr/bin/env python3
"""Find the documents that are not in English, so they stop being read as if.

`ingest.py` runs tesseract with `-l eng` on everything, and a Japanese manual
read that way comes back as noise:

    eng      yo09964Zd WO Ddivfay SARL 21 BHMGMII CP ZUGH EDEMA SUE SAR AS
    jpn+eng  © CAPCOM CO., LTD. 1996 ALL RIGHTS RESERVED. 取扱説明書 お客様各位

That is Super Puzzle Fighter's first page, and until now 75% of that document
was flagged as drawing noise — correctly, on the evidence, because what came
out was not words. Nothing on the site was wrong about it; everything was
wrong about what the page said.

Two stages, because the cheap test is not decisive on its own:

  filter   the share of a document's prose that is English function words.
           Real English prose is 10-20%; the corpus median is 14%. Below 5%
           the page is either not English or not prose.
  confirm  re-read one page with `-l jpn` and count the CJK characters. A
           parts catalogue is also short of function words and this is what
           tells it apart from a Japanese manual — it comes back with none.

Writes `data/languages.json`, which `ingest.py` reads. Language is a property
of the document, recorded once, rather than a flag someone has to remember.

    python3 tools/detect_language.py            # scan and write
    python3 tools/detect_language.py --dry-run  # report, write nothing
"""
import argparse, glob, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocrlib import ocr_page

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")
OUT = os.path.join(ROOT, "data", "languages.json")

WORD = re.compile(r"[A-Za-z]{2,}")
# Hiragana, katakana, and the CJK ideographs. Any of them in quantity settles it.
CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿]")
STOP = set("""the a an and or of to in on at for with from by is are was were be
been it its this that these those as if not no but which when where how then
than there their they you your we our will can may must should would shall each
other any all both more most such only same so up out off over under again
into within without per through during before after above below between""".split())

ENGLISH_FLOOR = 0.05      # below this a document is not reading as English
MIN_TOKENS = 200          # less than this is not evidence
CJK_CHARS = 40            # in one re-read page, to call it Japanese
CJK_SHARE = 0.05


def prose_pages(doc):
    for pg in doc.get("pages", []):
        if pg.get("draw") or pg.get("noise"):
            continue
        txt = " ".join(b.get("t", "") for b in pg.get("blocks", []))
        if len(txt) >= 400:
            yield pg["n"], txt


def english_share(doc):
    toks = []
    for _n, txt in prose_pages(doc):
        toks += [w.lower() for w in WORD.findall(txt)]
    if len(toks) < MIN_TOKENS:
        return None
    return sum(1 for w in toks if w in STOP) / len(toks)


def confirm_japanese(did, doc):
    """Re-read the document's wordiest prose page with the Japanese model."""
    best = None
    for n, txt in prose_pages(doc):
        if best is None or len(txt) > best[1]:
            best = (n, len(txt))
    if not best:
        return None
    img = os.path.join(CACHE, "pages", did, "p%04d.webp" % best[0])
    if not os.path.exists(img):
        return None
    text, _lines = ocr_page(img, lang="jpn")
    hits = len(CJK.findall(text))
    if hits >= CJK_CHARS and text and hits / len(text) >= CJK_SHARE:
        return best[0], hits, len(text)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    cat = {d["id"]: d for d in json.load(
        open(os.path.join(ROOT, "data", "index", "docs.json")))}
    langs, checked, candidates = {}, 0, 0

    for p in sorted(glob.glob(os.path.join(CACHE, "text", "*.json"))):
        did = os.path.basename(p)[:-5]
        try:
            doc = json.load(open(p))
        except Exception:
            continue
        # A vector document carries its own text and was never OCR'd.
        if doc.get("meta", {}).get("via") == "vector":
            continue
        checked += 1
        share = english_share(doc)
        if share is None or share >= ENGLISH_FLOOR:
            continue
        candidates += 1
        hit = confirm_japanese(did, doc)
        m = cat.get(did, {})
        if hit:
            n, cjk, total = hit
            langs[did] = "jpn+eng"
            print(f"  jpn  {share:5.1%} english · p{n} has {cjk} CJK of {total} chars"
                  f"  {m.get('machineName','?')[:22]:24}{m.get('title','?')[:34]}")
        else:
            print(f"  --   {share:5.1%} english · no CJK found"
                  f"       {m.get('machineName','?')[:22]:24}{m.get('title','?')[:34]}")

    print(f"\n{checked} OCR'd documents · {candidates} read as non-English · "
          f"{len(langs)} confirmed Japanese")
    if a.dry_run:
        print("(dry run; nothing written)")
        return
    json.dump(langs, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"-> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
