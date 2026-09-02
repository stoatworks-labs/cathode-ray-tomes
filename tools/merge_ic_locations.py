#!/usr/bin/env python3
"""Merge harvested parts-list locations into a board map, with provenance.

The rule, and it is the whole point of the file:

  * the drawing read is authoritative wherever it exists — it is someone
    looking at the board's own component-location drawing, and it stays put
  * the parts lists fill the gaps
  * a device is only taken from the parts lists when two or more independent
    printings agree on it, unless --allow-single says otherwise
  * every device records which source it came from, so a repair reference
    never hides that

The two-printing rule matters more than the raw accuracy figure. Measured
against the Asteroids hand read, a single printing is right about 85% of the
time — not good enough. But four printings of the Asteroids Deluxe manual agree
with each other on 100 of 100 designators and with all eight hand-read devices,
which is a different quality of evidence entirely. Where the printings disagree
with each other, nothing is taken.

Writes nothing without --apply.
"""
import argparse, json, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from extract_ic_locations import (locations, device_key, plausible,
                                  well_formed, best_spelling)


# Superseded by tools/designators.py, which reads both of Atari's conventions.
# The old implementation assumed row-letter-first and, given a 1983-on
# designator like `2L`, returned it unchanged and let the caller's `cell[0] not
# in rows` test reject it as off-grid — so a whole board silently harvested
# nothing rather than harvesting wrongly.
from designators import cell_and_span, parse as parse_desig


