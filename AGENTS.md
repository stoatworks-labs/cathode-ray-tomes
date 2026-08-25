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

**The grid alphabet skips G, I, O and Q**: A B C D E F H J K L M N P R. The board
definitions used to carry G and Q as rows, which put every device below F at the
wrong height. Three independent confirmations — nothing in any read, signature or
signal record in this repo sits in a G or Q row while both neighbours of each are
populated; and the sheets' own spanning designators treat F/H and H/J as adjacent
pairs, which a 24-pin DIP on a 0.75in row pitch requires. Pong predates the
convention and legitimately uses G.

## Traps that have already bitten

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

**Assumed / not yet done:**
- **Pong nets are not traced.** The schematic shows placed devices, not wired circuitry.
  Sheet 002826 Rev E is the source; start with the power rails and the H/V sync chains.
- The `7425` and `7450` symbols are hand-created from TI datasheets and have not been
  exercised in a wired design.
- `LM309K` vs `LM305K`: schematic 002826 says LM309, assembly A001433 says LM305K. The
  KiCad project uses LM309K. This discrepancy is real and unresolved — worth surfacing.
- Nothing has been checked against physical hardware.
- The full-corpus ingest was still running when this was written; `data/ingest-state.json`
  is the source of truth for how far it got.

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
