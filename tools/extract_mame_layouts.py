#!/usr/bin/env python3
"""Read the ASCII "PCB Layout" diagrams in MAME's driver comments into partial board maps.

Many MAME drivers carry a drawing of the board in a comment -- most of them the Guru's,
read off real PCBs -- with a "Notes:" legend under it that says what each part is:

    |AY-3-8910   SR01.C11  Z80A(2) 12MHz   Z80A(1) M58725(1)|
    ...
    Notes:
          Z80A(1) - Z80A CPU. Clock 3.000MHz [12/4] (Main CPU)
         SR01.C11 - 27C128 16kBx8-bit EPROM (sound program)

For the makers whose designators are not grid positions (Sega, Namco, Konami, IGS: U34
does not say where U34 is) this is the widest licence-clean source of *where things are*
there is. It is also the weakest kind of board map on the site, and it is kept apart from
both the others for the same reason ROM maps are:

  - It is major devices only. The diagrams name CPUs, customs, ROMs, RAMs, PALs, sound
    chips, crystals, DIP switches and connectors, and leave out the 74-series logic and
    every passive -- most of the parts on the board.
  - Positions are approximate: a character cell on a sketch, not a footprint.
  - It is one person's reading of one board, with no second source to check it against
    beyond the romset (see `dump` below).

So nothing here is ever merged into boards/ (read off factory location drawings, every
device with its provenance) or data/rommap/ (positions from romset filenames). A layout
records where it came from -- driver file, line, MAME tag and commit, licence and
copyright holders -- and every device records the source line it was read from.

Only files under a permissive licence are read: BSD-3-Clause and CC0. A handful of
drivers are GPL-2.0+ or LGPL-2.1+ (taito_b.cpp, naomi.cpp, hng64.cpp ...); they are
counted and skipped, not reproduced.

Which machine a layout belongs to, strongest first (`scope`):

  set     the comment sits directly above that set's ROM_START -- the Guru's habit
  title   the lines above the diagram name the game, and the name is the title of a
          parent set in the same driver ("Arkanoid / Taito 1986")
  driver  in the driver's header comment, naming no set: it describes the hardware
          the driver emulates, which may not be every set's board
  file    anywhere else in the file

A set's clones (GAME macros in the same file) go with it.

Input is a MAME checkout at a release tag (the source is not committed here):

  git clone --depth 1 --branch mame0289 --filter=blob:none --sparse \\
      https://github.com/mamedev/mame.git /tmp/mame
  git -C /tmp/mame sparse-checkout set src/mame
  python3 -I tools/extract_mame_layouts.py /tmp/mame

Output, both committed:

  data/mame/layouts/<dir>.json   {driver file: [layout, ...]}, sharded by MAME's source
                                 directory to keep the deploy's file count down
  data/mame/layouts.json         one summary row per layout, and the measurement
"""
import argparse, collections, fnmatch, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "mame", "layouts")
OUT_INDEX = os.path.join(ROOT, "data", "mame", "layouts.json")

PERMITTED = {"BSD-3-Clause", "CC0-1.0"}
TAB = 4                       # MAME's own tab width

LAYOUT_RE = re.compile(r"pcb\s+layout", re.I)


# --------------------------------------------------------------------------- comments

def comment_lines(text):
    """The comment text of every line, with code blanked to spaces so columns hold.

    A diagram only ever lives in a comment, and blanking the code means a run of
    `a | b` expressions can never pass for a board edge.
    """
    out, cur = [], []
    i, n = 0, len(text)
    state = "code"            # code | line | block | str | chr
    while i < n:
        c = text[i]
        nx = text[i + 1] if i + 1 < n else ""
        if c == "\n":
            out.append("".join(cur))
            cur = []
            if state == "line":
                state = "code"
            i += 1
            continue
        if state == "code":
            if c == "/" and nx == "/":
                state = "line"; cur.append("  "); i += 2; continue
            if c == "/" and nx == "*":
                state = "block"; cur.append("  "); i += 2; continue
            if c == '"':
                state = "str"
            elif c == "'" and not (cur and cur[-1].isalnum()):     # 0x1'0000 digit separators
                state = "chr"
            cur.append("\t" if c == "\t" else " ")
        elif state == "line":
            cur.append(c)
        elif state == "block":
            if c == "*" and nx == "/":
                state = "code"; cur.append("  "); i += 2; continue
            cur.append(c)
        else:                 # inside a string or char literal
            if c == "\\":
                cur.append("  "); i += 2; continue
            if (state == "str" and c == '"') or (state == "chr" and c == "'"):
                state = "code"
            cur.append("\t" if c == "\t" else " ")
        i += 1
    out.append("".join(cur))
    return [ln.expandtabs(TAB).rstrip() for ln in out]


def code_mask(raw, com):
    """True for each line that has code outside its comment."""
    out = []
    for r, c in zip(raw, com):
        r = r.expandtabs(TAB)
        rest = "".join(ch for k, ch in enumerate(r) if k >= len(c) or c[k] == " ")
        out.append(bool(re.sub(r"[/*\s]", "", rest)))
    return out


# --------------------------------------------------------------------------- diagrams

BORDER = re.compile(r"[-=_]{3,}")


def is_frameish(s):
    return "|" in s or BORDER.search(s) is not None


def find_diagrams(com):
    """Yield (top, bottom, left, right) for every board-shaped box in the comments.

    A board is a run of consecutive lines carrying `|` or a border, framed by a left
    and a right edge that most of its lines share. The frame is taken from the mode
    of each line's first and last `|` rather than from one border line, because real
    boards are not rectangles: connectors stick out, corners are notched, edges have
    a `|-|` where a plug sits.
    """
    n, i = len(com), 0
    while i < n:
        if not is_frameish(com[i]):
            i += 1
            continue
        j = i
        while j < n and is_frameish(com[j]):
            j += 1
        if j - i >= 5:
            f = _frame(com, i, j)
            if f:
                yield f
        i = j


