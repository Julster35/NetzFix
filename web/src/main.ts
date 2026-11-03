import "maplibre-gl/dist/maplibre-gl.css";
import "./style.css";
import maplibregl from "maplibre-gl";
import { MapboxOverlay } from "@deck.gl/mapbox";
import { PathLayer, ScatterplotLayer } from "@deck.gl/layers";
import { TripsLayer } from "@deck.gl/geo-layers";

// ------------------------------------------------------------------ types
type Branch = { i: number; id: string; kind: string; v: number; s_nom: number; path: [number, number][] };
type Bus = { i: number; id: string; lon: number; lat: number; v: number };
type Border = { border_id: string; bus: string; country: string; capacity_mw: number; kind: string };
type Behaviour = { type: string; [k: string]: unknown; modifiers?: Record<string, unknown>[] };
type Asset = {
  id: string; name?: string; kind: "producer" | "consumer" | "storage"; carrier: string; bus: string;
  p_nom: number | null; lon?: number | null; lat?: number | null; group?: string; n_units?: number;
  behaviour: Behaviour; source?: string;
};
type Grid = { buses: Bus[]; branches: Branch[]; borders: Border[]; behaviours: any; source: Record<string, string> };
type Sim = {
  snapshots: string[]; T: number; n_branches: number; n_buses: number;
  flow: Int16Array; inj: Int16Array; by_carrier: Record<string, number[]>;
  border_total: number[]; trade_deviation: number[]; price: number[];
  kpi: Record<string, number>; settings: Record<string, unknown>;
};

// ------------------------------------------------------------------ constants
const CARRIER_COLOR: Record<string, [number, number, number]> = {
  solar: [245, 197, 24], wind_onshore: [79, 195, 247], wind_offshore: [2, 136, 209],
  biomass: [139, 195, 74], hydro: [38, 166, 154], lignite: [141, 110, 99], hard_coal: [120, 120, 120],
  gas: [255, 138, 101], other_conventional: [176, 190, 197], other_renewable: [174, 213, 129],
  pumped_hydro: [126, 87, 194], battery: [206, 147, 216], load: [239, 83, 80],
};
const RES = ["solar", "wind_onshore", "wind_offshore", "biomass", "hydro", "other_renewable"];
const STACK = ["wind_offshore", "wind_onshore", "solar", "biomass", "hydro", "other_renewable",
  "lignite", "hard_coal", "gas", "other_conventional", "pumped_hydro", "battery"];

// ------------------------------------------------------------------ state
let grid: Grid;
let assets: Asset[] = [];
let sim: Sim | null = null;
let hour = 0;
let playing = false;
let speed = 1;
let placeMode = false;
let selected: { type: "bus"; id: string } | { type: "branch"; i: number } | null = null;
const busIndex = new Map<string, Bus>();

const $ = <T extends HTMLElement = HTMLElement>(id: string) => document.getElementById(id) as T;
const fmt = (x: number, d = 1) => x.toLocaleString("en-GB", { maximumFractionDigits: d, minimumFractionDigits: d });

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}
function decodeI16(b64: string): Int16Array {
  const bin = atob(b64);
  const u8 = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
  return new Int16Array(u8.buffer);
}

// ------------------------------------------------------------------ map
const map = new maplibregl.Map({
  container: "map",
  style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
  center: [10.4, 51.2], zoom: 5.6, attributionControl: { compact: true },
});
map.addControl(new maplibregl.NavigationControl(), "bottom-left");
const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
map.addControl(overlay as unknown as maplibregl.IControl);

function loadingColor(l: number, t: number): [number, number, number, number] {
  if (l > 1) return [255, 0, 200, Math.sin(t * 8) > 0 ? 255 : 110]; // overloaded: flashing
  const stops: [number, [number, number, number]][] = [
    [0, [46, 204, 113]], [0.4, [241, 196, 15]], [0.56, [230, 126, 34]], [0.8, [231, 76, 60]], [1, [231, 76, 60]],
  ];
  const x = Math.max(0, l);
  for (let k = 1; k < stops.length; k++) {
    if (x <= stops[k][0]) {
      const [x0, c0] = stops[k - 1], [x1, c1] = stops[k];
      const f = (x - x0) / (x1 - x0 || 1);
      return [0, 1, 2].map((j) => c0[j] + f * (c1[j] - c0[j])).concat(235) as [number, number, number, number];
    }
  }
  return [231, 76, 60, 235];
}

