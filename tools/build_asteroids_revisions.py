#!/usr/bin/env python3
"""Emit one board definition per Asteroids PCB revision.

There is no single "Asteroids board". Atari shipped assemblies 034986-01 thru
-06 and they differ in ways that matter to anyone holding one:

  * reference designators shift by one position from -05 onward, so the same
    chip is C10 on an early board and C11 on a late one
  * the program memory is a different complement in different locations on
    every one of -03, -04 and -05/-06
  * -05 uses 7497 rate multipliers where -06 uses PROMs

Reading the drawings recorded a primary designator and, where the drawing
showed one, the -05/-06 alternate. This turns that single read into separate,
individually correct boards rather than one board that is wrong for everybody.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
READ = os.path.join(ROOT, "boards", "asteroids.read.json")
OUT = os.path.join(ROOT, "boards")

# Grid geometry. Asteroids uses a larger grid than Pong; pitch is the standard
# DIP spacing since the drawings are not dimensioned.
GRID = {"rows": "RQPNMLKJHGFEDCBA", "col_pitch": 25.4, "row_pitch": 19.05,
        "x0": 26.0, "y0": 18.0, "rotation": 90}
SIZE = {"w": 300, "h": 330}

REVISIONS = {
    "asteroids-03": {
        "name": "Asteroids (034986-03)", "designators": "early",
        "memory_key": "-03 (PROMs)",
        "note": "Eleven PROMs. Rate multipliers fitted.",
    },
    "asteroids-04": {
        "name": "Asteroids (034986-04)", "designators": "early",
        "memory_key": "-04 (ROMs)",
        "note": "Three ROMs replace the eleven PROMs. Rate multipliers fitted.",
    },
    "asteroids-05": {
        "name": "Asteroids (034986-05)", "designators": "late",
        "memory_key": "-05/-06 (ROMs)",
        "note": "Designators shift one position. 7497 rate multipliers fitted, "
                "per the parts list entry 'Game PCB Assembly (with 7497 Rate Multipliers)'.",
    },
    "asteroids-06": {
        "name": "Asteroids (034986-06)", "designators": "late",
        "memory_key": "-05/-06 (ROMs)",
        "note": "Designators shift one position. Rate multipliers replaced by "
                "035904/035905 PROMs, per the drawing's '-06 PCB ONLY' block and "
                "the parts list entry 'Game PCB Assembly (with PROM)'.",
    },
}

def collect(read):
    """Flatten the per-sheet reads into {primary: {part, alt}}."""
    out = {}
    for key, sheet in read.items():
        if not key.startswith("sheet"):
            continue
        for desig, spec in sheet.items():
            base = desig.rstrip("b")          # de-duplicate my own suffixes
            if not spec.get("part"):
                continue
            out[base] = {"part": spec["part"], "alt": spec.get("alt"),
                         "note": spec.get("note", "")}
    return out

def main():
    read = json.load(open(READ))
    devices = collect(read)
    mem = read["memory_by_revision"]

    written = []
    for slug, rev in REVISIONS.items():
        late = rev["designators"] == "late"
        ics, skipped = {}, 0
        for primary, spec in devices.items():
            desig = spec["alt"] if (late and spec.get("alt")) else primary
            # only place things that sit on the letter+number grid
            if not (desig and desig[0].isalpha() and desig[1:].isdigit()):
                skipped += 1
                continue
            if desig[0] not in GRID["rows"]:
                skipped += 1
                continue
            ics[desig] = spec["part"]

        for loc, part in mem[rev["memory_key"]].items():
            if loc[0] in GRID["rows"] and loc[1:].isdigit():
                ics[loc] = part

        spec = {
            "slug": slug, "name": rev["name"], "mfr": "Atari", "year": "1979",
            "revision": rev["note"],
            "drawing": "DP-143 drawing package, sheets 01B and 02A/02B",
            "coverage": (f"{len(ics)} devices read from the drawings. This is a partial "
                         "complement — the sheets have regions not yet read — so it is a "
                         "board map, not a complete bill of materials."),
            "size": SIZE, "grid": GRID, "ics": ics,
        }
        path = os.path.join(OUT, slug + ".json")
        json.dump(spec, open(path, "w"), indent=1)
        written.append((slug, len(ics), skipped))

    for slug, n, sk in written:
        print(f"  {slug:<16} {n:>3} devices placed ({sk} off-grid, not placed)")

if __name__ == "__main__":
    main()
