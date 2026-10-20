# Capcom DL-020F-108U

A KiCad schematic of the inside of the Capcom DL-020F-108U, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/pang/sch/dl-020f-108

**Drawn by** Ulf Skutnabba (the people who committed these sheets to
jtcores), from a die photo by Furrtek, as the drawing says. The
schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `dl-020f-108.kicad_pro`
- `dl-020f-108.kicad_sch`

## What was added here

Nothing in this directory but this notice and the licence. On 2026-10-20, by
`tools/import_custom_chips.py` in this repository, and under the same licence:

- `data/customchips/dl-020f-108u.json` -- the chip's pinout, read off the symbol in
  these sheets; how many cells the drawing uses and from which libraries; the
  drawing's own notes on what the chip does and what silicon it was read from;
  and how the pinout compares with the board drawings on this site that carry
  the part.
- `web/chips/dl-020f-108u.pdf` -- every sheet, as KiCad plots it.
- `web/data/customchip/dl-020f-108u.json` -- all of that, with the boards, machines
  and MAME PCB layouts on this site that carry the chip, as the page reads it.
