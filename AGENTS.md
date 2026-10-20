# AGENTS.md — Cathode Ray Tomes

Onboarding for whoever (or whatever) picks this up next. `README.md` is the user-facing
description; this file is the *why*, the traps, and an honest account of what is real.

## Mental model

Cathode Ray Tomes is three things stacked:

1. **An ingestion pipeline** (`tools/`) that pulls the ArcadeRTFM PDF corpus, rasterises
   every page, OCRs it, and derives search indexes. Runs locally, output lands in `cache/`.
2. **A Cloudflare Worker + static app** (`src/`, `web/`) that serves the corpus: browse,
   read, search. Everything ships as static assets under `web/data/` — no KV, no R2 —
   so a deploy publishes code and corpus together and the two cannot drift.
3. **Hand-built KiCad conversions** (`kicad/`) of a few boards, with a schematic and BOM
   viewer in the web app.

The pipeline is batch and offline; the Worker only ever reads what the pipeline produced.

## Load-bearing facts

- **Every upstream PDF is a flat scan.** Zero text layers, zero vector content across the
  whole corpus — verified, not assumed. Never write code that expects extractable text.
- **Upstream URLs contain raw spaces and parentheses.** `files.arcadertfm.com/18 Wheeler
  STD Wiring Diagrams.pdf` is a real URL. Quote the *path only* — quoting the whole URL
  breaks the scheme. `ingest.py:fetch()` does this correctly.
- **`files.arcadertfm.com` sends no CORS headers**, so browsers cannot fetch those PDFs
  cross-origin. Original scans are therefore not hosted at all: `/pdf/<id>` 302s to the
  source archive and the browser follows it as a top-level navigation, which CORS does
  not apply to. Do not add code that tries to `fetch()` one.
- **The upstream host blocks requests without a User-Agent** (Cloudflare). All fetches set one.
- **`pdftoppm` on this machine rejects `-r150`** — it needs `-r 150` as two arguments. It
  also numbers pages *without* zero padding, so `p-10.png` sorts before `p-2.png`. Sort
  numerically; `render()` does.
- **`7490`, `7493` use VCC=5/GND=10 and `7483` uses VCC=5/GND=12** — not the usual corner
  pins. Verified against the KiCad symbols and TI datasheets.

## Architecture — why there is no R2

The site serves **HTML manuals**, not scans. Text and structure for the whole corpus is
~157 MB across ~11,400 files and ships as static assets alongside the UI. Mirroring page
images would have been 63,000 files and 8.9 GB, which is what forced R2 in the original
design and is no longer needed. Original scans are linked out to ArcadeRTFM.

KV went the same way. Once the indexes were small enough to ship as assets there was
nothing left for it to hold, and dropping it removed the whole class of bug where a
deploy published code against a stale index.

Measured before deciding (Asteroids TM-143, 52 pages):

| | |
|---|---|
| Structured text + outline | 24 KB gzipped |
| Figures traced to SVG | 8.2 MB (4.3 MB cleaned) |
| Figures as WebP crops | ~2–3 MB |
| Full page images | ~5 MB |

Figures remain the open question: they are the real payload, and vectorising them is not
cheaper than raster. The plan is figure crops for a curated set, kept under the
20,000-file Workers Assets cap, so R2 stays unnecessary.

**Where the page scans stand now.** A document the catalogue calls a schematic,
drawing or wiring package ships every page's scan under `web/pages/` and the reader
shows it inline (drawing pages as the sheet with the OCR collapsed beneath, prose pages
as the scan with the text set under it). Those 3,656 pages were the worst on the site:
sheets set as paragraphs of OCR debris, because no text score separates a sheet with a
typeset note from a prose page with a figure. A manual still publishes only the drawing
pages its outline names. The 2,007 `noise` pages in manuals — drawings by score alone,
some of them parts lists — still link out: publishing them would put the deploy within
a few hundred files of the cap. That is the next thing to want and the reason to want a
second asset store.

## Extracting connectivity from the scans

Hand-tracing does not scale to 506 schematic documents, so there is a pipeline
for recovering it from the images:

    tools/extract_nets.py    topology from the scan (CV, no OCR)
    tools/devices.py         pinouts and gate structure — the constraint set
    tools/check_devices.py   cross-checks that table against KiCAD's symbols
    tools/validate_nets.py   rejects electrically impossible readings

The load-bearing idea: **pin numbers are the unreliable part, and the fix is
not better OCR.** A candidate reading is trusted because the circuit it implies
is possible, not because the digits looked clear. Supply pins must carry
supply, pin numbers must exist on the package, two totem-pole outputs must not
share a net, and — the strongest constraint — gates must be coherent. A 7427
output misread as pin 8 instead of 6 passes every per-pin check, because 8 is
also an output; what exposes it is gate 3 driving with nothing feeding it while
gate 2 has inputs and no output.

Measured against the hand-traced video chain: the correct netlist passes with
zero errors, and four injected OCR-style faults (6→8, 14→4, an out-of-range
pin, two outputs shorted) are all caught.

`check_devices.py` verifies 17 of 20 parts against KiCAD's library. The three
it cannot (555, 7425, 7450) are the symbols KiCAD does not ship — the same ones
built by hand from TI datasheets. Note KiCAD omits no-connect pins, so its
symbol legitimately has fewer pins than the package: a 7493 is DIP-14 with four
NCs. Only an *excess* of pins is a contradiction.

## What the board conversions are for

Diagnosis, not cloning. The test of a board conversion here is whether it helps
someone with a dead PCB find the right chip — so completeness of the bill of
materials matters far less than being right about designators, revisions and
function. A 105-of-180 complement that correctly says "C8 is the state machine
PROM on a -03 board" earns its keep; a complete BOM that silently describes the
wrong revision does not.

This is why conflicts get logged rather than guessed, why every board names its
revision, and why devices carry a functional block rather than just a part
number.

## Adding a board

