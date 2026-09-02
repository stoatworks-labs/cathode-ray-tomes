#!/usr/bin/env python3
"""Generate a KiCAD board, BOM and interactive view from a board definition.

Adding a machine is data entry: describe its component grid in boards/<slug>.json
and this produces the .kicad_pcb, the bill of materials and the IBOM page. The
grid designators these manufacturers silkscreen on the board (A1-H9 on Pong)
become the reference designators, so the board view doubles as a "which chip is
at C4" map — which is how the service manuals index the hardware.

Run with KiCAD's bundled Python:

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/\
Versions/3.9/bin/python3 tools/build_board.py <slug>
"""
import argparse, json, os, sys
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
MM = pcbnew.FromMM

sys.path.insert(0, os.path.join(ROOT, "tools"))
from packages import package_for
from designators import parse as parse_desig

# KiCAD 10 moved footprint loading onto the IO plugin, and the object returned
# by PCB_IO_MGR.FindPlugin() is manager-owned and gets freed mid-run.
_IO = pcbnew.PCB_IO_KICAD_SEXPR()

def add(board, fpid, ref, value, x, y, rot=0):
    lib, name = fpid.split(":")
    fp = _IO.FootprintLoad(os.path.join(FPLIB, lib + ".pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {fpid}")
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    fp.SetReference(ref)
    fp.SetValue(value)
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.Reference().SetVisible(True)
    fp.Value().SetVisible(False)
    board.Add(fp)

def build(spec, out_path):
    # Always start from a fresh board: board.Remove() corrupts SWIG's type
    # registry for the rest of the process.
    board = pcbnew.NewBoard(out_path)
    g = spec["grid"]
    rows = g["rows"]

    # A device drawn across two or three grid cells is keyed at its first cell
    # (a grid cell is the only thing `ics` may be keyed by), with the sheet's
    # own designator — `L/M1`, `H/J2`, `L/M/N3` — recorded in `spans`. Placing
    # it at the first cell would hang a 2in DIP-40 symmetrically across its
    # neighbour on *both* sides, so the row index is the mean of the cells the
    # designator actually names.
    spans = spec.get("spans", {})
    # Which way round this board prints its designators — `A1` or `2L`. See
    # tools/designators.py; it is stated by the board, never inferred.
    transposed = bool(g.get("transposed"))

    for cell, desig in spans.items():
        parsed = parse_desig(desig, transposed)
        base = parse_desig(cell, transposed)
        if not parsed or not base:
            raise ValueError(f"span {desig} at {cell} is not a designator on "
                             f"this board's grid (transposed={transposed})")
        letters = list(parsed[0])
        if cell not in spec["ics"] or letters[0] != base[0][0]:
            raise ValueError(f"span {desig} must be keyed at its first cell, "
                             f"and that cell must be in `ics`; got {cell}")
        idx = sorted(rows.index(r) for r in letters)   # raises on a bad row
        if idx != list(range(idx[0], idx[0] + len(idx))):
            raise ValueError(f"span {desig} names rows that are not adjacent "
                             f"on this grid ({rows}) — one of them is likely a "
                             f"row the board does not actually have")

    n_ic = 0
    unsized = {}
    for cell, part in spec["ics"].items():
        parsed = parse_desig(cell, transposed)
        if not parsed:
            raise ValueError(f"`ics` key {cell!r} is not a grid cell on this "
                             f"board (transposed={transposed})")
        row, col = parsed[0][0], parsed[1]
        letters = list(parse_desig(spans[cell], transposed)[0]) \
            if cell in spans else [row]
        ri = sum(rows.index(r) for r in letters) / len(letters)
        x = g["x0"] + (col - 1) * g["col_pitch"]
        y = g["y0"] + ri * g["row_pitch"]
        lib, name, src = package_for(part)
        if src in ("no packaging entry",) or src.startswith("unidentified"):
            unsized.setdefault(part, []).append(cell)
        add(board, f"{lib}:{name}", f"U{cell}", part, x, y, g.get("rotation", 0))
        n_ic += 1

    d = spec.get("decoupling")
    if d:
        for i in range(d["count"]):
            add(board, d["footprint"], f"C{i+3}", d["value"],
                g["x0"] + i * g["col_pitch"], d["y"], 0)

    rl = spec.get("resistor_layout")
    for i, r in enumerate(spec.get("resistors", [])):
        add(board, rl["footprint"], r["ref"], r["value"],
            rl["x"], rl["y0"] + i * rl["dy"], rl.get("rotation", 0))

    for item in spec.get("discretes", []) + spec.get("connectors", []):
        add(board, item["footprint"], item["ref"], item["value"],
            item["x"], item["y"], item.get("rot", 0))

    size = spec["size"]
    for a, b in [((0, 0), (size["w"], 0)), ((size["w"], 0), (size["w"], size["h"])),
                 ((size["w"], size["h"]), (0, size["h"])), ((0, size["h"]), (0, 0))]:
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(a[0]), MM(a[1])))
        seg.SetEnd(pcbnew.VECTOR2I(MM(b[0]), MM(b[1])))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        board.Add(seg)

    pcbnew.SaveBoard(out_path, board)
    total = len(list(board.GetFootprints()))
    return n_ic, total, unsized

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.slug + ".json")))
    out_dir = os.path.join(ROOT, "kicad", a.slug)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, a.slug + ".kicad_pcb")

    n_ic, total, unsized = build(spec, out)
    parts, packages = {}, {}
    for cell, p in spec["ics"].items():
        parts[p] = parts.get(p, 0) + 1
        packages[package_for(p)[1]] = packages.get(package_for(p)[1], 0) + 1
    print(f"{spec['name']}: {total} footprints ({n_ic} ICs on the "
          f"{spec['grid']['rows'][-1]}-{spec['grid']['rows'][0]} grid)")
    print(f"  distinct IC types: {len(parts)}")
    print("  packages: " + ", ".join(
        f"{k.split('_')[0]}x{v}" for k, v in sorted(
            packages.items(), key=lambda kv: -kv[1])))
    # A part with no packaging entry is drawn as a DIP-14, which is the right
    # thing to do for one unreadable device on an otherwise good board and the
    # wrong thing to do quietly. Say so.
    if unsized:
        n = sum(len(v) for v in unsized.values())
        print(f"  {n} device(s) drawn as DIP-14 without a packaging entry:")
        for part, cells in sorted(unsized.items()):
            print(f"    {part:<24}{', '.join(sorted(cells))}")
    print(f"  -> {out}")

if __name__ == "__main__":
    main()
