/* Cathode Ray Tomes front-end: client-side router + views over the Worker API. */

const app = document.getElementById("app");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const api = async (path) => {
  const r = await fetch("/api/" + path);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
};

/* ---------- theme ---------- */
const themeBtn = document.getElementById("theme");
const applyTheme = (t) => {
  if (t) document.documentElement.setAttribute("data-theme", t);
  else document.documentElement.removeAttribute("data-theme");
};
applyTheme(localStorage.getItem("crt-theme"));
themeBtn.onclick = () => {
  const cur = document.documentElement.getAttribute("data-theme");
  const next = cur === "dark" ? "light" : cur === "light" ? "" : "dark";
  next ? localStorage.setItem("crt-theme", next) : localStorage.removeItem("crt-theme");
  applyTheme(next);
};

/* ---------- router ---------- */
const routes = [
  [/^\/$/, home],
  [/^\/machine\/(.+)$/, machine],
  [/^\/doc\/([a-f0-9]{12})$/, reader],
  [/^\/search\/?$/, search],
  [/^\/boards\/?$/, boards],
  [/^\/board\/(.+)$/, board],
  [/^\/about\/?$/, about],
];

async function route() {
  const path = location.pathname;
  for (const [re, view] of routes) {
    const m = path.match(re);
    if (m) {
      app.innerHTML = '<div class="spin">Loading…</div>';
      try { await view(...m.slice(1)); }
      catch (e) { app.innerHTML = `<div class="empty">Failed to load — ${esc(e.message)}</div>`; }
      window.scrollTo(0, 0);
      return;
    }
  }
  app.innerHTML = '<div class="empty">Page not found.</div>';
}

function go(href) {
  history.pushState({}, "", href);
  route();
}
document.addEventListener("click", (e) => {
  const a = e.target.closest("a");
  if (!a) return;
  const href = a.getAttribute("href") || "";
  if (href.startsWith("/") && !a.hasAttribute("download") && !a.target) {
    e.preventDefault();
    go(href);
  }
});
addEventListener("popstate", route);

/* ---------- home ---------- */
let allMachines = null;

async function home() {
  const q0 = new URLSearchParams(location.search).get("q") || "";
  app.innerHTML = `
    <div class="stats">
      <div class="stat"><b id="s1">—</b><span>Machines</span></div>
      <div class="stat"><b id="s2">—</b><span>Service documents</span></div>
      <div class="stat"><b id="s3">—</b><span>Digitised &amp; searchable</span></div>
      <div class="stat"><b id="s4">—</b><span>Pages OCR'd</span></div>
      <div class="stat"><b id="s5">—</b><span>KiCad conversions</span></div>
    </div>
    <div class="searchbar">
      <input id="q" placeholder="Search 7,812 machines by name, manufacturer or year…"
             value="${esc(q0)}" autocomplete="off" autofocus>
    </div>
    <div class="filters">
      <span class="chip" data-f="docs">Has manuals</span>
      <span class="chip" data-f="sch">Has schematics</span>
      <span class="chip" data-f="kicad">KiCad conversion</span>
    </div>
    <div id="results" class="rows"></div>`;

  if (!allMachines) allMachines = (await api("machines?limit=200")).results;
  const boardList = await api("boards").catch(() => []);
  const boardSlugs = new Set(boardList.map((b) => b.slug));

  const st = await api("stats");
  const put = (id, v) => (document.getElementById(id).textContent = v.toLocaleString());
  put("s1", st.machines); put("s2", st.documents);
  put("s3", st.digitised); put("s4", st.pages); put("s5", st.boards);

  const input = document.getElementById("q");
  const results = document.getElementById("results");
  const active = new Set();

  document.querySelectorAll(".chip[data-f]").forEach((c) => {
    c.onclick = () => {
      c.classList.toggle("on");
      active.has(c.dataset.f) ? active.delete(c.dataset.f) : active.add(c.dataset.f);
      render();
    };
  });

  let timer;
  input.oninput = () => { clearTimeout(timer); timer = setTimeout(render, 140); };

  async function render() {
    const q = input.value.trim();
    const data = await api(`machines?q=${encodeURIComponent(q)}&limit=150${active.has("docs") ? "&docs=1" : ""}`);
    let rows = data.results;
    if (active.has("sch")) rows = rows.filter((m) => m.k > 0);
    if (active.has("kicad")) rows = rows.filter((m) => boardSlugs.has(m.s));
    results.innerHTML = rows.length ? rows.map((m) => `
      <a class="row" href="/machine/${encodeURIComponent(m.s)}">
        <span class="nm">${esc(m.n)}</span>
        <span class="meta">${esc(m.m || "—")}${m.y ? " · " + esc(m.y) : ""}</span>
        <span class="grow"></span>
        ${boardSlugs.has(m.s) ? '<span class="badge kicad">KiCad</span>' : ""}
        ${m.k ? `<span class="badge doc">${m.k} schematic${m.k > 1 ? "s" : ""}</span>` : ""}
        ${m.d ? `<span class="badge">${m.d} doc${m.d > 1 ? "s" : ""}</span>` : ""}
        ${m.p ? `<span class="badge">${m.p} DIP</span>` : ""}
      </a>`).join("") : '<div class="empty">No machines match that search.</div>';
  }
  render();
}

