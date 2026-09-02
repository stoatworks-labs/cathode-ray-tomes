# Dead links

The scans are not mirrored: `/pdf/<id>` is a 302 to the source archive. So a
document whose source has gone is a dead link on this site, and until now the
reader found out by landing on somebody else's 404 in a new tab.

```bash
python3 tools/check_links.py            # the ones the ingest already failed on
python3 tools/check_links.py --all      # every document; hours, serial by design
python3 tools/check_links.py --offline  # trust the ingest state, no requests
```

Writes `data/link-health.json`; `build_index.py` merges it and stamps `dead` on
the affected catalogue records.

## What is actually broken

Sixteen documents of 2,448, and none of them is our mistake — arcadertfm's own
catalogue still lists all sixteen with the same URLs, verified against a fresh
`machines.json` months after the ingest first failed. Its index and its file
server disagree.

| | |
|---|---|
| `gone` — HTTP 404 at the source | 12 |
| `unreadable` — fetches fine, is not a readable PDF | 4 |

Every one of the twelve ends `.PDF`. Lowercasing the extension recovers none of
them, so it is not a case-sensitivity problem, just a batch that went away.

Both are now marked rather than dropped. The machine really does have that
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
exactly as Cloudflare does and asserts the status of sixteen routes. Writing it
immediately found a second instance of the same bug that the first fix had
missed — `/api/rommap` read the binding directly rather than through `asset()`,
so the content-type guard never covered it.

## Still open

`/machine/does-not-exist` returns **200** and the shell, which then says "Page
not found". Correct for a reader, invisible to anything that checks links, and
wrong for a crawler. Fixing it means validating the slug in the Worker before
serving the shell, which costs an index read on every page load — worth doing,
not free, and not done here.
