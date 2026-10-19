#!/usr/bin/env python3
"""Import DICE's netlists of 1970s TTL games as boards on this site.

DICE (the Discrete Integrated Circuit Emulator, github.com/mittonk/dice-libretro)
emulates the games that have no CPU at all by simulating every chip on the
board, so each game is a netlist: CHIP("A1", 7400) and CONNECTION("A1", 3,
"B2", 4), chip by chip, pin by pin, at the board positions Atari's drawings
use. That is connectivity for boards this repository has only placed, and it is
GPL-3.0, as is everything made from it here.

It is an emulator's model of the board, not a drawing of it, and it is read as
one. Per board in data/dice.json:

  - DICE's simplifications are undone where they hide a wire. A CAPACITOR or a
    BUFFER there is an RC delay standing in a net, so both its ends are one net
    on the board; a CLK_GATE is a speed hack between a clock and the pin it
    drives, and is the same wire; a WIRED_AND is open-collector outputs tied.
  - Everything else DICE adds -- VIDEO, AUDIO, the inputs, the power-on LATCH,
    the CLOCK -- is not a part on the board, and stays off the board view.
  - Two 555 halves at one position (B9A, B9B) are a 556, and their pins are
    renumbered to its pinout.
  - Every pin is checked against the part's KiCad symbol where KiCad has one,
    and the supply pins DICE never wires are joined to +5V and GND from it.
  - The signal names come from DICE's own #defines (`#define H1 "H5", 12`).

  python3 tools/import_dice.py --dice <dice-libretro checkout> [slug ...]

Then tools/build_board.py and tools/publish_board.py, as for any board.
"""
import argparse, collections, datetime, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/stoatworks-labs/cathode-ray-tomes"
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_board_nets import kicad_pins, custom_pins  # noqa: E402
from import_jtcores import natural, dump  # noqa: E402
from packages import package_for  # noqa: E402

KICAD_SYMBOLS = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

# DICE types that are a real part at a board position, as the part is named.
TIMERS = {"555_Mono", "555_Astable", "555_PWM", "POT_555_ASTABLE", "POT_555_MONO"}
PART = re.compile(r"^(74[A-Z]*\d+|82S\d+|9[36]\d\d|555|556|566|4016|324|2533|8225|75453|LM380)$")
# Fairchild's 93xx numbers name 74-series parts by another number.
EQUIV = {"9316": "74161", "9310": "74160", "9312": "74151", "9322": "74157",
         "9321": "74139", "9311": "74154", "9301": "7442"}
# DICE's stand-ins for a stretch of wire: every pin listed is one net.
WIRE = {"CAPACITOR": (1, 2), "BUFFER": (1, 2), "CLK_GATE": (2, 3), "CLK_GATE_n": (2, 3),
        "WIRED_AND": tuple(range(1, 11)), "WIRED_OR": tuple(range(1, 11))}
# A 555 half of a 556, renumbered: 555 pin -> 556 pin.
HALF = {"A": {1: 7, 2: 6, 3: 5, 4: 4, 5: 3, 6: 2, 7: 1, 8: 14},
        "B": {1: 7, 2: 8, 3: 9, 4: 10, 5: 11, 6: 12, 7: 13, 8: 14}}

_STR = re.compile(r'"(?:[^"\\]|\\.)*"')


def strip_comments(text):
    out, i, n = [], 0, len(text)
    while i < n:
        if text[i] == '"':
            m = _STR.match(text, i)
            j = m.end() if m else i + 1
            out.append(text[i:j]); i = j
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        else:
            out.append(text[i]); i += 1
    return "".join(out)


