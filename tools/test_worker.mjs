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
  ["/api/wiring",                     200, "connector library"],
  ["/api/layouts",                    200, "PCB layout index"],
  ["/api/layouts/capcom/1942",        200, "a driver's PCB layouts"],
  ["/api/layouts/capcom/nosuchdriver", 404, "a driver with no PCB layout"],
  ["/api/layouts/nosuchdir/1942",     404, "a directory with no PCB layout"],
  ["/api/layout/capcom/1942/1",       200, "one PCB layout"],
  ["/api/layout/capcom/1942/99",      404, "unknown PCB layout"],
  ["/api/layout/capcom/1942",         404, "a layout needs its number"],
  ["/api/customchips",                200, "custom chip index"],
  ["/api/customchip/007781",          200, "one custom chip"],
  ["/api/customchip/dl-050-115v",     200, "a custom chip no board here carries"],
  ["/api/customchip/nosuchchip",      404, "unknown custom chip"],
  ["/api/customchip/x%2F..%2Fboards", 404, "a chip slug cannot climb out"],
  ["/api/chip/zilog z80",             200, "the MAME device index is still there"],
  ["/api/stats",                      200, "stats"],
  ["/api/machines?kind=console",      200, "console filter"],
  ["/pdf/d282ad622596",               302, "healthy document redirects upstream"],
  ["/pdf/e27163bf0ed2",               410, "source gone, no mirror: explained"],
  ["/pdf/943469f413c9",               302, "source gone, mirrored: redirects to archive.org"],
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
  ["/layouts",                        200, "a route that names nothing"],
  ["/layout/capcom/1942/1",           200, "known PCB layout page"],
  ["/layout/capcom/1942/99",          404, "unknown PCB layout page"],
  ["/chip/007781",                    200, "known custom chip page"],
  ["/chip/dl-020f-108u",              200, "known custom chip page"],
  ["/chip/007790",                    404, "unknown custom chip page"],
  ["/chips",                          200, "a route that names nothing"],
  ["/search",                         200, "a route that names nothing"],
  ["/boards",                         200, "a route that names nothing"],
  ["/about",                          200, "a route that names nothing"],

  // Static assets go through the same handler now, so check they still do.
  ["/css/app.css",                    200, "stylesheet"],
  ["/js/app.js",                      200, "script"],
  ["/vendor/kicanvas/kicanvas.js",    200, "the schematic viewer ships with the site"],
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

// Routing is not the only way a handler can be silently wrong. /api/doc merges
// the catalogue record into the document through an explicit allowlist, and a
// field missing from that list is not an error anywhere — it is simply absent,
// and the feature that reads it never appears. `parts` was missing from it, so
// every one of the 194 parts lists the pipeline recovers was unreachable from
// the reader while being served perfectly well at /api/parts/<id>.
const docs = JSON.parse(readFileSync(join(WEB, "data", "docs.json"), "utf8"));
const withParts = docs.find((d) => d.parts);
const CONTENT = withParts ? [[
  `/api/doc/${withParts.id}`,
  (body) => body.parts === withParts.parts,
  `carries parts=${withParts.parts} from the catalogue`,
]] : [];

// Japanese has no spaces, so the query splitter and the index both work in
// character bigrams. They have to agree: index under 設 and look under `_` and
// the term is written and never found. A routing test cannot see that either.
CONTENT.push([
  "/api/search?q=" + encodeURIComponent("設定"),
  (body) => body.total > 0,
  "finds the Japanese manuals by a Japanese word",
]);

// A board's logged conflicts are what a repairer must weigh before trusting a
// pin. publish_board copies them from the read file; this is where they leave.
const boardList = JSON.parse(readFileSync(join(WEB, "data", "boards.json"), "utf8"));
const withConflicts = boardList.find((b) => (b.conflicts || []).length);
if (withConflicts) CONTENT.push([
  "/api/boards",
  (body) => body.find((b) => b.slug === withConflicts.slug)?.conflicts?.length
    === withConflicts.conflicts.length,
  `serves ${withConflicts.slug}'s ${withConflicts.conflicts.length} conflicts`,
]);

// Most machines have no document, and MAME's account of the board -- its ROM
// set and driver source -- is the whole page for them. A targeted publisher
// puts it there (build_assets.py --mame-only); a full rebuild must too.
CONTENT.push([
  "/api/machine/88games",
  (body) => (body.mame?.roms || []).length > 0 && !!body.mame?.src,
  "an undocumented machine carries MAME's ROM set and driver source",
]);

