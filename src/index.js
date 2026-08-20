/**
 * Cathode Ray Tomes — Worker entry point.
 *
 * Serves the browse/reader UI and a small JSON API over the corpus. Everything
 * — indexes, per-machine records, rendered documents and the search postings —
 * ships as static assets alongside the code, so a deploy publishes code and
 * corpus together and there is no store to keep in step.
 *
 * Original scans are not hosted; /pdf/<id> redirects to the source archive.
 */

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
 */
async function asset(env, request, path) {
  const res = await env.ASSETS.fetch(new Request(new URL(path, request.url)));
  if (!res.ok) return null;
  return res.json();
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

/** Postings are sharded by leading character to keep each file small. */
const shardOf = (term) => (/^[a-z0-9]/.test(term[0]) ? term[0] : "_");

async function handleApi(url, env, request) {
  const p = url.pathname.replace(/^\/api\//, "");

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
    const onlyDocs = url.searchParams.get("docs") === "1";
    let out = (await index(env, request, "machines")) || [];
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
    const { title, type, machine, machineName, src, schematic } = meta;
    return json({ ...body, title, type, machine, machineName, src, schematic });
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

  if (p === "boards") {
    return json((await index(env, request, "boards")) || []);
  }

  return notFound("unknown endpoint");
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
      return Response.redirect(doc.src, 302);
    }

    return env.ASSETS.fetch(request);
  },
};
