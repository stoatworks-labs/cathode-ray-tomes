# Cathode Ray Tomes

> **AI-assisted project.** This codebase was created with [Claude](https://claude.com/claude-code)
> (Anthropic), directed and reviewed by a human author.
> I've run the corpus index, the ingestion pipeline and the web application end to end against
> the real ArcadeRTFM corpus. The Pong KiCad conversion has a verified component complement and
> BOM, but only eight of its signal nets (the video output chain) have been traced, and nothing
> here has been checked against physical hardware.

Modern, searchable editions of service documentation: arcade boards, and the
consoles that came after them.

**It's here to help you fix boards.** The board conversions are
diagnostic aids. They answer "which chip is at C4, what does it do, and am I even
looking at the right revision", and they aren't trying to be complete clones.
A partial complement that gets you to the right chip is useful; a complete one
that's wrong about your board revision isn't. That's why Asteroids ships as
four separate boards rather than one averaged guess.

Arcade service manuals survive almost entirely as flat scans: page images with no text
layer, no structure and no way to search them. Cathode Ray Tomes rebuilds them as web
documents, with every page OCR'd and searchable, every machine cross-referenced against its
hardware specification and DIP switch settings, and (for a small number of boards) the
schematic rebuilt as a proper KiCad project with an accurate bill of materials.

Console service manuals are a different problem, and a much nicer one. Most of them
are native vector with a real text layer, so their schematic sheets already carry
designators, values and net names as text rather than as ink, which leaves nothing to OCR
and nothing to trace. Eleven consoles and handhelds are here, with 42 documents between
them; see `docs/EXTERNAL-SOURCES.md` for where they came from.

Not all of those are service manuals, and they don't pretend to be. Development
manuals and modchip installation guides have their own document types and sort after
every kind of service material, so a machine page shows the service manuals first.

## What the corpus actually is

I measured this rather than assuming it, from `https://arcadertfm.com/machines.json` and the
PDFs themselves:

| | |
|---|---|
| Machines (MAME-derived metadata) | 7,812 |
| Machines with documents | 1,384 |
| PDFs | 2,405 (~4.7 GB) |
| Schematic / drawing / wiring documents | 506 |
| PDFs containing a text layer | **0** |
| PDFs containing vector artwork | **0** |

Every page of every document is a single embedded raster image: bilevel CCITT/JBIG2 at
200–300 dpi for line drawings, JPEG/JPX greyscale for photographed pages. One file was
authored in Adobe Illustrator 9 and still contains only a placed scan. That one fact
drives the whole design: text has to be recovered by OCR, and diagrams have to be traced.

## Layout

```
src/            Cloudflare Worker (API + asset serving)
web/            Static front-end: browse, reader, schematic + BOM viewers
tools/          Ingestion, indexing, search and vectorisation pipeline
kicad/          Hand-built KiCad conversions (one directory per board)
data/           Generated indexes (machines, docs, chips, postings)
cache/          Local ingest cache: PDFs, page images, OCR text (gitignored)
```

## Pipeline

```bash
python3 tools/build_index.py                    # normalise upstream metadata
python3 tools/ingest.py --workers 6             # fetch, rasterise, OCR, detect structure
python3 tools/backfill_structure.py [--force]   # add/refresh outlines on existing docs
python3 tools/detect_language.py                # which documents are not English
python3 tools/parts_rows.py --all               # re-read parts-list pages that lost their rows
python3 tools/build_search.py                   # sharded OCR postings + chip index
python3 tools/build_doc_stats.py                # fold page/section counts into the catalogue
python3 tools/build_drawings.py --images        # mark drawing pages; publish their scans
python3 tools/vectorise.py <docId> --pages 1,3  # trace line art to SVG
python3 tools/build_assets.py                   # assemble web/data/ for the deploy
python3 tools/check_pages.py                    # read what shipped; exit 1 on a bad page
```

`ingest.py` is resumable: finished documents are checkpointed in
`data/ingest-state.json` and skipped on a re-run.

## Notes on the hard parts

**The HTML manual is the main event, and the scan is the backup.** Each document is rebuilt
as a proper web page (headings, paragraphs, lists, callouts and tables), and that's what the
reader shows by default. The scan is kept as a "see original" reference for anything the OCR
couldn't carry.

That's what makes the whole thing cheap to serve. The full structured text and outline
for a 52-page manual is **24 KB gzipped**; the entire corpus of text is ~90 MB, which ships
as static assets beside the code. Page images, by comparison, would be 63,000 files and 8.9 GB.

**Two-column layout.** These manuals are set in two columns. Recognised lines have to be kept
in tesseract's own reading order, because sorting them top to bottom interleaves the columns
and turns the text into nonsense. This matters more than anything else for whether the output
is readable.

**Document structure.** The scans carry no font information, so headings are recovered
from geometry: tesseract emits word boxes alongside the text in a single pass, lines are
reassembled, and a line counts as a heading when it's set noticeably larger than the
document's own body text *and* reads like a heading (short, capitalised, often numbered
`A.` / `1.`). Contents pages and illustrated-parts-list pages are left out, because both set
their rows in large type and would otherwise flood the outline with entries pointing at
the sections they only reference. Headings wrapped across two lines are joined back up.

