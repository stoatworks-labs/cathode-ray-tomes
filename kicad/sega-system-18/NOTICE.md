# Sega System 18

A KiCad schematic of the Sega System 18, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/s18/sch

**Drawn by** Jose Tejada, etriana85, rp-jt (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `amplifier.kicad_sch`
- `audio_amplifier.kicad_sch`
- `blanking.kicad_sch`
- `buffers.kicad_sch`
- `capacitors.kicad_sch`
- `colmix.kicad_sch`
- `comm_snd.kicad_sch`
- `cpurom.kicad_sch`
- `gfx_obj.kicad_sch`
- `gfx_scr.kicad_sch`
- `i_o controller.kicad_sch`
- `io_cabinet.kicad_sch`
- `main.kicad_sch`
- `memorymapper.kicad_sch`
- `objrom.kicad_sch`
- `romboard.kicad_sch`
- `romjp.kicad_sch`
- `romjp7.kicad_sch`
- `s18.kicad_pro`
- `s18.kicad_sch`
- `scrrom.kicad_sch`
- `sound_a.kicad_sch`
- `spriteram.kicad_sch`
- `tilemapg_ram.kicad_sch`
- `top _connectors.kicad_sch`
- `vdp.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `sega-system-18.kicad_pcb` (and the `sega-system-18.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/sega-system-18.json`, `boards/sega-system-18.netlist.json`,
  `data/chips/sega-system-18.json`, `data/signals/sega-system-18.json` and the published copy
  under `web/boards/sega-system-18/`.
