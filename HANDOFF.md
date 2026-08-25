# Cathode Ray Tomes — session handoff

**Live:** https://cathode-ray-tomes.com (also `cathode-ray-tomes.allan-sargeant.workers.dev`)
**Repo:** github.com/stoatworks-labs/cathode-ray-tomes (public)
**Local:** `~/Projects/publishing/cathode-ray-tomes`

Read `AGENTS.md` first — it holds the traps. This file is orientation and open work.

## What it is

Arcade service manuals rebuilt as searchable web documents, **for troubleshooting a
board in front of you, not for reproducing one**. That framing decides everything: a
partial complement that gets you to the right chip beats a complete one that is wrong
about your board revision.

## State

| | |
|---|---|
| Machines | 7,812 |
| Documents digitised | 2,389 of 2,405 (100% block structure) |
| Pages OCR'd | 62,784 · 44,668 sections |
| Board maps | 14, across 10 machines |
| Signal indexes | 136 machines, 13,540 entries |
| Diagnostics sections | 825 machines, 4,444 |
| Signature analysis | 16 machines, 220 codes + 113 pin-level (Battlezone/Red Baron) |
| Parts lists | 192 documents, 11,911 rows |

Corpus ships as **static assets** (`web/data/`, ~11,400 files, 157 MB). No KV, no R2 —
a deploy publishes code and data together. Repo `.git` is 133 MB as a result.

## Architecture

```
tools/     pipeline (ingest, OCR, structure, extraction, board generation)
           devices.py = verified pinouts (nets); packages.py = pin counts (maps)
src/       Cloudflare Worker — JSON API over web/data
web/       static UI + the corpus itself
boards/    board definitions (data) + *.read.json (hand-read source notes)
kicad/     generated KiCad projects
```

Deploy: push to `main` → Workers Build. **Version command must be
`npx wrangler versions upload`**, not `wrangler deploy`, or branch builds publish to
production.

Rebuild data: `build_doc_stats.py` → `build_parts.py` → `build_search.py` →
`build_assets.py`, then commit and push.

## Adding a board

1. Find a component-location drawing or schematic sheet with designators **and** part
   numbers. Render into `cache/sheets/` (never `/tmp` — see traps).
