#!/usr/bin/env python3
"""Where each custom chip is used, and the copy of them the site reads.

tools/import_custom_chips.py brings a chip's own drawing in and writes what it
says to data/customchips/<slug>.json. What carries the chip is a different
question, and its answer changes whenever a board or a MAME layout is
published, so it is worked out here, every time web/data/ is built:

  boards     every board on the site whose chip lookup names the part, with
             the designators -- the Twin 16 boards' 007781 at B_C11 and B_P4
  layouts    every PCB layout read from MAME's driver notes that names it --
             which is how the Capcom chips reach Pang and Last Duel, since no
             board here carries them
  machines   the machines those boards belong to, and the ones a layout is
             tied to by set or title. A layout tied to no set ("driver-wide")
             is listed on the chip's page but names no machine: it describes
             a driver's hardware, which may not be every set's board.

A chip is found by its markings (data/jtcores.json), matched as a whole word
in a part value, a layout label or the layout's legend.

  python3 tools/build_assets.py --chips-only     # web/data/customchip{s.json,/}
"""
import glob, json, os, re, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "data")


def load_manifest():
    return json.load(open(os.path.join(ROOT, "data", "jtcores.json")))


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def marking_re(markings):
    """A chip's markings as one pattern: whole words, hyphens optional.

    "052535" finds `052535(X3)` on a sketch and not `0525351`; "DL-010D-103"
    finds `DL010D103` as well.
    """
    alts = "|".join(re.escape(m).replace(r"\-", "-?")
                    for m in sorted(markings, key=len, reverse=True))
    return re.compile(rf"(?<![A-Za-z0-9])(?:{alts})(?![A-Za-z0-9])", re.I)


def _boards():
    """(board record, {ref: {part, section}}) for every published board."""
    for b in json.load(open(os.path.join(ROOT, "data", "boards.json"))):
        p = os.path.join(ROOT, "data", "chips", b["slug"] + ".json")
        if os.path.exists(p):
            lookup = json.load(open(p))
        else:
            spec_p = os.path.join(ROOT, "boards", b["slug"] + ".json")
            ics = json.load(open(spec_p)).get("ics", {}) if os.path.exists(spec_p) else {}
            lookup = {r: {"part": v} for r, v in ics.items()}
        yield b, lookup


def _layouts():
    """(index row, layout) for every PCB layout read from MAME's notes."""
    ip = os.path.join(ROOT, "data", "mame", "layouts.json")
    if not os.path.exists(ip):
        return
    rows = {r["id"]: r for r in json.load(open(ip))["layouts"]}
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "mame", "layouts", "*.json"))):
        for lays in json.load(open(p)).values():
            for l in lays:
                if l["id"] in rows:
                    yield rows[l["id"]], l


def where_used(entry, boards, layouts, names):
    pat = marking_re(entry["markings"])
    on_boards, machines = [], []
    for b, lookup in boards:
        refs = [{"ref": r, "section": v.get("section", "")}
                for r, v in lookup.items() if pat.search(str(v.get("part") or ""))]
        if not refs:
            continue
        refs.sort(key=lambda x: natural(x["ref"]))
        owners = [m for m in [b.get("machine")] + list(b.get("machines", [])) if m]
        on_boards.append({"slug": b["slug"], "name": b["name"], "mfr": b.get("mfr", ""),
                          "year": b.get("year", ""), "license": b.get("license", ""),
                          "refs": refs, "machines": owners})
        machines += owners
    on_layouts = []
    for row, l in layouts:
        labels = [d["label"] for d in l["devices"]
                  if pat.search(d.get("label") or "") or pat.search(d.get("part") or "")]
        if not labels:
            continue
        on_layouts.append({"id": row["id"], "name": row.get("name"), "caption": row.get("caption"),
                           "mfr": row.get("mfr"), "year": row.get("year"), "src": row["src"],
                           "scope": row["scope"], "slugs": row.get("slugs", []), "labels": labels})
        if row["scope"] in ("set", "title"):
            machines += row.get("slugs", [])
    machines = [[m, names[m]] for m in dict.fromkeys(machines) if m in names]
    return on_boards, on_layouts, machines


def publish(out=OUT):
    """Write web/data/customchips.json and web/data/customchip/<slug>.json.

    Returns (files, bytes). A chip with no import (no data/customchips/ record
    or no PDF) is skipped and reported, never published half-made.
    """
    cfg = load_manifest()
    names = {m["s"]: m["n"] for m in json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))}
    boards = list(_boards())
    layouts = list(_layouts())
    dst = os.path.join(out, "customchip")
    if os.path.isdir(dst):
        shutil.rmtree(dst)          # a chip dropped from the manifest must not linger
    os.makedirs(dst)
    index, files, total = [], 0, 0
    for entry in cfg.get("chips", []):
        slug = entry["slug"]
        rp = os.path.join(ROOT, "data", "customchips", slug + ".json")
        if not os.path.exists(rp) or not os.path.exists(os.path.join(ROOT, "web", "chips", slug + ".pdf")):
            print(f"  {slug}: not imported -- run tools/import_custom_chips.py")
            continue
        rec = json.load(open(rp))
        on_boards, on_layouts, machines = where_used(entry, boards, layouts, names)
        full = {"slug": slug, "name": entry["name"], "maker": entry["maker"],
                "markings": entry["markings"], "summary": entry.get("summary", ""),
                "conflicts": entry.get("conflicts", []), **{k: v for k, v in rec.items() if k != "slug"},
                "boards": on_boards, "layouts": on_layouts, "machines": machines}
        path = os.path.join(dst, slug + ".json")
        with open(path, "w") as f:
            json.dump(full, f, ensure_ascii=False, separators=(",", ":"))
        files += 1; total += os.path.getsize(path)
        index.append({"slug": slug, "name": entry["name"], "maker": entry["maker"],
                      "markings": entry["markings"], "role": rec["role"],
                      "pins": rec["package"]["pins"], "parts": rec["inside"]["parts"],
                      "readFrom": rec.get("readFrom"), "license": rec["license"],
                      "authors": rec["origin"]["authors"],
                      "boards": [{"slug": b["slug"], "refs": [r["ref"] for r in b["refs"]]}
                                 for b in on_boards],
                      "layouts": [{"id": l["id"], "labels": l["labels"]} for l in on_layouts],
                      "machines": [m for m, _ in machines]})
    path = os.path.join(out, "customchips.json")
    with open(path, "w") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    files += 1; total += os.path.getsize(path)
    for c in index:
        print(f"  {c['slug']}: {len(c['boards'])} board(s), {len(c['layouts'])} layout(s), "
              f"{len(c['machines'])} machine(s)")
    return files, total


if __name__ == "__main__":
    n, size = publish()
    print(f"{n} custom chip file(s), {size / 1e3:.0f} KB -> web/data/")