def preprocess(path, defines=None, seen=None):
    """The game's source with comments, dead #if blocks and macros resolved.

    Only object-like macros are expanded, and only the ones DICE's games use:
    a signal named for an endpoint (`#define H1 "H5", 12`) or for another.
    Returns (lines, defines-in-order).
    """
    defines = {} if defines is None else defines
    seen = set() if seen is None else seen
    text = strip_comments(open(path, errors="replace").read()).replace("\\\n", " ")
    lines, live = [], [True]
    order = []
    for raw in text.split("\n"):
        line = raw.strip()
        d = re.match(r"#\s*(\w+)\s*(.*)", line)
        if d:
            kw, rest = d.group(1), d.group(2).strip()
            if kw in ("if", "ifdef", "ifndef"):
                if kw == "if":
                    on = rest not in ("0",)
                elif kw == "ifdef":
                    on = rest.split()[0] in defines if rest else False
                else:
                    on = rest.split()[0] not in defines if rest else True
                live.append(live[-1] and on)
            elif kw == "else":
                prev = live.pop()
                live.append(live[-1] and not prev if len(live) else not prev)
            elif kw == "endif":
                if len(live) > 1:
                    live.pop()
            elif not live[-1]:
                continue
            elif kw == "define":
                m = re.match(r"([A-Za-z_]\w*)(\()?\s*(.*)", rest)
                if m and not m.group(2):
                    defines[m.group(1)] = m.group(3).strip()
                    order.append(m.group(1))
            elif kw == "undef":
                defines.pop(rest.split()[0], None)
            elif kw == "include":
                m = re.match(r'"([^"]+)"', rest)
                inc = os.path.normpath(os.path.join(os.path.dirname(path), m.group(1))) if m else None
                if inc and os.path.exists(inc) and inc not in seen and os.path.dirname(inc) == os.path.dirname(path):
                    seen.add(inc)
                    sub, sub_order = preprocess(inc, defines, seen)
                    lines += sub
                    order += sub_order
            continue
        if live[-1]:
            lines.append(expand(line, defines))
    return lines, order


def expand(line, defines, depth=8):
    for _ in range(depth):
        changed = False

        def sub(m):
            nonlocal changed
            tok = m.group(0)
            if tok.startswith('"'):
                return tok
            if tok in defines:
                changed = True
                return defines[tok]
            return tok
        line = re.sub(r'"(?:[^"\\]|\\.)*"|[A-Za-z_]\w*', sub, line)
        if not changed:
            break
    return line


def statements(lines, game):
    """CHIP and CONNECTION statements inside CIRCUIT_LAYOUT( game )."""
    body, inside = [], False
    for line in lines:
        if re.match(rf"(static\s+)?CIRCUIT_LAYOUT\(\s*{re.escape(game)}\s*\)", line):
            inside = True
            continue
        if inside and line.startswith("CIRCUIT_LAYOUT_END"):
            break
        if inside:
            body.append(line)
    text = "\n".join(body)
    out = []
    for m in re.finditer(r"\b(CHIP|CONNECTION|SUB_CIRCUIT)\s*\(", text):
        depth, i = 1, m.end()
        while i < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[i], 0)
            i += 1
        args = text[m.end():i - 1]
        out.append((m.group(1), [a.strip() for a in re.findall(r'"(?:[^"\\]|\\.)*"|[^,]+', args)]))
    return out


def is_position(name):
    """A board position as either convention writes it: a 555 half (B9A), and
    a part spanning two rows, which DICE writes without the slash (DE1 is the
    drawing's D/E1), included."""
    return bool(re.fullmatch(r"[A-Z]{1,2}\d{1,2}[AB]?|\d{1,2}[A-Z][AB]?", name))


def span_of(name, rows):
    """('D', 'E', 1) for DE1 when D and E are neighbouring rows, else None."""
    m = re.fullmatch(r"([A-Z])([A-Z])(\d{1,2})", name)
    if m and m.group(1) in rows and m.group(2) in rows \
            and abs(rows.index(m.group(1)) - rows.index(m.group(2))) == 1:
        return m.group(1), m.group(2), int(m.group(3))
    return None


_SYMS = {}


UNLIKE_LS = {"7450", "7451", "7453", "7454"}