/* ---------- machine detail ---------- */
async function machine(slug) {
  const m = await api("machine/" + encodeURIComponent(slug));
  const boardList = await api("boards").catch(() => []);
  const kb = boardList.find((b) => b.slug === slug);

  const cpu = (m.cpu || []).map((c) => `${esc(c.n)}${c.mhz ? ` @ ${c.mhz} MHz` : ""}`).join("<br>") || "—";
  const aud = (m.audio || []).map((a) => `${esc(a.n)}${a.mhz ? ` @ ${a.mhz} MHz` : ""}`).join("<br>") || "—";
  const disp = (m.display || []).map((d) =>
    `${esc(d.type || "")} ${d.w && d.h ? `${d.w}×${d.h}` : ""} ${d.hz ? `@ ${(+d.hz).toFixed(2)} Hz` : ""}${d.rot ? ` · rotated ${d.rot}°` : ""}`
  ).join("<br>") || "—";
  const inp = m.input || {};
  const ctrl = (inp.ctrl || []).map((c) => `${esc(c.type)}${c.btn ? ` · ${c.btn} btn` : ""}${c.ways ? ` · ${c.ways}-way` : ""}`).join("<br>") || "—";

  app.innerHTML = `
    <h1>${esc(m.name)}</h1>
    <p class="sub">${esc(m.mfr || "Unknown manufacturer")}${m.year ? " · " + esc(m.year) : ""}
      ${m.rom ? ` · <code>${esc(m.rom)}</code>` : ""}</p>

    ${kb ? `<div class="note"><b>KiCad conversion available.</b>
      This board has a hand-built KiCad project —
      <a href="/board/${esc(slug)}">open the schematic &amp; BOM viewer</a>.</div>` : ""}

    <h2>Hardware</h2>
    <div class="panel"><dl class="kv">
      <dt>CPU</dt><dd>${cpu}</dd>
      <dt>Audio</dt><dd>${aud}</dd>
      <dt>Display</dt><dd>${disp}</dd>
      <dt>Players</dt><dd>${inp.p ?? "—"}${inp.co ? ` · ${inp.co} coin slots` : ""}</dd>
      <dt>Controls</dt><dd>${ctrl}</dd>
    </dl></div>

    <h2>Documents (${(m.docs || []).length})</h2>
    ${docSections(m.docs || [])}

    ${(m.dip || []).length ? `<h2>DIP switch settings (${m.dip.length} banks)</h2>
      ${m.dip.map((b) => `<div class="panel" style="margin-bottom:12px">
        <strong>${esc(b.name)}</strong>
        ${b.loc ? `<span class="meta mono"> — ${esc(b.loc)}</span>` : ""}
        <table class="dip"><thead><tr><th>Setting</th><th>Switches</th></tr></thead><tbody>
        ${(b.opts || []).map((o) => `<tr class="${o.n === b.def ? "def" : ""}">
          <td>${esc(o.n)}${o.n === b.def ? " (default)" : ""}</td>
          <td class="sw">${esc(o.sw || "")}</td></tr>`).join("")}
        </tbody></table></div>`).join("")}` : ""}`;
}

