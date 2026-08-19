#!/usr/bin/env python3
"""Build the search artefacts served by the Worker.

  data/index/postings.json  token -> [[docId, hitCount], ...]   (OCR full text)
  data/index/chips.json     chip name -> [machine slugs]        (MAME metadata)

OCR of 1970s-80s scans is noisy, so tokens are filtered hard: they must look
like words or part numbers, and terms appearing in a large fraction of the
corpus carry no signal and are dropped.
"""
import json, os, re, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "cache", "text")
OUT = os.path.join(ROOT, "data", "index")

# A token is a word of 3+ letters, or a part-number-ish alphanumeric run.
TOKEN = re.compile(r"[a-z]{3,}|[a-z]{0,3}\d{2,}[a-z0-9]*")
MAX_POSTINGS = 400          # cap per term; the long tail is not useful
# Only terms that are in almost every document carry no signal. Filtering more
# aggressively than this breaks ordinary queries -- "voltage selection" and
# "self test" are exactly what people search service manuals for.
MAX_DF_RATIO = 0.92

def shard_of(token):
    """Postings are sharded by leading character so the Worker fetches only
    what a query needs, and no single KV value approaches the 25 MB limit."""
    c = token[0]
    return c if c.isalnum() else "_"

def build_postings():
    files = sorted(glob.glob(os.path.join(CACHE, "*.json")))
    if not files:
        print("no OCR text yet — skipping postings")
        return 0
    post = collections.defaultdict(collections.Counter)
    for fp in files:
        did = os.path.basename(fp)[:-5]
        try:
            doc = json.load(open(fp))
        except Exception:
            continue
        for page in doc.get("pages", []):
            body = page.get("text") or " ".join(b["t"] for b in page.get("blocks", []))
            for tok in TOKEN.findall(body.lower()):
                post[tok][did] += 1

    n = len(files)
    shards = collections.defaultdict(dict)
    kept = 0
    for tok, counts in post.items():
        if len(counts) > n * MAX_DF_RATIO and len(counts) > 8:
            continue
        shards[shard_of(tok)][tok] = [[d, c] for d, c in counts.most_common(MAX_POSTINGS)]
        kept += 1

    sdir = os.path.join(OUT, "postings")
    os.makedirs(sdir, exist_ok=True)
    for old in glob.glob(os.path.join(sdir, "*.json")):
        os.remove(old)
    total = 0
    for name, data in shards.items():
        fp = os.path.join(sdir, f"{name}.json")
        json.dump(data, open(fp, "w"), separators=(",", ":"))
        total += os.path.getsize(fp)
    biggest = max(((os.path.getsize(os.path.join(sdir, f"{k}.json")), k) for k in shards),
                  default=(0, "-"))
    print(f"postings: {kept} terms over {n} documents in {len(shards)} shards "
          f"({total/1e6:.1f} MB total, largest '{biggest[1]}' {biggest[0]/1e6:.1f} MB)")
    return kept

def build_chips():
    machines = json.load(open(os.path.join(ROOT, "data", "machines.raw.json")))
    idx = collections.defaultdict(list)
    seen = set()
    for m in machines:
        slug = m.get("id") or ""
        if not slug or slug in seen:
            continue
        seen.add(slug)
        parts = {c.get("n") for c in (m.get("cpu") or []) if c.get("n")}
        parts |= {a.get("n") for a in (m.get("aud") or []) if a.get("n")}
        for p in parts:
            idx[p.lower()].append(slug)
    idx = {k: v[:300] for k, v in idx.items()}
    json.dump(idx, open(os.path.join(OUT, "chips.json"), "w"), separators=(",", ":"))
    print(f"chips: {len(idx)} distinct devices")

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    build_chips()
    build_postings()
