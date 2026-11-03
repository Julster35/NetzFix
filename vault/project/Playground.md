---
type: plan
date: 2026-11-03
tags: [playground, simulation, web-ui, core]
ai-first: true
status: "v0 running (2026-11-03, commit 4c57ae5): 2024 grid as is, 6,911 assets, full year simulates in ~1.3 s; replay reproduces SMARD 2024 energy per technology; 0.134% of line-hours > 100% loading, partly attachment artefacts."
---

# Playground

## For future agent
The playground is Julien's chosen first step (2026-11-03, [[Decision Log]] "Re-scope"): the German transmission grid of 2024 "as is", with every producer and consumer attached to a substation, where assets can be added, edited and given stochastic behaviour, and the resulting DC line flows are shown on a map. It is a simulation, not an optimisation and not a market model. Run it with `uv run netzfix serve` and open http://127.0.0.1:8765.

---

## How to run
```
uv sync
uv run netzfix build      # downloads + builds everything (MaStR zip is 3.27 GB; ~15 min)
cd web && npm install && npm run build && cd ..
uv run netzfix serve      # http://127.0.0.1:8765
```
Dev mode for the UI: `uv run netzfix serve` + `cd web && npm run dev` (port 5173, proxies `/api`).

## What is in it (all `stated`, from `results/playground_baseline_2024/diagnostics.json`, `scripts/diagnose_baseline.py`, commit 4c57ae5, and `data/processed/assets_baseline_2024_report.json`)
- **Grid:** 780 German buses, 1,019 lines, 153 transformers; since 2026-11-03 also 41 real cross-border lines and Kron-reduced equivalents of the AC neighbours (38 buses, 60 equivalent lines; 818 buses / 1,273 branches in total), driven by measured 2024 physical flows per country ([[Energy-Charts]], [[Assumptions]] A18 v1, A21b). The v0 numbers below are from before that change.
- **Assets:** 6,911 (1,280 single producers ≥ 10 MW, 3,948 aggregated producer groups, 150 single + 896 aggregated storage, 637 demand nodes), built from 6,798,004 MaStR units operating in at least one month of 2024.
- **Locations (by capacity):** own coordinates 163.9 GW, powerplantmatching 73.0 GW, municipality 47.1 GW, district centre 1.1 GW, unplaced 6.8 MW (17 small solar units). Median distance unit → substation 11.2 km.
- **Fleet Jan → Dec 2024 (MW, MaStR):** solar 76,345 → 90,019; wind onshore 61,028 → 63,483; offshore 8,473 → 9,215; lignite 18,266 → 15,169; hard coal 18,226 → 15,382; gas 34,596 → 34,608; pumped hydro 9,960 → 9,900; batteries 8,367 → 12,015 ([[Marktstammdatenregister]]).
- **Replay check:** annual energy per technology equals SMARD 2024 (e.g. wind onshore 112.56 TWh, solar 63.15 TWh, lignite 70.97 vs 70.99 TWh: 17.1 GWh clipped where national output exceeded month-end capacity). Net trade reproduced exactly in "keep trade" mode.
- **Flows, full year 2024, baseline:** 92,467 line-hours > 70% loading, 13,843 > 100% (0.134% of line-hours), 51 of 1,172 branches overloaded at least once, max 3.95 on a 5 km 220 kV line next to Rheinhafen-Dampfkraftwerk Karlsruhe.

## How to read overloads
Flows are the physics of the **market-like dispatch before redispatch** (each unit follows its technology's national profile), so overloads are expected where real operators redispatch. But some come from **attachment artefacts** (`medium`): units placed at the nearest substation regardless of their real connection voltage (e.g. Karlsruhe: 1.7 GW at a 220 kV node); demand split by population only; neighbours not modelled. Do not quote overload numbers as congestion findings before [[Validation]].

## Engine (code: `src/netzfix/sim/`)
- **Behaviours** (JSON on each asset): `national_profile` (rated MW × 2024 national capacity factor of the technology = SMARD output ÷ MaStR capacity active that month), `demand_share`, `constant`, `replay_pumped_hydro`, `daily_arbitrage` (rule: charge in the k cheapest, discharge in the k dearest hours of each day).
- **Stochastic modifiers** ([[Assumptions]] A22): AR(1) multiplicative noise (sigma, phi), two-state Markov forced outages (rate, mean time to repair). Seeded per asset with crc32 keys, so runs are reproducible. Parameters are user inputs, never data.
- **Balancing** (A21): `keep_trade` holds the 2024 net import; edits are absorbed pro rata by lignite, hard coal, gas, other conventional; the rest goes to the border and is reported as trade deviation. Or `border`: the border absorbs everything.
- **Flows:** PTDF (PyPSA) × bus injections; loading = |flow| / s_nom; 70% = n-1 proxy line ([[N-1 Security Proxy]]).
- Tests: `tests/test_engine.py` (3-bus triangle flows 60/30, balance, keep-trade displacement, outage rate, noise std, arbitrage energy), `tests/test_server.py` (API, add asset, scenario round trip).

## UI (code: `web/`)
Full-screen dark map; KPI strip (hour, load, renewable share, net import, price, max loading, lines > 70% / > 100%); lines coloured by loading with flashing overloads; animated flow direction; net injection per substation; producer bubbles by technology; border points; time slider with 1×/5×/10×/20× playback; generation-mix chart; click a substation to list and remove assets and add new ones (technology, MW, behaviour, modifiers); click a line for its loading curve; "place new asset on map"; scenario save/load (`scenarios/*.json`, edits on top of the baseline); "Data & method" panel. English only for now (brief asks for DE + EN toggle).

## Not yet checked
- The UI was built and its assets are served (HTTP 200), but it was **not visually tested by Claude** (Chrome extension not connected on 2026-11-03). Julien to open it.
