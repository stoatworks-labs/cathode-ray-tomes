# External sources

Cathode Ray Tomes is built from one corpus: ArcadeRTFM's scans, keyed to MAME's
machine metadata. This note records two other archives that have been surveyed,
what each of them actually holds, and — for each — whether taking it is a
technical question or a rights question.

**The console decision has been taken, and the whole of GamingDoc is on the
site**: all 43 documents, 2,772 pages. The SNK MV2F/MV4F service manual sits on
two arcade machines that already existed with nothing on them; the other 42 are
console and handheld documents across eleven systems.

```bash
python3 tools/survey_gamingdoc.py            # -> data/sources/gamingdoc.json
python3 tools/survey_console5.py             # -> data/sources/console5.json
python3 tools/survey_console5.py --offline   # cross-reference only, no requests
```

Both are re-runnable. `survey_gamingdoc.py` caches PDFs under `cache/gamingdoc/`
and crawls serially with a delay; GamingDoc is a small non-profit archive with a
download limiter, not a CDN. `survey_console5.py` makes about a dozen API calls
and downloads no page content at all.

Prefer `--offline` for Console5. It recomputes the IC cross-reference from the
stored catalogue, which is what changes: the boards in `data/chips/` gain entries
weekly, the wiki's IC pages do not. Console5 sits behind Cloudflare and has
returned 403 to this script after a single day's use — that is an answer, not an
obstacle. Do not route around it.

## GamingDoc — a different kind of scan

<https://gamingdoc.org/> · 43 PDFs · 2,772 pages · 322 MB

The README's measurement of the ArcadeRTFM corpus is stark: of 2,405 PDFs, zero
have a text layer and zero contain vector artwork. Every page is a flat raster
image, which is why the pipeline is built the way it is.

GamingDoc is not like that. **37 of its 43 PDFs carry a text layer, and 1,413
pages are native vector.** The Sony service manuals are the reason to care: the
SCPH-30000 PS2 manual is 78 of 82 pages of native vector with selectable text,
and its schematic sheets carry net names, reference designators and component
values as real text rather than as ink.

Two consequences, both of which cut against assumptions baked into the current
tooling:

- **`vectorise.py` is the wrong tool for these.** It traces bilevel line art and
  recovers geometry, not meaning, and the README's own measurements show tracing
  loses to raster on bytes. None of that applies to a page that was vector to
  begin with — it renders to SVG directly, small and clean, with no scan noise
  to despeckle.
- **The parts lists are already structured.** A single regex over the text layer
  lifts 20,507 electrical-parts-list rows — designator, Sony part number,
  description, metric package code — across 22 manuals. That is the artefact
  `extract_parts.py` reconstructs from OCR for arcade boards, arriving without
  transcription error.

`data/sources/gamingdoc.json` assigns every document an `ingest` class, because
they do not all take the same path:

| class | docs | pages | what it needs |
|---|---|---|---|
| `vector` | 24 | 1,464 | text and SVG extracted directly; skips `ingest.py` |
| `text` | 13 | 576 | raster pages, text layer already applied upstream; rasterise only |
| `ocr` | 6 | 732 | no text layer; the existing `ingest.py` path |

Alongside the PDFs, GamingDoc publishes recap lists for **29 board revisions** —
465 rows of designator, value and voltage, as real HTML tables rather than
scans. The inventory records the count and the page, not the rows: every one of
those tables is credited to Console5, and Console5 has reserved its rights. See
below.

### The one arcade item

GamingDoc's entire arcade holding is the SNK **MV2F/MV4F service manual** — 22
pages, a flat scan, `ingest: ocr`. It is also the only document in the survey
that lands on machine slugs we already carry: `ng_mv2f` and `ng_mv4f` both exist
in the index with zero documents, and of 143 SNK machines only 16 have any
documentation, none of it covering the MVS motherboard itself.

That makes it the one item requiring no schema decision at all, and it is now on
the site: 22 pages OCR'd, 26 sections, both machines listing it.

Getting it there needed one piece of plumbing. `data/machines.raw.json` is
refetched from arcadertfm and overwritten, so a hand-added document has to live
somewhere that survives — `data/extra-docs.json`, which `build_index.py` merges
in. An overlay entry names every machine slug it covers, so one manual can sit
under several machines without being catalogued twice; the reader links all of
them, and credits the source on the document itself rather than leaning on the
footer's blanket ArcadeRTFM attribution.

