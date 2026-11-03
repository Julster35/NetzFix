---
type: input
date: 2026-11-03
tags: [input, brief, scope, frozen]
ai-first: true
from: Julien Froidefond
status: frozen copy of the owner's founding brief (verbatim below the line)
---

# 2026-11-03 Julien project brief

## For future agent
This is the founding brief for NetzFix, pasted by Julien into the first Claude Code session on 2026-11-03 and frozen here verbatim. It defines the research question (uniform vs zonal vs nodal pricing in Germany), the vault rules, the pre-registration, the model, the web twin and Milestones 0-1. Later decisions in [[Decision Log]] override it where they conflict.

---

# Project: NetzFix — German Grid Digital Twin (Uniform vs. Zonal vs. Nodal Pricing)

Repo: C:/Users/julie/Documents/NetzFix   ·   Python package: src/netzfix   ·   Owner: Julien Froidefond (M.Sc., JMU Würzburg)

## Goal
Build a reproducible, open-data model of the German transmission grid (generation, demand, network) that answers one question with defensible numbers:

  Is total system cost lower under (A) one German price zone + redispatch, (B) 2–5 bidding zones + redispatch, or (C) nodal pricing (LMP)? And under nodal/zonal prices, does generation or storage in southern Germany become profitable where it is not under a uniform price?

Plus an interactive HTML twin that makes the answer visible. This is a research model with a falsifiable answer, NOT an operational twin. There is a bet riding on the result, so rigor and traceability come before features. Never invent or hardcode numbers that look like data. Every input comes from a cited source, and every assumption is logged in the vault.

====================================================================
## PART 0 — Prior art: reuse, don't rebuild
====================================================================
Build on existing open code. Only write what doesn't exist yet. Verify each item live (repo activity, license, current API) and log the reuse decisions in the Decision Log.
- PyPSA-Eur (github.com/PyPSA/pypsa-eur, MIT): use its Snakemake workflow for the OSM transmission network, powerplantmatching, atlite renewable profiles, load, and network clustering. Configure for DE + neighbours, electricity only. Pin a release.
- PyPSA redispatch example (docs.pypsa.org/latest/examples/scigrid-redispatch/): the template for market designs A/B/C (zonal market → fix dispatch → nodal redispatch vs nodal benchmark). Generalise it to multi-period, real data, configurable zone maps, cost-based redispatch compensation.
- PyPSA-DE (github.com/PyPSA/pypsa-de, MIT): reference only. Borrow German-specific data/assumptions where useful (cite them). Don't fork it, because it's sector-coupled and too heavy.
- open-mastr, entsoe-py, atlite: use as libraries.
- eTraGo / eGon-data (AGPL, database-heavy): don't build on these. Read them for method comparison only.
- Benchmark paper: Knörr, Bichler, Dobos (arXiv 2403.09265, v6 2025): on the ENTSO-E BZR 2025 dataset, zonal splits save <1% of total cost and nodal saves 5–6%. Our results must be discussed against this. Check whether the BZR dataset they used is publicly downloadable. If yes, add it as a second network/input source for cross-validation (data/ note + Decision Log).

====================================================================
## PART 1 — Knowledge vault (set this up FIRST, before any code)
====================================================================
Follow the structure of my existing research vaults. Reference implementation: C:/Users/julie/Documents/the-elo-of-e-aura/vault. Read its _CLAUDE.md, index.md, 00_Home.md, log.md, one Logs/ file, project/Decision Log.md and project/Analysis Log.md, and mirror their conventions exactly. Don't copy their content.

