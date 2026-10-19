# Gradius III PCB (GX945)

A KiCad schematic of the Gradius III PCB (GX945), drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/grad3/sch/grad3

**Drawn by** Ulf Skutnabba, RafaP (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `color_mixer.kicad_sch`
- `cpu_master.kicad_sch`
- `cpu_slave.kicad_sch`
- `grad3.kicad_pro`
- `grad3.kicad_sch`
- `io.kicad_sch`
- `misc.kicad_sch`
- `object_layer.kicad_sch`
- `pcm.kicad_sch`
- `shram.kicad_sch`
- `sound.kicad_sch`
- `tile_layers.kicad_sch`
- `tile_logic.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `gradius-iii-gx945.kicad_pcb` (and the `gradius-iii-gx945.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/gradius-iii-gx945.json`, `boards/gradius-iii-gx945.netlist.json`,
  `data/chips/gradius-iii-gx945.json`, `data/signals/gradius-iii-gx945.json` and the published copy
  under `web/boards/gradius-iii-gx945/`.
