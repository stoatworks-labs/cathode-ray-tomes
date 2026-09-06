/* Cathode Ray Tomes front-end: client-side router + views over the Worker API. */

const app = document.getElementById("app");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const api = async (path) => {
  const r = await fetch("/api/" + path);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json();
};

/* ---------- list navigation: letters and pages ----------
   The corpus is 7,823 machines and 1,469 ROM maps. A list that shows the
   first 150 and stops is not a list, so every long one gets the same two
   things: an A–Z bar and pages of PAGE_SIZE. Both live in the query string,
   so the back button, a reload and a shared link all land on the same page. */
const PAGE_SIZE = 50;
const LETTERS = ["#", ..."ABCDEFGHIJKLMNOPQRSTUVWXYZ"];

/** The letter a name files under: A–Z, or "#" for a name that starts with a
    digit or a symbol. Leading quotes and brackets are skipped, so "'88 Games"
    files under #. Mirrored in src/index.js, which pages the machine list. */
const initialOf = (name) => {
  const c = String(name || "").replace(/^[^a-z0-9]+/i, "").charAt(0).toUpperCase();
  return /[A-Z]/.test(c) ? c : "#";
};
const nameKey = (name) => String(name || "").replace(/^[^a-z0-9]+/i, "").toLowerCase();
const byName = (get) => (a, b) =>
  nameKey(get(a)).localeCompare(nameKey(get(b)), "en", { numeric: true });

const param = (k) => new URLSearchParams(location.search).get(k) || "";
/** Write list state into the URL without adding a history entry. */
function setParams(obj) {
  const url = new URL(location.href);
  for (const [k, v] of Object.entries(obj)) v ? url.searchParams.set(k, String(v)) : url.searchParams.delete(k);
  history.replaceState({}, "", url);
}

/** A–Z bar. `present` is the set of letters with anything under them; the
    rest are dimmed rather than dropped, so the bar keeps its shape. */
function letterBar(active, present) {
  return `<div class="letters" role="navigation" aria-label="By letter">
    <button data-letter="" class="${active ? "" : "on"}">All</button>
    ${LETTERS.map((l) => `<button data-letter="${l}" class="${l === active ? "on" : ""}"
       ${present && !present.has(l) ? "disabled" : ""}>${l}</button>`).join("")}
  </div>`;
}

/** Prev / first … window round the current page … last / Next, plus the
    range on show. Nothing when it all fits on one page. */
function pagerHtml(page, total, size = PAGE_SIZE) {
  const pages = Math.max(1, Math.ceil(total / size));
  if (pages <= 1) return "";
  const from = (page - 1) * size + 1, to = Math.min(total, page * size);
  const nums = [...new Set([1, pages, page - 2, page - 1, page, page + 1, page + 2]
    .filter((n) => n >= 1 && n <= pages))].sort((a, b) => a - b);
  let out = "", prev = 0;
  for (const n of nums) {
    if (n - prev > 1) out += '<span class="gap">…</span>';
    out += `<button data-page="${n}" class="${n === page ? "on" : ""}" ${n === page ? 'aria-current="page"' : ""}>${n}</button>`;
    prev = n;
  }
  return `<div class="pager" role="navigation" aria-label="Pages">
    <button data-page="${page - 1}" ${page <= 1 ? "disabled" : ""}>‹ Prev</button>
    ${out}
    <button data-page="${page + 1}" ${page >= pages ? "disabled" : ""}>Next ›</button>
    <span class="range">${from.toLocaleString()}–${to.toLocaleString()} of ${total.toLocaleString()}</span>
  </div>`;
}

/** One click handler for a container's letter and page buttons. */
function wireNav(box, onChange) {
  box.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-letter], button[data-page]");
    if (!b || b.disabled || !box.contains(b)) return;
    if (b.dataset.letter !== undefined) onChange({ letter: b.dataset.letter, page: 1 });
    else onChange({ page: +b.dataset.page });
  });
}

/** Bring a list back to the top of the window after a page change, under the
    sticky header (scroll-margin-top does the offset). */
const scrollToList = (box) => box.scrollIntoView({ block: "start" });

/**
 * A list held whole in memory, shown by letter and page. `name` picks the
 * field the letters file under, `row` renders one entry, `filter` (optional)
 * says whether an entry matches a typed query.
 */
function pagedList(box, items, { name, row, filter, empty = "Nothing under that letter." }) {
  let letter = param("letter").toUpperCase(), page = Math.max(1, +param("page") || 1), q = param("q");
  if (!LETTERS.includes(letter)) letter = "";
  const sorted = [...items].sort(byName(name));
  function draw() {
    let rows = sorted;
    if (q && filter) rows = rows.filter((it) => filter(it, q.toLowerCase()));
    const present = new Set(rows.map((it) => initialOf(name(it))));
    if (letter) rows = rows.filter((it) => initialOf(name(it)) === letter);
    page = Math.min(page, Math.max(1, Math.ceil(rows.length / PAGE_SIZE)));
    const slice = rows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    box.innerHTML = `${letterBar(letter, present)}
      ${slice.length ? `<div class="rows">${slice.map(row).join("")}</div>` : `<div class="empty">${empty}</div>`}
      ${pagerHtml(page, rows.length)}`;
  }
  wireNav(box, (ch) => {
    if (ch.letter !== undefined) letter = ch.letter;
    page = ch.page;
    setParams({ letter, page: page > 1 ? page : "" });
    draw();
    scrollToList(box);
  });
  draw();
  return { setQuery(nq) { q = nq; page = 1; setParams({ q, page: "" }); draw(); } };
}

/* ---------- lightbox: a scan, full size, over the page ----------
   The sheets are shown inline at column width, which is enough to see that a
   page is a schematic and not enough to read a designator on it. Clicking one
   opens it over the page at whatever size the reader wants: wheel or pinch to
   zoom, drag to pan, double-click for 1:1, arrow keys for the next sheet. */
let lb = null;