def symbol_for(part):
    """The KiCad symbol with this part's pinout, or None.

    None for the standard-TTL AND-OR-INVERT gates. KiCad's 7454 puts its
    output on pin 6, as the 74LS54 does; DICE's model of the 7454
    (chips/7454.cpp) drives pin 8 and runs TV Basketball on it. Judging DICE
    by that symbol accused it of six wires, so these parts are not checked.
    """
    if part in UNLIKE_LS:
        return None
    if part in _SYMS:
        return _SYMS[part]
    base = EQUIV.get(part, part)
    candidates = []
    m = re.match(r"^74([A-Z]*)(\d+)$", base)
    if m:
        fam, num = m.groups()
        candidates = [f"74xx:74{fam}{num}", f"74xx:74LS{num}", f"74xx:74{num}", f"74xx:74HC{num}"]
    elif part == "555":
        candidates = ["Timer:NE555P"]
    elif part == "556":
        candidates = ["Timer:NE556"]
    elif part == "324":
        candidates = ["Amplifier_Operational:LM324"]
    found = None
    for c in candidates:
        try:
            kicad_pins(c)
            found = c
            break
        except (KeyError, FileNotFoundError):
            continue
    _SYMS[part] = found
    return found


def pins_of(part):
    sym = symbol_for(part)
    if sym:
        return kicad_pins(sym), sym
    try:
        return custom_pins(part), "tools/custom_pinouts.json"
    except KeyError:
        return None, None


