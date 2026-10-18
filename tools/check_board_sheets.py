#!/usr/bin/env python3
"""Check some sheets of a board's KiCad schematic against the read, before the rest exist.

check_board_schematic.py proves the finished schematic; this proves one sheet as soon as
it is drawn, so whoever drew it can fix it while the mistake is still theirs. Only pins on
the named sheets are judged: every read net's pins there must be one KiCad net, and that
net must hold no other drawn pin from a different read net. Other sheets may be half
drawn -- by someone else, at the same moment -- and are ignored.

  tools/check_board_sheets.py tempest-auxiliary alu
  tools/check_board_sheets.py tempest-auxiliary seq alu ctl
"""
import collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from check_board_schematic import kicad_nets  # noqa: E402


def main():
    slug, keys = sys.argv[1], sys.argv[2:]
    if not keys:
        sys.exit("name one or more sheet keys (the plan/<key>.json files)")
    plan_dir = os.path.join(ROOT, "kicad", slug, "plan")
    read = json.load(open(os.path.join(ROOT, "boards", f"{slug}.netlist.json")))
    drawn = set()
    for k in keys:
        plan = json.load(open(os.path.join(plan_dir, f"{k}.json")))
        pins = [p for ps in plan["local_nets"].values() for p in ps]
        pins += [(r, n) for _, r, n in plan["global_pins"]]
        pins += [p for ps in plan["power"].values() for p in ps]
        drawn |= {f"{r}.{n}" for r, n in pins if not r.startswith("#")}
    kn = kicad_nets(os.path.join(ROOT, "kicad", slug, f"{slug}.kicad_sch"))
    where = {p: n for n, ps in kn.items() for p in ps}
    read_of = {p: n for n, v in read["nets"].items() for p in v["pins"]}
    bad = 0
    for name, v in read["nets"].items():
        pins = [p for p in v["pins"] if p in drawn]
        if not pins:
            continue
        homes = collections.Counter(where.get(p, "<missing>") for p in pins)
        if len(homes) != 1 or "<missing>" in homes:
            print(f"  ! {name}: {dict(homes)}")
            bad += 1
            continue
        home = next(iter(homes))
        foreign = [p for p in kn[home] if p in drawn and read_of.get(p) != name]
        if foreign:
            print(f"  ! {name}: KiCad net {home} also holds {foreign}")
            bad += 1
    print(f"{', '.join(keys)}: {len(drawn)} pins drawn, {bad} disagreement(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
