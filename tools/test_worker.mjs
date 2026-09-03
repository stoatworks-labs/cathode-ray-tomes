/**
 * Exercise the Worker's routing against a stubbed ASSETS binding.
 *
 *   node tools/test_worker.mjs
 *
 * There is no other way to run it here: `wrangler dev` cannot spawn workerd on
 * this machine (`spawn EBADF`), so every Worker change until now went out
 * unexercised. The bug that prompted this needed no workerd anyway.
 *
 * `wrangler.jsonc` sets `not_found_handling: single-page-application`, so the
 * ASSETS binding answers a path that does not exist with **200 and
 * index.html** rather than a 404. Every handler that looked up an unknown id
 * therefore reached `res.json()`, threw a SyntaxError on the HTML, and returned
 * `error code: 1101` — a 500 — where the code plainly meant to return 404. That
 * is what a reader hit on any of the sixteen documents the ingest could not
 * read, and on any mistyped URL. The stub below reproduces exactly that
 * fallback, so these cases fail without the fix and pass with it.
 */
import worker from "../src/index.js";
import { readFileSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const WEB = join(ROOT, "web");
const INDEX_HTML = readFileSync(join(WEB, "index.html"), "utf8");

const isFile = (p) => {
  try { return statSync(p).isFile(); } catch { return false; }
};

const env = {
  SITE_NAME: "Cathode Ray Tomes",
  UPSTREAM: "https://files.arcadertfm.com",
  ASSETS: {
    async fetch(req) {
      const path = new URL(req.url).pathname;
      const file = join(WEB, path);
      // isFile, not exists: `web/boards/` is a real directory of KiCad exports
      // and `/boards` is also an app route. Cloudflare serves no directory, so
      // neither does this.
      if (!path.endsWith("/") && isFile(file)) {
        return new Response(readFileSync(file), {
          headers: {
            "content-type": path.endsWith(".json")
              ? "application/json" : "text/plain",
          },
        });
      }
      return new Response(INDEX_HTML, {
        status: 200,
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    },
  },
};

// Ids are real and come from the built corpus: a healthy document, one the
// ingest failed on, and one whose source has gone from the archive.
const CASES = [
  ["/api/machine/pong",               200, "known machine"],
  ["/api/machine/does-not-exist",     404, "unknown machine"],
  ["/api/doc/d282ad622596",           200, "rendered document"],
  ["/api/doc/38d2e147c5cd",           404, "catalogued but never rendered"],
  ["/api/doc/000000000000",           404, "unknown document"],
  ["/api/doc/nothex",                 404, "malformed id"],
  ["/api/parts/000000000000",         404, "unknown parts list"],
  ["/api/chips/nosuchboard",          404, "unknown board"],
  ["/api/signals/nosuchboard",        404, "unknown board signals"],
  ["/api/diagnostics/does-not-exist", 200, "diagnostics answer [] for unknown"],
  ["/api/rommap/does-not-exist",      404, "unknown ROM map"],
  ["/api/stats",                      200, "stats"],
  ["/api/machines?kind=console",      200, "console filter"],
  ["/pdf/d282ad622596",               302, "healthy document redirects upstream"],
  ["/pdf/e27163bf0ed2",               410, "source gone: explained, not redirected"],
  ["/pdf/000000000000",               404, "unknown document"],

  // Page routes. The shell is served either way — the router renders "Page not
  // found" for a reader — but the status has to be honest or a link checker
  // sweeps the site and calls every rotted link clean.
  ["/",                               200, "home"],
  ["/machine/pong",                   200, "known machine page"],
  ["/machine/sony-playstation-2",     200, "known console page"],
  ["/machine/does-not-exist",         404, "unknown machine page"],
  ["/doc/d282ad622596",               200, "known document page"],
  ["/doc/000000000000",               404, "unknown document page"],
  ["/board/pong",                     200, "known board page"],
  ["/board/does-not-exist",           404, "unknown board page"],
  ["/rom/centiped",                   200, "known ROM map page"],
  ["/rom/does-not-exist",             404, "unknown ROM map page"],
  ["/search",                         200, "a route that names nothing"],
  ["/boards",                         200, "a route that names nothing"],
  ["/about",                          200, "a route that names nothing"],

  // Static assets go through the same handler now, so check they still do.
  ["/css/app.css",                    200, "stylesheet"],
  ["/js/app.js",                      200, "script"],
];

let failures = 0;
for (const [path, want, why] of CASES) {
  let got, body = "";
  try {
    const res = await worker.fetch(
      new Request(`https://cathode-ray-tomes.com${path}`), env, {});
    got = res.status;
    if (got !== 302) body = (await res.text()).slice(0, 70);
  } catch (e) {
    got = `THREW ${e.constructor.name}`;
  }
  const ok = got === want;
  if (!ok) failures++;
  console.log(`${ok ? "ok  " : "FAIL"} ${String(got).padEnd(14)} want ${want}  `
    + `${path.padEnd(34)} ${why}`);
  if (!ok && body) console.log(`     body: ${body}`);
}

console.log(failures ? `\n${failures} failing` : `\nall ${CASES.length} pass`);
process.exit(failures ? 1 : 0);
