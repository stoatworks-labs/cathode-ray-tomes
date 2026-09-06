#!/usr/bin/env python3
"""Emit the recovered parts lists as site data.

Writes one file per document that has one, and records the row count on the
document catalogue so the UI can show which manuals carry a bill of materials
without fetching each one.
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_parts import from_document

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "parts")
MIN_ROWS = 8

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.json")):
        os.unlink(f)

    docs_path = os.path.join(ROOT, "data", "index", "docs.json")
    docs = json.load(open(docs_path))
    counts = {}

    for fp in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        did = os.path.basename(fp)[:-5]
        try:
            doc = json.load(open(fp))
        except Exception:
            continue
        rows = from_document(doc)
        if len(rows) < MIN_ROWS:
            continue
        # de-duplicate: the same part often repeats across figure lists.
        # A row whose description could not be recovered has to keep its item
        # number in the key, or every such row for one part collapses into one
        # and the item numbers that were the useful half are lost.
        seen, uniq = set(), []
        for r in rows:
            key = ((r["part"], r["item"]) if not r["desc"]
                   else (r["part"], r["desc"][:40].lower()))
            if key in seen:
                continue
            seen.add(key)
            uniq.append(r)
        json.dump(uniq, open(os.path.join(OUT, did + ".json"), "w"),
                  separators=(",", ":"))
        counts[did] = len(uniq)

    for d in docs:
        n = counts.get(d["id"])
        if n:
            d["parts"] = n
        else:
            d.pop("parts", None)
    json.dump(docs, open(docs_path, "w"), separators=(",", ":"))

    print(f"{len(counts)} documents with parts lists, "
          f"{sum(counts.values())} unique rows")

if __name__ == "__main__":
    main()
