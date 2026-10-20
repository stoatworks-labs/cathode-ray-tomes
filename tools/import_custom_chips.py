#!/usr/bin/env python3
"""Import the custom chips jtcores redraws from the inside.

A dead custom is one of the commonest faults on a late-1980s board, and the
part cannot be bought. jtcores' contributors have redrawn thirteen of them in
KiCad -- nine Konami gate arrays from the Twin 16 boards, three Capcom DL-series
chips from Pang, and Konami's 052535 video DAC -- cell by cell off a die photo,
or part by part for the DAC. They are GPL-3.0 like the jtcores boards and are
handled the same way, but they are not boards, and are kept apart from them:

  kicad/chips/<slug>/        the upstream project, byte for byte, with LICENSE
                             and a NOTICE.md saying who drew it and from what
  data/customchips/<slug>.json   what the drawing says about the chip: its
                             pinout, its cells, its sheets, its own notes on
                             what it does and what silicon it is -- and how its
                             pinout compares with every board drawing here that
                             carries the part
  web/chips/<slug>.pdf       every sheet, as kicad-cli plots it

Which boards and machines carry each chip is not decided here: it changes
whenever a board is published, so tools/custom_chips.py works it out when
web/data/ is built (build_assets.py --chips-only).

  python3 tools/import_custom_chips.py --jt <jtcores checkout> [slug ...]
  python3 tools/import_custom_chips.py --jt <jtcores checkout> --verify

The checkout must be at the commit data/jtcores.json names, with its history:
the authors credited on each chip are the people who committed its sheets.

**The chip symbol in each of these projects is drawn from inside the die.** Its
pin types say which way a signal crosses the pad *into the core*, so a pin the
chip drives is an `input` on it. The board drawings draw the same parts from
outside, so where one exists here the pinout takes its directions from there;
where none does, the inside symbol's are turned round. Both are then checked
against the circuit itself: a pad whose net some cell inside drives is an
output, one that only feeds cell inputs is an input. At the pinned commit the
three agree on every pin where they all say input or output -- 681 pins for the
turned-round symbols, the three Capcom chips' 170 included, and 501 for the
board drawings -- and main() prints the count, so a new import that breaks the
rule says so.
"""
import argparse, collections, datetime, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = "https://github.com/stoatworks-labs/cathode-ray-tomes"
sys.path.insert(0, os.path.join(ROOT, "tools"))
import kicad_netlist  # noqa: E402
import import_jtcores as jt  # noqa: E402
from publish_board import export_sheets  # noqa: E402
from custom_chips import load_manifest, marking_re, natural  # noqa: E402

# A board drawing's pin type, as a repairer reads it off a pinout.
OUTSIDE = {"input": "in", "output": "out", "bidirectional": "in/out", "tri_state": "out (3-state)",
           "open_collector": "out (o.c.)", "open_emitter": "out (o.e.)", "power_in": "power",
           "power_out": "power", "passive": "", "no_connect": "", "unspecified": "", "free": ""}
# The same, for a symbol drawn from inside the die: the pad's direction turned round.
INSIDE = {"input": "out", "output": "in", "bidirectional": "in/out", "power_in": "power",
          "power_out": "power", "tri_state": "in/out"}

# Notes on a sheet worth carrying to the page verbatim: what silicon the
# drawing was read from, and the drawing's own account of what the chip does.
SILICON = re.compile(r"(?i)die picture|image by|gate (?:cell )?array|basic cells|unit cells")
FUNCTION = re.compile(r"(?i)^the (?:konami )?\d{6} (?:is|does|scans)\b")


def bare(name):
    """A pin name without KiCad's overbar markup: ~{SYLD} -> SYLD."""
    return re.sub(r"~\{([^}]*)\}", r"\1", name or "").strip()


def texts(path):
    """Every free text item on a sheet, unescaped, in file order."""
    raw = open(path, errors="replace").read()
    out = []
    for m in re.finditer(r'\(text "((?:[^"\\]|\\.)*)"', raw):
        out.append(re.sub(r"\\(.)", lambda e: {"n": "\n", "t": "\t"}.get(e.group(1), e.group(1)),
                          m.group(1)))
    return out


