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

What differs from board to board -- which unit sits where on which sheet, the
symbols for its custom parts and connectors, label spellings the generic rule
gets wrong -- is data, in boards/<slug>.sheets.json. This file holds only the
rules.

  tools/plan_board_schematic.py battlezone-math-box         -> kicad/<slug>/plan/*.json
  tools/plan_board_schematic.py tempest-auxiliary --ops     ... and *.ops.json: every
      label, power symbol and no-connect flag as an explicit Konnect call
"""
import json, os, re, sys, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_board_nets import KICAD, pinout   # noqa: E402

# Rails drawn with KiCad power symbols. Any other rail (+22V, -5V) has no
# stock symbol worth trusting and few pins, so it travels by global label like
# any other net.
POWER = ("+5V", "GND")

# Where the power sheet puts things, unless the board's layout says otherwise:
# the multi-unit ICs' supply units in rows across the top, the bypass list and
# power-input parts below them, the PWR_FLAGs along the bottom.
POWER_GRID = {
    "units": {"x0": 25, "dx": 30, "per_row": 9, "y0": 40, "dy": 32},
    "extras": {"x0": 20, "dx": 13, "per_row": 20, "y0": 150, "dy": 25},
    "flags": {"x0": 120, "dx": 20, "y": 175},
}

# Which KiCad unit holds which pins, read from the library so a gate is never
# guessed. Filled lazily.
_units = {}
_project_libs = {}


def unit_of(libsym, pin):
    if libsym not in _units:
        lib, name = libsym.split(":")
        path = _project_libs.get(lib) or os.path.join(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols", lib + ".kicad_sym")
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


def label_name(name, special):
    """Sheet spelling -> KiCad label text."""
    if name in special:
        return special[name]
    if name.startswith("/"):
        name = "~{" + name[1:] + "}"
    return name.replace(" ", "_")


def load_layout(slug):
    """boards/<slug>.sheets.json: the per-board half of the plan."""
    layout = json.load(open(os.path.join(ROOT, "boards", f"{slug}.sheets.json")))
    lib = layout.get("project_lib", slug)
    # A project-library symbol's units are read from the project's own .kicad_sym.
    _project_libs[lib] = os.path.join(ROOT, "kicad", slug, f"{lib}.kicad_sym")
    return layout


def build_plan(slug):
    layout = load_layout(slug)
    LIB = dict(KICAD)
    LIB.update(layout.get("parts", {}))
    refsyms = layout.get("refs", {})
    special = layout.get("label_names", {})
    flags = layout.get("flags", {"#FLG01": "+5V", "#FLG02": "GND"})
    grid = {k: dict(v, **layout.get("power_grid", {}).get(k, {})) for k, v in POWER_GRID.items()}
    SHEETS = [(s["key"], s["title"], [tuple(u) for u in s.get("units", [])])
              for s in layout["sheets"]]
    power_key = next(s["key"] for s in layout["sheets"] if s.get("power"))
    extras = next(s.get("extras", []) for s in layout["sheets"] if s.get("power"))

    net = json.load(open(os.path.join(ROOT, "boards", f"{slug}.netlist.json")))
    comps = net["components"]
    nets = net["nets"]

    def libsym(ref):
        if ref in refsyms:
            return refsyms[ref]
        part = comps[ref]["part"]
        if part:
            return LIB[part]
        if ref.startswith("TP"):
            return "Connector:TestPoint"
        if ref.startswith("R"):
            return "Device:R"
        if ref.startswith("C"):
            return "Device:C_Polarized" if "uF" in comps[ref]["value"] and \
                not comps[ref]["value"].startswith(".") else "Device:C"
        raise KeyError(f"{ref}: no symbol -- name one under 'refs' in boards/{slug}.sheets.json")

    # Power units and the power sheet. Every multi-unit IC's supply unit goes on
    # the power sheet with the bypass capacitors and the power input.
    placed = {}                      # (ref, unit) -> sheet
    where = {}
    for key, title, units in SHEETS:
        for ref, unit, x, y in units:
            if ref.endswith("_dummy"):
                continue
            placed[(ref, unit)] = key
            where[(ref, unit)] = (x, y)
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
    g = grid["units"]
    psheet = []
    for i, (ref, unit) in enumerate(power_units):
        x = g["x0"] + (i % g["per_row"]) * g["dx"]
        y = g["y0"] + (i // g["per_row"]) * g["dy"]
        psheet.append((ref, unit, x, y))
    g = grid["extras"]
    for i, ref in enumerate(extras):
        x = g["x0"] + (i % g["per_row"]) * g["dx"]
        y = g["y0"] + (i // g["per_row"]) * g["dy"]
        psheet.append((ref, 1, x, y))
    SHEETS = [(k, t, psheet if k == power_key else u) for k, t, u in SHEETS]
    for ref, unit, x, y in psheet:
        placed[(ref, unit)] = power_key
        where[(ref, unit)] = (x, y)
    # The rails arrive on passive connector pins, so ERC is told where power
    # enters with a PWR_FLAG on each (`flags` in the layout).

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

    g = grid["flags"]
    for i, (ref, rail) in enumerate(flags.items()):
        plans[power_key]["place"].append({"lib_id": "power:PWR_FLAG", "reference": ref, "unit": 1,
                                          "value": "PWR_FLAG", "x": g["x0"] + i * g["dx"],
                                          "y": g["y"]})
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
            names[name] = label_name(name, special)
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
                by_sheet[power_key].append([ref, "1"])
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
    # Every component in the read must be drawn somewhere, or the schematic
    # silently loses it; a multi-unit IC needs at least one of its units placed.
    drawn = {ref for ref, _ in placed}
    missing = sorted(set(comps) - drawn)
    if missing:
        raise ValueError(f"in the read but on no sheet: {', '.join(missing)}")
    return plans, names


# ---------------------------------------------------------------------------
# Ops: the plan as explicit Konnect calls. Konnect's pin-location queries only
# see the first unit of a multi-unit part placed in a file, so every global
# label, power symbol and no-connect flag is positioned here instead, from the
# library's own pin geometry: a symbol at (X, Y) puts a library pin at
# (px, py) on (X + px, Y - py), and a label there reads away from the body.
# ---------------------------------------------------------------------------
GRID = 1.27
AWAY = {0: 180, 180: 0, 90: 270, 270: 90}    # library pin angle -> label rotation
PIN_AT = re.compile(r'\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\).*?'
                    r'\(number\s+"([^"]+)"', re.S)
_geometry = {}


def snap(v):
    """Konnect snaps a placed symbol to the 1.27 mm grid, to the nearest point."""
    return round(int(v / GRID + 0.5) * GRID, 2)


def pin_geometry(libsym):
    """{(unit, number): (px, py, angle)} for body style 1, unit 0 = every unit."""
    if libsym not in _geometry:
        lib, name = libsym.split(":")
        path = _project_libs.get(lib) or os.path.join(
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols", lib + ".kicad_sym")
        text = open(path).read()
        body = _symbol(text, name)
        ext = re.search(r'\(extends "([^"]+)"\)', body)
        if ext:
            name = ext.group(1)
            body = _symbol(text, name)
        table = {}
        for m in re.finditer(r'\(symbol "' + re.escape(name) + r'_(\d+)_(\d+)"', body):
            if m.group(2) not in ("0", "1"):
                continue                        # De Morgan body: same pins, drawn twice
            for px, py, ang, num in PIN_AT.findall(_block(body, m.start())):
                table[(int(m.group(1)), num)] = (float(px), float(py), int(float(ang)))
        _geometry[libsym] = table
    return _geometry[libsym]


def pin_end(place, num):
    """Where pin `num` of a placed unit lands on the sheet, and which way is out."""
    geo = pin_geometry(place["lib_id"])
    g = geo.get((place["unit"], num)) or geo.get((0, num))
    if g is None:
        raise KeyError(f"{place['reference']} unit {place['unit']} has no pin {num}")
    px, py, ang = g
    x, y = snap(place["x"]), snap(place["y"])
    return round(x + px, 2), round(y - py, 2), AWAY[ang % 360]


def build_ops(plan, slug):
    """The plan for one sheet as the calls that draw it, in order."""
    lib = load_layout(slug).get("project_lib", slug)
    _project_libs[lib] = os.path.join(ROOT, "kicad", slug, f"{lib}.kicad_sym")
    units = {}
    for p in plan["place"]:
        units.setdefault(p["reference"], []).append(p)

    def where(ref, num):
        for p in units[ref]:
            try:
                return pin_end(p, num)
            except KeyError:
                continue
        raise KeyError(f"{ref}.{num} is on no unit placed on {plan['sheet']}")

    local = [{"net": net, "pins": [{"reference": r, "pin_number": n} for r, n in pins]}
             for net, pins in plan["local_nets"].items()]
    power_symbols = []
    for rail, pins in plan["power"].items():
        local.append({"net": rail, "pins": [{"reference": r, "pin_number": n} for r, n in pins]})
        x, y, _ = where(*pins[0])
        power_symbols.append({"net": rail, "x": x, "y": y})
    glob = []
    for net, ref, num in plan["global_pins"]:
        x, y, rot = where(ref, num)
        glob.append({"net": net, "x": x, "y": y, "rotation": rot})
    nc = []
    for ref, num in plan["nc"]:
        x, y, _ = where(ref, num)
        nc.append({"x": x, "y": y, "pin": f"{ref}.{num}"})
    return {"sheet": plan["sheet"], "file": plan["file"], "place": plan["place"],
            "local": local, "global": glob, "power_symbols": power_symbols, "nc": nc}


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
    if "--ops" in sys.argv:
        for key, plan in plans.items():
            json.dump(build_ops(plan, slug), open(os.path.join(out, f"{key}.ops.json"), "w"),
                      indent=1)
        print(f"wrote {len(plans)} ops files")


if __name__ == "__main__":
    main()
