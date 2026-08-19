# AGENTS.md — Cathode Ray Tomes

Onboarding for whoever (or whatever) picks this up next. `README.md` is the user-facing
description; this file is the *why*, the traps, and an honest account of what is real.

## Mental model

Cathode Ray Tomes is three things stacked:

1. **An ingestion pipeline** (`tools/`) that pulls the ArcadeRTFM PDF corpus, rasterises
   every page, OCRs it, and derives search indexes. Runs locally, output lands in `cache/`.
2. **A Cloudflare Worker + static app** (`src/`, `web/`) that serves the corpus: browse,
   read, search. Indexes live in KV, page images and PDFs in R2.
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
  cross-origin. Everything is mirrored into R2 and served same-origin.
- **The upstream host blocks requests without a User-Agent** (Cloudflare). All fetches set one.
- **`pdftoppm` on this machine rejects `-r150`** — it needs `-r 150` as two arguments. It
  also numbers pages *without* zero padding, so `p-10.png` sorts before `p-2.png`. Sort
  numerically; `render()` does.
- **`7490`, `7493` use VCC=5/GND=10 and `7483` uses VCC=5/GND=12** — not the usual corner
  pins. Verified against the KiCad symbols and TI datasheets.

## Architecture — why there is no R2

The site serves **HTML manuals**, not scans. Text and structure for the whole corpus is
~90 MB and lives in KV; the UI is static assets. Mirroring page images would have been
63,000 files and 8.9 GB, which is what forced R2 in the original design and is no longer
needed. Original scans are linked out to ArcadeRTFM.

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
  debugging. Now 60s + stale-while-revalidate; only immutable R2 objects cache hard.

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

The site builds from GitHub (`stoatworks-labs/cathode-ray-tomes`, private) via Cloudflare
Workers Builds. Three commands are configured, and the third is the one that bites:

| Setting | Value |
|---|---|
| Build command | `npm ci` |
| Deploy command (production branch `main`) | `npx wrangler deploy` |
| Version command (**every other branch**) | `npx wrangler versions upload` |

If the Version command is left as plain `wrangler deploy`, a build on *any* branch
publishes straight to the live Worker. `versions upload` uploads a preview and leaves
production alone.

**CI builds the Worker and the static assets only.** The corpus itself — indexes in KV,
page images and PDFs in R2 — is pushed from a workstation by `tools/publish.sh remote`
after an ingest run. CI has no access to `cache/` and never needs it.

## Deployment

Not yet deployed. `wrangler.jsonc` carries `PLACEHOLDER_KV_ID` — a real KV namespace and
the `crt-docs` R2 bucket must be created first. The subdomain is a placeholder pending a
real domain.

The project was called *Bezel* until it was renamed to **Cathode Ray Tomes**; if you find
a stray `bezel` string outside `cache/` and `data/index/postings/`, it is a leftover.
(`data/index/postings/b.json` legitimately contains the word — it is OCR'd corpus text,
not a reference to the project.)

Renaming the project directory means stopping `ingest.py` and `backfill_structure.py`
first: both resolve `ROOT` at import and would write to the old path. Both are
checkpointed, so they resume cleanly afterwards.
