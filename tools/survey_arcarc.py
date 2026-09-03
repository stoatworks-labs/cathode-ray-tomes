#!/usr/bin/env python3
"""Catalogue the Arcade Archive (arcarc.xmission.com) without downloading a file.

Outputs: data/sources/arcarc.json

    python3 tools/survey_arcarc.py             # crawl the directory listings
    python3 tools/survey_arcarc.py --offline   # recompute from cache/arcarc/

The Arcade Archive is a plain Apache file tree hosted at XMission, maintained
by one volunteer (arcarc@xmission.com), with the documents sorted into
manufacturer directories (PDF_Arcade_Atari_Kee, PDF_Arcade_Bally_Midway, …)
and subject directories (PDF_Monitors, PDF_Dip_Switches_and_Pinouts, …). It
has no robots.txt, no API and no index beyond the listings themselves, so the
survey walks the listings — each one an HTML page a few KB long — and records
every PDF's path, size and date. It reads no document.

Rights: none stated anywhere on the site. It is a private mirror of the same
publisher-copyright material as everything else here. Taking from it is a
courtesy question for its maintainer before it is a technical one; the survey
exists so that conversation can start from numbers.

The crawl is serial with a delay and caches every listing under cache/arcarc/,
so a re-run touches only what it has not seen. The directories outside the
PDF_* set (pictures, ROM hacks, magazines, pinball) are counted from their
top-level listing and not descended into.
"""
import argparse, collections, html, json, os, re, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "arcarc")
OUT = os.path.join(ROOT, "data", "sources", "arcarc.json")
BASE = "https://arcarc.xmission.com/"
UA = "cathode-ray-tomes-survey/0.1 (+https://cathode-ray-tomes.com)"
DELAY = 0.4
MAX_DIRS = 4000

ROW = re.compile(r'<a href="([^"?][^"]*)">[^<]*</a>\s*</td>\s*<td[^>]*>\s*([\d-]+ [\d:]+)?\s*</td>\s*<td[^>]*>\s*([\d.]+[KMG]?|-)?\s*</td>', re.I)
LINK = re.compile(r'<a href="([^"?][^"]*)">')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", "replace")


def listing(path, offline):
    """The HTML of one directory listing, cached."""
    cpath = os.path.join(CACHE, urllib.parse.quote(path, safe="") + ".html")
    if os.path.exists(cpath):
        return open(cpath).read()
    if offline:
        return None
    s = get(BASE + urllib.parse.quote(path))
    os.makedirs(CACHE, exist_ok=True)
    open(cpath, "w").write(s)
    time.sleep(DELAY)
    return s


def bytes_of(s):
    if not s or s == "-":
        return 0
    mult = {"K": 1024, "M": 1024 ** 2, "G": 1024 ** 3}.get(s[-1], 1)
    return int(float(s.rstrip("KMG")) * mult)


def parse(s):
    """(dirs, files) in one listing; files are (name, date, bytes)."""
    dirs, files = [], []
    rows = ROW.findall(s)
    if rows:
        for href, date, size in rows:
            name = html.unescape(urllib.parse.unquote(href))
            if name.startswith("/") or name.startswith("../"):
                continue
            (dirs if name.endswith("/") else files).append(
                name if name.endswith("/") else (name, date, bytes_of(size)))
    else:                                  # a listing without size columns
        for href in LINK.findall(s):
            name = html.unescape(urllib.parse.unquote(href))
            if name.startswith("/") or name.startswith("../") or name.startswith("mailto"):
                continue
            (dirs if name.endswith("/") else files).append(
                name if name.endswith("/") else (name, "", 0))
    return dirs, files


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def machine_index(machines):
    idx = collections.defaultdict(list)
    for m in sorted(machines, key=lambda m: -(m.get("d") or 0)):
        base = re.sub(r"\s*\(.*?\)", "", m["n"]).split(" / ")[0]
        for key in {norm(m["n"]), norm(base)}:
            if key and m["s"] not in idx[key]:
                idx[key].append(m["s"])
    return idx