```bash
python3 tools/build_index.py                  # merges data/extra-docs.json
python3 tools/ingest.py --only ng_mv2f        # 22 pages, the flat-scan path
python3 tools/build_search.py
python3 tools/build_doc_stats.py
python3 tools/build_assets.py
```

The PDF itself still has to reach R2 before `/pdf/<id>` resolves — that is
`tools/publish.sh remote`, from a workstation, as with everything else.

Everything else in the survey is a console, and a console is not a MAME arcade
machine — which is the next section.

### Reading a vector manual: `tools/ingest_vector.py`

It writes the same `cache/text/<id>.json` the OCR path does, so build_search, build_doc_stats,
build_assets and the reader are unchanged — only line extraction differs
(`pdftotext -bbox-layout` instead of tesseract), and the heading classifier,
running-header filter and block builder are reused verbatim.

```bash
python3 tools/ingest_vector.py --doc <id>     # from data/sources/gamingdoc.json
python3 tools/ingest_vector.py --all          # every document classed `vector`
```

| manual | pages | sheets | words | sections |
|---|---|---|---|---|
| SCPH-30000 (PS2, 6th ed) | 82 | 49 | 52,241 | 30 |
| CECHG (PS3, 2nd ed) | 45 | 26 | 14,846 | 10 |
| SCPH-9000 (PS1, 3rd ed) | 28 | 12 | 16,602 | 12 |
| SCPH-70000 (PS2 slim) | 26 | 13 | 24,333 | 2 |
| PSP-2000 | 24 | 16 | 7,824 | 8 |

**The sheet text is the prize.** A schematic page comes back as
`R328 47k DIG_+1.8V2 … C343 0.1u B … IC104 394 pin … /CS8 238 SA26 247` —
designators, values, net names and pin numbers, exact rather than guessed. The
arcade corpus has nothing like it at any price.

**Three things measured that were not obvious:**

- **SVG is not a size win against a reading image, and is against a usable
  one.** For the five densest SCPH-30000 sheets, gzipped SVG is 3.0 MB against
  2.0 MB for the 150 dpi WebP (1.49×) but 4.9 MB for the 300 dpi WebP (0.62×) —
  and 300 dpi is what `ingest.py` already renders for schematic-bearing
  documents, because 150 dpi is not something you can follow a trace on. So SVG
  wins where it counts, and is resolution-independent besides. This is a better
  result than tracing gave (README: 109–267 KB traced against 68–174 KB raster)
  and for a different reason — there is no scan noise in the path data.
- **A text layer can be present and unreadable — but check *why* before
  believing it.** The SCPH-70000 measured 3.6% U+FFFD, 58% on its worst page,
  and this note used to conclude that its fonts were subsetted without a
  ToUnicode map and that "above a few percent a document wants the OCR path
  instead". Both halves were wrong, and the second would have made the document
  worse: its parts list is exact Sony part numbers, and OCR would have guessed
  at them.

  What actually happened is a fallback firing on the wrong document. Twenty-two
  glyphs in a symbol font on page 4 have no Unicode mapping, and poppler writes
  those as raw C0 control bytes — which are not legal XML, so `ET.fromstring`
  refused the file, the `pdftocairo -pdf` rewrite below ran, and *that* dropped
  the Adobe-Japan1 CMap the pages 19-26 parts list is set in. Twenty-two
  unreadable characters on one page cost the document five thousand words on
  seven others. `bbox_xml` now neutralises those bytes to U+FFFD before
  parsing, the rewrite stays reserved for what it was written for, and the
  document reads at 0.02% undecoded — the µ and Ω that genuinely have no
  mapping, and nothing else.

  The lesson is not about this file. `meta.undecoded` was recorded correctly
  and the tool printed its warning, and the document shipped anyway for as long
  as it was on the site, because a warning on a build that prints a hundred
  lines is not a control. `tools/check_pages.py` is the control.
- **poppler crashes on one of them.** The SCPH-9000's Producer string is
  mojibake and `pdftotext` dies writing the XML header with an uncaught
  `std::out_of_range`, truncating its output and exiting 0. Rewriting the file
  through `pdftocairo -pdf` drops the metadata and all 28 pages then extract.

