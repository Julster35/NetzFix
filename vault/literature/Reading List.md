---
type: reading-list
date: 2026-11-03
tags: [literature, reading-list]
ai-first: true
status: 10-sources-held
---

# Reading List

## For future agent
This is the catalog of all literature for NetzFix. **Held** items have a PDF in `literature/pdfs/` and may be cited, but only for what has actually been read (see each note's `read:` field). **Not held** items must not be used as evidence (see the [[_CLAUDE#Section 0.25 - THE LITERATURE RULE (project-specific, non-negotiable)|literature rule]]). The synthesis is in [[Literature Synthesis]]. State as of 2026-11-04: 14 sources held (2026-11-04: EnWG, Mindestfaktor-Festlegung, netztransparenz prices page, BK8-22-0001-A + Anlage 1).

---

## Held - core (own notes)
| Note | Topic | PDF | Read so far |
|---|---|---|---|
| [[Knoerr Bichler Dobos 2025]] | **Benchmark**: zonal vs nodal on BZR data, DE | `Knoerr_Bichler_Dobos_2025_..._arXiv2403.09265v6.pdf` | main text + App. B |
| [[Xiong et al 2025]] | OSM high-voltage grid in PyPSA-Eur | `Xiong_et_al_2025_..._arXiv2408.17178.pdf` (arXiv v1) | abstract |
| [[Hoersch et al 2018]] | PyPSA-Eur model paper | `Hoersch_et_al_2018_..._arXiv1806.01613v2.pdf` | abstract |
| [[Brown Hoersch Schlachtberger 2018]] | PyPSA software | `Brown_Hoersch_Schlachtberger_2018_..._arXiv1707.09913.pdf` | abstract |

## Held - grey literature (own notes)
| Note | Topic | PDF | Read so far |
|---|---|---|---|
| [[ENTSO-E 2025 BZR Report]] | BZR main report, DE2-DE5 | `ENTSO-E_2025_Bidding_Zone_Review_of_the_2025_Target_Year.pdf` | p. 6-8 |
| [[ENTSO-E 2022 LMP Report]] | LMP study behind the BZR data | `ENTSO-E_2022_LMP_Report.pdf` | p. 3-4 |
| [[EWI 2025 Policy Brief Gebotszonensplit]] | EWI brief on a DE split | `EWI_2025_Policy_Brief_Gebotszonensplit_in_Deutschland.pdf` | p. 4-5 |
| [[BNetzA BKartA 2025 Monitoringbericht]] | Regulators' monitoring report covering 2024 (validation figures) | `BNetzA_BKartA_2025_Monitoringbericht_Energie_2025.pdf` | pp. 18, 22-23, 96, 119-122, 131-136 |
| [[BNetzA 2024 Netzengpassmanagement Q4 2023]] | Congestion management Q4/2023 | `BNetzA_2024_Netzengpassmanagement_Q4_und_Gesamtjahr_2023.pdf` | p. 5, 7, 8 |
| [[EnWG 13 13a Redispatch]] | **Law**: redispatch selection (least cost, minimum factor, grid reserve) and compensation | `EnWG_Stand_2026-11-04_gesetze-im-internet.pdf` (text as of 2026-07-23) | § 13 Abs. 1-3, § 13a, § 13j Abs. 5-6 |
| [[BNetzA 2020 Mindestfaktor-Festlegung]] | EE minimum factor 10; annual calculated prices | `BNetzA_2020-11-30_Mindestfaktor-Festlegung.pdf` | tenor, pp. 1-7, 39-41 |
| [[netztransparenz Kalkulatorische Preise]] | TSOs' calculated EE / NR prices and average conventional RD costs 2021-2027 | `netztransparenz_2026-11-04_Kalkulatorische_Preise.html` | whole page |
| (no note yet) | BNetzA BK8-22-0001-A (2024): appropriate financial compensation of redispatch (§ 13a Abs. 2) + Anlage 1 | `BNetzA_2024_BK8-22-0001-A_Festlegung_Verguetung_Redispatch.pdf`, `..._Anlage1_Bestimmung_finanzieller_Ausgleich.pdf` | not read yet |

## To fetch next (grey literature and data documentation)
- **BNetzA congestion-management report for full year 2024** (U3): not found at a guessable URL on 2026-11-03; download by hand.
- BZR CE output data description PDF ([[BZR dataset]]).
- ENTSO-E BZR Annex 2 (CE input data) PDF.
- DEA technology catalogue (or PyPSA technology-data docs) for CAPEX (A15).

## Not held - do not cite
- Bundesnetzagentur (2024) and (2022) as cited in [[Knoerr Bichler Dobos 2025]] p. 2 and p. 19 (redispatch 2023: 34 TWh, EUR 3.1 bn; 2020-2022 daily average ~kEUR 7,200). Cite only "as cited in Knörr et al.".
- Dobos et al. (2025), zone clustering on BZR data - cited in Knörr et al. p. 5.
- Gerhardt et al. (2025), zonal split with a proprietary data set - cited in Knörr et al. p. 7.
- Kost et al. (2021), fixed costs - cited in Knörr et al. p. 40.
- ACER Decision 11/2022 and its annexes (BZ configurations).
- BMWi (2018-04-27) "Entwicklung von Maßnahmen zur effizienten Gewährleistung der Systemsicherheit im deutschen Stromnetz", p. 80 (formula minimum factor → calculated price) - cited in [[BNetzA 2020 Mindestfaktor-Festlegung]] p. 6 and [[netztransparenz Kalkulatorische Preise]]. Download failed 2026-11-04 (bundeswirtschaftsministerium.de timed out). Formula reconstructed from published numbers instead.
- Xiong et al. 2025 Scientific Data version of record (only the arXiv preprint is held).
- BMWE "Aktionsplan Gebotszone" press release, 2025-12-15 (web search only; see [[Prior Art#4. Policy context (secondary sources, not held - do not cite as evidence)]]).
- Secondary reports of 2024 congestion-management cost (~EUR 2.78 bn preliminary; correctiv.org, contextcrew.de, BDEW Fortschrittsmonitor 2025) - conflicting definitions, not evidence.
