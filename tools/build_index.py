#!/usr/bin/env python3
"""Normalise arcadertfm machines.json into Cathode Ray Tomes's index artefacts.

Inputs : data/machines.raw.json   (upstream MAME-derived metadata + doc list)
Outputs: data/index/machines.json    compact browse/search index (all machines)
         data/index/docs.json        flat doc catalogue with stable ids
         data/machine/<slug>.json    per-machine detail records
"""
import json, os, re, hashlib, sys, unicodedata
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW  = os.path.join(ROOT, "data", "machines.raw.json")
OUT  = os.path.join(ROOT, "data")

# Doc types that are expected to carry schematic/diagram line art worth vectorising.
SCHEMATIC_TYPES = {
    "Schematics", "Schematic Package", "Schematic Sheet",
    "Drawing Package", "Drawing Set", "Wiring Diagram", "Game Logic",
}

def slugify(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "unknown"

def doc_id(url):
    """Stable short id derived from the upstream URL, so ids survive re-ingest."""
    return hashlib.sha1(url.encode()).hexdigest()[:12]

def main():
    machines = json.load(open(RAW))
    seen_slugs, out_machines, out_docs, detail = {}, [], [], {}

    for m in machines:
        name = m.get("name") or "Unknown"
        base = m.get("id") or slugify(name)
        slug = base
        n = 2
        while slug in seen_slugs:            # romnames collide across clones/regions
            slug = f"{base}-{n}"; n += 1
        seen_slugs[slug] = True

        docs = m.get("docs") or []
        recs = []
        for d in docs:
            url = d.get("l") or ""
            if not url:
                continue
            did = doc_id(url)
            dtype = d.get("t") or "Document"
            rec = {
                "id": did, "machine": slug, "machineName": name,
                "title": d.get("f") or "", "type": dtype, "src": url,
                "schematic": dtype in SCHEMATIC_TYPES,
            }
            recs.append(rec); out_docs.append(rec)

        cpus = [c.get("n") for c in (m.get("cpu") or []) if c.get("n")]
        aud  = [a.get("n") for a in (m.get("aud") or []) if a.get("n")]
        disp = m.get("disp") or []
        dips = m.get("dip") or []

        # Compact record for the browse/search index shipped to the client.
        out_machines.append({
            "s": slug, "n": name, "y": m.get("y") or "", "m": m.get("m") or "",
            "d": len(recs),                              # doc count
            "k": sum(1 for r in recs if r["schematic"]),  # schematic-bearing doc count
            "p": len(dips),                              # dip switch bank count
            "c": cpus[:3],
        })

        # Full detail record, served per-machine.
        detail[slug] = {
            "slug": slug, "name": name, "year": m.get("y") or "",
            "mfr": m.get("m") or "", "rom": m.get("id") or "",
            "cpu": m.get("cpu") or [], "audio": m.get("aud") or [],
            "display": disp, "input": m.get("inp") or {},
            "dip": dips, "docs": recs,
        }

    os.makedirs(os.path.join(OUT, "index"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "machine"), exist_ok=True)
    json.dump(out_machines, open(os.path.join(OUT, "index", "machines.json"), "w"),
              separators=(",", ":"))
    json.dump(out_docs, open(os.path.join(OUT, "index", "docs.json"), "w"),
              separators=(",", ":"))
    for slug, rec in detail.items():
        json.dump(rec, open(os.path.join(OUT, "machine", slug + ".json"), "w"),
                  separators=(",", ":"))

    types = Counter(d["type"] for d in out_docs)
    print(f"machines      {len(out_machines)}")
    print(f"docs          {len(out_docs)}  ({sum(1 for d in out_docs if d['schematic'])} schematic-bearing)")
    print(f"with docs     {sum(1 for m in out_machines if m['d'])}")
    print(f"with dips     {sum(1 for m in out_machines if m['p'])}")
    print(f"index size    {os.path.getsize(os.path.join(OUT,'index','machines.json'))/1e6:.2f} MB")
    print("top doc types " + ", ".join(f"{t}={c}" for t, c in types.most_common(8)))

if __name__ == "__main__":
    main()
