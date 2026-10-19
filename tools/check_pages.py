#!/usr/bin/env python3
"""Read every published page the way the reader does, and report the bad ones.

The pipeline has checks for whether a document *ingested*. This one asks the
question after that: given what shipped, is there a page a reader would open
and find unusable? Everything here is a defect that survived ingestion, was
recorded in the output, and went live anyway.

That is not hypothetical. The SCPH-70000's electrical parts list shipped as
five thousand words of `U U U U U ... C1692 C1693` for as long as the document
had been on the site. The ingest knew — it wrote `undecoded: 0.0364` into the
document's own metadata and printed a warning — and the warning scrolled past.
A page-level check is the thing that would have caught it, so here it is.

    python3 tools/check_pages.py              # summary, exit 1 if anything fires
    python3 tools/check_pages.py --detail     # every hit, with a sample
    python3 tools/check_pages.py --json       # for a diff between runs

Checks, and why each is a real failure rather than a smell:

  undecoded     Characters the extractor could not read reaching the page.
                A handful is a symbol font with no ToUnicode and is honest; a
                percent of the page is a broken CMap and is a wall.
  prose-is-noise  A page rendered as paragraphs that scores as drawing debris
                on build_drawings.py's own measures. Either the classifier
                missed it or the document lies about itself; either way a
                reader gets fluent nonsense.
  missing-scan  A page carrying dw/dh, so the reader reserves a box and emits
                an <img>, with no file behind it. This one is invisible in
                testing: a missing sheet looks exactly like one still loading.
  orphan-scan   The reverse, and the one that caught this file's own author:
                a scan published under web/pages/ that no page points at,
                because the extraction that copied it ran without the image
                pass that sets dw/dh. The file ships and is never shown.
  empty-block   A block whose text is blank, which renders as an empty <p>.
                Only counted where the reader sets blocks as prose — a drawing
                page shows its scan and an empty block there is inert.
  one-cell-row  A `tr` the reader cannot split into cells, so a table draws as
                a single-column strip.
  control-char  A character that should never have survived extraction.

And for the PCB layouts read from MAME's driver notes (web/data/layout/):

  layout-licence    A layout from a file under anything but BSD-3-Clause or CC0.
                    The extractor skips GPL and LGPL drivers; this is what makes
                    sure none slipped through to the deploy.
  layout-provenance A layout without its commit, tag, lines or copyright holders,
                    which the page needs to credit it as the licence asks.
  layout-misplaced  A device whose recorded position does not land on its own
                    label in the published art: the page would light up the
                    wrong word, and say so confidently.
  layout-index      The index and the shards disagree, so a list row leads to a
                    404 or a layout is published that nothing lists.
"""
import argparse, glob, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "web", "data", "doc")
PAGES = os.path.join(ROOT, "web", "pages")

# build_drawings.py's measures, so a page that fires here fires for a reason
# that file already argues for at length rather than one invented in this one.
TOKEN = re.compile(r"[A-Za-z]{2,}")
SYMBOL = re.compile(r"[^A-Za-z0-9\s.,;:()\-/+%'\"&#*=\[\]]")
MIN_TOKENS, LONG_RATE, SYMBOL_RATE = 40, 0.20, 0.030
# Those measures are calibrated on English, and a kanji is in none of their
# character classes — SYMBOL counts every one as debris, so a correctly-read
# Japanese page scores like a schematic. build_drawings.py exempts these pages
# and so must this, or the check reports the 43 Japanese manuals as broken for
# being legible. Same constants, same reason.
CJK = re.compile("[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]")
CJK_MIN, CJK_SHARE = 60, 0.10


def is_cjk_text(text):
    hits = len(CJK.findall(text))
    return hits >= CJK_MIN and text and hits / len(text) >= CJK_SHARE