def harvest(doc_ids, figure=None):
    """{designator: (part, n_printings)} where the printings agree.

    A designator can also collide *inside* one printing — two rows of the same
    parts list claiming the same cell. `locations()` detects that and returns
    it, but resolves the cell by last write, so a caller that takes only the
    mapping gets one of the two readings with nothing to say the other existed.
    On a manual covering more than one PCB that is how two boards merge into
    one wrong map silently, which is the Red Baron failure.

    So a colliding designator is dropped from the printing it collided in. It
    is dropped there rather than everywhere because another printing may read
    the same cell cleanly, and that reading is still worth having; if no
    printing reads it cleanly the cell simply does not appear.
    """
    per, collisions = {}, defaultdict(list)
    for fid in doc_ids:
        try:
            loc, clash = locations(fid, figure)
        except Exception as e:
            print(f"  ! {fid}: {e}")
            continue
        # Gather every reading of a contested cell, not just the pair in one
        # clash entry — a cell claimed three times produces two entries, and
        # the surviving value in `loc` is a reading too.
        readings = defaultdict(set)
        for des, first, second in clash:
            readings[des].update((first, second))
            if des in loc:
                readings[des].add(loc[des])
        for des, seen in readings.items():
            # A contested cell is kept only when every reading of it names the
            # same device — '74L886' against '74LS86' is one part and an OCR of
            # S as 8. Anything else comes off the map.
            #
            # Deliberately NOT using plausible() to break the tie, though the
            # cross-printing split does. plausible() does not recognise the
            # Fairchild 93xx and 96xx series, so it calls 9312, 9322 and 9602
            # implausible — and 9316, which this file's own equivalence table
            # documents as Fairchild's 74161. Filtering on it here would have
            # discarded the 9312 reading of Indy 4's B3 and "resolved" the cell
            # to a 7474, which is a different device entirely. A false
            # correction is worse than the collision it replaces.
            if len({device_key(p) for p in seen}) == 1:
                loc[des] = best_spelling(*seen)
                continue
            collisions[des].append((fid, sorted(seen)))
            loc.pop(des, None)
        per[fid] = loc
    if collisions:
        print(f"  {len(collisions)} designator(s) dropped — claimed twice "
              f"within one printing, which says nothing about which is right:")
        for des, hits in sorted(collisions.items()):
            for fid, seen in hits:
                print(f"      {des}: {' against '.join(seen)} (in {fid})")
    votes = defaultdict(dict)
    for fid, loc in per.items():
        for des, part in loc.items():
            votes[des][fid] = part
    agreed, split = {}, {}
    for des, v in votes.items():
        keys = {device_key(p) for p in v.values()}
        if len(keys) > 1:
            # Before calling it a disagreement, drop the readings that are not
            # part numbers anyone ever made. '8T28' against '8728' is one
            # device and an OCR of T as 7, not two printings contradicting
            # each other — but '74LS42' against '74LS170' is a real split and
            # must stay one, so this only ever discards the implausible.
            good = {f: p for f, p in v.items() if plausible(p)}
            if good and len({device_key(p) for p in good.values()}) == 1:
                v = good
                keys = {device_key(p) for p in good.values()}
        if len(keys) == 1:
            # Choose between the printings' spellings the same way a single
            # row chooses between its own two readings. Length is not the
            # test: '74874' and '74S74' are the same length and only one of
            # them is a part.
            agreed[des] = (best_spelling(*v.values()), len(v))
        else:
            split[des] = v
    return agreed, split, len(per)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--figure", metavar="REGEX",
                    help="only rows under a matching parts-list figure "
                         "heading — needed whenever a manual covers more than "
                         "one PCB, or the two boards' designators collide")
    ap.add_argument("--allow-single", action="store_true",
                    help="accept a designator attested by only one printing")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    bpath = os.path.join(ROOT, "boards", a.slug + ".json")
    board = json.load(open(bpath))
    rows = board["grid"]["rows"]
    cols = board["grid"].get("cols")
    drawing = dict(board["ics"])
    spans = dict(board.get("spans", {}))
    # Which way round this board's designators are printed. Stated by the
    # board, never inferred from a designator — see tools/designators.py.
    transposed = bool(board["grid"].get("transposed"))

    agreed, split, ndocs = harvest(a.docs, a.figure)
    print(f"{ndocs} printings, {len(agreed)} designators agreed, "
          f"{len(split)} split between printings\n")

    need = 1 if a.allow_single else 2
    added, confirmed, conflicts, offgrid, thin = {}, [], [], [], []
    badspan = []
    collided, unnamed = [], []
    for des, (part, n) in sorted(agreed.items()):
        if not well_formed(part):
            unnamed.append((des, part))
            continue
        cell, span = cell_and_span(des, transposed)
        parsed = parse_desig(des, transposed)
        if not cell or not parsed or parsed[0][0] not in rows:
            offgrid.append((des, part))
            continue
        # Boards are ten or so columns wide. A designator claiming column 28 is
        # OCR wreckage, not a position, and placing it would stretch the board
        # to three times its width to hold one phantom.
        if cols and parsed[1] > cols:
            offgrid.append((des, part))
            continue
        # A span names the rows a wide device straddles, and they have to be
        # next to each other. build_board enforces that and raises, but it
        # enforced it too late: the merge wrote the span, the board file
        # carried it, and the build failed afterwards. Removing it by hand did
        # not stick either, because the next merge simply put it back. So the
        # rule belongs here, where the designator is first accepted.
        if span and len(parsed[0]) > 1:
            idx = sorted(rows.index(r) for r in parsed[0] if r in rows)
            if len(idx) != len(parsed[0]) or \
                    idx != list(range(idx[0], idx[0] + len(idx))):
                badspan.append((des, part))
                continue
        if cell in drawing:
            if device_key(drawing[cell]) == device_key(part):
                confirmed.append(cell)
            else:
                conflicts.append((cell, drawing[cell], part, n))
            continue
        if n < need:
            thin.append((des, part))
            continue
        # Two harvested designators can land on one cell — most often a
        # spanning 'B/C10' against a plain 'B10' from a different row. One of
        # the two readings is wrong and there is nothing here to say which, so
        # take neither. Overwriting silently is how a board map ends up naming
        # a chip that is not there.
        if cell in added and device_key(added[cell][0]) != device_key(part):
            collided.append((cell, added[cell][2] or cell, added[cell][0],
                             des, part))
            continue
        added[cell] = (part, n, span)
    for cell, d1, p1, d2, p2 in collided:
        added.pop(cell, None)

    print(f"  {len(confirmed):>3} drawing devices confirmed by the parts lists")
    print(f"  {len(conflicts):>3} disagree with the drawing — drawing keeps them")
    print(f"  {len(added):>3} added from the parts lists")
    print(f"  {len(thin):>3} skipped, attested by fewer than {need} printings")
    print(f"  {len(offgrid):>3} skipped, not a cell on this grid")
    print(f"  {len(badspan):>3} skipped, the span names rows that are not "
          f"adjacent")
    print(f"  {len(split):>3} skipped, the printings disagree with each other")
    print(f"  {len(collided):>3} skipped, two designators claim the same cell")
    print(f"  {len(unnamed):>3} skipped, the device name is not one we can stand behind")
    for des, part in unnamed:
        print(f"      unnamed {des}: {part!r}")
    for cell, d1, p1, d2, p2 in collided:
        print(f"      collision at {cell}: {d1}={p1} against {d2}={p2}")
    for cell, was, now, n in conflicts:
        print(f"      conflict {cell}: drawing {was}, parts lists {now} "
              f"({n} printings)")
    for des, part in badspan:
        print(f"      impossible span {des}: {part} — those rows are not "
              f"adjacent on this grid")
    for des, part in offgrid[:8]:
        print(f"      off-grid {des}: {part}")
    for des, v in list(split.items())[:8]:
        print(f"      split {des}: {sorted(set(v.values()))}")

    if not a.apply:
        print("\n(dry run — pass --apply to write)")
        return

    disputed = {c: (now, n) for c, was, now, n in conflicts}
    ics = dict(drawing)
    for cell, (part, n, span) in added.items():
        ics[cell] = part
        if span:
            spans[cell] = span
    board["ics"] = dict(sorted(ics.items()))
    if spans:
        board["spans"] = spans
    board["coverage"] = (
        f"{len(ics)} devices: {len(drawing)} read from the drawings and "
        f"{len(added)} recovered from the IC parts lists, taken only where "
        f"{need} or more printings agree. The chip lookup names the source for "
        f"each one. This is a board map, not a complete bill of materials.")
    json.dump(board, open(bpath, "w"), indent=1)

    cpath = os.path.join(ROOT, "data", "chips", a.slug + ".json")
    chips = json.load(open(cpath)) if os.path.exists(cpath) else {}
    # The chip lookup legitimately holds more than `ics` does: crystals,
    # transistors, resistor packs, test points — devices that are on the board
    # and worth answering for, but that `build_board.py` cannot place because
    # they are not on the letter-number grid. Rebuilding from `ics` alone drops
    # them, which is a silent loss of hand-read work.
    out = {k: {**v, "source": v.get("source") or "component-location drawing"}
           for k, v in chips.items() if k not in board["ics"]}
    for cell, part in board["ics"].items():
        prev = chips.get(cell, {})
        if cell in added:
            _, n, _ = added[cell]
            src = f"IC parts list, {n} printing" + ("s" if n > 1 else "")
        else:
            src = "component-location drawing"
            if cell in confirmed:
                src += ", confirmed by the parts list"
        note = prev.get("note", "")
        # Where the drawing wins a disagreement, the loser goes in the note.
        # The rule keeps the drawing because it is someone looking at the
        # board, but a reader at the bench should know that five manuals say
        # something else about the chip in front of them.
        if cell in disputed:
            other, n = disputed[cell]
            note = (note + " " if note else "") + (
                f"The IC parts lists call this a {other} "
                f"({n} printing{'s' if n > 1 else ''}); the drawing says "
                f"{part}. Unresolved.")
            src += ", disputed by the parts lists"
        out[cell] = {"part": part, "section": prev.get("section", ""),
                     "note": note.strip(),
                     "otherRev": prev.get("otherRev"), "source": src}
    json.dump(dict(sorted(out.items())), open(cpath, "w"), indent=1)
    offgrid_kept = len(out) - len(board["ics"])
    print(f"\nwrote {bpath}\n      {cpath}"
          + (f"\n      {offgrid_kept} off-grid devices kept in the lookup"
             if offgrid_kept else ""))


if __name__ == "__main__":
    main()