def import_board(entry, cfg, dice):
    slug, game = entry["slug"], entry["game"]
    path = os.path.join(dice, "games", game + ".cpp")
    # VCC and GND are the two macros the games take from DICE's own header
    # (circuit_desc.h), which is C++ and not read here.
    lines, _ = preprocess(path, {"VCC": '"_VCC", 1', "GND": '"_GND", 1'})
    stmts = statements(lines, entry.get("layout", game))

    chips, kinds = {}, {}
    for kind, args in stmts:
        if kind == "SUB_CIRCUIT":
            raise RuntimeError(f"{game}: sub-circuits are not handled")
        if kind == "CHIP":
            name = args[0].strip('"')
            kinds[name] = args[1]
    # Real parts, by DICE type; 555 halves at one position become a 556.
    real, alias, helpers = {}, {}, []
    for name, t in kinds.items():
        if (t in TIMERS or PART.match(t)) and not is_position(name):
            # DICE adds a gate here and there to model something the board
            # does another way (CARGASAND); it is not a chip anyone can find.
            helpers.append(f"{name} ({t})")
            continue
        if t in TIMERS or t == "555":
            # B9A is half of a 556 at B9; 12A is a 555 at row A, column 12.
            m = re.fullmatch(r"(.+\d)([AB])", name)
            if m and m.group(1) not in kinds and re.fullmatch(r"[A-Z]{1,2}\d{1,2}", m.group(1)):
                real[m.group(1)] = "556"
                alias[name] = (m.group(1), HALF[m.group(2)])
            else:
                real[name] = "555"
        elif PART.match(t):
            real[name] = {"324": "LM324"}.get(t, t)

    parent = {}

    def find(x):
        while parent.setdefault(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    def node(name, pin):
        if name in alias:
            base, remap = alias[name]
            return (base, remap.get(pin, pin))
        return (name, pin)

    unparsed = 0
    for kind, args in stmts:
        if kind != "CONNECTION":
            continue
        # A name is a string; a pin is a number, or -- on DICE's own parts,
        # the joystick, the video, a diode matrix -- a symbol (Joystick::DOWN,
        # ROW0), which is kept as the pin's label.
        items = []
        for a in args:
            if a.startswith('"'):
                items.append(("name", a.strip('"')))
            elif re.fullmatch(r"\d+", a):
                items.append(("pin", int(a)))
            elif re.fullmatch(r"\w[\w:]*", a):
                items.append(("pin", a))
        pts = [node(items[i][1], items[i + 1][1]) for i in range(0, len(items) - 1, 2)
               if items[i][0] == "name" and items[i + 1][0] == "pin"]
        if len(pts) * 2 != len(items) or len(pts) < 2:
            unparsed += 1
            continue
        for p in pts[1:]:
            union(pts[0], p)
    for name, t in kinds.items():
        for a, b in zip(WIRE.get(t, ()), WIRE.get(t, ())[1:]):
            union((name, a), (name, b))

    # Supply pins DICE never wires, from the part's own pinout; and every pin
    # DICE does wire, checked to exist on the part.
    problems, pinouts = [], {}
    for ref, part in real.items():
        pins, src = pins_of(part)
        pinouts[ref] = (pins, src)
        if not pins:
            continue
        for num, (pname, ptype) in pins.items():
            if ptype == "power_in":
                union((ref, int(num)) if num.isdigit() else (ref, num),
                      ("_GND", 1) if pname.upper() in ("GND", "VSS") else ("+5V", 1))
    nets = collections.defaultdict(list)
    for x in list(parent):
        nets[find(x)].append(x)
    for members in nets.values():
        for ref, pin in members:
            pins = pinouts.get(ref, (None, None))[0]
            if pins and str(pin) not in pins:
                problems.append(f"{ref} pin {pin}: a {real[ref]} has no such pin")

    # Names: DICE's own signal #defines, in the order the source gives them --
    # only those naming an endpoint outright, so the first name a net was
    # given wins.
    defs = {}
    for line in open(path, errors="replace").read().split("\n"):
        m = re.match(r'\s*#\s*define\s+([A-Za-z_]\w*)\s+"([^"]+)"\s*,\s*(\d+)\s*$', strip_comments(line))
        if m:
            defs.setdefault(m.group(1), node(m.group(2), int(m.group(3))))
    by_root = {}
    for sig, pt in defs.items():
        if pt in parent:
            by_root.setdefault(find(pt), []).append(sig)
    netlist = {"slug": slug, "source": f"kicad/{slug}/{game}.cpp (DICE, {cfg['license']})",
               "license": cfg["license"], "components": {}, "nets": {}}
    for ref in sorted(real, key=natural):
        netlist["components"][ref] = {"value": real[ref], "dice": kinds.get(ref) or "555 halves"}
    signals, used = {}, collections.Counter()
    for root, members in nets.items():
        on_board = sorted({f"{r}.{p}" for r, p in members if r in real}, key=natural)
        virtual = sorted({f"{r}.{p}" for r, p in members if r not in real and not r.startswith(("_", "+"))})
        rails = {r for r, _ in members if r in ("_VCC", "_GND", "+5V")}
        if len(on_board) < 1 or (len(on_board) < 2 and not virtual and not rails):
            continue
        if "_GND" in rails:
            name, named = "GND", "sheet"
        elif "+5V" in rails:
            name, named = "+5V", "sheet"
        elif "_VCC" in rails:
            name, named = "VCC", "sheet"
        elif root in by_root:
            name, named = by_root[root][0], "sheet"
        else:
            name, named = f"{on_board[0].replace('.', '-')}", "auto"
        used[name] += 1
        if used[name] > 1:
            name = f"{name}~{used[name]}"
        netlist["nets"][name] = {"pins": on_board, "named": named,
                                 "aliases": by_root.get(root, [])[1:], "dice": virtual}
        if named == "sheet":
            where = collections.Counter(p.split(".")[0] for p in on_board)
            signals[name] = dict(sorted(where.items(), key=lambda kv: natural(kv[0])))
    dump(os.path.join(ROOT, "boards", slug + ".netlist.json"), netlist)
    dump(os.path.join(ROOT, "data", "signals", slug + ".json"), signals)

    fpids = {}
    for ref, part in real.items():
        lib, name, _ = package_for(EQUIV.get(part, part))
        fpids[ref] = f"{lib}:{name}"
    # These are Atari, Ramtek and Midway boards of the Pong era, laid out the
    # way the hand-read Atari boards here are: a row a letter, bottom row A,
    # DIPs on their side at an inch a column and 0.75in a row. DICE writes
    # its positions as the drawings do, so they are the board's own.
    grid = place_grid = None
    transposed = sum(bool(re.fullmatch(r"\d{1,2}[A-Z]", r)) for r in real) > len(real) / 2
    cells = {}
    from designators import parse as parse_desig
    for r in real:
        p = parse_desig(r, transposed)
        if p and len(p[0]) == 1:
            cells[r] = p
    place = {}
    if cells:
        rows = "".join(sorted({p[0] for p in cells.values()}, reverse=True))
        cols = max(p[1] for p in cells.values())
        grid = {"rows": rows, "col_pitch": 25.4, "row_pitch": 19.05, "x0": 26.0, "y0": 18.0,
                "rotation": 90, "cols": cols, "transposed": transposed}
        size = {"w": round(26.0 + cols * 25.4 + 20, 1), "h": round(18.0 + len(rows) * 19.05 + 20, 1)}
        for r in real:
            if r in cells:
                continue
            sp = span_of(r, rows)
            if sp:
                ri = (rows.index(sp[0]) + rows.index(sp[1])) / 2
                place[r] = [round(26.0 + (sp[2] - 1) * 25.4, 2), round(18.0 + ri * 19.05, 2), 90]
            else:
                place[r] = [round(26.0 + len(place) * 25.4, 2), round(size["h"] - 10, 2), 90]
    else:
        size = {"w": 200.0, "h": 200.0}
    clashes = 0

    who = authors(dice, f"games/{game}.cpp")
    machine = json.load(open(os.path.join(ROOT, "web", "data", "machine", entry["machine"] + ".json")))
    pins = sum(len(n["pins"]) for n in netlist["nets"].values())
    virtual = sorted({t for n, t in kinds.items() if n not in real and n not in alias
                      and t not in WIRE and t not in TIMERS and not PART.match(t)
                      and t != "VCD_LOG"})
    cover = (f"{len(real)} ICs and {len(netlist['nets'])} nets over {pins} pins, from DICE's "
             f"netlist of the game. DICE is an emulator: its netlist is the circuit as it "
             f"simulates it, at the board positions the drawings use, and is not a drawing "
             f"of the board. Where it stands an RC delay or a speed hack in a wire, the wire is "
             f"restored; what it models that is not a chip on the board ({', '.join(virtual[:8])}"
             f"{', …' if len(virtual) > 8 else ''}) is left off the board view, and the "
             f"resistors and capacitors are not named at all. Supply pins are joined to +5V "
             f"and GND from each part's pinout. ")
    cover += "The ICs sit at their board positions, on the grid spacing of Atari's boards."
    if problems:
        cover += f" {len(problems)} pin(s) DICE wires do not exist on the part; they are listed below."
    origin = {
        "project": "DICE", "url": f"{cfg['repo']}/blob/{cfg['commit']}/games/{game}.cpp",
        "commit": cfg["commit"], "path": f"games/{game}.cpp", "authors": who,
        "license": cfg["license"], "licenseUrl": f"{REPO}/blob/main/kicad/{slug}/LICENSE.txt",
        "source": f"{REPO}/tree/main/kicad/{slug}",
        "what": ("The netlist is DICE's -- its emulation of this board, chip by chip -- and the "
                 "board view, chip lookup and bill of materials here are made from it."),
        "imported": datetime.date.today().isoformat(),
    }
    spec = {
        "slug": slug, "name": entry["name"], "mfr": machine.get("mfr", ""),
        "year": machine.get("year", ""), "machine": entry["machine"],
        "drawing": f"DICE games/{game}.cpp at {cfg['commit'][:8]}",
        "revision": entry.get("note", ""), "coverage": cover,
        "singleSource": False, "netsTraced": True, "license": cfg["license"], "origin": origin,
        "refPrefix": "", "size": size,
    }
    if entry.get("machines"):
        spec["machines"] = entry["machines"]
    if grid:
        spec["grid"] = grid
    spec["ics"] = {r: real[r] for r in sorted(real, key=natural)}
    if place:
        spec["place"] = {r: place[r] for r in sorted(place, key=natural)}
    spec["footprints"] = {r: fpids[r] for r in sorted(fpids, key=natural)}
    dump(os.path.join(ROOT, "boards", slug + ".json"), spec)

    chips = {}
    for ref in sorted(real, key=natural):
        t = kinds.get(ref)
        note = ""
        if real[ref] == "556":
            note = "DICE models it as two 555 halves; pins renumbered to the 556's"
        elif t and t != real[ref]:
            note = f"DICE type {t}"
        if real[ref] in EQUIV:
            note = (note + "; " if note else "") + f"same pinout as the {EQUIV[real[ref]]}"
        chips[ref] = {"part": real[ref], "section": "", "note": note, "otherRev": None,
                      "source": "DICE netlist"}
    dump(os.path.join(ROOT, "data", "chips", slug + ".json"), chips)

    NOTES.clear()
    conflicts = cross_check(entry, real) + cross_check_nets(entry, netlist) \
        + [f"DICE wires {p}." for p in problems]
    if helpers:
        NOTES.append(f"Parts DICE adds to model the circuit, not on the board: "
                     f"{', '.join(sorted(helpers, key=natural))}.")
    dump(os.path.join(ROOT, "boards", slug + ".read.json"), {
        "notes": [f"Converted from DICE's games/{game}.cpp by tools/import_dice.py. "
                  f"{unparsed} CONNECTION statement(s) could not be read." if unparsed else
                  f"Converted from DICE's games/{game}.cpp by tools/import_dice.py; "
                  f"every CONNECTION statement was read."] + NOTES,
        "conflicts": conflicts})

    dest = os.path.join(ROOT, "kicad", slug)
    os.makedirs(dest, exist_ok=True)
    keep = {f"{slug}.kicad_pcb", f"{slug}.kicad_pro"}
    for f in os.listdir(dest):
        if f not in keep:
            os.remove(os.path.join(dest, f))
    shutil.copyfile(path, os.path.join(dest, game + ".cpp"))
    for inc in re.findall(r'#include\s+"([^"/]+\.h)"', open(path, errors="replace").read()):
        if os.path.exists(os.path.join(dice, "games", inc)):
            shutil.copyfile(os.path.join(dice, "games", inc), os.path.join(dest, inc))
    shutil.copyfile(os.path.join(dice, "LICENSE.txt"), os.path.join(dest, "LICENSE.txt"))
    write_notice(dest, entry, cfg, slug, game, who, origin["url"])
    print(f"{slug}: {len(real)} ICs ({'grid ' + grid['rows'] if grid else 'no grid'}), "
          f"{len(netlist['nets'])} nets, {pins} pins"
          + (f", {len(problems)} pin problem(s)" if problems else "")
          + (f", {unparsed} unread connection(s)" if unparsed else "")
          + (f", {len(conflicts) - len(problems)} disagreement(s) with the board map" if len(conflicts) > len(problems) else "")
          + (f", {len(helpers)} DICE helper(s) left off" if helpers else ""))


NOTES = []


def cross_check(entry, real):
    """Where this machine has a board map read off its drawings, compare.

    Two independent sources for the same board are the strongest check this
    repository has. A disagreement is logged, never settled here: DICE may have
    simplified a chip away, or the map may have misread a part number.
    """
    out = []
    for bslug in entry.get("compare", []):
        spec = json.load(open(os.path.join(ROOT, "boards", bslug + ".json")))

        def norm(p):
            p = re.sub(r"^(\d\d)(LS|S|H|L)(\d+)$", r"\1\3", p.upper().replace("DM", "").replace("SN", ""))
            p = re.sub(r"^74(LS|S|H|L)", "74", p)
            return EQUIV.get(p, p)
        theirs = spec["ics"]
        both = [c for c in theirs if c in real]
        agree = [c for c in both if norm(real[c]) == norm(theirs[c])]
        for cell in sorted(both, key=natural):
            if norm(real[cell]) != norm(theirs[cell]):
                out.append(f"{cell}: DICE has a {real[cell]}, the {spec['name']} board map "
                           f"(read off the drawings) a {theirs[cell]}.")
        absent = sorted((c for c in theirs if c not in real), key=natural)
        if absent:
            out.append(f"The {spec['name']} board map places {', '.join(absent)}, where DICE "
                       f"has no chip.")
        NOTES.append(f"Checked against the {spec['name']} board map: of the {len(theirs)} "
                     f"positions it names, DICE agrees on {len(agree)}"
                     + (f" and disagrees on {len(both) - len(agree)}" if len(both) > len(agree) else "")
                     + f"; DICE names {len(set(real) - set(theirs))} the map does not.")
    return out


def cross_check_nets(entry, netlist):
    """Where nets have been traced by hand here, compare them pin for pin.

    `compare_nets` names a script holding a NETS table of {name: [(ref, pad)]}
    with U-prefixed grid refs (tools/pong_signal_nets.py). It is read as data
    -- the script itself wants pcbnew -- and a traced net agrees when DICE puts
    every one of its pins on one net.
    """
    out = []
    path = entry.get("compare_nets")
    if not path:
        return out
    import ast
    tree = ast.parse(open(os.path.join(ROOT, path)).read())
    nets = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(getattr(t, "id", None) == "NETS" for t in n.targets))
    where = {}
    for name, net in netlist["nets"].items():
        for p in net["pins"]:
            where[p] = name
    joined = agree = named = 0
    for name, pins in nets.items():
        ours = [f"{ref[1:] if ref.startswith('U') else ref}.{pad}" for ref, pad in pins]
        found = {p: where.get(p) for p in ours}
        if any(n is None for n in found.values()):
            out.append(f"Hand-traced {name}: DICE has nothing on "
                       f"{', '.join(p for p, n in found.items() if n is None)}.")
            continue
        if len(ours) > 1:
            joined += 1
            if len(set(found.values())) == 1:
                agree += 1
            else:
                out.append(f"Hand-traced {name} joins {', '.join(ours)}; DICE puts them on "
                           f"{', '.join(sorted(set(found.values())))}.")
        if name in found.values() or any(name in netlist["nets"][n]["aliases"] for n in found.values()):
            named += 1
    NOTES.append(f"Checked against the {len(nets)} nets traced by hand in {path}: of the "
                 f"{joined} that join pins, DICE agrees on {agree}; DICE gives {named} of the "
                 f"{len(nets)} the same signal name.")
    return out