function ensureLightbox() {
  if (lb) return lb;
  const root = document.createElement("div");
  root.className = "lightbox";
  root.hidden = true;
  root.setAttribute("role", "dialog");
  root.setAttribute("aria-label", "Enlarged scan");
  root.innerHTML = `
    <div class="lb-bar">
      <span class="lb-title"></span><span class="grow"></span>
      <button data-lb="prev" title="Previous sheet (←)">‹</button>
      <span class="lb-count"></span>
      <button data-lb="next" title="Next sheet (→)">›</button>
      <span class="lb-sep"></span>
      <button data-lb="zo" title="Zoom out (−)">−</button>
      <button data-lb="zi" title="Zoom in (+)">+</button>
      <button data-lb="fit" title="Fit to window (0)">fit</button>
      <button data-lb="one" title="Actual size (1)">1:1</button>
      <a data-lb="open" target="_blank" rel="noopener" title="Open the image on its own">open ↗</a>
      <button data-lb="close" title="Close (Esc)">✕</button>
    </div>
    <div class="lb-stage"><img alt="" draggable="false"></div>`;
  document.body.appendChild(root);
  const stage = root.querySelector(".lb-stage");
  const img = root.querySelector("img");
  lb = { root, stage, img, items: [], i: 0, z: 1, x: 0, y: 0, nat: [0, 0] };

  const paint = () => { img.style.transform = `translate(${lb.x}px,${lb.y}px) scale(${lb.z})`; };
  const box = () => stage.getBoundingClientRect();
  const clamp = (z) => Math.min(Math.max(z, 0.05), 16);
  /** Zoom by `f` about a point given relative to the stage. */
  lb.zoomAt = (f, cx, cy) => {
    const nz = clamp(lb.z * f), k = nz / lb.z;
    lb.x = cx - (cx - lb.x) * k; lb.y = cy - (cy - lb.y) * k; lb.z = nz; paint();
  };
  lb.fit = () => {
    const r = box(); const [w, h] = lb.nat;
    if (!w || !h) return;
    // Opened before the overlay has a size (a tab in the background, a pane
    // mid-resize): fit on the next frame instead of to a zero-width stage.
    if (r.width < 32 || r.height < 32) { requestAnimationFrame(lb.fit); return; }
    lb.z = clamp(Math.min((r.width - 16) / w, (r.height - 16) / h));
    lb.x = (r.width - w * lb.z) / 2; lb.y = (r.height - h * lb.z) / 2; paint();
  };
  lb.one = (cx, cy) => {
    if (cx === undefined) { const r = box(); cx = r.width / 2; cy = r.height / 2; }
    lb.zoomAt(1 / lb.z, cx, cy);
  };
  lb.show = (i) => {
    const n = lb.items.length;
    lb.i = ((i % n) + n) % n;
    const it = lb.items[lb.i];
    root.querySelector(".lb-title").textContent = it.alt || "";
    root.querySelector(".lb-count").textContent = n > 1 ? `${lb.i + 1} / ${n}` : "";
    root.querySelector("[data-lb=open]").href = it.src;
    root.querySelectorAll("[data-lb=prev],[data-lb=next]").forEach((b) => { b.disabled = n < 2; });
    lb.nat = [it.w || 0, it.h || 0];
    img.width = it.w || 0; img.height = it.h || 0;
    img.src = it.src;
    lb.fit();
  };
  // A sheet whose size was not known up front is fitted once it has loaded.
  img.onload = () => {
    if (!lb.nat[0] || !lb.nat[1]) { lb.nat = [img.naturalWidth, img.naturalHeight]; lb.fit(); }
  };

  let moved = false;
  root.addEventListener("click", (e) => {
    const b = e.target.closest("[data-lb]");
    if (b) {
      const r = box();
      switch (b.dataset.lb) {
        case "close": closeLightbox(); break;
        case "prev": lb.show(lb.i - 1); break;
        case "next": lb.show(lb.i + 1); break;
        case "zi": lb.zoomAt(1.25, r.width / 2, r.height / 2); break;
        case "zo": lb.zoomAt(1 / 1.25, r.width / 2, r.height / 2); break;
        case "fit": lb.fit(); break;
        case "one": lb.one(); break;
        default: return;               // the open link is a real link
      }
      e.preventDefault();
      return;
    }
    // A click on the backdrop — not a drag that ended there — closes it.
    if (e.target === stage && !moved) closeLightbox();
  });
  stage.addEventListener("wheel", (e) => {
    e.preventDefault();
    const r = box();
    // A trackpad pinch arrives as a ctrl+wheel with small deltas; treat it as
    // continuous. A mouse wheel clicks in bigger, fixed steps.
    const f = e.ctrlKey ? Math.exp(-e.deltaY / 100) : (e.deltaY < 0 ? 1.15 : 1 / 1.15);
    lb.zoomAt(f, e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });

  // One pointer drags; two pinch (and drag by their midpoint).
  const pts = new Map();
  let start = null, pinch = null;
  const mid = () => {
    const [a, b] = [...pts.values()];
    return { x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2, d: Math.hypot(a[0] - b[0], a[1] - b[1]) };
  };
  stage.addEventListener("pointerdown", (e) => {
    stage.setPointerCapture(e.pointerId);
    pts.set(e.pointerId, [e.clientX, e.clientY]);
    moved = false;
    if (pts.size === 1) start = { x: lb.x, y: lb.y, px: e.clientX, py: e.clientY };
    else if (pts.size === 2) { const m = mid(); pinch = { ...m, x0: lb.x, y0: lb.y }; }
    stage.classList.add("drag");
  });
  stage.addEventListener("pointermove", (e) => {
    if (!pts.has(e.pointerId)) return;
    pts.set(e.pointerId, [e.clientX, e.clientY]);
    if (pts.size === 1 && start) {
      const dx = e.clientX - start.px, dy = e.clientY - start.py;
      if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
      lb.x = start.x + dx; lb.y = start.y + dy; paint();
    } else if (pts.size === 2 && pinch) {
      moved = true;
      const m = mid(), r = box();
      lb.x += m.x - pinch.x; lb.y += m.y - pinch.y;
      if (pinch.d > 0) lb.zoomAt(m.d / pinch.d, m.x - r.left, m.y - r.top); else paint();
      pinch = { ...pinch, ...m };
    }
  });
  const up = (e) => {
    pts.delete(e.pointerId);
    if (pts.size === 1) {
      const [[x, y]] = pts.values();
      start = { x: lb.x, y: lb.y, px: x, py: y }; pinch = null;
    } else if (!pts.size) { start = null; pinch = null; stage.classList.remove("drag"); }
  };
  stage.addEventListener("pointerup", up);
  stage.addEventListener("pointercancel", up);
  stage.addEventListener("dblclick", (e) => {
    const r = box();
    if (Math.abs(lb.z - 1) < 0.01) lb.fit();
    else lb.one(e.clientX - r.left, e.clientY - r.top);
  });
  document.addEventListener("keydown", (e) => {
    if (root.hidden) return;
    const r = box();
    switch (e.key) {
      case "Escape": closeLightbox(); break;
      case "ArrowLeft": lb.show(lb.i - 1); break;
      case "ArrowRight": lb.show(lb.i + 1); break;
      case "+": case "=": lb.zoomAt(1.25, r.width / 2, r.height / 2); break;
      case "-": case "_": lb.zoomAt(1 / 1.25, r.width / 2, r.height / 2); break;
      case "0": lb.fit(); break;
      case "1": lb.one(); break;
      default: return;
    }
    e.preventDefault();
  });
  addEventListener("resize", () => { if (!root.hidden) lb.fit(); });
  return lb;
}

/** `items` is [{src, alt, w, h}] — every sheet in the document, so the arrows
    step between them — and `i` the one clicked. */
function openLightbox(items, i) {
  const l = ensureLightbox();
  l.items = items;
  l.root.hidden = false;
  document.body.classList.add("lb-open");
  l.show(i);
  l.root.querySelector("[data-lb=close]").focus();
}

function closeLightbox() {
  if (!lb || lb.root.hidden) return;
  lb.root.hidden = true;
  lb.img.removeAttribute("src");
  document.body.classList.remove("lb-open");
}

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
  [/^\/roms\/?$/, rommaps],
  [/^\/rom\/(.+)$/, rommap],
  [/^\/board\/(.+)$/, board],
  [/^\/about\/?$/, about],
  [/^\/submit\/?$/, submit],
];

/* Listeners a view hangs on window die with the view, rather than piling up
   across every document opened in a session. */
let viewAbort = new AbortController();