# A page fires only when it is unreadable by both measures. A symbol font the
# extractor could not map — a µ, an Ω — leaves a dozen U+FFFD on a short page,
# which reads as 2% and is honest; the SCPH-70000's broken CMap left 991 on one
# page. The count is what separates them, so both bars have to be cleared.
UNDECODED_PAGE = 0.01
UNDECODED_MIN = 25

CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def page_text(page):
    return " ".join(b.get("t", "") for b in page.get("blocks", [])
                    if isinstance(b.get("t"), str))


def measure(text):
    toks = [t.lower() for t in TOKEN.findall(text)]
    if not toks or not text:
        return 0, 0.0, 0.0
    return (len(toks),
            sum(len(t) >= 5 for t in toks) / len(toks),
            len(SYMBOL.findall(text)) / len(text))


def render_mode(page):
    """Which branch of the reader's renderBlocks this page takes."""
    if page.get("draw"):
        return "drawing"
    if page.get("noise"):
        return "noise-collapsed"
    if page.get("dw") and page.get("dh"):
        return "scan+prose"
    return "prose"


def scan_index():
    out = {}
    if not os.path.isdir(PAGES):
        return out
    for did in os.listdir(PAGES):
        d = os.path.join(PAGES, did)
        if os.path.isdir(d):
            out[did] = set(os.listdir(d))
    return out


def check():
    cat = {}
    cpath = os.path.join(ROOT, "web", "data", "docs.json")
    if os.path.exists(cpath):
        cat = {d["id"]: d for d in json.load(open(cpath))}
    scans = scan_index()
    found = defaultdict(list)
    stats = Counter()
    shown = {}          # doc -> the scans some page actually points at

    for path in sorted(glob.glob(os.path.join(DOCS, "*.json"))):
        did = os.path.basename(path)[:-5]
        doc = json.load(open(path))
        meta = cat.get(did, {})
        where = dict(doc=did, machine=meta.get("machineName") or meta.get("machine"),
                     title=meta.get("title"))
        stats["docs"] += 1

        for p in doc.get("pages", []):
            stats["pages"] += 1
            mode = render_mode(p)
            stats["mode:" + mode] += 1
            text = page_text(p)
            n, long_rate, sym = measure(text)

            bad = text.count("�")
            if bad >= UNDECODED_MIN and bad / max(len(text), 1) >= UNDECODED_PAGE:
                found["undecoded"].append(
                    dict(where, page=p["n"], mode=mode, count=bad,
                         rate=round(bad / max(len(text), 1), 4),
                         sample=text[:120]))

            if (mode == "prose" and n >= MIN_TOKENS
                    and long_rate < LONG_RATE and sym >= SYMBOL_RATE
                    and not is_cjk_text(text)):
                found["prose-is-noise"].append(
                    dict(where, page=p["n"], tokens=n,
                         long=round(long_rate, 3), sym=round(sym, 3),
                         sample=text[:120]))

            name = "p%04d.webp" % p["n"]
            has_file = name in scans.get(did, ())
            if p.get("dw") and p.get("dh"):
                if not has_file:
                    found["missing-scan"].append(
                        dict(where, page=p["n"], file=name))
                shown.setdefault(did, set()).add(name)

            if CONTROL.search(text):
                found["control-char"].append(
                    dict(where, page=p["n"], mode=mode,
                         chars=sorted({hex(ord(c)) for c in CONTROL.findall(text)})))

            for b in p.get("blocks", []):
                t = b.get("t")
                if not isinstance(t, str):
                    continue
                if not t.strip() and mode in ("prose", "scan+prose"):
                    found["empty-block"].append(
                        dict(where, page=p["n"], mode=mode, kind=b.get("k")))
                if b.get("k") == "tr" and not re.search(r"\s{3,}", t):
                    found["one-cell-row"].append(
                        dict(where, page=p["n"], mode=mode, text=t[:100]))

    # A scan nothing points at ships and is never shown. It happens when an
    # extraction copies the images but runs without the pass that sets dw/dh,
    # and it leaves no trace in the reader — the page simply renders as text.
    for did, files in scans.items():
        orphans = sorted(files - shown.get(did, set()))
        if orphans:
            meta = cat.get(did, {})
            found["orphan-scan"].append(
                dict(doc=did, machine=meta.get("machineName") or meta.get("machine"),
                     title=meta.get("title"), count=len(orphans),
                     files=orphans[:4]))

    check_layouts(stats, found)
    return stats, found


