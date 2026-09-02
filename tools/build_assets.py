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
import json, os, shutil, glob, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_drawings import apply_flags  # noqa: E402

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
    print(f"{n} board asset(s) refreshed in web/data/ — the corpus index was "
          f"left untouched")


def main():
    if "--boards-only" in sys.argv:
        return publish_boards_only()

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
        apply_flags(doc, flags)
        n_draw += sum(1 for page in doc.get("pages", []) if page.get("draw"))
        n_noise += sum(1 for page in doc.get("pages", []) if page.get("noise"))
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
