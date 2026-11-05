---
type: data-source
date: 2026-11-03
tags: [data, sources, master]
ai-first: true
status: "master list; nothing downloaded yet (2026-11-03)"
---

# Data Sources

## For future agent
Master list of every NetzFix data source, the layer it feeds, its access status and its note. Every download goes to `data/raw/` and gets a row in `data/MANIFEST.csv` (url, access date, sha256); processed tables go to `data/processed/`. Never fabricate data: if a source is down or behind a login, stop and tell Julien.

| Layer | Source | Note | Access | Status (2026-11-03) |
|---|---|---|---|---|
| 1 Grid | PyPSA-Eur OSM network v0.7 | [[OSM PyPSA-Eur Grid]] | open (ODbL) | ✅ 2026-11-03 |
| 2 Units | Marktstammdatenregister (+ powerplantmatching coordinates) | [[Marktstammdatenregister]] | open | ✅ 2026-11-03 |
| 3 Wind/PV | ERA5 via atlite | [[ERA5 and atlite]] | CDS key (Julien, 2026-11-04) | ⏳ 2024 cutout downloading (job 5733, 2026-11-04) |
| 4 Conventional calibration | ENTSO-E generation per unit | [[ENTSO-E Transparency]] | File Library (login, no token) | ✅ 2024 held 2026-11-04 (176 DE units) |
| 4 Fuel/CO2 prices 2024 | to choose (A14) | - | - | not chosen |
| 5 Demand | v0: SMARD load × LAU population shares; later ENTSO-E + DemandRegio | [[SMARD]], [[DemandRegio]] | open (v0) | ✅ v0 2026-11-03 |
| 6 Cross-border | ENTSO-E flows | [[ENTSO-E Transparency]] | token | not downloaded |
| 7 Validation / behaviour | SMARD 2024 hourly (load, generation per technology, price) | [[SMARD]], [[netztransparenz Redispatch]] | open | ✅ SMARD 2024 |
| X Cross-validation | ENTSO-E BZR data | [[BZR dataset]] | open | public, not downloaded |
| X Line ratings / FB | JAO | [[JAO]] | open | optional |

Inventory of what is actually on disk: [[Raw Data Inventory]].

- [[JAO Core Static Grid Model]] - TSO line ratings (Imax), R/X/B, transformers and PSTs per circuit for the Core region incl. 50Hertz, Amprion, TenneT DE, TransnetBW; 6th release (2024-09) held since 2026-11-05. Research use only (JAO terms).