2. Read it by eye, region by region. Record to `boards/<slug>.read.json` with a
   `section` per device (functional block, from the sheet's titled areas).
3. Write `boards/<slug>.json` (grid + `ics`), plus `data/chips/<slug>.json` for lookup.
4. `build_board.py <slug>` then `publish_board.py <slug> --machine <machine>`.
5. `build_assets.py`, commit, push.

**Automated harvesting does not work.** Tested across every Atari drawing package:
designators OCR fine (18–34/sheet), hand-lettered part numbers do not (1–9).
`harvest_board.py` exists and returns ~0 pairs. Don't re-litigate this.

## Cross-machine findings (verified, in `data/related/`)

- **Red Baron ≡ Battlezone** — clock/reset/watchdog identical chip for chip; shared
  Auxiliary Math Box PCB (035678-01), now its own board map, so every device position
  and signature on it applies to both games.
- **Battlezone's game PCB and Auxiliary PCB are separate boards** — 035742 and
  035678-01, in one drawing package, with separate designator grids. The Math Box, the
  POKEY, the control panel inputs and all the sound are on the Auxiliary PCB.
- **Tempest ≡ Battlezone inputs** — two DIP banks → LS244s under OPT0/OPT1, third LS244
  for coin door with 3KHZ and HALT.
- **Asteroids Deluxe = Asteroids, designators one row lower** (B5→B4, C4→C3, …).
- **Asteroids -05/-06 shift designators one position** from -01…-04, and program memory
  is a *different complement in different locations* on -03, -04 and -05/-06. Hence four
  separate Asteroids boards rather than one.

Designator equivalence is something to **check, never assume** — three separate shift
traps found so far.

## Open work

**Boards.** Battlezone's DP-156 is fully read — sheets 1A, 1B, 2A, 2B, 3A, 3B. It turned
out to be three boards: game PCB 035742 (97 devices), Auxiliary PCB 035678-01 (36, shared
with Red Baron), and Regulator/Audio II PCB 035435-02, which is discrete and has no board
map — its notes are in `boards/battlezone-regulator-audio.read.json` and its power story
in `data/power/bzone.json`. Still unread on sheet 1 Side A: the Coin Door schematic
(034988-01), International Power Supply (035887-01) and the cabinet wiring diagram
(036242-01) — cabinet-level, not board-level.

Centipede and Tempest still have unread sheets. Untouched machines with drawing packages:
Gravitar, Black Widow, Space Duel, Space Invaders, Tank. Asteroids' own complement is
~106 of ~180 devices; sheet 02B partly unread.

**One unresolved Battlezone conflict** (in `boards/battlezone-math-box.read.json`):
Figure 3 on sheet 1B gives E/D2 pin 22 as `4414`, the Test #3 box on sheet 3B gives the
same net as `441H`. Both legible, both valid signature strings.

**Two unresolved Asteroids conflicts** (in `boards/asteroids.read.json`): C8 reads as
both the state-machine PROM and an LS02; both need a physical board to settle.

**The Asteroids revision complements are fixed at the source.**
`build_asteroids_revisions.py` overlaid each revision's memory onto the base sheet read
without clearing what that memory *replaces*, so -04, -05 and -06 all carried leftover
-03 PROM positions; and its grid filter silently dropped any spanning designator, which
is why each was also missing exactly one of its own ROMs (`D/E1` on -04, `E/F2` on
-05/-06). Both fixed, and all four revisions now match `memory_by_revision` exactly:
-03 has eleven PROMs, the rest have three ROMs each.

The generator also emits `data/chips/<slug>.json` now. That file is what the site's
"which chip is at C4" lookup reads, nothing generated it, and it had drifted — it showed
the sheet's `ROM 035131` at J2 where the board map showed the table's `035131-02`, and
it still listed the leftovers. One pipeline, one answer.

It also **reports collisions instead of resolving them silently**, which surfaced three
that were being decided by dict ordering. All three are logged in `asteroids.read.json`:

- **`B10`'s alternate is recorded as `B9`** — the only one of the 28 alternates that
  shifts *down*; the other 27 all go up by one. It collides with `B8`→`B9`, so on a
  -05/-06 board two devices claim B9 and the LS08 is dropped. `B10`→`B11` would fit the
  pattern and clear the collision, but that is inference, not a reading.
- **`D12` reads as a 74LS374 on sheet 02A and a CD4016B on 02B**, same block. The maps
  show the CD4016B, which matches the revision note — but only because 02B is flattened
  after 02A.
- **`E2` on -05/-06** is the sheet read's 2114 against the table's `035143-02` at `E/F2`.
  The table wins, being typeset and revision-specific, so those maps no longer show
  where the MPU RAM is.

**Only 28 of 106 sheet-read devices carry a -05/-06 alternate**, so most of those two
maps are early designators. The status text now says so instead of claiming a clean
shift.

**Still open on sheet 01B:** both printings of the substitution table show a twelfth -03
PROM (035142-02 at L1) and a sixth -03 alternate (035155-02 at L1) that are recorded
nowhere. Not applied — the table is a three-column layout that OCR interleaves, and
reading a column boundary wrong puts a wrong part number into a repair reference.

**The -06 rate multipliers are resolved on paper but not in the data.**
`asteroids-06.json` still carries `74LS97` at F9/H9/J9/K9 although the `resolved` block
and the board's own status text both say the -06 fits 035904/035905 PROMs there. The
parts list is a third voice and agrees with neither, giving 035904-01 at F8/H8/J8 and
035905-01 at E8. Logged in `asteroids.read.json`; needs the -06 block on sheet 02B.

**Net extraction** (`extract_nets.py` + `validate_nets.py`) is a working prototype:
component detection exact, 82% of pin attachments, but pin-number OCR is 30–50% and
single-digit biased. The validator catches 4/4 injected faults using device pinouts
(`devices.py`, 17/20 cross-checked against KiCad). Pin extraction is the blocker.

**Pong** has 8 traced signal nets (video chain) out of ~200; the rest needs a cleaner
scan of sheet 002826 than the archive holds.

**Test-point markers** are drawn as a flag symbol on the sheets — extracting them needs
shape detection, not OCR. Not started.

**Package sizing is fixed.** `tools/packages.py` is a packaging-only pin-count table,
separate from `DEVICES`, covering all 112 part types the board maps use — 688 of 704
devices are now drawn at their real size, against 704 uniform DIP-14s before. 56 entries
were re-derived from KiCAD's own symbol library by `tools/check_packages.py` (comparing
the highest pin *number*, since KiCAD omits no-connect pins); the rest rest on the
drawings or on the part's standard package. All 20 parts in `DEVICES` agree with it.
What is left:

