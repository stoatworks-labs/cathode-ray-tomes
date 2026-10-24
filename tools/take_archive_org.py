#!/usr/bin/env python3
"""Take the archive.org documents the survey matched to machines.

    python3 tools/take_archive_org.py [--dry-run] [--whole-only]

Reads data/sources/archive_org.json (the survey) and the per-item metadata it
cached, and writes one entry per PDF into data/extra-docs.json for every item
that names a machine we carry. Each entry points at the archive's own copy of
the file and at the DjVu XML the archive OCR'd from it, so ingest.py reads
the archive's reading rather than running tesseract over seventy thousand
pages again. Nothing is downloaded here; the ingest does that.

Skipped, and said so: items with no PDF; pinball; titles that name no machine,
or name one too loosely (see tools/sources.py for the rule). A document whose
filename is already in the corpus is the same document and is not taken
twice.
"""
import argparse, collections, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sources import guess_machine, machine_index, type_of, add_documents  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, "data", "sources", "archive_org.json")
META = os.path.join(ROOT, "cache", "archive_org", "meta")
PINBALL = re.compile(r"pinball|flipper|gottlieb|\bbally\b.*\b(19[67]\d)\b", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--whole-only", action="store_true", help="only titles matched whole")
    a = ap.parse_args()

    survey = json.load(open(SURVEY))
    machines = json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))
    idx = machine_index(machines)
    entries, why, skipped = [], collections.Counter(), collections.Counter()
    for it in survey["new"]:
        title = it.get("title") or it["identifier"]
        if PINBALL.search(title):
            skipped["pinball"] += 1; continue
        pdfs = it.get("pdfs") or []
        if not pdfs:
            skipped["no pdf"] += 1; continue
        m = guess_machine(title, idx)
        if not m or (a.whole_only and not m["whole"]):
            skipped["no machine"] += 1; continue
        why[m["why"]] += 1
        ident = it["identifier"]
        meta = json.load(open(os.path.join(META, ident + ".json"))) if os.path.exists(
            os.path.join(META, ident + ".json")) else {}
        names = {f["name"] for f in meta.get("files") or []}
        for p in pdfs:
            stem = re.sub(r"\.pdf$", "", p["name"], flags=re.I)
            e = {
                "f": p["name"], "t": type_of(title if len(pdfs) == 1 else stem),
                "l": f"https://archive.org/download/{ident}/{p['name']}",
                "machines": [m["slug"]],
                "source": "archive_org",
                "page": f"https://archive.org/details/{ident}",
            }
            if stem + "_djvu.xml" in names:
                e["ocr"] = f"https://archive.org/download/{ident}/{stem}_djvu.xml"
            if not m["whole"]:
                e["note"] = (f"Filed under this machine because the title begins with its name "
                             f"(“{m['matched'].replace('_', ' ')}”); the rest of the title is "
                             f"“{title}”.")
            entries.append(e)

    added, dup = add_documents(entries, dry_run=a.dry_run)
    print(f"{len(entries)} PDFs from {sum(why.values())} items "
          f"({', '.join(f'{n} {k}' for k, n in why.most_common())}); "
          f"skipped {', '.join(f'{n} {k}' for k, n in skipped.most_common())}")
    print(f"{'would add' if a.dry_run else 'added'} {added}, {dup} already in the corpus")
    print(f"{sum(1 for e in entries if e.get('ocr'))} carry the archive's OCR")


if __name__ == "__main__":
    main()
