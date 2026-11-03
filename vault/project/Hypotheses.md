---
type: plan
date: 2026-11-03
tags: [hypotheses, pre-registration, core]
ai-first: true
status: "DRAFT - not frozen. Open: threshold X, friction base case (O1), north/south definition (O3). Freeze + OpenTimestamps before any A/B/C comparison run."
---

# Hypotheses

## For future agent
These are the three testable predictions from Julien's brief with a **proposed** metric and decision rule. They are a draft (2026-11-03), **not yet frozen**. They must be frozen and sealed with OpenTimestamps (`timestamps/`) before any A/B/C comparison run; the anchor commit goes into the [[Decision Log]]. Bracketed `[…]` items are open decisions for Julien ([[Open Questions]]).

---

## H1 - Cost ordering
**Claim:** total system cost C (nodal) < B (zonal) < A (uniform + redispatch).
- **Metric:** annual resource cost of the final feasible DE-LU dispatch (fuel + CO2 + variable O&M; definition in [[Research Design#Total system cost (metric for H1)]]), same fleet, demand, weather, cross-border exchange in all designs.
- **"Cheaper":** design X is cheaper than Y if `(cost_Y − cost_X) / cost_Y > [X = 0.5%, proposal]` in the base case **and** the sign holds in **every** sensitivity run of [[Research Design#7. Sensitivities (all reported against H1-H3)]].
- **Verdicts:** "supported" (both pairwise orderings cheaper by the rule), "partly supported" (C < A by the rule but B vs A or C vs B not), "not supported" (otherwise), "cannot tell" (sign flips across sensitivities).
- **B** is evaluated per zone map (B-DE2, B-DE5); H1 needs the ordering for [both maps / at least DE5 - decide].
- **Friction base case:** [O1 - to fix before freezing; see [[Research Design#Why A and C differ at all]]].

## H2 - North/south prices
**Claim:** southern nodal prices are systematically higher than northern ones.
- **Metric:** load-weighted annual mean LMP of southern buses minus northern buses (C); same for zones (B).
- **North/South:** [O3 - proposal: the BZR DE2 border].
- **"Systematically":** mean difference > 0 **and** south > north in ≥ [75%] of hours with any binding intra-DE line, in base case and all sensitivities.

## H3 - Southern investment signal
**Claim:** at least one of {battery 4h, PV} is profitable in the south under C or B but not under A.
- **Metric:** market value (€/MW/yr) minus annualised CAPEX + fixed O&M (catalogue + WACC per [[Assumptions]]) per southern bus ([[Market Value of a Unit]]).
- **"Profitable":** margin > 0 at ≥ [1] southern bus(es) [or: at the load-weighted median southern bus - decide] under C or B, and margin ≤ 0 at the same bus under A.
- Onshore wind and gas peaker are reported but not part of H3's test.

## Reporting rule
Report every hypothesis's verdict for the base case and each sensitivity, whatever the result, and compare with [[Knoerr Bichler Dobos 2025]] Table 3.