def check_layouts(stats, found):
    lay_dir = os.path.join(ROOT, "web", "data", "layout")
    ipath = os.path.join(ROOT, "web", "data", "layouts.json")
    if not os.path.isdir(lay_dir):
        return
    listed = {r["id"] for r in json.load(open(ipath))} if os.path.exists(ipath) else set()
    shipped = set()
    for path in sorted(glob.glob(os.path.join(lay_dir, "*.json"))):
        for src, lays in json.load(open(path)).items():
            for l in lays:
                stats["layouts"] += 1
                stats["layout-devices"] += len(l["devices"])
                shipped.add(l["id"])
                where = dict(doc=l["id"], machine=src, title=" · ".join(l.get("caption") or []))
                if l.get("licence") not in ("BSD-3-Clause", "CC0-1.0"):
                    found["layout-licence"].append(dict(where, licence=l.get("licence")))
                if not (re.match(r"^[0-9a-f]{40}$", l.get("commit") or "") and l.get("tag")
                        and l.get("copyright") and l.get("line") and l.get("end")):
                    found["layout-provenance"].append(where)
                for d in l["devices"]:
                    r, c0, c1 = d["at"][:3]
                    if len(d["at"]) > 3:
                        got = "".join((l["art"][k][c0:c0 + 1] if k < len(l["art"]) else "")
                                      for k in range(r, d["at"][3] + 1))
                    else:
                        got = l["art"][r][c0:c1] if r < len(l["art"]) else ""
                    if got != d["label"] or not (l["line"] <= d["line"] <= l["end"]):
                        found["layout-misplaced"].append(
                            dict(where, label=d["label"], found=got, line=d["line"]))
    for lid in sorted(listed - shipped):
        found["layout-index"].append(dict(doc=lid, machine=None, title="listed, not shipped"))
    for lid in sorted(shipped - listed):
        found["layout-index"].append(dict(doc=lid, machine=None, title="shipped, not listed"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--detail", action="store_true", help="every hit, not a count")
    ap.add_argument("--json", action="store_true", help="the findings, as JSON")
    ap.add_argument("--limit", type=int, default=12, help="hits shown per check")
    a = ap.parse_args()

    stats, found = check()
    if a.json:
        json.dump({k: v for k, v in found.items()}, sys.stdout, indent=1)
        return 1 if found else 0

    print(f"{stats['docs']:,} documents · {stats['pages']:,} pages")
    for mode in ("prose", "drawing", "scan+prose", "noise-collapsed"):
        if stats.get("mode:" + mode):
            print(f"  {stats['mode:' + mode]:>7,}  {mode}")
    if stats.get("layouts"):
        print(f"{stats['layouts']:,} PCB layouts · {stats['layout-devices']:,} devices")
    print()
    if not found:
        print("no pages a reader would find unusable")
        return 0

    for kind in sorted(found):
        hits = found[kind]
        docs = len({h["doc"] for h in hits})
        print(f"{kind}: {len(hits)} page(s) across {docs} document(s)")
        for h in hits[: (len(hits) if a.detail else a.limit)]:
            bits = " ".join(f"{k}={v}" for k, v in h.items()
                            if k not in ("doc", "title", "machine", "sample"))
            print(f"   {h['doc']} {bits}")
            print(f"     {h.get('machine')} · {h.get('title')}")
            if h.get("sample"):
                print(f"     {h['sample']!r}")
        if not a.detail and len(hits) > a.limit:
            print(f"   … {len(hits) - a.limit} more (--detail)")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
