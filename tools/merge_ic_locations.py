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
from extract_ic_locations import locations, device_key


def split_designator(desig):
    """'B/C10' -> ('B10', 'B/C10'); 'C3' -> ('C3', None)."""
    head = desig.rstrip("0123456789")
    col = desig[len(head):]
    if "/" not in head:
        return desig, None
    return head.split("/")[0] + col, desig


def harvest(doc_ids):
    """{designator: (part, n_printings)} where the printings agree."""
    per = {}
    for fid in doc_ids:
        try:
            per[fid] = locations(fid)[0]
        except Exception as e:
            print(f"  ! {fid}: {e}")
    votes = defaultdict(dict)
    for fid, loc in per.items():
        for des, part in loc.items():
            votes[des][fid] = part
    agreed, split = {}, {}
    for des, v in votes.items():
        keys = {device_key(p) for p in v.values()}
        if len(keys) == 1:
            # keep the longest spelling seen; the short ones are OCR losing
            # the family letters, and '74LS157' is more use than '157'
            agreed[des] = (max(v.values(), key=len), len(v))
        else:
            split[des] = v
    return agreed, split, len(per)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--docs", nargs="+", required=True)
    ap.add_argument("--allow-single", action="store_true",
                    help="accept a designator attested by only one printing")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    bpath = os.path.join(ROOT, "boards", a.slug + ".json")
    board = json.load(open(bpath))
    rows = board["grid"]["rows"]
    drawing = dict(board["ics"])
    spans = dict(board.get("spans", {}))

    agreed, split, ndocs = harvest(a.docs)
    print(f"{ndocs} printings, {len(agreed)} designators agreed, "
          f"{len(split)} split between printings\n")

    need = 1 if a.allow_single else 2
    added, confirmed, conflicts, offgrid, thin = {}, [], [], [], []
    collided = []
    for des, (part, n) in sorted(agreed.items()):
        cell, span = split_designator(des)
        if cell[0] not in rows or not cell[1:].isdigit():
            offgrid.append((des, part))
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
    print(f"  {len(split):>3} skipped, the printings disagree with each other")
    print(f"  {len(collided):>3} skipped, two designators claim the same cell")
    for cell, d1, p1, d2, p2 in collided:
        print(f"      collision at {cell}: {d1}={p1} against {d2}={p2}")
    for cell, was, now, n in conflicts:
        print(f"      conflict {cell}: drawing {was}, parts lists {now} "
              f"({n} printings)")
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
    out = {}
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
    print(f"\nwrote {bpath}\n      {cpath}")


if __name__ == "__main__":
    main()
