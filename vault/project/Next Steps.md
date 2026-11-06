---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-06 (resume block below supersedes the 2026-11-05 list). Model default = **v8** (cost rule, min load, grid reserve, margin 0.997; T1/T4/T5 pass, T2/T3 fail). New yardstick **T6** (TSO redispatch measures 2024, netztransparenz) fails on v8: monthly shape, daily timing and TSO split (TransnetBW 23.8% vs 12.5%). **v9** (TSO line ratings from JAO, A34, + stated connection kV, A35) gives 34.5 TWh even at 100% of rating, i.e. no calibrated margin. Agreed plan (Julien, 2026-11-05): add the operators' relief measures as separate pre-registered versions, PSTs first, then weather-dependent ratings, then CHP must-run. The market model (step 3) and A/B/C wait until validation is accepted by Julien.

> [!todo] Resume here (after 2026-11-06)
> **Claude, in order:**
> 1. **v10-n1 result** (job 6913, α_c 1.1-2.0, `results/calibration_v10_n1/` on the server): copy, interpolate α_c\*, run `jobs/tests.sh` (T1-T7) at α_c\* with `--n1` (needs a `N1` passthrough in tests.sh), write RESULT in [[Validation]].
> 2. **OOS-2023** (pre-registered): year-parametrise input paths (state.py, assets.py, weather_profiles.py, entsoe_units.py; check v8 α 0.997 still gives 24,462 GWh), build 2023 assets + regional profiles (ERA5 job 6916), compute the 2023 countertrade volume and target, then run every candidate on the server.
> 3. **Market v2:** CHP must-run (A33) as lower bound, renewables bidding at market-premium level (negative prices), storage; then feed market dispatch into flows (design A end to end).
> 4. Soft post-fault slack (Julien's idea): only with a sourced price for post-fault overload.
> 5. v10 phase shifters (JAO), v11 weather-dependent hourly ratings (needs IEEE 738/CIGRE PDF), v12 CHP must-run.
>
> **Julien:** ENTSO-E File Library login for 2023 per-unit output (A26 replay for OOS-2023); ask the colleague what the 120% refers to and which "pricing of overloading" data he meant; commit when happy.
>
> Done 2026-11-06: T7 (BNetzA bottleneck lists) fails on v8; v9b α\* 1.069 / 0.986 (volume explained by ratings, pattern worse); n-1 (A38) built + tested, grid running; market v1 fails V1 r / V2; OOS-2023 pre-registered; twin shows TSO and weather-adjusted max ratings.

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
