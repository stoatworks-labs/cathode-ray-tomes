#!/usr/bin/env python3
"""Publish a board: interactive view, BOM, and registration on the site.

Everything after the board definition is mechanical, so this is one command
rather than three ad-hoc snippets each time a board gains devices.
"""
import argparse, collections, csv, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KP = ("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/"
      "Versions/3.9/bin/python3")
IBOM = os.path.expanduser("~/Documents/KiCad/10.0/3rdparty/plugins/"
                          "org_openscopeproject_InteractiveHtmlBom/"
                          "generate_interactive_bom.py")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--machine", help="machine slug this board belongs to")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.slug + ".json")))
    web = os.path.join(ROOT, "web", "boards", a.slug)
    os.makedirs(web, exist_ok=True)

    pcb = os.path.join(ROOT, "kicad", a.slug, a.slug + ".kicad_pcb")
    subprocess.run([KP, IBOM, "--no-browser", "--dark-mode", "--show-fabrication",
                    "--layer-view", "F", "--include-nets",
                    "--name-format", f"{a.slug}-ibom", "--dest-dir", web, pcb],
                   capture_output=True, timeout=600)

    by = collections.defaultdict(list)
    for desig, part in spec["ics"].items():
        by[part].append(desig)
    with open(os.path.join(web, "bom.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Reference", "Value", "Quantity"])
        for part, ds in sorted(by.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            w.writerow([",".join(sorted(ds)), part, len(ds)])

    bp = os.path.join(ROOT, "data", "boards.json")
    boards = [b for b in json.load(open(bp)) if b["slug"] != a.slug]
    boards.append({
        "slug": a.slug, "name": spec["name"], "mfr": spec.get("mfr", ""),
        "year": spec.get("year", ""), "machine": a.machine or spec.get("machine", ""),
        "drawing": spec.get("drawing", ""), "devices": len(spec["ics"]),
        "netsTraced": spec.get("netsTraced", False),
        "status": spec.get("coverage", ""),
        "ibom": f"/boards/{a.slug}/{a.slug}-ibom.html",
        "bom": f"/boards/{a.slug}/bom.csv",
    })
    boards.sort(key=lambda b: (b.get("mfr", ""), b["name"]))
    json.dump(boards, open(bp, "w"), indent=1)
    print(f"{spec['name']}: {len(spec['ics'])} devices, {len(by)} BOM line items")
    print(f"  {len(boards)} boards registered")

if __name__ == "__main__":
    main()
