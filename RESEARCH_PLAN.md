# NetzFix - Research Plan

Open-data model of the German transmission grid: is total system cost lower under (A) one price zone + redispatch, (B) 2-5 bidding zones + redispatch, or (C) nodal pricing - and do locational prices make southern generation or storage profitable? Plus an interactive web twin.

Full detail lives in the vault: [Research Design](vault/project/Research%20Design.md) · [Hypotheses](vault/project/Hypotheses.md) · [Assumptions](vault/project/Assumptions.md) · [Validation](vault/project/Validation.md) · [Prior Art](vault/project/Prior%20Art.md) · [Open Questions](vault/project/Open%20Questions.md) · [Decision Log](vault/project/Decision%20Log.md).

Status 2026-11-03: Milestone 0 done, waiting for Julien's review.

## Method in five lines
1. Network: PyPSA-Eur **v2026.09.0** OSM grid, DE+LU detailed, neighbours one bus each, clustered (30 → 50 → 200+ buses).
2. Inputs 2024: MaStR fleet, atlite/ERA5 2024 wind+PV, ENTSO-E load (regionalised), fixed historical cross-border exchange, cited fuel/CO2 prices.
3. Designs: C nodal LOPF; A copper-plate market + cost-based redispatch; B zonal market (BZR DE2, DE5) + redispatch.
4. Validate design A against 2024 prices, mix, redispatch volume/cost; compare ratios with Knörr, Bichler, Dobos (2025).
5. Freeze hypotheses (OpenTimestamps) → run A/B/C + sensitivities → report against H1-H3 whatever the result.

**Key risk:** in a linear model, A with fully flexible cost-based redispatch equals C. The A-vs-C gap measures redispatch frictions (restricted pool, RES priority, fixed storage schedules, unit commitment). These must be decided (O1), calibrated, and frozen before the bet is settled.

## Milestones
| # | Milestone | Ends with |
|---|---|---|
| 0 | Scaffold repo + vault, verify prior art, design | ✅ 2026-11-03, review by Julien |
| 1 | End-to-end skeleton: ~30 DE buses, 1 week 2024, real MaStR + atlite + ENTSO-E load; designs A and C; toy-network tests; web export; first local map with line loading, nodal prices, time slider | Analysis Log #1 (smoke test, not a result); run < 30 min on laptop |
| 2 | Full data layers: all of 2024 (3 h → hourly), demand regionalisation, fuel/CO2 prices, cross-border, conventional calibration | data notes complete, MANIFEST complete |
| 3 | Design B (DE2, DE5 zone maps digitised; inter-zonal capacities); redispatch frictions per O1; BZR data downloaded for cross-validation | all three designs run on one week |
| 4 | Validation (V1-V7) at 50+ buses, full year | Validation note passes or Julien accepts failures |
| 5 | **Freeze hypotheses + OpenTimestamps anchor**, then A/B/C base + sensitivities | results logged against H1-H3 |
| 6 | Market values / profitability maps (H3) | H3 verdict |
| 7 | Web twin complete (all views, DE/EN, Data und Methode panel), GitHub Pages | public site (Julien decides) |

## Open decisions (for Julien; details in Open Questions)
O1 redispatch frictions (decides H1) · O2 threshold for "cheaper" (proposal 0.5%) · O3 north/south line (proposal DE2 border) · O4 zone-map digitisation · O5 inter-zonal capacity rule · O6 H3 profitability rule · O7 WACC · O8 licences (code MIT?, ODbL for OSM-derived web data).
Logins needed for Milestone 1: ENTSO-E API token (U2), Copernicus CDS key for ERA5 (U1).

## Repo structure
`config/` · `data/{raw,processed}` + `data/MANIFEST.csv` · `src/netzfix/{data,network,markets,analysis,viz}` · `workflow/` · `scripts/` · `tests/` · `notebooks/` · `results/` · `timestamps/` · `web/` · `vault/`
