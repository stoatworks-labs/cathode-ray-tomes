#!/usr/bin/env python3
"""Read the Internet Archive's OCR of our own scans against ours.

The `arcademanuals` collection holds 2,065 of this corpus's documents under the
same filenames, and archive.org runs its own OCR over every upload and
publishes the result beside the scan. That is a second, independent reading of
the *same page images* — the one thing this pipeline has never had. It cannot
say what a page really says, but where two independent readings disagree
sharply one of them is wrong, and where theirs recovers far more words than
ours the page is worth looking at.

This is a measurement, not an import. Nothing archive.org produced is
published: their text is read, compared, and thrown away, and what survives is
a ranked list of our own pages in `data/ocr-quality.json`.

    python3 tools/compare_ocr.py --fetch        # download the text (cached)
    python3 tools/compare_ocr.py                # compare what is cached
    python3 tools/compare_ocr.py --report       # print the ranking

Two things the data turned out to be, measured over all 2,057 documents:

  - `_djvu.txt` carries no page breaks. Not one of the 2,057 has a form feed
    in it, so the comparison is whole-document, and the 347 "aligned" cases
    are simply the single-page documents. Page-level comparison would need
    `_djvu.xml` (1.1 GB across the corpus), and the whole-document result
    below does not justify fetching it.
  - archive.org's OCR ran a multilingual model, and on an English scan it
    invents other scripts: Sente's SAC 1B manual comes back with 6,990
    Cyrillic and Arabic characters, its first line reading `Жү чы PAPIAS. B a
    пили aaa ap тен чад`. That inflates its word count with debris that
    happens to contain English function words, and it is what every one of
    the first pass's 23 "documents archive.org read better" turned out to be.
    A reading that is substantially foreign script is not a better reading of
    an English page and is discounted before anything is scored.

The result of the pass that ran on 2026-09-07: no document in the corpus that
archive.org's independent reading recovered and ours did not. On 96% ours holds
as much or more readable English; the remainder is hallucination volume or
debris off drawing sheets we already show as scans. That is the answer to the
question EXTERNAL-SOURCES.md posed — which of our 65,000 pages tesseract read
worst — and the answer is that a second reader found none it read better.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "archive_org")
TEXT = os.path.join(CACHE, "ocr")
SURVEY = os.path.join(ROOT, "data", "sources", "archive_org.json")
OUT = os.path.join(ROOT, "data", "ocr-quality.json")

UA = "cathode-ray-tomes/1.0 (+https://cathode-ray-tomes.com)"
DELAY = 0.5                     # archive.org is a charity, not a CDN
WORD = re.compile(r"[A-Za-z]{3,}")
# Function words. A page of real English has them; a page of OCR debris off a
# drawing does not, whoever did the reading. This is the measure, rather than
# raw word count, because a schematic sheet legitimately returns fragments and
# should not be reported as badly read.
STOP = set("""the a an and or of to in on at for with from by is are was were be
been it its this that these those as if not no but which when where how then
than there their they you your we our will can may must should would shall each
other any all both more most such only same so up out off over under again
into with within without per through during before after above below between""".split())
MIN_WORDS = 40                  # below this a page is not evidence of anything
# Scripts a multilingual model invents on an English scan. A reading with more
# than this share of them is not a reading of the page and is not scored.
FOREIGN = re.compile("[\u0400-\u04ff\u0600-\u06ff\uac00-\ud7af\u0370-\u03ff]")
FOREIGN_SHARE = 0.02
# A whole document has to be read clearly better to fire: this many more
# function words, and this much more as a ratio, so a page of theory-of-
# operation prose on an otherwise identical reading does not report.
DOC_MIN_GAIN = 100
DOC_MIN_RATIO = 1.3


def page_words(text):
    return [w.lower() for w in WORD.findall(text)]


def score(text):
    """(words, function-word share) — how much readable English a page holds."""
    ws = page_words(text)
    if not ws:
        return 0, 0.0
    return len(ws), sum(1 for w in ws if w in STOP) / len(ws)


def their_pages(path):
    """archive.org's OCR. It carries no form feeds, so this is one page."""
    raw = open(path, encoding="utf-8", errors="replace").read()
    return raw.split("\f")


def hallucinated(text):
    """True when a reading is substantially in scripts the page does not use."""
    return bool(text) and len(FOREIGN.findall(text)) / len(text) >= FOREIGN_SHARE


def english_words(text):
    """(function words, words) — a count of readable prose, which debris does
    not produce however much of it there is."""
    ws = page_words(text)
    return sum(1 for w in ws if w in STOP), len(ws)


