#!/usr/bin/env python3
"""Convert a MAME netlist (src/mame/*/nl_*.cpp) into boards/<slug>.nets.

MAME's netlist files are circuit descriptions written for a simulator, by people
reading the same schematics this repository reads. Most of them name real
designators and DIP pin numbers -- NET_C(VCC, IC_A7.14), CAP(C2, CAP_U(0.1)) --
so the connectivity is a machine-readable second reading of the sheet. What
they are not is a description of the board: to run in real time they swap
circuits for behavioural stand-ins, tie unused inputs to rails, scale values by
tuning constants and comment out what does not simulate. This converts the
connectivity and undoes that, and every undo is written into the .nets file it
produces, so the result can be argued with like any other read:

  * #if switches are re-evaluated with every HLE_*, *FRONTIER*, *HACK* and
    similar option off, so the real circuit is taken where MAME keeps both
  * virtual sources (TTL_INPUT, CLOCK, SWITCH, noise generators, AFUNC) are not
    parts: the nets they drove become `port`s -- the signal arrives from
    somewhere the netlist does not describe
  * a value multiplied by a named constant is written unscaled
  * MAME's "unused" ties become `nc` -- unless the circuit uses the pin -- and
    parts parked with both ends on a rail are listed as on the board, not here
  * a noise source MAME puts in series with a zener (its model of the zener's
    own noise) is a wire: on the board the zener and its load are one node
  * per-target entries in tools/mame_targets.py drop or rewrite specific lines,
    restore circuitry MAME commented out, correct what a sheet shows MAME got
    wrong, and split a netlist that spans two boards (Tank)

How MAME writes a netlist is read the way MAME reads it: a sub-netlist pulled
in with INCLUDE is spliced in where it is included, function-like #defines are
expanded, and a part's named pins (a 7486's A.Q, a CD4006's D1P4) are numbered
by the DIPPINS table of MAME's own DIP model for it, read from MAME's library
at the same tag. One op-amp or timer of a multi-section package, declared on
its own (LM3900(H5_3)), is put on its package's pins by the data sheet's
section numbering (SECTION_PINS); the target says which declarations are
sections. Every IC supply pin is checked against the rail it lands on, so a
part MAME powers backwards fails rather than converting.

Only files whose header says CC0-1.0 or BSD-3-Clause are converted. The source
is fetched from MAME's GitHub at a fixed tag into cache/mame/<tag>/, never the
whole repository.

  tools/mame_netlist.py --list                 targets and their licences
  tools/mame_netlist.py barrier-sound          write boards/barrier-sound.nets
  tools/mame_netlist.py tank                   write tank-board-1 and tank-board-2
  tools/mame_netlist.py barrier-sound --check  convert, write nothing, report

Then check it like any hand read: tools/build_board_nets.py <slug>.
"""
import argparse, collections, json, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_board_nets as checker                          # noqa: E402
from mame_targets import TARGETS                            # noqa: E402

TAG = "mame0289"
COMMIT = "f34f02505e32c1993c6a782b6814232cbfc74e36"         # what the tag points at
RAW = "https://raw.githubusercontent.com/mamedev/mame/" + TAG + "/"
CACHE = os.path.join(ROOT, "cache", "mame", TAG)
LICENCES = {"CC0-1.0", "BSD-3-Clause"}

# ---------------------------------------------------------------------------
# What MAME's build switches mean. Anything matching is set as shown, whatever
# the file defaults it to; a switch nothing here names keeps its default and is
# reported, so a new kind of hack cannot pass silently.
# ---------------------------------------------------------------------------
SWITCHES = [
    (r"REMOVE_POST_CRASH_NOISE_GLITCHES", 0, "a voltage limiter MAME adds on an op-amp output"),
    (r"CONVERGENCE_FRONTIERS", 0, "solver partitioning, with resistor values adjusted to suit"),
    (r"HLE_\w+|\w+_HLE_\w+", 0, "high-level stand-in for a real circuit"),
    (r"\w*FRONTIERS?\w*", 0, "solver partitioning only"),
    (r"HACK_\w+|\w+_HACK", 0, "simulation hack"),
    (r"USE_SPEED_HACKS", 0, "simulation hack"),
    (r"UNDERCLOCK_\w+", 0, "a part run slower than the board runs it"),
    (r"ADD_CLIPPING_DIODES", 0, "diodes standing in for the chip's own input clamps"),
    (r"REMOVE_\w+", 0, "parts removed for speed"),
    (r"ADD_\w+_PULLUPS", 0, "pull-ups the board does not have"),
    (r"DISABLE_\w+", 0, "a connection disabled for speed"),
    (r"SIMPLIFY_\w+|USE_SIMPLIFIED_\w+", 0, "a circuit simplified for speed"),
    (r"SPLIT_SHARED_OSCILLATORS", 0, "one oscillator split in two for speed"),
    (r"USE_AFUNC_MIXING", 0, "behavioural mixer"),
    (r"FAST_\w+", 0, "a speed option"),
    (r"SLOW_BUT_ACCURATE", 1, "the accurate option"),
]

# Supplies MAME feeds from ANALOG_INPUT. Anything else an ANALOG_INPUT carries
# (a 2.2V reference, a DAC level) is a stand-in, and becomes a port. A 0V input
# is ground only when its name says so (XGND, I_V0): MAME also feeds a sound
# chip's output in at 0V and drives it at run time (Rally-X's I_AUDIO).
RAIL_VOLTS = {5, 12, 15, 16, -5, -12, -15, 6, 9, 18, 24}
GROUND_NAME = re.compile(r"\w*(GND|VSS|V0)\w*")

# Named pins of non-DIP devices, as the DIP-8 package numbers them.
NAMED_PINS = {
    "OPAMP": {"MINUS": "2", "PLUS": "3", "GND": "4", "OUT": "6", "VCC": "7"},
    "NE555": {"GND": "1", "TRIG": "2", "OUT": "3", "RESET": "4", "CONT": "5",
              "THRESH": "6", "DISCH": "7", "VCC": "8"},
}
# One section of a multi-section package, declared as a device of its own:
# its pins on the package, by the data sheet's numbering of the sections. A
# target names which declarations are sections (`sections`).
_555 = ("GND", "TRIG", "OUT", "RESET", "CONT", "THRESH", "DISCH", "VCC")
SECTION_PINS = {
    # National LM3900 connection diagram (tools/custom_pinouts.json): amplifier
    # n is nIN+, nIN-, nOUT; all four share V+ (14) and GND (7).
    "LM3900": {s: dict(zip(("PLUS", "MINUS", "OUT", "VCC", "GND"), p)) for s, p in {
        "1": ("1", "6", "5", "14", "7"), "2": ("2", "3", "4", "14", "7"),
        "3": ("13", "8", "9", "14", "7"), "4": ("12", "11", "10", "14", "7")}.items()},
    # NE556 (KiCad Timer:NE556, TI's sheet): timer 1 on pins 1-6, timer 2 on
    # 8-13, GND 7 and VCC 14 shared.
    "NE556": {"1": dict(zip(_555, ("7", "6", "5", "4", "3", "2", "1", "14"))),
              "2": dict(zip(_555, ("7", "8", "9", "10", "11", "12", "13", "14")))},
}
# MAME's library, whose DIP models number each part's named pins (DIPPINS).
LIBRARY = ["src/lib/netlist/macro/nlm_cd4xxx_lib.cpp", "src/lib/netlist/macro/nlm_opamp_lib.cpp",
           "src/lib/netlist/macro/nlm_ttl74xx_lib.cpp", "src/lib/netlist/macro/nlm_otheric_lib.cpp",
           "src/lib/netlist/macro/modules/nlmod_ne556_dip.cpp"]
NOISE_SOURCES = {"SYS_NOISE_MT_N", "SYS_NOISE_MT_U"}
# A comment on a part's declaration that says what the schematic, parts list or a
# real board has, or doubts it ("PCB verified", "Guess", "Schematic says 47K").
VALUE_NOTE = re.compile(r"schem|parts? list|verif|FIXME|guess|assum|error|actually", re.I)
DIODE_PINS = {"K": "1", "A": "2"}       # the DSL: diode pin 1 is the cathode
# Outputs that are currents, not voltages: an OTA's output is summed with
# others on one node by design, which the checker must be told (`parallel`).
CURRENT_OUT = {"CA3080": {"6"}}

