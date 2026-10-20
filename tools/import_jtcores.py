#!/usr/bin/env python3
"""Import jotego/jtcores' KiCad board redraws as boards on this site.

jtcores recreates arcade boards in FPGA, and as part of that research its
contributors redraw the boards they study as KiCad schematics -- 43 of them are
whole boards or sections of one, against the handful this repository has traced
from scans. They are GPL-3.0, and so is everything made from them here.

Nothing in a jtcores drawing is changed. Per board in data/jtcores.json:

  kicad/<slug>/            the upstream sheets that make up the hierarchy, byte
                           for byte, with LICENSE and a NOTICE.md saying where
                           they came from, who drew them and what was added
  boards/<slug>.json       the board definition: every IC, placed on a nominal
                           layout (by its board position where the drawing names
                           ICs that way), its footprint sized from the symbol
  boards/<slug>.netlist.json   every net of two or more pins, from KiCad's own
                           netlist export of the copied sheets
  data/chips/<slug>.json   the chip lookup: designator, part, the sheet it is on
  data/signals/<slug>.json the signal lookup: named net -> sheets it reaches

Then, per board, tools/build_board.py builds the board view and
tools/publish_board.py the site's copy -- see AGENTS.md.

  python3 tools/import_jtcores.py --jt <jtcores checkout> [slug ...]

The checkout must be at the commit data/jtcores.json names, with its history:
the authors credited on each board are the people who committed its sheets.
"""
import argparse, collections, datetime, json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
REPO = "https://github.com/stoatworks-labs/cathode-ray-tomes"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kicad_netlist  # noqa: E402
from designators import parse as parse_desig  # noqa: E402

# Files that are part of a KiCad project. The .kicad_prl is one user's window
# layout, the .kicad_pcb in every board here is an empty stub, and backups and
# caches are not source.
KEEP_EXT = (".kicad_sch", ".kicad_pro", ".kicad_sym", ".kicad_dru", ".kicad_mod", ".lib", ".dcm")
KEEP_NAME = ("sym-lib-table", "fp-lib-table")

# A symbol that is on the board map only if it is not one of these. It is
# matched against the symbol's library name and description, never its value.
NOT_IC = re.compile(
    r"(?i)(\bconn|connector|header|jamma|\bedge\b|socket|r_network|r_pack|rpack|"
    r"resistor|\bsw_|switch|dip.?sw|jumper|\bemi\b|filter_|relay|transformer|"
    r"battery|crystal|resonator|speaker|potentiometer|r_pot|trimmer|\bled\b|diode|"
    r"capacitor|test.?point|\bsimm\b|slot|cartridge|fuse|ferrite|inductor|varistor|"
    r"thermistor|mounting|fiducial|transistor|q_npn|q_pnp|mosfet|rectifier|\bpwr_flag)")

# Commit names that are one person written two ways. Only merges the commit
# history itself supports: the title blocks give Ulf Skutnabba as @skutis77,
# and JOTEGO is Jose Tejada's handle.
ALIASES = {"skutis": "Ulf Skutnabba", "JOTEGO": "Jose Tejada", "FranR": "Fran.R"}


def hierarchy(src_dir, root_file):
    """Every sheet file the root reaches, root first, as paths relative to src_dir."""
    seen, todo = [], [root_file]
    while todo:
        f = todo.pop(0)
        if f in seen:
            continue
        seen.append(f)
        text = open(os.path.join(src_dir, f), errors="replace").read()
        # KiCad 6 spelled the property "Sheet file"; 7 onwards "Sheetfile".
        for child in re.findall(r'\(property "Sheet ?file" "([^"]+)"', text, re.I):
            child = os.path.normpath(os.path.join(os.path.dirname(f), child))
            if os.path.exists(os.path.join(src_dir, child)):
                todo.append(child)
    return seen


def generated(slug):
    """What tools/build_board.py writes beside the copy, and a re-import keeps."""
    return {"LICENSE", "NOTICE.md", f"{slug}.kicad_pcb", f"{slug}.kicad_pro"}


