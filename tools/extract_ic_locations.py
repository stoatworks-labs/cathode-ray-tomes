#!/usr/bin/env python3
"""Recover designator -> device type from the typeset IC parts lists.

AGENTS.md records that harvesting a board complement from the *drawings* does
not work: designators OCR fine but the hand-lettered part numbers do not, and
`harvest_board.py` returns ~0 usable pairs. That finding stands and this is not
a re-litigation of it — this reads a different source. The technical manuals
carry a typeset IC parts list, set in the same type as the body text, and it
gives exactly the pairing the drawings will not give up.

Two layouts appear in the corpus, and each carries its own checksum:

  paren   37-74LS00   Type 74LS00 Integrated Circuit (N5, C6)
  count   37-7400  10 Integrated Circuit 7400  A2,A6,A9,D5,D9,E3,H/J2,L8,R3

The paren layout states the device type twice — once as Atari's stock number
and once in the description — so a row is trusted only when two independent
OCR reads of it agree. The count layout states how many devices the row covers,
so the designators must come to that many. A row that fails its own checksum is
reported, never quietly used: the whole point of the exercise is that a wrong
designator in a repair reference is worse than an absent one.

This does not write board definitions. It produces candidate pairs and a
disagreement report for a person to adjudicate, because ~10% of trusted rows
still disagree with a hand read and the disagreements are interesting.
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from packages import (TTL_PINS, TTL_PINS_UNCHECKED, PART_PINS,
                      ATARI_MEMORY)

TTL_PINS = {**TTL_PINS, **TTL_PINS_UNCHECKED}

STOCK = re.compile(r'\b37[-\s]?([0-9][0-9A-Z]{2,7})\b')
# 'Type 74LS04' on the Asteroids manuals, 'Type-74LS04' on the Centipede and
# Tempest ones. That single hyphen was the whole reason those two machines
# harvested nothing at all from forty-odd documents each.
TYPE = re.compile(r'\bType[-\s]\s*([0-9A-Z][0-9A-Z\s.]{2,10}?)\s+'
                  r'(?:[A-Z]{2,4}\s+)?[Ii]ntegrated', re.I)
# OCR turns ( ) into { } [ ] often enough to be worth accepting
PARENS = re.compile(r'[\(\{\[]([^)}\]]{1,140})[\)\}\]]')
# The count layout names the device in its description too — 'Integrated
# Circuit, 74S74 L7' — so it has the same two-readings-of-one-row check the
# paren layout does, and it was going unused.
# Memory and the MPU are stocked under Atari's own part numbers, not as
# 37-series IC stock, so the rows above never see them. That is why Centipede's
# ROMs and Red Baron's whole complement were missing. Same typeset list, same
# shape — part number, description, positions — and the description names the
# device class, which is what fixes the package.
MEMORY = re.compile(
    r'\b((?:\d{2}-\d{4}|\d{6}-\d{2,3}|[A-Z]\d{6}-\d{2}))\s+'
    r'((?:Programmable\s+)?(?:Read-Only|Random-Access)\s+Memory|Microprocessor|'
    r'Read/Write\s+Memory)[^(]{0,40}\(([^)]{1,110})\)', re.I)

MEMORY_CLASS = {
    "microprocessor": "mpu",
    "read-only memory": "rom",
    "programmable read-only memory": "prom",
    "random-access memory": "ram",
    "read/write memory": "ram",
}


def memory_rows(fid, figure=None):
    """[(part, class, [cells], span_by_cell)] for the memory rows of a document."""
    txt = doc_text(fid)
    figs = [(m.start(), " ".join(m.group(0).split()))
            for m in FIGURE.finditer(txt)]
    pat = re.compile(figure, re.I) if figure else None
    out = []
    for m in MEMORY.finditer(txt):
        if pat:
            under = ""
            for pos, head in figs:
                if pos < m.start():
                    under = head
                else:
                    break
            if not pat.search(under):
                continue
        kind = MEMORY_CLASS.get(" ".join(m.group(2).split()).lower())
        if not kind:
            continue
        cells = []
        for d in DESIG.finditer(m.group(3)):
            if d.group(2) == "0":          # column 0 does not exist
                continue
            cells.append(d.group(1) + d.group(2))
        if cells:
            out.append((m.group(1), kind, cells))
    return out


INLINE_TYPE = re.compile(r'[Ii]ntegrated\s+Circuit[,.]?\s+([0-9A-Z][0-9A-Z.]{2,8})')
DESIG = re.compile(r'\b([A-Z](?:/[A-Z])*)\s?(\d{1,2})\b')
# a row that only names an alternative device carries no locations of its own;
# reading on past it picks up the *next* row's designators
SUBSTITUTE = re.compile(r'substitute\s+for|used\s+(?:only\s+)?(?:with|in)\b', re.I)
# A manual with more than one PCB gives each its own figure, and the heading
# names the board: 'Figure 25 Battlezone Auxiliary PCB Assembly Parts List'
# against 'Figure 26 Battlezone Analog Vector-Generator PCB Assembly'. Without
# this the two boards' parts land in one heap, and their designators collide —
# C1 on one is not C1 on the other.
FIGURE = re.compile(r'Figure\s+\d+[^\n]{0,80}?(?:Parts List|PCB Assembly|'
                    r'Assembly Parts)', re.I)

# Characters OCR confuses inside a stock number. Comparing a normalised form
# lets '37-74L832' match 'Type 74LS32' without loosening the check to nothing.
CONFUSE = str.maketrans({"8": "S", "5": "S", "1": "L", "0": "O"})


# Device equivalences established elsewhere in this repo, so a cross-check
# does not report them as disagreements. These are the same part under two
# names, not a substitution: 9316 is Fairchild's 74161, AM8304B is the LS245
# Atari's own drawing names as an alternate, and the LS670/LS170 pair is the
# documented option that decides whether RP1/RP2 are fitted.
EQUIVALENT = {"9316": "161", "74161": "161", "4016B": "4016",
              "CD4016B": "4016", "CD4066": "4066", "8304B": "245",
              "74LS170": "170", "74LS670": "170"}


# A well-formed device name: a 74-series part with a real family, a 4xxx CMOS
# part, or a lettered part number like LM324 or AD561J. Used only to choose
# between two OCR readings of the same row, never to reject one.
CANONICAL = re.compile(
    r'^(?:74(?:LS|ALS|AS|HCT|HC|S|H|L|F|C)?\d{2,3}[A-Z]?'
    r'|(?:CD)?4\d{3}[A-Z]?'
    r'|[A-Z]{2,3}\d{3,4}[A-Z]?'
    r'|\d{2}S\d{2,3})$')


# 74-series logic families. A spelling is only well-formed if what sits between
# the '74' and the function number is one of these.
FAMILY = re.compile(r'^74(LS|ALS|AS|HCT|HC|S|H|L|F|C)?(\d{2,3})([A-Z]?)$')


# A part number that could actually exist. Beyond the 74-series and 4xxx CMOS
# forms in CANONICAL, this covers the bipolar and bus parts of the era, which
# put a letter in the middle: 8T28, 82S129, 9316.
PLAUSIBLE = re.compile(r'^\d{1,2}[A-Z]\d{2,4}[A-Z]?$')


def plausible(part):
    return bool(CANONICAL.match(part) or PLAUSIBLE.match(part))


def well_formed(part):
    """Is this a name we can actually stand behind?

    Stricter than `plausible`, and the difference is the point. '74874' is a
    plausible-looking 74-series name — 74 followed by three digits — but its
    function number is 74, because that is what it ends in, and 874 is not
    what follows a real family. It is an OCR of 74S74 that both printings
    happened to make the same way, so nothing else catches it. A device the
    board map cannot name correctly does not go on the board map.
    """
    if part in PART_PINS or part in ATARI_MEMORY:
        return True
    if part.startswith("74"):
        m = FAMILY.match(part)
        # Test the digits against the vocabulary directly rather than against
        # device_key, which maps documented equivalents onto each other — the
        # LS670 is compared as a 170, and asking it to *spell* itself 170
        # rejected a perfectly good part.
        return bool(m and m.group(2) in TTL_PINS)
    return bool(PLAUSIBLE.match(part) or CANONICAL.match(part))


FAMILIES = ("", "LS", "S", "H", "L", "C", "F", "ALS", "AS", "HC", "HCT")
# The family letters are what OCR destroys, and it destroys them the same two
# ways every time: L read as 1, S read as 8 or 5.
UNMANGLE = str.maketrans({"1": "L", "8": "S", "5": "S"})


def repair_family(part):
    """'741808' -> '74LS08'. None if the repair is not unique or not a part.

    The corruption is systematic — 74LS08 comes back as 741808, 74LS74 as
    74L874, 74S04 as 74504 — and it is safe to undo *only* because the result
    has to land in the packaging table's vocabulary. Every split of the string
    into family and function number is tried; the repair is accepted when
    exactly one of them names a device we know. Anything ambiguous is left
    alone and the device is not placed.
    """
    if not part.startswith("74") or len(part) < 4:
        return None
    body, found = part[2:], set()
    for k in range(0, 4):
        fam, num = body[:k], body[k:]
        if not num.isdigit() or num not in TTL_PINS:
            continue
        if fam.translate(UNMANGLE) in FAMILIES:
            found.add("74" + fam.translate(UNMANGLE) + num)
    return found.pop() if len(found) == 1 else None


def best_spelling(*candidates):
    """The cleanest reading of a device name among several OCRs of it.

    A row states its device twice — Atari's stock number and the description —
    and OCR rarely mangles both the same way, so the two readings can be played
    against each other.

    Length is the wrong tie-break and cost a wrong answer before this was
    written: '74S32' misread as '74832' is *longer*, and it parses as a
    74-series part with function number 832. What exposes it is that its
    function number is 32 — the digits it actually ends in — and 832 is not
    what sits after a valid family. So prefer the spelling that decomposes as
    74 + a real family + this device's own function number.
    """
    cands = [c for c in candidates if c]
    if not cands:
        return None
    key = device_key(cands[0])
    good = [c for c in cands
            if (m := FAMILY.match(c)) and m.group(2).lstrip("0") == key]
    if good:
        return max(good, key=len)
    repaired = [r for r in (repair_family(c) for c in cands) if r]
    if repaired and len(set(repaired)) == 1:
        return repaired[0]
    clean = [c for c in cands if CANONICAL.match(c)]
    return max(clean or cands, key=len)


def device_key(part):
    """Compare devices by function number, ignoring the logic family.

    The family letters are what OCR mangles — '74LS157' comes back as
    '741S157' and 'LS374' as '18374' — so the number is recovered by asking
    which trailing digits name a device the packaging table already knows,
    rather than by trying to parse the family. That keeps a real distinction
    (a 7400 is '00', not '400') without inventing one for every OCR variant.
    """
    p = _norm(part)
    if p in EQUIVALENT:
        return EQUIVALENT[p]
    for n in (3, 2):
        tail = p[-n:]
        if tail.isdigit() and tail in TTL_PINS and len(p) > n:
            return tail.lstrip("0") or "0"
    m = re.match(r'^(?:74|CD)?[A-Z]*(\d+)[A-Z]?$', p)
    return m.group(1).lstrip("0") if m else p


def _norm(t):
    return re.sub(r'[\s.\-]', '', (t or "")).upper()


def _loose(t):
    return _norm(t).translate(CONFUSE)


def doc_text(fid):
    d = json.load(open(os.path.join(ROOT, "cache", "text", fid + ".json")))
    out = []

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("t"), str):
                out.append(o["t"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(d)
    return "\n".join(out)


def rows(fid):
    """Every IC parts-list row in a document, trusted or not.

    Each row carries the figure heading it sits under, so a manual covering
    several PCBs can be split back into them.
    """
    txt = doc_text(fid)
    figures = [(m.start(), " ".join(m.group(0).split()))
               for m in FIGURE.finditer(txt)]
    out = []
    for m in STOCK.finditer(txt):
        stock = m.group(1)
        tail = txt[m.end():m.end() + 220]
        nxt = STOCK.search(tail)
        if nxt:
            tail = tail[:nxt.start()]

        under = ""
        for pos, head in figures:
            if pos < m.start():
                under = head
            else:
                break
        rec = {"stock": stock, "type": None, "desigs": [], "trusted": False,
               "layout": None, "why": "", "qualified": False, "figure": under,
               "raw": " ".join(tail.split())[:150]}

        t = TYPE.search(tail)
        if t:
            rec["layout"] = "paren"
            rec["type"] = _norm(t.group(1))
            if SUBSTITUTE.search(tail):
                rec["why"] = "substitution row — names a device, not a location"
                out.append(rec)
                continue
            p = PARENS.search(tail, t.end())
            if p:
                inner = p.group(1)
                rec["qualified"] = bool(SUBSTITUTE.search(inner) or
                                        re.search(r'PCB|only', inner, re.I))
                rec["desigs"] = [d.group(1) + d.group(2)
                                 for d in DESIG.finditer(inner)]
            if not rec["desigs"]:
                rec["why"] = "no designators found"
            elif _loose(rec["type"]) != _loose(stock):
                rec["why"] = (f"stock 37-{stock} and description "
                              f"'Type {t.group(1).strip()}' disagree")
            else:
                rec["trusted"] = True
                rec["type"] = best_spelling(_norm(stock), rec["type"])
        else:
            q = re.match(r'\s*(\d{1,2})\b', tail)
            if q:
                rec["layout"] = "count"
                rec["type"] = _norm(stock)
                rec["qty"] = int(q.group(1))
                body = tail[q.end():]
                t2 = INLINE_TYPE.search(body)
                if t2:
                    rec["type"] = best_spelling(_norm(stock), _norm(t2.group(1)))
                    body = body[t2.end():]
                rec["desigs"] = [d.group(1) + d.group(2)
                                 for d in DESIG.finditer(body)]
                if not rec["desigs"]:
                    rec["why"] = "no designators found"
                elif rec["qty"] != len(rec["desigs"]):
                    rec["why"] = (f"row says {rec['qty']} devices, "
                                  f"{len(rec['desigs'])} designators read")
                else:
                    rec["trusted"] = True
        if rec["layout"]:
            out.append(rec)
    return out


def locations(fid, figure=None):
    """{designator: type} from the trusted rows only, plus any collision.

    `figure` is a regex; only rows under a matching figure heading count.
    """
    pat = re.compile(figure, re.I) if figure else None
    loc, clash = {}, []
    for r in rows(fid):
        if not r["trusted"]:
            continue
        if pat and not pat.search(r.get("figure", "")):
            continue
        for d in r["desigs"]:
            if d in loc and loc[d] != r["type"]:
                clash.append((d, loc[d], r["type"]))
            loc[d] = r["type"]
    return loc, clash


def cross_check(read_path, ids):
    """Compare the harvested pairs against a hand read of the same machine.

    A designator is checked against every numbering the read knows for it —
    primary and -05/-06 alternate both — because the parts lists are written in
    whichever numbering that printing used, and comparing one against the other
    manufactures disagreements that are only the shift.
    """
    read = json.load(open(read_path))
    known = defaultdict(set)
    for key, sheet in read.items():
        if not key.startswith("sheet"):
            continue
        for des, spec in sheet.items():
            if not spec.get("part"):
                continue
            known[des.rstrip("b")].add(device_key(spec["part"]))
            if spec.get("alt"):
                known[spec["alt"]].add(device_key(spec["part"]))

    agree, unseen, dis = 0, set(), defaultdict(int)
    for fid in ids:
        try:
            loc, _ = locations(fid)
        except Exception:
            continue
        for des, typ in loc.items():
            if des not in known:
                unseen.add(des)
            elif device_key(typ) in known[des]:
                agree += 1
            else:
                dis[(des, "/".join(sorted(known[des])), typ)] += 1
    total = agree + sum(dis.values())
    print(f"{agree} agree, {sum(dis.values())} disagree of {total} checked "
          f"({100*agree/total:.0f}%)" if total else "nothing to check")
    print(f"{len(unseen)} designators the read has never seen\n")
    print("disagreements, with the number of printings each appears in —")
    print("a disagreement in several independent printings is not OCR noise:")
    for (des, k, typ), n in sorted(dis.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {des:<6}read={k:<14}parts list={typ:<10} in {n} printing(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc", nargs="*", help="document id(s); default all")
    ap.add_argument("--failures", action="store_true",
                    help="show rows that failed their own checksum")
    ap.add_argument("--cross-check", metavar="READ",
                    help="boards/<slug>.read.json to compare against")
    a = ap.parse_args()

    if a.cross_check:
        ids = a.doc or []
        if not ids:
            ap.error("--cross-check needs the document ids to check against")
        return cross_check(a.cross_check, ids)

    ids = a.doc or [os.path.basename(p)[:-5]
                    for p in glob.glob(os.path.join(ROOT, "cache/text/*.json"))]
    titles = {d["id"]: d.get("title", "") for d in
              json.load(open(os.path.join(ROOT, "data/index/docs.json")))}

    total_rows = total_trusted = total_loc = 0
    for fid in sorted(ids):
        try:
            rs = rows(fid)
        except Exception:
            continue
        if not rs:
            continue
        loc, clash = locations(fid)
        tr = sum(1 for r in rs if r["trusted"])
        total_rows += len(rs)
        total_trusted += tr
        total_loc += len(loc)
        if not loc:
            continue
        print(f"{fid}  {titles.get(fid,'?')[:56]:<56} "
              f"{tr:>3}/{len(rs):<3} rows  {len(loc):>3} designators"
              + (f"  {len(clash)} collisions" if clash else ""))
        if a.failures:
            for r in rs:
                if not r["trusted"] and r["why"]:
                    print(f"      - 37-{r['stock']}: {r['why']}")
                    print(f"        {r['raw'][:110]}")
    print(f"\n{total_trusted} of {total_rows} rows pass their checksum, "
          f"{total_loc} designator/type pairs across {len(ids)} documents")


if __name__ == "__main__":
    main()
