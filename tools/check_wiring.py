#!/usr/bin/env python3
"""Check data/wiring/library.json against the pin tables it was read from.

Two checks, and they answer different questions:

  transcription  Every connector taken from a MAME pin table is re-read from
                 that table here and compared pin for pin. A pin the library
                 has that the source does not say, or says differently, is a
                 typing error in the library -- unless the connector logs it
                 as a conflict. Exits non-zero on any.

  consensus      The generic JAMMA connector, which comes from the 1986
                 standard, is compared against every independent JAMMA pin
                 table in MAME's driver comments plus the measured cabinet in
                 arcade-docs. Boards use pins for their own controls (a
                 trackball on the joystick pins, an accelerator on button 1),
                 so a label this tool cannot read as a standard signal counts
                 as the board's own use, not a disagreement. What it reports
                 is how many tables agree, pin by pin, and every table that
                 names a standard signal on a different pin.

  python3 tools/check_wiring.py /path/to/mame/src/mame [/path/to/arcade-docs]

The MAME tree is the same sparse 0.289 checkout tag_harness.py reads.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "data", "wiring", "library.json")
LETTERS = "ABCDEFHJKLMNPRSTUVWXYZabcdef"     # JAMMA solder side, 1..28


def norm(label, side=None):
    """A pin label as a library signal id, or None when it is a board's own use.

    `side` is the player a bare "Start" or "Up" belongs to when the label
    does not say (the parts side is player 1 on every JAMMA table).
    """
    t = label.strip().lower()
    t = re.sub(r"[-]{2,}", " ", t).strip()
    t = t.replace("vdc", "v").replace("  ", " ")
    if t in ("", "nc", "n/c", "not used", "(not used)", "unused", "-", "---"):
        return "nc"
    if "key" in t:
        return "key"
    if re.fullmatch(r"(gnd|ground|0v)", t):
        return "gnd"
    if re.fullmatch(r"\+?5v?", t) or t == "+5":
        return "+5v"
    if re.fullmatch(r"-5v?", t):
        return "-5v"
    if re.fullmatch(r"\+?12v?", t) or t == "+12":
        return "+12v"
    if re.fullmatch(r"-5v? \(not used\)", t):
        return "-5v"
    m = re.fullmatch(r"(coin )?(counter|meter)( #)? ?([12])?", t)
    if m:
        return f"counter{m.group(4) or ''}" if m.group(4) else "counter"
    m = re.fullmatch(r"coin lock( ?out)? ?([12])?", t)
    if m:
        return f"lockout{m.group(2)}" if m.group(2) else "lockout"
    m = re.fullmatch(r"(lockout) ([12])", t)
    if m:
        return f"lockout{m.group(2)}"
    if re.fullmatch(r"(l |r )?speaker ?\(?\+\)?|spk\+|speaker pos", t):
        return "spk+"
    if re.fullmatch(r"(l |r )?speaker ?\(?-\)?|spk-|speaker neg", t):
        return "spk-"
    if t in ("l speaker", "left speaker"):
        return "spk.l"
    if t in ("r speaker", "right speaker"):
        return "spk.r"
    if t == "speaker":
        return "spk"
    if t in ("audio gnd", "audio (gnd)"):
        return "audio.gnd"
    if t in ("audio+", "audio (+)", "mono audio"):
        return "audio+"
    m = re.fullmatch(r"(video )?(red|green|blue)", t)
    if m:
        return "video." + m.group(2)[0]
    if re.fullmatch(r"(video )?(composite )?sync|syn|vsync", t):
        return "video.sync"
    if t in ("video gnd", "video ground", "vgnd"):
        return "video.gnd"
    if re.fullmatch(r"service( switch| sw| button)?", t):
        return "service"
    if re.fullmatch(r"test( switch| sw| button)?", t):
        return "test"
    if re.fullmatch(r"tilt( switch| sw)?", t):
        return "tilt"
    m = re.fullmatch(r"coin( switch)?( #)? ?([1-4ab])( [12]p)?", t)
    if m:
        return "coin" + {"a": "1", "b": "2"}.get(m.group(3), m.group(3))
    m = re.fullmatch(r"coin ([1-4]) ([12])p", t)
    if m:
        return "coin" + m.group(1)
    if t == "coin switch" or t == "coin1":
        return "coin1"
    if t == "coin2":
        return "coin2"
    # players: "player 1 up", "1p up", "p1 up", "2up button 6", "start player 2"
    p = None
    m = re.search(r"\b(?:player|p) ?([1-4])\b|\b([1-4]) ?(?:p|up)\b", t)
    if m:
        p = m.group(1) or m.group(2)
        t = (t[:m.start()] + t[m.end():]).strip()
        if t == "coin lock":                    # cps2.cpp's "3Up Coin Lock"
            return f"lockout{p}"
        if t == "coin":
            return f"coin{p}"
    m = re.fullmatch(r"(start)( switch| sw)?( player)?( ?[12])?", t)
    if m:
        return f"p{p or (m.group(4) or '').strip() or side}.start"
    if t in ("up", "down", "left", "right"):
        return f"p{p or side}.{t}"
    m = re.fullmatch(r"(?:button|btn|push|b) ?([1-6])|button ([a-d])", t)
    if m:
        n = m.group(1) or str("abcd".index(m.group(2)) + 1)
        return f"p{p or side}.b{n}"
    if t in ("a", "b", "c", "d"):
        return f"p{p or side}.b{'abcd'.index(t) + 1}"
    if t == "shoot":
        return f"p{p or side}.b1"
    if t in ("sel up", "select up"):
        return "select.up"
    if t in ("sel down", "select down"):
        return "select.down"
    if t == "volume down":
        return "vol.down"
    if t == "volume up":
        return "vol.up"
    return None


# ---- table readers ---------------------------------------------------------

def lines_after(path, anchor, count=40):
    lines = open(path, encoding="latin-1").read().split("\n")
    rx = re.compile(anchor)
    for i, l in enumerate(lines):
        if rx.search(l):
            return i + 1, lines[i + 1:i + 1 + count]
    raise SystemExit(f"anchor {anchor!r} not in {path}")


def read_bar(path, anchor):
    """`solder | L | n | parts`, the format most MAME JAMMA tables use."""
    first, rows = lines_after(path, anchor)
    out = {}
    for l in rows:
        m = re.match(r"^\s*(.*?)\s*\|\s*([A-Za-z])\s*\|\s*(\d+)\s*\|\s*(.*?)\s*$", l)
        if m:
            out[m.group(2)] = m.group(1)
            out[m.group(3)] = m.group(4)
    return first, out


def read_cps_edge(path, anchor):
    """`parts NN L solder   <extra connector>`, cps2.cpp and cps3.cpp."""
    first, rows = lines_after(path, anchor, 34)
    out = {}
    for l in rows:
        m = re.match(r"^\s*(.*?)\s+(\d\d)\s+([A-Za-f])(?:\s{1,4}(\S.*?))?(?:\s{3,}|$)", l)
        if m and 1 <= int(m.group(2)) <= 28:
            out[str(int(m.group(2)))] = m.group(1)
            out[m.group(3)] = m.group(4) or ""
    return first, out


def read_cps_header(lines, start_col=0, end_col=None):
    """`label NN NN label` pairs of a 34-way header, from a column range.

    A label is words with single spaces between them, right-aligned two
    spaces from its pin number: on cps3.cpp's lines the JAMMA table's "Video
    Composite Sync" sits on the same line, far to the left of a blank pin.
    """
    out = {}
    word = r"\S+(?: \S+)*"
    rx = re.compile(rf"({word})?\s{{1,3}}(\d\d)\s+(\d\d)(?:\s+({word}))?\s*$")
    for l in lines:
        seg = l[start_col:end_col] if end_col else l[start_col:]
        m = rx.search(seg)
        if m and int(m.group(3)) == int(m.group(2)) + 1:
            out[str(int(m.group(2)))] = m.group(1) or ""
            out[str(int(m.group(3)))] = m.group(4) or ""
    return out


def read_neogeo(path):
    """The MVS and JAMMA tables neogeo.cpp prints side by side."""
    first, rows = lines_after(path, r"MVS\s+JAMMA", 30)
    mvs, jam = {}, {}
    rx = re.compile(r"^\s*(?:(.*?)\s*=\s*)?([A-Za-f])\s*\|\s*(\d+)\s*(?:=\s*(.*?))?\s*$")
    for l in rows:
        bars = [i for i, c in enumerate(l) if c == "|"]
        if len(bars) != 2:
            continue
        cut = bars[1] - 15
        for seg, out in ((l[:cut], mvs), (l[cut:], jam)):
            m = rx.match(seg)
            if m:
                out[m.group(2)] = m.group(1) or ""
                out[m.group(3)] = m.group(4) or ""
    return first, mvs, jam


def read_kenseim(path):
    first, rows = lines_after(path, r"Jamma \(on CPS board\)", 34)
    out = {}
    for l in rows:
        f = [x.strip() for x in l.split("|")]
        if len(f) >= 5 and f[2].isdigit():
            letter = "P" if f[3] == "O" else f[3]     # kenseim.cpp letters sync O
            out[f[2]] = f[1]
            out[letter] = f[4]
    return first, out


def read_popobear(path):
    """`parts n n solder`, with the solder side numbered 1-28 as well."""
    first, rows = lines_after(path, r"^JAMMA CONNECTOR", 30)
    out = {}
    for l in rows:
        m = re.match(r"^\s*(.*?)\s+(\d+)\s+(\d+)\s*(.*?)\s*$", l)
        if m and m.group(2) == m.group(3) and 1 <= int(m.group(2)) <= 28:
            n = int(m.group(2))
            out[str(n)] = m.group(1)
            out[LETTERS[n - 1]] = m.group(4)
    return first, out


def read_shaolins(path):
    """shaolins.cpp names the pins A1-A18 and B1-B18; Kicker's own manual
    letters the solder side A-V and numbers the parts side 1-18, as JAMMA
    does, and the library uses the manual's names."""
    first, rows = lines_after(path, r"18-WAY PCB Edge Connector Pinout", 30)
    out = {}
    for l in rows:
        f = [x.strip() for x in l.split("|")]
        if len(f) == 4 and re.fullmatch(r"A\d+", f[1]):
            out[LETTERS[int(f[1][1:]) - 1]] = f[0]
            out[f[2][1:]] = f[3]
    return first, out