/** Upstream filenames carry the real title but in filesystem form. */
function prettyTitle(f) {
  return (f || "Manual").replace(/\.pdf$/i, "").replace(/[_]+/g, " ").replace(/\s+/g, " ").trim();
}

/** Machines like Asteroids carry 49 documents across a dozen types; grouping
    them by type is the difference between a list and something navigable. */
function docSections(docs) {
  if (!docs.length) return '<div class="empty">No documents for this machine.</div>';
  const order = ["Technical Manual", "Manual", "Operating Manual", "Owner's Manual",
                 "Parts & Operating Manual", "Instruction Manual", "Kit Manual",
                 "Schematics", "Schematic Package", "Drawing Package", "Wiring Diagram",
                 "Troubleshooting", "Service Bulletin", "Parts Catalog", "Parts List"];
  const groups = new Map();
  docs.forEach((d) => {
    if (!groups.has(d.type)) groups.set(d.type, []);
    groups.get(d.type).push(d);
  });
  const rank = (t) => { const i = order.indexOf(t); return i < 0 ? order.length : i; };
  return [...groups.entries()]
    .sort((a, b) => rank(a[0]) - rank(b[0]) || a[0].localeCompare(b[0]))
    .map(([type, list]) => `
      <h2 style="margin-top:22px">${esc(type)} <span style="color:var(--ink-3);font-weight:400">(${list.length})</span></h2>
      <div class="rows">${list.map((d) => `
        <a class="row" href="/doc/${d.id}">
          <span class="nm">${esc(prettyTitle(d.title))}</span>
          <span class="meta">${d.ingested ? `${d.pages} page${d.pages > 1 ? "s" : ""}` : "not yet digitised"}</span>
          <span class="grow"></span>
          ${d.sections && d.pages >= 3 ? `<span class="badge">${d.sections} sections</span>` : ""}
          ${d.schematic ? '<span class="badge doc">schematic</span>' : ""}
        </a>`).join("")}</div>`).join("");
}

