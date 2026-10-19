# WWF Superstars PCB

A KiCad schematic of the WWF Superstars PCB, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/wwfss/sch

**Drawn by** Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `analog.kicad_sch`
- `bottom.kicad_sch`
- `char.kicad_sch`
- `chpixel.kicad_sch`
- `colmix.kicad_sch`
- `dual_line_buffer.kicad_sch`
- `io.kicad_sch`
- `line_buffer.kicad_sch`
- `main.kicad_sch`
- `object.kicad_sch`
- `objram.kicad_sch`
- `objrom.kicad_sch`
- `scroll.kicad_sch`
- `scrram.kicad_sch`
- `scrrom.kicad_sch`
- `sound.kicad_sch`
- `timing.kicad_sch`
- `top.kicad_sch`
- `wwfsstar.kicad_pro`
- `wwfsstar.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `wwf-superstars.kicad_pcb` (and the `wwf-superstars.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/wwf-superstars.json`, `boards/wwf-superstars.netlist.json`,
  `data/chips/wwf-superstars.json`, `data/signals/wwf-superstars.json` and the published copy
  under `web/boards/wwf-superstars/`.