def _frame(com, i, j):
    lefts, rights = collections.Counter(), collections.Counter()
    for k in range(i, j):
        s = com[k]
        if "|" in s:
            lefts[s.index("|")] += 1
            rights[s.rindex("|")] += 1
    if not lefts:
        return None
    # Edges wobble by a column where a line was hand-aligned; pool the neighbours.
    L, R = _mode_pooled(lefts), _mode_pooled(rights)
    if R - L < 20:
        return None
    rows = [k for k in range(i, j) if _edge_at(com[k], L) and _edge_at(com[k], R)]
    if len(rows) < 4:
        return None
    top, bottom = rows[0], rows[-1]
    # Take in the border lines just outside the first and last edged rows.
    if top > i and _border_spans(com[top - 1], L, R):
        top -= 1
    if bottom + 1 < j and _border_spans(com[bottom + 1], L, R):
        bottom += 1
    # The drawing is the whole run: a connector drawn proud of the frame is still
    # part of the board, and belongs in the art even though it is outside the box.
    return top, bottom, L, R, i, j - 1


def is_table(com, top, bottom, L, R, toks):
    """A ruled table -- a game list, a jumper chart, a ROM-size grid -- not a board.

    A table's rules run its whole height, so some column inside the frame carries
    a `|` on nearly every row. That alone is not enough: two boards drawn side by
    side do the same, and so does a board whose chips are drawn as tall outlines
    (funworld.cpp, namcos23.cpp). What a table has besides is table content -- game
    titles in mixed case, a `-+-` rule junction, or almost nothing a part could be.
    """
    rows = [com[k] for k in range(top + 1, bottom) if com[k].strip()]
    if len(rows) < 3:
        return False
    cols = collections.Counter()
    for s in rows:
        cols.update({c for c, ch in enumerate(s) if ch == "|" and L + 2 < c < R - 2})
    if not any(n >= 0.85 * len(rows) for n in cols.values()):
        return False
    words = [t[3] for t in toks if re.search(r"[A-Za-z]{2}", t[3]) and not FREQ.match(t[3])]
    lower = sum(1 for w in words if re.search(r"[a-z]", w)) / max(1, len(words))
    parts = sum(1 for t in toks if is_device_word(t[3]))
    junction = any(re.search(r"-\+-", com[k][L + 1:R]) for k in range(top + 1, bottom))
    return lower >= 0.4 or parts < 6 or junction


def _mode_pooled(counter):
    best, score = None, -1
    for c in sorted(counter):
        s = counter[c] + 0.5 * (counter.get(c - 1, 0) + counter.get(c + 1, 0))
        if s > score:
            best, score = c, s
    return best


def _edge_at(s, col):
    """A frame edge within two columns of col: a pipe, a corner, or a border reaching it."""
    for d in (0, -1, 1, -2, 2):
        c = col + d
        if 0 <= c < len(s) and s[c] in "|+.'":
            return True
    return _border_spans(s, col, col)


def _border_spans(s, a, b):
    return any(m.start() <= a + 2 and m.end() >= b - 2 for m in BORDER.finditer(s))


# --------------------------------------------------------------------------- tokens

WORD = re.compile(r"[^\s|]+")
DRAW_ONLY = re.compile(r"^[-=_+.'`~:*#<>^v/\\()\[\]{}]+$")


def tokens(com, top, bottom, L, R, phrases=()):
    """Every word inside the frame, as (row, c0, c1, text[, last row]).

    Two things are put back together that a plain split would break apart:

    - Text written down the edge of a board -- `|2` `|8` `|W` `|A` `|Y` -- is one
      label, the connector. It has to contain a letter: a column of single digits
      is grid numbering, not a word.
    - A legend key with a space in it (`IGS 025`, `Z80 CPU`) is one device where
      the diagram writes it on one line.
    """
    out = []
    singles = collections.defaultdict(list)       # column -> [(row, ch)]
    for r in range(top, bottom + 1):
        s = com[r]
        inner = list(s[:R] if len(s) > R else s)
        line = "".join(inner)
        for ph in phrases:
            for m in re.finditer(r"(?<![\w.])" + re.escape(ph) + r"(?![\w])", line):
                if m.start() > L:
                    out.append([r, m.start(), m.end(), ph])
                    inner[m.start():m.end()] = " " * len(ph)
            line = "".join(inner)
        for m in WORD.finditer(line):
            if m.start() <= L:
                # A word touching the left edge, as `|28WAY` or `|P`: keep what is inside.
                if m.end() <= L + 1:
                    continue
                c0, text = L + 1, line[L + 1:m.end()]
            else:
                c0, text = m.start(), m.group()
            lead = len(text) - len(text.lstrip("-=_.'`+"))
            text = text.strip("-=_.'`+")
            c0 += lead
            if not text or DRAW_ONLY.match(text):
                continue
            if len(text) == 1:
                singles[c0].append((r, text))
            out.append([r, c0, c0 + len(text), text])
    joined = set()
    for col, chars in singles.items():
        run = [chars[0]]
        for prev, cur in zip(chars, chars[1:]):
            if cur[0] == prev[0] + 1:
                run.append(cur)
                continue
            _vertical(run, col, out, joined)
            run = [cur]
        _vertical(run, col, out, joined)
    out = [t for t in out if (t[0], t[1]) not in joined or len(t[3]) > 1]
    out.sort(key=lambda t: (t[0], t[1]))
    return [tuple(t) for t in out]


def _vertical(run, col, out, joined):
    word = "".join(ch for _, ch in run)
    if len(run) >= 3 and re.search(r"[A-Za-z]", word):
        for r, _ in run:
            joined.add((r, col))
        out.append([run[0][0], col, col + 1, word, run[-1][0]])


# --------------------------------------------------------------------------- legend

LEGEND = re.compile(r"^(\s*)(\S(?:\S| (?! ))*?)\s+(?:-{1,2}|:|=)\s+(.*\S)?\s*$")
# A bracketed group member written without a dash: `SR14.L1 \`, `SR15.L2  | 27C128 ...`
BRACKETED = re.compile(r"^(\s*)(\S+)\s+([\\|/](?:\s.*)?)$")
NOTES = re.compile(r"^\s*notes?\s*:", re.I)


