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
| Board maps | 50, across 41 machines · 2,524 devices |
| Signal indexes | 136 machines, 13,540 entries |
| Diagnostics sections | 825 machines, 4,444 |
| Signature analysis | 16 machines, 220 codes + 113 pin-level (Battlezone/Red Baron) |
| Parts lists | 192 documents, 11,911 rows |

Corpus ships as **static assets** (`web/data/` ~12,900 files 160 MB, plus
`web/pages/` 430 page scans 64 MB). No KV, no R2 — a deploy publishes code and data
together. Repo `.git` grows accordingly.

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

**Automated harvesting does not work — from the drawings.** Tested across every Atari
drawing package: designators OCR fine (18–34/sheet), hand-lettered part numbers do not
(1–9). `harvest_board.py` exists and returns ~0 pairs. Don't re-litigate this.

**It does work from the technical manuals.** Their IC parts lists are typeset, and
`tools/extract_ic_locations.py` recovers 2,721 designator/device pairs across 52
documents, from the 1,238 of 2,525 rows that pass their own checksum. Measured against
the Asteroids hand read it is 85% — not good enough to populate a board map unattended,
and not meant to. It is a second source, so it is worth exactly what a second source is
worth: it finds where the first one is wrong, and it reaches machines the first one has
not. See AGENTS.md for the checksums and the three traps.

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

**Drawing pages** (`tools/build_drawings.py`, new). The reader used to set every
schematic sheet as prose — 10-Yard Fight's pages 31/32/37 rendered as paragraphs
reading "ZEP Py KT TI IATD wif vel aifac}ar". `renderBlocks` has one escape hatch, a
page with *zero* blocks, and a drawing never yields zero. 2,933 pages were doing it.

The trap is that illustrated parts lists, DIP-switch tables and pin-out tables score
almost identically to a drawing on long-word rate — they are part numbers and
abbreviations — so a threshold there hides exactly the pages a repairer came for.
Symbol density separates them (drawing 0.037–0.089, parts list and prose 0.000–0.006)
because tesseract's output off a drawing is full of marks it could not resolve.

Nothing is hidden on a score alone. Two sources must agree: the outline heading or
the catalogue's "this document is a schematic", **plus** the page reading as noise.
926 pages clear it; the other 2,007 keep their text behind a warning, because hiding
a parts list is worse than showing some noise. Validated against 20 hand-read pages —
every drawing caught, every parts list left alone.

430 of the 926 are sheets inside a manual and ship their scan inline (`web/pages/`,
64 MB). The other 496 are pages of documents that are *nothing but* schematics; the
whole document is the drawing and `/pdf/<id>` already serves it, so they link out.
Inlining them too would add 135 MB to duplicate a working link — that is the open
question if the deploy budget ever justifies it.

Two things to know before touching it:

- **`width`/`height` on the `<img>` are load-bearing.** With `height:auto` they give
  the box an aspect ratio so it reserves height before the image loads. A lazy image
  with no reserved height is zero-high, never intersects the viewport and therefore
  never loads — the sheet stays silently missing. For the same reason the first four
  sheets in a document load **eagerly**: a document with any scans averages 1.5 of
  them and 215 of 285 have exactly one, so laziness defers the only thing on the page
  worth reading and a sheet that has not appeared looks exactly like one that is
  missing. Only the two documents with a long run of sheets defer anything.
- **`cache/text/` is not written to.** It is the ingest's checkpoint and stays the OCR
  as it came out; flags live in `data/drawings.json` and are merged by
  `build_assets.py` at publish time. Re-run `build_drawings.py --images` after an
  ingest, then `build_assets.py`.

**The 2,007 warned-but-kept pages are measured now, and the bucket holds no parts
lists at all.** Running the parts-list extractor over each page's text on its own
— `doc_text` flattens a document, so page attribution needs one page at a time —
none of the 2,007 yields a single trusted row, and 99.7% contain no parts-list
rows whatever. Fourteen read at random are all schematics, wiring diagrams or PCB
layouts; not one is prose or a table.

So they render as collapsed drawings now rather than as prose behind a warning.
The caution that put them in that bucket was sound and is worth keeping in mind
for the next classifier — an illustrated parts list scores the same as a drawing
on every text measure — but it was guarding against something this bucket does
not contain. And the treatment never hid anything either way: the text is
collapsed, not dropped, so a page in here that turned out to be a parts list
costs a reader one click rather than the content. No scan is published for them,
because nothing in the document attests they are drawings; the caption says so.
And 107 documents are 40%+ noise; the worst are pure schematic packages with no
outline at all, which is why the catalogue label had to become a source.

