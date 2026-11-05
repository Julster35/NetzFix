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

### 2026-11-03 - Calibration of the line margin: PRE-REGISTRATION (written before any calibration run)
Julien (2026-11-03): "can you go ahead with the calibration and then test?" Model state: v1 (neighbour equivalents + measured flows), commit of this entry.

- **Calibrated parameter (one):** line margin `alpha`; redispatch keeps every real line (German and cross-border; not the fictitious equivalents) at or below `alpha * s_nom`. Grid alpha = 0.70, 0.75, ..., 1.00 (7 full-year runs, `jobs/calibrate.sh` on the chair server, `scripts/calibrate_margin.py`).
- **Target (the only number used for fitting):** annual redispatch volume up + down = **24,565 GWh** = adjusted feed-in of market plants 22,777 GWh (= 14,454 down + 8,322 up) + reserve plants 1,788 GWh, 2024 ([[SMARD 2025 Netzengpassmanagement 2024]]). Countertrading (5,739 GWh) is excluded because the model fixes cross-border exchange at measured values.
- **alpha\*:** linear interpolation of the annual volume between the two bracketing grid points; then one more full-year run at alpha\* (rounded to 3 decimals) for the tests. If the target lies outside the grid range, report that and do not extrapolate.
- **Tests at alpha\* (not used for fitting), fixed now:**
  - T1 renewables curtailment: real 9,374 GWh; pass if model within ±35% (6,093-12,655 GWh).
  - T2 curtailment mix among offshore wind / onshore wind / solar: real 4,562 / 3,384 / 1,389 GWh (shares 48.9 / 36.2 / 14.9%); pass if every model share is within ±15 percentage points.
  - T3 Q4 share: real Q4 2024 total measures 10,424 of 30,304 GWh (34.4%; includes countertrading and reserve); pass if model Q4 share of up + down within ±10 pp.
  - T4 upward by fuel: real gas 4,151 and hard coal 3,792 GWh are the two largest; pass if the model's two largest upward carriers are gas and hard coal (any order).
  - T5 renewables share of downward redispatch: real 9,374 / 14,454 = 64.9%; pass if model within ±15 pp.
- Attribution to technologies: a bus's curtailment / upward / downward volume is split over technologies in proportion to their output / headroom / output at that bus and hour (`scripts/calibrate_margin.py`, smoke-tested on one week: sums match).
- Whatever the outcome, all five tests are reported. Known handicaps stated in advance: national (not regional) weather profiles; minimum-volume instead of cost-ordered redispatch, so T4 depends only on headroom; offshore wind attached at 380 kV landing points.

### 2026-11-03 - Calibration of the line margin: RESULTS
- Runs: Slurm array **5597** on the chair server (alpha 0.70-0.90; code = `git archive` of `794dd32`, `commit_at_run` empty there because the server copy has no `.git`; file `CODE_COMMIT` = 794dd32) and the laptop (alpha 0.95, 1.00, 0.942; code unchanged since 794dd32). Files `results/calibration/alpha_*.json`, `report.json`; scripts `scripts/calibrate_margin.py`, `scripts/calibration_report.py`. Server tasks took 5-16 min each.
- Grid (annual up + down, GWh): 0.70 → 71,366; 0.75 → 58,028; 0.80 → 47,664; 0.85 → 39,009; 0.90 → 30,657; 0.95 → 23,349; 1.00 → 17,826. Monotone.
- **alpha\* = 0.942** (interpolated between 0.90 and 0.95, as pre-registered). Run at 0.942: 24,386 GWh vs target 24,565 (−0.7%); unresolved 126 GWh.

| Test (pre-registered) | Model at 0.942 | Real 2024 | Verdict |
|---|---|---|---|
| T1 renewables curtailment | 8,195 GWh | 9,374 GWh | **pass** (−12.6%) |
| T2 curtailment mix offshore / onshore / solar | 15.6 / 68.2 / 16.2% | 48.9 / 36.3 / 14.9% | **fail** (offshore −33 pp, onshore +32 pp; solar passes) |
| T3 Q4 share of annual volume | 57.5% | 34.4% | **fail** (+23 pp) |
| T4 two largest upward carriers | gas 5,319, hard coal 3,502 GWh | gas 4,151, hard coal 3,792 GWh | **pass** |
| T5 renewables share of downward | 67.2% | 64.9% | **pass** |

- **3 of 5 pass.** The grid model with one fitted parameter reproduces the total volume, the amount of renewables curtailment, the conventional fuels ramped up, and the up/down composition.
- **T2 (offshore vs onshore) fails.** Hypotheses, not tested: (a) offshore wind attaches at the 380 kV landing substations and the offshore connection systems (platforms, export cables) are not in the OSM set, so congestion on the offshore connections and around the landing points is missing; (b) minimum-volume redispatch is indifferent between technologies, while real practice follows cost and minimum factors; (c) all wind follows one national profile. `speculation`
- **T3 (Q4) fails at every margin** (44-60% across the grid), so it is structural, not caused by the calibration. Hypotheses, not tested: winter interaction of the measured border flows with the national wind profile; real operators also use countertrading (in the real Q4 total) and forecasts. `speculation`
- **Consequence:** the playground's redispatch default becomes "lines ≤ 94.2% (calibrated)". The failures are documented limits; do not quote seasonal or offshore-vs-onshore redispatch results from the model yet.

### 2026-11-03 - Calibration v2 after offshore reconstruction: PRE-REGISTRATION (before any v2 run)
- **Why a v2:** T2 (curtailment mix) failed in v1. Julien asked whether the offshore connections can be reverse-engineered from data. They were: MaStR connection points name the TSO platform (`L-155-<farm>-<platform>-...`), OSM has the HVDC export cables (Overpass, ODbL); farms are matched to cables purely by geography, and each cable's onshore end gives the 380 kV landing bus (`src/netzfix/data/offshore.py`; [[Assumptions]] A19d). 7.1 GW of the 2024 offshore fleet now lands at its cable's substation; 2.1 GW (Baltic, AC-connected) keeps the nearest 380 kV bus.
- **This is a second attempt after seeing a failed test.** Both v1 and v2 results are reported; v2 is not a confirmation of anything that v1 already passed.
- **Unchanged:** target 24,565 GWh, grid alpha 0.70-1.00, interpolation rule, tests T1-T5 with the same pass rules. Server job array as before; alpha\* run afterwards.
- Known residual issues stated in advance: DWKA (266 MW) is a geographic tie between DolWin2 and DolWin6 (assigned DolWin2); BorWin5's onshore end is 16 km from the nearest bus; export-cable capacity limits are not modelled (only the landing point).

