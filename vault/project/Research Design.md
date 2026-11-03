---
type: plan
date: 2026-11-03
tags: [research-design, method, core]
ai-first: true
status: "Draft for Julien's review (2026-11-03). No model code yet. The key risk is flagged in §3: in a linear model, A only differs from C through redispatch frictions, so the friction definition must be pre-registered."
---

# Research Design

## For future agent
This is the full plan for answering the [[Research Question]], written on 2026-11-03 before any model code or data download. Core idea: build one open-data German grid model (PyPSA-Eur OSM network, MaStR units, atlite profiles, ENTSO-E load, base year 2024) and run three market designs on it: A uniform + redispatch, B zonal + redispatch, C nodal. Compare total system cost, prices and per-node market values, after [[Validation]] against 2024 data and under the frozen [[Hypotheses]]. Section 3 explains why the **redispatch friction assumptions decide H1** and must be fixed before any comparison.

---

## 1. Scope
- **Question type:** short-run operational comparison of market designs on the **2024 German system** (fleet, demand, weather, fuel prices of 2024). Investment response is only assessed via market values of hypothetical marginal units (H3), not by re-optimising the fleet (optional extension).
- **Geography:** DE (+LU, same bidding zone) at transmission level (220/380 kV + HVDC from OSM), neighbours aggregated to one bus per country ([[Assumptions]] A3).
- **Not in scope:** distribution grid, ancillary-service markets, intraday, strategic bidding, demand response, reserve procurement, operational security beyond the `s_max_pu` proxy ([[N-1 Security Proxy]]).
- **Research model, not an operational twin.** The web twin visualises model output only.

## 2. Model pipeline
```
PyPSA-Eur v2026.09.0 (pinned)        NetzFix (src/netzfix)
  OSM base network  ──► simplified ──► clustered (DE: N buses, neighbours: 1 bus each)
                                             │
  MaStR units (open-mastr, bulk)  ──► data/  ├─► attach units to buses (nearest substation in cluster)
  ERA5 2024 + atlite             ──► data/  ├─► wind/PV p_max_pu per bus, weighted by MaStR capacity
  ENTSO-E 2024 load DE-LU         ──► data/  ├─► regionalised to buses (A12)
  ENTSO-E cross-border flows 2024 ──► data/  ├─► fixed net exchange per border per hour (A13)
  fuel + CO2 prices 2024 (cited)  ──► data/  └─► marginal costs per unit
                                             │
                          markets/  A uniform+RD │ B zonal+RD (DE2, DE5) │ C nodal LOPF
                                             │
                     analysis/  KPIs, market values, validation │ viz/ export_web.py ─► web/public/data
```
PyPSA-Eur is used for what it does well (network build, simplification, clustering, possibly cutouts). Its own load/powerplant attachment for DE is replaced by ours (MaStR, ENTSO-E 2024), because PyPSA-Eur's default demand and fleet years differ from 2024 ([[Prior Art#5. What NetzFix writes itself (gap analysis)]]).

Clustering: start 30 buses (Milestone 1 smoke), research runs 50 → 200+ ([[Network Clustering]]). Zone borders (B) must not cut through a cluster: zone maps are applied to **pre-clustering** buses and clustering is done within zones (`clustering.mode` / busmap per zone). `medium` - to verify in PyPSA-Eur that a custom busmap can enforce this.

## 3. Market designs

### C - Nodal (benchmark)
One-stage linear optimal power flow (LOPF) over all DE buses with DC power flow ([[DC Power Flow]]), line limits `s_max_pu × s_nom`. LMP = dual of the nodal balance ([[Nodal Pricing (LMP)]]). Storage optimised over the horizon.

### A - Uniform + redispatch
1. **Market stage:** DE-LU as one copper-plate bus (all intra-DE lines removed), same fleet, same fixed cross-border exchange. Uniform price = dual of the DE balance.
2. **Redispatch stage:** nodal network; market dispatch fixed; up/down redispatch variables per unit within the **redispatch pool**; cost-based compensation ([[Cost-Based Redispatch Compensation]]). Storage: market schedule fixed in the base case (A11).

### B - Zonal + redispatch
Same as A, but the market stage has one bus per zone and inter-zonal capacities. Zone maps: **B-DE2** (BZR config 2, "DE2") and **B-DE5** (BZR config 14, "DE5"), both from the [[ENTSO-E 2025 BZR Report]], digitised onto NUTS3 regions ([[Zonal Pricing and Bidding Zones]]; open decision O4). Inter-zonal capacity rule: open decision O5 (proposal: sum of `s_max_pu × s_nom` of the cutting lines, i.e. NTC-like, documented as optimistic; flow-based with zonal PTDFs as sensitivity).

