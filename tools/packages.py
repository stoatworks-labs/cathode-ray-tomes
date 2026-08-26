#!/usr/bin/env python3
"""Physical package sizes for the parts that appear on the board maps.

This is deliberately *not* `devices.py`. That file is the electrical constraint
set `validate_nets.py` trusts — every entry in it carries a full pinout and is
cross-checked gate by gate, so it only ever grows as far as a net reading needs.
This file answers a much smaller question — how many pins does the part have, so
the board map can draw the right outline — for every part number that appears in
`boards/*.json`, which is ~110 of them against DEVICES' 20.

Keeping them apart matters in both directions. A packaging entry must never be
mistaken for a verified pinout, and adding a part here must never widen what
`validate_nets.py` believes it can check.

Provenance is recorded per entry because the board maps are a repair reference:

  kicad      pin count read from KiCAD's own symbol library by
             tools/check_packages.py. Note KiCAD omits no-connect pins, so the
             symbol's pin *count* is a lower bound; the highest pin *number*
             is the package size. A 7493 is DIP-14 with four NCs.
  drawing    stated on the sheet and recorded in boards/<slug>.read.json.
  datasheet  standard package for the part, not otherwise verified here.
  unverified best available reading, still wants confirming. Listed by
             tools/check_packages.py so it stays visible.

Nothing in here is load-bearing for connectivity. Getting a package wrong makes
a board map draw an outline of the wrong size; getting devices.py wrong makes
the extractor trust a net that cannot exist.
"""

# --- 74-series ----------------------------------------------------------------
# Keyed by the bare function number, because the logic family prefix does not
# change the package: a 7404, 74LS04, 74S04 and 74H04 are all DIP-14. Every
# entry marked `kicad` was read off the KiCAD symbol for some member of the
# family; check_packages.py re-derives them and fails on a disagreement.
TTL_PINS = {
    "00": 14, "02": 14, "03": 14, "04": 14, "06": 14, "07": 14, "08": 14,
    "10": 14, "125": 14, "166": 16, "195": 16, "399": 16,
    "11": 14, "14": 14, "20": 14, "25": 14, "27": 14, "30": 14, "32": 14,
    "33": 14, "42": 16, "48": 16, "74": 14, "75": 16, "76": 16, "83": 16, "85": 16, "86": 14, "92": 14, "95": 14,
    "96": 16, "123": 16, "156": 16, "192": 16, "241": 20, "279": 16,
    "90": 14, "93": 14,
    "107": 14, "109": 16, "139": 16, "151": 16, "153": 16, "157": 16, "160": 16,
    "161": 16, "163": 16, "164": 14, "170": 16, "174": 16, "175": 16,
    "191": 16, "193": 16, "194": 16, "244": 20, "245": 20, "251": 16, "253": 16,
    "257": 16, "259": 16, "273": 20, "367": 16, "373": 20, "374": 20, "393": 14,
    "670": 16,
}

# KiCAD does not ship these three symbols, so they cannot be re-derived.
# 7450 is corroborated by devices.py, which was built from the TI datasheet.
TTL_PINS_UNCHECKED = {
    "50": 14,    # dual 2-wide 2-input AOI
    "97": 16,    # synchronous 6-bit binary rate multiplier
    "260": 14,   # dual 5-input NOR
}

# --- everything else ----------------------------------------------------------
# (pins, provenance, note)
PART_PINS = {
    # memory
    "2114":       (18, "datasheet", "1024x4 static RAM; Atari 90-7033"),
    "2101A-2":    (22, "datasheet", "256x4 static RAM; 0.4in body"),
    "8316E":      (24, "drawing",
                   "2K x 8 mask ROM; battlezone.read.json records that 2708s "
                   "may be fitted instead, and a 2708 is DIP-24"),
    "8T28":       (16, "datasheet", "quad bus transceiver"),
    "82S123":     (16, "datasheet", "32x8 bipolar PROM"),
    "82S129":     (16, "datasheet", "256x4 bipolar PROM"),
    "83S185":     (18, "datasheet", "2K x 4 bipolar PROM"),

    # processors and custom silicon
    "6502":       (40, "datasheet", "MOS 6502"),
    "6502A":      (40, "datasheet", "MOS 6502A; Atari 90-6013"),
    "137004-001": (40, "drawing",
                   "Atari-marked Am2901 4-bit slice; DIP-40 stated on the "
                   "Battlezone Math Box sheet"),
    "C012294-01": (40, "drawing",
                   "POKEY; DIP-40 stated on the Battlezone Auxiliary sheet"),

    # analogue
    "555":        (8,  "kicad", "timer"),
    "NE555":      (8,  "kicad", "timer"),
    "LM324":      (14, "kicad", "quad op-amp"),
    "TL082":      (8,  "kicad", "dual JFET op-amp"),
    "CD4016B":    (14, "kicad", "quad bilateral switch"),
    "4016B":      (14, "kicad", "quad bilateral switch; the parts lists' "
                                "spelling of the CD4016B"),
    "4584B":      (14, "kicad", "hex Schmitt-trigger inverter; == 40106"),
    "CD4066":     (14, "kicad", "quad bilateral switch"),
    "4066":       (14, "kicad", "quad bilateral switch; the parts lists' "
                                "spelling of the CD4066"),
    "DAC-08":     (16, "kicad", "8-bit multiplying DAC"),
    "AD561J":     (16, "datasheet", "10-bit DAC"),

    "137108-001": (8,  "datasheet",
                   "Atari 137108-001; the Caberat parts list names it TL081CP"),

    # Fairchild's own numbering for parts the 74-series also carries. 9316 is
    # already in devices.py under that name; the other two appear on the
    # mid-70s boards, which predate Atari standardising on 74-series numbers.
    "9316":       (16, "kicad", "synchronous 4-bit counter; == 74161"),
    "9312":       (16, "kicad", "8-input multiplexer; == 74151"),
    "9602":       (16, "kicad", "dual retriggerable monostable; == 74123"),
    "9300":       (16, "datasheet", "4-bit universal shift register"),
    "9301":       (16, "datasheet", "1-of-10 decoder"),
    "9322":       (16, "datasheet", "quad 2-input multiplexer"),
    "9334":       (16, "datasheet", "8-bit addressable latch"),
    "7489":       (16, "datasheet", "64-bit read/write memory"),
    "NE556":      (14, "kicad", "dual timer"),
    "LM723":      (14, "datasheet", "voltage regulator"),
}

