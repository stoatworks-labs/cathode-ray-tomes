#!/usr/bin/env python3
"""Shared OCR + document-structure logic.

Tesseract can emit plain text and a TSV of word boxes from a single recognition
pass, so line geometry costs nothing extra. Line height is what lets us tell a
section heading from body text on a scan that has no font information at all.
"""
import csv, os, subprocess, tempfile, statistics, re
from collections import defaultdict

def ocr_page(png, psm="1", lang="eng", timeout=180):
    """Return (plain_text, lines). Each line: {t,x,y,w,h,c}.

    One tesseract invocation produces both outputs -- asking for 'txt tsv'
    reuses the same recognition pass.
    """
    base = tempfile.mktemp(prefix="crt-ocr-")
    try:
        subprocess.run(["tesseract", png, base, "--psm", psm, "-l", lang, "txt", "tsv"],
                       capture_output=True, timeout=timeout)
        text = ""
        if os.path.exists(base + ".txt"):
            text = " ".join(open(base + ".txt", errors="ignore").read().split())
        lines = []
        if os.path.exists(base + ".tsv"):
            rows = list(csv.DictReader(open(base + ".tsv", errors="ignore"),
                                       delimiter="\t", quoting=csv.QUOTE_NONE))
            # Preserve tesseract's own ordering. It resolves multi-column
            # layouts for us; re-sorting by y interleaves the columns and turns
            # a two-column service manual into nonsense.
            grouped = {}
            for r in rows:
                if r.get("level") != "5" or not (r.get("text") or "").strip():
                    continue
                key = (int(r["block_num"]), int(r["par_num"]), int(r["line_num"]))
                grouped.setdefault(key, []).append(r)
            for key in sorted(grouped):
                ws = grouped[key]
                try:
                    conf = statistics.mean(float(w["conf"]) for w in ws)
                    lines.append({
                        "b": key[0], "pa": key[1],
                        "t": " ".join(w["text"] for w in ws),
                        # Where each word sat, which is the only record that a
                        # line is a row of a table: joining the words with
                        # single spaces below throws the column gaps away.
                        "words": [(int(w["left"]), int(w["left"]) + int(w["width"]),
                                   w["text"]) for w in ws],
                        "x": min(int(w["left"]) for w in ws),
                        "y": min(int(w["top"]) for w in ws),
                        "w": max(int(w["left"]) + int(w["width"]) for w in ws) - min(int(w["left"]) for w in ws),
                        "h": max(int(w["height"]) for w in ws),
                        "c": round(conf, 1),
                    })
                except (ValueError, statistics.StatisticsError):
                    continue
        return text, lines
    finally:
        for ext in (".txt", ".tsv"):
            try: os.unlink(base + ext)
            except OSError: pass

# Lines that are page furniture rather than content.
NOISE = re.compile(r"^[\s.\-_—·|]*$")
# "Power Supply . . . 4" / "D. Self-Test Procedure ." -- a contents entry, not a section.
TOC_ENTRY = re.compile(r"[.\s·]{2,}\d{1,3}\s*$|\s\.\s*$|\.{3,}")
CONTENTS_PAGE = re.compile(r"table of contents|list of illustrations|list of figures", re.I)
# Atari-style part numbers: A035056-01, 92-047, A021084.04
PART_NO = re.compile(r"\b[A-Z]?\d{2,6}[-.]\d{2,4}\b")
FIGURE = re.compile(r"^(figure|fig\.?|table|photo)\s*\d+", re.I)
PAGENO = re.compile(r"^[-—\s]*\d{1,3}[-—\s]*$")

def _is_parts_page(lines):
    """Illustrated-parts-list pages set their table rows in large type, so every
    row reads as a heading. Detect them by the density of part numbers."""
    hits = sum(1 for l in lines if PART_NO.search(l["t"]))
    return hits >= 5


def _is_contents_page(lines):
    """A contents page is large-type and full of dot leaders; its entries would
    otherwise be detected as the very sections they point at."""
    joined = " ".join(l["t"] for l in lines)
    if CONTENTS_PAGE.search(joined):
        return True
    leaders = sum(1 for l in lines if re.search(r"[.·]{3,}", l["t"]))
    return leaders >= 4


