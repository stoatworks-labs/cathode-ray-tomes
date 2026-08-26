#!/usr/bin/env python3
"""Recover Pong's netlist from MAME's netlist model of the board.

`src/mame/atari/nl_pong.cpp` in MAME is a component-level simulation of this
exact board, and it names its devices by the board's own grid positions —
`c9f` is gate f of the chip at C9. It is BSD-3-Clause, copyright Couriersud;
this reads the connectivity out of it and writes nothing back.

Only the unambiguous connections are taken:

  NET_C(a, b, c)     every term is one net, stated outright
  X.Q as an argument the output of X drives this device, and where the device
                     has one input the pin it drives is not in doubt

Multi-input devices are left for the argument-order table this does not have.
Guessing which of a 7400's two inputs an argument feeds would produce a netlist
that looks complete and is wrong in places, which is worse than a short one —
`validate_nets.py` would catch a gate that cannot exist but not an input swap
between two equivalent pins.

Gate letters map to `devices.py`'s gate order, which is the pinout table this
repo already cross-checks against KiCAD, so a gate letter resolves to real pin
numbers rather than an assumption.
"""
import argparse, collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from devices import DEVICES

DEV = re.compile(r'^\s*(TTL_(\d+)\w*|NE555|TTL_9316)\(\s*([A-Za-z0-9_]+)\s*'
                 r'(?:,([^)]*))?\)', re.M)
NETC = re.compile(r'NET_C\(([^)]*)\)')
CELL = re.compile(r'^(?:ic_)?([a-h])([1-9])([a-f])?$', re.I)
GATES = "abcdef"


def parse(path):
    src = open(path, encoding="utf-8", errors="ignore").read()
    devs = {}
    for m in DEV.finditer(src):
        typ, num, name, args = m.group(1), m.group(2), m.group(3), (m.group(4) or "")
        c = CELL.match(name)
        if not c:
            continue
        part = "555" if typ == "NE555" else ("9316" if "9316" in typ else num)
        devs[name.lower()] = {
            "part": part, "cell": (c.group(1) + c.group(2)).upper(),
            "gate": (c.group(3) or "").lower(),
            "args": [a.strip() for a in args.split(",") if a.strip()],
        }
    nets = [[t.strip() for t in m.group(1).split(",") if t.strip()]
            for m in NETC.finditer(src)]
    return devs, nets


def pins(dev):
    """(input pins, output pins) for this device's gate, from devices.py."""
    spec = DEVICES.get(dev["part"])
    if not spec or not spec.get("gates"):
        return [], []
    gs = spec["gates"]
    i = GATES.index(dev["gate"]) if dev["gate"] in GATES else 0
    if i >= len(gs):
        return [], []
    return gs[i].get("in", []), gs[i].get("out", [])


def terminal(devs, token):
    """'c9c.Q' -> ('UC9', '<output pin>'), or None if it is not a device pin."""
    if "." not in token:
        return None
    name, port = token.rsplit(".", 1)
    d = devs.get(name.lower())
    if not d:
        return None
    ins, outs = pins(d)
    if port.upper() in ("Q", "QQ") and outs:
        return ("U" + d["cell"], str(outs[0] if port.upper() == "Q" else outs[-1]))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist")
    ap.add_argument("--out")
    a = ap.parse_args()

    devs, netc = parse(a.netlist)

    # union-find over everything a NET_C ties together
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry: parent[rx] = ry

    for group in netc:
        for t in group[1:]:
            union(group[0], t)

    # a single-input device driven by X.Q: that output and this input are one net
    driven = []
    for name, d in devs.items():
        ins, _ = pins(d)
        if len(ins) != 1 or len(d["args"]) != 1:
            continue
        src = terminal(devs, d["args"][0])
        if src:
            driven.append((src, ("U" + d["cell"], str(ins[0]))))

    nets = collections.defaultdict(set)
    for group in netc:
        root = find(group[0])
        for t in group:
            term = terminal(devs, t)
            if term:
                nets[root].add(term)
    for i, (src, dst) in enumerate(driven):
        nets[f"drv{i}"].update({src, dst})

    real = {k: sorted(v) for k, v in nets.items() if len(v) >= 2}
    print(f"{len(devs)} devices on the grid, {len(netc)} NET_C groups")
    print(f"{len(driven)} single-input connections resolved unambiguously")
    print(f"{len(real)} nets with two or more device pins")
    pinc = sum(len(v) for v in real.values())
    print(f"{pinc} pin connections in total")
    if a.out:
        json.dump({f"MAME_{i}": v for i, v in enumerate(sorted(real.values()))},
                  open(a.out, "w"), indent=1)
        print(f"-> {a.out}")


if __name__ == "__main__":
    main()
