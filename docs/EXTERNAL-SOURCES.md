# External sources

Cathode Ray Tomes is built from one corpus: ArcadeRTFM's scans, keyed to MAME's
machine metadata. This note records two other archives that have been surveyed,
what each of them actually holds, and — for each — whether taking it is a
technical question or a rights question.

One document has been taken: the SNK MV2F/MV4F service manual, which lands on
two machines that already existed with nothing on them. Everything else is
inventoried and left where it is, so the decision can be made against
measurements instead of impressions.

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
machine.

### Reading a vector manual: `tools/ingest_vector.py`

Built and measured against five of them; nothing is on the site. It writes the
same `cache/text/<id>.json` the OCR path does, so build_search, build_doc_stats,
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
| SCPH-70000 (PS2 slim) | 26 | 13 | 23,217 | 14 |
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
- **A text layer can be present and unreadable.** The SCPH-70000's fonts are
  subsetted with no usable ToUnicode map, so 3.6% of its characters — 58% on its
  worst page — come back as U+FFFD, correctly positioned and meaningless. Four
  of the five are clean. `meta.undecoded` records it and the tool warns; above a
  few percent a document wants the OCR path instead.
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

### What consoles would cost

`build_index.py` reads `machines.raw.json` and stamps a `machine` slug onto every
document record; the browse index, the search postings and the reader all key on
it. A console does not fit that shape, and a board revision — PU-18, GH-010,
NUS-CPU-05 — is not a machine at all but a revision *of* one. Consoles need a
second entity alongside machines, and the front end currently says "Arcade
Service Documentation" on the masthead.

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
