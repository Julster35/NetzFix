---
type: concept
date: 2026-11-03
tags: [redispatch, compensation, design-A, design-B]
ai-first: true
---

# Cost-Based Redispatch Compensation

## For future agent
In Germany, units called for redispatch are compensated at cost, not at a market bid: a unit ramped up is paid its costs, a unit ramped down pays back the fuel cost it saved, and curtailed renewables are compensated for lost revenue. So redispatch gives no profit margin. NetzFix's designs A and B use this rule ([[Assumptions]] A10). The legal source is not yet held.

## In the model
- Resource cost (the H1 metric) counts real fuel/CO2/O&M costs of the final dispatch only; compensation payments are transfers, reported separately as "redispatch EUR". `high`
- Redispatch EUR (A, B) = sum(up x marginal cost) - sum(down x marginal cost) + sum(curtailment x compensation rate); the compensation rate for RES (lost market revenue + lost support payment) must come from a held legal source. `medium`
- Which units may be redispatched and in what order (RES last, via the BNetzA minimum factors; `FestlegungMindestfaktoren.pdf` is linked from the BNetzA redispatch page, not yet held) is the friction question O1 ([[Research Design#Why A and C differ at all]]).

## Contrast
- Market-based redispatch (bids) would let units behind congestion earn margins and invites inc-dec gaming; not modelled. `high`
