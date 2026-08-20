#!/usr/bin/env python3
"""Harvest a board map from schematic sheets automatically.

Hand-reading a drawing package gives an accurate complement but costs hours per
board. For diagnosis the useful facts are narrower — which chip sits at which
grid position — and those are printed together on the sheet, so OCR can harvest
them at scale.

A pair is accepted when a grid designator (letter + digits) sits close to a part
number (74xx / 9xxx / LSxxx / 82Sxxx), on the same line or immediately below.
Everything is scored, and low-confidence pairs are dropped rather than guessed.
"""
import argparse, csv, json, os, re, subprocess, tempfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DESIG = re.compile(r"^([A-R])(\d{1,2})$")
PART = re.compile(r"^(?:74)?(LS\d{2,3}|S\d{2,3}|\d{4,5}|82S\d{2,3})[A-Z]?$")
PART_CLEAN = re.compile(r"^(?:74)?(LS?\d{2,3}|\d{4,5}|82S\d{2,3})")

def ocr(png, psm="11"):
    base = tempfile.mktemp()
    try:
        subprocess.run(["tesseract", png, base, "--psm", psm, "tsv"],
                       capture_output=True, timeout=900)
        p = base + ".tsv"
        if not os.path.exists(p):
            return []
        out = []
        for r in csv.DictReader(open(p, errors="ignore"), delimiter="\t",
                                quoting=csv.QUOTE_NONE):
            t = (r.get("text") or "").strip()
            if not t or r.get("level") != "5":
                continue
            try:
                out.append({"t": t, "x": int(r["left"]), "y": int(r["top"]),
                            "w": int(r["width"]), "h": int(r["height"]),
                            "c": float(r["conf"])})
            except (ValueError, KeyError):
                continue
        return out
    finally:
        try: os.unlink(base + ".tsv")
        except OSError: pass

def normalise_part(t):
    t = t.upper().replace("O", "0") if re.match(r"^[A-Z]?\d", t) else t.upper()
    m = PART_CLEAN.match(t)
    if not m:
        return None
    p = m.group(1)
    if p.startswith("LS") or p.startswith("S"):
        return "74" + p
    return p

def harvest(png, min_conf=55, max_dist=70):
    words = [w for w in ocr(png) if w["c"] >= min_conf]
    desigs = [w for w in words if DESIG.match(w["t"].upper())]
    parts = []
    for w in words:
        p = normalise_part(w["t"])
        if p:
            parts.append((w, p))

    pairs = defaultdict(list)
    for d in desigs:
        dx, dy = d["x"], d["y"]
        best = None
        for w, p in parts:
            # same line, or the line directly beneath — how these sheets label
            dist = abs(w["x"] - dx) + abs(w["y"] - dy)
            vert = w["y"] - dy
            if abs(w["x"] - dx) > max_dist or not (-8 <= vert <= max_dist):
                continue
            if best is None or dist < best[0]:
                best = (dist, p)
        if best:
            pairs[d["t"].upper()].append(best[1])

    # keep the most common reading per designator
    out = {}
    for desig, cands in pairs.items():
        counts = defaultdict(int)
        for c in cands:
            counts[c] += 1
        part, n = max(counts.items(), key=lambda kv: kv[1])
        out[desig] = {"part": part, "votes": n, "candidates": len(cands)}
    return out, len(desigs), len(parts)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheets", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()

    merged = {}
    for s in a.sheets:
        got, nd, np_ = harvest(s)
        print(f"  {os.path.basename(s)}: {nd} designators, {np_} parts -> {len(got)} pairs")
        for k, v in got.items():
            if k not in merged or v["votes"] > merged[k]["votes"]:
                merged[k] = v
    print(f"total: {len(merged)} designator/part pairs")
    if a.out:
        json.dump(merged, open(a.out, "w"), indent=1, sort_keys=True)
        print(f"-> {a.out}")

if __name__ == "__main__":
    main()