def read_arcade_docs(path):
    """The Dancing Stage Fusion cabinet's primary connector, measured."""
    text = open(path).read()
    top = text.split("### Top side pinout", 1)[1].split("###", 1)[0]
    bottom = text.split("### Bottom side pinout", 1)[1].split("##", 1)[0]
    out = {}
    for block, key in ((top, lambda n: str(n)), (bottom, lambda n: LETTERS[n - 1])):
        for m in re.finditer(r"^\s*(\d+):\s*(.*?)\s*$", block, re.M):
            n = int(m.group(1))
            if 1 <= n <= 28:
                out[key(n)] = m.group(2)
    return 0, out


# ---- comparison -------------------------------------------------------------

def pins_of(conn):
    return {p["p"]: p for row in conn["rows"] for p in row}


def same(lib_s, src_s):
    if lib_s == src_s:
        return True
    # Same net under another name: a key slot printed blank, a lockout or
    # counter with no number, a ground called ground, stereo speakers.
    pairs = {("lockout1", "lockout"), ("lockout2", "lockout"), ("counter1", "counter"),
             ("key", "nc"), ("spare", "nc"), ("spk.l", "spk-"), ("spk.r", "spk+"),
             ("video.gnd", "gnd"), ("spk-", "gnd"), ("spk+", "spk")}
    return (lib_s, src_s) in pairs


