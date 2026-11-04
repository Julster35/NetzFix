---
type: literature
date: 2026-11-04
tags: [literature, grey, diw, costs, efficiency, minimum-load, technology-data]
ai-first: true
pdf: "[[DIW_2013_DD68_Schroeder_et_al_Current_and_Prospective_Costs_of_Electricity_Generation.pdf]]"
citation: "Schröder, A., Kunz, F., Meiss, J., Mendelevitch, R., von Hirschhausen, C. (2013). Current and Prospective Costs of Electricity Generation until 2050. DIW Data Documentation 68. doi:10.18723/diw_ddc:2013-68"
source_url: https://www.diw.de/documents/publikationen/73/diw_01.c.424566.de/diw_datadoc_2013-068.pdf
read: "2026-11-04: Table 27 (PDF pp. 76-77), Table 28 (PDF p. 78), Table 35 (PDF p. 89), fuel cost sentence (PDF p. 90)"
---

# DIW 2013 DD68 Schroeder et al

## For future agent
Widely used open compilation of German power-plant technology data (2013, corrected version, 104 PDF pages): efficiencies by technology and year, minimum load, minimum up/down times, ramping, part-load efficiency losses, O&M and capital costs. NetzFix uses it for **plant technical parameters** in step 2 (unit-specific costs, minimum load) where no unit-level data exist. Values are literature ranges from 2008-2012 studies, so they are `medium` for a 2024 fleet.

## Claims (`stated`, PDF page)
- Table 35 (p. 89), efficiency proposal for 2010 / 2015 / 2020: hard coal PC subcritical 39.0 / 39.0 / 39.0%; hard coal PC supercritical 46.0 / 46.1 / 46.2%; lignite BoA 43.0 / 43.4 / 43.9%; gas CC 60.0 / 60.2 / 60.5%; gas combustion turbine 39.0 / 39.1 / 39.2%; gas steam turbine 41.0 / 41.1 / 41.2%; oil CT 39.0 / 39.1 / 39.2%; pump storage round-trip 75.0%.
- Table 27 (pp. 76-77): minimum load and minimum up/down times compiled from several studies (ranges differ by study, e.g. lignite old 6 h / 6 h in Hundt et al. 2009; gas GT 0-1 h). Minimum-load rows to transcribe before use.
- Table 28 (p. 78): efficiency loss at minimum load, e.g. gas CC 8-11 %pt, gas GT 20-22 %pt (study ranges).
- p. 90: 2010 fuel costs used for their LCOE figure: lignite 2.9 EUR/MWh_th (10 $/t), coal 8.4 EUR/MWh_th (99 $/t), gas 21.6 EUR/MWh_th, CO2 20 EUR/t (2010 values, not 2024).
