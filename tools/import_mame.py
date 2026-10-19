#!/usr/bin/env python3
"""Take what MAME knows about each machine on the site, from MAME's own XML.

The machine list and its CPU, sound, display, input and DIP data came from
arcadertfm's machines.json, which is MAME-derived but carries no ROM files.
Most machines on the site (6,427 of 7,823 when this was written) have no
document at all, so for them MAME is the whole story: which ROMs make up the
set, what each is called and how big it is, which driver source file describes
the hardware, and which set it is a clone of. That is enough for a page that
says something true about the board while the documents are found.

The input is the "full driver information in XML format" file MAME publishes
with every release (mameNNNNlx.zip on github.com/mamedev/mame/releases), or the
output of `mame -listxml`. It is 300+ MB, so it is streamed and never
committed; what is committed is the extract this writes:

  data/mame/machines.json   {"version": "0.289", "machines": {romset: {...}}}

Per machine:
  src     driver source file, relative to src/mame/ (where the PCB notes live)
  parent  the set this is a clone of, if any
  roms    [{n, s, c, r, st?, b?, m?}]  name, size, CRC32, region, status when
          not good, BIOS set when bios-specific, merge name when the file
          is shared with the parent or BIOS
  disks   [{n, r, st?}]   CHDs, by name
  chips   [{t, n, hz?}]   only where the upstream data has no CPU at all

  python3 -I tools/import_mame.py /path/to/mame0289.xml
"""
import json, os, sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "mame", "machines.json")


def site_romsets():
    """Romset name -> slug, for every machine the site already lists."""
    sets = {}
    d = os.path.join(ROOT, "web", "data", "machine")
    for f in os.listdir(d):
        rec = json.load(open(os.path.join(d, f)))
        if rec.get("rom"):
            sets[rec["rom"]] = rec["slug"]
    return sets


def main():
    xml = sys.argv[1]
    wanted = site_romsets()
    no_cpu = set()
    d = os.path.join(ROOT, "web", "data", "machine")
    for rom, slug in wanted.items():
        rec = json.load(open(os.path.join(d, slug + ".json")))
        if not rec.get("cpu"):
            no_cpu.add(rom)

    version, out = None, {}
    for event, el in ET.iterparse(xml, events=("start", "end")):
        if event == "start":
            if el.tag == "mame" and version is None:
                version = (el.get("build") or "").split(" ")[0]
            continue
        if el.tag != "machine":
            continue
        name = el.get("name")
        if name in wanted:
            rec = {}
            if el.get("sourcefile"):
                rec["src"] = el.get("sourcefile")
            if el.get("cloneof"):
                rec["parent"] = el.get("cloneof")
            roms = []
            for r in el.findall("rom"):
                row = {"n": r.get("name"), "s": int(r.get("size") or 0)}
                if r.get("crc"):
                    row["c"] = r.get("crc")
                if r.get("region"):
                    row["r"] = r.get("region")
                if r.get("status") and r.get("status") != "good":
                    row["st"] = r.get("status")
                if r.get("bios"):
                    row["b"] = r.get("bios")
                if r.get("merge"):
                    row["m"] = r.get("merge")
                roms.append(row)
            if roms:
                rec["roms"] = roms
            disks = []
            for dk in el.findall("disk"):
                row = {"n": dk.get("name")}
                if dk.get("region"):
                    row["r"] = dk.get("region")
                if dk.get("status") and dk.get("status") != "good":
                    row["st"] = dk.get("status")
                disks.append(row)
            if disks:
                rec["disks"] = disks
            if name in no_cpu:
                chips = []
                for c in el.findall("chip"):
                    row = {"t": c.get("type"), "n": c.get("name")}
                    if c.get("clock"):
                        row["hz"] = int(c.get("clock"))
                    chips.append(row)
                if chips:
                    rec["chips"] = chips
            out[name] = rec
        el.clear()

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"version": version, "machines": dict(sorted(out.items()))},
              open(OUT, "w"), separators=(",", ":"))
    missing = sorted(set(wanted) - set(out))
    with_roms = sum(1 for r in out.values() if r.get("roms"))
    print(f"MAME {version}: {len(out)} of {len(wanted)} site romsets found, "
          f"{with_roms} with ROM files, {sum(len(r.get('roms', [])) for r in out.values())} ROM files")
    print(f"  not in this MAME: {len(missing)}" + (f" -- {', '.join(missing[:20])}"
          + (" ..." if len(missing) > 20 else "") if missing else ""))
    print(f"  wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) / 1048576:.1f} MB)")


if __name__ == "__main__":
    main()