def authors(repo, rel):
    """The DICE Team -- the copyright holder its README names, and whose
    original import the history records as "unknown" -- then whoever else
    committed the game to dice-libretro."""
    r = subprocess.run(["git", "-C", repo, "log", "--format=%an", "--", rel],
                       capture_output=True, text=True, check=True)
    c = collections.Counter(a for a in r.stdout.split("\n") if a and a != "unknown")
    return ["the DICE Team"] + [a for a, _ in c.most_common()]


def write_notice(dest, entry, cfg, slug, game, who, url):
    today = datetime.date.today().isoformat()
    with open(os.path.join(dest, "NOTICE.md"), "w") as f:
        f.write(f"""# {entry['name']}

The connectivity of the {entry['name']}, from the netlist
[DICE]({cfg['repo']}) -- the Discrete Integrated Circuit Emulator -- runs it
from:

    {url}

**Written by** {', '.join(who)} (the people who committed `games/{game}.cpp`
to dice-libretro).

**Licence:** GNU General Public License, version 3 -- see
[LICENSE.txt](LICENSE.txt), which is DICE's own copy. Everything made from this
netlist is published under it.

## What is unchanged

`{game}.cpp` and any header it includes are byte-for-byte copies of DICE's at
commit `{cfg['commit']}`.

## What was added here

On {today}, by `tools/import_dice.py` in this repository:

- `{slug}.kicad_pcb` (and the `{slug}.kicad_pro` KiCad writes beside it) -- a
  board view: the ICs DICE names, at their board positions on a nominal grid,
  with DICE's connections on their pins. DICE's stand-ins for a wire (an RC
  delay, a buffer, a clock gate, a wired-AND) are taken out so the wire is one
  net again; its models of analogue parts, inputs and outputs are left off.
- Elsewhere in the repository, derived from this netlist and under the same
  licence: `boards/{slug}.json`, `boards/{slug}.netlist.json`,
  `boards/{slug}.read.json`, `data/chips/{slug}.json`,
  `data/signals/{slug}.json` and the published copy under `web/boards/{slug}/`.
""")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dice", required=True, help="a dice-libretro checkout, with history")
    ap.add_argument("slugs", nargs="*")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, "data", "dice.json")))
    head = subprocess.run(["git", "-C", a.dice, "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != cfg["commit"]:
        sys.exit(f"{a.dice} is at {head}, but data/dice.json is pinned to {cfg['commit']}")
    for entry in cfg["boards"]:
        if not a.slugs or entry["slug"] in a.slugs:
            import_board(entry, cfg, a.dice)


if __name__ == "__main__":
    main()