- **Every device on every board is now sized** — 106 of 106 part types, 694 of 694
  devices. The four placeholders that used to draw as DIP-14 were settled from the parts
  lists rather than by re-reading the sheets: C5 is a 9316 counter (spelled 74LS161 in
  the earlier printings, same part), E12 is Atari 137108-001 — the Caberat manual names
  it a TL081CP — and M12 is Atari 66-114P1T, a 4-station DIP switch. The 8-station
  switches on Battlezone and Tempest are DIP-16.
- **20 devices are sized `unverified`** — the Atari 0351xx ROM/PROM numbers on the
  Asteroids maps, drawn as DIP-24 on the class default. Neither the drawing nor the
  parts list states a package. Wants one look at a board. This is the only soft spot
  left in the packaging table.
Two geometry bugs fell out of the same pass and are fixed:

- **The grid carried two rows that do not exist.** Atari's alphabet skips G, I, O and Q,
  and the board definitions listed G and Q, putting every device below F at the wrong
  height and making `F/H1` look like a three-position span. Confirmed by three
  independent routes; the reasoning is in `AGENTS.md` and `asteroids.read.json`.
- **Spanning devices are now placed across the cells they occupy.** `L/M1`, `H/J2`,
  `L/M/N3` and the rest go in a `spans` map on the board definition and are drawn at the
  midpoint of the cells the sheet's designator names, instead of hanging a 2in DIP-40
  symmetrically off one cell. The build rejects a span whose rows are not adjacent.

Still open there: **two of the Math Box's four Am2901 slices carry no span.** H/J2 and
D/E2 do, K2 and F2 do not, and all four are the same DIP-40 on the same row pitch, so
all four must span. Logged in `battlezone-math-box.read.json`; needs sheet 3 Side B.

## Traps that cost real time

- **tesseract silently returns nothing for images under `/tmp`.** No error, empty result.
  Rendering into the project cache took one sheet from 0 to 22,900 chars.
- **Signature codes are printed rotated.** Read the sheet twice — upright for
  designators, rotated for codes — and map coordinates back. Took Battlezone 9 → 68.
- **Sorting OCR lines by position destroys two-column reading order.** Tesseract already
  resolves it; re-sorting produced fluent-looking nonsense.
- **`board.Remove()` corrupts SWIG's type registry** for the rest of the process. Rebuild
  from `pcbnew.NewBoard()`, never clear.
- **`NETINFO_ITEM` without an explicit net code** serialises as a net with no number,
  which KiCad reads as *no net*.
- **IBOM needs `--include-nets`** or nets are silently omitted; it also compresses
  `pcbdata`, so grepping the HTML for a net name finds nothing even when present.
- **`kicad-cli pcb export bom` does not exist** — it silently exports XAO instead.
- **zsh does not word-split unquoted variables.** Bash-isms will not behave.
- **A signature box can be drawn with its header at the bottom**, so its column reads
  bottom-up. Read one against a known pin order before trusting the sequence.
- **Two printings of the same sheet genuinely disagree** on values, not just legibility.
  Where a procedure sheet gives the same signatures typeset and per device pin, prefer it.
- **The analyser alphabet (0-9 A C F H P U) rejects but does not decide.** "CAPE" is
  certainly wrong; reasoning it to "CAP5" was also wrong. It is `C4P5`.
- **`build_board.py` `ics` keys must be grid cells.** Passives (VR1, SW1, Y1, Q1, CR2,
  RP1, R125) throw; spanning designators (`L/M1`, `H/J2`, `L/M/N3`) go in at their first
  cell with the span in the note.
- **`wrangler dev` may not start in a sandboxed shell** (`esbuild spawn EBADF`). The
  corpus and the board views are static assets, so `python3 -m http.server --directory
  web` serves everything but the Worker's JSON API — enough to check an IBOM page. There
  is a `static` entry in `.claude/launch.json` for it.

## House rules being followed

Conflicts get logged, never guessed — a confidently wrong net in a repair reference is
worse than an absent one. Every board states its revision and says plainly that it is a
board map, not a complete BOM. Cross-referencing (a second sheet, the prose, a parts
list) has resolved every conflict so far; re-reading the same sheet never has.
