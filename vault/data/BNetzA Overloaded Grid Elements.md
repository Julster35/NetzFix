---
type: data-source
date: 2026-11-06
tags: [data, congestion, bottlenecks, bnetza, smard, validation]
ai-first: true
status: "Q1-Q4 2023 + Q1-Q2 2024 held (2026-11-06); Q3/Q4 2024 not published as a table"
---

# BNetzA Overloaded Grid Elements

## For future agent
The only held source that names **which transmission lines** were congested in Germany: the BNetzA table "Überlastete Netzelemente der ÜNB" (the 20-25 most overloaded elements per quarter, with hours of overload from the TSOs' operational planning process PRD1). Used as the yardstick of test T7 in [[Validation]]. Neither ENTSO-E internal redispatch ([[ENTSO-E Transparency]], asset fields empty for all 40,258 German rows of 2024) nor [[netztransparenz Redispatch]] (plant or area only) name the congested line.

## Files (all in `data/raw/bnetza/congestion/`, MANIFEST rows 2026-11-06)
| Period | Source | Format |
|---|---|---|
| Q1 2023 | dsc.bund.de `QuartalszahlenQ1in2023.pdf`, Tabelle 5 p. 12 | PDF |
| Q2 2023 | dsc.bund.de `QuartalszahlenQ2_2023.pdf`, Tabelle 6 p. 14 | PDF |
| Q3 2023 | data.bundesnetzagentur.de `Q3_2023_Quartalsbericht_Netzengpassmanagement.pdf`, Tabelle 6 p. 13 | PDF |
| Q4 2023 | dsc.bund.de `QuartalszahlenQ4_2023.pdf`, Tabelle 6 p. 12 | PDF |
| Q1 2024 | SMARD article "Netzengpassmanagement im 1. Quartal 2024" → `ueberlastete-netzelemente-der-uenb-q1-2024-data.xlsx` | xlsx |
| Q2 2024 | SMARD article "Netzengpassmanagement im 2. Quartal 2024" → `ueberlastete-netzelemente-der-uenb-q2-2024-data.xlsx` | xlsx |

- Downloader and parser: `src/netzfix/data/bnetza_congestion.py` → `data/processed/bnetza_overloaded_elements.csv` (year, quarter, rank, element, control area, hours). `stated`
- **Q3 and Q4 2024:** the SMARD articles for Q3 2024, Q4 2024 and the year 2024 have no element table; the dsc.bund.de names for 2024 return 404 (checked 2026-11-06). `stated`
- The source files carry U+FFFD in place of umlauts ("D�rpen"); matching uses a key that ignores umlauts.
- Hours add up over circuits/cases: Dörpen has 8,153 h in Q1 2023 (> 2,160 h in a quarter). `stated` (Q1 2023 report p. 12)
- Licence: BNetzA publication; SMARD data CC BY 4.0 (to confirm for the report tables).

## Largest elements (sum of the listed quarters, `stated` from the CSV)
- 2023: Dörpen (Dörpen-Niederlangen-Meppen-Hanekenfähr, TenneT/Amprion) 20,197 h; Ovenstädt-Bechterdissen 5,468 h; Großkrotzenburg-Dettingen/Urberach 4,930 h; Ensdorf-Vigy / Oberzier-Maasbracht 4,499 h; Dollern-Sottrum 3,168 h.
- Q1+Q2 2024: Dörpen 7,651 h; Vierraden-Krajnik (PL) 2,716 h; Neuenhagen-Vierraden-Pasewalk 1,784 h; Ensdorf-Vigy / Oberzier-Maasbracht 1,655 h; Ovenstädt-Bechterdissen 1,532 h.

## Links
[[Validation]] (T7) · [[Assumptions]] (A36) · [[Data Sources]] · [[BNetzA 2024 Netzengpassmanagement Q4 2023]]
