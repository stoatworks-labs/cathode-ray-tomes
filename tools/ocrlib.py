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

def _is_table_row(line, gap_px):
    """A row with two or more wide internal gaps reads as tabular."""
    return line.get("_gaps", 0) >= 2

def _annotate_gaps(lines, space_px):
    """Record how many wide internal gaps each line has, for table detection.
    Word positions are gone by this point, so approximate from the text: runs
    of two or more spaces survive tesseract's layout output in table rows."""
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
    _annotate_gaps(lines, med)

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
                blocks.append({"k": "tr", "t": " ".join(l["t"].split())})
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
