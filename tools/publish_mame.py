#!/usr/bin/env python3
"""Get the boards converted from MAME's netlists ready for the site.

tools/mame_netlist.py writes boards/<slug>.nets and a bare boards/<slug>.json,
and tools/build_board_nets.py checks the .nets and writes the netlist. This adds
what a published board needs on top, so that tools/build_board.py and
tools/publish_board.py can take it from there like any other board:

  * footprints and a nominal layout for the board view -- a DIP sized from the
    part's pinout, laid out by tools/import_jtcores.layout(): on the board's own
    grid where it has one (Tank), in designator order where it numbers its ICs
  * `license` and `origin`: MAME's file at the commit converted, its copyright
    holders, its licence, and the converted .nets as the source -- CC0-1.0 or
    BSD-3-Clause, never the GPL, so the page states those terms instead
  * `parts` for the bill of materials (the netlist names every passive)
  * boards/<slug>.read.json: the target's notes, with its open questions --
    "Open question(s) ... :" and the bullets under it -- as the page's
    conflicts, so a reader sees them above the board
  * data/chips/<slug>.json and data/signals/<slug>.json, the board page's lookups

  python3 tools/publish_mame.py              every board converted from MAME
  python3 tools/publish_mame.py tank-board-1

then, per board: tools/build_board.py <slug> (KiCad's Python), tools/publish_board.py
<slug>, and once: tools/build_assets.py --boards-only.
"""
import collections, datetime, glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_board_nets as checker                     # noqa: E402
import mame_netlist as M                               # noqa: E402
from import_jtcores import footprint_for, layout       # noqa: E402
from mame_targets import TARGETS, UNCHECKED            # noqa: E402

REPO = "https://github.com/stoatworks-labs/cathode-ray-tomes"
MAME = "https://github.com/mamedev/mame"