VIRTUAL = {"ANALOG_INPUT", "TTL_INPUT", "LOGIC_INPUT", "CLOCK", "VARCLOCK",
           "MAINCLOCK", "EXTCLOCK", "SYS_NOISE_MT_N", "SYS_NOISE_MT_U", "SWITCH",
           "SWITCH2", "SYS_DSW", "NC_PIN", "AFUNC", "VCVS", "VCCS", "CCCS", "VS",
           "CS", "R2R_DAC", "SYS_PULSE", "NOISE"}
IGNORED = {"SOLVER", "PARAM", "DEFPARAM", "OPTIMIZE_FRONTIER", "NET_MODEL",
           "LOCAL_SOURCE", "LOCAL_LIB_ENTRY", "INCLUDE", "NET_REGISTER_DEV",
           "NETLIST_START", "NETLIST_END", "DIPPINS"}

# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch(path):
    """MAME source at TAG, cached under cache/mame/<tag>/."""
    local = os.path.join(CACHE, path)
    if not os.path.isfile(local):
        os.makedirs(os.path.dirname(local), exist_ok=True)
        req = urllib.request.Request(RAW + path, headers={"User-Agent": "cathode-ray-tomes"})
        with urllib.request.urlopen(req) as r:
            open(local, "wb").write(r.read())
    return open(local, encoding="utf-8", errors="replace").read()


def licence(text):
    m = re.search(r"//\s*license:\s*(\S+)", text[:400])
    c = re.search(r"//\s*copyright-holders:\s*(.+)", text[:400])
    return (m.group(1) if m else "?"), (c.group(1).strip() if c else "?")


_library = None


