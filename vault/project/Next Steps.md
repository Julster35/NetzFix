---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-05. The 2024 twin now has the legal redispatch rule, real thermal output, regional weather, available renewables and minimum load; calibration v7 passes T1, T4, T5 (line margin 0.991); v8 (grid-reserve units, A32, margin 0.997) passes the same three, closer to the lower bands of T1/T5. Remaining failures: T2 (offshore share, a coastal-grid / operational question) and T3 (Q4 share, December-dominated, partly 220 kV artefacts). The market model (step 3) and A/B/C wait until validation is accepted by Julien.

> [!todo] Resume here (after 2026-11-05)
> **Claude, in order:**
> 1. ~~Evaluate v8~~ done 2026-11-05: alpha* 0.997, T1/T4/T5 pass, T2/T3 fail ([[Validation]]).
> 2. **v9 = CHP must-run** (A33, code ready, `chp_must_run.enabled: false` → true): pre-register in [[Validation]] first, then run.
> 3. **Network fix (v9-net), waiting for Julien's choice of rule:** evidence 2026-11-05 ([[Validation]] T6, Logs): T6c fails on TransnetBW (23.8% vs 12.5%), consistent with RDK (1.70 GW) and GKM (1.96 GW) on 220 kV buses; Onyx stated 380 kV in MaStR but attached at 220 kV; OSM Mannheim circuits=2 vs cables=12. Sourced rule ready: MaStR-stated kV overrides nearest-bus voltage (moves Onyx only). Open: kV of RDK/GKM (no held source), all-DE OSM cables/circuits check (`src/netzfix/data/osm_line_tags.py`, Overpass 502/429 on 2026-11-05 - retry later).
> 4. ~~Yardstick~~ done 2026-11-05: data downloaded, T6 pre-registered and run on v8 (T6a/b/c fail). Licence of the netztransparenz data still to check.
> 5. **T2 offshore:** look for a held source on how TSOs curtail offshore (TenneT direct control vs DSO-coordinated onshore under Redispatch 2.0).
> 6. ~~Update the UI to the defaults~~ done 2026-11-05: v8 confirmed (Decision Log); server redispatch uses cost rule + min load + reserve, dropdown 0.997.
>
> **Julien:** decide whether the inferred coal price (8.3 €/MWh_th, A29) is acceptable or a data subscription is available at the chair; permission for the netztransparenz download.

## Open problems from calibration v2 (2026-11-03)
1. **T2 curtailment mix fails** (offshore 6.8% vs 48.9% real). Rebuilt landing points did not help ([[Offshore Connections]]). Likely cause: our minimum-volume redispatch picks onshore wind near the bottleneck, while real operators follow the cost / priority order of § 13a EnWG with minimum factors for renewables (`medium`). → redispatch rule with priority weights (needs O1 decision; the weights must come from a held source, not invented).
2. **T3 Q4 share fails** (58.8% vs 34.4%) at every margin. Candidates: national wind profile too uniform across regions (→ regional weather), Dec 2024 dark doldrums + border flows, demand split by population only.
3. **Unresolved overloads** at 220 kV lines near the Austrian border.
4. **Offshore details:** DWKA (266 MW) tie DolWin2 vs DolWin6; BorWin5's onshore route 16 km from a bus in OSM.
5. **Karlsruhe attachment artefact** (1.7 GW at a 220 kV node): Kraftwerksliste cannot fix it; options are OSM plant/substation topology or accepting it as documented.

## Playground v1 (later)
- ENTSO-E (needs token): per-unit generation > 100 MW instead of pro-rata replay.
- Merit-order behaviour for conventional plants with cited 2024 fuel and CO2 prices (A14).
- Monte Carlo runs in the UI (N seeds → overload probability per line).
- Better demand: DemandRegio / industry (U4); DE/EN toggle in the UI.
- Visual test of the UI (Chrome extension).

## Later
- Market designs A and C on the playground network (Milestone 2), then B, hypothesis freeze, comparisons ([[Research Design]]).
- Download the BNetzA 2024 congestion-management report by hand (U3).
