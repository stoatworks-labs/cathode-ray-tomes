#!/usr/bin/env python3
"""Lay out boards/<slug>.netlist.json as a set of KiCad sheets, as data.

KiCad schematics are written through Konnect's MCP tools, never as text, so
this does not write one. It writes the plan those tools are driven from:
which symbol unit goes on which sheet and where, and which pins get a local
label, a global label (the net crosses sheets), a power symbol or a no-connect
flag. Every pin is connected by label rather than by drawn wire -- a scan
redrawn wire for wire would be no easier to follow than the scan.

Net names follow the sheet. Active-low names the sheet overbars get KiCad's
~{...} markup; a net the sheet leaves unnamed is named after the pin that
drives it, as the board silkscreens it (E4-6), so a label tells a reader where
the signal comes from.

  tools/plan_board_schematic.py battlezone-math-box   -> kicad/<slug>/plan/*.json
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_board_nets import KICAD, pinout   # noqa: E402

PROJECT_LIB = "battlezone-math-box"
LIB = dict(KICAD)
LIB.update({"137004-001": f"{PROJECT_LIB}:Am2901", "C012294-01": f"{PROJECT_LIB}:POKEY",
            "82S129": f"{PROJECT_LIB}:82S129", "82S123": f"{PROJECT_LIB}:82S123"})
# Rails drawn with KiCad power symbols. +22V has no stock symbol and only six
# pins, so it travels by global label like any other net.
POWER = ("+5V", "GND")

# Which KiCad unit holds which pins, read from the library so a gate is never
# guessed. Filled lazily.
_units = {}


def unit_of(libsym, pin):
    if libsym not in _units:
        lib, name = libsym.split(":")
        path = os.path.join("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
                            lib + ".kicad_sym")
        table = {}
        if os.path.exists(path):
            text = open(path).read()
            body = _symbol(text, name)
            ext = re.search(r'\(extends "([^"]+)"\)', body)
            if ext:
                name = ext.group(1)
                body = _symbol(text, name)
            for m in re.finditer(r'\(symbol "' + re.escape(name) + r'_(\d+)_\d+"', body):
                u = int(m.group(1))
                sub = _block(body, m.start())
                for n in re.findall(r'\(number "([^"]+)"', sub):
                    table[n] = u or 1
        _units[libsym] = table
    return _units[libsym].get(pin, 1)


def _block(text, i):
    d = 0
    for j in range(i, len(text)):
        d += {"(": 1, ")": -1}.get(text[j], 0)
        if d == 0:
            return text[i:j + 1]


def _symbol(text, name):
    return _block(text, text.find(f'(symbol "{name}"'))


def label_name(name):
    """Sheet spelling -> KiCad label text."""
    special = {
        "ER/WB": "ER/~{WB}", "/EI/O": "~{EI/O}", "SHELL L/S": "SHELL_L/~{S}",
        "EXPLO L/S": "EXPLO_L/~{S}", "/OUTPUT LATCH": "~{OUTPUT_LATCH}",
    }
    if name in special:
        return special[name]
    if name.startswith("/"):
        name = "~{" + name[1:] + "}"
    return name.replace(" ", "_")


# ---------------------------------------------------------------------------
# Sheets. Each unit: (ref, unit, x, y) in mm on an A4 sheet; refs are KiCad
# references. Passives and connectors are single-unit.
# ---------------------------------------------------------------------------
SHEETS = [
    ("seq", "Math Box sequencer", [
        ("UB1", 1, 45, 55), ("UC1", 1, 110, 55), ("UE1", 1, 175, 55), ("UD1", 1, 240, 55),
        ("UM1", 1, 30, 145), ("UL1", 1, 75, 145), ("UK1", 1, 120, 145),
        ("UJ1", 1, 165, 145), ("UH1", 1, 210, 145), ("UF1", 1, 255, 145)]),
    ("alu", "Math Box ALU", [
        ("UK2", 1, 45, 80), ("UF2", 1, 110, 80), ("UH2", 1, 175, 80), ("UD2", 1, 240, 80),
        ("UE5", 4, 25, 150), ("UD3", 4, 55, 150), ("UD3", 3, 85, 150), ("UE3", 4, 115, 150),
        ("UD3", 2, 145, 150), ("UE3", 3, 175, 150), ("UC5", 1, 210, 150), ("UD5", 2, 245, 150),
        ("UE5", 3, 270, 150), ("R1", 1, 130, 172)]),
    ("ctl", "Math Box control", [
        ("UB4", 1, 30, 45), ("UC5", 2, 75, 45), ("UC3", 1, 120, 45), ("UC3", 2, 165, 45),
        ("UJ4", 1, 210, 45), ("SA", 1, 255, 60),
        ("UC4", 4, 25, 95), ("UC4", 3, 55, 95), ("UC4", 2, 85, 95), ("UD4", 1, 115, 95),
        ("UD4", 2, 145, 95), ("UD4", 3, 175, 95), ("UD4", 4, 205, 95),
        ("UD3", 1, 25, 135), ("UD5", 1, 55, 135), ("UD5", 3, 85, 135), ("UD5", 4, 115, 135),
        ("UE3", 1, 145, 135), ("UE4", 3, 175, 135), ("UE4", 4, 205, 135), ("UE4", 5, 235, 135),
        ("UE4", 6, 265, 135),
        ("R2", 1, 40, 175), ("R3", 1, 80, 175), ("R22", 1, 120, 175)]),
    ("io", "Interconnect, edge connector and output latch", [
        ("P1", 1, 40, 95), ("P2", 1, 120, 95), ("UM2", 1, 210, 70),
        ("R38", 1, 210, 140), ("TP1", 1, 25, 175), ("TP2", 1, 45, 175), ("TP3", 1, 65, 175),
        ("TP4", 1, 85, 175), ("TP5", 1, 105, 175)]),
    ("pokey", "POKEY and control panel inputs", [
        ("UB2", 1, 200, 95),
        ("R43", 1, 30, 45), ("R44", 1, 40, 45), ("R41", 1, 50, 45), ("R42", 1, 60, 45),
        ("R39", 1, 70, 45), ("R40", 1, 80, 45),
        ("R51", 1, 30, 90), ("R52", 1, 45, 90), ("R49", 1, 60, 90), ("R50", 1, 75, 90),
        ("R47", 1, 90, 90), ("R48", 1, 105, 90),
        ("C34", 1, 30, 135), ("C35", 1, 45, 135), ("C32", 1, 60, 135), ("C33", 1, 75, 135),
        ("C30", 1, 90, 135), ("C31", 1, 105, 135),
        ("R46", 1, 255, 60), ("R36", 1, 255, 110), ("C25", 1, 255, 145)]),
    ("noise", "Noise generator and engine sound", [
        ("UB4", 2, 25, 45), ("UH5", 1, 75, 45), ("UH4", 1, 130, 45), ("UJ4", 2, 180, 40),
        ("UJ5", 1, 225, 40), ("UJ5", 2, 265, 40),
        ("UE5", 2, 180, 85), ("UE5", 1, 225, 85),
        ("UL4", 1, 25, 120), ("R5", 1, 45, 120), ("R6", 1, 55, 135), ("R7", 1, 65, 110),
        ("R8", 1, 80, 120), ("CR1", 1, 80, 135), ("R9", 1, 95, 135), ("C13", 1, 110, 140),
        ("UK5", 2, 130, 125), ("UF3", 1, 175, 130), ("R10", 1, 150, 110), ("R11", 1, 150, 130),
        ("C11", 1, 150, 150),
        ("UF4", 1, 215, 125), ("UF5", 1, 265, 125), ("UE4", 1, 215, 155), ("UE4", 2, 265, 155),
        ("R20", 1, 25, 175), ("R21", 1, 45, 175), ("R34", 1, 65, 175), ("R35", 1, 85, 175),
        ("C29", 1, 105, 175)]),
    ("audio", "Shell, explosion, mixer and output", [
        ("UL4", 3, 25, 35), ("R12", 1, 50, 45), ("R13", 1, 65, 35), ("C21", 1, 85, 25),
        ("R32", 1, 85, 35), ("UK5", 3, 110, 45),
        ("UJ3", 4, 25, 70), ("C9", 1, 45, 80), ("UJ3", 3, 60, 70), ("R14", 1, 80, 70),
        ("R15", 1, 90, 80),
        ("UL4", 2, 25, 105), ("R19", 1, 50, 115), ("R18", 1, 65, 105), ("C22", 1, 85, 95),
        ("R33", 1, 85, 105), ("UK5", 1, 110, 115),
        ("UJ3", 1, 25, 140), ("C14", 1, 45, 150), ("UJ3", 2, 60, 140), ("R17", 1, 80, 140),
        ("R16", 1, 90, 150),
        ("R25", 1, 150, 60), ("R28", 1, 150, 75), ("R26", 1, 150, 90), ("R27", 1, 150, 105),
        ("UL4", 4, 175, 80), ("R29", 1, 195, 105), ("UK5", 4, 215, 90), ("R30", 1, 200, 70),
        ("R31", 1, 225, 70), ("C20", 1, 240, 120), ("R24", 1, 255, 120), ("UM5", 4, 265, 150),
        ("R23", 1, 265, 130)]),
    ("power", "Power input and decoupling", []),
]


def build_plan(slug):
    net = json.load(open(os.path.join(ROOT, "boards", f"{slug}.netlist.json")))
    comps = net["components"]
    nets = net["nets"]

    def libsym(ref):
        part = comps[ref]["part"]
        if part:
            return LIB[part]
        if ref.startswith("TP"):
            return "Connector:TestPoint"
        if ref == "P1":
            return "Connector_Generic:Conn_01x24"
        if ref == "P2":
            return f"{PROJECT_LIB}:Edge_22x2_Atari"
        if ref == "SA":
            return "Connector_Generic:Conn_01x10"
        if ref == "R11":
            return "Device:R_Potentiometer"
        if ref == "CR1":
            return "Diode:1N914"
        if ref == "CR2":
            return "Device:LED"
        if ref.startswith("R"):
            return "Device:R"
        if ref.startswith("C"):
            return "Device:C_Polarized" if "uF" in comps[ref]["value"] and \
                not comps[ref]["value"].startswith(".") else "Device:C"
        raise KeyError(ref)

    # Power units and the power sheet. Every multi-unit IC's supply unit goes on
    # the power sheet with the bypass capacitors and the power input.
    placed = {}                      # (ref, unit) -> sheet
    layout = {}
    for key, title, units in SHEETS:
        for ref, unit, x, y in units:
            if ref.endswith("_dummy"):
                continue
            placed[(ref, unit)] = key
            layout[(ref, unit)] = (x, y)
    power_units = []
    for ref in sorted(comps):
        part = comps[ref]["part"]
        if not part:
            continue
        ls = LIB[part]
        units = {unit_of(ls, p) for p in pinout(part)}
        if len(units) > 1:
            pu = max(units)
            pins = [p for p in pinout(part) if unit_of(ls, p) == pu]
            if all(pinout(part)[p][1] == "power_in" for p in pins):
                power_units.append((ref, pu))
    psheet = []
    for i, (ref, unit) in enumerate(power_units):
        x, y = 25 + (i % 9) * 30, 40 + (i // 9) * 32
        psheet.append((ref, unit, x, y))
    # The sheet's bypass list: "C1-8, 10, 12, 15-19, 23, 24, 26".
    bypass = [f"C{n}" for n in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 16, 17, 18, 19, 23, 24, 26)]
    extras = ["C27", "C28", "R37", "CR2", "R45"] + bypass
    for i, ref in enumerate(extras):
        x, y = 20 + (i % 20) * 13, 150 + (i // 20) * 25
        psheet.append((ref, 1, x, y))
    SHEETS[-1] = ("power", SHEETS[-1][1], psheet)
    for ref, unit, x, y in psheet:
        placed[(ref, unit)] = "power"
        layout[(ref, unit)] = (x, y)
    # The rails arrive on passive connector pins, so ERC is told where power
    # enters with a PWR_FLAG on each.
    flags = {"#FLG01": "+5V", "#FLG02": "GND", "#FLG03": "+22V"}

    def sheet_of(pin):
        ref, _, num = pin.rpartition(".")
        part = comps[ref]["part"]
        u = unit_of(LIB[part], num) if part else 1
        s = placed.get((ref, u))
        if s is None:
            raise KeyError(f"{pin}: unit {u} of {ref} is on no sheet")
        return s

    # Every pin of every placed unit must be on a net, flagged nc, or be a
    # pin of a unit the sheet does not draw.
    plans = {key: {"sheet": key, "title": title, "file": f"{key}.kicad_sch", "place": [],
                   "local_nets": {}, "global_pins": [], "power": {}, "nc": []}
             for key, title, _ in SHEETS}
    for key, title, units in SHEETS:
        for ref, unit, x, y in units:
            if ref.endswith("_dummy"):
                continue
            part = comps[ref]["part"]
            plans[key]["place"].append({"lib_id": libsym(ref), "reference": ref, "unit": unit,
                                        "value": comps[ref]["value"] or part, "x": x, "y": y})

    for i, (ref, rail) in enumerate(flags.items()):
        plans["power"]["place"].append({"lib_id": "power:PWR_FLAG", "reference": ref, "unit": 1,
                                        "value": "PWR_FLAG", "x": 120 + i * 20, "y": 175})
    names = {}
    for name, n in nets.items():
        if n["named"] == "auto":
            drivers = [p for p in n["pins"] if comps[p.rpartition(".")[0]]["part"] and
                       pinout(comps[p.rpartition(".")[0]]["part"]).get(p.rpartition(".")[2], ("", ""))[1]
                       not in ("input", "power_in", "passive")]
            first = (drivers or n["pins"])[0]
            ref, _, num = first.rpartition(".")
            names[name] = f"{ref[1:] if ref.startswith('U') else ref}-{num}"
        else:
            names[name] = label_name(name)
    if len(set(names.values())) != len(names):
        dup = [v for v, c in collections.Counter(names.values()).items() if c > 1]
        raise ValueError(f"label names collide: {dup}")

    for name, n in nets.items():
        by_sheet = collections.defaultdict(list)
        for p in n["pins"]:
            ref, _, num = p.rpartition(".")
            by_sheet[sheet_of(p)].append([ref, num])
        lab = names[name]
        for ref, rail in flags.items():
            if rail == name:
                by_sheet["power"].append([ref, "1"])
        for s, pins in by_sheet.items():
            if name in POWER:
                plans[s]["power"][name] = pins
            elif len(by_sheet) == 1:
                plans[s]["local_nets"][lab] = pins
            else:
                plans[s]["global_pins"] += [[lab] + p for p in pins]
    for pin in net["nc"]:
        ref, _, num = pin.rpartition(".")
        part = comps[ref]["part"]
        u = unit_of(LIB[part], num) if part else 1
        if (ref, u) in placed:
            plans[placed[(ref, u)]]["nc"].append([ref, num])
    # Pins of placed units that are on no net and not flagged: refuse.
    on_net = {p for n in nets.values() for p in n["pins"]} | set(net["nc"])
    for (ref, unit), s in placed.items():
        part = comps[ref]["part"]
        if not part:
            continue
        for num in pinout(part):
            if unit_of(LIB[part], num) == unit and f"{ref}.{num}" not in on_net:
                raise ValueError(f"{ref}.{num} is drawn on {s} but on no net")
    return plans, names


def main():
    slug = sys.argv[1]
    plans, names = build_plan(slug)
    out = os.path.join(ROOT, "kicad", slug, "plan")
    os.makedirs(out, exist_ok=True)
    for key, plan in plans.items():
        json.dump(plan, open(os.path.join(out, f"{key}.json"), "w"), indent=1)
        print(f"{key:6} {len(plan['place']):3} units  {len(plan['local_nets']):3} local nets  "
              f"{len(plan['global_pins']):3} global labels  "
              f"{sum(len(v) for v in plan['power'].values()):3} power pins  {len(plan['nc']):3} nc")
    json.dump(names, open(os.path.join(out, "labels.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
