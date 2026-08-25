#!/usr/bin/env python3
"""Cross-check tools/packages.py against KiCAD, devices.py and the board maps.

Four things are checked, and each one has bitten:

  1. Every `kicad`-provenance pin count is re-derived from KiCAD's own symbol
     library. KiCAD omits no-connect pins, so the comparison is against the
     highest pin *number*, not the pin count — a 7493 symbol has 10 pins and a
     DIP-14 package.
  2. Where devices.py also knows a part, the two must agree. They are separate
     tables on purpose, which is exactly why they can drift.
  3. Every footprint the table can produce must exist in KiCAD's footprint
     library, because build_board.py raises rather than substitutes.
  4. Every part used in boards/*.json must be sized, or be logged as
     unidentified. Anything else is a silent DIP-14.

Runs on plain python3 — it parses the KiCAD libraries as text and does not
import pcbnew.
"""
import json, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from packages import (TTL_PINS, TTL_PINS_UNCHECKED, PART_PINS, ATARI_MEMORY,
                      UNIDENTIFIED, pins_for, package_for, ttl_base)
from devices import DEVICES

SYMLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"
FPLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

# Logic families to try when looking for a symbol for a bare function number.
# The package is the same across all of them; this is only about finding one.
FAMILIES = ["", "LS", "S", "HC", "HCT", "ALS", "AS", "F", "H", "L"]

# Non-74xx parts whose KiCAD symbol is not named the same as the part.
SYMBOL_ALIAS = {
    "555": "LM555xN", "NE555": "LM555xN", "CD4016B": "4016",
    "CD4066": "CD4066BE", "DAC-08": "DAC08", "9316": "74LS161",
    "4016B": "4016", "4066": "CD4066BE", "9312": "74151", "9602": "74LS123", "NE556": "NE556",
}


def _symbols(path):
    """{name: block} for each top-level symbol in a .kicad_sym file."""
    src = open(path, encoding="utf-8", errors="ignore").read()
    out = {}
    for m in re.finditer(r'\n\t\(symbol "([^"]+)"', src):
        i, depth, j = m.start() + 2, 0, m.start() + 2
        while j < len(src):
            if src[j] == "(":
                depth += 1
            elif src[j] == ")":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out[m.group(1)] = src[i:j]
    return out


def load_index():
    """{symbol name: highest pin number}, following (extends ...)."""
    raw = {}
    for fn in sorted(os.listdir(SYMLIB)):
        p = os.path.join(SYMLIB, fn)
        if not fn.endswith(".kicad_sym") or not os.path.isfile(p):
            continue
        for name, blk in _symbols(p).items():
            ext = re.search(r'\(extends\s+"([^"]+)"', blk)
            nums = [int(n) for n in re.findall(r'\(number\s+"(\d+)"', blk)]
            raw[name] = (max(nums) if nums else None,
                         ext.group(1) if ext else None)

    def resolve(name, depth=0):
        e = raw.get(name)
        if e is None:
            return None
        mx, ext = e
        if mx is not None or depth > 4 or not ext:
            return mx
        return resolve(ext, depth + 1)

    return {n: resolve(n) for n in raw}


def max_pin(index, part):
    """Highest pin number on the KiCAD symbol for `part`, or (None, None)."""
    base = ttl_base(part)
    names = []
    if base:
        names += [f"74{f}{base}" for f in FAMILIES]
    names += [SYMBOL_ALIAS.get(part, part), part]
    for n in names:
        if index.get(n):
            return index[n], n
    return None, None


def main():
    index = load_index()
    problems, notes = [], []

    # 1. kicad-provenance entries re-derived from the symbol library
    checked = unchecked = 0
    for base, pins in sorted(TTL_PINS.items()):
        mx, sym = max_pin(index, "74" + base)
        if mx is None:
            problems.append(f"74xx {base}: marked kicad but no symbol found")
            continue
        want = mx + (mx % 2)          # DIP pin counts are even
        if want != pins:
            problems.append(f"74xx {base}: table says {pins}, "
                            f"symbol {sym} implies {want}")
        else:
            checked += 1
    for base, pins in sorted(TTL_PINS_UNCHECKED.items()):
        if max_pin(index, "74" + base)[0]:
            notes.append(f"74xx {base}: KiCAD now ships a symbol — "
                         f"move it into TTL_PINS")
        unchecked += 1

    for part, (pins, src, _) in sorted(PART_PINS.items()):
        if src != "kicad":
            unchecked += 1
            continue
        mx, sym = max_pin(index, part)
        if mx is None:
            problems.append(f"{part}: marked kicad but no symbol found")
        elif mx + (mx % 2) != pins:
            problems.append(f"{part}: table says {pins}, "
                            f"symbol {sym} implies {mx + (mx % 2)}")
        else:
            checked += 1

    # 2. agreement with devices.py where both know a part
    agreed = 0
    for part, spec in sorted(DEVICES.items()):
        pins, _ = pins_for(part)
        if pins is None:
            problems.append(f"{part}: in devices.py but has no packaging entry")
        elif pins != spec["pins"]:
            problems.append(f"{part}: packages.py says {pins}, "
                            f"devices.py says {spec['pins']}")
        else:
            agreed += 1

    # 3. every producible footprint exists
    seen = set()
    for part in list(PART_PINS) + list(ATARI_MEMORY) + \
            ["74" + b for b in list(TTL_PINS) + list(TTL_PINS_UNCHECKED)]:
        lib, name, _ = package_for(part)
        if (lib, name) in seen:
            continue
        seen.add((lib, name))
        if not os.path.isfile(os.path.join(FPLIB, lib + ".pretty",
                                           name + ".kicad_mod")):
            problems.append(f"{part}: footprint {lib}:{name} does not exist")

    # 4. coverage of what the board maps actually use
    used, unsized, unverified = {}, {}, {}
    for f in sorted(glob.glob(os.path.join(ROOT, "boards", "*.json"))):
        b = os.path.basename(f)
        if b.endswith(".read.json") or b.endswith(".notes.json"):
            continue
        for cell, part in json.load(open(f)).get("ics", {}).items():
            used[part] = used.get(part, 0) + 1
    for part, n in used.items():
        pins, src = pins_for(part)
        if pins is None:
            unsized[part] = (n, src)
        elif src == "unverified":
            unverified[part] = n

    print(f"packaging table: {checked} entries re-derived from KiCAD, "
          f"{unchecked} on datasheet/drawing authority")
    print(f"devices.py agreement: {agreed} of {len(DEVICES)} parts")
    print(f"footprints: {len(seen)} distinct, all present"
          if not any("footprint" in p for p in problems) else "")
    print(f"board coverage: {len(used) - len(unsized)} of {len(used)} part "
          f"types sized, covering "
          f"{sum(n for p, n in used.items() if p not in unsized)} of "
          f"{sum(used.values())} devices")

    if unverified:
        print(f"\n  unverified sizes ({sum(unverified.values())} devices) — "
              f"class default, wants confirming against a board:")
        for part, n in sorted(unverified.items(), key=lambda kv: -kv[1]):
            print(f"    {part:<24}{n:>3}")
    if unsized:
        print(f"\n  unsized ({sum(n for n, _ in unsized.values())} devices) — "
              f"drawn as DIP-14 until identified:")
        for part, (n, why) in sorted(unsized.items(), key=lambda kv: -kv[1][0]):
            print(f"    {part:<24}{n:>3}  {why}")
    for n in notes:
        print(f"  note: {n}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nno contradictions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
