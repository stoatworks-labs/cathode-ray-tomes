#!/usr/bin/env python3
"""Turn a hand-read netlist (boards/<slug>.nets) into a checked netlist.

The .nets file is what a person reads off the sheet. This file decides nothing
about the circuit; it joins what the reader wrote, adds the power pins the sheet
leaves undrawn, and then argues with the result:

  * every pin must exist on the part, by the part's own pin list -- KiCad's
    symbol library for stock parts, tools/custom_pinouts.json for the rest
  * two driving outputs on one net is a misread, unless both can let go
    (open collector, tri-state, bidirectional)
  * an IC pin the reader neither wired nor marked `nc` is reported, because
    a pin that was simply missed looks exactly like one that is unused
  * pins on one net share a signature, so two different codes printed in the
    same test on one net mean one of the joins is wrong

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
}
# Electrical types that may share a net with another driver.
LETS_GO = {"open_collector", "open_emitter", "tri_state", "bidirectional", "passive"}
DRIVES = {"output", "power_out"} | LETS_GO - {"passive"}

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


def custom_pins(part):
    table = json.load(open(os.path.join(ROOT, "tools", "custom_pinouts.json")))
    entry = table[part]
    return {str(n): (p["name"], p["type"]) for n, p in entry["pins"].items()}


def pinout(part):
    if part in KICAD:
        return kicad_pins(KICAD[part])
    return custom_pins(part)


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
        if kind in ("net", "label"):
            name, _, pins = rest.partition(":")
            out.append((kind, name.strip(), pins.split(), None, n))
        elif kind in ("wire", "nc"):
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
    for kind, name, toks, extra, n in stmts:
        pins = [pin(t) for t in toks]
        seen.update(pins)
        if kind in ("net", "label"):
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
            rail = "GND" if pname.upper() in ("GND", "VSS", "V-") else "+5V"
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
        labels = [names[m] for m in members if m.startswith("#")]
        if not labels and all(p in nc for p in pins):
            continue                                # an unconnected pin is not a net
        sheet = [nm for lst in labels for k, nm in lst if k == "net"]
        ours = [nm for lst in labels for k, nm in lst if k == "label"]
        sheet, ours = list(dict.fromkeys(sheet)), list(dict.fromkeys(ours))
        if sheet:
            name, named_by = sheet[0], "sheet"
        elif ours:
            name, named_by = ours[0], "ours"
        else:
            first = pins[0]
            name, named_by = f"Net-({first.replace('.', '-Pad')})", "auto"
        if name in nets:
            problems.append(f"two separate nets would both be called {name}")
        nets[name] = {"pins": pins, "named": named_by,
                      "aliases": [a for a in sheet + ours if a != name]}
        if len(pins) == 1 and pins[0] not in nc:
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

    # Drivers.
    for name, n in nets.items():
        drivers, hard = [], []
        for p in n["pins"]:
            ref, _, num = p.rpartition(".")
            part = parts.get(ref)
            if part is None:
                continue
            pname, ptype = pinout(part).get(num, ("?", "?"))
            if ptype in DRIVES:
                drivers.append(f"{p} {pname}")
                if ptype not in LETS_GO:
                    hard.append(p)
        if len(hard) > 1 or (hard and len(drivers) > len(hard)):
            problems.append(f"{name}: more than one output drives it -- " + ", ".join(drivers))

    # Undriven nets: inputs only, nothing that could set the level -- no
    # output, no connector, no passive. Usually a join that was missed.
    for name, n in nets.items():
        if name in ("+5V", "GND", "+22V"):
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
    return {
        "slug": slug,
        "source": "boards/%s.nets" % slug,
        "components": components,
        "nets": dict(sorted(nets.items())),
        "signatures": {p: [{"code": c, "test": t} for c, t, _ in v] for p, v in sorted(sigs.items())},
        "nc": sorted(nc),
    }, problems, notes


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