// A board imported from someone else's drawing is published under their
// licence, and the page has to say so: whose drawing, on what terms, and where
// the source is. If publish_board stops carrying `license`/`origin`, the board
// still renders -- as though this repository had drawn it.
// Every board with a schematic gets the interactive viewer, which loads the
// sheets from GitHub by the list publish_board writes. A board whose list went
// missing still shows its PDF, so nothing fails -- the viewer just never appears.
CONTENT.push([
  "/api/boards",
  (body) => body.filter((b) => b.redrawn).every((b) => b.redrawn.kicanvas?.files?.length > 0
    && /^https:\/\/raw\.githubusercontent\.com\//.test(b.redrawn.kicanvas.base)),
  "every board with a schematic lists its sheets for the interactive viewer",
]);

const imported = boardList.find((b) => b.origin);
if (imported) {
  CONTENT.push([
    "/api/boards",
    (body) => {
      const b = body.find((x) => x.slug === imported.slug);
      return !!(b && b.license && b.origin?.authors?.length && b.origin?.source
        && (b.redrawn?.sheets || []).every((s) => s.page > 0));
    },
    `serves ${imported.slug}'s licence, authors and source`,
  ]);
  CONTENT.push([
    `/api/chips/${imported.slug}`,
    (body) => Object.keys(body).length > 0,
    `serves the chip lookup for ${imported.slug}`,
  ]);
}

// The generated wiring view rides on the machine record and is drawn from
// /api/wiring. Both halves have to be there, and the exclusions have to hold:
// a gambling board on a "JAMMA edge" wires its own assignment onto it, and a
// view that placed a joystick there would be confidently wrong.
CONTENT.push([
  "/api/machine/sf2",
  (body) => body.wiring?.std === "cps1" && body.wiring.use.includes("p1.b3")
    && body.wiring.miss?.some((m) => m.startsWith("Player 1 button")),
  "Street Fighter II: CPS-1 edge, kick buttons listed as not placed",
]);
CONTENT.push([
  "/api/machine/goldstar",
  (body) => !!body.slug && !body.wiring,
  "a gambling board gets no generated wiring view",
]);
CONTENT.push([
  "/api/wiring",
  (body) => body.connectors?.jamma?.rows?.length === 28
    && (body.standards?.cps2?.variants || []).length === 2
    && Object.values(body.connectors).every((c) => (c.sources || []).every((s) => body.sources[s])),
  "56-way JAMMA edge, both CPS-2 CN5 wirings, every cited source defined",
]);

// A PCB layout is reproduced from MAME's source, and the BSD licence it is
// reproduced under asks that the notice travel with it. A layout that arrives
// without its licence, copyright holders or the commit it was read at is one the
// page cannot credit, so check they leave the Worker -- and that only a
// permissive licence ever does.
CONTENT.push([
  "/api/layout/capcom/1942/1",
  (body) => ["BSD-3-Clause", "CC0-1.0"].includes(body.licence) && !!body.copyright
    && /^[0-9a-f]{40}$/.test(body.commit) && body.devices.length > 0
    && body.devices.every((d) => d.line >= body.line && d.line <= body.end),
  "a layout carries its licence, copyright and commit, and its devices their lines",
]);
CONTENT.push([
  "/api/layouts/capcom/1942",
  (body) => body.length > 0 && body.every((l) => !l.art && !l.devices && l.count > 0),
  "a driver's list is a summary, without the art",
]);

// A custom chip is someone else's drawing too, published under the GPL, and
// its page has to say whose and on what terms. Every chip the manifest lists
// must be published -- a chip that failed to import is otherwise just absent.
const manifest = JSON.parse(readFileSync(join(ROOT, "data", "jtcores.json"), "utf8"));
const chipSlugs = (manifest.chips || []).map((c) => c.slug);
CONTENT.push([
  "/api/customchips",
  (body) => chipSlugs.length > 0 && chipSlugs.every((s) => body.some((c) => c.slug === s))
    && body.every((c) => c.license === "GPL-3.0" && c.authors.length > 0 && c.pins > 0),
  `all ${chipSlugs.length} chips in data/jtcores.json, each with licence and authors`,
]);
CONTENT.push([
  "/api/customchip/007781",
  (body) => body.license === "GPL-3.0" && body.origin?.authors?.length > 0
    && /^[0-9a-f]{40}$/.test(body.origin?.commit) && !!body.origin?.source
    && body.pins.length === body.package.pins
    && body.inside.sheets.length > 1 && body.inside.sheets.every((s) => s.page > 0)
    && body.boards.some((b) => b.slug === "twin-16-gx687" && b.refs.some((r) => r.ref === "B_C11")),
  "a chip carries its licence, credits, pinout, sheets and the boards it is on",
]);
// No board here carries the Capcom customs, so the only way to Pang and Last
// Duel is through the sketches of their boards in MAME's notes.
CONTENT.push([
  "/api/customchip/dl-010d-103",
  (body) => body.boards.length === 0 && body.layouts.length > 0
    && ["pang", "lastduel"].every((m) => body.machines.some(([s]) => s === m)),
  "a chip on no board here reaches its machines through MAME's layouts",
]);
// A sketch tied to no set describes a driver's hardware, not a machine's.
CONTENT.push([
  "/api/customchip/052535",
  (body) => body.layouts.some((l) => l.scope === "driver")
    && body.machines.every(([s]) => body.boards.some((b) => b.machines.includes(s))
      || body.layouts.some((l) => ["set", "title"].includes(l.scope) && l.slugs.includes(s))),
  "a driver-wide sketch is listed but names no machine",
]);
// The board page links a designator to a chip from the index; the index and
// the board's own chip lookup have to agree about what is at it.
const chipIndex = JSON.parse(readFileSync(join(WEB, "data", "customchips.json"), "utf8"));
const onTwin16 = chipIndex.filter((c) => c.boards.some((b) => b.slug === "twin-16-gx687"));
CONTENT.push([
  "/api/chips/twin-16-gx687",
  (body) => onTwin16.length >= 9 && onTwin16.every((c) =>
    c.boards.find((b) => b.slug === "twin-16-gx687").refs.every((r) => body[r]?.part === c.markings[0])),
  `the index's ${onTwin16.length} chips on Twin 16 sit where its chip lookup says`,
]);

for (const [path, ok, why] of CONTENT) {
  let pass = false, note = "";
  try {
    const res = await worker.fetch(
      new Request(`https://cathode-ray-tomes.com${path}`), env, {});
    const body = await res.json();
    pass = ok(body);
    if (!pass) note = `got parts=${JSON.stringify(body.parts)}`;
  } catch (e) {
    note = `THREW ${e.constructor.name}`;
  }
  if (!pass) failures++;
  console.log(`${pass ? "ok  " : "FAIL"} ${"".padEnd(14)} content  `
    + `${path.padEnd(34)} ${why}`);
  if (note) console.log(`     ${note}`);
}

// Serving a field is not showing it. The board page's open questions, its read
// notes and the lookup's device notes went out in 26bdc549 and were reverted
// six minutes later by a61d2ab8, whose app.js predated them — a commit from a
// shared checkout carrying an old copy of a file. Nothing failed: the data was
// still served, and for seven weeks no page read it. There is no browser here, so
// this only asserts that the script still reads the fields; it cannot see
// whether they render well.
// The wiring view's warning and its not-placed list are what stop a generated
// diagram being taken for a traced one; they get the same guard.
const APP_READS = ["b.conflicts", "b.notes", "v.note", "b.origin.authors", "b.license", "b.machines", "kicanvas-embed", "l.licence", "l.copyright", "PARTIAL_NOTE", "w.miss", "Generated, not read.",
  // A chip page's credit and licence, its logged conflicts, and the links that
  // bring a reader to it from a board, a machine and a layout.
  "listOf(o.authors)", "c.license", "c.conflicts", "customsOn(list, slug)",
  "(c.machines || []).includes(slug)", "customs.has(d.label)"];
const appJs = await (await worker.fetch(
  new Request("https://cathode-ray-tomes.com/js/app.js"), env, {})).text();
for (const field of APP_READS) {
  const pass = appJs.includes(field);
  if (!pass) failures++;
  console.log(`${pass ? "ok  " : "FAIL"} ${"".padEnd(14)} script   `
    + `${"/js/app.js".padEnd(34)} reads ${field}`);
}

// The stub, like Cloudflare, answers a missing file with index.html and a 200,
// so a missing PDF passes a status check. Read the bytes.
const PDFS = chipIndex.map((c) => `/chips/${c.slug}.pdf`);
for (const path of PDFS) {
  const res = await worker.fetch(new Request(`https://cathode-ray-tomes.com${path}`), env, {});
  const head = Buffer.from(await res.arrayBuffer()).subarray(0, 5).toString("latin1");
  const pass = res.status === 200 && head === "%PDF-";
  if (!pass) failures++;
  console.log(`${pass ? "ok  " : "FAIL"} ${"".padEnd(14)} pdf      ${path.padEnd(34)} is a PDF`);
}

const total = CASES.length + CONTENT.length + APP_READS.length + PDFS.length;
console.log(failures ? `\n${failures} failing` : `\nall ${total} pass`);
process.exit(failures ? 1 : 0);
