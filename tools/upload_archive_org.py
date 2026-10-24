#!/usr/bin/env python3
"""Give the Internet Archive the documents we hold that it does not.

    python3 tools/upload_archive_org.py --check      # search the archive for each; no credentials
    python3 tools/upload_archive_org.py --dry-run    # print the items that would be created
    python3 tools/upload_archive_org.py --upload     # create them (needs `ia configure`)

The survey found 2,065 of our documents already on archive.org under the same
filenames. This is for the rest: the ArcadeRTFM documents no name matched,
and the GamingDoc set. `--check` searches the archive by title for each one
and caches the answer under cache/archive_org/check/, so a document that is
there under another name is not uploaded twice; `--dry-run` shows what would
go; `--upload` sends them.

Credentials are yours, not this script's. Install the archive's own client
(`pip install internetarchive`) and run `ia configure` once; it stores your
keys in ~/.config/internetarchive/ia.ini and this script reads nothing else.
Uploads go to the `opensource` (Community Texts) collection, which is where
an ordinary account can create items; the `arcademanuals` collection is
curated and its maintainers move items in. Each item credits its source
archive and carries the machine as a subject, the way the existing items do.

This is a rights decision as much as a technical one: these are publisher-
copyright manuals, uploaded as the archive's other arcade manuals were, for
preservation. The script does nothing without a flag.
"""
import argparse, json, os, re, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, "data", "sources", "archive_org.json")
CHECK = os.path.join(ROOT, "cache", "archive_org", "check")
UA = "cathode-ray-tomes-survey/0.1 (+https://cathode-ray-tomes.com)"
DELAY = 0.5
SOURCE_NAMES = {"arcadertfm": "ArcadeRTFM (arcadertfm.com)", "gamingdoc": "GamingDoc (gamingdoc.org)"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def pretty(title):
    return re.sub(r"\s+", " ", re.sub(r"\.pdf$", "", title, flags=re.I).replace("_", " ")).strip()


def candidates():
    docs = json.load(open(os.path.join(ROOT, "web", "data", "docs.json")))
    mirrors = json.load(open(SURVEY))["mirrors"]
    out = []
    for d in docs:
        if d["id"] in mirrors or d.get("dead"):
            continue
        pdf = os.path.join(ROOT, "cache", "pdf", d["id"] + ".pdf")
        if not os.path.exists(pdf) or os.path.getsize(pdf) == 0:
            continue
        out.append((d, pdf))
    return out


def search(title):
    """Items whose title matches, cached. A hit means: do not upload."""
    path = os.path.join(CHECK, norm(title) + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    q = {"q": f'title:("{pretty(title)}") AND mediatype:texts', "fl[]": "identifier",
         "rows": 5, "output": "json"}
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(q, doseq=True)
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60))
        hits = [x["identifier"] for x in d["response"]["docs"]]
    except Exception as e:                                  # noqa: BLE001
        hits = {"error": str(e)}
    os.makedirs(CHECK, exist_ok=True)
    json.dump(hits, open(path, "w"))
    time.sleep(DELAY)
    return hits


def item_for(d):
    name = pretty(d["title"])
    machine = d.get("machineName") or ""
    ident = re.sub(r"_+", "_", norm(d["title"]))[:80].strip("_") or d["id"]
    return {
        "identifier": ident,
        "metadata": {
            "title": name,
            "mediatype": "texts",
            "collection": "opensource",
            "subject": [s for s in (machine, "Arcade Manual", "Manual", "Retro") if s],
            "description": (f"Service documentation for the {machine} arcade machine: {name}. "
                            f"Mirrored for preservation from {SOURCE_NAMES.get(d.get('source') or 'arcadertfm', d.get('source'))}, "
                            f"where it is held at {d.get('src')}. Searchable, page by page, at "
                            f"https://cathode-ray-tomes.com/doc/{d['id']}."),
            "source": d.get("src"),
            "language": "eng",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--upload", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    if not (a.check or a.dry_run or a.upload):
        ap.error("one of --check, --dry-run, --upload")

    cands = candidates()
    print(f"{len(cands)} documents held here and not found on archive.org by name")
    if a.check:
        found = 0
        for i, (d, _) in enumerate(cands, 1):
            hits = search(d["title"])
            if isinstance(hits, list) and hits:
                found += 1
            if i % 50 == 0:
                print(f"  checked {i}/{len(cands)}, {found} found under another title", flush=True)
        print(f"{found} are there under another title; {len(cands) - found} are not")
        return

    todo = []
    for d, pdf in cands:
        hits = search.__wrapped__(d["title"]) if False else None
        path = os.path.join(CHECK, norm(d["title"]) + ".json")
        if os.path.exists(path):
            hits = json.load(open(path))
            if isinstance(hits, list) and hits:
                continue
        todo.append((d, pdf))
    if a.limit:
        todo = todo[:a.limit]
    total = sum(os.path.getsize(p) for _, p in todo)
    print(f"{len(todo)} to upload, {total/1e6:.0f} MB")

    if a.dry_run:
        for d, pdf in todo[:20]:
            it = item_for(d)
            print(f"  {it['identifier']:<60} {os.path.getsize(pdf)/1e6:6.1f} MB  {it['metadata']['title'][:50]}")
        if len(todo) > 20:
            print(f"  … and {len(todo) - 20} more")
        return

    try:
        import internetarchive as ia
    except ImportError:
        sys.exit("pip install internetarchive, then `ia configure`, then run again")
    done = 0
    for d, pdf in todo:
        it = item_for(d)
        r = ia.upload(it["identifier"], files={d["title"]: pdf}, metadata=it["metadata"],
                      retries=3, verbose=False)
        ok = all(getattr(x, "status_code", 0) == 200 for x in r)
        done += ok
        print(f"  {'ok  ' if ok else 'FAIL'} {it['identifier']}", flush=True)
        time.sleep(1)
    print(f"uploaded {done}/{len(todo)}")


if __name__ == "__main__":
    main()