`boards/<slug>.json` describes a board's component grid; `tools/build_board.py
<slug>` turns it into a .kicad_pcb. Packages come from `tools/packages.py`, which
is deliberately a different table from `devices.py`: packaging only needs a pin
count and has to cover every part on every board (~110 of them), while
`devices.py` carries full verified pinouts for the 20 parts `validate_nets.py`
reasons about. Mixing them would either starve the board maps or quietly widen
what the net validator thinks it can check.

`tools/check_packages.py` re-derives every `kicad`-provenance entry from KiCAD's
symbol library, asserts the two tables agree wherever they overlap, and lists the
parts a board uses that are still unsized. Run it after touching either table.

Adding a machine is therefore data entry — *once you have the grid map*.

Getting the grid map is the part that does not automate. It comes from a
component-location drawing, read by eye. Pong has one (assembly drawing
A001433, every IC at a labelled A-H x 1-9 cell). Not every manual does:

- **Breakout TM-058** carries a PCB parts list (page 55, A004533-01) giving IC
  *types* — 7400, 7408, 7432, 74192, 9316, 82S16 RAM and so on — but OCR
  garbles the reference designators and there is no grid. The ink-heavy pages
  in that manual are the **Motorola XM501 monitor** schematic, not the game
  board. A BOM is recoverable; a layout is not, from this document alone.

So the realistic unit of work per board is: find a component-location drawing,
read it once, write the JSON. Everything after that is scripted.

## The pipeline assumes English, and 43 documents are not

`ingest.py` reads `data/languages.json` and passes the language to tesseract. Only the
documents that are not English are in it. Three things break if that is forgotten:

- **A Japanese page read with `-l eng` is not a failure that looks like one.** It comes
  back as confident Latin nonsense, which every downstream measure then reads as drawing
  debris — correctly, on the evidence. The page was flagged as noise and the flag was
  right; what was wrong was what the page said.
- **`build_drawings.py` cannot read CJK.** Every measure in it is calibrated on English,
  and a kanji is in none of its character classes: SYMBOL counts each one as debris, so a
  correctly-read Japanese page scores 0.24-0.53 against a drawing threshold of 0.030.
  `is_cjk_text` exempts them. Anything else added to that file needs the same exemption.
- **`shard_of` must match the Worker's `/^[a-z0-9]/` exactly.** Python calls a kanji
  alphanumeric and JavaScript does not, so a bigram would be written to a shard named 設
  and looked for in `_`: indexed, and never found. Test the two together — `test_worker.mjs`
  has a case, and routing tests cannot see this class of bug.

Re-read named documents with `ingest.py --redo <ids>`, which ignores the checkpoint.

## A ruled table's columns are separate tesseract blocks

This is the fault behind most of what was wrong with the parts lists, and it is not
an OCR failure — the recognition is fine. A vertical rule between two columns is a
**block boundary**, so `cache/text/` stores a parts-list page as one block of item
and part numbers followed by another block of descriptions. Flattening it for the
extractor puts every description after every part number, and each row is then paired
with the *next* row's data.

    cache/text  31 281-0004-12 33 281-0014-28 … SCR, 8-32 x .750 PN HD PHIL …
    banded      31 281-0004-12 1   SCR, 8-32 x .750 PN HD PHIL

The geometry is what recovers it: `tools/parts_rows.py` re-reads the page from its
cached scan and bands the lines by vertical centre. **This is the same fault the
SCPH-70000 had** — pdftotext blocks a printed table by column too — and the same fix,
which is worth remembering the next time a table comes out as two runs.

Three things to know before touching it:

- **`cache/rows/` is gitignored.** Run `parts_rows.py --all` before `build_parts.py`
  or every description it recovered reverts to an em-dash on the next rebuild, with
  nothing to say it happened.
- **Both readings are kept and scored.** Banding is not always better: Xevious prints
  no item-number column at all and Tenpin prints its description first, and on those
  the banded read parses worse. `_score` prefers whichever recovers more descriptions,
  so the change cannot regress a page.
- **`cache/text/` is not written to**, exactly as `build_drawings.py` leaves it. It is
  the ingest's checkpoint and stays the OCR as it came out.

## A table row arrives on one line, and only the column gaps say where its cells are

`parts_rows.py` reunites a table whose **rows** tesseract split across blocks. The other
half of the same problem is a table whose rows arrive whole and whose **cells** do not.
Tesseract reads a DIP-switch row onto one line and sets its cells apart by whitespace an
order of magnitude wider than a word space — `Off [74] 70 [7] seconds [8] per [7] coin
[108] F` — and `ocr_page` then joined those words with single spaces. The row reached the
reader as a sentence, `_is_table_row` never fired, and the row beneath it was glued on as
the same paragraph. `ocrlib.table_rows` recovers the cells from the word boxes `ocr_page`
now keeps, and `tools/page_tables.py` applies it to the corpus.

Four things to know before touching it:

- **The threshold is per page, never per line.** This is the reason the obvious fix does
  not work. A row of three cells has two or three gaps of its own, so its median *is* the
  column gap: `On [149] 1-coin [9] minimum [138] N` has a median gap of 138, and no
  multiple of that finds anything. `_word_space` takes the **lower quartile of every gap
  on the page** — the lower quartile and not the median, because on a page that is mostly
  table the column gaps are half the sample and would drag a median up with them.
- **A wide gap is only a proposal.** The threshold that finds a column also finds the
  hole OCR leaves where it dropped a word. What separates them is that a column repeats:
  a cell start has to be shared by three rows before a split is kept, so debris at a
  random x is discarded. Rows may keep a stray cell the columns do not explain — a
  footnote mark in its own narrow column is real — so a row needs three of its cells in
  columns, not all of them.
- **Three columns, never two.** Two cells a row is a two-column prose page read across
  the gutter, and interleaving that is the worst thing that can happen to this text. It
  is why `GRID_MIN_CELLS` in `ingest_vector.py` is 3 as well, and it holds: on Hard
  Drivin' page 3-25 the flowchart boxes became rows and the two columns of numbered
  prose beneath them stayed prose, because those lines carry one wide gap and make two
  cells.
- **Rows are not all the same width, and that is not a bug to fix in place.** 27% of
  recovered pages have every row at the same cell count and the median page has two
  thirds of its rows at its modal width. The rest are ragged because tesseract splits a
  cell wherever its words happen to sit far enough apart (`IC,` and `74L8174` arrive as
  two cells where the page prints one) and because a row that skips a column has no way
  to say so: a `tr` is cells joined by three spaces, and `re.split(r"\s{3,}", "a      b")`
  is `["a", "b"]`, so an empty cell cannot be written down. Snapping cells onto the
  detected columns is the obvious fix and is wrong as stated — `Display During Self-Test`
  is one header centred over two columns and would be glued onto `Result`. Doing it
  properly needs spans and a `tr` that carries a list of cells rather than a string,
  which is a change to the reader, `check_pages.py` and the vector path as well.
- **The 43 Japanese manuals get no tables, and that is the guard working.** Their
  pages carry real pin-out charts, and re-reading one with `-l jpn+eng` finds them --
  26 rows on the JAMMA chart in `02b619948f1e` p3. The re-read does not reproduce the
  published Japanese *glyph for glyph* (`念 配置 図` against `品 面`), so the page is
  left alone rather than have its text swapped for a second opinion in a script the
  rest of the pipeline cannot score. Reading a page and replacing a page are different
  permissions. Note also that this checkout's `cache/text/` still held those documents
  in the English they were first read in while `web/data/doc/` had them in Japanese,
  which is why the reference is the published document and not the checkpoint.
- **`data/tables/` is committed**, which is the one place this differs from
  `cache/rows/`. `web/data/doc/` is built from `cache/text/` plus the side-cars, so a
  gitignored side-car silently reverts on the next rebuild — the trap `cache/rows/`
  already sets. Merge it with `build_assets.py --tables-only`; a full `build_assets.py`
  run wipes `web/data/` and rebuilds it from the gitignored `data/index/`, which a
  worktree does not have.

## Quantity is a column in most of these manuals, and the header says which

`extract_parts.py` recovers rows from the shape of the data, and the column
order it has to assume is the one thing it cannot read off the shape. Measured
over the corpus, 346 of 621 header occurrences name a quantity column between
PART NO. and DESCRIPTION and **183 have nothing at all** — the Sega lists are
ITEM, PART NO., DESCRIPTION and no more. So the split is gated on the page's
own header, never applied blanket:

    header names a quantity column : 94% of descriptions start with a number
    header names no such column    : 22% do, and those digits are the
                                     description — "2 Player Harness"

A continuation page inherits the last header seen; a document with no
recognised header anywhere falls back to `infer_qty_column`, which reads the
magnitude of the leading numbers, because a quantity is small and a component
value is not (`1 Speaker Cover` against `680 uf`). That fallback speaks only
when the manual is silent — a header always wins, in either direction.

**Clear the field that is wrong, never the row.** An electrical parts list
prints a rating where an illustrated one prints an item number, so `4W` arrives
as an item on rows whose part number and description are both good. And where a
page's columns OCR'd as separate runs, the "description" is the *next* row's
item and part number, while this row's own item and part are still correctly
paired — that pairing is what someone orders from. Both cases blank the bad
field and keep the row; the reader draws an em-dash for a description that
could not be read, which is a truthful answer rather than an empty cell.

Part numbers take a trailing revision letter (`75-010S`, `75-5124B`). Without
it the pattern does not recognise the next record and emits two rows as one.

## The parts lists are a second source, and they do harvest

The finding above is about the *drawings* and it stands. It does not extend to
the technical manuals, which carry a typeset IC parts list set in the same type
as the body text — and that list gives exactly the designator-to-device pairing
the hand-lettered drawings will not.

`tools/extract_ic_locations.py` reads it. Two layouts, each with its own
checksum:

    paren   37-74LS00   Type 74LS00 Integrated Circuit (N5, C6)
    count   37-7400  10 Integrated Circuit 7400  A2,A6,A9,D5,D9,E3,H/J2,L8,R3

The paren layout states the device type twice, as Atari's stock number and
again in the description, so a row is trusted only when two independent OCR
reads agree. The count layout states its own device count, so the designators
must come to that many. 1,238 of 2,525 rows across the corpus pass; the rest
are reported, never quietly used.

Measured against the Asteroids hand read: **394 of 464 designators agree, 85%**.
That is not good enough to populate a board map unattended and it is not meant
to. What it is good for is the two things a second source is always good for —
finding where the first one is wrong, and covering machines the first one has
not reached. Twelve machines with no board map at all have 15 or more
designators available, and Monte Carlo, Football, Outlaw, Crash 'n Score and
Sky Diver have 40 to 89 each.

`tools/merge_ic_locations.py` applies it to a board. The drawing read wins wherever it
exists, the lists fill gaps, and a device is taken only where two or more printings agree
— which is a far stronger test than the 85% figure suggests, because the printings agree
with *each other* almost perfectly when they are readable at all. Every device records
its source and the chip lookup shows it, so nothing in a repair reference hides where it
came from.

Two designators can land on one cell — usually a spanning `B/C10` against a plain `B10`
from a different row. Take neither and report it. Overwriting silently is the same bug
that put five phantom PROMs on the Asteroids -04 map.

**A manual covering more than one PCB gives each its own figure**, and the heading names
the board — `Figure 25 Battlezone Auxiliary PCB Assembly` against `Figure 26 Battlezone
Analog Vector-Generator PCB Assembly`. Pass `--figure` to split them. Without it the two
boards' parts land in one heap and their designators collide, which is the trap already
recorded above: C1 on one is not C1 on the other, and both have a +5V LED called CR2.

**A device the board map cannot name correctly does not go on the board map.**
`well_formed()` is stricter than "two printings agreed", and it has to be: both printings
of the Football manual spell L7 as `74874`, which is not a part anyone made — its
function number is 74, because that is what it ends in, and 874 is not what follows a
real logic family. It is an OCR of 74S74 that both printings happened to make the same
way, so cross-printing agreement cannot catch it. The guard tests the digits against the
packaging table's own vocabulary, which means the harvest can only place parts the table
can size — a good invariant, and the reason adding a machine sometimes means adding a
verified row to `packages.py` first.

**OCR destroys the logic family, and it does it the same two ways every time**: L read as
1, S read as 8 or 5. `74LS08` comes back as `741808`, `74LS74` as `74L874`, `74S04` as
`74504`. `repair_family()` undoes it, and it is safe to undo *only* because the result has
to land in the packaging table's vocabulary — every split of the string into family and
function number is tried, and the repair is taken when exactly one of them names a device
we know. Anything ambiguous is left alone and the device is not placed. On Orbit this took
the board from 16 devices to 37.

**Both layouts state the device twice**, and for a long time only the paren one used it.
The count layout carries the type in its description as well — `1 Integrated Circuit,
74S74 L7` — which is what finally identified a device both Football printings spelled
`74874`. If a row seems to have only one reading of its device, look again.

**The parts lists state package sizes too, and nobody has to infer them.** Atari stocked
IC sockets by contact count, so a row like `79-42C24  24-Contact Medium-Insertion-Force
Integrated Circuit Socket (J2, H2, E/F2, N/P3)` names the pin count of every socketed
position in the same typeset list the devices come from.
`tools/check_socket_pins.py` checks `packages.py` against them — 26 sizes confirmed and
none contradicted so far, including the Atari ROMs that were sitting on a class default.
Target it with `--docs` and `--figure` exactly like the merge: pooling a machine's
documents fails in the two ways this repo already knows, mixing Battlezone's two PCBs and
comparing one printing's numbering against another's.

**The harvest is Atari-only, and not because of the parts-list format.** It is because
Atari's reference designators *are* board positions — A1 through R13, the grid silkscreened
on the PCB — so recovering a designator recovers a location. Every other manufacturer in
this corpus numbers sequentially: Sega, Nintendo, Konami and the Midways all use U34, U38,
U42. A perfect harvest of those gives a chip list and no map, because U34 does not say
where U34 is. Checked across the six largest non-Atari manufacturers here (Sega 174
documents, Namco 170, Midway 116, Konami 106, Capcom 88, Williams 54): none carries a
parts list pairing a device with a grid position.

Sega's manuals do pair devices with designators in troubleshooting prose — "look at the
outputs of U34, a 74LS244" — which is a real source for a chip *list* if that is ever
wanted. It is not a source for a board map, and building one would need the silkscreen
layout from somewhere else.

## ROM maps are a different asset from board maps

`data/rommap/` holds 1,469 of them, built by `tools/build_rommaps.py` from the board
positions MAME records in its romset filenames — `036409-01.n1`, `pm1_prg1.6e`,
`136047-1108.5jh`. Those suffixes come from real dumped boards, so they are good
evidence for where a memory device sits.

They are **not** board maps and must not be merged with `boards/`. A ROM map names the
fifteen-to-forty socketed memory devices on a board of sixty to a hundred and fifty and
says nothing about the rest; it has one source and no cross-check. The board maps are
read off component-location drawings, carry per-device provenance, and have been checked
against parts lists, socket entries and MAME. Keeping them apart is why the site can be
honest about both, and the warning sits on every ROM map page.

Two grid conventions appear and both are kept as the board writes them: letter-first for
Atari and most US boards (N1, F/H1, L/M/N3), number-first for Namco, Konami and most
Japanese boards (6E, 12D, 7LM). `i` and `o` are skipped by every convention here because
they read as 1 and 0.

Clones share a layout, so sets are folded together by position signature — 350 further
sets matched one already written and produced no second page.

**The chip lookup holds more than `ics` does** — crystals, transistors, resistor packs,
test points, everything on the board that is not on the letter-number grid. Rebuilding it
from `ics` alone drops them. The first run of the Battlezone merge did exactly that and
lost twelve hand-read devices; `merge_ic_locations.py` now carries them through.

Three traps, all of which cost a wrong measurement before they were found:

- **Rows saying "substitute for item N" carry no locations of their own.**
  Read past one and it picks up the *next* row's designators, which is what
  made the LS245/AM8304B and LM324/LS170 substitutions look like errors.
- **A parts list is written in whichever numbering that printing used.**
  Checking a late-numbered list against an early-numbered board manufactures
  disagreements that are only the -05/-06 shift. `--cross-check` compares
  against both numberings for this reason.
- **Device equivalences must be normalised out first** — 9316 is the 74161,
  4016B is the CD4016B, AM8304B is the LS245 — or a third of the
  "disagreements" are two names for one part.

## MAME's account of each machine

6,427 of the 7,823 machines have no document. Their pages are kept, and listed, as
placeholders: everything on them comes from MAME, and the page says so ("No documentation
yet", with a link to the submission form), as does a muted badge in the browse list. Allan's
call (2026-10-19): no machine is removed for lacking documents, and the non-arcade entries
MAME carries (plug-and-play TV games, chess computers, Psion PDAs, fruit machines) stay too.

The CPU, sound, display, input and DIP data came with arcadertfm's machine list. The ROM set
did not, so it comes from the XML MAME publishes with every release:

    curl -LO https://github.com/mamedev/mame/releases/download/mame0289/mame0289lx.zip   # 19 MiB
    unzip mame0289lx.zip                                                                  # 326 MB
    python3 -I tools/import_mame.py mame0289.xml   # -> data/mame/machines.json (6 MB, committed)
    python3 tools/build_assets.py --mame-only      # onto web/data/machine/*.json

`import_mame.py` keeps, per romset on the site: the driver source file (linked on the page
at the release tag; MAME's driver comments often describe the PCB, and some 380 driver
files carry a "PCB Layout" sketch of where the chips sit), the parent set, every ROM file (name, size, CRC32, region, bad/no dump,
BIOS, merge) and disks. `tools/mame_data.py` puts it on a detail record; `build_index.py`
and `--mame-only` both call it, so a full rebuild and a targeted one agree. Never commit
the XML.

At 0.289: 7,444 of the site's 7,450 romsets match, with 90,264 ROM files. Six sets are gone
from that MAME (`dreamcha`, `gradiusb`, `hanaren2`, `twinbeeb`, `unkalba`, `unkamst`) and keep
only their older data. The four machines with no CPU in the upstream list (`higurashi`,
`systemy2`, `kof2002um` on Sega System Y2, and the Tandberg `tdv2115l`) have no CPU in MAME
either -- they are not emulated -- but do have ROM sets or a driver, so none was empty.

## Generated wiring views

Only 51 machines have a whole document filed as a wiring diagram, and nothing open maps games
to harnesses. So 1,153 machine pages carry a wiring view that is **generated, not read**: a
connector standard with the game's own controls placed on it. The page says so before any
pin, says what it leaves out (wire colours, lamps, the coin door's own wiring, the power
interconnect), and lists every control it could not place.

    data/wiring/library.json          connector standards, by hand, every pin table cited
    tools/check_wiring.py <mame>      the library against the MAME tables it came from
    tools/tag_harness.py <mame>       -> data/wiring/drivers.json: driver -> standard + evidence
    tools/wiring_data.py              generated view per machine; wiring pages in the corpus
    python3 tools/build_assets.py --wiring-only    onto web/data/machine/*.json + web/data/wiring.json

`<mame>` is a sparse 0.289 checkout of `src/mame` (275 MB, never committed); the commands to
make one are in `tag_harness.py`. `build_index.py` applies the views on a full rebuild, and the
full `build_assets.py` links the wiring pages last, once the documents are written.

**The JAMMA edge is read from the standard itself.** jamma-docs cites it and archive.org has
it: *Game Machine* no. 275, 1 January 1986, pp. 16-17, Table 1 (enacted 26 November 1985).
Read pin by pin from the scan, it disagrees with the community tables in two places, and both
are logged on the connector rather than smoothed over: pins 11/M are audio (+)/audio (GND), not
NC; and 25/c and 26/d are *spare inputs*, with 27/e GND. Buttons beyond three are therefore never
placed on a generic JAMMA edge -- jamma-docs puts button 6 on 27/e, which is a short on a board
that grounds it, as every MAME table says boards do.

**What `check_wiring.py` proves.** Every connector taken from a MAME table (CPS-1, CPS-2 and both
its CN5 wirings, CPS-3 and its CN5, both Neo-Geo edges, the Konami 18-way) is re-read from the
driver comment and compared pin for pin: no differences except the logged conflicts. The 1986
edge is then voted against eleven independent JAMMA tables in MAME's comments plus a measured
cabinet in arcade-docs: on 50 of 56 pins no table names a different standard signal. The six
that differ are 11/M (Lethal Justice puts its right speaker there) and R, 14, S, 15, which one
bootleg in `sfkick.cpp` uses for joystick lines. Parsing the tables is fiddly -- each driver
draws them differently, and cps3.cpp's header labels share lines with the JAMMA table -- so
read the parser before trusting a new table to it.

**Conflicts logged, not decided:**
- CPS-2 CN5 29/30: cps2.cpp has volume down/up, the CAPCOM-H2 sheet up/down.
- CPS-3 CN5 9, 15, 19, 21, 23: cps3.cpp orders the kicks the other way round from cps2.cpp, and
  the CAPCOM-H2 sheet (which says it covers CPS-2 and CPS-III) agrees with cps2.cpp. Drawn as
  cps3.cpp, struck through on the page.
- MVS 26: neogeo.cpp says "data input", NeoGeoDev unused. Not placed.
- The MVS has no kick harness, whatever the brief that started this said: button D is on 25/c in
  both sources. jamma-docs mentions a 15-pin MVS kick connector with no pin map; nothing confirms it.

**Tagging is per driver file, and the page says which kind it got.** `platform` (8 drivers,
reviewed by hand): a pin table in the driver (cps2, cps3, neogeo, shaolins), the CPS-1 edge
from kenseim.cpp (a CPS-1 board in a mole cabinet; cps1.cpp has no table), or a Sega 837-13551
JVS board instantiated in the machine config (naomi, chihiro, hikaru) -- code, not a comment.
`comment` (95 drivers): the driver's comments say its board has a JAMMA edge ("1x JAMMA edge
connector", a PCB layout with JAMMA at the edge, "Pinout = JAMMA"), quoted on the page with a
link to the line. A file with any line saying something is *not* JAMMA is left out; 30 drivers
are left out in all, each with its reason in `drivers.json` -- System 246 because its games
mostly run through Namco JVS I/O, Viper because its pots sit on JAMMA pins, PGM because its only
JAMMA line is about the 4-player link cable. Three filters on top, all in `wiring_data.py`:
comment tags only from 1985 on (a driver that mentions a JAMMA bootleg also holds the 1980
original), no gambling, mahjong, hanafuda, keyboard, keypad or mouse games (their "JAMMA edge"
carries their own assignment), and no CPS Changer.

**Coverage at 0.289:** 1,153 machines -- 674 generic JAMMA by comment, and by platform 230 JVS
(NAOMI, Chihiro, Hikaru), 163 Neo-Geo MVS, 40 CPS-2 (35 kick wiring, 5 on the 3-4 player CN5),
38 CPS-1, 7 CPS-3 and 1 Konami 18-way. 711 have every control placed; the rest list what is
not (mostly a fourth button on a generic edge, then light guns, analog sticks, pedals). The
estimate this started from was a floor of 555 on known platforms; the platform count is 479
because Sega PC and the CPS-1-like boards turned out to have no pin table to tag them from.

**Not in the library, and why.** Irem: no open pin table found. Sega JVS "Type 4": none either;
the Type 1 board (837-13551) is drawn in full, the Type 2 (837-13844) and the JVS-to-JAMMA board
(838-13683) only as far as naomi.cpp names their pins. The CPS-1 kick connector for Street
Fighter II: no open source gives its map, so kicks are listed as not placed. The JVS PDF and the
CAPCOM-H2 sheet are linked, never hosted, and KLOV was not used.

**The Konami 18-way is checked against a manual.** shaolins.cpp is the only open table, so only
its games are tagged. Kicker's own conversion kit manual is in the collection, and its harness
page (scan p. 8) agrees on all 36 positions. It letters the solder side A-V and numbers the parts
side 1-18, like JAMMA; the library uses those names, not MAME's A1-A18/B1-B18.

**Wiring pages already in the corpus.** `wiring_data.page_kind` flags a published page when a
heading near its top names a wiring diagram, harness or pin-out *and* the page shows it (wire
colours, a solder/parts side, a drawing's score), or when six or more two-colour wire codes
(WHT-BLK) sit on a drawing or pin table. 350 pages in 250 documents, linked from 204 machine
pages above the generated view, because they were drawn for the machine. A hand-read sample of
50 found two false hits, troubleshooting tables quoting wire colours, which are now excluded.

Traps:
- **A loader that finds its box before awaiting finds nothing.** `machine()` starts the loaders
  before it writes the page; `loadWiring` must await something first even when the library is
  cached, or the section silently never appears on the second machine a reader opens.
- **The browser holds API JSON for five minutes**, and `index()` memoises per isolate. After
  republishing, restart `dev_server.mjs` and fetch with `cache: 'reload'` before believing the page.
- **A pin a game does not use is greyed, never hidden.** A harness still has to know it is there.

## PCB layouts from MAME's driver notes are a third asset, and the weakest

Hundreds of MAME drivers carry an ASCII sketch of a board in a comment -- most of them the
Guru's, drawn off real PCBs -- with a `Notes:` legend under it saying what each part is.
For the makers whose designators are sequential (the harvest above is Atari-only because
U34 does not say where U34 is), this is the widest licence-clean source of *where things
sit*. `tools/extract_mame_layouts.py` reads them:

    git clone --depth 1 --branch mame0289 --filter=blob:none --sparse \
        https://github.com/mamedev/mame.git /tmp/mame
    git -C /tmp/mame sparse-checkout set src/mame
    python3 -I tools/extract_mame_layouts.py /tmp/mame    # -> data/mame/layouts{.json,/}
    python3 tools/build_assets.py --layouts-only           # -> web/data/layout{s.json,/}

A layout is the sketch verbatim (`art`), its devices -- label, designator where the label
carries one (`SR02.F2` is at F2), kind, the legend's description, position as a fraction of
the frame, and the source line each was read from -- and the layout's own provenance: driver
file, lines, MAME tag and commit, licence, copyright holders. Pages are `/layouts` and
`/layout/<dir>/<driver>/<n>`; a machine page links its own. **Never merge one into
`boards/` or `data/rommap/`**: major devices only, positions are a character cell on a
sketch, one reading of one board. The pages say "partial: major devices only" every time.

At mame0289: 391 files mention a PCB layout; **16 are GPL-2.0+ or LGPL-2.1+ and are skipped**
(taito_b, opwolf, naomi, hng64, raiden2, saturn ... -- the extractor reads `// license:` and
only BSD-3-Clause and CC0 go in; `check_pages.py` fails the deploy on anything else). 1,003
boards parsed; 950 in 319 drivers that have a machine on this site are published (32,544
devices, 9,233 described by a legend, 3,507 at a position a romset file is named after).
Reach, by the rule the machine page applies: **1,588 site machines show a layout** -- 398
for their own set or its parent, 44 only through a clone's board, 1,146 only from the
driver's general notes -- of 2,511 in a driver that has one. 1,352 of the 1,588 have no
document, and 16 are Atari's, so this does reach the makers the harvest cannot: Konami 180,
Namco 148, Sega 103, IGS 50, Capcom 49.

