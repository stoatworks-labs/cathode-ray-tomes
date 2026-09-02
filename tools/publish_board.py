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

def compose_status(spec):
    """The one-line status the site shows under a board.

    `revision` says what makes this board different from its siblings and
    `coverage` says how much of it has been read; the site shows them as one
    sentence, so they are joined here rather than duplicated in the spec.
    """
    return " ".join(x for x in (spec.get("revision"), spec.get("coverage")) if x)


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

    # Every conflict a read ever logged went into boards/<slug>.read.json, and
    # that file is not served — so a repairer looking at the page never saw
    # that A5 is disputed, or that MAME puts a ROM where the map has a 7400,
    # or that two sibling boards disagree with this one at H3. The whole point
    # of logging a conflict instead of guessing is that the reader gets to
    # weigh it, which they cannot do from a file in the repository. The read
    # file's notes and conflicts travel with the board from here on.
    rpath = os.path.join(ROOT, "boards", a.slug + ".read.json")
    read = json.load(open(rpath)) if os.path.exists(rpath) else {}
    conflicts = [c for c in read.get("conflicts", []) if isinstance(c, str)]
    notes = [n for n in read.get("notes", []) if isinstance(n, str)]

    bp = os.path.join(ROOT, "data", "boards.json")
    registered = json.load(open(bp))
    # Most board definitions carry no `machine` of their own — the link was
    # supplied by --machine the first time round and lives only in boards.json.
    # Republishing without the flag must not quietly unlink the board.
    prev = next((b for b in registered if b["slug"] == a.slug), {})
    boards = [b for b in registered if b["slug"] != a.slug]
    boards.append({
        "slug": a.slug, "name": spec["name"], "mfr": spec.get("mfr", ""),
        "year": spec.get("year", ""),
        "machine": a.machine or spec.get("machine") or prev.get("machine", ""),
        "drawing": spec.get("drawing") or prev.get("drawing", ""),
        "devices": len(spec["ics"]),
        "netsTraced": spec.get("netsTraced", prev.get("netsTraced", False)),
        # Boards recovered from a single printing carry no cross-check at all.
        # The site says so on the page rather than only in the provenance of
        # each device, because it changes how much the whole map is worth.
        "singleSource": spec.get("singleSource", prev.get("singleSource", False)),
        "status": compose_status(spec) or prev.get("status", ""),
        "ibom": f"/boards/{a.slug}/{a.slug}-ibom.html",
        "bom": f"/boards/{a.slug}/bom.csv",
        "conflicts": conflicts,
        "notes": notes,
    })
    boards.sort(key=lambda b: (b.get("mfr", ""), b["name"]))
    json.dump(boards, open(bp, "w"), indent=1)
    print(f"{spec['name']}: {len(spec['ics'])} devices, {len(by)} BOM line items")
    print(f"  {len(boards)} boards registered")

if __name__ == "__main__":
    main()