### Why A and C differ at all
In a deterministic linear model where **every** unit can be redispatched in both directions at its own marginal cost, the redispatch stage of A reproduces the nodal optimum exactly: total resource cost A = C. The PyPSA example shows this (301 k€ = 301 k€; [[Prior Art#PyPSA redispatch example (read 2026-11-03, docs.pypsa.org)]]). `stated` for the example, `high` in general.

So the A-vs-C (and B-vs-C) cost gap in any linear model comes **only** from redispatch frictions, e.g.:
- a restricted redispatch pool (in reality: units ≥ 100 kW under Redispatch 2.0, RES curtailed last via the BNetzA minimum factors, storage and most demand not in the pool);
- costs of curtailing RES (lost subsidy paid as compensation, CO2-free energy replaced by fossil);
- unit commitment / must-run (Knörr et al. use MILP UC: [[Knoerr Bichler Dobos 2025]] p. 18);
- stage-1 storage schedules that are wrong for the grid and cannot be corrected.

**Consequence for the bet:** H1's answer is mostly determined by which frictions the model contains. They must be (1) chosen from documented German rules, (2) calibrated against observed 2024 redispatch volumes and costs in [[Validation]], and (3) fixed in [[Hypotheses]] before any A/B/C run. Proposal (open decision O1): base case = pool and RES priority per German rules + storage schedule fixed + linear (no UC); sensitivity = UC on a representative-week subset. `high`

### Total system cost (metric for H1)
Proposal (to freeze in [[Hypotheses]]): annual **resource cost** of the final feasible dispatch in DE-LU = Σ (fuel + CO2 + variable O&M) of all units + cost of lost load (should be 0) + value of curtailed RES at 0 €/MWh resource cost (curtailment shows up as fossil replacement). Cross-border exchange fixed and identical across designs, so its cost cancels. **Not** consumer payments, which are reported separately (consumer cost north vs south). `high`

## 4. Outputs per design (each run)
Total system cost; node/zone prices (hourly series + means); RES curtailment (MWh); redispatch volume (MWh up/down) and cost (€); congestion rent; CO2 (t); consumer cost north vs south (€ and €/MWh, north/south per A9); hourly line loading (%). Written to `results/<run_id>/` (CSV/Parquet) + the solved network `.nc` (git-ignored). Each result cites script + file + commit in the [[Analysis Log]].

## 5. Investment question (H3)
For each DE bus and design, the **market value** of a small hypothetical unit ([[Market Value of a Unit]]):
- PV, onshore wind: Σ_t price_t × CF_t (atlite profile at that bus) → €/MWh and €/MW/yr. Price-taker assumption (unit small enough not to move prices).
- 4h battery: perfect-foresight price-taker arbitrage on that bus's price series (round-trip efficiency cited).
- Gas peaker (OCGT): Σ_t max(price_t − SRMC_t, 0).
Compare with annualised CAPEX + fixed O&M from a cited catalogue (DEA technology catalogue or PyPSA `technology-data`, version pinned; WACC an assumption A15). Profitability map per technology × design. Under A, the market value is the **uniform price only**: cost-based redispatch pays no margin (A10), which is the German rule. `high`

## 6. Validation (gate before any comparison)
See [[Validation]]. Modelled A-design uniform price vs actual 2024 DE-LU day-ahead price (correlation, MAE, duration curve); generation mix by carrier vs ENTSO-E/SMARD 2024; redispatch volume and curtailment vs BNetzA 2024 (order of magnitude; the brief's anchor is ~€3 bn/yr congestion management, to be replaced by the held 2024 figure); then A/B/C cost ratios vs [[Knoerr Bichler Dobos 2025]] Table 3 with differences explained (different target year, network, fleet, UC, frictions).

## 7. Sensitivities (all reported against H1-H3)
`s_max_pu` 0.6 / 0.7 / 0.8; cluster size (e.g. 50 / 100 / 200); CO2 and gas price (±, cited ranges); with/without SuedLink (not in operation in 2024 - "with" means adding it as a counterfactual HVDC link, parameters cited); redispatch friction variants (O1); zone map DE2 vs DE5.

## 8. Cross-validation with the BZR data
[[BZR dataset]]: compare the spatial pattern of our nodal prices (C) with ENTSO-E's published nodal prices (rank correlation of mean price by region; different target year and climate year, so pattern not level); compare the DE5 zone assignment. A full second network from BZR input files is a stretch goal (no coordinates, no unit mapping).

## 9. Repo structure
```
config/            default.yaml + scenarios/*.yaml (every value = an assumption ID)
workflow/          PyPSA-Eur config overrides (config.netzfix.yaml) + README; PyPSA-Eur cloned to workflow/pypsa-eur (git-ignored, pinned tag)
data/raw/          downloads (git-ignored); data/MANIFEST.csv (url, access date, sha256)
data/processed/    derived tables (git-ignored except *.small.csv)
src/netzfix/data/      downloaders (retry + backoff + cache + MANIFEST row) and processors
src/netzfix/network/   load PyPSA-Eur clustered network, attach units/load/profiles/exchange
src/netzfix/markets/   design A, B, C; redispatch stage; zone maps
src/netzfix/analysis/  KPIs, market values, validation metrics
src/netzfix/viz/       export_web.py (GeoJSON + compact time series + KPIs)
scripts/           CLI entry points (run_scenario.py, seal_anchor.py)
tests/             pytest (unit tests on toy networks with known answers + smoke)
results/           per-run outputs (networks/*.nc git-ignored)
timestamps/        OpenTimestamps anchors
web/               Vite + TypeScript + MapLibre + deck.gl
vault/             this vault
```

## 10. Toy-network tests (before real data)
A 3-bus network with one binding line, where uniform price, LMPs, redispatch volume and cost can be computed by hand. Tests assert: (i) C = A when the pool is unrestricted and costs are marginal (the PyPSA example property), (ii) A > C when the pool is restricted, (iii) LMP difference across the binding line = its shadow price × PTDF. These guard the market engine against sign and bookkeeping errors. `high`

## 11. Phasing
See `RESEARCH_PLAN.md` (Milestones 0-7) and [[Next Steps]].
