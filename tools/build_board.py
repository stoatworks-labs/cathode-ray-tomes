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
from devices import DEVICES

# KiCAD 10 moved footprint loading onto the IO plugin, and the object returned
# by PCB_IO_MGR.FindPlugin() is manager-owned and gets freed mid-run.
_IO = pcbnew.PCB_IO_KICAD_SEXPR()

def package_for(part):
    """Derive the DIP package from the device's pin count."""
    spec = DEVICES.get(part)
    if not spec:
        return "Package_DIP", "DIP-14_W7.62mm"
    return "Package_DIP", f"DIP-{spec['pins']}_W7.62mm"

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

    n_ic = 0
    for cell, part in spec["ics"].items():
        row, col = cell[0], int(cell[1:])
        ri = rows.index(row)
        x = g["x0"] + (col - 1) * g["col_pitch"]
        y = g["y0"] + ri * g["row_pitch"]
        lib, name = package_for(part)
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
    return n_ic, total

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.slug + ".json")))
    out_dir = os.path.join(ROOT, "kicad", a.slug)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, a.slug + ".kicad_pcb")

    n_ic, total = build(spec, out)
    parts = {}
    for cell, p in spec["ics"].items():
        parts[p] = parts.get(p, 0) + 1
    print(f"{spec['name']}: {total} footprints ({n_ic} ICs on the "
          f"{spec['grid']['rows'][-1]}-{spec['grid']['rows'][0]} grid)")
    print(f"  distinct IC types: {len(parts)}")
    print(f"  -> {out}")

if __name__ == "__main__":
    main()
