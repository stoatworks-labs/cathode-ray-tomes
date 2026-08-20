#!/usr/bin/env python3
"""Index the signature-analysis material across the corpus.

Signature analysis localises a fault to a node without tracing logic: clip the
analyser to a pin, read a four-character code, compare with the documented
value. Atari published these for a number of games and they are the sharpest
diagnostic material in the archive.

This records which documents carry it and, where the codes are printed on a
drawing sheet, extracts them. Per-IC association is approximate — the
designators are printed upright and the codes rotated, so the two come from
different OCR passes — and the output says so rather than implying precision.
"""
import json, glob, os, re, subprocess, sys, time
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_signatures import read, associate

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "signatures")
SHEETS = os.path.join(ROOT, "cache", "sheets")

MENTION = re.compile(r"signature\s+analy", re.I)

def render(doc_id, page=1, dpi=150):
    out = os.path.join(SHEETS, f"{doc_id}-{page}.png")
    if os.path.exists(out):
        return out
    pdf = os.path.join(ROOT, "cache", "pdf", doc_id + ".pdf")
    if not os.path.exists(pdf):
        return None
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-gray",
                    "-f", str(page), "-l", str(page), pdf,
                    os.path.join(SHEETS, doc_id)], capture_output=True, timeout=600)
    return out if os.path.exists(out) else None

def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(SHEETS, exist_ok=True)
    docs = {d["id"]: d for d in json.load(open(os.path.join(ROOT, "data/index/docs.json")))}

    # which documents carry signature analysis
    carriers = defaultdict(list)
    for f in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        did = os.path.basename(f)[:-5]
        meta = docs.get(did)
        if not meta:
            continue
        hit = bool(re.search(r"signature", meta["title"], re.I))
        if not hit:
            try:
                d = json.load(open(f))
            except Exception:
                continue
            txt = " ".join(b["t"] for p in d.get("pages", [])[:6]
                           for b in p.get("blocks", []))
            hit = bool(MENTION.search(txt))
        if hit:
            carriers[meta["machine"]].append(meta)

    t0, total_sigs = time.time(), 0
    for machine, metas in sorted(carriers.items()):
        entry = {"documents": [{"doc": m["id"], "title": m["title"],
                                "pages": m.get("pages", 0)} for m in metas],
                 "byDevice": {}, "codes": [],
                 "note": ("Signature codes are extracted from drawing sheets where "
                          "present. Per-device association is approximate: the "
                          "designators are printed upright and the codes rotated, so "
                          "they come from separate OCR passes. Treat the codes as "
                          "reliable and the grouping as a hint.")}
        merged, codes = defaultdict(set), set()
        for m in metas:
            if not m["schematic"] or m.get("pages", 0) > 4:
                continue
            png = render(m["id"])
            if not png:
                continue
            try:
                sigs, desigs = read(png)
            except Exception:
                continue
            codes.update(s["t"] for s in sigs)
            for k, v in associate(sigs, desigs).items():
                if k != "(unplaced)":
                    merged[k].update(v)
        entry["byDevice"] = {k: sorted(v) for k, v in sorted(merged.items())}
        entry["codes"] = sorted(codes)
        total_sigs += len(codes)
        json.dump(entry, open(os.path.join(OUT, machine + ".json"), "w"),
                  separators=(",", ":"))
        print(f"  {machine:<16} {len(metas):>2} docs, {len(codes):>3} codes, "
              f"{len(entry['byDevice']):>2} devices", flush=True)

    print(f"{len(carriers)} machines, {total_sigs} signature codes "
          f"({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()
