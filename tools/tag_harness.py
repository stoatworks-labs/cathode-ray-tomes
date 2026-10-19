#!/usr/bin/env python3
"""Tag MAME drivers with the cabinet harness their boards plug into.

The wiring view on a machine page is generated, not read: it takes a connector
standard from data/wiring/library.json and places the game's own controls on
it. What this tool decides is which standard, and it decides it per *driver
source file*, because that is the unit MAME documents hardware in and the unit
data/mame/machines.json records for every romset on the site.

Two kinds of evidence, and the page says which one a game got:

  platform  a driver reviewed by hand, whose standard is stated by MAME
            itself: a pin table in the driver comments (cps2.cpp, cps3.cpp,
            neogeo.cpp, shaolins.cpp), or a JVS I/O board instantiated in the
            machine config (naomi.cpp, chihiro.cpp, hikaru.cpp) -- code, not a
            comment, so the strongest evidence there is.
  comment   any other driver whose comments describe its board as having a
            JAMMA edge ("1x JAMMA edge connector", a PCB layout with JAMMA
            drawn at the edge, "Pinout = JAMMA"), with no line in the same
            file saying something is *not* JAMMA. Mixed files are left out
            unless REVIEWED says otherwise.

Every tag carries the line it rests on, with its number in the 0.289 source,
so the page can quote it and link to it. The MAME source tree itself is not
committed (it is 275 MB); what is committed is the extract:

  data/wiring/drivers.json   {"version", "drivers": {src: {std, basis, file,
                              line, text}}, "rejected": {src: reason}}

  git clone --depth 1 --branch mame0289 --filter=blob:none --sparse \\
      https://github.com/mamedev/mame.git /tmp/mame
  git -C /tmp/mame sparse-checkout set src/mame
  python3 tools/tag_harness.py /tmp/mame/src/mame [--candidates]

--candidates prints the comment-level drivers with their evidence instead of
writing, which is how REVIEWED was filled in.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "wiring", "drivers.json")
MAME = os.path.join(ROOT, "data", "mame", "machines.json")

# driver -> (standard, file the evidence is in, pattern for the evidence line)
PLATFORMS = {
    "capcom/cps2.cpp":   ("cps2", "capcom/cps2.cpp", r"JAMMA Connector\s+Extra Button Connector"),
    "capcom/cps3.cpp":   ("cps3", "capcom/cps3.cpp", r"JAMMA Connector\s+Extra Button Connector"),
    # cps1.cpp has no pin table of its own; Ken Sei Mogura is a CPS-1 board
    # with a mole cabinet bolted on, and its driver draws the CPS-1 edge.
    "capcom/cps1.cpp":   ("cps1", "capcom/kenseim.cpp", r"Jamma \(on CPS board\)"),
    "snk/neogeo.cpp":    ("mvs", "snk/neogeo.cpp", r"MVS\s+JAMMA"),
    "sega/naomi.cpp":    ("jvs", "sega/naomi.cpp", r"SEGA_837_13551\(config"),
    "sega/chihiro.cpp":  ("jvs", "sega/chihiro.cpp", r"SEGA_837_13551\(config"),
    "sega/hikaru.cpp":   ("jvs", "sega/hikaru.cpp", r"SEGA_837_13551\(config"),
    "konami/shaolins.cpp": ("konami18", "konami/shaolins.cpp", r"standard Konami pinout"),
}

# A line that says the board's own edge is JAMMA.
POS = re.compile(
    r"jamma\s*(edge|connector|harness|pinout|pcb|board|standard|compatible|i/o|interface|\(56p\))"
    r"|(standard|main|1x|2x28|28x2)\s+jamma"
    r"|pinout\s*[=:]\s*jamma"
    r"|^\W*\|.*\bjamma\b.*\|"            # JAMMA drawn at the edge of a PCB layout
    r"|-+\s*jamma\s*-+", re.I)
# A line that says something in this file is not.
NEG = re.compile(
    r"non[- ]?jamma|not\s+(a\s+)?(standard\s+)?jamma|isn'?t\s+jamma|no\s+jamma|pseudo[- ]?jamma"
    r"|jamma[- ]?(like|ish|style|esque)|similar\s+to\s+jamma|modified\s+jamma|almost\s+jamma"
    r"|jamma\s+backwards|non-?standard|maybe\s+not\s+jamma|pre-?jamma|mahjong\s+pinout", re.I)

# Comment-level drivers read by hand. "accept" keeps a file the patterns would
# drop (a negative line about some other board in it); anything else is the
# reason it is left out, and is published so the omission is visible.
REVIEWED = {
    "namco/namcops2.cpp": "System 246/256 games mostly reach the cabinet through Namco JVS I/O boards; the JAMMA PCB at line 352 is one variant",
    "namco/namcos10.cpp": "the only JAMMA line (1112) is a TODO about tracing the I/O, not a description of the board",
    "pacman/pacman.cpp": "the JAMMA line (4405) is about one bootleg board, not the hardware the driver is for",
    "itech/itech32.cpp": "one of its boards has its JAMMA edge reversed (line 253)",
    "konami/viper.cpp": "its analog controls connect to JAMMA pins (line 280), so a standard placement would be wrong for the driving games",
    "namco/namcona1.cpp": "quiz games on this hardware reassign the JAMMA button pins (line 74)",
    "snk/hng64.cpp": "only one of its I/O boards has a JAMMA edge (line 242)",
    "konami/kpython.cpp": "the board's JAMMA edge is marked not used (line 155)",
    "konami/hornet.cpp": "the only JAMMA line is a register comment",
    "konami/zr107.cpp": "the only JAMMA line is a DIP switch comment",
    "konami/plygonet.cpp": "the only JAMMA line is a DIP switch comment about network IDs",
    "taito/superqix.cpp": "the board's edge is reversed relative to a standard JAMMA harness (line 57)",
    "misc/artmagic.cpp": "the JAMMA edge is described as not connected (line 1043)",
    "pce/paranoia.cpp": "the JAMMA lines describe emulation work, not the board",
    "pce/tourvis.cpp": "the JAMMA line is an emulation TODO, not a description of the board",
    "taito/cchance.cpp": "the driver says its pinout is likely non-JAMMA (line 11)",
    "misc/plsonic4.cpp": "a switcher that JAMMA boards plug into, not a game board",
    "atari/atetris.cpp": "the board does not take its power from the JAMMA edge (line 1008)",
    "sega/system16.cpp": "the JAMMA line (2980) is about a single bootleg board",
    "toaplan/sunwise.cpp": "only the S951060-VGP board is said to have a standard JAMMA connector (line 629)",
    "success/kurukuru.cpp": "the edge drawn at line 124 is a medal-game assignment, not JAMMA's",
    "igs/pgm.cpp": "its only description of a JAMMA connector (line 184) is the cable linking a second cabinet for players 3 and 4",
}

# How well a line describes the board's own edge, for choosing which line to
# quote: an explicit connector or pinout beats a layout drawing beats a mention.
RANK = [
    re.compile(r"jamma\s*(edge\s*)?connector|edge connector|pinout|standard jamma|jamma \(56p\)|jamma pcb|jamma interface", re.I),
    re.compile(r"^\W*\|.*\bjamma\b.*\||-+\s*jamma\s*-+|jamma harness", re.I),
]
CODE = re.compile(r"^\s*(GAME|PORT_|ROM_|map\(|m_|void |if |//|/\*)")
HEDGED = re.compile(r"unknown|maybe|probably|likely|not sure|\?", re.I)


def best(pos):
    """The evidence line to quote: the highest-ranked plain statement.

    Code and inline code comments come last, and so does a line that hedges:
    "It's unknown if the controls are connected through the JAMMA harness"
    mentions the harness but is no evidence for it.
    """
    order = sorted(pos, key=lambda it: (bool(CODE.match(it[1])), bool(HEDGED.search(it[1]))))
    for rx in RANK:
        for i, t in order:
            if rx.search(t) and not HEDGED.search(t) and not CODE.match(t):
                return i, t
    return order[0]


def scan(path):
    pos, neg = [], []
    for i, line in enumerate(open(path, encoding="latin-1"), 1):
        if "jamma" not in line.lower():
            continue
        text = " ".join(line.strip().split())
        if NEG.search(line):
            neg.append((i, text))
        elif POS.search(line):
            pos.append((i, text))
    return pos, neg


def find(path, pattern):
    rx = re.compile(pattern)
    for i, line in enumerate(open(path, encoding="latin-1"), 1):
        if rx.search(line):
            return i, " ".join(line.strip().split())
    raise SystemExit(f"evidence pattern {pattern!r} not found in {path}")


def main():
    src_root = sys.argv[1]
    mame = json.load(open(MAME))
    used = {}
    for rom, rec in mame["machines"].items():
        if rec.get("src"):
            used[rec["src"]] = used.get(rec["src"], 0) + 1

    drivers, rejected, candidates = {}, {}, []
    for src, (std, efile, pattern) in PLATFORMS.items():
        line, text = find(os.path.join(src_root, efile), pattern)
        drivers[src] = {"std": std, "basis": "platform", "file": efile, "line": line, "text": text}

    for src in sorted(used):
        if src in drivers:
            continue
        path = os.path.join(src_root, src)
        if not os.path.exists(path):
            continue
        pos, neg = scan(path)
        verdict = REVIEWED.get(src)
        if not pos:
            continue
        candidates.append((used[src], src, pos, neg, verdict))
        if verdict and verdict != "accept":
            rejected[src] = verdict
            continue
        if neg and verdict != "accept":
            rejected[src] = (f"mixed: line {neg[0][0]} says \"{neg[0][1][:120]}\"")
            continue
        line, text = best(pos)
        drivers[src] = {"std": "jamma", "basis": "comment", "file": src, "line": line, "text": text[:200]}

    if "--candidates" in sys.argv:
        for n, src, pos, neg, verdict in sorted(candidates, key=lambda c: -c[0]):
            print(f"{n:4d} {src}  [{verdict or ('MIXED' if neg else 'auto')}]")
            for i, t in pos[:3]:
                print(f"       + {i}: {t[:150]}")
            for i, t in neg[:3]:
                print(f"       - {i}: {t[:150]}")
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"version": mame.get("version"), "drivers": drivers, "rejected": rejected},
                  f, indent=1, sort_keys=True)
        f.write("\n")
    plat = sum(1 for d in drivers.values() if d["basis"] == "platform")
    print(f"{len(drivers)} drivers tagged ({plat} by platform, {len(drivers) - plat} by comment), "
          f"{len(rejected)} left out -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
