# The Final Round PCB (GX870)

A KiCad schematic of the The Final Round PCB (GX870), drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/fround/sch

**Drawn by** Ulf Skutnabba, etriana85, Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `GFX-Fixed layer.kicad_sch`
- `GFX-Tiles.kicad_sch`
- `color_mixer.kicad_sch`
- `cpu.kicad_sch`
- `fround.kicad_pro`
- `fround.kicad_sch`
- `io.kicad_sch`
- `sound.kicad_sch`
- `sprite_timing_diagrams.kicad_sch`
- `sprites1.kicad_sch`
- `sprites2.kicad_sch`
- `timing.kicad_sch`
- `timing_diagrams.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `final-round-gx870.kicad_pcb` (and the `final-round-gx870.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/final-round-gx870.json`, `boards/final-round-gx870.netlist.json`,
  `data/chips/final-round-gx870.json`, `data/signals/final-round-gx870.json` and the published copy
  under `web/boards/final-round-gx870/`.
