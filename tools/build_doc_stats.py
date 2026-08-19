#!/usr/bin/env python3
"""Fold per-document ingest results back into the doc catalogue.

Adds page count, word count, section count and an `ingested` flag so the browse
and machine views can show what is actually readable without fetching each
document's OCR blob.
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "data", "index", "docs.json")
CACHE = os.path.join(ROOT, "cache", "text")

def main():
    docs = json.load(open(DOCS))
    stats = {}
    for fp in glob.glob(os.path.join(CACHE, "*.json")):
        try:
            d = json.load(open(fp))
        except Exception:
            continue
        m = d.get("meta", {})
        stats[d.get("id")] = {
            "pages": m.get("pageCount", 0),
            "words": m.get("words", 0),
            "sections": len(d.get("outline", [])),
        }
    hit = 0
    for doc in docs:
        s = stats.get(doc["id"])
        if not s:
            doc["ingested"] = False
            continue
        hit += 1
        doc.update({"ingested": True, "pages": s["pages"],
                    "words": s["words"], "sections": s["sections"]})
    json.dump(docs, open(DOCS, "w"), separators=(",", ":"))

    # The per-machine detail records embed their own copy of the doc list, so
    # they need the same fields or the machine page shows nothing as digitised.
    touched = 0
    for fp in glob.glob(os.path.join(ROOT, "data", "machine", "*.json")):
        rec = json.load(open(fp))
        changed = False
        for doc in rec.get("docs", []):
            s = stats.get(doc["id"])
            doc["ingested"] = bool(s)
            if s:
                doc.update({"pages": s["pages"], "words": s["words"],
                            "sections": s["sections"]})
                changed = True
        if changed:
            json.dump(rec, open(fp, "w"), separators=(",", ":"))
            touched += 1

    total_pages = sum(s["pages"] for s in stats.values())
    total_sections = sum(s["sections"] for s in stats.values())
    print(f"{hit}/{len(docs)} documents ingested · {total_pages} pages · "
          f"{total_sections} sections · {touched} machine records updated")

if __name__ == "__main__":
    main()
