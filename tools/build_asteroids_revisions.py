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
CHIPS = os.path.join(ROOT, "data", "chips")

# Grid geometry. Asteroids uses a larger grid than Pong; pitch is the standard
# DIP spacing since the drawings are not dimensioned. The row alphabet skips
# G, I, O and Q — see AGENTS.md; listing G and Q here put every device below F
# a row too low and made F/H look like a three-position span.
GRID = {"rows": "RPNMLKJHFEDCBA", "col_pitch": 25.4, "row_pitch": 19.05,
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
        "note": "Designators shift one position, but the drawing gives the "
                "alternate for only 28 of the devices read, so the rest are "
                "shown at their -03/-04 positions. 7497 rate multipliers "
                "fitted, per the parts list entry 'Game PCB Assembly (with "
                "7497 Rate Multipliers)'.",
    },
    "asteroids-06": {
        "name": "Asteroids (034986-06)", "designators": "late",
        "memory_key": "-05/-06 (ROMs)",
        "note": "Designators shift one position, but the drawing gives the "
                "alternate for only 28 of the devices read, so the rest are "
                "shown at their -03/-04 positions. Rate multipliers replaced "
                "by 035904/035905 PROMs, per the drawing's '-06 PCB ONLY' "
                "block and the parts list entry 'Game PCB Assembly (with "
                "PROM)'.",
    },
}

def split_designator(desig):
    """'D/E1' -> ('D1', 'D/E1'); 'C1' -> ('C1', None).

    A device drawn across two cells is keyed at the first one, with the
    sheet's own designator kept so build_board.py can place it across both.
    """
    head = desig.rstrip("0123456789")
    col = desig[len(head):]
    if "/" not in head:
        return desig, None
    return head.split("/")[0] + col, desig


def memory_parts(mem):
    """Every part number the substitution table names, in both spellings.

    The sheet reads record the -03 complement inline, so those devices are
    present in the base read for every revision. They are what each revision's
    own complement *replaces*, not something it adds to, and leaving them in
    is how a -04 board map ended up claiming five PROMs the -04 does not have.
    """
    parts = {p for rev in mem.values() if isinstance(rev, dict)
             for p in rev.values()}
    return parts | {"ROM " + p.split("-")[0] for p in parts}


def collect(read):
    """Flatten the per-sheet reads into {primary: {part, alt}}.

    Returns the devices and any collision — two reads landing on one
    designator. A collision is a real disagreement between two regions of the
    drawings, not a tidy-up: silently keeping whichever came last is how a
    board map ends up confidently naming the wrong chip.
    """
    out, clashes = {}, []
    for key, sheet in read.items():
        if not key.startswith("sheet"):
            continue
        for desig, spec in sheet.items():
            base = desig.rstrip("b")          # de-duplicate my own suffixes
            if not spec.get("part"):
                continue
            if base in out and out[base]["part"] != spec["part"]:
                clashes.append(f"{base}: {out[base]['part']} (as "
                               f"{out[base]['desig']}) vs {spec['part']} "
                               f"(as {desig})")
            out[base] = {"part": spec["part"], "alt": spec.get("alt"),
                         "note": spec.get("note", ""), "desig": desig,
                         "section": spec.get("section", "")}
    return out, clashes

def main():
    read = json.load(open(READ))
    devices, clashes = collect(read)
    for c in clashes:
        print(f"  ! two reads on one designator — {c}")
    mem = read["memory_by_revision"]
    mem_parts = memory_parts(mem)

    written = []
    for slug, rev in REVISIONS.items():
        late = rev["designators"] == "late"
        ics, spans, skipped, collisions, origin = {}, {}, 0, [], {}
        for primary, spec in devices.items():
            desig = spec["alt"] if (late and spec.get("alt")) else primary
            # Program memory comes from the substitution table below, not from
            # the sheet read, which records the -03 complement for every board.
            if spec["part"] in mem_parts:
                continue
            cell, span = split_designator(desig or "")
            # only place things that sit on the letter+number grid
            if not (cell and cell[0].isalpha() and cell[1:].isdigit()):
                skipped += 1
                continue
            if cell[0] not in GRID["rows"]:
                skipped += 1
                continue
            if cell in ics and ics[cell] != spec["part"]:
                collisions.append(f"{cell}: {ics[cell]} vs {spec['part']} "
                                  f"(from {primary})")
            ics[cell] = spec["part"]
            origin[cell] = primary
            if span:
                spans[cell] = span

        for loc, part in mem[rev["memory_key"]].items():
            cell, span = split_designator(loc)
            if cell[0] not in GRID["rows"] or not cell[1:].isdigit():
                skipped += 1
                continue
            # The substitution table is typeset and revision-specific, so it
            # wins over a sheet read — but only 28 of the sheet-read devices
            # carry a -05/-06 alternate, so an unshifted read landing here is
            # not evidence of anything. Say which ones were displaced.
            if cell in ics and ics[cell] != part:
                collisions.append(f"{cell}: sheet read {ics[cell]}, "
                                  f"substitution table {part} (as {loc})")
            ics[cell] = part
            if span:
                spans[cell] = span

        spec = {
            "slug": slug, "name": rev["name"], "mfr": "Atari", "year": "1979",
            "revision": rev["note"],
            "drawing": "DP-143 drawing package, sheets 01B and 02A/02B",
            "coverage": (f"{len(ics)} devices read from the drawings. This is a partial "
                         "complement — the sheets have regions not yet read — so it is a "
                         "board map, not a complete bill of materials."),
            "size": SIZE, "grid": GRID, "ics": ics,
        }
        if spans:
            spec["spans"] = spans
        path = os.path.join(OUT, slug + ".json")
        json.dump(spec, open(path, "w"), indent=1)

        # The chip lookup is the same set of devices seen designator-first,
        # and it used to be maintained separately — which is how it came to
        # show the sheet's 'ROM 035131' at J2 while the board map showed the
        # substitution table's '035131-02' for the same position. One source.
        chips = {}
        for cell, part in ics.items():
            src = devices.get(origin.get(cell, cell), {})
            # Memory placed from the substitution table has no sheet entry
            # of its own, so it falls back to the block name rather than
            # inventing a note the drawing does not carry.
            default = "Program memory" if part in mem_parts else ""
            section = src.get("section") or default
            note = src.get("note", "")
            other = None
            if src:
                other = src["alt"] if not late else (
                    origin.get(cell) if origin.get(cell) != cell else None)
            chips[cell] = {"part": part, "section": section, "note": note,
                           "otherRev": other}
        json.dump(chips, open(os.path.join(CHIPS, slug + ".json"), "w"),
                  indent=1)
        for c in collisions:
            print(f"  ! {slug}: {c}")
        written.append((slug, len(ics), skipped, len(spans)))

    for slug, n, sk, sp in written:
        print(f"  {slug:<16} {n:>3} devices placed, {sp} spanning "
              f"({sk} off-grid, not placed)")

if __name__ == "__main__":
    main()
