#!/usr/bin/env python3
"""Give a board page its schematic: one traced sheet, and links to the rest.

A board page has room for one drawing. The corpus has, for most boards, a whole
schematic package -- APB's SP-308 runs to 24 sheets. So the page gets two
things: one sheet traced to SVG for the pan/zoom viewer, and a link to every
schematic document the machine has, whose scans already ship under web/pages/.

**Which sheet.** Picking one sheet out of twenty-four is a judgement, so it is
made from what the corpus already records rather than from the image:

  1. `drawing` in the board's spec names the sheets the board map was read from
     -- "DP-182 drawing package, sheets 01B and 02A". Those are the board's own
     sheets, named by the person who read them, so they win. Ten boards say
     this.
  2. Everything else cites a TM parts list, which is a table, not a schematic.
     For those the sheet comes from the machine's schematic package (SP-xxx),
     taking the first page whose title block reads "Schematic Diagram" and not
     "Memory Map" or "Wiring Diagram" -- an Atari title block names the sheet,
     so this reads the drawing's own account of itself rather than guessing
     from ink coverage.

A pick is recorded in data/board-sheets.json so it can be corrected by hand and
survive a rebuild; --pick overrides one from the command line.

  tools/build_board_schematic.py [slug ...] [--all] [--dry-run]
  tools/build_board_schematic.py centipede --pick <docId>:<page>
"""
import argparse, json, os, re, subprocess, sys, tempfile, shutil, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# An Atari title block names the sheet. That is a better witness to what a page
# is than any measure of the ink on it -- but only the title block counts. A
# harness drawing is headed "APB Main Wiring Diagram" and still says "CPU PCB
# SCHEMATIC 042571-01" across the top, because it cross-references the sheets it
# connects. Matching "pcb schematic" anywhere therefore picks the wiring
# diagram, so the phrases are tried strongest first and a weaker one is only
# reached when the whole package lacks the stronger.
TITLE = re.compile(r"(?i)schematic\s+diagram")
NAMED = re.compile(r"(?i)pcb\s+schematic|schematic\s*\(")
ANY = re.compile(r"(?i)schematic")

# A schematic package holds every board in the cabinet -- APB's SP-308 covers
# the CPU, Video, Audio II and Triac PCBs -- and orders them by sheet number,
# so the first schematic in the file is the audio board. The board page is
# about one of those boards, and its slug says which: `apb` wants the CPU
# sheet, `paperboy-video` the video one, `tempest-auxiliary` the auxiliary.
ROLES = (
    ("video", ("video",)),
    ("regulator", ("regulator", "audio")),
    ("audio", ("audio", "regulator")),
    ("auxiliary", ("auxiliary", "aux")),
    ("math", ("math",)),
)
DEFAULT_ROLE = ("cpu", "main", "logic", "game")


def role_for(slug):
    """The board role a slug is asking for, most specific first."""
    for token, roles in ROLES:
        if token in slug:
            return roles
    return DEFAULT_ROLE


def role_pattern(role):
    return re.compile(rf"(?i)\b{role}\b[A-Za-z ]{{0,14}}(?:PCB|board)?[A-Za-z ]{{0,6}}schematic")
# Only whole-page tables veto. A drawing-package sheet routinely carries a
# wiring diagram *beside* a PCB schematic, so "wiring diagram" is not
# disqualifying on its own -- vetoing on it costs nine boards their sheet.
TABLE = re.compile(r"(?i)memory\s+map|parts?\s+list|illustrated\s+parts")
# "DP-182 drawing package, sheets 01B and 02A" -> ("DP-182", ["01B", "02A"])
PKG = re.compile(r"(?i)\b([A-Z]{2,3}-\d{2,4})\b")
SHEETS = re.compile(r"(?i)\b(\d{2}[AB])\b")


def load(path, default=None):
    return json.load(open(path)) if os.path.exists(path) else default