async function route() {
  const path = location.pathname;
  viewAbort.abort();
  viewAbort = new AbortController();
  closeLightbox();
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
async function home() {
  const q0 = param("q");
  const active = new Set(param("f").split(",").filter(Boolean));
  let letter = param("letter").toUpperCase(), page = Math.max(1, +param("page") || 1);
  if (!LETTERS.includes(letter)) letter = "";
  const chip = (f, label) => `<span class="chip${active.has(f) ? " on" : ""}" data-f="${f}">${label}</span>`;

  app.innerHTML = `
    <div class="stats">
      <div class="stat"><b id="s1">—</b><span>Machines</span></div>
      <div class="stat"><b id="s6">—</b><span>Consoles &amp; handhelds</span></div>
      <div class="stat"><b id="s2">—</b><span>Service documents</span></div>
      <div class="stat"><b id="s3">—</b><span>Digitised &amp; searchable</span></div>
      <div class="stat"><b id="s4">—</b><span>Pages</span></div>
      <div class="stat"><b id="s5">—</b><span>KiCad conversions</span></div>
    </div>
    <div class="searchbar">
      <input id="q" placeholder="Search by name, manufacturer or year…"
             value="${esc(q0)}" autocomplete="off" autofocus>
    </div>
    <div class="filters">
      ${chip("docs", "Has manuals")}
      ${chip("sch", "Has schematics")}
      ${chip("kicad", "KiCad conversion")}
      ${chip("arcade", "Arcade")}
      ${chip("console", "Consoles &amp; handhelds")}
    </div>
    <div id="results" class="listbox"></div>`;

  // A board names the machine it belongs to; its own slug is the board's
  // (asteroids-03 … asteroids-06 all belong to `asteroid`), so the badge is
  // keyed on that field. Matching board slug to machine slug found 13 of 50.
  const boardList = await api("boards").catch(() => []);
  const boardMachines = new Set(boardList.map((b) => b.machine || b.slug));

  const st = await api("stats");
  const put = (id, v) => (document.getElementById(id).textContent = v.toLocaleString());
  put("s1", st.machines); put("s2", st.documents);
  put("s3", st.digitised); put("s4", st.pages); put("s5", st.boards);
  put("s6", st.systems || 0);

  const input = document.getElementById("q");
  const results = document.getElementById("results");
  const sync = () => setParams({
    q: input.value.trim(), f: [...active].join(","), letter, page: page > 1 ? page : "",
  });

  document.querySelectorAll(".chip[data-f]").forEach((c) => {
    c.onclick = () => {
      c.classList.toggle("on");
      active.has(c.dataset.f) ? active.delete(c.dataset.f) : active.add(c.dataset.f);
      page = 1; sync(); render();
    };
  });

  let timer;
  input.oninput = () => {
    clearTimeout(timer);
    timer = setTimeout(() => { page = 1; sync(); render(); }, 140);
  };

  wireNav(results, (ch) => {
    if (ch.letter !== undefined) letter = ch.letter;
    page = ch.page;
    sync(); render().then(() => scrollToList(results));
  });

  let seq = 0;
  async function render() {
    const my = ++seq;
    const q = input.value.trim();
    // Every filter is applied by the Worker before the page is cut, so the
    // totals and page counts are exact. Selecting both kind chips is the same
    // as selecting neither.
    const kind = active.has("arcade") === active.has("console") ? ""
               : active.has("arcade") ? "arcade" : "console";
    const qs = new URLSearchParams({ q, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE });
    if (letter) qs.set("letter", letter);
    if (kind) qs.set("kind", kind);
    for (const f of ["docs", "sch", "kicad"]) if (active.has(f)) qs.set(f, "1");
    const data = await api("machines?" + qs);
    if (my !== seq) return;                         // a later keystroke answered first
    const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));
    if (page > pages) { page = pages; sync(); return render(); }
    const rows = data.results;
    results.innerHTML = letterBar(letter) + (rows.length ? `<div class="rows">${rows.map((m) => `
      <a class="row" href="/machine/${encodeURIComponent(m.s)}">
        <span class="nm">${esc(m.n)}</span>
        <span class="meta">${esc(m.m || "—")}${m.y ? " · " + esc(m.y) : ""}</span>
        <span class="grow"></span>
        ${m.t ? `<span class="badge kind">${esc(m.t)}</span>` : ""}
        ${boardMachines.has(m.s) ? '<span class="badge kicad">KiCad</span>' : ""}
        ${m.k ? `<span class="badge doc">${m.k} schematic${m.k > 1 ? "s" : ""}</span>` : ""}
        ${m.d ? `<span class="badge">${m.d} doc${m.d > 1 ? "s" : ""}</span>` : ""}
        ${m.p ? `<span class="badge">${m.p} ${m.t ? "board rev" : "DIP"}${m.p > 1 && m.t ? "s" : ""}</span>` : ""}
      </a>`).join("")}</div>` : '<div class="empty">Nothing matches that search.</div>')
      + pagerHtml(page, data.total);
  }
  await render();
}

/* ---------- machine detail ---------- */
async function machine(slug) {
  const m = await api("machine/" + encodeURIComponent(slug));
  const boardList = await api("boards").catch(() => []);
  // A board names the machine it belongs to; its own slug is the board's
  // (asteroids-03 … asteroids-06 all belong to `asteroid`). Matching board
  // slug to machine slug found 13 of the 50 and told Asteroids it had none.
  const kbs = boardList.filter((b) => b.machine === slug || b.slug === slug);
  loadRomMap(slug);

  loadDiagnostics(slug);
  loadSignatures(slug);
  loadPower(slug);

  const cpu = (m.cpu || []).map((c) => `${esc(c.n)}${c.mhz ? ` @ ${c.mhz} MHz` : ""}`).join("<br>") || "—";
  const aud = (m.audio || []).map((a) => `${esc(a.n)}${a.mhz ? ` @ ${a.mhz} MHz` : ""}`).join("<br>") || "—";
  const disp = (m.display || []).map((d) =>
    `${esc(d.type || "")} ${d.w && d.h ? `${d.w}×${d.h}` : ""} ${d.hz ? `@ ${(+d.hz).toFixed(2)} Hz` : ""}${d.rot ? ` · rotated ${d.rot}°` : ""}`
  ).join("<br>") || "—";
  const inp = m.input || {};
  const ctrl = (inp.ctrl || []).map((c) => `${esc(c.type)}${c.btn ? ` · ${c.btn} btn` : ""}${c.ways ? ` · ${c.ways}-way` : ""}`).join("<br>") || "—";

  const isConsole = !!m.kind;

  app.innerHTML = `
    <h1>${esc(m.name)}</h1>
    <p class="sub">${esc(m.mfr || "Unknown manufacturer")}${m.year ? " · " + esc(m.year) : ""}
      ${m.rom ? ` · <code>${esc(m.rom)}</code>` : ""}
      ${isConsole ? ` · <span class="badge kind">${esc(m.kind)}</span>` : ""}</p>

    ${kbs.length ? `<div class="note"><b>${kbs.length > 1 ? `${kbs.length} board maps` : "Board map"} available.</b>
      ${kbs.length > 1 ? "This machine's boards have" : "This board has"} a hand-built KiCad
      project with a schematic and bill of materials —
      ${kbs.map((b) => `<a href="/board/${esc(b.slug)}">${esc(b.name)}</a>`).join(" · ")}.</div>` : ""}
    <div id="rommap"></div>

    <h2>Hardware</h2>
    <div class="panel"><dl class="kv">
      <dt>CPU</dt><dd>${cpu}</dd>
      <dt>Audio</dt><dd>${aud}</dd>
      <dt>Display</dt><dd>${disp}</dd>
      ${isConsole ? "" : `<dt>Players</dt><dd>${inp.p ?? "—"}${inp.co ? ` · ${inp.co} coin slots` : ""}</dd>
      <dt>Controls</dt><dd>${ctrl}</dd>`}
    </dl></div>

    ${(m.boards || []).length ? `<h2>Board revisions (${m.boards.length})</h2>
      <div class="panel"><dl class="kv">
      ${m.boards.map((b) => `<dt><code>${esc(b.rev)}</code></dt>
        <dd>${esc(b.note || "")}</dd>`).join("")}
      </dl></div>` : ""}

    <div id="power"></div>
    <div id="sigs"></div>
    <div id="diag"></div>

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

/** One manual can document several machines — the MVS service manual covers
    the MV-2F and the MV-4F — so link every machine it is filed under, not just
    the one that happens to own the record. */
function machineLinks(doc) {
  const slugs = doc.machines && doc.machines.length ? doc.machines
              : doc.machine ? [doc.machine] : [];
  if (!slugs.length) return "";
  const names = doc.machineNames && doc.machineNames.length === slugs.length
              ? doc.machineNames : slugs.map(() => doc.machineName || "");
  return slugs.map((s, i) =>
    `<a href="/machine/${encodeURIComponent(s)}">${esc(names[i] || s)}</a>`
  ).join(" · ") + " · ";
}

/** The footer credits ArcadeRTFM, which is where all but a handful of the
    scans come from. Anything else says so on the document itself. */
const SOURCE_NAMES = { gamingdoc: "GamingDoc", console5: "Console5" };

function sourceCredit(doc) {
  // Where the usual source has lost the file, the scan behind "original scan"
  // is somebody else's copy. Say so: it is a different archive with a
  // different address, and the reader should know whose page they land on.
  if (doc.mirror) {
    return ` · <span class="meta">source archive lost this one;</span> ` +
           `scan from <a href="${esc(doc.mirror)}" target="_blank"` +
           ` rel="noopener noreferrer">the Internet Archive ↗</a>`;
  }
  if (!doc.source || !doc.sourcePage) return "";
  const name = SOURCE_NAMES[doc.source] || doc.source;
  return ` · scan from <a href="${esc(doc.sourcePage)}" target="_blank"` +
         ` rel="noopener noreferrer">${esc(name)} ↗</a>`;
}

/** Machines like Asteroids carry 49 documents across a dozen types; grouping
    them by type is the difference between a list and something navigable. */
function docSections(docs) {
  if (!docs.length) return '<div class="empty">No documents for this machine.</div>';
  // Service material first, then reference, then the things that are neither.
  // A development manual and an ODE install guide are worth having and are not
  // what someone with a dead console came for, so they sort last rather than
  // sitting among the service manuals.
  const order = ["Service Manual", "Technical Manual", "Manual", "Operating Manual",
                 "Owner's Manual", "Parts & Operating Manual", "Instruction Manual",
                 "Kit Manual", "Schematics", "Schematic Package", "Drawing Package",
                 "Wiring Diagram", "Troubleshooting", "Service Bulletin",
                 "Parts Catalog", "Parts List", "Datasheet",
                 "Developer Manual", "Installation Guide"];
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
      <div class="rows">${list.map((d) => {
        // A document that cannot be read is still worth listing — the machine
        // really does have that schematic somewhere — but it must not look
        // like a link. Nothing is behind it but someone else's 404. Unless
        // archive.org has a working copy, in which case it is an ordinary
        // document again and only the scan comes from somewhere else.
        const why = d.mirror ? null
                  : d.dead === "gone" ? "the source archive no longer has this file"
                  : d.dead === "unreadable" ? "the source file is not a readable PDF"
                  : null;
        const meta = why ? why
                   : d.ingested ? `${d.pages} page${d.pages > 1 ? "s" : ""}`
                   : "not yet digitised";
        const inner = `
          <span class="nm">${esc(prettyTitle(d.title))}</span>
          <span class="meta">${esc(meta)}</span>
          <span class="grow"></span>
          ${d.sections && d.pages >= 3 ? `<span class="badge">${d.sections} sections</span>` : ""}
          ${d.schematic ? '<span class="badge doc">schematic</span>' : ""}
          ${why ? '<span class="badge warn">unavailable</span>' : ""}`;
        return why ? `<div class="row dead">${inner}</div>`
                   : `<a class="row" href="/doc/${d.id}">${inner}</a>`;
      }).join("")}</div>`).join("");
}