/* ---------- manual reader ---------- */
async function reader(id) {
  const doc = await api("doc/" + id);
  const pages = doc.pages || [];
  const outline = pages.length >= 3 ? (doc.outline || []) : [];
  let cur = 1, query = "";

  app.innerHTML = `
    <h1>${esc(prettyTitle(doc.title))}</h1>
    <p class="sub">
      ${doc.machineName ? `<a href="/machine/${encodeURIComponent(doc.machine)}">${esc(doc.machineName)}</a> · ` : ""}
      ${doc.type ? esc(doc.type) + " · " : ""}${pages.length} pages${outline.length ? ` · ${outline.length} sections` : ""} ·
      <a href="/pdf/${id}" target="_blank" rel="noopener">original scan ↗</a></p>

    <div class="docbar">
      <input id="find" placeholder="Search inside this manual…" autocomplete="off">
      <span class="hits" id="hits"></span>
      ${doc.parts ? `<button id="showparts" class="chip">Parts list (${doc.parts})</button>` : ""}
    </div>
    <div id="partsbox"></div>

    <div class="reader wide">
      <div class="side">
        ${outline.length ? '<h3>Contents</h3><div class="toc" id="toc"></div>' : '<h3>Pages</h3><div class="toc" id="toc"></div>'}
      </div>
      <div id="stage"></div>
    </div>`;

  const toc = document.getElementById("toc");
  const stage = document.getElementById("stage");
  const find = document.getElementById("find");
  const hits = document.getElementById("hits");

  toc.innerHTML = outline.length
    ? outline.map((h, i) => `<a href="#" data-p="${h.p}" data-i="${i}" class="l${h.lvl}">${esc(h.t)}<span class="pg">p${h.p}</span></a>`).join("")
    : pages.map((p) => `<a href="#" data-p="${p.n}" data-i="${p.n - 1}" class="l1">Page ${p.n}</a>`).join("");

  const pageText = (p) => (p.blocks || []).map((b) => b.t).join(" ");
  const rx = () => query.length >= 2
    ? new RegExp("(" + query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi") : null;
  const mark = (t) => { const r = rx(); return r ? esc(t).replace(r, "<mark>$1</mark>") : esc(t); };
  const stripBullet = (t) => t.replace(/^\s*([•·*\-–—]|\(?[a-z]\)|\(?\d{1,2}[.)])\s+/, "");

  /** Render a page's semantic blocks as real HTML. */
  function renderBlocks(p) {
    const out = [];
    let list = [], table = [];
    const flushList = () => { if (list.length) { out.push(`<ul>${list.join("")}</ul>`); list = []; } };
    const flushTable = () => {
      if (table.length) {
        out.push(`<div class="tblwrap"><table class="ocr-tbl"><tbody>${table.join("")}</tbody></table></div>`);
        table = [];
      }
    };
    for (const b of p.blocks || []) {
      if (b.k !== "li") flushList();
      if (b.k !== "tr") flushTable();
      switch (b.k) {
        case "h":    out.push(`<h3>${mark(b.t)}</h3>`); break;
        case "note": out.push(`<div class="callout">${mark(b.t)}</div>`); break;
        case "li":   list.push(`<li>${mark(stripBullet(b.t))}</li>`); break;
        case "tr":   table.push(`<tr>${b.t.split(/\s{3,}/).map((c) => `<td>${mark(c)}</td>`).join("")}</tr>`); break;
        default:     out.push(`<p>${mark(b.t)}</p>`);
      }
    }
    flushList(); flushTable();
    return out.join("") ||
      '<p class="lowconf">This page carries no recoverable text — it is a drawing or a photograph. ' +
      `<a href="/pdf/${id}" target="_blank" rel="noopener">See the original scan ↗</a></p>`;
  }

  function draw() {
    stage.innerHTML = `<div class="textview">${pages.map((p) => `
      <div class="pg-sep" id="p${p.n}">Page ${p.n}</div>
      ${renderBlocks(p)}`).join("")}</div>`;
  }

  function goto(n) {
    cur = Math.min(Math.max(1, n), pages.length);
    const el = document.getElementById("p" + cur);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    highlightToc();
  }

  function highlightToc() {
    let best = -1;
    const marks = outline.length ? outline : pages.map((p) => ({ p: p.n }));
    marks.forEach((h, i) => { if (h.p <= cur) best = i; });
    toc.querySelectorAll("a").forEach((a) => a.classList.toggle("on", +a.dataset.i === best));
  }

  function runSearch() {
    query = find.value.trim();
    const q = query.toLowerCase();
    draw();
    if (q.length < 2) {
      hits.textContent = "";
      toc.querySelectorAll("a").forEach((a) => a.classList.remove("hit"));
      return;
    }
    const matched = new Set();
    pages.forEach((p) => { if (pageText(p).toLowerCase().includes(q)) matched.add(p.n); });
    toc.querySelectorAll("a").forEach((a) => a.classList.toggle("hit", matched.has(+a.dataset.p)));
    hits.textContent = matched.size ? `${matched.size} page${matched.size > 1 ? "s" : ""} match` : "no matches";
    if (matched.size) goto(Math.min(...matched));
  }

  let timer;
  find.oninput = () => { clearTimeout(timer); timer = setTimeout(runSearch, 180); };
  toc.onclick = (e) => { const a = e.target.closest("a"); if (a) { e.preventDefault(); goto(+a.dataset.p); } };

  // Keep the contents list in step with what is on screen.
  addEventListener("scroll", () => {
    const seps = [...document.querySelectorAll(".pg-sep")];
    const top = seps.filter((s) => s.getBoundingClientRect().top < 120).pop();
    if (top) { cur = +top.id.slice(1); highlightToc(); }
  }, { passive: true });

  // Parts list, recovered from the manual's own illustrated parts pages.
  const partsBtn = document.getElementById("showparts");
  if (partsBtn) {
    let rows = null, open = false;
    partsBtn.onclick = async () => {
      const box = document.getElementById("partsbox");
      open = !open;
      partsBtn.classList.toggle("on", open);
      if (!open) { box.innerHTML = ""; return; }
      box.innerHTML = '<div class="spin">Loading parts…</div>';
      if (!rows) rows = await api("parts/" + id);
      box.innerHTML = `
        <div class="panel" style="padding:0;overflow:auto;margin-bottom:18px">
          <table class="bom"><thead><tr>
            <th>Item</th><th>Part number</th><th>Description</th><th>Page</th>
          </tr></thead><tbody>
          ${rows.map((r) => `<tr>
            <td class="q">${esc(r.item)}</td>
            <td class="refs">${esc(r.part)}</td>
            <td>${esc(r.desc)}</td>
            <td class="q"><a href="#" data-p="${r.page}">p${r.page}</a></td>
          </tr>`).join("")}
          </tbody></table>
        </div>`;
      box.querySelectorAll("a[data-p]").forEach((a) => {
        a.onclick = (e) => { e.preventDefault(); goto(+a.dataset.p); };
      });
    };
  }

  draw();
  highlightToc();
}

/* ---------- corpus-wide search ---------- */
async function search() {
  const q0 = new URLSearchParams(location.search).get("q") || "";
  app.innerHTML = `
    <h1>Search the manuals</h1>
    <p class="sub">Full text across every digitised document — procedures, part numbers,
       chip designations, DIP settings.</p>
    <div class="searchbar">
      <input id="q" placeholder="e.g. fuse replacement, self test, 74153…"
             value="${esc(q0)}" autocomplete="off" autofocus>
    </div>
    <div id="out"></div>`;

  const input = document.getElementById("q");
  const out = document.getElementById("out");
  let timer;

  async function run() {
    const q = input.value.trim();
    const url = new URL(location.href);
    q ? url.searchParams.set("q", q) : url.searchParams.delete("q");
    history.replaceState({}, "", url);
    if (q.length < 3) { out.innerHTML = '<div class="empty">Type at least three characters.</div>'; return; }
    out.innerHTML = '<div class="spin">Searching…</div>';
    const d = await api("search?q=" + encodeURIComponent(q));
    if (!d.results.length) {
      out.innerHTML = `<div class="empty">Nothing found for “${esc(q)}”.</div>`;
      return;
    }
    out.innerHTML = `<p class="sub">${d.total} document${d.total > 1 ? "s" : ""} match</p>
      <div class="rows">${d.results.map((r) => `
        <a class="row" href="/doc/${r.id}">
          <span class="nm">${esc(prettyTitle(r.title))}</span>
          <span class="meta">${esc(r.machineName || "")}</span>
          <span class="grow"></span>
          ${r.sections ? `<span class="badge">${r.sections} sections</span>` : ""}
          <span class="badge doc">${r.hits} hit${r.hits > 1 ? "s" : ""}</span>
        </a>`).join("")}</div>`;
  }

  input.oninput = () => { clearTimeout(timer); timer = setTimeout(run, 220); };
  if (q0) run(); else out.innerHTML = '<div class="empty">Type to search.</div>';
}

/* ---------- boards index ---------- */
async function boards() {
  const list = await api("boards");
  app.innerHTML = `
    <h1>KiCad conversions</h1>
    <p class="sub">Boards rebuilt from the original drawings as real KiCad projects,
       with browsable schematics and bills of materials.</p>
    ${list.length ? `<div class="rows">${list.map((b) => `
      <a class="row" href="/board/${esc(b.slug)}">
        <span class="nm">${esc(b.name)}</span>
        <span class="meta">${esc(b.mfr || "")}${b.year ? " · " + esc(b.year) : ""}</span>
        <span class="grow"></span>
        <span class="badge">${b.devices} devices</span>
        <span class="badge ${b.netsTraced ? "kicad" : ""}">${b.netsTraced ? "nets traced" : "components only"}</span>
      </a>`).join("")}</div>` : '<div class="empty">No conversions published yet.</div>'}`;
}

/* ---------- board: schematic + BOM ---------- */
async function board(slug) {
  const list = await api("boards");
  const b = list.find((x) => x.slug === slug);
  if (!b) { app.innerHTML = '<div class="empty">Unknown board.</div>'; return; }

  app.innerHTML = `
    <h1>${esc(b.name)} — board</h1>
    <p class="sub">${esc(b.mfr || "")}${b.year ? " · " + esc(b.year) : ""}
      ${b.drawing ? ` · drawing <code>${esc(b.drawing)}</code>` : ""}</p>
    ${b.status ? `<div class="note"><b>Conversion status.</b> ${esc(b.status)}</div>` : ""}
    ${b.ibom ? `<h2>Board</h2>
    <p class="sub">Every device at its position on the board, cross-linked to the bill of
       materials — click a row to find the part, or a part to find the row.</p>
    <div class="zoombar"><a href="${esc(b.ibom)}" target="_blank" rel="noopener">Open full board view ↗</a></div>
    <iframe class="ibom" src="${esc(b.ibom)}" title="Interactive board view" loading="lazy"></iframe>` : ""}

    <h2>Find a chip</h2>
    <div class="searchbar">
      <input id="chipq" placeholder="Board position or part — e.g. C4, 74LS157, state machine…" autocomplete="off">
    </div>
    <div id="chipout"></div>

    <h2>Schematic</h2>
    <div class="zoombar">
      <button id="zi">+</button><button id="zo">−</button><button id="zr">reset</button>
      <span class="grow"></span>
      <a href="${esc(b.svg)}" target="_blank" rel="noopener">Open SVG ↗</a>
    </div>
    <div class="svgwrap" id="wrap"><img id="svg" src="${esc(b.svg)}" alt="Schematic"></div>
    <h2>Bill of materials</h2>
    <div class="searchbar"><input id="bq" placeholder="Filter by value or reference…" autocomplete="off"></div>
    <div class="panel" style="padding:0;overflow:auto">
      <table class="bom"><thead><tr>
        <th data-k="value">Value</th><th data-k="qty">Qty</th>
        <th data-k="refs">References (board grid position)</th>
      </tr></thead><tbody id="bom"></tbody></table>
    </div>`;

  /* chip lookup — "what is at C4, and what does it do?" */
  const chipq = document.getElementById("chipq");
  if (chipq) {
    let idx = null;
    const out = document.getElementById("chipout");
    chipq.oninput = async () => {
      const q = chipq.value.trim().toLowerCase();
      if (!q) { out.innerHTML = ""; return; }
      if (!idx) idx = await api("chips/" + slug).catch(() => ({}));
      const hits = Object.entries(idx).filter(([d, v]) =>
        d.toLowerCase() === q || d.toLowerCase().startsWith(q) ||
        (v.part || "").toLowerCase().includes(q) ||
        (v.section || "").toLowerCase().includes(q)).slice(0, 40);
      out.innerHTML = hits.length ? `<div class="rows">${hits.map(([d, v]) => `
          <div class="row">
            <span class="nm mono">${esc(d)}</span>
            <span class="badge doc">${esc(v.part)}</span>
            <span class="meta">${esc(v.section || "")}</span>
            <span class="grow"></span>
            ${v.otherRev ? `<span class="badge" title="same chip on the other revision">${esc(v.otherRev)} on other rev</span>` : ""}
          </div>`).join("")}</div>`
        : `<div class="empty">Nothing matches “${esc(chipq.value)}” on this board.</div>`;
    };
  }

  /* pan + zoom */
  const wrap = document.getElementById("wrap"), img = document.getElementById("svg");
  let z = 1, x = 0, y = 0, dragging = false, sx = 0, sy = 0;
  const paint = () => { img.style.transform = `translate(${x}px,${y}px) scale(${z})`; };
  document.getElementById("zi").onclick = () => { z *= 1.3; paint(); };
  document.getElementById("zo").onclick = () => { z /= 1.3; paint(); };
  document.getElementById("zr").onclick = () => { z = 1; x = y = 0; paint(); };
  wrap.onwheel = (e) => {
    e.preventDefault();
    const f = e.deltaY < 0 ? 1.12 : 1 / 1.12;
    const r = wrap.getBoundingClientRect();
    const mx = e.clientX - r.left, my = e.clientY - r.top;
    x = mx - (mx - x) * f; y = my - (my - y) * f; z *= f; paint();
  };
  wrap.onpointerdown = (e) => { dragging = true; sx = e.clientX - x; sy = e.clientY - y; wrap.classList.add("drag"); wrap.setPointerCapture(e.pointerId); };
  wrap.onpointermove = (e) => { if (dragging) { x = e.clientX - sx; y = e.clientY - sy; paint(); } };
  wrap.onpointerup = () => { dragging = false; wrap.classList.remove("drag"); };

  /* BOM */
  const rows = await fetch(b.bom).then((r) => r.text()).then(parseCsv);
  const tbody = document.getElementById("bom");
  const bq = document.getElementById("bq");
  let sortKey = "value", asc = true;

  function draw() {
    const q = bq.value.trim().toLowerCase();
    let out = rows.filter((r) => !q || r.value.toLowerCase().includes(q) || r.refs.toLowerCase().includes(q));
    out.sort((a, c) => {
      const va = sortKey === "qty" ? a.qty : a[sortKey].toLowerCase();
      const vc = sortKey === "qty" ? c.qty : c[sortKey].toLowerCase();
      return (va < vc ? -1 : va > vc ? 1 : 0) * (asc ? 1 : -1);
    });
    const total = out.reduce((s, r) => s + r.qty, 0);
    tbody.innerHTML = out.map((r) => `<tr>
        <td><strong>${esc(r.value)}</strong></td>
        <td class="q">${r.qty}</td>
        <td class="refs">${esc(r.refs)}</td></tr>`).join("")
      + `<tr><td colspan="3" style="color:var(--ink-3)">${out.length} line items · ${total} devices</td></tr>`;
  }
  document.querySelectorAll("table.bom th").forEach((th) => {
    th.onclick = () => { const k = th.dataset.k; asc = sortKey === k ? !asc : true; sortKey = k; draw(); };
  });
  bq.oninput = draw;
  draw();
}

/** Minimal RFC4180-ish CSV parse for the kicad-cli BOM export. */
function parseCsv(text) {
  const lines = [];
  let field = "", row = [], inQ = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQ) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') inQ = false;
      else field += c;
    } else if (c === '"') inQ = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field); lines.push(row); row = []; field = ""; }
    else if (c !== "\r") field += c;
  }
  if (field || row.length) { row.push(field); lines.push(row); }
  const [head, ...body] = lines.filter((r) => r.length > 1);
  const iRef = head.findIndex((h) => /reference/i.test(h));
  const iVal = head.findIndex((h) => /value/i.test(h));
  const iQty = head.findIndex((h) => /quantity|qty/i.test(h));
  return body.filter((r) => r[iVal]).map((r) => ({
    refs: r[iRef] || "", value: r[iVal] || "", qty: parseInt(r[iQty] || "1", 10) || 1,
  }));
}