def export(dest, root_file, pdf=None):
    """(netlist, sheets) from a scratch copy of the project.

    kicad-cli writes a .kicad_prl into whatever project it opens, and the copy
    under kicad/ has to stay exactly upstream's, so it never opens that one.
    """
    with tempfile.TemporaryDirectory() as t:
        work = os.path.join(t, "p")
        shutil.copytree(dest, work)
        net = kicad_netlist.read(kicad_netlist.export(os.path.join(work, root_file)))
        sheets = export_sheets(os.path.join(work, root_file), pdf) if pdf else None
    return net, sheets


_BOARDS = {}


def board_symbols(slug):
    """{ref: (value, pins)} for every part on an imported board's drawing."""
    if slug not in _BOARDS:
        spec = json.load(open(os.path.join(ROOT, "boards", slug + ".json")))
        (comps, libparts, _), _ = export(os.path.join(ROOT, "kicad", slug), spec["kicadRoot"])
        _BOARDS[slug] = {r: (c["value"], libparts.get((c["lib"], c["part"]), {}).get("pins", []))
                         for r, c in comps.items()}
    return _BOARDS[slug]


def boards_drawing(entry):
    """Boards here whose own drawing carries this part: {slug: [refs]}.

    Only boards imported with a schematic (`kicadRoot`) have a symbol to compare
    with; a board read off a location drawing has a part number and no pinout.
    """
    pat = marking_re(entry["markings"])
    out = {}
    for b in json.load(open(os.path.join(ROOT, "data", "boards.json"))):
        if not b.get("redrawn") or not b.get("origin"):
            continue
        spec = json.load(open(os.path.join(ROOT, "boards", b["slug"] + ".json")))
        if not spec.get("kicadRoot"):
            continue
        refs = sorted((r for r, v in spec.get("parts", spec["ics"]).items() if pat.search(v or "")),
                      key=natural)
        if refs:
            out[b["slug"]] = refs
    return out


def compare(pins, board_pins):
    """How a board drawing's symbol for this part agrees with the chip's own.

    A name that differs only by its overbar is the same signal written without
    the active-low mark; a blank name is a symbol that does not name its pins.
    Both are reported, neither is called a disagreement.
    """
    theirs = {n: (name or "") for n, name, _ in board_pins}
    rec = {"same": 0, "overbar": [], "unnamed": 0, "differ": [], "missing": [], "extra": []}
    for n, name, _ in pins:
        if n not in theirs:
            rec["missing"].append(n)
        elif theirs[n] == name:
            rec["same"] += 1
        elif not theirs[n].strip():
            rec["unnamed"] += 1
        elif bare(theirs[n]) == bare(name):
            rec["overbar"].append([n, name, theirs[n]])
        else:
            rec["differ"].append([n, name, theirs[n]])
    ours = {n for n, _, _ in pins}
    rec["extra"] = sorted((n for n in theirs if n not in ours), key=natural)
    return rec


def driven(own, nets):
    """{pin: "out" | "in" | "in/out" | ""} by what the circuit inside does with
    each pad: a net some cell drives leaves the chip as an output, a net that
    only feeds cell inputs arrives as an input. Independent of how either
    symbol was drawn, which is why it is the check on both."""
    out = {}
    for n in nets:
        pads = [p for ref, p, _, _ in n["nodes"] if ref == own]
        others = [ty for ref, _, _, ty in n["nodes"] if ref != own]
        if any(t in ("output", "tri_state", "power_out", "open_collector") for t in others):
            d = "out"
        elif "bidirectional" in others:
            d = "in/out"
        elif "input" in others:
            d = "in"
        else:
            d = ""
        for p in pads:
            out[p] = d
    return out


