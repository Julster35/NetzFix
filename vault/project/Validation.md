---
type: plan
date: 2026-11-03
tags: [validation, gate, core]
ai-first: true
status: "Plan only (2026-11-03). No validation run yet. Gate: no A/B/C comparison result before this note shows pass or accepted failures."
---

# Validation

## For future agent
The model must reproduce the 2024 German system closely enough before any A/B/C comparison result is reported. This note lists the checks, targets and pass rules (proposals, to confirm with Julien) and will record each validation run with script + file + commit. Failures are allowed only if Julien accepts them in the [[Decision Log]].

---

## Checks (proposed pass rules)
| # | Check | Model output | Observed (source) | Proposed pass rule |
|---|---|---|---|---|
| V1 | DE-LU day-ahead price | design A uniform price, hourly 2024 | ENTSO-E / SMARD ([[ENTSO-E Transparency]], [[SMARD]]) | Pearson r ≥ 0.8; MAE reported; duration curve plotted; annual mean within ±15% |
| V2 | Generation mix | annual TWh by carrier, design A market stage | ENTSO-E actual generation per type 2024 | each major carrier (lignite, hard coal, gas, wind on/off, PV, biomass, hydro) within ±20% or ±5 TWh |
| V3 | Large units | hourly output of units > 100 MW | ENTSO-E actual generation per unit | correlation reported per carrier (diagnostic, no pass rule) |
| V4 | Redispatch volume | design A redispatch MWh (up+down) | BNetzA 2024 congestion-management report ([[netztransparenz Redispatch]] for measures) | same order of magnitude (factor ≤ 2) |
| V5 | Redispatch / congestion cost | design A redispatch € | BNetzA 2024 (brief: ~€3 bn/yr; held 2023 report gives quarterly figures - [[BNetzA 2024 Netzengpassmanagement Q4 2023]]) | factor ≤ 2 |
| V6 | RES curtailment | design A curtailed TWh | BNetzA 2024 | factor ≤ 2 |
| V7 | Benchmark ratios | (A−C)/C, (B−C)/C | [[Knoerr Bichler Dobos 2025]] Table 3: 5.19-5.90% | no pass rule; differences explained |

## Runs
(none yet)
