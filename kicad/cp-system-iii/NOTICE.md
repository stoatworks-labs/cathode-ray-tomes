# CP System III

A KiCad schematic of the CP System III, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/cps3/sch

**Drawn by** etriana85, Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `buffer_line_driver.kicad_sch`
- `capacitors_uu.kicad_sch`
- `cassette.kicad_sch`
- `ccu.kicad_sch`
- `cps3.kicad_pro`
- `cps3.kicad_sch`
- `h_description.kicad_sch`
- `iou.kicad_sch`
- `memories_fb.kicad_sch`
- `memories_scu.kicad_sch`
- `objects.kicad_sch`
- `ppu.kicad_sch`
- `scroll.kicad_sch`
- `simm.kicad_sch`
- `simm_connector.kicad_sch`
- `simms.kicad_sch`
- `simms_2~1_snd.kicad_sch`
- `slots_females.kicad_sch`
- `sound.kicad_sch`
- `ssu.kicad_sch`
- `video_dac.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `cp-system-iii.kicad_pcb` (and the `cp-system-iii.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/cp-system-iii.json`, `boards/cp-system-iii.netlist.json`,
  `data/chips/cp-system-iii.json`, `data/signals/cp-system-iii.json` and the published copy
  under `web/boards/cp-system-iii/`.