def copy_project(src_dir, dest, root_file):
    """Copy the project's hierarchy and settings verbatim; returns the files copied.

    Whatever an earlier import copied is cleared first, so a sheet upstream has
    dropped does not linger -- but not the board view built from the copy,
    which a bare re-import must not delete (it did, once, for 35 boards).
    """
    keep = generated(os.path.basename(dest))
    if os.path.isdir(dest):
        for f in os.listdir(dest):
            p = os.path.join(dest, f)
            if f in keep:
                continue
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(dest, exist_ok=True)
    files = hierarchy(src_dir, root_file)
    for f in sorted(os.listdir(src_dir)):
        full = os.path.join(src_dir, f)
        if os.path.isfile(full) and (f in KEEP_NAME or (f.endswith(KEEP_EXT) and not f.endswith(".kicad_sch"))):
            files.append(f)
    for f in files:
        os.makedirs(os.path.dirname(os.path.join(dest, f)) or dest, exist_ok=True)
        shutil.copyfile(os.path.join(src_dir, f), os.path.join(dest, f))
    return sorted(set(files))


def authors(jt, rel):
    r = subprocess.run(["git", "-C", jt, "log", "--format=%an", "--", rel],
                       capture_output=True, text=True, check=True)
    c = collections.Counter(ALIASES.get(a, a) for a in r.stdout.split("\n") if a)
    return [a for a, _ in c.most_common()]


def pin_count(lp):
    """The package's pin count, as the symbol numbers its pins (None if not numeric)."""
    nums = [int(n) for n, _, _ in lp["pins"] if n and n.isdigit()]
    return max(nums) if nums and len(nums) >= len(lp["pins"]) * 0.9 else None


_FPS = None


def footprints():
    global _FPS
    if _FPS is None:
        _FPS = {}
        for lib in ("Package_DIP", "Package_QFP"):
            d = os.path.join(FPLIB, lib + ".pretty")
            _FPS[lib] = sorted(f[:-10] for f in os.listdir(d) if f.endswith(".kicad_mod"))
    return _FPS


def footprint_for(n):
    """A footprint with at least n pins: DIP up to 64, a quad flat pack above.

    Nominal -- jtcores does not say what package a part is in, and the board
    view only needs every pin the schematic wires to have a pad to carry it.
    """
    fps = footprints()
    if n <= 64:
        dips = []
        for name in fps["Package_DIP"]:
            m = re.fullmatch(r"DIP-(\d+)_W(7\.62|15\.24)mm", name)
            if m:
                pins, w = int(m.group(1)), float(m.group(2))
                if pins >= n and (w == 7.62) == (pins <= 22 or n <= 20):
                    dips.append((pins, name))
        if dips:
            return "Package_DIP:" + min(dips)[1]
    quads = []
    for name in fps["Package_QFP"]:
        m = re.fullmatch(r"(PQFP|LQFP|TQFP)-(\d+)_([\d.]+)x([\d.]+)mm_P[\d.]+mm", name)
        if m and int(m.group(2)) >= n:
            quads.append((int(m.group(2)), {"PQFP": 0, "LQFP": 1, "TQFP": 2}[m.group(1)], name))
    if quads:
        return "Package_QFP:" + min(quads)[2]
    return "Package_QFP:PQFP-256_28x28mm_P0.4mm"


