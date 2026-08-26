#!/usr/bin/env python3
"""Cross-check the packaging table against the manuals' IC socket entries.

The parts lists carry their own statement of how many pins a device has, and
it is one nobody has to interpret. Atari stocked sockets by contact count —
`79-42C24  24-Contact Medium-Insertion-Force Integrated Circuit Socket
(J2, H2, E/F2, N/P3)` — so every socketed position names its own package size
in the same typeset list the devices come from.

That makes it an independent check on `packages.py`, which otherwise rests on
KiCAD's symbol library and on datasheets. Where the two disagree, the socket
wins on the question of pin count: it is the board's own bill of materials
saying what is fitted, while the packaging table is a lookup from a part
number that may itself have been misread.

Only socketed devices appear here — most of a board is soldered down — so this
confirms a minority of positions. It is a spot check, not a survey.

Target it the way you target the merge: name the documents, and pass --figure
when one manual covers more than one PCB. Pooling every document for a machine
does not work, and fails in the two ways this repo already knows about. The
Battlezone manual carries both boards, so the Auxiliary PCB's 40-contact
sockets get checked against the game PCB's 2114s. And a socket list is written
in its own printing's numbering, so the -05/-06 manual's E/F2 is not the -03
board's E2.
"""
import argparse, glob, json, os, re, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from packages import pins_for

FIGURE = re.compile(r'Figure\s+\d+[^\n]{0,80}?(?:Parts List|PCB Assembly|'
                    r'Assembly Parts)', re.I)
SOCKET = re.compile(
    r'79-42C(\d{2})\s+(\d{2})[-\s]?Contact[^(]{0,80}\(([^)]{1,120})\)', re.I)
DESIG = re.compile(r'\b([A-Z](?:/[A-Z])*)\s?(\d{1,2})\b')


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
    return re.sub(r'\s+', ' ', " ".join(out))


def sockets(fid, figure=None):
    """{designator: contacts} for every socketed position a document names."""
    txt = doc_text(fid)
    figs = [(m.start(), " ".join(m.group(0).split()))
            for m in FIGURE.finditer(txt)]
    pat = re.compile(figure, re.I) if figure else None
    out = {}
    for m in SOCKET.finditer(txt):
        stock, contacts = int(m.group(1)), int(m.group(2))
        if stock != contacts:      # the two must agree or the row is misread
            continue
        if pat:
            under = ""
            for pos, head in figs:
                if pos < m.start():
                    under = head
                else:
                    break
            if not pat.search(under):
                continue
        for d in DESIG.finditer(m.group(3)):
            out[d.group(1) + d.group(2)] = contacts
    return out


def first_cell(desig):
    head = desig.rstrip("0123456789")
    return head.split("/")[0] + desig[len(head):] if "/" in head else desig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("board")
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--figure", metavar="REGEX",
                    help="only sockets under a matching parts-list figure")
    a = ap.parse_args()

    f = os.path.join(ROOT, "boards", a.board + ".json")
    ics = json.load(open(f))["ics"]
    found = {}
    for fid in a.docs:
        for des, n in sockets(fid, a.figure).items():
            found.setdefault(first_cell(des), set()).add(n)

    ok, bad, skipped = [], [], 0
    for cell, contacts in sorted(found.items()):
        if len(contacts) != 1:
            skipped += 1
            continue
        want = next(iter(contacts))
        if cell not in ics:
            skipped += 1
            continue
        got, _ = pins_for(ics[cell])
        if got is None:
            skipped += 1
        elif got == want:
            ok.append(f"{cell} {ics[cell]} DIP-{got}")
        else:
            bad.append(f"{cell}: {ics[cell]} sized DIP-{got}, "
                       f"socket is {want}-contact")

    print(f"{a.board}: {len(found)} socketed positions named, "
          f"{len(ok)} confirmed, {len(bad)} contradicted, {skipped} not checked")
    for x in ok:
        print(f"  ok  {x}")
    for x in bad:
        print(f"  !!  {x}")
    return 1 if bad else 0


def _unused():

    registered = {b["slug"]: b.get("machine", "") for b in
                  json.load(open(os.path.join(ROOT, "data/boards.json")))}
    docs = json.load(open(os.path.join(ROOT, "data/index/docs.json")))
    by_machine = defaultdict(list)
    for d in docs:
        if d.get("machine"):
            by_machine[d["machine"]].append(d["id"])

    agree = disagree = unseen = 0
    problems = []
    for f in sorted(glob.glob(os.path.join(ROOT, "boards", "*.json"))):
        slug = os.path.basename(f)[:-5]
        if slug.endswith(".read") or slug.endswith(".notes"):
            continue
        if a.board and slug != a.board:
            continue
        board = json.load(open(f))
        ics = board["ics"]
        # Most board definitions carry no machine of their own — the link
        # lives in data/boards.json. See AGENTS.md.
        mach = board.get("machine") or registered.get(slug, "")
        found = {}
        for fid in by_machine.get(mach, []):
            try:
                for des, n in sockets(fid).items():
                    found.setdefault(first_cell(des), set()).add(n)
            except Exception:
                continue
        if not found:
            continue
        hits = ok = bad = 0
        for cell, contacts in found.items():
            if cell not in ics or len(contacts) != 1:
                continue
            want = next(iter(contacts))
            got, _ = pins_for(ics[cell])
            if got is None:
                continue
            hits += 1
            if got == want:
                ok += 1
            else:
                bad += 1
                problems.append(f"{slug} {cell}: {ics[cell]} sized DIP-{got}, "
                                f"socket is {want}-contact")
        agree += ok
        disagree += bad
        unseen += len(found) - hits
        if hits:
            print(f"  {slug:<22}{ok:>3} confirmed, {bad} contradicted "
                  f"(of {len(found)} socketed positions named)")

    print(f"\n{agree} package sizes confirmed by a socket entry, {disagree} contradicted")
    for p in problems:
        print(f"  ! {p}")
    return 1 if disagree else 0


if __name__ == "__main__":
    sys.exit(main())
