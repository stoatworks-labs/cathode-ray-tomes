#!/usr/bin/env python3
"""Record which source documents cannot be fetched or read.

Outputs: data/link-health.json

`/pdf/<id>` is a 302 to the upstream file — the scans are not mirrored — so a
document whose source has gone is a dead link on this site, and the reader has
no way to know until it 404s in a new tab. Sixteen of them do:

  12  HTTP 404 — arcadertfm's own catalogue still lists them, and its file
      server no longer has them. Verified again months after the ingest first
      failed, so this is not a transient. Every one happens to end `.PDF`;
      lowercasing the extension recovers none of them, so it is not a case
      problem, just a batch that went away.
   4  fetched fine and are not readable PDFs. The link works and the document
      will never render, which is the more confusing of the two.

The ingest already knows all this — it records why each document failed in
data/ingest-state.json and does not retry a 404 — so the default run costs
nothing and asks the network only to confirm what it found. That matters:
arcadertfm rate-limits, and four concurrent workers tripped it inside 250
requests while writing this, which briefly took its main site down to 429s.
Reading at human speed does not. Hence serial, with a delay, and `--all` off by
default.
"""
import argparse, json, os, time, urllib.error, urllib.parse, urllib.request

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "ingest-state.json")
DOCS  = os.path.join(ROOT, "data", "index", "docs.json")
OUT   = os.path.join(ROOT, "data", "link-health.json")
UA    = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/126 Safari/537.36")
DELAY = 2.0


def head(url, timeout=45):
    """HEAD the source. Upstream URLs carry raw spaces, so quote the path."""
    p = urllib.parse.urlsplit(url)
    safe = urllib.parse.urlunsplit(
        (p.scheme, p.netloc, urllib.parse.quote(p.path), p.query, p.fragment))
    try:
        req = urllib.request.Request(safe, method="HEAD", headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true",
                    help="check every document, not just the ones ingest failed "
                         "on. Serial and slow by design; hours, not minutes.")
    ap.add_argument("--offline", action="store_true",
                    help="trust the ingest state; make no requests at all")
    a = ap.parse_args()

    docs = {d["id"]: d for d in json.load(open(DOCS))}
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"failed": {}}
    failed = state.get("failed", {})

    suspect = list(docs) if a.all else list(failed)
    print(f"{len(suspect)} document(s) to check"
          + ("" if a.offline else f", serially at {DELAY}s apart"))

    out = {}
    for i, did in enumerate(suspect, 1):
        d = docs.get(did)
        if not d or not d.get("src"):
            continue
        why = failed.get(did, "")
        if a.offline:
            status = 404 if "404" in why else (200 if why else None)
        else:
            status = head(d["src"])
            time.sleep(DELAY)
            if i % 50 == 0:
                print(f"  {i}/{len(suspect)}", flush=True)

        if status == 200 and "unreadable" in why:
            out[did] = {"state": "unreadable", "status": 200,
                        "note": "the file is there and is not a readable PDF"}
        elif status is not None and status != 200:
            out[did] = {"state": "gone", "status": status,
                        "note": "the source archive no longer has this file"}

    payload = {
        "checked": time.strftime("%Y-%m-%d"),
        "scope": "all documents" if a.all else "documents the ingest failed on",
        "documents": dict(sorted(out.items())),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(payload, open(OUT, "w"), indent=1)

    gone = sum(1 for v in out.values() if v["state"] == "gone")
    bad  = sum(1 for v in out.values() if v["state"] == "unreadable")
    print(f"\n{gone} gone, {bad} unreadable -> {os.path.relpath(OUT, ROOT)}")
    for did, v in sorted(out.items(), key=lambda kv: kv[1]["state"]):
        print(f"  {v['state']:<11} {v['status']:>4}  "
              f"{docs[did].get('machineName','?')[:24]:<24} "
              f"{docs[did].get('title','')[:44]}")


if __name__ == "__main__":
    main()
