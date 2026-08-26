#!/usr/bin/env python3
"""Recover functional blocks from the manuals' prose.

The section names on the hand-read boards come from titles printed on the
drawing sheets, not from prose — Asteroids' technical manual has thirty-five
headings and not one is a theory-of-operation block. But some manuals do carry
a chapter that names a block and the positions it occupies, and those name the
devices the IC parts lists structurally cannot: Atari stocks ROM, RAM and the
MPU under their own part numbers, not as 37-series IC stock, so the harvest
never sees them.

Measured against the boards that already have blocks, the prose agrees on
function 243 times out of 265. That is not good enough to apply unattended —
the failures are this extractor grabbing a designator list belonging to an
adjacent clause, and a wrong chip in a repair reference is worse than a missing
one. So this reports evidence for a person to adjudicate and writes nothing.

The false positives worth knowing about, because all three look exactly like a
grid cell: capacitor and resistor designators in parts lists (C56, R7), the
power-input connector in boilerplate (J3), and, on the driving games, regions
of the television picture ("in zone C4").
"""
import argparse, json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FUNCTION = (r'counter|latch|decoder|multiplex|register|buffer|shift|driver|'
            r'comparator|flip-flop|oscillator|divider|generator|memory|RAM|'
            r'ROM|PROM|MPU|processor|watchdog|clock|sync')
PAIR = re.compile(
    r'(' + FUNCTION + r')\w*\s*(?:circuitry\s*)?'
    r'\((?:at\s+location\s+)?([A-Z](?:/[A-Z])?\d{1,2}'
    r'(?:\s*,?\s*(?:and\s+)?[A-Z](?:/[A-Z])?\d{1,2})*)\)', re.I)
CELL = re.compile(r'[A-Z](?:/[A-Z])?\d{1,2}')
# Context that means the designator is not a grid position.
NOT_A_CELL = re.compile(r'zone|connector|VAC|voltage|capacitor|resistor|ohm|uf\b',
                        re.I)


def body(fid):
    d = json.load(open(os.path.join(ROOT, "cache", "text", fid + ".json")))
    out = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("t"), str):
                out.append(o["t"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(d)
    return re.sub(r'\s+', ' ', " ".join(out))


def first_cell(c):
    head = c.rstrip("0123456789")
    return head.split("/")[0] + c[len(head):] if "/" in head else c


def blocks(fid):
    """[(function, cell, span, context)] for every block the prose names."""
    txt = body(fid)
    out = []
    for m in PAIR.finditer(txt):
        ctx = txt[max(0, m.start() - 70):m.end() + 30]
        if NOT_A_CELL.search(ctx):
            continue
        for raw in CELL.findall(m.group(2)):
            out.append((m.group(1).lower(), first_cell(raw),
                        raw if "/" in raw else None, " ".join(ctx.split())))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.board + ".json")))
    ics, rows = spec["ics"], spec["grid"]["rows"]
    cols = spec["grid"].get("cols")
    mach = spec.get("machine") or next(
        (b.get("machine") for b in json.load(open(os.path.join(ROOT, "data/boards.json")))
         if b["slug"] == a.board), "")

    docs = [d for d in json.load(open(os.path.join(ROOT, "data/index/docs.json")))
            if d.get("machine") == mach and d.get("ingested")]

    found = defaultdict(lambda: {"funcs": set(), "docs": set(), "span": None,
                                 "ctx": ""})
    for d in docs:
        try:
            bl = blocks(d["id"])
        except Exception:
            continue
        for func, cell, span, ctx in bl:
            if cell[0] not in rows or not cell[1:].isdigit():
                continue
            if cols and int(cell[1:]) > cols:
                continue
            e = found[cell]
            e["funcs"].add(func)
            e["docs"].add(d["id"])
            e["span"] = e["span"] or span
            e["ctx"] = e["ctx"] or ctx

    on_map = {c: v for c, v in found.items() if c in ics}
    new = {c: v for c, v in found.items() if c not in ics}
    print(f"{a.board}: {len(docs)} documents, {len(found)} positions named by "
          f"prose — {len(on_map)} already on the map, {len(new)} new\n")
    print("already on the map (check the function against the part):")
    for c, v in sorted(on_map.items()):
        print(f"   {c:<5}{ics[c]:<14}{'/'.join(sorted(v['funcs'])):<22}"
              f"{len(v['docs'])} doc(s)")
    print("\nnot on the map — needs a second source before placing:")
    for c, v in sorted(new.items()):
        span = f" spans {v['span']}" if v["span"] else ""
        print(f"   {c:<5}{'/'.join(sorted(v['funcs'])):<22}{len(v['docs'])} doc(s){span}")
        print(f"        {v['ctx'][:104]}")


if __name__ == "__main__":
    main()
