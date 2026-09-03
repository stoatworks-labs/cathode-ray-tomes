# Dead links

The scans are not mirrored: `/pdf/<id>` is a 302 to the source archive. So a
document whose source has gone is a dead link on this site, and until now the
reader found out by landing on somebody else's 404 in a new tab.

```bash
python3 tools/check_links.py            # the ones the ingest already failed on
python3 tools/check_links.py --all      # every document; hours, serial by design
python3 tools/check_links.py --offline  # trust the ingest state, no requests
```

Writes `data/link-health.json`; `build_index.py` merges it and stamps `dead` —
and, where the Internet Archive has a working copy, `mirror` — on the affected
catalogue records. A broken document is also checked against
`data/sources/archive_org.json`, so a run needs that survey to have been done.

## What is actually broken

Sixteen documents of 2,448, and none of them is our mistake — arcadertfm's own
catalogue still lists all sixteen with the same URLs, verified against a fresh
`machines.json` months after the ingest first failed. Its index and its file
server disagree.

| | | |
|---|---|---|
| `gone` — HTTP 404 at the source | 12 | 2 recovered from archive.org |
| `unreadable` — fetches fine, is not a readable PDF | 4 | 1 recovered |

Every one of the twelve ends `.PDF`. Lowercasing the extension recovers none of
them, so it is not a case-sensitivity problem, just a batch that went away.

## Three of them are only broken here

`tools/survey_archive_org.py` found that the Internet Archive's `arcademanuals`
collection holds 2,065 of our documents under the same filenames, and five of
the sixteen broken ones. Five is optimistic: two of those items are metadata
shells with no files in them at all, which is why `check_links.py` reads each
item's own file list and confirms the URL with a HEAD before recording it.

Three are real, and they are not a fallback link — they are documents the corpus
can simply have. The mirrored copies are readable PDFs where ours are a 404 or
a truncated file, so `ingest.py` prefers the mirror for any document already
marked dead, and all three are now ingested and searchable: Speedway's wiring
diagram, 19 pages of Ten Yard Fight '85, and 6 pages of Raiden Fighters.

The mirror is recorded beside `src`, never in place of it. A document's id is
the sha1 of its source URL, so swapping the URL would change the id and break
every link already pointing at it.

That leaves **thirteen** with nowhere to go. Those are still marked rather than
dropped. The machine really does have that
schematic somewhere, and saying so with a reason is more use than either
silence or a link that fails. On a machine page they render as plain rows, not
links, reading *the source archive no longer has this file*. `/pdf/<id>` returns
410 with an explanation instead of redirecting into a 404.

## The bug underneath, which was much bigger

`wrangler.jsonc` sets `not_found_handling: single-page-application`, so the
ASSETS binding answers a path that does not exist with **200 and index.html**.
`asset()` tested `!res.ok` for a missing asset, which that never trips, and went
on to `res.json()` — which threw a SyntaxError on the HTML and returned
`error code: 1101`, a 500, from code that plainly meant to return 404.

Seven endpoints, every one of them: `/api/doc`, `/api/machine`, `/api/parts`,
`/api/chips`, `/api/signals`, `/api/diagnostics`, `/api/rommap`. Any mistyped
URL, and every link to one of those sixteen documents.

It survived because there was no way to run the Worker: `wrangler dev` cannot
spawn workerd on this machine, so Worker changes shipped unexercised. There is
now `tools/test_worker.mjs`, which stubs the binding to return the SPA fallback
exactly as Cloudflare does and asserts the status of thirty-one routes. Writing it
immediately found a second instance of the same bug that the first fix had
missed — `/api/rommap` read the binding directly rather than through `asset()`,
so the content-type guard never covered it.

## Soft 404s

`/machine/does-not-exist` used to return **200** and the shell, which then said
"Page not found". Right for a reader, invisible to anything that checks links,
and wrong for a crawler — which indexes the miss as a real page, and which is
how a reference site accumulates rot nobody can see.

The four routes that name a specific thing — `/machine/`, `/doc/`, `/board/`,
`/rom/` — are now checked against the index before the shell is served, and a
miss gets the same shell with a 404 on it. The reader sees exactly what they saw
before; everything else gets told the truth.

The cost is an index read, and only on the first request an isolate handles for
one of those paths: `index()` memoises, and the same indexes are already read by
`/api/machines`, `/api/search` and `/pdf`. Routes that name nothing in
particular — `/`, `/search`, `/boards`, `/about` — are not checked at all.

## Still open

A static asset that does not exist still answers 200 with the shell:
`/css/nope.css` returns HTML. Harmless in practice, since nothing links to one,
and the fix is a `not_found_handling` change that would take the SPA routing
with it.
