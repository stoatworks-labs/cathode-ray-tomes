/**
 * Cathode Ray Tomes — reader submissions.
 *
 * The corpus is not finished and never will be: ArcadeRTFM is one archive, and
 * the documents that are actually missing tend to be the ones sitting in
 * somebody's loft. This endpoint takes a scan (or a link to one) from a reader
 * and commits it, with its provenance, to a GitHub repository where it can be
 * triaged and folded into the pipeline by hand.
 *
 * It deliberately does *not* touch the live corpus. Nothing submitted here
 * appears on the site until someone has looked at it, run it through
 * `tools/ingest.py`, and committed the result — the same path every other
 * document takes. The queue repo is separate from this one so that unvetted
 * uploads never sit in the tree Workers Builds deploys.
 *
 * Configuration (see wrangler.jsonc):
 *   SUBMISSIONS_REPO   var    "owner/name" of the queue repo. Absent => disabled.
 *   SUBMISSIONS_BRANCH var    Defaults to "main".
 *   GITHUB_TOKEN       secret Fine-grained PAT, contents:write + issues:write
 *                             on the queue repo only.
 *   TURNSTILE_SITEKEY  var    Optional. Both halves must be set for the
 *   TURNSTILE_SECRET   secret   challenge to be enforced.
 *   SUBMIT_LIMIT       binding Optional rate limiter, keyed on client IP.
 */

/** Per-file and whole-request caps.
 *
 * A Worker gets 128 MB of memory and base64 costs ~1.37x on top of the bytes
 * themselves, so the ceiling here is memory, not the platform's 100 MB body
 * limit. 20 MB covers a scanned service manual comfortably — the corpus
 * averages ~2 MB a document — and anything larger is better handed over as a
 * link, which the form also accepts.
 */
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL_BYTES = 25 * 1024 * 1024;
const MAX_FILES = 5;

/** Extensions a scan can plausibly arrive as, mapped to their magic bytes.
 *  `null` means the format has no signature worth checking. */
const ACCEPT = {
  pdf: [[0x25, 0x50, 0x44, 0x46]], // %PDF
  png: [[0x89, 0x50, 0x4e, 0x47]],
  jpg: [[0xff, 0xd8, 0xff]],
  jpeg: [[0xff, 0xd8, 0xff]],
  webp: [[0x52, 0x49, 0x46, 0x46]], // RIFF....WEBP
  tif: [[0x49, 0x49, 0x2a, 0x00], [0x4d, 0x4d, 0x00, 0x2a]],
  tiff: [[0x49, 0x49, 0x2a, 0x00], [0x4d, 0x4d, 0x00, 0x2a]],
  zip: [[0x50, 0x4b, 0x03, 0x04], [0x50, 0x4b, 0x05, 0x06]],
  txt: null,
  md: null,
  csv: null,
};

const DOC_TYPES = [
  "service manual",
  "schematic",
  "wiring diagram",
  "parts list",
  "operator / instruction sheet",
  "field service bulletin",
  "ROM or chip data",
  "photographs of a board",
  "other",
];

const TEXT = {
  "content-type": "application/json; charset=utf-8",
  // A submission is a one-shot side effect; nothing about it is cacheable.
  "cache-control": "no-store",
};

const reply = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: TEXT });

/* ---------- helpers ---------- */

const trim = (v, max) => String(v ?? "").replace(/\s+/g, " ").trim().slice(0, max);

/** Free text kept for a human to read: newlines survive, control codes do not. */
const prose = (v, max) =>
  String(v ?? "")
    .replace(/\r\n?/g, "\n")
    .replace(/[\x00-\x09\x0b\x0c\x0e-\x1f\x7f]/g, "")
    .trim()
    .slice(0, max);

const slugify = (s) =>
  trim(s, 60).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "unknown";

/**
 * Reduce an uploaded filename to something that cannot escape its directory or
 * confuse a checkout: no separators, no leading dot, ASCII only.
 */
