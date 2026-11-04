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

