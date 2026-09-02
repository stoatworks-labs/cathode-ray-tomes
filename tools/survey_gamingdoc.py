#!/usr/bin/env python3
"""Catalogue what gamingdoc.org holds, and measure how much of it is already text.

Outputs: data/sources/gamingdoc.json

Unlike the ArcadeRTFM corpus — where every page of every document is a flat
raster scan — GamingDoc is mixed. Roughly half its pages are native vector with
a real text layer, which means most of `ingest.py` (rasterise, tesseract,
geometric heading recovery) is the wrong pipeline for them. So the survey does
not just list documents: it downloads each PDF and measures it, and assigns an
`ingest` class that says which path a document would actually take.

  vector  native vector + text layer  -> extract text and SVG directly
  text    raster pages, text layer already applied upstream -> rasterise only
  ocr     no text layer at all -> the existing ingest.py path

`partRows` counts the Sony-style electrical-parts-list rows a naive regex can
lift from the text layer. It is a floor, not a ceiling: it only matches rows
that carry a Sony part number, so a manual scoring zero may still have parts.

The PDFs are cached under cache/gamingdoc/ and the crawl is deliberately
serial with a delay — this is a small non-profit archive with a download
limiter, not a CDN.
"""
import json, os, re, html, time, subprocess, hashlib, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "gamingdoc")
OUT   = os.path.join(ROOT, "data", "sources", "gamingdoc.json")
BASE  = "https://gamingdoc.org/"
UA    = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
        "(KHTML, like Gecko) Chrome/126 Safari/537.36"
DELAY = 1.5

# Directory slug -> the name the machine actually goes by.
SYSTEMS = {
    "sony-playstation": "PlayStation", "sony-playstation-2": "PlayStation 2",
    "sony-playstation-3": "PlayStation 3", "sony-playstation-portable": "PSP",
    "sega-saturn": "Saturn", "sega-dreamcast": "Dreamcast",
    "sega-megadrive": "Mega Drive", "sega-32x": "32X",
    "atari-2600": "Atari 2600", "atari-5200": "Atari 5200",
    "super-nintendo": "Super Nintendo", "nintendo-64": "Nintendo 64",
    "nintendo-entertainment-system": "NES",
    "nintendo-game-boy-color": "Game Boy Color",
    "snk-neogeo-mvs": "Neo Geo MVS", "microsoft-x-box": "Xbox",
    "amiga-cd32": "Amiga CD32",
}

# Documents that land on a machine slug Cathode Ray Tomes already carries.
# Only the arcade hardware does; a console is not a MAME machine.
MACHINE_MAP = {"snk-neogeo-mvs": ["ng_mv2f", "ng_mv4f"]}

# Sony electrical parts list row: designator, part number, description, package.
PART_ROW = re.compile(
    r"\b([A-Z]{1,3}\d{2,4})\s+(\d-\d{3}-\d{3}-\d{2})\s+"
    r"([A-Z][^()]{2,45}?)(?:\s+\((\d{4})\))?(?=\s{2,}|$)")


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def sitemap_paths():
    """Every page URL, from WordPress's own sitemap rather than by crawling links."""
    xml = get(BASE + "wp-sitemap-posts-page-1.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    return [u.replace(BASE, "").rstrip("/") for u in locs]


def scan_page(path):
    """Return (title, [pdf urls], capacitor rows) for one page."""
    s = get(BASE + path + "/")
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)
    title = re.search(r"(?is)<title>(.*?)</title>", s)
    title = html.unescape(title.group(1)).replace(" – GamingDoc", "").strip() if title else ""
    pdfs = sorted(set(re.findall(
        r"https://gamingdoc\.org/wp-content/uploads/[^\"'\s<>&]+\.pdf", s)))

    caps = []
    table = re.search(r"(?is)<table.*?</table>", s)
    if table:
        for tr in re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", table.group(0)):
            cells = [strip_tags(c) for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)]
            if cells and re.fullmatch(r"[A-Z]{1,3}\d+", cells[0] or ""):
                caps.append({"ref": cells[0],
                             "value": cells[1] if len(cells) > 1 else "",
                             "voltage": cells[2] if len(cells) > 2 else ""})
    return title, pdfs, caps


def sh(*args):
    return subprocess.run(args, capture_output=True).stdout.decode("utf-8", "replace")


