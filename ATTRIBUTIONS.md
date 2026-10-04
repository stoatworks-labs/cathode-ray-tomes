# Attributions

Cathode Ray Tomes is built on other people's work. This file lists what that work is, who did
it, and what it is doing here.

It is generated — the master lists live in the `stoatworks-backend` repo and are
pushed out by `scripts/sync-attributions.py`. Edit it there, not here.

## Code we derived from other people's work

Someone else solved this first, and this project would not exist in its current form without their work.

### ArcadeRTFM

<https://arcadertfm.com/>

The corpus: arcade service manuals, schematics and drawing packages, every one a flat scan. Each page is OCR'd and rebuilt as a searchable HTML document, drawing-package scans are republished under web/pages/, and /pdf/<id> redirects to the original rather than mirroring it. The hand-built board maps and KiCad conversions are read by eye off the component-location drawings and IC parts lists in these scans (Pong from Atari assembly drawing A001433 Rev E). Manuals remain the property of their respective publishers and are presented for preservation and repair reference.

### MAME

<https://www.mamedev.org/>

Machine hardware metadata (CPUs, displays, inputs, DIP switches) derives from MAME, by way of ArcadeRTFM's machines.json. The 1,469 ROM maps in data/rommap/ are built from the board positions MAME records in its romset filenames, and the board maps are checked against MAME.

### GamingDoc

<https://gamingdoc.org/>

All 43 of its documents, 2,772 pages, are on the site: console and handheld service manuals across eleven systems (37 of the 43 carry a text layer and are read from it rather than OCR'd), plus developer manuals, modchip installation guides and the SNK MV2F/MV4F service manual. Each is credited on the document itself. GamingDoc re-hosts other people's manuals and states no licence; its recap lists, credited to Console5, are counted and not taken.

### InteractiveHtmlBom

<https://github.com/openscopeproject/InteractiveHtmlBom>

The 50 board viewers under web/boards/ (*-ibom.html) are its generated output from the KiCad conversions, and each page carries its viewer code together with Split.js, lz-string and PEP.

### Split.js v1.3.5

<https://github.com/nathancahill/Split.js>  
Licence: MIT

Embedded in each InteractiveHtmlBom page under web/boards/.

### lz-string 1.4.4 — Pieroxy

<http://pieroxy.net/blog/pages/lz-string/testing.html>  
Licence: WTFPL, Version 2  
Copyright: 2013 Pieroxy

The LZ-based compression library embedded in each InteractiveHtmlBom page under web/boards/.

### PEP v0.4.3 (Pointer Events Polyfill)

<https://github.com/jquery/PEP>  
Copyright: jQuery Foundation and other contributors

Embedded in each InteractiveHtmlBom page under web/boards/. Its header points at http://jquery.org/license for the licence.

## Third-party code this project uses

Libraries, SDKs and frameworks the project is built on or bundles.

### The npm ecosystem

<https://www.npmjs.com>  
Licence: predominantly MIT  
Copyright: the individual package authors

npm dependencies, resolved and pinned in the lockfile.

Build tooling, test runners and the libraries the front ends are assembled from. The exact set and versions for any build are in that repo's lockfile, which is the authoritative list.

The full transitive dependency set for any build is pinned in this repo's lockfile,
which is the authoritative list. What is named above is the layers a reader would
want to know about, not every package that has ever been resolved.

## Work we checked ourselves against

No code was taken from these — but they were how we knew we had it right, and that is worth saying out loud.

### Internet Archive, arcademanuals collection

<https://archive.org/details/arcademanuals>

It holds 2,065 of the corpus's 2,405 documents under the same filename. tools/compare_ocr.py read its OCR (_djvu.txt) for 2,057 of them against ours and found nothing we read worse. Where the source archive has lost a file, /pdf/<id> redirects to the archive.org copy and the reader credits the Internet Archive on the document.

### Console5 Tech Wiki

<https://wiki.console5.com/wiki/>

Surveyed and cross-referenced, never mirrored: Console5 expressly reserves its rights, so data/sources/console5.json stores titles, sizes, categories and URLs and no page content. Matching its 446 IC pages by part number covers 1,697 of 2,368 IC placements across the hand-built boards.

### KiCad symbol library

tools/check_devices.py and tools/check_packages.py cross-check the hand-verified pinouts and package sizes against KiCad's own symbols: 17 of the 20 parts the net validator reasons about verify, and the other three (555, 7425, 7450) are the symbols KiCad does not ship.

### TI datasheets

The 555, 7425 and 7450 symbols KiCad does not ship were built by hand from them, the unusual supply pins of the 7483, 7490 and 7493 were verified against them, and traced connectivity is cross-checked on their gate mapping.

## Getting this wrong

If your work is here and the description is inaccurate, the licence is wrong, or you would rather not be listed — open an issue and it will be fixed.
