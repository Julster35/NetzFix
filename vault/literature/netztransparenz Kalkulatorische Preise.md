---
type: literature
date: 2026-11-04
tags: [literature, grey, tso, redispatch, kalkulatorischer-preis, core]
ai-first: true
pdf: "[[netztransparenz_2026-11-04_Kalkulatorische_Preise.html]]"
citation: "Übertragungsnetzbetreiber (50Hertz, Amprion, TenneT, TransnetBW). Kalkulatorische Preise. netztransparenz.de, accessed 2026-11-04."
source_url: https://www.netztransparenz.de/de-de/Systemdienstleistungen/Betriebsfuehrung/Redispatch/Kalkulatorische-Preise
read: "2026-11-04, whole page (saved HTML; English page cross-checked)"
---

# netztransparenz Kalkulatorische Preise

## For future agent
The four German TSOs' official page with the **calculated (imputed) redispatch prices** for renewables (EE) and grid reserve (NR), and the **average costs of positive and negative redispatch with non-priority (conventional) electricity** behind them, for each year from 2021/22 to 2026/27 (valid 1 Oct - 30 Sep). These are the numbers our redispatch selection rule uses for 2024 ([[Validation]] v3). We reconstructed the price formula from them.

## Claims (`stated`, saved page, €/MWh)

| Validity | Avg cost positive RD | Avg cost negative RD | Calc. EE price | Calc. NR price | Calc. CHP price |
|---|---|---|---|---|---|
| 2021-10-01 - 2022-09-30 | 88.10 | -20.23 | 590.60 | 251.09 | 251.25 |
| 2022-10-01 - 2023-09-30 | 216.99 | -128.50 | 667.89 | 385.88 | not applicable (EnWG) |
| **2023-10-01 - 2024-09-30** | **222.00** | **-142.23** | **575.70** | **476.50** | - |
| **2024-10-01 - 2025-09-30** | **181.10** | **-130.40** | **325.8** | **476.9** | - |
| 2025-10-01 - 2026-09-30 | 149.37 | -40.15 | 942.8 | 182.0 | - |
| 2026-10-01 - 2027-09-30 | 181.30 | -83.31 | 798.6 | 342.0 | - |

- The prices are uniform (not per plant or per bottleneck) and must keep BNetzA's minimum factors "in general" ([[BNetzA 2020 Mindestfaktor-Festlegung]]).
- The minimum factors were converted to prices with the formula on p. 80 of the BMWi study "Entwicklung von Maßnahmen zur effizienten Gewährleistung der Systemsicherheit im deutschen Stromnetz" (not held).
- Footnote: the calculated CHP price was abolished by the Ersatzkraftwerkebereithaltungsgesetz.
- For calendar year 2024: Jan-Sep uses the 2023/24 row, Oct-Dec the 2024/25 row.

## Reconstructed formula (`high`, computed by us 2026-11-04)
With minimum factor MF = 10, average positive cost c⁺ and average negative cost c⁻ (negative number = refund to the TSO):

**p_EE = MF · (c⁺ + c⁻) − c⁺**

It reproduces all six published EE prices within 0.1 €/MWh (e.g. 2023/24: 10 · (222.00 − 142.23) − 222.00 = 575.70; 2024/25: 10 · 50.70 − 181.10 = 325.90 vs 325.8). Meaning: a "renewable pair" (1 MWh RE down + 1 MWh conventional up) costs c⁺ + p_EE = MF · (c⁺ + c⁻), i.e. exactly 10 times a "conventional pair" (1 MWh conventional down + 1 MWh up). So a cost-minimising operator curtails renewables only where that relieves the line at least ~10 times more effectively than reducing conventional plants. The NR price does not follow from these averages (the law only bounds it from below, [[EnWG 13 13a Redispatch]] Abs. 1c).
