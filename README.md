# Cathode Ray Tomes

> **AI-assisted project.** This codebase was created with [Claude Code](https://claude.com/claude-code).
> The corpus index, ingestion pipeline and web application have been run end-to-end against the
> real ArcadeRTFM corpus; the Pong KiCad conversion has a verified component complement and BOM
> but its nets have **not** been traced, and nothing here has been checked against physical hardware.

Modern, searchable editions of service documentation — arcade boards, and the
consoles that came after them.

**The purpose is troubleshooting, not reproduction.** The board conversions here
are diagnostic aids — they answer "which chip is at C4, what does it do, and am I
even looking at the right revision" — rather than attempts at a complete clone.
A partial complement that gets you to the right chip is useful; a complete one
that is wrong about your board revision is not. That is why Asteroids ships as
four separate boards rather than one averaged guess.

Arcade service manuals survive almost entirely as flat scans — page images with no text
layer, no structure, and no way to search them. Cathode Ray Tomes rebuilds them as web documents:
every page OCR'd and searchable, every machine cross-referenced against its hardware
specification and DIP switch settings, and — for a small number of boards — the schematic
rebuilt as a real KiCad project with an accurate bill of materials.

Console service manuals are a different problem, and a much better one. Most of them
are native vector with a real text layer, so their schematic sheets already carry
designators, values and net names as text rather than as ink — nothing to OCR and
nothing to trace. Eleven consoles and handhelds are here, with 42 documents between
them; see `docs/EXTERNAL-SOURCES.md` for where they came from.

Not all of those are service manuals, and they do not pretend to be. Development
manuals and modchip installation guides carry their own document types and sort after
every kind of service material, so a machine page reads service manuals first.

## What the corpus actually is

Measured, not assumed, from `https://arcadertfm.com/machines.json` and the PDFs themselves:

| | |
|---|---|
| Machines (MAME-derived metadata) | 7,812 |
| Machines with documents | 1,384 |
| PDFs | 2,405 (~4.7 GB) |
| Schematic / drawing / wiring documents | 506 |
| PDFs containing a text layer | **0** |
| PDFs containing vector artwork | **0** |

Every page of every document is a single embedded raster image — bilevel CCITT/JBIG2 at
200–300 dpi for line drawings, JPEG/JPX greyscale for photographed pages. One file was
authored in Adobe Illustrator 9 and still contains only a placed scan. This single fact
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
python3 tools/build_search.py                   # sharded OCR postings + chip index
python3 tools/build_doc_stats.py                # fold page/section counts into the catalogue
python3 tools/build_drawings.py --images        # mark drawing pages; publish their scans
python3 tools/vectorise.py <docId> --pages 1,3  # trace line art to SVG
bash    tools/publish.sh local|remote           # seed KV + R2
```

`ingest.py` is resumable — completed documents are checkpointed in
`data/ingest-state.json` and skipped on re-run.

## Notes on the hard parts

**The deliverable is the HTML manual, not the scan.** Each document is rebuilt as a real
web page — headings, paragraphs, lists, callouts and tables — and that is what the reader
shows by default. The scan is kept as a "see original" reference for anything the OCR
could not carry.

This is what makes the whole thing cheap to serve. The full structured text and outline
for a 52-page manual is **24 KB gzipped**; the entire corpus of text is ~90 MB, which fits
in KV. Page images, by contrast, would be 63,000 files and 8.9 GB.

**Two-column layout.** These manuals are set in two columns. Recognised lines must be kept
in tesseract's own reading order — sorting them top-to-bottom interleaves the columns and
turns the text into nonsense. This is the single biggest determinant of whether the output
is readable.

**Document structure.** The scans carry no font information, so headings are recovered
geometrically: tesseract emits word boxes alongside the text in a single pass, lines are
reassembled, and a line is treated as a heading when it is set noticeably larger than the
document's own body text *and* reads like a heading (short, capitalised, often numbered
`A.` / `1.`). Contents pages and illustrated-parts-list pages are excluded — both set
their rows in large type and would otherwise flood the outline with entries pointing at
the sections they merely reference. Headings wrapped across two lines are rejoined.

On the Asteroids TM-143 technical manual this recovers the real structure — *Location
Setup → A. New Parts → B. Game Inspection → C. Game Installation → D. Self-Test Procedure
→ E. Game Play → Maintenance and Repair → A. Cleaning → B. Fuse Replacement → …* — from a
52-page scan with no text layer. That outline becomes the in-page navigation.

**Search.** Postings are built from the OCR text and sharded by leading character, so a
query fetches only the shards its terms touch and no single index value approaches KV's
25 MB limit. Documents must contain every term and are ranked by total occurrences, so the
manual that actually documents a part outranks a schematic that prints it once in a
corner. Searching `7400` finds the Pong schematic alongside every other board using that
chip — which is what a repair search actually looks like.

**OCR.** Quality tracks the source scan. Dense schematic sheets return fragmentary text,
but usefully still recover part numbers (`7400`, `74107`, `9316`), which is what a
repairer actually searches for. Typed manual pages come back clean.

**Drawing pages.** A page that is a drawing has no prose to rebuild, but OCR does not
return nothing for one — it returns the marks it found and calls them words. Rendered
as paragraphs that reads as fluent nonsense, which was the worst thing on the site.
Those pages are now shown as the scan, with what OCR recovered kept underneath and
collapsed, because that is what the search index matched on.

Deciding which pages those are is the whole difficulty, and not because the nonsense
is hard to spot. Illustrated parts lists and DIP-switch tables score almost the same
as a schematic on any measure of how word-like the text is — they are part numbers and
abbreviations — and they are the most useful pages in the manual. So no page is hidden
on a score: the document's own outline heading, or the catalogue's record that the
document is a schematic package, has to agree with it. Pages where only the score
fires keep their text and are simply marked as having come off a drawing.

**Vectorisation.** `tools/vectorise.py` traces bilevel line art to SVG. It recovers
**geometry, not meaning** — it does not recognise a resistor and redraw it as an IEC
symbol. Converting a traced diagram into standard schematic symbols is recognition work,
done by hand per diagram.

Measured honestly, tracing is *not* a size win. Per page of the Asteroids manual:
whole-page trace 109–267 KB gzipped, figure-only trace ~63 KB, the 150 dpi WebP 68–174 KB.
Traced scans are path-heavy because every stroke edge carries scan noise; despeckling and
tracing at 200 dpi roughly halves it, but raster still wins on bytes. Vector buys
resolution independence and theme-awareness, not smaller files. (The one exception is a
dense, line-dominated schematic sheet, where the earlier Pong measurement favoured SVG —
that result does not generalise.)

**KiCad conversion.** There is no tool that turns a 1974 Atari drawing into a netlist.
Each board is hand-built. Conversions state plainly on the site whether nets have been
traced or only the component complement captured.

## Deployment

The Worker and static assets build from GitHub via Cloudflare Workers Builds on push to
`main`. The corpus is separate: indexes live in KV and page images/PDFs in R2, both pushed
from a workstation with `tools/publish.sh remote` after an ingest run — CI never touches
`cache/`.

```bash
npm ci                 # install pinned wrangler
npm run check          # validate config without deploying
npm run dev            # local worker + assets on :8787
```

## Submissions

`/submit` takes a document the corpus does not have — a scan, a schematic sheet, or a link
to one — and commits it, with whatever the sender knows about where it came from, to a
separate queue repository. Nothing submitted appears on the site: it is read by a person,
checked, and then run through the same ingest and indexing path as everything else.

The queue is deliberately a *different* repository from this one, so unvetted uploads never
sit in the tree Workers Builds deploys. Setting it up is three things:

```bash
gh repo create stoatworks-labs/cathode-ray-tomes-submissions --private
gh label create submission -R stoatworks-labs/cathode-ray-tomes-submissions
# Fine-grained PAT on that repo alone: Contents read+write, Issues read+write.
npx wrangler secret put GITHUB_TOKEN
```

The repo can be empty — the first submission creates `main`. Issue creation is best-effort:
if it fails the document is still committed and the sender is still told it worked, because
it did.

and `SUBMISSIONS_REPO` in `wrangler.jsonc` pointing at it. Without the secret the endpoint
reports itself disabled and the form says so rather than failing on send.

Uploads are capped at 20 MB a file and 25 MB a submission — the ceiling is the Worker's
128 MB of memory, since the file is base64'd to reach the git blob API — and anything
larger is taken as a link instead. Guards on a form that commits to a repository: a
per-IP rate limit, a honeypot field, an extension allowlist checked against the file's
own magic bytes, and optionally Cloudflare Turnstile if `TURNSTILE_SITEKEY` and
`TURNSTILE_SECRET` are both set.

## Sources

Scanned documents from [ArcadeRTFM](https://arcadertfm.com/). Machine hardware metadata
derived from [MAME](https://www.mamedev.org/). Manuals remain the property of their
respective publishers and are presented for preservation and repair reference.

Two further archives have been surveyed but not ingested — GamingDoc and the Console5
Tech Wiki. `docs/EXTERNAL-SOURCES.md` records what each holds, what it would cost to
take, and where the answer is "link to it, don't mirror it". The measured inventories
live in `data/sources/` and are rebuilt by `tools/survey_gamingdoc.py` and
`tools/survey_console5.py`.
