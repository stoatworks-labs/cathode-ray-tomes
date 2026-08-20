#!/usr/bin/env python3
"""Build a signal index from the schematic sheets.

Chasing a signal is the core diagnostic loop: you have a symptom, the manual
names a signal, and you need to know where on the board to put a probe. The
drawings label their nets generously, so OCR over the sheets recovers a usable
index of which signals appear where — and, because the sheets are divided into
titled functional blocks, roughly what each one belongs to.

This indexes *names and locations*, not connectivity. It answers "where does
VBLANK appear" rather than "which pins are on it".
"""
import argparse, csv, json, os, re, subprocess, tempfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Signal names on these drawings: capitals, digits, and the odd slash/bar.
SIGNAL = re.compile(r"^[A-Z][A-Z0-9/_]{1,15}$")
# Reference designators and part numbers, not signals.
NOT_SIGNAL = re.compile(
    r"^(LS\d+|\d+|[A-R]\d{1,2}|C\d+|R\d+|Q\d+|CR\d+|J\d+|P\d+|TP\d+|"
    r"VCC|GND|F/F|CK|CE|WE|CS)$")

# The sheets carry explanatory prose in capitals as well as net labels, so a
# stopword list keeps ordinary words out of the index. Words that are genuinely
# signals on these boards (HALT, RESET, GO, BLANK) are deliberately absent.
PROSE = {
    "MPU","SW","COUNTER","VECTOR","AS","DATA","CIRCUITRY","IS","THE","AND","FOR",
    "SEE","PCB","IC","NOTE","ONLY","THRU","REV","ATARI","SHEET","SIDE","FIGURE",
    "TABLE","PROM","ROM","RAM","MUX","GENERATOR","MEMORY","ADDRESS","SELECTOR",
    "LATCH","LATCHES","BUFFER","TIMER","TIMERS","STATE","MACHINE","POSITION",
    "PROGRAM","OUTPUT","OUTPUTS","INPUT","INPUTS","POWER","SUPPLY","CLOCK",
    "CIRCUIT","VDC","VAC","COIN","SOUND","AUDIO","VIDEO","PLAYER","GAME","BOARD",
    "ASSY","ASSEMBLY","PART","LIST","WITH","FROM","TO","OF","ON","IN","BY","OR",
    "NOT","ALL","USE","SEL","DIP","LED","DAC","VOLUME","FIRE","SHIP","SAUCER",
    "LIFE","THUMP","EXPLOSION","START","TEST","DIAG","STEP","SLAM","HYPER",
    "THRUST","LEFT","RIGHT","CENTER","ROT","SELF","DISABLE","OUT","STOP","RATE",
    "MULT","DECODER","ADDER","DRVR","REG","FILE","XCVR","DIR","NOISE","RESET",
    "THIS","THAT","AT","BE","IF","IT","SO","AN","ARE","WAS","HAS","CAN","MAY",
    "SPLIT","PAD","PADS","WHEN","THEN","EACH","BOTH","INTO","ONE","TWO","ALSO",
    "PLYR","SPACE","SHIPS","HEARD","GAINED","MERELY","FROM","THEIR","THESE",
}

# Bus names are the ones people trace, and OCR reliably confuses O for 0 and
# I for 1 inside them (AB0 -> ABO, AB10 -> ABIO). Normalise within known buses
# so the index does not split one signal across three spellings.
BUS = re.compile(r"^(AB|DB|DVX|DVY|DACX|DACY|ADMA|DDMA|AM|LOAD|TIMER|SCALE)([O0-9I]+)$")

def normalise(t):
    m = BUS.match(t)
    if not m:
        return t
    return m.group(1) + m.group(2).replace("O", "0").replace("I", "1")

def ocr_words(png, psm="11"):
    """Return [(text, x, y, conf)] for a rendered sheet."""
    base = tempfile.mktemp()
    try:
        subprocess.run(["tesseract", png, base, "--psm", psm, "tsv"],
                       capture_output=True, timeout=900)
        rows = list(csv.DictReader(open(base + ".tsv", errors="ignore"),
                                   delimiter="\t", quoting=csv.QUOTE_NONE))
        out = []
        for r in rows:
            t = (r.get("text") or "").strip()
            if not t or r.get("level") != "5":
                continue
            try:
                out.append((t, int(r["left"]), int(r["top"]), float(r["conf"])))
            except (ValueError, KeyError):
                continue
        return out
    finally:
        for e in (".tsv",):
            try: os.unlink(base + e)
            except OSError: pass

def signals_from(png, min_conf=60):
    hits = defaultdict(list)
    for t, x, y, conf in ocr_words(png):
        t = normalise(t.strip(".,;:()[]"))
        if conf < min_conf or not SIGNAL.match(t) or NOT_SIGNAL.match(t):
            continue
        # Net labels on these drawings almost always carry a digit or a bar
        # suffix (DVX4, AB12, TIMER0, VGCK). Bare words are usually prose.
        if t in PROSE and not any(c.isdigit() for c in t):
            continue
        hits[t].append((x, y))
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheets", nargs="+", required=True,
                    help="rendered sheet PNGs, as label=path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-occurrences", type=int, default=1)
    a = ap.parse_args()

    index = defaultdict(lambda: defaultdict(int))
    for spec in a.sheets:
        label, path = spec.split("=", 1)
        for sig, pts in signals_from(path).items():
            index[sig][label] += len(pts)

    out = {s: dict(v) for s, v in index.items()
           if sum(v.values()) >= a.min_occurrences}
    json.dump(out, open(a.out, "w"), separators=(",", ":"), sort_keys=True)
    print(f"{len(out)} signals indexed across {len(a.sheets)} sheet(s) -> {a.out}")
    top = sorted(out.items(), key=lambda kv: -sum(kv[1].values()))[:14]
    for s, v in top:
        print(f"  {s:<14} {sum(v.values()):>3} occurrences  {', '.join(v)}")

if __name__ == "__main__":
    main()