# "A." / "3." / "1.2" -- the section numbering these manuals use throughout.
SECTION_NO = re.compile(r"^([A-Z]|\d{1,2}(\.\d{1,2})?)[.)]\s+\S")

def _is_subheading(t, caps):
    """Sub-headings are short, start capitalised, and are either numbered,
    fully capitalised, or title-cased. This deliberately errs towards missing a
    heading rather than promoting a line of body text or a DIP-switch table row."""
    if not t[:1].isupper():
        return False
    words = t.split()
    if len(words) > 6:
        return False
    if SECTION_NO.match(t):
        return True
    # A sentence fragment usually has an interior full stop followed by a word.
    if re.search(r"\.\s+\w", t):
        return False
    if caps > 0.85:
        return True
    capitalised = sum(1 for w in words if w[:1].isupper())
    return capitalised / len(words) >= 0.7


def _merge_wrapped(heads):
    """A heading set on two lines ("Maintenance" / "and Repair") arrives as two
    detections. Join them when they sit directly under one another at the same
    size, so the outline reads as the page does."""
    merged = []
    for h in heads:
        if merged:
            prev, a, b = merged[-1], merged[-1]["_l"], h["_l"]
            gap = b["y"] - (a["y"] + a["h"])
            same_size = abs(a["h"] - b["h"]) <= max(a["h"], b["h"]) * 0.28
            aligned = abs(a["x"] - b["x"]) <= max(a["h"], b["h"]) * 2.5
            starts_lower = h["t"][:1].islower()
            if prev["lvl"] == h["lvl"] and same_size and aligned and -2 <= gap <= a["h"] * 1.1 \
               and (starts_lower or not SECTION_NO.match(h["t"])):
                prev.setdefault("parts", [prev["t"]]).append(h["t"])
                prev["t"] = (prev["t"] + " " + h["t"]).strip()
                prev["_l"] = {"y": b["y"], "h": b["h"], "x": a["x"]}
                continue
        merged.append(h)
    for h in merged:
        h.pop("_l", None)
    return merged


def _normalise_heading(t):
    """Trim trailing dot leaders and page numbers so duplicates collapse."""
    t = re.sub(r"[.\s·]{2,}\d{1,3}\s*$", "", t)
    t = re.sub(r"[\s.·—-]+$", "", t)
    return t.strip()


def _body_height(pages):
    """Modal body-text height across the document, in pixels."""
    hs = [l["h"] for p in pages for l in p if 8 <= l["h"] <= 200]
    if not hs:
        return None
    hs.sort()
    return statistics.median(hs)

JUNK_CHARS = re.compile(r"[|\\/~«»_^{}<>]")

def _looks_like_prose(t):
    """Reject OCR debris: drawing callouts, part-number soup, stray glyphs."""
    if JUNK_CHARS.search(t):
        return False
    letters = sum(c.isalpha() for c in t)
    if letters / max(len(t), 1) < 0.55:
        return False
    if sum(c.isdigit() for c in t) / max(len(t), 1) > 0.3:
        return False
    words = [w for w in re.split(r"[^A-Za-z]+", t) if w]
    if not words:
        return False
    # A one-word heading must be a real word, not a three-letter fragment.
    if len(words) == 1 and len(words[0]) < 4:
        return False
    return max(len(w) for w in words) >= 3


def classify_headings(pages, min_conf=70):
    """Tag section headings per page.

    `pages` is a list of line-lists (one per page, in order). Returns a list of
    per-page heading lists: [{"t": text, "lvl": 1|2}].

    A heading is a short, confident line that is set noticeably larger than the
    document's body text. Dot-leader contents lines and figure captions are
    excluded -- they are large but are references, not sections.
    """
    body = _body_height(pages)
    if not body:
        return [[] for _ in pages]

    big, med = body * 1.7, body * 1.28
    out = []
    for lines in pages:
        heads = []
        if _is_contents_page(lines) or _is_parts_page(lines):
            out.append([])       # keep the page, drop its entries
            continue
        for l in lines:
            t = l["t"].strip()
            if not t or NOISE.match(t) or PAGENO.match(t) or FIGURE.match(t):
                continue
            if l["c"] < min_conf or len(t) > 80 or len(t) < 4:
                continue
            if TOC_ENTRY.search(t) or not _looks_like_prose(t):
                continue
            t = _normalise_heading(t)
            if len(t) < 4:
                continue
            if t.count(".") > 4:          # dot leaders => contents entry
                continue
            letters = [c for c in t if c.isalpha()]
            if not letters:
                continue
            caps = sum(c.isupper() for c in letters) / len(letters)
            if l["h"] >= big:
                heads.append({"t": t, "lvl": 1, "_l": l})
            elif l["h"] >= med and _is_subheading(t, caps):
                heads.append({"t": t, "lvl": 2, "_l": l})
        heads = _merge_wrapped(heads)
        # A page that is mostly "headings" is a title page or a drawing; keep the
        # largest few rather than flooding the outline.
        if len(heads) > 6:
            heads = heads[:6]
        out.append(heads)
    return out