def legend(com, start, stop):
    """The `KEY - description` entries between start and stop, with their lines.

    Continuation lines (indented past the key) join the entry above. Grouped
    entries -- several keys bracketed by \\ | / against one description -- all
    take the description written beside the bracket.
    """
    entries, last, group = [], None, []
    seen_notes = False

    def close():
        text = " ".join(g["text"] for g in group if g["text"]).strip()
        for g in group:
            g["text"] = text
        group.clear()

    for k in range(start, stop):
        s = com[k]
        if not s.strip():
            last = None
            continue
        if NOTES.match(s):
            seen_notes = True
            rest = NOTES.sub("", s, count=1)
            if not rest.strip():
                continue
            s = " " * (len(s) - len(rest)) + rest
        m = LEGEND.match(s) or BRACKETED.match(s)
        key = m.group(2) if m else ""
        if m and len(key) <= 28 and not key.endswith(":") and \
                len(re.sub(r"[^A-Za-z0-9]", "", key)) >= 2:
            desc = (m.group(3) or "").strip()
            e = {"key": key, "text": desc, "line": k,
                 "col": s.index(desc) if desc else len(s)}
            bracket = re.match(r"^([\\|/])\s*(.*)$", desc)
            if bracket:
                e["text"] = bracket.group(2)
                group.append(e)
                if bracket.group(1) == "/":
                    close()
            elif group:
                close()              # an unclosed bracket ends where a plain entry starts
            entries.append(e)
            last = e
            continue
        if last is not None and len(s) - len(s.lstrip()) >= last["col"] - 2:
            last["text"] = (last["text"] + " " + s.strip()).strip()
            continue
        last = None
    if group:
        close()
    # Prose that happens to contain " - " is not a legend: keep runs of two or more,
    # or anything under a "Notes:" heading.
    if not seen_notes and len(entries) < 2:
        return []
    for e in entries:
        del e["col"]
    return entries


def expand_key(key):
    """'SWA/B' -> SWA, SWB; 'CN1/2' -> CN1, CN2; 'JP1-8' -> JP1..JP8; '2018/5814' both."""
    keys = {key}
    if "/" in key and not key.startswith("/") and not key.endswith("/"):
        parts = key.split("/")
        first = parts[0]
        keys.add(first)
        for p in parts[1:]:
            if len(p) < len(first) and re.match(r"^[A-Za-z0-9]+$", p):
                keys.add(first[:len(first) - len(p)] + p)
            keys.add(p)
    m = re.match(r"^([A-Za-z]+)(\d+)\s*-\s*(?:[A-Za-z]+)?(\d+)$", key)
    if m and 0 < int(m.group(3)) - int(m.group(2)) < 64:
        for v in range(int(m.group(2)), int(m.group(3)) + 1):
            keys.add(f"{m.group(1)}{v}")
    return {k.upper() for k in keys}


class Legend:
    def __init__(self, entries):
        self.exact, self.globs = {}, []
        for e in entries:
            k = e["key"]
            if "*" in k or "?" in k or re.search(r"\dx+$", k, re.I):
                pat = k if "*" in k or "?" in k else re.sub(r"x+$", "*", k, flags=re.I)
                # `*` alone, or `U*`, matches anything: a key has to say something.
                if len(re.sub(r"[^A-Za-z0-9]", "", pat)) >= 2:
                    self.globs.append((pat.upper(), e))
                continue
            for kk in expand_key(k):
                self.exact.setdefault(kk, e)

    def phrases(self):
        return sorted({k for k in self.exact if " " in k}, key=len, reverse=True)

    def find(self, token):
        t = token.upper()
        head, ref = split_designator(token)
        cands = [t, re.sub(r"\(\d+\)$", "", t)]
        if ref:
            cands += [head.upper(), ref]
        for c in cands:
            if c in self.exact:
                return self.exact[c]
        for pat, e in self.globs:
            if fnmatch.fnmatchcase(t, pat) or (ref and fnmatch.fnmatchcase(head.upper(), pat)):
                return e
        return None


# --------------------------------------------------------------------------- devices

FREQ = re.compile(r"^\d+(?:\.\d+)?\s*(?:[MK]HZ|HZ)$", re.I)
VOLTS = re.compile(r"^\d+(?:\.\d+)?V$", re.I)
DESIG = re.compile(r"^(?:IC|U)\d{1,4}[A-Z]?$|^[A-Z]{1,2}\d{1,2}[A-Z]?$|^\d{1,2}[A-Z]{1,3}$", re.I)
BARE_REF = re.compile(r"^(?:IC|U|CN|JP|J|DSW|SW|VR|X|XTAL|OSC|Y|BAT|BATT|BT|LED|TP|CON)\d{1,3}[A-Z]?$",
                      re.I)
GENERIC = {
    "PAL": "pld", "GAL": "pld", "PLD": "pld", "PEEL": "pld", "CPLD": "pld", "FPGA": "pld",
    "BATTERY": "battery", "BATT": "battery", "BAT": "battery",
    "VOL": "pot", "VOLUME": "pot", "VR": "pot",
    "JAMMA": "connector", "POWER": "connector", "SPEAKER": "connector",
    "RESET": "switch", "RESET_SW": "switch", "TEST_SW": "switch", "SERVICE_SW": "switch",
    "DSW": "dip", "DIPSW": "dip", "XTAL": "crystal", "OSC": "crystal",
    "EPROM": "rom", "SRAM": "ram", "DRAM": "ram",
}