function flowAt(i: number): number { return sim ? sim.flow[hour * sim.n_branches + i] : 0; }
function loadingAt(i: number): number { return Math.abs(flowAt(i)) / grid.branches[i].s_nom; }
function injAt(i: number): number { return sim ? sim.inj[hour * sim.n_buses + i] : 0; }

// precomputed normalised timestamps for the flow animation
let tripBase: { i: number; path: [number, number][]; ts: number[] }[] = [];
function buildTrips() {
  tripBase = grid.branches.map((b) => {
    const d = [0];
    for (let k = 1; k < b.path.length; k++) {
      const [x0, y0] = b.path[k - 1], [x1, y1] = b.path[k];
      d.push(d[k - 1] + Math.hypot((x1 - x0) * Math.cos((y0 * Math.PI) / 180), y1 - y0));
    }
    const L = d[d.length - 1] || 1;
    return { i: b.i, path: b.path, ts: d.map((x) => x / L) };
  });
}

let animT = 0;
function render() {
  if (!grid) return;
  const show = (id: string) => $<HTMLInputElement>(id).checked;
  const layers: any[] = [];
  if (show("ly-lines")) {
    layers.push(new PathLayer<Branch>({
      id: "lines", data: grid.branches, getPath: (b) => b.path, pickable: true,
      getColor: (b) => (sim ? loadingColor(loadingAt(b.i), animT) : [90, 110, 130, 200]),
      getWidth: (b) => (b.v >= 380 ? 3 : b.v >= 220 ? 1.8 : 1.2), widthUnits: "pixels",
      updateTriggers: { getColor: [hour, sim, Math.floor(animT * 4)] },
      onClick: (info) => info.object && openBranch(info.object.i),
    }));
  }
  if (sim && show("ly-flow")) {
    const data = tripBase
      .filter((t) => loadingAt(t.i) > 0.05)
      .map((t) => (flowAt(t.i) >= 0 ? t : { ...t, path: [...t.path].reverse(), ts: [...t.ts].reverse().map((x) => 1 - x) }));
    layers.push(new TripsLayer<any>({
      id: "flow", data, getPath: (d) => d.path, getTimestamps: (d) => d.ts,
      getColor: [230, 240, 255], widthMinPixels: 2, trailLength: 0.35, currentTime: animT % 1,
      fadeTrail: true, capRounded: true,
    }));
  }
  if (sim && show("ly-inj")) {
    layers.push(new ScatterplotLayer<Bus>({
      id: "inj", data: grid.buses, getPosition: (b) => [b.lon, b.lat], pickable: true,
      getRadius: (b) => Math.sqrt(Math.abs(injAt(b.i))) * 140, radiusUnits: "meters",
      getFillColor: (b) => (injAt(b.i) >= 0 ? [46, 204, 113, 150] : [239, 83, 80, 150]),
      updateTriggers: { getRadius: [hour, sim], getFillColor: [hour, sim] },
      onClick: (info) => info.object && openBus(info.object.id),
    }));
  }
  if (show("ly-assets")) {
    const prod = assets.filter((a) => a.kind !== "consumer" && (a.p_nom ?? 0) > 0);
    layers.push(new ScatterplotLayer<Asset>({
      id: "assets", data: prod, pickable: true,
      getPosition: (a) => (a.lon != null && a.lat != null ? [a.lon, a.lat] : posOfBus(a.bus)),
      getRadius: (a) => Math.sqrt(a.p_nom ?? 0) * 110, radiusUnits: "meters",
      getFillColor: (a) => [...(CARRIER_COLOR[a.carrier] ?? [200, 200, 200]), a.source === "user" ? 255 : 150] as any,
      getLineColor: [255, 255, 255, 220], getLineWidth: (a) => (a.source === "user" ? 2 : 0), lineWidthUnits: "pixels",
      stroked: true, onClick: (info) => info.object && openBus(info.object.bus),
      updateTriggers: { getFillColor: [assets.length] },
    }));
  }
  layers.push(new ScatterplotLayer<Bus>({
    id: "buses", data: grid.buses, getPosition: (b) => [b.lon, b.lat], pickable: true,
    getRadius: 1.6, radiusUnits: "pixels", getFillColor: (b) => (b.v >= 380 ? [200, 210, 220, 200] : [140, 150, 160, 160]),
    onClick: (info) => info.object && openBus(info.object.id),
  }));
  if (show("ly-border")) {
    const total = sim ? sim.border_total[hour] : 0;
    const capSum = grid.borders.reduce((s, b) => s + b.capacity_mw, 0);
    layers.push(new ScatterplotLayer<Border>({
      id: "border", data: grid.borders, getPosition: (b) => posOfBus(b.bus), pickable: true,
      getRadius: (b) => 5 + Math.sqrt(Math.abs((total * b.capacity_mw) / capSum)) * 0.6, radiusUnits: "pixels",
      stroked: true, filled: false, getLineWidth: 2, lineWidthUnits: "pixels",
      getLineColor: () => (total >= 0 ? [79, 195, 247, 230] : [255, 202, 40, 230]),
      updateTriggers: { getRadius: [hour, sim], getLineColor: [hour, sim] },
    }));
  }
  overlay.setProps({
    layers,
    getTooltip: ({ object, layer }: any) => tooltip(object, layer?.id),
  });
}

