#!/usr/bin/env python3
"""Build the Atari Pong board layout from assembly drawing A001433 Rev E.

Run with KiCAD's bundled Python (it needs pcbnew):

  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/\
Versions/3.9/bin/python3 tools/build_pong_pcb.py

The drawing gives every IC's position on an A-H by 1-9 grid, silkscreened on
the real board and referenced throughout the service manual. That grid is
reproduced here so the board view doubles as a "which chip is at C4" map.

Absolute dimensions are approximate: the drawing is not dimensioned, so the
grid pitch is set to a standard 1.0in x 0.75in DIP spacing, which puts the
board at roughly the 9.5in x 6.5in of the original. Grid *topology* is exact.
"""
import os, sys, re
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, "kicad", "pong", "pong.kicad_pcb")
FPLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

MM = pcbnew.FromMM
COL_PITCH, ROW_PITCH = 25.4, 19.05
X0, Y0 = 26.0, 20.0
ROWS = "HGFEDCBA"                      # H at the top of the drawing

# Grid map read from assembly drawing A001433 Rev E.
GRID = {
    "H": {1:"7400",2:"74107",3:"7474",4:"7400",5:"7400",6:"7420",7:"9316"},
    "G": {1:"7402",2:"7427",3:"7400",4:"555",5:"7410",6:"74107",7:"9316"},
    "F": {1:"7433",2:"7425",3:"74107",4:"555",5:"7402",6:"74107",7:"7430",8:"7493",9:"7493"},
    "E": {1:"7400",2:"7410",3:"7427",4:"7404",5:"7427",6:"7400",7:"7474",8:"7493",9:"7493"},
    "D": {1:"7404",2:"7402",3:"7430",4:"7410",5:"7410",6:"74153",7:"7490",8:"7410",9:"74107"},
    "C": {1:"7400",2:"7474",3:"7400",4:"7410",5:"7448",6:"74153",7:"7490",8:"74107",9:"7404"},
    "B": {2:"7400",3:"9316",4:"7483",5:"7474",6:"7450",7:"7400",8:"7493",9:"555"},
    "A": {2:"74107",3:"9316",4:"7486",5:"7474",6:"7450",7:"7420",8:"7493",9:"555"},
}
# 16-pin parts; everything else in the grid is a 14-pin DIP (555s are 8-pin).
DIP16 = {"9316", "74153", "7448", "7483"}
DIP8  = {"555"}

# Discretes, positioned to match the right-hand power/analog section and the
# decoupling row along the top edge of the drawing.
DISCRETE = [
    # ref, value, footprint, x, y, rot
    ("VR1", "LM309K",  "Package_TO_SOT_THT:TO-3",            238, 28, 0),
    ("C1",  "8000uF",  "Capacitor_THT:CP_Radial_D16.0mm_P7.50mm", 238, 62, 0),
    ("C2",  "470uF",   "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm", 238, 82, 0),
    ("D1",  "1N4001",  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 238, 96, 90),
    ("D2",  "1N4001",  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 238, 104, 90),
    ("D3",  "1N4001",  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 238, 112, 90),
    ("D4",  "1N4001",  "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 238, 120, 90),
    ("D5",  "1N914",   "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",  238, 128, 90),
    ("Q1",  "2N3643",  "Package_TO_SOT_THT:TO-92-2",      226, 140, 0),
    ("Q2",  "2N3644",  "Package_TO_SOT_THT:TO-92-2",      232, 140, 0),
    ("RV1", "50K POT (Player 1)", "Potentiometer_THT:Potentiometer_Alpha_RD901F-40-00D_Single_Vertical", 210, 150, 0),
    ("RV2", "50K POT (Player 2)", "Potentiometer_THT:Potentiometer_Alpha_RD901F-40-00D_Single_Vertical", 228, 150, 0),
    ("C12", "1.0uF",   "Capacitor_THT:C_Disc_D7.5mm_W2.5mm_P5.00mm", 120, 158, 0),
    ("C13", "5.0uF",   "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm",     134, 158, 0),
]
RES = [("R1","2.2M"),("R2","330K"),("R3","2.2K"),("R4","1K"),("R5","1M"),
       ("R6","330R"),("R7","330R"),("R8","100R"),("R9","5.6K"),("R10","50K")]

def outline(board, w, h):
    """Rectangular board edge on Edge.Cuts."""
    pts = [(0, 0), (w, 0), (w, h), (0, h), (0, 0)]
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        board.Add(seg)

# KiCAD 10 moved footprint loading onto the IO plugin; the module-level
# pcbnew.FootprintLoad() no longer works. The plugin must also be created
# *after* the board is loaded, or it hands back raw SWIG pointers instead of
# FOOTPRINT objects.
# Construct our own IO object rather than borrowing the manager's: the one
# PCB_IO_MGR.FindPlugin() hands back is manager-owned and gets freed
# unpredictably, after which it degrades to a bare SWIG pointer mid-run.
_IO = pcbnew.PCB_IO_KICAD_SEXPR()

def add(board, lib, name, ref, value, x, y, rot=0):
    fp = _IO.FootprintLoad(os.path.join(FPLIB, lib + ".pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint not found: {lib}:{name}")
    fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    fp.SetReference(ref)
    fp.SetValue(value)
    if rot:
        fp.SetOrientationDegrees(rot)
    fp.Reference().SetVisible(True)
    fp.Value().SetVisible(False)
    board.Add(fp)
    return fp

def main():
    # Build from a brand-new board every time. Never board.Remove() an existing
    # footprint: doing so corrupts SWIG's type registry for the rest of the
    # process, after which FootprintLoad() returns bare pointers instead of
    # FOOTPRINT objects and every attribute access fails.
    if os.path.exists(BOARD):
        os.remove(BOARD)
    board = pcbnew.NewBoard(BOARD)
    outline(board, 247.0, 165.0)

    n = 0
    for ri, row in enumerate(ROWS):
        for col, value in sorted(GRID[row].items()):
            x = X0 + (col - 1) * COL_PITCH
            y = Y0 + ri * ROW_PITCH
            if value in DIP8:
                lib, name = "Package_DIP", "DIP-8_W7.62mm"
            elif value in DIP16:
                lib, name = "Package_DIP", "DIP-16_W7.62mm"
            else:
                lib, name = "Package_DIP", "DIP-14_W7.62mm"
            # The drawing sets every IC long-axis horizontal.
            add(board, lib, name, f"U{row}{col}", value, x, y, 90)
            n += 1

    # Decoupling caps run along the top edge, one per column.
    for i in range(9):
        add(board, "Capacitor_THT", "C_Disc_D5.0mm_W2.5mm_P5.00mm",
            f"C{i+3}", "0.1uF", X0 + i * COL_PITCH, 9.0, 0)

    for i, (ref, val) in enumerate(RES):
        add(board, "Resistor_THT", "R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal",
            ref, val, 214.0, 24.0 + i * 6.0, 90)

    for ref, val, fpid, x, y, rot in DISCRETE:
        lib, name = fpid.split(":")
        add(board, lib, name, ref, val, x, y, rot)

    add(board, "Connector_PinHeader_2.54mm", "PinHeader_1x15_P2.54mm_Vertical",
        "J1", "Edge Connector", 8.0, 60.0, 0)

    pcbnew.SaveBoard(BOARD, board)
    print(f"placed {len(list(board.GetFootprints()))} footprints "
          f"({n} ICs on the A-H x 1-9 grid)")

if __name__ == "__main__":
    main()