# What a legend line says the part is. A legend reads "maker, part, what it is, then
# what it does here" -- `Mitsubishi M58725 2kBx8-bit SRAM (sound program RAM)` -- so
# the kind is the one named *first*, not the first in some fixed order: that SRAM is
# RAM, though it holds the sound program. Ties at one position go to the earlier row.
KIND_WORDS = [
    ("crystal", r"\b(?:crystal|xtal|oscillator|resonator|osc)\b"),
    ("dip", r"\bdip\s*-?\s*sw|\bdip ?switch|\b\d+[- ]position (?:dip|switch)|\bdipswitch"),
    ("other", r"\b(?:supervisor|reset chip|reset ic|reset generator|system reset|regulator|"
              r"watchdog|op-?amp|comparator|transistor|resistor array|level shifter|line driver|"
              r"darlington|opto-?coupler|real time clock|rtc|bus switch)\b"),
    ("rom", r"\b(?:e?eprom|rom|mask ?rom|prom|flash|otp|27c\d+|27\d{2,3}|29f\d+|mx29\w*|"
            r"bipolar)s?\b"),
    ("pld", r"\b(?:pal(?=\d|\b|ce)|gal\d|gal\b|pld|peel|cpld|fpga|epld|xilinx|altera|lattice|"
            r"actel|isplsi|epm\d)"),
    ("cpu", r"\b(?:cpu|microprocessor|micro-?controller|mcu|processor|z80|68000|68ec0\d0|6809|"
            r"6502|dsp|sh-?[1-4]|v[2-8]0|arm\d?|h8/|tms3[24]0)"),
    ("ram", r"\b(?:s?d?ram|sram|dram|vram|nvram|fram|sdram)s?\b"),
    ("sound", r"\b(?:sound|audio|psg|fm|adpcm|pcm|ssg|dac|ym\d|ymz|ay-?3|oki|msm\d|m6295|"
              r"amplifier|amp\b|speaker)"),
    ("custom", r"\bcustom\b|\basic\b|\bgate ?array\b"),
    ("connector", r"\b(?:connector|connection|connects|joins|joining|jamma|edge|header|plug|cn\d|"
                  r"\d+[- ]?way|\d+[- ]?pin conn)"),
    ("jumper", r"\b(?:jumper|wire link|solder pad|jp\d)"),
    ("battery", r"\bbattery\b"),
    ("switch", r"\b(?:push ?button|switch|reset)\b"),
    ("pot", r"\b(?:pot|potentiometer|volume)\b"),
    ("logic", r"\b74[a-z]{0,3}\d{2,4}\b|\bttl\b"),
]
KIND_RES = [(k, re.compile(p, re.I)) for k, p in KIND_WORDS]

# What a bare word on the diagram is, where no legend says. These are the part
# families that recur across the corpus; a word that fits none of them is still
# kept, as "other", if it is shaped like a part number.
TOKEN_KIND = [(k, re.compile(p, re.I)) for k, p in [
    ("crystal", FREQ.pattern),
    ("crystal", r"^(?:XTAL|OSC)\d*$|^X\d+$"),
    ("dip", r"^(?:DSW|DIPSW|DIP-?SW|SW[A-D]?)\d*[A-D]?(?:\(\d+\))?$"),
    ("connector", r"^(?:CN|CON|J)\d+[A-Z]?$|^\d+-?(?:WAY|PIN)$|^JAMMA$"),
    ("jumper", r"^JP\d+$"),
    ("pot", r"^VR\d+$|^VOL\d*$"),
    ("battery", r"^.*BATT.*$|^BT\d+$|^CR2032$"),
    ("cpu", r"^(?:Z80[A-Z]?|Z8400[A-Z]*|Z84C\d+\w*|68[0-9]{3}|MC680[0-9]0\w*|68EC0\d0|HD6309\w*|"
            r"TMP68\w+|6809E?|6502|68HC\d+\w*|8085A?|8088|8086|V[2-8]0|TMS3\d{4}\w*|SH-?[1-4]\w*|"
            r"SH7\d+\w*|HD6417\d+\w*|HD64\d+\w*|80C?3[12]\w*|8751\w*|8749\w*|8748\w*|I?8751\w*|"
            r"MC68705\w*|AT89C\d+\w*|UPD78C?\d+\w*|78C\d\d|IGS0?27A?|KONAMI\d*|HD63[0-9]{2}\w*|"
            r"ARM\d*|H8/\d+|MCU|CPU\d*|68301|R3000\w*|R4[0-9]00\w*|PPC\d+\w*|i960\w*)$"),
    ("sound", r"^(?:YM\d{3,4}[A-Z]?|YMF\d+\w*|YMZ\d+\w*|YAC\d+\w*|Y30\d\d\w*|AY-?3-?89\d{2}\w*|"
              r"M?6295|MSM\d{4}\w*|OKIM?\d+\w*|SN76\d{3}\w*|UPD7759\w*|K05\d{4}|ES\d{4}\w*|"
              r"TDA\d+\w*|LA\d{4}\w*|HA\d{4}\w*|UPC\d{4}\w*|TA\d{4}\w*|MB373\d\w*|YM3014\w*|"
              r"QSOUND|DSP16|UM3482\w*|M5205)$"),
    ("ram", r"^(?:2016|2018|2063|2111A?|2114|2148|2149|5101|5114|5814|6116|6148|6264|8464|43256|65256|"
            r"(?:N|M5M|D|HM|LH|KM|TMM|MB)?(?:41|42|44|48|51|53|62|61|81|84|341|514)\d{2,4}\w*|"
            r"TMM\d{4,6}\w*|M587\d{2}\w*|MB8\d{3,5}\w*|HM5\d{3,5}\w*|HM6\d{3,5}\w*|LH5\d{3,5}\w*|"
            r"LC3\d{3}\w*|UPD4\d{3,5}\w*|CY7C\d+\w*|KM\d{2}[A-Z]?\d+\w*|IS6\d\w*|IDT71\w*|"
            r"TC5\d{3,5}\w*|W24\d{3}\w*|HY5\d\w*|MT4\d\w*|M5\d{5}\w*|\d{2}LC\d+\w*|\d{2}C\d{3,4}\w*|"
            r"D?RAM\d*|SRAM\d*|VRAM\d*|NVRAM\d*|WRAM\d*|CRAM\d*|MEM\d+[A-Z]?)$"),
    ("pld", r"^(?:PAL|GAL|PEEL|PLD|EPM|PALCE|ATF|EPL|CPLD|MACH|QL|XPL|TPC|A10\d\d|XC\d)[\w.-]*$"),
    ("rom", r"^(?:(?:AM|M|TMS|MBM|HN|D|I|NM|M5L|TMM|HN4|MX)?27C?\d{2,4}\w*|28F\d+\w*|29F\d+\w*|"
            r"MX2\d+\w*|82S\d{3}\w*|63S\d{3}\w*|93C\d{2}\w*|(?:E?P?ROM|MROM|SROM)\d*[A-Z]?|"
            r"DIP\d{2}|MASKROM\d*|\d{1,3}M(?:BIT)?|(?:EPR|MPR|OPR)-?\d+\w*)$"),
    ("dip", r"^DIP\d$"),
    ("custom", r"^(?:IGS0\d{2}\w*|K0\d{5}\w*|315-\d{4}\w*|TC0\d{3}\w*|PC0\d{2}\w*|DECO\d+\w*|"
               r"SEI\d{3,4}\w*|GA\d{2,3}|CXD\d+\w*|GCU\d*|VU-\d+|CAT702|I4\d{3}|C\d{3})$"),
    ("logic", r"^(?:SN|GD|HD|DM|MC|M|TC|N|HCT)?74[A-Z]{0,4}\d{2,4}[A-Z]{0,3}$|^LS\d{2,3}[A-Z]?$|"
              r"^(?:CD|HEF|MC1|TC)?4[05](?<!45)\d\d(?:B\w*)?$|^(?:CD|HEF|TC)?45(?!58)\d\d(?:B\w*)?$"),
]]


