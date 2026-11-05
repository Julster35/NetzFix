---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-05, end of session. Model default = **v8** (cost rule, min load, grid reserve, margin 0.997; T1/T4/T5 pass, T2/T3 fail). New yardstick **T6** (TSO redispatch measures 2024, netztransparenz) fails on v8: monthly shape, daily timing and TSO split (TransnetBW 23.8% vs 12.5%). **v9** (TSO line ratings from JAO, A34, + stated connection kV, A35) gives 34.5 TWh even at 100% of rating, i.e. no calibrated margin. Agreed plan (Julien, 2026-11-05): add the operators' relief measures as separate pre-registered versions, PSTs first, then weather-dependent ratings, then CHP must-run. The market model (step 3) and A/B/C wait until validation is accepted by Julien.

> [!todo] Resume here (2026-11-06)
> **Claude, in order:**
> 1. **v10 = v9 + phase-shifting transformers.** Data: JAO Core SGM sheets Transformers (PST angle / phase regulation) and Remedial Actions ([[JAO Core Static Grid Model]]). Match German PSTs to OSM transformers; add PST angle variables to the redispatch LP (cost-free, before plants); **toy-network test with a hand-computed answer first** (CLAUDE.md). Pre-register in [[Validation]], then grid + alpha* + T1-T6 on the chair server.
> 2. **v11 = v10 + weather-dependent line ratings** (between DLRmin and DLRmax, hourly from ERA5 temperature/wind). **Blocked on a held source:** IEEE 738 or CIGRE TB 601 (paywalled) - Julien to check JMU library access; otherwise look for an open-access paper stating the heat balance in full. No formula without a held PDF.
> 3. **v12 = CHP must-run** (A33, code ready, `chp_must_run.enabled`).
> 4. **T2 offshore:** held source on how TSOs curtail offshore (TenneT direct control vs Redispatch 2.0). Real data now show offshore connection points carry 59.9% of RES curtailment (T6d).
> 5. Licence of the netztransparenz redispatch CSV (not stated on the page) - check before publishing anything derived.
>
> **Julien:** IEEE 738 / CIGRE TB 601 via the library; coal price A29 (8.3 €/MWh_th inferred) acceptable or a data subscription at the chair.
>
> Done 2026-11-05: v8 evaluated + default; UI on v8 call; netztransparenz data + T6; GKM = 220 kV (TransnetBW PDFs); JAO SGM held; v9 built, run (job 5966), no alpha*.

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
