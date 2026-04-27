const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function toast(msg, kind = "ok") {
  const t = $("#toast");
  t.textContent = msg;
  t.className = `toast ${kind}`;
  t.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { t.hidden = true; }, 3000);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const ct = res.headers.get("content-type") || "";
  const body = ct.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const msg = (body && body.error) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body;
}

// ---------- timings ----------
function timingsRow(r = { subject: "", type: "", string: "", url: "" }) {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td><input type="text" data-k="subject"></td>
    <td><input type="text" data-k="type"></td>
    <td><input type="text" data-k="string"></td>
    <td><input type="text" data-k="url"></td>
    <td class="actions-col"><button class="del" type="button" title="Remove row">×</button></td>
  `;
  for (const inp of tr.querySelectorAll("input")) {
    inp.value = r[inp.dataset.k] || "";
  }
  tr.querySelector("button.del").addEventListener("click", () => {
    tr.remove();
    refreshPriorityOptions();
  });
  for (const inp of tr.querySelectorAll("input")) {
    if (inp.dataset.k === "subject" || inp.dataset.k === "type") {
      inp.addEventListener("input", refreshPriorityOptions);
    }
  }
  return tr;
}

function readTimingsFromDOM() {
  return $$("#timingsTable tbody tr").map(tr => {
    const out = {};
    for (const inp of tr.querySelectorAll("input")) {
      out[inp.dataset.k] = inp.value.trim();
    }
    return out;
  }).filter(r => r.subject || r.type || r.string || r.url);
}

async function loadTimings() {
  const rows = await api("/api/timings");
  const tbody = $("#timingsTable tbody");
  tbody.innerHTML = "";
  for (const r of rows) tbody.appendChild(timingsRow(r));
  refreshPriorityOptions();
}

async function saveTimings() {
  const rows = readTimingsFromDOM();
  await api("/api/timings", { method: "POST", body: JSON.stringify(rows) });
  toast(`Saved ${rows.length} row(s)`);
}

// ---------- priority ----------
function priorityItem(entry, subjects, types) {
  const li = document.createElement("li");
  li.draggable = true;
  li.innerHTML = `
    <span class="handle" title="drag to reorder">⇅</span>
    <select data-k="subject"></select>
    <select data-k="type"></select>
    <button class="del" type="button" title="Remove">×</button>
  `;
  const subjSel = li.querySelector('select[data-k="subject"]');
  const typeSel = li.querySelector('select[data-k="type"]');
  for (const s of subjects) {
    const o = document.createElement("option");
    o.value = s; o.textContent = s;
    subjSel.appendChild(o);
  }
  for (const t of types) {
    const o = document.createElement("option");
    o.value = t; o.textContent = t;
    typeSel.appendChild(o);
  }
  // include current value even if not in observed sets
  if (entry.subject && !subjects.includes(entry.subject)) {
    const o = document.createElement("option");
    o.value = entry.subject; o.textContent = entry.subject + " (custom)";
    subjSel.appendChild(o);
  }
  if (entry.type && !types.includes(entry.type)) {
    const o = document.createElement("option");
    o.value = entry.type; o.textContent = entry.type + " (custom)";
    typeSel.appendChild(o);
  }
  subjSel.value = entry.subject || subjects[0] || "";
  typeSel.value = entry.type || types[0] || "";

  li.querySelector("button.del").addEventListener("click", () => li.remove());

  li.addEventListener("dragstart", () => li.classList.add("dragging"));
  li.addEventListener("dragend", () => li.classList.remove("dragging"));
  return li;
}

function refreshPriorityOptions() {
  // re-populate selects with currently observed subjects/types from the timings table
  const rows = readTimingsFromDOM();
  const subjects = Array.from(new Set(rows.map(r => r.subject).filter(Boolean))).sort();
  const types = Array.from(new Set(rows.map(r => r.type).filter(Boolean))).sort();

  for (const li of $$("#priorityList li")) {
    for (const sel of li.querySelectorAll("select")) {
      const k = sel.dataset.k;
      const current = sel.value;
      const set = k === "subject" ? subjects : types;
      sel.innerHTML = "";
      for (const v of set) {
        const o = document.createElement("option");
        o.value = v; o.textContent = v;
        sel.appendChild(o);
      }
      if (current && !set.includes(current)) {
        const o = document.createElement("option");
        o.value = current; o.textContent = current + " (custom)";
        sel.appendChild(o);
      }
      sel.value = current;
    }
  }
}

function setupDragReorder(listEl) {
  listEl.addEventListener("dragover", (e) => {
    e.preventDefault();
    const dragging = listEl.querySelector("li.dragging");
    if (!dragging) return;
    const after = [...listEl.querySelectorAll("li:not(.dragging)")].find(li => {
      const r = li.getBoundingClientRect();
      return e.clientY < r.top + r.height / 2;
    });
    if (after == null) listEl.appendChild(dragging);
    else listEl.insertBefore(dragging, after);
  });
}

async function loadPriority() {
  const data = await api("/api/priority");
  const list = $("#priorityList");
  list.innerHTML = "";
  const rows = readTimingsFromDOM();
  const subjects = Array.from(new Set(rows.map(r => r.subject).filter(Boolean))).sort();
  const types = Array.from(new Set(rows.map(r => r.type).filter(Boolean))).sort();
  for (const e of data) list.appendChild(priorityItem(e, subjects, types));
}

async function savePriority() {
  const items = $$("#priorityList li").map(li => ({
    subject: li.querySelector('select[data-k="subject"]').value,
    type: li.querySelector('select[data-k="type"]').value,
  })).filter(e => e.subject && e.type);
  await api("/api/priority", { method: "POST", body: JSON.stringify(items) });
  toast(`Saved ${items.length} priority item(s)`);
}

// ---------- config ----------
async function loadConfig() {
  const cfg = await api("/api/config");
  $("#headless").checked = !!cfg.headless;
  $("#slowMo").value = cfg.slow_mo ?? 400;
}

async function saveConfig() {
  const body = JSON.stringify({
    headless: $("#headless").checked,
    slow_mo: parseInt($("#slowMo").value || "400", 10),
  });
  await api("/api/config", { method: "POST", body });
  toast("Config saved");
}

// ---------- cookies ----------
async function loadCookieStatus() {
  const s = await api("/api/cookies/status");
  const fmt = (ts) => ts ? new Date(ts * 1000).toLocaleString() : "missing";
  $("#cookieStatus").textContent =
    `cookies.txt: ${fmt(s.cookies_txt)}    chrome_cookies.json: ${fmt(s.chrome_cookies_json)}`;
}

async function uploadCookies() {
  const f = $("#cookieFile").files[0];
  if (!f) { toast("Pick a cookies.txt file first", "error"); return; }
  const fd = new FormData();
  fd.append("file", f);
  const res = await fetch("/api/cookies", { method: "POST", body: fd });
  const body = await res.json();
  if (!res.ok) { toast(body.error || "upload failed", "error"); return; }
  toast(`Converted ${body.count} cookies`);
  loadCookieStatus();
}

// ---------- bot ----------
let logSource = null;

function appendLog(line) {
  const el = $("#logs");
  const stuck = el.scrollTop + el.clientHeight >= el.scrollHeight - 4;
  el.textContent += line + "\n";
  if (stuck) el.scrollTop = el.scrollHeight;
}

function startLogStream() {
  if (logSource) logSource.close();
  logSource = new EventSource("/api/bot/logs");
  logSource.onmessage = (ev) => {
    try {
      const e = JSON.parse(ev.data);
      appendLog(e.line);
    } catch {}
  };
  logSource.onerror = () => {
    // EventSource will retry; nothing to do
  };
}

async function refreshStatus() {
  try {
    const s = await api("/api/bot/status");
    const dot = $("#dot");
    const txt = $("#statusText");
    if (s.running) {
      dot.className = "dot running";
      txt.textContent = `running (pid ${s.pid})`;
      $("#startBtn").disabled = true;
      $("#stopBtn").disabled = false;
    } else {
      dot.className = "dot";
      txt.textContent = s.exit_code == null ? "idle" : `idle (last exit ${s.exit_code})`;
      $("#startBtn").disabled = false;
      $("#stopBtn").disabled = true;
    }
  } catch {}
}

async function startBot() {
  try {
    await api("/api/bot/start", { method: "POST" });
    toast("Bot started");
  } catch (e) { toast(e.message, "error"); }
  refreshStatus();
}

async function stopBot() {
  try {
    await api("/api/bot/stop", { method: "POST" });
    toast("Bot stopped");
  } catch (e) { toast(e.message, "error"); }
  refreshStatus();
}

// ---------- wire-up ----------
window.addEventListener("DOMContentLoaded", async () => {
  setupDragReorder($("#priorityList"));

  $("#addRow").addEventListener("click", () => {
    $("#timingsTable tbody").appendChild(timingsRow());
  });
  $("#saveTimings").addEventListener("click", () => saveTimings().catch(e => toast(e.message, "error")));

  $("#addPriority").addEventListener("click", () => {
    const rows = readTimingsFromDOM();
    const subjects = Array.from(new Set(rows.map(r => r.subject).filter(Boolean))).sort();
    const types = Array.from(new Set(rows.map(r => r.type).filter(Boolean))).sort();
    $("#priorityList").appendChild(priorityItem({}, subjects, types));
  });
  $("#savePriority").addEventListener("click", () => savePriority().catch(e => toast(e.message, "error")));

  $("#saveConfig").addEventListener("click", () => saveConfig().catch(e => toast(e.message, "error")));

  $("#uploadCookies").addEventListener("click", uploadCookies);

  $("#startBtn").addEventListener("click", startBot);
  $("#stopBtn").addEventListener("click", stopBot);
  $("#clearLogs").addEventListener("click", () => { $("#logs").textContent = ""; });

  try { await loadTimings(); } catch (e) { toast("Failed to load timings: " + e.message, "error"); }
  try { await loadPriority(); } catch (e) { toast("Failed to load priority: " + e.message, "error"); }
  try { await loadConfig(); } catch (e) {}
  try { await loadCookieStatus(); } catch (e) {}

  startLogStream();
  refreshStatus();
  setInterval(refreshStatus, 2500);
});