**Where it is weak.** Deciding which pages are drawings is a fresh problem here:
`build_drawings.py` answers it from OCR debris, and a vector page has none. The
signal is structural instead — a sheet is hundreds of one-word blocks — and
against the SCPH-30000 read by hand it finds 47 of 64 drawings and wrongly hides
none. The 17 it misses are mixed pages, a drawing beside a real CAUTION
paragraph, which keep their text. That is deliberately the same trade
`build_drawings.py` makes: hiding a parts list is worse than showing a drawing's
labels. Getting there needed a second signal — words per block — because the
PSP-2000's parts lists have cells too short to read as prose and the first rule
hid all four pages of them.

Outline quality is the honest weak point. These manuals head their sections
`SECTION 5` / `ELECTRICAL PARTS LIST` and set them barely larger than body text,
so a classifier tuned on arcade scans under-reads them; the manual's own table
of contents is a better source and is not used yet.

### Everything GamingDoc has is here

All 43 documents, 2,772 pages. The first pass held back thirteen of them on the
grounds that "the purpose is troubleshooting, not reproduction" — five developer
manuals (the PS1 MIPS reference and runtime library overview, the three SNES
books) and eight installation guides for modchips and optical-drive emulators.
That was overruled in favour of completeness, which is the right call for an
archive: the argument for leaving them out was about what the *site* is for, and
it was being used to decide what the *corpus* contains. Those are different
questions.

They are typed rather than filtered, which does the same job without losing
anything. `Developer Manual` and `Installation Guide` sort after every kind of
service material, so a machine page reads service manuals first and someone with
a dead console never has to scroll past a MIPS instruction set to reach them.

Two documents carry a `note`, shown at the top of the reader, because their
filing is misleading and a type cannot say so:

- The **MIPS instruction set reference** is MIPS Technologies' own MIPS32
  manual. The PS1's R3000A is MIPS I, an earlier architecture — most of it
  applies and not all of it, and it is not a Sony document.
- The **Dreamcast switching power supply control** document is a component
  datasheet for the PSU controller, not a Sega document.

### How consoles are carried

Not as a second entity. A console has no romname and no DIP banks, and what
identifies one is a board revision rather than a driver — but it is the same
*kind of thing* to a repairer, so it lives in the same index with `kind` set,
and every route, view and search path it needs already existed.

| | arcade machine | console |
|---|---|---|
| source | `data/machines.raw.json` (MAME) | `data/systems.json` (by hand) |
| identified by | romname | board revision |
| `p` in the browse index | DIP banks | board revisions |
| `t` in the browse index | absent | `console` / `handheld` |

`data/systems.json` is written by hand rather than derived. MAME has console
drivers, but they describe an emulation target: the thing a repairer needs —
which chassis a model number is, which board is inside it — is not in them.

### Two bugs this shook out

**`ingest.py` overwrote sixteen vector documents with worse OCR.**
`ingest_vector.py` did not write to `data/ingest-state.json`, so `ingest.py`
saw those documents as un-ingested and re-read them through tesseract. The
SCPH-30000 went from 52,241 exact words to 22,164 guessed ones. It now
checkpoints, and `ingest.py` independently refuses any document whose cache
says `via: vector` — a state file can be copied between trees and go stale, so
one guard was not enough.

**The tokeniser could not hold a part number together.** `[a-z]{3,}` was tried
before the part-number branch, so `CXD9615GB` — printed on the chip, and the
thing someone with a dead PS2 actually types — indexed as `cxd` and `9615gb`
and the search found nothing. Trying the part-number branch first, with up to
four leading letters, fixes it: that term now returns six documents, and the
arcade side is unchanged (`7400` still returns the same 157 documents in the
same order). Hyphenated board numbers are still split — `TA-085` indexes as
`085` — because the token charset has no hyphen in it, and widening that is a
larger change than it looks.

### What consoles cost

Less than expected, because the model absorbed them rather than being extended
for them. The whole change is one new data file, a merge pass in
`build_index.py`, a `kind` query parameter on `/api/machines`, and the front-end
bits that follow from having a kind at all: a badge, two filter chips, board
revisions where DIP switches would be, and copy that no longer says "arcade" on
a page that might be a PlayStation.

