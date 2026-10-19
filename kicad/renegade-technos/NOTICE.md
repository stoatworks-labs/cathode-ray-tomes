# Renegade PCB

A KiCad schematic of the Renegade PCB, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/kunio/sch

**Drawn by** etriana85, Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `capacitors.kicad_sch`
- `characters.kicad_sch`
- `colmix.kicad_sch`
- `counters.kicad_sch`
- `double_line_buffer.kicad_sch`
- `io.kicad_sch`
- `kunio.kicad_pro`
- `kunio.kicad_sch`
- `last unit.kicad_sch`
- `main.kicad_sch`
- `memories_sprite.kicad_sch`
- `obj_draw.kicad_sch`
- `obj_lut_buf.kicad_sch`
- `objects.kicad_sch`
- `scroll.kicad_sch`
- `scrom_memories.kicad_sch`
- `sound.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `renegade-technos.kicad_pcb` (and the `renegade-technos.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/renegade-technos.json`, `boards/renegade-technos.netlist.json`,
  `data/chips/renegade-technos.json`, `data/signals/renegade-technos.json` and the published copy
  under `web/boards/renegade-technos/`.
