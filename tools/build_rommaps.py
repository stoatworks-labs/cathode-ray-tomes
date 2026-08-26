#!/usr/bin/env python3
"""Build ROM maps for every MAME set that names its ROM positions.

MAME's romset filenames carry the board position as a suffix — '036409-01.n1',
'pm1_prg1.6e', 'roadf.12d' — and those come from real dumped boards. That is
enough to say which memory device sits where, for thousands of machines this
project has a manual for and no board map.

It is *not* enough to say what the rest of the board is. A ROM map names the
fifteen-to-forty socketed memory devices on a board of sixty to a hundred and
fifty; everything else is blank. So these are a separate kind of asset from the
board maps in `boards/`, which are read off component-location drawings, carry
per-device provenance and have been cross-checked against parts lists, socket
entries and MAME itself. Do not merge the two: a ROM map is one source and
positions only, and the site says so on every page.

Two grid conventions appear and both are kept as the board writes them:

    letter-number   Atari and most US boards   N1, F/H1, L/M/N3
    number-letter   Namco, Konami, most JP     6E, 12D, 7LM

Input is the parsed output of a MAME source scan; see the --roms argument.
"""
import argparse, collections, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A suffix that is a board position. 'i' and 'o' are skipped by every grid
# convention in this corpus because they read as 1 and 0.
LN = re.compile(r'^([a-hj-np-z]{1,3})(\d{1,2})$')
NL = re.compile(r'^(\d{1,2})([a-hj-np-z]{1,2})$')
# Sequential numbering is a chip list, not a map: u34 does not say where u34 is.
SEQ = re.compile(r'^(?:u|ic|rom|prom|p|bin|a|b|d)\.?\d{1,3}$')

# What MAME's region names mean on a board.
REGION_KIND = {
    "maincpu": "program", "audiocpu": "sound program", "sub": "sub-CPU program",
    "gfx1": "graphics", "gfx2": "graphics", "gfx3": "graphics",
    "gfx4": "graphics", "sprites": "graphics", "tiles": "graphics",
    "chars": "graphics", "bgtiles": "graphics",
    "proms": "PROM", "plds": "PLD", "pals": "PLD",
    "samples": "sound samples", "oki": "sound samples", "adpcm": "sound samples",
    "user1": "data", "user2": "data",
}


def suffix(fn):
    return fn.rsplit(".", 1)[1].lower() if "." in fn else None


def classify(roms):
    """('letter-number'|'number-letter', {cell: rom}) or (None, {})."""
    ln, nl = {}, {}
    for r in roms:
        s = suffix(r["file"])
        if not s or SEQ.match(s):
            continue
        if LN.match(s):
            ln.setdefault(s.upper(), r)
        elif NL.match(s):
            nl.setdefault(s.upper(), r)
    if len(ln) >= 3 and len(ln) > len(nl):
        return "letter-number", ln
    if len(nl) >= 3 and len(nl) > len(ln):
        return "number-letter", nl
    return None, {}


def pins_for_size(size, note):
    """Package size from the dump size, where the era makes it unambiguous."""
    n = (note or "").lower()
    for part, pins in (("82s123", 16), ("82s126", 16), ("82s129", 16),
                       ("82s131", 16), ("82s137", 16), ("82s147", 20),
                       ("6331", 16), ("74s287", 16), ("74s288", 16)):
        if part in n:
            return pins, part
    if size in (0x20, 0x100, 0x200):
        return 16, None            # bipolar PROM
    if size in (0x400, 0x800):
        return 24, None            # 1K/2K ROM, 2708/2716/2316 class
    if size in (0x1000, 0x2000):
        return 24, None            # 4K/8K, 2732/2764 class
    if size in (0x4000, 0x8000):
        return 28, None            # 27128/27256
    if size and size >= 0x10000:
        return 32, None            # 27512 and up
    return None, None


def cell_sort(cell, style):
    m = (LN if style == "letter-number" else NL).match(cell.lower())
    if not m:
        return (99, 99)
    a, b = m.groups()
    return (int(b), a) if style == "letter-number" else (int(a), b)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roms", required=True, help="parsed MAME ROM data (json)")
    ap.add_argument("--parents", help="machine -> parent set, from MAME's GAME macros")
    ap.add_argument("--out", default=os.path.join(ROOT, "data"))
    ap.add_argument("--with-docs-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    sets = json.load(open(a.roms))
    machines = {x["s"]: x for x in
                json.load(open(os.path.join(ROOT, "data/index/machines.json")))}
    docs = collections.Counter(
        d.get("machine") for d in
        json.load(open(os.path.join(ROOT, "data/index/docs.json")))
        if d.get("ingested") and d.get("machine"))
    boards = {b["machine"] for b in
              json.load(open(os.path.join(ROOT, "data/boards.json")))}

    parents = json.load(open(a.parents)) if a.parents else {}

    out_dir = os.path.join(a.out, "rommap")
    os.makedirs(out_dir, exist_ok=True)
    index, seen_sig = [], {}

    # Which set gets to name a shared layout. Alphabetical order put Pac-Man's
    # board under an obscure bootleg that happened to sort first, so: the set
    # with the most manuals here wins, then MAME's parent over its clones,
    # then the name.
    def rank(n):
        return (-docs.get(n, 0), 0 if parents.get(n, "?") is None else 1, n)

    for name in sorted(sets, key=rank):
        if a.with_docs_only and name not in docs:
            continue
        m = machines.get(name)
        if not m:
            continue
        style, cells = classify(sets[name]["roms"])
        if not style:
            continue
        # One board per position signature: clones share a layout, and 26
        # near-identical pages help nobody.
        sig = (style, tuple(sorted(cells)))
        if sig in seen_sig:
            seen_sig[sig].append(name)
            continue
        seen_sig[sig] = [name]

        devices = {}
        for cell, r in cells.items():
            pins, part = pins_for_size(r["size"], r["note"])
            devices[cell] = {
                "file": r["file"], "size": r["size"],
                "kind": REGION_KIND.get(r["region"] or "", r["region"] or "?"),
                "pins": pins, "part": part,
            }
        rec = {
            "machine": name, "name": m.get("n", name), "mfr": m.get("m", ""),
            "year": m.get("y", ""), "style": style,
            "source": sets[name]["src"], "docs": docs.get(name, 0),
            "devices": dict(sorted(devices.items(),
                                   key=lambda kv: cell_sort(kv[0], style))),
        }
        json.dump(rec, open(os.path.join(out_dir, name + ".json"), "w"), indent=1)
        index.append({"machine": name, "name": rec["name"], "mfr": rec["mfr"],
                      "year": rec["year"], "devices": len(devices),
                      "docs": rec["docs"], "style": style,
                      "hasBoard": name in boards})
        if a.limit and len(index) >= a.limit:
            break

    index.sort(key=lambda r: (-r["docs"], -r["devices"], r["name"]))
    json.dump(index, open(os.path.join(a.out, "rommaps.json"), "w"), indent=1)
    shared = sum(len(v) - 1 for v in seen_sig.values() if len(v) > 1)
    print(f"{len(index)} ROM maps written to {out_dir}")
    print(f"  {sum(1 for r in index if r['docs'])} have a manual on the site")
    print(f"  {sum(1 for r in index if r['hasBoard'])} also have a full board map")
    print(f"  {shared} further sets share a layout with one of these and were folded in")
    print(f"  {sum(r['devices'] for r in index)} devices placed in total")


if __name__ == "__main__":
    main()
