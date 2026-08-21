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

**Boards.** Battlezone is done: sheets 1B, 2A, 3A and 3B are read, the game PCB is at
97 devices and the Auxiliary PCB is a separate map at 36. Sheet 1 Side A is the only one
left there, and it is cabinet-level — International Power Supply 035887-01, Coin Door
034988-01, the wiring diagram, and **Regulator/Audio II PCB 035435-02**, which is a third
board (Q1/Q2/Q3 regulator with remote sensing, R8 sets +5V, two TDA2002AV audio amps at
gain 10) with a four-step adjustment procedure printed beside it. Worth a read.

Centipede and Tempest still have unread sheets. Untouched machines with drawing packages:
Gravitar, Black Widow, Space Duel, Space Invaders, Tank. Asteroids' own complement is
~106 of ~180 devices; sheet 02B partly unread.

**One unresolved Battlezone conflict** (in `boards/battlezone-math-box.read.json`):
Figure 3 on sheet 1B gives E/D2 pin 22 as `4414`, the Test #3 box on sheet 3B gives the
same net as `441H`. Both legible, both valid signature strings.

**Two unresolved Asteroids conflicts** (in `boards/asteroids.read.json`): C8 reads as
both the state-machine PROM and an LS02; both need a physical board to settle.

**Net extraction** (`extract_nets.py` + `validate_nets.py`) is a working prototype:
component detection exact, 82% of pin attachments, but pin-number OCR is 30–50% and
single-digit biased. The validator catches 4/4 injected faults using device pinouts
(`devices.py`, 17/20 cross-checked against KiCad). Pin extraction is the blocker.

**Pong** has 8 traced signal nets (video chain) out of ~200; the rest needs a cleaner
scan of sheet 002826 than the archive holds.

**Test-point markers** are drawn as a flag symbol on the sheets — extracting them needs
shape detection, not OCR. Not started.

**Package sizing is wrong on every board map.** `build_board.py:package_for()` reads pin
counts from `DEVICES`, which holds 20 Pong-era parts, and falls back to DIP-14 for
everything else. ~90 part types are in use, so a 24-pin ROM and a 20-pin LS245 both draw
as 14-pin parts in the KiCad boards and the IBOM views the site links. Fix with a
packaging-only pin-count table kept *separate* from `DEVICES` — that one is the
electrical constraint set `validate_nets.py` trusts.

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
- **`wrangler dev` may not start in a sandboxed shell** (`esbuild spawn EBADF`). Verify
  the JSON the UI reads and check the live site after deploy instead.

## House rules being followed

Conflicts get logged, never guessed — a confidently wrong net in a repair reference is
worse than an absent one. Every board states its revision and says plainly that it is a
board map, not a complete BOM. Cross-referencing (a second sheet, the prose, a parts
list) has resolved every conflict so far; re-reading the same sheet never has.
