---
type: plan
date: 2026-11-03
tags: [todo, next-steps]
ai-first: true
---

# Next Steps

## For future agent
Ordered actions as of 2026-11-03 evening. Julien re-scoped to a playground first ([[Decision Log]] "Re-scope"); Playground v0 runs ([[Playground]]). The A/B/C market-design work and the hypothesis freeze wait until the playground is validated. Open decisions O1-O8 ([[Open Questions]]) are still open but not blocking.

> [!todo] Resume here (status 2026-11-03)
> - **Julien:** open the playground (`uv run netzfix serve` → http://127.0.0.1:8765) and give feedback; Claude could not test the UI visually (Chrome extension not connected).
> - **Logins for v1 (Julien):** ENTSO-E API token into `.env` (U2); Copernicus CDS key for ERA5 (U1).

## Playground v1 (proposed order)
1. ~~Connection voltage from the BNetzA Kraftwerksliste~~ checked 2026-11-03: it only says "Hoechstspannung" (220 or 380 kV), so it cannot place Karlsruhe (1.7 GW at a 220 kV node, max loading 3.95) ([[Marktstammdatenregister#BNetzA Kraftwerksliste (checked 2026-11-03)]]). Remaining options: OSM `power=plant` / substation topology near each plant, or TSO grid maps; or accept as a documented artefact.
2. **Regional weather:** atlite + ERA5 2024 capacity factors per bus (needs CDS key) instead of national profiles.
3. **ENTSO-E (needs token):** per-unit generation > 100 MW (replay real plant output instead of pro-rata), cross-border physical flows per border (replace the capacity split).
4. **Merit-order behaviour** for conventional plants with cited 2024 fuel and CO2 prices (A14), as an alternative to replay.
5. **Monte Carlo runs** in the UI (N seeds → overload probability per line).
6. **Better demand:** DemandRegio / industry (U4); DE/EN toggle in the UI.
7. **Validation of flows:** compare overloaded corridors with published redispatch (netztransparenz) before quoting any congestion number.

## Later
- Market designs A and C on the playground network (Milestone 2), then B, validation, hypothesis freeze, comparisons ([[Research Design]]).
- Download the BNetzA 2024 congestion-management report by hand (U3).
