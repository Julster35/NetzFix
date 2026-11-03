---
type: literature
date: 2026-11-03
tags: [literature, benchmark, zonal, nodal, germany, bzr, core]
ai-first: true
pdf: "[[Knoerr_Bichler_Dobos_2025_Zonal_vs_Nodal_German_DayAhead_arXiv2403.09265v6.pdf]]"
citation: "Knörr, J., Bichler, M., Dobos, T. (2025). Zonal vs. Nodal Pricing: An Analysis of Different Pricing Rules in the German Day-Ahead Market. arXiv:2403.09265v6 [econ.GN], 2 Jun 2025. Journal: Energy Economics."
source_url: https://arxiv.org/abs/2403.09265v6
read: 2026-11-03 (abstract, Sec. 1-3.1, Tables 1-3, conclusion, Appendix B via text extraction; Appendices A, C-F not read)
---

# Knoerr Bichler Dobos 2025 - Zonal vs Nodal Pricing in the German Day-Ahead Market

## For future agent
**The benchmark NetzFix must discuss its results against.** On ENTSO-E's Bidding Zone Review data for Germany (target year 2025), zonal splits into 2-4 zones cut total cost by less than 1%, nodal pricing by about 5-6% (Tables 2-3, p. 19). Held version is arXiv v6 (2 Jun 2025), headed for Energy Economics; numbers may differ from the version of record. Pages below are **PDF pages** of the held file.

## Claims (all `stated`, from the PDF)
- **Abstract (p. 1):** "While the total cost savings after introducing zonal splits were less than 1%, nodal pricing led to savings of 5-6%."
- **Context (p. 2):** German redispatch "to 34 TWh and EUR 3.1 billion in 2023 (Bundesnetzagentur, 2024)". SuedLink (expected 2028) is not modelled in the data set (footnote 1, p. 2).
- **Data (p. 5, p. 36-38):** independent analysis of the BZR dataset, "based on supply and load data collected in 2019 and models the target year 2025" (p. 5). ENTSO-E released the LMP-study data in September 2022 (Appendix B, p. 36). Climate years 1989, 1995, 2009 (p. 36). Pre-processed German grid: **1,670 nodes and 2,407 lines** (p. 37). **4,537 generation units, 1,709 (37%) with unit-commitment rigidities** (p. 38). Some data aggregated before publication (local demand to country-wide), generator-to-grid mapping not revealed (p. 36). Fixed costs from Kost et al. 2021 (p. 40).
- **Line count vs JAO (footnote 5, p. 4):** JAO Static Grid model has 837 lines ≥ 220 kV; their data set has 2,407 lines at various voltage levels.
- **Method (p. 18):** Python 3.11 + Gurobi; "eight weeks in 2009 for the German BZ"; MIP gap 5%. Unit commitment as MILP; demand inelastic (p. 10).
- **Configurations (Table 1, p. 18):** National, 2 Zones (k-means), 2 Zones (spectral), 3 Zones, 4 Zones, Nodal (+ Euphemia).
- **Table 2 (p. 19), average daily costs, kEUR:**

| | National | 2 Zones (k) | 2 Zones (s) | 3 Zones | 4 Zones | Nodal |
|---|---|---|---|---|---|---|
| Generation | 32,145.08 | 32,428.55 | 32,219.17 | 32,198.95 | 32,382.74 | 36,150.7 |
| RD-Min-Cost (redispatch) | 6,140.06 | 5,687.83 | 5,863.74 | 5,827.86 | 5,726.9 | 0 |
| Total | 38,285.14 | 38,116.38 | 38,082.91 | 38,026.81 | 38,109.64 | 36,150.7 |

- **Table 3 (p. 19):** percentage by which zonal total cost exceeds nodal (x/y·100 − 100): National 5.90, 2Z(k) 5.44, 2Z(s) 5.34, 3Z 5.19, 4Z 5.42.
- p. 19: "we assume that all generators can be redispatched in our model, such that redispatch costs in reality might be higher." Average daily German redispatch costs 2020-2022 roughly kEUR 7,200 (Bundesnetzagentur, 2022).
- **Inconsistency:** p. 7 says nodal savings are "around 7-8%"; the abstract, Table 3 and conclusion (p. 29) say 5-6%. Cite Tables 2-3.
- **BZR 2025 final results (p. 4, p. 50):** welfare gains of alternative configurations < 1% of simulated CE system costs; DE-LU splits EUR 251-339 million, highest for a five-zone split (Appendix F, p. 50).

## Our computations from Table 2 (`high`, recomputed 2026-11-03)
- Zonal vs National total-cost savings: 2Z(k) 0.44%, 2Z(s) 0.53%, 3Z 0.67% (0.675), 4Z 0.46%. Nodal vs National: 5.58% of National cost (5.90% expressed relative to nodal, as in Table 3).

## Relevance to NetzFix
- [[Validation]] V7 and the discussion of H1 ([[Hypotheses]]).
- Differences to expect: their year is 2025 (2019 data) and climate year 2009, ours 2024/2024; they use MILP UC on an unclustered 1,670-node grid, we a linear model on 30-200+ clusters; their redispatch pool is unrestricted. Our A-vs-C gap is driven by frictions ([[Research Design#Why A and C differ at all]]).
- Their zone sets are the ACER 2022 configurations, not the final DE5 ([[Zonal Pricing and Bidding Zones]]).
- No code release found (2026-11-03).