def player_of(pin):
    return "1" if pin.isdigit() else "2"


def transcription(name, conn, table, where, problems):
    logged = {p for c in conn.get("conflicts", []) for p in c["pins"]}
    pins = pins_of(conn)
    for pin, p in pins.items():
        if pin not in table:
            problems.append(f"{name} {pin}: not in {where}")
            continue
        got = norm(table[pin], player_of(pin))
        if got is None or not same(p["s"], got):
            if pin in logged:
                continue
            problems.append(f"{name} {pin}: library {p['s']} ({p['n']}), {where} says {table[pin]!r}")


def main():
    mame = sys.argv[1]
    adocs = sys.argv[2] if len(sys.argv) > 2 else None
    lib = json.load(open(LIB))
    C = lib["connectors"]
    f = lambda rel: os.path.join(mame, rel)

    problems = []
    first, cps2 = read_cps_edge(f("capcom/cps2.cpp"), r"JAMMA Connector\s+Extra Button Connector")
    transcription("cps2-jamma", C["cps2-jamma"], cps2, "cps2.cpp", problems)
    _, cps2_lines = lines_after(f("capcom/cps2.cpp"), r"Most fighting type games", 20)
    transcription("cps2-cn5-fight", C["cps2-cn5-fight"], read_cps_header(cps2_lines, 0, 52), "cps2.cpp", problems)
    transcription("cps2-cn5-4p", C["cps2-cn5-4p"], read_cps_header(cps2_lines, 52), "cps2.cpp", problems)
    _, cps3 = read_cps_edge(f("capcom/cps3.cpp"), r"JAMMA Connector\s+Extra Button Connector")
    transcription("cps3-jamma", C["cps3-jamma"], cps3, "cps3.cpp", problems)
    _, cps3_lines = lines_after(f("capcom/cps3.cpp"), r"JAMMA Connector\s+Extra Button Connector", 34)
    transcription("cps3-cn5", C["cps3-cn5"], read_cps_header(cps3_lines), "cps3.cpp", problems)
    _, kenseim = read_kenseim(f("capcom/kenseim.cpp"))
    transcription("cps1-jamma", C["cps1-jamma"], kenseim, "kenseim.cpp", problems)
    _, mvs, ngjamma = read_neogeo(f("snk/neogeo.cpp"))
    transcription("mvs-multi", C["mvs-multi"], mvs, "neogeo.cpp MVS", problems)
    transcription("mvs-jamma", C["mvs-jamma"], ngjamma, "neogeo.cpp JAMMA", problems)
    _, shaolins = read_shaolins(f("konami/shaolins.cpp"))
    transcription("konami18", C["konami18"], shaolins, "shaolins.cpp", problems)

    print("Transcription, library against the MAME table each connector was read from:")
    print("  " + ("\n  ".join(problems) if problems else "every pin agrees (logged conflicts aside)"))

    # consensus over the generic JAMMA edge
    tables = {
        "gaelco2.cpp": read_bar(f("gaelco/gaelco2.cpp"), r"PCB Conector JAMMA")[1],
        "unico.cpp": read_bar(f("unico/unico.cpp"), r"Zero Point 2 board JAMMA Pinout")[1],
        "lethalj.cpp": read_bar(f("ice/lethalj.cpp"), r"Egg Venture & Lethal Justice JAMMA Pinout")[1],
        "lordgun.cpp": read_bar(f("igs/lordgun.cpp"), r"Lord of Gun JAMMA Pinout")[1],
        "champbwl.cpp": read_bar(f("seta/champbwl.cpp"), r"Main Jamma Connector")[1],
        "sfkick.cpp": read_bar(f("msx/sfkick.cpp"), r"Documentation as per manual")[1],
        "popobear.cpp": read_popobear(f("bmc/popobear.cpp"))[1],
        "kenseim.cpp": kenseim,
        "cps2.cpp": cps2,
        "cps3.cpp": cps3,
        "neogeo.cpp": ngjamma,
    }
    if adocs:
        tables["arcade-docs e33"] = read_arcade_docs(os.path.join(adocs, "konami/io/e33-jamma-wiring.md"))[1]
    jam = pins_of(C["jamma"])
    print(f"\nConsensus, the 1986 JAMMA edge against {len(tables)} independent tables:")
    agree_all = undisputed = 0
    for row in C["jamma"]["rows"]:
        for p in row:
            pin = p["p"]
            yes, blank, own, no = [], [], [], []
            for name, t in tables.items():
                if pin not in t:
                    blank.append(name)
                    continue
                got = norm(t[pin], player_of(pin))
                if got is None or (p["s"] == "spare" and re.match(r"p\d\.", got or "")):
                    own.append(name)            # the 1986 spare inputs are there to be used
                elif got == "nc":
                    blank.append(name)
                elif same(p["s"], got):
                    yes.append(name)
                else:
                    no.append(f"{name}={t[pin]!r}")
            if not no and not blank and not own:
                agree_all += 1
            if not no:
                undisputed += 1
            flag = "  " if not no else "!!"
            print(f" {flag} {pin:>2} {p['n']:<28} agree {len(yes):2d}  blank {len(blank):2d}  own use {len(own):2d}"
                  + (f"   differ: {', '.join(no)}" if no else ""))
    print(f"\n{undisputed} of {len(jam)} pins: no table names a different standard signal there")
    print(f"{agree_all} of {len(jam)} pins: every table names it, and names it the same")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