On the Asteroids TM-143 technical manual this recovers the actual structure (*Location
Setup → A. New Parts → B. Game Inspection → C. Game Installation → D. Self-Test Procedure
→ E. Game Play → Maintenance and Repair → A. Cleaning → B. Fuse Replacement → …*) from a
52-page scan with no text layer. That outline becomes the in-page navigation.

**Search.** Postings are built from the OCR text and sharded by leading character, so a
query only fetches the shards its terms touch and no single shard gets near the 25 MiB
limit on one static asset. Documents have to contain every term and are ranked by total
occurrences, so the manual that actually documents a part outranks a schematic that prints
it once in a corner. Searching `7400` finds the Pong schematic alongside every other board using that
chip, which is what a repair search actually looks like.

**OCR.** Quality follows the source scan. Dense schematic sheets return fragmentary text,
but helpfully still recover part numbers (`7400`, `74107`, `9316`), which is what a
repairer actually searches for. Typed manual pages come back clean.

**Tables and block order.** A page is stored as an ordered list of blocks, which is right
for prose and wrong for a ruled table: tesseract treats the vertical rule between two
columns as a block boundary, so flattening the page emits every item number, part number
and quantity first and every description afterwards. The parts extractor then pairs each
row's part number with the *next* row's item number, and 22% of recovered rows had no
usable description at all.

Nothing is lost, only unlabelled, because every cell still knows where it sat. `parts_rows.py`
re-reads those pages from their cached scans, bands the lines by vertical centre and
joins each row's cells back together, which is the shape the extractor already reads.
Both readings are then taken and the better one kept per page, scored on descriptions
recovered, so a page the banded read can't parse (Xevious prints no item-number
column, Tenpin prints its description first) keeps the flat one.

Its output lives in `cache/rows/`, which is **gitignored like the rest of the cache**.
Run it before `build_parts.py`, or the descriptions it recovered silently go back to
em-dashes on the next rebuild. It's incremental: 346 pages, six minutes cold, and
nothing on a re-run.

**A DIP-switch table arrived as a sentence, and nothing was feeding the machinery that
would have fixed it.** `build_blocks` has emitted a `tr` for any line carrying two or
more wide gaps since tables were added, and the reader splits a `tr` on those gaps into
cells. Nothing ever reached it: `ocr_page` built each line's text by joining tesseract's
words with single spaces, so the gaps that say where one cell ends and the next begins
didn't survive the read. 4-Player Football's option-switch page reached the reader as
`Off 70 seconds per coin F On 90 seconds per coin $ N` (two rows of a table set as one
paragraph), and every DIP-switch, option-switch and pin-out table in the corpus was in
the same state. Those are the pages a repairer actually opens.

The distances aren't subtle: on that page a word space is 8 pixels and the column gaps
are 43 to 251. What makes them unsafe on their own is that a gap wide enough to be a
column is also wide enough to be the hole OCR leaves where it dropped a word. So the
gaps are only a suggestion, and a cell start has to **repeat** down the page before a
split is kept. The Result column there begins at x = 459–462 on all nine of its rows,
while debris lands wherever it lands and gets dropped.

