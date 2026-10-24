#!/usr/bin/env python3
"""Take Sega Retro's service documentation.

    python3 tools/take_segaretro.py [--dry-run]

Sega Retro has reserved rights in its robots.txt (`ai-train=no,
use=reference`), which the survey respected by recording pointers only. The
decision to carry its service documents was taken deliberately, on the
material nobody else holds: Sega's own system service manuals — NAOMI,
NAOMI 2 and GD-ROM, Atomiswave, Lindbergh — and the console service manuals by
board revision. Every document credits Sega Retro on its page, links to the
wiki's file page, and the reader offers the wiki's copy as the original.

Only the files the survey classed `service` are taken, filed by an explicit
map from filename to machine or system: these are system-level documents, and
a name like "NAOMI_Service_Manual_EN" is not something the general matcher
should be guessing at. Anything not in the map is listed, not taken. The
consoles this brings in (Master System, Game Gear, Mega Drive, Mega CD, 32X)
are added to data/systems.json alongside the others.
"""
import argparse, json, os, sys, collections, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import type_of, add_documents  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, "data", "sources", "segaretro.json")

# filename fragment -> machine or system slugs it documents
HOMES = [
    ("NAOMI_2_", ["naomi2"]),
    ("NAOMI_GD-ROM", ["naomigd"]),
    ("NAOMI_Service", ["naomi"]),
    ("Atomiswave_Service", ["awbios"]),
    ("Hummer_Lindbergh", ["lindbios"]),
    ("OutRun2SPSDX_Lindbergh", ["lindbios"]),
    ("DerbyOwnersClubWorldEdition_NAOMI", ["derbyoc"]),
    ("005_G80", ["005"]),
    ("HangOn_Schematics", ["hangon"]),
    ("OutRun_Schematics", ["outrun"]),
    ("OutRun_Arcade_US_Manual", ["outrun"]),
    ("SpaceHarrier_Schematics", ["sharrier"]),
    ("Turbo_Schematics", ["turbo"]),
    ("Zaxxon_Arcade_US_ServiceNote", ["zaxxon"]),
    ("Dark_Edge_Service", ["darkedge"]),
    ("Fonz_service", ["fonz"]),
    ("MoonCresta_Arcade_US_Manual", ["mooncrst"]),
    ("TicTacQuiz", ["tictac"]),
    ("Sega_Master_System_II_Service", ["sega-master-system"]),
    ("Sega_Master_System_Service", ["sega-master-system"]),
    ("SMS2ServiceManualEU", ["sega-master-system"]),
    ("SMSServiceManualEU", ["sega-master-system"]),
    ("Game_Gear_VA1", ["sega-game-gear"]),
    ("TV_Tuner_Pack_PAL_for_Game_Gear", ["sega-game-gear"]),
    ("Genesis_-_Mega_Drive_PAL_-_Mega_CD", ["sega-mega-drive", "sega-mega-cd"]),
    ("Genesis_II", ["sega-mega-drive"]),
    ("Sega_CD_II_-_Mega_CD_II", ["sega-mega-cd"]),
    ("Sega_32X_Service", ["sega-32x"]),
    ("Sega_Saturn_(PAL)", ["sega-saturn"]),
    ("SC-3000ServiceManual", ["sc3000"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    survey = json.load(open(SURVEY))
    known = {m["s"] for m in json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))}
    systems = {s["slug"] for s in json.load(open(os.path.join(ROOT, "data", "systems.json")))["systems"]}
    entries, left = [], []
    for p in survey["pdfs"]:
        if p["kind"] != "service":
            continue
        homes = next((h for frag, h in HOMES if frag in p["name"]), None)
        if not homes:
            left.append(p["name"]); continue
        for h in homes:
            if h not in known and h not in systems:
                raise SystemExit(f"{p['name']}: {h} is neither a machine nor a system")
        entries.append({
            "f": p["name"], "t": type_of(p["name"]),
            "l": urllib.parse.unquote(p["url"]), "machines": homes,
            "source": "segaretro",
            "page": "https://segaretro.org/File:" + p["name"],
        })
    added, dup = add_documents(entries, dry_run=a.dry_run)
    print(f"{len(entries)} documents on {len({h for e in entries for h in e['machines']})} machines/systems; "
          f"{'would add' if a.dry_run else 'added'} {added}, {dup} already in the corpus")
    print(f"not taken ({len(left)}): " + "; ".join(left))


if __name__ == "__main__":
    main()