How a layout is tied to a set (`scope`), strongest first: **set** -- the comment sits directly
above that set's `ROM_START`, the Guru's habit; **title** -- a line just above the drawing *is*
the title of a parent set in the same file ("Arkanoid" / "Taito 1986"); **driver** / **file**
-- tied to no set, shown on every machine in the driver as "tied to no set". A set's clones
come with it from the `GAME` macros. `layouts_for` in the extractor and `layoutsFor` in
`app.js` are one rule written twice, so the measurement is what the pages do; change both.

Traps, every one hit:

- **A ruled table is shaped like a board.** Game lists (`triforce.cpp`), ROM-size grids
  (`psikyosh.cpp`), Namco's jumper charts all have a frame and words. A table's rules run the
  whole height -- but so do two boards drawn side by side (`mwarr.cpp`) and chips drawn as
  tall outlines (`funworld.cpp`, `namcos23.cpp`). `is_table` needs the full-height rule *and*
  table content: mixed-case words, a `-+-` junction, or fewer than six part-shaped words.
- **A legend key of `*` matches everything.** Arkanoid's notes have `* - these NC pins ...`,
  and as a wildcard it described the crystal, the volume pot and a DIP sheet as joystick
  pins. A key has to carry two alphanumerics before it can be a glob.
- **Text runs down the board's edge.** `|2` `|8` `|W` `|A` `|Y` is the 28-way connector.
  Single characters stacked in one column are rejoined, but only with a letter in them: a
  column of digits is the board's own grid numbering.