/* ---------- about ---------- */
async function about() {
  app.innerHTML = `
    <h1>About Cathode Ray Tomes</h1>
    <p class="sub">Modern, searchable editions of arcade service documentation.</p>
    <div class="panel">
      <p>Arcade service manuals survive almost entirely as flat scans — page images with
      no text layer, no structure and no way to search them. Cathode Ray Tomes takes those scans and
      rebuilds them as web documents: every page OCR'd and searchable, every machine
      cross-referenced against its hardware specification and DIP switch settings.</p>
      <p>For a small number of boards we go further and rebuild the schematic itself as a
      real KiCad project, giving a browsable schematic and an accurate bill of materials
      that can actually be sourced against.</p>
      <h2>Sources</h2>
      <p>Scanned documents come from <a href="https://arcadertfm.com/">ArcadeRTFM</a>.
      Machine hardware metadata (CPUs, displays, inputs, DIP switches) derives from the
      <a href="https://www.mamedev.org/">MAME</a> project. Manuals remain the property of
      their respective publishers and are presented here for preservation and repair
      reference.</p>
      <h2>Honest status</h2>
      <p>OCR quality varies with the source scan; 1970s and 80s documents are frequently
      typewritten, faded or hand-annotated, and the recovered text reflects that. KiCad
      conversions state plainly whether nets have been traced or only the component
      complement has been captured.</p>
    </div>`;
}

route();