**Boards.** Battlezone's DP-156 is fully read — sheets 1A, 1B, 2A, 2B, 3A, 3B. It turned
out to be three boards: game PCB 035742 (97 devices), Auxiliary PCB 035678-01 (36 —
**not** shared with Red Baron, see below), and Regulator/Audio II PCB 035435-02, which is discrete and has no board
map — its notes are in `boards/battlezone-regulator-audio.read.json` and its power story
in `data/power/bzone.json`. Still unread on sheet 1 Side A: the Coin Door schematic
(034988-01), International Power Supply (035887-01) and the cabinet wiring diagram
(036242-01) — cabinet-level, not board-level.

**The parts lists cover machines the drawings have not reached.** Twelve machines with
no board map at all have 15 or more designators available — Monte Carlo 89, Football 82,
Outlaw 50, Crash 'n Score 48, Sky Diver 42, Orbit 40, Triple Hunt 34, Indy 4 30, Super
Breakout 20, Soccer 18, Starship 1 15. Existing maps could grow too: Asteroids Deluxe
8 → 97, Missile Command 14 → 82, Lunar Lander 6 → 63. `tools/merge_ic_locations.py` is the adjudication: the drawing read is authoritative
wherever it exists, the parts lists fill the gaps, a device is taken only where two or
more printings agree, and every device records its source — which the chip lookup shows.

**Three machines are through it, for +207 devices**, and in each case the drawing read
came out unchanged:

| | drawing | after | added | disputes |
|---|---|---|---|---|
| Asteroids Deluxe | 8 | 92 | 84, from 4 printings agreeing 100/100 | 3 cells dropped, claimed twice |
| Missile Command | 14 | 83 | 69, from 5 printings agreeing 82/82 | D3 |
| Lunar Lander | 6 | 60 | 54, from 3 printings | L6, E7, E8 dropped; 9 single-printing |
| Battlezone | 97 | 105 | 8, from 4 printings | none |
| Battlezone Auxiliary | 36 | 37 | 1, from 4 printings | none |
| **Football** | — | 77 | 77, from 2 printings agreeing 82/82 | L7 unnamed; 4 single-printing |
| **Crash 'n Score** | — | 38 | 38, from 2 manuals agreeing 38/38 | R28 off-grid; 18 single-printing |

**Nine more boards are published from a single printing**, flagged as such. Monte Carlo
79, Outlaw 47, Sky Diver 38, Orbit 37, Indy 4 30, Triple Hunt 29, Super Breakout 18,
Soccer 17, Starship 1 10 — 305 devices with no cross-check behind any of them. Every one
carries `singleSource: true`, which puts a warning at the top of the board page and a
badge in the boards list, and the chip lookup still names the source per device. The
whole site is 50 boards and 2,524 devices.

That leaves the well-formedness guard doing all the work on those nine, since
cross-printing agreement is unavailable. It rejected 24 device names outright and each
rejection is listed on the board's own read file.

**Football is the first board here with no drawing read at all**, and it is a fair test of
whether that is worth publishing. Its two printings agree on all 82 designators with no
split. The board says plainly that every device came from the parts list and that the
grid spacing is nominal, and the chip lookup names the source per device. The designators
are the real content and they are as attested as anything on the hand-read boards.

Its row alphabet is A B C D E F H J K L M N P — skipping G, I, O and Q, exactly as the
later boards do. That is the convention confirmed on a 1978 game, four years before
Battlezone. Crash 'n Score confirms it again on a 1975 one.

**Crash 'n Score carries a caveat the others do not.** The game has a main PCB and a
steering PCB per wheel, and its manual predates the figure headings that let Battlezone
be split, so the IC rows cannot be attributed to a board automatically. They are treated
as the main PCB — both manuals carry one continuous P.C. Board Assembly list with no
steering section, and the steering PCBs are described as producing a pair of signals
rather than as logic boards — but that is reasoning, not evidence, and it is logged as
such.

**Battlezone is the result worth trusting the method on.** It is the most carefully
hand-read board here — 97 devices off six sheet sides — and across both its PCBs the
parts lists confirm 87 of 87 overlapping designators with no disagreement at all. That
says the harvest is sound *and* that the six-sheet read was, and it makes the 21
disagreements on Asteroids look much more like errors in that read than noise in the
lists. Battlezone needs `--figure` because one manual covers both PCBs and their
designators collide.

The printings agreeing with *each other* is the real evidence, not the 85% single-printing
figure — Asteroids Deluxe's four agree on 100 of 100 designators and with all eight
hand-read devices.

