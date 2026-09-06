#!/usr/bin/env python3
"""Recover illustrated-parts-list BOMs from digitised manuals.

Service manuals carry their own bill of materials: an item number, a
manufacturer part number and a description, repeated down the page. OCR
flattens the column whitespace, so the rows are recovered from the shape of the
data rather than its layout — part numbers are distinctive enough to anchor
each record and split the run.

Covers the numbering styles seen across this corpus:
    A035053-01   035047-01   160001-001   92-047   A021084.04   72-00049-001
    75-010S      72-1810S    75-5124B                (Bally/Midway, revision suffix)

Quantity is its own column in most of these manuals but not all, and it is the
page's own header that says which — see QTY_COL below.
"""
import argparse, glob, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A trailing letter is a revision suffix, and Bally/Midway use them heavily:
# 75-010S, 72-1810S, 75-5124B. Without it the pattern does not recognise the
# *next* record's part number, the lookahead below never fires, and the two
# rows are emitted as one — 199 such tokens were sitting inside descriptions.
# It has to sit tight against the digits: a space before it and it would eat
# the first word of a description instead.
PN = r"[A-Z]{0,2}\d{2,6}(?:[-.]\d{2,4}){1,2}[A-Z]?"
PART = re.compile(rf"\b({PN})\b")
# a record starts at an item number immediately followed by a part number
RECORD = re.compile(
    rf"(?<!\d)(\d{{1,3}}[A-Z]?)\s+({PN})\s+(.{{3,90}}?)"
    rf"(?=\s+\d{{1,3}}[A-Z]?\s+{PN}\s|$)")
HEADER = re.compile(r"item\s+part\s*(no|number)", re.I)
LIST_PAGE = re.compile(r"parts\s+list|illustrated\s+parts", re.I)

# The column header, read for what sits between the part number and the
# description. Separate from HEADER, which only says where the body starts.
COLUMNS = re.compile(
    r"(?:item|no\.?)\s*[.|_]?\s*part[\s_]*(?:number|no\.?)?\.?"
    r"(?P<mid>.{0,60}?)descript\w*", re.I)
# "Qty.", "QTY REQD", "Qty. Req'd", "Quantity", and the OCR of each. Measured
# over the corpus: 346 of 621 header occurrences name a quantity column and
# 183 have nothing at all between PART NO. and DESCRIPTION (the Sega manuals).
QTY_COL = re.compile(r"\b(qty|oty|qtv|aty|q'?ty|quan\w*|ty)\b|req'?d", re.I)
# What that column holds. "A/R" is as-required and "Ref" is reference-only;
# both are real values in Atari's lists, not descriptions.
QTY_VALUE = re.compile(r"^(\d{1,3}|A\s*/\s*R|AR|Ref)\s*\|?\s+(?=\S)", re.I)
# For infer_qty_column only: a leading number in front of a word.
QTY_LEAD = re.compile(r"^(\d{1,3})\s+[A-Za-z]")
QTY_MAX = 20            # a quantity; above this it reads as a component value
INFER_SHARE = 0.90      # of the leading numbers, at or under it
INFER_MIN_ROWS = 5      # fewer than this is not evidence of anything
# An item number never carries a unit. `50V`, `4W`, `2K` are a component's
# rating read out of an electrical parts list, where the value column sits
# where the item number does in an illustrated one; `1A`, `1D`, `1E` are real
# item numbers and are kept.
ITEM_IS_UNIT = re.compile(r"^\d{1,3}[VWK]$", re.I)
# A description has a word in it. What is left when it does not is the next
# row's data, dragged in because this page's columns OCR'd as separate runs —
# the item and part number are still right, so the row is kept without it.
HAS_WORD = re.compile(r"[A-Za-z]{3,}")

def page_text(page):
    return " ".join(b["t"] for b in page.get("blocks", [])) or page.get("text", "")

def has_qty_column(doc):
    """True/False from this document's own headers, or None if it has none.

    The default for a continuation page that carries no header of its own. A
    multi-page list prints its header once, and the running-header filter can
    remove it from the pages that do repeat it.
    """
    seen = None
    for page in doc.get("pages", []):
        m = COLUMNS.search(page_text(page))
        if m:
            if QTY_COL.search(m.group("mid")):
                return True
            seen = False
    return seen


def infer_qty_column(descs):
    """Last resort, for a document whose header was never recognised.

    Only ever consulted when the manual says nothing — a header that names the
    columns always wins, in either direction. What is left to go on is the
    shape of the numbers: a quantity is small and repetitive, a component value
    is not, so `1 Speaker Cover` and `680 uf` separate on magnitude. Measured
    over the corpus, eleven of the twelve header-less documents have every
    leading number at or under 20 and the twelfth has half, which is where the
    bar sits.
    """
    nums = [int(m.group(1)) for d in descs if (m := QTY_LEAD.match(d))]
    if len(nums) < INFER_MIN_ROWS:
        return False
    return sum(1 for n in nums if n <= QTY_MAX) / len(nums) >= INFER_SHARE


