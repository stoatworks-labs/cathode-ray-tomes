#!/usr/bin/env python3
"""Shared logic for taking documents from a surveyed archive into the corpus.

A surveyed archive gives us titles or filenames; the corpus is keyed by MAME
machine slug. What lives here is the translation, used by every take_*.py:

  guess_machine   the machine a title names, with a rule for when a match is
                  trustworthy enough to file the document under it
  type_of         the document type a title implies, in the catalogue's own
                  vocabulary (Schematics, Service Manual, ...)
  add_documents   append entries to data/extra-docs.json without duplicating
                  a URL already there or a file already in the corpus

The matching is deliberately conservative. A title is stripped of the words
that describe the document rather than the machine ("Operators Manual", "2nd
Printing", "DP-139"), and of an uploader's label ("Arcade Game Manual:") or a
maker's name ("Atari ...", "... by Konami"); what is left is matched against
every machine name as the longest leading run of words. A match on the whole
of what is left is taken. A match on a leading part is taken only when the
part is a name and not a word — five characters or more, or more than one
word, or the whole of a segment the title sets off with a dash or colon
("005 - Arcade Manual") — because "Zero Team" matching Zero and "Gun Buster"
matching Gun were what the loose rule produced.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRA = os.path.join(ROOT, "data", "extra-docs.json")

# Words that describe a document rather than name a machine.
DOC_WORDS = set("""
manual manuals schematic schematics package drawing drawings wiring diagram
diagrams parts list lists catalog catalogue operators operator operating owners
owner service instructions instruction technical installation install kit
conversion bulletin bulletins printing rev revision preliminary supplement
supplemental amendment addendum insert sheet sheets guide chart settings setting
switch switches dip dipswitch dipswitches pinout pinouts pin out troubleshooting
test notes note and of the with for from to sound board boards pcb logic
harness power supply monitor cabinet set upright cocktail table sitdown deluxe
standard type version complete partial alternative alt misc miscellaneous
universal german french spanish italian japanese english us uk eu jp usa
europe european japan digital digitalmanual serviceman partscatalog
electrical assembly assy field final ptm scan scans copy pages page
""".split())
# Atari's TM-143 / DP-139 / SP-218 / ST-139 codes, part numbers, dates, ordinals.
DOC_CODE = re.compile(r"^(tm|dp|sp|st|ck|sm|pm|om|ml|vm)?\d{2,}[a-z0-9-]*$|^\d+(st|nd|rd|th)$|^[a-z]\d{5,}[a-z0-9-]*$")

LABEL = re.compile(r"^\s*arcade\s+game[^:]*:\s*", re.I)
MAKER_SUFFIX = re.compile(r"\s+(?:by|from)\s+[A-Z][\w.&' -]*$")
MAKERS = """atari atari-games williams midway bally bally-midway sega namco konami
taito capcom nintendo data-east exidy gottlieb stern cinematronics centuri irem snk
jaleco kaneko tecmo technos nichibutsu universal gremlin zaccaria leland merit sente
rock-ola meadows gaelco psikyo raizing toaplan seibu sammy nmk visco seta mitchell
sunsoft playmark dynax tehkan banpresto hudson upl taito-america midway-games
""".split()


def norm(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s or "").lower()).strip("_")


def machine_index(machines):
    """Normalised machine name -> [slug], slugs that already have documents
    first. Both the full MAME name and its base (before any parenthetical or
    " / " alternative) are keys."""
    idx = {}
    # Documents-bearing slugs first, then arcade before consoles and handhelds:
    # "Teenage Mutant Ninja Turtles" is the arcade game, not the LCD handheld.
    for m in sorted(machines, key=lambda m: (-(m.get("d") or 0), bool(m.get("t")))):
        base = re.sub(r"\s*\(.*?\)", "", m["n"]).split(" / ")[0]
        for key in {norm(m["n"]), norm(base)}:
            if key:
                idx.setdefault(key, [])
                if m["s"] not in idx[key]:
                    idx[key].append(m["s"])
    return idx


def _words(title):
    t = MAKER_SUFFIX.sub("", LABEL.sub("", str(title or "")))
    t = re.sub(r"\.pdf$", "", t, flags=re.I)
    words = [w for w in norm(t).split("_") if w]
    while words and (words[-1] in DOC_WORDS or DOC_CODE.match(words[-1])):
        words.pop()
    return words


def _segments(title):
    """What the title sets off before a dash or colon: "005 - Arcade Manual"
    -> "005"; "1943: The Battle of Midway Schematics" -> "1943"."""
    t = LABEL.sub("", str(title or ""))
    return {norm(seg) for seg in re.split(r"\s+[-–—]\s+|:\s+", t)[:1]}


def guess_machine(title, idx):
    """{slug, matched, whole, why} or None. `why` says how it was accepted."""
    best = None
    words = _words(title)
    candidates = [words]
    if words and words[0].replace("_", "-") in MAKERS or (words and words[0] in MAKERS):
        candidates.append(words[1:])            # "Atari 4 Player Football"
    for ws in candidates:
        for n in range(len(ws), 0, -1):
            key = "_".join(ws[:n])
            if key in idx:
                whole = n == len(ws)
                cand = {"slug": idx[key][0], "matched": key, "whole": whole}
                if best is None or len(key) > len(best["matched"]):
                    best = cand
                break
    if not best:
        return None
    key = best["matched"]
    if best["whole"]:
        best["why"] = "whole title"
    elif "_" in key or len(key) >= 5:
        best["why"] = "leading name"
    elif key in _segments(title):
        best["why"] = "leading segment"
    else:
        return None
    return best


TYPES = [
    ("Schematics", re.compile(r"schematic|game logic|circuit", re.I)),
    ("Wiring Diagram", re.compile(r"wiring", re.I)),
    ("Drawing Package", re.compile(r"drawing (?:package|set)|\bdp-\d", re.I)),
    ("Parts Catalog", re.compile(r"parts? (?:catalog|list)|illustrated parts", re.I)),
    ("Service Bulletin", re.compile(r"bulletin|service note|amendment|addendum|field", re.I)),
    ("Service Manual", re.compile(r"service|repair|maintenance|troubleshoot", re.I)),
    ("Kit Manual", re.compile(r"\bkit\b|conversion|installation", re.I)),
    ("Instruction Manual", re.compile(r"instruction", re.I)),
    ("Operating Manual", re.compile(r"operat|owner", re.I)),
    ("Technical Manual", re.compile(r"technical|\btm-\d", re.I)),
    ("Document", re.compile(r"dip|pinout|pin-out|switch|settings|chart", re.I)),
    ("Manual", re.compile(r"manual", re.I)),
]


def type_of(title):
    for t, rx in TYPES:
        if rx.search(str(title or "")):
            return t
    return "Document"


def load_extra():
    if os.path.exists(EXTRA):
        return json.load(open(EXTRA))
    return {"note": "", "documents": []}


def add_documents(entries, dry_run=False):
    """Append entries to extra-docs.json. Returns (added, skipped) counts.

    An entry is skipped when its URL is already there, or when a file of the
    same name is already in the corpus catalogue — a document mirrored under
    the same name is the same document, whichever archive it came from.
    """
    data = load_extra()
    have_url = {d.get("l") for d in data["documents"]}
    have_name = {norm(re.sub(r"\.pdf$", "", d.get("f") or "", flags=re.I)) for d in data["documents"]}
    cat = os.path.join(ROOT, "web", "data", "docs.json")
    if os.path.exists(cat):
        for d in json.load(open(cat)):
            have_name.add(norm(re.sub(r"\.pdf$", "", d.get("title") or "", flags=re.I)))
    added = skipped = 0
    for e in entries:
        key = norm(re.sub(r"\.pdf$", "", e["f"], flags=re.I))
        if e["l"] in have_url or key in have_name:
            skipped += 1
            continue
        data["documents"].append(e)
        have_url.add(e["l"]); have_name.add(key)
        added += 1
    if not dry_run:
        json.dump(data, open(EXTRA, "w"), indent=1, ensure_ascii=False)
    return added, skipped
