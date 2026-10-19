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
  web/data/wiring.json          cabinet connector standards (data/wiring/library.json)
  web/data/layouts.json         index of the PCB layouts read from MAME's driver notes
  web/data/layout/<dir>.json    those layouts, one file per MAME source directory
"""
import json, os, shutil, glob, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_drawings import apply_flags  # noqa: E402
from page_tables import apply_tables, load as load_tables  # noqa: E402
import mame_data  # noqa: E402
import wiring_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "data")

def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return os.path.getsize(dst)

def published(path):
    """What the last commit published at web/data/<path>, or None."""
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", f"HEAD:web/data/{path}"],
                             capture_output=True, timeout=60)
        return json.loads(out.stdout) if out.returncode == 0 else None
    except Exception:
        return None


def check_sources_are_current():
    """Refuse to publish a corpus index older than the one already published.

    web/data/ is generated wholesale from data/index/, which is gitignored and
    built locally by build_index.py. Anyone whose local index is behind will
    regenerate web/data/ from it and silently revert whatever the last person
    published — the corpus only ever grows, so a smaller index is a stale one,
    never a real change.

    This is not hypothetical. Several sessions share these repos, and a run
    from a worktree whose data/index was a symlink to a stale checkout
    overwrote 39 files of another session's work — the whole document
    catalogue, the machine records and every search posting — in a commit that
    was otherwise a two-file front-end change. It was caught by reading `git
    status` before staging, which is not a control.
    """
    problems = []
    for name, src in (("docs.json", "data/index/docs.json"),
                      ("machines.json", "data/index/machines.json"),
                      ("chips.json", "data/index/chips.json")):
        local_path = os.path.join(ROOT, src)
        if not os.path.exists(local_path):
            continue
        was = published(name)
        if was is None:
            continue
        try:
            now = json.load(open(local_path))
        except Exception:
            continue
        if len(now) < len(was):
            problems.append(f"  {src}: {len(now)} records, but the published "
                            f"web/data/{name} already has {len(was)}")
    if not problems:
        return
    print("REFUSING to rebuild web/data/ — the local corpus index is behind "
          "what is already published:")
    print("\n".join(problems))
    print("\nRegenerating from it would revert whoever published the larger "
          "index. Fix the source first:")
    print("  git pull                                   # if the index is "
          "tracked upstream work")
    print("  python3 tools/build_index.py               # rebuild data/index/ "
          "from data/machines.raw.json")
    print("\nIf you are only publishing board work, which does not touch the "
          "corpus index,\npass --boards-only instead — that is the right answer "
          "almost every time.")
    print("If the shrinkage is genuinely intended, pass --force.")
    raise SystemExit(1)


def publish_boards_only():
    """Refresh just the board assets, leaving the rest of web/data/ alone.

    Board work does not touch the corpus index, but a full rebuild regenerates
    everything from data/index/ — so someone whose index is stale has to choose
    between not publishing their boards and reaching for --force, which is the
    one thing that reintroduces the clobber. This is the third option, and the
    one to take: it copies only what changed.
    """
    n = 0
    for name, src in (("boards.json", "data/boards.json"),):
        p = os.path.join(ROOT, src)
        if os.path.exists(p):
            copy(p, os.path.join(OUT, name)); n += 1
    for p in glob.glob(os.path.join(ROOT, "data", "chips", "*.json")):
        copy(p, os.path.join(OUT, "chips", os.path.basename(p))); n += 1
    # Which boards share hardware is board work too, and is corrected by it --
    # the Math Box trace is what showed Red Baron's board is not Battlezone's.
    for p in glob.glob(os.path.join(ROOT, "data", "related", "*.json")):
        copy(p, os.path.join(OUT, "related", os.path.basename(p))); n += 1
    # A board imported with its netlist (tools/import_jtcores.py) brings its
    # own signal lookup, and the board page searches it beside the chips.
    for p in glob.glob(os.path.join(ROOT, "data", "signals", "*.json")):
        copy(p, os.path.join(OUT, "signals", os.path.basename(p))); n += 1
    print(f"{n} board asset(s) refreshed in web/data/ — the corpus index was "
          f"left untouched")


def publish_tables_only():
    """Merge the recovered tables into the published documents, leaving the
    rest of web/data/ alone.

    Same reasoning as publish_boards_only, and the same trap avoided: a full
    rebuild regenerates everything from data/index/, which is gitignored and
    built per checkout, so running one from a worktree that has never built an
    index would clobber the corpus it is trying to improve. A table changes
    nothing but the blocks of the page it was found on.
    """
    docs = pages = 0
    for p in sorted(glob.glob(os.path.join(OUT, "doc", "*.json"))):
        rows = load_tables(os.path.basename(p)[:-5])
        if not rows:
            continue
        doc = json.load(open(p))
        n = apply_tables(doc, rows)
        if not n:
            continue
        with open(p, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        docs += 1
        pages += n
    print(f"{pages} page(s) across {docs} document(s) set as tables in "
          f"web/data/ — the corpus index was left untouched")


def publish_mame_only():
    """Put MAME's account of each machine on the published machine pages.

    The same reasoning as the other targeted publishers: a full rebuild needs
    data/index/, which a worktree does not have, and would clobber the corpus.
    This touches only web/data/machine/ and the CPU column of machines.json,
    which a machine with no upstream CPU data gets from MAME's chip list.
    """
    path = os.path.join(OUT, "machines.json")
    machines = json.load(open(path))
    by = {m["s"]: m for m in machines}
    changed = filled = 0
    pages = sorted(glob.glob(os.path.join(OUT, "machine", "*.json")))
    rom_to_slug = {}
    for p in pages:
        rec = json.load(open(p))
        if rec.get("rom"):
            rom_to_slug[rec["rom"]] = rec["slug"]
    for p in pages:
        rec = json.load(open(p))
        if not mame_data.apply(rec, rom_to_slug):
            continue
        with open(p, "w") as f:
            json.dump(rec, f, separators=(",", ":"))
        changed += 1
        m = by.get(rec.get("slug"))
        if m is not None and not m.get("c") and rec.get("cpu"):
            m["c"] = [c["n"] for c in rec["cpu"]][:3]
            filled += 1
    with open(path, "w") as f:
        json.dump(machines, f, separators=(",", ":"))
    print(f"{changed} machine page(s) given MAME {mame_data.load().get('version')} data, "
          f"{filled} CPU list(s) filled -- the corpus index was left untouched")


def write_wiring_library():
    with open(os.path.join(OUT, "wiring.json"), "w") as f:
        json.dump(wiring_data.library(), f, separators=(",", ":"))


def publish_wiring_only():
    """Put the generated wiring view on the published machine pages.

    Touches web/data/wiring.json (the connector library the page draws from)
    and the `wiring` field of web/data/machine/*.json, nothing else -- the same
    reasoning as --mame-only, which it otherwise mirrors.
    """
    write_wiring_library()
    pages_by_doc = wiring_pages_in_corpus()
    changed = tagged = with_pages = 0
    by_std = {}
    for p in sorted(glob.glob(os.path.join(OUT, "machine", "*.json"))):
        rec = json.load(open(p))
        a = wiring_data.apply(rec)
        b = wiring_data.apply_pages(rec, pages_by_doc)
        if a or b:
            with open(p, "w") as f:
                json.dump(rec, f, separators=(",", ":"))
            changed += 1
        if rec.get("wpages"):
            with_pages += 1
        if rec.get("wiring"):
            tagged += 1
            k = rec["wiring"]["std"]
            by_std[k] = by_std.get(k, 0) + 1
    print(f"{tagged} machine page(s) carry a generated wiring view "
          f"({', '.join(f'{k} {v}' for k, v in sorted(by_std.items(), key=lambda kv: -kv[1]))}); "
          f"{sum(len(v) for v in pages_by_doc.values())} wiring page(s) found in "
          f"{len(pages_by_doc)} document(s), linked from {with_pages} machine page(s); "
          f"{changed} changed -- the corpus index was left untouched")


def wiring_pages_in_corpus():
    """{doc id: [(page, kind, heading)]} over every published document."""
    out = {}
    for p in glob.glob(os.path.join(OUT, "doc", "*.json")):
        try:
            doc = json.load(open(p))
        except Exception:
            continue
        found = wiring_data.doc_pages(doc)
        if found:
            out[doc.get("id") or os.path.basename(p)[:-5]] = found
    return out


def publish_layouts(out=OUT):
    """Copy the PCB layouts read from MAME's driver notes into web/data/.

    tools/extract_mame_layouts.py writes them to data/mame/; this publishes the
    shards as they are and the index without its measurement block, which is
    for the repository and not the reader. Returns (files, bytes).
    """
    src = os.path.join(ROOT, "data", "mame", "layouts.json")
    if not os.path.exists(src):
        return 0, 0
    dst = os.path.join(out, "layout")
    if os.path.isdir(dst):
        shutil.rmtree(dst)          # a directory MAME no longer has must not linger
    files = total = 0
    for p in glob.glob(os.path.join(ROOT, "data", "mame", "layouts", "*.json")):
        total += copy(p, os.path.join(dst, os.path.basename(p))); files += 1
    rows = json.load(open(src))["layouts"]
    keep = ("id", "src", "line", "name", "mfr", "year", "caption", "scope", "slugs",
            "devices")
    with open(os.path.join(out, "layouts.json"), "w") as f:
        json.dump([{k: r[k] for k in keep if k in r} for r in rows], f,
                  ensure_ascii=False, separators=(",", ":"))
    total += os.path.getsize(os.path.join(out, "layouts.json")); files += 1
    return files, total


def publish_layouts_only():
    """Publish just the PCB layouts. Same reasoning as the other targeted
    publishers: a full rebuild needs data/index/, which a worktree does not
    have, and would clobber the corpus."""
    files, total = publish_layouts()
    print(f"{files} PCB layout file(s), {total / 1e6:.1f} MB, refreshed in web/data/ -- "
          f"the corpus index was left untouched")


def main():
    if "--boards-only" in sys.argv:
        return publish_boards_only()
    if "--mame-only" in sys.argv:
        return publish_mame_only()
    if "--wiring-only" in sys.argv:
        return publish_wiring_only()
    if "--layouts-only" in sys.argv:
        return publish_layouts_only()
    if "--tables-only" in sys.argv:
        return publish_tables_only()

    if "--force" not in sys.argv:
        check_sources_are_current()

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

    # The connector library the machine pages' wiring views draw from; the
    # views themselves were put on the records by build_index.py.
    write_wiring_library(); files += 1

    # Drawing pages are decided by tools/build_drawings.py and merged in here
    # rather than written back into cache/text/, which is the ingest's own
    # checkpoint and has to stay the OCR as it came out. A page flagged `draw`
    # is shown as its scan; one flagged `noise` keeps its text and is marked as
    # having come off a drawing. See build_drawings.py for why those are
    # different answers.
    dpath = os.path.join(ROOT, "data", "drawings.json")
    drawings = json.load(open(dpath)) if os.path.exists(dpath) else {}
    # Tables are merged the same way and for the same reason: tools/page_tables.py
    # re-reads a page from its scan to recover the columns the flat text lost,
    # and the result belongs to the published document rather than to the
    # checkpoint the ingest wrote.
    n_draw = n_noise = n_table = 0
    for p in glob.glob(os.path.join(ROOT, "cache", "text", "*.json")):
        fid = os.path.basename(p)[:-5]
        flags = drawings.get(fid)
        tables = load_tables(fid)
        dst = os.path.join(OUT, "doc", os.path.basename(p))
        if not flags and not tables:
            total += copy(p, dst); files += 1
            continue
        doc = json.load(open(p))
        if tables:
            n_table += apply_tables(doc, tables)
        if flags:
            apply_flags(doc, flags)
        n_draw += sum(1 for page in doc.get("pages", []) if page.get("draw"))
        n_noise += sum(1 for page in doc.get("pages", []) if page.get("noise"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w") as f:
            json.dump(doc, f, separators=(",", ":"))
        total += os.path.getsize(dst); files += 1
    if drawings:
        print(f"  {n_draw} pages marked as drawings, {n_noise} as drawing noise")
    if n_table:
        print(f"  {n_table} pages set as tables")

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

    n, size = publish_layouts()
    files += n; total += size
    # Wiring pages are found in the rendered documents, so they can only be
    # linked from the machine pages once those are written -- the last step.
    pages_by_doc = wiring_pages_in_corpus()
    for p in glob.glob(os.path.join(OUT, "machine", "*.json")):
        rec = json.load(open(p))
        if wiring_data.apply_pages(rec, pages_by_doc):
            with open(p, "w") as f:
                json.dump(rec, f, separators=(",", ":"))

    print(f"{files:,} files, {total/1e6:.1f} MB -> web/data/")
    if files > 19000:
        print("  WARNING: approaching the 20,000-file Workers Assets limit")
    big = [p for p in glob.glob(os.path.join(OUT, "**", "*.json"), recursive=True)
           if os.path.getsize(p) > 25 * 1024 * 1024]
    if big:
        print(f"  WARNING: {len(big)} file(s) exceed the 25 MiB per-file limit")

if __name__ == "__main__":
    main()
