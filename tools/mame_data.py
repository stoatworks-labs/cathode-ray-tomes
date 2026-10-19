"""MAME's own account of a machine, for the machine page.

data/mame/machines.json is written by tools/import_mame.py from the XML MAME
publishes with each release. build_index.py and build_assets.py --mame-only
both put it on the machine's detail record through `apply`, so a full rebuild
and a targeted one produce the same page.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "data", "mame", "machines.json")

_cache = None


def load():
    global _cache
    if _cache is None:
        _cache = json.load(open(PATH)) if os.path.exists(PATH) else {"machines": {}}
    return _cache


def _mhz(hz):
    return {"mhz": round(hz / 1e6, 2)} if hz >= 1e6 else ({"khz": round(hz / 1e3, 2)} if hz else {})


def apply(detail, rom_to_slug=None):
    """Add the MAME block to one detail record, in place. Returns True if it changed.

    The block is `mame`: {v, src?, parent?, parentSlug?, roms?, disks?}.
    `parentSlug` is set only when the parent set is itself a machine on the
    site (rom_to_slug maps romset to slug), so the page never links to nothing.
    Where the upstream metadata has no CPU at all, MAME's chip list fills `cpu`
    and `audio`, so a page never says "CPU: —" about a machine MAME can describe.
    """
    data = load()
    rec = data["machines"].get(detail.get("rom") or "")
    if rec is None:
        return False
    block = {"v": data.get("version")}
    for k in ("src", "parent", "roms", "disks"):
        if rec.get(k):
            block[k] = rec[k]
    if rec.get("parent") and rom_to_slug and rec["parent"] in rom_to_slug:
        block["parentSlug"] = rom_to_slug[rec["parent"]]
    before = json.dumps(detail, sort_keys=True)
    detail["mame"] = block
    if not detail.get("cpu") and rec.get("chips"):
        detail["cpu"] = [dict(n=c["n"], **_mhz(c.get("hz", 0))) for c in rec["chips"] if c["t"] == "cpu"]
        if not detail.get("audio"):
            detail["audio"] = [dict(n=c["n"], **_mhz(c.get("hz", 0))) for c in rec["chips"] if c["t"] == "audio"]
    return json.dumps(detail, sort_keys=True) != before
