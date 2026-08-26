/* Tests for the submission endpoint — the only write path in the Worker.
 *
 *   node tools/test_submit.mjs
 *
 * Runs `src/submit.js` directly against a stubbed GitHub API. It needs no
 * network and no credentials, and `wrangler dev` is not involved: miniflare
 * cannot spawn workerd under Node 26 on the machine this was written on.
 */
import { handleSubmit, submitConfig } from "../src/submit.js";

const env = {
  SUBMISSIONS_REPO: "stoatworks-labs/cathode-ray-tomes-submissions",
  SUBMISSIONS_BRANCH: "main",
  GITHUB_TOKEN: "test-token",
};

let calls = [];
const realFetch = globalThis.fetch;
globalThis.fetch = async (url, init = {}) => {
  const u = String(url);
  calls.push({ url: u, method: init.method || "GET", headers: init.headers || {},
    body: init.body ? JSON.parse(init.body) : null });
  const ok = (data) => new Response(JSON.stringify(data), { status: 200, headers: { "content-type": "application/json" } });
  if (/\/git\/blobs$/.test(u)) return ok({ sha: "blob" + calls.length });
  if (/\/git\/ref\/heads\//.test(u)) return ok({ object: { sha: "parentsha" } });
  if (/\/git\/commits\/parentsha$/.test(u)) return ok({ tree: { sha: "basetree" } });
  if (/\/git\/trees$/.test(u)) return ok({ sha: "newtree" });
  if (/\/git\/commits$/.test(u)) return ok({ sha: "c0ffee1234567890" });
  if (/\/git\/refs\/heads\/main$/.test(u)) return new Response(null, { status: 200 });
  if (/\/git\/refs$/.test(u)) return ok({ ref: "refs/heads/main", object: { sha: "c0ffee1234567890" } });
  if (/\/issues$/.test(u)) return ok({ html_url: "https://github.com/x/y/issues/1" });
  return new Response("unexpected " + u, { status: 500 });
};

const pdf = (kb = 4) => {
  const b = new Uint8Array(kb * 1024);
  b.set([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x34]);
  return b;
};

function req(fields, files = []) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) fd.set(k, v);
  for (const [name, bytes] of files) fd.append("files", new File([bytes], name, { type: "application/pdf" }));
  return new Request("https://cathode-ray-tomes.com/api/submit", {
    method: "POST",
    body: fd,
    headers: { "cf-connecting-ip": "203.0.113.9" },
  });
}

const good = {
  machine: "Asteroids Deluxe",
  manufacturer: "Atari",
  year: "1981",
  docType: "service manual",
  provenance: "Came with a board bought in 2004.",
  notes: "Pages 12-13 missing.",
  contact: "someone@example.com",
  rights: "on",
};

let pass = 0, fail = 0;
const check = (name, cond, extra = "") => {
  if (cond) { pass++; console.log("  ok   " + name); }
  else { fail++; console.log("  FAIL " + name + (extra ? " — " + extra : "")); }
};

async function run(label, fn) {
  console.log("\n" + label);
  calls = [];
  await fn();
}

await run("GET /api/submit config", async () => {
  const body = await submitConfig(env).json();
  check("enabled", body.enabled === true);
  check("advertises caps", body.maxFileBytes === 20971520 && body.maxFiles === 5);
  check("no token leaked", !JSON.stringify(body).includes("test-token"));
  const off = await submitConfig({}).json();
  check("disabled without config", off.enabled === false);
});

