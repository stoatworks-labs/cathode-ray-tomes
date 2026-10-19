# Exed Exes PCB

A KiCad schematic of the Exed Exes PCB, drawn for
[jtcores](https://github.com/jotego/jtcores) -- jotego's FPGA recreations of arcade hardware -- and
copied here from

    https://github.com/jotego/jtcores/tree/e7b11263b04978790d4a3b9dd7e188b2dc976e4b/cores/exed/sch

**Drawn by** etriana85, Jose Tejada (the people who committed these sheets to
jtcores). The schematic symbols are from jtkicad, by Jose Tejada.

**Licence:** GNU General Public License, version 3 -- see [LICENSE](LICENSE),
which is jtcores' own copy. jtcores and jtkicad are both published under it,
and so is everything made from these sheets.

## What is unchanged

These files are byte-for-byte copies of the upstream files at commit
`e7b11263b04978790d4a3b9dd7e188b2dc976e4b`: the sheets the root reaches, and the project settings.

- `capacitors.kicad_sch`
- `char.kicad_sch`
- `colmix.kicad_sch`
- `ds_cabinete.kicad_sch`
- `exed.kicad_pro`
- `exed.kicad_sch`
- `h_counter.kicad_sch`
- `h_scroll1.kicad_sch`
- `interruption.kicad_sch`
- `last_u.kicad_sch`
- `logics_gates.kicad_sch`
- `main.kicad_sch`
- `mux.kicad_sch`
- `mux_ot.kicad_sch`
- `obj_counters.kicad_sch`
- `obj_lut.kicad_sch`
- `obj_ram.kicad_sch`
- `object_table.kicad_sch`
- `psg.kicad_sch`
- `ram_rom.kicad_sch`
- `rom_olut.kicad_sch`
- `scroll1.kicad_sch`
- `scroll2.kicad_sch`
- `snd_c_latch.kicad_sch`
- `sound.kicad_sch`
- `v_counter.kicad_sch`
- `v_scroll.kicad_sch`
- `video.kicad_sch`
- `video_timings.kicad_sch`

Sheets in the upstream directory that the root sheet does not reach are not
copied.

## What was added here

On 2026-10-19, by `tools/import_jtcores.py` in this repository:

- `exed-exes.kicad_pcb` (and the `exed-exes.kicad_pro` KiCad writes beside it) -- a
  board view generated from this schematic's netlist by `tools/build_board.py`.
  It carries the ICs and the nets between them on a nominal layout; it is not
  the board's real layout, and jtcores has none.
- Elsewhere in the repository, derived from these sheets and under the same
  licence: `boards/exed-exes.json`, `boards/exed-exes.netlist.json`,
  `data/chips/exed-exes.json`, `data/signals/exed-exes.json` and the published copy
  under `web/boards/exed-exes/`.