That repeat test is also the guard against the thing that must never happen. A page has to
show **three** columns before anything is split, because two is what two-column prose
looks like when tesseract reads across the gutter: those lines carry a single wide gap,
make two cells, and are left alone. On Hard Drivin' page 3-25 the flowchart boxes became
rows and the two columns of numbered prose beneath them didn't.

`page_tables.py` applies this to the corpus the way `parts_rows.py` applies its banding,
and for the same reason: `cache/text/` stores blocks, and the word boxes that say where
a cell began aren't in them, so the pages are read again from their cached scans. A page
is only kept if it gained a table **and** still says, word for word, what it said before,
which is what makes a 4,000-document backfill safe. A page whose re-read doesn't reproduce
its own published text didn't read the same way twice, and is left alone. The one
difference allowed is a word hyphenated across a line break, `Designator` becoming
`Desig-` / `nator` where the row broke out of its paragraph.

Its output is `data/tables/`, which unlike `cache/rows/` is **committed**, because
`web/data/doc/` is built from `cache/text/` plus the side-cars, and a gitignored one
reverts on the next rebuild with nothing to say it happened. It's merged in by
`build_assets.py --tables-only`, which leaves the corpus index alone for the same reason
`--boards-only` does. 12,145 pages across 1,810 documents are now set as tables, 244,719
rows, and `check_pages.py` reports the same as it did before.

**Not everything is in English.** 43 of these manuals are Japanese, and tesseract
run with `-l eng` doesn't so much fail on one as make things up: Super Puzzle Fighter's first
page came back as `yo09964Zd WO Ddivfay SARL 21 BHMGMII`, and with `-l jpn+eng` it's
`© CAPCOM CO., LTD. 1996 ALL RIGHTS RESERVED. 取扱説明書`. `detect_language.py` finds them
from the share of a document's prose that's English function words, then confirms by
re-reading one page in Japanese and counting the CJK. That's what tells a Japanese
manual from a parts catalogue, which is also short of function words but has no CJK at
all. The answer lives in `data/languages.json`, so the language is a property of the
document rather than a flag to remember.

Two things had to follow from that. `build_drawings.py` is calibrated on English OCR debris
and counts every kanji as a symbol, so a correctly read Japanese page scored 0.24-0.53
against a drawing threshold of 0.030 and would have been hidden for being legible.
And Japanese is written without spaces, so `build_search.py` indexes it as character
bigrams and the Worker splits a query the same way: 2,538 more terms for 0.8% more
index, with no dictionary and no segmenter.

**Checking what shipped.** Every check in the pipeline asks whether a document
*ingested*. `tools/check_pages.py` asks the next question: given what's in
`web/data/`, is there a page a reader would open and find unusable? It reads each page
the way the reader renders it and reports drawing debris set as prose, text the
extractor couldn't decode, a scan promised by `dw`/`dh` with no file behind it, a scan
published that no page points at, and a table row that can't be split into cells. It
exits non-zero when anything fires, so it belongs before a deploy rather than after one.

It exists because the alternative didn't work. The SCPH-70000's parts list shipped as
five thousand words of `U U U U U … C1692 C1693` for as long as the document was on the
site. The ingest had measured the problem, written it into the document's own metadata
and printed a warning, and the warning scrolled past in a build that prints a hundred
lines. It currently reports two one-cell table rows, which clear when those two
documents are next ingested.

**Drawing pages.** A page that's a drawing has no prose to rebuild, but OCR doesn't
return nothing for one. It returns the marks it found and calls them words. Rendered
as paragraphs, that reads as fluent nonsense, which was the worst thing on the site.
Those pages are now shown as the scan, with what OCR recovered kept underneath and
collapsed, because that's what the search index matched on.

Deciding which pages those are is the whole difficulty, and not because the nonsense
is hard to spot. Illustrated parts lists and DIP-switch tables score almost the same
as a schematic on any measure of how word-like the text is (they're part numbers and
abbreviations), and they're the most useful pages in the manual. So no page is hidden
on a score alone: the document's own outline heading, or the catalogue's record that the
document is a schematic package, has to agree with it. Pages where only the score
fires keep their text and are just marked as having come off a drawing.

**Vectorisation.** `tools/vectorise.py` traces bilevel line art to SVG. It recovers
**geometry, not meaning**: it doesn't recognise a resistor and redraw it as an IEC
symbol. Turning a traced diagram into standard schematic symbols is recognition work,
done by hand per diagram.