def import_chip(entry, cfg, jtdir, measure):
    slug = entry["slug"]
    src = os.path.join(jtdir, entry["dir"])
    pros = [f for f in os.listdir(src) if f.endswith(".kicad_pro")]
    if len(pros) != 1:
        raise RuntimeError(f"{entry['dir']}: expected one .kicad_pro, found {pros}")
    root_file = pros[0][:-len(".kicad_pro")] + ".kicad_sch"
    dest = os.path.join(ROOT, "kicad", "chips", slug)
    files = jt.copy_project(src, dest, root_file)
    shutil.copyfile(os.path.join(jtdir, "LICENSE"), os.path.join(dest, "LICENSE"))

    pdf = os.path.join(ROOT, "web", "chips", slug + ".pdf")
    os.makedirs(os.path.dirname(pdf), exist_ok=True)
    (comps, libparts, nets), sheets = export(dest, root_file, pdf)
    if jt.verify_copy(src, dest, slug):
        raise RuntimeError(f"{slug}: the copy under kicad/chips/ is not upstream's")

    # The package: the one symbol drawn as the chip's inside.
    own = [r for r, c in comps.items() if (c["part"] or "").endswith("_internal")]
    if len(own) != 1:
        raise RuntimeError(f"{slug}: expected one *_internal chip symbol, found {own}")
    ref = own[0]
    lp = libparts[(comps[ref]["lib"], comps[ref]["part"])]
    pins = sorted(lp["pins"], key=lambda p: natural(p[0]))

    # Every board drawing here that carries the part, and what it calls each pin.
    checks, votes = [], collections.defaultdict(collections.Counter)
    for board, refs in boards_drawing(entry).items():
        syms = board_symbols(board)
        seen = {}
        for r in refs:
            value, bpins = syms.get(r, ("", []))
            seen.setdefault(tuple(bpins), []).append(r)
        for bpins, rs in seen.items():
            rec = compare(pins, bpins)
            checks.append({"board": board, "refs": rs, **rec})
            for n, _, ty in bpins:
                if OUTSIDE.get(ty):
                    votes[n][OUTSIDE[ty]] += 1
    drive = driven(ref, nets)
    pinout = []
    for n, name, ty in pins:
        turned = INSIDE.get(ty, "")
        if votes.get(n):
            d, src_of = votes[n].most_common(1)[0][0], "board"
            if d in ("in", "out") and drive.get(n) in ("in", "out"):
                measure["board"][drive[n] == d] += 1
        else:
            d, src_of = turned, "inside"
        if turned in ("in", "out") and drive.get(n) in ("in", "out"):
            measure["turned"][drive[n] == turned] += 1
            if drive[n] != turned:
                measure["against"][f"{slug} pin {n}"] += 1
        pinout.append({"n": n, "name": name, "dir": d, "from": src_of if d else "",
                       "drive": drive.get(n, "")})

    cells = collections.Counter(c["lib"] or "(drawn in the sheet)" for r, c in comps.items() if r != ref)
    named = [n for n in nets if not n["name"].startswith(("Net-(", "unconnected-("))]
    notes, seen_text = [], set()
    for f in files:
        if not f.endswith(".kicad_sch"):
            continue
        for t in texts(os.path.join(dest, f)):
            kind = "function" if FUNCTION.search(t) else "silicon" if SILICON.search(t) else None
            if kind and t not in seen_text:
                seen_text.add(t)
                notes.append({"kind": kind, "text": t.strip()})
    read_from = None
    for n in notes:
        m = re.search(r"die picture by\s+([^.\n]+)\.", n["text"])
        if m:
            read_from = f"a die photo by {m.group(1)}"
        m = re.search(r"image by\s+(\S+)\s+on\s+(\S+?)\.(?=\s|$)", n["text"])
        if m:
            read_from = f"an image by {m.group(1)} on {m.group(2)}"

    who = jt.authors(jtdir, entry["dir"])
    upstream = f"{cfg['repo']}/tree/{cfg['commit']}/{entry['dir']}"
    rec = {
        "slug": slug,
        "role": comps[ref]["description"] or lp["description"],
        "package": {"pins": len(pins), "symbol": f"{comps[ref]['lib']}:{comps[ref]['part']}"},
        "pins": pinout,
        "pinCheck": checks,
        "inside": {"parts": sum(cells.values()), "libraries": dict(cells.most_common()),
                   "nets": len(nets), "named": len(named), "sheets": sheets},
        "notes": notes,
        "readFrom": read_from,
        "pdf": f"/chips/{slug}.pdf",
        "license": cfg["license"],
        "origin": {
            "project": "jtcores", "url": upstream, "commit": cfg["commit"], "path": entry["dir"],
            "authors": who, "license": cfg["license"],
            "licenseUrl": f"{REPO}/blob/main/kicad/chips/{slug}/LICENSE",
            "source": f"{REPO}/tree/main/kicad/chips/{slug}",
            "imported": datetime.date.today().isoformat(),
        },
    }
    jt.dump(os.path.join(ROOT, "data", "customchips", slug + ".json"), rec)
    write_notice(dest, entry, cfg, slug, files, who, upstream, read_from)
    agree = sum(c["same"] for c in checks)
    print(f"{slug}: {len(pins)} pins, {sum(cells.values())} parts inside ({', '.join(cells)}), "
          f"{len(nets)} nets, {len(sheets)} sheet(s), {os.path.getsize(pdf) / 1e6:.1f} MB PDF; "
          + (f"pinout against {len(checks)} board symbol(s): {agree} pin names agree, "
             f"{sum(len(c['overbar']) for c in checks)} differ by an overbar, "
             f"{sum(c['unnamed'] for c in checks)} unnamed, "
             f"{sum(len(c['differ']) for c in checks)} differ"
             if checks else "no board drawing here carries it"))


