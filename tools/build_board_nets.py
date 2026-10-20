#!/usr/bin/env python3
"""Turn a hand-read netlist (boards/<slug>.nets) into a checked netlist.

The .nets file is what a person reads off the sheet. This file decides nothing
about the circuit; it joins what the reader wrote, adds the power pins the sheet
leaves undrawn, and then argues with the result:

  * every pin must exist on the part, by the part's own pin list -- KiCad's
    symbol library for stock parts, tools/custom_pinouts.json for the rest
  * two driving outputs on one net is a misread, unless both can let go
    (open collector, tri-state, bidirectional) -- or the sheet ties them on
    purpose, which the read must declare with `parallel PIN PIN ...` (Tempest's
    K3 is four LM324 sections driving one charge pump)
  * an IC pin the reader neither wired nor marked `nc` is reported, because
    a pin that was simply missed looks exactly like one that is unused
  * pins on one net share a signature, so two different codes printed in the
    same test on one net mean one of the joins is wrong

A `port NAME: PIN ...` is a net that leaves what the file describes without a
connector pin to land on -- a netlist converted from MAME names the signal its
CPU or the other board drives, not the contact it arrives on. It is exempt
from the one-pin and nothing-drives-it checks, because what drives it is
somewhere else; a hand read has a connector and should not need one.

  tools/build_board_nets.py battlezone-math-box            # check and write JSON
  tools/build_board_nets.py battlezone-math-box --check    # check only

Writes boards/<slug>.netlist.json, which the schematic build reads.
"""
import argparse, collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KICAD_SYMBOLS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

# Part as the board map names it -> KiCad library symbol with the same pinout.
# The S and plain-TTL parts share their LS sibling's pinout; the 74HC164 is the
# only 164 KiCad ships and its pinout is the 74LS164's.
KICAD = {
    "74LS00": "74xx:74LS00", "74LS02": "74xx:74LS02", "74LS04": "74xx:74LS04",
    "74S03": "74xx:74LS03", "74S08": "74xx:74LS08", "74S86": "74xx:74LS86",
    "74LS20": "74xx:74LS20", "74LS32": "74xx:74LS32", "74LS74": "74xx:74LS74",
    "74109": "74xx:74LS109", "74LS139": "74xx:74LS139", "74LS161": "74xx:74LS161",
    "74LS164": "74xx:74HC164", "74LS273": "74xx:74LS273", "74LS374": "74xx:74LS374",
    "CD4066": "4xxx:4066", "LM324": "Amplifier_Operational:LM324",
    "555": "Timer:NE555P",
    "74LS10": "74xx:74LS10", "74LS14": "74xx:74LS14", "74LS157": "74xx:74LS157",
    "74LS174": "74xx:74LS174", "74LS175": "74xx:74LS175", "74LS191": "74xx:74LS191",
    "74LS244": "74xx:74LS244", "74LS08": "74xx:74LS08", "74LS86": "74xx:74LS86",
    "74S04": "74xx:74LS04",
    # The 4584 is the 40106's pinout: six Schmitt inverters, 14 VDD, 7 VSS.
    "4584B": "4xxx:40106",
    # Parts the MAME conversions use (tools/mame_netlist.py), by the name the
    # netlist gives them. Plain TTL and LS share a pinout; the 9316 is the
    # 74161, the 9322 the 74157 and the 9321 the 74139, pin for pin; the 74S113
    # is the 74LS113. The 74LS92's QB is pin 11 and QD pin 8, as TI's sheet has
    # it -- MAME's own 7492 model swaps them.
    "7400": "74xx:74LS00", "7402": "74xx:74LS02", "7404": "74xx:74LS04", "74H04": "74xx:74LS04",
    "7406": "74xx:74LS06", "7407": "74xx:74LS07", "7408": "74xx:74LS08",
    "7410": "74xx:74LS10", "7414": "74xx:74LS14", "7420": "74xx:74LS20",
    "7427": "74xx:74LS27", "7474": "74xx:74LS74", "7486": "74xx:74LS86",
    "7492": "74xx:74LS92", "7493": "74xx:74LS93", "74107": "74xx:74LS107",
    "74153": "74xx:74LS153", "74165": "74xx:74LS165", "74193": "74xx:74HC193",
    "9316": "74xx:74LS161", "9321": "74xx:74LS139", "9322": "74xx:74LS157",
    "74LS21": "74xx:74LS21", "74LS107": "74xx:74LS107", "74LS125": "74xx:74LS125",
    "74LS75": "74xx:74LS75", "74LS123": "74xx:74LS123", "74LS259": "74xx:74LS259",
    "74LS163": "74xx:74LS163", "74LS377": "74xx:74LS377", "74LS393": "74xx:74LS393",
    "74S113": "74xx:74LS113", "74S113A": "74xx:74LS113",
    "74S20": "74xx:74LS20", "74H08": "74xx:74LS08",
    "TL081": "Amplifier_Operational:TL081", "TL082": "Amplifier_Operational:TL082",
    "TL084": "Amplifier_Operational:TL084", "CA3080": "Amplifier_Operational:CA3080",
    "CA3080A": "Amplifier_Operational:CA3080",
    "LM741": "Amplifier_Operational:LM741", "UA741": "Amplifier_Operational:LM741",
    "LM555": "Timer:NE555P", "NE555": "Timer:NE555P", "NE556": "Timer:NE556",
    "LM556": "Timer:NE556", "CD4011": "4xxx:4011", "CD4017": "4xxx:4017",
    "CD4024": "4xxx_IEEE:4024", "CD4053": "4xxx:4053", "CD4069": "4xxx:4069",
    # The second batch of MAME conversions. The 7428 is pinned as the 7402
    # (KiCad's 74LS28); the 7416 is the 7406's open-collector pinout at 15V;
    # the LM2902 is the LM324's; the MC14584B is the 4584.
    "74164": "74xx:74HC164", "7428": "74xx:74LS28", "7432": "74xx:74LS32",
    "7416": "74xx:74LS06", "74123": "74xx:74LS123", "CD4016": "4xxx:4016",
    "CD4070": "4xxx:4070", "LM2902": "Amplifier_Operational:LM2902",
    "LM358": "Amplifier_Operational:LM358", "MC14584B": "4xxx:40106",
    "CD4030": "4xxx:4070",          # the older quad XOR, the 4070's pinout
    # Dribbling's: plain-TTL names MAME's models use, and the quad comparator.
    "74161": "74xx:74LS161", "74393": "74xx:74LS393", "LM339": "Comparator:LM339",
}
# Electrical types that may share a net with another driver.
LETS_GO = {"open_collector", "open_emitter", "tri_state", "bidirectional", "passive"}
DRIVES = {"output", "power_out"} | LETS_GO - {"passive"}

