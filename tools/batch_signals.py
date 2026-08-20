#!/usr/bin/env python3
"""Build signal indexes for every machine that has schematic sheets.

Automated board maps are not achievable from these drawings — the part numbers
are hand-lettered and OCR recovers only a handful per sheet, consistently
across every Atari drawing package tested. Signal *names* are a different
matter: they are set as net labels and come through well, and they are what you
follow when chasing a symptom.

So this indexes what can be read reliably rather than guessing at what cannot.
Resumable: machines already done are skipped.
"""
import json, os, subprocess, sys, glob, time, argparse
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_signals import signals_from

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHEETS = os.path.join(ROOT, "cache", "sheets")
OUT = os.path.join(ROOT, "data", "signals")
STATE = os.path.join(ROOT, "data", "signals-state.json")

def render(doc_id, page=1, dpi=200):
    """Sheets must live under the project cache: tesseract cannot read /tmp
    here and fails silently, returning an empty result rather than an error."""
    out = os.path.join(SHEETS, f"{doc_id}-{page}.png")
    if os.path.exists(out):
        return out
    pdf = os.path.join(ROOT, "cache", "pdf", doc_id + ".pdf")
    if not os.path.exists(pdf):
        return None
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-gray",
                    "-f", str(page), "-l", str(page), pdf,
                    os.path.join(SHEETS, doc_id)],
                   capture_output=True, timeout=600)
    return out if os.path.exists(out) else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-sheets", type=int, default=6,
                    help="sheets per machine; drawing packages repeat heavily")
    a = ap.parse_args()

    os.makedirs(SHEETS, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"done": []}
    done = set(state["done"])

    docs = json.load(open(os.path.join(ROOT, "data/index/docs.json")))
    by_machine = defaultdict(list)
    for d in docs:
        if d.get("ingested") and d["schematic"] and d.get("pages", 0) <= 4:
            by_machine[d["machine"]].append(d)

    todo = [m for m in sorted(by_machine) if m not in done]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(todo)} machines to index ({len(done)} already done)", flush=True)

    t0 = time.time()
    for i, machine in enumerate(todo, 1):
        index = defaultdict(lambda: defaultdict(int))
        sheets = by_machine[machine][:a.max_sheets]
        for d in sheets:
            png = render(d["id"])
            if not png:
                continue
            try:
                for sig, pts in signals_from(png).items():
                    index[sig][d["title"].replace(".pdf", "")] += len(pts)
            except Exception:
                continue
        if index:
            json.dump({s: dict(v) for s, v in index.items()},
                      open(os.path.join(OUT, machine + ".json"), "w"),
                      separators=(",", ":"), sort_keys=True)
        done.add(machine)
        if i % 5 == 0 or i == len(todo):
            json.dump({"done": sorted(done)}, open(STATE, "w"))
            el = time.time() - t0
            rate = i / el * 60 if el else 0
            print(f"  [{i}/{len(todo)}] {machine}: {len(index)} signals | "
                  f"{rate:.1f} machines/min | ETA {(len(todo)-i)/max(rate,.1):.0f} min",
                  flush=True)
    json.dump({"done": sorted(done)}, open(STATE, "w"))
    print(f"done: {len(glob.glob(os.path.join(OUT,'*.json')))} signal indexes")

if __name__ == "__main__":
    main()
