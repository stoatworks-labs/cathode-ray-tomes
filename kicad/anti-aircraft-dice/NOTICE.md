# Anti-Aircraft (DICE netlist)

The connectivity of the Anti-Aircraft (DICE netlist), from the netlist
[DICE](https://github.com/mittonk/dice-libretro) -- the Discrete Integrated Circuit Emulator -- runs it
from:

    https://github.com/mittonk/dice-libretro/blob/4b4596b8dd2252b9d08bd6aaa02afda4be834db3/games/antiaircraft.cpp

**Written by** the DICE Team, Ken Mitton (the people who committed `games/antiaircraft.cpp`
to dice-libretro).

**Licence:** GNU General Public License, version 3 -- see
[LICENSE.txt](LICENSE.txt), which is DICE's own copy. Everything made from this
netlist is published under it.

## What is unchanged

`antiaircraft.cpp` and any header it includes are byte-for-byte copies of DICE's at
commit `4b4596b8dd2252b9d08bd6aaa02afda4be834db3`.

## What was added here

On 2026-10-19, by `tools/import_dice.py` in this repository:

- `anti-aircraft-dice.kicad_pcb` (and the `anti-aircraft-dice.kicad_pro` KiCad writes beside it) -- a
  board view: the ICs DICE names, at their board positions on a nominal grid,
  with DICE's connections on their pins. DICE's stand-ins for a wire (an RC
  delay, a buffer, a clock gate, a wired-AND) are taken out so the wire is one
  net again; its models of analogue parts, inputs and outputs are left off.
- Elsewhere in the repository, derived from this netlist and under the same
  licence: `boards/anti-aircraft-dice.json`, `boards/anti-aircraft-dice.netlist.json`,
  `boards/anti-aircraft-dice.read.json`, `data/chips/anti-aircraft-dice.json`,
  `data/signals/anti-aircraft-dice.json` and the published copy under `web/boards/anti-aircraft-dice/`.