def envelope(fpid, upright=False):
    """(width, height, origin_dx, origin_dy, rotation) of a footprint as placed.

    Pin 1 is a DIP's footprint origin. Lying on its side (rotation 90) the body
    runs right of the origin and above it; upright (rotation 0), right of it and
    below. Quad packs are centred.
    """
    name = fpid.split(":")[1]
    m = re.match(r"DIP-(\d+)_W([\d.]+)mm", name)
    if m:
        length = (int(m.group(1)) // 2 - 1) * 2.54
        w = float(m.group(2))
        if upright:
            return w + 4.0, length + 4.0, 2.0, 2.0, 0
        return length + 4.0, w + 4.0, 2.0, w + 2.0, 90
    m = re.search(r"_([\d.]+)x([\d.]+)mm", name)
    a, b = (float(m.group(1)), float(m.group(2))) if m else (28.0, 28.0)
    return a + 6.0, b + 6.0, (a + 6.0) / 2, (b + 6.0) / 2, 0


def section(sheet):
    parts = [p for p in sheet.strip("/").split("/") if p]
    return " / ".join(parts)


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def layout(ics, fpids, transposed):
    """Board positions for every IC: (place, grid record or None, size).

    Where the drawing names ICs by board position (B9, 12F) they are laid out
    on that grid. Anything else -- a U-numbered board, or the stray U5 on a
    gridded one -- follows below in designator order. A letter that carries
    most of the board (all those U12, U34) is a numbering prefix, not a row.

    A big part takes several cells on the real board, and the next IC along is
    numbered past the cells it covers, so the spacing of the designators says
    roughly how far apart the cells are: the pitch is set where nineteen in twenty
    neighbours clear each other. Which way each DIP stands is not recorded, so
    each is stood upright at its cell unless that runs into a part already
    placed, in which case it is laid on its side -- the biggest parts first.
    What still collides is counted, not hidden.

    Whether the drawing writes B9 or 9B is read off its ICs when the manifest
    does not say: unlike an Atari sheet, a redraw is one convention throughout,
    so the majority is the answer.
    """
    if transposed is None:
        lf = sum(1 for r in ics if parse_desig(r, False))
        df = sum(1 for r in ics if parse_desig(r, True))
        transposed = df > lf
    parsed = {}
    for r in ics:
        p = parse_desig(r, transposed)
        if p and len(p[0]) == 1 and 1 <= p[1] <= 40:
            parsed[r] = p
    letters = collections.Counter(p[0] for p in parsed.values())
    prefix = {l for l, n in letters.items() if n >= 8 and n > 0.5 * len(ics)}
    grid = {r: p for r, p in parsed.items() if p[0] not in prefix}
    rows = sorted({p[0] for p in grid.values()})
    if not (len(grid) >= 0.5 * len(ics) and len(rows) >= 3):
        grid, rows = {}, []
    cols = sorted({p[1] for p in grid.values()})
    gap, margin = 3.0, 8.0

    def pitch(lines):
        need = []
        for parts in lines.values():
            parts.sort()
            need += [size / (b - a) for (a, size), (b, _) in zip(parts, parts[1:]) if b > a]
        need.sort()
        return round(max(10.0, need[int(0.95 * (len(need) - 1))] if need else 10.0) + 0.5, 1)

    along = collections.defaultdict(list)
    down = collections.defaultdict(list)
    for r, (row, col) in grid.items():
        w, h, *_ = envelope(fpids[r], True)
        along[row].append((col, w))
        down[col].append((rows.index(row), h))
    cp, rp = pitch(along), pitch(down)
    xs = {c: margin + (c - cols[0]) * cp for c in cols}
    ys = {row: margin + i * rp for i, row in enumerate(rows)}

    place, boxes, clashes = {}, [], 0

    def overlap(a, b):
        return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))

    biggest = sorted(grid, key=lambda r: -envelope(fpids[r], True)[0] * envelope(fpids[r], True)[1])
    for r in biggest:
        row, col = grid[r]
        tries = []
        for upright in (True, False):
            w, h, ox, oy, rot = envelope(fpids[r], upright)
            box = (xs[col], ys[row], xs[col] + w, ys[row] + h)
            tries.append((sum(overlap(box, b) for b in boxes), not upright, box, ox, oy, rot))
        hit, _, box, ox, oy, rot = min(tries)
        clashes += hit > 0
        boxes.append(box)
        place[r] = [round(box[0] + ox, 2), round(box[1] + oy, 2), rot]
    x = max((b[2] for b in boxes), default=margin) + gap
    y = max((b[3] for b in boxes), default=margin) + gap
    rest = sorted((r for r in ics if r not in grid), key=natural)
    area = sum(envelope(fpids[r], True)[0] * envelope(fpids[r], True)[1] for r in rest)
    right = max(x, 1.4 * area ** 0.5, 120.0)
    cx, cy, line_h = margin, (y + 10.0 if grid else margin), 0.0
    for r in rest:
        w, h, ox, oy, rot = envelope(fpids[r], True)
        if cx + w > right and cx > margin:
            cx, cy, line_h = margin, cy + line_h + gap, 0.0
        place[r] = [round(cx + ox, 2), round(cy + oy, 2), rot]
        cx += w + gap
        line_h = max(line_h, h)
    bottom = cy + line_h if rest else y
    size = {"w": round(max(right, x) + margin, 1), "h": round(bottom + margin, 1)}
    rec = {"rows": "".join(rows), "cols": max(cols), "transposed": bool(transposed)} if grid else None
    return place, rec, size, clashes