# Not ICs, but they are DIP-bodied and sit on the grid, so the board map has to
# draw something. n SPST switches in a DIP is 2n pins.
PART_PINS.update({
    "4-position DIP switch": (8,  "datasheet", "Atari 66-114P1T, 4-station"),
    "8-position DIP switch": (16, "datasheet", "8-station DIP switch"),
})

# Atari mask ROM / PROM part numbers used as the part field on the Asteroids
# board maps. 24 pins is no longer a class default: the manual states it, in
# the same parts list the devices come from. Item 188 is a '79-42C24
# 24-Contact Medium-Insertion-Force Integrated Circuit Socket' fitted at J2,
# H2, E/F2 and N/P3 — the program ROM positions and the vector ROM. The memory
# map agrees arithmetically: 6800-7FFF is 6144 bytes, which is three 2K ROMs
# or twelve 512-byte PROMs and nothing else that tiles evenly.
# tools/check_socket_pins.py re-derives this from the corpus.
ATARI_MEMORY_PINS = 24
ATARI_MEMORY = {
    "035131-02", "035132-02", "035133-02", "035134-02", "035135-02",
    "035136-02", "035137-02", "035138-02", "035139-02", "035140-02",
    "035141-02", "035142-02", "035143-02", "035144-02", "035145-02",
    "035150-02", "035151-02", "035152-02", "035153-02", "035154-02",
    "035155-02",
    # Centipede's ROMs, from MAME's dumps of real boards. 24-pin, confirmed
    # independently by the manual's own 24-contact socket entries at the same
    # six positions.
    "136001-407", "136001-408", "136001-409", "136001-410",
    "136001-211", "136001-212",
    "ROM 035131", "ROM 035132", "ROM 035133", "ROM 035134", "ROM 035135",
}

# Descriptions that were recorded in place of a part number, because the sheet
# did not give one. These are data gaps, not packaging gaps: they should be
# resolved by re-reading, and until then the board map cannot size them.
# Descriptions recorded in place of a part number, because the sheet did not
# give one. These are data gaps, not packaging gaps. Kept as a named list
# rather than deleted: the entries that used to be here — `counter`, `op-amp`
# and `DIP switch` — were all settled from the parts lists rather than by
# re-reading the sheet, which is the route worth trying first.
UNIDENTIFIED = {}

import re

_TTL = re.compile(r'^74([A-Z]*)(\d+)([A-Z]?)$')


def ttl_base(part):
    """'74LS163A' -> '163'. None if the part is not a 74-series number."""
    m = _TTL.match(part)
    return m.group(2) if m else None


def pins_for(part):
    """(pins, provenance) for a part number, or (None, reason) if unsized."""
    if part in UNIDENTIFIED:
        return None, f"unidentified: {UNIDENTIFIED[part]}"
    if part in PART_PINS:
        pins, src, _ = PART_PINS[part]
        return pins, src
    if part in ATARI_MEMORY:
        return ATARI_MEMORY_PINS, "parts list"
    base = ttl_base(part)
    if base in TTL_PINS:
        return TTL_PINS[base], "kicad"
    if base in TTL_PINS_UNCHECKED:
        return TTL_PINS_UNCHECKED[base], "datasheet"
    return None, "no packaging entry"


# Body width is not derivable from the pin count alone. Up to 20 pins the
# era's parts are all 0.3in; from 24 pins they are all 0.6in; 22 is genuinely
# mixed, so the parts that are not 0.3in are named here.
WIDTH_OVERRIDE = {
    "2101A-2": "W10.16mm",   # 0.4in body
}


def dip_width(part, pins):
    if part in WIDTH_OVERRIDE:
        return WIDTH_OVERRIDE[part]
    return "W7.62mm" if pins < 24 else "W15.24mm"


def package_for(part, fallback=14):
    """(footprint_lib, footprint_name, provenance).

    Falls back to DIP-14 so a board with one unreadable part still builds, but
    the caller is expected to surface the provenance: silently drawing every
    unknown part as a 14-pin DIP is the bug this module exists to fix.
    """
    pins, src = pins_for(part)
    if pins is None:
        return "Package_DIP", f"DIP-{fallback}_W7.62mm", src
    return "Package_DIP", f"DIP-{pins}_{dip_width(part, pins)}", src