def dippins(text):
    """{model: {pin name: number}} for every NETLIST_START(model) in a file
    that has a DIPPINS table. DIPPINS lists pins 1, N, 2, N-1, ... -- the
    two sides of the package as drawn -- so a model also says which number
    each name is on the package (ALIAS(1, ...) does the same for SIL parts)."""
    code = "\n".join(c for _, c, _ in split_comments(text))
    out = {}
    for m in re.finditer(r"NETLIST_START\(\s*(\w+)\s*\)\s*\{(.*?)\n\}", code, re.S):
        body, table = m.group(2), {}
        d = re.search(r"DIPPINS\((.*?)\)", body, re.S)
        if d:
            pins = [p.strip() for p in d.group(1).split(",") if p.strip()]
            n = len(pins)
            for i in range(n // 2):
                table.setdefault(pins[2 * i], str(i + 1))
                table.setdefault(pins[2 * i + 1], str(n - i))
        for num, name in re.findall(r"ALIAS\(\s*(\d+)\s*,\s*([\w.]+)\s*\)", body):
            table.setdefault(name, num)
        if table:
            out[m.group(1)] = table
    return out


def library():
    """MAME's DIP models: {model: {pin name: number}}."""
    global _library
    if _library is None:
        _library = {}
        for path in LIBRARY:
            _library.update(dippins(fetch(path)))
    return _library


def library_pin(macro, pin):
    """The package pin MAME's own DIP model gives a named pin of `macro`:
    TTL_7486_DIP's A.Q is 3, and CD4006's D1P4 is CD4006_DIP's A.D1P4, 13."""
    model = macro if re.search(r"_(DIP\d*|SIL)$", macro) else macro + "_DIP"
    table = library().get(model, {})
    for name in (pin, "A." + pin):
        if name in table:
            return table[name]
    return None


# ---------------------------------------------------------------------------
# Preprocessing: comments, #define, #if
# ---------------------------------------------------------------------------

def split_comments(text, restore=()):
    """[(lineno, code, comment)] with // and /* */ comments separated out.
    Lines inside a `restore` range have their block-comment text kept as code:
    that is MAME's commented-out circuitry being brought back."""
    out, in_block = [], False
    for n, line in enumerate(text.split("\n"), 1):
        keep = any(a <= n <= b for a, b in restore)
        code, comment, i = "", "", 0
        while i < len(line):
            if in_block:
                j = line.find("*/", i)
                seg = line[i:] if j < 0 else line[i:j]
                if keep:
                    code += seg
                else:
                    comment += seg
                if j < 0:
                    i = len(line)
                else:
                    in_block, i = False, j + 2
            elif line.startswith("/*", i):
                in_block, i = True, i + 2
            elif line.startswith("//", i):
                comment += line[i + 2:]
                i = len(line)
            elif line[i] == '"':
                j = line.find('"', i + 1)
                j = len(line) if j < 0 else j + 1
                code += line[i:j]
                i = j
            else:
                code += line[i]
                i += 1
        out.append((n, code.rstrip(), comment.strip()))
    return out


def switch_value(name, default):
    for pat, val, why in SWITCHES:
        if re.fullmatch(pat, name):
            return val, why
    return default, None


def c_eval(expr, defines):
    """Evaluate a #if expression."""
    e = re.sub(r"defined\s*\(\s*(\w+)\s*\)", lambda m: "1" if m.group(1) in defines else "0", expr)
    e = re.sub(r"defined\s+(\w+)", lambda m: "1" if m.group(1) in defines else "0", e)
    for _ in range(5):                       # defines may name other defines
        e = re.sub(r"\b[A-Za-z_]\w*\b", lambda m: str(defines.get(m.group(0), 0))
                   if m.group(0) not in ("and", "or", "not") else m.group(0), e)
    e = e.replace("&&", " and ").replace("||", " or ")
    e = re.sub(r"!(?!=)", " not ", e)
    return eval(e, {"__builtins__": {}}, {})


def preprocess(lines, preset, log):
    """Active (lineno, code, comment) lines, with #if evaluated. `preset` are
    defines the target fixes before the file sees them; switches the file
    defines are forced to their real-circuit value as SWITCHES says."""
    defines = dict(preset)
    funcs = {}
    stack = []                                # [(active, taken_already, parent_active)]
    out = []
    active = True
    lines = iter(lines)
    for n, code, comment in lines:
        s = code.strip()
        while s.startswith("#") and s.endswith("\\"):    # a directive continued
            s = s[:-1] + " " + next(lines)[1].strip()
        if s.startswith("#"):
            d = s[1:].strip()
            word, _, rest = d.partition(" ")
            rest = rest.strip()
            if word in ("if", "ifdef", "ifndef"):
                if word == "ifdef":
                    cond = rest in defines
                elif word == "ifndef":
                    cond = rest not in defines
                else:
                    cond = bool(c_eval(rest, defines)) if active else False
                stack.append((active, cond, active))
                if active:
                    log.append(("if", n, f"#{word} {rest}", cond))
                active = active and cond
            elif word == "elif":
                parent, taken, _ = stack[-1]
                cond = (not taken) and parent and bool(c_eval(rest, defines))
                stack[-1] = (parent, taken or cond, parent)
                active = parent and cond
                if parent:
                    log.append(("if", n, f"#elif {rest}", cond))
            elif word == "else":
                parent, taken, _ = stack[-1]
                active = parent and not taken
                stack[-1] = (parent, True, parent)
            elif word == "endif":
                active = stack.pop()[0]
            elif not active:
                pass
            elif word == "define":
                m = re.match(r"(\w+)\(([^)]*)\)\s*(.*)", rest)
                if m:
                    funcs[m.group(1)] = ([p.strip() for p in m.group(2).split(",")], m.group(3))
                    continue
                name, _, val = rest.partition(" ")
                val = val.strip() or "1"
                if name in preset:
                    continue
                try:
                    v = c_eval(val, defines)
                except Exception:
                    v = val
                forced, why = switch_value(name, v)
                if why and forced != v:
                    log.append(("switch", n, name, (v, forced, why)))
                elif why is None and isinstance(v, int) and re.search(
                        r"HLE|HACK|FRONT|FAST|SLOW|SIMPL|CLOCK|VCO|NOISE|DIODE|FIX|USE_|ENABLE|DISABLE",
                        name):
                    log.append(("unknown-switch", n, name, v))
                defines[name] = forced
            elif word == "undef":
                defines.pop(rest, None)
            continue
        if active:
            out.append((n, code, comment))
    return out, defines, funcs


# ---------------------------------------------------------------------------
# Statements
# ---------------------------------------------------------------------------

Call = collections.namedtuple("Call", "name args line comment section via", defaults=(None,))
# `via`: the function-like macro a call was expanded from, if any.


def split_args(s):
    args, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            args.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        args.append(cur.strip())
    return args


CALL = re.compile(r"\b([A-Z_][A-Z0-9_]*)\s*\(")
DECLARES = re.compile(r"D_\w+|Q_\w+|\w+_DIP8?|\w+_SIL")


def scan(text, i, where, comments, sections, funcs, line=None, via=None):
    """Calls in text[i:] up to the brace that closes the block, expanding
    function-like macros as the C preprocessor would. `line` pins every call
    to one source line (a macro's expansion is on the line that used it)."""
    out, depth = [], 1
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                break
        mm = CALL.match(text, i)
        if mm and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")):
            j, d = mm.end(), 1
            while d and j < len(text):
                d += {"(": 1, ")": -1}.get(text[j], 0)
                j += 1
            n = line if line is not None else where[i]
            name, args = mm.group(1), split_args(text[mm.end():j - 1])
            # A macro whose own name already says what the part is (Q_2N4093,
            # D_1N914, MB4391_DIP) is kept: its expansion can say less.
            if name in funcs and not DECLARES.fullmatch(name):
                params, body = funcs[name]
                for p, a in zip(params, args):
                    body = re.sub(r"\b%s\b" % re.escape(p), lambda _, a=a: a, body)
                out += scan(body + "}", 0, None, comments, sections, funcs, line=n,
                            via=via or name)
            else:
                out.append(Call(name, args, n, comments.get(n, ""), sections.get(n, ""), via))
            i = j
            continue
        i += 1
    return out


def calls(active, netlist, funcs=None):
    """The macro calls in NETLIST_START(<netlist>) { ... }, in order, each with
    its line, the comment on that line, and the section heading above it. A
    netlist of the same file that this one INCLUDEs is spliced in where it is
    included, as MAME's parser does."""
    # Flatten, remembering where each character came from.
    text, where, comments = "", [], {}
    section, sections = "", {}
    for n, code, comment in active:
        # A comment on a line of its own is a heading if it reads like one
        # (and is not commented-out code). Inside a /* ... */ block the line's
        # leading * is the block's, not the heading's (Borderline's " *  RST").
        head = comment.lstrip("* ").rstrip(" *")
        if not code.strip() and re.fullmatch(r"[A-Z0-9][\w &/'(),.:+-]{1,60}", head) \
                and not re.match(r"[A-Z_0-9]+\(", head):
            section = head.rstrip(":")
        comments[n] = comment
        sections[n] = section
        text += code + "\n"
        where += [n] * (len(code) + 1)

    def block(name, seen):
        m = re.search(r"NETLIST_START\(\s*%s\s*\)\s*\{?" % re.escape(name), text)
        if not m:
            raise SystemExit(f"no NETLIST_START({name})")
        if text[m.end() - 1] != "{":
            raise SystemExit(f"NETLIST_START({name}) has no opening brace on its line")
        out = []
        for c in scan(text, m.end(), where, comments, sections, funcs or {}):
            if c.name == "INCLUDE" and re.search(r"NETLIST_START\(\s*%s\s*\)" % re.escape(c.args[0]),
                                                 text):
                if c.args[0] in seen:
                    raise SystemExit(f"INCLUDE({c.args[0]}) includes itself")
                out += block(c.args[0], seen | {c.args[0]})
            else:
                out.append(c)
        return out

    return block(netlist, {netlist})


def commented_calls(lines, netlist_range):
    """Device declarations and connections MAME left in comments -- what it
    chose not to simulate. Reported, so a reader knows the gap is there."""
    out = []
    for n, code, comment in lines:
        if not (netlist_range[0] <= n <= netlist_range[1]):
            continue
        for m in re.finditer(r"\b(RES|CAP|POT|DIODE|D_\w+|Q_\w+|QBJT_EB|\w+_DIP8?|NET_C)\(([^)]*)\)", comment):
            out.append((n, m.group(0), comment))
    return out


# ---------------------------------------------------------------------------
# Values
# ---------------------------------------------------------------------------

UNIT = {"RES_K": (1e3, "K"), "RES_M": (1e6, "M"), "RES_R": (1, ""),
        "CAP_U": (1e-6, "uF"), "CAP_N": (1e-9, "nF"), "CAP_P": (1e-12, "pF")}


def value(expr, defines):
    """(printed value, [constants it was scaled by]). Printed in the unit
    MAME's own macro used, which is the unit the schematic printed."""
    expr = expr.strip()
    m = re.fullmatch(r"(RES_K|RES_M|RES_R|CAP_U|CAP_N|CAP_P)\(\s*([\d.eE+-]+)\s*\)(.*)", expr)
    scaled = []
    if m:
        unit, num, rest = m.group(1), m.group(2), m.group(3).strip()
        if rest:
            scaled = re.findall(r"[A-Za-z_]\w*", rest) or [rest]
        num = num.rstrip("0").rstrip(".") if "." in num else num
        suffix = UNIT[unit][1]
        return (num + suffix) if suffix else num, scaled
    m = re.fullmatch(r"([\d.eE+-]+)(.*)", expr)
    if m:
        num, rest = m.group(1), m.group(2).strip()
        if rest:
            scaled = re.findall(r"[A-Za-z_]\w*", rest) or [rest]
        return num, scaled
    return expr, ["?"]


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

Device = collections.namedtuple("Device", "name kind part value line comment section macro")


def ic_part(macro):
    p = re.sub(r"^(TTL_|PROM_|EPROM_|AMI_)", "", macro)
    p = re.sub(r"_(FAST_|SLOW_)?DIP8?$|_SIL$", "", p)
    return p


def classify(c, defines):
    """Device for a declaration call, or None."""
    name, args = c.name, c.args
    if name in ("RES", "CAP", "POT", "POT2"):
        v, scaled = value(args[1], defines) if len(args) > 1 else ("", [])
        kind = {"RES": "R", "CAP": "C"}.get(name, "POT")
        return Device(args[0], kind, None, v, c.line, c.comment, c.section, name), scaled
    if name in ("DIODE", "ZDIODE", "LED") or re.fullmatch(r"D_\w+", name):
        part = args[1].strip('"') if len(args) > 1 else name[2:]
        return Device(args[0], "D", None, part, c.line, c.comment, c.section, name), []
    if name in ("QBJT_EB", "QBJT_SW") or re.fullmatch(r"Q_\w+", name):
        part = args[1].strip('"') if len(args) > 1 else name[2:]
        return Device(args[0], "Q", None, part, c.line, c.comment, c.section, name), []
    if name == "SUBMODEL":
        part = ic_part(args[0].lstrip("_"))
        return Device(args[1], "IC", part, part, c.line, c.comment, c.section, args[0]), []
    if name in ("OPAMP",):
        part = args[1].strip('"')
        return Device(args[0], "IC", part, part, c.line, c.comment, c.section, name), []
    if name == "NE555":
        return Device(args[0], "IC", "NE555", "NE555", c.line, c.comment, c.section, name), []
    if re.fullmatch(r"\w+_DIP8?|\w+_SIL", name) or name == "AMI_S2688":
        part = ic_part(name)
        return Device(args[0], "IC", part, part, c.line, c.comment, c.section, name), []
    if name in VIRTUAL:
        return Device(args[0], "V", None, ",".join(args[1:]), c.line, c.comment, c.section, name), []
    if re.fullmatch(r"TTL_\d+\w*_(NAND|NOR|AND|OR|XOR|INVERT|ANDORINVERT)|TTL_\d+\w*", name):
        raise SystemExit(f"line {c.line}: {name} is a gate-level device -- which package "
                         "and pins it is on is not in the netlist; this converter only "
                         "handles DIP-level netlists")
    if args and library().get(name + "_DIP"):
        # A whole part declared without its package (Tank Battalion's CD4006):
        # MAME's DIP model of it numbers its named pins.
        return Device(args[0], "IC", name, name, c.line, c.comment, c.section, name), []
    return None, []


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------

def parked_parts(terms, devices):
    """The parts a NET_C to a rail holds by every terminal -- both ends of a
    resistor, capacitor or diode, all three of a pot (a pot with its wiper on
    one end is a rheostat, and real)."""
    if not any("." not in t for t in terms):
        return set()
    held = collections.defaultdict(set)
    for t in terms:
        if "." in t and not t.startswith("~"):
            dev, _, pin = t.partition(".")
            held[dev].add(pin)
    full = {"R": {"1", "2"}, "C": {"1", "2"}, "D": {"1", "2"}, "POT": {"1", "2", "3"}}
    return {d for d, pins in held.items() if pins >= full.get(devices[d].kind, {None})}


def convert(slug, cfg):
    path = cfg["source"]
    text = fetch(path)
    lic, holders = licence(text)
    if lic not in LICENCES:
        raise SystemExit(f"{path}: licence {lic} -- only {', '.join(sorted(LICENCES))} are converted")
    log = []
    lines = split_comments(text, cfg.get("restore", ()))
    # A local header (nl_cinemat_common.h) contributes defines and submodels.
    preset = dict(cfg.get("defines", {}))
    for inc in re.findall(r'#include\s+"(nl_\w+\.h)"', text):
        hdr = fetch(os.path.join(os.path.dirname(path), inc))
        _, hdefs, _ = preprocess(split_comments(hdr), {}, [])
        for k, v in hdefs.items():
            preset.setdefault(k, v)
    active, defines, funcs = preprocess(lines, preset, log)

    # Undo entries: check every guard before acting on any.
    undo = {}
    raw = text.split("\n")
    for u in cfg.get("undo", []):
        n = u["line"]
        if u["text"] not in raw[n - 1]:
            raise SystemExit(f"{slug}: undo guard failed at line {n}: "
                             f"expected {u['text']!r}, found {raw[n - 1].strip()!r}")
        undo[n] = u
    for a, b in cfg.get("restore", ()):
        if not any("/*" in l or "*/" in l or l.strip().startswith("//") for l in raw[a - 1:b]):
            raise SystemExit(f"{slug}: restore {a}-{b} is not commented out")

    cs = calls(active, cfg["netlist"], funcs)
    devices, aliases, nets, hints, scaled, used_undo = {}, {}, [], [], [], set()
    rename = cfg.get("rename", {})
    section_of = {}                             # MAME name -> (package, section)
    modelled = []                               # (device, stock part, why)
    sections = [(macro, re.compile(rx), part) for macro, rx, part in cfg.get("sections", ())]
    for c in cs:
        if c.line in undo and undo[c.line].get("action") == "drop-line":
            used_undo.add(c.line)
            continue
        if c.name in IGNORED:
            continue
        if c.name == "NET_C":
            nets.append(c)
            continue
        if c.name == "ALIAS":
            aliases[c.args[0]] = (c.args[1], c)
            continue
        if c.name == "HINT":
            if c.args[1] == "NC":
                hints.append((c.args[0], c))
            continue
        sec = next(((m, part) for macro, rx, part in sections
                    for m in [rx.fullmatch(c.args[0])] if macro == c.name and m), None)
        if sec:
            # One section of a package, declared alone: the package is the part.
            # IC_ keeps the package's name apart from a passive's (Super Speed
            # Race has an LM3900 at C1 and a capacitor C1).
            m, part = sec
            pkg = "IC_" + m.group(1)
            section_of[c.args[0]] = (pkg, m.group(2))
            if pkg not in devices:
                devices[pkg] = Device(pkg, "IC", part, part, c.line, c.comment, c.section,
                                      "sections of " + part)
            continue
        dev, sc = classify(c, defines)
        if dev is None:
            continue
        if dev.kind == "IC" and dev.part in cfg.get("models", {}):
            # A model of a stock part under its own name (an LM324 for a -5V/+12V
            # supply): the part on the board is the stock one.
            part, why = cfg["models"][dev.part]
            modelled.append((dev, part, why))
            dev = dev._replace(part=part, value=part)
        if dev.name in rename:
            dev = dev._replace(name=rename[dev.name])
        if dev.name in cfg.get("not_parts", {}):
            # A part MAME adds that the board does not have, standing in for
            # something that is (the monitor's input, a sound chip's output).
            dev = dev._replace(kind="V", macro="not a part: " + cfg["not_parts"][dev.name])
        if dev.name in cfg.get("loads", {}):
            # A dummy load MAME hangs on a pin the board leaves open, because
            # the simulator will not have an output drive nothing.
            dev = dev._replace(kind="V", macro="load: " + cfg["loads"][dev.name])
        if dev.name in cfg.get("shorts", {}):
            # A part MAME puts in series where the board has a wire.
            dev = dev._replace(kind="V", macro="short: " + cfg["shorts"][dev.name])
        devices[dev.name] = dev
        if sc:
            scaled.append((dev, sc))

    # Corrections read off the sheet: parts and connections the sheet draws
    # that MAME does not have (here), and parts MAME types or values wrongly
    # (once commented-out declarations are back, below). Every one is logged.
    for p in cfg.get("add_parts", []):
        kind = p["kind"]
        part = p["part"] if kind == "IC" else None
        devices[p["name"]] = Device(p["name"], kind, part, p.get("value", part), 0,
                                    p["why"], p.get("section", ""), "sheet")
    for i, a in enumerate(cfg.get("add", [])):
        call = Call("NET_C", a["terms"], -1 - i, a["why"], a.get("section", ""))
        nets.append(call)
        if a.get("name"):
            aliases[a["name"]] = (a["terms"][0], call)

    # A part the real-circuit branch uses but whose declaration MAME commented
    # out ("not used" -- by the stand-in): bring the declaration back.
    revived = []
    # (A term that is itself an alias -- Kid Niki's ALIAS(I_V0.Q, GND) -- names
    # no device, whatever its spelling.)
    used = {t.strip().partition(".")[0] for c in nets for t in c.args if t.strip() not in aliases}
    used |= {t.partition(".")[0] for t, _ in aliases.values()}
    for name in sorted(used - set(devices) - set(aliases) - {"GND"}):
        for n, code, comment in lines:
            m = re.match(r"\s*(\w+)\(\s*%s\s*[,)](.*)" % re.escape(name), comment)
            if m and not m.group(1) in ("NET_C", "ALIAS", "HINT"):
                call = next(iter(calls([(n, "NETLIST_START(_x) {" + comment.split("//")[0]
                                         .split("--")[0] + "}", "")], "_x")), None)
                dev, _ = classify(call._replace(comment=comment, section=""), defines)
                if dev:
                    devices[dev.name] = dev
                    revived.append((n, comment, dev.name))
                break

    fixes = []                                  # (what, [MAME names it concerns])
    for name, (part, why) in cfg.get("fix_parts", {}).items():
        was = devices[name].part
        devices[name] = devices[name]._replace(part=part, value=part)
        fixes.append((f"{name}: the sheet's part is {part}, MAME's {was} -- {why}", [name]))
    for name, (val, why) in cfg.get("fix_values", {}).items():
        was = devices[name].value
        devices[name] = devices[name]._replace(value=val)
        fixes.append((f"{name}: the sheet's value is {val}, MAME's {was} -- {why}", [name]))
    # A part MAME declares by its simulation model (a zener as "D(BV=9.1 ...)")
    # written by its part number: not a correction, so not logged as one.
    renamed = []
    for name, (val, why) in cfg.get("values", {}).items():
        renamed.append((devices[name], val, why))
        devices[name] = devices[name]._replace(value=val)

    # Resolve a term to a pin "DEV.PIN", a rail "+5V", or a virtual "~DEV.PIN".
    rails = {"GND": "GND"}
    for d in devices.values():
        if d.macro == "ANALOG_INPUT":
            try:
                volts = float(d.value)
            except ValueError:
                continue
            if volts == 0:
                if GROUND_NAME.fullmatch(d.name):
                    rails[d.name] = "GND"
            elif volts in RAIL_VOLTS:
                rails[d.name] = ("+" if volts > 0 else "-") + f"{abs(volts):g}V"

    # A noise source in series -- neither terminal on a rail -- is MAME's model
    # of the noise in the zener it sits beside; on the board the two are one
    # node. (One with a terminal on a rail is a source standing in for a
    # circuit, and its other terminal becomes a port as any stand-in's does.)
    held = collections.defaultdict(set)
    for c in nets:
        for t in c.args:
            dev, _, pin = t.strip().partition(".")
            if dev in devices and devices[dev].macro in NOISE_SOURCES and pin in ("1", "2"):
                held[dev] |= {a.strip() for a in c.args} - {t.strip()}
    series = {d for d, others in held.items()
              if not any(o in rails or o.partition(".")[0] in rails for o in others)
              and {p for c in nets for t in c.args if t.strip().startswith(d + ".")
                   for p in [t.strip().partition(".")[2]]} >= {"1", "2"}}
    wires = set()                               # virtual tokens that are wires, not ports

    repin = cfg.get("repin", {})

    def resolve(term, seen=(), sheet=False):
        """`sheet` terms come from a correction and are in the board's own pin
        numbers; MAME's are in the numbering of the part MAME models, which
        `repin` maps onto the part the board has."""
        term = term.strip()
        if term in rails:
            return rails[term]
        if sheet and checker.is_rail(term):
            return term                            # a rail named outright (-12V)
        if term in aliases and term not in seen:
            return resolve(aliases[term][0], seen + (term,))
        dev, _, pin = term.partition(".")
        dev = rename.get(dev, dev)
        if dev in rails and pin == "Q":
            return rails[dev]                      # an ANALOG_INPUT's output is its rail
        if dev not in devices and dev in aliases and pin == "Q":
            return resolve(dev, seen)              # a clock's output, aliased to a pin
        if dev in section_of:
            pkg, sec = section_of[dev]
            table = SECTION_PINS[devices[pkg].part][sec]
            if pin not in table:
                raise SystemExit(f"{term}: section {sec} of {devices[pkg].part} has no pin {pin}")
            return f"{pkg}.{table[pin]}"
        if dev in devices:
            d = devices[dev]
            if d.kind == "V":
                if dev in series and pin in ("1", "2"):
                    wires.add(f"~{dev}.series")
                    return f"~{dev}.series"
                if d.macro.startswith("short: "):
                    wires.add(f"~{dev}.short")
                    return f"~{dev}.short"
                return f"~{dev}.{pin or 'Q'}"
            if not pin:
                raise SystemExit(f"{term}: a device used without a pin")
            if d.kind == "D":
                pin = DIODE_PINS.get(pin, pin)
            elif d.kind == "IC" and d.macro in NAMED_PINS:
                pin = NAMED_PINS[d.macro][pin]
            elif d.kind == "IC" and d.macro == "OPAMP":
                pin = NAMED_PINS["OPAMP"][pin]
            elif d.kind == "IC" and not pin.isdigit():
                num = library_pin(d.macro, pin)
                if num is None:
                    raise SystemExit(f"{term}: MAME's {d.macro} has no DIP pin named {pin}")
                pin = num
            if dev in repin and not sheet:
                if pin not in repin[dev]:
                    raise SystemExit(f"{term}: repin for {dev} has no pin {pin}")
                pin = repin[dev][pin]
            return f"{dev}.{pin}"
        raise SystemExit(f"unresolved term {term!r}")

    u = checker.Union()
    first_line = {}
    dropped, made_nc, ports_from_undo, parked, kept = [], [], {}, set(), []
    unused = re.compile(cfg.get("unused_sections", r".*\b(unused|unconnected|not connected)\b.*"),
                        re.I)
    for c in nets:
        terms = [resolve(t, sheet=c.line < 0) for t in c.args]
        if c.via in cfg.get("hack_macros", {}) and c.line not in undo:
            # A tie made by a macro the file itself calls a hack (Borderline's
            # UNUSED_OP_PLUS): what the board does with the pin is not here.
            made_nc.append((c, [t for t in terms if "." in t and not t.startswith("~")],
                            f"MAME's {c.via}(), {cfg['hack_macros'][c.via]}"))
            continue
        if c.line in undo:
            used_undo.add(c.line)
            act = undo[c.line]
            pins = [t for t in terms if "." in t and not t.startswith("~")]
            if act["action"] == "nc":
                made_nc.append((c, pins, act["why"]))
                continue
            if act["action"] == "keep":            # a tie in an "unused" block the sheet draws
                kept.append((c, act["why"]))
                for t in terms:
                    first_line.setdefault(t, c)
                for a, b in zip(terms, terms[1:]):
                    u.join(a, b)
                continue
            if act["action"] == "drop":
                dropped.append((c, act["why"], terms))
                continue
            if act["action"] == "port":            # the pin goes somewhere MAME does not draw
                dropped.append((c, act["why"], terms))
                for p in pins:
                    ports_from_undo[p] = (act["name"], act["why"])
                    u.find(p)
                    first_line.setdefault(p, c)
                continue
            if act["action"] == "remove":          # drop some terms, keep the rest
                gone = [resolve(t) for t in act["terms"]]
                dropped.append((c, f"took {', '.join(act['terms'])} out of it: " + act["why"],
                                gone))
                terms = [t for t in terms if t not in gone]
        elif parked_parts(terms, devices):
            # Both ends of a part tied to one rail: MAME parks the parts of a
            # circuit it replaced with a stand-in. They are on the board, but
            # where they go is not in the netlist.
            two = parked_parts(terms, devices)
            parked.update(two)
            made_nc.append((c, [t for t in terms if "." in t and t.partition(".")[0] not in two],
                            "parked on a rail with " + ", ".join(sorted(two, key=nat)) +
                            " -- MAME replaces this circuit with a stand-in"))
            continue
        elif unused.fullmatch(c.section or "") and len([t for t in terms if "." not in t]) <= 1 \
                and any(t in devices and devices[t].kind == "IC"
                        for t in (x.partition(".")[0] for x in terms if "." in x)):
            # MAME's block of unused pins tied to a rail, or to each other: a
            # simulator needs a defined level on every input, and nothing says
            # the board ties them. A passive in the same statement is circuit,
            # not a tie-off (Rally-X grounds C35 in its unused-gate line), and
            # keeps its rail.
            rail = next((t for t in terms if "." not in t), None)
            ics = [t for t in terms if "." in t and not t.startswith("~")
                   and devices[t.partition(".")[0]].kind == "IC"]
            made_nc.append((c, ics, (f"tied to {rail}" if rail else "tied to one another") +
                            f" in MAME's \"{c.section}\" block"))
            rest = [t for t in terms if t not in ics]
            if rail and len(rest) > 1:
                for t in rest:
                    first_line.setdefault(t, c)
                for a, b in zip(rest, rest[1:]):
                    u.join(a, b)
            continue
        for t in terms:
            first_line.setdefault(t, c)
        for a, b in zip(terms, terms[1:]):
            u.join(a, b)
    for name, (term, c) in aliases.items():
        t = resolve(term)
        u.find(t)
        first_line.setdefault(t, c)
    for t, c in hints:
        made_nc.append((c, [resolve(t)], "MAME's own HINT(NC)"))
    for n in undo:
        if n not in used_undo:
            raise SystemExit(f"{slug}: undo at line {n} matched no statement")

    # Group.
    groups = collections.defaultdict(set)
    for t in list(u.parent):
        groups[u.find(t)].add(t)

    # A pin MAME ties off as unused while its own netlist (or a correction)
    # connects it: the tie is the mistake, so drop it rather than call the
    # pin unconnected.
    joined = {t for m in groups.values() if len(m) > 1 for t in m}
    used_ties = []
    for i, (c, pins, why) in enumerate(made_nc):
        keep = [p for p in pins if p not in joined]
        if len(keep) != len(pins):
            used_ties.append((c, [p for p in pins if p in joined]))
            made_nc[i] = (c, keep, why)
    made_nc = [x for x in made_nc if x[1]]
    alias_of = collections.defaultdict(list)
    for name, (term, c) in aliases.items():
        alias_of[u.find(resolve(term))].append(name)

    port_names = dict(cfg.get("ports", {}))
    out_nets = []
    for root, members in groups.items():
        pins = sorted(m for m in members if "." in m and not m.startswith("~"))
        rail = sorted({m for m in members if "." not in m})
        virt = sorted(m for m in members if m.startswith("~") and m not in wires)
        names = [a for a in alias_of[root] if a not in rails]
        if len(rail) > 1:
            raise SystemExit(f"rails shorted together: {rail} via {pins[:6]}")
        if not pins:
            continue
        for p in pins if rail else ():
            # A supply pin on the wrong rail is a MAME slip the checker cannot
            # see (it joins whatever it is told to): Tank Battalion's netlist
            # puts its 7486's pin 14 on ground and pin 7 on +5V.
            dev, _, num = p.partition(".")
            d = devices[dev]
            if d.kind != "IC":
                continue
            try:
                pname, ptype = checker.pinout(d.part).get(num, ("", ""))
            except KeyError:
                continue                            # no pinout: write() says so
            if ptype != "power_in":
                continue
            if d.part not in checker.KICAD and "rail" not in checker.custom_entry(d.part)["pins"][num]:
                continue        # a custom pinout says which rail only with `rail` (PMOS VSS is +)
            low = lambda r: r == "GND" or r.startswith("-")             # noqa: E731
            if low(checker.supply_rail(d.part, num, pname)) != low(rail[0]):
                raise SystemExit(f"{p} is {d.part} pin {num} ({pname}) but MAME puts it on "
                                 f"{rail[0]} -- correct it in the target")
        sec = min((first_line[m] for m in members if m in first_line), key=lambda c: c.line)
        undone = [ports_from_undo[p] for p in pins if p in ports_from_undo]
        if undone:
            names = [undone[0][0]] + names
        out_nets.append(dict(pins=pins, rail=rail[0] if rail else None, virt=virt,
                             names=names, line=sec.line, section=sec.section,
                             undone_port=undone[0][1] if undone else None))

    return dict(slug=slug, cfg=cfg, path=path, licence=lic, holders=holders, log=log,
                devices=devices, nets=out_nets, dropped=dropped, made_nc=made_nc, revived=revived,
                parked=parked, fixes=fixes, used_ties=used_ties, series=series,
                modelled=modelled, section_of=section_of, renamed=renamed, kept=kept,
                scaled=scaled, port_names=port_names, defines=defines,
                commented=commented_calls(lines, (min(c.line for c in cs), max(c.line for c in cs))),
                text=text)


# ---------------------------------------------------------------------------
# Designators and boards
# ---------------------------------------------------------------------------

def nat(s):
    """Natural sort key: C2 before C10."""
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", s)]


def designator(cfg, dev):
    """MAME's name for a device -> the designator the .nets file uses."""
    m = cfg.get("designators", {})
    if dev.name in m:
        return m[dev.name]
    if dev.kind == "IC":
        # IC_A7, IC6, U8, and Namco's _6F (a name cannot start with a digit).
        r = re.fullmatch(r"(?:IC_|IC|U|_)([A-Z]?\d+[A-Z]?)", dev.name) or \
            re.fullmatch(cfg.get("ic_names", r"(?!)"), dev.name)
        if r:
            return "U" + r.group(1)
        raise SystemExit(f"{dev.name}: no designator rule for this IC -- add it to the target")
    strip = cfg.get("strip_suffix")
    if strip:
        r = re.fullmatch(strip, dev.name)
        if r:
            return r.group(1)
    return dev.name


TARGET_TITLES = {}                      # board slug -> title, for cross-board comments


def split(res, cfg):
    """One converted netlist that spans boards -> one result per board.

    cfg["assign"] puts every part on a board ({slug: [MAME names]}); a net
    with pins on two boards appears on each, as a port, or as a label through
    the connector contacts cfg["contacts"] gives it on that board."""
    assign = {n: slug for slug, names in cfg["assign"].items() for n in names}
    real = {n for n, d in res["devices"].items() if d.kind != "V"}
    if set(assign) - real:
        raise SystemExit(f"split: assigned but not in the netlist {sorted(set(assign) - real, key=nat)}")
    for n in real - set(assign):
        if not cfg.get("assign_default"):
            break
        assign[n] = cfg["assign_default"]
    if real - set(assign):
        raise SystemExit(f"split: not assigned {sorted(real - set(assign), key=nat)}; "
                         f"assigned but not in the netlist {sorted(set(assign) - real, key=nat)}")
    on = lambda t: assign.get(t.partition(".")[0])                   # noqa: E731
    out = []
    for slug, meta in cfg["split"].items():
        TARGET_TITLES[slug] = meta["title"]
        sub_cfg = dict(cfg, **meta)
        nets, used_virt = [], set()
        for n in res["nets"]:
            mine = [p for p in n["pins"] if on(p) == slug]
            if not mine:
                continue
            others = sorted({on(p) for p in n["pins"]} - {slug})
            nn = dict(n, pins=mine)
            if others and not n["rail"]:
                nn["cross"] = others
                if n["names"]:
                    nn["cross_name"] = n["names"][0]
                else:                                           # name it by the far end
                    far = next(p for p in n["pins"] if on(p) != slug)
                    dev, _, pin = far.partition(".")
                    nn["cross_name"] = f"{designator(cfg, res['devices'][dev])}.{pin}"
            used_virt.update(v[1:].partition(".")[0] for v in n["virt"])
            nets.append(nn)
        devs = {k: d for k, d in res["devices"].items()
                if assign.get(k) == slug or (d.kind == "V" and k in used_virt)}
        sub = dict(res, slug=slug, cfg=sub_cfg, devices=devs, nets=nets,
                   all_devices=set(res["devices"]),
                   made_nc=[(c, [p for p in pins if on(p) == slug], why)
                            for c, pins, why in res["made_nc"]
                            if any(on(p) == slug for p in pins)],
                   # A dropped statement belongs to the board its own parts are on,
                   # not the board an alias in it happens to resolve to.
                   dropped=[(c, why, terms) for c, why, terms in res["dropped"]
                            if any(assign.get(t.partition(".")[0]) == slug for t in c.args)
                            or (not any(t.partition(".")[0] in assign for t in c.args)
                                and any(on(t) == slug for t in terms if "." in t))],
                   parked={p for p in res["parked"] if assign.get(p) == slug},
                   revived=[x for x in res["revived"] if assign.get(x[2]) == slug],
                   fixes=[f for f in res["fixes"] if any(assign.get(n) == slug for n in f[1])],
                   used_ties=[(c, [p for p in pins if on(p) == slug])
                              for c, pins in res["used_ties"] if any(on(p) == slug for p in pins)])
        out.append((slug, sub))
    return out


def port_name(net, devices):
    if net["names"]:
        return net["names"][0]
    v = net["virt"][0][1:]
    dev = v.partition(".")[0]
    return re.sub(r"^I_", "", dev)


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------

def write(res, out_path, board_path):
    cfg, devices = res["cfg"], res["devices"]
    des = {name: designator(cfg, d) for name, d in devices.items() if d.kind != "V"}
    clash = collections.Counter(des.values())
    dup = [k for k, n in clash.items() if n > 1]
    if dup:
        raise SystemExit(f"designators collide: {dup}")

    def P(t):
        dev, _, pin = t.partition(".")
        return f"{des[dev]}.{pin}"

    def contact_of(n):
        """Connector contacts the target gives a net, by any name it has."""
        keys = list(n["names"]) + ([port_name(n, devices)] if n["virt"] else [])
        keys += [k for k in (n["rail"], n.get("cross_name")) if k]
        for k in keys:
            c = cfg.get("contacts", {}).get(k)
            if isinstance(c, dict):
                c = c.get(res["slug"])
            if c:
                return [c] if isinstance(c, str) else list(c)
        return []

    ics = {des[n][1:]: d.part for n, d in devices.items() if d.kind == "IC"}
    mentioned = set()
    for n in res["nets"]:
        mentioned.update(P(p) for p in n["pins"])
    for c, pins, why in res["made_nc"]:
        mentioned.update(P(p) for p in pins)

    L = []
    w = L.append
    r = res
    w(f"# {cfg['title']} -- netlist converted from MAME")
    w("#")
    for line in cfg["about"].strip().split("\n"):
        w(("# " + line).rstrip())
    w("#")
    w(f"# Source: MAME {TAG} (commit {COMMIT[:12]}), {r['path']},")
    w(f"# NETLIST_START({cfg['netlist']}). Licence {r['licence']} by the file's own header (line 1),")
    w(f"# copyright-holders {r['holders']} (line 2).")
    w(f"# {RAW}{r['path']}")
    w("# Converted by tools/mame_netlist.py; checked by tools/build_board_nets.py.")
    w("#")
    w("# What the conversion means. MAME's netlists are written to be simulated, so this is a")
    w("# second reading of the sheet by someone else, not a read of it: designators and pin")
    w("# numbers are MAME's unless the notes say the sheet was read to correct them. Names on")
    w("# `label` lines are MAME's, which mostly follow the sheet's with Q for an overbar; `net`")
    w("# is used only for the supply rails. A `port` is a net that leaves what this file")
    w("# describes -- a signal from the CPU or the other board, a cabinet control, or a source")
    w("# MAME simulates with a stand-in rather than the circuit.")
    w("#")
    w("#   net NAME: PIN ...     a supply rail")
    w("#   label NAME: PIN ...   a net MAME names")
    w("#   wire PIN PIN ...      an unnamed connection")
    w("#   port NAME: PIN ...    a net that leaves this file (see above)")
    w("#   nc PIN ...            a pin with nothing attached")
    w("#   parallel PIN ...      outputs the board sums on one node by design")
    w("#   value REF VALUE       a passive's value, in the unit MAME's own macro uses")
    w("#")
    w("# PIN is DESIGNATOR.NUMBER. Diode pin 1 is the cathode; transistors keep B, C and E;")
    w("# MAME does not record which way round an electrolytic goes, so C pins are MAME's 1/2.")
    if any(re.fullmatch(r"IC\d+[A-Z]?", n) for n, d in devices.items() if d.kind == "IC"):
        w("# The sheet numbers its ICs IC1, IC2 ...; they are written U1, U2 ... here, because the")
        w("# checker files every IC under a U designator.")
    if cfg.get("designator_note"):
        for line in cfg["designator_note"].strip().split("\n"):
            w(("# " + line).rstrip())

    # What was undone.
    w("#")
    w("# ---------------------------------------------------------------------------")
    w("# Undone: what MAME does to simulate the board that the board does not do")
    w("# ---------------------------------------------------------------------------")
    sw = [x for x in r["log"] if x[0] == "switch"]
    for _, n, name, (was, now, why) in sw:
        w(f"# line {n}: #define {name} {was} -> {now} ({why})")
    for kind, n, name, v in r["log"]:
        if kind == "unknown-switch":
            w(f"# line {n}: #define {name} {v} -- kept as MAME has it (not a known kind of hack)")
    for dev, sc in r["scaled"]:
        w(f"# line {dev.line}: {dev.name} written as {dev.value}, without the {' '.join(sc)} "
          "MAME multiplies it by")
    for c, why, _ in r["dropped"]:
        w(f"# line {c.line}: dropped NET_C({', '.join(c.args)}) -- {why}")
    for c, pins, why in r["made_nc"]:
        if why == "MAME's own HINT(NC)":
            continue
        w(f"# line {c.line}: NET_C({', '.join(c.args)}) -> nc -- {why}")
    for c, why in r.get("kept", []):
        w(f"# line {c.line}: NET_C({', '.join(c.args)}) kept, though MAME files it as a tie-off -- "
          f"{why}")
    for c, pins in r.get("used_ties", []):
        if c.name == "HINT":
            w(f"# line {c.line}: MAME hints {', '.join(P(p) for p in pins)} as unconnected, but its "
              "own netlist connects it -- the hint is dropped")
            continue
        w(f"# line {c.line}: MAME ties {', '.join(P(p) for p in pins)} off as unused, but the "
          "circuit uses them -- the tie is dropped")
    for a, b in cfg.get("restore", ()):
        if any(a <= d.line <= b for d in devices.values()):
            w(f"# lines {a}-{b}: restored from a comment -- "
              f"{cfg.get('restore_why', {}).get((a, b), '')}")
    revived = [(n, c.split("//")[0].split("--")[0].strip()) for n, c, _ in r["revived"]]
    if revived:
        w("# Declarations MAME comments out but the restored circuit uses, restored: " +
          ", ".join(f"{des[name]} (line {n})" for (n, _), (_, _, name) in zip(revived, r["revived"])))
    if r.get("fixes") or cfg.get("add"):
        w("#")
        w("# Corrected from " + cfg.get("corrected_from",
                                       "the sheet (the notes below say what was read where)") + ":")
        for text, names in r.get("fixes", []):
            w(f"#   {text.replace(names[0], des.get(names[0], names[0]), 1)}")
        added = [p for p in cfg.get("add_parts", []) if p["name"] in devices]
        if added:
            w("#   parts the sheet draws that MAME does not have: " + ", ".join(
                f"{des[p['name']]} {p.get('value', p.get('part'))}" for p in added))
        by_why = collections.OrderedDict()
        for a in cfg.get("add", []):
            mine = [t for t in a["terms"] if t.partition(".")[0] in devices]
            if mine:
                by_why.setdefault(a["why"], []).append(
                    " ".join(P(t) if "." in t else t for t in mine) +
                    (f" ({a['name']})" if a.get("name") else ""))
        for why, joins in by_why.items():
            w(f"#   {why}: " + "; ".join(joins))
    if r["parked"]:
        w("# Parked by MAME, both ends on a rail, because a stand-in replaces their circuit; on")
        w("# the board, not in this file: " + ", ".join(
            f"{des[p]} {devices[p].value}" for p in sorted(r["parked"], key=nat)))
    for d in sorted(devices.values(), key=lambda d: d.line):
        if d.macro.startswith(("not a part: ", "load: ")):
            w(f"# line {d.line}: {d.name} is not a part -- {d.macro.partition(': ')[2]}")
        elif d.macro.startswith("short: "):
            w(f"# line {d.line}: {d.name} is not a part, and its two ends are one node here -- "
              f"{d.macro.partition(': ')[2]}")
    for name in sorted(r.get("series", ()), key=nat):
        if name in devices:
            w(f"# line {devices[name].line}: {devices[name].macro}({name}) is MAME's noise source in "
              "series with the zener it models the noise of; its two ends are one node here")
    by_value = collections.OrderedDict()
    for dev, val, why in r.get("renamed", ()):
        if dev.name in des:
            by_value.setdefault((val, why, dev.value), []).append(des[dev.name])
    for (val, why, model), refs in by_value.items():
        w(f"# {', '.join(sorted(refs, key=nat))} written {val}, where MAME gives its model "
          f"({model}) -- {why}")
    for dev, part, why in r.get("modelled", ()):
        if dev.name in des:
            w(f"# line {dev.line}: {des[dev.name]} is MAME's {dev.part} model, {why}; the part is "
              f"the {part}")
    packages = collections.defaultdict(list)
    for name, (pkg, sec) in r.get("section_of", {}).items():
        if pkg in des:
            packages[pkg].append(name)
    if packages:
        w("# MAME declares one section of these packages at a time; each is written on its package's")
        w("# pins by the data sheet's numbering of the sections (SECTION_PINS in the converter): " +
          "; ".join(f"{des[p]} {devices[p].part} ({', '.join(sorted(s, key=nat))})"
                    for p, s in sorted(packages.items(), key=lambda kv: nat(kv[0]))))
    virt = [d for d in devices.values() if d.kind == "V" and d.macro != "ANALOG_INPUT"
            and not d.macro.startswith(("not a part: ", "load: ", "short: "))
            and d.name not in r.get("series", ())]
    if virt:
        w("# Stand-ins that are not parts (the nets they drive are ports): " +
          ", ".join(f"{d.macro}({d.name})" for d in sorted(virt, key=lambda d: d.line)))
    for note in cfg.get("undo_notes", []):
        for i, line in enumerate(note.strip().split("\n")):
            w(("# " + line).rstrip())

    if r["commented"]:
        w("#")
        w("# Left out by MAME (commented out at TAG, so not in this file either):")
        seen = set()
        for n, call, comment in r["commented"]:
            if any(a <= n <= b for a, b in cfg.get("restore", ())):
                continue
            key = call.split("(")[1].split(",")[0].strip()
            if key in r.get("all_devices", devices):
                continue                        # restored, or put back from the sheet
            if call.startswith("NET_C") or key in seen:
                continue
            seen.add(key)
            w(f"#   line {n}: {comment[:86]}")

    for note in cfg.get("notes", []):
        w("#")
        for line in note.strip().split("\n"):
            w(("# " + line).rstrip())

    # Parts.
    w("")
    by_des = sorted(devices.items(), key=lambda kv: nat(des.get(kv[0], "")))
    for name, d in by_des:
        if d.kind == "IC":
            extra = f"  (MAME: {d.name})" if des[name][1:] != re.sub(r"^(IC_|IC|U)", "", name) else ""
            w(f"# part {des[name]} {d.part}{extra}")
    w("")
    for kind in ("R", "POT", "C", "D", "Q", "Y", "SW"):
        for name, d in by_des:
            if d.kind == kind and name not in r["parked"]:
                extra = [f"MAME: {name}"] if des[name] != name else []
                if VALUE_NOTE.search(d.comment or ""):
                    # What MAME says about a value travels with it (Tank Battalion's R46:
                    # "Possible schematic or scan-quality error: Schematic says 47K").
                    extra.append(f"MAME's comment: {d.comment.strip()!r}")
                w(f"value {des[name]} {d.value}" + (f"  # {'; '.join(extra)}" if extra else ""))

    # Nets: the rails, then the rest by MAME's section.
    by_sec = collections.OrderedDict()
    by_sec["Supplies"] = sorted((n for n in r["nets"] if n["rail"]),
                                key=lambda n: (n["rail"] != "GND", n["rail"]))
    for n in sorted(r["nets"], key=lambda n: n["line"]):
        if not n["rail"]:
            by_sec.setdefault(n["section"] or "Parts", []).append(n)
    for sec, nets in by_sec.items():
        w("")
        w("# " + "-" * 75)
        w(f"# {sec}")
        w("# " + "-" * 75)
        for n in nets:
            contacts = contact_of(n)
            pins = " ".join([P(p) for p in n["pins"]] + contacts)
            # A net that reaches a connector contact is drawn to it: a label, not a port.
            port = "label" if contacts else "port"
            leaves = [x for x in n["names"] if x in r["port_names"]]
            loads = [devices[v[1:].partition(".")[0]] for v in n["virt"]
                     if devices[v[1:].partition(".")[0]].macro.startswith("load: ")]
            if loads and len(loads) == len(n["virt"]):
                n = dict(n, virt=[])
                if len(n["pins"]) == 1 and not leaves:
                    w(f"nc {pins}  # MAME hangs {loads[0].name} on it: {loads[0].macro[6:]}")
                    continue
            if n["rail"]:
                w(f"net {n['rail']}: {pins}")
            elif n["undone_port"]:
                w(f"{port} {n['names'][0]}: {pins}  # {n['undone_port']}")
            elif contacts and not n.get("cross") and not (n["virt"] or leaves):
                w(f"label {n['names'][0] if n['names'] else port_name(n, devices)}: {pins}")
            elif n.get("cross"):
                other = " and ".join(TARGET_TITLES.get(b, b) for b in n["cross"])
                also = f"; MAME also calls it {', '.join(n['names'][1:])}" if len(n["names"]) > 1 else ""
                if contacts:
                    w(f"label {n['cross_name']}: {pins}  # to {other}{also}")
                else:
                    w(f"port {n['cross_name']}: {pins}  # to {other}, where MAME joins it by "
                      f"name; the contact it crosses on is not in MAME{also}")
            elif n["virt"] or leaves:
                # A stand-in by its macro; parts that are not parts by name, with the
                # reason once (Kid Niki's AY drives one node through six of them).
                virt_devs = sorted({v[1:].partition(".")[0] for v in n["virt"]}, key=nat)
                why_not = collections.OrderedDict()
                for d in virt_devs:
                    if devices[d].macro.startswith("not a part: "):
                        why_not.setdefault(devices[d].macro[12:], []).append(d)
                srcs = ", ".join(sorted({f"{devices[d].macro}({d})" for d in virt_devs
                                         if not devices[d].macro.startswith("not a part: ")}) +
                                 [f"{', '.join(ds)}, not part{'s' if len(ds) > 1 else ''}: {w_}"
                                  for w_, ds in why_not.items()])
                why = f"  # in MAME: {srcs}" if srcs else f"  # {r['port_names'][leaves[0]]}"
                w(f"{port} {port_name(n, devices)}: {pins}{why}")
            elif len(n["pins"]) == 1 and n["names"]:
                w(f"nc {pins}  # MAME names it {n['names'][0]}; nothing else here connects to it")
            elif n["names"]:
                also = f"  # also {', '.join(n['names'][1:])}" if len(n["names"]) > 1 else ""
                w(f"label {n['names'][0]}: {pins}{also}")
            elif len(n["pins"]) == 1:
                w(f"nc {pins}  # MAME connects this pin to nothing else")
            else:
                w(f"wire {pins}")
            summed = [P(p) for p in n["pins"] if p.partition(".")[2] in
                      CURRENT_OUT.get(devices[p.partition(".")[0]].part, ())]
            if len(summed) > 1:
                w(f"parallel {' '.join(summed)}  # transconductance outputs: currents, summed here")

    # nc: undone ties, HINTs, and pins MAME never mentions.
    w("")
    w("# " + "-" * 75)
    w("# Pins with nothing attached")
    w("# " + "-" * 75)
    for c, pins, why in r["made_nc"]:
        if pins:
            w(f"nc {' '.join(P(p) for p in pins)}  # line {c.line}: {why}")
    silent = []
    for name, d in by_des:
        if d.kind != "IC":
            continue
        try:
            table = checker.pinout(d.part)
        except KeyError:
            raise SystemExit(f"{d.part} ({name}): no pinout -- map it to a KiCad symbol in "
                             "build_board_nets.KICAD or add it to tools/custom_pinouts.json")
        for num, (pname, ptype) in sorted(table.items(), key=lambda kv: nat(kv[0])):
            p = f"{des[name]}.{num}"
            if p not in mentioned and ptype != "power_in":
                silent.append((des[name], num, pname or ptype.replace("_", " ")))
    if silent:
        w("# Pins the MAME netlist never mentions. On a real board these are unused outputs, or")
        w("# inputs left open or tied in a way MAME did not draw; they are written here so that")
        w("# the checker's coverage test still means something for every other pin.")
        by_ref = collections.OrderedDict()
        for ref, num, pname in silent:
            by_ref.setdefault(ref, []).append((num, pname))
        for ref, lst in by_ref.items():
            w(f"nc {' '.join(f'{ref}.{n}' for n, _ in lst)}  # {' '.join(p for _, p in lst)}")

    open(out_path, "w").write("\n".join(L) + "\n")

    board = dict(cfg["board"])
    board["slug"] = res["slug"]
    board["ics"] = dict(sorted(ics.items(), key=lambda kv: (len(kv[0]), kv[0])))
    board["source"] = {"mame": r["path"], "tag": TAG, "commit": COMMIT,
                       "netlist": cfg["netlist"], "licence": r["licence"],
                       "copyright": r["holders"]}
    if os.path.isfile(board_path):
        old = json.load(open(board_path))
        for k in ("grid", "size", "spans"):
            if k in old:
                board[k] = old[k]
    json.dump(board, open(board_path, "w"), indent=1)
    return silent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--check", action="store_true", help="convert and report, write nothing")
    a = ap.parse_args()
    if a.list or not a.slug:
        for slug, cfg in TARGETS.items():
            text = fetch(cfg["source"])
            print(f"{slug:24} {licence(text)[0]:14} {cfg['source']}")
        return 0
    for target in a.slug:
        cfg = TARGETS[target]
        res = convert(target, cfg)
        parts = split(res, cfg) if "split" in cfg else [(target, res)]
        for slug, sub in parts:
            out = os.path.join(ROOT, "boards", f"{slug}.nets")
            board = os.path.join(ROOT, "boards", f"{slug}.json")
            if a.check:
                out, board = os.devnull, os.devnull
            silent = write(sub, out, board)
            undone = len(sub["dropped"]) + len([x for x in sub["made_nc"]
                                                if x[2] != "MAME's own HINT(NC)"])
            cross = len([n for n in sub["nets"] if n.get("cross")])
            print(f"{slug}: {len([d for d in sub['devices'].values() if d.kind != 'V'])} parts, "
                  f"{len(sub['nets'])} nets ({cross} to another board), "
                  f"{undone} undone connections, "
                  f"{len([x for x in sub['log'] if x[0] == 'switch'])} switches changed, "
                  f"{len(silent)} pins MAME never mentions")
        for kind, n, name, v in res["log"]:
            if kind == "unknown-switch":
                print(f"  ? line {n}: {name} = {v} kept -- not a known kind of switch")
    return 0


if __name__ == "__main__":
    sys.exit(main())
