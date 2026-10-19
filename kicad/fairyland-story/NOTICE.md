# The FairyLand Story PCB

A KiCad schematic of the The FairyLand Story PCB, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/flstory/sch/flstory

**Drawn by** Jose Tejada, Fran.R (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `amplifiers.kicad_sch`
- `capacitors_lu.kicad_sch`
- `fairyland.kicad_pro`
- `fairyland.kicad_sch`
- `io_cabinet.kicad_sch`
- `latches.kicad_sch`
- `linebuf.kicad_sch`
- `main.kicad_sch`
- `mcu.kicad_sch`
- `obj_ram.kicad_sch`
- `ongen.kicad_sch`
- `palette.kicad_sch`
- `shared.kicad_sch`
- `snd_clocks.kicad_sch`
- `sound.kicad_sch`
- `sub_main.kicad_sch`
- `tilerom.kicad_sch`
- `timing.kicad_sch`
- `video.kicad_sch`
- `vram.kicad_sch`
- `watchdog.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `fairyland-story.kicad_pcb` (and the `fairyland-story.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/fairyland-story.json`, `boards/fairyland-story.netlist.json`,
  `data/chips/fairyland-story.json`, `data/signals/fairyland-story.json` and the published copy
  under `web/boards/fairyland-story/`.