### 2026-11-03 - Calibration v2: RESULTS (second attempt, after offshore reconstruction)
- Runs on the laptop (chair server unreachable: SSH timeout, VPN presumably down), code at `68cfb1b` + report `--dir` option; files `results/calibration_v2/`.
- Grid (GWh): 0.70 → 68,012; 0.75 → 54,996; 0.80 → 45,123; 0.85 → 36,968; 0.90 → 29,120; 0.95 → 22,257; 1.00 → 17,106. **alpha\* = 0.933**; run at 0.933: 24,478 GWh vs 24,565.

| Test | v1 (alpha 0.942) | v2 (alpha 0.933) | Real |
|---|---|---|---|
| T1 curtailment | 8,195 pass | 7,864 pass | 9,374 |
| T2 offshore / onshore / solar | 15.6 / 68.2 / 16.2% fail | **6.8 / 75.0 / 18.2% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 57.5% fail | 58.8% fail | 34.4% |
| T4 top-2 upward | gas, hard coal pass | gas 5,423, hard coal 3,500 pass | gas 4,151, hard coal 3,792 |
| T5 renewables share of down | 67.2% pass | 64.3% pass | 64.9% |

- **Reading:** hypothesis (a) for T2 (wrong landing points) is **rejected**: with data-based landings offshore curtailment falls further. Remaining explanation `medium`: the redispatch *rule*. Minimum-volume redispatch picks the most effective units per MW; real operators follow the cost-based order and minimum factors and curtail offshore wind heavily. This is the friction/rule question O1 of the market-design part, not a grid error. Export-cable limits and regional weather remain untested.
- **Decision (Claude, reversible):** keep v2 (data-based landings) as the model; redispatch default margin 0.933.

### 2026-11-04 - Calibration v3 with the legal redispatch rule: PRE-REGISTRATION (before any v3 run)
Julien (2026-11-04): "it is realy important that we build redispatch like it happens in real life with regulations" and "yes go ahead and restest vs our data".
- **Why a v3:** T2 (curtailment mix) failed in v1 and v2; v2 rejected the landing-point explanation and left the redispatch *rule* as the likely cause. **This is a third attempt after seeing failed tests**; v1, v2 and v3 are all reported.
- **Only change vs v2:** the selection rule. `min_volume` → `cost_based` ([[Assumptions]] A25; `src/netzfix/sim/redispatch.py`, `CostRule`): per hour minimise c_up·up + c_down·down_conventional + p_ee·curtailment subject to the same line limits and balance. Prices are the TSO-published 2024 values ([[netztransparenz Kalkulatorische Preise]]): Jan-Sep (valid from 2023-10-01) c_up 222.00, c_down -142.23, p_ee 575.70 €/MWh; Oct-Dec (from 2024-10-01) 181.10, -130.40, 325.8. Legal basis [[EnWG 13 13a Redispatch]] (§ 13 Abs. 1 S. 2, Abs. 1a), minimum factor 10 ([[BNetzA 2020 Mindestfaktor-Festlegung]]). Toy-network tests with hand-computed answers: `tests/test_redispatch_cost.py`.
- **Unchanged:** network and assets of v2 (data-based offshore landings), national weather profiles (ERA5 is downloading, not used in v3), measured border flows, target **24,565 GWh**, grid alpha 0.70, 0.75, ..., 1.00, linear interpolation for alpha\*, one run at alpha\* (3 decimals), tests **T1-T5 with the same pass rules** as the 2026-11-03 pre-registration. Results go to `results/calibration_v3/`.
- **Also reported (descriptive, not a test):** the selection cost in M€. It is not comparable with real payments (calculated prices are selection prices, not compensation).
- **Known handicaps stated in advance:** no grid-reserve units in the asset list (the target still includes 1,788 GWh reserve; reserve price p_nr unused); conventional plants all at the same average cost, so among conventional plants the choice is still by grid effectiveness and T4 stays headroom-driven; no countertrading, no grid switching, no < 100 kW last-resort rule, no n-1 analysis; national weather (T3 handicap unchanged).
- **Expectation (not a test, written down so it can be wrong):** if the rule is the cause, renewables curtailment falls in total (T1 may fail low) and its offshore share rises.

### 2026-11-04 - Calibration v3: implementation bug found in the first grid (job 5735), rerun pre-registered
- Grid job **5735** (code `ff8fdcd`, files kept in `results/calibration_v3_bug5735/`) gave **lower** volumes than v2's minimum-volume rule (e.g. alpha 0.90: 19,381 vs 29,120 GWh) and **more unresolved overload** (245 vs 185 GWh), which a cost rule cannot do if line limits are binding. Looked at: the grid volumes, unresolved overloads and the interpolated alpha\* (0.850). **Not looked at: T1-T5** (no run at alpha\*, no test evaluation).
- Cause: the overload slack penalty (1e4 per MW, sized for the min-volume objective with unit weights) is cheaper than relieving 1 MW through weakly coupled plants at real prices (up to ~800 €/MWh / PTDF sensitivity), so the LP left overloads instead of redispatching. This contradicts the rule: § 13 Abs. 1 EnWG makes removing the danger mandatory; cost only selects among suitable measures.
- Fix (commit after this entry): `PENALTY_COST = 1e8` for the cost-based rule (min-volume rule unchanged); toy test `test_cost_rule_resolves_overload_even_when_relief_is_expensive` (fails with the old penalty: 10 MW unresolved; passes with the fix).
- **Rerun = v3 as pre-registered above, unchanged in every other respect** (grid, target, interpolation, T1-T5 pass rules). Both the buggy grid and the rerun are reported.
- **Second fix (2026-11-04):** rerun grid **5742** (penalty 1e8) failed in every task: HiGHS numerical failure ("Status 0: Not Set"), no results. Penalty set to **1e6** €/MW (covers sensitivities down to ~1e-3 for renewable pairs). Smoke test on the laptop, alpha 0.85, full year (smoke test, not a result; only runtime and unresolved overload looked at): 383 s, unresolved 290 GWh in 1,602 h, equal to v2's min-volume run at 0.85 (290 GWh, 1,601 h) → remaining overload is infeasible for any rule, not left by the cost rule. Grid rerun follows, otherwise unchanged.