What it does cost is 93 MB of page scans. Every vector schematic sheet is
published as a WebP so the reader can show it, which is 420 files across 21
documents — more than the 430 already in `web/pages/` for the whole arcade
corpus, because an A3 schematic sheet at 150 dpi is a much larger image than a
letter-size drawing. The SVGs are rendered into `cache/svg/` and not yet served;
what to do with them is an open question, and the measurements are above.

Board revisions are listed on the system record but are not entities. A document
attaches to a console, not to a GH-010, which is right for a service manual
covering a series and wrong for the day someone wants the recap list for one
board. That is where Console5's material would go, if it ever could.

## Console5 — the actual upstream

<https://wiki.console5.com/wiki/> · 931 pages · 446 IC pages · 1,595 images

Every capacitor list and every Dreamcast schematic on GamingDoc is credited
"Source: Console5". GamingDoc is the mirror; this is the origin, and it is
considerably larger than the slice GamingDoc republished.

**It is not available for the taking, and the survey is built to reflect that.**
Console5's `robots.txt` carries an express reservation — `ai-train=no`,
`use=reference`, ClaudeBot disallowed outright — and the wiki exists to support
the Console5 store, where every capacitor list sits beside a "Purchase these
parts as a kit" link. Copying those lists would take the shop's catalogue and
drop its commerce. `data/sources/console5.json` therefore stores titles, sizes,
categories and URLs, and no page content. If any of it is ever worth carrying,
that is a conversation with Console5, not a scrape.

### The IC cross-reference

One thing is worth wiring up without carrying a byte of their text. Console5 has
446 pages that are each a one-line function description plus an ASCII pinout,
keyed by part number — including Sega and Atari customs (`315-5313`, `137170-001`)
that have no datasheet anywhere.

Our boards in `data/chips/` know that a 74LS163A sits at A5. They know nothing
about what a 74LS163A *does*. Matching the two covers **1,697 of 2,368 IC
placements across the hand-built boards — 75 of 194 distinct part numbers** — and
turns a designator into a part with a pinout one link away.

Matching normalises away vendor prefixes (`SN`/`DM`/`MC`) and family letters
(`LS`/`S`/`HC`), because a 74LS157 and a 74157 share a pinout. That equivalence
is the only claim `icCrossref` makes; it says nothing about timing or drive.

### Arcade material worth knowing about

Console5 is console-first but not console-only, and some of what it has is
squarely ours:

- **Category:Arcade** (14 pages) — CPS1, CPS2, Sega Naomi, Naomi 2, ST-V,
  Atomiswave, Taito B System, Taito F3, Namco NA-1/NA-2 and ND-1, Sammy/Seta/Visco
  SSV, Midway audio boards, Astro City, Neo Geo MVS.
- **Category:Arcade Monitor** (4 pages) — Wells-Gardner K7000, Hantarex Polo,
  TC-RM251s, TC-RM25T. Monitor chassis are a real gap: the corpus documents
  monitors only where a game manual happens to include the chassis drawings.

## Three more archives, surveyed the same way

Surveyed in September 2026, after the corpus had taken everything ArcadeRTFM
holds. Each survey records pointers and measurements and takes no document.

```bash
python3 tools/survey_archive_org.py              # -> data/sources/archive_org.json
python3 tools/survey_archive_org.py --metadata   # per-item file lists, ~40 min, resumable
python3 tools/survey_arcarc.py                   # -> data/sources/arcarc.json
python3 tools/survey_segaretro.py                # -> data/sources/segaretro.json
```

The headline is that the arcade documentation world is mostly one corpus
mirrored around. ArcadeRTFM, the Internet Archive's `arcademanuals` collection
and the Arcade Archive at XMission hold the same files under the same names,
uploaded by different people in different years. What each adds on top is
smaller than its size suggests, and it is different in each case.

| archive | PDFs | size | same file as ours | new to us |
|---|---|---|---|---|
| Internet Archive `arcademanuals` | 4,753 items | 165 GB stored, 16 GB of original PDF in the new items | 2,065 | 2,696 |
| Arcade Archive (arcarc.xmission.com) | 3,709 | 9.6 GB | 2,440 | 1,269 |
| Sega Retro | 12,737 | 99 GB | — | 63 service documents |

Only six of the Arcade Archive's new files also appear among archive.org's, so
the two sets barely overlap: together they are about 3,950 documents the corpus
does not have.

