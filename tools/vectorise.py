#!/usr/bin/env python3
"""Vectorise scanned line-art pages to SVG.

The schematic and wiring-diagram pages in this corpus are bilevel CCITT/JBIG2
scans -- clean black-on-white line work, which is exactly what potrace handles
well. Tracing them gives a resolution-independent SVG: a schematic sheet that
stays crisp at any zoom instead of turning to mush, at a fraction of the bytes
of the 300 dpi raster.

This recovers *geometry*, not meaning. It does not identify a resistor and
redraw it as an IEC symbol -- that is recognition work, done by hand per
diagram. What it does give is a clean, zoomable, selectable drawing.

  tools/vectorise.py <docId> [--pages 1,3] [--dpi 400]
"""
import argparse, json, os, subprocess, sys, tempfile, shutil, glob, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache")

def render_bilevel(pdf, outdir, dpi):
    """-mono gives potrace the 1bpp PBM it wants, with no half-tone noise."""
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["pdftoppm", "-r", str(dpi), "-mono", pdf,
                    os.path.join(outdir, "p")], capture_output=True, timeout=1800)
    files = [f for f in os.listdir(outdir) if f.endswith(".pbm")]
    return sorted(files, key=lambda f: int(re.search(r"-(\d+)\.", f).group(1)))

def trace(pbm, svg, turd=4, alphamax=1.0, opttolerance=0.6):
    """turdsize drops speckles from the scan; alphamax keeps corners sharp."""
    subprocess.run([
        "potrace", pbm, "-s", "-o", svg,
        "--turdsize", str(turd),
        "--alphamax", str(alphamax),
        "--opttolerance", str(opttolerance),
        "--flat",
    ], check=True, capture_output=True)
    theme_aware(svg)

def theme_aware(svg):
    """potrace hard-codes black fill on a transparent ground, which renders
    black-on-black in a dark UI. Re-point the ink at currentColor so the page
    decides, and paint an explicit paper rect behind it."""
    s = open(svg).read()
    s = s.replace('fill="#000000"', 'fill="currentColor"')
    s = re.sub(r'(<g[^>]*fill=")#000000(")', r'\1currentColor\2', s)
    # Insert a paper-coloured backdrop as the first child of <svg>.
    m = re.search(r"<svg[^>]*>", s)
    if m:
        paper = '<rect width="100%" height="100%" fill="var(--paper,#fff)"/>'
        s = s[:m.end()] + paper + s[m.end():]
    open(svg, "w").write(s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("doc")
    ap.add_argument("--pages", help="comma-separated page numbers (default: all)")
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--outdir")
    a = ap.parse_args()

    pdf = os.path.join(CACHE, "pdf", a.doc + ".pdf")
    if not os.path.exists(pdf):
        sys.exit(f"no such document: {pdf}")
    outdir = a.outdir or os.path.join(CACHE, "vector", a.doc)
    os.makedirs(outdir, exist_ok=True)

    want = {int(x) for x in a.pages.split(",")} if a.pages else None
    tmp = tempfile.mkdtemp(prefix="crt-vec-")
    try:
        pbms = render_bilevel(pdf, tmp, a.dpi)
        total_raster = total_vector = 0
        for i, fn in enumerate(pbms, 1):
            if want and i not in want:
                continue
            src = os.path.join(tmp, fn)
            dst = os.path.join(outdir, f"p{i:04d}.svg")
            trace(src, dst)
            r = os.path.getsize(src)
            v = os.path.getsize(dst)
            total_raster += r
            total_vector += v
            paths = open(dst).read().count("<path")
            print(f"  p{i}: {paths} paths, {v/1024:.0f} KB SVG "
                  f"(from {r/1024:.0f} KB {a.dpi}dpi bitmap)")
        if total_vector:
            print(f"total: {total_vector/1024:.0f} KB vector vs {total_raster/1024:.0f} KB raster")
        print(f"-> {outdir}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