### 2026-11-04 - Calibration v3 (legal cost-based redispatch rule): RESULTS
- Runs: chair server, grid job **5749** (code `abf9c80`, server `CODE_COMMIT`), alpha\* run job **5756**; files `results/calibration_v3/alpha_*.json`, `report.json`; scripts `scripts/calibrate_margin.py` (`rule: cost_based`), `scripts/calibration_report.py --dir results/calibration_v3 --test 0.944`. 2-11 min per task.
- Grid (GWh, unresolved in brackets): 0.70 → 73,403 (976); 0.75 → 58,764 (673); 0.80 → 47,771 (450); 0.85 → 38,965 (290); 0.90 → 30,729 (185); 0.95 → 23,656 (118); 1.00 → 18,162 (72). Volumes are above v2 at every alpha (as a cost rule must be) and unresolved overload equals v2. **alpha\* = 0.944**; run at 0.944: 24,438 GWh vs 24,565 (up 12,219; conventional down 7,355; curtailment 4,864; unresolved 124). Selection cost 3,490 M€ (descriptive; selection prices, not payments).

| Test | v1 (min-vol, 0.942) | v2 (min-vol, 0.933) | **v3 (cost rule, 0.944)** | Real 2024 |
|---|---|---|---|---|
| T1 curtailment (GWh) | 8,195 pass | 7,864 pass | **4,864 fail** | 9,374 (pass 6,093-12,655) |
| T2 offshore / onshore / solar | 15.6 / 68.2 / 16.2% fail | 6.8 / 75.0 / 18.2% fail | **6.8 / 73.5 / 19.7% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 57.5% fail | 58.8% fail | **57.5% fail** (Q1 6,600, Q2 730, Q3 3,044, Q4 14,063 GWh) | 34.4% |
| T4 top-2 upward | gas, hard coal pass | gas, hard coal pass | **gas 5,303, hard coal 3,630 pass** | gas 4,151, hard coal 3,792 |
| T5 renewables share of down | 67.2% pass | 64.3% pass | **39.8% fail** | 64.9% |

- Curtailment by carrier (GWh): onshore 3,122, solar 835, biomass 434, offshore 290, hydro 169. Conventional down: lignite 2,908, gas 2,207, hard coal 1,585, other 656.
- **Reading (`high` for the numbers, `medium` for the causes):**
  - The pre-registered expectation held only half: renewables curtailment fell (T1 now fails low), but the **offshore share did not rise** (6.8% under both rules). So **the selection rule is not the cause of the T2 failure** either. With the landing points (v2) and the rule (v3) both rejected, the offshore gap must sit in what the model offers the operator: in our grid offshore wind is almost never behind a binding constraint. Candidates, untested: congestion close to the coast that our OSM grid / line margin does not reproduce (export cables, 220 kV coastal grid, TenneT north), and the national offshore profile (A20).
  - **T5 / T1 failing under the legal rule** says the model has **too much conventional output available for downward redispatch near the bottlenecks** (2.9 TWh lignite down). Likely cause `medium`: behaviour A20 runs every conventional plant at the national hourly capacity factor, so northern and eastern plants always produce something to reduce, while in reality many are off or must-run (CHP heat, system services; § 13 Abs. 3 "netztechnisch erforderliches Minimum"). The min-volume rule hid this because it ignored cost.
  - T3 unchanged by the rule: structural, as before.
- **Report against the tests:** v3 passes 1 of 5 (T4); v2 passed 3 of 5. The legal rule is the right rule to keep, but it exposes that the plant dispatch (A20) is the weakest layer for redispatch. **No change of model default until Julien decides** (see [[Next Steps]]): config `redispatch.rule` stays `cost_based`, the UI still uses the v2 margin and the min-volume rule.

### 2026-11-04 - Calibration v4: real 2024 output of large thermal plants: PRE-REGISTRATION (before any v4 run)
Julien (2026-11-04): plants should behave as in real life; "yes go ahead" to replaying ENTSO-E per-unit data.
- **Why a v4:** v3 (legal redispatch rule) showed T1/T5 failing because every conventional plant ran at the national average (A20), giving the operator output to reduce everywhere. **Fourth attempt after seeing failed tests**; v1-v4 are all reported.
- **Only change vs v3:** plant behaviour of large thermal units = **actual 2024 output** ([[Assumptions]] A26; [[ENTSO-E Transparency]] TR 16.1.A, File Library). 130 thermal ENTSO-E units → 65 production units → 178 MaStR assets (118 units linked by EIC via the ENTSO-E unit master file and powerplantmatching v0.9.1, 2 by name ≥ 90; 10 unlinked; conflicts across control areas resolved by the asset's federal state, same-site overlaps merged, assets > 30 km from the plant's median site dropped). Each plant's output is shared over its assets by p_nom (capped at p_nom); gaps ≤ 3 h interpolated, longer gaps = 0; the first local hour (2023-12-31 23:00 UTC) copied from the next. Replayed TWh vs SMARD: lignite 68.6 / 71.0, hard coal 22.9 / 27.3, gas 30.2 / 56.9, other conventional 7.3 / 15.8. All other conventional assets follow the **residual** national profile (SMARD − replayed, clipped at 0; 0.15 TWh hard coal and 0.11 TWh lignite clipped) over the residual capacity. Replayed plants stay dispatchable for redispatch (down to 0, up to p_nom). Tests `tests/test_replay_entsoe.py`.
- **Unchanged:** cost-based redispatch rule and prices (A25, penalty 1e6), network, renewables (national profiles), border flows, target **24,565 GWh**, grid alpha 0.70-1.00, interpolation, run at alpha\*, tests **T1-T5 with the same pass rules**. Results `results/calibration_v4/`.
- **Known handicaps stated in advance:** units that are off still offer their full p_nom as upward headroom (no start-up times or minimum up-time); must-run / CHP heat constraints of the small residual plants not modelled; renewables still national profiles (ERA5 not yet used), so T2/T3 handicaps are unchanged.
- **Expectation (not a test):** conventional downward redispatch falls where plants were really off, so T5 (renewables share of down) and T1 rise compared with v3; T2 and T3 are not expected to change much.

### 2026-11-04 - Calibration v4 (real thermal plant output + legal rule): RESULTS
- Runs: chair server grid job **5758** (code `ac4e34d`), 2-12 min per task; files `results/calibration_v4/`. Grid (GWh, unresolved): 0.70 → 75,722 (976); 0.75 → 60,766 (673); 0.80 → 49,533 (450); 0.85 → 40,480 (290); 0.90 → 31,982 (185); 0.95 → 24,598 (118); 1.00 → 18,869 (72). **alpha\* = 0.950** (interpolation gives 0.9503, rounded to 3 decimals = grid point 0.950, so the grid run serves as the alpha\* run). 24,598 GWh vs 24,565: up 12,299, conventional down 7,568, curtailment 4,731. Selection cost 3,421 M€ (descriptive).