def write_notice(dest, entry, cfg, slug, files, who, upstream, read_from):
    today = datetime.date.today().isoformat()
    with open(os.path.join(dest, "NOTICE.md"), "w") as f:
        f.write(f"""# {entry['name']}

A KiCad schematic of the inside of the {entry['name']}, drawn for
[jtcores]({cfg['repo']}) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    {upstream}

**Drawn by** {', '.join(who)} (the people who committed these sheets to
jtcores){f', from {read_from}, as the drawing says' if read_from else ''}. The
schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`{cfg['commit']}`: the sheets the root reaches, and the project settings.

{chr(10).join('- `' + p + '`' for p in files)}

## What was added here

Nothing in this directory but this notice and the licence. On {today}, by
`tools/import_custom_chips.py` in this repository, and under the same licence:

- `data/customchips/{slug}.json` -- the chip's pinout, read off the symbol in
  these sheets; how many cells the drawing uses and from which libraries; the
  drawing's own notes on what the chip does and what silicon it was read from;
  and how the pinout compares with the board drawings on this site that carry
  the part.
- `web/chips/{slug}.pdf` -- every sheet, as KiCad plots it.
- `web/data/customchip/{slug}.json` -- all of that, with the boards, machines
  and MAME PCB layouts on this site that carry the chip, as the page reads it.
""")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--jt", required=True, help="a jtcores checkout, with history")
    ap.add_argument("--verify", action="store_true",
                    help="check the copies under kicad/chips/ against upstream; change nothing")
    ap.add_argument("slugs", nargs="*", help="chips to import (default: all)")
    a = ap.parse_args()
    cfg = load_manifest()
    head = subprocess.run(["git", "-C", a.jt, "rev-parse", "HEAD"], capture_output=True,
                          text=True, check=True).stdout.strip()
    if head != cfg["commit"]:
        sys.exit(f"{a.jt} is at {head}, but data/jtcores.json is pinned to {cfg['commit']}")
    bad = 0
    measure = collections.defaultdict(collections.Counter)
    for entry in cfg["chips"]:
        if a.slugs and entry["slug"] not in a.slugs:
            continue
        if a.verify:
            bad += jt.verify_copy(os.path.join(a.jt, entry["dir"]),
                                  os.path.join(ROOT, "kicad", "chips", entry["slug"]), entry["slug"])
        else:
            import_chip(entry, cfg, a.jt, measure)
    if a.verify:
        print(f"{bad} file(s) differ from upstream" if bad else "every copied file matches upstream")
        sys.exit(1 if bad else 0)
    if measure:
        print("\nPin directions against what drives each pad inside the drawing:")
        for k, what in (("turned", "the chip symbols, turned round"), ("board", "the board drawings")):
            yes, no = measure[k][True], measure[k][False]
            print(f"  {what}: {yes} of {yes + no} input/output pins agree")
        if measure["against"]:
            print("  disagreeing: " + ", ".join(measure["against"]))


if __name__ == "__main__":
    main()