def describe(entry, n_parts, n_ics, n_nets, n_pins, sections, on_grid):
    # Who drew it and on what terms is the page's licence note, from `origin`;
    # the status says what is in the drawing, and what is not.
    names = ", ".join(sections) if sections else "one sheet"
    revision = entry.get("note", "")
    cover = (f"{n_parts} parts, {n_ics} of them ICs, and {n_nets} nets over {n_pins} pins, "
             f"on sheets for {names}.")
    if entry.get("partial"):
        cover += " The redraw covers only that part of the board."
    cover += (" Nothing in it has been checked against a manual or a board here. The board "
              "view carries the ICs and the nets between them; passives and connectors are "
              "in the schematic only. ")
    cover += ("The ICs sit at the board positions their designators name, on a nominal grid "
              "spacing." if on_grid else
              "The drawing numbers its ICs rather than naming board positions, so the board "
              "view lays them out in designator order -- the positions are not the board's.")
    return revision, cover


def import_board(entry, cfg, jt):
    slug = entry["slug"]
    src = os.path.join(jt, entry["dir"])
    pros = [f for f in os.listdir(src) if f.endswith(".kicad_pro")]
    if len(pros) != 1:
        raise RuntimeError(f"{entry['dir']}: expected one .kicad_pro, found {pros}")
    root_file = pros[0][:-len(".kicad_pro")] + ".kicad_sch"
    dest = os.path.join(ROOT, "kicad", slug)
    files = copy_project(src, dest, root_file)
    shutil.copyfile(os.path.join(jt, "LICENSE"), os.path.join(dest, "LICENSE"))

    comps, libparts, nets = kicad_netlist.read(
        kicad_netlist.export(os.path.join(dest, root_file)))
    # kicad-cli writes the project's local settings as it opens it. They are
    # not upstream's and not source; the copy must hold only what was copied.
    for f in os.listdir(dest):
        if f not in files and f not in generated(slug) and os.path.isfile(os.path.join(dest, f)):
            os.remove(os.path.join(dest, f))
    for f in files:
        with open(os.path.join(src, f), "rb") as a, open(os.path.join(dest, f), "rb") as b:
            if a.read() != b.read():
                raise RuntimeError(f"{slug}: {f} changed while exporting the netlist")
    nets = [n for n in nets if len(n["nodes"]) >= 2]

    ics, fpids, unmapped = {}, {}, []
    for ref, c in comps.items():
        lp = libparts.get((c["lib"], c["part"]), {"description": "", "pins": []})
        if NOT_IC.search(f"{c['part'] or ''} {c['lib'] or ''} {c['description']} {lp['description']}"):
            continue
        n = pin_count(lp)
        if n is None:
            if len(lp["pins"]) >= 6:
                unmapped.append(ref)
            continue
        if n < 6:
            continue
        ics[ref] = c["value"]
        fp = c["footprint"]
        ok = fp and ":" in fp and os.path.exists(
            os.path.join(FPLIB, fp.split(":")[0] + ".pretty", fp.split(":")[1] + ".kicad_mod"))
        fpids[ref] = fp if ok else footprint_for(n)
    place, grid, size, clashes = layout(ics, fpids, entry.get("transposed"))

    machine = json.load(open(os.path.join(ROOT, "web", "data", "machine", entry["machine"] + ".json")))
    machines = list(entry.get("machines", []))
    if entry.get("system"):
        for f in sorted(os.listdir(os.path.join(ROOT, "web", "data", "machine"))):
            rec = json.load(open(os.path.join(ROOT, "web", "data", "machine", f)))
            mm = rec.get("mame") or {}
            if mm.get("src") == entry["system"] and not mm.get("parent"):
                machines.append(rec["slug"])
    machines = [m for m in dict.fromkeys(machines) if m != entry["machine"]]

    who = authors(jt, entry["dir"])
    sections = sorted({section(c["sheet"]) for c in comps.values()} - {""})
    pins = sum(len(n["nodes"]) for n in nets)
    revision, coverage = describe(entry, len(comps), len(ics), len(nets), pins, sections,
                                  grid is not None)
    upstream = f"{cfg['repo']}/tree/{cfg['commit']}/{entry['dir']}"
    origin = {
        "project": "jtcores", "url": upstream, "commit": cfg["commit"], "path": entry["dir"],
        "authors": who, "license": cfg["license"],
        "licenseUrl": f"{REPO}/blob/main/kicad/{slug}/LICENSE",
        "source": f"{REPO}/tree/main/kicad/{slug}",
        "imported": datetime.date.today().isoformat(),
    }
    spec = {
        "slug": slug, "name": entry["name"], "mfr": machine.get("mfr", ""),
        "year": machine.get("year", ""), "machine": entry["machine"],
        "drawing": f"jtcores {entry['dir']} at {cfg['commit'][:8]}",
        "revision": revision, "coverage": coverage,
        "singleSource": False, "netsTraced": True,
        "license": cfg["license"], "origin": origin,
        "kicadRoot": root_file, "refPrefix": "", "size": size,
    }
    if machines:
        spec["machines"] = machines
    if entry.get("partial"):
        spec["partial"] = True
    if grid:
        spec["grid"] = grid
    spec["ics"] = {r: ics[r] for r in sorted(ics, key=natural)}
    spec["place"] = {r: place[r] for r in sorted(place, key=natural)}
    spec["footprints"] = {r: fpids[r] for r in sorted(fpids, key=natural)}
    spec["parts"] = {r: comps[r]["value"] for r in sorted(comps, key=natural)}
    dump(os.path.join(ROOT, "boards", slug + ".json"), spec)

    netlist = {"slug": slug, "source": f"kicad/{slug}/{root_file} (jtcores, {cfg['license']})",
               "license": cfg["license"], "components": {}, "nets": {}}
    for r in sorted(comps, key=natural):
        netlist["components"][r] = {"value": comps[r]["value"], "sheet": section(comps[r]["sheet"])}
    for n in nets:
        auto = n["name"].startswith(("Net-(", "unconnected-("))
        netlist["nets"][n["name"]] = {
            "pins": sorted({f"{ref}.{pin}" for ref, pin, _, _ in n["nodes"]}, key=natural),
            "named": "auto" if auto else "sheet", "aliases": []}
    dump(os.path.join(ROOT, "boards", slug + ".netlist.json"), netlist)

    chips = {}
    for r in sorted(ics, key=natural):
        c = comps[r]
        lp = libparts.get((c["lib"], c["part"]), {})
        desc = c["description"] or lp.get("description", "")
        chips[r] = {"part": c["value"], "section": section(c["sheet"]),
                    "note": desc if desc and desc.lower() != c["value"].lower() else "",
                    "otherRev": None, "source": "jtcores redraw"}
    dump(os.path.join(ROOT, "data", "chips", slug + ".json"), chips)

    signals = {}
    for n in nets:
        if n["name"].startswith(("Net-(", "unconnected-(")):
            continue
        where = collections.Counter(section(comps[ref]["sheet"]) or "top sheet"
                                    for ref, _, _, _ in n["nodes"] if ref in comps)
        signals[n["name"]] = dict(where.most_common())
    dump(os.path.join(ROOT, "data", "signals", slug + ".json"), signals)

    write_notice(dest, entry, cfg, slug, files, who, upstream)
    print(f"{slug}: {len(comps)} parts, {len(ics)} ICs ({'grid ' + grid['rows'] if grid else 'sequence'}), "
          f"{len(nets)} nets, {pins} pins, {len(files)} files, {size['w']:.0f}x{size['h']:.0f} mm"
          + (f", {clashes} placement clash(es)" if clashes else "")
          + (f"; {len(unmapped)} IC(s) with non-numeric pins left off the board view: "
             f"{', '.join(sorted(unmapped, key=natural)[:8])}" if unmapped else ""))