| Test | v2 (min-vol) | v3 (cost rule) | **v4 (cost rule + real plants)** | Real 2024 |
|---|---|---|---|---|
| T1 curtailment (GWh) | 7,864 pass | 4,864 fail | **4,731 fail** | 9,374 |
| T2 offshore / onshore / solar | 6.8 / 75.0 / 18.2% fail | 6.8 / 73.5 / 19.7% fail | **6.8 / 73.7 / 19.4% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 58.8% fail | 57.5% fail | **56.4% fail** | 34.4% |
| T4 top-2 upward | pass | pass | **gas 5,123, hard coal 3,435 pass** | gas 4,151, hard coal 3,792 |
| T5 renewables share of down | 64.3% pass | 39.8% fail | **38.5% fail** | 64.9% |

- Conventional down (GWh): lignite 2,914, gas 2,758, hard coal 1,196, other 700 (sum 7,568; real conventional down = 14,454 − 9,374 = 5,080).
- **Reading:** the pre-registered expectation was **wrong**: real plant output barely changed T1/T5. So "plants that were really off" was not the main reason the cost rule under-curtails renewables. With real output, lignite (which really ran) is still reduced 2.9 TWh. Remaining candidates (`medium`, untested): (1) **uniform average costs**: the published average refund for conventional down (−142 €/MWh in 2024) is far above lignite's real saved cost, so the model finds lignite reductions cheap; real operators price each plant at its own cost (§ 13a Abs. 2) → unit-specific costs; (2) **technical minimum load / must-run** of lignite and CHP (§ 13 Abs. 3 "netztechnisch erforderliches Minimum"), so plants cannot go to 0; (3) regional weather (T2/T3 unchanged as expected).
- v4 passes 1 of 5 (T4). Model default unchanged pending Julien.

### 2026-11-04 - Calibration v5: regional wind and solar weather (ERA5): PRE-REGISTRATION (before any v5 run)
Julien (2026-11-04): agreed order 1. regional weather, 2. plant costs and minimum load, 3. market model.
- **Fifth attempt after seeing failed tests**; v1-v5 all reported.
- **Only change vs v4:** wind onshore, wind offshore and solar use **per-bus capacity factors** from ERA5 2024 ([[Assumptions]] A27; [[ERA5 and atlite]]; `src/netzfix/data/weather_profiles.py`): atlite 0.7.0 (Vestas V112 3 MW onshore, Vestas V164 7 MW offshore, CSi panel latitude-optimal) per ERA5 cell; each bus = capacity-weighted mean over the cells of its MaStR units (Dec-2024 capacity); **national total scaled to SMARD every hour**, so only the regional shape comes from ERA5. Time alignment checked by lag correlation: solar shifted −1 h (0.925 → 0.971 national), wind = mean of hour start/end. Diagnostics before scaling (correlation with SMARD, raw vs SMARD TWh): onshore 0.982, 143.1 vs 112.6; offshore 0.876, 43.4 vs 25.7; solar 0.968, 88.6 vs 63.1. Fallback to the national factor in 1 / 0 / 38 hours. Profiles built on the chair server (code `cc7b916`), cutout `data/raw/era5/DE_2024_era5.nc` (MANIFEST row, sha256 462b77f5…).
- **Unchanged:** A25 cost rule, A26 thermal replay, network, borders, target 24,565 GWh, grid 0.70-1.00, interpolation, tests T1-T5 and pass rules. Results `results/calibration_v5/`.
- **Known handicaps stated in advance:** (1) **SMARD is actual feed-in after curtailment**: the profiles (national and now regional) already lack the energy really curtailed in 2024 (offshore 4,562 GWh, [[SMARD 2025 Netzengpassmanagement 2024]]), so where it was curtailed the model cannot curtail it again; this biases T1 and T2 low in all versions v1-v5 and is **not** changed here; (2) uniform conventional costs and no minimum load (v4 reading); (3) unit-to-cell placement uses the nearest ERA5 cell of the unit's location (municipality centre for 39% of solar capacity).
- **Expectation (not a test):** T3 (Q4 share) moves towards 34% if regional wind patterns drive the winter redispatch; T2 changes little because of handicap (1).

### 2026-11-04 - Calibration v6: available (pre-curtailment) wind and solar: PRE-REGISTRATION (before any v6 run; written while v5 was running, v5 results not yet looked at)
Julien (2026-11-04): "can we work on the fix already".
- **Why:** v5 pre-registration handicap (1): SMARD and all profiles so far are actual feed-in **after** curtailment, so the model cannot curtail what was really curtailed. **Sixth attempt**; v1-v6 all reported.
- **Only change vs v5:** `weather.profile_basis: available` ([[Assumptions]] A28). Per carrier, national available output per hour = max(SMARD actual, k × ERA5 raw), with k set (bisection) so that the year's available energy = SMARD actual + energy curtailed by redispatch in 2024 ([[SMARD 2025 Netzengpassmanagement 2024]]: offshore 4,562, onshore 3,384, solar 1,389 GWh); buses keep ERA5's regional shape. Result (laptop build, `weather_profiles.py`): k = 0.734 / 0.668 / 0.481; available − actual = 3,384 / 4,562 / 1,389 GWh; hours with available below actual 45 / 11 / 1 (clipping at cf 1). Descriptive plausibility check (not a test): the offshore excess by quarter is Q1 683, Q2 1,275, Q3 1,205, Q4 1,399 GWh (real Q4 offshore redispatch 1,812 GWh). Tests `tests/test_available.py` (hand-computed).
- **Consequence stated in advance:** the extra renewable energy enters the pre-redispatch state; the existing balancing (keep trade) lowers dispatchable output pro rata, which roughly removes the real upward redispatch already contained in the replayed thermal output (ENTSO-E is also measured after redispatch), but not plant by plant. A clean pre-redispatch market state is part of the market model (step 3).
- **Unchanged:** A25, A26, A27 shapes, network, borders, target 24,565 GWh, grid, interpolation, T1-T5 and pass rules. Results `results/calibration_v6/`.
- **Expectation (not a test):** T1 and the offshore share in T2 rise compared with v5.

