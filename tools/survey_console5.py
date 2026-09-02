#!/usr/bin/env python3
"""Catalogue the Console5 Tech Wiki, and cross-reference its IC pages to our boards.

Outputs: data/sources/console5.json

This deliberately records **pointers, not content**. Console5's robots.txt
carries an express reservation — `ai-train=no`, `use=reference`, and ClaudeBot
disallowed outright — and the wiki exists to support the Console5 store: every
capacitor list on it sits next to a "Purchase these parts as a kit" link.
Copying those lists would take the shop's catalogue and drop its commerce. So
the survey stores titles, sizes, categories and URLs, and leaves the text where
it is. If any of it is ever worth carrying, that is a conversation to have with
Console5, not a scrape.

The one thing worth wiring up regardless is the IC cross-reference. Console5
has 446 pages that are each a one-line function description plus an ASCII
pinout, keyed by part number — including Sega/Atari customs that have no
datasheet anywhere else. Our hand-built boards in data/chips/ know which part
sits at which designator but nothing about what the part *does*. Matching the
two turns "A5 is a 74LS163A" into "A5 is a 74LS163A, a synchronous 4-bit
counter, pinout here" without carrying a byte of their text.

Matching normalises away vendor prefixes (SN/DM/MC) and family letters
(LS/S/HC/ALS), because a 74LS157 and a 74157 are the same pinout — which is the
only claim the cross-reference makes.

`--offline` recomputes the cross-reference from the catalogue already in
data/sources/console5.json without contacting the wiki at all. That is the
common case: our boards gain entries weekly, the wiki's IC pages do not. It is
also the fallback when the site declines to answer — Cloudflare fronts it and
has returned 403 to this script before. Do not work around that; run offline.
"""
import json, os, re, sys, time, glob, collections, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "data", "sources", "console5.json")
API  = "https://wiki.console5.com/tw/api.php"
PAGE = "https://wiki.console5.com/wiki/"
UA   = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
       "(KHTML, like Gecko) Chrome/126 Safari/537.36"
DELAY = 0.8


def query(**kw):
    kw.setdefault("action", "query"); kw.setdefault("format", "json")
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(kw),
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def paged(**kw):
    """Walk MediaWiki's continuation, yielding each response."""
    cont = {}
    while True:
        r = query(**kw, **cont)
        yield r
        if "continue" not in r:
            return
        cont = r["continue"]
        time.sleep(DELAY)


def catalogue():
    pages = {}
    for r in paged(generator="allpages", gaplimit=100, gapnamespace=0,
                   prop="info|categories", cllimit="max"):
        for p in r.get("query", {}).get("pages", {}).values():
            e = pages.setdefault(p["title"], {
                "title": p["title"],
                "url": PAGE + urllib.parse.quote(p["title"].replace(" ", "_")),
                "bytes": p.get("length"), "touched": p.get("touched"), "cats": []})
            e["cats"] += [c["title"].removeprefix("Category:")
                          for c in p.get("categories", [])]
    for e in pages.values():
        e["cats"] = sorted(set(e["cats"]))
    return sorted(pages.values(), key=lambda e: e["title"])


def normalise(part):
    """74LS157, SN74157N and 74157 are one pinout; Sega customs are left alone."""
    p = part.upper().strip()
    p = re.sub(r"^(SN|DM|MC|M|N|F|HD)(74)", r"\2", p)
    p = re.sub(r"^74(LS|S|ALS|HC|HCT|F|C)", "74", p)
    if re.fullmatch(r"74\d+[A-Z]", p):      # trailing speed grade: 74163A
        p = p[:-1]
    return p


def our_parts():
    """Every IC placement on the hand-built boards, by part number."""
    placements = collections.Counter()
    boards = collections.defaultdict(set)
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "chips", "*.json"))):
        board = os.path.basename(path)[:-5]
        for rec in json.load(open(path)).values():
            part = (rec.get("part") or "").strip()
            if part:
                placements[part] += 1
                boards[part].add(board)
    return placements, boards


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    offline = "--offline" in sys.argv

    if offline:
        prev = json.load(open(OUT))
        stats = {k: prev["totals"][k] for k in ("images", "edits")}
        pages = prev["pages"]
        print(f"offline: {len(pages)} pages from the stored catalogue")
    else:
        stats = query(meta="siteinfo", siprop="statistics")["query"]["statistics"]
        pages = catalogue()
        print(f"{len(pages)} main-namespace pages, {stats['images']} images")

    by_cat = collections.Counter(c for p in pages for c in (p["cats"] or ["(none)"]))
    ic_index = {normalise(p["title"]): p for p in pages if "IC" in p["cats"]}

    placements, boards = our_parts()
    crossref = []
    for part, n in placements.most_common():
        hit = ic_index.get(normalise(part))
        if hit:
            crossref.append({"part": part, "placements": n,
                             "boards": sorted(boards[part]),
                             "console5": hit["title"], "url": hit["url"]})
    covered = sum(c["placements"] for c in crossref)
    print(f"{len(crossref)} of {len(placements)} distinct parts matched; "
          f"{covered} of {sum(placements.values())} placements covered")

    json.dump({
        "source": {
            "id": "console5", "name": "Console5 Tech Wiki", "url": PAGE,
            "surveyed": time.strftime("%Y-%m-%d"),
            "kind": "origin",
            "rights": "robots.txt carries Content-Signal ai-train=no, use=reference, "
                      "and disallows ClaudeBot. The wiki is support material for the "
                      "Console5 store — cap lists sit beside 'buy this as a kit' links. "
                      "This file records pointers only; nothing is re-hosted.",
            "note": "Upstream of the capacitor lists GamingDoc republishes. Link to "
                    "these pages, do not copy them.",
        },
        "totals": {
            "pages": len(pages), "images": stats["images"], "edits": stats["edits"],
            "wikitextBytes": sum(p["bytes"] or 0 for p in pages),
            "categories": len(by_cat),
            "icPages": sum(1 for p in pages if "IC" in p["cats"]),
            "matchedParts": len(crossref),
            "distinctParts": len(placements),
            "coveredPlacements": covered,
            "totalPlacements": sum(placements.values()),
        },
        "categories": [{"name": k, "pages": v} for k, v in by_cat.most_common()],
        "icCrossref": crossref,
        "pages": pages,
    }, open(OUT, "w"), indent=1)
    print("wrote", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