await run("happy path", async () => {
  const res = await handleSubmit(req(good, [["TM-143 manual.pdf", pdf(8)]]), env);
  const body = await res.json();
  check("200", res.status === 200, JSON.stringify(body));
  check("ok + queued", body.ok && body.queued && body.files === 1);
  check("commit sha reported", body.commit === "c0ffee123456");
  check("issue url reported", body.issue === "https://github.com/x/y/issues/1");
  check("no-store", res.headers.get("cache-control") === "no-store");

  const tree = calls.find((c) => /\/git\/trees$/.test(c.url)).body.tree;
  check("two blobs committed", tree.length === 2, JSON.stringify(tree.map((t) => t.path)));
  check("paths under incoming/", tree.every((t) => /^incoming\/\d{4}-\d\d-\d\d-asteroids-deluxe-[a-z0-9]{6}\//.test(t.path)),
    JSON.stringify(tree.map((t) => t.path)));
  check("filename sanitised", tree.some((t) => t.path.endsWith("/files/1-TM-143-manual.pdf")),
    JSON.stringify(tree.map((t) => t.path)));
  check("submission.md present", tree.some((t) => t.path.endsWith("/submission.md")));

  const md = Buffer.from(calls.filter((c) => /\/git\/blobs$/.test(c.url)).at(-1).body.content, "base64").toString();
  check("front matter", md.startsWith('---\nmachine: "Asteroids Deluxe"'));
  check("provenance kept", md.includes("Came with a board bought in 2004."));
  check("triage checklist", md.includes("- [ ] Run through `tools/ingest.py`"));

  const issue = calls.find((c) => /\/issues$/.test(c.url)).body;
  check("issue titled", issue.title === "Asteroids Deluxe — service manual");
  check("issue links the folder", /tree\/main\/incoming\//.test(issue.body));
  check("issue carries contact", issue.body.includes("someone@example.com"));

  check("every call authenticated", calls.every((c) => c.headers.authorization === "Bearer test-token"));
  check("every call sends a user-agent", calls.every((c) => Boolean(c.headers["user-agent"])));
});

await run("empty queue repo (no ref yet)", async () => {
  const outer = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    if (/\/git\/ref\/heads\//.test(String(url))) return new Response("Not Found", { status: 404 });
    return outer(url, init);
  };
  const res = await handleSubmit(req(good, [["m.pdf", pdf(2)]]), env);
  const body = await res.json();
  check("still succeeds", res.status === 200 && body.ok, JSON.stringify(body));
  const tree = calls.find((c) => /\/git\/trees$/.test(c.url)).body;
  check("no base_tree on first commit", tree.base_tree === undefined);
  const commit = calls.find((c) => /\/git\/commits$/.test(c.url) && c.method === "POST").body;
  check("no parents on first commit", Array.isArray(commit.parents) && commit.parents.length === 0);
  check("creates the ref", calls.some((c) => /\/git\/refs$/.test(c.url) && c.body?.ref === "refs/heads/main"));
  globalThis.fetch = outer;
});

await run("repository with no commits at all", async () => {
  // GitHub refuses the git data API outright on an empty repo — blobs included,
  // which is *before* the ref, so this cannot be handled at the ref. This is the
  // state every fresh deployment starts in, and it was a live bug.
  let seeded = false;
  const outer = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    const u = String(url);
    // These branches answer without delegating, so they record themselves.
    const note = () => calls.push({ url: u, method: init.method || "GET",
      headers: init.headers || {}, body: init.body ? JSON.parse(init.body) : null });
    if (/\/git\/blobs$/.test(u) && !seeded) {
      note();
      return new Response(JSON.stringify({ message: "Git Repository is empty." }), { status: 409 });
    }
    if (/\/contents\/README\.md$/.test(u)) {
      note();
      seeded = true;
      return new Response(JSON.stringify({ commit: { sha: "seed" } }), { status: 201 });
    }
    if (/\/git\/ref\/heads\//.test(u) && seeded) return new Response("Not Found", { status: 404 });
    return outer(url, init);
  };
  const res = await handleSubmit(req(good, [["m.pdf", pdf(2)]]), env);
  const body = await res.json();
  check("succeeds after seeding", res.status === 200 && body.ok, JSON.stringify(body));
  const seed = calls.find((c) => /\/contents\/README\.md$/.test(c.url));
  check("seeded through the contents API", Boolean(seed));
  check("seed sends no branch", seed && seed.body.branch === undefined);
  check("blobs retried after seeding", calls.filter((c) => /\/git\/blobs$/.test(c.url)).length === 3);
  check("the submission itself still committed", calls.some((c) => /\/git\/commits$/.test(c.url)));
  globalThis.fetch = outer;
});

await run("issue failure does not fail the submission", async () => {
  const outer = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    if (/\/issues$/.test(String(url))) return new Response("no", { status: 403 });
    return outer(url, init);
  };
  const body = await (await handleSubmit(req(good, [["m.pdf", pdf(2)]]), env)).json();
  check("ok with null issue", body.ok === true && body.issue === null, JSON.stringify(body));
  globalThis.fetch = outer;
});

await run("commit failure is reported", async () => {
  const outer = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    if (/\/git\/blobs$/.test(String(url))) return new Response("bad credentials", { status: 401 });
    return outer(url, init);
  };
  const res = await handleSubmit(req(good, [["m.pdf", pdf(2)]]), env);
  const body = await res.json();
  check("502", res.status === 502);
  check("no token in the error", !JSON.stringify(body).includes("test-token"), JSON.stringify(body));
  globalThis.fetch = outer;
});