class Corpus:
    """The indexes and the OCR, read once."""

    def __init__(self, root, cache):
        self.root, self.cache = root, cache
        self.boards = load(os.path.join(root, "data", "boards.json"), [])
        self.docs = load(os.path.join(root, "web", "data", "docs.json"), [])
        self.draw = load(os.path.join(root, "data", "drawings.json"), {})
        self.by_machine = collections.defaultdict(list)
        for d in self.docs:
            self.by_machine[d.get("machine")].append(d)
        self._text = {}

    def pdf(self, doc):
        return os.path.join(self.cache, "pdf", doc + ".pdf")

    def text(self, doc):
        if doc not in self._text:
            self._text[doc] = load(os.path.join(self.cache, "text", doc + ".json"))
        return self._text[doc]

    def page_text(self, doc, n):
        j = self.text(doc)
        if not j:
            return ""
        for pg in j.get("pages", []):
            if pg.get("n") == n:
                return " ".join((b.get("t") or "") for b in (pg.get("blocks") or []))
        return ""

    def drawing_pages(self, doc):
        """Pages this document draws on. A one-page sheet is its own drawing."""
        d = next((x for x in self.docs if x["id"] == doc), {})
        pages = (self.draw.get(doc, {}) or {}).get("draw")
        if pages:
            return list(pages)
        return [1] if d.get("pages", 0) == 1 else []

    def schematic_docs(self, machine):
        """Every schematic document for a machine whose scan we hold."""
        out = [d for d in self.by_machine.get(machine, [])
               if d.get("schematic") and os.path.exists(self.pdf(d["id"]))]
        out.sort(key=lambda d: d.get("title", ""))
        return out


def pick_from_provenance(corpus, board):
    """The sheets the board map was actually read from, when it names them."""
    drawing = board.get("drawing") or ""
    pkgs = PKG.findall(drawing)
    sheets = [s.upper() for s in SHEETS.findall(drawing)]
    if not pkgs or not sheets:
        return None
    for pkg in pkgs:
        for sheet in sheets:
            for d in corpus.schematic_docs(board.get("machine") or board["slug"]):
                title = d.get("title", "")
                if pkg.lower() not in title.lower():
                    continue
                if not re.search(rf"(?i)[-_]{sheet}\b", title):
                    continue
                pages = corpus.drawing_pages(d["id"])
                if pages:
                    return d["id"], pages[0], f"{pkg} sheet {sheet} (named by the board's provenance)"
    return None


def pick_from_package(corpus, board):
    """First real schematic sheet of the machine's schematic package."""
    machine = board.get("machine") or board["slug"]
    docs = corpus.schematic_docs(machine)
    # A schematic package before a drawing package: it is the board's own
    # schematic, where a DP is as often the cabinet's power supply and coin door.
    docs.sort(key=lambda d: (0 if re.search(r"(?i)\bSP-\d+", d.get("title", "")) else 1,
                             d.get("title", "")))
    # A title block that says "Schematic Diagram" is the strongest witness, so
    # take one wherever the package has it. Older packages -- and Pong, whose
    # sheets predate the convention -- only ever say "Schematic", so fall back
    # to that rather than leaving the board with nothing.
    for pattern, why in ((TITLE, "title block reads Schematic Diagram"),
                         (NAMED, "sheet names a PCB schematic"),
                         (ANY, "page names a schematic; package predates the title-block convention")):
        hits = []
        for d in docs:
            for n in corpus.drawing_pages(d["id"]):
                t = corpus.page_text(d["id"], n)
                if TABLE.search(t) or not pattern.search(t):
                    continue
                hits.append((d, n, t))
        if not hits:
            continue
        for role in role_for(board["slug"]):
            pat = role_pattern(role)
            hit = next((h for h in hits if pat.search(h[2])), None)
            if hit:
                d, n, _ = hit
                return d["id"], n, f"{d.get('title', '')} p{n} ({role.upper()} board; {why})"
        d, n, _ = hits[0]
        return d["id"], n, f"{d.get('title', '')} p{n} ({why})"
    return None


def pick(corpus, board, overrides):
    if board["slug"] in overrides:
        o = overrides[board["slug"]]
        return o["doc"], o["page"], o.get("why", "pinned in data/board-sheets.json")
    return pick_from_provenance(corpus, board) or pick_from_package(corpus, board)


