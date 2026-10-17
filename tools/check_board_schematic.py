#!/usr/bin/env python3
"""Prove a board's KiCad schematic says what its hand-read netlist says.

The schematic is drawn through Konnect from boards/<slug>.netlist.json, one
label at a time across several sheets, so it can drift from the read in ways
no single tool call would notice: a label on the wrong pin, a net that missed
a sheet, a global label that never met its partner. This exports the netlist
KiCad itself computes and compares it, pin for pin, with the read.

  tools/check_board_schematic.py battlezone-math-box

Exit status 0 only when every net in the read is exactly one net in KiCad and
no pin is joined to anything the read does not join it to.
"""
import json, os, re, subprocess, sys, tempfile, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"


def kicad_nets(sch):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "board.net")
        subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", out, sch],
                       check=True, capture_output=True)
        text = open(out).read()
    nets = {}
    for name, body in re.findall(r'\(net\s+\(code "\d+"\)\s+\(name "([^"]*)"\)(.*?)\n\t\t\)', text, re.S):
        pins = {f"{r}.{p}" for r, p in re.findall(r'\(ref "([^"]+)"\)\s+\(pin "([^"]+)"', body)}
        pins = {p for p in pins if not p.startswith("#")}
        if pins:
            nets[name] = pins
    return nets


def main():
    slug = sys.argv[1]
    read = json.load(open(os.path.join(ROOT, "boards", f"{slug}.netlist.json")))
    sch = os.path.join(ROOT, "kicad", slug, f"{slug}.kicad_sch")
    kn = kicad_nets(sch)
    where = {p: n for n, pins in kn.items() for p in pins}
    problems = []
    seen_kicad = set()
    for name, net in read["nets"].items():
        pins = set(net["pins"])
        homes = collections.Counter(where.get(p, "<missing>") for p in pins)
        if len(homes) != 1:
            problems.append(f"{name}: split across KiCad nets {dict(homes)}")
            continue
        home = next(iter(homes))
        if home == "<missing>":
            problems.append(f"{name}: none of its pins are in the schematic")
            continue
        seen_kicad.add(home)
        extra = kn[home] - pins
        if extra:
            problems.append(f"{name}: KiCad net {home} also joins {sorted(extra)}")
    nc = set(read["nc"])
    for name, pins in kn.items():
        if name in seen_kicad:
            continue
        stray = pins - nc
        if stray:
            problems.append(f"KiCad net {name} is not in the read: {sorted(stray)}")
    for p in problems:
        print("  !", p)
    total = sum(len(n["pins"]) for n in read["nets"].values())
    print(f"{slug}: {len(read['nets'])} nets / {total} pins in the read, "
          f"{len(kn)} nets in the schematic, {len(problems)} disagreement(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
