#!/usr/bin/env python3
"""Index the diagnostic material across the corpus, per machine.

Someone with a dead board wants the self-test procedure, the troubleshooting
chart and the adjustment steps — not the whole manual. Those sections are
already recovered as headings, so this collects them per machine and deep-links
to the page they start on.

  data/diagnostics/<machine>.json  [{doc, title, section, page, kind}]
"""
import json, glob, os, re
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "diagnostics")

KINDS = [
    ("self-test",      re.compile(r"self[\s-]?test", re.I)),
    ("troubleshooting", re.compile(r"trouble[\s-]?shoot|fault|symptom|diagnos", re.I)),
    ("adjustment",     re.compile(r"adjust|align|calibrat", re.I)),
    ("test equipment", re.compile(r"test\s+(point|equipment|procedure)", re.I)),
    ("schematic",      re.compile(r"schematic|wiring\s+diagram", re.I)),
    ("dip switches",   re.compile(r"option\s+switch|dip\s+switch|switch\s+setting", re.I)),
    ("safety",         re.compile(r"warning|caution|safety|shock", re.I)),
]

def classify(text):
    for kind, rx in KINDS:
        if rx.search(text):
            return kind
    return None

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.json")):
        os.unlink(f)

    docs = {d["id"]: d for d in json.load(open(os.path.join(ROOT, "data/index/docs.json")))}
    per_machine = defaultdict(list)

    for fp in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        did = os.path.basename(fp)[:-5]
        meta = docs.get(did)
        if not meta:
            continue
        try:
            doc = json.load(open(fp))
        except Exception:
            continue
        for h in doc.get("outline", []):
            kind = classify(h["t"])
            if not kind:
                continue
            per_machine[meta["machine"]].append({
                "doc": did, "title": meta["title"], "section": h["t"],
                "page": h["p"], "kind": kind,
            })

    order = {k: i for i, (k, _) in enumerate(KINDS)}
    total = 0
    for machine, rows in per_machine.items():
        rows.sort(key=lambda r: (order.get(r["kind"], 99), r["title"], r["page"]))
        json.dump(rows[:200], open(os.path.join(OUT, machine + ".json"), "w"),
                  separators=(",", ":"))
        total += len(rows)

    print(f"{len(per_machine)} machines with diagnostic sections, {total} sections total")
    top = sorted(per_machine.items(), key=lambda kv: -len(kv[1]))[:6]
    for m, rows in top:
        kinds = {}
        for r in rows:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print(f"  {m:<22} {len(rows):>3}  " +
              ", ".join(f"{v} {k}" for k, v in sorted(kinds.items(), key=lambda x: -x[1])[:4]))

if __name__ == "__main__":
    main()
