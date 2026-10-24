#!/usr/bin/env python3
"""Take the Arcade Archive documents the survey matched to machines.

    python3 tools/take_arcarc.py [--dry-run]

Reads data/sources/arcarc.json and writes an entry into data/extra-docs.json
for every PDF that is not already in the corpus and whose filename names a
machine we carry. Only the arcade directories are considered — the jukebox,
monitor and coin-mechanism references have no machine to be filed under
until the corpus has a home for them. No file is read here; the ingest
fetches it, and the Arcade Archive has no OCR of its own, so these go
through tesseract.
"""
import argparse, collections, json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import guess_machine, machine_index, type_of, add_documents  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, "data", "sources", "arcarc.json")
DIRS = ("PDF_Arcade_", "PDF_Dip_Switches_and_Pinouts", "PDF_LaserDisc_Games", "PDF_Misc")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    survey = json.load(open(SURVEY))
    base = survey["source"]["url"]
    machines = json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))
    idx = machine_index(machines)
    entries, why, skipped = [], collections.Counter(), collections.Counter()
    for p in survey["pdfs"]:
        if p["ours"]:
            skipped["already ours"] += 1; continue
        if not p["path"].startswith(DIRS):
            skipped["not an arcade directory"] += 1; continue
        name = p["path"].split("/")[-1]
        m = guess_machine(name, idx)
        if not m:
            skipped["no machine"] += 1; continue
        why[m["why"]] += 1
        e = {
            "f": name, "t": type_of(name),
            "l": base + p["path"],
            "machines": [m["slug"]],
            "source": "arcarc",
            "page": base + urllib.parse.quote(p["path"].rsplit("/", 1)[0] + "/"),
        }
        if not m["whole"]:
            e["note"] = (f"Filed under this machine because the filename begins with its name "
                         f"(“{m['matched'].replace('_', ' ')}”); the file is “{name}”.")
        entries.append(e)
    added, dup = add_documents(entries, dry_run=a.dry_run)
    print(f"{len(entries)} PDFs ({', '.join(f'{n} {k}' for k, n in why.most_common())}); "
          f"skipped {', '.join(f'{n} {k}' for k, n in skipped.most_common())}")
    print(f"{'would add' if a.dry_run else 'added'} {added}, {dup} already in the corpus")


if __name__ == "__main__":
    main()
