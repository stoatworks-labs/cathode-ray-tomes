#!/usr/bin/env python3
"""Extract signature-analysis data from service drawings.

Signature analysis is the sharpest diagnostic tool in these manuals: you clip a
signature analyser to a pin, read a four-character code, and compare it with
the documented value. A mismatch localises the fault to that node — no logic
tracing required. Atari printed these charts for several games.

The codes use the HP signature character set (0-9 A C F H P U) and are printed
*rotated* alongside the IC pins, which is why a straight OCR pass finds almost
none. Rotating the sheet first takes the yield from 9 to 59 on Battlezone.
"""
import argparse, json, os, re, sys
from collections import defaultdict
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harvest_board import ocr

Image.MAX_IMAGE_PIXELS = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# HP signature analyser charset. Excludes B, D, E, G etc. by design, which is
# what makes these codes distinguishable from part numbers and pin numbers.
SIG = re.compile(r"^[0-9ACFHPU]{4}$")
# Pin numbers and obvious non-signatures that fit the shape by accident.
NOT_SIG = re.compile(r"^(0000|1111|CC\d\d|\d{2}(0[1-9]|1[0-9]|2[0-4]))$")
DESIG = re.compile(r"^([A-Z])/?([A-Z])?(\d{1,2})$")

def read(png, min_conf=45):
    """Two OCR passes in one coordinate frame.

    The IC designators are printed upright and the signatures rotated, so
    neither pass alone sees both. Signature coordinates are mapped back from
    the rotated frame into the original so the two can be associated.
    """
    im = Image.open(png)
    W, H = im.size

    desigs = []
    for w in ocr(png):
        t = w["t"].upper().strip(".,;:()[]")
        if w["c"] >= min_conf and DESIG.match(t):
            desigs.append({**w, "t": t})

    rot = png.replace(".png", ".rot.png")
    if not os.path.exists(rot):
        im.rotate(-90, expand=True).save(rot)
    sigs = []
    for w in ocr(rot):
        t = w["t"].upper().strip(".,;:()[]")
        if w["c"] < min_conf or not SIG.match(t) or NOT_SIG.match(t):
            continue
        # rotate(-90, expand) maps original (x, y) -> (H-1-y, x); invert it
        ox = w["y"]
        oy = H - 1 - w["x"]
        sigs.append({**w, "t": t, "x": ox, "y": oy})
    return sigs, desigs

def associate(sigs, desigs, max_dist=420):
    """Attach each signature to its nearest IC designator."""
    out = defaultdict(list)
    for s in sigs:
        best, bd = None, 1e9
        for d in desigs:
            dist = abs(d["x"] - s["x"]) + abs(d["y"] - s["y"])
            if dist < bd:
                best, bd = d, dist
        if best and bd <= max_dist:
            out[best["t"]].append(s["t"])
        else:
            out["(unplaced)"].append(s["t"])
    return {k: sorted(set(v)) for k, v in out.items()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheets", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()

    merged = defaultdict(set)
    total = 0
    for png in a.sheets:
        sigs, desigs = read(png)
        got = associate(sigs, desigs)
        total += len(sigs)
        print(f"  {os.path.basename(png)}: {len(sigs)} signatures, "
              f"{len(desigs)} designators -> {len(got)} groups")
        for k, v in got.items():
            merged[k].update(v)

    out = {k: sorted(v) for k, v in sorted(merged.items()) if k != "(unplaced)"}
    unplaced = sorted(merged.get("(unplaced)", []))
    print(f"total: {total} signatures across {len(out)} ICs "
          f"({len(unplaced)} unplaced)")
    if a.out:
        json.dump({"byDevice": out, "unplaced": unplaced},
                  open(a.out, "w"), indent=1)
        print(f"-> {a.out}")

if __name__ == "__main__":
    main()