**Missile Command's D3 is the one to look at.** All five printings call it a 74LS14 where
the drawing read says 7404. The drawing keeps the cell by the rule, but five-to-one is
worth a second look, and the two are both hex inverters with the same pinout — exactly
the pair a drawing makes easy to confuse. The chip lookup shows the dispute on that row.

Three cells were dropped rather than guessed. `B10`, `D10` and `F10` are each claimed
twice — a spanning designator from the 74LS157 row against a plain one from another row —
and there is nothing in the lists to say which is right, so the map has neither. Logged in
`asteroids-deluxe.read.json`; one look at the drawing recovers all three.

**The cross-check found 21 disagreements on Asteroids**, most repeating across
independent printings and so not OCR noise. Logged in `asteroids.read.json`. B7, C7 and
D7 are the strongest candidates for a bad read rather than a bad list: recorded as
74LS191, called 74LS161 by four to six printings and 9316 by two more — and the 9316 is
the 74161, so the list agrees with itself twice. The parts lists also give independent
support for the LS02 reading of C8, which was already an open conflict.

**"The corpus has been swept" was true of one thing only and was read as two.** It
was swept for *new machines to hand-read*. It had never been run against the boards
already published, and running it there found 499 devices and four new boards — Red
Baron 15 -> 66, Warlords 12 -> 57, plus Gravitar (68), Space Duel (70), Fast Freddie
(79) and Red Baron's Auxiliary PCB (18). Everything else is now genuinely at its
evidence limit: Crash 'n Score, Monte Carlo, Asteroids Deluxe, Centipede, Football,
Missile Command and the nine single-printing boards all confirm and add nothing.
Tempest gained 5.

Two results carry more than the device count. **Red Baron's Analog Vector-Generator
PCB agrees with Battlezone's hand-read game PCB on 58 of the 63 positions they
share** — sources with nothing in common, six sides of DP-156 read by eye against OCR
of two Red Baron parts lists — which validates the hand read and the harvest at once.
Gravitar and Space Duel check each other the same way, 54 of 62, from different
manuals.

And **Red Baron's Auxiliary PCB is not Battlezone's Math Box 035678-01.** It agrees
with it on 2 of 14 shared designators and carries no Am2901 slices and no 82S129
microcode PROMs at all, where the Math Box has four and six; a 555 sits where
Battlezone has a bit slice. The old note claiming a shared Math Box is withdrawn, and
with it the claim that Battlezone's 68 signature codes apply to Red Baron. What that
implicates on Red Baron's game PCB map — A1, K1 and K7 carry Atari 0361xx numbers that
are Math Box devices on Battlezone, at different positions — is logged in
`red-baron.read.json` and needs DP-169 or a board.

**Red Baron's manual covers two PCBs whose designator grids collide** — 8 collisions in
TM-169, 6 in TM-171 — and `locations()` resolves a collision by last write, so
harvesting it whole merges two boards into one wrong map silently. `--figure` clears
both to zero. Always check the figure headings before harvesting a manual.

**Asteroids is deliberately untouched by the harvest.** Its four revision maps are
generated by `build_asteroids_revisions.py` from a revision-specific memory overlay,
so a merge into `boards/asteroids-0*.json` is lost on the next regeneration; and its
ten printings span revisions whose numbering shifts, which is exactly what
manufactures false disagreements. The +24 per revision the dry run offers has to go
through the generator, not around it.

**The parts lists had a third layout nobody had read.** Black Widow, Liberator,
Major Havoc, Food Fight, Pole Position, Millipede, I-Robot and Quantum all carry a
perfectly good typeset IC parts list and all harvested exactly nothing, because
they print the designators *before* the device rather than after it:

    paren   37-74LS00   Type 74LS00 Integrated Circuit (N5, C6)
    lead    A6, A7 Type-74S74 Integrated Circuit  37-74S74

`rows()` reads forward from each `37-` stock number, so on those documents it
found the next row's designators, reported "no designators found" for every row,
and quietly paired each row's type with the *previous* row's stock number. It
produced no output rather than wrong output, which is the only reason it survived
this long. The trust rule is unchanged — the row states its device twice and is
taken only when the two agree. 35 documents that yielded nothing now yield, and no
document behind an existing board changed by a single designator.

**The designator convention transposes in 1983.** The later boards print `2L`, not
`L2`, and the alphabet widens with it — Major Havoc has devices at 2Q and 2S,
letters the early boards skip. `tools/designators.py` reads both; the board states
which it is in `grid.transposed` and it is never inferred, because `2L` and `L2`
are the same cell and only the silkscreen says which is printed. A wrong guess
does not corrupt a map, it transposes one.