def kind_of(token, text):
    """(kind, how): from the legend's words, else from the token's own shape, else None."""
    best = None
    for kind, pat in KIND_RES:
        m = pat.search(text or "")
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), kind)
    if best:
        return best[1], "legend"
    base = re.sub(r"\(\d+\)$", "", token)
    head, ref = split_designator(base)
    # A speed grade is not part of the family: TMM41464-10 is a TMM41464.
    for cand in (base, head, re.sub(r"-\d{1,3}[A-Z]?$", "", base)):
        if cand.upper() in GENERIC:
            return GENERIC[cand.upper()], "token"
        for kind, pat in TOKEN_KIND:
            if pat.match(cand):
                return kind, "token"
    if ref and head != base:
        # `SR08.A1`: a label and a location is how these diagrams write a socketed
        # chip with a sticker on it, which is nearly always a ROM. Nearly.
        return "rom", "label"
    return None, None


def split_designator(token):
    """'SR02.F2' -> ('SR02', 'F2'); 'A75-09.IC22' -> ('A75-09', 'IC22'); else (token, None)."""
    if FREQ.match(token) or VOLTS.match(token):
        return token, None
    if "." in token:
        # `BATT_3.6V` would split as position 6V, but for the voltage test. A bare
        # number is a position only after a label with a letter in it -- Taito's
        # `B77_20.54` is IC54 -- and never after a number, so 21.47 stays a crystal.
        head, tail = token.rsplit(".", 1)
        if head and (DESIG.match(tail) and not VOLTS.match(tail)
                     or re.match(r"^\d{1,3}$", tail) and re.search(r"[A-Za-z]", head)):
            return head, tail.upper()
    if BARE_REF.match(token):
        return token, token.upper()
    return token, None


# Shaped like a part number: letters and digits together, upper case (a lower-case
# `u` prefix as in uPD7759 is allowed), no slash. Rules out set names (`jking02`),
# wiring labels (`4/start`) and prose (`8-Liner`).
PARTISH = re.compile(r"^(?=.*\d)(?=.*[A-Z])[uμ]?[A-Z0-9][A-Z0-9_.()\-+]{2,23}$|^\d{4,6}[A-Z]?$")


def is_device_word(text):
    base = re.sub(r"\(\d+\)$", "", text)
    if FREQ.match(text) or base.upper() in GENERIC:
        return True
    if split_designator(text)[1]:
        return True
    if any(p.match(base) for _, p in TOKEN_KIND):
        return True
    return bool(PARTISH.match(base))


CORE = {"cpu", "rom", "ram", "pld", "sound", "custom", "crystal", "dip"}


# --------------------------------------------------------------------------- drivers

ROM_START = re.compile(r"^\s*ROM_START\s*\(\s*(\w+)\s*\)")
ROM_END = re.compile(r"^\s*ROM_END\b")
ROM_FILE = re.compile(r"^\s*ROM_\w*LOAD\w*\s*\(\s*\"([^\"]+)\"")
SYSTEM = re.compile(r"^\s*(?:GAME|GAMEL|GAMEB|CONS|COMP|SYST)\s*\(\s*[^,]+,\s*(\w+)\s*,\s*(\w+)\s*,(.*)$")


def driver_sets(raw):
    """ROM_START lines, {set: parent}, {set: full name} and {set: [rom file names]}."""
    starts, parents, names, files = [], {}, {}, {}
    cur = None
    for k, ln in enumerate(raw):
        m = ROM_START.match(ln)
        if m:
            cur = m.group(1)
            starts.append((k, cur))
            files.setdefault(cur, [])
            continue
        if cur and ROM_END.match(ln):
            cur = None
            continue
        if cur:
            m = ROM_FILE.match(ln)
            if m:
                files[cur].append(m.group(1))
            continue
        m = SYSTEM.match(ln)
        if m:
            parents[m.group(1)] = None if m.group(2) == "0" else m.group(2)
            quoted = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(3))
            if len(quoted) >= 2:
                names[m.group(1)] = quoted[1]
    return starts, parents, names, files


def family(root, parents):
    return [root] + sorted(s for s, p in parents.items() if p == root and s != root)


def anchor_set(cend, raw, iscode):
    """The set whose ROM_START follows this comment with only comments between, or None."""
    for k in range(cend + 1, len(raw)):
        if not iscode[k]:
            continue
        s = raw[k].strip()
        if s.startswith("#") and not s.startswith("#include"):
            continue
        m = ROM_START.match(raw[k])
        return m.group(1) if m else None
    return None


