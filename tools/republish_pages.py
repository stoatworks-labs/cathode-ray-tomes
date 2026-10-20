#!/usr/bin/env python3
"""Merge freshly extracted pages into a published document, and nothing else.

    python3 tools/ingest_vector.py --doc <id> --no-svg --no-images   # -> cache/text/<id>.json
    python3 tools/republish_pages.py <id> <page> [<page> ...]        # -> web/data/doc/<id>.json

Why this exists: a change to the extraction rules reaches web/data/ only when a
document is next ingested, and the documents published before the change keep
the old output indefinitely. check_pages.py is how a stale one shows up -- the
one-cell rows it reported came from rules fixed two days before the check
existed. Re-ingesting a whole document to clear one page is not always the right
shape, though: a rule added since can change other pages of the same document
(band_rows regrouped page 29 of the PS3 BD-drive manual into a table, which wants
its scan published with it), and that is a separate decision from the page that
failed. So this takes pages by number, replaces their text, and reports what
changed. Everything the page already carries -- its scan, drawing flags -- stays.

It is the document-level counterpart of build_assets.py's `--tables-only`, with
the same reasoning: a full build_assets.py regenerates web/data/ from
data/index/, which is gitignored and built per checkout, so running one from a
worktree that never built an index would wipe the corpus it set out to repair.
This touches one file per document and no index; the postings are untouched,
which is safe only while the words are -- it refuses a page whose word count
changes, and says so.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_TEXT = os.path.join(ROOT, "cache", "text")
PUBLISHED = os.path.join(ROOT, "web", "data", "doc")


def merge(did, pages, apply=True):
    """Return [(page, [(old block, new block), ...])] for what would change.

    Writes the published document unless `apply` is false.
    """
    with open(os.path.join(CACHE_TEXT, did + ".json")) as f:
        fresh = json.load(f)
    path = os.path.join(PUBLISHED, did + ".json")
    with open(path) as f:
        doc = json.load(f)

    new_by_n = {p["n"]: p for p in fresh["pages"]}
    report = []
    for page in doc["pages"]:
        if page["n"] not in pages:
            continue
        new = new_by_n.get(page["n"])
        if new is None:
            sys.exit(f"{did}: page {page['n']} is not in the fresh extraction")
        if new["words"] != page["words"]:
            # The postings were built from the old text. Same words in another
            # order or spacing is invisible to them; different words are not.
            sys.exit(f"{did} p{page['n']}: word count {page['words']} -> "
                     f"{new['words']}; the search index would be stale -- "
                     f"rebuild it rather than patch the page")
        old_blocks, new_blocks = page["blocks"], new["blocks"]
        diffs = [(a, b) for a, b in zip(old_blocks, new_blocks) if a != b]
        if len(old_blocks) != len(new_blocks):
            diffs.append((f"{len(old_blocks)} blocks", f"{len(new_blocks)} blocks"))
        report.append((page["n"], diffs))
        page["blocks"] = new_blocks
        if "heads" in new:
            page["heads"] = new["heads"]

    missing = pages - {p["n"] for p in doc["pages"]}
    if missing:
        sys.exit(f"{did}: no such page(s) in the published document: {sorted(missing)}")

    doc["meta"]["blocks"] = sum(len(p["blocks"]) for p in doc["pages"])
    if apply:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        os.replace(tmp, path)
    return report


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    did, pages = sys.argv[1], {int(p) for p in sys.argv[2:]}
    for n, diffs in merge(did, pages):
        print(f"{did} p{n}: {len(diffs)} block(s) changed")
        for a, b in diffs:
            print(f"    - {a}\n    + {b}")


if __name__ == "__main__":
    main()