def trace_page(pdf, page, dst, dpi=400):
    """Render one page bilevel and trace it. potrace wants the 1bpp PBM."""
    tmp = tempfile.mkdtemp(prefix="crt-sheet-")
    try:
        subprocess.run(["pdftoppm", "-r", str(dpi), "-mono",
                        "-f", str(page), "-l", str(page),
                        pdf, os.path.join(tmp, "p")],
                       capture_output=True, timeout=1800, check=True)
        pbms = [f for f in os.listdir(tmp) if f.endswith(".pbm")]
        if not pbms:
            raise RuntimeError(f"no page {page} in {pdf}")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        subprocess.run(["potrace", os.path.join(tmp, pbms[0]), "-s", "-o", dst,
                        "--turdsize", "4", "--alphamax", "1.0",
                        "--opttolerance", "0.6", "--flat"],
                       check=True, capture_output=True)
        theme_aware(dst)
        return os.path.getsize(dst)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def theme_aware(svg):
    """potrace hard-codes black on a transparent ground, which is black-on-black
    in a dark UI. Point the ink at currentColor and paint the paper explicitly."""
    s = open(svg).read()
    s = s.replace('fill="#000000"', 'fill="currentColor"')
    s = re.sub(r'(<g[^>]*fill=")#000000(")', r"\1currentColor\2", s)
    m = re.search(r"<svg[^>]*>", s)
    if m:
        s = s[:m.end()] + '<rect width="100%" height="100%" fill="var(--paper,#fff)"/>' + s[m.end():]
    open(svg, "w").write(s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="report picks, trace nothing")
    ap.add_argument("--pick", help="<docId>:<page>, with a single slug")
    ap.add_argument("--cache", default=os.path.join(ROOT, "cache"))
    ap.add_argument("--dpi", type=int, default=400)
    ap.add_argument("--budget", type=float, default=4.0,
                    help="MB above which a trace is discarded for the page scan")
    a = ap.parse_args()

    corpus = Corpus(ROOT, a.cache)
    sheets_path = os.path.join(ROOT, "data", "board-sheets.json")
    overrides = load(sheets_path, {})

    if a.pick:
        if len(a.slugs) != 1:
            sys.exit("--pick takes exactly one slug")
        doc, _, page = a.pick.partition(":")
        overrides[a.slugs[0]] = {"doc": doc, "page": int(page), "why": "pinned by hand"}
        json.dump(overrides, open(sheets_path, "w"), indent=1, sort_keys=True)
        print(f"pinned {a.slugs[0]} -> {doc} p{page}")

    todo = [b for b in corpus.boards
            if a.all or b["slug"] in a.slugs] if (a.all or a.slugs) else []
    if not todo:
        sys.exit("name a board slug, or pass --all")

    changed = built = skipped = scanned = 0
    for b in todo:
        slug = b["slug"]
        machine = b.get("machine") or slug
        chosen = pick(corpus, b, overrides)
        docs = corpus.schematic_docs(machine)
        # Link every schematic document whose scans already ship; the reader
        # shows them page by page, so the page need not carry them itself.
        b["schematicDocs"] = [{"id": d["id"], "title": d["title"], "pages": d.get("pages", 0)}
                              for d in docs]
        if not chosen:
            for k in ("svg", "svgSource", "sheet", "sheetKind", "sheetSource"):
                b.pop(k, None)
            print(f"{slug:<32} no schematic in the corpus")
            skipped += 1
            changed += 1
            continue
        doc, page, why = chosen
        scan = f"/pages/{doc}/p{page:04d}.webp"
        rel = f"/boards/{slug}/schematic.svg"
        dst = os.path.join(ROOT, "web", "boards", slug, "schematic.svg")
        print(f"{slug:<32} {doc} p{page:<3} {why[:52]}")
        kind, sheet = "scan", scan
        if not a.dry_run:
            size = trace_page(corpus.pdf(doc), page, dst, a.dpi)
            # Tracing pays off on the schematic packages, which are clean
            # bilevel line art: a sheet lands around a megabyte and stays sharp
            # at any zoom. The older drawing packages are greyscale photographs
            # of stained paper, where a global threshold either breaks the pale
            # ink or traces the foxing -- 26 MB of speckle for a sheet that is
            # no more readable than its scan, and past the 25 MiB per-file
            # asset limit besides. So the trace has to earn its place: over
            # budget and the board falls back to the scan it already ships,
            # which costs the deploy nothing and reads just as well.
            if size <= a.budget * 1048576:
                kind, sheet = "svg", rel
                print(f"{'':<32} -> {rel}  {size/1024:.0f} KB")
                built += 1
            else:
                os.remove(dst)
                d = os.path.dirname(dst)
                if not os.listdir(d):
                    os.rmdir(d)
                print(f"{'':<32} -> {scan}  (trace was {size/1048576:.0f} MB, over the {a.budget} MB budget)")
                scanned += 1
        b["sheet"] = sheet
        b["sheetKind"] = kind
        b["sheetSource"] = {"doc": doc, "page": page}
        b.pop("svg", None)
        b.pop("svgSource", None)
        changed += 1

    if not a.dry_run and changed:
        json.dump(corpus.boards, open(os.path.join(ROOT, "data", "boards.json"), "w"), indent=1)
        print(f"\n{changed} boards updated in data/boards.json "
              f"({built} traced, {scanned} kept their scan, {skipped} without a schematic)")
        print("run tools/build_assets.py --boards-only to publish")
    elif a.dry_run:
        print(f"\ndry run: {changed} boards would change, {skipped} have no schematic")


if __name__ == "__main__":
    main()