def comment_bounds(iscode, k):
    """First and last line of the comment run that line k sits in."""
    a = k
    while a > 0 and not iscode[a - 1]:
        a -= 1
    b = k
    while b + 1 < len(iscode) and not iscode[b + 1]:
        b += 1
    return a, b


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def title_of(name):
    """'Arkanoid (World, older)' -> 'arkanoid'."""
    return _norm(re.split(r"\s+\(|\s+/\s+", name)[0])


def titled_sets(com, floor, top, parents, names):
    """Parent sets whose title the lines above the diagram give, as 'Arkanoid / Taito 1986'.

    Only a line that is the whole title counts -- 'Arkanoid' or '1942, Capcom 1984'
    -- never one that merely contains it, so prose about a sequel does not attach.
    And it has to be one or two lines: a header that lists every game on a system
    board (Namco System 12 names twenty) is saying the board is shared, and picking
    the two titles that happen to sit nearest the drawing would be a guess.
    """
    titles = collections.defaultdict(set)
    for s, full in names.items():
        if parents.get(s) is None:
            t = title_of(full)
            if len(t) >= 3:
                titles[t].add(s)
    hit, lines = set(), 0
    for k in range(max(floor, top - 25), top):
        line = com[k].strip()
        if not line or len(line) > 70:
            continue
        for cand in (line, re.split(r",|\s+\(|\s+-\s+|\s{2,}", line)[0]):
            t = _norm(cand)
            if t in titles:
                hit |= titles[t]
                lines += 1
                break
    return sorted(hit) if lines <= 2 else []


def caption(com, top, floor):
    """The few lines just above a diagram that name the board: PCB numbers, 'Top board:'."""
    out, k, blanks = [], top - 1, 0
    while k >= floor and len(out) < 4:
        s = com[k].strip()
        if not s:
            blanks += 1
            if out:
                # One blank line may separate the PCB number from the board's name
                # ('Top board:' / '' / '84100-01A-03'); anything else past a gap is
                # the previous drawing's notes, which are not this board's caption.
                j = k - 1
                while j >= floor and not com[j].strip():
                    j -= 1
                nxt = com[j].strip() if j >= floor else ""
                if blanks > 1 or len(nxt) > 40 or not re.search(
                        r"\b(?:board|pcb|top|bottom|main|sub|daughter|rom|cpu|video|sound)\b", nxt, re.I):
                    break
            k -= 1
            continue
        if re.match(r"^[-=*_+.' ]+$", s):
            if out:
                break
            k -= 1
            continue
        if "|" in com[k] or len(s) > 80 or len(s.split()) >= 8 or NOTES.match(s) \
                or LEGEND.match(com[k]):
            break             # a drawing, a paragraph, or the notes of the one before
        out.append(s)
        blanks = 0
        if LAYOUT_RE.search(s):
            break
        k -= 1
    return list(reversed(out))


def dumps_for(ref, sets, files):
    """ROM files in these sets whose name ends in this position: 'u29', 'pm1_prg1.6e'."""
    r = ref.lower()
    out = []
    for s in sets:
        for f in files.get(s, []):
            low = f.lower()
            stem = low.rsplit(".", 1)
            if low == r or (len(stem) == 2 and (stem[1] == r or stem[0].endswith("_" + r)
                                                or stem[0].endswith("-" + r))) \
                    or low.endswith("." + r) or low.endswith("_" + r) or low.endswith("-" + r):
                out.append(f)
    return sorted(set(out))


# --------------------------------------------------------------------------- one file

