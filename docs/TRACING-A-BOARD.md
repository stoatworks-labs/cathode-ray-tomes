# Tracing a board: the brief and the recipe

The two documents the Tempest Auxiliary PCB was traced and redrawn from, generalised. AGENTS.md
has the pipeline and the traps; this is what to hand a reader or a drawer so they can do one
part of the job without the rest of the context. Both were used as written: four readers read
Tempest's sheet at once from the first, eight drawers drew its eleven KiCad sheets at once
from the second.

## 1. Reading one region of a sheet

Render the sheet first, into `cache/sheets/<board>/` (never `/tmp`): 300 dpi tiles of 1450 px
overlapping by 150, so tile `rRcC` has its corner at `x = 1300*C`, `y = 1300*R` in 300 dpi
sheet pixels (clamp the last row and column to the edge). Readers render their own 600 dpi
crops for dense spots, `pdftoppm -r 600 -x <2X> -y <2Y> -W <w> -H <h>` -- `-r 600` as two
arguments. Split the sheet by its own titled boxes: Atari names nearly every signal that
crosses a box edge, so the parts join by name.

What each reader is told:

- **Source.** Which printing is primary and which are cross-checks. Prefer a colour printing
  if there is one: its signature annotations are blue and can never be mistaken for wire.
  Where a band hides a line, read that spot on another printing.
- **The legend, from the sheet.** Square = edge connector, hexagon = interconnect, circle =
  SA header, flag = test point -- but read the sheet's own legend box, which names the
  connectors (Tempest: J18, J17, J16). `P,R54` at a pin means pulled up through R54: write
  the pin on `R54.1`; `R54.2` goes on +5V where R54 is drawn.
- **The DSL** (`boards/battlezone-math-box.nets` is the style reference): `net NAME:` for a
  printed name, `wire` for an unnamed join, `nc`, `label` for a name of ours, `sig PIN CODE
  [TEST]`, `value REF VALUE`, `parallel PIN ...` for outputs tied on purpose. ICs are `U` +
  the grid position as printed (`UK/L2`); passives as printed. Overbar = leading `/`. Diode
  pin 1 is the cathode, electrolytic pin 1 is +.
- **Rules.** A dot joins, a crossing does not. Read every IC pin by pin: each must end up on
  a net or in `nc` -- the checker reports a pin never mentioned, and a missed pin looks
  exactly like an unused one. Record power pins only where drawn. Unnamed wires leaving the
  region become `label X<region><n>:` with the sheet coordinate where they cross the edge.
  Part types as comments: `# part UB4 74LS139`. Anything uncertain gets an `# Uncertain:`
  line saying what was checked.
- **Hand back** the region file plus a short report: parts, the named nets used (so spellings
  can be reconciled), exits, uncertainties, where printings disagree, and two to four facts
  a repairer would want.

Then merge, and argue with the result: `tools/build_board_nets.py <slug>` to 0 problems; the
parts list's passives and IC positions against the read (every value); and, where another
board carries the same circuit, its traced netlist mapped onto this board's positions.

## 2. Drawing one KiCad sheet

`tools/plan_board_schematic.py <slug> --ops` writes `kicad/<slug>/plan/<key>.ops.json`: the
placements, and every label, power symbol and no-connect at an explicit coordinate. The
sheet's `.kicad_sch` must already exist and be linked into the root (Konnect's
`add_hierarchical_sheet`). The drawer then, through Konnect only:

1. `batch_place_components` with `ops.place` as given (Konnect snaps to 1.27 mm; the
   coordinates already assume it).
2. One `batch_connect_to_net` per entry of `ops.local` -- the power rails are in there too.
3. `add_power_symbol` for each `ops.power_symbols` entry.
4. `add_schematic_net_label` with `label_type` global_label, `shape` bidirectional, for every
   entry of `ops.global`, with the rotation given.
5. `add_no_connect` for each `ops.nc` entry.
6. Prove it: the counts of `(global_label`, `(no_connect` and `(label ` in the file match the
   ops file, and `tools/check_board_sheets.py <slug> <key>` reports 0 disagreements.

Never edit a `.kicad_*` file as text, touch only your own sheet, and run no git. Calls to one
file may go in parallel: Konnect serialises them. When every sheet is in,
`tools/check_board_schematic.py <slug>` proves the whole schematic and ERC runs on the root.