def build_outline(page_heads):
    """Flatten per-page headings into a document outline with page anchors."""
    outline, seen = [], set()
    for i, heads in enumerate(page_heads, 1):
        for h in heads:
            key = re.sub(r"[^a-z0-9]+", "", h["t"].lower())
            if not key or key in seen:
                continue
            seen.add(key)
            outline.append({"t": h["t"], "lvl": h["lvl"], "p": i})
    return outline


# ---------------------------------------------------------------------------
# Block structure — turning recognised lines into a real document
# ---------------------------------------------------------------------------

BULLET = re.compile(r"^\s*([•·*\-–—]|\(?[a-z]\)|\(?\d{1,2}[.)])\s+\S")
# "CAUTION" / "NOTE:" style callouts these manuals use constantly
CALLOUT = re.compile(r"^(NOTE|CAUTION|WARNING|IMPORTANT|DANGER)\b[:.]?\s*", re.I)

def _dehyphenate(a, b):
    """Join a line ending in a hyphen to the next word without the hyphen."""
    if a.endswith("-") and not a.endswith("--") and b[:1].islower():
        return a[:-1] + b
    return a + " " + b

def _tidy_row(t):
    """Tidy a table row's spacing without closing up its column gaps.

    The reader splits a `tr` on runs of three or more spaces to get its cells,
    so the flat `" ".join(t.split())` that is right for a paragraph turns every
    table into a single-cell row — which is what the whole corpus had. Wide
    gaps are the only thing separating one cell from the next, so they survive;
    ordinary spacing is normalised as before.
    """
    return re.sub(r"\s+", lambda m: "   " if len(m.group()) >= 3 else " ",
                  t.strip())

# ---------------------------------------------------------------------------
# Table columns
# ---------------------------------------------------------------------------
#
# A DIP-switch row reaches us from tesseract on a single line, its cells set
# apart by whitespace an order of magnitude wider than a word space:
#
#     Off [74] 70 [7] seconds [8] per [7] coin [108] F
#
# The line's text throws that away -- the words are joined with single spaces
# -- so the row reads as a sentence, `_is_table_row` never fires, and
# `build_blocks` glues it to the row beneath it as a paragraph. The distances
# are not subtle; only the record of them was missing, which is why `ocr_page`
# now keeps the word boxes.
#
# The gap alone is not enough to act on, because the threshold that finds a
# real column also finds the hole OCR leaves where it dropped a word. What
# separates them is that a column *repeats*: a table's cells start at the same
# x line after line, and debris lands wherever it lands. So the gaps are only
# a proposal, and a cell start has to stack up down the page before the split
# is kept.
#
# Three columns, not two, because two is what a two-column prose page looks
# like when tesseract fails to separate its columns -- and interleaving those
# is the worst thing that can happen to this text.
COL_GAP_MULT  = 3.0   # a column gap, counted in word spaces
COL_GAP_MIN   = 12    # ...and in pixels, at the 150 dpi these scans are read at
COL_TOL_MULT  = 2.5   # cell starts this close, in word spaces, are one column
COL_MIN_CELLS = 3     # two cells a row is two-column prose
COL_MIN_ROWS  = 3     # a grid has to repeat before it is a grid
COL_MIN_HITS  = 3     # rows sharing a start before it counts as a column
CELL_GAP = "   "      # three spaces: what _is_table_row and the reader read