Still open there: **Atari System 1 is not published.** Its two manuals agree on
only 3 designators and split on 8, which is the signature of a manual covering
more than one PCB — the Red Baron problem. It needs `--figure`, and the figure
headings need looking at first. 45 designators are waiting behind it.

**Atari System 1 turned out to be two boards, and is published as two.** Its two
manuals document different PCBs rather than two printings of one — TM-286 the LSI
Main PCB (45 devices) and TM-27 the Regulator/Audio III (30). That is why merging
them agreed on 3 designators and split on 8. System 1 is a platform, not a game,
so both maps apply to Marble Madness, Peter Pack Rat and Indiana Jones alike.

Return of the Jedi (37), Super Sprint (31), APB (23), Paperboy (20), Road Blasters
(16) and 720 Degrees (11) are published, all single-printing and flagged.

**A collision inside one printing used to be resolved by last write, and 22
published devices were chosen that way.** `locations()` detects a cell claimed
twice by the same parts list and returns it, but `harvest()` took only
`locations(...)[0]` and dropped the collision list on the floor — so the map got
one of two readings picked by position in the file. Fixed: a contested cell is
kept only when every reading of it names the same device, and is otherwise
dropped and reported. The 22 are withdrawn from Food Fight (1), I-Robot (8),
Indy 4 (3), Monte Carlo (4) and Pole Position (6), each logged with both
readings in the board's read file, because "it is one of these two" serves a
repairer better than silence.

That also unblocked **Pole Position II (38) and Xevious (18)**, which were
withheld for exactly this reason. Their contested cells are now dropped rather
than guessed, so no figure-splitting is needed to publish them safely.

**`plausible()` did not know the Fairchild 93xx/96xx series, and now does.** It
called 9312, 9322, 9602, 9300, 9301, 9316, 9321 and 9334 implausible — eight
parts appearing in 111 trusted rows and on 64 devices of published maps, every
one of them admitted by `well_formed()`. The two functions disagreed, and it was
not academic: `plausible()` is what breaks a tie between two printings, so on
Asteroids P9 a printing reading 9316 lost to one reading 74LS164, the 9316
discarded as wreckage when it is the more specific reading. The pattern is
bounded to `9[36]\d{2}` because that is what the corpus contains; a bare
`9\d{3}` would admit any four-digit smear.

**The split path was audited and had done no damage.** Replaying it over every
published board found 8 cells decided by the filter: 4 were Asteroids P9 (the
blind spot, and on no map), and 4 were genuine OCR corrections — `8728` to
`8T28` on Football, `74LSI91` to `74LS191` on Major Havoc, capital-I for 1.
After the fix, 4 remain and all four are the genuine kind. No published device
ever came from a false resolution.

**An impossible span is rejected at merge time now, not at build time.**
build_board raised on APB's `3B/F` — rows B to F, five apart, where every other
span on that board covers two — but by then the merge had already written it to
the board file, and removing it by hand did not stick: the next merge put it
straight back. The adjacency rule now runs where the designator is first
accepted, and reports it.

**Marble Madness and Championship Sprint are withheld for a different reason** —
10 designators each, and Marble's overlap the System 1 main board on 2 cells while
agreeing on none, so it is not clear which board its rows even describe. Ten
devices of uncertain provenance is not a map.

**Do not go looking for more machines to harvest from the drawings.** The
technique is Atari-only, and the reason is not the parts-list format: Atari's designators
*are* board positions, so recovering one recovers a location. Sega, Namco, Konami,
Nintendo and both Midways number sequentially (U34, U38), which gives a chip list and no
map. Checked across all six of the largest non-Atari manufacturers in the corpus.

**1,469 ROM maps are published from MAME**, a separate and weaker asset than the board
maps — memory devices only, one source, no cross-check, and the page says so. 407 are
machines whose manual is already here. They came from parsing every ROM_START block in
MAME's 4,682 driver sources: 35,517 sets, of which 5,581 name their ROM positions in a
grid convention and 3,160 are distinct layouts.

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

**Settled since, without needing the sheet read again.** The twelfth -03 PROM is real and
is in: 035142-02 at L1, with 035155-02 as its alternate. Sheet 01B of the 4th-printing
drawing package carries `035142-01 L1` directly, six further documents repeat it, and the
memory map requires it — 6800-7FFF is 6144 bytes, which is exactly twelve 512-byte PROMs
or three 2K ROMs and nothing else that tiles evenly. Eleven could never have been right.

**The -05/-06 ROM positions were the wrong way round and are corrected.** 035143-02 is at
J2 and 035145-02 at E/F2, not the reverse; 035144-02 at H2 was right. The 6th and 7th
printings both list the positions explicitly, and MAME's asteroid driver names its dumps
`035143-02.j2` and `035145-04e.ef2` — its suffixes are board positions, checked against
real boards.

