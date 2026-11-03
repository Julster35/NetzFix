---
type: concept
date: 2026-11-03
tags: [investment, market-value, H3]
ai-first: true
---

# Market Value of a Unit

## For future agent
The revenue a small (price-taking) unit would earn from energy prices at a given node, per MWh produced and per MW installed per year. Comparing it with annualised investment cost tells whether the unit would be profitable there. This answers H3 ([[Hypotheses]]).

## Formulas (price-taker)
- Variable RES (PV, onshore wind): MV per MWh = sum_t(p_t * CF_t) / sum_t(CF_t); MV per MW-year = sum_t(p_t * CF_t) over hourly steps. `high`
- Gas peaker (OCGT): sum_t max(p_t - SRMC_t, 0) per MW. `high`
- 4h battery: max sum_t p_t * (discharge_t - charge_t) s.t. state-of-charge dynamics, round-trip efficiency, energy = 4 x power, perfect foresight over the year (an upper bound on real revenue). `high`
- Profitability margin = MV per MW-year - (annuity(CAPEX, WACC, lifetime) + fixed O&M) ([[Assumptions]] A15).

## Caveats
- Price-taker: valid only for small units; a large southern battery would flatten the prices it earns. `high`
- Under A, the price is the uniform price everywhere; cost-based redispatch pays no margin ([[Cost-Based Redispatch Compensation]]). `high`
- Energy-only revenue: no balancing, capacity or redispatch revenue streams.
