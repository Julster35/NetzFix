---
type: data-source
date: 2026-11-03
tags: [data, smard, bnetza, validation]
ai-first: true
status: "2024 hourly series downloaded 2026-11-03 (public API, no login)"
---

# SMARD

## For future agent
SMARD (smard.de) is the Bundesnetzagentur's electricity market data portal: day-ahead prices, generation, consumption and congestion-management (redispatch) data for Germany. NetzFix uses it as a second validation source next to ENTSO-E ([[Validation]] V1, V2, V4-V6).

## Use
- Cross-check of DE-LU day-ahead prices and generation mix vs [[ENTSO-E Transparency]].
- Possibly congestion-management figures for 2024 if the BNetzA report (U3) is not found.

## State (2026-11-03) `stated`
- API: `https://www.smard.de/app/chart_data/{filter}/DE/{filter}_DE_hour_{ts}.json`, weekly chunks; filter IDs from the bundesAPI OpenAPI spec (https://github.com/bundesAPI/smard-api). Code: `src/netzfix/data/smard.py`.
- 2024, region DE: 8,784 hours, no gaps. Annual TWh: load 465.50; lignite 70.99, hard coal 27.34, gas 56.92, other conventional 15.84, wind onshore 112.56, offshore 25.67, solar 63.15, biomass 36.20, hydro 17.55, other renewable 1.06, pumped storage generation 10.39 / consumption 13.05; nuclear empty (closed April 2023).
- Generation sum (437.7 TWh) + net import must cover load + pumped consumption; the playground keeps this residual as border trade.

## Access
- https://www.smard.de (download centre; licence to record at first download, expected CC BY 4.0 - verify). `speculation` until checked.