### 2026-11-04 - Calibration v5 (regional ERA5 weather): RESULTS
- Runs: grid job **5776** (code `ccd6323`), alpha\* run via `srun` on the same code before v6 was synced; files `results/calibration_v5/`. Grid (GWh, unresolved): 0.70 → 86,348 (968); 0.75 → 69,771 (666); 0.80 → 56,899 (445); 0.85 → 45,897 (286); 0.90 → 36,062 (182); 0.95 → 27,774 (115); 1.00 → 21,325 (70). **alpha\* = 0.975**; run at 0.975: 24,267 GWh (up 12,134, conventional down 7,461, curtailment 4,672; unresolved 91). Selection cost 3,406 M€.
- Tests: **T1** 4,672 fail; **T2** offshore / onshore / solar 6.6 / 77.0 / 16.4% fail; **T3** Q4 share 54.8% fail (Q1 6,737, Q2 1,013, Q3 3,211, Q4 13,306 GWh); **T4** gas 4,973, hard coal 3,544 pass; **T5** 38.5% fail. 1 of 5.
- **Reading:** regional weather raised the volume at every margin (alpha\* up from 0.950 to 0.975: weather-driven flows are more concentrated) and moved T3 only slightly (56.4 → 54.8%). The pre-registered expectation (T3 towards 34%) did not hold. T2 unchanged, as expected under handicap (1), which v6 addresses.

### 2026-11-04 - Calibration v6 (available pre-curtailment wind/solar): RESULTS
- Runs: grid job **5785** (code `9094571`), alpha\* run via `srun` on the same code; files `results/calibration_v6/`. Grid (GWh, unresolved): 0.70 → 90,294 (969); 0.75 → 73,352 (667); 0.80 → 59,881 (447); 0.85 → 48,381 (287); 0.90 → 38,120 (184); 0.95 → 29,388 (117); 1.00 → 22,483 (73). **alpha\* = 0.985**; run at 0.985: 24,274 GWh (up 12,137, conventional down 6,851, curtailment 5,286; unresolved 84). Selection cost 3,745 M€.

| Test | v4 | v5 | **v6** | Real 2024 |
|---|---|---|---|---|
| T1 curtailment (GWh) | 4,731 fail | 4,672 fail | **5,286 fail** | 9,374 |
| T2 offshore / onshore / solar | 6.8 / 73.7 / 19.4% | 6.6 / 77.0 / 16.4% | **8.4 / 75.5 / 16.1% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 56.4% | 54.8% | **54.8% fail** | 34.4% |
| T4 top-2 upward | pass | pass | **gas 4,963, hard coal 3,603 pass** | gas, hard coal |
| T5 renewables share of down | 38.5% | 38.5% | **43.5% fail** | 64.9% |

- Curtailment by carrier (GWh): onshore 3,578, solar 762, **offshore 399** (real 4,562), biomass 393, hydro 141.
- **Reading:** the pre-registered direction held (T1 +13%, T5 +5 pp, offshore share +1.8 pp) but the effect is small. The decisive number: the model makes 4.56 TWh more offshore energy available and curtails only 0.4 TWh of offshore in total. **Offshore wind is almost never behind a binding constraint in our grid**, even with the real energy and weather. The remaining T2 gap is therefore in the **network near the coast / the landing points** (export cable and onshore connection capacities, 220/380 kV coastal grid in the OSM model, or how TSOs actually curtail offshore under § 13 rather than via the cost rule), not in plant behaviour, weather or the selection rule (v2-v6 have now tested landing points, rule, real thermal output, weather and available energy). `medium`
- v6 passes 1 of 5 (T4). Model default kept at v6 settings pending Julien.

### 2026-11-04 - Calibration v7: minimum load of thermal units: PRE-REGISTRATION (before any v7 run)
Julien (2026-11-04): "yes" to step 2 (plant costs, minimum load), "go on".
- **Why:** v3-v6 fail T1/T5 because the model turns down too much conventional output (v6: 6.9 TWh vs real ≈ 5.1 TWh). A pre-run sanity calculation with held prices showed unit-specific fuel costs would make lignite reductions *cheaper*, not dearer (lignite ≈ 72 €/MWh vs gas CC ≈ 83 €/MWh in 2024), so the v4 hypothesis about uniform costs is weakened; technical minimum load is the remaining physical limit. Unit-specific costs wait for a held 2024 hard-coal price. **Seventh attempt**; v1-v7 all reported.
- **Only change vs v6:** [[Assumptions]] A31: 394 individual thermal units get a minimum load (VDE 2012 row of [[DIW 2013 DD68 Schroeder et al]] Table 27, midpoints: lignite old 0.55 / new 0.40, hard coal old 0.325 / new 0.20, gas CC 0.40, gas GT 0.35; gas steam and other conventional none). Technology from MaStR `Technologie` and commissioning year (`src/netzfix/markets/plants.py`, `data/processed/unit_technology_2024.csv`). Redispatch may lower a running unit only to its minimum load (no shut-down within the hour); units below their minimum load in an hour offer no downward room; upward room unchanged. Engine `down_bus`; test `tests/test_min_load.py` (hand-computed).
- **Input description (not a result):** downward room over the year falls from 162.0 to 85.9 TWh (lignite 61.7 → 14.1, hard coal 26.7 → 14.3, gas 57.4 → 41.3, other unchanged 16.2).
- **Unchanged:** A25-A28 (cost rule with published averages, thermal replay, regional available wind/solar), target 24,565 GWh, grid 0.70-1.00, interpolation, T1-T5 and pass rules. Results `results/calibration_v7/`.
- **Known handicaps:** no CHP heat must-run beyond minimum load; no shut-down option (real TSOs can order units off); minimum loads are technology midpoints, not unit data.
- **Expectation (not a test):** conventional down falls, renewables curtailment and T5 rise; the volume per margin rises, so alpha\* moves up.

### 2026-11-04 - Calibration v7 (minimum load of thermal units): RESULTS
- Runs: grid job **5810** (code `9eed501`), alpha\* run via `srun` on the same code; files `results/calibration_v7/`. Grid (GWh, unresolved): 0.70 → 88,271 (986); 0.75 → 72,540 (680); 0.80 → 59,981 (457); 0.85 → 49,041 (296); 0.90 → 38,835 (191); 0.95 → 30,252 (122); 1.00 → 23,313 (76). **alpha\* = 0.991**; run at 0.991: 24,433 GWh (up 12,216, conventional down 5,860, curtailment 6,357; unresolved 83). Selection cost 4,301 M€. 394 units with minimum load.

