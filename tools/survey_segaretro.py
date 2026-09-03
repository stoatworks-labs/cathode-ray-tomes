#!/usr/bin/env python3
"""Measure Sega Retro's PDF holdings through its API. Pointers, not content.

Outputs: data/sources/segaretro.json

    python3 tools/survey_segaretro.py

Sega Retro's robots.txt carries the same express reservation Console5's does
(`Content-Signal: search=yes, ai-train=no, use=reference`, an Article 4
reservation under the EU copyright directive). So, as with Console5, this
records what the wiki holds and where — names, sizes, URLs — and leaves every
document where it is. If any of it is ever worth carrying, that is a
conversation with Sega Retro, not a fetch.

It is worth knowing the shape of anyway, because it is the one archive with
Sega's own system-level service documentation: NAOMI, Atomiswave, Lindbergh,
the G80 and System boards, and the console service manuals. Measured, that is
a few dozen files among twelve thousand, most of which are game instruction
manuals and flyers — recorded as counts here, not listed.

A dozen paginated API calls, no page content.
"""
import collections, json, os, re, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "sources", "segaretro.json")
API = "https://segaretro.org/api.php"
UA = "cathode-ray-tomes-survey/0.1 (+https://cathode-ray-tomes.com)"
DELAY = 0.5

# What a filename says the document is. First match wins.
KINDS = [
    ("service", re.compile(r"service|schematic|servicem|repair|parts", re.I)),
    ("arcade",  re.compile(r"arcade|naomi|atomiswave|lindbergh|chihiro|st-?v|model[123]|"
                           r"system\s?(16|18|24|32|c|e|32x)|g80|hikaru|ringedge|triforce|"
                           r"europa|nu\b|alls", re.I)),
    ("flyer",   re.compile(r"flyer|leaflet|brochure|catalog|advert|press", re.I)),
    ("manual",  re.compile(r"manual", re.I)),
]


def api(**q):
    q["format"] = "json"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def kind_of(name):
    for k, rx in KINDS:
        if rx.search(name):
            return k
    return "other"


def main():
    files, cont = [], {}
    while True:
        d = api(action="query", list="allimages", aimime="application/pdf",
                ailimit=500, aiprop="size|timestamp|url", **cont)
        files += d["query"]["allimages"]
        cont = d.get("continue", {})
        if not cont:
            break
        time.sleep(DELAY)

    kinds = collections.Counter(kind_of(f["name"]) for f in files)
    listed = [{"name": f["name"], "bytes": f["size"], "url": f["url"],
               "uploaded": f["timestamp"][:10], "kind": kind_of(f["name"])}
              for f in files if kind_of(f["name"]) in ("service", "arcade")]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "source": {
            "name": "Sega Retro", "url": "https://segaretro.org/",
            "surveyed": time.strftime("%Y-%m-%d"),
            "rights": "robots.txt: Content-Signal search=yes, ai-train=no, use=reference — "
                      "an express reservation. Pointers only; nothing taken.",
        },
        "totals": {
            "pdfs": len(files),
            "pdfBytes": sum(f["size"] for f in files),
            "byKind": dict(kinds),
            "listed": len(listed),
        },
        "pdfs": sorted(listed, key=lambda f: f["name"].lower()),
    }, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"{len(files):,} PDFs, {sum(f['size'] for f in files)/1e9:.0f} GB; by kind "
          + ", ".join(f"{k} {n:,}" for k, n in kinds.most_common()))
    print(f"listed the {len(listed)} service and arcade-system files; wrote {OUT}")


if __name__ == "__main__":
    main()
