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
from packages import TTL_PINS, TTL_PINS_UNCHECKED

TTL_PINS = {**TTL_PINS, **TTL_PINS_UNCHECKED}

STOCK = re.compile(r'\b37[-\s]?([0-9][0-9A-Z]{2,7})\b')
TYPE = re.compile(r'\bType\s+([0-9A-Z][0-9A-Z\s.]{2,10}?)\s+[Ii]ntegrated', re.I)
# OCR turns ( ) into { } [ ] often enough to be worth accepting
PARENS = re.compile(r'[\(\{\[]([^)}\]]{1,140})[\)\}\]]')
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
                rec["desigs"] = [d.group(1) + d.group(2)
                                 for d in DESIG.finditer(tail[q.end():])]
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