function safeName(name) {
  const base = String(name || "file").split(/[\\/]/).pop();
  const dot = base.lastIndexOf(".");
  const stem = (dot > 0 ? base.slice(0, dot) : base).replace(/[^A-Za-z0-9._-]+/g, "-");
  const ext = (dot > 0 ? base.slice(dot + 1) : "").toLowerCase().replace(/[^a-z0-9]/g, "");
  return (stem.replace(/^[-.]+/, "").slice(0, 80) || "file") + (ext ? "." + ext.slice(0, 8) : "");
}

const extOf = (name) => (name.includes(".") ? name.split(".").pop().toLowerCase() : "");

/** Does the head of the file match one of the signatures we expect? */
function looksLike(bytes, ext) {
  const sigs = ACCEPT[ext];
  if (!sigs) return true;
  return sigs.some((sig) => sig.every((b, i) => bytes[i] === b));
}

/**
 * base64 in chunks. `String.fromCharCode(...bytes)` blows the argument limit
 * somewhere around a megabyte, which is well inside the sizes accepted here.
 */
function toBase64(bytes) {
  const CHUNK = 0x8000;
  let bin = "";
  for (let i = 0; i < bytes.length; i += CHUNK) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + CHUNK));
  }
  return btoa(bin);
}

/** Short, non-guessable directory suffix so two Pong submissions never collide. */
function token(n = 6) {
  const b = crypto.getRandomValues(new Uint8Array(n));
  return [...b].map((x) => "0123456789abcdefghijklmnopqrstuvwxyz"[x % 36]).join("");
}

