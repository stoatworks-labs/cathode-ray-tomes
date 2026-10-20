#!/usr/bin/env python3
"""Merge freshly extracted pages into a published document, and nothing else.

    python3 tools/ingest_vector.py --doc <id> --no-svg --no-images   # -> cache/text/<id>.json
    python3 tools/ingest_vector.py --doc <id> --no-svg               # ...and web/pages/<id>/ scans,
                                                                     # for a page that now banded into a table
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
A page that banded into a table gains the scan it needs (dw/dh), provided the
extraction ran with images on and web/pages/<id>/p####.webp exists.

It is the document-level counterpart of build_assets.py's `--tables-only`, with
the same reasoning: a full build_assets.py regenerates web/data/ from
data/index/, which is gitignored and built per checkout, so running one from a
worktree that never built an index would wipe the corpus it set out to repair.
This touches one document file and the postings shards its words fall in, and no
index. It refuses a page whose word count changes -- that is the extraction's own
count, taken from lines. It cannot see the other way the words move: the blocks
the old build kept can hold fewer words than the lines had (PS3 BD page 29's old
paragraphs had dropped 22 bare numbers and two "Remark" headers that its table
rows keep). So the postings are checked at the token level too, the way
build_search reads them, and where a term's count in this document rose the shard
entry is patched in place -- in the order build_search would give it, count then
document id, within its 400-entry cap. A count that would fall, or a shard that
was not built from this text, stops the merge instead.
"""
import collections, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_TEXT = os.path.join(ROOT, "cache", "text")
PUBLISHED = os.path.join(ROOT, "web", "data", "doc")
SCANS = os.path.join(ROOT, "web", "pages")
POSTINGS = os.path.join(ROOT, "web", "data", "postings")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_search


def _tokens(page):
    """The terms build_search would index for one page, as a Counter."""
    body = page.get("text") or " ".join(b["t"] for b in page.get("blocks", []))
    return collections.Counter(build_search.tokens(body.lower()))


def patch_postings(did, old, new, apply=True):
    """Bring this document's entries in the postings shards up to `new`.

    `old` and `new` are the document's token counts before and after. Returns
    (patched, skipped): terms changed, and terms left alone with the reason.
    """
    patched, skipped, work = [], [], {}
    for t in sorted(set(old) | set(new)):
        if old[t] == new[t]:
            continue
        if new[t] < old[t]:
            sys.exit(f"{did}: '{t}' falls from {old[t]} to {new[t]} hits; a patch "
                     f"cannot know who the cut-off entry would have been -- "
                     f"rebuild the index instead")
        shard = work.get(build_search.shard_of(t))
        if shard is None:
            fp = os.path.join(POSTINGS, build_search.shard_of(t) + ".json")
            with open(fp) as f:
                shard = work[build_search.shard_of(t)] = (fp, json.load(f))
        data = shard[1]
        entry = data.get(t)
        if entry is None:
            # Filtered for appearing in nearly every document, or never indexed.
            skipped.append((t, "not in the index"))
            continue
        mine = [e for e in entry if e[0] == did]
        if mine and mine[0][1] != old[t]:
            skipped.append((t, f"index says {mine[0][1]}, text says {old[t]}"))
            continue
        entry[:] = [e for e in entry if e[0] != did]
        at = next((i for i, e in enumerate(entry) if (-e[1], e[0]) > (-new[t], did)),
                  len(entry))
        entry.insert(at, [did, new[t]])
        del entry[build_search.MAX_POSTINGS:]
        if at >= build_search.MAX_POSTINGS:
            skipped.append((t, f"{new[t]} hits is below the {build_search.MAX_POSTINGS}"
                               f"-entry cut-off"))
            continue
        patched.append((t, old[t], new[t]))
    if apply:
        for fp, data in work.values():
            tmp = fp + ".tmp"
            with open(tmp, "w") as f:
                json.dump(data, f, separators=(",", ":"))
            os.replace(tmp, fp)
    return patched, skipped


def merge(did, pages, apply=True):
    """Return ([(page, [(old block, new block), ...])], patched, skipped).

    Writes the published document and patches its postings unless `apply` is false.
    """
    with open(os.path.join(CACHE_TEXT, did + ".json")) as f:
        fresh = json.load(f)
    path = os.path.join(PUBLISHED, did + ".json")
    with open(path) as f:
        doc = json.load(f)

    new_by_n = {p["n"]: p for p in fresh["pages"]}
    report = []
    old_tok = collections.Counter()
    for page in doc["pages"]:
        old_tok.update(_tokens(page))
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
        page["blocks"] = new_blocks
        if "heads" in new:
            page["heads"] = new["heads"]
        # A page that banded into a table now ships its scan, and dw/dh are what
        # make the reader show it. Taken only from a fresh extraction that ran
        # with images on, and only when the file is really there: dw/dh without
        # web/pages/<id>/p####.webp is the `missing-scan` fault check_pages names.
        if new.get("dw") and new.get("dh") and not page.get("dw"):
            scan = os.path.join(SCANS, did, "p%04d.webp" % page["n"])
            if not os.path.exists(scan):
                sys.exit(f"{did} p{page['n']}: fresh extraction carries dw/dh but "
                         f"{os.path.relpath(scan, ROOT)} does not exist; ingest "
                         f"with images on (no --no-images) first")
            page["dw"], page["dh"] = new["dw"], new["dh"]
            diffs.append(("no scan shown", f"scan {new['dw']}x{new['dh']} "
                          f"(web/pages/{did}/p{page['n']:04d}.webp)"))
        report.append((page["n"], diffs))

    missing = pages - {p["n"] for p in doc["pages"]}
    if missing:
        sys.exit(f"{did}: no such page(s) in the published document: {sorted(missing)}")

    doc["meta"]["blocks"] = sum(len(p["blocks"]) for p in doc["pages"])
    new_tok = collections.Counter()
    for page in doc["pages"]:
        new_tok.update(_tokens(page))
    patched, skipped = patch_postings(did, old_tok, new_tok, apply=apply)
    if apply:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        os.replace(tmp, path)
    return report, patched, skipped


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    did, pages = sys.argv[1], {int(p) for p in sys.argv[2:]}
    report, patched, skipped = merge(did, pages)
    for n, diffs in report:
        print(f"{did} p{n}: {len(diffs)} block(s) changed")
        for a, b in diffs:
            print(f"    - {a}\n    + {b}")
    print(f"postings: {len(patched)} term(s) patched, {len(skipped)} left alone")
    for t, a, b in patched:
        print(f"    {t}: {a} -> {b}")
    for t, why in skipped:
        print(f"    {t}: left alone ({why})")


if __name__ == "__main__":
    main()