- **Kind is the first thing a legend names**, not the first match in a fixed order:
  `Mitsubishi M58725 2kBx8-bit SRAM (sound program RAM)` is RAM, and `palette` is not a PAL.
  Where no legend speaks, `SR08.A1` -- a sticker and a socket -- is taken as a ROM and marked
  as a guess; a match with the romset (`dumps_for`) settles it.
- **A header that lists every game on a system board is not naming one.** Namco System 12's
  header has twenty titles; matching the two nearest the sketch tied a shared motherboard to
  Tekken 3. Title matching gives up past two matching lines.
- **Captions walk up into the previous board's notes.** The lines above a sketch name it
  ("Top board:", a PCB number) but only until a blank line, a paragraph or a legend.

`check_pages.py` checks every published layout: permitted licence, full provenance, index
and shards in step, and that each device's position lands on its own label in `art` -- the
page lights up exactly that span, so a wrong offset would point confidently at the wrong
word. `test_worker.mjs` has routing and content cases, including that a layout leaves the
Worker with its licence, copyright and commit.

The BSD licence asks that the copyright notice travel with what is reproduced; every layout
page states the licence and the file's copyright holders and links the lines at the commit.
`ATTRIBUTIONS.md` is generated in `stoatworks-backend`, so its MAME entry should mention these
there. The shards cost 72 files (17,668 -> 17,740 under `web/`).

## The Pong board

`tools/build_pong_pcb.py` builds the layout from assembly drawing A001433 Rev E;
`tools/pong_power_nets.py` wires the rails; `tools/pong_signal_nets.py` holds the
hand-traced signal nets. All three want KiCAD's bundled Python (they need pcbnew):

    /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3

pcbnew quirks that cost real time:

- **`board.Remove()` corrupts SWIG's type registry for the rest of the process.**
  Every later `FootprintLoad()` returns a bare `SwigPyObject` and attribute access
  fails. Never clear a board — rebuild it from `pcbnew.NewBoard()`.
- **`PCB_IO_MGR.FindPlugin()` returns a manager-owned object** that gets freed
  mid-run. Construct `PCB_IO_KICAD_SEXPR()` and keep the reference.
- **`NETINFO_ITEM(board, name)` without a net code** serialises as `(net "NAME")`
  with no number, which KiCAD reads as no net at all. Pass an explicit code.
- **IBOM omits nets unless `--include-nets` is passed** — the output is
  indistinguishable from having no netlist, which sends you debugging the wrong
  thing entirely.
- IBOM compresses `pcbdata`, so grepping the generated HTML for a net name finds
  nothing even when the net is present. Check in the browser via `pcbdata`.

Tracing is done against the 500 dpi render and cross-checked on datasheet gate
mapping: a 7427 gate 2 is pins 3/4/5 into 6, a 7425 gate 2 is 9/10/12/13 into 8.
A misread pin number therefore shows up as a gate that cannot exist, which is the
main defence against quietly wrong connectivity.

## Tracing a whole board: the Battlezone Math Box

