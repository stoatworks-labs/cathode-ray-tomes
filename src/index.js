/**
 * Cathode Ray Tomes — Worker entry point.
 *
 * Serves the static browse/reader UI from the ASSETS binding and a small JSON
 * API over the corpus. Everything the site serves — indexes, per-machine
 * records and the rendered documents themselves — lives in KV (binding INDEX).
 * Original scans are not hosted; requests for one redirect to the source
 * archive.
 */

// API responses are re-derived whenever the corpus is re-ingested, so they get
// a short TTL. Only the immutable R2 objects below are cached hard.
const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "public, max-age=60, stale-while-revalidate=600",
};

const json = (data, status = 200, extra = {}) =>
  new Response(JSON.stringify(data), { status, headers: { ...JSON_HEADERS, ...extra } });

const notFound = (what = "not found") => json({ error: what }, 404);

/**
 * Index blobs are read on nearly every request, so they are cached in the
 * isolate — but only briefly. Isolates are long-lived, and an unbounded cache
 * means a re-ingested index is never picked up until the isolate recycles.
 */
const MEMO_TTL_MS = 60_000;
const memo = new Map();
async function indexBlob(env, key) {
  const hit = memo.get(key);
  if (hit && Date.now() - hit.at < MEMO_TTL_MS) return hit.val;
  const val = await env.INDEX.get(key, { type: "json" });
  if (val) memo.set(key, { val, at: Date.now() });
  return val;
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

async function handleApi(url, env) {
  const p = url.pathname.replace(/^\/api\//, "");

  // /api/machines?q=&limit=  — name/manufacturer search over the browse index.
  if (p === "machines") {
    const q = (url.searchParams.get("q") || "").trim().toLowerCase();
    const limit = Math.min(+url.searchParams.get("limit") || 50, 200);
    const onlyDocs = url.searchParams.get("docs") === "1";
    const machines = (await indexBlob(env, "machines")) || [];
    let out = machines;
    if (onlyDocs) out = out.filter((m) => m.d > 0);
    if (q) {
      out = out
        .map((m) => [scoreMachine(m, q), m])
        .filter(([s]) => s >= 0)
        .sort((a, b) => b[0] - a[0])
        .map(([, m]) => m);
    }
    return json({ total: out.length, results: out.slice(0, limit) });
  }

  // /api/machine/<slug> — full detail record (specs, DIP switches, docs).
  if (p.startsWith("machine/")) {
    const slug = decodeURIComponent(p.slice("machine/".length));
    const rec = await env.INDEX.get(`m:${slug}`, { type: "json" });
    return rec ? json(rec) : notFound("unknown machine");
  }

  // /api/doc/<id> — OCR text + page manifest, enriched with catalogue metadata.
  if (p.startsWith("doc/")) {
    const id = p.slice("doc/".length);
    if (!/^[a-f0-9]{12}$/.test(id)) return notFound("bad doc id");
    const body = await env.INDEX.get(`d:${id}`, { type: "json" });
    if (!body) return notFound("document not digitised yet");
    const docs = (await indexBlob(env, "docs")) || [];
    const meta = docs.find((d) => d.id === id) || {};
    // Pick catalogue fields explicitly: a blanket spread let the catalogue's
    // `pages` count overwrite the document's `pages` array.
    const { title, type, machine, machineName, src, schematic } = meta;
    return json({ ...body, title, type, machine, machineName, src, schematic });
  }

  // /api/chip/<part> — which machines use a given chip (from MAME metadata).
  if (p.startsWith("chip/")) {
    const part = decodeURIComponent(p.slice("chip/".length)).toLowerCase();
    const idx = (await indexBlob(env, "chips")) || {};
    return json({ chip: part, machines: idx[part] || [] });
  }

  // /api/search?q= — full-text over OCR'd manuals via the token postings list.
  // All terms must be present in a document; documents are ranked by total
  // occurrences so the manual that actually covers a part sorts above a
  // schematic that merely prints it once in a corner.
  if (p === "search") {
    const q = (url.searchParams.get("q") || "").trim().toLowerCase();
    const limit = Math.min(+url.searchParams.get("limit") || 60, 200);
    if (q.length < 3) return json({ query: q, total: 0, results: [] });

    const terms = [...new Set(q.split(/\s+/).filter((t) => t.length >= 3))];
    if (!terms.length) return json({ query: q, total: 0, results: [] });

    // Postings are sharded by leading character; fetch only the shards this
    // query touches rather than the whole index.
    const shardOf = (t) => (/[a-z0-9]/.test(t[0]) ? t[0] : "_");
    const shards = {};
    await Promise.all([...new Set(terms.map(shardOf))].map(async (sh) => {
      shards[sh] = (await indexBlob(env, `p:${sh}`)) || {};
    }));

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

    const docs = (await indexBlob(env, "docs")) || [];
    const byId = new Map(docs.map((d) => [d.id, d]));
    const ranked = [...(scores || new Map())]
      .sort((a, b) => b[1] - a[1])
      .map(([id, n]) => {
        const d = byId.get(id);
        return d ? { ...d, hits: n } : null;
      })
      .filter(Boolean);
    return json({ query: q, terms, total: ranked.length, results: ranked.slice(0, limit) });
  }

  // /api/stats — corpus totals, derived rather than hard-coded so the site
  // reports digitisation progress honestly while ingest is still running.
  if (p === "stats") {
    const machines = (await indexBlob(env, "machines")) || [];
    const docs = (await indexBlob(env, "docs")) || [];
    const boards = (await indexBlob(env, "boards")) || [];
    const digitised = docs.filter((d) => d.ingested);
    return json({
      machines: machines.length,
      machinesWithDocs: machines.filter((m) => m.d > 0).length,
      documents: docs.length,
      schematics: docs.filter((d) => d.schematic).length,
      digitised: digitised.length,
      pages: digitised.reduce((n, d) => n + (d.pages || 0), 0),
      sections: digitised.reduce((n, d) => n + (d.sections || 0), 0),
      boards: boards.length,
    });
  }

  // /api/boards — machines that have a hand-built KiCad conversion.
  if (p === "boards") {
    return json((await indexBlob(env, "boards")) || []);
  }

  return notFound("unknown endpoint");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/api/")) {
      return handleApi(url, env);
    }

    // Original scans are not mirrored — send the reader to the source archive.
    const pdf = url.pathname.match(/^\/pdf\/([a-f0-9]{12})$/);
    if (pdf) {
      const docs = (await indexBlob(env, "docs")) || [];
      const doc = docs.find((d) => d.id === pdf[1]);
      if (!doc || !doc.src) return notFound("unknown document");
      return Response.redirect(doc.src, 302);
    }

    return env.ASSETS.fetch(request);
  },
};
