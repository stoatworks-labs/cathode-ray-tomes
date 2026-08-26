#!/usr/bin/env python3
"""Place the memory and MPU devices the IC parts lists never reach.

Atari stocks ROM, RAM and the microprocessor under its own part numbers —
90-7033, 036175-01, 90-6013 — not as 37-series IC stock, so
`extract_ic_locations.py` cannot see them however well it reads. That is why
Centipede's six ROMs were missing and why Red Baron's map had ten devices.

Same parts list, same typeset rows, same discipline as the IC merge: the
drawing read wins where it exists, two documents must agree, and a device is
only placed when its package can be established. What differs is how the
package is established, because a part number like 036175-01 says nothing about
pin count on its own. Two sources are used, in order:

  table    packages.py, whose Atari stock numbers were themselves derived from
           socket entries counted *within* a single document
  MAME     the dump size for that position in MAME's romset, which fixes the
           device class: 2K is a 24-pin 2716/2316, 256 bytes a 16-pin PROM

Socket entries are deliberately *not* consulted per-machine here. Aggregating
them across a machine's documents correlates one printing's parts list against
another printing's sockets, and those number the board differently — it is what
put a 2114 in a 40-pin socket when this was first written. The only sound use
of them is within one document, which is where packages.py's entries come from.

A cell with neither is reported and left off the map. Writes nothing without
--apply.
"""
import argparse, collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from extract_ic_locations import memory_rows
from check_socket_pins import sockets, first_cell
from packages import pins_for

CLASS_NAME = {"mpu": "Microprocessor", "ram": "RAM", "rom": "ROM",
              "prom": "PROM"}


def pins_from_size(size):
    if size in (0x20, 0x100, 0x200):
        return 16
    if size in (0x400, 0x800, 0x1000, 0x2000):
        return 24
    if size in (0x4000, 0x8000):
        return 28
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--machine", required=True)
    ap.add_argument("--figure", metavar="REGEX")
    ap.add_argument("--mame", help="parsed MAME ROM data (json)")
    ap.add_argument("--mame-set", help="MAME set name; defaults to --machine")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.board + ".json")))
    ics, rows_, spans = spec["ics"], spec["grid"]["rows"], spec.get("spans", {})
    cols = spec["grid"].get("cols")

    docs = [d["id"] for d in
            json.load(open(os.path.join(ROOT, "data/index/docs.json")))
            if d.get("machine") == a.machine and d.get("ingested")]

    # what the parts lists say, and how many documents say it
    votes = collections.defaultdict(collections.Counter)
    for fid in docs:
        try:
            rows = memory_rows(fid, a.figure)
        except Exception:
            continue
        for part, kind, cells in rows:
            for c in cells:
                votes[c][(part, kind)] += 1

    # what the socket entries say about pin counts
    sock = {}
    for fid in docs:
        try:
            for des, n in sockets(fid, a.figure).items():
                sock.setdefault(first_cell(des), set()).add(n)
        except Exception:
            continue

    # what MAME dumped at each position
    mame = {}
    if a.mame:
        sets = json.load(open(a.mame))
        s = sets.get(a.mame_set or a.machine)
        if s:
            for r in s["roms"]:
                if "." not in r["file"]:
                    continue
                cell = r["file"].rsplit(".", 1)[1].upper()
                if re.match(r'^[A-Z]{1,3}\d{1,2}$|^\d{1,2}[A-Z]{1,2}$', cell):
                    # keep the part number too: a dump at this cell only sizes
                    # the device the parts list names if it *is* that device
                    mame[first_cell(cell)] = (r["size"], r["file"].rsplit(".", 1)[0])

    placed, thin, unsized, conflict, offgrid = {}, [], [], [], []
    for cell, v in sorted(votes.items()):
        (part, kind), n = v.most_common(1)[0]
        base = first_cell(cell)
        span = cell if "/" in cell else None
        if base[0] not in rows_ or not base[1:].isdigit():
            offgrid.append((cell, part)); continue
        if cols and int(base[1:]) > cols:
            offgrid.append((cell, part)); continue
        if base in ics:
            conflict.append((base, ics[base], part)); continue
        if n < 2:
            thin.append((cell, part)); continue
        pins = why = None
        known, prov = pins_for(part)
        if known:
            pins, why = known, f"packaging table ({prov})"
        elif base in mame:
            size, fname = mame[base]
            # MAME's dump sizes the part only when it is the same part. The
            # same cell holds different devices on different revisions, and
            # sizing 036175-01 from a dump of 037000-01 is sizing the socket,
            # not the chip.
            stem = part.lower().replace("-", "")
            if stem in fname.lower().replace("-", "") and pins_from_size(size):
                pins, why = pins_from_size(size), f"MAME dump of {part}, {size} bytes"
        if pins is None:
            unsized.append((cell, part, kind)); continue
        placed[base] = {"part": part, "kind": kind, "pins": pins,
                        "why": why, "docs": n, "span": span}

    print(f"{a.board}: {len(docs)} documents, {len(votes)} memory positions named")
    print(f"  {len(placed):>3} placed")
    print(f"  {len(conflict):>3} already on the map, left alone")
    print(f"  {len(unsized):>3} no package could be established")
    print(f"  {len(thin):>3} attested by only one document")
    print(f"  {len(offgrid):>3} not a cell on this grid")
    for c, p, k in unsized:
        print(f"      unsized {c}: {p} ({k})")
    for c, was, now in conflict:
        print(f"      on map  {c}: has {was}, parts list says {now}")
    for c, p in offgrid:
        print(f"      off-grid {c}: {p}")
    if not a.apply:
        print("\n(dry run — pass --apply to write)")
        return

    for cell, d in placed.items():
        ics[cell] = d["part"]
        if d["span"]:
            spans[cell] = d["span"]
    spec["ics"] = dict(sorted(ics.items()))
    if spans:
        spec["spans"] = spans
    json.dump(spec, open(os.path.join(ROOT, "boards", a.board + ".json"), "w"),
              indent=1)

    cpath = os.path.join(ROOT, "data", "chips", a.board + ".json")
    chips = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for cell, d in placed.items():
        chips[cell] = {
            "part": d["part"], "section": CLASS_NAME.get(d["kind"], "Memory"),
            "note": f"Package established from the {d['why']}."
                    + (f" Spans {d['span']}." if d["span"] else ""),
            "otherRev": None,
            "source": f"parts list, {d['docs']} documents; package from "
                      f"the {d['why'].split(',')[0]}"}
    json.dump(dict(sorted(chips.items())), open(cpath, "w"), indent=1)
    print(f"\nwrote boards/{a.board}.json and data/chips/{a.board}.json")


if __name__ == "__main__":
    main()