| Test | v2 (min-vol) | v6 | **v7 (min load)** | Real 2024 |
|---|---|---|---|---|
| T1 curtailment (GWh) | 7,864 pass | 5,286 fail | **6,357 pass** (band 6,093-12,655) | 9,374 |
| T2 offshore / onshore / solar | 6.8 / 75.0 / 18.2% fail | 8.4 / 75.5 / 16.1% fail | **9.7 / 75.3 / 15.0% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 58.8% fail | 54.8% fail | **54.9% fail** | 34.4% |
| T4 top-2 upward | pass | pass | **gas 4,936, hard coal 3,666 pass** | gas 4,151, hard coal 3,792 |
| T5 renewables share of down | 64.3% pass | 43.5% fail | **52.0% pass** (band 49.9-79.9) | 64.9% |

- Conventional down 5,860 GWh (lignite 754, gas 2,937, hard coal 989, other 1,180) vs real 5,080 (= 14,454 − 9,374); lignite down fell from 2,486 (v6) to 754.
- **Reading:** the pre-registered expectation held: minimum load was the main missing physical limit behind T1/T5 under the legal cost rule. **v7 passes 3 of 5 (T1, T4, T5)** with the legal redispatch rule, real thermal output, regional weather and available renewables, i.e. it matches v2's pass count with a realistic operator instead of a minimum-volume one. T1 and T5 pass near the lower edge of their bands. Remaining failures: **T2 (offshore share; network near the coast, see v6 reading)** and **T3 (Q4 share; unchanged across v3-v7)**.
- **Decision (Claude, reversible, for Julien to confirm):** v7 settings become the model default (`redispatch.rule` cost_based, line margin 0.991, A26-A28, A31). The UI still shows the v2 margin and the min-volume rule until updated.

### 2026-11-04 - v7 diagnostics and Calibration v8 (grid-reserve units): PRE-REGISTRATION (before any v8 run)
Julien (2026-11-04): "do nr. 1-3" (coast grid / T2, Q4 / T3, CHP must-run).
- **v7 diagnostics** (descriptive, `scripts/diagnose_v7.py`, `results/diagnostics/v7_alpha_0.991.json`, code `1244b60`+script commit): monthly volume is dominated by December (8,773 GWh = 36% of the year) and November (4,110). The most binding branches are 220 kV lines with up to **3.1 × s_nom** before redispatch (Karlsruhe 49.02 N 8.29 E; Austrian border 48.28 N 13.06 E; Lübeck, Wilhelmshaven, Hamburg 220 kV). Offshore landing buses have PTDF up to 0.56 on the top branches, but onshore wind next to those lines is as or more effective at the same calculated price, so the cost rule curtails onshore. ENTSO-E 13.1.A internal redispatch for DE sums to only 1.7-6.3 TWh (vs 30.3 TWh) → not usable as a yardstick.
- **Finding behind v8:** 12.4 GW of units with a reserve / grid-security status in the BNetzA Kraftwerksliste (held; status as of 2026-06) are ordinary market assets in the model. 24 of them have measured 2024 output (ENTSO-E) that shows several were in the market during 2024 (e.g. Irsching 4/5 all year; Staudinger 5, Scholven B, RDK 7 stop during the year), so the 2026 status cannot be applied to them. **36 units (3.13 GW) without a measurement were running on the national profile as if in the market.**
- **Only change vs v7 ([[Assumptions]] A32):** those 36 unmeasured reserve-status units have no market output and offer only upward redispatch, priced at the calculated grid-reserve price p_nr (476.50 / 476.9 €/MWh, [[netztransparenz Kalkulatorische Preise]]; § 13 Abs. 1c EnWG, [[EnWG 13 13a Redispatch]]); their capacity leaves the national-profile fleet. Measured units keep their 2024 replay. LP gains a reserve block (`redispatch(..., reserve=...)`), toy test `test_reserve_used_only_after_market_plants` (hand-computed).
- **Unchanged:** everything else of v7 (A25-A28, A31), target 24,565 GWh (it includes 1,788 GWh reserve), grid, interpolation, T1-T5. The reserve volume counts in up + down. Results `results/calibration_v8/`.
- **Expectation (not a test):** small effect on T1/T5; slightly less winter volume near Karlsruhe (RDK 4S no longer injects).


### 2026-11-05 - Calibration v8 (grid-reserve units): RESULT
- Runs: chair server grid job **5819** (code `9a33e0f`, server `CODE_COMMIT`), alpha\* run via `srun` on the same code (2026-11-05); files `results/calibration_v8/alpha_*.json`, `report.json`; script `scripts/calibration_report.py --dir results/calibration_v8 --test 0.997`. Grid (GWh, unresolved): 0.70 → 89,311 (983); 0.75 → 73,507 (678); 0.80 → 60,928 (455); 0.85 → 50,011 (294); 0.90 → 39,800 (190); 0.95 → 31,090 (122); 1.00 → 24,080 (76). **alpha\* = 0.997** (grid interpolation 0.9965, rounded to 3 decimals); run at 0.997: 24,462 GWh (up from market plants 11,742 + **grid reserve 489**, conventional down 6,042, curtailment 6,189; unresolved 78 GWh in 347 h). Selection cost 4,345 M€ (descriptive). 36 reserve units (3,129 MW) without market output; 24 measured units kept as replay. `stated` (our result files)
- Note on `report.json`: after the alpha\* run is added, the report re-interpolates with that point as a bracket (v8: 0.9963; v7: 0.9901; v6: 0.9830), so the stored `alpha_star` differs slightly from the alpha that was run. The run alpha is the grid-only interpolation, rounded as pre-registered. Not a deviation.

| Test | v6 | v7 (min load) | **v8 (grid reserve)** | Real 2024 |
|---|---|---|---|---|
| T1 curtailment (GWh) | 5,286 fail | 6,357 pass | **6,189 pass** (band 6,093-12,655) | 9,374 |
| T2 offshore / onshore / solar | 8.4 / 75.5 / 16.1% fail | 9.7 / 75.3 / 15.0% fail | **9.5 / 75.5 / 15.0% fail** | 48.9 / 36.3 / 14.9% |
| T3 Q4 share | 54.8% fail | 54.9% fail | **54.8% fail** | 34.4% |
| T4 top-2 upward | pass | gas 4,936, hard coal 3,666 pass | **gas 4,300, hard coal 3,902 pass** | gas 4,151, hard coal 3,792 |
| T5 renewables share of down | 43.5% fail | 52.0% pass | **50.6% pass** (band 49.9-79.9) | 64.9% |