**The Atari ROM sizes are no longer a class default.** Item 188 of the parts list is a
`79-42C24 24-Contact Medium-Insertion-Force Integrated Circuit Socket` fitted at J2, H2,
E/F2 and N/P3. Socket entries give a package size per position for every socketed device
in the corpus, and `tools/check_socket_pins.py` now checks the packaging table against
them: 26 confirmed, none contradicted.

**Missile Command D3 is a 74LS14** and the 7404 reading is withdrawn. All five printings
give `37-74LS14 Type 74LS14 Integrated Circuit (D3)` with stock number and description
agreeing, and the same rows put a plain 7414 at J9, so the lists are not blurring the two
parts.

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

**Two published maps were two PCBs stacked, and nothing warned.** The collision
work catches a manual whose boards share designators — C1 on one is not C1 on the
other, so a cell is claimed twice and something notices. It cannot catch the
quieter case: two PCBs whose designators do not overlap merge into one map with
no collision at all, and the result looks complete. Asking of every published
board whether its trusted rows sat under more than one figure heading naming a
different PCB found I, Robot (a CPU PCB and a Video PCB) and Paperboy (the same
pair). Both are split; the existing slug keeps the CPU board so its URL stays
valid.

Splitting recovered devices rather than losing them — I, Robot goes 45 to 33+24 —
because cells the two boards both claimed had been dropped as collisions and are
now separable.

Three more took a few devices from the wrong board's figure and are re-harvested
under their own: Tempest 5 (from its *Auxiliary* PCB, on a map that is the Analog
Vector-Generator PCB), Pole Position 4 (as attributable to a video-display
monitor list as to the CPU one), Food Fight 1 (shared with an EMI Shield figure).
Under the right figure all three add nothing back, which confirms the diagnosis.

**The figure survey, run over the whole corpus, is closed.** 50 machines yield
trusted rows under a figure heading; 13 document more than one PCB, and every one
of those is now either split, published as its own board, or understood:

- **Tempest's Auxiliary PCB is published** (23 devices, 4 printings, no split).
  It shares 16 grid positions with the Analog Vector-Generator board and agrees on
  none of them — A4 is a 74LS191 there and a 74LS08 here — which is the proof it
  is a different PCB and not a misattributed heading.
- **Food Fight's and Millipede's "EMI Shield PCB" figures are the game PCB,
  misattributed.** 22 of 23 and 11 of 12 overlapping designators carry the same
  device, which is what inherited-heading rows look like and what a second board
  never does. Nothing to build there, and it confirms the Millipede map is sound.
- **Pole Position's "Video Display" figures are the Electrohome monitor's parts
  list**, not a PCB grid. Not a board for this site.
- The rest (Star Wars, Kangaroo, TX-1) have 2–7 designators per figure — noise,
  not boards.

The discriminator that settles heading-vs-board in every case is the same:
overlap the two figures' designators, and count how many carry the same device.
High overlap with the same devices is one board under two headings; overlap with
different devices is two boards colliding by coincidence.

**Millipede looked like the same fault and is not.** Its TM-217 has one figure
heading the FIGURE regex recognises, so all 46 trusted rows inherit 'Utility
Panel Assembly' — but they are plainly game-PCB TTL, and a utility panel does not
carry 46 logic chips. The attribution is meaningless for that document rather
than wrong about the board, and both its printings agree on shared designators.
Left alone.

**Splitting a board leaves the other half in its chip lookup.**
`merge_ic_locations` deliberately keeps lookup entries that are not on the grid —
crystals, transistors, hand-read passives — so resetting `ics` to split a board
leaves the other half's devices behind as if they were off-grid extras. I,
Robot's lookup held 51 entries for a 33-device map, still answering "which chip
is at 5A" from both boards at once. Purged. Worth re-checking after any future
split.

## Traps that cost real time

- **`build_assets.py` will revert another session's corpus if your `data/index/`
  is stale, and it did.** web/data/ is generated wholesale from data/index/,
  which is gitignored and built locally, so a worktree whose index is behind
  regenerates the whole published corpus from the older one. It cost 39 files of
  a co-session's work in a commit that was otherwise a two-file front-end change
  — the document catalogue, the machine records and every search posting —
  caught only by reading `git status` before staging. There is a guard now: the
  corpus only grows, so a local index with fewer records than the published one
  is stale by definition, and the build refuses. `--force` overrides it. Do not
  reach for `--force` to make an error go away; rebuild the index or pull.


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
