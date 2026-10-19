# Capcom Bowling PCB

A KiCad schematic of the Capcom Bowling PCB, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/capbowl/sch

**Drawn by** Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `bowl.kicad_pro`
- `bowl.kicad_sch`
- `main.kicad_sch`
- `memories.kicad_sch`
- `sound.kicad_sch`
- `video.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `capcom-bowling.kicad_pcb` (and the `capcom-bowling.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/capcom-bowling.json`, `boards/capcom-bowling.netlist.json`,
  `data/chips/capcom-bowling.json`, `data/signals/capcom-bowling.json` and the published copy
  under `web/boards/capcom-bowling/`.