### Layout
  CLAUDE.md                  repo root: code conventions + commands + "@vault/_CLAUDE.md" import
  RESEARCH_PLAN.md           repo root: short plan, links into the vault
  vault/                     Obsidian vault
    _CLAUDE.md               operating manual, single source of truth for how Claude works here
    .claude/CLAUDE.md        contains only: @../_CLAUDE.md
    00_Home.md               dashboard / MOC: research question, dated status line, links, one-paragraph summary
    index.md                 catalog of every note by folder with one-line descriptions. Read it before searching. Update it on every new note.
    log.md                   pointer only (format of the per-day logs), never written to
    Logs/YYYY-MM-DD.md       per-day ops log: "**HH:MM** - action | description", actions: init, ingest, save, spec, check, result, decision, infra, viz, outbox
    project/                 Research Question, Research Design, Hypotheses, Assumptions, Validation, Decision Log, Analysis Log, Next Steps, Open Questions, Prior Art
    concepts/                Uniform Pricing and Redispatch, Zonal Pricing and Bidding Zones, Nodal Pricing (LMP), DC Power Flow, N-1 Security Proxy, Market Value of a Unit, Network Clustering, Cost-Based Redispatch Compensation
    data/                    Data Sources (master) + one note per source (ENTSO-E Transparency, SMARD, Marktstammdatenregister, OSM / PyPSA-Eur Grid, ERA5 and atlite, DemandRegio, netztransparenz Redispatch, JAO, BZR dataset) + Raw Data Inventory
    literature/              one note per paper + Reading List + Literature Synthesis; PDFs in literature/pdfs/
    figures/                 PNGs + Figures note
    inputs/                  frozen external inputs, "YYYY-MM-DD Who what.md"
    outbox/                  "YYYY-MM-DD Julien to X topic.md"

### Vault rules (in _CLAUDE.md as Sections 0 / 0.25 / 0.5, as in the reference vault)
0. AI-first: each new note opens with "## For future agent" (2–3 sentences) and is self-contained. Frontmatter: type, date, tags, ai-first: true (+ status: for findings, pdf: for literature). Every claim gets a recency marker, inline source URLs, and results cite script + data file + commit. [[wikilinks]] are mandatory. Each claim gets a confidence level: stated | high | medium | speculation.
0.25. LITERATURE RULE: only rely on literature whose PDF is held in literature/pdfs/. Quote numbers with page/table. Papers not held go in "Reading List#Not held - do not cite". Grey literature (ENTSO-E BZR study, BNetzA reports, EWI briefs) counts as held only once downloaded. First PDFs to fetch: Knörr/Bichler/Dobos (arXiv 2403.09265), the PyPSA-Eur paper, the ENTSO-E BZR 2025 study, the EWI Gebotszonen policy brief, BNetzA Netzengpassmanagement reports.
0.5. Verify live state before acting: read the data before declaring a result, recompute before quoting, and fetch live figures (never from training data).

### Pre-registration (this is what settles the bet)
- project/Hypotheses.md: H1–H3 below + exact metric + decision rule + what counts as "cheaper" (e.g. difference in total system cost > X% and robust in all sensitivity runs). Freeze it BEFORE any A/B/C comparison run.
- Seal the freeze with OpenTimestamps as in the-elo-of-e-aura (timestamps/ + README + .ots proof, `ots upgrade` later). Log the anchor commit in the Decision Log. Only a hash leaves the machine.
- Analysis Log: an entry for every specification BEFORE its result is looked at, whatever the result. Newest at the bottom. Template:
    ### YYYY-MM-DD - short name
    - Scenario: (design A/B/C, zone map, year, weather year, buses, resolution, line rating, solver)
    - Inputs: (data versions / MANIFEST rows)
    - Output metric:
    - Result: (numbers) - script, results file, commit
    - Why run / what changed vs previous:
- Decision Log: newest first, with decision, who, reason, consequences. It overrides any other note.

### Second brain propagation (C:/Users/julie/Documents/SecondBrain)
Read SecondBrain/_CLAUDE.md. At the end of each working session: update SecondBrain/Projects/NetzFix.md (Templates/Project.md), add SecondBrain/Dev Logs/YYYY-MM-DD - NetzFix <topic>.md (Templates/Dev Log.md), and add a line to SecondBrain/Daily/YYYY-MM-DD.md. Detail stays in the repo vault; the second brain gets summaries + links. Ask before deleting or archiving anything.

