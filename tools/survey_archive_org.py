#!/usr/bin/env python3
"""Catalogue the Internet Archive's arcade manual holdings, measured against ours.

Outputs: data/sources/archive_org.json

    python3 tools/survey_archive_org.py              # index the collection (one call)
    python3 tools/survey_archive_org.py --metadata   # per-item file lists; slow, resumable
    python3 tools/survey_archive_org.py --offline    # recompute from the cache only

The `arcademanuals` collection is the largest arcade documentation holding
anywhere: 4,753 items when first surveyed. It turns out to contain most of the
ArcadeRTFM corpus this site is built from — 2,065 of our 2,405 documents are
there under the same filenames, uploaded in three waves (2011, 2017, 2025) by
different people from their own archives — plus roughly 2,700 documents we do
not have. So this survey answers two questions at once:

  mirrors   for each of our documents, the archive.org item that carries the
            same file. That is a second home for a corpus whose source has
            already lost twelve files, and it costs no upload: archive.org
            serves any item's files directly at
            https://archive.org/download/<identifier>/<file>.
  new       every item that is not one of ours, with a best guess at the MAME
            machine it documents, so the next ingest can be sized before it
            is started.

Archive.org also runs its own OCR over every uploaded PDF and publishes the
result beside it (`*_djvu.txt`, `*_text.pdf`). Nothing here reads it — it is
recorded as present or not, because a second independent OCR of the same scan
is exactly the cross-check the pipeline's structure detection lacks.

Rights, as far as they can be read from the metadata: items carry no licence
field. They are uploads by private individuals, described as personal
archives being preserved, of manuals whose copyright stays with their
publishers — the same footing as ArcadeRTFM and GamingDoc, and the footing
this site already stands on. archive.org's robots.txt disallows nothing that
this touches, and its search and metadata APIs are public and documented.

The index is one request. `--metadata` is one request per unmatched item,
serial with a delay, cached under cache/archive_org/ so it resumes.
"""
import argparse, collections, json, os, re, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "archive_org")
OUT = os.path.join(ROOT, "data", "sources", "archive_org.json")
UA = "cathode-ray-tomes-survey/0.1 (+https://cathode-ray-tomes.com)"
COLLECTION = "arcademanuals"
DELAY = 0.5
FIELDS = "identifier,title,subject,creator,publicdate,item_size,files_count,imagecount"

# Tokens that are a document's designation rather than its machine's name:
# Atari's TM/DP/SP/ST codes, printings, part numbers, revisions.
DOC_TOKEN = re.compile(
    r"^(tm|dp|sp|st|ck|sm|pm|om|manual|schematics?|schematic|package|drawing|"
    r"wiring|diagram|parts|list|catalog|operators?|owners?|service|"
    r"instructions?|technical|installation|kit|conversion|bulletin|"
    r"\d+(st|nd|rd|th)|printing|rev|revision|preliminary|supplement|"
    r"[a-z]{0,3}\d{2,}[a-z0-9-]*|ptm)$")


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def scrape(offline):
    """Every item in the collection, from the scrape API (cursor-paginated)."""
    path = os.path.join(CACHE, "scrape.json")
    if offline or os.path.exists(path) and offline is None:
        return json.load(open(path))
    items, cursor = [], None
    while True:
        q = {"q": f"collection:{COLLECTION}", "fields": FIELDS, "count": 10000}
        if cursor:
            q["cursor"] = cursor
        d = get_json("https://archive.org/services/search/v1/scrape?" + urllib.parse.urlencode(q))
        items += d["items"]
        cursor = d.get("cursor")
        if not cursor:
            break
        time.sleep(1)
    os.makedirs(CACHE, exist_ok=True)
    json.dump(items, open(path, "w"))
    return items


def metadata(identifier, fetch):
    """The PDFs an item carries and whether archive.org has OCR'd it."""
    path = os.path.join(CACHE, "meta", identifier + ".json")
    if os.path.exists(path):
        d = json.load(open(path))
    elif not fetch:
        return None
    else:
        try:
            d = get_json("https://archive.org/metadata/" + urllib.parse.quote(identifier))
        except Exception as e:                      # noqa: BLE001 — recorded, not fatal
            d = {"error": str(e)}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        json.dump(d, open(path, "w"))
        time.sleep(DELAY)
    files = d.get("files") or []
    pdfs = [{"name": f["name"], "size": int(f.get("size") or 0), "format": f.get("format")}
            for f in files if f["name"].lower().endswith(".pdf")
            and f.get("format") != "Additional Text PDF"]
    count = str((d.get("metadata") or {}).get("imagecount", ""))
    return {
        "pdfs": pdfs,
        "ocr": any(f["name"].endswith("_djvu.txt") for f in files),
        "pages": int(count) if count.isdigit() else None,
        "error": d.get("error"),
    }


def machine_index(machines):
    """Normalised machine name -> [slug], docs-bearing slugs first."""
    idx = collections.defaultdict(list)
    for m in sorted(machines, key=lambda m: -(m.get("d") or 0)):
        base = re.sub(r"\s*\(.*?\)", "", m["n"]).split(" / ")[0]
        for key in {norm(m["n"]), norm(base)}:
            if key and m["s"] not in idx[key]:
                idx[key].append(m["s"])
    return idx


# Uploaders' own labelling, which is not part of any machine's name: a leading
# "Arcade Game Manual:" and a trailing "by Konami".
LABEL = re.compile(r"^\s*arcade\s+game[^:]*:\s*", re.I)
MAKER = re.compile(r"\s+by\s+[A-Z][\w.&' -]*$")


