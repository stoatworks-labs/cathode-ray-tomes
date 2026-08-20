#!/usr/bin/env python3
"""Recover illustrated-parts-list BOMs from digitised manuals.

Service manuals carry their own bill of materials: an item number, a
manufacturer part number and a description, repeated down the page. OCR
flattens the column whitespace, so the rows are recovered from the shape of the
data rather than its layout — part numbers are distinctive enough to anchor
each record and split the run.

Covers the numbering styles seen across this corpus:
    A035053-01   035047-01   160001-001   92-047   A021084.04   72-00049-001
"""
import argparse, glob, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PART = re.compile(r"\b([A-Z]{0,2}\d{2,6}(?:[-.]\d{2,4}){1,2})\b")
# a record starts at an item number immediately followed by a part number
RECORD = re.compile(
    r"(?<!\d)(\d{1,3}[A-Z]?)\s+([A-Z]{0,2}\d{2,6}(?:[-.]\d{2,4}){1,2})\s+(.{3,90}?)"
    r"(?=\s+\d{1,3}[A-Z]?\s+[A-Z]{0,2}\d{2,6}(?:[-.]\d{2,4}){1,2}\s|$)")
HEADER = re.compile(r"item\s+part\s*(no|number)", re.I)
LIST_PAGE = re.compile(r"parts\s+list|illustrated\s+parts", re.I)

def page_text(page):
    return " ".join(b["t"] for b in page.get("blocks", [])) or page.get("text", "")

def from_document(doc):
    """Return [{page, item, part, desc}] for every parts-list row found."""
    rows = []
    for page in doc.get("pages", []):
        txt = page_text(page)
        # Gate on the page's own shape as well as its header: running-header
        # suppression can remove the "Item Part No." line that used to be the
        # only anchor, silently dropping otherwise perfectly readable tables.
        if not (HEADER.search(txt) or LIST_PAGE.search(txt)
                or len(RECORD.findall(txt)) >= 5):
            continue
        # start after the column header where there is one; it prevents the
        # header itself being parsed as a row
        m = HEADER.search(txt)
        body = txt[m.end():] if m else txt
        for r in RECORD.finditer(body):
            item, part, desc = r.group(1), r.group(2), r.group(3).strip(" .-—")
            if len(desc) < 3:
                continue
            rows.append({"page": page["n"], "item": item, "part": part, "desc": desc})
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
