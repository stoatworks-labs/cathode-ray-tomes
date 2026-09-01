#!/usr/bin/env python3
"""Assemble web/data/ — the corpus, served as static assets.

Everything the site reads ships with the deploy rather than living in KV:
no write quotas, and code and corpus can never drift apart because they are
versioned and published together.

  web/data/machines.json        browse index (all machines)
  web/data/docs.json            document catalogue
  web/data/chips.json           chip -> machines
  web/data/boards.json          KiCad conversions
  web/data/machine/<slug>.json  per-machine detail
  web/data/doc/<id>.json        rendered document (blocks + outline)
  web/data/postings/<n>.json    search postings, sharded by leading character
  web/data/parts/<id>.json      parts list recovered from a manual
  web/data/chips/<board>.json   designator -> part, function and revision
  web/data/rommaps.json         index of ROM maps recovered from MAME
  web/data/rommap/<machine>.json  ROM positions for one machine
"""
import json, os, shutil, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "data")

def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return os.path.getsize(dst)

def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    total = files = 0
    for name, src in [
        ("machines.json", "data/index/machines.json"),
        ("docs.json",     "data/index/docs.json"),
        ("chips.json",    "data/index/chips.json"),
        ("boards.json",   "data/boards.json"),
        ("rommaps.json",  "data/rommaps.json"),
    ]:
        p = os.path.join(ROOT, src)
        if os.path.exists(p):
            total += copy(p, os.path.join(OUT, name)); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "machine", "*.json")):
        total += copy(p, os.path.join(OUT, "machine", os.path.basename(p))); files += 1

    # Drawing pages are decided by tools/build_drawings.py and merged in here
    # rather than written back into cache/text/, which is the ingest's own
    # checkpoint and has to stay the OCR as it came out. A page flagged `draw`
    # is shown as its scan; one flagged `noise` keeps its text and is marked as
    # having come off a drawing. See build_drawings.py for why those are
    # different answers.
    dpath = os.path.join(ROOT, "data", "drawings.json")
    drawings = json.load(open(dpath)) if os.path.exists(dpath) else {}
    n_draw = n_noise = 0
    for p in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        fid = os.path.basename(p)[:-5]
        flags = drawings.get(fid)
        dst = os.path.join(OUT, "doc", os.path.basename(p))
        if not flags:
            total += copy(p, dst); files += 1
            continue
        doc = json.load(open(p))
        draw, noise = set(flags.get("draw", [])), set(flags.get("noise", []))
        sizes = flags.get("size", {})
        for page in doc.get("pages", []):
            if page["n"] in draw:
                page["draw"] = True; n_draw += 1
                sz = sizes.get(str(page["n"]))
                if sz:
                    page["dw"], page["dh"] = sz
            elif page["n"] in noise:
                page["noise"] = True; n_noise += 1
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        total += os.path.getsize(dst); files += 1
    if drawings:
        print(f"  {n_draw} pages marked as drawings, {n_noise} as drawing noise")

    # The scans for the drawing pages, so a schematic the manual refers to is
    # actually on the page instead of being a link to a 45-page PDF.
    for p in glob.glob(os.path.join(ROOT, "web", "pages", "*", "*.webp")):
        files += 1; total += os.path.getsize(p)

    for p in glob.glob(os.path.join(ROOT, "data", "index", "postings", "*.json")):
        total += copy(p, os.path.join(OUT, "postings", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "parts", "*.json")):
        total += copy(p, os.path.join(OUT, "parts", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "chips", "*.json")):
        total += copy(p, os.path.join(OUT, "chips", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "signals", "*.json")):
        total += copy(p, os.path.join(OUT, "signals", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "diagnostics", "*.json")):
        total += copy(p, os.path.join(OUT, "diagnostics", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "signatures", "*.json")):
        total += copy(p, os.path.join(OUT, "signatures", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "power", "*.json")):
        total += copy(p, os.path.join(OUT, "power", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "related", "*.json")):
        total += copy(p, os.path.join(OUT, "related", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "rommap", "*.json")):
        total += copy(p, os.path.join(OUT, "rommap", os.path.basename(p))); files += 1

    print(f"{files:,} files, {total/1e6:.1f} MB -> web/data/")
    if files > 19000:
        print("  WARNING: approaching the 20,000-file Workers Assets limit")
    big = [p for p in glob.glob(os.path.join(OUT, "**", "*.json"), recursive=True)
           if os.path.getsize(p) > 25 * 1024 * 1024]
    if big:
        print(f"  WARNING: {len(big)} file(s) exceed the 25 MiB per-file limit")

if __name__ == "__main__":
    main()
