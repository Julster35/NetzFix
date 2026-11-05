---
type: data-source
date: 2026-11-05
tags: [data, grid, line-ratings, tso, jao, core]
ai-first: true
status: "6th release (2024-09) downloaded 2026-11-05; not yet used in the model"
---

# JAO Core Static Grid Model

## For future agent
The static grid model of the Core capacity-calculation region, published by JAO for all Core TSOs, **including the four German TSOs (50Hertz, Amprion, TenneT DE, TransnetBW)**. Per circuit: name, EIC code, TSO, substations, voltage, **maximum current Imax** (fixed, six seasonal periods, or DLR min/max), R, X, B, length; plus tie-lines, transformers (incl. phase shifters) and remedial actions. It is the TSOs' own data for the line ratings that our OSM network only guesses (PyPSA-Eur default: every 220 kV circuit 1,290 A). Found 2026-11-05 while checking the 220 kV corridor Mannheim - Karlsruhe ([[Validation]]).

## Access (as of 2026-11-05)
- Page: https://www.jao.eu/static-grid-model (no login). Releases: 4th (2023-09), 5th (2024-04), **6th (file date 202409, listed 2024-10-21; used)**, 7th (2025-03), 8th (2025-09), 9th (2026-03).
- File: `data/raw/jao/core_sgm_6th_202409.zip` (MANIFEST row), unpacked to `data/raw/jao/core_sgm_6th/`: `20240916_Core Static Grid Model_for publication.xlsx` (sheets Lines, Tielines, Transformers, Remedial Actions, Change Log), a Handbook (.docx, not read yet) and an HTML map (`map/`) with substation coordinates and line polylines keyed by EIC code (usable for matching to OSM).
- Imax encoding: `Fixed` column, or `Period 1-6`, or for DLR lines `DLRmin(A)` / `DLRmax(A)`; "-" or empty = not given in that column.
- German 220 kV circuits in the file: 50Hertz 25, TenneT 49, TransnetBW 15, Amprion ~161 rows. Median Imax of the first three: 1,070 / 1,310 / 855 A; 21% above 1,290 A. `stated` (our parse, 2026-11-05)
- Corridor examples (TransnetBW 220 kV): Altlussheim - GKM DLR 2,505-3,000 A; Altlussheim - Daxlanden 2,267 A; Y-GKM (-Neurott - Weinheim) 2,080 A; Daxlanden - Oberwald DLR 1,535-1,916 A; Daxlanden - Karlsruhe West 769 A. `stated`

## Licence (JAO General Terms, https://www.jao.eu/terms-conditions, read 2026-11-05 by a fetch agent)
- Use allowed "for educational, academic or research purposes"; source must be mentioned. All rights reserved to JAO; content "derived from, based on, generated from" counts as Content and may not be "distributed or reproduced" beyond Legitimate Use; scraping/bots prohibited; ML training needs authorisation. `stated`
- **Open point for Julien:** whether publishing the web twin or model files with JAO-derived ratings is Legitimate Use (ask contact@jao.eu if needed).