def split_qty(desc, qty_col):
    """(qty, desc) — take the quantity off the front where there is one.

    Only on a page whose header says the column exists. Measured over the
    corpus: where it does, 94% of descriptions start with a number; where it
    does not, 22% do, and those digits are the description ("2 Player
    Harness", "8 Ohm Speaker"). Splitting unconditionally would eat them.
    """
    if not qty_col:
        return None, desc
    m = QTY_VALUE.match(desc)
    if not m:
        return None, desc
    return m.group(1).replace(" ", ""), desc[m.end():].strip()


def from_document(doc):
    """Return [{page, item, part, qty?, desc}] for every parts-list row found."""
    rows = []
    qty_col = has_qty_column(doc)
    # No header anywhere in the document. Parse without splitting anything, and
    # judge from what comes out — see infer_qty_column.
    inferring = qty_col is None
    if inferring:
        qty_col = False
    for page in doc.get("pages", []):
        txt = page_text(page)
        # Gate on the page's own shape as well as its header: running-header
        # suppression can remove the "Item Part No." line that used to be the
        # only anchor, silently dropping otherwise perfectly readable tables.
        if not (HEADER.search(txt) or LIST_PAGE.search(txt)
                or len(RECORD.findall(txt)) >= 5):
            continue
        # A page that prints its own header overrides the document default: a
        # manual can carry an illustrated parts list with a quantity column and
        # an electrical one without.
        cols = COLUMNS.search(txt)
        if cols:
            qty_col = bool(QTY_COL.search(cols.group("mid")))

        # start after the column header where there is one; it prevents the
        # header itself being parsed as a row
        m = HEADER.search(txt)
        body = txt[m.end():] if m else txt
        for r in RECORD.finditer(body):
            item, part, desc = r.group(1), r.group(2), r.group(3).strip(" .-—")
            # Clear the field that is wrong, never the row. An electrical parts
            # list prints its rating where an illustrated one prints an item
            # number, so `4W` here is a ¼W resistor on a row whose part number
            # and description are both good — Xybots has 31 of them.
            if ITEM_IS_UNIT.match(item):
                item = ""
            qty, desc = split_qty(desc, qty_col)
            desc = desc.strip(" .-—|")
            # Same principle for the description. Where a page's columns OCR'd
            # as separate runs the description that lands here is the *next*
            # row's item and part number — Pepper II's `2 D90-0002-00`, Star
            # Trek's `4 4`. The item and part on this row are still correctly
            # paired, and that pairing is what someone orders from, so the row
            # stays and the description goes.
            if not HAS_WORD.search(desc):
                desc = ""
            # What is left has to identify something: a part number alone,
            # with neither an item number nor a description, is not a row.
            if not desc and not item:
                continue
            row = {"page": page["n"], "item": item, "part": part, "desc": desc}
            if qty is not None:
                row["qty"] = qty
            rows.append(row)

    if inferring and infer_qty_column([r["desc"] for r in rows]):
        for r in rows:
            qty, desc = split_qty(r["desc"], True)
            if qty is not None:
                r["qty"], r["desc"] = qty, desc.strip(" .-—|")
    return rows

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", help="single document id")
    ap.add_argument("--all", action="store_true", help="scan the whole corpus")
    ap.add_argument("--min-rows", type=int, default=5)
    ap.add_argument("--out", help="write JSON here")
    a = ap.parse_args()

    cat = {d["id"]: d for d in json.load(open(os.path.join(ROOT, "data/index/docs.json")))}
    ids = [a.doc] if a.doc else [os.path.basename(p)[:-5]
                                 for p in glob.glob(os.path.join(ROOT, "cache/text/*.json"))]

    found, total = {}, 0
    for did in ids:
        fp = os.path.join(ROOT, "cache", "text", did + ".json")
        if not os.path.exists(fp):
            continue
        try:
            doc = json.load(open(fp))
        except Exception:
            continue
        rows = from_document(doc)
        if len(rows) >= a.min_rows:
            found[did] = rows
            total += len(rows)
            if a.doc or not a.all:
                meta = cat.get(did, {})
                print(f"{meta.get('machineName','?')} — {meta.get('title','?')}")
                print(f"  {len(rows)} parts across "
                      f"{len(set(r['page'] for r in rows))} pages")
                for r in rows[:12]:
                    print(f"    p{r['page']:>3} {r['item']:>4}  {r['part']:<14} {r['desc'][:52]}")

    if a.all:
        print(f"{len(found)} documents carry a usable parts list, {total} rows total")
        top = sorted(found.items(), key=lambda kv: -len(kv[1]))[:10]
        for did, rows in top:
            m = cat.get(did, {})
            print(f"  {len(rows):>4} rows  {m.get('machineName','?')[:30]:32} {m.get('title','?')[:44]}")

    if a.out:
        json.dump({k: v for k, v in found.items()}, open(a.out, "w"), indent=1)
        print(f"-> {a.out}")

if __name__ == "__main__":
    main()