def guess_machine(title, idx):
    """The longest leading run of the title that is a machine's name."""
    title = MAKER.sub("", LABEL.sub("", str(title or "")))
    words = [w for w in norm(title).split("_") if w]
    while words and DOC_TOKEN.match(words[-1]):
        words.pop()
    for n in range(len(words), 0, -1):
        key = "_".join(words[:n])
        if key in idx:
            return {"slug": idx[key][0], "matched": key, "whole": n == len(words)}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metadata", action="store_true", help="fetch per-item file lists for the unmatched items")
    ap.add_argument("--offline", action="store_true", help="no requests; recompute from cache/archive_org/")
    a = ap.parse_args()

    items = scrape(True if a.offline else None)
    docs = json.load(open(os.path.join(ROOT, "web", "data", "docs.json")))
    machines = json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))
    idx = machine_index(machines)
    by_id = {it["identifier"].lower(): it for it in items}
    by_title = {norm(it.get("title")): it for it in items}

    # Ours -> theirs, by the filename the upload kept.
    mirrors, matched = {}, set()
    for d in docs:
        if d.get("source") and d["source"] != "arcadertfm":
            continue
        key = norm(re.sub(r"\.pdf$", "", d["title"], flags=re.I))
        it = by_id.get(key) or by_title.get(key)
        if it:
            mirrors[d["id"]] = {"identifier": it["identifier"], "title": it.get("title"),
                                "dead": d.get("dead")}
            matched.add(it["identifier"])

    new, per_uploader, per_year = [], collections.Counter(), collections.Counter()
    no_docs = {m["s"] for m in machines if not m.get("d")}
    if a.metadata and not a.offline:
        # Three at a time with the per-request delay: polite to archive.org,
        # and an afternoon's pass becomes half an hour. Results go to the
        # cache; the loop below reads them back.
        todo = [it["identifier"] for it in items if it["identifier"] not in matched
                and not os.path.exists(os.path.join(CACHE, "meta", it["identifier"] + ".json"))]
        with ThreadPoolExecutor(max_workers=3) as pool:
            for i, _ in enumerate(pool.map(lambda i: metadata(i, True), todo), 1):
                if i % 100 == 0:
                    print(f"  metadata {i}/{len(todo)}", flush=True)
    for it in items:
        per_uploader[str(it.get("creator") or "?")] += 1
        per_year[(it.get("publicdate") or "????")[:4]] += 1
        if it["identifier"] in matched:
            continue
        rec = {
            "identifier": it["identifier"], "title": it.get("title"),
            "uploaded": (it.get("publicdate") or "")[:10],
            "bytes": int(it.get("item_size") or 0),
            "machine": guess_machine(it.get("title") or it["identifier"], idx),
        }
        meta = metadata(it["identifier"], False)
        if meta:
            rec.update(meta)
        new.append(rec)

    matched_machine = [r for r in new if r["machine"]]
    first_doc = {r["machine"]["slug"] for r in matched_machine if r["machine"]["slug"] in no_docs}
    with_meta = [r for r in new if r.get("pdfs") is not None]
    totals = {
        "items": len(items),
        "itemBytes": sum(int(it.get("item_size") or 0) for it in items),
        "oursMirrored": len(mirrors),
        "oursNotFound": sum(1 for d in docs if (not d.get("source") or d["source"] == "arcadertfm")
                            and d["id"] not in mirrors),
        "deadMirrored": sum(1 for m in mirrors.values() if m["dead"]),
        "new": len(new),
        "newMatchedToMachine": len(matched_machine),
        "newWholeTitleMatch": sum(1 for r in matched_machine if r["machine"]["whole"]),
        "machinesGainingFirstDocument": len(first_doc),
        "newWithMetadata": len(with_meta),
        "newPdfBytes": sum(p["size"] for r in with_meta for p in r["pdfs"]),
        "newWithArchiveOcr": sum(1 for r in with_meta if r.get("ocr")),
        "uploaders": per_uploader.most_common(6),
        "years": sorted(per_year.items()),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "source": {
            "name": "Internet Archive — arcademanuals collection",
            "url": f"https://archive.org/details/{COLLECTION}",
            "download": "https://archive.org/download/<identifier>/<file>",
            "surveyed": time.strftime("%Y-%m-%d"),
            "rights": "No licence on the items; private uploads of publisher-copyright "
                      "manuals, the same footing as ArcadeRTFM. Nothing taken; pointers only.",
        },
        "totals": totals,
        "mirrors": mirrors,
        "new": sorted(new, key=lambda r: r["title"] or ""),
    }, open(OUT, "w"), indent=1, sort_keys=True)

    print(f"{totals['items']:,} items, {totals['itemBytes']/1e9:.0f} GB as stored")
    print(f"ours mirrored {totals['oursMirrored']:,} (not found {totals['oursNotFound']}), "
          f"{totals['deadMirrored']} of our dead documents among them")
    print(f"new {totals['new']:,}: {totals['newMatchedToMachine']:,} matched to a machine "
          f"({totals['newWholeTitleMatch']:,} on the whole title), "
          f"{totals['machinesGainingFirstDocument']:,} machines would gain their first document")
    if with_meta:
        print(f"metadata for {len(with_meta):,}: {totals['newPdfBytes']/1e9:.1f} GB of PDF, "
              f"{totals['newWithArchiveOcr']:,} already OCR'd by archive.org")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
