# Caliber 50 PCB (P0-044B)

A KiCad schematic of the Caliber 50 PCB (P0-044B), drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/cal50/sch

**Drawn by** Ulf Skutnabba (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `cal50.kicad_pro`
- `cal50.kicad_sch`
- `color_mixer.kicad_sch`
- `cpu.kicad_sch`
- `graphics_1.kicad_sch`
- `graphics_2.kicad_sch`
- `io.kicad_sch`
- `misc.kicad_sch`
- `sound.kicad_sch`
- `sound_output.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `caliber-50-p0-044b.kicad_pcb` (and the `caliber-50-p0-044b.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/caliber-50-p0-044b.json`, `boards/caliber-50-p0-044b.netlist.json`,
  `data/chips/caliber-50-p0-044b.json`, `data/signals/caliber-50-p0-044b.json` and the published copy
  under `web/boards/caliber-50-p0-044b/`.
