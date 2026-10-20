#!/usr/bin/env python3
"""Publish a board: interactive view, BOM, and registration on the site.

Everything after the board definition is mechanical, so this is one command
rather than three ad-hoc snippets each time a board gains devices.
"""
import argparse, collections, csv, glob, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KP = ("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/"
      "Versions/3.9/bin/python3")
KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
REPO = "https://github.com/stoatworks-labs/cathode-ray-tomes"
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


def export_sheets(sch, pdf):
    """Plot a schematic's whole hierarchy into one PDF; returns its sheets.

    Each sheet comes with the page it opens at, read back off the PDF's own
    title block, so the list cannot drift from the order KiCad plots in.
    """
    subprocess.run([KICAD_CLI, "sch", "export", "pdf", "-o", pdf, sch], check=True, capture_output=True)
    text = subprocess.run(["pdftotext", "-layout", pdf, "-"], check=True, capture_output=True,
                          text=True).stdout
    sheets = []
    for i, page in enumerate(text.split("\f"), 1):
        if not page.strip():
            continue
        m = re.search(r"Sheet: (/.*?/|/)(?:\s{2,}|\n|$)", page)
        path = m.group(1) if m else ""
        title = " / ".join(x for x in path.strip("/").split("/") if x) or "Top sheet"
        sheets.append({"title": title, "page": i})
    return sheets


def publish_imported(slug, spec, web):
    """Export an imported schematic -- one this repository did not draw.

    A jtcores board runs to a dozen sheets or more and there are forty of them,
    so the page gets one PDF and a list of its sheets, each linked to its page,
    rather than an SVG a sheet: the deploy is within a few thousand files of the
    Workers Assets cap.
    """
    sch = os.path.join(ROOT, "kicad", slug, spec["kicadRoot"])
    shutil.rmtree(os.path.join(web, "schematic"), ignore_errors=True)
    sheets = export_sheets(sch, os.path.join(web, "schematic.pdf"))
    return {"pdf": f"/boards/{slug}/schematic.pdf", "sheets": sheets,
            "project": spec["origin"]["source"],
            "netlist": f"{REPO}/blob/main/boards/{slug}.netlist.json"}


def publish_schematic(slug, web):
    """Export a board's redrawn KiCad schematic, where it has one, for the site.

    kicad/<slug>/<slug>.kicad_sch is drawn from the hand-read netlist (see
    tools/plan_board_schematic.py) and checked against it by
    tools/check_board_schematic.py. The page gets one SVG per sheet, titled from
    the plan, a PDF of the lot, and a link to the project itself on GitHub.
    """
    sch = os.path.join(ROOT, "kicad", slug, slug + ".kicad_sch")
    if not os.path.exists(sch):
        return None
    out = os.path.join(web, "schematic")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    subprocess.run([KICAD_CLI, "sch", "export", "svg", "--exclude-drawing-sheet", "-o", out, sch],
                   check=True, capture_output=True)
    subprocess.run([KICAD_CLI, "sch", "export", "pdf", "-o",
                    os.path.join(web, "schematic.pdf"), sch], check=True, capture_output=True)
    plans = {}
    for p in glob.glob(os.path.join(ROOT, "kicad", slug, "plan", "*.json")):
        plan = json.load(open(p))
        if isinstance(plan, dict) and "title" in plan:
            plans[plan["file"]] = plan
    # Sheets are shown in the order the board's layout lists them.
    lpath = os.path.join(ROOT, "boards", slug + ".sheets.json")
    order = [s["key"] for s in json.load(open(lpath))["sheets"]] if os.path.exists(lpath) else []
    sheets = []
    for f in sorted(os.listdir(out)):
        # kicad-cli names a sheet's SVG after the project and the sheet name;
        # the root sheet is only the sheet boxes and is not shown.
        stem = f[:-4]
        if stem == slug:
            os.remove(os.path.join(out, f))
            continue
        tidy = re.sub(r"[^a-z0-9]+", "-", stem[len(slug):].lower()).strip("-") + ".svg"
        os.rename(os.path.join(out, f), os.path.join(out, tidy))
        title = next((pl["title"] for pl in plans.values()
                      if re.sub(r"[^a-z0-9]+", "-", pl["title"].lower()).strip("-") + ".svg" == tidy), stem)
        key = next((pl["sheet"] for pl in plans.values() if pl["title"] == title), "")
        sheets.append({"title": title, "svg": f"/boards/{slug}/schematic/{tidy}",
                       "order": order.index(key) if key in order else 99})
    sheets.sort(key=lambda s: s.pop("order"))
    return {"pdf": f"/boards/{slug}/schematic.pdf", "sheets": sheets,
            "project": f"{REPO}/tree/main/kicad/{slug}",
            "netlist": f"{REPO}/blob/main/boards/{slug}.nets"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--machine", help="machine slug this board belongs to")
    a = ap.parse_args()

    spec = json.load(open(os.path.join(ROOT, "boards", a.slug + ".json")))
    web = os.path.join(ROOT, "web", "boards", a.slug)
    os.makedirs(web, exist_ok=True)

    pcb = os.path.join(ROOT, "kicad", a.slug, a.slug + ".kicad_pcb")
    has_pcb = os.path.exists(pcb) and bool(spec["ics"])
    if has_pcb:
        subprocess.run([KP, IBOM, "--no-browser", "--dark-mode", "--show-fabrication",
                        "--layer-view", "F", "--include-nets",
                        "--name-format", f"{a.slug}-ibom", "--dest-dir", web, pcb],
                       capture_output=True, timeout=600)

    # An imported board brings its schematic (jtcores) or only a netlist
    # (DICE, whose source is an emulator's, not a drawing).
    redrawn = publish_imported(a.slug, spec, web) if spec.get("kicadRoot") \
        else publish_schematic(a.slug, web)

    # An imported drawing names every part, passives and all, so its bill of
    # materials can too; a board read off a location drawing has only `ics`.
    by = collections.defaultdict(list)
    for desig, part in spec.get("parts", spec["ics"]).items():
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
        "ibom": f"/boards/{a.slug}/{a.slug}-ibom.html" if has_pcb else "",
        "bom": f"/boards/{a.slug}/bom.csv",
        "conflicts": conflicts,
        "notes": notes,
    })
    if redrawn:
        boards[-1]["redrawn"] = redrawn
    # A board that belongs to several machines -- a system board, or one game
    # board its sequels run on -- lists the rest; `machine` stays the first.
    # Licence and origin go with a board this repository did not draw: the
    # page has to say whose drawing it is and on what terms.
    for k in ("machines", "license", "origin", "partial"):
        if spec.get(k):
            boards[-1][k] = spec[k]
    if spec.get("origin") and not redrawn:
        boards[-1]["netlist"] = f"{REPO}/blob/main/boards/{a.slug}.netlist.json"
    # The schematic is built by tools/build_board_schematic.py, not from the
    # spec, so it is only ever in the previous record. Rebuilding without it
    # silently dropped Pong's sheet -- the file kept shipping, nothing pointed
    # at it, and the board page rendered an <img> with an empty src.
    for k in ("sheet", "sheetKind", "sheetSource", "schematicDocs"):
        if prev.get(k):
            boards[-1][k] = prev[k]
    boards.sort(key=lambda b: (b.get("mfr", ""), b["name"]))
    json.dump(boards, open(bp, "w"), indent=1)
    print(f"{spec['name']}: {len(spec['ics'])} devices, {len(by)} BOM line items")
    print(f"  {len(boards)} boards registered")

if __name__ == "__main__":
    main()
