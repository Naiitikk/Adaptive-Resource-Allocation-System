const $ = (id) => document.getElementById(id);
let latest = null;

async function getState() {
  const response = await fetch("/api/state");
  if (!response.ok) throw new Error("Unable to load simulation state");
  latest = await response.json();
  render(latest);
}

function render(state) {
  $("connection").textContent = "Live";
  $("connection").style.color = "#87e0bc";
  $("toggle").textContent = state.running ? "Pause" : "Resume";
  $("action").textContent = state.last_action;
  $("tick").textContent = state.tick;
  $("process-count").textContent = state.processes.length;
  const cpu = state.system.cpu_percent;
  const memory = state.system.memory_percent;
  $("cpu-value").textContent = `${cpu.toFixed(1)}%`;
  $("memory-value").textContent = `${memory.toFixed(1)}%`;
  $("cpu-meter").style.width = `${Math.min(100, cpu)}%`;
  $("memory-meter").style.width = `${Math.min(100, memory)}%`;
  $("process-table").innerHTML = state.processes.map((p) => `
    <tr><td><strong>${escapeHtml(p.name)}</strong></td>
      <td><span class="status ${p.status.toLowerCase()}">${p.status}</span></td>
      <td>${p.priority}/10</td><td>${p.cpu_demand.toFixed(1)}%</td><td>${p.cpu_allocation.toFixed(1)}%</td>
      <td>${p.memory_demand.toFixed(0)} MB</td><td>${p.memory_allocation.toFixed(0)} MB</td>
      <td><button class="remove" data-id="${p.id}" title="Remove program">Remove</button></td></tr>`).join("");
  drawChart(state.history);
}

function drawChart(history) {
  const canvas = $("chart"), ctx = canvas.getContext("2d"), width = canvas.clientWidth, height = 180, dpr = window.devicePixelRatio || 1;
  canvas.width = width * dpr; canvas.height = height * dpr; ctx.scale(dpr, dpr); ctx.clearRect(0, 0, width, height);
  const draw = (values, color) => {
    if (!values.length) return;
    ctx.beginPath(); values.forEach((value, i) => { const x = i / Math.max(1, values.length - 1) * width; const y = height - (value / 100) * (height - 12) - 6; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
  };
  ctx.strokeStyle = "#223653"; ctx.lineWidth = 1; for (let y = 0; y <= 3; y++) { ctx.beginPath(); ctx.moveTo(0, y * 55 + .5); ctx.lineTo(width, y * 55 + .5); ctx.stroke(); }
  draw(history.cpu, "#69d1a7"); draw(history.memory.map((v) => v / 8192 * 100), "#75a9ff");
}

function escapeHtml(text) { return text.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]); }

$("toggle").addEventListener("click", async () => { await fetch("/api/simulation/toggle", { method: "POST" }); getState(); });
$("reset").addEventListener("click", async () => { await fetch("/api/simulation/reset", { method: "POST" }); getState(); });
$("add-form").addEventListener("submit", async (event) => {
  event.preventDefault(); $("form-error").textContent = "";
  const payload = Object.fromEntries(new FormData(event.target));
  const response = await fetch("/api/processes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  if (!response.ok) { $("form-error").textContent = (await response.json()).error; return; }
  event.target.reset(); $("priority-output").textContent = "5"; getState();
});
$("add-form").priority.addEventListener("input", (event) => $("priority-output").textContent = event.target.value);
document.addEventListener("click", async (event) => { if (!event.target.matches(".remove")) return; await fetch(`/api/processes/${event.target.dataset.id}`, { method: "DELETE" }); getState(); });
getState().catch(() => { $("connection").textContent = "Offline"; });
setInterval(() => getState().catch(() => {}), 1000);
