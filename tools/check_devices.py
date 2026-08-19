#!/usr/bin/env python3
"""Cross-check tools/devices.py against KiCAD's own symbol library.

The pinout table is the constraint set the extractor trusts, so it must not
rest on recall. This parses the .kicad_sym files shipped with KiCAD and
compares pin count, supply pins and pin numbering.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devices import DEVICES

LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

# our part number -> KiCAD symbol name. The library carries the plain 74xx
# names, most of which are `(extends "74LSxx")`, so the lookup follows that.
# 7400 and 7402 exist under their plain names; the rest of the family is only
# present as the LS part, which is pin-compatible.
MAP = {"7400": "7400", "7402": "7402"}
MAP.update({p: "74LS" + p[2:] for p in
            ["7404", "7410", "7420", "7427", "7430", "7433", "7448", "7474",
             "7483", "7486", "7490", "7493", "74107", "74153"]})
MAP["9316"] = "74LS161"

def _block(src, name):
    i = src.find(f'(symbol "{name}"')
    if i < 0:
        return None
    depth, j = 0, i
    while j < len(src):
        if src[j] == "(":
            depth += 1
        elif src[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    return src[i:j]

def parse_symbol(path, name, _depth=0):
    """Return {pin_number: (name, electrical_type)}.

    Most plain 74xx symbols are `(extends "74LSxx")` and carry no pins of their
    own, so follow the inheritance to wherever the pins actually live.
    """
    src = open(path, encoding="utf-8", errors="ignore").read()
    block = _block(src, name)
    if block is None:
        return None
    ext = re.search(r'\(extends\s+"([^"]+)"', block)
    if ext and _depth < 4:
        return parse_symbol(path, ext.group(1), _depth + 1)
    i = 0
    pins = {}
    for m in re.finditer(r'\(pin\s+(\w+)\s+\w+\s*\n.*?'
                         r'\(name\s+"([^"]*)".*?\(number\s+"([^"]*)"', block, re.S):
        etype, pname, num = m.group(1), m.group(2), m.group(3)
        pins[num] = (pname, etype)
    return pins

def main():
    ok = bad = skipped = 0
    for part, spec in sorted(DEVICES.items()):
        sym = MAP.get(part)
        if not sym:
            print(f"  {part:<7} no KiCAD equivalent — not cross-checked")
            skipped += 1
            continue
        pins = parse_symbol(os.path.join(LIB, "74xx.kicad_sym"), sym)
        if not pins:
            print(f"  {part:<7} symbol {sym} not found")
            skipped += 1
            continue

        problems, notes = [], []
        # KiCAD omits no-connect pins, so its symbol can legitimately have
        # fewer pins than the physical package (a 7493 is DIP-14 with 4 NCs).
        # Only an excess is a real contradiction.
        if len(pins) > spec["pins"]:
            problems.append(f"symbol has {len(pins)} pins, package is {spec['pins']}")
        elif len(pins) < spec["pins"]:
            notes.append(f"{spec['pins'] - len(pins)} no-connect pin(s) absent from symbol")
        # supply pins
        for role, want in (("vcc", spec["vcc"]), ("gnd", spec["gnd"])):
            got = [n for n, (pn, et) in pins.items()
                   if pn.upper() in ({"VCC"} if role == "vcc" else {"GND"})]
            if got and str(want) not in got:
                problems.append(f"{role} is {'/'.join(sorted(got))}, table says {want}")
        # every pin we reference must exist on the real part
        referenced = {p for g in spec["gates"]
                      for p in g.get("in", []) + g.get("out", []) + g.get("ctrl", [])}
        missing = sorted(p for p in referenced if str(p) not in pins)
        if missing:
            problems.append(f"pins not on device: {missing}")
        # outputs in the table should be outputs on the symbol
        for g in spec["gates"]:
            for p in g.get("out", []):
                et = pins.get(str(p), ("", ""))[1]
                if et not in ("output", "tri_state", "open_collector", "bidirectional",
                              "open_emitter", "unspecified", "passive"):
                    problems.append(f"pin {p} typed '{et}', table calls it an output")

        if problems:
            bad += 1
            print(f"  {part:<7} {sym:<9} MISMATCH")
            for p in problems:
                print(f"            - {p}")
        else:
            ok += 1
            extra = f" — {notes[0]}" if notes else ""
            print(f"  {part:<7} {sym:<9} ok ({len(pins)} functional pins, "
                  f"VCC={spec['vcc']} GND={spec['gnd']}){extra}")

    print(f"\n{ok} verified, {bad} mismatched, {skipped} not cross-checkable")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
