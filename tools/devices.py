#!/usr/bin/env python3
"""Pinouts and gate structure for the TTL devices used on these boards.

This is the constraint set the net extractor is validated against. Pin numbers
on a scanned schematic are ~10px stencilled digits and OCR on them is
unreliable; what makes a candidate reading trustworthy is not better character
recognition but whether the resulting circuit is electrically possible. A 7427
gate is three inputs into one output — a reading that implies anything else is
wrong regardless of how confident the OCR was.

Every entry here is cross-checked against KiCAD's own symbol library by
tools/check_devices.py, so this file is not resting on recall.

  vcc/gnd  power pins
  gates    list of {"in": [...], "out": [...], "ctrl": [...]}
"""

DEVICES = {
    # --- gates, DIP-14, power on 14/7 ---
    "7400": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "quad 2-input NAND", "gates": [
        {"in": [1, 2], "out": [3]}, {"in": [4, 5], "out": [6]},
        {"in": [9, 10], "out": [8]}, {"in": [12, 13], "out": [11]}]},
    "7402": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "quad 2-input NOR", "gates": [
        {"in": [2, 3], "out": [1]}, {"in": [5, 6], "out": [4]},
        {"in": [8, 9], "out": [10]}, {"in": [11, 12], "out": [13]}]},
    "7404": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "hex inverter", "gates": [
        {"in": [1], "out": [2]}, {"in": [3], "out": [4]}, {"in": [5], "out": [6]},
        {"in": [9], "out": [8]}, {"in": [11], "out": [10]}, {"in": [13], "out": [12]}]},
    "7410": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "triple 3-input NAND", "gates": [
        {"in": [1, 2, 13], "out": [12]}, {"in": [3, 4, 5], "out": [6]},
        {"in": [9, 10, 11], "out": [8]}]},
    "7420": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "dual 4-input NAND", "gates": [
        {"in": [1, 2, 4, 5], "out": [6]}, {"in": [9, 10, 12, 13], "out": [8]}]},
    "7425": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "dual 4-input NOR w/ strobe", "gates": [
        {"in": [1, 2, 4, 5], "ctrl": [3], "out": [6]},
        {"in": [9, 10, 12, 13], "ctrl": [11], "out": [8]}]},
    "7427": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "triple 3-input NOR", "gates": [
        {"in": [1, 2, 13], "out": [12]}, {"in": [3, 4, 5], "out": [6]},
        {"in": [9, 10, 11], "out": [8]}]},
    "7430": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "8-input NAND", "gates": [
        {"in": [1, 2, 3, 4, 5, 6, 11, 12], "out": [8]}]},
    "7433": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "quad 2-input NOR buffer (OC)", "gates": [
        {"in": [2, 3], "out": [1]}, {"in": [5, 6], "out": [4]},
        {"in": [8, 9], "out": [10]}, {"in": [11, 12], "out": [13]}]},
    "7450": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "dual 2-wide 2-input AOI", "gates": [
        {"in": [1, 13, 9, 10], "ctrl": [11, 12], "out": [8]},
        {"in": [2, 3, 4, 5], "out": [6]}]},
    "7486": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "quad 2-input XOR", "gates": [
        {"in": [1, 2], "out": [3]}, {"in": [4, 5], "out": [6]},
        {"in": [9, 10], "out": [8]}, {"in": [12, 13], "out": [11]}]},

    # --- flip-flops ---
    "7474": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "dual D flip-flop", "gates": [
        {"in": [2, 3, 4, 1], "out": [5, 6]},
        {"in": [12, 11, 10, 13], "out": [9, 8]}]},
    "74107": {"pins": 14, "vcc": 14, "gnd": 7, "desc": "dual JK flip-flop", "gates": [
        {"in": [1, 4, 12, 13], "out": [3, 2]},
        {"in": [8, 9, 11, 10], "out": [5, 6]}]},

    # --- counters: note the non-standard power pins ---
    "7490": {"pins": 14, "vcc": 5, "gnd": 10, "desc": "decade counter", "gates": [
        {"in": [14, 1, 2, 3, 6, 7], "out": [12, 9, 8, 11]}]},
    "7493": {"pins": 14, "vcc": 5, "gnd": 10, "desc": "4-bit binary counter", "gates": [
        {"in": [14, 1, 2, 3], "out": [12, 9, 8, 11]}]},
    "9316": {"pins": 16, "vcc": 16, "gnd": 8, "desc": "sync 4-bit counter (74161)", "gates": [
        {"in": [1, 2, 3, 4, 5, 6, 7, 9, 10], "out": [11, 12, 13, 14, 15]}]},

    # --- MSI ---
    "7448": {"pins": 16, "vcc": 16, "gnd": 8, "desc": "BCD to 7-segment decoder", "gates": [
        {"in": [7, 1, 2, 6, 3, 5, 4], "out": [13, 12, 11, 10, 9, 15, 14]}]},
    "7483": {"pins": 16, "vcc": 5, "gnd": 12, "desc": "4-bit full adder", "gates": [
        {"in": [10, 8, 3, 1, 11, 7, 4, 16, 13], "out": [9, 6, 2, 15, 14]}]},
    "74153": {"pins": 16, "vcc": 16, "gnd": 8, "desc": "dual 4-to-1 multiplexer", "gates": [
        {"in": [14, 2, 1, 6, 5, 4, 3], "out": [7]},
        {"in": [14, 2, 15, 10, 11, 12, 13], "out": [9]}]},

    # --- analogue ---
    "555": {"pins": 8, "vcc": 8, "gnd": 1, "desc": "timer", "gates": [
        {"in": [2, 4, 5, 6], "out": [3, 7]}]},
}

def signal_pins(part):
    """Every pin that carries a signal (i.e. not a supply pin)."""
    d = DEVICES[part]
    return sorted(set(range(1, d["pins"] + 1)) - {d["vcc"], d["gnd"]})

def pin_role(part, pin):
    """'vcc' | 'gnd' | 'in' | 'out' | 'ctrl' | None."""
    d = DEVICES[part]
    if pin == d["vcc"]:
        return "vcc"
    if pin == d["gnd"]:
        return "gnd"
    for g in d["gates"]:
        if pin in g.get("out", []):
            return "out"
        if pin in g.get("ctrl", []):
            return "ctrl"
        if pin in g.get("in", []):
            return "in"
    return None