def parse_file(path, rel):
    text = open(path, encoding="utf-8", errors="replace").read()
    head = text[:600]
    m = re.search(r"license:\s*(\S+)", head)
    licence = m.group(1) if m else None
    m = re.search(r"copyright-holders:\s*(.+)", head)
    holders = m.group(1).strip() if m else None
    info = {"src": rel, "licence": licence, "copyright": holders, "layouts": [], "parents": {}}
    if licence not in PERMITTED:
        return info
    raw = text.split("\n")
    com = comment_lines(text)
    iscode = code_mask(raw, com)
    starts, parents, names, files = driver_sets(raw)
    info["parents"] = parents
    hdr = next((k for k, c in enumerate(iscode) if c), len(iscode))

    found = []
    diagrams = list(find_diagrams(com))
    for idx, (top, bottom, L, R, first, last) in enumerate(diagrams):
        a, b = comment_bounds(iscode, top)
        nxt = diagrams[idx + 1][4] if idx + 1 < len(diagrams) else len(com)
        entries = legend(com, last + 1, min(nxt, b + 1, last + 160))
        found.append({"top": top, "bottom": bottom, "L": L, "R": R, "first": first,
                      "last": last, "a": a, "b": b, "entries": entries})

    for d in found:
        # A legend usually follows its own diagram, but the notes for a pair of boards
        # may follow only the second. Look a word up in its own legend first, then in
        # the legends of the other diagrams in the same comment.
        own = Legend(d["entries"])
        near = Legend([e for o in found if o is not d and o["b"] == d["b"] for e in o["entries"]])
        toks = tokens(com, d["top"], d["bottom"], d["L"], d["R"],
                      phrases=own.phrases() + near.phrases())
        if is_table(com, d["top"], d["bottom"], d["L"], d["R"], toks):
            continue
        art = [com[k].rstrip() for k in range(d["first"], d["last"] + 1)]
        indent = min((len(x) - len(x.lstrip()) for x in art if x.strip()), default=0)
        indent = min(indent, d["L"])
        rows, cols = d["bottom"] - d["top"], d["R"] - d["L"]
        devices = []
        for t in toks:
            r, c0, c1, word = t[:4]
            r1 = t[4] if len(t) > 4 else r
            e = own.find(word) or near.find(word)
            if not e and not is_device_word(word):
                continue
            _, ref = split_designator(word)
            kind, how = kind_of(word, e["text"] if e else "")
            dev = {"label": word}
            if ref:
                dev["ref"] = ref
            if e:
                dev["part"] = e["text"]
                dev["legend"] = e["line"] + 1
            # A word shaped like a part number with nothing to say what it is stays
            # on the map as "other": it is on the board, and that is all the diagram
            # says about it.
            dev["kind"] = kind or "other"
            if how == "label":
                dev["guess"] = 1
            dev["x"] = round(((c0 + c1) / 2 - d["L"]) / cols, 3)
            dev["y"] = round(((r + r1) / 2 - d["top"]) / max(rows, 1), 3)
            dev["line"] = r + 1
            # Where the label sits in `art`: row, first and past-last column, and the
            # last row when it is written down the edge.
            dev["at"] = [r - d["first"], c0 - indent, c1 - indent] + ([r1 - d["first"]] if r1 != r else [])
            devices.append(dev)
        core = [v for v in devices if v["kind"] in CORE]
        if len(core) < 3 and not (len(core) >= 2 and any(v["kind"] == "cpu" for v in core)):
            continue          # a table, a pinout, a DIP sheet or a sprite format: not a board

        anchor = anchor_set(d["b"], raw, iscode)
        prev = info["layouts"][-1] if info["layouts"] else None
        if anchor:
            scope, sets = "set", family(anchor, parents)
        else:
            # Look no further up than the drawing before, whose own notes are its own.
            floor = max(d["a"], prev["end"] if prev and prev["_b"] == d["b"] else 0)
            roots = titled_sets(com, floor, d["first"], parents, names)
            if roots:
                scope, sets = "title", [s for r in roots for s in family(r, parents)]
            elif prev and prev["_b"] == d["b"] and prev["scope"] == "title" and not any(
                    LAYOUT_RE.search(com[k]) for k in range(prev["end"], d["first"])):
                # The bottom board under the same heading as the top one: one game's
                # two boards, so the second is that game's too. A new "PCB Layout"
                # heading in between means a new game, and nothing is inherited.
                scope, sets = "title", prev["sets"]
            else:
                scope, sets = ("driver" if d["first"] < hdr else "file"), []

        # The romset is a second, independent record of where a ROM sits: MAME names
        # a dump after its socket. Where a device's position matches a file the set
        # loads, say so -- and, when the layout is tied to that set, that settles what
        # the device is. A driver-wide layout is checked against every set in the
        # driver, which is weaker: another set's U5 may be on another board.
        pool = sets or [s for _, s in starts]
        checked = 0
        for v in devices:
            if not v.get("ref"):
                continue
            hits = dumps_for(v["ref"], pool, files)
            if hits:
                v["dump"] = hits[:4]
                checked += 1
                if sets and (v["kind"] == "other" or v.get("guess")):
                    v["kind"] = "rom"
                    v.pop("guess", None)

        found_caption = caption(com, d["first"], max(d["a"], d["first"] - 12))
        info["layouts"].append({
            "_b": d["b"],
            "line": d["first"] + 1, "end": d["last"] + 1,
            "caption": found_caption,
            "scope": scope, "sets": sets,
            # MAME's own name for the set, for a layout whose set the site lacks.
            "game": names.get(sets[0]) if sets else None,
            # A board documented for a clone is still a board of its parent's game;
            # the parent's page can say so, as a variant.
            "parent": parents.get(anchor) if anchor else None,
            "cols": cols, "rows": rows,
            "art": [x[indent:] for x in art],
            "devices": devices,
            "dumpsMatched": checked,
            "notes": [{"key": e["key"], "text": e["text"], "line": e["line"] + 1}
                      for e in d["entries"]],
        })
    for lay in info["layouts"]:
        del lay["_b"]
    return info


# --------------------------------------------------------------------------- main