/** The ROM map, where MAME's romset gives one — linked from the machine so a
    reader does not have to know the /roms list exists to find it. */
async function loadRomMap(slug) {
  const r = await api("rommap/" + encodeURIComponent(slug)).catch(() => null);
  const box = document.getElementById("rommap");
  if (!box || !r || !r.devices) return;
  const n = Object.keys(r.devices).length;
  box.innerHTML = `<div class="note"><b>ROM map.</b> ${n} memory device${n === 1 ? "" : "s"}
    placed from MAME's romset — <a href="/rom/${esc(slug)}">see which device sits where</a>.</div>`;
}

/** Power supply reference — fuses and rails, checked first on a dead machine. */
async function loadPower(slug) {
  const p = await api("power/" + encodeURIComponent(slug)).catch(() => null);
  const box = document.getElementById("power");
  if (!box || !p) return;
  const rows = (o) => Object.entries(o || {}).map(([k, v]) =>
    `<tr><td class="refs">${esc(k)}</td><td>${esc(v)}</td></tr>`).join("");
  box.innerHTML = `<h2>Power supply — ${esc(p.title || "")}</h2>
    ${p.note ? `<div class="note">${esc(p.note)}</div>` : ""}
    <div class="panel" style="padding:0;overflow:auto">
      <table class="bom"><tbody>
        <tr><td colspan="2"><strong>Fuses</strong></td></tr>${rows(p.fuses)}
        <tr><td colspan="2"><strong>Rails</strong></td></tr>${rows(p.rails)}
        <tr><td colspan="2"><strong>Mains</strong></td></tr>${rows(p.mains)}
      </tbody></table></div>`;
}

/** Signature-analysis material: the sharpest fault-localising tool in these
 *  manuals — probe a pin, compare the four-character code. */
async function loadSignatures(slug) {
  const rec = await api("signatures/" + encodeURIComponent(slug)).catch(() => null);
  const box = document.getElementById("sigs");
  if (!box || !rec || !rec.documents?.length) return;
  const devices = Object.entries(rec.byDevice || {});
  box.innerHTML = `<h2>Signature analysis</h2>
    <div class="note">Probe a pin, read the four-character code, compare with the
      documented value — a mismatch localises the fault to that node.</div>
    ${rec.shared ? `<div class="note"><b>Shared hardware.</b> ${esc(rec.shared)}</div>` : ""}
    <div class="rows">${rec.documents.map((d) => `
      <a class="row" href="/doc/${d.doc}">
        <span class="nm">${esc(prettyTitle(d.title))}</span>
        <span class="grow"></span>
        <span class="badge">${d.pages} pages</span>
      </a>`).join("")}</div>
    ${devices.length ? `<div class="panel" style="margin-top:12px">
      <strong>Codes read from the drawings</strong>
      <div class="meta" style="margin:6px 0 10px">${esc(rec.note || "")}</div>
      <table class="bom"><tbody>${devices.map(([d, codes]) => `
        <tr><td class="refs">${esc(d)}</td><td>${codes.map(esc).join(" · ")}</td></tr>`).join("")}
      </tbody></table></div>` : ""}`;
}

/** Diagnostic sections for a machine — where someone with a dead board starts. */
async function loadDiagnostics(slug) {
  const rows = await api("diagnostics/" + encodeURIComponent(slug)).catch(() => []);
  const box = document.getElementById("diag");
  if (!box || !rows.length) return;
  const byKind = {};
  rows.forEach((r) => (byKind[r.kind] = byKind[r.kind] || []).push(r));
  box.innerHTML = `<h2>Diagnostics &amp; service (${rows.length})</h2>
    ${Object.entries(byKind).map(([kind, rs]) => `
      <div class="panel" style="margin-bottom:10px">
        <strong>${esc(kind)}</strong>
        <div class="rows" style="margin-top:8px">${rs.slice(0, 12).map((r) => `
          <a class="row" href="/doc/${r.doc}#p${r.page}">
            <span class="nm">${esc(r.section)}</span>
            <span class="grow"></span>
            <span class="meta">${esc(prettyTitle(r.title))}</span>
            <span class="badge">p${r.page}</span>
          </a>`).join("")}</div>
      </div>`).join("")}`;
}

