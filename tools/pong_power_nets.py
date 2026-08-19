#!/usr/bin/env python3
"""Assign the +5V and GND rails across the Pong board.

Power pins are the one part of this board that can be stated with certainty
without tracing the schematic: they are fixed by each device's datasheet. Note
the three exceptions that catch people out —

  7490 / 7493   VCC=5,  GND=10   (not the corner pins)
  7483          VCC=5,  GND=12
  555           VCC=8,  GND=1

Everything else follows the usual TTL convention: last pin VCC, middle pin GND.

Run with KiCAD's bundled Python. Signal nets are NOT set here; those require
tracing schematic 002826 by hand.
"""
import os, sys
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD = os.path.join(ROOT, "kicad", "pong", "pong.kicad_pcb")

# value -> (vcc pin, gnd pin)
POWER = {
    "7400": (14, 7), "7402": (14, 7), "7404": (14, 7), "7410": (14, 7),
    "7420": (14, 7), "7425": (14, 7), "7427": (14, 7), "7430": (14, 7),
    "7433": (14, 7), "7450": (14, 7), "7474": (14, 7), "7486": (14, 7),
    "74107": (14, 7),
    "7490": (5, 10), "7493": (5, 10),          # non-standard
    "7483": (5, 12),                            # non-standard
    "9316": (16, 8), "74153": (16, 8), "7448": (16, 8),
    "555": (8, 1),
}

def main():
    board = pcbnew.LoadBoard(BOARD)

    def net(name, code):
        """A NETINFO_ITEM needs an explicit net code: created without one it
        serialises as (net "NAME") with no number, which KiCAD treats as no
        net at all and IBOM reads as an empty netlist."""
        found = board.FindNet(name)
        if found:
            return found
        n = pcbnew.NETINFO_ITEM(board, name, code)
        board.Add(n)
        return n

    vcc, gnd = net("+5V", 1), net("GND", 2)

    ics = caps = 0
    for fp in board.GetFootprints():
        ref, val = fp.GetReference(), fp.GetValue()
        pins = POWER.get(val)
        if pins:
            vp, gp = pins
            for pad in fp.Pads():
                num = pad.GetNumber()
                if num == str(vp):
                    pad.SetNet(vcc)
                elif num == str(gp):
                    pad.SetNet(gnd)
            ics += 1
        elif val == "0.1uF" and ref.startswith("C"):
            # The decoupling row sits directly across the rails.
            for pad in fp.Pads():
                pad.SetNet(vcc if pad.GetNumber() == "1" else gnd)
            caps += 1

    board.BuildListOfNets()
    pcbnew.SaveBoard(BOARD, board)
    tally = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            n = pad.GetNetname()
            if n:
                tally[n] = tally.get(n, 0) + 1
    print(f"{ics} ICs and {caps} decoupling caps connected to the rails")
    for n, c in sorted(tally.items()):
        print(f"  {n:6} {c} pads")

if __name__ == "__main__":
    main()
