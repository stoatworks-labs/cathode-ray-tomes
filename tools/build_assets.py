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
    ]:
        p = os.path.join(ROOT, src)
        if os.path.exists(p):
            total += copy(p, os.path.join(OUT, name)); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "machine", "*.json")):
        total += copy(p, os.path.join(OUT, "machine", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        total += copy(p, os.path.join(OUT, "doc", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "index", "postings", "*.json")):
        total += copy(p, os.path.join(OUT, "postings", os.path.basename(p))); files += 1

    for p in glob.glob(os.path.join(ROOT, "data", "parts", "*.json")):
        total += copy(p, os.path.join(OUT, "parts", os.path.basename(p))); files += 1

    print(f"{files:,} files, {total/1e6:.1f} MB -> web/data/")
    if files > 19000:
        print("  WARNING: approaching the 20,000-file Workers Assets limit")
    big = [p for p in glob.glob(os.path.join(OUT, "**", "*.json"), recursive=True)
           if os.path.getsize(p) > 25 * 1024 * 1024]
    if big:
        print(f"  WARNING: {len(big)} file(s) exceed the 25 MiB per-file limit")

if __name__ == "__main__":
    main()
