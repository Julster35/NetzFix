---
type: plan
date: 2026-11-03
tags: [assumptions, config, core]
ai-first: true
status: "A1-A15 registered 2026-11-03; mirrors config/default.yaml. Demand regionalisation (A12) is the weakest layer."
---

# Assumptions

## For future agent
Every modelling assumption, with an ID that `config/default.yaml` refers to, its default, its source and why. If code and this note disagree, fix one of them in the same commit (`tests/test_config.py` checks the core defaults). Sources marked "to cite" must get a held source or a live URL before the first comparison run.

---

| ID | Assumption | Default | Source / reason | Conf. |
|---|---|---|---|---|
| A1 | Base year (fleet, demand, prices) | 2024 | Brief; latest full year with published redispatch data | stated |
| A2 | Weather year | 2024 | Brief; consistent with A1 | stated |
| A3 | Geography | DE+LU detailed; AT, BE, CH, CZ, DK, FR, NL, NO, PL, SE one bus each | DE-LU is one bidding zone; neighbours of DE-LU | high |
| A4 | Network source | PyPSA-Eur v2026.09.0 `base_network: osm`, OSM archive version pinned at download | [[Prior Art]], [[Xiong et al 2025]] | stated |
| A5 | Spatial resolution | 30 buses (smoke) → 50 / 100 / 200+ | Brief; [[Network Clustering]] | stated |
| A6 | Line rating | `s_max_pu = 0.7` (sens. 0.6 / 0.8) | n-1 proxy; also the PyPSA-Eur default ([[N-1 Security Proxy]]) | stated |
| A7 | Power flow | linear DC, lossless | [[DC Power Flow]] | high |
| A8 | Time resolution | 3 h, one week (smoke) → representative weeks → full hourly 2024 | Brief; runtime | stated |
| A9 | Zone maps | DE2 = BZR config 2; DE5 = BZR config 14; digitised to NUTS3 | [[ENTSO-E 2025 BZR Report]] p. 6-8; digitisation method open (O4) | medium |
| A10 | Redispatch compensation | cost-based: up paid at marginal cost, down refunds avoided marginal cost; RES curtailment compensated (transfer, not resource cost) | German practice; [[Cost-Based Redispatch Compensation]]; legal source to hold | medium |
| A11 | Redispatch pool / frictions | open (O1) | Decides H1 ([[Research Design#Why A and C differ at all]]) | - |
| A12 | Demand regionalisation | ENTSO-E hourly DE-LU load × static NUTS3 shares (DemandRegio/FfE if accessible, else population + industrial employment) | **Weakest layer**: no hourly nodal demand is published | medium |
| A13 | Cross-border | fixed historical 2024 hourly physical net exchange per border (ENTSO-E), identical in A/B/C | Isolates intra-DE design effects; ignores loop flows through neighbours | medium |
| A14 | Fuel & CO2 prices | 2024 monthly/daily averages, cited (to cite: EEX/ICE via a public source, EU ETS) | to cite | - |
| A15 | Investment cost & WACC | DEA catalogue or PyPSA technology-data (pinned); WACC [to decide] | to cite | - |
| A16 | Demand | inelastic, no lost load (VoLL as slack only, cost reported) | Standard; same as [[Knoerr Bichler Dobos 2025]] (p. 10) | stated |

## Playground v0 (added 2026-11-03, see [[Decision Log]] "Re-scope")
| ID | Assumption | Default | Source / reason | Conf. |
|---|---|---|---|---|
| A12 v0 | Demand regionalisation | SMARD hourly DE load × bus share; share = municipal population (GISCO LAU 2024 `POP_2024`, 10,978 municipalities, sum 84.67 M) at each municipality's representative point, attached to the nearest bus. Alternative kept in code: NUTS3 population (Eurostat 1 Jan 2024, 83.46 M) split over bus Voronoi cells by area | No nodal demand published; industry not located (weakest layer). The two population totals differ (reference date/census basis); only shares are used | medium |
| A17 | Grid as is | DE buses of the largest AC-connected component of OSM v0.7 (780 of 785 DE buses); transformers x = 0.1 p.u. (PyPSA-Eur default) | `src/netzfix/network/grid.py` | stated |
| A18 | Border (v0, superseded 2026-11-03) | 45 border points (41 AC lines, 4 HVDC); SMARD residual split pro rata to capacity | Simplest closure without ENTSO-E flows | medium |
| A18 v1 | Neighbours | each AC neighbour's own OSM v0.7 grid Kron-reduced onto its border substations + one hub per grid component (bus nearest the component centroid); 60 equivalent lines without thermal limit; real cross-border lines kept with their r, x, s_nom. Measured hourly 2024 physical flow per country ([[Energy-Charts]]) injected at the hub(s); HVDC share at the German converter, split by capacity where a country has both (DK). Loop flows between neighbours (third-country paths) not modelled | Julien: "roughly model these outside connections without modelling the whole country". One copper-plate node per country produced ~4 GW fake transit through NL | medium |
| A21b | Domestic gap | SMARD load + pumped load - generation - measured physical import (15.8 TWh in 2024) = unmetered domestic supply, spread over buses like demand | SMARD generation series do not add up to its load; the gap is domestic, not at the border | medium |
| A19 | Fleet as is | MaStR export 2026-11-03; a unit counts in month m of 2024 if operating at that month-end (commissioned, not finally decommissioned, not temporarily shut down); ≥ 10 MW individual, smaller aggregated per bus × technology; nearest substation (ties → lower voltage) | Julien's granularity choice; monthly fleet because lignite/coal retired and solar grew during 2024 | medium |
| A19a | Unit location | own MaStR coordinates > powerplantmatching v0.9.1 coordinates matched by MaStR number > municipality (8-digit key → GISCO LAU point) > district (5-digit key → mean of its municipalities) | The public export has no coordinates for most large plants | medium |
| A19b | Offshore wind attachment | nearest bus ≥ 380 kV | Offshore connections land at extra-high voltage; nearest-bus put 4.9 GW on 220 kV stubs near Emden | medium |
| A19c | Carrier mapping MaStR → SMARD | Verbrennung: Braunkohle → lignite, Steinkohle → hard_coal, Erdgas → gas, rest (Mineralöl, andere Gase, Abfall, Wärme, Wasserstoff) → other_conventional; Geothermie/Klärschlamm/Druckentspannung/Solarthermie → other_renewable, Grubengas → other_conventional; storage: Pumpspeicher, Batterie, rest → other_storage (idle) | SMARD category definitions not yet read from a held source | medium |
| A20 | Behaviour as is | unit output = MW active that month × national hourly 2024 capacity factor of its technology (SMARD ÷ MaStR capacity active that month); batteries idle (no 2024 operation data) | No regional weather in v0 (ERA5 needs CDS login) | medium |
| A21 | Balancing | keep 2024 net import (SMARD load + pumped load − generation); scenario edits absorbed pro rata by lignite, hard coal, gas, other conventional; remainder at the border, reported | Playground default; no merit order yet | medium |
| A23 | Redispatch line margin | 0.933 × s_nom on real lines (v2, calibrated 2026-11-03 to the 2024 market + reserve redispatch volume, 24,565 GWh; v1 was 0.942; [[Validation]]); 1.0 and 0.7 kept as options | One fitted parameter; tests T1, T4, T5 pass, T2, T3 fail | medium |
| A22 | Stochastic modifiers | AR(1) multiplicative noise; two-state Markov outages; parameters are user inputs, never shipped as data | Julien: "simulation based on known distributions" | high |
| A19d | Offshore landing points | MaStR connection point → TSO platform code → OSM HVDC export cable (nearest offshore end to the platform group's centroid; farms without code: nearest cable end within 15 km) → cable's onshore point → nearest ≥ 380 kV bus. Replaces A19b for 7.1 GW of the 2024 fleet | Reconstructed from data 2026-11-03; v1 put 5.1 GW on one Emden bus | medium |
| A24 | Weather cutout | ERA5 2024 (atlite 0.7.0) for Germany only: box = DE NUTS3 land ∪ MaStR offshore wind units, + 0.25° margin, snapped to the 0.25° grid (x 5.25-15.5 °E, y 47.0-55.75 °N); features wind, influx, temperature | Neighbours run on measured border flows, so they need no weather; box from data, not typed in ([[ERA5 and atlite]]) | high |
| A25 | Redispatch selection rule | `cost_based`: per hour least selection cost; conventional up/down at the TSO-published average costs, renewable curtailment at the calculated EE price (minimum factor 10); 2024 values Jan-Sep 222.00 / -142.23 / 575.70, Oct-Dec 181.10 / -130.40 / 325.8 €/MWh (`config/default.yaml` `redispatch:`). v0-v2 used `min_volume` | § 13 Abs. 1 S. 2 and Abs. 1a EnWG ([[EnWG 13 13a Redispatch]]), [[BNetzA 2020 Mindestfaktor-Festlegung]], [[netztransparenz Kalkulatorische Preise]]. Not modelled: switching, grid reserve units, countertrading, < 100 kW rule, unit-specific costs | stated (rule, prices) / medium (uniform conventional cost) |
| A26 | Behaviour of large thermal plants | replay actual 2024 output per production unit from ENTSO-E TR 16.1.A (130 units → 65 plants → 178 MaStR assets; link via EIC + powerplantmatching, conflicts by federal state → control area (A26b, `config` `entsoe_units.tso_by_nuts1`), site radius 30 km, name fallback ≥ 90); remaining conventional assets follow SMARD minus replayed output over residual capacity. Replaces A20 for these units | Real behaviour instead of national average; [[ENTSO-E Transparency]] | stated (data) / medium (link heuristics, A26b state→TSO mapping) |
| A27 | Regional wind / solar profiles | ERA5 2024 → atlite 0.7.0 capacity factors per cell (Vestas V112 3 MW onshore, Vestas V164 7 MW offshore, CSi latitude-optimal PV); per bus = capacity-weighted over its units' cells; national total scaled to SMARD hourly; solar −1 h, wind hour-mean alignment. Replaces the national profile (A20) for these carriers | Regional weather drives line loading; SMARD scaling keeps totals and removes ERA5 level bias ([[ERA5 and atlite]]) | high (method) / medium (turbine and panel choice; only shape matters) |
