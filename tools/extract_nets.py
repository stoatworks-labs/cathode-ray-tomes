#!/usr/bin/env python3
"""Extract circuit connectivity from a scanned schematic sheet.

These drawings are unusually tractable: clean bilevel line art, wires almost
entirely orthogonal, junctions drawn as filled dots, components as labelled
rectangles. That makes classical CV a better fit than anything learned.

  1. isolate wires        long orthogonal runs survive directional opening
  2. bridge junctions     filled dots join crossing runs into one conductor
  3. label nets           connected components of the wire mask
  4. find components      rectangular outlines that are not wires
  5. attach pins          wire endpoints terminating at a component edge

Pin *numbers* are the weak link — they are 10px-tall stencilled digits and OCR
on them is unreliable. Topology is recovered regardless, so a net is known to
exist and to touch a given component edge even when its pin number is not.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

Image.MAX_IMAGE_PIXELS = None

def load(path, box=None):
    im = Image.open(path).convert("L")
    if box:
        im = im.crop(box)
    return np.array(im) < 128

def wire_mask(ink, run=45, thick=13):
    """Long orthogonal runs are wires; text and gate bodies are not.

    Directional opening finds the runs but eats the corners — an L-bend belongs
    to neither a long horizontal nor a long vertical run, so the net splits in
    two exactly where it turns. Reconstructing the runs back through the thin
    ink recovers corners without re-admitting text or filled bodies.
    """
    hor = ndimage.binary_opening(ink, np.ones((1, run)))
    ver = ndimage.binary_opening(ink, np.ones((run, 1)))
    seeds = hor | ver
    # thin ink = strokes, excluding anything solid enough to be a body or glyph
    thin = ink & ~ndimage.binary_opening(ink, np.ones((thick, thick)))
    return ndimage.binary_propagation(seeds, mask=thin | seeds)

def junction_dots(ink, lo=6, hi=26):
    """Solid round blobs sitting on wires: the draughtsman's junction dot."""
    thin = ndimage.binary_opening(ink, np.ones((1, 12))) | \
           ndimage.binary_opening(ink, np.ones((12, 1)))
    solid = ink & ~thin
    lab, n = ndimage.label(solid)
    out = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if lo <= h <= hi and lo <= w <= hi and abs(h - w) <= 6:
            out.append(((sl[0].start + sl[0].stop) // 2,
                        (sl[1].start + sl[1].stop) // 2))
    return out

def components(ink, wires, min_side=40):
    """Component outlines: rectangles left once wires are removed."""
    body = ink & ~ndimage.binary_dilation(wires, np.ones((3, 3)))
    filled = ndimage.binary_closing(body, np.ones((9, 9)))
    lab, n = ndimage.label(filled)
    boxes = []
    for sl in ndimage.find_objects(lab):
        h = sl[0].stop - sl[0].start
        w = sl[1].stop - sl[1].start
        if h >= min_side and w >= min_side:
            boxes.append((sl[0].start, sl[1].start, sl[0].stop, sl[1].stop))
    return boxes

def nets(wires, dots, bridge=9):
    """Connected wire runs, with junction dots bridging crossings.

    Without the dots a crossing looks identical to a connection; with them,
    only dotted crossings merge — which is exactly the drawing convention.
    """
    m = wires.copy()
    for (y, x) in dots:
        y0, y1 = max(0, y - bridge), y + bridge
        x0, x1 = max(0, x - bridge), x + bridge
        m[y0:y1, x0:x1] = True
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    sizes = ndimage.sum(m, lab, range(1, n + 1))
    keep = {i + 1 for i, s in enumerate(sizes) if s > 200}
    return lab, keep

def attach(lab, keep, boxes, pad=14):
    """Which nets touch which component, via wires meeting its outline."""
    hits = {}
    for bi, (y0, x0, y1, x1) in enumerate(boxes):
        ring = np.zeros(lab.shape, bool)
        ring[max(0, y0 - pad):y1 + pad, max(0, x0 - pad):x1 + pad] = True
        ring[y0:y1, x0:x1] = False
        touching = {int(v) for v in np.unique(lab[ring]) if int(v) in keep}
        if touching:
            hits[bi] = sorted(touching)
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--box", help="x0,y0,x1,y1 fractional crop, e.g. .66,.31,.80,.42")
    ap.add_argument("--json", help="write the extracted graph here")
    a = ap.parse_args()

    im = Image.open(a.image)
    box = None
    if a.box:
        f = [float(v) for v in a.box.split(",")]
        W, H = im.size
        box = (int(W * f[0]), int(H * f[1]), int(W * f[2]), int(H * f[3]))

    ink = load(a.image, box)
    wires = wire_mask(ink)
    dots = junction_dots(ink)
    boxes = components(ink, wires)
    lab, keep = nets(wires, dots, bridge=9)
    hits = attach(lab, keep, boxes)

    print(f"region        {ink.shape[1]}x{ink.shape[0]} px")
    print(f"components    {len(boxes)}")
    print(f"junction dots {len(dots)}")
    print(f"nets          {len(keep)}")
    print(f"attachments   {sum(len(v) for v in hits.values())} "
          f"across {len(hits)} components")
    deg = sorted((len(v) for v in hits.values()), reverse=True)
    print(f"nets per component (desc): {deg[:12]}")

    if a.json:
        json.dump({
            "components": [{"id": i, "box": list(map(int, b))} for i, b in enumerate(boxes)],
            "nets": sorted(int(k) for k in keep),
            "attachments": {str(k): v for k, v in hits.items()},
        }, open(a.json, "w"), indent=1)
        print(f"-> {a.json}")

if __name__ == "__main__":
    main()
