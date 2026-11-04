---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-04, end of session. The 2024 twin now has the legal redispatch rule, real thermal output, regional weather, available renewables and minimum load; calibration v7 passes T1, T4, T5 (line margin 0.991). Remaining failures: T2 (offshore share, a coastal-grid / operational question) and T3 (Q4 share, December-dominated, partly 220 kV artefacts). The market model (step 3) and A/B/C wait until validation is accepted by Julien.

> [!todo] Resume here (2026-11-05)
> **Claude, in order:**
> 1. **Evaluate v8** (grid-reserve units, job 5819 on the chair server, `results/calibration_v8/` there): copy JSONs, `calibration_report.py --dir results/calibration_v8`, run at alpha* (rounded, via `srun`, same code `9a33e0f`), T1-T5 into [[Validation]].
> 2. **v9 = CHP must-run** (A33, code ready, `chp_must_run.enabled: false` → true): pre-register in [[Validation]] first, then run.
> 3. **T3 / 220 kV artefacts:** check the worst branches from `results/diagnostics/v7_alpha_0.991.json` (Karlsruhe 49.02 N 8.29 E up to 3.1×; AT border 48.28 N 13.06 E) against OSM (parallel circuits, missing 380 kV links, wrong attachment) — a network fix is its own pre-registered version.
> 4. **Yardstick:** netztransparenz.de daily per-plant redispatch CSV (public "Download CSV" form, 2024) - **ask Julien before downloading**; then monthly / per-TSO / per-plant comparison (T2, T3) as a new pre-registered test T6.
> 5. **T2 offshore:** look for a held source on how TSOs curtail offshore (TenneT direct control vs DSO-coordinated onshore under Redispatch 2.0).
> 6. Update the UI to the v7 defaults (cost rule, margin 0.991) once Julien confirms.
>
> **Julien:** confirm v7 as default; decide whether the inferred coal price (8.3 €/MWh_th, A29) is acceptable or a data subscription is available at the chair; permission for the netztransparenz download.

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
