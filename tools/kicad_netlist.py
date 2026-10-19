#!/usr/bin/env python3
"""Read a KiCad schematic's netlist, as kicad-cli exports it.

KiCad 10 writes the netlist as an s-expression spread over many lines, one
field to a line, so it cannot be scraped with a regex the way the old one-line
format could. This is a small reader for the parts of it the board pipeline
uses: the components, the symbols they come from, and the nets.

    comps, libparts, nets = read(export(sch))
"""
import os, re, subprocess, tempfile

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"

_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    """The s-expression as nested lists of strings."""
    stack, cur, pos = [], [], 0
    while pos < len(text):
        m = _TOK.match(text, pos)
        if not m:
            if not text[pos:].strip():
                break
            raise ValueError(f"unreadable s-expression at offset {pos}")
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done, cur = cur, stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(m.group(3).replace('\\"', '"').replace("\\\\", "\\"))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def find(node, key):
    for c in node or []:
        if isinstance(c, list) and c and c[0] == key:
            yield c


def first(node, key):
    return next(find(node, key), None)


def val(node, key, default=None):
    c = first(node, key)
    return c[1] if c is not None and len(c) > 1 else default


def export(sch, out=None):
    """Export the netlist of a root sheet with kicad-cli; returns its text."""
    with tempfile.TemporaryDirectory() as t:
        path = out or os.path.join(t, "board.net")
        r = subprocess.run([KICAD_CLI, "sch", "export", "netlist", "-o", path, sch],
                           capture_output=True, text=True)
        if not os.path.exists(path):
            raise RuntimeError(f"kicad-cli could not export {sch}: {r.stderr[-400:]}")
        return open(path, errors="replace").read()


def read(text):
    """(components, libparts, nets) from a netlist's text.

    components  {ref: {value, footprint, lib, part, description, sheet}}
    libparts    {(lib, part): {description, pins: [(num, name, type)]}}
    nets        [{name, nodes: [(ref, pin, pinfunction, pintype)]}]
    """
    root = parse(text)
    comps = {}
    for c in find(first(root, "components"), "comp"):
        lib = first(c, "libsource")
        sheet = first(c, "sheetpath")
        comps[val(c, "ref")] = {
            "value": val(c, "value", ""),
            "footprint": val(c, "footprint", ""),
            "lib": val(lib, "lib") if lib else None,
            "part": val(lib, "part") if lib else None,
            "description": val(c, "description") or (val(lib, "description") if lib else "") or "",
            "sheet": val(sheet, "names", "/") if sheet else "/",
        }
    libparts = {}
    for lp in find(first(root, "libparts"), "libpart"):
        pins = [(val(p, "num"), val(p, "name"), val(p, "type"))
                for p in find(first(lp, "pins"), "pin")]
        libparts[(val(lp, "lib"), val(lp, "part"))] = {
            "description": val(lp, "description", "") or "", "pins": pins}
    nets = []
    for n in find(first(root, "nets"), "net"):
        nodes = [(val(x, "ref"), val(x, "pin"), val(x, "pinfunction"), val(x, "pintype"))
                 for x in find(n, "node")]
        nets.append({"name": val(n, "name"), "nodes": nodes})
    return comps, libparts, nets
