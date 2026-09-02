#!/usr/bin/env python3
"""Normalise arcadertfm machines.json into Cathode Ray Tomes's index artefacts.

Inputs : data/machines.raw.json   (upstream MAME-derived metadata + doc list)
         data/systems.json        (consoles and handhelds, written by hand)
         data/extra-docs.json     (documents found elsewhere, merged in by hand)
Outputs: data/index/machines.json    compact browse/search index (all machines)
         data/index/docs.json        flat doc catalogue with stable ids
         data/machine/<slug>.json    per-machine detail records

A console is not a MAME machine — no romname, no DIP switches, and what
actually identifies one is a board revision rather than a driver. But it is the
same *kind of thing* to a repairer: something with documents, a chip complement
and a fault. So consoles are carried in the same index with `kind` set, rather
than as a second entity with a duplicate set of routes and views. Arcade
machines carry no kind at all, which keeps 7,812 records the size they were.

The raw dump is refetched and overwritten, so a document that is not in it has
to be carried separately or it disappears on the next fetch — hence the overlay.

An overlay entry names every machine it covers, because a document can. The
MVS service manual documents the two-slot and four-slot boards in one book, and
the honest model is one document on two machines rather than two copies: the id
is derived from the URL, so copies would collide on the rendered document
anyway. The record therefore carries a `machines` list alongside its primary
`machine`, and is listed under each of them.
"""
import json, os, re, hashlib, sys, unicodedata
from collections import Counter

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW     = os.path.join(ROOT, "data", "machines.raw.json")
SYSTEMS = os.path.join(ROOT, "data", "systems.json")
EXTRA   = os.path.join(ROOT, "data", "extra-docs.json")
OUT     = os.path.join(ROOT, "data")

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

def load_extra():
    """Overlay documents, grouped by the machine slug they should appear under."""
    if not os.path.exists(EXTRA):
        return {}, []
    entries = json.load(open(EXTRA)).get("documents") or []
    by_slug = {}
    for d in entries:
        slugs = d.get("machines") or []
        if not slugs or not d.get("l"):
            continue
        for slug in slugs:
            by_slug.setdefault(slug, []).append(d)
    return by_slug, entries


def overlay_docs(slug, name, extra, emitted, out_docs):
    """Overlay records for one slug. A document covering several machines is
    catalogued once, by whichever claims it first, and listed under each."""
    recs = []
    for d in extra.get(slug, []):
        did = doc_id(d["l"])
        rec = emitted.get(did)
        if rec is None:
            dtype = d.get("t") or "Document"
            rec = {
                "id": did, "machine": slug, "machineName": name,
                "title": d.get("f") or "", "type": dtype, "src": d["l"],
                "schematic": dtype in SCHEMATIC_TYPES,
                "machines": list(d["machines"]),
            }
            for k, out in (("source", "source"), ("page", "sourcePage"),
                           ("ingest", "ingest"), ("note", "note")):
                if d.get(k):
                    rec[out] = d[k]
            out_docs.append(rec); emitted[did] = rec
        recs.append(rec)
    return recs


def main():
    machines = json.load(open(RAW))
    extra, extra_entries = load_extra()
    seen_slugs, out_machines, out_docs, detail = {}, [], [], {}
    emitted = {}                             # doc id -> record, so a shared
                                             # document is catalogued once
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
            recs.append(rec); out_docs.append(rec); emitted[did] = rec

        recs += overlay_docs(slug, name, extra, emitted, out_docs)

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

    # Consoles and handhelds, into the same two artefacts. They have no
    # romname and no DIP banks; what identifies one is its board revision, so
    # that takes the place the DIP count holds for an arcade machine.
    systems = []
    if os.path.exists(SYSTEMS):
        systems = json.load(open(SYSTEMS)).get("systems") or []
    for s in systems:
        slug = s["slug"]
        if slug in seen_slugs:
            print(f"WARNING  system slug {slug} collides with a machine",
                  file=sys.stderr)
            continue
        seen_slugs[slug] = True
        name = s["name"]
        recs = overlay_docs(slug, name, extra, emitted, out_docs)
        boards = s.get("boards") or []

        out_machines.append({
            "s": slug, "n": name, "y": s.get("year") or "",
            "m": s.get("mfr") or "",
            "d": len(recs),
            "k": sum(1 for r in recs if r["schematic"]),
            "p": len(boards),                     # board revisions, not DIP banks
            "c": [c.get("n") for c in (s.get("cpu") or []) if c.get("n")][:3],
            "t": s.get("kind") or "console",      # absent on arcade machines
        })

        detail[slug] = {
            "slug": slug, "name": name, "year": s.get("year") or "",
            "mfr": s.get("mfr") or "", "rom": "",
            "kind": s.get("kind") or "console",
            "cpu": s.get("cpu") or [], "audio": s.get("audio") or [],
            "display": s.get("display") or [], "input": {},
            "dip": [], "boards": boards, "docs": recs,
        }

    # Names for the other machines a shared document covers, so the reader can
    # say "MV-2F · MV-4F" without fetching a record per slug.
    names = {slug: rec["name"] for slug, rec in detail.items()}
    missing = set()
    for rec in out_docs:
        if "machines" not in rec:
            continue
        missing |= {s for s in rec["machines"] if s not in names}
        rec["machineNames"] = [names.get(s, s) for s in rec["machines"]]
    if missing:
        print(f"WARNING  overlay names {len(missing)} unknown machine slug(s): "
              + ", ".join(sorted(missing)), file=sys.stderr)

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
    if systems:
        kinds = Counter(s.get("kind") or "console" for s in systems)
        print("systems       " + ", ".join(f"{c} {k}" for k, c in kinds.most_common()))
    if extra_entries:
        print(f"overlay       {len(extra_entries)} document(s) from data/extra-docs.json, "
              f"on {len(extra)} machine(s)")
    print(f"docs          {len(out_docs)}  ({sum(1 for d in out_docs if d['schematic'])} schematic-bearing)")
    print(f"with docs     {sum(1 for m in out_machines if m['d'])}")
    print(f"with dips     {sum(1 for m in out_machines if m['p'])}")
    print(f"index size    {os.path.getsize(os.path.join(OUT,'index','machines.json'))/1e6:.2f} MB")
    print("top doc types " + ", ".join(f"{t}={c}" for t, c in types.most_common(8)))

if __name__ == "__main__":
    main()