`battlezone-math-box` is the first board with every connection traced: 186 nets over
845 pins, ICs and passives both, from DP-156 sheet 3 Side B. Pong's eight nets live in a
pcbnew script; this one is data, and the pipeline after the read is generic:

    boards/<slug>.nets                 the read, by hand: net / wire / sig / nc / value
    tools/build_board_nets.py <slug>   -> boards/<slug>.netlist.json, and argues with it
    tools/plan_board_schematic.py      -> kicad/<slug>/plan/*.json, one per A4 sheet
    (Konnect MCP, one agent per sheet) -> kicad/<slug>/*.kicad_sch
    tools/check_board_schematic.py     KiCad's own netlist against the read, pin for pin
    tools/build_board.py <slug>        the PCB, now with the read's nets on the IC pads
    tools/publish_board.py <slug>      iBOM with nets, plus SVG/PDF of the redrawn sheets

**How the read was done.** The 400 dpi scan, rendered at 300 dpi in overlapping 1450 px
tiles, is legible down to the pin numbers; 600 dpi crops settle the dense spots (the
slices' carry chain, junction dots). Every IC's pins are recorded where they land, so a
two-ended wire is read twice. Long lines that cross tiles are the weak point: they were
settled by following them in one zoomed strip, and the control logic was then compared pin
for pin against the 1st printing, which agrees.

**What `build_board_nets.py` catches, and why it is worth running before anything is
drawn:** a pin number the part does not have (from KiCad's own symbol library, or
`tools/custom_pinouts.json` for the Am2901, POKEY, 82S129 and 82S123 -- each entry names
the datasheet it came from); two hard outputs on one net; a net only inputs listen to; an
IC pin neither wired nor marked `nc`; and two different signatures printed in the same
test on one net. A pin that was simply missed looks exactly like a pin that is unused, so
the coverage check is the one that earns its keep.

Traps, all hit once:

- **The legend is on the sheet, and an earlier note had it wrong.** Square: edge
  connector. Hexagon: the interconnect (the 24-pin cable from J19 on the game PCB).
  Pentagon flag: a test point (+5V, GND, +22V, AUD+, AUD-) -- not an off-sheet reference.
  The circles are not in the legend at all: they are the signature-analysis header.
- **The 2nd printing's bow-ties and heavy arrows are signature-analysis annotations.**
  The 1st printing draws the same lines without them. They are plain wire.
- **Read the slice order off the circuit, not the drawing order.** K2 is the most
  significant slice (only its F3 and OVR are wired; its RAM3 is the arithmetic-shift
  input) and D/E2 the least (carry-in from microcode bit A23). The notes had it reversed.
- **Red Baron draws the same Math Box at different positions** on its own board,
  036305-01: PROMs E1-L1 not M1-F1, the multiply latch D4 not C5. Same circuit, same
  PROMs, same signatures; not the same sockets.
- **A label is not an off-sheet join.** In KiCad a local label and a global label with the
  same name do not connect by name -- only by touching. So a net that crosses sheets gets
  a global label on every pin it has there, and a power rail gets local labels plus one
  power symbol placed on one of them. The plan decides which is which.
- **Konnect writes A4 sheets and has no paper-size tool.** Anything placed off the page is
  still in the netlist but clipped from every export, hence eight sheets rather than one.
- **Konnect's pin-location queries see one unit of a multi-unit part** (whichever was
  placed first). `batch_connect_to_net` places labels on the right unit; the queries do
  not report the others, so global labels on those pins were placed from the symbol
  geometry. `check_board_schematic.py` is what proves they landed.
- **A gate the sheet does not draw is not placed** (C4's first OR, E3's second NAND, three
  of M5's op-amps). KiCad's ERC reports them as unplaced units; that is the drawing being
  honest, not a fault.
- **Undrawn power pins are assumed.** The sheet draws VCC/GND only where it is unusual
  (the slices, C1, the POKEY, the LM324s on +22V); the build joins every other IC's supply
  pins to +5V/GND from its standard pinout, the two 4066s included.

## The second whole board: the Tempest Auxiliary PCB

`tempest-auxiliary` is DP-190 sheet 3 Side B, Auxiliary PCB 037585-01: 216 nets over 1,036
pins, 41 ICs and 147 passives, connectors and test points. It is the Math Box, the high-score
EAROM, both POKEYs and the audio output -- Tempest's equivalent of the Battlezone board, so the
same pipeline ran end to end. What it added:

- **The sheet was read in four parts at once**, one reader per titled box (decoder + power,
  Math Box, high-score memory, player inputs + audio), each working from one brief with the
  DSL, the legend and the tile coordinates. Atari names nearly every line that leaves a box,
  so the parts join by name; a reader writes any unnamed exit as a coordinate for the merge.
  None was needed. The brief is `docs/TRACING-A-BOARD.md`, part 1.
- **The 4th printing is in colour, and that makes it the one to read.** Wiring is black, the
  signature annotations blue, so a highlight band can never pass for a wire; where a blue
  band hides a line, the 2nd printing (1-bit) shows it.
- **The parts list is a completeness check for the passives.** TM-190 Figure 22 lists every
  resistor, capacitor and diode by value: all 130 are in the read with the listed value, and
  all 41 ICs at the listed positions. A read that is missing a pull-up shows up here and
  nowhere else, because a passive has no pinout to be checked against.
- **A second board with the same circuit is the strongest check there is.** Mapping
  Battlezone's PROMs, slices, counters and latch onto Tempest's positions, all 79 nets
  between them agree pin for pin and all 65 shared signatures agree -- two drawings, two
  independent reads. Red Baron's 036305-01 is the third copy and can be checked the same way.
- **A sheet can contradict itself.** B1 pin 1 is lettered BEGIN but drawn wired into /BEGIN,
  in all three printings. The read takes the pin's label (the circuit cannot work the other
  way), the read file logs the conflict and the board's status line states it. Record it; do
  not quietly pick one. The board page shows a read file's `conflicts` as **Open questions**
  above the board and its `notes` collapsed beneath them, so a logged conflict does reach the
  repairer; the status line is for the one they must not miss, and this is one.
- **`parallel PIN ...`** declares outputs the sheet ties together on purpose -- K3 is four
  LM324 sections driving one charge pump. The checker then counts them as one driver, and
  still reports them if the read did not put them on one net.
- **A custom pinout can name a supply pin's rail** (`"rail": "+5V"`). The ER2055 is PMOS: its
  VSS is the *positive* supply, and the build's name heuristic would have grounded it.
- **The per-board layout is data**: `boards/<slug>.sheets.json` (units, positions, custom
  symbols, connector symbols, label spellings, PWR_FLAGs). `plan_board_schematic.py` holds
  only rules, and Battlezone's plan regenerates byte for byte from its own file.
- **`plan_board_schematic.py <slug> --ops`** writes every global label, power symbol and
  no-connect as an explicit coordinate from the library's pin geometry (a symbol at X,Y puts
  pin px,py on X+px, Y-py; positions snap to the nearest 1.27 mm). That is the way round
  Konnect's first-unit-only pin queries, and it makes drawing a sheet mechanical: eight
  Sonnet agents drew ten sheets in parallel from `docs/TRACING-A-BOARD.md` part 2, each
  proving its own sheet with `tools/check_board_sheets.py` before the whole-board check. Konnect
  serialises calls, so parallel calls against one file are safe.
- **`build_board_nets.py` named a net with two sheet names by hash order**, so Battlezone's
  EXPLO EN / SAEN2,3 net changed name from run to run. The first name the read declares now
  wins; Battlezone's read lists SAEN2,3 first because that is what its drawn schematic says.

## Netlists converted from MAME

MAME's `src/mame/*/nl_*.cpp` files are circuit descriptions for its netlist simulator,
written by people reading the same schematics this repo reads. The DIP-level ones name real
designators and pin numbers (`NET_C(VCC, IC_A7.14)`, `CAP(C2, CAP_U(0.1))`), so they are a
machine-readable second reading of a sheet. `tools/mame_netlist.py` turns one into a
`boards/<slug>.nets` that `build_board_nets.py` checks like any hand read; the judgements
about each file live in `tools/mame_targets.py`, so the converter holds only rules.

    tools/mame_netlist.py --list               targets, with each file's licence
    tools/mame_netlist.py tank barrier-sound   -> boards/<slug>.nets and boards/<slug>.json
    tools/build_board_nets.py <slug>           as for a hand read

**Converted (2026-10-19, MAME 0.289, commit f34f02505e32), all passing with 0 problems:**
Tank, split into `tank-board-1` and `tank-board-2` (Ryan Holtz, BSD-3-Clause), and fourteen
sound boards by Aaron Giles (CC0-1.0): Barrier, Armor Attack, Boxing Bugs, Rip Off, Solar
Quest, Speed Freak, Star Castle, Starhawk, Sundance, Tailgunner, Astro Blaster, Eliminator,
Frogs and Space Fury. Only CC0 and BSD-3 files are converted -- the converter reads the
licence off line 1 and refuses anything else -- and MAME's DICE-derived GPL files
(Breakout, Rebound, Pong Doubles) are left to the DICE conversion. Every `.nets` header
names the file, the licence line, the tag and the commit. The source is fetched file by
file into `cache/mame/<tag>/`, never the whole repository.

**A simulator's netlist is not a board's, and most of the converter is undoing that.** The
rules every target gets:

- `#if` switches are re-evaluated with every `HLE_*`, `*FRONTIER*`, `*HACK*`, `UNDERCLOCK_*`,
  `ADD_CLIPPING_DIODES` and the like off, so where MAME keeps the real circuit beside a
  stand-in the real one is taken. A switch the converter does not recognise keeps its
  default and is reported.