Measured properly, tracing *isn't* a size win. Per page of the Asteroids manual:
whole-page trace 109–267 KB gzipped, figure-only trace ~63 KB, the 150 dpi WebP 68–174 KB.
Traced scans are path-heavy because every stroke edge carries scan noise; despeckling and
tracing at 200 dpi roughly halves it, but raster still wins on bytes. What vector buys you
is resolution independence and theme-awareness, not smaller files. (The one exception is a
dense, line-dominated schematic sheet, where the earlier Pong measurement favoured SVG,
and that result doesn't generalise.)

**KiCad conversion.** There's no tool that turns a 1974 Atari drawing into a netlist, so
each board is built by hand. Each conversion says on the site whether its nets have been
traced or only the component complement captured.

## Deployment

The Worker and static assets build from GitHub via Cloudflare Workers Builds on push to
`main`. The corpus ships with them: `tools/build_assets.py` assembles the indexes and documents
in `web/data/`, the page scans the reader shows sit in `web/pages/`, and both are committed, so
a deploy publishes code and corpus together. Original PDFs aren't hosted; `/pdf/<id>`
redirects to the source archive. CI never touches `cache/`.

```bash
npm ci                 # install pinned wrangler
npm run check          # validate config without deploying
npm run dev            # local worker + assets on :8787
npm test               # submit endpoint + Worker routing, no wrangler needed
```

`npm test` runs the Worker against a stubbed ASSETS binding. That's worth
having because `wrangler dev` can't spawn workerd on every machine, and a
Worker change that ships unexercised is how `not_found_handling:
single-page-application` turned every unknown id into a 500 for months. The
stub reproduces that fallback, so the routing cases fail without the fix.

## Submissions

`/submit` takes a document the corpus doesn't have (a scan, a schematic sheet, or a link
to one) and commits it, with whatever the sender knows about where it came from, to a
separate queue repository. Nothing submitted appears on the site: a person reads it,
checks it, and then runs it through the same ingest and indexing path as everything else.

The queue is a *different* repository from this one on purpose, so unvetted uploads never
sit in the tree Workers Builds deploys. Setting it up is three things:

```bash
gh repo create stoatworks-labs/cathode-ray-tomes-submissions --private
gh label create submission -R stoatworks-labs/cathode-ray-tomes-submissions
# Fine-grained PAT on that repo alone: Contents read+write, Issues read+write.
npx wrangler secret put GITHUB_TOKEN
```

Then set `SUBMISSIONS_REPO` in `wrangler.jsonc` to point at it. Without the secret, the
endpoint reports itself disabled and the form says so rather than failing on send.

The repo can be empty, because the first submission creates `main`. Issue creation is
best-effort: if it fails, the document is still committed and the sender is still told it
worked, because it did.

Uploads are capped at 20 MB a file and 25 MB a submission (the ceiling is the Worker's
128 MB of memory, since the file is base64'd to reach the git blob API), and anything
larger is taken as a link instead. The guards on a form that commits to a repository are a
per-IP rate limit, a honeypot field, an extension allowlist checked against the file's
own magic bytes, and optionally Cloudflare Turnstile if `TURNSTILE_SITEKEY` and
`TURNSTILE_SECRET` are both set.

## Sources

Scanned documents from [ArcadeRTFM](https://arcadertfm.com/). Machine hardware metadata
derived from [MAME](https://www.mamedev.org/). Manuals remain the property of their
respective publishers and are presented for preservation and repair reference.

GamingDoc has been taken whole: the console documents above, and one SNK arcade manual.
The Console5 Tech Wiki, the Internet Archive's `arcademanuals` collection, the Arcade
Archive at XMission and Sega Retro have been surveyed but not ingested.
`docs/EXTERNAL-SOURCES.md` records what each holds, what it would cost to take, and where
the answer is "link to it, don't mirror it". The measured inventories live in
`data/sources/` and are rebuilt by the `tools/survey_*.py` scripts.

<!-- attributions:start -->
This project is built on other people's work — see [ATTRIBUTIONS.md](ATTRIBUTIONS.md).
<!-- attributions:end -->