def dump(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


def converted():
    """Every board a MAME target writes, with its target."""
    out = {}
    for target, cfg in TARGETS.items():
        for slug in (cfg["split"] if "split" in cfg else [target]):
            out[slug] = target
    return out


def pins_of(part):
    """The highest pin number on the part's pinout -- its package size."""
    return max(int(n) for n in checker.pinout(part) if n.isdigit())


# ---------------------------------------------------------------------------
# Notes and open questions
# ---------------------------------------------------------------------------

def paragraphs(text):
    return [p for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def read_notes(notes):
    """(notes, conflicts) from a target's notes. An "Open question(s) ...:" or
    "Open, ...:" paragraph is the questions -- its bullets, or what follows the
    colon -- and a bullet that starts "Open question." is one; the rest are notes."""
    out, questions = [], []
    for note in notes:
        for para in paragraphs(note):
            head = para.split("\n", 1)[0]
            if re.match(r"open(?: questions?\b|,)", head, re.I) and ":" in para:
                bullets = re.split(r"\n\s*\*\s+", "\n" + para.split(":", 1)[1])
                inline = bullets[0].strip()
                if inline:
                    questions.append(flat(inline))
                questions += [flat(b) for b in bullets[1:] if b.strip()]
                continue
            bullets = re.split(r"\n\s*\*\s+", "\n" + para)
            lead, items = bullets[0].strip(), bullets[1:]
            kept = []
            for b in items:
                m = re.match(r"open question[.:]\s*", b, re.I)
                if m:
                    questions.append(flat(b[m.end():]))
                else:
                    kept.append(b)
            text = flat(lead)
            if kept:
                text = (text + " " if text else "") + " ".join("* " + flat(b) for b in kept)
            if text:
                out.append(text)
    return out, questions


# ---------------------------------------------------------------------------
# One board
# ---------------------------------------------------------------------------

def prepare(slug, target, results):
    spec = json.load(open(os.path.join(ROOT, "boards", slug + ".json")))
    netlist = json.load(open(os.path.join(ROOT, "boards", slug + ".netlist.json")))
    cfg = TARGETS[target]
    meta = cfg["split"][slug] if "split" in cfg else {}
    sub_cfg = dict(cfg, **meta)
    res = results[slug]
    src = spec["source"]

    # Footprints and layout.
    fpids = {cell: footprint_for(pins_of(part)) for cell, part in spec["ics"].items()}
    place, grid, size, clashes = layout(spec["ics"], fpids, None)
    spec["footprints"] = dict(sorted(fpids.items(), key=lambda kv: M.nat(kv[0])))
    spec["place"] = dict(sorted(place.items(), key=lambda kv: M.nat(kv[0])))
    spec["size"] = size
    if grid:
        spec["grid"] = grid
    else:
        spec.pop("grid", None)
    spec["refPrefix"] = "U"

    # Licence, origin, machines.
    holders = [h.strip() for h in re.split(r",", src["copyright"]) if h.strip()]
    spec["license"] = src["licence"]
    spec["origin"] = {
        "project": "MAME",
        "url": f"{MAME}/blob/{src['commit']}/{src['mame']}",
        "commit": src["commit"], "tag": src["tag"], "path": src["mame"],
        "netlist": src["netlist"], "authors": holders,
        "license": src["licence"], "copyright": ", ".join(holders),
        "licenseUrl": f"/licenses/{src['licence']}.txt",
        "credit": "netlist written by",
        "source": f"{REPO}/blob/main/boards/{slug}.nets",
        "sourceLabel": "The conversion, every change from MAME's file logged",
        "what": ("The netlist is MAME's -- written to simulate this board, from its "
                 "schematics -- converted here into the board's own nets, with MAME's "
                 "simulation stand-ins undone and, where this site holds the schematic, "
                 "checked and corrected against it. The board view, chip lookup and bill "
                 "of materials are made from it."),
        "imported": datetime.date.today().isoformat(),
    }
    if sub_cfg.get("machines"):
        spec["machines"] = sub_cfg["machines"]
    spec["partial"] = True
    spec["netsTraced"] = True
    # The site's "single source" warning is about a parts list OCR'd once; a
    # MAME conversion is a different thing, and its notes say whether it was
    # compared with the sheet.
    spec["singleSource"] = False

    # Parts for the bill of materials: every part the netlist names. Not P by
    # designator: Coco Loco's P1 is its volume pot, and a connector has no value.
    parts = {}
    for ref, c in netlist["components"].items():
        label = c.get("part") or c.get("value") or ""
        if label and not re.fullmatch(r"(J|TP)\d+", ref):
            parts[ref] = label
    spec["parts"] = dict(sorted(parts.items(), key=lambda kv: M.nat(kv[0])))

    # A target says it was not compared by carrying the UNCHECKED note. Not a
    # search for "compared with": "Not compared with the sheet" matches that too.
    checked = UNCHECKED not in sub_cfg.get("notes", [])

    # Status: counts, then what the target says, then what the view is.
    n_pins = sum(len(n["pins"]) for n in netlist["nets"].values())
    n_ic = len(spec["ics"])
    cover = (f"{n_ic} ICs, {len(parts) - n_ic} other parts and {len(netlist['nets'])} nets "
             f"over {n_pins} pins. ")
    cover += sub_cfg["board"].get("coverage", "").replace(
        " See the .nets file for what was undone and what MAME leaves out.", "")
    if not checked:
        cover += (" Not compared with a sheet: it is MAME's reading as MAME has it, and the "
                  "notes say why.")
    if not n_ic:
        cover += (" It has no ICs, so there is no board view: the netlist and the bill of "
                  "materials carry it.")
    elif grid:
        cover += (" The board view carries the ICs and the nets between them, with the board's "
                  "grid positions on a nominal spacing.")
    else:
        cover += (" The board view carries the ICs and the nets between them; the board numbers "
                  "its ICs rather than naming positions, so they are laid out in designator "
                  "order, not where they sit.")
    spec["coverage"] = re.sub(r"\s+", " ", cover).strip()

    dump(os.path.join(ROOT, "boards", slug + ".json"), spec)

    # Notes and open questions.
    notes, questions = read_notes(sub_cfg.get("notes", []))
    lead = (f"Converted from MAME's {src['mame']} (NETLIST_START({src['netlist']}), "
            f"{src['licence']}, {', '.join(holders)}) at {src['tag']} by "
            f"tools/mame_netlist.py. Every change from MAME's file -- the simulation "
            f"stand-ins undone, the hacks dropped, the corrections from the sheet -- is "
            f"logged at the top of boards/{slug}.nets.")
    dump(os.path.join(ROOT, "boards", slug + ".read.json"),
         {"notes": [lead] + notes, "conflicts": questions})

    # Chip lookup: keyed as the sheet prints the designator.
    des = {name: M.designator(sub_cfg, d) for name, d in res["devices"].items() if d.kind == "IC"}
    # A chip's section is the part of MAME's file that wires most of its pins:
    # the first net to touch it is often a shared clock or bus, which says
    # nothing about where it belongs.
    section = {d: v.most_common(1)[0][0] for d, v in res["mentions"].items() if v}
    fixed = {f[1][0]: f[0].split(" -- ", 1)[-1] for f in res.get("fixes", [])}
    chips, key_of = {}, {}
    for name, d in sorted(res["devices"].items(), key=lambda kv: M.nat(des.get(kv[0], ""))):
        if name not in des:
            continue
        ref = des[name]
        key = ref[1:] if grid else ref
        key_of[ref] = key
        note = []
        if re.fullmatch(r"IC\d+[A-Z]?", name):
            note.append(f"the sheet prints {name}; {ref} in the board view and the netlist")
        elif name != "IC_" + key and not name.endswith(key):
            note.append(f"MAME calls it {name}")
        if name in fixed:
            note.append(fixed[name])
        if d.part in ("9316", "9322", "9321"):
            note.append({"9316": "same pinout as the 74161", "9322": "same pinout as the 74157",
                         "9321": "same pinout as the 74139"}[d.part])
        chips[key] = {"part": d.part, "section": section.get(name, ""),
                      "note": "; ".join(note), "otherRev": None,
                      "source": "MAME netlist, checked against the sheet" if checked
                      else "MAME netlist"}
    dump(os.path.join(ROOT, "data", "chips", slug + ".json"), chips)

    signals = {}
    for name, n in netlist["nets"].items():
        if n["named"] == "auto" or checker.is_rail(name):
            continue
        where = collections.Counter(key_of.get(p.rpartition(".")[0], p.rpartition(".")[0])
                                    for p in n["pins"])
        signals[name] = dict(sorted(where.items(), key=lambda kv: M.nat(kv[0])))
    dump(os.path.join(ROOT, "data", "signals", slug + ".json"), signals)

    print(f"{slug}: {n_ic} ICs ({'grid ' + grid['rows'] if grid else 'designator order'}, "
          f"{clashes} overlaps), {len(parts)} parts, {len(questions)} open question(s), "
          f"{len(notes)} note(s), licence {src['licence']}")


def main():
    want = sys.argv[1:]
    boards = converted()
    unknown = [s for s in want if s not in boards]
    if unknown:
        raise SystemExit(f"not converted from MAME: {', '.join(unknown)}")
    want = want or sorted(boards)
    results = {}
    for target in sorted({boards[s] for s in want}):
        cfg = TARGETS[target]
        res = M.convert(target, cfg)
        for slug, sub in (M.split(res, cfg) if "split" in cfg else [(target, res)]):
            results[slug] = sub
    for slug in want:
        prepare(slug, boards[slug], results)


if __name__ == "__main__":
    main()