await run("validation", async () => {
  const cases = [
    ["missing machine", { ...good, machine: "" }, [["m.pdf", pdf()]], 400],
    ["missing provenance", { ...good, provenance: "" }, [["m.pdf", pdf()]], 400],
    ["rights unconfirmed", { ...good, rights: "" }, [["m.pdf", pdf()]], 400],
    ["nothing attached", good, [], 400],
    ["bad url", { ...good, sourceUrl: "javascript:alert(1)" }, [], 400],
    ["disallowed type", good, [["boot.exe", pdf()]], 400],
    ["extension lies about content", good, [["x.pdf", new Uint8Array([0x4d, 0x5a, 0x90, 0x00])]], 400],
    ["too many files", good, Array.from({ length: 6 }, (_, i) => [`m${i}.pdf`, pdf(1)]), 400],
    ["file too large", good, [["big.pdf", pdf(21 * 1024)]], 413],
    ["total too large", good, [["a.pdf", pdf(13 * 1024)], ["b.pdf", pdf(13 * 1024)]], 413],
  ];
  for (const [name, fields, files, status] of cases) {
    calls = [];
    const res = await handleSubmit(req(fields, files), env);
    const body = await res.json();
    check(`${name} -> ${status}`, res.status === status, `${res.status} ${JSON.stringify(body)}`);
    check(`${name} wrote nothing`, calls.length === 0);
  }
});

await run("link-only submission", async () => {
  const res = await handleSubmit(req({ ...good, sourceUrl: "https://example.com/manual.pdf" }, []), env);
  const body = await res.json();
  check("accepted", res.status === 200 && body.ok && body.files === 0, JSON.stringify(body));
  const tree = calls.find((c) => /\/git\/trees$/.test(c.url)).body.tree;
  check("only submission.md", tree.length === 1 && tree[0].path.endsWith("submission.md"));
  const md = Buffer.from(calls.find((c) => /\/git\/blobs$/.test(c.url)).body.content, "base64").toString();
  check("link recorded", md.includes("<https://example.com/manual.pdf>") && md.includes("files:\n  []"));
});

await run("path traversal in filename", async () => {
  await handleSubmit(req(good, [["../../../etc/passwd.pdf", pdf(1)]]), env);
  const tree = calls.find((c) => /\/git\/trees$/.test(c.url)).body.tree;
  check("stays inside incoming/", tree.every((t) => t.path.startsWith("incoming/") && !t.path.includes("..")),
    JSON.stringify(tree.map((t) => t.path)));
});

await run("honeypot", async () => {
  const body = await (await handleSubmit(req({ ...good, website: "http://spam" }, [["m.pdf", pdf(1)]]), env)).json();
  check("looks accepted to the bot", body.ok === true && body.queued === false);
  check("nothing committed", calls.length === 0);
});

await run("rate limit", async () => {
  const limited = { ...env, SUBMIT_LIMIT: { limit: async () => ({ success: false }) } };
  const res = await handleSubmit(req(good, [["m.pdf", pdf(1)]]), limited);
  check("429", res.status === 429);
  check("nothing committed", calls.length === 0);
});

await run("turnstile enforced only when both halves are set", async () => {
  const withTs = { ...env, TURNSTILE_SITEKEY: "0xkey", TURNSTILE_SECRET: "0xsecret" };
  const res = await handleSubmit(req(good, [["m.pdf", pdf(1)]]), withTs);
  check("missing token rejected", res.status === 400);
  check("nothing committed", calls.length === 0);
});

await run("not configured", async () => {
  const res = await handleSubmit(req(good, [["m.pdf", pdf(1)]]), { SUBMISSIONS_REPO: "" });
  check("503", res.status === 503);
});

globalThis.fetch = realFetch;
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