- Virtual sources -- `TTL_INPUT` (the CPU's latch), `CLOCK`, `SWITCH`, noise generators,
  `AFUNC` -- are not parts. The nets they drive become `port`s, a statement added to the DSL
  for this: a net that leaves what the file describes, exempt from the one-pin and
  nothing-drives-it checks. A hand read has a connector instead and should not need one.
- A value multiplied by a named constant (`RES_K(100) * FRND1`) is written unscaled.
- A NET_C in a block MAME calls "Unused" or "Unconnected" becomes `nc` -- unless the circuit
  uses the pin, in which case the tie is dropped and logged. On Tank that is thirteen
  pins: the "unused" A7 pins are the crystal oscillator, N4's are the antenna latch.
- **Parked parts.** When a stand-in replaces a circuit without a switch, MAME parks the
  circuit's parts by tying *both* ends to a rail (`NET_C(R142.1, R142.2, C68.1, C68.2,
  U32.5, U32.9, GND)` on Eliminator). The checker cannot see this -- a resistor shorted to
  ground is electrically legal -- so the converter detects it and lists the parts as on the
  board but not in the file. Astro Blaster, Eliminator and Space Fury all do it.
- The real-circuit branches MAME never runs are bit-rotted: Armor Attack's and Tailgunner's
  use a Q1 declared only in a comment marked "not used" (by the stand-in), so commented
  declarations the real branch needs are brought back. Warrior's names a part `A3` that does
  not exist, and is not converted.

Per-target judgements: `undo` (a specific line, guarded by a fragment of its text so a wrong
number fails loudly), `restore` (commented-out circuitry), `loads` and `not_parts` (dummy
loads on open 555 outputs, a sound chip's outputs as 1K resistors), `fix_parts`,
`fix_values`, `repin`, `add_parts` and `add` (corrections read off the sheet), `contacts`
(the connector contact a named net lands on), and `split` for a netlist that spans boards.
CA3080 outputs on one node are declared `parallel`: they are currents, summed by design.

**Tank is two boards on one grid of designators**, so Board I's D11 is not Board II's. MAME's
single netlist is split by what each sheet draws, and every net that crosses lands on the
cable contact (Board I J1/J2 to Board II J4/J5) or stays a port where the sheet prints no
number. MAME's passive suffixes (R53A, R48B, C33C, R4V, R102MX, R74M1) are its own way of
telling the boards apart and are stripped; they are not a reliable board marker (R8A-R11A
are Board II's). The four sheets were read in full against the conversion -- the reports
are worth keeping in mind for any further work on Tank:

- MAME is right almost everywhere: motion counters and presets, the ROM's address and data
  wiring, the multiplexers, minefield, mine control, video summing, the one-shots, the stick
  inputs, the 556, and the 7492 at A12 -- whose pin numbers are the sheet's even though
  MAME's own 7492 *model* swaps QB and QD against TI (the MiSTer Tank core's point).
- Its errors, all corrected in the target: the score counters (D11's QA/QD into E11 the wrong
  way round, SCR1E on the wrong pin -- MiSTer's "score counter wiring"); HD1/HD2 taken from Q
  instead of Q-bar (MiSTer's "output pin of the HD1/HD2 flip-flops"); B6 a 7404, not a 7400;
  K6, L6, N15, F15 MFC6040s, whose pins are not the MC3340's (`repin`); shell 1's 2^2/2^3
  latches crossed; R53 330K; C50/C51 .22uF; the ROM's pin 9 and pull-downs on -12V.
- MAME feeds one board's signal straight into the other where the real board re-derives it
  from the cable: Board I makes its own HMCE, /EXPL1 and /EXPL2; Board II its own /START and
  ATTRACT. Splitting by board is what exposes this.
- Put back from the sheets in place of MAME's stand-ins: the crystal oscillator, the antenna
  latch, the noise transistor, the 25c/50c switch, the coin counter driver, and the motor
  sounds MAME comments out.
- The ROM is printed "24-PIN EA ROM" -- an Electronic Arrays MOS part, -12V on pin 9. MAME's
  MK28000 is a substitute (a handwritten note on one print agrees) whose pin 9 is GND.

**Compared with the sheet beyond Tank:** Barrier (the whole board -- every net and value
MAME has agrees, with one open question: the sheet draws U8's output onto the summing line,
which would swamp every other sound, and MAME leaves it out) and Star Castle (sheet 2 of 2).
The other twelve sound boards are MAME's reading, internally consistent and unchecked, and
their files say so.

**What does not convert, and why** (survey in the shared notes, `mame-netlist-survey.md`):

- **Gate-level netlists.** `TTL_7400_NAND(ic_e4a, ...)` names a gate, not a package or a
  pin, so it cannot become a pin-level net without reading the gate-to-package assignment
  off the sheet. That rules out Pong, Gran Trak 10 and Stunt Cycle -- of MAME's seven
  whole-board netlists only Tank is pin-level -- and a dozen others. DICE's game files
  name chips and pins, and are the better source for those boards.
- Space Wars: drawn from a redrawn schematic with part numbers borrowed from Barrier, so its
  designators name nothing on a Space Wars board.
- Warrior (the bit-rotted branch above); Sega's Universal Sound Board and speech board
  (mostly MAME devices, the netlist is a fragment).
- Not yet attempted, and mostly small resolver or pinout gaps: 280-ZZZAP, Gun Fight and
  Speed Race (Colin Howell, CC0, carefully documented), Destroyer, Flyball, Tank Battalion,
  Rally-X, Kid Niki and others.

Traps:

- **`CAP` has no polarity in MAME**, so an electrolytic's pins are MAME's 1/2, not + and -.
- **Pin-name maps for MAME's non-DIP devices** (`OPAMP`, `NE555`) are in the converter; a
  new one fails loudly rather than guessing.
- **A custom pinout can be `same_as` another** (NE566 = LM566, S2688 = MM5837, 74S287 =
  82S129); `build_board_nets.py` follows it.
- **Undo line numbers are of the file at the tag.** Moving `TAG` means re-checking every
  guard, which the guards make impossible to skip.

## Boards from jtcores, and the GPL-3.0

jtcores (jotego's FPGA recreations, github.com/jotego/jtcores) redraws the boards it studies
in KiCad: 43 of its projects are whole boards or sections of one, against two traced here.
They are GPL-3.0, and so is everything made from them, so they arrive as a different kind of
board and must stay one:

    data/jtcores.json          the manifest: board -> jtcores directory, site machine(s),
                               pinned commit, and every jtcores project left out, with why
    tools/import_jtcores.py    copy, netlist, layout, lookups (--verify checks the copies)
    tools/build_board.py       the board view, from the import's own `place`/`footprints`
    tools/publish_board.py     one PDF, the iBOM, the BOM, `license` and `origin`

**What is GPL in this repository.** For each of those boards: `kicad/<slug>/` (upstream's
sheets byte for byte, its LICENSE, and a NOTICE.md saying who drew it and what was added),
`boards/<slug>.json`, `boards/<slug>.netlist.json`, `data/chips/<slug>.json`,
`data/signals/<slug>.json` and `web/boards/<slug>/`. A board's registry entry carries
`license` and `origin` (upstream URL at the commit, the authors, the source here), and the
board page states both. **Never merge a GPL drawing into a hand-read board** -- the
Tempest and Battlezone reads are this repository's own work and carry no such licence --
and never copy one of these boards' data into a file that is not marked the same way.

**Credit is the commit history.** The authors on a board are the people who committed its
sheets to jtcores, with the aliases the history itself supports folded together (skutis is
Ulf Skutnabba, @skutis77 in his title blocks; JOTEGO is Jose Tejada). Title blocks are
missing or copied between projects too often to be the source.

Traps, all hit once:

- **KiCad 6 spelled it `"Sheet file"`, 7 onwards `"Sheetfile"`.** The importer copies only
  the sheets the root reaches, and following one spelling lost every child sheet on five
  boards: Capcom Bowling arrived as 4 parts of 132, Sly Spy as none at all, and nothing
  failed.
- **kicad-cli writes a `.kicad_prl` into the project as it exports.** The importer deletes
  what it did not copy and then compares every copied file with upstream's, so NOTICE.md's
  "byte for byte" is checked rather than asserted. Opening one of these projects in KiCad
  and saving rewrites the files; `import_jtcores.py --verify` is the test.
- **Every jtcores `.kicad_pcb` is an empty stub.** The board view is generated: ICs only,
  each with a footprint sized from its symbol's pin numbers (DIP to 64 pins, a quad pack
  above), nets from KiCad's netlist on their pads. Positions are nominal and the page says so.
- **Where the drawing names board positions, the layout uses them -- but which way round
  is read off the drawing.** `9B` against `B9` is the majority of the ICs (Premier Soccer
  was laid out as a numbered board until this was detected rather than listed). A big part
  takes several cells and the next IC along is numbered past it, so the pitch is where 19
  in 20 numbered neighbours clear each other; each DIP stands upright unless that collides,
  then lies down; what still collides is counted in the import log. A letter carrying most
  of the board (U12, U34) is a numbering prefix, and boards whose designators are prefixed
  by sub-board (Twin 16's `A_A3`, Fairyland's `B12`/`M12`) are laid out in designator order.
- **The deploy is within a few thousand files of the Workers Assets cap**, so an imported
  board publishes one PDF with its sheet list (each linked to its page, read back off the
  PDF's own title block) rather than an SVG a sheet: three files a board.
- **Custom chips are not boards.** jtcores also redraws the insides of Konami's gate
  arrays (Twin 16's 007779-007787), Capcom's DL-series and Konami's 052535. They are
  listed under `skipped` in the manifest: valuable for a dead custom, but a different asset.

## Boards from DICE: an emulator's netlist, read as one

DICE (dice-libretro, GPL-3.0) emulates the CPU-less games by simulating every chip, so each
game is a netlist -- `CHIP("A1", 7400)`, `CONNECTION("A1", 3, "B2", 4)` -- at the positions
Atari's drawings use. `tools/import_dice.py` turns 16 of them into boards (`data/dice.json`
says which, and why the other five are not), under the same rules as jtcores: GPL-3.0 on
everything made from them, the source copied into `kicad/<slug>/` with DICE's LICENSE.txt
and a NOTICE.md, and a page that says whose it is. There is no drawing, so the page carries
the netlist instead of a schematic.

It is the circuit as an emulator simulates it, not a drawing, and the conversion has to
undo DICE's shortcuts or it publishes them as wiring:

- **A CAPACITOR, BUFFER, CLK_GATE or WIRED_AND in DICE is a wire.** The first two are RC
  delays standing in a net, the third a speed hack between a clock and what it clocks, the
  last open-collector outputs tied. Their pins are joined into one net. Everything else DICE
  adds (VIDEO, the inputs, the power-on LATCH, the CLOCK, SERIES_RC) is not on the board.
- **A part with a part number is only a chip if it is at a board position.** DICE adds gates
  to model what the board does another way (Crash 'n Score's `CARGASAND`, a 7408); those are
  listed in the read notes as helpers, not placed. Positions spanning two rows are written
  without the slash (`DE1` is D/E1) and are placed between their rows.
- **Two 555 halves at one position (`B9A`, `B9B`) are a 556**, renumbered to its pinout.
- **VCC and GND are macros from DICE's C++ header**, which is not read; the importer seeds
  them. Missing them silently lost a hundred tie-offs from Rebound.
- **DICE's tie-high (`VCC`) is a net of its own,** not +5V: on the board it is a pull-up or
  a direct connection, and DICE does not say which. Supply pins, which DICE never wires, are
  joined to +5V and GND from each part's KiCad pinout.
- **Every wired pin is checked against the part's KiCad symbol, except the standard-TTL
  AND-OR-INVERT gates.** KiCad ships the 74LS54 and not the 7454, and they are pinned
  differently; checking against it accused DICE of six pins TV Basketball really wires.
- **Where a board map read off the drawings exists, the two are compared** (`compare` in the
  manifest). Crash 'n Score's map names 38 positions and DICE agrees on 36; H10 (7404
  against 7414) and B8 are logged on the page as open questions, not settled.
- **Hand-traced nets are compared pin for pin** (`compare_nets`, a script's `NETS` table read
  with `ast` because the script itself wants pcbnew). Pong is the case: DICE agrees with its
  map at 65 of 66 positions and with all three traced nets that join pins.
- **Pong comes from DICE, not MAME.** MAME's `nl_pong.cpp` is gate-level -- it names gates
  (`TTL_7400_NAND(ic_e4a, ...)`), not package pins -- so it cannot give pin-level nets; the
  MAME-netlist work found only Tank is DIP-level. MAME is the cross-check instead, and on F1
  it agrees with DICE (a 7493, the ball-speed counter) against the hand map's 7433. That is
  logged on the Pong board, not settled: the map changes when the drawing is re-read.

## The interactive schematic viewer

Every board with a KiCad schematic -- the 43 jtcores boards and the two redrawn here --
gets "Open the interactive schematic" on its page: KiCanvas (MIT, Alethea Flowers),
vendored as one file at `web/vendor/kicanvas/kicanvas.js` with its LICENSE.md, reading the
sheets themselves so a reader can pan, zoom, move between sheets and click a part or a net.
The PDF stays beside it as the fallback.

- **The sheets are not deploy assets.** They load from `raw.githubusercontent.com` (this
  repository is public and that host sends `Access-Control-Allow-Origin: *`), at `main`.
  Shipping them would cost ~470 files against the Workers Assets cap and ~150 MB. The
  consequence: a board's viewer shows what is on `main` on GitHub, so it works only once
  the board is pushed, and a local dev server shows the pushed sheets, not your edits.
- **Nothing loads until the reader asks.** CP System III is 5 MB of sheets across 20 files.
  The button states the sheet count and size; the script itself is fetched on first click.
- **The sheet list is data**: `redrawn.kicanvas` = `{base, files, bytes}` in the registry,
  the root first and every sheet the hierarchy reaches (`import_jtcores.hierarchy`, which
  follows both KiCad 6's `"Sheet file"` and later `"Sheetfile"`). `publish_board.py` writes
  it; `publish_board.py all --sources-only` refreshes it everywhere without rebuilding
  board views or PDFs. Filenames are URL-encoded per segment -- Final Round has
  `GFX-Fixed layer.kicad_sch`.
- KiCanvas asks for a `$$:0:$$` URL relative to the page and gets a 404. It is harmless and
  every sheet still loads; do not chase it as a missing sheet.
- Checked in a browser on Gradius III, Final Round, CP System III (all 20 sheets) and the
  Battlezone Math Box (KiCad 10 files written through Konnect, custom Am2901 symbols), and
  at 375 px wide.

## Structure detection

`tools/ocrlib.py` is the shared brain: one tesseract pass emits both plain text and a TSV
of word boxes, lines are regrouped, and headings are classified by height relative to the
document's median body height. It is deliberately high-precision — it would rather miss a
heading than promote a DIP-switch table row. The suppressors matter as much as the
detector: contents pages, illustrated-parts-list pages (detected by part-number density),
dot-leader entries and mid-sentence fragments are all excluded.

`ingest.py` computes structure inline (free — same OCR pass).
`backfill_structure.py` re-derives it from cached page images for documents ingested
earlier; run it with `--force` after any change to the classifier, since existing
outlines are otherwise left alone. A full pass is ~27 docs/min.

## Reading drawing packages

A drawing package is not one board. Battlezone's DP-156 sheets 2 and 3 Side A are
sections of game PCB 035742; sheet 3 Side B is Auxiliary PCB 035678-01, a
different board with its own designator grid. **Read the "Section of <part>" line
in the title block before merging any designators.** C1 on one is not C1 on the
other, and both boards have a +5V LED called CR2.

The title block's contents list is worth reading first. Battlezone's says sheet 1
Side B is the Math Box Signature Analysis Procedure — the most useful sheet in
the package, and one nothing else points at.

**Test-point maps are a completeness check.** Where a package carries a
signature-analysis figure showing every device with a test point, read the sheet
first and then check the read against that figure. Doing this on Battlezone found
two LS161s — the entire microcode program counter — missed on the first pass
through sheet 3 Side B.

**Printings disagree, and typeset beats hand-lettered.** The 1st and 2nd
printings of DP-156-03 differ on real values, and one prints a signature column
in reverse order. Where a procedure sheet gives the same values typeset and per
device pin, that is the better source. Every conflict logged from the
hand-lettered sheets was settled this way — never by re-reading the same sheet,
which is what the house rule already said.

**Signature codes use the analyser's alphabet: 0-9 A C F H P U.** No B, D, E, G,
S. `extract_signatures.py` already enforces this. It is a genuine constraint on a
reading — but it only rejects, it does not decide. A code read as "CAPE" is
certainly wrong, and reasoning "E is illegal, a 5 looks like that, so CAP5" still
produced the wrong answer: the typeset figure says C4P5. Use the constraint to
find what needs cross-referencing, not to manufacture the replacement.

Signatures marked with an asterisk are taken with a 1k resistor between the
analyser's data probe and +5V. Without it those readings do not reproduce, and
the note appears on only one printing.

## Designator namespaces collide on Atari sheets

`AGENTS.md` already notes that grid designators collide with KiCad refdes. The
sharper problem is that they collide *on the drawing*: R9, R10 and R11 are ICs at
those grid positions and also ordinary resistor numbers on the same package;
Q1 is a grid position and a transistor. Nothing distinguishes them but the symbol
drawn — a box or gate with a part number beneath, versus a zigzag with a value.
Not fixable by renaming. Read it off the symbol every time.

`build_board.py` keys `ics` by grid cell, so only real grid positions belong
there. Passives (VR1, SW1, Y1, Q1, CR2, RP1, R125) must stay out or the build
throws. Devices drawn spanning two or three cells — `L/M1`, `F/H1`, `B/C3`,
`H/J2`, `L/M/N3` — go in at their first cell, with the sheet's own designator in
the board's `spans` map so the footprint is placed across the cells it occupies
rather than hanging off one of them. The build rejects a span whose rows are not
adjacent, which is usually a sign the grid is wrong rather than the span.

**The grid alphabet skips G, I, O and Q — on the pre-1983 boards.** A B C D E F H
J K L M N P R. The board definitions used to carry G and Q as rows, which put
every device below F at the wrong height.

That rule does not hold for the later boards, and applying it to one rejects real
positions. From 1983 the designator convention transposes — Major Havoc, Food
Fight, Pole Position, Millipede, I-Robot and Quantum print `2L`, not `L2` — and
the alphabet widens with it: Major Havoc has devices at 2Q and 2S. Which way round
a board's designators are is stated in `grid.transposed` and read by
`tools/designators.py`; it is never inferred from a designator, because `2L` and
`L2` name the same cell and only the silkscreen says which is printed. Getting it
wrong does not corrupt a map, it transposes one, which is harder to notice. Three independent confirmations — nothing in any read, signature or
signal record in this repo sits in a G or Q row while both neighbours of each are
populated; and the sheets' own spanning designators treat F/H and H/J as adjacent
pairs, which a 24-pin DIP on a 0.75in row pitch requires. Pong predates the
convention and legitimately uses G.

## Traps that have already bitten

- **A fallback that fires on the wrong document does more damage than the fault it
  catches.** `bbox_xml`'s `pdftocairo -pdf` rewrite exists for the SCPH-9000, whose
  Producer string kills `pdftotext`. It also fired on the SCPH-70000, because poppler
  writes an unmapped glyph as a raw C0 byte and twenty-two of those on page 4 made the
  XML unparseable — and the rewrite re-renders the PDF, losing the Adobe-Japan1 CMap
  that seven other pages were set in. A 22-character fault destroyed 5,000 words.
  Sanitise the input to the primary path before letting a fallback take the file.
- **`/api/doc` merges the catalogue through an explicit allowlist**, and a field left out
  of it is not an error anywhere — the feature reading it simply never appears. `parts`
  was missing, so all 194 parts lists were unreachable from the reader while being
  served correctly at `/api/parts/<id>`. Add a catalogue field, add it there too, and
  add a content case to `test_worker.mjs`: routing tests cannot see this class of bug.
- **`build_blocks` collapsed the whitespace that makes a table a table.** The reader
  splits a `tr` on runs of three or more spaces to get its cells, and the block builder
  ran `" ".join(t.split())` over it first, so every table in the corpus rendered as a
  single-column strip. Kinds that carry structure in their spacing need `_tidy_row`,
  not the paragraph normaliser.
- **A commit from a shared checkout can revert someone else's feature without a conflict.**
  26bdc549 put every board's conflicts and notes on its page and every device note in the
  chip lookup; a61d2ab8, six minutes later, committed an `app.js` and `app.css` that
  predated it and took all three out. Git saw an ordinary edit, the data was still served,
  and the pages went without them for seven weeks -- long enough for the Tempest trace to
  document the gap as if it had always been there. `test_worker.mjs` now checks that the
  script still reads `b.conflicts`, `b.notes` and `v.note`. Work in a worktree, and read
  `git diff --cached` before committing a file another session may have touched.
- **A warning in a build that prints a hundred lines is not a control.** `ingest_vector`
  measured the SCPH-70000's undecoded text, wrote `undecoded: 0.0364` into the document
  and printed `⚠ text does not decode`, and the document shipped anyway and stayed
  shipped. `tools/check_pages.py` reads what is actually in `web/data/` and exits
  non-zero; run it before a deploy.
- **Reference-designator collisions.** Atari labels ICs by board grid position (`A2`, `C1`,
  `H7`). Used directly as KiCad refdes, `C1`–`C9` and `D1`–`D9` collide with capacitors and
  diodes, and `batch_delete_schematic_components` then deletes *both*. ICs are therefore
  `U` + grid (`UC1`, `UH7`); strip the leading `U` to recover the silkscreened position.
- **KiCad source files are never edited as text.** All changes go through Konnect MCP tools.
- **KiCad 10 renamed symbols** — `Device:Q_NPN_BEC` is gone, use `Device:Q_NPN`.
- **`zsh` does not word-split unquoted variables**, so `set -- $pair` in a loop silently
  passes one argument. Bash-isms will not behave here.
- **`.scrollIntoView()` scrolls the nearest scrollable ancestor.** With the contents list
  and thumbnail strip sharing one sticky sidebar, scrolling a thumbnail into view dragged
  the whole sidebar and hid the contents. The strip now scrolls via its own `scrollTop`.
- **The isolate-level index cache had no TTL**, so a re-ingested index was never picked up
  and search silently returned stale, near-empty results. Now 60s.
- **Aggressive document-frequency filtering broke ordinary queries.** Dropping terms
  present in >30% of documents removed "test", "switch", "monitor" — exactly the words
  people search service manuals for. Now 92%, with the index sharded to stay small.
- **`pgrep -f <script>.py` matches the wait-loop that contains the pattern**, so
  `until ! pgrep -f backfill_structure.py` never exits. Bracket the first character.
- **`data/chips/<slug>.json` and `boards/<slug>.json` are the same facts twice.** The
  chip lookup the site reads used to be maintained by hand, and drifted: it showed the
  sheet's `ROM 035131` at J2 where the board map showed the substitution table's
  `035131-02`. The Asteroids revisions now emit both from one pipeline. The other boards
  still have hand-written chip files, and theirs legitimately hold *more* than `ics` —
  off-grid devices the board map cannot draw — so do not "fix" that by regenerating from
  `ics` alone.
- **Most board definitions carry no `machine` of their own.** The link to a machine
  was supplied by `publish_board.py --machine` the first time and lives only in
  `data/boards.json`, so republishing without the flag used to silently unlink the
  board. `publish_board.py` now falls back to the existing registration; a board
  page that suddenly has no machine is this bug coming back.
- **A board's site status is `revision` + `coverage`, joined.** They are separate
  fields for a reason — one says what makes this board different from its siblings,
  the other how much of it has been read — and duplicating the revision text into
  `coverage` to "fix" a short status just makes the next republish print it twice.
- **Sorting OCR lines by position destroys two-column reading order.** Tesseract already
  resolves columns; re-sorting by y interleaves them. This produced fluent-looking but
  meaningless text ("All five of these leaf switches operate on 5 volts at The exterior of
  the game cabinet…") and is easy to miss unless you actually read the output.
- **Spreading the catalogue over a document overwrote its data** — `{...body, ...meta}`
  let the catalogue's `pages` *count* replace the document's `pages` *array*. Pick fields
  explicitly when merging two records that share key names.
- **A board's slug is not its machine's slug.** `asteroids-03` through `-06` belong to
  `asteroid`; only 13 of 50 boards share a slug with their machine. The machine page and
  the home-page KiCad badge used to test `board.slug === machine.slug`, so Asteroids said
  it had no board map. Match on `board.machine` (falling back to the slug).
- **`.reader.wide` beat the phone layout.** It is declared after the `max-width: 820px`
  rule and is more specific, so a 375px screen kept a 240px contents column beside the
  text. Any override of a `.reader` grid rule has to name `.reader.wide` too.
- **Lists must page, not truncate.** The home list stopped at 150 machines and the ROM
  map list at 400 of 1,469 with "search finds the rest" — and search only covers manuals.
  Every long list now has an A–Z bar and 50-a-page pager whose state lives in the query
  string; `/api/machines` takes `letter`, `offset`, `sch=1` and `kicad=1` so the totals
  are exact.
- **`wrangler dev` cannot spawn workerd here** (`spawn EBADF`, sandboxed or not), and a
  plain static server has no API. `node tools/dev_server.mjs` runs the real Worker in Node
  over a stub ASSETS binding with the production fallback, so the whole site can be
  driven in a browser; `tools/test_worker.mjs` covers the routing without a browser.
- **`build_drawings.py` reads whichever catalogue is larger** — `data/index/docs.json`
  or the published `web/data/docs.json` — because a fresh worktree's local index is
  behind what another session published, and `--apply` writes the flags straight onto
  the published documents so the drawing decisions can change without a full
  `build_assets.py`, which would refuse on the stale index (correctly).
- **A view that renders once needs an explicit first draw.** `show()` only re-rendered the
  paginated view, so the default document view came up empty until something else
  triggered a redraw.
- **API responses had a 1-hour cache TTL** and served stale JSON through several rounds of
  debugging. Now `max-age=300, stale-while-revalidate=3600` — short enough that a deploy
  shows up promptly, since the corpus ships with the code and both move together.

## Verified vs assumed

**Verified — run and observed:**
- Corpus statistics (7,812 / 1,384 / 2,405 / 506) queried directly from upstream.
- "No text layer, no vectors" — checked with `pdftotext`, `pdfimages`, `pdftocairo`.
- Ingest, OCR, page rendering: run end-to-end; hundreds of documents processed.
- The web app: browse, search, machine detail, reader, schematic + BOM viewer all
  exercised in a browser against the real Worker.
- Pong BOM: 66 ICs + 34 discretes = 100 devices, read off assembly drawing A001433 Rev E
  and cross-checked against the well-documented 66-IC figure.
- Vectorisation: traced, rendered and visually compared against the source scan.
- Battlezone Math Box nets: `boards/battlezone-math-box.nets` passes `build_board_nets.py`
  with no problems, and the redrawn schematic's KiCad netlist matches it net for net
  (`check_board_schematic.py`, 0 disagreements). The board page and its iBOM (175 nets) were
  looked at in a browser against the real Worker.
- Tempest Auxiliary PCB nets: `boards/tempest-auxiliary.nets` passes `build_board_nets.py` with
  no problems; every passive value and IC position agrees with the TM-190 parts list; its Math
  Box agrees with Battlezone's net for net and signature for signature; the redrawn
  schematic's KiCad netlist matches the read (`check_board_schematic.py`, 0 disagreements).
  ERC: 5 errors, all the drawing's own design, each confirmed on the 4th and 2nd printings:
  K3's LM324 sections paralleled into the -28V charge pump (3, "output to output"), and each
  POKEY's open-collector SOD looped to its SID with no pull-up (2, "input not driven"). The
  symbols keep their true pin types so ERC keeps reporting them; the read file's notes say
  where each is on the sheet. The bar for a redraw is 0 *unexplained* ERC errors.
  Not checked against a board: the B1/BEGIN conflict, the 4th printing's K3, R58 and C39
  readings, and which spinner edge pins carry clock and which direction (inferred).
- Wiring library: the JAMMA edge read pin by pin from the 1986 standard's Table 1 and voted
  against twelve independent tables (`check_wiring.py`); every MAME-derived connector re-read
  from its driver with no differences beyond the logged conflicts; the Konami 18-way agreeing
  on all 36 positions with Kicker's manual. The wiring section was looked at in a browser on
  CPS-1, CPS-2 (both CN5 wirings), CPS-3, MVS (both boards), NAOMI, Konami and generic JAMMA
  pages at desktop width in the dark theme, and on a generic JAMMA page at phone width in the
  light theme (no sideways scroll).

- jtcores boards: every copied sheet under `kicad/<slug>/` matches upstream at the pinned
  commit (`import_jtcores.py --verify`), and each board's netlist is KiCad's own export of
  those copies. Not checked: anything in them against a manual or a board -- they are
  jtcores' readings, published as such -- or how complete each is beyond what its sheet
  names say (five are flagged partial).
- DICE boards: every CONNECTION in the 16 games is read, every wired pin of a part KiCad has
  a symbol for exists on it, Crash 'n Score agrees with its hand-read map at 36 of 38
  positions, and Pong at 65 of 66 and on all three hand-traced nets that join pins. Not checked: that DICE's circuit is the board's -- it is an emulator's, and its
  simplifications beyond the four undone here are not undone.

**Assumed / not yet done:**
- **Every generated wiring view is generated.** None of the 1,153 has been checked against
  that game's own wiring diagram; the standard is right for the platform, and the game's
  controls come from MAME. The 674 comment-tagged ones rest on one line in a driver that may
  describe a different board from the one a given game shipped on. The CPS-3 kick order and the
  CPS-2 volume pins are open between sources; nobody has put a meter on either.
- **Pong nets are mostly not traced.** Eight signal nets (the video output chain) are, in
  `pong_signal_nets.py`, and `pong_power_nets.py` wires the rails from datasheet pinouts;
  the rest of the schematic shows placed devices, not wired circuitry. Sheet 002826 Rev E
  is the source; the H/V sync chains are still to do.
- The `7425` and `7450` symbols are hand-created from TI datasheets and have not been
  exercised in a wired design.
- `LM309K` vs `LM305K`: schematic 002826 says LM309, assembly A001433 says LM305K. The
  KiCad project uses LM309K. This discrepancy is real and unresolved — worth surfacing.
- Nothing has been checked against physical hardware.
- **The Math Box read is one person's reading of one scan.** The long lines that cross
  render tiles, and every power pin the sheet does not draw (the 4066s on +5V included), are
  the soft spots. The 1st printing agrees wherever it was compared, which was the control
  logic pin for pin and the sound section part for part, not the whole sheet.
- The full-corpus ingest was still running when this was written; `data/ingest-state.json`
  is the source of truth for how far it got.
- **The MAME conversions are MAME's reading, not ours,** except where a sheet was read.
  Verified: all sixteen pass `build_board_nets.py` with no problems; Tank's four sheets were
  read in full and every disagreement found is corrected and logged; Barrier was compared
  net for net and Star Castle's sheet 2 net for net. Not verified: the other twelve sound
  boards against their sheets; Tank's cable contacts where the two boards' sheets disagree
  (VLD1 and /FIRE1); the MFC6040 pinout against a Motorola data sheet (it is read off four
  places on Tank's two boards, which agree); the 8277's pinout (MAME's, marked "FIXME" there);
  and whether Tank's two 25c/50c switches are one part. The sheet readings themselves were
  done by four parallel readers and spot-checked by eye at the points that changed the
  netlist (B6, the antenna, the oscillator, the score counters, HD1/HD2, the ROM's -12V,
  C51), not at every point.
- None of the MAME conversions is redrawn in KiCad or published; they are netlists only.
- **The MAME PCB layouts are a parser's reading of hand-drawn ASCII.** About fifteen were
  read against their source by eye while the parser was built, and `check_pages.py` proves
  each label sits where the page says; neither proves a label is a part or that a kind is
  right. 7,503 devices are "other" (op-amps, drivers, regulators and words the patterns do
  not know), and outline-drawn sketches (`kurukuru.cpp`, `funworld.cpp`) lose names split
  across lines. Title-scoped layouts were spot-checked, not audited.

## Submissions — the one write path

`/api/submit` (`src/submit.js`) is the only endpoint in the Worker with a side effect.
It takes a reader's document and commits it to a **separate** GitHub repository named by
`SUBMISSIONS_REPO`, then opens an issue against it for triage.

Why the decisions are what they are:

- **A different repo, not this one.** CI builds and deploys whatever is committed under
  `web/`. A public form that can write to this repository is a form that can write to the
  thing that deploys. The queue repo has no CI and nothing reads it automatically.
- **One commit per submission, via the git data API.** The contents API is one commit per
  file, which scatters a submission across the log. Blobs go up first, then a tree, then a
  commit, then the ref. The ref update is retried on 409/422 because two submissions can
  land at once; the blobs survive the retry.
- **A repo with no commits refuses the git data API entirely.** Not just the ref —
  `POST /git/blobs` itself answers `409 Git Repository is empty`, so this cannot be
  handled at the ref, which is where the first attempt put it. The contents API *does*
  work on an empty repo, so the first submission lays down a README through it and then
  retries. This is the state every fresh deployment starts in, and it was a live bug:
  the endpoint went out configured and the first real submission failed on it.
- **An empty queue repo has no ref either.** Once seeded, the first submission still has
  to create `refs/heads/main` rather than patch it, with no `parents` and no `base_tree`.
- **The commit is the submission; the issue is only a handle on it.** If issue creation
  fails the reader is still told it worked, because it did. Do not reorder these.
- **20 MB a file, 25 MB a submission.** The binding constraint is the Worker's 128 MB of
  memory, not the platform's 100 MB request limit: the file is held as bytes *and* as
  base64 to reach the blob API. `toBase64` chunks at 32 KB because
  `String.fromCharCode(...bytes)` blows the argument limit around a megabyte. Anything
  larger is taken as a link.
- **Extension allowlist checked against magic bytes.** An upload claiming `.pdf` has to
  start `%PDF`. Filenames are stripped to `[A-Za-z0-9._-]`, cannot start with a dot, and
  are placed under a generated `incoming/<date>-<machine>-<token>/files/` prefix, so no
  submitted name can escape its directory.
- **Guards.** Per-IP rate limit (the `SUBMIT_LIMIT` unsafe binding — `period` accepts only
  10 or 60), an off-screen honeypot field, and Turnstile *only* when both
  `TURNSTILE_SITEKEY` and `TURNSTILE_SECRET` are set, so a half-configured challenge
  cannot lock the form.
- **`gh()` reads the body as text before parsing.** A body-less 2xx — which the ref update
  can be — is not a parse failure. This was a real bug.
- **The front end uses XHR, not fetch,** because `fetch()` cannot report upload progress
  and these are slow uploads over whatever wifi is in the building.

Local `wrangler dev` cannot start on this machine (Node 26 + miniflare, `spawn EBADF`),
so the endpoint is exercised with a stub-`fetch` harness against `src/submit.js` directly
and the form against a small static server. `npm run check` still validates the config
and the bindings.

Contact details a submitter leaves end up in the queue repo and its issues. That is the
reason the queue repo is private, and the form says so where the field is.

## Deployment — Workers Builds

The site builds from GitHub (`stoatworks-labs/cathode-ray-tomes`, public) via Cloudflare
Workers Builds. Three commands are configured, and the third is the one that bites:

| Setting | Value |
|---|---|
| Build command | `npm ci` |
| Deploy command (production branch `main`) | `npx wrangler deploy` |
| Version command (**every other branch**) | `npx wrangler versions upload` |

If the Version command is left as plain `wrangler deploy`, a build on *any* branch
publishes straight to the live Worker. `versions upload` uploads a preview and leaves
production alone.

**CI builds and deploys whatever is committed under `web/`,** corpus included. There is
no separate publish step and no out-of-band upload: run `python3 tools/build_assets.py`
after an ingest or a board change, commit the result, and the push deploys it. CI has no
access to `cache/` and never needs it.

Live at **cathode-ray-tomes.com**, with `cathode-ray-tomes.allan-sargeant.workers.dev`
deliberately kept alive beside it — the apex domain is newly registered and some network
filters block it.

The project was called *Bezel* until it was renamed to **Cathode Ray Tomes**; if you find
a stray `bezel` string outside `cache/` and `data/index/postings/`, it is a leftover.
(`data/index/postings/b.json` legitimately contains the word — it is OCR'd corpus text,
not a reference to the project.)

Renaming the project directory means stopping `ingest.py` and `backfill_structure.py`
first: both resolve `ROOT` at import and would write to the old path. Both are
checkpointed, so they resume cleanly afterwards.