/* ---------- manual reader ---------- */
async function reader(id) {
  const doc = await api("doc/" + id);
  const pages = doc.pages || [];
  const outline = pages.length >= 3 ? (doc.outline || []) : [];
  // Page numbers of the pages whose scan is published, in order, so the
  // first few load eagerly.
  const drawingPages = pages.filter((p) => p.dw && p.dh).map((p) => p.n);
  let cur = 1, query = "";

  app.innerHTML = `
    <h1>${esc(prettyTitle(doc.title))}</h1>
    <p class="sub">
      ${machineLinks(doc)}
      ${doc.type ? esc(doc.type) + " · " : ""}${pages.length} pages${outline.length ? ` · ${outline.length} sections` : ""} ·
      <a href="/pdf/${id}" target="_blank" rel="noopener">original scan ↗</a>${sourceCredit(doc)}</p>

    ${doc.note ? `<div class="note">${esc(doc.note)}</div>` : ""}

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

  /**
   * A page the corpus has decided is a drawing: show the scan.
   *
   * These pages used to render as paragraphs of whatever tesseract found on a
   * schematic sheet, which reads as fluent nonsense — the single worst thing
   * on the site. The scan is the content here; the recovered text is kept
   * underneath and collapsed, because it is what the search index matched on
   * and a reader who searched a part number needs to see where it hit.
   */
  function renderDrawing(p) {
    const src = `/pages/${id}/p${String(p.n).padStart(4, "0")}.webp`;
    const text = pageText(p).trim();
    // width/height are the scan's real pixel size and are load-bearing, not
    // decoration: with `height:auto` they give the box an aspect ratio, so it
    // reserves its full height before the image arrives. A lazy image with no
    // reserved height is zero-high, never enters the viewport, and therefore
    // never loads — the sheet would silently stay missing.
    // A page only carries dw/dh when its scan is published. Pages of documents
    // that are nothing but schematics do not: the whole document is the
    // drawing, so "see the original" already hands over the right thing and
    // there is no image to frame.
    const hasScan = !!(p.dw && p.dh);
    // Loading these lazily is the wrong default. A document that has any
    // scans averages 1.5 of them and 215 of the 285 have exactly one, so
    // laziness saves almost nothing — and what it defers is the only thing on
    // the page worth reading, on a page whose text is deliberately collapsed.
    // A sheet that has not appeared is indistinguishable from one that is
    // missing. So the first few load eagerly and only a long run of them, on
    // the two documents that have one, is deferred.
    const eager = drawingPages.indexOf(p.n) < 4;
    const img = hasScan
      ? `<img class="zoomable" title="Click to enlarge" loading="${eager ? "eager" : "lazy"}" decoding="async"
             width="${p.dw}" height="${p.dh}" src="${src}"
             alt="Scan of page ${p.n}"
             onerror="this.closest('figure').classList.add('noscan')">`
      : "";
    // A vector sheet is a different claim. Its labels are the document's own
    // text, read straight off the page rather than guessed at by tesseract, so
    // saying "nothing to rebuild" and "what OCR recovered" would both be wrong.
    const caption = p.vec
      ? `This page is a schematic sheet, shown as drawn. Its designators, values
         and net names are the document's own text and are searchable.
         <a href="/pdf/${id}" target="_blank" rel="noopener">See it in the full
         document ↗</a>`
      : hasScan
      ? `This page is a drawing. It is shown as the original scan — the text on
         it was drawn, not typeset, so there is nothing to rebuild.
         <a href="/pdf/${id}" target="_blank" rel="noopener">See it in the full
         document ↗</a>`
      : `This page is a drawing, so there is nothing to rebuild as text.
         <a href="/pdf/${id}" target="_blank" rel="noopener">See the original
         scan ↗</a>`;
    return `<figure class="sheet${hasScan ? "" : " noscan"}">
      ${img}
      <figcaption>${caption}</figcaption>
      ${text ? `<details class="ocrdump"><summary>${p.vec
        ? `Every label on this sheet (${text.split(/\s+/).length} words)`
        : `What OCR recovered from this sheet (${text.split(/\s+/).length} words —
           fragments, not prose)`}</summary>
        <p class="${p.vec ? "" : "lowconf"}">${mark(text)}</p></details>` : ""}
    </figure>`;
  }

  /**
   * A page of a schematic or drawing package that reads as prose — the theory
   * of operation at the front of an Atari SP package. The scan is shown, as
   * it is for every page of such a document, with the text set as prose under
   * it rather than collapsed: it is real text, and it is what search matched.
   */
  function renderScannedText(p, body) {
    const src = `/pages/${id}/p${String(p.n).padStart(4, "0")}.webp`;
    const eager = drawingPages.indexOf(p.n) < 4;
    return `<figure class="sheet">
      <img class="zoomable" title="Click to enlarge" loading="${eager ? "eager" : "lazy"}"
           decoding="async" width="${p.dw}" height="${p.dh}" src="${src}"
           alt="Scan of page ${p.n}"
           onerror="this.closest('figure').classList.add('noscan')">
      <figcaption>This page is shown as scanned; the text below was recovered
        from it and is searchable.</figcaption>
    </figure>${body}`;
  }

  /** Render a page's semantic blocks as real HTML. */
  function renderBlocks(p) {
    if (p.draw) return renderDrawing(p);
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
    const body = out.join("") ||
      '<p class="lowconf">This page carries no recoverable text — it is a drawing or a photograph. ' +
      `<a href="/pdf/${id}" target="_blank" rel="noopener">See the original scan ↗</a></p>`;
    // A text page whose scan is published: a prose page inside a drawing
    // document, shown as its page with the text beneath.
    if (!p.noise && p.dw && p.dh) return renderScannedText(p, body);
    // Reads as coming off a drawing, but nothing corroborates that, so the
    // text stays: this bucket also holds illustrated parts lists and
    // DIP-switch tables, which score the same and are the most useful pages
    // in a service manual. Warn, never hide.
    if (!p.noise) return body;
    // These read as coming off a drawing but the document never says so, so
    // they were left as prose behind a warning — the worry being that the same
    // bucket could hold an illustrated parts list, and hiding one of those is
    // worse than showing noise.
    //
    // Measured since: of the 2,007 pages in it, none yields a single trusted
    // parts-list row, and fourteen read at random are all schematics, wiring
    // diagrams or PCB layouts. The worry was sound but the bucket is not what
    // it guarded against. And the treatment never hid anything anyway — the
    // text is collapsed, not dropped — so a page in here that turned out to be
    // a parts list costs a reader one click, not the content.
    //
    // No scan is published for these: nothing in the document attests they are
    // drawings, so they are shown as text-behind-a-disclosure rather than as a
    // sheet, and the caption says which kind of evidence is behind it.
    const words = pageText(p).trim().split(/\s+/).length;
    return `<figure class="sheet noscan">
      <figcaption>This page reads as a drawing — its text was drawn rather than
        typeset, so it comes out fragmentary and out of order. The document does
        not label it, so the recovered text is kept below rather than replaced.
        <a href="/pdf/${id}" target="_blank" rel="noopener">See the original
        scan ↗</a></figcaption>
      <details class="ocrdump"><summary>What OCR recovered from this page
        (${words} words — fragments, not prose)</summary>
        <div class="fromdrawing">${body}</div></details>
    </figure>`;
  }

  function draw() {
    stage.innerHTML = `<div class="textview">${pages.map((p) => `
      <div class="pg-sep" id="p${p.n}">Page ${p.n}</div>
      ${renderBlocks(p)}`).join("")}</div>`;
  }

  function goto(n, smooth = true) {
    cur = Math.min(Math.max(1, n), pages.length);
    const el = document.getElementById("p" + cur);
    if (el) el.scrollIntoView({ behavior: smooth ? "smooth" : "instant", block: "start" });
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
  }, { passive: true, signal: viewAbort.signal });

  // A sheet opens over the page at full size; the arrows step through every
  // sheet in this document.
  stage.addEventListener("click", (e) => {
    const img = e.target.closest("figure.sheet img.zoomable");
    if (!img) return;
    const all = [...stage.querySelectorAll("figure.sheet img.zoomable")];
    openLightbox(all.map((i) => ({
      src: i.currentSrc || i.src, alt: i.alt,
      w: +i.getAttribute("width") || 0, h: +i.getAttribute("height") || 0,
    })), all.indexOf(img));
  });

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
      // Only the manuals that print a quantity column get one. Where the
      // header does not name one — the Sega lists are ITEM, PART NO.,
      // DESCRIPTION and nothing else — an empty column would invent a field
      // the page never had.
      const hasQty = rows.some((r) => r.qty);
      // A blank description is a real answer, not a missing one: the page's
      // columns came off the scan as separate runs, so the item and part
      // number are known and the description is not. Say so rather than
      // leaving a cell the reader reads as a bug.
      const noDesc = '<span class="q" title="This row\'s description could not be '
        + 'read off the page. Its item and part number were.">—</span>';
      box.innerHTML = `
        <div class="panel" style="padding:0;overflow:auto;margin-bottom:18px">
          <table class="bom"><thead><tr>
            <th>Item</th><th>Part number</th>${hasQty ? "<th>Qty</th>" : ""}
            <th>Description</th><th>Page</th>
          </tr></thead><tbody>
          ${rows.map((r) => `<tr>
            <td class="q">${esc(r.item)}</td>
            <td class="refs">${esc(r.part)}</td>
            ${hasQty ? `<td class="q">${esc(r.qty)}</td>` : ""}
            <td>${r.desc ? esc(r.desc) : noDesc}</td>
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

  // Deep link from the diagnostics index: /doc/<id>#p11 lands on that page.
  // Instantly — a smooth scroll through nine thousand pixels of manual is not
  // a landing, and a background tab abandons it part way.
  const anchor = location.hash.match(/^#p(\d+)$/);
  if (anchor) setTimeout(() => goto(+anchor[1], false), 60);
}

/* ---------- corpus-wide search ---------- */
async function search() {
  const q0 = param("q");
  app.innerHTML = `
    <h1>Search the manuals</h1>
    <p class="sub">Full text across every digitised document — procedures, part numbers,
       chip designations, DIP settings.</p>
    <div class="searchbar">
      <input id="q" placeholder="e.g. fuse replacement, self test, 74153…"
             value="${esc(q0)}" autocomplete="off" autofocus>
    </div>
    <div id="out" class="listbox"></div>`;

  const input = document.getElementById("q");
  const out = document.getElementById("out");
  let timer, page = Math.max(1, +param("page") || 1), last = null, seq = 0;

  const row = (r) => `
    <a class="row" href="/doc/${r.id}">
      <span class="nm">${esc(prettyTitle(r.title))}</span>
      <span class="meta">${esc(r.machineName || "")}</span>
      <span class="grow"></span>
      ${r.sections ? `<span class="badge">${r.sections} sections</span>` : ""}
      <span class="badge doc">${r.hits} hit${r.hits > 1 ? "s" : ""}</span>
    </a>`;

  function show(d) {
    const pages = Math.max(1, Math.ceil(d.results.length / PAGE_SIZE));
    page = Math.min(page, pages);
    const slice = d.results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
    out.innerHTML = `<p class="sub">${d.total} document${d.total > 1 ? "s" : ""} match${
        d.total > d.results.length ? `; the ${d.results.length} best are shown` : ""}</p>
      <div class="rows">${slice.map(row).join("")}</div>
      ${pagerHtml(page, d.results.length)}`;
  }

  async function run() {
    const q = input.value.trim();
    if (q !== last) { page = 1; last = q; }
    setParams({ q, page: page > 1 ? page : "" });
    if (q.length < 3) { out.innerHTML = '<div class="empty">Type at least three characters.</div>'; return; }
    const my = ++seq;
    out.innerHTML = '<div class="spin">Searching…</div>';
    const d = await api("search?q=" + encodeURIComponent(q) + "&limit=200");
    if (my !== seq) return;
    if (!d.results.length) {
      out.innerHTML = `<div class="empty">Nothing found for “${esc(q)}”.</div>`;
      return;
    }
    last = q; run.data = d;
    show(d);
  }

  wireNav(out, (ch) => {
    page = ch.page;
    setParams({ page: page > 1 ? page : "" });
    if (run.data) { show(run.data); scrollToList(out); }
  });

  input.oninput = () => { clearTimeout(timer); timer = setTimeout(run, 220); };
  if (q0) { last = q0; run(); } else out.innerHTML = '<div class="empty">Type to search.</div>';
}

/* ---------- boards index ---------- */
async function boards() {
  const list = await api("boards");
  app.innerHTML = `
    <h1>KiCad conversions</h1>
    <p class="sub">Boards rebuilt from the original drawings as real KiCad projects,
       with browsable schematics and bills of materials.</p>
    <div id="list" class="listbox"></div>`;
  if (!list.length) {
    document.getElementById("list").innerHTML = '<div class="empty">No conversions published yet.</div>';
    return;
  }
  pagedList(document.getElementById("list"), list, {
    name: (b) => b.name,
    row: (b) => `
      <a class="row" href="/board/${esc(b.slug)}">
        <span class="nm">${esc(b.name)}</span>
        <span class="meta">${esc(b.mfr || "")}${b.year ? " · " + esc(b.year) : ""}</span>
        <span class="grow"></span>
        <span class="badge">${b.devices} devices</span>
        ${b.singleSource ? `<span class="badge warn" title="every device from a single printing of one manual, with no cross-check">single source</span>` : ""}
        <span class="badge ${b.netsTraced ? "kicad" : ""}">${b.netsTraced ? "nets traced" : "components only"}</span>
      </a>`,
  });
}

/* ---------- ROM maps recovered from MAME ----------
   A weaker asset than a board map and kept separate from them on purpose:
   memory devices only, from one source, with nothing cross-checked. */
async function rommaps() {
  const list = await api("rommaps");
  const withDoc = list.filter((r) => r.docs).length;
  app.innerHTML = `
    <h1>ROM maps</h1>
    <p class="sub">Which memory device sits at which position, for ${list.length}
       machines — recovered from the board positions MAME records in its romset
       filenames.</p>
    <div class="note warn"><b>Memory devices only.</b> A ROM map names the ROMs,
       PROMs and PLDs on a board and nothing else, so most of the board is missing
       from it. It comes from one source and has not been cross-checked against a
       drawing. The <a href="/boards">board maps</a> are the other thing: read off
       component-location drawings, every device carrying its own provenance.</div>
    <p class="sub">${withDoc} of these are machines whose manual is also on
       this site.</p>
    <div class="searchbar">
      <input id="rq" placeholder="Filter by name or manufacturer…"
             value="${esc(param("q"))}" autocomplete="off">
    </div>
    <div id="list" class="listbox"></div>`;

  const view = pagedList(document.getElementById("list"), list, {
    name: (r) => r.name,
    filter: (r, q) => `${r.name} ${r.mfr || ""} ${r.machine}`.toLowerCase().includes(q),
    empty: "No ROM map matches that.",
    row: (r) => `
      <a class="row" href="/rom/${esc(r.machine)}">
        <span class="nm">${esc(r.name)}</span>
        <span class="meta">${esc(r.mfr || "")}${r.year ? " · " + esc(r.year) : ""}</span>
        <span class="grow"></span>
        ${r.docs ? `<span class="badge doc">${r.docs} manual${r.docs > 1 ? "s" : ""}</span>` : ""}
        ${r.hasBoard ? `<span class="badge kicad">board map</span>` : ""}
        <span class="badge">${r.devices} devices</span>
      </a>`,
  });
  const rq = document.getElementById("rq");
  let timer;
  rq.oninput = () => { clearTimeout(timer); timer = setTimeout(() => view.setQuery(rq.value.trim()), 140); };
}

async function rommap(machine) {
  const r = await api("rommap/" + machine);
  const rows = Object.entries(r.devices);
  // The "board map" badge on the list promised something; this is where it
  // is. Boards name the machine they belong to, so match on that.
  const kbs = (await api("boards").catch(() => []))
    .filter((b) => b.machine === machine || b.slug === machine);
  const kinds = [...new Set(rows.map(([, d]) => d.kind))];
  app.innerHTML = `
    <h1>${esc(r.name)} — ROM map</h1>
    <p class="sub">${esc(r.mfr || "")}${r.year ? " · " + esc(r.year) : ""} ·
       ${rows.length} memory devices · positions written
       ${r.style === "letter-number" ? "letter-first (N1)" : "number-first (6E)"}</p>
    <div class="note warn"><b>Memory devices only, and not cross-checked.</b>
       These positions come from the filenames MAME records for this machine's
       romset, which are taken from real dumped boards. Everything on the board
       that is not a ROM, PROM or PLD is absent, and nothing here has been checked
       against a component-location drawing.</div>
    ${kbs.length ? `<p class="sub">Board map${kbs.length > 1 ? "s" : ""} for this machine —
       every device, read from the drawings:
       ${kbs.map((b) => `<a href="/board/${esc(b.slug)}">${esc(b.name)}</a>`).join(" · ")}.</p>` : ""}
    <p class="sub"><a href="/machine/${esc(machine)}">${esc(r.name)}</a>${r.docs
       ? ` — ${r.docs} manual${r.docs > 1 ? "s" : ""} for this machine are on the site.`
       : " — hardware and DIP switch settings."}</p>
    <h2>Devices</h2>
    <div class="rows">${rows.map(([cell, d]) => `
      <div class="row">
        <span class="nm mono">${esc(cell)}</span>
        <span class="badge doc">${esc(d.kind || "?")}</span>
        <span class="meta mono">${esc(d.file)}</span>
        <span class="grow"></span>
        ${d.size ? `<span class="badge">${d.size >= 1024 ? (d.size / 1024) + "K" : d.size + "B"}</span>` : ""}
        ${d.pins ? `<span class="badge">DIP-${d.pins}</span>` : ""}
        ${d.part ? `<span class="badge">${esc(d.part)}</span>` : ""}
      </div>`).join("")}</div>
    <p class="sub">Device classes present: ${kinds.map(esc).join(", ")}.
       Source: MAME <code>${esc(r.source)}</code>.</p>`;
}

/* ---------- board: schematic + BOM ---------- */

/* Say which sheet this is, and say plainly what the reader is looking at. A
   traced sheet stays sharp at any zoom; a scan does not, and pretending
   otherwise wastes the reader's time when they zoom in and find mush. */
function sheetNote(b) {
  const src = b.sheetSource || {};
  const doc = (b.schematicDocs || []).find((d) => d.id === src.doc);
  const where = doc ? `${doc.title}, page ${src.page}` : "the schematic package";
  return b.sheetKind === "svg"
    ? `Traced from ${where} — vector, so it stays sharp at any zoom.`
    : `Page scan from ${where}. This drawing is a photograph of stained paper, `
      + `which traces to speckle rather than line work, so the scan is shown instead.`;
}
async function board(slug) {
  const list = await api("boards");
  const b = list.find((x) => x.slug === slug);
  if (!b) { app.innerHTML = '<div class="empty">Unknown board.</div>'; return; }

  app.innerHTML = `
    <h1>${esc(b.name)} — board</h1>
    <p class="sub">${esc(b.mfr || "")}${b.year ? " · " + esc(b.year) : ""}
      ${b.drawing ? ` · drawing <code>${esc(b.drawing)}</code>` : ""}</p>
    ${b.singleSource ? `<div class="note warn"><b>Read once, and not cross-checked.</b>
       Every device on this board comes from a single printing of one manual. Everywhere
       else on this site a device is only placed when two independent sources agree, and
       that test does real work — it is what catches an OCR of a part number that looks
       perfectly plausible on its own. Nothing here has had that test. Treat it as a
       lead, and check the chip against the board before you act on it.</div>` : ""}
    ${b.status ? `<div class="note"><b>Conversion status.</b> ${esc(b.status)}</div>` : ""}
    ${b.ibom ? `<h2>Board</h2>
    <p class="sub">Every device at its position on the board, cross-linked to the bill of
       materials — click a row to find the part, or a part to find the row.</p>
    <div class="zoombar"><a href="${esc(b.ibom)}" target="_blank" rel="noopener">Open full board view ↗</a></div>
    <iframe class="ibom" src="${esc(b.ibom)}" title="Interactive board view" loading="lazy"></iframe>` : ""}

    <div id="related"></div>

    <h2>Find a chip</h2>
    <div class="searchbar">
      <input id="chipq" placeholder="Board position or part — e.g. C4, 74LS157, state machine…" autocomplete="off">
    </div>
    <div id="chipout"></div>

    ${b.sheet ? `<h2>Schematic</h2>
    <p class="sub">${esc(sheetNote(b))}</p>
    <div class="zoombar">
      <button id="zi">+</button><button id="zo">−</button><button id="zr">reset</button>
      <span class="grow"></span>
      <a href="${esc(b.sheet)}" target="_blank" rel="noopener">Open sheet ↗</a>
    </div>
    <div class="svgwrap" id="wrap"><img id="svg" src="${esc(b.sheet)}" alt="Schematic sheet"></div>` : ""}
    ${(b.schematicDocs || []).length ? `<h2>Schematic documents</h2>
    <p class="sub">Every schematic and drawing package this machine has, page by page.</p>
    <div class="rows">${b.schematicDocs.map((d) => `
      <a class="row" href="/doc/${esc(d.id)}">
        <span class="nm">${esc(d.title)}</span>
        <span class="grow"></span>
        <span class="meta">${esc(d.pages)} page${d.pages === 1 ? "" : "s"}</span>
      </a>`).join("")}</div>` : ""}
    <h2>Bill of materials</h2>
    <div class="searchbar"><input id="bq" placeholder="Filter by value or reference…" autocomplete="off"></div>
    <div class="panel" style="padding:0;overflow:auto">
      <table class="bom"><thead><tr>
        <th data-k="value">Value</th><th data-k="qty">Qty</th>
        <th data-k="refs">References (board grid position)</th>
      </tr></thead><tbody id="bom"></tbody></table>
    </div>`;

  /* Related boards — a known-good sibling is often the fastest confirmation. */
  api("related/" + slug).then((rows) => {
    const box = document.getElementById("related");
    if (!box || !rows.length) return;
    box.innerHTML = `<h2>Related hardware</h2>
      <div class="rows">${rows.map((r) => `
        ${r.board ? `<a class="row" href="/board/${esc(r.board)}">` : '<div class="row">'}
          <span class="nm">${esc(r.name)}</span>
          <span class="badge doc">${esc(r.kind)}</span>
          <span class="grow"></span>
          <span class="meta">${esc(r.detail)}</span>
        ${r.board ? "</a>" : "</div>"}`).join("")}</div>`;
  }).catch(() => {});

  /* chip lookup — "what is at C4, and what does it do?" */
  const chipq = document.getElementById("chipq");
  if (chipq) {
    let idx = null, sig = null;
    const out = document.getElementById("chipout");
    chipq.oninput = async () => {
      const q = chipq.value.trim().toLowerCase();
      if (!q) { out.innerHTML = ""; return; }
      if (!idx) idx = await api("chips/" + slug).catch(() => ({}));
      if (!sig) sig = await api("signals/" + slug).catch(() => ({}));
      const hits = Object.entries(idx).filter(([d, v]) =>
        d.toLowerCase() === q || d.toLowerCase().startsWith(q) ||
        (v.part || "").toLowerCase().includes(q) ||
        (v.section || "").toLowerCase().includes(q)).slice(0, 40);
      const sigHits = Object.entries(sig).filter(([n]) =>
        n.toLowerCase().includes(q)).slice(0, 12);
      const sigHtml = sigHits.length ? `<h2>Signals</h2><div class="rows">${sigHits.map(([n, where]) => `
          <div class="row">
            <span class="nm mono">${esc(n)}</span>
            <span class="meta">appears on ${Object.keys(where).map(esc).join(", ")}</span>
            <span class="grow"></span>
            <span class="badge">${Object.values(where).reduce((a, b) => a + b, 0)} refs</span>
          </div>`).join("")}</div>` : "";
      out.innerHTML = (hits.length ? `<div class="rows">${hits.map(([d, v]) => `
          <div class="row">
            <span class="nm mono">${esc(d)}</span>
            <span class="badge doc">${esc(v.part)}</span>
            <span class="meta">${esc(v.section || "")}</span>
            <span class="grow"></span>
            ${v.otherRev ? `<span class="badge" title="same chip on the other revision">${esc(v.otherRev)} on other rev</span>` : ""}
            ${v.source ? `<span class="badge src" title="where this reading comes from">${esc(v.source)}</span>` : ""}
          </div>`).join("")}</div>` : "") + sigHtml
        || `<div class="empty">Nothing matches “${esc(chipq.value)}” on this board.</div>`;
    };
  }

  /* pan + zoom — only when the board has a sheet to pan over. Thirteen boards
     have no schematic in the corpus at all, and wiring this up unconditionally
     threw on the missing buttons and took the bill of materials down with it. */
  const wrap = document.getElementById("wrap"), img = document.getElementById("svg");
  if (wrap && img) {
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
  }

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

/* ---------- submit documentation ---------- */

const mb = (b) => `${Math.round(b / 1048576)} MB`;

/**
 * The contribution form. Everything it collects is filed as one commit in the
 * submissions repo; nothing reaches the corpus without being triaged first,
 * and the page says so rather than implying an upload appears on the site.
 */
async function submit() {
  const cfg = await api("submit");

  if (!cfg.enabled) {
    app.innerHTML = `
      <h1>Submit documentation</h1>
      <p class="sub">Uploads are not configured on this deployment.</p>
      <div class="panel"><p>Open an issue on
        <a href="https://github.com/stoatworks-labs/cathode-ray-tomes/issues">the project repository</a>
        instead and describe what you have.</p></div>`;
    return;
  }

  app.innerHTML = `
    <h1>Submit documentation</h1>
    <p class="sub">Send a manual, a schematic sheet or a wiring diagram we do not have.</p>

    <div class="panel" style="margin-bottom:18px">
      <p>The corpus comes from one archive, and what is missing from it is mostly
      what never got scanned — the folder in the back of a cabinet, the photocopy
      that came with a board twenty years ago. If you have one, this is where it goes.</p>
      <p style="margin-bottom:0"><b>What happens to it.</b> Your submission is committed to a
      private queue repository along with everything you write below. It does not appear
      on the site: a person reads it, checks it is what it says it is, and only then does it
      go through the same OCR and indexing pipeline as everything else. That is a manual
      step and it is not fast.</p>
    </div>

    <form id="sf" class="form" novalidate>
      <label>
        <span>Machine <b class="req">*</b></span>
        <input name="machine" required maxlength="120" placeholder="Asteroids Deluxe" autocomplete="off">
        <em>The game the document covers. A model or board number is even better.</em>
      </label>

      <div class="row2">
        <label>
          <span>Manufacturer</span>
          <input name="manufacturer" maxlength="80" placeholder="Atari" autocomplete="off">
        </label>
        <label>
          <span>Year</span>
          <input name="year" maxlength="12" placeholder="1981" autocomplete="off">
        </label>
      </div>

      <label>
        <span>What kind of document</span>
        <select name="docType">
          ${cfg.docTypes.map((t) => `<option value="${esc(t)}">${esc(t)}</option>`).join("")}
        </select>
      </label>

      <label>
        <span>Files</span>
        <input type="file" name="files" id="files" multiple accept="${cfg.accept.map((e) => "." + e).join(",")}">
        <em>Up to ${cfg.maxFiles} files, ${mb(cfg.maxFileBytes)} each and ${mb(cfg.maxTotalBytes)}
            in total: ${esc(cfg.accept.join(", "))}. A scan at 300 dpi reads far better than a
            phone photograph, but a phone photograph beats nothing.</em>
      </label>
      <div id="picked" class="picked"></div>

      <label>
        <span>…or a link to it</span>
        <input name="sourceUrl" type="url" maxlength="500" placeholder="https://…" autocomplete="off">
        <em>For anything over ${mb(cfg.maxFileBytes)}, or already hosted somewhere.</em>
      </label>

      <label>
        <span>Where it came from <b class="req">*</b></span>
        <textarea name="provenance" rows="3" required maxlength="2000"
          placeholder="Came with a board I bought in 2004; the operator said it was the original manual."></textarea>
        <em>Provenance is the difference between a document and a rumour. Say what you know,
            including that you are not sure.</em>
      </label>

      <label>
        <span>Anything else worth knowing</span>
        <textarea name="notes" rows="3" maxlength="4000"
          placeholder="Pages 12 and 13 are missing. Someone has pencilled revision notes on the schematic sheet."></textarea>
        <em>Missing pages, annotations, a revision that does not match the machine — all of it helps.</em>
      </label>

      <label>
        <span>Contact or credit</span>
        <input name="contact" maxlength="120" placeholder="Name, email or GitHub handle" autocomplete="off">
        <em>Optional. Stored in the private queue repository so we can come back to you
            about the document, and used to credit you if you would like that.</em>
      </label>

      <label class="check">
        <input type="checkbox" name="rights" id="rights">
        <span>This is a service or repair document, it is mine to share, and I understand
              its copyright stays with its publisher. <b class="req">*</b></span>
      </label>

      <!-- Bots fill this in; people never see it. -->
      <div class="hp" aria-hidden="true">
        <label>Website<input name="website" tabindex="-1" autocomplete="off"></label>
      </div>

      <div id="ts"></div>

      <div class="actions">
        <button type="submit" id="go">Send it</button>
        <span id="prog" class="prog"></span>
      </div>
      <div id="msg"></div>
    </form>`;

  const form = document.getElementById("sf");
  const picked = document.getElementById("picked");
  const msg = document.getElementById("msg");
  const prog = document.getElementById("prog");
  const go = document.getElementById("go");

  // Size is worth checking here rather than after a reader has spent five
  // minutes pushing 40 MB up a venue's wifi.
  document.getElementById("files").onchange = (e) => {
    const list = [...e.target.files];
    let total = 0;
    picked.innerHTML = list
      .map((f) => {
        total += f.size;
        const over = f.size > cfg.maxFileBytes;
        return `<div class="${over ? "over" : ""}">${esc(f.name)}
          <span>${(f.size / 1048576).toFixed(1)} MB${over ? " — too large" : ""}</span></div>`;
      })
      .join("");
    if (list.length > cfg.maxFiles) {
      picked.innerHTML += `<div class="over">${list.length} files — at most ${cfg.maxFiles}</div>`;
    }
    if (total > cfg.maxTotalBytes) {
      picked.innerHTML += `<div class="over">${(total / 1048576).toFixed(1)} MB total — the limit is ${mb(cfg.maxTotalBytes)}</div>`;
    }
  };

  if (cfg.turnstileSiteKey) {
    const s = document.createElement("script");
    s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js";
    s.async = true;
    document.head.appendChild(s);
    document.getElementById("ts").className = "cf-turnstile";
    document.getElementById("ts").dataset.sitekey = cfg.turnstileSiteKey;
  }

  form.onsubmit = (e) => {
    e.preventDefault();
    msg.innerHTML = "";

    const data = new FormData(form);
    if (!String(data.get("machine") || "").trim()) return fail("Which machine is it for?");
    if (!String(data.get("provenance") || "").trim()) return fail("Say where the document came from.");
    if (!document.getElementById("rights").checked) return fail("Please confirm the rights statement.");
    const files = [...document.getElementById("files").files];
    if (!files.length && !String(data.get("sourceUrl") || "").trim()) {
      return fail("Attach a file, or give a link to one.");
    }

    // fetch() cannot report upload progress, and these are slow uploads over
    // whatever wifi is in the building.
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/submit");
    xhr.upload.onprogress = (ev) => {
      if (!ev.lengthComputable) return;
      prog.textContent = `${Math.round((ev.loaded / ev.total) * 100)}%`;
    };
    xhr.onload = () => {
      go.disabled = false;
      prog.textContent = "";
      let body = {};
      try { body = JSON.parse(xhr.responseText); } catch { /* keep the status */ }
      if (xhr.status === 200 && body.ok) return done(body);
      fail(body.error || `The server said ${xhr.status}.`);
    };
    xhr.onerror = () => {
      go.disabled = false;
      prog.textContent = "";
      fail("The upload did not complete. Nothing was sent — try again.");
    };

    go.disabled = true;
    prog.textContent = "0%";
    xhr.send(data);
  };

  function fail(text) {
    go.disabled = false;
    msg.innerHTML = `<div class="note warn"><b>Not sent.</b> ${esc(text)}</div>`;
  }

  function done(body) {
    app.innerHTML = `
      <h1>Filed — thank you</h1>
      <div class="panel">
        <p>${body.files ? `${body.files} file${body.files > 1 ? "s" : ""} and your notes are` : "Your submission is"}
        committed to the queue as <code>${esc(body.commit)}</code>.</p>
        <p>It will be read by a person before anything happens to it, and it does not
        appear on the site until it has been through the pipeline. If you left a contact
        we will come back to you if the document raises a question.</p>
        <p style="margin-bottom:0"><a href="/submit">Submit another</a> ·
        <a href="/">Back to the machines</a></p>
      </div>`;
  }
}

route();

// Offline shell and home-screen install. The manuals themselves are not
// cached -- see web/sw.js for why. A failure here costs the install prompt and
// nothing else, and there is nothing a reader could do about it, so it is
// logged and dropped.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch((error) => {
      console.warn('offline support unavailable:', error);
    });
  });
}
