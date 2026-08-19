#!/usr/bin/env python3
"""Emit wrangler kv bulk-put payloads for the machine records and documents.

wrangler's bulk endpoint takes an array of {key, value} pairs; values must be
strings, so each record is serialised. Chunked to stay well inside the
per-request size limit.
"""
import json, os, glob, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHUNK_BYTES = 8 * 1024 * 1024      # comfortably under the 100 MB request cap

def entries():
    for fp in sorted(glob.glob(os.path.join(ROOT, "data", "machine", "*.json"))):
        slug = os.path.basename(fp)[:-5]
        yield f"m:{slug}", open(fp).read()
    for fp in sorted(glob.glob(os.path.join(ROOT, "cache", "text", "*.json"))):
        did = os.path.basename(fp)[:-5]
        yield f"d:{did}", open(fp).read()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in glob.glob(os.path.join(a.out, "*.json")):
        os.unlink(f)

    batch, size, n = [], 0, 0
    def flush():
        nonlocal batch, size, n
        if not batch:
            return
        with open(os.path.join(a.out, f"chunk-{n:03d}.json"), "w") as f:
            json.dump(batch, f)
        n += 1
        batch, size = [], 0

    total = 0
    for key, value in entries():
        batch.append({"key": key, "value": value})
        size += len(value) + len(key) + 32
        total += 1
        if size >= CHUNK_BYTES:
            flush()
    flush()
    print(f"{total} keys in {n} chunk(s) -> {a.out}")

if __name__ == "__main__":
    main()