function tooltip(o: any, layer?: string): string | null {
  if (!o) return null;
  if (layer === "lines") {
    const l = loadingAt(o.i);
    return `${o.kind} ${o.id}\n${o.v} kV · s_nom ${fmt(o.s_nom, 0)} MVA\nflow ${fmt(flowAt(o.i), 0)} MW · loading ${fmt(l * 100, 0)}%`;
  }
  if (layer === "inj" || layer === "buses") return `${o.id} (${o.v} kV)\nnet injection ${fmt(injAt(o.i), 0)} MW\nclick for assets`;
  if (layer === "assets") return `${o.name ?? o.id}\n${o.carrier} · ${fmt(o.p_nom ?? 0, 1)} MW${o.n_units ? ` · ${o.n_units} units` : ""}`;
  if (layer === "border") return `${o.kind} to ${o.country}\n${fmt(o.capacity_mw, 0)} MW capacity\nborder flow is split pro rata by capacity (v0)`;
  return null;
}

function posOfBus(id: string): [number, number] {
  const b = busIndex.get(id);
  return b ? [b.lon, b.lat] : [0, 0];
}

// ------------------------------------------------------------------ KPIs, mix chart
function updateKpis() {
  if (!sim) return;
  const c = sim.by_carrier;
  const load = c.load?.[hour] ?? 0;
  const gen = STACK.reduce((s, k) => s + Math.max(0, c[k]?.[hour] ?? 0), 0);
  const res = RES.reduce((s, k) => s + (c[k]?.[hour] ?? 0), 0);
  let maxL = 0, n70 = 0, n100 = 0;
  for (let i = 0; i < sim.n_branches; i++) {
    const l = loadingAt(i);
    maxL = Math.max(maxL, l); if (l > 0.7) n70++; if (l > 1) n100++;
  }
  const t = new Date(sim.snapshots[hour]);
  $("k-time").textContent = t.toLocaleString("de-DE", { timeZone: "Europe/Berlin", weekday: "short", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  $("k-load").textContent = `${fmt(load / 1000)} GW`;
  $("k-res").textContent = `${fmt((100 * res) / (gen || 1), 0)}%`;
  $("k-imp").textContent = `${fmt(sim.border_total[hour] / 1000)} GW`;
  $("k-price").textContent = `${fmt(sim.price[hour], 0)} €/MWh`;
  $("k-max").textContent = `${fmt(maxL * 100, 0)}%`;
  $("k-over").textContent = `${n70} / ${n100}`;
  drawMix();
}

function drawMix() {
  const cv = $<HTMLCanvasElement>("mix");
  const w = (cv.width = cv.clientWidth * devicePixelRatio), h = (cv.height = 70 * devicePixelRatio);
  const g = cv.getContext("2d")!;
  g.clearRect(0, 0, w, h);
  if (!sim) return;
  const T = sim.T, c = sim.by_carrier;
  let ymax = 1;
  for (let t = 0; t < T; t++) {
    ymax = Math.max(ymax, c.load?.[t] ?? 0, STACK.reduce((s, k) => s + Math.max(0, c[k]?.[t] ?? 0), 0));
  }
  const X = (t: number) => (t / Math.max(1, T - 1)) * w, Y = (v: number) => h - (v / ymax) * (h - 4);
  const base = new Array(T).fill(0);
  for (const k of STACK) {
    if (!c[k]) continue;
    g.beginPath();
    for (let t = 0; t < T; t++) g.lineTo(X(t), Y(base[t] + Math.max(0, c[k][t])));
    for (let t = T - 1; t >= 0; t--) g.lineTo(X(t), Y(base[t]));
    const col = CARRIER_COLOR[k] ?? [200, 200, 200];
    g.fillStyle = `rgba(${col.join(",")},0.85)`;
    g.fill();
    for (let t = 0; t < T; t++) base[t] += Math.max(0, c[k][t]);
  }
  if (c.load) {
    g.beginPath(); g.strokeStyle = "#fff"; g.lineWidth = 1.5 * devicePixelRatio;
    for (let t = 0; t < T; t++) g.lineTo(X(t), Y(c.load[t]));
    g.stroke();
  }
  g.fillStyle = "rgba(255,255,255,.9)";
  g.fillRect(X(hour) - devicePixelRatio, 0, 2 * devicePixelRatio, h);
}

// ------------------------------------------------------------------ side panel
function openBus(busId: string) {
  selected = { type: "bus", id: busId };
  const b = busIndex.get(busId)!;
  const here = assets.filter((a) => a.bus === busId);
  const rows = here
    .sort((a, b2) => (b2.p_nom ?? 0) - (a.p_nom ?? 0))
    .map((a) => `<tr>
      <td><span class="dot" style="background:rgb(${(CARRIER_COLOR[a.carrier] ?? [200, 200, 200]).join(",")})"></span>${a.name ?? a.carrier}
        ${a.source === "user" ? '<span class="tag">yours</span>' : a.group === "aggregate" ? `<span class="tag">${a.n_units ?? ""} small units</span>` : ""}</td>
      <td>${a.kind}</td><td class="num">${a.p_nom != null ? fmt(a.p_nom, 1) : "–"}</td>
      <td class="muted">${a.behaviour.type}${a.behaviour.modifiers?.length ? " +" + a.behaviour.modifiers.map((m) => m.type).join("+") : ""}</td>
      <td><button class="ghost" data-del="${a.id}" title="remove">✕</button></td></tr>`).join("");
  $("right-body").innerHTML = `
    <h3>Substation</h3><b>${busId}</b> · ${b.v} kV · ${b.lat.toFixed(3)}, ${b.lon.toFixed(3)}
    <div class="muted">net injection now: ${fmt(injAt(b.i), 0)} MW</div>
    <h3>Assets here (${here.length})</h3>
    <table><tr><th>asset</th><th>kind</th><th>MW</th><th>behaviour</th><th></th></tr>${rows}</table>
    ${assetForm(busId)}`;
  $("right").classList.remove("hidden");
  bindForm(busId);
  $("right-body").querySelectorAll<HTMLButtonElement>("[data-del]").forEach((btn) =>
    btn.addEventListener("click", async () => {
      await api(`/api/assets/${encodeURIComponent(btn.dataset.del!)}`, { method: "DELETE" });
      await refreshAssets(); openBus(busId); runSim();
    }));
}

function assetForm(busId: string): string {
  const carriers = Object.keys(CARRIER_COLOR).filter((c) => c !== "load");
  return `<h3>Add asset at ${busId}</h3>
    <label>Kind <select id="f-kind"><option>producer</option><option>storage</option><option>consumer</option></select></label>
    <label>Technology <select id="f-carrier">${carriers.map((c) => `<option>${c}</option>`).join("")}</select></label>
    <label>Name <input id="f-name" placeholder="e.g. my wind farm" /></label>
    <label>Rated power (MW) <input id="f-pnom" type="number" value="100" min="0" /></label>
    <label>Behaviour <select id="f-beh">
      <option value="national_profile">national 2024 profile of the technology</option>
      <option value="constant">constant output / demand</option>
      <option value="daily_arbitrage">daily price arbitrage (storage rule)</option>
    </select></label>
    <div id="f-params"></div>
    <fieldset><legend>Stochastic modifiers (your assumptions, not data)</legend>
      <label class="chk"><input type="checkbox" id="f-noise" /> AR(1) noise</label>
      <div class="row"><input id="f-sigma" type="number" step="0.01" placeholder="sigma (e.g. relative std)" /><input id="f-phi" type="number" step="0.05" placeholder="phi 0-1" /></div>
      <label class="chk"><input type="checkbox" id="f-out" /> forced outages</label>
      <div class="row"><input id="f-for" type="number" step="0.01" placeholder="outage rate 0-1" /><input id="f-mttr" type="number" placeholder="mean repair h" /></div>
    </fieldset>
    <button id="f-add">Add &amp; simulate</button><div id="f-msg" class="muted"></div>`;
}

function bindForm(busId: string) {
  const params = () => {
    const beh = $<HTMLSelectElement>("f-beh").value;
    $("f-params").innerHTML = beh === "constant"
      ? `<label>Constant MW <input id="f-pmw" type="number" value="${$<HTMLInputElement>("f-pnom").value}" /></label>`
      : beh === "daily_arbitrage"
      ? `<label>Energy (hours at rated power) <input id="f-eh" type="number" value="4" /></label>
         <label>Round-trip efficiency <input id="f-eta" type="number" step="0.01" placeholder="0-1, your input" /></label>`
      : `<div class="muted">Output = rated MW × 2024 national capacity factor of the technology (SMARD ÷ MaStR capacity).</div>`;
  };
  $("f-beh").addEventListener("change", params);
  $("f-kind").addEventListener("change", () => {
    const k = $<HTMLSelectElement>("f-kind").value;
    if (k === "storage") { $<HTMLSelectElement>("f-carrier").value = "battery"; $<HTMLSelectElement>("f-beh").value = "daily_arbitrage"; }
    if (k === "consumer") { $<HTMLSelectElement>("f-beh").value = "constant"; }
    params();
  });
  params();
  $("f-add").addEventListener("click", async () => {
    const kind = $<HTMLSelectElement>("f-kind").value as Asset["kind"];
    const carrier = kind === "consumer" ? "load" : $<HTMLSelectElement>("f-carrier").value;
    const p_nom = Number($<HTMLInputElement>("f-pnom").value);
    const type = $<HTMLSelectElement>("f-beh").value;
    const behaviour: Behaviour = { type };
    if (type === "constant") behaviour.p_mw = Number($<HTMLInputElement>("f-pmw").value);
    if (type === "national_profile") behaviour.carrier = carrier;
    if (type === "daily_arbitrage") {
      behaviour.energy_hours = Number($<HTMLInputElement>("f-eh").value);
      const eta = $<HTMLInputElement>("f-eta").value;
      if (eta === "") { $("f-msg").textContent = "Enter a round-trip efficiency (your assumption)."; return; }
      behaviour.efficiency = Number(eta);
    }
    const mods: Record<string, unknown>[] = [];
    if ($<HTMLInputElement>("f-noise").checked) mods.push({ type: "noise", sigma: Number($<HTMLInputElement>("f-sigma").value), phi: Number($<HTMLInputElement>("f-phi").value || 0) });
    if ($<HTMLInputElement>("f-out").checked) mods.push({ type: "outage", forced_outage_rate: Number($<HTMLInputElement>("f-for").value), mttr_hours: Number($<HTMLInputElement>("f-mttr").value) });
    if (mods.length) behaviour.modifiers = mods;
    const b = busIndex.get(busId)!;
    try {
      await api("/api/assets", { method: "POST", body: JSON.stringify({
        kind, carrier, bus: busId, p_nom, name: $<HTMLInputElement>("f-name").value || `${carrier} ${fmt(p_nom, 0)} MW`,
        lon: b.lon, lat: b.lat, group: "unit", n_units: 1, behaviour }) });
      await refreshAssets(); openBus(busId); runSim();
    } catch (e) { $("f-msg").textContent = String(e); }
  });
}

function openBranch(i: number) {
  selected = { type: "branch", i };
  const b = grid.branches[i];
  $("right-body").innerHTML = `<h3>${b.kind}</h3><b>${b.id}</b><div class="muted">${b.v} kV · s_nom ${fmt(b.s_nom, 0)} MVA</div>
    <h3>Loading over the run</h3><canvas id="spark" style="width:100%;height:140px"></canvas>
    <div class="muted">dashed: 70% (n-1 proxy) and 100%</div>`;
  $("right").classList.remove("hidden");
  if (!sim) return;
  const cv = $<HTMLCanvasElement>("spark");
  const w = (cv.width = cv.clientWidth * devicePixelRatio), h = (cv.height = 140 * devicePixelRatio);
  const g = cv.getContext("2d")!;
  const vals = Array.from({ length: sim.T }, (_, t) => Math.abs(sim!.flow[t * sim!.n_branches + i]) / b.s_nom);
  const ymax = Math.max(1.1, ...vals);
  const X = (t: number) => (t / Math.max(1, sim!.T - 1)) * w, Y = (v: number) => h - (v / ymax) * h;
  for (const ref of [0.7, 1]) { g.setLineDash([4, 4]); g.strokeStyle = "#8b98a8"; g.beginPath(); g.moveTo(0, Y(ref)); g.lineTo(w, Y(ref)); g.stroke(); }
  g.setLineDash([]); g.strokeStyle = "#4fc3f7"; g.lineWidth = 1.5 * devicePixelRatio; g.beginPath();
  vals.forEach((v, t) => g.lineTo(X(t), Y(v))); g.stroke();
}

// ------------------------------------------------------------------ data flow
async function refreshAssets() {
  assets = await api<Asset[]>("/api/assets");
  const sc = await api<any>("/api/scenario");
  $("edits").textContent = `edits: +${Object.keys(sc.added).length} added, ${Object.keys(sc.modified).length} modified, ${sc.removed.length} removed`;
}

let simToken = 0;
async function runSim() {
  const token = ++simToken;
  $("run-status").textContent = "simulating…";
  const t0 = performance.now();
  try {
    const raw = await api<any>("/api/simulate", { method: "POST", body: JSON.stringify({
      start: $<HTMLInputElement>("in-start").value, hours: Number($<HTMLSelectElement>("in-hours").value),
      balancing: $<HTMLSelectElement>("in-bal").value, seed: Number($<HTMLInputElement>("in-seed").value) }) });
    if (token !== simToken) return;
    sim = { ...raw, flow: decodeI16(raw.flow_i16), inj: decodeI16(raw.injection_i16) };
    const s = $<HTMLInputElement>("slider");
    s.max = String(sim!.T - 1);
    hour = Math.min(hour, sim!.T - 1); s.value = String(hour);
    const k = sim!.kpi;
    $("run-status").textContent = `${sim!.T} h in ${fmt((performance.now() - t0) / 1000)} s · max loading ${fmt(k.max_loading * 100, 0)}% · ` +
      `${k.line_hours_over_100pct} overloaded line-hours · max trade deviation ${fmt(k.max_trade_deviation_mw, 0)} MW`;
    updateKpis(); render();
    if (selected?.type === "branch") openBranch(selected.i);
  } catch (e) { $("run-status").textContent = String(e); }
}

async function refreshScenarioList() {
  const list = await api<string[]>("/api/scenarios");
  $("sc-list").innerHTML = list.map((n) => `<option>${n}</option>`).join("");
}

function methodPanel() {
  $("modal-body").innerHTML = `<button class="x" id="mclose">×</button>
  <h2>Data &amp; method</h2>
  <p>A <b>playground</b> of the German transmission grid as it was in 2024. It shows physics of a
  linear (DC) power flow for the injections you define. It is <b>not an optimisation</b> and not a
  market model yet.</p>
  <h3>Sources</h3><ul>
    <li>Grid: ${grid.source.grid} – <a href="https://zenodo.org/records/18619025" target="_blank">Zenodo</a>, built by PyPSA-Eur (<a href="https://github.com/PyPSA/pypsa-eur" target="_blank">GitHub</a>).</li>
    <li>Units: ${grid.source.units} – <a href="https://www.marktstammdatenregister.de/MaStR" target="_blank">MaStR</a>, via open-mastr.</li>
    <li>Hourly load, generation per technology, prices: ${grid.source.timeseries} – <a href="https://www.smard.de" target="_blank">smard.de</a>.</li>
    <li>Population by NUTS3 (demand split): Eurostat demo_r_pjanaggr3; boundaries © EuroGeographics (GISCO).</li>
    <li>Base map © OpenStreetMap contributors © CARTO.</li></ul>
  <h3>Method</h3><ol>
    <li>Static grid: German 220–380 kV substations, lines and transformers from OSM (s_nom, r, x).</li>
    <li>Producers: MaStR units in operation at 2024-12-31; units ≥ 10 MW individually, smaller ones aggregated per substation and technology; all attached to the nearest substation.</li>
    <li>Behaviour: each producer = rated MW × the 2024 national hourly capacity factor of its technology (SMARD output ÷ MaStR capacity). Demand = national SMARD load × population share of the substation's area.</li>
    <li>Balancing: historical 2024 net import is kept at the border; your edits are absorbed by dispatchable plants (or the border, if chosen).</li>
    <li>Flows: DC power flow via the PTDF matrix; loading = |flow| / s_nom.</li></ol>
  <h3>Known limits (v0)</h3><ul>
    <li>No regional weather: every wind/PV unit follows the national profile.</li>
    <li>Demand split by population only (industry not located).</li>
    <li>Neighbouring grids not modelled; border flows split by interconnector capacity.</li>
    <li>Offshore wind attached to the nearest coastal substation (offshore connections not in the OSM set).</li>
    <li>Conventional plants replay their technology's national output pro rata (no merit order yet).</li>
    <li>Distribution grid not modelled.</li></ul>`;
  $("modal").classList.remove("hidden");
  $("mclose").addEventListener("click", () => $("modal").classList.add("hidden"));
}

// ------------------------------------------------------------------ wiring
function wire() {
  $("btn-run").addEventListener("click", runSim);
  $("slider").addEventListener("input", (e) => { hour = Number((e.target as HTMLInputElement).value); updateKpis(); render(); });
  $("btn-play").addEventListener("click", () => { playing = !playing; $("btn-play").textContent = playing ? "❚❚" : "▶"; });
  document.querySelectorAll<HTMLButtonElement>(".speeds button").forEach((b) => b.addEventListener("click", () => {
    speed = Number(b.dataset.speed); document.querySelectorAll(".speeds button").forEach((x) => x.classList.remove("on")); b.classList.add("on");
  }));
  ["ly-lines", "ly-flow", "ly-inj", "ly-assets", "ly-border"].forEach((id) => $(id).addEventListener("change", render));
  $("close-right").addEventListener("click", () => { $("right").classList.add("hidden"); selected = null; });
  $("btn-method").addEventListener("click", methodPanel);
  $("sc-save").addEventListener("click", async () => {
    const n = $<HTMLInputElement>("sc-name").value.trim();
    if (!n) return;
    await api(`/api/scenarios/${encodeURIComponent(n)}/save`, { method: "POST" });
    refreshScenarioList();
  });
  $("sc-load").addEventListener("click", async () => {
    await api(`/api/scenarios/${encodeURIComponent($<HTMLSelectElement>("sc-list").value)}/load`, { method: "POST" });
    await refreshAssets(); runSim();
  });
  $("btn-place").addEventListener("click", () => { placeMode = !placeMode; document.body.classList.toggle("place-mode", placeMode);
    $("btn-place").textContent = placeMode ? "click on the map… (Esc to cancel)" : "+ Place new asset on map"; });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && placeMode) $("btn-place").click(); });
  map.on("click", (e) => {
    if (!placeMode) return;
    let best: Bus | null = null, bd = Infinity;
    for (const b of grid.buses) {
      const d = Math.hypot((b.lon - e.lngLat.lng) * Math.cos((b.lat * Math.PI) / 180), b.lat - e.lngLat.lat);
      if (d < bd) { bd = d; best = b; }
    }
    $("btn-place").click();
    if (best) openBus(best.id);
  });

  let last = performance.now(), acc = 0;
  const tick = (now: number) => {
    const dt = (now - last) / 1000; last = now;
    animT += dt * 0.6;
    if (playing && sim) {
      acc += dt * speed;
      if (acc >= 1) { hour = (hour + Math.floor(acc)) % sim.T; acc %= 1; $<HTMLInputElement>("slider").value = String(hour); updateKpis(); }
    }
    render();
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

async function main() {
  grid = await api<Grid>("/api/grid");
  grid.buses.forEach((b) => busIndex.set(b.id, b));
  buildTrips();
  await refreshAssets();
  await refreshScenarioList();
  wire();
  render();
  runSim();
}
main().catch((e) => { $("run-status").textContent = `failed to load: ${e}`; console.error(e); });
