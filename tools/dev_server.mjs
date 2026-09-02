/**
 * Serve the site locally without workerd.
 *
 *   node tools/dev_server.mjs [port]      (default 8790)
 *
 * `wrangler dev` cannot spawn workerd on this machine (`spawn EBADF`), and
 * `python3 -m http.server` serves the assets but none of the JSON API, so the
 * app's every list and reader page fails. This runs the real Worker in Node
 * against a stub ASSETS binding with the production contract — a path that
 * does not exist answers 200 and index.html, exactly as
 * `not_found_handling: single-page-application` does — so what a browser sees
 * here is what it sees deployed, submissions aside.
 *
 * Edits to web/ show on reload. Edits to src/ need a restart: the module is
 * imported once.
 */
import http from "node:http";
import { readFileSync, statSync, existsSync } from "node:fs";
import { join, extname, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const WEB = join(ROOT, "web");
const PORT = +process.argv[2] || 8790;
const worker = (await import(join(ROOT, "src", "index.js"))).default;

const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".webp": "image/webp", ".png": "image/png",
  ".svg": "image/svg+xml", ".csv": "text/csv", ".txt": "text/plain",
  ".webmanifest": "application/manifest+json",
};

const env = {
  SITE_NAME: "Cathode Ray Tomes",
  UPSTREAM: "https://files.arcadertfm.com",
  SUBMISSIONS_REPO: "stoatworks-labs/cathode-ray-tomes-submissions",
  SUBMISSIONS_BRANCH: "main",
  ASSETS: {
    async fetch(req) {
      const path = decodeURIComponent(new URL(req.url).pathname);
      const file = join(WEB, path);
      if (!path.endsWith("/") && file.startsWith(WEB) && existsSync(file) && statSync(file).isFile()) {
        return new Response(readFileSync(file), {
          headers: { "content-type": MIME[extname(file)] || "application/octet-stream" },
        });
      }
      return new Response(readFileSync(join(WEB, "index.html")), {
        headers: { "content-type": "text/html; charset=utf-8" },
      });
    },
  },
};

http.createServer(async (req, res) => {
  try {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const init = { method: req.method, headers: req.headers };
    if (chunks.length) init.body = Buffer.concat(chunks);
    const r = await worker.fetch(new Request(`http://127.0.0.1:${PORT}${req.url}`, init), env);
    res.writeHead(r.status, Object.fromEntries(r.headers));
    res.end(Buffer.from(await r.arrayBuffer()));
  } catch (e) {
    res.writeHead(500, { "content-type": "text/plain" });
    res.end(String(e.stack || e));
  }
}).listen(PORT, "127.0.0.1", () => console.log(`http://127.0.0.1:${PORT}`));