### Internet Archive — `arcademanuals`

<https://archive.org/details/arcademanuals> · 4,753 items · three upload waves
(2011, 2017, 2025) by different people from their own collections.

It holds **2,065 of our 2,405 documents under the same filename**, including
five of the sixteen the ingest could not read — three that arrive unreadable
from ArcadeRTFM and two that ArcadeRTFM has since lost. That is a second home
for the corpus that costs no upload, and `mirrors` in the survey output maps
our document ids to the archive.org items that carry them. Any item's files are
served directly at `https://archive.org/download/<identifier>/<file>`, which
is the whole of the "archive.org as a CDN" question: a fallback for `/pdf/<id>`
when the source is gone, and a primary for those five, wired up by reading that
map. It is not a CDN in the performance sense — no SLA, periodic slowness,
occasional outages — so it is a fallback, not a replacement for the redirect.
Uploading our own copies of the 340 not found there is possible through the
S3-style API but is a rights decision, not a technical one; the collection's
items carry no licence and are private uploads of publisher-copyright manuals,
the same footing as everything else here.

Two things the archive does that ArcadeRTFM does not. It **runs its own OCR**
over every upload and publishes the result beside the scan (`_djvu.txt`,
`_text.pdf`; 2,670 of the 2,696 new items have it): a second, independent reading of the same page, which is exactly
the cross-check `build_drawings.py` lacks. And its titles carry the machine
name in the clear, so the 2,696 new items match MAME machines by name: 1,707
of them land on a machine (873 on the whole title, the rest on a leading
run), and 367 machines would gain their first document. By kind, reading
the titles: 1,798 manuals, 206 schematics, 136 DIP and pin-out sheets, 70
parts lists, and 143 that are pinball, which is out of scope.

### Arcade Archive — arcarc.xmission.com

A plain Apache file tree run by one volunteer at XMission, sorted into
manufacturer and subject directories. No robots.txt, no API, no licence
stated; the survey walks the 233 directory listings and reads no file.

Its 3,709 PDFs are mostly ours already — 2,440 share a filename — and what is
new is mostly *not game manuals*: 320 jukebox, 247 monitor chassis, 106 coin
mechanism, 89 laserdisc-game and 60 more arcade documents, plus DIP-switch
sheets and electronics references. The monitor and coin-mech material is the
interesting part: the corpus documents a monitor only where a game manual
happens to include the chassis drawings, and someone at a dead cabinet needs
the chassis manual as often as the game's. 256 of the new files match a
machine name and 46 machines would gain a first document.

Taking from it is a courtesy question before a technical one — a single
maintainer's mirror, reached at arcarc@xmission.com — and the survey exists so
that conversation can start from numbers.

### Sega Retro

<https://segaretro.org/> · 12,737 PDFs · 99 GB, through the MediaWiki API.

The robots file carries the same express reservation Console5's does
(`Content-Signal: search=yes, ai-train=no, use=reference`), so this is pointers
only, on the same terms as Console5. Read by filename, it is 5,522 game
instruction manuals, 1,480 flyers and 1,138 arcade-system documents, of which
**63 are service material** — and those are the ones nobody else has: the
NAOMI, NAOMI 2 and GD-ROM service manuals, Atomiswave, Lindbergh, the Master
System and Mega Drive service manuals by revision, the Out Run and Hang-On
schematics. The survey lists the 1,201 service and arcade-system files with
their URLs and leaves the rest as counts.

### What to take next, if anything

In order of value per document: the Sega system service manuals, if Sega
Retro agrees; the Arcade Archive's monitor and coin-mech references, if its
maintainer does; then the archive.org items that would give a machine its first
document. The archive.org OCR text is worth reading against ours before any of
that, because it costs nothing and would tell us which of our 65,000 pages
tesseract read worst.

## Rights, stated plainly

The two sources sit differently and should not be treated the same way.

**GamingDoc** re-hosts other people's manuals, states no licence, and asks to be
contacted about takedowns. That is the same footing the project already stands on
with ArcadeRTFM. It is worth noting that Sony service manuals for hardware still
within living memory are defended more actively than 1980s Atari drawings, so
this should be a deliberate decision rather than an inherited one.

**Console5** has expressly reserved rights and sells the thing its wiki
documents. Link to it, credit it, and cross-reference against it. Do not mirror
it.