def _word_space(lines):
    """The page's ordinary space between two words, in pixels.

    Taken across the whole page rather than per line, which is what makes this
    work: a row of three cells has only two or three gaps of its own, and its
    median is the column gap itself, so a line-local threshold measures the
    thing it is meant to be detecting and finds nothing.
    """
    gaps = []
    for l in lines:
        ws = l.get("words") or []
        gaps += [b[0] - a[1] for a, b in zip(ws, ws[1:]) if b[0] >= a[1]]
    if len(gaps) < 8:
        return None
    gaps.sort()
    # The lower quartile, not the median: on a page that is mostly table the
    # column gaps are half the sample and would drag the median up with them.
    return max(gaps[len(gaps) // 4], 1)


def _split_cells(words, wide):
    """A line's words grouped into cells, breaking on any gap at least `wide`."""
    cells = [[words[0]]]
    for prev, w in zip(words, words[1:]):
        (cells.append([w]) if w[0] - prev[1] >= wide else cells[-1].append(w))
    return cells


def _cluster(xs, tol):
    """Sorted positions grouped into runs, breaking where the step exceeds `tol`."""
    runs, run = [], [xs[0]]
    for x in xs[1:]:
        if x - run[-1] <= tol:
            run.append(x)
        else:
            runs.append(run)
            run = [x]
    runs.append(run)
    return runs


# Geometry gets one page wrong, and always the same page. A schematic sheet
# sets its theory of operation in four or five narrow columns of running text,
# and those columns stack up as consistently as any grid does -- Asteroids
# sheet 2 side A is five columns of prose and reads, to everything above, as a
# five-column table. What separates them is not where the cells are but what
# is in them: a table's cell is a value, a designator, a part number, a short
# description, and a cell holding a clause is a sentence. One clause in a row
# is a description column and is common; a row built mostly of them is prose,
# and a page whose rows are mostly like that is prose in columns.
PROSE_STOP = frozenset(
    "the a an and or of to in is are was were for with that this it be on at "
    "as by from not you your".split())
PROSE_CELL_WORDS = 5   # words in a cell before it can be a clause
PROSE_CELL_STOPS = 2   # ...and function words in it
PROSE_ROW_CELLS = 2    # clauses in a row before the row reads as prose
PROSE_SHARE = 0.6      # of the rows, before the page does


def _is_clause(cell):
    words = cell.lower().split()
    return (len(words) >= PROSE_CELL_WORDS
            and sum(1 for w in words if w in PROSE_STOP) >= PROSE_CELL_STOPS)


def _reads_as_prose(rows):
    """Whether a page's recovered rows are running text in columns."""
    if not rows:
        return False
    wordy = sum(1 for cells in rows.values()
                if sum(1 for c in cells if _is_clause(c)) >= PROSE_ROW_CELLS)
    return wordy >= 3 and wordy >= len(rows) * PROSE_SHARE


def table_rows(lines, keep=()):
    """The page's lines that read as rows of one consistent grid.

    Returns {index in `lines`: [cell text, ...]}. An empty result is the common
    case and means "this page is not a table, leave it alone".

    `keep` is the text of lines already claimed as headings, which stand alone
    and are never rewritten as rows.
    """
    # A contents page is a column of entries against a column of page numbers,
    # so it reads as a grid and is not one. It already renders acceptably as
    # the list it is, and `classify_headings` holds it out of structure
    # detection for its own reasons; hold it out of this too rather than churn
    # a page that was never the problem.
    if _is_contents_page(lines):
        return {}
    space = _word_space(lines)
    if not space:
        return {}
    wide = max(space * COL_GAP_MULT, COL_GAP_MIN)

    proposed = {}
    for i, l in enumerate(lines):
        ws = l.get("words") or []
        if len(ws) < COL_MIN_CELLS or l["t"].strip() in keep:
            continue
        cells = _split_cells(ws, wide)
        if len(cells) >= COL_MIN_CELLS:
            proposed[i] = cells
    if len(proposed) < COL_MIN_ROWS:
        return {}

    # Which proposed cell starts are columns: the ones several rows share.
    tol = max(space * COL_TOL_MULT, 1)
    starts = sorted(c[0][0] for cells in proposed.values() for c in cells)
    cols = [(min(r), max(r)) for r in _cluster(starts, tol)
            if len(r) >= COL_MIN_HITS]
    if len(cols) < COL_MIN_CELLS:
        return {}

    rows = {}
    for i, cells in proposed.items():
        # Most of a row's cells must sit in a column, but not all of them: a
        # stray footnote mark in its own narrow column is real, and rejecting
        # the row over it would lose the setting the row documents.
        hits = sum(1 for c in cells
                   if any(lo - tol <= c[0][0] <= hi + tol for lo, hi in cols))
        if hits >= COL_MIN_CELLS:
            rows[i] = [" ".join(w[2] for w in c) for c in cells]
    if len(rows) < COL_MIN_ROWS or _reads_as_prose(rows):
        return {}
    return rows


def _is_table_row(line, gap_px):
    """A row with two or more wide internal gaps reads as tabular."""
    return line.get("_gaps", 0) >= 2


def _annotate_gaps(lines, space_px, keep=()):
    """Record how many wide internal gaps each line has, for table detection.

    Rows of a grid have their cells rejoined here with the wide gaps the rest
    of the pipeline reads as column breaks. Lines that already carry those gaps
    in their text -- the vector path bands its rows that way, having never had
    word boxes to lose -- are counted exactly as they always were.
    """
    for i, cells in table_rows(lines, keep).items():
        lines[i]["t"] = CELL_GAP.join(cells)
    for l in lines:
        l["_gaps"] = len(re.findall(r"\s{3,}", l["t"]))

def running_headers(pages, threshold=0.4):
    """Text that repeats on a large fraction of pages is a running header or
    footer (the game's name, a manual number), not content."""
    from collections import Counter
    seen = Counter()
    for lines in pages:
        for t in {re.sub(r"\d+", "", l["t"]).strip().lower() for l in lines[:3] + lines[-3:]}:
            if 3 <= len(t) <= 60:
                seen[t] += 1
    n = max(len(pages), 1)
    return {t for t, c in seen.items() if c >= n * threshold and n >= 4}


def build_blocks(lines, heads=None, body_h=None, skip=None):
    """Group recognised lines into semantic blocks for HTML rendering.

    Returns a list of {k: kind, t: text} where kind is one of:
      h1/h2  heading      p   paragraph
      li     list item    tr  table row
      note   callout (NOTE/CAUTION/WARNING)

    Blocks break on vertical gaps larger than normal leading, which is what
    separates paragraphs on a typewritten page.
    """
    if not lines:
        return []
    # Map every constituent line of a (possibly merged) heading to its full text.
    head_of, emitted = {}, set()
    for h in (heads or []):
        for part in h.get("parts", [h["t"]]):
            head_of[part] = h["t"]
    skip = skip or set()
    hs = sorted(l["h"] for l in lines)
    med = body_h or hs[len(hs) // 2]
    _annotate_gaps(lines, med, keep=set(head_of))

    blocks, cur, prev = [], [], None
    def flush():
        if not cur:
            return
        txt = cur[0]["t"]
        for nxt in cur[1:]:
            txt = _dehyphenate(txt, nxt["t"])
        txt = " ".join(txt.split())
        if not txt:
            cur.clear(); return
        if all(_is_table_row(l, med) for l in cur):
            for l in cur:
                blocks.append({"k": "tr", "t": _tidy_row(l["t"])})
        elif CALLOUT.match(txt):
            blocks.append({"k": "note", "t": txt})
        elif BULLET.match(cur[0]["t"]):
            blocks.append({"k": "li", "t": txt})
        else:
            blocks.append({"k": "p", "t": txt})
        cur.clear()

    for l in lines:
        t = l["t"].strip()
        if not t or NOISE.match(t) or PAGENO.match(t):
            continue
        if re.sub(r"\d+", "", t).strip().lower() in skip:
            continue                         # running header / footer
        if t in head_of:                     # headings stand alone
            full = head_of[t]
            flush()
            if full not in emitted:
                blocks.append({"k": "h", "t": full})
                emitted.add(full)
            prev = l
            continue
        if prev is not None:
            gap = l["y"] - (prev["y"] + prev["h"])
            starts_item = bool(BULLET.match(t)) or bool(CALLOUT.match(t))
            # a wide gap, a new list item, or a switch in/out of tabular layout
            if gap > med * 0.9 or starts_item or \
               (_is_table_row(l, med) != _is_table_row(prev, med)):
                flush()
        cur.append(l)
        prev = l
    flush()
    return blocks


def page_text(blocks):
    """Flatten blocks back to plain text for search indexing."""
    return " ".join(b["t"] for b in blocks)