def is_rail(name):
    """A supply net: GND, or a voltage as the sheet prints one (+5V, -12V, +22V)."""
    return name == "GND" or re.fullmatch(r"[+-]\d+(\.\d+)?V", name) is not None


PIN_RE = re.compile(r"\(pin\s+(\w+)\s+\w+.*?\(name\s+\"([^\"]*)\".*?\(number\s+\"([^\"]+)\"", re.S)


def _block(text, start):
    """The balanced s-expression starting at text[start] == '('."""
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    raise ValueError("unbalanced s-expression")


_libs = {}


def kicad_pins(libsym):
    """{number: (name, type)} for a KiCad library symbol, following `extends`."""
    lib, name = libsym.split(":")
    if lib not in _libs:
        _libs[lib] = open(os.path.join(KICAD_SYMBOLS, lib + ".kicad_sym")).read()
    text = _libs[lib]
    i = text.find(f'(symbol "{name}"')
    if i < 0:
        raise KeyError(libsym)
    body = _block(text, i)
    ext = re.search(r'\(extends\s+"([^"]+)"\)', body)
    if ext:
        return kicad_pins(f"{lib}:{ext.group(1)}")
    pins = {}
    for m in PIN_RE.finditer(body):
        pins[m.group(3)] = (m.group(2), m.group(1))
    return pins


def custom_entry(part):
    """A custom pinout, following `same_as` for a second source's name."""
    table = json.load(open(os.path.join(ROOT, "tools", "custom_pinouts.json")))
    entry = table[part]
    while "same_as" in entry:
        entry = table[entry["same_as"]]
    return entry


def custom_pins(part):
    return {str(n): (p["name"], p["type"]) for n, p in custom_entry(part)["pins"].items()}


def pinout(part):
    if part in KICAD:
        return kicad_pins(KICAD[part])
    return custom_pins(part)


def supply_rail(part, num, pname):
    """The net an undrawn supply pin belongs on. A custom pinout may say so
    outright (`rail`) -- on a PMOS part like the ER2055, VSS is the *positive*
    supply, and going by the name would ground it."""
    if part not in KICAD:
        rail = custom_entry(part)["pins"][num].get("rail")
        if rail:
            return rail
    return "GND" if pname.upper() in ("GND", "VSS", "V-") else "+5V"


# ---------------------------------------------------------------------------
# The .nets file
# ---------------------------------------------------------------------------