def layouts_for(rom, parent, lays):
    """{layout id: [how]} for one machine, from its driver's layouts.

    set      the layout is tied to this set, or to the set this one is a clone of
    variant  it is tied to a clone of this set: a board of this game, documented
             for another release of it
    general  it is in the driver's notes and tied to no set
    Mirrored in web/js/app.js (layoutsFor); change both.
    """
    out = {}
    for lay in lays:
        how = []
        if rom in lay["sets"] or (parent and parent in lay["sets"]):
            how.append("set")
        elif lay.get("parent") == rom:
            how.append("variant")
        elif lay["scope"] in ("driver", "file"):
            how.append("general")
        if how:
            out[lay["id"]] = how
    return out


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout.strip() or None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mame", help="a MAME checkout (the directory holding src/mame)")
    ap.add_argument("--tag", help="release tag, e.g. mame0289 (read from git if absent)")
    ap.add_argument("--only", help="parse one driver file (relative to src/mame) and print it")
    a = ap.parse_args()

    src = os.path.join(a.mame, "src", "mame")
    if a.only:
        json.dump(parse_file(os.path.join(src, a.only), a.only), sys.stdout,
                  indent=1, ensure_ascii=False)
        return

    commit = git("-C", a.mame, "rev-parse", "HEAD")
    tag = a.tag or git("-C", a.mame, "describe", "--tags", "--exact-match")
    if not tag:
        raise SystemExit("not a release tag checkout; pass --tag")

    files = []
    for d, _, fs in os.walk(src):
        for f in fs:
            if f.endswith(".cpp"):
                p = os.path.join(d, f)
                if LAYOUT_RE.search(open(p, encoding="utf-8", errors="replace").read()):
                    files.append(os.path.relpath(p, src).replace(os.sep, "/"))
    files.sort()

    mame = json.load(open(os.path.join(ROOT, "data", "mame", "machines.json")))
    site = mame["machines"]
    machines = {m["s"]: m for m in json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))}
    rom_to_slug = {}
    mdir = os.path.join(ROOT, "web", "data", "machine")
    for p in os.listdir(mdir):
        rec = json.load(open(os.path.join(mdir, p)))
        if rec.get("rom"):
            rom_to_slug[rec["rom"]] = rec["slug"]
    by_src = collections.defaultdict(list)
    for rom, rec in site.items():
        if rec.get("src"):
            by_src[rec["src"]].append(rom)

    shards = collections.defaultdict(dict)
    index, skipped, empty, offsite = [], [], [], collections.Counter()
    for rel in files:
        info = parse_file(os.path.join(src, rel), rel)
        if info["licence"] not in PERMITTED:
            skipped.append({"src": rel, "licence": info["licence"]})
            continue
        if not info["layouts"]:
            empty.append(rel)
            continue
        if not any(r in rom_to_slug for r in by_src.get(rel, [])):
            # Computers, gambling boards, consoles the site does not list: parsed and
            # counted, not published, since nothing here would ever link to them.
            offsite[rel] = len(info["layouts"])
            continue
        dirn, stem = rel.split("/", 1)[0], rel.rsplit("/", 1)[-1][:-4]
        # What the list calls a layout that names no machine: the driver's own
        # machines, by their most common maker and earliest year.
        mine = [machines[rom_to_slug[r]] for r in by_src[rel] if rom_to_slug.get(r) in machines]
        mfr = collections.Counter(m.get("m") for m in mine if m.get("m")).most_common(1)
        years = sorted(m.get("y") for m in mine if (m.get("y") or "").isdigit())
        recs = []
        for n, lay in enumerate(info["layouts"], 1):
            lid = f"{dirn}/{stem}/{n}"
            # The site's own slug for each set, where the site has the machine.
            slugs = [rom_to_slug[s] for s in lay["sets"] if s in rom_to_slug]
            first = machines.get(slugs[0]) if slugs else None
            recs.append({"id": lid, "src": rel, "n": n, "tag": tag, "commit": commit,
                         "licence": info["licence"], "copyright": info["copyright"],
                         "slugs": slugs,
                         "machines": [[s, machines[s]["n"], machines[s].get("y", "")]
                                      for s in slugs if s in machines],
                         **lay})
            kinds = collections.Counter(v["kind"] for v in lay["devices"])
            index.append({
                "id": lid, "src": rel, "line": lay["line"],
                "name": first["n"] if first else lay["game"],
                "mfr": (first or {}).get("m") or (mfr[0][0] if mfr else ""),
                "year": (first or {}).get("y") or (years[0] if years else ""),
                "caption": " · ".join(lay["caption"])[:140],
                "scope": lay["scope"], "slugs": slugs,
                "devices": len(lay["devices"]),
                "withPart": sum(1 for v in lay["devices"] if v.get("part")),
                "withRef": sum(1 for v in lay["devices"] if v.get("ref")),
                "dumps": lay["dumpsMatched"],
                "kinds": dict(kinds.most_common()),
            })
        shards[dirn][rel] = recs

    os.makedirs(OUT_DIR, exist_ok=True)
    for f in os.listdir(OUT_DIR):
        if f.endswith(".json"):
            os.remove(os.path.join(OUT_DIR, f))
    for dirn, recs in sorted(shards.items()):
        with open(os.path.join(OUT_DIR, dirn + ".json"), "w") as f:
            json.dump(recs, f, ensure_ascii=False, separators=(",", ":"))

    # ---- measure, against the machines the site lists, by the rule the machine
    # page applies (web/js/app.js, layoutsFor): the page reads its own driver's
    # layouts and sorts them into these.
    by_file = collections.defaultdict(list)
    for dirn, recs in shards.items():
        for rel, lays in recs.items():
            by_file[rel] = lays
    reach = collections.defaultdict(set)      # how -> slugs
    for rom, rec in site.items():
        slug = rom_to_slug.get(rom)
        if not slug or rec.get("src") not in by_file:
            continue
        reach["driver"].add(slug)
        for how in layouts_for(rom, rec.get("parent"), by_file[rec["src"]]).values():
            for h in how:
                reach[h].add(slug)
    reach_set = reach["set"]
    reach_any = reach["set"] | reach["variant"] | reach["general"]
    with_layout = set(by_file)
    mfr = collections.Counter((machines.get(s) or {}).get("m", "?") for s in reach_any)
    stats = {
        "mame": {"tag": tag, "commit": commit},
        "files_mentioning_pcb_layout": len(files),
        "files_skipped_for_licence": len(skipped),
        "skipped": skipped,
        "files_with_no_board_found": len(empty),
        "layouts_parsed": len(index) + sum(offsite.values()),
        "layouts_in_drivers_with_no_site_machine": sum(offsite.values()),
        "files_with_no_site_machine": len(offsite),
        "files_with_layouts": len(with_layout),
        "layouts": len(index),
        "layouts_by_scope": dict(collections.Counter(r["scope"] for r in index).most_common()),
        "devices": sum(r["devices"] for r in index),
        "devices_with_legend_part": sum(r["withPart"] for r in index),
        "devices_with_designator": sum(r["withRef"] for r in index),
        "devices_matching_a_romset_file": sum(r["dumps"] for r in index),
        "devices_by_kind": dict(sum((collections.Counter(r["kinds"]) for r in index),
                                    collections.Counter()).most_common()),
        "site_machines_in_a_driver_with_a_layout": len(reach["driver"]),
        "site_machines_shown_a_layout": len(reach_any),
        "  for_their_own_set_or_its_parent": len(reach_set),
        "  for_one_of_their_clones_only": len(reach["variant"] - reach_set),
        "  from_driver_notes_only": len(reach["general"] - reach_set - reach["variant"]),
        "of_those_undocumented": sum(1 for s in reach_any if not (machines.get(s) or {}).get("d")),
        "of_those_atari": sum(1 for s in reach_any if "atari" in (machines.get(s) or {}).get("m", "").lower()),
        "of_those_with_a_board_map": None,
        "manufacturers": dict(mfr.most_common(20)),
    }
    boards = json.load(open(os.path.join(ROOT, "data", "boards.json")))
    board_machines = {b.get("machine") or b.get("slug") for b in boards}
    stats["of_those_with_a_board_map"] = len(reach_any & board_machines)
    json.dump({"stats": stats, "layouts": index}, open(OUT_INDEX, "w"),
              ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in stats.items() if k != "skipped"}, indent=1, ensure_ascii=False))
    print("skipped for licence: " + ", ".join(f"{s['src']} ({s['licence']})" for s in skipped))


if __name__ == "__main__":
    main()