def our_pages(did):
    p = os.path.join(ROOT, "cache", "text", did + ".json")
    if not os.path.exists(p):
        return None
    doc = json.load(open(p))
    return [" ".join(b.get("t", "") for b in pg.get("blocks", []))
            for pg in doc.get("pages", [])]


def shown_as_drawings(did):
    """Share of a document's pages the reader shows as their scan.

    Those pages' text is never set as prose — the sheet is on the page and the
    OCR sits collapsed beneath it — so a second reader finding more words on
    them changes nothing a reader sees. After the hallucination discount, every
    remaining "read better" document was a schematic or drawing package we
    show that way: theory-of-operation fragments and debris off the sheets.
    """
    p = os.path.join(ROOT, "web", "data", "doc", did + ".json")
    if not os.path.exists(p):
        return 0.0
    pages = json.load(open(p)).get("pages", [])
    if not pages:
        return 0.0
    return sum(1 for pg in pages if pg.get("draw")) / len(pages)


def djvu_name(identifier):
    p = os.path.join(CACHE, "meta", identifier + ".json")
    if not os.path.exists(p):
        return None
    d = json.load(open(p))
    for f in d.get("files") or []:
        if f["name"].endswith("_djvu.txt"):
            return f["name"]
    return None


def fetch(identifier, name):
    dst = os.path.join(TEXT, identifier + ".txt")
    if os.path.exists(dst):
        return dst, False
    url = ("https://archive.org/download/" + urllib.parse.quote(identifier)
           + "/" + urllib.parse.quote(name))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
    except Exception:                            # noqa: BLE001 — skipped, not fatal
        return None, False
    os.makedirs(TEXT, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(body)
    time.sleep(DELAY)
    return dst, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download missing text")
    ap.add_argument("--report", action="store_true", help="print the ranking")
    ap.add_argument("--limit", type=int, help="stop after this many documents")
    a = ap.parse_args()

    mirrors = json.load(open(SURVEY))["mirrors"]
    got = skipped = discounted = 0
    findings = []
    docs = 0

    for i, (did, m) in enumerate(sorted(mirrors.items())):
        if a.limit and docs >= a.limit:
            break
        ident = m["identifier"]
        name = djvu_name(ident)
        if not name:
            continue
        path = os.path.join(TEXT, ident + ".txt")
        if not os.path.exists(path):
            if not a.fetch:
                skipped += 1
                continue
            path, new = fetch(ident, name)
            if not path:
                skipped += 1
                continue
            got += new
            if got and got % 100 == 0:
                print(f"  {got} fetched…", flush=True)
        ours = our_pages(did)
        if ours is None:
            continue
        theirs = their_pages(path)
        docs += 1
        mine = " ".join(ours)
        yours = " ".join(theirs)
        if hallucinated(yours) or shown_as_drawings(did) >= 0.5:
            discounted += 1
            continue
        oe, ow = english_words(mine)
        te, tw = english_words(yours)
        if te - oe >= DOC_MIN_GAIN and te >= oe * DOC_MIN_RATIO and te >= MIN_WORDS:
            findings.append({
                "doc": did, "page": None,
                "ours": {"words": ow, "english": oe},
                "theirs": {"words": tw, "english": te},
                "identifier": ident,
            })

    findings.sort(key=lambda f: -(f["theirs"]["english"] - f["ours"]["english"]))
    json.dump({"checked": time.strftime("%Y-%m-%d"),
               "documents": docs, "discounted": discounted, "findings": findings},
              open(OUT, "w"), indent=1)
    print(f"{docs} documents compared, {got} newly fetched, {skipped} without text, "
          f"{discounted} discounted (hallucinated, or shown as drawings)")
    print(f"{len(findings)} documents archive.org read as English and we did not")
    print(f"-> {os.path.relpath(OUT, ROOT)}")

    if a.report:
        cat = {d["id"]: d for d in json.load(
            open(os.path.join(ROOT, "data", "index", "docs.json")))}
        by_doc = {}
        for f in findings:
            by_doc.setdefault(f["doc"], []).append(f)
        print("\ndocuments archive.org read clearly better:")
        for f in findings[:20]:
            meta = cat.get(f["doc"], {})
            print(f"  +{f['theirs']['english'] - f['ours']['english']:>5} fn-words  "
                  f"{meta.get('type','?')[:16]:18}"
                  f"{meta.get('machineName','?')[:24]:26}{meta.get('title','?')[:36]}")


if __name__ == "__main__":
    main()