def write_notice(dest, entry, cfg, slug, files, who, upstream):
    today = datetime.date.today().isoformat()
    with open(os.path.join(dest, "NOTICE.md"), "w") as f:
        f.write(f"""# {entry['name']}

A KiCad schematic of the {entry['name']}, drawn for
[jtcores]({cfg['repo']}) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    {upstream}

**Drawn by** {', '.join(who)} (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`{cfg['commit']}`: the sheets the root reaches, and the project settings.

{chr(10).join('- `' + p + '`' for p in files)}

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On {today}, by `tools/import_jtcores.py` in this repository:

- `{slug}.kicad_pcb` (and the `{slug}.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/{slug}.json`, `boards/{slug}.netlist.json`,
  `data/chips/{slug}.json`, `data/signals/{slug}.json` and the published copy
  under `web/boards/{slug}/`.
""")


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jt", required=True, help="a jtcores checkout, with history")
    ap.add_argument("--verify", action="store_true",
                    help="check the copies under kicad/ against upstream; change nothing")
    ap.add_argument("slugs", nargs="*", help="boards to import (default: all)")
    a = ap.parse_args()
    cfg = json.load(open(os.path.join(ROOT, "data", "jtcores.json")))
    head = subprocess.run(["git", "-C", a.jt, "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != cfg["commit"]:
        sys.exit(f"{a.jt} is at {head}, but data/jtcores.json is pinned to {cfg['commit']}")
    bad = 0
    for entry in cfg["boards"]:
        if a.slugs and entry["slug"] not in a.slugs:
            continue
        if a.verify:
            bad += verify(entry, a.jt)
        else:
            import_board(entry, cfg, a.jt)
    if a.verify:
        print(f"{bad} file(s) differ from upstream" if bad else "every copied file matches upstream")
        sys.exit(1 if bad else 0)


def verify(entry, jt):
    """The claim NOTICE.md makes -- these are upstream's files, unchanged -- checked.

    KiCad rewrites a project's files when it opens one for editing, so a copy
    that someone opened and saved is no longer the file the notice describes.
    """
    return verify_copy(os.path.join(jt, entry["dir"]), os.path.join(ROOT, "kicad", entry["slug"]),
                       entry["slug"])


def verify_copy(src, dest, label):
    """How many of the files a copy of upstream project `src` should hold at
    `dest` are missing or differ from upstream's; each is reported."""
    root_file = next(f for f in os.listdir(src) if f.endswith(".kicad_pro"))[:-len(".kicad_pro")] + ".kicad_sch"
    want = hierarchy(src, root_file) + [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f))
                                        and (f in KEEP_NAME or (f.endswith(KEEP_EXT) and not f.endswith(".kicad_sch")))]
    bad = 0
    for f in sorted(set(want)):
        p = os.path.join(dest, f)
        if not os.path.exists(p) or open(p, "rb").read() != open(os.path.join(src, f), "rb").read():
            print(f"{label}: {f} is not upstream's")
            bad += 1
    return bad


if __name__ == "__main__":
    main()
