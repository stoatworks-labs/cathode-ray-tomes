#!/usr/bin/env python3
"""Check an extracted netlist against what the devices can electrically do.

Pin numbers read off a scan are the unreliable part of extraction. Rather than
trying to recognise the digits better, this rejects readings that produce a
circuit which cannot exist — a 7427 gate with four inputs, an output shorted to
another output, a supply pin carrying a signal. The device pinouts constrain
the answer the way a crossword grid constrains letters.

Input is a JSON netlist:  {"UG2": {"6": "NET", "4": "VBLANK", ...}, ...}
plus a refdes -> part mapping.
"""
import argparse, json, os, sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from devices import DEVICES, pin_role

POWER = {"+5V", "VCC", "5V", "GND", "0V"}

def validate(netlist, parts):
    """Return (errors, warnings). Errors mean the reading cannot be right."""
    errors, warnings = [], []
    drivers = defaultdict(list)       # net -> [(ref, pin)] of outputs driving it

    for ref, pins in netlist.items():
        part = parts.get(ref)
        if part is None:
            warnings.append(f"{ref}: unknown part, not checked")
            continue
        spec = DEVICES.get(part)
        if spec is None:
            warnings.append(f"{ref}: no pinout for {part}, not checked")
            continue

        for pin_s, net in pins.items():
            try:
                pin = int(pin_s)
            except ValueError:
                errors.append(f"{ref}: pin '{pin_s}' is not a number")
                continue

            if not 1 <= pin <= spec["pins"]:
                errors.append(f"{ref} ({part}): pin {pin} outside 1..{spec['pins']}")
                continue

            role = pin_role(part, pin)
            if role is None:
                warnings.append(f"{ref} ({part}): pin {pin} is a no-connect")
                continue

            # Supply pins must carry supply, and vice versa.
            if role == "vcc" and net not in POWER:
                errors.append(f"{ref} ({part}): pin {pin} is VCC but reads '{net}'")
            if role == "gnd" and net not in POWER:
                errors.append(f"{ref} ({part}): pin {pin} is GND but reads '{net}'")
            if role in ("in", "out", "ctrl") and net in POWER:
                # legitimate (tying an unused input high) but worth surfacing
                warnings.append(f"{ref} ({part}): signal pin {pin} tied to {net}")

            if role == "out":
                drivers[net].append((ref, pin))

        # Gate coherence. A pin number can be misread as another pin of the
        # same role — a 7427 output read as 8 instead of 6 is still "an
        # output" — so per-pin checks pass. What gives it away is the gate:
        # one gate ends up driving with nothing feeding it while another has
        # inputs and no output.
        connected = {int(k) for k in pins if k.isdigit()}
        dangling_out, starved_in = [], []
        for gi, g in enumerate(spec["gates"], 1):
            n_in = len(set(g.get("in", [])) & connected)
            n_out = len(set(g.get("out", [])) & connected)
            if n_out and not n_in:
                dangling_out.append(gi)
            if n_in >= 2 and not n_out:
                starved_in.append(gi)
        if dangling_out and starved_in:
            errors.append(
                f"{ref} ({part}): gate {dangling_out[0]} drives with no inputs while "
                f"gate {starved_in[0]} has inputs and no output — output pin likely misread")
        elif dangling_out:
            warnings.append(
                f"{ref} ({part}): gate {dangling_out[0]} output connected but no inputs")

    # Two totem-pole outputs on one net is a short, not a circuit.
    for net, ds in drivers.items():
        if len(ds) > 1 and net not in POWER:
            open_collector = all(DEVICES[parts[r]]["desc"].endswith("(OC)") for r, _ in ds)
            msg = f"net '{net}' driven by {len(ds)} outputs: " + \
                  ", ".join(f"{r}.{p}" for r, p in ds)
            (warnings if open_collector else errors).append(msg)

    # A net reaching only one pin went nowhere — usually a broken trace.
    reach = defaultdict(int)
    for ref, pins in netlist.items():
        for net in pins.values():
            reach[net] += 1
    for net, n in reach.items():
        if n == 1 and net not in POWER:
            warnings.append(f"net '{net}' touches only one pin — likely incomplete")

    return errors, warnings

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("netlist", help="JSON: {ref: {pin: net}}")
    ap.add_argument("--parts", required=True, help="JSON: {ref: part}")
    a = ap.parse_args()

    netlist = json.load(open(a.netlist))
    parts = json.load(open(a.parts))
    errors, warnings = validate(netlist, parts)

    pins = sum(len(v) for v in netlist.values())
    print(f"checked {pins} pin assignments across {len(netlist)} devices")
    for e in errors:
        print(f"  ERROR   {e}")
    for w in warnings:
        print(f"  warn    {w}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