const isHttpUrl = (s) => {
  try {
    const u = new URL(s);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
};

/* ---------- GitHub ---------- */

class GitHubError extends Error {}

async function gh(env, path, init = {}) {
  const res = await fetch(`https://api.github.com${path}`, {
    ...init,
    headers: {
      authorization: `Bearer ${env.GITHUB_TOKEN}`,
      accept: "application/vnd.github+json",
      "x-github-api-version": "2022-11-28",
      // GitHub rejects requests without one.
      "user-agent": "cathode-ray-tomes-submissions",
      ...(init.body ? { "content-type": "application/json" } : {}),
      ...(init.headers || {}),
    },
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new GitHubError(
      `${init.method || "GET"} ${path} -> ${res.status} ${detail.slice(0, 300)}`
    );
  }
  // Not every write answers with a body — read it as text first so a body-less
  // success is not mistaken for a parse failure.
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

/**
 * Commit every file of a submission in one go via the git data API.
 *
 * The contents API would be one commit per file; this is one commit for the
 * whole submission, which is what a reviewer wants to see. Blobs are uploaded
 * first and are reusable, so a lost race on the ref costs only the tree and
 * commit objects on retry.
 */
async function commitFiles(env, repo, branch, files, message) {
  const blobs = [];
  for (const f of files) {
    const { sha } = await gh(env, `/repos/${repo}/git/blobs`, {
      method: "POST",
      body: JSON.stringify({ content: f.base64, encoding: "base64" }),
    });
    blobs.push({ path: f.path, mode: "100644", type: "blob", sha });
  }

  for (let attempt = 0; attempt < 3; attempt++) {
    // An empty queue repo has no ref yet — the first submission creates it.
    let parent = null;
    try {
      const ref = await gh(env, `/repos/${repo}/git/ref/heads/${branch}`);
      parent = ref.object.sha;
    } catch (e) {
      if (!(e instanceof GitHubError) || !/-> 404/.test(e.message)) throw e;
    }

    const baseTree = parent
      ? (await gh(env, `/repos/${repo}/git/commits/${parent}`)).tree.sha
      : undefined;

    const tree = await gh(env, `/repos/${repo}/git/trees`, {
      method: "POST",
      body: JSON.stringify({ ...(baseTree ? { base_tree: baseTree } : {}), tree: blobs }),
    });

    const commit = await gh(env, `/repos/${repo}/git/commits`, {
      method: "POST",
      body: JSON.stringify({ message, tree: tree.sha, parents: parent ? [parent] : [] }),
    });

    try {
      if (parent) {
        await gh(env, `/repos/${repo}/git/refs/heads/${branch}`, {
          method: "PATCH",
          body: JSON.stringify({ sha: commit.sha }),
        });
      } else {
        await gh(env, `/repos/${repo}/git/refs`, {
          method: "POST",
          body: JSON.stringify({ ref: `refs/heads/${branch}`, sha: commit.sha }),
        });
      }
      return commit.sha;
    } catch (e) {
      // Someone else submitted between our read of the ref and our write of
      // it. Rebuild the tree on the new head and try again.
      const racy = e instanceof GitHubError && /-> (409|422)/.test(e.message);
      if (!racy || attempt === 2) throw e;
    }
  }
  throw new GitHubError("could not update ref");
}

/* ---------- guards ---------- */

async function turnstileOk(env, token, ip) {
  if (!env.TURNSTILE_SECRET || !env.TURNSTILE_SITEKEY) return true;
  if (!token) return false;
  const body = new FormData();
  body.set("secret", env.TURNSTILE_SECRET);
  body.set("response", token);
  if (ip) body.set("remoteip", ip);
  const res = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body,
  });
  if (!res.ok) return false;
  return Boolean((await res.json()).success);
}

async function withinRate(env, ip) {
  if (!env.SUBMIT_LIMIT || !ip) return true;
  const { success } = await env.SUBMIT_LIMIT.limit({ key: ip });
  return success;
}

/* ---------- the endpoint ---------- */

/** GET /api/submit — what the form needs to draw itself. */
export function submitConfig(env) {
  return reply({
    enabled: Boolean(env.SUBMISSIONS_REPO && env.GITHUB_TOKEN),
    maxFileBytes: MAX_FILE_BYTES,
    maxTotalBytes: MAX_TOTAL_BYTES,
    maxFiles: MAX_FILES,
    accept: Object.keys(ACCEPT),
    docTypes: DOC_TYPES,
    turnstileSiteKey: env.TURNSTILE_SITEKEY || null,
  });
}

/** POST /api/submit — multipart form: metadata plus zero or more files. */
export async function handleSubmit(request, env) {
  if (!env.SUBMISSIONS_REPO || !env.GITHUB_TOKEN) {
    return reply({ error: "Submissions are not configured on this deployment." }, 503);
  }

  const ip = request.headers.get("cf-connecting-ip") || "";
  if (!(await withinRate(env, ip))) {
    return reply({ error: "Too many submissions from this address. Try again shortly." }, 429);
  }

  let form;
  try {
    form = await request.formData();
  } catch {
    return reply({ error: "Could not read the form — the upload may have been truncated." }, 400);
  }

  // Hidden field, positioned off-screen: a human never fills it in.
  if (trim(form.get("website"), 200)) return reply({ ok: true, queued: false });

  if (!(await turnstileOk(env, form.get("cf-turnstile-response"), ip))) {
    return reply({ error: "Verification failed. Reload the page and try again." }, 400);
  }

  const machine = trim(form.get("machine"), 120);
  const provenance = prose(form.get("provenance"), 2000);
  const typed = trim(form.get("docType"), 60);
  const docType = DOC_TYPES.includes(typed) ? typed : "other";
  const manufacturer = trim(form.get("manufacturer"), 80);
  const year = trim(form.get("year"), 12);
  const notes = prose(form.get("notes"), 4000);
  const contact = trim(form.get("contact"), 120);
  const sourceUrl = trim(form.get("sourceUrl"), 500);
  const rights = form.get("rights") === "on" || form.get("rights") === "true";

  if (!machine) return reply({ error: "Tell us which machine this documents." }, 400);
  if (!provenance) return reply({ error: "Say where the document came from." }, 400);
  if (!rights) return reply({ error: "Please confirm the rights statement." }, 400);
  if (sourceUrl && !isHttpUrl(sourceUrl)) {
    return reply({ error: "The link must be an http or https URL." }, 400);
  }

  const uploads = form.getAll("files").filter((f) => f && typeof f === "object" && f.size > 0);
  if (!uploads.length && !sourceUrl) {
    return reply({ error: "Attach a file or give a link to one." }, 400);
  }
  if (uploads.length > MAX_FILES) {
    return reply({ error: `At most ${MAX_FILES} files per submission.` }, 400);
  }

  const dir = `incoming/${new Date().toISOString().slice(0, 10)}-${slugify(machine)}-${token()}`;
  const files = [];
  const manifest = [];
  let total = 0;

  for (const up of uploads) {
    const name = safeName(up.name);
    const ext = extOf(name);
    if (!(ext in ACCEPT)) {
      return reply(
        {
          error: `“${name}” is a .${ext || "?"} — accepted types are ${Object.keys(ACCEPT).join(", ")}.`,
        },
        400
      );
    }
    if (up.size > MAX_FILE_BYTES) {
      return reply(
        {
          error: `“${name}” is ${(up.size / 1048576).toFixed(1)} MB; the limit is ${
            MAX_FILE_BYTES / 1048576
          } MB. Host it somewhere and send the link instead.`,
        },
        413
      );
    }
    total += up.size;
    if (total > MAX_TOTAL_BYTES) {
      return reply(
        { error: `The whole submission must stay under ${MAX_TOTAL_BYTES / 1048576} MB.` },
        413
      );
    }

    const bytes = new Uint8Array(await up.arrayBuffer());
    if (!looksLike(bytes, ext)) {
      return reply({ error: `“${name}” does not contain ${ext.toUpperCase()} data.` }, 400);
    }
    // Two submitted files can share a name; the index keeps them apart.
    const rel = `files/${files.length + 1}-${name}`;
    files.push({ path: `${dir}/${rel}`, base64: toBase64(bytes) });
    manifest.push({ path: rel, bytes: up.size, type: up.type || "" });
  }

  const front = [
    "---",
    `machine: ${JSON.stringify(machine)}`,
    `manufacturer: ${JSON.stringify(manufacturer)}`,
    `year: ${JSON.stringify(year)}`,
    `docType: ${JSON.stringify(docType)}`,
    `sourceUrl: ${JSON.stringify(sourceUrl)}`,
    `contact: ${JSON.stringify(contact)}`,
    `submitted: ${JSON.stringify(new Date().toISOString())}`,
    "status: untriaged",
    "files:",
    ...(manifest.length
      ? manifest.map(
          (f) =>
            `  - { path: ${JSON.stringify(f.path)}, bytes: ${f.bytes}, type: ${JSON.stringify(f.type)} }`
        )
      : ["  []"]),
    "---",
  ].join("\n");

  const summary = [
    `# ${machine}${manufacturer ? ` — ${manufacturer}` : ""}${year ? ` (${year})` : ""}`,
    "",
    `**Type:** ${docType}`,
    "",
    "## Provenance",
    "",
    provenance,
    "",
    ...(sourceUrl ? ["## Link", "", `<${sourceUrl}>`, ""] : []),
    ...(notes ? ["## Notes from the submitter", "", notes, ""] : []),
    "## Triage",
    "",
    "- [ ] Document is legible and is what it says it is",
    "- [ ] Machine identified against `data/machines.json`",
    "- [ ] Rights position understood",
    "- [ ] Run through `tools/ingest.py` and committed to the corpus",
    "",
  ].join("\n");

  files.push({
    path: `${dir}/submission.md`,
    base64: toBase64(new TextEncoder().encode(`${front}\n\n${summary}`)),
  });

  const repo = env.SUBMISSIONS_REPO;
  const branch = env.SUBMISSIONS_BRANCH || "main";
  let sha;
  try {
    sha = await commitFiles(env, repo, branch, files, `Submission: ${machine} — ${docType}`);
  } catch (e) {
    console.error("submission commit failed", e.message);
    return reply(
      { error: "Could not file the submission. Nothing was lost on your side — please try again." },
      502
    );
  }

  // The commit is the submission; the issue is only the tracking handle for
  // it, so a failure here must not read as a failed submission.
  let issue = null;
  try {
    const created = await gh(env, `/repos/${repo}/issues`, {
      method: "POST",
      body: JSON.stringify({
        title: `${machine} — ${docType}`,
        body: [
          `Submitted through the website${contact ? ` by \`${contact}\`` : ""}.`,
          "",
          `Files: [\`${dir}\`](https://github.com/${repo}/tree/${branch}/${dir})`,
          "",
          "---",
          "",
          summary,
        ].join("\n"),
        labels: ["submission"],
      }),
    });
    issue = created.html_url;
  } catch (e) {
    console.error("submission issue failed", e.message);
  }

  return reply({ ok: true, queued: true, files: manifest.length, commit: sha.slice(0, 12), issue });
}
