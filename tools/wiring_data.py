"""A generated wiring view for a machine page, from a connector standard.

Nothing here is read off a game's own wiring diagram. It joins three things:

  data/wiring/library.json   connector standards, pin by pin, with sources
  data/wiring/drivers.json   which standard each MAME driver's boards use,
                             with the line in the driver that says so
                             (tools/tag_harness.py)
  the machine record         MAME's players, coin slots and controls

and places each of the game's controls on the pin the standard gives it. What
the standard has no pin for is listed as not placed rather than guessed. The
page says, every time, that the view is generated.

build_index.py applies it on a full rebuild and build_assets.py --wiring-only
as a targeted publish, so the two agree.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "data", "wiring", "library.json")
DRIVERS = os.path.join(ROOT, "data", "wiring", "drivers.json")
MAME = os.path.join(ROOT, "data", "mame", "machines.json")

# Control types that are never on a JAMMA-style harness in a standard way.
# A gambling or mahjong board with a "JAMMA edge" wires its own assignment
# onto it (MAME says so in several drivers), and a keyboard is a computer.
EXCLUDE = {"gambling", "mahjong", "hanafuda", "keyboard", "keypad", "mouse"}
# Control types that are real but have no standard pin: listed as not placed.
OFF_EDGE = {"dial": "Dial", "trackball": "Trackball", "paddle": "Paddle", "pedal": "Pedal",
            "lightgun": "Light gun", "stick": "Analog stick", "positional": "Positional control",
            "doublejoy": "Twin joysticks"}
DIRS = {"8": "udlr", "4": "udlr", "16": "udlr", "5 (half8)": "udlr", "3 (half4)": "udlr",
        "2": "lr", "vertical2": "ud"}
DIR_NAMES = {"u": "up", "d": "down", "l": "left", "r": "right"}
# JAMMA was published on 1 January 1986. A driver-comment tag is only taken
# for games from 1985 on: a file that mentions a JAMMA bootleg also holds the
# 1980 original it was copied from.
FIRST_YEAR = 1985

_lib = _drivers = _src = None


def load():
    global _lib, _drivers, _src
    if _lib is None:
        _lib = json.load(open(LIB))
        _drivers = json.load(open(DRIVERS))["drivers"] if os.path.exists(DRIVERS) else {}
        _src = {rom: rec.get("src") for rom, rec in json.load(open(MAME))["machines"].items()} \
            if os.path.exists(MAME) else {}
    return _lib, _drivers, _src


def _year(rec):
    m = re.match(r"\s*(\d{4})", str(rec.get("year") or ""))
    return int(m.group(1)) if m else None


def _variant(std, players):
    for v in std["variants"]:
        lo, hi = v.get("players", [0, 99])
        if lo <= players <= hi:
            return v
    return std["variants"][0]


def _span(a, b):
    return str(a) if a == b else f"{a}-{b}"


def generate(rec):
    """The `wiring` block for one machine record, or None when there is none."""
    lib, drivers, src = load()
    if rec.get("kind"):
        return None
    drv = src.get(rec.get("rom") or "")
    tag = drivers.get(drv or "")
    if not tag:
        return None
    inp = rec.get("input") or {}
    players = inp.get("p") or 0
    ctrls = inp.get("ctrl") or []
    types = {c.get("type") for c in ctrls}
    if not players or types & EXCLUDE:
        return None
    if tag["basis"] == "comment":
        year = _year(rec)
        if year is None or year < FIRST_YEAR:
            return None
    if tag["std"] == "cps1" and "CPS Changer" in (rec.get("name") or ""):
        return None                       # the consumer unit, not a JAMMA board

    std = lib["standards"][tag["std"]]
    var = _variant(std, players)
    have = {}
    for cid in var["connectors"]:
        for row in lib["connectors"][cid]["rows"]:
            for p in row:
                have.setdefault(p["s"], []).append(p)

    dirs = set()
    for c in ctrls:
        if c.get("type") == "joy":
            dirs |= set(DIRS.get(str(c.get("ways")), ""))
    buttons = max([c.get("btn") or 0 for c in ctrls if c.get("type") not in EXCLUDE] or [0])
    coins = inp.get("co") or 0

    use, miss = [], []
    lost_players = [n for n in range(1, players + 1) if f"p{n}.start" not in have]
    for n in range(1, players + 1):
        if n in lost_players:
            continue
        want = [f"p{n}.start"] + [f"p{n}.{DIR_NAMES[d]}" for d in "udlr" if d in dirs]
        use += [s for s in want if s in have]
        lost = [b for b in range(1, buttons + 1) if f"p{n}.b{b}" not in have]
        use += [f"p{n}.b{b}" for b in range(1, buttons + 1) if b not in lost]
        if lost:
            miss.append(f"Player {n} button{'s' if len(lost) > 1 else ''} {_span(lost[0], lost[-1])}")
    if lost_players:
        miss.insert(0, f"Player{'s' if len(lost_players) > 1 else ''} "
                       f"{_span(lost_players[0], lost_players[-1])} controls")
    placed_coins = [k for k in range(1, coins + 1) if f"coin{k}" in have]
    use += [f"coin{k}" for k in placed_coins]
    if coins > len(placed_coins):
        miss.append(f"Coin slot{'s' if coins - len(placed_coins) > 1 else ''} "
                    f"{_span(len(placed_coins) + 1, coins)}")
    for t in sorted(types):
        if t in OFF_EDGE:
            miss.append(OFF_EDGE[t])
    if any(c.get("type") == "joy" and str(c.get("ways")) in ("1", "strange2") for c in ctrls):
        miss.append("Joystick (MAME records an unusual direction set)")

    block = {"std": tag["std"], "var": var["id"], "basis": tag["basis"], "drv": drv,
             "ev": {"file": tag["file"], "line": tag["line"], "text": tag["text"]},
             "use": use}
    if miss:
        block["miss"] = miss
    wd = [d["id"] for d in rec.get("docs") or [] if d.get("type") == "Wiring Diagram"]
    if wd:
        block["doc"] = wd[0]
    return block


def apply(rec):
    """Set or clear `wiring` on one machine record, in place. True if it changed."""
    before = json.dumps(rec.get("wiring"), sort_keys=True)
    block = generate(rec)
    if block is None:
        rec.pop("wiring", None)
    else:
        rec["wiring"] = block
    return json.dumps(rec.get("wiring"), sort_keys=True) != before


def library():
    """The published library: connectors and standards, for the page to draw."""
    lib, _, _ = load()
    return {k: lib[k] for k in ("sources", "connectors", "standards")}


# ---- wiring pages already in the corpus ------------------------------------
#
# Only 51 machines have a whole document filed as a wiring diagram, but many
# manuals carry one as a page or two -- a harness chart with its wire colours,
# a cabinet wiring drawing. Those are read, not generated, so the page points
# at them above anything this module makes. A page counts when two things
# agree, the same rule build_drawings.py uses for drawings:
#
#   titled   a heading near the top of the page names a wiring diagram,
#            harness or connector pin-out, and the page carries evidence of
#            one: wire colours, a solder/parts side, or a drawing's score
#   striped  six or more two-colour wire codes (WHT-BLK, ORG/BRN) on a page
#            that is a drawing or names pins or sides -- a Williams cabinet
#            sheet has no title the OCR can read, but its stripes survive
#
# Measured over the 65,582 published pages: 287 titled and 66 striped, in 253
# documents. A sample of 50 read by hand found two false hits, both
# troubleshooting tables that quote wire colours, which NOT_STRIPED now drops.
TITLE = re.compile(r"\b(wiring\s+diagram|wiring\s+harness|harness\s+(?:diagram|wiring)|interconnect(?:ion)?\s+diagram|"
                   r"cabinet\s+wiring|main\s+wiring|jamma\s+(?:harness|connector|pin\s*-?\s*out|wiring)|"
                   r"edge\s+connector\s+pin\s*-?\s*outs?|connector\s+pin\s*-?\s*outs?|pin\s*-?\s*out\s+information)\b", re.I)
NOT_TITLE = re.compile(r"contents|\.{4,}|\.\.\s|\brefer\s+to\b|\bsee\s+(the\s+)?(cabinet|wiring|figure)|\bcheck\b|"
                       r"llustrations|figures\b", re.I)
NOT_STRIPED = re.compile(r"\btable\s+\d|initial\s+tests|symptom", re.I)
_CODE = r"(?:BLK|WHT|RED|GRN|BLU|YEL|ORN|ORG|BRN|VIO|PUR|GRY|GRA|PNK)"
STRIPE = re.compile(rf"\b{_CODE}\s*[-/]\s*{_CODE}\b")
COLOUR = re.compile(rf"\b{_CODE}\b|\b(?:BLACK|WHITE|GREEN|BLUE|YELLOW|ORANGE|BROWN|PURPLE|VIOLET|GREY|GRAY)\b")
SIDES = re.compile(r"\b(solder|parts|component)\s+side\b", re.I)
PINWORD = re.compile(r"\bpin\b|\bedge\s+conn|\bconnector\b", re.I)


def page_kind(p):
    """"titled", "striped" or None for one published page."""
    blocks = p.get("blocks") or []
    text = " ".join(b.get("t", "") for b in blocks)
    head = " ".join(b.get("t", "")[:160] for b in blocks[:3])
    starts = " | ".join(b.get("t", "")[:70] for b in blocks[:3])
    drawn = bool(p.get("draw") or p.get("noise"))
    sides = bool(SIDES.search(text))
    stripes = len(STRIPE.findall(text))
    if TITLE.search(starts) and not NOT_TITLE.search(head):
        if stripes >= 2 or len(COLOUR.findall(text)) >= 6 or sides or drawn:
            return "titled"
    if stripes >= 6 and (drawn or sides or PINWORD.search(text)) and not NOT_STRIPED.search(head):
        return "striped"
    return None


def doc_pages(doc):
    """[(page, kind, heading)] of the wiring pages in one published document.

    The heading is the block the title was found in, so the link reads
    "KICKER: WIRING HARNESS". A page found by its wire colours alone has no
    heading the OCR could read, and gets none rather than a line of debris.
    """
    out = []
    for p in doc.get("pages") or []:
        k = page_kind(p)
        if not k:
            continue
        head = ""
        if k == "titled":
            for b in (p.get("blocks") or [])[:3]:
                t = " ".join(b.get("t", "").split())
                if TITLE.search(t[:70]):
                    head = t[:80]
                    break
        out.append((p["n"], k, head))
    return out


def apply_pages(rec, pages_by_doc):
    """Set or clear `wpages` on a machine record from {doc id: doc_pages(...)}."""
    before = json.dumps(rec.get("wpages"), sort_keys=True)
    found = [{"d": d["id"], "p": n, "k": k, "h": h}
             for d in rec.get("docs") or [] for n, k, h in pages_by_doc.get(d["id"], [])]
    if found:
        rec["wpages"] = found
    else:
        rec.pop("wpages", None)
    return json.dumps(rec.get("wpages"), sort_keys=True) != before
