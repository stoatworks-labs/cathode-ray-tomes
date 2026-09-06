/**
 * Cathode Ray Tomes — Worker entry point.
 *
 * Serves the browse/reader UI and a small JSON API over the corpus. Everything
 * — indexes, per-machine records, rendered documents and the search postings —
 * ships as static assets alongside the code, so a deploy publishes code and
 * corpus together and there is no store to keep in step.
 *
 * Original scans are not hosted; /pdf/<id> redirects to the source archive.
 *
 * The one write path is /api/submit, which files a reader's contribution into a
 * separate GitHub repository for triage — see src/submit.js. It never touches
 * the corpus this Worker serves.
 */

import { handleSubmit, submitConfig } from "./submit.js";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  // Assets are immutable within a deploy, but the API shape is stable across
  // deploys, so allow a short cache with revalidation.
  "cache-control": "public, max-age=300, stale-while-revalidate=3600",
};

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });

const notFound = (what = "not found") => json({ error: what }, 404);

/**
 * Read a corpus asset. Assets are fetched through the ASSETS binding, which
 * hits Cloudflare's cache rather than an origin.
 *
 * The binding is configured `not_found_handling: single-page-application`, so a
 * path that does not exist comes back as **200 with index.html**, not 404. That
 * makes `!res.ok` useless as a missing-asset test: every endpoint below that
 * looks up an unknown id used to reach `res.json()`, throw a SyntaxError on the
 * HTML, and return a Worker exception — `error code: 1101`, a 500 — where the
 * code plainly intended a 404. It affected /api/doc, /api/machine, /api/parts,
 * /api/chips, /api/signals, /api/diagnostics and /api/rommap alike, which is
 * every link into a document the ingest could not read.
 */
async function asset(env, request, path) {
  const res = await env.ASSETS.fetch(new Request(new URL(path, request.url)));
  if (!res.ok) return null;
  if (!(res.headers.get("content-type") || "").includes("json")) return null;
  try {
    return await res.json();
  } catch {
    return null;                       // truncated or not JSON after all
  }
}

/** Hot indexes are read on nearly every request — keep them in the isolate. */
const memo = new Map();
async function index(env, request, name) {
  if (memo.has(name)) return memo.get(name);
  const data = await asset(env, request, `/data/${name}.json`);
  if (data) memo.set(name, data);
  return data;
}

function scoreMachine(m, q) {
  const name = m.n.toLowerCase();
  if (name === q) return 1000;
  if (name.startsWith(q)) return 500 - name.length;
  const i = name.indexOf(q);
  if (i >= 0) return 200 - i;
  if ((m.m || "").toLowerCase().includes(q)) return 50;
  return -1;
}

/** The letter a name files under: A–Z, or "#" for a name that starts with a
    digit or a symbol. Leading quotes and brackets are skipped, so "'88 Games"
    files under # and "(Unknown) Foo" under F. Mirrored in web/js/app.js. */
const initialOf = (name) => {
  const c = String(name || "").replace(/^[^a-z0-9]+/i, "").charAt(0).toUpperCase();
  return /[A-Z]/.test(c) ? c : "#";
};
const nameKey = (name) => String(name || "").replace(/^[^a-z0-9]+/i, "").toLowerCase();

/** The machine index in name order, sorted once per index load. The upstream
    order is close to alphabetical but not quite, and a paged list that is
    nearly sorted puts the same machine on two pages. */
let sortedFor = null, sortedMachinesList = null;
async function sortedMachines(env, request) {
  const list = (await index(env, request, "machines")) || [];
  if (list !== sortedFor) {
    sortedMachinesList = [...list].sort((a, b) =>
      nameKey(a.n).localeCompare(nameKey(b.n), "en", { numeric: true }) || a.n.localeCompare(b.n));
    sortedFor = list;
  }
  return sortedMachinesList;
}

/** Postings are sharded by leading character to keep each file small. */
const shardOf = (term) => (/^[a-z0-9]/.test(term[0]) ? term[0] : "_");

