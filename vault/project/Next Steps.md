---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-03, end of session. Julien re-scoped to a playground first ([[Decision Log]] "Re-scope"). The playground runs with neighbours as Kron equivalents, measured border flows, a redispatch operator and a calibrated line margin (0.933, [[Validation]] v2). Tests T1, T4, T5 pass and T2 (curtailment mix), T3 (Q4 share) fail. The A/B/C market-design work and the hypothesis freeze wait until [[Validation]] passes or Julien accepts the failures in the [[Decision Log]].

> [!todo] Resume here (2026-11-04)
> **Julien (before or at the start of the session):**
> - [ ] Copernicus CDS key: register at https://cds.climate.copernicus.eu, copy the token from https://cds.climate.copernicus.eu/how-to-api into `C:\Users\julie\.cdsapirc` (two lines: `url: https://cds.climate.copernicus.eu/api` and `key: <token>`); accept the ERA5 single-levels licence at the bottom of the dataset's download form. Do not paste the token into chat.
> - [ ] Reconnect the chair VPN so `ssh jufr@10.86.177.11` works again (it timed out on 2026-11-03).
> - [ ] Decide what comes first: (a) priority/cost-based redispatch rule (O1) or (b) regional weather (ERA5).
> - [ ] Optional: ENTSO-E API token into `.env` (U2); open the playground and give UI feedback.
>
> **Claude:**
> - [ ] Check that `.cdsapirc` works (without printing it), then fetch ERA5 2024 for DE + neighbours (on the server if reachable) and build per-bus wind/solar capacity factors with atlite.
> - [ ] Pre-register the next calibration run (v3) in [[Validation]] before running it.

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