def parse(path):
    """Statements in file order: (kind, name, [pins], extra, lineno)."""
    out = []
    for n, raw in enumerate(open(path), 1):
        line = raw.split("#", 1)[0].strip() if not raw.lstrip().startswith("#") else ""
        if not line:
            continue
        kind, _, rest = line.partition(" ")
        if kind in ("net", "label", "port"):
            name, _, pins = rest.partition(":")
            out.append((kind, name.strip(), pins.split(), None, n))
        elif kind in ("wire", "nc", "parallel"):
            out.append((kind, None, rest.split(), None, n))
        elif kind == "sig":
            parts = rest.split()
            test = parts[2] if len(parts) > 2 else "1"
            out.append((kind, None, [parts[0]], (parts[1], test), n))
        elif kind == "value":
            ref, _, val = rest.partition(" ")
            out.append((kind, ref, [], val.strip(), n))
        else:
            raise SyntaxError(f"{path}:{n}: unknown statement '{kind}'")
    return out


class Union:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, a, b):
        self.parent[self.find(a)] = self.find(b)


def build(slug):
    board = json.load(open(os.path.join(ROOT, "boards", f"{slug}.json")))
    spans = {v: k for k, v in board.get("spans", {}).items()}   # "H/J2" -> "H2"
    ics = board["ics"]

    def kref(ref):
        """Designator as written -> KiCad reference."""
        if ref.startswith("U"):
            cell = spans.get(ref[1:], ref[1:])
            if cell not in ics:
                raise KeyError(f"{ref}: no IC at grid position {cell}")
            return "U" + cell
        return ref

    def pin(tok):
        ref, _, num = tok.rpartition(".")
        return f"{kref(ref)}.{num}"

    stmts = parse(os.path.join(ROOT, "boards", f"{slug}.nets"))
    u = Union()
    names = collections.defaultdict(list)       # root pin -> [(kind, name)]
    sigs = collections.defaultdict(list)        # pin -> [(code, test, line)]
    values, nc, seen = {}, set(), set()
    parallel = []                               # [pins] the sheet ties together on purpose
    for kind, name, toks, extra, n in stmts:
        pins = [pin(t) for t in toks]
        if kind == "parallel":
            parallel.append(pins)               # declares; the wire itself joins them
            continue
        seen.update(pins)
        if kind in ("net", "label", "port"):
            for p in pins:
                u.join(p, f"#{name}")
            names[f"#{name}"].append((kind, name))
        elif kind == "wire":
            for a, b in zip(pins, pins[1:]):
                u.join(a, b)
        elif kind == "nc":
            nc.update(pins)
        elif kind == "sig":
            sigs[pins[0]].append((extra[0], extra[1], n))
        elif kind == "value":
            values[name] = extra

    # Parts: ICs from the board map, everything else from its designator.
    parts = {}
    for p in seen:
        ref = p.rpartition(".")[0]
        if ref.startswith("U"):
            parts[ref] = ics[ref[1:]]
        else:
            parts[ref] = None

    # Power pins the sheet does not draw.
    problems, notes = [], []
    for ref, part in parts.items():
        if part is None:
            continue
        for num, (pname, ptype) in pinout(part).items():
            if ptype != "power_in":
                continue
            p = f"{ref}.{num}"
            if p in seen:
                continue
            rail = supply_rail(part, num, pname)
            u.join(p, f"#{rail}")
            seen.add(p)
            notes.append(f"{p} ({pname}) joined to {rail}: power pin not drawn")

    # Collect nets.
    groups = collections.defaultdict(set)
    for p in list(seen) + [k for k in names]:
        groups[u.find(p)].add(p)
    nets = {}
    for members in groups.values():
        pins = sorted(m for m in members if not m.startswith("#"))
        # In file order, so that where the sheet prints two names on one net the
        # first one the read declares names it -- every run, not by hash order.
        labels = [names[m] for m in names if m in members]
        if not labels and all(p in nc for p in pins):
            continue                                # an unconnected pin is not a net
        sheet = [nm for lst in labels for k, nm in lst if k == "net"]
        ours = [nm for lst in labels for k, nm in lst if k == "label"]
        port = [nm for lst in labels for k, nm in lst if k == "port"]
        sheet, ours, port = (list(dict.fromkeys(x)) for x in (sheet, ours, port))
        if sheet:
            name, named_by = sheet[0], "sheet"
        elif port:
            name, named_by = port[0], "port"
        elif ours:
            name, named_by = ours[0], "ours"
        else:
            first = pins[0]
            name, named_by = f"Net-({first.replace('.', '-Pad')})", "auto"
        if name in nets:
            problems.append(f"two separate nets would both be called {name}")
        nets[name] = {"pins": pins, "named": named_by,
                      "aliases": [a for a in sheet + port + ours if a != name]}
        if port:
            nets[name]["port"] = True
        if len(pins) == 1 and pins[0] not in nc and not port and not is_rail(name):
            problems.append(f"{name}: only one pin ({pins[0]}) -- a wire that goes nowhere")

    # Pin existence and coverage.
    net_of = {p: name for name, n in nets.items() for p in n["pins"]}
    for ref, part in sorted(parts.items()):
        if part is None:
            continue
        table = pinout(part)
        used = {p.rpartition(".")[2] for p in seen if p.rpartition(".")[0] == ref}
        for num in sorted(used - set(table), key=lambda x: int(x) if x.isdigit() else 0):
            problems.append(f"{ref} ({part}) has no pin {num}")
        missing = [num for num in table if f"{ref}.{num}" not in seen]
        if missing:
            problems.append(f"{ref} ({part}): pins never mentioned -- " + ", ".join(
                f"{n} {table[n][0]}" for n in sorted(missing, key=lambda x: int(x) if x.isdigit() else 0)))

    # Drivers. Outputs a `parallel` statement declares -- the sections of one
    # package the sheet draws tied together to share a load -- count as one
    # driver, but only if the read really did put them all on one net.
    group_of = {}
    for i, pins in enumerate(parallel):
        if len({net_of.get(p) for p in pins}) != 1 or None in {net_of.get(p) for p in pins}:
            problems.append("parallel " + " ".join(pins) + ": not all on one net")
        for p in pins:
            group_of[p] = i
    for name, n in nets.items():
        drivers, hard, soft = [], set(), 0
        for p in n["pins"]:
            ref, _, num = p.rpartition(".")
            part = parts.get(ref)
            if part is None:
                continue
            pname, ptype = pinout(part).get(num, ("?", "?"))
            if ptype in DRIVES:
                drivers.append(f"{p} {pname}")
                if ptype in LETS_GO:
                    soft += 1
                else:
                    hard.add(group_of.get(p, p))
        if len(hard) > 1 or (hard and soft):
            problems.append(f"{name}: more than one output drives it -- " + ", ".join(drivers))

    # Undriven nets: inputs only, nothing that could set the level -- no
    # output, no connector, no passive. Usually a join that was missed.
    for name, n in nets.items():
        if is_rail(name) or n.get("port"):
            continue
        types = []
        for p in n["pins"]:
            ref, _, num = p.rpartition(".")
            part = parts.get(ref)
            types.append(pinout(part).get(num, ("?", "?"))[1] if part else "passive")
        if types and all(t == "input" for t in types):
            problems.append(f"{name}: nothing drives it -- " + ", ".join(n["pins"]))

    # Signatures.
    for name, n in nets.items():
        by_test = collections.defaultdict(set)
        for p in n["pins"]:
            for code, test, line in sigs.get(p, []):
                by_test[test].add((code, p))
        for test, codes in by_test.items():
            if len({c for c, _ in codes}) > 1:
                problems.append(f"{name}: Test #{test} signatures disagree -- " +
                                ", ".join(f"{p} {c}" for c, p in sorted(codes)))

    components = {}
    for ref, part in sorted(parts.items()):
        components[ref] = {"part": part or "", "value": values.get(ref, part or "")}
    for ref in values:
        if ref not in components:
            problems.append(f"value given for {ref}, which is on no net")
    out = {
        "slug": slug,
        "source": "boards/%s.nets" % slug,
        "components": components,
        "nets": dict(sorted(nets.items())),
        "signatures": {p: [{"code": c, "test": t} for c, t, _ in v] for p, v in sorted(sigs.items())},
        "nc": sorted(nc),
    }
    if parallel:
        out["parallel"] = parallel
    return out, problems, notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--check", action="store_true", help="report only, write nothing")
    ap.add_argument("-v", "--verbose", action="store_true", help="also list undrawn power pins")
    args = ap.parse_args()
    data, problems, notes = build(args.slug)
    if args.verbose:
        for n in notes:
            print("  note:", n)
    for p in problems:
        print("  !", p)
    ncomp = len(data["components"])
    npins = sum(len(n["pins"]) for n in data["nets"].values())
    print(f"{args.slug}: {ncomp} components, {len(data['nets'])} nets, {npins} pin connections, "
          f"{len(problems)} problem(s)")
    if not args.check:
        out = os.path.join(ROOT, "boards", f"{args.slug}.netlist.json")
        json.dump(data, open(out, "w"), indent=1)
        print("wrote", os.path.relpath(out, ROOT))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