def probe(pdf):
    """Measure text layer and vector content — the thing that picks the pipeline."""
    info = sh("pdfinfo", pdf)
    m = re.search(r"Pages:\s+(\d+)", info)
    pages = int(m.group(1)) if m else 0
    raster = {int(p[0]) for l in sh("pdfimages", "-list", pdf).splitlines()[2:]
              for p in [l.split()] if p and p[0].isdigit()}
    text = sh("pdftotext", "-layout", pdf, "-")
    per_page = text.split("\f")[:pages]
    words = sum(len(t.split()) for t in per_page)
    producer = re.search(r"Producer:\s+(.*)", info)

    if words == 0:                       ingest = "ocr"
    elif pages - len(raster) >= pages * 0.6: ingest = "vector"
    else:                                ingest = "text"

    return {"pages": pages, "vectorPages": pages - len(raster),
            "textPages": sum(1 for t in per_page if len(t.split()) > 20),
            "words": words, "ingest": ingest,
            "producer": (producer.group(1).strip() if producer else ""),
            "partRows": len(PART_ROW.findall(text))}


def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    paths = sitemap_paths()
    print(f"{len(paths)} pages in the sitemap")

    docs, boards, seen = {}, [], set()
    for i, path in enumerate(paths, 1):
        if not path:
            continue
        try:
            title, pdfs, caps = scan_page(path)
        except Exception as e:
            print(f"  ! {path}: {e}"); time.sleep(DELAY); continue
        parts = path.split("/")
        slug = next((p for p in parts if p in SYSTEMS), None)

        # Count the recap rows but do not copy them: every one of these tables is
        # credited "Source: Console5", and Console5 has reserved its rights. The
        # count is what the decision needs; the values stay on their page.
        if caps:
            boards.append({"system": SYSTEMS.get(slug, slug), "systemSlug": slug,
                           "revision": parts[-1], "page": BASE + path + "/",
                           "capRows": len(caps), "upstream": "console5"})
        for url in pdfs:
            if url in seen:
                docs[url]["pages_on"].append(BASE + path + "/"); continue
            seen.add(url)
            docs[url] = {"id": hashlib.sha1(url.encode()).hexdigest()[:12],
                         "url": url, "pages_on": [BASE + path + "/"],
                         "title": title, "section": parts[0],
                         "family": parts[1] if len(parts) > 1 else "",
                         "system": SYSTEMS.get(slug, slug), "systemSlug": slug}
        if i % 40 == 0:
            print(f"  {i}/{len(paths)} pages, {len(docs)} documents")
        time.sleep(DELAY)

    print(f"{len(docs)} documents, {len(boards)} board revisions with cap lists")

    for d in docs.values():
        dest = os.path.join(CACHE, d["id"] + ".pdf")
        if not os.path.exists(dest) or os.path.getsize(dest) < 1000:
            try:
                blob = get(d["url"], binary=True)
            except Exception as e:
                print(f"  ! {d['url']}: {e}"); continue
            if blob[:4] != b"%PDF":
                print(f"  ! not a PDF (rate limited?): {d['url']}"); continue
            open(dest, "wb").write(blob)
            time.sleep(DELAY)
        d["bytes"] = os.path.getsize(dest)
        d.update(probe(dest))
        if d["systemSlug"] in MACHINE_MAP:
            d["machines"] = MACHINE_MAP[d["systemSlug"]]
        print(f"  {d['ingest']:6s} {d['pages']:4d}p {d['words']:7d}w  {d['title'][:52]}")

    out = sorted(docs.values(), key=lambda d: (d["system"] or "", d["title"]))
    for d in out:
        d["pageUrls"] = d.pop("pages_on")

    json.dump({
        "source": {
            "id": "gamingdoc", "name": "GamingDoc", "url": BASE,
            "surveyed": time.strftime("%Y-%m-%d"),
            "kind": "mirror",
            "rights": "Re-hosts third-party manuals; states no licence and invites "
                      "takedown requests. Same footing as ArcadeRTFM, but Sony service "
                      "manuals are defended harder than 1980s Atari drawings.",
            "note": "Every board capacitor list here is credited 'Source: Console5'. "
                    "GamingDoc is the mirror; see data/sources/console5.json.",
        },
        "totals": {
            "documents": len(out),
            "pages": sum(d.get("pages", 0) for d in out),
            "vectorPages": sum(d.get("vectorPages", 0) for d in out),
            "words": sum(d.get("words", 0) for d in out),
            "bytes": sum(d.get("bytes", 0) for d in out),
            "partRows": sum(d.get("partRows", 0) for d in out),
            "boardRevisions": len(boards),
            "capacitorRows": sum(b["capRows"] for b in boards),
        },
        "documents": out,
        "boards": sorted(boards, key=lambda b: (b["system"] or "", b["revision"])),
    }, open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
