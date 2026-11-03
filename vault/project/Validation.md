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

### 2026-11-03 - Playground v0 "as is" 2024 vs published figures (descriptive check, not a comparison result)
- Script `scripts/validate_2024.py`, output `results/validation_2024/summary.json`, `redispatch_by_month.csv`, `unresolved_branches.csv`; commit at run `379ace7`. Baseline playground (no edits), full year 2024, keep-trade balancing.
- Reference figures from the held [[BNetzA BKartA 2025 Monitoringbericht]] (PDF pages): congestion management 2024 ~30,320 GWh (p. 23); net import 64.9 − 37.6 = 27.3 TWh (p. 23); TSO circuit length 38.4 thousand km (p. 18); peak load 75.8 GW on 15 Jan 2024 11:30-11:45 (p. 18).

| Check | Model | Real 2024 | Reading |
|---|---|---|---|
| TSO circuit length | 34,201 km (380 kV 22,822; 220 kV 11,379) | 38,400 km | −11%: plausible (cross-border segments, offshore cables, dropped stubs missing) `high` |
| Peak load | 75.51 GW, 15 Jan 2024 11:00 (hourly) | 75.8 GW, 15 Jan 11:30-11:45 (quarter-hour) | matches `high` |
| Net import | 40.9 TWh (SMARD load + pumped load − generation) | 27.3 TWh (commercial) | **model +13.6 TWh**: SMARD generation series do not cover all generation; the gap enters at the borders as artificial import (~1.5 GW mean) `high` (size), `medium` (cause) |
| Generation per technology | equals SMARD by construction | – | not a test |
| Redispatch volume (up + down), lines ≤ 100% | 7.53 TWh (up 3.76, down 1.22 + curtail 2.55); 10.9 GWh unresolved in 275 h | ~30.3 TWh | 25% of real |
| Redispatch volume, lines ≤ 70% (n-1 proxy) | 21.37 TWh (up 10.68, down 3.12 + curtail 7.56); 145.7 GWh unresolved in 1,545 h | ~30.3 TWh | 70% of real |
| Seasonality of redispatch | Jan 1.9 / Feb 1.5 / Dec 1.3 TWh vs Jun 0.09 TWh (≤ 100%) | monthly 2024 not held | winter-heavy, as expected from wind `medium` |

- **Reading:** the grid model produces congestion of the right order of magnitude. Our redispatch is a minimum-volume lower bound and leaves out n-1 contingency analysis, countertrading (in the BNetzA total, p. 23), possibly measures for 110 kV distribution-grid congestion (whether the total includes them is not stated on p. 23), forecast errors and regional weather. So staying below 30.3 TWh is expected; 21.4 TWh at the 70% proxy is a reasonable bracket. `medium`
- **Unresolved overloads:** almost all at 70% sit on one 220 kV line near the Austrian border (`way/41642831-220`, 11.3°E 47.6°N, 1,533 h). Likely cause: fixed border injections that our redispatch cannot change. `speculation` until checked.
- **Not checked (needs ENTSO-E token):** physical flows per border, plant-level output, prices. The Monitoringbericht's per-border physical flows (Abbildung 66, p. 135) are a chart without numbers in the PDF text.

### 2026-11-03 - v1: neighbour equivalents + measured border flows (descriptive check)
- Same script `scripts/validate_2024.py`, commit at run `bed649b`; outputs in `results/validation_2024/` (v0 kept as `summary_v0_capacity_split.json`, `redispatch_by_month_v0.csv`, `unresolved_branches_v0.csv`). Change vs v0: [[Decision Log]] "Neighbours as Kron-reduced equivalents" ([[Assumptions]] A18 v1, A21b).

| | v0 (capacity split) | v1 (equivalents + measured flows) | Real 2024 |
|---|---|---|---|
| Net import at the borders | 40.9 TWh | 25.14 TWh ([[Energy-Charts]]) | 25.1 physical / 27.3 commercial (Monitoringbericht p. 23) |
| Domestic unmetered gap | 0 | 15.76 TWh (spread like demand) | – |
| Line-hours > 100% before redispatch | 13,843 | 17,912 | – |
| Redispatch up + down, ≤ 100% | 7.53 TWh | **17.83 TWh** (up 8.91, down 2.90 + curtail 6.01); 71.7 GWh unresolved in 417 h | ~30.3 TWh |
| Redispatch up + down, ≤ 70% | 21.37 TWh | **71.37 TWh** (up 35.68, down 14.19 + curtail 21.49); 975 GWh unresolved in 3,750 h | ~30.3 TWh |
| Monthly (≤ 100%), GWh | Jan 1,916 … Dec 1,273 | Jan 2,475, Feb 1,553, Aug 1,092, Nov 3,400, **Dec 7,032**; Jun 37 | monthly 2024 not held |

- **Reading:** with measured border flows the real volume lies between the two line limits: ≤ 100% gives 59% of it, a flat 70% on every line gives 235%. A uniform 0.7 n-1 proxy is too strict for operations (real operators use line-specific margins, dynamic line rating, curative measures, and reserve plants). `medium`
- **Unresolved at 70%:** concentrated on a few 220 kV lines near the Austrian border (`merged_relation/3943784-220+1` 2,978 h; AT border lines `way/125690613-220`, `way/125690616-220` ~1,100 h each; `way/1293441399-220`, `way/1293441403-220`, `way/73306291-220` ~700 h). Measured AT flows are fixed and cannot be redispatched in our model; the OSM voltage/rating of this corridor is unchecked. `speculation` until checked.
- **December 2024** dominates (7.0 TWh at ≤ 100%). Plausible given winter wind and the Q4 2024 cost spike reported in secondary sources (not held). `speculation`
- **Next:** calibrate one line-margin factor between 0.7 and 1.0 so that annual redispatch matches 30.3 TWh, then check the monthly pattern and the regional split out of sample. Label it as calibration (one parameter, one target).