def guess_machine(name, idx):
    words = [w for w in norm(re.sub(r"\.pdf$", "", name, flags=re.I)).split("_") if w]
    for n in range(len(words), 0, -1):
        key = "_".join(words[:n])
        if key in idx:
            return {"slug": idx[key][0], "matched": key, "whole": n == len(words)}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()

    root = listing("", a.offline)
    top_dirs, top_files = parse(root)
    walk = [d for d in top_dirs if d.startswith("PDF_")]
    skipped = [d for d in top_dirs if not d.startswith("PDF_")]

    machines = json.load(open(os.path.join(ROOT, "web", "data", "machines.json")))
    idx = machine_index(machines)
    docs = json.load(open(os.path.join(ROOT, "web", "data", "docs.json")))
    ours = {norm(re.sub(r"\.pdf$", "", d["title"], flags=re.I)) for d in docs}

    files, per_top, n_dirs = [], collections.defaultdict(lambda: [0, 0, 0]), 0
    queue = list(walk)
    while queue and n_dirs < MAX_DIRS:
        path = queue.pop(0)
        s = listing(path, a.offline)
        if s is None:
            continue
        n_dirs += 1
        dirs, fs = parse(s)
        queue += [path + d for d in dirs]
        top = path.split("/")[0]
        for name, date, size in fs:
            per_top[top][0] += 1
            per_top[top][1] += size
            if not name.lower().endswith(".pdf"):
                continue
            per_top[top][2] += 1
            key = norm(re.sub(r"\.pdf$", "", name, flags=re.I))
            files.append({
                "path": path + name, "bytes": size, "date": date,
                "ours": key in ours,
                "machine": guess_machine(name, idx),
            })

    pdfs = files
    matched = [f for f in pdfs if f["machine"]]
    no_docs = {m["s"] for m in machines if not m.get("d")}
    totals = {
        "directoriesWalked": n_dirs,
        "capped": bool(queue),
        "pdfs": len(pdfs),
        "pdfBytes": sum(f["bytes"] for f in pdfs),
        "sameFilenameAsOurs": sum(1 for f in pdfs if f["ours"]),
        "matchedToMachine": len(matched),
        "wholeNameMatch": sum(1 for f in matched if f["machine"]["whole"]),
        "machinesGainingFirstDocument": len({f["machine"]["slug"] for f in matched
                                             if f["machine"]["slug"] in no_docs}),
        "byDirectory": {k: {"files": v[0], "bytes": v[1], "pdfs": v[2]}
                        for k, v in sorted(per_top.items())},
        "notWalked": skipped,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "source": {
            "name": "Arcade Archive (ARC ARC), XMission",
            "url": BASE, "contact": "arcarc@xmission.com",
            "surveyed": time.strftime("%Y-%m-%d"),
            "rights": "None stated; a volunteer mirror of publisher-copyright manuals. "
                      "No robots.txt. Ask before taking. Nothing taken; pointers only.",
        },
        "totals": totals,
        "pdfs": pdfs,
    }, open(OUT, "w"), indent=1, sort_keys=True)
    print(f"{n_dirs} directories walked{' (capped)' if queue else ''}, "
          f"{totals['pdfs']:,} PDFs, {totals['pdfBytes']/1e9:.1f} GB")
    print(f"{totals['sameFilenameAsOurs']:,} share a filename with ours; "
          f"{totals['matchedToMachine']:,} match a machine name "
          f"({totals['wholeNameMatch']:,} whole), "
          f"{totals['machinesGainingFirstDocument']:,} machines would gain a first document")
    for k, v in totals["byDirectory"].items():
        print(f"  {k:<40} {v['pdfs']:>6,} PDFs {v['bytes']/1e9:>6.1f} GB")
    print(f"not walked: {', '.join(skipped)}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
