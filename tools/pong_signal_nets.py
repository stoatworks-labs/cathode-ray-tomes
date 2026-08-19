#!/usr/bin/env python3
"""Signal nets traced by hand from Atari schematic 002826 Rev E.

Each entry below was read off the drawing at 500 dpi and cross-checked against
the device's datasheet gate mapping — a 7427 gate 2 really is pins 3/4/5 into
6, a 7425 gate 2 really is 9/10/12/13 into 8 — so a misread pin number shows up
as a gate that does not exist.

This covers the video output chain only. The rest of the sheet is not traced;
`COVERAGE` records that honestly rather than implying a complete netlist.
"""
import os
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, "kicad", "pong", "pong.kicad_pcb")

# net name -> [(ref, pad), ...]
NETS = {
    # 7427 G2 gate 2: VBLANK + 4V nor'd together produce the centre net line.
    "VBLANK":     [("UG2", "4")],
    "4V":         [("UG2", "3")],
    "NET":        [("UG2", "6"), ("UF2", "10")],

    # 7402 G1 gate 2 combines the horizontal and vertical video strobes.
    "HVID":       [("UG1", "6")],
    "VVID":       [("UG1", "5")],
    "HV_SUM":     [("UG1", "4"), ("UF2", "13")],

    # 7425 F2 gate 2 sums the picture elements; E4 buffers it to the output.
    "VIDEO_SUM":  [("UF2", "8"), ("UE4", "13")],
    "VIDEO":      [("UE4", "12")],
}

COVERAGE = "video output chain (8 nets); remainder of sheet 002826 not traced"

def main():
    board = pcbnew.LoadBoard(BOARD)
    by_ref = {fp.GetReference(): fp for fp in board.GetFootprints()}

    # Start net codes above the power rails already assigned.
    used = {n.GetNetCode() for n in board.GetNetsByName().values()} if hasattr(board.GetNetsByName(), "values") else set()
    next_code = 10

    added = missing = 0
    for name, pins in NETS.items():
        net = board.FindNet(name)
        if net is None:
            net = pcbnew.NETINFO_ITEM(board, name, next_code)
            board.Add(net)
            next_code += 1
        for ref, pad_no in pins:
            fp = by_ref.get(ref)
            if not fp:
                print(f"  ! no footprint {ref}")
                missing += 1
                continue
            pad = next((p for p in fp.Pads() if p.GetNumber() == pad_no), None)
            if not pad:
                print(f"  ! {ref} has no pad {pad_no}")
                missing += 1
                continue
            pad.SetNet(net)
            added += 1

    pcbnew.SaveBoard(BOARD, board)
    names = sorted({p.GetNetname() for fp in board.GetFootprints()
                    for p in fp.Pads() if p.GetNetname()})
    print(f"{added} pin connections over {len(NETS)} signal nets ({missing} unresolved)")
    print(f"nets on board: {', '.join(names)}")
    print(f"coverage: {COVERAGE}")

if __name__ == "__main__":
    main()
