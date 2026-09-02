#!/usr/bin/env python3
"""Put MAME's ROM positions onto a board map, as their own named source.

The parts-list harvest never reaches memory. Atari stocks ROMs and PROMs under
its own part numbers rather than as 37-series IC stock, so the rows that carry
them fail the checksum the harvest depends on. That is why Red Baron's whole
complement was missing and why Centipede's ROMs were, and it is why 79 memory
positions on 15 published boards were empty when everything around them was
filled.

MAME has them. Its ROM file names encode the board position — `035224.e2` is
Atari part 035224 at E2, `037587-01.fh1` is at the span F/H1 — and they were
checked against real boards by people dumping them. The site already publishes
those maps as their own asset with their own caveat; this puts the positions on
the board map too, labelled as MAME's so the chip lookup says where each came
from, and only where the map has nothing. A cell the parts list already claims
is never touched: the three where MAME and a parts list disagree are logged in
the read files and stay logged, not overridden.

Letter-first boards only. MAME's rommaps carry a `style` and the early Atari
boards are all `letter-number`; a transposed board would need its cells read
the other way and none of the fifteen is one.
"""
import argparse, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from designators import cell_and_span

CELL = re.compile(r"^([A-Z]+)(\d{1,2})$")


def rom_cells(machine):
    """{cell: (part, span, file)} from MAME's map, spans keyed at first row."""
    p = os.path.join(ROOT, "data", "rommap", machine + ".json")
    if not os.path.exists(p):
        return {}
    rm = json.load(open(p))
    if rm.get("style") != "letter-number":
        raise SystemExit(f"{machine}: rommap style {rm.get('style')!r} — "
                         f"this tool reads letter-first cells only")
    out = {}
    for raw, dev in rm["devices"].items():
        m = CELL.match(raw.upper())
        if not m:
            continue
        letters, col = m.group(1), m.group(2)
        desig = "/".join(letters) + col if len(letters) > 1 else raw.upper()
        cell, span = cell_and_span(desig, False)
        part = dev["file"].rsplit(".", 1)[0]       # 035224.e2 -> 035224
        out[cell] = (part, span, dev["file"], dev.get("kind", "rom"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    registered = {b["slug"]: b for b in
                  json.load(open(os.path.join(ROOT, "data", "boards.json")))}
    for slug in a.slugs:
        bpath = os.path.join(ROOT, "boards", slug + ".json")
        board = json.load(open(bpath))
        if board["grid"].get("transposed"):
            print(f"{slug}: transposed grid — skipped"); continue
        machine = registered.get(slug, {}).get("machine") or board.get("machine")
        rows = board["grid"]["rows"]
        cols = board["grid"].get("cols")
        cells = rom_cells(machine)
        added, kept, offgrid = {}, [], []
        for cell, (part, span, f, kind) in sorted(cells.items()):
            if cell in board["ics"]:
                kept.append(cell); continue
            if cell[0] not in rows or (cols and int(cell[1:]) > cols):
                offgrid.append(cell); continue
            added[cell] = (part, span, f, kind)
        print(f"{slug:<20} {len(added):>2} ROM position(s) to add, "
              f"{len(kept)} already on the map, {len(offgrid)} off-grid")
        for cell, (part, span, f, kind) in added.items():
            print(f"      {span or cell:<6} {part:<14} {f}")
        if not a.apply or not added:
            continue

        for cell, (part, span, f, kind) in added.items():
            board["ics"][cell] = part
            if span:
                board.setdefault("spans", {})[cell] = span
        board["coverage"] = (board.get("coverage", "").rstrip() +
            f" {len(added)} memory device{'s' if len(added) > 1 else ''} "
            f"placed from MAME's ROM map, which encodes board positions in its "
            f"file names and was checked against real boards; the chip lookup "
            f"names MAME as the source for each.")
        board["ics"] = dict(sorted(board["ics"].items()))
        json.dump(board, open(bpath, "w"), indent=1)

        cpath = os.path.join(ROOT, "data", "chips", slug + ".json")
        chips = json.load(open(cpath)) if os.path.exists(cpath) else {}
        for cell, (part, span, f, kind) in added.items():
            chips[cell] = {"part": part, "section": "Program memory"
                           if kind == "program" else "Memory",
                           "note": f"MAME ROM {f}", "otherRev": None,
                           "source": "MAME ROM map"}
        json.dump(dict(sorted(chips.items())), open(cpath, "w"), indent=1)
        print(f"      wrote {len(added)} to {slug}")


if __name__ == "__main__":
    main()