- Conventional down 6,042 GWh (gas 3,039, hard coal 1,002, lignite 778, other 1,224) vs real 5,080. Quarter volume (GWh): Q1 6,960, Q2 1,116, Q3 2,970, Q4 13,415.
- **Reading:** the pre-registered expectation held: a small effect on T1/T5, and the pass/fail pattern is unchanged (**3 of 5: T1, T4, T5**). Upward gas is now closer to the real figure (4,300 vs 4,151, v7 4,936), because the reserve block takes over part of the upward volume. The reserve supplies 489 GWh against 1,788 GWh in the real target (27%). T1 (6,189 vs lower bound 6,093) and T5 (50.6% vs 49.9%) both sit closer to the lower edge of their bands than in v7, so a further change could flip them to fail. T2 and T3 are unchanged: the reserve units do not touch the coastal-grid or December problems.
- **Status:** v8 is a realism fix (A32) with no test change; whether it replaces v7 as the default is for Julien to decide (Claude's suggestion: yes, since A32 follows § 13 Abs. 1c EnWG and the test results are equivalent).

### 2026-11-05 - T6 (yardstick: TSO redispatch measures 2024): PRE-REGISTRATION (before any T6 number is computed)
Julien (2026-11-05): "ok then do 1 and 2" (2 = netztransparenz yardstick).
- **Data (real, R):** netztransparenz.de "Redispatch" Download CSV, 2024, one file per month in UTC, `data/raw/netztransparenz/redispatch/redispatch_2024_MM_UTC.csv` (12 MANIFEST rows, downloaded 2026-11-05 by `src/netzfix/data/netztransparenz_redispatch.py`), [[netztransparenz Redispatch]]. Per measure and German day: start, end, reason, direction, mean/max MW, energy MWh, instructing TSO, plant or area, primary-energy class. Exact duplicate rows across month files are dropped (30 of 17,390). Only counts per category were looked at before this entry (reasons, directions, classes, TSOs, plant names); **no volume was summed by month, day, TSO or plant.**
- **Selection R:** reasons `Strombedingter Redispatch` and `Strom- und Spannungsbedingter RD`; both directions; `BETROFFENE_ANLAGE != "Börse"` (the exchange leg has no location). Excluded: countertrades DE-DK1/DK2/NO2 (cross-border, not modelled), voltage-only redispatch (no AC voltage in the model), all test and trial runs of reserve units. Volume = `GESAMTE_ARBEIT_MWH`; each row counts on the Europe/Berlin date of its start + half its duration; days outside 2024 dropped.
- **Model (M):** v8 default ([[Decision Log]] 2026-11-05), margin 0.997, same redispatch call as `scripts/calibrate_margin.py` (cost rule, minimum load, grid reserve). Volume = up + reserve up + conventional down + curtailment per bus and hour, summed per Europe/Berlin date.
- **Tests (thresholds frozen here):**
  - **T6a monthly shape:** total-variation distance between M and R monthly volume shares, ½·Σ|m_i − r_i| ≤ **0.15**. Overlaps T3 (Q4 share, model already known to be 54.8%).
  - **T6b daily timing:** Spearman rank correlation of daily volumes, M vs R (366 days) ≥ **0.50**.
  - **T6c control area:** share of volume by TSO; R by `ANWEISENDER_UENB`, M by the federal state of each bus mapped to a TSO with A26b (`entsoe_units.tso_by_nuts1`; approximate, since Hesse, Lower Saxony and Rhineland-Palatinate are split between two TSOs in reality). Pass if each of the four shares is within **±0.10**.
  - **T6d offshore (descriptive, no pass/fail):** share of R's downward `Erneuerbar` volume at entries named `OWP*` (offshore connection points); a cross-check of the 48.9% offshore share used in T2 (BNetzA Monitoringbericht).
- **Script:** `scripts/t6_yardstick.py` (to be written; result to `results/calibration_v8/t6.json`). The same test is applied to every later version without changing selection or thresholds; a change needs a new pre-registration entry.
- Expectation (not a test): T6a fails (December-heavy model, see T3); T6c may pass, since the TSO split depends less on the 220 kV artefacts than the location within a control area.

### 2026-11-05 - T6 on v8: RESULT
- Run: laptop, `scripts/t6_yardstick.py --alpha 0.997 --out results/calibration_v8` at HEAD `d1cdb4a` plus uncommitted working tree (new script and downloader; the model and redispatch code path is unchanged since `9a33e0f`); files `results/calibration_v8/t6.json`, `t6_daily.csv`. Model total 24,462 GWh (= the v8 alpha\* run, reproduced on the laptop); 89 GWh of model volume sits on buses outside the NUTS-1 map (neighbour equivalents) and is left out of T6c. Real selection: 14,678 measures, **17,654 GWh** (lower than the 24,565 GWh calibration target, which also counts countertrade, reserve and voltage measures). `stated` (our result files)

| Month (GWh) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Model v8 | 3,288 | 2,586 | 1,086 | 560 | 292 | 264 | 389 | 1,591 | 990 | 520 | 4,110 | 8,786 |
| Real (selection R) | 2,632 | 1,513 | 841 | 847 | 1,673 | 695 | 459 | 617 | 1,585 | 1,652 | 2,067 | 3,074 |

| Test | Model v8 | Real 2024 | Threshold | Result |
|---|---|---|---|---|
| T6a monthly shape (TVD) | 0.286 | - | ≤ 0.15 | **fail** |
| T6b daily Spearman | 0.483 | - | ≥ 0.50 | **fail** |
| T6c 50Hertz / Amprion / TenneT / TransnetBW | 17.7 / 25.0 / 33.5 / **23.8%** | 16.3 / 28.5 / 42.7 / **12.5%** | ±0.10 each | **fail** (TransnetBW +11.3 pp; TenneT −9.1 pp, inside) |
| T6d offshore (`OWP*`) share of real RES down (descriptive) | - | 59.9% (4,183 of 6,981 GWh) | - | consistent with T2's 48.9% being mostly offshore |

- **Reading:** as expected, T6a fails: the model puts 36% of the year in December (real 17%) and almost nothing in May (292 vs 1,673 GWh). Unlike the expectation, **T6c fails**, because of TransnetBW: the model has twice the real share in Baden-Württemberg. This matches the v7 diagnostics, where the Karlsruhe (RDK, 1.70 GW on a 220 kV bus) and Mannheim (GKM, 1.96 GW on a 220 kV bus) branches are among the most binding. T6b misses its threshold narrowly. The real data confirm that offshore wind (`OWP*` connection points) carries most of the renewable curtailment (T2).

### 2026-11-05 - Network diagnosis Karlsruhe / Mannheim (descriptive, no run)
- **GKM (Mannheim, 1.96 GW) feeds 220 kV in 2024:** "den im GKM erzeugten Kraftwerksstrom von der 220-kV- auf die verlustärmere 380-kV-Spannungsebene transformieren" (future UW Mannheim) [[TransnetBW 2021 Newsletter Rhein-Neckar Karlsruhe]] p. 4; that substation belongs to the Weinheim-Karlsruhe project with target commissioning 2031 [[TransnetBW 2025 Projektbroschuere Weinheim-Karlsruhe]] p. 1-2. `stated` → the model's 220 kV attachment of GKM is **correct**.
- **Corridor:** Weinheim - Mannheim - Rheinau - Altlußheim - Daxlanden is "eine bestehende 220-Kilovolt (kV)-Freileitung", reinforced to 380 kV "So soll Überlastungen besser vorgebeugt werden" (same brochure); the Daxlanden area is 220 kV today [[TransnetBW 2023 Erlaeuterungsbericht UW Daxlanden]] p. 9-10. `stated`
- **RDK (Karlsruhe, 1.70 GW):** connection voltage not found in any held or online source (Kraftwerksliste/MaStR: "Höchstspannung" only). Keep 220 kV (`medium`: the Daxlanden area is 220 kV).
- **Onyx (Wilhelmshaven, 726 MW):** MaStR connection point "380-kV Anschluss KW Wilhelmshaven (Onyx)" at UW Fedderwarden; model attaches it at 220 kV → a real attachment error. `stated` (MaStR export 2026-11-03)
- **Reading:** the TransnetBW excess in T6c (23.8% vs 12.5%) is **not** an attachment artefact at GKM. With measured plant output (A26) and a real 220 kV corridor, the remaining candidates are the corridor's rating (all 220 kV circuits at 491.6 MVA, PyPSA-Eur default conductor 2×240/40) and operational measures the model lacks (topology switching, temperature-dependent ratings). `medium` - not tested.

### 2026-11-05 - Calibration v9 (TSO line ratings + stated connection voltage): PRE-REGISTRATION (before any v9 run)
Julien (2026-11-05): "ok then do 1 and 2", "yes look for it" (TSO static grid model), "ok we wont publish the twin and only use it for our reserach" ([[Decision Log]]).
- **Changes vs v8 (only these):** [[Assumptions]] **A34** (`line_ratings.source: jao`): 566 of 1,060 German AC lines (62% of line km) get ratings from 512 matched TSO circuits of the [[JAO Core Static Grid Model]]; rated MVA 1,105,912 → 1,160,168 (+4.9%); median ratio 1.00 (220 kV quartiles 0.78 / 1.00 / 1.05). Corridor examples: Maximiliansau-Daxlanden 492 → 953 MVA, Lübeck-Siems 492 → 362 MVA. Unmatched: 177 circuits without Imax (mostly Amprion: DLRmax only), 79 tripod legs incomplete, 75 length mismatches, 58 no bus near an end, 39 no path. **A35** (`connection_kv.enabled`): Onyx (726 MW) 220 → 380 kV (0.8 km). Matching method and its tuning (name lookup, tripods, length rule, lower bound) were developed on match diagnostics only (statuses, ratings of named lines); **no redispatch run with A34/A35 was looked at** except the smoke test below.
- **Smoke test (not a result):** one week 2024-12-09 + 168 h at margin 0.997, laptop, working tree: 2,743 GWh up+down (v8 same week 2,120), unresolved 13.0 GWh. Only used to check that the code runs.
- **Unchanged:** everything else of v8 (A25-A28, A31, A32; CHP must-run A33 off), target 24,565 GWh, alpha grid 0.70-1.00, interpolation and rounding, T1-T5, **T6 with the thresholds frozen 2026-11-05**. Results `results/calibration_v9/` (+ `t6.json`).
- **Expectation (not a test):** T6c TransnetBW share falls (corridor ratings up to ~2x); alpha\* moves (direction unclear: some lines tighter, e.g. Lübeck, AT border); T2/T3 unclear.

### 2026-11-05 - Calibration v9: RESULT (target outside the grid range)
- Runs: chair server grid job **5966** (code `c4ec936`, server `CODE_COMMIT`); files `results/calibration_v9/alpha_*.json`. 4-25 min per task. `stated` (our result files)
- Grid (GWh up + down, unresolved): 0.70 → 116,364 (1,773); 0.75 → 97,391 (1,212); 0.80 → 80,702 (845); 0.85 → 66,425 (607); 0.90 → 54,063 (438); 0.95 → 43,407 (309); **1.00 → 34,501 (212)**. v8 at 1.00: 24,080 (76).
- **The target (24,565 GWh) lies below the whole grid.** Per the pre-registered rule ("If the target lies outside the grid range, report that and do not extrapolate") there is **no alpha\*, no alpha\* run and no T1-T6 test for v9**.
- Descriptive, at the grid point 1.00 (not a test): up 16,534 + reserve 717; curtailment 8,422 (real 9,374; v8 6,086); conventional down 8,829 (real 5,080; v8 5,954); Q4 share 51.3% (v8 55.0%); selection cost 5,993 M€.
- **Reading:** with the TSOs' own ratings (Imax = Fixed / DLRmin / lowest season), the model network is tighter than with the OSM defaults, although the total rated MVA rose 4.9%: the binding lines got lower ratings on balance. Even at 100% of rating the model needs 40% more redispatch than 2024. Candidate reasons (`medium`, untested): (1) **DLRmin is the lower band** of temperature-dependent ratings; redispatch peaks in cold, windy winter hours when DLR is near its upper band; (2) operational measures absent from the model: phase-shifting transformers (listed in the JAO "Remedial Actions" sheet), topology switching, curative redispatch (temporary post-fault overload); (3) 177 circuits without a usable Imax keep OSM defaults (mostly Amprion).
- **Status:** v8 stays the model default (v9 has no calibrated margin). `line_ratings.source` and `connection_kv.enabled` were switched on for this run and are set back to the v8 values (osm / false) in `config/default.yaml` after it (2026-11-05), so the default stays v8.