### .gitignore
data/raw/, data/processed/* (whitelist small tables), *.nc, cutouts/, results/networks/*.nc, web/node_modules/, web/dist/, .env, .venv/, __pycache__/, vault/.obsidian/workspace*.json

====================================================================
## PART 2 — The model
====================================================================
### Before writing model code
Write project/Prior Art.md (Part 0 verified), project/Research Design.md and RESEARCH_PLAN.md with milestones, structure and open decisions. Then STOP and show me.

### Tech stack
Python 3.11+, uv, pypsa, linopy, atlite, pandas, geopandas, entsoe-py, open-mastr, snakemake (via PyPSA-Eur), pytest, ruff. Solver: HiGHS default, Gurobi via config (academic license). Secrets (ENTSOE_API_TOKEN) in .env. Windows machine: Windows-safe paths and commands. If PyPSA-Eur's workflow is painful on Windows, propose WSL2 and log the decision.

### Base year
2024, weather year 2024, both configurable.

### Data layers (download → data/raw + MANIFEST.csv: url, access date, sha256 → data/processed; one vault note each)
1. Grid: PyPSA-Eur OSM network, DE + aggregated neighbours.
2. Units: Marktstammdatenregister via open-mastr.
3. Wind/solar: atlite + ERA5, weighted by MaStR capacities per node.
4. Conventional: ENTSO-E actual generation per unit (>100 MW) for calibration. Cited 2024 fuel + CO2 prices.
5. Demand: ENTSO-E hourly DE load regionalised to nodes (DemandRegio/FfE if accessible, else population + industrial employment, NUTS3). This is the weakest layer, so document it in Assumptions.
6. Cross-border: ENTSO-E flows / neighbour prices (fixed from history first).
7. Validation: SMARD/ENTSO-E day-ahead prices, netztransparenz.de redispatch measures, BNetzA curtailment + congestion-management costs.

### Physics defaults (configurable, all in project/Assumptions.md)
Linear DC power flow. s_max_pu = 0.7 (n-1 proxy). Clustered to N buses (start 50 → 200+). Representative weeks / 3h resolution first, then a full hourly year. No distribution grid.

### Market designs
A. Uniform: stage 1 copper-plate DE dispatch (cross-border limits kept). Stage 2 cost-based redispatch with network constraints.
B. Zonal: 2-zone N/S + an approximation of the ENTSO-E 2025 BZR 5-zone map (mapping documented). Stage 1 with inter-zonal limits, stage 2 redispatch.
C. Nodal: one-stage LOPF. LMP = shadow price of the nodal balance.
Outputs per design: total system cost, node/zone prices (series + means), RES curtailment, redispatch MWh and €, congestion rent, CO2, consumer cost north vs south, line loadings per hour.

### Investment question
Market value (€/MWh, €/MW/yr) of a hypothetical PV, onshore wind, 4h battery and gas peaker unit at every node under A/B/C, vs annualised CAPEX (cited, e.g. DEA catalogue). Map profitability. Optional: capacity expansion, nodal vs uniform siting.

### Validation (mandatory before any comparison result → project/Validation.md)
Modelled vs actual 2024 DE-LU price (correlation, MAE, duration curve), generation mix, redispatch volume + curtailment vs published figures (~€3bn/yr congestion management, order of magnitude must match). Then compare our A/B/C cost ratios to Knörr et al.'s and explain any differences.

### Hypotheses (project/Hypotheses.md, freeze + timestamp before A/B/C comparisons)
H1: total system cost nodal < zonal < uniform+redispatch
H2: southern nodal prices are systematically higher than northern ones
H3: at least one technology (battery or PV) is profitable in the south under nodal/zonal but not under uniform
Sensitivities: line rating 0.6/0.7/0.8, cluster size, CO2/gas price, with/without SuedLink. Report against the hypotheses whatever the result.

====================================================================
## PART 3 — NetzFix web twin (interactive HTML)
====================================================================
Style reference: https://aabhash.de/ki-regio/wuerzburg-tram-twin/ (JMU/CAIDAS "Transit Twin"). Study its page and match its pattern: a full-screen map, a KPI strip, layer toggles, a playback time slider with speed buttons, a selector to switch modes, and a "Data and method" panel listing sources, method steps and known limits.

### Architecture
- The Python side exports static artifacts per scenario into web/public/data/: network GeoJSON (buses, lines with voltage/capacity), hourly time series as compact JSON or Arrow (bus prices, line loading %, flows, generation by carrier per node, redispatch up/down), plus scenario KPIs. Exporter: src/netzfix/viz/export_web.py. The site must load without a backend.
- Frontend in web/: Vite + TypeScript, MapLibre GL JS + deck.gl. Free base map with attribution (OSM / CARTO dark-matter style), dark theme by default. Deploy as a static site (GitHub Pages).

### Views and controls
- Market design switch: A Uniform+Redispatch | B Zonal (2 / 5 zones) | C Nodal, plus a "Diff" mode (C minus A).
- Layers: transmission lines coloured by loading (green → red, overloaded flashing), animated flow direction along lines (deck.gl TripsLayer or a dashed-offset animation), nodes coloured by price (diverging scale around the national mean), zone polygons for B, generation bubbles by carrier, redispatch up/down markers, curtailment heat.
- Time: hourly playback over the year with play/pause, 1x/5x/10x/20x speed, a date picker, and "jump to" presets (windiest hour, max redispatch hour, max N/S spread).
- KPI strip (updates with the scenario and time): total system cost, redispatch €, curtailed TWh, N/S price spread, CO2, and the selected hour's price.
- Side panel: click a node to see its price duration curve, generation mix, and the market value of PV/battery under A/B/C. Click a line to see its loading time series.
- Investment map: profitability per node per technology under A/B/C (this answers H3 visually).
- "Data und Methode" panel: sources with links, method steps, assumptions, known limits, validation scores, a link to the frozen hypotheses + timestamp. German UI with an EN toggle.
- Responsive and fast: precompute everything, lazy-load time series per scenario, target <3 s first load.

====================================================================
## Repo structure (proposal, adjust in Research Design)
config/, data/raw, data/processed, src/netzfix/{data,network,markets,analysis,viz}, workflow/ (PyPSA-Eur config/overrides), scripts/, tests/, notebooks/ (exploration only), results/, timestamps/, web/, vault/

## Working rules
- Small milestones. Each ends with tests passing, a smoke run, a commit, a Logs/ entry, updated index.md / 00_Home status / Next Steps, and second-brain propagation.
- Cache downloads, retry with backoff. If a source is unavailable or behind a login: stop and tell me. Never fabricate data. The web twin may show only real model output (no mock data, except a clearly labelled dev fixture).
- First end-to-end run (tiny network, 1 week) under ~30 min on my laptop.

## Milestone 0 (now)
Scaffold repo + vault (folders, _CLAUDE.md, index, 00_Home, log.md, first Logs entry, stub notes with "For future agent" summaries), root CLAUDE.md, .gitignore, git init, and the SecondBrain project note. Verify Part 0 and write Prior Art + Research Design + RESEARCH_PLAN.md, then stop for my review.

## Milestone 1 (after approval)
End-to-end skeleton: PyPSA-Eur network clustered to ~30 DE buses, 1 week, real MaStR + atlite + ENTSO-E load. Run designs A and C, export to web/, and get a first map with line loading + nodal prices + a time slider running locally. Log it as Analysis Log #1 (smoke test, not a result).