async function handleApi(url, env, request) {
  const p = url.pathname.replace(/^\/api\//, "");

  // The only endpoint with a side effect, and the only one that reads a body.
  // Handled ahead of the corpus routes because those answer GET only and cache
  // their replies, neither of which is right for a submission.
  if (p === "submit") {
    if (request.method === "POST") return handleSubmit(request, env);
    if (request.method === "GET") return submitConfig(env);
    return json({ error: "method not allowed" }, 405);
  }

  if (p === "stats") {
    const [machines, docs, boards] = await Promise.all([
      index(env, request, "machines"),
      index(env, request, "docs"),
      index(env, request, "boards"),
    ]);
    const ingested = (docs || []).filter((d) => d.ingested);
    return json({
      machines: (machines || []).length,
      machinesWithDocs: (machines || []).filter((m) => m.d > 0).length,
      systems: (machines || []).filter((m) => m.t).length,
      documents: (docs || []).length,
      schematics: (docs || []).filter((d) => d.schematic).length,
      digitised: ingested.length,
      pages: ingested.reduce((s, d) => s + (d.pages || 0), 0),
      sections: ingested.reduce((s, d) => s + (d.sections || 0), 0),
      boards: (boards || []).length,
    });
  }

  if (p === "machines") {
    const q = (url.searchParams.get("q") || "").trim().toLowerCase();
    const limit = Math.min(+url.searchParams.get("limit") || 50, 200);
    const offset = Math.max(0, +url.searchParams.get("offset") || 0);
    const onlyDocs = url.searchParams.get("docs") === "1";
    const onlySch = url.searchParams.get("sch") === "1";
    const onlyKicad = url.searchParams.get("kicad") === "1";
    // A–Z, or "#" for names starting with a digit or a symbol.
    const letter = (url.searchParams.get("letter") || "").toUpperCase();
    // Every filter is applied here, before the page is cut, so the total the
    // client prints and the pages it offers are exact. Consoles are a few
    // dozen records among 7,823; filtering one page of results client-side
    // used to find none of them.
    const kind = url.searchParams.get("kind") || "";
    let out = await sortedMachines(env, request);
    if (onlyDocs) out = out.filter((m) => m.d > 0);
    if (onlySch) out = out.filter((m) => m.k > 0);
    if (onlyKicad) {
      // A board is keyed by its own slug and names the machine it belongs to
      // — asteroids-03 through -06 all point at `asteroid` — so the test is on
      // that field, not on the board slug matching the machine slug.
      const boards = (await index(env, request, "boards")) || [];
      const withBoard = new Set(boards.map((b) => b.machine || b.slug));
      out = out.filter((m) => withBoard.has(m.s));
    }
    if (kind === "arcade") out = out.filter((m) => !m.t);
    else if (kind === "console") out = out.filter((m) => !!m.t);
    if (letter) out = out.filter((m) => initialOf(m.n) === letter);
    if (q) {
      out = out
        .map((m) => [scoreMachine(m, q), m])
        .filter(([s]) => s >= 0)
        .sort((a, b) => b[0] - a[0])
        .map(([, m]) => m);
    }
    return json({ total: out.length, offset, limit, results: out.slice(offset, offset + limit) });
  }

  if (p.startsWith("machine/")) {
    const slug = decodeURIComponent(p.slice("machine/".length));
    if (!/^[a-z0-9][a-z0-9._-]*$/i.test(slug)) return notFound("bad slug");
    const rec = await asset(env, request, `/data/machine/${slug}.json`);
    return rec ? json(rec) : notFound("unknown machine");
  }

  if (p.startsWith("doc/")) {
    const id = p.slice("doc/".length);
    if (!/^[a-f0-9]{12}$/.test(id)) return notFound("bad doc id");
    const body = await asset(env, request, `/data/doc/${id}.json`);
    if (!body) return notFound("document not digitised yet");
    const docs = (await index(env, request, "docs")) || [];
    const meta = docs.find((d) => d.id === id) || {};
    // Pick catalogue fields explicitly: a blanket spread lets the catalogue's
    // `pages` count overwrite the document's `pages` array.
    // machines/machineNames are present only where one manual documents more
    // than one machine, as the MVS service manual does for MV-2F and MV-4F.
    //
    // `parts` is the row count of the manual's own illustrated parts list, and
    // the reader draws its "Parts list (n)" button from it. Leaving it out of
    // this list hid every one of them: 194 documents and 11,940 rows were
    // being served at /api/parts/<id> with nothing on the page linking there.
    // An allowlist fails closed, which is the right way round, but it only
    // works if adding a catalogue field means adding it here too.
    const { title, type, machine, machineName, machines, machineNames,
            src, source, sourcePage, schematic, note, dead, mirror,
            parts } = meta;
    return json({ ...body, title, type, machine, machineName, machines,
                  machineNames, src, source, sourcePage, schematic, note, dead,
                  mirror, parts });
  }

  // /api/parts/<docId> — bill of materials recovered from a manual's own
  // illustrated parts list.
  if (p.startsWith("parts/")) {
    const id = p.slice("parts/".length);
    if (!/^[a-f0-9]{12}$/.test(id)) return notFound("bad doc id");
    const rows = await asset(env, request, `/data/parts/${id}.json`);
    return rows ? json(rows) : notFound("no parts list for this document");
  }

  // /api/chips/<board> — designator -> part, functional block and the
  // equivalent designator on the other revision. This is the lookup a repairer
  // actually makes: "what is at C4, and what does it do?"
  if (p.startsWith("chips/")) {
    const b = p.slice("chips/".length);
    if (!/^[a-z0-9-]{1,40}$/.test(b)) return notFound("bad board");
    const idx = await asset(env, request, `/data/chips/${b}.json`);
    return idx ? json(idx) : notFound("no chip index for this board");
  }

  // /api/signals/<board> — signal name -> which sheets it appears on. Answers
  // "where do I look for VBLANK", which is the first step in chasing a symptom
  // back to a probe point.
  if (p.startsWith("signals/")) {
    const b = p.slice("signals/".length);
    if (!/^[a-z0-9-]{1,40}$/.test(b)) return notFound("bad board");
    const idx = await asset(env, request, `/data/signals/${b}.json`);
    return idx ? json(idx) : notFound("no signal index for this board");
  }

  // /api/diagnostics/<machine> — the self-test, troubleshooting and adjustment
  // sections across that machine's manuals, deep-linked to the page.
  if (p.startsWith("diagnostics/")) {
    const slug = decodeURIComponent(p.slice("diagnostics/".length));
    if (!/^[a-z0-9][a-z0-9._-]*$/i.test(slug)) return notFound("bad slug");
    const rows = await asset(env, request, `/data/diagnostics/${slug}.json`);
    return rows ? json(rows) : json([]);
  }

  // /api/signatures/<machine> — signature-analysis material: which documents
  // carry it, and the codes where they are printed on a drawing sheet.
  if (p.startsWith("signatures/")) {
    const slug = decodeURIComponent(p.slice("signatures/".length));
    if (!/^[a-z0-9][a-z0-9._-]*$/i.test(slug)) return notFound("bad slug");
    const rec = await asset(env, request, `/data/signatures/${slug}.json`);
    return rec ? json(rec) : json(null);
  }

  // /api/power/<machine> — fuse ratings and expected rails. The first things
  // checked on a machine that is completely dead.
  if (p.startsWith("power/")) {
    const slug = decodeURIComponent(p.slice("power/".length));
    if (!/^[a-z0-9][a-z0-9._-]*$/i.test(slug)) return notFound("bad slug");
    const rec = await asset(env, request, `/data/power/${slug}.json`);
    return rec ? json(rec) : json(null);
  }

  // /api/related/<board> — other boards that share hardware with this one.
  // A known-good sibling is often the fastest way to confirm a fault.
  if (p.startsWith("related/")) {
    const b = p.slice("related/".length);
    if (!/^[a-z0-9-]{1,40}$/.test(b)) return notFound("bad board");
    const rows = await asset(env, request, `/data/related/${b}.json`);
    return json(rows || []);
  }

  if (p.startsWith("chip/")) {
    const part = decodeURIComponent(p.slice("chip/".length)).toLowerCase();
    const idx = (await index(env, request, "chips")) || {};
    return json({ chip: part, machines: idx[part] || [] });
  }

  // Full text over the OCR'd manuals. All terms must be present; documents are
  // ranked by total occurrences so a manual that covers a part sorts above a
  // schematic that prints it once in a corner.
  if (p === "search") {
    const q = (url.searchParams.get("q") || "").trim().toLowerCase();
    const limit = Math.min(+url.searchParams.get("limit") || 60, 200);
    if (q.length < 3) return json({ query: q, total: 0, results: [] });

    const terms = [...new Set(q.split(/\s+/).filter((t) => t.length >= 3))];
    if (!terms.length) return json({ query: q, total: 0, results: [] });

    // Only the shards the query touches are fetched.
    const shards = {};
    await Promise.all(
      [...new Set(terms.map(shardOf))].map(async (s) => {
        shards[s] = (await asset(env, request, `/data/postings/${s}.json`)) || {};
      })
    );

    let scores = null;
    for (const t of terms) {
      const here = new Map(((shards[shardOf(t)] || {})[t] || []).map(([id, n]) => [id, n]));
      if (scores === null) {
        scores = here;
      } else {
        for (const id of [...scores.keys()]) {
          if (here.has(id)) scores.set(id, scores.get(id) + here.get(id));
          else scores.delete(id);
        }
      }
      if (!scores.size) break;
    }

    const docs = (await index(env, request, "docs")) || [];
    const byId = new Map(docs.map((d) => [d.id, d]));
    const ranked = [...(scores || new Map())]
      .sort((a, b) => b[1] - a[1])
      .map(([id, n]) => (byId.has(id) ? { ...byId.get(id), hits: n } : null))
      .filter(Boolean);
    return json({ query: q, terms, total: ranked.length, results: ranked.slice(0, limit) });
  }

  // /api/rommaps and /api/rommap/<machine> — ROM positions recovered from
  // MAME's romset filenames. A different and much weaker thing than a board
  // map: memory devices only, one source, no cross-check.
  if (p === "rommaps") {
    return json((await index(env, request, "rommaps")) || []);
  }
  const rm = url.pathname.match(/^\/api\/rommap\/([a-z0-9_-]{1,40})$/);
  if (rm) {
    // Through asset(), not ASSETS directly: reading the binding raw is what
    // made this the one endpoint the content-type guard did not cover, and it
    // threw on the SPA fallback exactly as the rest used to.
    const map = await asset(env, request, `/data/rommap/${rm[1]}.json`);
    return map ? json(map) : notFound("no ROM map for this machine");
  }

  if (p === "boards") {
    return json((await index(env, request, "boards")) || []);
  }

  return notFound("unknown endpoint");
}

/**
 * Serve the app shell, with a status that tells the truth about the URL.
 *
 * `not_found_handling: single-page-application` answers everything with 200 and
 * index.html, which is right for a reader — the router renders "Page not found"
 * — and wrong for everything else. A crawler indexes the miss as a real page; a
 * link checker sweeps the site and reports it clean however many of its links
 * rot. So the routes that name a specific thing are checked against the index
 * first, and a miss gets the same shell with a 404 on it.
 *
 * The check costs an index read, but only the first time an isolate handles one
 * of these paths: index() memoises, and the same two indexes are already read
 * by /api/machines, /api/search and /pdf. Routes that name nothing in
 * particular — /, /search, /boards, /about — are not checked at all.
 */
const PAGE_ROUTES = [
  [/^\/machine\/(.+)$/, "machines", (idx, id) =>
    idx.some((m) => m.s === decodeURIComponent(id))],
  [/^\/doc\/(.+)$/, "docs", (idx, id) => idx.some((d) => d.id === id)],
  [/^\/board\/(.+)$/, "boards", (idx, id) =>
    idx.some((b) => b.slug === decodeURIComponent(id))],
  [/^\/rom\/(.+)$/, "rommaps", (idx, id) =>
    idx.some((r) => r.machine === decodeURIComponent(id))],
];

async function servePage(url, env, request) {
  const res = await env.ASSETS.fetch(request);
  for (const [re, name, has] of PAGE_ROUTES) {
    const m = url.pathname.match(re);
    if (!m) continue;
    const idx = await index(env, request, name);
    if (idx && !has(idx, m[1])) {
      // Same body, honest status. Rebuilt rather than mutated because a
      // Response from the binding has immutable headers.
      return new Response(res.body, {
        status: 404,
        headers: new Headers(res.headers),
      });
    }
    break;
  }
  return res;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      return handleApi(url, env, request);
    }

    // Original scans are not mirrored — send the reader to the source archive.
    const pdf = url.pathname.match(/^\/pdf\/([a-f0-9]{12})$/);
    if (pdf) {
      const docs = (await index(env, request, "docs")) || [];
      const doc = docs.find((d) => d.id === pdf[1]);
      if (!doc || !doc.src) return notFound("unknown document");
      // Most of this corpus has a second home in archive.org's arcademanuals
      // collection, and for a document the source has lost that copy is the
      // only one there is.
      if (doc.dead && doc.mirror) return Response.redirect(doc.mirror, 302);
      // Redirecting into a known 404 is worse than saying so: the reader ends
      // up on someone else's error page with no idea whose fault it is.
      if (doc.dead === "gone") {
        return json({
          error: "the source archive no longer has this file",
          document: doc.title, source: doc.src,
        }, 410);
      }
      return Response.redirect(doc.src, 302);
    }

    return servePage(url, env, request);
  },
};
